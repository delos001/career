# JD needs ranker: redesign handoff (GitHub #89)

Status 2026-11-09. Pick up here. The plan this belongs to: `design/cv_persuasion_plan.md` (step 1).

## Where it stands

- Built and tested (uncommitted): `jd-needs-ranker` agent, role-intake Phase 5b and Step 9b, `assemble.py needs`, `role_intake_qc.py` I8, fixture, tests (72/72 pass). Design entry: `design_decisions.md` `role-intake-ranked-needs-2026-11`.
- The agent's instructions (`.claude/agents/jd-needs-ranker.md`) were patched one example at a time into long paragraphs. The user stopped the session over this. **Rewrite them as the steps below before any more test runs.**
- Remove the "type or level of role words are an umbrella, not needs" sentence (Rank step, role-defining bullet). It tells the ranker "technical leader" is not about leading. Wrong: leading the build-out is not building it.
- APP-028 (Jazz) `research.md` has `## Ranked Needs` reset to `_(pending)_`, so `role_intake_qc.py` I8 fails for Jazz until the ranker is re-run and its output written with `assemble.py needs`.

## Proposed steps (user had not approved yet; present them first, one short message)

1. **Separate role from boilerplate.** Mark which JD text is about the role and which is the company describing itself (mission, values, benefits, legal).
2. **Describe the job.** Answer fixed questions, each citing the JD lines it rests on:
   - What does the person deliver or own?
   - Do they lead the work, do it, or both? If lead: whom (staff, teams, vendors)?
   - What level is the role?
   - What does the JD say matters most?
3. **Group requirements into needs.** Follow how the JD groups items, read through step 2. Interchangeable lists under one parent term. Leading people is one need. Every requirement in exactly one need.
4. **Rank.** What the JD says matters most (role text only); then what the opening role sentence names; then repetition across sections; then hard minimums. Boilerplate and attitude statements last.
5. **Check the ranking against the step 2 description.** If the top needs don't match the job, fix grouping or ranking.
6. **Return** the description and the table.

## Settled by the user this session

- JD layout is the author's view of the work: group as the JD groups, but layout can mislead (template bullets, space-saving lists).
- Understand the whole JD: any sentence can explain another (next sentence, end of paragraph, another section). No fixed sentence windows.
- Leading people is one need however worded (people, functional, operational, team, line). Never argue those distinctions.
- Leading the build-out of something is not building it.
- Boilerplate and attitude/values ("passion for fighting cancer") rank last; no CV line can prove them.
- No examples from one application in the instructions; they must work for any role.
- Test on JDs the instructions were not tuned on: BeOne APP-027, Otsuka APP-026, Acadia APP-025, plus Jazz.

## Test runs 2026-11-09 (instructions before the step rewrite)

| Application | Ranker's top needs | Problem the user confirmed or raised |
|---|---|---|
| Jazz | 1 monitoring, safety, patient profile tools incl. self-service; 2 leading people; 3 strategy and roadmap; 4 collaboration (10 needs) | Matched his read. Skipped the job description (now required). |
| Acadia | 1 data integration and automation; 2 R/Python dashboards; 3 "hands-on technical role"; 4 R, Python, SQL, APIs | "Hands-on technical" describes role type and level, not a need. |
| BeOne | 1 "passionate interest in fighting cancer"; 2 R&D strategy; 3 strategic projects | Company boilerplate ranked first. |
| Otsuka | 1 technical and cross-functional leadership; 2 architecting AI solutions; 3 feasibility research (23 needs) | Not reviewed: my framing called it an individual contributor role, which he rejected. 23 needs is too many. |

## How to run it with him

One step or one result per message, a few lines, his words, no coined terms. Rewrite the instructions as steps first; then test all four applications; then confirm Jazz; then close #89.
