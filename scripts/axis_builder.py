#!/usr/bin/env python3
"""
axis_builder.py - axis-builder skill artifact assembler

Mechanical file operations for the per-axis builder skills (industry-builder,
specialty-builder, orientation-builder, level-builder, work-state-builder).
Five subcommands:

  list           Phase 1 - emit every registry entry for an axis as JSON, so
                 the builder can identify the target's state AND build the
                 siblings list in one call without parsing the registry itself.
  lookup         Phase 1 - inspect a single registry entry; same shape as one
                 element of `list`. Kept for callers that only need one entry.
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
  apply-refresh  Phase 6 (refresh path) - overwrite an existing value file
                 with the post-QC drafted text and bump last_researched.
                 Optional --provisional behaves identically to apply-create.

Nothing repo-dependent is hardcoded here. Folder locations and filenames come
from config.yaml (via _config). All writes are scoped: whole-file overwrite
for refresh, targeted bullet insertion for sibling back-edges, single-line
swap for the registry entry.

Author    : Jason Delosh
Created   : 2026-05-18
Project   : career
Usage     : python scripts/axis_builder.py list <axis>
            python scripts/axis_builder.py lookup <axis> <value>
            python scripts/axis_builder.py qc <axis> <value> --mode create|refresh --value-file ... [--sibling-edits ... --registry-entry ... --changes ...]
            python scripts/axis_builder.py apply-create <axis> <value> --value-file ... --sibling-edits ... --registry-entry ... [--provisional --issues ...]
            python scripts/axis_builder.py apply-refresh <axis> <value> --value-file ... [--provisional --issues ...]
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


def _unwrap_list(parsed, key):
    """Return the inner list regardless of which contract shape the caller used.

    The reconciler subagent emits self-describing objects
    ({'mode': 'create', 'sibling_edits': [...]} or
    {'mode': 'refresh', 'changes': [...]}); legacy callers and tests pass the
    bare list. Both shapes are accepted so a contract mismatch between the
    agent and the script cannot surface as a Python traceback in front of
    the end user (see deferral 'builder-contract-drift-guardrails').
    """
    if isinstance(parsed, dict) and isinstance(parsed.get(key), list):
        return parsed[key]
    if isinstance(parsed, list):
        return parsed
    raise ValueError(
        f'expected a JSON list or {{"{key}": [...]}}; got {type(parsed).__name__}'
    )


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
# Axis value files use '## <Heading>' sections. Sibling back-edges (create
# mode) are inserted at the end of the target file's '## Adjacency' section.
# Refresh mode overwrites the whole file from the drafted text, so no
# in-section modify/remove helpers are needed here.
# ---------------------------------------------------------------------------

def _find_section_bounds(text, heading):
    """Return (start, end) character offsets of a '## heading' section body.

    Body excludes the heading line itself; start is the offset just after the
    heading line's trailing newline; end is the offset of the next '## ' line
    or the end of file. Raises ValueError if the heading is absent.
    """
    pattern = re.compile(
        r'^##[ ]+' + re.escape(heading) + r'[ \t]*\n',
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
    """Inspect a registry entry and print {value, state, value_file_path} as JSON.

    State is one of 'not-in-registry', 'file-deferred', 'registry-only',
    'file-backed'. The calling skill uses this to decide create vs refresh
    and to refuse incoherent invocations (e.g. refresh on a missing file).
    """
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
# Subcommand: list
# Emit every registry entry as a single JSON object. The calling skill uses
# this in Phase 1 to identify the target value's state AND to build the
# siblings list in one call, without parsing the registry itself.
# ---------------------------------------------------------------------------

def cmd_list(args, repo_root, cfg):
    """Print {"entries": [...]} for every bullet in the axis registry.

    Each entry is {value, state, value_file_path}. State is one of
    'file-backed', 'file-deferred', 'registry-only'. value_file_path is
    the absolute path for file-backed entries, None otherwise.
    """
    registry_path = _registry_path(repo_root, cfg, args.axis)
    if not os.path.exists(registry_path):
        raise FileNotFoundError(f'registry not found: {registry_path}')
    text = _read(registry_path)
    entries = []
    for m in _BULLET_RE.finditer(text):
        value = m.group('value').strip()
        state, value_filename = _classify_bullet(m.group('rest'))
        value_file_path = (
            _value_file_path(repo_root, cfg, args.axis, value_filename)
            if value_filename else None
        )
        entries.append({
            'value': value,
            'state': state,
            'value_file_path': value_file_path,
        })
    print(json.dumps({'entries': entries}))


# ---------------------------------------------------------------------------
# Subcommand: slice
# Return the body of a named '## Section' from a file-backed axis value file.
# Used by the industry-builder skill's Phase 4 to give the reconciler subagent
# just the Adjacency section content of each sibling, rather than the full
# file. Keeps the reconciler's context cost bounded regardless of how many
# siblings an axis registry contains.
# ---------------------------------------------------------------------------

def cmd_slice(args, repo_root, cfg):
    """Print the body text of '## <section>' from a file-backed value's file.

    Requires the value to be file-backed (otherwise there is no file to
    slice). Output is the raw section body on stdout, no JSON wrapper, so
    the caller can splice it directly into a subagent prompt.
    """
    registry_path = _registry_path(repo_root, cfg, args.axis)
    if not os.path.exists(registry_path):
        raise FileNotFoundError(f'registry not found: {registry_path}')
    text = _read(registry_path)
    _, state, value_filename = _find_registry_entry(text, args.value)
    if state != 'file-backed' or not value_filename:
        raise ValueError(
            f'slice requires a file-backed value; {args.value} is {state}')
    value_path = _value_file_path(repo_root, cfg, args.axis, value_filename)
    if not os.path.exists(value_path):
        raise FileNotFoundError(f'value file missing: {value_path}')
    body = _read(value_path)
    start, end = _find_section_bounds(body, args.section)
    sys.stdout.write(body[start:end])


# ---------------------------------------------------------------------------
# Subcommand: qc
# Mechanical QC per rules/quality_control/qc-<axis>-builder.md. Runs the
# checks the script can verify deterministically and applies auto-fixes
# in place where the fix is purely textual (frontmatter shell + keys,
# title insertion when missing, Used-by header, section order, Adjacency
# self-reference). Checks that need LLM judgment to fix (missing section
# content, missing adjacency bullets, misdirected sibling edits,
# registry-filename mismatch, em-dash rewrites) are reported but not
# fixed - the calling skill loops by re-entering the earlier phase.
#
# Output: a JSON object on stdout with per-check entries:
#   { "checks": [ { "id": "A1", "passed": bool, "fixed": bool,
#                   "detail": "<one-line explanation>" }, ... ] }
# The calling skill aggregates with the judgment-check subagent's output
# to build the final unresolved-issues list passed to apply-* --issues.
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
    fm, _ = _split_frontmatter(text)
    if fm is not None:
        return text, _record('A1', True, False, 'frontmatter present')
    new_text = '---\n---\n' + text
    return new_text, _record('A1', True, True, 'inserted empty frontmatter shell')


def _check_a2_frontmatter_key(text, axis_key, value):
    """A2: frontmatter has '<axis_key>: <value>'. A1 guarantees fm exists."""
    fm, body = _split_frontmatter(text)
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
    fm, body = _split_frontmatter(text)
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
    """A4: a top-level title exists and ends with '- CV Framing Rules'.

    Case-insensitive on the trailing fixed phrase. The display form of the
    value (CRO vs Cro vs cro) is the drafter's responsibility; the script
    neither enforces nor seeds capitalization, since most casing decisions
    are judgment calls (initialisms, acronyms, brand forms). When the
    title is absent, A4 fails and Phase 5 routes the failure to Phase 3
    redraft.
    """
    _, body = _split_frontmatter(text)
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
    fm, body = _split_frontmatter(text)
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

def _check_e1_adjacency_complete(text, value, registry_path):
    """E1: Adjacency has one bullet per non-self registry entry.

    Includes file-backed, file-deferred, and registry-only siblings - the
    Adjacency section enumerates every other axis value so a candidate can
    translate between any pair. The reconciler still drafts back-edges only
    into file-backed siblings (the other states have no file to edit); E1
    just enforces completeness of the new file's own Adjacency.
    """
    try:
        body_start, body_end = _find_section_bounds(text, 'Adjacency')
    except ValueError:
        return text, _record('E1', False, False, 'no Adjacency section')
    adjacency_body = text[body_start:body_end]
    if not os.path.exists(registry_path):
        return text, _record('E1', False, False, f'registry missing: {registry_path}')
    registry_text = _read(registry_path)
    siblings = []
    for m in _BULLET_RE.finditer(registry_text):
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
        dialect_start, dialect_end = _find_section_bounds(text, 'Dialect')
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
            s, e = _find_section_bounds(text, section)
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


# ---------------------------------------------------------------------------
# QC orchestrator
# Runs each check group in order against the drafted value-file text. Auto-fix
# checks return mutated text; report-only checks return the text unchanged.
# Mode-specific checks (E4, G1, I1, I2, I3) run only when the matching inputs
# are present. The (possibly mutated) text is written back to --value-file so
# the calling skill picks up the auto-fixed draft for the next phase.
# ---------------------------------------------------------------------------

def cmd_qc(args, repo_root, cfg):
    """Run mechanical QC checks against --value-file and print a per-check JSON report.

    Auto-fix-capable checks mutate the file in place; report-only checks
    leave the file unchanged. Mode-specific checks (E4, G1, I1, I2, I3) run
    only when their matching inputs are present.
    """
    schema = _axis_schema(cfg, args.axis)
    axis_key = schema['frontmatter_key']
    required_sections = schema['required_sections']
    used_by_line = schema['used_by']

    text = _read(args.value_file)
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
    registry_path = _registry_path(repo_root, cfg, args.axis)
    text, rec = _check_e1_adjacency_complete(text, args.value, registry_path); checks.append(rec)
    text, rec = _check_e2_no_self_reference(text, args.value); checks.append(rec)

    # --- Group H (mechanical): acronym list reconciles with body usage ---
    text, rec = _check_h2_acronym_reconciliation(text); checks.append(rec)

    # --- Mode-specific: create runs E4 + G1 + I1; refresh runs I2 + I3 ---
    value_path = _value_file_path(repo_root, cfg, args.axis, f'{args.value}.md')
    if args.mode == 'create':
        checks.append(_check_i1_create_invariant(value_path))
        # E4 (sibling-edits target Adjacency) and G1 (registry filename
        # matches value file) are required in create mode. Refuse to
        # silently skip them when their inputs are missing; the absent
        # input is itself the bug worth surfacing.
        if not args.sibling_edits:
            raise ValueError(
                'create mode requires --sibling-edits; '
                'refusing to skip the sibling-edits-target check silently'
            )
        sibling_edits = _unwrap_list(_load_json(args.sibling_edits), 'sibling_edits')
        checks.append(_check_e4_sibling_edits_targeting(sibling_edits))
        if not args.registry_entry:
            raise ValueError(
                'create mode requires --registry-entry; '
                'refusing to skip the registry-filename check silently'
            )
        registry_entry_text = _read(args.registry_entry).strip()
        checks.append(_check_g1_registry_entry_filename(registry_entry_text, f'{args.value}.md'))
    elif args.mode == 'refresh':
        checks.append(_check_i2_refresh_invariant(value_path))
        # I3 (no-op refresh detection) is required in refresh mode. Refuse
        # to silently skip it when --changes is missing; the absent input
        # is itself the bug worth surfacing.
        if not args.changes:
            raise ValueError(
                'refresh mode requires --changes (the reconciler change list); '
                'refusing to skip the no-op-refresh check silently'
            )
        changes = _unwrap_list(_load_json(args.changes), 'changes')
        checks.append(_check_i3_refresh_has_changes(changes))

    # --- Persist the (possibly fixed) value-file text and emit the report ---
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
#                                    "bullet": "- **<value>**: <translation>."},
#                      OR the reconciler's self-describing wrapper
#                      {"mode": "create", "sibling_edits": [...]}.
#                      Either is accepted (see _unwrap_list).
#   --registry-entry   one-line Markdown bullet for the registry entry, e.g.
#                      "- **generics** - generic and 505(b)(2) ... File: generics.md."
#   --issues           JSON list of {"check": "...", "detail": "...",
#                                    "attempted": "..."} (provisional only)
# ---------------------------------------------------------------------------

def cmd_apply_create(args, repo_root, cfg):
    """Write a new value file, apply sibling Adjacency back-edges, update the registry.

    Refuses if the value file already exists. With --provisional, marks the
    file's frontmatter and appends a record to design/build_issues.md after
    the main writes succeed.

    Two-stage protection against half-modified state:
    - All transformations (sibling reads, Adjacency-section locate, bullet
      insert) run in memory before any disk write. A missing sibling file or
      malformed input fails the run without touching disk.
    - The write loop snapshots each target's prior content (or "did not
      exist") up front. If any _write raises mid-loop, every write that
      already landed is rolled back: pre-existing files are restored to
      their prior content; new files (only the value file) are deleted.
      The original exception then propagates. If rollback itself fails
      (disk still full, file just became locked), both errors are reported
      and the user must reconcile by hand.

    Prints every path written, one per line, as it is written (not at the
    end), so the calling skill and user see partial-write state if the
    rollback path itself fails.
    """
    axis = args.axis
    value = args.value
    registry_path = _registry_path(repo_root, cfg, axis)

    # --- Resolve target paths and refuse if the value file already exists ---
    # Filename convention: <value>.md. If a custom filename is ever needed, add
    # a --filename arg rather than parsing it out of the registry-entry text.
    value_filename = f'{value}.md'
    value_path = _value_file_path(repo_root, cfg, axis, value_filename)
    if os.path.exists(value_path):
        raise FileExistsError(
            f'value file already exists: {value_path}. Use refresh, not create.')

    # --- Read all inputs upfront ---
    value_text = _read(args.value_file)
    sibling_edits = _unwrap_list(_load_json(args.sibling_edits), 'sibling_edits')
    registry_entry_line = _read(args.registry_entry).strip()
    issues = _load_json(args.issues) if args.provisional else None

    # --- Re-enforce G1 at the apply step ---
    # QC's 3-iteration loop can give up and ship a provisional build with
    # unresolved findings, but a registry entry whose 'File:' pointer does
    # not match the value file is structural corruption (downstream
    # consumers would follow the pointer to a missing file), not a
    # triage-able content issue. Refuse the apply rather than write a
    # broken pointer.
    g1 = _check_g1_registry_entry_filename(registry_entry_line, value_filename)
    if not g1['passed']:
        raise ValueError(f"registry entry mismatch (G1): {g1['detail']}")

    # --- Provisional marking on the value text (in-memory only) ---
    if args.provisional:
        value_text = _apply_provisional(value_text, issues)

    # --- Stage all overwrite writes ---
    # Build a list of (path, text) pairs. Nothing is written to disk yet.
    # If any transformation below raises (missing sibling file, missing
    # Adjacency section, malformed input), the repo is unchanged.
    staged = [(value_path, value_text)]

    # Sibling Adjacency back-edges.
    for edit in sibling_edits:
        sibling_path = _value_file_path(repo_root, cfg, axis, edit['sibling_file'])
        if not os.path.exists(sibling_path):
            raise FileNotFoundError(f'sibling file missing: {sibling_path}')
        sibling_text = _read(sibling_path)
        sibling_text = _insert_bullet_in_section(
            sibling_text, edit.get('section', 'Adjacency'), edit['bullet'])
        staged.append((sibling_path, sibling_text))

    # Registry: replace existing bullet or append new one.
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
    staged.append((registry_path, registry_text))

    # --- Snapshot pre-write state for transactional rollback ---
    # For each staged target, remember either its prior content (existed
    # before) or None (did not exist). On a mid-loop write failure we use
    # this to put the repo back to its pre-run state.
    originals = {}
    for path, _ in staged:
        originals[path] = _read(path) if os.path.exists(path) else None

    # --- Apply staged writes with rollback on failure ---
    written_paths = []
    try:
        for path, text in staged:
            _write(path, text)
            written_paths.append(path)
            # Print as we go (flushed) so any partial state is visible if
            # the rollback path itself fails below.
            print(path, flush=True)
    except Exception:
        # Roll back in reverse order: undo most recent writes first. For
        # pre-existing files restore the prior text; for newly-created
        # files delete them. Best-effort: if a rollback step itself
        # raises, log it to stderr and continue so the rest of the rollback
        # still runs, then re-raise the original exception.
        for path in reversed(written_paths):
            try:
                original = originals[path]
                if original is None:
                    os.remove(path)
                else:
                    _write(path, original)
                print(f'rolled back: {path}', file=sys.stderr)
            except Exception as rollback_err:
                print(
                    f'rollback FAILED for {path}: {rollback_err}',
                    file=sys.stderr,
                )
        raise

    # --- Provisional: append to build-issues log (last; append-only) ---
    if args.provisional:
        log_path = _append_build_issues(repo_root, cfg, axis, value, 'create', issues)
        print(log_path, flush=True)


# ---------------------------------------------------------------------------
# Subcommand: apply-refresh
# Overwrite an existing value file with the post-QC drafted text, bump
# last_researched, and (optionally) mark provisional + log issues.
#
# Input file shapes:
#   --value-file  full Markdown text of the refreshed value file (the same
#                 temp file qc was run against, with any auto-fixes carried
#                 through). The reconciler's change list is informational
#                 for QC only; the apply step writes the drafted file
#                 wholesale so Phase 5 auto-fixes are preserved.
#   --issues      JSON list of {"check": "...", "detail": "...",
#                               "attempted": "..."} (provisional only)
# ---------------------------------------------------------------------------

def cmd_apply_refresh(args, repo_root, cfg):
    """Overwrite an existing value file with the drafted text and bump last_researched.

    Refuses if the value file is missing. With --provisional, marks the
    file's frontmatter and appends a record to design/build_issues.md.
    Prints every path touched, one per line.
    """
    axis = args.axis
    value = args.value
    value_filename = f'{value}.md'
    value_path = _value_file_path(repo_root, cfg, axis, value_filename)

    # --- Refuse if the value file does not already exist ---
    if not os.path.exists(value_path):
        raise FileNotFoundError(
            f'value file missing: {value_path}. Use create, not refresh.')

    # --- Load drafted text (the post-QC --value-file temp) ---
    text = _read(args.value_file)

    # --- Bump last_researched (always; the research run happened) ---
    text = _bump_last_researched(text, _today_ym())

    # --- Load issues and apply provisional flag to the in-memory text ---
    issues = None
    if args.provisional:
        issues = _load_json(args.issues)
        text = _apply_provisional(text, issues)

    # --- Write the value file first (primary artifact) ---
    _write(value_path, text)
    written_paths = [value_path]

    # --- Append the build-issues log only after the primary write succeeds ---
    # Inverted order would leave a phantom log entry if the value-file write
    # failed (disk full, permissions); the log is append-only and not rolled
    # back. Mirrors the order in cmd_apply_create.
    if args.provisional:
        log_path = _append_build_issues(repo_root, cfg, axis, value, 'refresh', issues)
        written_paths.append(log_path)

    for p in written_paths:
        print(p)


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses subcommand and arguments, loads config, runs the subcommand, and
# reports failure to stderr with a non-zero exit so the calling skill halts
# per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch to the selected subcommand.

    Exits 1 with a one-line stderr message on any uncaught exception so the
    calling skill halts per global-rules.md.
    """
    parser = argparse.ArgumentParser(description='axis-builder artifact assembler')
    sub = parser.add_subparsers(dest='command', required=True)

    # --- Subparser: lookup ---
    p_look = sub.add_parser('lookup', help='Phase 1: inspect a single registry entry')
    p_look.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    p_look.add_argument('value', help='registry key (e.g. generics)')
    p_look.set_defaults(func=cmd_lookup)

    # --- Subparser: list ---
    p_list = sub.add_parser('list', help='Phase 1: list every registry entry for an axis')
    p_list.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    p_list.set_defaults(func=cmd_list)

    # --- Subparser: slice ---
    p_slice = sub.add_parser(
        'slice',
        help='Phase 4: print the body of one section from a file-backed value file',
    )
    p_slice.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    p_slice.add_argument('value', help='registry key of the file-backed value to slice')
    p_slice.add_argument(
        '--section', required=True,
        help='heading (without ## prefix) of the section to extract, e.g. Adjacency',
    )
    p_slice.set_defaults(func=cmd_slice)

    # --- Subparser: qc ---
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

    # --- Subparser: apply-create ---
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

    # --- Subparser: apply-refresh ---
    p_ref = sub.add_parser('apply-refresh', help='Phase 6 refresh: overwrite value file with drafted text + bump last_researched')
    p_ref.add_argument('axis')
    p_ref.add_argument('value')
    p_ref.add_argument('--value-file', required=True,
                       help='path to the drafted (post-QC) value-file Markdown to write')
    p_ref.add_argument('--provisional', action='store_true',
                       help='mark the value file provisional and log unresolved QC issues')
    p_ref.add_argument('--issues', default=None,
                       help='path to a JSON file of unresolved QC issues (required with --provisional)')
    p_ref.set_defaults(func=cmd_apply_refresh)

    # --- Cross-cutting validation argparse cannot express natively ---
    args = parser.parse_args()
    if getattr(args, 'provisional', False) and not args.issues:
        parser.error('--provisional requires --issues')

    # --- Dispatch to the selected subcommand ---
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
