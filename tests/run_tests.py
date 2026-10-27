#!/usr/bin/env python3
"""
run_tests.py - invariant checks for the profile-update and retrieval machinery

Runs the real command-line entry points against a disposable copy of the test
corpus in tests/fixture/ and asserts the things that must always hold. Every
check here corresponds to a defect that actually shipped, so the set is a record
of what has broken rather than a guess at what might.

Two safety properties, both enforced rather than documented:

  1. The runner sets CAREER_FIXTURE itself and refuses to proceed unless the
     resolved profile path sits under tests/. A test can therefore never write
     to the candidate's real documents, including by forgetting a flag.
  2. Every test runs against a fresh copy in tests/.run/, not against
     tests/fixture/ itself, so the committed corpus is the same before and
     after a run however badly a test misbehaves.

Usage     : python tests/run_tests.py
            python tests/run_tests.py --only counter
Exit code : 0 when every check passes, 1 otherwise, so this can gate a change.

Author    : Jason Delosh
Created   : 2026-08-26
Project   : career
Depends   : pyyaml (via the scripts it drives)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import traceback

# ---------------------------------------------------------------------------
# Paths and the fixture guard
# CAREER_FIXTURE is set here, before any script is imported or invoked, and is
# pointed at a copy rather than at the corpus. _assert_isolated then proves the
# redirect actually took effect; without that proof a silently-ignored
# environment variable would send every write below into the real profile.
# ---------------------------------------------------------------------------

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
SCRIPTS_DIR = os.path.join(REPO_ROOT, 'scripts')
FIXTURE = os.path.join(TESTS_DIR, 'fixture')
RUN_DIR = os.path.join(TESTS_DIR, '.run')
RUN_REL = os.path.join('tests', '.run')

os.environ['CAREER_FIXTURE'] = RUN_REL
sys.path.insert(0, SCRIPTS_DIR)

import _config          # noqa: E402
import _util            # noqa: E402
import profile_update as pu   # noqa: E402
from inventory_model import document, entry_block, ex   # noqa: E402


def _assert_isolated():
    """Stop the run unless every resolved path sits inside tests/."""
    root, cfg = _config.load()
    for path in (pu._inventory_path(root, cfg), pu._staging_path(root, cfg),
                 pu._narratives_path(root, cfg)):
        if not os.path.abspath(path).startswith(TESTS_DIR + os.sep):
            raise SystemExit(
                f'REFUSING TO RUN: {path} is outside tests/. The fixture '
                f'redirect is not in effect and these tests write.')


# ---------------------------------------------------------------------------
# Harness
# Commands go through subprocess so the real argparse layer, the real exit
# codes, and the real error text are all exercised. State is read back through
# direct imports, because assertions want parsed structures rather than stdout.
# ---------------------------------------------------------------------------

def reset():
    """Replace the run copy with a pristine copy of the corpus."""
    if os.path.isdir(RUN_DIR):
        shutil.rmtree(RUN_DIR)
    shutil.copytree(FIXTURE, RUN_DIR)


def run(script, *args):
    """Invoke a script's CLI; return (returncode, combined output)."""
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, script), *args],
        capture_output=True, text=True, cwd=SCRIPTS_DIR)
    return result.returncode, (result.stdout + result.stderr).strip()


def pu_cmd(*args):
    """Invoke profile_update.py."""
    return run('profile_update.py', *args)


def ok(*args):
    """Invoke profile_update.py and require success; return stdout."""
    code, out = pu_cmd(*args)
    assert code == 0, f'expected success from {args[0]}, got:\n{out}'
    return out


def fails(*args):
    """Invoke profile_update.py and require failure; return the message."""
    code, out = pu_cmd(*args)
    assert code != 0, f'expected {args[0]} to fail, but it succeeded:\n{out}'
    return out


def docs():
    """Return (inventory_text, staging_text) as they currently stand."""
    root, cfg = _config.load()
    return (_util.read(pu._inventory_path(root, cfg)),
            _util.read(pu._staging_path(root, cfg)))


def queued_labels(staging_text):
    """Return the labels of the items still waiting in the queue."""
    return [item['label'] for item in pu.parse_staging(staging_text)]


# The fixture's two queued items.
VENDOR_ITEM = 'Vendor management scope at Northwind'
TOOL_ITEM = 'Additional analytics tooling'

# A complete capture file, as staging_append.py takes it.
CAPTURE = """Work role: RL-002
Did: Ran the monthly data-transfer reconciliation with the central lab.
Others did: The lab's data manager produced the transfer files.
Outcome: none stated
Limits: none
"""


def stage(capture, label='Lab transfer reconciliation', requirement='CR-002'):
    """Run staging_append.py against the fixture application; return (code, out)."""
    path = write_block('capture.md', capture)
    return run('staging_append.py', '--folder', FIXTURE_APP,
               '--requirement', requirement, '--capture-file', path,
               '--label', label)


def write_block(name, text):
    """Write a working file for insert/set and return its path."""
    path = os.path.join(RUN_DIR, name)
    _util.write(path, text)
    return path


EX_BLOCK = """Role: RL-002
Industry: pharma
Specialty: operations-strategy
Orientation: process-operations
Level: leadership
Work-state: mature
Description: **Ran the quarterly vendor performance review.** Set the scorecard and chaired the review.
Impact: Vendor scope changes followed a documented review rather than ad hoc request.
"""

# The fixture's first RL-002 topic group, where EX_BLOCK inserts land.
EX_GROUP = 'establish processes: study start-up data handling'


# ---------------------------------------------------------------------------
# The checks
# Each name is the defect it exists to catch. The docstring says what shipped.
# ---------------------------------------------------------------------------

def test_review_fix_lands_while_the_item_waits():
    """Shipped 2026-10-05 (#70): the item left the queue before review, so every
    fix the review asked for failed with 'not in the staging queue'.

    Writes no longer depend on the queue, and the item is removed only after
    review, so a fix after the first write succeeds and the item is still there.
    """
    write_block('b.md', EX_BLOCK)
    new_id = ok('insert', '--prefix', 'EX', '--block-file', os.path.join(RUN_DIR, 'b.md'),
                '--group', EX_GROUP)
    write_block('v.md', 'Vendor scope changes went through a documented review.')
    ok('set', '--id', new_id, '--field', 'Impact',
       '--value-file', os.path.join(RUN_DIR, 'v.md'))
    assert VENDOR_ITEM in queued_labels(docs()[1]), 'the item left before review'

    out = ok('remove', '--item', VENDOR_ITEM)
    assert 'scope negotiation' in out, f'remove did not print what it held:\n{out}'
    assert queued_labels(docs()[1]) == [TOOL_ITEM]


