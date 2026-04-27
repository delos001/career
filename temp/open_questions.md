# Career Repo Open Questions

Items blocking specific work that need answers now. When answered, move resolved decision to `design_decisions.md` and remove from this file. Protocol in memory `process_session_protocol.md`.

## Active

### foundation-execution-order
In what order across the four knowledge documents and four axis builder skills?
- (a) Migrate existing knowledge docs by hand → build knowledge-doc builder skills against migrated examples → build axis builders.
- (b) Axis builders first (greenfield) → migrate knowledge docs → build knowledge-doc builders.
- (c) Knowledge docs only via builder skills (no manual migration); start with smallest.
- (d) Interleave (axis builders + knowledge-doc audit independent).
- Triggered by: operating-model lock-in.
- Blocks: starting foundation work.
- Refs: `approach-foundation-first`, `four-builders-axis-parity`, `knowledge-document-roster`.

### knowledge-doc-update-mechanism
Hand-edit, builder-skill refresh-mode, or one-time migration script for existing knowledge documents?
- (a) Hand-edit: fastest, no reusable skill.
- (b) Builder-skill refresh: slower this round; produces reusable refresh capability.
- (c) Migration scripts for mechanical pieces; hand-edit the rest.
- Triggered by: foundation execution decision.
- Blocks: knowledge-document updates.
- Likely resolved by `foundation-execution-order` answer.
- Refs: `user-info-rename-and-schema`, `career-narratives-schema`, `positioning-schema`, `experience-inventory-domain-scoping`, `builder-mode-parameter`.
