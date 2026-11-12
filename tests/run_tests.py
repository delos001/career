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


def test_cv_bullets_sit_under_their_own_role():
    """Added 2026-11-05 (GitHub #11 follow-on): with every role now its own
    sub-entry, the likely error is a bullet under the wrong role's title. C5
    only counted titles against roles, and it counted the bold employer line as
    a title, so a block holding two roles' bullets under one title passed.
    """
    def cv(northwind_bullets, calder_title='Manager, Clinical Data Systems'):
        return ('## Professional Summary\nText. <!-- src: EX-001 -->\n\n'
                '## Professional Experience\n'
                '**Northwind Therapeutics** | Boston, MA | 2022 - 2025\n'
                '**Director, Data Platform Operations** (2022 - 2025) | Remote\n'
                f'{northwind_bullets}'
                '**Calder Bio** | Austin, TX | 2018 - 2022\n'
                f'**{calder_title}**\n'
                '- B. <!-- src: EX-002 -->\n')
    assert cv_qc_report(cv('- A. <!-- src: EX-004 -->\n'))['C5'][0], 'a correct CV failed'
    wrong = cv_qc_report(cv('- A. <!-- src: EX-004 -->\n- C. <!-- src: EX-001 -->\n'))['C5']
    assert not wrong[0] and 'EX-001' in wrong[1], f'bullet under the wrong role passed: {wrong}'
    renamed = cv_qc_report(cv('- A. <!-- src: EX-004 -->\n', calder_title='Data Lead'))['C5']
    assert not renamed[0] and 'Data Lead' in renamed[1], f'unknown title passed: {renamed}'


def test_cv_summary_carries_no_figures():
    """Decided 2026-11-05 (GitHub #12): the summary rolls impact up into words;
    figures stay in their bullets. The only number allowed is the career span.
    """
    def summary(text):
        return cv_qc_report(f'## Professional Summary\n{text} <!-- src: EX-001 -->\n\n'
                            '## Professional Experience\n- A. <!-- src: EX-001 -->\n')['S4']
    ok = summary('Leader with 25+ years and a 20-year record, saving millions on a '
                 'Phase 3 program under 21 CFR Part 11 and ICH E6(R3) with USDM v4.')
    assert ok[0], f'career span, words, or a name flagged: {ok}'
    for figure, digits in (('60%', '60'), ('$1M', '1'), ('30+ CRAs', '30'), ('roughly 10 studies', '10')):
        result = summary(f'Leader with 25+ years who delivered {figure} across programs.')
        assert not result[0] and digits in result[1], f'{figure} passed: {result}'


def test_cv_section_order_comes_from_the_rule_file():
    """Fixed 2026-11-05 (GitHub #21): cv_qc.py kept its own copy of the CV
    section list, which had already drifted from cv-structure.md (Earlier
    Professional Roles, the required set). The script now reads the rule's
    Section order block, so changing the block changes the check.
    """
    import cv_qc
    root, cfg = _config.load()
    rule = _util.read(os.path.join(root, cfg['paths']['cv_rules'], cfg['filenames']['cv_structure_file']))
    live = cv_qc.parse_section_order(rule)
    assert 'earlier professional roles' in live['order'], live
    assert live['required'] == {'professional summary', 'core competencies',
                                'professional experience', 'education'}, live['required']
    cv = ('## Professional Summary\nA.\n\n## Core Competencies\n- a\n\n'
          '## Professional Experience\n- b\n\n## Selected Projects\n- c\n')
    sections = cv_qc._split_sections(cv, live)
    assert not cv_qc._check_s2_required_sections(sections, live)['passed'], 'missing Education passed'
    relaxed = cv_qc.parse_section_order(rule.replace('- Education (required)', '- Education'))
    assert cv_qc._check_s2_required_sections(sections, relaxed)['passed'], 'block edit did not reach the check'
    assert any(norm == 'work-output' for _, norm, _ in sections), 'Selected Projects not read as work output'


def test_every_interview_audience_has_a_rule_file_and_stage_label():
    """Fixed 2026-11-05 (GitHub #62): a recruiter round after a hiring-manager
    round had no rule file to load and no stage label, so the skill choice was made
    by hand mid-run. Every rule file must be offered at intake, and every audience
    offered must have a file with the same sections as its siblings.
    """
    root, cfg = _config.load()
    folder = os.path.join(root, cfg['paths']['rules'], 'interview-types')
    files = {name[:-3] for name in os.listdir(folder) if name.endswith('.md')}
    skill = _util.read(os.path.join(root, '.claude', 'skills', 'preparation-interview', 'SKILL.md'))
    intake = re.search(r'- Audience \(rule-file key -> stage label\): (.+?)\. The key', skill)[1]
    offered = dict(pair.split(' -> ') for pair in intake.split(', '))
    assert set(offered) == files, f'intake offers {sorted(offered)}, rule files are {sorted(files)}'
    assert offered['recruiter'] == 'Recruiter Screen', offered

    def headings(name):
        return re.findall(r'(?m)^## (.+)$', _util.read(os.path.join(folder, f'{name}.md')))
    assert headings('recruiter') == headings('hiring-manager'), headings('recruiter')

    screen = _util.read(os.path.join(root, '.claude', 'skills', 'preparation-screen', 'SKILL.md'))
    assert 'rules/interview-types/recruiter.md' in screen, 'the screen skill must read the shared rule file'
    assert 'other than Recruiter Screen' in screen, 'the screen skill must hand off a late recruiter round'
    assert 'hold for later rounds' not in screen, 'recruiter emphasis must live only in the rule file'


def test_length_finding_names_the_cheapest_lines_to_recover():
    """Fixed 2026-11-05 (GitHub #61): on APP-020 the writer trimmed against its
    own line model and counted citations, burning two QC rounds; five bullets
    shortened slightly recovered the five lines needed. A length finding now names
    those bullets, citations cost nothing, and the rules' numbers match the code.
    """
    import cv_measure
    import cv_qc
    capacity = cv_qc.CHARS_PER_LINE_BULLET
    cheap, costly, short = 'a' * (capacity + 3), 'b' * (capacity + 60), 'c' * 40
    cv = (f'## Professional Experience\n- {costly} <!-- src: EX-001 -->\n'
          f'- {cheap} <!-- src: EX-002, EX-003, EX-004, EX-005, EX-006, EX-007 -->\n'
          f'- {short} <!-- src: {"EX-008, " * 30}EX-009 -->\nA plain line {"d" * 200}\n')
    found = cv_measure.trim_candidates(cv, 1)
    assert [c['chars_to_save_a_line'] for c in found] == [3, 60], f'citations or prose were counted: {found}'
    assert found[0]['bullet'] == cheap[:60], found
    many = '\n'.join(f'- {"e" * (capacity + i)}' for i in range(1, 20))
    assert len(cv_measure.trim_candidates(many, 2)) == 7, 'the list should stay near the overage'

    root, cfg = _config.load()
    rules = _util.read(os.path.join(root, cfg['paths']['cv_rules'], cfg['filenames']['cv_structure_file']))
    usable = re.search(r'Usable lines per page: ~(\d+) \(page 1.*?~(\d+) \(later', rules)
    chars = re.search(r'Characters per line at wrap: ~(\d+) full-width; bullets ~(\d+)', rules)
    assert (int(usable[1]), int(usable[2])) == (cv_qc.USABLE_LINES_PAGE_1, cv_qc.USABLE_LINES_LATER), usable[0]
    assert (int(chars[1]), int(chars[2])) == (cv_qc.CHARS_PER_LINE_FULL, cv_qc.CHARS_PER_LINE_BULLET), chars[0]

    architect = _util.read(os.path.join(root, '.claude', 'agents', 'cv-architect.md'))
    assert 'estimated_pages' not in architect, 'the writer must not keep a second page estimate'
    assert 'cost no length' in architect, 'the writer must be told citations are free'


def test_cv_length_is_measured_not_estimated():
    """Fixed 2026-11-05 (GitHub #17): the L1 estimate passed CVs that rendered
    4-9 lines over, and once cut a vetted bullet for an estimated 2-line
    overage. cv_measure.py asks Word; the trim decision rests on that.
    """
    import cv_measure
    assert cv_measure.assess(3, 0, 3)['fits']
    over = cv_measure.assess(4, 7, 3)
    assert over['fits'] is False and over['lines_over'] == 7, over
    gone = cv_measure.unmeasured(3, 'no Word')
    assert gone['measured'] is False and gone['fits'] is None, 'an unmeasured CV must not read as over'
    # Real measurement where Word is available; skipped elsewhere.
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        return
    cv = write_block('measure_cv.md', '# Name\nCity, ST | a@b.c\n\n## Professional Summary\nShort. <!-- src: EX-001 -->\n')
    code, out = run('cv_measure.py', '--cv-file', cv, '--level', 'ic', '--scratch-dir', RUN_DIR)
    assert code == 0, out
    # run() appends stderr (the builder's 'Saved:' line); the JSON is the line that opens with '{'.
    result = json.loads(next(line for line in out.splitlines() if line.startswith('{')))
    assert result['measured'] is False or (result['pages'] == 1 and result['fits']), result


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


def split_fixture_payloads(*extra):
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
                    '--app-id', 'APP-001', '--folder', FIXTURE_APP, '--temp-dir', scratch, *extra)
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

    import requirement_kinds
    _, cfg = _config.load()
    requirements = requirement_kinds.requirements_table(FIXTURE_APP, cfg, demand=False)
    jd = _util.read(os.path.join(FIXTURE_APP, 'jd.md')).strip('\n')
    assert requirements in context, 'the requirements table is not in the context'
    # The scorer judges evidence strength only, so it never sees Demand.
    assert '| 6 | Familiarity with regulatory submission data packages | L27 Nice to have |' in context, context
    assert 'preferred' not in requirements and 'required' not in requirements, 'the scorer was shown Demand'
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
    os.remove(os.path.join(FIXTURE_APP, 'jd_needs.md'))
    code, out, _ = split_fixture_payloads()
    assert code != 0, f'split wrote a context with no requirements:\n{out}'
    assert 'jd_needs.md' in out, out


# ---------------------------------------------------------------------------
# Cross-chunk score calibration
# Found 2026-11-04 (APP-027): each inventory chunk has its own scorer, and one
# chunk ran 0.15-0.40 below another on near-identical entries, moving entries
# between rank ~95 and the top 15 by chunk alone. Every chunk now also scores
# the same anchors, picked from a seed chunk's scores, and the merge maps each
# chunk onto one scale. The fixture is forced into several chunks with a small
# byte budget. True scores spread evenly from 0.15 to 0.85 across the payload.
# ---------------------------------------------------------------------------

def true_scores(scratch):
    """Return {id: true score} spread evenly across the inventory payload."""
    with open(os.path.join(scratch, f'{FIXTURE_PREFIX}_inventory_payload.json'),
              encoding='utf-8') as f:
        ids = [e['id'] for e in json.load(f)['entries']]
    return {i: round(0.15 + 0.7 * k / (len(ids) - 1), 3) for k, i in enumerate(ids)}


def write_chunk_scores(scratch, chunk, true, slope=1.0, offset=0.0):
    """Score one inventory chunk as slope x true + offset."""
    entries = chunk_entries(scratch, 'inv')[chunk][1]
    _util.write(os.path.join(scratch, f'{FIXTURE_PREFIX}_scores_inventory_chunk{chunk}.json'),
                json.dumps({'corpus': 'inventory', 'scores': [
                    {'id': e['id'], 'score': round(slope * true[e['id']] + offset, 2),
                     'reason': 'Test.'} for e in entries]}))


def split_synthetic(n_items=30, chunk_bytes='800'):
    """Run split on a synthetic n-item inventory payload; return the scratch dir.

    The fixture inventory (9 items) is too small to give both a seed of
    several items and three or more chunks, so the inventory payload split
    reads is replaced with n uniform items. Narratives and themes stay real.
    """
    code, out, scratch = split_fixture_payloads()
    assert code == 0, f'split failed:\n{out}'
    entries = [{'id': f'EX-{100 + k}', 'payload': f'Synthetic entry {k} ' + 'x' * 60}
               for k in range(n_items)]
    _util.write(os.path.join(scratch, f'{FIXTURE_PREFIX}_inventory_payload.json'),
                json.dumps({'corpus': 'inventory', 'entry_count': n_items, 'entries': entries}))
    code, out = run('retrieval_payload.py', 'split', '--slug', 'aldridge', '--app-id', 'APP-001',
                    '--folder', FIXTURE_APP, '--temp-dir', scratch, '--inv-chunk-bytes', chunk_bytes)
    assert code == 0, f'split failed on the synthetic payload:\n{out}'
    return scratch


