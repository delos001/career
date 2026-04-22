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

### Three Orthogonal Axes
Role evaluation and deliverable production compose three axes:
- **Specialty** (renamed from archetype). Governs deliverable structure (e.g., CV section order, Core Competencies, summary framing).
- **Domain** (industry). Governs vocabulary and dialect.
- **Level** (IC vs leadership today). Governs framing and voice.

Axes are independent files. Overrides exist only where axes genuinely interact. Override discipline: narrow interaction rules, not mini-archetypes. If an override drifts toward restating an axis, split the axis or accept a new specialty.

### Dual-Specialty (Asymmetric Authority)
A role may map to two specialties. Primary governs most surfaces. Secondary gets bounded, explicitly-scoped slots within the deliverable. Primary and secondary do not compete over the same surface. Each deliverable decides what surfaces (if any) it exposes to a secondary.

- CV: secondary appears in 2-3 achievements and 1-2 Core Competencies items. Summary is primary-only.
- Other deliverables: per-deliverable composition rule written as needed.

Existing CV dual-specialty rule transfers in; place at `rules/specialties/cv_dual_specialty_composition.md` (or equivalent location that reflects its CV-specific scope).

### Level Axis: Two Buckets Today, Gradient-Capable Later
Today: IC and leadership only. Later expansion (e.g., staff/principal IC, mid-level management, executive) requires adding files plus a registry entry. No skill changes required. Level files are deliverable-agnostic (voice/framing). Deliverable-specific concerns (e.g., CV section order) belong in the deliverable's format spec.

### Skill Stability via Loose Coupling
Skills reference rules by category/slug. A resolver script looks up the current file. Skill body does not hard-code paths, so rule/template/axis churn does not touch skills. Skill interface changes only when skill behavior changes; that is not what caused churn in the prior repo.

---

## Naming

### Terminology and Folder Renames Committed
- `archetypes` → `specialties` (rules folder: `rules/specialties/`)
- `role_level` → `levels` (rules folder: `rules/levels/`)
- Under Pattern A, skills are flat under `.claude/skills/` (no `rule_builders/` parent folder). The old `rule_builders/archetype/` concept becomes a standalone skill such as `.claude/skills/specialty_builder/SKILL.md`.

### Specialty File Names
Drop the numeric prefix (previously `a1_`, `a2_`, etc. from the archetype era). Files use descriptive slugs only: `transformation_strategy.md`, `data_analytics.md`, `process_operations.md`, `platform_technology.md`. Retrieval scripts look up by descriptive name, so the prefix adds no functional value.

### Level File Names
Drop deliverable prefix. `ic.md` and `leadership.md` (not `content_ic_cv.md`). Folder path provides context.

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

Under Pattern A, skills like `.claude/skills/specialty_builder/SKILL.md` and `.claude/skills/domain_builder/SKILL.md` do not reference nested "building rules" files. The construction procedure is the skill itself and lives inside its SKILL.md. No `rules/builders/` folder is created. If construction grows complex enough to warrant extraction later, it can be addressed at that point.

## Workflow Sequence Diagram

Deleted, not relocated. The old registry contained an ASCII workflow diagram; it does not carry over to the new repo. A richer visual (e.g., Visio) may be authored later if useful.

## Interview Template Artifacts

`interview_completion` and `interview_scratch` exist as both blank skeletons (in `templates/`, copied per round) and populated instances (in `personal/applications/<slug>-NNN_<yyyy-mm>/`). Different purposes, two locations, no duplication.

## Stack

**Orchestration:** Claude Code native for most of the workflow (skills as markdown, Task tool for sub-agents with isolated context, hooks, Bash for Python invocation). LangGraph approved for the CV generation loop specifically (perform → QC → fix → QC, potentially parallel format / structural / content QC sub-agents) as a bounded learning experiment. Two hard constraints: (1) no dual state management between Claude Code and LangGraph — one state model, one well-defined integration handoff; (2) if friction materializes beyond the initial learning curve, the experiment stops at the CV loop and does not extend to role_evaluation, interview_prep, or other workflows. Skills outside the CV loop stay Claude Code native.

**Retrieval:** Mixed by content shape. Structured lookup (Python script fetches a known slice by slug/key) for structured documents (Experience_Inventory, Positioning, registries, format specs). RAG reserved for genuinely unstructured content (e.g., interview_scratch notes, questions_library free-form entries). Default is structured; add RAG only where structure truly doesn't exist.

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

- Application ID assignment script: prompts for company slug at first encounter, stores it plus the full company name in `rules/organizations/company_slugs.md`, increments the per-company counter, returns the compound ID.
- Session log YAML schema: specify metadata fields and body entry format.

---

## Skill Authoring Template Library

Location: `engops/cheatsheets/skill-templates/`. First template: `human-gated-workflow.md` capturing phase types (Action / QC / Presentation / Transition) and closing conventions for this project's pattern. Folder structure from the start so future templates (autonomous-agent, bounded-task, etc.) add as siblings without restructuring. The user's project here is a human-gated AI workflow; other projects may use different patterns, hence the library approach rather than one universal template.

---

## Pacing Consolidation

Resolved. User-level `CLAUDE.md` holds general response-shape pacing rules (applies across all projects). Skill approval-gating behavior lives in the skill authoring template as a Presentation Phase convention, not as a global rule. No duplicate to remove.

---

## Tag Taxonomy

Location: `rules/tags.yaml`. YAML chosen because tags are structured data read primarily by scripts for retrieval and validation, not by LLMs. YAML supports comments and human-editable grouping. Categories inside (specialty_tags, domain_tags, activity_tags, etc.). Split into a folder only if categories grow beyond one file.

---

## Configuration File

