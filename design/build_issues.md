# Build Issues

Auto-appended log of unresolved QC issues from axis-builder runs that completed in provisional mode. Each section is one build run. Triage and address; remove the section when the underlying value file no longer carries `provisional: true`.

## cv-targeted APP-007 (Worldwide Clinical Trials, Sr Director Data Intelligence) — 2026-06-04

Shipped provisional at the Phase 4 3-iteration cap. One unresolved finding:

- **L1 length guard:** estimated ~149 rendered lines vs the ~147 leadership ceiling (~2 lines over). All other mechanical and judgment checks pass. L1 is a heuristic estimate; authoritative length is confirmed at the render stage (cv-render). If the render exceeds 3 pages, trim ~2 lines from the lowest-relevance older-role bullets (AbbVie/Amgen/Quintiles) with real render data.

Not a defect in the CV content; carried to handoff. See `personal/applications/wct_APP-007_2026-06/cv_collaboration_log.md` for the full QC trail.

