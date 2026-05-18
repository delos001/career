# Session Log - template

**Used by:** role-intake (creates and finalizes). Downstream skills append their own
sections below role-intake's; each writing skill owns its own sections.

One per evaluated job, written to `personal/sessions/<SLUG>_APP-NNN_YYYY-MM_SessionLog.md`.
`scripts/assemble.py` renders the skeleton below: tokens in `{{double braces}}` are
substituted. The `{{research_completed_date}}` and `{{axis_*}}` tokens are set to a
pending marker at `init` (Phase 3) and filled with real content at `finalize` (Phase 7).
All other fields are populated at `init`.

## Skeleton

```
# Session Log: {{company}} | {{role}} | {{ym}}

## Metadata
- APP-NNN: {{app_id}}
- Company: {{company}}
- Role: {{role}}
- Role Level: {{role_level}}
- Industry: {{industry}}
- Session Start Date: {{start_date}}
- Research Completed Date: {{research_completed_date}}
- JD file: {{jd_file}}
- JD source: {{jd_source}}
- Comms file: {{comms_file}}
- Comms source: {{comms_source}}

{{axis_classification}}

{{axis_gaps}}
```

## Field notes

- **{{app_id}}** - the global application counter, from `scripts/app_id.py`.
- **{{role_level}}** - the level as titled, described, or inferred from the JD;
  user-confirmed in Phase 2. Distinct from the Level-axis value recorded in the
  axis classification section.
- **{{industry}}** - the role's industry, inferred from the JD and user-confirmed
  in Phase 2; consumed by `industry-research` in Phase 4.
- **{{jd_file}}** / **{{comms_file}}** - filenames within the application folder.
  `jd.md` always present after Phase 3; `comms.md` present only when role
  communications were ingested.
- **{{jd_source}}** / **{{comms_source}}** - URL, original file path, or
  `"pasted"`. `{{comms_source}}` is blank when no comms were ingested.
- **Dates** - `YYYY-MM-DD`. `{{start_date}}` is set at creation;
  `{{research_completed_date}}` is `_(pending)_` until finalization.
- **{{axis_classification}}** / **{{axis_gaps}}** - `_(pending)_` markers at `init`;
  replaced at `finalize` with the `axis-classifier` subagent's output, which carries
  the `## Axis Classification` and `## Axis Gaps` headings and the per-axis lines.
