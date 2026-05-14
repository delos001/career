#!/usr/bin/env python3
"""
Convert a CV markdown file to a formatted Word document.
Follows design/format_spec.md exactly.

Usage:
    python scripts/cv_to_docx.py <input.md> <output.docx>
    python scripts/cv_to_docx.py   # uses default PFM paths
"""

import re
import sys
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _set_para_spacing(para, space_before_pt=0):
    """space_before in pt, space_after=0, single line (240 DXA auto)."""
    pPr = para._p.get_or_add_pPr()
    spacing = pPr.find(qn('w:spacing'))
    if spacing is None:
        spacing = OxmlElement('w:spacing')
        pPr.append(spacing)
    spacing.set(qn('w:before'), str(int(space_before_pt * 20)))  # pt -> DXA
    spacing.set(qn('w:after'), '0')
    spacing.set(qn('w:line'), '240')
    spacing.set(qn('w:lineRule'), 'auto')


def _set_para_indent(para, left_dxa, hanging_dxa):
    pPr = para._p.get_or_add_pPr()
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        ind = OxmlElement('w:ind')
        pPr.append(ind)
    ind.set(qn('w:left'), str(left_dxa))
    ind.set(qn('w:hanging'), str(hanging_dxa))


def _make_run(para, text, bold=False, italic=False, size_pt=11,
              font_name='Calibri', color_rgb=None):
    run = para.add_run(text)
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color_rgb:
        run.font.color.rgb = RGBColor(*color_rgb)
    return run


def _new_para(doc, align=WD_ALIGN_PARAGRAPH.LEFT, space_before_pt=0):
    para = doc.add_paragraph()
    para.alignment = align
    _set_para_spacing(para, space_before_pt)
    return para


