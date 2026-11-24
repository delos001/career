#!/usr/bin/env python3
"""
jd_extraction_tables.py - role-extract's table files: their layout, the kinds
they use, and the rows later skills read (named requirement_kinds.py until
2026-11-19)

jd_needs.md is the one home of a job's requirements. role-extract writes it in
two steps:

  1. Extraction: the jd-splitter's parts, each with the Part ID it gave, are
     written to scratch/jd_assemble.md under '## Requirements' with their
     unit (from jd_sentences.md), text and JD line. Since 2026-11-23 no
     Demand or Bar is set there; jd_needs.md rows still carry both
     (jd_demand.py, jd_bar.py).
  2. Ranking: every row is labeled with a kind from the KINDS section of
     rules/jd-processing.md (Function, Means, Setting, ...) and jd-needs-ranker groups
     the rows into ranked needs. The file is rewritten as the job, one heading
     per need with its rows under it, then the Qualifications and Not ranked
     rows. A row the ranker placed nowhere stays under '## Requirements', where
     role_extract_qc.py X3 reports it, so no requirement is lost on rewrite.

Rows on the Not ranked list (boilerplate, role shape, administrative detail)
have done their job by the end of role-classify; retrieval and gap analysis
must never score or evaluate them. requirements_table() is the one reader
those skills use, so every reader filters the same way and sees the same
'| # | Text | Demand | Source |' table.

The kinds and where each one lands are derived from the rules file at run time,
not held here: a kind is a '### N. <name>' heading under KINDS_HEADING, and its
section text says where it goes ('Not ranked list', 'Qualifications group',
otherwise a need).

The file ends with a '## Definitions' appendix: what each Kind, Demand and Bar
value means, for a person reviewing the file. Kind definitions are copied from
the rules file (kind_definitions); read_needs ignores the appendix.

jd_needs.md layout (written by render_needs, read by read_needs):

    # JD needs: <Company> | <Role>

    ## The job

    - Role statement:
      - <key item, a few words in the JD's terms> (L<n>)
    - Outcomes:
      - <what one deliverable achieves, in the JD's terms> (L<n>)
    - Leads, does, or both: ...

    ## Needs

    ### N-01: <label>

    - Signals: role-statement, repetition N, space N
    - Quote: L<n> <JD heading> "<verbatim JD passage>"

    | Part ID | Unit ID | Line | Section | Requirement | Demand | Bar | Kind |
    |---|---|---|---|---|---|---|---|
    | 2 | S-014 | L<n> | <JD heading> | <requirement text, as split> | required | preferred | exposure | working | (blank) | <kind, or kinds joined by + with each part's JD words> |

    ## Qualifications

    <same table>

    ## Not ranked

    <same table, or None.>

Part ID is the row's permanent number; later skills cite it as CR-NNN. Unit
ID, Line and Section are the unit the part was split from, its jd.md line and
its heading, taken from jd_sentences.units() by role_extract_assemble.py; the
full sentence is not copied onto the row, since Unit ID and Line find it in
jd.md. A row dict also carries 'source' ('L<n> <Section>'), the one JD
reference later readers use. A need's Quote is found from its quote (jd_ref).
Files written before 2026-11-18 have five columns ('| Req | Requirement |
Kind | Demand | JD line |', no unit); they are still read. Before ranking the
file holds only the H1 and '## Requirements', with the Kind cells empty.

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

# The section holding extracted rows not yet placed by the ranker.
UNPLACED = 'Requirements'

# How strongly the JD demands a row. 'preferred' only when the JD marks it
# optional; a duty the JD lists is required. How much a row matters comes from
# its need's rank, never from this value.
ALLOWED_DEMANDS = {'required', 'preferred'}

TABLE_HEADER = '| # | Text | Demand | Source |\n|---|------|------|--------|'

# The requirement table in jd_needs.md: which row, where it came from, what it
# says, then the judgments on it (Demand and Bar by jd_demand.py and
# jd_bar.py, Kind at ranking; none of them in scratch/jd_assemble.md before
# the kinds step).
# Files written before 2026-11-18 have the five-column ROW_HEADER.
UNIT_ROW_HEADER = ('| Part ID | Unit ID | Line | Section | Requirement | Demand | Bar | Kind |\n'
                   '|---|---|---|---|---|---|---|---|')
# scratch/jd_assemble.md (2026-11-19): the splitter's parts joined to
# scratch/jd_sentences.md, Part ID as the splitter numbered it. Since
# 2026-11-23 it opens with where the part sits in the JD (Line, Section),
# then Unit ID, Part ID and Part, and carries no Demand or Bar. The assemble
# step writes it with no Kind column (ASSEMBLE_ROW_HEADER); the kinds step
# rewrites it in place with a Kind column at the end
# (ASSEMBLE_KIND_ROW_HEADER). Files written before 2026-11-23 open with
# Unit ID and have Demand and Bar after Part; files written before
# 2026-11-20 also have From and Hints after Line.
ASSEMBLE_ROW_HEADER = ('| Line | Section | Unit ID | Part ID | Part |\n'
                       '|---|---|---|---|---|')
ASSEMBLE_KIND_ROW_HEADER = ('| Line | Section | Unit ID | Part ID | Part | Kind |\n'
                            '|---|---|---|---|---|---|')
ROW_HEADER = '| Req | Requirement | Kind | Demand | JD line |\n|---|---|---|---|---|'

# The kinds are the '### N. <name>' headings under this section of
# rules/jd-processing.md (config filenames.jd_rules_file).
KINDS_HEADING = '## KINDS: Kinds of row'
_KIND_HEADING_RE = re.compile(r'^### \d+\.\s+(.+?)\s*$')
_NEED_HEADING_RE = re.compile(r'^### (N-\d+):\s*(.*?)\s*$')
# Regex: a table cell separator (a pipe not escaped as \|).
_CELL_SPLIT_RE = re.compile(r'(?<!\\)\|')
# Regex: a location the extractor or ranker wrote after a JD heading
# ('¶4', '#2', 'line 10', 'lines 10-12'), or a leading 'L<n>' already written.
_LOCATION_RE = re.compile(r'\s*(?:¶\s*\d+|#\s*\d+|\blines?\s+[\d,\s-]+)\s*$', re.I)
_LINE_REF_RE = re.compile(r'^L\d+\s*')
_FIELD_RE = re.compile(r'^- (Signals|Quote|Role statement|Outcomes|Leads, does, or both):\s*(.*?)\s*$')
# Regex: a nested item under a job field (the role statement's key items).
_SUBITEM_RE = re.compile(r'^\s+- (.+?)\s*$')

# Regex: a double-quoted span in a Source cell (straight or curly), with the
# space before it.
_SOURCE_QUOTE_RE = re.compile(r'\s*["“]([^"“”]+)["”]')


# ---------------------------------------------------------------------------
# Kinds from the rules file
# ---------------------------------------------------------------------------

def load_kinds(repo_root, cfg):
    """Return {kind name: NEED | QUALIFICATIONS | NOT_RANKED} from the rules file."""
    path = os.path.join(repo_root, cfg['paths']['rules'], cfg['filenames']['jd_rules_file'])
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
            in_kinds = line.strip() == KINDS_HEADING
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
        raise ValueError(f'{path} defines no kinds under "{KINDS_HEADING}"')
    return kinds


def kind_definitions(repo_root, cfg):
    """Return [(kind name, definition)] from the rules file, in file order.

    A kind's definition is the first paragraph under its '### N. <name>'
    heading in the KINDS_HEADING section, copied as written, so the
    definitions shown in jd_needs.md never drift from the rules.
    """
    path = os.path.join(repo_root, cfg['paths']['rules'], cfg['filenames']['jd_rules_file'])
    out, in_kinds = [], False
    current, para, done = None, [], False

    def flush():
        if current and para:
            out.append((current, ' '.join(para)))

    for line in _util.read(path).split('\n'):
        if line.startswith('## '):
            flush()
            current, para, done = None, [], False
            in_kinds = line.strip() == KINDS_HEADING
            continue
        if not in_kinds:
            continue
        m = _KIND_HEADING_RE.match(line)
        if m:
            flush()
            current, para, done = m.group(1), [], False
            continue
        if current is None or done:
            continue
        text = line.strip()
        # The paragraph ends at the first blank line after it, or the first bullet.
        if text.startswith('- ') or (not text and para):
            done = True
        elif text:
            para.append(text)
    flush()
    return out


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
# Rows and the splitter's table
# The jd-splitter writes '## Parts' with '| Unit ID | Part ID | Part |' rows,
# Part 'whole' when the unit is one part. role_extract_assemble.py turns them
# into rows.
# ---------------------------------------------------------------------------

def _row(num, text, demand, source, kind=None, unit=None, line=None, section=None, bar=None):
    """Return a row dict. With a line, 'source' is built as 'L<n> <Section>'."""
    if line:
        source = f'{line} {section or ""}'.strip()
    return {'num': num, 'unit': unit, 'line': line, 'section': section, 'text': text,
            'kind': kind, 'demand': demand, 'bar': bar, 'source': source}


# Regex: a jd_sentences.md unit id (S-046, S-046a).
UNIT_ID_RE = re.compile(r'^S-\d+[a-z]?$')


def parse_parts_table(block):
    """Return [(unit id, part id, part)] from the jd-splitter's '## Parts' table, in order.

    Raises when the heading or every row is missing, a Unit cell is not a
    unit id, or a Part ID cell is not a whole number, so a malformed file
    stops the write instead of losing parts. Whether the Part IDs run 1..N is
    role_extract_qc.py X1's check, run on the assembled file.
    """
    if not re.search(r'(?m)^## Parts[ \t]*$', block):
        raise ValueError('the splitter output has no "## Parts" heading')
    parts, bad, bad_ids = [], [], []
    for line in block.split('\n'):
        body = line.strip()
        if not body.startswith('|'):
            continue
        cells = [c.strip().replace(r'\|', '|') for c in _CELL_SPLIT_RE.split(body.strip('|'))]
        if len(cells) < 2 or cells[0] in ('Unit ID', '') or set(cells[0]) <= set('-'):
            continue
        if not UNIT_ID_RE.match(cells[0]):
            bad.append(cells[0])
            continue
        if len(cells) < 3 or not cells[1].isdigit():
            bad_ids.append(f'{cells[0]} {cells[1]!r}')
            continue
        # A pipe inside the text would add cells, so the rest is joined back.
        parts.append((cells[0], int(cells[1]), ' | '.join(cells[2:])))
    if bad:
        raise ValueError(f"Unit cells that are not unit ids: {', '.join(bad)}")
    if bad_ids:
        raise ValueError(f"rows with no whole-number Part ID: {', '.join(bad_ids)}; rerun the splitter")
    if not parts:
        raise ValueError('the splitter output holds no rows under "## Parts"')
    return parts


def optional_word(text, patterns):
    """Return the first optional-demand word (config requirement_optional_words)
    in `text`, or None. A row whose own text carries one must be 'preferred'."""
    for pattern in patterns:
        m = re.search(rf'\b(?:{pattern})\b', normalize(text))
        if m:
            return m.group(0)
    return None


def normalize(text):
    """Lowercase, straighten quotes and dashes, drop bold, collapse whitespace."""
    for fancy, plain in (('’', "'"), ('‘', "'"), ('–', '-'), ('—', '-'), ('*', '')):
        text = text.replace(fancy, plain)
    return re.sub(r'\s+', ' ', text).strip().lower()


def quote_line(jd_text, quote):
    """Return the 1-based jd.md line holding `quote`, or None."""
    target = normalize(quote)
    if not target:
        return None
    for n, line in enumerate(jd_text.split('\n'), start=1):
        if target in normalize(line):
            return n
    return None


def jd_ref(jd_text, text, source):
    """Return a JD reference cell as 'L<n> <JD heading>', plus the quote when it
    differs from `text`.

    `source` is '<JD heading> "<quote>"' as the extractor or ranker wrote it;
    with no quote, `text` is the quote. Any other location the agent wrote
    ('¶4', '#2', 'line 10', '; also ...' pointers) is dropped: one scheme, the
    jd.md line, found from the quote. A requirement row passes its text, so a
    quote equal to it is dropped and the text is not stored twice; a need's
    Quote passes '' and keeps its quote. When the quote is not in the JD the
    cell is returned unchanged, and role_extract_qc.py reports it.
    """
    quotes = list(_SOURCE_QUOTE_RE.finditer(source))
    if len(quotes) > 1:
        return source
    quote = quotes[0].group(1).strip() if quotes else text.strip()
    line = quote_line(jd_text, quote)
    if line is None:
        return source
    heading = (source[:quotes[0].start()] if quotes else source).split(';')[0].strip()
    heading = _LOCATION_RE.sub('', _LINE_REF_RE.sub('', heading)).strip()
    ref = f'L{line} {heading}'.strip()
    return ref if quote == text.strip() else f'{ref} "{quote}"'


def row_quote(row):
    """Return the JD words a row rests on: its Source quote, or its text when
    the writer dropped a quote equal to it (see jd_ref)."""
    quote = _SOURCE_QUOTE_RE.search(row.get('source') or '')
    return quote.group(1).strip() if quote else (row.get('text') or '').strip()


def jd_heading(source):
    """Return the JD section heading of a JD reference cell ('L<n> <heading>',
    optionally followed by a quote), or '' when the cell names none."""
    quote = _SOURCE_QUOTE_RE.search(source or '')
    head = (source or '')[:quote.start()] if quote else (source or '')
    return normalize(_LINE_REF_RE.sub('', head.split(';')[0].strip()))


# ---------------------------------------------------------------------------
# jd_needs.md: path, render, read
# ---------------------------------------------------------------------------

def needs_path(app_folder, cfg):
    return os.path.join(app_folder, cfg['filenames']['jd_needs_file'])


def _cell(value):
    """Return a table cell value with any pipe escaped."""
    return (value or '').replace('|', r'\|')


def _row_table(rows, with_kind=True, assembled=False):
    """Return the requirement table lines for rows, or ['None.'].

    assembled=True writes scratch/jd_assemble.md's layout: ASSEMBLE_ROW_HEADER,
    or ASSEMBLE_KIND_ROW_HEADER when with_kind is True. Otherwise rows from the
    jd-splitter carry their unit, so the table gets the eight-column layout
    (jd_needs.md); a file written before 2026-11-18 has no unit and keeps its
    five columns when it is rewritten.
    """
    if not rows:
        return ['None.']
    if assembled:
        header = ASSEMBLE_KIND_ROW_HEADER if with_kind else ASSEMBLE_ROW_HEADER
        return [header] + [
            f"| {_cell(row.get('line'))} | {_cell(row.get('section'))} | "
            f"{_cell(row.get('unit'))} | {row['num']} | {_cell(row['text'])} |"
            + (f" {_cell(row.get('kind'))} |" if with_kind else '') for row in rows]
    if any(row.get('unit') for row in rows):
        return [UNIT_ROW_HEADER] + [
            f"| {row['num']} | {_cell(row.get('unit'))} | {_cell(row.get('line'))} | "
            f"{_cell(row.get('section'))} | {_cell(row['text'])} | {_cell(row['demand'])} | "
            f"{_cell(row.get('bar'))} | {_cell(row.get('kind'))} |" for row in rows]
    return [ROW_HEADER] + [
        f"| {row['num']} | {_cell(row['text'])} | {_cell(row.get('kind'))} | "
        f"{_cell(row['demand'])} | {_cell(row['source'])} |" for row in rows]


def _table_row(line):
    """Return a row dict from a requirement table line, or None for any other line.

    Five or six cells opening with a JD line (L<n>) is scratch/jd_assemble.md,
    before and after the kinds step adds the Kind (ASSEMBLE_ROW_HEADER,
    ASSEMBLE_KIND_ROW_HEADER). Seven or eight cells opening with a Unit ID is
    that file written before 2026-11-23, with Demand and Bar after Part; nine
    or ten is that file written before 2026-11-20, with From and Hints after
    Line, which are skipped.
    Eight cells is the ranked layout (Part ID, Unit ID, Line, Section,
    Requirement, Demand, Bar, Kind); five is a file written before 2026-11-18,
    read so later skills keep working on older applications.
    """
    body = line.strip()
    if not (body.startswith('|') and body.endswith('|')):
        return None
    cells = [c.strip().replace(r'\|', '|') for c in _CELL_SPLIT_RE.split(body[1:-1])]
    if len(cells) in (5, 6) and re.fullmatch(r'L\d+', cells[0]) and UNIT_ID_RE.match(cells[2]) \
            and cells[3].isdigit():
        jd_line, section, unit, num, text = cells[:5]
        kind = cells[5] if len(cells) == 6 else None
        return _row(int(num), text, None, None, kind or None, unit, jd_line or None, section or None)
    if len(cells) in (7, 8, 9, 10) and UNIT_ID_RE.match(cells[0]) and cells[1].isdigit():
        if len(cells) >= 9:
            cells = cells[:4] + cells[6:]
        unit, num, section, jd_line, text, demand, bar = cells[:7]
        kind = cells[7] if len(cells) == 8 else None
        return _row(int(num), text, demand or None, None, kind or None, unit, jd_line or None,
                    section or None, bar)
    if not cells[0].isdigit():
        return None
    if len(cells) == 8:
        num, unit, jd_line, section, text, demand, bar, kind = cells
        return _row(int(num), text, demand or None, None, kind or None, unit or None,
                    jd_line or None, section or None, bar)
    if len(cells) == 5:
        num, text, kind, demand, source = cells
        return _row(int(num), text, demand or None, source or None, kind or None)
    return None


def render_requirements(title, rows, definitions=(), with_kind=True, assembled=False):
    """Return the text of a file holding the extracted rows only (before ranking).

    definitions: the lines of the '## Definitions' appendix (built by
    role_extract_assemble.py), placed last so readers can stop before it.
    assembled=True writes scratch/jd_assemble.md's layout; with_kind=False
    leaves out the Kind column, which the kinds step adds.
    """
    out = [f'# {title}', '', f'## {UNPLACED}', '']
    out += _row_table(rows, with_kind, assembled)
    if definitions:
        out += [''] + list(definitions)
    return '\n'.join(out) + '\n'


def render_needs(title, job_lines, needs, qualifications, not_ranked, unplaced=(), definitions=()):
    """Return the ranked jd_needs.md text.

    needs: [{'id', 'label', 'signals', 'quote', 'rows': [row dict]}];
    qualifications, not_ranked, unplaced: [row dict]. Unplaced rows (the ranker
    named them nowhere) keep a '## Requirements' section so QC can name them.
    """
    out = [f'# JD needs: {title}', '', '## The job', '']
    out += job_lines
    out += ['', '## Needs', '']
    for need in needs:
        out += [f"### {need['id']}: {need['label']}", '',
                f"- Signals: {need['signals']}",
                f"- Quote: {need['quote']}", '']
        out += _row_table(need['rows'])
        out.append('')
    sections = [('Qualifications', qualifications), ('Not ranked', not_ranked)]
    if unplaced:
        sections.append((UNPLACED, unplaced))
    for heading, rows in sections:
        out += [f'## {heading}', '']
        out += _row_table(rows)
        out.append('')
    out += list(definitions)
    return '\n'.join(out)


def read_needs(text):
    """Parse jd_needs.md into {'title', 'job': {field: value}, 'job_items':
    {field: [nested items]}, 'needs': [...],
    'Qualifications': [...], 'Not ranked': [...], 'Requirements': [...],
    'sections': [...]}. Need dicts carry id, label, Signals, Quote, rows;
    rows are row dicts (num, text, kind, demand, source; a missing field is None).
    Unknown lines are ignored; the QC script reports what is missing."""
    out = {'title': '', 'job': {}, 'job_items': {}, 'needs': [], 'Qualifications': [], 'Not ranked': [],
           UNPLACED: [], 'sections': []}
    # The title is '# <Company> | <Role>'; files written before 2026-11-19 open '# JD needs: '.
    m = re.match(r'# (?:JD needs:\s*)?(.*)', text)
    if m:
        out['title'] = m.group(1).strip()
    section, rows, job_field = None, None, None
    for line in text.split('\n'):
        # A nested item under a job field joins that field's value, '; '-separated,
        # and is also kept whole in job_items, since an item may hold its own ';'.
        sub = _SUBITEM_RE.match(line)
        if sub and section == 'The job' and job_field:
            prior = out['job'].get(job_field, '')
            out['job'][job_field] = f'{prior}; {sub.group(1)}' if prior else sub.group(1)
            out['job_items'].setdefault(job_field, []).append(sub.group(1))
            continue
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
        row = _table_row(line)
        if row and rows is not None:
            rows.append(row)
            continue
        m = _FIELD_RE.match(line)
        if m:
            if section == 'The job':
                out['job'][m.group(1)] = m.group(2)
                job_field = m.group(1)
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
    skill run before role-extract halts instead of working from nothing.
    """
    path = needs_path(app_folder, cfg)
    if not os.path.isfile(path):
        raise FileNotFoundError(f'{path} not found; run /role-extract first')
    parsed = read_needs(_util.read(path))
    skip = {row['num'] for row in parsed['Not ranked']}
    rows = sorted((r for r in all_rows(parsed) if r['num'] not in skip), key=lambda r: r['num'])
    if not rows:
        raise ValueError(f'{path} holds no requirements; run /role-extract first')
    return rows


