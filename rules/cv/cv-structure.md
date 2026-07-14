---
last_researched: 2026-05
---

# CV Structure - Content and Layout Rules

**Used by:** cv-targeted

Cross-cutting CV skeleton consumed by the cv-targeted skill alongside the five
axis files. Owns section order, per-section content rules, bullet and summary
structure, and the page-length guard. It does not vary by axis value; the axis
files supply the voice, vocabulary, and emphasis that compose with this
structure. Rules marked `(hard rule)` are non-negotiable; rules marked
`(guideline)` are defaults a reviewer may negotiate. All rules operate under
`global-rules.md` no-fabrication (every claim traces to a source entry; nothing
is invented); that is assumed throughout and not repeated per rule.

## Section order - two bands

The CV is two ordered bands, not one frozen list. Within each band the members
hold a fixed order; relevance-gated members appear only when they earn space
(see each section's gating rule).

**Evidence band** (top - carries the case for fit):
1. Professional Summary
2. Core Competencies
3. Professional Experience
4. Work-output sections (Selected Projects / Publications / Research) - relevance-gated

**Credentials tail** (bottom - verifies):
5. Education
6. Certifications & Training
7. Professional Affiliations - conditional, relevance-gated
8. Technical Proficiencies (always last)

Work-output sections sit in the evidence band, not the tail - a deliberate
deviation from the academic-CV convention of tailing publications, because on a
targeted industry CV these read as demonstrated work product, not credentials.
The class is extensible (e.g. Patents, Presentations) under the same relevance
gate.

## Header (name and contact)

The CV opens with the candidate name, then the contact block on up to two
centered lines:
- Line 1: location | email | phone.
- Line 2 (when profile links exist): the profile links, each shown as its bare
  domain and path (strip the scheme, any `www.`, and any trailing slash) with no
  platform label, since the domain identifies it (e.g. `linkedin.com/in/...`,
  `github.com/...`).

Keep links on their own second line, not appended to line 1 (long URLs wrap
mid-link). The full URLs live in `user-info.md`; the header shows the compact form.

## Professional Summary

The opening value proposition. It primes both the fast human skim and the
keyword match, so it leads with the candidate's positioning for THIS role, not a
generic career abstract.

**Content.** Strategic scope and - for leadership - scale (team size, budget,
cross-functional or enterprise reach); domain and industry positioning; and one
to two quantified signature achievements. Weave the target role's terminology in
naturally; do not stuff a keyword list.

**Length (guideline, not a hard rule).** Default 3-4 sentences. IC 2-4
sentences; a focused 2-sentence summary can read as confident for a very senior,
narrow target. Leadership up to ~6 sentences when scope genuinely requires it.
Never pad to reach a count.

**Line cap (guard).** Vertical space is the binding constraint, so the summary
carries a line budget, not only a sentence count: target <=6 rendered lines
(default / IC), <=8 lines (leadership exception). A 5-sentence summary at 3-4
lines each would eat roughly half a page - over budget even when the sentence
count looks fine. Caps are estimated at draft time and confirmed at render (see
Page length and line economy).

## Core Competencies

A high-placed keyword-and-skill block (directly under the summary) that doubles
as the ATS keyword anchor and the recruiter's fast-scan signal. Tailored to the
target role: the terms mirror the JD's language for the hard skills and domain
capabilities the candidate genuinely holds.

**Count.** 8-10 items at IC; 8-12 at leadership. Each item is a concise
capability phrase, not a sentence. Do not pad toward the ceiling or stuff a long
keyword list; relevance to the target role governs inclusion. A bare tool or
keyword enumeration (e.g. `SQL, R, Python, SAS`) belongs in Technical
Proficiencies, not crammed into a competency item.

**Format (ATS-safe).** Single column. Items separated by the pipe delimiter
(`|`), or set as a simple single-level bulleted list. The pipe (or bullet) is the
only item separator; commas are within-item punctuation only (a parenthetical
enumeration such as `(CDASH, SDTM, CDISC LAB)` stays part of its one item). Do
not separate items with commas. No multi-column layouts or tables - parsers read
left-to-right and scramble columns.

**Zoning.** Group the items into 2-3 coherent zones rather than one flat list,
so the block reads as a structured capability profile aligned to the target
role's emphasis. Label zones where a label adds scan value.

Defined zonings by orientation:
- **data-analytics** (3 zones): data strategy & governance; analytics capability
  & operating model; technical credibility.
- **platform-technology** (3 zones): technology strategy & platform governance;
  systems & domain knowledge; analytical & process credibility.

For an orientation without a defined zoning above, cluster the competencies into
2-3 zones following that orientation's emphasis (see the orientation axis file's
Section emphasis); a flat single list is acceptable when zones would be
artificial.