def test_remove_leaves_no_residue():
    """Removing the last item restores the empty marker and keeps no record, so
    the next capture appends into a well-formed queue."""
    ok('remove', '--item', VENDOR_ITEM)
    ok('remove', '--item', TOOL_ITEM)
    staging = docs()[1]
    assert not pu.parse_staging(staging), 'queue should be empty'
    assert '_(none)_' in staging, 'empty marker not restored'
    assert 'Migrated' not in staging and 'PU-' not in staging, staging
    fails('remove', '--item', VENDOR_ITEM)

    code, out = stage(CAPTURE)
    assert code == 0, out
    assert queued_labels(docs()[1]) == ['Lab transfer reconciliation']


def test_capture_refuses_a_missing_or_blank_field():
    """Shipped 2026-08-25: one free-text field let the role, the split of work,
    and the outcome go unrecorded, and every first-run entry needed its
    attribution corrected. Each capture field is now required."""
    before = docs()[1]
    cases = [
        ('a missing field', CAPTURE.replace('Others did: The lab\'s data manager '
                                            'produced the transfer files.\n', ''),
         'Others did'),
        ('a blank field', CAPTURE.replace('Outcome: none stated', 'Outcome:'),
         'Outcome'),
        ('a made-up role', CAPTURE.replace('RL-002', 'RL-099'), 'RL-099'),
        ('an unshaped role', CAPTURE.replace('RL-002', 'Northwind'), 'Work role'),
        ('an unknown field', CAPTURE + 'Notes: extra\n', 'Notes'),
    ]
    for label, capture, expect in cases:
        code, out = stage(capture)
        assert code != 0, f'{label} was accepted:\n{out}'
        assert 'capture refused' in out and expect in out, f'{label}: {out}'
    assert docs()[1] == before, 'a refused capture still changed the file'

    code, out = stage(CAPTURE.replace('RL-002', 'new: Halloway Labs, Analyst'))
    assert code == 0, out
    item = pu.find_item(docs()[1], 'Lab transfer reconciliation')
    for field in ('Work role', 'Did', 'Others did', 'Outcome', 'Limits'):
        assert pu.bullet_value(item['body'], field), f'{field} not rendered'
    code, out = stage(CAPTURE)
    assert code != 0 and 'already waiting' in out, f'a duplicate label was accepted:\n{out}'


def test_related_pull_covers_the_role_and_shared_words():
    """The routing decision (new entry, addition, or duplicate) used to rest on
    a by-hand search that missed covering entries. The pull is now fixed: every
    entry in the item's Work role, plus entries elsewhere sharing key words."""
    inventory = docs()[0]
    role_ids = re.findall(r'^ID: ((?:EX|PR|PB|PS)-\d+)\nRole: RL-002$', inventory, re.MULTILINE)
    assert role_ids, 'fixture lost its RL-002 entries'

    code, out = stage(CAPTURE.replace(
        'Ran the monthly data-transfer reconciliation with the central lab.',
        'Extended the shared clinical warehouse schema and its load jobs.'))
    assert code == 0, out
    code, out = run('profile_slice.py', 'related', '--item', 'Lab transfer reconciliation')
    assert code == 0, out
    same, other = out.split('## Shared key words', 1)
    for entry_id in role_ids:
        assert f'ID: {entry_id}' in same, f'{entry_id} missing from the same-role pull'
    assert 'ID: EX-001' in other and 'warehouse' in other, f'shared-word entry not pulled:\n{other}'
    assert 'Orientation:' not in out, 'axis fields leaked into the pull'
    # Routing a new EX entry names the topic group it joins, so each label
    # heads its own entries in the same-role pull (ex-topic-groups-2026-10).
    assert re.search(r'^--- enrollment forecasting\n+ID: EX-003$', same, re.MULTILINE), \
        f'topic group labels missing from the same-role pull:\n{same}'

    import profile_slice
    blocks = [f'block {i} ' + 'x' * 40 for i in range(9)]
    parts = profile_slice.split_parts(blocks, 120)
    assert len(parts) > 1 and [b for p in parts for b in p] == blocks, 'parts lost or reordered blocks'
    assert all(sum(len(b) for b in p) <= 120 for p in parts), 'a part exceeded the limit'


def test_rules_slice_prints_shared_rules_and_one_type():
    """Writing one entry type loads the shared rules and that type's section
    only; a type with no section is an error, never the shared rules alone."""
    import rules_slice
    text = ('# Rules\n\nOpening.\n\n## Shared wording\n\nShared rule.\n\n'
            '## EX: Experience entries\n\nEX rule.\n\n## ED: Education\n\nED rule.\n')
    ex_slice = rules_slice.slice_text(text, 'EX')
    assert 'Opening.' in ex_slice and 'Shared rule.' in ex_slice and 'EX rule.' in ex_slice, ex_slice
    assert 'ED rule.' not in ex_slice, 'another type leaked into the slice'
    assert rules_slice.slice_text(text) == text
    try:
        rules_slice.slice_text(text, 'PR')
    except ValueError as e:
        assert 'PR' in str(e) and 'EX, ED' in str(e), e
    else:
        raise AssertionError('a type with no section did not raise')
    code, out = run('rules_slice.py', 'routing')
    assert code == 0 and '# Routing rules' in out, out


def test_every_entry_type_has_writing_rules():
    """The writer and the reviewer load rules per entry type; a type with no
    section stops the run rather than leaving the model to guess. Every type the
    template defines, plus the list sections, must have one."""
    import rules_slice
    root, cfg = _config.load()
    prefixes = set(document.parse_template(_util.read(pu._template_path(root, cfg))))
    keys = set(rules_slice.type_keys(rules_slice.load(root, cfg, 'inventory-writing')))
    missing = sorted((prefixes | {'LIST'}) - keys)
    assert not missing, f'entry types with no writing rules: {missing}'


def test_reviewer_context_carries_items_entries_and_rules():
    """The reviewer gets its inputs from a script, never a hand-composed prompt:
    the staged item, the entry written, and only that entry type's rules."""
    write_block('b.md', EX_BLOCK)
    new_id = ok('insert', '--prefix', 'EX', '--block-file', os.path.join(RUN_DIR, 'b.md'),
                '--group', EX_GROUP)
    target = 'Technical Experience / Programming, Data & Analytics / Platforms'
    ok('list-add', '--target', target, '--item', 'Tableau')
    path = os.path.join(RUN_DIR, 'qc_context.md')
    code, out = run('profile_update_qc.py', 'context', '--item', VENDOR_ITEM,
                    '--scope-id', new_id, '--scope-id', target, '--out', path)
    assert code == 0 and f'Context file: {path}' in out, out
    context = _util.read(path)
    assert pu.find_item(docs()[1], VENDOR_ITEM)['body'] in context, 'item not copied verbatim'
    assert f'ID: {new_id}' in context and 'Tableau' in context, 'written entries missing'
    assert '## EX: ' in context and '## LIST: ' in context and '## Shared wording' in context
    assert '## PR: ' not in context and '## ED: ' not in context, 'unrelated rules leaked'


