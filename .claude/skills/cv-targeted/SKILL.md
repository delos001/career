---
name: cv-targeted
description: Draft a role-tailored CV. Reads role-intake's research file, the retrieval manifest, and the gap analysis, then a lead writer (cv-architect) composes the CV while three stakeholders (career-strategist for craft, hiring-manager for fit and credibility, candidate-advocate for the applicant's interest) shape it and QC verifies every claim traces to a real inventory entry. Produces cv_content.md (text only, with source-citation comments) plus a session log section. Run after gap-analysis; the .docx render is a separate skill.
---

# cv-targeted - draft a role-tailored CV

Produces a **CV content artifact** at
`personal/applications/<SLUG>_APP-NNN_YYYY-MM/cv_content.md` (text only, every
content unit carrying a source-citation comment), an internal `drafting_plan.md`
in the same folder, and a brief session log section pointing to the artifact.
`cv_content.md` is the sole handoff to the separate render skill (cv-render);
this skill stops at the cited text and does not produce a .docx.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases below run in order; each has a declared input and output.
- Each phase opens with the **bold lead line** under its heading - speak it
  verbatim before running the phase.
- User-facing status and prompts use plain English. No raw check ids, route-back
  labels, or implementation jargon (subagent, JSON). Translate every finding,
  loop status, and error to what the user needs to decide or act.
- **Single writer:** only the cv-architect edits the CV text. The stakeholders
  (career-strategist, hiring-manager, candidate-advocate) and QC return
  contributions and findings; the architect integrates them. This is the
  traceability control.
- Heavy reading (inventory, narratives, retrieval manifest) lives in the
  sub-agents' isolated context, not the main skill's. The main skill carries
  only compact contributions, findings, and loop state.
- Phase 3 (collaboration) and Phase 4 (QC) loop per their caps; on a bounded
  loop failure the artifact ships provisional with findings surfaced.
- **Run-scratch goes in the application's scratch folder.** `<scratch>` denotes
  `<app_folder>/scratch/`; create it if absent. Write every working file this
  skill produces - and tell every sub-agent it spawns to write its output files -
  under `<scratch>`, never the shared `temp/`. Scratch persists for the life of
  the application (a resumed run reuses it); it is wiped in one shot by
  `scratch_cleanup.py` when the application is declined (gap-analysis) or closed
  (the `close-application` skill).

## Resume check - run before Phase 0

Ask if this session is for a new CV or to resume a previous one.

- **New:** ask the APP-NNN; locate the matching folder under
  `personal/applications/`. Confirm `research.md`, `retrieval.md`, AND
  `gap_analysis.md` all exist in the folder (cv-targeted depends on all three).
  If any is missing, halt and direct the user to run the missing upstream skill.
- **Resume:** ask the APP-NNN; locate the matching folder. Probe and land per
  the ladder (first match wins):
  1. Folder missing - halt; APP-NNN likely wrong. Ask for APP-NNN again.
  2. `research.md` missing - halt; direct the user to run `/role-intake`.
  3. `retrieval.md` missing - halt; direct the user to run `/retrieval`.
  4. `gap_analysis.md` missing - halt; direct the user to run `/gap-analysis`.
  5. `cv_content.md` exists - announce ("A CV already exists for APP-NNN at
     <path>. Re-run? Y/N.") and on Y resume at **Phase 3** against the existing
     draft; on N print the path and exit.
  6. `drafting_plan.md` exists without `cv_content.md` - resume at **Phase 2**.
  7. Otherwise - resume at the start of **Phase 1**.

  Announce ("Resuming APP-NNN at Phase N.") and proceed without prompting
  further.

## Phase 0 - Intro

**Introducing the cv-targeted skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py cv-targeted` and show the output.
- Output: user oriented.

## Phase 1 - Load context

**Loading the upstream artifacts and the CV rules for this application.**

- Input: application folder path (from the resume check), APP-NNN, slug.
- Read `research.md` from the application folder. Extract:
  - the `## Critical Requirements` section (each requirement's text and type;
    research.md carries no stable id, the `CR-NNN` ids are assigned downstream by
    gap-analysis, below),
  - the `## Role`, `## Company`, `## Industry` summary blocks (role context).
