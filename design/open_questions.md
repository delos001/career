# Career Repo Open Questions

Items blocking specific work that need answers now. When answered, move resolved decision to `design_decisions.md` and remove from this file. Protocol in memory `process_session_protocol.md`.

## Active

### jd-conclusions-agent (raised 2026-11-20, undecided)
Whether to replace role-extract's splitter, kind labeler, kinds and SPLIT rules with one agent that reads the numbered sentences in `scratch/jd_sentences.md` and writes four conclusions, each quoting exact JD words with the sentence number: (1) ranked needs, required or preferred; (2) results the role exists to achieve; (3) level and scope; (4) the capability behind each need and what would count from another setting.
- Why: the user judges the current process failing. Each new JD needs another split rule, and CVs copied profile entries without rewriting them toward the job's needs or level. A part split on agreed purpose kept failing because whether to split depends on the needs, which are decided later.
- Agreed so far: keep the JD broken into pieces rather than sending the whole JD; the four conclusions are what downstream steps need; stability is measured on the conclusions, not on wording; the CV writer must see a work-first and a result-first option per need; use JD words only where the profile supports an equivalent.
- Proposed steps: conclusions agent; script checking each quote matches its sentence; stability test on several JDs; retrieval scores against capability statements; gap analysis weights by rank and judges transferability; CV writer pairs a need with its result and picks the order; retire splitter, labeler, kinds, SPLIT rules.
- Doubts: one large judgment per JD may vary most on long sentences (APP-029 S-001); retrieval, gap analysis and CV writer each need redesign; untested.
- Evidence: `temp/need_impact_survey.md` (180 result/need clauses across 26 JDs: 113 impact, 52 unsure, 11 need, 4 both; 170 of 180 attached to a work clause).
