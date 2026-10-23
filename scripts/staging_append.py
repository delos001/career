#!/usr/bin/env python3
"""
staging_append.py - append a Profile Updates Pending item

Called by the gap-analysis skill (Phase 6, Step 6a) once per captured fact, and
by the prep skills for facts surfaced during interview preparation. Appends one
item to the cross-application staging file at
personal/profile/profile_updates_pending.md, creating the file from the
templates/profile_updates_pending.md skeleton if it does not yet exist.

An item has two halves. The context half (when, from which application, the
requirement anchor, the target job's axis values) is derived here. The capture
half (the role where the work happened, what the candidate did, what others
did, the outcome they stated, and any limits on the claim) is passed in a
capture file of 'Label: value' lines. The capture labels are read from the
template's per-entry schema, never named here, and every one is required: a
capture missing a field, or carrying a blank one, is refused. That refusal is
the point. Every first-run capture needed its attribution corrected because a
single free-text field let the role, the split of work, and the outcome go
unrecorded (capture-is-not-an-interview).

Context comes from the application folder, not from the caller. Given --folder,
the script reads the date (today), the application ID, the company, the role,
and the five axis values out of that application's session log. Every derived
field still has an explicit flag that overrides it, for the case where the
session log is absent or the value needs correcting.

The item's label is its handle: profile_update.py finds an item by it, so the
label must be unique within the queue. There is no item number and no record of
where an item went once promoted (#70); the profile is the source.

Author    : Jason Delosh
Created   : 2026-05-27
Project   : career
Usage     : python scripts/staging_append.py --folder <app_folder> \\
                --requirement CR-NNN --requirement-text-short ... \\
                --capture-file <path> --label ...
            python scripts/staging_append.py --folder <app_folder> \\
                --requirement "n/a (surfaced during prep)" \\
                --capture-file <path> --label ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import profile_update as pu
from inventory_model import document, entry_block


# ---------------------------------------------------------------------------
# Template parsing
# The template carries two fenced blocks: the skeleton of an empty file, then
# the per-entry schema. The skeleton initialises a missing file. The schema's
# bullet labels, minus the ones this script derives itself, are the capture
# fields a caller must supply.
#
# profile_update.py owns the staging file's section layout, so its section
# constant and empty marker are reused here rather than re-derived. One parser
# for one file format; profile_update_qc.py reaches into it the same way.
# ---------------------------------------------------------------------------

# Regex: every fenced block in the template, in order.
_FENCE_RE = re.compile(r'```\n(.*?)\n```', re.DOTALL)

# Regex: a schema bullet label, e.g. '- **Work role:** ...'.
_SCHEMA_LABEL_RE = re.compile(r'^- \*\*(.+?):\*\*', re.MULTILINE)

# The labels this script writes itself, from the application folder or flags.
DERIVED_LABELS = ('Captured', 'From', 'Requirement', 'Role context')

# The capture label naming where the work happened, and the forms its value
# may take besides an RL-NNN: a role the inventory does not carry yet, or an
# explicit reason no role applies (a tool, a certification).
WORK_ROLE_LABEL = 'Work role'
_WORK_ROLE_RE = re.compile(r'^(RL-\d{3}|new: .+|n/a \(.+\))$')


def _template_blocks(templates_dir, template_name):
    """Return the template's fenced blocks: [skeleton, per-entry schema]."""
    text = _util.read(os.path.join(templates_dir, template_name))
    blocks = _FENCE_RE.findall(text)
    if len(blocks) < 2:
        raise ValueError(
            f'{template_name} must carry a skeleton block and a per-entry '
            f'schema block')
    return blocks[0], blocks[1]


def schema_labels(schema_block):
    """Return every field label an item carries, in schema order."""
    return _SCHEMA_LABEL_RE.findall(schema_block)


def capture_labels(schema_block):
    """Return the capture field labels, in schema order."""
    return [label for label in schema_labels(schema_block)
            if label not in DERIVED_LABELS]


def load_schema(repo_root, cfg):
    """Return (skeleton, per-entry schema) from the staging template."""
    return _template_blocks(os.path.join(repo_root, cfg['paths']['templates']),
                            cfg['filenames']['staging_file'])


# ---------------------------------------------------------------------------
# Capture file
# One 'Label: value' line per capture field. A value runs to the end of its
# line, so a capture field is always one line, which is also what keeps the
# rendered item one bullet per field.
# ---------------------------------------------------------------------------

