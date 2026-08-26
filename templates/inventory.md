# Experience Inventory - template

**Used by:** the inventory builder (creates a first `inventory.md` for a user),
the profile-update skill (inserts and enriches entries), and
`scripts/profile_update_qc.py` (parses this file at check time for the section
roster and the per-prefix field rosters).
**Structure authority** for `personal/profile/inventory.md` per
`structure-authority-is-the-template`. Change the schema here, not in the
consuming scripts.

Lives at `personal/profile/inventory.md`. One per user. Every downstream skill
(retrieval, gap-analysis, cv-targeted, the prep skills) reads from it and none
writes to it directly; writes go through the profile-update skill.

## How this template is parsed

Two blocks below are machine-read. Nothing else in this file is.

- **`## Document skeleton`** - the fenced block gives the section roster and its
  canonical order. A heading written literally (`## Education`) is schema and
  must be present. A heading written as a placeholder (`### {Category}`) is the
  per-user category mechanism: the heading level and its position are schema,
  the names are derived per user and are never copied from this file or from
  another user's inventory.
  A section that no entry schema claims and that carries sub-headings is a
  **list section**: it holds flat item lines rather than entries, so it has no
  IDs, and `profile-update` reaches it with `list-add` against a
  `<Section> / <Category>` address rather than with `insert`. Adding one here is
  the whole change; no script names these sections.
- **`## Entry schemas`** - each `### <PREFIX>` fenced block gives that entry
  type's field roster in canonical order. A field line ending in `{optional}`
  may be omitted. Every other field line is required. Field order in a written
  entry matches the order here.

Placeholders are `{...}`. `{NNN}` is a zero-padded three-digit counter.

## Document skeleton

```
# Experience Inventory

## Table of Contents

{generated: one ordered list entry per heading below, in document order}

---

## Employment & Role History

{RL records}

---

## Experience Entries

---

### RL-{NNN}

{EX entries for that role, one '### RL-{NNN}' sub-heading per role}

---

## Independent & Volunteer Projects

{PR entries}

## Industry Exposure Profile

### {Category}

{flat item lines}

---

## Technical Experience

### {Category}

{flat item lines, or '**{Sub-category}:** item, item, item' lines}

---

## Education

{ED entries}

---

## Professional Training

### Completed

{TR entries}

### In Progress

{TR entries}

---

## Professional Certifications

{CERT entries}

---

## Professional Affiliations

{AFF entries}

## Publications

{PB entries}

## Presentations

{PS entries}

## Awards & Honors

{AW entries}
```

Section order is three clusters per `inventory-section-denumbering-and-reorder-2026-07`:
work (Employment & Role History through Technical Experience), credentials
(Education through Professional Certifications), professional standing
(Professional Affiliations through Awards & Honors). Headings carry no numeric
prefix; heading text is the sole section identifier.

A section holding no entries carries a single `Entries: None` line rather than
being omitted, so a downstream skill can distinguish observed absence from an
unscaffolded document.

## Entry schemas

### RL - Employment & Role History

```
ID: RL-{NNN}
Title: {role title}
Company: {employer, or 'Independent' for self-directed periods}
Location: {city, state}
Type: {Direct | Contract | Freelance | Military | Independent}
Style: {Remote | Hybrid | On-site}
Concurrent: {Yes | No}
Allocation: {percentage}
Start Date: {YYYY-MM}
End Date: {YYYY-MM, blank if current}
Entries: None {optional}
```

`Entries: None` asserts that the role is intentionally carried with zero EX and
PR entries (a background role). Present it only on that assertion; absence of
the field means entries are expected.

### EX - Experience Entries

```
ID: EX-{NNN}
Role: RL-{NNN}
Industry: {value} {optional}
Specialty: {value}
Orientation: {value}
Level: {value}
Work-state: {value}
Description: **{what was done}**
Impact: {value-type}: {residual outcome}
Context: {situation, constraint, or scope bound} {optional}
```

### PR - Independent & Volunteer Projects

```
ID: PR-{NNN}
Project: {project name}
Role: RL-{NNN}
Company: {employer} {optional}
Industry: {value} {optional}
Specialty: {value}
Orientation: {value}
Level: {value}
Work-state: {value}
Description: **{what was done}**
Impact: {value-type}: {residual outcome}
Context: {situation, constraint, or scope bound} {optional}
```

`Role:` and `Company:` are mutually exclusive. Use `Role:` whenever a role
record exists; `Company:` is the fallback for a project with no role record.

### ED - Education

```
ID: ED-{NNN}
Degree: {degree}
Discipline: {field of study}
Institution: {institution}
Start Date: {YYYY}
End Date: {YYYY}
Coursework: {optional}
```

`Coursework:` is a multi-line field: the label sits on its own line and each
following line is indented two spaces as `{Category}: {items}`.

### TR - Professional Training

```
ID: TR-{NNN}
Training: {course or program name}
Provider: {provider}
Format: {Online | In-Person | Hybrid} {optional}
Start Date: {YYYY-MM}
End Date: {YYYY-MM, blank if in progress}
```