def row_places(app_folder, cfg):
    """Return {row number: need id, or 'Qual'} for the rows later skills read.

    Retrieval uses it to show which needs each scored entry serves, so priority
    is applied from the ranking by script, never re-judged by the scorer.
    """
    parsed = read_needs(_util.read(needs_path(app_folder, cfg)))
    places = {row['num']: need['id'] for need in parsed['needs'] for row in need['rows']}
    places.update({row['num']: 'Qual' for row in parsed['Qualifications']})
    return places


def requirement_info(app_folder, cfg):
    """Return {CR-NNN: info} for the rows gap analysis judges, in need rank order.

    info: text, demand, place (need id, 'Qual', or '' for a row the ranker has
    not placed), label (need label, or 'Qualifications'), core. A row is core
    when it sits in a need carrying the role-statement signal, or in
    Qualifications: the hard thresholds and the job's central work. Only an
    unmet required core row moves the gap-analysis label.
    """
    parsed = read_needs(_util.read(needs_path(app_folder, cfg)))

    def info(row, place, label, core):
        return f"CR-{row['num']:03d}", {'text': row['text'], 'demand': row['demand'],
                                         'place': place, 'label': label, 'core': core}

    out = dict(info(row, need['id'], need['label'], 'role-statement' in need.get('Signals', ''))
               for need in parsed['needs'] for row in need['rows'])
    out.update(info(row, 'Qual', 'Qualifications', True) for row in parsed['Qualifications'])
    out.update(info(row, '', 'Not yet ranked', False)
               for row in sorted(parsed[UNPLACED], key=lambda r: r['num']))
    return out


