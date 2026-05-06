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

---

## rules/orientations/data-analytics.md

**Cleanup pass:** 2026-04-29
**External research:** 2026-04-29

### Methodology shift
Orientation files differ from industry/specialty files: the closed decision in `temp/design_decisions.md` line 45 scopes orientation as "governs deliverable structure" — a presentation lens, not a domain. External-source research (practitioner CVs, frameworks) targets domain claims; for orientations the testable claim is whether the file describes CV framing rules without bleeding into domain content. First pass on each orientation file is therefore an internal scope-cleanup, not a research sweep. External research, if any remains, runs after cleanup.

### Key decisions
- Identity rewritten to describe the CV frame ("CV is framed as...", "headline deliverables read as...") instead of the work types ("characteristic contexts: building analytics functions..."). Selection rule rephrased as "select when target role's primary deliverable is..." rather than "applies when the candidate directs..." (level scope removed; level is its own axis).
- Adjacency bullets rewritten as re-anchoring rules ("translates when entry's deliverable can be re-anchored on X outcome") instead of domain-of-work descriptions ("platform work involving data infrastructure...").
- Summary lead and Section emphasis sections kept as-is; both already describe presentation rules.
- `last_researched` field unchanged (no external research run).

### Reconciliation candidates
- **Adjacency weights (frontmatter)**: 0.60 platform-technology, 0.55 process-operations, 0.40 transformation-strategy. Body uses binary "translates / does not translate" language; weight semantics live in cv_targeted (`cv-targeted-weighted-matching` deferral). Verify weights are reciprocal with paired files during reconciliation.
- **Section emphasis claim**: "Technical Proficiencies carries more weight than transformation-strategy or process-operations orientations." Comparative claim across orientation files; verify after process-operations and transformation-strategy cleanups whether the relative weighting holds and is symmetric.
- **Identity selection rule references other orientations**: "use platform-technology" and "use process-operations" exclusion criteria. Verify those orientations have reciprocal selection criteria after their cleanup passes. (Resolved: data-analytics now names all three; see Selection rule asymmetry resolution below.)

### External research sources used
- QwikResume CDO resume samples 2026; QwikResume VP Data Analytics 2026
- Resume Worded: CDO skills, Director of Analytics, Data Science VP, Senior Data Analyst (all 2026 editions)
- Enhancv: 26 CDO Resume Examples 2026
- CIO.com: CDO resumes — 5 tips
- Wozber: Chief Analytics Officer Resume Example
- Deloitte: 2026 CDO playbook on data stewardship
- ServiceNow Workflow: Ideal CDO Resume profile
- iCareerSolutions: 2025 CDO Resume Examples + Guide
- MIT/Accenture CDO success-skills survey (cited across multiple resume guides)

### External research key decisions
- Identity headline deliverables: added "data translated into action that executives or operators can use." Rationale: MIT/Accenture CDO survey names "translator" as a top-six success skill (34%); resume guides consistently cite "translating data into actionable insights" as a senior-data-leader signal. Current file captured the output (decision-relevant insight) but not the act (translation). Made explicit.
- Summary lead: added "translation of data into business outcomes" to lead-with content. Same source basis. "Data storytelling" appears in research as the popular branding; "translation" used as the more durable framing.
- Section emphasis claim that Technical Proficiencies "carries more weight" than transformation-strategy or process-operations orientations: confirmed. Multiple sources state senior data CVs require "credible technical skills near the top" while leading with strategy. Comparative-vs-other-orientations claim is consistent with the data-leadership-specific emphasis on technical credentials.
- "Does-not-lead-with" content (programming languages, ML method names, tools): confirmed. "Lead with strategic impact and leadership examples while maintaining credible technical skills" is the dominant 2026 convention.
- Core Competencies three-zone split (data strategy/governance, analytics capability/operating model, technical credibility): confirmed. Research cites the same three-zone composition.
- "Change agent" / "evangelist" framings (top CDO success skills): not added to orientation file. These are level-axis territory (leadership scope/influence) and would be domain bleed if added here.
- Multi-year horizon / strategic roadmap framing: not added. Level-axis territory.

---

## rules/orientations/process-operations.md

**Cleanup pass:** 2026-04-29
**External research:** 2026-04-29

