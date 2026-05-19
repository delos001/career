---
qc_target: industry-builder
last_updated: 2026-05
---

# QC - industry-builder

**Used by:** qc-industry-builder, industry-builder, scripts/axis_qc.py, scripts/axis_apply.py

Quality checks the `qc-industry-builder` subagent runs against a drafted
industry value file plus the per-sibling Adjacency edits (create mode) or
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
- **`subagent`** - `qc-industry-builder` subagent runs the check in isolated
  context (LLM judgment required). The skill collects the subagent's findings
  and feeds the unresolved set to `axis_apply.py create` / `axis_apply.py
  refresh` via `--issues`.

The calling skill runs the script first (auto-fixes applied), then the
subagent (judgment-only set), then aggregates both result lists.

### A - Frontmatter and metadata

- **A1** *(script)*: Frontmatter present and bounded by `---` fences at
  the top of the value file.
  - Fix on fail: report; Phase 5 routes the failure to Phase 3 for the
    drafter to add the fences. Not auto-fixed because prepending empty
    fences to a file whose drafter wrote keys at the top without fences
    would push those orphan keys into the body and let A2/A3 insert
    duplicate copies into the new shell.
- **A2** *(script)*: `industry: <value>` key present and matches the
  value being built.
  - Fix on fail: insert or correct the line.
- **A3** *(script)*: `last_researched: YYYY-MM` key present and equals
  the current year-month of the build.
  - Fix on fail: insert or correct the line.
- **A4** *(script)*: A top-level title line is present and ends with
  `- CV Framing Rules` (case-insensitive on the suffix). The display form
  of the value (e.g. CRO vs Cro) is the drafter's responsibility; the
  script neither enforces nor seeds capitalization, since most casing
  decisions are judgment calls (initialisms, acronyms, brand forms).
  - Fix on fail: report; Phase 5 routes the failure to Phase 3 for the
    drafter to write or correct the title line.
- **A5** *(script)*: `**Used by:** <consumers>` header present on the
  line immediately under the title (after a blank line).
  - Fix on fail: insert the standard header listing `cv_targeted,
    axis-classifier`.

### B - Structural schema

- **B1** *(script)*: All four required sections present, unique, and
  non-empty: `## Vocabulary`, `## Dialect`, `## Emphasis`, `## Adjacency`.
  Duplicate headings fail B1 too; the section-order auto-fix in B2 would
  otherwise silently collapse them and lose one copy's content.
  - Fix on fail: re-enter Phase 3 to draft the missing or merge the
    duplicated section from research.
- **B2** *(script)*: Section order matches the schema (Vocabulary,
  Dialect, Emphasis, Adjacency).
  - Fix on fail: reorder sections.
- **B3** *(script)*: No sections beyond the schema (no extra `## ` headings).
  - Fix on fail: relocate content from extra sections into the appropriate
    schema section, then remove the extra heading.

### C - Content traceability

- **C1** *(subagent)*: Every regulatory citation (named framework, guidance,
  rule number) in the drafted file traces to a source named in the research
  findings.
  - Fix on fail: re-enter Phase 2 to re-research the missing citation; on
    re-draft, remove the citation if no source can be found.
- **C2** *(subagent)*: Every version-stamped framework (e.g. `ICH E6(R3)`,
  `eCTD v4.0`) carries a version stamp consistent with the research findings'
  currency.
  - Fix on fail: correct the version stamp from research; remove if no source
    supports any specific version.
- **C3** *(subagent)*: Every quantitative or temporal claim
  (counts, dates, "current as of", market-share figures) traces to a source.
  - Fix on fail: re-research; if unsourced, rewrite the claim qualitatively
    or remove it.

### D - Cross-file responsibility boundaries

- **D1** *(subagent)*: The drafted file's content does not restate terms,
  acronyms, or framings already owned by a sibling industry file in
  `rules/industries/` (the new file's vocabulary belongs to its own
  industry; sibling-owned content belongs to siblings).
  - Fix on fail: remove the duplicated content; if the content is genuinely
    distinct in the new industry's context, rewrite it to reflect that
    distinction.
