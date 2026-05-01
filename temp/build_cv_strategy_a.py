"""Build CV for Insmed Director, Data Acquisition & Partnerships — Strategy (a): axes filter + Description ranking."""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def set_paragraph_spacing(p, space_before_pt=0, space_after_pt=0):
    pPr = p._p.get_or_add_pPr()
    spacing = pPr.find(qn('w:spacing'))
    if spacing is None:
        spacing = OxmlElement('w:spacing')
        pPr.append(spacing)
    spacing.set(qn('w:before'), str(int(space_before_pt * 20)))
    spacing.set(qn('w:after'), str(int(space_after_pt * 20)))
    spacing.set(qn('w:line'), '240')
    spacing.set(qn('w:lineRule'), 'auto')


def add_name(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p, 0, 0)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(18)


def add_contact(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p, 0, 0)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(10)


def add_section_header(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 8, 0)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.bold = True


def add_company_header(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 8, 0)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.bold = True


def add_job_title(doc, text, first_under_company=False):
    p = doc.add_paragraph()
    space_before = 0 if first_under_company else 8
    set_paragraph_spacing(p, space_before, 0)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.font.bold = True


def add_bullet(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 0, 0)
    pPr = p._p.get_or_add_pPr()
    ind = OxmlElement('w:ind')
    ind.set(qn('w:left'), '144')
    ind.set(qn('w:hanging'), '144')
    pPr.append(ind)
    bullet_run = p.add_run('·  ')
    bullet_run.font.name = 'Cambria'
    bullet_run.font.size = Pt(11)
    text_run = p.add_run(text)
    text_run.font.name = 'Calibri'
    text_run.font.size = Pt(11)


def add_body(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, 0, 0)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)


doc = Document()
section = doc.sections[0]
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
section.left_margin = Inches(1)
section.right_margin = Inches(1)

# Header
add_name(doc, 'JASON DELOSH')
add_contact(doc, '[Email] | [Phone] | LinkedIn: [LINKEDIN_URL] | github.com/jdelosh')

# Professional Summary
add_section_header(doc, 'Professional Summary')
add_body(doc, (
    "Pharmaceutical and biotech leader with 25+ years across clinical development and 6+ years building "
    "and governing third-party data acquisition capabilities in regulated environments. Stood up BioMarin's "
    "external data acquisition function from greenfield: established the operating model, governance "
    "frameworks, decision rights, vendor lifecycle, and standards libraries that absorbed 200+ vendor "
    "data transfers across 12+ external providers without proportional headcount growth. Translates ambiguous "
    "data-strategy goals into governed, fit-for-purpose data ecosystems that produce business decisions "
    "rather than administrative deliverables. Targets director-level data acquisition and partnership roles "
    "where operating-model design, vendor governance, and cross-functional adoption determine whether data "
    "investment compounds or drifts."
))

# Core Competencies
add_section_header(doc, 'Core Competencies')
competencies = [
    'Operating model design and capability buildout (greenfield to governed)',
    'Data acquisition strategy and external data partnership governance',
    'Cross-functional governance frameworks and decision-rights design',
    'Vendor evaluation, negotiation, and lifecycle performance management',
    'Data inventory, catalog, and standards library development',
    'Regulatory-aware data governance (HIPAA, 21 CFR Part 11, ICH/GCP, GxP)',
    'Stakeholder influence in matrixed environments without formal authority',
    'Change management, adoption design, and council facilitation',
    'Strategic technology evaluation and platform selection',
    'Executive communication and cross-functional roadmap alignment',
    'Data quality, fit-for-purpose evaluation, and conformance design',
]
for c in competencies:
    add_bullet(doc, c)

# Professional Experience
add_section_header(doc, 'Professional Experience')

add_company_header(doc, 'BioMarin Pharmaceutical | Wake Forest, NC | 2020 to 2026')
add_job_title(doc, 'External Data Acquisition Head | 2024 to 2026', first_under_company=True)
bullets_eda = [
    'Stood up the external data acquisition function from greenfield: defined the operating model, decision rights, controlled documentation, governance frameworks, and standards libraries within Data Management Sciences. Lean, multidisciplinary team of four absorbed 200+ vendor transfers across 12+ external providers in the first full year without FTE headcount growth.',
    'Redesigned and digitized the data transfer agreement framework around a standard-but-flexible CDISC-aligned model with structured capture of provider-specific variability; updated SOPs, trained cross-functional staff and external providers, and positioned the workflow for downstream automation and AI-enabled conformance. Generated positive provider feedback and replaced a generic legacy template that had produced persistent conformance failures.',
    'Spearheaded the preferred-partner laboratory model with the enterprise procurement initiative: defined data acquisition and conformance assessment criteria, narrowed a fragmented field of approximately 40 providers to 3 preferred partners across routine, safety, and PK domains, and replaced ad hoc single-vendor concentration that had diluted negotiating leverage and concentrated risk.',
    'Applied the DTA governance framework to absorb the unplanned Inozyme acquisition integration spanning 5 studies, 7+ vendors, and 30+ datasets; executed all data transfer agreements, completed test transfers, and delivered conformance evaluation ahead of interim analysis cutoffs. Personal execution absorbed concurrent team attrition without delaying any cross-functional deliverable.',
    'Advised executive leadership on enterprise data, AI, and platform strategy; authored the Databricks selection recommendation, defined and prioritized an 8-use-case portfolio aligned to functional goals, and directed initiation of three priority use cases (EDC API connectivity, data blinding, data warehouse and data flow testing). Secured $65K evaluation budget and negotiated sandbox access from list to $15K through coordinated cross-functional procurement.',
    'Partnered with cross-functional leaders (clinical operations, product management, solution architects, procurement) to integrate data acquisition workflows into downstream regulatory submission, AI-readiness, and quality processes; institutionalized adoption through training, controlled documentation handoff to end users, and recurring governance forums.',
]
for b in bullets_eda:
    add_bullet(doc, b)

