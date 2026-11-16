---
name: role-research
description: Research the company, the role and the industry for an application that role-intake started, and write the research file. Run after role-intake; role-classify runs next. Works from the application folder, so a fresh session is fine.
---

# role-research - research the company, role and industry

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Each phase opens with the **bold lead line** under its heading - speak it verbatim before running the phase.

## Start

Ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`; use it as `<app_folder>`.

- **No folder, or no session log:** role-intake has not finished for this APP-NNN. Say so and stop.
- **`research.md` exists:** tell the user the research is already written, then go to Phase 3 to re-check it.
- **Otherwise:** go to Phase 0.

## Phase 0 - Intro

**Introducing the role-research skill.**

- Run `python scripts/display/introduce.py role-research` and show the output.

## Phase 1 - Research

**Researching the company, role, and industry in parallel.**

- Dispatch `company-research`, `title-research` and `industry-research` in parallel. For each, run `python scripts/dispatch_prompt.py <agent> --folder <app_folder>` and send the prompt between `=== PROMPT ===` and `=== END ===` exactly as printed.
- Write each returned block, unchanged, to its own file in `<scratch>`.

## Phase 2 - Write the research file

**Writing the research file.**

- Run `python scripts/role_research_assemble.py research --folder <app_folder> --date <today> --company-file <file> --role-file <file> --industry-file <file>`.

## Phase 3 - QC

**Checking the research file.**

- **Step 3a:** run `python scripts/role_research_qc.py check --folder <app_folder>`.
- **Step 3b:** after 3a passes, run `python scripts/dispatch_prompt.py qc-role-research --folder <app_folder>` and dispatch `qc-role-research` with the printed prompt exactly as printed.
- On a failure or finding, tell the user what is wrong, fix it per *Routing on failure*, and re-run from Step 3a. Show any change to the research file's wording as a before/after table first.
- Stop after 3 rounds and carry anything left to Phase 4.

## Phase 4 - Approval and handoff

**Reviewing the research with you and handing off to role-classify.**

- Present each finding QC left open as its own decision, one per response: what is wrong, the recommended fix, the before/after text.
- Give the user the `research.md` path and ask for corrections or "approved". On a correction, fix it per *Routing on failure* and re-run Phase 3.
- On approval, tell the user to run `/role-classify`.

## Routing on failure

| Finding | Fix |
|---|---|
| Research incomplete or wrong | Phase 1, then Phase 2 |
| Title or company wrong | Run `python scripts/assemble.py relabel --folder <app_folder>` with `--role` and/or `--company` (and `--slug` if it asks for one); the path it prints is `<app_folder>` from then on. Then Phase 1. |
