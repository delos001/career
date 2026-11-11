#!/usr/bin/env python3
"""
requirement_kinds.py - the requirements file (jd_needs.md): its layout, the
kinds it uses, and the rows later skills read

jd_needs.md is the one home of a job's requirements. role-classify writes it in
two steps:

  1. Extraction: the critical-requirements-extractor's rows are written under
     '## Requirements', each with its text, Type and Source.
  2. Ranking: jd-needs-ranker labels every row with a kind from
     rules/jd-requirement-kinds.md (Function, Means, Setting, ...) and groups
     the rows into ranked needs. The file is rewritten as the job, one heading
     per need with its rows under it, then the Qualifications and Not ranked
     rows. A row the ranker placed nowhere stays under '## Requirements', where
     role_classify_qc.py C6 reports it, so no requirement is lost on rewrite.

Rows on the Not ranked list (boilerplate, role shape, administrative detail)
have done their job by the end of role-classify; retrieval and gap analysis
must never score or evaluate them. requirements_table() is the one reader
those skills use, so every reader filters the same way and sees the same
'| # | Text | Type | Source |' table.

The kinds and where each one lands are derived from the rules file at run time,
not held here: a kind is a '### N. <name>' heading under '## Kinds', and its
section text says where it goes ('Not ranked list', 'Qualifications group',
otherwise a need).

jd_needs.md layout (written by render_needs, read by read_needs):

    # JD needs: <Company> | <Role>

    ## The job

    - Delivers or owns: ...
    - Leads, does, or both: ...

    ## Needs

    ### N-01: <label>

    - Basis: stated | derived
    - Signals: role-statement, repetition N, space
    - Quote: <JD section> "<verbatim JD passage>"

    - **2.** <requirement text, as extracted>
      - Kind: <kind, or kinds joined by + with each part's JD words>
      - Type: must-have | preferred | duty-derived | contextual
      - Source: <JD section> "<verbatim JD passage>"

    ## Qualifications

    - **10.** ...

    ## Not ranked

    - **25.** ...

Before ranking the file holds only the H1 and '## Requirements', and rows
carry no Kind line.

Author  : Jason Delosh
Created : 2026-11-10
Project : career
Usage   : imported (no command line)
Depends : pyyaml (via _config)
"""

import os
import re
import sys

import _util


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Where a row lands, by kind. A row with several kinds lands at the first of
# these its kinds reach: any need kind puts it in a need, else any
# qualification kind in Qualifications, else Not ranked.
NEED, QUALIFICATIONS, NOT_RANKED = 'need', 'qualifications', 'not ranked'

# The needs file's section headings for the two non-need places.
SECTION_FOR = {QUALIFICATIONS: 'Qualifications', NOT_RANKED: 'Not ranked'}

# The section holding extracted rows not yet placed by the ranker.
UNPLACED = 'Requirements'

# The only Type values the gap-analysis coverage table counts.
ALLOWED_TYPES = {'must-have', 'preferred', 'duty-derived', 'contextual'}

TABLE_HEADER = '| # | Text | Type | Source |\n|---|------|------|--------|'

_KIND_HEADING_RE = re.compile(r'^### \d+\.\s+(.+?)\s*$')
_NEED_HEADING_RE = re.compile(r'^### (N-\d+):\s*(.*?)\s*$')
_ROW_RE = re.compile(r'^- \*\*(\d+)\.\*\*\s*(.*?)\s*$')
_ROW_FIELD_RE = re.compile(r'^\s+- (Kind|Type|Source):\s*(.*?)\s*$')
_FIELD_RE = re.compile(r'^- (Basis|Signals|Quote|Delivers or owns|Leads, does, or both):\s*(.*?)\s*$')


# ---------------------------------------------------------------------------
# Kinds from the rules file
# ---------------------------------------------------------------------------

