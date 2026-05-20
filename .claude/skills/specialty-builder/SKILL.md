---
name: specialty-builder
description: Build or refresh a specialty value file in rules/specialties/. Researches the target specialty, drafts the value file (Capability vocabulary, Terminology, Knowledge-transfer mode, Adjacency), reconciles against sibling files, runs QC with auto-fix, and updates the registry. Invoke when a specialty value is "File deferred" in the registry, or when an existing file needs a periodic refresh.
---

# specialty-builder - build or refresh a specialties axis value file

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
- **Script failure categorization.** Every `scripts/axis_*.py` invocation
  follows the same exit contract:
  - Exit 0: success. Parse stdout per the subcommand's documented output.
  - Exit 2 with `ContractError:` stderr prefix: a subagent's JSON output
    did not match the declared shape. The build cannot continue. Halt and
    tell the user verbatim:
    "The build couldn't continue because one of the helper outputs didn't
    match the expected shape. Details logged for dev triage."
    Then append a section to `design/build_issues.md` (header
    `## <YYYY-MM-DD> - <axis>-builder <mode> - <value> (contract failure)`),
    with one bullet containing the full stderr text and one bullet naming
    which subagent produced the offending output. Do not retry.
  - Exit 1 with `Error:` stderr prefix: any other failure (file missing,
    registry malformed, mode invariant violated). Translate the stderr
    text to plain English using the situation context; halt.

## Phase 0 - Intro

**Building or refreshing a specialty value file.**

- Input: invocation.
- Output: user oriented.

## Phase 1 - Resolve target and mode

**Resolving the target specialty value and mode.**

- Input: invocation arguments (may include `<value>`). Mode is NOT a
  user-supplied argument; the registry state determines the only valid
  mode. Ignore any `create`/`refresh` token the user may have passed.
- Ask the user for the target value if it is not in the arguments. Do
  not ask for mode.
- Run `python scripts/axis_registry.py list specialties`. It returns
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
  - `not-in-registry` or `file-deferred` -> mode is `create`. Tell the
    user "No file exists yet for `<value>`. Want me to create one now?"
    and wait for yes/no. If no, halt cleanly.
  - `file-backed` -> mode is `refresh`. Read the value file's
    `last_researched` from its frontmatter and tell the user
    "`<value>` already has a file (last researched `<YYYY-MM>`).
    Refresh it?" and wait for yes/no. If no, halt cleanly.
  - `registry-only` -> refuse. Tell the user "`<value>` is intentionally
    registry-only; no file should be built. Stopping." Do not offer to
    create.
- Build the siblings list as every non-self entry from the `list` output,
  preserving its `{value, state, value_file_path}` shape.
- Output: `{value, mode, state, value_file_path or null, siblings}`.

## Phase 2 - Research

**Researching the target specialty.**

- Input: target value, siblings list (from Phase 1).
- Dispatch the `specialty-builder-research` subagent with the inputs it
  declares in `.claude/agents/specialty-builder-research.md`:
  - `axis`: `specialties`
  - `value`: the target value
  - `siblings`: every non-self entry from Phase 1's siblings list, as just
    the value names.
- Output: research findings block per the agent's return schema (capability
  landscape, practice-specific terminology, knowledge-transfer convention,
  adjacency considerations per sibling).

## Phase 3 - Draft value file (and registry entry, create mode)

**Drafting the new (or updated) value file from the research findings.**

- Input: research findings, mode, value file path (refresh only).
- Draft the value file content per the per-axis schema: frontmatter
  (`specialty: <value>`, `last_researched: <current YYYY-MM>`),
  `Used by:` header, then Capability vocabulary, Terminology,
  Knowledge-transfer mode, Adjacency.
- Match the voice and density of existing files in `rules/specialties/`.
  `clinical-operations.md` is the canonical reference.
- **Terminology scoping discipline.** The Terminology section lists only
  practice-specific terms; sector-wide terms (regulatory bodies,
  pharmacovigilance vocabulary, trial-lifecycle stages) belong to
  `rules/industries/*.md` and must not be restated. Open the Terminology
  section with the explicit cross-reference sentence naming which industry
  file owns the sector-wide vocabulary (D1 checks for it).
