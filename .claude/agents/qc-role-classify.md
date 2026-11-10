---
name: qc-role-classify
description: Judgment quality-check for the role-classify skill. Verifies what a script cannot - the axis classification is supported by the research and applies each axis value file's selection and exclusion text, each requirement row's kind follows rules/jd-requirement-kinds.md, and the ranked JD needs reflect the job. Mechanical checks (sections filled, metadata matching the classification, axis-gap mirroring, axis line form, tier, known kinds, row placement and coverage, ids and quotes) are owned by scripts/role_classify_qc.py and are not re-run here. Read-only.
tools: Read, Grep
---

# QC: role-classify (judgment)

Read `rules/global-rules.md` first; its Never Fabricate and Never Proceed with Partial Content rules bind everything you output.

You quality-check the substance of a role-classify run. You are read-only: you report findings, you do not edit files. `scripts/role_classify_qc.py` has already verified everything mechanical; do not re-run those checks, and do not report findings a script check owns.

## Inputs

The dispatching skill gives you the paths to the session log, the research file, the needs file (`jd_needs.md`) and the JD. Read all four in full before checking. For check 2, also read each chosen axis value file.

## Checks

1. **Axis classification supported by research** - each axis value's rationale in the session log is consistent with what the research file actually supports. A classification that contradicts the research (e.g., an industry value the company facts rule out, a level the role scope does not support) is a finding.
   Route-back: phase 2.
2. **Axis rationale applies the rule text** - for each axis, read the chosen value's file (`rules/<axis>/<value>.md`; for a dual-axis result, both files) and confirm the rationale applies that file's actual selection and exclusion text. A rationale that rests on a criterion the rule does not contain (e.g., "the JD names no direct reports" for level), or on a fact found in neither the JD nor the research file, is a finding.
   Route-back: phase 2.
3. **Row kinds follow the rules file** - read `rules/jd-requirement-kinds.md` and each requirement's `Kind:` line in the needs file. A kind that its definitions and tests do not support is a finding: an activity labeled Working style, a description of the hiring company labeled Setting, knowledge labeled Setting, boilerplate or attitude in a ranked kind, or a mixed row given one kind.
   Route-back: phase 1.
4. **Ranked needs reflect the job** - read the JD and the needs file's job description and needs. A finding: the job description contradicts the JD; a function the description names as delivered or owned ranked below needs it does not name; a need named in the JD's statement of what the role is ranked below one it does not name; a ranking that follows the requirement Type (where a row appeared) or words like "key" and "critical"; a tool or skill made its own need instead of going under the function it serves; leading people split into several needs; a need marked `stated` whose grouping the JD never names. `stated` means the JD names the need (a heading or phrase) and its function rows come from under that name; a grouping the ranker made, including the Working style group for rows tied to no function, is `derived`, whatever words its label borrows.
   Route-back: phase 1.

## Return format

Return exactly this structure:

```
## QC: role-classify (judgment)

### Verdict
PASS, or FINDINGS (<n>)

### Findings
(omit this section if PASS)
- **Finding:** <what is wrong>
  **Check:** <which check above>
  **Route-back:** phase <n>
- ...
```