## Professional Experience

The core evidence section. Reverse-chronological. Each role earns its space by
relevance to the target; depth concentrates on the roles that matter most for
this application.

**"Relevant" is an upstream signal, not Drafter judgment.** Throughout this file,
"relevant" / "relevance" means the retrieval manifest scores (semantic, axis
exact-match, axis adjacency-weighted) and the gap-analysis per-requirement
coverage, read together. The Drafter consumes those signals; it does not
re-decide relevance ad hoc.

**Selection under scarcity (tie-break).** When relevant entries compete for
limited space (the page ceiling, or bullets-per-role), select deterministically
in this order rather than by ad hoc judgment:
1. **Weighted coverage before duplication.** The coverage floor is guaranteed
   only for the highest-weighted requirement types. Every **must-have and
   preferred** requirement keeps its single strongest cited entry before any
   requirement receives a second. **Contextual and duty-derived** requirements
   earn no guaranteed slot; they are covered only when an entry already chosen
   for a must-have/preferred requirement or a protected differentiator speaks to
   them (ride-along coverage), reflected in that entry's framing rather than
   claiming a dedicated bullet or subheading. A scarce slot never goes to a
   duplicate for an already-covered must-have/preferred while another
   must-have/preferred would otherwise be thinly covered or uncovered. This can
   rank a lower-semantic entry above a higher-semantic one when the lower entry
   is the only strong evidence for a must-have/preferred requirement: weighted
   coverage overrides raw relevance score. Requirement type comes from the
   gap-analysis requirement headers (per the upstream-signal principle); it is
   not re-judged here.
2. **Then by signal, in fixed order.** Among entries of equivalent coverage
   contribution (choosing extra entries once coverage is met, or choosing which
   of several entries on one requirement to keep), order by (a) semantic score,
   then (b) axis-exact count, then (c) axis-adjacency score, then (d) recency of
   the role.
3. **Protected differentiator.** A genuinely differentiating, truthful strength
   (candidate-advocate domain) is not dropped for a marginally higher-ranked but
   generic entry; it earns space even if it sits slightly lower on the chain.

This makes selection reproducible from the retrieval signals and the gap-analysis
coverage map, and operationalizes the relevance-prioritized, no-pad principle
below. The inputs are the upstream signals applied in this fixed order; it does
not license re-judging relevance.

**Adjacency translation (transferable experience).** Entries whose axis value is
adjacent to the target (per the axis file's Adjacency section; adjacency weight
~0.5 in the manifest) are translated, not dropped: reworded toward the target
value's language while the underlying facts stay intact. Entries whose axis value
is non-adjacent are surfaced for their cross-cutting capability only (e.g.
leadership, capability building, driving process), not claimed as target-domain
experience. Cross-cutting themes that are not domain-bound transfer regardless of
axis distance. Translation rewords; it never fabricates a domain, metric, or
scope the source entry does not support.

**Entry header.** Each company is a `Company | Location | dates` line (company
name bold), followed by its role(s). `dates` on the company line is the total
span across the company's roles (multi-role) or that single role's dates
(single-role). The hiring organization (the end client) is the company; a
staffing agency is shown as a role qualifier (Type, below), not as the company.

**Role line and qualifiers.** Each role is `Title (dates) | Style | Type |
Allocation`. `Title` is bold. The `(dates)` parenthetical appears only when the
company has more than one role (a single-role company carries the dates on the
company line, so the role line omits them to avoid duplication). The qualifiers
follow in this fixed order, and each appears only when it deviates from the
standard role (Direct, On-site, non-concurrent, fully allocated):
- **Style** (default On-site, hidden): `Remote` or `Hybrid`.
- **Type** (default Direct, hidden): `Contract: <Agency>` (naming the staffing
  agency) or `Freelance`.
