# Career Repo Design Decisions

Running record of design decisions made during evaluation of the draft spec. Updated as we go. Source of truth for the eventual repo build.

---

## Structural

### Pattern A (Framework-Native Skills and Agents)
The repo uses Claude Code's official extension points, not a custom skill/dispatcher pattern. Skills live at `.claude/skills/[name]/SKILL.md` with YAML frontmatter. Agents live at `.claude/agents/[name].md` with frontmatter. Claude Code auto-discovers both. Users invoke a skill via its slash command (e.g., `/role_evaluation`). The framework's skill picker is the entry point. No custom `skill_registry`, no `control.md` dispatcher. `.claude/` travels with the repo.

### Top-Level Containers
`.claude/` (skills + agents + optional project settings), `rules/`, `templates/`, `scripts/`, `outputs/`, `personal/`. Plus `CLAUDE.md` at the repo root. Skills and sub-agents live inside `.claude/` per Pattern A; they are not separate top-level folders.

### QC Organization
Specs (checklists, pass/fail criteria) live in `rules/quality_control/`. Executors live as sub-agents in `.claude/agents/`. Skills call QC; sub-agents execute it in isolated context so QC does not consume the skill's context window and can loop if the skill output is non-compliant.

**Naming convention:** `qc_<scope>_<aspect>.md` for both specs (in `rules/quality_control/`) and executors (in `.claude/agents/`). Scope is what is being QC'd (e.g., `cv`, `gap_analysis`, `interview_prep`); aspect is the dimension (e.g., `format`, `structural`, `content`, `completeness`). Examples: `qc_cv_format`, `qc_cv_structural`, `qc_cv_content`, `qc_gap_analysis_completeness`, `qc_interview_prep_coverage`. The `qc_` prefix is kept on both sides even though it's redundant in the spec path, because the `.claude/agents/` folder contains mixed content (research agents, QC agents) and spec↔executor pairing by matching name matters more than avoiding path redundancy. Flat folder today; subdivide only if count grows too large to scan.

QC is expected to grow as new targets and aspects are identified. Structure accommodates growth without restructuring.

### Template vs Format Spec
Templates are physical carrier files (e.g., Word) that get filled in and persist as outputs. Format specs are structural/rendering rules applied to free-form content. Both folders justified. No DRY issue.

### Scripts Centralized
Top-level `scripts/` folder, subdivided internally (retrieval, resolvers, format conversion, etc.). Not co-located with the skill or sub-agent that uses them, because many scripts (especially retrieval) will be called by multiple consumers.

### Skill Registry and Control Dissolved (Pattern A)
Under Pattern A, the custom `skill_registry` and `control.md` both go away. Framework discovery replaces the registry. The slash-command picker replaces the dispatcher. Per-skill interface metadata lives in the SKILL.md frontmatter (name, description, trigger conditions, etc.). State detection logic (what skill to run based on existing artifacts) either lives in a lightweight rule file under `rules/` referenced by skills that need it, or is embedded in each skill's own startup check.

### role_evaluation and cv_targeted Remain Separate Skills
Kept distinct, not merged into a single "application" skill. The shared-inputs argument for merging is resolved by retrieval scripts (slice-level lookup, not whole-document loading). The GapAnalysis file is the handoff artifact between them, which doubles as a natural stopping point for long workflows and persists evaluation conclusions across sessions. `/role_evaluation` and `/cv_targeted` are invoked independently. "Application" stays as a data-model concept (folder name under `personal/applications/`), not a skill name.

### knowledge_update Collapse
Collapse `knowledge_update_adhoc` and `knowledge_update_inline` into one skill with a mode parameter. A retrieval script fetches only the relevant slice of the underlying knowledge at read time. This retrieval pattern generalizes across the repo to avoid loading full documents when only slices are needed.

---

## Composition Model

### Four Orthogonal Axes
Role evaluation and deliverable production compose four axes:
- **Specialty** (renamed from archetype). Governs deliverable structure (e.g., CV section order, Core Competencies, summary framing).
- **Industry** (sector). Governs vocabulary, dialect, and regulatory framing. Files in `rules/industries/`.
- **Skill** (technical/professional area). Governs Capability vocabulary and skill-specific framing. Files in `rules/skills/`.
- **Level** (IC vs leadership today). Governs framing and voice.

The Industry/Skill split replaces the prior single Domain axis. Inspection of `Experience_Inventory.md` showed that "domain" was conflating two independent concerns: where the work happens (Industry) and what kind of work it is (Skill). Hiring scenarios where a clinical-research company hires an AI engineer require these to weight independently in cv_targeted matching.

Axes are independent files. Overrides exist only where axes genuinely interact. Override discipline: narrow interaction rules, not mini-archetypes. If an override drifts toward restating an axis, split the axis or accept a new specialty.

### Dual-Specialty (Asymmetric Authority)
A role may map to two specialties. Primary governs most surfaces. Secondary gets bounded, explicitly-scoped slots within the deliverable. Primary and secondary do not compete over the same surface. Each deliverable decides what surfaces (if any) it exposes to a secondary.

- CV: secondary appears in 2-3 achievements and 1-2 Core Competencies items. Summary is primary-only.
- Other deliverables: per-deliverable composition rule written as needed.

Existing CV dual-specialty rule transfers in; place at `rules/specialties/cv_dual_specialty_composition.md` (or equivalent location that reflects its CV-specific scope).

### Level Axis: Two Buckets Today, Gradient-Capable Later
Today: IC and leadership only. Later expansion (e.g., staff/principal IC, people manager, senior leadership, c-suite) adds files through the `level_builder` skill (see Rule-Builder Skills section). Level files are deliverable-agnostic (voice/framing). Deliverable-specific concerns (e.g., CV section order) belong in the deliverable's format spec.

The current `leadership.md` will likely need to split or be renamed once finer distinctions are added (people manager vs senior leadership vs c-suite carry materially different voice expectations). That is a `level_builder` design call, deferred until the first new level is authored.

### Skill Stability via Loose Coupling
Skills reference rules by category/slug. A resolver script looks up the current file. Skill body does not hard-code paths, so rule/template/axis churn does not touch skills. Skill interface changes only when skill behavior changes; that is not what caused churn in the prior repo.

---

## Naming

### Terminology and Folder Renames Committed
- `archetypes` → `specialties` (rules folder: `rules/specialties/`)
- `role_level` → `levels` (rules folder: `rules/levels/`)
- Under Pattern A, skills are flat under `.claude/skills/` (no `rule_builders/` parent folder). The old `rule_builders/archetype/` concept becomes a standalone skill such as `.claude/skills/specialty-builder/SKILL.md`.

### File and Folder Naming Convention

Authoritative naming rule for the repo.

**Folders:** lowercase kebab-case. No underscores. Examples: `rules/specialties/`, `docs/decisions/`, `personal/applications/`, `scripts/display/`, `.claude/skills/specialty-builder/`.

**Files:** lowercase. Underscore between semantic fields; kebab within a field. A "semantic field" is a distinct meaning unit (company, identifier, date, document type, round number). Compound document-type tokens (session log, gap analysis, content decisions, interview followup) count as one field, joined with kebab.

Examples:
- `pfizer-001_session-log.md` (two fields: application-id, document-type).
- `gap-analysis_pfizer-001.md` (two fields: document-type, application-id).
- `interview-followup_r1_pfizer-001.md` (three fields: document-type, round, application-id).

Attention files and ADR files are the exceptions (below).

### Attention Files

Capitalized files are reserved for top-tier navigation, reference, or specification documents that a reader should notice first when entering a directory. All-caps signals "read me first / authoritative reference."

Applied set for this repo: `README.md`, `SETUP.md`, `COMPONENTS.md`. If a future attention-tier file emerges (e.g., a repo-level README under a new directory), it inherits capitalization automatically without further discussion.

Dropped from consideration: `LICENSE` (not open source), `CONTRIBUTING.md` (single user), `CHANGELOG.md` (git and ADRs already cover evolution), `SPEC.md` (specs live scoped inside `rules/`).

### ADR Naming

Architecture Decision Records follow the MADR / adr-tools convention:

