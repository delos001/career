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

- **L1 length guard:** estimated 4 pages (~181 rendered lines) vs the 3-page leadership ceiling (~147-line boundary), so roughly 34 estimated lines over - a notably larger residual than APP-007 (~2 lines) or APP-008 (~10 lines). All other mechanical checks (C1-C5, B1-B2, S1-S3, F1-F2, N1-N2) pass and judgment QC passes (including a full re-verify after a 12-bullet compression pass introduced no drift). The cv-architect compressed across three fix passes (194 -> 186 -> 181 estimated lines: 16 bullets then 3 + ~12 more by elevation, plus the Earlier-Roles reorder) without gutting stakeholder-vetted content (the EX-076 238-site statistical-inference differentiator, the EX-107/EX-109/EX-114 applied-ML bullets, the governance/MLOps arc, the modern-AI Selected Projects), then stopped per the cv-length-handling guidance rather than cut protected wins against a conservative estimate. L1 is a heuristic estimate; authoritative length is confirmed at the render stage (cv-render). Because the residual is large (~34 lines, not ~2-10), the real render has a high likelihood of exceeding 3 pages; if it does, the user should make genuine content decisions at the render stage - candidates are the lowest-relevance older-role bullets (AbbVie/PRA/Amgen) and any remaining BioMarin redundancy before touching protected content, or accepting a 4-page CV for a deep senior-IC profile. Tiered-L1 estimate redesign remains deferred.

Not a content defect per se; carried to handoff. See `personal/applications/beone_APP-009_2026-06/cv_collaboration_log.md` for the full QC trail.

