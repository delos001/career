#!/usr/bin/env python3
"""
role_intake_qc.py - deterministic QC for the role-intake skill's artifacts

Owns the mechanical checks that the qc-role-intake judgment subagent must
not re-run: section and field presence, pending-marker detection, date
form, URL presence in Sources, cross-file field equality, and axis-gap
mirroring. The judgment agent keeps what a script cannot verify (whether
the axis classification is supported by the research content, and whether
claims trace to sources).

Checks (IDs map to the original qc-role-intake check numbering; check 3
split into its mechanical half, check 5 stays with the agent):
  I1  Research file completeness: H1 + APP-NNN + Research completed lines;
      Company / Role / Industry sections each carrying non-empty Summary,
      Key facts, and Sources (with at least one URL); Critical Requirements
      with at least one row; Axis Gaps present. No pending markers.
  I2  Session log completeness: every Metadata field line present, the
      required ones non-empty, dates well-formed; Axis Classification with
      all five axis lines; Axis Gaps present. No pending markers.
  I3  Cross-file consistency (mechanical half): company, role, and APP-NNN
      match between the two files; the metadata Role Level and Industry
      values match the Axis Classification's Level and Industry values.
  I4  Axis gaps recorded in both: the set of axes flagged in the session
      log's Axis Gaps matches the set flagged in the research file's.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT
line. Exit 0 when all pass, 1 otherwise.

Author  : Jason Delosh
Created : 2026-07-14
Project : career
Usage   : python scripts/role_intake_qc.py check --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Constants: artifact structure
# ---------------------------------------------------------------------------

# Research file: the three research blocks, each with these H3 subsections.
RESEARCH_BLOCKS = ['Company', 'Role', 'Industry']
BLOCK_SUBSECTIONS = ['Summary', 'Key facts', 'Sources']

# Session log Metadata: fields that must be present AND non-empty. Comms
# file/source must be present but may be blank (no comms ingested).
METADATA_REQUIRED = ['APP-NNN', 'Company', 'Role', 'Role Level', 'Industry',
                     'Session Start Date', 'Research Completed Date',
                     'JD file', 'JD source']
METADATA_OPTIONAL = ['Comms file', 'Comms source']

# Metadata date fields that must be YYYY-MM-DD.
DATE_FIELDS = ['Session Start Date', 'Research Completed Date']

# The five axes of the classification section.
AXES = ['Orientation', 'Industry', 'Specialty', 'Level', 'Work-state']

# Pending markers that finalize (Phase 7) must have replaced.
_PENDING_RE = re.compile(r'_\(pending\)_|\{\{[a-z_]+\}\}')

# Regex: a URL, for the Sources subsection check.
_URL_RE = re.compile(r'https?://\S+')


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _section_body(text, heading, depth=2):
    """Return the body of a `## `/`### ` section, or None if absent."""
    marker = '#' * depth + ' ' + heading
    lines = text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if line.strip() == marker:
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        m = re.match(r'^(#+)\s', lines[j])
        if m and len(m.group(1)) <= depth:
            end = j
            break
    return '\n'.join(lines[start:end]).strip()


def _metadata_fields(log_text):
    """Return {label: value} from the session log's ## Metadata section."""
    body = _section_body(log_text, 'Metadata')
    if body is None:
        return None
    fields = {}
    for line in body.split('\n'):
        m = re.match(r'^- (.+?):\s*(.*)$', line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


def _axis_values(log_text):
    """Return {axis: value part} from ## Axis Classification lines.

    Each line is `- <Axis>: <values> - <rationale>`; kebab-case values carry
    no spaced hyphen, so the first ' - ' isolates the value part.
    """
    body = _section_body(log_text, 'Axis Classification')
    if body is None:
        return None
    values = {}
    for line in body.split('\n'):
        # Labels appear both plain (`- Orientation:`) and bold
        # (`- **Orientation:**`) across runs; accept both (same seam as the
        # finalize metadata fill, fixed 2026-07).
        m = re.match(
            r'^- (?:\*\*)?(Orientation|Industry|Specialty|Level|Work-state):(?:\*\*)?\s*(.+)$',
            line)
        if m:
            values[m.group(1)] = m.group(2).split(' - ')[0].strip()
    return values


def _gap_axes(text):
    """Return the set of axis names flagged in a file's ## Axis Gaps section.

    `- None` (or an empty body) means no gaps and yields the empty set.
    Returns None if the section is absent.
    """
    body = _section_body(text, 'Axis Gaps')
    if body is None:
        return None
    axes = set()
    for line in body.split('\n'):
        # Accept plain and bold labels (see _axis_values).
        m = re.match(r'^- (?:\*\*)?(Orientation|Industry|Specialty|Level|Work-state)\b', line)
        if m:
            axes.add(m.group(1))
    return axes


def _h1_company_role(text, prefix):
    """Parse `# <prefix>: <company> | <role>` from a file's H1, or None."""
    m = re.match(rf'^# {re.escape(prefix)}:\s*(.+?)\s*\|\s*(.+?)\s*$', text.split('\n')[0])
    return (m.group(1), m.group(2)) if m else None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_research(research_text, findings):
    """I1: research file structure, block subsections, sources, requirements."""
    problems = []
    if _h1_company_role(research_text, 'Research') is None:
        problems.append('H1 is not `# Research: <company> | <role>`')
    for label in ('APP-NNN', 'Research completed'):
        m = re.search(rf'^\*\*{re.escape(label)}:\*\*\s*(.+)$', research_text, re.MULTILINE)
        if not m or not m.group(1).strip():
            problems.append(f'missing or empty **{label}:** line')
    for block in RESEARCH_BLOCKS:
        body = _section_body(research_text, block)
        if body is None:
            problems.append(f'missing `## {block}` section')
            continue
        for sub in BLOCK_SUBSECTIONS:
            sub_body = _section_body(body, sub, depth=3)
            if not sub_body:
                problems.append(f'`## {block}` missing or empty `### {sub}`')
            elif sub == 'Sources' and not _URL_RE.search(sub_body):
                problems.append(f'`## {block}` Sources carries no URL')
    cr_body = _section_body(research_text, 'Critical Requirements')
    if cr_body is None:
        problems.append('missing `## Critical Requirements` section')
    elif not re.search(r'^\|\s*\d+\s*\|', cr_body, re.MULTILINE) \
            and not re.search(r'^- Text:', cr_body, re.MULTILINE):
        problems.append('`## Critical Requirements` carries no requirement rows')
    if _section_body(research_text, 'Axis Gaps') is None:
        problems.append('missing `## Axis Gaps` section')
    if _PENDING_RE.search(research_text):
        problems.append('pending markers or unfilled template tokens remain')
    findings.append(('I1', not problems, '; '.join(problems) or 'research file complete'))


def check_session_log(log_text, meta, findings):
    """I2: metadata fields, date form, axis classification, axis gaps."""
    problems = []
    if meta is None:
        findings.append(('I2', False, 'session log has no ## Metadata section'))
        return
    for field in METADATA_REQUIRED:
        if not meta.get(field):
            problems.append(f'metadata field {field!r} missing or empty')
    for field in METADATA_OPTIONAL:
        if field not in meta:
            problems.append(f'metadata field {field!r} line missing')
    for field in DATE_FIELDS:
        value = meta.get(field, '')
        if value and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            problems.append(f'{field} malformed: {value!r}')
    axes = _axis_values(log_text)
    if axes is None:
        problems.append('missing `## Axis Classification` section')
    else:
        missing = [a for a in AXES if not axes.get(a)]
        if missing:
            problems.append(f"axis lines missing: {', '.join(missing)}")
    if _gap_axes(log_text) is None:
        problems.append('missing `## Axis Gaps` section')
    if _PENDING_RE.search(log_text):
        problems.append('pending markers or unfilled template tokens remain')
    findings.append(('I2', not problems, '; '.join(problems) or 'session log complete'))


def check_consistency(research_text, log_text, meta, findings):
    """I3: company/role/APP-NNN equality across files; metadata Level and
    Industry equal the axis classification's values."""
    problems = []
    if meta is None:
        findings.append(('I3', False, 'session log has no ## Metadata section'))
        return
    h1 = _h1_company_role(research_text, 'Research')
    if h1 is None:
        problems.append('research H1 unparseable; company/role comparison skipped')
    else:
        if meta.get('Company', '') != h1[0]:
            problems.append(f"company diverges: session log {meta.get('Company')!r} vs research {h1[0]!r}")
        if meta.get('Role', '') != h1[1]:
            problems.append(f"role diverges: session log {meta.get('Role')!r} vs research {h1[1]!r}")
    m = re.search(r'^\*\*APP-NNN:\*\*\s*(\S+)', research_text, re.MULTILINE)
    if m and meta.get('APP-NNN', '') != m.group(1):
        problems.append(f"APP-NNN diverges: session log {meta.get('APP-NNN')!r} vs research {m.group(1)!r}")
    axes = _axis_values(log_text) or {}
    # Metadata Level/Industry are finalize-filled FROM the axis result; the
    # metadata value must appear in the axis line's value part (which may
    # carry primary/secondary annotations).
    for meta_field, axis in (('Role Level', 'Level'), ('Industry', 'Industry')):
        meta_val, axis_val = meta.get(meta_field, ''), axes.get(axis, '')
        if meta_val and axis_val and meta_val not in axis_val:
            problems.append(
                f'metadata {meta_field} {meta_val!r} not in axis classification {axis} {axis_val!r}')
    findings.append(('I3', not problems, '; '.join(problems) or 'cross-file fields consistent'))


def check_gap_mirroring(research_text, log_text, findings):
    """I4: the axes flagged as gaps match between the two files."""
    log_gaps, research_gaps = _gap_axes(log_text), _gap_axes(research_text)
    if log_gaps is None or research_gaps is None:
        findings.append(('I4', False, 'an `## Axis Gaps` section is missing (see I1/I2)'))
        return
    ok = log_gaps == research_gaps
    findings.append(('I4', ok,
                     f'gap axes diverge: session log {sorted(log_gaps)} vs research {sorted(research_gaps)}'
                     if not ok else 'axis gaps mirrored'))


# ---------------------------------------------------------------------------
# Command: check
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Run all checks against one application folder; print report; return exit code."""
    fn = cfg['filenames']
    app_folder = args.folder

    research_text = _read(os.path.join(app_folder, fn['research_file']))
    log_text = _read(os.path.join(app_folder, fn['session_log_file']))
    if research_text is None or log_text is None:
        missing = fn['research_file'] if research_text is None else fn['session_log_file']
        print(f'FATAL  {missing} not found in {app_folder}')
        return 1

    meta = _metadata_fields(log_text)

    findings = []
    check_research(research_text, findings)
    check_session_log(log_text, meta, findings)
    check_consistency(research_text, log_text, meta, findings)
    check_gap_mirroring(research_text, log_text, findings)

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
        description='Deterministic QC for role-intake artifacts.')
    sub = parser.add_subparsers(dest='command', required=True)
    p_check = sub.add_parser('check', help='validate one application folder')
    p_check.add_argument('--folder', required=True,
                         help='absolute path to the application folder')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    if args.command == 'check':
        sys.exit(cmd_check(args, repo_root, cfg))


if __name__ == '__main__':
    main()
