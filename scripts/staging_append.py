#!/usr/bin/env python3
"""
staging_append.py - append a Profile Updates Pending entry

Called by the gap-analysis skill (Phase 6, Step 6a) once per PU entry, and by
the prep skills for facts surfaced during interview preparation. Appends a single
PU-NNN entry to the cross-application staging file at
personal/profile/profile_updates_pending.md. Creates the file from the
templates/profile_updates_pending.md skeleton if it does not yet exist.

Each entry captures: when, from which application, the requirement anchor, the
role's axis context, the user's surfaced content (kept concise - this is CONTEXT
for the downstream profile-update skill, NOT copy-paste content for inventory /
narratives / positioning per the respect-profile-doc-conventions feedback
memory).

The file's '## Entries' section is a queue. A PU entry sits in it only while it
waits to be promoted; the profile-update skill takes it out once its content is
in the profile and records one line under '## Migrated' naming what became of
it. There is no status field, because presence in '## Entries' IS the waiting
state.

That migrated record is what makes the PU-NNN counter safe. The next ID is the
highest number across BOTH sections: taking it from the queue alone would let
the counter walk backwards as PU entries are promoted and reissue a number a
closed application's gap_analysis.md already cites in a 'Closure ref:' line.

Context comes from the application folder, not from the caller. Given --folder,
the script reads the date (today), the application ID, the company, the
role, and the five axis values out of that application's session log. Nine of
the thirteen fields an entry carries are therefore derived rather than passed,
which is what keeps the calling instruction in each skill to a single line.
Every derived field still has an explicit flag that overrides it, for the case
where the session log is absent or the value needs correcting.

Every entry carries one 'Requirement:' line anchoring where the fact surfaced:
a CR-NNN from that gap-analysis run, or 'n/a' plus a short reason when nothing
anchors it (a general fact raised during interview prep). The anchor is
provenance only. Whether the fact happened to close a gap is a fact about that
one application, recorded in its gap_analysis.md, and the profile does not carry
it: an entry that closed nothing is promoted exactly the same way, because it
may close a gap on a future application.

The script assigns the next PU-NNN by scanning every ID the file records, queued
and migrated alike, appends the new entry under '## Entries' (replacing that
section's '_(none)_' placeholder when the queue is empty), and prints the
assigned PU-NNN on stdout so the caller can record the reference inline in
gap_analysis.md.

Author    : Jason Delosh
Created   : 2026-05-27
Project   : career
Usage     : python scripts/staging_append.py --folder <app_folder> \\
                --requirement CR-NNN --requirement-text-short ... \\
                --content-file ... --label ...
            python scripts/staging_append.py --folder <app_folder> \\
                --requirement "n/a (surfaced during prep)" \\
                --content-file ... --label ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import profile_update as pu


# ---------------------------------------------------------------------------
# Skeleton and ID parsing helpers
# The staging file is an accumulating doc: initialise from the template if
# missing, then append. PU-NNN IDs are globally sequential within the file,
# independent of APP-NNN. Scanning existing IDs is cheap because the file is
# small (one entry per closure across all gap-analysis runs).
#
# profile_update.py owns the staging file's section layout, so its section
# constants and bounds helper are reused here rather than re-derived. One
# parser for one file format; profile_update_qc.py reaches into it the same way.
# ---------------------------------------------------------------------------

# Regex: capture the fenced skeleton block from the template.
_FENCE_RE = re.compile(r'```\n(.*?)\n```', re.DOTALL)

# Regex: a PU-NNN entry's heading in the queue. Captures the integer.
_PU_HEADING_RE = re.compile(r'^### PU-(\d+)\b', re.MULTILINE)

# Regex: a PU-NNN line in the migrated record. Captures the integer. Anchored to
# the line start so a PU-NNN mentioned inside a PU entry's Content field, which
# sits on a '- **Content:**' bullet, is never mistaken for an issued ID.
_PU_MIGRATED_RE = re.compile(r'^PU-(\d+):', re.MULTILINE)

# How many digits to render: PU-001, PU-042, etc. Matches the APP-NNN style.
_PU_DIGITS = 3


def _skeleton(templates_dir, template_name):
    """Return the fenced skeleton block from a template file."""
    text = _util.read(os.path.join(templates_dir, template_name))
    m = _FENCE_RE.search(text)
    if not m:
        raise ValueError(f'no fenced skeleton found in template: {template_name}')
    return m.group(1)


def _next_pu_id(staging_text):
    """Return the next PU-NNN ID by scanning every ID the file records.

    Both sections count. A queued PU entry's heading and a migrated PU entry's
    line are equally proof that the number was issued, and a number is issued
    once: a promoted PU entry's number stays cited by its originating
    application's gap_analysis.md forever, so reusing it would silently
    re-point that reference at unrelated content.

    Returns 'PU-001' when the file records none; otherwise max+1 zero-padded.
    """
    existing = [int(m.group(1)) for m in _PU_HEADING_RE.finditer(staging_text)]
    existing += [int(m.group(1)) for m in _PU_MIGRATED_RE.finditer(staging_text)]
    next_n = (max(existing) + 1) if existing else 1
    return f'PU-{next_n:0{_PU_DIGITS}d}'


# ---------------------------------------------------------------------------
# Context derivation from the application folder
# The session log already holds every contextual field a staging entry needs:
# the metadata block names the application, company, and role, and the axis
# classification names the five axis values. Reading them here rather than
# making each caller look them up and pass them one at a time is what keeps
# the call short enough to state in one line of a skill document.
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
    found, so a silent partial derivation never produces a half-filled entry.
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
# Entry rendering
# Builds the markdown block for one PU-NNN entry. Field labels match the
# per-entry schema in templates/profile_updates_pending.md.
# ---------------------------------------------------------------------------

def _requirement_line(args):
    """Return the requirement bullet anchoring where the fact surfaced."""
    anchor = args.requirement.strip()
    if args.requirement_text_short:
        anchor = f'{anchor} - {args.requirement_text_short.strip()}'
    return f'- **Requirement:** {anchor}\n'


def _render_entry(pu_id, args, content):
    """Render one PU-NNN entry block per the staging-file per-entry schema."""
    role_context = (
        f'Industry={args.industry}, Specialty={args.specialty}, '
        f'Orientation={args.orientation}, Level={args.level}, '
        f'Work-state={args.work_state}'
    )
    return (
        f'### {pu_id} - {args.label}\n\n'
        f'- **Captured:** {args.captured}\n'
        f'- **From:** {args.from_app} ({args.company} | {args.role})\n'
        f'{_requirement_line(args)}'
        f'- **Role context:** {role_context}\n'
        f'- **Content:** {content}\n'
    )


# ---------------------------------------------------------------------------
# Append logic
# When the file is missing, initialise from the template skeleton (so it
# carries the standard header, both sections, and a '_(none)_' placeholder in
# each). Then insert the new entry inside '## Entries': replace that section's
# placeholder on the first append, or follow the last queued PU entry on
# subsequent ones.
#
# Every step is bounded to the section. The file now carries two placeholders
# and ends with the migrated record, so a whole-file marker search would append
# into the wrong section and a whole-file append would land past both.
# ---------------------------------------------------------------------------

def _ensure_file(staging_path, templates_dir, template_name):
    """Create the staging file from the template if missing; return its text."""
    if os.path.exists(staging_path):
        return _util.read(staging_path)
    body = _skeleton(templates_dir, template_name)
    _util.write(staging_path, body)
    return body


def _append_entry(staging_text, entry_block):
    """Insert entry_block at the end of '## Entries'.

    Raises if '## Entries' is missing - the file is malformed and the caller
    should not silently rebuild it (could clobber unprocessed entries).
    """
    bounds = pu._section_bounds(staging_text, pu.ENTRIES_HEADING)
    if bounds is None:
        raise ValueError("staging file missing '## Entries' section")
    start, end = bounds
    lines = staging_text.split('\n')
    block = entry_block.rstrip().split('\n')
    content = [i for i in range(start + 1, end) if lines[i].strip()]

    # An empty queue holds only its placeholder; the first entry replaces it.
    if len(content) == 1 and lines[content[0]].strip() == pu._EMPTY_MARKER:
        return '\n'.join(lines[:content[0]] + block + lines[content[0] + 1:])

    # Otherwise follow the last queued PU entry, separated by a blank line.
    at = (content[-1] if content else start) + 1
    return '\n'.join(lines[:at] + [''] + block + lines[at:])


# ---------------------------------------------------------------------------
# Main entry
# Resolves paths from config, builds the entry, appends it, prints the PU-NNN.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, append the entry, print the assigned PU-NNN."""
    parser = argparse.ArgumentParser(
        description='append a Profile Updates Pending entry'
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
    parser.add_argument('--content-file', required=True,
                        help='path to a file holding the concise content (2-3 sentences max)')
    parser.add_argument('--label', required=True,
                        help='3-5 word descriptor of the surfaced information')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()

        # Fill the contextual fields from the application folder. An explicit
        # flag always wins, so a caller can correct a derived value without
        # having to pass all nine.
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

        templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
        template_name = cfg['filenames']['staging_file']  # template lives at same name in templates/
        profile_dir = os.path.join(repo_root, cfg['paths']['profile'])
        staging_path = os.path.join(profile_dir, cfg['filenames']['staging_file'])

        # Initialise file from template if missing; otherwise load current text.
        staging_text = _ensure_file(staging_path, templates_dir, template_name)

        # Determine next PU-NNN and load the content from the supplied file.
        pu_id = _next_pu_id(staging_text)
        content = _util.read(args.content_file).strip()

        # Render and append.
        entry_block = _render_entry(pu_id, args, content)
        staging_text = _append_entry(staging_text, entry_block)
        _util.write(staging_path, staging_text)

        # Echo the assigned ID so the caller can reference it in gap_analysis.md.
        print(pu_id)

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
