---
name: cv-render
description: Render a targeted CV to a formatted .docx. Reads the cv_content.md that the cv-targeted skill produced and renders it to a Word document matching the CV format spec (Calibri 11pt, native middle-dot bullets, US Letter / 1-inch margins, centered name and contact, page-number footer). Carries no judgment - it does not rewrite, re-order, or re-cite; cv_content.md is the sole input and its citation comments are stripped. Run after cv-targeted; the render is the final step of the CV pipeline.
---

# cv-render - render the targeted CV to a .docx

Renders `personal/applications/<SLUG>_APP-NNN_YYYY-MM/cv_content.md` (the
cv-targeted handoff) to a formatted `.docx` in the same folder. The render is
mechanical: `scripts/cv_to_docx.py` parses the markdown, strips the
`<!-- src: ... -->` / `<!-- cr: ... -->` citation comments, and applies the
formatting in `design/format_spec.md`. This skill adds no content judgment - it
does not rewrite, re-order, re-cite, or trim. `cv_content.md` is the sole input.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- User-facing status and prompts use plain English. No raw script internals.
- The script is the single source of formatting truth (it encodes
  `format_spec.md`); this skill resolves paths, runs it, and reports.

## Phase 0 - Intro

**Introducing the cv-render skill.**

- Run `python scripts/display/introduce.py cv-render` and show the output.

## Phase 1 - Locate the input

**Finding the CV content artifact for this application.**

- Ask for the APP-NNN. Locate the matching folder under
  `personal/applications/` (the folder name is `<SLUG>_APP-NNN_YYYY-MM`).
- Probe and land (first match wins):
  1. Folder missing - halt; APP-NNN likely wrong. Ask for APP-NNN again.
  2. `cv_content.md` missing - halt; direct the user to run `/cv-targeted`
     (the render has nothing to render without it).
  3. `cv_content.md` present - proceed.

## Phase 2 - Resolve the output filename

**Naming the output document.**

- Build the default output filename per `design/format_spec.md`:
  `<LastName>_CV_<Company>_<AbbreviatedRole>_<YYYY-MM>.docx`, where:
  - `LastName` is the candidate's surname from the contact block in
    `personal/profile/user-info.md` (e.g. `Delosh`). Surname only, not the full
    name and not initials.
  - `Company` and the role come from `## Company` / `## Role` in the
    application's `research.md`; abbreviate the role to a short token
    (e.g. "Associate Director, Operational Excellence" -> `AssocOpExDir`).
  - `YYYY-MM` is the application folder's `ym`.
- Present the proposed filename and ask the user to confirm or override it. The
  output path is `<application folder>/<confirmed filename>`.

## Phase 3 - Render

**Rendering the .docx.**

- Run:
  `python scripts/cv_to_docx.py --cv-file <application folder>/cv_content.md
  --out <application folder>/<confirmed filename>`
- A non-zero exit is a script error: halt per `global-rules.md` and surface the
  message; do not silently retry.

## Phase 4 - Handoff

**Confirming the render and handing off.**

- Report the output path.
- State the pagination caveat plainly: markdown has no geometry, so the true
  page count is only knowable once rendered. The cv-targeted length guard was a
  conservative estimate; the user should open the `.docx` in Word to confirm the
  final page count, and if it exceeds the level's page ceiling, re-run
  `/cv-targeted` to trim (content edits belong to that skill, not this one).
- End the run. This skill produces the formatted document only.

## Phase routing on failure

| Finding | Action |
|---|---|
| Application folder missing | Halt; ask for APP-NNN again |
| `cv_content.md` missing | Halt; direct the user to run `/cv-targeted` |
| `cv_to_docx.py` non-zero exit (script error) | Halt per `global-rules.md`; surface the error; do not loop |
| Rendered page count over the level ceiling (seen on opening in Word) | Out of scope here; re-run `/cv-targeted` to trim content |
