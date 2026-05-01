import json
import re

with open('temp/_inventory_entries_dump.json', 'r', encoding='utf-8') as f:
    entries = json.load(f)

LEADERSHIP_VERBS = ['accountable for', 'accountability for', 'oversaw', 'oversight', 'directed', 'owned', 'led ', 'governed', 'spearheaded', 'managed end-to-end', 'held accountability', 'held end-to-end', 'represented ', 'influenced', 'authored the recommendation', 'established', 'built ', 'designed and built', 'formed', 'architected', 'spearheaded']
IC_VERBS = ['performed', 'executed', 'conducted', 'applied ', 'reviewed', 'monitored ', 'tracked ', 'wrote ', 'prepared', 'developed', 'collaborated', 'assisted']

def infer_specialty(desc, impact, context, competency, role_title):
    text = ' '.join(filter(None, [desc, impact, context])).lower()
    specs = set()
    co_kw = ['site', 'monitor', 'cra', 'protocol', 'trial', 'phase 2', 'phase 3', 'phase 4', 'ind', 'irb', 'icf', 'ecrf', 'gcp', 'study', 'enrollment', 'subject', 'eclinical', 'rbm', 'rbqm', 'kri', 'qtl', 'data acquisition', 'data transfer', 'edc', 'ctms', 'investigator', 'feasibility', 'dbl', 'database lock', 'cro ', 'fsp', 'lab', 'central monitoring', 'sae']
    if any(k in text for k in co_kw): specs.add('clinical-operations')
    qc_kw = ['sop', 'audit', 'inspection', 'capa', 'alcoa', 'validat', 'csv', 'csa', 'gxp', 'governance framework', 'controlled documentation', 'deviation', 'quality system', 'iq oq', '21 cfr', 'compliance', 'regulatory framework']
    if any(k in text for k in qc_kw): specs.add('quality-compliance')
    de_kw = ['database', 'pipeline', 'etl', 'schema', 'data warehouse', 'databricks', 'lakehouse', 'cdisc', 'mapping library', 'data infrastructure', 'data flow', 'sdtm', 'data architecture', 'data product', 'transfer specification', 'machine-readable', 'data dictionary', 'standards']
    if any(k in text for k in de_kw): specs.add('data-engineering')
    ai_kw = ['ai ', 'machine learning', 'llm', 'predictive model', 'algorithm', 'anomaly detection', 'ai agent', 'ml ', 'nlp', 'decision engine']
    if any(k in text for k in ai_kw): specs.add('ai-engineering')
    pl_kw = ['team composition', 'team build', 'led the team', 'hired', 'hiring', 'coach', 'performance management', 'direct report', 'led a team', 'designed team', 'team formation', 'team development', 'team leadership']
    if any(k in text for k in pl_kw): specs.add('people-leadership')
    if competency:
        cl = competency.lower()
        if 'team leadership' in cl or 'organizational design' in cl:
            specs.add('people-leadership')
    return sorted(specs)

def infer_orientation(desc, impact, context, competency, work_state):
    text = ' '.join(filter(None, [desc, impact, context])).lower()
    comp = (competency or '').lower()
    scores = {'transformation-strategy': 0, 'data-analytics': 0, 'process-operations': 0, 'platform-technology': 0}
    ts_kw = ['greenfield', 'built new', 'operating model', 'redesigned', 'novel', 'established', 'capability build', 'function build', 'from scratch', 'transformation', 'formed and led']
    scores['transformation-strategy'] += sum(2 if k in text else 0 for k in ts_kw)
    if work_state == 'greenfield': scores['transformation-strategy'] += 2
    pt_kw = ['platform', 'architecture', 'databricks', 'lakehouse', 'system selection', 'system implementation', 'technology strategy', 'deployment strategy', 'system design', 'integration', 'api ']
    scores['platform-technology'] += sum(2 if k in text else 0 for k in pt_kw)
    if 'technology strategy' in comp: scores['platform-technology'] += 2
    da_kw = ['analyz', 'data-driven', 'predictive', 'statistical', 'insight', 'metric', 'trend', 'kpi', 'dashboard', 'visualiz', 'analytics']
    scores['data-analytics'] += sum(2 if k in text else 0 for k in da_kw)
    if 'data & analytics' in comp: scores['data-analytics'] += 1
    po_kw = ['operationalized', 'conducted', 'executed', 'performed', 'monitored', 'oversaw', 'applied', 'standardized', 'scaled', 'delivered', 'routine', 'process design', 'process improvement', 'lean', 'six sigma', 'efficiency', 'governance']
    scores['process-operations'] += sum(1 if k in text else 0 for k in po_kw)
    if 'process design' in comp: scores['process-operations'] += 1
    return max(scores, key=scores.get)

