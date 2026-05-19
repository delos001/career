#!/usr/bin/env python3
"""
axis_qc.py - mechanical QC and auto-fix for axis-builder value files

Runs the deterministic QC checks per rules/quality_control/qc-<axis>-builder.md
against a drafted value file. Auto-fixes are applied in place where the fix
is purely textual (frontmatter shell + keys, title-suffix detection, Used-by
header, section order, Adjacency self-reference). Checks that need LLM
judgment to resolve (missing section content, missing adjacency bullets,
misdirected sibling edits, registry-filename mismatch, em-dash rewrites) are
reported but not fixed - the calling skill loops by re-entering the earlier
phase.

Output: a JSON object on stdout with per-check entries:
  { "checks": [ { "id": "A1", "passed": bool, "fixed": bool,
                  "detail": "<one-line explanation>" }, ... ] }
The calling skill aggregates with the judgment-check subagent's output to
build the final unresolved-issues list passed to axis_apply.py --issues.

Check groups:
  A1-A5  Frontmatter and metadata (auto-fix)
  B1-B3  Structural schema (B2 auto-fix; B1/B3 report)
  E1-E2  Adjacency completeness and self-reference (E2 auto-fix; E1 report)
  E4     (create mode) sibling-edits target Adjacency (report)
  G1     (create mode) registry entry filename matches value file (report)
  H2     Acronym list reconciles with body usage (report)
  I1     (create mode) value file does not yet exist (report)
  I2-I3  (refresh mode) value file exists, refresh has changes (report)

H1 (em dashes) is judgment-only and lives in the qc-industry-builder subagent;
removing an em dash requires sentence rewriting, not substitution.

Author    : Jason Delosh
Created   : 2026-05-19
Project   : career
Usage     : python scripts/axis_qc.py <axis> <value> --mode create|refresh \
                --value-file <path> [--sibling-edits <path> --registry-entry <path>] \
                [--changes <path>]
Depends   : pyyaml (via _config)
"""

import argparse
import json
import os
import re
import sys

import _config
import _util
import axis_registry
import axis_utils


# ---------------------------------------------------------------------------
# Axis schema lookup
# Each axis has a schema block in config.yaml declaring its frontmatter key
# (e.g. 'industry'), required '## Section' headings in canonical order, and
# the 'Used by:' header consumers downstream expect.
# ---------------------------------------------------------------------------

def _axis_schema(cfg, axis):
    """Return the per-axis schema block from config (or raise if unknown)."""
    axes = cfg.get('axes', {})
    if axis not in axes:
        raise ValueError(f'axis not configured in config.yaml: {axis}')
    return axes[axis]


def _all_section_headings(text):
    """Return a list of every '## heading' in text, in document order."""
    return re.findall(r'(?m)^##[ ]+(.+?)[ \t]*$', text)


def _record(check_id, passed, fixed, detail):
    """Build one entry for the qc output report."""
    return {'id': check_id, 'passed': passed, 'fixed': fixed, 'detail': detail}


# ---------------------------------------------------------------------------
# Frontmatter mutation
# Provisional marking is consumed by axis_apply.py but the helper lives here
# so the QC layer can use _apply_provisional consistently for any in-line
# preview/test runs. apply also imports it from this module.
# ---------------------------------------------------------------------------

