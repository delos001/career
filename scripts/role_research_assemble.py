#!/usr/bin/env python3
"""
role_research_assemble.py - role-research artifact writer

Writes research.md from the three research agents' output blocks (company,
role, industry) and fills the session log's research-completed date, so the
role-research skill writes files through a deterministic tool instead of by
hand. Moved out of assemble.py when research became its own skill (2026-11-16).

  research  Write (or, on a re-run, refresh) research.md. The APP-NNN, company
            and role come from the session log, never from the caller. On a
            re-run only the Industry, Company and Title sections and the
            completed date are replaced, so sections other skills added are
            left in place. Every write lays the file out as Industry, Company,
            Title, other sections, then one Sources list in citation order (see
            Layout). An older file's '## Role' is renamed '## Title'.

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
from role_research_qc import (BLOCK_PREFIX, LEGACY_HEADINGS, RESEARCH_BLOCKS, _MARKER_RE, _SOURCE_ENTRY_RE,
                              _metadata_fields, research_heading)


# ---------------------------------------------------------------------------
# Layout (2026-11-17)
# research.md reads Industry, Company, Title (RESEARCH_BLOCKS order), then any
# section another skill added, then one `## Sources` list. Each agent block
# arrives with its own `### Sources`; the list moves to the end of the file and
# the section's markers are renumbered by first citation, so the list follows
# the body whatever order the agent numbered in.
# ---------------------------------------------------------------------------

# Regex: a block's '### Sources' subsection, up to the next heading or the end.
_BLOCK_SOURCES_RE = re.compile(r'(?ms)^### Sources[ \t]*\n(.*?)(?=^#{1,3} |\Z)')


def _split_sources(block, prefix):
    """Return (block without its Sources subsection, its source lines).

    Marker-style lines (`- [c1] <URL>`) are renumbered by first citation in
    the block, and the block's markers with them. Older inline-URL lists move
    as they are. Uncited or unmatched lines are kept, last, for QC to report.
    """
    m = _BLOCK_SOURCES_RE.search(block)
    if not m:
        return block.strip(), []
    body = (block[:m.start()] + block[m.end():]).strip()
    lines = [ln.strip() for ln in m.group(1).split('\n') if ln.strip()]
    entries = {}
    for ln in lines:
        e = _SOURCE_ENTRY_RE.match(ln)
        if e and e.group(1) == prefix:
            entries[e.group(2)] = ln
    if not entries:
        return body, lines
    order = []
    for letter, num in _MARKER_RE.findall(body):
        if letter == prefix and num in entries and num not in order:
            order.append(num)
    order += [num for num in entries if num not in order]
    new = {old: str(i) for i, old in enumerate(order, 1)}
    body = _MARKER_RE.sub(
        lambda mm: f'[{prefix}{new[mm.group(2)]}]' if mm.group(1) == prefix and mm.group(2) in new
        else mm.group(0), body)
    renumbered = [re.sub(r'^- \[[a-z]\d+\]', f'- [{prefix}{new[old]}]', entries[old]) for old in order]
    others = [ln for ln in lines if ln not in entries.values()]
    return body, renumbered + others


def _layout(text):
    """Return research.md rebuilt in reading order with all sources last."""
    first = re.search(r'(?m)^## ', text)
    header = (text[:first.start()] if first else text).rstrip()
    sections = re.split(r'(?m)^(?=## )', text[first.start():]) if first else []
    # An older file's '## Role' takes the current name, '## Title'.
    headings = {s.split('\n', 1)[0][3:].strip() for s in sections}
    for new, old in LEGACY_HEADINGS.items():
        if old in headings and new not in headings:
            sections = [f'## {new}' + s[3 + len(old):] if s.split('\n', 1)[0][3:].strip() == old else s
                        for s in sections]
    named = {}
    for section in sections:
        heading = section.split('\n', 1)[0][3:].strip()
        named.setdefault(heading, []).append(section.strip())
    # The end list already on file (a laid-out file): a research section that
    # brings its own Sources replaces its entries there; one that does not keeps
    # them. Lines that belong to no research section (prep [pN] entries, older
    # plain URLs) follow in their existing order.
    kept = [ln.strip() for sec in named.pop('Sources', []) for ln in sec.split('\n')[1:] if ln.strip()]

    def prefix_of(line):
        m = _SOURCE_ENTRY_RE.match(line)
        return m.group(1) if m else None

    parts, sources = [header], []
    for name in RESEARCH_BLOCKS:
        prefix = BLOCK_PREFIX[name]
        for section in named.pop(name, []):
            body, lines = _split_sources(section, prefix)
            parts.append(body)
            sources += lines or [ln for ln in kept if prefix_of(ln) == prefix]
    sources += [ln for ln in kept if prefix_of(ln) not in BLOCK_PREFIX.values()]
    for section in sections:
        heading = section.split('\n', 1)[0][3:].strip()
        if heading in named:
            parts += named.pop(heading)
    parts.append('## Sources\n\n' + '\n'.join(sources))
    return '\n\n'.join(parts) + '\n'


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
        })
        _util.write(research_file, _layout(body))
    else:
        # Re-run: replace only the research sections and the completed-date
        # line, so a current-state refresh does not clobber anything else.
        text = _util.read(research_file)
        # Lambda replacement: the value is inserted literally, never read as a
        # regex template.
        text = re.sub(r'(?m)^\*\*Research completed:\*\* .*$',
                      lambda _m: f'**Research completed:** {args.date}', text)
        text = _replace_section(text, 'Company', company_block)
        text = _replace_section(text, research_heading(text, 'Title'), role_block)
        text = _replace_section(text, 'Industry', industry_block)
        _util.write(research_file, _layout(text))
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
