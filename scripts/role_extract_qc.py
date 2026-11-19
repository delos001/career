#!/usr/bin/env python3
"""
role_extract_qc.py - deterministic QC for the role-extract skill's writes

Owns the mechanical checks on jd_needs.md, the file role-extract writes: the
extracted requirements and the ranked needs. The qc-role-extract judgment
agent keeps what a script cannot verify (whether the kinds and the ranking
are right).

Moved from role_classify_qc.py when role-extract was split out of
role-classify (2026-11-16): X1 was C7, X2 was C8, X3 was C6.

Two commands. 'requirements' runs X1 and X2 alone on scratch/jd_assemble.md,
right after extraction, so a bad extraction is caught before ranking is spent
on it. 'check' runs them all on jd_needs.md.

Checks:
  X1  jd_needs.md holds at least one requirement, numbered 1..N with no gaps
      or repeats, each with a Unit ID, a Line, text, and a Demand of required
      or preferred, and a Bar of exposure, working or blank; a row whose text
      carries an optional word is preferred.
  X2  Each row's Unit is a unit of jd.md (jd_sentences.units); the row's
      words appear in that unit in the same order (cut, never added or
      rearranged); no row sits wholly inside another from the same unit; and
      every modifier (config requirement_qualifiers) and year count (config
      requirement_year_count) in a unit survives on at least one row from it.
  X3  jd_needs.md: the job description is present and cites jd.md lines as
      L<n>; each Role statement key item ends with its line, and a need
      with the role-statement signal quotes from one of those lines; the
      lead-or-do line opens with its answer and what is led; every need Quote
      and row JD line opens with its quote's L<n>; ids N-01.. in rank order,
      Signals from the allowed set, each need's quote verbatim in jd.md; every
      requirement in exactly one of a need, Qualifications or Not ranked (none
      left under Requirements); and every kind known and placed where its
      kinds set.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT line.
Exit 0 when all pass, 1 otherwise.

Author  : Jason Delosh
Created : 2026-11-16
Project : career
Usage   : python scripts/role_extract_qc.py requirements --folder <app_folder>
          python scripts/role_extract_qc.py check --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import jd_bar
import jd_sentences
import jd_extraction_tables
from role_research_qc import _read


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Ranked Needs cell vocabularies. A Signals cell is a comma-separated list of
# these; repetition and space carry the counts role_extract_assemble.py writes.
_SIGNAL_RE = re.compile(r'^(?:role-statement|repetition \d+|space \d+)$')

# Regex: the job description's lead-or-do answer, then what is led (work or people).
_LEAD_ANSWER_RE = re.compile(r'^(?:leads|does|both(?:, mainly (?:leading|doing))?); what: \S')

# Regex: a double-quoted span in a Source or Quote (straight or curly).
_QUOTE_RE = re.compile(r'["“]([^"“”]+)["”]')

# Regex: where a JD clause ends (see _clause_holding).
_CLAUSE_END_RE = re.compile(r'[.;!?]\s')

# Regex: one word for the word-order check (see _word_out_of_order); hyphens
# and apostrophes stay inside a word, other punctuation separates words.
_WORD_RE = re.compile(r"[\w'\-]+")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_normalize = jd_extraction_tables.normalize


def _line_ref_problem(label, cell, jd_text, quote):
    """Return a problem string when `cell` does not open with L<n> for `quote`'s
    jd.md line, else None. Every JD reference is a jd.md line number."""
    expected = jd_extraction_tables.quote_line(jd_text, quote)
    m = re.match(r'L(\d+)\b', cell or '')
    if expected is not None and (m is None or int(m.group(1)) != expected):
        return f'{label}: JD line should open with L{expected}'
    return None


def _clause_holding(jd_text, quote):
    """Return the normalized JD clause holding `quote`, or None if not found.

    A clause runs between sentence ends and semicolons within one JD line, so
    in 'Bachelor's degree required; advanced degree preferred.' the 'preferred'
    never binds the Bachelor's row. A quote must sit on one line of the JD.
    """
    target = _normalize(quote)
    for raw_line in jd_text.split('\n'):
        line = _normalize(raw_line)
        pos = line.find(target)
        if pos < 0:
            continue
        start = max((m.end() for m in _CLAUSE_END_RE.finditer(line, 0, pos)), default=0)
        end_match = _CLAUSE_END_RE.search(line, pos + len(target))
        return line[start:end_match.start() + 1] if end_match else line[start:]
    return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_requirements_present(needs_text, optional_words, findings):
    """X1: the extracted requirements are on file, numbered, with Demand and Source.

    Row numbers are the CR-NNN ids every later skill cites, so a gap or a
    repeat would point a citation at the wrong requirement. A row whose own
    text carries an optional word (config requirement_optional_words) must be
    'preferred'; the reverse (a row under a preferred heading) is the
    extractor's judgment, since JD headings have no standard form.
    """
    if needs_text is None:
        findings.append(('X1', False, 'requirements file not found (requirements not extracted)'))
        return
    rows = jd_extraction_tables.all_rows(jd_extraction_tables.read_needs(needs_text))
    problems = []
    nums = sorted(row['num'] for row in rows)
    if not rows:
        problems.append('no requirement rows')
    elif nums != list(range(1, len(nums) + 1)):
        problems.append(f"row numbers are not 1..{len(nums)} with no gaps or repeats: {nums}")
    for row in rows:
        cr = f"CR-{row['num']:03d}"
        if not jd_extraction_tables.UNIT_ID_RE.match(row.get('unit') or ''):
            problems.append(f'{cr}: no Unit ID (re-extract: role-extract writes each row with its jd_sentences unit)')
        if not row['text']:
            problems.append(f'{cr}: no text')
        if not row['source']:
            problems.append(f'{cr}: no Line')
        if row['demand'] not in jd_extraction_tables.ALLOWED_DEMANDS:
            problems.append(f"{cr}: Demand {row['demand']!r} is not one of "
                            f"{', '.join(sorted(jd_extraction_tables.ALLOWED_DEMANDS))}")
        if row.get('unit') and (row.get('bar') or '') not in jd_bar.ALLOWED_BARS:
            problems.append(f"{cr}: Bar {row['bar']!r} is not exposure, working or blank")
        word = jd_extraction_tables.optional_word(row['text'] or '', optional_words)
        if word and row['demand'] == 'required':
            problems.append(f"{cr}: says '{word}', so its Demand is preferred, not required")
    findings.append(('X1', not problems, '; '.join(problems)
                     or f'{len(rows)} requirements, each with Unit ID, Line, text and Demand'))


def _word_outside_unit(unit_text, text):
    """Return the first word of `text` not in `unit_text` in the same order,
    or None when every word is. Punctuation is ignored."""
    unit_words = _WORD_RE.findall(_normalize(unit_text))
    pos = 0
    for word in _WORD_RE.findall(_normalize(text)):
        try:
            pos = unit_words.index(word, pos) + 1
        except ValueError:
            return word
    return None


def check_requirement_text(needs_text, jd_text, cfg, findings):
    """X2: each row's words come from its own unit, and the bar survives (GitHub #83).

    Each row names its jd_sentences unit, found here by running
    jd_sentences.units() on jd.md. The row's words must appear in that unit
    in the same order: cutting words passes, adding or rearranging them fails
    (six extractor runs on APP-028 and APP-029 cut non-adjacent words, 'Strong
    facilitation skills', which is allowed). Until 2026-11-18 the extractor
    gave each row a quote and the check found its clause from the quote; a
    split part is not one run of JD words, so the unit replaced the quote.

    The extractor once dropped 'familiarity with' from a must-have, and the
    stricter text reached the gap walk. Modifiers (config
    requirement_qualifiers) and year counts (config requirement_year_count)
    are held across the rows sharing a unit rather than on each row: in '10
    years in the industry, with at least 5 years in people management' each
    count belongs to one of two parts, and in 'understanding of data ... to be
    able to be effectively build AI solutions' (Otsuka APP-026) the modifier
    belongs only to the first half. Whether a modifier carries onto each part
    is a reading judgment, left to qc-role-extract; this check needs it to
    survive on some row.
    """
    if needs_text is None:
        findings.append(('X2', False, 'requirements file not found (requirements not extracted)'))
        return
    if jd_text is None:
        findings.append(('X2', False, 'jd.md not found, so requirement wording cannot be checked'))
        return
    units = {u['id']: u for u in jd_sentences.units(jd_text, cfg)}
    rows = jd_extraction_tables.all_rows(jd_extraction_tables.read_needs(needs_text))
    qualifiers, year_count = cfg['requirement_qualifiers'], cfg['requirement_year_count']
    problems = []
    texts_by_clause = {}
    for row in rows:
        num, text, unit = row['num'], row['text'], row.get('unit')
        if unit not in units:
            problems.append(f'CR-{num:03d}: Unit ID {unit!r} is not a unit of jd.md')
            continue
        clause = _normalize(units[unit]['text'])
        word = _word_outside_unit(clause, text)
        if word:
            problems.append(f"CR-{num:03d}: '{word}' is added or out of the JD's order; "
                            f"cut words only, never add or rearrange them")
        texts_by_clause.setdefault(clause, []).append((num, _normalize(text)))
    # Two rows from one unit where one row's text sits whole inside the
    # other's are the same requirement twice (Medtronic APP-024 rows 40 and 41,
    # with and without 'including AWS'; Acadia APP-025 rows 37 and 38, the second
    # repeating the first to add a preferred setting). Rows from different units may
    # overlap: 'Bachelor's degree' required and 'Bachelor's degree in X' preferred.
    for entries in texts_by_clause.values():
        for num, norm in entries:
            for other, other_norm in entries:
                if num != other and norm in other_norm:
                    problems.append(f'CR-{num:03d} is wholly inside CR-{other:03d}, from the same JD '
                                    f'sentence; give the extra words their own row, or write one row')
    # Each modifier or year count in a unit must survive on at least one row
    # from that unit. With one row, that row must keep it.
    patterns = list(qualifiers) + [year_count]
    for clause, entries in texts_by_clause.items():
        for pattern in patterns:
            for match in re.finditer(rf'\b(?:{pattern})\b', clause):
                word = rf'\b{re.escape(match.group(0))}\b'
                if not any(re.search(word, norm_text) for _, norm_text in entries):
                    ids = ', '.join(f'CR-{num:03d}' for num, _ in entries)
                    problems.append(f"{ids}: no row keeps '{match.group(0)}' from the JD clause: {clause[:80]}")
    findings.append(('X2', not problems, '; '.join(problems) or f'{len(rows)} requirement rows keep the JD\'s words, order and modifiers'))


def check_ranked_needs(needs_text, jd_text, kinds, findings, units=None):
    """X3: jd_needs.md places every requirement once, where its kind says.

    jd-needs-ranker labels each requirement with a kind from
    the KINDS section of rules/jd-processing.md, describes the job, and groups the rows into
    ranked needs; role_extract_assemble.py rewrites jd_needs.md with each
    requirement's text, Demand and Source carried over from the extracted rows.
    This check holds the mechanical half: the job description is present; ids
    N-01.. in sequence; allowed Signals values; each quote verbatim in
    the JD; every requirement in exactly one of a need, Qualifications or Not
    ranked, none left under Requirements (the ranker placed it nowhere); and
    every kind known and placed where its kinds set. The Not ranked placement is
    what keeps boilerplate out of retrieval and gap analysis, so a misplaced row
    is a failure here, not a style note. Whether the kinds and the ranking are
    right is qc-role-extract's judgment and the user's confirmation.
    """
    if needs_text is None:
        findings.append(('X3', False, 'jd_needs.md not found (requirements not extracted)'))
        return
    parsed = jd_extraction_tables.read_needs(needs_text)
    req = {row['num'] for row in jd_extraction_tables.all_rows(parsed)}
    problems = []
    for row in parsed[jd_extraction_tables.UNPLACED]:
        problems.append(f"CR-{row['num']:03d} is in no need, Qualifications or Not ranked")
    jd_lines = (jd_text or '').split('\n')
    # The role statement and outcomes: items a few words each, each citing its line.
    # Outcomes is optional (older files predate it, and 'none' is allowed).
    for field in ('Role statement', 'Outcomes'):
        for item in (i.strip() for i in parsed['job_items'].get(field, []) if i.strip()):
            if not re.search(r'\(L\d+(?:, L\d+)*\)$', item):
                problems.append(f'{field}: item {item[:40]!r} must end with its jd.md line, e.g. (L22)')
    if parsed['job_items'].get('Outcomes'):
        refs = [int(n) for n in re.findall(r'\bL(\d+)\b', parsed['job'].get('Outcomes') or '')]
        bad = [n for n in refs if not (1 <= n <= len(jd_lines) and jd_lines[n - 1].strip())]
        if bad:
            problems.append(f"The job: Outcomes cite no JD text on L{', L'.join(map(str, bad))}")
    statement_lines = {int(n) for n in re.findall(r'\bL(\d+)\b', parsed['job'].get('Role statement') or '')}
    for field in ('Role statement', 'Leads, does, or both'):
        value = parsed['job'].get(field)
        if not value:
            problems.append(f'The job: no "{field}" line')
            continue
        refs = [int(n) for n in re.findall(r'\bL(\d+)\b', value)]
        bad = [n for n in refs if not (1 <= n <= len(jd_lines) and jd_lines[n - 1].strip())]
        if not refs or bad:
            problems.append(f'The job: "{field}" must cite jd.md lines as L<n>'
                            + (f"; no JD text on L{', L'.join(map(str, bad))}" if bad else ''))
    # The lead-or-do line states its answer and what is led; it never argues it.
    lead = parsed['job'].get('Leads, does, or both') or ''
    if lead and not _LEAD_ANSWER_RE.match(lead):
        problems.append('The job: "Leads, does, or both" must open with leads, does, both, '
                        'both, mainly leading or both, mainly doing, then "; what:"')
    seen = {}
    for n, need in enumerate(parsed['needs'], start=1):
        nid = need['id']
        if nid != f'N-{n:02d}':
            problems.append(f'{nid}: expected N-{n:02d}; ids run in rank order with no gaps')
        if not need['label']:
            problems.append(f'{nid}: empty label')
        signals = need.get('Signals', '')
        bad = [s for s in (x.strip() for x in signals.split(',')) if not _SIGNAL_RE.match(s)]
        if not signals or bad:
            problems.append(f'{nid}: Signals {signals!r} outside role-statement, repetition N, space N')
        quotes = _QUOTE_RE.findall(need.get('Quote', ''))
        if len(quotes) != 1:
            problems.append(f'{nid}: Quote needs one quoted JD passage, found {len(quotes)}')
        elif jd_text is not None and _clause_holding(jd_text, quotes[0]) is None:
            problems.append(f'{nid}: quote not found in the JD: {quotes[0][:60]}')
        elif jd_text is not None:
            problems.append(_line_ref_problem(nid, need.get('Quote'), jd_text, quotes[0]))
        # The role-statement signal needs the quote on a line the role statement cites.
        if 'role-statement' in signals and len(quotes) == 1 and jd_text is not None \
                and jd_extraction_tables.quote_line(jd_text, quotes[0]) not in statement_lines:
            problems.append(f'{nid}: role-statement signal, but its quote is on no Role statement line')
        if not need['rows']:
            problems.append(f'{nid}: no requirements')
        for row in need['rows']:
            seen.setdefault(row['num'], []).append((nid, jd_extraction_tables.NEED, row))
    # Each row's JD line opens with its unit's line; a hand edit at the user's
    # review can break it. A row from a file written before 2026-11-18 has no
    # Unit, and its line is found from its quote (the text when it has none).
    if jd_text is not None:
        for row in jd_extraction_tables.all_rows(parsed):
            label = f"CR-{row['num']:03d}"
            if row.get('unit') and units is not None:
                expected = units[row['unit']]['line'] if row['unit'] in units else None
                m = re.match(r'L(\d+)\b', row['source'] or '')
                if expected is None:
                    problems.append(f"{label}: Unit ID {row['unit']} is not a unit of jd.md")
                elif m is None or int(m.group(1)) != expected:
                    problems.append(f'{label}: Line should be L{expected}')
                continue
            quotes = _QUOTE_RE.findall(row['source'] or '') or [row['text']]
            problems.append(_line_ref_problem(label, row['source'], jd_text, quotes[0]))
    problems = [p for p in problems if p]
    if req and not parsed['needs']:
        problems.append('no needs')
    for place, heading in jd_extraction_tables.SECTION_FOR.items():
        if heading not in parsed['sections']:
            problems.append(f'no `## {heading}` section')
        for row in parsed[heading]:
            seen.setdefault(row['num'], []).append((heading, place, row))
    for num in sorted(seen):
        if len(seen[num]) > 1:
            problems.append(f"CR-{num:03d} appears in {', '.join(w for w, _, _ in seen[num])}")
            continue
        where, place, row = seen[num][0]
        kind = row['kind']
        if not kind:
            problems.append(f'CR-{num:03d} has no Kind')
            continue
        names = jd_extraction_tables.parse_kind_cell(kind)
        unknown = [k for k in names if k not in kinds]
        if unknown:
            problems.append(f"CR-{num:03d}: unknown kind {', '.join(unknown)}")
        elif jd_extraction_tables.placement(names, kinds) != place:
            problems.append(f'CR-{num:03d} is in {where} but its kind places it in '
                            f'{jd_extraction_tables.placement(names, kinds)}')
    findings.append(('X3', not problems, '; '.join(problems)
                     or f"{len(parsed['needs'])} needs; all {len(req)} requirements have a "
                        f"kind and land once where it places them"))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _needs_and_jd(folder, cfg, scratch=False):
    """Return (requirements file text, jd.md text), each None when absent.

    scratch=True reads scratch/jd_assemble.md, for the Phase 3
    extraction check; otherwise jd_needs.md, for the full check.
    """
    fn = cfg['filenames']
    path = (os.path.join(folder, fn['scratch_subdir'], fn['jd_assemble_file']) if scratch
            else os.path.join(folder, fn['jd_needs_file']))
    return _read(path), _read(os.path.join(folder, fn['jd_file']))


def _requirement_checks(needs_text, jd_text, cfg, findings):
    """X1 and X2: the extraction checks."""
    check_requirements_present(needs_text, cfg['requirement_optional_words'], findings)
    check_requirement_text(needs_text, jd_text, cfg, findings)


def cmd_requirements(args, repo_root, cfg):
    """Run the extraction checks only (X1, X2) on jd_assemble.md; return exit code."""
    findings = []
    _requirement_checks(*_needs_and_jd(args.folder, cfg, scratch=True), cfg, findings)
    return _report(findings)


def cmd_check(args, repo_root, cfg):
    """Run all checks against one application folder; return exit code."""
    findings = []
    needs_text, jd_text = _needs_and_jd(args.folder, cfg)
    _requirement_checks(needs_text, jd_text, cfg, findings)
    units = {u['id']: u for u in jd_sentences.units(jd_text, cfg)} if jd_text is not None else None
    check_ranked_needs(needs_text, jd_text, jd_extraction_tables.load_kinds(repo_root, cfg), findings, units)
    return _report(findings)


def _report(findings):
    """Print one line per check and a RESULT line; return the exit code."""
    failed = [f for f in findings if not f[1]]
    for check, ok, detail in findings:
        print(f"{check}  {'PASS' if ok else 'FAIL'}  {detail}")
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  "
          f"{len(findings) - len(failed)}/{len(findings)} checks passed")
    return 0 if not failed else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Deterministic QC for role-extract writes.')
    sub = parser.add_subparsers(dest='command', required=True)
    commands = {'requirements': ('check the extracted requirements only', cmd_requirements),
                'check': ('validate one application folder', cmd_check)}
    for name, (help_text, _) in commands.items():
        p = sub.add_parser(name, help=help_text)
        p.add_argument('--folder', required=True,
                       help='absolute path to the application folder')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    sys.exit(commands[args.command][1](args, repo_root, cfg))


if __name__ == '__main__':
    main()
