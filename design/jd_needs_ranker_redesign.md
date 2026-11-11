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

## Otsuka APP-026: Phase 1 run and confirmed, 2026-11-10

Run through Phase 1 only (the user's choice: Phase 2 would overwrite the classification the submitted CV was built from, so C5 fails on the missing tier). `jd_needs.md` holds 16 needs, every section confirmed by the user. Fixed on the way:
- The extractor quoted heading names in its "also" pointers; line 42 now forbids it.
- C8 failed a correct split of one JD sentence; a modifier now must survive on some row of the clause, and `qc-role-classify` check 3 judges carry-over (`requirements-in-jd-needs-2026-11`).
- The ranker wrote the JD words in parentheses on every Kind line; single-kind rows now carry the kind name alone (step 1). Otsuka's file predates this.

Watch items seen: row 22 split from row 21's JD line into the leading-people need, on purpose. The job description's lead-or-do line now gives the answer and its sources. The extractor carried a shared word across a split on rows 37, 50 and 56, which C8 does not check for.

## Acadia APP-025: Phase 1 run twice, reviewed by qc-role-classify, 2026-11-10

The user confirmed the job description, then had `qc-role-classify` (checks 3 and 4) review the rest instead of walking each section. Three faults fixed for future runs, then Phase 1 rerun (47 rows became 57) and reviewed again:
- Role statement read as its first sentence only, so Applied AI lost its signal; the ranker's step 4 now defines the statement as the whole opening paragraph. Held on the rerun. Replaced 2026-11-11, since Jazz's statement spans two paragraphs and JDs have no standard layout: the ranker names the role statement sentences by what they say (step 2, a `Role statement` line in the job), and C6 checks every `role-statement` quote sits in one of them.
- The extractor's own generic-skills filter dropped "Balances competing priorities and deadlines"; removed, the ranker alone judges boilerplate (`requirement-kinds-2026-11`). Held.
- Split sentences lost a half (four clauses); the extractor now makes every part a row. Held.

Second review: rows 47 and 48 labeled Means where the kinds test says Function; left, since placement and downstream are unaffected. Row 38 lost "10 years" in a split; hand-edited to the whole sentence, as the reviewer is the designed backstop for carry-over.

## Jazz APP-028: Phase 1 run, reviewed by qc-role-classify, 2026-11-10

Extraction passed first time (41 rows); all 8 checks pass. The "primary focus" paragraph that ranked last on the old ranker is now N-01. One review finding: row 6 labeled Working style where the test says Function; left, same class as Acadia rows 47 and 48. Watch: if a kind slip ever moves a row into another need or forms its own need, fix the ranker then.

## Next

#89 closed 2026-11-10. Next is `design/cv_persuasion_plan.md` steps 2 to 7 (#88).

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
