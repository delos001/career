# Career Repo Open Questions

Items blocking specific work that need answers now. When answered, move resolved decision to `design_decisions.md` and remove from this file. Protocol in memory `process_session_protocol.md`.

## Active

### retrieval-method-for-discrete-elements
How does cv_targeted retrieve and filter across the five axes? Pure tag-based (every entry tagged on every axis) vs hybrid (some axes tagged, others retrieved semantically) vs other. Tagging burden across ~190 inventory entries is the cost. Decision needed before adding `Orientation:` and `Work-state:` fields to inventory entry schema and before deciding whether Tools becomes a tag dimension.
- Triggered by: Work-state axis promotion raised concern about per-entry tagging burden across all five axes.
- Blocks: finalizing inventory entry schema (Orientation/Work-state fields), Tools tag-vs-reference decision, applying tagging to existing entries.
- Refs: `five-orthogonal-axes`, `experience-inventory-domain-scoping`, `cv-targeted-hybrid-retrieval`, `stack-retrieval`.

### knowledge-doc-update-mechanism
Hand-edit, builder-skill refresh-mode, or one-time migration script for existing knowledge documents?
- (a) Hand-edit: fastest, no reusable skill.
- (b) Builder-skill refresh: slower this round; produces reusable refresh capability.
- (c) Migration scripts for mechanical pieces; hand-edit the rest.
- Triggered by: foundation execution decision.
- Blocks: knowledge-document updates.
- Downstream of: `foundation-execution-order`.
- Refs: `user-info-rename-and-schema`, `career-narratives-schema`, `positioning-schema`, `experience-inventory-domain-scoping`, `builder-mode-parameter`.
