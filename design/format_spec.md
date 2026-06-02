# CV Formatting Specification

> **This file is the authoritative formatting reference for all CV output.**
> In any conflict between this spec and instructions elsewhere (e.g. CLAUDE.md skill), this spec takes precedence.
>
> Source of truth (confirmed 2026-06-02): the user's example CVs
> `temp/CV_example_for_specs{1,2,3}.docx`, verified by XML analysis. Where this
> spec conflicted with those files, the files governed and this spec was
> corrected to match (the `cv-render-build-2026-06` decision).
> The renderer that implements this spec is `scripts/cv_to_docx.py` (run by the
> cv-render skill); it parses `cv_content.md` and strips its citation comments.
> All measurements in DXA (twips) unless noted. 1440 DXA = 1 inch. 1 pt = 20 DXA.

---

## Page Layout

| Property | Value | Notes |
|---|---|---|
| Paper size | US Letter | 12240 × 15840 DXA |
| Top margin | 1080 DXA | 0.75 inch |
| Bottom margin | 1080 DXA | 0.75 inch |
| Left margin | 1080 DXA | 0.75 inch |
| Right margin | 1080 DXA | 0.75 inch |
| Header distance | 720 DXA | 0.5 inch |
| Footer distance | 720 DXA | 0.5 inch |
| Content width | 10080 DXA | 12240 − 2160 |

> **Margin note (2026-06-02):** The example CVs use 1-inch margins; 0.75 inch is a
> deliberate choice (within the accepted 0.5-1 inch resume range) to widen lines
> (fewer bullet wraps) and add vertical room (lower page-count risk) without
> breaking norms. The `cv_qc.py` length-guard constants and the `cv-structure.md`
> calibration constants are calibrated to this 0.75-inch geometry.

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
| Within-role thematic subheading | Calibri (minorHAnsi theme) | 22 | 11 | Yes | Black |
| Earlier Professional Roles entries | Calibri (minorHAnsi theme) | 22 | 11 | No | Black |

> **Note:** Section headers must be mixed case bold, never ALL CAPS.
>
> **Earlier Professional Roles render as plain 11pt black lines** (`Company | Title | Dates`), identical in typography to body text. The blue Calibri-Light `SectionHeading` and 9pt all-caps `Subsection` styles a prior version of this spec documented do **not** appear in any example CV and are not used (confirmed 2026-06-02, `cv-render-build-2026-06`).

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
| Within-role thematic subheading | 120 | 6 |
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
| Bullet character | • (round bullet, Symbol font code U+F0B7) |
| Bullet glyph font | Symbol |
| Bullet glyph size | 20 half-pts (10pt) |
| Indent left | 360 DXA (0.25 inch) |
| Hanging indent | 360 DXA (0.25 inch) |
| Bullet text font / size | Calibri 11pt |

**Implementation: a native Word list, not a literal bullet character.** Bullets
render as a real bulleted list (`numPr` referencing a numbering definition), not
by prepending a bullet-character text run to the paragraph. The list definition
(`abstractNum`) carries the glyph (round bullet, Symbol font code U+F0B7, 10pt),
the `bullet` numbering format, and the 360/360 indent; each bullet paragraph
references it via `numPr`. The hanging indent puts a 0.25-inch gap between the
glyph and the text, which starts at a tab stop at the left indent.

`scripts/cv_to_docx.py` (`_ensure_bullet_numbering` + `_set_numbering`) injects
one such definition into the document's numbering part and references it from
every bullet paragraph. One indent (360/360) is used for all bulleted lists.

**Bulleted sections.** These sections render every content line as a bullet:
Professional Experience (role bullets), Core Competencies (one bullet per zone),
Earlier Professional Roles, Education, Certifications & Training, Professional
Affiliations, Technical Proficiencies, and the description lines of Selected
Projects. The Professional Summary is prose (never bulleted); company / role
header lines and the Selected Projects project-name line are headers, not
bullets.

---

## Footer

A centered page-number footer appears on every page (present in the example
CVs). Live Word fields, so the count updates as content changes.

| Property | Value |
|---|---|
| Content | `Page <PAGE> of <NUMPAGES>` (live fields) |
| Alignment | Center |
| Font | Calibri 10pt |
| Footer distance | 720 DXA (0.5 inch) |

## Earlier Professional Roles rendering

Plain 11pt black `Company | Title | Dates` lines, identical typography to body
text. No bullets, no descriptions, no special color or case. The blue
Calibri-Light `SectionHeading` and 9pt all-caps `Subsection` styles documented
in an earlier version of this spec are **not used** (they appear in no example
CV; confirmed 2026-06-02, `cv-render-build-2026-06`).

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

Section order is governed by `rules/cv/cv-structure.md`. This spec does not define or default section order; it covers .docx rendering only.

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
| Section header case | Mixed case bold; **never ALL CAPS** |
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