- **Allocation** (default 100%, hidden): when allocation is under 100%,
  `Concurrent X%` if the role is concurrent, otherwise `X%`. A concurrent role at
  100% allocation shows nothing.

The qualifier values (Type, Style, Concurrent, Allocation, Agency) come from the
inventory's Employment & Role History records.

**Date format.** Month and year: `Mon YYYY - Mon YYYY` (e.g. `Feb 2024 - Jan
2026`), `Mon YYYY - Present` for an active role. Pull months from the role
records; fall back to year-only when a record carries only a year. Applies to the
company-line span, the role-line `(dates)`, and the `Company | Title | Dates`
lines in Earlier Professional Roles. Do not collapse to year-only when the source
carries months.

**Default entry layout: flat.** Bullets sit directly under the role title as a
single-level list. This is the default for every role and the only layout at IC
level. (Senior/leadership roles may add thematic subheadings under defined
conditions - see Within-role thematic subheadings.)

**Bullets per role, by relevance and recency.** The most recent, most relevant
roles carry the most bullets; older or less-relevant roles compress. Roughly 2-8
bullets per role as a norm; a heavy recent senior role may run higher.

**Ordering.** Lead each role with its strongest, most role-relevant bullet
(impact-first), not the role's chronological first task. The top of each entry is
high-attention space.

**Multiple roles at one company.** When a candidate held more than one role at
the same company, never merge the titles onto one header line (no
`Title A; Title B`). Order the roles reverse-chronologically. Choose the layout
by bullet volume:
- Stacked: when the roles together carry only a few bullets (roughly one or two
  per role), stack the role titles, each with its own dates, directly under the
  company line, then a single shared bullet list ordered impact-first. Qualifiers
  shared by ALL the stacked roles (Style, Type/Agency) hoist to the company line
  (`Company | Location | Style | Type | dates`); each stacked title then shows
  only what differs (its allocation).
- Separate sub-entries: when one or more roles carry enough substantial bullets
  to stand on their own (about three or more), give each role its own title,
  dates, bullets, and its own qualifiers (no hoisting, even when a qualifier
  repeats across the roles).
Pick the form that keeps impact density high without fragmenting a short
engagement into thin one-bullet entries.

**Earlier Professional Roles.** CV experience uses two sections: Professional
Experience and Earlier Professional Roles. A role belongs in **Professional
Experience** when any of these hold:
1. It is currently active or ended within the last 10 years (threshold: current
   year minus 10).
2. It is older but directly closes a critical-requirement gap that would
   otherwise be unaddressed.
3. It is newer than any rule-2 inclusion, so no perceived gap opens between the
   two sections.

A within-threshold role kept only to prevent a perceived timeline gap (not for
content) earns a 1-2 line scope summary, not detailed bullets. Whether an older
role "closes a gap" (rule 2) and whether a role is content-relevant versus
timeline-only come from the retrieval / gap-analysis relevance signal (the
upstream-signal principle above), not a fresh judgment here. For
transformation-strategy or process-operations applications, operational roles
(e.g. project management, clinical monitoring) that predate the transformation
work stay in Professional Experience when within threshold; their summary
reflects operational breadth, establishing the foundation the transformation arc
builds on, rather than matching a JD cluster.

**Earlier Professional Roles** holds every role outside the threshold that does
not meet rule 2. Format: Company | Title | Dates only; no bullets, no
descriptions. List each role on its own line; do not merge multiple or
concurrent roles at the same company onto a single line. The section sits
immediately after Professional Experience.

**Gap-prevention principle.** Account for every period of professional activity
across the two sections; note concurrent roles as concurrent. A documented gap
(e.g. full-time study) is preferable to filling it with a role that does not
belong.

### Bullet rules

**Bullet construction: CCAR, rendered impact-first.** The underlying model is
Challenge - Context - Action - Result. On the page the bullet leads with the
result/impact, then the action and (briefly) the context; full narration is
reserved for interviews, not the bullet. IC bullets compress Challenge and
Context into a single clause or imply them, foregrounding action and result.
Leadership bullets carry all four components, because scope and stakes (the
challenge and context) are part of what the bullet must establish.

