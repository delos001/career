---
last_researched: 2026-05
---

# CV Structure - Content and Layout Rules

**Used by:** cv-targeted.

**Purpose.** The CV must persuade a reviewer to invite the candidate for an interview. Every rule in this file serves that purpose.

**Claims.** Every claim cites the profile entries that support it. A claim may reword or combine entries. A combined claim must cite each individual entry it draws on. No claim may state more than its entries show (`global-rules.md`).

**How to read this file.** A section headed `## KEY: name` applies to one drafting step; a section without a key applies to every step. The five axis files are used to align the CV's prose with the job's orientation, industry, specialty, level and work state. A rule marked `(hard rule)` always applies; no reviewer suggestion overrides it.

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

Decide for each job; no section appears because it usually does. For each optional section below, include it only if all three tests hold. (1) Its inventory section has entries (not `Entries: None`). (2) The entries are relevant to this job. (3) The section more effectively persuades a reviewer to interview the candidate than whatever would be cut to make room for it. Record each decision in `drafting_plan.md`. Independent Projects is the exception to (2) and (3): when the inventory has a current project, the section appears (see PROJ).

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

The summary is the first thing a reviewer reads. In a few seconds it must persuade the reviewer that the candidate has done the core work this job exists to do, so the reviewer keeps reading.

**Content.** Build each sentence from one key item of the role statement in `jd_needs.md`, or two closely related items. State that the candidate has done that work, summarized across roles, and anchor it in a detail particular to the candidate's experience (a domain, setting, result or impact), so the sentence does not merely restate the JD. Detailed results, and descriptions of methods, tools or individual projects, belong in the bullets; the summary states the work at a high level. Every kind of work the summary names must appear in at least one bullet. Mention current work only where it maps to a job need.

**Figures in the summary (hard rule).** Besides the career span, the summary may carry at most 2 figures, and only when each directly shows a job requirement or a scale signal the level file names. Pair each figure with words that give its scope ("30-person global study team"). Every other figure stays in its bullet. Never add a figure to reach the limit.

**Length (hard rule).** At most 5 sentences and at most 6 lines in the rendered CV (8 for a leadership job). Never pad to reach either limit.

**Career span.** State a span of years only when a job requirement asks for years of experience. Match that requirement's field and threshold: a requirement for "15+ years in clinical data management" gets "over 15 years in clinical data management," never the candidate's total career years. A long total span signals age, which lowers callbacks; show breadth in words instead ("global and multi-regional study teams"). The writer names the positions in that field, and a script computes their span from the dates in `inventory.md`; if the span falls short of the threshold, state no span. Never copy a span from a previous CV.

## COMP: Core Competencies

Core Competencies persuades a reviewer, at a glance, that the candidate has the capabilities this job asks for. Each item is a short phrase naming one capability, in the JD's terms where they accurately describe the candidate's capability. A capability shown only in the candidate's Independent Projects may appear when the job asks for it (e.g. "AI-driven USDM and regulation knowledge graphing").

**Count.** At most 10 items. Each item is a concise capability phrase, not a sentence. Include a capability only when it answers something the JD or `jd_needs.md` asks for. It may be an equivalent or transferable capability (a JD asking for leading a team of ten is answered by "functional and technical team leadership"). Never pad toward the ceiling. A bare tool or keyword enumeration (e.g. `SQL, R, Python, SAS`) belongs in Technical Proficiencies, not crammed into a competency item.

**Format (ATS-safe).** Single column. Items separated by the pipe delimiter (`|`), or set as a simple single-level bulleted list. The pipe (or bullet) is the only item separator; commas are within-item punctuation only (a parenthetical enumeration such as `(CDASH, SDTM, CDISC LAB)` stays part of its one item). Do not separate items with commas. No multi-column layouts or tables - parsers read left-to-right and scramble columns.

**Groups.** Sort the items into 2 or 3 groups (zones) of related capabilities, each with a short label, so the reviewer sees at a glance which kinds of work the candidate covers for this job.

