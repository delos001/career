#!/usr/bin/env python3
"""
role_research_assemble.py - role-research artifact writer

Writes research.md from the three research agents' output blocks (company,
role, industry) and fills the session log's research-completed date, so the
role-research skill writes files through a deterministic tool instead of by
hand. Moved out of assemble.py when research became its own skill (2026-11-16).

  research  Write (or, on a re-run, refresh) research.md. The APP-NNN, company
            and role come from the session log, never from the caller. Axis
            Gaps is written pending for role-classify. On a re-run only the
            Company, Role and Industry sections and the completed date are
            replaced, so sections other skills added are left in place.

Nothing repo-dependent is hardcoded here: filenames and the template location
come from config.yaml (via _config); the structure comes from
templates/research_file.md.

Author    : Jason Delosh
Created   : 2026-11-16
Project   : career
Usage     : python scripts/role_research_assemble.py research --folder ... --date ...
                --company-file ... --role-file ... --industry-file ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
from assemble import _fill, _replace_section, _skeleton
from role_research_qc import _metadata_fields


# ---------------------------------------------------------------------------
# Subcommand: research
# ---------------------------------------------------------------------------

def cmd_research(args, repo_root, cfg):
    research_file = os.path.join(args.folder, cfg['filenames']['research_file'])
    session_log = os.path.join(args.folder, cfg['filenames']['session_log_file'])
    if not os.path.exists(session_log):
        raise FileNotFoundError(f'session log not found (run role-intake first): {session_log}')
    # The application's identity comes from its session log, never from the
    # caller, so a resumed run has nothing to carry over by hand.
    meta = _metadata_fields(_util.read(session_log)) or {}
    for field in ('APP-NNN', 'Company', 'Role'):
        if not meta.get(field):
            raise ValueError(f'session log has no {field} value: {session_log}')
    company_block = _util.read(args.company_file).strip()
    role_block = _util.read(args.role_file).strip()
    industry_block = _util.read(args.industry_file).strip()

    if not os.path.exists(research_file):
        # First write: render the whole file from the template.
        templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
        skeleton = _skeleton(templates_dir, cfg['filenames']['research_file_template'])
        body = _fill(skeleton, {
            'company': meta['Company'],
            'role': meta['Role'],
            'app_id': meta['APP-NNN'],
            'research_completed_date': args.date,
            'company_block': company_block,
            'role_block': role_block,
            'industry_block': industry_block,
            # Filled by the role-classify skill.
            'axis_gaps': '## Axis Gaps\n\n_(pending)_',
        })
        _util.write(research_file, body)
    else:
        # Re-run: replace only the research sections and the completed-date
        # line, so a current-state refresh does not clobber anything else.
        text = _util.read(research_file)
        # Lambda replacement: the value is inserted literally, never read as a
        # regex template.
        text = re.sub(r'(?m)^\*\*Research completed:\*\* .*$',
                      lambda _m: f'**Research completed:** {args.date}', text)
        text = _replace_section(text, 'Company', company_block)
        text = _replace_section(text, 'Role', role_block)
        text = _replace_section(text, 'Industry', industry_block)
        _util.write(research_file, text)
    log_text = re.sub(r'(?m)^- Research Completed Date: .*$',
                      lambda _m: f'- Research Completed Date: {args.date}', _util.read(session_log))
    _util.write(session_log, log_text)
    print(research_file)


# ---------------------------------------------------------------------------
# Command-line entry point
# Reports failure to stderr with exit 1 so the calling skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='role-research artifact writer')
    sub = parser.add_subparsers(dest='command', required=True)

    p_res = sub.add_parser('research', help='write research.md; APP-NNN, company and role '
                                            'come from the session log')
    p_res.add_argument('--folder', required=True, help='the application folder')
    p_res.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_res.add_argument('--company-file', required=True)
    p_res.add_argument('--role-file', required=True)
    p_res.add_argument('--industry-file', required=True)
    p_res.set_defaults(func=cmd_research)

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
