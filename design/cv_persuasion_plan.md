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
8. Relevance before size: a claim earns its place by the JD need it serves. The arc-composition ban (line 187) and the quantified-first preference are replaced by these rules.

**Architect (`cv-architect.md`)**
9. Remove "do not re-judge relevance"; the architect judges what each entry means for each need.
10. Two-stage draft: a long, persuasive draft with no length limit, each bullet tagged with its JD need (`<!-- need: N-NN -->`) beside its source citation; then a cut to length by need priority, lowest first.
11. The drafting plan records claims per need; limits become one column, not the plan.

**Reviewers**
12. Inputs:
    - Hiring manager: draft, JD, company research. No profile, gap analysis or retrieval.
    - Career strategist: draft, JD, all five axis files, `cv-structure.md`, `cv-best-practices.md`, gap analysis.
    - Advocate: draft, JD, inventory, narratives, gap analysis CV Notes. No retrieval or research.
13. Each answers its own goal-framed question with yes or "no, because"; none can return satisfied on a no.
    - Hiring manager: does the CV show what the role needs clearly enough to interview? Returns challenges as questions the architect answers from the profile.
    - Strategist: does the writing keep a reviewer reading and show the role's level?
    - Advocate: does each line carry the full weight of what happened?
14. All three may suggest wording. The domain bans on phrasing are removed.
15. A final read of the cut CV by the hiring manager and strategist can fail it.

**QC**
16. `qc-cv-targeted` sorts each claim: same work in other words (pass), roll-up (pass if backed), overstatement (fix), arguable (flag to the user at handoff, never rewritten down).
17. `cv_qc.py` adds a check: every need tagged in the summary appears on at least one bullet.

## Build sequence

Reordered 2026-11-09: test whether the writing changes fix the CV before touching reviewers. No change is tuned or judged on one application.

1. #89 ranker: rewrite its instructions as steps, run on Jazz, BeOne APP-027, Otsuka APP-026, Acadia APP-025; the user reviews once. Close enough is the bar, since the user confirms the ranking at intake.
2. Check decisions 2 to 8 (drawn from Jazz only) against the user's edits on about 5 other applications, varied by role type and level, excluding Jazz and the test set. Recurring edits confirm, change or add a rule. The user reviews each pattern one at a time.
3. `cv-structure.md` rule changes (decisions 2 to 8, as revised by step 2).
4. `cv-architect.md` (9 to 11) and the `cv-targeted/SKILL.md` long draft and cut (10).
5. `qc-cv-targeted.md` (16): test on combined claims from several applications. Accurate rewrites from sent CVs pass; deliberately overstated versions fail, seen to fail.
6. Rerun cv-targeted on the test set: Acadia APP-025, BeOne APP-027, Otsuka APP-026, Medtronic APP-024, from their existing research, retrieval and gap analysis.
7. Only if step 6 shows the need: reviewer files and file sets (12 to 14), final read (15), `cv_qc.py` need-tag check (17).
8. Record the decisions in `design_decisions.md`; rewrite #88's body from this plan, including its Done when.

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
