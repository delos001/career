#!/usr/bin/env python3
"""
role_classify_qc.py - deterministic QC for the role-classify skill's writes

Owns the mechanical checks on what role-classify adds to an application: the
requirements and needs file (jd_needs.md), and the axis classification, Level
and Industry metadata, and Axis Gaps in the session log (mirrored into
research.md). The qc-role-classify judgment agent keeps what a script cannot
verify (whether the classification and the ranking are right).

C1 to C6 lived in role_intake_qc.py (as I3's axis half, I4, I5, I6, I8) until
role-classify was split out of role-intake; C7 and C8 (as I1's requirements
half and I7) until requirement extraction moved here too. The metadata parsing
helpers stay in role_intake_qc.py.

Two commands. 'requirements' runs C7 and C8 alone, right after extraction, so a
bad extraction is caught before ranking is spent on it. 'check' runs them all.

Checks:
  C1  Completeness: the session log's Role Level and Industry metadata are
      filled; Axis Classification carries all five axis lines; Axis Gaps is
      filled in both files. No pending markers in these sections.
  C2  The metadata Role Level and Industry values match the Axis
      Classification's Level and Industry values.
  C3  Axis gaps recorded in both: the set of axes flagged in the session log's
      Axis Gaps matches the set flagged in the research file's.
  C4  Axis lines match the axis-classifier's declared return format
      (`- <Axis>: <values> - <rationale>`, no bold, no bare label).
  C5  A leadership Level carries exactly one `- Tier:` line naming a tier from
      rules/levels/leadership.md's Tiers block; other levels carry none.
  C6  jd_needs.md: the job description is present; ids N-01.. in rank
      order, Basis stated|derived, Signals from the allowed set, each need's
      quote verbatim in jd.md; every requirement in exactly one of a need,
      Qualifications or Not ranked (none left under Requirements); and every
      kind known and placed where its kinds set.
  C7  jd_needs.md holds at least one requirement, numbered 1..N with no gaps
      or repeats, each with text, a Source, and a Type from the allowed four.
  C8  Each requirement's Source carries one verbatim quote found in jd.md, and
      every modifier (config requirement_qualifiers) and year count (config
      requirement_year_count) in the JD clause holding that quote survives on
      at least one row quoting that clause.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT line.
Exit 0 when all pass, 1 otherwise.

Author  : Jason Delosh
Created : 2026-11-09
Project : career
Usage   : python scripts/role_classify_qc.py requirements --folder <app_folder>
          python scripts/role_classify_qc.py check --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import requirement_kinds
from role_intake_qc import _PENDING_RE, _metadata_fields, _read, _section_body


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The five axes of the classification section.
AXES = ['Orientation', 'Industry', 'Specialty', 'Level', 'Work-state']

# Ranked Needs cell vocabularies. A Signals cell is a comma-separated list of
# these; repetition carries a count.
BASIS_VALUES = {'stated', 'derived'}
_SIGNAL_RE = re.compile(r'^(?:role-statement|repetition \d+|space)$')

# Regex: a double-quoted span in a Source or Quote (straight or curly).
_QUOTE_RE = re.compile(r'["“]([^"“”]+)["”]')

# Regex: where a JD clause ends (see _clause_holding).
_CLAUSE_END_RE = re.compile(r'[.;!?]\s')


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _normalize(text):
    """Lowercase, straighten quotes and dashes, drop bold, collapse whitespace."""
    for fancy, plain in (('’', "'"), ('‘', "'"), ('–', '-'), ('—', '-'), ('*', '')):
        text = text.replace(fancy, plain)
    return re.sub(r'\s+', ' ', text).strip().lower()


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

def _axis_values(log_text):
    """Return {axis: value part} from ## Axis Classification lines.

    Each line is `- <Axis>: <values> - <rationale>`; kebab-case values carry
    no spaced hyphen, so the first ' - ' isolates the value part.
    """
    body = _section_body(log_text, 'Axis Classification')
    if body is None:
        return None
    values = {}
    for line in body.split('\n'):
        # The spec form is plain (`- Orientation:`). Bold and un-bulleted forms
        # are classifier drift; `role_classify_assemble.py finalize` normalizes
        # them away on write, so they should not reach a new log. Parsing stays
        # tolerant so the other checks still work on a legacy log while check C4
        # reports the drift.
        m = re.match(
            r'^- (?:\*\*)?(Orientation|Industry|Specialty|Level|Work-state):(?:\*\*)?\s*(.+)$',
            line)
        if m:
            values[m.group(1)] = m.group(2).split(' - ')[0].strip()
    return values


def _gap_axes(text):
    """Return the set of axis names flagged in a file's ## Axis Gaps section.

    `- None` (or an empty body) means no gaps and yields the empty set.
    Returns None if the section is absent.
    """
    body = _section_body(text, 'Axis Gaps')
    if body is None:
        return None
    axes = set()
    for line in body.split('\n'):
        # Accept plain and bold labels (see _axis_values).
        m = re.match(r'^- (?:\*\*)?(Orientation|Industry|Specialty|Level|Work-state)\b', line)
        if m:
            axes.add(m.group(1))
    return axes


def leadership_tiers(repo_root, cfg):
    """Return the tier names from leadership.md's '### Tiers' block, in order.

    The block is the single source of tier names (GitHub #51); each tier is a
    bullet opening with its bold name, e.g. '- **function-lead** (...)'.
    """
    path = os.path.join(repo_root, cfg['paths']['rules'], 'levels', 'leadership.md')
    body = _section_body(_util.read(path), 'Tiers', depth=3) or ''
    return re.findall(r'(?m)^- \*\*([a-z][a-z-]*)\*\*', body)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_complete(research_text, log_text, meta, findings):
    """C1: every section role-classify writes is filled."""
    problems = []
    if meta is None:
        problems.append('session log has no ## Metadata section')
    else:
        for field in ('Role Level', 'Industry'):
            value = meta.get(field, '')
            if not value or _PENDING_RE.search(value):
                problems.append(f'metadata field {field!r} not filled')
    axes = _axis_values(log_text)
    body = _section_body(log_text, 'Axis Classification')
    if body is None:
        problems.append('session log missing `## Axis Classification`')
    elif _PENDING_RE.search(body):
        problems.append('session log `## Axis Classification` still pending')
    else:
        missing = [a for a in AXES if not (axes or {}).get(a)]
        if missing:
            problems.append(f"axis lines missing: {', '.join(missing)}")
    for name, text in (('session log', log_text), ('research file', research_text)):
        gaps = _section_body(text, 'Axis Gaps')
        if gaps is None:
            problems.append(f'{name} missing `## Axis Gaps`')
        elif _PENDING_RE.search(gaps):
            problems.append(f'{name} `## Axis Gaps` still pending')
    findings.append(('C1', not problems, '; '.join(problems) or 'classification sections filled'))


def check_level_industry(log_text, meta, findings):
    """C2: metadata Level and Industry equal the axis classification's values."""
    axes = _axis_values(log_text) or {}
    problems = []
    # Metadata Level/Industry are finalize-filled FROM the axis result; the
    # metadata value must appear in the axis line's value part (which may
    # carry primary/secondary annotations).
    for meta_field, axis in (('Role Level', 'Level'), ('Industry', 'Industry')):
        meta_val, axis_val = (meta or {}).get(meta_field, ''), axes.get(axis, '')
        if meta_val and axis_val and meta_val not in axis_val:
            problems.append(
                f'metadata {meta_field} {meta_val!r} not in axis classification {axis} {axis_val!r}')
    findings.append(('C2', not problems, '; '.join(problems) or 'metadata matches the classification'))


def check_gap_mirroring(research_text, log_text, findings):
    """C3: the axes flagged as gaps match between the two files."""
    log_gaps, research_gaps = _gap_axes(log_text), _gap_axes(research_text)
    if log_gaps is None or research_gaps is None:
        findings.append(('C3', False, 'an `## Axis Gaps` section is missing (see C1)'))
        return
    ok = log_gaps == research_gaps
    findings.append(('C3', ok,
                     f'gap axes diverge: session log {sorted(log_gaps)} vs research {sorted(research_gaps)}'
                     if not ok else 'axis gaps mirrored'))


def check_axis_line_form(log_text, findings):
    """C4: axis lines match the axis-classifier's declared return format.

    The classifier's return-format spec (`.claude/agents/axis-classifier.md`)
    emits `- <Axis>: <values> - <rationale>` with no bold markers, and
    `role_classify_assemble.py finalize` writes that output into the session
    log. So a bolded or un-bulleted axis line is subagent drift from its own
    spec, not a style choice. `_axis_values` deliberately tolerates the drifted
    forms so the other checks keep working while it is corrected; this check is
    what makes the drift visible instead of silently accommodated. Downstream
    readers (`staging_append.py`) match the spec form and nothing else.
    """
    body = _section_body(log_text, 'Axis Classification')
    if body is None:
        findings.append(('C4', False, 'no `## Axis Classification` section to check'))
        return
    conforming = re.compile(
        r'^- (?:Orientation|Industry|Specialty|Level|Work-state): \S')
    drifted = [line.strip() for line in body.split('\n')
               if re.search(r'\b(?:Orientation|Industry|Specialty|Level|'
                            r'Work-state):', line)
               and not conforming.match(line)]
    findings.append((
        'C4', not drifted,
        '; '.join(f'axis line does not match the classifier return format: '
                  f'{line[:60]}' for line in drifted)
        or 'axis lines match the classifier return format'))


def check_tier(log_text, tiers, findings):
    """C5: a leadership role records exactly one known tier; an IC role none.

    Research calibrates seniority within leadership (Associate Director vs
    VP); the tier line carries that calibration to the CV writer instead of
    flattening every leadership role into one voice.
    """
    body = _section_body(log_text, 'Axis Classification')
    if body is None:
        findings.append(('C5', False, 'no `## Axis Classification` section to check'))
        return
    level = (_axis_values(log_text) or {}).get('Level', '')
    tier_lines = re.findall(r'(?m)^- Tier:[ \t]*(.+)$', body)
    values = [re.split(r'[ \t]+-[ \t]+', t.strip(), maxsplit=1)[0] for t in tier_lines]
    if level == 'leadership':
        if len(values) != 1:
            ok, detail = False, f'leadership needs one `- Tier:` line, found {len(values)}'
        elif values[0] not in tiers:
            ok, detail = False, f"tier {values[0]!r} is not one of {', '.join(tiers)}"
        else:
            ok, detail = True, f'tier {values[0]}'
    else:
        ok = not values
        detail = 'no tier for a non-leadership level' if ok else f'level {level!r} must carry no tier'
    findings.append(('C5', ok, detail))


def check_ranked_needs(needs_text, jd_text, kinds, findings):
    """C6: jd_needs.md places every requirement once, where its kind says.

    jd-needs-ranker labels each requirement with a kind from
    rules/jd-requirement-kinds.md, describes the job, and groups the rows into
    ranked needs; role_classify_assemble.py rewrites jd_needs.md with each
    requirement's text, Type and Source carried over from the extracted rows.
    This check holds the mechanical half: the job description is present; ids
    N-01.. in sequence; allowed Basis and Signals values; each quote verbatim in
    the JD; every requirement in exactly one of a need, Qualifications or Not
    ranked, none left under Requirements (the ranker placed it nowhere); and
    every kind known and placed where its kinds set. The Not ranked placement is
    what keeps boilerplate out of retrieval and gap analysis, so a misplaced row
    is a failure here, not a style note. Whether the kinds and the ranking are
    right is qc-role-classify's judgment and the user's confirmation.
    """
    if needs_text is None:
        findings.append(('C6', False, 'jd_needs.md not found (requirements not extracted)'))
        return
    parsed = requirement_kinds.read_needs(needs_text)
    req = {row['num'] for row in requirement_kinds.all_rows(parsed)}
    problems = []
    for row in parsed[requirement_kinds.UNPLACED]:
        problems.append(f"CR-{row['num']:03d} is in no need, Qualifications or Not ranked")
    for field in ('Delivers or owns', 'Leads, does, or both'):
        if not parsed['job'].get(field):
            problems.append(f'The job: no "{field}" line')
    seen = {}
    for n, need in enumerate(parsed['needs'], start=1):
        nid = need['id']
        if nid != f'N-{n:02d}':
            problems.append(f'{nid}: expected N-{n:02d}; ids run in rank order with no gaps')
        if not need['label']:
            problems.append(f'{nid}: empty label')
        if need.get('Basis') not in BASIS_VALUES:
            problems.append(f"{nid}: Basis {need.get('Basis')!r} is not stated or derived")
        signals = need.get('Signals', '')
        bad = [s for s in (x.strip() for x in signals.split(',')) if not _SIGNAL_RE.match(s)]
        if not signals or bad:
            problems.append(f'{nid}: Signals {signals!r} outside role-statement, repetition N, space')
        quotes = _QUOTE_RE.findall(need.get('Quote', ''))
        if len(quotes) != 1:
            problems.append(f'{nid}: Quote needs one quoted JD passage, found {len(quotes)}')
        elif jd_text is not None and _clause_holding(jd_text, quotes[0]) is None:
            problems.append(f'{nid}: quote not found in the JD: {quotes[0][:60]}')
        if not need['rows']:
            problems.append(f'{nid}: no requirements')
        for row in need['rows']:
            seen.setdefault(row['num'], []).append((nid, requirement_kinds.NEED, row))
    if req and not parsed['needs']:
        problems.append('no needs')
    for place, heading in requirement_kinds.SECTION_FOR.items():
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
        names = requirement_kinds.parse_kind_cell(kind)
        unknown = [k for k in names if k not in kinds]
        if unknown:
            problems.append(f"CR-{num:03d}: unknown kind {', '.join(unknown)}")
        elif requirement_kinds.placement(names, kinds) != place:
            problems.append(f'CR-{num:03d} is in {where} but its kind places it in '
                            f'{requirement_kinds.placement(names, kinds)}')
    findings.append(('C6', not problems, '; '.join(problems)
                     or f"{len(parsed['needs'])} needs; all {len(req)} requirements have a "
                        f"kind and land once where it places them"))


def check_requirements_present(needs_text, findings):
    """C7: the extracted requirements are on file, numbered, with Type and Source.

    Row numbers are the CR-NNN ids every later skill cites, so a gap or a
    repeat would point a citation at the wrong requirement.
    """
    if needs_text is None:
        findings.append(('C7', False, 'jd_needs.md not found (requirements not extracted)'))
        return
    rows = requirement_kinds.all_rows(requirement_kinds.read_needs(needs_text))
    problems = []
    nums = sorted(row['num'] for row in rows)
    if not rows:
        problems.append('no requirement rows')
    elif nums != list(range(1, len(nums) + 1)):
        problems.append(f"row numbers are not 1..{len(nums)} with no gaps or repeats: {nums}")
    for row in rows:
        cr = f"CR-{row['num']:03d}"
        if not row['text']:
            problems.append(f'{cr}: no text')
        if not row['source']:
            problems.append(f'{cr}: no Source')
        if row['type'] not in requirement_kinds.ALLOWED_TYPES:
            problems.append(f"{cr}: Type {row['type']!r} is not one of "
                            f"{', '.join(sorted(requirement_kinds.ALLOWED_TYPES))}")
    findings.append(('C7', not problems, '; '.join(problems)
                     or f'{len(rows)} requirements, each with text, Type and Source'))


def check_requirement_text(needs_text, jd_text, qualifiers, year_count, findings):
    """C8: requirement text keeps the modifiers that set the JD's bar (GitHub #83).

    The extractor once dropped 'familiarity with' from a must-have, and the
    stricter text reached the gap walk. Modifiers are read from the whole JD
    clause rather than the quote alone: the extractor chooses the quote, so a
    narrow one would otherwise step around the check. A row that keeps every
    modifier but rewords the rest passes; this check guards the bar, not style.

    Modifiers and year counts are held across the rows sharing a clause rather
    than on each row: in '10 years in the industry, with at least 5 years in
    people management' each count belongs to one of two requirements, and in
    'understanding of data ... to be able to be effectively build AI solutions'
    (Otsuka APP-026) the modifier belongs only to the first half. Whether a
    modifier carries onto each part of a split clause is a reading judgment,
    left to qc-role-classify; this check needs it to survive on some row.
    """
    if needs_text is None:
        findings.append(('C8', False, 'jd_needs.md not found (requirements not extracted)'))
        return
    if jd_text is None:
        findings.append(('C8', False, 'jd.md not found, so requirement quotes cannot be checked'))
        return
    rows = requirement_kinds.all_rows(requirement_kinds.read_needs(needs_text))
    problems = []
    texts_by_clause = {}
    for row in rows:
        num, text = row['num'], row['text']
        quotes = _QUOTE_RE.findall(row['source'] or '')
        if len(quotes) != 1:
            problems.append(f'CR-{num:03d}: Source needs one quote, found {len(quotes)}')
            continue
        clause = _clause_holding(jd_text, quotes[0])
        if clause is None:
            problems.append(f'CR-{num:03d}: quote not found in the JD: {quotes[0][:60]}')
            continue
        texts_by_clause.setdefault(clause, []).append((num, _normalize(text)))
    # Each modifier or year count in a clause must survive on at least one row
    # quoting that clause. With one row, that row must keep it.
    patterns = list(qualifiers) + [year_count]
    for clause, entries in texts_by_clause.items():
        for pattern in patterns:
            for match in re.finditer(rf'\b(?:{pattern})\b', clause):
                word = rf'\b{re.escape(match.group(0))}\b'
                if not any(re.search(word, norm_text) for _, norm_text in entries):
                    ids = ', '.join(f'CR-{num:03d}' for num, _ in entries)
                    problems.append(f"{ids}: no row keeps '{match.group(0)}' from the JD clause: {clause[:80]}")
    findings.append(('C8', not problems, '; '.join(problems) or f'{len(rows)} requirement rows keep their JD modifiers'))



# ---------------------------------------------------------------------------
# Command: check
# ---------------------------------------------------------------------------

def _needs_and_jd(folder, cfg):
    """Return (jd_needs.md text, jd.md text), each None when absent."""
    return (_read(requirement_kinds.needs_path(folder, cfg)),
            _read(os.path.join(folder, cfg['filenames']['jd_file'])))


def _requirement_checks(needs_text, jd_text, cfg, findings):
    """C7 and C8: the extraction checks."""
    check_requirements_present(needs_text, findings)
    check_requirement_text(needs_text, jd_text, cfg['requirement_qualifiers'],
                           cfg['requirement_year_count'], findings)


def cmd_requirements(args, repo_root, cfg):
    """Run the extraction checks only (C7, C8); return exit code."""
    findings = []
    _requirement_checks(*_needs_and_jd(args.folder, cfg), cfg, findings)
    return _report(findings)


def cmd_check(args, repo_root, cfg):
    """Run all checks against one application folder; print report; return exit code."""
    fn = cfg['filenames']
    research_text = _read(os.path.join(args.folder, fn['research_file']))
    log_text = _read(os.path.join(args.folder, fn['session_log_file']))
    if research_text is None or log_text is None:
        missing = fn['research_file'] if research_text is None else fn['session_log_file']
        print(f'FATAL  {missing} not found in {args.folder}')
        return 1
    meta = _metadata_fields(log_text)

    findings = []
    check_complete(research_text, log_text, meta, findings)
    check_level_industry(log_text, meta, findings)
    check_gap_mirroring(research_text, log_text, findings)
    check_axis_line_form(log_text, findings)
    check_tier(log_text, leadership_tiers(repo_root, cfg), findings)
    needs_text, jd_text = _needs_and_jd(args.folder, cfg)
    check_ranked_needs(needs_text, jd_text, requirement_kinds.load_kinds(repo_root, cfg), findings)
    _requirement_checks(needs_text, jd_text, cfg, findings)
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
    parser = argparse.ArgumentParser(description='Deterministic QC for role-classify writes.')
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
