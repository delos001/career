---
name: interview-notes
description: Scaffold the note-taking file for an upcoming interview round. Creates or extends interview_notes.md in the application folder - one section per round with logistics, planned questions, a note space per interviewer, and a debrief skeleton - so notes can be typed straight in during the call. Collects round facts conversationally, confirming against session_log.md and interview_prep.md instead of re-asking. Run before each interview, with or without a prep run; the artifact feeds the downstream follow-up skill.
---

# interview-notes

Scaffold one round's note-taking section in `interview_notes.md` in the
application folder. The template (`templates/interview_notes.md`) is the
structure authority; `scripts/notes_assemble.py` renders it. The file is the
user's live note surface during the interview, so this skill only scaffolds;
it never writes into note spaces.

## Interaction contract

- One question per turn; plain English; concise.
- Confirm-not-trust: any fact pulled from session_log.md, interview_prep.md,
  or an earlier round section is SHOWN for confirmation, never silently
  reused.

## Phase 1: intake

1. Identify the application folder (ask if not given).
2. If `interview_notes.md` does not exist, create it:
   `python <repo>/scripts/notes_assemble.py init --folder <absolute app folder> --app-id APP-NNN --company <name> --role <title>`
   (app id, company, role from the session log, confirmed with the user).
3. Collect the round facts, one per turn, pre-filling from session_log.md or
   interview_prep.md where they exist:
   - Stage label. Offer the standard vocabulary as defaults: Recruiter
     Screen, Hiring Manager, Panel, Peer / Team, Executive, Final / Offer
     Discussion. Free text allowed. Where a session-log stage section exists
     for this round, the label matches its stage name.
   - Date, time (with timezone), medium (phone | video | in-person), format
     (single | panel | sequential).
   - Interviewers: name and title each; an empty list is allowed (renders a
     TBD note block).
4. If a section headed `## <N>. <stage> | <date>` already exists (match on
   stage + date; the leading number is a cosmetic ordinal), switch to AMEND:
   walk that section's logistics, interviewer blocks, and questions with the
   user and edit it directly; do not run add-round. Never touch hand-written
   note content while amending.

## Phase 2: questions

Build the planned-questions list from three tiers, presenting candidates and
letting the user pick, edit, add, or skip (an empty list is allowed):

1. The round's Appendix block in interview_prep.md names which Question Bank
   items to prioritize ('Prioritize from Question Bank: ...'); pull those items'
   full text from the shared Question Bank. If no Appendix block or prep exists
   yet, offer the whole Question Bank.
2. Carryover: unchecked questions from earlier round sections of this file, and
   any other Question Bank item (the bank is shared and reusable; the user may
   deliberately re-ask one to compare answers across rounds).
3. User-supplied additions.

Selected questions are copied as full text (the file is the live surface
during the call; no pointers to other documents).

## Phase 3: scaffold

1. Write the payload to `<app folder>/scratch/notes_round_payload.json`:
   `{"stage", "date" (YYYY-MM-DD), "datetime", "medium", "format",
   "interviewers": [{"name", "title"}], "questions": [..]}`.
2. Run:
   `python <repo>/scripts/notes_assemble.py add-round --folder <absolute app folder> --payload <absolute payload path>`
   The script appends the section, assigning the round number automatically
   from append order, and deletes the payload on success; on failure it leaves
   the payload for diagnosis. It refuses duplicate stage + date headings (the
   number and any status suffix are ignored when matching); that case should
   have been caught in Phase 1.
3. Show the user the appended section.

## Close

Plain English: where the file is, how to use it (jot anchor phrases under
each interviewer during the call, check questions off as asked, fill the
debrief right after the round), and run the follow-up skill after the
interview.
