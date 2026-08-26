# Test corpus

A complete, invented candidate that the scripts can run against instead of the
real profile. Nothing in `tests/fixture/` describes a real person, company,
journal, or job. The candidate is "Morgan Ellery"; every employer, school,
publication, and award is made up.

## Why it exists

Before this, the only way to test a change to the profile machinery was to run
it against the real profile in `personal/`, or to copy that profile out, run,
and copy it back. That put the candidate's own documents in the blast radius of
every test, and it meant situations the real profile does not contain went
untested until they hit him for real.

## Running the checks

```powershell
python tests\run_tests.py            # all of them
python tests\run_tests.py --only counter
```

Exit code is 0 when everything passes, 1 otherwise, so it can gate a change.

`run_tests.py` sets `CAREER_FIXTURE` itself, points it at a throwaway copy in
`tests/.run/`, and refuses to start unless the resolved profile path is inside
`tests/`. A check therefore cannot reach the real profile even by mistake, and
the committed corpus is identical before and after a run.

Every check corresponds to a defect that actually shipped, so the set is a
record of what has broken rather than a guess at what might. The docstring on
each one says what it caught.

Two of them are about the checkers themselves: they break the fixture
deliberately, nine different ways, and require a complaint each time. That
exists because the worst failure this repo has had was not a missing check but
a check written to tolerate two shapes, which stopped catching anything for four
months.

**A new check is only finished once you have seen it fail.** Reintroduce the bug,
watch the check go red, then restore. A check that has only ever passed proves
nothing.

## How to use the corpus directly

Set `CAREER_FIXTURE` to a repo-root-relative folder. Every path that lives under
the `personal` root is rebased onto it, so while the variable is set no script
can read or write the real profile.

```powershell
$env:CAREER_FIXTURE = 'tests/fixture'
python scripts\profile_update_qc.py check
python scripts\gap_qc.py check --folder <repo>\tests\fixture\applications\aldridge_APP-001_2026-01
Remove-Item Env:\CAREER_FIXTURE     # back to the real profile
```

A value naming a folder that does not exist raises rather than silently falling
back to the real profile.

Tests that write are expected to dirty the fixture. Reset it with
`git checkout tests/fixture`; the committed state is the canonical starting
point.

## What the corpus deliberately contains

Shapes chosen to exercise the machinery, not to look like a plausible career:

| Shape | Where |
|---|---|
| A role with entries, and a background role asserting `Entries: None` | `RL-001` / `RL-002` vs `RL-003` |
| Two entries per role group, ordered so sort correctness is visible | `EX-003`/`EX-004`, `EX-001`/`EX-002` |
| An entry omitting optional fields, and one carrying them | `EX-001` (no `Industry`) vs `EX-003` |
| A multi-line field | `ED-001` `Coursework` |
| A section split into sub-sections, one populated and one empty | Professional Training: `Completed` vs `In Progress` |
| Whole sections legitimately empty | Professional Affiliations, Presentations |
| A cross-reference that must resolve | `AW-001` `Recognizes: EX-001` |
| List lines in both label styles | Technical Experience (bold) vs Industry Exposure Profile (plain) |
| A category label containing a comma | `Programming, Data & Analytics` |
| A staging queue with entries waiting | `PU-003`, `PU-004` |
| Every migrated outcome | targets, multi-target, `dropped`, `duplicate` |
| Every requirement status in the taxonomy | `CR-001` through `CR-006` |
| A closure ref pointing at an already-migrated entry | `CR-002` to `PU-001` |
| A fit score and unmet-must-have count that must compute | 63.3%, 1 unmet |

## What it does not cover yet

No `retrieval.md`, `cv_content.md`, `interview_prep.md`, or `interview_notes.md`,
so the retrieval, CV, and interview-prep scripts have no fixture to run against.
Add them when those become the thing under change.

## Keeping it valid

The corpus has to stay consistent with `templates/inventory.md`, which is the
structure authority. When the template changes, run the checks against the
fixture; they will name what drifted.
