# CV persuasion rebuild: plan

GitHub #88 (cv-targeted) and #89 (role-intake priority). Drafted 2026-11-09 from the APP-028 review.

## Context

APP-028 passed every check and reviewer, and the user rewrote it by hand. The draft copied entries one at a time, ranked bullets by number size, planned only what not to claim, and its reviewers rearranged facts inside that frame. Goal for every change below: a CV that persuades a reviewer to interview, with every claim accurate and citable.

## Locked decisions

**JD priority (#89, role-intake)**
1. Each requirement is labeled by kind (`rules/jd-requirement-kinds.md`); requirements are grouped into the functions the role delivers and ranked by the JD's statement of the role, repetition, then space spent. Boilerplate, role shape and administrative detail are not ranked and never reach retrieval or gap analysis. Derived needs are marked derived. The user confirms the ranking in role-classify.

**Writing rules (`rules/cv/cv-structure.md`)**
2. Summary: at most 5 sentences, plus a line cap reset from the measured Jazz summary. Each sentence maps one of the top JD needs to experience or achievement, rolled up, with no granular detail. Each claim keeps one thing specific to the candidate, not an echo of the JD.
3. Current work appears in the summary only when it maps to a JD need.
4. Bullet order within a role follows JD priority.
5. A requirement with qualifiers is answered by the closest exact match first, then broader transferable scope. Never claim the unmet qualifier; never drop a match because its wording differs from the JD's.
6. A summary roll-up is allowed when every area it names has at least one bullet behind it.
7. A generic phrase gives way to the JD's own phrase when the evidence supports it; a risk claim names the risk type the JD cares about.
    - 7a. Within-role subheadings name needs (N-NN), in rank order, marked `<!-- need: N-NN -->`, not single requirements (`cv-structure.md:171`, `cv_qc.py` C4, `cv_to_docx.py`); built with the need tags of decision 10 (user, 2026-11-12, replacement audit).
8. Relevance before size: a claim earns its place by the JD need it serves. The arc-composition ban (line 187) and the quantified-first preference are replaced by these rules.

**Architect (`cv-architect.md`)**
9. Remove "do not re-judge relevance"; the architect judges what each entry means for each need.
10. Two-stage draft: a long, persuasive draft with no length limit, each bullet tagged with its JD need (`<!-- need: N-NN -->`) beside its source citation; then a cut to length by need priority, lowest first.
11. The drafting plan records claims per need; limits become one column, not the plan.
    - 11a. Starting point (user, 2026-11-12, from his hand rewrite): the architect starts from the role statement's key items in `jd_needs.md` and, for each, picks the experience showing the candidate has done that core function in some capacity; specifics come second. Tools and methods the JD names are included when the candidate has them, and the closest ones the candidate has otherwise.

**Reviewers**
12. Inputs:
    - Hiring manager: draft, JD, company research. No `jd_needs.md`, profile, gap analysis or retrieval: like a real hiring manager it reads only the JD, which makes it an independent check on the ranking. Where its reading differs from the confirmed ranking, `jd_needs.md` wins by default and the difference goes to the user at handoff as a possible ranking error (user, 2026-11-12).
    - Career strategist: draft, JD, `jd_needs.md`, all five axis files, `cv-structure.md`, `cv-best-practices.md`, gap analysis.
    - Advocate: draft, JD, gap analysis CV Notes, and only the relevant parts of the profile: the per-need subset of entries, the Experience Entries of roles inside the `cv-structure.md` Professional Experience window, and Independent Projects. No full inventory or narratives, retrieval or research (user, 2026-11-12, Q1 architect workload).
13. Each answers its own goal-framed question with yes or "no, because"; none can return satisfied on a no.
    - Hiring manager: would you interview him from this CV? If not, what would change your mind? This makes it the judge of persuasion, on the long draft and in the final read of the cut CV (decision 15) (user, 2026-11-12, replacing "does the CV show what the role needs clearly enough to interview?", which read as a clarity test). Returns challenges as questions the architect answers from the profile.
    - Strategist: does the writing keep a reviewer reading and show the role's level?
    - Advocate: does each line carry the full weight of what happened? Profile entries are general descriptions of work, not text to preserve; the advocate judges whether the CV makes a persuasive case from his actual experience, never whether an entry's wording survived. The no-overstatement limit is unchanged (user, 2026-11-12).
14. All three may suggest wording. The domain bans on phrasing are removed.
15. A final read of the cut CV by the hiring manager and strategist can fail it.

**QC**
16. `qc-cv-targeted` sorts each claim: same work in other words (pass), roll-up (pass if backed), overstatement (fix), arguable (flag to the user at handoff, never rewritten down).
17. `cv_qc.py` adds a check: every need tagged in the summary appears on at least one bullet.
    - 17a. `cv_qc.py` adds a check: every inventory role inside the `cv-structure.md` Professional Experience window (ended within 10 years, or newer than any role kept there) appears in Professional Experience; a dropped role fails the run (user, 2026-11-12, Genmab: the draft dropped eClinical, opening a timeline gap readers do not close from Earlier Professional Roles). Built in steps 3 and 4 with the other `cv_qc.py` changes.

## Build sequence

Before step 3: work through `cv_rebuild_inventory.md` (architect workload first, then the conflicts, constraints and retire candidates).

Reordered 2026-11-09: test whether the writing changes fix the CV before touching reviewers. No change is tuned or judged on one application.

1. #89 ranker: rewrite its instructions as steps, run on Jazz, BeOne APP-027, Otsuka APP-026, Acadia APP-025; the user reviews once. Close enough is the bar, since the user confirms the ranking at intake.
2. Check decisions 2 to 8 (drawn from Jazz only) against the user's edits on Jazz (the reference: his edits there read the JD the way the ranker now does; it shows a principle but cannot confirm its own rules) and 5 others varied by orientation (Summit APP-023, WCT APP-022, Vertex APP-021, Faro APP-020, Genmab APP-018), excluding the test set. Each edit the user made is evidence; an edit recurring across CVs is stronger evidence. A place where an edit would apply but was not made is not evidence against it, since the user edited as time allowed, and the drafts were not good writing where left unedited. His edits depend on context (the JD, how his experience reads, neighboring bullets), so each pattern becomes a judgment principle stating its intent and when it applies, rarely a mechanical rule. The user confirms each principle one at a time.
3. `cv-structure.md` rule changes (decisions 2 to 8, as revised by step 2), plus the section split and retire cuts decided under Q1 in `cv_rebuild_inventory.md`.
4. `cv-architect.md` (9 to 11) and the `cv-targeted/SKILL.md` long draft and cut (10), in the shape decided under Q1 in `cv_rebuild_inventory.md` (read once, separate drafting steps, fresh revisers). Build #81 first: retrieval records which needs, and which requirements inside them, each entry fits, keeping topic-group neighbours together; the new writer steps read that subset.
5. `qc-cv-targeted.md` (16): test on combined claims from several applications. Accurate rewrites from sent CVs pass; deliberately overstated versions fail, seen to fail.
6. Rerun cv-targeted on the test set: Acadia APP-025, BeOne APP-027, Otsuka APP-026, Medtronic APP-024, from their existing research. First rerun retrieval (the per-need mapping, #81) and gap analysis for each, BeOne's role-classify Phase 2 before both: their `jd_needs.md` were re-extracted on 2026-11-11/12 in step 1, so the older gap analyses' CR numbers no longer match the current rows (checked 2026-11-12: no header matched in any of the four).
7. Only if step 6 shows the need: reviewer files and file sets (12 to 14), final read (15), `cv_qc.py` need-tag check (17).
8. Record the decisions in `design_decisions.md`, marking superseded the old reviewer rules (1523, 1644, 1646, 1659, 1749) whether or not step 7 ran; rewrite #88's body from this plan, including its Done when.

## Verification

- `python tests\run_tests.py` passes; any new check was first seen to fail.
- Accuracy check (step 5) passes accurate rewrites and fails overstated versions across several applications.
- Reruns (step 6), per application:
  - For each edit the user made to the sent CV, does the new draft already do what the edit did?
  - The user reads the new draft as a hiring manager would. Each combined claim is shown with its sources.
- The user edited every sent CV as time allowed, not as needed. Unedited text is no evidence either way, and edit counts are not a measure.

## Open, decided during the build

- Number of review rounds on the long draft (start with one, plus the final read).
- The summary line cap value, measured from the sent CVs.

## Out of scope

- The inventory Impact test (`rules/profile/inventory-writing.md:40`, #88 comment 3).
- Using finished CVs as voice examples (#88 fix 2) until the replay shows whether it is needed.
