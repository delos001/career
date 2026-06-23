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
- **Run-scratch goes in the application's scratch folder.** `<scratch>` denotes
  `<app_folder>/scratch/`; create it if absent. Write every working file this
  skill produces - and tell every sub-agent it spawns to write its output files -
  under `<scratch>`, never the shared `temp/`. Scratch persists for the life of
  the application (a resumed run reuses it); it is wiped in one shot by
  `scratch_cleanup.py` when the application is declined (gap-analysis) or closed
  (the `close-application` skill).

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

**Extracting role title and company from the JD.**

- Input: JD text + comms.
- Infer title and company only. Do NOT infer level or industry here - inferring
  them from the JD alone is unreliable (a JD's industry is often recruiter-facing
  or generic, and level is a registry judgment). They are decided later, after
  the research is done and the axis files are read, by the axis-classifier
  (Phase 6) and written into the session log at finalize (Phase 7).
- Prompt the user for title or company if either cannot be inferred.
- Present for explicit confirmation:

  ```
  Confirm role metadata:
    Title:    <value>
    Company:  <value>
  Reply with corrections or "confirmed".
  ```

- Re-present on corrections until confirmed.
- Output: user-confirmed {title, company}. Level and industry are deferred to
  Phase 6/7.

## Phase 3 - Session init

**Creating the application folder and starting the session log.**

- Input: title, company; JD text + source; comms text + source (if any).
  (Level and industry are not known yet - they are decided at Phase 6/7.)
- Run `python scripts/app_id.py` for the next APP-NNN. Determine the current `YYYY-MM`.
- **Resolve the company slug from the registry first.** Run
  `python scripts/company_slug.py lookup --company "<confirmed company>"`.
  - If it prints a slug, reuse it (do NOT ask). Tell the user which slug is being
    reused, e.g. "Using the existing slug `thermofisher` for Thermo Fisher Scientific."
  - If it prints nothing (company not seen before), ask the user for a short
    lowercase slug, then record it for reuse:
    `python scripts/company_slug.py record --company "<confirmed company>" --slug "<slug>"`.
- Write JD (and comms if present) to scratch files under `<scratch>` (this first write creates the application folder; the `ingest` step in 3a tolerates the pre-existing folder).
- **Step 3a - ingest (checkpoint):** Run `python scripts/assemble.py ingest`
  with `--slug`, `--app-id`, `--ym`, `--jd-text-file` (plus `--comms-text-file`
  if present). This creates the folder and writes `jd.md` and optionally
  `comms.md` immediately. Capture the printed paths: `app_folder`, `jd_path`,
  and optionally `comms_path`.
  - **Identity header for unlabeled JDs.** Check whether the confirmed role
    title and company each actually appear in the JD body. For any that do NOT,
    pass it so ingest prepends an identity header to `jd.md`: `--add-title
    "<title>"` and/or `--add-company "<company>"`. This keeps a JD that carries
    no in-text identifiers traceable to its application when read in isolation.
    Omit the flag for a value the JD already names (no redundant header).
- **Step 3b - session log:** Run `python scripts/assemble.py init` with the
  slug, APP-NNN, YM, confirmed metadata (company, role), `--start-date`, and
  `--jd-source`. Do NOT pass `--level` or `--industry` - they are deferred to the
  axis-classifier; init writes them as pending and finalize (Phase 7) fills them.
  For `--jd-source`: pass `jd_path` from Step 3a,
  unless the original JD source was a URL (pass the URL instead). For
  `--comms-source`: pass `comms_path` from Step 3a if comms were written and
  the original source was a local file; pass `"pasted"` if comms were pasted;
  pass the URL if the original source was a URL; omit if no comms.
- Output: paths printed by `assemble.py init`.

## Phase 4 - Research

**Researching the company, role, industry, and critical requirements in parallel.**

- Input: JD text, company, role.
- Dispatch four subagents **in parallel** - `company-research`,
  `role-research`, `industry-research`, and `critical-requirements-extractor` -
  giving each the JD text plus the company and role context they need.
- For `industry-research`: instruct the subagent to identify and research the
  industry the company *actually operates in*, using the company name and JD
  context to determine the real sector. No industry label is inferred at Phase 2,
  so the subagent establishes the sector from scratch rather than confirming a
  prior guess.
- For `critical-requirements-extractor`: pass the full JD text. The agent scans
  every JD section (not just labeled "Requirements") and emits a
  `| # | Text | Type | Source |` table of competency requirements; the `#`
  column is a 1-based sequential index that maps to each requirement's
  downstream `CR-NNN` id.
- Each returns a fixed block:
  - `company-research` -> `## Company` with Summary / Key facts / Sources.
  - `role-research` -> `## Role` with Summary / Key facts / Sources.
  - `industry-research` -> `## Industry` with Summary / Key facts / Sources.
  - `critical-requirements-extractor` -> `## Critical Requirements` as a `| # | Text | Type | Source |` table.
  Scoped to what this skill needs to classify and characterize, not exhaustive
  dossiers.
