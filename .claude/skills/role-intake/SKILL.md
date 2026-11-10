---
name: role-intake
description: Understand a job opportunity - ingest a job description, research the company/role/industry, extract the critical requirements, and produce a session log plus a research file. Run this first when evaluating a new role; role-classify runs next.
---

# role-intake - understand the job

Builds the foundational understanding of a job opportunity. It produces two artifacts that later skills will consume: a **session log** and a **research file**.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases below run in order; each has a declared input and output.
- Each phase opens with the **bold lead line** under its heading - speak it verbatim before running the phase.
- User-facing status and prompts use plain English. No raw QC check tags or route-back labels, no implementation jargon (subagent, JSON). Translate every finding, loop status, and error message to what the user needs to know to decide or act.
- Phase 6 (QC) and Phase 7 (approval) loop back per *Phase routing on failure*.
- **Run-scratch goes in the application's scratch folder.** `<scratch>` denotes `<app_folder>/scratch/`; create it if absent. Write every working file this skill produces - and tell every sub-agent it spawns to write its output files - under `<scratch>`, never the shared `temp/`. Scratch persists for the life of the application (a resumed run reuses it); it is wiped in one shot by `scratch_cleanup.py` when the application is declined (gap-analysis) or closed (the `close-application` skill).

## Resume check - run before Phase 0

Ask if this session is for a new role or to resume a previous one?

- **New:** proceed to Phase 0.
- **Resume:** ask the APP-NNN; locate its folder with `python scripts/paths.py app <APP-NNN>`. Probe and land per the ladder (first match wins):
  1. Folder missing - halt; APP-NNN likely wrong.  Ask for APP-NNN again.
  2. Session log missing - ingest already ran but init did not; re-confirm metadata with user and resume at **Phase 3b** (session log write only).
  3. `research.md` missing - resume at start of **Phase 4**.
  4. Otherwise - resume at start of **Phase 6** (re-QC).

  Before running the landing phase, reload its declared inputs from the artifacts already on disk - the prior phases' in-conversation outputs are gone on a resume. `jd.md` (and any `comms.md`) holds the JD and comms text; the session log holds the confirmed metadata; `research.md` holds the research findings.

  Announce ("Resuming APP-NNN at Phase N.") and proceed without prompting.

## Phase 0 - Intro (new runs only)

**Introducing the role-intake skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py role-intake` and show the output.
- Output: user oriented.

## Phase 1 - JD + comms ingestion

**Ingesting the Job Description and any role communications.**

- Input: paste text, or a source path/URL for the JD.
- For a file path or URL, run `python scripts/ingest/jd_extract.py <source>`; capture stdout. Non-zero exit = halt per global rules.
- Ask the user about role communications (e.g. recruiter email). Ingest via `jd_extract.py` if file/URL; accept pasted text otherwise.
- Output: JD text + source; comms text + source if any. ("Source" = URL, original file path, or `"pasted"`.)

## Phase 2 - Metadata extraction + confirmation

**Extracting role title and company from the JD.**

- Input: JD text + comms.
- Infer title and company only. Do NOT infer level or industry here - inferring them from the JD alone is unreliable (a JD's industry is often recruiter-facing or generic, and level is a registry judgment). The role-classify skill decides them after the research is done.
- Prompt the user for title or company if either cannot be inferred.
- Present for explicit confirmation:

  ```
  Confirm role metadata:
    Title:    <value>
    Company:  <value>
  Reply with corrections or "confirmed".
  ```

- Re-present on corrections until confirmed.
- Output: user-confirmed {title, company}.

## Phase 3 - Session init

**Creating the application folder and starting the session log.**

- Input: title, company; JD text + source; comms text + source (if any).
- Run `python scripts/app_id.py` once; it claims the next APP-NNN and prints it. Use that ID for the whole run and never re-run the script for it (each run claims a new number). Determine the current `YYYY-MM`.
- **Resolve the company slug from the registry first.** Run `python scripts/company_slug.py lookup --company "<confirmed company>"`.
  - If it prints a slug, reuse it (do NOT ask). Tell the user which slug is being reused, e.g. "Using the existing slug `thermofisher` for Thermo Fisher Scientific."
  - If it prints nothing (company not seen before), ask the user for a short lowercase slug, then record it for reuse: `python scripts/company_slug.py record --company "<confirmed company>" --slug "<slug>"`.
- Write JD (and comms if present) to scratch files under `<scratch>` (this first write creates the application folder; the `ingest` step in 3a tolerates the pre-existing folder).
- **Step 3a - ingest (checkpoint):** Run `python scripts/assemble.py ingest` with `--slug`, `--app-id`, `--ym`, `--jd-text-file` (plus `--comms-text-file` if present). This creates the folder and writes `jd.md` and optionally `comms.md` immediately. Capture the printed paths: `app_folder`, `jd_path`, and optionally `comms_path`.
  - **Identity header for unlabeled JDs.** Check whether the confirmed role title and company each actually appear in the JD body. For any that do NOT, pass it so ingest prepends an identity header to `jd.md`: `--add-title "<title>"` and/or `--add-company "<company>"`. This keeps a JD that carries no in-text identifiers traceable to its application when read in isolation. Omit the flag for a value the JD already names (no redundant header).
- **Step 3b - session log:** Run `python scripts/assemble.py init` with the slug, APP-NNN, YM, confirmed metadata (company, role), `--start-date`, and `--jd-source`. Do NOT pass `--level` or `--industry`; init writes them as pending for role-classify. For `--jd-source`: pass `jd_path` from Step 3a, unless the original JD source was a URL (pass the URL instead). For `--comms-source`: pass `comms_path` from Step 3a if comms were written and the original source was a local file; pass `"pasted"` if comms were pasted; pass the URL if the original source was a URL; omit if no comms.
- Output: paths printed by `assemble.py init`.

## Phase 4 - Research

**Researching the company, role, industry, and critical requirements in parallel.**

- Input: JD text, company, role.
- Dispatch four subagents **in parallel** - `company-research`, `role-research`, `industry-research`, and `critical-requirements-extractor`. For each, run `python scripts/dispatch_prompt.py <agent> --folder <app_folder>` and send the prompt between `=== PROMPT ===` and `=== END ===` **exactly as printed**. Non-zero exit = halt per global rules; never supply a missing input by hand.
- `critical-requirements-extractor` scans every JD section (not just labeled "Requirements") and emits a `| # | Text | Type | Source |` table of competency requirements; the `#` column is a 1-based sequential index that maps to each requirement's downstream `CR-NNN` id.
- Each returns a fixed block:
  - `company-research` -> `## Company` with Summary / Key facts / Sources.
  - `role-research` -> `## Role` with Summary / Key facts / Sources.
  - `industry-research` -> `## Industry` with Summary / Key facts / Sources.
  - `critical-requirements-extractor` -> `## Critical Requirements` as a `| # | Text | Type | Source |` table. Scoped to what this skill needs to classify and characterize, not exhaustive dossiers.
