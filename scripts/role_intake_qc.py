#!/usr/bin/env python3
"""
role_intake_qc.py - deterministic QC for the role-intake skill's artifacts

Owns the mechanical checks that the qc-role-intake judgment subagent must
not re-run: section and field presence, pending-marker detection, date
form, URL presence in Sources, cross-file field equality, and requirement
quotes. The judgment agent keeps what a script cannot verify (whether
claims trace to sources).

The sections role-classify fills (Axis Classification, Axis Gaps, and the
Role Level and Industry metadata; its ranked needs go to jd_needs.md) are pending when role-intake
hands off, so these checks skip them; scripts/role_classify_qc.py checks
them. The checks that moved there were I4, I5, I6, I8 and I3's axis half.
role_classify_qc.py imports this file's parsing helpers.

Checks:
  I1  Research file completeness: H1 + APP-NNN + Research completed lines;
      Company / Role / Industry sections each carrying non-empty Summary,
      Key facts, and Sources (with at least one URL); Critical Requirements
      with at least one row. No pending markers outside role-classify's
      sections.
  I2  Session log completeness: every Metadata field line present, the
      required ones non-empty, dates well-formed. No pending markers outside
      role-classify's sections.
  I3  Cross-file consistency: company, role, and APP-NNN match between the
      two files.
  I7  Each requirement row's Source carries one verbatim quote found in jd.md,
      and its Text keeps every modifier (config requirement_qualifiers) in the
      JD clause holding that quote. A year count (config requirement_year_count)
      must survive on at least one row quoting that clause.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT
line. Exit 0 when all pass, 1 otherwise.

Author  : Jason Delosh
Created : 2026-07-14
Project : career
Usage   : python scripts/role_intake_qc.py check --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Constants: artifact structure
# ---------------------------------------------------------------------------

# Research file: the three research blocks, each with these H3 subsections.
RESEARCH_BLOCKS = ['Company', 'Role', 'Industry']
BLOCK_SUBSECTIONS = ['Summary', 'Key facts', 'Sources']

# Session log Metadata: fields that must be present AND non-empty. Comms
# file/source must be present but may be blank (no comms ingested). Role Level
# and Industry must be present but are filled later, by role-classify.
METADATA_REQUIRED = ['APP-NNN', 'Company', 'Role',
                     'Session Start Date', 'Research Completed Date',
                     'JD file', 'JD source']
METADATA_OPTIONAL = ['Comms file', 'Comms source', 'Role Level', 'Industry']

# Metadata date fields that must be YYYY-MM-DD.
DATE_FIELDS = ['Session Start Date', 'Research Completed Date']

# What role-classify fills after role-intake hands off: whole sections, and
# metadata lines. Their pending markers are not role-intake's to clear.
CLASSIFY_SECTIONS = ['Axis Classification', 'Axis Gaps']
_CLASSIFY_META_RE = re.compile(r'(?m)^- (?:Role Level|Industry):.*$')

# Pending markers and unfilled template tokens.
_PENDING_RE = re.compile(r'_\(pending\)_|\{\{[a-z_]+\}\}')

# Regex: a URL, for the Sources subsection check.
_URL_RE = re.compile(r'https?://\S+')

# Regex: a double-quoted span in a requirement's Source cell (straight or curly).
_QUOTE_RE = re.compile(r'["“]([^"“”]+)["”]')

# Regex: where a JD clause ends (see _clause_holding).
_CLAUSE_END_RE = re.compile(r'[.;!?]\s')


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _section_body(text, heading, depth=2):
    """Return the body of a `## `/`### ` section, or None if absent."""
    marker = '#' * depth + ' ' + heading
    lines = text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if line.strip() == marker:
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        m = re.match(r'^(#+)\s', lines[j])
        if m and len(m.group(1)) <= depth:
            end = j
            break
    return '\n'.join(lines[start:end]).strip()


def _metadata_fields(log_text):
    """Return {label: value} from the session log's ## Metadata section."""
    body = _section_body(log_text, 'Metadata')
    if body is None:
        return None
    fields = {}
    for line in body.split('\n'):
        m = re.match(r'^- (.+?):\s*(.*)$', line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


def _outside_classify(text):
    """Return text with role-classify's sections and metadata lines removed.

    Used only for the pending-marker scan: those parts are legitimately pending
    when role-intake hands off.
    """
    for heading in CLASSIFY_SECTIONS:
        text = re.sub(rf'(?ms)^## {re.escape(heading)}[ \t]*\n.*?(?=^## |\Z)', '', text)
    return _CLASSIFY_META_RE.sub('', text)


def _h1_company_role(text, prefix):
    """Parse `# <prefix>: <company> | <role>` from a file's H1, or None."""
    m = re.match(rf'^# {re.escape(prefix)}:\s*(.+?)\s*\|\s*(.+?)\s*$', text.split('\n')[0])
    return (m.group(1), m.group(2)) if m else None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_research(research_text, findings):
    """I1: research file structure, block subsections, sources, requirements."""
    problems = []
    if _h1_company_role(research_text, 'Research') is None:
        problems.append('H1 is not `# Research: <company> | <role>`')
    for label in ('APP-NNN', 'Research completed'):
        m = re.search(rf'^\*\*{re.escape(label)}:\*\*\s*(.+)$', research_text, re.MULTILINE)
        if not m or not m.group(1).strip():
            problems.append(f'missing or empty **{label}:** line')
    for block in RESEARCH_BLOCKS:
        body = _section_body(research_text, block)
        if body is None:
            problems.append(f'missing `## {block}` section')
            continue
        for sub in BLOCK_SUBSECTIONS:
            sub_body = _section_body(body, sub, depth=3)
            if not sub_body:
                problems.append(f'`## {block}` missing or empty `### {sub}`')
            elif sub == 'Sources' and not _URL_RE.search(sub_body):
                problems.append(f'`## {block}` Sources carries no URL')
    cr_body = _section_body(research_text, 'Critical Requirements')
    if cr_body is None:
        problems.append('missing `## Critical Requirements` section')
    elif not re.search(r'^\|\s*\d+\s*\|', cr_body, re.MULTILINE) \
            and not re.search(r'^- Text:', cr_body, re.MULTILINE):
        problems.append('`## Critical Requirements` carries no requirement rows')
    if _PENDING_RE.search(_outside_classify(research_text)):
        problems.append('pending markers or unfilled template tokens remain')
    findings.append(('I1', not problems, '; '.join(problems) or 'research file complete'))


def check_session_log(log_text, meta, findings):
    """I2: metadata fields and date form."""
    problems = []
    if meta is None:
        findings.append(('I2', False, 'session log has no ## Metadata section'))
        return
    for field in METADATA_REQUIRED:
        if not meta.get(field):
            problems.append(f'metadata field {field!r} missing or empty')
    for field in METADATA_OPTIONAL:
        if field not in meta:
            problems.append(f'metadata field {field!r} line missing')
    for field in DATE_FIELDS:
        value = meta.get(field, '')
        if value and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            problems.append(f'{field} malformed: {value!r}')
    if _PENDING_RE.search(_outside_classify(log_text)):
        problems.append('pending markers or unfilled template tokens remain')
    findings.append(('I2', not problems, '; '.join(problems) or 'session log complete'))


def check_consistency(research_text, log_text, meta, findings):
    """I3: company/role/APP-NNN equality across files."""
    problems = []
    if meta is None:
        findings.append(('I3', False, 'session log has no ## Metadata section'))
        return
    h1 = _h1_company_role(research_text, 'Research')
    if h1 is None:
        problems.append('research H1 unparseable; company/role comparison skipped')
    else:
        if meta.get('Company', '') != h1[0]:
            problems.append(f"company diverges: session log {meta.get('Company')!r} vs research {h1[0]!r}")
        if meta.get('Role', '') != h1[1]:
            problems.append(f"role diverges: session log {meta.get('Role')!r} vs research {h1[1]!r}")
    m = re.search(r'^\*\*APP-NNN:\*\*\s*(\S+)', research_text, re.MULTILINE)
    if m and meta.get('APP-NNN', '') != m.group(1):
        problems.append(f"APP-NNN diverges: session log {meta.get('APP-NNN')!r} vs research {m.group(1)!r}")
    findings.append(('I3', not problems, '; '.join(problems) or 'cross-file fields consistent'))


def _normalize(text):
    """Lowercase, straighten quotes and dashes, drop bold, collapse whitespace."""
    for fancy, plain in (('’', "'"), ('‘', "'"), ('–', '-'), ('—', '-'), ('*', '')):
        text = text.replace(fancy, plain)
    return re.sub(r'\s+', ' ', text).strip().lower()


def _clause_holding(jd_text, quote):
    """Return the normalized JD clause holding `quote`, or None if not found.

    A clause runs between sentence ends and semicolons within one JD line, so
    in 'Bachelor's degree required; advanced degree preferred.' the 'preferred'
    never binds the Bachelor's row. A quote must sit on one line of the JD.
    """
    target = _normalize(quote)
    for raw_line in jd_text.split('\n'):
        line = _normalize(raw_line)
        pos = line.find(target)
        if pos < 0:
            continue
        start = max((m.end() for m in _CLAUSE_END_RE.finditer(line, 0, pos)), default=0)
        end_match = _CLAUSE_END_RE.search(line, pos + len(target))
        return line[start:end_match.start() + 1] if end_match else line[start:]
    return None


def _requirement_rows(research_text):
    """Return [(row number, Text, Source)] from the Critical Requirements table."""
    rows = []
    for line in (_section_body(research_text, 'Critical Requirements') or '').split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) >= 4 and cells[0].isdigit():
            rows.append((int(cells[0]), cells[1], ' | '.join(cells[3:])))
    return rows


