# Build Issues

Auto-appended log of unresolved QC issues from axis-builder runs that completed in provisional mode. Each section is one build run. Triage and address; remove the section when the underlying value file no longer carries `provisional: true`.

## cv-targeted APP-007 (Worldwide Clinical Trials, Sr Director Data Intelligence) — 2026-06-04

Shipped provisional at the Phase 4 3-iteration cap. One unresolved finding:

- **L1 length guard:** estimated ~149 rendered lines vs the ~147 leadership ceiling (~2 lines over). All other mechanical and judgment checks pass. L1 is a heuristic estimate; authoritative length is confirmed at the render stage (cv-render). If the render exceeds 3 pages, trim ~2 lines from the lowest-relevance older-role bullets (AbbVie/Amgen/Quintiles) with real render data.

Not a defect in the CV content; carried to handoff. See `personal/applications/wct_APP-007_2026-06/cv_collaboration_log.md` for the full QC trail.

## cv-targeted APP-008 (Medable, Leader of Clinical Monitoring (Digital & AI Transformation)) — 2026-06-05

Shipped provisional at the Phase 4 3-iteration cap. One unresolved finding:

- **L1 length guard:** estimated 4 pages (~157 rendered lines) vs the 3-page leadership ceiling (~147-line boundary), so roughly 10 estimated lines over, a larger residual than APP-007's 2-line case. All other mechanical checks (C1-C5, B1-B2, S1-S3, F1-F2, N1-N2) pass and judgment QC passes. The cv-architect compressed twice (172 -> 157 estimated lines; cut 2 BioMarin bullets by elevation, restructured the BioMarin title progression for C5, tightened multiple bullets) without gutting stakeholder-vetted content, then stopped per the cv-length-handling guidance rather than cut protected wins against a conservative estimate. L1 is a heuristic estimate; authoritative length is confirmed at the render stage (cv-render). Because the residual is non-trivial (~10 lines, not ~2), the real render has a genuine chance of exceeding 3 pages; if it does, trim against real pagination at the render stage, targeting lowest-relevance older-role bullets (eClinical/AbbVie/Quintiles) and any remaining BioMarin redundancy before touching protected content. Tiered-L1 estimate redesign remains deferred.

Not a content defect; carried to handoff. See `personal/applications/medable_APP-008_2026-06/cv_collaboration_log.md` for the full QC trail.

## cv-targeted APP-009 (BeOne, Associate Director, AI and Machine Learning) — 2026-06-09

Shipped provisional at the Phase 4 3-iteration cap. One unresolved finding:

- **L1 length guard:** estimated 4 pages vs the 3-page leadership ceiling (~147-line boundary). All other mechanical checks (C1-C5, B1-B2, S1-S3, F1-F2, N1-N2) pass and judgment QC passes. **Re-run 2026-06-09 under the new importance-aware coverage rule** (`cv-structure.md` rule 1 "Weighted coverage before duplication"): the rule confirmed it works (duty-derived/contextual now ride-along, 3 within-role subheadings vs 5, 42 cited entries vs 49) and reduced the final draft from ~181 to ~168 estimated lines, but did NOT bring this deep profile under 3 pages. So ~168 lines / ~21 estimated lines over (improved from the pre-weighted ~34-over, still larger than APP-007 ~2 / APP-008 ~10). The cv-architect did not gut stakeholder-vetted content (EX-076 238-site differentiator, EX-107/EX-108 applied-ML bullets, governance/MLOps arc) against the estimate. L1 is a heuristic estimate; authoritative length is at the render stage (cv-render). The real render has a real chance of exceeding 3 pages; if it does, candidates are the lowest-relevance older-role bullets (AbbVie/PRA/Amgen) before touching protected content, or accepting a 4-page CV for a deep senior-IC profile. **Conclusion from the re-run:** for profiles this deep, the coverage rule alone cannot force a 3-page fit; if 3 pages is a hard target, additional levers (per-role minimum-bullet rule, Earlier-Roles compression, Selected-Projects gating) need attention. Tiered-L1 estimate redesign remains deferred.

Not a content defect per se; carried to handoff. See `personal/applications/beone_APP-009_2026-06/cv_collaboration_log.md` for the full QC trail.


