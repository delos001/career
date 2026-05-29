# Career Repo Deferred Items

When a deferral's trigger fires, promote to `open_questions.md`. Protocol in memory `process_session_protocol.md`.

## Build-Time Tasks

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

### inventory-filter-tool
A CLI or UI utility that filters `inventory.md` EX/PR entries by Role (RL-NNN), Industry, Specialty, Orientation, Level, Work-state, or other tag axes. Surfaces matching entries with ID + Description for human review. Needed for narrative authoring (selecting Linked Inventory anchors), CV bullet sourcing, and inventory navigation generally. The flat-file structure of the inventory makes manual lookup impractical at 216-entry scale.
- Trigger: next narrative authoring or refresh task, or when CV bullet sourcing becomes a recurring workflow.
- Blocks: nothing currently.
- Refs: `career-narratives-schema`.

### inventory-builder-research-classification-sections-5-6
inventory builder skill needs a research component to classify Section 5 (Technical Experience) tools and Section 6 (Industry Exposure Profile) content against industry-pack and specialty-pack vocabularies. Drives downstream retrieval relevance and cv_targeted's ability to surface section content matched to JD industry/specialty signals.
- Trigger: inventory builder skill design.
- Blocks: inventory builder build; cv_targeted's section-5/section-6 consumption pattern.
- Refs: `experience-inventory-section-5-restructure`, `experience-inventory-section-6-rename`, `cv-targeted-content-rules-from-axes`.

### inventory-builder-quality-check-encoding
inventory builder must encode all quality checks accumulated across reconciliation passes, so future inventory creation/refresh does not require manual reconciliation. Specification consolidated in `design/inventory_builder_quality_checks.md`; categories: structural integrity, content quality within entries, cross-entry quality, voice consistency, coverage, taxonomic notes. New checks surfaced during ongoing reconciliation get added to that file inline.
- Trigger: inventory builder skill design.
- Blocks: inventory builder build.
- Refs: `design/inventory_builder_quality_checks.md`, `inventory-builder-research-classification-sections-5-6`.

### qc-rules-execution-mode-tagging
Re-tag each rule in `design/inventory_builder_quality_checks.md` with an execution-mode dimension (auto / quick-review / judgment) alongside its existing shape category (Structural / Content / Cross-entry / Voice / Coverage / Taxonomic). Shape describes what kind of issue the rule catches; execution-mode describes what handling a finding costs the user. The two are orthogonal. Goal: enable a QC report (and eventual QC agent) to sort/group findings by mode so user engagement matches activity importance — auto-fixes execute silently, cheap-review batches surface as tables, judgment findings get full structured presentation. Insight surfaced 2026-05-08 during exploration of QC efficiency: user couldn't tell from "verification" whether a finding was a 30-second decision or a 30-minute one, which contributed to the 6-session / 8-hour cost of the prior audit.
- Trigger: before next QC pass after the immediate final clean pass; or before QC agent design.
- Blocks: nothing currently; QC can run with current organization.
- Refs: `design/inventory_builder_quality_checks.md`, audit-phase-ordering rule (in same file).