def check_requirement_text(research_text, jd_text, qualifiers, year_count, findings):
    """I7: requirement Text keeps the modifiers that set the JD's bar (GitHub #83).

    The extractor once dropped 'familiarity with' from a must-have, and the
    stricter text reached the gap walk. Modifiers are read from the whole JD
    clause rather than the quote alone: the extractor chooses the quote, so a
    narrow one would otherwise step around the check. A row that keeps every
    modifier but rewords the rest passes; this check guards the bar, not style.

    A year count is held across the rows sharing a clause rather than on each
    row: in '10 years in the industry, with at least 5 years in people management'
    each count belongs to one of two requirements, so it needs only to survive on
    some row from that clause. Wording modifiers stay per row.
    """
    rows = _requirement_rows(research_text)
    if jd_text is None:
        findings.append(('I7', False, 'jd.md not found, so requirement quotes cannot be checked'))
        return
    problems = []
    texts_by_clause = {}
    for num, text, source in rows:
        quotes = _QUOTE_RE.findall(source)
        if len(quotes) != 1:
            problems.append(f'CR-{num:03d}: Source needs one quote, found {len(quotes)}')
            continue
        clause = _clause_holding(jd_text, quotes[0])
        if clause is None:
            problems.append(f'CR-{num:03d}: quote not found in the JD: {quotes[0][:60]}')
            continue
        norm_text = _normalize(text)
        for pattern in qualifiers:
            for match in re.finditer(rf'\b(?:{pattern})\b', clause):
                if not re.search(rf'\b{re.escape(match.group(0))}\b', norm_text):
                    problems.append(f"CR-{num:03d}: Text drops '{match.group(0)}' from the JD clause: {clause[:80]}")
        texts_by_clause.setdefault(clause, []).append((num, norm_text))
    for clause, entries in texts_by_clause.items():
        for match in re.finditer(rf'\b(?:{year_count})\b', clause):
            count = rf'\b{re.escape(match.group(0))}\b'
            if not any(re.search(count, norm_text) for _, norm_text in entries):
                ids = ', '.join(f'CR-{num:03d}' for num, _ in entries)
                problems.append(f"{ids}: no row keeps '{match.group(0)}' from the JD clause: {clause[:80]}")
    findings.append(('I7', not problems, '; '.join(problems) or f'{len(rows)} requirement rows keep their JD modifiers'))


