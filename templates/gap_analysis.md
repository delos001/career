# Gap Analysis - template

**Used by:** gap-analysis (creates and updates). Downstream skills (CV creation,
interview prep, career brief) read sections directly via section-level retrieval.

One per evaluated job, written to
`personal/applications/<SLUG>_APP-NNN_YYYY-MM/gap_analysis.md`.

A **current-state document**: re-running gap-analysis overwrites the file. The
session log carries the durable cross-run record (fit score, recommendation,
key gaps).

`scripts/assemble.py gap-analysis` renders the skeleton below: tokens in
`{{double braces}}` are substituted. Per-record blocks (Eligibility Flags,
Requirements, Language-Shift Cases, Partial-Match Cases, De-emphasize) are
rendered from structured inputs the skill passes to the script.

## Skeleton

```
# Gap Analysis: {{company}} | {{role}}

**APP-NNN:** {{app_id}}
**Date:** {{date}}
**Fit Score:** {{fit_score_pct}}
**Unmet Must-Haves:** {{unmet_must_haves_count}}
**Recommendation:** {{recommendation_label}}

## Eligibility Flags

{{eligibility_flags_block}}

## Requirements

{{requirements_block}}

## Language-Shift Cases

{{language_shift_block}}

## Partial-Match Cases

{{partial_match_block}}

## De-emphasize

{{de_emphasize_block}}

## CV Notes

{{cv_notes_block}}

## Recommendation

{{recommendation_block}}
```

## Field notes

- **{{fit_score_pct}}** - the type-weighted fit score from Phase 5 as a
  percentage with one decimal place (e.g., `78.3%`).
- **{{unmet_must_haves_count}}** - integer count of must-have requirements
  with final status `interview-deferred` or `unresolved`.
- **{{recommendation_label}}** - one of `Proceed`, `Proceed with caution`,
  `Do not pursue`.

### Per-section block rendering

- **{{eligibility_flags_block}}** - one bullet per flag in the format
  `- **<flag_type>**: <evidence>. User chose: <decision>.` Renders `_(none)_`
  when no flags fired.

- **{{requirements_block}}** - one sub-section per requirement:

  ```
  ### {{requirement_id}} - {{requirement_text}} ({{requirement_type}})
  - **Status:** {{status}}
  - **Evidence:** {{evidence_ids_comma_sep_or_none}}
  - **Notes:** {{notes_or_em_dash}}
  ```

  Closures via user input append `Closure ref: <staging_pointer>` to **Notes**.
  Status values: `covered`, `closed`, `language-shift`, `partial-match`,
  `interview-deferred`, `unresolved`. Always rendered (every requirement appears,
  regardless of status).

- **{{language_shift_block}}** - one sub-section per case:

  ```
  ### {{requirement_id}} - {{requirement_text_short}}
  - **Role terminology:** {{role_terminology}}
  - **Candidate terminology:** {{candidate_terminology}}
  - **Entries to reframe for CV:** {{entries_to_reframe_comma_sep}}
  ```

  Renders `_(none)_` when no language-shift cases. Only requirements with status
  `language-shift` appear here; partial-match cases have their own section.

- **{{partial_match_block}}** - one sub-section per requirement with status
  `partial-match` (genuine transferable experience, but a real gap remains):

  ```
  ### {{requirement_id}} - {{requirement_text_short}}
  - **Transferable evidence to cite:** {{entry_ids_comma_sep_or_none}}
  - **Transferable element and gap remaining:** {{notes}}
  ```

  Evidence to cite is the `entries_to_reframe` list when the case carries
  language-shift framing, otherwise the requirement's evidence IDs. Renders
  `_(none)_` when no partial-match cases.

- **{{de_emphasize_block}}** - one bullet per item in the format
  `- **<entry_id>**: <rationale>.` Renders `_(none)_` when no items.

- **{{cv_notes_block}}** - free-text general framing guidance for the CV
  architect captured during the Phase 4 gap-closure loop (not tied to any
  specific requirement). Renders `_(none)_` when no general notes were
  provided. Per-requirement Notes fields live inside `{{requirements_block}}`
  and are not repeated here.

- **{{recommendation_block}}** - paragraph in the format
  `**<recommendation_label>.** <1-2 sentence rationale>`.
