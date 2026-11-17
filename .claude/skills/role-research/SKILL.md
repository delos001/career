---
name: role-research
description: Research the industry, company, and the role title for an application that role-intake started, and write the research file. Run after role-intake; role-extract runs next.
---

# role-research - research the company, role and industry

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Start each phase by saying "The next step is to" followed by the phase title after the dash, in lower case.

## Start

Ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`; use it as `<app_folder>`. Then check the folder against the cases below, in order, and follow the first one that is true:

- **There is no folder or no session log:** role-intake has not finished for this APP-NNN. Tell the user role intake must be completed first and stop.
- **`research.md` already exists:** tell the user the research is already written, then go to Phase 3 to re-check it.
- **Otherwise:** go to Phase 0.

## Phase 0 - Show the intro

- Run `python scripts/display/introduce.py role-research` and show the output.

## Phase 1 - Research the company, role and industry

- Dispatch `company-research`, `title-research` and `industry-research` in parallel. For each, run `python scripts/dispatch_prompt.py <agent> --folder <app_folder>` and send the prompt between `=== PROMPT ===` and `=== END ===` exactly as printed. Each agent writes its block to the output file the prompt names; never write or edit those files yourself.

## Phase 2 - Write the research file

- Run `python scripts/role_research_assemble.py research --folder <app_folder> --date <today> --company-file <scratch>/research_company.md --role-file <scratch>/research_role.md --industry-file <scratch>/research_industry.md`.

## Phase 3 - Check the research file

- **Step 3a:** run `python scripts/role_research_qc.py check --folder <app_folder>`.
- **Step 3b:** after 3a passes, run `python scripts/dispatch_prompt.py qc-role-research --folder <app_folder>` and dispatch `qc-role-research` with the printed prompt exactly as printed.
- On a failure or finding, tell the user what is wrong, fix it per *Routing on failure*, and re-run from Step 3a.
- Stop after 3 rounds and carry anything left to Phase 4.

## Phase 4 - Get approval and hand off to role-extract

- Present each finding QC left open as its own decision, one per response: what is wrong, the recommended fix, the before/after text.
- Give the user the `research.md` path and ask for corrections or "approved". On a correction, fix it per *Routing on failure* and re-run Phase 3.
- On approval, tell the user to run `/role-extract`.

## Routing on failure

| Finding | Fix |
|---|---|
| A section missing or substantially wrong | Phase 1, then Phase 2 |
| One claim, hedge or source wrong | Edit that passage in `research.md` directly, showing the before/after first |
| Session log check fails | If the research date is still pending, re-run Phase 2. Otherwise stop and tell the user role-intake's files changed after its check. |
| Title or company wrong | Run `python scripts/assemble.py relabel --folder <app_folder>` with `--role` and/or `--company` (and `--slug` if it asks for one); the path it prints is `<app_folder>` from then on. Then Phase 1. |
