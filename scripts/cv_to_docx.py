#!/usr/bin/env python3
"""
cv_to_docx.py - render a targeted CV (cv_content.md) to a formatted .docx

Converts the cv-targeted skill's handoff artifact (cv_content.md) into a Word
document whose geometry, typography, spacing, and bullets match the user's
example CVs (temp/CV_example_for_specs{1,2,3}.docx, the source of truth per the
cv-render-build-2026-06 design decision) and design/format_spec.md.

Input grammar (the cv_qc.py + cv-architect contract):
  - '# Name' and the contact line(s) sit above the first '## ' heading.
  - '## <Section>'           section heading.
  - '### <subheading text>'  within-role thematic subheading (its following
                             '<!-- cr: CR-NNN -->' marker line strips to empty).
  - '- <text> <!-- src: ... -->'  bullet; the citation comment is stripped.
  - Company / role header lines are plain text (not list items); bold/italic are
    carried by markdown '**...**' / '*...*' and rendered faithfully.
  - All HTML comments ('<!-- ... -->') are stripped so citations never render.

Bullets render as a native Word list (middle-dot U+00B7 in Cambria, indent
left=144 / hanging=144), not a literal bullet character run.

Author    : Jason Delosh
Created   : 2026-06-02
Project   : career
Usage     : python scripts/cv_to_docx.py --cv-file <cv_content.md> --out <out.docx>
Depends   : python-docx
"""

import argparse
import re
import sys

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ---------------------------------------------------------------------------
# Formatting constants (design/format_spec.md, grounded on the example CVs)
# Sizes in points; indents/spacing in DXA (twips): 1 pt = 20 DXA, 1440 DXA = 1 in.
# ---------------------------------------------------------------------------

FONT_BODY = 'Calibri'
FONT_BULLET = 'Symbol'           # round-bullet glyph font (U+F0B7 renders as •)
BULLET_CHAR = ''           # Symbol-font round bullet
SIZE_BODY = 11
SIZE_NAME = 18
SIZE_CONTACT = 10
SIZE_BULLET_GLYPH = 10           # bullet glyph size (text stays SIZE_BODY)

SPACE_SECTION = 8                # pt before a section header
SPACE_COMPANY = 8                # pt before the first company block in a section
SPACE_SUBSEQUENT_TITLE = 8       # pt before a 2nd+ role title under one company
SPACE_SUBHEADING = 6             # pt before a within-role thematic subheading

BULLET_INDENT_LEFT = 360         # DXA: text starts 0.25" from the margin
BULLET_INDENT_HANGING = 360      # DXA: bullet hangs back to the margin (0.25" gap)
BULLET_NUM_ID = 100              # our injected numbering definition id

# A company header line is distinguished from a role-title line by a location
# token: '(Remote)'/'(Onsite)'/'(Hybrid)' or a 'City, ST' two-letter state.
LOCATION_RE = re.compile(r'\((?:Remote|Onsite|On-site|Hybrid)\)|,\s*[A-Z]{2}\b')

# Sections whose every content line renders as a bullet (matched on the
# normalized lowercase heading). Professional Experience is excluded (its
# company / title header lines are not bullets); Selected Projects is excluded
# (its project-name line is a header, with '- ' description bullets beneath it).
FORCE_BULLET_SECTIONS = {
    'core competencies',
    'education',
    'earlier professional roles',
    'certifications & training',
    'professional affiliations',
    'technical proficiencies',
}

COMMENT_RE = re.compile(r'<!--.*?-->')
BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
# Inline markdown tokenizer: a bold span, an italic span, or a plain run.
INLINE_RE = re.compile(r'(\*\*.+?\*\*|\*[^*]+?\*)')


# ---------------------------------------------------------------------------
# Low-level docx helpers (paragraph spacing, indent, runs)
# ---------------------------------------------------------------------------

def _set_spacing(para, before_pt=0):
    """Single line spacing (240 auto), zero after, `before_pt` before."""
    pPr = para._p.get_or_add_pPr()
    spacing = pPr.find(qn('w:spacing'))
    if spacing is None:
        spacing = OxmlElement('w:spacing')
        pPr.append(spacing)
    spacing.set(qn('w:before'), str(int(before_pt * 20)))
    spacing.set(qn('w:after'), '0')
    spacing.set(qn('w:line'), '240')
    spacing.set(qn('w:lineRule'), 'auto')


def _set_indent(para, left_dxa, hanging_dxa):
    pPr = para._p.get_or_add_pPr()
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        ind = OxmlElement('w:ind')
        pPr.append(ind)
    ind.set(qn('w:left'), str(left_dxa))
    ind.set(qn('w:hanging'), str(hanging_dxa))


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


def _run(para, text, bold=False, italic=False, size_pt=SIZE_BODY,
         font=FONT_BODY, color=None):
    r = para.add_run(text)
    r.font.name = font
    r.font.size = Pt(size_pt)
    # Only emit the b/i toggles when on, so plain runs carry no element (the
    # examples omit them entirely rather than writing an explicit "off").
    if bold:
        r.font.bold = True
    if italic:
        r.font.italic = True
    if color:
        r.font.color.rgb = RGBColor(*color)
    return r


def _para(doc, align=WD_ALIGN_PARAGRAPH.LEFT, before_pt=0):
    p = doc.add_paragraph()
    p.alignment = align
    _set_spacing(p, before_pt)
    return p


def _add_inline(para, text, size_pt=SIZE_BODY):
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
# Numbering definition: inject the example CVs' bullet (U+00B7, Cambria, 144/144)
# ---------------------------------------------------------------------------