- Read the session log (`session_log.md`) from the application folder. Extract
  the `## Axis Classification` section (the five axis values, each with primary and
  optional secondary), and from it the candidate **level** (`ic` or
  `leadership`, the level axis value). The session log is the authoritative
  source for the classification (per `retrieval-architecture-2026-05`); the same
  source retrieval reads.
- Read `gap_analysis.md`. Extract:
  - The per-requirement coverage statuses keyed by `CR-NNN`. The `CR-NNN` ids
    are gap-analysis's id space and are the authoritative requirement ids for
    the CV; each maps positionally (same order) to a `research.md` requirement,
    and to the bare "requirement N" references in `retrieval.md`.
  - The `## De-emphasize` list (entry ids to down-weight).
  - The `## CV Notes` section. This is general framing guidance from the
    gap-closure session that applies across the CV rather than to a single
    requirement. Surface it as a named input alongside the requirement statuses
    and de-emphasize list; the cv-architect must review and apply it before
    drafting begins.
- Read `user-info.md` from the profile folder (`personal/profile/`). Extract the
  contact block (name, location, contact line, profile links) for the CV header.
- **Resolve the axis value files.** For each classified axis value, resolve its
  rule file path `rules/<axis>/<value>.md`. Pass the files that exist to the
  sub-agents; for any axis marked "File deferred" in the classification, note it
  (the architect proceeds without that axis's voice file and the gap is surfaced
  at handoff).
- **CV best-practices staleness check.** Narrate this in plain English before
  running it, e.g. "Let me check that the CV best-practices guidance this skill
  relies on is still current." Do not name the field or call it a "staleness
  check" to the user. Read the `last_researched` field from
  `rules/cv/cv-best-practices.md`. If it is more than ~12 months older than today,
  surface a plain-English warning that the CV best-practices research may be due
  for a refresh (per the `cv-best-practices-refresh` process). Non-blocking; the
  run continues.
- Note the corpus paths the sub-agents will read in their own context, NOT loaded
  into the main skill. From the profile folder (`personal/profile/`):
  `inventory.md`, `narratives.md`. From the application folder: `retrieval.md`,
  `gap_analysis.md`, `jd.md`, and `comms.md` (if present). From `rules/`:
  `rules/cv/cv-structure.md`, `rules/cv/cv-best-practices.md`, and the resolved
  axis files.
- Output: critical requirements; axis classification with resolved axis-file
  paths (and any deferred-axis note); level; de-emphasize list; per-requirement
  coverage; CV Notes (general framing guidance, or empty); contact block;
  staleness warning (if any); corpus paths.

## Phase 2 - Initial draft

**Composing the first CV draft via the cv-architect.**

- Input: from Phase 1 - folder path, level, the resolved axis-file paths, and the
  corpus paths.
- Dispatch the `cv-architect` sub-agent in `mode = draft` with: the application
  folder path, the `level`, the CV Notes (general framing guidance extracted in
  Phase 1 — pass inline if short, or as a file path), and paths to
  `rules/cv/cv-structure.md`, the resolved axis files, `research.md`,
  `retrieval.md`, `gap_analysis.md`, `inventory.md`, `narratives.md`, and
  `user-info.md`. The architect must apply the CV Notes as standing constraints
  before selecting and framing any content. For requirements with status
  `partial-match`, the architect cites the transferable experience honestly
  without overclaiming — the CV shows the real capability the candidate has, not
  the full capability the JD requires; the Notes field on each partial-match
  requirement describes what to cite and what the gap is. The architect writes
  `drafting_plan.md` first (recording how CV Notes constraints and partial-match
  framings were applied), then composes `cv_content.md` with a citation on every
  unit, and returns its compact summary
  (paths, sections, estimated pages, de-emphasized applied, self-flagged issues).
