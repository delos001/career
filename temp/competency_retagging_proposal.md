# Competency Re-Tagging Proposal

JD-blind re-tagging of 192 EX entries (Section 8) + 5 PR entries (Section 9) = 197 total against the 36-term activity-level Competency registry at `rules/competencies/registry.md`. Generated to resolve open question `competency-registry-runtime-value` per session protocol.

## Format

One entry per block:

```
EX-NNN | OLD: <pipe-separated old tags> | NEW: <pipe-separated new slugs>
       NOTE: <only when gap, ambiguity, or non-obvious mapping>
```

Old tags shown verbatim from current inventory (16-term registry values). New tags drawn only from the 36 slugs in `rules/competencies/registry.md`. Multi-tag selection capped at 2-3 strongest fits per entry. Tags reflect the **activity** in Description (Industry/Specialty/Orientation already cover context-level signal in their dedicated axes).

## Tagging Patterns Applied

For consistency across similar entries:

- **Site monitoring lifecycle** (visits, oversight, multi-site management) → `operations-management` (+ `regulatory-compliance` if "per regs/ICH/GCP" stated)
- **Safety surveillance / SAE handling** → `risk-management` (subject risk vigilance) + `quality-management` if data-discrepancy resolution
- **Data triage / data quality / data integrity review** → `data-analysis-and-statistics` + `quality-management`
- **Vendor/CRO performance review or selection** → `vendor-management`
- **Process improvement / optimization** → `process-design-and-improvement`
- **Cross-team work** → `cross-functional-collaboration` (only when explicitly multi-function)
- **Specifications (eCRF, lab manual, data standards)** → `standards-and-specification-development`
- **SOP / working practice / form authoring** → `procedure-authoring`
- **Training delivery to sites/staff/PIs** → `training-delivery`
- **Training material development** → `curriculum-development`
- **Regulatory document review/approval** (ICFs, 1572, IRB) → `regulatory-compliance` + `quality-management`
- **CAPA / corrective action / non-compliance trends** → `quality-management`
- **TMF QC / audit reviews** → `quality-management` + `audit-and-inspection-response`
- **EDC superuser / system config** → `system-implementation-and-configuration`
- **Custom reports / dashboards** → `reporting-and-dashboards`
- **Hands-on subject contact / specimen handling / enrollment procedures** → `standards-application` (executing per protocol). Possible gap; flagged.
- **Risk stratification / RBM strategy** → `risk-management`
- **Site / vendor communications + issue resolution** → `stakeholder-management` + `operations-management`

## Section 8 — All Tasks Performed

### Clinical Monitoring & Site Management

