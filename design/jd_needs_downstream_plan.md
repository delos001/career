# Ranked needs downstream: plan

Drafted 2026-11-11 during the ranker audit (#89 follow-on). Retrieval and gap analysis ran entirely on the old extraction fields (Type), so the ranker's work reached only the CV agents, and Type's section-of-origin values capped retrieval scores for the job's top need (Jazz N-01 rows 3 and 4, `contextual`).

## Locked decisions (user, 2026-11-11)

1. **Demand replaces Type.** `required` or `preferred`; `preferred` only when the JD marks the row optional ("preferred", "a plus", "ideally", "highly desirable", "nice to have", or under a preferred heading). How much a row matters comes from its need's rank. Script guard: an optional word in the row's JD sentence forces `preferred`.
2. **Alternatives and examples.** Items joined by "or" (or "and/or") are one requirement in one row, met by any one; the gap detector treats them as one part, `absent` only when none is shown. "e.g." and "such as" are examples: kept in the row text, never a judged part; showing one strengthens evidence, showing none is not a gap.
3. **Gap analysis judges per row, organized by need** in rank order.
4. **Retrieval: the scorer judges evidence strength only** (no Type, Demand or rank in its bands) and names the rows each entry matches; a script maps rows to needs in the manifest.
5. **Go / no-go** counts unmet `required` rows in core needs (needs with the `role-statement` signal) and in Qualifications, on today's bands (0 / 1-2 / several). Every other unmet row is listed under its need and does not move the label.

## Build sequence

Steps 1 to 5 and 7 built 2026-11-11 (decisions in `design_decisions.md` `ranked-needs-downstream-2026-11`); step 6 is next.

1. Extraction: Type to Demand in the extractor, `requirement_kinds.py` and C7; the optional-word guard; the alternatives and examples rule in the extractor. Convert the six open `jd_needs.md` files' Type column by script.
2. Retrieval: scorer bands and a `rows` field; `retrieval_apply.py` maps rows to needs in `retrieval.md`.
3. Gap analysis: the detector's alternatives and examples rule; `gap_context.py` groups requirements by need; `gap_assemble.py`, `gap_qc.py` (G10, G14) and the gap-analysis SKILL recommendation on the new count; report organized by need.
4. CV readers: replace must-have wording in hiring-manager and any other Type reader.
5. Remaining ranker audit items (4.3 to 4.5, finding 5).
6. The post-audit batch (see the session resume).
7. Record the decisions in `design_decisions.md`.

## Verification

- `python tests\run_tests.py` passes; every new check was first seen to fail.
- The batch: Medtronic and Summit are the fresh-JD test of extraction and ranking.
- The first real retrieval and gap run on a batch application is the live test of steps 2 and 3. Compare its label and unmet list against the old rule on the same statuses.
