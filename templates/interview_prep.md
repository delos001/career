---
application: APP-NNN
company: <company>
role_title: <title>
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
sources: [research.md, gap_analysis.md, interview_notes.md, cv_content.md, jd.md, retrieval.md]
---
<!--
TEMPLATE - structure authority for interview_prep.md (the cumulative, one-per-application
interview prep doc), parsed by scripts/prep_qc.py and scripts/prep_interview_qc.py. Comments
are drafting guidance; REMOVE them all from the artifact copy so the frontmatter above stays
the first line of the file. The `sources` list above is a curated menu: keep only the files
this run actually used AND that exist. Drop any not yet present (e.g. `interview_notes.md` at
screen-only stage, before any interview round has happened) and add a downstream file back only
when a later refinement genuinely draws on it. QC (P5) fails a listed source that is absent.

Architecture:
- MAIN BODY = shared across all interviews; refined cumulatively; never duplicated per interview.
- APPENDIX = one thin block per interview; interview-specific only; points into the main body.

Conventions:
- Plain text = facts the candidate knows or lines they say. [bracketed] = coaching, never said aloud.
  Named labels (Cue / Avoid / If probed / Note) keep their labels.
- Scannable bullets and key words, NOT paragraphs. The doc is used live; answers are spoken-cue arcs,
  not text to memorize (exception: verbatim content such as the comp range).
- One element per bullet. A bullet packing a series of discrete, weight-bearing elements (semicolon-
  joined facts, or a bold label + colon + list) expands to indented sub-bullets, label as parent.
  Test: would each element want its own note, source ID, or spoken beat? If yes, expand. A reference
  list scanned as a set (values, TAs, a tool list) stays inline. Any element already carrying its own
  [bracket] or source ID MUST be its own bullet.
- No connector tokens as pseudo-operators: never weld list items with **plus** / **and** / **+** /
  **&**; break them into bullets. Ordinary "and/plus" inside one spoken sentence is fine.
- No build/process narration in the artifact. Lines explaining how this doc is made, maintained, or
  cross-linked live in the SKILL or these comments, never in the body. A short section-purpose
  orientation is allowed ONLY as a brief [bracketed] cue when it aids live use, never as a prose line.
- No redundant restatement. Same content in two places -> pick one home (single-home); the other
  points to it by label. Cross-references link, they do not re-state.
