# career

end to end career maintenance and career path support

## Approach

Human-gated AI workflow built on Claude Code. Moderate complexity and nuance with explicit user checkpoints rather than full autonomy. Claude Code is the primary orchestrator; Python scripts handle deterministic logic (retrieval, formatting, validation); LangGraph is used only for the CV generation loop where multi-branch QC warrants it. Retrieval is slice-based against structured documents — whole documents are not loaded into skill context. Ground-up rebuild of the prior `career_development` repo, designed to avoid the context-bloat failure that made its predecessor unusable.

## Repo Structure

```
career/
├── .claude/
│   ├── skills/                                    # Pattern A, auto-discovered
│   │   ├── role_evaluation/SKILL.md
│   │   ├── cv_targeted/SKILL.md
│   │   ├── cv_general/SKILL.md
│   │   ├── interview_prep/SKILL.md
│   │   ├── interview_capture/SKILL.md
│   │   ├── interview_followup/SKILL.md
│   │   ├── career_brief/SKILL.md
│   │   ├── experience_inventory/SKILL.md
│   │   ├── career_narratives/SKILL.md
│   │   ├── positioning/SKILL.md
│   │   ├── knowledge_update/SKILL.md
│   │   ├── specialty_builder/SKILL.md
│   │   ├── domain_builder/SKILL.md
│   │   └── level_builder/SKILL.md
│   ├── agents/                                    # Pattern A sub-agents, flat
│   │   ├── role_research.md
│   │   ├── organization_research.md
│   │   ├── domain_research.md
│   │   ├── specialty_research.md
│   │   ├── level_research.md
│   │   ├── qc_cv_format.md
│   │   ├── qc_cv_structural.md
│   │   └── qc_cv_content.md                       # more QC agents added as identified
│   └── settings.json                              # optional project-level
├── rules/
│   ├── global_rules.md                            # minimal cross-skill rules
│   ├── tags.yaml                                  # structured data, script-consumed
│   ├── specialties/
│   │   ├── transformation_strategy.md
│   │   ├── data_analytics.md
│   │   ├── process_operations.md
│   │   ├── platform_technology.md
│   │   └── cv_dual_specialty_composition.md
│   ├── domains/
│   │   └── clinical_development.md
│   ├── levels/
│   │   ├── ic.md
│   │   └── leadership.md
│   ├── organizations/
│   │   ├── org_industry.md                        # industry research scoping
│   │   ├── org_maturity.md                        # CV context framing
│   │   └── company_slugs.md                       # slug registry for app IDs
│   ├── narratives/
│   │   ├── decision_adr.md
│   │   ├── decision_personal.md
│   │   ├── story_atola.md
│   │   ├── story_star.md
│   │   └── story_personal.md
│   ├── format_specs/
│   │   └── cv.md
│   └── quality_control/                           # qc_<scope>_<aspect> naming
│       ├── qc_cv_format.md
│       ├── qc_cv_structural.md
│       └── qc_cv_content.md
├── templates/                                     # blank skeletons, copied per use
│   ├── interview_completion.md
│   └── interview_scratch.md
├── scripts/
│   ├── retrieval/                                 # slice knowledge docs by key/tag
│   ├── resolvers/                                 # e.g., application ID assignment
│   ├── format/                                    # e.g., python-docx CV renderer
│   └── display/                                   # orient.py + orientations.yaml; sibling catalogs added as needed
├── outputs/                                       # temporary holding for deliverables
├── personal/                                      # nested private repo; PII, not shared
│   ├── knowledge/
│   │   ├── experience_inventory.md
│   │   ├── career_narratives.md
│   │   ├── positioning.md
│   │   └── contact_info.md
│   ├── sessions/
│   │   └── <slug>-NNN_session_log.md              # one per evaluation
│   ├── applications/
│   │   └── <slug>-NNN_<role_slug>_<yyyy-mm>/      # only if user decides to apply
│   │       ├── gap_analysis_<slug>-NNN.md
│   │       ├── cv_<slug>-NNN.docx
│   │       ├── interview_prep_<slug>-NNN.md
│   │       ├── interview_completion_<slug>-NNN.md
│   │       ├── interview_scratch_<slug>-NNN.md
│   │       └── interview_followup_<slug>-NNN_r<N>.md
│   ├── do_not_pursue/                             # evaluated roles not pursued
│   ├── questions_library.md
│   └── config.yaml                                # paths, output destinations, user name
├── CLAUDE.md                                      # project-level context for Claude Code
└── README.md
```

## Out-of-Repo References

- **Memory:** `~/.claude/projects/C--Users-delos-code-career/memory/` is a junction to `engops/claude-config/projects/career/memory/`. Memory is user-scoped, backed up in engops, not in the career repo.
- **Skill authoring template:** `engops/cheatsheets/skill-templates/human-gated-workflow.md` — referenced when writing new skills.

## Key Concepts

- **Specialty, Domain, Level.** Three orthogonal axes governing deliverable content and voice. Org maturity is a narrow modifier on CV context framing, not a fourth axis.
- **Application ID.** Compound format `<company-slug>-NNN`. User-entered company slug, per-company counter. Example: `pfizer-001`.
- **Session Log.** `personal/sessions/<slug>-NNN_session_log.md`. Written regardless of whether the user applies; enables workflow resume mid-stream.
- **Personal nested repo.** `personal/` holds PII and knowledge documents. Kept private; does not ship with the career repo if shared.

## Status

Currently in design phase. Structural decisions are settled; skill, agent, rule, and script content is being authored next. Source of truth during build is `temp/design_decisions.md`.

## References

- `temp/design_decisions.md` — full design decisions record
- `engops/runbooks/claude-code.md` — Claude Code setup reference
- `engops/cheatsheets/claude-code.md` — Claude Code day-to-day reference