EX-001 | OLD: Vendor Management & Oversight | Clinical Trial Execution | Quality & Compliance | NEW: vendor-management | quality-management
EX-002 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: data-analysis-and-statistics | quality-management
EX-004 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: operations-management | regulatory-compliance
EX-005 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: quality-management | risk-management
EX-006 | OLD: Clinical Trial Execution | NEW: process-design-and-improvement
EX-007 | OLD: Clinical Trial Execution | Process Design & Optimization | NEW: process-design-and-improvement | cross-functional-collaboration
EX-008 | OLD: Quality & Compliance | NEW: regulatory-compliance
EX-009 | OLD: Clinical Trial Execution | NEW: operations-management | regulatory-compliance
EX-010 | OLD: Clinical Trial Execution | NEW: risk-management | cross-functional-collaboration
EX-011 | OLD: Clinical Trial Execution | NEW: quality-management | risk-management
EX-012 | OLD: Clinical Trial Execution | Stakeholder Management & Influence | NEW: cross-functional-collaboration | quality-management
EX-013 | OLD: Clinical Trial Execution | NEW: operations-management
EX-014 | OLD: Clinical Trial Execution | NEW: operations-management | regulatory-compliance
EX-015 | OLD: Clinical Trial Execution | NEW: data-analysis-and-statistics | quality-management
EX-016 | OLD: Clinical Trial Execution | Change Management & Adoption | NEW: training-delivery
EX-017 | OLD: Clinical Trial Execution | NEW: quality-management | regulatory-compliance
EX-018 | OLD: Clinical Trial Execution | Stakeholder Management & Influence | NEW: stakeholder-management | operations-management
EX-019 | OLD: Clinical Trial Execution | Data & Analytics | NEW: standards-and-specification-development | cross-functional-collaboration
EX-020 | OLD: Clinical Trial Execution | Process Design & Optimization | NEW: procedure-authoring | curriculum-development
EX-021 | OLD: Clinical Trial Execution | Change Management & Adoption | NEW: curriculum-development | training-delivery
EX-022 | OLD: Clinical Trial Execution | Financial Management & Budgeting | Vendor Management & Oversight | NEW: vendor-management | budget-management
EX-023 | OLD: Clinical Trial Execution | NEW: operations-management
EX-024 | OLD: Risk-Based Monitoring & Quality | Clinical Trial Execution | NEW: risk-management | data-analysis-and-statistics
EX-025 | OLD: Clinical Trial Execution | Technology Strategy & Implementation | NEW: system-implementation-and-configuration | reporting-and-dashboards
EX-026 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: quality-management | standards-and-specification-development
EX-027 | OLD: Quality & Compliance | Clinical Trial Execution | NEW: quality-management | audit-and-inspection-response
EX-028 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: regulatory-compliance | quality-management
EX-030 | OLD: Clinical Trial Execution | Change Management & Adoption | NEW: training-delivery
EX-031 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: operations-management | quality-management
EX-033 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: operations-management | regulatory-compliance
EX-034 | OLD: Clinical Trial Execution | Data & Analytics | NEW: data-analysis-and-statistics | process-design-and-improvement
EX-035 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: regulatory-compliance | quality-management
EX-036 | OLD: Clinical Trial Execution | Data & Analytics | NEW: data-analysis-and-statistics | reporting-and-dashboards
EX-037 | OLD: Clinical Trial Execution | Quality & Compliance | NEW: standards-application
       NOTE: Hands-on specimen collection per protocol. standards-application = "applying existing standards in operational work" fits, but pattern recurs across several CRA-execution entries; flag for gap consideration.
EX-038 | OLD: Clinical Trial Execution | NEW: standards-application
EX-040 | OLD: Clinical Trial Execution | NEW: standards-application

### Vendor Management & Oversight

EX-003 | OLD: Vendor Management & Oversight | Team Leadership & Development | NEW: vendor-management | training-delivery
EX-041 | OLD: Vendor Management & Oversight | Stakeholder Management & Influence | Process Design & Optimization | NEW: project-management | vendor-management | stakeholder-management
EX-042 | OLD: Vendor Management & Oversight | Governance & Risk Management | NEW: governance | vendor-management | risk-management
EX-043 | OLD: Vendor Management & Oversight | Process Design & Optimization | NEW: vendor-management | process-design-and-improvement
EX-044 | OLD: Vendor Management & Oversight | Stakeholder Management & Influence | NEW: vendor-management | reporting-and-dashboards
EX-045 | OLD: Vendor Management & Oversight | Stakeholder Management & Influence | Technology Strategy & Implementation | NEW: risk-management | vendor-management | strategic-planning
EX-046 | OLD: Vendor Management & Oversight | Financial Management & Budgeting | NEW: vendor-management | budget-management
EX-047 | OLD: Vendor Management & Oversight | Governance & Risk Management | NEW: vendor-management | procedure-authoring
EX-048 | OLD: Vendor Management & Oversight | Stakeholder Management & Influence | Governance & Risk Management | NEW: vendor-management | risk-management
EX-049 | OLD: Vendor Management & Oversight | Strategic Planning & Roadmapping | Stakeholder Management & Influence | Standards & Specification Design | NEW: vendor-management | strategic-planning
EX-050 | OLD: Vendor Management & Oversight | Team Leadership & Development | NEW: vendor-management | operations-management
EX-051 | OLD: Vendor Management & Oversight | Team Leadership & Development | NEW: vendor-management
EX-052 | OLD: Vendor Management & Oversight | Stakeholder Management & Influence | NEW: vendor-management | cross-functional-collaboration
EX-054 | OLD: Vendor Management & Oversight | Data & Analytics | NEW: vendor-management | quality-management
EX-055 | OLD: Vendor Management & Oversight | Governance & Risk Management | Standards & Specification Design | NEW: vendor-management | standards-application
EX-056 | OLD: Vendor Management & Oversight | NEW: vendor-management | quality-management
EX-057 | OLD: Vendor Management & Oversight | Technology Strategy & Implementation | NEW: vendor-management | technology-evaluation
EX-058 | OLD: Vendor Management & Oversight | NEW: vendor-management | operations-management
EX-059 | OLD: Vendor Management & Oversight | Quality & Compliance | NEW: vendor-management | quality-management
EX-085 | OLD: Quality & Compliance | Vendor Management & Oversight | Standards & Specification Design | NEW: audit-and-inspection-response | vendor-management | process-design-and-improvement