- Zero-padded three-digit sequential number prefix + kebab-case descriptive title.
- Three digits accommodates 999 decisions.
- Numbers are sequential and never reused. Supersession is a new record that references the old.
- Example: `001-base-overlay-pattern.md`.

Location: `docs/decisions/`. Directory created when formalization happens. The current `temp/design_decisions.md` is an informal ADR log; contents split into individually numbered files during formalization. Retroactive-vs-forward-only timing deferred.

### Specialty File Names
Drop the numeric prefix (previously `a1_`, `a2_`, etc. from the archetype era). Files use descriptive slugs only: `transformation-strategy.md`, `data-analytics.md`, `process-operations.md`, `platform-technology.md`. Retrieval scripts look up by descriptive name, so the prefix adds no functional value.

### Level File Names
Drop deliverable prefix. `ic.md` and `leadership.md` (not `content_ic_cv.md`). Folder path provides context.

### Cascade to Earlier Sections

Earlier inline examples throughout this document predate this taxonomy and use an older underscore-everywhere pattern. Most prominent rule-stating examples updated inline (Specialty File Names above; Application Folder and File Naming Convention in the Lineage and Traceability section). Other inline examples (QC naming at `qc_<scope>_<aspect>`, skill and sub-agent folder identifiers, builder folder names, etc.) stand corrected by the convention above and will be swept during migration.

---

## Terminology

Vocabulary discipline for three granularity levels commonly discussed together:

- **Phase**: a process or major step WITHIN a single skill. Example: within `role_evaluation`, phases might include research, specialty confirmation, fit analysis.
- **Skill**: one standalone skill (e.g., `role_evaluation`, `cv_targeted`, `interview_prep`).
- **Workflow**: the overall project-level flow across skills.

"Phase" is reserved for sub-skill granularity. Skills are not phases even though the project has workflow-level stages. Workflow-level stages are described as workflow stages, not phases.

Matters for: the session log body (`phase_complete` entries refer to within-skill phases), skill authoring docs, and any workflow description that spans multiple skills.

---

## Format Spec (CV)

### Boundary
Format spec = rendering config (fonts, margins, spacing, bullet chars, file-naming pattern). Deliverable-specific, axis-agnostic. Axes shape content and voice. Format spec renders the final file. The existing CV format spec already declares this boundary on its own line 175.

### Transfer Notes
Existing `temp/format_spec.md` transfers largely as-is with two cleanups:
1. Move embedded python-docx code (lines 95-123) to a script under `scripts/`. Format spec stays declarative (values and tables only).
2. Parameterize the hardcoded name in the output filename pattern (line 182). Pull from `personal/config.yaml`.

---

## Rule-Builder Skills Inline Procedure

Under Pattern A, builder skills (`.claude/skills/specialty_builder/SKILL.md`, `.claude/skills/industry_builder/SKILL.md`, `.claude/skills/skill_builder/SKILL.md`, `.claude/skills/level_builder/SKILL.md`) do not reference nested "building rules" files. The construction procedure is the skill itself and lives inside its SKILL.md. No `rules/builders/` folder is created. If construction grows complex enough to warrant extraction later, it can be addressed at that point.

### Four Builders for Axis Parity

One builder per axis: `specialty_builder`, `industry_builder`, `skill_builder`, `level_builder`. Each is wired to its corresponding research sub-agent (see Research Sub-Agents section). `level_builder` closes a prior gap where level expansion was treated as a manual file add. The prior `domain_builder` is replaced by `industry_builder` and `skill_builder` per the Four Orthogonal Axes split. Parity across the four axes is preferred because the pattern is easier to document, remember, and extend consistently.

### Mode Parameter (create / refresh)

Each builder accepts a mode parameter:

- `create` drafts a new rule file from research output. Used for greenfield additions.
- `refresh` targets an existing rule file, re-runs the research sub-agent, diffs the fresh output against the current file, and proposes updates. Used when a rule has gone stale.

Both modes invoke the research sub-agent before drafting or diffing, so research enforcement is not bypassed at refresh time. Pattern mirrors the `knowledge_update` mode-parameter approach. A separate `axis_refresh` skill was rejected because it would duplicate most of the builder logic.

## Workflow Sequence Diagram

Deleted, not relocated. The old registry contained an ASCII workflow diagram; it does not carry over to the new repo. A richer visual (e.g., Visio) may be authored later if useful.

## Interview Template Artifacts

`interview_completion` and `interview_scratch` exist as both blank skeletons (in `templates/`, copied per round) and populated instances (in `personal/applications/<slug>-NNN_<yyyy-mm>/`). Different purposes, two locations, no duplication.

## Stack

**Orchestration:** Claude Code native for most of the workflow (skills as markdown, Task tool for sub-agents with isolated context, hooks, Bash for Python invocation). LangGraph approved for the CV generation loop specifically (perform → QC → fix → QC, potentially parallel format / structural / content QC sub-agents) as a bounded learning experiment. Two hard constraints: (1) no dual state management between Claude Code and LangGraph — one state model, one well-defined integration handoff; (2) if friction materializes beyond the initial learning curve, the experiment stops at the CV loop and does not extend to role_evaluation, interview_prep, or other workflows. Skills outside the CV loop stay Claude Code native.

**Retrieval:** Mixed by content shape. Structured lookup (Python script fetches a known slice by slug/key) for structured documents (Experience_Inventory, Positioning, registries, format specs). RAG reserved for genuinely unstructured content (e.g., interview_scratch notes). Default is structured; add RAG only where structure truly doesn't exist.

**Execution:** Skills are markdown. Deterministic logic is Python scripts invoked via Bash. LLM-judgment stays in the skill or in LLM sub-agents. Build scripts alongside the skill that uses them, not after; never use an LLM where a script can verify a rule deterministically.

---

## Approach for Remaining Design Work

Remaining design proceeds in workflow-dependency (foundation-up) order, not draft-enumeration order. Path:

1. **Lineage and traceability requirements.** What must be tracked (application IDs, session logs, source citations, timestamps, cross-references) and how it is carried across artifacts. Likely precedes knowledge document structure because knowledge docs must be shaped to support lineage needs.
2. **Knowledge documents** (Experience_Inventory, Career_Narratives, Positioning, contact_info). Structure designed to support lineage/traceability and downstream retrieval.
3. **Session-log and application-ID creation.** The first step in any application workflow.
4. **Each workflow step in sequence.** role_evaluation, cv_targeted, interview_prep, interview_capture, interview_followup, career_brief, cv_general.
5. **Remaining items** that don't fit a workflow step, at the end.

Focus at this stage is structure decisions only. No content pass, no implementation work.

Rationale: the prior repo was built starting from CV creation and working backwards. That order required extensive rework as foundational decisions (knowledge doc structure, lineage semantics, retrieval logic) surfaced after downstream work was already committed. Foundation-first prevents that.

---

## Decision Filter for New Additions

Ordered: value → friction → scalability → learning tiebreaker. During active build-out, scope creep and gold plating route to an "enhancements" list for post-build consideration, not inline additions. Full framework lives in memory at `feedback_addition_evaluation.md`.

---

## Global Rules Minimized

`rules/global_rules.md` written as a single file (no `rules/global/` subfolder). Three rules only: never fabricate content, failure handling protocol, never proceed with partial content. Everything else from the old global_rules.md either moved out (APP-NNN to scripts, phase discipline to a skill authoring template, workflow context check to per-skill startup, doc load mechanics to retrieval scripts) or deleted as tautological (Skill Adherence) or redundant (Pacing — consolidated at user-level CLAUDE.md).

## Pending Follow-on Work