## preparation-screen / preparation-interview: no home for a late recruiter round — 2026-08-03

Tracked as [#62](https://github.com/delos001/career/issues/62). That issue is the working copy; this entry is the run record.

Surfaced running APP-020 (Faro, Director Implementation Services). The recruiter
round with internal recruiting was scheduled AFTER the hiring-manager round, which
neither skill anticipates.

- `preparation-screen` owns recruiter rounds, but its Phase 0 UPDATE mode fires
  whenever `interview_prep.md` exists and then walks every main-body section for
  confirm/amend. It has no path to add a per-interview Appendix block; the block is
  written only on the CREATE path in Phase 3. So a recruiter round that follows a
  post-screen round cannot be represented in the cumulative doc by the skill that
  owns it.
- `rules/interview-types/` carries `hiring-manager.md`, `peer-team.md` and
  `executive.md`. There is no recruiter file, so `preparation-interview` has no
  audience rule file to load for this case.

Workaround used this run: ran `preparation-interview` in EXTEND mode, which handles
the cumulative architecture correctly, and substituted `preparation-screen`'s Phase 3
recruiter-specific emphasis rules (comp posture, process intel, flagging which
Question Bank items to hold for people with real authority) in place of the missing
rule file. Stage label `Recruiter Screen`, matching the existing convention and
`interview_lifecycle`'s `--stage`.

Two candidate fixes, not yet decided:

1. Add `rules/interview-types/recruiter.md` and let `preparation-interview` own every
   round including recruiter ones, reducing `preparation-screen` to the create-first-doc
   case. Cleanest, and matches how the architecture already works.
2. Give `preparation-screen` an EXTEND path mirroring `preparation-interview`'s Phase 0,
   so both skills can add an Appendix block to an existing cumulative doc. More
   duplication between the two skills.

Option 1 is the smaller change and removes a skill boundary that has now cost a
decision mid-run.

## preparation-interview: no QC check that the cue-card and the question checklist agree - 2026-08-05

Tracked as [#67](https://github.com/delos001/career/issues/67). That issue is the working copy; this entry is the run record.

Surfaced running APP-020 (Faro, Director Implementation Services), peer/team round.

The Appendix block's prioritized Question Bank list is the only place a round's
ASKING order is recorded. `interview-notes` projects that list into the round's
`### Questions to Ask` checklist in `interview_notes.md`. On this run the projection
preserved WHICH questions were priority (the `(P)` markers matched the Appendix list
exactly) but dropped the ORDER, emitting the checklist in Question Bank physical order
instead. The result contradicted the cue-card sitting directly above it: the cue-card
said "get to Q8 early" while the checklist put Q8 sixth, below three non-priority
questions.

No check catches this. `prep_interview_qc.py` validates the prep doc's structure and
X2 confirms every Q-label reference resolves, but nothing compares the projected
checklist against the Appendix list that produced it, and nothing reads
`interview_notes.md` at all from this skill's QC.

Fixed for this run by hand, and `SKILL.md` Phase 4 now requires the Appendix priority
list to be written in asking order and carried verbatim into the checklist. That is a
model-followed instruction, not an enforced one, so the failure can recur silently.

**2026-08-06.** The Phase 4 rule landed in the one document that does NOT write the
checklist. `interview-notes/SKILL.md` Phase 2 and the template's Appendix block comment
both still said to order the projection by the shared Question Bank's topical order, so
the next run would have re-sorted the asking order away by following its own explicit
instruction. Both are now aligned with Phase 4 (priority items verbatim in the Appendix's
order, non-priority tail below in topical order), and the reversal of the 2026-07-07
projection clause is recorded as `appendix-priority-list-is-asking-order-2026-08`. The
enforcement gap and its ownership question are unchanged and still open.

Candidate check, not yet designed:

- A cross-artifact check that reads the round's Appendix block and the matching
  `interview_notes.md` round section, then asserts the checklist contains exactly the
  prioritized questions in the Appendix's order, with non-priority questions below
  them. Needs a decision on ownership first: `prep_interview_qc.py` does not currently
  read `interview_notes.md`, and `interview-notes` is the sole writer of that file, so
  the check may belong to that skill instead.
