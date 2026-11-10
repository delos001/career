#!/usr/bin/env python3
"""
requirement_kinds.py - the role-classify needs file (jd_needs.md): its layout,
the kinds it uses, and the rows later skills must not read

role-classify labels every row of research.md's Critical Requirements table
with a kind from rules/jd-requirement-kinds.md (Function, Means, Setting, ...),
groups the rows into ranked needs, and writes the result to jd_needs.md in the
application folder, laid out for reading: one heading per need with each
requirement's exact text and kind under it, then the Qualifications and Not
ranked rows. research.md stays role-intake's file.

Rows on the Not ranked list (boilerplate, role shape, administrative detail)
have done their job by the end of role-classify; retrieval and gap analysis
must never score or evaluate them. This module is the one place that reads
that list, so every reader filters the same way. A needs file whose rows no
longer match research.md (the requirements were re-extracted) is refused,
because its row numbers may now point at different requirements.

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

    - **2.** <requirement text, exactly as in research.md>
      - Kind: <kind, or kinds joined by + with each part's JD words>

    ## Qualifications

    - **10.** ...
      - Kind: Qualification

    ## Not ranked

    - **25.** ...
      - Kind: Administrative detail

Author  : Jason Delosh
Created : 2026-11-10
Project : career
Usage   : imported (no command line)
Depends : pyyaml (via _config)
"""

import os
import re

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

_KIND_HEADING_RE = re.compile(r'^### \d+\.\s+(.+?)\s*$')
_NEED_HEADING_RE = re.compile(r'^### (N-\d+):\s*(.*?)\s*$')
_ROW_RE = re.compile(r'^- \*\*(\d+)\.\*\*\s*(.*?)\s*$')
_KIND_LINE_RE = re.compile(r'^\s+- Kind:\s*(.*?)\s*$')
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
# research.md's Critical Requirements table
# ---------------------------------------------------------------------------

def requirement_texts(section):
    """Return {row number: Text} from a Critical Requirements body (table form)."""
    texts = {}
    for line in (section or '').split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if line.strip().startswith('|') and len(cells) >= 4 and cells[0].isdigit():
            texts[int(cells[0])] = cells[1]
    return texts


def without_rows(section, nums):
    """Return a Critical Requirements body with the given rows removed."""
    if not nums:
        return section
    out = []
    for line in section.split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if line.strip().startswith('|') and cells[0].isdigit() and int(cells[0]) in nums:
            continue
        out.append(line)
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# jd_needs.md: path, render, read
# ---------------------------------------------------------------------------

def needs_path(app_folder, cfg):
    return os.path.join(app_folder, cfg['filenames']['jd_needs_file'])


def _row_lines(num, text, kind):
    return [f'- **{num}.** {text}', f'  - Kind: {kind}']


def render_needs(title, job_lines, needs, qualifications, not_ranked):
    """Return jd_needs.md text.

    needs: [{'id', 'label', 'basis', 'signals', 'quote', 'rows': [(num, text, kind)]}];
    qualifications, not_ranked: [(num, text, kind)].
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
            out += _row_lines(*row)
        out.append('')
    for heading, rows in (('Qualifications', qualifications), ('Not ranked', not_ranked)):
        out += [f'## {heading}', '']
        out += [line for row in rows for line in _row_lines(*row)] or ['None.']
        out.append('')
    return '\n'.join(out)


def read_needs(text):
    """Parse jd_needs.md into {'job': {field: value}, 'needs': [...], 'Qualifications': [...],
    'Not ranked': [...]}. Need dicts carry id, label, Basis, Signals, Quote, rows;
    rows are [(num, text, kind or None)]. Unknown lines are ignored; the QC
    script reports what is missing."""
    out = {'job': {}, 'needs': [], 'Qualifications': [], 'Not ranked': [], 'sections': []}
    section, rows = None, None
    for line in text.split('\n'):
        if line.startswith('## '):
            section = line[3:].strip()
            out['sections'].append(section)
            rows = out.get(section) if section in ('Qualifications', 'Not ranked') else None
            continue
        m = _NEED_HEADING_RE.match(line)
        if m and section == 'Needs':
            need = {'id': m.group(1), 'label': m.group(2), 'rows': []}
            out['needs'].append(need)
            rows = need['rows']
            continue
        m = _ROW_RE.match(line)
        if m and rows is not None:
            rows.append([int(m.group(1)), m.group(2), None])
            continue
        m = _KIND_LINE_RE.match(line)
        if m and rows:
            rows[-1][2] = m.group(1)
            continue
        m = _FIELD_RE.match(line)
        if m:
            if section == 'The job':
                out['job'][m.group(1)] = m.group(2)
            elif section == 'Needs' and out['needs']:
                out['needs'][-1][m.group(1)] = m.group(2)
    return out


# ---------------------------------------------------------------------------
# The filter retrieval and gap analysis apply
# ---------------------------------------------------------------------------

def not_ranked_rows(app_folder, cfg, section):
    """Return the row numbers on jd_needs.md's Not ranked list.

    Returns the empty set when the application has no jd_needs.md (role-classify
    predates it). Raises when the needs file's rows do not match the
    requirements in research.md, since its row numbers may then name different
    requirements than the ones it was built on.
    """
    path = needs_path(app_folder, cfg)
    if not os.path.isfile(path):
        return set()
    parsed = read_needs(_util.read(path))
    listed = {num: text for rows in ([n['rows'] for n in parsed['needs']]
                                     + [parsed['Qualifications'], parsed['Not ranked']])
              for num, text, _ in rows}
    current = requirement_texts(section)
    if listed != current:
        raise ValueError(f'{path} does not match the requirements in research.md '
                         f'(they were re-extracted); rerun /role-classify')
    return {num for num, _, _ in parsed['Not ranked']}


def ranked_section(section, app_folder, cfg):
    """Return a Critical Requirements body without its Not ranked rows.

    What retrieval scores and gap analysis evaluates.
    """
    return without_rows(section, not_ranked_rows(app_folder, cfg, section))