- Application ID assignment script: prompts for company slug at first encounter, stores it plus the full company name in `rules/organizations/company-slugs.yaml`, increments the per-company counter, returns the compound ID.
- Session log YAML schema: specify metadata fields and body entry format.
- Session log parser latest-wins tests: verify consumers receive the most recent entry per topic (for `decision` entries) and per phase (for `phase_complete` entries), never superseded data. Authored when parser implementation lands.
- cv_targeted weighted matching logic: when target role JD emphasizes industry experience, weight Industry match higher than Skill match in inventory entry selection. When JD emphasizes skill, weight Skill higher. When both are required, weight equally and surface entries with both tags. Per-skill design work, not structural.
- cv_targeted hybrid retrieval (structured filter + semantic ranking): structured tag filters narrow inventory candidates (e.g., Director-level entries in clinical_development with Capability matching role); semantic similarity ranking against the role description picks the strongest N from the narrowed set. Combines the reproducibility of categorical filtering with relevance ranking from semantic similarity. Considered alongside the weighted matching logic; same per-skill design phase.
- Initial skill-pack content design: which skill packs to create at build time (candidate set: clinical_operations, data_science, data_engineering, ai_engineering, quality_compliance, technology_strategy, leadership), and how Capability values from the existing inventory map to each.
- Initial industry-pack content design: which industries to cover at build time (clinical_development is the obvious first), and what content goes inside (vocabulary, dialect, regulations) versus what stays in the inventory (Section 6 Therapeutic Area exposure may be personal data, not industry-pack content).
- Vocabularies reference generation script (`scripts/registry/generate_vocabularies.py`): reads tag and registry sources across `rules/` and generates `VOCABULARIES.md` at repo root as a single read-only reference for human browsing. Authored when the first tag source (skill pack, industry pack, etc.) actually exists.
- Document metadata header reconciliation script: sweeps all in-scope docs (knowledge documents, rule files, templates), parses metadata headers, cross-references declared `Used by` / `Stamps` / `Generated by` values against COMPONENTS.md entries and actual skill code load patterns. Flags drift in either direction (header claims a consumer that doesn't actually load it, or a skill loads a doc whose header doesn't list it). Authored when the first metadata header is in place and at least one consuming skill exists.

---

## Skill Authoring Template Library

Location: `engops/cheatsheets/skill-templates/`. First template: `human-gated-workflow.md` capturing phase types (Action / QC / Presentation / Transition), workflow communication conventions (see Workflow Communication Conventions section), and closing conventions for this project's pattern. Folder structure from the start so future templates (autonomous-agent, bounded-task, etc.) add as siblings without restructuring. The user's project here is a human-gated AI workflow; other projects may use different patterns, hence the library approach rather than one universal template.

### Authoring Timing

`human-gated-workflow.md` is authored alongside the first skill that uses it, not in isolation now. Authoring in a vacuum risks specifying conventions that need adjustment once a real skill stress-tests them. The conventions settled so far (phase types, orientation pattern, mid-flight narration, consent gating) are recorded in this design_decisions.md document until the template is written.

---

## Pacing Consolidation

Resolved. User-level `CLAUDE.md` holds general response-shape pacing rules (applies across all projects). Skill approval-gating behavior lives in the skill authoring template as a Presentation Phase convention, not as a global rule. No duplicate to remove.

---

## Workflow Communication Conventions

Skills communicate state to the user at three points so the workflow supports thoughtfulness, not just output production. Conventions live in the skill authoring template (`engops/cheatsheets/skill-templates/human-gated-workflow.md`) once that template is authored; captured here in the interim.

### Orientation (forward-looking, at skill start)

Two patterns based on skill complexity:

- **Full orientation** for multi-activity skills where the skill name alone does not convey the arc. Invokes `python scripts/display/orient.py <skill_name>`. Script reads the message body from `scripts/display/orientations.yaml` (keyed by skill name) and prints it. Ends with a "Ready?" consent gate so the user can back out before multi-step commitment.
- **Brief inline preamble** for single-activity skills where the name is self-explanatory. One-sentence declaration written directly in SKILL.md body. No script, no catalog, no consent gate (approval gates inside the skill already provide exit points).

Heuristic for which pattern applies: if the skill name alone conveys what is about to happen, brief inline. If not, full orientation.

Roster classification:
- **Full orientation:** `role_evaluation`, `cv_targeted`, `interview_prep`.
- **Brief inline:** `career_brief`, `industry_builder`, `skill_builder`, `specialty_builder`, `level_builder`, `knowledge_update`, `positioning`.
- **Ambiguous, deferred to skill-design time:** `interview_capture`, `interview_followup`, `cv_general`, `experience_inventory`, `career_narratives`.

### Mid-Flight Narration (in-progress, during Action Phase)

Before any tool call that takes more than a few seconds or represents a material step forward in the skill's arc (sub-agent dispatches, long script runs, LangGraph loop iterations), narrate:

- **What** operation is about to run.
- **Why** it matters to the phase's goal. Required. One clause, not a paragraph.
- **Duration** estimate if a typical range is known. Optional.

Skip narration for fast, mechanical operations (single file reads, existence checks, registry lookups). On return, output a brief acknowledgment line before proceeding: what came back, what the skill does next.

Pure template discipline. No script, no catalog. Content is contextual to each invocation (which sub-agent, what parameters, which phase), so pre-canning does not carry the specific detail that makes the narration useful.

### Presentation (retrospective, at phase boundaries)

Existing convention, unchanged. Phase boundaries close with the Presentation Phase per the skill authoring template.

### Folder Structure

`scripts/display/` holds the Orientation utility (`orient.py`) and message catalog (`orientations.yaml`). Sibling YAML catalogs for future pre-defined message categories (transitions, gates, input prompts, completions, failures) may add as siblings here if and when a concrete second category has a real use case. Split into a dedicated top-level folder (e.g., `messages/`) only after that second category is committed. The refactor is cheap; preemptive scaffolding solves no current problem.

---

## Tag Taxonomy

`rules/tags.yaml` holds only global tag vocabularies that apply to every entry regardless of industry or skill: Role Level, Org Context, Purpose. YAML chosen because tags are structured data read primarily by scripts for retrieval and validation, not by LLMs.

Skill-specific tag vocabularies do not live in `tags.yaml`. Capability values are skill-specific and live in their skill pack at `rules/skills/<skill>.md` Section 1. Industry packs at `rules/industries/<industry>.md` hold industry-specific reference content (vocabulary, dialect, regulations) but do not hold Capability lists; Capability is a skill-axis concern.

Specialty values live in `rules/specialties/` (their own axis files), not duplicated in `tags.yaml`. Industry and Skill registries are separate files at `rules/industries/registry.md` and `rules/skills/registry.md`, not tag vocabularies inside `tags.yaml`.

Validation cost for an inventory entry: a script loads `tags.yaml` (globals) plus each skill pack listed in the entry's `Skill:` field (Capability validation). Two-or-more file reads.

This revises the prior session's Tag Taxonomy decision, which listed "specialty_tags, domain_tags, activity_tags" as categories inside `tags.yaml`. Inspection of the existing inventory showed that activity_tags is really the Capability field (skill-specific, belongs in the skill pack), specialty_tags belongs in its axis directory, and domain_tags is really the industry/skill registries (separate files). `tags.yaml` narrows accordingly.

### Field Rename: Outcome → Purpose

The existing inventory's `Outcome:` field semantically classifies the kind of value the work delivered (Risk Reduction, Quality Improvement, Efficiency Gain, Capability Building), not the actual measurable outcome (which is narrated in the free-form `Impact:` field). Renamed to `Purpose:` to match function. Selected over "Value" because "value" is overloaded in code/data contexts and grep-ambiguous; "purpose" also gracefully accommodates achievements where the intent did not fully materialize. Cascade is bounded: search-replace in the inventory file plus the key name in `tags.yaml`. No downstream skills exist yet to migrate.

---

## Inventory Domain Scoping

Every retrievable entry in `Experience_Inventory.md` (EX-NNN, PR-NNN) carries explicit `Industry:` and `Skill:` fields. Both are multi-value (pipe-delimited, mirroring `Capability:`). The inventory does not declare an Active Domain at the document level; per-entry tagging replaces the prior single-document scope.

The `Industry:` field identifies the sector(s) the work happened in. May be omitted or empty for entries with no industry context (e.g., independent projects). Validates against `rules/industries/registry.md`.

The `Skill:` field identifies the technical/professional area(s) the work draws on. Required on every retrievable entry. Each value validates against `rules/skills/registry.md` and identifies the skill pack used for Capability validation.

