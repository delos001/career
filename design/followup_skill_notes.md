# Follow-up Skill Notes: Design Inputs

Design inputs for the future **followup** skill (post-interview follow-up
message). First run executed ad hoc 2026-06-12; worked specimen:
`personal/applications/medable_APP-008_2026-06/followup_recruiter_screen_2026-06-12.md`.

## Scope and trigger

- Run after an interview round, once the user has filled the round's debrief
  in `interview_notes.md`. One follow-up artifact per round.
- The skill drafts; the user sends (email or LinkedIn) and reports back; the
  skill records the send.

## Inputs

- `interview_notes.md`: the round section is the primary source (questions
  asked, answers captured, General Notes, Round Debrief). The debrief's
  "rough patches to address in follow-up" field is a direct prompt for the
  message's substantive beat.
- `interview_prep.md` and `session_log.md`: context and stage facts.
- `positioning.md`: conviction lines for the forwardable sentence.

## Artifact

- Name: `followup_<stage_snake_case>_<YYYY-MM-DD>.md` in the application
  folder (stage label from the interview_notes round heading; date is the
  interview date).
- Frontmatter: `application`, `company`, `stage`, `interview_date`,
  `recipient`, `sent` (pending until the user confirms; then the send date).
- Body: `# Follow-up: <stage> | <date>`, then Subject line, then the letter.

## Drafting rules (learned on the specimen)

- Short. Recruiters skim; three short paragraphs was right for email.
  LinkedIn messages run about half that length; ask the channel before
  drafting.
- One substantive beat that shows the user already doing the role's
  thinking, sourced from the debrief (specimen: 30-60-90 sketching).
- One forwardable conviction line. The real audience may be whoever the
  interviewer reports the conversation to; the conviction explains why this
  role specifically. Pull from positioning, phrased as a flat positive. No
  "not X, it's Y" constructions anywhere (user's standing AI-tell ban for
  written products).
- Trace every "as we discussed" to the notes. If the user recalls a thread
  the notes missed, confirm it with the user, use it, and suggest they add
  it to General Notes themselves (notes content is the user's hand-written
  surface; the skill never writes into it).
- Echo the interviewer's own phrases where the notes or user supply them.
- Never name a product, tool, or fact from model memory; research it or
  leave it generic.
- No overstated claims; initiative claims ("I have been sketching") must be
  literally true per the user.
- Confirm-not-trust and one-decision-per-turn interaction contract, same as
  the prep-family skills.

## Close-out

- On user confirmation of send, set `sent` to the date.
- Candidate addition: a dated follow-up line item in the session log's
  interview stage section (decide at build time).

## Trigger to build

User-committed: next session. Reuses prep-family machinery where it fits
(template-as-structure-authority, QC script + judgment agent if the artifact
grows enough structure to warrant it).