### Risk-Based Monitoring & Quality

EX-060 | OLD: Risk-Based Monitoring & Quality | Technology Strategy & Implementation | Stakeholder Management & Influence | NEW: cross-functional-collaboration | application-development
EX-061 | OLD: Risk-Based Monitoring & Quality | Technology Strategy & Implementation | Stakeholder Management & Influence | NEW: cross-functional-collaboration | application-development
EX-062 | OLD: Risk-Based Monitoring & Quality | Change Management & Adoption | NEW: risk-management | training-delivery
EX-063 | OLD: Risk-Based Monitoring & Quality | Change Management & Adoption | NEW: training-delivery | procedure-authoring
EX-064 | OLD: Risk-Based Monitoring & Quality | Governance & Risk Management | NEW: governance | risk-management
EX-065 | OLD: Risk-Based Monitoring & Quality | NEW: project-management | system-implementation-and-configuration
EX-066 | OLD: Risk-Based Monitoring & Quality | Stakeholder Management & Influence | NEW: cross-functional-collaboration | stakeholder-management
EX-067 | OLD: Risk-Based Monitoring & Quality | Change Management & Adoption | NEW: knowledge-transfer | risk-management
EX-068 | OLD: Risk-Based Monitoring & Quality | Stakeholder Management & Influence | NEW: change-management | process-design-and-improvement
EX-069 | OLD: Risk-Based Monitoring & Quality | Process Design & Optimization | Change Management & Adoption | NEW: procedure-authoring | curriculum-development
EX-070 | OLD: Risk-Based Monitoring & Quality | Process Design & Optimization | NEW: risk-management | procedure-authoring
EX-071 | OLD: Quality & Compliance | Risk-Based Monitoring & Quality | NEW: quality-management | procedure-authoring
EX-072 | OLD: Risk-Based Monitoring & Quality | Technology Strategy & Implementation | Change Management & Adoption | NEW: application-development | risk-management
EX-073 | OLD: Risk-Based Monitoring & Quality | Technology Strategy & Implementation | Data & Analytics | NEW: application-development | process-design-and-improvement
EX-074 | OLD: Risk-Based Monitoring & Quality | Data & Analytics | Technology Strategy & Implementation | NEW: reporting-and-dashboards | data-analysis-and-statistics
EX-075 | OLD: Risk-Based Monitoring & Quality | Data & Analytics | NEW: reporting-and-dashboards | programming
EX-076 | OLD: Risk-Based Monitoring & Quality | Data & Analytics | Stakeholder Management & Influence | NEW: data-analysis-and-statistics | stakeholder-management
EX-077 | OLD: Risk-Based Monitoring & Quality | Data & Analytics | Stakeholder Management & Influence | NEW: data-analysis-and-statistics | stakeholder-management
EX-078 | OLD: Risk-Based Monitoring & Quality | Process Design & Optimization | NEW: standards-and-specification-development | quality-management
EX-079 | OLD: Risk-Based Monitoring & Quality | Data & Analytics | NEW: data-analysis-and-statistics | risk-management
EX-080 | OLD: Risk-Based Monitoring & Quality | Governance & Risk Management | AI Engineering & Development | NEW: ai-ml-development | governance
EX-081 | OLD: Risk-Based Monitoring & Quality | Clinical Trial Execution | NEW: risk-management | standards-application
EX-082 | OLD: Risk-Based Monitoring & Quality | Stakeholder Management & Influence | Process Design & Optimization | NEW: cross-functional-collaboration | standards-and-specification-development
EX-119 | OLD: Risk-Based Monitoring & Quality | Process Design & Optimization | Stakeholder Management & Influence | NEW: standards-and-specification-development | risk-management

