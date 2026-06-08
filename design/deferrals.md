# Career Repo Deferred Items

When a deferral's trigger fires, promote to `open_questions.md`. Protocol in memory `process_session_protocol.md`.

## Build-Time Tasks

### skills-config-driven-paths
All built skills (role-intake, retrieval, gap-analysis, cv-targeted) hardcode repo path strings in SKILL.md prose (`personal/profile/`, application-folder filenames) rather than resolving them from `config.yaml`. The `no-hardcoded-repo-values` rule was always intended to cover skill prose, not just scripts (confirmed 2026-06-01), but was never implemented for skills. The scripts already read paths from config via `_config.py`; skills should instruct the executor to resolve paths from config the same way. Cross-skill change; do in one pass.
- Trigger: project bandwidth, or user direction.
- Blocks: nothing currently (hardcoded prose works; it just breaks on repo reorg).
- Refs: `config.yaml`, `.claude/skills/*/SKILL.md`, memory `no-hardcoded-repo-values`.

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

### axis-classification-slot-count-beyond-two
Axis classification records two values per axis (primary + secondary), and retrieval builds its deterministic axis-scoring signal from `{primary, secondary}` only - it reads the session log's `## Axis Classification` section, not `## Axis Gaps`. APP-007 (Senior Director, Data Intelligence; 2026-06-03) is the first observed role to legitimately span three values on one axis: specialty = operations-strategy + people-leadership + data-science. The third (data-science) was forced into `## Axis Gaps` and therefore excluded from the axis-scoring pass. Its underlying skills (Azure, Power BI, Databricks, advanced analytics) still surface via semantic scoring against the critical requirements, so the loss is only the deterministic axis exact-match/adjacency boost for data-science-tagged entries, not total exclusion. Hypothesis worth watching, raised by the user 2026-06-03: seniority correlates with axis breadth (a leadership role can own strategy AND people AND hands-on craft simultaneously), so the fixed two-slot cap may systematically under-weight senior/leadership roles. Options at trigger: (a) allow N ordered values per axis instead of fixed primary/secondary; (b) add a third slot only where a role demonstrably spans three; (c) keep two and accept semantic scoring as the compensation. Change spans role-intake (axis-classifier output format + session log axis section), retrieval Phase 1 (the `{primary, secondary}` JSON construction) and `scripts/retrieval_apply.py` (axis signal computation), plus any downstream consumer reading the two-slot shape (gap-analysis, cv-targeted).
- Trigger: a second observed role spanning >2 values on any axis, OR evidence the lost axis weighting changed a retrieval/CV outcome, OR user direction.
- Blocks: nothing currently (semantic scoring partially compensates).
- Refs: `retrieval-architecture-2026-05`, `five-orthogonal-axes`, `dual-orientation-asymmetric-authority` (the primary/secondary asymmetry pattern), session log `wct_APP-007_2026-06` and its `## Axis Gaps`.


## Per-Skill Design Items

### cv-targeted-reviewer-autonomy-reconciliation
**Resolved 2026-05-29** by `cv-targeted-name-and-structure-2026-05` and `cv-targeted-candidate-advocate-2026-05` (DACI stakeholder model). See those entries.