def test_concurrent_inserts_do_not_collide():
    """The APP-NNN collision class: two writes in one run claiming one number.

    insert assigns the ID at write time rather than letting a caller pick one,
    so a second insert cannot reuse the first's number.
    """
    write_block('b.md', EX_BLOCK)
    first = ok('insert', '--prefix', 'EX',
               '--block-file', os.path.join(RUN_DIR, 'b.md'), '--group', EX_GROUP)
    second = ok('insert', '--prefix', 'EX',
                '--block-file', os.path.join(RUN_DIR, 'b.md'), '--group', EX_GROUP)
    assert first != second, f'both inserts claimed {first}'
    ids = [e['id'] for e in entry_block.parse_blocks(docs()[0])]
    assert len(ids) == len(set(ids)), 'duplicate IDs in the inventory'


def test_new_entry_lands_at_the_end_of_its_named_group():
    """Shipped 2026-08-25 as a dead end: an entry could be placed outside the
    group its Role names. Since ex-topic-groups-2026-10 it must also land in the
    topic group it names, never by a sort rule the user's groups do not follow.
    """
    path = os.path.join(RUN_DIR, 'b.md')
    write_block('b.md', EX_BLOCK)
    new_id = ok('insert', '--prefix', 'EX', '--block-file', path, '--group', EX_GROUP)
    inventory, _ = docs()
    groups = ex.role_groups(inventory, 'RL-002')
    assert [g['entries'] for g in groups] == [['EX-004', new_id], ['EX-003']], \
        f'{new_id} did not close the "{EX_GROUP}" group: {groups}'

    out = fails('insert', '--prefix', 'EX', '--block-file', path)
    assert '--group' in out, f'an EX insert with no group was accepted:\n{out}'
    out = fails('insert', '--prefix', 'EX', '--block-file', path, '--group', 'no such topic')
    assert EX_GROUP in out, f'an unknown group was not refused with the real labels:\n{out}'
    out = fails('insert', '--prefix', 'EX', '--block-file', path, '--new-group', EX_GROUP)
    assert 'already' in out, f'a duplicate group label was accepted:\n{out}'

    newer = ok('insert', '--prefix', 'EX', '--block-file', path,
               '--new-group', 'vendor oversight: quarterly reviews')
    groups = ex.role_groups(docs()[0], 'RL-002')
    assert groups[-1] == {'label': 'vendor oversight: quarterly reviews',
                          'entries': [newer]}, f'new group did not close RL-002: {groups}'


def test_group_label_stays_out_of_the_entry_above():
    """Found 2026-10-27 on the live inventory: an entry ran on to the next ID
    line, so the last entry of every topic group carried the following group's
    label into every slice, and an edit to that entry could delete or move it.
    """
    code, out = run('profile_slice.py', 'id', 'EX-004')
    assert code == 0 and '---' not in out, f'the next group label leaked into EX-004:\n{out}'

    # Replacing the last field of a group's last entry keeps the next label.
    write_block('v.md', 'Prior state was nightly extracts refreshed by hand.')
    ok('set', '--id', 'EX-001', '--field', 'Context',
       '--value-file', os.path.join(RUN_DIR, 'v.md'))
    assert '--- vendor evaluation: data capture platform' in docs()[0], \
        'set deleted the next group label'

    # Adding an omitted last field lands above the next label, not below it.
    write_block('v.md', 'Each study lead ran start-up by local convention.')
    ok('set', '--id', 'EX-004', '--field', 'Context',
       '--value-file', os.path.join(RUN_DIR, 'v.md'))
    inventory = docs()[0]
    assert inventory.index('Each study lead ran') < inventory.index('--- enrollment forecasting'), \
        'set placed the new field inside the next group'


def test_new_role_creates_its_entry_group():
    """Shipped 2026-08-25: inserting a role record did not create the group its
    entries land in, so the next entry insert had nowhere to go.
    """
    write_block('r.md', """Title: Analyst
Company: Halloway Labs
Location: Remote
Type: Full-time
Style: Remote
Concurrent: No
Allocation: 100%
Start Date: 2014-01
End Date: 2016-01
""")
    role = ok('insert', '--prefix', 'RL',
              '--block-file', os.path.join(RUN_DIR, 'r.md'))
    inventory, _ = docs()
    assert document.section_bounds(inventory, role) is not None, \
        f'no "### {role}" group was created under Experience Entries'

    # And an entry for that role now has somewhere to go.
    write_block('b.md', EX_BLOCK.replace('Role: RL-002', f'Role: {role}'))
    ok('insert', '--prefix', 'EX', '--block-file', os.path.join(RUN_DIR, 'b.md'),
       '--new-group', 'lead execution: lab onboarding')
    code, out = run('profile_update_qc.py', 'check')
    assert code == 0, f'the first entry of a new role left the document invalid:\n{out}'


def test_list_add_is_additive():
    """A whole-line rewrite on a roster of thirty tool names loses items.

    list-add appends and refuses a repeat; it must never drop or reorder.
    """
    target = 'Technical Experience / Programming, Data & Analytics / Platforms'
    root, cfg = _config.load()
    tpl = _util.read(pu._template_path(root, cfg))
    sections = pu.list_sections(tpl, document.parse_template(tpl))
    before = pu.split_items(pu.resolve_list_target(docs()[0], target, sections)['value'])

    ok('list-add', '--target', target, '--item', 'Tableau')
    after = pu.split_items(pu.resolve_list_target(docs()[0], target, sections)['value'])
    assert after[:len(before)] == before, f'existing items changed: {before} -> {after}'
    assert after[-1] == 'Tableau'

    out = fails('list-add', '--target', target, '--item', 'tableau')
    assert 'already listed' in out, out


