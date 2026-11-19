#!/usr/bin/env python3
"""
jd_sentences.py - break jd.md into numbered units with mechanical hints

Reads an application's jd.md and writes <app-folder>/scratch/jd_sentences.md:
the JD as numbered units under their section and subsection headings, so
every later step works from the same fixed breakdown instead of each agent
deciding where one requirement ends and the next begins. Used by role-extract
Phase 1, before the jd-splitter agent runs.

A unit is one sentence, or one part of a sentence split at a semicolon
(S-046a, S-046b). Each unit carries:
  Line   the jd.md line it came from
  From   'bullet' when its line is a list item, else 'paragraph'
  Hints  words the script found in the unit's text, never a verdict:
           continues S-NNN  opens with a pointer word (config
                            jd_sentence_continues_words)
           optional: <word> holds an optional word (config
                            requirement_optional_words)
           years: <count>   holds a year count (config requirement_year_count)
           degree           names a degree (config jd_sentence_degree_words)

Headings are found from layout, so jd.md must have its headings on their own
lines (scripts/ingest/jd_headings.py, GitHub #93): a short line with no
sentence-ending punctuation is a heading; one ending in ':' is a subheading
under the last heading.

Fails loudly, writing nothing, when jd.md is missing or holds no JD text.

Author  : Jason Delosh
Created : 2026-11-17
Project : career
Usage   : python scripts/jd_sentences.py --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
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
# vocabulary; the word lists the hints use come from config.yaml.
# ---------------------------------------------------------------------------

# Regex: a list item's marker at the start of a line (bullet, dash, star, "1." or "1)").
_BULLET_RE = re.compile(r'^\s*(?:[•\-\*]|\d+[.)])\s+')

# Regex: a sentence end. Either end punctuation, whitespace, then a capital or
# '(', or end punctuation glued straight onto a capitalized word, which a
# pasted JD leaves behind ("permitted by law.Benefits include"). "e.g.," never
# matches, since a comma or lowercase word follows it.
_SENTENCE_END_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z(])|(?<=[a-z][.!?])(?=[A-Z][a-z])')

# A heading is at most this many words; longer lines are text even without a full stop.
_HEADING_MAX_WORDS = 8


# ---------------------------------------------------------------------------
# Breaking the JD into units
# ---------------------------------------------------------------------------

def _is_heading(text):
    """True for a short line with no sentence-ending punctuation that is not a list item."""
    return (not _BULLET_RE.match(text) and len(text.split()) <= _HEADING_MAX_WORDS
            and not re.search(r'[.!?]$', text))


def _body_start(lines):
    """Return the index of the first JD line after the identity header.

    assemble.py ingest writes '**Role:** / **Company:**' then a '---' rule
    before the verbatim JD; a file without the header starts at line 1.
    """
    for i, line in enumerate(lines[:6]):
        if line.strip() == '---':
            return i + 1
    return 0


def units(jd_text, cfg):
    """Return [unit dict] for the JD: id, line, section, subsection, from, hints, text."""
    continues = re.compile(rf"^{cfg['jd_sentence_continues_words']}\b", re.I)
    years = re.compile(cfg['requirement_year_count'], re.I)
    degree = re.compile(rf"\b{cfg['jd_sentence_degree_words']}\b", re.I)
    lines = jd_text.split('\n')
    section = subsection = ''
    out, n = [], 0
    for index in range(_body_start(lines), len(lines)):
        text = lines[index].strip()
        if not text:
            continue
        if _is_heading(text):
            if text.endswith(':'):
                subsection = text.rstrip(':').strip()
            else:
                section, subsection = text, ''
            continue
        source = 'bullet' if _BULLET_RE.match(text) else 'paragraph'
        for sentence in (s.strip() for s in _SENTENCE_END_RE.split(_BULLET_RE.sub('', text))):
            if not sentence:
                continue
            n += 1
            parts = [p.strip() for p in sentence.split(';') if p.strip()]
            for k, part in enumerate(parts):
                hints = []
                # Only a sentence's first part can point back; a part after a
                # semicolon continues its own sentence by construction.
                if k == 0 and out and continues.match(part):
                    hints.append(f"continues {out[-1]['id']}")
                word = jd_extraction_tables.optional_word(part, cfg['requirement_optional_words'])
                if word:
                    hints.append(f'optional: {word}')
                counts = list(dict.fromkeys(m.group(0) for m in years.finditer(part)))
                if counts:
                    hints.append('years: ' + ', '.join(counts))
                if degree.search(part):
                    hints.append('degree')
                out.append({'id': f'S-{n:03d}' + (chr(ord('a') + k) if len(parts) > 1 else ''),
                            'line': index + 1, 'section': section, 'subsection': subsection,
                            'from': source, 'hints': hints, 'text': part})
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
           '- **Line:** the `jd.md` line the unit came from.',
           '- **From:** `bullet` when that line is a list item, else `paragraph`.',
           '- **Hints:** words found in the unit\'s text: `continues S-NNN` (opens with a word '
           'pointing back to the unit before), `optional: <word>`, `years: <count>`, `degree`. '
           'Never a verdict.']
    current = None
    for u in unit_list:
        if (u['section'], u['subsection']) != current:
            current = (u['section'], u['subsection'])
            heading = u['section'] + (f" > {u['subsection']}" if u['subsection'] else '')
            out += ['', f'## {heading or "(no heading)"}', '',
                    '| Unit ID | Line | From | Hints | Unit |', '|---|---|---|---|---|']
        out.append(f"| {u['id']} | L{u['line']} | {u['from']} | {'; '.join(u['hints'])} | "
                   f"{u['text'].replace('|', '/')} |")
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------------------
# Reading the file
# role_extract_assemble.py joins the splitter's parts to this file, so the
# assembled split carries the units exactly as the splitter saw them.
# ---------------------------------------------------------------------------

def read(text):
    """Return [unit dict] from jd_sentences.md text: id, line (int), heading, from, hints, text.

    heading is the '## ' heading the unit sits under ('' for '(no heading)');
    hints is the list render() joined with '; '.
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
        if len(cells) < 5 or not jd_extraction_tables.UNIT_ID_RE.match(cells[0]):
            continue
        out.append({'id': cells[0], 'line': int(cells[1].lstrip('L')), 'heading': heading,
                    'from': cells[2], 'hints': [h for h in cells[3].split('; ') if h],
                    'text': ' | '.join(cells[4:])})
    return out


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Break jd.md into numbered units with hints.')
    parser.add_argument('--folder', required=True, help='absolute path to the application folder')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    fn = cfg['filenames']

    jd_path = os.path.join(args.folder, fn['jd_file'])
    if not os.path.isfile(jd_path):
        print(f'Error: {jd_path} not found; role-intake writes it', file=sys.stderr)
        return 1
    unit_list = units(_util.read(jd_path), cfg)
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