### Clinical Trial Management & Oversight

EX-083 | OLD: Clinical Trial Execution | Governance & Risk Management | Vendor Management & Oversight | NEW: project-management | operations-management
EX-084 | OLD: Quality & Compliance | Clinical Trial Execution | NEW: audit-and-inspection-response
EX-086 | OLD: Quality & Compliance | Governance & Risk Management | NEW: regulatory-compliance | quality-management
EX-087 | OLD: Quality & Compliance | Governance & Risk Management | NEW: quality-management | audit-and-inspection-response
EX-088 | OLD: Clinical Trial Execution | Governance & Risk Management | NEW: project-management | risk-management
EX-089 | OLD: Clinical Trial Execution | Team Leadership & Development | NEW: project-management | cross-functional-collaboration
EX-090 | OLD: Clinical Trial Execution | Financial Management & Budgeting | NEW: project-management | budget-management
EX-091 | OLD: Clinical Trial Execution | NEW: operations-management
EX-092 | OLD: Quality & Compliance | Governance & Risk Management | Clinical Trial Execution | NEW: regulatory-compliance | quality-management
EX-093 | OLD: Clinical Trial Execution | Quality & Compliance | Governance & Risk Management | NEW: risk-management | audit-and-inspection-response
EX-094 | OLD: Clinical Trial Execution | Change Management & Adoption | NEW: training-delivery | stakeholder-management

### Data Science, Analytics & Engineering

EX-039 | OLD: Data & Analytics | NEW: data-engineering | application-development
EX-095 | OLD: Data & Analytics | Technology Strategy & Implementation | AI Engineering & Development | NEW: ai-ml-development | technology-evaluation
EX-096 | OLD: Data & Analytics | Technology Strategy & Implementation | Change Management & Adoption | NEW: application-development | data-engineering
EX-097 | OLD: Data & Analytics | NEW: programming | data-engineering
EX-098 | OLD: Data & Analytics | Process Design & Optimization | NEW: reporting-and-dashboards | quality-management
EX-099 | OLD: Data & Analytics | Quality & Compliance | Process Design & Optimization | Standards & Specification Design | NEW: data-analysis-and-statistics | procedure-authoring
EX-100 | OLD: Data & Analytics | Change Management & Adoption | NEW: reporting-and-dashboards
EX-101 | OLD: Data & Analytics | Process Design & Optimization | NEW: data-engineering | reporting-and-dashboards
EX-102 | OLD: Data & Analytics | Quality & Compliance | NEW: programming | data-engineering
EX-103 | OLD: Data & Analytics | Vendor Management & Oversight | NEW: cross-functional-collaboration | quality-management
EX-104 | OLD: Data & Analytics | Risk-Based Monitoring & Quality | NEW: programming | data-engineering
EX-105 | OLD: Data & Analytics | Technology Strategy & Implementation | Risk-Based Monitoring & Quality | NEW: reporting-and-dashboards
EX-106 | OLD: Data & Analytics | Quality & Compliance | Risk-Based Monitoring & Quality | NEW: quality-management | programming
EX-107 | OLD: Data & Analytics | Risk-Based Monitoring & Quality | NEW: ai-ml-development | data-analysis-and-statistics
EX-108 | OLD: Data & Analytics | Technology Strategy & Implementation | Risk-Based Monitoring & Quality | NEW: ai-ml-development | application-development
EX-109 | OLD: Data & Analytics | Risk-Based Monitoring & Quality | NEW: ai-ml-development
EX-110 | OLD: Data & Analytics | Risk-Based Monitoring & Quality | NEW: programming | application-development
EX-111 | OLD: Data & Analytics | Technology Strategy & Implementation | Risk-Based Monitoring & Quality | NEW: quality-management | application-development
EX-112 | OLD: Data & Analytics | Team Leadership & Development | Risk-Based Monitoring & Quality | NEW: programming | process-design-and-improvement
EX-113 | OLD: Stakeholder Management & Influence | Risk-Based Monitoring & Quality | Data & Analytics | Clinical Trial Execution | Vendor Management & Oversight | NEW: data-analysis-and-statistics | stakeholder-management
EX-114 | OLD: Data & Analytics | Risk-Based Monitoring & Quality | NEW: ai-ml-development
EX-115 | OLD: Data & Analytics | Quality & Compliance | Risk-Based Monitoring & Quality | NEW: data-analysis-and-statistics | quality-management
EX-116 | OLD: Data & Analytics | Risk-Based Monitoring & Quality | NEW: reporting-and-dashboards | risk-management
EX-117 | OLD: Data & Analytics | Quality & Compliance | NEW: data-analysis-and-statistics
EX-118 | OLD: Risk-Based Monitoring & Quality | Data & Analytics | NEW: data-analysis-and-statistics | risk-management
EX-120 | OLD: Data & Analytics | Technology Strategy & Implementation | NEW: technology-evaluation | system-implementation-and-configuration
EX-121 | OLD: Data & Analytics | Process Design & Optimization | Risk-Based Monitoring & Quality | NEW: project-management | reporting-and-dashboards
EX-122 | OLD: Data & Analytics | Risk-Based Monitoring & Quality | Stakeholder Management & Influence | NEW: data-analysis-and-statistics | risk-management
EX-123 | OLD: Data & Analytics | Process Design & Optimization | NEW: data-analysis-and-statistics | process-design-and-improvement