def _apply_provisional(text, issues):
    """Add provisional: true and provisional_issues: list to frontmatter.

    issues is a list of dicts with at minimum 'check' and 'detail' keys.
    Rendered as a YAML inline list of short {check, detail} maps so the field
    stays single-source and the file remains parseable.
    """
    frontmatter, body = axis_utils.split_frontmatter(text)
    if frontmatter is None:
        # No frontmatter at all; build one. Should not happen on a builder
        # output, but fail loud rather than silently skip.
        raise ValueError('cannot mark provisional: file has no frontmatter')
    # Build the issues YAML block. One issue per line under the key.
    issue_lines = []
    for issue in issues:
        check = issue.get('check', 'unknown')
        detail = issue.get('detail', '').replace('"', "'")
        issue_lines.append(f'  - check: "{check}"')
        issue_lines.append(f'    detail: "{detail}"')

    # Remove any existing provisional block so re-runs replace rather than stack.
    frontmatter = re.sub(
        r'(?m)^provisional:.*$\n(?:^  .*$\n)*',
        '',
        frontmatter,
    )
    frontmatter = re.sub(
        r'(?m)^provisional_issues:.*$\n(?:^  .*$\n)*',
        '',
        frontmatter,
    )

    # Insert just before the closing fence.
    insertion = 'provisional: true\nprovisional_issues:\n' + '\n'.join(issue_lines) + '\n'
    # Use the lambda form so any regex-special characters in the issue
    # text (backslashes, in particular) are treated as literals rather
    # than backreferences. Issue text comes from the LLM subagent and is
    # unpredictable; a bare 'insertion + r"\1"' replacement string would
    # let a stray '\1' or '\g' corrupt the YAML.
    frontmatter = re.sub(
        r'(---\n)$',
        lambda m: insertion + m.group(1),
        frontmatter,
        count=1,
    )
    return frontmatter + body


# ---------------------------------------------------------------------------
# Build-issues log
# Provisional builds append a record to design/build_issues.md so dev can
# triage later. One Markdown section per build run.
# ---------------------------------------------------------------------------

def _append_build_issues(repo_root, cfg, axis, value, mode, issues):
    """Append a provisional-build record to design/build_issues.md."""
    log_path = os.path.join(
        repo_root, cfg['paths']['design'], cfg['filenames']['build_issues_log'])

    # Header on first write so the file is self-describing.
    if not os.path.exists(log_path):
        header = (
            '# Build Issues\n\n'
            'Auto-appended log of unresolved QC issues from axis-builder runs '
            'that completed in provisional mode. Each section is one build '
            'run. Triage and address; remove the section when the underlying '
            'value file no longer carries `provisional: true`.\n\n'
        )
        _util.write(log_path, header)

    ts = _util.today_iso()
    lines = [f'## {ts} - {axis}-builder {mode} - {value}', '']
    for issue in issues:
        check = issue.get('check', 'unknown')
        detail = issue.get('detail', '').strip()
        attempted = issue.get('attempted', '').strip()
        lines.append(f'- **{check}**: {detail}')
        if attempted:
            lines.append(f'  - Tried: {attempted}')
    lines.append('')

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    return log_path


# ---------------------------------------------------------------------------
# Check group A - Frontmatter and metadata
# A1-A5 verify the YAML frontmatter block, the canonical title line, and the
# 'Used by:' header that downstream skills parse. Each check returns a fix
# applied in place when the correction is purely textual (key insertion,
# value substitution, header rewrite).
# ---------------------------------------------------------------------------

def _check_a1_frontmatter_present(text):
    """A1: frontmatter present and bounded by --- fences at top.

    Auto-fix when missing: insert an empty '---\\n---\\n' shell. A2 and A3 then
    populate the required keys via their normal insert-before-closing-fence
    path, so the end state is a fully populated frontmatter and every check
    in the A group reports honestly.
    """
    fm, _ = axis_utils.split_frontmatter(text)
    if fm is not None:
        return text, _record('A1', True, False, 'frontmatter present')
    new_text = '---\n---\n' + text
    return new_text, _record('A1', True, True, 'inserted empty frontmatter shell')


def _check_a2_frontmatter_key(text, axis_key, value):
    """A2: frontmatter has '<axis_key>: <value>'. A1 guarantees fm exists."""
    fm, body = axis_utils.split_frontmatter(text)
    pattern = re.compile(r'(?m)^' + re.escape(axis_key) + r':[ \t]+(.+)$')
    m = pattern.search(fm)
    if m and m.group(1).strip() == value:
        return text, _record('A2', True, False, f'{axis_key} matches value')
    new_line = f'{axis_key}: {value}'
    if m:
        new_fm = pattern.sub(new_line, fm)
    else:
        # Insert before the closing fence (same idiom A3 uses).
        new_fm = re.sub(r'(---\n)$', new_line + '\n' + r'\1', fm, count=1)
    return new_fm + body, _record('A2', True, True, f'corrected {axis_key} to {value}')


