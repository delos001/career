#!/usr/bin/env python3
"""
retrieval_qc.py - deterministic QC for the retrieval skill's manifest

Replaces the qc-retrieval subagent: every check that agent ran was
mechanical (structure, counts, column population, cross-ID existence,
date format), so retrieval QC is script-only with no judgment residue.

Checks (IDs mirror the original qc-retrieval check numbering):
  R1  Manifest structure: H1, Generated line, JD axis classification
      block, signal-column explanation, and the three tables with their
      expected column headers, in order.
  R2  Axis classification consistency: the manifest's per-axis values
      match the session log's ## Axis Classification values.
  R3  Inventory coverage: source inventory entry count (the authoritative
      baseline) == manifest inventory row count; with --scored-inventory,
      the three-way comparison distinguishes dropped-before-scoring from
      dropped-at-merge/assemble.
  R4  Signal column population: every inventory row fully populated;
      `-` for Semantic only on tag-pull-only rows; `-` for Employer only
      on PB/PS rows.
  R5  Narrative integrity: every Linked-from ID exists in the manifest's
      inventory table.
  R6  Theme integrity: every theme row ID exists in positioning.md.
  R7  No fabricated IDs anywhere: every EX/PR/PB/PS, ST/DC, TH ID in the
      manifest exists in its source profile document.
  R8  Generated date well-formed (and equal to --date when given).

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT
line. Exit 0 when all pass, 1 otherwise.

Author  : Jason Delosh
Created : 2026-07-14
Project : career
Usage   : python scripts/retrieval_qc.py check --folder <app_folder> [--scored-inventory N] [--date YYYY-MM-DD]
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Constants: manifest structure
# ---------------------------------------------------------------------------

# The three manifest tables with their expected column headers, in order.
TABLES = {
    'Inventory candidates': ['ID', 'Employer', 'Semantic', 'Axis exact', 'Axis adj',
                             'Source', 'Axis matches', 'Reason'],
    'Narratives': ['ID', 'Semantic', 'Linked from', 'Reason'],
    'Triggered themes': ['ID', 'Semantic', 'Title', 'Reason'],
}

# The five axes of the JD classification block.
AXES = ['Industry', 'Specialty', 'Orientation', 'Level', 'Work-state']

# Regex: inventory entry ID lines in inventory.md (retrievable prefixes).
_INV_ID_RE = re.compile(r'^ID:\s+((?:EX|PR|PB|PS)-\d+)\s*$', re.MULTILINE)

# Regex: narrative ID lines in narratives.md.
_NARR_ID_RE = re.compile(r'^ID:\s+((?:ST|DC)-\d+)\s*$', re.MULTILINE)

# Regex: theme headings in positioning.md.
_THEME_ID_RE = re.compile(r'^##\s+(TH-\d+)\b', re.MULTILINE)

# Regex: a value token with optional (primary)/(secondary) annotation, for
# normalizing axis classification values before comparison.
_AXIS_ANNOTATION_RE = re.compile(r'\s*\((?:primary|secondary)\)')


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_table(manifest_text, heading, expected_cols):
    """Return (rows, header_ok) for the table under `## <heading>`.

    Each row is a list of cell strings. Cells beyond the expected count are
    merged into the last column so a pipe inside the free-text Reason cell
    cannot shift the parse.
    """
    lines = manifest_text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f'## {heading}':
            start = i + 1
            break
    if start is None:
        return None, False
    rows = []
    header_ok = False
    in_table = False
    for line in lines[start:]:
        if line.startswith('## '):
            break
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if not in_table:
            header_ok = cells == expected_cols
            in_table = True
            continue
        if all(re.fullmatch(r'-*', c) for c in cells):
            continue  # the |----| separator row
        if len(cells) > len(expected_cols):
            cells = cells[:len(expected_cols) - 1] + [' | '.join(cells[len(expected_cols) - 1:])]
        elif len(cells) < len(expected_cols):
            # Pad short rows so R4's empty-cell checks flag them as findings
            # instead of the column unpack crashing on a malformed row.
            cells = cells + [''] * (len(expected_cols) - len(cells))
        rows.append(cells)
    return rows, header_ok


def _manifest_axes(manifest_text):
    """Return {axis: normalized value string} from the manifest header block."""
    axes = {}
    for axis in AXES:
        m = re.search(rf'^- \*\*{re.escape(axis)}:\*\*\s*(.+)$', manifest_text, re.MULTILINE)
        if m:
            axes[axis] = _normalize_axis_value(m.group(1))
    return axes


def _session_log_axes(log_text):
    """Return {axis: normalized value string} from ## Axis Classification.

    Session log lines carry a ` - <rationale>` suffix after the value list;
    kebab-case values contain no spaced hyphen, so splitting on the first
    ' - ' isolates the values.
    """
    lines = log_text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if line.strip() == '## Axis Classification':
            start = i + 1
            break
    if start is None:
        return None
    axes = {}
    for line in lines[start:]:
        if line.startswith('## '):
            break
        # Labels appear both plain (`- Industry:`) and bold
        # (`- **Industry:**`) across runs; accept both.
        m = re.match(
            r'^- (?:\*\*)?(Industry|Specialty|Orientation|Level|Work-state):(?:\*\*)?\s*(.+)$',
            line)
        if m:
            axes[m.group(1)] = _normalize_axis_value(m.group(2).split(' - ')[0])
    return axes


def _normalize_axis_value(raw):
    """Strip (primary)/(secondary) annotations and normalize separators."""
    value = _AXIS_ANNOTATION_RE.sub('', raw)
    return ', '.join(v.strip() for v in value.split(',') if v.strip())


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_structure(manifest_text, tables, findings):
    """R1: H1, Generated line, axis block, signal explanation, three tables."""
    problems = []
    if not re.match(r'^# Retrieval Manifest', manifest_text):
        problems.append('missing `# Retrieval Manifest` H1')
    if not re.search(r'^\*\*Generated:\*\*', manifest_text, re.MULTILINE):
        problems.append('missing `**Generated:**` line')
    if not re.search(r'^\*\*JD axis classification', manifest_text, re.MULTILINE):
        problems.append('missing JD axis classification block')
    if not re.search(r'^\*\*Signal columns:\*\*', manifest_text, re.MULTILINE):
        problems.append('missing signal-column explanation')
    for heading, (rows, header_ok) in tables.items():
        if rows is None:
            problems.append(f'missing `## {heading}` section')
        elif not header_ok:
            problems.append(f'`## {heading}` table header off-spec')
    findings.append(('R1', not problems, '; '.join(problems) or 'manifest structure canonical'))


def check_axis_consistency(manifest_text, log_text, findings):
    """R2: manifest axis block matches the session log classification."""
    if log_text is None:
        findings.append(('R2', False, 'session log not found'))
        return
    log_axes = _session_log_axes(log_text)
    if log_axes is None:
        findings.append(('R2', False, 'session log has no ## Axis Classification section'))
        return
    manifest_axes = _manifest_axes(manifest_text)
    problems = []
    for axis in AXES:
        mv, lv = manifest_axes.get(axis), log_axes.get(axis)
        if mv is None or lv is None:
            problems.append(f'{axis} missing from ' + ('manifest' if mv is None else 'session log'))
        elif mv != lv:
            problems.append(f'{axis} diverges: manifest {mv!r} vs session log {lv!r}')
    findings.append(('R2', not problems, '; '.join(problems) or 'axis classification consistent'))


def check_coverage(inv_rows, source_count, scored_count, findings):
    """R3: source entry count is the baseline; manifest (and the scored
    count, when given) must match it."""
    manifest_count = len(inv_rows or [])
    problems = []
    if manifest_count != source_count:
        if scored_count is not None and scored_count == manifest_count:
            problems.append(
                f'source has {source_count} entries but only {scored_count} were scored: '
                'entries dropped before scoring (payload build)')
        elif scored_count is not None and manifest_count < scored_count:
            problems.append(
                f'{scored_count} entries scored but manifest carries {manifest_count}: '
                'entries dropped at merge/assemble')
        else:
            problems.append(
                f'manifest carries {manifest_count} inventory rows, source has {source_count}')
    elif scored_count is not None and scored_count != source_count:
        problems.append(
            f'{scored_count} entries scored vs {source_count} in source, '
            'yet the manifest matches source; scored-count input is suspect')
    findings.append(('R3', not problems,
                     '; '.join(problems) or f'all {source_count} source entries in the manifest'))


def check_columns(inv_rows, findings):
    """R4: every inventory row fully populated per the column rules."""
    problems = []
    for row in inv_rows or []:
        rid, employer, semantic, ax_exact, ax_adj, source, matches, reason = row
        row_problems = []
        if employer == '' or (employer == '-' and not rid.startswith(('PB-', 'PS-'))):
            row_problems.append('Employer')
        if semantic == '' or (semantic == '-' and 'semantic' in source):
            row_problems.append('Semantic')
        if not re.fullmatch(r'[0-5]', ax_exact):
            row_problems.append('Axis exact')
        if not re.fullmatch(r'\d+(\.\d+)?', ax_adj):
            row_problems.append('Axis adj')
        for label, value in (('Source', source), ('Axis matches', matches), ('Reason', reason)):
            if not value:
                row_problems.append(label)
        if row_problems:
            problems.append(f"{rid}: {', '.join(row_problems)}")
    findings.append(('R4', not problems,
                     f"unpopulated or off-rule columns: {'; '.join(problems)}" if problems
                     else 'all signal columns populated'))


def check_narrative_links(narr_rows, inv_rows, findings):
    """R5: every Linked-from ID appears in the manifest's inventory table."""
    inv_ids = {row[0] for row in inv_rows or []}
    problems = []
    for row in narr_rows or []:
        nid, _, linked, _ = row
        if linked in ('', '-'):
            continue
        missing = [i.strip() for i in linked.split(',')
                   if i.strip() and i.strip() not in inv_ids]
        if missing:
            problems.append(f"{nid} links to {', '.join(missing)} not in the inventory table")
    findings.append(('R5', not problems, '; '.join(problems) or 'narrative links intact'))


