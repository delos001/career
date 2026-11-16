#!/usr/bin/env python3
"""
cv_to_docx.py - render a targeted CV (cv_content.md) to a formatted .docx

Converts the cv-targeted skill's handoff artifact (cv_content.md) into a Word
document. Every format rule (page geometry, fonts, sizes, alignment, bold /
italic / caps, spacing, bullets, footer) comes from rules/cv/cv-format.yaml,
read at import and checked: a missing or unrecognized setting stops the script.
This script holds only how cv_content.md is read and how Word builds a list.

Input grammar (the cv_qc.py + cv-architect contract):
  - '# Name' and the contact line(s) sit above the first '## ' heading.
  - '## <Section>'           section heading.
  - '### <subheading text>'  within-role thematic subheading (its following
                             '<!-- cr: CR-NNN -->' marker line strips to empty).
                             Any deeper level ('#### ', ...) renders the same, so
                             an architect heading-level slip never renders raw hashes.
  - '- <text> <!-- src: ... -->'  bullet; the citation comment is stripped.
  - Company / role header lines are plain text (not list items); bold/italic are
    carried by markdown '**...**' / '*...*' and rendered faithfully.
  - All HTML comments ('<!-- ... -->') are stripped so citations never render.

The command line refuses to overwrite a .docx that changed since this script last
wrote it, or that it has no record of writing, because hand edits are never synced
back to cv_content.md (GitHub #69). It exits 2 and writes nothing; --overwrite-edited
overrides. The record is a hash in the output folder's scratch subfolder.

Author    : Jason Delosh
Created   : 2026-06-02
Project   : career
Usage     : python scripts/cv_to_docx.py --cv-file <cv_content.md> --out <out.docx>
                [--overwrite-edited]
Depends   : python-docx, pyyaml
"""

import argparse
import hashlib
import os
import re
import sys

import yaml

import _config

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ---------------------------------------------------------------------------
# Format settings
# Every format rule lives in rules/cv/cv-format.yaml. FORMAT_SCHEMA lists every
# setting the file must hold; a setting missing from the file, or present in
# the file but not listed here, stops the script, so a typo or a stale setting
# never renders silently.
# ---------------------------------------------------------------------------

# Setting types: NUM a number; SIZE a font size in points, in half-point steps
# (Word stores sizes as whole half-points); BOOL true or false; TEXT a string;
# ALIGN_T one of the ALIGN names; SECTIONS a list of section names.
NUM, SIZE, BOOL, TEXT, ALIGN_T, SECTIONS = 'a number', 'a size in half-point steps', \
    'true or false', 'text', 'an alignment', 'a list of section names'

FORMAT_SCHEMA = {
    'page': {'width_in': NUM, 'height_in': NUM, 'margin_in': NUM,
             'header_distance_in': NUM, 'footer_distance_in': NUM},
    'body': {'font': TEXT, 'size_pt': SIZE, 'line_spacing': NUM, 'space_before_pt': NUM,
             'space_after_pt': NUM, 'align': ALIGN_T},
    'name': {'size_pt': SIZE, 'align': ALIGN_T, 'space_before_pt': NUM},
    'contact': {'size_pt': SIZE, 'align': ALIGN_T, 'space_before_pt': NUM},
    'section_header': {'bold': BOOL, 'all_caps': BOOL, 'space_before_pt': NUM},
    'subheading': {'italic': BOOL, 'space_before_pt': NUM},
    'company_line': {'name_bold': BOOL, 'first_space_before_pt': NUM, 'space_before_pt': NUM},
    'role_title': {'first_space_before_pt': NUM, 'space_before_pt': NUM, 'stacked_space_before_pt': NUM},
    'company_block_sections': SECTIONS,
    'project_header': {'first_space_before_pt': NUM, 'space_before_pt': NUM},
    'project_sections': SECTIONS,
    'bullets': {'char': TEXT, 'font': TEXT, 'size_pt': SIZE, 'indent_left_dxa': NUM,
                'indent_hanging_dxa': NUM, 'space_before_pt': NUM, 'every_line_sections': SECTIONS},
    'footer': {'text': TEXT, 'size_pt': SIZE, 'align': ALIGN_T, 'space_before_pt': NUM},
}