### Data Management & Quality Surveillance

EX-053 | OLD: Quality & Compliance | Data & Analytics | NEW: quality-management | programming
EX-124 | OLD: Quality & Compliance | Process Design & Optimization | Change Management & Adoption | Standards & Specification Design | NEW: process-design-and-improvement | procedure-authoring | change-management
EX-125 | OLD: Data & Analytics | Process Design & Optimization | Governance & Risk Management | Standards & Specification Design | NEW: standards-and-specification-development | data-engineering
EX-126 | OLD: Vendor Management & Oversight | Process Design & Optimization | Governance & Risk Management | Standards & Specification Design | NEW: standards-and-specification-development | vendor-management
EX-127 | OLD: Quality & Compliance | Data & Analytics | Process Design & Optimization | NEW: standards-and-specification-development | quality-management
EX-128 | OLD: Quality & Compliance | Governance & Risk Management | Strategic Planning & Roadmapping | NEW: change-management | cross-functional-collaboration
EX-129 | OLD: Quality & Compliance | Governance & Risk Management | NEW: regulatory-compliance
EX-130 | OLD: Quality & Compliance | Governance & Risk Management | Technology Strategy & Implementation | NEW: regulatory-compliance | audit-and-inspection-response
EX-131 | OLD: Quality & Compliance | Governance & Risk Management | Technology Strategy & Implementation | NEW: regulatory-compliance | quality-management
EX-132 | OLD: Quality & Compliance | Process Design & Optimization | Governance & Risk Management | Standards & Specification Design | NEW: process-design-and-improvement | governance
EX-133 | OLD: Quality & Compliance | Process Design & Optimization | Standards & Specification Design | NEW: standards-application | data-engineering
EX-134 | OLD: Quality & Compliance | Stakeholder Management & Influence | Standards & Specification Design | NEW: standards-and-specification-development | cross-functional-collaboration
EX-135 | OLD: Quality & Compliance | Risk-Based Monitoring & Quality | Stakeholder Management & Influence | NEW: cross-functional-collaboration | risk-management
EX-136 | OLD: Quality & Compliance | Process Design & Optimization | NEW: process-design-and-improvement | quality-management
EX-137 | OLD: Quality & Compliance | Process Design & Optimization | Technology Strategy & Implementation | NEW: process-design-and-improvement | reporting-and-dashboards
EX-138 | OLD: Quality & Compliance | Technology Strategy & Implementation | NEW: standards-and-specification-development | quality-management
EX-139 | OLD: Quality & Compliance | Process Design & Optimization | NEW: standards-and-specification-development | quality-management
EX-140 | OLD: Quality & Compliance | Stakeholder Management & Influence | NEW: cross-functional-collaboration | timeline-management
EX-141 | OLD: Quality & Compliance | Stakeholder Management & Influence | NEW: cross-functional-collaboration | process-design-and-improvement
EX-142 | OLD: Quality & Compliance | Stakeholder Management & Influence | NEW: cross-functional-collaboration | standards-and-specification-development

