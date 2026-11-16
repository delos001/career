---
last_researched: 2026-05
---

# CV Structure - Sections, Layout and Length

**Used by:** cv-targeted.

**Purpose.** This file sets the CV's structure: which sections exist, their order, their line layouts and the length limits. Which sections appear is in `cv-sections.md`; what content goes into each section is in `cv-section-content.md`; how it is worded is in `cv-writing.md`.

**How to read this file.** Each section is headed `## KEY: name`. A KEY names the drafting step that reads it. The string `ALL` is a key that marks a section every drafting step reads.

A drafting step is never given this whole file at once. Instead, `scripts/cv_rules_slice.py` returns only the `ALL` sections and the relevant sections as defined by the key for that drafting step. The script stops if any heading has no key.

A rule marked `(hard rule)` always applies; no reviewer suggestion overrides it.

## ALL: Section order

Sections appear in the CV in the order listed below. The sections on the Work output line may appear in any order among themselves.

The block below is the single source for section order and required sections: `scripts/cv_qc.py` (S1, S2) reads it. Change the structure here, not in the script.

```
- Professional Summary (required)
- Core Competencies (required)
- Professional Experience (required)
- Earlier Professional Roles
- Work output: Independent Projects, Publications, Presentations
- Education (required)
- Certifications & Training
- Professional Affiliations
- Languages
- Technical Proficiencies
```

A new work-output section is added to this list when the inventory gains a matching section.

## SUM: Professional Summary

**Prose.** The summary is a paragraph, never bullets.

**Length (hard rule).** At most 5 sentences and at most 6 lines in the rendered CV (8 for a leadership job). Never pad to reach either limit.

## COMP: Core Competencies

**Count.** At most 10 items.

**Format (ATS-safe).** Single column. Items separated by the pipe delimiter (`|`), or set as a simple single-level bulleted list. The pipe (or bullet) is the only item separator; commas are within-item punctuation only (a parenthetical enumeration such as `(CDASH, SDTM, CDISC LAB)` stays part of its one item). Do not separate items with commas. No multi-column layouts or tables - parsers read left-to-right and scramble columns.

**Groups.** Items sit in 2 or 3 groups (zones), each with a short label, or in a single unlabeled list.

## EXP: Professional Experience

Roles run newest first.

**Company line.** Each company is a `Company | Location | dates` line, company name in bold, followed by its roles. For a company with several roles, `dates` is the total span across them; for a single role, it is that role's dates. The hiring organization (the end client) is the company; a staffing agency appears as a role qualifier (Type, below).

**Role line and qualifiers.** Each role is `Title (dates) | Style | Type | Allocation`, title in bold. The `(dates)` appear only when the company has more than one role. Each qualifier appears only when the role differs from the default (on-site, direct hire, not concurrent, fully allocated), in this order:
- **Style:** `Remote` or `Hybrid`.
- **Type:** `Contract: <Agency>` (naming the staffing agency) or `Freelance`.
- **Allocation:** a concurrent role shows `Concurrent`, followed by its allocation when under 100% (`Concurrent 60%`). A role that is not concurrent shows `X%` only when under 100%.

Qualifier values come from the inventory's Employment & Role History records.

**Date format.** `Mon YYYY - Mon YYYY` (e.g. `Feb 2024 - Jan 2026`), or `Mon YYYY - Present` for an active role. Use the months in the role records; use the year alone only when a record has only a year. This applies to company lines, role lines and Earlier Professional Roles lines.

**Multiple roles at one company.** Give each role its own title line, dates, qualifiers and bullets, newest first, however few bullets a role carries. Never put two titles on one line, and never share one bullet list across roles: a shared list hides which work belongs to which role. The candidate combines titles by hand when wanted.

**Role summary.** A role summary is a single bullet under the role line, one to two lines long.

**Earlier Professional Roles.** Each role gets one `Company | Title | Dates` line, with no bullets or description. Give each role its own line, including several or concurrent roles at one company.