ALIGN = {
    'left': WD_ALIGN_PARAGRAPH.LEFT,
    'center': WD_ALIGN_PARAGRAPH.CENTER,
    'right': WD_ALIGN_PARAGRAPH.RIGHT,
    'justify': WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def _type_ok(value, kind):
    """True when a setting's value has the type its schema entry names."""
    # bool is a subclass of int in Python, so exclude it from the number checks.
    is_num = isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == NUM:
        return is_num and value >= 0
    if kind == SIZE:
        return is_num and value > 0 and float(value * 2).is_integer()
    if kind == BOOL:
        return isinstance(value, bool)
    if kind == TEXT:
        return isinstance(value, str) and value != ''
    if kind == ALIGN_T:
        return value in ALIGN
    if kind == SECTIONS:
        return (isinstance(value, list) and value
                and all(isinstance(v, str) and v.strip() for v in value))
    raise ValueError(f'unknown setting type {kind}')


def format_path():
    """Return the path of the configured format file."""
    root, cfg = _config.load()
    return os.path.join(root, cfg['paths']['cv_rules'], cfg['filenames']['cv_format_file'])


def _section_set(names):
    """Normalize section names the way headings are matched: lowercase, single spaces."""
    return {re.sub(r'\s+', ' ', n).strip().lower() for n in names}


def load_format(text=None, known_sections=None):
    """Return cv-format.yaml as a dict, after checking it against FORMAT_SCHEMA
    and checking every section it names against cv-structure.md.

    Takes the file text and the known section names for tests; reads the
    configured files otherwise.
    """
    if text is None:
        with open(format_path(), encoding='utf-8') as f:
            text = f.read()
    fmt = yaml.safe_load(text) or {}
    problems = []
    for group, spec in FORMAT_SCHEMA.items():
        if group not in fmt:
            problems.append(f'missing {group}')
            continue
        if not isinstance(spec, dict):
            # A top-level setting with its own type (a section list).
            if not _type_ok(fmt[group], spec):
                problems.append(f'{group} must be {spec}, not {fmt[group]!r}')
            continue
        values = fmt[group] if isinstance(fmt[group], dict) else {}
        problems += [f'missing {group}.{k}' for k in sorted(set(spec) - set(values))]
        problems += [f'unknown {group}.{k}' for k in sorted(set(values) - set(spec))]
        for key, kind in spec.items():
            if key in values and not _type_ok(values[key], kind):
                extra = f' ({", ".join(ALIGN)})' if kind == ALIGN_T else ''
                problems.append(f'{group}.{key} must be {kind}{extra}, not {values[key]!r}')
    problems += [f'unknown {g}' for g in sorted(set(fmt) - set(FORMAT_SCHEMA))]

    # Every section named in a section list must be a real CV section: one in
    # the Section order block of cv-structure.md (cv_qc.py parses that block).
    if known_sections is None:
        import cv_qc
        order = cv_qc.load_section_order()
        known_sections = set(order['order']) | order['work_output']
    for where, names in (('company_block_sections', fmt.get('company_block_sections')),
                         ('project_sections', fmt.get('project_sections')),
                         ('bullets.every_line_sections', (fmt.get('bullets') or {}).get('every_line_sections'))):
        if _type_ok(names, SECTIONS):
            problems += [f'{where} names {n!r}, which is not a section in cv-structure.md'
                         for n in names if _section_set([n]).pop() not in known_sections]
    if problems:
        raise ValueError('cv-format.yaml: ' + '; '.join(problems))
    return fmt


FMT = load_format()

PAGE = FMT['page']
BODY = FMT['body']
BULLETS = FMT['bullets']
BULLET_NUM_ID = 100              # our injected numbering definition id (internal, not a format rule)


# ---------------------------------------------------------------------------
# Input parsing patterns (how cv_content.md is read; not format rules)
# ---------------------------------------------------------------------------

# A company header line is distinguished from a role-title line by a location
# token: '(Remote)'/'(Onsite)'/'(Hybrid)' or a 'City, ST' two-letter state.
LOCATION_RE = re.compile(r'\((?:Remote|Onsite|On-site|Hybrid)\)|,\s*[A-Z]{2}\b')
COMMENT_RE = re.compile(r'<!--.*?-->')
# Inline markdown tokenizer: a bold span, an italic span, or a plain run.
INLINE_RE = re.compile(r'(\*\*.+?\*\*|\*[^*]+?\*)')
# A {FIELD} token in the footer text, rendered as a live Word field.
FIELD_RE = re.compile(r'\{([A-Z]+)\}')


# ---------------------------------------------------------------------------
# Low-level docx helpers (paragraph spacing, runs)
# ---------------------------------------------------------------------------

def _set_spacing(para, before_pt):
    """Body line spacing and space after, `before_pt` before."""
    pPr = para._p.get_or_add_pPr()
    spacing = pPr.find(qn('w:spacing'))
    if spacing is None:
        spacing = OxmlElement('w:spacing')
        pPr.append(spacing)
    spacing.set(qn('w:before'), str(int(before_pt * 20)))
    spacing.set(qn('w:after'), str(int(BODY['space_after_pt'] * 20)))
    spacing.set(qn('w:line'), str(int(240 * BODY['line_spacing'])))   # 240 = single
    spacing.set(qn('w:lineRule'), 'auto')


def _set_numbering(para, num_id, ilvl=0):
    """Attach a list numbering reference (numPr) to a paragraph."""
    pPr = para._p.get_or_add_pPr()
    numPr = OxmlElement('w:numPr')
    ilvl_el = OxmlElement('w:ilvl')
    ilvl_el.set(qn('w:val'), str(ilvl))
    numId_el = OxmlElement('w:numId')
    numId_el.set(qn('w:val'), str(num_id))
    numPr.append(ilvl_el)
    numPr.append(numId_el)
    pPr.append(numPr)


def _run(para, text, bold=False, italic=False, size_pt=None, font=None, color=None):
    r = para.add_run(text)
    r.font.name = font or BODY['font']
    r.font.size = Pt(size_pt or BODY['size_pt'])
    # Only emit the b/i toggles when on, so plain runs carry no element (the
    # examples omit them entirely rather than writing an explicit "off").
    if bold:
        r.font.bold = True
    if italic:
        r.font.italic = True
    if color:
        r.font.color.rgb = RGBColor(*color)
    return r


def _para(doc, before_pt, align=None):
    p = doc.add_paragraph()
    p.alignment = ALIGN[align or BODY['align']]
    _set_spacing(p, before_pt)
    return p


def _add_inline(para, text, size_pt=None):
    """Render a line with inline markdown: '**bold**' and '*italic*' spans.

    Splits the text into bold / italic / plain runs so company names, zone
    labels, degree names, etc. carry their markdown emphasis faithfully.
    """
    for token in INLINE_RE.split(text):
        if not token:
            continue
        if token.startswith('**') and token.endswith('**'):
            _run(para, token[2:-2], bold=True, size_pt=size_pt)
        elif token.startswith('*') and token.endswith('*'):
            _run(para, token[1:-1], italic=True, size_pt=size_pt)
        else:
            _run(para, token, size_pt=size_pt)


# ---------------------------------------------------------------------------
# Footer and bullet list definition
# ---------------------------------------------------------------------------

def _add_field(para, instr, size_pt):
    """Append a simple Word field (e.g. PAGE, NUMPAGES) to a footer paragraph.

    Uses w:fldSimple with a placeholder result; Word recalculates the value when
    the document is opened.
    """
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), instr)
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), BODY['font'])
    rFonts.set(qn('w:hAnsi'), BODY['font'])
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(int(size_pt * 2)))   # whole half-points
    rPr.append(rFonts)
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.text = '1'
    r.append(t)
    fld.append(r)
    para._p.append(fld)


