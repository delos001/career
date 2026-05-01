"""Build CV for AstraZeneca Director, Process Management — Strategy (a): axes filter + Description ranking."""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def set_paragraph_spacing(p, sb=0, sa=0):
    pPr = p._p.get_or_add_pPr()
    spacing = pPr.find(qn('w:spacing'))
    if spacing is None:
        spacing = OxmlElement('w:spacing')
        pPr.append(spacing)
    spacing.set(qn('w:before'), str(int(sb * 20)))
    spacing.set(qn('w:after'), str(int(sa * 20)))
    spacing.set(qn('w:line'), '240')
    spacing.set(qn('w:lineRule'), 'auto')


def add_name(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p)
    r = p.add_run(text); r.font.name = 'Calibri'; r.font.size = Pt(18)


def add_contact(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p)
    r = p.add_run(text); r.font.name = 'Calibri'; r.font.size = Pt(10)


def add_section_header(doc, text):
    p = doc.add_paragraph(); set_paragraph_spacing(p, 8, 0)
    r = p.add_run(text); r.font.name = 'Calibri'; r.font.size = Pt(11); r.font.bold = True


def add_company_header(doc, text):
    p = doc.add_paragraph(); set_paragraph_spacing(p, 8, 0)
    r = p.add_run(text); r.font.name = 'Calibri'; r.font.size = Pt(11); r.font.bold = True


def add_job_title(doc, text, first=False):
    p = doc.add_paragraph(); set_paragraph_spacing(p, 0 if first else 8, 0)
    r = p.add_run(text); r.font.name = 'Calibri'; r.font.size = Pt(11); r.font.bold = True


def add_bullet(doc, text):
    p = doc.add_paragraph(); set_paragraph_spacing(p)
    pPr = p._p.get_or_add_pPr()
    ind = OxmlElement('w:ind'); ind.set(qn('w:left'), '144'); ind.set(qn('w:hanging'), '144'); pPr.append(ind)
    br = p.add_run('·  '); br.font.name = 'Cambria'; br.font.size = Pt(11)
    tr = p.add_run(text); tr.font.name = 'Calibri'; tr.font.size = Pt(11)


def add_body(doc, text):
    p = doc.add_paragraph(); set_paragraph_spacing(p)
    r = p.add_run(text); r.font.name = 'Calibri'; r.font.size = Pt(11)


doc = Document()
s = doc.sections[0]
s.top_margin = Inches(1); s.bottom_margin = Inches(1); s.left_margin = Inches(1); s.right_margin = Inches(1)

add_name(doc, 'JASON DELOSH')
add_contact(doc, '[Email] | [Phone] | LinkedIn: [LINKEDIN_URL] | github.com/jdelosh')

add_section_header(doc, 'Professional Summary')
add_body(doc, (
    "Pharma and biotech process leader with 25+ years across clinical development. Designs, governs, and "
    "optimizes clinical operations processes from greenfield to mature: data quality surveillance, data "
    "transfer agreements, vendor lifecycle, central statistical monitoring, and regulated-grade documentation. "
    "Lean Six Sigma Black Belt with applied experience in value stream mapping, SIPOC, root cause analysis, "
    "and KPI design. Targets director-level process management roles where process ownership, regulatory-grade "
    "documentation, governance, and continuous improvement methodology drive clinical execution quality."
))

add_section_header(doc, 'Core Competencies')
for c in [
    'Clinical process design, documentation, and lifecycle ownership',
    'Lean Six Sigma methodology (VSM, SIPOC, RCA, gap analysis)',
    'KPI design, performance monitoring, and quality dashboards',
    'Regulatory documentation and SOP authoring (ICH/GCP, 21 CFR Part 11, GxP)',
    'Governance frameworks, decision rights, and accountability design',
    'Cross-functional change management and adoption',
    'Vendor lifecycle, CRO partnership, and preferred-partner governance',
    'Audit response and inspection readiness',
    'People management, mentoring, and capability development',
    'Stakeholder influence in matrixed global organizations',
    'Project management of complex, multi-functional initiatives',
]:
    add_bullet(doc, c)