Capability validation rule for multi-Skill entries: each Capability value must appear in at least one of the entry's listed skill packs (any-skill rule, not all-skill). Selected because multi-Skill entries span skill domains by virtue of having aspects of each, not by being fully cross-cutting in every Capability value.

Reference sections of the inventory (Education, Certifications, Affiliations, Training, Tech Experience, Therapeutic Areas, Employment & Role History) do not carry Industry/Skill tags. Background Roles (Not Tagged) appendix remains explicitly untagged.

Selected over a default-with-override pattern (single inventory header + per-entry override) because conditional logic ("if entry has Industry/Skill, use it; else fall back to header") creates uniform-treatment violations. Per-entry tagging is uniform: every entry self-describes, no implicit defaults.

Migration cost (logged for the implementation phase): every existing EX-NNN entry (~190+) and PR-NNN entry (5+) gets explicit `Industry:` and `Skill:` fields added; the inventory's existing `Active Domain` header is removed. Search-and-replace work, not design work.

---

## Inventory Entry Types

Two entry types in `Experience_Inventory.md`:
- `EX-NNN` for employment achievements (Section 8 of the inventory).
- `PR-NNN` for independent and volunteer projects (Section 10).

Both share the same field schema (headline, optional Context/Impact, Capability, Industry, Skill, Role Level, Org Context, Purpose, Added, Last Used). They differ only in:
- ID prefix (EX vs PR).
- Descriptor field name (`Role:` vs `Project:`).
- Physical section in the inventory (8 vs 10).

Selected over consolidation to a single `ENT-NNN` type with a `Type:` field. The employment-vs-independent distinction is semantic and unlikely to sprawl into a large type taxonomy. Zero migration cost. If new categories emerge later (volunteer, consulting, board, fellowship), add a new ID prefix ad hoc (e.g., VL-NNN, CN-NNN) without restructuring.

---

## Inventory Reference Sections

Reference-style sections in `Experience_Inventory.md` (Sections 1-7, 9) are not retrieval-target entries; they hold block content read by skills as needed. Restructuring decisions for these sections are recorded here as they are resolved.

### Section 6: Industry Exposure Profile (renamed from Therapeutic Area and Domain Exposure)

Renamed because "Domain" in the prior title conflated industry/skill (the term retired per the Four Orthogonal Axes split). New title reflects that this section catalogs the user's industry-specific exposure across multiple dimensions.

Internal structure converted from `**Bold Label:**` lines to `### Sub-section` headings, making each category an addressable retrieval slice. Final sub-sections:

- Therapeutic Areas
- Trial Phases
- Study Types
- Geographic Scope
- Data Domains (renamed from Data Modalities; reflects CDISC-style data domain categorization)
- Data Modalities (new sub-section: actual data shapes — tabular, time series, image)
- Standards (new sub-section: clinical data standards including CDISC, CDISC LAB Model, CDASH, SDTM)
- Regulatory Frameworks
- Functional Experience (renamed from Functional Domains; broad enough to accommodate technical functions like Data Engineering and Data Science alongside clinical-specific ones, and avoids reusing "domain")

"Data Domains" reuses the word "domain" in an industry-specific CDISC sense (data subject areas like DM, AE, LB), distinct from the retired axis term. Acceptable terminology overlap; no conceptual collision.

Migration: convert each `**Label:**` to `### Label`; rename Section 6 title; rename two sub-sections; add the new Data Modalities sub-section content (tabular, time series, image).

### Section 4: Professional Training

Internal structure converted from informal grouping (a labeled "Current Coursework (2025):" sub-list mixed with completed-training entries) to explicit sub-sections:

- Completed
- In Progress

Year (e.g., "2025") dropped from the "In Progress" sub-section header to prevent staleness on January 1. If year visibility per item is desired, add inline on the entry (e.g., "Generative AI Primer | Towards AI | 2025").

### Section 5: Technical Experience

Restructured into three sub-sections (each addressable as a retrieval slice):

- Programming, Data & Analytics (categories: Languages & Data Engineering, ML & Analytics, Cloud & Platforms, Visualization & Reporting, Development Tools, Project Management Tools)
- Office & Collaboration (SharePoint, MS Teams, OneNote, Visio, Adobe Acrobat Pro, Adobe LiveCycle Designer)
- Clinical Application Systems (9 bold-labeled categories carried forward from existing structure)

The prior "Methodologies" sub-section was dropped entirely. Each former item lives elsewhere: Lean Six Sigma in Section 4 (credentials); RBM, CSM in EX entry Capability tags; regulatory items (ICH/GCP, 21 CFR, HIPAA, EU Clinical Trials Directive) in Section 6 Regulatory Frameworks; CDISC standards in Section 6 Standards; Agile/Scrum evidenced through work practice.

Recategorizations applied: Minitab moved to ML & Analytics (statistical tool, not productivity); Microsoft Access moved to Languages & Data Engineering (database, not Office); JIRA and MS Project moved to a new Project Management Tools category under Programming, Data & Analytics (project management is its own discipline, not development tooling); Oracle Apex dropped (no remembered usage).

The umbrella "Programming, Data & Analytics" replaces the working name "Technical Tools." "Technical Tools" was too generic to identify the contents accurately. Office & Collaboration name retained over "Office & Communication" because most contents (SharePoint, Teams, OneNote, Visio) are about working together on shared content rather than messaging.

### Section 7: Employment & Role History

Restructured from grouped (roles clustered under company headers) to flat (each role record self-contained, with company as a field on the record). Each role gets a stable document-wide sequential ID (`RL-NNN`).

Example shape:

```
ID: RL-001
**Role:** External Data Acquisition Head
Company: BioMarin Pharmaceutical
Location: Wake Forest, NC
Type: Direct
Style: Remote
Concurrent: Yes
Start Date: Feb 2024
End Date: Jan 2026

ID: RL-002
**Role:** Associate Director, Data Quality Sciences
Company: BioMarin Pharmaceutical
Location: Wake Forest, NC
Type: Direct
Style: Remote
Concurrent: Yes
Start Date: Aug 2022
End Date: Jul 2025
```

Selected over the grouped status quo because flat records are simpler for validators (no inheritance logic needed to associate role with parent company) and easier to skim individually without scrolling up.

Role ID (`RL-NNN`) is supplementary metadata for compact reference. The EX entries' `Role:` field continues to use the readable "Title | Company" string per the Section 7 strict-match validation decision (Option D), not the `RL-NNN`. Both representations coexist; the validator builds a Title | Company set from Section 7 and matches EX entries against it.

### Section Ordering

Sections 9 and 10 swap. Independent & Volunteer Projects (PR-NNN entries) becomes Section 9, immediately after Section 8 (EX-NNN employment achievements). Academic Coursework Detail becomes Section 10. Rationale: Independent Projects and Employment Achievements share entry structure and read better adjacent; Coursework is reference detail and reads last.

Education (Section 1) stays at top. Position has no retrieval impact (scripts use heading anchors), so the choice is conventional readability. Education early matches reader expectation; moving it adjacent to Coursework was considered but not chosen.

### Tagging Granularity for Reference Sections

Reference sections (1-7, plus the new Section 10 Coursework after the reorder) are addressable at sub-section level via heading anchors. Per-item tagging is not added; sub-section addressability is sufficient for downstream skill needs identified to date. If a future skill develops a real need for finer slicing (e.g., interview_prep with proficiency-marked Therapeutic Areas), address per-skill at that point, not preemptively across all reference sections.

This confirms the prior project decision (no tagging of reference sections) with the refinement that sub-section headings, added during this rebuild, now provide the slicing mechanism.

---

## Configuration File

Location: `personal/config.yaml` in the nested private repo. Holds key paths, file output destinations, the parameterized user name (replaces the hardcoded value in format_spec), and placeholder for future tracker integration settings. YAML for structured data with comments. Read by Python scripts; may also be referenced inline by skills where paths or config values matter.

This also closes the format_spec transfer note about parameterizing the hardcoded name — name now comes from `personal/config.yaml`.

---

## Organizations

`rules/organizations/` contains three files serving different skills. Org maturity is a narrow modifier on CV composition (environmental / context language only), not a primary axis. Specialty, industry, skill, and level govern CV substance.

