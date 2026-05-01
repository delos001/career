# Competency Clustering Proposal — Consolidated

Final cluster list after applying user feedback on points 1-6 and recommended folds (#3→#1, #10→#8). Working count: **31 clusters**, organized into 5 navigation domains. Domains are organizational only; the registry itself stays flat.

Format: cluster name (lowercase kebab) + short scope + approximate member count.

---

## Domain 1 — Clinical Operations Execution

1. **site-monitoring-and-visit-conduct** — site initiation/monitoring/close-out visits, site selection, multi-site oversight, visit efficiency. Absorbs old cluster #3 (site issue resolution and communication) and EX-037 (specimen collection from CRT role). ~12 entries.

2. **subject-recruitment-and-retention** — recruitment and retention planning, follow-up, recruitment tracking, recruitment risk modeling. ~7 entries.

3. **subject-safety-monitoring-and-surveillance** — subject safety monitoring, endpoint reporting, corrective action recommendation, SAE-related work. ~3 entries.

4. **investigator-and-site-training-delivery** — investigator meetings, site staff training on protocol/GCP, site-facing training material. ~3 entries.

5. **regulatory-document-management-and-tmf** — TMF/eTMF accountability, regulatory document review (ICF/1572/Financial Disclosure/IRB), study start-up and close-out documentation. ~6 entries.

6. **study-execution-and-trial-management** — end-to-end trial accountability, project planning, timelines, study start-up operations leadership, regulatory submission coordination, database lock. ~8 entries.

## Domain 2 — Quality, Compliance & Risk

7. **audit-and-inspection-response** — formal audit role (preparation, auditor engagement, findings response), audit readiness, gap analysis under audit conditions. Absorbs old cluster #10 (CAPA and issue management). ~7 entries.

8. **sop-and-controlled-document-authoring** — SOP authoring, controlled document development, planning document development. (Training content moved out to cluster #24.) ~6 entries.

9. **regulatory-framework-application** — 21 CFR Part 11 application/assessment/oversight, Anti-Kickback/False Claims compliance. ~4 entries.

10. **data-quality-surveillance** — operational data integrity monitoring, conformity troubleshooting, surveillance redesign, RBM/data-validation integration, validation check optimization. ~10 entries.

11. **computer-system-and-programming-validation** — formal CSV/CSA-aligned validation deliverables: double-programming validation, CSV documentation/artifacts, validation test scripts, peer code QC. ~3 entries.

12. **risk-based-monitoring-and-quality-indicators** — RBM strategy, KRI/threshold/trigger design, site risk stratification and tiering, custom RBM application design, signal flagging. ~10 entries.

13. **central-statistical-monitoring** — CSM signal governance, algorithm parameter configuration, deployment leadership, clinops/biostats liaison, post-deployment hyper-care. ~6 entries.

## Domain 3 — Data, Analytics & Engineering

14. **statistical-methods-and-quantitative-analysis** — statistical hypothesis testing, EDA, anomaly detection, time-series forecasting, predictive modeling, earned-value modeling. (RCA moved out to cluster #23.) ~7 entries.

15. **data-engineering-and-pipelines** — ETL/ELT, R/Python/SQL data transformation, automation scripting, relational database design. ~8 entries.

16. **reporting-and-dashboard-development** — Spotfire/R-TERR/Power-BI dashboards, KPI reporting models, real-time reporting, custom reporting tools. ~8 entries.

17. **standards-and-specification-design** — CDISC mapping (CDASH/SDTM/LAB), eCRF specs, edit check specs, transfer specs (DTAs, lab specs), CRF library design, conformance check libraries, standards governance. ~10 entries.

18. **custom-application-and-integration-development** — custom application build (RBM apps, integration apps, NLP parsers, R functions), POC architecture, legacy process replacement, document generation pipelines. ~9 entries.

19. **ai-and-machine-learning-engineering** — AI workflow architecture, ML/LLM system design, decision engine frameworks, AI agent exploration, prompt engineering, context-window optimization. ~8 entries.

## Domain 4 — Vendor, Technology & Strategy

20. **vendor-and-cro-operational-management** — day-to-day vendor/CRO oversight of active work: scope-of-work compliance, FSP-model functional oversight, vendor team direction, external lab acquisition, technology vendor ecosystem oversight. ~11 entries.

21. **vendor-and-cro-selection-and-partnership-design** — vendor selection, preferred partner evaluation, contracting/engagement model design, vendor strategy contribution, vendor utilization analysis. ~11 entries.

22. **technology-platform-strategy-and-selection** — enterprise platform deployment strategy (Databricks, AWS), multi-vendor platform evaluation, POC budget securing, platform fit assessment, project charter authoring for technology initiatives. ~12 entries.

## Domain 5 — Leadership, Strategy & Process Design

23. **process-design-and-optimization** — process redesign, gap analysis, lean tools (VSM, SIPOC), process pilot and measurement, workflow design, planning infrastructure digitization, root cause analysis. ~13 entries.

24. **training-development-and-knowledge-transfer** — internal training content development, curriculum authoring (including SOP training content), mentoring, peer technical guidance, onboarding preceptor role, training delivery to internal teams. ~13 entries.

25. **people-leadership-and-direct-management** — direct management, performance feedback, hiring and selection, internship program ownership, matrix team direction, leader-as-doer crisis posture. ~7 entries.

26. **stakeholder-management-and-cross-functional-engagement** — cross-functional collaboration, executive communication, sponsor-facing communication, stakeholder influence, agile sprint participation, clinical SME-to-product translation. ~9 entries.

27. **change-management-and-capability-adoption** — enterprise change management, platform adoption leadership, training rollout for new capabilities, knowledge-sharing initiative formation, developer-tooling rollout, resistance management. ~8 entries.

28. **organizational-design-and-function-building** — greenfield team formation, operating-model build, structural-gap diagnosis, industry benchmarking, competency-based org modeling, function direction. ~7 entries.

29. **strategic-planning-and-roadmapping** — capability roadmap development, strategic narrative authoring, future-state model design, ML/AI roadmap shaping, executive technology strategy advisory, strategic restructuring proposals. ~9 entries.

30. **governance-and-risk-management** — governance framework construction, accountability framework establishment, M&A integration risk escalation, GxP/Part-11 system oversight, decision-rights design. ~9 entries.

31. **financial-management-and-budgeting** — vendor negotiation and procurement, study supply procurement, POC budget securing, scope/cost optimization, budget-priority alignment. ~5 entries.

---

## Remaining Decisions

Two user-call merges were flagged in the original proposal but not yet decided:
- CSM (#13) — keep separate from RBM (#12) or merge?
- Reporting (#16) — keep separate from data-engineering (#15) or merge?

After these are settled, Step 3 (write the new `rules/competencies/registry.md`) can begin.