- **Initialize the collaboration log.** Write `cv_collaboration_log.md` with a
  header (APP-NNN, role, company, date) and a Round 0 record of the initial draft
  (the architect's summary: sections, estimated pages, de-emphasized applied,
  self-flagged). The orchestrator writes this log directly throughout; it is an
  internal record, not handed to cv-render.
- Output: `cv_content.md`, `drafting_plan.md`, and `cv_collaboration_log.md` on
  disk; the architect summary held for the loop.

## Phase 3 - Stakeholder collaboration loop

**Shaping the draft with the career-strategist, hiring-manager, and candidate-advocate.**

- Input: `cv_content.md`, `drafting_plan.md`, and `cv_collaboration_log.md` paths,
  corpus paths, level.
- **Step 3a - Parallel stakeholder pass.** On the first round, spawn
  `career-strategist`, `hiring-manager`, and `candidate-advocate` in parallel
  with the input sets below. They do not see each other's output; the architect
  is the single reconciliation point. **The three advisors persist for the life
  of the run.** On every later round, do not spawn new advisor agents: continue
  each existing advisor (SendMessage to its agent id), passing only the
  architect's dispositions of its own prior-round contributions (from the
  architect's previous return) and the instruction to re-read the revised
  `cv_content.md` and re-assess. A continued advisor already holds its sources
  from the first round and must not re-read them. If an advisor cannot be
  continued (the run was resumed in a new session, or the agent is gone),
  re-spawn it fresh with its full first-round input set.
  - `career-strategist` gets: `cv_content.md`, `rules/cv/cv-structure.md`,
    `rules/cv/cv-best-practices.md`, the level and orientation axis files,
    `research.md`, and `level`.
  - `hiring-manager` gets: `cv_content.md`, `research.md`, `gap_analysis.md`,
    `retrieval.md`, `jd.md` (and `comms.md` if present), and `level`.
  - `candidate-advocate` gets: `cv_content.md`, `retrieval.md`, `gap_analysis.md`,
    `inventory.md`, `narratives.md`, `research.md`, and `level`.
  Each returns a verdict (`satisfied` or `contributions`) and any contributions
  tagged `material` or `nit`. The hiring-manager may additionally return
  `suspected_extraction_misses[]` (a critical JD element absent from both the
  requirements and the gap analysis). Collect these separately; they are NOT
  contributions and do not enter the Phase 3c integrate loop or affect
  convergence. They are surfaced as an advisory note at handoff (Phase 6).
- **Step 3b - Convergence check.** If all three return `satisfied` (no material
  contributions), the loop has converged. If any nits remain, carry them into one
  final integration; otherwise proceed directly to Phase 4. Do not run further
  stakeholder rounds once converged, regardless of how many of the 3 rounds remain.
- **Step 3c - Integrate.** If any has material contributions, dispatch
  `cv-architect` in `mode = revise` with the combined contributions and the
  existing draft/plan paths. The architect seeks good-faith compromise on each
  contribution, arbitrates any genuine cross-advisor conflict by its precedence
  (logging the call in `drafting_plan.md`), edits `cv_content.md` in place, and
  returns its summary, including a disposition for every material contribution
  (integrated / partial / declined, with a reason addressed to the advisor on
  anything less than fully integrated) and any cross-advisor arbitration calls.
- **Step 3d - Loop.** Repeat 3a-3c until converged or a **cap of 3 rounds**. If
  the cap is reached with material contributions still open, carry them forward
  to handoff for the user to see; do not block.
- **Step 3e - Log the round.** Append a round record to `cv_collaboration_log.md`:
  each stakeholder's verdict and contributions verbatim (location, severity,
  observation, direction, rationale), then the architect's disposition of every
  material contribution (integrated / partial / declined, with the reason given
  to the advisor) and any cross-advisor arbitration calls. Every material
  contribution must appear with a disposition; none is dropped silently. Also
  record any `suspected_extraction_misses` the hiring-manager returned this round
  (deduped by JD element across rounds) under a `Suspected extraction misses`
  note; these carry forward to Phase 6 unchanged (the architect does not act on
  them).
