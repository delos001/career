#!/usr/bin/env python3
"""
role_classify_qc.py - deterministic QC for the role-classify skill's writes

Owns the mechanical checks on what role-classify adds to an application: the
needs file (jd_needs.md), and the axis classification, Level and
Industry metadata, and Axis Gaps in the session log (mirrored into research.md).
The qc-role-classify judgment agent keeps what a script cannot verify (whether
the classification and the ranking are right).

These checks lived in role_intake_qc.py (as I3's axis half, I4, I5, I6, I8)
until role-classify was split out of role-intake; the parsing helpers they
share with role-intake's checks stay in role_intake_qc.py.

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
      Qualifications or Not ranked, with its research.md text unchanged; and
      every kind known and placed where its kinds set.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT line.
Exit 0 when all pass, 1 otherwise.

Author  : Jason Delosh
Created : 2026-11-09
Project : career
Usage   : python scripts/role_classify_qc.py check --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import requirement_kinds
from role_intake_qc import (_PENDING_RE, _QUOTE_RE, _clause_holding, _metadata_fields,
                            _read, _requirement_rows, _section_body)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# The five axes of the classification section.
AXES = ['Orientation', 'Industry', 'Specialty', 'Level', 'Work-state']

# Ranked Needs cell vocabularies. A Signals cell is a comma-separated list of
# these; repetition carries a count.
BASIS_VALUES = {'stated', 'derived'}
_SIGNAL_RE = re.compile(r'^(?:role-statement|repetition \d+|space)$')


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

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


def check_ranked_needs(research_text, needs_text, jd_text, kinds, findings):
    """C6: jd_needs.md places every requirement once, where its kind says.

    jd-needs-ranker labels each requirement with a kind from
    rules/jd-requirement-kinds.md, describes the job, and groups the rows into
    ranked needs; role_classify_assemble.py writes the result to jd_needs.md
    with each requirement's text copied from research.md. This check holds the
    mechanical half: the job description is present; ids N-01.. in sequence;
    allowed Basis and Signals values; each quote verbatim in the JD; every
    requirement in exactly one of a need, Qualifications or Not ranked, with
    its research.md text unchanged (a mismatch means the requirements were
    re-extracted after the ranking); and every kind known and placed where its
    kinds set. The Not ranked placement is what keeps boilerplate out of
    retrieval and gap analysis, so a misplaced row is a failure here, not a
    style note. Whether the kinds and the ranking are right is
    qc-role-classify's judgment and the user's confirmation.
    """
    req = {num: text for num, text, _ in _requirement_rows(research_text)}
    if needs_text is None:
        ok = not req
        findings.append(('C6', ok, 'no requirements, no needs file' if ok
                         else 'jd_needs.md not found (role-classify Phase 1 not run)'))
        return
    parsed = requirement_kinds.read_needs(needs_text)
    problems = []
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
            seen.setdefault(row[0], []).append((nid, requirement_kinds.NEED, row))
    if req and not parsed['needs']:
        problems.append('no needs')
    for place, heading in requirement_kinds.SECTION_FOR.items():
        if heading not in parsed['sections']:
            problems.append(f'no `## {heading}` section')
        for row in parsed[heading]:
            seen.setdefault(row[0], []).append((heading, place, row))
    for num, text in req.items():
        if num not in seen:
            problems.append(f'CR-{num:03d} is in no need, Qualifications or Not ranked')
            continue
        if len(seen[num]) > 1:
            problems.append(f"CR-{num:03d} appears in {', '.join(w for w, _, _ in seen[num])}")
            continue
        where, place, (_, listed_text, kind) = seen[num][0]
        if listed_text != text:
            problems.append(f'CR-{num:03d}: text differs from research.md (requirements '
                            f're-extracted; rerun Phase 1)')
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
    for num in sorted(set(seen) - set(req)):
        problems.append(f'row {num} is not a requirement row')
    findings.append(('C6', not problems, '; '.join(problems)
                     or f"{len(parsed['needs'])} needs; all {len(req)} requirements have a "
                        f"kind and land once where it places them"))



# ---------------------------------------------------------------------------
# Command: check
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Run all checks against one application folder; print report; return exit code."""
    fn = cfg['filenames']
    research_text = _read(os.path.join(args.folder, fn['research_file']))
    log_text = _read(os.path.join(args.folder, fn['session_log_file']))
    if research_text is None or log_text is None:
        missing = fn['research_file'] if research_text is None else fn['session_log_file']
        print(f'FATAL  {missing} not found in {args.folder}')
        return 1
    jd_text = _read(os.path.join(args.folder, fn['jd_file']))
    meta = _metadata_fields(log_text)

    findings = []
    check_complete(research_text, log_text, meta, findings)
    check_level_industry(log_text, meta, findings)
    check_gap_mirroring(research_text, log_text, findings)
    check_axis_line_form(log_text, findings)
    check_tier(log_text, leadership_tiers(repo_root, cfg), findings)
    check_ranked_needs(research_text, _read(requirement_kinds.needs_path(args.folder, cfg)),
                       jd_text, requirement_kinds.load_kinds(repo_root, cfg), findings)

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
    p_check = sub.add_parser('check', help='validate one application folder')
    p_check.add_argument('--folder', required=True,
                         help='absolute path to the application folder')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    if args.command == 'check':
        sys.exit(cmd_check(args, repo_root, cfg))


if __name__ == '__main__':
    main()