- **Create mode only**: also draft the one-line registry-entry bullet
  Phase 6 will splice into `rules/specialties/registry.md`. Format:
  `- **<value>**: <short scope description>. File: <value>.md.`
- Output:
  - Refresh: drafted value file content as text.
  - Create: drafted value file content as text + registry-entry line as text.

## Phase 4 - Reconcile against existing files

**Reconciling the draft against the rest of the rules/specialties/ folder.**

- Input: drafted value file content, mode, siblings list (from Phase 1),
  value file path (refresh only), research findings (refresh only).
- **Create mode pre-step (extract sibling Adjacency slices).** For each
  file-backed sibling from Phase 1's siblings list, run:

  ```
  python scripts/axis_registry.py slice specialties <sibling_value> \
    --section Adjacency
  ```

  Capture the stdout as `adjacency_text` for that sibling.
- Dispatch the `specialty-builder-reconciler` subagent with the inputs it
  declares in `.claude/agents/specialty-builder-reconciler.md`:
  - `axis`: `specialties`
  - `value`: the target value
  - `mode`: `create` or `refresh`
  - `drafted_value_file`: the Phase 3 drafted text
  - `siblings`:
    - Create mode: `{value, adjacency_text}` pairs for every file-backed
      sibling.
    - Refresh mode: `{value, path}` pairs for cross-reference checks.
  - `current_value_file` (refresh only): the existing value-file path
  - `research_findings` (refresh only): the Phase 2 research block

- Output:
  - Create: drafted value file + per-sibling back-edge edits.
  - Refresh: drafted value file + structured change list against current.

## Phase 5 - QC with auto-fix

**Quality-checking the build and auto-fixing what can be fixed.**

- Input: Phase 4 output, research findings, mode.
- The QC runs in two halves per `rules/quality_control/qc-specialty-builder.md`:
  the script half (mechanical checks with auto-fix) and the subagent half
  (judgment checks).

  **Script half - mechanical checks + auto-fix.** Write the drafted value
  file to a temp file. Run:

  ```
  python scripts/axis_qc.py specialties <value> \
    --mode <create|refresh> \
    --value-file <temp> \
    [--sibling-edits <temp>]   # create mode
    [--registry-entry <temp>]  # create mode
    [--changes <temp>]         # refresh mode
  ```

  The script auto-fixes script-owned issues in place. Re-read the
  (possibly mutated) value-file temp before dispatching the subagent.

  **Subagent half - judgment checks.** Dispatch `qc-specialty-builder` with
  the (post-script) drafted file, the research findings, the file-backed
  sibling file paths (for D1), and (create mode only) the sibling edits
  plus the registry entry text.

- Aggregate failures from both halves. For each failure, follow the
  Fix-on-fail entry for that check in
  `rules/quality_control/qc-specialty-builder.md` - it names the phase to
  re-enter, or directs a halt for invocation errors - then re-run Phase 5.
  Loop up to 3 iterations. After 3 iterations, accept the best draft and
  treat unresolved failures as the provisional-issues list.

- Output:
  - Final drafted value file + sibling edits (create) or change list (refresh).
  - QC result: `clean` or `provisional` with unresolved-issues list.

## Phase 6 - Write

**Writing the file(s) and updating the registry.**

- Input: Phase 5 output, target value, mode.

### Create path

```
python scripts/axis_apply.py create specialties <value> \
  --value-file <temp> \
  --sibling-edits <temp> \
  --registry-entry <temp> \
  [--provisional --issues <temp>]
```

### Refresh path

```
python scripts/axis_apply.py refresh specialties <value> \
  --value-file <temp> \
  [--provisional --issues <temp>]
```

- Output: paths printed by the script.

## Phase 7 - Confirmation

**Confirming completion.**

- Output:
  - Clean: `build completed; <value file path>`.
  - Provisional: `build completed (provisional, issues logged); <value file path>`.
- For create mode, also state the sibling files modified and the registry
  entry's new state.
