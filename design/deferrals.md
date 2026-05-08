# Career Repo Deferred Items

When a deferral's trigger fires, promote to `open_questions.md`. Protocol in memory `process_session_protocol.md`.

## Build-Time Tasks

### application-id-script-implementation
Script: prompts for company slug at first encounter, stores slug + name in `rules/organizations/company-slugs.yaml`, increments counter, returns compound ID.
- Trigger: first skill needing application ID (role_evaluation).
- Blocks: role_evaluation skill build.
- Refs: `application-id-format`, `company-slug-registry`.

### session-log-parser-tests
Tests verifying latest-wins per topic (decision entries) and per phase (phase_complete entries).
- Trigger: parser implementation lands.
- Blocks: production session log parser.
- Refs: `session-log-frontmatter-schema`.

### vocabularies-reference-script
`scripts/registry/generate_vocabularies.py`. Reads tag/registry sources across `rules/`; generates `VOCABULARIES.md`.
- Trigger: first tag source exists.
- Blocks: vocabulary browsing (not a skill blocker).
- Refs: `tag-taxonomy`.

### metadata-header-reconciliation-script
Sweeps in-scope docs, parses metadata headers, cross-references against COMPONENTS.md and skill load patterns. Flags drift either direction.
- Trigger: first metadata header in place AND at least one consuming skill.
- Blocks: drift detection (not a hard blocker).
- Refs: `document-metadata-header-discipline`, `component-documentation-discipline`.

### introduce-py-implementation
`scripts/display/introduce.py` and `scripts/display/introductions.yaml` content.
- Trigger: first long-arc skill built.
- Blocks: full-introduction pattern in classified skills.
- Refs: `workflow-communication-conventions`.

### research-notes-disposition
`design/axis_research_notes.md` retained as historical record of pre-reconciliation research candidates. Disposition deferred until axis-builder skills are built — at that point either delete the notes or formalize them into a research-sources file (precedent from prior projects where research sources were maintained as permanent reference).
- Trigger: axis-builder skills built (industry_builder, specialty_builder, orientation_builder, level_builder, work_state_builder).
- Blocks: nothing currently.
- Refs: `design/axis_research_notes.md`, `builders-axis-parity`.

### inventory-builder-research-classification-sections-5-6
experience_inventory builder skill needs a research component to classify Section 5 (Technical Experience) tools and Section 6 (Industry Exposure Profile) content against industry-pack and specialty-pack vocabularies. Drives downstream retrieval relevance and cv_targeted's ability to surface section content matched to JD industry/specialty signals.
- Trigger: experience_inventory builder skill design.
- Blocks: experience_inventory builder build; cv_targeted's section-5/section-6 consumption pattern.
- Refs: `experience-inventory-section-5-restructure`, `experience-inventory-section-6-rename`, `cv-targeted-content-rules-from-axes`.

### inventory-builder-quality-check-encoding
experience_inventory builder must encode all quality checks accumulated across reconciliation passes, so future inventory creation/refresh does not require manual reconciliation. Specification consolidated in `design/inventory_builder_quality_checks.md`; categories: structural integrity, content quality within entries, cross-entry quality, voice consistency, coverage, taxonomic notes. New checks surfaced during ongoing reconciliation get added to that file inline.
- Trigger: experience_inventory builder skill design.
- Blocks: experience_inventory builder build.
- Refs: `design/inventory_builder_quality_checks.md`, `inventory-builder-research-classification-sections-5-6`.

### qc-rules-execution-mode-tagging
Re-tag each rule in `design/inventory_builder_quality_checks.md` with an execution-mode dimension (auto / quick-review / judgment) alongside its existing shape category (Structural / Content / Cross-entry / Voice / Coverage / Taxonomic). Shape describes what kind of issue the rule catches; execution-mode describes what handling a finding costs the user. The two are orthogonal. Goal: enable a QC report (and eventual QC agent) to sort/group findings by mode so user engagement matches activity importance — auto-fixes execute silently, cheap-review batches surface as tables, judgment findings get full structured presentation. Insight surfaced 2026-05-08 during exploration of QC efficiency: user couldn't tell from "verification" whether a finding was a 30-second decision or a 30-minute one, which contributed to the 6-session / 8-hour cost of the prior audit.
- Trigger: before next QC pass after the immediate final clean pass; or before QC agent design.
- Blocks: nothing currently; QC can run with current organization.
- Refs: `design/inventory_builder_quality_checks.md`, audit-phase-ordering rule (in same file).

