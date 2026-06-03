#!/usr/bin/env python3
"""
session_log.py - shared session-log section manager across all skills

The session log for an evaluated job is a multi-skill shared artifact at
`personal/sessions/<SLUG>_APP-NNN_YYYY-MM_SessionLog.md`. role-intake
creates it; every downstream skill (retrieval, gap analysis, CV creation,
interview prep, career brief, follow-up) appends its own section recording
what it did and when. This script owns the mechanics so each skill keeps
its SKILL.md free of file-manipulation instructions.

One subcommand:

  append-section  Read a section body from a file. If a section with the
                  given heading already exists in the session log, replace
                  it in place (current-state discipline; re-runs overwrite,
                  do not accumulate history). If absent, append a new
                  section at the end of the file with one preceding blank
                  line. Echoes the session log path on stdout.

Nothing repo-dependent is hardcoded; folder, filename pattern, and naming
template come from config.yaml.

Author    : Jason Delosh
Created   : 2026-05-26
Project   : career
Usage     : python scripts/session_log.py append-section \\
                --slug <slug> --app-id <APP-NNN> --ym <YYYY-MM> \\
                --heading "Retrieval" --body-file <path-to-section-body>
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Path resolution
# Build the session-log path from slug + app-id + ym using the naming
# patterns in config.yaml. No path is hardcoded so a folder or naming
# convention change is a config edit, not a code change.
# ---------------------------------------------------------------------------

def _session_log_path(repo_root, cfg, slug, app_id, ym):
    """Return absolute path of the session log for this application."""
    stem = cfg['naming']['application_stem'].format(
        slug=slug, app_id=app_id, ym=ym
    )
    name = cfg['naming']['session_log_filename'].format(stem=stem)
    return os.path.join(repo_root, cfg['paths']['sessions'], name)


# ---------------------------------------------------------------------------
# Section replace-or-append
# Locate '## <heading>' in the text and replace everything from that line
# up to (but not including) the next '## ' heading or end of file. If the
# heading is not present, append the section at the end with one preceding
# blank line, so the file stays cleanly section-separated.
# ---------------------------------------------------------------------------

def _replace_or_append_section(text, heading, new_section_body):
    """Replace section '## <heading>' with new body, or append if missing.

    new_section_body is the full section text starting with the '## <heading>'
    line. The function trusts the caller to format that block correctly; it
    does not synthesize the heading line.
    """
    # Regex: the '## heading' line and everything after it, lazily, up to
    # the next '## ' line or end of string. Identical pattern to the
    # _replace_section helper in scripts/assemble.py.
    pattern = re.compile(
        r'^##[ ]' + re.escape(heading) + r'[ \t]*\n.*?(?=^##[ ]|\Z)',
        re.DOTALL | re.MULTILINE,
    )
    if pattern.search(text):
        # Replace; normalise to one trailing blank line.
        return pattern.sub(new_section_body.rstrip() + '\n\n', text)
    # Append at the end. Ensure one blank line separates the new section
    # from whatever currently ends the file.
    return text.rstrip() + '\n\n' + new_section_body.rstrip() + '\n'


# ---------------------------------------------------------------------------
# Subcommand: append-section
# Reads the section body from a file, applies replace-or-append, writes the
# session log back. The body file holds the section content; the '## <heading>'
# line is optional in it and is prepended from --heading when absent.
# ---------------------------------------------------------------------------

def cmd_append_section(args, repo_root, cfg):
    """Read body file, apply replace-or-append to the session log, write back."""
    log_path = _session_log_path(repo_root, cfg, args.slug, args.app_id, args.ym)
    if not os.path.exists(log_path):
        raise FileNotFoundError(
            f'session log not found: {log_path} '
            '(role-intake must run first to create the log)'
        )
    body = _util.read(args.body_file).rstrip() + '\n'
    # The body file may be content-only or may already lead with its heading.
    # Normalize to a full section: prepend '## <heading>' when absent, so callers
    # never have to duplicate the heading they already pass via --heading. If the
    # heading is present it is used as-is (no double heading).
    expected_first = f'## {args.heading}'
    first_line = body.split('\n', 1)[0].strip()
    if first_line != expected_first:
        body = f'{expected_first}\n\n{body}'
    text = _util.read(log_path)
    text = _replace_or_append_section(text, args.heading, body)
    _util.write(log_path, text)
    print(log_path)


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch the append-section subcommand."""
    parser = argparse.ArgumentParser(
        description='shared session-log section manager across all skills'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_app = sub.add_parser(
        'append-section',
        help='replace (if exists) or append (if not) a section in the session log',
    )
    p_app.add_argument('--slug', required=True,
                       help='application slug, e.g. fortrea')
    p_app.add_argument('--app-id', required=True,
                       help='application ID, e.g. APP-005')
    p_app.add_argument('--ym', required=True,
                       help='year-month, e.g. 2026-05')
    p_app.add_argument('--heading', required=True,
                       help='section heading text (without the ## prefix)')
    p_app.add_argument('--body-file', required=True,
                       help='path to a file holding the section content; the '
                            'leading ## <heading> line is optional and is added '
                            'from --heading when absent')
    p_app.set_defaults(func=cmd_append_section)

    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
