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

### orient-py-implementation
`scripts/display/orient.py` and `scripts/display/orientations.yaml` content.
- Trigger: first long-arc skill built.
- Blocks: full-orientation pattern in classified skills.
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

### orientation-roster-ambiguous-skills
Orientation classification for `interview_capture`, `interview_followup`, `cv_general`, `experience_inventory`, `career_narratives`.
- Trigger: each skill at its design time.
- Blocks: those skill builds.
- Refs: `workflow-communication-conventions`.

### builder-refresh-mechanics
Diff presentation, approval gate shape, file-write flow for create vs refresh across the four axis builders.
- Trigger: first builder skill at design time.
- Blocks: builder skill builds.
- Refs: `builder-mode-parameter`, `four-builders-axis-parity`.

### initial-skill-pack-content-design
Which skill packs at build time (candidate set: clinical_operations, data_science, data_engineering, ai_engineering, quality_compliance, technology_strategy, leadership). How Capability values map.
- Trigger: skill_builder design or first skill pack.
- Blocks: skill pack authoring; downstream Capability validation.
- Refs: `four-orthogonal-axes`, `tag-taxonomy`.

### initial-industry-pack-content-design
Which industries at build time (clinical_development first); content scope (vocabulary, dialect, regulations) vs what stays in inventory.
- Trigger: industry_builder design or first industry pack.
- Blocks: industry pack authoring.
- Refs: `four-orthogonal-axes`.

### cv-targeted-weighted-matching
Weighted matching by JD emphasis: industry-emphasis weights Industry higher; skill-emphasis weights Skill higher; both required = equal weight.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `four-orthogonal-axes`, `experience-inventory-domain-scoping`.

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
Apply `experience-inventory-domain-scoping`, `-section-6-rename`, `-section-4-restructure`, `-section-5-restructure`, `-section-7-flat-records`, `-section-ordering`, `field-rename-outcome-purpose` to `Experience_Inventory.md`. Roughly 190+ EX entries and 5+ PR entries gain Industry/Skill fields.

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

### org-maturity-content-rewrite
Rewrite `org_maturity.md` header (currently old-repo language about "catalog of CV format references").
- Trigger: organizations folder migration.
- Blocks: organizations folder migration.
- Refs: `organizations-folder`.

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