add_section_header(doc, 'Professional Experience')

# BioMarin
add_company_header(doc, 'BioMarin Pharmaceutical | Wake Forest, NC | 2020 to 2026')

add_job_title(doc, 'External Data Acquisition Head | 2024 to 2026', first=True)
for b in [
    'Built the external data acquisition function from greenfield: operating model, governance frameworks, decision rights, controlled documentation, and standards libraries. Team of four absorbed 200+ vendor transfers across 12+ external providers without FTE headcount growth.',
    'Redesigned and digitized the data transfer agreement process around a CDISC-aligned model with structured provider variability; trained cross-functional staff and external providers; replaced a generic legacy template that had produced persistent conformance failures.',
    'Applied SIPOC during capability roadmap development to frame functional capabilities and establish a high-level standard for downstream roadmaps. Used Lean as a structuring tool for strategic alignment, not as a project deliverable.',
    'Championed integration of data acquisition workflows into downstream regulatory submission, AI readiness, and quality processes; institutionalized adoption through training, controlled documentation handoff to end users, and recurring governance forums.',
    'Built domain-specific configuration and conformance libraries (DTA library by lab, 100+ check library tripling legacy breadth) to eliminate ad hoc per-study specifications across the provider portfolio.',
]:
    add_bullet(doc, b)

add_job_title(doc, 'Associate Director, Data Quality Sciences | 2022 to 2025')
for b in [
    'Redesigned data quality surveillance planning end-to-end: established cross-functional accountability frameworks, built a CDASH-aligned check library with criticality-based validation traceability, and eliminated the legacy one-size-fits-all template. Reduced mid-study programming rework across five functions.',
    'Applied value stream mapping to the database development process; surfaced redundancy, bottlenecks, and waste across people, technology, and process dimensions; delivered the VSM artifact to the development team for their continuous improvement work.',
    'Digitized the data management planning oversight infrastructure: standardized documentation, KPI-based reporting, and metadata foundations positioned for AI-enabled automation.',
    'Led onboarding of LLX Solutions as data management CRO partner: defined data sharing agreements, oversaw programming build-out, and established structured issue reporting; reduced laboratory data acquisition rework from approximately 50% to 0% across all governed studies.',
    'Optimized vendor spend through scope-based utilization analysis; identified two underutilized billable roles and consolidated annual billing to approximately $100K.',
    'Produced four competency-based structural models for Data Management Sciences (5 roles, 30+ FTEs and contractors), benchmarked against rare disease and small-cap biotech peers; informed adoption of a new functional structure.',
]:
    add_bullet(doc, b)

add_job_title(doc, 'Senior Manager, Clinical Data Management Sciences | 2021 to 2022')
for b in [
    'Identified data quality root causes through systematic comparison of datasets against transfer specifications across two pivotal studies; corrected specification errors and realigned test results; surveillance approach extended proactively to new studies at startup.',
    'Participated in for-cause audit of a central laboratory vendor; performed gap analysis across the end-to-end vendor data flow and reoriented the engagement model to restrict provider activities to core competency. Materially reduced data conformance issues.',
    'Held end-to-end accountability for data management activities across multiple pivotal Phase 3 studies; directed CDM audits, eTMF compliance, and team adherence to ICH/GCP regulatory document procedures.',
    'Directed external vendor partners and global matrix teams (US and offshore) across data acquisition and quality surveillance; facilitated cross-functional decisions with physicians, statisticians, programmers, and project managers.',
]:
    add_bullet(doc, b)

add_job_title(doc, 'Clinical Data Quality Consultant (via Ivory Solutions) | 2020 to 2021')
for b in [
    'Led acquisition and review of external laboratory data; governed execution of data transfer agreements and verified completeness and conformance to transfer specifications.',
]:
    add_bullet(doc, b)

# AbbVie
add_company_header(doc, 'AbbVie (via Clinical Solutions Group) | Durham, NC | 2019 to 2020')
add_job_title(doc, 'RBM & Analytics Consultant', first=True)
for b in [
    'Led cross-functional development of an Integrated Data Review Plan defining data quality standards across statistical sciences, clinical operations, data management, and pharmacovigilance; the plan governs downstream programming, dashboard, and tool configuration.',
    'Designed and rolled out the GitHub SME team operating framework across 12 to 15 team members: repository structure, controlled documentation, and adoption support.',
]:
    add_bullet(doc, b)

