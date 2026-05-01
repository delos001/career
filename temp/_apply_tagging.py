"""
Apply tag updates to Experience_Inventory.md per the proposals.

Updates:
1. Specialty (multi-tag) per heuristic + sample-decided
2. Orientation (single) per heuristic + sample-decided
3. Level overrides for 5 entries
4. Competency additions per heuristic + sample-decided
5. Sub-section moves for 9 entries
6. Work-state for PR-001..PR-005: Independent -> greenfield
"""
import re
import json
import sys

PATH = 'personal/knowledge/Experience_Inventory.md'

# Approved level overrides (EX-167 NOT included per user disagreement)
LEVEL_OVERRIDES = {
    'EX-069': 'ic',
    'EX-097': 'ic',
    'EX-100': 'ic',
    'EX-155': 'leadership',
    'EX-162': 'leadership',
}

# Approved sub-section moves (EX-182 → Process Design & Governance per user choice; EX-157 reverted to PD&G no-op)
SUBSECTION_MOVES = {
    'EX-003': 'Vendor Management & Oversight',
    'EX-029': 'Organizational & Team Leadership',
    'EX-032': 'Change Management, Training & Adoption',
    'EX-039': 'Data Science, Analytics & Engineering',
    'EX-053': 'Data Management & Quality Surveillance',
    'EX-085': 'Vendor Management & Oversight',
    'EX-119': 'Risk-Based Monitoring & Quality',
    'EX-170': 'Technology Strategy, Evaluation & Platform',
    'EX-182': 'Process Design & Governance',
}

# Sample-decided values (calibration entries)
SAMPLE_DECIDED = {
    'EX-001': {'specialty': ['clinical-operations', 'quality-compliance'], 'orientation': 'process-operations', 'comp_add': ['Quality & Compliance']},
    'EX-041': {'specialty': ['clinical-operations', 'data-engineering'], 'orientation': 'process-operations', 'comp_add': ['Process Design & Optimization']},
    'EX-060': {'specialty': ['clinical-operations', 'data-engineering'], 'orientation': 'platform-technology', 'comp_add': ['Stakeholder Management & Influence']},
    'EX-083': {'specialty': ['clinical-operations'], 'orientation': 'process-operations', 'comp_add': ['Vendor Management & Oversight']},
    'EX-095': {'specialty': ['data-engineering', 'ai-engineering'], 'orientation': 'platform-technology', 'comp_add': ['AI Engineering & Development']},
    'EX-124': {'specialty': ['clinical-operations', 'data-engineering', 'quality-compliance'], 'orientation': 'process-operations', 'comp_add': ['Standards & Specification Design']},
    'EX-143': {'specialty': ['data-engineering', 'ai-engineering'], 'orientation': 'platform-technology', 'comp_add': ['Change Management & Adoption']},
    'EX-157': {'specialty': ['clinical-operations', 'quality-compliance', 'people-leadership'], 'orientation': 'transformation-strategy', 'comp_add': ['Change Management & Adoption']},
    'EX-165': {'specialty': ['people-leadership', 'clinical-operations'], 'orientation': 'transformation-strategy', 'comp_add': []},
    'EX-181': {'specialty': ['clinical-operations', 'quality-compliance'], 'orientation': 'process-operations', 'comp_add': ['Stakeholder Management & Influence']},
    'PR-001': {'specialty': ['ai-engineering', 'data-engineering'], 'orientation': 'platform-technology', 'comp_add': ['Process Design & Optimization', 'Technology Strategy & Implementation']},
}

TS_STRONG = ['greenfield', 'built new function', 'founded', 'from scratch', 'operating model', 'realign functional', 'redesigned the', 'redesigned, digitized', 'novel data transfer agreement', 'novel approach', 'new operating model', 'formed and led', 'strategic narratives', 'enterprise-wide adoption', 'capability roadmap', 'function from greenfield', 'capability architecture', 'capability design']
PT_STRONG = ['platform', 'architecture', 'databricks', 'lakehouse', 'system selection', 'system implementation', 'deployment strategy', 'sprint planning', 'agile development', 'feature design', 'system design', 'lakehouse architecture', 'product management', 'requirements gathering', 'sme to develop', 'platform evaluation']
DA_STRONG = ['developed dashboard', 'developed spotfire', 'spotfire dashboard', 'predictive model', 'data-driven site', 'eda ', 'kpi dashboard', 'r script', 'r-terr', 'aws-hosted', 'r server', 'reporting model', 'analytics platform', 'machine learning', 'algorithm', 'statistical analysis', 'trend analysis', 'data visualization', 'analytics capability', 'analysis of findings', 'data review dashboard', 'value stream', 'sipoc']

