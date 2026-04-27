# Career Repo Open Questions

Items blocking specific work that need answers now. When answered, move resolved decision to `design_decisions.md` and remove from this file. Protocol in memory `process_session_protocol.md`.

## Active

### axis-completeness
Are the current four axes (Specialty, Industry, Skill, Level) the right and complete set for what JDs require? Surfaced via discrete/continuous analysis (prior session): JD elements decompose into discrete (presence/threshold check, gap-analysis territory) and continuous (weighted match/ranking, axis territory). Continuous independent dimensions → axes. Continuous nested dimensions → in-axis vocabulary (e.g., Capability values inside discipline packs). Discrete elements → filter checks during gap analysis.

Sub-questions:
- (a) **Org Stage**: promote to fifth axis (continuous, independent per the framework) or keep as `org_maturity.md` modifier? Currently the Org Context tag value (Mature/Enterprise, Scaling, Greenfield, Independent) plus the modifier rule. Decision affects inventory schema (Org Stage tag field on entries) and axis-builder roster (would add `stage-builder` and `stage_research`).
- (b) **Tools**: first-class tag dimension on entries (allowing categorical filter "must have Salesforce" in cv_targeted), or stay as Inventory Section 5 reference picked up only by semantic retrieval? Discrete element.
- (c) **Soft skills / executive qualities**: first-class treatment or implicit in Specialty + Capability framing? User leaning toward implicit; worth closing.
- (d) **Rename Skill axis → Discipline**: conceptually agreed (no collision with `.claude/skills/` or Capability field). Execution pending (a)-(c) since axis count and roster may shift.

- Triggered by: discrete/continuous analysis (prior session) showing axis composition must be validated before foundation can proceed.
- Blocks: foundation work. Supersedes `foundation-execution-order` and `knowledge-doc-update-mechanism` (cannot resolve until axis composition is settled).
- Refs: `four-orthogonal-axes`, `level-axis-two-buckets`, `tag-taxonomy`, `experience-inventory-section-5-restructure`, `organizations-folder`.

### foundation-execution-order
In what order across knowledge documents and axis builder skills?
- (a) Migrate existing knowledge docs by hand → build knowledge-doc builder skills against migrated examples → build axis builders.
- (b) Axis builders first (greenfield) → migrate knowledge docs → build knowledge-doc builders.
- (c) Knowledge docs only via builder skills (no manual migration); start with smallest.
- (d) Interleave (axis builders + knowledge-doc audit independent).
- Triggered by: operating-model lock-in.
- Blocks: starting foundation work.
- Downstream of: `axis-completeness` (axis count and rename change scope of both migration and builder roster).
- Refs: `approach-foundation-first`, `four-builders-axis-parity`, `knowledge-document-roster`.

### knowledge-doc-update-mechanism
Hand-edit, builder-skill refresh-mode, or one-time migration script for existing knowledge documents?
- (a) Hand-edit: fastest, no reusable skill.
- (b) Builder-skill refresh: slower this round; produces reusable refresh capability.
- (c) Migration scripts for mechanical pieces; hand-edit the rest.
- Triggered by: foundation execution decision.
- Blocks: knowledge-document updates.
- Downstream of: `axis-completeness` and `foundation-execution-order`.
- Refs: `user-info-rename-and-schema`, `career-narratives-schema`, `positioning-schema`, `experience-inventory-domain-scoping`, `builder-mode-parameter`.
