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

## ALL: Date format

- **Professional Experience, Earlier Professional Roles, Independent Projects:** a range, `Mon YYYY - Mon YYYY` (e.g. `Feb 2024 - Jan 2026`), or `Mon YYYY - Present` when active. When only the year is known, `YYYY - YYYY`.
- **Education:** the year completed, `YYYY`.
- **Certifications & Training:** the year earned or completed, `YYYY`, or `In progress` for unfinished training.

## SUM: Professional Summary

**Prose.** The summary is a paragraph, never bullets.

**Length (hard rule).** At most 5 sentences. The sentences fill at most 8 lines in the rendered CV for a leadership job, or 6 lines for an individual contributor job.

## COMP: Core Competencies

**Layout.** Core Competencies is made up of 2 or 3 competency groups. Each group is one bulleted line: a short group label, a colon, then the group's items separated by a pipe, as in `Label: item | item | item`. A group's line may wrap to a second line. When the items do not form at least 2 groups of 2 or more, the section is a single bulleted line of items with no label. The section holds at most 10 items across all groups. Items are separated only by the pipe; a comma appears only inside an item, as in `(CDASH, SDTM, CDISC LAB)`.

## EXP: Professional Experience

**Shape.** Professional Experience is a list of companies. Under each company line are its roles, each on its own role line. Under each role line are the bullets that describe the work in that role.

**Company order.** Companies run newest first by their most recent role, with an active role counting as newest.

**Company line.** Each company is one line: `Company | Location | dates`. The company is the organization the work was done for and the company name is used even if a staffing agency placed the candidate.

For a single role, `dates` is that role's start and end. For a company with several roles, `dates` runs from the earliest role's start to the latest role's end.

**Role line.** Each role is `Title (dates) | Style | Type | Allocation`. The `(dates)` appear on the role line only when the company has more than one role. Style, Type and Allocation appear in this order, each only when it applies.

- **Style:** `Remote` or `Hybrid`. Left off for an on-site role.
- **Type:** `Contract: <Agency>` or `Freelance`. Left off for a direct hire.
- **Allocation:** `Concurrent` for a role held at the same time as another, followed by its share when under 100% (`Concurrent 60%`); `X%` for a single role under 100%. Left off for a single full-time role.

**Multiple roles at one company.** Give each role its own role line and bullets, newest first. Never put two titles on one line, and never share one bullet list across roles.

**Layout.** A role's bullets are one flat list, never nested.

### Within-role subheadings

Used only when the job is classified at the leadership level.

**Shape.** A subheading groups a role's bullets under a short label, below the role line. It never acts as a new section.

**Count.** At most 3 subheadings per role, each with at least 2 bullets under it. A role that cannot form at least 2 such groups has no subheadings.

**Labels.** Each label is at most 3 words, marked `<!-- need: N-NN -->`. Subheadings run in need-rank order.

## EPR: Earlier Professional Roles

Each role gets one `Company | Title | Dates` line, with no bullets or description. Give each role its own line, including several or concurrent roles at one company. Lines run newest first by end date; roles with the same end date run newest first by start date.

## PROJ: Independent Projects

**Shape.** Independent Projects is a list of projects. Each project is one header line followed by its bullets, or the header line alone for a one-line project. A project appears once, under one header, however many inventory entries it has.

**Order.** Projects run newest first by start date.

**Project header.** `Name | dates`, then an optional `| repository link`.

## CRED: Header

The CV opens with the candidate's name, then the contact block on one or two lines:
- Line 1: `location | email | phone`.
- Line 2, when profile links exist: the links, each as its bare domain and path with no platform label (`linkedin.com/in/...`, `github.com/...`). Links never go on line 1, where a long URL would wrap mid-link.

## CRED: Education

One bulleted line per degree: `Degree, Discipline | Institution | YYYY`.

## CRED: Certifications & Training

One bulleted line per item, certifications first, then training.
- A certification: `Certification | Issuer | YYYY | Status`, where Status is `Active` or `Inactive`.
- A training item: `Training | Provider | YYYY`, or `Training | Provider | In progress` when not finished.

## CRED: Professional Affiliations

One bulleted line per affiliation: `Affiliation | Membership | Status`. Membership is the role held, such as `Member`, `Committee Chair` or `Peer reviewer`; Status is `Active` or `Inactive`.

## CRED: Languages

One bulleted line per language: `Language | Proficiency`, as in `Spanish | Fluent`.

## TECH: Technical Proficiencies

**Layout.** Technical Proficiencies is made up of groups, one bulleted line per group: a short group label, a colon, then the group's items separated by a pipe, as in `Platforms: Databricks | Spotfire | SAS`. A group's line may wrap to a second line. When the items do not form at least 2 groups of 2 or more, the section is a single bulleted line of items with no label. Items are separated only by the pipe; a comma appears only inside an item.

**Caps.** At most 4 groups and at most 15 items across all groups. Each group label is at most 3 words.

## PLAN: Length

**Page limit (hard rule).** At most 3 pages, for an individual contributor job and a leadership job alike.
