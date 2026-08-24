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

Each capture appends one entry under `## Entries`. Two kinds, differing only in
the requirement line:

**Closure** - the user's input fully closed a gap during the Phase 4 loop.

```
### PU-{NNN} - {short_label}

- **Captured:** {YYYY-MM-DD}
- **From:** {APP-NNN} ({company} | {role})
- **Closed requirement:** {CR-NNN} - {requirement_text_short}
- **Role context:** Industry={industry}, Specialty={specialty}, Orientation={orientation}, Level={level}, Work-state={work_state}
- **Content:** {2-3 sentences max - what the user surfaced, in their own terms}
- **Status:** pending
```

**Enrichment** - new or under-represented profile information surfaced on a
partial-match or covered requirement, or during interview prep. Not a closure.

```
### PU-{NNN} - {short_label}

- **Captured:** {YYYY-MM-DD}
- **From:** {APP-NNN} ({company} | {role})
- **Related requirement:** {CR-NNN} - {requirement_text_short}, or 'n/a' with a short reason
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
- **Closed requirement / Related requirement** - the CR-NNN identifier from that
  gap-analysis run + the requirement text in short form. Anchors the entry's
  provenance. Which label appears is the entry kind: `Closed requirement:` means
  the input closed the gap, `Related requirement:` means it did not and the
  requirement is context only. A capture with no requirement anchor at all (a
  general fact surfaced during interview prep) is an enrichment carrying
  `Related requirement: n/a` plus a short reason. The label matters inside
  gap-analysis, where `gap_qc.py` check G7 verifies that anything staged as a
  closure is referenced back from `gap_analysis.md` as the evidence that closed
  a requirement. The promotion step does not read it.
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
