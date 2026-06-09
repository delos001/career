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