def split_multichunk(distort=((1.0, 0.0),)):
    """Run both split stages with every chunk scored per distort[chunk].

    Returns (scratch, true scores, split-anchored output). The seed is scored
    before split-anchored, as in a live run; the rest after.
    """
    scratch = split_synthetic()
    write_fake_scores(scratch)  # narratives and themes; inventory is overwritten below
    true = true_scores(scratch)
    write_chunk_scores(scratch, 0, true, *distort[0])
    code, anchored = run('retrieval_payload.py', 'split-anchored', '--slug', 'aldridge',
                         '--app-id', 'APP-001', '--temp-dir', scratch, '--inv-anchors', '4')
    assert code == 0, f'split-anchored failed:\n{anchored}'
    for c in range(1, len(chunk_entries(scratch, 'inv'))):
        write_chunk_scores(scratch, c, true, *distort[c % len(distort)])
    return scratch, true, anchored


def inventory_anchors(scratch):
    """Return the inventory anchor IDs split-anchored recorded."""
    return _util.load_json(os.path.join(
        scratch, f'{FIXTURE_PREFIX}_calibration.json'))['inventory']['anchors']


def test_seed_spans_the_corpus_and_anchors_reach_every_chunk():
    """The seed must sample the whole corpus, the anchors must span the seed's
    scores top to bottom, and every chunk must score every anchor exactly once
    while every other item is scored once, the non-seed chunks in order."""
    scratch, true, _ = split_multichunk()
    with open(os.path.join(scratch, f'{FIXTURE_PREFIX}_inventory_payload.json'),
              encoding='utf-8') as f:
        order = [e['id'] for e in json.load(f)['entries']]
    chunks = chunk_entries(scratch, 'inv')
    assert len(chunks) >= 3, f'fixture split into only {len(chunks)} chunks'
    seed_ids = [e['id'] for e in chunks[0][1]]
    positions = sorted(order.index(i) for i in seed_ids)
    assert positions[0] < len(order) / 3 and positions[-1] >= 2 * len(order) / 3, \
        f'seed is not a spread sample of the corpus: positions {positions} of {len(order)}'

    anchors = inventory_anchors(scratch)
    assert len(anchors) == 4 and set(anchors) <= set(seed_ids), f'anchors not from the seed: {anchors}'
    seed_true = {i: true[i] for i in seed_ids}
    for extreme in (max(seed_true, key=seed_true.get), min(seed_true, key=seed_true.get)):
        assert extreme in anchors, f"anchors miss the seed's extreme {extreme}: {anchors}"
    for name, entries in chunks:
        ids = [e['id'] for e in entries]
        bad = [a for a in anchors if ids.count(a) != 1]
        assert not bad, f'{name} does not score each anchor once: {bad}'

    rest = [e['id'] for _, entries in chunks[1:] for e in entries if e['id'] not in seed_ids]
    assert sorted(seed_ids + rest) == sorted(order), 'items lost or repeated across chunks'
    assert rest == [i for i in order if i not in seed_ids], f'non-seed chunks reordered: {rest}'


def test_merge_maps_drifted_chunks_onto_one_scale():
    """Chunks scored with different slopes and offsets must merge to one scale:
    the same true score lands on the same corrected score whatever its chunk."""
    distort = [(1.0, 0.0), (0.8, -0.05), (1.15, 0.0), (0.9, 0.06)]
    scratch, true, _ = split_multichunk(distort)
    code, out = merge(scratch)
    assert code == 0, f'merge failed:\n{out}'

    n = len(chunk_entries(scratch, 'inv'))
    used = [distort[c % len(distort)] for c in range(n)]
    common_slope = sum(s for s, _ in used) / n
    common_offset = sum(o for _, o in used) / n
    merged = _util.load_json(os.path.join(scratch, f'{FIXTURE_PREFIX}_inventory_scores.json'))
    off = [(s['id'], s['score'], round(common_slope * true[s['id']] + common_offset, 2))
           for s in merged['scores']
           if abs(s['score'] - (common_slope * true[s['id']] + common_offset)) > 0.02]
    assert not off, f'scores not on one scale (id, merged, expected): {off}'
    record = merged['calibration']
    assert record['status'] == 'applied' and record['after'] < record['before'], record


def test_merge_keeps_the_rows_each_entry_matches():
    """Built 2026-11-11: the scorer now names the requirement rows each entry
    matches, and retrieval_apply.py maps them to needs. They must come through
    calibration: whole for an ordinary entry, and for an anchor scored in every
    chunk, the rows of the one copy the merge keeps (never a mix or nothing).
    """
    scratch, _, _ = split_multichunk([(1.0, 0.0), (0.8, -0.05), (1.15, 0.0)])
    anchors = set(inventory_anchors(scratch))
    written = {}
    for c in range(len(chunk_entries(scratch, 'inv'))):
        path = os.path.join(scratch, f'{FIXTURE_PREFIX}_scores_inventory_chunk{c}.json')
        data = _util.load_json(path)
        for s in data['scores']:
            # An anchor gets different rows in each chunk; anything else one fixed set.
            s['rows'] = [c + 1] if s['id'] in anchors else [int(s['id'][3:]) % 5 + 1, 6]
            written.setdefault(s['id'], []).append(s['rows'])
        _util.write(path, json.dumps(data))
    code, out = merge(scratch)
    assert code == 0, f'merge failed:\n{out}'
    merged = {s['id']: s.get('rows') for s in _util.load_json(
        os.path.join(scratch, f'{FIXTURE_PREFIX}_inventory_scores.json'))['scores']}
    lost = [i for i in written if i not in anchors and merged.get(i) != written[i][0]]
    assert not lost, f'rows lost or changed in the merge: {lost}'
    bad = [a for a in anchors if merged.get(a) not in written[a]]
    assert not bad, f'an anchor kept rows no chunk gave it: {[(a, merged.get(a)) for a in bad]}'


def test_merge_refuses_uncalibratable_scores():
    """Three ways a merge would otherwise publish unaligned scores: an anchor
    absent from a chunk, a chunk that ranks the anchors backwards, and a run
    whose second split stage never happened. Each must stop the merge."""
    scratch, true, _ = split_multichunk()
    anchors = inventory_anchors(scratch)
    path = os.path.join(scratch, f'{FIXTURE_PREFIX}_scores_inventory_chunk1.json')
    pristine = _util.read(path)

    data = json.loads(pristine)
    _util.write(path, json.dumps({**data, 'scores': [s for s in data['scores']
                                                    if s['id'] != anchors[0]]}))
    code, out = merge(scratch)
    assert code != 0 and 'anchor' in out, f'the merge accepted a chunk missing an anchor:\n{out}'

    _util.write(path, json.dumps({**data, 'scores': [
        {**s, 'score': round(1 - s['score'], 2)} for s in data['scores']]}))
    code, out = merge(scratch)
    assert code != 0 and 'slope' in out, f'the merge accepted a backwards chunk:\n{out}'

    _util.write(path, pristine)
    code, out = merge(scratch)
    assert code == 0, f'the restored scores failed to merge:\n{out}'
    scratch = split_synthetic()
    write_fake_scores(scratch)
    code, out = merge(scratch)
    assert code != 0 and 'pending' in out, f'the merge ran without split-anchored:\n{out}'


def test_retrieval_qc_checks_the_calibration_record():
    """A manifest merged without calibration, or still disagreeing after it,
    must fail R9; a calibrated one within tolerance must pass."""
    def r9(calibration_line):
        _util.write(os.path.join(FIXTURE_APP, 'retrieval.md'),
                    f'# Retrieval Manifest\n\n**Generated:** 2026-01-01\n\n{calibration_line}\n')
        _, out = run('retrieval_qc.py', 'check', '--folder', FIXTURE_APP)
        return next(line for line in out.split('\n') if line.startswith('R9'))

    good = ('**Calibration:** inventory applied (5 chunks, 10 anchors; anchor disagreement '
            '0.100 before / 0.020 after; leave-one-out 0.010); narratives not needed (1 chunk)')
    assert 'PASS' in r9(good), r9(good)
    for broken, expect in (
            ('', 'missing'),
            (good.replace('narratives not needed (1 chunk)', 'narratives not recorded'),
             'without calibration'),
            (good.replace('0.020 after', '0.200 after'), 'still disagree')):
        line = r9(broken)
        assert 'FAIL' in line and expect in line, f'R9 passed a bad record ({expect}): {line}'


def test_manifest_shows_the_needs_each_entry_serves():
    """Built 2026-11-11: the scorer capped evidence for duty-derived and
    contextual rows, so the job's top need (Jazz N-01) looked weakly evidenced.
    The scorer now judges evidence strength only and names the rows an entry
    matches; the script maps those rows to the ranked needs.
    """
    axes = write_block('axes.json', '{}')
    empty = write_block('empty_scores.json', '{"scores": []}')

    def assemble(rows):
        scores = write_block('inv_scores.json', json.dumps(
            {'scores': [{'id': 'EX-004', 'score': 0.8, 'rows': rows, 'reason': 'r'}]}))
        return run('retrieval_apply.py', 'assemble', '--folder', FIXTURE_APP, '--slug', 'x',
                   '--app-id', 'APP-001', '--date', '2026-01-01', '--jd-axes-file', axes,
                   '--inventory-scores-file', scores, '--narrative-scores-file', empty,
                   '--theme-scores-file', empty)

    code, out = assemble([4, 3, 1])
    assert code == 0, out
    row = next(line for line in _util.read(os.path.join(FIXTURE_APP, 'retrieval.md')).split('\n')
               if line.startswith('| EX-004 |'))
    assert '| N-01: 3; N-03: 4; Qual: 1 |' in row, f'needs not mapped in rank order: {row}'
    code, out = assemble([9])
    assert code != 0 and 'row(s) 9' in out, 'a row the ranking does not hold was accepted'
    code, out = assemble([])
    assert code == 0 and '| EX-004 |' in _util.read(os.path.join(FIXTURE_APP, 'retrieval.md')), out


def test_manifest_names_where_its_axes_came_from():
    """Found on APP-028: the manifest said its axes came from research.md, but
    they come from the session log, and research.md holds no classification.
    The label is built from config, and QC fails a manifest naming another source.
    """
    _, cfg = _config.load()
    log_name = cfg['filenames']['session_log_file']
    label = f'**JD axis classification (from {log_name}):**'
    empty = write_block('empty_scores.json', '{"scores": []}')
    axes = write_block('axes.json', '{}')
    code, out = run('retrieval_apply.py', 'assemble', '--folder', FIXTURE_APP, '--slug', 'x',
                    '--app-id', 'APP-001', '--date', '2026-01-01', '--jd-axes-file', axes,
                    '--inventory-scores-file', empty, '--narrative-scores-file', empty,
                    '--theme-scores-file', empty)
    assert code == 0, out
    path = os.path.join(FIXTURE_APP, 'retrieval.md')
    text = _util.read(path)
    assert label in text, f'the manifest does not name {log_name} as its axis source'

    def r1():
        _, qc_out = run('retrieval_qc.py', 'check', '--folder', FIXTURE_APP)
        return next(line for line in qc_out.split('\n') if line.startswith('R1'))

    # Empty scores leave the tables empty, so R1 fails on those regardless; only
    # its axis-classification finding is under test here.
    assert 'axis classification' not in r1(), r1()
    _util.write(path, text.replace(label, '**JD axis classification (from research.md):**'))
    assert 'axis classification' in r1(), f'QC passed a manifest naming the wrong source: {r1()}'


# ---------------------------------------------------------------------------
# Gap-detector context
# The detector's requirements, role context, and the inventory sections that
# retrieval never scores reach it through a file gap_context.py writes. The
# expected text is again extracted independently of the script's parser.
# ---------------------------------------------------------------------------

MANIFEST_INVENTORY = ('EX-003', 'EX-001', 'PR-001', 'PR-001.01', 'PB-001')
MANIFEST_NARRATIVES = ('ST-001', 'DC-001')


def write_manifest(inventory_ids=MANIFEST_INVENTORY, narrative_ids=MANIFEST_NARRATIVES):
    """Write a fixture retrieval.md whose two candidate tables list these IDs."""
    def rows(ids):
        return ''.join(f'| {i} | 0.50 | Test. |\n' for i in ids)
    _util.write(os.path.join(FIXTURE_APP, 'retrieval.md'),
                '# Retrieval Manifest\n\n## Inventory candidates\n\n'
                f'| ID | Semantic | Reason |\n|----|----|----|\n{rows(inventory_ids)}\n'
                '## Narratives\n\n'
                f'| ID | Semantic | Reason |\n|----|----|----|\n{rows(narrative_ids)}\n'
                '## Triggered themes\n\n| ID | Semantic |\n|----|----|\n| TH-001 | 0.50 |\n')