def _add_field(para, instr):
    """Append a simple Word field (e.g. PAGE, NUMPAGES) to a footer paragraph.

    Uses w:fldSimple with a placeholder result; Word recalculates the value when
    the document is opened.
    """
    fld = OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'), instr)
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), FONT_BODY)
    rFonts.set(qn('w:hAnsi'), FONT_BODY)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(SIZE_CONTACT * 2))   # half-points
    rPr.append(rFonts)
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.text = '1'
    r.append(t)
    fld.append(r)
    para._p.append(fld)


def add_page_footer(sec):
    """Centered 'Page X of Y' footer (10pt Calibri), shown on every page."""
    footer = sec.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _set_spacing(p, 0)
    _run(p, 'Page ', size_pt=SIZE_CONTACT)
    _add_field(p, 'PAGE')
    _run(p, ' of ', size_pt=SIZE_CONTACT)
    _add_field(p, 'NUMPAGES')


def _ensure_bullet_numbering(doc):
    """Add an abstractNum + num for the CV bullet to the document numbering part.

    Mirrors the example CVs' list definition: a middle-dot glyph in Cambria with
    a left indent of 144 DXA and a 144 DXA hanging indent. Idempotent on id.
    """
    numbering = doc.part.numbering_part.element
    abstract_id = str(BULLET_NUM_ID)

    abstract = OxmlElement('w:abstractNum')
    abstract.set(qn('w:abstractNumId'), abstract_id)
    lvl = OxmlElement('w:lvl')
    lvl.set(qn('w:ilvl'), '0')
    for tag, val in (('w:start', '1'), ('w:numFmt', 'bullet'),
                     ('w:lvlText', BULLET_CHAR), ('w:lvlJc', 'left')):
        el = OxmlElement(tag)
        el.set(qn('w:val'), val)
        lvl.append(el)
    pPr = OxmlElement('w:pPr')
    ind = OxmlElement('w:ind')
    ind.set(qn('w:left'), str(BULLET_INDENT_LEFT))
    ind.set(qn('w:hanging'), str(BULLET_INDENT_HANGING))
    pPr.append(ind)
    lvl.append(pPr)
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), FONT_BULLET)
    rFonts.set(qn('w:hAnsi'), FONT_BULLET)
    rFonts.set(qn('w:hint'), 'default')
    rPr.append(rFonts)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(SIZE_BULLET_GLYPH * 2))   # half-points
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
    p = _para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before_pt=0)
    _run(p, text, size_pt=SIZE_NAME)


def add_contact(doc, text):
    p = _para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before_pt=0)
    _add_inline(p, text, size_pt=SIZE_CONTACT)


def add_section_header(doc, text):
    p = _para(doc, before_pt=SPACE_SECTION)
    _run(p, text, bold=True)


def add_subheading(doc, text):
    p = _para(doc, before_pt=SPACE_SUBHEADING)
    _run(p, text, bold=True)


def add_line(doc, text, before_pt=0):
    """A non-bullet content line rendered with inline markdown."""
    p = _para(doc, before_pt=before_pt)
    _add_inline(p, text)


def add_bullet(doc, text):
    p = _para(doc, before_pt=0)
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

    # Page layout: US Letter, 0.75-inch margins, 0.5-inch header/footer.
    sec = doc.sections[0]
    sec.page_height = Inches(11)
    sec.page_width = Inches(8.5)
    sec.top_margin = sec.bottom_margin = Inches(0.75)
    sec.left_margin = sec.right_margin = Inches(0.75)
    sec.header_distance = sec.footer_distance = Inches(0.5)

    # Normal style: Calibri 11pt, no space before/after.
    normal = doc.styles['Normal']
    normal.font.name = FONT_BODY
    normal.font.size = Pt(SIZE_BODY)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)

    _ensure_bullet_numbering(doc)
    add_page_footer(sec)

    # Parser state.
    section = None              # normalized current section
    saw_name = False            # have we emitted the name (h1) yet
    in_first_section = False    # have we passed the first '## '
    pending_first_title = False  # next title under the current company is the 1st

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
            add_section_header(doc, line[3:].strip())
            continue

        # Within-role thematic subheading.
        if line.startswith('### '):
            add_subheading(doc, line[4:].strip())
            continue

        # Bullet (explicit '- ' list item, in any section).
        if re.match(r'^\s*-\s+', line):
            add_bullet(doc, re.sub(r'^\s*-\s+', '', line).strip())
            continue

        text = line.strip()

        # Sections whose every content line renders as a bullet.
        if section in FORCE_BULLET_SECTIONS:
            add_bullet(doc, text)
            continue

        # Non-list content line: spacing depends on the section.
        if section == 'professional experience':
            if _is_company_line(text):
                add_line(doc, text, before_pt=SPACE_COMPANY)
                pending_first_title = True
            elif pending_first_title:
                add_line(doc, text, before_pt=0)
                pending_first_title = False
            else:
                # A subsequent role title under the same company.
                add_line(doc, text, before_pt=SPACE_SUBSEQUENT_TITLE)
        else:
            add_line(doc, text, before_pt=0)

    doc.save(out_path)
    print(f'Saved: {out_path}')
    return out_path


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Render cv_content.md to a formatted .docx')
    parser.add_argument('--cv-file', required=True, help='path to cv_content.md')
    parser.add_argument('--out', required=True, help='path to the output .docx')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        build_cv(args.cv_file, args.out)
    except FileNotFoundError as e:
        print(f'Error: input file not found: {e.filename}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