def test_enrichment_preserves_the_rest_of_the_entry():
    """set replaces one field's span; it must not drop a sibling, reorder the
    roster, or land on a neighbouring entry.
    """
    before = {e['id']: e['field_map'] for e in entry_block.parse_blocks(docs()[0])}
    write_block('v.md', 'Enrollment projections now run from one reviewed model.')
    ok('set', '--id', 'EX-003', '--field', 'Impact',
       '--value-file', os.path.join(RUN_DIR, 'v.md'))

    after = {e['id']: e['field_map'] for e in entry_block.parse_blocks(docs()[0])}
    assert set(before) == set(after), 'an entry appeared or vanished'
    assert after['EX-003']['Impact'] != before['EX-003']['Impact'], 'no change applied'
    assert set(after['EX-003']) == set(before['EX-003']), 'field roster changed'
    for entry_id in before:
        if entry_id != 'EX-003':
            assert after[entry_id] == before[entry_id], f'{entry_id} was altered'


def test_document_stays_valid_after_writes():
    """Any sequence of writes must leave a document the checker still passes."""
    write_block('b.md', EX_BLOCK)
    ok('insert', '--prefix', 'EX', '--block-file', os.path.join(RUN_DIR, 'b.md'),
       '--group', EX_GROUP)
    ok('list-add',
       '--target', 'Technical Experience / Programming, Data & Analytics / Platforms',
       '--item', 'Tableau')

    code, out = run('profile_update_qc.py', 'check')
    assert code == 0, f'checker failed after a normal run:\n{out}'
    ok('remove', '--item', VENDOR_ITEM)
    ok('remove', '--item', TOOL_ITEM)
    code, out = run('profile_update_qc.py', 'check')
    assert code == 0, f'checker failed on an emptied queue:\n{out}'


# ---------------------------------------------------------------------------
# The checker must actually check
# The 2026-08-25 axis-drift root cause was three QC scripts written to accept
# both the correct shape and the drifted one. A check that tolerates two shapes
# has stopped checking, and nothing detects that from the passing side. So each
# case below breaks the document deliberately and requires a complaint.
# ---------------------------------------------------------------------------

# The fixture project's last line, and a second objective block for the same
# project that disagrees on Level, for the project-agreement breakage.
PR_LAST_LINE = '    Outcome: Used by a small number of external groups for format conversion.\n'
PR_SECOND_BLOCK = """ID: PR-002
Project: Open Trial Metadata Toolkit
Role: RL-002
Specialty: data-engineering
Orientation: platform-technology
Level: leadership
Work-state: greenfield
Objective: Make the toolkit the reference converter for partner groups.
Elements:
"""

BREAKAGES = [
    ('a missing required field',
     lambda t: t.replace('Specialty: data-science\nOrientation: data-analytics',
                         'Orientation: data-analytics')),
    ('an off-registry axis value',
     lambda t: t.replace('Specialty: data-science', 'Specialty: astrology')),
    ('a dangling cross-reference',
     lambda t: t.replace('Recognizes: EX-001', 'Recognizes: EX-404')),
    ('a duplicate ID',
     lambda t: t.replace('ID: EX-002', 'ID: EX-001')),
    ('an entry in the wrong role group',
     lambda t: t.replace('ID: EX-001\nRole: RL-001', 'ID: EX-001\nRole: RL-002')),
    # Topic groups (ex-topic-groups-2026-10).
    ('an entry outside any topic group',
     lambda t: t.replace('--- tool development: clinical data warehouse\n\n', '')),
    ('a malformed group marker',
     lambda t: t.replace('--- vendor evaluation:', '---vendor evaluation:')),
    ('an empty topic group',
     lambda t: t.replace('--- vendor evaluation:', '--- empty topic\n\n--- vendor evaluation:')),
    ('a group label repeated within a role',
     lambda t: t.replace('--- vendor evaluation: data capture platform',
                         '--- tool development: clinical data warehouse')),
    ('a hand-edited table of contents',
     lambda t: t.replace('- [Languages](#languages)\n', '')),
    ('a populated section still marked empty',
     lambda t: t.replace('## Presentations\n\nEntries: None',
                         '## Presentations\n\nID: PS-001')),
    ('an item listed twice in one category',
     lambda t: t.replace('Platforms: Snowflake, Databricks',
                         'Platforms: Snowflake, Databricks, Snowflake')),
    ('a fields-out-of-order entry',
     lambda t: t.replace('Level: ic\nWork-state: greenfield',
                         'Work-state: greenfield\nLevel: ic')),
    ('an element numbered for another project',
     lambda t: t.replace('  - PR-001.02:', '  - PR-002.02:')),
    ('an element not padded to two digits',
     lambda t: t.replace('  - PR-001.02:', '  - PR-001.2:')),
    ('a duplicate element',
     lambda t: t.replace('  - PR-001.02:', '  - PR-001.01:')),
    ('an Outcome not under an element',
     lambda t: t.replace('Elements:\n', 'Elements:\n    Outcome: Stray result.\n')),
    ('two blocks of one project that disagree',
     lambda t: t.replace(PR_LAST_LINE, PR_LAST_LINE + '\n' + PR_SECOND_BLOCK)),
    # The mechanical wording rules (P15), one per rule.
    ('first person in a Description',
     lambda t: t.replace('Replaced per-study spreadsheets', 'I replaced per-study spreadsheets')),
    ('a banned phrase in an Impact',
     lambda t: t.replace('Impact: Enrollment projections', 'Impact: Positioned for enrollment projections')),
    ('an em dash in a Context',
     lambda t: t.replace('No central enrollment view existed;',
                         'No central enrollment view existed —')),
    ('an Impact that does not end in a period',
     lambda t: t.replace('used at portfolio planning.\n', 'used at portfolio planning\n', 1)),
    ('an AI-tell in an element Outcome',
     lambda t: t.replace('    Outcome: Used by', '    Outcome: Successfully used by', 1)),
]


def test_checker_catches_each_breakage():
    """Every deliberate defect must produce a complaint, not a pass."""
    root, cfg = _config.load()
    path = pu._inventory_path(root, cfg)
    pristine = _util.read(path)
    # A pristine document that already fails would let every breakage "fail"
    # for the wrong reason, so the baseline has to pass first.
    code, out = run('profile_update_qc.py', 'check')
    assert code == 0, f'the unbroken fixture already fails the checker:\n{out}'
    missed = []
    for label, break_it in BREAKAGES:
        broken = break_it(pristine)
        assert broken != pristine, f'breakage "{label}" did not change the file'
        _util.write(path, broken)
        code, _ = run('profile_update_qc.py', 'check')
        if code == 0:
            missed.append(label)
        _util.write(path, pristine)
    assert not missed, 'the checker passed a broken document: ' + '; '.join(missed)


