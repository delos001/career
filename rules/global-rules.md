# Global Rules

Cross-skill rules that apply to every skill in this workflow. Kept minimal intentionally. Anything that can live per-skill, in scripts, or in a skill authoring template does not belong here.

---

## Never Fabricate Content

All output must trace to source documents or explicit user input. If a metric, experience, role, date, quote, or framing is not in the user's profile documents or provided in the session, flag the gap. Do not invent, interpolate, or generalize.

Applies to CVs, career briefs, interview preparation, follow-up letters, role evaluations, and any other career-facing output.

---

## Failure Handling

On any failure - QC failure, document load failure, validation failure, unexpected state, ambiguous input - do not proceed and do not invent a resolution.

1. State the specific failure in one or two sentences: what failed, at what step, with what error if known.
2. Present the user with explicit options (re-run the prior step, accept the gap with acknowledgment, stop the session).
3. Wait for the user's explicit direction. Silent non-response is not approval to continue.

---

## Never Proceed with Partial Content

If a required document, slice, or input is incomplete or degraded, stop. Retrieval scripts are expected to fail loudly rather than return partial content; this rule covers LLM-side discipline when partial content reaches the skill anyway.

Partial content includes: documents missing expected sections, retrieval returning structural fragments without identifiable boundaries, user input that is ambiguous about a required field.

The only acceptable actions when content is partial are (a) halt and report per Failure Handling, or (b) request the missing content from the user.

---

## Stay Inside the Phase

A phase produces its declared output and nothing else. No commentary, no forward-looking assessment, no work belonging to a later phase or skill.

Not restricted: halting per Failure Handling, and observations about the phase's own subject matter. Role-intake may report that a JD contradicts itself; it may not report how the candidate scores against it.

---

## Approval Gates Open With Two Lines

Wherever a skill asks the user to approve, choose, or decide, the first two lines are what breaks in plain words, then what you would do about it. No file names, IDs, or code above those two lines. Detail underneath, only if wanted.

If it is not those two lines, the user replies "plain" and it is redone.

---

## Stage New Candidate Facts, Never Write Them Direct

A fact about the candidate that the profile documents do not already carry is staged with `scripts/staging_append.py` and nothing more. Never write it into `inventory.md`, `narratives.md`, or `positioning.md`; `profile-update` is their only writer. `staging_append.py` needs no application folder, so this holds with no skill running.

Amend a staged entry in place when better information arrives before promotion. The staging file is a queue, not a record.
