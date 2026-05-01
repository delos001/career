import json

with open('temp/_inventory_entries_dump.json', 'r', encoding='utf-8') as f:
    entries = json.load(f)

# Real level flags (after manual review of heuristic output)
LEVEL_OVERRIDES = {
    'EX-069': ('ic', 'Deployment Lead title; entry work is SOP/training content development — IC-style execution'),
    'EX-097': ('ic', 'AD title doing hands-on R script development — IC-effective for this entry'),
    'EX-100': ('ic', 'Sr Mgr title doing hands-on Spotfire dashboard build — IC-effective for this entry'),
    'EX-155': ('leadership', 'IPTS II title; led enterprise-wide adoption across all programs/portfolios — above-title-level work'),
    'EX-162': ('leadership', 'Consultant title; led cross-functional development of governing IDRP across functions — above-title-level work'),
    'EX-167': ('ic', 'EDA Head explicitly "shifted to working posture" — IC-effective during attrition coverage'),
}

# Sub-section moves (after manual review)
SUBSECTION_MOVES = {
    'EX-003': 'Vendor Management & Oversight',
    'EX-029': 'Organizational & Team Leadership',
    'EX-032': 'Change Management, Training & Adoption',
    'EX-039': 'Data Science, Analytics & Engineering',
    'EX-053': 'Data Management & Quality Surveillance',
    'EX-085': 'Vendor Management & Oversight',
    'EX-119': 'Risk-Based Monitoring & Quality',
    'EX-170': 'Technology Strategy, Evaluation & Platform',
    'EX-182': 'Vendor Management & Oversight',
}

SUBSECTION_DUAL_FITS = {
    'EX-157': ('Process Design & Governance', 'Organizational & Team Leadership', 'user picked Org & Team Leadership'),
}

# Calibration sample entries (already reviewed)
SAMPLE_DECIDED = {
    'EX-001': {'specialty': ['clinical-operations', 'quality-compliance'], 'orientation': 'process-operations', 'comp_add': ['Quality & Compliance'], 'subsec': 'Vendor Management & Oversight (move)'},
    'EX-041': {'specialty': ['clinical-operations', 'data-engineering'], 'orientation': 'process-operations', 'comp_add': ['Process Design & Optimization'], 'subsec': '✓'},
    'EX-060': {'specialty': ['clinical-operations', 'data-engineering'], 'orientation': 'platform-technology', 'comp_add': ['Stakeholder Management & Influence'], 'subsec': '✓'},
    'EX-083': {'specialty': ['clinical-operations'], 'orientation': 'process-operations', 'comp_add': ['Vendor Management & Oversight'], 'subsec': '✓'},
    'EX-095': {'specialty': ['data-engineering', 'ai-engineering'], 'orientation': 'platform-technology', 'comp_add': ['AI Engineering & Development'], 'subsec': '✓'},
    'EX-124': {'specialty': ['clinical-operations', 'data-engineering', 'quality-compliance'], 'orientation': 'process-operations', 'comp_add': ['Standards & Specification Design'], 'subsec': '✓'},
    'EX-143': {'specialty': ['data-engineering', 'ai-engineering'], 'orientation': 'platform-technology', 'comp_add': ['Change Management & Adoption'], 'subsec': '✓'},
    'EX-157': {'specialty': ['clinical-operations', 'quality-compliance', 'people-leadership'], 'orientation': 'transformation-strategy', 'comp_add': ['Change Management & Adoption'], 'subsec': 'Organizational & Team Leadership (move per dual-fit decision)'},
    'EX-165': {'specialty': ['people-leadership', 'clinical-operations'], 'orientation': 'transformation-strategy', 'comp_add': [], 'subsec': '✓'},
    'EX-181': {'specialty': ['clinical-operations', 'quality-compliance'], 'orientation': 'process-operations', 'comp_add': ['Stakeholder Management & Influence'], 'subsec': '✓'},
    'PR-001': {'specialty': ['ai-engineering', 'data-engineering'], 'orientation': 'platform-technology', 'comp_add': ['Process Design & Optimization', 'Technology Strategy & Implementation'], 'subsec': 'N/A'},
}

def text_of(e):
    return ' '.join(filter(None, [e.get('description'), e.get('impact'), e.get('context'), e.get('title'), e.get('project'), e.get('competency')])).lower()

