---
name: retrieval
description: Surface the relevant profile content for a role. Reads role-intake's outputs, scores inventory entries, narratives, and Signature Themes against the role's critical requirements, and writes a retrieval manifest that downstream skills (gap analysis, CV creation, interview prep, career brief) consume. Run this after role-intake.
---

# retrieval - surface the relevant profile content

Produces one artifact for the role: a **retrieval manifest** at
`personal/applications/<SLUG>_APP-NNN_YYYY-MM/retrieval.md`. The manifest
exposes raw per-entry signals (semantic score, axis exact-match count, axis
adjacency-weighted score) for inventory, narratives, and themes. Downstream
skills derive their own tier cutoffs from the raw signals - retrieval does
NOT pre-classify entries.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases below run in order; each has a declared input and output.
- Each phase opens with the **bold lead line** under its heading - speak it
  verbatim before running the phase.
- User-facing status and prompts use plain English. No raw QC check tags or
  route-back labels, no implementation jargon (subagent, JSON). Translate
  every finding, loop status, and error message to what the user needs to
  know to decide or act.
- Phase 5 (QC) loops back per *Phase routing on failure*.
- **Run-scratch goes in the application's scratch folder.** `<scratch>` denotes
  `<app_folder>/scratch/`; create it if absent. Write every working file this
  skill produces - and tell every sub-agent it spawns to write its output files -
  under `<scratch>`, never the shared `temp/`. Scratch persists for the life of
  the application (a resumed run reuses it); it is wiped in one shot by
  `scratch_cleanup.py` when the application is declined (gap-analysis) or closed
  (the `close-application` skill).

## Resume check - run before Phase 0

Ask if this session is for a new retrieval run or to resume a previous one?

