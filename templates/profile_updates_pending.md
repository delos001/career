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
calling skill passes per capture.

## Skeleton (initial empty file)

```
# Profile Updates Pending

New information about the candidate raised during gap analysis or interview
prep, awaiting processing into inventory / narratives / positioning by the
profile-update skill.

## Entries

_(none)_
```

## Per-entry schema

Each capture appends one entry under `## Entries`. One shape, whatever surfaced
the fact:

```
### PU-{NNN} - {short_label}

- **Captured:** {YYYY-MM-DD}
- **From:** {APP-NNN} ({company} | {role})
- **Requirement:** {CR-NNN} - {requirement_text_short}, or 'n/a' with a short reason
- **Role context:** Industry={industry}, Specialty={specialty}, Orientation={orientation}, Level={level}, Work-state={work_state}
- **Content:** {2-3 sentences max - what the user surfaced, in their own terms}
- **Status:** pending
```

When the profile-update skill processes an entry it rewrites the Status line and
appends one Processed line:

```
- **Status:** processed
- **Processed:** {YYYY-MM-DD} into {comma-separated target IDs, or 'no change'}
```

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
  that a `Closure ref: PU-NNN` in `gap_analysis.md` resolves to a complete
  staging entry.
- **Role context** - the five axis values from that role-intake's classification.
  These are CONTEXT for the processing skill's tagging judgment, not the only
  tags the processed inventory entry will carry.
- **Content** - the surfaced information itself, captured concisely. The
  processing skill rewrites this to the target doc's voice and conventions; it
  is not copied verbatim.
- **Status** - `pending` on append. Updated to `processed` by the profile-update
  skill when the entry has been written into the target doc(s). Processed
  entries are retained, not removed: the entry plus its `Processed:` line is the
  audit trail from a surfaced fact to the profile IDs that now carry it.
- **Processed** - written by the profile-update skill alongside the status flip.
  Carries the run date and the target IDs the content landed in (`EX-210`,
  `EX-049, EX-058`, `ST-011`). `no change` records a deliberate decision that
  the entry needed no profile edit, which is a valid outcome and still closes
  the entry.
