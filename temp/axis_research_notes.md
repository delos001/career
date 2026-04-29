# Axis Research Notes

Working notes from per-axis research. Captures sources, methodology decisions, and items to revisit during cross-axis reconciliation. One section per axis file.

---

## rules/industries/pharma.md

**Researched:** 2026-04-29

### Sources used
- FDA: ICH E6(R3) publication (Sep 2025), eCTD v4.0 standards, DCT final guidance (Sep 2024), RWE program pages
- ICH: E6(R3) Step 4 final guideline (Jan 2025)
- CDISC: SDTM and ADaM standard pages
- Industry interpretation: ACRP, FlorenceHC, IntuitionLabs (ICH E6(R3))
- Resume keyword sources: ResumeAdapter, JobHero, CVCompiler, PharmaUni
- Outsourcing models: TFS HealthScience (FSP), KPS Life (FSO/FSP white paper)
- Pharma vs biotech: Sci.bio, AAAS Science Careers
- Participant terminology: Clariness, PRIM&R blog, on-Biostatistics blog
- Pharmacovigilance: CliniIndia, NextPV Services, DLRC Group

### Key decisions
- "Participant" is now the primary trial-population term (TransCelerate/NIH/FDA/NEJM/ClinicalTrials.gov align). "Patient" is contextually correct for trials in patient populations; "subject" is dated.
- ICH E6(R3) cited as current GCP standard (finalized Jan 2025; FDA published Sep 2025; EU effective Jul 2025).
- Added CDISC data standards section: SDTM/ADaM are FDA-required for NDA/BLA/ANDA submissions.
- Added Operating concepts and Pharmacovigilance sections.
- Acronym list expanded from 21 to 51 (added PV, data, quality, FSP/FSO, DCT/RWE/RWD).

### Reconciliation candidates (revisit during cross-axis reconciliation)
- **"Evidence over claims" Emphasis paragraph**: Pharma-flavored (audits, CAPA, batch volume), but the underlying rule (proof points beat adjectives) may recur across industries and could belong in cv_targeted procedural rules instead. Keep here for now; check whether biotech/med-device/diagnostics show the same pattern.
- **CDISC/SDTM/ADaM data standards**: Pharma vocabulary, but the technical depth might belong in a data-engineering specialty if one is built. Industry framing stays; technical scope could migrate.
- **DSMB/DMC, IRB/IEC stakeholders**: Currently in industry; may also be relevant to orientation axis (process-operations) if stakeholder management surfaces there.
- **"Therapeutic area" reference**: Vocabulary item here; if therapeutic area becomes a tag dimension or sub-axis later, it moves.
- **Risk-based monitoring (RBM), Quality by Design (QbD)**: Pharma operating concepts, but RBM/QbD as methodologies could overlap with quality-compliance specialty; check during specialty research.

---

## rules/specialties/clinical-operations.md

**Researched:** 2026-04-29

### Sources used
- MRCT Center: JTF Clinical Trial Competency Framework (8 domains)
- ACRP: Core Competency Framework for CRAs; Improving Study Start-Up Efficiency (Feb 2026)
- TransCelerate: Risk Based Monitoring Initiative; QTL framework
- FDA: Dec 2024 draft guidance on protocol deviations; Sep 2024 DCT final guidance; ICH E6(R3) Sep 2025 publication
- Industry: IntuitionLabs (vendor management), Klein Hersh (Director job descs), Precision for Medicine (start-up vs site start-up), Pharmiweb (CPM responsibilities)
- Resume keywords: ResumeWorded (Director Clinical Operations 2026), ZipRecruiter

### Key decisions
- "RBM" framing updated to "RBQM" with QTL and KRI as codified components — matches current TransCelerate/industry standard.
- ICH E6(R3) Section 3.9 cited as the basis for vendor oversight capability (R3 explicitly mandates governance committees and risk-based oversight).
- FSP/FSO governance promoted to its own capability (distinct from CRO project management) — FSP is dominant model for top-10 biopharmas per 2024 industry survey.
- Removed AE/SAE/SUSAR, FSP, CSR/CTD module 5 from Terminology — these are now in pharma.md and the file's own discipline says sector-wide terms live there.
- Added FPI/LPI/LPO/DBL milestone abbreviations — universal in clinical operations status reporting.
- Added "important protocol deviation" — FDA Dec 2024 draft guidance defines this regulatory category.
- Added "Operational input to protocol design" capability — clinical ops contributes feasibility/recruitment input at protocol design time, distinct from study start-up.