### inventory-qc-findings-decision-log
A decision log for QC findings on the inventory that could not be fully closed by updating the source document (e.g., user-reviewed findings resolved as "no change needed; reviewed YYYY-MM-DD with reason"). Goal: prevent re-flagging the same findings on subsequent QC rounds and avoid wasted review cycles on settled questions. Expected scope minimal: primary resolution path should always remain source-document updates that make the finding self-evidently inapplicable on the next pass; the decision log captures only the residual cases where source-update doesn't dispel the finding (e.g., a tag that looks ambiguous on its face but has a documented justification). Format, storage location, and entry schema TBD.
- Trigger: inventory builder skill design.
- Blocks: nothing currently (manual audits proceed with the user's mental model of "no-change-needed").
- Refs: `inventory-builder-quality-check-encoding`, `design/inventory_builder_quality_checks.md`.

### axis-builder-qc-drift-resolution
The acronym check in `scripts/axis_qc.py` flags ~70 mismatches across pharma, biotech, med-device, and diagnostics industry files. Sample analysis (pharma, 2026-05-26) shows a roughly 60/40 noise-to-real split: regex artifacts ("JSON" pulled out of "Dataset-JSON"), cross-domain reference noise (NIH, NEJM appearing as external-organization names in body prose), and a smaller set of genuine catalog/body inconsistencies. Pharma partial cleanup applied 2026-05-26 (dropped OOS from catalog; spelled out CFR as "21 CFR (Code of Federal Regulations) Part 11" on first use; added CDER/CBER/CDRH to catalog; added eCRF to body in Adjacency's eclinical bullet). Remaining ~25 pharma items and the full mismatch set in biotech/med-device/diagnostics deferred — axis builders are tangential to core capability builds. Note: even spelled-out terms (like CFR after the pharma edit) remain flagged by the mechanical check because the token still appears in body without being in the catalog; the spell-out-on-first-use convention is a human-reader pattern, not a check-satisfying pattern. Two paths to evaluate at trigger: (1) fix each remaining flagged item correctly (drop from catalog, add to catalog, or rewrite body to remove the token), (2) build an "accepted findings" log mechanism so noise can be suppressed permanently — same pattern as `inventory-qc-findings-decision-log`.
- Trigger: next axis-builder refresh, OR concurrent with `inventory-qc-findings-decision-log` build.
- Blocks: nothing currently (axis files remain functional; the acronym check is report-only).
- Refs: `inventory-qc-findings-decision-log` (parallel mechanism), `scripts/axis_qc.py`, `rules/quality_control/qc-industry-builder.md`.

### design-decisions-audit-closure-bloat-cleanup
**Resolved 2026-05-26.** Five audit-log entries removed from `design_decisions.md`: the three named audit-closure entries (`experience-inventory-final-audit-phases-1-2-and-3p-applied-2026-05`, `experience-inventory-final-audit-phase-5-applied-2026-05`, `experience-inventory-final-audit-step-0-and-phases-6-7-applied-2026-05`) plus two related apply-status entries (`specialty-retagging-applied-2026-05`, `specialty-training-entries-catch-all-cleanup-2026-05`). Genuine design changes from those entries live in their authoring slugs and rule files: QC rules in `design/inventory_builder_quality_checks.md`, the rl-allocation schema in `rl-allocation-field-schema-2026-05`, the orientation scope-qualifier change in `rules/orientations/transformation-strategy.md`, and the memory feedback entries in `memory/`. Broken slug refs cleaned up across `design_decisions.md`. Standing rule going forward: future audit closures stay as memory or session-log notes; only genuine design changes (rules, schemas, architectural shifts) go into `design_decisions.md`.
- Refs: `design/design_decisions.md`, `design/inventory_builder_quality_checks.md`.

### vacuous-design-decisions-cleanup
**Resolved 2026-05-26.** `rule-builder-skills-inline-procedure` removed from `design_decisions.md`. Future vacuous entries surfaced during ongoing review get handled inline; no need for a perpetual parking-spot deferral.
- Refs: `design/design_decisions.md`, `design-decisions-audit-closure-bloat-cleanup` (parallel cleanup deferral, still open).

### registry-overlap-tracking
Use `rules/industries/registry.md` (or an extension file) as a cross-reference of which terms appear in which industry files, so updates to shared regulatory/vocabulary terms (FDA guidance, ICH adoptions) can be propagated to all relevant files. Full-enumeration approach (`industry-files-full-enumeration`) duplicates shared terms across pharma/biotech/cro; redundancy is acceptable now but update-cost grows over time.

The same inverted term index is the scaled fix for the axis-builder QC D1 check (cross-sibling-content redundancy). D1 currently reads whole sibling files into the QC subagent's context, which is O(N-siblings); the deliberate choice to leave it that way holds only while axes stay small. At scale the fix is to compute verbatim term/acronym overlap deterministically against the index and surface only the flagged candidates to the subagent, making its context independent of sibling count. One index serves both the propagation use case and D1.
- Trigger: first shared-term update where propagation cost surfaces as friction; or any axis registry exceeding ~15 file-backed values (where D1's whole-file reads start to pressure context); or earlier if foundation tooling investment is warranted.
- Blocks: nothing currently.
- Refs: `industry-files-full-enumeration`, `builder-reconciler-adjacency-slice-2026-05` (D1 whole-file rationale).

### participant-terminology-cross-file-consistency
The Participant terminology paragraph ("participant" is the current preference in protocols and consent forms... TransCelerate / NIH / FDA / NEJM standard) is verbatim identical in `rules/industries/pharma.md` and `rules/industries/biotech.md`. Surfaced 2026-05-19 during /industry-builder refresh of cro.md when D1 fired on the same paragraph copied into cro.md from the prior 2026-04 build. The paragraph is cross-cutting CV-style editorial guidance, not industry-specific. Resolved for cro.md by dropping the paragraph (D1 cleared). The pharma↔biotech overlap is still in place and would fire D1 on any future refresh of either file. Options: (a) drop the paragraph from pharma.md and biotech.md (matches the post-cro state across 6 of 7 industry files); (b) move the rule to a cross-cutting location such as `rules/conventions/participant-terminology.md` or fold into a future CV format spec, and remove from all industry files; (c) accept the duplication and override D1 with a documented exception for cross-cutting CV-style content.
- Trigger: next refresh of pharma.md or biotech.md (D1 will fire); or before cv_targeted skill design if cross-cutting CV rules need a canonical home.
- Blocks: nothing currently (clean ship on cro.md was achieved).
- Refs: `rules/industries/pharma.md`, `rules/industries/biotech.md`, `rules/quality_control/qc-industry-builder.md` (D1 definition), `cv-format-spec-from-axes` (parallel cross-cutting concern).

### skill-file-line-wrap-normalization
SKILL.md files have inconsistent line-wrap conventions. role-intake/SKILL.md is mostly wrapped at ~80 chars; retrieval/SKILL.md and gap-analysis/SKILL.md run long lines (some >900 chars). Pick one convention and apply across all SKILL.md, agent .md, template .md, and other prose files in the repo in one pass.
- Trigger: project bandwidth, or user direction.
- Blocks: nothing currently.
- Refs: `.claude/skills/*/SKILL.md`, `.claude/agents/*.md`, `templates/*.md`.

### bloated-skill-architecture-revisit
Built skills (role-intake, retrieval, gap-analysis) carry architectural bloat: per-phase input/output declarations, sub-step enumeration, route-back tables, structured JSON contracts between subagents, deterministic rendering scripts, and separate QC files with enumerated checks. The legacy 65-line gap-analysis + role-fit reference (pre-career-repo project) shows the work itself does not require this scaffolding pattern. Pattern surfaced 2026-05-27 during gap-analysis audit; user declined to redesign mid-project to avoid cross-skill inconsistency and the audit-finding cycles that would generate. Revisit in one pass across all built skills when project bandwidth allows.
- Trigger: project bandwidth, or user direction.
- Blocks: nothing currently; built skills function as-is.
- Refs: `gap-analysis-architecture-2026-05`, `role-intake-architecture`, `retrieval-architecture-2026-05`.

### axis-programmatic-slicing-audit
Audit all axes (industries, specialties, orientations, levels, work-states) to verify section structure supports programmatic section-level retrieval rather than full-file reads into LLM context. Goal: skills consume only relevant sections of axis files (Vocabulary, Dialect, Emphasis, Adjacency individually addressable), not entire files. Refactor where not.
- Trigger: knowledge files finalized.
- Blocks: section-level retrieval scripts; downstream skills depending on retrieval pattern.
- Refs: `axes-file-schema`, `stack-retrieval`.


## Per-Skill Design Items

### cv-targeted-reviewer-autonomy-reconciliation
After the cv-targeted agents are built (step b), reconcile to confirm the career-dev and hiring-manager reviewer agents have genuine authority to participate, challenge, and shape the CV, and are not steamrolled by the prescriptive `rules/cv/cv_structure.md` (400+ lines) plus the sole-writer Drafter. Check: arbitration precedence leaves reviewers real latitude on their owned layers (career-dev = how/craft, HM = what/coverage); hard rules constrain without erasing judgment; reviewer findings can change the draft, not just rubber-stamp it.
- Trigger: cv-targeted agents authored (step b).
- Blocks: step-b sign-off.
- Refs: `cv-content-agent-architecture-2026-05`, `cv-content-collaboration-mechanism-2026-05`, `cv-targeted-name-and-structure-2026-05`.

### cv-content-within-entry-layout
**Resolved 2026-05-29 by `cv-targeted-name-and-structure-2026-05`:** flat by default; thematic subheadings only on recent, accomplishment-heavy senior/leadership roles with CR-sourced labels (capped 3-6); IC always flat; arc rollups synthesize into one bullet via narratives. Bullet-capacity guard constant set at ~90-95 chars/line (flat). Original framing below.

Whether experience entries use within-role sub-section groupings (doc 1 style: sub-headers such as "Strategic Process Leadership & Governance" with an indented role-summary line and deeper bullet indent) or flat bullets directly under the role (doc 2 style, shallower indent, optionally with front "Role-Aligned Capabilities" / "Selected Outcomes" blocks). The choice drives bullet density (chars/line ~85 nested vs ~95 flat) and therefore the calibration guard's bullet-capacity constant. Surfaced 2026-05 during length calibration from the user's two sample CVs.
- Trigger: cv_structure.md authoring / cv-content build.
- Blocks: structure-file content; the bullet-capacity guard constant.
- Refs: `cv-content-output-and-length-2026-05`, `cv-content-structure-decisions-2026-05`.

### gap-analysis-schema
**Resolved 2026-05-27 by `gap-analysis-architecture-2026-05`.** Output schema settled: `gap_analysis.md` carries a header (APP-NNN, date, fit score, unmet must-haves count, recommendation label) and six sections (Eligibility Flags, Requirements, Language-Shift Cases, De-emphasize, Recommendation — optional sections render `_(none)_` when empty). Per-requirement records carry CR-NNN id, text, type, status from the locked taxonomy (covered / closed / language-shift / interview-deferred / unresolved), evidence IDs, and notes. The format does not depend on cv_targeted; cv_targeted reads `gap_analysis.md` as input.
- Refs: `gap-analysis-architecture-2026-05`.

### introduction-roster-ambiguous-skills
Introduction classification for `interview_capture`, `interview_followup`, `cv_general`, `inventory`, `narratives`.
- Trigger: each skill at its design time.
- Blocks: those skill builds.
- Refs: `workflow-communication-conventions`.

### why-i-left-specifics-for-interview-prep
Positioning.md's "Why I Chose to Leave BioMarin" section is deliberately diplomatic for external use (no named transition, no defined "traditional model," no specified modernization scope). Interview follow-ups will probe behind the diplomatic language: what changed in the leadership transition, what "traditional model" means concretely, what kind of modernization the current scope does not allow. The specifics needed to defend the diplomatic version under questioning belong in interview_prep skill content (or a private prep document interview_prep references), not in positioning.md. Surfaced 2026-05-25 during positioning audit (finding #13); user chose Option 1 (positioning stays as-is) + Option 3 (specifics deferred to interview_prep design).
- Trigger: interview_prep skill design.
- Blocks: interview_prep build — the skill cannot anticipate follow-up questions without these specifics.
- Refs: `positioning-schema` (the section's diplomatic framing was retained per this design decision); `personal/profile/positioning.md` (Why I Chose to Leave BioMarin section); `.claude/skills/interview_prep/SKILL.md` (Drafted).

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
**Resolved 2026-05-26 by `retrieval-architecture-2026-05`.** All previously deferred implementation details settled: semantic pass is LLM-judgment (not RAG) on Description + Impact, chunked at ~50 entries per call; deterministic tag-pull pass is adjacency-aware with N≥1 inclusion floor; merge happens at manifest level with raw signals exposed (semantic score, axis exact-match count, axis adjacency-weighted score) for downstream tier derivation rather than pre-computed at retrieval. Reshaping moved retrieval out of cv_targeted into a standalone skill serving all downstream consumers.
- Refs: `retrieval-architecture-2026-05`, `cv-targeted-retrieval-architecture-2026-05` (superseded).

### cross-axis-composition-mechanism
Mechanism by which cv_targeted reconciles per-axis composition outputs. Possibilities range from per-axis sub-agents proposing content for their owned surface and engaging in review/challenge rounds to converge, to rule-based application of default precedence with no cross-axis review. Specific implementation deferred to cv_targeted skill design.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `axes-composition-precedence`, `cv-targeted-content-rules-from-axes`, `cv-targeted-weighted-matching`.

### axis-adjacency-weights-redefinition
**Resolved 2026-05-26 by `retrieval-architecture-2026-05`.** Adjacency weights drive retrieval-time axis scoring (exposed in the manifest as an adjacency-weighted float per entry) and feed downstream tier derivation by gap analysis and CV creation. Default semantics: exact axis-value match = 1.0, adjacent value per axis file's Adjacency section = 0.5. Per-axis-file Adjacency text remains authoritative; individual axis files may override the 0.5 default if their Adjacency section so specifies. Open follow-on for translation-strength behavior (CV bullet rewording vs filtering) reverts to `cv-targeted-content-rules-from-axes` and `cv-targeted-weighted-matching` at cv_targeted build time.
- Refs: `retrieval-architecture-2026-05`, `cv-targeted-weighted-matching`, `cv-targeted-content-rules-from-axes`.

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
**Status (2026-05-29):** Largely authored into `rules/cv/cv_structure.md` (CCAR; impact types + fallback chain; Core Competencies zoning for data-analytics and platform-technology; project voice exception; adjacency translation; acronym rule). Routed elsewhere, not into the structure file: tag-query logic and inventory-coverage-gap flagging (owned by retrieval / the cv-targeted skill procedure); achievement-framing-by-orientation points to the orientation axis files' Section emphasis rather than being duplicated. Remaining procedure-level items resolve at step b (skill build).
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
**Status (2026-05-29):** Authored into `rules/cv/cv_structure.md`: two-band section order (with Affiliations conditional), Core Competencies counts (8-10 IC / 8-12 leadership), bullet length limits (2 target / 3 max / 4 never), page targets (IC 2-3, leadership ceiling 3), and the em-dash rule (tightened to no em dashes at all, superseding the header-separator allowance). `format_spec.md` stays .docx-rendering-only; fixing its dangling "section order set by archetype" pointer remains a step-c item.
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

### scaffolding-folder-layout
Folder name, sub-folder layout, file naming for `support/`.
- Trigger: scaffolding migration.
- Blocks: scaffolding migration.
- Refs: `knowledge-document-scaffolding`.

### scaffolding-content-updates
Strip phase-based references; describe loading patterns descriptively; update skill names; add metadata header to `user-info.md` template.
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