# PRA Health Sciences
add_company_header(doc, 'PRA Health Sciences | Raleigh, NC | 2018 to 2019')
add_job_title(doc, 'Clinical Data Scientist', first=True)
for b in [
    'Led Analysis of Findings meetings to communicate data findings and overall trial risk to cross-functional internal and external sponsor teams.',
    'Created tiering-level thresholds and priority categories for communication and escalation of data quality and site performance findings.',
]:
    add_bullet(doc, b)

# Amgen
add_company_header(doc, 'Amgen (via DOCS Global) | Durham, NC | 2016 to 2018')
add_job_title(doc, 'Central Statistical Monitoring Deployment Lead / Regional and Global Clinical Trial Manager (concurrent)', first=True)
for b in [
    'Led change management for enterprise-level CSM deployment as a net-new capability: built training content, communications plan, stakeholder engagement strategy, and signal response workflows across approximately 10 studies.',
    'Configured CSM algorithm parameters across a portfolio of studies through a governed specification sign-off process; tuned thresholds by clinical risk and maintained an ongoing feedback loop with PMs and statistics teams.',
    'Held end-to-end accountability for global and regional clinical trial execution: project planning, timelines, budget, vendor oversight, and risk management; led multi-regional matrix teams from start-up through close-out.',
]:
    add_bullet(doc, b)

# Grifols
add_company_header(doc, 'Grifols Pharmaceuticals (via People Solutions) | Durham, NC | 2015 to 2016')
add_job_title(doc, 'Lead Clinical Research Associate / Clinical Trial Lead', first=True)
for b in [
    'Managed CRO vendor activities and oversight across data management and clinical operations within scope of work; identified non-compliance and drove corrective action to resolution.',
]:
    add_bullet(doc, b)

# Quintiles
add_company_header(doc, 'Quintiles | Research Triangle Park, NC | 2011 to 2015')
add_job_title(doc, 'Integrated Process Technology Specialist II / Infosario Business Champion (concurrent)', first=True)
for b in [
    'Led enterprise-wide adoption of the Infosario Analytics platform across all programs and portfolios as Business Champion: delivered global training, end-user consultation, and liaison between Data Management, project teams, and IT.',
    'Designed risk-based monitoring triggers, thresholds, and controlled process documentation across two global RBM trials; developed and maintained validation documentation filed in eTMF.',
    'Standardized critical data entry oversight for a global study enrolling 21,000+ subjects; reported as instrumental to on-time database lock.',
]:
    add_bullet(doc, b)

# Earlier roles
add_section_header(doc, 'Earlier Professional Roles')
for b in [
    'Clinical Research Associate II | NeoVista Inc. | 2011',
    'Clinical Research Associate I/II | The Duke Clinical Research Institute | 2007 to 2011',
    'Clinical Research Technician | The Duke Clinical Research Institute | 2002 to 2006',
    'Pharmacy Technician | CVS Pharmacy | 2006 to 2007',
    'Certified Phlebotomy Technician | Duke Medical Center | 2000 to 2002',
    'Medic / Medical Technician 5 Level | United States Air Force | 1996 to 2000',
]:
    add_bullet(doc, b)

# Education
add_section_header(doc, 'Education')
for b in ['MS, Data Science, Northwestern University', 'MBA, Project Management focus']:
    add_bullet(doc, b)

# Certifications
add_section_header(doc, 'Certifications and Training')
add_bullet(doc, 'Lean Six Sigma Black Belt')

# Tech Proficiencies
add_section_header(doc, 'Technical Proficiencies')
add_body(doc, 'Per Inventory Section 5 (low weight per process-operations orientation framing).')

out = r'C:\Users\delos\code\career\temp\Jason_Delosh_CV_AZ_DirProcessMgmt_2026-05_strategy-a.docx'
doc.save(out)
print(f'Saved: {out}')
