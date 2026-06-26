---
name: followup
description: Draft a post-interview follow-up message for one application round from the round's debrief in interview_notes.md, write it as a followup artifact, and keep the session log current (creating the round's stage section if a prep run never made one). The skill drafts; the user sends and reports back; the skill records the send. Run after an interview round, once the debrief is filled in.
---

# followup

Post-interview follow-up for one application round. Reads the round's debrief
from `interview_notes.md`, drafts a short follow-up message, writes it as a
followup artifact, and keeps the session log current. The skill drafts; the
user sends (email or LinkedIn) and reports back; the skill records the send.

## Interaction contract

- One item per turn: one question, one draft decision. Never bundle.
- Plain English.
- Confirm-not-trust: any fact pulled from the notes, prep, session log, or
  positioning is SHOWN for confirmation before it enters the message, never
  silently reused.
- Nothing is written to the artifact before the user approves the draft. The
  skill NEVER writes into `interview_notes.md` (the user's hand-written note
  surface); if the user recalls a thread the notes missed, confirm it, use it,
  and suggest they add it to General Notes themselves.

## Inputs

- `interview_notes.md`: the round section is primary (questions asked + answers
  captured, General Notes, Round Debrief). The debrief's "rough patches to
  address in follow-up" field is the prompt for the message's substantive beat.
- `interview_prep.md` and `session_log.md`: context and stage facts.
- `personal/profile/positioning.md`: the conviction line.

## Phase 1: intake

1. Identify the application folder and the round (stage) to follow up; ask if
   not given. If `interview_notes.md` carries more than one round, confirm which.
2. Read the inputs. Confirm with the user: the recipient (name + title, from the
   round's interviewer block) and the channel (email or LinkedIn). Channel sets
   length (email about three short paragraphs; LinkedIn about half).

## Phase 2: draft

Draft the message under the rules in `templates/followup.md` (the structure and
drafting authority). Present it, one decision per turn, and revise until the
user approves. Hold to: short; one substantive beat sourced from the debrief
that shows the candidate already doing the role's thinking; one forwardable
conviction line from positioning, a flat positive that explains why this role;
trace every "as we discussed" to the notes; echo the interviewer's phrases where
supplied; no product/tool/fact from model memory; no overstatement (initiative
claims must be literally true); no "not X, it's Y"; no em dashes.

## Phase 3: write + session log

1. On approval, copy `templates/followup.md` to
   `<app folder>/followup_<stage_snake_case>_<interview_date>.md`, fill the
   frontmatter (`sent: pending`) and the body.
2. Keep the session log current. Touch only this round's stage section, never
   rewrite the file.
   - If `## Interview: <stage>` already exists (a prep run created it), add a
     `Follow-up:` line to it and update `Outcome:` if the user reports the
     round's result.
   - If it is missing (the round ran with no prep run), append a new
     `## Interview: <stage>` section in the same field shape the
     preparation-screen skill uses (Prep date / Prep artifact / Research added
     marked `n/a`; Interview date from the notes logistics; Outcome; Follow-up).

## Phase 4: close

The user sends, then reports back. On confirmation, set `sent` to the send date
in the artifact and complete the session-log `Follow-up:` line. Plain-English
handoff: where the artifact is, and that the next round (hiring manager) uses
the `preparation-interview` skill.