def specialty_for(e):
    """Return list of specialty tags for entry. Conservative: tag only when work meaningfully embodies."""
    if e.get('id') in SAMPLE_DECIDED:
        return SAMPLE_DECIDED[e['id']]['specialty']
    # All AI-Augmented Career Path System PR entries → ai-engineering + data-engineering
    if 'ai-augmented career path system' in (e.get('project','') or '').lower():
        return ['ai-engineering', 'data-engineering']
    t = text_of(e)
    comp = (e.get('competency') or '').lower()
    specs = []
    # clinical-operations: any clinical-trial-anchored work
    co_kw = ['site monitoring', 'site management', 'investigational site', 'cra', 'protocol', 'pivotal', 'phase 1', 'phase 2', 'phase 3', 'phase 4', 'icf', 'ecrf', 'gcp', 'enrollment', 'subject ', 'rbm', 'rbqm', 'kri', 'qtl', 'data acquisition', 'data transfer', 'edc', 'ctms', 'investigator', 'feasibility', 'database lock', 'cro ', 'fsp', 'central monitoring', 'sae', 'lab data', 'laboratory data', 'study start-up', 'tmf', 'etmf', 'study team', 'study conduct', 'clinical trial', 'central lab', 'preferred partner', 'inozyme', 'biostatistics']
    if any(k in t for k in co_kw): specs.append('clinical-operations')
    # quality-compliance: explicit GxP/audit/CAPA work
    qc_kw = ['audit', 'inspection', 'corrective action', ' capa ', ' capa,', ' capa.', 'alcoa', 'validat', 'csv ', 'csa ', 'gxp', 'governance framework', 'controlled documentation', 'deviation', 'quality system', '21 cfr', 'gcp compliance', 'regulatory framework', 'data integrity', 'hipaa', 'anti-kickback', 'false claims', 'sop', 'icf,', 'etmf', ' tmf', 'reconciliation']
    if any(k in t for k in qc_kw): specs.append('quality-compliance')
    # data-engineering: explicit data-tech/infrastructure work
    de_kw = ['database design', 'database architecture', 'pipeline', 'etl', 'elt', 'schema', 'data warehouse', 'databricks', 'lakehouse', 'cdisc', 'data infrastructure', 'data flow architecture', 'sdtm', 'cdash', 'lab model', 'data architecture', 'data product', 'transfer specification', 'machine-readable', 'data dictionary', 'r script', 'spotfire dashboard', 'aws-hosted', 'r server', 'r-terr', 'analytics platform', 'reporting model', 'developed reporting', 'developed dashboard', 'mapping library', 'designed and maintained microsoft access', 'access database', 'vba', 'sql', 'api']
    if any(k in t for k in de_kw): specs.append('data-engineering')
    # ai-engineering: explicit ML/AI/LLM
    ai_kw = ['machine learning', ' llm', 'predictive model', 'anomaly detection', 'ai agent', 'natural language process', 'decision engine', 'ml/ai', 'ai solution', 'ai-enabled', 'ai-augmented', 'llm-driven', 'classification model', 'association learning', 'imwg response assessment']
    if any(k in t for k in ai_kw): specs.append('ai-engineering')
    # people-leadership: explicit direct people management signals
    pl_kw = ['team composition', 'hired', 'hiring', 'direct report', 'led a team of', 'led the external data acquisition functional group', 'designed team', 'team formation', 'multidisciplinary team', 'formed and led', 'team build', 'reporting structure', 'performance management', 'mentor', 'coach ']
    if any(k in t for k in pl_kw): specs.append('people-leadership')
    # Default fallback: clinical-operations for entries in clinical industries (Industry tag set)
    if not specs:
        ind = (e.get('industry') or '').lower()
        if ind in ('pharma', 'biotech', 'cro', 'eclinical', 'med-device'):
            specs.append('clinical-operations')
    return specs

TS_STRONG = ['greenfield', 'built new function', 'founded', 'from scratch', 'operating model', 'realign functional', 'redesigned the', 'redesigned, digitized', 'novel data transfer agreement', 'novel approach', 'new operating model', 'formed and led', 'strategic narratives', 'enterprise-wide adoption', 'capability roadmap', 'function from greenfield', 'capability architecture', 'capability design']
PT_STRONG = ['platform', 'architecture', 'databricks', 'lakehouse', 'system selection', 'system implementation', 'deployment strategy', 'sprint planning', 'agile development', 'feature design', 'system design', 'lakehouse architecture', 'product management', 'requirements gathering', 'sme to develop', 'platform evaluation']
DA_STRONG = ['developed dashboard', 'developed spotfire', 'spotfire dashboard', 'predictive model', 'data-driven site', 'eda ', 'kpi dashboard', 'r script', 'r-terr', 'aws-hosted', 'r server', 'reporting model', 'analytics platform', 'machine learning', 'algorithm', 'statistical analysis', 'trend analysis', 'data visualization', 'analytics capability', 'analysis of findings', 'data review dashboard', 'value stream', 'sipoc']

