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

Draft the message under the rules in `templates/followup.md`, which is the sole
structure and drafting authority (read it; do not reproduce its rules here).
Present the draft, one decision per turn, and revise until the user approves.

## Phase 3: write + session log

1. If a followup artifact for this round already exists with `sent:` set to a
   date (already sent), STOP and confirm before overwriting; re-drafting a sent
   message discards the record of what was sent. On approval, copy
   `templates/followup.md` to
   `<app folder>/followup_<stage_snake_case>_<interview_date>.md`, fill the
   frontmatter (`sent: pending`) and the body.
2. Keep the session log current. Touch only this round's stage section, never
   rewrite the file. The section's field shape is defined by the
   `## Interview section` and `## Interview field notes` blocks of
   `templates/session_log.md` (the single authority; read it, do not reproduce it
   from memory).
   - If `## Interview: <stage>` already exists (a prep run created it): add a
     `Follow-up: pending` line, update `Outcome:` if the user reports the round's
     result, and set `Status: held`.
   - If it is missing (the round ran with no prep run), append a new
     `## Interview: <stage>` section in that field shape, with Prep date / Prep
     artifact / Research added marked `n/a`. Because follow-up only runs after a
     round happened, set `Status: held`, an explicit `Outcome:` (the reported
     result, or `pending` if none yet), and a `Follow-up: pending` line. Leaving
     `Status` at `scheduled` would make `close-application` later flag a round
     that happened as one that never did.
   - Reconcile the scheduling fields against the notes round, EVERY run, not only
     when creating the section. The session log is the one home for this metadata
     and a rescheduled round may never have had a lifecycle run. Read the round's
     `- Date / Time:` (split its packed `YYYY-MM-DD HH:MM tz` into date and time
     before comparing), `- Duration:`, `- Medium:` and `- Schedule changes:` lines,
     and if any disagree with the session log's `Interview date:` / `Time:` /
     `Duration:` / `Medium:` / `Schedule history:` fields, SHOW the user both
     versions and confirm before writing. `Interview date:` is a bare
     `YYYY-MM-DD`: the date the round was actually held.

## Phase 4: close

The user sends, then reports back. On confirmation, set `sent` to the send date
in the artifact and complete the session-log `Follow-up:` line (set it to
`sent <YYYY-MM-DD> (<channel>)`). Plain-English
handoff: where the artifact is, and that the next round (hiring manager) uses
the `preparation-interview` skill.
