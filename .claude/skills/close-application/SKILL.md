---
name: close-application
description: Close out an evaluated job application - record the final outcome and its date in the session log, then wipe the application's run-scratch folder. Run when an application reaches a terminal state (offer accepted or declined, rejected, withdrawn, no response, or not pursued).
---

# close-application - close out an application

Closes a single application: records the final outcome and its date in the
session log, then removes the application's run-scratch in one shot. This is one
of the two scratch-cleanup triggers (the other is the gap-analysis "not
pursuing" path).

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Plain English to the user. Halt and ask on any failure rather than guessing.

## Phase 1 - Identify the application

**Identifying the application to close.**

- Input: an APP-NNN (from the invocation, or ask for it).
- Locate the application folder under `personal/applications/` and the session
  log at `personal/sessions/<SLUG>_APP-NNN_YYYY-MM_SessionLog.md`.
- If the folder or the session log is missing, halt and report (the APP-NNN is
  likely wrong); ask for it again.
- Output: application folder path, session log path, slug, ym.

## Phase 2 - Capture the outcome

**Capturing the outcome and its date.**

- Ask the user for the outcome and the date it occurred.
- Outcome vocabulary (the user picks one, or supplies their own): `offer-accepted`,
  `offer-declined`, `rejected`, `withdrawn`, `no-response`, `not-pursued`.
- Outcome date: ask; default to today only if the user declines to specify.
- Output: outcome value, outcome date.

## Phase 3 - Record the outcome

**Recording the outcome in the session log.**

- Write a `## Closed` section body to a scratch file
  (`<app_folder>/scratch/closed_section.md`) carrying: Outcome, Outcome date,
  Closed-out date (today).
- Run `python scripts/session_log.py append-section --slug <slug> --app-id
  APP-NNN --ym YYYY-MM --heading Closed --body-file <path>`. The script replaces
  the section on re-runs and appends it on first runs.
- Output: session log `## Closed` section written.

## Phase 4 - Wipe scratch

**Removing the application's run-scratch.**

- Run `python scripts/scratch_cleanup.py --app-folder <app_folder> --apply`.
- Report what was removed (file count and size, or "nothing to clean" if the
  scratch folder was already gone).
- State completion: the application is closed and its run-scratch is cleared.
- Output: scratch removed.