# ---------------------------------------------------------------------------
# Command: check
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Run all checks against one application folder; print report; return exit code."""
    fn = cfg['filenames']
    app_folder = args.folder

    research_text = _read(os.path.join(app_folder, fn['research_file']))
    log_text = _read(os.path.join(app_folder, fn['session_log_file']))
    if research_text is None or log_text is None:
        missing = fn['research_file'] if research_text is None else fn['session_log_file']
        print(f'FATAL  {missing} not found in {app_folder}')
        return 1

    meta = _metadata_fields(log_text)

    findings = []
    check_research(research_text, findings)
    check_session_log(log_text, meta, findings)
    check_consistency(research_text, log_text, meta, findings)
    jd_text = _read(os.path.join(app_folder, fn['jd_file']))
    check_requirement_text(research_text, jd_text,
                           cfg['requirement_qualifiers'], cfg['requirement_year_count'], findings)

    failed = [f for f in findings if not f[1]]
    for check, ok, detail in findings:
        print(f"{check}  {'PASS' if ok else 'FAIL'}  {detail}")
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  "
          f"{len(findings) - len(failed)}/{len(findings)} checks passed")
    return 0 if not failed else 1


def _read(path):
    """Read a file, or return None if it does not exist."""
    if not os.path.isfile(path):
        return None
    return _util.read(path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Deterministic QC for role-intake artifacts.')
    sub = parser.add_subparsers(dest='command', required=True)
    p_check = sub.add_parser('check', help='validate one application folder')
    p_check.add_argument('--folder', required=True,
                         help='absolute path to the application folder')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    if args.command == 'check':
        sys.exit(cmd_check(args, repo_root, cfg))


if __name__ == '__main__':
    main()
