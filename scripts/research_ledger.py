#!/usr/bin/env python3
"""
research_ledger.py - files interview-prep research into research.md

The prep skills (preparation-screen, preparation-interview) dispatch the
prep-research agent and used to append each result by hand as its own '##'
section at the end of research.md, which put it after the file's Sources list.
This script files each result as one '### <target>' entry under
'## Interview prep', dated and attributed, and moves its sources to the
file's '## Sources' list (2026-11-17).

  add   File one prep-research block. The block is the agent's return:
        '## <target>', then '### Summary' / '### Key facts' / '### Sources'
        with plain markers ([1], [2]) and a numbered list ('1. <URL>'). Its
        headings drop one level; its markers become [pN], numbered by first
        citation and continuing after the last [pN] already in the file; its
        sources join the end of '## Sources'. The file is laid out first
        (role_research_assemble._layout), so an older research.md gains the
        Industry, Company, Title order and the end list on its first entry.

Author    : Jason Delosh
Created   : 2026-11-17
Project   : career
Usage     : python scripts/research_ledger.py add --folder ... --block-file ... --date YYYY-MM-DD --stage "<stage>"
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
from role_research_assemble import _layout

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PREP_SECTION = 'Interview prep'
PLACEHOLDER = 'No interview prep research yet.'
PREFIX = 'p'

# Regex: the agent's plain markers ([2]) and numbered source lines (2. <URL>).
_PLAIN_MARKER_RE = re.compile(r'\[(\d+)\]')
_NUMBERED_SOURCE_RE = re.compile(r'^\s*(\d+)\.\s+(https?://\S+)\s*$')
# Regex: a [pN] entry already in the file, to continue the numbering.
_PREP_ENTRY_RE = re.compile(r'(?m)^- \[p(\d+)\] ')


# ---------------------------------------------------------------------------
# Block conversion
# ---------------------------------------------------------------------------

def _convert(block, start, date, stage):
    """Return (entry text, source lines) for one prep-research block.

    Markers are renumbered from `start` by first citation; a marker with no
    numbered source keeps its number with the p prefix, so the research check
    reports it rather than it vanishing.
    """
    m = re.search(r'(?ms)^### Sources[ \t]*\n(.*?)(?=^#{1,3} |\Z)', block)
    body = (block[:m.start()] + block[m.end():]).strip() if m else block.strip()
    urls = {}
    for line in (m.group(1).split('\n') if m else []):
        s = _NUMBERED_SOURCE_RE.match(line)
        if s:
            urls[s.group(1)] = s.group(2)
    order = list(dict.fromkeys(n for n in _PLAIN_MARKER_RE.findall(body) if n in urls))
    order += [n for n in urls if n not in order]
    new = {old: str(start + i) for i, old in enumerate(order)}
    body = _PLAIN_MARKER_RE.sub(lambda mm: f'[{PREFIX}{new.get(mm.group(1), mm.group(1))}]', body)

    # Headings drop one level: the target becomes an entry under the section.
    lines = body.split('\n')
    if not lines or not lines[0].startswith('## '):
        raise ValueError('the block does not start with a "## <target>" heading')
    lines = [('#' + ln) if re.match(r'^#{2,3} ', ln) else ln for ln in lines]
    lines.insert(1, f'\n**Added:** {date} (interview prep, {stage})')
    sources = [f'- [{PREFIX}{new[old]}] {urls[old]}' for old in order]
    return '\n'.join(lines).strip(), sources


# ---------------------------------------------------------------------------
# Subcommand: add
# ---------------------------------------------------------------------------

def cmd_add(args, cfg):
    path = os.path.join(args.folder, cfg['filenames']['research_file'])
    if not os.path.isfile(path):
        raise FileNotFoundError(f'research file not found (run role-research first): {path}')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        raise ValueError(f'--date must be YYYY-MM-DD: {args.date}')
    text = _layout(_util.read(path))
    existing = [int(n) for n in _PREP_ENTRY_RE.findall(text)]
    entry, sources = _convert(_util.read(args.block_file), max(existing, default=0) + 1, args.date, args.stage)

    # The Interview prep section sits just before Sources; an older file gets one.
    if not re.search(rf'(?m)^## {PREP_SECTION}[ \t]*$', text):
        text = text.replace('\n## Sources', f'\n## {PREP_SECTION}\n\n{PLACEHOLDER}\n\n## Sources', 1)
    head, sep, tail = text.partition('\n## Sources')
    head = head.rstrip()
    if head.endswith(PLACEHOLDER):
        head = head[:-len(PLACEHOLDER)].rstrip()
    head += '\n\n' + entry
    tail = tail.rstrip() + ('\n' + '\n'.join(sources) if sources else '')
    _util.write(path, head + '\n' + sep + tail + '\n')
    print(path)


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='file interview-prep research into research.md')
    sub = parser.add_subparsers(dest='command', required=True)
    p_add = sub.add_parser('add', help='file one prep-research block under ## Interview prep')
    p_add.add_argument('--folder', required=True, help='the application folder')
    p_add.add_argument('--block-file', required=True, help='the prep-research block, as returned')
    p_add.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_add.add_argument('--stage', required=True, help='e.g. "phone screen", "hiring manager"')
    p_add.set_defaults(func=cmd_add)

    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        _, cfg = _config.load()
        args.func(args, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