def _check_a3_last_researched(text):
    """A3: last_researched is the current YYYY-MM. A1 guarantees fm exists."""
    fm, body = axis_utils.split_frontmatter(text)
    current = _util.today_ym()
    pattern = re.compile(r'(?m)^last_researched:[ \t]+(.+)$')
    m = pattern.search(fm)
    if m and m.group(1).strip() == current:
        return text, _record('A3', True, False, f'last_researched is {current}')
    new_line = f'last_researched: {current}'
    if m:
        new_fm = pattern.sub(new_line, fm)
    else:
        # Insert before closing fence.
        new_fm = re.sub(r'(---\n)$', new_line + '\n' + r'\1', fm, count=1)
    return new_fm + body, _record('A3', True, True, f'set last_researched to {current}')


def _check_a4_title(text, value):
    """A4: a top-level title exists and ends with '- CV Framing Rules'.

    Case-insensitive on the trailing fixed phrase. The display form of the
    value (CRO vs Cro vs cro) is the drafter's responsibility; the script
    neither enforces nor seeds capitalization, since most casing decisions
    are judgment calls (initialisms, acronyms, brand forms). When the
    title is absent, A4 fails and Phase 5 routes the failure to Phase 3
    redraft.
    """
    _, body = axis_utils.split_frontmatter(text)
    # Title is the first '# ' line in the body.
    title_pattern = re.compile(r'(?m)^#[ ]+(.+)$')
    m = title_pattern.search(body)
    suffix_pattern = re.compile(r'-[ \t]+CV Framing Rules[ \t]*$', re.IGNORECASE)
    if m and suffix_pattern.search(m.group(1)):
        return text, _record('A4', True, False, 'title present with expected suffix')
    if m:
        return text, _record('A4', False, False,
                             "title present but does not end with '- CV Framing Rules'")
    return text, _record('A4', False, False, 'no title line found')


def _check_a5_used_by(text, used_by_line):
    """A5: '**Used by:** <consumers>' present right after the title."""
    fm, body = axis_utils.split_frontmatter(text)
    fm = fm or ''
    expected = f'**Used by:** {used_by_line}'
    pattern = re.compile(r'(?m)^\*\*Used by:\*\*[ \t]+(.+)$')
    m = pattern.search(body)
    if m and m.group(1).strip() == used_by_line:
        return text, _record('A5', True, False, 'Used by header matches')
    if m:
        new_body = body[:m.start()] + expected + body[m.end():]
        return fm + new_body, _record('A5', True, True, f'corrected Used by to: {used_by_line}')
    # Insert after the title line. Normalize the surrounding whitespace so
    # the result is always 'title\n\n**Used by:** ...\n\n<rest>', regardless
    # of whether the original had a blank line after the title or not.
    title_match = re.search(r'(?m)^#[ ]+.+$', body)
    if not title_match:
        return text, _record('A5', False, False, 'cannot insert Used by: no title found')
    insert_at = title_match.end()
    following = body[insert_at:].lstrip('\n')
    new_body = body[:insert_at] + '\n\n' + expected + '\n\n' + following
    return fm + new_body, _record('A5', True, True, f'inserted Used by: {used_by_line}')


# ---------------------------------------------------------------------------
# Check group B - Structural schema
# B1-B3 verify the value file has exactly the required section headings (per
# the per-axis schema in config.yaml) in canonical order, each with non-blank
# content. B2 auto-fixes order by extracting and rebuilding sections; B1 and
# B3 report failures because adding or removing whole sections requires LLM
# judgment that lives in the calling skill's redraft loop.
# ---------------------------------------------------------------------------