def check_level(current, desc, impact, context):
    text = ' '.join(filter(None, [desc, impact, context])).lower()
    has_leadership_verb = any(v in text for v in LEADERSHIP_VERBS)
    has_ic_verb = any(v in text for v in IC_VERBS)
    if current == 'leadership' and has_ic_verb and not has_leadership_verb:
        return 'flag-may-be-ic'
    if current == 'ic' and has_leadership_verb and not has_ic_verb:
        return 'flag-may-be-leadership'
    return 'ok'

SUBSEC_COMP = {
    'Clinical Monitoring & Site Management': ['Clinical Trial Execution'],
    'Vendor Management & Oversight': ['Vendor Management & Oversight'],
    'Risk-Based Monitoring & Quality': ['Risk-Based Monitoring & Quality'],
    'Clinical Trial Management & Oversight': ['Clinical Trial Execution'],
    'Data Science, Analytics & Engineering': ['Data & Analytics', 'AI Engineering & Development'],
    'Data Management & Quality Surveillance': ['Quality & Compliance', 'Data & Analytics', 'Vendor Management & Oversight'],
    'Technology Strategy, Evaluation & Platform': ['Technology Strategy & Implementation'],
    'Process Design & Governance': ['Process Design & Optimization', 'Governance & Risk Management'],
    'Organizational & Team Leadership': ['Team Leadership & Development', 'Organizational Design'],
    'Change Management, Training & Adoption': ['Change Management & Adoption'],
}

def check_subsection(subsec, competency):
    if not subsec or not competency:
        return 'ok'
    expected_list = SUBSEC_COMP.get(subsec, [])
    comps = [c.strip() for c in competency.split('|')]
    if not comps:
        return 'ok'
    primary = comps[0]
    if any(exp in comps for exp in expected_list):
        return 'ok'
    return f'flag-misplaced (primary={primary})'

proposals = []
for e in entries:
    p = {
        'id': e.get('id'),
        'subsection': e.get('subsection'),
        'title': (e.get('title') or e.get('project') or '')[:60],
        'company': e.get('company', ''),
        'level_current': e.get('level'),
        'level_check': check_level(e.get('level'), e.get('description'), e.get('impact'), e.get('context')),
        'work_state_current': e.get('work_state'),
        'specialty_proposed': infer_specialty(e.get('description'), e.get('impact'), e.get('context'), e.get('competency'), e.get('title') or e.get('project')),
        'orientation_proposed': infer_orientation(e.get('description'), e.get('impact'), e.get('context'), e.get('competency'), e.get('work_state')),
        'competency_current': e.get('competency', ''),
        'subsec_check': check_subsection(e.get('subsection'), e.get('competency')),
        'description_preview': (e.get('description', '') or '')[:200],
    }
    proposals.append(p)

with open('temp/_inventory_tagging_heuristic.json', 'w', encoding='utf-8') as f:
    json.dump(proposals, f, indent=2, ensure_ascii=False)

print(f'Total entries: {len(proposals)}')
print(f'Level flags: {sum(1 for p in proposals if p["level_check"] != "ok")}')
print(f'Subsection flags: {sum(1 for p in proposals if "flag" in p["subsec_check"])}')
print()
print('=== LEVEL FLAGS ===')
for p in proposals:
    if p['level_check'] != 'ok':
        ss = (p['subsection'] or 'N/A')[:30]
        print(f'  {p["id"]} ({ss}): {p["level_check"]} | current={p["level_current"]} | {p["title"][:50]}')
print()
print('=== SUBSECTION FLAGS ===')
for p in proposals:
    if 'flag' in p['subsec_check']:
        ss = (p['subsection'] or 'N/A')[:30]
        print(f'  {p["id"]} (in {ss}): {p["subsec_check"]}')
        print(f'    competency: {p["competency_current"]}')
        print(f'    title: {p["title"]}')
