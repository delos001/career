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
gap-detector reads retrieval.md plus every manifest-listed entry and narrative (via `gap_context.py` evidence files since 2026-10-27; ~60-80k tokens, once per application). Assessed 2026-07-14 and deliberately left alone: the manifest surfaces the entire corpus by design (broad recall so gap detection produces no false gaps; the axis floor cannot discriminate on this profile since nearly every entry is adjacent on at least one axis), so the only real read-reduction lever is making retrieval genuinely selective (semantic-score threshold), a recall-vs-cost design change, not an optimization.
- Trigger: inventory grows several-fold beyond ~220 entries (the arithmetic then favors a scoring threshold on gap-detector's reading set despite the recall risk).
- Blocks: nothing currently.
- Refs: `retrieval-architecture-2026-05`, `qc-mechanical-script-retrofit-2026-07`, memory `retrieval-token-cost`.

### axis-classification-slot-count-beyond-two
**Undecided: whether any change to slot count is needed at all.** The options below are what we would choose among *if* we decide yes; they are not a menu implying the need is established.

Axis classification records two values per axis (primary + secondary), and retrieval builds its deterministic axis-scoring signal from `{primary, secondary}` only - it reads the session log's `## Axis Classification` section, not `## Axis Gaps`. APP-007 (Senior Director, Data Intelligence; 2026-06-03) is the first observed role to legitimately span three values on one axis: specialty = operations-strategy + people-leadership + data-science. The third (data-science) was forced into `## Axis Gaps` and therefore excluded from the axis-scoring pass. Its underlying skills (Azure, Power BI, Databricks, advanced analytics) still surface via semantic scoring against the critical requirements, so the loss is only the deterministic axis exact-match/adjacency boost for data-science-tagged entries, not total exclusion. Hypothesis raised by the user 2026-06-03: seniority correlates with axis breadth (a leadership role can own strategy AND people AND hands-on craft simultaneously), so the fixed two-slot cap may systematically under-weight senior/leadership roles.

**Evidence as of 2026-07-16 (the `## Axis Gaps` section of all 17 session logs was read):** APP-007 remains the *only* role that has ever spanned three values on one axis. Ten applications have run since, several of them leadership (APP-008 VP-tier, APP-015 and APP-016 among them), and every one records "None". The hypothesis is **not supported to date**. Not refuted either — ten is a small sample and APP-007 was a Senior Director — but the direction of the evidence runs against it. Record any further recurrence here rather than re-deriving this.

**Second case, 2026-11-05: APP-028 (Jazz, Director, Clinical Data Analytics; leadership, tier function-lead).** The classifier reported five specialty values confirming by vocabulary (data-science, clinical-operations, people-leadership, operations-strategy, quality-compliance) and recorded data-science + people-leadership by JD weight. Unlike APP-007, nothing went into `## Axis Gaps` (it records "None"), because the classifier now resolves this by dominance, so the 2026-07-16 method of reading `## Axis Gaps` would not have found this case. `rules/specialties/data-science.md` names clinical-operations as the domain anchor for analytical work on clinical data, yet it is outside the two slots. Vocabulary overlap is a low bar for "spans", so five overstates the breadth. Effect on the retrieval or CV outcome is not yet known; APP-028 retrieval has not run.

Options at trigger: (a) allow N ordered values per axis instead of fixed primary/secondary; (b) add a third slot only where a role demonstrably spans three; (c) keep two and accept semantic scoring as the compensation. Change spans role-intake (axis-classifier output format + session log axis section), retrieval Phase 1 (the `{primary, secondary}` JSON construction) and `scripts/retrieval_apply.py` (axis signal computation), plus any downstream consumer reading the two-slot shape (gap-analysis, cv-targeted).
- Trigger: a second observed role spanning >2 values on any axis, OR evidence the lost axis weighting changed a retrieval/CV outcome, OR user direction.
- Blocks: nothing currently (semantic scoring partially compensates).
- Refs: `retrieval-architecture-2026-05`, `five-orthogonal-axes`, `dual-orientation-asymmetric-authority` (the primary/secondary asymmetry pattern), session log `wct_APP-007_2026-06` and its `## Axis Gaps`.

### ic-axis-finer-grained-files
**Undecided: whether splitting is needed at all.** Whether/when to split `ic.md` into junior-IC, mid-IC, senior-IC (Staff/Principal). 2026-04-29 research surfaced a meaningful gap between junior IC framing (project scope, hands-on verbs) and Staff/Principal framing (architecture-scale decisions, cross-team influence, influence without authority). Currently bridged within one file via voice/scope qualifiers ("differs in depth, independence, complexity, and breadth of technical influence"). Whether that bridge holds is the actual open question, and it has never been tested.

**The original trigger already half-fired and was never recorded (found 2026-07-16).** The trigger read "a Staff/Principal-flavored role application surfaces AND the unified file's framing fails to carry senior IC voice cleanly." APP-011 (Gilead, "AI Data Science Lead - Research", 2026-06-09) is that application: classified `ic` — "Lead/Staff-equivalent with no direct reports; mentors but does not manage" — and the only non-leadership application of 17. It scored 77.0% fit, zero unmet must-haves, Proceed. Outcome: `not-pursued` (2026-06-15), so the pipeline stopped at gap-analysis and cv-targeted never ran. The role arrived; the framing was never exercised.

A test CV for APP-011 was considered (GitHub #50) and declined 2026-11-05: building a CV for a role not pursued is not worth the run, so the question waits for a real IC application. Note also that this user's application pattern is leadership-heavy (16 of 17), so waiting for another IC application may wait forever; the need is product-general even where this user's flow does not test it.
- Trigger: **the next genuine IC application that gets a CV built** (judge then whether `ic.md` carries the role's voice). Restated 2026-11-05: the previous triggers were closed (#50, a test CV for the not-pursued APP-011; #35, the second-user test). APP-027 (2026-11) was classified IC but judged misleveled (should have been leadership), so it does not count. Applications run 21 leadership to 2 IC, and the 2026-11-05 level rule (judge by where the work lands) pushes borderline roles further toward leadership.
- Blocks: nothing currently.
- Refs: `level-axis-two-buckets`, GitHub #50 and #35 (closed), #51 (the leadership-side parallel, built 2026-11-05 as tiers).

### staleness-per-axis-overrides
**Undecided: whether per-axis overrides are needed at all.** Per-axis overrides on the 9-month staleness threshold — e.g. whether `pharma.md` should go stale faster than `ic.md` because regulatory guidance moves faster than what a Staff engineer is.

Distinct from staleness *detection*, which is a live bug in GitHub #47, not a deferral. The 9-month constant itself is decided and settled (`rule-staleness-threshold`, reconfirmed by the user 2026-07-16); do not re-open it.
- Trigger: **#47 is wired AND at least one refresh cycle has run.** Until staleness detection exists for axis files at all, no axis has ever been refreshed on a staleness signal, so the "evidence supports divergent drift rates" the original trigger asked for cannot exist. Replaced that non-trigger 2026-07-16.
- Blocks: nothing currently.
- Refs: `rule-staleness-threshold`, GitHub #47.

## Moved to GitHub (2026-07-16)

Citations of moved entries were repointed at their GitHub issues and the forwarding headings deleted (GitHub #55, 2026-11-05). The one kept below records where its content landed.

### cv-format-spec-from-axes
**Status (2026-05-29):** Authored into `rules/cv/cv-structure.md`: two-band section order (with Affiliations conditional), Core Competencies counts (8-10 IC / 8-12 leadership), bullet length limits (2 target / 3 max / 4 never), page targets (IC 2-3, leadership ceiling 3), and the em-dash rule (tightened to no em dashes at all, superseding the header-separator allowance). `format_spec.md` stays .docx-rendering-only. The remaining step-c item (its dangling "section order set by archetype" pointer) moved to GitHub **#4**.

## Dropped (2026-07-16)

Reviewed and removed as noise, not work. Headings retained for inbound refs.

### introduction-roster-ambiguous-skills
**Dropped 2026-11-05 (GitHub #6 audit): not undecided.** The `workflow-communication-conventions` heuristic (name conveys arc, brief; otherwise full) classifies each skill at build; cv_general, inventory and narratives are unbuilt. The interview family was resolved 2026-06 (preparation-screen, interview-notes, followup open conversationally with intake).

### cv-targeted-weighted-matching
**Dropped 2026-11-05 (GitHub #6 audit): fossil, the design it was written for was replaced.** It asked cv-targeted to weight axes by JD emphasis (industry-emphasis JD weights Industry higher, and so on). Matching then moved out of cv-targeted into the retrieval skill (`retrieval-architecture-2026-05`), where JD emphasis is carried by semantic scoring against the critical requirements, which are themselves extracted from the JD. The axis signal that remains (`retrieval_apply.py`: exact 1.0, adjacent 0.5, summed with equal axis weights) serves only as the single-axis inclusion floor and a tertiary sort, and it barely discriminates on this profile because nearly every entry is adjacent on at least one axis (`gap-detector-read-reduction`). Weighting it by emphasis would reorder a tie-break.

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

### cv-targeted-content-rules-from-axes
**Resolved 2026-11-05 (GitHub #6 audit).** Of the ten content rules stripped from the axis files, seven are built: CCAR with IC compression (`rules/cv/cv-structure.md`), impact types and fallback chain, Core Competencies zoning for data-analytics and platform-technology, the Selected Projects voice exception, adjacency translation, acronym expansion (all `cv-structure.md`), and achievement framing by orientation (each orientation file's Section emphasis). Three depended on tag queries that the design replaced: level filtering (retrieval includes on any single axis and never filters by level, `retrieval-architecture-2026-05`), compound Capability-tag queries (no Capability field exists, `competency-field-and-registry-removed-2026-05`), and the compound-query coverage flag (gap detection is the gap-analysis skill).

### role-evaluation-orientation-selection-from-axes
**Resolved 2026-11-05 (GitHub #6 audit).** Routing to another orientation, exclusion enforcement, and dual-orientation detection are built (each `rules/orientations/*.md` Identity section's "Do not select when... (use Y)"; `axis-classifier.md` selection/exclusion confirmation and primary/secondary). The IC-vs-leadership criteria split was not carried: orientation is classified independently of level (`five-orthogonal-axes`).

### builder-refresh-mechanics
**Resolved 2026-11-05 (GitHub #6 audit)** by `builder-refresh-qc-with-auto-fix-2026-05`: QC with auto-fix, no per-change approval gate, wholesale write via `axis_apply.py`. Create and refresh write paths are built in all five builders.

### cross-axis-composition-mechanism
**Resolved 2026-11-05 (GitHub #6 audit)** by `cv-content-agent-architecture-2026-05` and `cv-targeted-candidate-advocate-2026-05`: a single writer (cv-architect) reads and applies all five classified axis files, and the stakeholders are split by concern (hiring-manager, career-strategist, candidate-advocate), not by axis. No per-axis sub-agents and no cross-axis review rounds.

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
