---
last_researched: 2026-05
---

# CV Structure - Sections, Layout and Length

**Used by:** cv-targeted.

**Purpose.** The CV must persuade a reviewer to invite the candidate for an interview. Every rule in this file serves that purpose.

**How to read this file.** This file says which sections exist, their order, when each appears, their line layouts and the length limits; `cv-writing.md` says how content is chosen and written. A section headed `## KEY: name` applies to one drafting step; a section without a key applies to every step. A rule marked `(hard rule)` always applies; no reviewer suggestion overrides it.

## Section order - two bands

To persuade a reviewer of a candidate's qualifications and abilities, a CV opens with evidence that the candidate fits the job's needs (Evidence band) and closes with sections outlining the candidate's credentials (Credentials tail). Sections marked `(required)` always appear. Other sections appear only when they pass the tests in "Which sections appear." Technical Proficiencies, when present, is always last. Independent Projects, Publications and Presentations appear together after Earlier Professional Roles, in any order.

The block below is the single source for section order and required sections: `scripts/cv_qc.py` (S1, S2) reads it. Change the structure here, not in the script.

```
Evidence band:
- Professional Summary (required)
- Core Competencies (required)
- Professional Experience (required)
- Earlier Professional Roles
- Work output: Independent Projects, Publications, Presentations
Credentials tail:
- Education (required)
- Certifications & Training
- Professional Affiliations
- Languages
- Technical Proficiencies
```

Work-output sections sit in the evidence band, not the tail - a deliberate deviation from the academic-CV convention of tailing publications, because on a targeted industry CV these read as demonstrated work product, not credentials. A new work-output section is added to this list when the inventory gains a matching section.

## Which sections appear

Decide for each job; no section appears because it usually does. For each optional section below, include it only if all three tests hold. (1) Its inventory section has entries (not `Entries: None`). (2) The entries are relevant to this job. (3) The section more effectively persuades a reviewer to interview the candidate than whatever would be cut to make room for it. Record each decision in `drafting_plan.md`. Independent Projects is the exception to (2) and (3): when the inventory has a current project, the section appears (see Independent Projects).

```
Inventory section -> CV section
Employment & Role History -> Professional Experience, Earlier Professional Roles
Experience Entries -> Professional Experience
Independent & Volunteer Projects -> Independent Projects
Industry Exposure Profile -> none of its own; may supply terms to Core Competencies and the Summary
Technical Experience -> Technical Proficiencies
Education -> Education
Professional Training -> Certifications & Training
Professional Certifications -> Certifications & Training
Professional Affiliations -> Professional Affiliations
Publications -> not designed; no entries yet
Presentations -> not designed; no entries yet
Awards & Honors -> not designed; no entries yet
Languages -> Languages
```

A section marked not designed gets its rules when its first entry exists (`design/deferrals.md`, `cv-rules-for-empty-inventory-sections`).

## SUM: Professional Summary

**Length (hard rule).** At most 5 sentences and at most 6 lines in the rendered CV (8 for a leadership job). Never pad to reach either limit.

## COMP: Core Competencies

**Count.** At most 10 items. Each item is a concise capability phrase, not a sentence. A bare tool or keyword enumeration (e.g. `SQL, R, Python, SAS`) belongs in Technical Proficiencies, not crammed into a competency item.

**Format (ATS-safe).** Single column. Items separated by the pipe delimiter (`|`), or set as a simple single-level bulleted list. The pipe (or bullet) is the only item separator; commas are within-item punctuation only (a parenthetical enumeration such as `(CDASH, SDTM, CDISC LAB)` stays part of its one item). Do not separate items with commas. No multi-column layouts or tables - parsers read left-to-right and scramble columns.

**Groups.** Sort the items into 2 or 3 groups (zones) of related capabilities, each with a short label, so the reviewer sees at a glance which kinds of work the candidate covers for this job.

Build the groups from the orientation file's Section emphasis. Keep a group only when the JD asks for capabilities that belong in it; never add an item to fill a group. Use a single unlabeled list when the items do not form at least 2 groups of 2 or more.

## Professional Experience

Roles run newest first.

**Company line.** Each company is a `Company | Location | dates` line, company name in bold, followed by its roles. For a company with several roles, `dates` is the total span across them; for a single role, it is that role's dates. The hiring organization (the end client) is the company; a staffing agency appears as a role qualifier (Type, below).

**Role line and qualifiers.** Each role is `Title (dates) | Style | Type | Allocation`, title in bold. The `(dates)` appear only when the company has more than one role. Each qualifier appears only when the role differs from the default (on-site, direct hire, not concurrent, fully allocated), in this order:
- **Style:** `Remote` or `Hybrid`.
- **Type:** `Contract: <Agency>` (naming the staffing agency) or `Freelance`.
- **Allocation:** a concurrent role shows `Concurrent`, followed by its allocation when under 100% (`Concurrent 60%`). A role that is not concurrent shows `X%` only when under 100%.

Qualifier values come from the inventory's Employment & Role History records.

