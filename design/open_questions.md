# Career Repo Open Questions

Items blocking specific work that need answers now. When answered, move resolved decision to `design_decisions.md` and remove from this file. Protocol in memory `process_session_protocol.md`.

## Active

### Role extraction: the user's proposed paths (raised 2026-11-24, testing)
Two steps: split the JD into a useful form, then apply meaningful categories that retrieval, gap analysis and CV writing can use. The user proposed five paths, usable alone or in combination:
1. **Slot form after semantic role labeling** (PropBank: who acts, what is acted on, with what, how, why). A fixed form per JD unit; the model copies exact words into each slot or leaves it empty, so it never decides how many parts a sentence has, and most labels follow from the slot. Status: tested twice; details below.
2. **spaCy grammar parser.** Parse each sentence into verb, objects and modifiers by script. Status: untested. Likely fit: splitting lists under one verb and keeping a method inside its work phrase, both held below.
3. **Yes/no questions instead of split rules.** Fixed questions the model answers to make each categorization easier to decide. Status: untested.
4. **Dense X Retrieval propositions.** Split text into atomic, self-contained statements, one fact per unit, so one tag per unit. Catch: it rewrites the text, so each proposition must record which original words it came from. Status: untested.
5. **Trained classifier.** A model that only assigns categories, trained on phrases already labeled from the JDs in the repo. Status: untested; needs a labeled set first.

Also proposed (by Claude, not the user): a hand-labeled reference JD the model labels against. Overlaps with path 5's need for a labeled set.

Added by Claude from research, 2026-11-24 (each untested):

6. **Map phrases to the O*NET content model.** O*NET already publishes categories close to the slots (Work Activities, Knowledge, Technology Skills and Tools, Abilities, Work Styles, Work Context, Education and Experience), each with a maintained list of descriptors. Each JD phrase is matched by embedding similarity to its nearest descriptor, and the descriptor's category becomes the slot, so the definitions come with thousands of published examples nobody writes. The same descriptors could index the profile inventory, so JD and CV evidence meet in one vocabulary.
7. **GLiNER zero-shot span extraction.** A small local model (NAACL 2024) takes the slot names as plain labels and returns exact text spans with a confidence score, with no prompt prose. Low-score spans go to review, and the model can be fine-tuned on a hand-labeled set; SkillSpan, a public set of job-posting sentences labeled for skill and knowledge spans, could test the Means and Capability boundary.
8. **Multi-run agreement as the review filter. Tried before; rejected.** Run the same form several times and send only disagreements for review. The user tried this several times: it did not help, sifting the disagreements was heavy work, and runs that agreed were still wrong. Do not propose again.
9. **SetFit for path 5.** SetFit trains a classifier from about 8 to 16 labeled phrases per category on a laptop in minutes, competitive with full fine-tuning in its published benchmarks. It makes path 5 feasible with one or two hand-labeled JDs instead of a large training set.

**Candidate combined path (user, 2026-11-24; untested).** Combines paths 2 and 6: (1) a slot form aligned to O*NET categories; (2) spaCy splits sentences into parts and parts into phrases; (3) each phrase is mapped to its nearest O*NET descriptor by embedding similarity, below a similarity cut-off it goes to Other.
- Gap: O*NET covers Function, Means, Capability and Qualification, and Setting only partly (its Work Context is conditions, not industry or organization type). Result, Scope, Bar, Role shape, Employment condition and Boilerplate need another source; the spaCy parse can supply the role-in-sentence slots from grammar (a purpose clause for Result, "with" or "for" phrases for Scope).
- Training (path 9): not needed for the split, since spaCy is already trained. Not needed for the mapping at first, since the O*NET descriptors act as the labeled examples; add SetFit only if measured mapping accuracy is poor, for example on pharma or clinical terms.
- Untested risk: spaCy parse quality on long sentences with many parallel clauses (APP-029 S-001).

**Path 1 detail.** Slot definitions live in `rules/jd-processing.md` under `## SPLIT: Units and slots`.
- Principles set by the user: definitions define a concept in plain words a person can read cold; no examples or application rules inside a definition; JD phrasing ("ability to X", "experience doing X") is not a reason to change a definition; definitions are a foundation for later steps, not tuned to an error number.
- Decided: copy-only form, checked by script (0 copy errors in 1,663 slots); Role shape is answered as a choice among its options, not copied; an Other slot shows gaps; Logistic merged into Scope; Bar is its own slot.
- Results (10 JDs, APP-020 to APP-029; reviewer agents judged each slot against the definitions): run 1, 183 errors in 1,530 slots (12%), about 60 from copying into Role shape; run 2 after definition revisions, 154 in 1,663 (9%). Largest remaining: Function vs Means, Capability vs Function. Target agreed: 5%. Reviewer findings are unverified model judgments.
- Open: which path (2 to 7, 9, or the combined path), or the reference JD, to test next. The agreed stop point after run 2 was a method change, not more wording.
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
