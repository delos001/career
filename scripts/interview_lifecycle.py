#!/usr/bin/env python3
"""
interview_lifecycle.py - reschedule / cancel sync for the preparation-interview skill

An interview lives in three files: session_log.md (the event record), the prep
Appendix block in interview_prep.md, and the round section in interview_notes.md.
A reschedule or cancellation must reach all three or they drift. This script is
the small deterministic op that keeps them in sync.

Scope is deliberately narrow (no bloat): it ANNOTATES an existing interview's
section in each file and, in the session log, flips the Outcome line and adds a
dated audit bullet. It never deletes a block - a cancelled interview may be
rescheduled and the history matters. Interviewer name/title tweaks are trivial
manual edits; structural changes (single -> panel, add/remove interviewer) are
handled by the skill plus the interview-notes AMEND flow, not here.

Sections are matched by the human stage label (e.g. "Hiring Manager"), which is
the one key common to all three files' headings. If more than one section in a
file matches the label, pass --date to disambiguate, or edit that file by hand.

Subcommands
  reschedule  record a new date/time across the three files.
  cancel      mark the interview cancelled across the three files, and tag the
              notes round heading [CANCELLED <date>] so it is visible in outline.

Usage
  python interview_lifecycle.py reschedule --folder <app-folder>
      --stage "Hiring Manager" --new-datetime "2026-07-10 14:00 EST" [--date 2026-07-02] [--reason "..."]
  python interview_lifecycle.py cancel --folder <app-folder>
      --stage "Hiring Manager" [--date 2026-07-02] [--reason "..."]

Exit code 0 if at least one section was updated, 1 on error or no match.

Author    : Jason Delosh
Created   : 2026-07-02
Project   : career
Depends   : pyyaml (via _config)
"""

import argparse
import os
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Section location
# Every heading of interest is a level-2 '## ' line containing the stage label.
# restrict_after limits the search to lines after a marker line (used to scope
# interview_prep.md matching to the '# APPENDIX' region, so a main-body heading
# can never match). date, when given, must also appear in the heading text
# (present in the notes '## <stage> | <date>' and prep '(<date>, ...)' headings).
# ---------------------------------------------------------------------------

def _heading_matches(lines, stage, date, restrict_after=None, require_token=None):
    """Return the indices of '## ' heading lines that identify the interview."""
    start = 0
    if restrict_after is not None:
        start = next((i for i, l in enumerate(lines)
                      if l.strip().startswith(restrict_after)), None)
        if start is None:
            return []  # marker absent -> region does not exist yet
    out = []
    for i in range(start, len(lines)):
        line = lines[i]
        if not line.startswith('## ') or stage not in line:
            continue
        if date is not None and date not in line:
            continue
        if require_token is not None and require_token not in line:
            continue
        out.append(i)
    return out


def _section_end(lines, heading_idx):
    """Index one past the section: the next '## '/'# ' heading, or end of file."""
    for j in range(heading_idx + 1, len(lines)):
        if lines[j].startswith('## ') or lines[j].startswith('# '):
            return j
    return len(lines)


# ---------------------------------------------------------------------------
# Per-file edits
# _annotate inserts a bold status line just under a section heading (prep and
# notes). _edit_session_log flips the Outcome line and adds a dated audit
# bullet inside the '## Interview: <stage>' section. Both are idempotent: a
# re-run that would repeat the same annotation is skipped, not duplicated.
# ---------------------------------------------------------------------------

def _annotate(folder, filename, stage, date, annotation,
              restrict_after=None, label=None):
    """Insert a bold status line under the interview's heading in one file."""
    label = label or filename
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        return (label, 'skipped (file missing)')
    lines = _util.read(path).split('\n')
    hits = _heading_matches(lines, stage, date, restrict_after=restrict_after)
    if not hits:
        return (label, 'section not found')
    if len(hits) > 1:
        return (label, f'{len(hits)} sections match "{stage}"; '
                       f'pass --date or edit manually')
    h = hits[0]
    end = _section_end(lines, h)
    if any(annotation == lines[k].strip() for k in range(h, end)):
        return (label, 'already annotated (skipped)')
    lines[h + 1:h + 1] = ['', annotation]
    _util.write(path, '\n'.join(lines))
    return (label, 'annotated')


def _tag_notes_heading(folder, filename, stage, date, tag):
    """Append a bracketed status tag to the notes round heading.

    Outline view shows only heading lines, so the bold annotation under a
    heading is invisible when navigating by outline; this puts the status in the
    heading itself (e.g. '## 1. Hiring Manager | 2026-07-02 [CANCELLED ...]').
    Idempotent: a heading already carrying a bracketed tag is left untouched.
    """
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        return (filename, 'skipped (file missing)')
    lines = _util.read(path).split('\n')
    hits = _heading_matches(lines, stage, date)
    if not hits:
        return (filename, 'section not found')
    if len(hits) > 1:
        return (filename, f'{len(hits)} sections match "{stage}"; '
                          f'pass --date or edit manually')
    h = hits[0]
    if '[' in lines[h]:
        return (filename, 'heading already tagged (skipped)')
    lines[h] = lines[h].rstrip() + f' {tag}'
    _util.write(path, '\n'.join(lines))
    return (filename, 'heading tagged')