def _check_b1_sections_present(text, required_sections):
    """B1: every required section heading is present and has non-blank content."""
    headings = _all_section_headings(text)
    missing = [s for s in required_sections if s not in headings]
    if missing:
        return text, _record('B1', False, False,
                             f'missing section(s): {", ".join(missing)}')
    # Each present section must have non-blank content.
    empty = []
    for section in required_sections:
        try:
            start, end = axis_utils.find_section_bounds(text, section)
            if not text[start:end].strip():
                empty.append(section)
        except ValueError:
            empty.append(section)
    if empty:
        return text, _record('B1', False, False,
                             f'empty section(s): {", ".join(empty)}')
    return text, _record('B1', True, False, 'all required sections present and non-empty')


def _check_b2_section_order(text, required_sections):
    """B2: required sections appear in canonical order. Auto-fix by reordering."""
    headings = _all_section_headings(text)
    present_required = [h for h in headings if h in required_sections]
    expected_order = [s for s in required_sections if s in headings]
    if present_required == expected_order:
        return text, _record('B2', True, False, 'section order matches')
    # Auto-fix: extract each required section, rebuild in canonical order, keep
    # any non-required sections at the end (B3 catches those separately).
    fm, body = axis_utils.split_frontmatter(text)
    fm = fm or ''
    # Locate the title + Used by prefix so we can preserve it.
    prefix_end = 0
    used_by_match = re.search(r'(?m)^\*\*Used by:\*\*.+$', body)
    if used_by_match:
        prefix_end = used_by_match.end()
        # Include trailing blank line(s) up to first section.
        first_section_match = re.search(r'(?m)^##[ ]', body)
        if first_section_match:
            prefix_end = first_section_match.start()
    prefix = body[:prefix_end]

    # Extract each section's full text (heading + body).
    sections = {}
    extras = []
    pattern = re.compile(r'(?m)(^##[ ]+(.+?)[ \t]*\n.*?)(?=^##[ ]|\Z)', re.DOTALL)
    for m in pattern.finditer(body):
        heading = m.group(2).strip()
        if heading in required_sections:
            sections[heading] = m.group(1).rstrip() + '\n\n'
        else:
            extras.append(m.group(1).rstrip() + '\n\n')

    reordered = prefix.rstrip() + '\n\n'
    for section_name in required_sections:
        if section_name in sections:
            reordered += sections[section_name]
    for extra in extras:
        reordered += extra
    return fm + reordered, _record('B2', True, True, 'reordered sections to canonical order')


def _check_b3_no_extra_sections(text, required_sections):
    """B3: no '## ' sections outside the required set."""
    headings = _all_section_headings(text)
    extras = [h for h in headings if h not in required_sections]
    if not extras:
        return text, _record('B3', True, False, 'no extra sections')
    return text, _record('B3', False, False,
                         f'extra section(s): {", ".join(extras)}')


# ---------------------------------------------------------------------------
# Check group E - Adjacency completeness
# E1 checks the new file references every file-backed sibling. E2 removes a
# self-reference if present. E4 (create only) verifies sibling-edits target
# the Adjacency section rather than another section. E3 (sibling-voice
# phrasing) is judgment-only and lives in the qc-industry-builder subagent.
# ---------------------------------------------------------------------------

def _check_e1_adjacency_complete(text, value, registry_path):
    """E1: Adjacency has one bullet per non-self registry entry.

    Includes file-backed, file-deferred, and registry-only siblings - the
    Adjacency section enumerates every other axis value so a candidate can
    translate between any pair. The reconciler still drafts back-edges only
    into file-backed siblings (the other states have no file to edit); E1
    just enforces completeness of the new file's own Adjacency.
    """
    try:
        body_start, body_end = axis_utils.find_section_bounds(text, 'Adjacency')
    except ValueError:
        return text, _record('E1', False, False, 'no Adjacency section')
    adjacency_body = text[body_start:body_end]
    if not os.path.exists(registry_path):
        return text, _record('E1', False, False, f'registry missing: {registry_path}')
    registry_text = _util.read(registry_path)
    siblings = []
    for m in axis_registry.BULLET_RE.finditer(registry_text):
        sibling_value = m.group('value').strip()
        if sibling_value == value:
            continue
        siblings.append(sibling_value)
    missing = []
    for sibling in siblings:
        # A bullet referencing the sibling has '- **<sibling>**' near its start.
        if not re.search(r'^- \*\*' + re.escape(sibling) + r'\*\*', adjacency_body, re.MULTILINE):
            missing.append(sibling)
    if missing:
        return text, _record('E1', False, False,
                             f'Adjacency missing sibling(s): {", ".join(missing)}')
    return text, _record('E1', True, False, 'Adjacency covers all non-self registry entries')


