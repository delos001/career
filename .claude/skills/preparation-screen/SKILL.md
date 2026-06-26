---
name: preparation-screen
description: Prepare for a recruiter / phone-screen interview. Reads the application's existing artifacts (research, gap analysis, session log) and the profile, closes purpose-fit research gaps via the prep-research subagent, then drafts interview_prep.md section by section with user approval before every write. QC is a deterministic script (prep_qc.py) plus a judgment subagent (qc-preparation-screen). Run after gap-analysis, when a screen is scheduled. Hiring-manager rounds are the separate preparation-interview skill (not yet built).
---

# preparation-screen

Prepare the candidate for a recruiter or phone-screen interview for one
application. The output artifact is `interview_prep.md` in the application
folder, created from `templates/interview_prep.md` (the structure authority).

## Interaction contract (non-negotiable)

- One item per turn: one research gap, one section draft, one question. Never
  bundle. State counts up front ("4 gaps; here is the first"), then wait.
- Plain English at every step, including QC explanations and decision points.
  No internal check IDs or implementation jargon to the user.
- Concise presentation: short bullets and chunked drafts, never long
  paragraphs. Headings concise.
- Confirm-not-trust: every element pulled from another artifact or a profile
  default (logistics, comp target/floor, defense-layer language, constraint
  answers from gap analysis) is SHOWN to the user with an "is this still
  accurate?" check before it enters the artifact. Never silently reuse.
- Nothing is written to the artifact before the user approves that section's
  content. Research ledger appends and the session log entry do not need
  per-write approval once their step is reached.

## Inputs

From the application folder: `research.md`, `gap_analysis.md`,
`session_log.md`, `jd.md`, `cv_content.md` (the CV the interviewer holds),
and the Signature Theme score table in `retrieval.md` (targeted read of that
table only, never the whole manifest).
From `personal/profile/`: `positioning.md` (all sections; the routing rules
in Phase 3 say where each lands), `user-info.md` (static facts and
dated defaults), `inventory.md` Section 7 (authoritative role records; verify
any date/scope/count claim here before writing it).

## Phase 0: mode

If `interview_prep.md` already exists in the application folder, run in
UPDATE mode: walk the existing sections with the user, confirm or amend each,
refresh research only where the user says something changed, bump
`last_updated`, and add a dated line item to the existing session-log section
rather than a new section. Otherwise run in CREATE mode (phases 1-5).

## Phase 1: intake

Collect the screen facts conversationally (one question per turn): who is
conducting it, when, how long, medium. These go to the session log later, not
into the artifact frontmatter. Then read the inputs above.

## Phase 2: research gap pass

Evaluate existing research by PURPOSE-FIT against live-conversation needs,
never by artifact age. Enumerate the gaps, state the count, then present one
per turn with: what it is, why a screen needs it, expected confidence, and an
honest value ranking. The user approves or skips each.

Standard checklist (plus any role-specific gaps):
1. Compensation calibration (skip if a posted band and user numbers settle it).
2. Interview-process intel.
3. JD internal-reference decode (company shorthand; one per phrase found).
4. Interviewer context.
5. Company mission and core values (normally already captured at role-intake in
   research.md's Company section; add a top-up only if intake predated that
   capture or left them blank). Some employers screen explicitly against their
   values, so this grounds natural values-fit conversation.

ALL research goes through the `prep-research` subagent, one target per
invocation, foreground (background subagents cannot write under `personal/`,
and findings must return before any write). This includes ad-hoc lookups
raised mid-conversation by the user, however small; never answer one with an
inline search. On return, append the findings to `research.md` as a dated
section attributed `**Added:** YYYY-MM-DD (interview prep, phone screen)`
with Summary / Key facts / Sources, then relay them with confidence hedges
intact.

## Phase 3: draft section by section

Create the artifact by copying `templates/interview_prep.md` and filling the
frontmatter (template comments are guidance for drafting; remove them from
the artifact copy). Then draft one section per turn, present it, and write it
only on approval. The template's comments define each section's content rules.