### Reconciliation candidates
- **FSP framing**: removed from this file's Terminology because pharma.md now lists FSP as a stakeholder; kept here as a *capability* (FSP and FSO governance). Confirm during reconciliation that the capability-vs-stakeholder distinction holds across other specialties.
- **PI in stakeholder vs role lens**: PI appears in pharma.md (stakeholder) and here (operational site role). Different lenses justify duplication; revisit if both lenses prove unnecessary.
- **Database lock**: kept here as operational milestone; CSR moved to pharma.md submission terms. Verify the operational/submission split makes sense across other specialties.
- **"Important protocol deviation" attribution**: cited per FDA Dec 2024 draft guidance; when guidance finalizes, attribution should update.
- **RBQM vs RBM as a methodology**: appears here as a clinical-ops capability and in pharma.md as an operating concept. The pharma.md framing is broader (industry-wide concept); the clinical-ops framing is the specialty practice. Distinction may hold but verify when researching quality-compliance.

---

## rules/specialties/quality-compliance.md

**Researched:** 2026-04-29

### Sources used
- FDA: Computer Software Assurance final guidance (Sep 2025); CDER QMM program pages; data integrity Q&A guidance
- ICH: Q9(R1) Step 4 (Jan 2023); Q-series quality guidelines page; Q10 PQS interpretation
- EU: GMP Annex 1 (2022 revision) on contamination control strategy
- Industry: IntuitionLabs (CSV/CSA, ALCOA+, ICH Q-series), Florence/Pharmtech (Q9(R1)), West Pharma (Annex 1), Kneat/BlueMountain (CSA)
- Resume keywords: PharmUni 2026, Teal HQ, JRG Partners (GMP Director)
- Distinctions: TheFDAGroup (GCP vs GMP audit), SEC Life Sciences (golden trio), RQA (GCP careers)

### Key decisions
- "Risk-based quality management" → "Quality Risk Management (QRM) per ICH Q9(R1)" — Q9(R1) finalized Jan 2023; current framework reference is more falsifiable than the generic phrase.
- Added CSA alongside CSV — FDA Sep 2025 final guidance shifts the validation paradigm from exhaustive verification to risk-based assurance. Both CSV and CSA still appear on CVs depending on era and context.
- Added ALCOA+ data integrity as a top-level capability and terminology entry — FDA CDER warning letters jumped 50% in FY2025 with data integrity as a major concern; ALCOA+ is the codified industry standard.
- Added "Pre-approval inspection (PAI) readiness" as separate capability — distinct event with its own preparation cadence; reads differently than routine inspection response on senior quality CVs.
- Added Contamination Control Strategy (CCS) per EU GMP Annex 1 (2022) — required documented framework for sterile manufacturing as of 2023.
- Added FDA Quality Management Maturity (QMM) program as terminology — voluntary but signals quality-culture-leadership work for senior roles.
- Expanded inspection-outcome enumeration to FDA Form 483, Warning Letter, Untitled Letter, Consent Decree (full enforcement ladder).
- Added qualified person (QP, EU) to roles — distinct EU regulatory role for product release.

### Reconciliation candidates
- **QRM / RBQM / QbD overlap**: QRM (here, ICH Q9(R1)), RBQM (clinical-operations as RBQM with QTL/KRI), QbD (here in terminology, ICH Q8(R2)). All risk-management family; the lens differs (manufacturing-quality vs clinical-operations practice). Verify the lens-based separation holds across other specialties.
- **Data integrity (ALCOA+)**: here as quality-compliance capability; could also be pharma-axis vocabulary (data integrity is pharma-wide). Program-level design stays here; data integrity as a *concept* may belong in pharma.md.
- **CSV/CSA**: here as quality-compliance capability. May also be relevant in data-engineering specialty when validating data systems. Verify after data-engineering research.
- **Quality-compliance to data-engineering adjacency**: not added now (data-engineering not yet researched). Revisit after data-engineering research; potential weight 0.30-0.40 through CSV/CSA, data integrity, and system audits.
- **ISO 13485**: included here for combination products. Pharma.md med-device adjacency mentions ISO 13485 maps to GMP. Confirm cross-reference consistency during reconciliation.
- **Knowledge management**: added to change-control line; could become a more prominent capability if PQS-focused roles surface. Currently terminology-only.

---

## rules/specialties/data-engineering.md

**Researched:** 2026-04-29