def requirements_table(app_folder, cfg, demand=True, by_need=False):
    """Return the '| # | Text | Demand | Source |' table of ranked_rows().

    What retrieval scores and gap analysis evaluates. With demand=False the
    Demand column is left out: the retrieval scorer judges evidence strength
    only, so it never sees how strongly the JD demands a row. With by_need=True
    the rows come in need rank order with a Need column, which is how gap
    analysis judges and reports them.
    """
    rows = ranked_rows(app_folder, cfg)
    if by_need:
        info = requirement_info(app_folder, cfg)
        order = {cr: i for i, cr in enumerate(info)}
        lines = []
        for r in sorted(rows, key=lambda r: order[f"CR-{r['num']:03d}"]):
            need = info[f"CR-{r['num']:03d}"]
            name = ' '.join(v for v in (need['place'] if need['place'] != 'Qual' else '', need['label']) if v)
            lines.append(f"| {r['num']} | {_cell(name)} | {r['text']} | {r['demand']} | {r['source']} |")
        return ('| # | Need | Text | Demand | Source |\n|---|------|------|------|--------|\n'
                + '\n'.join(lines))
    if not demand:
        return ('| # | Text | Source |\n|---|------|--------|\n'
                + '\n'.join(f"| {r['num']} | {r['text']} | {r['source']} |" for r in rows))
    lines = [f"| {r['num']} | {r['text']} | {r['demand']} | {r['source']} |" for r in rows]
    return TABLE_HEADER + '\n' + '\n'.join(lines)
