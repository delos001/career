---
qc_target: level-builder
last_updated: 2026-05
---

# QC - level-builder

**Used by:** qc-level-builder, level-builder, scripts/axis_qc.py, scripts/axis_apply.py

Quality checks the `qc-level-builder` subagent runs against a drafted level
value file plus the per-sibling Adjacency edits (create mode) or structured
change list (refresh mode). The QC is part of the build loop, not a user
surface: every failed check either gets auto-fixed within the loop or is
written to the build issues log when the loop exits with unresolved items.

## Loop and exit

The builder runs QC, attempts fixes, and re-runs QC. The loop caps at
**3 iterations**. On the final iteration, all checks pass = clean; any
remaining failure = provisional with unresolved findings emitted to
`--issues` for `axis_apply.py` to attach to frontmatter and append to
`design/build_issues.md`.

## Checks

Two owners:
- **`script`** - `scripts/axis_qc.py` runs the check and auto-fixes where
  the fix is purely textual.
- **`subagent`** - `qc-level-builder` subagent runs the check in isolated
  context (LLM judgment required).

The calling skill runs the script first (auto-fixes applied), then the
subagent (judgment-only set), aggregates both result lists, and routes
each failure per the failing check's **Fix on fail** entry below, which
names the phase to re-enter (or directs a halt). This file is the single
routing source; the skill's Phase 5 does not carry its own routing table.

### A - Frontmatter and metadata

- **A1** *(script)*: Frontmatter present and bounded by `---` fences.
  - Fix on fail: report; Phase 5 routes to Phase 3 redraft.
- **A2** *(script)*: `level: <value>` key present and matches the value
  being built.
  - Fix on fail: insert or correct the line.
- **A3** *(script)*: `last_researched: YYYY-MM` key present and equals
  the current year-month.
  - Fix on fail: insert or correct the line.
- **A4** *(script)*: Title line present, ends with `- CV Framing Rules`
  (case-insensitive on the suffix).
  - Fix on fail: report; Phase 5 routes to Phase 3.
- **A5** *(script)*: `**Used by:** <consumers>` header present on the
  first non-blank line after the title.
  - Fix on fail: insert standard header (`cv_targeted, axis-classifier`);
    if buried elsewhere, report and route to Phase 3.

### B - Structural schema

- **B1** *(script)*: All five required sections present, unique, and
  non-empty: `## Identity`, `## Voice`, `## Verb vocabulary`,
  `## Scope signals`, `## Adjacency`.
  - Fix on fail: re-enter Phase 3 to draft the missing or merge the
    duplicated section.
- **B2** *(script)*: Section order matches the schema.
  - Fix on fail: order mismatches are auto-fixed. The only failure the
    script surfaces is "cannot reorder: duplicate headings," which always
    co-occurs with a B1 duplicate-heading failure; B1's Phase 3 redraft
    resolves it. No separate routing.
- **B3** *(script)*: No sections beyond the schema.
  - Fix on fail: re-enter Phase 3 to relocate content from extra sections
    into the appropriate schema section, then remove the extra heading.
- **B4** *(script)*: `## Adjacency` contains the mandatory
  `### Low or no adjacency` sub-section per `axes-file-schema`.
  - Fix on fail: insert the sub-section at the end of `## Adjacency`
    with the `_(none)_` placeholder. Auto-fix.

### C - Content traceability

- **C1** *(subagent)*: Every named framework or convention in the drafted
  file traces to a source in `research_findings`.
  - Fix on fail: re-enter Phase 2 to re-research the missing citation.
- **C2** *(subagent)*: Version-stamped references carry stamps consistent
  with research-findings currency. Level files rarely carry version
  stamps; pass silently when none are present.
  - Fix on fail: re-enter Phase 2 to re-confirm the reference's current
    version; correct or remove the stamp on redraft.
- **C3** *(subagent)*: Every quantitative or temporal claim traces to a
  source.
  - Fix on fail: re-enter Phase 2 to re-research; if still unsourced,
    rewrite the claim qualitatively or remove it on redraft.

