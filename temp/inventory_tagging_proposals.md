# Inventory Tagging Proposals — Per-Entry Pass

Generated 2026-04-30. All 197 EX/PR entries reviewed against calibrated rules.

## Calibrated rules
- **Level**: keep current unless work signals override per `level-on-entries-effective-level`. "Accountability/ownership/oversight" verbs = leadership; "performed/executed/conducted" = IC. Per-entry override allowed.
- **Work-state**: keep current unless explicit signal (greenfield/scaling/turnaround/etc) in Description/Impact/Context.
- **Specialty** (multi-tag by work nature): clinical-operations, quality-compliance, data-engineering, ai-engineering, people-leadership. Tag where work meaningfully embodies, not where tangentially present.
- **Orientation** (single primary): transformation-strategy, data-analytics, process-operations, platform-technology. Pick by deliverable framing.
- **Competency**: review against 16-term registry (`rules/competencies/registry.md`); propose additions where missing. Cap at 2 additions per entry to avoid noise.
- **Sub-section**: flag misplacements; primary Competency should match the sub-section it lives under.

## A. Critical flags requiring user decision

### A.1 Level overrides (per-entry effective level)
Entries where my proposed level differs from current. Per `level-on-entries-effective-level` an entry can override its role-default level.

- **EX-069** Central Statistical Monitoring Deployment Lead: leadership → **ic**. Deployment Lead title; entry work is SOP/training content development — IC-style execution
- **EX-097** Associate Director, Data Quality Sciences: leadership → **ic**. AD title doing hands-on R script development — IC-effective for this entry
- **EX-100** Senior Manager, Clinical Data Management Sciences: leadership → **ic**. Sr Mgr title doing hands-on Spotfire dashboard build — IC-effective for this entry
- **EX-155** Integrated Process Technology Specialist II: ic → **leadership**. IPTS II title; led enterprise-wide adoption across all programs/portfolios — above-title-level work
- **EX-162** RBM & Analytics Consultant: ic → **leadership**. Consultant title; led cross-functional development of governing IDRP across functions — above-title-level work
- **EX-167** External Data Acquisition Head: leadership → **ic**. EDA Head explicitly "shifted to working posture" — IC-effective during attrition coverage

### A.2 Sub-section moves (misplaced entries)
- **EX-003** Lead Clinical Research Associate: `Clinical Monitoring & Site Management` → `Vendor Management & Oversight`
- **EX-029** Clinical Research Associate I/II: `Clinical Monitoring & Site Management` → `Organizational & Team Leadership`
- **EX-032** Clinical Research Associate I/II: `Clinical Monitoring & Site Management` → `Change Management, Training & Adoption`
- **EX-039** Clinical Research Technician: `Clinical Monitoring & Site Management` → `Data Science, Analytics & Engineering`
- **EX-053** Senior Manager, Clinical Data Management Sciences: `Vendor Management & Oversight` → `Data Management & Quality Surveillance`
- **EX-085** Senior Manager, Clinical Data Management Sciences: `Clinical Trial Management & Oversight` → `Vendor Management & Oversight`
- **EX-119** Clinical Data Scientist: `Data Science, Analytics & Engineering` → `Risk-Based Monitoring & Quality`
- **EX-170** External Data Acquisition Head: `Organizational & Team Leadership` → `Technology Strategy, Evaluation & Platform`
- **EX-182** Associate Director, Data Quality Sciences: `Change Management, Training & Adoption` → `Vendor Management & Oversight`

### A.3 Sub-section dual-fits (decided)
- **EX-157**: fits both `Process Design & Governance` and `Organizational & Team Leadership`. user picked Org & Team Leadership

## B. All entry proposals (197 rows)

Format: `EX-NNN <title> (<company>, <level>, <work-state>): Spec=[...] | Orient=<value> | Comp=[+additions] | <flags if any>`

### Section 8 entries (by sub-section)


#### Clinical Monitoring & Site Management

