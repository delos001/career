# Interview Notes - template

**Used by:** interview-notes (creates and appends). The follow-up skill reads
round sections after each interview.

One per evaluated job, written to
`personal/applications/<SLUG>_APP-NNN_YYYY-MM/interview_notes.md`.

An **append-and-amend document**: `scripts/notes_assemble.py init` renders the
file shell once; `add-round` appends one round section per interview, rendered
from the blocks below. Hand-written notes fill the scaffold between scaffold
runs; nothing the script does overwrites them. Section identity is the round
heading (`## <stage> | <YYYY-MM-DD>`); the skill amends an existing section
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

One appended per `add-round` run. `{{questions_block}}` renders one checkbox
bullet per planned question, each followed by an indented answer line for
typing the response directly during the call (`- [ ] <question>` then
`    - Answer: `; `_(none)_` when empty); check a question off when asked, so
unchecked questions are the carryover candidates for the next round.
`{{interviewer_blocks}}` renders one interviewer block per attendee, in
payload order.

```
## {{stage}} | {{date}}

- Date / Time: {{datetime}}
- Medium: {{medium}}
- Format: {{format}}

### Questions to Ask

{{questions_block}}

{{interviewer_blocks}}

### General Notes

-

### Round Debrief

- Impression:
- Interest level:
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
- **{{medium}}** - phone | video | in-person.
- **{{format}}** - single | panel | sequential.
- **Round Debrief** - filled by hand after the round; consumed by the
  follow-up skill. Interest level convention: Strong | Uncertain but
  continuing | Undecided.