def test_checker_catches_an_incomplete_staging_item():
    """An item missing a capture field, written by hand or by the old schema,
    would make the profile-update run guess the missing fact."""
    root, cfg = _config.load()
    path = pu._staging_path(root, cfg)
    text = _util.read(path)
    _util.write(path, text.replace('- **Others did:** Procurement owned the contracts.\n', ''))
    code, out = run('profile_update_qc.py', 'check')
    assert code != 0 and 'Others did' in out, f'an incomplete item passed:\n{out}'

    _util.write(path, text.replace(f'### {TOOL_ITEM}', f'### {VENDOR_ITEM}'))
    code, out = run('profile_update_qc.py', 'check')
    assert code != 0 and 'share the label' in out, f'a repeated label passed:\n{out}'


def test_wording_check_spares_domain_terms():
    """Found 2026-10-22 on the live inventory: 'PI/sub-I' read as first person.
    'Phase I' is everywhere in clinical work and must pass too."""
    import profile_update_qc
    for clean in ('Ran Phase I and Class I device studies.',
                  'Kept PI/sub-I alignment across sites.',
                  'Supported US and EU filings.'):
        assert profile_update_qc.wording_problems(clean, True) == [], clean
    for dirty in ('I ran the study.', 'Our team ran it.', 'Ran it for us.'):
        assert profile_update_qc.wording_problems(dirty, True), dirty


def test_wording_findings_outside_the_run_are_advisory():
    """A pre-existing wording problem elsewhere must not block a run's own work,
    or every scoped run fails on the backlog."""
    root, cfg = _config.load()
    path = pu._inventory_path(root, cfg)
    _util.write(path, _util.read(path).replace('used at portfolio planning.\n',
                                               'used at portfolio planning\n', 1))
    code, out = run('profile_update_qc.py', 'check', '--scope-id', 'EX-001')
    assert code == 0 and 'pre-existing' in out, f'an out-of-scope finding blocked the run:\n{out}'
    code, out = run('profile_update_qc.py', 'check', '--scope-id', 'EX-003')
    assert code != 0 and 'period' in out, f'an in-scope finding passed:\n{out}'


# ---------------------------------------------------------------------------
# Project elements (pr-objective-elements-schema-2026-10)
# A project is an Objective plus numbered elements. A CV cites an element by
# its own ID, so an element number must never be reissued, a made-up one must
# fail every ID check, and an element must travel with its objective.
# ---------------------------------------------------------------------------

def write_retired(*rows):
    """Write inventory-ret.md into the run copy with the given ID rows."""
    root, cfg = _config.load()
    path = os.path.join(root, cfg['paths']['profile'],
                        cfg['filenames']['inventory_retired_file'])
    _util.write(path, '# Retired\n\n| ID | Retired | Notes |\n|---|---|---|\n'
                + ''.join(f'| {r} | 2026-10-21 | Retired text: an old element. |\n'
                          for r in rows))


def element_ids_in_inventory():
    """Return the fixture project's element IDs, read independently of pr.py."""
    return re.findall(r'^  - (PR-001\.\d+):', docs()[0], re.MULTILINE)


def test_element_numbers_are_never_reissued():
    """An element a sent CV cites keeps its number for good: a new element
    takes max+1 over the current and the retired ones, and an edit keeps the
    number it changes.
    """
    write_block('el.md', 'Schema-validated output, so a malformed record fails at conversion')
    assert ok('element', '--id', 'PR-001',
              '--text-file', os.path.join(RUN_DIR, 'el.md')) == 'PR-001.04'
    write_block('oc.md', 'Caught two malformed vendor files before load.')
    assert ok('element', '--id', 'PR-001.04',
              '--outcome-file', os.path.join(RUN_DIR, 'oc.md')) == 'PR-001.04'
    assert element_ids_in_inventory() == ['PR-001.01', 'PR-001.02', 'PR-001.03', 'PR-001.04']

    write_retired('PR-001.07')
    assert ok('element', '--id', 'PR-001',
              '--text-file', os.path.join(RUN_DIR, 'el.md')) == 'PR-001.08', \
        'a retired element number was reissued'


def test_elements_are_never_rewritten_as_a_field():
    """set rewrites a whole field, which would drop or renumber cited elements;
    changing the Objective must leave every element as it was."""
    before = element_ids_in_inventory()
    write_block('v.md', 'Let trial teams exchange study metadata without re-entry.')
    ok('set', '--id', 'PR-001', '--field', 'Objective',
       '--value-file', os.path.join(RUN_DIR, 'v.md'))
    assert element_ids_in_inventory() == before, 'Objective change touched the elements'
    out = fails('set', '--id', 'PR-001', '--field', 'Elements',
                '--value-file', os.path.join(RUN_DIR, 'v.md'))
    assert 'one element at a time' in out, out


def test_new_project_cannot_bring_its_own_element_numbers():
    """A new project's elements are numbered by the element command, never by
    hand, so a pasted block cannot carry numbers that collide or skip."""
    write_block('p.md', PR_SECOND_BLOCK.split('\n', 1)[1] + '  - PR-002.01: Pasted element\n')
    out = fails('insert', '--prefix', 'PR',
                '--block-file', os.path.join(RUN_DIR, 'p.md'))
    assert 'element command' in out, out


def test_element_lookup_and_retired_fallback():
    """An element is read with its project; a retired one still resolves, so an
    interview-prep run for a CV already sent can trace its citations."""
    code, out = run('profile_slice.py', 'id', 'PR-001.02')
    assert code == 0, out
    assert 'Objective:' in out and 'PR-001.02:' in out and 'PR-001.01:' not in out, out

    code, out = run('profile_slice.py', 'id', 'PR-001.07')
    assert code != 0, f'a missing element resolved with no retired row:\n{out}'
    write_retired('PR-001.07')
    code, out = run('profile_slice.py', 'id', 'PR-001.07')
    assert code == 0 and 'RETIRED' in out, out


def test_retrieval_scores_objective_and_each_element():
    """A project is scored as its objective plus one item per element, each led
    by the project name and carrying the project's role."""
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, 'retrieval_payload.py'), 'inventory'],
        capture_output=True, text=True, encoding='utf-8', cwd=SCRIPTS_DIR)
    assert result.returncode == 0, result.stderr
    items = {e['id']: e for e in json.loads(result.stdout)['entries']}
    expected = ['PR-001'] + element_ids_in_inventory()
    assert [i for i in items if i.startswith('PR-')] == expected, list(items)
    for item_id in expected:
        assert items[item_id]['payload'].startswith('Open Trial Metadata Toolkit: '), items[item_id]
        assert items[item_id]['role'] == 'RL-002', items[item_id]