### Key decisions
- Identity rewritten to describe CV frame and headline deliverables; "characteristic contexts" enumeration of work types removed. Selection rule rephrased as "select when target role's primary deliverable is..." with reciprocal exclusion criteria pointing to platform-technology, data-analytics, transformation-strategy.
- Adjacency bullets rewritten as re-anchoring rules. Pattern matches data-analytics: "translates when entry's deliverable can be re-anchored on X outcome."
- Summary lead and Section emphasis sections kept as-is; both already describe presentation rules.
- `last_researched` field unchanged.

### Reconciliation candidates
- **Adjacency weights (frontmatter)**: 0.50 transformation-strategy, 0.55 data-analytics, 0.55 platform-technology. data-analytics→process-operations is also 0.55, so that pair is reciprocal. Verify transformation-strategy and platform-technology pairings during their cleanup.
- **Selection rule reciprocity**: process-operations exclusion now points to all three other orientations. data-analytics exclusion points to platform-technology and process-operations only (no transformation-strategy mention). Asymmetry resolved 2026-04-29 in data-analytics.md.

### External research sources used
- Resume Worded: VP Operations, Operational Excellence Director, Operations Director, Process Improvement Manager, Process Manager (2026 editions)
- QwikResume: VP of Operations samples 2026
- iCareerSolutions: VP of Operations Resume 2026; COO Resume 2026
- MakeTheResume: COO/VP Operations Resume Writing Guide 2026
- CVCompiler: Process Improvement Manager Resume Examples 2026
- iCert Global: Lean Six Sigma Career Growth 2026 strategy guide
- Resume Genius: COO Resume Example 2026
- Enhancv: COO Resume Examples & Guide 2026

### External research key decisions
- Removed "regulated-environment execution" from Summary lead `lead-with content` list. Rationale: industry-axis territory (regulated industries) bleeding into orientation file. Orientation should be domain-agnostic; regulated-industry signal layers in via pharma.md / quality-compliance.md / clinical-operations.md.
- No additions made for Lean Six Sigma / Kaizen / DMAIC / Value Stream Mapping methodology names. Rationale: orientation files exclude method-name vocabulary by design (matches how data-analytics excludes ML method names from lead-with). Methodologies belong in specialty axes or cv_targeted procedural rules.
- Existing headline deliverables (durable process improvement, governance/SOP frameworks, harmonization across sites/functions) confirmed against current research. No edits.
- Section emphasis (Core Competencies on process design/governance/risk/stakeholder influence; Technical Proficiencies low weight; Professional Experience on efficiency/risk/quality/inspection) confirmed. Per process-ops convention, methodology certifications live in Certifications section, not Technical Proficiencies, so the "low weight" claim for Technical Proficiencies is research-aligned.
- Cross-functional team leadership, change management, P&L accountability, multi-year horizon: not added. Level-axis or transformation-strategy-axis territory.

---

## rules/orientations/platform-technology.md

**Cleanup pass:** 2026-04-29
**External research:** 2026-04-29

### Key decisions
- Identity rewritten to describe CV frame and headline deliverables; "characteristic contexts" enumeration removed. Removed "applies whether the candidate directs... or contributes hands-on" sentence (level scope; level is its own axis).
- Selection rule rephrased; exclusion criteria point to data-analytics, process-operations, transformation-strategy.
- Adjacency bullets rewritten as re-anchoring rules.
- Summary lead and Section emphasis kept as-is.
- `last_researched` field unchanged.

### Reconciliation candidates
- **Adjacency weights (frontmatter)**: 0.40 transformation-strategy, 0.60 data-analytics, 0.55 process-operations. data-analytics→platform-technology is 0.60 (reciprocal); process-operations→platform-technology is 0.55 (reciprocal); transformation-strategy→platform-technology is 0.40 (reciprocal). All reciprocal, confirmed.