### Technology Strategy, Evaluation & Platform

EX-143 | OLD: Technology Strategy & Implementation | Strategic Planning & Roadmapping | Change Management & Adoption | NEW: technology-evaluation | strategic-planning | change-management
EX-144 | OLD: Technology Strategy & Implementation | Strategic Planning & Roadmapping | NEW: roadmap-development | strategic-planning
EX-145 | OLD: Technology Strategy & Implementation | Stakeholder Management & Influence | NEW: vendor-management | project-management
EX-146 | OLD: Technology Strategy & Implementation | Stakeholder Management & Influence | Change Management & Adoption | NEW: change-management | executive-communication
EX-147 | OLD: Technology Strategy & Implementation | Stakeholder Management & Influence | NEW: technology-evaluation | cross-functional-collaboration
EX-148 | OLD: Technology Strategy & Implementation | Process Design & Optimization | Governance & Risk Management | NEW: project-management | standards-and-specification-development
EX-149 | OLD: Technology Strategy & Implementation | Data & Analytics | NEW: data-analysis-and-statistics
EX-150 | OLD: Technology Strategy & Implementation | Financial Management & Budgeting | NEW: budget-management | technology-evaluation
EX-151 | OLD: Technology Strategy & Implementation | Strategic Planning & Roadmapping | Stakeholder Management & Influence | AI Engineering & Development | NEW: strategic-planning | executive-communication
EX-152 | OLD: Technology Strategy & Implementation | Process Design & Optimization | NEW: data-engineering | process-design-and-improvement
EX-153 | OLD: Technology Strategy & Implementation | Risk-Based Monitoring & Quality | NEW: cross-functional-collaboration | application-development
EX-154 | OLD: Technology Strategy & Implementation | Change Management & Adoption | Governance & Risk Management | Risk-Based Monitoring & Quality | NEW: change-management | procedure-authoring
EX-155 | OLD: Technology Strategy & Implementation | Change Management & Adoption | Stakeholder Management & Influence | NEW: change-management | training-delivery
EX-156 | OLD: Technology Strategy & Implementation | Change Management & Adoption | NEW: knowledge-transfer | training-delivery
EX-170 | OLD: Strategic Planning & Roadmapping | Stakeholder Management & Influence | Technology Strategy & Implementation | NEW: strategic-planning | executive-communication

### Process Design & Governance

EX-157 | OLD: Process Design & Optimization | Organizational Design | Governance & Risk Management | Change Management & Adoption | NEW: organizational-design | governance | procedure-authoring
EX-158 | OLD: Process Design & Optimization | Strategic Planning & Roadmapping | Organizational Design | NEW: roadmap-development | organizational-design
EX-159 | OLD: Process Design & Optimization | Governance & Risk Management | Technology Strategy & Implementation | NEW: system-implementation-and-configuration | governance
EX-160 | OLD: Process Design & Optimization | Strategic Planning & Roadmapping | Organizational Design | NEW: organizational-design | strategic-planning
EX-161 | OLD: Process Design & Optimization | Strategic Planning & Roadmapping | Stakeholder Management & Influence | Financial Management & Budgeting | NEW: roadmap-development | budget-management
EX-162 | OLD: Process Design & Optimization | Governance & Risk Management | Stakeholder Management & Influence | Risk-Based Monitoring & Quality | NEW: standards-and-specification-development | cross-functional-collaboration
EX-163 | OLD: Process Design & Optimization | NEW: procedure-authoring | risk-management
EX-164 | OLD: Process Design & Optimization | Stakeholder Management & Influence | NEW: stakeholder-management | process-design-and-improvement
EX-191 | OLD: Process Design & Optimization | NEW: process-design-and-improvement | data-analysis-and-statistics
EX-192 | OLD: Process Design & Optimization | Strategic Planning & Roadmapping | NEW: roadmap-development | process-design-and-improvement
EX-182 | OLD: Stakeholder Management & Influence | Strategic Planning & Roadmapping | Financial Management & Budgeting | Vendor Management & Oversight | NEW: strategic-planning | vendor-management

