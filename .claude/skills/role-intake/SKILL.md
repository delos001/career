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
- User-facing status and prompts use plain English. No raw QC check tags or
  route-back labels, no implementation jargon (subagent, JSON). Translate
  every finding, loop status, and error message to what the user needs to
  know to decide or act.
- Phase 8 (QC) and Phase 9 (approval) loop back per *Phase routing on failure*.

## Resume check - run before Phase 0

Ask if this session is for a new role or to resume a previous one?

- **New:** proceed to Phase 0.
- **Resume:** ask the APP-NNN; locate the matching folder under
  `personal/applications/`. Probe and land per the ladder (first match wins):
  1. Folder missing - halt; APP-NNN likely wrong.  Ask for APP-NNN again.
  2. Session log missing - ingest already ran but init did not; re-confirm
     metadata with user and resume at **Phase 3b** (session log write only).
  3. `research.md` missing - resume at start of **Phase 4**.
  4. Axis classification still `_(pending)_` in the session log - resume at start of **Phase 6**.
  5. All filled - resume at start of **Phase 8** (re-QC).

  Before running the landing phase, reload its declared inputs from the
  artifacts already on disk - the prior phases' in-conversation outputs are
  gone on a resume. `jd.md` (and any `comms.md`) holds the JD and comms
  text; the session log holds the confirmed metadata; `research.md` holds
  the research findings.

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
- Read `rules/levels/registry.md` first. Use only values defined there when
  inferring or presenting a level. Do not present a level value not in the
  registry.
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
- **Step 3a - ingest (checkpoint):** Run `python scripts/assemble.py ingest`
  with the slug, APP-NNN, YM, and the JD temp-file (plus comms temp-file if
  present). This creates the folder and writes `jd.md` and optionally `comms.md`
  immediately. Capture the printed paths: `app_folder`, `jd_path`, and
  optionally `comms_path`.
- **Step 3b - session log:** Run `python scripts/assemble.py init` with the
  slug, APP-NNN, YM, confirmed metadata (company, role, level, industry), start
  date, and `--jd-source`. For `--jd-source`: pass `jd_path` from Step 3a,
  unless the original JD source was a URL (pass the URL instead). For
  `--comms-source`: pass `comms_path` from Step 3a if comms were written and
  the original source was a local file; pass `"pasted"` if comms were pasted;
  pass the URL if the original source was a URL; omit if no comms.
- Output: paths printed by `assemble.py init`.

## Phase 4 - Research

**Researching the company, role, and industry in parallel.**

- Input: JD text, company, role, role industry (per Phase 2 confirmation).
- Dispatch three subagents **in parallel** - `company-research`,
  `role-research`, `industry-research` - giving each the JD text, company, and role.
- For `industry-research`: pass the Phase 2 industry label as a starting hint,
  but explicitly instruct the subagent to research the industry the company
  *actually operates in* - using the company name and JD context to identify the
  real sector. The Phase 2 label may be generic or recruiter-facing; the subagent
  should not treat it as the definitive sector if the company's actual business
  suggests otherwise.
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

- Input: session log path, research file path, `axis-classifier` output, research-completed date.
- Write the `axis-classifier` output to a temp file. Run
  `python scripts/assemble.py finalize` with the session log path, the date,
  the temp file, and `--research-file` pointing to `research.md`. It fills the
  date, replaces the pending axis sections in the session log, and writes the
  resolved `## Axis Gaps` section to `research.md`.
- Output: session log complete; `research.md` Axis Gaps section filled.

## Phase 8 - QC

**Running QC on the session log and research file.**

- Input: session log path, research file path, brief activity record.
- Dispatch `qc-role-intake`. **Loops on FINDINGS:** translate the findings
  to plain English for the user, then apply each per *Phase routing on
  failure* (or as a direct session-log edit where the finding specifies
  one), re-run forward, and return to Phase 8.
- Cap the loop at **3 iterations**. Exit earlier on **PASS**. If findings
  remain after the third iteration, stop looping and carry them into the
  Phase 9 approval block so the user decides whether to approve as-is or
  intervene.
- Output: PASS verdict, or the unresolved findings after 3 iterations.

## Phase 9 - User approval and handoff

**Reviewing key outputs with you and handing off to the gap-analysis skill.**

- Input: session log and research file - QC-passed, or with unresolved
  findings carried over after 3 QC iterations.
- Present the approval block:

  ```
  Title / Company / Level / Industry: <values>
  Axis classification - per axis (Orientation, Industry, Specialty, Level,
    Work-state): <primary> / <secondary>
  Axis gaps: <listed, or "none">
  Unresolved QC findings: <listed in plain English, or "none">
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