### External research sources used
- Enhancv: 27 CTO Resume Examples 2026; 10 VP of Engineering Resume Examples 2026; 10 Platform Engineer Resume Examples 2026
- iCareerSolutions: CTO Resume Examples 2026
- Resume Genius: CTO Resume Examples & Template 2026
- Resume Worded: CTO Skills 2026; VP Engineering Skills 2026; Platform Engineer CV Examples 2026
- PlatformEngineering.org: What does a Head of Platform Engineering do
- Appsvolt: Platform Engineering 2026 — Building Internal Developer Platforms
- Calmops: Internal Developer Platform IDP 2026 Complete Guide
- Northflank: Top 6 IDPs for 2026
- Gartner (cited across sources): 80% of engineering organizations will have an IDP by 2026

### External research key decisions
- Identity headline deliverables: added "platform adoption and user outcomes improved." Rationale: 2026 dominant framing for platform leadership is platform-as-product with user/developer experience as the outcome measure (not the platform itself). Multiple sources cite "treating internal developers as customers," "platform teams act as internal product managers," "impact on reliability, scalability, and developer productivity over descriptive task lists." Generalized to "user outcomes" so the framing applies to any platform (CRM, ERP, customer-facing systems), not just developer platforms.
- Summary lead: added "platform adoption and user outcomes" to lead-with content. Same source basis. Used durable language ("user outcomes") rather than time-bound terminology ("platform-as-product," "DevEx") to avoid datedness.
- Section emphasis claim that Technical Proficiencies is "expanded relative to transformation-strategy and process-operations orientations" with systems/platforms as priority subsection: confirmed. Research consistently names tools (Kubernetes, Terraform, CI/CD, observability stacks, cloud platforms) as required signal for platform leadership CVs.
- Core Competencies three-zone split (technology strategy/governance, systems/domain, cross-functional credibility): confirmed.
- "Does-not-lead-with" content (programming languages, data science methods, hands-on configuration): confirmed. CTO research explicitly states: "the list of candidates who understand technology is a lot longer than the one of those who can think strategically" — strategic framing differentiates.
- Cross-functional partnerships (security, compliance, finance), strategic-and-hands-on balance, multi-year horizon: not added. Level-axis territory.
- Specific tool names (Kubernetes, Terraform, etc.): not added. Tools-vocabulary territory belongs in cv_targeted procedural rules or specialty axes (data-engineering, ai-engineering currently host tool vocabulary).

---

## rules/orientations/transformation-strategy.md

**Cleanup pass:** 2026-04-29
**External research:** 2026-04-29

### Key decisions
- Identity rewritten to describe CV frame and headline deliverables; "characteristic contexts" enumeration removed. Em-dash in original Identity ("structural change — not a product...") removed per global writing-style rule.
- Selection rule rephrased; exclusion criteria point to all three other orientations (process-operations, platform-technology, data-analytics) plus the "incremental improvements reframed as transformation" guard.
- Adjacency bullets rewritten as re-anchoring rules.
- Summary lead and Section emphasis kept as-is.
- `last_researched` field unchanged.

### Reconciliation candidates
- **Adjacency weights (frontmatter)**: 0.40 data-analytics, 0.50 process-operations, 0.40 platform-technology. data-analytics→transformation-strategy is 0.40 (reciprocal); process-operations→transformation-strategy is 0.50 (reciprocal); platform-technology→transformation-strategy is 0.40 (reciprocal). All reciprocal, confirmed.

### External research sources used
- Resume Worded: Chief Transformation Officer Resume Examples 2026; Digital Transformation Resume Examples 2026; Change Management Resume Examples 2026; Senior Change Manager Resume Examples 2026; Business Transformation Consultant Resume Examples 2026
- Wozber: Chief Transformation Officer Resume Example
- iCareerSolutions: Chief Transformation Officer Resume Examples 2025
- emlyon business school: How to Become a Chief Transformation Officer
- McKinsey: Avoiding pitfalls in operating model transformation
- HR Executive: 5 ways to build transformations that really matter in 2026
- CVCompiler: 13 Corporate Strategy Resume Examples 2026; 13 Change Management Resume Examples 2026
- LiveCareer: 4 Director Of Transformation Resume Examples 2025; 4 Digital Transformation Leader Resume Examples 2026