def build_detector_context(*extra, manifest=True):
    """Run gap_context.py build on the fixture; return (returncode, output, scratch)."""
    scratch = os.path.join(FIXTURE_APP, 'scratch')
    if manifest:
        write_manifest()
    code, out = run('gap_context.py', 'build', '--folder', FIXTURE_APP,
                    '--temp-dir', scratch, *extra)
    return code, out, scratch


def detector_evidence(scratch):
    """Return [(file name, text)] for the evidence files build wrote, in order."""
    out, i = [], 0
    while os.path.exists(path := os.path.join(scratch, f'gap_detector_evidence_{i}.md')):
        out.append((os.path.basename(path), _util.read(path)))
        i += 1
    return out


def expected_block(text, entry_id, narrative=False):
    """Return one entry's text as the detector should see it, cut independently.

    An inventory entry runs from its ID line to the next ID line, heading, or
    topic-group marker; a narrative runs from its '## ' heading to the next.
    """
    lines = text.split('\n')
    at = lines.index(f'ID: {entry_id}')
    if narrative:
        start = max(i for i in range(at) if lines[i].startswith('## '))
        end = next((i for i in range(at, len(lines)) if lines[i].startswith(('## ', '# '))),
                   len(lines))
    else:
        start = at
        end = next((i for i in range(at + 1, len(lines))
                    if lines[i].startswith(('ID: ', '#', '--- '))), len(lines))
    return '\n'.join(lines[start:end]).strip('\n')


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

    import requirement_kinds
    research = h2_bodies(_util.read(os.path.join(FIXTURE_APP, 'research.md')))
    table = requirement_kinds.requirements_table(FIXTURE_APP, _config.load()[1], by_need=True)
    assert table in context, 'the requirements table is not in the context'
    assert table.split('\n')[2].startswith('| 3 | N-01 '), f'the detector table is not in need rank order: {table}'
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
    os.remove(os.path.join(FIXTURE_APP, 'jd_needs.md'))
    code, out, _ = build_detector_context()
    assert code != 0, f'build wrote a context with no requirements:\n{out}'
    assert 'jd_needs.md' in out, out


def test_detector_evidence_carries_every_manifest_entry_once():
    """Found 2026-10-27: the detector was told to read inventory.md (206 KB,
    3,383 lines) in full, past what one read returns, so entries late in the
    file could go unread. Every entry the manifest surfaces now reaches it
    whole, in files sized to a single read."""
    budget = 1500
    code, out, scratch = build_detector_context('--max-bytes', '45000',
                                                '--evidence-bytes', str(budget))
    assert code == 0, f'build failed:\n{out}'
    files = detector_evidence(scratch)
    assert len(files) > 1, f'a {budget}-byte budget should split the evidence: {len(files)} file(s)'
    for name, text in files:
        size = len(text.encode('utf-8'))
        assert size <= budget, f'{name} is {size} bytes, over the {budget}-byte budget'
        assert f'{os.path.join(scratch, name)}' in out, f'prompt does not name {name}:\n{out}'
    evidence = '\n'.join(text for _, text in files)

    root, cfg = _config.load()
    inventory = _util.read(pu._inventory_path(root, cfg))
    narratives = _util.read(pu._narratives_path(root, cfg))
    # PR-001.01 is an element; it reaches the detector inside PR-001.
    for entry_id in ('EX-003', 'EX-001', 'PR-001', 'PB-001'):
        block = expected_block(inventory, entry_id)
        assert evidence.count(block) == 1, f'{entry_id} not copied whole exactly once'
    for entry_id in MANIFEST_NARRATIVES:
        block = expected_block(narratives, entry_id, narrative=True)
        assert evidence.count(block) == 1, f'{entry_id} not copied whole exactly once'
    assert 'ID: EX-002' not in evidence, 'an entry the manifest does not list was copied'
    assert 'inventory.md:' not in out and 'narratives.md:' not in out, \
        f'the prompt still sends the detector to the full profile files:\n{out}'


def labels_by_entry(text):
    """Return {entry ID: (section, role, group)} as read top-down through text.

    A '## ' line resets role and group; a '### ' line resets group. The same
    rule applied to an inventory file and to one evidence file must agree.
    """
    section = role = group = ''
    out = {}
    for line in text.split('\n'):
        if line.startswith(('## ', '# ')):
            section, role, group = line.rstrip(), '', ''
        elif line.startswith('### '):
            role, group = line.rstrip(), ''
        elif line.startswith('--- '):
            group = line.rstrip()
        elif m := re.match(r'^ID: ((?:EX|PR|PB|PS)-\d+)\s*$', line):
            out[m.group(1)] = (section, role, group)
    return out


def test_detector_evidence_keeps_roles_and_topic_groups():
    """Found 2026-11-04 (APP-027): evidence went to the detector in retrieval
    score order with no role or topic-group lines, so the atomic entries of one
    experience arrived scattered, and a requirement whose pieces sat in one
    group was called a gap. Entries must follow inventory order under their
    own role and group labels, restated at the top of any file that starts
    mid-group, with narratives after them in file order."""
    # Score order deliberately differs from inventory order.
    write_manifest(inventory_ids=('PB-001', 'EX-001', 'PR-001', 'PR-001.01', 'EX-003'),
                   narrative_ids=tuple(reversed(MANIFEST_NARRATIVES)))
    code, out, scratch = build_detector_context('--max-bytes', '45000', '--evidence-bytes', '1500',
                                                manifest=False)
    assert code == 0, f'build failed:\n{out}'
    files = detector_evidence(scratch)
    assert len(files) > 1, 'a 1500-byte budget should split the evidence'

    root, cfg = _config.load()
    inventory = _util.read(pu._inventory_path(root, cfg))
    narratives = _util.read(pu._narratives_path(root, cfg))
    expected = labels_by_entry(inventory)
    seen = {}
    for name, text in files:
        for entry_id, labels in labels_by_entry(text).items():
            seen[entry_id] = labels
            assert labels == expected[entry_id], \
                f'{entry_id} in {name} reads under {labels}, inventory has {expected[entry_id]}'

    evidence = '\n'.join(text for _, text in files)
    order = re.findall(r'^ID: ((?:EX|PR|PB|PS|ST|DC)-\d+)\s*$', evidence, re.M)
    inv_order = [i for i in re.findall(r'^ID: ((?:EX|PR|PB|PS)-\d+)\s*$', inventory, re.M)
                 if i in seen]
    nar_order = [i for i in re.findall(r'^ID: ((?:ST|DC)-\d+)\s*$', narratives, re.M)
                 if i in MANIFEST_NARRATIVES]
    assert order == inv_order + nar_order, f'evidence not in profile order: {order}'
    assert set(seen) == {'EX-003', 'EX-001', 'PR-001', 'PB-001'}, f'wrong entries: {sorted(seen)}'


def test_detector_evidence_refuses_an_unknown_or_empty_manifest():
    """An ID with no entry would leave the detector judging without it, and an
    empty manifest would leave it judging with nothing; both must stop."""
    write_manifest(inventory_ids=('EX-001', 'EX-999'))
    code, out, _ = build_detector_context(manifest=False)
    assert code != 0 and 'EX-999' in out, f'build accepted an ID with no entry:\n{out}'

    write_manifest(inventory_ids=(), narrative_ids=())
    code, out, _ = build_detector_context(manifest=False)
    assert code != 0 and 'no candidate' in out, f'build accepted an empty manifest:\n{out}'


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
# Application IDs
# role-intake draws its APP-NNN several steps before ingest creates the folder,
# so the ID has to be held from the moment it is printed.
# ---------------------------------------------------------------------------

def test_back_to_back_app_ids_differ():
    """Shipped 2026-07-14: two role-intake sessions started back to back both
    drew APP-015 (novartis and biogen), because app_id.py returned max+1 over
    the folders and reserved nothing until ingest ran.
    """
    first_code, first = run('app_id.py')
    second_code, second = run('app_id.py')
    assert first_code == 0 and second_code == 0, f'app_id.py failed:\n{first}\n{second}'
    assert first != second, f'both calls drew {first}'
    # The fixture already holds APP-001, so neither call may hand it out again.
    assert 'APP-001' not in (first, second), f'reissued an ID in use: {first}, {second}'


# ---------------------------------------------------------------------------
# Markdown convention
# Prose is one paragraph or bullet per line (md_unwrap.py). Fenced skeletons
# are machine-read, so the unwrap must leave them byte for byte.
# ---------------------------------------------------------------------------

def test_markdown_has_no_hard_wraps():
    """Decided 2026-11-05 (GitHub #5): files mixed 80-column hard wraps with
    one-line paragraphs. Every in-scope file must pass md_unwrap.py check, and
    the check must catch a wrapped paragraph while sparing a fenced skeleton.
    """
    code, out = run('md_unwrap.py', 'check')
    assert code == 0, f'hard-wrapped prose in scope:\n{out}'
    sample = ('Prose that was wrapped\nat a column.\n\n'
              '```\n- Field: {{value}}\nline two\n```\n')
    path = write_block('wrapped.md', sample)
    code, out = run('md_unwrap.py', 'check', '--file', path)
    assert code == 1, f'check missed a wrapped paragraph:\n{out}'
    run('md_unwrap.py', 'apply', '--file', path)
    fixed = _util.read(path)
    assert 'Prose that was wrapped at a column.' in fixed, 'paragraph was not joined'
    assert '```\n- Field: {{value}}\nline two\n```' in fixed, 'fenced skeleton was altered'


# ---------------------------------------------------------------------------
# Axis-builder QC: industry acronym list
# The list names acronyms an industry's hiring panel reads without expansion.
# It is not an index of the file's own prose, so the two need not match.
# ---------------------------------------------------------------------------

def test_acronym_list_is_not_an_index_of_the_text():
    """Fixed 2026-11-05 (GitHub #10): H2 failed whenever a listed acronym was
    absent from the file's own text, and asked for valid entries (SDTM, eTMF in
    biotech) to be removed. A listed-but-unmentioned acronym must pass; an
    acronym the text uses but the list lacks is passed on as a suggestion for
    the reviewer to judge, not a failure.
    """
    import axis_qc
    text = ('## Vocabulary\n\nSponsors file with the FDA and fund NIH work.\n\n'
            '## Dialect\n\nPlain voice.\n\n### Acronyms\n\nFDA, SDTM, eTMF\n\n'
            '## Emphasis\n\nNone.\n\n## Adjacency\n\nNone.\n')
    _, rec = axis_qc._check_h2_acronym_reconciliation(text)
    assert rec['passed'], f'H2 failed a list that only holds extra acronyms: {rec["detail"]}'
    assert rec.get('suggestions') == ['NIH'], f'expected NIH as the one suggestion, got {rec}'


# ---------------------------------------------------------------------------
# Repo paths
# Skills and agents look locations up through paths.py, never spell them out.
# ---------------------------------------------------------------------------

def test_skills_look_up_paths_instead_of_spelling_them():
    """Fixed 2026-11-05 (GitHub #22): skills, agents, templates and rules
    spelled out personal/... paths and found application folders by hand.
    paths.py does the lookup; none of those files may name a personal/ path
    again. (design/ and the root docs describe locations for the reader and
    are out of scope.)
    """
    code, out = run('paths.py', 'app', 'APP-001')
    assert code == 0 and out.endswith('aldridge_APP-001_2026-01'), out
    code, out = run('paths.py', 'app', 'APP-099')
    assert code != 0 and 'no application folder' in out, out
    code, out = run('paths.py', 'profile')
    assert code == 0 and os.path.isdir(out), out
    offenders = []
    for folder in ('.claude/skills', '.claude/agents', 'templates', 'rules'):
        for dirpath, _, files in os.walk(os.path.join(REPO_ROOT, *folder.split('/'))):
            for name in files:
                if name.endswith('.md') and 'personal/' in _util.read(os.path.join(dirpath, name)):
                    offenders.append(os.path.relpath(os.path.join(dirpath, name), REPO_ROOT))
    assert not offenders, 'files naming a personal/ path: ' + ', '.join(offenders)