def _check_e2_no_self_reference(text, value):
    """E2: Adjacency does not reference the value being built."""
    try:
        body_start, body_end = axis_utils.find_section_bounds(text, 'Adjacency')
    except ValueError:
        return text, _record('E2', True, False, 'no Adjacency section to check')
    adjacency_body = text[body_start:body_end]
    pattern = re.compile(r'^- \*\*' + re.escape(value) + r'\*\*.*$\n?', re.MULTILINE)
    if not pattern.search(adjacency_body):
        return text, _record('E2', True, False, 'no self-reference')
    new_adjacency = pattern.sub('', adjacency_body)
    new_text = text[:body_start] + new_adjacency + text[body_end:]
    return new_text, _record('E2', True, True, f'removed self-reference to {value}')


def _check_e4_sibling_edits_targeting(sibling_edits):
    """E4 (create only): every sibling-edit targets the Adjacency section."""
    bad = [e for e in sibling_edits if e.get('section', 'Adjacency') != 'Adjacency']
    if not bad:
        return _record('E4', True, False, 'all sibling edits target Adjacency')
    return _record('E4', False, False,
                   f'{len(bad)} sibling edit(s) target non-Adjacency sections')


# ---------------------------------------------------------------------------
# Check group G - Registry alignment
# G1 (create only) verifies the registry entry text the calling skill drafted
# names the same filename the script will write. G2 (description matches file
# scope) is judgment-only and lives in the qc-industry-builder subagent.
# ---------------------------------------------------------------------------

def _check_g1_registry_entry_filename(registry_entry_text, expected_filename):
    """G1 (create only): registry entry's 'File: ...' names the actual filename."""
    m = re.search(r'File:\s+`?([\w\-.]+\.md)`?', registry_entry_text)
    if not m:
        return _record('G1', False, False, 'registry entry text has no File: clause')
    if m.group(1) == expected_filename:
        return _record('G1', True, False, f'registry entry names {expected_filename}')
    return _record('G1', False, False,
                   f'registry entry names {m.group(1)}; expected {expected_filename}')


# ---------------------------------------------------------------------------
# Check group H - Voice and style
# H1 (em dashes) is a subagent judgment check. Removing an em dash requires
# rewriting the surrounding sentence, not substitution; the script previously
# enforced H1 with a regex that corrupted '---' fences and adjacent content.
# H1 now lives in the qc-industry-builder subagent and routes failures to
# Phase 3 redraft.
#
# H2 (acronym list reconciliation) is script-owned as of 2026-05. The check
# is deterministic regex extraction in both directions (acronyms used in
# body but absent from the Dialect list, and listed acronyms unused in the
# body). Report-only in both directions; the drafter resolves either case
# in Phase 3 redraft. Moved from the subagent after a generics-build run
# where the subagent oscillated across iterations catching different
# subsets of the same all-caps tokens each pass (resolves deferral
# 'qc-h2-acronym-reconciliation-should-be-mechanical').
# ---------------------------------------------------------------------------

