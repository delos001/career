#!/usr/bin/env python3
"""
jd_sentences.py - break jd.md into numbered units

Reads an application's jd.md and writes <app-folder>/scratch/jd_sentences.md:
the JD as numbered units under their section and subsection headings, so
every later step works from the same fixed breakdown instead of each agent
deciding where one requirement ends and the next begins. Used by role-extract
Phase 1, before the jd-splitter agent runs.

A unit is one sentence, or one part of a sentence split at a semicolon
(S-046a, S-046b). Each unit carries the jd.md line it came from.

Headings are never guessed. A section heading is a line marked '## ' and a
subheading one marked '### ', which only scripts/ingest/jd_headings.py writes,
for the headings and levels the user confirmed in role-intake Phase 5 (a
heading the user added, tagged '[added] ', is named without the tag). Every
other non-empty line is JD text, however short. (Until 2026-11-24 a short line
with no full stop was taken as a heading, which silently dropped short
requirement lines such as "PMP certification preferred", and a heading ending
in ':' was always a subheading, which nested top-level "Requirements:" under
an unrelated section.)

Fails loudly, writing nothing, when jd.md is missing or holds no JD text.

Author  : Jason Delosh
Created : 2026-11-17
Project : career
Usage   : python scripts/jd_sentences.py --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import functools
import os
import re
import sys

import _config
import _util
import jd_rules_slice
import jd_extraction_tables


# ---------------------------------------------------------------------------
# Patterns
# Layout patterns are fixed here because they describe text shape, not
# vocabulary.
# ---------------------------------------------------------------------------

# Regex: a list item's marker at the start of a line (bullet, dash, star, "1." or "1)").
_BULLET_RE = re.compile(r'^\s*(?:[•\-\*]|\d+[.)])\s+')

# Regex: a sentence end. Either end punctuation, whitespace, then a capital or
# '(', or end punctuation glued straight onto a capitalized word, which a
# pasted JD leaves behind ("permitted by law.Benefits include"). "e.g.," never
# matches, since a comma or lowercase word follows it.
_SENTENCE_END_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z(])|(?<=[a-z][.!?])(?=[A-Z][a-z])')

# Regex: a dotted abbreviation, letter groups each closed by a period ("U.S.",
# "e.g.", "Ph.D."). A sentence end found right after one is not a sentence end,
# so "the U.S. Medical team" stays one unit. Matched by shape, not by a list.
# Cost: a sentence that really ends on one ("based in the U.S. We offer")
# stays joined to the next, which keeps every word in one unit.
_DOTTED_ABBREV_RE = re.compile(r'\(?(?:[A-Za-z]{1,2}\.){2,}')

# The marks jd_headings.py puts in front of a confirmed section heading and a
# confirmed subheading.
HEADING_MARK = '## '
SUBHEADING_MARK = '### '

# Regex: either mark at the start of a line.
MARK_RE = re.compile(r'^#{2,3} ')

# The tag after the mark on a heading the user added at intake, one the posting
# itself does not have ('## [added] Compensation'); never part of the name.
ADDED_TAG = '[added] '


# ---------------------------------------------------------------------------
# Breaking the JD into units
# ---------------------------------------------------------------------------

def heading_mark(line):
    """Return the mark a line opens with (HEADING_MARK or SUBHEADING_MARK), or None for JD text."""
    for mark in (SUBHEADING_MARK, HEADING_MARK):
        if line.startswith(mark):
            return mark
    return None


def heading_text(line):
    """Return the heading on a marked line ('### Duties:' -> 'Duties:'), or None for JD text."""
    mark = heading_mark(line)
    return line[len(mark):].strip() if mark else None


@functools.lru_cache(maxsize=1)
def _abbreviations():
    """Return the single-period abbreviations from config sentence_abbreviations."""
    return frozenset(_config.load()[1]['sentence_abbreviations'])


def _is_abbreviation(token):
    """True when a token is a dotted abbreviation or a listed one ('U.S.', '(e.g.', 'Dr.')."""
    return bool(_DOTTED_ABBREV_RE.fullmatch(token)) or token.lstrip('(').rstrip('.') in _abbreviations()


def _sentences(text):
    """Return text cut at each sentence end, except one right after an abbreviation."""
    out, start = [], 0
    for m in _SENTENCE_END_RE.finditer(text):
        before = text[start:m.start()].split()
        if before and _is_abbreviation(before[-1]):
            continue
        out.append(text[start:m.start()])
        start = m.end()
    out.append(text[start:])
    return out


def _body_start(lines):
    """Return the index of the first JD line after the identity header.

    assemble.py ingest writes '**Role:** / **Company:**' then a '---' rule
    before the verbatim JD; a file without the header starts at line 1.
    """
    for i, line in enumerate(lines[:6]):
        if line.strip() == '---':
            return i + 1
    return 0


def units(jd_text):
    """Return [unit dict] for the JD: id, line, section, subsection, text.

    Works line by line: a sentence hard-wrapped across lines is rejoined in
    jd.md itself when it is saved (scripts/ingest/jd_unwrap.py).
    """
    lines = jd_text.split('\n')
    section = subsection = ''
    out, n = [], 0
    for index in range(_body_start(lines), len(lines)):
        text = lines[index].strip()
        if not text:
            continue
        mark = heading_mark(text)
        if mark is not None:
            # The level is the confirmed mark; a trailing colon is only spelling.
            name = heading_text(text).removeprefix(ADDED_TAG).rstrip(':').strip()
            if mark == SUBHEADING_MARK:
                subsection = name
            else:
                section, subsection = name, ''
            continue
        for sentence in (s.strip() for s in _sentences(_BULLET_RE.sub('', text))):
            if not sentence:
                continue
            n += 1
            parts = [p.strip() for p in sentence.split(';') if p.strip()]
            for k, part in enumerate(parts):
                out.append({'id': f'S-{n:03d}' + (chr(ord('a') + k) if len(parts) > 1 else ''),
                            'line': index + 1, 'section': section, 'subsection': subsection,
                            'text': part})
    return out


# ---------------------------------------------------------------------------
# Writing the file
# One table per section or subsection, in JD order.
# ---------------------------------------------------------------------------

def sentence_id(unit_id):
    """Return the sentence a unit belongs to: 'S-046' for 'S-046b' or 'S-046'.

    A unit id is the sentence id plus a part letter when the sentence was split
    at semicolons, so dropping the letter links the parts back together.
    """
    return re.match(r'S-\d+', unit_id).group(0)


# What a unit is lives in the SPLIT section of the JD rules file, on a line
# opening '**Unit:** '. The header copies it from there, so the definition is
# never typed into this script and cannot drift from the rules the splitter reads.
_UNIT_LABEL = '**Unit:** '


def unit_definition(split_rules):
    """Return the unit definition from the SPLIT rules text; raise when it is missing."""
    for line in split_rules.split('\n'):
        if line.startswith(_UNIT_LABEL):
            return line[len(_UNIT_LABEL):].strip()
    raise ValueError(f'the SPLIT rules have no line opening "{_UNIT_LABEL.strip()}"; nothing written')


def render(unit_list, jd_path, definition):
    """Return the jd_sentences.md text for the units; definition is unit_definition()'s text."""
    sentences = len({sentence_id(u['id']) for u in unit_list})
    out = ['# JD sentences', '',
           f'From `{jd_path}`: {sentences} sentences, {len(unit_list)} units.', '',
           'How to read this file:', '',
           f'- **Unit:** {definition}',
           '- **Unit ID:** every unit has its own row and Unit ID; drop the letter to get the sentence. '
           'Units are listed in job-description order, under their section heading.',
           '- **Line:** the `jd.md` line the unit came from.']
    current = None
    for u in unit_list:
        if (u['section'], u['subsection']) != current:
            current = (u['section'], u['subsection'])
            heading = u['section'] + (f" > {u['subsection']}" if u['subsection'] else '')
            out += ['', f'## {heading or "(no heading)"}', '',
                    '| Unit ID | Line | Unit |', '|---|---|---|']
        out.append(f"| {u['id']} | L{u['line']} | {u['text'].replace('|', '/')} |")
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------------------
# Reading the file
# role_extract_assemble.py joins the splitter's parts to this file, so the
# assembled split carries the units exactly as the splitter saw them.
# ---------------------------------------------------------------------------

