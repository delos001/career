# Career Narratives Builder — Quality Checks

Cumulative quality checks from manual reconciliation passes of `personal/knowledge/Career_Narratives.md`. The `career_narratives` builder skill must encode these so future creation and refresh do not require manual reconciliation. Each check is a defect class observed during review; checks new to this file should be added inline as future reconciliation surfaces them.

Parallel artifact to `design/inventory_builder_quality_checks.md`.

## Finding Resolution Protocol

User decisions on findings are authoritative; the builder applies the response. The post-resolution state must satisfy the corresponding rule in this file and any referenced rule files (`rules/narratives/story_personal.md`, `rules/narratives/decision_adr.md`, etc.).

Applies at creation, refresh, and audit.

## Audit Phase Ordering

Categories are organized in this file by logical grouping (1–6), but audit execution order is **rework-minimizing**: do high-blast-radius substantive content checks early; finish with mechanical/structural verification.

**Recommended audit execution order (per 2026-05-12 framework):**

1. **§2 ID & Reference Integrity** — verify the refs we populated are valid. Cheap. Catches typos before they cascade.
2. **§6 Content Quality** — biggest blast radius. Substantive rewrites done early so downstream consistency checks see final content.
3. **§3 Content Completeness** — after rewrites stabilize, check section presence and placeholders.
4. **§4 Cross-Entry Consistency** — uniformity on final content.
5. **§5 Cross-Document Consistency** — final cross-doc state check.
6. **§1 Structural Integrity** — final mechanical sweep. Catches blank-line / delimiter drift from rewrites.

Rationale: Cat 6 rewrites can invalidate findings from Cat 3/4/5 if done after them. Cat 1 is content-agnostic and best run last to catch drift introduced during rewrites.

## 1. Structural Integrity

- **Document header block required at top.** Order: H1 title (`# Career Narratives`), blank, `**Used by:** <pipe-separated skill list>`, blank, `**Stamps:** <stamp description>`, blank, then TOC. Per `career-narratives-schema` document-header rule.
- **TOC required after document header.** TOC structure: H2 `## Table of Contents` followed by nested bullet list. Includes one entry per H1 section and one entry per narrative (H2). Each narrative TOC entry prepends the ID: `- [ST-NNN <Title>](#anchor)`. Anchor must match the heading text via standard CommonMark slug algorithm.
- **TOC anchor consistency.** When a narrative title changes, its TOC anchor must update in the same edit. Builder validates anchor-to-heading-text correspondence at audit time. 2026-05-12 finding: ST-009 title changed from "Duke CRI" to "Duke Clinical Research Institute" but anchor was not updated in same edit; fixed during Cat 1 sweep.
- **Per-entry metadata block: 6 fields in fixed order.** `ID`, `Role`, `Framework`, `Linked Inventory`, `Added`, `Last Used`. Each on its own line, format `<Field>: <value>`. No blank lines within the block. Field order is part of the schema; reordering is a defect.
- **Blank line between H2 entry heading and metadata block.** Pattern: `## <Title>` blank line, then `ID: <value>`. No blank line between metadata fields (they are tight block).
- **Blank line between metadata block and first H3 section.** Pattern: `Last Used: <value>` blank line, then `### <Section>`. Static parsers depend on this. Enforced 2026-05-12; defect prevented field-line vs section-line disambiguation.
- **H3 level for framework sections.** All framework sections (Situation, Action, The Decision, etc.) use `### `, not `## ` or `#### `. Builder validates at audit time.
- **Standard CommonMark bullet indentation.** Top-level bullet: `- <content>` (single space after dash). Sub-bullet: `  - <content>` (2-space indent, single space after dash). Pandoc style (`-   ` with 3 spaces, 4-space sub-indent) prohibited.
- **Pipe delimiter for multi-value reference lists.** Per §2 rule, applied to `Role`, `Linked Inventory`, document `**Used by:**`. Format: `A | B | C` (space-pipe-space).
- **Comma delimiter for tag-list multi-value.** Where multi-value semantics are tag-list (not reference-list), comma-separated. Currently no narrative field uses comma format; documented for symmetry with inventory conventions and User_Info precedent.
- **Sub-list nesting required where parent introduces children.** Two trigger patterns:
  - Pattern A (colon-introduced): parent bullet ends with `:` (e.g., "This created risk for patients:"). Children indent 2 spaces beneath.
  - Pattern B (contextual continuation): parent bullet introduces a concept that the next bullets elaborate on, even without colon. Example: "Process evolution lagged behind technology adoption." with sub-bullets "skill gaps existed..." and "traditional technology was still heavily relied upon." Indicators: child bullets start with lowercase, child bullets read as descriptive of parent, child bullets cannot stand alone as siblings.
  - Both patterns must be caught during sub-list nesting passes. 2026-05-12 audit surfaced two missed cases (ST-001 Action sub-list, ST-004 Situation sub-list) fixed in Cat 1 sweep.