**Accomplishment-framed, not duty-framed.** Every bullet states what was
achieved, not what the role was responsible for. "Responsible for X" and
duty-list phrasing are not acceptable bullet forms.

**Impact-type preference order.** Lead with the strongest impact type available
for the claim, in this order:
1. Type 1 - quantified (a number: %, $, time, count, scale).
2. Type 2 - bounded qualitative (a concrete, verifiable outcome without a clean
   number: "eliminated rework," "passed inspection with no findings").
3. Type 3 - contextual narrative (significance or effect described in context).

Fallback chain when quantitative data is absent: quantified -> bounded
qualitative -> contextual narrative -> proxy metric (scale/scope affected) ->
scope as signal (team size, budget, breadth) as a last resort. Never fabricate a
number to satisfy Type 1.

**One sentence per bullet (hard rule).** Each bullet is exactly one sentence.
Multi-sentence bullets are not permitted. CCAR components render as clauses
within that single sentence, never as separate sentences. If a bullet contains
two distinct accomplishments, split it into two bullets; if it is one
accomplishment written as two sentences, condense it to one.

**Bullet length (hard rule).** Target 2 lines; 3 lines acceptable only for a
highest-value, genuinely complex achievement; 4+ lines never. A bullet over the
limit is condensed (tighter wording), or split when it bundles distinct
accomplishments - never left to run long. Line count is the ceiling; the
one-sentence rule and the line limit are applied at draft time and enforced
mechanically by QC (both are deterministically checkable).

### Within-role thematic subheadings (senior/leadership only)

An optional device to group a heavy role's bullets under thematic subheadings.
Use sparingly and only where it earns its space; the default remains flat.

**Level gate.** Senior/leadership roles only. IC CVs never use subheadings (flat
only, per Default entry layout).

**Per-role condition.** Apply only to a recent, accomplishment-heavy role - one
carrying enough bullets (roughly 8+ across distinct themes) that a flat list
would be hard to skim. Lighter and older roles stay flat even on a leadership CV.
Typically only the one or two most recent senior roles qualify.