# Acronym detection: alphabetic 2-6 char runs with at least 2 uppercase
# letters. Captures pure all-caps (ANDA, FDA, CFR), lowercase-prefix
# CamelCase (eCTD, eTMF, ePRO), and mid-CamelCase initialisms (QbD, SaMD,
# ADaM). Excludes single-uppercase tokens like Cmax and Tmax, which the
# spec ("any all-caps token 2-6 letters") does not target. Exclusion set
# covers: Roman numerals (II..XII); the 'CV' artifact from the canonical
# title suffix ('- CV Framing Rules'); cross-domain world acronyms that
# no industry file would reasonably catalog as industry-specific
# terminology (DNA, RNA, UN, EU, UK, USA, XML).
_ACRONYM_TOKEN_RE = re.compile(r'\b[A-Za-z]{2,6}\b')
_ACRONYM_EXCLUSIONS = frozenset({
    'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII',
    'CV',
    'DNA', 'RNA', 'UN', 'EU', 'UK', 'USA', 'XML',
})


def _singular_acronym(tok):
    """Strip a lowercase 's' plural suffix from an all-caps acronym.

    Acronym plurals in body prose typically take a lowercase 's' (ANDAs,
    CROs, CRFs) while the Dialect catalog lists the singular (ANDA, CRO,
    CRF). Normalize both sides to singular for comparison so plurals do
    not surface as false H2 findings. Only triggered for tokens where the
    pre-'s' segment is entirely uppercase; mixed-case forms (eTMFs would
    map to eTMF) are left untouched since they are rarer and the regex
    treats them on their own merits.
    """
    if len(tok) >= 3 and tok.endswith('s') and tok[:-1].isupper():
        return tok[:-1]
    return tok


def _extract_acronyms(text):
    """Return the set of acronym-shaped tokens in text.

    A token is acronym-shaped when it is 2-6 alphabetic characters with at
    least 2 uppercase letters and is not in the hardcoded exclusion set.
    Used by H2 to compare body usage against the Dialect catalog.
    """
    found = set()
    for tok in _ACRONYM_TOKEN_RE.findall(text):
        if tok in _ACRONYM_EXCLUSIONS:
            continue
        if sum(1 for c in tok if c.isupper()) >= 2:
            found.add(tok)
    return found


def _check_h2_acronym_reconciliation(text):
    """H2: Dialect acronym list reconciles with body usage. Report-only.

    Extracts acronyms from:
      - the Dialect section's catalog (the content after the first ':' in
        the Dialect section body, treated as the list area)
      - the concatenated bodies of Vocabulary, Emphasis, and Adjacency
        (frontmatter, title, Used-by header, and Dialect prose excluded)

    Reports two directions:
      - in_body_not_listed: acronyms used in the body sections that the
        Dialect catalog does not name. Drafter adds to the list, rewrites
        to drop, or judges as a false positive in Phase 3.
      - in_list_not_in_body: acronyms in the catalog that no body section
        actually uses. Drafter prunes in Phase 3 (auto-fix deferred to a
        v2 that handles comma-list splicing safely).

    Both directions are report-only; the check passes when both sets are
    empty.
    """
    # Locate the Dialect section. If it is missing, B1 already flagged it
    # and H2 cannot evaluate meaningfully; report pass to avoid double-flagging.
    try:
        dialect_start, dialect_end = axis_utils.find_section_bounds(text, 'Dialect')
    except ValueError:
        return text, _record('H2', True, False, 'no Dialect section to check')
    dialect_body = text[dialect_start:dialect_end]

    # The Dialect catalog is the content after the first ':' in the section
    # body (matching the established pattern: optional prose intro, then
    # 'Acronyms recognized without expansion in <industry> hiring contexts: <list>').
    # When no colon exists, treat the whole section as the catalog.
    colon_idx = dialect_body.find(':')
    catalog_text = dialect_body[colon_idx + 1:] if colon_idx != -1 else dialect_body
    listed = _extract_acronyms(catalog_text)

    # Body scope: concatenate Vocabulary, Emphasis, Adjacency bodies. Each
    # may be absent (B1 will have flagged it); skip absent sections.
    body_text_parts = []
    for section in ('Vocabulary', 'Emphasis', 'Adjacency'):
        try:
            s, e = axis_utils.find_section_bounds(text, section)
        except ValueError:
            continue
        body_text_parts.append(text[s:e])
    body_used = _extract_acronyms('\n'.join(body_text_parts))

    # Normalize plurals so 'ANDAs' in body and 'ANDA' in catalog match.
    listed_norm = {_singular_acronym(t) for t in listed}
    body_norm = {_singular_acronym(t) for t in body_used}

    in_body_not_listed = sorted(body_norm - listed_norm)
    in_list_not_in_body = sorted(listed_norm - body_norm)

    if not in_body_not_listed and not in_list_not_in_body:
        return text, _record('H2', True, False,
                             'acronym list reconciles with body usage')

    parts = []
    if in_body_not_listed:
        parts.append('used in body but not listed: ' + ', '.join(in_body_not_listed))
    if in_list_not_in_body:
        parts.append('listed but unused in body: ' + ', '.join(in_list_not_in_body))
    return text, _record('H2', False, False, '; '.join(parts))