### D - Cross-file responsibility boundaries

- **D1** *(subagent)*: The drafted file's Identity section does not
  paraphrase the identity of a sibling level. Each level's identity is
  uniquely owned by its own file; the new file's identity should be
  distinct enough that the exclusion conditions explicitly route sibling
  cases away.
  - Fix on fail: re-enter Phase 3 to remove or rewrite the overlapping
    content to make the distinction explicit.
- **D2** *(subagent)*: The drafted file's content stays within the levels
  axis (identity framing, voice register, verb vocabulary, scope signals,
  adjacency translation). Off-axis content includes: industry-specific
  terminology or regulatory framing (industries territory), capability
  vocabulary or practice methods (specialties territory), CV-identity or
  section-emphasis rules (orientations territory), achievement framing by
  work-state (work-states territory).
  - Fix on fail: re-enter Phase 3 to remove off-axis content.

### E - Adjacency completeness

- **E1** *(script)*: The drafted file's `## Adjacency` section enumerates
  every non-self entry in `rules/levels/registry.md` in one of two forms
  per `axes-file-schema`: substantive bullet
  (`- **<sibling>**: <translation rule>.`) or plain bullet inside
  `### Low or no adjacency` (`- <sibling>`). Missing from both is the
  failure case.
  - Fix on fail: re-enter Phase 3 to add the missing bullet(s).
- **E2** *(script)*: The drafted file's `## Adjacency` section does not
  reference itself.
  - Fix on fail: remove the self-reference.
- **E3** *(subagent, create only)*: Each per-sibling back-edge bullet is
  phrased in that sibling's voice (describes when entries tagged with
  this level translate to the sibling level's CV framing).
  - Fix on fail: re-enter Phase 4 reconciler to redraft.
- **E4** *(script)*: Each per-sibling back-edge targets the sibling's
  `## Adjacency` section.
  - Fix on fail: re-enter Phase 4 for the reconciler to re-target the
    edit to the Adjacency section.

### F - Source quality

- **F1** *(subagent)*: Sources cited in research findings match the
  acceptable source class for the claim type they support. Level files
  are framing-heavy; F1 typically applies to hiring-pattern and
  CV-convention claims. Acceptable sources at that tier: authoritative
  references where they exist; otherwise verified industry intelligence
  (recognized recruiter firms, established trade publications, sector-
  specific newsletters with editorial accountability). Marketing pages,
  unsourced blogs, sponsored content, and AI-generated summaries without
  attribution fail F1.
  - Fix on fail: re-enter Phase 2 to find a source in the acceptable class.

### G - Registry alignment

- **G1** *(script)*: The registry entry text lists the same filename as
  the value file being written.
  - Fix on fail: re-enter Phase 3 to rewrite the registry entry text to
    match.
- **G2** *(subagent)*: The registry entry's one-line description summarizes
  the file's scope.
  - Fix on fail: re-enter Phase 3 to redraft the registry-entry line.

### H - Voice and style

- **H1** *(subagent)*: Em dashes do not appear in body prose. Frontmatter
  fences (`---`) and structural separators are exempt.
  - Fix on fail: re-enter Phase 3 to redraft the offending sentence
    without an em dash.
### I - Mode invariants

- **I1** *(script, create only)*: The value file did not exist before this run.
  - Fix on fail: halt; invocation error.
- **I2** *(script, refresh only)*: The value file existed before this run.
  - Fix on fail: halt; invocation error.
- **I3** *(script, refresh only)*: At least one meaningful change is present.
  - Fix on fail: re-enter Phase 2 with broader research scope; if still no
    change, exit clean and note that the file is current.

## Unresolved-finding output format

```json
{
  "check": "<check-id from above, e.g. C1>",
  "detail": "<one-line description of what failed and where>",
  "attempted": "<one-line description of fix attempts within the loop>"
}
```
