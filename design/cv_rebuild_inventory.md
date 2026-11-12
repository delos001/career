# CV rebuild: whole-picture inventory

Companion to `cv_persuasion_plan.md`. Written 2026-11-12 so the next session starts from one place. Why the rebuild exists (the user's words): the CVs were not persuasive; the writing was guided by excluding what was not correct instead of including the persuasive experience that gets an interview. Persuasion stays the top test (`cv_edit_principles.md`).

## How each kind is treated (user, 2026-11-12)

- **Conflicts:** the old rules were not optimized for persuasion, so a legacy rule is a target to improve, especially where it conflicts with a principle or the plan.
- **Constraints:** keep them, but group them into retrievable sections the writer reads just in time, or split the architect into pre-architect steps, or another method. Decided under Q1 below.
- **Retire:** anything obsolete, that fails the objectives or hinders them, is cleaned out, so it stops costing context.
- Walk all of it so nothing is lost.

## Q1, decide first: the architect's workload

The user's concern: the architect reads a lot (JD, jd_needs, five axis files, research, writing rules, gap analysis, retrieval, inventory, more), much of it long prose, then must write prose that is both accurate and persuasive, not copied inventory entries, as a good start for the reviewers. That may be too much for one agent's context and attention.

Why first: the answer decides the shape of step 3 (how `cv-structure.md` is split) and step 4 (one architect or several steps).

Next session:
1. Measure, do not guess: list every file the architect reads in a real run (`cv-targeted/SKILL.md`, `cv-architect.md`, `scripts/dispatch_prompt.py`) with its line and token count. Jazz APP-028 is the reference run.
2. Then weigh options against that evidence, e.g. sections read just in time; a pre-architect step that turns the inputs into a short per-need brief; a separate drafting step per section; cutting retire candidates.

## Then: the 8 decisions the conflicts reduce to

One at a time, each verified against its file first (the lists below are an agent's report, not yet verified line by line).

1. Summary: orientation file sets the summary lead (design_decisions 77) vs principle 1 (role statement). Also secondary-orientation quotas (56).
2. Impact-first, numbers-first, CCAR (`cv-structure.md`, `cv-best-practices.md` 19/51/52/56, design_decisions 1601, deferrals 98) vs principle 2 and plan decision 8.
3. The 3-line bullet allowance (design_decisions 1611, deferrals 66, `cv-structure.md` 161) vs principle 14.
4. Per-row guarantee (design_decisions 1517, 1526) vs per-need selection and cuts.
5. Advocate pushes beyond the JD (design_decisions 1714, 1720) vs principle 3.
6. Upstream scores vs writer judgment for relevance and Earlier Roles (design_decisions 344) vs plan decision 9.
7. Selected Projects to Independent Projects (design_decisions 351, 1736; `format_spec.md` 139/145; `cv-best-practices.md` 38; `cv_qc.py`; renderer; the fenced section-order block).
8. Old reviewer design (what/how split 1646, comprehension-only 1749, 3 rounds 1644, QC never checks coverage 1659, success criterion lacks persuasion 1677, reviewer inputs 1523) vs plan decisions 12 to 17. Belongs to step 7, except 1677.

Also: summary figures and length in `cv-best-practices.md` 62/63; tenure option 68 (already not adopted). The strategist reads that file, so each departure is marked there.

## Then: step 3 edits

Edit 0 (purpose statement at the top of `cv-structure.md`) is approved in principle. The 13 planned edits: summary content (69), summary length (73-75), Core Competencies (87), relevance and selection (105-112), bullets per role and order (129-131), bullet construction (148-157), bullet length (161), arc composition (181-199), Independent Projects rename, Education and certifications (219-221), clarity example (236, "make decisions in the meeting"), JD term, "led", no critical contrasts (253), compress order (268). Line numbers are from 2026-11-12; re-read before editing.

## Open GitHub issues that bear on this

#88 (parent; body rewritten at step 8), #9 (hand-edit diff; done by step 2), #81 (requirement-grouped evidence), #82 (positioning.md as CV input), #74 and #75 (post-retrieval inventory entries), #31 (cv-general), #87 (skill redundancy).

## Agent findings (2026-11-12, unverified)

### Conflicts

- design/design_decisions.md:56: "CV: secondary in 2-3 achievements and 1-2 Core Competencies items. Summary primary-only." Requires the secondary orientation to get a fixed number of slots and to stay out of the summary. Conflicts with principle 1 and plan decision 2, where summary sentences come from role-statement items whatever their orientation, and with principle 3, where content is chosen per need rather than by orientation quota.
- design/design_decisions.md:77: "**Orientation** → Section structure, Section emphasis, Summary lead framing." Requires the orientation file to set how the summary leads. Conflicts with principle 1 and plan decision 2, which build the summary from the role statement. Note that cv_edit_principles.md:5 says axis files win.
- design/design_decisions.md:1601: "It owns ... summary structure, the CCAR bullet structure, impact-type preference order, acronym-expansion rule". Requires cv-structure.md to keep CCAR and an impact-type preference order. Conflicts with principle 2 (each bullet opens with the function or the impact, judged per bullet) and plan decision 8 (quantified-first preference replaced).
- design/design_decisions.md:1611: "the same discipline as the bullet line-limits (2 lines target, 3 max)". Requires a 3-line maximum per bullet. Conflicts with principle 14, which leaves open whether the 3-line allowance survives.
- deferrals.md:66: "bullet length limits (2 target / 3 max / 4 never)". Same 3-line allowance as above. Conflicts with principle 14 (open for step 3).
- design/design_decisions.md:1633: "Drafting plan: chosen orientation/level framing, page-budget allocation per section, and the entries held back for a bad signal". Requires the drafting plan to be built around page budgets. Conflicts with plan decision 11 (the plan records claims per need; limits become one column).
- design/design_decisions.md:1644: "Repeat 2-3 until both reviewers return no material findings (converged) or a review-round cap of 3 is hit." Requires up to 3 review rounds with persistent advisors. Conflicts with the plan's open item "start with one, plus the final read" and with plan decision 15 (final read of the cut CV).
- design/design_decisions.md:1646: "the hiring manager owns *what* ... the career-dev expert owns *how* it is expressed ... coverage / employer-relevance (hiring manager) outranks craft preference (career-dev)". Requires reviewers split into what and how, with that split used to settle conflicts. Conflicts with plan decisions 13 and 14 (each reviewer answers its own goal question; all three may suggest wording).
- design/design_decisions.md:1659: "Out of QC scope ... requirement coverage / fit (hiring-manager reviewer)". Requires that QC never check coverage. Conflicts with plan decisions 17 and 17a (cv_qc.py checks that summary needs have bullets and that no role is dropped).
- design/design_decisions.md:1677: "fully traceable ..., within the page ceiling ..., role-tailored per the axes and structure file, and passes QC". Requires a success criterion that never mentions persuasion. Conflicts with the plan Context goal ("a CV that persuades a reviewer to interview") and cv_edit_principles.md:3.
- design/design_decisions.md:1714: "push genuinely differentiating achievements even beyond the literal JD requirements". Line 1720 adds "The advocate is not requirement-bound." Requires the advocate to push content that serves no JD need. Conflicts with principle 3 ("Cut bullets that serve no need, even strong ones") and plan decision 8 (a claim earns its place by the need it serves).
- design/design_decisions.md:1749: "the hiring-manager may raise comprehension only". Requires the hiring-manager to stay out of wording. Conflicts with plan decision 14 (all three may suggest wording). The clarity rule itself is covered by principles 6 and 14.
- design/design_decisions.md:344: "determined by the retrieval / gap-analysis relevance signal ... not by a fresh subjective judgment in the CV skill". Requires the Earlier-Roles split and role relatedness to come from upstream signals. Conflicts with plan decision 9 (the architect judges what each entry means for each need) and adds to 17a.
- design/design_decisions.md:1517: "each required core row is guaranteed a cited CV entry (`cv-structure.md` rule 1)". Line 1526 adds "required core rows each keep one cited entry before any row gets a second". Gap analysis's must-meet logic rests on this row-level guarantee. Conflicts with principle 3 and plan decision 10, which select and cut by need rank rather than by row.
- design/design_decisions.md:1523: "hiring-manager (raw JD only for extraction misses), career-strategist (reads `jd_needs.md`)". Requires both reviewers to read jd_needs.md. Plan decision 12's input lists say only "JD", so this is a possible conflict.
- design/design_decisions.md:351: "Independent / self-directed project work goes in the **Selected Projects** work-output section". The rule is enforced by cv_qc.py C6 (line 355). Requires the section name Selected Projects. Conflicts with principle 12 ("Independent Projects"). Placement after Professional Experience is consistent.
- design/design_decisions.md:1736: "Bulleted sections: ... and Selected Projects description lines". Requires the renderer's force-bullet rule to key on the Selected Projects name. Conflicts with principle 12.
- design/format_spec.md:139: "Used for entries in the "Selected Projects" CV section." Line 145 gives the example "Personal Project | 2025–Present". Requires the Selected Projects name and a year-only date example. Conflicts with principle 12 (name, true date range) and the Faro accuracy specimen ("2026" to "Mar 2026").
- deferrals.md:98: "impact types and fallback chain ... (all `cv-structure.md`)". Requires an impact-type preference and fallback chain in cv-structure.md. Conflicts with principle 2 and plan decision 8.
- rules/cv/cv-best-practices.md:19: "impact-first quantified bullets". Requires bullets to lead with a quantified impact. Conflicts with principle 2 (opening judged per bullet) and plan decision 8.
- rules/cv/cv-best-practices.md:51: "Lead with the impact you delivered + numerically measure what you accomplished + detail what you did." Requires every bullet to lead with impact. Conflicts with principle 2.
- rules/cv/cv-best-practices.md:52: "Quantify wherever possible." Line 90 adds "Emphasize quantified outcomes over task lists". Requires numbers by default. Conflicts with plan decision 8 (relevance before size) and principle 14 (detail the claim does not need is cut).
- rules/cv/cv-best-practices.md:56: "lead the bullet with the OUTCOME (impact-first) ... the rendered bullet is result-first". Requires every rendered bullet to open with the result. Conflicts with principle 2.
- rules/cv/cv-best-practices.md:62: "strategic scope and leadership scale (team size, budget, P&L ...) ... and 1-2 quantified signature achievements". Requires figures and achievements in the summary. Conflicts with principle 1 and plan decision 2, and with design_decisions.md:1704 (no figures; that departure is already recorded).
- rules/cv/cv-best-practices.md:63: "Proposed 3-4 sentences sits squarely inside the consensus band and is a reasonable default." Requires a 3-4 sentence summary default. Conflicts with plan decision 2 (at most 5 sentences, with a line cap).
- rules/cv/cv-best-practices.md:38: ""Selected Projects" ... may be redundant with Experience for pure leadership resumes". Requires a lean toward omitting projects on leadership CVs. Conflicts with principle 12 (WCT, a leadership CV, uses Independent Projects).
- rules/cv/cv-best-practices.md:68: "a "years of tenure" rendering option is an evidence-based design feature". Recommends a tenure-as-years option. Conflicts with design_decisions.md:1698 (not adopted), not with a principle.

### Constraints to carry forward

- design/design_decisions.md:57: "Existing CV dual-orientation rule transfers to `rules/orientations/cv_dual_orientation_composition.md`." Requires a home file for the dual-orientation CV rule. That file does not exist (rules/orientations/ holds only the 4 value files plus registry.md), so the rule lives only at line 56.
- design/design_decisions.md:73: "cv-targeted passes it [Tier] to cv-architect and career-strategist". Requires the writer and strategist to apply the leadership tier from leadership.md. The principles name the level file, not the tier.
- design/design_decisions.md:85: "a single writer applies all five axis files ... The default precedence above is applied by `cv-architect.md` (Rules)." Requires the architect rewrite to keep the per-axis surface map and precedence (lines 76-83).
- design/design_decisions.md:1422: "the cv-architect applies the per-value rule files at bullet-composition time". Requires entry-level Level, Orientation and Work-state framing per the axis files.
- design/design_decisions.md:309: "`cv-architect` holds such entries back while choosing content and records each in `drafting_plan.md`; the `hiring-manager` persona checks each draft for them". Requires the bad-signal hold-back, which is not in the principles or plan. Plan decision 12 gives the hiring-manager no profile.
- design/de_emphasize_removal_plan.md:18: "Industry rule files keep their "Hiring-panel de-emphasis" lines: a different concept (framings panels weigh low), untouched." Requires the writer to honor the industry files' de-emphasis framings.
- design/design_decisions.md:1621: "Owns adjacency translation (transferable-experience content)." Requires the architect to keep translating adjacent-axis experience.
- design/design_decisions.md:1627: "Only the Drafter edits text. Reviewers and QC return findings; the Drafter applies them." Requires the single-writer rule. Plan decision 14 allows wording suggestions only.
- design/design_decisions.md:1646: "(1) hard constraints (traceability/no-fabrication, page ceiling, structure-file invariants) beat both reviewers ... The Drafter logs each non-trivial arbitration call in the drafting plan ... No mid-loop user escalation". Requires hard-constraint precedence, an arbitration log and no escalation mid-loop.
- design/design_decisions.md:1653: "acronym-expansion-on-first-use where determinable, bullet line-count limits, summary line cap; structure (section order + two-band placement ...); internal consistency (dates / tenure coherent ...)". Requires the mechanical checks the rewritten rules must still feed.
- design/design_decisions.md:1657: "capped at 3; bounded-loop failure ships provisional with findings surfaced". Requires the QC loop cap and provisional ship.
- design/design_decisions.md:1666: "The drafting plan is an internal working file (not handed downstream), retained for audit and resume". Requires the drafting plan to persist for resume and audit.
- design/design_decisions.md:1603: "Evidence band (top): Professional Summary -> Core Competencies -> Professional Experience -> relevance-gated work-output sections. Credentials tail: ...". Requires the two-band section order.
- design/design_decisions.md:1605: "Relevance-gated, not existence-gated ... Pure leadership roles default to omit unless a project demonstrably evidences a role requirement." Requires a rule for when the projects section is included. Principle 12 says nothing on this.
- design/design_decisions.md:1607: "Leadership: target 2-3 pp, hard ceiling 3 pp ... never pad to fill, never drop genuinely high-relevance content to hit a lower count." Requires the page ceiling that the plan decision 10 cut aims at.
- design/design_decisions.md:1789: "`cv-structure.md:480` already sets a 3-page hard ceiling for leadership". Line 1790 adds "CV appendix ... rejected" and line 1791 "4-page tier ... rejected". Requires the 3-page ceiling with no appendix or 4-page escape.
- design/design_decisions.md:1685: "thematic subheadings only on recent, accomplishment-heavy senior/leadership roles ... capped 3-6); IC always flat". Requires a gate and cap on subheadings. Plan 7a changes the label source only.
- design/design_decisions.md:1769: "Within-role subheadings are short theme labels (a few words), not the full requirement sentence". Requires short subheading labels under plan 7a.
- design/design_decisions.md:1687: "one sentence per bullet; no em dashes ...; no AI-tell phrasing". Line 1773 adds an allowlist for "pivotal <study/trial/Phase/program>". Requires these hard rules, which are not in the principles.
- design/design_decisions.md:1688: "**Affiliations:** conditional, relevance-gated credentials-tail member". Requires Affiliations to be gated on relevance.
- design/design_decisions.md:1695: "CV section order and the required-section set live once, in the fenced block under `## Section order` in `rules/cv/cv-structure.md`; `cv_qc.py` S1/S2 parse it". Requires the fenced block to be kept. A principle-12 rename must happen there.
- design/design_decisions.md:1698: "Role headers keep date ranges; no tenure-as-years option ... career-strategist no longer proposes it." Requires date ranges in role headers.
- design/design_decisions.md:1701: "Trim levers in order: compress by elevation, then drop as a last resort ... the writer keeps no page estimate of its own ... `trim_candidates` ... A test holds the numbers in `cv-structure.md` to the `cv_qc.py` constants." Requires length to be measured in Word and the writer to keep no estimate. The rewrite must keep cv-structure numbers in sync with cv_qc.py constants (a test checks this).
- design/design_decisions.md:1756: "the architect does not self-measure geometry or create scratch/helper files (it has no execution tool)". Constrains how the plan decision 10 long draft is cut.
- design/design_decisions.md:1757: "the architect flags any QC fix that reverses a prior stakeholder contribution (`qc_regressions` return field)". Requires the architect to disclose QC reversals at handoff.
- design/design_decisions.md:1761: "`retrieval.md` gains an **Employer** column ... so the architect places bullets under the right company". Line 1709 adds "C5 now matches each bullet's cited entry (its Role tag) against the RL Title". Requires merged claims (principle 3) to sit under the role their entries belong to.
- design/design_decisions.md:1774: "bare tool enumerations belong in Technical Proficiencies". Requires tool lists to stay out of Core Competencies (relevant to principle 10). The pipe-only count rule (S3) is on the same line.
- design/design_decisions.md:1523: "Kept as is: Core Competencies zoning by orientation, presence gates on optional CV sections". The same line says the cv-architect thesis and the cv-structure.md summary and arc trigger come from "the role statement, lead-or-do line and need rank". Requires zoning to stay and the lead-or-do line to feed the thesis. The plan never names the lead-or-do line.
- design/design_decisions.md:1518: "leading work is not managing people, and the answer never lifts a need". Requires the writer not to read the lead-or-do line as people management.
- design/design_decisions.md:1521: "The CV writer treats each outcome as a theme met by evidence from any function." Requires the CV to use the jd_needs.md Outcomes line. The plan does not cover it; open_questions.md:7 records it as resolved here.
- design/design_decisions.md:1563: "consumed by the cv-architect as a standing constraint before drafting". Requires the architect to honor the gap-analysis CV Notes. Plan decision 12 routes them only to the advocate.
- design/design_decisions.md:1860: "A fact not yet in the inventory is cited as `GAP CR-NNN`. `cv_qc.py` C9 requires the requirement to be `closed` or `partial-match`". Requires this citation form for staged facts.
- design/design_decisions.md:840: "A project appears as its objective, framed for the role, with relevant elements folded in; never one bullet per element. A line citing an element must also cite its objective". Requires this PR composition and citation rule under Independent Projects. The plan at pr_schema_plan.md:55 adds "Outcome as impact source".
- design/design_decisions.md:360: "a company block whose bullets precede any bold title line fails". Requires every role to keep its title line, including older roles cut to one or two lines (principle 7).
- design/design_decisions.md:418: "cv_targeted / role_evaluation consume it secondarily for bullet-framing depth via inventory linkage. Narratives are not a primary CV retrieval anchor." Requires narratives to be used as framing depth only.
- design/design_decisions.md:606: "cv-architect's Education-block read for the CV tail". Requires the architect to read Education, including Coursework, from ED entries (relevant to principle 8).
- design/design_decisions.md:1879: "Description now uses an umbrella term, and the CV writer picks the granularity." Line 1881 adds "a leadership entry never reads as hands-on skill". Requires tool granularity to be set by the writer and hands-on claims only from Hands-on Tools. Interacts with plan decision 11a's tools clause.
- design/design_decisions.md:1311: "derived facts about the candidate (career span, counts, scope) are computed from `inventory.md` at run time, never stored." Requires the career span to be computed at run time (WCT specimen).
- design/design_decisions.md:1310: "Before recording a new rule, name the file that executes it". Requires each rewritten principle to name its executor.
- design/design_decisions.md:1307: "A QC check written to accept both the correct format and a drifted one has stopped checking." Bears on moving C4 from cr to need markers (plan 7a): C4 should not accept both.
- design/design_decisions.md:1723: "an explicit **overreach / credibility** function in the hiring-manager, distinct from QC". Line 1721 adds "an advocate push the hiring-manager flags as overstated yields". Requires the hiring-manager credibility check. Plan decision 13's question does not include it.
- design/cv_targeted_audit.md:12: "Added `suspected_extraction_misses[]` channel to hiring-manager return". Requires the extraction-miss channel to survive the plan decision 13 return format.
- design/cv_targeted_audit.md:17: "added the section to cv-architect.md composition step + output contract (plain Company\|Title\|Dates lines, no citation needed)". Requires the Earlier Professional Roles output contract.
- deferrals.md:17-18: "Undecided: how Publications, Presentations, and Awards & Honors render on a CV." Requires the rewrite not to decide this; the trigger is the first entry in any of those sections.
- deferrals.md:36: "Effect on the retrieval or CV outcome is not yet known". Line 39 sets the trigger: "evidence the lost axis weighting changed a retrieval/CV outcome". Requires watching the step 6 reruns for this.
- deferrals.md:49: "Trigger: **the next genuine IC application that gets a CV built** (judge then whether `ic.md` carries the role's voice)." Bears on principle 3's IC-depth branch, which is untested.
- design/jd_needs_ranker_redesign.md:50: "Rerun role-classify Phase 2 before BeOne goes to retrieval." Requires this before BeOne APP-027 can join the plan step 6 test set.
- rules/cv/cv-best-practices.md:13: "Cascade any changed rule into `rules/cv/cv-structure.md` ..., noting deliberate departures (as its no-figures summary rule does)." Requires the rewrite to record its departures from this file (principle 2, plan decision 8).
- rules/cv/cv-best-practices.md:7: "**Used by:** cv-targeted (career-strategist grounding)". The strategist reads this file (plan decision 12), so its conflicting guidance reaches a reviewer unless departures are marked.

### Already covered

- design/design_decisions.md:1629: "every bullet, summary claim, and competency carries the inventory entry ID (EX/PR/RL) it derives from". Per-unit citation. Covered by plan decision 10 and principle 3 (a merged claim cites every entry).
- design/design_decisions.md:346: "Level-elevation language ... valid only when the inventory entry itself supports the elevated framing". No elevation beyond the source. Covered by plan decision 16, principle 3 and the accuracy specimens (Vertex).
- design/design_decisions.md:1655: "does each cited inventory entry actually support its claim text (semantic traceability; no fabrication, no overstatement beyond source)". QC judges support. Covered and refined by plan decision 16.
- design/design_decisions.md:1704: "The Professional Summary carries no figures except the career span ... Enforced by `cv_qc.py` S4". Covered by principle 1 and plan decision 2. S4 stays.
- design/design_decisions.md:1707: "every role at a multi-role employer gets its own title, dates, bullets and qualifiers ... the generator never stacks titles". Covered by principle 9.
- design/design_decisions.md:1542: "the CV cites the transferable experience without overclaiming". Partial matches. Covered by plan decision 5.
- design/design_decisions.md:1623: "are the JD's critical requirements visibly addressed, would this earn an interview". The hiring-manager's goal. Covered by plan decision 13.
- design/design_decisions.md:1505: "The CV agents (cv-architect, hiring-manager) read `jd_needs.md` directly." Covered by plan decision 11a.
- design/design_decisions.md:1755: "the stakeholder loop exits the moment all three return `satisfied`". Early convergence. Covered by plan decision 13 (no satisfied on a no).
- design/design_decisions.md:1909: "A check is only finished once it has been seen to fail." Covered by the plan Verification section.
- design/build_issues.md:25: "additional levers (per-role minimum-bullet rule, Earlier-Roles compression, Selected-Projects gating) need attention". Lines 9 and 17 add "trim ... from the lowest-relevance older-role bullets". Covered by principles 7 and 9.
- design/de_emphasize_removal_plan.md:8: "35% of CV citations come from outside the gap-analysis evidence. The CV writer chooses beyond the evidence". Covered by plan decision 9.
- rules/cv/cv-best-practices.md:46: "using the job description's exact terminology ... Matching the posting's job title". Covered by principle 5. Line 85, "not term dumping", is also covered by principle 5 ("if and only if it accurately describes").
- rules/cv/cv-best-practices.md:47: "design the top third for a fast skim AND provide depth". Line 84 adds "reorders the most relevant experience into the high-attention top third". Covered by principles 1, 4 and 9.
- rules/cv/cv-best-practices.md:53: "Accomplishment-framed bullets beat responsibility/duty-framed bullets". Covered by principle 2: the function is shown as done, not listed as a duty.
- rules/cv/cv-best-practices.md:76: "3 pages only when justified and trimmed of early-career detail". Covered by principle 9.
- plan "Open, decided during the build" (cv_persuasion_plan.md:72) and design_decisions.md:1611 "the summary carries a line cap". The summary line cap value. Covered by plan decision 2 and that open item.

### Retire candidates

- design/design_decisions.md:325-336 (arc-composition-for-high-impact-roles): "narratives (ST-NNN entries with Linked Inventory fields) are the primary composition unit when a role's scope requires arc-level proof points". Requires arc-first composition through narratives. Superseded by plan decision 8 (arc ban replaced) and principle 3 (merge across entries). Its gap-analysis arc-first use (line 332, line 1544) is a separate consumer.
- design/design_decisions.md:1686: "synthesis into one higher-level bullet ..., only via a backing narrative (ST-NNN); ad-hoc re-assembly of atomic entries disallowed (fabrication risk)." Superseded by plan decision 8 and principle 3.
- design/design_decisions.md:1609: "default 3-4 sentences; IC 2-4; leadership up to ~6 when scope genuinely requires". Summary length. Superseded by plan decision 2 (at most 5).
- design/design_decisions.md:1622: "Reviews writing craft and best practice (impact-first quantified bullets, CCAR ...). Owns gap framing (employment-history gaps via tenure-as-years ...)". The old strategist mandate. Superseded by plan decisions 8 and 13; tenure-as-years was already dropped at line 1698.
- design/design_decisions.md:1720: "Three-way domain fence (no overlap) ... Reciprocal fences added to all three agent files." The phrasing fences. Superseded by plan decision 14 (domain bans on phrasing removed).
- design/design_decisions.md:1758: "coverage-before-duplication, then semantic > axis-exact > axis-adj > recency, with a protected differentiator ... must-have + preferred only; contextual + duty-derived are ride-along". The selection tie-break. Superseded by plan decisions 8 and 10. Its Type vocabulary was already replaced by Demand (line 1515), and line 1526 marks this selection rule interim.
- design/design_decisions.md:1685: "labels sourced from critical requirements (CR-NNN ...)". Subheading label source. Superseded by plan decision 7a (needs N-NN).
- design/design_decisions.md:1741: "`### subheading` + `<!-- cr: CR-NNN -->`". The render and QC input grammar. Superseded by plan decision 7a (`<!-- need: N-NN -->`), which needs changes to cv_qc.py C4 and cv_to_docx.py.
- design/design_decisions.md:1451: "CV creation: `must-have` requirements receive explicit CV bullets; `preferred` and `duty-derived` widen the matching surface; `contextual` informs framing/voice rather than bullets." Already marked superseded in-line by role-intake-ranked-needs-2026-11. It is retired only if cv-structure.md still carries it.