- **No em-dashes or Pandoc artifacts.** Already enforced in §6; mechanical re-check at audit time.
- **No trailing whitespace on lines.** Mechanical.
- **File ends with single newline.** Mechanical.

**2026-05-12 audit findings (all resolved during Cat 1 sweep):**
- F-6.1 (resolved): ST-001 Action sub-list (lines 64-74) — 4 product-description bullets indented under parent introducer.
- F-6.2 (resolved): ST-004 Situation sub-list (lines 408-412) — 2 bullets indented under "Process evolution lagged behind technology adoption."
- TOC anchor stale for ST-009 — updated to `#early-risk-based-site-monitoring-at-duke-clinical-research-institute`.

## 2. ID & Reference Integrity

- **Story ID format: `ST-NNN`.** Three-digit zero-padded sequence starting at `ST-001`. Stories appear under the `# STORIES: STAR / ATOLA` heading.
- **Decision ID format: `DC-NNN`.** Three-digit zero-padded sequence starting at `DC-001`. Decisions appear under the `# DECISIONS` heading.
- **ID sequence contiguous within prefix.** ST-NNN and DC-NNN sequences allocate from `max(existing) + 1` without skipping numbers at creation. Gaps from deletions remain (per ID immutability) but are not refilled with new entries.
- **ID immutability after creation; deleted IDs retire, not recycle.** Parallel to inventory rule (`design/inventory_builder_quality_checks.md` §3). Once an ST or DC ID is assigned, it does not reattach to unrelated content even after the original entry is deleted.
- **Role field references inventory Section 7.** Every `Role:` value is one or more `RL-NNN` IDs that exist in `personal/knowledge/Experience_Inventory.md` Section 7. Multi-value separated by ` | ` (space-pipe-space) per multi-value reference list convention. Builder validates each RL-NNN exists at audit time.
- **Linked Inventory field references inventory Sections 8 or 9.** Every Linked Inventory value is one or more `EX-NNN` (employment, Section 8) or `PR-NNN` (independent/volunteer, Section 9) IDs that exist in the inventory. Multi-value separated by ` | `. Builder validates each ID exists at audit time.
- **Linked Inventory is required and non-empty.** Per `career-narratives-schema` (design_decisions.md), Linked Inventory is the retrieval anchor. Empty value is a defect; if no inventory entry substantiates a narrative, escalate to user (either add the missing inventory entry or remove the orphan narrative).
- **Multi-value reference list delimiter: ` | ` (space-pipe-space).** Applies to Role, Linked Inventory, and document-header `**Used by:**`. Comma is reserved for tag-list fields (Impact value-type prefix, etc.) per `design_decisions.md` precedent. Decision recorded 2026-05-12.
- **Validator script (deferred).** Per `career-narratives-schema` stale-link mitigation: builder skill includes a grep-based validator that compares narrative Role/Linked Inventory IDs against inventory IDs and surfaces missing refs at audit time.

**2026-05-12 audit results:** all 15 narratives pass all rules. Verified: ID sequences contiguous (ST-001/010, DC-001/005); all 8 distinct RL refs and all 39 EX/PR refs resolve to existing inventory entries; delimiter format uniform; Linked Inventory populated on all entries.

## 3. Content Completeness

- **Stories use the `story_personal` framework template (13 sections, fixed order).** Required sections, in order: `Situation`, `Baseline`, `Task`, `Action`, `My Role`, `Thinking`, `Tradeoff`, `Constraints / Mitigation`, `Outcome`, `Value Translation`, `Scale`, `Learnings`, `Application`. Section heading text exact; case-sensitive; no abbreviations (e.g., "Constraints / Mitigation" not "Constraints").
- **Decisions use the `decision_adr` framework template (7 sections, fixed order).** Required sections, in order: `The Decision`, `The Context`, `The Options and What Each Cost`, `My Criteria`, `My Reasoning`, `Resistance`, `The Outcome`. Per `career-narratives-schema` (2026-05-12 revision): `Who Pushed Back` renamed to `Resistance`; `What I'd Own Differently` dropped (purely reflective; no replacement).
- **Empty sections retained with `Not applicable` placeholder, not blank.** Per `career-narratives-schema`: when a framework section has no content for a specific narrative, populate with a single bullet `- Not applicable` rather than leaving the heading empty or deleting the section. Preserves structural uniformity for retrieval and parsing.
- **Section heading H3 level.** Every framework section heading uses `### <Name>`. Sub-content as bullets with standard markdown indentation (`- ` top-level, `  - ` sub-bullet).
- **Section ordering uniform within framework.** Stories' 13 sections appear in the order above on every entry; decisions' 7 sections likewise. Builder validates ordering at audit time and reports any deviation.
- **Stories include `Learnings` and `Application` even when sparse.** Per 2026-05-12 read-through audit of Duke CRI entry (originally missing Learnings/Application): the framework requires both; absence is a defect, not an option for "thinner" entries. Populate with `Not applicable` if no content.

