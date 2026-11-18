# JD processing rules

Rules for each step that works on a job description after role-intake saves it. Each `## ` section is headed `## <KEY>: <name>`; the key names the step that reads it. Steps never read this file whole: `python scripts/jd_rules_slice.py --key <KEY>` prints this opening text and the sections for that key.

Keys:

- `SPLIT`: splitting each unit of `jd_sentences.md` into parts (the jd-splitter agent, role-extract Phase 1).

## SPLIT: Splitting units into parts

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

**Words every part keeps**

10. **Shared words go on each part.** Words that apply to every part go on each part. Examples: a label before a colon ("Clinical Data Knowledge:"), a lead-in ("Knowledge of", "Experience with"), a shared noun ("certifications"), a scope at the end ("within data, analytics, and reporting solutions"). "Clinical Data Knowledge: Thorough understanding of clinical trial workflows, phases (Phase I–IV), data streams (EDC, eCOA/ePRO, lab data, biomarkers), and foundational clinical data structures (CDISC SDTM and ADaM)" is four parts, each starting "Clinical Data Knowledge: Thorough understanding of".
11. **Bar words stay with their part.** Bar words set how much the job description asks, or mark something optional. Keep each one with the part it belongs to. Examples: "familiarity with", "exposure to", "understanding of", "ability to", "N years", "preferred", "preferably", "ideally", "a plus", "nice to have", "desirable", "advantageous".