- Narrate each round in plain English (what each stakeholder contributed and that
  the architect is integrating), not check ids or agent mechanics.
- Context-safe: the advisors hold their sources in their own persistent isolated
  contexts and the architect revises from on-disk state, so the main skill
  accumulates only compact contributions and a round counter. Advisor
  persistence is within-session only; a cross-session resume re-spawns fresh.
- Output: the converged (or cap-reached) `cv_content.md` and `drafting_plan.md`;
  any unresolved material contributions carried forward; the log updated.

## Phase 4 - QC gate

**Verifying the CV: mechanical checks plus traceability judgment.**

- Input: `cv_content.md`, `inventory.md`, `narratives.md`, `gap_analysis.md`,
  `research.md`, level, `cv_collaboration_log.md` path.
- **Step 4a - Mechanical QC.** Run `python scripts/cv_qc.py --cv-file <cv_content.md>
  --inventory <inventory.md> --narratives <narratives.md> --level <level>
  --gap-analysis <gap_analysis.md>`. Parse the per-check JSON (this includes the
  L1 page-length guard). A non-zero exit is a script error: halt per global rules.
- **Step 4b - Judgment QC.** Dispatch `qc-cv-targeted` with `cv_content.md`,
  `inventory.md`, `narratives.md`, `research.md`, and `level`. It returns a verdict
  and any semantic-traceability / acronym / summary-support / judgment-AI-tell
  findings.
- **Step 4c - Aggregate and log.** Combine the mechanical check failures and the
  judgment findings into one findings list. Append the QC verdict and findings to
  `cv_collaboration_log.md`.
- **Step 4d - Fix loop.** If there are findings, dispatch `cv-architect` in
  `mode = revise` with them; the architect fixes `cv_content.md` and the fixes are
  appended to the log. Re-run 4a-4c. Cap at **3 iterations**; exit early when both
  QC layers pass. On a length finding, pass the architect the measured page count
  and the longest offending lines so it trims from real data, not a self-estimate.
  Also pass the Phase-3 integrated/partial contributions from the log; the
  architect returns `qc_regressions` for any fix that reverses or weakens one.
  Append any `qc_regressions` to the log and carry them to handoff.
- **Step 4e - Bounded-loop failure.** If findings remain after the third iteration,
  ship **provisional**: keep `cv_content.md`, append a provisional record to
  `design/build_issues.md` (per `artifact-skill-qc-internal`), write the final
  status to the collaboration log, and carry the remaining findings to handoff so
  the user sees them.
- Narrate QC outcomes in plain English (what failed and that it is being fixed),
  not raw check ids.
- Output: PASS, or provisional with surfaced findings; final `cv_content.md`;
  collaboration log updated.

## Phase 5 - Write session-log section

**Writing the session log section for this CV run.**

- Input: APP-NNN, slug, ym; `cv_content.md`, `drafting_plan.md`, and
  `cv_collaboration_log.md` paths; estimated pages; QC verdict; role and company.
- Build the `## Targeted CV (cv-targeted)` section body in a scratch file (`<scratch>/...`) with: Run
  date, Role and company, CV content file path, Drafting plan path, Collaboration
  log path, Estimated page count, QC verdict.
- Run `python scripts/session_log.py append-section --folder <app_folder>
  --heading "Targeted CV (cv-targeted)" --body-file <path>`. The
  script replaces the section on re-runs and appends it on first runs.
- Detail lives in `cv_content.md`, `drafting_plan.md`, and `cv_collaboration_log.md`;
  the session log section is a pointer plus headline, consistent with the other
  skills.
- Output: session log section written.

## Phase 6 - Handoff

**Presenting the CV and handing off to the render stage.**

- Input: `cv_content.md` path, estimated pages, QC verdict, any unresolved items
  (open stakeholder contributions from a Phase 3 cap, or provisional QC findings
  from Phase 4), and the Phase 1 notes (best-practices staleness warning,
  deferred-axis note).
