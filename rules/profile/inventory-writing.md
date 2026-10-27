# Inventory writing rules

**Used by:** profile-update (drafting) and qc-profile-update (review).
Read through `python scripts/rules_slice.py inventory-writing --type <PREFIX>`,
which prints this opening, the shared rules, and the one entry type's section.

`templates/inventory.md` holds the schema: which fields each entry type has and
in what order. This file holds how to write them.

## Shared wording

These apply to every entry type.

- Use plain words and the field's standard terms (risk assessment, rules
  engine, medallion layers), never invented phrases. Before using or keeping a
  term, say what the work actually was.
- The verb carries the role: Led, Executed, Authored, Collaborated. Never
  upgrade one ("collaborated" does not become "built").
- Work that was designed but never built is written as "proposed" or "would",
  and the entry says it was not built.
- Full sentences end in periods, not semicolons.
- Ask for a missing fact instead of inferring it. Flag an unverified fact in one
  line.
- `scripts/profile_update_qc.py` (check P15) catches first person, banned
  phrases, em dashes, filler words, and missing final periods. Do not restate
  that list here; fix what it reports.

## RL: Employment & Role History

- Title as actually held, not reworded for a CV. The scope of the work belongs
  in EX entries.
- Company is the employer's name; `Independent` for self-directed periods.
- Dates are YYYY-MM. End Date stays blank while the role is current.
- Allocation is the share of working time: 100% unless the role ran alongside
  another.
- `Entries: None` only for a role deliberately carried with no entries.
- Never infer a date, title, or allocation. Ask.

## EX: Experience entries

**Description: what was done.** Test: is this an action?
- One bolded sentence: a verb carrying the role, the named object of the work,
  then two or three defining descriptors. Never a full list of the people,
  documents, or sub-steps involved.
- Name a tool here only when it is the object of the work (evaluating
  Pinnacle 21 Enterprise). Tools used hands-on go in Hands-on Tools. Otherwise
  use the umbrella term (BI dashboards, clinical data platforms).
- Group the people involved as teams or functions (cross-functional teams,
  Clinical Operations). Name them in Context.
- No purpose clause that restates Impact. No "from greenfield": Work-state
  already says it.

**Hands-on Tools: software and languages used hands-on in this work.** Test:
did you use it yourself?
- Names separated by ` | `, written exactly as the vendor writes them, with no
  version numbers.
- A tool that was the object of the work, such as one being evaluated, stays
  in Description. Tools a directed team used go in Context.
- Leave the field out if no tool was used hands-on.

**Impact: the observable result of the work.** Test: could someone see the
result without being told what you did?
- A changed process, a number, an adoption, or a decision others acted on
  passes. Results the work caused count, including a roadmap that led to tested
  capabilities.
- Fails: restated activity, alignment claims, "positioned for", purpose framing.
- No category tag (Risk Reduction and similar).
- If nothing observable came of the work, leave Impact out.
- For a "no X observed" result, state the scale first (all studies, a named
  scope, a time span), then that the result held.
- Put numbers on group parents and the most-cited entries first. Do not chase a
  number for every entry.

**Context: the situation before the work, constraints, or scope bounds.**
Test: is this the state of things, not what was done or what came of it?
- The previous state, when known.
- The organizational change the work prepared for (planned growth, a strategy
  shift), when it drove the work.
- Details behind anything Description groups or summarizes: the named teams,
  documents, or sub-steps.
- Tools a directed team used.
- Activity moves to Description. Outcomes move to Impact.
- No notes about how to frame the entry.
- Design work that was never built says so here.

**Topic group label: the body of work the group's entries share.** Test: would
every entry in the group fit under it?
- Form: `verb phrase: qualifier`, naming the kind of work and then the project
  or body of work (`lead execution: risk-based monitoring`,
  `tool development: data management operational oversight`).
- Recurring kinds of work reuse the terms already in the inventory (establish
  processes, evolve processes, lead execution, operational team leadership,
  resourcing and hiring). Check the role's existing labels before coining one.
- A label with no qualifier is valid when the kind of work is the whole topic
  (`site regulatory compliance and oversight`).
