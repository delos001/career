# Profile writing rules - plan

## Context

The RL-020 inventory review (2026-10-21 to 22) rewrote most entries the model had placed in earlier runs. The writing rules applied in that review exist only in conversation. The template carries three short field rules (`templates/inventory.md` field notes), one of which the review contradicts. Without written rules, every profile update comes back to the user for judgment calls.

`profile-update` (about 220 lines) is already the only writer to `inventory.md`. Its inventory writes are deterministic (`insert`, `set`, `list-add`). Narrative enrichment is a hand Edit.

## Decisions

- Writing rules live in rules files, one per target document, not in skills. The skill loads the file for the document it is writing.
- A routing rules file holds the steps that come before any write: which document, which section, new entry or addition to an existing one.
- The template keeps the schema (fields, order, placement). Writing judgment moves to the rules file, and the template points to it.
- A rules file exists for every document the model writes with judgment: inventory, routing, and the staging file. Staging gets its own rules because capture differs from the final write (destination unknown; limits, uncertainty, and attribution must be kept).
- Each rule lives in one place. The template, skills, and review agent pull rules through a script that prints only the shared section plus the section for the entry type being written.
- Scripts do what needs no judgment: required staging fields, the related-entry pull, and mechanical wording checks. The model decides only routing and wording.
- #70 is folded in as step 0, amended: a staged item is deleted only after its entry passes review.
- Narratives move after the application: 1 of about 43 staged facts ever targeted a narrative. Until then a narrative-bound fact stays in staging, as positioning already does.
- The tag strip, if tags are dropped, is a one-time throwaway script. Nothing about it goes into rules, skills, or docs.

## Rules captured from the review (EX entries)

Field tests:
- **Description:** what was done. Ask "is this an action?" Keep it lean: name one or two examples, never the full list of sub-steps. Name tools and platforms here (Spotfire, SQL Server, Databricks), because retrieval scores Description. Who was involved goes in Context. No purpose clause that restates Impact. No "from greenfield" (Work-state says it).
- **Impact:** the observable result of the work. Ask "could someone see the result without being told what you did?" (Replaced "after you left", which failed for current work.) Results caused by the work count, including a roadmap leading to tested capabilities. Alignment claims, "positioned for", and restated activity fail.
- **Context:** the situation before the work, constraints, or scope bounds. Ask "is this the state of things, not what was done or what came of it?" Activity moves to Description, and outcomes move to Impact. Notes about how to frame the entry do not belong here.

Wording:
- "No X observed" results state the scale first (all studies, a named scope, a time span), then that the result held. Numbers go on group parents and the most-cited entries first. Do not chase numbers for every entry.
- Full sentences end in periods, not semicolons.
- Use plain words. Write "proposed" or "would" for design-stage work that was never built, and say in Context that it was not built.
- Use standard field terms (risk assessment, rules engine, medallion layers) over invented phrases. Before using or keeping a term, state what the work actually was.
- Verbs carry the role: Led, Executed, Authored, Collaborated. Do not upgrade "collaborated" to "built". Do not add "personally".
- No first person in the inventory.

Structure:
- A thin parent entry is fine: a headline plus the group-level Impact. The children carry the activities.
- Split an entry when it holds two kinds of work (leadership vs hands-on; process vs a technical component; roles and responsibilities vs stakeholder management).
- Merge or cut an entry that repeats another's result.
- One home per piece of work. When two roles overlap, file the work where most of its substance happened.
- Remove an entry the person cannot explain if pressed. Log the ID in `inventory-ret.md`.

Review method:
- Review the whole entry (Description, Impact, Context) in one pass.
- Before rewriting, check related entries for overlap.
- Ask for a missing fact instead of inferring it. Flag an unverified fact in one line.

## Open decisions

- **Impact value-type tags.** The user is removing tags that are only there for tagging's sake. Whether to drop them entirely is undecided, and nothing reads them except the unbuilt inventory-builder (#27). The template rule "the bare prefix stands alone; the field is not dropped" conflicts with the review and changes with this decision. The off-list "Strategy Impact" waits on it too.
- **Whether EX Impact becomes optional** in the template.
- **Scope of the single skill:** updates only, or also building a profile from scratch for other users (inventory-builder #27).
- **EX sort rule (P4):** closed 2026-10-27 by `ex-topic-groups-2026-10` (markers, not parents).

## Build sequence

First: settle the Impact tags decision.

0. **Simplify staging (#70).** Drop PU numbering and the migrated record. A staged item is deleted only after its entry passes review.
1. **Staging fields.** `staging_append.py` takes separate required fields: the role where the work happened (not the target job), what the user did and what others did, the outcome the user stated (or "none stated"), and the source (gap analysis requirement). It refuses a capture with a field missing.
2. **Staging rules.** `rules/profile/staging-writing.md`, read by gap-analysis. Seeded from `gap-analysis/SKILL.md`, the staging rule in `rules/global-rules.md`, and the capture lessons from the 2026-08-25 run.
3. **Routing rules.** `rules/profile/routing.md`: which section, and new entry, addition, list item, or duplicate. Seeded from `profile-update` steps 3b-3c and the structure rules above.
4. **Related-entry pull.** A script prints Description, Impact, and Context for every entry in the same role plus entries sharing key words. It chunks only past a size limit (largest role today, RL-020: 44 entries, about 23K characters). The model makes the routing decision from that list.
5. **Inventory rules.** `rules/profile/inventory-writing.md`: shared wording rules, then one section per entry type under a fixed heading pattern. Seeded from the template field notes, `qc-profile-update.md` checks 5-8, the Impact rules in `design_decisions.md`, `inventory_builder_quality_checks.md`, and the review rules above. The user reviews each section.
6. **Mechanical wording checks** in `profile_update_qc.py`: first person, "personally", banned phrases ("positioned for", "from greenfield"), semicolon sentence endings, em dashes, leftover tags. Reuse the `cv_qc.py` patterns.
7. **Targeted rule loading.** A script prints the shared section plus the target type's section. The template, `profile-update`, gap-analysis, and `qc-profile-update` pull rules through it and keep no copies.

After the application: narratives rules and a narratives write command, positioning rules, skill scope.

## Verification

- `python tests\run_tests.py` green, including a test that fails when an entry type has no rules section. Each new test is seen to fail first.
- A grep shows each rule lives in one place only.
- A dry run on one staged item reaches a proposal without asking the user anything the rules answer.
