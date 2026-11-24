# Career Repo Open Questions

Items blocking specific work that need answers now. When answered, move resolved decision to `design_decisions.md` and remove from this file. Protocol in memory `process_session_protocol.md`.

## Active

### Slot-form role extraction (raised 2026-11-24, testing)
The user's proposal: replace the free split with a fixed form per JD unit, after semantic role labeling (PropBank: who acts, what is acted on, with what, how, why). The model copies exact words into each slot or leaves it empty; it never decides how many parts a sentence has. Slot definitions live in `rules/jd-processing.md` under `## SPLIT: Units and slots`.
- Principles set by the user: definitions define a concept in plain words a person can read cold; no examples or application rules inside a definition; JD phrasing ("ability to X", "experience doing X") is not a reason to change a definition; definitions are a foundation for later steps, not tuned to an error number.
- Decided: copy-only form, checked by script (0 copy errors in 1,663 slots); Role shape is answered as a choice among its options, not copied; an Other slot shows gaps; Logistic merged into Scope; Bar is its own slot.
- Results (10 JDs, APP-020 to APP-029; reviewer agents judged each slot against the definitions): run 1, 183 errors in 1,530 slots (12%), about 60 from copying into Role shape; run 2 after definition revisions, 154 in 1,663 (9%). Largest remaining: Function vs Means, Capability vs Function. Target agreed: 5%. Reviewer findings are unverified model judgments.
- Open: which method to add next, since the agreed stop point was method change, not more wording. Options from the user's research: a hand-labeled reference JD the model labels against (recommended); spaCy grammar parse to split verbs, objects and lists before labeling; yes/no questions per slot boundary; Dense X propositions (rewrites text, needs source tracking); a trained classifier on labeled phrases.
- Held for form design: whether one slot's words may sit inside another's (fragments like Function "applying"); whether lists under one verb are split by script.
- Not yet synced: removed agents jd-activity-extractor and jd-needs-ranker are still referenced in COMPONENTS.md, README.md, several scripts and tests.
- Evidence: `temp/slot_test/` (review, review2, findings, findings2; tally.py and build_review.py rebuild the counts).

### jd-conclusions-agent (raised 2026-11-20, undecided)
Whether to replace role-extract's splitter, kind labeler, kinds and SPLIT rules with one agent that reads the numbered sentences in `scratch/jd_sentences.md` and writes four conclusions, each quoting exact JD words with the sentence number: (1) ranked needs, required or preferred; (2) results the role exists to achieve; (3) level and scope; (4) the capability behind each need and what would count from another setting.
- Why: the user judges the current process failing. Each new JD needs another split rule, and CVs copied profile entries without rewriting them toward the job's needs or level. A part split on agreed purpose kept failing because whether to split depends on the needs, which are decided later.
- Agreed so far: keep the JD broken into pieces rather than sending the whole JD; the four conclusions are what downstream steps need; stability is measured on the conclusions, not on wording; the CV writer must see a work-first and a result-first option per need; use JD words only where the profile supports an equivalent.
- Proposed steps: conclusions agent; script checking each quote matches its sentence; stability test on several JDs; retrieval scores against capability statements; gap analysis weights by rank and judges transferability; CV writer pairs a need with its result and picks the order; retire splitter, labeler, kinds, SPLIT rules.
- Doubts: one large judgment per JD may vary most on long sentences (APP-029 S-001); retrieval, gap analysis and CV writer each need redesign; untested.
- Evidence: `temp/need_impact_survey.md` (180 result/need clauses across 26 JDs: 113 impact, 52 unsure, 11 need, 4 both; 170 of 180 attached to a work clause).