Build the groups from the orientation file's Section emphasis. Keep a group only when the JD asks for capabilities that belong in it; never add an item to fill a group. Use a single unlabeled list when the items do not form at least 2 groups of 2 or more.

## PLAN: Selection

The plan step decides what goes on the CV before any section is written. It works from `jd_needs.md`, which lists the job's requirements and groups them into ranked needs (N-01 is the highest), and from the profile entries retrieval found for each need.

**Read profile entries for what the candidate did.** A profile entry is a general description of work, not text to copy or to match word for word. For each entry, identify the core work done, function performed, goal reached or impact made, setting aside its contextual details. Then judge which needs that experience answers, considering whether its function, goal or impact is equivalent or transferable to what the job needs. Example: a JD asks for oversight of CROs; the candidate oversaw laboratory and imaging vendors. That oversight is a good substitute for what the JD asks, so the entry is chosen, and the bullet names the vendors the candidate actually oversaw, never CROs. Never choose an entry because its words match the JD, and never pass one over because they do not.

**Choose content one ranked need at a time.** Work through the ranked needs in `jd_needs.md`, highest first. For each need, decide which entries best show that the candidate has done that work, reached that goal or had that impact, and which role each claim sits under. The writer makes this judgment; retrieval scores only find entries and break ties between entries that serve a need equally well.

**Relevance decides, never the size of a figure.** Choose a claim for the need it serves. Never choose one claim over another because its figure (a percentage, count or amount) is larger.

**Cover every required requirement.** Every requirement marked required in `jd_needs.md` must be present in the CV, in whichever section fits it. One bullet or item may cover several of them.

**Strengths the JD does not ask for.** A strength or experience the JD does not specify gets a bullet only when an outcome in `jd_needs.md`, the level file and tier, or another axis file makes it persuasive for this job. When it does, the plan states the specific reason.

**Record the choices in `drafting_plan.md`.** For each need, list the claims chosen and cite the profile entries each claim draws on. For each role older than the Professional Experience window, record whether it is included because it closes a gap no newer role closes. For each role inside the window, record whether it gets bullets or a one-to-two-line summary. When a reviser could not work out a choice from its need and citations alone, record a one-line reason for it: for example, when a strength beyond the JD is included, an older role is included, or a lower-ranked need is kept over a higher one.

**Revisers keep the plan.** A later writer or reviser keeps each recorded choice unless a reviewer or QC finding challenges it.

**Draft long, then cut.** The first draft is deliberately longer than the CV can be. Its goal is a complete set of persuasive, relevant options for every need, so the later cut has good options to choose from. Tag every bullet with the need it serves (`<!-- need: N-NN -->`) beside its source citation. A later step cuts the draft to length under the length rules, starting with the lowest-ranked need.

## Professional Experience

The core evidence section. Reverse-chronological. Each role earns its space by relevance to the target; depth concentrates on the roles that matter most for this application.

