# Career Repo Deferred Items

**Scope (as of 2026-07-16):** this file holds only *deferred decisions* — items where we have not decided whether the thing is needed at all, and a named condition would tell us. Work that is decided-but-unbuilt lives in GitHub issues (`delos001/career`), not here.

The tests an entry must pass to stay in this file:

1. **Trigger test.** Can you name the condition that fires it, in terms you would recognize when it happens? "User need surfaces" and "first request for X" are not triggers; they are "someday."
2. **Needed test.** Have we decided the thing is needed? If yes, it is an enhancement — file it in GitHub. Only genuinely undecided items belong here.
3. **Fossil test.** Does its premise still exist, or was the thing it depends on designed away?

When a trigger fires, promote to `open_questions.md` or file the issue. Protocol in memory `process_session_protocol.md`.

Tombstones below are deliberate: `design_decisions.md` and several other files reference these slugs, so the headings stay to keep those pointers resolving. Do not delete a tombstone without repointing its inbound refs.

## Active Deferred Decisions

### gap-detector-read-reduction
gap-detector reads retrieval.md + inventory.md + narratives.md in full (~60-80k tokens, once per application). Assessed 2026-07-14 and deliberately left alone: the manifest surfaces the entire corpus by design (broad recall so gap detection produces no false gaps; the axis floor cannot discriminate on this profile since nearly every entry is adjacent on at least one axis), so the only real read-reduction lever is making retrieval genuinely selective (semantic-score threshold), a recall-vs-cost design change, not an optimization.
- Trigger: inventory grows several-fold beyond ~220 entries (the arithmetic then favors a scoring threshold on gap-detector's reading set despite the recall risk).
- Blocks: nothing currently.
- Refs: `retrieval-architecture-2026-05`, `qc-mechanical-script-retrofit-2026-07`, memory `retrieval-token-cost`.

### axis-classification-slot-count-beyond-two
**Undecided: whether any change to slot count is needed at all.** The options below are what we would choose among *if* we decide yes; they are not a menu implying the need is established.

Axis classification records two values per axis (primary + secondary), and retrieval builds its deterministic axis-scoring signal from `{primary, secondary}` only - it reads the session log's `## Axis Classification` section, not `## Axis Gaps`. APP-007 (Senior Director, Data Intelligence; 2026-06-03) is the first observed role to legitimately span three values on one axis: specialty = operations-strategy + people-leadership + data-science. The third (data-science) was forced into `## Axis Gaps` and therefore excluded from the axis-scoring pass. Its underlying skills (Azure, Power BI, Databricks, advanced analytics) still surface via semantic scoring against the critical requirements, so the loss is only the deterministic axis exact-match/adjacency boost for data-science-tagged entries, not total exclusion. Hypothesis raised by the user 2026-06-03: seniority correlates with axis breadth (a leadership role can own strategy AND people AND hands-on craft simultaneously), so the fixed two-slot cap may systematically under-weight senior/leadership roles.

**Evidence as of 2026-07-16 (the `## Axis Gaps` section of all 17 session logs was read):** APP-007 remains the *only* role that has ever spanned three values on one axis. Ten applications have run since, several of them leadership (APP-008 VP-tier, APP-015 and APP-016 among them), and every one records "None". The hypothesis is **not supported to date**. Not refuted either — ten is a small sample and APP-007 was a Senior Director — but the direction of the evidence runs against it. Record any further recurrence here rather than re-deriving this.

Options at trigger: (a) allow N ordered values per axis instead of fixed primary/secondary; (b) add a third slot only where a role demonstrably spans three; (c) keep two and accept semantic scoring as the compensation. Change spans role-intake (axis-classifier output format + session log axis section), retrieval Phase 1 (the `{primary, secondary}` JSON construction) and `scripts/retrieval_apply.py` (axis signal computation), plus any downstream consumer reading the two-slot shape (gap-analysis, cv-targeted).
- Trigger: a second observed role spanning >2 values on any axis, OR evidence the lost axis weighting changed a retrieval/CV outcome, OR user direction.
- Blocks: nothing currently (semantic scoring partially compensates).
- Refs: `retrieval-architecture-2026-05`, `five-orthogonal-axes`, `dual-orientation-asymmetric-authority` (the primary/secondary asymmetry pattern), session log `wct_APP-007_2026-06` and its `## Axis Gaps`.

### ic-axis-finer-grained-files
**Undecided: whether splitting is needed at all.** Whether/when to split `ic.md` into junior-IC, mid-IC, senior-IC (Staff/Principal). 2026-04-29 research surfaced a meaningful gap between junior IC framing (project scope, hands-on verbs) and Staff/Principal framing (architecture-scale decisions, cross-team influence, influence without authority). Currently bridged within one file via voice/scope qualifiers ("differs in depth, independence, complexity, and breadth of technical influence"). Whether that bridge holds is the actual open question, and it has never been tested.

**The original trigger already half-fired and was never recorded (found 2026-07-16).** The trigger read "a Staff/Principal-flavored role application surfaces AND the unified file's framing fails to carry senior IC voice cleanly." APP-011 (Gilead, "AI Data Science Lead - Research", 2026-06-09) is that application: classified `ic` — "Lead/Staff-equivalent with no direct reports; mentors but does not manage" — and the only non-leadership application of 17. It scored 77.0% fit, zero unmet must-haves, Proceed. Outcome: `not-pursued` (2026-06-15), so the pipeline stopped at gap-analysis and cv-targeted never ran. The role arrived; the framing was never exercised.

So this is no longer waiting on an event. It is waiting on a test that can be run today: APP-011's full input set (`jd.md`, `research.md`, `retrieval.md`, `gap_analysis.md`, session log with axis classification) is preserved. Note also that this user's application pattern is leadership-heavy (16 of 17), so waiting for another IC application may wait forever; the need is product-general even where this user's flow does not test it.
- Trigger: **GitHub #50** (run cv-targeted against APP-011 and judge whether `ic.md` carries senior-IC voice), OR **#35** (the second-user transfer test, if that user is an IC — the question then answers itself against a real profile). Superseded the original "a Staff/Principal role surfaces" trigger, which fired 2026-06-09.
- Blocks: nothing currently.
- Refs: `level-axis-two-buckets`, GitHub #50, #35, #51 (the leadership-side parallel, which IS decided and lives in GitHub).

### staleness-per-axis-overrides
**Undecided: whether per-axis overrides are needed at all.** Per-axis overrides on the 9-month staleness threshold — e.g. whether `pharma.md` should go stale faster than `ic.md` because regulatory guidance moves faster than what a Staff engineer is.

Distinct from staleness *detection*, which is a live bug in GitHub #47, not a deferral. The 9-month constant itself is decided and settled (`rule-staleness-threshold`, reconfirmed by the user 2026-07-16); do not re-open it.
- Trigger: **#47 is wired AND at least one refresh cycle has run.** Until staleness detection exists for axis files at all, no axis has ever been refreshed on a staleness signal, so the "evidence supports divergent drift rates" the original trigger asked for cannot exist. Replaced that non-trigger 2026-07-16.
- Blocks: nothing currently.
- Refs: `rule-staleness-threshold`, GitHub #47.

### profile-usage-derivation-report
A script that derives profile-entry usage from the application artifacts rather than from stamped fields, since `provenance-stamps-dropped-2026-07` removed `Added` / `Last Used`. Sources: each application's retrieval manifest (what surfaced), `cv_content.md` `<!-- src: ID -->` citations (what was actually used), and the gap-analysis / prep evidence citations. Emits per entry: which applications cited it, at what dates, and at what strength (surfaced-only versus CV-cited — different signals for archiving). `Added` equivalents come from the personal repo's git history (`git log -S "ID: EX-NNN"`), which dates entries to the day rather than the field's month granularity. Answers "what was added this year", "which entries never get used" (the inventory-ret archiving question the stamps were originally for), and "which entries carry the most weight". User framed a visualization/dashboard layer over the aggregate as the eventual shape; low priority (raised 2026-07-16).
- Trigger: user demand for the archiving decision or the importance visualization; or inventory growth making inventory-ret archiving live.
- Blocks: nothing. Corpus-level questions are answerable ad hoc from the same artifacts in the interim.
- Refs: `provenance-stamps-dropped-2026-07`, `last-used-stamping` (superseded), `feedback_scripts_separate_by_concern`.

## Under Audit (GitHub #6)

These entries are gated on triggers that have already fired, or whose premise may have dissolved. They are held here in full because #6's action is "confirm resolved and delete, or restate with a real trigger," and that work happens in these entries. Do not delete them ahead of that audit.

### introduction-roster-ambiguous-skills
Introduction classification for `cv_general`, `inventory`, `narratives`. (Resolved for the interview family: preparation-screen and interview-notes 2026-06-11, followup 2026-06-26; all open conversationally with intake, no introduce.py entry. `interview_capture` retired, superseded by interview-notes; see `interview-notes-architecture-2026-06`.)
- Trigger: each skill at its design time.
- Blocks: those skill builds.
- Refs: `workflow-communication-conventions`. Under audit: GitHub #6.

### builder-refresh-mechanics
Diff presentation, approval gate shape, file-write flow for create vs refresh across the four axis builders.
- Trigger: first builder skill at design time. **(Fired: all five axis builders are built.)**
- Blocks: builder skill builds.
- Refs: `builder-mode-parameter`, `builders-axis-parity`. Under audit: GitHub #6.

### cv-targeted-weighted-matching
Weighted matching by JD emphasis: industry-emphasis weights Industry higher; specialty-emphasis weights Specialty higher; both required = equal weight. Generalizes to all five axes once per-axis weighting heuristics are defined.
- Trigger: cv_targeted skill design. **(Fired: cv-targeted is built.)**
- Blocks: cv_targeted build.
- Refs: `five-orthogonal-axes`, `experience-inventory-domain-scoping`, `axis-adjacency-weights-redefinition`. Under audit: GitHub #6.

### cross-axis-composition-mechanism
Mechanism by which cv_targeted reconciles per-axis composition outputs. Possibilities range from per-axis sub-agents proposing content for their owned surface and engaging in review/challenge rounds to converge, to rule-based application of default precedence with no cross-axis review. Specific implementation deferred to cv_targeted skill design.
- Trigger: cv_targeted skill design. **(Fired: cv-targeted is built.)**
- Blocks: cv_targeted build.
- Refs: `axes-composition-precedence`, `cv-targeted-content-rules-from-axes`, `cv-targeted-weighted-matching`. Under audit: GitHub #6.

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
- Trigger: cv_targeted skill design. **(Fired: cv-targeted is built.)**
- Blocks: cv_targeted build.
- Refs: `rules/orientations/*`, `rules/levels/*`, `rules/industries/*`, `rules/specialties/*`, `rules/work-states/*`. Under audit: GitHub #6.

### role-evaluation-orientation-selection-from-axes
Orientation selection logic and match criteria stripped from axis rule files. Belongs in role_evaluation, not rule files. Items to apply when designing role_evaluation:
- Orientation match criteria split by IC vs leadership scope (e.g., transformation-strategy at leadership level requires enterprise-level organizational change; transformation-strategy at IC level requires execution within a transformation program).
- Disambiguation logic ("verify against orientation N if..."): if the role centers on standardization or steady-state efficiency, verify against process-operations; if platform-focused, verify against platform-technology; if data-strategy-focused, verify against data-analytics; if enterprise organizational transformation, verify against transformation-strategy.
- Dual-orientation detection: when a role legitimately maps to two orientations; primary/secondary asymmetric authority per `dual-orientation-asymmetric-authority`.
- Orientation exclusion criteria (route-to-other-orientation logic): each orientation file's Identity section names exclusion conditions; role_evaluation enforces them during orientation selection.
- Trigger: role_evaluation skill design. **(Fired: role-intake is built.)**
- Blocks: role_evaluation build.
- Refs: `rules/orientations/*`, `dual-orientation-asymmetric-authority`. Under audit: GitHub #6.

## Moved to GitHub (2026-07-16)

Decided-but-unbuilt work. Headings retained so inbound `Refs:` pointers keep resolving.

### skills-config-driven-paths
Moved to GitHub **#22**.

### vocabularies-reference-script
Moved to GitHub **#38**.

### metadata-header-reconciliation-script
Moved to GitHub **#39**.

### inventory-filter-tool
Moved to GitHub **#25**.

### inventory-builder-research-classification-sections-5-6
Moved to GitHub **#27** (folded in as a sub-item of the inventory builder build).

### inventory-builder-quality-check-encoding
Moved to GitHub **#27** (folded in as a sub-item of the inventory builder build).

### qc-rules-execution-mode-tagging
Moved to GitHub **#49**. Sequencing note: do it before #27, not after — the inventory builder must encode these rules, and doing the tagging first means each rule is touched once.

### inventory-qc-findings-decision-log
Moved to GitHub **#48**, generalized beyond inventory. Its recorded trigger ("inventory builder skill design") was wrong: #10 needs the same mechanism today.

### axis-builder-qc-drift-resolution
Moved to GitHub **#10**.

### registry-overlap-tracking
Moved to GitHub **#43**, promoted to a skeleton build rather than waiting on the trigger.

### participant-terminology-cross-file-consistency
Moved to GitHub **#13**.

### cv-qc-section-structure-single-source
Moved to GitHub **#21**.

### skill-file-line-wrap-normalization
Moved to GitHub **#5**.

### bloated-skill-architecture-revisit
Moved to GitHub **#23**.

### axis-programmatic-slicing-audit
Moved to GitHub **#24**.

### profile-startup-investment-gradient
Moved to GitHub **#15**.

### cv-architect-multi-role-employer-title-stacking
Moved to GitHub **#18**. Resolve together with #11 (they point in opposite directions).

### cv-stacking-newer-roles-standalone
Moved to GitHub **#11**. Resolve together with #18.

### cv-best-practices-refresh
Moved to GitHub **#47** (folded in). This was never a deferral: it is the refresh *procedure* for `cv-best-practices.md`, the one stamped file with no builder skill to own its refresh, and `cv-targeted/SKILL.md:112` references it at runtime ("per the `cv-best-practices-refresh` process"). #47 relocates the procedure into `rules/cv/cv-best-practices.md` itself and repoints the skill. **Do not delete this heading until that repoint lands** — the runtime pointer depends on it.

### cv-targeted-length-remediation-levers
Moved to GitHub: **#17** (the L1 lever reorder, part a) and **#12** (the summary-metric-repeat sub-question, part b).

### presentation-build-skill
Moved to GitHub **#44**, promoted to a skeleton build rather than waiting for an interview to demand one.

### level-axis-finer-grained-files
Moved to GitHub **#51**, and reframed. The original title presumed the fix was splitting into files; the diagnosis is that seniority is calibrated by research and then discarded at classification. Was decided-needed and back-burnered on time, so it is an enhancement, not a deferral.

### cv-format-spec-from-axes
**Status (2026-05-29):** Authored into `rules/cv/cv-structure.md`: two-band section order (with Affiliations conditional), Core Competencies counts (8-10 IC / 8-12 leadership), bullet length limits (2 target / 3 max / 4 never), page targets (IC 2-3, leadership ceiling 3), and the em-dash rule (tightened to no em dashes at all, superseding the header-separator allowance). `format_spec.md` stays .docx-rendering-only. The remaining step-c item (its dangling "section order set by archetype" pointer) moved to GitHub **#4**.

### tenure-as-years-rendering
Moved to GitHub **#20**.

### cv-render-uppercase-section-headers
Moved to GitHub **#19**.

### scaffolding-folder-layout
Moved to GitHub **#37** (both migration items folded into one issue).

### scaffolding-content-updates
Moved to GitHub **#37** (both migration items folded into one issue).

### tracker-integration
Moved to GitHub **#46**. Both this deferral and its paired decision (`tracker-integration-out-of-scope`) were one line each and referenced only each other; neither defined the action. #46 reconstructs it from what the repo and the tracker actually contain — confirm it matches intent before building.

### cv-structure-rules-for-pb-ps-aw
Moved to GitHub **#45**, promoted to a skeleton design rather than waiting on the first PB/PS/AW entry.

## Dropped (2026-07-16)

Reviewed and removed as noise, not work. Headings retained for inbound refs.

### session-log-parser-tests
**Dropped: fossil.** The tests were blocked on a "production session log parser." No such parser exists or is planned, because the design it belonged to was replaced. `scripts/session_log.py` is a section *writer* (`_replace_or_append_section`), and `phase_complete` entries, decision entries, and latest-wins semantics appear nowhere in `templates/session_log.md` or `scripts/`. The recorded frontmatter schema is five flat fields with no event-log structure. Replace-or-append makes latest-wins true by construction, so there is nothing to resolve, no parser, and no tests. Revive only if a real session-log *reader* is ever built (e.g. a cross-application analytics pass) — and then write tests against that reader's actual semantics, not this spec.

### staleness-threshold-revisit
**Dropped: collapsed into GitHub #47.** Re-evaluating the threshold and resolving its contradiction are the same act. The user confirmed 2026-07-16 that **9 months stands** — it was arrived at deliberately and is not to be re-opened. #47 covers alignment and wiring only.

### adr-formalization-timing
**Dropped 2026-07-16.** Converting `design_decisions.md` to numbered MADR files buys nothing here. The slugs already serve as stable IDs and read better than numbers (`retrieval-architecture-2026-05` versus `042`), and every cross-reference in the repo already uses them. The repo has twice rejected numeric prefixes on exactly this reasoning (`orientation-file-names`, `level-file-names`: "Drop numeric prefix... look up by descriptive name"). ADR numbering earns its keep on teams needing citation and supersession chains; supersession here is already handled by inline "Resolved YYYY-MM-DD by X" tombstones. If the file ever gets unwieldy, the useful split is by its existing section headings, which is different and cheaper work. `adr-naming` (the MADR convention decision) is retained in `design_decisions.md` as a dormant record.

### maintained-by-metadata-field
**Dropped 2026-07-16.** Extending the Document Metadata Header with `Maintained by:` would restate on every consumed doc what COMPONENTS.md already records (each component's outputs and update triggers), creating a sync obligation across dozens of files to buy a reverse lookup. The reverse-lookup argument is real but does not clear the cost on a repo with one maintainer. If revisited, file it *behind* #39 (the header/COMPONENTS reconciliation script) — the field without the drift check is the bad half of the pair.

### crisis-response-as-separate-work-state
**Dropped 2026-07-16.** Would subdivide a work-state that has never been exercised on either side: **0 inventory entries and 0 JD classifications** across 17 applications and 225 Work-state tags. The one candidate (BioMarin external-data quality, ~60% re-work rate) is chronic by the user's own description ("persistent and pervasive"), which `turnaround.md:14` defines as turnaround, not crisis. The deferral originated from that same line 14, which flags the absorption in passing — a note-to-self promoted to a tracked item. Revisit only with concrete justification. Note that the work-state tagging itself is under audit in GitHub #52, which may change the turnaround count.

## Resolved

Retained as tombstones; inbound refs depend on these headings.

### cv-targeted-reviewer-autonomy-reconciliation
**Resolved 2026-05-29** by `cv-targeted-name-and-structure-2026-05` and `cv-targeted-candidate-advocate-2026-05` (DACI stakeholder model). See those entries.

### cv-content-within-entry-layout
**Resolved 2026-05-29** by `cv-targeted-name-and-structure-2026-05`. See that entry.

### gap-analysis-schema
**Resolved 2026-05-27** by `gap-analysis-architecture-2026-05`. Full schema lives there.

### interview-prep-skill-build-notes
**Resolved 2026-07-02** by `preparation-interview-architecture-2026-07`: the `preparation-interview` skill was built (SKILL, the canonical `templates/interview_prep.md`, `rules/interview-types/` audience rule files, `scripts/interview_lifecycle.py`, `scripts/prep_interview_qc.py` + `qc-preparation-interview`), and `preparation-screen` was migrated onto the shared cumulative architecture. The design inputs in `design/interview_prep_skill_notes.md` are realized; the file was removed 2026-07-02 (working-files-deleted-after-apply pattern).

### why-i-left-specifics-for-interview-prep
**Resolved 2026-06-11.** The defense-layer specifics were captured from the user during the APP-008 phone-screen prep and, by the user's direction (superseding the 2026-05-25 "positioning stays diplomatic-only" choice), written into positioning.md's "Why I Chose to Leave BioMarin" section as "The layer beneath (when probed for specifics)" plus an Avoid guard. Prep skills consume it from positioning; the role-specific bridge stays per-application in interview_prep.md.

### cv-targeted-hybrid-retrieval
**Resolved 2026-05-26** by `retrieval-architecture-2026-05`. See that entry.

### axis-adjacency-weights-redefinition
**Resolved 2026-05-26** by `retrieval-architecture-2026-05` (exact axis match 1.0, adjacent 0.5; per-axis Adjacency may override). See that entry.
