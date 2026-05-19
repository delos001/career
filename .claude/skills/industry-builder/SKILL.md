---
name: industry-builder
description: Build or refresh an industry value file in rules/industries/. Researches the target industry, drafts the value file (Vocabulary, Dialect, Emphasis, Adjacency), reconciles against sibling files, runs QC with auto-fix, and updates the registry. Invoke when an industry value is "File deferred" in the registry, or when an existing file needs a periodic refresh.
---

# industry-builder - build or refresh an industries axis value file

User-invoked. Not called from role-intake; role-intake's Phase 6 may recommend
invoking it after flagging an axis gap.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases below run in order; each has a declared input and output.
- Each phase opens with the bold lead line under its heading. Speak it verbatim
  before running the phase.
- Halt on any failure or ambiguity outside the QC auto-fix loop; never proceed
  on partial content; never fabricate.
- User-facing status uses plain English. No internal check IDs (A1, B2, E4,
  G1, H2, etc.), no implementation jargon (subagent, iteration, script half,
  judgment half, JSON, regex). Translate every phase summary, loop status, and
  error message to what the user needs to know to wait, decide, or act.
  Reserve technical detail for explicit dev-triage contexts (the
  `build_issues.md` log, deferral entries, this SKILL file).

## Phase 0 - Intro

**Building or refreshing an industry value file.**

- Input: invocation.
- Output: user oriented.

## Phase 1 - Resolve target and mode

**Resolving the target industry value and mode.**

- Input: invocation arguments (may include `<value>`). Mode is NOT a
  user-supplied argument; the registry state determines the only valid
  mode. Ignore any `create`/`refresh` token the user may have passed.
- Ask the user for the target value if it is not in the arguments. Do
  not ask for mode.
- Run `python scripts/axis_registry.py list industries`. It returns
  `{"entries": [{value, state, value_file_path}, ...]}` with every
  registry entry. Each `state` is `file-backed`, `file-deferred`, or
  `registry-only`; `value_file_path` is set for file-backed entries and
  null otherwise. Do not parse the registry by hand; the script owns the
  parser.
- Find the target value's entry in `entries`. If absent, treat as
  `not-in-registry`.
- Derive mode from state and ask the user a yes/no continuation. Do not
  present a multiple-choice mode picker; for any given state only one
  mode is valid.
  - `not-in-registry` or `file-deferred` → mode is `create`. Tell the
    user "No file exists yet for `<value>`. Want me to create one now?"
    and wait for yes/no. If no, halt cleanly.
  - `file-backed` → mode is `refresh`. Read the value file's
    `last_researched` from its frontmatter and tell the user
    "`<value>` already has a file (last researched `<YYYY-MM>`).
    Refresh it?" and wait for yes/no. If no, halt cleanly.
  - `registry-only` (by-design entries like `eclinical`) → refuse. Tell
    the user "`<value>` is intentionally registry-only - no file should
    be built. Stopping." Do not offer to create.
- Build the siblings list as every non-self entry from the `list` output,
  preserving its `{value, state, value_file_path}` shape.
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
- Output: research findings block per the agent's return schema
  (regulatory landscape, terminology and acronyms, hiring-panel emphasis,
  adjacency considerations per sibling).

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
- **Create mode pre-step (extract sibling Adjacency slices).** For each
  file-backed sibling from Phase 1's siblings list, run:

  ```
  python scripts/axis_registry.py slice industries <sibling_value> \
    --section Adjacency
  ```

  Capture the stdout as `adjacency_text` for that sibling. This gives the
  reconciler the exact context it needs (existing translation bullets in
  the sibling's voice) without dumping full sibling files into its context
  window. Bounded cost regardless of how many siblings the axis has.
- Dispatch the `industry-builder-reconciler` subagent with the inputs it
  declares in `.claude/agents/industry-builder-reconciler.md`:
  - `axis`: `industries`
  - `value`: the target value
  - `mode`: `create` or `refresh`
  - `drafted_value_file`: the Phase 3 drafted text
  - `siblings`:
    - Create mode: `{value, adjacency_text}` pairs for every file-backed
      sibling, using the slices captured in the pre-step.
    - Refresh mode: `{value, path}` pairs for cross-reference checks.
    File-deferred and registry-only entries have no file to slice or read
    and are excluded.
  - `current_value_file` (refresh only): the existing value-file path
  - `research_findings` (refresh only): the Phase 2 research block, so
    refresh-mode change records can cite their source

  **Create mode**: the agent reads each sibling's Adjacency slice,
  identifies which already cover the new value, drafts a back-edge bullet
  for each one that does not (in that sibling's voice, matching the slice's
  existing-bullet style), and returns the per-sibling edits.

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
  python scripts/axis_qc.py industries <value> \
    --mode <create|refresh> \
    --value-file <temp> \
    [--sibling-edits <temp>]   # create mode
    [--registry-entry <temp>]  # create mode
    [--changes <temp>]         # refresh mode
  ```

  The script auto-fixes script-owned issues in place and prints
  `{"checks": [{"id": "...", "passed": bool, "fixed": bool, "detail": "..."}]}`.
  Re-read the (possibly mutated) value-file temp before dispatching the
  subagent so the subagent sees the auto-fixed text.

  **Subagent half - judgment checks.** Dispatch `qc-industry-builder` with
  the (post-script) drafted file, the research findings, the file-backed
  sibling file paths (for the D1 cross-sibling-content check, which runs
  in both modes), and (create mode only) the sibling edits plus the
  registry entry text. The reconciler's refresh change list is not
  passed - no judgment check uses it; it is the script's I3 input only.
  The subagent returns
  `{"findings": [{"check": "...", "detail": "..."}]}` covering only the
  judgment-owned checks (C1-C3, D1-D2, E3, F1, G2, H1).

- Aggregate failures from both halves:
  - Script half: any `passed: false` from the script's `checks` array.
  - Subagent half: every entry in the `findings` array.

- For each aggregated failure, route to the phase that produced the
  failing artifact, then re-enter Phase 5 from the script half:
  - **A4** (title exists but suffix wrong) -> Phase 3 redraft of the title line.
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
  - **H1** (em dash in body prose) -> Phase 3 redraft of the offending sentence.
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
  python scripts/axis_apply.py create industries <value> \
    --value-file <temp> \
    --sibling-edits <temp> \
    --registry-entry <temp> \
    [--provisional --issues <temp>]
  ```

  Side effects: value file written, sibling Adjacency sections edited,
  registry entry replaced. With `--provisional`, the value-file frontmatter
  is marked and `design/build_issues.md` is appended.

### Refresh path

- The post-QC `--value-file` temp (with script auto-fixes already in it) is
  the source of truth; the reconciler's change list is informational, not
  the apply mechanism, so Phase 5 auto-fixes always carry through. Run:

  ```
  python scripts/axis_apply.py refresh industries <value> \
    --value-file <temp> \
    [--provisional --issues <temp>]
  ```

  Side effects: `rules/industries/<value>.md` overwritten, `last_researched`
  bumped. With `--provisional`, the file is marked and
  `design/build_issues.md` is appended.

- Output: paths printed by the script.

## Phase 7 - Confirmation

**Confirming completion.**

- Output:
  - Clean: `build completed; <value file path>`.
  - Provisional: `build completed (provisional, issues logged); <value file path>`.
- For create mode, also state the sibling files modified and the registry
  entry's new state.
