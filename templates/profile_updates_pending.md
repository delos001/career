# Profile Updates Pending - template

**Used by:** gap-analysis (appends entries during the Phase 4 closure loop).
**Processed by:** the separate profile-update skill (TBD), which reads entries
and writes them into `inventory.md` / `narratives.md` / `positioning.md`.

Lives at `personal/profile/profile_updates_pending.md`. **Cross-application** -
one file accumulates entries across all gap-analysis runs until the
profile-update skill processes them.

Entries are **context for correct downstream insertion**, not copy-paste content.
The processing skill adapts each entry to the target doc's conventions (entry
headers, ID schemes, tag fields, length norms). Keep content concise. See
[[respect-profile-doc-conventions]].

`scripts/staging_append.py` renders new entries from structured inputs the
gap-analysis skill passes per closure.

## Skeleton (initial empty file)

```
# Profile Updates Pending

New information raised during gap-analysis closure loops, awaiting processing
into inventory / narratives / positioning by the profile-update skill.

## Entries

_(none)_
```

## Per-entry schema

Each closure-via-user-input appends one entry under `## Entries`:

```
### PU-{NNN} - {short_label}

- **Captured:** {YYYY-MM-DD}
- **From:** {APP-NNN} ({company} | {role})
- **Closed requirement:** {CR-NNN} - {requirement_text_short}
- **Role context:** Industry={industry}, Specialty={specialty}, Orientation={orientation}, Level={level}, Work-state={work_state}
- **Content:** {2-3 sentences max - what the user surfaced, in their own terms}
- **Status:** pending
```

## Field notes

- **PU-NNN** - global sequential staging counter, derived by `staging_append.py`
  scanning existing entry IDs in the file. Independent of APP-NNN.
- **short_label** - 3-5 word descriptor of the surfaced information (e.g.,
  `Healthcare regulatory work at Acme`). Used for skim/navigation.
- **From** - APP-NNN + the company/role pair, so the processing skill can
  cross-reference back to the originating application if context is needed.
- **Closed requirement** - the CR-NNN identifier from that gap-analysis run +
  the requirement text in short form. Anchors the entry's provenance.
- **Role context** - the five axis values from that role-intake's classification.
  These are CONTEXT for the processing skill's tagging judgment, not the only
  tags the processed inventory entry will carry.
- **Content** - the surfaced information itself, captured concisely. The
  processing skill rewrites this to the target doc's voice and conventions; it
  is not copied verbatim.
- **Status** - `pending` on append. Updated to `processed` by the profile-update
  skill when the entry has been written into the target doc(s). Removal vs
  retention of processed entries is a profile-update-skill decision.