- **EX-001** Lead Clinical Research Associate (Grifols Pharmaceuticals, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[+Quality & Compliance]
- **EX-002** Lead Clinical Research Associate (Grifols Pharmaceuticals, ic, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-003** Lead Clinical Research Associate (Grifols Pharmaceuticals, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)] | MOVE→Vendor Management & Oversight
- **EX-004** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-005** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-006** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-007** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-008** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-009** Clinical Research Associate II (NeoVista Inc., ic, scaling): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-010** Clinical Research Associate II (NeoVista Inc., ic, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-011** Clinical Research Associate II (NeoVista Inc., ic, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-012** Clinical Research Associate II (NeoVista Inc., ic, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-013** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-014** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-015** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-016** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-017** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-018** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-019** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-020** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-021** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-022** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-023** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-024** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=data-analytics | Comp=[(none)]
- **EX-025** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=platform-technology | Comp=[(none)]
- **EX-026** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-027** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-028** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-029** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)] | MOVE→Organizational & Team Leadership
- **EX-030** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-031** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-032** Clinical Research Associate I/II (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)] | MOVE→Change Management, Training & Adoption
- **EX-033** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-034** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-035** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-036** Clinical Research Technician (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-037** Clinical Research Technician (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-038** Clinical Research Technician (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-039** Clinical Research Technician (The Duke Clinical Researc, ic, mature): Spec=[data-engineering] | Orient=data-analytics | Comp=[(none)] | MOVE→Data Science, Analytics & Engineering
- **EX-040** Clinical Research Technician (The Duke Clinical Researc, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]

#### Vendor Management & Oversight

- **EX-041** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | data-engineering] | Orient=process-operations | Comp=[+Process Design & Optimization]
- **EX-042** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-043** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-044** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-045** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=platform-technology | Comp=[+Technology Strategy & Implementation]
- **EX-046** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-047** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-048** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-049** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | data-engineering] | Orient=transformation-strategy | Comp=[+Standards & Specification Design]
- **EX-050** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-051** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-052** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-053** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)] | MOVE→Data Management & Quality Surveillance
- **EX-054** Sr. Data Scientist, Data Management Sciences (BioMarin Pharmaceutical, ic, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-055** Sr. Data Scientist, Data Management Sciences (BioMarin Pharmaceutical, ic, scaling): Spec=[clinical-operations | data-engineering] | Orient=process-operations | Comp=[+Standards & Specification Design]
- **EX-056** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-057** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=platform-technology | Comp=[(none)]
- **EX-058** Lead Clinical Research Associate (Grifols Pharmaceuticals, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-059** Lead Clinical Research Associate (Grifols Pharmaceuticals, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]

#### Risk-Based Monitoring & Quality

- **EX-060** RBM Software Consultant (eClinical Solutions, ic, scaling): Spec=[clinical-operations | data-engineering] | Orient=platform-technology | Comp=[+Stakeholder Management & Influence]
- **EX-061** RBM Software Consultant (eClinical Solutions, ic, scaling): Spec=[clinical-operations] | Orient=platform-technology | Comp=[(none)]
- **EX-062** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-063** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-064** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-065** Central Statistical Monitoring Deployment Lead (Amgen, leadership, mature): Spec=[clinical-operations | quality-compliance] | Orient=data-analytics | Comp=[(none)]
- **EX-066** Central Statistical Monitoring Deployment Lead (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-067** Central Statistical Monitoring Deployment Lead (Amgen, leadership, mature): Spec=[quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-068** Central Statistical Monitoring Deployment Lead (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-069** Central Statistical Monitoring Deployment Lead (Amgen, leadership, mature): Spec=[quality-compliance] | Orient=process-operations | Comp=[(none)] | LEVEL→ic (Deployment Lead title; entry work is SOP/training content development — IC-style execution)
- **EX-070** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-071** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-072** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations | data-engineering] | Orient=process-operations | Comp=[+Change Management & Adoption]
- **EX-073** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations | data-engineering] | Orient=process-operations | Comp=[(none)]
- **EX-074** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations | data-engineering] | Orient=data-analytics | Comp=[(none)]
- **EX-075** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[data-engineering] | Orient=data-analytics | Comp=[(none)]
- **EX-076** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-077** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-078** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-079** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-080** Central Statistical Monitoring Deployment Lead (Amgen, leadership, mature): Spec=[clinical-operations | ai-engineering] | Orient=data-analytics | Comp=[+AI Engineering & Development]
- **EX-081** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-082** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[data-engineering] | Orient=process-operations | Comp=[(none)]

#### Clinical Trial Management & Oversight

- **EX-083** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Vendor Management & Oversight]
- **EX-084** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-085** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance | data-engineering] | Orient=process-operations | Comp=[+Standards & Specification Design] | MOVE→Vendor Management & Oversight
- **EX-086** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-087** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-088** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-089** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-090** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-091** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-092** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-093** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-094** Regional/Global Clinical Trial Manager (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]

#### Data Science, Analytics & Engineering

