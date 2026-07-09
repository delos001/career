# preparation-interview audit — RESOLVED

Two audit passes, both now closed.

- **2026-07-08:** first pass; fixed the top finding (lifecycle op vs QC X3
  collision) and moved scheduling metadata to discrete session-log fields
  (design_decisions.md, "Scheduling metadata has one home"). Logged F2-F5 as
  remaining.
- **2026-07-09:** full re-audit across all five seams (QC script vs SKILL;
  `interview_lifecycle.py` behavior; single-home consistency; follow-up +
  close-application seams; presentation pointer + cross-refs), run to catch new
  issues from the 2026-07-08 changes and to re-check F2-F5. The fresh audit
  independently re-identified F2-F5 (prior scoping confirmed) and surfaced new
  findings. ALL are now fixed and verified; nothing outstanding.

## What was fixed 2026-07-09

Real bugs (`interview_lifecycle.py`):
- Reschedule dropped the original interview date from the session log; now seeds
  `originally <date>` in Schedule history, matching the template spec.
- Cancel could overwrite a real recorded Outcome; now refuses when the round is
  already resolved (`refuse_if_resolved`).
- Cancel + notes tagging was a partial op on a session-log conflict (record
  untouched, notes tagged, reported success). `_apply` now aborts on any
  non-success session-log edit BEFORE touching the notes (`_abort_if_log_failed`).

QC / consistency:
- F2/F3: SKILL Phase 5 claimed three checks the script never ran (citation IDs,
  Appendix/main-body duplication, core-section length) plus a stale "QC not
  finalized" hedge. Rewritten to the real script/agent split. Length was never a
  deferral; claim dropped, not built.
- X4 event-status vocabulary drifted from the template (`held` leaked; stale
  `complete`/`rescheduled`). Realigned.
- Scheduling metadata could hide in an Appendix BODY (X3 = bold labels only, X4 =
  headings only). Covered by widening judgment check J6 (no false-positive risk on
  Emphasis prose).
- Both QC scripts hardcoded `Interview date:` / `Outcome:` value-validators that
  bypass the template-driven field set; added a fail-loud guard so a field rename
  can't silently disable the check.

Skill seams:
- F4: presentation-skill dead pointers softened to a manual-build path (skill
  still deferred; `presentation-build-skill`).
- Field-shape pointer named only `## Interview section` (tokens), not
  `## Interview field notes` (enums); fixed in all four writing skills
  (preparation-screen, preparation-interview, followup, close-application).
- followup create-path now sets `Status: held` + explicit `Outcome:` so a
  no-prep-run round is not later flagged by close-application as "never happened".
- close-application cancellation bullet now inlines the exact target strings
  (terminal, no-QC path).

LOW: cross-day cancel idempotency; `[NO-SHOW]`+`[CANCELLED]` co-existence;
impossible-calendar-date rejection; `--date` docstring precision; followup
datetime-split instruction; S1/S2 empty-Outcome symmetry across the two scripts;
COMPONENTS presentation-skill roster entry.

## Verification

Every code change exercised on scratch fixtures (reschedule chain + revive, cancel
+ refuse + idempotency, cross-day skip, no-show co-tag, impossible date, duplicate-
section abort). Both QC scripts pass on real APP-006 artifacts:
prep_interview_qc 17/17, prep_qc 8/8.

Files touched: `scripts/interview_lifecycle.py`, `scripts/prep_interview_qc.py`,
`scripts/prep_qc.py`, the four writing SKILLs, `templates/interview_prep.md`,
`.claude/agents/qc-preparation-interview.md`, `COMPONENTS.md`.
