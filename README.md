# career

End-to-end career maintenance and career path support.

## Approach

Human-gated AI workflow built on Claude Code. Moderate complexity and nuance with explicit user checkpoints rather than full autonomy. Claude Code is the primary orchestrator; Python scripts handle deterministic logic (retrieval, formatting, validation); LangGraph is used only for the CV generation loop. Retrieval is slice-based against structured documents; whole documents are not loaded into skill context. Ground-up rebuild of the prior `career_development` repo, designed to avoid the context-bloat failure that made its predecessor unusable.

## Repo Structure

```
career/
├── .claude/
│   ├── skills/                                    # Pattern A, auto-discovered. Kebab folder names.
│   │   ├── role-evaluation/SKILL.md
│   │   ├── cv-targeted/SKILL.md
│   │   ├── cv-general/SKILL.md
│   │   ├── interview-prep/SKILL.md
│   │   ├── interview-capture/SKILL.md
│   │   ├── interview-followup/SKILL.md
│   │   ├── career-brief/SKILL.md
│   │   ├── experience-inventory/SKILL.md
│   │   ├── career-narratives/SKILL.md
│   │   ├── positioning/SKILL.md
│   │   ├── knowledge-update/SKILL.md              # mode parameter (adhoc / inline)
│   │   ├── orientation-builder/SKILL.md
│   │   ├── industry-builder/SKILL.md
│   │   ├── specialty-builder/SKILL.md
│   │   ├── level-builder/SKILL.md
│   │   └── work-state-builder/SKILL.md
│   ├── agents/                                    # flat
│   │   ├── role_research.md
│   │   ├── organization_research.md
│   │   ├── industry_research.md
│   │   ├── specialty_research.md
│   │   ├── orientation_research.md
│   │   ├── level_research.md
│   │   ├── work_state_research.md
│   │   ├── qc_cv_format.md
│   │   ├── qc_cv_structural.md
│   │   └── qc_cv_content.md                       # qc agents grow as identified
│   └── settings.json                              # optional
├── rules/
│   ├── global_rules.md                            # three rules only
│   ├── tags.yaml                                  # globals: Role Level, Purpose
│   ├── orientations/
│   │   ├── transformation-strategy.md
│   │   ├── data-analytics.md
│   │   ├── process-operations.md
│   │   ├── platform-technology.md
│   │   └── cv_dual_orientation_composition.md
│   ├── industries/
│   │   ├── registry.md
│   │   └── pharma.md                              # plus others as built
│   ├── specialties/
│   │   ├── registry.md
│   │   ├── clinical-operations.md
│   │   ├── data-engineering.md
│   │   ├── ai-engineering.md
│   │   ├── quality-compliance.md
│   │   └── people-leadership.md
│   ├── levels/
│   │   ├── ic.md
│   │   └── leadership.md
│   ├── work-states/
│   │   ├── greenfield.md
│   │   ├── scaling.md
│   │   ├── mature.md
│   │   ├── turnaround.md
│   │   ├── post-merger-integration.md
│   │   ├── divestiture.md
│   │   └── pivot.md
│   ├── organizations/
│   │   ├── org_industry.md
│   │   └── company-slugs.yaml
│   ├── narratives/
│   │   ├── decision_adr.md
│   │   ├── decision_personal.md
│   │   ├── story_atola.md
│   │   ├── story_star.md
│   │   └── story_personal.md
│   ├── format_specs/
│   │   └── cv.md
│   └── quality_control/                           # qc_<scope>_<aspect>
│       ├── qc_cv_format.md
│       ├── qc_cv_structural.md
│       └── qc_cv_content.md
├── templates/
│   ├── interview_completion.md
│   ├── interview_scratch.md
│   └── recruiter_pitch_template.md
├── scripts/
│   ├── retrieval/
│   ├── resolvers/
│   ├── format/
│   ├── registry/
│   ├── migration/
│   └── display/                                   # introduce.py + introductions.yaml
├── outputs/                                       # temporary holding for deliverables
├── support/                                       # scaffolding for fresh user setup
│   └── knowledge_repo_scaffolding/                # final folder layout deferred
│       ├── User_Info.md
│       ├── README.md
│       ├── SETUP.md
│       └── .gitignore
├── personal/                                      # nested private repo; not shared
│   ├── knowledge/
│   │   ├── User_Info.md
│   │   ├── Experience_Inventory.md
│   │   ├── Career_Narratives.md
│   │   └── Positioning.md
│   ├── sessions/
│   │   └── <slug>-NNN_session-log.md
│   ├── applications/
│   │   └── <slug>-NNN-<role-slug>-<yyyy-mm>/
│   │       ├── gap-analysis_<slug>-NNN.md
│   │       ├── cv_<slug>-NNN.docx
│   │       ├── interview-prep_<slug>-NNN.md
│   │       ├── interview-completion_<slug>-NNN.md
│   │       ├── interview-scratch_<slug>-NNN.md
│   │       └── interview-followup_r<N>_<slug>-NNN.md
│   ├── do-not-pursue/
│   └── config.yaml
├── temp/                                          # live design state during pre-build
│   ├── design_decisions.md
│   ├── deferrals.md
│   └── open_questions.md
├── CLAUDE.md
├── COMPONENTS.md                                  # registry for skills, sub-agents, scripts
└── README.md
```

## Out-of-Repo References

- **Memory:** `~/.claude/projects/C--Users-delos-code-career/memory/` is a junction to `engops/claude-config/projects/career/memory/`. User-scoped, backed up in engops, not in the career repo.
- **Skill authoring template:** `engops/cheatsheets/skill-templates/human-gated-workflow.md`.

## Key Concepts

- **Five orthogonal axes.** Orientation, Industry, Specialty, Level, Work-state govern deliverable content and voice. Each axis is a discrete categorical dimension; partial-match scoring runs through adjacency maps in each value's frontmatter.
- **Application ID.** Compound `<company-slug>-NNN`. User-entered slug, per-company counter. Example: `pfizer-001`.
- **Session Log.** `personal/sessions/<slug>-NNN_session-log.md`. Written regardless of apply decision; enables resume.
- **Personal nested repo.** `personal/` holds PII and knowledge documents.
- **COMPONENTS.md.** Single registry for every skill, sub-agent, and standalone script: inputs, outputs, triggers, update triggers.

## Status

Pre-build. Foundation block (knowledge documents creatable + five-axis builders working) is the next execution target. Per-skill detail design happens at each skill's build time.

## References

- `temp/design_decisions.md` — closed design decisions
- `temp/deferrals.md` — deferred items
- `temp/open_questions.md` — items blocking specific work
- `engops/runbooks/claude-code.md` — Claude Code setup reference
- `engops/cheatsheets/claude-code.md` — Claude Code day-to-day reference