def add_page_footer(sec):
    """The footer text on every page, its {FIELD} tokens as live Word fields."""
    footer_fmt = FMT['footer']
    footer = sec.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = ALIGN[footer_fmt['align']]
    _set_spacing(p, footer_fmt['space_before_pt'])
    # re.split with one capture group alternates text, field name, text, ...
    for i, part in enumerate(FIELD_RE.split(footer_fmt['text'])):
        if i % 2:
            _add_field(p, part, footer_fmt['size_pt'])
        elif part:
            _run(p, part, size_pt=footer_fmt['size_pt'])


def _ensure_bullet_numbering(doc):
    """Add an abstractNum + num for the CV bullet to the document numbering part.

    The glyph, its font and size, and the indents come from the bullets
    settings; the rest is how Word defines a one-level bulleted list.
    """
    numbering = doc.part.numbering_part.element
    abstract_id = str(BULLET_NUM_ID)

    abstract = OxmlElement('w:abstractNum')
    abstract.set(qn('w:abstractNumId'), abstract_id)
    lvl = OxmlElement('w:lvl')
    lvl.set(qn('w:ilvl'), '0')
    for tag, val in (('w:start', '1'), ('w:numFmt', 'bullet'),
                     ('w:lvlText', BULLETS['char']), ('w:lvlJc', 'left')):
        el = OxmlElement(tag)
        el.set(qn('w:val'), val)
        lvl.append(el)
    pPr = OxmlElement('w:pPr')
    ind = OxmlElement('w:ind')
    ind.set(qn('w:left'), str(BULLETS['indent_left_dxa']))
    ind.set(qn('w:hanging'), str(BULLETS['indent_hanging_dxa']))
    pPr.append(ind)
    lvl.append(pPr)
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), BULLETS['font'])
    rFonts.set(qn('w:hAnsi'), BULLETS['font'])
    rFonts.set(qn('w:hint'), 'default')
    rPr.append(rFonts)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(int(BULLETS['size_pt'] * 2)))   # whole half-points
    rPr.append(sz)
    lvl.append(rPr)
    abstract.append(lvl)

    num = OxmlElement('w:num')
    num.set(qn('w:numId'), str(BULLET_NUM_ID))
    abstract_ref = OxmlElement('w:abstractNumId')
    abstract_ref.set(qn('w:val'), abstract_id)
    num.append(abstract_ref)

    # abstractNum elements must precede num elements in the numbering part.
    last_abstract = numbering.findall(qn('w:abstractNum'))
    if last_abstract:
        last_abstract[-1].addnext(abstract)
    else:
        numbering.insert(0, abstract)
    numbering.append(num)