# ---------------------------------------------------------------------------
# Check group I - Mode invariants
# I1/I2 verify the on-disk state agrees with the requested mode (create
# against a missing file, refresh against an existing file). I3 (refresh
# only) verifies the refresh actually produced changes; a no-op refresh
# wasted research effort and should be flagged.
# ---------------------------------------------------------------------------

def _check_i1_create_invariant(value_path):
    """I1 (create only): value file did not exist before the run.

    Note: by the time qc runs, the file content is in --value-file (a temp).
    The on-disk value file at value_path should not yet exist (axis_apply
    create will raise if it does). I1 is therefore the lookup-time invariant.
    """
    if not os.path.exists(value_path):
        return _record('I1', True, False, 'value file does not yet exist on disk')
    return _record('I1', False, False, f'value file already exists: {value_path}')


def _check_i2_refresh_invariant(value_path):
    """I2 (refresh only): value file existed before the run."""
    if os.path.exists(value_path):
        return _record('I2', True, False, 'value file exists on disk')
    return _record('I2', False, False, f'value file missing: {value_path}')


def _check_i3_refresh_has_changes(changes):
    """I3 (refresh only): at least one change is present in --changes."""
    if changes:
        return _record('I3', True, False, f'{len(changes)} change(s) present')
    return _record('I3', False, False, 'no changes in refresh run')


# ---------------------------------------------------------------------------
# QC orchestrator
# Runs each check group in order against the drafted value-file text. Auto-fix
# checks return mutated text; report-only checks return the text unchanged.
# Mode-specific checks (E4, G1, I1, I2, I3) run only when the matching inputs
# are present. The (possibly mutated) text is written back to --value-file so
# the calling skill picks up the auto-fixed draft for the next phase.
# ---------------------------------------------------------------------------

