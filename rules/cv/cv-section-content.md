---
last_researched: 2026-11
---

# CV Section Content - What Goes Into Each Section

**Used by:** cv-targeted.

**Purpose.** This file holds the rules for choosing which profile content goes into each CV section for this job, decided before any section is written. Which sections appear is in `cv-sections.md`; how the chosen content is worded is in `cv-writing.md`; section order, line layouts and length limits are in `cv-structure.md`.

**How to read this file.** A section headed `## KEY: name` applies to one drafting step; a section without a key applies to every step. A rule marked `(hard rule)` always applies; no reviewer suggestion overrides it.

## PLAN: Selection

The plan step decides what goes on the CV before any section is written. It works from `jd_needs.md`, which lists the job's requirements and groups them into ranked needs (N-01 is the highest), and from the profile entries retrieval found for each need.

**Read profile entries for what the candidate did.** A profile entry is a general description of work, not text to copy or to match word for word. For each entry, identify the core work done, function performed, goal reached or impact made, setting aside its contextual details. Then judge which needs that experience answers, considering whether its function, goal or impact is equivalent or transferable to what the job needs. Example: a JD asks for oversight of CROs; the candidate oversaw laboratory and imaging vendors. That oversight is a good substitute for what the JD asks, so the entry is chosen, and the bullet names the vendors the candidate actually oversaw, never CROs. Never choose an entry because its words match the JD, and never pass one over because they do not.

**Choose content one ranked need at a time.** Work through the ranked needs in `jd_needs.md`, highest first. For each need, decide which entries best show that the candidate has done that work, reached that goal or had that impact, and which role each claim sits under. The writer makes this judgment; retrieval scores only find entries and break ties between entries that serve a need equally well.

**Relevance decides, never the size of a figure.** Choose a claim for the need it serves. Never choose one claim over another because its figure (a percentage, count or amount) is larger.

**Cover every required requirement.** Every requirement marked required in `jd_needs.md` must be present in the CV, in whichever section fits it. One bullet or item may cover several of them.

**Strengths the JD does not ask for.** A strength or experience the JD does not specify gets a bullet only when an outcome in `jd_needs.md`, the level file and tier, or another axis file makes it persuasive for this job. When it does, the plan states the specific reason.

**Record the choices in `drafting_plan.md`.** For each need, list the claims chosen and cite the profile entries each claim draws on. For each role older than the Professional Experience window, record whether it is included because it closes a gap no newer role closes. For each role inside the window, record whether it gets bullets or a role summary. When a reviser could not work out a choice from its need and citations alone, record a one-line reason for it: for example, when a strength beyond the JD is included, an older role is included, or a lower-ranked need is kept over a higher one.

**Revisers keep the plan.** A later writer or reviser keeps each recorded choice unless a reviewer or QC finding challenges it.

**Draft long, then cut.** The first draft is deliberately longer than the CV can be. Its goal is a complete set of persuasive, relevant options for every need, so the later cut has good options to choose from. Tag every bullet with the need it serves (`<!-- need: N-NN -->`) beside its source citation. A later step cuts the draft to length under Length and cuts, below.

### Which roles appear in Professional Experience

A role belongs in Professional Experience when any of these hold:
1. It is active, or its end year is no earlier than the current year minus 10 (the window).
2. It is older, but it covers a requirement in `jd_needs.md` that no newer role covers.
3. It is newer than a role included under rule 2, so no gap opens between the two sections.

Every role inside the window appears there, except a role whose only entries are projects; never drop one. The plan step decides whether each role inside the window gets bullets or a role summary, and whether an older role qualifies under rule 2. A role kept only so the timeline has no gap gets the role summary. On a transformation-strategy or process-operations job, an earlier operational role's summary (for example, project management or clinical monitoring) shows the operational breadth the later work built on.

**Earlier Professional Roles.** Every role outside the window that does not qualify under rule 2 goes in Earlier Professional Roles.

**No unexplained gaps.** Across the two sections, account for every period of professional activity, and mark each concurrent role with the Allocation qualifier. A stated gap (for example, full-time study) is better than filling it with a role that does not belong.