### External research key decisions
- Identity headline deliverables: changed "operating model redesigned" to "operating model redesigned and adopted." Rationale: 2026 transformation CV research repeatedly cites adoption rate as the differentiating outcome ("70% acceptance rate," "85% employee adoption rate"). Original headline deliverables list read as work-being-done verbs; adoption as outcome was implicit in Summary lead but missing from deliverable level. Made adoption explicit at the structural-change deliverable to align with current research-backed framing.
- Lead-with content (transformation, capability building, organizational change leadership, stakeholder navigation, cultural adoption, operating-model redesign): research-aligned. No edits.
- Section emphasis (change management, organizational design, stakeholder influence, capability building at top of Core Competencies; Technical Proficiencies low weight): confirmed.
- Specific change methodology names (Kotter 8-Step, ADKAR, Prosci, CCMP, Lean Change Management): not added. Methodology vocabulary belongs in cv_targeted procedural rules or specialty axes (people-leadership currently lists Kotter/ADKAR/McKinsey 7-S as change frameworks). Consistent with how data-analytics excludes ML method names and platform-technology excludes specific tool names.
- "Architect (High IQ) + Coach (High EQ)" framing for transformation leaders: not added. Level-axis territory (combining strategic and people skills at senior leadership scope).
- Digital transformation specifically: not added as a sub-area. Orientation should be durable; "digital" qualifier may date.
- "Translation" theme (cited as next frontier in one source): not added. Single-source signal; revisit if it becomes dominant in future research.

### Reconciliation candidates
- **Section emphasis references work-state axis values**: "greenfield, scaling, and turnaround contexts surface most strongly. Mature contexts without an explicit transformation anchor are off-spec." Same pattern in platform-technology.md ("greenfield, scaling, capability-building, risk-reduction contexts"). Cross-axis reference. Could be intentional (orientation describing which work-states frame well in this orientation) or unintentional bleed. Flag for cross-axis reconciliation.

---

## Cross-orientation findings (post-cleanup)

### Reciprocity check across all four orientation files
All adjacency weights are reciprocal across paired files. No asymmetry to resolve.

### Selection rule asymmetry (resolved)
Initial cleanup left data-analytics naming only platform-technology and process-operations in exclusion criteria. Resolved 2026-04-29 by adding transformation-strategy ("enterprise-scope organizational change") to the exclusion list. All four files now name all three peers.

### Methodology decision (candidate)
For axes derived from the prior archetype model, internal scope-cleanup precedes external research. Confirmed for orientations. Apply same evaluation to levels and work-states before research begins on those axes — both may also have domain bleed from archetype residue.

### Section emphasis comparative claims (verified by reading all four files)
- data-analytics says Technical Proficiencies "carries more weight than transformation-strategy or process-operations orientations." Confirmed: those two files say "low weight."
- platform-technology says Technical Proficiencies is "expanded relative to transformation-strategy and process-operations orientations." Confirmed.
- Comparative claims are internally consistent across the four files.

---

## rules/levels/ic.md and rules/levels/leadership.md

**Cleanup pass:** 2026-04-29
**External research:** 2026-04-29

### Methodology finding
Level files do not have the same archetype-residue domain bleed as orientation files. Levels axis is fundamentally about scope of authority, so scope-language content (project ownership, portfolio breadth, etc.) is level-axis-appropriate, not domain bleed. The cleanup-first methodology applied but yielded smaller edits than for orientations.

### Key decisions
- ic.md Voice: em-dash removed per global writing-style rule. Otherwise content kept intact.
- leadership.md Adjacency: em-dash removed (replaced with colon). Otherwise content kept intact.
- leadership.md Scope signals: pharma-specific parenthetical examples ("studies, programs, therapeutic areas, product lines") removed from the portfolio-breadth scale signal. Generic category retained. Parenthetical was archetype-era industry-flavored example carryover and was the only domain bleed identified across both level files.
- Verb vocabulary, adjacency rules, and scope-signals categories otherwise kept as-is. All level-axis appropriate.

### Reconciliation candidates
- **Adjacency weights (frontmatter)**: ic.md→leadership 0.40; leadership.md→ic 0.40. Reciprocal. Confirmed.
- **Voice gradient inside leadership.md**: "Director voice differs from Associate Director voice in scope and authority; both differ from VP and C-suite voice in horizon and breadth." Implies finer-grained level distinctions exist, which the `level-axis-finer-grained-files` deferral parks. Keep as-is until that deferral fires; revisit phrasing then.
- **"depth in a specific tool/method/domain" in ic.md scope signals**: references domain (specialty/industry territory) but used as a presentation marker for IC depth, not as a domain claim. Acceptable level-axis content.

