---
name: preparation-interview
description: Prepare the candidate for a post-screen interview (hiring manager, peer/team, or executive). Maintains ONE cumulative interview_prep.md per application - a shared main body refined across interviews plus a thin per-interview Appendix block - and projects a live cue-card into interview_notes.md. Prompts audience + format at intake and reads the matching rules/interview-types file. QC is a deterministic script plus a judgment subagent (qc-preparation-interview). Run after a post-screen interview is scheduled. Recruiter screens are the separate preparation-screen skill; building a presentation deliverable is the separate presentation skill.
---

# preparation-interview

Prepare the candidate for one post-screen interview: hiring manager, peer/team,
or executive. The output artifact is `interview_prep.md` in the application
folder, created from `templates/interview_prep.md` (the structure authority).

Recruiter/phone screens are the separate `preparation-screen` skill. Both skills
share the SAME `interview_prep.md`; this skill owns the cumulative architecture
below and reconciles a screen-era doc into it. Building a presentation
deliverable is a separate skill; here a presentation is only a flag in the
Appendix.

## Interaction contract (non-negotiable)

- One item per turn: one research gap, one section, one question. State counts
  up front, then wait. Never bundle.
- Plain English at every step, including QC and decision points. No internal
  check IDs or jargon to the user.
- Scannable: short bullets and key words, never long paragraphs. The artifact
  is used live; the user scans keywords and speaks from them.
- Artifact formatting (full rules in the template's Conventions comment; the QC
  enforcement split, script vs subagent, is in Phase 5): no em dashes (commas or hyphens); headings are
  short labels from the template's allowed set only, never coaching / citations /
  sentences in a heading, never a company, product, or person name; `###`
  sub-headings are the navigation layer and bold labels break content up within
  one, so a section needing more internal shape gets a bold label and never a new
  sub-heading; keep an `{optional}` sub-heading when it carries material, drop it
  when the run left it empty, never rename or delete one that has content; a
  genuinely homeless, role-agnostic topic is a template gap, so surface the
  proposal with the material that forced it, add it to the template tagged
  `{optional}` on approval, and only then use it, since an artifact-local heading
  is never invented; one weight-bearing element per bullet (expand discrete-
  element series to sub-bullets); no bold connector tokens (**plus** / **and**)
  welding list items; no build/process narration in the body; no redundant
  restatement (single-home, cross-refs link by label); frontmatter is the first
  line, so strip every template comment from the copy.
- Confirm-not-trust, two layers: (a) every element pulled from another artifact
  or a profile default is SHOWN with an "is this still accurate?" check before
  it enters the doc; (b) every screen- or JD-sourced claim about the role/team/
  interviewer is written as UNCONFIRMED and, if decision-critical, generates a
  confirmation question (see Phase 3). Second-hand intel is never stated as fact.
- Nothing enters the artifact before the user approves that section. Research
  ledger appends and the session-log entry do not need per-write approval.

## Doc architecture (what this skill maintains)

ONE cumulative `interview_prep.md` per application:

- MAIN BODY = shared, refined cumulatively, never duplicated per interview:
  Company & Industry, The Role, Positioning & Approach, Fit and Gaps,
  Anticipated Questions, Question Bank, Concerns to Resolve, Comp / Logistics.
- APPENDIX = one thin block per interview: purpose + interviewer(s) + emphasis
  (which Question Bank items to prioritize, which Concerns to raise here, what
  to lead with) + presentation flag if any. Pointers into the main body, never
  copies.
- The interview's live cue-card is projected from its Appendix block into
  `interview_notes.md`.

## Inputs

From the application folder: `research.md`, `gap_analysis.md`, `session_log.md`,
`jd.md`, `cv_content.md`, the Signature Theme table in `retrieval.md` (that
table only), and the existing `interview_prep.md` / `interview_notes.md` if
present.
From `personal/profile/`: `positioning.md`, `user-info.md`, `inventory.md`
Employment & Role History section (authoritative role records; verify any
date/scope/count before writing it).
Rule file: `rules/interview-types/<audience>.md` for the prompted audience; it
sets this interview's emphasis and any audience-specific research gaps.

