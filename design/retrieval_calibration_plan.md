# Retrieval cross-batch score calibration - plan

Status: built and verified 2026-11-04 on APP-027. Decision: `retrieval-cross-chunk-calibration-2026-11` in `design_decisions.md` (holds the verification numbers).

## Context

Inventory and narratives are scored in byte-budgeted chunks, one `retrieval-scorer` per chunk. The rubric binds consistency only "across all items in your batch"; nothing ties one batch's scale to another's.

Evidence from APP-027 (files in `personal/applications/beone_APP-027_2026-11/scratch/audit/`):
- Score audit: in 7 of 7 near-equivalent pairs split across chunks, the chunk 1 entry scored lower (gaps -0.15 to -0.40). Two entries moved from about rank 95 to the top 15 depending on chunk.
- Re-scoring chunk 1 narrowed but kept every gap (-0.10 to -0.30), so not a one-off.
- Probe: the 16 paired entries scored in one batch. Mean pair gap fell from -0.25 to -0.07. Chunk 1 entries rose (0.43 to 0.53) and their chunk 0/2 peers fell (0.67 to 0.60): both sides had drifted. Two residual gaps trace to real wording differences ("advised", "adopted"), which is legitimate.

Root cause: no shared reference across batches. Every run with more than one chunk carries this error, unmeasured.

## Design

Every chunk of a corpus also scores the same small **anchor set**. The merge uses the anchors to map each chunk onto one common scale, then reports how far the chunks disagreed.

1. **Seed chunk (split, stage 1).** A corpus that needs more than one chunk gets a seed chunk 0: an evenly spaced sample across the whole corpus (every Nth item), so it sees the full range of relevance. The remaining items are chunked in inventory order as before, keeping topic groups together. Stage 1 prints prompts for the seed chunks, any single-chunk corpus, and themes; only those are scored first.
2. **Anchor selection (split-anchored, stage 2).** Reads the seed chunk's scores and picks anchors at evenly spaced score values from the seed's highest to its lowest (nearest item to each target, ties by ID). Anchors are chosen by the scorer's own judgment of fit, so they span the scores that actually occur, including the top, for any role, typical or not. Inventory starts at 10 anchors (config); narratives use 3 (17 items in 2 chunks; more would crowd the corpus). Stage 2 inserts the anchors at even positions in every non-seed chunk (unlabeled; the scorer is blind to them), writes `<prefix>_calibration.json`, and prints the remaining prompts.
   - Rejected selection methods, measured on APP-027's uncalibrated scores: axis-tag ranking (anchors spanned 0.04-0.55, none in the top range); requirement word overlap (spanned 0.04-0.88 here, but depends on shared vocabulary and would bunch low for atypical roles, where transferable experience is worded differently); embeddings (a different model's proxy, plus a heavy local dependency or sending the profile to an outside service).
3. **Correction (merge).** For each anchor, consensus = mean of its raw scores across chunks. Per chunk, outlier-resistant fit raw-anchor -> consensus (Theil-Sen: median of pairwise slopes, median offset), so one anchor the scorers genuinely disagree on cannot swing the correction; apply to that chunk's non-anchor scores, clamp to [0, 1]. Offset-only when the chunk's anchors span under 0.2. Anchor final score = consensus. Coverage: each non-anchor once, each anchor once per chunk. Merge stops if stage 2 never ran.
4. **Drift record.** Merge writes per-chunk slope, offset, pre/post anchor disagreement and leave-one-out stability (largest change in a chunk's corrected scores when any single anchor is dropped) into the merged score file and prints them. Merge stops when a fit is degenerate (slope outside 0.5-2.0) or an anchor is missing from a chunk.
5. **Manifest + QC.** `retrieval_apply.py` writes a Calibration line into `retrieval.md`; `retrieval_qc.py` R9 checks it is present and that post-correction disagreement is under `max_post_residual` (FAIL above it). Single-chunk corpora record "not needed".
6. **Raw scores kept.** Raw per-chunk score files stay in scratch for audit; the merged file carries corrected scores only.

Cost: no extra scoring beyond the anchors (10 short items per non-seed chunk); about one chunk's scoring time added as wall-clock, since the seed is scored before the rest.

Rejected alternatives to anchoring: rubric clarification alone (reduces variance, no cross-batch alignment); fewer, larger chunks (reintroduces the attention degradation chunking fixed); a second re-rank pass over top entries (extra stage, drift still unmeasured).

## Build sequence

1. `retrieval_payload.py`: seed chunk in `split`; new `split-anchored` subcommand; header and section comments.
2. `retrieval_score_merge.py`: anchor-aware coverage, fit/correct, record, failure modes (built).
3. `retrieval_apply.py` + `retrieval_qc.py`: Calibration line and R9 (built).
4. `config.yaml`: anchor counts, min anchor span, slope bounds, QC threshold (built).
5. `tests/run_tests.py` (fixture): seed is a spread sample; anchors span the seed's score range and sit once in every chunk; known drift recovered; missing anchor, backwards chunk, and skipped stage 2 all stop the merge; R9 catches a missing or over-threshold record. Each check seen red first.
6. Docs: retrieval `SKILL.md` Phases 2-3 (two scoring waves), `design_decisions.md` entry, `retrieval-scorer.md` untouched.

## Verification (APP-027)

Re-run Phases 2-3 for this application with anchors. Pass when:
- the 7 matched pairs' mean gap after correction is within 0.05 of the single-batch probe's (-0.07);
- post-correction anchor disagreement is under the QC threshold;
- the full test suite passes.

Anchor count: from the 10-anchor run, refit every chunk on 6- and 8-anchor subsets (spread-preserving) and compare to the 10-anchor correction. Set the config default to the smallest count whose corrections stay within 0.02 of the 10-anchor result; record the numbers in the decision entry.

Then Phase 4-6 as normal.