**2026-05-12 audit results:** all 15 narratives pass framework template checks. Duke CRI entry's 5 originally-missing/empty sections were filled with `Not applicable` placeholders during Phase B / read-through phases of the migration.

## 4. Cross-Entry Consistency

- **Section heading text identical across entries within a framework.** Already enforced in §3. Captured here for cross-entry uniformity reasoning: a story's `Constraints / Mitigation` heading must match every other story's `Constraints / Mitigation` exactly (no `Constraints` alone, no `Constraints/Mitigation` without spaces, no case variation).
- **Constraints / Mitigation pair format uniform.** Pattern: `- <Problem statement>` (top-level, no terminal period), `  - Mitigation: <Mitigation statement.>` (sub-bullet, prefix `Mitigation:`, first letter of mitigation content capitalized, terminal period). When multiple mitigations exist for one problem, each gets its own `Mitigation:`-prefixed sub-bullet. Per Phase B finding (2026-05-12 migration).
- **Acronym convention: introduce full form at first use per entry, abbreviate thereafter — OR use full form throughout.** Each narrative entry stands alone for retrieval purposes; consumers cannot count on having seen the full form earlier. Acceptable patterns:
  - Pattern A (introduce-then-abbreviate within entry): "Data Management Sciences (DMS)" on first mention, then "DMS" subsequently within that entry.
  - Pattern B (full-form throughout entry): "Data Management Sciences" every time.
  - Defect: mixing full form and abbreviation within one entry without an initial introduction.
- **Mood/tense uniform within a single section.** Within one `Learnings` (or any) section of one narrative, bullets share mood: all conditional ("Would..."), all present-tense rules ("Iterative design can slow..."), all imperative ("Map out..."), or all past observation. Mixing moods within a single section is a defect. Different sections across the file can use different moods as appropriate to content.

**2026-05-12 audit findings:**
- F-4.1: DMS / Data Management Sciences usage inconsistent across entries. Stories favor full form; Decisions favor abbreviation. Within DC-001 specifically, "DMS" appears multiple times with no first-mention full-form introduction in that entry. Resolve per acronym convention.
- F-4.2: ST-001 Learnings (lines 134-140) mixes conditional ("Would invest...", "Would segment...") and imperative ("Map out...", "Utilize..."). Normalize to one mood per Learnings section. User call: conditional fits "what I'd do differently" framing; imperative fits rule-of-thumb framing.

## 5. Cross-Document Consistency

- **Narrative quantitative claims substantiated by linked inventory.** Every number (percentage, headcount, dollar amount, count, date, duration) asserted in a narrative must appear in (or be derivable from) at least one entry listed in that narrative's `Linked Inventory:` field. Builder grep-checks numeric claims at audit time and surfaces any unsubstantiated number for resolution: substantiate by adding to inventory, soften the narrative claim (e.g., remove the specific figure), or escalate as a fabrication risk per `feedback_no_fabricated_facts`.
- **Narrative qualitative claims thematically align with linked inventory.** Narrative content describing what was done should be supported by linked inventory entries' Descriptions / Impact / Context. Direct contradictions are defects. Builder semantic-check at audit time.
- **No orphan narratives.** Every narrative must have a non-empty `Linked Inventory:` value pointing at at least one EX/PR entry. Already enforced in §2; surfaced again at the cross-doc level because the implication for retrieval is: a narrative with no inventory anchor has no axis grounding (Industry, Specialty, Orientation, Level, Work-state inherit from Linked Inventory at consumption per `career-narratives-schema`).
- **No orphan inventory references.** Every `Role: RL-NNN` and `Linked Inventory: EX/PR-NNN` in narratives must point at an existing entry. Already enforced in §2; surfaced again because cross-doc drift can re-introduce stale refs over time.
- **Title and label consistency.** When a narrative names an entity (employer, partner, system, project) by name, the same entity should be referenced by the same name string in linked inventory. Builder cross-checks entity names at audit time.

**2026-05-12 audit findings:**
- F-5.1: "$100K annual cost savings" claim (ST-003 Outcome; DC-004 Context and Options) not substantiated by any linked inventory entry. EX-046 describes the LLX cost reduction qualitatively without dollarizing.
- F-5.2: "Over 10 new studies eventually onboarded" (ST-002 Scale) and "External CRO managed four pivotal program studies" (ST-002 Scale) not specifically counted in linked inventory entries (EX-133 references "all new studies" + "2 existing studies" without listing the rollout count).
- Other quantitative claims verified consistent: "200+ data transfers" (ST-003↔EX-041), "$65K / $15K" (ST-006↔EX-150), "238 global sites / 30+ PI specialty categories" (ST-008↔EX-076), "5 roles / 30+ FTE/contractors" (ST-004↔EX-171).