# ---------------------------------------------------------------------------
# Element builders
# ---------------------------------------------------------------------------

def add_name(doc, text):
    p = _para(doc, FMT['name']['space_before_pt'], align=FMT['name']['align'])
    _run(p, text, size_pt=FMT['name']['size_pt'])


def add_contact(doc, text):
    p = _para(doc, FMT['contact']['space_before_pt'], align=FMT['contact']['align'])
    _add_inline(p, text, size_pt=FMT['contact']['size_pt'])


def add_section_header(doc, text):
    fmt = FMT['section_header']
    p = _para(doc, before_pt=fmt['space_before_pt'])
    _run(p, text.upper() if fmt['all_caps'] else text, bold=fmt['bold'])


def add_subheading(doc, text):
    fmt = FMT['subheading']
    p = _para(doc, before_pt=fmt['space_before_pt'])
    _run(p, text, italic=fmt['italic'])


def add_line(doc, text, before_pt):
    """A non-bullet content line rendered with inline markdown."""
    p = _para(doc, before_pt=before_pt)
    _add_inline(p, text)


def add_bullet(doc, text):
    p = _para(doc, BULLETS['space_before_pt'])
    _set_numbering(p, BULLET_NUM_ID)
    _add_inline(p, text)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _strip_comments(line):
    return COMMENT_RE.sub('', line).rstrip()