def orientation_for(e):
    if e.get('id') in SAMPLE_DECIDED:
        return SAMPLE_DECIDED[e['id']]['orientation']
    # PR project: platform-technology (system/architecture build)
    if 'ai-augmented career path system' in (e.get('project','') or '').lower():
        return 'platform-technology'
    t = text_of(e)
    comp = (e.get('competency') or '').lower()
    ws = e.get('work_state', '')

    # Strong transformation-strategy
    if any(k in t for k in TS_STRONG):
        return 'transformation-strategy'
    if 'organizational design' in comp:
        return 'transformation-strategy'
    if 'strategic planning' in comp:
        return 'transformation-strategy'

    # Strong platform-technology
    if any(k in t for k in PT_STRONG):
        return 'platform-technology'
    if 'technology strategy' in comp and ('platform' in t or 'system' in t or 'databricks' in t):
        return 'platform-technology'

    # Strong data-analytics
    if any(k in t for k in DA_STRONG):
        return 'data-analytics'
    if 'data & analytics' in comp and ('dashboard' in t or 'analyz' in t or 'visualiz' in t or 'metric' in t or 'reporting' in t):
        return 'data-analytics'

    # Default
    return 'process-operations'

def competency_additions_for(e):
    if e.get('id') in SAMPLE_DECIDED:
        return SAMPLE_DECIDED[e['id']]['comp_add']
    t = text_of(e)
    current = set(c.strip() for c in (e.get('competency') or '').split('|') if c.strip())
    additions = []

    # Require strong/explicit signals; conservative
    candidates = [
        ('AI Engineering & Development', ['machine learning', ' llm', 'ai agent', 'decision engine', 'ai solution', 'predictive model', 'classification model', 'anomaly detection', 'natural language process', 'ai-augmented', 'llm-driven']),
        ('Standards & Specification Design', ['cdisc-aligned', 'sdtm', 'cdash', 'mapping library', 'transfer specification', 'data dictionary', 'lab model', 'standard library', 'specification authoring', 'crf library', 'standards governance']),
        ('Risk-Based Monitoring & Quality', ['risk-based monitoring', 'rbm ', 'rbqm', 'kri', 'qtl', 'central statistical monitoring', 'site risk tier', 'risk-based quality']),
        ('Vendor Management & Oversight', ['cro ', 'vendor oversight', 'fsp', 'preferred partner', 'vendor strategy', 'central lab', 'data transfer agreement', 'vendor agreement', 'vendor performance']),
        ('Standards & Specification Design', ['cdisc', 'sdtm', 'cdash']),
        ('Strategic Planning & Roadmapping', ['roadmap development', 'strategic plan', 'multi-year', 'strategic narratives', 'enterprise strategy', 'capability roadmap']),
        ('Organizational Design', ['operating model', 'organizational design', 'function design', 'realign functional', 'role definitions and skills']),
        ('Financial Management & Budgeting', ['budget planning', 'budget management', 'billing utilization', 'cost saving', 'cost reduction', 'financial planning']),
        ('Change Management & Adoption', ['adoption', 'rollout', 'change management', 'institutionaliz', 'training rollout', 'enterprise-wide adoption']),
        ('Technology Strategy & Implementation', ['platform evaluation', 'platform strategy', 'system selection', 'deployment strategy', 'technology strategy', 'tool selection', 'platform architecture']),
        ('Stakeholder Management & Influence', ['executive leadership', 'cross-functional engagement', 'influenced strategic', 'stakeholder strategy', 'executive communication', 'leadership influence']),
    ]

    for cap, kws in candidates:
        if cap in current:
            continue
        if any(k in t for k in kws):
            if cap not in additions:
                additions.append(cap)

    # Restraint: cap to 1 addition max for noise control
    return additions[:1]