**Layout.** Bullets sit directly under the role line as one flat list. Individual contributor CVs always use this layout; leadership CVs may add subheadings (see Within-role subheadings).

**Bullets per role.** The long draft has no limit on bullets per role. In the cut CV, a recent role carries roughly 2 to 8 bullets, and an older role kept in Professional Experience may carry just one. A role given a role summary carries only that summary, in both drafts.

### Within-role subheadings (leadership only)

**Labels.** Each subheading is a short label of a few words, marked `<!-- need: N-NN -->`. Subheadings run in need-rank order.

**Count.** At most 3 subheadings per role, each over at least 2 bullets. If fewer than 2 groups qualify, the role stays flat.

**Subheadings stay below the role.** Subheadings organize bullets under a role and never act as new sections.

## PROJ: Independent Projects

Independent Projects holds the candidate's independent and volunteer project work (inventory Independent & Volunteer Projects, `PR-NNN`). Publications and Presentations, the other work-output sections, have no rules yet (see `cv-sections.md`).

**Order and dates.** Each project shows its own Start Date and End Date from its inventory entry (a blank End Date shows as `Present`), in the date format used in Professional Experience. List projects newest first by Start Date.

**Project header.** Each project opens with one header line: `**Name** | Context | dates`, then an optional ` | repository link`. The name comes from the `Project:` field; the context is a short descriptor such as `Personal Project`; the link, when given, is the specific repository URL, not a profile landing page. Blocks that share a project sit under one header. A one-line project is that header alone, with no bullets.

## CRED: Header and credentials

### Header (name and contact)

The CV opens with the candidate name, then the contact block on up to two centered lines:
- Line 1: location | email | phone.
- Line 2 (when profile links exist): the profile links, each shown as its bare domain and path (strip the scheme, any `www.`, and any trailing slash) with no platform label, since the domain identifies it (e.g. `linkedin.com/in/...`, `github.com/...`).

Keep links on their own second line, not appended to line 1 (long URLs wrap mid-link). The full URLs live in `user-info.md`; the header shows the compact form.

### Education, certifications, affiliations and languages

Order is set in "Section order."

**Education.** Degree, discipline, institution, year. No GPA or honors (per inventory schema).

**Certifications & Training.** Each certification shows its issuer, year earned and status (Active or Inactive). Each item is one short line, not an achievement bullet.

**Professional Affiliations.** Affiliation, role (Member through Board / Officer / Committee Chair), and whether it is current; one short line each, drawn from the inventory's Professional Affiliations section.

**Languages.** Spoken languages with proficiency, one short line each.

**Technical Proficiencies.** Tools, platforms, languages, and methods from the inventory's Technical Experience section. Group into short labeled clusters (e.g. Languages, Platforms, Methods) where that aids scanning.

## PLAN: Length

**Page limits.** An individual contributor CV aims for 2 pages and may run to 3 for a long, relevant history. A leadership CV aims for 2 to 3 pages and never exceeds 3.

**Length is measured in Word.** At QC, the skill renders a draft .docx and asks Word for the page count (`scripts/cv_measure.py`). Only a measured overage sends the CV back to be cut, by the number of lines Word measured. If Word is unavailable, the length is reported as unmeasured and nothing is cut. The character-count estimate below is an early warning only and never triggers a cut; it has run 4 to 9 lines short of the Word measurement.

**Estimate settings.** The early-warning estimate uses these numbers, set for the CV layout (US Letter, 0.75-inch margins, 0.5-inch header and footer, Calibri 11pt body). `cv_qc.py` holds them, and a test fails if the two lines below differ from it. Citation comments are removed before any length check, so they add no length.
- Usable lines per page: ~47 (page 1, with the name and contact block) / ~50 (later pages).
- Characters per line at wrap: ~100 full-width; bullets ~95 (bullets sit at a 0.25-inch indent).
- A unit's estimated lines are its characters divided by the line capacity, rounded up. The Word measurement always overrides the estimate.