add_job_title(doc, 'Associate Director, Data Quality Sciences | 2022 to 2025')
bullets_ad = [
    'Led onboarding of LLX Solutions as data management CRO partner: defined data sharing agreements, oversaw programming build-out, and established structured issue reporting that doubled the number of domain-customized quality checks and accelerated dataset resolution timelines during interim analysis windows. Reduced laboratory data acquisition rework from approximately 50% to 0% across all governed studies.',
    'Optimized vendor spend through scope-based utilization analysis: identified two underutilized LLX billable roles (programmer at approximately 20% utilization, project manager at approximately 10%) and consolidated annual billing to approximately $100K.',
    'Produced four competency-based structural models for the Data Management Sciences group (5 roles, 30+ FTEs and contractors), benchmarked against comparable rare disease and small-cap biotech peers; presented directly to leadership and informed adoption of a substantively aligned target structure.',
    'Redesigned data quality surveillance planning capabilities end-to-end: established cross-functional accountability frameworks, built a CDASH-aligned check library with traceability between data criticality and validation effort, and removed the one-size-fits-all legacy template. Materially reduced mid-study quality programming rework across Data Management Sciences, Clinical Sciences, Statistical Sciences, Clinical Operations, and Pharmacovigilance.',
    'Advised leadership on enterprise and functional technology strategy and shaped ML/AI integration roadmaps and functional priorities; contributed to enterprise vendor strategy decisions for CRO and laboratory preferred partner initiatives.',
]
for b in bullets_ad:
    add_bullet(doc, b)

add_job_title(doc, 'Senior Manager, Clinical Data Management Sciences | 2021 to 2022')
bullets_sm = [
    'Designed workflows and use cases to expand SQL Server platform utilization across Data Management Sciences; led automation development and oversaw ETL pipeline build-out for operational data processing.',
    'Participated in recruitment and selection for over 50 data management science candidates, supporting functional capability growth during an extended scaling period.',
]
for b in bullets_sm:
    add_bullet(doc, b)

add_company_header(doc, 'AbbVie (via Clinical Solutions Group) | Durham, NC | 2019 to 2020')
add_job_title(doc, 'RBM & Analytics Consultant', first_under_company=True)
bullets_abbvie = [
    'Led cross-functional development of an Integrated Data Review Plan defining data quality standards and review procedures across statistical sciences, clinical operations, data management, medical monitoring, and safety; the plan governs downstream programming, dashboard, and tool configuration decisions.',
    'Designed and rolled out the GitHub SME team operating framework across 12 to 15 team members: repository structure, controlled documentation, and training reduced inconsistent programming storage practices.',
]
for b in bullets_abbvie:
    add_bullet(doc, b)

add_company_header(doc, 'Amgen (via DOCS Global) | Durham, NC | 2016 to 2018')
add_job_title(doc, 'Central Statistical Monitoring Deployment Lead (concurrent with Regional and Global Clinical Trial Manager roles)', first_under_company=True)
bullets_amgen = [
    'Led change management for enterprise-level deployment of central statistical monitoring as a net-new capability at Amgen: built training content, communications plan, stakeholder engagement strategy, and signal response workflows across approximately 10 studies. Managed resistance from teams accustomed to traditional monitoring while establishing foundational understanding of statistical signal concepts alongside operational procedures.',
]
for b in bullets_amgen:
    add_bullet(doc, b)

add_company_header(doc, 'Quintiles | Research Triangle Park, NC | 2011 to 2015')
add_job_title(doc, 'Integrated Process Technology Specialist II / Infosario Business Champion (concurrent)', first_under_company=True)
bullets_quintiles = [
    'Led enterprise-wide adoption of the Infosario Analytics platform across all Quintiles programs and portfolios as Business Champion: delivered global training (sessions of 100+ attendees), end-user consultation, and liaison between Data Management, project teams, and IT; replaced spreadsheet-based reporting with a real-time platform across study execution, data quality, and clinical safety domains.',
]
for b in bullets_quintiles:
    add_bullet(doc, b)

# Earlier Roles
add_section_header(doc, 'Earlier Professional Roles')
earlier = [
    'Lead CRA / Clinical Trial Lead, Grifols Pharmaceuticals (2015 to 2016)',
    'Clinical Data Scientist, PRA Health Sciences (2018 to 2019)',
    'Clinical Research Associate II, NeoVista Inc. (2011)',
    'Clinical Research Associate I/II, The Duke Clinical Research Institute (2007 to 2011)',
]
for e in earlier:
    add_bullet(doc, e)

# Education
add_section_header(doc, 'Education')
add_bullet(doc, 'MS, Data Science, Northwestern University')
add_bullet(doc, 'MBA, Project Management focus')

# Certifications
add_section_header(doc, 'Certifications and Training')
add_bullet(doc, 'Lean Six Sigma Black Belt')

# Tech Proficiencies
add_section_header(doc, 'Technical Proficiencies')
add_body(doc, 'Per Inventory Section 5 (low weight per orientation framing).')

out = r'C:\Users\delos\code\career\temp\Jason_Delosh_CV_Insmed_DirDataAcq_2026-05_strategy-a.docx'
doc.save(out)
print(f'Saved: {out}')