def test_gap_analysis_states_work_state_coverage():
    """Built 2026-11-05 (GitHub #53): a role's work-state was classified and
    then never reported, so a role no entry matched was carried silently by
    adjacency. The gap analysis now says per classified value which entries
    match exactly, or that none do, with the adjacent values carrying it.
    """
    import gap_assemble
    entries = {'EX-001': ['pivot'], 'EX-002': ['scaling', 'pivot'], 'EX-003': ['mature']}
    adjacency = {'pivot': ['scaling'], 'turnaround': ['mature', 'scaling']}
    block = gap_assemble.render_work_state_coverage(['pivot', 'turnaround'], entries, adjacency)
    assert '**pivot**: 2 entries match exactly (EX-001, EX-002)' in block, block
    assert '**turnaround**: no entry matches exactly' in block, block
    assert 'mature (1), scaling (1)' in block and 'interview' in block, block
    assert gap_assemble.render_work_state_coverage([], entries, adjacency) == '_(none)_'


def test_gap_analysis_leads_with_the_picture_not_a_score():
    """Built 2026-11-05 (GitHub #59): a single fit score was the wrong deliverable
    and read optimistic. The artifact now leads with a computed coverage table and
    per-run themes, and the recommendation states what it depends on. Assembles
    the fixture for real, then proves QC catches each way the picture can go wrong.
    """
    def report():
        _, out = run('gap_qc.py', 'check', '--folder', FIXTURE_APP)
        return {line.split()[0]: line for line in out.split('\n') if line.startswith('G')}

    assert all('PASS' in line for line in report().values()), report()

    requirements = [{'requirement_id': f'CR-{i:03d}', 'status': s, 'evidence': [], 'notes': 'n'}
                    for i, s in enumerate(['covered', 'closed', 'language-shift', 'partial-match',
                                           'interview-deferred', 'unresolved'], start=1)]
    judgment = {'themes': [{'name': 'Soft spots', 'kind': 'reader-dependent',
                            'requirements': ['CR-003', 'CR-004', 'CR-005', 'CR-006'],
                            'meaning': 'Depends on the reader.'}],
                'depends_on': ['They screen for transferable capability (CR-004, CR-005).']}
    inputs = {name: write_block(f'{name}.json', json.dumps(body)) for name, body in
              (('requirements', requirements), ('eligibility', []), ('themes', judgment))}
    code, out = run('gap_assemble.py', 'assemble', '--folder', FIXTURE_APP, '--app-id', 'APP-001',
                    '--date', '2026-01-12', '--company', 'Aldridge Pharma', '--role', 'Director',
                    '--recommendation-label', 'Proceed with caution',
                    '--recommendation-rationale-file', write_block('why.txt', 'Mixed.'),
                    '--requirements-file', inputs['requirements'],
                    '--eligibility-file', inputs['eligibility'], '--themes-file', inputs['themes'])
    assert code == 0, out
    path = os.path.join(FIXTURE_APP, 'gap_analysis.md')
    built = _util.read(path)
    assert 'Fit Score' not in built, built
    assert built.index('## Coverage Picture') < built.index('## Gap Themes') \
        < built.index('## Recommendation') < built.index('## Requirements'), built
    # One row per need in rank order; only required core rows (a role-statement
    # need, or Qualifications) are counted as unmet: CR-005, not CR-004.
    assert '| N-01 Operating model for clinical data: standards and governance (3, core) | 0 | 0 | 1 | 0 | 1 | 1 |' \
        in built, built
    assert '| N-03 Leading a data team (1) | 0 | 0 | 0 | 1 | 0 | 0 |' in built, built
    assert '- **Core, required:** 1 of 2 shown, 0 partly shown, 1 open.' in built, built
    assert '**Unmet Core Requirements:** 1' in built, built
    heads = re.findall(r'^### (CR-\d+) - .*\((.+)\)$', built.split('## Requirements')[1].split('## Language')[0],
                       re.MULTILINE)
    assert heads[0] == ('CR-003', 'N-01, preferred') and heads[-1] == ('CR-001', 'Qual, required'), \
        f'requirements not reported in need rank order: {heads}'
    assert all('PASS' in line for line in report().values()), report()

    def fails_check(check, old, new):
        _util.write(path, built.replace(old, new))
        assert old in built, f'{old!r} is not in the artifact, so this proves nothing'
        result = report()[check]
        assert 'FAIL' in result, f'{check} passed after replacing {old!r}: {result}'
        return result

    assert 'does not match' in fails_check('G10', '| N-03 Leading a data team (1) | 0 | 0 | 0 | 1 | 0 | 0 |',
                                           '| N-03 Leading a data team (1) | 1 | 0 | 0 | 0 | 0 | 0 |')
    assert 'statuses give 1' in fails_check('G10', '**Unmet Core Requirements:** 1', '**Unmet Core Requirements:** 2')
    assert 'CR-005' in fails_check('G12', 'CR-003, CR-004, CR-005, CR-006', 'CR-003, CR-004, CR-006')
    fails_check('G12', '(reader-dependent)', '(depends)')
    fails_check('G13', '- They screen for transferable capability (CR-004, CR-005).', '')
    fails_check('G9', '**Recommendation:** Proceed with caution', '**Recommendation:** Proceed')

    # An unmet required row outside the core needs is listed, never counted:
    # CR-004 (N-03, which the role statement does not name) left unresolved.
    requirements[3]['status'] = 'unresolved'
    _util.write(inputs['requirements'], json.dumps(requirements))
    code, out = run('gap_assemble.py', 'assemble', '--folder', FIXTURE_APP, '--app-id', 'APP-001',
                    '--date', '2026-01-12', '--company', 'Aldridge Pharma', '--role', 'Director',
                    '--recommendation-label', 'Proceed with caution',
                    '--recommendation-rationale-file', write_block('why.txt', 'Mixed.'),
                    '--requirements-file', inputs['requirements'],
                    '--eligibility-file', inputs['eligibility'], '--themes-file', inputs['themes'])
    assert code == 0, out
    assert '**Unmet Core Requirements:** 1' in _util.read(path), 'a non-core unmet row moved the count'


def test_every_soft_must_have_is_named_in_a_condition():
    """Found on APP-028: the recommendation listed conditions but none tested the
    SDTM and ADaM must-have, and QC only asked for at least one condition. A
    must-have that is partial or unmet must now be named in a condition.
    """
    path = os.path.join(FIXTURE_APP, 'gap_analysis.md')
    text = _util.read(path)

    def g14():
        _, out = run('gap_qc.py', 'check', '--folder', FIXTURE_APP)
        return next(line for line in out.split('\n') if line.startswith('G14'))

    assert 'PASS' in g14(), g14()
    # CR-005 is a required row in a core need (role-statement signal): it must be named.
    assert '(CR-005)' in text, 'the fixture names no CR-005 condition, so this proves nothing'
    _util.write(path, text.replace(' (CR-005)', ''))
    line = g14()
    assert 'FAIL' in line and 'CR-005' in line, f'an unnamed core requirement passed: {line}'
    # CR-004 is partial but in a need the role statement does not name: listed, never required here.
    _util.write(path, text.replace(' (CR-004)', ''))
    assert 'PASS' in g14(), f'a non-core requirement was demanded in a condition: {g14()}'


def test_eligibility_lines_use_an_allowed_ending():
    """Found on APP-028: location was open because the JD did not state it, but
    the only endings available read 'Confirmed, no conflict' or 'User chose', so
    an open question was recorded as settled.
    """
    import gap_assemble
    line = gap_assemble._render_eligibility(
        [{'flag_type': 'Modality', 'evidence': 'The JD states none', 'decision': 'open'}])
    assert line == '- **Modality**: The JD states none. Not stated in the JD; ask at the screen.', line
    try:
        gap_assemble._render_eligibility([{'flag_type': 'x', 'evidence': 'y', 'decision': 'maybe'}])
    except ValueError:
        pass
    else:
        raise AssertionError('an unknown eligibility decision rendered')

    path = os.path.join(FIXTURE_APP, 'gap_analysis.md')
    text = _util.read(path)

    def g15():
        _, out = run('gap_qc.py', 'check', '--folder', FIXTURE_APP)
        return next(line for line in out.split('\n') if line.startswith('G15'))

    assert 'PASS' in g15(), g15()
    _util.write(path, text.replace('Confirmed, no conflict.', 'Probably fine.', 1))
    assert 'FAIL' in g15(), f'an off-list eligibility ending passed: {g15()}'


def test_leadership_classification_carries_a_valid_tier():
    """Built 2026-11-05 (GitHub #51): research calibrated seniority (e.g. VP vs
    Associate Director) and classification threw it away, so every leadership
    CV got one voice. A leadership role now records a tier named in
    leadership.md's Tiers block; an IC role records none.
    """
    import role_classify_qc as rcq
    root, cfg = _config.load()
    tiers = rcq.leadership_tiers(root, cfg)
    assert tiers == ['delivery-lead', 'function-lead', 'multi-function-head', 'executive'], tiers

    def result(level, tier_line):
        log = (f'## Axis Classification\n\n- Orientation: x (primary) - r\n- Industry: x - r\n'
               f'- Specialty: x - r\n- Level: {level} - r\n{tier_line}- Work-state: x - r\n\n## Axis Gaps\n\nNone\n')
        findings = []
        rcq.check_tier(log, tiers, findings)
        return findings[0]

    assert result('leadership', '- Tier: function-lead - scope spans R&D\n')[1]
    assert not result('leadership', '')[1], 'leadership without a tier passed'
    assert not result('leadership', '- Tier: senior-vp - r\n')[1], 'unknown tier passed'
    assert result('ic', '')[1]
    assert not result('ic', '- Tier: function-lead - r\n')[1], 'ic with a tier passed'


def needs_file(*rows, type_='required'):
    """Return a jd_needs.md text holding (text, source) rows before ranking."""
    body = ''.join(f'| {i} | {text} |  | {type_} | {source} |\n'
                   for i, (text, source) in enumerate(rows, 1))
    return ('# JD needs: X | Y\n\n## Requirements\n\n| Req | Requirement | Kind | Type | JD line |\n'
            f'|---|---|---|---|---|\n{body}')


def test_requirement_text_keeps_jd_modifiers():
    """Fixed 2026-11-05 (GitHub #83): the extractor dropped 'familiarity with'
    from a must-have and nothing compared requirement text with the JD. Modifiers
    are read from the JD clause holding the quote, so a narrow quote cannot step
    around the check.
    """
    import role_classify_qc as rcq
    _, cfg = _config.load()
    jd = ('Strong knowledge of the industry, including familiarity with drug discovery.\n'
          "Bachelor's degree required; advanced degree preferred.\n"
          'Master’s degree with 6 years of experience.\n')

    def result(text, source):
        findings = []
        rcq.check_requirement_text(needs_file((text, source)), jd, cfg['requirement_qualifiers'],
                                   cfg['requirement_year_count'], findings)
        return findings[0]

    whole ='Knowledge of the industry, including familiarity with drug discovery'
    assert result(whole, 'Quals #1 "including familiarity with drug discovery"')[1]
    dropped = result('Knowledge of the industry, including drug discovery', 'Quals #1 "including familiarity with drug discovery"')
    assert not dropped[1] and 'familiarity with' in dropped[2], dropped
    assert not result('Knowledge of the industry, including drug discovery', 'Quals #1 "drug discovery"')[1], 'a narrow quote hid the dropped modifier'
    assert result("Bachelor's degree", 'Quals #2 "Bachelor\'s degree required"')[1], "'preferred' from the next clause bound this row"
    assert not result('Advanced degree required', 'Quals #2 "advanced degree preferred"')[1], 'a swapped modifier passed'
    assert result("Master's degree with 6 years", 'Quals #3 "Master\'s degree with 6 years"')[1], 'curly apostrophe broke the match'
    assert not result("Master's degree with 5 years", 'Quals #3 "Master\'s degree with 6 years"')[1], 'a changed year count passed'
    assert not result('Degree', 'Quals #2 "not in the JD"')[1], 'a quote absent from the JD passed'
    assert not result('Advanced degree required', 'Quals #2')[1], 'a quoteless row whose text is not in the JD passed'
    assert result('advanced degree preferred', 'Quals #2')[1], 'a quoteless row whose text is in the JD failed'
    assert result('Degree', 'Quals #2 "Bachelor\'s degree required"; also Summary')[1], 'a section pointer after the quote broke the row'