## Phase 0: mode

- If `interview_prep.md` exists: EXTEND the cumulative doc. Refresh main-body
  sections only where something changed, then add-or-update this interview's
  Appendix block. If the existing doc is screen-era structure (no main-body /
  Appendix split), first reconcile it into this architecture, folding the
  screen's specifics into a `Recruiter Screen` Appendix block.
- Else: CREATE from `templates/interview_prep.md` (main body + first Appendix
  block). Remove template comments from the copy.

## Phase 1: intake (pin the interview)

One question per turn:

- Audience (rule-file key -> stage label): hiring-manager -> Hiring Manager,
  peer-team -> Peer / Team, executive -> Executive. The key selects the
  rules/interview-types file; the stage label is what goes in every heading
  (Appendix, session log, notes round), matching interview_lifecycle's --stage.
- Format: single | panel | presentation | technical (combine as needed; panel
  drives per-interviewer blocks; presentation sets the Appendix flag).
- Purpose/objective: use it if the user has one; otherwise run the audience's
  standard prep. Never narrow to a stated purpose unless the user is certain
  it is the only topic - the stated purpose can be wrong or change (prepare
  for flex).
- Interviewer(s): name + title each (empty allowed).
- Logistics: date, time+tz, medium. These go to the session log, not the
  frontmatter.

Load the audience rule file, then read the inputs.

## Phase 2: research gap pass

Evaluate by PURPOSE-FIT, never by artifact age. Enumerate gaps, state the
count, present one per turn (what it is, why this audience needs it, expected
confidence, honest value), user approves or skips.

- Per-interviewer intel is the primary gap: one `prep-research` invocation per
  interviewer. Degrade gracefully when a footprint is empty - output
  "confirm live" handling plus an opener question, do not pad guesses.
- Plus any audience-specific gaps the rule file names.
- All research via `prep-research`, one target per invocation, foreground.
  Append to `research.md` dated `**Added:** YYYY-MM-DD (interview prep,
  <audience>)` with Summary / Key facts / Sources; relay with hedges intact.

## Phase 3: main body (build or refine)

Build missing main-body sections; refine existing ones with what this interview
added (cumulative). One section per turn, present it, write on approval.
Scannable bullets. Separate substance from coaching (coaching in [brackets];
Cue / Avoid / If probed keep their labels).

- The Role, Concerns, and positioning are SHARED, not per-interview; refine in
  place, do not copy into the Appendix.
- Inference-triggers-a-question: any decision-critical item that is inferred or
  unconfirmed (esp. The Role decision-rights map, stakeholder web) is framed as a
  flagged hypothesis, never stated as fact, and gets a matching confirmation
  question in the Question Bank that REFERENCES the map, not re-lists it. Governor:
  decision-critical only, or the bank bloats.
- Question Bank is shared and reusable (the user may re-ask across interviews);
  order it in topical clusters, insert a later interview's new question into its
  cluster via a sub-label (Q1b, Q4a) rather than appending, and never renumber. Do
  not tailor phrasing per interview here - that is the Appendix's job.
- No build/process narration in the artifact, and no redundant restatement: each
  content unit has one home, other sections point by label; the walk-out crux lives
  in Concerns, not The Role.
- Claims trace to the profile; never overstate beyond `gap_analysis.md` /
  inventory. Career-span numbers from the profile, never the JD's minimum bar.

## Phase 4: appendix block + cue-card

1. Generate/refresh this interview's Appendix block: purpose; interviewer(s)
   with researched intel and confirm-live handling; emphasis = the Question
   Bank items to prioritize, the Concerns to raise here, the lead framing;
   presentation flag if the format includes one (the presentation skill is not
   yet built; note the flag and prepare the deliverable manually). Pointers into
   the main body, never copies. Prep-forward only: no
   outcomes, no asked/debrief content, and no scheduling metadata at all (no
   date, time, or event status, including in the block heading); those live in
   session_log.md and interview_notes.md. The heading is
   `## <Stage label> - <Interviewer(s)>` (the Title-Case stage label, e.g.
   `## Hiring Manager - Joanne Bugembe`), nothing more.
