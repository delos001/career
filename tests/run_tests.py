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
                    '--research-file', os.path.join(FIXTURE_APP, 'research.md'),
                    '--requirements-file', inputs['requirements'],
                    '--eligibility-file', inputs['eligibility'], '--themes-file', inputs['themes'])
    assert code == 0, out
    path = os.path.join(FIXTURE_APP, 'gap_analysis.md')
    built = _util.read(path)
    assert 'Fit Score' not in built, built
    assert built.index('## Coverage Picture') < built.index('## Gap Themes') \
        < built.index('## Recommendation') < built.index('## Requirements'), built
    assert '| Must-have (4) | 1 | 1 | 0 | 1 | 1 | 0 |' in built, built
    assert '**Unmet Must-Haves:** 1' in built, built
    assert all('PASS' in line for line in report().values()), report()

    def fails_check(check, old, new):
        _util.write(path, built.replace(old, new))
        assert old in built, f'{old!r} is not in the artifact, so this proves nothing'
        result = report()[check]
        assert 'FAIL' in result, f'{check} passed after replacing {old!r}: {result}'
        return result

    assert 'does not match' in fails_check('G10', '| Must-have (4) | 1 | 1 | 0 | 1 | 1 | 0 |',
                                           '| Must-have (4) | 2 | 1 | 0 | 1 | 0 | 0 |')
    assert 'CR-005' in fails_check('G12', 'CR-003, CR-004, CR-005, CR-006', 'CR-003, CR-004, CR-006')
    fails_check('G12', '(reader-dependent)', '(depends)')
    fails_check('G13', '- They screen for transferable capability (CR-004, CR-005).', '')
    fails_check('G9', '**Recommendation:** Proceed with caution', '**Recommendation:** Proceed')


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
    assert '(CR-004)' in text, 'the fixture names no CR-004 condition, so this proves nothing'
    _util.write(path, text.replace(' (CR-004)', ''))
    line = g14()
    assert 'FAIL' in line and 'CR-004' in line, f'an unnamed must-have passed: {line}'


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
    import role_intake_qc as riq
    root, cfg = _config.load()
    tiers = riq.leadership_tiers(root, cfg)
    assert tiers == ['delivery-lead', 'function-lead', 'multi-function-head', 'executive'], tiers

    def result(level, tier_line):
        log = (f'## Axis Classification\n\n- Orientation: x (primary) - r\n- Industry: x - r\n'
               f'- Specialty: x - r\n- Level: {level} - r\n{tier_line}- Work-state: x - r\n\n## Axis Gaps\n\nNone\n')
        findings = []
        riq.check_tier(log, tiers, findings)
        return findings[0]

    assert result('leadership', '- Tier: function-lead - scope spans R&D\n')[1]
    assert not result('leadership', '')[1], 'leadership without a tier passed'
    assert not result('leadership', '- Tier: senior-vp - r\n')[1], 'unknown tier passed'
    assert result('ic', '')[1]
    assert not result('ic', '- Tier: function-lead - r\n')[1], 'ic with a tier passed'


def test_requirement_text_keeps_jd_modifiers():
    """Fixed 2026-11-05 (GitHub #83): the extractor dropped 'familiarity with'
    from a must-have and nothing compared requirement text with the JD. Modifiers
    are read from the JD clause holding the quote, so a narrow quote cannot step
    around the check.
    """
    import role_intake_qc as riq
    _, cfg = _config.load()
    jd = ('Strong knowledge of the industry, including familiarity with drug discovery.\n'
          "Bachelor's degree required; advanced degree preferred.\n"
          'Master’s degree with 6 years of experience.\n')

    def result(text, source):
        research = ('## Critical Requirements\n\n| # | Text | Type | Source |\n|---|---|---|---|\n'
                    f'| 1 | {text} | must-have | {source} |\n\n## Axis Gaps\n')
        findings = []
        riq.check_requirement_text(research, jd, cfg['requirement_qualifiers'], cfg['requirement_year_count'], findings)
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
    assert not result('Degree', 'Quals #2')[1], 'a row with no quote passed'
    assert result('Degree', 'Quals #2 "Bachelor\'s degree required"; also Summary')[1], 'a section pointer after the quote broke the row'


def test_split_requirement_keeps_each_year_count():
    """A clause can hold one year count per requirement. Requiring both counts on
    every row failed a correct split of '10 years..., with at least 5 years...',
    which left two tests sharing one gap verdict. Each count now needs to survive
    on some row from the clause, and a count lost from all of them still fails.
    """
    import role_intake_qc as riq
    _, cfg = _config.load()
    jd = 'Minimum of 10 years in the industry, with at least 5 years in people management.\n'

    def result(*rows):
        body = ''.join(f'| {i} | {text} | must-have | Quals #1 "{quote}" |\n'
                       for i, (text, quote) in enumerate(rows, 1))
        research = ('## Critical Requirements\n\n| # | Text | Type | Source |\n|---|---|---|---|\n'
                    f'{body}\n## Axis Gaps\n')
        findings = []
        riq.check_requirement_text(research, jd, cfg['requirement_qualifiers'], cfg['requirement_year_count'], findings)
        return findings[0]

    ten = 'Minimum of 10 years in the industry'
    five = 'at least 5 years in people management'
    split = result((ten, ten), (five, five))
    assert split[1], f'a correct split failed: {split}'
    assert result((f'{ten}, with {five}', ten))[1], 'the whole clause on one row failed'
    lost = result((ten, ten), ('people management', 'people management'))
    assert not lost[1] and '5 years' in lost[2], f'a count lost from every row passed: {lost}'
    assert not result(('Minimum of 8 years in the industry', ten), (five, five))[1], 'a changed count passed'


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