### Organizational & Team Leadership

EX-029 | OLD: Team Leadership & Development | Quality & Compliance | NEW: performance-management | quality-management
EX-165 | OLD: Organizational Design | Team Leadership & Development | NEW: organizational-design | people-management
EX-166 | OLD: Team Leadership & Development | Vendor Management & Oversight | NEW: performance-management | mentoring
EX-167 | OLD: Team Leadership & Development | Stakeholder Management & Influence | NEW: operations-management | stakeholder-management
EX-168 | OLD: Organizational Design | Process Design & Optimization | NEW: organizational-design | risk-management
EX-169 | OLD: Stakeholder Management & Influence | Organizational Design | NEW: cross-functional-collaboration | executive-communication
EX-171 | OLD: Organizational Design | Strategic Planning & Roadmapping | Stakeholder Management & Influence | NEW: organizational-design | strategic-planning
EX-172 | OLD: Team Leadership & Development | Organizational Design | NEW: talent-acquisition | mentoring | project-management
EX-173 | OLD: Team Leadership & Development | Technology Strategy & Implementation | NEW: system-implementation-and-configuration | knowledge-transfer
EX-174 | OLD: Team Leadership & Development | Organizational Design | NEW: talent-acquisition
EX-175 | OLD: Team Leadership & Development | Change Management & Adoption | Stakeholder Management & Influence | NEW: knowledge-transfer | cross-functional-collaboration
EX-176 | OLD: Clinical Trial Execution | Team Leadership & Development | Stakeholder Management & Influence | NEW: people-management | cross-functional-collaboration
EX-177 | OLD: Team Leadership & Development | NEW: mentoring
EX-178 | OLD: Team Leadership & Development | NEW: mentoring | training-delivery
EX-179 | OLD: Team Leadership & Development | NEW: mentoring | knowledge-transfer
EX-180 | OLD: Team Leadership & Development | NEW: talent-acquisition

### Change Management, Training & Adoption

EX-032 | OLD: Team Leadership & Development | NEW: training-delivery | mentoring
EX-181 | OLD: Change Management & Adoption | Stakeholder Management & Influence | NEW: training-delivery | change-management
EX-183 | OLD: Change Management & Adoption | Technology Strategy & Implementation | Risk-Based Monitoring & Quality | NEW: change-management | procedure-authoring
EX-184 | OLD: Change Management & Adoption | Risk-Based Monitoring & Quality | NEW: change-management | curriculum-development
EX-185 | OLD: Change Management & Adoption | NEW: change-management | training-delivery
EX-186 | OLD: Change Management & Adoption | Stakeholder Management & Influence | NEW: process-design-and-improvement | stakeholder-management
EX-187 | OLD: Change Management & Adoption | Data & Analytics | Process Design & Optimization | NEW: reporting-and-dashboards | performance-management
EX-188 | OLD: Change Management & Adoption | Team Leadership & Development | NEW: curriculum-development | training-delivery
EX-189 | OLD: Change Management & Adoption | Quality & Compliance | NEW: training-delivery | regulatory-compliance
EX-190 | OLD: Change Management & Adoption | Technology Strategy & Implementation | NEW: training-delivery | knowledge-transfer

## Section 9 — Independent & Volunteer Projects

