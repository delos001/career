---
name: gap-analysis
description: Evaluate candidate-to-role fit. Reads role-intake's research file and the retrieval manifest, detects gaps per critical requirement, runs an interactive loop with the user to close or categorize each gap, scores fit, surfaces items to de-emphasize, and produces a gap analysis artifact plus session log entries for downstream CV creation, interview prep, and career brief. New information surfaced during the loop is captured to a profile-level staging file for a separate profile-update skill. Run this after retrieval.
---

# gap-analysis - evaluate candidate-to-role fit

Produces a **gap analysis artifact** at
`personal/applications/<SLUG>_APP-NNN_YYYY-MM/gap_analysis.md` plus a brief
session log section pointing to the artifact (run date, path, fit score, QC
verdict). New information the user raises during gap closure is appended to
a profile-level staging file at `personal/profile/profile_updates_pending.md`
for a separate profile-update skill to process later.

The gap analysis is a **stopping point**: the user reads it to decide whether
to pursue the role. If they pursue, downstream skills (CV creation, interview
prep, career brief) consume this artifact.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases below run in order; each has a declared input and output.
- Each phase opens with the **bold lead line** under its heading - speak it
  verbatim before running the phase.
- User-facing status and prompts use plain English. No raw QC check tags or
  route-back labels, no implementation jargon (subagent, JSON). Translate
  every finding, loop status, and error message to what the user needs to
  know to decide or act.
- Phase 7 (QC) loops back per *Phase routing on failure*.
- Heavy reading (retrieval manifest, inventory/narrative bodies) lives in
  sub-agents' isolated context, not the main skill's. The main skill
  receives only structured outcomes for the interactive loop.

## Resume check - run before Phase 0

Ask if this session is for a new gap analysis or to resume a previous one?

- **New:** ask the APP-NNN; locate the matching folder under
  `personal/applications/`. Confirm that `research.md` AND `retrieval.md`
  exist in the folder (gap analysis depends on both). If either is missing,
  halt and direct the user to run the missing upstream skill.
- **Resume:** ask the APP-NNN; locate the matching folder. Probe and land
  per the ladder (first match wins):
  1. Folder missing - halt; APP-NNN likely wrong. Ask for APP-NNN again.
  2. `research.md` missing - halt; direct the user to run `/role-intake`.
  3. `retrieval.md` missing - halt; direct the user to run `/retrieval`.
  4. `gap_analysis.md` exists - announce ("Gap analysis already exists for APP-NNN at <path>. Re-run? Y/N.") and on Y resume at **Phase 1**; on N print the path and exit (no Phase 8 walk - the user can open the file directly).
  5. Otherwise - resume at start of **Phase 1**.

  Announce ("Resuming APP-NNN at Phase N.") and proceed without prompting
  further.

## Phase 0 - Intro

**Introducing the gap-analysis skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py gap-analysis` and show the output.
- Output: user oriented.

## Phase 1 - Load context

**Loading the role-intake and retrieval artifacts for this application.**

- Input: application folder path (from the resume check), APP-NNN, slug.
- Read `research.md` from the application folder. Extract:
  - `## Critical Requirements` section (the per-requirement scoring target).
  - `## Role`, `## Company`, `## Industry` summary blocks (role context for downstream judgment).
- Read the session log at `personal/sessions/<SLUG>_APP-NNN_YYYY-MM_SessionLog.md`. Extract the `## Axis Classification` section (passed to `de-emphasize-identifier` as role-context input).
- Read `user-info.md` from the profile folder. Extract the eligibility / fit-signal sections:
  - `## Work Authorization` (Status, Sponsorship Required).
  - `## Geographic Preferences` (Modality, Willing to Relocate).
  - `## Exclusions` (Industries / Company Types).
- Note the corpus paths the downstream sub-agents will read (`retrieval.md` in the application folder; `inventory.md` and `narratives.md` in the profile folder). These files are NOT loaded into main skill context; the `gap-detector` and `de-emphasize-identifier` sub-agents read them in isolated context.
- Output: critical-requirements block, role/company/industry summary, axis classification, user-info eligibility sections, paths to `retrieval.md`, `inventory.md`, `narratives.md`.

## Phase 2 - Eligibility / fit-signal check

**Flagging eligibility mismatches against the role for user review.**

- Input: user-info eligibility sections, role/company/industry context.
- Compare deterministically:
  - **Work Authorization**: if the role text suggests sponsorship is required and user requires sponsorship, flag.
  - **Geographic Preferences**: if the role's modality (remote/hybrid/onsite) or location requirements conflict with user preferences, flag.
  - **Exclusions**: if the role's industry or company type matches a user exclusion, flag.
- Present flags to the user in plain English (if any) with override option per flag: `override` (continue) or `stop` (end the skill). Non-flags are not surfaced.
- Flags do NOT short-circuit the skill on their own. User chooses to continue or stop. Each flag's user decision is recorded for the gap analysis artifact and the recommendation logic in Phase 5.
- If the user chose `stop` on any flag, exit the skill with a brief summary; record the decision in the do-not-pursue folder per Phase 8's "no" path.
- Output: list of flags (type, evidence, user decision).

