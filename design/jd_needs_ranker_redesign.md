# JD needs ranker: redesign handoff (GitHub #89)

Status 2026-11-10, end of session. The plan this belongs to: `design/cv_persuasion_plan.md` (step 1).

## Where it stands

- The user approved the ranker's six steps one at a time, and `.claude/agents/jd-needs-ranker.md` is rewritten as those steps. Design entry: `design_decisions.md` `requirement-kinds-2026-11`.
- Requirement kinds and their tests: `rules/jd-requirement-kinds.md`. Every kind and wording list was approved by the user.
- role-classify writes its result to `jd_needs.md` in each application folder (the job, each need with its requirements' text and kinds, then Qualifications, then Not ranked). Written by `role_classify_assemble.py needs`; read and filtered by `scripts/requirement_kinds.py`; checked by `role_classify_qc.py` C6. Not ranked rows never reach retrieval or gap analysis. All 73 tests pass; the filter and the text-match check were seen to fail.
- BeOne APP-027: `jd_needs.md` written and the ranking confirmed by the user. Two instruction faults found and fixed on the way: `stated` was defined by where the label's words came from (now: who made the grouping); step 3 contradicted it.
- To watch on the next runs: working style the JD ties to a function through other sentences was made its own need (BeOne rows 7, 9); one JD line split across two needs (rows 17, 18); the job description's "Leads, does, or both" line explains its reasoning instead of giving the answer and its sources.
- Nothing is committed.

## Next: move requirement extraction into role-classify

Decided by the user, not yet built. Requirement extraction is the same kind of work as labeling and ranking, so it belongs in role-classify, and the requirements should live in one file.

1. role-classify runs the `critical-requirements-extractor` agent, then the ranker. role-intake keeps only the company, role and industry research.
2. The requirements move out of `research.md` (`## Critical Requirements`) into `jd_needs.md`, so the text exists once. Keep each requirement's Type and Source; gap analysis uses Type, and the extraction check uses Source.
3. The extraction check (`role_intake_qc.py` I7: requirement text keeps the JD's modifiers) moves to `role_classify_qc.py`.
4. Readers switch to `jd_needs.md`: `retrieval_payload.py`, `gap_context.py`, `gap_assemble.py`, `gap_qc.py`, `assemble.py research`, and the retrieval, gap-analysis and cv-targeted skills and agents that name Critical Requirements (grep for it).
5. Existing application folders (about 23 have the table) are converted by a script, not handled by a fallback.

Before building: show the user the `jd_needs.md` layout for one requirement and get approval. Then build, test, see each check fail, and present the result in a few lines.

## After that

1. Run `/role-classify` on Otsuka APP-026, Acadia APP-025 and Jazz APP-028. The user reviews each `jd_needs.md` one section at a time, exact text, never paraphrased; "close enough" is the bar.
2. Close #89.

## BeOne APP-027 classification: fix before its CV

The classification was rerun 2026-11-10 (level ic became leadership, function-lead; orientation data-analytics became transformation-strategy primary). The reviewer then found two faults, not yet fixed: the industry rationale uses "small-molecule BRUKINSA", which is in neither the JD nor the research; the orientation rationale picks transformation-strategy with a test the rule files do not contain. Rerun role-classify Phase 2 before BeOne goes to retrieval. Not part of the ranker work; do not raise it during ranker reviews.

## Set aside for a separate fix (requirement extractor)

Each breaks the rule that a requirement carries the JD's wording, nothing added or dropped. A check comparing each requirement's text with the JD sentence it quotes could catch all four.

- WCT APP-007 #21: the middle of the JD sentence was dropped.
- Genmab APP-018 #41: "recognized" was added.
- BeOne APP-019 #7: an extraction note was added to the text.
- Formation Bio APP-010 #17: "Comfort operating in" was added, turning a company description into a requirement.

## How to work with him

- One point and one question per message, a few lines, his words, no coined terms.
- Show file text exactly as written, never paraphrased or shortened.
- Stay on the named goal; do not raise findings outside it.
- When a skill is split or work is moved, list every step doing the same kind of work and ask whether it moves too.