def test_retrieval_scores_hands_on_tools():
    """An entry's Hands-on Tools reach the scored payload, so a job naming a
    tool can match the entry that used it."""
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, 'retrieval_payload.py'), 'inventory'],
        capture_output=True, text=True, encoding='utf-8', cwd=SCRIPTS_DIR)
    assert result.returncode == 0, result.stderr
    items = {e['id']: e for e in json.loads(result.stdout)['entries']}
    payload = items['EX-001']['payload']
    assert payload.endswith('Hands-on Tools: SQL Server, Python.'), payload
    assert 'Hands-on Tools' not in items['EX-002']['payload'], items['EX-002']


def cv_qc_report(cv_text, with_gap=False):
    """Run cv_qc.py on a CV text; return {check id: (passed, detail)}."""
    path = write_block('cv_content.md', cv_text)
    root, cfg = _config.load()
    profile = os.path.join(root, cfg['paths']['profile'])
    extra = ['--gap-analysis', os.path.join(FIXTURE_APP, 'gap_analysis.md')] if with_gap else []
    code, out = run('cv_qc.py', '--cv-file', path, '--level', 'ic',
                    '--inventory', os.path.join(profile, 'inventory.md'),
                    '--narratives', os.path.join(profile, 'narratives.md'), *extra)
    assert code == 0, out
    return {c['id']: (c['passed'], c['detail']) for c in json.loads(out)['checks']}


def test_cv_gap_citations_resolve_to_a_closed_requirement():
    """#70: a fact surfaced in the gap analysis but not yet in the inventory is
    cited as GAP CR-NNN. The citation must name a requirement the user closed
    or partly matched, and cannot pass unverified."""
    cv = ('## Professional Summary\nText. <!-- src: EX-001 -->\n\n'
          '## Professional Experience\n- A. <!-- src: GAP CR-002 -->\n'
          '- B. <!-- src: GAP CR-004 -->\n')
    assert cv_qc_report(cv, with_gap=True)['C9'][0], 'closed and partial-match citations failed'
    unverified = cv_qc_report(cv)['C9']
    assert not unverified[0] and 'no --gap-analysis' in unverified[1], unverified
    for cr in ('CR-005', 'CR-099'):
        bad = cv_qc_report(cv.replace('GAP CR-004', f'GAP {cr}'), with_gap=True)['C9']
        assert not bad[0] and cr in bad[1], bad


def test_staged_items_anchor_to_a_real_requirement():
    """With closure refs gone, the staged item's Requirement anchor is the link a
    GAP CR-NNN citation depends on, so it must name a requirement that exists."""
    def g7():
        _, out = run('gap_qc.py', 'check', '--folder', FIXTURE_APP)
        return next(line for line in out.split('\n') if line.startswith('G7'))
    assert 'PASS' in g7(), g7()
    root, cfg = _config.load()
    path = pu._staging_path(root, cfg)
    _util.write(path, _util.read(path).replace('CR-002 - Vendor', 'CR-099 - Vendor'))
    assert 'FAIL' in g7() and 'CR-099' in g7(), g7()


def test_cv_cites_real_elements_with_their_objective():
    """A made-up element must fail like a made-up entry; an element cited
    without its project fails; the same element twice as a bullet's only
    source is a duplicate."""
    report = cv_qc_report(
        '## Professional Summary\nText. <!-- src: EX-001 -->\n\n## Selected Projects\n'
        '- A. <!-- src: PR-001, PR-001.99 -->\n'
        '- B. <!-- src: PR-001.01 -->\n'
        '- C. <!-- src: PR-001, PR-001.02 -->\n'
        '- D. <!-- src: PR-001, PR-001.02 -->\n')
    assert not report['C3'][0] and 'PR-001.99' in report['C3'][1], report['C3']
    assert not report['C8'][0] and 'PR-001.01' in report['C8'][1], report['C8']
    assert not report['N2'][0] and 'PR-001.02' in report['N2'][1], report['N2']

    clean = cv_qc_report(
        '## Professional Summary\nText. <!-- src: EX-001 -->\n\n## Selected Projects\n'
        '- A. <!-- src: PR-001, PR-001.01 -->\n- B. <!-- src: PR-001, PR-001.02 -->\n')
    for check in ('C3', 'C8', 'N2'):
        assert clean[check][0], clean[check]


def test_gap_and_retrieval_qc_catch_a_made_up_element():
    """Before, PR-001.99 read as PR-001 and passed as a real ID."""
    path = os.path.join(FIXTURE_APP, 'gap_analysis.md')
    _util.write(path, _util.read(path).replace('**Evidence:** EX-003',
                                               '**Evidence:** EX-003, PR-001.99'))
    code, out = run('gap_qc.py', 'check', '--folder', FIXTURE_APP)
    g8 = next(line for line in out.split('\n') if line.startswith('G8'))
    assert 'FAIL' in g8 and 'PR-001.99' in g8, g8

    _util.write(os.path.join(FIXTURE_APP, 'retrieval.md'),
                '# Retrieval Manifest\n\nCites PR-001.02 and PR-001.99.\n')
    code, out = run('retrieval_qc.py', 'check', '--folder', FIXTURE_APP)
    r7 = next(line for line in out.split('\n') if line.startswith('R7'))
    assert 'FAIL' in r7 and 'PR-001.99' in r7 and 'PR-001.02' not in r7, r7


def test_objective_and_element_share_qc_scope():
    """A run that wrote a project owns findings on its elements, and a run that
    wrote an element owns findings on its project; a run that touched only an
    unrelated entry owns neither."""
    root, cfg = _config.load()
    path = pu._inventory_path(root, cfg)
    pristine = _util.read(path)
    cases = [
        # A duplicate element is reported on the element ID.
        (pristine.replace('  - PR-001.02:', '  - PR-001.01:'), 'PR-001'),
        # A stray Outcome is reported on the project ID.
        (pristine.replace('Elements:\n', 'Elements:\n    Outcome: Stray result.\n'), 'PR-001.01'),
    ]
    for broken, scope in cases:
        _util.write(path, broken)
        code, out = run('profile_update_qc.py', 'check', '--scope-id', scope)
        assert code != 0, f'a related finding did not fail a run scoped to {scope}:\n{out}'
        code, out = run('profile_update_qc.py', 'check', '--scope-id', 'EX-001')
        assert code == 0, f'a project finding failed a run scoped to EX-001:\n{out}'
    _util.write(path, pristine)


# ---------------------------------------------------------------------------
# Retrieval scoring context
# The scorer's requirements and JD reach it through a file the split script
# writes, never through a hand-composed prompt. These checks hold the script
# to copying both verbatim and to refusing when either is absent. The expected
# text is extracted independently here, so a bug in the script's own section
# parser cannot also hide in the check.
# ---------------------------------------------------------------------------

FIXTURE_APP = os.path.join(RUN_DIR, 'applications', 'aldridge_APP-001_2026-01')
FIXTURE_PREFIX = 'aldridge_APP-001'


