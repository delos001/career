# Research File - template

**Used by:** role-intake (creates). Downstream skills append their own sections below
role-intake's; each writing skill owns its own sections and its own portion of this spec.

One per evaluated job, written to
`personal/applications/<SLUG>_APP-NNN_YYYY-MM/research.md`.

A **current-state document**: re-running or deepening research overwrites the affected
sections; it does not accumulate a history of everything ever found.

`scripts/assemble.py` renders the skeleton below: tokens in `{{double braces}}` are
substituted. The `{{*_block}}` tokens are filled with the verbatim output of the
four Phase 4 subagents - `company-research`, `role-research`, `industry-research`,
and `critical-requirements-extractor`. Each block carries its own heading and body:

- `{{company_block}}` - `## Company` with Summary / Key facts / Sources.
- `{{role_block}}` - `## Role` with Summary / Key facts / Sources.
- `{{industry_block}}` - `## Industry` with Summary / Key facts / Sources.
- `{{critical_requirements_block}}` - `## Critical Requirements` with a list of
  requirements, each Text / Type / Source.

## Skeleton

```
# Research: {{company}} | {{role}}

**APP-NNN:** {{app_id}}
**Research completed:** {{research_completed_date}}

{{company_block}}

{{role_block}}

{{industry_block}}

{{critical_requirements_block}}

{{axis_gaps}}
```