### External research sources used
- Enhancv: 10 Senior Engineer Resume Examples 2026; 16 VP Resume Examples 2026
- IGotAnOffer: 5 Senior Software Engineer Resume Examples (Google, Amazon, etc.)
- LeadDev: Who are staff, principal, and distinguished engineers; Influencing without management authority as a senior IC
- REN Network: Resume Writing 101 for Senior Leaders
- Resume Worded: Action Verbs 2026; Management Action Verbs; C-Level and Executive Resume Examples 2026
- Page Executive: How to Write an Executive CV 2026
- Coursera: 150 Resume Action Words to Impress Employers 2026
- Medium / various: Senior IC vs Engineering Manager career path 2026

### External research key decisions
- ic.md Voice: changed senior-vs-junior IC differentiation from "depth, independence, and complexity, not in organizational scope" to "depth, independence, complexity, and breadth of technical influence, not in management authority." Rationale: research strongly supports that Staff/Principal-level IC scope does extend cross-team / cross-organization (architecture for an org area, influence across teams) — the original "not in organizational scope" qualifier under-stated this. New framing preserves the IC/leadership boundary at "management authority" (the actual line) rather than at "organizational scope" (which Staff/Principal cross via influence).
- ic.md Scope signals: added "architecture or system-scale decisions" and changed "technical leadership within a team" to "technical leadership and influence within or across teams." Rationale: 2026 senior IC research consistently names architecture-scale decisions and cross-team influence without authority as the Staff/Principal differentiator. "Influence without authority" was already in Adjacency but needed to surface in Scope signals where it acts as a level-detection marker.
- leadership.md Voice: added "teams scaled" to the organizational unit-of-work list. Rationale: 2026 leadership research emphasizes the people-development side of leadership voice ("scaled teams and organizations," "team-building," "grew teams") which the original Voice list (decisions made, capabilities built, functions led, cross-functional influence) under-captured. Scope signals already covered headcount via "headcount and budget responsibility" so no change there.
- Verb vocabularies (IC and leadership lists): research-aligned. No additions. Verb lists are illustrative not exhaustive; adding individual verbs (engineered, architected, led, oversaw, mentored) is endless and risks list bloat without changing the framing logic.
- Director/AD/VP/C-suite gradient in leadership.md Voice: research-aligned. Kept as-is. Implies finer-grained level distinctions exist; parked under `level-axis-finer-grained-files` deferral.
- Senior-IC vs junior-IC split discussion: research surfaces a real gap between junior IC and Staff/Principal framing. Decision (2026-04-29): not splitting `ic.md` now; bridging within one file via the proposed Voice/Scope refinements. Logged parallel deferral `ic-axis-finer-grained-files` mirroring the leadership-side `level-axis-finer-grained-files`. Trigger for revisit: Staff/Principal-flavored role application where unified file fails to carry senior IC voice cleanly.

---

## rules/work-states/*.md (all seven files)

**Cleanup pass:** 2026-04-29
**External research:** 2026-04-29

### Methodology finding
Work-states axis is about organizational state at the time of the work. Most "characteristic contexts" enumerations describe the state dynamic itself (greenfield = no prior structure; scaling = growth of working model; etc.) and are work-state-axis appropriate, not domain bleed. Clean files overall. Two pharma-specific examples surfaced.

### Key decisions
- divestiture.md: removed "therapeutic area" from "carving out a therapeutic area, business unit, or functional capability" — pharma-specific archetype-era example. Replaced with generic "business unit or functional capability."
- pivot.md: removed "redirecting a function from one therapeutic area to another" example — pharma-specific. Other generic examples (product line, service model, strategic priority) sufficient on their own.
- turnaround.md: parenthetical noting "crisis response is currently absorbed into turnaround" was undocumented as a deferral. Added entry `crisis-response-as-separate-work-state` to deferrals.md (trigger: experience-inventory entry surfaces that fits crisis-response and reads off-spec under turnaround).
- greenfield, scaling, mature, post-merger-integration, pivot Identity sections: no domain bleed, kept as-is.
- All Achievement framing sections: signal verbs and before/after framing patterns kept as-is. Work-state-axis appropriate.
- All Adjacency sections: translation rules kept as-is.
- `last_researched` fields unchanged across all seven files.