- Prefer an existing group. Propose a new one only when no existing label fits,
  and get the user's approval for its label.

## PR: Independent & Volunteer Projects

**Objective**
- One sentence stating the goal or problem.
- No methods, tools, or status. The role's dates show whether the work is
  ongoing.
- An exploratory project says so: "An exploration of ...".

**New objective or new element?**
- If it could stand on a CV alone, it is a new objective: a second block with
  the same `Project:` name.
- Otherwise it is an element.

**Elements**
- Each element states the technique and the problem it solves, e.g.
  "Deterministic scripts build every subagent prompt, reducing variation in LLM
  output."
- No benefit claims.
- Name techniques by the field's standard term, never a coined or internal one,
  so retrieval and applicant-tracking systems match the market's wording.
- One line; a second only when the element is too complex for one.
- Unbuilt work opens with Designed, Proposed, or Planned. Built work is stated
  plainly, with no progress wording.

**Outcome (under an element)**
- Observed results only: a number or a concrete event.
- Optional, and never padded.
- For a "no X observed" result, state the scale first (all runs, a named scope,
  a time span), then that the result held.

## ED: Education

- Degree, discipline, and institution exactly as conferred, by official name.
- Years only (YYYY).
- **Coursework** is optional. Include only courses that support the kind of
  roles applied to, grouped by category as the template shows, with course
  names as listed, not paraphrased.
- Never infer a degree, year, or course. Ask.

## TR: Professional Training

- Training and provider names exactly as the provider lists them.
- Completed only when finished. Unfinished training sits under In Progress with
  End Date blank.
- Record a course, not a single lesson or video. A short module counts only if
  the provider issues a completion record.
- Never infer a date or a completion. Ask.

## CERT: Professional Certifications

- Certification and issuer names exactly as the issuer states them, with the
  official credential name and abbreviation.
- Status is Active only if the certification is current against its expiration
  date; otherwise Inactive, and the entry stays.
- A course certificate of completion is training, not a certification: it goes
  under TR.
- Never infer a date or status. Ask.

## AFF: Professional Affiliations

- Organization name exactly as it styles itself.
- **Membership** names the role actually held (Member, Committee Member,
  Committee Chair, Board Member, Peer Reviewer). The highest role held, never
  upgraded: attending a committee meeting is not committee membership.
- Status is Active while membership or service continues.
- Never infer a role or date. Ask.

## AW: Awards & Honors

- Award and issuer names exactly as given.
- **Recognizes** links the award to the EX entry for the work it recognized,
  whenever one exists, so a CV can show the award with the work.
- **Description** only when the award's name does not say what it was for: one
  sentence, the reason as the issuer stated it.
- Never infer what an award recognized. Ask.

## LIST: List sections

Technical Experience, Industry Exposure Profile, and Languages.

- Each item is a named thing: a tool, product, platform, therapeutic area, or
  language. Never a method or capability; those belong in EX entries.
- One item per name, no version numbers.
- Product names exactly as the vendor writes them. When the candidate is unsure
  of the exact name, keep the uncertain wording rather than guessing a product.
- Add an item only if it was actually used, not just seen in a meeting.
- Categories come from the candidate's own field, never copied from another
  inventory.

## PB: Publications

- Title, venue, and author list exactly as published, authors in published
  order.
- Type matches the venue: "peer-reviewed article" only for a refereed journal.
- **Description:** what the publication covers, in one or two sentences. The
  author list shows the candidate's part; do not restate it here.
- **Impact:** the observable result of publishing it, such as citations,
  adoption, or a decision based on it. Same test as EX. No category tag. Leave
  it out if there was none.

## PS: Presentations

- Title, event, and co-presenters exactly as billed.
- Type matches what was delivered: a poster is not a talk, and a panel seat is
  not a keynote.
- **Description:** what the presentation covered, in one or two sentences. The
  Presenters field shows whether it was solo or shared; do not restate it here.
- **Impact:** the observable result, such as a follow-on invitation, adoption,
  or a decision based on it. Same test as EX. No category tag. Leave it out if
  there was none.