def parse_capture(text, labels, known_roles):
    """Return {label: value} for a capture file, or raise naming every problem.

    Refuses a missing label, a blank value, an unknown label, a label given
    twice, and a Work role that is neither a real RL-NNN nor one of the two
    explicit forms.
    """
    values, problems = {}, []
    for line in text.split('\n'):
        if not line.strip():
            continue
        m = re.match(r'^([A-Za-z][A-Za-z ]*):\s*(.*?)\s*$', line)
        if not m or m.group(1) not in labels:
            problems.append(f'not a capture field line: "{line.strip()}"')
            continue
        label, value = m.group(1), m.group(2)
        if label in values:
            problems.append(f'"{label}" is given twice')
        values[label] = value
    for label in labels:
        if label not in values:
            problems.append(f'"{label}" is missing')
        elif not values[label]:
            problems.append(f'"{label}" is blank; write the explicit none form '
                            f'from the staging rules instead')

    role = values.get(WORK_ROLE_LABEL, '')
    if role and not _WORK_ROLE_RE.match(role):
        problems.append(f'"{WORK_ROLE_LABEL}: {role}" must be an RL-NNN, '
                        f'"new: <employer>, <title>", or "n/a (<reason>)"')
    elif role.startswith('RL-') and role not in known_roles:
        problems.append(f'{role} is not a role record in the inventory')

    if problems:
        raise ValueError('capture refused: ' + '; '.join(problems))
    return values


# ---------------------------------------------------------------------------
# Context derivation from the application folder
# The session log already holds every contextual field an item needs: the
# metadata block names the application, company, and role, and the axis
# classification names the five axis values.
# ---------------------------------------------------------------------------

# Regex: a '- Label: value' line in the session log's metadata block.
_META_RE = r'(?m)^-\s+{label}:\s*(.+?)\s*$'

# Regex: an axis line, e.g. '- Industry: eclinical - Faro is a ...'. The form is
# the axis-classifier's return-format spec, which assemble.py finalize writes
# into the session log verbatim; it carries no bold markers. Captures the first
# value token, which is the primary per the classifier's
# '<primary> (primary), <secondary> (secondary)' convention.
_AXIS_RE = r'(?m)^-\s+{label}:\s+([A-Za-z0-9-]+)'

# Axis flag name -> the label the session log uses for it.
_AXIS_LABELS = {
    'industry': 'Industry',
    'specialty': 'Specialty',
    'orientation': 'Orientation',
    'level': 'Level',
    'work_state': 'Work-state',
}


def _derive_from_folder(folder, cfg):
    """Return the contextual fields read from an application's session log.

    Raises when the folder or session log is missing, or when a field cannot be
    found, so a silent partial derivation never produces a half-filled item.
    """
    log_path = os.path.join(folder, cfg['filenames']['session_log_file'])
    if not os.path.exists(log_path):
        raise ValueError(f'no session log in the application folder: {log_path}')
    text = _util.read(log_path)

    derived = {}
    for flag, label in (('from_app', 'APP-NNN'), ('company', 'Company'),
                        ('role', 'Role')):
        m = re.search(_META_RE.format(label=re.escape(label)), text)
        if not m:
            raise ValueError(f'session log has no "{label}:" line to read')
        derived[flag] = m.group(1)

    for flag, label in _AXIS_LABELS.items():
        m = re.search(_AXIS_RE.format(label=re.escape(label)), text)
        if not m:
            raise ValueError(
                f'session log has no "{label}" line in its axis classification; '
                f'pass --{flag.replace("_", "-")} explicitly')
        derived[flag] = m.group(1)

    return derived


# ---------------------------------------------------------------------------
# Item rendering
# Field labels match the per-entry schema in templates/profile_updates_pending.md.
# ---------------------------------------------------------------------------

def _requirement_line(args):
    """Return the requirement bullet anchoring where the fact surfaced."""
    anchor = args.requirement.strip()
    if args.requirement_text_short:
        anchor = f'{anchor} - {args.requirement_text_short.strip()}'
    return f'- **Requirement:** {anchor}\n'


def _render_item(args, capture, labels):
    """Render one item block per the staging-file per-entry schema."""
    role_context = (
        f'Industry={args.industry}, Specialty={args.specialty}, '
        f'Orientation={args.orientation}, Level={args.level}, '
        f'Work-state={args.work_state}'
    )
    return (
        f'### {args.label}\n\n'
        f'- **Captured:** {args.captured}\n'
        f'- **From:** {args.from_app} ({args.company} | {args.role})\n'
        f'{_requirement_line(args)}'
        f'- **Role context:** {role_context}\n'
        + ''.join(f'- **{label}:** {capture[label]}\n' for label in labels)
    )