## 6. Content Quality

- **Bullets are grammatical complete thoughts; sentence fragments acceptable.** Narrative bullets are not required to be complete sentences. Fragment style ("Developed capability.", "Led the team.", "Drove change management.") is the convention, parallel to inventory Description style.
- **Tense: past tense for events; present tense for general statements.** Past for what happened (e.g., "Created a novel..."); present for generalizations and rules of thumb ("Specialization can mitigate risk..."). Future/conditional for Learnings phrased aspirationally ("Would invest more in change management...").
- **No em-dashes (— or ---) in any field.** Per global writing-style rule and prior audit (2026-05-12 em-dash sweep). Use periods, semicolons, parentheses, conjunctions, or rewrite. Document `design_decisions.md` and `design/inventory_builder_quality_checks.md` §4 apply identical rule.
- **No Pandoc artifacts.** No `[Name]{.underline}` syntax, no ` ```{=html} ` fence blocks, no `\'` / `\"` / `\$` escape backslashes. Per the 2026-05-12 cleanup.
- **Voice: hybrid acceptable, framework-aware.** Stories (`story_personal`) and Decisions (`decision_adr`) tolerate different voice patterns by section:
  - `Situation`, `Baseline`, `Task`, `Outcome`, `Value Translation`, `Scale`: implicit first-person or descriptive third-person dominant. Past tense for events.
  - `Action`, `My Role`: implicit first-person dominant ("Created...", "Led...", "Developed..."). Subject is the user; first-person pronoun typically omitted.
  - `Thinking`, `Tradeoff`, `My Reasoning`, `My Criteria`, `Resistance`: explicit "I" allowed and common; reflective voice. "We"/"our" allowed when describing team or organizational context.
  - `Learnings`, `Application`: conditional/aspirational ("Would invest more...") or imperative ("Map out potential resistance...") both occur; prefer consistency within a single entry.
- **Internal numerical consistency.** Quantitative claims used in multiple sections of one narrative must agree. Common defect: Baseline says "50-60%" but Outcome says "approximately 50%". Builder validates at audit time that paired numbers (baseline-outcome, before-after, count claims) are mutually consistent.
- **Cross-document numerical consistency.** Quantitative claims in a narrative must agree with the same claims in linked inventory entries (`Linked Inventory: EX-NNN | ...`). Numbers (percentages, headcount, counts, dollar amounts) authored independently in narrative vs inventory drift over time; builder validates against linked inventory at audit time.
- **No fabricated specifics about user's history.** Per `feedback_no_fabricated_facts` memory rule: employer names, role titles, dates, headcount numbers, dollar amounts, count claims must verify against `Experience_Inventory.md` Section 7 (RL records) and the substantive entries (EX/PR). Builder grep-checks named facts in narratives against inventory records; surfaces inconsistencies.
- **No line-management framing.** Per `feedback_no_line_management_experience` memory rule: user has no direct line-management experience; all leadership is operational matrix management. Builder applies same framing rules as inventory `§4`: avoid "Managed" applied to people/teams (use "Operationally led" / "Directed"); avoid "held accountability for individual performance" (use "operational accountability for team delivery"); avoid "without holding direct line management" as a contrast vocabulary signal.
- **Reference clarity in Application section.** `Application` bullets begin with the lesson/approach being applied, not a pronoun referring back. "Applied these when building X" (vague) → "Applied this segmentation approach when building X" (concrete). Each Application bullet should be self-contained: future reader of just that bullet should understand what was applied.

**2026-05-12 audit findings:**
- F-6.1: ST-001 Action sub-list (lines 64-74) not indented; missed during Pattern 1a sub-list nesting sweep because parent has mid-sentence colon, not standalone introducer. Logged for Cat 1 fix.
- F-6.2: ST-004 Situation sub-list (lines 408-412) not indented; missed because parent ends with period not colon. Logged for Cat 1 fix.
- F-6.3: ST-001 Learnings mixes conditional ("Would invest...") and imperative ("Map out...") moods. Logged for Cat 4.
- F-6.4: ST-001 Application "Applied these when..." has vague antecedent. Rewrite to "Applied these learnings when..." or similar.
- F-6.5: ST-002 Baseline ("50-60%") and Outcome ("approximately 50%") internally inconsistent. Linked EX-133 says "~60%". Reconcile to a single value.
- No fabricated specifics found in 2026-05-12 spot-check of ST-001, ST-002, ST-006, DC-001 against linked inventory entries. Comprehensive validation deferred to builder skill implementation.