def split_fixture_payloads():
    """Build the three payloads, run split; return (returncode, output, scratch)."""
    scratch = os.path.join(FIXTURE_APP, 'scratch')
    os.makedirs(scratch, exist_ok=True)
    for corpus in ('inventory', 'narratives', 'themes'):
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, 'retrieval_payload.py'), corpus],
            capture_output=True, text=True, encoding='utf-8', cwd=SCRIPTS_DIR)
        assert result.returncode == 0, f'{corpus} payload failed:\n{result.stderr}'
        _util.write(os.path.join(scratch, f'{FIXTURE_PREFIX}_{corpus}_payload.json'),
                    result.stdout)
    code, out = run('retrieval_payload.py', 'split', '--slug', 'aldridge',
                    '--app-id', 'APP-001', '--folder', FIXTURE_APP, '--temp-dir', scratch)
    return code, out, scratch


def test_scorer_context_is_copied_verbatim():
    """Shipped 2026-10-14 (APP-023): scorer prompts were composed by hand, and
    the requirements and JD arrived as file paths, then as a summarised JD.

    The split script now copies both into one context file and prints every
    prompt, so the check is that the copy is exact and every prompt names it.
    """
    code, out, scratch = split_fixture_payloads()
    assert code == 0, f'split failed:\n{out}'
    context_path = os.path.join(scratch, f'{FIXTURE_PREFIX}_scoring_context.md')
    context = _util.read(context_path)

    research = _util.read(os.path.join(FIXTURE_APP, 'research.md'))
    requirements = research.split('## Critical Requirements\n', 1)[1] \
                           .split('\n## ', 1)[0].strip('\n')
    jd = _util.read(os.path.join(FIXTURE_APP, 'jd.md')).strip('\n')
    assert requirements in context, 'Critical Requirements not copied verbatim'
    assert jd in context, 'JD not copied verbatim'
    assert context.index(requirements) < context.index('## Job Description'), \
        'the JD must follow the requirements so its headings cannot cut them'

    # One prompt per chunk plus themes, each naming the context file and a real input.
    prompts = out.split('=== PROMPT ')[1:]
    chunks = [f for f in os.listdir(scratch)
              if f.startswith(f'{FIXTURE_PREFIX}_inv_chunk')
              or f.startswith(f'{FIXTURE_PREFIX}_narr_chunk')]
    assert len(prompts) == len(chunks) + 1, f'{len(prompts)} prompts for {len(chunks)} chunks + themes'
    for prompt in prompts:
        assert f'Context file: {context_path}' in prompt, f'prompt lacks the context file:\n{prompt}'
        input_path = prompt.split('Input file: ', 1)[1].split('\n', 1)[0]
        assert os.path.isfile(input_path), f'prompt names a missing input: {input_path}'


def chunk_entries(scratch, kind):
    """Return [(chunk file name, entries)] for the inv or narr chunk files, in order."""
    out, i = [], 0
    while os.path.exists(path := os.path.join(scratch, f'{FIXTURE_PREFIX}_{kind}_chunk{i}.json')):
        with open(path, encoding='utf-8') as f:
            out.append((os.path.basename(path), json.load(f)['entries']))
        i += 1
    return out


def test_inventory_chunks_carry_only_what_the_scorer_reads():
    """Found 2026-10-27: inventory chunk files carried every entry's axis tags,
    role, and a second copy of Description and Impact beside the payload, about
    60% of each scorer's read, all of which the scorer is told to ignore."""
    code, out, scratch = split_fixture_payloads()
    assert code == 0, f'split failed:\n{out}'
    with open(os.path.join(scratch, f'{FIXTURE_PREFIX}_inventory_payload.json'),
              encoding='utf-8') as f:
        expected = [e['id'] for e in json.load(f)['entries']]
    chunks = chunk_entries(scratch, 'inv')
    assert chunks, 'split wrote no inventory chunk files'
    for name, entries in chunks:
        extra = {k for e in entries for k in e} - {'id', 'payload'}
        assert not extra, f'{name} carries fields the scorer ignores: {sorted(extra)}'
    written = [e['id'] for _, entries in chunks for e in entries]
    assert written == expected, f'chunks lost, repeated, or reordered items: {written}'


def write_fake_scores(scratch):
    """Write a score file for every chunk split wrote, scoring each item 0.5."""
    def score(entries):
        return [{'id': e['id'], 'score': 0.5, 'reason': 'Test.'} for e in entries]
    for kind, out_kind in (('inv', 'inventory_chunk'), ('narr', 'narr_chunk')):
        for i, (_, entries) in enumerate(chunk_entries(scratch, kind)):
            _util.write(os.path.join(scratch, f'{FIXTURE_PREFIX}_scores_{out_kind}{i}.json'),
                        json.dumps({'corpus': kind, 'scores': score(entries)}))
    with open(os.path.join(scratch, f'{FIXTURE_PREFIX}_themes_payload.json'),
              encoding='utf-8') as f:
        themes = json.load(f)['entries']
    _util.write(os.path.join(scratch, f'{FIXTURE_PREFIX}_scores_themes.json'),
                json.dumps({'corpus': 'themes', 'scores': score(themes)}))


def merge(scratch):
    """Run retrieval_score_merge.py on the fixture scratch dir."""
    return run('retrieval_score_merge.py', '--slug', 'aldridge', '--app-id', 'APP-001',
               '--temp-dir', scratch)


def test_inventory_merge_refuses_a_duplicate_or_missing_score():
    """Found 2026-10-27: two live entries shared EX-231 and the inventory merge
    accepted both scores, where the narrative merge would have refused. Every
    payload item must be scored exactly once."""
    code, out, scratch = split_fixture_payloads()
    assert code == 0, f'split failed:\n{out}'
    write_fake_scores(scratch)
    code, out = merge(scratch)
    assert code == 0, f'a complete scoring failed to merge:\n{out}'

    path = os.path.join(scratch, f'{FIXTURE_PREFIX}_scores_inventory_chunk0.json')
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    complete = list(data['scores'])
    for broken, expect in ((complete + complete[:1], 'duplicate'), (complete[1:], 'unscored')):
        _util.write(path, json.dumps({**data, 'scores': broken}))
        code, out = merge(scratch)
        assert code != 0 and expect in out, f'the merge accepted a {expect} score:\n{out}'


def test_split_refuses_without_requirements():
    """A context file with no requirements would score every entry against
    nothing; split must stop instead of writing one."""
    path = os.path.join(FIXTURE_APP, 'research.md')
    research = _util.read(path)
    _util.write(path, research.split('## Critical Requirements', 1)[0]
                + '## Axis Gaps\n\nNone.\n')
    code, out, _ = split_fixture_payloads()
    assert code != 0, f'split wrote a context with no requirements:\n{out}'
    assert 'Critical Requirements' in out, out