- NO em dashes anywhere in the artifact (product doc; QC enforces). Use commas or hyphens.
- Citations stay in italic-parens *(CR-001)*, never in brackets, never in a heading.
- Headings: a heading is a SHORT LABEL only, never coaching, citations, confirm/process text, or a
  full sentence. Allowed headings = the fixed set below, required and {optional} alike, PLUS three
  dynamic families: Appendix per-interview blocks, one per Anticipated Question (###), one per STAR
  story (####). Never invent a sub-heading outside that set.
- Sub-headings and bold labels do different jobs and neither outranks the other. A ### sub-heading is
  the navigation layer: it exists so the candidate can jump to a topic without scanning a whole
  section. A bold label breaks discrete content up WITHIN a sub-heading, which is the right tool once
  the reader is already there. A section that needs more internal shape gets a bold label, never a new
  sub-heading. The fixed set is meant to be sufficient; content that seems to need a new heading almost
  always belongs under an existing one, structured with bold labels.
- {optional} marks standard vocabulary that is not required every run: draft it, keep it when it
  carries material, drop it when the run left it empty, and never rename or delete one that has
  content. The tag is template-only and never appears in the artifact. Heading text is role-agnostic:
  no company, product, or person name, since the same structure serves the next application.
  STAR heading = "Story X - <short title>"; competency-framework mapping goes in the first bullet.
  Max depth four (####); inside a #### entry use bold labels, not headings.
- A genuinely new sub-heading is a TEMPLATE change, never an artifact-local one. If material is
  decision-relevant and has no home, the vocabulary is incomplete, and the fix belongs where every
  future application gets it. Test all three before proposing one:
  (1) the material earns space in the doc at all (decision-relevant for this round, not interesting);
  (2) it does not fit under an existing sub-heading even as a bold label;
  (3) the heading name is role-agnostic: it would make sense for a different company in a different
      industry, with no company, product, or person name in it.
  Fail (3) and this is role content rather than a new section; put it under the closest existing
  heading as a bold label. Pass all three and surface the proposal to the user with the material that
  forced it. On approval, add it to this template tagged {optional}, then use it. An unapproved
  heading never enters an artifact.
- This doc carries NO interview-event facts anywhere: no dates, times, or event status, in the
  frontmatter, the body, or an Appendix heading. Scheduling metadata has one home, session_log.md.
  Appendix headings name the round and its interviewer(s), nothing more.
- Confirm-vs-assume: screen- or JD-sourced claims about role/team/interviewer are written as
  UNCONFIRMED; decision-critical inferences generate a confirmation question in the Question Bank.
-->

# Interview Prep - <company> | <role title>

# MAIN BODY (shared across all interviews)

## Company & Industry - ready facts
<!-- Self-sufficient for live use: the candidate should not need to open research.md during the
interview. Interview-usable hooks, NOT a research dump. Company value-positioning (products / TAs /
platform / service lines); the strategic hook(s) that bridge to the candidate and to role decisions;
mission + values + any leadership/competency framework the employer screens on; 2-4 industry-timing
facts. Keep it high-level (research.md holds the depth). End with a brief 1-2 word pointer, e.g.
"Depth: research.md". A "do not volunteer financials" note goes as a [bracketed] cue, not a bare line.
Sub-topics are the ### headings below. Each is conditional: draft it, and drop it if the run produced
no usable material rather than carrying a bare heading. -->

### Leadership {optional}
<!-- Founding, and the named executives whose remit touches this seat. -->

### Scale {optional}
<!-- How big: headcount, hiring mix and open requisitions, function sizes, footprint. What size of
company the candidate is walking into. Any "do not volunteer headcount" cue sits here with the facts. -->

### Traction {optional}
<!-- Who they have won and what proves it: customer count and named customers, partnerships,
multi-year commitments, awards, geographic expansion. Sits next to Scale: together they answer how big
the company is and how well it is doing. -->

### Mission and culture {optional}
<!-- Stated mission, values, any competency framework the employer screens on, plus [hooks] to the candidate. -->

### Product and Services {optional}
<!-- What the company sells and how the pieces move. The part the seat has to be fluent in. -->

### Financials {optional}
<!-- Funding, stage, profitability. Cue what not to volunteer. -->

### Industry Timing {optional}
<!-- 2-4 dated facts that explain why this market is moving now. -->

## The Role
<!-- The candidate's role understanding; shared, refined cumulatively, never copied per interview.
Sub-topics are the ### headings below, each conditional: draft it, and drop it if the run produced no
usable material rather than carrying a bare heading. Decision rights (what the seat OWNS vs
INFLUENCES-but-does-not-own) split across Accountabilities and Influences. When inferred from the JD,
frame explicitly as a hypothesis to confirm (hedge every line: "likely...") and flag it inferred;
never state it as fact. Its confirmation question in the Question Bank REFERENCES this map, it does
not re-list it (single-home).
The deciding question / walk-out crux is NOT stated here; it lives in Concerns to Resolve (single-home).
Every decision-critical inference here MUST have a matching confirmation question in the Question Bank. -->

### Confirmed scope {optional}
<!-- First-hand, dated, attributed account of the job from someone inside it (hiring manager, recruiter,
peer). Highest-confidence content in the section, so it leads. Everything below it is inference from the
JD and public research; keeping the two apart is the point of this heading. -->

### Role Accountabilities {optional}
<!-- What the seat owns outright. Derived from the JD unless a Confirmed scope line covers it. -->

### Role Influences {optional}
<!-- What it shapes without owning, and who takes it from there. -->

### Stakeholders {optional}
<!-- Reporting line, sibling functions, partner functions named in the JD, external counterparties. -->

### Miscellaneous {optional}
<!-- Role-scope material with no home above: how a named duty actually divides, the boundary with a
sibling function, what the JD does not say the role requires. Not a dumping ground; if a topic recurs
across applications it earns its own heading here. -->

## Positioning & Approach
<!-- SHARED framing, reusable every interview (NOT interview-specific): the dual goal (advance AND
assess fit); the core reframe/stance for this role; title/level framing if the title is ambiguous;
posture + avoids. Interview-specific "frame" material does NOT belong here - it goes in the Appendix.
Sub-topics are the ### headings below, each conditional on the run producing usable material. -->

### The core stance {optional}
<!-- The one reframe the candidacy rests on, plus the counterweight to the biggest gap. -->

### Level and title framing {optional}
<!-- Only when the title is ambiguous: player-coach, founding seat, IC carrying a leadership title. -->

### Posture {optional}
<!-- How to behave in the room. -->

### Avoid {optional}
<!-- What not to do in the room. -->

## Fit and Gaps
<!-- The whole fit case in one place. -->

### Strengths to Lead With
<!-- Each a memorable bold key phrase + proof, with source IDs (CR-/TH-). Technical strengths
distribute here. Career-span numbers come from the profile, never the JD's minimum bar. -->

### Gaps They May Screen For
<!-- Cluster by underlying gap; carry CR numbers; jointly cover every non-covered requirement in
gap_analysis.md. Responses never overstate beyond the gap analysis. Technical gaps distribute here.
Each gap cluster is a BULLET, not a heading: bold label + italic-paren citation, matching Strengths,
e.g. "- **Named platform depth** *(CR-005, CR-010, CR-012)*", with probe / response / avoid as
indented sub-bullets. -->

### Proof points - STAR stories
<!-- One #### heading per story, form "Story X - <short title>"; put the competency/leadership-
framework mapping in the first bullet, not the heading. [A] line left open for the candidate. Anchor
to sourced strengths; do not invent. Narrative answers (background, why-leave, gap) live under
Anticipated Questions, not here. -->

### Situational / hypothetical
<!-- Insurance for competency-style prompts. Each prompt -> the STAR story / principle it anchors to.
Anchor to the stories above; do not invent. -->

## Anticipated Questions
<!-- Prepared answers to standard questions they ASK: walk-me-through-background, why-this-company,
what-do-you-know, why-leave, what-are-you-looking-for, employment gap. Spoken-cue arcs, not paragraphs
to memorize. Diplomatic answers carry If-probed + Avoid layers. "What are you looking for" is drafted
fresh for THIS role from positioning - a generic answer reads as "settling." -->

## Question Bank (questions to ask them)
<!-- SHARED, reusable across interviews (the candidate may deliberately re-ask to compare answers).
- Order the bank in TOPICAL CLUSTERS (role-scope adjacent, level/delivery adjacent, team, roadmap,
  etc.) so like questions can be asked back-to-back live.
- Stable labels (Opener, Q1, Q1a, Q2, ...) for cross-reference. A later interview's new question
  inserts into its cluster via a sub-label (Q1b, Q4a), it does not append at the end; labels never
  renumber once assigned.
- Each: the question text + a short [listen-for].
- Confirmation questions for inferred Role items reference the Role map, they do not re-list it
  (governor: decision-critical only).
- Frame screen-sourced confirmations as "the recruiter mentioned..." - never as fact.
- Per-interview PRIORITY is set in the Appendix, not here. -->

## Concerns to Resolve
<!-- The candidate's decision checklist; shared, refined as interviews resolve items. Each concern ->
the Question Bank Q(s) that resolve it, plus a [walk-out test] where one applies. -->

## Compensation / Logistics
<!-- Comp: posted band; stated range (scope-conditional if level is inferred); private floor
[never said aloud]; total-comp framing. Logistics: work auth, location/remote, relocation, travel,
availability - conditional facts confirmed this run, static facts from user-info.md shown to confirm.
Cue: usually defers past early rounds; do not volunteer. -->

# APPENDIX - Per-Interview Playbooks
<!-- One thin block per interview, chronological. PREP-FORWARD ONLY: purpose + interviewer(s) +
emphasis pointing INTO the main body. No outcomes, no "asked"/debrief content, and NO SCHEDULING
METADATA: no date, no time, no event status. Those live in session_log.md (the record) and
interview_notes.md (the capture surface). A date here goes stale the moment the interview moves,
in the one doc read immediately before the interview. Carry-forward that affects future prep flows
into the main body's cumulative refinement, not here. Never copies main-body content. The live
cue-card is projected from each block into interview_notes.md. Copy the block below per interview. -->

## <Stage label> - <Interviewer(s)>

**Purpose**
<!-- What this interview is for. If only screen-sourced, tag [confirm]. Prepare for flex: do not
narrow the whole prep to a stated purpose unless the user is certain it is the only topic. -->
- <...>

**Interviewer: <Name>** - <title / remit>
<!-- Researched intel; tag single-source / "confirm live". If the public footprint is empty, give
confirm-live handling + an opener, do not pad guesses. -->
- <...>

**Emphasis for this interview** (pointers into the main body)
- Primary goal: <...>
- Lead with: <Positioning stance>
- Prioritize from Question Bank: <Opener, Q#, Q#, ...> <!-- write in the order the questions should be ASKED, not by label number; this is the only record of that order, and interview-notes projects the list verbatim with a (P) prefix -->
- Push these Concerns here: <...>
- Presentation: <none | required -> skill not yet built; prepare manually>
- Unique to this interview: <none | ...>
