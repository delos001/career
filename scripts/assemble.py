#!/usr/bin/env python3
"""
assemble.py - role-intake artifact assembler

Writes the two artifacts the role-intake skill produces - the session log and the
research file - so the skill does mechanical file-writing through a deterministic
tool instead of by hand. Three subcommands, one per write point in the skill:

  init      Phase 3 - create the application folder and write the initial session
            log (metadata filled in, axis sections marked pending).
  research  Phase 5 - write (or, on a re-run, refresh) research.md from the three
            research subagents' output blocks.
  finalize  Phase 7 - complete the session log: fill the research-completed date
            and replace the pending axis sections with the axis-classifier output.

Nothing repo-dependent is hardcoded here. Folder locations, filenames, and naming
patterns come from config.yaml (via _config); the artifact structures come from
the skeletons in the templates folder. Every write is section-scoped: the script
replaces only the sections role-intake owns and leaves anything else in place, so
re-runs and sections added by downstream skills are not clobbered.

Author    : Jason Delosh
Created   : 2026-05-14
Project   : career
Usage     : python scripts/assemble.py init     --slug ... --app-id ... --ym ... --company ... --role ... [--level ...] --industry ... --start-date ... --jd-text-file ... --jd-source ... [--comms-text-file ... --comms-source ...]
            python scripts/assemble.py research --folder ... --app-id ... --company ... --role ... --date ... --company-file ... --role-file ... --industry-file ...
            python scripts/assemble.py finalize --session-log ... --date ... --axis-file ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config


# ---------------------------------------------------------------------------
# Shared helpers
# Small utilities used by more than one subcommand: reading and writing UTF-8
# files, pulling the skeleton out of a template, substituting {{tokens}}, and
# replacing a single Markdown section in place.
# ---------------------------------------------------------------------------

def _read(path):
    """Read a UTF-8 text file and return its contents (raises if it is missing)."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _write(path, text):
    """Write text to a UTF-8 file, creating parent folders if they do not exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def _skeleton(templates_dir, template_name):
    """Return the skeleton block from a template file in the templates folder.

    Each template documents its artifact in prose and carries the actual skeleton
    inside the first fenced code block. This pulls out the text between the first
    pair of triple-backtick fences.
    """
    text = _read(os.path.join(templates_dir, template_name))
    # Regex: capture everything between the first ``` fence and the next one.
    # re.DOTALL lets '.' span newlines so the whole block is captured.
    m = re.search(r'```\n(.*?)\n```', text, re.DOTALL)
    if not m:
        raise ValueError(f'no fenced skeleton found in template: {template_name}')
    return m.group(1)


def _fill(skeleton, values):
    """Substitute every {{token}} in a skeleton with its value.

    'values' maps token name -> replacement text. Every token in the skeleton
    must be supplied, and no {{...}} may remain afterwards - a mismatch is a bug,
    so it raises rather than writing a half-filled file.
    """
    result = skeleton
    for token, value in values.items():
        placeholder = '{{' + token + '}}'
        if placeholder not in result:
            raise ValueError(f'token not found in skeleton: {placeholder}')
        result = result.replace(placeholder, value)
    # Any {{...}} left over means the caller missed a token.
    leftover = re.findall(r'\{\{.*?\}\}', result)
    if leftover:
        raise ValueError(f'unfilled tokens remain: {leftover}')
    return result


def _replace_section(text, heading, new_section):
    """Replace one Markdown '## heading' section in text with new_section.

    Finds the line '## <heading>' and replaces from there up to (but not
    including) the next '## ' heading, or end of file if it is the last section.
    This keeps every write section-scoped: other sections - including any a
    downstream skill added - are untouched. Raises if the heading is absent.
    """
    # Regex: match the '## heading' line and everything after it, lazily, up to
    # the next '## ' line or the end of the string.
    pattern = re.compile(
        r'^##[ ]' + re.escape(heading) + r'[ \t]*\n.*?(?=^##[ ]|\Z)',
        re.DOTALL | re.MULTILINE,
    )
    if not pattern.search(text):
        raise ValueError(f'section not found: ## {heading}')
    # Normalise to one trailing blank line so sections stay visually separated.
    return pattern.sub(new_section.rstrip() + '\n\n', text)


# ---------------------------------------------------------------------------
# Subcommand: init  (role-intake Phase 3)
# Creates the application folder and writes the initial session log - metadata
# filled in, axis sections marked pending for finalize to fill later. Folder
# locations and naming patterns come from config.yaml.
# ---------------------------------------------------------------------------

def cmd_init(args, repo_root, cfg):
    # Build the per-job stem and the two artifact locations from config patterns.
    stem = cfg['naming']['application_stem'].format(
        slug=args.slug, app_id=args.app_id, ym=args.ym)
    app_folder = os.path.join(repo_root, cfg['paths']['applications'], stem)
    session_log_name = cfg['naming']['session_log_filename'].format(stem=stem)
    session_log = os.path.join(repo_root, cfg['paths']['sessions'], session_log_name)

    # Fail loudly rather than overwrite: an existing session log means this is
    # really a resume, which the skill's resume check should have caught.
    if os.path.exists(session_log):
        raise FileExistsError(f'session log already exists: {session_log}')

    os.makedirs(app_folder, exist_ok=True)

    # Persist the JD into the application folder so it survives across sessions;
    # resume detection relies on jd.md being present.
    jd_file_name = cfg['filenames']['jd_file']
    jd_path = os.path.join(app_folder, jd_file_name)
    _write(jd_path, _read(args.jd_text_file))

    # Comms is optional; persist only when supplied. Blank session-log fields
    # carry through when no comms were ingested.
    comms_file_name = cfg['filenames']['comms_file']
    if args.comms_text_file:
        comms_path = os.path.join(app_folder, comms_file_name)
        _write(comms_path, _read(args.comms_text_file))
        comms_file_value = comms_file_name
        comms_source_value = args.comms_source or ''
    else:
        comms_path = None
        comms_file_value = ''
        comms_source_value = ''

    templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
    skeleton = _skeleton(templates_dir, cfg['filenames']['session_log_template'])
    body = _fill(skeleton, {
        'company': args.company,
        'role': args.role,
        'ym': args.ym,
        'app_id': args.app_id,
        'role_level': args.level or '_(not stated)_',
        'industry': args.industry,
        'start_date': args.start_date,
        'jd_file': jd_file_name,
        'jd_source': args.jd_source,
        'comms_file': comms_file_value,
        'comms_source': comms_source_value,
        # Not known yet; finalize (Phase 7) fills these in.
        'research_completed_date': '_(pending)_',
        'axis_classification': '## Axis Classification\n\n_(pending)_',
        'axis_gaps': '## Axis Gaps\n\n_(pending)_',
    })
    _write(session_log, body)
    # Print all written paths so the calling skill knows where things landed.
    print(app_folder)
    print(session_log)
    print(jd_path)
    if comms_path is not None:
        print(comms_path)


# ---------------------------------------------------------------------------
# Subcommand: research  (role-intake Phase 5)
# Writes research.md from the three research subagents' output blocks. On a
# re-run it replaces only role-intake's own sections, leaving anything else.
# ---------------------------------------------------------------------------

def cmd_research(args, repo_root, cfg):
    research_file = os.path.join(args.folder, cfg['filenames']['research_file'])
    company_block = _read(args.company_file).strip()
    role_block = _read(args.role_file).strip()
    industry_block = _read(args.industry_file).strip()

    if not os.path.exists(research_file):
        # First write: render the whole file from the template.
        templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
        skeleton = _skeleton(templates_dir, cfg['filenames']['research_file_template'])
        body = _fill(skeleton, {
            'company': args.company,
            'role': args.role,
            'app_id': args.app_id,
            'research_completed_date': args.date,
            'company_block': company_block,
            'role_block': role_block,
            'industry_block': industry_block,
        })
        _write(research_file, body)
    else:
        # Re-run: replace only role-intake's sections and the completed-date
        # line, so a current-state refresh does not clobber anything else.
        text = _read(research_file)
        text = re.sub(r'(?m)^\*\*Research completed:\*\* .*$',
                      f'**Research completed:** {args.date}', text)
        text = _replace_section(text, 'Company', company_block)
        text = _replace_section(text, 'Role', role_block)
        text = _replace_section(text, 'Industry', industry_block)
        _write(research_file, text)
    print(research_file)


# ---------------------------------------------------------------------------
# Subcommand: finalize  (role-intake Phase 7)
# Completes the session log: fills the research-completed date and replaces the
# pending axis sections with the axis-classifier subagent's output.
# ---------------------------------------------------------------------------

def cmd_finalize(args, repo_root, cfg):
    # repo_root and cfg are unused here by design: finalize only edits an existing
    # session log (path passed in), and the section headings it targets stay
    # inline rather than in config.
    text = _read(args.session_log)

    # Fill the research-completed date line in the Metadata section.
    text = re.sub(r'(?m)^- Research Completed Date: .*$',
                  f'- Research Completed Date: {args.date}', text)

    # The axis file holds both '## Axis Classification' and '## Axis Gaps'.
    # Split on the gaps heading so each section can be replaced on its own.
    axis_text = _read(args.axis_file).strip()
    parts = re.split(r'(?m)^(?=## Axis Gaps)', axis_text, maxsplit=1)
    classification_section = parts[0].strip()
    gaps_section = parts[1].strip() if len(parts) > 1 else '## Axis Gaps\n\nNone'

    text = _replace_section(text, 'Axis Classification', classification_section)
    text = _replace_section(text, 'Axis Gaps', gaps_section)
    _write(args.session_log, text)
    print(args.session_log)


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses the subcommand and its arguments, loads config, runs the subcommand,
# and reports any failure to stderr with a non-zero exit so the calling skill
# halts per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='role-intake artifact assembler')
    sub = parser.add_subparsers(dest='command', required=True)

    p_init = sub.add_parser('init', help='Phase 3: folder + JD + comms + initial session log')
    p_init.add_argument('--slug', required=True)
    p_init.add_argument('--app-id', required=True)
    p_init.add_argument('--ym', required=True, help='year-month, e.g. 2026-05')
    p_init.add_argument('--company', required=True)
    p_init.add_argument('--role', required=True)
    p_init.add_argument('--level', default=None)
    p_init.add_argument('--industry', required=True)
    p_init.add_argument('--start-date', required=True, help='YYYY-MM-DD')
    p_init.add_argument('--jd-text-file', required=True,
                        help='path to a file holding the extracted JD text')
    p_init.add_argument('--jd-source', required=True,
                        help='URL, original file path, or "pasted"')
    p_init.add_argument('--comms-text-file', default=None,
                        help='path to a file holding the extracted comms text (optional)')
    p_init.add_argument('--comms-source', default=None,
                        help='URL, original file path, or "pasted" (optional)')
    p_init.set_defaults(func=cmd_init)

    p_res = sub.add_parser('research', help='Phase 5: write research.md')
    p_res.add_argument('--folder', required=True, help='the application folder')
    p_res.add_argument('--app-id', required=True)
    p_res.add_argument('--company', required=True)
    p_res.add_argument('--role', required=True)
    p_res.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_res.add_argument('--company-file', required=True)
    p_res.add_argument('--role-file', required=True)
    p_res.add_argument('--industry-file', required=True)
    p_res.set_defaults(func=cmd_research)

    p_fin = sub.add_parser('finalize', help='Phase 7: complete the session log')
    p_fin.add_argument('--session-log', required=True)
    p_fin.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_fin.add_argument('--axis-file', required=True)
    p_fin.set_defaults(func=cmd_finalize)

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