### Sources used
- Industry: ResumeOptimizerPro (DE Resume 2026), DataEngineerAcademy (Resume Guide 2026), lakeFS (State of Data and AI Engineering 2025), DS Stream (Future of DE 2025)
- Lakehouse/table formats: Onehouse (Iceberg vs Delta vs Hudi), DataLakehouseHub (2025/2026 ultimate guide), Dremio (Iceberg vs Delta), Conduktor (medallion architecture)
- Streaming: Kai Waehner (top trends 2025/2026), Onehouse (engine comparisons), Databricks (Spark Real-Time Mode Aug 2025), AWS (Spark vs Flink)
- Quality/observability: Sparvi (tools 2025), dbt Labs (Monte Carlo partnership), DataKitchen (open-source 2026), Datacoves (advanced data quality)
- Data mesh/contracts: Springer (data contracts gray literature review), Dataversity (2025 trends), Snowflake (data products + data mesh), dbt Labs (4 principles)
- Resume keywords: ResumeWorded, BeamJobs, EnhanceCV, Medium (5 skills 2026)

### Key decisions
- Open table formats (Iceberg, Delta Lake, Hudi) promoted to capability vocabulary — they are now the lakehouse standard; absent from original.
- Quality framework split into testing (dbt tests, Great Expectations, Soda, Elementary) + observability (Monte Carlo, Bigeye) — current resumes name specific tools.
- Data contracts, data products, and data mesh patterns added as a capability — Gartner 2025: 70% of organizations piloting data mesh; data contracts emerging as central component.
- DataOps narrowed to engineering operations (CI/CD for data, IaC); observability moved to data quality bullet.
- Apache Beam removed from terminology — declining usage; replaced by Flink/Spark.
- Added medallion architecture (Bronze/Silver/Gold) — Databricks-popularized standard layering vocabulary.
- Added streaming semantics (exactly-once vs at-least-once delivery, watermarking) — load-bearing for streaming-engineering CVs.
- Added orchestration trio (Airflow, Prefect, Dagster) — Prefect/Dagster now standard alternatives to Airflow.
- Added Microsoft Fabric — Microsoft's unified analytics platform, now distinct from Synapse.

### Reconciliation candidates
- **Quality-compliance to data-engineering adjacency**: in regulated industries, data-engineering work involves CSV/CSA, data integrity (ALCOA+), audit trail design — overlapping with quality-compliance specialty. Adjacency exists but is industry-conditional. Decide during reconciliation whether to add as bidirectional adjacency (~0.30) or handle as industry-conditional translation in cv_targeted.
- **Data observability tooling**: appears here in capability and terminology. Could overlap with platform-technology orientation if observability is treated as an operational discipline broader than data. Verify after orientation research.
- **Vector databases**: deliberately omitted from data-engineering terminology; will appear in ai-engineering specialty. Confirm during reconciliation that the split is clean (vector DB engineering = ai-engineering ownership).
- **CI/CD for data, infrastructure-as-code**: DataOps capability here. Could overlap with platform-technology orientation. Verify after orientation research.
- **Data integrity / ALCOA+**: appears in quality-compliance (program design) and could be relevant in data-engineering when working in regulated industries. Concept-level cross-reference may be needed.

---

## rules/specialties/ai-engineering.md

**Researched:** 2026-04-29

### Sources used
- Hiring/skills: ResumeAdapter (AI Engineer 2026), KORE1 (Agentic AI Engineers 2026, LLM Engineers 2026), SecondTalent (Top 10 AI skills 2026), HiringHello (AI Engineer Roadmap 2026)
- Agent frameworks: Intuz (Top 5 frameworks 2026), Softmax (Definitive Guide 2026), DEV Community (MCP-Native vs Traditional), Future AGI, AIMultiple, FrankX
- Evaluation: Braintrust (Best LLM eval platforms 2025), LangWatch (LangSmith/Braintrust/Langfuse/Langwatch comparison), Arize, Maxim
- RAG: arXiv (Agentic RAG survey 2501.09136, A-RAG 2602.03442), DataNucleus (Enterprise Guide 2025), Pinecone, Microsoft Azure, Signity
- Fine-tuning: YoungJu (LLM Fine-tuning 2026 guide), PatSnap (RLHF vs DPO patent analysis), Red Hat (Post-training methods 2025), Phil Schmid (DPO 2025), Hugging Face (TRL/PEFT)

