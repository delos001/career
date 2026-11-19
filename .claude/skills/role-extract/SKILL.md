---
name: role-extract
description: Extract the job's requirements from the job description. Requirements are labeled by what they are asking for, and grouped and ranked. Reads jd.md and research.md. Writes jd_needs.md, which is used by role-classify, retrieval, gap analysis, CV creation and interview prep. Run after role-research; role-classify runs next.
---

# role-extract - extract the requirements and rank the needs

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Start each phase by saying "The next step is to" followed by the phase title after the dash, in lower case.

## Resume check - run before Phase 0

Ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`; use it as `<app_folder>`. Then check the folder against the cases below, in order, and follow the first one that is true:

- **There is no folder or no session log:** role-intake has not finished for this APP-NNN. Tell the user role intake must be completed first and stop.
- **There is no `research.md`, or `Research Completed Date` in the session log is still pending:** tell the user role research must be completed and approved first and stop.
- **There is no `jd_needs.md`:** go to Phase 0.
- **`jd_needs.md` rows have no Kind:** go to Phase 2.
- **`jd_needs.md` has no `## Needs` section:** go to Phase 4.
- **Otherwise:** tell the user the needs are already ranked, then go to Phase 5 to re-check them.

## Phase 0 - Show the intro

- Run `python scripts/display/introduce.py role-extract` and show the output.

## Phase 1 - Extract the requirements

- Run `python scripts/jd_sentences.py --folder <app_folder>`. It writes `<scratch>/jd_sentences.md`, the job description as numbered sentences with hints. On a failure, stop and tell the user what is wrong with the job description.
- Run `python scripts/dispatch_prompt.py jd-splitter --folder <app_folder>` and dispatch `jd-splitter` with the prompt between `=== PROMPT ===` and `=== END ===` exactly as printed. The agent writes its table to `<scratch>/requirements.md`; never write or edit that file yourself.
- Run `python scripts/role_extract_assemble.py requirements --folder <app_folder> --requirements-file <scratch>/requirements.md`. It writes `jd_needs.md`, one row per part, and sets each row's Demand and Bar. Re-extracting replaces any earlier kinds and ranking.

## Phase 2 - Check the extraction against the job description

- Run `python scripts/role_extract_qc.py requirements --folder <app_folder>`.
- On a failure, tell the user which requirement does not match the job description and redo Phase 1. Do not label or rank until it passes.

## Phase 3 - Label each row's kind

- Run `python scripts/dispatch_prompt.py jd-kind-labeler --folder <app_folder>` and dispatch `jd-kind-labeler` with the printed prompt exactly as printed. The agent writes its result to `<scratch>/kinds.md`; never write or edit that file yourself.
- Run `python scripts/role_extract_assemble.py kinds --folder <app_folder> --kinds-file <scratch>/kinds.md`. It writes each row's Kind into `jd_needs.md`.

## Phase 4 - Rank the needs

- Run `python scripts/dispatch_prompt.py jd-needs-ranker --folder <app_folder>` and dispatch `jd-needs-ranker` with the printed prompt exactly as printed. The agent writes its result to `<scratch>/needs.md`; never write or edit that file yourself.
- Run `python scripts/role_extract_assemble.py needs --folder <app_folder> --needs-file <scratch>/needs.md`.

## Phase 5 - Check the requirements and the ranking

- **Step 5a:** run `python scripts/role_extract_qc.py check --folder <app_folder>`.
- **Step 5b:** after 5a passes, run `python scripts/dispatch_prompt.py qc-role-extract --folder <app_folder>` and dispatch `qc-role-extract` with the printed prompt exactly as printed.
- On a failure or finding, tell the user what is wrong, fix it per *Routing on failure*, and re-run from Step 5a. Before any fix that changes wording or substance, show the before/after.
- Stop after 3 rounds and carry anything left to Phase 6.

## Phase 6 - Get approval and hand off to role-classify

- Present each finding QC left open as its own decision, one per response: what is wrong, the recommended fix, the before/after text.
- A wrong ranking steers every later skill, so the user confirms it section by section. Show `jd_needs.md` one section at a time, its text exactly as written: the job, then each need with its requirements and kinds, then Qualifications, then Not ranked (retrieval and gap analysis never see those). Tell the user that what each Kind, Demand and Bar value means is in the `## Definitions` appendix at the end of `jd_needs.md`. The user confirms, or reorders, regroups, relabels or changes a kind. Apply a change as a direct edit to `jd_needs.md` (ids renumbered to rank order), show it as before/after, re-run Step 5a, and show the changed section again until confirmed.
- Once every section is confirmed, tell the user to run `/role-classify`. If role-classify has already run for this application, tell the user to run it again, since it reads the job section.

## Routing on failure

| Finding | Fix |
|---|---|
| A requirement wrong, missing, or reworded from the job description | Phase 1 (kinds and ranking are redone from Phase 3) |
| A kind wrong | Phase 3 (the ranking is redone from Phase 4), or a direct edit when the user changes it in Phase 6 |
| The ranking misreads the job description | Phase 4, or a direct edit when the user changes it in Phase 6 |
| Company or role research wrong | Stop; the user reruns `/role-research`, then this skill from Phase 3 |