def test_split_requirement_keeps_each_year_count():
    """A clause can hold one year count per requirement. Requiring both counts on
    every row failed a correct split of '10 years..., with at least 5 years...',
    which left two tests sharing one gap verdict. Each count now needs to survive
    on some row from the clause, and a count lost from all of them still fails.
    """
    import role_classify_qc as rcq
    _, cfg = _config.load()
    jd = 'Minimum of 10 years in the industry, with at least 5 years in people management.\n'

    def result(*rows):
        findings = []
        rcq.check_requirement_text(needs_file(*((text, f'Quals #1 "{quote}"') for text, quote in rows)),
                                   jd, cfg['requirement_qualifiers'], cfg['requirement_year_count'], findings)
        return findings[0]

    ten = 'Minimum of 10 years in the industry'
    five = 'at least 5 years in people management'
    split = result((ten, ten), (five, five))
    assert split[1], f'a correct split failed: {split}'
    assert result((f'{ten}, with {five}', ten))[1], 'the whole clause on one row failed'
    lost = result((ten, ten), ('people management', 'people management'))
    assert not lost[1] and '5 years' in lost[2], f'a count lost from every row passed: {lost}'
    assert not result(('Minimum of 8 years in the industry', ten), (five, five))[1], 'a changed count passed'
    # One requirement written twice from the same sentence fails; Medtronic
    # APP-024 rows 40 and 41 differed only by 'including AWS'.
    dup = result((ten, ten), (f'{ten}, with {five}', ten))
    assert not dup[1] and 'wholly inside' in dup[2], f'an overlapping pair of rows passed: {dup}'


def test_split_requirement_keeps_modifier_on_some_row():
    """Otsuka APP-026, 2026-11-10: 'understanding of data ... to be able to be
    effectively build AI solutions' split correctly into two rows, and C8 failed
    the second for lacking 'understanding of', which belongs only to the first.
    A script cannot read whether a modifier carries onto each half, so it needs
    the modifier on some row from the clause (qc-role-classify judges the rest);
    a modifier lost from every row still fails.
    """
    import role_classify_qc as rcq
    _, cfg = _config.load()
    jd = ('Possess a deep understanding of clinical trial data to be able to build '
          'AI solutions that conform to regulatory compliance.\n')

    def result(*rows):
        findings = []
        rcq.check_requirement_text(needs_file(*((text, f'Skills "{quote}"') for text, quote in rows)),
                                   jd, cfg['requirement_qualifiers'], cfg['requirement_year_count'], findings)
        return findings[0]

    first = 'Possess a deep understanding of clinical trial data'
    second = 'build AI solutions that conform to regulatory compliance'
    split = result((first, first), (second, second))
    assert split[1], f'a correct split failed: {split}'
    lost = result(('Possess clinical trial data', first), (second, second))
    assert not lost[1] and 'understanding of' in lost[2], f'a modifier lost from every row passed: {lost}'


def test_ranked_needs_cover_every_requirement_once():
    """Built 2026-11-09 (GitHub #89): the requirement Type records which JD
    section a row came from, so APP-028's 'primary focus' paragraph ranked last
    of 35. Needs are now ranked, and every requirement belongs to exactly one, so
    grouping can never silently drop a requirement the CV must answer.
    Redesigned 2026-11-10: every requirement carries a kind, the result lives in
    its own readable file (jd_needs.md), and Not ranked rows (boilerplate, role
    shape, administrative detail) never reach retrieval or gap analysis.
    Moved 2026-11-10: jd_needs.md is the requirements' only home, so ranking
    rewrites the file from its own rows and a row the ranker drops stays on file.
    """
    import requirement_kinds
    import role_classify_qc as rcq
    repo_root, cfg = _config.load()
    kinds = requirement_kinds.load_kinds(repo_root, cfg)
    # Employment conditions (travel, location, authorization) are checked by
    # gap analysis's eligibility phase, so they are never a Qualification row
    # that counts toward go / no-go or claims a CV slot (2026-11-11).
    assert kinds.get('Employment condition') == requirement_kinds.NOT_RANKED, kinds
    assert kinds.get('Qualification') == requirement_kinds.QUALIFICATIONS, kinds
    research_path = os.path.join(FIXTURE_APP, 'research.md')
    needs_path = os.path.join(FIXTURE_APP, 'jd_needs.md')
    jd = _util.read(os.path.join(FIXTURE_APP, 'jd.md'))
    research = _util.read(research_path)
    good = _util.read(needs_path)
    row6 = '| 6 | Familiarity with regulatory submission data packages | Means | preferred | L27 Nice to have |\n'
    assert row6 in good, 'fixture row 6 changed shape'
    table_head = requirement_kinds.ROW_HEADER + '\n'

    def result(needs_text):
        findings = []
        rcq.check_ranked_needs(needs_text, jd, kinds, findings)
        return findings[0]

    assert result(good)[1], result(good)
    unplaced = good.replace(row6, '') + '\n## Requirements\n\n' + table_head + row6
    assert not result(unplaced)[1], 'a requirement left out of every need passed'
    assert not result(good.replace(table_head + '| 1 |', table_head + row6 + '| 1 |'))[1], 'a requirement in two places passed'
    assert not result(good.replace('N-03', 'N-05'))[1], 'a gap in the need ids passed'
    assert not result(good.replace('- Signals: repetition 1, space 10', '- Signals: emphasis'))[1], 'an unknown signal passed'
    assert not result(good.replace('- Signals: repetition 1, space 10', '- Signals: repetition 1, space'))[1], \
        'a space signal with no count passed'
    assert not result(good.replace('- Signals: repetition 1, space 10', '- Signals: priority-words'))[1], 'a retired signal passed'
    assert not result(good.replace('"Lead and develop a data team of five or more"\n\n',
                                   '"Hire and develop a data team of five or more"\n\n'))[1], 'a quote absent from the JD passed'
    assert not result(good.replace('- Leads, does, or both:', '- Leads:'))[1], 'a ranking without the job description passed'
    # Every JD reference is a jd.md line number, and it must be the right one.
    assert not result(good.replace('(L17)', '(Responsibilities)'))[1], 'a job line citing no jd.md line passed'
    assert not result(good.replace('(L17)', '(L18)'))[1], 'a job line citing a blank jd.md line passed'
    # The lead-or-do line states its answer and what is led, never an argument.
    assert not result(good.replace('leads; what: a data team', 'leads. It is a leadership role over a data team'))[1], \
        'a lead-or-do line arguing its answer passed'
    assert result(good.replace('leads; what:', 'both, mainly doing; what:'))[1], 'an allowed lead-or-do answer failed'
    assert result(good.replace('what: a data team of five or more', 'what: the enterprise rollout of the data platform'))[1], \
        'a lead-or-do line naming work, not people, failed'
    assert not result(good.replace('Quote: L17', 'Quote: L16'))[1], 'a need Quote on the wrong line passed'
    assert not result(good.replace(row6, row6.replace('L27', 'L26')))[1], 'a row on the wrong line passed'
    assert not result(good.replace(row6, row6.replace('L27 ', '')))[1], 'a row with no line number passed'
    # The role statement is short key items, each ending with its line; the
    # role-statement signal must quote from a line the role statement cites.
    statement = '- Role statement:\n  - owns the operating model for clinical data (L8)\n'
    assert statement in good, 'fixture role statement changed shape'
    assert not result(good.replace(statement, ''))[1], 'a job description with no role statement passed'
    assert not result(good.replace(statement, statement.replace('(L8)', '(L18)')))[1], \
        'a role statement item citing a blank line passed'
    assert not result(good.replace(statement, statement.replace(' (L8)', '')))[1], \
        'a role statement item with no line passed'
    # Outcomes the role's work achieves sit on their own job line, each citing its line.
    outcomes = statement + '- Outcomes:\n  - enable faster study decisions (L8)\n'
    assert result(good.replace(statement, outcomes))[1], result(good.replace(statement, outcomes))
    assert not result(good.replace(statement, outcomes.replace(' decisions (L8)', ' decisions')))[1], \
        'an outcome with no line passed'
    assert not result(good.replace(statement, outcomes.replace('decisions (L8)', 'decisions (L18)')))[1], \
        'an outcome citing a blank line passed'
    # An item may hold its own semicolon (a restatement merged into it).
    assert result(good.replace(statement, statement.replace('clinical data (L8)', 'clinical data; runs it (L8)')))[1], \
        'a role statement item holding a semicolon failed'
    assert not result(good.replace(statement, statement.replace('(L8)', '(L9)')))[1], \
        'a role-statement need quoting a line the role statement does not cite passed'
    assert not result(good.replace('- Signals: repetition 2', '- Signals: role-statement, repetition 2'))[1], \
        'a role-statement signal on a quote outside the role statement passed'
    assert not result(None)[1], 'a missing needs file passed'

    # Kinds: every row has a known kind, and lands where its kinds put it.
    # Boilerplate in a need is how it reached the CV before.
    assert not result(good.replace(row6, row6.replace('| Means |', '| Vibes |')))[1], 'an unknown kind passed'
    assert not result(good.replace(row6, row6.replace('| Means |', '|  |')))[1], 'a row with no kind passed'
    boiler_row = row6.replace('| Means |', '| Boilerplate or attitude |')
    assert not result(good.replace(row6, boiler_row))[1], 'a Not ranked row inside a need passed'
    moved = good.replace(row6, '').replace('## Not ranked\n\nNone.', '## Not ranked\n\n' + table_head + boiler_row.rstrip())
    assert result(moved)[1], result(moved)
    assert not result(moved.replace('Boilerplate or attitude', 'Means'))[1], 'a Means row on the Not ranked list passed'
    mixed = good.replace(row6, row6.replace('| Means |', '| Boilerplate or attitude (passion) + Means (submission data) |'))
    assert result(mixed)[1], 'a row with a ranked part was refused a need'

    # Retrieval and gap analysis never see a Not ranked row.
    import gap_context
    import gap_qc
    import retrieval_payload
    _util.write(needs_path, moved)
    try:
        scoring = retrieval_payload.build_scoring_context(FIXTURE_APP, cfg, 'x', 10 ** 7)
        detector, _ = gap_context.build_context(FIXTURE_APP, repo_root, cfg, 10 ** 7)
        info = gap_qc._requirement_info(FIXTURE_APP, cfg)
    finally:
        _util.write(needs_path, good)
    assert '| 5 |' in scoring and '| 6 |' not in scoring, 'retrieval scored a Not ranked row'
    assert '| 5 |' in detector and '| 6 |' not in detector, 'gap analysis was handed a Not ranked row'
    # The detector judges scope from the job section, not the title's market read.
    assert 'owns the operating model for clinical data (L8)' in detector.split('# Profile reference sections')[0], \
        'the gap detector was not handed the role statement'
    assert 'CR-006' not in info and info['CR-005']['demand'] == 'required', 'gap QC expected a Not ranked row'

    # The assembler rewrites jd_needs.md from the ranker's output, carrying each
    # requirement's text, Type and Source over from the file, and leaves
    # research.md alone.
    ranker = ('## Row Kinds\n\n| # | Kind |\n|---|---|\n'
              + ''.join(f'| {n} | {k} |\n' for n, k in enumerate(
                  ['Qualification', 'Function', 'Function', 'Function', 'Means', 'Boilerplate or attitude'], 1))
              + '\n## Ranked Needs\n\n**The job:**\n'
              '- Role statement:\n  - owns the operating model for clinical data (L8)\n'
              '- Outcomes:\n  - enable faster study decisions (L8)\n'
              '- Leads, does, or both: leads; what: a team (L17)\n\n'
              '| Need | Label | Requirements | Signals | Quote |\n|---|---|---|---|---|\n'
              '| N-01 | Operating model | 3, 5 | role-statement | About the role "The Director owns the operating model for clinical data across the Aldridge" |\n'
              '| N-02 | Vendor oversight | 2 | repetition 2 | Requirements "Vendor oversight and contract management across external data providers" |\n'
              '| N-03 | Leading a data team | 4 | space | Responsibilities "Lead and develop a data team of five or more" |\n')
    code, out = run('role_classify_assemble.py', 'needs', '--folder', FIXTURE_APP, '--needs-file', write_block('ranker.md', ranker))
    assert code == 0, out
    written = _util.read(needs_path)
    assert result(written)[1], result(written)
    assert '### N-01: Operating model' in written, written
    assert '- Outcomes:\n  - enable faster study decisions (L8)' in written, 'the assembler dropped the Outcomes line'
    # The script sets repetition (distinct JD sections of the need's rows) and
    # space (words in their distinct JD clauses), whatever the ranker wrote, and
    # orders by role-statement, repetition, space: Vendor oversight's claimed
    # 'repetition 2' (one section) is 1, so the team need's 10 words to its 9
    # put it above, against the ranker's order.
    assert '### N-01: Operating model\n\n- Signals: role-statement, repetition 2, space 20\n' in written, written
    assert '### N-02: Leading a data team\n\n- Signals: repetition 1, space 10\n' in written, written
    assert '### N-03: Vendor oversight\n\n- Signals: repetition 1, space 9\n' in written, written
    # Rows outside the needs are placed by kind, not by the ranker.
    assert '## Not ranked\n\n' + table_head + boiler_row.rstrip() in written, 'row 6 was not placed in Not ranked by its kind'
    assert '## Qualifications\n\n' + table_head + '| 1 |' in written, 'row 1 was not placed in Qualifications by its kind'
    assert _util.read(research_path) == research, 'the needs step changed research.md'
    bad = write_block('ranker_bad.md', ranker.replace('| 3, 5 |', '| 3, 5, 9 |'))
    code, out = run('role_classify_assemble.py', 'needs', '--folder', FIXTURE_APP, '--needs-file', bad)
    assert code != 0 and 'not in' in out, 'a row the file does not have was written'
    dropped = write_block('ranker_dropped.md', ranker.replace('| 3, 5 |', '| 3 |'))
    code, out = run('role_classify_assemble.py', 'needs', '--folder', FIXTURE_APP, '--needs-file', dropped)
    assert code == 0, out
    kept = _util.read(needs_path)
    assert '## Requirements\n\n' + table_head + '| 5 | Direct experience' in kept, 'a row the ranker dropped was lost on rewrite'
    assert not result(kept)[1], 'a row the ranker dropped passed'
    _util.write(needs_path, good)