## Phase 3 - Gap detection

**Detecting per-requirement coverage gaps via the gap-detector sub-agent.**

- Input: critical-requirements block, role/company/industry context, paths to `retrieval.md`, `inventory.md`, `narratives.md`.
- Dispatch `gap-detector` sub-agent with the inputs. The sub-agent reads the manifest, inventory, and narratives in isolated context, assigns sequential `CR-NNN` IDs in the order requirements appear in role-intake's list, evaluates each requirement at arc-level first and entry-level second (per `arc-composition-for-high-impact-roles`), and returns a structured per-requirement assessment.
- Returned shape (one record per requirement): `requirement_id` (CR-NNN), `requirement_text`, `requirement_type`, `verdict` (covered | gap | language-shift), `evidence` (list of `{id, relevance}`), `missing` (gap only), `language_shift` (language-shift only, with role / candidate terminology and entries to reframe), `reasoning`.
- Output: per-requirement assessment list (JSON), held in memory for Phase 4.

## Phase 4 - Interactive gap closure loop

**Walking gaps with the user to close or categorize each.**

- Input: per-requirement assessment list from Phase 3.
- **Step 4a - Compact presentation.** Render the assessment list in plain English: per requirement, show `CR-NNN`, text (short), type, verdict, and a one-line of why. Skip rendering for `covered` requirements that need no user input.
- **Step 4b - Initial categorization.** Ask the user to assign an initial intent to each non-covered item:
  - Gap items: `evidence?` (might have something) / `interview` (defer to interview) / `unresolved` (no plan to close).
  - Language-shift items: `confirm` (re-frame for CV) / `no-shift-needed` (drop as not a real shift).
- **Step 4c - Walk `evidence?` items one at a time.** For each, surface the requirement text and the sub-agent's `missing` field; the user provides clarifying information. Judge in main skill (no sub-agent) whether the information closes the gap. If closed: assign final status `closed` and capture the new information for the staging file per the [[respect-profile-doc-conventions]] rule (concise structured fields, not copy-paste content). If not closed: re-categorize as `interview` or `unresolved`.
- **Step 4d - Final statuses.** Map intents to final statuses per the locked taxonomy:
  - `covered` (from Phase 3, no user input needed).
  - `closed` (was a gap; closed via user input; staging entry queued).
  - `language-shift` (from Phase 3, user confirmed).
  - `interview-deferred` (gap carried into interview, not addressed in CV).
  - `unresolved` (gap acknowledged, no plan to close).
- Initial categorizations from Step 4b are not binding; the user may re-categorize during the walk.
- **Step 4e - Capture notes.** Compose a one-sentence `notes` string for every non-`covered`/non-`language-shift` requirement, recording the reasoning behind the final status:
  - `closed` - short paraphrase of what the user surfaced (e.g., "User cited 18 months of healthcare regulatory work at Acme"). The `Closure ref: PU-NNN` pointer is appended automatically by the renderer in Phase 6; do not add it here.
  - `interview-deferred` - user's stated reason for deferring (or default: "Deferred to interview; no CV-side evidence to cite").
  - `unresolved` - user's stated acknowledgment (or default: "Acknowledged gap; no plan to close").
  `covered` and `language-shift` requirements do not need notes.
- Output: per-requirement final-record list (each carrying `requirement_id`, `requirement_text`, `requirement_type`, `status`, `evidence`, `notes`, and `language_shift` where applicable), and queued staging-file entries (held in memory; written in Phase 6).

## Phase 5 - Fit scoring, de-emphasize, recommendation

**Computing fit, identifying de-emphasize items, and generating the recommendation.**

- Input: per-requirement final status list, Phase 2 flags + decisions.
- **Step 5a - Fit score.** Compute deterministically (in skill body):
  - Per-requirement weight by Type: `must-have=3`, `preferred=2`, `contextual=1`, `duty-derived=1`.
  - Per-requirement coverage credit by status: `covered | closed | language-shift = 1.0`; `interview-deferred | unresolved = 0.0`.
  - Fit score = `sum(weight × credit) / sum(weight)`. Render as percentage with one decimal place (e.g., `78.3%`).
  - Count unmet must-haves: must-have requirements with status `interview-deferred` or `unresolved`.
- **Step 5b - De-emphasize identification.** Dispatch `de-emphasize-identifier` sub-agent with role context (research summaries + axis classification), final per-requirement assessments, and paths to `retrieval.md` and `inventory.md`. Sub-agent returns a list of `{entry_id, rationale}` items.
- **Step 5c - Recommendation.** Generate one of three labels in main skill, with a 1-2 sentence rationale:
  - **`Proceed`** - strong signals across fit, must-haves, eligibility (high fit, zero unmet must-haves, no overriding eligibility flag).
  - **`Proceed with caution`** - mixed signals (moderate fit, 1-2 unmet must-haves, or an overridden eligibility flag).
  - **`Do not pursue`** - weak signals (low fit, multiple unmet must-haves).
  - Soft anchors (consistency, not threshold): fit ≥ ~75% reads as high; 50-75% moderate; < 50% low. Adapt to role context.
