# Interview Notes - template

**Used by:** interview-notes (creates and appends). The follow-up skill reads
round sections after each interview.

One per evaluated job, written to
`personal/applications/<SLUG>_APP-NNN_YYYY-MM/interview_notes.md`.

An **append-and-amend document**: `scripts/notes_assemble.py init` renders the
file shell once; `add-round` appends one round section per interview, rendered
from the blocks below. Hand-written notes fill the scaffold between scaffold
runs; nothing the script does overwrites them. Section identity is the round
heading (`## <N>. <stage> | <YYYY-MM-DD>`), where `N` is the round's append
order. Identity for duplicate-detection and amend is stage + date; the number is
a cosmetic ordinal, ignored when matching. The skill amends an existing section
directly instead of appending a duplicate.

Stage labels are free text; the standard vocabulary (offered as defaults at
intake) is: Recruiter Screen, Hiring Manager, Panel, Peer / Team, Executive,
Final / Offer Discussion. Where a stage has a session-log counterpart, the
label matches the session-log stage name.

## File shell

```
---
application: {{app_id}}
company: {{company}}
role_title: {{role}}
created: {{created}}
---

# Interview Notes: {{company}} | {{role}}
```

## Round block

One appended per `add-round` run. `{{number}}` is the round's ordinal (its
append order in the file), computed by the script; it is not a payload field.
`{{cue_card_block}}` renders the live cue-card the candidate reads first: bullets
the interview-notes skill composes from `interview_prep.md` (opener, lead framing,
top concerns), `_(none)_` when no prep exists. `{{questions_block}}` renders one
checkbox bullet per planned question, each followed by an indented answer line for
typing the response directly during the call (`- [ ] <question>` then
`    - Answer: `; `_(none)_` when empty); check a question off when asked, so
unchecked questions are the carryover candidates for the next round.
`{{interviewer_blocks}}` renders one interviewer block per attendee, in
payload order.

```
## {{number}}. {{stage}} | {{date}}

- Date / Time: {{datetime}}
- Schedule changes:
- Duration:
- Medium: {{medium}}
- Format: {{format}}

### Cue-card

{{cue_card_block}}

### Questions to Ask

{{questions_block}}

{{interviewer_blocks}}

### General Notes

-

### Round Debrief

- Impression:
- Interest level:
- Gate: opened? when / what opened it:
- Format dynamic: scripted | conversational | shifted (when):
- Rough patches to address in follow-up:
- Personal connection threads:
- Next steps communicated:
- Aware I am pursuing other roles:
```

## Interviewer block

`{{interviewer}}` is `<name> (<title>)`, or `<name>` when the title is
unknown; `TBD` when attendees are not yet known. The bullet is the note space
for what that person says.

```
### Notes: {{interviewer}}

-
```

## Field notes

- **{{datetime}}** - `YYYY-MM-DD HH:MM <tz>` as known at scaffold time; the
  heading `{{date}}` is the identity date (`YYYY-MM-DD`).
- **Schedule changes** - optional, hand-filled. If the round was rescheduled,
  note the original and new date(s) here (e.g. `originally 2026-07-02; moved to
  2026-07-07`); left blank when nothing moved. The heading keeps its identity
  date; this line carries the reschedule history.
- **Duration** - optional, hand-filled. Planned vs actual length and any
  over/underrun (e.g. `planned 25 min; ran ~15 over`); left blank unless
  noteworthy. An over/underrun is ambiguous on its own; note the cause (their
  engagement extending it vs. my question backlog cramming the end), which is
  what the debrief scores.
- **{{medium}}** - phone | video | in-person.
- **{{format}}** - single | panel | sequential.
- **{{number}}** - the round's ordinal, the count of existing round headings + 1
  at append time; assigned once and never renumbered (a cancelled round keeps
  its number).
- **Status suffix** - a round heading may carry a trailing bracketed status,
  `## <N>. <stage> | <date> [<STATUS>]`, so a dead or unusual round is visible
  in outline view. `interview_lifecycle.py cancel` writes `[CANCELLED <date>]`
  automatically; other statuses (e.g. `[NO-SHOW]`, `[DECLINED]`) may be added by
  hand.
- **Round Debrief** - filled by hand after the round; consumed by the
  follow-up skill. Interest level is free text: a word or a fuller note; it is
  often more nuanced than a simple label.