### Files
- `org_industry.md` (was `registry_company_type`): research scoping for interview_prep, listing research branches per industry type (CRO, Pharma, Biotech, SaaS, Consulting, etc.). Parallel naming to `org_maturity.md`.
- `org_maturity.md` (was `registry_org_type`): context framing modifier for cv_targeted. Two states today (Large Enterprise Established, Mid-Size Scale-Up), extensible.
- `company-slugs.yaml`: slug registry for application IDs (per Lineage and Traceability section above).

### Naming
Drop the `registry_` prefix. Folder already indicates reference tables; prefix is redundant.

### Content Transfer Note
Current `registry_org_type.md` header refers to a "catalog of CV format references" and instructs loading per-org Word templates. That's old-repo language. During transfer the header must be rewritten to describe the new role: context framing rules for cv_targeted, not template references.

---

## Research Sub-Agents

Six research sub-agents under `.claude/agents/` in the current build. Priority reflects workflow frequency, not whether something is in scope:

- `role_research` (primary-workflow path). Used by role_evaluation. Focused on the role itself (what the position involves, what it's worth) to support the apply / no-apply decision.
- `organization_research` (primary-workflow path). Used by interview_prep. Broader scope: the company and where the role fits within it. Builds on (does not duplicate) the research produced by role_research for the same slug-NNN.
- `industry_research` (extension-workflow path). Used by `industry_builder` when a new industry is added or an existing one refreshed. Lower build priority but still in scope.
- `skill_research` (extension-workflow path). Used by `skill_builder` when a new skill is added or an existing one refreshed. Lower build priority but still in scope.
- `specialty_research` (extension-workflow path). Used by `specialty_builder` when a new specialty is added or an existing one refreshed. Lower build priority but still in scope.
- `level_research` (extension-workflow path). Used by `level_builder` when a new level is added or an existing one refreshed. Lower build priority but still in scope.

All six are built in the current project. industry_research, skill_research, specialty_research, and level_research are not deferred because end-to-end testing requires all pieces to exist; incremental addition while waiting for real-world examples blocks integration testing and creates rework risk.

Research output location and format to be designed during per-skill work.

---

## Rule Refresh and Staleness

Axis rule files (specialty, industry, skill, level) drift as industry vocabulary and best practices shift. Refresh is user-triggered via the corresponding builder skill in `refresh` mode. No scheduled automation.

### Metadata

Every axis rule file carries a `last_researched: YYYY-MM` field in its YAML frontmatter. Builders stamp this field on every successful run, whether in `create` or `refresh` mode.

### Staleness Detection at Use Time

Consuming skills (`role_evaluation`, `cv_targeted`, `interview_prep`, and any other skill that loads an axis rule) read the stamp on load. If the stamp is older than the threshold, the skill presents an explicit binary choice before proceeding:

> "Rule X was last researched N months ago. Proceed with existing information, or perform a research refresh first?"

If the user picks refresh, the consuming skill invokes the relevant builder in `refresh` mode (which includes its own approval gate on the research output and the diff), re-loads the updated rule when the builder returns, and continues.

### Grouped Prompt

If multiple rules are stale at the start of a consuming skill (e.g., specialty and skill both past threshold), the skill presents one grouped prompt rather than a series, to prevent prompt fatigue.

### Threshold

9 months as a single repo-wide constant. Selected as a compromise between the 6-month evidence-based lower bound (resume best practices turn over noticeably within 2-3 years; AI-driven drift is accelerating cross-industry) and the 12-month upper bound (minimum resume-update guidance in current sources). Per-axis overrides deferred until evidence supports divergent drift rates (e.g., clinical industry likely slower than tech-adjacent specialties).

The threshold itself should be revisited periodically; drift rates themselves drift.

---

## Narratives Placement

`rules/narratives/` as drafted with five files (decision_adr, decision_personal, story_atola, story_star, story_personal) is kept. Consolidating to two files (decisions.md, stories.md) is equivalent under retrieval scripts and not worth the churn. "Source documents" terminology retires in favor of "knowledge documents" for consistency with `personal/knowledge/` and the `knowledge_update` skill.

---

## Lineage and Traceability

Scope is application lineage only. Knowledge-doc version history is handled by git and does not need project-level lineage infrastructure.

### Application ID Format
`<company-slug>-NNN`. All lowercase. Per-company counter — NNN increments per company, not globally. Compound form yields globally unique, meaningful identifiers. Examples: `pfizer-001`, `jnj-003`, `jpmc-002`.

### Company Slug Registry
User enters a short slug at first encounter with each company. Skill prompts for slug, stores it plus the full legal company name in `rules/organizations/company-slugs.yaml`. Subsequent applications for the same company reuse the registry lookup. No auto-derivation; user picks the slug.

#### Schema
YAML, keyed by slug. Three fields per entry:
- **Key** (slug): user-picked short identifier at first encounter. Lowercase kebab. Used as the slug in application IDs.
- **name**: full legal company name. Used for matching on repeat encounter and for display.
- **counter**: per-company application count. Incremented on each ID issue.

Example:
```yaml
pfizer:
  name: Pfizer Inc.
  counter: 3
jnj:
  name: Johnson & Johnson
  counter: 1
beone:
  name: BeOne Medicines
  counter: 2
```

Fields considered and cut (minimum viable; add if a consumer emerges):
- `aliases`: variation handling done at match time via disambiguation prompt.
- `former_names`: rebrand cases (e.g., BeiGene → BeOne) handled by manual entry update.
- `first_seen`: nice-to-have metadata, no consumer.
- `applications` list: derivable from counter plus lookup.
- Access stamp (`Last Used` / `Last Accessed`): no consumer acts on the timestamp; recency is derivable from counter and application folder dates. Access stamps are selective in the system; they appear only where a specific consumer uses the timestamp (Experience_Inventory and Career_Narratives stamp `Last Used` to drive active-vs-dormant selection; axis rule files stamp `last_researched` to drive builder-refresh staleness detection).

Format chosen over `.md` because this is structured data primarily read by scripts, matching the rationale for `tags.yaml`.

### Session Log
Created at start of role_evaluation regardless of whether the user ultimately applies. Location: `personal/sessions/<slug>-NNN_session-log.md`. Records phase completions with timestamps plus key decisions (specialty confirmed, industry/skill locked, fit verdict). Read on resume to determine state.

### Session Log Format
YAML frontmatter for metadata. Structured entries in body for phase completions and decisions. No free-form narrative. Enables future tracker integration via script parsing.

#### Frontmatter Schema

Five fields:

```yaml
---
application_id: pfizer-001
company: Pfizer Inc.
role: Director, Clinical Data Operations
created: 2026-04-24
state: evaluating
---
```

- **application_id**: compound slug-NNN. Required. Mirrors the filename prefix.
- **company**: snapshot of the company name at session creation. Denormalized from the registry for self-containment (session log readable without loading the registry) and historical accuracy (preserves the name at time of application if the company later rebrands; e.g., "BeiGene" retained even after BeOne rebrand).
- **role**: role title as entered by the user. Free-text; not in any registry.
- **created**: YYYY-MM-DD date of session creation.
- **state**: workflow state. Enum: `evaluating | applied | interviewing | do-not-pursue`. Self-contained in frontmatter so consumers don't need path-checking. Session log file stays at `personal/sessions/` regardless of state; closure is signaled by state value, not file location.

Fields considered and cut:
- `role_slug`: derivable from `role` when the application folder is created.
- `last_updated`: programmatic recency is accessible via the timestamp of the last body entry; no current consumer needs a denormalized frontmatter field. File mtime handles casual browsing. Add if a scenario emerges that git operations would break mtime-based checks.
- `outcome` / `fit_verdict`: captured in body as structured decision entries (decision 3).
- Access stamps (`Last Used` / `Last Accessed`): per the access-stamp filter (consumer-driven), no consumer acts on session-log access timestamps.

### Per-Application Folder
`personal/applications/<slug>-NNN-<role-slug>-<yyyy-mm>/`. Created only if the user decides to apply. Self-describing: folder name shows company, app counter, role, and date without opening the contents. User enters a short role slug at application start (lowercase kebab). Holds downstream artifacts (CV, interview-prep, interview-completion, interview-scratch, interview-followup). Files inside the folder do not restate the role-slug; they use `<slug>-NNN` alone since role is clear from folder path.

### Do-Not-Pursue Folder
`personal/do-not-pursue/` holds artifacts from role_evaluations that did not advance to application.

### File Naming Convention
Follows the File and Folder Naming Convention in the Naming section. Compound application ID embedded. Examples: `gap-analysis_pfizer-001.md`, `cv_pfizer-001.docx`, `interview-prep_pfizer-001.md`.

### Last Used Stamping
Preserved for both `Experience_Inventory` and `Career_Narratives` entries. Skills that produce accepted outputs stamp cited entries with `Last Used: YYYY-MM`. Enables distinguishing active from dormant content.

### State Detection
Ordered checks combine file existence and session log entries to determine resume point. Exact logic and location (standalone rule file vs per-skill) designed during per-skill work.

### Tracker Integration (Deferred)
External Google Drive tracker integration is not in scope for the current build. Decisions above keep it simple later: compound ID is stable and string-safe (no coercion in Sheets); YAML session logs enable script-based status extraction.

---

## Component Documentation Discipline

Every skill, sub-agent, and standalone script has an entry in `COMPONENTS.md` (at repo root) capturing inputs, outputs, triggers, and update triggers. The entry is authored alongside the component itself; it is never deferred. Component evolution requires entry update in the same change.

`COMPONENTS.md` is the single point of lookup for any maintenance question: what feeds into this component, what does it produce, what other components depend on it, what external changes should prompt revisiting it. Without it, dependencies and operational consequences scatter into tribal memory and rot when sessions end.

The repo's `CLAUDE.md` (when authored) references `COMPONENTS.md` so future Claude sessions consult it before proposing any modification to a component or its dependencies. The discipline is enforced both at design time (each new component gets its entry) and at modification time (dependent components flagged via update-trigger lookup).

This subsumes the simpler "operations map" idea originally proposed. Standalone scripts, skills, and sub-agents all live in one registry under one schema.

---

## Document Metadata Header Discipline

Every document programmatically consumed by skills, sub-agents, or scripts carries a structured metadata header below its title. The header surfaces consumer/producer relationships in parseable form, supporting both human findability (top of document, scannable) and reconciliation against COMPONENTS.md.

### Scope

In: knowledge documents (`personal/knowledge/*.md`), rule files (`rules/**/*.md`, `rules/**/*.yaml`), templates (`templates/*.md`).

Out: skills and sub-agents (both already carry framework YAML frontmatter and have COMPONENTS.md entries; adding markdown headers would create triplicate maintenance), meta docs (README, COMPONENTS.md, design_decisions.md, design_open_questions.md), outputs, scripts (Python convention is docstrings).

### Format

Plain markdown lines below the document title, before prose body. Pattern: `**Field:** value`. Multiple fields stack as separate lines. Selected over YAML frontmatter because frontmatter renders invisibly in VS Code's markdown preview, contradicting the "communicate to users" goal of the header.

### Field Set

Three fields in v1, applied minimally (only present where applicable; authors do not pad with N/A):

1. **Used by:** named components that load or copy this doc. Required when the doc is consumed.
2. **Stamps:** what consumers modify on this doc (e.g., `Last Used (YYYY-MM)`). Optional; only where stamping happens. Describe the modification pattern in minimal form; do not list specific stamped IDs (those live on the entries themselves).
3. **Generated by:** script that produces this doc. Optional; only for script-generated docs.

Multi-value (e.g., multiple consumers in `Used by`): comma-separated on one line. Bullet list acceptable if more than ~5 entries.

Other potential fields (Sources, Schema version, Status, Last regenerated) deferred until concrete need emerges.

### Authoring Schema Documentation

The available field set is documented in COMPONENTS.md ("Document Metadata Header Schema" section) so authors know what fields exist without depending on N/A prompts in every doc. Reconciliation script (deferred to implementation, logged in Pending Follow-on Work) detects unexpected absences by cross-checking against COMPONENTS.md and skill code load patterns.

### Inline Prose Reference Principle

Inline prose references to specific component names (e.g., "loaded by cv_targeted") remain discouraged per the descriptive-over-named-references principle. Named references belong in the structured metadata header, where the reconciliation script can verify them. Prose in the document body should describe the consumption pattern descriptively (e.g., "any skill that renders contact info"), not name specific components.

---

## Data-Only Discipline for Knowledge Documents

Knowledge documents and rule files hold data and metadata only. They do not carry procedural instructions about how consumers should use the data (e.g., "all fields except X are required," "include Y only if Z," "remember to update W when V changes," "before loading this file, do Q"). Procedural logic lives in skills, format specs, and scripts.

### Why

A "Usage Notes" section in a data document creates a duplicate source of truth: the doc says one thing, the consuming skill says another. Drift between them goes undetected (no reconciliation script catches "your skill says X but your doc says Y"). Authors maintaining the data must remember to update the instructions; authors maintaining the skill must remember to update the doc. The discipline removes this dual-maintenance burden.

### What Belongs in a Data Document

- The data itself.
- The metadata header per the Document Metadata Header Discipline (`Used by`, `Stamps`, `Generated by`).
- A brief one-line purpose statement at the top, descriptive of what the file is (not procedural about how it is used).

### What Does Not Belong

- "Usage Notes" sections.
- Field-level conditional logic (e.g., "include only if present").
- Layout / composition rules (e.g., "GitHub appears alongside LinkedIn").
- Self-referential meta-instructions about future updates (e.g., "if you add X, update skill Y").

### Migration

Existing knowledge documents and rule files inherited from the prior project carry varying amounts of procedural-instruction sprawl. Each is reviewed during its design pass; instruction-flavored content moves to its consuming skill or format spec, and the data document keeps only data + metadata + brief purpose.

---

## Knowledge Document Scaffolding

A `support/` folder at repo root holds scaffolding files that the user copies into their private personal repo on first clone. The career repo itself never holds the user's actual personal data; the scaffolding provides templates and setup support so a fresh user can stand up their own private knowledge repo.

### Scope

Scaffolded (template files):
- `User_Info.md` (placeholder template for direct authoring)
- `README.md` and `SETUP.md` for the personal repo
- `.gitignore` for the personal repo

Not scaffolded (built by skills at first use):
- `Experience_Inventory.md` (built by `experience_inventory` skill)
- `Career_Narratives.md` (built by `career_narratives` skill)
- `Positioning.md` (built by `positioning` skill)

### Specifics Deferred

Folder name, sub-folder layout (e.g., `support/knowledge_repo_scaffolding/` vs flat `support/`), and individual file naming are deferred to migration phase. Working name carries over from the prior project; can simplify when migration applies.

### Content Updates Required at Migration

Prior scaffolding files reference retired architecture (Phase 5a, old skill names like `experience_inventory_bootstrap`). Migration applies:
- Strip phase-based references; describe loading patterns descriptively per the inline-prose principle.
- Update skill names to current roster (per COMPONENTS.md).
- Add metadata header (`**Used by:**` etc.) to the `User_Info.md` template per the Document Metadata Header Discipline.

---

## User_Info (renamed from Contact_Info)

Single source of truth for the user's identity and profile data, used by skills that render contact and profile information into outputs (CV, etc.). Renamed from `Contact_Info.md` because the file holds more than strict contact data (Name is identity; GitHub/Website are profile URLs); `User_Info.md` accommodates current and likely future contents.

### Decisions Captured

- **Rename**: `Contact_Info.md` → `User_Info.md`. Migration: rename file in scaffolding template and (when populated) in the user's `personal/knowledge/`. Update any references in skills, scripts, and rule files (none currently exist; the rename happens cleanly in migration).
- **Name field source of truth**: lives in `User_Info.md` only. The parameterized `name` in `personal/config.yaml` is removed; the format_spec rendering script reads the name from `User_Info.md` when composing CV output filenames. (Updates the prior Configuration File design decision, which had `name` in `config.yaml`.)
- **Drop "Usage Notes" section**: per the Data-Only Discipline, the file's existing Usage Notes (required vs optional fields, conditional inclusion logic, GitHub-alongside-LinkedIn layout, future-update meta-instructions) move to the consuming CV-rendering skill and/or format_spec. The data document keeps only data + metadata + brief purpose.
- **Metadata header**: `User_Info.md` carries `**Used by:** ...` per the Document Metadata Header Discipline. No `Stamps` or `Generated by` (none apply).
- **Placeholder values**: the user's actual values live in their private `personal/knowledge/User_Info.md`. The scaffolding template in `support/knowledge_repo_scaffolding/User_Info.md` carries placeholder values like `[Your Name]` for fresh users.

---

## Career_Narratives

Per-narrative IDs and schema realignment with inventory captured as decisions are settled during the per-doc design pass.

### Decisions Captured

- **Per-narrative IDs added.** Two prefixes mirror the inventory's EX/PR distinction:
  - `ST-NNN` for stories (10 currently: ST-001 through ST-010).
  - `DC-NNN` for decisions (6 currently: DC-001 through DC-006).

  Sequential within type, document-wide. Placed as the first line of the metadata block, before Tags/Archetype/Era. Stable under heading rename, supporting lineage citations from consuming skills (e.g., `interview_prep` referencing "told ST-001").

- **Field renames in metadata block (downstream of axis-rename decisions):**
  - `Tags` → `Capability` (same semantic; aligns with inventory's field naming).
  - `Archetype` → `Specialty` (per the axis rename: archetype became specialty).

- **Inventory-aligned field additions to metadata block:**
  - `Industry` (multi-value): sector(s) the narrative happened in.
  - `Skill` (multi-value): technical/professional area(s) the narrative draws on.
  - `Role Level` (single): user's career stage at the time of the narrative.
  - `Org Context` (single): organizational context (Mature/Enterprise, Scaling, Greenfield, Independent).
  - `Purpose` (single, optional): value type the narrative demonstrates. Optional because not all decisions map cleanly to a single value bucket.

  Era field retained as the company-specific shorthand (BioMarin, Duke CRI, Independent, etc.). Industry is the sector level; Era is the company level. Both useful, not redundant.

  Final narrative metadata block contains: ID, Capability, Industry, Skill, Specialty, Role Level, Org Context, Purpose (optional), Era, Added, Last Used.

  Migration cost: roughly 50-80 new field values across 16 narratives. One-time work.

- **Document Metadata Header Discipline applied:**
  - `**Used by:** cv_targeted, cv_general, interview_prep, role_evaluation, positioning, career_brief`
  - `**Stamps:** Last Used (YYYY-MM)` (minimal form, per the discipline)
  - `Generated by:` N/A. The doc is interactively built by the `career_narratives` builder skill, not script-generated. Builder/maintainer relationships live in COMPONENTS.md, not the doc header (extending the schema with a `Maintained by:` field deferred until concrete need).

- **Data-Only Discipline applied: Tag Taxonomy section removed.** The existing top-of-file Tag Taxonomy block contained instructional schema description, tag governance pointers (with old-architecture file paths), and an Era taxonomy list. All three move out:
  - Schema description → COMPONENTS.md career_narratives entry (when authored).
  - Tag governance → validator logic in skills (validator already knows where Capability/Specialty/Industry/Skill values live per the new design).
  - Era taxonomy → derived at validation time from inventory Section 7's company list plus "Independent" for project-context narratives. No hand-maintained Era list inside Career_Narratives.

  After cleanup, `Career_Narratives.md` begins with the metadata header (`Used by`, `Stamps`) and proceeds directly to `# STORIES: STAR / ATOLA`.

- **Framework field added to metadata block.** Each narrative declares which framework it follows; the framework files in `rules/narratives/` define the expected subsection schema (validator-checkable).
  - Stories: `Framework: story_personal` for all 10 current stories. The user designed `story_personal` as a richer master format that downstream consumers can subset into STAR or ATOLA presentations as needed; `story_star.md` and `story_atola.md` in `rules/narratives/` define those output projections.
  - Decisions: `Framework: decision_adr` for all 6 current decisions. Current decision shape has drifted from canonical ADR with personal/reflective subsections ("Who Pushed Back", "What I'd Own Differently") added during prior Claude updates (see memory `feedback_frameworks_are_constraints.md`). Migration cleanup: fold "Who Pushed Back" content into the Context subsection of each decision; drop "What I'd Own Differently" subsections.
  - Field placement: after Era, before Added.

- **APPENDIX section removed.** The Decision/Stories Framework Key at the bottom of Career_Narratives.md duplicates what `rules/narratives/` framework files (`story_personal.md`, `story_star.md`, `story_atola.md`, `decision_adr.md`, `decision_personal.md`) hold (or will hold). Per Data-Only Discipline, framework definitions live in `rules/narratives/`, not in the data document. Migration step: when the framework files are authored, the APPENDIX content serves as starting material; after authoring, the APPENDIX in Career_Narratives is deleted entirely.

- **Authoring artifact cleanup.** Two mechanical transformations applied during migration:
  - Strip Pandoc underline syntax from subsection headings: `### [Section Name]{.underline}:` becomes `### Section Name`.
  - Remove HTML comment blocks: every ` ```{=html}\n<!-- -->\n``` ` block is a .docx-conversion artifact and gets deleted; surrounding bullets rejoin into continuous lists.

  Implementation: a one-time script (e.g., `scripts/migration/cleanup_pandoc_artifacts.py`) or careful find-and-replace in an editor. No content decisions involved.

- **Variance accepted; empty subsections retained with `Not applicable` placeholder.** Subsections are optional per narrative (some narratives have less depth than others; older narratives may lack content for Thinking/Tradeoff/Constraints, etc.). Validator allows omission; framework files in `rules/narratives/` define the LIST of allowed subsections, not a required-every-time list.

  For existing narratives with empty subsections (e.g., Duke CRI's Thinking, Tradeoff, Constraints): retain the heading and populate with `Not applicable` rather than deleting. Career_Narratives is read heavily by the user during interview prep, where structural consistency across narratives aids readability; present-but-explicitly-marked subsections preserve the framework's shape.

- **Cross-reference field added: `Linked Inventory:`.** Narratives that correspond to specific inventory entries declare those entries via this multi-value, optional field. Direction is asymmetric: narrative → inventory only (narratives are 16 entries; inventory is 190+; one-way reduces authoring and maintenance cost). Reconciliation script derives the inverse mapping (which narratives reference which EX/PR entries) when needed.

  Field placement: after Framework, before Added.

  Use cases unlocked: cv_targeted can fetch related narrative context when selecting an inventory entry; interview_prep surfaces narrative + linked inventory entries for topic prep; lineage tracing across the two documents.

---

## Questions_Library (eliminated)

Originally scoped as a role/company-agnostic library of reusable interview question patterns accumulated over time. Inspection of the existing file showed it had drifted to a per-application question record (questions tightly bound to a specific application's context) rather than a context-free pattern library.

Two paths considered: (A) restructure into a context-free templates library plus per-application questions moved to application folders, with `interview_prep` extracting new patterns at session end; (B) eliminate the library entirely and let per-application questions live only in the application folder.

**Path B chosen.** Rationale: the templates-library value depends on disciplined post-application genericization work that the user is not committed to doing. Without that work, the library accumulates context-bound noise (the current state). Per-application question records still exist in `personal/applications/<slug>-NNN_*/` and can be mined for patterns ad hoc if a future need surfaces.

### Cascade

- Knowledge documents roster shrinks from 5 to 4: User_Info, Experience_Inventory, Career_Narratives, Positioning.
- Removed from the Stack section's RAG reference list.
- Removed from the Knowledge Document Scaffolding "not scaffolded" list.
- `interview_prep` no longer references `Questions_Library.md`; per-application question lists live at `personal/applications/<slug>-NNN_<role>_<date>/questions.md` (or similar; exact filename to be settled during interview workflow design).
- Migration: delete `personal/knowledge/Questions_Library.md` after extracting any content the user wants to keep manually.

---

## Positioning

Per-doc design decisions captured here as they are settled.

### Decisions Captured

- **Two sections cut for primary-purpose alignment.** The user's stated primary purpose for `Positioning.md` is recall under pressure when communicating about experience, abilities, positions, and value (with CV creation and role evaluation as secondary uses). Section-by-section utility evaluation against that primary purpose identified two sections that fail for recall and duplicate Experience_Inventory at worse abstraction:
  - **Competencies** (~30 bullets across 4 sub-areas: Process & Operations, Analytics & Data, Technology & Platforms, Leadership & Transformation): essentially a skills list. Not internalizable; functions as reference, not recall.
  - **Role-Targeted Accomplishments** (~30 bullets across 5 role variants: Transformation Leader, Clinical Operations Leader, Executive Data & Analytics Leader, Individual Contributor — Data & Analytics, M&A and Clinical Trial Activity Transfers): reads like inventory entries grouped by role type. Tells what was done, not how to talk about it. Duplicates Experience_Inventory at coarser abstraction.

  Both sections removed. CV creation and role evaluation workflows are unaffected: those skills pull from Experience_Inventory directly, where atomic achievements are properly tagged (Capability, Industry, Skill, Role Level, Org Context, Purpose) for categorical filtering. Positioning sharpens to its primary purpose.

  Sections retained (recall-effective): Positioning Statement + Focus Bullets, Core Philosophy (Orient/Diagnose/Intervene/Stabilize/Scale), What Makes This Different, Industry Trajectory, Signature Themes (4), Elevator Statement, LinkedIn About Me variants, Recruiter Pitch Template, Why I Chose to Leave BioMarin, Appendix (Story-to-Theme matching only after procedural-instructions cleanup).

- **Section reorder: Signature Themes moved up.** Currently sits near the bottom (line 293); moves to immediately follow Core Philosophy. Themes are the practical-recall pairing to Philosophy's framework framing; placing them adjacent makes both surfaces accessible together when the doc is consumed in pieces.

- **Positioning Statement focus bullets retained** despite overlap with Core Philosophy stages. Different abstraction levels of the same ideas (bullets are punchy one-liners; Philosophy is longer-form treatment). Self-containment serves the recall use case (doc is consumed in pieces); the small redundancy (4 lines) is not duplicate content.

- **Replacement summary sentences for cut sections, folded into renamed section.** Two recall-friendly distillations:
  - Role-type breadth: "I work effectively as a transformation leader, clinical operations leader, executive data and analytics leader, individual contributor in data and analytics, and have led M&A and clinical trial activity transfers."
  - Competency-area breadth: "I bring depth in process and operations, analytics and data, technology and platforms, and leadership and transformation."

  Placement: folded into the renamed section (see next bullet). The two sentences reinforce the differentiation argument the section already opens with (cross-functional fluency claim); placing them there keeps Core Positioning lean as the headline.

- **Section rename: "What Makes This Different" → "What Makes Me Unique."** The section's content is about distinctive qualities (cross-functional fluency, breadth across role types, breadth across competency areas, foundational arc, translation discipline), not fit-for-a-specific-role; "Unique" reads more accurately than "Fit."

- **Document Metadata Header Discipline applied:** `**Used by:** cv_targeted, cv_general, role_evaluation, interview_prep, career_brief`. The `positioning` skill (builder of this doc) is excluded from Used by per the convention used for `career_narratives`; builder relationships live in COMPONENTS.md. Used by stays scoped to named components so the reconciliation script can verify entries; human use cases (the user reading the doc for professional conversations) are not in the metadata header (would dilute the reconciliation contract). No Stamps; no Generated by.

- **Stable IDs for cross-references: `TH-NNN` for Themes; appendix matching tables updated to use ST-NNN and TH-NNN.** Each Theme gains an `ID: TH-NNN` line below its heading (TH-001 through TH-004 for the 4 themes). The Story-to-Theme and Theme-to-Story matching tables in the APPENDIX migrate from positional numbering ("Story 1, Theme 2") to stable IDs ("ST-001, TH-002").

  Migration surfaces existing inaccuracies in the appendix:
  - "Story 7 — Direct Report Accountability" is misclassified; Direct Report Accountability is a decision in Career_Narratives (DC-003), not a story. Correct during migration.
  - Current appendix lists Stories 1-9 but Career_Narratives has 10 stories (LLX CRO Onboarding and Capability Building is Story 10 / ST-010). User decides whether to add ST-010 to the matching tables during migration.

- **APPENDIX Customization Instructions removed.** The "Recruiter Pitch Template Customization Instructions" sub-section (Steps 1-4 plus a worked example) is procedural skill logic, not data. Per Data-Only Discipline, it moves to the `career_brief` skill design (the skill that composes recruiter pitches). Captured as design intent for the per-skill design pass.

- **Recruiter Pitch Template moved out of Positioning to `templates/recruiter_pitch_template.md`.** The template (Fixed Opening + Variable Middle skeleton + Fixed Close) is a carrier file that gets filled in, not positioning data per se. Per the Templates section in design_decisions.md, templates live under `templates/`. Positioning is a communication document (recall material), not a template repository; pulling the template out lets Positioning drift toward its purer form. The new template file gets the standard metadata header (`**Used by:** career_brief`).

- **`Linked Stories:` field on themes.** Each theme gains `**Linked Stories:**` listing supporting ST-NNN entries. Field placement: after `ID:`, before `Use when:`. Reader looking at a theme immediately sees which stories prove it; primary recall flow (theme → story) is satisfied without consulting the appendix.

- **APPENDIX section removed entirely.** With `Linked Stories:` on theme entries, the Theme-to-Story matching table is redundant; with the Customization Instructions moved to `career_brief` and the Recruiter Pitch Template moved to `templates/`, no APPENDIX content remains. The Story-to-Theme matching table is also removed; the inverse-direction lookup (story → theme) is uncommon enough that it does not justify retaining the table. If the inverse lookup becomes a real need later, two paths: add `Linked Themes:` to narratives in Career_Narratives (mirror pattern), or run a derivation script.

  Historical note: the Story-to-Theme matching was useful when stories lived in this document; now that stories live in `Career_Narratives.md`, the in-doc convenience no longer applies.

- **"Avoid:" instructional line removed from Positioning.** The WHY I CHOSE TO LEAVE BIOMARIN section ended with `**Avoid:** burnout narratives, complaints about culture or individuals, over-technical jargon.` Per Data-Only Discipline, this is skill-territory guidance (how to deliver talking points, not data). Captured as design intent for `interview_prep` (the most likely consumer for transition-question prep). After removal, the WHY I LEFT section holds only the narrative content; the avoid-guidance lives with the skill.

- **"Last Revised" line kept as plain text at top.** Status quo. The line `Last Revised: YYYY-MM` at the very top of Positioning provides at-a-glance freshness visibility without requiring a `git log` query. Considered folding into the metadata header as a structured `**Last Revised:**` field; rejected as schema bloat for one minor field. Considered removing entirely (since git is authoritative for revision history per Lineage and Traceability); rejected because the user wrote it intentionally for visibility.

- **Typo fix at migration: "INDUSTRY TRAGECTORY" → "INDUSTRY TRAJECTORY"** (line 85 of Positioning today). Mechanical correction; no design decision involved.

---

## Open Items

All structural design items are closed. Remaining items to be addressed during per-skill design (not structural):

- Knowledge-builder skills internal design (career_narratives, experience_inventory, positioning). Scope captured structurally; interactive prompting and tag classification behaviors are per-skill design work.
- State detection logic: exact form and location (standalone rule file, per-skill, or hybrid).
- Session log YAML schema specification.
- Application ID assignment script implementation.
- Research output file location and format (referenced in Research Sub-Agents section).
- `level_builder` design, including whether and when to split `leadership.md` into finer-grained level files (people manager, senior leadership, c-suite, etc.) once the first new level is authored.
- Builder refresh-mode mechanics: exact diff presentation, approval gate shape, and file-write flow for create vs refresh across all four axis builders.
- `scripts/display/orient.py` implementation and `scripts/display/orientations.yaml` content (authored when the first long-arc skill is built).
- Threshold revisit: the 9-month staleness threshold should be re-evaluated periodically as drift patterns themselves shift.