**Adjacency translation (transferable experience).** Entries whose axis value is adjacent to the target (per the axis file's Adjacency section; adjacency weight ~0.5 in the manifest) are translated, not dropped: reworded toward the target value's language while the underlying facts stay intact. Entries whose axis value is non-adjacent are surfaced for their cross-cutting capability only (e.g. leadership, capability building, driving process), not claimed as target-domain experience. Cross-cutting themes that are not domain-bound transfer regardless of axis distance. Translation rewords; it never fabricates a domain, metric, or scope the source entry does not support.

**Entry header.** Each company is a `Company | Location | dates` line (company name bold), followed by its role(s). `dates` on the company line is the total span across the company's roles (multi-role) or that single role's dates (single-role). The hiring organization (the end client) is the company; a staffing agency is shown as a role qualifier (Type, below), not as the company.

**Role line and qualifiers.** Each role is `Title (dates) | Style | Type | Allocation`. `Title` is bold. The `(dates)` parenthetical appears only when the company has more than one role (a single-role company carries the dates on the company line, so the role line omits them to avoid duplication). The qualifiers follow in this fixed order, and each appears only when it deviates from the standard role (Direct, On-site, non-concurrent, fully allocated):
- **Style** (default On-site, hidden): `Remote` or `Hybrid`.
- **Type** (default Direct, hidden): `Contract: <Agency>` (naming the staffing agency) or `Freelance`.
- **Allocation** (default 100%, hidden): when allocation is under 100%, `Concurrent X%` if the role is concurrent, otherwise `X%`. A concurrent role at 100% allocation shows nothing.

The qualifier values (Type, Style, Concurrent, Allocation, Agency) come from the inventory's Employment & Role History records.

**Date format.** Month and year: `Mon YYYY - Mon YYYY` (e.g. `Feb 2024 - Jan 2026`), `Mon YYYY - Present` for an active role. Pull months from the role records; fall back to year-only when a record carries only a year. Applies to the company-line span, the role-line `(dates)`, and the `Company | Title | Dates` lines in Earlier Professional Roles. Do not collapse to year-only when the source carries months.

**Default entry layout: flat.** Bullets sit directly under the role title as a single-level list. This is the default for every role and the only layout at IC level. (Senior/leadership roles may add thematic subheadings under defined conditions - see Within-role thematic subheadings.)

**Bullets per role, by relevance and recency.** The most recent, most relevant roles carry the most bullets; older or less-relevant roles compress. Roughly 2-8 bullets per role as a norm; a heavy recent senior role may run higher.

**Ordering.** Lead each role with its strongest, most role-relevant bullet (impact-first), not the role's chronological first task. The top of each entry is high-attention space.

**Multiple roles at one company.** When a candidate held more than one role at the same company, never merge the titles onto one header line (no `Title A; Title B`). Order the roles reverse-chronologically. In Professional Experience, never stack: give each role its own title, dates, bullets, and qualifiers (no hoisting, even when a qualifier repeats across the roles), however few bullets a role carries. A shared bullet list hides which accomplishment belongs to which role, and the user stacks by hand when wanted (stacking is easy to do by hand; unstacking is not).

**Earlier Professional Roles.** CV experience uses two sections: Professional Experience and Earlier Professional Roles. A role belongs in **Professional Experience** when any of these hold:
1. It is currently active or ended within the last 10 years (threshold: current year minus 10).
2. It is older but directly closes a critical-requirement gap that would otherwise be unaddressed.
3. It is newer than any rule-2 inclusion, so no perceived gap opens between the two sections.

A within-threshold role kept only to prevent a perceived timeline gap (not for content) earns a 1-2 line scope summary, not detailed bullets. Whether an older role "closes a gap" (rule 2) and whether a role is content-relevant versus timeline-only come from the retrieval / gap-analysis relevance signal (the upstream-signal principle above), not a fresh judgment here. For transformation-strategy or process-operations applications, operational roles (e.g. project management, clinical monitoring) that predate the transformation work stay in Professional Experience when within threshold; their summary reflects operational breadth, establishing the foundation the transformation arc builds on, rather than matching a JD cluster.

**Earlier Professional Roles** holds every role outside the threshold that does not meet rule 2. Format: Company | Title | Dates only; no bullets, no descriptions. List each role on its own line; do not merge multiple or concurrent roles at the same company onto a single line. The section sits immediately after Professional Experience.

**Gap-prevention principle.** Account for every period of professional activity across the two sections; note concurrent roles as concurrent. A documented gap (e.g. full-time study) is preferable to filling it with a role that does not belong.

### Bullet rules

**Bullet construction: CCAR, rendered impact-first.** The underlying model is Challenge - Context - Action - Result. On the page the bullet leads with the result/impact, then the action and (briefly) the context; full narration is reserved for interviews, not the bullet. IC bullets compress Challenge and Context into a single clause or imply them, foregrounding action and result. Leadership bullets carry all four components, because scope and stakes (the challenge and context) are part of what the bullet must establish.

**Accomplishment-framed, not duty-framed.** Every bullet states what was achieved, not what the role was responsible for. "Responsible for X" and duty-list phrasing are not acceptable bullet forms.

**Impact-type preference order.** Lead with the strongest impact type available for the claim, in this order:
1. Type 1 - quantified (a number: %, $, time, count, scale).
2. Type 2 - bounded qualitative (a concrete, verifiable outcome without a clean number: "eliminated rework," "passed inspection with no findings").
3. Type 3 - contextual narrative (significance or effect described in context).

Fallback chain when quantitative data is absent: quantified -> bounded qualitative -> contextual narrative -> proxy metric (scale/scope affected) -> scope as signal (team size, budget, breadth) as a last resort. Never fabricate a number to satisfy Type 1.

**One sentence per bullet (hard rule).** Each bullet is exactly one sentence. Multi-sentence bullets are not permitted. CCAR components render as clauses within that single sentence, never as separate sentences. If a bullet contains two distinct accomplishments, split it into two bullets; if it is one accomplishment written as two sentences, condense it to one.

**Bullet length (hard rule).** Target 2 lines; 3 lines acceptable only for a highest-value, genuinely complex achievement; 4+ lines never. A bullet over the limit is condensed (tighter wording), or split when it bundles distinct accomplishments - never left to run long. Line count is the ceiling; the one-sentence rule and the line limit are applied at draft time and enforced mechanically by QC (both are deterministically checkable).

### Within-role thematic subheadings (senior/leadership only)

An optional device to group a heavy role's bullets under thematic subheadings. Use sparingly and only where it earns its space; the default remains flat.

**Level gate.** Senior/leadership roles only. IC CVs never use subheadings (flat only, per Default entry layout).

**Per-role condition.** Apply only to a recent, accomplishment-heavy role - one carrying enough bullets (roughly 8+ across distinct themes) that a flat list would be hard to skim. Lighter and older roles stay flat even on a leadership CV. Typically only the one or two most recent senior roles qualify.

**Labels come from the critical-requirements artifact, not the raw JD (hard rule).** Each subheading is a short descriptive phrase (a few words, not a sentence) naming the theme of one critical requirement (CR-NNN) produced by role-classify in `jd_needs.md` and carried through gap-analysis - the processed JD. Condense the requirement's vetted wording into a compact label in the Core Competencies label style (e.g. CR-015 "...FSP resource allocation and strategic vendor partnerships..." becomes `FSP and vendor oversight`); never reproduce the full requirement sentence - it wastes scarce vertical space and reads as over-specific. The Drafter never re-parses the raw JD, and labels are never drawn from the candidate's narratives or inventory. The `<!-- cr: CR-NNN -->` marker carries the requirement id. Restrict labels to requirements this role has cited evidence for (per the retrieval manifest and gap-analysis coverage), so a subheading both mirrors a real JD priority and is genuinely backed by the role.

**Cap.** 3-6 subheadings per role. Fewer than 3 distinct JD-aligned themes -> stay flat (subheadings add clutter, not signal). More than 6 -> the role is over-segmented; consolidate.

**No forcing.** A subheading appears only when the role has genuine, cited evidence for that JD theme. Never create a JD-themed subheading the role cannot fill, and never stretch a bullet to fit a theme.

**Bullets under a subheading** follow all standard bullet rules: flat single-level, impact-first, one sentence each, within the line limit, each citing its inventory entry ID.

**ATS.** Keep subheadings visually subordinate to the role title (the standard section headings carry the parse); subheadings are an organizational aid, not new top-level sections.

### Arc composition (senior / enterprise-scope roles)

For roles whose target requires enterprise or cross-functional program-scope proof points, a list of atomic bullets undersells collective impact (the panel reads ten process improvements, not one transformation). Arc composition synthesizes related atomic entries into a single higher-level achievement bullet. Governed by `arc-composition-for-high-impact-roles`; reconciled here to flat layout.

**Trigger.** The role statement in `jd_needs.md` is at enterprise or cross-functional program scope ("led enterprise initiative," "built and scaled a capability"), and gap-analysis surfaced the relevant strength at arc level. Senior/leadership context. Otherwise compose atomic bullets normally.

**Composition unit: narratives (ST-NNN).** A narrative's required Linked Inventory field defines which atomic EX/PR entries form the arc and supplies the arc claim. The Drafter reads that authored grouping; it does not re-derive which entries combine. Synthesis without a backing narrative is not permitted - ad-hoc re-assembly of atomic entries is the fabrication-risk path and is disallowed.

**Output: one synthesized bullet (not nested).** The arc renders as a single higher-level bullet that subsumes its linked entries - one sentence, within the line limit, impact-first. The atomic entries are compressed into the claim, not listed beneath it (flat layout; no sub-bullets). Citation is the union of the linked source ids (e.g. `<!-- src: EX-12, EX-15, EX-23 -->`), optionally also the ST-NNN.

**Facts not yet in the inventory.** A fact the user surfaced in this application's gap analysis, still waiting in staging, is cited by its requirement: `<!-- src: GAP CR-005 -->`. Allowed only for a `closed` or `partial-match` requirement; the claim may not exceed that requirement's Notes.

**No overstatement.** The synthesized claim must not assert scope, scale, or impact beyond the union of its cited entries. QC verifies the arc bullet against its cited slices.

**Same role/company only.** An arc bullet composes only from entries within the role/company it sits under. A narrative arc that spans employers is a career-level theme: it informs the Professional Summary and positioning, not a single experience bullet.

**Relationship to subheadings.** Orthogonal. A synthesized arc bullet may sit under a JD-sourced subheading or in a flat list; the arc determines bullet content, never the heading.

**Default is atomic.** Synthesize only when a narrative arc exists and collective impact genuinely exceeds the sum of granular bullets. Do not over-synthesize - concrete, quantified atomic achievements that carry their own weight stay as their own bullets.

## Work-output sections (Selected Projects / Publications / Research)

One relevance-gated section class in the evidence band, demonstrating work product beyond the role history. Members: Selected Projects, Publications, Research (extensible to Patents, Presentations). Each renders only when it earns its space.

**Relevance-gated, not existence-gated.** Include a member section only when its entries add signal for the target role (per the retrieval manifest and gap-analysis), not merely because such entries exist in the inventory. This supersedes the legacy "include whenever project entries exist" rule. Pure leadership roles default to omitting Selected Projects unless a specific project demonstrably evidences a JD requirement.

**Independent / self-directed project work belongs here, not in Professional Experience (hard rule).** Self-employment or independent activity whose accomplishments are recorded only as independent-project entries (inventory Independent & Volunteer Projects, `PR-NNN`) is represented as Selected Projects entries in this work-output section, placed after Professional Experience, never as a role at the top of Professional Experience, regardless of recency. A role record carrying no employment (`EX-NNN`) accomplishments and only `PR-NNN` project content is project work, not an experience role; a between-roles personal build is the canonical case. Inclusion stays relevance-gated (above); this rule governs placement once included. The short Professional Experience gap this may leave is preferred to elevating off-experience project work above the role history (see the Gap-prevention principle under Professional Experience). `cv_qc.py` enforces this mechanically (a `PR-NNN` citation inside Professional Experience fails QC).

**Placement.** Evidence band, not the credentials tail (rationale under Section order). Most defensible for senior-scientist / regulated-IC profiles.

**Project voice exception.** Project entries follow design/build voice (what was designed, built, analyzed, delivered), not the organizational leadership framing used in Professional Experience. Leadership voice rules apply to Professional Experience entries only; a project is described as work product regardless of the CV's level framing.

**Standard rules still apply.** Entries are impact-first, one sentence per bullet, within the line limit, and each cites its inventory entry id (PR-NNN, or the relevant id for publications/research). A project appears as its objective, framed for the role, with the relevant elements folded in, never one bullet per element. A bullet using an element cites it with its objective (`PR-015, PR-015.03`), and an element's Outcome is the source for its impact.

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
## Cross-cutting writing rules

Apply across every section.

**Reads clearly on the first pass (hard rule).** The CV exists to win an interview, so every summary sentence and bullet must be a complete, natural sentence that a hiring manager who has never seen the source understands on one read, and that shows why the work mattered. A sentence that only makes sense to someone who already knows the work fails, however accurate it is. When a clear sentence will not fit, drop a fact, a list item, or a whole bullet; never drop the words that make it read clearly. This outranks adding coverage, keywords, or one more fact.

- Fails: "Delivered dashboards that study teams used to decide in meetings and centralized data surveillance with real-time findings, and drove self-service analytics adoption."
- Passes: "Replaced weekly spreadsheet reporting with near-real-time dashboards, so study teams could make decisions in the meeting instead of waiting on follow-up."

**Impact-first.** Lead with the outcome/result wherever a claim has one, in bullets and in the summary. The high-attention position carries the strongest signal.

**Acronym expansion.** Spell out a less-common acronym on first use, with the acronym in parentheses; use the acronym thereafter. Common in-industry acronyms the hiring panel reads fluently (e.g. FDA, GCP, ICH, IRB, GxP in pharma) need no expansion. Judge "common" by the target industry, not the general reader.

**No em dashes (hard rule).** Em dashes do not appear in the CV. Use a pipe (|) or hyphen for header separators (Company | Location | Dates), and rewrite prose and bullets with periods, semicolons, or natural connectives instead of em-dash clause breaks.

**No AI-tell phrasing (hard rule).** The CV must not read as machine-written. (Source: Wikipedia, "Signs of AI writing.") Avoid:
- Negation-contrast framing: "not just X, but Y," "it's not X, it's Y," "less about X and more about Y." State the point directly.
- Rule-of-three padding: do not force a third item (adjective, adjective, adjective; phrase, phrase, and phrase) for rhythm. List only what is real.
- Trailing significance clauses: the appended "-ing" flourish ("..., driving efficiency," "..., streamlining operations") that asserts vague impact. Replace with a quantified result (per impact-type order) or cut it.
- Buzzword/puffery used as filler: leverage, robust, seamless, pivotal, crucial, foster, underscore, showcase, groundbreaking, world-class, cutting-edge, transformative (and "spearhead" except where level-appropriate). Prefer the level axis file's verb vocabulary and concrete language.
- Marketing copulas: "serves as," "stands as," "is designed to" in place of plain "is/was" or an action verb.
- Vague intensifiers standing in for a number: significantly, greatly, successfully, substantially. Quantify if the impact is real; otherwise state it plainly.
- Title Case headings and decorative boldface: labels use the defined heading style, not Title Case On Every Word.

**Plain, verifiable language (hard rule).** No keyword-stuffing, no verbs inflated beyond the level's voice (governed by the level axis file), no duty-list phrasing. Tailoring means genuine relevance and terminology alignment, not term dumping. Never substitute a job-description buzzword for an accurate term to manufacture a keyword match or stretch a claim: when a plainer, more accurate word describes the experience, use the accurate word. Every term must map to what the candidate actually did, without overstatement.

**Achievement single-home (hard rule).** Each distinct achievement - a specific quantified result or named accomplishment (e.g. "200+ data transfers without headcount growth," "interim-analysis rework from ~60% to 0%," "selected Databricks as the enterprise platform") - has ONE home in Professional Experience: a single bullet, under the role that owns it. It is not restated as a second bullet under the same or another role. The Professional Summary may name the impact of a signature achievement in rolled-up words (the outcome and why it matters), but never its figure, which stays in the owning bullet (per the no-figures summary rule). Core Competencies are capability phrases only; a competency item never restates a metric or accomplishment carried by the summary or a bullet. The same number/metric surfacing in two places is redundancy.

**Protect the lead role.** The most recent senior role is the highest-attention block; each of its bullets must carry a distinct achievement. When one initiative (e.g. a greenfield function build) spans several related entries, do not spend one bullet per facet (operating model, team, throughput, roadmap) repeating a shared qualifier ("greenfield," "without proportional headcount"). Prefer the arc-composition synthesis, or consolidate the facets so the qualifier appears once. This is Arc composition's "do not over-synthesize" applied in the other direction: do not over-fragment the lead role either.

## Page length and line economy

**Page targets.** Senior IC: target 2 pages, up to 3 for a deep history.
Leadership: target 2-3 pages, hard ceiling 3. 4+ pages is a flagged exception only (genuine academic CV, federal/SES, or publication-heavy scientist).

**Governing principle: relevance-prioritized, no-pad.** Length follows relevance-prioritized content within the ceiling. Never pad to fill a page; never drop genuinely high-relevance content to hit a lower count. Page count is an outcome of including the right content, not a target to engineer.

**Line economy.** The binding constraint in every section is vertical space (rendered lines), not item or sentence counts; counts are proxies that fail when a unit runs long. Section real-estate budgets enforce the page ceiling. This is why the summary carries a line cap and bullets carry a line limit.

**Length is measured in Word, not estimated.** Markdown has no geometry and python-docx cannot paginate, so at QC the skill renders a throwaway .docx and asks Word for the page count (`scripts/cv_measure.py`). Only a measured overage routes back to the writer, who trims to the measured line count: compress by elevation first, drop content only as a last resort (single-writer preserved, capped). If Word is unavailable the length is reported as unmeasured and nothing is cut. The character-count estimate below (L1) is an early warning only and never triggers a cut; it ran 4 to 9 lines short of the rendered length.

**Calibration guard constants** (US Letter, 0.75-inch margins, 0.5-inch header/footer, Calibri 11pt body; the cv-render layout fixed 2026-06-02. `cv_qc.py` owns these numbers; a test fails if the two below drift from it). Citation comments are stripped before every length check, so they cost no length:
- Usable lines per page: ~47 (page 1, with the name and contact block) / ~50 (later pages).
- Characters per line at wrap: ~100 full-width; bullets ~95 (bullets sit at a 0.25-inch indent).
- Estimate each unit as ceil(characters / line capacity) and sum against the section's page budget. Early warning only; the Word measurement is authoritative.

**Compressing for length is a traceability risk, not a style pass.** Trimming a bullet to fit deletes words, and qualifier words carry claims. Removing "a version of", "contributed to", "supported", or the citation that licensed a strong verb turns an accurate claim into an overstatement without changing a single fact. Two consequences:
- Re-run the judgment traceability check after any compression pass, not only the mechanical one. Compression can pass every mechanical check while introducing new overstatements.
- When a compression removes a qualifier, fund the qualifier's return from somewhere else in the same unit rather than dropping it. The qualifier is usually the part the source actually supports.

**docx boundary.** Visual styling and the Earlier Professional Roles rendering belong to the render stage (cv-render), not this skill; the page count is measured here, on a throwaway render built with the same code. cv_content.md is the only handoff.

## Scope boundary

This file owns CV content structure and writing rules only. It does not own, and does not restate:

- **Relevance scoring, retrieval, and coverage** - the retrieval skill scores entries and exposes manifest signals; gap-analysis assigns per-requirement coverage. This file uses those scores to find entries and break ties (see PLAN: Selection).
- **Adjacency weights** - set by the retrieval manifest and the axis files' Adjacency sections. This file owns only the translation framing (how adjacent vs non-adjacent experience is worded; see Professional Experience).
- **Axis voice and vocabulary** - level voice and verb vocabulary, orientation summary-lead and section-emphasis, and industry/specialty terminology come from the five axis files and compose with this structure.
- **Critical-requirements extraction** - produced by role-classify in `jd_needs.md` (as text and Demand, grouped under ranked needs; a requirement's row number is its `CR-NNN` id). This file consumes them; it does not derive them.
- **Visual rendering** - styling, fonts, and the visual rendering of Earlier Professional Roles belong to cv-render (docx); the page count is measured by this skill in Word (see Length is measured in Word). The single handoff is cv_content.md. (The Earlier Professional Roles inclusion threshold and content density are owned by this file, above; only their visual rendering is deferred.)
- **No-fabrication, failure handling, partial-content discipline** - `global-rules.md`.
- **Skill procedure** - the Drafter/reviewer/QC loop, orchestration, and citation mechanics live in the cv-targeted SKILL.md and its agents, not in this rule file.
