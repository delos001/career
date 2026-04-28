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

### initial-specialty-pack-content-design
Specialty pack roster: clinical-operations, data-engineering, ai-engineering, quality-compliance, people-leadership. Initial Capability values drafted in each pack; validation against current practitioner usage pending specialty_builder refresh-mode run.
- Trigger: specialty_builder design or first refresh against drafted packs.
- Blocks: validated Capability lists; downstream Capability validation in inventory.
- Refs: `five-orthogonal-axes`, `tag-taxonomy`.

### initial-industry-pack-content-design
Which industries at build time (clinical_development first); content scope (vocabulary, dialect, regulations) vs what stays in inventory.
- Trigger: industry_builder design or first industry pack.
- Blocks: industry pack authoring.
- Refs: `five-orthogonal-axes`.

### cv-targeted-weighted-matching
Weighted matching by JD emphasis: industry-emphasis weights Industry higher; specialty-emphasis weights Specialty higher; both required = equal weight. Generalizes to all five axes once per-axis weighting heuristics are defined.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `five-orthogonal-axes`, `experience-inventory-domain-scoping`.

### cv-targeted-hybrid-retrieval
Structured tag filter + semantic similarity ranking.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `experience-inventory-domain-scoping`, `stack-retrieval`.

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

### cv-targeted-content-rules-from-axes
Procedural content stripped from axis rule files (`rules/orientations/*`, `rules/levels/*`, `rules/industries/*`, `rules/specialties/*`, `rules/work-states/*`) during data-only-discipline cleanup. Belongs in the cv_targeted skill, not the rule files. Items to apply when designing cv_targeted:
- Bullet construction (CCAR framework). IC compresses Context/Challenge into one clause; leadership requires all four components.
- Impact statement types and preference order: Type 1 quantified, Type 2 bounded qualitative, Type 3 contextual narrative. Fallback chain when quantitative data is absent (bounded qualitative → contextual narrative → proxy metrics → scope as signal).
- Tag query logic: filter by Role Level for leadership; do not filter by Role Level for IC.
- Compound tag query requirement for `platform-technology` orientation: single-tag queries on Technology Implementation are invalid; require Capability AND Capability or Capability AND Context combinations.
- Core Competencies zoning for `data-analytics` orientation (3 zones: data strategy/governance, analytics capability/operating model, technical credibility) and `platform-technology` orientation (3 zones: technology strategy/platform governance, systems/domain knowledge, analytical/process credibility).
- Selected Projects voice exception: leadership voice rules apply to Professional Experience entries only; project entries follow design/build voice without organizational framing.
- Achievement framing patterns by orientation/level (problem → strategy → execution → outcome variants per orientation). Full set in `temp/Archetype_*.md`.
- Inventory coverage gap flagging: when fewer than two High priority compound queries return qualifying entries, flag before generating.
- Adjacency translation behavior: entries tagged with adjacent industries/specialties/orientations/work-states get translated (not filtered out) per adjacency weight; non-adjacent entries get role-translation only (cross-cutting capabilities), not industry-translation.
- Acronym expansion rule: spell out less-common acronyms on first use; common in-industry acronyms (e.g., FDA, GCP, ICH, IRB in pharma) need no expansion.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `rules/orientations/*`, `rules/levels/*`, `rules/industries/*`, `rules/specialties/*`, `rules/work-states/*`, `temp/Archetype_*.md`, `temp/content_rules_ic.md`, `temp/content_rules_leadership.md`.

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
- Refs: `temp/format_spec.md`, `temp/content_rules_ic.md`, `temp/content_rules_leadership.md`, `temp/Archetype_*.md`, `format-spec-cv-boundary`.

### role-evaluation-orientation-selection-from-axes
Orientation selection logic and match criteria stripped from axis rule files. Belongs in role_evaluation, not rule files. Items to apply when designing role_evaluation:
- Orientation match criteria split by IC vs leadership scope (e.g., transformation-strategy at leadership level requires enterprise-level organizational change; transformation-strategy at IC level requires execution within a transformation program). Full set in `temp/Archetype_*.md`.
- Disambiguation logic ("verify against orientation N if..."): if the role centers on standardization or steady-state efficiency, verify against process-operations; if platform-focused, verify against platform-technology; if data-strategy-focused, verify against data-analytics; if enterprise organizational transformation, verify against transformation-strategy.
- Dual-orientation detection: when a role legitimately maps to two orientations; primary/secondary asymmetric authority per `dual-orientation-asymmetric-authority`.
- Orientation exclusion criteria (route-to-other-orientation logic): each orientation file's Identity section names exclusion conditions; role_evaluation enforces them during orientation selection.
- Trigger: role_evaluation skill design.
- Blocks: role_evaluation build.
- Refs: `rules/orientations/*`, `temp/Archetype_*.md`, `dual-orientation-asymmetric-authority`.

## Migration Items

All trigger on foundation execution; all block foundation completion. Apply the referenced design decisions to the existing files in `personal/knowledge/`.

### user-info-existing-data-migration
Apply `user-info-rename-and-schema` to `Contact_Info.md`.

### career-narratives-existing-data-migration
Apply `career-narratives-schema` to `Career_Narratives.md`.

### career-narratives-cleanup-script
One-time script: strip Pandoc underline syntax; remove HTML comment blocks. Mechanical.
- Refs: `career-narratives-schema`.

### positioning-existing-data-migration
Apply `positioning-schema` to `Positioning.md`. Migration surfaces existing inaccuracies: "Story 7 (Direct Report Accountability)" is misclassified (it's DC-003); appendix lists Stories 1-9 but 10 exist (ST-010 may need addition).

### experience-inventory-existing-data-migration
Apply `experience-inventory-domain-scoping`, `-section-6-rename`, `-section-4-restructure`, `-section-5-restructure`, `-section-7-flat-records`, `-section-ordering`, `field-rename-outcome-purpose` to `Experience_Inventory.md`. Roughly 190+ EX entries and 5+ PR entries gain Industry/Specialty fields.

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
When to convert `temp/design_decisions.md` to numbered ADR files. Retroactive vs forward-only.
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
