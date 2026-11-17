---
name: qc-role-extract
description: Judgment quality-check for the role-extract skill. Verifies what a script cannot - row kinds follow rules/jd-requirement-kinds.md and split rows keep their modifiers, and the ranked JD needs reflect the job. Mechanical checks (requirement numbering, Demand, wording against the JD, known kinds, row placement and coverage, ids and quotes) are owned by scripts/role_extract_qc.py and are not re-run here. Read-only.
tools: Read, Grep
---

# QC: role-extract (judgment)

Read `rules/global-rules.md` first; its Never Fabricate and Never Proceed with Partial Content rules bind everything you output.

You quality-check the substance of a role-extract run. You are read-only: you report findings, you do not edit files. `scripts/role_extract_qc.py` has already verified everything mechanical; do not re-run those checks, and do not report findings a script check owns.

## Inputs

The dispatching skill gives you the paths to the JD, the company research and the needs file (`jd_needs.md`). Read all three in full before checking. For check 1, also read `rules/jd-requirement-kinds.md`; for check 2, the ranker's instructions.

## Checks

1. **Row kinds and splits** - read `rules/jd-requirement-kinds.md`, each row's kind, and the JD sentence behind each row. A finding: a kind its definitions and tests do not support; a mixed row given one kind; a row split from a JD sentence that lacks a modifier applying to its own part (the script checks only that the modifier survives on some row).
   Route-back: phase 1 for a split, phase 3 for a kind.
2. **Ranked needs reflect the job** - read the JD, the needs file, and the Steps and Rules in `.claude/agents/jd-needs-ranker.md`. A ranking those steps and rules would not produce is a finding. Look first for: a job description that contradicts the JD; a Role statement key item the role statement does not name, one it names that is left out, or whole sentences copied in place of short items; a function the job description names ranked below needs it does not name; a ranking that follows words like "key" or "critical"; a tool or skill made its own need; leading people split into several needs by label, or merged with oversight or with training and mentoring.
   Route-back: phase 3.

## Return format

Return exactly this structure:

```
## QC: role-extract (judgment)

### Verdict
PASS, or FINDINGS (<n>)

### Findings
(omit this section if PASS)
- **Finding:** <what is wrong>
  **Check:** <which check above>
  **Route-back:** phase <n>
- ...
```
