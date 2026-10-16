# PR schema rebuild - plan

Decision: `pr-objective-elements-schema-2026-10` in `design_decisions.md`. This file is the build sequence only.

## Context

PR entries move from EX-shaped blocks to Objective + Elements. The 2026-10-16 impact survey found the change concentrated in two shared parsers (`retrieval_payload.py`, `profile_update.py`), with moderate changes in the citation and QC checks and wording changes in agents and rules. Most parsing is shared across EX/PR/PB/PS, which is why the module refactor comes first.

## Build sequence

1. **Shared core + per-type modules.** Extract entry boundaries, ID format (with optional `.NN`), and template roster reading into a core; move EX, PR, and the other types behind one module each. Behavior-neutral for every type: tests and a full retrieval payload diff must match before and after.
2. **Template.** Rewrite the PR fence and field notes in `templates/inventory.md` (Objective, `Elements:`, indented element and Outcome lines, Company kept, Industry note no longer points at Context).
3. **PR module.**
   - Parse Objective and Elements.
   - `profile_update.py`:
     - add an element subcommand (add/edit an element, assign `.NN`);
     - `set` must never span into `Elements:`;
     - `verify_targets` accepts `PR-NNN.NN`.
   - `profile_slice.py id PR-NNN.NN` returns block header + Objective + that element.
4. **Retrieval.**
   - `retrieval_payload.py` emits the objective item and one item per element (project name + element + Outcome).
   - `retrieval_qc.py` R3 counts elements; R7 accepts sub-IDs.
   - `gap_de_emphasize.py` keeps element rows and treats objective/element citations as protecting each other.
   - `gap_assemble.py` uses the same parent/child exclusion.
5. **Checks.**
   - `cv_qc.py`:
     - `ENTRY_ID_RE` accepts `.NN`;
     - C3 valid IDs include elements;
     - N2 duplicate logic is sub-ID aware;
     - new check: an element cited without its objective fails.
   - `gap_qc.py` G8 same.
   - `profile_update_qc.py`: element ID uniqueness, padding, parent match; Outcome attached to an element; shared-field agreement across same-Project blocks.
6. **Agents, skills, rules.**
   - Agents: `retrieval-scorer`, `gap-detector`, `de-emphasize-identifier`, `cv-architect`, `qc-cv-targeted`, `qc-profile-update`.
   - Skills: profile-update SKILL.md (element path), retrieval SKILL.md (item count).
   - Rules: `rules/cv/cv-structure.md` (citation convention, Outcome as impact source), narrative templates (`Linked Inventory` may cite block IDs).
7. **Tests and fixture.**
   - Migrate the fixture PR-001.
   - Add tests: element numbering, `set Objective` keeps elements, sub-ID existence (C3/G8/R7), R3 with elements, de-emphasize element rows, element-without-objective.
   - Watch each go red first.
8. **Migration (with user, one project at a time).**
   - Projects: 17 PR entries in 6 projects.
     - career system: 001, 003-005, 012-014, 018
     - engops: 006-009
     - knowledge graph: 015-016
     - requirements graph: 017
     - job monitor: 010
     - candidacy: 011
   - Lowest ID survives per project.
   - Retired IDs go to `inventory-ret.md` with the absorbing element.
   - Repoint narratives.md lines citing PR-001/003/004/005/009.
   - Then mark superseded decisions.

## Verification

- `python tests\run_tests.py` green, with each new check seen to fail first.
- Step 1: retrieval payload for EX/PB/PS byte-identical before and after.
- After migration: `profile_update_qc.py check` passes on the full inventory; every PR ID gap has an `inventory-ret.md` row; a retrieval dry run on one application shows objective and element rows.
- Old application artifacts are not re-QC'd against the new schema.
