# Profile Updates Pending - template

**Used by:** gap-analysis (appends entries during the Phase 4 loop) and the prep
skills (facts surfaced during interview preparation).
**Processed by:** the profile-update skill, which reads entries and writes them
into `inventory.md` / `narratives.md` / `positioning.md`.

Lives at `personal/profile/profile_updates_pending.md`. **Cross-application** -
one file accumulates entries across every run until the profile-update skill
processes them.

Entries are **context for correct downstream insertion**, not copy-paste content.
The processing skill adapts each entry to the target doc's conventions (entry
headers, ID schemes, tag fields, length norms). Keep content concise. See
[[respect-profile-doc-conventions]].

`scripts/staging_append.py` renders new entries from structured inputs the
calling skill passes per PU entry.

## Skeleton (initial empty file)

```
# Profile Updates Pending

New information about the candidate raised during gap analysis or interview
prep, awaiting processing into inventory / narratives / positioning by the
profile-update skill.

## Entries

_(none)_

## Migrated

_(none)_
```

## Per-entry schema

Each PU entry appends one entry under `## Entries`. One shape, whatever surfaced
the fact:

```
### PU-{NNN} - {short_label}

- **Captured:** {YYYY-MM-DD}
- **From:** {APP-NNN} ({company} | {role})
- **Requirement:** {CR-NNN} - {requirement_text_short}, or 'n/a' with a short reason
- **Role context:** Industry={industry}, Specialty={specialty}, Orientation={orientation}, Level={level}, Work-state={work_state}
- **Content:** {2-3 sentences max - what the user surfaced, in their own terms}
```

There is no status field on a PU entry. `## Entries` holds what is waiting, and a
PU entry leaves it once it is finished. The inventory is where the information
itself persists, so the PU entry's body is not kept after promotion.

## Migrated section

Every PU entry that leaves `## Entries` is recorded there, one line, permanently:

```
## Migrated

PU-005: EX-229; EX-230; EX-231; EX-049
PU-008: dropped
PU-009: duplicate
```

The left side is the `PU-NNN`. The right side is what became of it, in one of
three forms:

- **Targets** - where the content landed: an inventory entry ID, a narratives or
  positioning entry ID, or a list address (`Technical Experience / Clinical
  Application Systems / Document Management`) for the sections that hold flat
  lists rather than entries. Several targets are separated by `; `, because a
  list address can itself contain a comma.
- **`dropped`** - the user retracted the PU entry; nothing reached the profile.
- **`duplicate`** - the profile already carried the substance accurately, so
  nothing needed writing.

The skill verifies the targets resolve before it moves a PU entry here.

This section is why the file can be a queue without losing anything that
depends on it. Two things read a `PU-NNN` after its PU entry is gone:

- **The ID counter.** `staging_append.py` takes the next `PU-NNN` from the
  highest number in `## Entries` **and** `## Migrated`. Without the migrated
  half the counter walks backwards as PU entries are promoted and reissues a
  number a closed application already cites.
- **Past applications.** A `Closure ref: PU-NNN` written into a
  `gap_analysis.md` is permanent. `gap_qc.py` resolves it against both sections,
  so a promoted PU entry stays traceable to the entry it became.

## Field notes

- **PU-NNN** - global sequential staging counter, derived by `staging_append.py`
  scanning existing entry IDs in the file. Independent of APP-NNN.
- **short_label** - 3-5 word descriptor of the surfaced information (e.g.,
  `Healthcare regulatory work at Acme`). Used for skim/navigation.
- **From** - APP-NNN + the company/role pair, so the processing skill can
  cross-reference back to the originating application if context is needed.
- **Requirement** - the CR-NNN under discussion when the fact surfaced, plus the
  requirement text in short form. Anchors the entry's provenance so whoever
  promotes it weeks later knows what conversation produced it. A general fact
  raised during interview prep carries `n/a` plus a short reason instead.

  The anchor does NOT record whether the fact closed a gap. That is a fact about
  one application, it lives in that application's `gap_analysis.md`, and the
  profile has no use for it: an entry that closed nothing is promoted exactly
  the same way, because it may close a gap on a future application. Closure
  linkage is checked where it belongs, by `gap_qc.py` check G7, which verifies
  that a `Closure ref: PU-NNN` in `gap_analysis.md` resolves - to a complete
  PU entry in `## Entries` while it waits, or to its `## Migrated` line once it
  has been promoted.
- **Role context** - the five axis values from that role-intake's classification.
  These are CONTEXT for the processing skill's tagging judgment, not the only
  tags the processed inventory entry will carry.
- **Content** - the surfaced information itself, captured concisely. The
  processing skill rewrites this to the target doc's voice and conventions; it
  is not copied verbatim.
- **Removal** - two commands take a PU entry out of `## Entries`, and both record
  it under `## Migrated`. `profile_update.py close` is the promoted path: it
  verifies the targets the content landed in, then moves the PU entry, recording
  those targets. `profile_update.py drop` is the retraction path, for a PU entry
  the user decides should not go into the profile after all; it is their call,
  never the skill's, and it records `dropped`. Closing with
  `--targets duplicate` is a third finish: the profile already carried the
  content accurately, so nothing was written and the PU entry still leaves.
