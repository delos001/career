# PR schema rebuild - plan

Decision: `pr-objective-elements-schema-2026-10` in `design_decisions.md`. This file is the build sequence only.

## Context

PR entries move from EX-shaped blocks to Objective + Elements. The 2026-10-16 impact survey found the change concentrated in two shared parsers (`retrieval_payload.py`, `profile_update.py`), with moderate changes in the citation and QC checks and wording changes in agents and rules. Most parsing is shared across EX/PR/PB/PS, which is why the module refactor comes first.

## Isolation

Applications must keep running throughout. Nothing the application pipeline reads changes until the cutover.

- **Code:** steps 1-7 are built on a branch of the career repo, checked out in a separate git worktree. Tests run against `tests/fixture`. `main` stays unchanged for application runs. The worktree has no `personal/` (it is gitignored), so it cannot touch the live profile.
- **Data:** step 8 migrates PR entries in a copy, `personal/profile/inventory_mig.md`. `inventory.md` stays on the old format. No branch in `personal/`.
- **Freeze:** no PR edits in `inventory.md` between the copy and the cutover. PU entries targeting a PR stay in the queue. EX, RL, and other edits continue as normal.
- **Cutover (one session):** merge the code branch; replace the projects section of the current `inventory.md` with the migrated section from `inventory_mig.md`; run the verification below; delete `inventory_mig.md`.
- **Rollback:** revert the code merge and restore `inventory.md` from git in `personal/`.

## Build sequence

0. **Draft the data first.** Done 2026-10-20; schema locked. Before any branch or code: draft the PR fence in `design/pr_template_draft.md` (step 2; the live template stays untouched until cutover, since the scripts read it at run time) and migrate every project, with the user, into `personal/profile/inventory_mig.md`, which holds only the projects section. Start with the career system (hardest case). Lock the schema from what drafting finds; steps 1-7 then build to it, and step 8 becomes a check of the drafts by the new scripts.
1. **`scripts/inventory_model/` package.** Built 2026-10-21 on `pr-schema`. Behavior-neutral for every type: tests and a full retrieval payload diff must match before and after.
   - `document.py`: section bounds, template field lists.
   - `entry_block.py`: find and read ID blocks into fields, next ID (with optional `.NN`), field order against the template. Used by every type.
   - `ex.py`, `pr.py`, `pb.py`, `ps.py`, `rl.py`: only what each type does differently. ED, CERT, AFF, TR, AW get a file when a type first needs its own rule.
   - Replaces the three separate parsers in `profile_update.py`, `retrieval_payload.py` and `profile_slice.py`.
   - Private helpers used across scripts must keep working or have their callers moved in the same change: `profile_update_qc.py` and `staging_append.py` (`pu._section_bounds` and about 20 others), `gap_context.py` (`retrieval_payload._ENTRY_RE`, `extract_section`), `retrieval_apply.py` (parser output keys).
2. **Template.** Done 2026-10-21 on `pr-schema`, from `design/pr_template_draft.md` (fixture PR-001 migrated with it so the suite stays green). Rewrite the PR fence and field notes in `templates/inventory.md` (Objective, `Elements:`, indented element and Outcome lines, Company kept, Industry note no longer points at Context).
3. **PR module.** Built 2026-10-21 on `pr-schema`; smoke-tested, regression tests in step 7. Retired rows carry the element's text in Notes (template note).
   - Parse Objective and Elements.
   - `profile_update.py`:
     - add an element subcommand (add/edit an element, assign `.NN`);
     - `set` must never span into `Elements:`;
     - `verify_targets` accepts `PR-NNN.NN`.
   - `profile_slice.py id PR-NNN.NN` returns block header + Objective + that element.
   - `profile_slice.py id` falls back to `inventory-ret.md` for an ID not in the inventory and labels the result retired, so an in-flight application's citations still resolve.