- **D2** *(subagent)*: The drafted file's content stays within the industries
  axis (regulatory landscape, industry terminology, hiring-panel emphasis).
  Capability vocabulary, method names, voice-and-verb framing, identity
  framing, and work-state framing belong to other axis files and are excluded.
  - Fix on fail: remove off-axis content.

### E - Adjacency completeness

- **E1** *(script)*: The drafted file's `## Adjacency` section enumerates
  every non-self entry in `rules/industries/registry.md` (file-backed,
  file-deferred, and registry-only). Per `axes-file-schema`, each sibling
  appears in exactly one of two forms:
  - **Substantive bullet** in the main portion: `- **<sibling>**:
    <translation rule>.` Used when the pair has a real translation rule.
  - **Plain bullet** inside the optional terminal `### Low or no
    adjacency` sub-section: `- <sibling>`. Used when the pair has no
    translation logic worth stating.

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
  - Fix on fail: reject the edit; reconciler must re-target.

### F - Source quality

- **F1** *(subagent)*: Sources cited in the research findings match the
  acceptable source class for the claim type they support. Tier table:
  - **Regulatory framework / statute / rule-number citations** (FDA guidance,
    CFR sections, EMA, EU regulations, ICH guidelines, formal industry
    codification such as the RAPS regulatory-affairs corpus): require the
    issuing body or a recognized authoritative reference.
  - **Standards-body citations** (ISO, IEC, AAMI, CLSI, USP, EP): require the
    standards body itself or a recognized authoritative reference.
  - **Quantitative or temporal claims** (counts, percentages, dates, "current
    as of", "X is dominant"): require peer-reviewed literature, government
    statistics, or a recognized standards body.
  - **Hiring-pattern or qualitative-industry-sentiment claims** (what hiring
    panels weight, which credentials matter, where talent moves between
    sectors): require an authoritative source if one exists at the claim's
    granularity; otherwise accept verified industry intelligence (recognized
    recruiter firms, established trade publications, sector-specific
    newsletters) provided the source has editorial accountability (named
    authors or named organization, traceable to a known entity in the sector).

  In any tier, marketing pages (vendor self-promotion), unsourced blogs (no
  editorial accountability), sponsored content, and AI-generated summaries
  without attribution fail F1 regardless of claim type.
  - Fix on fail: re-enter Phase 2 to find a source in the acceptable class
    for the claim's tier. If the tier is hiring-pattern and re-research
    confirms no authoritative source exists at the claim's granularity, a
    verified-industry-intelligence source is acceptable.

### G - Registry alignment

- **G1** *(script)*: The registry entry text passed to `apply-create` or
  the existing registry entry (refresh) lists the same filename as the value
  file being written (`File: <value>.md` matches the actual filename).
  - Fix on fail: rewrite the registry entry text to match.
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
- **H2** *(script)*: Where the file defines an acronym list under
  `## Dialect`, acronyms used in the body but not in the list are flagged
  for addition; acronyms listed but unused in the body are flagged for
  removal. The script extracts both sets deterministically (regex on
  2-6 char alphabetic runs with at least 2 uppercase letters, with plural
  normalization so `ANDAs` matches `ANDA`, and a small exclusion set for
  Roman numerals, the `CV` title artifact, and cross-domain world
  acronyms like `DNA`, `UN`, `XML`). Report-only in both directions;
  splicing tokens out of the comma-separated Dialect catalog safely is
  deferred to a v2 auto-fix.
  - Fix on fail: re-enter Phase 3 for the drafter to add to the list,
    rewrite the body to drop the term, or prune the unused entry.

### I - Mode invariants

- **I1** *(script, create only)*: The value file did not exist before this
  run (`apply-create` will raise on a pre-existing file; QC verifies the
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
