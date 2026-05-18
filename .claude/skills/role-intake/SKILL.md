---
name: role-intake
description: Understand a job opportunity - ingest a job description, research the company/role/industry, classify the job against the five axes, and produce a session log plus a research file for downstream gap analysis. Run this first when evaluating a new role.
---

# role-intake - understand the job

Builds the foundational understanding of a job opportunity. It produces two
artifacts that later skills will consume: a **session log** and a **research
file**.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases below run in order; each has a declared input and output.
- Each phase opens with the **bold lead line** under its heading - speak it
  verbatim before running the phase.
- Phase 8 (QC) and Phase 9 (approval) loop back per *Phase routing on failure*.

## Resume check - run before Phase 0

Ask if this session is for a new role or to resume a previous one?

- **New:** proceed to Phase 0.
- **Resume:** ask the APP-NNN; locate the matching folder under
  `personal/applications/`. Probe and land per the ladder (first match wins):
  1. Folder missing - halt; APP-NNN likely wrong.  Ask for APP-NNN again.
  2. `research.md` missing - resume at start of **Phase 4**.
  3. Axis classification still `_(pending)_` in the session log - resume at start of **Phase 6**.
  4. All filled - resume at start of**Phase 8** (re-QC).

  Announce ("Resuming APP-NNN at Phase N.") and proceed without prompting.

## Phase 0 - Intro (new runs only)

**Introducing the role-intake skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py role-intake` and show the output.
- Output: user oriented.

## Phase 1 - JD + comms ingestion

**Ingesting the Job Description and any role communications.**

- Input: paste text, or a source path/URL for the JD.
- For a file path or URL, run `python scripts/ingest/jd_extract.py <source>`;
  capture stdout. Non-zero exit = halt per global rules.
- Ask the user about role communications (e.g. recruiter email). Ingest via
  `jd_extract.py` if file/URL; accept pasted text otherwise.
- Output: JD text + source; comms text + source if any. ("Source" = URL,
  original file path, or `"pasted"`.)

## Phase 2 - Metadata extraction + confirmation

**Extracting role title, company, level, and industry from the JD.**

- Input: JD text + comms.
- Infer title, company, level, industry. Infer level (it may appear in the
  title, body, or be implicit from scope) rather than leaving blank.
- Prompt the user for any value that cannot be inferred.
- Present for explicit confirmation:

  ```
  Confirm role metadata:
    Title:    <value>
    Company:  <value>
    Level:    <value>
    Industry: <value>
  Reply with corrections or "confirmed".
  ```

- Re-present on corrections until confirmed.
- Output: user-confirmed {title, company, role-level, industry}.

## Phase 3 - Session init

**Creating the application folder and starting the session log.**

- Input: title, company, level, industry; JD text + source; comms text + source
  (if any).
- Run `python scripts/app_id.py` for the next APP-NNN. Ask the user for a short
  company slug. Determine the current `YYYY-MM`.
- Write JD (and comms if present) to temp files.
- Run `python scripts/assemble.py init` with the slug, APP-NNN, YM, metadata
  (company, role, level, industry), start date, JD temp-file + source, and (if
  comms) comms temp-file + source. It creates the folder, writes `jd.md` and
  optionally `comms.md`, writes the initial session log, and prints all paths.
- Output: paths printed by `assemble.py`.

## Phase 4 - Research

**Researching the company, role, and industry in parallel.**

- Input: JD text, company, role, role industry (per Phase 2 confirmation).
- Dispatch three subagents **in parallel** - `company-research`,
  `role-research`, `industry-research` - giving each the JD text, company, role,
  and (for `industry-research`) the role industry.
- Each returns a fixed block (`## Company` / `## Role` / `## Industry`, with
  Summary / Key facts / Sources). Scoped to what this skill needs to classify
  and characterize - not exhaustive dossiers.
- Output: three structured findings blocks.

## Phase 5 - Research file assembly

**Assembling the research findings into the research file.**

- Input: three findings blocks.
- Write each block to its own temp file, then run `python scripts/assemble.py
  research` with the application folder, APP-NNN, company, role, date, and the
  three temp-file paths. It section-replaces only role-intake's own sections so
  nothing else is clobbered.
- Output: `research.md` written.

## Phase 6 - Axis classification

**Classifying the role against the five axes.**

- Input: JD text, research findings.
- Dispatch `axis-classifier` with the JD text and the research findings. It
  works registry-first per axis: read the registry, pick candidate value(s),
  read only the candidate value files, confirm each pick. Where no registry
  value confirms, flag an axis gap (not blocked, not routed to a builder).
- Output: per-axis primary/secondary + a list of axis gaps.

## Phase 7 - Session log finalization

**Finalizing the session log with the classification results.**

- Input: session log path, `axis-classifier` output, research-completed date.
- Write the `axis-classifier` output to a temp file. Run
  `python scripts/assemble.py finalize` with the session log path, the date,
  and the temp file. It fills the date and replaces the pending axis sections.
- Output: session log complete.

## Phase 8 - QC

**Running QC on the session log and research file.**

- Input: session log path, research file path, brief activity record.
- Dispatch `qc-role-intake`. **Loops on FINDINGS:** present findings, route back
  per *Phase routing on failure*, re-run forward, return to Phase 8. Exit on
  **PASS** only.
- Output: PASS verdict.

## Phase 9 - User approval and handoff

**Reviewing key outputs with you and handing off to the gap-analysis skill.**

- Input: QC-passed session log and research file.
- Present the approval block:

  ```
  Title / Company / Level / Industry: <values>
  Axis classification - per axis (Orientation, Industry, Specialty, Level,
    Work-state): <primary> / <secondary>
  Axis gaps: <listed, or "none">
  Session log + Research file: <paths>

  Reply with corrections, or "approved" to hand off.
  ```

- **Loops on rejection.** For each issue, assess whether it could alter
  downstream conclusions or outcomes:
  - Yes (level shifts axis, industry invalidates research, etc.) - recommend
    re-run; route back per *Phase routing on failure*.
  - No (typo, capitalization, swap primary/secondary between value-file-
    confirmed values) - recommend direct edit to the session log or research
    file.

  User chooses. Apply, re-QC, return to Phase 9.
- On approval: state completion. Artifacts are ready for the gap-analysis skill.

## Phase routing on failure

Consumed by Phase 8 (QC failures) and Phase 9 (approval rejections). Route back,
fix, re-run forward (Phase 8 always re-runs); for an approval-path rejection,
return to Phase 9 to re-present the block.

| Finding type | Route back to |
|---|---|
| Metadata wrong (title, company, level, industry) | Phase 2 |
| Research incomplete or wrong | Phase 4 then 5 |
| Axis classification wrong, or gap not recorded in both files | Phase 6 |
| Session log field missing | Phase 7 |