4. **Retrieval.** Built 2026-10-21 on `pr-schema`. `gap_context.py` needed no change (PR blocks keep their `ID:` line). Inventory chunks are now byte-budgeted (`--chunk-bytes`, default 60000) instead of 50 items: the cutover preview gives 6 scorers instead of 8, no chunk larger than today's largest. At cutover, update `retrieval-architecture-2026-05` (design_decisions.md, "chunks of approximately 50 entries").
   - `retrieval_payload.py` emits the objective item and one item per element (project name + element + Outcome).
   - `retrieval_qc.py` R3 counts elements; R7 accepts sub-IDs.
   - `gap_de_emphasize.py` keeps element rows and treats objective/element citations as protecting each other.
   - `gap_assemble.py` uses the same parent/child exclusion.
   - `retrieval_apply.py` reads the new PR item keys; `gap_context.py` recognizes element ID lines.
5. **Checks.** Built 2026-10-21 on `pr-schema`: cv_qc C3/C6/N2 element-aware and new C8 (element without objective); gap_qc G8; profile_update_qc P12 (retired IDs), new P13 (elements) and P14 (same-project agreement); QC scope treats a block and its elements as one. Smoke-tested; regression tests in step 7.
   - `cv_qc.py`:
     - `ENTRY_ID_RE` accepts `.NN`;
     - C3 valid IDs include elements;
     - N2 duplicate logic is sub-ID aware;
     - new check: an element cited without its objective fails.
   - `gap_qc.py` G8 same.
   - `profile_update_qc.py`: element ID uniqueness, padding, parent match; Outcome attached to an element; shared-field agreement across same-Project blocks.
   - `profile_update.verify_targets` (close, P12) accepts IDs logged in `inventory-ret.md`: past PU migrated lines name PR IDs that retire at cutover (found in the step 4 cutover preview: PU-012, 018, 025, 026, 029, 030, 033, 034).
6. **Agents, skills, rules.** Done 2026-10-21 on `pr-schema`, edited in place. No change needed: `qc-cv-targeted`, retrieval SKILL.md, narrative templates (block IDs already allowed), `career-strategist` and `cv-best-practices.md` (their Impact is CV-bullet craft, not the inventory field).
   - Agents: `retrieval-scorer`, `gap-detector`, `de-emphasize-identifier`, `cv-architect`, `qc-cv-targeted`, `qc-profile-update`.
   - Skills: profile-update SKILL.md (element path), retrieval SKILL.md (item count).
   - Rules: `rules/cv/cv-structure.md` (citation convention, Outcome as impact source), narrative templates (`Linked Inventory` may cite block IDs).
   - Check whether their Impact mentions apply to PR: `career-strategist` agent, `rules/cv/cv-best-practices.md`.
   - Docs: `COMPONENTS.md`.
7. **Tests and fixture.** Done 2026-10-21 on `pr-schema`: 9 new tests and 5 new checker breakages (28 tests total); each of 14 code mutations turned its test red. Added in passing: element numbering skips retired element numbers.
   - Migrate the fixture PR-001 (done with step 2).
   - Add tests: element numbering, `set Objective` keeps elements, sub-ID existence (C3/G8/R7), R3 with elements, de-emphasize element rows, element-without-objective.
   - Watch each go red first.
8. **Migration check.** Done 2026-10-21: all new checks pass on the migrated projects. Drafting (step 0) produced 8 blocks in `inventory_mig.md`: PR-001, 006, 009, 010, 011, 015, 017, and new PR-019. Run the new checks over it.
   - Retire to `inventory-ret.md` with the absorbing block: 003, 004, 005, 012, 013, 014, 018 into PR-001; 007, 008 into PR-006; 016 into PR-015.
   - Repoint narratives.md lines citing PR-001/003/004/005/009 (at cutover).
   - Then mark superseded decisions.
9. **Cutover.** Done 2026-10-21: code applied to `main`, projects section swapped (rest of `inventory.md` byte-identical), 10 retired rows added, narratives ST-011 and DC-005 repointed, retrieval dry run gives 8 objective and 137 element items in 6 chunks. `inventory_mig.md`, the two design drafts, and the `pr-schema` worktree and branch deleted.

## Verification

- `python tests\run_tests.py` green, with each new check seen to fail first.
- Step 1: retrieval payload for EX/PB/PS byte-identical before and after.
- At cutover: `profile_update_qc.py check` passes on the full inventory; every PR ID gap has an `inventory-ret.md` row; a retrieval dry run on one application shows objective and element rows.
- Old application artifacts are not re-QC'd against the new schema.