### Reconciliation candidates
- **Adjacency weights (frontmatter) reciprocity check**:
  - greenfield↔scaling: 0.65 ↔ 0.65 ✓
  - greenfield↔divestiture: 0.45 ↔ 0.45 ✓
  - greenfield↔pivot: 0.40 ↔ 0.40 ✓
  - scaling↔mature: 0.55 ↔ 0.55 ✓
  - scaling↔pivot: 0.45 ↔ 0.45 ✓
  - mature↔post-merger-integration: 0.45 ↔ 0.45 ✓
  - mature↔turnaround: 0.40 ↔ 0.40 ✓
  - turnaround↔pivot: 0.55 ↔ 0.55 ✓
  - turnaround↔post-merger-integration: 0.45 ↔ 0.45 ✓
  - post-merger-integration↔divestiture: 0.50 ↔ 0.50 ✓
  - divestiture↔pivot: 0.40 ↔ 0.40 ✓
  - All adjacency declarations reciprocal across paired files. No asymmetry to resolve.
- **Crisis-response distinction**: deferral added; revisit when experience inventory has a clear crisis-response candidate.

### External research sources used
- Enhancv: 27 CTO Resume Examples 2026; 49 Executive Resume Examples 2026
- BeamJobs: 5 Founder and CEO Resume Examples 2026
- Rezi: 20+ Startup Founder Resume Examples
- JRG Partners: Scaling Leadership Hiring Tech Executives for Hyper-Growth; Hiring for Turnaround and Restructuring Expertise
- Executive Job Experts: Executive Resume Examples 2026
- eAmped: Hypergrowth Playbook 2026; 2026 Guide to Scaling Your Startup
- Deloitte: 2026 Turnaround and Restructuring Outlook
- Hacking The Case Interview: Restructuring Case Interview Step-by-Step Guide
- BCG: Post-Merger Integration Framework, Strategy, and Consulting
- LEK Consulting: Post-Merger Integration capability page
- Aurelius: Carve-outs set to continue increase in 2026
- KPMG: Winning the carve-out relay (March 2026)
- Chief Executive: How To Do A Strategic Pivot — 8 CEOs Share
- TechRepublic: Top Trends Shaping Enterprise IT Infrastructure and Operations in 2026
- Resume Target: Director of Operations Resume 2026
- Resume Worded: Action Verbs 2026; C-Level Executive Resume Examples 2026

### External research key decisions
- 6 of 7 work-state files (greenfield, mature, turnaround, post-merger-integration, divestiture, pivot) research-validated against 2026 sources. No content edits. Identity, Achievement framing signal verbs, and Adjacency rules track current literature on each org-state.
- scaling.md: added "accelerated" to Achievement framing signal-verb list. Rationale: 2026 hyper-growth executive research consistently includes "accelerated" alongside scaled, expanded, replicated. Original list omitted it.
- Four-phase turnaround framework (Diagnose, Stabilize, Restructure, Reposition) appears in research but not added to turnaround.md. Methodology territory; belongs in cv_targeted procedural rules, not work-state file.
- IMO (Integration Management Office) and "Day One" PMI vocabulary appears in research but not added to post-merger-integration.md. Vocabulary territory; belongs in cv_targeted or specialty axes if PMI specialty surfaces.
- Talent retention / "retain critical employees through transition" appears in divestiture research but not added to divestiture.md. HR-specialty territory rather than work-state-axis content.
- Pivot research is dominated by career pivots (individuals changing industries), not business pivots (organization redirecting). Limited additional signal for pivot.md as a work-state. Existing framing (redirection without starting over, operational continuity) defensible.

### Reconciliation candidates
- **mature.md "regulated environments" phrasing**: "risk management within mature regulated environments" carries industry-condition framing into a work-state file. "Regulated" covers pharma/finance/healthcare/energy contexts — broader than any one industry but narrower than industry-agnostic. Removing it would weaken regulated-mature context coverage; keeping it carries some industry framing. Flag for cross-axis reconciliation.
