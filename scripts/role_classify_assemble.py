#!/usr/bin/env python3
"""
role_classify_assemble.py - role-classify artifact writer

Writes what the role-classify skill adds to an application that role-research
has already researched, and prints the skill's approval block, so none of it is
written or composed by hand. Two subcommands:

  finalize  Write the axis-classifier output into the session log (Axis
            Classification, Axis Gaps, and the Role Level and Industry metadata
            lines). Axis Gaps is not copied into research.md (2026-11-17).
  approval  Print the approval block from the files on disk.

finalize moved here from assemble.py when role-classify was split out of
role-intake. The requirements and needs commands moved to
role_extract_assemble.py when role-extract was split out (2026-11-16). Every
write is section-scoped, so sections other skills own are left in place.

Author    : Jason Delosh
Created   : 2026-11-09
Project   : career
Usage     : python scripts/role_classify_assemble.py finalize  --folder ... --axis-file ...
            python scripts/role_classify_assemble.py approval  --folder ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import jd_extraction_tables
from assemble import _replace_section
from role_research_qc import _metadata_fields, _section_body


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _paths(folder, cfg):
    """Return (research.md path, session log path), failing if either is missing."""
    fn = cfg['filenames']
    research = os.path.join(folder, fn['research_file'])
    log = os.path.join(folder, fn['session_log_file'])
    for path in (research, log):
        if not os.path.exists(path):
            raise FileNotFoundError(f'{path} not found (run role-intake and role-research first)')
    return research, log


# ---------------------------------------------------------------------------
# Subcommand: finalize
# ---------------------------------------------------------------------------

# Regex: an axis label in any form the classifier has emitted - with or without
# the leading bullet, with or without bold markers around the label.
_AXIS_LINE_RE = re.compile(
    r'^-?\s*\*{0,2}(Orientation|Industry|Specialty|Level|Work-state):\*{0,2}'
    r'\s*(.*)$')


def _normalize_axis_lines(body):
    """Return an axis block rewritten into the classifier's declared form.

    The classifier's return-format spec emits `- <Axis>: <values> - <rationale>`
    with a bare label and a plain-hyphen separator, but it has drifted to bolded
    labels, missing bullets, and em dash separators across runs. Normalizing on
    the way in means the session log always carries the spec form no matter what
    the subagent produced, so every downstream reader (staging_append.py,
    retrieval_qc.py, role_classify_qc.py check C4) has one shape to match.

    Lines carrying no axis label pass through untouched, so sub-bullets the
    classifier adds are preserved rather than silently dropped.
    """
    out = []
    for line in body.split('\n'):
        m = _AXIS_LINE_RE.match(line)
        if not m:
            out.append(line)
            continue
        # Only the FIRST em dash is the value/rationale separator; any later one
        # sits inside the rationale prose and is left alone.
        rest = m.group(2).replace(' — ', ' - ', 1)
        out.append(f'- {m.group(1)}: {rest}')
    return '\n'.join(out)


def cmd_finalize(args, cfg):
    _, log = _paths(args.folder, cfg)
    text = _util.read(log)

    # Split the axis file into classification lines and gaps lines. The classifier
    # may emit either '## Axis Gaps' (heading form) or 'Axis gaps:' (inline form);
    # accept both so the split is reliable regardless of classifier output style.
    axis_text = _util.read(args.axis_file).strip()
    parts = re.compile(r'(?mi)^(?:##\s+)?Axis\s+Gaps:?\s*$').split(axis_text, maxsplit=1)

    # The classifier emits its own '## Axis Classification' heading; strip it so
    # the heading re-added below is not duplicated.
    classification_body = re.sub(
        r'(?i)\A##[ \t]+Axis[ \t]+Classification[ \t]*\n+', '', parts[0].strip()).strip()
    classification_body = _normalize_axis_lines(classification_body)
    gaps_body = _normalize_axis_lines(parts[1].strip()) if len(parts) > 1 else ''
    gaps_content = 'None' if not gaps_body or gaps_body.lower() == 'none' else gaps_body

    # Fill the Role Level and Industry metadata lines from the axis result. The
    # classifier line is '<value> - <rationale>'; keep only the value. Lambda
    # replacements so a value is never read as a regex template.
    for axis, field in (('Level', 'Role Level'), ('Industry', 'Industry')):
        m = re.search(rf'(?m)^- {axis}:[ \t]*(.+)$', classification_body)
        if m:
            value = re.split(r'[ \t]+-[ \t]+', m.group(1).strip(), maxsplit=1)[0].strip()
            text = re.sub(rf'(?m)^- {field}: .*$', lambda _m: f'- {field}: {value}', text)

    gaps_section = f'## Axis Gaps\n\n{gaps_content}'
    text = _replace_section(text, 'Axis Classification',
                            f'## Axis Classification\n\n{classification_body}')
    text = _replace_section(text, 'Axis Gaps', gaps_section)
    _util.write(log, text)
    print(log)


# ---------------------------------------------------------------------------
# Subcommand: approval
# Prints the block the user approves at the end of role-classify. It shows only
# what is on disk; the skill decides QC findings and the ranking first.
# ---------------------------------------------------------------------------

def _axis_value_lines(axes_body):
    """Return {label: values} from Axis Classification lines, rationale dropped.

    The values part runs up to the first ' - '; '(primary)' and '(secondary)'
    markers are dropped, since order already says which is which.
    """
    out = {}
    for line in axes_body.split('\n'):
        m = re.match(r'^- (Orientation|Industry|Specialty|Level|Tier|Work-state):\s*(.+)$', line.strip())
        if m:
            values = m.group(2).split(' - ')[0]
            out[m.group(1)] = re.sub(r'\s*\((?:primary|secondary)\)', '', values).strip()
    return out


def cmd_approval(args, cfg):
    """Print the approval block: the values only. The rationales stay in the
    session log for the reviewer; the block once ran past 400 words."""
    _, log = _paths(args.folder, cfg)
    log_text = _util.read(log)
    meta = _metadata_fields(log_text) or {}
    axes = _axis_value_lines(_section_body(log_text, 'Axis Classification') or '')
    gaps = (_section_body(log_text, 'Axis Gaps') or '_(missing)_').strip()
    needs_file = jd_extraction_tables.needs_path(args.folder, cfg)
    needs = _util.read(needs_file) if os.path.isfile(needs_file) else ''
    need_count = len(jd_extraction_tables.read_needs(needs)['needs'])
    level = meta.get('Role Level', '')
    if axes.get('Tier'):
        level = f"{level}, {axes['Tier']}"
    print('\n'.join([
        f"Role:         {meta.get('Role', '')} at {meta.get('Company', '')}",
        f'Level:        {level}',
        f"Industry:     {meta.get('Industry', '')}",
        f"Orientation:  {axes.get('Orientation', '_(missing)_')}",
        f"Specialty:    {axes.get('Specialty', '_(missing)_')}",
        f"Work-state:   {axes.get('Work-state', '_(missing)_')}",
        f'Axis gaps:    {gaps}',
        f'Ranked needs: {need_count}',
        '',
        'Reply with corrections, or "approved" to hand off.',
    ]))


# ---------------------------------------------------------------------------
# Command-line entry point
# A failure goes to stderr with a non-zero exit so the skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='role-classify artifact writer')
    sub = parser.add_subparsers(dest='command', required=True)

    p_fin = sub.add_parser('finalize', help="write the classifier's output into the session log")
    p_fin.add_argument('--folder', required=True, help='the application folder')
    p_fin.add_argument('--axis-file', required=True,
                       help='path to a file holding the axis-classifier output block')
    p_fin.set_defaults(func=cmd_finalize)

    p_app = sub.add_parser('approval', help='print the approval block')
    p_app.add_argument('--folder', required=True, help='the application folder')
    p_app.set_defaults(func=cmd_approval)

    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        args.repo_root, cfg = _config.load()
        args.func(args, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
