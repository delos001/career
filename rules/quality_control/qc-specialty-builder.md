---
qc_target: specialty-builder
last_updated: 2026-05
---

# QC - specialty-builder

**Used by:** qc-specialty-builder, specialty-builder, scripts/axis_qc.py, scripts/axis_apply.py

Quality checks the `qc-specialty-builder` subagent runs against a drafted
specialty value file plus the per-sibling Adjacency edits (create mode) or
structured change list (refresh mode). The QC is part of the build loop, not a
user surface: every failed check either gets auto-fixed within the loop or is
written to the build issues log when the loop exits with unresolved items.

## Loop and exit

The builder runs QC, attempts fixes for any failures, and re-runs QC. The loop
caps at **3 iterations**. On the final iteration:
- All checks pass: build proceeds clean.
- One or more checks still fail: build proceeds with the latest draft as
  provisional. Unresolved findings are emitted to `--issues` for
  `scripts/axis_apply.py` to attach to the file's frontmatter and append to
  `design/build_issues.md`.

## Checks

Each check has a stable ID, a rule, an **owner** (which runtime executes the
check), and the fix the build attempts on failure.

Two owners:

- **`script`** - `scripts/axis_qc.py` runs the check and, where the fix is
  purely textual, auto-fixes the value file in place. Reports the result in
  the script's JSON output.
- **`subagent`** - `qc-specialty-builder` subagent runs the check in isolated
  context (LLM judgment required). The skill collects the subagent's findings
  and feeds the unresolved set to `axis_apply.py create` / `axis_apply.py
  refresh` via `--issues`.

The calling skill runs the script first (auto-fixes applied), then the
subagent (judgment-only set), then aggregates both result lists. It routes
each failure per the failing check's **Fix on fail** entry below, which
names the phase to re-enter (or directs a halt). This file is the single
routing source; the skill's Phase 5 does not carry its own routing table.

### A - Frontmatter and metadata

- **A1** *(script)*: Frontmatter present and bounded by `---` fences at
  the top of the value file.
  - Fix on fail: report; Phase 5 routes the failure to Phase 3 for the
    drafter to add the fences. Not auto-fixed because prepending empty
    fences to a file whose drafter wrote keys at the top without fences
    would push those orphan keys into the body and let A2/A3 insert
    duplicate copies into the new shell.
- **A2** *(script)*: `specialty: <value>` key present and matches the
  value being built.
  - Fix on fail: insert or correct the line.
- **A3** *(script)*: `last_researched: YYYY-MM` key present and equals
  the current year-month of the build.
  - Fix on fail: insert or correct the line.
- **A4** *(script)*: A top-level title line is present and ends with
  `- CV Framing Rules` (case-insensitive on the suffix). The display form
  of the value (e.g. data-engineering vs Data Engineering) is the drafter's
  responsibility; the script neither enforces nor seeds capitalization.
  - Fix on fail: report; Phase 5 routes the failure to Phase 3 for the
    drafter to write or correct the title line.
- **A5** *(script)*: `**Used by:** <consumers>` header present on the
  first non-blank line after the title.
  - Fix on fail: insert the standard header listing `cv_targeted,
    axis-classifier`. If the header exists but is buried elsewhere in
    the body, report and route to Phase 3.

### B - Structural schema

- **B1** *(script)*: All four required sections present, unique, and
  non-empty: `## Capability vocabulary`, `## Terminology`,
  `## Knowledge-transfer mode`, `## Adjacency`. Duplicate headings fail
  B1 too; the section-order auto-fix in B2 would otherwise silently
  collapse them and lose one copy's content.
  - Fix on fail: re-enter Phase 3 to draft the missing or merge the
    duplicated section from research.
- **B2** *(script)*: Section order matches the schema (Capability
  vocabulary, Terminology, Knowledge-transfer mode, Adjacency).
  - Fix on fail: order mismatches are auto-fixed. The only failure the
    script surfaces is "cannot reorder: duplicate headings," which always
    co-occurs with a B1 duplicate-heading failure; B1's Phase 3 redraft
    resolves it. No separate routing.
