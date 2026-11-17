---
name: role-classify
description: Classify the job against the five axes (orientation, industry, specialty, level, work-state). Reads the jd.md that role-intake wrote, the research.md that role-research wrote and the jd_needs.md that role-extract wrote, and writes the classification into the session log for retrieval, gap analysis, CV creation and interview prep. Run after role-extract; retrieval runs next.
---

# role-classify - classify the job

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Start each phase by saying "The next step is to" followed by the phase title after the dash, in lower case.

## Resume check - run before Phase 0

Ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`; use it as `<app_folder>`. Then check the folder against the cases below, in order, and follow the first one that is true:

- **There is no folder or no session log:** role-intake has not finished for this APP-NNN. Tell the user role intake must be completed first and stop.
- **There is no `research.md`:** tell the user role research must be completed first and stop.
- **There is no `jd_needs.md`, or it has no `## Needs` section:** tell the user role extraction must be completed first and stop.
- **`## Axis Classification` in the session log is still `_(pending)_`:** go to Phase 0.
- **Otherwise:** tell the user the job is already classified, then go to Phase 2 to re-check it.

## Phase 0 - Show the intro

- Run `python scripts/display/introduce.py role-classify` and show the output.

## Phase 1 - Classify the job against the five axes

- Run `python scripts/dispatch_prompt.py axis-classifier --folder <app_folder>` and dispatch `axis-classifier` with the prompt between `=== PROMPT ===` and `=== END ===` exactly as printed. It classifies all five axes from scratch and is the authority on each.
- Every axis needs a confirmed value whose rule file exists, or a `Registry-only` value. If the classifier flags an axis gap, stop, explain each gap, and resolve it before going on:
  - **Value confirmed, file `File deferred`:** run the matching builder skill (`orientation-builder`, `industry-builder`, `specialty-builder`, `level-builder` or `work-state-builder`), then rerun this phase.
  - **No registry value confirms:** show the closest registry values. The user maps the role to one (rerun the classifier with that steer) or runs the builder to add a value, then this phase reruns.
  - A gap is never carried past this phase.
- Once every axis resolves, save the output to `<scratch>/axes.md` and run `python scripts/role_classify_assemble.py finalize --folder <app_folder> --axis-file <scratch>/axes.md`.

## Phase 2 - Check the classification

- **Step 2a:** run `python scripts/role_classify_qc.py check --folder <app_folder>`.
- **Step 2b:** after 2a passes, run `python scripts/dispatch_prompt.py qc-role-classify --folder <app_folder>` and dispatch `qc-role-classify` with the printed prompt exactly as printed.
- On a failure or finding, tell the user what is wrong, fix it per *Routing on failure*, and re-run from Step 2a. Before any fix that changes wording or substance, show the before/after.
- Stop after 3 rounds and carry anything left to Phase 3.

## Phase 3 - Get approval and hand off to retrieval

- Present each finding QC left open as its own decision, one per response: what is wrong, the recommended fix, the before/after text.
- Run `python scripts/role_classify_assemble.py approval --folder <app_folder>` and show its output. On a correction, fix it per *Routing on failure* and re-run Phase 2.
- On approval, tell the user to run `/retrieval`.

## Routing on failure

| Finding | Fix |
|---|---|
| Classification wrong, or an axis gap got past Phase 1 | Phase 1 |
| Requirements or ranked needs wrong | Stop; the user reruns `/role-extract`, then this skill from Phase 1 |
| Company, role or industry research wrong | Stop; the user reruns `/role-research`, then this skill from Phase 1 |
