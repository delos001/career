# Career Repo Design Decisions

Closed decisions only. Deferrals: `deferrals.md`. Open questions: `open_questions.md`. Cross-references slug-based. Session protocol in memory `process_session_protocol.md`.

## Cross-Cutting

### Architecture & Conventions

#### pattern-a-framework-native
Use Claude Code's official extension points. Skills at `.claude/skills/[name]/SKILL.md`, agents at `.claude/agents/[name].md`, both with YAML frontmatter. Auto-discovered. No custom skill_registry, no control.md dispatcher. `.claude/` travels with the repo.

#### top-level-containers
`.claude/`, `rules/`, `templates/`, `scripts/`, `outputs/`, `personal/`. Plus `CLAUDE.md` at root. Skills and sub-agents live inside `.claude/`.

#### scripts-centralized
Top-level `scripts/`, subdivided internally (retrieval, resolvers, format conversion). Not co-located with consumers; many scripts called by multiple consumers.

#### file-and-folder-naming
Folders: lowercase kebab-case. No underscores.
Files: lowercase. Underscore between semantic fields; kebab within a field. Compound document-type tokens count as one field.
Examples: `pfizer-001_session-log.md`, `gap-analysis_pfizer-001.md`, `interview-followup_r1_pfizer-001.md`. Attention files and ADRs are exceptions.

#### attention-files
All-caps signals "read me first." Applied set: `README.md`, `SETUP.md`, `COMPONENTS.md`. Future attention-tier files inherit capitalization.

#### adr-naming
MADR convention: zero-padded three-digit prefix + kebab-case title. Sequential, never reused. Supersession is a new record. Example: `001-base-overlay-pattern.md`. Location: `docs/decisions/` at formalization.
Refs: `adr-formalization-timing` (deferral).

#### orientation-file-names
Drop numeric prefix. Files in `rules/orientations/`: `transformation-strategy.md`, `data-analytics.md`, `process-operations.md`, `platform-technology.md`. Retrieval scripts look up by descriptive name.

#### level-file-names
Drop deliverable prefix. `ic.md` and `leadership.md`. Folder path provides context.

#### terminology-phase-skill-workflow
Phase = step within a single skill. Skill = one standalone skill. Workflow = project-level flow across skills. Phase reserved for sub-skill granularity.

#### template-vs-format-spec
Templates are physical carrier files (e.g., Word) that get filled in. Format specs are structural/rendering rules applied to free-form content.

### Composition Model

#### five-orthogonal-axes
- **Orientation** (renamed from prior Specialty / Archetype): governs deliverable structure. `rules/orientations/`. Values: transformation-strategy, data-analytics, process-operations, platform-technology.
- **Industry**: sector. Vocabulary, dialect, regulatory framing. `rules/industries/`. Values: pharma authored; others as built.
- **Specialty** (renamed from prior Skill): professional field of practice. Capability vocabulary and field-specific framing. `rules/specialties/`. Values: clinical-operations, data-engineering, ai-engineering, quality-compliance, people-leadership, data-science, operations-strategy. Extended 2026-05 per `specialty-axis-extension-data-science-operations-strategy-2026-05`.
- **Level**: IC vs leadership. Voice and scope framing. `rules/levels/`.
- **Work-state**: operating state of the work environment. `rules/work-states/`. Values: greenfield, scaling, mature, turnaround, post-merger-integration, divestiture, pivot.

Industry/Specialty split replaces prior Domain axis. Axes are independent files. Overrides only where axes genuinely interact, narrow rules not mini-archetypes. Each axis is a discrete categorical dimension; partial-match scoring runs through the adjacency map in each value's frontmatter.

#### dual-orientation-asymmetric-authority
A role may map to two orientations. Primary governs most surfaces; secondary gets bounded explicitly-scoped slots. They do not compete over the same surface.
- CV: secondary in 2-3 achievements and 1-2 Core Competencies items. Summary primary-only.
- Other deliverables: per-deliverable composition rule as needed.
Existing CV dual-orientation rule transfers to `rules/orientations/cv_dual_orientation_composition.md`.

#### inventory-entry-multi-value-orientation-2026-05
Orientation on EX/PR inventory entries supports multi-value primary/secondary via pipe-delimited convention (`Orientation: <primary> | <secondary>`), extending `dual-orientation-asymmetric-authority` from CV-level to inventory-level.
- First-position = primary; second = secondary. Same asymmetric-authority semantics propagate to downstream CV composition.
- Each tag independently substantiates per `rules/orientations/<value>.md` vocabulary; un-substantiated values get dropped rather than force-fit.
- Use only when work substantively carries both shapes; not a hedge against tag ambiguity.
- Retrieval: each tag is an independent supplemental tag-pull trigger per `cv-targeted-retrieval-architecture-2026-05`. Single-tagging dual-shape work creates retrieval false negatives, blast radius amplified for thin work histories or thin topic coverage.
Refs: `dual-orientation-asymmetric-authority`, `cv-targeted-retrieval-architecture-2026-05`, `cv-targeted-hybrid-retrieval`.

#### level-axis-two-buckets
IC and leadership only today. Expansion via `level_builder`. Level files are deliverable-agnostic; deliverable-specific concerns belong in the deliverable's format spec.
Refs: `level-axis-finer-grained-files`, `level-builder-design` (deferrals).

#### axes-composition-precedence
Each axis owns a primary surface for cv_targeted composition:
- **Orientation** → Section structure, Section emphasis, Summary lead framing.
- **Level** → Voice, verb selection, scope framing within bullets.
- **Specialty** → Capability vocabulary, field-specific terminology, capability surfacing in Professional Experience.
- **Industry** → Sector vocabulary, dialect (acronym recognition, non-preferred terms), sector-emphasis signal.
- **Work-state** → Achievement framing (signal verbs, before/after framing, off-spec patterns) within bullets.

Default conflict resolution: orientation governs structure; other axes govern content within that structure. The more-specific axis wins within its surface — specialty terminology supersedes industry vocabulary in capability descriptions; industry dialect supersedes specialty terminology for sector-recognized acronyms.