- Output: four structured findings blocks.

## Phase 5 - Research file assembly

**Assembling the research findings into the research file.**

- Input: four findings blocks.
- Write each block to its own scratch file under `<scratch>`, then run `python scripts/assemble.py research` with `--folder`, `--app-id`, `--company`, `--role`, `--date`, and the four scratch-file paths (`--company-file`, `--role-file`, `--industry-file`, `--critical-requirements-file`). It section-replaces only role-intake's own sections so nothing else is clobbered.
- Output: `research.md` written and the session log's research-completed date filled. Ranked Needs, Axis Gaps, and the session log's axis sections stay pending for role-classify.

## Phase 6 - QC

**Running QC on the session log and research file.**

- Input: session log path, research file path.
- **Step 6a - Mechanical checks (script).** Run `python scripts/role_intake_qc.py check --folder <app_folder>`. The script owns section and field presence, pending markers, date form, URL presence, cross-file field equality, and requirement quotes and modifiers against the JD. On FAIL: translate the failed checks to plain English for the user, apply each per *Phase routing on failure* (or as a direct session-log edit for a one-field correction), re-run forward, and return to Step 6a.
- **Step 6b - Judgment checks (subagent).** Only after Step 6a passes, run `python scripts/dispatch_prompt.py qc-role-intake --folder <app_folder>` and dispatch `qc-role-intake` with the printed prompt exactly as printed. It verifies substance only (claims trace to sources, no section completed on partial content). **Loops on FINDINGS:** translate to plain English, apply per *Phase routing on failure*, re-run forward (Step 6a re-runs after any fix), and return to Phase 6.
- **Show every content edit as before/after.** Whenever a fix changes the wording or substance of the session log or research file, present a before/after table (one row per changed passage: location, before, after) before re-running QC. Skip the table only for purely mechanical fixes that have no meaningful "before" (filling a blank required field, a date, a path).
- Cap the loop at **3 iterations**. Exit earlier on **PASS**. If findings remain after the third iteration, carry them to Phase 7 Step 7a.
- Output: PASS verdict, or the unresolved findings after 3 iterations.

## Phase 7 - User approval and handoff

**Reviewing the research with you and handing off to role-classify.**

- **Step 7a - unresolved findings, one at a time.** Skip if QC passed. Otherwise present each carried-over finding as its own decision, one per response: what is wrong, the recommended fix, and the before/after text. Act on the user's decision before presenting the next.
- **Step 7b - approval.** Give the session log and research file paths and ask for corrections or "approved". On a correction, route back per *Phase routing on failure*, re-QC, and return here.
- On approval: tell the user the application is ready for `/role-classify`. Run-scratch in `<scratch>` is left in place (it is wiped when the application is closed or declined).

## Phase routing on failure

Consumed by Phase 6 (QC failures) and Phase 7 (corrections). Route back, fix, re-run forward; Phase 6 always re-runs.

| Finding type | Route back to |
|---|---|
| Title or company wrong | Phase 2 |
| Research incomplete or wrong, or a requirement's quote or modifier fails against the JD | Phase 4 then 5 (re-extracted requirements void any ranking, so role-classify reruns) |
