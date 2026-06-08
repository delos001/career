# career

End-to-end career maintenance and career path support.

## Approach

Human-gated AI workflow built on Claude Code. Moderate complexity and nuance with explicit user checkpoints rather than full autonomy. Claude Code is the primary orchestrator; Python scripts handle deterministic logic (retrieval, formatting, validation); LangGraph is used only for the CV generation loop. Retrieval is slice-based against structured documents; whole documents are not loaded into skill context. Ground-up rebuild of the prior `career_development` repo, designed to avoid the context-bloat failure that made its predecessor unusable.

## Repo Structure

```
career/
├── .claude/
│   ├── skills/                                    # Pattern A, auto-discovered. Kebab folder names.
│   │   └── role-intake/SKILL.md                   # first skill built; more planned (see COMPONENTS.md)
│   ├── agents/                                    # flat; more added as skills are built
│   │   ├── company-research.md
│   │   ├── role-research.md
│   │   ├── industry-research.md
│   │   ├── axis-classifier.md
│   │   └── qc-role-intake.md
│   └── settings.local.json
├── config.yaml                                    # repo-structure constants read by the scripts
├── rules/
│   ├── global-rules.md                            # three rules only
│   ├── tags.yaml                                  # globals: Role Level, Purpose
│   ├── orientations/                              # registry.md + one file per value
│   │   ├── registry.md
│   │   ├── transformation-strategy.md
│   │   ├── data-analytics.md
│   │   ├── process-operations.md
│   │   └── platform-technology.md
│   ├── industries/
│   │   ├── registry.md
│   │   ├── pharma.md
│   │   ├── biotech.md
│   │   ├── cro.md
│   │   └── med-device.md
│   ├── specialties/
│   │   ├── registry.md
│   │   ├── clinical-operations.md
│   │   ├── quality-compliance.md
│   │   ├── data-engineering.md
│   │   ├── ai-engineering.md
│   │   ├── data-science.md
│   │   ├── operations-strategy.md
│   │   └── people-leadership.md
│   ├── levels/
│   │   ├── registry.md
│   │   ├── ic.md
│   │   └── leadership.md
│   ├── work-states/
│   │   ├── registry.md
│   │   ├── greenfield.md
│   │   ├── scaling.md
│   │   ├── mature.md
│   │   ├── turnaround.md
│   │   ├── post-merger-integration.md
│   │   ├── divestiture.md
│   │   └── pivot.md
│   ├── organizations/                             # planned
│   ├── narratives/                                # planned
│   ├── format_specs/                              # planned
│   └── quality_control/                           # planned; qc_<scope>_<aspect>
├── templates/
│   ├── session_log.md
│   └── research_file.md
├── scripts/
│   ├── _config.py                                 # shared: resolves repo root, loads config.yaml
│   ├── app_id.py                                  # next global APP-NNN
│   ├── assemble.py                                # writes role-intake's artifacts from templates
│   ├── cv_to_docx.py
│   ├── ingest/                                    # jd_extract.py
│   └── display/                                   # introduce.py + introductions.yaml
├── outputs/                                       # temporary holding for deliverables
├── support/                                       # scaffolding for fresh user setup (layout planned)
├── personal/                                      # nested private repo; not shared
│   ├── profile/                                   # user-info, inventory, narratives, positioning
│   ├── applications/                              # <SLUG>_APP-NNN_YYYY-MM/ (session_log.md, research.md, gap analysis, cv, ...)
│   ├── do-not-pursue/
│   └── config.yaml                                # reserved for user-specific config; created when first needed
├── design/                                        # live design state
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
- **Application ID.** Global counter `APP-NNN` (e.g. `APP-004`), embedded in the per-job stem `<SLUG>_APP-NNN_YYYY-MM`. `SLUG` is a short user-entered company tag.
- **Session Log.** `session_log.md` inside each application folder (`personal/applications/<SLUG>_APP-NNN_YYYY-MM/`). Created by `role-intake`; downstream skills append their own sections.
- **Personal nested repo.** `personal/` holds PII and profile documents.
- **COMPONENTS.md.** Single registry for every skill, sub-agent, and standalone script: inputs, outputs, triggers, update triggers.

## Status

First skill (`role-intake`) built: JD ingestion, company/role/industry research, five-axis classification, and a session log + research file for downstream gap analysis. Next: axis builder skills, then end-to-end verification of `role-intake`. Per-skill detail design happens at each skill's build time.

## References

- `design/design_decisions.md` — closed design decisions
- `design/deferrals.md` — deferred items
- `design/open_questions.md` — items blocking specific work
- `engops/runbooks/claude-code.md` — Claude Code setup reference
- `engops/cheatsheets/claude-code.md` — Claude Code day-to-day reference