**Project work never goes in Professional Experience (hard rule).** Work recorded only as project entries (`PR-NNN`) goes in Independent Projects, never as a role in Professional Experience, however recent. A role record with no employment entries (`EX-NNN`) and only project content is project work; a personal build between jobs is the usual case. The short gap this may leave in Professional Experience is better than presenting project work as a job (see No unexplained gaps). `cv_qc.py` fails a `PR-NNN` citation inside Professional Experience. Such a role appears in neither Professional Experience nor Earlier Professional Roles; its projects account for its period.

## SUM: Professional Summary

**What the summary covers.** Build each sentence from one key item of the role statement in `jd_needs.md`, or two closely related items. Every kind of work the summary names must appear in at least one bullet. Mention current work only where it maps to a job need.

**Figures in the summary (hard rule).** Besides the career span, the summary may carry at most 2 figures, and only when each directly shows a job requirement or a scale signal the level file names. A figure a bullet already carries is never repeated in the summary. Never add a figure to reach the limit.

**Career span.** State a span of years only when a job requirement asks for years of experience. Match that requirement's field and threshold: a requirement for "15+ years in clinical data management" gets "over 15 years in clinical data management," never the candidate's total career years. A long total span signals age, which lowers callbacks. The writer names the positions in that field, and a script computes their span from the dates in `inventory.md`; if the span falls short of the threshold, state no span. Never copy a span from a previous CV.

## COMP: Core Competencies

**What qualifies.** Include a capability only when it answers something the JD or `jd_needs.md` asks for. It may be an equivalent or transferable capability (a JD asking for leading a team of ten is answered by "functional and technical team leadership"). A capability shown only in the candidate's Independent Projects may appear when the job asks for it (e.g. "AI-driven USDM and regulation knowledge graphing"). A bare tool or keyword enumeration (e.g. `SQL, R, Python, SAS`) belongs in Technical Proficiencies. Never pad toward the ceiling.

**Groups.** Group the items so the reviewer sees at a glance which kinds of work the candidate covers for this job. Build the groups from the orientation file's Section emphasis. Keep a group only when the JD asks for capabilities that belong in it; never add an item to fill a group. Use a single unlabeled list when the items do not form at least 2 groups of 2 or more.

## EXP: Professional Experience

**Depth follows need rank.** The roles that serve the job's highest-ranked needs get the most depth.

**Within-role subheadings.** Use them only on a leadership CV, and only for a recent role with many bullets (roughly 8 or more) across distinct needs. Older and lighter roles stay flat.

**Subheading labels name needs (hard rule).** Each label names one ranked need in `jd_needs.md` that the role has cited evidence for, condensed from the need's wording (for example, `FSP and vendor oversight`). Never draw labels from the raw JD or from the profile.

**No forcing.** Never create a subheading the role cannot fill, and never stretch a bullet to fit one.

## PROJ: Independent Projects

**Bullets or one line.** A current project gets bullets when it serves a job need, or when an outcome in `jd_needs.md`, the level file and tier, or another axis file makes it persuasive for this job (see Strengths the JD does not ask for); any other current project gets one line with its name and dates.

## CRED: Credentials

**Education.** List every degree, except that an associate degree is omitted when a bachelor's degree is present.

**Certifications & Training.** List only items relevant to the job, most relevant first. If a higher level of the same certification is listed, omit the lower level (e.g., Lean Six Sigma Green Belt beside a Black Belt; CAPM beside a PMP). In-progress training is an early cut when space is short.

**Languages.** Programming languages belong in Technical Proficiencies, not Languages.

**Technical Proficiencies.** For a pure-leadership job the section may be brief.

## Length and cuts

**Content decides length.** Never add content to fill a page. Never cut persuasive content for a high-ranked need only to reach a lower page count. The page count follows from choosing the right content, within the page limits in `cv-structure.md`.

**Order of cuts.** Only whole lines shorten the CV, so every cut must remove at least one rendered line. When Word measures the CV over its page limit, cut in this order. First, reword bullets so they end a line sooner: 3-line bullets first, then 2-line bullets whose last line holds only a few words. Second, merge related bullets into one, in older roles first and then newer roles, where the level file supports merging. Third, drop in-progress training. If the CV is still over the limit, remove nothing more: hand it to the candidate with the measured overage and a list of cut candidates: the bullets serving the lowest-ranked needs first, older roles first on a tie, then one-line projects that serve no need. Every cut follows "Cutting words can create an overstatement" in `cv-writing.md`.
