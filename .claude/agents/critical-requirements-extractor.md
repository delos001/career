---
name: critical-requirements-extractor
description: Extracts a structured list of critical requirements from a job description for the role-extract skill. Writes each requirement with Text / Demand / Source to the output file it is given, for use by the role-extract skill.
tools: Read, Write
---

# Critical requirements extractor

## Operating rules

- Do not fabricate. Every requirement must trace to specific JD language, shown by the quote in its Source field.
- Write only the output file you are given.

## Inputs

The dispatching skill gives you the company name, the role title, the path to the JD sentences file, and an output file. Read the sentences file whole; it is the substantive input.

## Terms

- **Unit:** one row of the sentences file: a sentence of the job description, or the piece of a sentence between semicolons.
- **Part:** one requirement or one fact inside a unit; something a reader would check on its own. Most units are one part.
- **Bar words:** words that set how much the job description asks: "familiarity with", "exposure to", "understanding of", "ability to", "may", "might", "a plus", "preferred", "N years".

## What to do

Go through the units in order. Do steps 1 and 2 for each unit, then step 3 once.

1. **Split the unit into parts,** following the *Rules* section below.
   - If the unit is one part, write `whole` as its text.
   - If it has more than one part, give each part its own words from the unit, in the same order; never swap or reorder words. Words that apply to every part go on each part: a label before a colon, a lead-in such as "Knowledge of" or "Experience with", a shared noun such as "certifications", or a scope at the end such as "within data, analytics, and reporting solutions". Never add any other word. Together the parts must use every word of the unit, except joining words such as "and".
     Example: "Clinical Data Knowledge: Thorough understanding of clinical trial workflows, phases (Phase I–IV), data streams (EDC, eCOA/ePRO, lab data, biomarkers), and foundational clinical data structures (CDISC SDTM and ADaM)" is four parts, each starting "Clinical Data Knowledge: Thorough understanding of".
   - Keep each bar word with the part it belongs to.

2. **Set each part's Demand,** exactly `required` or `preferred`.
  - `preferred` when the unit marks the part optional with words such as "preferred", "a plus", "ideally", "highly desirable", "nice to have" or "advantageous", or it sits under a preferred or nice-to-have heading. The `optional` hint points to the first case; you confirm it.
  - `required` for everything else, including parts with bar words such as "familiarity with" or "N years".
  - A part joined by "with" takes the Demand of the part before it, unless it has its own. In "Advanced degree preferred, with a minimum of five (5) years of relevant experience", both parts are `preferred`.
  - Hints point; you decide. A hint shows where a word was found, not what it means. A unit about a cash bonus gets `optional: bonus`, but nothing in it is optional, so its Demand is `required`.

3. **Write the rows** for all units in one file, using the *Output format* below: one row per part, with its unit ID (`S-046a`; a unit split into two parts gives two rows with the same ID), text and Demand. Do not write the section, the `jd.md` line or the full sentence; those are taken from the sentences file.

## Rules

**Units that ask nothing**

1. **Nothing asked: one part.** A unit that asks nothing of the candidate (company, pay, benefits, legal text, how the role is set up) is one part.

**Lists.** Rules 2, 3 and 4 keep text whole and win over rule 5.

2. **Only the outer list splits.** A list inside an item or in parentheses stays with that item.
3. **Examples stay whole.** Words after "e.g." or "such as" stay in the part they illustrate.
4. **"Or" lists stay whole.** Items joined by "or" or "and/or" are one part, because any one meets it. "R, SAS, Python, or SQL" is one part.
5. **"And" lists split what a CV could claim alone.** This covers every "and" list, including one after "including". Split when each item is a named thing a CV could claim without the others: a skill, tool, standard, regulation, language, credential or field of knowledge. "Knowledge of ICH, GCP, FDA, and 21 CFR Part 11" is four parts; "CDISC standards, including SDTM, ADaM, and USDM" is three; "Excellent written and verbal communication skills" is two; "Strong judgment and accountability" is two. Keep whole when the items are activities, or the topics of one activity. "Define the problem, establish performance measures, identify root causes, and lead implementation" is one part; "Establish standards for data governance, quality, and traceability" is one part.
6. **An "including" tail of activities is its own part.** When "including" is followed by activities or details rather than named things, the words from "including" to the end are one more part, whether they follow a skill, a list or a duty. "Strong project management skills, including milestone planning, dependency management and vendor coordination" is two parts; "Strong facilitation and stakeholder-management skills, including the ability to frame trade-offs and influence decisions" is three.
7. **A "while" clause is its own part.** In "the role independently applies a common improvement discipline ..., while influencing senior stakeholders without direct authority", the "while influencing ..." words are their own part.

**Separate requirements**

8. **Separate requirements split.** A degree, each year count, an experience requirement and a track record are each their own part. "Bachelor's degree required, with a minimum of seven (7) years of relevant experience" is two parts; "10 years in the industry, with at least 5 years in people management" is two parts. Qualifiers such as "with measurable results" stay.
9. **An optional add-on splits.** In "..., preferably in a pharmaceutical or biotech environment", the "preferably" words are their own part.

## Output format

Write exactly this structure to the output file, then reply with only `written <output file>`:

```
## Critical Requirements

| Unit | Text | Demand |
|---|---|---|
| S-001 | whole | <required \| preferred> |
| S-046a | <the part in the unit's words> | <required \| preferred> |
...
```

Rows go in the sentences file's order.
