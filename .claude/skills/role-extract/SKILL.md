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
- **There is no `<scratch>/jd_split.md`:** go to Phase 0.
- **There is no `<scratch>/jd_assemble.md`:** go to Phase 3.
- **Otherwise:** tell the user the split is already assembled, then go to Phase 4 to re-check it.

## Phase 0 - Show the intro

- Run `python scripts/display/introduce.py role-extract` and show the output.

## Phase 1 - Split the job description into sentences (units)

- Run `python scripts/jd_sentences.py --folder <app_folder>`. It writes `<scratch>/jd_sentences.md`, the job description as numbered sentences. On a failure, stop and tell the user what is wrong with the job description.

## Phase 2 - Split the sentences into parts
- Run `python scripts/dispatch_prompt.py jd-splitter --folder <app_folder>` and dispatch `jd-splitter` with the prompt between `=== PROMPT ===` and `=== END ===` exactly as printed. The agent writes its table, each part with its Part ID, to `<scratch>/jd_split.md`; never write or edit that file yourself.

## Phase 3 - Assemble the split

- Run `python scripts/role_extract_assemble.py requirements --folder <app_folder> --requirements-file <scratch>/jd_split.md`. It joins the parts to `<scratch>/jd_sentences.md` and writes `<scratch>/jd_assemble.md` as an outline: one block per sentence with its line and section, and each part under its Part ID. Re-extracting replaces any earlier kinds and ranking.

## Phase 4 - Check the split against the job description

- Run `python scripts/role_extract_qc.py requirements --folder <app_folder>`.
- On a failure, tell the user which requirement does not match the job description and redo Phase 2. Do not label or rank until it passes.