def test_requirements_are_extracted_into_jd_needs():
    """Moved 2026-11-10 (GitHub #89): requirement extraction moved from
    role-intake into role-classify, and the requirements from research.md into
    jd_needs.md, so the text exists once. The extractor's table is written before
    ranking, its Type held to the four allowed values, and its rows checked
    before any ranking is spent on them.
    """
    import requirement_kinds
    import role_classify_qc as rcq
    _, cfg = _config.load()
    needs_path = os.path.join(FIXTURE_APP, 'jd_needs.md')
    research = _util.read(os.path.join(FIXTURE_APP, 'research.md'))
    assert 'Critical Requirements' not in research, 'research.md still holds requirements'
    table = ('## Critical Requirements\n\n| # | Text | Demand | Source |\n|------|------|------|------|\n'
             '| 1 | Bachelor\'s degree in a scientific or quantitative discipline | education (required) | '
             'Requirements "Bachelor\'s degree in a scientific or quantitative discipline" |\n'
             '| 2 | Familiarity with regulatory submission data packages | preferred | '
             'Nice to have "Familiarity with regulatory submission data packages"; also Requirements |\n'
             '| 3 | Direct experience with a commercial data warehouse platform | required | '
             'Requirements "Direct experience with a commercial data warehouse platform in production" |\n')
    code, out = run('role_classify_assemble.py', 'requirements', '--folder', FIXTURE_APP,
                    '--requirements-file', write_block('reqs.md', table))
    assert code == 0, out
    written = _util.read(needs_path)
    # Every reference becomes the quote's jd.md line. A quote equal to the row
    # text is dropped; a quote the text was cut from stays; other pointers go.
    assert '| L21 Requirements |\n' in written, 'a quote equal to the text was kept, or the line is wrong'
    assert '| 2 | Familiarity with regulatory submission data packages |  | preferred | L27 Nice to have |\n' in written, \
        'an also-pointer survived'
    assert '| L23 Requirements "Direct experience with a commercial data warehouse platform in production" |\n' \
        in written, 'a quote that differs from the text was dropped'
    piped = {'num': 1, 'text': 'SAS | R', 'kind': None, 'demand': 'required', 'source': 'L5 Skills'}
    back = requirement_kinds.all_rows(requirement_kinds.read_needs(requirement_kinds.render_requirements('X | Y', [piped])))
    assert back and back[0]['text'] == 'SAS | R' and back[0]['source'] == 'L5 Skills', f'a pipe in a requirement broke its row: {back}'
    assert written.startswith('# JD needs: Aldridge Pharma | Director, Clinical Data Strategy\n\n## Requirements\n'), written
    assert "| 1 | Bachelor's degree in a scientific or quantitative discipline |  | required |" in written, \
        'a recoverable Demand was not reduced to its allowed value'
    assert '## Needs' not in written, 're-extraction kept an old ranking'
    code, out = run('role_classify_qc.py', 'requirements', '--folder', FIXTURE_APP)
    assert code == 0, out

    code, out = run('role_classify_assemble.py', 'requirements', '--folder', FIXTURE_APP,
                    '--requirements-file', write_block('bad.md', table.replace('| preferred |', '| Knowledge |')))
    assert code != 0 and 'Knowledge' in out, 'a Demand with no allowed value was written'
    old = write_block('old.md', table.replace('| preferred |', '| contextual |'))
    code, out = run('role_classify_assemble.py', 'requirements', '--folder', FIXTURE_APP, '--requirements-file', old)
    assert code != 0 and 'contextual' in out, 'a retired Type value was written as a Demand'

    def present(text):
        findings = []
        rcq.check_requirements_present(text, cfg['requirement_optional_words'], findings)
        return findings[0]

    ok = needs_file(('A', 'S "a"'), ('B', 'S "b"'))
    assert present(ok)[1], present(ok)
    assert not present(ok.replace('| 2 | B', '| 3 | B'))[1], 'a gap in the row numbers passed'
    assert not present(ok.replace('| 2 | B', '| 1 | B'))[1], 'a repeated row number passed'
    assert not present(ok.replace('| required |', '| Knowledge |', 1))[1], 'an unknown Demand passed'
    # A row whose own text marks it optional must be preferred; the reverse
    # (a row under a preferred heading) is the extractor's judgment.
    optional = needs_file(('Python experience is a plus', 'S "a"'))
    word = present(optional)
    assert not word[1] and 'a plus' in word[2], f'an optional row marked required passed: {word}'
    assert present(optional.replace('| required |', '| preferred |'))[1], 'an optional row marked preferred failed'
    assert present(needs_file(('Python', 'S "a"'), type_='preferred'))[1], 'a preferred row with no optional word failed'
    assert not present(ok.replace('| S "b" |', '|  |'))[1], 'a row with no Source passed'
    assert not present('# JD needs: X | Y\n\n## Requirements\n\nNone.\n')[1], 'an empty extraction passed'
    assert not present(None)[1], 'a missing jd_needs.md passed'


def test_role_intake_hands_classification_to_role_classify():
    """Split 2026-11-09: ranking and axis classification moved out of role-intake
    into role-classify, because role-intake had grown to 193 lines. role-intake
    now hands off with those sections pending, so its checks must leave them
    alone, and role-classify's checks must refuse them until filled.
    """
    import role_classify_qc as rcq
    import role_intake_qc as riq
    log_path = os.path.join(FIXTURE_APP, 'session_log.md')
    research_path = os.path.join(FIXTURE_APP, 'research.md')
    pending = '_(pending)_'
    meta_lines = '- Role Level: {0}\n- Industry: {0}\n- Research Completed Date: {0}\n'
    log = _util.read(log_path).replace('- Source: fixture\n', '- Source: fixture\n' + meta_lines.format(pending))
    axes = log.split('## Axis Classification\n\n', 1)[1].split('\n\n## Axis Gaps', 1)[0]
    handed_log = log.replace(axes, pending).replace('## Axis Gaps\n\nNone.', f'## Axis Gaps\n\n{pending}')
    research = _util.read(research_path)
    handed_research = research.replace('## Axis Gaps\n\nNone.', f'## Axis Gaps\n\n{pending}')

    def detail(check, *args):
        findings = []
        check(*args, findings)
        return findings[0]

    # role-intake's checks ignore what role-classify fills, but not its own fields.
    assert 'pending' not in detail(riq.check_research, handed_research)[2], 'role-intake flagged the pending axis gaps'
    handed_meta = riq._metadata_fields(handed_log)
    dated_log = handed_log.replace(f'Research Completed Date: {pending}', 'Research Completed Date: 2026-01-11')
    session = detail(riq.check_session_log, dated_log, riq._metadata_fields(dated_log))
    assert 'pending' not in session[2] and 'Role Level' not in session[2], session
    assert 'pending' in detail(riq.check_session_log, handed_log, handed_meta)[2], 'a pending research date passed'

    # role-classify's checks refuse the hand-off state until it is filled.
    complete = detail(rcq.check_complete, handed_research, handed_log, handed_meta)
    assert not complete[1] and 'Role Level' in complete[2] and 'Axis Classification' in complete[2], complete

    # The research step fills the date; finalize fills Level, Industry and the axes.
    _util.write(log_path, handed_log)
    blocks = {k: write_block(f'{k}.md', f'## {k.capitalize()}\n\nx\n') for k in ('company', 'role', 'industry')}
    code, out = run('assemble.py', 'research', '--folder', FIXTURE_APP, '--app-id', 'APP-001', '--company', 'Aldridge Pharma',
                    '--role', 'Director, Clinical Data Strategy', '--date', '2026-01-11', '--company-file', blocks['company'],
                    '--role-file', blocks['role'], '--industry-file', blocks['industry'])
    assert code == 0, out
    assert 'Critical Requirements' not in _util.read(research_path), 'the research step wrote requirements'
    assert '- Research Completed Date: 2026-01-11' in _util.read(log_path), 'the research step left the date pending'
    code, out = run('role_classify_assemble.py', 'finalize', '--folder', FIXTURE_APP,
                    '--axis-file', write_block('axes.md', f'## Axis Classification\n\n{axes}\n\n## Axis Gaps\n\nNone'))
    assert code == 0, out
    filled_log, filled_research = _util.read(log_path), _util.read(research_path)
    assert '- Role Level: leadership' in filled_log and '- Industry: pharma' in filled_log, filled_log
    complete = detail(rcq.check_complete, filled_research, filled_log, riq._metadata_fields(filled_log))
    assert complete[1], complete
    code, out = run('role_classify_assemble.py', 'approval', '--folder', FIXTURE_APP)
    # The approval block shows values only; rationales stay in the session log
    # (2026-11-11: the block had grown past 400 words).
    assert code == 0 and 'Level:        leadership' in out, out
    assert 'Orientation:  process-operations\n' in out and 'Work-state:   mature\n' in out, out
    assert 'the deliverables are' not in out and 'established function' not in out, out
    # C4 caps each rationale at config axis_rationale_max_words.
    cap = _config.load()[1]['axis_rationale_max_words']
    assert detail(rcq.check_axis_line_form, filled_log, cap)[1], detail(rcq.check_axis_line_form, filled_log, cap)
    long_log = filled_log.replace('- Work-state: mature - ', '- Work-state: mature - ' + 'word ' * cap)
    assert not detail(rcq.check_axis_line_form, long_log, cap)[1], 'a rationale over the word cap passed'


def test_stale_rule_files_are_flagged():
    """Fixed 2026-11-05 (GitHub #47): the 9-month staleness rule lived only in
    prose, the one check that ran used ~12 months, and 23 of 24 stamped rule
    files were never age-checked. staleness.py reads the threshold from config
    and flags any file at or past it.
    """
    import staleness
    root, cfg = _config.load()
    months = cfg['staleness_months']
    assert months == 9, f'threshold drifted from the decided 9 months: {months}'
    assert staleness.months_old('2026-02', today='2026-11') == 9
    assert staleness.is_stale('2026-02', months, today='2026-11')
    assert not staleness.is_stale('2026-03', months, today='2026-11')
    old = write_block('old_rule.md', '---\nlast_researched: 2020-01\n---\n# Old\n')
    new = write_block('new_rule.md', f'---\nlast_researched: {_util.today_ym()}\n---\n# New\n')
    code, out = run('staleness.py', '--file', old, '--file', new)
    assert code == 0, out
    assert 'old_rule.md' in out and 'new_rule.md' not in out, f'wrong files flagged:\n{out}'


