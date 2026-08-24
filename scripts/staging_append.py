#!/usr/bin/env python3
"""
staging_append.py - append a Profile Updates Pending entry

Called by the gap-analysis skill (Phase 6, Step 6a) once per capture, and by the
prep skills for facts surfaced during interview preparation. Appends a single
PU-NNN entry to the cross-application staging file at
personal/profile/profile_updates_pending.md. Creates the file from the
templates/profile_updates_pending.md skeleton if it does not yet exist.

Each entry captures: when, from which application, the requirement anchor, the
role's axis context, the user's surfaced content (kept concise - this is CONTEXT
for the downstream profile-update skill, NOT copy-paste content for inventory /
narratives / positioning per the respect-profile-doc-conventions feedback
memory), and a pending status.

Context comes from the application folder, not from the caller. Given --folder,
the script reads the capture date (today), the application ID, the company, the
role, and the five axis values out of that application's session log. Nine of
the thirteen fields an entry carries are therefore derived rather than passed,
which is what keeps the calling instruction in each skill to a single line.
Every derived field still has an explicit flag that overrides it, for the case
where the session log is absent or the value needs correcting.

Two entry kinds, selected by --kind:

  closure     The user's input fully closed a gap. Requires --closed-requirement;
              renders a 'Closed requirement:' line.
  enrichment  New or under-represented profile information surfaced on a
              partial-match or covered requirement, or during interview prep.
              Renders a 'Related requirement:' line, which may be 'n/a' plus a
              short reason. Passing --closed-requirement here is an error: the
              distinction is what tells the downstream profile-update skill
              whether the information was already credited in a fit score.

The script assigns the next PU-NNN by scanning existing entry IDs in the file,
appends the new entry under '## Entries' (replacing the '_(none)_' placeholder
when the file is empty), and prints the assigned PU-NNN on stdout so the
caller can record the reference inline in gap_analysis.md.

Author    : Jason Delosh
Created   : 2026-05-27
Project   : career
Usage     : python scripts/staging_append.py --folder <app_folder> \\
                --kind enrichment --content-file ... --label ...
            python scripts/staging_append.py --folder <app_folder> \\
                --kind closure --closed-requirement CR-NNN \\
                --requirement-text-short ... --content-file ... --label ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Skeleton and ID parsing helpers
# The staging file is an accumulating doc: initialise from the template if
# missing, then append. PU-NNN IDs are globally sequential within the file,
# independent of APP-NNN. Scanning existing IDs is cheap because the file is
# small (one entry per closure across all gap-analysis runs).
# ---------------------------------------------------------------------------

# Regex: capture the fenced skeleton block from the template.
_FENCE_RE = re.compile(r'```\n(.*?)\n```', re.DOTALL)

# Regex: a PU-NNN entry's heading. Captures the integer.
_PU_HEADING_RE = re.compile(r'^### PU-(\d+)\b', re.MULTILINE)

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
    """Return the next PU-NNN ID by scanning existing entry headings.

    Returns 'PU-001' on an empty / no-entries file; otherwise max+1 zero-padded.
    """
    existing = [int(m.group(1)) for m in _PU_HEADING_RE.finditer(staging_text)]
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

# Regex: an axis line, e.g. '- **Industry:** eclinical - Faro is a ...'.
# Captures the first value token, which is the primary per the axis-classifier's
# '<primary> (primary), <secondary> (secondary)' convention.
_AXIS_RE = r'(?m)^-\s+\*\*{label}:\*\*\s+([A-Za-z0-9-]+)'

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
# per-entry schema in templates/profile_updates_pending.md. The requirement
# line is the only difference between the two kinds: a closure names the
# requirement it closed, an enrichment names a requirement that is context only
# (or 'n/a' when the fact was surfaced outside a requirement walk).
# ---------------------------------------------------------------------------

def _requirement_line(args):
    """Return the requirement bullet for this entry's kind."""
    if args.kind == 'closure':
        return (f'- **Closed requirement:** {args.closed_requirement} - '
                f'{args.requirement_text_short}\n')
    related = args.related_requirement or 'n/a'
    return f'- **Related requirement:** {related}\n'


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
        f'- **Status:** pending\n'
    )


# ---------------------------------------------------------------------------
# Append logic
# When the file is missing, initialise from the template skeleton (so it
# carries the standard header / Entries section / '_(none)_' placeholder).
# Then locate '## Entries' and insert the new entry after it: replace
# '_(none)_' on the first append, or append after existing entries on
# subsequent appends.
# ---------------------------------------------------------------------------

def _ensure_file(staging_path, templates_dir, template_name):
    """Create the staging file from the template if missing; return its text."""
    if os.path.exists(staging_path):
        return _util.read(staging_path)
    body = _skeleton(templates_dir, template_name)
    _util.write(staging_path, body)
    return body


def _append_entry(staging_text, entry_block):
    """Insert entry_block under '## Entries', replacing '_(none)_' if present.

    Raises if '## Entries' is missing - the file is malformed and the caller
    should not silently rebuild it (could clobber unprocessed entries).
    """
    if not re.search(r'(?m)^##\s+Entries\s*$', staging_text):
        raise ValueError("staging file missing '## Entries' section")
    # '_(none)_' placeholder appears on initial file; replace it on first append.
    if re.search(r'(?m)^_\(none\)_\s*$', staging_text):
        return re.sub(
            r'(?m)^_\(none\)_\s*$',
            entry_block.rstrip(),
            staging_text,
            count=1,
        )
    # Otherwise append the new entry at end of file, separated by a blank line.
    return staging_text.rstrip() + '\n\n' + entry_block.rstrip() + '\n'


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
                        help='application folder; the capture date, application '
                             'ID, company, role, and five axis values are read '
                             'from its session log')
    parser.add_argument('--captured', help='YYYY-MM-DD (default: today)')
    parser.add_argument('--from-app', dest='from_app',
                        help='APP-NNN of the originating application')
    parser.add_argument('--company')
    parser.add_argument('--role')
    parser.add_argument('--kind', choices=['closure', 'enrichment'],
                        default='closure',
                        help='closure = the input closed a gap; enrichment = new '
                             'or under-represented information that did not')
    parser.add_argument('--closed-requirement',
                        help='closure only: CR-NNN of the requirement this input closed')
    parser.add_argument('--requirement-text-short',
                        help='closure only: short form of the requirement text')
    parser.add_argument('--related-requirement',
                        help="enrichment only: 'CR-NNN - short text' for context, or "
                             "'n/a (reason)' when no requirement anchors the capture")
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

    # Kind-conditional argument validation. argparse cannot express this, and a
    # silent default here would reintroduce the mislabeling this flag exists to
    # prevent: an enrichment rendered under a 'Closed requirement:' label reads
    # downstream as a gap the fit score already credited.
    if args.kind == 'closure':
        missing = [flag for flag, value in (
            ('--closed-requirement', args.closed_requirement),
            ('--requirement-text-short', args.requirement_text_short),
        ) if not value]
        if missing:
            parser.error(f"--kind closure requires {' and '.join(missing)}")
        if args.related_requirement:
            parser.error('--related-requirement is enrichment-only; a closure '
                         'names its requirement with --closed-requirement')
    else:
        if args.closed_requirement:
            parser.error('--closed-requirement is closure-only; an enrichment '
                         'did not close a gap. Use --related-requirement.')

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