**Labels come from the critical-requirements artifact, not the raw JD (hard
rule).** Each subheading is a short descriptive phrase (a few words, not a
sentence) naming the theme of one critical requirement (CR-NNN) produced by
role-intake and carried through gap-analysis - the processed JD. Condense the
requirement's vetted wording into a compact label in the Core Competencies label
style (e.g. CR-015 "...FSP resource allocation and strategic vendor
partnerships..." becomes `FSP and vendor oversight`); never reproduce the full
requirement sentence - it wastes scarce vertical space and reads as over-specific.
The Drafter never re-parses the raw JD, and labels are never drawn from the
candidate's narratives or inventory. The `<!-- cr: CR-NNN -->` marker carries the
requirement id. Restrict labels to requirements this role has cited evidence for
(per the retrieval manifest and gap-analysis coverage), so a subheading both
mirrors a real JD priority and is genuinely backed by the role.

**Cap.** 3-6 subheadings per role. Fewer than 3 distinct JD-aligned themes ->
stay flat (subheadings add clutter, not signal). More than 6 -> the role is
over-segmented; consolidate.

**No forcing.** A subheading appears only when the role has genuine, cited
evidence for that JD theme. Never create a JD-themed subheading the role cannot
fill, and never stretch a bullet to fit a theme.

**Bullets under a subheading** follow all standard bullet rules: flat
single-level, impact-first, one sentence each, within the line limit, each citing
its inventory entry ID.

**ATS.** Keep subheadings visually subordinate to the role title (the standard
section headings carry the parse); subheadings are an organizational aid, not new
top-level sections.

### Arc composition (senior / enterprise-scope roles)

For roles whose target requires enterprise or cross-functional program-scope
proof points, a list of atomic bullets undersells collective impact (the panel
reads ten process improvements, not one transformation). Arc composition
synthesizes related atomic entries into a single higher-level achievement bullet.
Governed by `arc-composition-for-high-impact-roles`; reconciled here to flat
layout.

**Trigger.** The JD's primary deliverable language is at enterprise or
cross-functional program scope ("led enterprise initiative," "built and scaled a
capability"), and gap-analysis surfaced the relevant strength at arc level.
Senior/leadership context. Otherwise compose atomic bullets normally.

**Composition unit: narratives (ST-NNN).** A narrative's required Linked Inventory
field defines which atomic EX/PR entries form the arc and supplies the arc claim.
The Drafter reads that authored grouping; it does not re-derive which entries
combine. Synthesis without a backing narrative is not permitted - ad-hoc
re-assembly of atomic entries is the fabrication-risk path and is disallowed.

**Output: one synthesized bullet (not nested).** The arc renders as a single
higher-level bullet that subsumes its linked entries - one sentence, within the
line limit, impact-first. The atomic entries are compressed into the claim, not
listed beneath it (flat layout; no sub-bullets). Citation is the union of the
linked source ids (e.g. `<!-- src: EX-12, EX-15, EX-23 -->`), optionally also the
ST-NNN.

**No overstatement.** The synthesized claim must not assert scope, scale, or
impact beyond the union of its cited entries. QC verifies the arc bullet against
its cited slices.

**Same role/company only.** An arc bullet composes only from entries within the
role/company it sits under. A narrative arc that spans employers is a
career-level theme: it informs the Professional Summary and positioning, not a
single experience bullet.

**Relationship to subheadings.** Orthogonal. A synthesized arc bullet may sit
under a JD-sourced subheading or in a flat list; the arc determines bullet
content, never the heading.

**Default is atomic.** Synthesize only when a narrative arc exists and collective
impact genuinely exceeds the sum of granular bullets. Do not over-synthesize -
concrete, quantified atomic achievements that carry their own weight stay as
their own bullets.

## Work-output sections (Selected Projects / Publications / Research)

One relevance-gated section class in the evidence band, demonstrating work product
beyond the role history. Members: Selected Projects, Publications, Research
(extensible to Patents, Presentations). Each renders only when it earns its space.

**Relevance-gated, not existence-gated.** Include a member section only when its
entries add signal for the target role (per the retrieval manifest and
gap-analysis), not merely because such entries exist in the inventory. This
supersedes the legacy "include whenever project entries exist" rule. Pure
leadership roles default to omitting Selected Projects unless a specific project
demonstrably evidences a JD requirement.

**Independent / self-directed project work belongs here, not in Professional
Experience (hard rule).** Self-employment or independent activity whose
accomplishments are recorded only as independent-project entries (inventory
Independent & Volunteer Projects, `PR-NNN`) is represented as Selected Projects entries in this
work-output section, placed after Professional Experience, never as a role at the
top of Professional Experience, regardless of recency. A role record carrying no
employment (`EX-NNN`) accomplishments and only `PR-NNN` project content is
project work, not an experience role; a between-roles personal build is the
canonical case. Inclusion stays relevance-gated (above); this rule governs
placement once included. The short Professional Experience gap this may leave is
preferred to elevating off-experience project work above the role history (see
the Gap-prevention principle under Professional Experience). `cv_qc.py` enforces
this mechanically (a `PR-NNN` citation inside Professional Experience fails QC).

**Placement.** Evidence band, not the credentials tail (rationale under Section
order). Most defensible for senior-scientist / regulated-IC profiles.

**Project voice exception.** Project entries follow design/build voice (what was
designed, built, analyzed, delivered), not the organizational leadership framing
used in Professional Experience. Leadership voice rules apply to Professional
Experience entries only; a project is described as work product regardless of the
CV's level framing.

**Standard rules still apply.** Entries are impact-first, one sentence per bullet,
within the line limit, and each cites its inventory entry id (PR-NNN, or the
relevant id for publications/research).

## Credentials tail

The verifying band, below the evidence band, read at lower attention. Fixed
order: Education, then Certifications & Training, then Professional Affiliations
(conditional), then Technical Proficiencies (always last).

**Education.** Below Professional Experience (the experienced-candidate
convention; education leads only for new graduates). Degree, discipline,
institution, year. No GPA or honors (per inventory schema). List all degrees;
short reference content, not relevance-gated.

**Certifications & Training.** Certifications (with issuer and, where relevant,
status/currency) and material training. Lead with credentials relevant to the
target role; omit stale or off-target items that add noise rather than signal.
Concise reference lines, not bulleted achievements.

**Professional Affiliations (conditional, relevance-gated).** Include only for
board, governance, or senior-leadership targets where memberships, board seats,
or committee roles are a JD signal; omit otherwise. When included, place after
Certifications & Training and before Technical Proficiencies. Affiliation, role
(Member through Board / Officer / Committee Chair), and currency; concise
reference lines drawn from the inventory's Professional Affiliations section.

**Technical Proficiencies (always last).** Tools, platforms, languages, and
methods the candidate genuinely holds, tailored to mirror the JD's technical
terminology (a secondary ATS keyword anchor). Group into short labeled clusters
(e.g. Languages, Platforms, Methods) where that aids scanning. For pure-leadership
targets the section may be brief or omitted when technical tooling is not a JD
signal. Listed proficiencies must be real; never list a technology to match a
keyword the candidate does not actually know.

## Cross-cutting writing rules

Apply across every section.

**Impact-first.** Lead with the outcome/result wherever a claim has one, in
bullets and in the summary. The high-attention position carries the strongest
signal.

**Acronym expansion.** Spell out a less-common acronym on first use, with the
acronym in parentheses; use the acronym thereafter. Common in-industry acronyms
the hiring panel reads fluently (e.g. FDA, GCP, ICH, IRB, GxP in pharma) need no
expansion. Judge "common" by the target industry, not the general reader.

**No em dashes (hard rule).** Em dashes do not appear in the CV. Use a pipe (|) or
hyphen for header separators (Company | Location | Dates), and rewrite prose and
bullets with periods, semicolons, or natural connectives instead of em-dash
clause breaks.

**No AI-tell phrasing (hard rule).** The CV must not read as machine-written.
(Source: Wikipedia, "Signs of AI writing.") Avoid:
- Negation-contrast framing: "not just X, but Y," "it's not X, it's Y," "less
  about X and more about Y." State the point directly.
- Rule-of-three padding: do not force a third item (adjective, adjective,
  adjective; phrase, phrase, and phrase) for rhythm. List only what is real.
- Trailing significance clauses: the appended "-ing" flourish ("..., driving
  efficiency," "..., streamlining operations") that asserts vague impact. Replace
  with a quantified result (per impact-type order) or cut it.
- Buzzword/puffery used as filler: leverage, robust, seamless, pivotal, crucial,
  foster, underscore, showcase, groundbreaking, world-class, cutting-edge,
  transformative (and "spearhead" except where level-appropriate). Prefer the
  level axis file's verb vocabulary and concrete language.
- Marketing copulas: "serves as," "stands as," "is designed to" in place of plain
  "is/was" or an action verb.
- Vague intensifiers standing in for a number: significantly, greatly,
  successfully, substantially. Quantify if the impact is real; otherwise state it
  plainly.
- Title Case headings and decorative boldface: labels use the defined heading
  style, not Title Case On Every Word.

**Plain, verifiable language (hard rule).** No keyword-stuffing, no verbs inflated
beyond the level's voice (governed by the level axis file), no duty-list phrasing.
Tailoring means genuine relevance and terminology alignment, not term dumping.
Never substitute a job-description buzzword for an accurate term to manufacture a
keyword match or stretch a claim: when a plainer, more accurate word describes the
experience, use the accurate word. Every term must map to what the candidate
actually did, without overstatement.

**Achievement single-home (hard rule).** Each distinct achievement - a specific
quantified result or named accomplishment (e.g. "200+ data transfers without
headcount growth," "interim-analysis rework from ~60% to 0%," "selected Databricks
as the enterprise platform") - has ONE home in Professional Experience: a single
bullet, under the role that owns it. It is not restated as a second bullet under
the same or another role. The Professional Summary may headline one to two
signature achievements (per the Summary content rule); when it does, it states
them at headline altitude (the outcome and why it matters), not as a verbatim
repeat of the owning bullet's wording and number. Choose one: headline the metric
in the summary and frame the owning bullet on the mechanism (how it was done), OR
keep the metric in the bullet and lift the summary to scope and positioning;
re-running the same sentence and number in both is duplication. Core Competencies
are capability phrases only; a competency item never restates a metric or
accomplishment carried by the summary or a bullet. The same number/metric
surfacing in two places (other than the deliberate summary-headline-plus-owning-
bullet pairing) is redundancy.

**Protect the lead role (guideline).** The most recent senior role is the
highest-attention block; each of its bullets must carry a distinct achievement.
When one initiative (e.g. a greenfield function build) spans several related
entries, do not spend one bullet per facet (operating model, team, throughput,
roadmap) repeating a shared qualifier ("greenfield," "without proportional
headcount"). Prefer the arc-composition synthesis, or consolidate the facets so
the qualifier appears once. This is Arc composition's "do not over-synthesize"
applied in the other direction: do not over-fragment the lead role either.

## Page length and line economy

**Page targets.** Senior IC: target 2 pages, up to 3 for a deep history.
Leadership: target 2-3 pages, hard ceiling 3. 4+ pages is a flagged exception only
(genuine academic CV, federal/SES, or publication-heavy scientist).

**Governing principle: relevance-prioritized, no-pad.** Length follows
relevance-prioritized content within the ceiling. Never pad to fill a page; never
drop genuinely high-relevance content to hit a lower count. Page count is an
outcome of including the right content, not a target to engineer.

**Line economy.** The binding constraint in every section is vertical space
(rendered lines), not item or sentence counts; counts are proxies that fail when a
unit runs long. Section real-estate budgets enforce the page ceiling. This is why
the summary carries a line cap and bullets carry a line limit.

**Length verification is a guard, confirmed at render (Option A).** This skill
cannot authoritatively measure rendered length (markdown has no geometry, and
python-docx does not compute wrapping or pagination). It enforces a conservative
geometry-informed estimate as a guard; the render stage measures actual
lines/pages and routes any violation back to the Drafter to trim (single-writer
preserved), capped, before re-rendering.

**Calibration guard constants** (US Letter, 0.75-inch margins, 0.5-inch
header/footer, Calibri 11pt body; the cv-render layout fixed 2026-06-02. These
mirror the `cv_qc.py` constants and must move with them):
- Usable lines per page: ~47 (page 1, with the name and contact block) / ~50
  (later pages).
- Characters per line at wrap: ~100 full-width; bullets ~95 (bullets sit at a
  0.25-inch indent).
- Estimate each unit as ceil(characters / line capacity) and sum against the
  section's page budget. Guard only; the render stage is authoritative.

**docx boundary.** Visual styling, authoritative pagination and page count, and
the Earlier Professional Roles rendering belong to the render stage (cv-render),
not this skill. cv_content.md is the only handoff.

## Scope boundary

This file owns CV content structure and writing rules only. It does not own, and
does not restate:

- **Relevance scoring, retrieval, and coverage** - the retrieval skill scores
  entries and exposes manifest signals; gap-analysis assigns per-requirement
  coverage. This file consumes those signals (see "Relevant is an upstream
  signal").
- **Adjacency weights** - set by the retrieval manifest and the axis files'
  Adjacency sections. This file owns only the translation framing (how adjacent
  vs non-adjacent experience is worded; see Professional Experience).
- **Axis voice and vocabulary** - level voice and verb vocabulary, orientation
  summary-lead and section-emphasis, and industry/specialty terminology come from
  the five axis files and compose with this structure.
- **Critical-requirements extraction** - produced by role-intake (as text and
  type; the `CR-NNN` ids are assigned downstream by gap-analysis, in the same
  order). This file consumes them; it does not derive them.
- **Visual rendering** - styling, fonts, authoritative pagination and page count,
  and the visual rendering of Earlier Professional Roles belong to cv-render
  (docx). The single handoff is cv_content.md. (The Earlier Professional Roles
  inclusion threshold and content density are owned by this file, above; only
  their visual rendering is deferred.)
- **No-fabrication, failure handling, partial-content discipline** -
  `global-rules.md`.
- **Skill procedure** - the Drafter/reviewer/QC loop, orchestration, and citation
  mechanics live in the cv-targeted SKILL.md and its agents, not in this rule file.
