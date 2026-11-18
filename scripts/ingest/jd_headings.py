#!/usr/bin/env python3
"""
jd_headings.py - put a job description's section headings back on their own lines

A JD copied from a job board often loses the line break before (and sometimes
after) each section heading, so the heading ends up glued to the paragraph of
the section before it: "...business outcomes.  Duties & Responsibilities".
Every reader of jd.md then has to guess which section a sentence belongs to.

This script moves line breaks only. The caller names the headings (deciding
what is a heading is a judgment the user confirms; the script does not guess),
and the script puts each one on its own line. It never adds, removes or changes
a word: before writing, it checks that the text with all whitespace removed is
identical to the input, and refuses to write if it is not.

Rules for a heading match:
  - case-sensitive, and the heading must stand alone: the character before it
    is the line start, whitespace or punctuation, and the character after it
    is the line end, whitespace or punctuation;
  - a colon directly after the heading stays with it, so a run-in subheading
    keeps its colon whether or not the caller includes it;
  - longer headings are matched first, so "Additional Duties & Responsibilities"
    is not also counted as "Duties & Responsibilities";
  - each heading must occur exactly once. None means a typo and stops the run.
    More than one stops the run and lists each occurrence with its line, so the
    caller can pick the heading and re-run with --nth "<heading>" <N>.
A heading already on its own line is left as it is. On jd.md, the identity
header ingest writes above the '---' rule is not searched.

Without --write the script prints each split as before/after and changes
nothing. With --write it saves the file in place.

Author    : Jason Delosh
Created   : 2026-11-17
Project   : career
Usage     : python scripts/ingest/jd_headings.py <file> --heading "<text>" [--heading ...]
            [--nth "<text>" <N> ...] [--write]
Depends   : scripts/_util.py; scripts/jd_sentences.py (where jd.md's body starts)
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _util  # noqa: E402
import jd_sentences  # noqa: E402


# ---------------------------------------------------------------------------
# Finding the headings
# Each heading is located as a stand-alone run of text on one line. Matches are
# collected longest heading first, and a shorter heading's match that falls
# inside a longer one's span is discarded, so nested headings are not double
# counted.
# ---------------------------------------------------------------------------

def find_headings(lines, headings, start=0):
    """Return {heading: [(line_index, start, end), ...]} for every stand-alone match.

    'lines' is the file split on newlines; positions are character offsets in
    that line. A match counts only when it is bounded on both sides by the line
    edge, whitespace or punctuation (anything that is not a letter or digit).
    Lines before index 'start' (jd.md's identity header) are not searched.
    """
    taken = {}      # line_index -> list of (start, end) spans already claimed
    found = {h: [] for h in headings}
    for heading in sorted(headings, key=len, reverse=True):
        # ':?' keeps a run-in subheading's colon with the heading even when the
        # caller leaves it off; jd_sentences.py reads that colon as a subsection.
        pattern = re.compile(r'(?<![^\W_])' + re.escape(heading) + r':?(?![^\W_])')
        for i, line in enumerate(lines):
            if i < start:
                continue
            for m in pattern.finditer(line):
                spans = taken.setdefault(i, [])
                if any(m.start() < e and s < m.end() for s, e in spans):
                    continue    # inside a longer heading already matched
                spans.append((m.start(), m.end()))
                found[heading].append((i, m.start(), m.end()))
    return found


# ---------------------------------------------------------------------------
# Splitting the lines
# Each line holding a heading is cut at the heading's edges. Spaces at a cut are
# dropped (they were only there because the line break was lost); empty pieces
# are dropped, so a heading already alone on its line yields just itself.
# ---------------------------------------------------------------------------

def split_lines(lines, found):
    """Return (new_lines, changes); changes is [(line_number, before, [after lines])]."""
    cuts = {}       # line_index -> sorted list of (start, end)
    for matches in found.values():
        for i, s, e in matches:
            cuts.setdefault(i, []).append((s, e))

    new_lines, changes = [], []
    for i, line in enumerate(lines):
        if i not in cuts:
            new_lines.append(line)
            continue
        pieces, pos = [], 0
        for s, e in sorted(cuts[i]):
            pieces.append(line[pos:s])
            pieces.append(line[s:e])
            pos = e
        pieces.append(line[pos:])
        pieces = [p.strip() for p in pieces if p.strip()]
        new_lines.extend(pieces)
        if pieces != [line.strip()]:
            changes.append((i + 1, line, pieces))
    return new_lines, changes


def same_words(a, b):
    """True when a and b are identical once every whitespace character is removed."""
    return re.sub(r'\s+', '', a) == re.sub(r'\s+', '', b)


# ---------------------------------------------------------------------------
# Reporting
# Each changed line is shown with its original line number, then the lines it
# becomes. Long paragraph text is shortened around the cut so the output stays
# readable; the file itself is never shortened.
# ---------------------------------------------------------------------------

def _clip(text, keep=60):
    """Shorten a long line to its first and last 'keep' characters."""
    return text if len(text) <= 2 * keep + 5 else f'{text[:keep]} ... {text[-keep:]}'


def report(changes):
    """Return the before/after text for every changed line."""
    out = []
    for number, before, after in changes:
        out.append(f'line {number} before: {_clip(before)}')
        for piece in after:
            out.append(f'        after:  {_clip(piece)}')
        out.append('')
    return '\n'.join(out).rstrip()


# ---------------------------------------------------------------------------
# Command-line entry point
# Reads the file, finds and checks every heading, splits, verifies that no word
# changed, then prints the before/after and writes only when --write is given.
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="put a JD's section headings on their own lines")
    parser.add_argument('file', help='the JD text file (jd.md, or the intake text file)')
    parser.add_argument('--heading', action='append', default=[],
                        help='a section heading exactly as it appears; repeat for each one')
    parser.add_argument('--nth', action='append', nargs=2, default=[], metavar=('HEADING', 'N'),
                        help='a heading that appears more than once: use its Nth occurrence; repeat for each one')
    parser.add_argument('--write', action='store_true',
                        help='save the change; without it the script only prints the before/after')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    if not os.path.isfile(args.file):
        print(f'Error: file not found: {args.file}', file=sys.stderr)
        return 1
    text = _util.read(args.file)
    trailing_newline = text.endswith('\n')
    lines = text.split('\n')
    if trailing_newline:
        lines = lines[:-1]

    # Each heading must occur exactly once unless --nth names the occurrence to
    # use; otherwise the run stops before any change.
    problems = []
    nth = {}
    for heading, n in args.nth:
        if not n.isdigit() or int(n) < 1:
            problems.append(f'--nth "{heading}" {n}: N must be a whole number from 1')
        else:
            nth[heading] = int(n)
    headings = list(dict.fromkeys(args.heading + list(nth)))
    if not headings:
        parser.error('give at least one --heading or --nth')
    # jd.md opens with the '**Role:** / **Company:**' header ingest writes; the
    # same body-start rule role-extract uses keeps it out of the search.
    found = find_headings(lines, headings, jd_sentences._body_start(lines))
    for heading, matches in found.items():
        if not matches:
            problems.append(f'"{heading}" does not appear as a stand-alone heading')
        elif heading in nth:
            if nth[heading] > len(matches):
                problems.append(f'--nth "{heading}" {nth[heading]}: it appears only {len(matches)} time(s)')
            else:
                found[heading] = [matches[nth[heading] - 1]]
        elif len(matches) > 1:
            # List each occurrence with the text around it, so the caller can
            # pick the one that is the heading and re-run with --nth.
            problems.append(f'"{heading}" appears {len(matches)} times; re-run with --nth "{heading}" <N>:')
            for k, (i, s, e) in enumerate(matches, 1):
                problems.append(f'  {k}: line {i + 1}: ...{lines[i][max(0, s - 40):e + 40]}...')
    if problems:
        for p in problems:
            print(p if p.startswith('  ') else f'Error: {p}', file=sys.stderr)
        return 1

    new_lines, changes = split_lines(lines, found)
    new_text = '\n'.join(new_lines) + ('\n' if trailing_newline else '')

    # The guarantee this script exists to keep: line breaks moved, words untouched.
    if not same_words(text, new_text):
        print('Error: the split changed the text itself; nothing written', file=sys.stderr)
        return 1

    if not changes:
        print('No change: every heading is already on its own line.')
        return 0
    print(report(changes))
    if args.write:
        _util.write(os.path.abspath(args.file), new_text)
        print(f'\nwritten {args.file} ({len(changes)} line(s) split)')
    else:
        print(f'\n{len(changes)} line(s) would be split; nothing written (add --write to save)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