### Key decisions
- DPO and RLAIF added to fine-tuning vocabulary — DPO is now production-default (40-75% lower compute than RLHF, more stable training).
- Multi-agent system orchestration promoted to capability — Gartner expects ~33% of agentic deployments to be multi-agent by 2027; agentic AI is the steepest-growth subcategory.
- Named agent frameworks: LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, Anthropic Agent SDK — current top frameworks in 2026 hiring market.
- Model Context Protocol (MCP) added as capability and terminology — emerging industry standard for agent-to-tool communication, supported by VS Code/JetBrains/Anthropic/others.
- LLMOps split from MLOps — distinct discipline with different observability tools (LangSmith/Braintrust/Langfuse) and evaluation patterns.
- Inference engine vocabulary expanded: vLLM, TGI, Triton, SGLang, Ollama (current production engines); added optimization terms (quantization formats GGUF/AWQ, KV cache, prompt caching, speculative decoding).
- Agentic RAG, contextual retrieval, graph RAG added — current RAG evolution beyond pure-vector retrieval.
- Multi-modal as new terminology line — multi-modal applications now baseline.
- DeepSeek added to foundation models list.

### Reconciliation candidates
- **Quality-compliance to ai-engineering adjacency**: emerging in regulated industries via FDA AI/ML guidance, CSV/CSA validation of AI systems, model bias evaluation as compliance work. Industry-conditional. Decide during reconciliation whether to add bidirectional adjacency at ~0.25 or handle as industry-conditional translation in cv_targeted.
- **Data-engineering vs ai-engineering boundary on inference/serving**: vLLM and inference engines live here, not in data-engineering. Boundary appears clean.
- **Vector databases**: confirmed lives here (per data-engineering reconciliation note). Resolved.
- **MLOps/LLMOps observability vs data-engineering observability**: LangSmith/Braintrust/Langfuse here; Monte Carlo/Bigeye in data-engineering. Tool families don't overlap; observability *concept* could be a shared theme worth noting but tool-level split is clean.
- **Model Context Protocol (MCP)**: appears as ai-engineering capability/terminology. Could grow into broader integration vocabulary if MCP adoption extends beyond AI tools.

---

## rules/specialties/people-leadership.md

**Researched:** 2026-04-29

### Sources used
- Hiring/skills: EnhanceCV (People Manager 2026), ResumeAdapter (Management 2026), TheInterviewGuys (Top 50 Mgmt Keywords), Coursera, ResumeBuilder
- Engineering management: TealHQ (EM Skills 2025), engineeringmanagement.org, GeeksforGeeks (Top 10 EM Skills 2025), LeadDev, Adaface
- Performance management: ThriveSparrow (Stats 2025), KlaarHQ (Trends 2025), Deel, HR.com, DISA, Acciyo (continuous feedback)
- Org design: Team Topologies official site (key concepts, 2nd edition 2025), IT Revolution, Mia-Platform, microservices.io
- Distributed/hybrid: MIT Sloan (Hybrid Tips 2025), HRMorning (Remote 2025), Oyster, GoodHabitz, Workplaceless, TIMIFY

### Key decisions
- Continuous feedback added to performance management — current standard (80% of employees prefer ongoing feedback over annual reviews).
- Team Topologies framework named explicitly in capability and terminology — current dominant engineering org design framework (2nd edition 2025).
- Distributed/hybrid/remote leadership promoted to capability — only 27% of companies returned to fully in-person in 2025.
- Workforce restructuring/RIF leadership added — distinct skill following 2022-2024 layoff cycle and ongoing restructuring activity.
- Manager-of-managers and skip-level promoted from terminology to capability.
- Change frameworks (Kotter 8 steps, ADKAR, McKinsey 7-S) named — falsifiable signals over abstract "change leadership."
- DEI kept in terminology, not promoted to capability — politically dynamic; revisit if hiring-language stabilizes.

### Reconciliation candidates
- **Team Topologies as capability and terminology**: engineering-specific framework; for non-engineering people-leadership work it doesn't apply. Verify the framework reference doesn't bias the specialty toward engineering contexts.
- **Distributed/hybrid/remote leadership**: industry-agnostic capability with strong tech-industry resonance. Could overlap with platform-technology orientation if remote-first operating models are treated as orientation-level patterns.
- **Change frameworks**: appears here as change leadership. Could overlap with transformation-strategy orientation. Verify during reconciliation that change *leadership* (people-leadership lens) and transformation *strategy* (orientation lens) are cleanly separated.
- **Workforce restructuring / RIF leadership**: capability here. May appear in work-state axis as well (turnaround, divestiture work-states often involve RIF). Verify lens separation.
- **DEI**: in terminology but not promoted to capability. Revisit if hiring-language stabilizes.
