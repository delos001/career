---
name: role-extract
description: Extract the job's requirements from the job description, label each by kind, and group and rank them into the job's needs. Reads the jd.md that role-intake wrote and the research.md that role-research wrote, and writes jd_needs.md, which role-classify, retrieval, gap analysis, CV creation and interview prep read. Run after role-research; role-classify runs next.
---

# role-extract - extract the requirements and rank the needs

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Start each phase by saying "The next step is to" followed by the phase title after the dash, in lower case.

## Start

Ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`; use it as `<app_folder>`. Then check the folder against the cases below, in order, and follow the first one that is true:

- **There is no folder or no session log:** role-intake has not finished for this APP-NNN. Tell the user role intake must be completed first and stop.
- **There is no `research.md`:** tell the user role research must be completed first and stop.
- **There is no `jd_needs.md`:** go to Phase 0.
- **`jd_needs.md` has no `## Needs` section:** go to Phase 2.
- **Otherwise:** tell the user the needs are already ranked, then go to Phase 4 to re-check them.

## Phase 0 - Show the intro

- Run `python scripts/display/introduce.py role-extract` and show the output.

## Phase 1 - Extract the requirements

- Run `python scripts/dispatch_prompt.py critical-requirements-extractor --folder <app_folder>` and dispatch `critical-requirements-extractor` with the prompt between `=== PROMPT ===` and `=== END ===` exactly as printed.
- Save its output to `<scratch>/requirements.md`, then run `python scripts/role_extract_assemble.py requirements --folder <app_folder> --requirements-file <scratch>/requirements.md`. Re-extracting replaces any earlier ranking.

## Phase 2 - Check the extraction against the job description

- Run `python scripts/role_extract_qc.py requirements --folder <app_folder>`.
- On a failure, tell the user which requirement does not match the job description and redo Phase 1. Do not rank until it passes.

## Phase 3 - Rank the needs

- Run `python scripts/dispatch_prompt.py jd-needs-ranker --folder <app_folder>` and dispatch `jd-needs-ranker` with the printed prompt exactly as printed.
- Save its output to `<scratch>/needs.md`, then run `python scripts/role_extract_assemble.py needs --folder <app_folder> --needs-file <scratch>/needs.md`.

## Phase 4 - Check the requirements and the ranking

- **Step 4a:** run `python scripts/role_extract_qc.py check --folder <app_folder>`.
- **Step 4b:** after 4a passes, run `python scripts/dispatch_prompt.py qc-role-extract --folder <app_folder>` and dispatch `qc-role-extract` with the printed prompt exactly as printed.
- On a failure or finding, tell the user what is wrong, fix it per *Routing on failure*, and re-run from Step 4a. Before any fix that changes wording or substance, show the before/after.
- Stop after 3 rounds and carry anything left to Phase 5.

## Phase 5 - Get approval and hand off to role-classify

- Present each finding QC left open as its own decision, one per response: what is wrong, the recommended fix, the before/after text.
- A wrong ranking steers every later skill, so the user confirms it section by section. Show `jd_needs.md` one section at a time, its text exactly as written: the job, then each need with its requirements and kinds, then Qualifications, then Not ranked (retrieval and gap analysis never see those). The user confirms, or reorders, regroups, relabels or changes a kind. Apply a change as a direct edit to `jd_needs.md` (ids renumbered to rank order), show it as before/after, re-run Step 4a, and show the changed section again until confirmed.
- Once every section is confirmed, tell the user to run `/role-classify`. If role-classify has already run for this application, tell the user to run it again, since it reads the job section.

## Routing on failure

| Finding | Fix |
|---|---|
| A requirement wrong, missing, or reworded from the job description | Phase 1 (the ranking is redone from Phase 3) |
| A kind wrong, or the ranking misreads the job description | Phase 3, or a direct edit when the user changes it in Phase 5 |
| Company or role research wrong | Stop; the user reruns `/role-research`, then this skill from Phase 3 |
