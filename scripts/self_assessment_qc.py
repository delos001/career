#!/usr/bin/env python3
"""
self_assessment_qc.py - deterministic QC for a self-assessment product

Validates one product file (profile_<date>.md) against the mechanical rules of
rules/self-assessment/assessment-protocol.md. Judgment checks (grades matching
evidence, hedge survival, neutrality) belong to the qc-self-assessment agent
and are not attempted here. Every pattern and threshold comes from
config.yaml's self_assessment block; nothing protocol-specific is hardcoded.

Checks
  V1  product names the protocol version it ran under, and the stamped
      version number matches the current version declared in the protocol
      file (resolved via config paths, read at run time)
  H1  every required product heading present, in canonical order
  L1  the three mandatory How-to-read labels present
  L2  corpus-limitation (Scope) statement present
  E1  no em dashes
  E2  no "not X, it's Y" constructions
  G1  every "(inferred ...)" parenthetical carries an anchored confidence term
  R1  no sentence longer than the configured word ceiling (prose paragraphs
      and bullet lines both measured)
  R2  no prose paragraph longer than the configured character ceiling
      (bullet lists and headings are exempt; the ceiling targets wall-of-text
      paragraphs, which bullets are the cure for)

Usage
  python self_assessment_qc.py check --file <absolute-path-to-product>

Exit code 0 when all checks pass, 1 otherwise. Findings print one per line as
'CHECK  PASS|FAIL  detail'.

Author    : Jason Delosh
Created   : 2026-07-10
Project   : career
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prose_paragraphs(text):
    """Split into (start_line, block_text) prose paragraphs.

    Blocks are runs of non-blank lines. Lines that are headings, bullets,
    tables, or horizontal rules are excluded from a block's measured text, so
    the paragraph-length check targets only wall-of-text prose.
    """
    paragraphs = []
    block, start = [], None
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        is_prose = (stripped
                    and not stripped.startswith(('#', '-', '*', '|', '>'))
                    and stripped != '---')
        if is_prose:
            if start is None:
                start = i
            block.append(stripped)
        else:
            if block:
                paragraphs.append((start, ' '.join(block)))
            block, start = [], None
    if block:
        paragraphs.append((start, ' '.join(block)))
    return paragraphs


def _bullet_lines(text):
    """(line_number, text) for bullet lines, marker stripped.

    R1 measures sentences in bullets too (rule 9's sentence rule has no
    bullet exemption); R2 deliberately does not, since bullets are its cure,
    not its target. Only '- ' / '* ' markers count as bullets, which keeps
    bold-opening lines and horizontal rules out.
    """
    for i, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(('- ', '* ')):
            yield i, stripped[2:].strip()


def _sentences(paragraph_text):
    """Naive sentence split on terminal punctuation followed by whitespace.

    Good enough for a word-count ceiling; abbreviations may over-split, which
    only ever makes the check more lenient (shorter fragments), never stricter.
    """
    return re.split(r'(?<=[.!?])\s+', paragraph_text)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def run_checks(text, spec, findings, protocol_version):
    """Run V1-R2 against the product text. Appends (check, ok, detail)."""

    # V1: protocol version stamp, and it must name the current version.
    stamp = re.search(spec['version_stamp_regex'], text, re.IGNORECASE)
    if stamp is None:
        findings.append(('V1', False,
                         'product does not name the protocol version it ran under'))
    else:
        stamped = re.search(r'\d+', stamp.group(0)).group(0)
        if stamped == protocol_version:
            findings.append(('V1', True,
                             f'protocol version named and current (v{stamped})'))
        else:
            findings.append(('V1', False,
                             f'product stamps protocol v{stamped}; current '
                             f'protocol is v{protocol_version}'))

    # H1: required headings, in canonical order.
    heading_lines = [(i, line) for i, line in enumerate(text.splitlines(), 1)
                     if line.startswith('#')]
    cursor, missing, out_of_order = 0, [], []
    for pattern in spec['required_headings']:
        rx = re.compile(pattern)
        # first heading matching the pattern, as an index into heading_lines
        hit_idx = next((idx for idx, (_, ln) in enumerate(heading_lines)
                        if rx.search(ln)), None)
        if hit_idx is None:
            missing.append(pattern)
        elif hit_idx < cursor:
            out_of_order.append(pattern)
        else:
            cursor = hit_idx
    if missing or out_of_order:
        detail = []
        if missing:
            detail.append('missing: ' + '; '.join(missing))
        if out_of_order:
            detail.append('out of order: ' + '; '.join(out_of_order))
        findings.append(('H1', False, ' | '.join(detail)))
    else:
        findings.append(('H1', True, 'all required headings present in order'))

    # L1: the mandatory labels. Case-insensitive: a label fragment may open
    # a sentence and pick up a capital.
    text_lower = text.lower()
    absent = [p for p in spec['required_labels'] if p.lower() not in text_lower]
    findings.append(('L1', not absent,
                     'labels missing: ' + '; '.join(absent) if absent
                     else 'all mandatory labels present'))

    # L2: corpus-limitation statement marker.
    findings.append(('L2', bool(re.search(spec['scope_marker'], text)),
                     'corpus-limitation (Scope) statement '
                     + ('present' if re.search(spec['scope_marker'], text)
                        else 'missing')))

    # E1: em dashes.
    dash_count = text.count('—')
    findings.append(('E1', dash_count == 0,
                     f'{dash_count} em dash(es) found' if dash_count
                     else 'no em dashes'))

    # E2: "not X, it's Y" construction. Bounded lookahead keeps the match to a
    # single clause so ordinary uses of "not" across sentences don't trip it.
    e2_hits = re.findall(r"\bnot\b[^.\n]{0,60},\s*(?:it's|it is)\b", text,
                         re.IGNORECASE)
    findings.append(('E2', not e2_hits,
                     f'{len(e2_hits)} "not X, it\'s Y" construction(s)'
                     if e2_hits else 'none found'))

    # G1: every inferred parenthetical carries an anchored confidence term.
    # Matches "(inferred" through the closing paren; the term must appear
    # inside that parenthetical. Boundaries exclude word chars AND hyphens so
    # a hyphenated compound (e.g. "moderate-to-high") never passes via one of
    # its parts; only the exact anchored terms count.
    terms = sorted(spec['confidence_terms'], key=len, reverse=True)
    term_rx = re.compile('|'.join(r'(?<![\w-])' + re.escape(t) + r'(?![\w-])'
                                  for t in terms), re.IGNORECASE)
    bare = [m.group(0) for m in re.finditer(r'\(inferred[^)]*\)', text,
                                            re.IGNORECASE)
            if not term_rx.search(m.group(0))]
    findings.append(('G1', not bare,
                     f'{len(bare)} inferred tag(s) without an anchored '
                     f'confidence term, e.g. {bare[0]}' if bare
                     else 'all inferred tags carry anchored confidence'))

    # R1: sentence length ceiling. Prose paragraphs and bullet lines both
    # count; rule 9's sentence rule has no bullet exemption.
    long_sents = []
    r1_sources = list(_prose_paragraphs(text)) + list(_bullet_lines(text))
    for start, para in r1_sources:
        for s in _sentences(para):
            if len(s.split()) > spec['max_sentence_words']:
                long_sents.append((start, len(s.split())))
    findings.append(('R1', not long_sents,
                     f'{len(long_sents)} sentence(s) over '
                     f'{spec["max_sentence_words"]} words '
                     f'(near lines {", ".join(str(l) for l, _ in long_sents[:5])})'
                     if long_sents else 'no over-length sentences'))

    # R2: prose paragraph length ceiling.
    long_paras = [(start, len(para)) for start, para in _prose_paragraphs(text)
                  if len(para) > spec['max_paragraph_chars']]
    findings.append(('R2', not long_paras,
                     f'{len(long_paras)} paragraph(s) over '
                     f'{spec["max_paragraph_chars"]} chars '
                     f'(lines {", ".join(str(l) for l, _ in long_paras[:5])})'
                     if long_paras else 'no over-length paragraphs'))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check', help='QC one self-assessment product file')
    check.add_argument('--file', required=True,
                       help='absolute path to the product (profile_<date>.md)')
    args = parser.parse_args()

    root, config = _config.load()
    spec = config['self_assessment']

    # Current protocol version, from the protocol file's own Version line.
    protocol_path = os.path.join(root,
                                 config['paths']['self_assessment_rules'],
                                 config['filenames']['assessment_protocol'])
    with open(protocol_path, 'r', encoding='utf-8') as f:
        version_match = re.search(r'\*\*Version:\*\*\s*v(\d+)', f.read())
    if version_match is None:
        sys.exit(f'ERROR: no "**Version:** v<N>" line found in {protocol_path}')
    protocol_version = version_match.group(1)

    with open(args.file, 'r', encoding='utf-8') as f:
        text = f.read()

    findings = []
    run_checks(text, spec, findings, protocol_version)

    failed = False
    for check_id, ok, detail in findings:
        print(f'{check_id}  {"PASS" if ok else "FAIL"}  {detail}')
        if not ok:
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
