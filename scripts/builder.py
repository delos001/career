#!/usr/bin/env python3
"""
builder.py - axis-builder skill artifact assembler

Mechanical file operations for the per-axis builder skills (industry-builder,
specialty-builder, orientation-builder, level-builder, work-state-builder).
Four subcommands:

  lookup         Phase 1 - inspect a registry entry; return state + value-file
                 path so the builder can decide create vs refresh and refuse
                 incoherent invocations.
  qc             Phase 5 - run mechanical QC checks per
                 rules/quality_control/qc-<axis>-builder.md, apply auto-fixes
                 to the input file in place where the fix is purely
                 deterministic, and return a JSON per-check report so the
                 calling skill can dispatch the judgment-check subagent and
                 decide whether to loop.
  apply-create   Phase 6 (create path) - write a new value file, apply
                 per-sibling Adjacency back-edges, and update the registry
                 entry. Optional --provisional marks the file and logs unresolved
                 QC issues to design/build_issues.md.
  apply-refresh  Phase 6 (refresh path) - apply an approved change list to an
                 existing value file and bump last_researched. Optional
                 --provisional behaves identically to apply-create.

Nothing repo-dependent is hardcoded here. Folder locations and filenames come
from config.yaml (via _config). All writes are scoped: section-replace for
refresh, targeted bullet insertion for sibling back-edges, single-line swap
for the registry entry.

Author    : Jason Delosh
Created   : 2026-05-18
Project   : career
Usage     : python scripts/builder.py lookup <axis> <value>
            python scripts/builder.py qc <axis> <value> --mode create|refresh --value-file ... [--sibling-edits ... --registry-entry ...]
            python scripts/builder.py apply-create <axis> <value> --value-file ... --sibling-edits ... --registry-entry ... [--provisional --issues ...]
            python scripts/builder.py apply-refresh <axis> <value> --changes ... [--provisional --issues ...]
Depends   : pyyaml (via _config)
"""

import argparse
import datetime
import json
import os
import re
import sys

import _config


# ---------------------------------------------------------------------------
# Shared helpers
# Small utilities used by more than one subcommand: UTF-8 read/write, JSON
# input loading, section locating and editing, and frontmatter mutation.
# ---------------------------------------------------------------------------

