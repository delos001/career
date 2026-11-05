#!/usr/bin/env python3
"""
session_log.py - shared session-log section manager across all skills

The session log for an evaluated job is a multi-skill shared artifact living
in the application folder as `<app-folder>/session_log.md` (filename from
config). role-intake creates it; every downstream skill (retrieval, gap
analysis, CV creation, interview prep, career brief, follow-up) appends its
own section recording what it did and when. This script owns the mechanics so
each skill keeps its SKILL.md free of file-manipulation instructions.

Two subcommands:

  append-section  Read a section body from a file. If a section with the
                  given heading already exists in the session log, replace
                  it in place (current-state discipline; re-runs overwrite,
                  do not accumulate history). If absent, append a new
                  section at the end of the file with one preceding blank
                  line. Echoes the session log path on stdout.

  interview       Create or update one interview round's '## Interview:
                  <stage>' section from field values (--set 'Label=value').
                  The required field set and its order come from the
                  template's '## Interview section' block, so no skill builds
                  the block by hand (GitHub #40). A new section gets every
                  required field, blank unless set; an existing section has
                  only the named fields changed and every other line kept.
                  Labels outside the required set are the template's optional
                  extras (e.g. 'Follow-up') and go after Outcome; a label that
                  nearly matches a required one is refused as a likely typo.

Nothing repo-dependent is hardcoded; the session-log filename comes from
config.yaml and the application folder is passed in by the calling skill.

Author    : Jason Delosh
Created   : 2026-05-26
Project   : career
Usage     : python scripts/session_log.py append-section \\
                --folder <app-folder> \\
                --heading "Retrieval" --body-file <path-to-section-body>
            python scripts/session_log.py interview --folder <app-folder> \\
                --stage "Hiring Manager" --set "Interview date=2026-11-12" \\
                --set "Status=held"
Depends   : pyyaml (via _config)
"""

import argparse
import difflib
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Path resolution
# The session log lives in the application folder under the fixed filename
# from config.yaml. The folder is supplied by the caller, so no slug/app-id/ym
# stem-building (and its casing pitfalls) is needed here.
# ---------------------------------------------------------------------------

def _session_log_path(cfg, folder):
    """Return absolute path of the session log inside the application folder."""
    return os.path.join(folder, cfg['filenames']['session_log_file'])


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
        # Replace; normalise to one trailing blank line. Replacement via lambda
        # so a body holding a backslash (a Windows path) is not read as a regex
        # replacement template.
        replacement = new_section_body.rstrip() + '\n\n'
        return pattern.sub(lambda _m: replacement, text)
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
    log_path = _session_log_path(cfg, args.folder)
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
# Subcommand: interview
# Field-level create-or-update of one '## Interview: <stage>' section. The
# required labels and their order are read from the template, the single
# authority the prep QC scripts also read (_util.interview_section_fields).
# ---------------------------------------------------------------------------

_FIELD_LINE_RE = re.compile(r'^-\s+([^:]+):[ \t]?(.*)$')


def _parse_sets(pairs, required):
    """Return an ordered {label: value} from 'Label=value' strings.

    A label that is not required but closely resembles a required one is a
    likely typo ('Interveiw date') and is refused rather than silently added
    as an optional extra.
    """
    values = {}
    bare_required = [r.rstrip(':') for r in required]
    for pair in pairs:
        if '=' not in pair:
            raise ValueError(f"--set expects 'Label=value', got {pair!r}")
        label, value = (part.strip() for part in pair.split('=', 1))
        if label not in bare_required:
            near = difflib.get_close_matches(label, bare_required, n=1, cutoff=0.8)
            if near:
                raise ValueError(f'unknown field {label!r}; did you mean {near[0]!r}?')
        values[label] = value
    return values


def _render_new(stage, required, values):
    """Build a new section: every required field in order, then extras."""
    lines = [f'## Interview: {stage}', '']
    bare_required = [r.rstrip(':') for r in required]
    for label in bare_required:
        lines.append(f'- {label}: {values.get(label, "")}'.rstrip())
    for label, value in values.items():
        if label not in bare_required:
            lines.append(f'- {label}: {value}'.rstrip())
    return '\n'.join(lines) + '\n'


def _update_existing(section, values):
    """Change only the named fields in an existing section; append new ones."""
    lines = section.rstrip('\n').split('\n')
    remaining = dict(values)
    for i, line in enumerate(lines):
        m = _FIELD_LINE_RE.match(line)
        if m and m.group(1).strip() in remaining:
            label = m.group(1).strip()
            lines[i] = f'- {label}: {remaining.pop(label)}'.rstrip()
    # Fields not yet present go after the last field line (after Outcome and
    # any existing extras), keeping prose or blank lines below them in place.
    last_field = max((i for i, ln in enumerate(lines) if _FIELD_LINE_RE.match(ln)), default=len(lines) - 1)
    for offset, (label, value) in enumerate(remaining.items(), start=1):
        lines.insert(last_field + offset, f'- {label}: {value}'.rstrip())
    return '\n'.join(lines) + '\n'


def cmd_interview(args, repo_root, cfg):
    """Create or update one interview round's section from field values."""
    log_path = _session_log_path(cfg, args.folder)
    if not os.path.exists(log_path):
        raise FileNotFoundError(
            f'session log not found: {log_path} (role-intake must run first to create the log)')
    template = _util.read(os.path.join(repo_root, cfg['paths']['templates'],
                                       cfg['filenames']['session_log_template']))
    required = _util.interview_section_fields(template)
    values = _parse_sets(args.set or [], required)
    heading = f'Interview: {args.stage}'
    text = _util.read(log_path)
    m = re.search(r'^##[ ]' + re.escape(heading) + r'[ \t]*\n.*?(?=^##[ ]|\Z)',
                  text, re.DOTALL | re.MULTILINE)
    section = _update_existing(m.group(0), values) if m else _render_new(args.stage, required, values)
    _util.write(log_path, _replace_or_append_section(text, heading, section))
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
    p_app.add_argument('--folder', required=True,
                       help='the application folder containing session_log.md')
    p_app.add_argument('--heading', required=True,
                       help='section heading text (without the ## prefix)')
    p_app.add_argument('--body-file', required=True,
                       help='path to a file holding the section content; the '
                            'leading ## <heading> line is optional and is added '
                            'from --heading when absent')
    p_app.set_defaults(func=cmd_append_section)

    p_int = sub.add_parser(
        'interview',
        help="create or update one '## Interview: <stage>' section from field values",
    )
    p_int.add_argument('--folder', required=True,
                       help='the application folder containing session_log.md')
    p_int.add_argument('--stage', required=True,
                       help="round label, e.g. 'Recruiter Screen' or 'Hiring Manager'")
    p_int.add_argument('--set', action='append', metavar='LABEL=VALUE',
                       help="a field value, e.g. 'Interview date=2026-11-12' (repeatable)")
    p_int.set_defaults(func=cmd_interview)

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
