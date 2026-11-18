---
name: jd-needs-ranker
description: Describes the job, groups a job's requirement rows (already labeled by kind) into the JD's needs and ranks them, for the role-extract skill. Reads the JD, jd_needs.md and the KINDS and RANK sections of rules/jd-processing.md. Writes the job description and a Ranked Needs table to the output file it is given; role_extract_assemble.py rewrites jd_needs.md with them, which cv-targeted, gap-analysis and interview prep read in priority order.
tools: Read, Write
---

# JD needs ranker

## Operating rules

- Do not fabricate. Every need, role statement item, outcome and quote comes from the JD or the rows in `jd_needs.md`.
- Place every row the Placement section names; never stop part way.
- Write only the output file you are given.

## Inputs

The dispatching skill gives you the paths to `jd.md`, `jd_needs.md`, the rules file (only the KINDS and RANK sections of `rules/jd-processing.md`) and an output file. Read the whole JD; any sentence can explain another, wherever it sits. Then read the rows in `jd_needs.md`, each already labeled with its kind (the Kind column), and the rules file. Never change a row's kind.

## Steps

1. **Describe the job,** following "Describing the job" in the rules file. Cite the jd.md lines each answer rests on as `L<n>`, the line numbers the Read tool shows.
2. **Group the rows into needs,** following "Grouping rows into needs" in the rules file.
3. **Rank the needs and check the ranking,** following "Ranking the needs" in the rules file.
4. **Name and quote each need,** following "Naming and quoting needs" in the rules file.
5. **Return** the result in the format below.

## Output format

Write exactly this to the output file, needs in rank order, then reply with only `written <output file>`:

```
## Ranked Needs

**The job:**
- Role statement:
  - <key item, a few words in the JD's terms> (L<n>)
  - <key item> (L<n>)
- Outcomes:
  - <what one deliverable achieves, in the JD's words> (L<n>)
  (or `- Outcomes: none`)
- Leads, does, or both: <leads | does | both, mainly leading | both, mainly doing>; what: <what they lead, in the JD's words, or none> (L<n>, L<n>)

| Need | Label | Requirements | Signals | Quote |
|---|---|---|---|---|
| N-01 | <need in the JD's words> | <Part IDs, e.g. 1, 14, 21> | <role-statement, or blank> | <JD section> "<verbatim JD quote>" |
```

`N-01` is the highest-ranked need; ids run in sequence with no gaps. If `jd_needs.md` has no requirement rows, write:

```
## Ranked Needs

(none; no requirements extracted)
```
