# career_development_knowledge

Private repository containing master source documents and session artifacts for the CV generation workflow in [career_development](https://github.com/<your-github-username>/career_development).

This repo is cloned into `career_development/personal/` and is gitignored by the framework repo. Both `knowledge/` and `sessions/` subdirectories are tracked here and pushed to this private repo.

---

## Documents

| File | Purpose | Loaded By |
|---|---|---|
| `Experience_Inventory.md` | Atomic, tagged experience entries across all roles. Authoritative source for tag taxonomy, achievement retrieval, and CV content. | role_evaluation Phase 3a; cv_targeted Phase 2a; cv_general Phase 3a; interview_prep Phase 3a; positioning_builder optional ref |
| `Career_Narratives.md` | Stories (STAR / ATOLA / Personal) and decisions (ADR / Personal) for interview prep and CV anchor bullets. | role_evaluation Phase 3a; cv_targeted Phase 2a; cv_general Phase 3a; interview_prep Phase 3a; career_narratives_builder; positioning_builder optional ref |
| `Positioning.md` | Strategic positioning statements, signature themes, recruiter pitch language. | role_evaluation Phase 3a; cv_targeted Phase 2a; cv_general Phase 3a; interview_prep Phase 3a; career_brief Phase 2a; positioning_builder |
| `Contact_Info.md` | Single source of truth for CV contact line values (name, email, phone, LinkedIn, GitHub, optional website). | cv_targeted Phase 3a; cv_general Phase 5a |
| `Questions_Library.md` | Reusable interview questions accumulated across applications. Created and appended by interview_prep. | interview_prep Phase 4a |

---

## Workflow

Documents are loaded just-in-time by skills in the framework repo. The full loading map is defined in `career_development/README.md`.

Do not modify document structure, tag taxonomy, or schema (Added / Last Used / Last Revised metadata, classification line format, narrative metadata block) without updating the corresponding skill and rule files in the framework repo. The schema contract is documented in the `Knowledge Document Schemas` section of the framework `README.md`.
