#!/usr/bin/env python3
"""
role_classify_assemble.py - role-classify artifact writer

Writes what the role-classify skill adds to an application that role-intake
has already researched, and prints the skill's approval block, so none of it is
written or composed by hand. Three subcommands:

  needs     Write the jd-needs-ranker output into research.md's Ranked Needs
            section.
  finalize  Write the axis-classifier output into the session log (Axis
            Classification, Axis Gaps, and the Role Level and Industry metadata
            lines) and mirror Axis Gaps into research.md.
  approval  Print the approval block from the files on disk.

needs and finalize moved here from assemble.py when role-classify was split out
of role-intake. Every write is section-scoped, so sections other skills own are
left in place.

Author    : Jason Delosh
Created   : 2026-11-09
Project   : career
Usage     : python scripts/role_classify_assemble.py needs     --folder ... --needs-file ...
            python scripts/role_classify_assemble.py finalize  --folder ... --axis-file ...
            python scripts/role_classify_assemble.py approval  --folder ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
from assemble import _replace_section, _upsert_section
from role_intake_qc import _metadata_fields, _section_body


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
            raise FileNotFoundError(f'{path} not found (run role-intake first)')
    return research, log


# ---------------------------------------------------------------------------
# Subcommand: needs
# Structure and coverage are checked by role_classify_qc.py C6, not here, so a
# malformed ranking still lands where QC can name what is wrong with it.
# ---------------------------------------------------------------------------

def cmd_needs(args, cfg):
    research, _ = _paths(args.folder, cfg)
    block = _util.read(args.needs_file).strip()
    if not re.match(r'^## Ranked Needs[ \t]*\n', block):
        raise ValueError('needs file must open with the "## Ranked Needs" heading')
    _util.write(research, _upsert_section(_util.read(research), 'Ranked Needs', block))
    print(research)


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
    research, log = _paths(args.folder, cfg)
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

    _util.write(research, _replace_section(_util.read(research), 'Axis Gaps', gaps_section))
    print(research)


# ---------------------------------------------------------------------------
# Subcommand: approval
# Prints the block the user approves at the end of role-classify. It shows only
# what is on disk; the skill decides QC findings and the ranking first.
# ---------------------------------------------------------------------------

def cmd_approval(args, cfg):
    research, log = _paths(args.folder, cfg)
    log_text = _util.read(log)
    meta = _metadata_fields(log_text) or {}
    axes = _section_body(log_text, 'Axis Classification') or '_(missing)_'
    gaps = _section_body(log_text, 'Axis Gaps') or '_(missing)_'
    needs = _section_body(_util.read(research), 'Ranked Needs') or ''
    need_count = len(re.findall(r'(?m)^\|\s*N-\d+\s*\|', needs))
    print('\n'.join([
        f"Role:     {meta.get('Role', '')} at {meta.get('Company', '')}",
        f"Level:    {meta.get('Role Level', '')}",
        f"Industry: {meta.get('Industry', '')}",
        '',
        'Axis classification:',
        axes,
        '',
        f'Axis gaps: {gaps}',
        f'Ranked needs: {need_count}',
        f'Files: {log}',
        f'       {research}',
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

    p_needs = sub.add_parser('needs', help="write the ranker's output into research.md")
    p_needs.add_argument('--folder', required=True, help='the application folder')
    p_needs.add_argument('--needs-file', required=True,
                         help='path to a file holding the jd-needs-ranker output block')
    p_needs.set_defaults(func=cmd_needs)

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
        _, cfg = _config.load()
        args.func(args, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