# ---------------------------------------------------------------------------
# Append logic
# When the file is missing, initialise it from the template skeleton. Then
# insert the new item at the end of '## Entries': replace the section's
# '_(none)_' placeholder on the first append, or follow the last queued item.
# ---------------------------------------------------------------------------

def _ensure_file(staging_path, skeleton):
    """Create the staging file from the skeleton if missing; return its text."""
    if os.path.exists(staging_path):
        return _util.read(staging_path)
    _util.write(staging_path, skeleton)
    return skeleton


def _append_item(staging_text, item_block):
    """Insert item_block at the end of '## Entries'.

    Raises if '## Entries' is missing - the file is malformed and the caller
    should not silently rebuild it (could clobber unprocessed items).
    """
    bounds = document.section_bounds(staging_text, pu.ENTRIES_HEADING)
    if bounds is None:
        raise ValueError("staging file missing '## Entries' section")
    start, end = bounds
    lines = staging_text.split('\n')
    block = item_block.rstrip().split('\n')
    content = [i for i in range(start + 1, end) if lines[i].strip()]

    # An empty queue holds only its placeholder; the first item replaces it.
    if len(content) == 1 and lines[content[0]].strip() == pu._EMPTY_MARKER:
        return '\n'.join(lines[:content[0]] + block + lines[content[0] + 1:])

    # Otherwise follow the last queued item, separated by a blank line.
    at = (content[-1] if content else start) + 1
    return '\n'.join(lines[:at] + [''] + block + lines[at:])


# ---------------------------------------------------------------------------
# Main entry
# Resolves paths from config, validates the capture, appends the item, and
# prints its label.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, append the item, print its label."""
    parser = argparse.ArgumentParser(
        description='append a Profile Updates Pending item'
    )
    parser.add_argument('--folder',
                        help='application folder; the date, application '
                             'ID, company, role, and five axis values are read '
                             'from its session log')
    parser.add_argument('--captured', help='YYYY-MM-DD (default: today)')
    parser.add_argument('--from-app', dest='from_app',
                        help='APP-NNN of the originating application')
    parser.add_argument('--company')
    parser.add_argument('--role')
    parser.add_argument('--requirement', required=True,
                        help='CR-NNN of the requirement under discussion when '
                             "the fact surfaced, or 'n/a (reason)' when nothing "
                             'anchors it')
    parser.add_argument('--requirement-text-short',
                        help='short form of the requirement text; appended to '
                             '--requirement when given')
    parser.add_argument('--industry')
    parser.add_argument('--specialty')
    parser.add_argument('--orientation')
    parser.add_argument('--level')
    parser.add_argument('--work-state', dest='work_state')
    parser.add_argument('--capture-file', required=True,
                        help="file of 'Label: value' lines, one per capture "
                             'field in the template schema')
    parser.add_argument('--label', required=True,
                        help='3-5 word descriptor; unique within the queue')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()

        # Fill the contextual fields from the application folder. An explicit
        # flag always wins, so a caller can correct a derived value.
        if args.folder:
            for flag, value in _derive_from_folder(args.folder, cfg).items():
                if not getattr(args, flag):
                    setattr(args, flag, value)
        if not args.captured:
            args.captured = _util.today_iso()
        missing = [f"--{flag.replace('_', '-')}" for flag in
                   ('from_app', 'company', 'role', 'industry', 'specialty',
                    'orientation', 'level', 'work_state')
                   if not getattr(args, flag)]
        if missing:
            raise ValueError(
                f"missing context: {', '.join(missing)}. Pass --folder to read "
                f'these from the application session log, or pass each flag '
                f'explicitly.')

        skeleton, schema = load_schema(repo_root, cfg)
        labels = capture_labels(schema)

        # Validate the capture before touching the staging file.
        known_roles = {e['id'] for e in entry_block.parse_blocks(
            _util.read(pu._inventory_path(repo_root, cfg))) if e['prefix'] == 'RL'}
        capture = parse_capture(_util.read(args.capture_file), labels, known_roles)

        label = args.label.strip()
        if not label:
            raise ValueError('--label is empty')
        staging_path = pu._staging_path(repo_root, cfg)
        staging_text = _ensure_file(staging_path, skeleton)
        if any(item['label'] == label for item in pu.parse_staging(staging_text)):
            raise ValueError(f'an item labelled "{label}" is already waiting; '
                             f'labels are how items are found, so pick another')
        args.label = label

        staging_text = _append_item(staging_text, _render_item(args, capture, labels))
        _util.write(staging_path, staging_text)
        print(label)

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