def text_of(e):
    return ' '.join(filter(None, [e.get('description'), e.get('impact'), e.get('context'), e.get('title'), e.get('project'), e.get('competency')])).lower()

def specialty_for(e):
    if e.get('id') in SAMPLE_DECIDED:
        return SAMPLE_DECIDED[e['id']]['specialty']
    if 'ai-augmented career path system' in (e.get('project','') or '').lower():
        return ['ai-engineering', 'data-engineering']
    t = text_of(e)
    specs = []
    co_kw = ['site monitoring', 'site management', 'investigational site', 'cra', 'protocol', 'pivotal', 'phase 1', 'phase 2', 'phase 3', 'phase 4', 'icf', 'ecrf', 'gcp', 'enrollment', 'subject ', 'rbm', 'rbqm', 'kri', 'qtl', 'data acquisition', 'data transfer', 'edc', 'ctms', 'investigator', 'feasibility', 'database lock', 'cro ', 'fsp', 'central monitoring', 'sae', 'lab data', 'laboratory data', 'study start-up', 'tmf', 'etmf', 'study team', 'study conduct', 'clinical trial', 'central lab', 'preferred partner', 'inozyme', 'biostatistics']
    if any(k in t for k in co_kw): specs.append('clinical-operations')
    qc_kw = ['audit', 'inspection', 'corrective action', ' capa ', ' capa,', ' capa.', 'alcoa', 'validat', 'csv ', 'csa ', 'gxp', 'governance framework', 'controlled documentation', 'deviation', 'quality system', '21 cfr', 'gcp compliance', 'regulatory framework', 'data integrity', 'hipaa', 'anti-kickback', 'false claims', 'sop', 'icf,', 'etmf', ' tmf', 'reconciliation']
    if any(k in t for k in qc_kw): specs.append('quality-compliance')
    de_kw = ['database design', 'database architecture', 'pipeline', 'etl', 'elt', 'schema', 'data warehouse', 'databricks', 'lakehouse', 'cdisc', 'data infrastructure', 'data flow architecture', 'sdtm', 'cdash', 'lab model', 'data architecture', 'data product', 'transfer specification', 'machine-readable', 'data dictionary', 'r script', 'spotfire dashboard', 'aws-hosted', 'r server', 'r-terr', 'analytics platform', 'reporting model', 'developed reporting', 'developed dashboard', 'mapping library', 'designed and maintained microsoft access', 'access database', 'vba', 'sql', 'api']
    if any(k in t for k in de_kw): specs.append('data-engineering')
    ai_kw = ['machine learning', ' llm', 'predictive model', 'anomaly detection', 'ai agent', 'natural language process', 'decision engine', 'ml/ai', 'ai solution', 'ai-enabled', 'ai-augmented', 'llm-driven', 'classification model', 'association learning', 'imwg response assessment']
    if any(k in t for k in ai_kw): specs.append('ai-engineering')
    pl_kw = ['team composition', 'hired', 'hiring', 'direct report', 'led a team of', 'led the external data acquisition functional group', 'designed team', 'team formation', 'multidisciplinary team', 'formed and led', 'team build', 'reporting structure', 'performance management', 'mentor', 'coach ']
    if any(k in t for k in pl_kw): specs.append('people-leadership')
    if not specs:
        ind = (e.get('industry') or '').lower()
        if ind in ('pharma', 'biotech', 'cro', 'eclinical', 'med-device'):
            specs.append('clinical-operations')
    return specs

def orientation_for(e):
    if e.get('id') in SAMPLE_DECIDED:
        return SAMPLE_DECIDED[e['id']]['orientation']
    if 'ai-augmented career path system' in (e.get('project','') or '').lower():
        return 'platform-technology'
    t = text_of(e)
    comp = (e.get('competency') or '').lower()
    if any(k in t for k in TS_STRONG):
        return 'transformation-strategy'
    if 'organizational design' in comp:
        return 'transformation-strategy'
    if 'strategic planning' in comp:
        return 'transformation-strategy'
    if any(k in t for k in PT_STRONG):
        return 'platform-technology'
    if 'technology strategy' in comp and ('platform' in t or 'system' in t or 'databricks' in t):
        return 'platform-technology'
    if any(k in t for k in DA_STRONG):
        return 'data-analytics'
    if 'data & analytics' in comp and ('dashboard' in t or 'analyz' in t or 'visualiz' in t or 'metric' in t or 'reporting' in t):
        return 'data-analytics'
    return 'process-operations'

def competency_additions_for(e):
    if e.get('id') in SAMPLE_DECIDED:
        return SAMPLE_DECIDED[e['id']]['comp_add']
    t = text_of(e)
    current = set(c.strip() for c in (e.get('competency') or '').split('|') if c.strip())
    additions = []
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
    return additions[:1]

