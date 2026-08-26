#!/usr/bin/env python3
"""
run_tests.py - invariant checks for the profile-update machinery

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
import os
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


def queued_ids(staging_text):
    """Return the PU-NNN set still waiting in the queue.

    parse_staging returns records rather than a mapping, so the ids have to be
    pulled out; parse_migrated already returns {id: outcome}.
    """
    return {entry['id'] for entry in pu.parse_staging(staging_text)}


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


# ---------------------------------------------------------------------------
# The checks
# Each name is the defect it exists to catch. The docstring says what shipped.
# ---------------------------------------------------------------------------

def test_counter_never_reissues_a_number():
    """Shipped 2026-08-26: promoting entries let the ID counter walk backwards.

    The counter read the queue only, so removing the highest-numbered entry
    lowered the maximum and the next one issued reused a number a closed
    application's gap_analysis.md already cited.
    """
    _, staging = docs()
    issued = queued_ids(staging) | set(pu.parse_migrated(staging))

    # Drain the queue completely, which is the state that exposed the bug.
    for entry in pu.parse_staging(staging):
        ok('drop', '--pu', entry['id'])

    _, staging = docs()
    assert not pu.parse_staging(staging), 'queue should be empty'

    # Every issued number must still be on record, and the next one must be new.
    recorded = set(pu.parse_migrated(staging))
    assert issued <= recorded, f'lost from the record: {sorted(issued - recorded)}'

    import staging_append
    nxt = staging_append._next_pu_id(staging)
    assert nxt not in issued, f'{nxt} was already issued'
    assert int(nxt.split('-')[1]) > max(int(i.split('-')[1]) for i in issued), \
        f'{nxt} does not exceed every number ever issued'


def test_entry_cannot_leave_the_queue_unrecorded():
    """The invariant the whole design rests on.

    Every PU-NNN ever issued appears exactly once across the two sections. If
    an entry can leave without leaving its number, the counter breaks again and
    a past application's closure pointer stops resolving.
    """
    _, staging = docs()
    before = queued_ids(staging) | set(pu.parse_migrated(staging))

    write_block('b.md', EX_BLOCK)
    ok('insert', '--prefix', 'EX', '--pu', 'PU-003',
       '--block-file', os.path.join(RUN_DIR, 'b.md'))
    ok('close', '--pu', 'PU-003')
    ok('drop', '--pu', 'PU-004')

    _, staging = docs()
    queued, migrated = queued_ids(staging), set(pu.parse_migrated(staging))
    assert not (queued & migrated), f'in both sections: {sorted(queued & migrated)}'
    assert queued | migrated == before, 'a PU number was lost or invented'


def test_close_refuses_without_a_recorded_write():
    """Shipped 2026-08-26: close verified that its targets existed, which for an
    enrichment or a list item proved nothing, because both existed beforehand.

    A failed or skipped write could therefore be closed against the entry it was
    meant to change, writing a permanently false migrated line.
    """
    out = fails('close', '--pu', 'PU-003')
    assert 'records no writes' in out, out

    # And it still refuses after a write that went to a DIFFERENT entry.
    ok('list-add', '--pu', 'PU-004',
       '--target', 'Technical Experience / Programming, Data & Analytics / Platforms',
       '--item', 'Tableau')
    out = fails('close', '--pu', 'PU-003')
    assert 'records no writes' in out, out


def test_duplicate_and_writes_are_mutually_exclusive():
    """'nothing needed writing' and 'these writes happened' cannot both hold."""
    ok('list-add', '--pu', 'PU-004',
       '--target', 'Technical Experience / Programming, Data & Analytics / Platforms',
       '--item', 'Tableau')
    out = fails('close', '--pu', 'PU-004', '--duplicate')
    assert 'not a duplicate' in out, out
    # An untouched entry closes as a duplicate cleanly.
    ok('close', '--pu', 'PU-003', '--duplicate')
    assert pu.parse_migrated(docs()[1])['PU-003'] == 'duplicate'


def test_made_up_targets_are_rejected():
    """Shipped 2026-08-26: any ID whose prefix the inventory template did not
    define passed unverified, so ST-999 or a positioning target resolved clean.
    """
    for bad in ('EX-999', 'ST-999', 'ZZ-123'):
        out = fails('record', '--pu', 'PU-003', '--target', bad)
        assert 'exists in neither' in out, f'{bad}: {out}'
    # A real narratives ID is accepted; that document has no template and the
    # earlier fix must not have closed the door on it.
    ok('record', '--pu', 'PU-003', '--target', 'ST-001')
    ok('record', '--pu', 'PU-003', '--target', 'DC-001')


def test_concurrent_inserts_do_not_collide():
    """The APP-NNN collision class: two writes in one run claiming one number.

    insert assigns the ID at write time rather than letting a caller pick one,
    so a second insert cannot reuse the first's number.
    """
    write_block('b.md', EX_BLOCK)
    first = ok('insert', '--prefix', 'EX', '--pu', 'PU-003',
               '--block-file', os.path.join(RUN_DIR, 'b.md'))
    second = ok('insert', '--prefix', 'EX', '--pu', 'PU-003',
                '--block-file', os.path.join(RUN_DIR, 'b.md'))
    assert first != second, f'both inserts claimed {first}'
    ids = [e['id'] for e in pu.parse_entries(docs()[0])]
    assert len(ids) == len(set(ids)), 'duplicate IDs in the inventory'


def test_new_entry_lands_in_its_role_group_in_order():
    """Shipped 2026-08-25 as a dead end: an entry could be placed outside the
    group its Role names, or out of sort order within it.
    """
    write_block('b.md', EX_BLOCK)
    new_id = ok('insert', '--prefix', 'EX', '--pu', 'PU-003',
                '--block-file', os.path.join(RUN_DIR, 'b.md'))
    inventory, _ = docs()

    start, end = pu._section_bounds(inventory, 'RL-002')
    group = '\n'.join(inventory.split('\n')[start:end])
    assert new_id in [e['id'] for e in pu.parse_entries(group)], \
        f'{new_id} did not land in its RL-002 group'

    keys = [pu._ex_sort_key(e['field_map'], e['number'])
            for e in pu.parse_entries(group) if e['prefix'] == 'EX']
    assert keys == sorted(keys), f'RL-002 group is out of sort order: {keys}'


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
    role = ok('insert', '--prefix', 'RL', '--pu', 'PU-003',
              '--block-file', os.path.join(RUN_DIR, 'r.md'))
    inventory, _ = docs()
    assert pu._section_bounds(inventory, role) is not None, \
        f'no "### {role}" group was created under Experience Entries'

    # And an entry for that role now has somewhere to go.
    write_block('b.md', EX_BLOCK.replace('Role: RL-002', f'Role: {role}'))
    ok('insert', '--prefix', 'EX', '--pu', 'PU-003',
       '--block-file', os.path.join(RUN_DIR, 'b.md'))


def test_list_add_is_additive():
    """A whole-line rewrite on a roster of thirty tool names loses items.

    list-add appends and refuses a repeat; it must never drop or reorder.
    """
    target = 'Technical Experience / Programming, Data & Analytics / Platforms'
    root, cfg = _config.load()
    tpl = _util.read(pu._template_path(root, cfg))
    sections = pu.list_sections(tpl, pu.parse_template(tpl))
    before = pu.split_items(pu.resolve_list_target(docs()[0], target, sections)['value'])

    ok('list-add', '--pu', 'PU-004', '--target', target, '--item', 'Tableau')
    after = pu.split_items(pu.resolve_list_target(docs()[0], target, sections)['value'])
    assert after[:len(before)] == before, f'existing items changed: {before} -> {after}'
    assert after[-1] == 'Tableau'

    out = fails('list-add', '--pu', 'PU-004', '--target', target, '--item', 'tableau')
    assert 'already listed' in out, out


def test_enrichment_preserves_the_rest_of_the_entry():
    """set replaces one field's span; it must not drop a sibling, reorder the
    roster, or land on a neighbouring entry.
    """
    before = {e['id']: e['field_map'] for e in pu.parse_entries(docs()[0])}
    write_block('v.md', 'Enrollment projections now run from one reviewed model.')
    ok('set', '--id', 'EX-003', '--pu', 'PU-003', '--field', 'Impact',
       '--value-file', os.path.join(RUN_DIR, 'v.md'))

    after = {e['id']: e['field_map'] for e in pu.parse_entries(docs()[0])}
    assert set(before) == set(after), 'an entry appeared or vanished'
    assert after['EX-003']['Impact'] != before['EX-003']['Impact'], 'no change applied'
    assert set(after['EX-003']) == set(before['EX-003']), 'field roster changed'
    for entry_id in before:
        if entry_id != 'EX-003':
            assert after[entry_id] == before[entry_id], f'{entry_id} was altered'


def test_document_stays_valid_after_writes():
    """Any sequence of writes must leave a document the checker still passes."""
    write_block('b.md', EX_BLOCK)
    new_id = ok('insert', '--prefix', 'EX', '--pu', 'PU-003',
                '--block-file', os.path.join(RUN_DIR, 'b.md'))
    ok('list-add', '--pu', 'PU-004',
       '--target', 'Technical Experience / Programming, Data & Analytics / Platforms',
       '--item', 'Tableau')
    ok('close', '--pu', 'PU-003')
    ok('close', '--pu', 'PU-004')

    code, out = run('profile_update_qc.py', 'check')
    assert code == 0, f'checker failed after a normal run:\n{out}'
    assert new_id in pu.parse_migrated(docs()[1])['PU-003']


# ---------------------------------------------------------------------------
# The checker must actually check
# The 2026-08-25 axis-drift root cause was three QC scripts written to accept
# both the correct shape and the drifted one. A check that tolerates two shapes
# has stopped checking, and nothing detects that from the passing side. So each
# case below breaks the document deliberately and requires a complaint.
# ---------------------------------------------------------------------------

BREAKAGES = [
    ('a missing required field',
     lambda t: t.replace('Impact: Enrollment projections moved from per-study '
                         'guesswork to a single reviewed model used at portfolio '
                         'planning.\n', '')),
    ('an off-registry axis value',
     lambda t: t.replace('Specialty: data-science', 'Specialty: astrology')),
    ('a dangling cross-reference',
     lambda t: t.replace('Recognizes: EX-001', 'Recognizes: EX-404')),
    ('a duplicate ID',
     lambda t: t.replace('ID: EX-002', 'ID: EX-001')),
    ('an entry in the wrong role group',
     lambda t: t.replace('ID: EX-001\nRole: RL-001', 'ID: EX-001\nRole: RL-002')),
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
]


def test_checker_catches_each_breakage():
    """Every deliberate defect must produce a complaint, not a pass."""
    root, cfg = _config.load()
    path = pu._inventory_path(root, cfg)
    pristine = _util.read(path)
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


def test_checker_catches_an_unrecorded_departure():
    """A PU entry removed by hand, without its migrated line, must be caught."""
    root, cfg = _config.load()
    path = pu._staging_path(root, cfg)
    text = _util.read(path)
    entry = next(e for e in pu.parse_staging(text) if e['id'] == 'PU-003')
    lines = text.split('\n')
    _util.write(path, '\n'.join(lines[:entry['start']] + lines[entry['end']:]))

    code, out = run('profile_update_qc.py', 'check', '--processed-pu', 'PU-003')
    assert code != 0, f'a PU entry vanished without a record and nothing complained:\n{out}'
    assert 'Migrated' in out, out


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