- **New:** ask the APP-NNN; locate the matching folder under
  `personal/applications/`. Confirm that `research.md` exists in the folder
  (retrieval depends on role-intake's output). If missing, halt and direct
  the user to run `/role-intake` first.
- **Resume:** ask the APP-NNN; locate the matching folder. Probe and land
  per the ladder (first match wins):
  1. Folder missing - halt; APP-NNN likely wrong. Ask for APP-NNN again.
  2. `research.md` missing - halt; direct the user to run `/role-intake`.
  3. `retrieval.md` missing - resume at start of **Phase 1**.
  4. `retrieval.md` exists - announce ("Manifest already exists for APP-NNN. Re-run? Y/N.") and either resume at Phase 1 (re-run) or jump to Phase 6 (review existing).

  Announce ("Resuming APP-NNN at Phase N.") and proceed without prompting
  further.

## Phase 0 - Intro

**Introducing the retrieval skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py retrieval` and show the output.
- Output: user oriented.

## Phase 1 - Load context

**Loading the role-intake artifacts for this application.**

- Input: application folder path (from the resume check), APP-NNN, slug.
- Read `research.md` from the application folder. Extract the `## Critical Requirements` section (the matching target for all three scoring passes).
- Read the session log (`session_log.md`) from the application folder. Extract the `## Axis Classification` section (used for the deterministic axis-scoring pass). The session log is the authoritative source for the classification per `retrieval-architecture-2026-05`.
- Read `jd.md` from the application folder. The JD text is passed to the scorer subagent as supporting context.
- Format the axis classification as a JSON object with one key per axis (`Industry`, `Specialty`, `Orientation`, `Level`, `Work-state`), each holding `{primary: <value>, secondary: <value or null>}`. Write to a scratch file (for example `<scratch>/<SLUG>_jd_axes.json`).
- Output: critical-requirements text block, JD text, axis-classification JSON scratch-file path, session-log path (for Phase 5 QC cross-reference).

## Phase 2 - Build payloads

**Building scoring payloads for the inventory, narratives, and themes corpora.**

- Input: slug, APP-NNN.
- Run three commands in sequence (or in parallel via shell):
  - `python scripts/retrieval_payload.py inventory` - prints JSON to stdout with the chunked inventory payload.
  - `python scripts/retrieval_payload.py narratives` - prints JSON to stdout with the narrative payload.
  - `python scripts/retrieval_payload.py themes` - prints JSON to stdout with the theme payload.
- Capture each output to a scratch file: `<scratch>/<SLUG>_APP-NNN_inventory_payload.json`, `<scratch>/<SLUG>_APP-NNN_narratives_payload.json`, `<scratch>/<SLUG>_APP-NNN_themes_payload.json`.
- Non-zero exit on any of these = halt per global rules.
- Run `python scripts/retrieval_payload.py split --slug <slug> --app-id APP-NNN --temp-dir <scratch>`. This writes one JSON file per inventory chunk (`<scratch>/<SLUG>_APP-NNN_inv_chunk0.json`, etc.) and one JSON file per narrative chunk (`<scratch>/<SLUG>_APP-NNN_narr_chunk0.json`, etc.; narratives are batched by byte budget, not one file per narrative), and prints a plain-English summary of chunk counts and sizes per corpus and theme count. Non-zero exit = halt per global rules.
- Output: three payload scratch-file paths, per-chunk scratch-file paths for both corpora, chunk counts and entry counts (from split output).

## Phase 3 - Score all three corpora

**Scoring inventory chunks, narratives, and themes against critical requirements.**

- Input: critical-requirements block, JD text, per-chunk file paths for both corpora (from Phase 2 split output), themes payload file path.
- Dispatch the scorer subagent in parallel. Each invocation receives: input file path, output file path, corpus type, critical requirements, JD text. The scorer writes results to the output file and returns only a brief confirmation — do not read or echo the scores in the main context.
  - **One `retrieval-scorer` invocation per inventory chunk.**
    - Input file: `<scratch>/<SLUG>_APP-NNN_inv_chunk{N}.json`
    - Output file: `<scratch>/<SLUG>_APP-NNN_scores_inventory_chunk{N}.json`
    - Corpus: `inventory`
  - **One `retrieval-scorer` invocation per narrative chunk.**
    - Input file: `<scratch>/<SLUG>_APP-NNN_narr_chunk{N}.json`
    - Output file: `<scratch>/<SLUG>_APP-NNN_scores_narr_chunk{N}.json`
    - Corpus: `narratives`
  - **One `retrieval-scorer` invocation for themes.**
    - Input file: `<scratch>/<SLUG>_APP-NNN_themes_payload.json`
    - Output file: `<scratch>/<SLUG>_APP-NNN_scores_themes.json`
    - Corpus: `themes`
- After all scorers confirm completion, run `python scripts/retrieval_score_merge.py --slug <slug> --app-id APP-NNN --temp-dir <scratch>`. This reads all per-agent output files, merges by corpus, and writes `<scratch>/<SLUG>_APP-NNN_inventory_scores.json`, `<scratch>/<SLUG>_APP-NNN_narrative_scores.json`, and `<scratch>/<SLUG>_APP-NNN_theme_scores.json`. Non-zero exit = halt per global rules.
- Output: three merged score file paths.

## Phase 4 - Assemble and write manifest

**Computing axis signals, walking linked inventory, and writing the manifest.**

- Input: application folder path, slug, APP-NNN, today's date, axis-classification JSON path, three scoring scratch-file paths.
- Run `python scripts/retrieval_apply.py assemble --folder <app_folder> --slug <slug> --app-id APP-NNN --date YYYY-MM-DD --jd-axes-file <path> --inventory-scores-file <path> --narrative-scores-file <path> --theme-scores-file <path>`.
- The script reads all inputs, computes per-entry axis exact-match count and adjacency-weighted score (using `rules/<axis>/<value>.md` Adjacency sections), unions the semantic-pass set with the tag-pull set on inventory, unions the semantic-scored narratives with the Linked-Inventory walk for narratives, and writes the manifest to `personal/applications/<SLUG>_APP-NNN_YYYY-MM/retrieval.md`.
- Capture the printed manifest path. Non-zero exit = halt per global rules.
- Output: `retrieval.md` written.

## Phase 5 - QC

**Running QC on the manifest.**

- Input: application folder path, run date, inventory scored-entry count (from the `retrieval_score_merge.py` output in Phase 3).
- Run `python scripts/retrieval_qc.py check --folder <app_folder> --scored-inventory <N> --date YYYY-MM-DD`. Every check is deterministic (structure, axis consistency, coverage counts, column population, link and ID existence, date); there is no judgment subagent for this artifact.
- **Loops on FAIL:** translate the failed checks to plain English for the user, then apply each per *Phase routing on failure*, re-run forward, and return to Phase 5.
- Cap the loop at **3 iterations**. Exit earlier on **PASS**. If failures remain after the third iteration, stop looping and carry them into the Phase 6 handoff so the user sees them.
- Output: PASS verdict, or unresolved failures after 3 iterations.

## Phase 6 - Handoff

**Reviewing the manifest, recording the run in the session log, and confirming readiness for downstream skills.**

- Input: manifest (QC-passed, or with unresolved findings).
- Write the run record to a scratch file (`<scratch>/<SLUG>_retrieval_section.md`) starting with `## Retrieval` and carrying: run date, manifest path, item counts per corpus, QC verdict. Then run `python scripts/session_log.py append-section --folder <app_folder> --heading Retrieval --body-file <scratch path>`. The script replaces the section on re-runs and appends it on first runs. Non-zero exit = halt per global rules.
- Present a compact summary to the user:

  ```
  Retrieval manifest: <manifest path>
  Inventory candidates: <N> entries surfaced (<M> via semantic, <P> via tag-pull only).
  Narratives: <N> surfaced (<M> semantic-scored, <P> linkage-only).
  Triggered themes: <N>.
  Unresolved QC findings: <listed in plain English, or "none">
  Session log: ## Retrieval section written.

  Ready for gap analysis or CV creation.
  ```

- No approval gate. The manifest is read-only output of this skill; downstream skills consume it directly. If the user disagrees with what was surfaced, they re-run retrieval (the appropriate scoring threshold tuning lives in the scorer subagent, not in this skill body).

## Phase routing on failure

Consumed by Phase 5 (QC failures). Route back, fix, re-run forward (Phase 5 always re-runs after a fix).

| Finding type | Route back to |
|---|---|
| Manifest structure malformed | Phase 4 |
| Axis classification inconsistent with session log | Phase 1 |
| Inventory coverage short of source, manifest matches activity record (entries dropped before scoring) | Phase 2 |
| Inventory coverage missing rows, manifest short of activity record (dropped at merge/assemble) | Phase 4 |
| Signal column population incomplete | Phase 4 |
| Narrative linked-from IDs not in inventory | Phase 4 |
| Theme ID fabricated | Phase 3 (theme scoring) |
| Other fabricated IDs | Phase 3 (corresponding corpus scoring) |
| Generated date missing or malformed | Phase 4 |