- **EX-095** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[data-engineering | ai-engineering] | Orient=platform-technology | Comp=[+AI Engineering & Development]
- **EX-096** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance | data-engineering] | Orient=platform-technology | Comp=[+Change Management & Adoption]
- **EX-097** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[data-engineering] | Orient=data-analytics | Comp=[(none)] | LEVEL→ic (AD title doing hands-on R script development — IC-effective for this entry)
- **EX-098** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[quality-compliance] | Orient=data-analytics | Comp=[(none)]
- **EX-099** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | data-engineering] | Orient=data-analytics | Comp=[+Standards & Specification Design]
- **EX-100** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | data-engineering] | Orient=data-analytics | Comp=[+Change Management & Adoption] | LEVEL→ic (Sr Mgr title doing hands-on Spotfire dashboard build — IC-effective for this entry)
- **EX-101** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[data-engineering] | Orient=data-analytics | Comp=[(none)]
- **EX-102** Sr. Data Scientist, Data Management Sciences (BioMarin Pharmaceutical, ic, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-103** Sr. Data Scientist, Data Management Sciences (BioMarin Pharmaceutical, ic, scaling): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-104** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality]
- **EX-105** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations | data-engineering] | Orient=data-analytics | Comp=[+Risk-Based Monitoring & Quality]
- **EX-106** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations | quality-compliance | data-engineering] | Orient=data-analytics | Comp=[+Risk-Based Monitoring & Quality]
- **EX-107** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality]
- **EX-108** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality]
- **EX-109** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations | ai-engineering] | Orient=transformation-strategy | Comp=[+Risk-Based Monitoring & Quality]
- **EX-110** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations | ai-engineering] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality]
- **EX-111** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality]
- **EX-112** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations | data-engineering] | Orient=data-analytics | Comp=[+Risk-Based Monitoring & Quality]
- **EX-113** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[+Vendor Management & Oversight]
- **EX-114** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-115** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[+Risk-Based Monitoring & Quality]
- **EX-116** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[data-engineering] | Orient=process-operations | Comp=[(none)]
- **EX-117** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-118** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations | quality-compliance] | Orient=platform-technology | Comp=[(none)]
- **EX-119** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)] | MOVE→Risk-Based Monitoring & Quality
- **EX-120** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations | data-engineering] | Orient=data-analytics | Comp=[(none)]
- **EX-121** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations | quality-compliance | data-engineering] | Orient=data-analytics | Comp=[+Risk-Based Monitoring & Quality]
- **EX-122** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-123** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]

#### Data Management & Quality Surveillance

- **EX-124** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | data-engineering | quality-compliance] | Orient=process-operations | Comp=[+Standards & Specification Design]
- **EX-125** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | data-engineering] | Orient=process-operations | Comp=[+Standards & Specification Design]
- **EX-126** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | data-engineering] | Orient=transformation-strategy | Comp=[+Standards & Specification Design]
- **EX-127** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-128** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[(none)]
- **EX-129** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | quality-compliance] | Orient=platform-technology | Comp=[(none)]
- **EX-130** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | quality-compliance] | Orient=platform-technology | Comp=[(none)]
- **EX-131** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | quality-compliance] | Orient=platform-technology | Comp=[(none)]
- **EX-132** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[quality-compliance | data-engineering] | Orient=process-operations | Comp=[+Standards & Specification Design]
- **EX-133** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | data-engineering] | Orient=process-operations | Comp=[+Standards & Specification Design]
- **EX-134** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Standards & Specification Design]
- **EX-135** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-136** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-137** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[ai-engineering] | Orient=process-operations | Comp=[(none)]
- **EX-138** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-139** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-140** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-141** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[quality-compliance] | Orient=process-operations | Comp=[(none)]
- **EX-142** Sr. Data Scientist, Data Management Sciences (BioMarin Pharmaceutical, ic, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]

#### Technology Strategy, Evaluation & Platform

- **EX-143** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[data-engineering | ai-engineering] | Orient=platform-technology | Comp=[+Change Management & Adoption]
- **EX-144** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | data-engineering] | Orient=transformation-strategy | Comp=[(none)]
- **EX-145** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | data-engineering] | Orient=platform-technology | Comp=[(none)]
- **EX-146** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | data-engineering] | Orient=platform-technology | Comp=[(none)]
- **EX-147** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=platform-technology | Comp=[(none)]
- **EX-148** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=platform-technology | Comp=[(none)]
- **EX-149** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-150** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[data-engineering] | Orient=platform-technology | Comp=[(none)]
- **EX-151** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[data-engineering | ai-engineering] | Orient=transformation-strategy | Comp=[+AI Engineering & Development]
- **EX-152** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[data-engineering] | Orient=platform-technology | Comp=[(none)]
- **EX-153** RBM Software Consultant (eClinical Solutions, ic, scaling): Spec=[clinical-operations] | Orient=platform-technology | Comp=[+Risk-Based Monitoring & Quality]
- **EX-154** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality]
- **EX-155** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[data-engineering] | Orient=transformation-strategy | Comp=[(none)] | LEVEL→leadership (IPTS II title; led enterprise-wide adoption across all programs/portfolios — above-title-level work)
- **EX-156** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]

