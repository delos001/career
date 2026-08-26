#!/usr/bin/env python3
"""
gap_qc.py - deterministic QC for the gap-analysis skill's artifacts

Owns the mechanical checks that the qc-gap-analysis judgment subagent must
not re-run: structure, field presence, taxonomy, ID existence, closure
linkage, fit-score math, and cross-document mirroring. The judgment agent
keeps only what a script cannot verify (whether Notes content actually
names valid reasoning).

Checks (IDs mirror the original qc-gap-analysis check numbering):
  G1  Section structure: H1 + the seven H2 sections present, in order.
  G2  Header completeness: APP-NNN / Date / Fit Score / Unmet Must-Haves /
      Recommendation fields present and non-empty.
  G3  Session log ## Gap Analysis section carries Run date, Gap analysis
      file, Fit score, QC verdict fields.
  G4  Requirement coverage: every requirement in research.md's
      ## Critical Requirements appears exactly once as a CR-NNN sub-section.
  G5  Status taxonomy: every requirement Status is in the locked set.
  G6  Non-covered Notes present: status outside {covered, language-shift}
      carries a non-empty Notes value. (Whether the Notes content is
      adequate stays with the judgment agent.)
  G7  Closure linkage: every `Closure ref: PU-NNN` still in the staging queue
      carries all required fields; every --appended-pu ID is referenced from
      the artifact. (Closed-without-ref is legitimate for eligibility
      attestations, so ref presence anchors on --appended-pu. A ref to a
      capture already promoted out of the queue is normal and is skipped.)
  G8  No fabricated IDs: every profile-prefixed ID in the artifact exists
      in the profile documents (the prefix set is derived from the
      documents' own `ID:` lines, so new sections are covered without a
      code change); every CR-NNN is within the requirements range. PU-NNN
      references are not checked: the staging file is a queue and a promoted
      capture is no longer in it.
  G9  Session log mirroring: session log fit score matches the artifact
      header fit score.
  G10 Math: header fit score equals the type-weighted formula result and
      the unmet must-haves count matches the statuses.
  G11 Recommendation label is exactly one of the three approved labels.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT
line. Exit 0 when all pass, 1 otherwise, so the calling skill can gate on
the exit code per global rules.

Author  : Jason Delosh
Created : 2026-07-14
Project : career
Usage   : python scripts/gap_qc.py check --folder <app_folder> [--appended-pu PU-NNN[,PU-NNN]]
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Constants: locked vocabularies from the gap-analysis design
# ---------------------------------------------------------------------------

# The seven H2 sections of gap_analysis.md, in canonical order.
SECTIONS = [
    'Eligibility Flags', 'Requirements', 'Language-Shift Cases',
    'Partial-Match Cases', 'De-emphasize', 'CV Notes', 'Recommendation',
]

# Required header fields (bold-label lines under the H1).
HEADER_FIELDS = ['APP-NNN', 'Date', 'Fit Score', 'Unmet Must-Haves', 'Recommendation']

# Required session log ## Gap Analysis fields (label prefixes of `- ` lines).
SESSION_LOG_FIELDS = ['Run date', 'Gap analysis file', 'Fit score', 'QC verdict']

# Locked status taxonomy and its scoring credits.
STATUS_CREDIT = {
    'covered': 1.0, 'closed': 1.0, 'language-shift': 1.0,
    'partial-match': 0.5, 'interview-deferred': 0.0, 'unresolved': 0.0,
}

# Requirement-type weights for the fit-score formula.
TYPE_WEIGHT = {'must-have': 3, 'preferred': 2, 'contextual': 1, 'duty-derived': 1}

# Statuses that count a must-have as unmet.
UNMET_STATUSES = {'interview-deferred', 'unresolved'}

# Approved recommendation labels.
RECOMMENDATION_LABELS = {'Proceed', 'Proceed with caution', 'Do not pursue'}

# Required fields of a staging PU entry.
PU_FIELDS = ['Captured', 'From', 'Requirement', 'Role context', 'Content']

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


def _parse_staging_entries(staging_text):
    """Return {PU-NNN: {field: value}} from the staging file."""
    entries = {}
    current = None
    for line in staging_text.split('\n'):
        m = re.match(r'^### (PU-\d+) - ', line)
        if m:
            current = {}
            entries[m.group(1)] = current
            continue
        if current is None:
            continue
        m = _FIELD_LINE_RE.match(line)
        if m:
            current[m.group(1)] = m.group(2).strip()
    return entries


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


def _parse_pct(value):
    """Extract the first `NN.N%` in value as a float, or None if absent.

    Search rather than full-match: session log fit-score lines may carry a
    suffix (e.g. `91.7% (Recommendation: ...)`), and the mirroring check
    compares the number only.
    """
    m = re.search(r'(\d+(?:\.\d+)?)\s*%', value)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Checks
# Each check appends (id, passed, detail) tuples to findings. A check that
# cannot run because an upstream parse failed reports FAIL with the cause
# rather than crashing, so one broken file yields readable output.
# ---------------------------------------------------------------------------

def check_structure(artifact_text, findings):
    """G1: H1 present; the seven H2 sections present in canonical order."""
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
           if rec['status'] not in STATUS_CREDIT]
    findings.append(('G5', not bad,
                     f"off-taxonomy or missing status: {', '.join(bad)}" if bad
                     else 'all statuses in the locked set'))


def check_notes_presence(records, findings):
    """G6: non-covered/non-language-shift requirements carry non-empty Notes."""
    bad = [cr for cr, rec in sorted(records.items())
           if rec['status'] in STATUS_CREDIT
           and rec['status'] not in ('covered', 'language-shift')
           and (not rec['notes'] or rec['notes'] == '_(none)_')]
    findings.append(('G6', not bad,
                     f"empty Notes on: {', '.join(bad)}" if bad
                     else 'all non-covered requirements carry Notes'))


def check_closure_linkage(records, staging_entries, appended_pu, artifact_text, findings):
    """G7: every Closure ref resolves to a complete staging entry; every
    appended PU is referenced from the artifact.

    A `closed` requirement without a Closure ref is legitimate (eligibility
    attestations close via user confirmation with nothing to stage), so the
    ref-presence direction is anchored on --appended-pu: closures that DID
    stage an entry are caught by the appended-but-unreferenced check.
    """
    problems = []
    for cr, rec in sorted(records.items()):
        m = re.search(r'Closure ref:\s*(PU-\d+)', rec['notes'])
        if not m:
            continue
        pu = m.group(1)
        entry = staging_entries.get(pu)
        if entry is None:
            # Absent means promoted: the staging file is a queue holding only
            # captures still waiting, and profile-update removes each one when
            # its content reaches the inventory. A ref to a cleared capture is
            # the expected steady state, and there is nothing left to check it
            # against. Only a capture still in the queue can be checked here.
            continue
        missing = [f for f in PU_FIELDS if not entry.get(f)]
        if missing:
            problems.append(f"{pu} missing fields: {', '.join(missing)}")
    for pu in appended_pu:
        if pu not in artifact_text:
            problems.append(f'{pu} appended this run but not referenced from the artifact')
    findings.append(('G7', not problems, '; '.join(problems) or 'closure linkage intact'))


def check_ids(artifact_text, profile_ids, req_count, staging_entries, findings):
    """G8: every cited ID exists in its source document."""
    problems = []
    if not profile_ids:
        findings.append(('G8', False,
                         'no IDs found in the profile documents (unreadable or empty)'))
        return
    # Citable prefixes are derived from the profile documents themselves, so a
    # new inventory section with a new ID prefix is covered without a code change.
    prefixes = sorted({pid.split('-')[0] for pid in profile_ids})
    id_re = re.compile(r'\b(?:' + '|'.join(prefixes) + r')-\d+\b')
    fabricated = sorted({t for t in id_re.findall(artifact_text)
                         if t not in profile_ids})
    if fabricated:
        problems.append(f"IDs not in profile documents: {', '.join(fabricated)}")
    bad_cr = sorted({t for t in re.findall(r'\bCR-(\d+)\b', artifact_text)
                     if req_count is not None and int(t) > req_count})
    if bad_cr:
        problems.append(f"CR IDs beyond the requirements list: {', '.join('CR-' + t for t in bad_cr)}")
    # PU IDs are deliberately NOT checked against the staging file. That file is
    # a queue: profile-update removes each capture once its content is in the
    # inventory, so an artifact citing a promoted capture would name an ID the
    # file no longer holds. Absence cannot be told apart from fabrication here,
    # and failing every promoted reference is the worse error of the two.
    findings.append(('G8', not problems, '; '.join(problems) or 'all cited IDs exist'))


def check_mirroring(header, log_fields, findings):
    """G9: session log fit score matches the artifact header fit score."""
    if log_fields is None:
        findings.append(('G9', False, 'session log has no ## Gap Analysis section'))
        return
    art, log = header.get('Fit Score', ''), log_fields.get('Fit score', '')
    ok = _parse_pct(art) is not None and _parse_pct(art) == _parse_pct(log)
    findings.append(('G9', ok,
                     f'fit score diverges: artifact {art!r} vs session log {log!r}' if not ok
                     else 'fit score mirrored'))


def check_math(header, records, req_types, findings):
    """G10: fit score and unmet must-haves recompute from statuses and types."""
    # Compare key sets, not lengths: a dropped CR plus an invented one keeps
    # the count equal but would KeyError the recompute loop below.
    expected = None if req_types is None else {f'CR-{i:03d}' for i in range(1, len(req_types) + 1)}
    if expected is None or set(records) != expected:
        findings.append(('G10', False,
                         'cannot recompute: requirements list and artifact do not align'))
        return
    unknown_types = sorted({t for t in req_types if t not in TYPE_WEIGHT})
    off_taxonomy = any(rec['status'] not in STATUS_CREDIT for rec in records.values())
    if unknown_types or off_taxonomy:
        findings.append(('G10', False,
                         f"cannot recompute: unknown types {unknown_types}" if unknown_types
                         else 'cannot recompute: off-taxonomy status present (see G5)'))
        return
    total = weighted = 0.0
    unmet = 0
    for i, rtype in enumerate(req_types, start=1):
        rec = records[f'CR-{i:03d}']
        weight = TYPE_WEIGHT[rtype]
        total += weight
        weighted += weight * STATUS_CREDIT[rec['status']]
        if rtype == 'must-have' and rec['status'] in UNMET_STATUSES:
            unmet += 1
    expected_pct = round(100.0 * weighted / total, 1)
    problems = []
    stated_pct = _parse_pct(header.get('Fit Score', ''))
    # One-decimal rounding tolerance on the stated percentage.
    if stated_pct is None or abs(stated_pct - expected_pct) > 0.05:
        problems.append(f"fit score is {header.get('Fit Score')!r}, formula gives {expected_pct}%")
    stated_unmet = header.get('Unmet Must-Haves', '')
    if not stated_unmet.isdigit() or int(stated_unmet) != unmet:
        problems.append(f"unmet must-haves is {stated_unmet!r}, statuses give {unmet}")
    findings.append(('G10', not problems, '; '.join(problems) or 'fit math verified'))


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
    profile_ids.update(_ID_LINE_RE.findall(narratives_text))
    staging_entries = _parse_staging_entries(staging_text)
    header = _header_fields(artifact_text)
    records, duplicates = _parse_requirements(artifact_text)
    req_types = _parse_research_types(research_text) if research_text is not None else None
    log_fields = _session_log_section(log_text) if log_text is not None else None
    appended_pu = [p.strip() for chunk in (args.appended_pu or [])
                   for p in chunk.split(',') if p.strip()]

    findings = []
    check_structure(artifact_text, findings)
    check_header(header, findings)
    check_session_log(log_fields, findings)
    check_coverage(records, duplicates, req_types, findings)
    check_taxonomy(records, findings)
    check_notes_presence(records, findings)
    check_closure_linkage(records, staging_entries, appended_pu, artifact_text, findings)
    check_ids(artifact_text, profile_ids,
              len(req_types) if req_types is not None else None,
              staging_entries, findings)
    check_mirroring(header, log_fields, findings)
    check_math(header, records, req_types, findings)
    check_recommendation(header, findings)

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
    p_check.add_argument('--appended-pu', action='append', default=[],
                         help='PU-NNN appended this run (repeatable or comma-separated); '
                              'each must be referenced from the artifact')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    repo_root, cfg = _config.load()
    if args.command == 'check':
        sys.exit(cmd_check(args, repo_root, cfg))


if __name__ == '__main__':
    main()