### cv-architect-multi-role-employer-title-stacking
When a single employer's cited CV bullets span multiple role records (RL-NNN), the cv-architect must render the role progression as stacked bold role-title lines (the pattern it already applies to Amgen), even when the block also uses thematic `###` subheadings; otherwise `cv_qc.py` C5 reads N role records under 1 title line and flags likely misattribution, costing an avoidable QC fix iteration. Surfaced 2026-06-05 on APP-008 (Medable): the BioMarin block folded four BioMarin roles (RL-017/018/019/020) under one title line with thematic subheadings; C5 flagged "3 employers under 1 title"; resolved by stacking the title progression with dates from inventory Section 7. Not a content defect (QC catches it every time and the architect fixes it), but it recurs on any candidate with a multi-role tenure at one employer (e.g., the user's BioMarin, four roles) and burns one iteration each run. Fix is a one-line drafting guard: add to the cv-architect agent spec (and/or `cv-structure.md`'s entry-header rule) that for a multi-role single employer the role progression renders as bold title lines so the C5 title-line count is at least the distinct cited role records.
- Trigger: next cv-targeted run for a candidate with a multi-role single employer (recurs on the user's BioMarin every run); OR user direction.
- Blocks: nothing (QC catches it; cost is one avoidable fix iteration per affected run).
- Refs: `scripts/cv_qc.py` (C5), `.claude/agents/cv-architect.md`, `rules/cv/cv-structure.md` (entry-header rule), `personal/applications/medable_APP-008_2026-06/cv_collaboration_log.md` (worked example).

### cv-stacking-newer-roles-standalone
User decided (2026-06-08) that newer multi-role single-employer blocks should NOT stack: each role should stand on its own with its own role-targeted bullets, even if only ~3 bullets. Stacking (shared bullet pool under stacked title lines) stays acceptable only for older roles. Driver is readability: the stacked BioMarin block in the APP-008 (Medable) CV is hard to digest because you cannot tell which accomplishment belongs to which role. This refines the current `cv-structure.md` "Multiple roles at one company" rule (lines ~201-216), which today picks stacked vs separate purely by bullet volume (stacked at ~1-2 bullets/role, separate at ~3+), with no recency dimension. The change adds a recency override so recent multi-role employers default to separate sub-entries. **Held by the user pending external feedback**: they want to circulate the stacked format and gather others' opinions before committing. The open boundary question (the one thing needed before editing the rule) is where the newer/older line falls: (a) current employer only must stand alone; (b) all multi-role companies within Professional Experience stand alone (effectively retires stacking there, since Earlier Professional Roles is already condensed plain lines); or (c) a recency cutoff (e.g. roles ending within the last N years stand alone). Note this is the inverse direction of `cv-architect-multi-role-employer-title-stacking` (which forces stacked title lines for C5 QC); if newer roles stop stacking, that deferral's premise narrows to older blocks only, so resolve the two together.
- Trigger: user returns with external feedback and picks a boundary (a/b/c); OR user direction.
- Blocks: nothing currently (CVs render with bullet-volume-based stacking today; the user manually adjusts).
- Refs: `rules/cv/cv-structure.md` (Multiple roles at one company, ~lines 201-216), `cv-architect-multi-role-employer-title-stacking` (inverse-direction deferral), `personal/applications/medable_APP-008_2026-06/cv_content.md` (BioMarin block, worked example).

### cv-best-practices-refresh
`rules/cv/cv-best-practices.md` is the vetted evidence base behind `cv-structure.md` and the grounding for the career-strategist stakeholder. It is static research and will go stale (the AI-tell guidance ages fastest). Refresh procedure: re-run the CV best-practice web research, reconcile against the current doc, bump `last_researched`, and cascade any rule changes into `cv-structure.md` (the rules are derived from this evidence).
- Trigger: the cv-targeted skill's runtime staleness check fires when `last_researched` is over ~12 months old (the reliable, point-of-use trigger; built into `SKILL.md` at step b). Also refresh on demand if a CV run surfaces obsolete or missing guidance.
- Blocks: nothing; the doc functions until stale.
- Refs: `cv-targeted-name-and-structure-2026-05`, `rules/cv/cv-structure.md`, `rules/cv/cv-best-practices.md`.

### cv-targeted-length-remediation-levers
The cv-targeted L1 length guard auto-drops stakeholder-vetted content to satisfy a heuristic line-count estimate, inside the Phase 4 QC loop, upstream of cv-render (the only stage that measures real page geometry). On the APP-007 run (2026-06-04) it cut a real achievement bullet (AbbVie ARIMA) and a quantified figure (CA-7 "50 candidates") for a ~2-line overage on a 149-vs-147 estimate, after three stakeholder rounds had vetted that content as relevant. User flagged this as wrong: a small overage should surface to the user, not trigger content removal. The length norm itself is real (a senior CV over ~3 pages gets screened down), so the fix is to reorder the remediation levers, not remove the ceiling: (1) small overage on the estimate → surface a warning at handoff, do not cut; (2) prefer compression-by-elevation (merge granular bullets into one higher-altitude statement) over dropping; (3) drop content only as a last resort and only against a real render measurement. Open sub-question: whether L1 should stop gating content edits entirely and move length remediation downstream of cv-render (draft → traceability QC → render → measure → trim only if truly over), inverting the current order. Note: the Phase 4 3-iteration cap is the same arbitrary-threshold pattern (forcing "ship provisional" on a 1-line estimate); on APP-007 the cap was deliberately exceeded by one pass to fix two newly-surfaced overstatements, which was correct. User deferred the redesign (behind schedule, 2026-06-04). APP-008 (Medable, 2026-06-05) is a second data point and confirms the lever-reorder works: L1 surfaced a warning and did not auto-drop content. But APP-008's overage was ~10 estimated lines (4-page estimate), much larger than APP-007's 2, after two compression-by-elevation passes that did not gut vetted content; this strengthens the open sub-question (invert the order: draft -> traceability QC -> render -> measure -> trim only if truly over), since at a 10-line estimate gap the real page count is genuinely unknown until cv-render measures it.
- Trigger: user direction; OR next cv-targeted run where L1 forces a content drop on a small overage.
- Blocks: nothing currently (cv-targeted ships correct CVs; the cost is occasional over-aggressive trimming the user must manually reverse).
- Refs: `.claude/skills/cv-targeted/SKILL.md` (Phase 4 L1 + fix loop + 3-iteration cap), `scripts/cv_qc.py` (L1 check), `cv-render-build-2026-06`, memory `feedback_cv_length_handling`, memory `feedback_no_arbitrary_length_targets` (parallel stance for docs).

### cv-content-within-entry-layout
**Resolved 2026-05-29** by `cv-targeted-name-and-structure-2026-05`. See that entry.

### gap-analysis-schema
**Resolved 2026-05-27** by `gap-analysis-architecture-2026-05`. Full schema lives there.

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
**Resolved 2026-05-26** by `retrieval-architecture-2026-05`. See that entry.

### cross-axis-composition-mechanism
Mechanism by which cv_targeted reconciles per-axis composition outputs. Possibilities range from per-axis sub-agents proposing content for their owned surface and engaging in review/challenge rounds to converge, to rule-based application of default precedence with no cross-axis review. Specific implementation deferred to cv_targeted skill design.
- Trigger: cv_targeted skill design.
- Blocks: cv_targeted build.
- Refs: `axes-composition-precedence`, `cv-targeted-content-rules-from-axes`, `cv-targeted-weighted-matching`.

### axis-adjacency-weights-redefinition
**Resolved 2026-05-26** by `retrieval-architecture-2026-05` (exact axis match 1.0, adjacent 0.5; per-axis Adjacency may override). See that entry.

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
**Status (2026-05-29):** Largely authored into `rules/cv/cv-structure.md` (CCAR; impact types + fallback chain; Core Competencies zoning for data-analytics and platform-technology; project voice exception; adjacency translation; acronym rule). Routed elsewhere, not into the structure file: tag-query logic and inventory-coverage-gap flagging (owned by retrieval / the cv-targeted skill procedure); achievement-framing-by-orientation points to the orientation axis files' Section emphasis rather than being duplicated. Remaining procedure-level items resolve at step b (skill build).
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
**Status (2026-05-29):** Authored into `rules/cv/cv-structure.md`: two-band section order (with Affiliations conditional), Core Competencies counts (8-10 IC / 8-12 leadership), bullet length limits (2 target / 3 max / 4 never), page targets (IC 2-3, leadership ceiling 3), and the em-dash rule (tightened to no em dashes at all, superseding the header-separator allowance). `format_spec.md` stays .docx-rendering-only; fixing its dangling "section order set by archetype" pointer remains a step-c item.
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

### tenure-as-years-rendering
`cv-best-practices.md:62` calls Kristal et al. (2022, Nature Human Behaviour, N≈9,022) the single strongest empirical finding in the brief: rendering tenure as years worked instead of date ranges raised callbacks ~15% vs gapped resumes and ~8% even vs gap-free ones, and line 63 names "a 'years of tenure' rendering option" an evidence-based design feature. But the rule it grounds does not reflect it: `cv-structure.md:117` mandates date-range headers only ("Company | Location | dates, then the role title and its dates") with no tenure-as-years option, and `cv_qc.py` N1 (lines 474-499) reads 4-digit year tokens from header lines to enforce reverse-chronological order and start<=end, i.e. it assumes and parses date ranges. Surfaced 2026-06-02 during the cv-targeted audit (F5). Direction: the finding has a trade-off the brief itself flags (line 63) - pure year-only headers can read evasive and break ATS date parsing; the study tested tenure framing, not removing chronology - so the fix is most likely additive (a "(N yrs)" annotation alongside the date range, or an architect-selectable mode when gaps exist), not replacing date ranges. Resolving it well is a CV-format design decision spanning three artifacts in concert: `cv-structure.md` (define the option), `cv_qc.py` N1 (tolerate the annotation), and the render skill (cv-render).
- Trigger: investment in the additive tenure-as-years header option, OR a real application where employment-gap framing materially affects callbacks, OR user direction. (Note: the original "cv-render skill design" trigger fired 2026-06-02 when cv-render was built, but did not resolve this - cv-render is a judgment-free renderer that takes cv_content.md's date-range headers as-is, so its existence does not force the decision. Trigger reset to the real condition.)
- Blocks: nothing currently; the skill produces correct CVs with date ranges today.
- Refs: `rules/cv/cv-best-practices.md` (Kristal finding), `rules/cv/cv-structure.md` (entry header), `scripts/cv_qc.py` (N1), `.claude/agents/career-strategist.md` (owns the tenure-as-years gap-framing lever at its domain, but cannot apply it under the current structure rule), `cv-format-spec-from-axes`.

### cv-render-uppercase-section-headers
User wants the `##` section headers (Professional Summary, Core Competencies, Professional Experience, Earlier Professional Roles, Education, Certifications & Training, Technical Proficiencies) rendered in ALL CAPS to break sections up for a reviewer. Scope: section headers only - NOT the name, NOT the `###` within-role subheadings, NOT company/job-title lines (all stay mixed case). This reverses an explicit, example-grounded rule (`format_spec.md`: "Section headers must be mixed case bold, never ALL CAPS", two places); flagged to and overridden by the user 2026-06-03. Implementation, both in lockstep: `cv_to_docx.py` `add_section_header` uppercases the display text (keep bold); flip the two "never ALL CAPS" rules in `format_spec.md` to "ALL CAPS". Render-only; `cv_content.md` stays mixed case. User deferred to "the end" of the 2026-06-03 render-tuning session, then closed before applying.
- Trigger: user direction (next render-styling pass).
- Blocks: nothing; CVs render with mixed-case headers today.
- Refs: `design/format_spec.md`, `scripts/cv_to_docx.py`, `cv-render-build-2026-06`, `cv-targeted-render-refinements-2026-06`.

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

