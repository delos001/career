#!/usr/bin/env python3
"""
interview_lifecycle.py - reschedule / cancel sync for the preparation-interview skill

An interview's scheduling metadata has ONE home: the `## Interview: <stage>`
section of session_log.md, whose field set is defined by templates/session_log.md.
The notes file carries a capture line and an outline-visible tag; the prep doc
carries no scheduling facts at all. This script keeps the two files that hold
event state in sync when an interview moves or dies.

  session_log.md      the record. Reschedule rewrites 'Interview date:', 'Time:'
                      (when a time is given) and the one-line 'Schedule history:'
                      field. Cancel sets 'Status:' and 'Outcome:'. Sections hold
                      current state, never an accumulating audit trail.
  interview_notes.md  the capture surface. Reschedule appends to the round's
                      '- Schedule changes:' line; cancel tags the round heading
                      '[CANCELLED <date>]' so an empty section explains itself in
                      outline view. The round heading's date is the section's
                      identity for duplicate detection and amend, never rewritten.
  interview_prep.md   NOT TOUCHED. Prep content does not change when a date moves,
                      and a stale date in the doc the candidate reads before an
                      interview is worse than no date.

Scope is deliberately narrow (no bloat). It never deletes a block; a cancelled
interview may be rescheduled and the history matters. Interviewer name/title
tweaks are trivial manual edits; structural changes (single -> panel,
add/remove interviewer) are handled by the skill plus the interview-notes AMEND
flow, not here.

Cancel has no downstream skill to catch it (a cancelled round never reaches the
follow-up skill), so running `cancel` at the time is the accurate capture path;
`close-application` verifies the record at close-out as a backstop. Reschedule is
a convenience: the follow-up skill reconciles the date from the notes round's
'Schedule changes:' line if this was never run.

Sections are matched by the human stage label (e.g. "Hiring Manager"), which is
the one key common to both files' headings. If more than one section in a file
matches the label, pass --date to disambiguate, or edit that file by hand.

Subcommands
  reschedule  rewrite the session-log date/time and schedule-history fields, and
              append to the notes round's 'Schedule changes:' line.
  cancel      set the session-log Status and Outcome, and tag the notes round
              heading [CANCELLED <date>].

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
import re
import sys

import _config
import _util


# An ISO date anywhere in a line (the identity date of a notes round heading).
_DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}')

# '--new-datetime' is "<YYYY-MM-DD> [HH:MM tz...]"; the date is required, the
# rest is an optional time that lands in the session log's 'Time:' field.
_DATETIME_RE = re.compile(r'^\s*(\d{4}-\d{2}-\d{2})\s*(.*?)\s*$')


# ---------------------------------------------------------------------------
# Section location
# Every heading of interest is a level-2 '## ' line containing the stage label.
# date, when given, must also appear in the heading text (present in the notes
# '## <N>. <stage> | <date>' heading). require_token scopes the session-log
# match to '## Interview: <stage>' so a same-named non-interview heading cannot
# match.
# ---------------------------------------------------------------------------

def _heading_matches(lines, stage, date, require_token=None):
    """Return the indices of '## ' heading lines that identify the interview."""
    out = []
    for i, line in enumerate(lines):
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


def _locate(folder, filename, stage, date, require_token=None):
    """Resolve one interview's heading line in one file.

    Returns (lines, heading_index, None) on a unique match, or
    (None, None, status_string) describing why no edit can be made.
    """
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        return (None, None, 'skipped (file missing)')
    lines = _util.read(path).split('\n')
    hits = _heading_matches(lines, stage, date, require_token=require_token)
    if not hits:
        return (None, None, 'section not found')
    if len(hits) > 1:
        return (None, None, f'{len(hits)} sections match "{stage}"; '
                            f'pass --date or edit manually')
    return (lines, hits[0], None)


def _field_index(lines, start, end, label):
    """Index of the '- <label>:' line within [start, end), or None."""
    return next((k for k in range(start, end)
                 if lines[k].strip().startswith(f'- {label}:')), None)


def _field_value(line):
    """The text after '- Label:' on a field line."""
    return line.split(':', 1)[1].strip()


# ---------------------------------------------------------------------------
# Per-file edits
# Idempotent: a re-run that would produce identical content reports 'skipped'.
# ---------------------------------------------------------------------------

_CANCELLED_OUTCOME = 'n/a (round cancelled)'
_CANCELLED_TAG_RE = re.compile(r'\s*\[CANCELLED[^\]]*\]')


def _edit_session_log(folder, cfg, stage, updates, appends, revive_outcome=False):
    """Set the given session-log fields on the round's '## Interview: <stage>'.

    updates: {label: new_value}   replace the field's value outright.
    appends: {label: fragment}    append '; fragment' to the field's current
                                  value (used for the current-state one-line
                                  'Schedule history:' field), or set it when blank.
    Fields named here must exist in the section; the template defines the set, so
    a missing field means the section was written against an older shape.
    """
    label_name = cfg['filenames']['session_log_file']
    lines, h, err = _locate(folder, label_name, stage, None,
                            require_token='Interview:')
    if err:
        return (label_name, err)
    end = _section_end(lines, h)

    missing = [lbl for lbl in list(updates) + list(appends)
               if _field_index(lines, h, end, lbl) is None]
    if missing:
        return (label_name, f'section missing field(s) {missing}; '
                            f'convert it to the current template shape')

    changed = False
    # Rescheduling a cancelled round revives it. Clear the cancellation marker in
    # Outcome, but only that exact marker: a real recorded outcome is never
    # overwritten by a scheduling operation.
    if revive_outcome:
        k = _field_index(lines, h, end, 'Outcome')
        if k is not None and _field_value(lines[k]).startswith(_CANCELLED_OUTCOME):
            lines[k] = '- Outcome: pending'
            changed = True

    for lbl, value in updates.items():
        k = _field_index(lines, h, end, lbl)
        new = f'- {lbl}: {value}'
        if lines[k].rstrip() != new:
            lines[k] = new
            changed = True
    for lbl, fragment in appends.items():
        k = _field_index(lines, h, end, lbl)
        current = _field_value(lines[k])
        if fragment in current:
            continue
        lines[k] = (f'- {lbl}: {current}; {fragment}' if current
                    else f'- {lbl}: {fragment}')
        changed = True

    if not changed:
        return (label_name, 'already current (skipped)')
    _util.write(os.path.join(folder, label_name), '\n'.join(lines))
    return (label_name, 'updated')


def _note_schedule_change(folder, filename, stage, date, moved_to, suffix):
    """Append to the notes round block's '- Schedule changes:' capture line.

    The round heading's date stays frozen as the section's identity; this line
    carries the move. Appends to any text the user hand-filled rather than
    replacing it.
    """
    lines, h, err = _locate(folder, filename, stage, date)
    if err:
        return (filename, err)
    end = _section_end(lines, h)
    idx = _field_index(lines, h, end, 'Schedule changes')
    if idx is None:
        return (filename, 'no "- Schedule changes:" line in the round block')

    existing = _field_value(lines[idx])
    # Name the original date only on the first entry; once the line carries
    # history, "originally" has already been stated.
    original = _DATE_RE.search(lines[h])
    entry = f'moved to {moved_to}{suffix}'
    if not existing and original:
        entry = f'originally {original.group(0)}; {entry}'
    if entry in existing:
        return (filename, 'already recorded (skipped)')
    lines[idx] = (f'- Schedule changes: {existing}; {entry}' if existing
                  else f'- Schedule changes: {entry}')
    _util.write(os.path.join(folder, filename), '\n'.join(lines))
    return (filename, 'schedule change recorded')


def _tag_notes_heading(folder, filename, stage, date, tag):
    """Append a bracketed status tag to the notes round heading.

    Outline view shows only heading lines, and a cancelled round leaves an empty
    section; the tag explains the emptiness. Idempotent.
    """
    lines, h, err = _locate(folder, filename, stage, date)
    if err:
        return (filename, err)
    if '[' in lines[h]:
        return (filename, 'heading already tagged (skipped)')
    lines[h] = lines[h].rstrip() + f' {tag}'
    _util.write(os.path.join(folder, filename), '\n'.join(lines))
    return (filename, 'heading tagged')


def _untag_cancelled(folder, filename, stage, date):
    """Strip a '[CANCELLED ...]' tag from the notes round heading on a reschedule.

    A revived round is no longer cancelled. Only that tag is removed; hand-added
    tags such as [NO-SHOW] are left alone.
    """
    lines, h, err = _locate(folder, filename, stage, date)
    if err:
        return (filename, err)
    if not _CANCELLED_TAG_RE.search(lines[h]):
        return (filename, 'no cancellation tag (skipped)')
    lines[h] = _CANCELLED_TAG_RE.sub('', lines[h]).rstrip()
    _util.write(os.path.join(folder, filename), '\n'.join(lines))
    return (filename, 'cancellation tag cleared')


# ---------------------------------------------------------------------------
# Apply an action across the two files that hold event state
# ---------------------------------------------------------------------------

def _apply(action, args, cfg):
    """Build the action's field values and edit the session log and the notes."""
    folder = os.path.abspath(args.folder)
    fn = cfg['filenames']
    today = _util.today_iso()
    suffix = f' ({args.reason})' if args.reason else ''

    if action == 'reschedule':
        m = _DATETIME_RE.match(args.new_datetime)
        if not m:
            raise ValueError('--new-datetime must start with YYYY-MM-DD, '
                             f'got "{args.new_datetime}"')
        new_date, new_time = m.group(1), m.group(2)
        updates = {'Interview date': new_date, 'Status': 'scheduled'}
        if new_time:
            updates['Time'] = new_time
        results = [
            _edit_session_log(folder, cfg, args.stage, updates,
                              appends={'Schedule history':
                                       f'moved to {new_date}{suffix}'},
                              revive_outcome=True),
            _note_schedule_change(folder, fn['interview_notes_file'], args.stage,
                                  args.date, args.new_datetime, suffix),
            _untag_cancelled(folder, fn['interview_notes_file'], args.stage,
                             args.date),
        ]
    else:  # cancel
        results = [
            _edit_session_log(folder, cfg, args.stage,
                              updates={'Status': f'cancelled {today}{suffix}',
                                       'Outcome': _CANCELLED_OUTCOME},
                              appends={}),
            _tag_notes_heading(folder, fn['interview_notes_file'], args.stage,
                               args.date, f'[CANCELLED {today}]'),
        ]

    changed = {'updated', 'heading tagged', 'schedule change recorded',
               'cancellation tag cleared', 'already current (skipped)',
               'already recorded (skipped)', 'heading already tagged (skipped)',
               'no cancellation tag (skipped)'}
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
                      help='current date of the target notes section, to disambiguate duplicates')
    p_re.add_argument('--reason', default=None)
    p_re.set_defaults(action='reschedule')

    p_ca = sub.add_parser('cancel', help='mark the interview cancelled')
    p_ca.add_argument('--folder', required=True,
                      help='absolute path to the application folder')
    p_ca.add_argument('--stage', required=True,
                      help='stage label as it appears in the headings, e.g. "Hiring Manager"')
    p_ca.add_argument('--date', default=None,
                      help='current date of the target notes section, to disambiguate duplicates')
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
