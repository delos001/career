---
name: industry-builder
description: Build or refresh an industry value file in rules/industries/. Researches the target industry, drafts the value file (Vocabulary, Dialect, Emphasis, Adjacency), reconciles against sibling files, runs QC with auto-fix, and updates the registry. Invoke when an industry value is "File deferred" in the registry, or when an existing file needs a periodic refresh.
---

# industry-builder - build or refresh an industries axis value file

Builds (or refreshes) a value file in `rules/industries/` per the per-axis schema:
frontmatter (`industry: <value>`, `last_researched: YYYY-MM`), `Used by:` header,
and the four sections Vocabulary, Dialect, Emphasis, Adjacency.

User-invoked. Not called from role-intake; role-intake's Phase 6 may recommend
invoking it after flagging an axis gap.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases below run in order; each has a declared input and output.
- Each phase opens with the bold lead line under its heading. Speak it verbatim
  before running the phase.
- Halt on any failure or ambiguity outside the QC auto-fix loop; never proceed
  on partial content; never fabricate.

## Phase 0 - Intro

**Building or refreshing an industry value file.**

- Input: invocation.
- Output: user oriented.

## Phase 1 - Resolve target and mode

**Resolving the target industry value and mode.**

- Input: invocation arguments (may include `<value>` and/or `create`/`refresh`).
- Ask the user for any missing argument:
  - Target value (registry key, e.g. `generics`).
  - Mode: `create` (greenfield value file) or `refresh` (re-research existing file).
- Run `python scripts/axis_builder.py lookup industries <value>`. It returns the
  registry state: `not-in-registry`, `file-deferred`, `registry-only`,
  `file-backed`, plus the value-file path if any.
- Validate mode against state:
  - `create` valid when state is `not-in-registry` or `file-deferred`.
  - `refresh` valid when state is `file-backed`.
  - `registry-only` (by-design entries like `eclinical`): refuse; this value is
    intentionally registry-only and no file should be built.
  - Any other mismatch: halt and ask.
- Read `rules/industries/registry.md` and build the siblings list:
  every non-self registry entry as `{value, state, path}` where `state` is
  `file-backed`, `file-deferred`, or `registry-only` and `path` is the
  absolute value-file path (file-backed entries only; null otherwise).
  Carried through Phases 2, 4, and 5; computed once here. Consumers filter
  by state: Phase 2 research passes all; Phase 4 reconciler passes only
  file-backed (the other states have no file to read or edit).
- Output: `{value, mode, state, value_file_path or null, siblings}`.

## Phase 2 - Research

**Researching the target industry.**

- Input: target value, siblings list (from Phase 1).
- Dispatch the `industry-builder-research` subagent with the inputs it
  declares in `.claude/agents/industry-builder-research.md`:
  - `axis`: `industries`
  - `value`: the target value
  - `siblings`: every non-self entry from Phase 1's siblings list, as just
    the value names. The agent researches adjacency considerations for
    each; file-deferred and registry-only siblings are included so the
    drafter has source material for the Adjacency bullets E1 requires.
- The agent returns a fixed block scoped to what this skill needs to draft
  the four sections: regulatory landscape, terminology and acronyms,
  hiring-panel emphasis signals, and adjacency considerations vs. sibling
  industries.
- Output: research findings block.

## Phase 3 - Draft value file (and registry entry, create mode)

**Drafting the new (or updated) value file from the research findings.**

- Input: research findings, mode, value file path (refresh only).
- Draft the value file content per the per-axis schema: frontmatter
  (`industry: <value>`, `last_researched: <current YYYY-MM>`), `Used by:`
  header, then Vocabulary, Dialect, Emphasis, Adjacency.
- Match the voice and density of existing files in `rules/industries/`.
  `pharma.md` is the canonical reference.
- **Create mode only**: also draft the one-line registry-entry bullet that
  Phase 6 will splice into `rules/industries/registry.md`. Format:
  `- **<value>** - <short scope description>. File: <value>.md.`
  The description must summarize the same substantive area the drafted
  value file covers (so G2 holds), and the filename must match the value
  (so G1 holds). For a value currently in the registry as `File deferred`,
  reuse the existing description if it still fits; otherwise rewrite it
  from the drafted value file's scope.
- Output:
  - Refresh: drafted value file content as text.
  - Create: drafted value file content as text + registry-entry line as text.

## Phase 4 - Reconcile against existing files

**Reconciling the draft against the rest of the rules/industries/ folder.**

- Input: drafted value file content, mode, siblings list (from Phase 1),
  value file path (refresh only), research findings (refresh only).
- Dispatch the `industry-builder-reconciler` subagent with the inputs it
  declares in `.claude/agents/industry-builder-reconciler.md`:
  - `axis`: `industries`
  - `value`: the target value
  - `mode`: `create` or `refresh`
  - `drafted_value_file`: the Phase 3 drafted text
  - `siblings`: only the file-backed entries from Phase 1's siblings list,
    as `{value, path}` pairs (file-deferred and registry-only entries have
    no file to read or edit)
  - `current_value_file` (refresh only): the existing value-file path
  - `research_findings` (refresh only): the Phase 2 research block, so
    refresh-mode change records can cite their source

  **Create mode**: the agent reads each sibling file, identifies which
  siblings' Adjacency sections do not yet cover the new value, drafts a
  back-edge bullet for each in that sibling's voice, and returns the
  per-sibling edits.

  **Refresh mode**: the agent reads the current value file, compares
  against the new draft section-by-section, and returns a structured
  change list (per change: section, type [add/remove/modify], current,
  proposed, reasoning citing a research finding).