def test_interview_section_is_written_by_script():
    """Built 2026-11-05 (GitHub #40, audit finding F5): four skills built the
    '## Interview: <stage>' block by hand from the template. The script now
    creates it with every required field in template order, changes only the
    named fields on update, adds optional extras after Outcome, and refuses a
    near-miss label as a typo.
    """
    log_path = os.path.join(FIXTURE_APP, 'session_log.md')
    root, cfg = _config.load()
    required = [f.rstrip(':') for f in _util.interview_section_fields(
        _util.read(os.path.join(root, cfg['paths']['templates'], cfg['filenames']['session_log_template'])))]

    def section():
        text = _util.read(log_path)
        m = re.search(r'^## Interview: Hiring Manager\n.*?(?=^## |\Z)', text, re.S | re.M)
        assert m, 'section not written'
        return m.group(0)

    code, out = run('session_log.py', 'interview', '--folder', FIXTURE_APP, '--stage', 'Hiring Manager',
                    '--set', 'Interview date=2026-11-12', '--set', 'Status=scheduled')
    assert code == 0, out
    labels = [ln[2:].split(':')[0] for ln in section().splitlines() if ln.startswith('- ')]
    assert labels == required, f'fields not in template order: {labels}'
    assert '- Interview date: 2026-11-12' in section()

    code, out = run('session_log.py', 'interview', '--folder', FIXTURE_APP, '--stage', 'Hiring Manager',
                    '--set', 'Status=held', '--set', 'Follow-up=pending')
    assert code == 0, out
    body = section()
    assert '- Status: held' in body and '- Interview date: 2026-11-12' in body, body
    assert body.index('- Follow-up: pending') > body.index('- Outcome:'), 'extra field not after Outcome'
    assert _util.read(log_path).count('## Interview: Hiring Manager') == 1, 'section duplicated'

    code, out = run('session_log.py', 'interview', '--folder', FIXTURE_APP, '--stage', 'Hiring Manager',
                    '--set', 'Interveiw date=2026-11-13')
    assert code != 0 and 'did you mean' in out, f'typo label accepted: {out}'


def test_dispatch_prompts_are_printed_not_composed():
    """Built 2026-11-05 (GitHub #71): hand-composed prompts drifted silently (file
    paths for content, a summarized JD, a retyped JD). Prompts now come from one
    script, sources go by path, and a missing input stops the run.
    """
    def prompt(agent, *extra):
        code, out = run('dispatch_prompt.py', agent, '--folder', FIXTURE_APP, *extra)
        assert code == 0, f'{agent}: {out}'
        return out.split('=== PROMPT ===\n')[1].split('\n=== END ===')[0]

    jd_path = os.path.join(FIXTURE_APP, 'jd.md')
    for agent in ('company-research', 'role-research', 'industry-research', 'critical-requirements-extractor'):
        text = prompt(agent)
        assert 'Company: Aldridge Pharma' in text and jd_path in text, text
        assert 'Fixture job description' not in text, 'JD text was pasted into the prompt'
    assert 'actually operates in' in prompt('industry-research')
    ranker = prompt('jd-needs-ranker')
    company_path = os.path.join(FIXTURE_APP, 'scratch', 'company.md')
    assert jd_path in ranker and company_path in ranker, ranker
    assert os.path.join(FIXTURE_APP, 'research.md') not in ranker, 'the ranker was given the whole research file'
    company = _util.read(company_path)
    assert company.startswith('## Company\n') and '## Role' not in company, f'the Company slice is wrong: {company[:200]}'
    assert os.path.join(FIXTURE_APP, 'jd_needs.md') in ranker, 'the ranker was not given the requirements'
    assert 'Comms' not in prompt('axis-classifier'), 'an absent optional file was listed'
    _util.write(os.path.join(FIXTURE_APP, 'comms.md'), 'A note.')
    assert 'Comms: ' in prompt('axis-classifier')

    # The CV Notes reach the writer byte for byte.
    code, out = run('dispatch_prompt.py', 'cv-architect', '--folder', FIXTURE_APP)
    assert code != 0 and 'Tier' in out, f'a leadership role with no tier got through: {out}'
    _util.write(os.path.join(FIXTURE_APP, 'cv_content.md'), '# Name\n')
    _util.write(os.path.join(FIXTURE_APP, 'retrieval.md'), '# Retrieval Manifest\n')
    assert 'CV content: ' in prompt('hiring-manager') and 'JD: ' in prompt('hiring-manager')
    architect = prompt('cv-architect', '--tier', 'function-lead')
    assert 'Mode: draft' in architect and 'Tier: function-lead' in architect, architect
    assert os.path.join('rules', 'industries', 'pharma.md') in architect, architect
    notes = _util.read(os.path.join(FIXTURE_APP, 'scratch', 'cv_notes.md'))
    gap = _util.read(os.path.join(FIXTURE_APP, 'gap_analysis.md'))
    assert notes.strip() and notes in gap, f'CV Notes were not copied verbatim: {notes!r}'

    # Run-produced input goes by file, and continued agents get only that.
    code, out = run('dispatch_prompt.py', 'cv-architect', '--folder', FIXTURE_APP, '--mode', 'revise', '--tier', 'function-lead')
    assert code != 0 and 'input-file' in out, out
    brief = write_block('brief.md', 'Findings.')
    continued = prompt('hiring-manager', '--continued', '--input-file', brief)
    assert brief in continued and 'gap_analysis' not in continued, continued
    code, out = run('dispatch_prompt.py', 'qc-gap-analysis', '--folder', FIXTURE_APP, '--continued', '--input-file', brief)
    assert code != 0, 'a QC agent was treated as continued'

    # A missing required file stops the run rather than dropping out of the prompt.
    os.remove(os.path.join(FIXTURE_APP, 'research.md'))
    code, out = run('dispatch_prompt.py', 'qc-role-intake', '--folder', FIXTURE_APP)
    assert code != 0 and 'research.md' in out, f'a prompt was printed without its source: {out}'

    # The skills use it, and no listed step still hands an agent pasted content.
    skills = os.path.join(REPO_ROOT, '.claude', 'skills')
    for skill, agents in (('role-intake', ['<agent>', 'qc-role-intake']),
                          ('role-classify', ['jd-needs-ranker', 'axis-classifier', 'qc-role-classify']),
                          ('cv-targeted', ['<agent>', 'cv-architect']), ('gap-analysis', ['qc-gap-analysis'])):
        text = _util.read(os.path.join(skills, skill, 'SKILL.md'))
        for agent in agents:
            assert f'dispatch_prompt.py {agent}' in text, f'{skill} does not print the {agent} prompt'
    assert 'giving each the JD text' not in _util.read(os.path.join(skills, 'role-intake', 'SKILL.md'))


def test_gap_verdicts_come_from_checked_claims():
    """Built 2026-11-05 (GitHub #72): the detector wrote 'its only Veeva Vault use is
    eTMF' with the other Vault systems in its context, and read silence as a gap.
    It now answers parts with proof; a script checks the proof and sets the verdict.
    """
    import gap_verdicts as gv
    reference = '## Technical Experience\n\n**Clinical:** Veeva Vault, Vault Submissions, Medidata Rave\n'
    evidence = ('ID: EX-001\nDescription: **Ran the vendor oversight program.**\n\n'
                'ID: PR-015\nObjective: Built a *requirements* graph.\n')

    def one(*parts):
        return gv.derive([{'requirement_id': 'CR-001', 'parts': list(parts)}], reference, evidence, 1)

    direct = {'part': 'vendors', 'answer': 'direct', 'evidence_id': 'EX-001', 'quote': 'ran the vendor  oversight program'}
    reworded = {'part': 'graph', 'answer': 'reworded', 'evidence_id': 'PR-015.03', 'quote': 'Built a requirements graph',
                'role_term': 'ontology', 'candidate_term': 'graph'}
    absent = {'part': 'IRT', 'answer': 'absent', 'searched_terms': ['Suvoda', 'IRT']}
    silent = {'part': 'audience', 'answer': 'not-stated', 'not_stated': 'Was this for executives?'}
    tool = {'part': 'Vault', 'answer': 'direct', 'evidence_id': 'reference', 'quote': 'Vault Submissions'}

    def verdict(*parts):
        records, rejected = one(*parts)
        assert not rejected, rejected
        return records[0]

    assert verdict(direct, tool)['verdict'] == 'covered'
    assert verdict(direct, tool)['evidence'] == ['EX-001'], 'reference lines have no ID to cite'
    assert verdict(direct, reworded)['verdict'] == 'covered', 'one reworded part sank a requirement'
    assert verdict(reworded)['verdict'] == 'language-shift'
    assert verdict(reworded)['language_shift']['role_terminology'] == 'ontology'
    assert verdict(silent)['verdict'] == 'not-stated', 'silence was read as something else'
    assert verdict(silent)['question'] == 'Was this for executives?'
    assert verdict(absent)['verdict'] == 'gap' and verdict(absent)['missing'] == 'IRT: not found'
    assert verdict(direct, absent)['verdict'] == 'gap', 'absent parts matched shown parts'
    assert verdict(silent, absent)['verdict'] == 'gap', 'a real absence was hidden by silence'

    # One open part leaves a partial that says what is shown and what is open.
    partial = verdict(direct, tool, silent)
    assert partial['verdict'] == 'partial', 'one open part sank or hid a requirement'
    assert partial['shown_parts'] == ['vendors', 'Vault'] and partial['open_parts'] == ['audience'], partial
    assert verdict(direct, tool, absent)['verdict'] == 'partial'

    # The APP-023 failure: a system claimed absent that the profile lists.
    records, rejected = one({'part': 'Vault', 'answer': 'absent', 'searched_terms': ['Vault Submissions']})
    assert not records and 'in the profile' in rejected['CR-001'][0], rejected
    # A term must match whole words, so 'IRT' is not found inside 'shIRT'.
    assert gv.derive([{'requirement_id': 'CR-001', 'parts': [absent]}], reference + 'shirt', evidence, 1)[0]

    bad = [dict(direct, quote='Ran a program nobody ran'), dict(direct, evidence_id='EX-999'),
           dict(direct, reasoning='its only use is eTMF'), {'part': 'x', 'answer': 'direct', 'evidence_id': 'EX-001'},
           {'part': 'x', 'answer': 'maybe'}]
    for part in bad:
        records, rejected = one(part)
        assert not records and rejected, f'accepted a bad claim: {part}'
    assert gv.derive([], reference, evidence, 1)[1]['CR-001'] == ['no parts answered']

    # A claim that keeps failing becomes a question, never a verdict.
    records, _ = gv.derive([{'requirement_id': 'CR-001', 'parts': [bad[0]]}], reference, evidence, 1, final=True)
    assert records[0]['verdict'] == 'not-stated' and 'Could not be verified' in records[0]['question'], records

    # End to end through the command line.
    scratch = os.path.join(RUN_DIR, 'gap_scratch')
    os.makedirs(scratch)
    _util.write(os.path.join(scratch, 'gap_detector_context.md'),
                '# Critical Requirements\n\n| 1 | Veeva Vault | required | x |\n\n# Profile reference sections\n\n' + reference)
    _util.write(os.path.join(scratch, 'gap_detector_evidence_0.md'), evidence)
    output = os.path.join(scratch, 'gap_detector_output.json')
    _util.write(output, json.dumps({'assessments': [{'requirement_id': 'CR-001', 'parts': [
        {'part': 'Vault', 'answer': 'absent', 'searched_terms': ['Veeva Vault']}]}]}))
    code, out = run('gap_verdicts.py', 'derive', '--temp-dir', scratch)
    assert code == 1 and '=== PROMPT ===' in out and 'in the profile' in out, out
    assert not os.path.exists(os.path.join(scratch, 'gap_detector_verdicts.json')), 'verdicts written despite a rejection'
    _util.write(output, json.dumps({'assessments': [{'requirement_id': 'CR-001', 'parts': [tool]}]}))
    code, out = run('gap_verdicts.py', 'derive', '--temp-dir', scratch)
    assert code == 0 and 'covered: 1' in out, out

    skill = _util.read(os.path.join(REPO_ROOT, '.claude', 'skills', 'gap-analysis', 'SKILL.md'))
    assert 'gap_verdicts.py derive' in skill and 'Not-stated items' in skill