def load_kinds(repo_root, cfg):
    """Return {kind name: NEED | QUALIFICATIONS | NOT_RANKED} from the rules file."""
    path = os.path.join(repo_root, cfg['paths']['rules'],
                        cfg['filenames']['requirement_kinds_file'])
    kinds, current, body, in_kinds = {}, None, [], False

    def flush():
        if current:
            text = ' '.join(body)
            if 'Not ranked list' in text:
                kinds[current] = NOT_RANKED
            elif 'Qualifications group' in text:
                kinds[current] = QUALIFICATIONS
            else:
                kinds[current] = NEED

    for line in _util.read(path).split('\n'):
        if line.startswith('## '):
            flush()
            current, body = None, []
            in_kinds = line.strip() == '## Kinds'
            continue
        if not in_kinds:
            continue
        m = _KIND_HEADING_RE.match(line)
        if m:
            flush()
            current, body = m.group(1), []
        elif current:
            body.append(line)
    flush()
    if not kinds:
        raise ValueError(f'{path} defines no kinds under "## Kinds"')
    return kinds


def parse_kind_cell(cell):
    """Return the kind names in a Kind value, dropping each part's (JD words)."""
    names = []
    for part in cell.split(' + '):
        name = re.sub(r'\s*\(.*\)\s*$', '', part).strip()
        if name:
            names.append(name)
    return names


def placement(names, kinds):
    """Return where a row with these kind names lands (see the constants)."""
    places = {kinds.get(n) for n in names}
    if NEED in places:
        return NEED
    if QUALIFICATIONS in places:
        return QUALIFICATIONS
    return NOT_RANKED


# ---------------------------------------------------------------------------
# The extractor's table
# The critical-requirements-extractor returns '| # | Text | Type | Source |'.
# Its Type cell is held to ALLOWED_TYPES here, before anything is written.
# ---------------------------------------------------------------------------

def _row(num, text, type_, source, kind=None):
    return {'num': num, 'text': text, 'kind': kind, 'type': type_, 'source': source}


def normalize_type(value):
    """Return (allowed Type, recovered?) for a Type cell, or (None, False).

    The extractor is an LLM and drifts from the vocabulary two ways. A category
    label bolted onto one valid token ('education (must-have)') is recoverable:
    the token is kept. A cell with no token, or two, is not: severity cannot be
    inferred without guessing, so the caller fails loudly.
    """
    if value in ALLOWED_TYPES:
        return value, False
    # None of the four is a substring of another, so a substring scan is a
    # whole-token test.
    present = [t for t in sorted(ALLOWED_TYPES) if t in value.lower()]
    return (present[0], True) if len(present) == 1 else (None, False)


def parse_extractor_table(block):
    """Return [row dict] from the extractor's output, Types normalized.

    Raises on an unrecoverable Type cell, listing every offender at once; warns
    on stderr for each recovered one.
    """
    rows, offenders, recovered = [], [], []
    for line in block.split('\n'):
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue
        cells = [c.strip() for c in stripped.strip('|').split('|')]
        if len(cells) < 4 or not cells[0].isdigit():
            continue
        # Source is the last cell; a pipe inside a quote would add cells, so
        # everything after Type is joined back into it.
        num, text, raw_type, source = int(cells[0]), cells[1], cells[2], ' | '.join(cells[3:])
        type_, was_recovered = normalize_type(raw_type)
        if type_ is None:
            offenders.append(f'row {num}: "{raw_type}"')
        elif was_recovered:
            recovered.append(f'row {num}: "{raw_type}" -> "{type_}"')
        rows.append(_row(num, text, type_ or raw_type, source))
    if offenders:
        raise ValueError(f"requirement Type has values outside {', '.join(sorted(ALLOWED_TYPES))} "
                         f"({'; '.join(offenders)}); rerun the extractor")
    if recovered:
        print(f"WARNING: Type reduced to its allowed value ({'; '.join(recovered)})", file=sys.stderr)
    return rows


# ---------------------------------------------------------------------------
# jd_needs.md: path, render, read
# ---------------------------------------------------------------------------

def needs_path(app_folder, cfg):
    return os.path.join(app_folder, cfg['filenames']['jd_needs_file'])


def _row_lines(row):
    lines = [f"- **{row['num']}.** {row['text']}"]
    if row.get('kind'):
        lines.append(f"  - Kind: {row['kind']}")
    lines += [f"  - Type: {row['type']}", f"  - Source: {row['source']}"]
    return lines


def render_requirements(title, rows):
    """Return jd_needs.md text holding the extracted rows only (before ranking)."""
    out = [f'# JD needs: {title}', '', f'## {UNPLACED}', '']
    out += [line for row in rows for line in _row_lines(row)] or ['None.']
    return '\n'.join(out) + '\n'