- **B3** *(script)*: No sections beyond the schema (no extra `## ` headings).
  - Fix on fail: re-enter Phase 3 to relocate content from extra sections
    into the appropriate schema section, then remove the extra heading.
- **B4** *(script)*: `## Adjacency` contains the mandatory
  `### Low or no adjacency` sub-section per `axes-file-schema`. The
  sub-section is always present, with a `_(none)_` placeholder body when
  no siblings qualify; structural presence signals "considered and none"
  rather than "forgotten or absent."
  - Fix on fail: insert the sub-section at the end of `## Adjacency`
    with the `_(none)_` placeholder. Auto-fix.

### C - Content traceability

- **C1** *(subagent)*: Every named framework, methodology, tool, or
  standard in the drafted file traces to a source named in the research
  findings.
  - Fix on fail: re-enter Phase 2 to re-research the missing citation; on
    re-draft, remove the citation if no source can be found.
- **C2** *(subagent)*: Every version-stamped framework or tool (e.g.
  `ICH E6(R3)`, `scikit-learn 1.x`) carries a version stamp consistent
  with the research findings' currency.
  - Fix on fail: re-enter Phase 2 to re-confirm the framework's current
    version; correct or remove the stamp on redraft.
- **C3** *(subagent)*: Every quantitative or temporal claim (counts,
  dates, "current as of", adoption-share figures) traces to a source.
  - Fix on fail: re-enter Phase 2 to re-research; if still unsourced,
    rewrite the claim qualitatively or remove it on redraft.

### D - Cross-file responsibility boundaries

- **D1** *(subagent)*: Two checks. First, the drafted file's Terminology
  section opens with the explicit cross-reference sentence naming which
  industry file(s) own the sector-wide vocabulary; D1 verifies that
  sentence is present. Second, the drafted file's Capability vocabulary
  and Terminology do not restate capability vocabulary owned by another
  specialty file in `rules/specialties/`. Detection of industry vocabulary
  actually restated in the draft is D2's job (a specialty file carrying
  industry vocabulary is off-axis content); D1 only checks that the
  scoping sentence is present.
  - Fix on fail: re-enter Phase 3 to add the missing cross-reference
    sentence, or to remove or rewrite content that duplicates a sibling
    specialty file.
- **D2** *(subagent)*: The drafted file's content stays within the
  specialties axis (capability vocabulary, practice-specific terminology,
  knowledge-transfer convention, adjacency). Off-axis content includes:
  industry-specific terminology and regulatory framing (industries
  territory), voice-and-verb framing (level territory), identity framing
  (orientation territory), achievement framing by work-state
  (work-states territory).
  - Fix on fail: re-enter Phase 3 to remove off-axis content.

### E - Adjacency completeness

- **E1** *(script)*: The drafted file's `## Adjacency` section enumerates
  every non-self entry in `rules/specialties/registry.md` (file-backed,
  file-deferred, and registry-only). Per `axes-file-schema`, each sibling
  appears in exactly one of two forms:
  - **Substantive bullet** in the main portion: `- **<sibling>**:
    <translation rule>.` Used when the pair has a real translation rule.
  - **Plain bullet** inside the optional terminal `### Low or no
    adjacency` sub-section: `- <sibling>`. Used when the pair has no
    translation logic worth stating (the candidate either holds both
    tags or does not, and the axis files have nothing more to say).

  Missing from both is the failure case. The reconciler still drafts
  back-edges only into file-backed siblings; E1 just enforces the new
  file's Adjacency completeness.
  - Fix on fail: re-enter Phase 3 to add the missing bullet(s) based on
    the research findings, choosing the appropriate form.
- **E2** *(script)*: The drafted file's `## Adjacency` section does not
  reference itself.
  - Fix on fail: remove the self-reference.