Location: `personal/config.yaml` in the nested private repo. Holds key paths, file output destinations, the parameterized user name (replaces the hardcoded value in format_spec), and placeholder for future tracker integration settings. YAML for structured data with comments. Read by Python scripts; may also be referenced inline by skills where paths or config values matter.

This also closes the format_spec transfer note about parameterizing the hardcoded name — name now comes from `personal/config.yaml`.

---

## Organizations

`rules/organizations/` contains three files serving different skills. Org maturity is a narrow modifier on CV composition (environmental / context language only), not a fourth axis. Specialty, domain, and level still govern CV substance.

### Files
- `org_industry.md` (was `registry_company_type`): research scoping for interview_prep, listing research branches per industry type (CRO, Pharma, Biotech, SaaS, Consulting, etc.). Parallel naming to `org_maturity.md`.
- `org_maturity.md` (was `registry_org_type`): context framing modifier for cv_targeted. Two states today (Large Enterprise Established, Mid-Size Scale-Up), extensible.
- `company_slugs.md`: slug registry for application IDs (per Lineage and Traceability section above).

### Naming
Drop the `registry_` prefix. Folder already indicates reference tables; prefix is redundant.

### Content Transfer Note
Current `registry_org_type.md` header refers to a "catalog of CV format references" and instructs loading per-org Word templates. That's old-repo language. During transfer the header must be rewritten to describe the new role: context framing rules for cv_targeted, not template references.

---

## Research Sub-Agents

Four research sub-agents under `.claude/agents/` in the current build. Priority reflects workflow frequency, not whether something is in scope:

- `role_research` (primary-workflow path). Used by role_evaluation. Focused on the role itself (what the position involves, what it's worth) to support the apply / no-apply decision.
- `organization_research` (primary-workflow path). Used by interview_prep. Broader scope: the company and where the role fits within it. Builds on (does not duplicate) the research produced by role_research for the same slug-NNN.
- `domain_research` (extension-workflow path). Used by domain_creation when a new career domain is being added. Lower build priority but still in scope.
- `specialty_research` (extension-workflow path). Used by specialty_creation when a new specialty is being added. Lower build priority but still in scope.

All four are built in the current project. domain_research and specialty_research are not deferred because end-to-end testing requires all pieces to exist; incremental addition while waiting for real-world examples blocks integration testing and creates rework risk.

Research output location and format to be designed during per-skill work.

---

## Narratives Placement

`rules/narratives/` as drafted with five files (decision_adr, decision_personal, story_atola, story_star, story_personal) is kept. Consolidating to two files (decisions.md, stories.md) is equivalent under retrieval scripts and not worth the churn. "Source documents" terminology retires in favor of "knowledge documents" for consistency with `personal/knowledge/` and the `knowledge_update` skill.

---

## Lineage and Traceability

Scope is application lineage only. Knowledge-doc version history is handled by git and does not need project-level lineage infrastructure.

### Application ID Format
`<company-slug>-NNN`. All lowercase. Per-company counter — NNN increments per company, not globally. Compound form yields globally unique, meaningful identifiers. Examples: `pfizer-001`, `jnj-003`, `jpmc-002`.

### Company Slug Registry
User enters a short slug at first encounter with each company. Skill prompts for slug, stores it plus the full legal company name in `rules/organizations/company_slugs.md` (or equivalent). Subsequent applications for the same company reuse the registry lookup. No auto-derivation; user picks the slug.

### Session Log
Created at start of role_evaluation regardless of whether the user ultimately applies. Location: `personal/sessions/<slug>-NNN_session_log.md`. Records phase completions with timestamps plus key decisions (specialty confirmed, domain locked, fit verdict). Read on resume to determine state.

### Session Log Format
YAML frontmatter for metadata (ID, company, role, creation date, current state, etc.). Structured entries in body for phase completions and decisions. No free-form narrative. Enables future tracker integration via script parsing.

### Per-Application Folder
`personal/applications/<slug>-NNN_<role_slug>_<yyyy-mm>/`. Created only if the user decides to apply. Self-describing — folder name shows company, app counter, role, and date without opening the contents. User enters a short role slug at application start (lowercase, underscores or dashes). Holds downstream artifacts (CV, interview_prep, interview_completion, interview_scratch, interview_followup). Files inside the folder do not restate the role_slug; they use `<slug>-NNN` alone since role is clear from folder path.

### do_not_pursue Folder
`personal/do_not_pursue/` holds artifacts from role_evaluations that did not advance to application.

### File Naming Convention
Lowercase throughout. Compound ID embedded. Examples: `gap_analysis_pfizer-001.md`, `cv_pfizer-001.docx`, `interview_prep_pfizer-001.md`.

### Last Used Stamping
Preserved for both `Experience_Inventory` and `Career_Narratives` entries. Skills that produce accepted outputs stamp cited entries with `Last Used: YYYY-MM`. Enables distinguishing active from dormant content.

### State Detection
Ordered checks combine file existence and session log entries to determine resume point. Exact logic and location (standalone rule file vs per-skill) designed during per-skill work.

### Tracker Integration (Deferred)
External Google Drive tracker integration is not in scope for the current build. Decisions above keep it simple later: compound ID is stable and string-safe (no coercion in Sheets); YAML session logs enable script-based status extraction.

---

## Open Items

All structural design items are closed. Remaining items to be addressed during per-skill design (not structural):

- Knowledge-builder skills internal design (career_narratives, experience_inventory, positioning) — scope captured structurally; interactive prompting and tag classification behaviors are per-skill design work.
- State detection logic: exact form and location (standalone rule file, per-skill, or hybrid).
- Session log YAML schema specification.
- Application ID assignment script implementation.
- Research output file location and format (referenced in Research Sub-Agents section).
