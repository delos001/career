# Profile Updates Pending - template

**Used by:** gap-analysis (appends items during the Phase 4 loop) and the prep
skills (facts surfaced during interview preparation).
**Processed by:** the profile-update skill, which writes each item into
`inventory.md` and removes it once the written entry passes review.

Lives at `personal/profile/profile_updates_pending.md`. **Cross-application** -
one file accumulates items across every run until the profile-update skill
processes them.

How a capture is written is governed by `rules/profile/staging-writing.md`.
`scripts/staging_append.py` is the only writer; it renders each item from the
caller's capture file and refuses a capture with a field missing.

## Skeleton (initial empty file)

```
# Profile Updates Pending

New information about the candidate raised during gap analysis or interview
prep, waiting to be written into the profile by the profile-update skill.

## Entries

_(none)_
```

## Per-entry schema

```
### {label}

- **Captured:** {YYYY-MM-DD}
- **From:** {APP-NNN} ({company} | {role})
- **Requirement:** {CR-NNN} - {requirement_text_short}, or n/a ({reason})
- **Role context:** Industry={industry}, Specialty={specialty}, Orientation={orientation}, Level={level}, Work-state={work_state}
- **Work role:** {RL-NNN}, or new: {employer}, {title}, or n/a ({reason})
- **Did:** {what the candidate did}
- **Others did:** {what others did, or none}
- **Outcome:** {the outcome the candidate stated, or none stated}
- **Limits:** {framing limits and uncertainty, or none}
```

## Field notes

- **label** - 3-5 word descriptor. It is the item's handle: `show` and
  `remove` find the item by it, so it is unique within the queue.
- **Captured, From, Requirement, Role context** - written by the script.
  `From` and `Role context` describe the job being applied for, not the job
  where the work happened. `Requirement` is where the fact surfaced; a CV that
  uses the fact before it reaches the inventory cites it as `GAP CR-NNN`.
- **Work role, Did, Others did, Outcome, Limits** - the capture, passed in the
  capture file. Every field is required; the "none" forms are explicit answers,
  never blanks.
- **Removal** - `profile_update.py remove` deletes an item after its written
  entry passes review, or when it needed no write or was retracted. Nothing
  records where an item went: the profile is the source.