**Date format.** `Mon YYYY - Mon YYYY` (e.g. `Feb 2024 - Jan 2026`), or `Mon YYYY - Present` for an active role. Use the months in the role records; use the year alone only when a record has only a year. This applies to company lines, role lines and Earlier Professional Roles lines.

**Multiple roles at one company.** Give each role its own title line, dates, qualifiers and bullets, newest first, however few bullets a role carries. Never put two titles on one line, and never share one bullet list across roles: a shared list hides which work belongs to which role. The candidate combines titles by hand when wanted.

**Which roles appear here.** A role belongs in Professional Experience when any of these hold:
1. It is active, or its end year is no earlier than the current year minus 10 (the window).
2. It is older, but it covers a requirement in `jd_needs.md` that no newer role covers.
3. It is newer than a role included under rule 2, so no gap opens between the two sections.

Every role inside the window appears here, except a role whose only entries are projects (see Independent Projects); never drop one. The plan step decides whether each role inside the window gets bullets or a one-to-two-line summary, and whether an older role qualifies under rule 2 (see PLAN: Selection in `cv-writing.md`). A role kept only so the timeline has no gap gets the one-to-two-line summary. The summary is a single bullet under the role line and follows every bullet rule. On a transformation-strategy or process-operations job, an earlier operational role's summary (for example, project management or clinical monitoring) shows the operational breadth the later work built on.

**Earlier Professional Roles.** Every role outside the window that does not qualify under rule 2 goes in Earlier Professional Roles. Each role gets one `Company | Title | Dates` line, with no bullets or description. Give each role its own line, including several or concurrent roles at one company.

**No unexplained gaps.** Across the two sections, account for every period of professional activity, and mark each concurrent role with the Allocation qualifier. A stated gap (for example, full-time study) is better than filling it with a role that does not belong.

**Layout.** Bullets sit directly under the role line as one flat list. Individual contributor CVs always use this layout; leadership CVs may add subheadings under the conditions below.

**Bullets per role.** The long draft has no limit on bullets per role. In the cut CV, a recent role carries roughly 2 to 8 bullets, and an older role kept in Professional Experience may carry just one. A role given a one-to-two-line summary carries only that summary, in both drafts.

### Within-role subheadings (leadership only)

**When.** Only on a leadership CV, and only for a recent role with many bullets (roughly 8 or more) across distinct needs. Older and lighter roles stay flat.

**Labels name needs (hard rule).** Each subheading is a short label (a few words) naming one ranked need in `jd_needs.md` that the role has cited evidence for, condensed from the need's wording (for example, `FSP and vendor oversight`). Mark it `<!-- need: N-NN -->`. Order subheadings by need rank. Never draw labels from the raw JD or from the profile.

**Count.** At most 3 subheadings per role, each over at least 2 bullets. If fewer than 2 groups qualify, the role stays flat.

**No forcing.** Never create a subheading the role cannot fill, and never stretch a bullet to fit one. Bullets under a subheading follow every bullet rule.

**Subheadings stay below the role.** Format subheadings smaller than the role title; they organize bullets and never act as new sections.

## Independent Projects

Independent Projects holds the candidate's independent and volunteer project work (inventory Independent & Volunteer Projects, `PR-NNN`). Publications and Presentations, the other work-output sections, have no rules yet (see Which sections appear).

**When it appears.** The section appears whenever the inventory has a current project, one whose End Date is blank. A current project gets bullets when it serves a job need, or when an outcome in `jd_needs.md`, the level file and tier, or another axis file makes it persuasive for this job (see PLAN: Selection in `cv-writing.md`); any other current project gets one line with its name and dates. A project that is not current appears only when it passes the three tests in Which sections appear.

**Order and dates.** Each project shows its own Start Date and End Date from its inventory entry (a blank End Date shows as `Present`), in the date format used in Professional Experience. List projects newest first by Start Date.

**Project work never goes in Professional Experience (hard rule).** Work recorded only as project entries (`PR-NNN`) goes here, never as a role in Professional Experience, however recent. A role record with no employment entries (`EX-NNN`) and only project content is project work; a personal build between jobs is the usual case. The short gap this may leave in Professional Experience is better than presenting project work as a job (see No unexplained gaps). `cv_qc.py` fails a `PR-NNN` citation inside Professional Experience. Such a role appears in neither Professional Experience nor Earlier Professional Roles; its projects account for its period.

**Project header.** Each project opens with one header line, its name from the `Project:` field followed by its dates, in the format in `design/format_spec.md` (Project Entry Structure). Blocks that share a project sit under one header. A one-line project is that header alone, with no bullets.

## CRED: Header and credentials

### Header (name and contact)

The CV opens with the candidate name, then the contact block on up to two centered lines:
- Line 1: location | email | phone.
- Line 2 (when profile links exist): the profile links, each shown as its bare domain and path (strip the scheme, any `www.`, and any trailing slash) with no platform label, since the domain identifies it (e.g. `linkedin.com/in/...`, `github.com/...`).

Keep links on their own second line, not appended to line 1 (long URLs wrap mid-link). The full URLs live in `user-info.md`; the header shows the compact form.

