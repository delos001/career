#!/usr/bin/env python3
"""
staging_append.py - append a Profile Updates Pending entry

Called by the gap-analysis skill (Phase 6, Step 6b) once per closure-via-user-
input. Appends a single PU-NNN entry to the cross-application staging file at
personal/profile/profile_updates_pending.md. Creates the file from the
templates/profile_updates_pending.md skeleton if it does not yet exist.

Each entry captures: when, from which application, which critical requirement
was closed, the role's axis context, the user's surfaced content (kept
concise - this is CONTEXT for the downstream profile-update skill, NOT
copy-paste content for inventory / narratives / positioning per the
respect-profile-doc-conventions feedback memory), and a pending status.

The script assigns the next PU-NNN by scanning existing entry IDs in the file,
appends the new entry under '## Entries' (replacing the '_(none)_' placeholder
when the file is empty), and prints the assigned PU-NNN on stdout so the
caller can record the reference inline in gap_analysis.md.

Author    : Jason Delosh
Created   : 2026-05-27
Project   : career
Usage     : python scripts/staging_append.py \\
                --captured YYYY-MM-DD --from-app APP-NNN \\
                --company ... --role ... \\
                --closed-requirement CR-NNN --requirement-text-short ... \\
                --industry ... --specialty ... --orientation ... \\
                --level ... --work-state ... \\
                --content-file ... --label ...
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
# Entry rendering
# Builds the markdown block for one PU-NNN entry. Field labels match the
# per-entry schema in templates/profile_updates_pending.md.
# ---------------------------------------------------------------------------

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
        f'- **Closed requirement:** {args.closed_requirement} - {args.requirement_text_short}\n'
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
    parser.add_argument('--captured', required=True, help='YYYY-MM-DD')
    parser.add_argument('--from-app', required=True, dest='from_app',
                        help='APP-NNN of the originating application')
    parser.add_argument('--company', required=True)
    parser.add_argument('--role', required=True)
    parser.add_argument('--closed-requirement', required=True,
                        help='CR-NNN of the requirement closed by this user input')
    parser.add_argument('--requirement-text-short', required=True,
                        help='short form of the requirement text for the entry header')
    parser.add_argument('--industry', required=True)
    parser.add_argument('--specialty', required=True)
    parser.add_argument('--orientation', required=True)
    parser.add_argument('--level', required=True)
    parser.add_argument('--work-state', required=True, dest='work_state')
    parser.add_argument('--content-file', required=True,
                        help='path to a file holding the concise content (2-3 sentences max)')
    parser.add_argument('--label', required=True,
                        help='3-5 word descriptor of the surfaced information')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()

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
