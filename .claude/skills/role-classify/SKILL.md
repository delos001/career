---
name: role-classify
description: Rank what the job description says matters most, and classify the job against the five axes (orientation, industry, specialty, level, work-state). Reads the jd.md and research.md that role-intake wrote and writes the ranked needs and the classification into the application's files for retrieval, gap analysis, CV creation and interview prep. Run after role-intake; it works from files, so a fresh session is fine.
---

# role-classify - rank the needs and classify the job

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Each phase opens with the **bold lead line** under its heading; speak it verbatim.
- Talk to the user in plain English: no check IDs, route-back labels, or words like subagent or JSON.
- Working files go in `<scratch>`, which is `<app_folder>/scratch/`.

## Start

Ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`. Land on the first match:

1. Folder missing: the APP-NNN is likely wrong; ask again.
2. `research.md` missing, or its `## Critical Requirements` table empty: halt and tell the user to finish `/role-intake` first.
3. `## Ranked Needs` in `research.md` still `_(pending)_`: run `python scripts/display/introduce.py role-classify`, show the output, then go to Phase 1.
4. `## Axis Classification` in the session log still `_(pending)_`: Phase 2.
5. Otherwise: Phase 3.

Say "Starting APP-NNN at Phase N." and proceed.

## Phase 1 - Rank the needs

**Ranking what the job description says matters most.**

- Run `python scripts/dispatch_prompt.py jd-needs-ranker --folder <app_folder>` and dispatch `jd-needs-ranker` with the printed prompt exactly as printed.
- Save its output to a file in `<scratch>`, then run `python scripts/role_classify_assemble.py needs --folder <app_folder> --needs-file <path>`.

## Phase 2 - Classify the axes

**Classifying the role against the five axes.**

- Run `python scripts/dispatch_prompt.py axis-classifier --folder <app_folder>` and dispatch `axis-classifier` with the printed prompt exactly as printed. It classifies all five axes from scratch and is the authority on each.
- **Gate.** Every axis needs a confirmed value whose rule file exists, or a `Registry-only` value. If the classifier flags an axis gap, stop, explain each gap in plain English, and resolve it before going on:
  - **Value confirmed, file `File deferred`:** run the matching builder skill (`orientation-builder`, `industry-builder`, `specialty-builder`, `level-builder` or `work-state-builder`), then rerun this phase.
  - **No registry value confirms:** show the closest registry values. The user maps the role to one (rerun the classifier with that steer) or runs the builder to add a value, then this phase reruns.
  - A gap is never carried past this gate.
- Once every axis resolves, save the output to a file in `<scratch>` and run `python scripts/role_classify_assemble.py finalize --folder <app_folder> --axis-file <path>`. It writes the classification, the Level and Industry lines, and the Axis Gaps.

## Phase 3 - QC

**Checking the ranking and the classification.**

- **3a.** Run `python scripts/role_classify_qc.py check --folder <app_folder>`. On a failure, tell the user what is wrong in plain English, fix it per *Routing on failure*, and rerun 3a.
- **3b.** After 3a passes, run `python scripts/dispatch_prompt.py qc-role-classify --folder <app_folder>` and dispatch `qc-role-classify` with the printed prompt exactly as printed. On findings, tell the user in plain English, fix per *Routing on failure*, and rerun from 3a.
- Before any fix that changes wording or substance, show a before/after table.
- At most 3 rounds. Findings still open after round 3 go to Phase 4.

## Phase 4 - Your review

**Reviewing the ranking and the classification with you.**

- **4a. Open findings.** One per message: what is wrong, the recommended fix, and the before/after. Act on the user's decision before showing the next.
- **4b. Confirm the ranking.** Its own decision, because a wrong ranking steers every later skill. Show the needs in rank order in plain English: the label, which requirements it groups, why it ranks there, and whether the JD stated it or it was derived. The user confirms, or reorders, regroups or relabels. Apply a change as a direct edit to `research.md` (ids renumbered to rank order), show it as before/after, rerun 3a, and show the ranking again until confirmed.
- **4c. Approval.** Run `python scripts/role_classify_assemble.py approval --folder <app_folder>` and show its output. On a correction, fix per *Routing on failure*, rerun Phase 3, and return here. On approval, tell the user the application is ready for `/retrieval`.

## Routing on failure

| Problem | Go back to |
|---|---|
| Ranking fails its checks or misreads the JD | Phase 1, or a direct edit when the user reorders at 4b |
| Classification wrong, or an axis gap got past Phase 2 | Phase 2 |
| Research or requirements wrong | Halt; rerun `/role-intake` from its research phase, then this skill from Phase 1 |