def parse_inventory():
    """Parse file into: header, section8 (subsec -> entries), background_roles, section9_entries, footer."""
    with open(PATH, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')

    # Find boundaries
    sec8_start = next(i for i, l in enumerate(lines) if l == '## 8. All Tasks Performed')
    bg_start = next(i for i, l in enumerate(lines) if l == '## Background Roles (Not Tagged)')
    sec9_start = next(i for i, l in enumerate(lines) if l == '## 9. Independent & Volunteer Projects')
    sec10_start = next(i for i, l in enumerate(lines) if l == '## 10. Academic Coursework Detail')

    header_lines = lines[:sec8_start]
    sec8_lines = lines[sec8_start:bg_start]
    bg_lines = lines[bg_start:sec9_start]
    sec9_lines = lines[sec9_start:sec10_start]
    sec10_lines = lines[sec10_start:]

    # Parse Section 8 sub-sections and entries
    sec8_data = {'header': [], 'subsections': {}}  # subsec_name -> [list of entry blocks]
    current_subsec = None
    in_entry = False
    current_entry_lines = []
    leading_sec8_lines = []  # lines before first subsection
    found_first_subsec = False

    for line in sec8_lines:
        if line.startswith('### '):
            # Save previous entry if any
            if current_entry_lines:
                sec8_data['subsections'].setdefault(current_subsec, []).append(current_entry_lines)
                current_entry_lines = []
            current_subsec = line[4:].strip()
            sec8_data['subsections'].setdefault(current_subsec, [])
            found_first_subsec = True
            continue
        if not found_first_subsec:
            leading_sec8_lines.append(line)
            continue
        # Within a subsection
        if re.match(r'^ID: (EX|PR)-', line):
            # Save previous entry if any
            if current_entry_lines:
                sec8_data['subsections'].setdefault(current_subsec, []).append(current_entry_lines)
            current_entry_lines = [line]
        elif current_entry_lines:
            # Continuation of entry — empty line ends entry
            if line.strip() == '':
                # End of entry block
                if current_entry_lines:
                    sec8_data['subsections'].setdefault(current_subsec, []).append(current_entry_lines)
                current_entry_lines = []
            else:
                current_entry_lines.append(line)
    # Final entry
    if current_entry_lines:
        sec8_data['subsections'].setdefault(current_subsec, []).append(current_entry_lines)

    sec8_data['leading'] = leading_sec8_lines
    sec8_data['subsec_order'] = []
    for line in sec8_lines:
        if line.startswith('### '):
            sec8_data['subsec_order'].append(line[4:].strip())

    # Parse Section 9 entries
    sec9_entries = []
    leading_sec9_lines = []
    current_entry_lines = []
    seen_first_id = False
    for line in sec9_lines:
        if re.match(r'^ID: (EX|PR)-', line):
            if not seen_first_id:
                seen_first_id = True
            if current_entry_lines:
                sec9_entries.append(current_entry_lines)
            current_entry_lines = [line]
        elif current_entry_lines:
            if line.strip() == '':
                sec9_entries.append(current_entry_lines)
                current_entry_lines = []
            else:
                current_entry_lines.append(line)
        elif not seen_first_id:
            leading_sec9_lines.append(line)
    if current_entry_lines:
        sec9_entries.append(current_entry_lines)

    return {
        'header': header_lines,
        'sec8': sec8_data,
        'bg': bg_lines,
        'sec9_leading': leading_sec9_lines,
        'sec9_entries': sec9_entries,
        'sec10': sec10_lines,
    }

def parse_entry_block(block_lines):
    """Parse a list of entry lines into a dict of fields."""
    e = {}
    for line in block_lines:
        for fname in ['ID', 'Title', 'Project', 'Company', 'Industry', 'Specialty', 'Orientation', 'Level', 'Work-state', 'Competency', 'Added', 'Last Used', 'Description', 'Impact', 'Context']:
            if line.startswith(fname + ':'):
                e[fname.lower().replace('-', '_')] = line[len(fname)+1:].strip()
                break
    return e

def render_entry(e_lines, updates):
    """Render entry with applied updates. Preserves field order and adds missing fields where needed."""
    # Updates is a dict potentially with: industry, specialty, orientation, level, competency (full), work_state
    new_lines = []
    for line in e_lines:
        rendered = False
        for fname, key in [('Specialty', 'specialty'), ('Orientation', 'orientation'), ('Level', 'level'), ('Work-state', 'work_state'), ('Competency', 'competency')]:
            if line.startswith(fname + ':') and key in updates:
                new_lines.append(f'{fname}: {updates[key]}')
                rendered = True
                break
        if not rendered:
            new_lines.append(line)
    return new_lines

def apply():
    data = parse_inventory()

    # Process Section 8 entries: collect all, apply updates, group by target subsection
    all_entries_by_id = {}  # id -> {subsec, lines, parsed}
    for subsec, entry_blocks in data['sec8']['subsections'].items():
        for block in entry_blocks:
            parsed = parse_entry_block(block)
            eid = parsed.get('id')
            if eid:
                all_entries_by_id[eid] = {'subsec': subsec, 'lines': block, 'parsed': parsed}

    # Section 9 entries
    sec9_parsed = []
    for block in data['sec9_entries']:
        parsed = parse_entry_block(block)
        sec9_parsed.append({'lines': block, 'parsed': parsed})

    # Apply tag updates: build new field values per entry
    def compute_updates(parsed):
        updates = {}
        eid = parsed.get('id')
        # Specialty
        specs = specialty_for(parsed)
        updates['specialty'] = ' | '.join(specs) if specs else ''
        # Orientation
        updates['orientation'] = orientation_for(parsed)
        # Level override
        if eid in LEVEL_OVERRIDES:
            updates['level'] = LEVEL_OVERRIDES[eid]
        # Competency: current + additions
        current_comps = [c.strip() for c in (parsed.get('competency') or '').split('|') if c.strip()]
        adds = competency_additions_for(parsed)
        for a in adds:
            if a not in current_comps:
                current_comps.append(a)
        updates['competency'] = ' | '.join(current_comps)
        # Work-state for PR Independent -> greenfield
        if eid and eid.startswith('PR-') and parsed.get('work_state') == 'Independent':
            updates['work_state'] = 'greenfield'
        return updates

    # Apply updates to all entries
    for eid, info in all_entries_by_id.items():
        updates = compute_updates(info['parsed'])
        info['lines'] = render_entry(info['lines'], updates)

    for s9 in sec9_parsed:
        updates = compute_updates(s9['parsed'])
        s9['lines'] = render_entry(s9['lines'], updates)

    # Now reorganize Section 8: assign each entry to target subsection
    new_subsec_groups = {s: [] for s in data['sec8']['subsec_order']}
    # Preserve original order within subsection unless moved
    for subsec in data['sec8']['subsec_order']:
        for block in data['sec8']['subsections'].get(subsec, []):
            parsed = parse_entry_block(block)
            eid = parsed.get('id')
            if not eid:
                continue
            # Determine target subsection
            target = SUBSECTION_MOVES.get(eid, subsec)
            # Use the updated lines
            new_subsec_groups[target].append(all_entries_by_id[eid]['lines'])

    # Reconstruct file
    out = []
    out.extend(data['header'])
    out.append('## 8. All Tasks Performed')
    out.extend(data['sec8']['leading'][1:])  # skip the header line we already added
    for subsec in data['sec8']['subsec_order']:
        out.append(f'### {subsec}')
        out.append('')
        for entry_lines in new_subsec_groups[subsec]:
            out.extend(entry_lines)
            out.append('')
        out.append('---')
        out.append('')
    # Background Roles
    out.extend(data['bg'])
    # Section 9 leading
    out.extend(data['sec9_leading'])
    out.append('## 9. Independent & Volunteer Projects')
    # actually leading already includes the header; fix:
    # Reset and do this more carefully
    # Actually we need sec9 properly
    # Strip first occurrence of leading 9 header from leading
    pass

    # Simpler reconstruction approach
    out = []
    out.extend(data['header'])
    out.append('## 8. All Tasks Performed')
    # Section 8 has empty line + --- between header and first subsec
    out.append('')
    out.append('---')
    out.append('')
    for subsec in data['sec8']['subsec_order']:
        out.append(f'### {subsec}')
        out.append('')
        for entry_lines in new_subsec_groups[subsec]:
            out.extend(entry_lines)
            out.append('')
        out.append('---')
        out.append('')
    # Background Roles
    out.extend(data['bg'])
    # Section 9
    # Find where in data['sec9_leading'] the header is — it's already in there; but our header includes ## 9. line itself
    # Actually data['sec9_leading'] is everything BEFORE the first ID: in section 9 — which includes the ## 9 header
    out.extend(data['sec9_leading'])
    for s9 in sec9_parsed:
        out.extend(s9['lines'])
        out.append('')
    # Section 10
    out.extend(data['sec10'])

    with open(PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))

    print('Applied updates.')
    print(f'Section 8 entries reorganized across {len(data["sec8"]["subsec_order"])} sub-sections.')
    moves_applied = []
    for eid, target in SUBSECTION_MOVES.items():
        if eid in all_entries_by_id:
            orig = all_entries_by_id[eid]['subsec']
            moves_applied.append(f'  {eid}: {orig} -> {target}')
    print(f'Moves applied: {len(moves_applied)}')
    for m in moves_applied:
        print(m)

if __name__ == '__main__':
    apply()
