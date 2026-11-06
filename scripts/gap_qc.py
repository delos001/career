#!/usr/bin/env python3
"""
gap_qc.py - deterministic QC for the gap-analysis skill's artifacts

Owns the mechanical checks that the qc-gap-analysis judgment subagent must
not re-run: structure, field presence, taxonomy, ID existence, staging
anchors, coverage arithmetic, and cross-document mirroring. The judgment
agent keeps only what a script cannot verify (whether Notes and themes
actually carry valid reasoning).

Checks (IDs mirror the original qc-gap-analysis check numbering):
  G1  Section structure: H1 + the H2 sections present, in order.
  G2  Header completeness: APP-NNN / Date / Unmet Must-Haves / Recommendation
      fields present and non-empty.
  G3  Session log ## Gap Analysis section carries Run date, Gap analysis
      file, Recommendation, QC verdict fields.
  G4  Requirement coverage: every requirement in research.md's
      ## Critical Requirements appears exactly once as a CR-NNN sub-section.
  G5  Status taxonomy: every requirement Status is in the locked set.
  G6  Non-covered Notes present: status outside {covered, language-shift}
      carries a non-empty Notes value. (Whether the Notes content is
      adequate stays with the judgment agent.)
  G7  Staging anchors: every item this application staged that is still
      waiting names a CR-NNN that exists in the artifact. (Replaces the
      closure-ref linkage retired with the PU numbering, #70; a CV now cites
      such a fact as `GAP CR-NNN`, so the anchor is what has to hold.)
  G8  No fabricated IDs: every profile-prefixed ID (PR elements included) in the artifact exists
      in the profile documents (the prefix set is derived from the
      documents' own `ID:` lines, so new sections are covered without a
      code change); every CR-NNN is within the requirements range.
  G9  Session log mirroring: session log recommendation matches the artifact
      header recommendation.
  G10 Arithmetic: the Coverage Picture table and the unmet must-haves count
      match the statuses.
  G11 Recommendation label is exactly one of the three approved labels.
  G12 Gap themes: every language-shift, partial-match, interview-deferred, and
      unresolved requirement sits in exactly one theme; each theme has a known
      kind, real requirements, and a stated meaning.
  G13 The Recommendation states at least one condition it depends on.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT
line. Exit 0 when all pass, 1 otherwise, so the calling skill can gate on
the exit code per global rules.

Author  : Jason Delosh
Created : 2026-07-14
Project : career
Usage   : python scripts/gap_qc.py check --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import gap_assemble
import profile_update as pu
from inventory_model import pr


# ---------------------------------------------------------------------------
# Constants: locked vocabularies from the gap-analysis design
# ---------------------------------------------------------------------------

# The H2 sections of gap_analysis.md, in canonical order (must match
# templates/gap_analysis.md). The picture and the recommendation lead (GitHub #59).
SECTIONS = [
    'Coverage Picture', 'Gap Themes', 'Recommendation', 'Eligibility Flags',
    'Requirements', 'Language-Shift Cases', 'Partial-Match Cases',
    'Work-State Coverage', 'CV Notes',
]

# Required header fields (bold-label lines under the H1).
HEADER_FIELDS = ['APP-NNN', 'Date', 'Unmet Must-Haves', 'Recommendation']

# Required session log ## Gap Analysis fields (label prefixes of `- ` lines).
SESSION_LOG_FIELDS = ['Run date', 'Gap analysis file', 'Recommendation', 'QC verdict']

# Locked status taxonomy.
STATUSES = {'covered', 'closed', 'language-shift', 'partial-match',
            'interview-deferred', 'unresolved'}

# Statuses whose requirements must each be grouped into a gap theme. 'covered'
# and 'closed' may join a theme but need not.
THEMED_STATUSES = {'language-shift', 'partial-match', 'interview-deferred', 'unresolved'}

# Gap theme kinds: how far the outcome depends on who reads the application.
THEME_KINDS = {'reader-dependent', 'reader-independent', 'structural', 'strong-ground'}

# Approved recommendation labels.
RECOMMENDATION_LABELS = {'Proceed', 'Proceed with caution', 'Do not pursue'}

# Regex: an `ID: <PREFIX>-NNN` line in the profile documents. The citable
# prefix set is derived from these lines at check time (see check_ids), so a
# new inventory section with a new ID prefix is covered without a code change.
_ID_LINE_RE = re.compile(r'^ID:\s+([A-Z]+-\d+)\s*$', re.MULTILINE)

# Regex: a bold-label field line, e.g. `- **Status:** covered`.
_FIELD_LINE_RE = re.compile(r'^- \*\*(.+?):\*\*\s*(.*)$')


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _section_text(text, heading):
    """Return the body of an H2 section (to the next H2/H1), or None."""
    lines = text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f'## {heading}':
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith('## ') or (lines[j].startswith('# ') and not lines[j].startswith('## ')):
            end = j
            break
    return '\n'.join(lines[start:end])


def _parse_requirements(artifact_text):
    """Parse the ## Requirements section into {CR-NNN: {status, notes, order}}.

    Duplicate CR headings are recorded so G4 can flag them.
    """
    section = _section_text(artifact_text, 'Requirements')
    if section is None:
        return {}, []
    records = {}
    duplicates = []
    current = None
    for line in section.split('\n'):
        m = re.match(r'^### (CR-\d+) - ', line)
        if m:
            cr = m.group(1)
            if cr in records:
                duplicates.append(cr)
            current = {'status': '', 'notes': ''}
            records[cr] = current
            continue
        if current is None:
            continue
        m = _FIELD_LINE_RE.match(line)
        if m:
            label, value = m.group(1), m.group(2).strip()
            if label == 'Status':
                current['status'] = value
            elif label == 'Notes':
                current['notes'] = value
    return records, duplicates


def _parse_research_types(research_text):
    """Return the ordered requirement-type list from ## Critical Requirements.

    Two formats exist: current research files render a
    `| # | Text | Type | Source |` table; files from before the table
    convention render `- Text:` blocks with `Type:` continuation lines.
    CR-NNN derives from the 1-based row/block order in both.
    """
    section = _section_text(research_text, 'Critical Requirements')
    if section is None:
        return None
    types = []
    # Table format. Type is the second-to-last cell, anchored on the locked
    # type vocabulary so a pipe inside the Text cell cannot shift the parse.
    row_re = re.compile(
        r'^\|\s*\d+\s*\|.*\|\s*(must-have|preferred|contextual|duty-derived)\s*\|[^|]*\|\s*$')
    for line in section.split('\n'):
        m = row_re.match(line)
        if m:
            types.append(m.group(1))
    if types:
        return types
    # Bullet-block format (pre-table research files).
    for line in section.split('\n'):
        if re.match(r'^- Text:', line):
            types.append('')
            continue
        m = re.match(r'^\s+Type:\s*(\S+)', line)
        if m and types and types[-1] == '':
            types[-1] = m.group(1)
    return types


def _parse_staging_items(staging_text):
    """Return [{label, field: value}] for the items waiting in the queue.

    profile_update.py owns the staging layout; its parser is reused so the
    two scripts cannot disagree about where an item starts and ends.
    """
    if not staging_text:
        return []
    items = []
    for item in pu.parse_staging(staging_text):
        fields = {'label': item['label']}
        for line in item['body'].split('\n'):
            m = _FIELD_LINE_RE.match(line)
            if m:
                fields[m.group(1)] = m.group(2).strip()
        items.append(fields)
    return items


def _header_fields(artifact_text):
    """Return {label: value} for the bold `**Label:** value` header lines."""
    fields = {}
    for line in artifact_text.split('\n'):
        if line.startswith('## '):
            break
        m = re.match(r'^\*\*(.+?):\*\*\s*(.*)$', line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def _session_log_section(log_text):
    """Return {label: value} for `- Label: value` lines of ## Gap Analysis."""
    section = _section_text(log_text, 'Gap Analysis')
    if section is None:
        return None
    fields = {}
    for line in section.split('\n'):
        m = re.match(r'^- (.+?):\s*(.*)$', line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    return fields


def _parse_themes(artifact_text):
    """Return [{name, kind, requirements, meaning}] from the ## Gap Themes section."""
    themes = []
    for line in (_section_text(artifact_text, 'Gap Themes') or '').split('\n'):
        m = re.match(r'^### (.+) \(([^()]*)\)\s*$', line)
        if m:
            themes.append({'name': m.group(1), 'kind': m.group(2), 'requirements': [], 'meaning': ''})
            continue
        m = _FIELD_LINE_RE.match(line)
        if m and themes:
            if m.group(1) == 'Requirements':
                themes[-1]['requirements'] = re.findall(r'CR-\d+', m.group(2))
            elif m.group(1) == 'What it means':
                themes[-1]['meaning'] = m.group(2).strip()
    return themes


# ---------------------------------------------------------------------------
# Checks
# Each check appends (id, passed, detail) tuples to findings. A check that
# cannot run because an upstream parse failed reports FAIL with the cause
# rather than crashing, so one broken file yields readable output.
# ---------------------------------------------------------------------------

def check_structure(artifact_text, findings):
    """G1: H1 present; the H2 sections present in canonical order."""
    problems = []
    if not re.match(r'^# Gap Analysis: ', artifact_text):
        problems.append('missing `# Gap Analysis:` H1')
    h2s = [m.group(1) for m in re.finditer(r'^## (.+)$', artifact_text, re.MULTILINE)]
    if h2s != SECTIONS:
        missing = [s for s in SECTIONS if s not in h2s]
        extra = [s for s in h2s if s not in SECTIONS]
        if missing:
            problems.append(f"missing sections: {', '.join(missing)}")
        if extra:
            problems.append(f"unexpected sections: {', '.join(extra)}")
        if not missing and not extra:
            problems.append(f"section order is {', '.join(h2s)}")
    findings.append(('G1', not problems, '; '.join(problems) or 'section structure canonical'))


def check_header(header, findings):
    """G2: required header fields present and non-empty."""
    missing = [f for f in HEADER_FIELDS if not header.get(f)]
    findings.append(('G2', not missing,
                     f"empty or missing header fields: {', '.join(missing)}" if missing
                     else 'header fields complete'))


def check_session_log(log_fields, findings):
    """G3: session log ## Gap Analysis section carries the required fields."""
    if log_fields is None:
        findings.append(('G3', False, 'session log has no ## Gap Analysis section'))
        return
    missing = [f for f in SESSION_LOG_FIELDS if not log_fields.get(f)]
    findings.append(('G3', not missing,
                     f"session log section missing fields: {', '.join(missing)}" if missing
                     else 'session log section complete'))


def check_coverage(records, duplicates, req_types, findings):
    """G4: CR-001..CR-NNN each appear exactly once; none dropped or invented."""
    if req_types is None:
        findings.append(('G4', False, 'research.md has no ## Critical Requirements section'))
        return
    expected = {f'CR-{i:03d}' for i in range(1, len(req_types) + 1)}
    present = set(records)
    problems = []
    if expected - present:
        problems.append(f"dropped: {', '.join(sorted(expected - present))}")
    if present - expected:
        problems.append(f"not in research.md: {', '.join(sorted(present - expected))}")
    if duplicates:
        problems.append(f"duplicated: {', '.join(sorted(set(duplicates)))}")
    findings.append(('G4', not problems,
                     '; '.join(problems) if problems
                     else f'all {len(expected)} requirements present exactly once'))


def check_taxonomy(records, findings):
    """G5: every Status value is in the locked set."""
    bad = [f"{cr} ({rec['status'] or 'missing'})" for cr, rec in sorted(records.items())
           if rec['status'] not in STATUSES]
    findings.append(('G5', not bad,
                     f"off-taxonomy or missing status: {', '.join(bad)}" if bad
                     else 'all statuses in the locked set'))


def check_notes_presence(records, findings):
    """G6: non-covered/non-language-shift requirements carry non-empty Notes."""
    bad = [cr for cr, rec in sorted(records.items())
           if rec['status'] in STATUSES
           and rec['status'] not in ('covered', 'language-shift')
           and (not rec['notes'] or rec['notes'] == '_(none)_')]
    findings.append(('G6', not bad,
                     f"empty Notes on: {', '.join(bad)}" if bad
                     else 'all non-covered requirements carry Notes'))


def check_staging_anchors(records, staging_items, app_id, findings):
    """G7: every waiting item this application staged names a real CR-NNN.

    The anchor is how a CV citing `GAP CR-NNN` reaches the fact before it is in
    the inventory, so an item from this application pointing at a requirement
    the artifact does not carry is a broken link. Items from other
    applications, and items anchored 'n/a (...)', are out of scope.
    """
    problems = []
    for item in staging_items:
        if not app_id or not item.get('From', '').startswith(app_id):
            continue
        m = re.match(r'(CR-\d+)\b', item.get('Requirement', ''))
        if m and m.group(1) not in records:
            problems.append(f'"{item["label"]}" names {m.group(1)}, which is not '
                            f'in this gap analysis')
    findings.append(('G7', not problems,
                     '; '.join(problems) or 'staged items anchor to real requirements'))


def check_ids(artifact_text, profile_ids, req_count, findings):
    """G8: every cited ID exists in its source document."""
    problems = []
    if not profile_ids:
        findings.append(('G8', False,
                         'no IDs found in the profile documents (unreadable or empty)'))
        return
    # Citable prefixes are derived from the profile documents themselves, so a
    # new inventory section with a new ID prefix is covered without a code change.
    # The optional '.NN' reads a PR element ID whole, so a made-up element of a
    # real project is not waved through as its parent.
    prefixes = sorted({pid.split('-')[0] for pid in profile_ids})
    id_re = re.compile(r'\b(?:' + '|'.join(prefixes) + r')-\d+(?:\.\d+)?\b')
    fabricated = sorted({t for t in id_re.findall(artifact_text)
                         if t not in profile_ids})
    if fabricated:
        problems.append(f"IDs not in profile documents: {', '.join(fabricated)}")
    bad_cr = sorted({t for t in re.findall(r'\bCR-(\d+)\b', artifact_text)
                     if req_count is not None and int(t) > req_count})
    if bad_cr:
        problems.append(f"CR IDs beyond the requirements list: {', '.join('CR-' + t for t in bad_cr)}")
    findings.append(('G8', not problems, '; '.join(problems) or 'all cited IDs exist'))


def check_mirroring(header, log_fields, findings):
    """G9: session log recommendation matches the artifact header recommendation."""
    if log_fields is None:
        findings.append(('G9', False, 'session log has no ## Gap Analysis section'))
        return
    art, log = header.get('Recommendation', ''), log_fields.get('Recommendation', '')
    ok = bool(art) and art == log
    findings.append(('G9', ok,
                     f'recommendation diverges: artifact {art!r} vs session log {log!r}' if not ok
                     else 'recommendation mirrored'))


def check_coverage_math(artifact_text, header, records, req_types, findings):
    """G10: the coverage table and unmet must-haves recompute from the statuses."""
    # Compare key sets, not lengths: a dropped CR plus an invented one keeps
    # the count equal but would KeyError the lookup below.
    expected = None if req_types is None else {f'CR-{i:03d}' for i in range(1, len(req_types) + 1)}
    if expected is None or set(records) != expected:
        findings.append(('G10', False,
                         'cannot recompute: requirements list and artifact do not align'))
        return
    pairs = [(rtype, records[f'CR-{i:03d}']['status']) for i, rtype in enumerate(req_types, start=1)]
    problems = []
    # The same renderer wrote the table, so any difference means the statuses
    # and the picture no longer describe the same run.
    table = (_section_text(artifact_text, 'Coverage Picture') or '').strip()
    if table != gap_assemble.render_coverage_picture(pairs):
        problems.append('the Coverage Picture table does not match the requirement statuses')
    unmet = gap_assemble.count_unmet_must_haves(pairs)
    stated_unmet = header.get('Unmet Must-Haves', '')
    if not stated_unmet.isdigit() or int(stated_unmet) != unmet:
        problems.append(f"unmet must-haves is {stated_unmet!r}, statuses give {unmet}")
    findings.append(('G10', not problems, '; '.join(problems) or 'coverage arithmetic verified'))


def check_themes(artifact_text, records, findings):
    """G12: every soft requirement sits in exactly one well-formed theme."""
    themes = _parse_themes(artifact_text)
    placed = [cr for theme in themes for cr in theme['requirements']]
    problems = []
    for theme in themes:
        if theme['kind'] not in THEME_KINDS:
            problems.append(f"theme {theme['name']!r} has unknown kind {theme['kind']!r}")
        if not theme['requirements']:
            problems.append(f"theme {theme['name']!r} names no requirements")
        if not theme['meaning']:
            problems.append(f"theme {theme['name']!r} does not say what it means")
    missing = sorted(cr for cr, rec in records.items()
                     if rec['status'] in THEMED_STATUSES and cr not in placed)
    if missing:
        problems.append(f"not in any theme: {', '.join(missing)}")
    repeated = sorted({cr for cr in placed if placed.count(cr) > 1})
    if repeated:
        problems.append(f"in more than one theme: {', '.join(repeated)}")
    unknown = sorted(set(placed) - set(records))
    if unknown:
        problems.append(f"not in this gap analysis: {', '.join(unknown)}")
    findings.append(('G12', not problems, '; '.join(problems) or f'{len(themes)} gap themes complete'))


def check_depends_on(artifact_text, findings):
    """G13: the Recommendation section lists at least one condition."""
    section = _section_text(artifact_text, 'Recommendation') or ''
    ok = re.search(r'^\*\*Depends on:\*\*\s*\n- \S', section, re.MULTILINE) is not None
    findings.append(('G13', ok, 'recommendation states its conditions' if ok
                     else 'recommendation states no condition it depends on'))


def check_recommendation(header, findings):
    """G11: recommendation label is exactly one of the approved three."""
    label = header.get('Recommendation', '')
    ok = label in RECOMMENDATION_LABELS
    findings.append(('G11', ok,
                     f'label {label!r} not in the approved set' if not ok
                     else 'recommendation label approved'))


# ---------------------------------------------------------------------------
# Command: check
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Run all checks against one application folder; print report; return exit code."""
    fn = cfg['filenames']
    profile_dir = os.path.join(repo_root, cfg['paths']['profile'])
    app_folder = args.folder

    artifact_text = _read(os.path.join(app_folder, fn['gap_analysis_file']))
    if artifact_text is None:
        print(f"FATAL  {fn['gap_analysis_file']} not found in {app_folder}")
        return 1

    research_text = _read(os.path.join(app_folder, fn['research_file']))
    log_text = _read(os.path.join(app_folder, fn['session_log_file']))
    staging_text = _read(os.path.join(profile_dir, fn['staging_file'])) or ''
    inventory_text = _read(os.path.join(profile_dir, fn['inventory_file'])) or ''
    narratives_text = _read(os.path.join(profile_dir, fn['narratives_file'])) or ''

    profile_ids = set(_ID_LINE_RE.findall(inventory_text))
    profile_ids.update(pr.element_ids(inventory_text))
    profile_ids.update(_ID_LINE_RE.findall(narratives_text))
    staging_items = _parse_staging_items(staging_text)
    header = _header_fields(artifact_text)
    records, duplicates = _parse_requirements(artifact_text)
    req_types = _parse_research_types(research_text) if research_text is not None else None
    log_fields = _session_log_section(log_text) if log_text is not None else None

    findings = []
    check_structure(artifact_text, findings)
    check_header(header, findings)
    check_session_log(log_fields, findings)
    check_coverage(records, duplicates, req_types, findings)
    check_taxonomy(records, findings)
    check_notes_presence(records, findings)
    check_staging_anchors(records, staging_items, header.get('APP-NNN', ''), findings)
    check_ids(artifact_text, profile_ids,
              len(req_types) if req_types is not None else None, findings)
    check_mirroring(header, log_fields, findings)
    check_coverage_math(artifact_text, header, records, req_types, findings)
    check_recommendation(header, findings)
    check_themes(artifact_text, records, findings)
    check_depends_on(artifact_text, findings)

    failed = [f for f in findings if not f[1]]
    for check, ok, detail in findings:
        print(f"{check}  {'PASS' if ok else 'FAIL'}  {detail}")
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  "
          f"{len(findings) - len(failed)}/{len(findings)} checks passed")
    return 0 if not failed else 1


def _read(path):
    """Read a file, or return None if it does not exist."""
    if not os.path.isfile(path):
        return None
    return _util.read(path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Deterministic QC for gap-analysis artifacts.')
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