def _read(path):
    """Read a UTF-8 text file and return its contents (raises if missing)."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _write(path, text):
    """Write text to a UTF-8 file, creating parent folders if they do not exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def _load_json(path):
    """Load a JSON file and return its parsed content."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _axis_dir(repo_root, cfg, axis):
    """Return the absolute path to rules/<axis>/."""
    return os.path.join(repo_root, cfg['paths']['rules'], axis)


def _registry_path(repo_root, cfg, axis):
    """Return the absolute path to rules/<axis>/registry.md."""
    return os.path.join(_axis_dir(repo_root, cfg, axis), cfg['filenames']['axis_registry'])


def _value_file_path(repo_root, cfg, axis, value_filename):
    """Return the absolute path to rules/<axis>/<value_filename>."""
    return os.path.join(_axis_dir(repo_root, cfg, axis), value_filename)


def _today_ym():
    """Return the current year-month as YYYY-MM."""
    return datetime.date.today().strftime('%Y-%m')


def _today_iso():
    """Return the current date as YYYY-MM-DD."""
    return datetime.date.today().strftime('%Y-%m-%d')


# ---------------------------------------------------------------------------
# Registry parsing
# The registry is a Markdown file with a frontmatter block and a bullet list
# under a # heading. Each bullet is one of:
#   - **<value>** - <description>. File: <name>.md.
#   - **<value>** - <description>. File deferred.
#   - **<value>** - <description>. Registry-only; <reason>.
# Parse loosely so minor whitespace variation does not break lookup.
# ---------------------------------------------------------------------------

# Regex: capture an axis-registry bullet's value name (the bolded token) and the
# rest of the line. The bullet starts with '- **<value>**' on its own line.
_BULLET_RE = re.compile(
    r'^- \*\*(?P<value>[^*]+)\*\*(?P<rest>.*)$',
    re.MULTILINE,
)


def _classify_bullet(rest_of_line):
    """Decide registry state from the text after the bolded value token.

    Returns (state, value_filename_or_None). State is one of
    'file-backed', 'file-deferred', 'registry-only'.
    """
    # File-backed entries name the file explicitly: 'File: <name>.md'.
    m = re.search(r'File:\s+`?([\w\-.]+\.md)`?', rest_of_line)
    if m:
        return 'file-backed', m.group(1)
    if re.search(r'File deferred', rest_of_line):
        return 'file-deferred', None
    if re.search(r'Registry-only', rest_of_line):
        return 'registry-only', None
    # Anything else is an unrecognised state; treat as registry-only with no
    # file so the caller halts rather than guessing.
    return 'registry-only', None


def _find_registry_entry(registry_text, value):
    """Locate a value's bullet in the registry.

    Returns (match_object, state, value_filename) if found; (None, None, None)
    if the value is not in the registry.
    """
    for m in _BULLET_RE.finditer(registry_text):
        if m.group('value').strip() == value:
            state, value_filename = _classify_bullet(m.group('rest'))
            return m, state, value_filename
    return None, None, None


# ---------------------------------------------------------------------------
# Section locating and editing
# Axis value files use '## <Heading>' sections. Sibling back-edges are
# inserted at the end of the target file's '## Adjacency' section. Refresh
# changes are applied within named sections.
# ---------------------------------------------------------------------------

def _find_section_bounds(text, heading):
    """Return (start, end) character offsets of a '## heading' section body.

    Body excludes the heading line itself; start is the offset just after the
    heading line's trailing newline; end is the offset of the next '## ' line
    or the end of file. Raises ValueError if the heading is absent.
    """
    pattern = re.compile(
        r'^##[ ]' + re.escape(heading) + r'[ \t]*\n',
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        raise ValueError(f'section not found: ## {heading}')
    body_start = m.end()
    next_heading = re.search(r'^##[ ]', text[body_start:], re.MULTILINE)
    body_end = body_start + next_heading.start() if next_heading else len(text)
    return body_start, body_end


def _insert_bullet_in_section(text, heading, bullet_text):
    """Append a bullet line at the end of a named section.

    The bullet is inserted just before the section-ending blank line (or just
    before the next '## ' heading if no trailing blank line). Preserves any
    existing trailing whitespace structure.
    """
    body_start, body_end = _find_section_bounds(text, heading)
    body = text[body_start:body_end]
    # Strip trailing whitespace/newlines from the body, append the bullet, then
    # add one trailing blank line so section separation is preserved.
    new_body = body.rstrip() + '\n' + bullet_text.rstrip() + '\n\n'
    return text[:body_start] + new_body + text[body_end:]


def _replace_in_section(text, heading, current_text, proposed_text):
    """Replace one occurrence of current_text within a named section.

    Used by refresh-mode 'modify' changes. Raises if the current text is not
    found in the section (the QC loop should not produce a modify pointing at
    text that does not exist).
    """
    body_start, body_end = _find_section_bounds(text, heading)
    body = text[body_start:body_end]
    if current_text not in body:
        raise ValueError(
            f"refresh 'modify' current text not found in section ## {heading}")
    new_body = body.replace(current_text, proposed_text, 1)
    return text[:body_start] + new_body + text[body_end:]


def _remove_in_section(text, heading, current_text):
    """Remove one occurrence of current_text within a named section."""
    body_start, body_end = _find_section_bounds(text, heading)
    body = text[body_start:body_end]
    if current_text not in body:
        raise ValueError(
            f"refresh 'remove' current text not found in section ## {heading}")
    new_body = body.replace(current_text, '', 1)
    return text[:body_start] + new_body + text[body_end:]


def _add_to_section(text, heading, proposed_text):
    """Append proposed_text to the end of a named section.

    Used by refresh-mode 'add' changes that are not bullet-form back-edges.
    """
    body_start, body_end = _find_section_bounds(text, heading)
    body = text[body_start:body_end]
    new_body = body.rstrip() + '\n\n' + proposed_text.rstrip() + '\n\n'
    return text[:body_start] + new_body + text[body_end:]


# ---------------------------------------------------------------------------
# Frontmatter mutation
# Both apply-create and apply-refresh may add a provisional flag and an
# issues list to a file's YAML frontmatter. apply-refresh also bumps
# last_researched. Frontmatter is a simple key: value block between two
# '---' lines at the top of the file; we edit line-by-line rather than
# round-tripping YAML to preserve whatever formatting the file already has.
# ---------------------------------------------------------------------------

def _split_frontmatter(text):
    """Return (frontmatter_block_with_fences, body) or (None, text) if absent.

    Frontmatter is recognized as the text from the first '---' line to the
    next '---' line, inclusive of both fences.
    """
    if not text.startswith('---\n'):
        return None, text
    # Find the closing fence.
    rest = text[4:]
    m = re.search(r'^---\n', rest, re.MULTILINE)
    if not m:
        return None, text
    end = 4 + m.end()
    return text[:end], text[end:]


def _set_frontmatter_field(frontmatter, key, value):
    """Set a single key: value line in a frontmatter block.

    If the key exists, replace its line; otherwise insert before the closing
    fence. Preserves all other lines.
    """
    pattern = re.compile(r'(?m)^' + re.escape(key) + r':[ \t].*$')
    new_line = f'{key}: {value}'
    if pattern.search(frontmatter):
        return pattern.sub(new_line, frontmatter)
    # Insert just before the closing '---' fence.
    return frontmatter.replace('---\n', new_line + '\n---\n', 1).replace(
        # That replaces the *first* fence; undo by replacing the opening fence
        # back. Cleaner approach: split, append, rejoin.
        new_line + '\n---\n', '---\n', 1)


def _apply_provisional(text, issues):
    """Add provisional: true and provisional_issues: list to frontmatter.

    issues is a list of dicts with at minimum 'check' and 'detail' keys.
    Rendered as a YAML inline list of short {check, detail} maps so the field
    stays single-source and the file remains parseable.
    """
    frontmatter, body = _split_frontmatter(text)
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
    # The closing fence is the second '---\n' in the frontmatter block.
    frontmatter = re.sub(
        r'(---\n)$',
        insertion + r'\1',
        frontmatter,
        count=1,
    )
    return frontmatter + body


def _bump_last_researched(text, ym):
    """Update last_researched: <YYYY-MM> in frontmatter."""
    frontmatter, body = _split_frontmatter(text)
    if frontmatter is None:
        raise ValueError('cannot bump last_researched: file has no frontmatter')
    new_frontmatter = re.sub(
        r'(?m)^last_researched:[ \t].*$',
        f'last_researched: {ym}',
        frontmatter,
    )
    return new_frontmatter + body


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
        _write(log_path, header)

    ts = _today_iso()
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
# Subcommand: lookup
# Inspect a registry entry; return state + value-file path. JSON output so
# the calling skill can parse a single line reliably.
# ---------------------------------------------------------------------------

def cmd_lookup(args, repo_root, cfg):
    registry_path = _registry_path(repo_root, cfg, args.axis)
    if not os.path.exists(registry_path):
        raise FileNotFoundError(f'registry not found: {registry_path}')
    text = _read(registry_path)
    _, state, value_filename = _find_registry_entry(text, args.value)
    if state is None:
        result = {
            'value': args.value,
            'state': 'not-in-registry',
            'value_file_path': None,
        }
    else:
        value_file_path = (
            _value_file_path(repo_root, cfg, args.axis, value_filename)
            if value_filename else None
        )
        result = {
            'value': args.value,
            'state': state,
            'value_file_path': value_file_path,
        }
    print(json.dumps(result))


# ---------------------------------------------------------------------------
# Subcommand: qc
# Mechanical QC per rules/quality_control/qc-<axis>-builder.md. Runs the
# checks the script can verify deterministically and applies auto-fixes
# in place where the fix is purely textual (em dashes, frontmatter keys,
# title line, section order, Adjacency self-reference). Checks that need
# LLM judgment to fix (missing section content, missing adjacency bullets,
# misdirected sibling edits, registry-filename mismatch) are reported but
# not fixed - the calling skill loops by re-entering the earlier phase.
#
# Output: a JSON object on stdout with per-check entries:
#   { "checks": [ { "id": "A1", "passed": bool, "fixed": bool,
#                   "detail": "<one-line explanation>" }, ... ] }
# The calling skill aggregates with the judgment-check subagent's output
# to build the final unresolved-issues list passed to apply-* --issues.
# ---------------------------------------------------------------------------

# Regex: em dash detection. U+2014 is the literal character; double-hyphen ('--')
# is conventionally rendered as an em dash and is also caught.
_EM_DASH_RE = re.compile(r'—|--')


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
# Check group A - Frontmatter and metadata
# A1-A5 verify the YAML frontmatter block, the canonical title line, and the
# 'Used by:' header that downstream skills parse. Each check returns a fix
# applied in place when the correction is purely textual (key insertion,
# value substitution, header rewrite).
# ---------------------------------------------------------------------------

def _check_a1_frontmatter_present(text):
    """A1: frontmatter present and bounded by --- fences at top."""
    fm, _ = _split_frontmatter(text)
    if fm is not None:
        return text, _record('A1', True, False, 'frontmatter present')
    # Auto-fix: cannot synthesize frontmatter without knowing all required keys;
    # leave to A2/A3 to populate keys after the missing frontmatter is reported.
    return text, _record('A1', False, False, 'frontmatter block missing')


def _check_a2_frontmatter_key(text, axis_key, value):
    """A2: frontmatter has '<axis_key>: <value>'."""
    fm, body = _split_frontmatter(text)
    if fm is None:
        # Build a minimal frontmatter so subsequent checks have something to fix.
        fm = f'---\n{axis_key}: {value}\nlast_researched: {_today_ym()}\n---\n'
        return fm + body, _record('A2', True, True, f'inserted {axis_key}: {value}')
    pattern = re.compile(r'(?m)^' + re.escape(axis_key) + r':[ \t]+(.+)$')
    m = pattern.search(fm)
    if m and m.group(1).strip() == value:
        return text, _record('A2', True, False, f'{axis_key} matches value')
    new_line = f'{axis_key}: {value}'
    if m:
        new_fm = pattern.sub(new_line, fm)
    else:
        new_fm = fm.replace('---\n', new_line + '\n', 1).replace(new_line + '\n', '---\n' + new_line + '\n', 1)
    return new_fm + body, _record('A2', True, True, f'corrected {axis_key} to {value}')


def _check_a3_last_researched(text):
    """A3: last_researched is the current YYYY-MM."""
    fm, body = _split_frontmatter(text)
    if fm is None:
        return text, _record('A3', False, False, 'no frontmatter to verify last_researched')
    current = _today_ym()
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
    """A4: title line is '# <Value> - CV Framing Rules'."""
    _, body = _split_frontmatter(text)
    # Title is the first '# ' line in the body.
    pattern = re.compile(r'(?m)^#[ ]+(.+)$')
    m = pattern.search(body)
    # Display name: convert value (kebab-case) to title case (med-device -> Med-Device).
    display = '-'.join(part.capitalize() for part in value.split('-'))
    expected = f'# {display} - CV Framing Rules'
    if m and m.group(0).strip() == expected:
        return text, _record('A4', True, False, 'title matches expected format')
    # Auto-fix: replace the first '# ...' line, or insert one if missing.
    fm, body2 = _split_frontmatter(text)
    fm = fm or ''
    if m:
        new_body = body2[:m.start()] + expected + body2[m.end():]
    else:
        # Insert title at the top of body with a trailing blank line.
        new_body = expected + '\n\n' + body2.lstrip()
    return fm + new_body, _record('A4', True, True, f'wrote title: {expected}')


def _check_a5_used_by(text, used_by_line):
    """A5: '**Used by:** <consumers>' present right after the title."""
    _, body = _split_frontmatter(text)
    expected = f'**Used by:** {used_by_line}'
    pattern = re.compile(r'(?m)^\*\*Used by:\*\*[ \t]+(.+)$')
    m = pattern.search(body)
    if m and m.group(1).strip() == used_by_line:
        return text, _record('A5', True, False, 'Used by header matches')
    fm, body2 = _split_frontmatter(text)
    fm = fm or ''
    if m:
        new_body = body2[:m.start()] + expected + body2[m.end():]
        return fm + new_body, _record('A5', True, True, f'corrected Used by to: {used_by_line}')
    # Insert after the title line.
    title_match = re.search(r'(?m)^#[ ]+.+$', body2)
    if not title_match:
        return text, _record('A5', False, False, 'cannot insert Used by: no title found')
    insert_at = title_match.end()
    new_body = body2[:insert_at] + '\n\n' + expected + body2[insert_at:]
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
            start, end = _find_section_bounds(text, section)
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
    fm, body = _split_frontmatter(text)
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

def _check_e1_adjacency_complete(text, axis_dir, value, registry_path):
    """E1: Adjacency has one bullet per file-backed sibling."""
    try:
        body_start, body_end = _find_section_bounds(text, 'Adjacency')
    except ValueError:
        return text, _record('E1', False, False, 'no Adjacency section')
    adjacency_body = text[body_start:body_end]
    # Collect siblings: every file-backed entry in the registry except self.
    if not os.path.exists(registry_path):
        return text, _record('E1', False, False, f'registry missing: {registry_path}')
    registry_text = _read(registry_path)
    siblings = []
    for m in _BULLET_RE.finditer(registry_text):
        sibling_value = m.group('value').strip()
        if sibling_value == value:
            continue
        state, value_filename = _classify_bullet(m.group('rest'))
        if state == 'file-backed':
            siblings.append(sibling_value)
    missing = []
    for sibling in siblings:
        # A bullet referencing the sibling has '- **<sibling>**' near its start.
        if not re.search(r'^- \*\*' + re.escape(sibling) + r'\*\*', adjacency_body, re.MULTILINE):
            missing.append(sibling)
    if missing:
        return text, _record('E1', False, False,
                             f'Adjacency missing sibling(s): {", ".join(missing)}')
    return text, _record('E1', True, False, 'Adjacency covers all file-backed siblings')


def _check_e2_no_self_reference(text, value):
    """E2: Adjacency does not reference the value being built."""
    try:
        body_start, body_end = _find_section_bounds(text, 'Adjacency')
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
# Check group H - Voice and style (mechanical only)
# H1 strips em dashes per the em_dash_scope rule (axis files are products, not
# design docs). H2 (acronym list reconciliation) is left to the subagent
# because reliable acronym detection in prose requires context-sensitive
# disambiguation that the script cannot do well.
# ---------------------------------------------------------------------------

def _check_h1_no_em_dashes(text):
    """H1: no em dashes (U+2014 or '--') in the file body. Auto-fix to hyphen."""
    if not _EM_DASH_RE.search(text):
        return text, _record('H1', True, False, 'no em dashes')
    new_text = _EM_DASH_RE.sub('-', text)
    return new_text, _record('H1', True, True, 'replaced em dashes with hyphens')


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
    The on-disk value file at value_path should not yet exist (apply-create
    will raise if it does). I1 is therefore the lookup-time invariant.
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


def cmd_qc(args, repo_root, cfg):
    schema = _axis_schema(cfg, args.axis)
    axis_key = schema['frontmatter_key']
    required_sections = schema['required_sections']
    used_by_line = schema['used_by']

    text = _read(args.value_file)
    checks = []

    # Run frontmatter and title/header checks with auto-fix.
    text, rec = _check_a1_frontmatter_present(text); checks.append(rec)
    text, rec = _check_a2_frontmatter_key(text, axis_key, args.value); checks.append(rec)
    text, rec = _check_a3_last_researched(text); checks.append(rec)
    text, rec = _check_a4_title(text, args.value); checks.append(rec)
    text, rec = _check_a5_used_by(text, used_by_line); checks.append(rec)

    # Structural checks.
    text, rec = _check_b1_sections_present(text, required_sections); checks.append(rec)
    text, rec = _check_b2_section_order(text, required_sections); checks.append(rec)
    text, rec = _check_b3_no_extra_sections(text, required_sections); checks.append(rec)

    # Adjacency mechanical checks.
    registry_path = _registry_path(repo_root, cfg, args.axis)
    axis_dir = _axis_dir(repo_root, cfg, args.axis)
    text, rec = _check_e1_adjacency_complete(text, axis_dir, args.value, registry_path); checks.append(rec)
    text, rec = _check_e2_no_self_reference(text, args.value); checks.append(rec)

    # Mode-specific.
    value_path = _value_file_path(repo_root, cfg, args.axis, f'{args.value}.md')
    if args.mode == 'create':
        checks.append(_check_i1_create_invariant(value_path))
        if args.sibling_edits:
            sibling_edits = _load_json(args.sibling_edits)
            checks.append(_check_e4_sibling_edits_targeting(sibling_edits))
        if args.registry_entry:
            registry_entry_text = _read(args.registry_entry).strip()
            checks.append(_check_g1_registry_entry_filename(registry_entry_text, f'{args.value}.md'))
    elif args.mode == 'refresh':
        checks.append(_check_i2_refresh_invariant(value_path))
        if args.changes:
            changes = _load_json(args.changes)
            checks.append(_check_i3_refresh_has_changes(changes))

    # Style auto-fix.
    text, rec = _check_h1_no_em_dashes(text); checks.append(rec)

    # Write back the (possibly fixed) value-file text.
    _write(args.value_file, text)
    print(json.dumps({'checks': checks}))


# ---------------------------------------------------------------------------
# Subcommand: apply-create
# Write the new value file, apply per-sibling Adjacency back-edges, replace
# the registry entry, and (optionally) mark provisional + log issues.
#
# Input file shapes:
#   --value-file       full Markdown text of the new value file.
#   --sibling-edits    JSON list of {"sibling_file": "<name>.md",
#                                    "section": "Adjacency",
#                                    "bullet": "- **<value>**: <translation>."}
#   --registry-entry   one-line Markdown bullet for the registry entry, e.g.
#                      "- **generics** - generic and 505(b)(2) ... File: generics.md."
#   --issues           JSON list of {"check": "...", "detail": "...",
#                                    "attempted": "..."} (provisional only)
# ---------------------------------------------------------------------------

def cmd_apply_create(args, repo_root, cfg):
    axis = args.axis
    value = args.value
    axis_dir = _axis_dir(repo_root, cfg, axis)
    registry_path = _registry_path(repo_root, cfg, axis)

    # Determine the value file's filename. Convention: <value>.md. The registry
    # entry must point to the same file. If a custom filename is ever needed,
    # introduce a --filename arg rather than parsing the registry-entry string
    # here.
    value_filename = f'{value}.md'
    value_path = _value_file_path(repo_root, cfg, axis, value_filename)

    if os.path.exists(value_path):
        raise FileExistsError(
            f'value file already exists: {value_path}. Use refresh, not create.')

    # Read inputs.
    value_text = _read(args.value_file)
    sibling_edits = _load_json(args.sibling_edits)
    registry_entry_line = _read(args.registry_entry).strip()

    # Apply provisional marking before writing if requested.
    written_paths = []
    if args.provisional:
        issues = _load_json(args.issues)
        value_text = _apply_provisional(value_text, issues)
        log_path = _append_build_issues(repo_root, cfg, axis, value, 'create', issues)
        written_paths.append(log_path)

    # Write the new value file.
    _write(value_path, value_text)
    written_paths.append(value_path)

    # Apply sibling Adjacency edits.
    for edit in sibling_edits:
        sibling_path = _value_file_path(repo_root, cfg, axis, edit['sibling_file'])
        if not os.path.exists(sibling_path):
            raise FileNotFoundError(f'sibling file missing: {sibling_path}')
        sibling_text = _read(sibling_path)
        sibling_text = _insert_bullet_in_section(
            sibling_text, edit.get('section', 'Adjacency'), edit['bullet'])
        _write(sibling_path, sibling_text)
        written_paths.append(sibling_path)

    # Update the registry: replace existing entry if present, append otherwise.
    registry_text = _read(registry_path)
    existing, _, _ = _find_registry_entry(registry_text, value)
    if existing:
        # Replace the matched bullet line (and only that line).
        line_start = registry_text.rfind('\n', 0, existing.start()) + 1
        line_end = registry_text.find('\n', existing.end())
        if line_end == -1:
            line_end = len(registry_text)
        registry_text = (
            registry_text[:line_start] + registry_entry_line + registry_text[line_end:])
    else:
        # Append as a new bullet at the end of the file, preserving trailing newline.
        if not registry_text.endswith('\n'):
            registry_text += '\n'
        registry_text += registry_entry_line + '\n'
    _write(registry_path, registry_text)
    written_paths.append(registry_path)

    # Print every path written so the calling skill can confirm.
    for p in written_paths:
        print(p)


# ---------------------------------------------------------------------------
# Subcommand: apply-refresh
# Apply an approved change list to an existing value file, bump
# last_researched, and (optionally) mark provisional + log issues.
#
# Input file shape:
#   --changes  JSON list of {"section": "<heading>",
#                            "type": "add" | "remove" | "modify",
#                            "current": "<existing text>" (remove/modify only),
#                            "proposed": "<new text>" (add/modify only)}
#   --issues   JSON list of {"check": "...", "detail": "...",
#                            "attempted": "..."} (provisional only)
# ---------------------------------------------------------------------------

def cmd_apply_refresh(args, repo_root, cfg):
    axis = args.axis
    value = args.value
    value_filename = f'{value}.md'
    value_path = _value_file_path(repo_root, cfg, axis, value_filename)

    if not os.path.exists(value_path):
        raise FileNotFoundError(
            f'value file missing: {value_path}. Use create, not refresh.')

    text = _read(value_path)
    changes = _load_json(args.changes)

    # Apply each change in declared order. Order matters for adjacent edits;
    # the caller is responsible for sequencing.
    for ch in changes:
        section = ch['section']
        change_type = ch['type']
        if change_type == 'add':
            text = _add_to_section(text, section, ch['proposed'])
        elif change_type == 'remove':
            text = _remove_in_section(text, section, ch['current'])
        elif change_type == 'modify':
            text = _replace_in_section(text, section, ch['current'], ch['proposed'])
        else:
            raise ValueError(f'unknown change type: {change_type}')

    # Bump last_researched even on a no-op refresh; the run happened.
    text = _bump_last_researched(text, _today_ym())

    written_paths = []
    if args.provisional:
        issues = _load_json(args.issues)
        text = _apply_provisional(text, issues)
        log_path = _append_build_issues(repo_root, cfg, axis, value, 'refresh', issues)
        written_paths.append(log_path)

    _write(value_path, text)
    written_paths.append(value_path)

    for p in written_paths:
        print(p)


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses subcommand and arguments, loads config, runs the subcommand, and
# reports failure to stderr with a non-zero exit so the calling skill halts
# per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='axis-builder artifact assembler')
    sub = parser.add_subparsers(dest='command', required=True)

    p_look = sub.add_parser('lookup', help='Phase 1: inspect a registry entry')
    p_look.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    p_look.add_argument('value', help='registry key (e.g. generics)')
    p_look.set_defaults(func=cmd_lookup)

    p_qc = sub.add_parser('qc', help='Phase 5: run mechanical QC + auto-fix on the drafted value file')
    p_qc.add_argument('axis')
    p_qc.add_argument('value')
    p_qc.add_argument('--mode', required=True, choices=['create', 'refresh'])
    p_qc.add_argument('--value-file', required=True,
                      help='path to the drafted value-file Markdown; auto-fixes are written back in place')
    p_qc.add_argument('--sibling-edits', default=None,
                      help='path to the per-sibling Adjacency edits JSON (create mode)')
    p_qc.add_argument('--registry-entry', default=None,
                      help='path to the proposed registry entry text (create mode)')
    p_qc.add_argument('--changes', default=None,
                      help='path to the approved change list JSON (refresh mode)')
    p_qc.set_defaults(func=cmd_qc)

    p_cre = sub.add_parser('apply-create', help='Phase 6 create: write value file + back-edges + registry')
    p_cre.add_argument('axis')
    p_cre.add_argument('value')
    p_cre.add_argument('--value-file', required=True,
                       help='path to a file holding the new value-file Markdown')
    p_cre.add_argument('--sibling-edits', required=True,
                       help='path to a JSON file of per-sibling Adjacency edits')
    p_cre.add_argument('--registry-entry', required=True,
                       help='path to a file holding the one-line registry bullet')
    p_cre.add_argument('--provisional', action='store_true',
                       help='mark the value file provisional and log unresolved QC issues')
    p_cre.add_argument('--issues', default=None,
                       help='path to a JSON file of unresolved QC issues (required with --provisional)')
    p_cre.set_defaults(func=cmd_apply_create)

    p_ref = sub.add_parser('apply-refresh', help='Phase 6 refresh: apply approved changes + bump last_researched')
    p_ref.add_argument('axis')
    p_ref.add_argument('value')
    p_ref.add_argument('--changes', required=True,
                       help='path to a JSON file of approved change records')
    p_ref.add_argument('--provisional', action='store_true',
                       help='mark the value file provisional and log unresolved QC issues')
    p_ref.add_argument('--issues', default=None,
                       help='path to a JSON file of unresolved QC issues (required with --provisional)')
    p_ref.set_defaults(func=cmd_apply_refresh)

    args = parser.parse_args()
    # --provisional requires --issues; argparse cannot express this conditional
    # natively, so validate after parsing.
    if getattr(args, 'provisional', False) and not args.issues:
        parser.error('--provisional requires --issues')

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
