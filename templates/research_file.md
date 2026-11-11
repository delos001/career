# Research File - template

**Used by:** role-intake (creates); role-classify (fills Axis Gaps). Downstream skills append their own sections below role-intake's; each writing skill owns its own sections and its own portion of this spec.

One per evaluated job, written to `research.md` in the application folder (`python scripts/paths.py app <APP-NNN>`).

A **current-state document**: re-running or deepening research overwrites the affected sections; it does not accumulate a history of everything ever found.

`scripts/assemble.py` renders the skeleton below: tokens in `{{double braces}}` are substituted. The `{{*_block}}` tokens are filled with the verbatim output of the three Phase 4 subagents - `company-research`, `role-research`, and `industry-research`. Each block carries its own heading and body:

- `{{company_block}}` - `## Company` with Summary / Key facts / Sources.
- `{{role_block}}` - `## Role` with Summary / Key facts / Sources.
- `{{industry_block}}` - `## Industry` with Summary / Key facts / Sources.

`{{axis_gaps}}` starts pending; role-classify fills it. The job's requirements live in their own file, `jd_needs.md`, which role-classify writes; they are not kept here.

## Skeleton

```
# Research: {{company}} | {{role}}

**APP-NNN:** {{app_id}}
**Research completed:** {{research_completed_date}}

{{company_block}}

{{role_block}}

{{industry_block}}

{{axis_gaps}}
```
