# JD needs ranker: redesign handoff (GitHub #89)

Status 2026-11-10, second session closed. The plan this belongs to: `design/cv_persuasion_plan.md` (step 1).

## Where it stands

- The user approved the ranker's six steps one at a time, and `.claude/agents/jd-needs-ranker.md` is rewritten as those steps. Design entry: `design_decisions.md` `requirement-kinds-2026-11`.
- Requirement kinds and their tests: `rules/jd-requirement-kinds.md`. Every kind and wording list was approved by the user.
- role-classify writes its result to `jd_needs.md` in each application folder (the job, each need with its requirements' text and kinds, then Qualifications, then Not ranked). Written by `role_classify_assemble.py needs`; read and filtered by `scripts/requirement_kinds.py`; checked by `role_classify_qc.py` C6. Not ranked rows never reach retrieval or gap analysis. All 73 tests pass; the filter and the text-match check were seen to fail.
- BeOne APP-027: `jd_needs.md` written and the ranking confirmed by the user. Two instruction faults found and fixed on the way: `stated` was defined by where the label's words came from (now: who made the grouping); step 3 contradicted it.
- To watch on the next runs: working style the JD ties to a function through other sentences was made its own need (BeOne rows 7, 9); one JD line split across two needs (rows 17, 18); the job description's "Leads, does, or both" line explains its reasoning instead of giving the answer and its sources.
## Requirement extraction moved into role-classify: built

Design entry: `design_decisions.md` `requirements-in-jd-needs-2026-11`. role-classify now extracts (1a), checks the wording against the JD (1b, `role_classify_qc.py` C7 and C8), then ranks (1c). The requirements live only in `jd_needs.md`; `research.md` no longer has a Critical Requirements section. All 74 tests pass; each new or moved check was seen to fail.

Existing folders, decided by the user: only open applications were converted. Medtronic APP-024, Summit APP-023 and BeOne APP-027 were converted; the 22 closed ones were left as they are, since nothing reruns skills on them. Acadia, Otsuka and Jazz were left unconverted on purpose: with no `jd_needs.md`, `/role-classify` starts at a fresh extraction, which is the test.

- The three converted folders fail C8 on every row whose Source names a JD section instead of quoting the line. The old extractor wrote Sources that way. Nothing downstream runs C8; re-extract only if role-classify is rerun on one of them.
- BeOne rows 11 and 24 had dropped "preferred" and "might"; both fixed by hand.
- C8 catches only the softening words listed in `config.yaml` `requirement_qualifiers`. Add a word when a run shows one getting through.

## Next

1. Start a new session. Run `/role-classify` on Otsuka APP-026, Acadia APP-025 and Jazz APP-028. The user reviews each `jd_needs.md` one section at a time, exact text, never paraphrased; "close enough" is the bar.
2. Close #89.

## BeOne APP-027 classification: fix before its CV

The classification was rerun 2026-11-10 (level ic became leadership, function-lead; orientation data-analytics became transformation-strategy primary). The reviewer then found two faults, not yet fixed: the industry rationale uses "small-molecule BRUKINSA", which is in neither the JD nor the research; the orientation rationale picks transformation-strategy with a test the rule files do not contain. Rerun role-classify Phase 2 before BeOne goes to retrieval. Not part of the ranker work; do not raise it during ranker reviews.

## Old extractor faults (closed applications, left as they are)

Each breaks the rule that a requirement carries the JD's wording, nothing added or dropped. C8 now checks new extractions for dropped softening words; it does not catch added words.

- WCT APP-007 #21: the middle of the JD sentence was dropped.
- Genmab APP-018 #41: "recognized" was added.
- BeOne APP-019 #7: an extraction note was added to the text.
- Formation Bio APP-010 #17: "Comfort operating in" was added, turning a company description into a requirement.

## How to work with him

- One point and one question per message, a few lines, his words, no coined terms.
- Show file text exactly as written, never paraphrased or shortened.
- Stay on the named goal; do not raise findings outside it.
- When a skill is split or work is moved, list every step doing the same kind of work and ask whether it moves too.