- **Compose Open items from `cv_collaboration_log.md`:** for each material
  contribution still open at the Phase 3 cap, list its advisor, the ask, and the
  architect's reason for not fully integrating it (pulled from the logged
  dispositions); add any provisional QC findings from Phase 4. This gives the user
  a precise, reviewable account of what was left unresolved and why, since the
  workflow proceeds without requiring full agreement. Render "none" if empty.
- **Compose Possible missed requirements from `cv_collaboration_log.md`:** for
  each suspected extraction miss the hiring-manager flagged (deduped by JD
  element), state it as a plain advisory: the JD appears to emphasize this, it is
  absent from the tracked requirements and gap analysis, so the pipeline never
  evaluated it, and the user should address it upstream if it is a real
  requirement. This is advisory only (a reading of the raw JD that may be a false
  positive), kept separate from Open items, and does not block the run. Render
  "none" if empty.
- **Compose QC reversals from `cv_collaboration_log.md`:** for each
  `qc_regression` the architect flagged, name the advisor, the contribution, and
  the QC constraint that forced the reversal, so the user sees any stakeholder win
  QC undid and why. Render "none" if empty.
- Present the summary block:

  ```
  Targeted CV: <role> at <company>
  CV content: <path>
  Estimated length: <N> pages (guard estimate; confirmed at the render stage)
  QC: <PASS | provisional - see open items>
  Open items (or "none"):
    - <advisor>: <ask> | not fully integrated because: <architect's reason>
    - QC (if provisional): <finding>
  QC reversals (or "none"):
    - <advisor>'s <contribution> reversed by a QC fix: <constraint>
  Possible missed requirements (or "none"):
    - The JD appears to emphasize <X>; it is not in your requirements or gap
      analysis, so the pipeline never evaluated it. Address upstream if it is real.
  Notes: <best-practices staleness warning and/or deferred-axis note, if any>
  ```

- State the next step: the formatted .docx is produced by the separate render
  skill (cv-render); `cv_content.md` is its sole input. The user reviews
  `cv_content.md` (the citation comments are invisible in any render).
- This skill produces the CV; it does not make a pursue/no-pursue decision (that
  was gap-analysis). End the run.

## Phase routing on failure

Consumed by Phase 3 (stakeholder loop) and Phase 4 (QC). Route back, fix, re-run
forward. Phase 3 and Phase 4 each cap at 3 iterations; on a bounded-loop failure
the artifact ships provisional with the remaining items surfaced at handoff.

| Finding type | Route back to |
|---|---|
| Mechanical QC failure: missing citation, multi-sentence bullet, bullet over line limit, section order / banding invalid, competency count out of range, em dash present, AI-tell phrasing flagged | Phase 4 fix loop (cv-architect revise) |
| Cited id not found in inventory / narratives (fabricated id) | Phase 4 fix loop (cv-architect revise) |
| Employer/role misattribution: a role block cites entries from more employers than it has role titles (C5) | Phase 4 fix loop (cv-architect revise) |
| Length guard: estimated pages over the level ceiling | Phase 4 fix loop (cv-architect trim) |
| Invalid CR-NNN on a within-role subheading | Phase 4 fix loop (cv-architect revise) |
| Semantic-traceability finding: cited entry does not support its claim, overstatement beyond source, arc bullet exceeds its cited union, adjacency translation fabricates the domain | Phase 4 fix loop (cv-architect revise) |
| Acronym-expansion, summary-support, or judgment-AI-tell finding | Phase 4 fix loop (cv-architect revise) |
| Unresolved material stakeholder contribution | Phase 3 collaboration loop (cv-architect integrate) |
| Hiring-manager suspected extraction miss (a critical JD element absent from both the extracted requirements and the gap analysis) | Surface at handoff as an advisory note (not fixable in this skill; the user decides whether to address it upstream) |
| `cv_qc.py` non-zero exit (script error) | Halt per `global-rules.md`; do not loop |
| Required upstream artifact missing (research / retrieval / gap_analysis) | Resume-check halt; direct the user to the missing upstream skill |
