#!/usr/bin/env python3
"""
role_classify_assemble.py - role-classify artifact writer

Writes what the role-classify skill adds to an application that role-intake
has already researched, and prints the skill's approval block, so none of it is
written or composed by hand. Four subcommands:

  requirements  Write the critical-requirements-extractor output to jd_needs.md
            under '## Requirements' (text, Type, Source). Re-extracting
            replaces the whole file, so a ranking built on old rows never
            survives.
  needs     Rewrite jd_needs.md with the jd-needs-ranker output: the job, each
            need with its requirements (copied from the file's own rows) and
            their kinds, then the Qualifications and Not ranked rows.
  finalize  Write the axis-classifier output into the session log (Axis
            Classification, Axis Gaps, and the Role Level and Industry metadata
            lines) and mirror Axis Gaps into research.md.
  approval  Print the approval block from the files on disk.

needs and finalize moved here from assemble.py when role-classify was split out
of role-intake; requirements moved here from assemble.py research when
extraction moved into role-classify (2026-11-10). Every write is section-scoped, so sections other skills own are
left in place.

Author    : Jason Delosh
Created   : 2026-11-09
Project   : career
Usage     : python scripts/role_classify_assemble.py requirements --folder ... --requirements-file ...
            python scripts/role_classify_assemble.py needs     --folder ... --needs-file ...
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
import requirement_kinds
from assemble import _replace_section
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


def _title(research):
    """Return '<Company> | <Role>' from research.md's H1."""
    m = re.match(r'# Research: (.*)', _util.read(research))
    if not m:
        raise ValueError(f'{research} has no "# Research: <company> | <role>" heading')
    return m.group(1).strip()


# ---------------------------------------------------------------------------
# Subcommand: requirements
# Type values are held to the allowed four here; wording against the JD is
# role_classify_qc.py's 'requirements' check, run right after this write.
# ---------------------------------------------------------------------------

def cmd_requirements(args, cfg):
    """Write the extractor's rows to jd_needs.md, replacing any earlier file."""
    research, _ = _paths(args.folder, cfg)
    rows = requirement_kinds.parse_extractor_table(_util.read(args.requirements_file))
    if not rows:
        raise ValueError('the extractor output holds no requirement rows')
    path = requirement_kinds.needs_path(args.folder, cfg)
    _util.write(path, requirement_kinds.render_requirements(_title(research), rows))
    print(path)


# ---------------------------------------------------------------------------
# Subcommand: needs
# Structure and coverage are checked by role_classify_qc.py C6, not here, so a
# malformed ranking still lands where QC can name what is wrong with it. A row
# the ranker placed nowhere stays under '## Requirements' for C6 to report.
# ---------------------------------------------------------------------------

def _row_kinds(block):
    """Return {row number: Kind cell} from the ranker's '## Row Kinds' table."""
    kinds = {}
    for line in block.split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if line.strip().startswith('|') and len(cells) >= 2 and cells[0].isdigit():
            kinds[int(cells[0])] = ' | '.join(cells[1:])
    return kinds


def _line_rows(block, label):
    """Return the row numbers on a '**<label>:** 3, 7 (kind), ...' line."""
    m = re.search(rf'(?m)^\*\*{label}:\*\*[ \t]*(.*)$', block)
    if m is None:
        raise ValueError(f'ranker output has no "**{label}:**" line')
    return [int(n) for n in re.findall(r'(?<![\w(-])(\d+)(?![\w)])', m.group(1))]


def cmd_needs(args, cfg):
    """Rewrite jd_needs.md from the ranker's output and the file's own rows.

    The ranker returns '## Row Kinds' (a row-number/kind table), then
    '## Ranked Needs' (the job lines, the needs table, and the Qualifications
    and Not ranked lines). Each requirement's text, Type and Source are copied
    from jd_needs.md's existing rows, never from the ranker, so the requirements
    are never reworded by ranking. A row number the file does not have stops the
    write; a row the ranker placed nowhere is kept under '## Requirements'.
    """
    _paths(args.folder, cfg)
    path = requirement_kinds.needs_path(args.folder, cfg)
    if not os.path.isfile(path):
        raise FileNotFoundError(f'{path} not found (extract the requirements first)')
    current = requirement_kinds.read_needs(_util.read(path))
    by_num = {row['num']: row for row in requirement_kinds.all_rows(current)}
    text = _util.read(args.needs_file).strip()
    m = re.search(r'(?m)^## Ranked Needs[ \t]*$', text)
    if not m:
        raise ValueError('needs file has no "## Ranked Needs" heading')
    kinds_part, block = text[:m.start()], text[m.start():]
    kind_by_row = _row_kinds(kinds_part)
    placed = set()

    def rows(nums):
        unknown = [n for n in nums if n not in by_num]
        if unknown:
            raise ValueError(f"row(s) {', '.join(map(str, unknown))} are not in {path}")
        placed.update(nums)
        return [{**by_num[n], 'kind': kind_by_row.get(n, '')} for n in nums]

    job = [line.strip() for line in block.split('\n')
           if re.match(r'^- (Delivers or owns|Leads, does, or both):', line.strip())]
    needs = []
    for line in block.split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 6 or not re.fullmatch(r'N-\d+', cells[0]):
            continue
        nums = [int(t) for t in re.split(r'[,\s]+', cells[3]) if t.isdigit()]
        needs.append({'id': cells[0], 'label': cells[1], 'basis': cells[2],
                      'signals': cells[4], 'quote': ' | '.join(cells[5:]), 'rows': rows(nums)})
    qualifications = rows(_line_rows(block, 'Qualifications'))
    not_ranked = rows(_line_rows(block, 'Not ranked'))
    unplaced = [row for num, row in sorted(by_num.items()) if num not in placed]
    out = requirement_kinds.render_needs(current['title'], job, needs, qualifications,
                                         not_ranked, unplaced)
    _util.write(path, out)
    print(path)


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
    needs_file = requirement_kinds.needs_path(args.folder, cfg)
    needs = _util.read(needs_file) if os.path.isfile(needs_file) else ''
    need_count = len(requirement_kinds.read_needs(needs)['needs'])
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
        f'       {needs_file}',
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

    p_req = sub.add_parser('requirements', help="write the extractor's rows to jd_needs.md")
    p_req.add_argument('--folder', required=True, help='the application folder')
    p_req.add_argument('--requirements-file', required=True,
                       help='path to a file holding the critical-requirements-extractor output table')
    p_req.set_defaults(func=cmd_requirements)

    p_needs = sub.add_parser('needs', help="rewrite jd_needs.md with the ranker's output")
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