def _strip_md(text):
    """Remove **bold** and *italic* markdown markers."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    return text


def _parse_bold_line(line):
    """Return (bold_part, rest) for a line starting with **text**..."""
    m = re.match(r'^\*\*(.+?)\*\*(.*)$', line)
    if m:
        return m.group(1), m.group(2)
    return line, ''


def _extract_company_and_title(bold_part, rest):
    """
    Input:  bold_part='Company', rest=' | Title | Dates [*(note)*]'
    Output: (company_str, title_dates_raw)
    title_dates_raw preserves *(...)* for italic rendering in add_title_para.
    """
    company = bold_part.strip()
    if rest.startswith(' | '):
        title_dates_raw = rest[3:]
    elif rest.startswith('| '):
        title_dates_raw = rest[2:]
    else:
        title_dates_raw = rest.strip()
    return company, title_dates_raw


# ---------------------------------------------------------------------------
# Paragraph builders
# ---------------------------------------------------------------------------

def add_name_para(doc, text):
    """Name header: 18pt, centered."""
    p = _new_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=0)
    _make_run(p, text, size_pt=18)


def add_contact_para(doc, text):
    """Contact line: 10pt, centered."""
    p = _new_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before_pt=0)
    _make_run(p, text, size_pt=10)


def add_section_header(doc, text):
    """Section header: bold 11pt, 8pt before, mixed case."""
    p = _new_para(doc, space_before_pt=8)
    _make_run(p, text, bold=True)


def add_body_para(doc, text, space_before_pt=0):
    """Regular narrative body text: 11pt, left-aligned."""
    text = _strip_md(text)
    p = _new_para(doc, space_before_pt=space_before_pt)
    _make_run(p, text)


def add_bullet_para(doc, text):
    """
    Middle-dot bullet per format_spec.md.
    Bullet char: U+00B7 in Cambria 11pt; text: Calibri 11pt.
    Indent: left 144 DXA, hanging 144 DXA.
    """
    text = _strip_md(text)
    p = _new_para(doc, space_before_pt=0)
    _set_para_indent(p, left_dxa=144, hanging_dxa=144)
    br = p.add_run('· ')
    br.font.name = 'Cambria'
    br.font.size = Pt(11)
    tr = p.add_run(text)
    tr.font.name = 'Calibri'
    tr.font.size = Pt(11)


def add_company_para(doc, text, space_before_pt=8):
    """Company name line: bold 11pt, 8pt before."""
    p = _new_para(doc, space_before_pt=space_before_pt)
    _make_run(p, text, bold=True)


def add_title_para(doc, text, space_before_pt=0):
    """
    Job title line: bold 11pt.
    Handles trailing *(italic note)* rendered as non-bold italic.
    """
    p = _new_para(doc, space_before_pt=space_before_pt)
    m = re.search(r'\s*\*\((.+?)\)\*\s*$', text)
    if m:
        normal = text[:m.start()]
        italic_text = '(' + m.group(1) + ')'
        _make_run(p, normal, bold=True)
        _make_run(p, ' ' + italic_text, bold=False, italic=True)
    else:
        _make_run(p, text, bold=True)


def add_earlier_role_para(doc, text):
    """
    Earlier Professional Roles entry.
    SectionHeading style: Calibri Light, bold, #2198CF, 8pt before.
    """
    text = _strip_md(text)
    p = _new_para(doc, space_before_pt=8)
    _make_run(p, text, bold=True, font_name='Calibri Light',
              color_rgb=(0x21, 0x98, 0xCF))


def add_edu_cert_para(doc, bold_part, rest):
    """Education or Certification: degree/cert name bold, rest normal."""
    p = _new_para(doc, space_before_pt=0)
    _make_run(p, bold_part, bold=True)
    if rest:
        _make_run(p, rest, bold=False)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_cv(md_path, out_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    doc = Document()

    # Remove default empty paragraph that Document() creates
    for p in doc.paragraphs:
        if not p.text.strip():
            p._element.getparent().remove(p._element)
            break

    # Page layout: US Letter, 1-inch margins all sides
    sec = doc.sections[0]
    sec.page_height = Inches(11)
    sec.page_width = Inches(8.5)
    sec.top_margin = Inches(1)
    sec.bottom_margin = Inches(1)
    sec.left_margin = Inches(1)
    sec.right_margin = Inches(1)
    sec.header_distance = Inches(0.5)
    sec.footer_distance = Inches(0.5)

    # Default style: Calibri 11pt, no space after
    normal = doc.styles['Normal']
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.space_before = Pt(0)
    normal.font.name = 'Calibri'
    normal.font.size = Pt(11)

    # Parser state
    current_section = None
    prev_company = None
    saw_name = False

    for raw_line in lines:
        line = raw_line.rstrip()

        # Skip blank lines and horizontal rules
        if not line or line == '---':
            continue

        # ── Name (h1) ──────────────────────────────────────────────────────
        if re.match(r'^# (?!#)', line):
            add_name_para(doc, line[2:].strip())
            saw_name = True
            continue

        # ── Section header (h2) ────────────────────────────────────────────
        if line.startswith('## '):
            section_name = line[3:].strip()
            current_section = section_name
            prev_company = None
            saw_name = False
            add_section_header(doc, section_name)
            continue

        # ── Contact line (first text line before any section header) ───────
        if saw_name and current_section is None:
            add_contact_para(doc, line)
            saw_name = False
            continue

        # ── Bullet item ────────────────────────────────────────────────────
        if line.startswith('- '):
            add_bullet_para(doc, line[2:].strip())
            continue

        # ── Bold-led line: **...** ─────────────────────────────────────────
        if line.startswith('**'):
            bold_part, rest = _parse_bold_line(line)

            if current_section == 'Earlier Professional Roles':
                add_earlier_role_para(doc, bold_part + rest)

            elif current_section == 'Professional Experience':
                company, title_dates_raw = _extract_company_and_title(bold_part, rest)

                if company == prev_company:
                    # Subsequent role under same company: title line only, 8pt before
                    add_title_para(doc, title_dates_raw, space_before_pt=8)
                else:
                    # New company block: company line (8pt) + title line (0pt)
                    add_company_para(doc, company, space_before_pt=8)
                    if title_dates_raw:
                        add_title_para(doc, title_dates_raw, space_before_pt=0)
                    prev_company = company

            elif current_section in ('Education', 'Certifications'):
                add_edu_cert_para(doc, bold_part, rest)

            else:
                # Fallback: bold body line
                p = _new_para(doc)
                _make_run(p, bold_part + rest, bold=True)
            continue

        # ── Regular body paragraph ─────────────────────────────────────────
        add_body_para(doc, line)

    doc.save(out_path)
    print(f'Saved: {out_path}')
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) == 3:
        md_path = sys.argv[1]
        out_path = sys.argv[2]
    else:
        base = r'C:\Users\delos\code\career\personal\applications\PFM_APP-003_2026-05'
        md_path = os.path.join(base, 'CV_Draft_2026-05.md')
        out_path = os.path.join(
            base,
            'Jason_Delosh_CV_PrecisionForMedicine_AssocOpExDir_2026-05.docx'
        )

    if not os.path.exists(md_path):
        print(f'Error: input file not found: {md_path}', file=sys.stderr)
        sys.exit(1)

    build_cv(md_path, out_path)
