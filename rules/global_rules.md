# Global Rules

Cross-skill rules that apply to every skill in this workflow. Kept minimal intentionally. Anything that can live per-skill, in scripts, or in a skill authoring template does not belong here.

---

## Never Fabricate Content

All output must trace to source documents or explicit user input. If a metric, experience, role, date, quote, or framing is not in the user's knowledge documents or provided in the session, flag the gap. Do not invent, interpolate, or generalize.

Applies to CVs, career briefs, interview preparation, follow-up letters, role evaluations, and any other career-facing output.

---

## Failure Handling

On any failure — QC failure, document load failure, validation failure, unexpected state, ambiguous input — do not proceed and do not invent a resolution.

1. State the specific failure in one or two sentences: what failed, at what step, with what error if known.
2. Present the user with explicit options (re-run the prior step, accept the gap with acknowledgment, stop the session).
3. Wait for the user's explicit direction. Silent non-response is not approval to continue.

---

## Never Proceed with Partial Content

If a required document, slice, or input is incomplete or degraded, stop. Retrieval scripts are expected to fail loudly rather than return partial content; this rule covers LLM-side discipline when partial content reaches the skill anyway.

Partial content includes: documents missing expected sections, retrieval returning structural fragments without identifiable boundaries, user input that is ambiguous about a required field.

The only acceptable actions when content is partial are (a) halt and report per Failure Handling, or (b) request the missing content from the user.
