# Profile writing rules - plan

## Context

The RL-020 inventory review (2026-10-21 to 22) rewrote most entries the model had placed in earlier runs. The writing rules applied in that review exist only in conversation. The template carries three short field rules (`templates/inventory.md` field notes), one of which the review contradicts. Without written rules, every profile update comes back to the user for judgment calls.

`profile-update` (about 220 lines) is already the only writer to `inventory.md`. Its inventory writes are deterministic (`insert`, `set`, `list-add`). Narrative enrichment is a hand Edit.

## Decisions

- Writing rules live in rules files, one per target document, not in skills. The skill loads the file for the document it is writing.
- A routing rules file holds the steps that come before any write: which document, which section, new entry or addition to an existing one.
- The template keeps the schema (fields, order, placement). Writing judgment moves to the rules file, and the template points to it.
- Every write to a profile document is a script command. Narratives gain a `set`-style command so no hand Edits remain.
- `profile-update` gets shorter: the guidance it carries moves out to the rules files.

## Rules captured from the review (EX entries)

Field tests:
- **Description:** what was done. Ask "is this an action?" Keep it lean: name one or two examples, never the full list of sub-steps. Name tools and platforms here (Spotfire, SQL Server, Databricks), because retrieval scores Description. Who was involved goes in Context. No purpose clause that restates Impact. No "from greenfield" (Work-state says it).
- **Impact:** what was observable after the person left. Ask "could someone see this after you left?" Results caused by the work count, including a roadmap leading to tested capabilities. Alignment claims, "positioned for", and restated activity fail.
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
- **EX sort rule (P4):** change it to fit the user's groups, or formalize groups as parents using the PR objective/elements pattern. Comes after the cleanup.

## Build sequence

1. `rules/profile/routing.md`: which document, which section, new or existing, with the test for each.
2. `rules/profile/inventory-writing.md`: one file for the whole inventory, with a section per entry type. The EX section holds the rules above, as a short decision flow per field. Settle the tags decision first.
3. `templates/inventory.md`: replace the Description/Impact/Context field notes with a pointer to the rules file.
4. `profile-update` SKILL.md: Step 3 loads the routing file, then the target document's rules file. Remove the writing guidance now held there.
5. Narratives write command in `profile_update.py`, with a test seen to fail.
6. Later: `rules/profile/narratives-writing.md`, `rules/profile/positioning-writing.md`, and sections in `inventory-writing.md` for the other entry types when needed.

## Verification

- `python tests\run_tests.py` green. The new write command's test is seen to fail first.
- `profile-update` SKILL.md is shorter than before.
- A dry run on one staged PU entry reaches a proposal without asking the user anything the rules answer.
