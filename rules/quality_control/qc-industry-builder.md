---
qc_target: industry-builder
last_updated: 2026-05
---

# QC - industry-builder

**Used by:** qc-industry-builder, industry-builder, scripts/builder.py

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
  `scripts/builder.py` to attach to the file's frontmatter and append to
  `design/build_issues.md`.

## Checks

Each check has a stable ID, a rule, an **owner** (which runtime executes the
check), and the fix the build attempts on failure.

Two owners:

- **`script`** - `scripts/builder.py qc` runs the check and, where the fix is
  purely textual, auto-fixes the value file in place. Reports the result in
  the qc subcommand's JSON output.
- **`subagent`** - `qc-industry-builder` subagent runs the check in isolated
  context (LLM judgment required). The skill collects the subagent's findings
  and feeds the unresolved set to `apply-create` / `apply-refresh` via
  `--issues`.

The calling skill runs the script first (auto-fixes applied), then the
subagent (judgment-only set), then aggregates both result lists.

### A - Frontmatter and metadata

- **A1** *(script)*: Frontmatter present and bounded by `---` fences at
  the top of the value file.
  - Fix on fail: rebuild the frontmatter block from required keys.
- **A2** *(script)*: `industry: <value>` key present and matches the
  value being built.
  - Fix on fail: insert or correct the line.
- **A3** *(script)*: `last_researched: YYYY-MM` key present and equals
  the current year-month of the build.
  - Fix on fail: insert or correct the line.
- **A4** *(script)*: Title is `# <Value Name> - CV Framing Rules`
  (display capitalization of the value, hyphen rather than em dash).
  - Fix on fail: rewrite the title line.
- **A5** *(script)*: `**Used by:** <consumers>` header present on the
  line immediately under the title (after a blank line).
  - Fix on fail: insert the standard header listing `cv_targeted,
    axis-classifier`.

### B - Structural schema

- **B1** *(script)*: All four required sections present and non-empty:
  `## Vocabulary`, `## Dialect`, `## Emphasis`, `## Adjacency`.
  - Fix on fail: re-enter Phase 3 to draft the missing section from research.
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

- **E1** *(script)*: The drafted file's `## Adjacency` section contains
  one bullet per file-backed sibling in `rules/industries/` (excluding the
  registry and the value being built; including any file-deferred siblings
  marked appropriately).
  - Fix on fail: add the missing bullet(s); the QC subagent supplies the
    placeholder text based on research, then re-runs to verify.
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

- **F1** *(subagent)*: Sources cited in the research findings are
  authoritative for their claim type (regulatory bodies for regulatory
  frameworks, recognized industry organizations or standards bodies for
  terminology, peer-reviewed or governmental sources for quantitative claims).
  Marketing pages and low-authority blogs are recorded as findings even when
  the underlying claim is uncontroversial.
  - Fix on fail: re-enter Phase 2 to find a stronger source for the same claim.

### G - Registry alignment

- **G1** *(script)*: The registry entry text passed to `apply-create` or
  the existing registry entry (refresh) lists the same filename as the value
  file being written (`File: <value>.md` matches the actual filename).
  - Fix on fail: rewrite the registry entry text to match.
- **G2** *(script)*: The registry entry's one-line description summarizes
  the file's scope (description and file content agree on the substantive area).
  - Fix on fail *(subagent)*: rewrite the registry description from the
    drafted file's content.

### H - Voice and style (mechanical only)

- **H1** *(script)*: No em dashes (`—` U+2014 or `--` rendered as em dash)
  anywhere in the file body. Axis files are products per the `em_dash_scope`
  rule.
  - Fix on fail: replace each em dash with a hyphen, period, or rewrite per
    context; default to a comma when ambiguous.
- **H2** *(script)*: Where the file defines an acronym list under
  `## Dialect`, acronyms used in the body but not in the list are added to
  the list; acronyms listed but unused in the body are removed.
  - Fix on fail: reconcile the list to actual body usage.

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
list to the `--issues` temp file passed to `scripts/builder.py
apply-create` or `apply-refresh`. Each entry:

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