def check_theme_ids(theme_rows, theme_ids, findings):
    """R6: every theme row ID exists in positioning.md."""
    bad = [row[0] for row in theme_rows or [] if row[0] not in theme_ids]
    findings.append(('R6', not bad,
                     f"theme IDs not in positioning.md: {', '.join(bad)}" if bad
                     else 'theme IDs verified'))


def check_all_ids(manifest_text, inv_ids, narr_ids, theme_ids, findings):
    """R7: every profile ID token in the manifest exists in its source doc."""
    problems = []
    fabricated_inv = sorted({t for t in re.findall(r'\b(?:EX|PR|PB|PS)-\d+\b', manifest_text)
                             if t not in inv_ids})
    fabricated_narr = sorted({t for t in re.findall(r'\b(?:ST|DC)-\d+\b', manifest_text)
                              if t not in narr_ids})
    fabricated_theme = sorted({t for t in re.findall(r'\bTH-\d+\b', manifest_text)
                               if t not in theme_ids})
    for label, fabricated in (('inventory.md', fabricated_inv),
                              ('narratives.md', fabricated_narr),
                              ('positioning.md', fabricated_theme)):
        if fabricated:
            problems.append(f"not in {label}: {', '.join(fabricated)}")
    findings.append(('R7', not problems, '; '.join(problems) or 'all cited IDs exist'))