def run_qc(args, repo_root, cfg):
    """Run mechanical QC checks against --value-file and print a per-check JSON report.

    Auto-fix-capable checks mutate the file in place; report-only checks
    leave the file unchanged. Mode-specific checks (E4, G1, I1, I2, I3) run
    only when their matching inputs are present.
    """
    schema = _axis_schema(cfg, args.axis)
    axis_key = schema['frontmatter_key']
    required_sections = schema['required_sections']
    used_by_line = schema['used_by']

    text = _util.read(args.value_file)
    checks = []

    # --- Group A: frontmatter and metadata (auto-fix) ---
    text, rec = _check_a1_frontmatter_present(text); checks.append(rec)
    text, rec = _check_a2_frontmatter_key(text, axis_key, args.value); checks.append(rec)
    text, rec = _check_a3_last_researched(text); checks.append(rec)
    text, rec = _check_a4_title(text, args.value); checks.append(rec)
    text, rec = _check_a5_used_by(text, used_by_line); checks.append(rec)

    # --- Group B: structural schema (B2 auto-fix; B1/B3 report) ---
    text, rec = _check_b1_sections_present(text, required_sections); checks.append(rec)
    text, rec = _check_b2_section_order(text, required_sections); checks.append(rec)
    text, rec = _check_b3_no_extra_sections(text, required_sections); checks.append(rec)

    # --- Group E (mechanical): Adjacency completeness and self-reference ---
    reg_path = axis_utils.registry_path(repo_root, cfg, args.axis)
    text, rec = _check_e1_adjacency_complete(text, args.value, reg_path); checks.append(rec)
    text, rec = _check_e2_no_self_reference(text, args.value); checks.append(rec)

    # --- Group H (mechanical): acronym list reconciles with body usage ---
    text, rec = _check_h2_acronym_reconciliation(text); checks.append(rec)

    # --- Mode-specific: create runs E4 + G1 + I1; refresh runs I2 + I3 ---
    vf_path = axis_utils.value_file_path(repo_root, cfg, args.axis, f'{args.value}.md')
    if args.mode == 'create':
        checks.append(_check_i1_create_invariant(vf_path))
        # E4 (sibling-edits target Adjacency) and G1 (registry filename
        # matches value file) are required in create mode. Refuse to
        # silently skip them when their inputs are missing; the absent
        # input is itself the bug worth surfacing.
        if not args.sibling_edits:
            raise ValueError(
                'create mode requires --sibling-edits; '
                'refusing to skip the sibling-edits-target check silently'
            )
        sibling_edits = axis_utils.unwrap_list(
            _util.load_json(args.sibling_edits), 'sibling_edits')
        checks.append(_check_e4_sibling_edits_targeting(sibling_edits))
        if not args.registry_entry:
            raise ValueError(
                'create mode requires --registry-entry; '
                'refusing to skip the registry-filename check silently'
            )
        registry_entry_text = _util.read(args.registry_entry).strip()
        checks.append(_check_g1_registry_entry_filename(registry_entry_text, f'{args.value}.md'))
    elif args.mode == 'refresh':
        checks.append(_check_i2_refresh_invariant(vf_path))
        # I3 (no-op refresh detection) is required in refresh mode. Refuse
        # to silently skip it when --changes is missing; the absent input
        # is itself the bug worth surfacing.
        if not args.changes:
            raise ValueError(
                'refresh mode requires --changes (the reconciler change list); '
                'refusing to skip the no-op-refresh check silently'
            )
        changes = axis_utils.unwrap_list(_util.load_json(args.changes), 'changes')
        checks.append(_check_i3_refresh_has_changes(changes))

    # --- Persist the (possibly fixed) value-file text and emit the report ---
    _util.write(args.value_file, text)
    print(json.dumps({'checks': checks}))


# ---------------------------------------------------------------------------
# Cross-script helpers
# Other axis-builder scripts re-use _apply_provisional (axis_apply both
# create and refresh use it) and _check_g1_registry_entry_filename
# (axis_apply re-enforces G1 at the apply step). Expose at module scope.
# ---------------------------------------------------------------------------

apply_provisional = _apply_provisional
append_build_issues = _append_build_issues
check_g1_registry_entry_filename = _check_g1_registry_entry_filename


# ---------------------------------------------------------------------------
# Command-line entry point
# Single-purpose script: no subcommand. Required args: axis, value, --mode,
# --value-file. Mode-specific args: --sibling-edits / --registry-entry
# (create), --changes (refresh).
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, run QC, emit JSON report."""
    parser = argparse.ArgumentParser(
        description='axis-builder mechanical QC + auto-fix (Phase 5)')
    parser.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    parser.add_argument('value', help='registry key (e.g. generics)')
    parser.add_argument('--mode', required=True, choices=['create', 'refresh'])
    parser.add_argument(
        '--value-file', required=True,
        help='path to the drafted value-file Markdown; auto-fixes are written back in place')
    parser.add_argument(
        '--sibling-edits', default=None,
        help='path to the per-sibling Adjacency edits JSON (create mode)')
    parser.add_argument(
        '--registry-entry', default=None,
        help='path to the proposed registry entry text (create mode)')
    parser.add_argument(
        '--changes', default=None,
        help='path to the approved change list JSON (refresh mode)')

    args = parser.parse_args()

    # --- Dispatch ---
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        run_qc(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