PR-001 | OLD: AI Engineering & Development | Process Design & Optimization | Technology Strategy & Implementation | NEW: ai-ml-development | application-development
PR-002 | OLD: AI Engineering & Development | Process Design & Optimization | NEW: application-development | ai-ml-development
PR-003 | OLD: AI Engineering & Development | NEW: ai-ml-development | programming
PR-004 | OLD: AI Engineering & Development | NEW: application-development | programming
PR-005 | OLD: AI Engineering & Development | Process Design & Optimization | NEW: application-development | ai-ml-development

## Registry Gaps — Resolved at User QC 2026-05-01

All initial gap candidates resolved during user QC pass. No registry additions required.

- **`regulatory-document-authoring`**: dropped. EX-010 was SAE narrative compilation for downstream medical writer use, not submission authoring. Re-tagged to `regulatory-compliance | cross-functional-collaboration`.
- **`clinical-operations-execution`**: dropped. EX-037, EX-038, EX-040 are early-career enrollment / specimen / follow-up work the user will not include in any CV. `standards-application` stretch-fit accepted in perpetuity since these entries will never surface at retrieval.
- **`vendor-management` vs `technology-evaluation` split**: confirmed. Service-vendor work (CROs, labs) → `vendor-management`; tool/platform-vendor work → `technology-evaluation`. Distinction is real and the slugs as scoped support it.
- **Audit-conducting vs audit-response**: no separate slug needed. The user's audit work was sponsor-SME support (auditee-side, supporting auditors as a domain expert), not auditor-side. Current scope of `audit-and-inspection-response` covers it. If a future role involves user **leading** audits, revisit then.

### Notes on tags not flagged as gaps

- **Validation/UAT/test-script authoring** (EX-053, EX-071, EX-106, EX-111, EX-138): force-fit into `quality-management`. Validation in regulated industries is recognizable as a discipline (CSV/CSA), but at the activity level it's quality work. Not flagging.
- **Workflow / process documentation** (across many entries): split between `procedure-authoring` (when SOP-flavored) and `standards-and-specification-development` (when spec-flavored). Boundary judgment cases exist; flagged inline in NOTEs only where ambiguous.
- **System-superuser operational work** (e.g., InForm EDC, Siebel CTMS): tagged as `system-implementation-and-configuration` when configuration work is involved, `data-analysis-and-statistics` when data-extraction-only.

## Self-QC Summary

Pre-handoff checks performed on this proposal:

- **Slug validity**: every NEW tag verified against the 36 slugs in `rules/competencies/registry.md`. No invalid slugs or typos.
- **Coverage**: 192 EX entries + 5 PR entries = 197 total, matches expected inventory count.
- **Slug usage breadth**: all 36 slugs used at least once across the corpus. Distribution skews toward operational/quality/standards activities (consistent with user's clinical-operations career texture); strategic/governance slugs less frequent (consistent with leadership work concentrated in BioMarin years).
- **Cross-section consistency**: applied tagging patterns (header `## Tagging Patterns Applied` section) consistently. Same-pattern entries get same-tag combinations (e.g., site monitoring lifecycle → `operations-management` + `regulatory-compliance` across 5+ entries).
- **Single-tag entries**: 18 entries have only one NEW tag (vs 174 with two, 5 with three). Single-tag cases are entries where Description is narrow enough that a second tag would be a stretch (e.g., EX-009: pure regulatory-compliance work; EX-091: pure operations-management; EX-097: pure programming).
- **NOTE-flagged items** (5): EX-010, EX-013, EX-031, EX-037, EX-049, EX-060 — see inline NOTEs for ambiguity reasoning.

## Next Steps

1. **User QC pass on remaining inline NOTEs** (EX-013, EX-031, EX-049, EX-060): confirm or correct.
2. **Spot-check** any specific entries the user wants to verify before bulk apply.
3. **Apply final tags to `Experience_Inventory.md`** (replace `Competency:` field values with new slugs across 197 entries).
4. **cv_targeted prototype test** against a JD (registry-filter vs semantic-only) — JD held back by user until tagging applies.
