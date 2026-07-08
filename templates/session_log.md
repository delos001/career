# Session Log - template

**Used by:** role-intake (creates and finalizes). Downstream skills append their own
sections below role-intake's; each writing skill owns its own sections.

One per evaluated job, written to `personal/applications/<SLUG>_APP-NNN_YYYY-MM/session_log.md`.
`scripts/assemble.py` renders the skeleton below: tokens in `{{double braces}}` are
substituted. The `{{research_completed_date}}`, `{{role_level}}`, `{{industry}}`, and
`{{axis_*}}` tokens are set to a pending marker at `init` (Phase 3) and filled with real
content at `finalize` (Phase 7). All other fields are populated at `init`.

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

## Interview section

The single authority for the shape of an interview round's session-log section,
parsed by `scripts/prep_qc.py` and `scripts/prep_interview_qc.py` (the `- Label:`
lines below are the required field set) and written by the prep skills, the
follow-up skill, `scripts/interview_lifecycle.py`, and `close-application`. One
section per round. `{{stage}}` is the round's stage label (Screen, Hiring Manager,
Peer / Team, Executive, ...), matching the `interview_notes.md` round label.

The session log is the ONE home for an interview's scheduling metadata. Each fact
is its own field so a program can update one without rewriting the others; the
prep doc and the notes file never restate a date. Sections hold CURRENT STATE, not
an accumulating audit trail (`Schedule history` is one line, rewritten in place).

```
## Interview: {{stage}}

- Prep date: {{prep_date}}
- Prep artifact: {{prep_artifact}}
- Research added: {{research_added}}
- Interview date: {{interview_date}}
- Time: {{time}}
- Duration: {{duration}}
- Medium: {{medium}}
- Interviewers: {{interviewers}}
- Schedule history: {{schedule_history}}
- Status: {{status}}
- Outcome: {{outcome}}
```

## Interview field notes

- **{{prep_date}}** / **{{prep_artifact}}** / **{{research_added}}** - `n/a` when the
  round ran with no prep skill run.
- **{{interview_date}}** - `YYYY-MM-DD`, bare. The current date, rewritten on a
  reschedule. Never prose; the other facts have their own fields.
- **{{time}}** - `HH:MM <tz>` (e.g. `12:30 EST`). Blank when not yet known.
- **{{duration}}** - planned, or planned vs actual (`30 min`; `planned 25 min; ran 15 over`).
- **{{medium}}** - phone | video | in-person.
- **{{interviewers}}** - `<name> (<title>)`, comma-separated; `TBD` when unknown.
- **{{schedule_history}}** - blank when nothing moved; otherwise one current-state
  line, e.g. `originally 2026-07-02; moved to 2026-07-20`. Written by
  `scripts/interview_lifecycle.py reschedule`, or reconciled from the notes round's
  `Schedule changes:` line by the follow-up skill.
- **{{status}}** - `scheduled` | `held` | `cancelled <YYYY-MM-DD>` | `no-show`.
  Distinct from Outcome: status is what happened to the *event*, outcome is its result.
- **{{outcome}}** - `pending` until resolved; `n/a (round cancelled)` for a cancelled
  round. A `pending` outcome at close-out time is what `close-application` queries on.
- **Optional extra fields** may follow `Outcome` (e.g. `Follow-up:` written by the
  follow-up skill; `Notes artifact:`; a `Role note:`). Only the fields above are required.

## Field notes

- **{{app_id}}** - the global application counter, from `scripts/app_id.py`.
- **{{role_level}}** - the Level-axis value. NOT inferred at JD read-in; `_(pending)_`
  at `init`, filled by `finalize` (Phase 7) from the axis-classifier's Level result.
- **{{industry}}** - the Industry-axis value. NOT inferred at JD read-in; `_(pending)_`
  at `init`, filled by `finalize` (Phase 7) from the axis-classifier's Industry result.
- **{{jd_file}}** / **{{comms_file}}** - filenames within the application folder.
  `jd.md` always present after Phase 3; `comms.md` present only when role
  communications were ingested.
- **{{jd_source}}** / **{{comms_source}}** - canonical persistent location of
  the file: the app-folder path written by `ingest`, or a URL if the source was
  a URL, or `"pasted"` if comms were pasted. Never an ephemeral path such as a
  desktop location. `{{comms_source}}` is blank when no comms were ingested.
- **Dates** - `YYYY-MM-DD`. `{{start_date}}` is set at creation;
  `{{research_completed_date}}` is `_(pending)_` until finalization.
- **{{axis_classification}}** / **{{axis_gaps}}** - `_(pending)_` markers at `init`;
  replaced at `finalize` with the `axis-classifier` subagent's output, which carries
  the `## Axis Classification` and `## Axis Gaps` headings and the per-axis lines.