Across every section, separate substance from coaching. Substance is what the
user knows or says; coaching is your interpretive steer on how to weigh or use
it. Classification test: would the user ever say this aloud (substance), or are
you steering them (coaching)? Mark every coaching aside in square brackets per
the template's bracket rule; the named Cue / Avoid / If probed labels are
coaching subtypes that keep their labels.

The rules that need judgment emphasis:

- Orientation: populate only chunks research supports. Capture the company's
  value-positioning axis (products/platform, therapeutic areas, service
  lines), not just the strategic story. The Mission and Values chunk consumes
  the company's mission/values from research.md's Company section (top up via
  the company-values prep-research fallback only if intake left them blank) and
  adds "how to speak to them" hooks tying 1-2 values to the candidate's themes;
  the template comment carries the full rule. Orientation is the reference
  briefing; the deployable "what do you know about us?" answer is a question
  entry that curates its headline facts.
- Fit and Gaps: strengths lead with a memorable bold key phrase; career-span
  numbers come from the profile, never the JD's minimum bar. The top-scored
  Signature Themes from the retrieval theme table contribute their core
  message and proof point, mapped to the requirements they hit. Gap chunks
  cluster by underlying gap, carry their CR numbers, and must jointly cover
  every non-covered requirement in `gap_analysis.md`. Responses never
  overstate beyond the gap analysis notes.
- Questions: generic durable entry names; spoken-cue arcs, not paragraphs to
  memorize; If-probed and Avoid layers on diplomatic answers (pull the
  "layer beneath" from positioning and confirm it with the user); "what are
  you looking for" is drafted fresh for THIS role from positioning plus the
  role context. A generic or other-role-shaped answer reads as "this
  candidate is settling," which is disqualifying.
- Positioning routing (compress to cue level, never import prose verbatim):
  - "Walk me through your background" opens with the identity thesis from
    the Positioning Statement / What Makes Me Unique / Elevator Statement,
    with the Experience Profile selecting which 1-2 role identities lead.
    Chronology is one compressed sweep beat, not a role-by-role tour; the
    interviewer already holds the CV. Land on this role.
  - "Why this company?" draws on Industry Trajectory and Where I Fit,
    matched to the company's strategic thesis from research.
  - A leadership-style or how-would-you-approach entry built from Core
    Philosophy (Orient-Diagnose-Intervene-Stabilize-Scale) is a standard
    optional add; its authority/matrix/hands-on flex line is the defense
    layer for direct-reports probes.
- Compensation: user's numbers (confirm current), scope-conditional stated
  range when the role's level is inferred, market data cited from the
  research ledger.
- Logistics and Availability: conditional facts confirmed this run; static
  facts from user-info.md, shown for confirmation.

## Phase 4: session log, then QC

1. Session log: append the stage section (or a dated line item in UPDATE
   mode) before QC runs, so the QC pass covers it:

   ```
   ## Interview: Screen

   - Prep date: YYYY-MM-DD
   - Prep artifact: <relative path to interview_prep.md>
   - Research added: <prep section names added to research.md>
   - Interview date: <date, duration, interviewer (role)>
   - Outcome: pending
   ```

2. QC, an internal loop; do not stall the user with check-by-check
   narration. Run:
   `python <repo>/scripts/prep_qc.py check --folder <absolute application folder>`
3. Dispatch `qc-preparation-screen` (judgment checks) with the application
   folder and profile folder paths.
4. Fix findings and re-run. Cap at 3 iterations; if findings remain, ship
   provisional, summarize the residual in plain English, and log it to
   `design/build_issues.md`.

## Phase 5: close out

1. Staging: if the prep surfaced new GENERAL facts about the candidate
   (role-independent), list them and ask the user which to stage; append
   approved items to `personal/profile/profile_updates_pending.md` following
   that file's existing entry format. Role-specific answers stay in the
   artifact only.

2. Handoff, in plain English: where the artifact is, what the user should do
   before the call (read it once, speak the arcs aloud), and any provisional
   QC residual.