Completion status is carried by which sub-section the entry sits in, not by a
field.

### CERT - Professional Certifications

```
ID: CERT-{NNN}
Certification: {certification name}
Issuer: {issuing body}
Date Earned: {YYYY}
Expiration Date: {YYYY, blank if non-expiring or unknown}
Status: {Active | Inactive}
```

### AFF - Professional Affiliations

```
ID: AFF-{NNN}
Affiliation: {organization}
Membership: {Member through Board / Officer / Committee Chair / peer reviewer}
Start Date: {YYYY}
End Date: {YYYY, blank if current}
Status: {Active | Inactive}
```

This section carries active professional service (committee and working-group
roles, advisory boards, peer review, conference organizing, board service)
alongside passive memberships. The `Membership:` field carries the distinction;
there is no heading split.

### PB - Publications

```
ID: PB-{NNN}
Title: {title}
Type: {peer-reviewed article | published abstract | white paper | industry article}
Venue: {journal, publisher, or outlet}
Authors: {author list}
Published: {YYYY-MM}
Industry: {value}
Specialty: {value}
Orientation: {value} {optional}
Role: RL-{NNN} {optional}
Link: {DOI or URL} {optional}
Description: {what it covers}
Impact: {value-type}: {residual outcome} {optional}
```

Eligibility floor: accepted or better. Nothing in preparation.

### PS - Presentations

```
ID: PS-{NNN}
Title: {title}
Type: {conference talk | keynote | panel | poster | webinar | podcast | media interview}
Event: {event or series name}
Location: {city, state, or 'Virtual'}
Delivered: {YYYY-MM}
Industry: {value}
Specialty: {value}
Orientation: {value} {optional}
Presenters: {co-presenters} {optional}
Role: RL-{NNN} {optional}
Link: {URL} {optional}
Description: {what it covered}
Impact: {value-type}: {residual outcome} {optional}
```

Eligibility floor: delivered. Accepted-but-not-yet-delivered items wait.

### AW - Awards & Honors

```
ID: AW-{NNN}
Award: {award name}
Issuer: {issuing body}
Date: {YYYY}
Recognizes: EX-{NNN} {optional}
Description: {what it was for} {optional}
```

Reference content, not retrieval-scored. `Recognizes:` links the award to the
work entry it recognizes so cv-targeted can pull it alongside a cited entry.
`Description:` is carried only when the award name does not self-describe.

## Field notes

- **IDs** are per-prefix sequential counters, zero-padded to three digits, and
  are never reused or renumbered. A new entry takes the highest existing number
  for its prefix plus one, derived by scanning the document rather than from any
  recorded count.
- **Axis fields** (`Industry`, `Specialty`, `Orientation`, `Level`,
  `Work-state`) take values from the axis registries under `rules/`. A field may
  carry multiple values separated by ` | `; the value before the first pipe is
  the primary and governs sort order.
- **Omit `Industry` when the work has no industry the registry recognizes.**
  The industry registry is a matching vocabulary listing the industries the
  candidate applies into, not a descriptive taxonomy of every industry they have
  worked in. Self-directed work has no client industry at all, and work done for
  an industry outside the registry can never match a job classified against it.
  In both cases the field is omitted rather than filled with an invented value:
  scoring is identical either way (no match, 0.0), and the entry still reaches
  retrieval on its other axes. Keep the real industry as prose in `Context:`
  where it is worth recording; for self-directed work the role record already
  carries `Type: Independent`. Never widen the registry to cover a source
  industry the candidate does not target.
- **Retrieval participation.** EX, PR, PB, and PS entries are axis-tagged and
  scored during retrieval. RL, ED, TR, CERT, AFF, and AW entries are reference
  content: they are addressable by ID and by section heading, and they are not
  scored.
- **Description** is one bolded sentence naming what was done. Activity and
  methodology stay here; a realized outcome belongs in Impact.
- **Impact** is a value-type prefix plus optional residual-outcome prose. The
  prefix may be a comma-delimited list. When no residual outcome survives beyond
  the Description, the bare prefix stands alone; the field is not dropped.
- **Context** carries prior state, constraint envelope, or a load-bearing scope
  decision. It is omitted when there is none.
- **EX entry placement.** Entries sit under the `### RL-{NNN}` sub-heading
  matching their `Role:` field, sorted by primary Orientation, then primary
  Specialty, then ID ascending. The RL sub-headings themselves run in the same
  order as the Employment & Role History records.
- **Technical Experience lists named tools, products, libraries, and platforms
  only.** Capability descriptions, methods, and algorithms belong in EX entries.
  One item per token, comma-separated, no versions.
- **Per-user category sets.** The `### {Category}` headings under Industry
  Exposure Profile are derived per user from their field and its hiring
  conventions, never copied from another inventory. The current user's
  Technical Experience sub-sections were recorded as schema by
  `experience-inventory-section-5-restructure` and have not been reclassified;
  a builder serving a user outside clinical research should treat that roster as
  an open question rather than copying it.