- Output: fit score (%), unmet must-haves count, de-emphasize list, recommendation label + rationale.

## Phase 6 - Assemble outputs

**Writing the gap analysis artifact, session log section, and staging-file additions.**

- Input: Phase 2 flags + decisions, Phase 4 per-requirement final status list, Phase 4 queued staging entries, Phase 5 fit score / unmet count / de-emphasize / recommendation.
- **Step 6a - Write gap_analysis.md.** Write the structured inputs to temp files (the requirements list with each record carrying `requirement_id` / `requirement_text` / `requirement_type` / `status` / `evidence` / `notes` / optional `closure_ref` / optional `language_shift`; the eligibility-flags list; the de-emphasize list; the recommendation rationale text). Then run `python scripts/gap_assemble.py assemble --folder <app_folder> --app-id APP-NNN --date YYYY-MM-DD --company <company> --role <role> --fit-score <pct> --unmet-must-haves <count> --recommendation-label <label> --recommendation-rationale-file <path> --requirements-file <path> --eligibility-file <path> --de-emphasize-file <path>`. Renders `templates/gap_analysis.md` with substituted blocks. Language-shift cases are filtered from the requirements list internally; no separate file is passed. Capture the printed path. Non-zero exit = halt per global rules.
- **Step 6b - Append staging entries.** For each queued staging entry, run `python scripts/staging_append.py --captured YYYY-MM-DD --from-app APP-NNN --company <company> --role <role> --closed-requirement <CR-NNN> --requirement-text-short <text> --industry <value> --specialty <value> --orientation <value> --level <value> --work-state <value> --content-file <path> --label <short-label>`. Script assigns the next `PU-NNN` and prints the assigned ID. Capture each PU-NNN; the gap_analysis.md requirement Notes references it inline (Step 6a's `--requirements-file` carries the references).
- **Step 6c - Write session log section.** Build the `## Gap Analysis` section body in a temp file with: Run date, Gap analysis file path, Fit score, QC verdict (filled after Phase 7). Run `python scripts/session_log.py append-section --slug <slug> --app-id APP-NNN --ym YYYY-MM --heading "Gap Analysis" --body-file <path>`. Script replaces the section on re-runs and appends it on first runs. Detail (requirements, language-shift cases, eligibility flags, de-emphasize, recommendation rationale) lives in `gap_analysis.md`; the session log section is a pointer + headline.
- Output: gap_analysis.md written; staging entries appended; session log section written.

## Phase 7 - QC

**Running QC on the gap analysis artifact, session log, and staging additions.**

- Input: gap_analysis.md path, session log path, research.md path, staging file path, inventory.md path, narratives.md path, activity record (PU-NNN entries appended this run, fit score and recommendation computed, eligibility flag outcomes).
- Dispatch `qc-gap-analysis`. **Loops on FINDINGS:** translate the findings to plain English for the user, then apply each per *Phase routing on failure*, re-run forward, return to Phase 7.
- Cap the loop at **3 iterations**. Exit earlier on **PASS**. If findings remain after the third iteration, carry them into Phase 8 so the user sees them. After QC verdict is known, re-run Step 6c to refresh the session log section's QC verdict field.
- Output: PASS verdict, or unresolved findings after 3 iterations.

## Phase 8 - User decision and handoff

**Presenting the recommendation and handing off to the user's pursue decision.**

- Input: gap_analysis.md path, fit score, recommendation, unresolved QC findings (if any).
- Present the decision block:

  ```
  Role: <title> at <company>
  Fit score: <score> (Recommendation: <label>)
  Eligibility flags: <listed in plain English, or "none">
  Key gaps: <unmet must-haves listed with status; or "none">
  Unresolved QC findings: <listed in plain English, or "none">
  Gap analysis: <path>

  Pursue this role? Reply "yes" or "no".
  ```

- **On "yes"**: ask whether to run the profile-update skill now (process queued staging entries into inventory / positioning / narratives) or defer. State that CV creation and interview prep are ready to run.
- **On "no"**: ask whether to record the role in `personal/do-not-pursue/` (per `do-not-pursue-folder`). State completion.

## Phase routing on failure

Consumed by Phase 7 (QC failures). Route back, fix, re-run forward (Phase 7 always re-runs after a fix).

| Finding type | Route back to |
|---|---|
| Artifact section structure malformed or section out of order | Phase 6 |
| Header field missing or malformed | Phase 6 |
| Session log `## Gap Analysis` section missing fields | Phase 6 |
| Critical requirement dropped from Requirements section | Phase 3 |
| Requirement status missing or off-taxonomy | Phase 4 |
| Non-covered requirement missing Notes | Phase 4 |
| Closure / staging linkage broken | Phase 6 |
| Fabricated EX/PR/ST/DC ID in Requirements evidence | Phase 3 |
| Fabricated EX/PR ID in De-emphasize | Phase 5 |
| Fabricated PU-NNN reference | Phase 6 |
| Session log mirroring divergence | Phase 6 |
| Fit-score math wrong or unmet-must-haves count wrong | Phase 5 |
| Recommendation label off-set | Phase 5 |