def _edit_session_log(folder, cfg, stage, outcome_line, audit_bullet):
    """Update Outcome and add an audit bullet in '## Interview: <stage>'."""
    label = cfg['filenames']['session_log_file']
    path = os.path.join(folder, label)
    if not os.path.isfile(path):
        return (label, 'skipped (file missing)')
    lines = _util.read(path).split('\n')
    # Session-log interview headings are '## Interview: <stage>'; require the
    # 'Interview:' token so a same-named non-interview heading cannot match.
    hits = _heading_matches(lines, stage, None, require_token='Interview:')
    if not hits:
        return (label, 'section not found')
    if len(hits) > 1:
        return (label, f'{len(hits)} interview sections match "{stage}"; '
                       f'edit manually')
    h = hits[0]
    end = _section_end(lines, h)
    if any(audit_bullet == lines[k].strip() for k in range(h, end)):
        return (label, 'already recorded (skipped)')
    outcome_idx = next((k for k in range(h, end)
                        if lines[k].startswith('- Outcome:')), None)
    if outcome_idx is not None:
        lines[outcome_idx] = outcome_line          # flip current state
        lines[outcome_idx:outcome_idx] = [audit_bullet]  # audit above it
    else:
        # No Outcome line: append audit + outcome after the last content line.
        last = max((k for k in range(h, end) if lines[k].strip()), default=h)
        lines[last + 1:last + 1] = [audit_bullet, outcome_line]
    _util.write(path, '\n'.join(lines))
    return (label, 'updated')


# ---------------------------------------------------------------------------
# Apply an action across the three files
# ---------------------------------------------------------------------------

def _apply(action, args, cfg):
    """Build the action's text and edit session log, prep Appendix, and notes."""
    folder = os.path.abspath(args.folder)
    today = _util.today_iso()
    suffix = f' ({args.reason})' if args.reason else ''

    if action == 'reschedule':
        annotation = f'**RESCHEDULED {today}: now {args.new_datetime}{suffix}**'
        outcome_line = (f'- Outcome: pending '
                        f'(rescheduled {today} to {args.new_datetime})')
        audit_bullet = (f'- Lifecycle ({today}): rescheduled to '
                        f'{args.new_datetime}{suffix}')
        heading_tag = None
    else:  # cancel
        annotation = f'**CANCELLED {today}{suffix}**'
        outcome_line = f'- Outcome: cancelled {today}{suffix}'
        audit_bullet = f'- Lifecycle ({today}): cancelled{suffix}'
        heading_tag = f'[CANCELLED {today}]'

    results = [
        _edit_session_log(folder, cfg, args.stage, outcome_line, audit_bullet),
        _annotate(folder, cfg['filenames']['interview_prep_file'], args.stage,
                  args.date, annotation, restrict_after='# APPENDIX',
                  label=cfg['filenames']['interview_prep_file']),
        _annotate(folder, cfg['filenames']['interview_notes_file'], args.stage,
                  args.date, annotation,
                  label=cfg['filenames']['interview_notes_file']),
    ]

    # On cancel, also tag the notes round heading so the status is visible in
    # outline view (the bold annotation above lives below the heading line).
    if heading_tag is not None:
        results.append(_tag_notes_heading(
            folder, cfg['filenames']['interview_notes_file'],
            args.stage, args.date, heading_tag))

    changed = {'annotated', 'updated', 'heading tagged',
               'already annotated (skipped)', 'already recorded (skipped)',
               'heading already tagged (skipped)'}
    any_changed = False
    for name, status in results:
        print(f'  {name}: {status}')
        if status in changed:
            any_changed = True
    if not any_changed:
        raise ValueError(f'no interview section matched stage "{args.stage}" '
                         f'in any file')
    print(f'{action}: done')


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch the subcommand."""
    parser = argparse.ArgumentParser(
        description='reschedule/cancel sync across the interview artifacts')
    sub = parser.add_subparsers(dest='command', required=True)

    p_re = sub.add_parser('reschedule', help='record a new date/time')
    p_re.add_argument('--folder', required=True,
                      help='absolute path to the application folder')
    p_re.add_argument('--stage', required=True,
                      help='stage label as it appears in the headings, e.g. "Hiring Manager"')
    p_re.add_argument('--new-datetime', required=True, dest='new_datetime',
                      help='the new date/time, e.g. "2026-07-10 14:00 EST"')
    p_re.add_argument('--date', default=None,
                      help='current date of the target section, to disambiguate duplicates')
    p_re.add_argument('--reason', default=None)
    p_re.set_defaults(action='reschedule')

    p_ca = sub.add_parser('cancel', help='mark the interview cancelled')
    p_ca.add_argument('--folder', required=True,
                      help='absolute path to the application folder')
    p_ca.add_argument('--stage', required=True,
                      help='stage label as it appears in the headings, e.g. "Hiring Manager"')
    p_ca.add_argument('--date', default=None,
                      help='current date of the target section, to disambiguate duplicates')
    p_ca.add_argument('--reason', default=None)
    p_ca.set_defaults(action='cancel', new_datetime=None)

    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        _repo_root, cfg = _config.load()
        _apply(args.action, args, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