### Credentials tail

Order is set in "Section order."

**Education.** Degree, discipline, institution, year. No GPA or honors (per inventory schema). List every degree, with the exception that if a bachelor's degree is present, an associate degree is omitted.

**Certifications & Training.** Certifications, each with issuer, year earned and status (Active or Inactive), and training. List only items relevant to the job, most relevant first. If a higher level of the same certification is listed, omit the lower level (e.g., Lean Six Sigma Green Belt beside a Black Belt; CAPM beside a PMP). In-progress training is an early cut when space is short. Each item is one short line, not an achievement bullet.

**Professional Affiliations.** Include only for board, governance, or senior-leadership jobs where the JD mentions memberships, board seats, or committee roles; omit otherwise. Affiliation, role (Member through Board / Officer / Committee Chair), and whether it is current; one short line each, drawn from the inventory's Professional Affiliations section.

**Languages.** Spoken languages with proficiency, one short line each. Include when the job names a language or works across regions where one matters; omit a candidate's native language alone. Programming languages belong in Technical Proficiencies.

**Technical Proficiencies.** Tools, platforms, languages, and methods listed in the inventory's Technical Experience section, named in the JD's terms so applicant tracking systems match them. Group into short labeled clusters (e.g. Languages, Platforms, Methods) where that aids scanning. For pure-leadership jobs the section may be brief or omitted when the JD does not ask for technical tools.

## Length

**Page limits.** An individual contributor CV aims for 2 pages and may run to 3 for a long, relevant history. A leadership CV aims for 2 to 3 pages and never exceeds 3.

**Content decides length.** Never add content to fill a page. Never cut persuasive content for a high-ranked need only to reach a lower page count. The page count follows from choosing the right content, within the page limits.

**Length is measured in Word.** At QC, the skill renders a draft .docx and asks Word for the page count (`scripts/cv_measure.py`). Only a measured overage sends the CV back to be cut, by the number of lines Word measured. If Word is unavailable, the length is reported as unmeasured and nothing is cut. The character-count estimate below is an early warning only and never triggers a cut; it has run 4 to 9 lines short of the Word measurement.

**Order of cuts.** Only whole lines shorten the CV, so every cut must remove at least one rendered line. When Word measures the CV over its page limit, cut in this order. First, reword bullets so they end a line sooner: 3-line bullets first, then 2-line bullets whose last line holds only a few words. Second, merge related bullets into one, in older roles first and then newer roles, where the level file supports merging. Third, drop in-progress training. If the CV is still over the limit, remove nothing more: hand it to the candidate with the measured overage and a list of cut candidates: the bullets serving the lowest-ranked needs first, older roles first on a tie, then one-line projects that serve no need. Every cut follows "Cutting words can create an overstatement" in `cv-writing.md`.

**Estimate settings.** The early-warning estimate uses these numbers, set for the CV layout (US Letter, 0.75-inch margins, 0.5-inch header and footer, Calibri 11pt body). `cv_qc.py` holds them, and a test fails if the two lines below differ from it. Citation comments are removed before any length check, so they add no length.
- Usable lines per page: ~47 (page 1, with the name and contact block) / ~50 (later pages).
- Characters per line at wrap: ~100 full-width; bullets ~95 (bullets sit at a 0.25-inch indent).
- A unit's estimated lines are its characters divided by the line capacity, rounded up. The Word measurement always overrides the estimate.

## Scope boundary

This file owns CV sections, order, line layouts and length only. It does not own, and does not restate:

- **How content is chosen and written** - `cv-writing.md`: claims and citation, selection, summary and Core Competencies content, bullet rules, and the writing rules.
- **Relevance scoring, retrieval, and coverage** - the retrieval skill scores entries and exposes manifest signals; gap-analysis assigns per-requirement coverage. `cv-writing.md` uses those scores to find entries and break ties (see PLAN: Selection).
- **Adjacency weights** - set by the retrieval manifest and the axis files' Adjacency sections. `cv-writing.md` owns only how adjacent vs non-adjacent experience is worded (see Transferable experience).
- **Axis voice and vocabulary** - level voice and verb vocabulary, orientation summary-lead and section-emphasis, and industry/specialty terminology come from the five axis files and compose with this structure.
- **Critical-requirements extraction** - produced by role-classify in `jd_needs.md` (as text and Demand, grouped under ranked needs; a requirement's row number is its `CR-NNN` id). This file consumes them; it does not derive them.
- **Visual rendering** - styling, fonts, and the visual rendering of Earlier Professional Roles belong to cv-render (docx); the page count is measured by this skill in Word (see Length is measured in Word). The single handoff is cv_content.md. (The Earlier Professional Roles inclusion threshold and content density are owned by this file, above; only their visual rendering is deferred.)
- **No-fabrication, failure handling, partial-content discipline** - `global-rules.md`.
- **Skill procedure** - the Drafter/reviewer/QC loop, orchestration, and citation mechanics live in the cv-targeted SKILL.md and its agents, not in this rule file.
