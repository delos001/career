# De-emphasize step removal - plan

## Context

Gap analysis builds a "de-emphasize" list (entries the CV should not feature) with a pre-filter script and the `de-emphasize-identifier` agent. With PR elements (2026-10-21) its candidates file passes the agent's read limit (#60).

Comparison of 18 applications (2026-10-21):
- 35% of CV citations come from outside the gap-analysis evidence. The CV writer chooses beyond the evidence, guided by the retrieval scores, which rank every entry.
- 5 of 18 CVs cited entries on the list anyway (Genmab 7).

The list repeats what low retrieval scores already say. Its one unique value, catching an entry that scores fine but sends a bad signal (PR-010 signals job hunting), belongs where the CV is written and reviewed.

## Decisions

- Remove the de-emphasize step from gap analysis.
- Add the bad-signal check to the `cv-architect` (applied while choosing content) and the `hiring-manager` persona (applied to each draft).
- Close #60 as not planned: the file it concerns no longer exists.
- Industry rule files keep their "Hiring-panel de-emphasis" lines: a different concept (framings panels weigh low), untouched.

## Build sequence

Built 2026-10-21; decision `de-emphasize-step-removed-2026-10`.

1. **Gap analysis.**
   - `gap-analysis` SKILL.md: drop Step 5b and the de-emphasize inputs and outputs.
   - `templates/gap_analysis.md`: drop the `## De-emphasize` section.
   - `gap_assemble.py`: drop `--de-emphasize-file`, the section render, and the cited-evidence safety net.
   - `gap_qc.py`: drop the section from the roster.
   - Delete `gap_de_emphasize.py`, the `de-emphasize-identifier` agent, and the config cutoffs.
2. **CV.**
   - `cv-targeted` SKILL.md and `cv-architect`: drop the de-emphasize list input, the copy into `drafting_plan.md` and "respect the list".
   - Add the bad-signal line to `cv-architect` and to the `hiring-manager` domain.
   - `hiring-manager` and `candidate-advocate`: drop their "de-emphasized item" lines.
3. **Tests and fixture.** Update the fixture gap analysis; rework the test that relies on de-emphasis (`run_tests.py`, objective and element protect each other) to cover whatever still uses `pr.is_cited`, or retire it.
4. **Docs.** `COMPONENTS.md`, `README.md`, `scripts/display/introductions.yaml`; mark `de-emphasize-prefilter-2026-07` and `de-emphasize-cited-evidence-filter-2026-06` superseded; amend `gap-analysis-architecture-2026-05` outputs; record this decision.

## Verification

- `python tests\run_tests.py` green; every reworked check seen to fail first.
- Grep finds no `de-emphasi` outside the industry rule files, design history and old application artifacts.
- Old application artifacts are not re-QC'd.