def test_builder_prompts_share_one_script():
    """Built 2026-11-05 (GitHub #71): five builders each pasted the draft, research,
    and sibling text into their agents' prompts. One script now prints path-only
    prompts for all five, and sibling Adjacency text is copied verbatim.
    """
    import axis_dispatch
    import axis_utils
    root, cfg = _config.load()
    scratch = os.path.join(RUN_DIR, 'bscratch')
    os.makedirs(scratch)

    def dispatch(kind, *extra):
        return run('axis_dispatch.py', kind, 'industries', 'test-value', '--scratch-dir', scratch, *extra)

    def prompt(kind, *extra):
        code, out = dispatch(kind, *extra)
        assert code == 0, f'{kind}: {out}'
        return out.split('=== PROMPT ===\n')[1].split('\n=== END ===')[0]

    assert 'siblings: ' in prompt('research') and 'pharma' in prompt('research')
    code, out = dispatch('reconciler', '--mode', 'create')
    assert code != 0 and 'value_file.md' in out, f'a prompt was printed without the draft: {out}'
    code, out = dispatch('reconciler')
    assert code != 0 and '--mode' in out, out

    for name, text in (('value_file.md', 'DRAFT TEXT'), ('research_findings.md', 'FINDINGS'),
                       ('sibling_edits.json', '[]'), ('registry_entry.md', '- entry'),
                       ('qc_result.json', json.dumps({'checks': [{'id': 'H2', 'suggestions': ['GMP']}]}))):
        _util.write(os.path.join(scratch, name), text)

    reconciler = prompt('reconciler', '--mode', 'create')
    assert 'DRAFT TEXT' not in reconciler and 'value_file.md' in reconciler, reconciler
    copied = _util.read(os.path.join(scratch, 'sibling_adjacency.md'))
    pharma = _util.read(axis_utils.value_file_path(root, cfg, 'industries', 'pharma.md'))
    start, end = axis_utils.find_section_bounds(pharma, 'Adjacency')
    assert f'# Sibling: pharma\n\n{pharma[start:end]}' in copied, 'sibling text was not copied verbatim'

    qc = prompt('qc', '--mode', 'create')
    assert 'FINDINGS' not in qc and 'research_findings.md' in qc and 'acronym_suggestions: GMP' in qc, qc
    assert 'sibling pharma: ' in qc and 'sibling_edits.json' in qc, qc

    # Every builder and its agents use it; no input list is left in the skills.
    for name, axis in (('industry', 'industries'), ('specialty', 'specialties'), ('orientation', 'orientations'),
                       ('level', 'levels'), ('work-state', 'work-states')):
        skill = _util.read(os.path.join(REPO_ROOT, '.claude', 'skills', f'{name}-builder', 'SKILL.md'))
        for kind in ('research', 'reconciler', 'qc'):
            assert f'axis_dispatch.py {kind} {axis}' in skill, f'{name}-builder does not print its {kind} prompt'
        assert '`drafted_value_file`:' not in skill, f'{name}-builder still lists pasted inputs'
        agents = os.path.join(REPO_ROOT, '.claude', 'agents')
        assert 'path to the new' in _util.read(os.path.join(agents, f'{name}-builder-reconciler.md'))
        assert '`value_file_text`: path' in _util.read(os.path.join(agents, f'qc-{name}-builder.md'))


def test_render_will_not_overwrite_a_hand_edited_docx():
    """Fixed 2026-11-05 (GitHub #69): hand edits to the rendered .docx are never
    synced back to cv_content.md, and re-rendering silently destroyed them.
    """
    cv = write_block('render_cv.md', '# Name\nCity, ST | a@b.c\n\n## Professional Summary\nShort. <!-- src: EX-001 -->\n')
    out = os.path.join(RUN_DIR, 'render_test.docx')

    def render(*extra):
        return run('cv_to_docx.py', '--cv-file', cv, '--out', out, *extra)

    code, msg = render()
    assert code == 0 and os.path.exists(out), msg
    code, msg = render()
    assert code == 0, f'an unedited .docx was refused: {msg}'

    with open(out, 'ab') as f:
        f.write(b'hand edit')
    edited = open(out, 'rb').read()
    code, msg = render()
    assert code == 2 and 'Refused' in msg, f'an edited .docx was overwritten: {code} {msg}'
    assert open(out, 'rb').read() == edited, 'the refused run changed the file'

    code, msg = render('--overwrite-edited')
    assert code == 0 and open(out, 'rb').read() != edited, msg
    code, msg = render()
    assert code == 0, f'the record was not refreshed after an overwrite: {msg}'

    other = os.path.join(RUN_DIR, 'older_cv.docx')
    _util.write(other, 'a file this script has no record of')
    code, msg = run('cv_to_docx.py', '--cv-file', cv, '--out', other)
    assert code == 2, f'a .docx with no record was overwritten: {msg}'


def test_cv_rules_account_for_every_inventory_section():
    """Built 2026-11-05 (GitHub #68): CV sections followed the usual shape. Every
    inventory section must now have a stated CV outcome, so a new inventory section
    fails here until someone decides, and every CV section named must be real.
    """
    import cv_qc
    import cv_to_docx
    root, cfg = _config.load()
    rules = _util.read(os.path.join(root, cfg['paths']['cv_rules'], cfg['filenames']['cv_structure_file']))
    block = re.search(r'(?ms)^## Which sections appear.*?^```\s*\nInventory section -> CV section\n(.*?)\n```', rules)[1]
    mapping = dict(line.split(' -> ') for line in block.splitlines())

    template = _util.read(os.path.join(root, cfg['paths']['templates'], cfg['filenames']['inventory_template']))
    skeleton = re.search(r'(?ms)^## Document skeleton.*?^```\s*\n(.*?)\n```', template)[1]
    sections = set(re.findall(r'(?m)^## (.+)$', skeleton)) - {'Table of Contents'}
    assert set(mapping) == sections, f'inventory and CV rules differ: {sorted(set(mapping) ^ sections)}'

    structure = cv_qc.parse_section_order(rules)
    known = set(structure['order']) | structure['work_output']
    for inventory_section, outcome in mapping.items():
        if outcome.startswith(('none', 'not designed')):
            continue
        for cv_section in outcome.split(', '):
            assert cv_section.lower() in known, f'{inventory_section} points at unknown section {cv_section}'

    assert structure['order'].index('languages') < structure['order'].index('technical proficiencies')
    assert 'languages' in cv_to_docx.FORCE_BULLET_SECTIONS, 'Languages lines would not render as bullets'


def test_notes_checklist_follows_the_appendix_order():
    """Fixed 2026-11-05 (GitHub #67): the cue-card said to get to Q8 early while the
    checklist put Q8 sixth, and nothing compared the two. add-round now refuses a
    checklist that disagrees with the Appendix, while still allowing questions to
    be skipped, reworded, or added.
    """
    import notes_assemble as na
    q1, q2, q3, q4 = 'How is the team set up?', 'Who owns the roadmap?', 'What does success look like?', 'Why is this open?'
    prep = (f'## Question Bank (questions to ask them)\n\n**Topic**\n\n- **Q1:** {q1}\n  - [Listen for: x]\n\n'
            f'- **Q2:** Who owns\n  the roadmap?\n  - [Listen for: y]\n\n- **Q3:** {q3}\n\n- **Q4:** {q4}\n\n'
            '## Concerns to Resolve\n\n'
            '## Hiring Manager - Pat Lee\n\n- Prioritize from Question Bank: Q3, Q1.\n\n'
            '## Panel - Three People\n\n- Prioritize from Question Bank, in this order:\n  - Q2, Q3.\n  - Then if time allows: Q1.\n- Do not raise: comp.\n')

    assert na._priority_labels(prep, 'Panel') == ['Q2', 'Q3'], na._priority_labels(prep, 'Panel')
    assert na.checklist_problems(prep, 'Panel', [f'(P) {q2}', f'(P) {q3}', q1]) == [], "an 'if time allows' item needs no (P)"
    assert na._bank_questions(prep)[na._squash(q2)] == 'Q2', 'a wrapped question was not read whole'
    good = [f'(P) {q3}', f'(P) {q1}', q4, 'A question I added myself']
    assert na.checklist_problems(prep, 'Hiring Manager', good) == []
    assert na.checklist_problems(prep, 'Hiring Manager', [f'(P) {q1}']) == [], 'skipping a question was refused'
    assert na.checklist_problems(prep, 'Hiring Manager', ['(P) Reworded question', f'(P) {q1}']) == []
    assert na.checklist_problems(prep, 'No Such Round', [f'(P) {q1}', f'(P) {q3}']) == [], 'a round with no block was refused'

    bad_order = na.checklist_problems(prep, 'Hiring Manager', [f'(P) {q1}', f'(P) {q3}'])
    assert len(bad_order) == 1 and 'Q3 comes after Q1' in bad_order[0], bad_order
    assert 'not in the Appendix' in na.checklist_problems(prep, 'Hiring Manager', [f'(P) {q4}'])[0]
    assert 'not marked (P)' in na.checklist_problems(prep, 'Hiring Manager', [q3])[0]
    assert 'sits below' in na.checklist_problems(prep, 'Hiring Manager', [q4, f'(P) {q3}'])[0]

    # The real entry point refuses, writes nothing, and keeps the payload.
    root, cfg = _config.load()
    _util.write(os.path.join(FIXTURE_APP, cfg['filenames']['interview_prep_file']), prep)
    code, out = run('notes_assemble.py', 'init', '--folder', FIXTURE_APP, '--app-id', 'APP-001',
                    '--company', 'Aldridge', '--role', 'Director')
    notes_path = os.path.join(FIXTURE_APP, cfg['filenames']['interview_notes_file'])
    before = _util.read(notes_path)

    def add(questions):
        payload = write_block('payload.json', json.dumps({
            'stage': 'Hiring Manager', 'date': '2026-11-12', 'datetime': '2026-11-12 14:00 EST', 'medium': 'video',
            'format': 'single', 'cue_card': [], 'interviewers': [], 'questions': questions}))
        return payload, run('notes_assemble.py', 'add-round', '--folder', FIXTURE_APP, '--payload', payload)

    payload, (code, out) = add([f'(P) {q1}', f'(P) {q3}'])
    assert code != 0 and 'Q3 comes after Q1' in out, out
    assert _util.read(notes_path) == before and os.path.exists(payload), 'a refused round changed something'
    payload, (code, out) = add(good)
    assert code == 0, out
    assert '- [ ] (P) What does success look like?' in _util.read(notes_path)


def test_round_prepped_before_booking_passes_only_as_unscheduled():
    """Fixed 2026-11-05 (GitHub #63): a round prepped before it was booked could not
    pass S1, since nothing could say it had no date yet. Blank is legal only with
    an explicit status, so a scheduled round missing its date is still a defect.
    """
    import prep_interview_qc
    import prep_qc
    root, cfg = _config.load()
    fields = _util.interview_section_fields(
        _util.read(os.path.join(root, cfg['paths']['templates'], cfg['filenames']['session_log_template'])))
    log_path = os.path.join(FIXTURE_APP, 'session_log.md')

    def set_fields(stage, *pairs):
        args = ['interview', '--folder', FIXTURE_APP, '--stage', stage]
        for pair in pairs:
            args += ['--set', pair]
        code, out = run('session_log.py', *args)
        assert code == 0, out

    def s1(module):
        findings = []
        module.check_session_log(_util.read(log_path), fields, findings)
        return next(f for f in findings if f[0] == 'S1')

    for module, stage in ((prep_interview_qc, 'Hiring Manager'), (prep_qc, 'Recruiter Screen')):
        set_fields(stage, 'Status=unscheduled', 'Outcome=pending')
        assert s1(module)[1], f'an unscheduled round failed: {s1(module)}'
        set_fields(stage, 'Status=scheduled')
        result = s1(module)
        assert not result[1] and 'blank' in result[2], f'a scheduled round with no date passed: {result}'
        set_fields(stage, 'Status=unscheduled', 'Interview date=2026-11-12')
        assert not s1(module)[1], 'an unscheduled round holding a date passed'
        set_fields(stage, 'Status=scheduled')
        assert s1(module)[1], s1(module)
        set_fields(stage, 'Interview date=Nov 12 at noon')
        assert not s1(module)[1], 'a prose date passed'
        set_fields(stage, 'Interview date=', 'Status=cancelled 2026-11-10')
        assert s1(module)[1], f'a round cancelled before booking failed: {s1(module)}'

    # A first booking must not be recorded as a move.
    set_fields('Peer / Team', 'Status=unscheduled', 'Outcome=pending')
    code, out = run('interview_lifecycle.py', 'reschedule', '--folder', FIXTURE_APP,
                    '--stage', 'Peer / Team', '--new-datetime', '2026-11-20 14:00 EST')
    assert code != 0 and 'first date' in out, f'reschedule accepted an unscheduled round: {out}'
    assert 'moved to' not in _util.read(log_path), 'a first booking was recorded as a move'
    # Cancelling one still works, and then leaves no S1 problem for later rounds.
    code, out = run('interview_lifecycle.py', 'cancel', '--folder', FIXTURE_APP, '--stage', 'Peer / Team')
    assert code == 0, out
    assert '- Outcome: n/a (round cancelled)' in _util.read(log_path)


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