- Output:
  - Create: drafted value file + per-sibling back-edge edits.
  - Refresh: drafted value file + structured change list against current.

## Phase 5 - QC with auto-fix

**Quality-checking the build and auto-fixing what can be fixed.**

- Input: Phase 4 output, research findings, mode.
- The QC runs in two halves per `rules/quality_control/qc-industry-builder.md`:
  the script half (mechanical checks with auto-fix) and the subagent half
  (judgment checks).

  **Script half - mechanical checks + auto-fix.** Write the drafted value file
  to a temp file. Run:

  ```
  python scripts/axis_builder.py qc industries <value> \
    --mode <create|refresh> \
    --value-file <temp> \
    [--sibling-edits <temp>]   # create mode
    [--registry-entry <temp>]  # create mode
    [--changes <temp>]         # refresh mode
  ```

  The script auto-fixes script-owned issues in place (frontmatter keys, title
  line, `Used by:` header, section order, Adjacency self-reference) and
  prints a JSON report:
  `{"checks": [{"id": "...", "passed": bool, "fixed": bool, "detail": "..."}]}`.
  Re-read the (now possibly mutated) value-file temp before dispatching the
  subagent so the subagent sees the auto-fixed text.

  **Subagent half - judgment checks.** Dispatch `qc-industry-builder` with the
  (post-script) drafted file, the sibling edits or change list, the
  research findings, and (create mode) the sibling file paths plus the
  registry entry text. The subagent returns
  `{"findings": [{"check": "...", "detail": "..."}]}` covering only the
  judgment-owned checks (C1-C3, D1-D2, E3, F1, G2, H2).

- Aggregate failures from both halves:
  - Script half: any `passed: false` from the script's `checks` array.
  - Subagent half: every entry in the `findings` array.

- For each aggregated failure, route to the phase that produced the
  failing artifact, then re-enter Phase 5 from the script half:
  - **B1, B3** (missing or extra sections) -> Phase 3 redraft.
  - **E1** (new file's Adjacency missing a sibling) -> Phase 3 redraft of
    the Adjacency section. The reconciler does not touch this section.
  - **E4** (sibling edits target non-Adjacency section) -> Phase 4
    reconciler re-run.
  - **G1, G2** (registry-entry filename or description wrong) -> Phase 3
    redraft of the registry-entry line.
  - **I1-I3** (mode invariants) -> halt and surface; these are invocation
    errors, not content errors.
  - **C1-C3, F1** (citation traceability, source authority) -> Phase 2
    re-research.
  - **D1, D2, H2** (cross-file boundaries, acronym list) -> Phase 3 redraft.
  - **E3** (sibling-voice phrasing) -> Phase 4 reconciler re-run.

- Loop up to 3 iterations. After 3 iterations, accept the best draft as-is
  and treat the still-unresolved failures as the provisional-issues list.

- Output:
  - Final drafted value file + sibling edits (create) or change list (refresh).
  - QC result: `clean` (all checks pass) or `provisional` with the unresolved
    list. Each unresolved entry is `{check, detail, attempted}` where
    `attempted` summarizes what the loop tried (e.g. `redrafted twice; same
    traceability gap on ICH E6(R3) citation`).

## Phase 6 - Write

**Writing the file(s) and updating the registry.**

- Input: Phase 5 output, target value, mode.

### Create path

- Write the final value file content, sibling edits, and registry-entry text to
  temp files. Run:

  ```
  python scripts/axis_builder.py apply-create industries <value> \
    --value-file <temp> \
    --sibling-edits <temp> \
    --registry-entry <temp> \
    [--provisional --issues <temp>]
  ```

  The script writes the value file, applies sibling Adjacency edits, replaces
  the registry entry, and (if `--provisional`) adds `provisional: true` plus
  the unresolved-issues list to the value file's frontmatter and appends a
  record to `design/build_issues.md`.

### Refresh path

- The post-QC drafted file (the `--value-file` temp from Phase 5, with any
  script auto-fixes already applied in place) is the source of truth. Run:

  ```
  python scripts/axis_builder.py apply-refresh industries <value> \
    --value-file <temp> \
    [--provisional --issues <temp>]
  ```

  The script overwrites `rules/industries/<value>.md` with the drafted text,
  bumps `last_researched`, and (if `--provisional`) marks the file and logs
  to `design/build_issues.md`. The reconciler's change list from Phase 4 is
  informational (used by QC's I3 check to detect a no-op refresh); it is
  not the apply mechanism, so Phase 5 auto-fixes always carry through.

- Output: paths printed by the script.

## Phase 7 - Confirmation

**Confirming completion.**

- Output:
  - Clean: `build completed; <value file path>`.
  - Provisional: `build completed (provisional, issues logged); <value file path>`.
- For create mode, also state the sibling files modified and the registry
  entry's new state.