def read(text):
    """Return [unit dict] from jd_sentences.md text: id, line (int), heading, text.

    heading is the '## ' heading the unit sits under ('' for '(no heading)').
    A file written before 2026-11-20 also has From and Hints columns; they
    are skipped.
    """
    heading, out = '', []
    for line in text.split('\n'):
        if line.startswith('## '):
            heading = line[3:].strip()
            heading = '' if heading == '(no heading)' else heading
            continue
        body = line.strip()
        if not body.startswith('|'):
            continue
        cells = [c.strip() for c in body.strip('|').split('|')]
        if len(cells) < 3 or not jd_extraction_tables.UNIT_ID_RE.match(cells[0]):
            continue
        # The older layout puts From ('bullet' or 'paragraph') third.
        text_at = 4 if len(cells) >= 5 and cells[2] in ('bullet', 'paragraph') else 2
        out.append({'id': cells[0], 'line': int(cells[1].lstrip('L')), 'heading': heading,
                    'text': ' | '.join(cells[text_at:])})
    return out


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Break jd.md into numbered units.')
    parser.add_argument('--folder', required=True, help='absolute path to the application folder')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    fn = cfg['filenames']

    jd_path = os.path.join(args.folder, fn['jd_file'])
    if not os.path.isfile(jd_path):
        print(f'Error: {jd_path} not found; role-intake writes it', file=sys.stderr)
        return 1
    unit_list = units(_util.read(jd_path))
    if not unit_list:
        print(f'Error: {jd_path} holds no JD text after its headings; nothing written', file=sys.stderr)
        return 1

    try:
        split_rules = jd_rules_slice.slice_steps(jd_rules_slice.load(repo_root, cfg), ['SPLIT'])
        definition = unit_definition(split_rules)
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    dest = os.path.join(args.folder, fn['scratch_subdir'], fn['jd_sentences_file'])
    _util.write(dest, render(unit_list, jd_path, definition))
    print(f'{dest} ({len(unit_list)} units)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