def _is_company_line(text):
    """A header line naming a company (carries a location token)."""
    return bool(LOCATION_RE.search(text))


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_cv(md_path, out_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    doc = Document()
    # Drop the default empty paragraph the template starts with.
    for p in doc.paragraphs:
        if not p.text.strip():
            p._element.getparent().remove(p._element)
            break

    sec = doc.sections[0]
    sec.page_height = Inches(PAGE['height_in'])
    sec.page_width = Inches(PAGE['width_in'])
    sec.top_margin = sec.bottom_margin = Inches(PAGE['margin_in'])
    sec.left_margin = sec.right_margin = Inches(PAGE['margin_in'])
    sec.header_distance = Inches(PAGE['header_distance_in'])
    sec.footer_distance = Inches(PAGE['footer_distance_in'])

    normal = doc.styles['Normal']
    normal.font.name = BODY['font']
    normal.font.size = Pt(BODY['size_pt'])
    normal.paragraph_format.space_before = Pt(BODY['space_before_pt'])
    normal.paragraph_format.space_after = Pt(BODY['space_after_pt'])

    _ensure_bullet_numbering(doc)
    add_page_footer(sec)

    company_fmt, title_fmt = FMT['company_line'], FMT['role_title']
    # Read the section lists at render time, not import time, so every setting
    # is taken from FMT when the document is built.
    force_bullet_sections = _section_set(BULLETS['every_line_sections'])
    company_block_sections = _section_set(FMT['company_block_sections'])
    project_sections = _section_set(FMT['project_sections'])
    project_fmt = FMT['project_header']

    # Parser state.
    section = None              # normalized current section
    saw_name = False            # have we emitted the name (h1) yet
    in_first_section = False    # have we passed the first '## '
    pending_first_title = False  # next title under the current company is the 1st
    prev_was_title = False      # previous company-block line was a role-title line
    section_just_started = False  # next content line is the first under a header

    for raw in lines:
        line = _strip_comments(raw)
        if not line.strip():
            continue

        # Name (h1) and contact block, above the first '## '.
        if not in_first_section:
            if line.startswith('# ') and not line.startswith('## '):
                add_name(doc, line[2:].strip())
                saw_name = True
                continue
            if saw_name and not line.startswith('#'):
                add_contact(doc, line.strip())
                continue

        # Section heading.
        if line.startswith('## '):
            section = re.sub(r'\s+', ' ', line[3:].strip()).lower()
            in_first_section = True
            pending_first_title = False
            prev_was_title = False
            section_just_started = True
            add_section_header(doc, line[3:].strip())
            continue

        # Within-role thematic subheading: any heading deeper than the '## '
        # section ('### ', '#### ', ...). Tolerant of the heading level the
        # cv-architect emits - a level slip (e.g. '####') must still render as a
        # styled subheading, not fall through to a body line with literal hashes.
        if re.match(r'^#{3,}\s', line):
            add_subheading(doc, re.sub(r'^#{3,}\s+', '', line).strip())
            prev_was_title = False
            continue

        # Bullet (explicit '- ' list item, in any section).
        if re.match(r'^\s*-\s+', line):
            add_bullet(doc, re.sub(r'^\s*-\s+', '', line).strip())
            prev_was_title = False
            continue

        text = line.strip()

        # Sections whose every content line renders as a bullet.
        if section in force_bullet_sections:
            add_bullet(doc, text)
            prev_was_title = False
            continue

        # Non-list content line: spacing depends on the section.
        if section in company_block_sections:
            if _is_company_line(text):
                # The company name is the segment before the first ' | '. It may
                # arrive plain (older files) or bold-wrapped (current output), so
                # strip any bold markers and apply the format setting uniformly;
                # the text after the first '|' stays regular.
                name, sep, rest = text.partition(' | ')
                name = re.sub(r'\*\*', '', name.strip())
                if company_fmt['name_bold']:
                    name = f'**{name}**'
                rendered = name + (f' | {rest}' if sep else '')
                add_line(doc, rendered,
                         before_pt=company_fmt['first_space_before_pt'] if section_just_started
                         else company_fmt['space_before_pt'])
                section_just_started = False
                pending_first_title = True
                prev_was_title = False
            elif pending_first_title:
                # First role title under this company.
                add_line(doc, text, before_pt=title_fmt['first_space_before_pt'])
                pending_first_title = False
                prev_was_title = True
            elif prev_was_title:
                # A role line directly under another role line.
                add_line(doc, text, before_pt=title_fmt['stacked_space_before_pt'])
            else:
                # A later role, following the previous role's bullets.
                add_line(doc, text, before_pt=title_fmt['space_before_pt'])
                prev_was_title = True
        elif section in project_sections:
            # Every non-bullet line here is a project header line.
            add_line(doc, text,
                     before_pt=project_fmt['first_space_before_pt'] if section_just_started
                     else project_fmt['space_before_pt'])
            section_just_started = False
            prev_was_title = False
        else:
            add_line(doc, text, before_pt=BODY['space_before_pt'])
            prev_was_title = False

    doc.save(out_path)
    print(f'Saved: {out_path}')
    return out_path


# ---------------------------------------------------------------------------
# Overwrite guard (GitHub #69)
# Word rewrites the whole file on any save, so a hash of the file's bytes catches
# every edit, formatting included. Lives here rather than in build_cv so that
# cv_measure.py's throwaway renders are unaffected.
# ---------------------------------------------------------------------------

def _file_hash(path):
    """Return the SHA-256 of a file's bytes."""
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def _record_path(out_path, scratch_subdir):
    """Return where the hash of a rendered .docx is kept."""
    folder, name = os.path.split(os.path.abspath(out_path))
    return os.path.join(folder, scratch_subdir, f'{name}.render.sha256')


def _is_unrecorded_or_edited(out_path, record_path):
    """True when out_path exists and is not exactly what this script last wrote."""
    if not os.path.exists(out_path):
        return False
    if not os.path.exists(record_path):
        return True
    with open(record_path, encoding='utf-8') as f:
        return f.read().strip() != _file_hash(out_path)


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Render cv_content.md to a formatted .docx')
    parser.add_argument('--cv-file', required=True, help='path to cv_content.md')
    parser.add_argument('--out', required=True, help='path to the output .docx')
    parser.add_argument('--overwrite-edited', action='store_true',
                        help='replace the .docx even if it changed since the last render')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        _, cfg = _config.load()
        record = _record_path(args.out, cfg['filenames']['scratch_subdir'])
        if not args.overwrite_edited and _is_unrecorded_or_edited(args.out, record):
            print(f'Refused: {args.out} changed since it was last rendered, or has no render '
                  'record, so it may hold hand edits. Nothing was written.', file=sys.stderr)
            sys.exit(2)
        build_cv(args.cv_file, args.out)
        os.makedirs(os.path.dirname(record), exist_ok=True)
        with open(record, 'w', encoding='utf-8') as f:
            f.write(_file_hash(args.out))
    except FileNotFoundError as e:
        print(f'Error: input file not found: {e.filename}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