#### Process Design & Governance

- **EX-157** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | quality-compliance | people-leadership] | Orient=transformation-strategy | Comp=[+Change Management & Adoption] | DUAL-FIT (user picked Org & Team Leadership)
- **EX-158** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[+Organizational Design]
- **EX-159** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[(none)]
- **EX-160** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[(none)]
- **EX-161** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[+Financial Management & Budgeting]
- **EX-162** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality] | LEVEL→leadership (Consultant title; led cross-functional development of governing IDRP across functions — above-title-level work)
- **EX-163** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-164** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-191** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-192** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[(none)]

#### Organizational & Team Leadership

- **EX-165** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[people-leadership | clinical-operations] | Orient=transformation-strategy | Comp=[(none)]
- **EX-166** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Vendor Management & Oversight]
- **EX-167** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)] | LEVEL→ic (EDA Head explicitly "shifted to working posture" — IC-effective during attrition coverage)
- **EX-168** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[(none)]
- **EX-169** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[(none)]
- **EX-170** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | ai-engineering] | Orient=transformation-strategy | Comp=[+Technology Strategy & Implementation] | MOVE→Technology Strategy, Evaluation & Platform
- **EX-171** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations | quality-compliance] | Orient=transformation-strategy | Comp=[(none)]
- **EX-172** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[people-leadership] | Orient=transformation-strategy | Comp=[(none)]
- **EX-173** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-174** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[(none)]
- **EX-175** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-176** Senior Manager, Clinical Data Management Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-177** Clinical Data Scientist (PRA Health Sciences, ic, mature): Spec=[clinical-operations | people-leadership] | Orient=process-operations | Comp=[(none)]
- **EX-178** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-179** In-House Clinical Research Associate (Quintiles, ic, mature): Spec=[people-leadership] | Orient=process-operations | Comp=[(none)]
- **EX-180** Clinical Research Associate II (NeoVista Inc., ic, scaling): Spec=[clinical-operations | people-leadership] | Orient=process-operations | Comp=[(none)]

#### Change Management, Training & Adoption

- **EX-181** External Data Acquisition Head (BioMarin Pharmaceutical, leadership, greenfield): Spec=[clinical-operations | quality-compliance] | Orient=process-operations | Comp=[+Stakeholder Management & Influence]
- **EX-182** Associate Director, Data Quality Sciences (BioMarin Pharmaceutical, leadership, scaling): Spec=[clinical-operations] | Orient=transformation-strategy | Comp=[+Vendor Management & Oversight] | MOVE→Vendor Management & Oversight
- **EX-183** RBM & Analytics Consultant (AbbVie, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[+Risk-Based Monitoring & Quality]
- **EX-184** Central Statistical Monitoring Deployment Lead (Amgen, leadership, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-185** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[data-engineering] | Orient=platform-technology | Comp=[(none)]
- **EX-186** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-187** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=data-analytics | Comp=[(none)]
- **EX-188** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-189** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]
- **EX-190** Integrated Process Technology Specialist II (Quintiles, ic, mature): Spec=[clinical-operations] | Orient=process-operations | Comp=[(none)]

### Section 9 entries (Independent & Volunteer Projects)

- **PR-001** AI-Augmented Career Path System (Independent, ic, Independent): Spec=[ai-engineering | data-engineering] | Orient=platform-technology | Comp=[+Process Design & Optimization | +Technology Strategy & Implementation] | WORK-STATE→greenfield
- **PR-002** AI-Augmented Career Path System (Independent, ic, Independent): Spec=[ai-engineering | data-engineering] | Orient=platform-technology | Comp=[(none)] | WORK-STATE→greenfield
- **PR-003** AI-Augmented Career Path System (Independent, ic, Independent): Spec=[ai-engineering | data-engineering] | Orient=platform-technology | Comp=[(none)] | WORK-STATE→greenfield
- **PR-004** AI-Augmented Career Path System (Independent, ic, Independent): Spec=[ai-engineering | data-engineering] | Orient=platform-technology | Comp=[(none)] | WORK-STATE→greenfield
- **PR-005** AI-Augmented Career Path System (Independent, ic, Independent): Spec=[ai-engineering | data-engineering] | Orient=platform-technology | Comp=[(none)] | WORK-STATE→greenfield