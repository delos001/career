# Session Log - template

**Used by:** role-intake (creates and finalizes). Downstream skills append their own
sections below role-intake's; each writing skill owns its own sections.

One per evaluated job, written to `personal/sessions/<SLUG>_APP-NNN_YYYY-MM_SessionLog.md`.
`scripts/assemble.py` renders the skeleton below: tokens in `{{double braces}}` are
substituted. The `{{research_completed_date}}` and `{{axis_*}}` tokens are set to a
pending marker at `init` (Phase 3) and filled with real content at `finalize` (Phase 7).

## Skeleton

```
# Session Log: {{company}} | {{role}} | {{ym}}

## Metadata
- APP-NNN: {{app_id}}
- Company: {{company}}
- Role: {{role}}
- Role Level: {{role_level}}
- Session Start Date: {{start_date}}
- Research Completed Date: {{research_completed_date}}

{{axis_classification}}

{{axis_gaps}}
```

## Field notes

- **{{app_id}}** - the global application counter, from `scripts/app_id.py`.
- **{{role_level}}** - the level as titled or described in the JD; may be refined by axis
  classification (Phase 6).
- **Dates** - `YYYY-MM-DD`. `{{start_date}}` is set at creation; `{{research_completed_date}}`
  is `_(pending)_` until finalization.
- **{{axis_classification}}** / **{{axis_gaps}}** - `_(pending)_` markers at `init`;
  replaced at `finalize` with the `axis_classifier` subagent's output, which carries the
  `## Axis Classification` and `## Axis Gaps` headings and the per-axis lines.