2. The live cue-card lives in `interview_notes.md`, composed and written by the
   `interview-notes` skill (the sole writer of that file) from this round's
   Appendix Emphasis and the main body. Make the Appendix Emphasis name the
   opener, what to lead with, the top Concerns, and which Question Bank items to
   prioritize, so interview-notes can pull their full text into the round's
   Cue-card and Questions to Ask. Write the prioritized list in the order the
   questions should be ASKED, not by label number, because that sequence is the
   only place the asking order is recorded and the projection carries it
   verbatim: the checklist lands in that order, priority questions above
   non-priority ones, so it never contradicts the cue-card sitting above it. If
   the notes file lacks this interview's section, run the `interview-notes` flow
   to scaffold it.

## Phase 5: session log, then QC

1. Append (or update, in EXTEND mode) the session-log section before QC, in the
   field shape defined by the `## Interview section` and `## Interview field notes`
   blocks of `templates/session_log.md` (the single authority; read it, do not
   reproduce it from memory). `Interview date:` is a bare `YYYY-MM-DD`; time, duration, medium,
   and interviewers each have their own field. `Status: scheduled`, `Outcome: pending`.
   This section is the ONE home for the interview's scheduling metadata; the prep
   doc records none of it.

2. QC, an internal loop (no check-by-check narration): a deterministic script
   (`scripts/prep_interview_qc.py`) plus the judgment subagent
   `qc-preparation-interview`. The script owns structure and format (frontmatter,
   headings and their allow-set, no em dashes / bold connectors / coaching or
   citations in headings), the Appendix (present, schema-only fields, no date or
   event-status token in headings), Question-Bank cross-ref resolution, and the
   research-ledger and session-log interview fields; it also emits advisory
   warnings (non-blocking) for bullet-packing and build/process narration. The
   subagent owns what a script cannot judge: that each citation supports its
   claim, that no main-body content is copied into an Appendix block, that the
   body single-homes each point (no redundant restatement; cross-refs link by
   label), and that the body carries no build/process narration.
3. Fix and re-run. Cap 3 iterations; else ship provisional, summarize the
   residual in plain English, log it to `design/build_issues.md`.

## Phase 6: close out

- Lifecycle (separate op, only when an interview moves or dies). Run
  `scripts/interview_lifecycle.py`, which updates `session_log.md` (the record)
  and `interview_notes.md` (the capture surface). It never touches
  `interview_prep.md`: prep content does not change when a date moves.

  ```
  python <repo>/scripts/interview_lifecycle.py reschedule --folder <abs app folder>
      --stage "<stage label>" --new-datetime "<YYYY-MM-DD HH:MM tz>" [--date <YYYY-MM-DD>] [--reason "<why>"]
  python <repo>/scripts/interview_lifecycle.py cancel --folder <abs app folder>
      --stage "<stage label>" [--date <YYYY-MM-DD>] [--reason "<why>"]
  ```

  `--stage` is the label as it appears in the headings, e.g. "Hiring Manager".
  `--date` is only needed when two notes rounds share a stage label.

  Reschedule rewrites the session log's `Interview date:` / `Time:` / `Schedule
  history:` / `Status:` fields (and clears a prior cancelled `Outcome:` back to
  pending) and appends to the notes round's `Schedule changes:` line.
  Cancel sets the session log's `Status:` and `Outcome:` and tags the notes round
  heading `[CANCELLED <date>]`. The notes round heading's date is that section's
  identity and is never rewritten; a move is recorded, not overwritten. Blocks are
  tagged, never deleted.

  Running the op is optional for a reschedule (the `followup` skill reconciles the
  date from the notes round's `Schedule changes:` line) but is the accurate capture
  path for a cancel, which no downstream skill sees. `close-application` verifies
  the record at close-out either way.

  Interviewer-structural changes (single to panel, add/remove a person) are the
  skill plus the `interview-notes` AMEND flow, not this op.
- Staging: new GENERAL (role-independent) candidate facts - list them, ask
  which to stage, append approved to `profile_updates_pending.md`.
- Handoff in plain English: where the doc is, read the main body plus this
  interview's Appendix, speak the arcs aloud.
