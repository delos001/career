#!/usr/bin/env python3
"""
jd_unwrap.py - rejoin a job description's sentences that are hard-wrapped across lines

Some postings arrive hard-wrapped: one sentence broken over several lines
("...with the potential to deliver" / "transformative benefits"). Every reader
of jd.md, and role-extract's units, then sees fragments instead of sentences.

A line is joined to the one above it when the line above has no closing
punctuation and the line opens in lower case. A continuation opening in upper
case stays its own line, since it reads the same as a new item; role-intake
Phase 5 points those out for the user to fix by hand. A blank line or a marked
heading ('## ' / '### ') is never joined.

Moves line breaks only: before returning, it checks that the text with all
whitespace removed is unchanged, and refuses otherwise. assemble.py ingest runs
it as it writes jd.md, before any later step cites jd.md line numbers.

Author    : Jason Delosh
Created   : 2026-11-24
Project   : career
Usage     : python scripts/ingest/jd_unwrap.py <file> [--write]
            (assemble.py ingest calls unwrap() directly)
Depends   : scripts/_util.py; scripts/jd_sentences.py (heading marks, body start)
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _util  # noqa: E402
import jd_sentences  # noqa: E402


# ---------------------------------------------------------------------------
# Rejoining
# ---------------------------------------------------------------------------

# Regex: the end of a line that closes a sentence (end punctuation, then any
# closing quote or bracket).
_LINE_CLOSED_RE = re.compile(r'[.!?]["\')\]]*$')


def _continues(prev, line):
    """True when 'line' continues the sentence 'prev' left open."""
    return (bool(prev.strip()) and bool(line.strip())
            and jd_sentences.heading_mark(prev.strip()) is None
            and jd_sentences.heading_mark(line.strip()) is None
            and line.strip()[0].islower()
            and not _LINE_CLOSED_RE.search(prev.strip()))


def unwrap(text, start=0):
    """Return (text with hard-wrapped sentences rejoined, number of lines joined).

    Lines before index 'start' (jd.md's identity header) are left as they are.
    Raises ValueError if the result differs from the input by more than whitespace.
    """
    lines = text.split('\n')
    out, joined = lines[:start], 0
    for line in lines[start:]:
        if len(out) > start and _continues(out[-1], line):
            out[-1] = f'{out[-1].rstrip()} {line.strip()}'
            joined += 1
        else:
            out.append(line)
    new_text = '\n'.join(out)
    if re.sub(r'\s+', '', new_text) != re.sub(r'\s+', '', text):
        raise ValueError('rejoining changed the text itself')
    return new_text, joined


# ---------------------------------------------------------------------------
# Command-line entry point
# For a jd.md saved before ingest rejoined lines. Prints the count; writes
# only with --write.
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="rejoin a JD's hard-wrapped sentences")
    parser.add_argument('file', help='the JD file (jd.md)')
    parser.add_argument('--write', action='store_true', help='save the change; without it, only report')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    if not os.path.isfile(args.file):
        print(f'Error: file not found: {args.file}', file=sys.stderr)
        return 1
    text = _util.read(args.file)
    try:
        new_text, joined = unwrap(text, jd_sentences._body_start(text.split('\n')))
    except ValueError as e:
        print(f'Error: {e}; nothing written', file=sys.stderr)
        return 1
    if args.write and joined:
        _util.write(os.path.abspath(args.file), new_text)
        print(f'written {args.file} ({joined} line(s) joined)')
    else:
        print(f'{joined} line(s) would be joined' + ('' if args.write else ' (add --write to save)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
