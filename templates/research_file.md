# Research File - template

**Used by:** role-intake (creates); role-classify (fills Ranked Needs and Axis Gaps). Downstream skills append their own sections below role-intake's; each writing skill owns its own sections and its own portion of this spec.

One per evaluated job, written to `research.md` in the application folder (`python scripts/paths.py app <APP-NNN>`).

A **current-state document**: re-running or deepening research overwrites the affected sections; it does not accumulate a history of everything ever found.

`scripts/assemble.py` renders the skeleton below: tokens in `{{double braces}}` are substituted. The `{{*_block}}` tokens are filled with the verbatim output of the four Phase 4 subagents - `company-research`, `role-research`, `industry-research`, and `critical-requirements-extractor`. Each block carries its own heading and body:

- `{{company_block}}` - `## Company` with Summary / Key facts / Sources.
- `{{role_block}}` - `## Role` with Summary / Key facts / Sources.
- `{{industry_block}}` - `## Industry` with Summary / Key facts / Sources.
- `{{critical_requirements_block}}` - `## Critical Requirements` as a `| # | Text | Type | Source |` table, one row per requirement; the `#` column is a 1-based sequential index that maps to each requirement's downstream `CR-NNN` id.

`{{ranked_needs}}` and `{{axis_gaps}}` start pending. role-classify fills Ranked Needs with `role_classify_assemble.py needs` from the `jd-needs-ranker` agent: `## Ranked Needs` as a `| Need | Label | Basis | Requirements | Signals | Quote |` table in rank order, `N-01` highest. Every requirement row belongs to exactly one need. Downstream skills read needs in this order; the Type column records only where a requirement appeared in the JD.

## Skeleton

```
# Research: {{company}} | {{role}}

**APP-NNN:** {{app_id}}
**Research completed:** {{research_completed_date}}

{{company_block}}

{{role_block}}

{{industry_block}}

{{critical_requirements_block}}

{{ranked_needs}}

{{axis_gaps}}
```
