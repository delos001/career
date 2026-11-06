---
name: close-application
description: Close out an evaluated job application - record the final outcome and its date in the session log, then wipe the application's run-scratch folder. Run when an application reaches a terminal state (offer accepted or declined, rejected, withdrawn, no response, not pursued, or role unavailable).
---

# close-application - close out an application

Closes a single application: records the final outcome and its date in the session log, then removes the application's run-scratch in one shot. This is one of the two scratch-cleanup triggers (the other is the gap-analysis "not pursuing" path).

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Plain English to the user. Halt and ask on any failure rather than guessing.

## Phase 1 - Identify the application

**Identifying the application to close.**

- Input: an APP-NNN (from the invocation, or ask for it).
- Locate the application folder with `python scripts/paths.py app <APP-NNN>`; the session log is `session_log.md` inside that folder.
- If the folder or the session log is missing, halt and report (the APP-NNN is likely wrong); ask for it again.
- Output: application folder path, session log path.

## Phase 2 - Capture the outcome

**Capturing the outcome and its date.**

- Ask the user for the outcome and the date it occurred.
- Outcome vocabulary (the user picks one, or supplies their own): `offer-accepted`, `offer-declined`, `rejected`, `withdrawn`, `no-response`, `not-pursued`, `unavailable` (the role became unavailable without a decision on the candidate: filled before or during the application, or the requisition pulled).
- Outcome date: ask; default to today only if the user declines to specify.
- Output: outcome value, outcome date.

## Phase 2b - Reconcile the interview record

The session log is the one home for each round's scheduling metadata, and a cancelled or rescheduled round may never have reached a skill that recorded it. Close-out is the last chance to make the record true. This is a backstop, not the capture mechanism: an accurate record depends on the lifecycle op or the follow-up skill having run at the time.

Do not ask an open "is everything accurate?" question; the user will not remember. Read `interview_notes.md` and each `## Interview: <stage>` section, then surface only what is provably unresolved, one item per turn:

- A round whose `Outcome:` still reads `pending`. Ask what happened.
- A round whose `Interview date:` is in the future, or whose `Status:` is still `scheduled` or `unscheduled`. It never happened; ask whether it was cancelled or moved, or for an `unscheduled` round, whether it was ever booked.
- A round tagged `[CANCELLED ...]` in `interview_notes.md` whose session-log `Status:` does not say cancelled. Propose the correction (`Status: cancelled
  <YYYY-MM-DD>`, `Outcome: n/a (round cancelled)`).
- A round whose notes `- Schedule changes:` line disagrees with the session-log `Schedule history:` / `Interview date:` fields. Show both, confirm, write.

Apply confirmed corrections with `python scripts/session_log.py interview --folder <app_folder> --stage "<stage>" --set "<Label>=<value>"`, passing only the fields being corrected; the script leaves every other field as it is. Value formats are in `templates/session_log.md` `## Interview field notes`.

If nothing is unresolved, say so in one line and move on.

## Phase 3 - Record the outcome

**Recording the outcome in the session log.**

- Write a `## Closed` section body to a scratch file (`<app_folder>/scratch/closed_section.md`) carrying: Outcome, Outcome date, Closed-out date (today).
- Run `python scripts/session_log.py append-section --folder <app_folder> --heading Closed --body-file <path>`. The script replaces the section on re-runs and appends it on first runs.
- Output: session log `## Closed` section written.

## Phase 4 - Wipe scratch

**Removing the application's run-scratch.**

- Run `python scripts/scratch_cleanup.py --app-folder <app_folder> --apply`.
- Report what was removed (file count and size, or "nothing to clean" if the scratch folder was already gone).
- State completion: the application is closed and its run-scratch is cleared.
- Output: scratch removed.
