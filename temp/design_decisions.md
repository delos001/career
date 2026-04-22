# Career Repo Design Decisions

Running record of design decisions made during evaluation of the draft spec. Updated as we go. Source of truth for the eventual repo build.

---

## Structural

### Top-Level Containers (7)
`skills/`, `rules/`, `sub-agents/`, `templates/`, `scripts/`, `outputs/`, `personal/`. Matches the seven glossary entries one-to-one. No glossary term is unhomed.

### QC Organization
Specs live in `rules/quality_control/`. Executors live in `sub-agents/quality_control/`. Skills call QC; sub-agents execute it. QC runs in sub-agents so it does not consume the skill's context window and can loop if the skill output is non-compliant.

### Template vs Format Spec
Templates are physical carrier files (e.g., Word) that get filled in and persist as outputs. Format specs are structural/rendering rules applied to free-form content. Both folders justified. No DRY issue.

### Scripts Centralized
Top-level `scripts/` folder, subdivided internally (retrieval, resolvers, format conversion, etc.). Not co-located with the skill or sub-agent that uses them, because many scripts (especially retrieval) will be called by multiple consumers.

### Skills Do Not Include Skill Registry or Control
`skill_registry` and `control` placement stays under `skills/` (TOC-adjacent to the book), but neither is a skill by the glossary. They must not contain skill-type instructions.

### Skill Registry Split
Per-skill interface metadata (trigger, prerequisites, completion signal, outputs, typical next steps) moves out of the central registry and into a standard header at each skill. State Detection Guide moves to `rules/` (it is algorithmic decision logic). The central registry either shrinks to a thin index or is auto-derived from skill headers by a script.

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

### Folder Renames Committed
- `rules/archetypes/` → `rules/specialties/`
- `rules/role_level/` → `rules/levels/`
- `skills/rule_builders/archetype/` → `skills/rule_builders/specialty/`

### Level File Names
Drop deliverable prefix. `ic.md` and `leadership.md` (not `content_ic_cv.md`). Folder path provides context.

---

## Format Spec (CV)

### Boundary
Format spec = rendering config (fonts, margins, spacing, bullet chars, file-naming pattern). Deliverable-specific, axis-agnostic. Axes shape content and voice. Format spec renders the final file. The existing CV format spec already declares this boundary on its own line 175.

### Transfer Notes
Existing `temp/format_spec.md` transfers largely as-is with two cleanups:
1. Move embedded python-docx code (lines 95-123) to a script under `scripts/`. Format spec stays declarative (values and tables only).
2. Parameterize the hardcoded name in the output filename pattern (line 182). Pull from `personal/` (knowledge or config).

---

## rule_builders Procedure Inline

`skills/rule_builders/specialty/` and `skills/rule_builders/domain/` do not have nested "building rules" files. The construction procedure is the skill itself and lives inside the skill file. No `rules/builders/` folder is created. If specialty or domain construction grows complex enough to warrant extraction later, it can be addressed at that point.

## Workflow Sequence Diagram

Deleted, not relocated. The old registry contained an ASCII workflow diagram; it does not carry over to the new repo. A richer visual (e.g., Visio) may be authored later if useful.

## Interview Template Artifacts

`interview_completion` and `interview_scratch` exist as both blank skeletons (in `templates/`, copied per round) and populated instances (in `personal/applications/[Company_...]/`). Different purposes, two locations, no duplication.

## Stack

**Orchestration:** Claude Code native (skills as markdown, Task tool for sub-agents with isolated context, hooks, Bash for Python invocation). No LangChain/LangGraph layered on top today. Revisit if the workflow becomes heavily branching with stateful multi-agent iteration beyond what skill + Task can express cleanly.

**Retrieval:** Mixed by content shape. Structured lookup (Python script fetches a known slice by slug/key) for structured documents (Experience_Inventory, Positioning, registries, format specs). RAG reserved for genuinely unstructured content (e.g., interview_scratch notes, questions_library free-form entries). Default is structured; add RAG only where structure truly doesn't exist.

**Execution:** Skills are markdown. Deterministic logic is Python scripts invoked via Bash. LLM-judgment stays in the skill or in LLM sub-agents. Build scripts alongside the skill that uses them, not after; never use an LLM where a script can verify a rule deterministically.

---

## Open Items

- `sub-agents/` folder semantics under Claude Code native: is the folder a prompt library that skills load and pass to Task invocations, or registered Claude Code agents, or both?
- Still-unexamined draft areas: `rules/global/`, `rules/narratives/`, `rules/organizations/`, `sub-agents/research/` scopes, `skills/knowledge_builders/` entries (beyond the knowledge_update collapse), the State Detection Guide's new filename/location within `rules/`, and whether the registry shrinks to a thin index or is auto-derived.
