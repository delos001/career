#!/usr/bin/env python3
"""
md_unwrap.py - enforce the no-hard-wrap markdown convention

The repo's markdown is written one paragraph or bullet per line; prose is never
hard-wrapped at a column. Hard wrapping forces a reflow on every edit, spreads
a one-word change across several diff lines, and makes multi-line text matches
fragile. This script joins hard-wrapped prose lines back into one line and
checks that none remain.

Only prose is touched. Fenced blocks, frontmatter, HTML comments, headings,
tables and blockquotes pass through byte for byte, which matters because the
templates carry machine-read skeletons inside fences. A line is joined onto
the one above only when both are ordinary prose; a line that opens a new block
(a list marker, a '**' lead, a 'Label:' lead, a {{token}}) always starts its
own line, as does any line after an explicit line break. When the rules are
unsure they leave the line alone: a missed join costs nothing, a wrong join
would change meaning.

The files in scope are the globs under markdown_no_wrap in config.yaml.

Author    : Jason Delosh
Created   : 2026-11-05
Project   : career
Usage     : python scripts/md_unwrap.py check            (exit 1 if any file would change)
            python scripts/md_unwrap.py apply            (rewrite files in place)
            python scripts/md_unwrap.py check --file F   (one file, any path)
Depends   : pyyaml (via _config)
"""

import argparse
import glob
import os
import re
import sys

import _config


# ---------------------------------------------------------------------------
# Line classification
# A "block start" may never be joined onto the line above. A "hard stop" may
# never take the next line as a continuation.
# ---------------------------------------------------------------------------

# A list item: '-', '*', '+', or '1.' / '1)' followed by whitespace.
_LIST_RE = re.compile(r'^\s*([-*+]|\d+[.)])\s+')
# A short capitalized label lead such as 'Route-back:' or 'Trigger:'. These
# are field lines, deliberately one per line even inside a list item.
_LABEL_RE = re.compile(r'^\s*[A-Z][A-Za-z0-9 /&()-]{0,30}:(\s|$)')
# A thematic break: three or more of the same '-', '*' or '_'.
_HR_RE = re.compile(r'^\s*([-*_])(\s*\1){2,}\s*$')
# Leads that make a line structural rather than prose.
_STRUCTURAL_LEADS = ('#', '|', '>', '<', '```', '~~~', '{{', '**')


def _is_fence(stripped):
    return stripped.startswith('```') or stripped.startswith('~~~')


def _is_block_start(line):
    """True when the line must begin its own line."""
    s = line.strip()
    return (not s or s.startswith(_STRUCTURAL_LEADS) or bool(_HR_RE.match(line))
            or bool(_LIST_RE.match(line)) or bool(_LABEL_RE.match(line)))


def _is_hard_stop(line):
    """True when the line may not take a continuation."""
    s = line.strip()
    return (not s or s.startswith(('#', '|', '>', '<')) or bool(_HR_RE.match(line))
            or line.endswith('  ') or line.endswith('\\') or line.endswith('<br>'))


# ---------------------------------------------------------------------------
# Unwrap
# One pass over the lines. Verbatim regions (frontmatter, fences, comments) are
# copied as they are. Elsewhere a line is joined onto the previous output line
# when the previous line can take a continuation and this line is prose at a
# compatible indent: top-level prose at indent 0, or list-item continuation.
# ---------------------------------------------------------------------------

def unwrap(text):
    """Return (new_text, joins) for one document's text ('\\n' line ends)."""
    lines = text.split('\n')
    out = []
    joins = 0
    in_front = bool(lines) and lines[0].strip() == '---'
    in_fence = in_comment = False
    joinable = False      # the last output line may take a continuation
    in_list = False       # inside a list item (continuations are indented)
    prev_blank = True

    for i, line in enumerate(lines):
        s = line.strip()

        # Verbatim regions.
        if in_front:
            out.append(line)
            if i > 0 and s == '---':
                in_front = False
            joinable = False
            continue
        if _is_fence(s):
            in_fence = not in_fence
            out.append(line)
            joinable = False
            continue
        if in_fence:
            out.append(line)
            continue
        if in_comment or s.startswith('<!--'):
            in_comment = '-->' not in s
            out.append(line)
            joinable = False
            continue

        indent = len(line) - len(line.lstrip())
        if joinable and not _is_block_start(line) and (indent == 0 or in_list):
            out[-1] = out[-1].rstrip() + ' ' + s
            joins += 1
        else:
            out.append(line)
            # List context starts at a list marker and ends at a new top-level
            # paragraph (an unindented, non-list line after a blank line).
            if _LIST_RE.match(line):
                in_list = True
            elif s and indent == 0 and prev_blank:
                in_list = False

        joinable = not _is_hard_stop(out[-1])
        prev_blank = not s

    return '\n'.join(out), joins


# ---------------------------------------------------------------------------
# File handling
# Line endings are preserved: a CRLF file is normalized for the pass and
# written back as CRLF.
# ---------------------------------------------------------------------------

def _process(path, write):
    """Return the join count for one file; rewrite it when write is set."""
    with open(path, encoding='utf-8', newline='') as f:
        raw = f.read()
    crlf = '\r\n' in raw
    new, joins = unwrap(raw.replace('\r\n', '\n'))
    if joins and write:
        if crlf:
            new = new.replace('\n', '\r\n')
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(new)
    return joins


def _scope(repo_root, cfg):
    """Return the in-scope files, sorted, from the configured globs."""
    files = set()
    for pattern in cfg['markdown_no_wrap']['globs']:
        files.update(glob.glob(os.path.join(repo_root, pattern), recursive=True))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description='Enforce the no-hard-wrap markdown convention.')
    parser.add_argument('command', choices=('check', 'apply'))
    parser.add_argument('--file', action='append',
                        help='check or apply one file instead of the configured scope (repeatable)')
    args = parser.parse_args()

    repo_root, cfg = _config.load()
    files = [os.path.abspath(f) for f in args.file] if args.file else _scope(repo_root, cfg)

    total = 0
    for path in files:
        joins = _process(path, write=args.command == 'apply')
        if joins:
            total += joins
            print(f'{joins:5d}  {os.path.relpath(path, repo_root)}')
    verb = 'joined' if args.command == 'apply' else 'hard-wrapped lines'
    print(f'{total} {verb} across {len(files)} file(s)')
    return 1 if (args.command == 'check' and total) else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