- **E3** *(subagent, create only)*: Each per-sibling back-edge bullet is
  phrased in that sibling's voice (reads as the sibling describing the new
  value, not the new value describing itself).
  - Fix on fail: re-enter Phase 4 reconciler to redraft the offending back-edge.
- **E4** *(script)*: Each per-sibling back-edge targets the sibling's
  `## Adjacency` section (no other section is modified).
  - Fix on fail: re-enter Phase 4 for the reconciler to re-target the
    edit to the Adjacency section.

### F - Source quality

- **F1** *(subagent)*: Sources cited in the research findings match the
  acceptable source class for the claim type they support. Tier table:
  - **Methodology / framework / standard citations** (named methods,
    statistical standards, software libraries with documented APIs,
    industry-organization standards): require the issuing body, peer-reviewed
    literature, or a recognized authoritative reference.
  - **Quantitative or temporal claims** (counts, percentages, dates, "current
    as of", "X is the dominant tool"): require peer-reviewed literature,
    government statistics, or a recognized standards body.
  - **Hiring-pattern or qualitative-practice-sentiment claims** (what hiring
    panels weight, which credentials matter, where talent moves between
    practices): require an authoritative source if one exists at the claim's
    granularity; otherwise accept verified industry intelligence (recognized
    recruiter firms, established trade publications, sector-specific
    newsletters) provided the source has editorial accountability.

  In any tier, marketing pages (vendor self-promotion), unsourced blogs (no
  editorial accountability), sponsored content, and AI-generated summaries
  without attribution fail F1 regardless of claim type.
  - Fix on fail: re-enter Phase 2 to find a source in the acceptable class
    for the claim's tier.

### G - Registry alignment

- **G1** *(script)*: The registry entry text passed to `apply create` or
  the existing registry entry (refresh) lists the same filename as the value
  file being written (`File: <value>.md` matches the actual filename).
  - Fix on fail: re-enter Phase 3 to rewrite the registry entry text to
    match.
- **G2** *(subagent)*: The registry entry's one-line description summarizes
  the file's scope (description and file content agree on the substantive area).
  - Fix on fail: re-enter Phase 3 to redraft the registry-entry line from
    the drafted value file's content.

### H - Voice and style

- **H1** *(subagent)*: Em dashes do not appear in body prose. Frontmatter
  fences (`---`) and structural separators are exempt. On finding an em
  dash in body text, the check fails with the offending sentence quoted;
  the fix is to **rewrite the sentence** so it reads naturally without
  the em dash (period, semicolon, conjunction, or restructure). The check
  does not delete characters or sub-clauses.
  - Fix on fail: re-enter Phase 3 to redraft the offending sentence.
### I - Mode invariants

- **I1** *(script, create only)*: The value file did not exist before this
  run (`apply create` will raise on a pre-existing file; QC verifies the
  registry state was `not-in-registry` or `file-deferred` before the run).
  - Fix on fail: halt; this is an invocation error, not a content error.
- **I2** *(script, refresh only)*: The value file existed before this run.
  - Fix on fail: halt; invocation error.
- **I3** *(script, refresh only)*: At least one meaningful change is
  present (a refresh that produced no changes wasted research effort and
  should be flagged).
  - Fix on fail: re-enter Phase 2 with broader research scope; if still no
    change, exit clean and note that the file is current.

## Unresolved-finding output format

When the loop exits with unresolved findings, the QC subagent emits a JSON
list to the `--issues` temp file passed to `scripts/axis_apply.py create` or
`scripts/axis_apply.py refresh`. Each entry:

```json
{
  "check": "<check-id from above, e.g. C1>",
  "detail": "<one-line description of what failed and where>",
  "attempted": "<one-line description of fix attempts within the loop>"
}
```

The script attaches the list to the value file's frontmatter under
`provisional_issues:` and appends a record to `design/build_issues.md` using
the same fields.