### inventory-qc-findings-decision-log
A decision log for QC findings on the experience_inventory that could not be fully closed by updating the source document (e.g., user-reviewed findings resolved as "no change needed; reviewed YYYY-MM-DD with reason"). Goal: prevent re-flagging the same findings on subsequent QC rounds and avoid wasted review cycles on settled questions. Expected scope minimal: primary resolution path should always remain source-document updates that make the finding self-evidently inapplicable on the next pass; the decision log captures only the residual cases where source-update doesn't dispel the finding (e.g., a tag that looks ambiguous on its face but has a documented justification). Format, storage location, and entry schema TBD.
- Trigger: experience_inventory builder skill design.
- Blocks: nothing currently (manual audits proceed with the user's mental model of "no-change-needed").
- Refs: `inventory-builder-quality-check-encoding`, `design/inventory_builder_quality_checks.md`.

### registry-overlap-tracking
Use `rules/industries/registry.md` (or an extension file) as a cross-reference of which terms appear in which industry files, so updates to shared regulatory/vocabulary terms (FDA guidance, ICH adoptions) can be propagated to all relevant files. Full-enumeration approach (`industry-files-full-enumeration`) duplicates shared terms across pharma/biotech/cro; redundancy is acceptable now but update-cost grows over time.
- Trigger: first shared-term update where propagation cost surfaces as friction; or earlier if foundation tooling investment is warranted.
- Blocks: nothing currently.
- Refs: `industry-files-full-enumeration`.

### axis-programmatic-slicing-audit
Audit all axes (industries, specialties, orientations, levels, work-states) to verify section structure supports programmatic section-level retrieval rather than full-file reads into LLM context. Goal: skills consume only relevant sections of axis files (Vocabulary, Dialect, Emphasis, Adjacency individually addressable), not entire files. Refactor where not.
- Trigger: knowledge files finalized.
- Blocks: section-level retrieval scripts; downstream skills depending on retrieval pattern.
- Refs: `axes-file-schema`, `stack-retrieval`.


## Per-Skill Design Items

### session-log-body-schema
Entry format, granularity, field set, ordering, timestamp precision, state-transition triggers, first-write contents.
- Trigger: each consuming skill at design time.
- Blocks: any skill writing to session log.
- Refs: `session-log-frontmatter-schema`.

### state-detection-logic-and-location
Form and location: standalone rule file, per-skill, or hybrid.
- Trigger: first skill needing resume-point determination (role_evaluation).
- Blocks: role_evaluation skill build.
- Refs: `state-detection`.

### gap-analysis-schema
Output schema for the role_evaluation gap analysis artifact: which axis values to capture from JD, JD emphasis signals (must-haves vs nice-to-haves), detected vocabulary, and application-specific framing notes that cv_targeted will consume. Format depends on axis structure (now stable post-axis-cleanup) and on the matching protocol per `role-evaluation-axis-matching-protocol`.
- Trigger: role_evaluation skill design.
- Blocks: role_evaluation build; cv_targeted consumes this format and depends on it.
- Refs: `role-evaluation-and-cv-targeted-separate`, `role-evaluation-axis-matching-protocol`, `cv-targeted-weighted-matching`.

### research-output-location-and-format
Where research sub-agent outputs land and what format.
- Trigger: first skill invoking a research sub-agent.
- Blocks: any skill calling research.
- Refs: `research-sub-agents-roster`.

### introduction-roster-ambiguous-skills
Introduction classification for `interview_capture`, `interview_followup`, `cv_general`, `experience_inventory`, `career_narratives`.
- Trigger: each skill at its design time.
- Blocks: those skill builds.
- Refs: `workflow-communication-conventions`.

### builder-refresh-mechanics
Diff presentation, approval gate shape, file-write flow for create vs refresh across the four axis builders.
- Trigger: first builder skill at design time.
- Blocks: builder skill builds.
- Refs: `builder-mode-parameter`, `builders-axis-parity`.

### cv-targeted-weighted-matching
Weighted matching by JD emphasis: industry-emphasis weights Industry higher; specialty-emphasis weights Specialty higher; both required = equal weight. Generalizes to all five axes once per-axis weighting heuristics are defined.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `five-orthogonal-axes`, `experience-inventory-domain-scoping`, `axis-adjacency-weights-redefinition`.

### cv-targeted-hybrid-retrieval
Reshaped 2026-05-01 per `cv-targeted-retrieval-architecture-2026-05`. Two-pass hybrid: (1) semantic ranking over a Description-only payload returns candidate IDs; (2) supplemental tag-pulls driven by role_evaluation's matched axis values catch entries whose descriptions undersell their nature (Specialty/Orientation are the natural triggers; Industry weights ranking; Level/Work-state are framing-only). Merge, dedup, then load full entry detail for the merged candidate set. Implementation details (pre-extracted Description payload generation, embedding vs LLM-judgment, merge weighting) deferred to cv_targeted skill design.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `cv-targeted-retrieval-architecture-2026-05`, `role-evaluation-axis-matching-protocol`, `experience-inventory-domain-scoping`, `stack-retrieval`.

### cross-axis-composition-mechanism
Mechanism by which cv_targeted reconciles per-axis composition outputs. Possibilities range from per-axis sub-agents proposing content for their owned surface and engaging in review/challenge rounds to converge, to rule-based application of default precedence with no cross-axis review. Specific implementation deferred to cv_targeted skill design.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `axes-composition-precedence`, `cv-targeted-content-rules-from-axes`, `cv-targeted-weighted-matching`.

### axis-adjacency-weights-redefinition
Numeric adjacency weights stripped from all axis file frontmatter; rule-format adjacency text in file bodies remains as actionable content. Weights to be re-authored with documented semantics at cv_targeted skill design — what a weight should drive (translation strength threshold, retrieval ranking, bullet count modulation, or other) is undefined and was never deliberately set when the original weights were authored.
- Trigger: cv_targeted skill design specifies what adjacency weights should drive in translation behavior.
- Blocks: cv_targeted weighted-translation behavior.
- Refs: `cv-targeted-weighted-matching`, `cv-targeted-content-rules-from-axes`.

### level-builder-design
Full level_builder design, including whether/when to split `leadership.md` into finer levels.
- Trigger: first new level being authored or level_builder design.
- Blocks: level_builder build.
- Refs: `level-axis-two-buckets`.

### level-axis-finer-grained-files
Whether/when to split `leadership.md` into people manager, senior leadership, c-suite, etc.
- Trigger: first request for finer-grained level distinction.
- Blocks: nothing currently.
- Refs: `level-axis-two-buckets`.

### ic-axis-finer-grained-files
Parallel to `level-axis-finer-grained-files`: whether/when to split `ic.md` into junior-IC, mid-IC, senior-IC (Staff/Principal). 2026-04-29 research surfaced a meaningful gap between junior IC framing (project scope, hands-on verbs) and Staff/Principal framing (architecture-scale decisions, cross-team influence, influence without authority). Currently bridged within one file via voice/scope qualifiers ("differs in depth, independence, complexity, and breadth of technical influence"). Splitting deferred until a Staff/Principal-flavored role application surfaces and the unified file's framing fails to carry senior IC voice cleanly.
- Trigger: Staff/Principal-flavored role application where unified `ic.md` framing does not produce a clean CV; OR resolution of `level-axis-finer-grained-files` (the leadership-side parallel) creates pressure for symmetric IC granularity.
- Blocks: nothing currently.
- Refs: `level-axis-two-buckets`, `level-axis-finer-grained-files`.

### cv-targeted-content-rules-from-axes
Procedural content stripped from axis rule files (`rules/orientations/*`, `rules/levels/*`, `rules/industries/*`, `rules/specialties/*`, `rules/work-states/*`) during data-only-discipline cleanup. Belongs in the cv_targeted skill, not the rule files. Items to apply when designing cv_targeted:
- Bullet construction (CCAR framework). IC compresses Context/Challenge into one clause; leadership requires all four components.
- Impact statement types and preference order: Type 1 quantified, Type 2 bounded qualitative, Type 3 contextual narrative. Fallback chain when quantitative data is absent (bounded qualitative → contextual narrative → proxy metrics → scope as signal).
- Tag query logic: filter by Role Level for leadership; do not filter by Role Level for IC.
- Compound tag query requirement for `platform-technology` orientation: single-tag queries on Technology Implementation are invalid; require Capability AND Capability or Capability AND Context combinations.
- Core Competencies zoning for `data-analytics` orientation (3 zones: data strategy/governance, analytics capability/operating model, technical credibility) and `platform-technology` orientation (3 zones: technology strategy/platform governance, systems/domain knowledge, analytical/process credibility).
- Selected Projects voice exception: leadership voice rules apply to Professional Experience entries only; project entries follow design/build voice without organizational framing.
- Achievement framing patterns by orientation/level (problem → strategy → execution → outcome variants per orientation).
- Inventory coverage gap flagging: when fewer than two High priority compound queries return qualifying entries, flag before generating.
- Adjacency translation behavior: entries tagged with adjacent industries/specialties/orientations/work-states get translated (not filtered out) per adjacency weight; non-adjacent entries get role-translation only (cross-cutting capabilities), not industry-translation.
- Acronym expansion rule: spell out less-common acronyms on first use; common in-industry acronyms (e.g., FDA, GCP, ICH, IRB in pharma) need no expansion.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `rules/orientations/*`, `rules/levels/*`, `rules/industries/*`, `rules/specialties/*`, `rules/work-states/*`.

### cv-format-spec-from-axes
Bullet formatting, section order, item counts, and page targets stripped from axis rule files. Belongs in CV format spec, not rule files. Items to apply when authoring/refining CV format spec:
- Bullet length: target 2 lines per bullet; 3 lines acceptable for highest-value complex achievements with significant detail; 4+ lines never acceptable (compress or split).
- Em-dash rules: prohibited as clause connectors in bullet text and prose (rewrite or use natural connective language); permitted only as structural separators in company/location header lines.
- Section order: Professional Summary, Core Competencies, Professional Experience, Selected Projects (only if entries exist), Education, Certifications and Training, Technical Proficiencies. Identical across all four specialties; format-spec home because it does not vary by specialty.
- Core Competencies item counts: 8-10 items at IC, 8-12 items at leadership.
- Page targets: 2-3 pages for IC; 4-5 pages for leadership (flexibility for role depth; do not artificially truncate relevant content).
- No unnecessary carriage returns; spacing handled by format spec.
- Trigger: CV format spec authoring or refinement.
- Blocks: CV format spec completion.
- Refs: `design/format_spec.md`, `format-spec-cv-boundary`.

### role-evaluation-orientation-selection-from-axes
Orientation selection logic and match criteria stripped from axis rule files. Belongs in role_evaluation, not rule files. Items to apply when designing role_evaluation:
- Orientation match criteria split by IC vs leadership scope (e.g., transformation-strategy at leadership level requires enterprise-level organizational change; transformation-strategy at IC level requires execution within a transformation program).
- Disambiguation logic ("verify against orientation N if..."): if the role centers on standardization or steady-state efficiency, verify against process-operations; if platform-focused, verify against platform-technology; if data-strategy-focused, verify against data-analytics; if enterprise organizational transformation, verify against transformation-strategy.
- Dual-orientation detection: when a role legitimately maps to two orientations; primary/secondary asymmetric authority per `dual-orientation-asymmetric-authority`.
- Orientation exclusion criteria (route-to-other-orientation logic): each orientation file's Identity section names exclusion conditions; role_evaluation enforces them during orientation selection.
- Trigger: role_evaluation skill design.
- Blocks: role_evaluation build.
- Refs: `rules/orientations/*`, `dual-orientation-asymmetric-authority`.

## Migration Items

All trigger on foundation execution; all block foundation completion. Apply the referenced design decisions to the existing files in `personal/knowledge/`.

### user-info-existing-data-migration
Applied 2026-05-04. Migration complete. File renamed `Contact_Info.md` → `User_Info.md`; intro paragraph and Usage Notes dropped; `**Used by:** cv_targeted, cv_general` header added; field-value brackets cleaned. External references updated: `temp/support/knowledge_repo_scaffolding/{README.md, SETUP.md}`, scaffolding template renamed to `User_Info.md`. Deeper scaffolding-template content updates (metadata header, phase-based reference stripping, descriptive loading patterns) remain owned by `scaffolding-content-updates`.

### career-narratives-existing-data-migration
Apply `career-narratives-schema` to `Career_Narratives.md`.

### career-narratives-cleanup-script
One-time script: strip Pandoc underline syntax; remove HTML comment blocks. Mechanical.
- Refs: `career-narratives-schema`.

### positioning-existing-data-migration
Apply `positioning-schema` to `Positioning.md`. Migration surfaces existing inaccuracies: "Story 7 (Direct Report Accountability)" is misclassified (it's DC-003); appendix lists Stories 1-9 but 10 exist (ST-010 may need addition).

### experience-inventory-existing-data-migration
All clusters closed. Migration complete.

Closed:
- Cluster C (Company → `Role: RL-NNN` reference): closed 2026-05-04 by `inventory-role-rl-reference-applied-2026-05`. Title field also dropped from EX entries; two RL Title corrections during reconciliation; one compound-title cluster split per-entry between RL-011 and RL-013.
- Step 5 (Competency re-tagging) and Step 6 (Section 8 sub-section reassignment) both rendered moot by `competency-field-and-registry-removed-2026-05`. Field stripped 2026-05-01.

Done 2026-05-01:
- Sections 1-4 restructured with structured-field schemas (Education, Certifications, Affiliations, Training); year-only or YYYY-MM date granularity per section.
- Section 5 cleaned to tools-only discipline; flat-list convention; capability/method tokens stripped (moved to Section 8 territory).
- Section 6 closed: Data Sources renamed from Data Modalities; Data Modalities sub-section dropped.
- Competency field and registry removed entirely (`competency-field-and-registry-removed-2026-05`).

Done 2026-04-30:
- Section 4/5/6/7 initial restructures per their decisions; per-entry Industry/Specialty/Orientation/Level/Work-state tagging across 197 entries; Capability→Competency rename + initial 16-term registry; Outcome→Impact fold; sub-section reorganization (9 moves); 5 PR Work-state Independent→greenfield; Level removed from RL records; field-drift cleanup. Background Roles encoding-artifact cleanup cleared as no-op (bytes are correct UTF-8; appearance was terminal-rendering artifact).

### questions-library-deletion
Delete `personal/knowledge/Questions_Library.md` after manual content extraction if any.
- Refs: `questions-library-eliminated`.

### scaffolding-folder-layout
Folder name, sub-folder layout, file naming for `support/`.
- Trigger: scaffolding migration.
- Blocks: scaffolding migration.
- Refs: `knowledge-document-scaffolding`.

### scaffolding-content-updates
Strip phase-based references; describe loading patterns descriptively; update skill names; add metadata header to `User_Info.md` template.
- Trigger: scaffolding migration.
- Blocks: scaffolding migration.
- Refs: `knowledge-document-scaffolding`, `document-metadata-header-discipline`.

## Periodic Revisits

### staleness-threshold-revisit
Re-evaluate 9-month threshold periodically.
- Trigger: annually or sooner if refresh failure pattern emerges.
- Blocks: nothing currently.
- Refs: `rule-staleness-threshold`.

### staleness-per-axis-overrides
Per-axis overrides on the 9-month threshold.
- Trigger: evidence supports divergent drift rates.
- Blocks: nothing currently.
- Refs: `rule-staleness-threshold`.

### adr-formalization-timing
When to convert `design/design_decisions.md` to numbered ADR files. Retroactive vs forward-only.
- Trigger: project maturation; first need to reference an ADR by number.
- Blocks: nothing currently.
- Refs: `adr-naming`.

### tracker-integration
External Google Drive tracker integration.
- Trigger: user need surfaces.
- Blocks: nothing currently.
- Refs: `tracker-integration-out-of-scope`, `application-id-format`, `session-log-frontmatter-schema`.

### maintained-by-metadata-field
Extending Document Metadata Header schema with `Maintained by:` field.
- Trigger: concrete need (currently in COMPONENTS.md).
- Blocks: nothing currently.
- Refs: `document-metadata-header-discipline`, `career-narratives-schema`.

### crisis-response-as-separate-work-state
`rules/work-states/turnaround.md` notes that acute, event-driven underperformance ("crisis response") is currently absorbed into turnaround, distinct from chronic distress. Decision deferred on whether crisis response should split into its own work-state.
- Trigger: experience-inventory entry surfaces that fits crisis-response framing (acute, event-driven recovery) and reads off-spec under turnaround.
- Blocks: nothing currently.
- Refs: `rules/work-states/turnaround.md`.