def render_needs(title, job_lines, needs, qualifications, not_ranked, unplaced=()):
    """Return the ranked jd_needs.md text.

    needs: [{'id', 'label', 'basis', 'signals', 'quote', 'rows': [row dict]}];
    qualifications, not_ranked, unplaced: [row dict]. Unplaced rows (the ranker
    named them nowhere) keep a '## Requirements' section so QC can name them.
    """
    out = [f'# JD needs: {title}', '', '## The job', '']
    out += job_lines
    out += ['', '## Needs', '']
    for need in needs:
        out += [f"### {need['id']}: {need['label']}", '',
                f"- Basis: {need['basis']}",
                f"- Signals: {need['signals']}",
                f"- Quote: {need['quote']}", '']
        for row in need['rows']:
            out += _row_lines(row)
        out.append('')
    sections = [('Qualifications', qualifications), ('Not ranked', not_ranked)]
    if unplaced:
        sections.append((UNPLACED, unplaced))
    for heading, rows in sections:
        out += [f'## {heading}', '']
        out += [line for row in rows for line in _row_lines(row)] or ['None.']
        out.append('')
    return '\n'.join(out)


def read_needs(text):
    """Parse jd_needs.md into {'title', 'job': {field: value}, 'needs': [...],
    'Qualifications': [...], 'Not ranked': [...], 'Requirements': [...],
    'sections': [...]}. Need dicts carry id, label, Basis, Signals, Quote, rows;
    rows are row dicts (num, text, kind, type, source; a missing field is None).
    Unknown lines are ignored; the QC script reports what is missing."""
    out = {'title': '', 'job': {}, 'needs': [], 'Qualifications': [], 'Not ranked': [],
           UNPLACED: [], 'sections': []}
    m = re.match(r'# JD needs:\s*(.*)', text)
    if m:
        out['title'] = m.group(1).strip()
    section, rows = None, None
    for line in text.split('\n'):
        if line.startswith('## '):
            section = line[3:].strip()
            out['sections'].append(section)
            rows = out.get(section) if section in ('Qualifications', 'Not ranked', UNPLACED) else None
            continue
        m = _NEED_HEADING_RE.match(line)
        if m and section == 'Needs':
            need = {'id': m.group(1), 'label': m.group(2), 'rows': []}
            out['needs'].append(need)
            rows = need['rows']
            continue
        m = _ROW_RE.match(line)
        if m and rows is not None:
            rows.append(_row(int(m.group(1)), m.group(2), None, None))
            continue
        m = _ROW_FIELD_RE.match(line)
        if m and rows:
            rows[-1][m.group(1).lower()] = m.group(2)
            continue
        m = _FIELD_RE.match(line)
        if m:
            if section == 'The job':
                out['job'][m.group(1)] = m.group(2)
            elif section == 'Needs' and out['needs']:
                out['needs'][-1][m.group(1)] = m.group(2)
    return out


def all_rows(parsed):
    """Return every row in a parsed needs file, in file order."""
    return ([row for need in parsed['needs'] for row in need['rows']]
            + parsed['Qualifications'] + parsed['Not ranked'] + parsed[UNPLACED])


# ---------------------------------------------------------------------------
# The reader retrieval and gap analysis use
# ---------------------------------------------------------------------------

def ranked_rows(app_folder, cfg):
    """Return the rows later skills read: every row except Not ranked, by number.

    Raises when the application has no jd_needs.md or it holds no rows, so a
    skill run before role-classify halts instead of working from nothing.
    """
    path = needs_path(app_folder, cfg)
    if not os.path.isfile(path):
        raise FileNotFoundError(f'{path} not found; run /role-classify first')
    parsed = read_needs(_util.read(path))
    skip = {row['num'] for row in parsed['Not ranked']}
    rows = sorted((r for r in all_rows(parsed) if r['num'] not in skip), key=lambda r: r['num'])
    if not rows:
        raise ValueError(f'{path} holds no requirements; run /role-classify first')
    return rows


def requirements_table(app_folder, cfg):
    """Return the '| # | Text | Type | Source |' table of ranked_rows().

    What retrieval scores and gap analysis evaluates.
    """
    lines = [f"| {r['num']} | {r['text']} | {r['type']} | {r['source']} |"
             for r in ranked_rows(app_folder, cfg)]
    return TABLE_HEADER + '\n' + '\n'.join(lines)