# ---------------------------------------------------------------------------
# Gap-detector context
# The detector's requirements, role context, and the inventory sections that
# retrieval never scores reach it through a file gap_context.py writes. The
# expected text is again extracted independently of the script's parser.
# ---------------------------------------------------------------------------

def build_detector_context():
    """Run gap_context.py build on the fixture; return (returncode, output, scratch)."""
    scratch = os.path.join(FIXTURE_APP, 'scratch')
    # The manifest's content is not read by the build; it only has to exist.
    _util.write(os.path.join(FIXTURE_APP, 'retrieval.md'), '# Retrieval Manifest\n')
    code, out = run('gap_context.py', 'build', '--folder', FIXTURE_APP, '--temp-dir', scratch)
    return code, out, scratch


def h2_bodies(text):
    """Return {heading: body} for every '## ' section, bodies trimmed of blank edges."""
    parts = ('\n' + text).split('\n## ')[1:]
    return {p.split('\n', 1)[0].strip(): (p.split('\n', 1) + [''])[1].strip('\n')
            for p in parts}


def test_detector_context_carries_unscored_profile_sections():
    """Shipped 2026-10-14 (APP-023): the gap-detector was left to find the
    systems list in a full-file read, missed it, and reported the candidate's
    Veeva use as eTMF-only although the Technical Experience section listed
    four other Veeva products.
    """
    code, out, scratch = build_detector_context()
    assert code == 0, f'build failed:\n{out}'
    context_path = os.path.join(scratch, 'gap_detector_context.md')
    context = _util.read(context_path)

    research = h2_bodies(_util.read(os.path.join(FIXTURE_APP, 'research.md')))
    assert research['Critical Requirements'] in context, 'requirements not copied verbatim'
    for name in ('Role', 'Company', 'Industry'):
        assert research[name] in context, f'{name} context not copied verbatim'

    root, cfg = _config.load()
    inventory = h2_bodies(_util.read(pu._inventory_path(root, cfg)))
    unscored = {h: b for h, b in inventory.items() if h != 'Table of Contents'
                and not any(line.startswith(('ID: EX-', 'ID: PR-', 'ID: PB-', 'ID: PS-'))
                            for line in b.split('\n'))}
    assert 'Technical Experience' in unscored, 'fixture lost its Technical Experience section'
    for heading, body in unscored.items():
        assert f'## {heading}\n\n{body}' in context, f'"{heading}" not copied verbatim'
    assert '## Experience Entries' not in context, 'a scored section leaked into the context'

    assert f'Context file: {context_path}' in out, f'prompt lacks the context file:\n{out}'


def test_detector_context_refuses_without_requirements():
    """No requirements means nothing to judge against; build must stop."""
    path = os.path.join(FIXTURE_APP, 'research.md')
    research = _util.read(path)
    _util.write(path, research.split('## Critical Requirements', 1)[0]
                + '## Axis Gaps\n\nNone.\n')
    code, out, _ = build_detector_context()
    assert code != 0, f'build wrote a context with no requirements:\n{out}'
    assert 'Critical Requirements' in out, out


# ---------------------------------------------------------------------------
# Section replacement
# Re-runs replace a session-log section in place. The new body is user and
# path text, so it must land literally rather than as a regex template.
# ---------------------------------------------------------------------------

def test_section_replace_keeps_backslashes_literal():
    """Shipped 2026-10-16 (APP-024): re-running retrieval died with 'bad escape
    \\U' because the replacement body held a Windows path (C:\\Users\\...) and
    was read as a regex template. First runs append, so only re-runs broke.
    """
    body = '## Retrieval\n\n- Manifest: C:\\Users\\cand\\retrieval.md\n- Ref: \\1 \\g<0>\n'
    path = write_block('section_body.md', body)
    for attempt in ('append', 'replace'):
        code, out = run('session_log.py', 'append-section', '--folder', FIXTURE_APP,
                        '--heading', 'Retrieval', '--body-file', path)
        assert code == 0, f'{attempt} failed:\n{out}'
    log = _util.read(os.path.join(FIXTURE_APP, 'session_log.md'))
    assert log.count('## Retrieval') == 1, 'replace stacked a second section'
    assert body.rstrip() in log, 'body was not written literally'


# ---------------------------------------------------------------------------
# Agent definitions
# Sub-agents run in their own context, so the global rules reach them only if
# the definition points there. Web-only agents cannot read files and are
# exempt; their per-fact source URLs carry the no-fabrication rule instead.
# ---------------------------------------------------------------------------

def test_file_reading_agents_load_global_rules():
    """Shipped 2026-10-16 (APP-025): the axis-classifier put outside knowledge
    of the company's drugs into an industry rationale, because nothing in its
    definition pointed it at rules/global-rules.md.
    """
    agents_dir = os.path.join(REPO_ROOT, '.claude', 'agents')
    missing = []
    for name in sorted(os.listdir(agents_dir)):
        if not name.endswith('.md'):
            continue
        text = _util.read(os.path.join(agents_dir, name))
        tools = next((ln for ln in text.splitlines() if ln.startswith('tools:')), '')
        if 'Read' in tools and 'rules/global-rules.md' not in text:
            missing.append(name)
    assert not missing, 'agents that can read files but never load the global rules: ' + ', '.join(missing)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    """Run every check against a fresh copy and report."""
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('--only', help='substring of the check name to run')
    args = parser.parse_args()

    # The copy has to exist before isolation can be proven, because the guard
    # in _config resolves against a real folder.
    reset()
    _assert_isolated()

    checks = [(name, fn) for name, fn in sorted(globals().items())
              if name.startswith('test_') and callable(fn)
              and (not args.only or args.only in name)]
    if not checks:
        print('no checks matched')
        return 1

    failures = []
    for name, fn in checks:
        reset()
        label = name[len('test_'):].replace('_', ' ')
        try:
            fn()
            print(f'  PASS  {label}')
        except Exception as exc:
            failures.append((label, exc))
            print(f'  FAIL  {label}')
            print('        ' + str(exc).replace('\n', '\n        '))
            if not isinstance(exc, AssertionError):
                print('        ' + traceback.format_exc().replace('\n', '\n        '))

    if os.path.isdir(RUN_DIR):
        shutil.rmtree(RUN_DIR)

    print(f'\n{len(checks) - len(failures)}/{len(checks)} checks passed')
    print('FAIL' if failures else 'PASS')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