Surface ownership is the default precedence, not absolute authority. cv_targeted may implement cross-axis review or challenge mechanisms (e.g., per-axis sub-agents proposing content for their owned surface and reviewing peers' outputs) where converged outputs override default precedence. Mechanism deferred to cv_targeted skill design.

Refs: `five-orthogonal-axes`, `cv-targeted-content-rules-from-axes`, `cross-axis-composition-mechanism` (deferrals).

#### role-evaluation-axis-matching-protocol
role_evaluation matches a JD to each axis by axis-specific mechanism:
- **Framing axes** (orientations, work-states, levels): match via Identity + Selection rule. Read the JD, apply the rule, pick the value.
- **Vocabulary axes** (industries, specialties): match via vocabulary/terminology overlap against the file's existing data sections — Vocabulary + Dialect + Emphasis for industries; Capability vocabulary + Terminology for specialties.

The asymmetry reflects the matching task. Framing decisions require interpreting the JD's primary deliverable, scope, or organizational state (rule-driven). Vocabulary matches resolve via signal overlap (count-driven). Disambiguation between adjacent values within an axis falls to Adjacency rules + JD context.

Refs: `axes-composition-precedence`, `five-orthogonal-axes`, `role-evaluation-orientation-selection-from-axes` (deferral).

#### specialty-axis-tagging-by-work-nature
Specialty tags on inventory and narrative entries reflect the nature of the work performed, not the role's title or formal classification. An entry tags every specialty whose work was meaningfully present, regardless of whether the role was titled with that specialty.

Other axes (industry, orientation, level, work-state) tag by role context — the role's industry, primary deliverable, scope of authority, and organizational state respectively. Specialty is the exception because field-of-practice work can genuinely span within a single role; the other axes describe role-level attributes that do not span within a single role.

Rationale: titles in the wild are unreliable signals (Data Scientist, ML Engineer, Data Engineer overlap; titles drift by company and era). Work-nature tagging trades precision for recall at the inventory level. Precision is recovered at retrieval time when cv_targeted and role_evaluation rank entries by JD relevance.

Refined by `specialty-axis-training-as-specialty-work-2026-05` (training delivery on a specialty's content counts as specialty work in knowledge-transfer mode, with concurrent-doing qualifier).

Refs: `experience-inventory-domain-scoping`, `five-orthogonal-axes`, `specialty-axis-training-as-specialty-work-2026-05`.

#### specialty-axis-training-as-specialty-work-2026-05
Refines `specialty-axis-tagging-by-work-nature`. Training delivery on a specialty's content is specialty work performed in knowledge-transfer mode, tagged with the trained specialty, when the trainer also performs specialty-doing work in the role. Pure learning-and-development delivery (where the role is content rebroadcast without concurrent practice of the specialty) tags `people-leadership` for change leadership but not the trained specialty.

Rationale: symmetry with content authoring (already specialty-tagged via the work-nature rule when authoring SOPs, controlled documents, etc.). Training delivery exercises the same specialty knowledge as the doing, just in a knowledge-transfer mode. The "concurrent specialty doing" qualifier protects the rule from over-extending into pure L&D situations where the trainer is not a practitioner of the specialty being trained. The pure-L&D edge case is not present in the user's current inventory but the qualifier keeps the rule durable.

Driven by inventory retag against the extended 7-specialty axis (2026-05): four entries (EX-185, EX-199, EX-200, EX-201) sat at the boundary because they were Infosario Business Champion role training/adoption work; removing `people-leadership` left only `clinical-operations`, which understated the change-leadership delivery axis. Independently, the user surfaced that training delivery on specialty content materially exercises the specialty. Both observations resolved by this rule plus reinstating `people-leadership` on those entries via the change-leadership capability already codified in `rules/specialties/people-leadership.md`.

Knock-on retags applied 2026-05 under this rule:
- EX-016, EX-030 (training on GCP / regulatory): ADD `quality-compliance`.
- EX-183 (GitHub adoption training): ADD `data-engineering`.
- EX-184 (CSM adoption change management): ADD `people-leadership` (change leadership).
- EX-188 (Excel Pivot table training): ADD `data-science`.
- EX-189 (ELVIS regulatory compliance training): ADD `quality-compliance`.

Refs: `specialty-axis-tagging-by-work-nature`, `specialty-axis-extension-data-science-operations-strategy-2026-05`, `rules/specialties/people-leadership.md`.

#### specialty-knowledge-transfer-section-applied-2026-05
Added `## Knowledge-transfer mode` section to all 7 specialty files (ai-engineering, data-engineering, data-science, quality-compliance, operations-strategy, clinical-operations, people-leadership), placed between `## Terminology` and `## Adjacency`. Section content identical across all 7 files:

> - Training delivery, curriculum design, and adoption coaching on this specialty's capabilities, methods, tools, or artifacts, when concurrently practicing the specialty in the role.

`axes-file-schema` amended in parallel: specialty body sections list updated to "Capability vocabulary, Terminology, Knowledge-transfer mode, Adjacency."

Driven by audit gap: `specialty-axis-training-as-specialty-work-2026-05` codified the substantiation rule but specialty rule files lacked corresponding file-level vocabulary. Taggers had no rule-file evidence to substantiate against when tagging training entries; future inventory builder runs would have no rule signal to apply the rule programmatically.

Wording chosen generically: references "this specialty's capabilities, methods, tools, or artifacts" rather than enumerating specific items. Auto-tracks future Capability vocabulary and Terminology refreshes; specific enumerations would drift out of sync over the 9-month staleness cycle (`rule-staleness-threshold`).

Placement chosen as separate section over appended bullet inside Capability vocabulary: (1) honors the conceptual mode distinction codified in the original rule (knowledge-transfer mode vs doing-work mode), (2) discoverability via dedicated heading rather than trailing bullet in a long list, (3) forward-compatibility: section absorbs future knowledge-transfer-mode additions (e.g., documentation authoring on specialty content) without restructuring.

Schema variation rationale: rule applies only to specialty axis. Industries are sector context (no trainable knowledge corpus), Levels and Work-states are framing (no trainable content), Orientations are operational posture (not knowledge bodies). Adding parallel sections to other axis files would be empty-section bloat. Per-axis schema variation is principled when an axis-specific rule requires it.

Refs: `specialty-axis-training-as-specialty-work-2026-05`, `axes-file-schema` (amended in this decision), `rule-staleness-threshold`, `specialty-axis-tagging-by-work-nature`.

#### rl-allocation-field-schema-2026-05
Section 7 RL records carry a required `Allocation: <percentage>%` field capturing fraction of one FTE on the role at its most current (steady-state) value. Defaults to `100%` for full-time roles. Partial roles carry user-provided values: RL-008 (20%, Infosario Business Champion concurrent within Quintiles primary), RL-012 (20%, CSM Deployment Lead concurrent within Amgen primary), RL-013 (80%, Global CTM concurrent), RL-016 (10%, RBM Software Consultant freelance side-engagement). Cross-employer overlapping roles are not constrained to sum to 100% (freelance time is additive on top of primary). Stacked same-employer roles (concurrent layered titles at the same company, e.g., RL-018/019/020 at BioMarin) report each role's allocation just before transition or end, not the historical split during overlap. Required on Background Roles for schema consistency.

Rationale: prior per-RL density math used raw tenure-months as denominator, producing false-sparse signals on partial-allocation roles. Allocation field makes the density rule operable across real-world tenure variations (concurrent partial-time assignments, freelance overlaps, stacked-title transitions). Enables `effective FTE-months = tenure-months × Allocation/100` formula in QC §5.

Applied to all 20 RL records; partial-allocation roles validated via subsequent density check.

Refs: `experience-inventory-section-7-flat-records`, `design/inventory_builder_quality_checks.md`.

#### axes-file-schema
Each axis carries a distinct file schema reflecting its purpose per `axes-composition-precedence`:

- **Industries** (`rules/industries/<value>.md`): frontmatter (industry, last_researched) + body sections: Vocabulary, Dialect, Emphasis, Adjacency.
- **Specialties** (`rules/specialties/<value>.md`): frontmatter (specialty, last_researched) + body sections: Capability vocabulary, Terminology, Knowledge-transfer mode, Adjacency.
- **Orientations** (`rules/orientations/<value>.md`): frontmatter (orientation, last_researched) + body sections: Identity, Summary lead, Section emphasis, Adjacency.
- **Levels** (`rules/levels/<value>.md`): frontmatter (level, last_researched) + body sections: Identity, Voice, Verb vocabulary, Scope signals, Adjacency.
- **Work-states** (`rules/work-states/<value>.md`): frontmatter (work-state, last_researched) + body sections: Identity, Achievement framing, Adjacency.

All axis files carry a `**Used by:**` metadata header below the title per `document-metadata-header-discipline`.

The `## Adjacency` section in every axis enumerates the relationship between this value and every non-self entry in the same axis's registry. Two forms are permitted within the section, used in combination:

- **Substantive bullets** for siblings that carry a translation rule. Format: `- **<sibling>**: <translation rule>.` These are the bullets cv_targeted reads to translate work across adjacent values.
- **Mandatory terminal sub-section `### Low or no adjacency`** for siblings that have no translation logic worth stating (the candidate either holds both tags or does not, and the axis files have nothing more to say). Format: plain bulleted list of value names, one per line: `- <sibling>`. No bolding, no translation prose. The sub-section is always present in every value file, even when no siblings qualify; when empty, the body is the single placeholder line `_(none)_`. Mandatory presence signals "considered and none" rather than "forgotten or absent" and makes future low-adjacency additions pure-append rather than create-the-section-first.

Every non-self registry entry must appear in exactly one of the two forms. Missing from both is the QC failure case (E1).

Rationale: fully enumerating every sibling as a substantive bullet bloats Adjacency sections as an axis grows, and most sibling pairs in a typical axis carry no real translation logic (the bullets restate "co-tags only when both held" in different prose). Pure omission of weak siblings creates ambiguity between "considered weak" and "forgotten." The two-form rule preserves the audit trail (every sibling appears somewhere) without paying full-bullet cost for non-translating pairs.

**Industries' `## Dialect`** carries a mandatory `### Acronyms` sub-section containing the catalog of acronyms recognized without expansion in the industry's hiring contexts. Catalog format: one comma-separated paragraph, optionally split into two when distinguishing inherited versus domain-specific acronyms. Voice prose (style, cadence, posture) stays in Dialect's main body, above the sub-section. The H2 acronym-reconciliation QC check (scripts/axis_qc.py) uses the sub-heading as the catalog boundary; text above the sub-section is treated as body usage rather than as catalog content. Industries are the only axis whose schema currently includes Dialect; other axes have no acronym catalog and no parallel sub-section.

Per-section content authoring guidance (what each section should contain, depth expectations, framing rules) is per-axis-builder design territory and deferred to those skills.

Refs: `axes-composition-precedence`, `document-metadata-header-discipline`, `foundation-execution-order`, `adjacency-graph-fully-connected-rule-revisit` (deferral closed by this amendment).

#### skill-stability-loose-coupling
Skills reference rules by category/slug. Resolver script looks up the current file. Skill body does not hard-code paths.

#### retrieval-method-pure-tag-based
Every retrievable inventory entry tagged on every applicable axis (Industry, Specialty, Orientation, Level, Work-state). Pure tag-based as default retrieval mechanism; semantic retrieval can layer on later if cv_targeted needs it. Tagging is reversible; deferring foundation completion is not. Resolves the open question `retrieval-method-for-discrete-elements`.
**Superseded by `cv-targeted-retrieval-architecture-2026-05`.** Prototype testing on two real JDs (one off-corpus-center, one on-corpus-center) showed pure tag-based filtering reduced recall by excluding legitimately translatable entries — particularly IC-level entries with description text matching the JD when the target role was leadership. Semantic retrieval over Description text became the primary path; tags retained for composition-time framing and supplemental tag-pull driven by role_evaluation matched axis values.

#### cv-targeted-retrieval-architecture-2026-05
cv_targeted retrieval is a two-pass hybrid:
1. **Primary pass (semantic on Description):** Pre-extracted Description-only payload (one line per EX-NNN/PR-NNN with ID + Description text) ranked by semantic relevance to the JD. Returns a list of candidate IDs. Cheap on context (description-only is roughly one quarter the size of full entry blocks).
2. **Supplemental pass (tag-pull):** role_evaluation produces matched axis values for the JD. Those matched values drive targeted tag-pulls of inventory entries whose tags signal what their descriptions undersell (an entry whose description reads "designed accountability frameworks" doesn't say "this is governance work"; tags do). Specialty and Orientation are the natural supplemental triggers because they capture the kind-of-work; Level and Work-state are framing axes (used at composition, not retrieval). Industry weights ranking but rarely needs a hard supplemental pull.
3. **Merge and dedup** the two candidate sets. Full entry detail is loaded only for the merged candidate set.

Tags become composition-time data, not retrieval filter:
- **Inclusion:** semantic on Description text, supplemented by JD-driven tag-pulls. Tag filter is dropped.
- **Ranking:** semantic relevance score plus optional Industry/Specialty match weight.
- **Framing:** Level / Orientation / Work-state on each entry drive voice-translation rules at bullet composition time per the axis files.

Rationale: prototype testing showed (b) pure-semantic outperformed (a) tag-filter-plus-semantic on inclusion in both off-corpus-center (Insmed commercial data acquisition) and on-corpus-center (AstraZeneca process management) JDs. JDs vary too much for a fixed tag filter to handle edge cases. Semantic retrieval addresses the variability; tag supplements address the descriptions-undersell problem.

Supplemental tag selection is dynamic, not static — driven by role_evaluation's axis-matching output rather than a fixed "always pull Specialty + Orientation" rule. The matched axes for the role tell us which tags should trigger supplemental pulls for that role.

**Superseded by `retrieval-architecture-2026-05`.** Prior design framed retrieval as part of cv_targeted; new design separates retrieval into its own skill serving multiple downstream consumers, uses critical requirements (not raw JD) as the LLM-judgment matching target, adds adjacency-aware axis scoring, adds an independent narrative semantic pass, and locks LLM-judgment (not RAG) as the semantic mechanism.

Refs: `competency-registry-runtime-value` (resolved here), `cv-targeted-hybrid-retrieval` (deferral, reshaped), `role-evaluation-axis-matching-protocol`, `axes-composition-precedence`, `cv-targeted-content-rules-from-axes` (deferral).

#### retrieval-architecture-2026-05
Retrieval is a standalone skill that runs after role-intake and serves multiple downstream consumers (gap analysis, CV creation, interview prep, career brief). It produces a single manifest at `personal/applications/<SLUG>_APP-NNN_YYYY-MM/retrieval.md` containing scored references to inventory entries, narratives, and triggered themes. Manifests do not embed full content; downstream consumers fetch entry bodies via `scripts/profile_slice.py` on demand.

**Inputs (read from role-intake outputs):**
- Critical requirements list (from `research.md`; see `role-intake-critical-requirements-extraction-2026-05`).
- Axis classification (from the session log).
- JD text (from `jd.md`).

**Three parallel retrieval passes; results unioned into the manifest:**

1. **Inventory semantic pass (LLM-judgment, chunked).** EX/PR corpus split into chunks of approximately 50 entries each. Each chunk sent to Claude alongside the critical requirements list, with payload format `EX-NNN: <Description + Impact concatenated>`. Returns semantic score (0-1) plus one-line reason per entry. Chunking mitigates attention degradation that affects ranking long lists in a single prompt. Cost scales linearly with corpus size: one LLM call per chunk.

2. **Inventory tag-pull pass (deterministic).** For each axis in the JD classification, include every EX/PR entry whose tag for that axis is an exact match OR an adjacency-match per the axis file's Adjacency section. Inclusion criterion: N≥1 axes (single-axis floor). Broad recall preserves the "no false-positive gaps" goal in downstream gap analysis.

3. **Theme semantic pass (LLM-judgment).** Each Signature Theme (`TH-NNN`) in `positioning.md` is scored against the critical requirements list. The LLM sees `Core message` + `Proof point` + `Use when:` triggers concatenated as the theme description (OR semantics: any one field can justify triggering). Score 0-1 with one-line reason.

**Narrative retrieval — two-signal:**
- Deterministic Linked-Inventory walk: every narrative (`ST-NNN`, `DC-NNN`) whose `Linked Inventory:` references any inventory entry already in the manifest is included.
- Independent semantic pass: every narrative is also scored by LLM-judgment against the critical requirements list, providing an arc-level relevance signal independent of inventory linkage.
A narrative may carry either signal alone or both. Both are reported in the manifest.

**Manifest exposes raw signals; downstream consumers derive tiers locally.** No pre-computed `strong/moderate/weak` tier at retrieval time. Per-entry signals exposed:
- semantic score (float 0-1) from the LLM-judgment pass.
- axis exact-match count (int 0-5) against JD axis classification.
- axis adjacency-weighted score (float; exact match = 1.0, adjacent match per axis file = 0.5 default, axis file Adjacency section can override).
- match evidence: which axes matched, which adjacency rules fired, LLM-generated free-text reason.

Downstream consumers (gap analysis, CV creation, interview prep) apply their own tier cutoffs locally because "strong coverage" (gap analysis) and "primary bullet candidate" (CV) are different questions and a baked-in retrieval-time tier forces them into the same cuts.

**Scope boundaries:**
- Sections 1-6 of inventory (reference content: education, certifications, training, technical experience, industry exposure) are OUT of retrieval scope. Downstream skills read these directly via `scripts/profile_slice.py` when a JD requirement names a specific qualification.
- Positioning scope limited to Signature Themes. Other positioning sections (Core Philosophy, Experience Profile, What Makes Me Unique, Positioning Statement) are voice/framing content; downstream skills load them whole when needed.

**Semantic mechanism: LLM-judgment, not RAG.** The inventory corpus and per-application retrieval workload are well below the scale at which RAG infrastructure (embedding model, vector store, re-indexing on inventory edits) is the right architecture. LLM-judgment via the existing Claude integration is simpler, has stronger nuance handling on cross-domain phrasing (e.g., "regulatory readiness" against "FDA compliance posture"), and avoids stale-embedding risk on inventory edits. Tradeoff: scores may shift slightly across Claude model upgrades; reproducibility within a session is sufficient and retrieval is re-runnable on demand.

**Supersedes `cv-targeted-retrieval-architecture-2026-05`.** Prior design framed retrieval as part of cv_targeted. New design separates retrieval into its own skill serving multiple consumers, uses critical requirements (not raw JD) as the matching target, adds adjacency-aware axis scoring, adds the narrative independent semantic pass, and locks LLM-judgment as the mechanism.

Resolves deferrals: `cv-targeted-hybrid-retrieval` (implementation details specified by this design), `axis-adjacency-weights-redefinition` (adjacency weights drive retrieval ranking and downstream tier derivation; per-axis-file Adjacency text remains authoritative).

Refs: `cv-targeted-retrieval-architecture-2026-05` (superseded), `role-intake-critical-requirements-extraction-2026-05`, `experience-inventory-domain-scoping`, `career-narratives-schema`, `axes-composition-precedence`.

#### arc-composition-for-high-impact-roles
Atomic inventory entry structure enables broad JD matching and retrieval recall. Roles requiring high-level, enterprise-scope proof points need the composition layer to synthesize related entries into unified achievement arcs rather than treating each as an independent bullet.

Mechanism: narratives (ST-NNN entries with Linked Inventory fields) are the primary composition unit when a role's scope requires arc-level proof points. Atomic EX entries surface as supporting detail beneath the arc claim, not as parallel top-level bullets.

cv_targeted trigger: when role_evaluation identifies that the JD's primary deliverable language is at enterprise or cross-functional program scope (e.g., "led enterprise initiative," "built and scaled a capability"), the composition pass checks narratives for arcs linking the relevant EX entries before composing individual bullets. An arc claim anchors the achievement; the atomic entries (individual process improvements, governance artifacts, training activities) provide the evidence layer underneath.

role_evaluation trigger: when producing gap analysis, evaluate coverage at arc level first, not entry level. A cluster of related atomic entries that together constitute a high-impact story should be surfaced as a unified arc gap or strength, not as a list of individual entry matches.

Rationale: without this rule, cv_targeted composes atomic bullets that individually undersell scope and collective impact. The hiring panel reads a list of process improvements rather than a transformation story. The inventory is structured atomically for retrieval; the CV must be structured architecturally for persuasion.

Refs: `cv-targeted-retrieval-architecture-2026-05`, `career-narratives-schema`, `role-evaluation-and-cv-targeted-separate`.

#### level-on-entries-effective-level
Level lives only on EX/PR entries (effective level). Captures the pattern of doing higher-than-title-level work within a titled role.
Prior version had Level on both RL-NNN role records (titled level) and EX/PR entries (effective level), with EX/PR defaulting from RL when missing. Removed RL Level after per-entry Level became fully populated on every EX/PR entry: cv_targeted matches JD Level against entry effective level directly; RL Level was never read in retrieval and added no signal. If a future builder skill needs role-level defaulting for new EX entries, the field can be reintroduced.

#### cv-section-structure-professional-vs-earlier-roles
CV experience uses two sections: **Professional Experience** and **Earlier Professional Roles**.

**Professional Experience inclusion rules:**
1. Any role currently active or with an end date within the last 10 years (threshold: current year minus 10).
2. Any older role that directly closes a gap between the candidate's experience and a specific JD competency cluster — but only when that gap would otherwise be unaddressed.
3. If a newer role is included solely to prevent a perceived timeline gap (not for content), it earns 1-2 lines summarizing scope and responsibilities — not detailed bullets.
4. Any role newer than an older rule-2 inclusion must also appear in Professional Experience to avoid a perceived gap between the two sections.

**Professional Experience treatment:**
- Roles with strong JD alignment: full arc-level bullet treatment per role scope.
- Roles included only for timeline continuity (rule 3 above): 1-2 line breadth summary only.
- For transformation-strategy or process-operations oriented applications: operational roles (project management, clinical monitoring, site management) that predate the transformation work belong in Professional Experience if within threshold. They establish operational foundation that validates the transformation arc. Their 1-2 line summary should reflect operational breadth, not JD-cluster matching.

**Earlier Professional Roles:**
All roles outside the threshold that do not meet rule-2. Format: Company | Title | Dates only. No bullets, no descriptions.

**Gap prevention principle:** Readers notice unexplained gaps. Every period of professional activity should be accounted for across the two sections. Concurrent roles (multiple employers simultaneously) should be noted as concurrent; low-allocation side engagements can appear as brief notes. A gap during a documented period (e.g., COVID, full-time study) is preferable to artificially filling it with a role that doesn't belong.

**Traceability constraint:** Every claim in a Professional Experience entry must trace to a specific EX inventory entry or RL role record. Level-elevation language (reframing IC work as director-level framing) is valid only when the inventory entry itself supports the elevated framing — not as a general elevation pass. Claims that cannot be defended in interview are liabilities, not assets.

Refs: `arc-composition-for-high-impact-roles`, `cv-targeted-retrieval-architecture-2026-05`.

### Profile Documents (Schemas)

#### knowledge-document-roster
Four documents: `user-info`, `inventory`, `narratives`, `positioning`. `Questions_Library` eliminated.

#### knowledge-to-profile-rename-2026-05
`personal/knowledge/` folder renamed to `personal/profile/`. The four documents renamed to lowercase: `Experience_Inventory.md` → `inventory.md`, `Career_Narratives.md` → `narratives.md`, `Positioning.md` → `positioning.md`, `User_Info.md` → `user-info.md`. The collective term "knowledge documents" becomes "profile documents". Builder skills renamed to match: `experience_inventory` → `inventory`, `career_narratives` → `narratives`, `knowledge_update` → `profile_update`; the `knowledge-builder` type → `profile-builder`. Scaffolding folder `support/knowledge_repo_scaffolding/` → `support/profile_repo_scaffolding/`.

Rationale: three issues converged. (1) Renaming inventory Section 8 to "Experience Entries" (per `inventory-section-8-rl-grouping-2026-05`) made "Experience_Inventory" collide semantically — the file has ten numbered sections, not just experience. (2) The four documents violated the lowercase rule in `file-and-folder-naming`; they were Title_Case. (3) "knowledge" was a non-descriptive legacy folder name that could not justify one-word filenames; `profile/` describes the content (the four documents collectively are the user's professional profile). Lowercase with the folder path providing context follows the same principle as `adr-naming` (drop deliverable prefix). Three documents reduce to a single word; `user-info` is two words and is kebab-cased, because `file-and-folder-naming` kebab-cases within a field and a compound document-type token is one field (consistent with `gap-analysis`, `session-log`).

Scope boundaries: decision slugs containing "knowledge" (`knowledge-document-roster`, `knowledge-document-scaffolding`, `knowledge-doc-update-mechanism-hand-edit`, `knowledge-update-collapse`) left unchanged as immutable identifiers — only their bodies and the section header updated. The suggested GitHub repo name `career_development_knowledge` left unchanged (repo name, not folder). "Knowledge-transfer mode", "knowledge management", "domain knowledge" are unrelated term uses, untouched.

Apply: folder/file renames via `git mv` (personal repo) and `mv` (gitignored scaffolding); reference updates across 16 files via `scripts/_rename_refs.py` (ordered explicit patterns), plus manual edits to `README.md` and `.claude/settings.local.json`. Per `working-files-deleted-after-apply` the script is deleted; this decision is the durable record.

Refs: `inventory-section-8-rl-grouping-2026-05`, `file-and-folder-naming`, `adr-naming`, `knowledge-document-roster`.

#### user-info-rename-and-schema
Rename `Contact_Info.md` to `user-info.md`.
- Name field source of truth: `user-info.md`. Removed from `personal/config.yaml`. Format_spec rendering script reads name from `user-info.md`.
- Drop "Usage Notes" section per data-only-discipline.
- Metadata header: `**Used by:**` per document-metadata-header-discipline. No Stamps or Generated by.
- Placeholder values in scaffolding template like `[Your Name]`.

Schema (revised 2026-05-04 after two generalization audits; original was single-value-only and lacked Location, profile extensibility, and any fields needed by role_evaluation / interview_prep / interview_followup):
- **Used by:** cv_targeted, cv_general, role_evaluation, interview_prep, interview_followup. user-info holds durable personal data; per-application overrides (situational salary negotiation, role-specific items) live in application files.
- **Identity** section: Name (required), Preferred Name (optional), Pronouns (optional), Name Pronunciation (optional, useful for interview_prep).
- **Location** section: City, State / Region, Country, Time Zone. Split into fields; CV format spec renders the line. Time zone consumed by interview_prep / interview_followup for scheduling and send-timing.
- **Contact** section: Email and Phone as multi-value sub-bulleted lists, each entry labeled (Primary, Work, Mobile, etc.). Schema uniform whether one or many entries.
- **Online Presence** section: unified `Profiles:` labeled list (LinkedIn, GitHub, ORCID, Stack Overflow, Kaggle, Medium, Hugging Face, etc.) plus separate `Websites:` labeled list (Personal Site, Blog, Portfolio). CV format spec privileges LinkedIn/GitHub for contact line by label match; other profiles surface conditionally per CV format rules.
- **Languages** section: bullet list, format `Language — proficiency` (e.g., native, fluent, conversational, basic). Consumed by cv_targeted (CV inclusion when role-relevant) and interview_prep (small-talk anchors, multilingual role fit).
- **Work Authorization** section: Status, Sponsorship Required (Y/N). Consumed by role_evaluation as filter against role's sponsorship policy.
- **Geographic Preferences** section: Modality Preference (Remote/Hybrid/Onsite/Open), Willing to Relocate. Consumed by role_evaluation as fit signal. Travel Willingness intentionally excluded — case-by-case per role, not a static preference.
- **Exclusions** section: Industries / Company Types not under consideration. Consumed by role_evaluation as hard filter.
- Sections intentionally excluded: Availability (notice period, start date) and Compensation (target range, floor) — both change too often and are evaluated case-by-case at application time. They live in per-application files (gap_analysis or equivalent), not user-info.
- All multi-value fields use bullet sub-list pattern; consumers iterate and select by label.
- Sensitive fields (compensation, authorization) acceptable in this file because `personal/` is gitignored.

Parser conventions (markdown is the storage format; structure is regular enough for regex parsing without semantic LLM). Guiding principle: **structure the file for natural human typing; the parser absorbs format variability.** The user does not carry separator conventions in their head; the parser knows how to read what a human naturally writes.

- Section headings: `## Section Name`.
- Single-value field: `**Field:** value`.
- Multi-value field: `**Field:**` header line followed by `- ...` bullets. Per-section rules:
  - **Email / Phone** bullets carry a label that is metadata for CV rendering (Primary, Work, Mobile). Form is `- Label: value`. Parser is tolerant of separator variants (`:`, ` - `, ` — `).
  - **Profiles** bullets are URLs only; parser auto-detects platform from URL domain (`linkedin.com` → LinkedIn, `github.com` → GitHub, `orcid.org` → ORCID, etc.). Labeled form (`- LinkedIn: <url>`) also tolerated for users who prefer it.
  - **Websites** bullets follow the same pattern as Profiles (URL-only, parser identifies category by domain heuristic or accepts user label).
  - **Languages** bullets are freeform strings displayed as-is in CV (e.g., `- English (native)`). No required separator structure.
  - **Exclusions** bullets are freeform strings.
- Empty marker is forgiving: parser accepts `none`, `*(none)*`, `(none)`, `n/a`, blank-after-colon. All map to null. Recommended canonical form is bare lowercase `none` but not required.
- Scaffolding placeholders: `[bracketed]` form (e.g., `[Your Name]`, `[Yes / No]`). Parser treats any `[...]`-enclosed content as unfilled and emits warnings if encountered at consumption time.
- Multi-value field with no entries: single bullet `- none` or any tolerated empty marker.

Tolerant-parser principle applies file-wide and to other profile documents where format conventions exist. Move cognitive burden off the human (every edit) onto the parser implementation (once).

#### career-narratives-schema
Schema (revised 2026-05-12: Era replaced with `Role: RL-NNN` for inventory-schema alignment; Purpose field dropped as phantom. Prior revision 2026-05-06 after retrieval-anchor reframe; supersedes original schema that proposed Tags→Capability rename plus four new axis fields).

narratives is interview-prep primary; cv_targeted / role_evaluation consume it secondarily for bullet-framing depth via inventory linkage. Narratives are not a primary CV retrieval anchor.

- IDs: `ST-NNN` for stories, `DC-NNN` for decisions.
- Per-entry fields: ID, Role (RL-NNN reference, multi-value; matches inventory `Role:` field; rebrand-resilient), Framework, Linked Inventory (required, multi-value), Added, Last Used.
- **Era field replaced with `Role: RL-NNN`.** Original Era field used uncontrolled free-text employer strings, drift-prone and inconsistent with inventory's canonical Role reference. RL records hold authoritative title + company; narratives can carry multiple RLs since a single narrative may span multiple roles within an employer.
- **Purpose field dropped.** Phantom field: no defined content scope, no controlled vocabulary, no consumer. Schema parsimony preferred over speculative optionality.
- **Tags field dropped.** Same overlap problem inventory had with Capability/Competency: Tags values mix Specialty, Orientation, Role Level, and leadership soft-skill signals. Removing Tags reduces schema and eliminates drift risk against the axes.
- **Per-entry Industry/Specialty/Orientation/Role Level fields not added.** Narrative axes inherit from Linked Inventory at consumption time (walk linked EX/PR IDs, union their axes). Authoring per-narrative axis tags duplicates work and creates drift when the linked inventory entry's tags change.
- `Linked Inventory:` is **required**, multi-value, and becomes the retrieval anchor:
  - cv_targeted / role_evaluation: select inventory entries by axis match; pass list to narratives lookup; intersecting narratives surface for bullet framing or decision context.
  - interview_prep: retrieves narratives via semantic body match plus inventory-axis-inheritance ranking via Linked Inventory.
- **Asymmetric linkage (narrative to inventory only).** Reverse direction (inventory to narrative) rejected: the inventory corpus is much larger than the narratives corpus, so back-references on inventory would mean many inventory edits per narrative authoring event and most inventory entries would carry an empty field. Authoring burden stays on the smaller doc.
- Framework: stories use `story_personal`; decisions use `decision_adr`.
- Migration body operations: rename "Who Pushed Back" → "Resistance" (keep as standalone section; scope expanded to non-person resistance including time, skill, and technology constraints); drop "What I'd Own Differently" subsections (purely reflective content; no replacement); empty subsections retained with `Not applicable` placeholder.
- APPENDIX removed; framework defs live in `rules/narratives/`. Tag Taxonomy section removed.
- Header: `**Used by:** cv_targeted, cv_general, interview_prep, role_evaluation, positioning, career_brief`. `**Stamps:** Last Used (YYYY-MM)`.

Stale-link mitigation: validator script (deferred to skill build) grep-checks Linked Inventory IDs against actual EX/PR IDs in inventory.

Refs: `maintained-by-metadata-field` (deferral); `competency-field-and-registry-removed-2026-05`, `cv-targeted-retrieval-architecture-2026-05`.

#### positioning-schema
- Cut: Competencies (~30 bullets), Role-Targeted Accomplishments (~30 bullets). CV and role evaluation pull from inventory directly.
- Retain: Positioning Statement + Focus Bullets, Core Philosophy, What Makes Me Unique (renamed from "What Makes This Different"), Industry Trajectory, Signature Themes, Elevator Statement, LinkedIn About Me, Why I Chose to Leave BioMarin.
- Reorder: Signature Themes follows Core Philosophy.
- IDs: `TH-NNN` on themes.
- APPENDIX removed entirely; `Linked Stories:` field added to themes.
- Customization Instructions move to `career_brief`.
- Recruiter Pitch Template moves to `templates/recruiter_pitch_template.md`.
- "Avoid:" line removed from WHY I LEFT (moves to `interview_prep`).
- "Last Revised" line kept as plain text at top.
- Typo fix: "INDUSTRY TRAGECTORY" → "INDUSTRY TRAJECTORY".
- Header: `**Used by:** cv_targeted, cv_general, role_evaluation, interview_prep, career_brief`.

#### experience-inventory-domain-scoping
Every retrievable entry (EX-NNN, PR-NNN) carries `Industry:` and `Specialty:` fields. Multi-value, pipe-delimited. No document-level Active Domain.
- Industry validates against `rules/industries/registry.md`. May be empty.
- Specialty required. Validates against `rules/specialties/registry.md`. Identifies specialty pack for Capability validation.
- Capability validation: any-specialty rule.
- Reference sections (Education, Certifications, etc.) untagged.

Per-entry fields for Orientation and Work-state pending `retrieval-method-for-discrete-elements` resolution.

#### experience-inventory-entry-types
`EX-NNN` (employment, Section 8), `PR-NNN` (independent and volunteer, Section 10). Same field schema. Differ in ID prefix, descriptor field name (`Role:` vs `Project:`), section. New categories add new prefix ad hoc.

#### experience-inventory-section-6-rename
Renamed "Therapeutic Area and Domain Exposure" → "Industry Exposure Profile". `**Bold:**` lines → `### Sub-section` headings.
Sub-sections: Therapeutic Areas, Trial Phases, Study Types, Geographic Scope, Data Sources (renamed from Data Modalities), Standards (new), Regulatory Frameworks, Functional Experience (renamed from Functional Domains).
Data Modalities sub-section dropped — content folded; "Data Sources" carries the operative meaning (EDC, central lab, ePRO, IXRS, etc.).

#### experience-inventory-section-1-structured-fields
Section 1 (Education) entries carry structured fields, no IDs: Degree, Discipline, Institution, Start Date, End Date. Year-only date granularity (YYYY). Honors/GPA omitted. No retrieval tagging — section remains reference content per `experience-inventory-tagging-granularity`; structure exists to give cv_targeted's renderer reliable field handles instead of comma-parsing a flat line (which broke on disciplines containing commas).
Refs: `experience-inventory-tagging-granularity`.

#### experience-inventory-section-2-structured-fields
Section 2 (Professional Certifications) entries carry structured fields, no IDs: Certification, Issuer, Date Earned, Expiration Date, Status. Year-only date granularity. Expiration Date optional (blank for non-expiring or unknown). Status enum: Active | Inactive. No retrieval tagging — reference content. Schema designed for generalization (other users may hold active expiring certs); blank fields acceptable.
Refs: `experience-inventory-tagging-granularity`, `feedback_design_for_generalization`.

#### experience-inventory-section-3-structured-fields
Section 3 (Professional Affiliations) entries carry structured fields, no IDs: Affiliation, Role, Start Date, End Date, Status. Year-only date granularity. Role field accommodates Member through Board/Officer/Committee Chair (general-utility, not just current user's "Member"). Status enum: Active | Inactive (extensible). No retrieval tagging.
Refs: `experience-inventory-tagging-granularity`, `feedback_design_for_generalization`.

#### experience-inventory-section-4-restructure
Professional Training: Completed and In Progress sub-sections. Year dropped from In Progress sub-header.
Structured fields per entry, no IDs: Training, Provider, Format, Start Date, End Date. Date granularity YYYY-MM. Format optional (Online | In-Person | Hybrid). Sub-section split provides Status indicator (no separate Status field). No retrieval tagging — reference content. Schema designed for generalization.
Refs: `experience-inventory-tagging-granularity`, `feedback_design_for_generalization`.

#### experience-inventory-section-5-restructure
Technical Experience: three sub-sections.
- Programming, Data & Analytics (Languages & Data Engineering, ML & Analytics, Cloud & Platforms, Visualization & Reporting, Development Tools, Project Management Tools)
- Office & Collaboration (SharePoint, MS Teams, OneNote, Visio, Adobe Acrobat Pro, Adobe LiveCycle Designer)
- Clinical Application Systems (9 categories carried forward)
Methodologies sub-section dropped; items relocated. Recategorizations: Minitab → ML & Analytics; MS Access → Languages & Data Engineering; JIRA, MS Project → Project Management Tools. Oracle Apex dropped.

Tools-only discipline: Section 5 lists named tools, products, libraries, and platforms only. Capability descriptions, methods, algorithms, and work-scope descriptors do not belong here — that content lives in Section 8 (EX entries) or other sections. Cleanup pass stripped: ETL/ELT workflows, file parsing, ML methods (ARIMA, regression, clustering, PCA, NLP, EDA, etc.), simulation/optimization, decision analytics, Python/R viz libraries (generic), custom user-built apps, "(generic)" placeholders.

Flat-list convention: one tool/product per token, comma-separated. Sub-products enumerated separately (Jupyter Notebook, JupyterLab — not Jupyter (Notebooks, Lab); Git, GitHub — not Git/GitHub). Acronym-expansion parens permitted (eRT (e-Research Technology)) since JDs may use either form. Scope/role descriptors stripped from parens. Generic category mentions (ePRO platforms, eCOA platforms) retained when no specific named platform exists — supports JD category-level matching. Versions dropped from tool names (Minitab, not Minitab17).
Refs: `feedback_design_for_generalization`.

#### experience-inventory-section-7-flat-records
Flat records, each role self-contained, company as a field. Stable ID `RL-NNN`.
EX entries reference Section 7 via `Role: RL-NNN` field per `inventory-role-rl-reference-applied-2026-05`. RL Title and Company are canonical; EX entries do not carry duplicate Title/Company fields. Resolves the rebrand-resilience problem that motivated the original "Title | Company" coexistence design.

`Type:` enum: `Direct | Contract | Freelance | Military | Independent`. `Independent` added 2026-05-12 to support self-directed work periods with no external employer (distinct from `Freelance`, which is paid work for an external client). Independent RLs use `Company: Independent` uniformly; Title carries the discrimination between different independent focuses (parallels how a single company holds multiple RL records with different titles for different focuses).

#### experience-inventory-section-ordering
Sections 9 and 10 swap. Independent & Volunteer Projects → 9. Academic Coursework Detail → 10. Education stays at top.

#### experience-inventory-tagging-granularity
Reference sections addressable at sub-section level via heading anchors. Per-item tagging not added.

#### inventory-section-8-rl-grouping-2026-05
Section 8 renamed "All Tasks Performed" → "Experience Entries" (the `EX-` prefix denotes experience units, not to-do tasks). The ten hand-curated topical sub-headings are replaced with one `### RL-NNN` sub-heading per role; heading text is the RL ID only, preserving the rebrand resilience of `inventory-role-rl-reference-applied-2026-05`.

Structure: RL sub-headings ordered to match Section 7 (reverse-chronological by Start Date). Within each RL, entries sort by primary Orientation value, then primary Specialty value, then EX-ID ascending. "Primary value" is the value before the pipe in a multi-value field per `inventory-entry-multi-value-orientation-2026-05`.

Rationale: the topical sub-headings had no assignment rule and no naming rule, and did not map to any tag axis (one heading spanned 12 Specialty combinations across 3 Orientations). The Specialty/Orientation/Industry/Level/Work-state tags already carry the classification, and cv_targeted retrieval (`cv-targeted-retrieval-architecture-2026-05`) reads tags from entry fields, not document position — so the sub-heading scheme had no retrieval role. RL grouping is deterministic and self-maintaining: every entry's `Role:` field assigns it unambiguously.

ID-matching convention: `### RL-NNN` adds a third occurrence pattern for an RL ID alongside `ID: RL-NNN` (Section 7 record) and `Role: RL-NNN` (Section 8 reference). RL/EX/PR ID matching uses anchored line patterns (`^ID:`, `^Role:`, `^### `, `^Linked Inventory:`), never bare substring.

Background Roles: the `Background Roles (Not Tagged)` block formerly after Section 8 is removed — its three roles already exist as full Section 7 records (RL-001, RL-002, RL-004), so the block was redundant. The QC-exemption function it served is now carried by an `Experience Entries: None` field on those three RL records, machine-checkable per-record. This implements the Background Roles exception to the per-RL completeness rule in `design/inventory_builder_quality_checks.md`.

Closes `inventory-section-8-subsection-reassignment` (the deferred Step 6 sub-section remap, already moot since `competency-field-and-registry-removed-2026-05`; the structural question is now resolved by this decision). Apply executed via `scripts/_reorg_section8.py` against 212 EX entries; per `working-files-deleted-after-apply` the script is deletable, this decision is the durable record.

Refs: `inventory-role-rl-reference-applied-2026-05`, `inventory-entry-multi-value-orientation-2026-05`, `cv-targeted-retrieval-architecture-2026-05`, `competency-field-and-registry-removed-2026-05`, `experience-inventory-section-7-flat-records`, `inventory-section-8-subsection-reassignment` (deferral, closed), `design/inventory_builder_quality_checks.md` (parallel-construction scope + §5 background-role exemption updated), `design/narratives_builder_quality_checks.md` (anchored-matching note added).

#### narratives-placement
`rules/narratives/` with five files: `decision_adr`, `decision_personal`, `story_atola`, `story_star`, `story_personal`.

#### tag-taxonomy
`rules/tags.yaml` holds only global tag vocabularies that apply to every entry: Role Level, Purpose. YAML. Org Context absorbed into the Work-state axis.
Specialty-specific tags do not live here. Specialty-pack capability vocabulary (fine-grained, specialty-specific) in `rules/specialties/<specialty>.md` Capability vocabulary section. Industry packs hold industry content but not Capability lists.
Orientation values in `rules/orientations/`. Industry/Specialty registries: `rules/industries/registry.md`, `rules/specialties/registry.md`. (Competency registry previously lived at `rules/competencies/registry.md`; removed per `competency-field-and-registry-removed-2026-05`.)

#### initial-industry-pack-content-design
Pharma industry pack (`rules/industries/pharma.md`) content-validated through manual research against current practitioner sources (FDA, ICH, ACRP, regulatory publications, hiring keyword surveys). Vocabulary, dialect, emphasis, adjacency captured. Future industry packs trigger `industry_builder` build at that time; pharma serves as the worked example.
Refs: `design/axis_research_notes.md`, `foundation-execution-order`, `five-orthogonal-axes`.

#### initial-specialty-pack-content-design
Five specialty packs (`rules/specialties/clinical-operations.md`, `data-engineering.md`, `ai-engineering.md`, `quality-compliance.md`, `people-leadership.md`) content-validated through manual research against current practitioner sources (industry frameworks, hiring keyword surveys, regulatory publications, framework authorities). Capability vocabulary, terminology, adjacency captured per specialty. Future refresh runs through `specialty_builder` if/when built.
**Extended by `specialty-axis-extension-data-science-operations-strategy-2026-05`.** Two additional specialty packs (`data-science.md`, `operations-strategy.md`) added 2026-05 with research-validated capability vocabulary, terminology, and adjacency. Original 5 packs received bidirectional adjacency entries for the new specialties; people-leadership.md received a capability-vocabulary tightening on the "Organizational design" line to specify "from the people-management lens".
Refs: `design/axis_research_notes.md`, `foundation-execution-order`, `five-orthogonal-axes`, `tag-taxonomy`, `specialty-axis-extension-data-science-operations-strategy-2026-05`.

#### specialty-axis-extension-data-science-operations-strategy-2026-05
Specialty axis extended from 5 to 7. Two new specialties added:
- `data-science`: statistical programming, statistical and quantitative methods, exploratory and applied analysis, analytic-application development carrying method, applied modeling in research/POC mode. File: `rules/specialties/data-science.md`.
- `operations-strategy`: operating-model design, capability strategy and roadmapping, process architecture and improvement, technology and vendor strategy, transformation program design. File: `rules/specialties/operations-strategy.md`.

Driven by recognition that the 5-specialty set forced misclassification of (a) statistical/analytical/programmatic work that was not engineering or production AI, and (b) function- or portfolio-level operating-model and capability-strategy work. Both clusters were defaulting to `clinical-operations` (as functional anchor) or `people-leadership` (via vision-setting / cross-functional-influence vocabulary), diluting both specialties.

Practitioner-usage validation (search-confirmed 2026-05): "data-science" is the dominant cross-industry umbrella covering statistical programming, applied analytics, applied non-production ML; "Clinical Data Science" replaced "Clinical Data Management" in pharma. "Operations strategy" is the LinkedIn-volume term (85K+ postings); "Operating Model" is the McKinsey/EY/BCG canonical practice.

Bidirectional Adjacency populated across all 7 specialty files. Capability vocabulary tightened on `people-leadership.md` ("Organizational design from the people-management lens") to disambiguate from operations-strategy's capability-lens org-design work. Registry description tightenings: `ai-engineering` qualified as "production... as deployed services"; `people-leadership` qualified as "from the people-management lens".

Schema unchanged per `axes-file-schema`: Capability vocabulary + Terminology + Adjacency. A `## Boundary rules` section was prototyped during the session and removed; OUT-rules duplicated Adjacency content and did not scale beyond a small specialty count. Boundary qualifiers remain inline in Capability vocabulary.

Inventory retag against the extended axis is the next session's work. All specialty files' `last_researched` updated to 2026-05.

Resolves: `people-leadership-scope-or-new-strategy-specialty` (operations-strategy absorbs the strategy/influence work that was driving people-leadership's broader scope; people-leadership stays narrowed by the explicit "people-management lens" qualifier on org-design). Closes proactively: `regulated-industry-cross-specialty-adjacency` (bidirectional adjacency between quality-compliance and data-engineering / ai-engineering / data-science added in this session).

Refs: `axes-file-schema`, `initial-specialty-pack-content-design` (extended here), `specialty-axis-tagging-by-work-nature`, `experience-inventory-domain-scoping`, `five-orthogonal-axes`.

#### outcome-folded-into-impact
`Outcome:` field removed from inventory entries. Closed-enum value (Capability Building, Risk Reduction, Quality Improvement, Efficiency Gain, Cost Savings, Scalability/Growth Enablement) folded into `Impact:` field as a colon-delimited prefix: `Impact: <value-type>: <prose>` when prose exists, `Impact: <value-type>` when prose was absent.
Rationale: Outcome was not called out as a retrieval signal in `cv-targeted-content-rules-from-axes`; coverage was 64% (126/197) so it added a sparse field with no committed downstream consumer. Folding into Impact preserves the value-type signal (grep-extractable via the leading colon-delimited token) while collapsing schema. Reads as natural narrative — the value-type clause is not "wrong" as the leading word of impact prose.
Supersedes the prior `field-rename-outcome-purpose` decision (Outcome was to be renamed to Purpose; now removed entirely).
Refs: `inventory-entry-structure-applied`, `inventory-field-drift-cleanup` (deferral), `cv-targeted-content-rules-from-axes` (deferral).

#### competency-field-and-registry
Inventory entry field `Capability:` renamed to `Competency:`. Controlled vocabulary at `rules/competencies/registry.md`. Validator (deferred to script build) parses inventory Competency lines, splits on `|`, rejects unknown tokens; aliases auto-canonicalize near-misses.
Rationale: name-collision avoided with specialty-pack `Capability vocabulary` sections; "Competency" links semantically to CV format spec's "Core Competencies" section.
Initial 16-term registry derived from existing inventory tags. **Superseded by `competency-registry-bottom-up-redesign-2026-05`** which replaced the registry contents with 31 lowercase-kebab values via bottom-up phrase extraction across all 197 entries. The Capability→Competency rename and registry-as-controlled-vocabulary concept established here remain valid; only the value list was replaced. **Further superseded by `competency-field-and-registry-removed-2026-05`** which removed the field and registry entirely.
Refs: `tag-taxonomy`, `inventory-entry-structure-applied`, `competency-registry-bottom-up-redesign-2026-05`, `competency-field-and-registry-removed-2026-05`.

#### competency-registry-bottom-up-redesign-2026-05
Replaced prior 16-term coarse Competency registry with a 31-term granular registry. Format changed from Title Case to lowercase kebab to match other axis value formats. **Superseded by `competency-registry-activity-level-redesign-2026-05`**, which replaced the 31-term inventory-derived shape with a 36-term activity-level taxonomy. The bottom-up extraction approach was found to produce inventory-shaped clusters (over-fit to the specific texture of the user's work) rather than activity-level competencies that transcend industry and specialty.
Refs: `competency-field-and-registry`, `competency-registry-activity-level-redesign-2026-05`.

#### competency-retagging-applied-2026-05
Re-tagged all 197 EX/PR inventory entries (`Competency:` field) against the 36-term activity-level Competency registry. JD-blind authoring; consistency-validated against a tagging-pattern reference (site-monitoring lifecycle → `operations-management` + `regulatory-compliance`; safety surveillance / SAE handling → `risk-management`; specifications → `standards-and-specification-development`; SOP / form authoring → `procedure-authoring`; etc.). Prior 16-term and 31-term Competency values fully replaced. All 36 slugs used at least once. Apply executed via `apply_competency_retagging.py` against per-EX-ID Competency mapping. Both deleted later in same session per `working-files-deleted-after-apply`.
Resolves the work component of the prior `competency-retagging-step-5` deferral. Whether the registry remains in cv_targeted's runtime retrieval path is still pending prototype outcome (`competency-registry-runtime-value` open question); if semantic-only retrieval wins, the new Competency tags become informational rather than active retrieval signal but the labor is not wasted.
Registry-gap candidates surfaced and resolved during user QC: `regulatory-document-authoring` (dropped — re-framed as `risk-management` + `cross-functional-collaboration`), `clinical-operations-execution` (dropped — entries won't surface in any CV), `vendor-management` ↔ `technology-evaluation` (split confirmed: service vendors → vendor-management; tool/platform vendors → technology-evaluation), audit-conducting (no separate slug — sponsor-SME audit support belongs under `audit-and-inspection-response`).
**Superseded by `competency-field-and-registry-removed-2026-05`.** Prototype outcome was semantic-only wins; the retagging labor is not lost — it stress-tested the registry design and confirmed the orthogonality problem with Specialty. Field stripped from inventory.
Refs: `competency-registry-activity-level-redesign-2026-05`, `competency-registry-runtime-value` (resolved by `cv-targeted-retrieval-architecture-2026-05`), `inventory-section-8-subsection-reassignment` (deferral — Step 6 trigger fires here but action deferred pending prototype outcome), `competency-field-and-registry-removed-2026-05`.

#### inventory-role-rl-reference-applied-2026-05
Cluster C migration applied: EX entry `Title:` and `Company:` fields collapsed into a single `Role: RL-NNN` reference to Section 7. RL becomes canonical for role title and company; rebrand resilience is now one record's update instead of 192. PR entries unchanged (no RL counterpart).

Reconciliation produced two RL Title corrections (Section 7 was holding contracted/HR titles where EX entries held operational/working titles; user resolved each by adopting the operational title as canonical):
- RL-017: `Clinical Data Quality Consultant` → `Sr. Data Scientist, Data Management Sciences`.
- RL-012: `Central Statistical Monitoring Lead` → `Central Statistical Monitoring Deployment Lead`.

One compound EX Title (`Regional/Global Clinical Trial Manager`, Amgen-via-DOCS, 10 entries) split between RL-011 (Regional CTM) and RL-013 (Global CTM) per per-entry user assignment based on Description content. 7 → RL-011; 3 → RL-013 (EX-088, 089, 091).

Mapping logic: explicit per-EX-ID overrides for the compound-title cluster, then exact (Title, Company) match, then whitespace+slash-normalized title match within company, then EX-title-as-substring of RL Title within company. Whitespace+slash normalization handled `Clinical Research Associate I/II` (EX) vs `Clinical Research Associate I / II` (RL-005, 19 entries).

Apply executed via `_apply_role_rl_reference.py`. Line count 3045 → 2853 (delta -192). Script deleted later per `working-files-deleted-after-apply`; this decision is the durable record.

Closes the company-field RL-reference work and inventory Cluster C.

Refs: `experience-inventory-section-7-flat-records`, `inventory-entry-structure-applied`.

#### competency-field-and-registry-removed-2026-05
Inventory `Competency:` field removed from all EX/PR entries. `rules/competencies/registry.md` deleted; `rules/competencies/` folder removed.

Removal driven by the `cv-targeted-retrieval-architecture-2026-05` decision: tags become composition-time data, not retrieval filter, and Industry/Specialty/Orientation/Level/Work-state already cover the framing and ranking signals cv_targeted needs. Competency added no orthogonal axis once the activity-level redesign was understood as overlapping with what Specialty already captures (specialty-pack capability vocabularies). The bottom-up and activity-level redesign attempts (16→31→36 terms) confirmed the registry could not stably partition the corpus without either over-fitting to inventory texture or duplicating Specialty content.

Strip executed via `_strip_competency_field.py` (line count 3242 → 3045). Folder deletion via filesystem.

Supersedes: `competency-field-and-registry`, `competency-registry-bottom-up-redesign-2026-05`, `competency-registry-activity-level-redesign-2026-05`, `competency-retagging-applied-2026-05`. Closes the work component of all four. Per `working-files-deleted-after-apply`, the proposal/extraction `.md` files and the apply scripts (`apply_competency_retagging.py`, `_strip_competency_field.py`) were all deleted on 2026-05-06; this decision and `competency-retagging-applied-2026-05` are the durable record.

Updates:
- `inventory-entry-structure-applied`: field list shortened (Competency removed). EX/PR entries now carry: ID, Title-or-Project, Company, Industry, Specialty, Orientation, Level, Work-state, Added, Last Used, Description, Impact, Context.
- `tag-taxonomy`: registry reference removed. `rules/tags.yaml` retains global tag vocabularies (Role Level, Purpose); axis files retain their own vocabularies. No entry-level coarse functional grouping field.

Refs: `cv-targeted-retrieval-architecture-2026-05`, `inventory-entry-structure-applied`, `tag-taxonomy`, `competency-registry-runtime-value` (resolved).

#### competency-registry-activity-level-redesign-2026-05
Replaced 31-term inventory-derived registry with 36-term top-down activity taxonomy. Each value names a unit of work that means the same thing across industries (e.g., `budget-management` is the same competency for a clinical PM and a small-business owner). Industry- and specialty-agnostic by design; industry/specialty context is captured by the dedicated axes.
Rationale: the bottom-up approach over-fit to the user's inventory texture, producing artificial splits like `vendor-and-cro-operational-management` vs `vendor-and-cro-selection-and-partnership-design`. JDs do not distinguish at this granularity, and granular splits prevent transferable-skill surfacing (vendor-selection experience IS relevant to a vendor-oversight JD; programming-in-R IS relevant to a Python JD). The activity-level reframe asks: "could a hiring manager in any industry write 'looking for someone with __ experience' and have it sound like a real ask?" Tools and clinical-specific terms (TMF, RBM, CSM, CSV, site monitoring, investigator training) leave the registry; tools live in `inventory.md` Section 5; clinical-specific work is captured at the underlying activity level (RBM strategy → `risk-management` or `quality-management`; TMF reconciliation → `procedure-authoring` or `regulatory-compliance`; site monitoring → `operations-management`).
Format: lean. Each entry is `- **slug**: one-line scope phrase`. No `Aliases:` section in this iteration; JD-language → slug mapping deferred to cv_targeted matching layer (semantic vs alias-list approach undecided).
Process: top-down draft of activity categories validated against extracted Competency phrasing for coverage (the user's 197 inventory entries should all map cleanly into the new taxonomy via Step 5).
Status: registry written. Step 5 (re-tag 197 entries against new 36-term registry) and Step 6 (Section 8 sub-section reassignment) remain deferred.
**Superseded by `competency-field-and-registry-removed-2026-05`.** Field and registry removed entirely.
Refs: `competency-registry-bottom-up-redesign-2026-05` (superseded), `competency-field-and-registry`, `tag-taxonomy`, `inventory-entry-structure-applied`, `competency-retagging-step-5` (deferral), `inventory-section-8-subsection-reassignment` (deferral), `cv-targeted-content-rules-from-axes` (deferral — owns JD-to-slug matching mechanism), `competency-field-and-registry-removed-2026-05`.

#### knowledge-document-scaffolding
`support/` folder at repo root holds scaffolding files; user copies into private personal repo on first clone. Career repo never holds user's personal data.
- Scaffolded: `user-info.md` (placeholder), `README.md`, `SETUP.md`, `.gitignore` for personal repo.
- Not scaffolded (built by skills): `inventory.md`, `narratives.md`, `positioning.md`.
Refs: `scaffolding-folder-layout`, `scaffolding-content-updates` (deferrals).

#### questions-library-eliminated
Originally context-free interview question library; drifted to per-application questions. Eliminated. Per-application questions live in application folder.
Refs: `questions-library-deletion` (deferral).

#### knowledge-doc-update-mechanism-hand-edit
Existing profile documents (user-info, inventory, narratives, positioning) updated by hand-edit. Builder skills become refresh tools later, only if refresh demand recurs. Mechanical sub-tasks may use one-off scripts (deleted after apply per `working-files-deleted-after-apply`). Resolves the open question `knowledge-doc-update-mechanism`.

#### inventory-entry-structure-applied
EX-NNN entries carry, in order: ID, Role, Industry, Specialty, Orientation, Level, Work-state, Added, Last Used, Description (`Description:` label, bold preserved on value), Impact, Context.
PR-NNN entries carry, in order: ID, Project, Company, Industry, Specialty, Orientation, Level, Work-state, Added, Last Used, Description, Impact, Context.
Schemas diverge on the second field: EX uses `Role: RL-NNN` reference to Section 7 (per `inventory-role-rl-reference-applied-2026-05`); PR uses `Project:` + `Company:` since Independent & Volunteer projects have no RL counterpart. Title field on EX entries dropped; RL is canonical for role title and company.
Prose section order at end of block: Description (Action), then Impact (Result), then Context (Situation). Impact is sparse-permitted, may carry a colon-delimited value-type prefix per `outcome-folded-into-impact` (e.g., `Impact: Risk Reduction: <prose>` or `Impact: Risk Reduction`). Context is sparse-permitted, free prose.
Competency field removed per `competency-field-and-registry-removed-2026-05` (originally listed between Work-state and Added).
Refs: `experience-inventory-domain-scoping`, `experience-inventory-entry-types`, `outcome-folded-into-impact`, `impact-field-semantics-2026-05`, `competency-field-and-registry`, `inventory-role-rl-reference-applied-2026-05`, `inventory-field-drift-cleanup` (deferral).

#### impact-field-semantics-2026-05
Refines `outcome-folded-into-impact` based on 2026-05-04/05 reconciliation pass against existing entries.

**Multi-value-type prefix permitted.** Impact value-type prefix may be a single value or comma-delimited list (e.g., `Impact: Capability Building, Quality Improvement, Risk Reduction` or `Impact: Capability Building, Quality Improvement, Risk Reduction: <prose>`). The Impact field is free-text prose with structured value-type prefix; the prefix is grep-extractable in either single or multi-value form. Multi-value reflects that real work often produces value across multiple types.

**Bare-tag is the fallback, not drop.** When an entry has no recoverable residual outcome beyond the Description, the value-type tag stays bare (`Impact: <value-type>` or `Impact: <type>, <type>`). The "substantiate or drop" wording in earlier `inventory_builder_quality_checks.md` was too aggressive: substantiate where possible, otherwise keep bare. Dropping the Impact line entirely is not the convention.

**Strip-aggressively rules for Impact prose.** When prose is present, it must be only outcome content. Strip:
- Audit/diagnostic findings ("revealed that X was opaque"). Move to Description as activity output, or Context as situational state.
- Pattern descriptions ("a pattern that consumed significant effort"). Move to Context.
- Qualifiers and explanatory clauses ("from sample receipt to dataset exchange"). Move with the finding.
- Mechanism narratives ("CDISC-terminology standardization eliminated non-standard legacy terminology that had been creating downstream programming overhead"). Mechanism is in Description; outcome stays as the bare residual.
- Purpose/aspirational framing ("to support enterprise data quality and regulatory submission objectives"). Drop entirely; the value-type tag carries this.
- Attribution caveats ("Full attribution to the redesign alone is not claimed; concurrent improvements contributed"). Move to Context.
- Restatements of Description's purpose clause as Impact ("worked X to support Y" with Impact "supported Y"). Description's purpose is not residual.

**Context narrative trim rules.** Cut from Context:
- Granular numbers (step counts, person counts, function counts) when generic descriptors preserve the signal.
- Colorisms ("symbolic comfort", "concentrated risk") if they restate a plain claim already made.
- Implementation tactics (how skepticism was overcome, what filtering choices reduced noise).
- Designer-decision defenses unless the boundary itself is residual signal.

Keep in Context: prior state when it makes the outcome legible; constraint envelope (resource model, headcount, organizational positioning); deliberate scope decisions when the bound is load-bearing.

**Restructure license.** Status-reached outcomes mistakenly placed in Description (e.g., "Developed roadmaps that shaped functional priorities") should be moved to Impact. Activity verbs and methodology stay in Description; realized outcomes move to Impact.

Refs: `outcome-folded-into-impact`, `inventory-entry-structure-applied`, `design/inventory_builder_quality_checks.md`.

#### industry-value-granularity
Industry registry values: pharma, biotech, cro, med-device, eclinical, generics, diagnostics. Discrete rule files for pharma, biotech, cro, med-device (all research-validated 2026-04). eclinical = registry-only (single inventory entry; pharma adjacency handles translation). generics, diagnostics = file authoring deferred.
Reasoning: GICS/NAICS treat pharma and biotech distinct; submission pathway (NDA via CDER vs BLA via CBER) is meaningful CV signal. CRO is service-side perspective with distinct hiring emphasis (cross-sponsor, contract delivery). Med-device has fundamentally different regulatory framework (510(k)/PMA/De Novo, ISO 13485, design controls).
Refs: `industry-files-full-enumeration`, `initial-industry-pack-content-design`.

#### industry-files-full-enumeration
Each industry file (`pharma.md`, `biotech.md`, `cro.md`, `med-device.md`) enumerates its full vocabulary, dialect, and stakeholder content. No `inherits from <other>.md` shorthand. Shorthand was attempted in initial biotech.md and cro.md drafts and broke `role-evaluation-axis-matching-protocol` (vocabulary axes match by overlap against the file's data sections; a matcher reading the file alone misses inherited terms). Resolution: full enumeration accepts cross-file content redundancy as the cost of discrete-industry granularity. Update propagation tracked via `registry-overlap-tracking`.
Refs: `axes-file-schema`, `role-evaluation-axis-matching-protocol`, `industry-value-granularity`, `registry-overlap-tracking` (deferral).

### Skills System

#### skill-registry-and-control-dissolved
Pattern A removes custom `skill_registry` and `control.md`. Framework discovery + slash-command picker. Per-skill metadata in SKILL.md frontmatter.

#### role-evaluation-and-cv-targeted-separate
Kept distinct. Shared inputs resolved by retrieval scripts (slice-level lookup). GapAnalysis is the handoff artifact and a stopping point. "Application" is a data-model concept (folder name), not a skill name.

#### knowledge-update-collapse
One skill with mode parameter, replacing `profile_update_adhoc` and `profile_update_inline`. Retrieval script fetches relevant slice at read time.

#### builders-axis-parity
One builder per axis. Each wired to its corresponding research sub-agent.

#### builder-mode-parameter
- `create`: drafts new rule file from research output. Greenfield.
- `refresh`: targets existing rule file, re-runs research, diffs against current, proposes updates.
Both invoke research sub-agent.
Refs: `builder-refresh-mechanics` (deferral).

#### research-sub-agents-roster
Seven sub-agents in `.claude/agents/`:
- `role-research` (used by role_evaluation)
- `organization_research` (used by interview_prep)
- `industry-research` (used by industry_builder)
- `specialty_research` (used by specialty_builder)
- `orientation_research` (used by orientation_builder)
- `level_research` (used by level_builder)
- `work_state_research` (used by work_state_builder)
All seven built (end-to-end testing requires all pieces).
Refs: `research-output-location-and-format` (deferral).

#### qc-organization
Specs in `rules/quality_control/`. Executors as sub-agents in `.claude/agents/`. Skills call QC; sub-agents execute in isolated context.
Naming: `qc-<scope>-<aspect>.md` for both specs and executors, fully kebab per `file-and-folder-naming`. Examples: `qc-cv-format`, `qc-cv-structural`, `qc-gap-analysis-completeness`. The `qc-` prefix is kept on both sides.
Amended 2026-05-14: was `qc_<scope>_<aspect>` with underscores; changed to all-kebab so QC agent and spec filenames match the general naming rule and the rest of the agent roster.

#### skill-authoring-template-library
Location: `engops/cheatsheets/skill-templates/`. First template: `human-gated-workflow.md`. Authored alongside the first skill that uses it. Conventions recorded here in the interim.

#### workflow-communication-conventions
Three communication points in skills.

**Introduction (skill start):**
- Full: multi-activity skills. Invokes `python scripts/display/introduce.py <skill_name>`. Reads from `scripts/display/introductions.yaml`. Ends with "Ready?" consent gate.
- Brief inline: single-activity skills. One-sentence declaration in SKILL.md.
Heuristic: name conveys arc → brief; otherwise → full.
Roster: full = role_evaluation, cv_targeted, interview_prep. Brief = career_brief, industry_builder, specialty_builder, orientation_builder, level_builder, work_state_builder, profile_update, positioning. Ambiguous (deferred): interview_capture, interview_followup, cv_general, inventory, narratives.

**Mid-flight narration:** before tool calls > a few seconds, narrate What/Why (one clause)/Duration (optional). Skip for fast operations. On return, brief acknowledgment.

**Phase lead lines:** each phase opens with a one-line present-tense active-voice announce, specified verbatim in the skill's SKILL.md. Renders identically on new runs and resumes. Guide, not requirement — skills may diverge where different UX needs apply. First applied 2026-05 in role-intake.

Folder: `scripts/display/`.
Refs: `introduce-py-implementation`, `introduction-roster-ambiguous-skills` (deferrals).

#### builder-research-agent-naming
The five builder research agents are named `<axis>-builder-research`: `industry-builder-research`, `specialty-builder-research`, `orientation-builder-research`, `level-builder-research`, `work-state-builder-research`. Separate from role-intake's research agents (`industry-research`, `company-research`, `role-research`), which serve role-intake's lighter classification needs. Selected over `<axis>-axis-research` and `<axis>-rule-research` for naming explicitness about the caller and parallelism with the existing `<purpose>-research` convention.
Refs: `builders-axis-parity`, `research-sub-agents-roster`.

#### builder-adjacency-back-edge-handling
When a builder creates a new value file, it also drafts back-edge bullets for the new value into each sibling file's Adjacency section, using the same research, presents all proposed sibling edits in one batch for user approval, then writes them. Builder takes responsibility for back-edges; user does not hand-author them.
Refs: `builders-axis-parity`.

#### builder-refresh-diff-presentation
**Superseded by `builder-refresh-qc-with-auto-fix-2026-05`.** The per-change interactive user-approval flow described here was replaced by the QC-with-auto-fix loop (no per-change approval; loop ships clean or provisional with unresolved findings logged). Subsequent audit (2026-05-18) further removed the change list from the apply mechanism entirely.
Original body retained for history: Refresh mode presents changes one at a time in a fixed structure: change number, file, section, type (add/remove/modify), Current (exact text or `(none - new entry)`), Proposed (exact text), Reasoning (one sentence from research). User reply required: `approve`, `reject`, `modify: <edit>`, or `defer: <reason>`. No batching, no "approve all", non-answers do not advance.
Refs: `builder-mode-parameter`, `builder-refresh-mechanics` (deferral), `builder-refresh-qc-with-auto-fix-2026-05`.

#### builder-research-value-agnostic
Each builder research agent operates value-agnostically within its axis. Given `(axis, value)`, the agent produces appropriate research output without value-specific hardcoding, so registry additions (e.g., a new `senior-leadership` level value) work without agent rework.
Refs: `builder-research-agent-naming`.

#### builder-sequencing-industry-first
`industry-builder` is built end-to-end first and validated by authoring `generics.md` and `diagnostics.md` (the two `File deferred` values in `rules/industries/registry.md`). Pattern replicated to the other four builders once industry-builder's flow is proven.
Refs: `builders-axis-parity`.

#### builder-refresh-qc-with-auto-fix-2026-05
Refresh runs through QC with auto-fix: Phase 5 mechanical checks correct script-fixable issues in place on a temp drafted file; the QC subagent runs judgment checks; the skill loops up to 3 iterations; ship clean or provisional with unresolved findings logged to `design/build_issues.md`. No user-approval-per-change gate. Phase 6 `apply-refresh` overwrites the existing value file wholesale from the post-QC drafted text (`--value-file`); the reconciler's change list survives only as informational input to QC's I3 no-op-detection check, not as the apply mechanism. This ensures Phase 5 auto-fixes always reach disk.
Supersedes `builder-refresh-diff-presentation`.
Refs: `builder-mode-parameter`, `builders-axis-parity`.

#### builder-em-dash-judgment-not-regex-2026-05
Em-dash removal in axis value files is owned by the qc-industry-builder subagent (judgment), not `scripts/axis_builder.py` (regex substitution). Removing an em dash usually requires rewriting the surrounding sentence; mechanical replacement leaves the sentence broken, and a naive `--` regex would also corrupt `---` frontmatter fences and horizontal rules. General rule for the builder family: judgment-grade text edits belong in the QC subagent, not the script.
Refs: `builders-axis-parity`.

#### builder-case-sensitivity-scope-2026-05
`scripts/axis_builder.py` does not enforce display capitalization for axis values. A4 (title check) verifies only the structural suffix `- CV Framing Rules` (case-insensitive on the suffix); the display form (e.g. `CRO` vs `Cro`, `IVD` vs `Ivd`) is the drafter's responsibility. General rule: case-sensitive structural checks should only fire when case itself carries meaning. Initialisms, acronyms, and brand forms cannot be derived deterministically from kebab-case registry keys.
Refs: `builders-axis-parity`.

#### builder-e1-all-non-self-2026-05
E1 (script) requires the new value file's `## Adjacency` section to contain one bullet per non-self entry in the axis registry: file-backed, file-deferred, AND registry-only. The reconciler still drafts back-edges only into file-backed siblings (the other states have no file to edit); E1 enforces the new file's own Adjacency completeness, not the back-edge fan-out. SKILL Phase 1 carries the siblings list as `{value, state, path}` for every non-self entry so Phase 2 research can cover adjacency reasoning for all states (drafter needs source material for the bullets E1 requires).
Refs: `builders-axis-parity`, `builder-adjacency-back-edge-handling`.

#### builder-phase-3-registry-entry-output-2026-05
SKILL Phase 3 (drafter) produces two artifacts in create mode: the value file content AND the one-line registry-entry text (`- **<value>** - <scope description>. File: <value>.md.`). Phase 5 fix routing for E1, G1, G2 returns to Phase 3 for redraft (the reconciler does not produce these artifacts and routing them there wastes loop iterations). For a value currently `File deferred`, the existing registry description may be reused if it still fits the drafted scope; otherwise the drafter rewrites from the value file's content.
Refs: `builders-axis-parity`, `builder-refresh-qc-with-auto-fix-2026-05`.

#### builder-required-inputs-fail-loud-2026-05
`scripts/axis_builder.py qc` raises an invocation error when a mode-required input is missing, rather than silently skipping the corresponding check. Refresh mode requires `--changes`; create mode requires `--sibling-edits` and `--registry-entry`. The script previously skipped the relevant check (I3, E4, G1) when its input flag was absent and reported the run as clean, indistinguishable from genuinely passing. General rule for the builder family: mode-required inputs are part of the invocation contract; an absent input is itself the bug, not a license to skip the check.
Refs: `builders-axis-parity`, `builder-refresh-qc-with-auto-fix-2026-05`.

#### builder-apply-step-structural-invariants-2026-05
`scripts/axis_builder.py apply-create` re-runs structural-coherence checks at the apply step, after the QC loop, even when the loop has hit its 3-iteration cap and shipped a provisional draft. Today this enforces G1 (the registry-entry's `File:` pointer must name the value file the script will write); a mismatch refuses the apply rather than commit corruption. Rationale: the provisional path is for content-imperfect drafts (a weak source, an unresolved citation) that a human can triage from `design/build_issues.md`. A wrong `File:` pointer is structural corruption, not a triage candidate: every downstream consumer that resolves the registry entry would follow the pointer to a missing file. General rule for the builder family: structural-coherence invariants run at the apply step too, not only inside the QC loop that can give up.
Refs: `builders-axis-parity`, `builder-refresh-qc-with-auto-fix-2026-05`, `builder-phase-3-registry-entry-output-2026-05`.

#### builder-script-owns-registry-parsing-2026-05
`scripts/axis_builder.py` exposes a `list <axis>` subcommand that emits every registry entry as `{value, state, value_file_path}` JSON. SKILL Phase 1 consumes that output rather than parsing `rules/<axis>/registry.md` itself. The script already owns the registry-format parser (`_BULLET_RE`, `_classify_bullet`); two parsers for the same format means two places that drift if the registry format ever changes, and the skill's natural-language parsing has already produced a documentation mismatch once. General rule for the builder family: where the script owns a format, the calling skill consumes parsed output via subcommand, never by re-parsing the file. Carries to specialty-builder, orientation-builder, level-builder, work-state-builder as the pattern is replicated.
Refs: `builders-axis-parity`.

#### builder-plain-english-narration-2026-05
SKILL.md for every builder includes an Operating Rule requiring plain-English user-facing status updates. No internal check IDs (A1, B2, E4, G1, H2, etc.), no implementation jargon (subagent, iteration, script half, judgment half, JSON, regex). Every phase summary, loop status note, and error message must translate to what the user needs to wait, decide, or act on. Technical detail is reserved for explicit dev-triage destinations: the `design/build_issues.md` log, deferral entries, the SKILL files themselves. Surfaced 2026-05-18 during /industry-builder generics end-to-end test when the operator narrated Phase 5 as "Script half: 13/13 pass across all 3 iterations; Subagent half: 3 iterations needed; H2 was the only failing check" — incomprehensible to a non-developer user. Cross-cutting memory `plain-english-phase-narration` captures the same principle for any skill the operator runs.
Refs: `builders-axis-parity`, `artifact-skill-qc-internal`.

#### builder-state-derives-mode-2026-05
Builder skills do not ask the user to pick a mode. Phase 1 looks up the registry state via the script's `list` subcommand and derives the only valid mode from the state: `not-in-registry` or `file-deferred` → create; `file-backed` → refresh; `registry-only` → refuse. The user gets a plain-English yes/no continuation prompt ("No file exists yet for `<value>`. Want me to create one now?"), not a multiple-choice mode picker. Mode is no longer a user-supplied invocation argument; any `create`/`refresh` token passed in invocation is ignored. Surfaced 2026-05-18 during the generics test when the operator asked the user "create or refresh?" after the state had already determined that only create was valid. General rule for the builder family: when state determines the only valid mode, do not present mode as a choice. Carries to the four remaining axis builders.
Refs: `builders-axis-parity`, `builder-mode-parameter` (superseded for user-facing prompt; mode arg removed from invocation contract), `builder-script-owns-registry-parsing-2026-05`.

#### builder-reconciler-adjacency-slice-2026-05
The Phase 4 reconciler subagent receives each file-backed sibling's `## Adjacency` section body as text, NOT the file path. The dispatching skill extracts the slice via the `scripts/axis_registry.py slice <axis> <value> --section Adjacency` subcommand before dispatching the reconciler. Rationale: the reconciler's job in create mode is to draft a back-edge bullet in each sibling's voice; the existing translation bullets in the sibling's Adjacency section are the correct voice reference for drafting a new translation bullet (more relevant than Vocabulary, Dialect, or Emphasis). Passing only the slice bounds the reconciler's context cost regardless of how many siblings the axis registry holds, which becomes load-bearing as the four remaining axis builders are built against axes with potentially more values. The QC subagent's D1 check (cross-sibling-content redundancy) still receives full sibling file paths and reads whole sibling files. This is a deliberate choice at current axis sizes (no axis exceeds ~7 file-backed values), where the cost is trivial; it is NOT because D1 needs whole files (D1 compares only the Vocabulary and Dialect sections). Slicing D1's input would be a constant-factor saving and would not change its O(N-siblings) scaling; the proper fix if an axis ever approaches context pressure is to mechanize D1's verbatim-overlap detection against an inverted term index, per the `registry-overlap-tracking` deferral, not to slice. The slice optimization applies only to the reconciler. Surfaced 2026-05-18 during generics test when discussing scale concerns. General rule for the builder family: when a subagent's task is narrowly scoped to one section of each sibling, pass the slice via the script's `slice` subcommand, not the file path.
Refs: `builders-axis-parity`, `axes-file-schema`, `adjacency-graph-fully-connected-rule-revisit` (deferral; the slice optimization is independent of whether the graph stays fully connected).

#### builder-script-accepts-wrapped-or-bare-2026-05
`scripts/axis_builder.py` accepts both the reconciler subagent's self-describing wrapper objects (`{"mode": "create", "sibling_edits": [...]}` or `{"mode": "refresh", "changes": [...]}`) AND the bare list shape its own docstring originally specified. Implementation: `_unwrap_list(parsed, key)` helper at each subagent-fed `_load_json` site (three sites: qc's `--sibling-edits` and `--changes`, apply-create's `--sibling-edits`). Surfaced 2026-05-18 during generics test when the dispatching skill wrote the reconciler's wrapped output to the temp file and the script crashed with "'str' object has no attribute 'get'" because it iterated dict keys instead of array elements. Rationale: a contract mismatch between a subagent's output and a script's input should never reach the user as a Python traceback; the script tolerating both shapes makes the contract resilient to drift in either direction. Issues files (constructed by the skill from aggregated QC findings, not by a subagent) remain bare-list-only and are not at risk. General rule for the builder family: script inputs that come from a subagent must tolerate both wrapped and bare JSON shapes. The deeper systemic concern (any contract drift should fail inside the build loop with a triage log, not as a user-facing traceback) is tracked separately as `builder-contract-drift-guardrails` deferral.
Refs: `builders-axis-parity`, `builder-contract-drift-guardrails` (deferral; this decision patches the immediate symptom; the systemic guardrail is the deferred work).

#### qc-h2-mechanical-script-check-2026-05
H2 (Dialect acronym list reconciles with body usage) moves from the `qc-industry-builder` subagent to `scripts/axis_builder.py qc`. The check is deterministic regex extraction in both directions: acronyms used in body sections (Vocabulary, Emphasis, Adjacency) that are missing from the Dialect catalog, and acronyms in the catalog that are unused in body. Surfaced 2026-05-18 during the generics end-to-end test where the subagent oscillated across iterations catching different subsets of the same all-caps tokens each pass (iter 1 missed 9; iter 2 caught 7 of those but still missed 2; only converged on iter 3 with user manually catching gaps). Subagents are inconsistent at exhaustive token enumeration; the check definition is deterministic and belongs in the script. Implementation: regex `\b[A-Za-z]{2,6}\b` with filter "at least 2 uppercase letters" (captures pure all-caps and CamelCase initialisms like eCTD, QbD, SaMD; skips single-uppercase like Cmax/Tmax which the spec does not target); plural normalization so `ANDAs`/`ANDA` and `CRFs`/`CRF` match (lowercase 's' suffix where pre-'s' is uppercase); hardcoded exclusion set for Roman numerals (II..XII), the `CV` artifact from the canonical title suffix, and cross-domain world acronyms (DNA, RNA, UN, EU, UK, USA, XML) that no industry file would reasonably catalog as industry-specific. Report-only in both directions; the drafter handles in Phase 3 (add to list, rewrite to drop, or prune unused). Auto-fix on the "listed-but-unused" direction (splicing tokens out of the comma-separated catalog safely) is deferred to a v2 if it earns the complexity. Smoke test on the shipped generics.md drops from 21 raw findings (with 12 plural false positives + 3 cross-domain noise) to 6 actionable items (TE codes AA/AB/BX, brand-reference GSK, genuine misses KOL and PMA). Resolves deferral `qc-h2-acronym-reconciliation-should-be-mechanical`. General rule for the builder family: checks whose definition is deterministic regex extraction belong in the script, not a subagent.
Refs: `builders-axis-parity`, `builder-plain-english-narration-2026-05`, `builder-em-dash-judgment-not-regex-2026-05` (the inverse case: H1 stays subagent because em-dash removal requires sentence rewriting, not pattern matching).

#### axis-builder-script-split-applied-2026-05
`scripts/axis_builder.py` (1315 lines, 6 subcommands) is split into four concern-scoped scripts plus two shared helper modules. Concern split: `scripts/axis_registry.py` owns `lookup` / `list` / `slice` (read-only registry parsing + section extraction); `scripts/axis_qc.py` owns mechanical QC with auto-fix (single command, no subcommand); `scripts/axis_apply.py` owns `create` / `refresh` (file writes with transactional rollback). Helper modules: `scripts/_util.py` holds general I/O and date helpers (`read`, `write`, `load_json`, `today_ym`, `today_iso`) usable by any script and adopted in this change by `scripts/assemble.py`; `scripts/axis_utils.py` holds axis-builder-internal helpers (path resolution, markdown section bounds, frontmatter split, subagent-JSON-shape unwrap). CLI substitutions across all spec files: `axis_builder.py list` → `axis_registry.py list`; `axis_builder.py slice` → `axis_registry.py slice`; `axis_builder.py qc` → `axis_qc.py` (no subcommand); `axis_builder.py apply-create` → `axis_apply.py create`; `axis_builder.py apply-refresh` → `axis_apply.py refresh`. No back-compat shim; the old script is deleted. Naming caveat: `_io.py` was the original helper-module name following the `_config.py` convention, but it shadowed CPython's stdlib private `_io` module and broke import resolution at runtime; renamed to `_util.py`. Rule for the rest of the axis-builder family: replicating the pattern to specialty / orientation / level / work-state builders uses the same four-script + two-helper structure, not a single bundled CLI. Resolves deferral `axis-builder-script-split`.
Refs: `builders-axis-parity`, `scripts-separate-by-concern` (memory), `builder-contract-drift-guardrails` (parallel deferral on systemic resilience, still open).

#### builder-contract-drift-guardrails-applied-2026-05
Contract drift between subagent JSON outputs and the consuming scripts (`axis_qc.py`, `axis_apply.py`) now fails with a categorized error rather than a Python traceback. Implementation: a `ContractError` exception class and a centralized `validate_list_of_dicts` function in `scripts/axis_utils.py`, plus three shape constants (`SIBLING_EDIT_SHAPE`, `CHANGE_SHAPE`, `ISSUE_SHAPE`) that every JSON input is validated against at the script boundary. Validation enforces top-level shape (list), required keys per element, unexpected-key rejection, string-type per field, and enum values for `type` in the change shape. CLI entry points catch `ContractError` and exit with code 2 plus a `ContractError:` stderr prefix, distinct from the generic `Error:` / exit 1 path. The dispatching SKILL recognizes the prefix and translates to a user-facing message ("the build couldn't continue because one of the helper outputs didn't match the expected shape; details logged for dev triage"), appending the full stderr text to `design/build_issues.md` under a `(contract failure)` section header. Why option (b) of the three deferral options: (a) documentation-only would rely on every future builder author following the SKILL template, drift recurs the moment discipline lapses; (c) try/recover wrapper hides the error from the user but does not prevent it, dev still pays the cost. Only (b) eliminates the class — the validator lives in the shared script tree so future axis builders (specialty, orientation, level, work-state) inherit the protection without per-axis discipline. `unwrap_list` retained for the dual-shape tolerance (bare list vs. `{"<key>": [...]}` wrapper) but now raises `ContractError` instead of `ValueError` so its failures route through the same categorized path. Resolves deferral `builder-contract-drift-guardrails`. General rule for the builder family: every subagent/script JSON boundary is validated against a declared shape; raw input shape failures are categorized errors, not script crashes.
Refs: `axis-builder-script-split-applied-2026-05`, `builders-axis-parity`, `feedback_artifact_qc_internal.md` (memory: dev-triage log discipline for end-user-facing skills).

#### f1-source-authority-tiering-2026-05
F1 (source authority) tiers acceptable source classes by claim type rather than applying one strict standard. Regulatory / standards-body / quantitative / temporal claims continue to require authoritative sources (issuing body, peer-reviewed literature, government statistics, recognized standards body). Hiring-pattern and qualitative-industry-sentiment claims accept "verified industry intelligence" (recognized recruiter firms, established trade publications, sector-specific newsletters with editorial accountability) when authoritative survey data is structurally unavailable at the claim's granularity. In any tier, marketing pages, unsourced blogs, sponsored content, and AI-generated summaries without attribution still fail. Surfaced 2026-05-18 during the diagnostics test: F1 fired on the Emphasis section's hiring-pattern claims sourced from Cerca Talent (an IVD-specialist recruiter); scoped Phase 2 re-research confirmed AAMI / AdvaMed / ACLA / CAP / AMP / CLSI / BLS publish no IVD-manufacturer hiring-panel survey data at the relevant granularity (gap is structural, not addressable by more iteration). Treating all non-authoritative sources identically was forcing every industry create / refresh to ship provisional whenever the Emphasis section had hiring-pattern content. The fix tiers F1 so the subagent classifies each claim and matches against the acceptable source class for that claim's tier. Knock-on: under the new rule, the diagnostics F1 finding clears (Cerca Talent qualifies as verified industry intelligence per user framing "a verified recruiter's blog is on the cusp but I wouldn't totally ignore it"); `rules/industries/diagnostics.md` provisional flag removed; `design/build_issues.md` 2026-05-18 entry removed. Resolves deferral `f1-source-authority-tiering-revisit`. General rule for the builder family: checks against source authority tier by claim type, not a single across-the-board standard, when authoritative coverage is uneven across claim types.
Refs: `builders-axis-parity`, `qc-h2-mechanical-script-check-2026-05` (parallel pattern: an over-strict subagent check was relaxed once the claim definition was sharpened).

#### builder-qc-file-single-routing-source-2026-05
Builder Phase 5 no longer carries a QC-failure routing table. Each builder's `rules/quality_control/qc-<axis>-builder.md` is the single routing source: every check's `Fix on fail` entry names the phase to re-enter (or directs a halt for invocation errors), and the skill's Phase 5 instruction is simply to follow that entry. This removes a ~26-line routing table that was duplicated in the industry-builder and specialty-builder SKILL files and had already drifted from the QC files (the A5 entry described the auto-insert rather than the routed buried-header failure). Surfaced during the 2026-05-20 six-skill audit, which also found orientation-builder cross-referencing "the table used by the other axis builders" (not self-contained) and work-state-builder and level-builder missing the routing step entirely (judgment-check failures could not be fixed); all three corrected by this decision. The QC files' `Fix on fail` entries were swept so each names its phase, auto-fix, or halt disposition. General rule for the builder family: QC-failure routing lives in the per-axis QC rule file, not in the skill.
Refs: `builders-axis-parity`, `builder-refresh-qc-with-auto-fix-2026-05`, `axis-builder-script-split-applied-2026-05`.

### Lineage & Traceability

Application lineage only. Knowledge-doc version history handled by git.

#### application-id-format
`<company-slug>-NNN`. Lowercase. Per-company counter. Examples: `pfizer-001`, `jnj-003`.

#### company-slug-registry
User enters slug at first encounter. Stored in `rules/organizations/company-slugs.yaml` with full company name. Counter increments on each ID issue.
Schema: YAML keyed by slug. Three fields: slug (key), `name`, `counter`.
```yaml
pfizer:
  name: Pfizer Inc.
  counter: 3
```
Cut fields: aliases, former_names, first_seen, applications list, access stamp.
Refs: `application-id-script-implementation` (deferral).

#### session-log-location-and-creation
Created at start of role_evaluation regardless of apply decision. `personal/sessions/<slug>-NNN_session-log.md`.

#### session-log-frontmatter-schema
YAML frontmatter, five fields:
```yaml
---
application_id: pfizer-001
company: Pfizer Inc.
role: Director, Clinical Data Operations
created: 2026-04-24
state: evaluating
---
```
- `application_id`: required. Mirrors filename prefix.
- `company`: snapshot at creation. Denormalized for self-containment and historical accuracy under rebrand.
- `role`: free-text.
- `created`: YYYY-MM-DD.
- `state`: enum `evaluating | applied | interviewing | do-not-pursue`. File location stays in `personal/sessions/`; closure signaled by state.
Cut fields: role_slug, last_updated, outcome/fit_verdict, access stamps.
Refs: `session-log-body-schema`, `session-log-parser-tests` (deferrals).

#### per-application-folder
`personal/applications/<slug>-NNN-<role-slug>-<yyyy-mm>/`. Created on apply decision. User enters role slug at application start. Files inside use `<slug>-NNN` alone.

#### do-not-pursue-folder
`personal/do-not-pursue/` for role_evaluations not advancing.

#### lineage-file-naming-convention
Per file-and-folder-naming. Compound application ID embedded. Examples: `gap-analysis_pfizer-001.md`, `cv_pfizer-001.docx`.

#### last-used-stamping
Skills stamping accepted outputs add `Last Used: YYYY-MM` to cited entries in `inventory` and `narratives`.

#### state-detection
Ordered checks combine file existence and session log entries.
Refs: `state-detection-logic-and-location` (deferral).

#### tracker-integration-out-of-scope
External Google Drive tracker not in current scope.
Refs: `tracker-integration` (deferral).

### Documentation Discipline

#### component-documentation-discipline
Every skill, sub-agent, standalone script has a `COMPONENTS.md` entry: inputs, outputs, triggers, update triggers. Authored alongside the component. Component evolution requires entry update in same change.
Repo `CLAUDE.md` references `COMPONENTS.md`.

Roster conventions (added 2026-05-23):
- **Drafted** tier sits between Built and Planned. Use when a skeleton SKILL.md exists (frontmatter + a `Status: Draft` note + reserved content) but orchestration is not yet designed. No detailed entry until the design lands.
- **Family entries** under Detailed Entries collapse parametric component families (N variants differing only by one parameter) into a single entry naming all variants in the heading and using a placeholder in the body. Used for the axis-builder ecosystem (5 builder skills + 15 supporting agents).

#### document-metadata-header-discipline
Every doc programmatically consumed by skills/sub-agents/scripts carries a metadata header below the title.
Scope in: profile documents, rule files, templates.
Scope out: skills/sub-agents (have YAML frontmatter and COMPONENTS.md entries), meta docs, outputs, scripts.
Format: plain markdown lines, `**Field:** value`, multi-value comma-separated. Selected over YAML frontmatter (renders invisibly in VS Code preview).
Fields v1, applied minimally:
1. **Used by**: required when consumed.
2. **Stamps**: optional, only where stamping happens.
3. **Generated by**: optional, only for script-generated docs.
Inline prose references to component names discouraged; named refs belong in metadata header.
Refs: `metadata-header-reconciliation-script`, `maintained-by-metadata-field` (deferrals).

#### data-only-discipline
Knowledge documents and rule files hold data and metadata only. No procedural instructions. Procedural logic lives in skills, format specs, scripts.
What belongs: data, metadata header, brief one-line purpose at top.
What does not: Usage Notes sections, field-level conditional logic, layout/composition rules, self-referential meta-instructions.

#### working-files-deleted-after-apply
Working files in `temp/` (proposals, drafts, intermediate artifacts, apply scripts) are deleted after the operation they describe is applied. The closed decision in `design/design_decisions.md` is the durable record of what was done, the rule that governed the operation, and the verification result. The inventory and other affected files reflect the applied state. Apply scripts may be retained locally at user discretion if there is a concrete future need to re-run them, but they are not committed evidence trail and the closed decision must be self-sufficient as the historical record.

Rationale: retaining proposals or apply scripts alongside the closed decision creates overlapping records of the same operation. Proposals can drift from the applied state during a session (a mid-session refinement reverses a removal, but the proposal file is not re-written). Apply scripts can become orphaned when the data shape they operate on is later changed by subsequent decisions (e.g., the Competency apply script targeting a field that was later removed). Either creates conflicting statements across documents. The closed decision text is the only artifact that stays correct as the design evolves; the rule treats it as such and forces it to be complete.

Applied 2026-05-06. Files deleted under this rule include: proposal/extraction `.md` files (`specialty_retag_proposal_2026-05.md`, `competency_extraction.md`, `competency_clustering_proposal.md`, `competency_retagging_proposal.md`, `inventory_tagging_proposals.md`, `_inventory_backup_pre_tagging.md`) and the corresponding apply scripts (`_apply_specialty_retag_2026-05.py`, `apply_competency_retagging.py`, `_strip_competency_field.py`, `_apply_role_rl_reference.py`, `_apply_tagging.py`, `migrate_inventory.py`, `build_cv_*.py`). All affected closed decisions updated to remove "retained as evidence trail" language and reference this rule instead.

Subsumes the prior "apply script retained as evidence trail" pattern that ran across multiple closed decisions before this rule existed.

Refs: `data-only-discipline`, `component-documentation-discipline`, `document-metadata-header-discipline`, `competency-field-and-registry-removed-2026-05` (decision whose orphaned scripts proved that retained scripts go stale).

#### memory-vs-project-files-discipline
Operating rule for where information lives:

- **Memory (`~/.claude/.../memory/feedback_*.md`):** cross-cutting behavioral feedback to Claude that applies across projects and sessions (pacing, asking-too-much, audit-before-applying, communication style). Project-agnostic.
- **`design/design_decisions.md`:** all project-specific closed decisions, including design principles applied within this project (schema rules, parser conventions, file organization, retrieval architecture).
- **Topical files in `design/` (e.g., `inventory_builder_quality_checks.md`):** used only when a decision area outgrows an inline block in `design_decisions.md` and needs a dedicated file referenced from there.

Established 2026-05-06 after audit found 5 project-specific feedback memories misplaced in memory (cv_role_completeness, atomic_inventory, impact rules, context_trim_narrative). Content was either already in `inventory_builder_quality_checks.md` or folded in during the audit; memory entries deleted.

When in doubt: if the rule applies only when working in the career repo, it goes to `design/`. If the rule applies whenever Claude is working with the user regardless of project, it goes to memory.

### Rule Refresh & Staleness

#### rule-refresh-user-triggered
Axis rule files refresh via builder in `refresh` mode. User-triggered. No automation.

#### rule-staleness-metadata
`last_researched: YYYY-MM` in YAML frontmatter. Builders stamp on every successful run.

#### rule-staleness-detection-at-use
Consuming skills read the stamp on load. If older than threshold, present binary choice:
> "Rule X was last researched N months ago. Proceed with existing information, or perform a research refresh first?"
On refresh: skill invokes builder in `refresh` mode, reloads, continues.

#### rule-staleness-grouped-prompt
Multiple stale rules at skill start: one grouped prompt, not a series.

#### rule-staleness-threshold
9 months as repo-wide constant.
Refs: `staleness-threshold-revisit`, `staleness-per-axis-overrides` (deferrals).

#### organizations-folder
`rules/organizations/`:
- `org_industry.md` (was `registry_company_type`): research scoping for interview_prep.
- `company-slugs.yaml`: slug registry.
Drop `registry_` prefix. Prior `org_maturity.md` plan superseded by Work-state axis (per-entry tagging supersedes org-level modifier).

### Templates & Format Specs

#### format-spec-cv-boundary
Format spec = rendering config (fonts, margins, spacing, bullet chars, file-naming). Deliverable-specific, axis-agnostic.
`design/format_spec.md` transfers with two cleanups: (1) move embedded python-docx code (lines 95-123) to a script under `scripts/`; (2) parameterize hardcoded name in output filename (line 182), pull from `user-info.md`.

#### interview-template-artifacts
`interview_completion` and `interview_scratch` exist as blank skeletons (in `templates/`, copied per round) and as populated instances (in application folder).

#### workflow-sequence-diagram-deleted
Old registry's ASCII diagram does not carry over.

### Stack & Infrastructure

#### stack-orchestration
Claude Code native for most workflow. LangGraph approved for the CV generation loop only as a bounded learning experiment.
Constraints:
1. No dual state management. One state model, one integration handoff.
2. If friction beyond initial learning curve materializes, the experiment stops at the CV loop; does not extend to other skills.

#### stack-retrieval
Mixed by content shape. Structured lookup (Python script) for structured documents. RAG reserved for genuinely unstructured content (interview_scratch). Default structured.

#### stack-execution
Skills are markdown. Deterministic logic = Python scripts via Bash. LLM-judgment in skill or LLM sub-agents. Build scripts alongside the skill that uses them. Never use an LLM where a script can verify deterministically.

#### configuration-file
Two-tier:
- **Repo-structure config** at the career-repo root (`config.yaml`, version-controlled): the repo-structure constants scripts depend on - relative folder paths, filename patterns, the APP-NNN scheme. Identical for every clone; not edited on clone. Scripts resolve the repo root from `__file__` (never an absolute literal) and read these from `config.yaml`. Section-heading strings stay inline in scripts (config indirection for those is overkill). It grows by adding semantically-named keys in the appropriate section (e.g. a CV naming convention as a new `naming` key); never numbered-suffix keys (`foo2`), and nest into a named sub-map only when a genuine second variant of one concept appears.
- **Personal config** (`personal/config.yaml`, nested private repo): reserved for genuinely user-specific values - output destinations outside the repo, future tracker placeholder. Created only when a script actually needs one. The `name` field is in neither (lives in `user-info.md`).

Amended 2026-05-14: the original single-`personal/config.yaml` decision assumed the config would hold personal/absolute paths. With `__file__`-resolved root and relative paths, repo-structure config carries nothing clone-specific and belongs in the version-controlled career repo. See memory `feedback_no_hardcoded_repo_values`.

### Operational Discipline

#### approach-foundation-first
Foundation-up order:
1. Lineage and traceability requirements.
2. Knowledge documents.
3. Session-log and application-ID.
4. Each workflow skill in sequence.
5. Remaining items.
Qualified by `feedback_build_incrementally.md`: per-skill detail at skill build time, not in advance.

#### foundation-execution-order
Hand-edit axis rule files first → finalize profile documents next → build axis_builder skills later, only if refresh demand recurs. Builder skills become refresh tools, not validation gates that block progress. Decision driven by avoiding the planning-paralysis pattern that killed the prior build (deferring real work because a hypothetical future skill might do it differently).
Refs: `initial-industry-pack-content-design`, `initial-specialty-pack-content-design`, `cross-axis-reconciliation` (deferral), `approach-foundation-first`, `builders-axis-parity`.

#### decision-filter
Order: value, friction, scalability, learning tiebreaker. Scope creep and gold plating route to "enhancements" list, not inline.

#### global-rules-minimized
`rules/global-rules.md` as single file. Three rules: never fabricate content; failure handling protocol; never proceed with partial content.

#### pacing-consolidation
User-level CLAUDE.md holds general response-shape pacing. Skill approval-gating lives in skill authoring template as Presentation Phase convention.

---

## Foundation Stage

Empty. Stage-specific items populate as builder skills surface them at build time.

## Application Workflow Stage

### role-intake

The first skill. Ingests a job description, researches it, classifies it against the five axes, and produces a session log + a research file for the downstream gap-analysis skill. Supersedes the old `role_evaluation` design — that skill's scattered pre-build specs are reference only, not spec. Gap analysis is a separate later skill.

#### role-intake-architecture
Plain Claude Code skill: `career/.claude/skills/role-intake/SKILL.md` orchestrates ten separable phases (0-9), each with an explicit input/output contract so a LangGraph orchestrator could wrap the system later without rewriting work units. No LangGraph now. Deterministic work in scripts, web research and QC in subagents, to keep the main session context light.
- Scripts: `scripts/ingest/jd_extract.py` (JD/comms → text), `scripts/app_id.py` (next global APP-NNN), `scripts/display/introduce.py` + `introductions.yaml` (phase-0 user guidance), `scripts/assemble.py` (deterministic artifact writing; see role-intake-artifacts).
- Subagents: `company-research`, `role-research`, `industry-research` (Phase 4, parallel), `qc-role-intake` (Phase 8).
Resolves deferrals: `application-id-script-implementation`, `introduce-py-implementation`.

#### role-intake-research-scope
Research is three parallel subagents (company / role / industry), each in isolated context returning a fixed `Summary / Key facts / Sources` block. Scoped to only the information that supports the skill's own decisions (title/company/level confirmation, axis classification, first-pass context) — not exhaustive dossiers. Subagents return structured markdown to the caller; the caller owns persistence. Resolves deferral: `research-output-location-and-format`.

#### role-intake-axis-classification
Phase 6 dispatches the `axis-classifier` subagent, which classifies the job against the five axes (primary + secondary where applicable) in isolated context — keeping axis files out of the main session, consistent with research and QC. It is registry-first for every axis: read the axis registry, pick candidate value(s) from the one-line identities, read only the candidate value file(s), then confirm each pick against the value file's Identity / selection criteria before recording it. A pick that does not confirm is re-picked; if no registry value confirms, an axis gap is flagged (recorded in both artifacts, not blocked, not routed to the unbuilt builder skills). Three registries were created so this is consistent across all five axes — `rules/orientations/registry.md`, `rules/levels/registry.md`, `rules/work-states/registry.md` — matching the pre-existing `rules/industries/registry.md` and `rules/specialties/registry.md`.

#### role-intake-artifacts
- Session log → `personal/sessions/<SLUG>_APP-NNN_YYYY-MM_SessionLog.md`: Metadata (APP-NNN, company, role, role level, session-start + research-completed dates), Axis Classification, Axis Gaps.
- Research file → `personal/applications/<SLUG>_APP-NNN_YYYY-MM/research.md`: the three research blocks. A current-state document; re-running research overwrites stale sections, it does not accumulate history.
- APP-NNN is a global sequential counter derived from existing `personal/applications/` folders. No registry or slug-counter machinery.
- Canonical schemas live in `templates/session_log.md` and `templates/research_file.md`. Skills reference the templates rather than inlining the schema, so it stays single-source across role-intake and downstream skills.
- `scripts/assemble.py` performs all deterministic file-writing (folder creation, initial session log, research file, session log finalization) by rendering the templates, rather than the skill's LLM hand-writing artifacts. Every write is section-scoped: it replaces only role-intake's own sections, so re-runs and any sections added by downstream skills are not clobbered.
- The session log and research file are shared multi-skill artifacts: each writing skill owns its own sections and its own portion of the template/spec. Downstream skills (e.g. interview-prep) append their own sections rather than editing role-intake's templates or `assemble.py`. interview-prep's deeper, less-structured research is where the deterministic-script + LLM-free-text hybrid earns its place.
Resolves deferral: `session-log-body-schema`.

#### role-intake-control-flow
The skill operates under `rules/global-rules.md` (loaded in Phase 0): halt and ask on failure/ambiguity, never fabricate, never proceed on partial content. Resume rule superseded 2026-05 by `role-intake-resume-ladder-2026-05`. QC failure (Phase 8) and user approval rejection (Phase 9) both route per `role-intake-phase-routing-standalone-2026-05`. Resolves deferral: `state-detection-logic-and-location`.
Refs: `role-intake-resume-ladder-2026-05`, `role-intake-phase-routing-standalone-2026-05`, `role-intake-user-approval-gate-2026-05`.

#### role-intake-resume-ladder-2026-05
On re-invocation the user is asked new or resume, then supplies the APP-NNN. The skill probes artifacts in the application folder and lands at the right phase via a ladder (first match wins):
1. Folder missing → halt, ask user (likely wrong APP-NNN).
2. `research.md` missing → Phase 4.
3. Axis classification section still `_(pending)_` in the session log → Phase 6.
4. All filled → Phase 8 (re-QC).

One-line announce, auto-proceed, no interactive confirm. The probe relies on Phase 3 atomicity (folder + `jd.md` + session log written together per `role-intake-jd-persistence-2026-05`). Phase 6 → Phase 7 split deliberately not introduced — re-running axis-classifier is a cheap recovery from interruption in that narrow window, and avoids splitting `assemble.py finalize`.
Supersedes resume rule in `role-intake-control-flow`.
Refs: `role-intake-jd-persistence-2026-05`.

#### role-intake-metadata-confirmation-gate-2026-05
Phase 2 infers title, company, level, and industry from the JD; prompts the user for any value that couldn't be inferred; presents the full set for explicit confirmation before Phase 3 persistence:

```
Confirm role metadata:
  Title:    <inferred or supplied>
  Company:  <inferred or supplied>
  Level:    <inferred or supplied>
  Industry: <inferred or supplied>
Reply with corrections or "confirmed".
```

Universal gate — every value, not just conflicts. Reason: extraction can be wrong silently (multi-title JDs, ambiguous parent-vs-subsidiary names) and Phase 3 persists the values; better to confirm before persistence. Industry is confirmed here so Phase 4 `industry-research` runs against a user-approved target — a wrong industry inference wastes a parallel research pass.

#### role-intake-jd-persistence-2026-05
Phase 3 writes the JD into the application folder as `jd.md`. If the user supplied role communications in Phase 1, those are written as `comms.md`. Both files plus the initial session log are written atomically by `scripts/assemble.py init` — when the folder exists, all three exist.

Session log metadata block gains four fields:
- `JD file:` — `jd.md`
- `JD source:` — URL, original file path, or `"pasted"`
- `Comms file:` — `comms.md` (or blank if no comms)
- `Comms source:` — URL, original file path, `"pasted"`, or blank

Resume relies on this atomicity per `role-intake-resume-ladder-2026-05`. Source fields preserve traceability when the original file location is later cleared.

#### role-intake-user-approval-gate-2026-05
Phase 9 grows from bare handoff into user-approval-and-handoff, running after Phase 8 PASS. Surfaces:
- Metadata: title, company, level, industry
- Per-axis primary/secondary classification
- Axis gaps
- Paths to session log and research file

User approves or raises issues. For each issue the skill assesses impact and recommends a path:
- **Could alter conclusions or outcomes** (e.g., level shift affecting axis, industry shift invalidating industry research) → recommend re-run, route back per `role-intake-phase-routing-standalone-2026-05`.
- **No downstream impact** (typo, capitalization, swap primary/secondary between already-confirmed values) → recommend direct edit to the session log, then re-QC.

User chooses path. Apply, re-QC, re-present the approval block. Loop until approval. Separation rationale: QC validates structure and consistency mechanically; user validates content judgment; both gate handoff.

#### role-intake-phase-routing-standalone-2026-05
The route-back table sits as a standalone section after Phase 9 in SKILL.md, consumed by both Phase 8 (QC failures) and Phase 9 (user approval rejections). Renamed from "QC failure routing" to reflect dual use. Maps finding type to owning phase:
- Metadata wrong → Phase 2
- Research incomplete or wrong → Phase 4
- Axis classification wrong, or gap recorded incorrectly → Phase 6
- Session log field missing → Phase 7

Re-run forward from the routed phase, re-QC, then (Phase 9 path) re-present the approval block.

#### role-intake-phase-6-gap-recommendation-2026-05
When Phase 6 flags an axis gap, the skill surfaces it at Phase 6 (not Phase 9) with a brief explanation and a choice per gap:
- (a) halt and invoke `<axis>-builder` to author a new value file; re-invoke role-intake afterward (resume ladder returns to Phase 6).
- (b) record the gap in the session log and proceed to Phase 7.

Placement at Phase 6, not Phase 9, avoids running Phases 7-8 on a known-incomplete classification.
Refs: `role-intake-axis-classification`, `builder-sequencing-industry-first`.

#### role-intake-critical-requirements-extraction-2026-05
Role-intake gains a critical-requirements extraction step. A new sub-agent `critical-requirements-extractor` reads the JD and writes a structured list of competency requirements into `research.md` as a new top-level `## Critical Requirements` section.

**Why in role-intake, not retrieval.** Critical requirements describe the JOB, not the candidate's matched experience. They belong alongside other JD-understanding artifacts (axis classification, role/company/industry research), not inside retrieval's manifest. Centralizing extraction in role-intake means every downstream consumer (retrieval, gap analysis, CV creation, interview prep) reads the same canonical artifact rather than re-extracting.

**Three-field schema per requirement:**
- **Text:** the requirement phrased as a concrete competency or qualification.
- **Type:** one of `must-have` (explicit hard requirement), `preferred` (explicit nice-to-have), `duty-derived` (implied by duties/responsibilities), `contextual` (implied by company/role/team context).
- **Source:** short pointer to where in the JD the signal came from (e.g., "Required Qualifications #2", "Day-to-day Responsibilities", "About the Team paragraph").

**Comprehensive JD scan.** The sub-agent reads the entire JD, not just sections labeled "Requirements" or "Qualifications." Duties, responsibilities, "about the role" paragraphs, and team/company-context language often carry competency signals the hiring panel will use even when not labeled as requirements. The `Type` field captures the source nature so downstream consumers can weigh accordingly.

**Downstream consumption:**
- Retrieval: critical requirements are the matching target for the LLM-judgment passes (inventory entries, narratives, themes), replacing raw JD text as the matching target.
- Gap analysis: `Type` drives severity. Unmet `must-have` = high severity; unmet `preferred` = low; unmet `contextual` may not constitute a real gap.
- CV creation: `must-have` requirements receive explicit CV bullets; `preferred` and `duty-derived` widen the matching surface; `contextual` informs framing/voice rather than bullets.
- Interview prep: requirements inform anticipated panel questions.

**Architecture:**
- New sub-agent: `critical-requirements-extractor`. Parallel to the existing `company-research`, `role-research`, `industry-research` subagents. Keeps role-intake SKILL.md from accumulating inline extraction logic.
- Invocation phase TBD at build time (likely Phase 4 alongside the three research subagents, or a Phase 5 JD-understanding consolidation). Output flows through `scripts/assemble.py` writing into `research.md`.
- `templates/research_file.md` gains a new `## Critical Requirements` section carrying the three-field per-requirement structure.

Refs: `retrieval-architecture-2026-05`, `role-intake-architecture`, `role-intake-research-scope`, `role-intake-artifacts`.

### gap-analysis

(The skill formerly referenced as `role_evaluation` in pre-build design notes is named `gap-analysis` as built. The old slug `gap-analysis-cluster-derivation` is retained below as a deferred presentation enhancement; v1 of the built skill renders requirements in CR-NNN order rather than cluster-grouped.)

#### gap-analysis-architecture-2026-05
Built artifact-producing skill running after retrieval; stopping point for the user's pursue / don't-pursue decision; handoff for downstream CV creation, interview prep, and career brief.

**Pipeline position.** role-intake -> retrieval -> **gap-analysis** -> [cv_targeted | interview_prep | career_brief]. Gap analysis reads `research.md` (critical requirements + role/company/industry context), `retrieval.md` (per-entry scored signals), the session log's axis classification, and the user-info eligibility sections. It writes `gap_analysis.md` to the application folder, appends a `## Gap Analysis` section to the session log, and appends per-closure entries to a cross-application staging file at `personal/profile/profile_updates_pending.md`.

**Unit.** One record per critical requirement (CR-NNN assigned in the order requirements appear in role-intake's list). Each carries a status from the locked taxonomy: `covered`, `closed`, `language-shift`, `interview-deferred`, `unresolved`. Status `closed` applies when the user provided clarifying information during the Phase 4 loop that resolved an initial gap; the new information is queued for the staging file.

**Phases (high level).** 0 intro; 1 load context; 2 eligibility / fit-signal check (work auth, geographic prefs, exclusions; flags surface for user override / stop, no automatic short-circuit); 3 gap detection via `gap-detector` sub-agent (arc-first per `arc-composition-for-high-impact-roles`, then entry-level); 4 interactive closure loop (categorize-first walk-evidence-items shape; new info captured to staging buffer); 5 fit scoring + de-emphasize identification (via `de-emphasize-identifier` sub-agent) + recommendation; 6 assemble outputs (gap_analysis.md via `scripts/gap_assemble.py`, staging entries via `scripts/staging_append.py`, session log section via `scripts/session_log.py`); 7 QC via `qc-gap-analysis` sub-agent (loop cap 3); 8 user decision + handoff (on yes, prompt to run the separate profile-update skill now or defer; on no, record in `personal/do-not-pursue/`).

**Fit-score formula.** Per-requirement weight by Type (must-have=3, preferred=2, contextual=1, duty-derived=1); per-requirement coverage credit by status (covered / closed / language-shift = 1.0; interview-deferred / unresolved = 0.0). Fit score = `sum(weight * credit) / sum(weight)`, rendered as percentage with one decimal place. Separately tracked: count of unmet must-haves (must-haves with status interview-deferred or unresolved).

**Recommendation.** LLM judgment in main skill from fit score, unmet must-haves count, and eligibility flag outcomes. Three labels: `Proceed`, `Proceed with caution`, `Do not pursue` + a 1-2 sentence rationale. Hard rule: an eligibility flag whose user decision is `stop` forces `Do not pursue`. Soft anchors (consistency, not threshold): fit >= ~75% reads as high; 50-75% moderate; < 50% low.

**Outputs.** `gap_analysis.md` (current-state, re-runs overwrite) carries header + six sections (Eligibility Flags, Requirements, Language-Shift Cases, De-emphasize, Recommendation; optional sections render `_(none)_` when empty). Session log `## Gap Analysis` section carries run date, fit score, unmet must-haves (with sub-list), recommendation, eligibility flag summary, QC verdict, artifact path. Staging file accumulates `PU-NNN` entries cross-application; processing into inventory / narratives / positioning is the job of a separate profile-update skill (TBD name; out of scope for the gap-analysis build).

**Staging-file discipline.** New information captured to the staging file is concise structured context for correct downstream insertion, not copy-paste content. The profile-update skill adapts captured material to each target doc's conventions; gap-analysis does not write directly into inventory / narratives / positioning. Per the `respect-profile-doc-conventions` feedback memory.

**QC.** `qc-gap-analysis` checks 12 items across structural, content integrity, cross-document consistency, and logic groups; loops up to 3 iterations with per-finding route-back; on bounded-loop failure the artifact ships provisional with findings surfaced in Phase 8 per `artifact-skill-qc-internal`.

Refs: `role-evaluation-and-cv-targeted-separate` (gap analysis as stopping point and handoff artifact), `arc-composition-for-high-impact-roles` (arc-first rule in Phase 3), `retrieval-architecture-2026-05` (gap analysis as downstream consumer of the manifest; raw signals not pre-tiered), `role-intake-critical-requirements-extraction-2026-05` (Type drives severity / coverage credit), `gap-analysis-schema` (deferral resolved here), `respect-profile-doc-conventions` (staging-file discipline).

#### gap-analysis-cluster-derivation
Gap analysis clusters are distinct competency domains, where a domain is a coherent area of professional capability the JD is independently evaluating. Two JD requirements belong in the same cluster when a hiring panel would assess them as part of the same underlying skill set. Cluster count emerges from this grouping; no target range is prescribed.

Prior rule specified "identify the main 3-5 clusters." That was an arbitrary constraint that under-served packed JDs where the competency landscape genuinely spans more domains. A JD with 8 distinct competency domains requires 8 clusters; forcing consolidation to 5 either loses a domain or creates artificially bundled clusters that obscure gaps.

Practical guard: if the analysis produces more than 9-10 clusters, some are likely too granular and should be consolidated. Fewer than 3 clusters suggests the JD has not been read with sufficient granularity.

Derivation process: read the JD; identify distinct competency domains; group related requirements under each domain. The grouping should reflect how a hiring panel thinks about the role's requirements, not the JD's section headings.

**Status (2026-05-27):** Not used in `gap-analysis-architecture-2026-05` v1. The built skill renders requirements in CR-NNN order rather than cluster-grouped; clusters remain a deferred presentation enhancement that the Requirements section's rendering could adopt later without changing the underlying unit (per-requirement record).

Refs: `role-evaluation-and-cv-targeted-separate`, `arc-composition-for-high-impact-roles`, `gap-analysis-architecture-2026-05`.

## Career Workflow Stage

Empty. career_brief, cv_general, profile_update, positioning skill designed at their build time.