def check_generated_date(manifest_text, run_date, findings):
    """R8: Generated date is YYYY-MM-DD (and equals --date when given)."""
    m = re.search(r'^\*\*Generated:\*\*\s*(.+)$', manifest_text, re.MULTILINE)
    if not m:
        findings.append(('R8', False, 'missing `**Generated:**` line'))
        return
    value = m.group(1).strip()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        findings.append(('R8', False, f'Generated date malformed: {value!r}'))
        return
    if run_date and value != run_date:
        findings.append(('R8', False, f'Generated date {value} does not match run date {run_date}'))
        return
    findings.append(('R8', True, f'Generated date well-formed ({value})'))


# ---------------------------------------------------------------------------
# Command: check
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Run all checks against one application folder; print report; return exit code."""
    fn = cfg['filenames']
    profile_dir = os.path.join(repo_root, cfg['paths']['profile'])
    app_folder = args.folder

    manifest_text = _read(os.path.join(app_folder, fn['retrieval_manifest']))
    if manifest_text is None:
        print(f"FATAL  {fn['retrieval_manifest']} not found in {app_folder}")
        return 1

    log_text = _read(os.path.join(app_folder, fn['session_log_file']))
    inventory_text = _read(os.path.join(profile_dir, fn['inventory_file'])) or ''
    narratives_text = _read(os.path.join(profile_dir, fn['narratives_file'])) or ''
    positioning_text = _read(os.path.join(profile_dir, fn['positioning_file'])) or ''

    inv_ids = set(_INV_ID_RE.findall(inventory_text))
    narr_ids = set(_NARR_ID_RE.findall(narratives_text))
    theme_ids = set(_THEME_ID_RE.findall(positioning_text))

    tables = {heading: _parse_table(manifest_text, heading, cols)
              for heading, cols in TABLES.items()}
    inv_rows = tables['Inventory candidates'][0]
    narr_rows = tables['Narratives'][0]
    theme_rows = tables['Triggered themes'][0]

    findings = []
    check_structure(manifest_text, tables, findings)
    check_axis_consistency(manifest_text, log_text, findings)
    check_coverage(inv_rows, len(inv_ids), args.scored_inventory, findings)
    check_columns(inv_rows, findings)
    check_narrative_links(narr_rows, inv_rows, findings)
    check_theme_ids(theme_rows, theme_ids, findings)
    check_all_ids(manifest_text, inv_ids, narr_ids, theme_ids, findings)
    check_generated_date(manifest_text, args.date, findings)

    failed = [f for f in findings if not f[1]]
    for check, ok, detail in findings:
        print(f"{check}  {'PASS' if ok else 'FAIL'}  {detail}")
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  "
          f"{len(findings) - len(failed)}/{len(findings)} checks passed")
    return 0 if not failed else 1


def _read(path):
    """Read a file, or return None if it does not exist."""
    if not os.path.isfile(path):
        return None
    return _util.read(path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Deterministic QC for the retrieval manifest.')
    sub = parser.add_subparsers(dest='command', required=True)
    p_check = sub.add_parser('check', help='validate one application folder')
    p_check.add_argument('--folder', required=True,
                         help='absolute path to the application folder')
    p_check.add_argument('--scored-inventory', type=int, default=None,
                         help='inventory entry count the scoring pass reported '
                              '(from retrieval_score_merge.py output); enables '
                              'the three-way coverage diagnosis')
    p_check.add_argument('--date', default=None,
                         help='run date YYYY-MM-DD; the Generated line must match')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    if args.command == 'check':
        sys.exit(cmd_check(args, repo_root, cfg))


if __name__ == '__main__':
    main()
