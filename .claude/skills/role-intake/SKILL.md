---
name: role-intake
description: Understand a job opportunity - ingest a job description, research the company/role/industry, classify the job against the five axes, and produce a session log plus a research file for downstream gap analysis. Run this first when evaluating a new role.
---

# role-intake - understand the job

Builds the foundational understanding of a job opportunity. It produces two
artifacts a later gap-analysis skill consumes: a **session log** and a **research
file**. It does not write a CV or a gap analysis.

## Operating rules

- **Global rules.** Read `rules/global-rules.md` at the start and operate under it
  for the whole run.
- **Separable phases.** Each phase below has a defined input and output. Run them
  in order. A phase consumes only its declared input and produces only its
  declared output.
- **One non-linear loop.** Phase 8 (QC) may route back to an earlier phase; see
  *QC failure routing* at the end.

## Resume check - run before Phase 1

Ask the user: new role, or resuming an interrupted one?
- **Resuming:** ask which (APP-NNN or folder name). Confirm
  `personal/applications/<folder>/research.md` exists. If it does, read the
  existing session log and `research.md`, then jump to **Phase 6**. If it does
  not, the run was interrupted before the resume checkpoint - start at Phase 1.
- **New:** proceed to Phase 0.

## Phase 0 - Intro

- Input: invocation.
- Run `python scripts/display/introduce.py role-intake` and show the output.
- Output: user oriented; ready to proceed.

## Phase 1 - JD + comms ingestion

- Input: paste text, or a source path/URL.
- If the JD is a file path or URL, run `python scripts/ingest/jd_extract.py
  <source>` and capture stdout as the JD text. If the script exits non-zero, halt
  per global rules.
- Ask the user whether there are any role communications (e.g. a recruiter
  email). If yes: if the JD is a file, ask them to place the comms in the same
  folder and ingest each via `jd_extract.py`; if the JD was pasted, accept pasted
  comms or a path.
- Output: JD text + any supplementary comms text.

## Phase 2 - Metadata extraction

- Input: JD text + comms.
- Extract the role title, company, and role level (if stated).
- If title or company is absent, prompt the user for it (ambiguous input - ask).
- Output: `{title, company, role-level?}`.

## Phase 3 - Session init

- Input: company, role.
- Run `python scripts/app_id.py` to get the next APP-NNN.
- Ask the user for a short company slug for filenames (e.g. `PFM` for Precision
  for Medicine). Determine the current `YYYY-MM`.
- Run `python scripts/assemble.py init` with the slug, APP-NNN, year-month,
  company, role, role level (if known), and session start date. It creates the
  application folder, writes the initial session log per
  `templates/session_log.md`, and prints both paths.
- Output: APP-NNN, application folder path, session log path.

## Phase 4 - Research

- Input: JD text, company, role, candidate industry (inferred from JD + company).
- Dispatch three subagents **in parallel**: `company_research`, `role_research`,
  `industry_research`. Give each the JD text, company, role, and (for
  `industry_research`) the candidate industry.
- Each returns a fixed block (`## Company` / `## Role` / `## Industry`, with
  Summary / Key facts / Sources). Research is scoped to what this skill needs to
  classify and characterize the job - not exhaustive dossiers.
- Output: three structured findings blocks.

## Phase 5 - Research file assembly

- Input: three findings blocks.
- Write each research subagent's output block to its own temp file, then run
  `python scripts/assemble.py research` with the application folder, APP-NNN,
  company, role, date, and the three temp file paths. It writes `research.md` per
  `templates/research_file.md` (on a re-run it section-replaces only role-intake's
  own sections, so nothing else is clobbered).
- Output: `research.md` written. **This is the resume checkpoint.**

## Phase 6 - Axis classification

- Input: JD text, research findings.
- Dispatch the `axis_classifier` subagent with the JD text and the research
  findings. It works registry-first for every axis - reads each axis registry,
  picks candidate value(s), reads only the candidate value files, and confirms
  each pick against the value file before recording it. Where no registry value
  confirms, it flags an axis gap (not blocked, not routed to a builder skill).
- Output: per-axis primary/secondary values + a list of axis gaps.

## Phase 7 - Session log finalization

- Input: session log path, `axis_classifier` output, research-completed date.
- Write the `axis_classifier` output to a temp file, then run
  `python scripts/assemble.py finalize` with the session log path, the
  research-completed date, and that temp file. It fills the research-completed
  date and replaces the pending axis sections.
- Output: session log complete.

## Phase 8 - QC

- Input: session log path, research file path, a brief activity record (which
  phases ran).
- Dispatch the `qc_role_intake` subagent with those inputs.
- **This phase is a loop.** If the verdict is **FINDINGS**: present them to the
  user per global rules, route back to the phase each finding names, re-run
  forward from there - and return to Phase 8 to QC the changes. Repeat until the
  verdict is **PASS**.
- The skill leaves Phase 8 only on a **PASS**. No artifact is changed after the
  passing QC - Phase 9 makes no edits - so every change is itself QC'd.
- Output: PASS verdict.

## Phase 9 - Handoff

- State completion. The session log and research file are ready for the
  gap-analysis skill.

## QC failure routing

Each QC finding names the phase that owns the deficiency. Route back, fix, and
re-run forward - **including Phase 8 again**, so the changes are themselves QC'd.
The skill leaves Phase 8 only on a PASS.

| Finding type | Route back to |
|---|---|
| Company/role metadata wrong | Phase 2 |
| Research file incomplete/insufficient | Phase 4 (re-research) then 5 |
| Axis classification wrong, or gap not recorded in both files | Phase 6 |
| Session log field missing | Phase 7 |
