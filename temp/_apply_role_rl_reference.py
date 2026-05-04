"""Cluster C migration: replace Title:/Company: on EX entries with Role: RL-NNN reference.
Per inventory-company-field-rl-reference (deferral) and Option B decision (drop Title).
PR entries untouched.

Two phases:
1. Dry run: build (Title, Company) -> RL-NNN mapping; report any EX entry that fails to match.
2. Apply: rewrite EX entry blocks; preserve all other content verbatim.

Run with --apply to write; default is dry-run.
"""
import re
import sys
from pathlib import Path

PATH = Path(r'C:\Users\delos\code\career\personal\knowledge\Experience_Inventory.md')

# Cluster 3 overrides: compound title "Regional/Global Clinical Trial Manager" at Amgen-via-DOCS
# splits between RL-011 (Regional CTM) and RL-013 (Global CTM) per user assignment.
EXPLICIT_OVERRIDES = {
    'EX-056': 'RL-011',
    'EX-057': 'RL-011',
    'EX-081': 'RL-011',
    'EX-088': 'RL-013',
    'EX-089': 'RL-013',
    'EX-090': 'RL-011',
    'EX-091': 'RL-013',
    'EX-092': 'RL-011',
    'EX-093': 'RL-011',
    'EX-094': 'RL-011',
}

def normalize(s: str) -> str:
    """Collapse internal whitespace and strip spaces around slashes for tolerant title comparison."""
    s = ' '.join(s.split())
    s = re.sub(r'\s*/\s*', '/', s)
    return s

def parse_rl_records(text: str) -> dict:
    """Return {(title, company): rl_id} from Section 7."""
    sec7_match = re.search(r'## 7\. Employment & Role History\s*\n(.*?)(?=\n## )', text, re.DOTALL)
    if not sec7_match:
        raise RuntimeError('Section 7 not found')
    sec7 = sec7_match.group(1)
    blocks = re.split(r'\n\s*\n', sec7.strip())
    mapping = {}
    rl_titles_by_company = {}
    for block in blocks:
        rl_id = title = company = None
        for line in block.splitlines():
            if line.startswith('ID: '):
                rl_id = line[4:].strip()
            elif line.startswith('Title: '):
                title = line[7:].strip()
            elif line.startswith('Company: '):
                company = line[9:].strip()
        if rl_id and title and company:
            mapping[(title, company)] = rl_id
            rl_titles_by_company.setdefault(company, []).append((title, rl_id))
    return mapping, rl_titles_by_company

def find_rl(ex_id: str, ex_title: str, ex_company: str, exact_map: dict, by_company: dict) -> str | None:
    """Match EX (title, company) to RL ID. Override map first, then exact, then whitespace-normalized, then substring."""
    if ex_id in EXPLICIT_OVERRIDES:
        return EXPLICIT_OVERRIDES[ex_id]
    if (ex_title, ex_company) in exact_map:
        return exact_map[(ex_title, ex_company)]
    norm_ex_title = normalize(ex_title)
    candidates = by_company.get(ex_company, [])
    norm_hits = [(rl_title, rl_id) for rl_title, rl_id in candidates if normalize(rl_title) == norm_ex_title]
    if len(norm_hits) == 1:
        return norm_hits[0][1]
    if len(norm_hits) > 1:
        return f'AMBIGUOUS:{[h[1] for h in norm_hits]}'
    substring_hits = [(rl_title, rl_id) for rl_title, rl_id in candidates if ex_title in rl_title]
    if len(substring_hits) == 1:
        return substring_hits[0][1]
    if len(substring_hits) > 1:
        return f'AMBIGUOUS:{[h[1] for h in substring_hits]}'
    return None

def parse_ex_entries(text: str):
    """Yield (start_line_idx, end_line_idx_exclusive, ex_id, title, company) for each EX entry.
    End is the line index just past the Company: line — that's all we replace.
    """
    lines = text.splitlines(keepends=True)
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].startswith('ID: EX-'):
            ex_id = lines[i][4:].strip()
            title_idx = i + 1
            company_idx = i + 2
            if title_idx < n and company_idx < n \
                    and lines[title_idx].startswith('Title: ') \
                    and lines[company_idx].startswith('Company: '):
                title = lines[title_idx][7:].strip()
                company = lines[company_idx][9:].strip()
                yield (i, title_idx, company_idx, ex_id, title, company)
                i = company_idx + 1
                continue
        i += 1

def main():
    apply = '--apply' in sys.argv
    text = PATH.read_text(encoding='utf-8')
    exact_map, by_company = parse_rl_records(text)
    print(f'Section 7: parsed {len(exact_map)} RL records across {len(by_company)} companies')

    lines = text.splitlines(keepends=True)
    entries = list(parse_ex_entries(text))
    print(f'Section 8: found {len(entries)} EX entries')

    unmatched = []
    ambiguous = []
    matched = []
    for entry in entries:
        i_id, i_title, i_company, ex_id, title, company = entry
        rl_id = find_rl(ex_id, title, company, exact_map, by_company)
        if rl_id is None:
            unmatched.append((ex_id, title, company))
        elif isinstance(rl_id, str) and rl_id.startswith('AMBIGUOUS:'):
            ambiguous.append((ex_id, title, company, rl_id))
        else:
            matched.append((entry, rl_id))

    print(f'\nMatched: {len(matched)}')
    print(f'Unmatched: {len(unmatched)}')
    print(f'Ambiguous: {len(ambiguous)}')

    if unmatched:
        print('\n--- UNMATCHED ---')
        for ex_id, title, company in unmatched:
            print(f'  {ex_id}: Title="{title}" Company="{company}"')
    if ambiguous:
        print('\n--- AMBIGUOUS ---')
        for ex_id, title, company, hit in ambiguous:
            print(f'  {ex_id}: Title="{title}" Company="{company}" -> {hit}')

    if not apply:
        print('\n[dry-run] Add --apply to write changes.')
        return 0

    if unmatched or ambiguous:
        print('\nRefusing to apply: unmatched or ambiguous entries present.')
        return 1

    # Apply: replace Title: + Company: lines (two consecutive lines) with one Role: RL-NNN line.
    # Build edits as (line_to_replace_start, line_to_replace_end_exclusive, new_text).
    edits = []
    for entry, rl_id in matched:
        i_id, i_title, i_company, ex_id, title, company = entry
        edits.append((i_title, i_company + 1, f'Role: {rl_id}\n'))

    edits.sort(reverse=True)
    new_lines = list(lines)
    for start, end, new_text in edits:
        new_lines[start:end] = [new_text]

    PATH.write_text(''.join(new_lines), encoding='utf-8')
    before_count = len(lines)
    after_count = len(new_lines)
    print(f'\nApplied. Line count: {before_count} -> {after_count} (delta {after_count - before_count})')
    return 0

if __name__ == '__main__':
    sys.exit(main())