- Output: four structured findings blocks.

## Phase 5 - Research file assembly

**Assembling the research findings into the research file.**

- Input: four findings blocks.
- Write each block to its own scratch file under `<scratch>`, then run `python scripts/assemble.py
  research` with `--folder`, `--app-id`, `--company`, `--role`, `--date`, and
  the four scratch-file paths (`--company-file`, `--role-file`, `--industry-file`,
  `--critical-requirements-file`). It section-replaces only role-intake's own
  sections so nothing else is clobbered.
- Output: `research.md` written.

## Phase 6 - Axis classification

**Classifying the role against the five axes.**

- Input: JD text, research findings.
- Dispatch `axis-classifier` with the JD text and the research findings. It
  classifies all five axes - including level and industry - from scratch; no
  level or industry is inferred earlier, so there are no "confirmed starting
  points" to hand it. The classifier is the authoritative source for every axis.
  It works registry-first per axis: read the registry, pick candidate value(s),
  read only the candidate value files, confirm each pick. It must commit to a
  value on every axis; an axis gap has only two legitimate causes - no registry
  value confirms, or a value confirms but its rule file is not yet authored
  (`File deferred`). Indecision between confirming values is never a gap.
- **Resolution gate (checkpoint).** Every axis must carry a confirmed value AND
  a present rule file before this skill proceeds to Phase 7. The CV writer
  applies the per-value rule files, so a value with no file cannot be handed off.
  If the classifier returns any axis gap, do NOT continue to Phase 7. Halt here,
  state each gap to the user in plain English, and resolve it before moving on:
  - **File deferred** (value confirmed, file missing) → run the matching builder
    skill (`orientation-builder`, `industry-builder`, `specialty-builder`,
    `level-builder`, or `work-state-builder`) to author the rule file, then
    re-invoke role-intake; the resume ladder returns to Phase 6 (axis still
    pending in the session log) and re-classifies against the now-complete rules.
  - **No registry value confirms** → present the closest registry values; the
    user either maps the role to an existing value (re-run the classifier with
    that steer) or runs the builder to author a new registry value, after which
    role-intake is re-invoked and re-classifies.
  No axis gap is ever recorded-and-carried past this point. Only once all five
  axes are fully resolved (value + file) does the skill advance to Phase 7.
- Output: per-axis primary/secondary with one-line rationale each; zero
  outstanding axis gaps.

## Phase 7 - Session log finalization

**Finalizing the session log with the classification results.**

- Input: session log path, research file path, `axis-classifier` output, research-completed date.
- Write the `axis-classifier` output to a scratch file under `<scratch>`. Run
  `python scripts/assemble.py finalize` with `--session-log`, `--date`,
  `--axis-file`, and `--research-file` pointing to `research.md`. It fills the
  date, fills the pending Level and Industry metadata lines from the axis result,
  replaces the pending axis sections in the session log, and writes the resolved
  `## Axis Gaps` section to `research.md`.
- Output: session log complete (Level and Industry now filled from the axis
  classification); `research.md` Axis Gaps section filled.

## Phase 8 - QC

**Running QC on the session log and research file.**

- Input: session log path, research file path, brief activity record.
- Dispatch `qc-role-intake`. **Loops on FINDINGS:** translate the findings
  to plain English for the user, then apply each per *Phase routing on
  failure* (or as a direct session-log edit where the finding specifies
  one), re-run forward, and return to Phase 8.
- **Show every content edit as before/after.** Whenever a fix changes the
  wording or substance of the session log or research file, present a
  before/after table (one row per changed passage: location, before, after)
  before re-running QC, so the user can spot-check the change. This covers
  any edit that alters claims, framing, or text - including those a sub-agent
  re-run produces. Skip the table only for purely mechanical fixes that have
  no meaningful "before" (filling a blank required field, a date, a path).
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
  Axis classification:
    Orientation:  <primary>[, <secondary>] - <rationale>
    Industry:     <value> - <rationale>
    Specialty:    <primary>[, <secondary>] - <rationale>
    Level:        <value> - <rationale>
    Work-state:   <value> - <rationale>
  Axis gaps: none  (all five axes are resolved by the Phase 6 gate; this line is
             a backstop and must read "none" - if it does not, return to Phase 6)
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
- On approval: state completion. Artifacts are ready for the retrieval skill.
  Run-scratch in `<scratch>` is left in place (it is wiped when the application
  is closed or declined), not deleted here.

## Phase routing on failure

Consumed by Phase 8 (QC failures) and Phase 9 (approval rejections). Route back,
fix, re-run forward (Phase 8 always re-runs); for an approval-path rejection,
return to Phase 9 to re-present the block.

| Finding type | Route back to |
|---|---|
| Metadata wrong (title, company, level, industry) | Phase 2 |
| Research incomplete or wrong | Phase 4 then 5 |
| Axis classification wrong, or an axis gap reached handoff unresolved | Phase 6 (resolve the gap via the builder before proceeding; gaps must not pass the Phase 6 gate) |
| Session log field missing | Phase 7 |
