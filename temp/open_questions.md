# Career Repo Open Questions

Items blocking specific work that need answers now. When answered, move resolved decision to `design_decisions.md` and remove from this file. Protocol in memory `process_session_protocol.md`.

## Active

### competency-registry-runtime-value
Is the Competency registry load-bearing in cv_targeted's retrieval path, or does semantic retrieval against entry Description text produce comparable or better results? The 36-term activity-level registry is now in place, but the user flagged that the per-user authoring labor (registry construction, alias maintenance, per-entry tagging) may not justify the value over semantic retrieval at this corpus size (197 entries).
- Triggered by: user architectural concern raised 2026-05-01 after registry redesign.
- Blocks: `competency-retagging-step-5` (Step 5 should not proceed if registry is dropped from retrieval path).
- Resolution approach: build a bounded cv_targeted retrieval prototype against a real JD using two strategies (registry-filter + entry-text vs semantic-only); compare surfaced entries; pick the winner.
- Refs: `competency-registry-activity-level-redesign-2026-05`, `competency-retagging-step-5` (deferral), `cv-targeted-hybrid-retrieval` (deferral), `cv-targeted-content-rules-from-axes` (deferral).
