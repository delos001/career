# CV Formatting Specification

> **This file is the authoritative formatting reference for all CV output.**
> In any conflict between this spec and instructions elsewhere (e.g. CLAUDE.md skill), this spec takes precedence.
>
> Extracted from `user_CV_General_Lrge_Enterprise_Established.docx` and `user_CV_General_Mid_Size_Scale_Up.docx` via XML analysis.
> Both source files are formatting-identical. This single spec covers both archetypes.
> All measurements in DXA (twips) unless noted. 1440 DXA = 1 inch. 1 pt = 20 DXA.

---

## Page Layout

| Property | Value | Notes |
|---|---|---|
| Paper size | US Letter | 12240 × 15840 DXA |
| Top margin | 1440 DXA | 1 inch |
| Bottom margin | 1440 DXA | 1 inch |
| Left margin | 1440 DXA | 1 inch |
| Right margin | 1440 DXA | 1 inch |
| Header distance | 720 DXA | 0.5 inch |
| Footer distance | 720 DXA | 0.5 inch |
| Content width | 9360 DXA | 12240 − 2880 |

---

## Typography

| Element | Font | Size (half-pts) | Size (pt) | Bold | Color |
|---|---|---|---|---|---|
| Default body | Calibri (minorHAnsi theme) | 22 | 11 | No | Black |
| Name header | Calibri (minorHAnsi theme) | 36 | 18 | No | Black |
| Contact line | Calibri (minorHAnsi theme) | 20 | 10 | No | Black |
| Section headers | Calibri (minorHAnsi theme) | 22 | 11 | Yes | Black |
| Company header | Calibri (minorHAnsi theme) | 22 | 11 | Yes | Black |
| Job title | Calibri (minorHAnsi theme) | 22 | 11 | Yes | Black |
| Body text / narrative | Calibri (minorHAnsi theme) | 22 | 11 | No | Black |
| Bullet text | Calibri (minorHAnsi theme) | 22 | 11 | No | Black |
| Earlier roles (SectionHeading style) | Calibri (majorHAnsi theme) | 22 | 11 | Yes | #2198CF |
| Earlier roles secondary (Subsection style) | Calibri (minorHAnsi theme) | 18 | 9 | Yes | All-caps, #171717 |

> **Note:** Section headers must be mixed case bold — NEVER ALL CAPS (except Subsection style used only for earlier roles secondary entries).

---

## Line Spacing

| Property | Value |
|---|---|
| Line spacing | Single (240 DXA, auto rule) — all paragraphs |
| Space after | 0 — all paragraphs |

---

## Paragraph Spacing (Space Before)

| Element | Space Before (DXA) | Space Before (pt) |
|---|---|---|
| Name header | 0 | 0 |
| Contact line | 0 | 0 |
| Section header | 160 | 8 |
| First company block header in section | 160 | 8 |
| First job title under a company | 0 | 0 |
| Subsequent job titles under same company | 160 | 8 |
| Body text / narrative | 0 | 0 |
| Bullet items | 0 | 0 |
| Education entries | 0 | 0 |

> **Rule:** No unnecessary carriage returns anywhere. Spacing is achieved via Space Before values above — not blank paragraphs.

---

## Alignment

| Element | Alignment |
|---|---|
| Name header | Center |
| Contact line | Center |
| All other content | Left |

---

## Bullets

Single-column bulleted list only. Two-column tables are never used anywhere in the document.

| Property | Value |
|---|---|
| Bullet character | · (middle dot, U+00B7) |
| Bullet font | Cambria |
| Indent left | 144 DXA |
| Hanging indent | 144 DXA |
| Font size | 22 half-pts (11pt) |

**python-docx implementation:**
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Inches
import docx

# Add bullet paragraph
def add_bullet(doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles['Normal']

    # Set indentation: left 144 DXA, hanging 144 DXA (144 DXA = 0.1 inch)
    pPr = p._p.get_or_add_pPr()
    ind = OxmlElement('w:ind')
    ind.set(qn('w:left'), '144')
    ind.set(qn('w:hanging'), '144')
    pPr.append(ind)

    # Add bullet character run (middle dot U+00B7, Cambria font, 11pt)
    bullet_run = p.add_run('\u00B7 ')
    bullet_run.font.name = 'Cambria'
    bullet_run.font.size = Pt(11)

    # Add bullet text run (Calibri, 11pt)
    text_run = p.add_run(text)
    text_run.font.name = 'Calibri'
    text_run.font.size = Pt(11)
```

---

## Custom Paragraph Styles

Two custom styles exist in the source documents. Use only for the elements described.

### SectionHeading
Used for: "Earlier Professional Roles" section entries (company/role lines, not body text).

| Property | Value |
|---|---|
| Font | majorHAnsi theme (Calibri Light) |
| Bold | Yes |
| Color | #2198CF |
| Space before | 160 DXA (8pt) |
| Space after | 0 |
| Line spacing | Single |

### Subsection
Used for: Secondary earlier role entries (older/less prominent roles in the earlier roles section).

| Property | Value |
|---|---|
| Bold | Yes |
| All caps | Yes |
| Color | #171717 |
| Size | 18 half-pts (9pt) |
| Space before | 0 |
| Space after | 0 |

---

## Project Entry Structure

Used for entries in the "Selected Projects" CV section. Structure differs from role entries — there is no company header or job title line.

| Element | Style | Notes |
|---|---|---|
| Project name | Bold, 11pt, Calibri | Same style as company header. Space before: 8pt (160 DXA). |
| Timeframe / context | Not bold, 11pt, Calibri | Rendered inline on the same line as project name, separated by a pipe ( \| ). |
| Repository link | Not bold, 11pt, Calibri | Optional. Plain text URL rendered inline on the same line as project name and timeframe, separated by a pipe ( \| ). Use the specific repo URL, not the GitHub profile landing page. Example: **AI-Augmented Career Development System** \| Personal Project \| 2025–Present \| github.com/delos001/career_development |
| Body text | Normal body style | Optional. Zero space before. Same style as narrative body text. |
| Bullets | Standard bullet style | Same bullet character, indent, and font as all other bullets. |

No job title line is used. The timeframe, context descriptor, and optional repository link replace it inline.

---

## Section Order

Section order is governed exclusively by the archetype approved in Phase 2. This spec does not define or default section order. Refer to the approved archetype.

---

## Output File Naming

```
Jason_Delosh_CV_[CompanyName]_[AbbreviatedRole]_[YYYY-MM].docx
```

Example: `Jason_Delosh_CV_Pfizer_VPDataOps_2026-03.docx`

---

## Formatting Rules (Consolidated)

These rules are the single source of truth for CV output. All rules below are derived from XML analysis of the source templates or carried forward from prior skill instructions where consistent with the template.

| Rule | Specification |
|---|---|
| Section header case | Mixed case bold — **never ALL CAPS** (Subsection style entries for secondary earlier roles are the only exception) |
| Font size | 11pt throughout the entire document, **except** the name header (18pt) and contact line (10pt) |
| Space between job title and first bullet | **None** — zero space before first bullet under any job title |
| Space before section headers | 8pt (160 DXA) |
| Space before first company block element in a section | 8pt (160 DXA) |
| Space before job titles (multiple roles under same company) | 8pt (160 DXA) before each title **except the first** title under a company |
| Carriage returns | No unnecessary carriage returns anywhere — spacing is achieved via Space Before values only |
| Name and contact alignment | Centered |
| Bullet list format | Single-column bulleted list only — **two-column tables are never used anywhere in the document** |
| Space after all paragraphs | 0 |
| Line spacing | Single (240 DXA, auto rule) throughout |