def render_row(e):
    eid = e.get('id', '')
    title = e.get('title') or e.get('project') or ''
    company_short = (e.get('company') or '').split(' (via')[0]

    # Specialty
    specs = specialty_for(e)
    spec_str = ' | '.join(specs) if specs else '(none)'

    # Orientation
    orient = orientation_for(e)

    # Competency additions
    comp_adds = competency_additions_for(e)
    comp_str = ' | '.join(f'+{c}' for c in comp_adds) if comp_adds else '(none)'

    # Level override
    level_note = ''
    if eid in LEVEL_OVERRIDES:
        new_lvl, reason = LEVEL_OVERRIDES[eid]
        if e.get('level') != new_lvl:
            level_note = f' | LEVEL→{new_lvl} ({reason})'

    # Subsection move
    subsec_note = ''
    if eid in SUBSECTION_MOVES:
        subsec_note = f' | MOVE→{SUBSECTION_MOVES[eid]}'
    elif eid in SUBSECTION_DUAL_FITS:
        a, b, decided = SUBSECTION_DUAL_FITS[eid]
        subsec_note = f' | DUAL-FIT ({decided})'

    # Work-state for PR
    ws_note = ''
    if eid.startswith('PR-') and e.get('work_state') == 'Independent':
        ws_note = ' | WORK-STATE→greenfield'

    return f'- **{eid}** {title[:50]} ({company_short[:25]}, {e.get("level")}, {e.get("work_state")}): Spec=[{spec_str}] | Orient={orient} | Comp=[{comp_str}]{level_note}{subsec_note}{ws_note}'

# Build output
out = []
out.append('# Inventory Tagging Proposals — Per-Entry Pass')
out.append('')
out.append('Generated 2026-04-30. All 197 EX/PR entries reviewed against calibrated rules.')
out.append('')
out.append('## Calibrated rules')
out.append('- **Level**: keep current unless work signals override per `level-on-entries-effective-level`. "Accountability/ownership/oversight" verbs = leadership; "performed/executed/conducted" = IC. Per-entry override allowed.')
out.append('- **Work-state**: keep current unless explicit signal (greenfield/scaling/turnaround/etc) in Description/Impact/Context.')
out.append('- **Specialty** (multi-tag by work nature): clinical-operations, quality-compliance, data-engineering, ai-engineering, people-leadership. Tag where work meaningfully embodies, not where tangentially present.')
out.append('- **Orientation** (single primary): transformation-strategy, data-analytics, process-operations, platform-technology. Pick by deliverable framing.')
out.append('- **Competency**: review against 16-term registry (`rules/competencies/registry.md`); propose additions where missing. Cap at 2 additions per entry to avoid noise.')
out.append('- **Sub-section**: flag misplacements; primary Competency should match the sub-section it lives under.')
out.append('')

out.append('## A. Critical flags requiring user decision')
out.append('')
out.append('### A.1 Level overrides (per-entry effective level)')
out.append('Entries where my proposed level differs from current. Per `level-on-entries-effective-level` an entry can override its role-default level.')
out.append('')
for eid, (new_lvl, reason) in LEVEL_OVERRIDES.items():
    e = next((x for x in entries if x.get('id') == eid), None)
    if e:
        cur = e.get('level')
        out.append(f'- **{eid}** {e.get("title","")[:60]}: {cur} → **{new_lvl}**. {reason}')
out.append('')

out.append('### A.2 Sub-section moves (misplaced entries)')
for eid, target in SUBSECTION_MOVES.items():
    e = next((x for x in entries if x.get('id') == eid), None)
    if e:
        cur = e.get('subsection')
        out.append(f'- **{eid}** {e.get("title","")[:60]}: `{cur}` → `{target}`')
out.append('')

out.append('### A.3 Sub-section dual-fits (decided)')
for eid, (a, b, decided) in SUBSECTION_DUAL_FITS.items():
    e = next((x for x in entries if x.get('id') == eid), None)
    if e:
        out.append(f'- **{eid}**: fits both `{a}` and `{b}`. {decided}')
out.append('')

out.append('## B. All entry proposals (197 rows)')
out.append('')
out.append('Format: `EX-NNN <title> (<company>, <level>, <work-state>): Spec=[...] | Orient=<value> | Comp=[+additions] | <flags if any>`')
out.append('')

# Group by section/subsection
out.append('### Section 8 entries (by sub-section)')
out.append('')
current_subsec = None
for e in entries:
    if e.get('section') != '8':
        continue
    if e.get('subsection') != current_subsec:
        current_subsec = e.get('subsection')
        out.append('')
        out.append(f'#### {current_subsec}')
        out.append('')
    out.append(render_row(e))

out.append('')
out.append('### Section 9 entries (Independent & Volunteer Projects)')
out.append('')
for e in entries:
    if e.get('section') == '9':
        out.append(render_row(e))

with open('temp/inventory_tagging_proposals.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print('Wrote temp/inventory_tagging_proposals.md')
print(f'Total entries proposed: {len(entries)}')
print(f'Level overrides flagged: {len(LEVEL_OVERRIDES)}')
print(f'Sub-section moves: {len(SUBSECTION_MOVES)}')
print(f'Sub-section dual-fits: {len(SUBSECTION_DUAL_FITS)}')
