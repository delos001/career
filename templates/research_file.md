# Research File - template

**Used by:** role-research (creates). Downstream skills append their own sections below role-research's; each writing skill owns its own sections and its own portion of this spec.

One per evaluated job, written to `research.md` in the application folder (`python scripts/paths.py app <APP-NNN>`).

A **current-state document**: re-running or deepening research overwrites the affected sections; it does not accumulate a history of everything ever found.

`scripts/role_research_assemble.py` renders the skeleton below: tokens in `{{double braces}}` are substituted. The research-completed date lives in the session log only (`Research Completed Date`); files before 2026-11-19 carry a `**Research completed:**` line, which laying the file out removes. The `{{*_block}}` tokens are filled with the verbatim output of the three role-research agents - `company-research`, `title-research`, and `industry-research`. Each block carries its own heading and body:

- `{{industry_block}}` - `## Industry` with Summary / Key facts.
- `{{company_block}}` - `## Company` with Summary / Key facts.
- `{{role_block}}` - `## Title` with Summary / Key facts: what the job title means in the market (written by title-research). Files before 2026-11-17 call it `## Role`; readers accept both.

The sections read widest context first: industry, company, then the title. Each agent block arrives with its own `### Sources`; the script moves every list into the one `## Sources` at the end of the file, renumbering each section's `[i1]` / `[c1]` / `[t1]` markers by first citation so the list follows the body. A section another skill adds goes before `## Sources`.

`## Interview prep` holds the prep skills' research, one `### <target>` entry per prep-research result with a `**Added:** YYYY-MM-DD (interview prep, <stage>)` line, filed by `scripts/research_ledger.py add`, which moves the entry's sources to the end list as `[p1]`, `[p2]`, numbered across all entries. Files written before 2026-11-17 may instead carry prep results as their own `##` sections.

Axis gaps are recorded in the session log only. The job's requirements live in their own file, `jd_needs.md`, which role-extract writes; they are not kept here.

## Skeleton

```
# Research: {{company}} | {{role}}

**APP-NNN:** {{app_id}}

{{industry_block}}

{{company_block}}

{{role_block}}

## Interview prep

No interview prep research yet.

## Sources
```
