#!/usr/bin/env python3
"""
role_intake_qc.py - deterministic QC for the role-intake skill's hand-off

Checks what role-intake leaves behind before the user reviews it and runs
role-research: the application folder, jd.md / comms.md, and the session log.
Every one of these is written by assemble.py from confirmed values, so a
failure here means an interrupted run or a hand edit, not a judgment call.
The research file and its checks belong to role_research_qc.py, which held
this file's name until research became its own skill (2026-11-16).

Checks:
  S1  Folder name has the form <slug>_<APP-NNN>_<YYYY-MM>.
  S2  jd.md exists and is not empty.
  S3  comms.md exists exactly when the session log names a comms source.
  S4  Session log: every metadata field filled and the start date well
      formed; only the research date, Role Level, Industry and the axis
      sections may still be pending.
  S5  The session log's APP-NNN matches the folder name.

Output: one `<ID>  PASS|FAIL  <detail>` line per check, then a RESULT line.
Exit 0 when all pass, 1 otherwise.

Author  : Jason Delosh
Created : 2026-11-16
Project : career
Usage   : python scripts/role_intake_qc.py check --folder <app_folder>
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
from role_research_qc import _PENDING_RE, _metadata_fields, _outside_classify


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Metadata fields role-intake fills; each must be present and non-empty.
FILLED_FIELDS = ['APP-NNN', 'Company', 'Role', 'Session Start Date', 'JD file', 'JD source']

# Fields filled later: present, but pending is allowed.
LATER_FIELDS = ['Research Completed Date', 'Role Level', 'Industry']


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check(folder, cfg):
    """Return [(id, ok, detail)] for one application folder."""
    fn = cfg['filenames']
    findings = []

    # S1: folder name.
    prefix = re.escape(cfg['naming']['app_id_prefix'])
    m = re.fullmatch(rf'.+?_({prefix}\d+)_\d{{4}}-\d{{2}}', os.path.basename(folder))
    folder_id = m.group(1) if m else None
    findings.append(('S1', bool(m), 'folder name well formed' if m else
                     f'folder name is not <slug>_APP-NNN_YYYY-MM: {os.path.basename(folder)}'))

    # S2: jd.md.
    jd_path = os.path.join(folder, fn['jd_file'])
    jd_ok = os.path.isfile(jd_path) and _util.read(jd_path).strip()
    findings.append(('S2', bool(jd_ok), 'jd.md present' if jd_ok else f'{fn["jd_file"]} missing or empty'))

    # S3 to S5 need the session log.
    log_path = os.path.join(folder, fn['session_log_file'])
    if not os.path.isfile(log_path):
        for check_id in ('S3', 'S4', 'S5'):
            findings.append((check_id, False, f'{fn["session_log_file"]} missing'))
        return findings
    log = _util.read(log_path)
    meta = _metadata_fields(log) or {}

    comms_named = bool(meta.get('Comms source'))
    comms_there = os.path.isfile(os.path.join(folder, fn['comms_file']))
    findings.append(('S3', comms_named == comms_there,
                     'comms file matches the session log' if comms_named == comms_there else
                     f'session log {"names" if comms_named else "names no"} comms source but '
                     f'{fn["comms_file"]} is {"missing" if comms_named else "present"}'))

    problems = [f'{f} missing or empty' for f in FILLED_FIELDS
                if not meta.get(f) or _PENDING_RE.search(meta[f])]
    problems += [f'{f} line missing' for f in LATER_FIELDS if f not in meta]
    start = meta.get('Session Start Date', '')
    if start and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', start):
        problems.append(f'Session Start Date malformed: {start!r}')
    outside = re.sub(r'(?m)^- Research Completed Date:.*$', '', _outside_classify(log))
    if _PENDING_RE.search(outside):
        problems.append('pending markers outside the fields filled later')
    findings.append(('S4', not problems, '; '.join(problems) or 'session log complete'))

    log_id = meta.get('APP-NNN', '')
    findings.append(('S5', log_id == folder_id,
                     'APP-NNN matches the folder' if log_id == folder_id else
                     f'session log APP-NNN {log_id!r} does not match the folder {folder_id!r}'))
    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Deterministic QC for role-intake's hand-off.")
    sub = parser.add_subparsers(dest='command', required=True)
    p_check = sub.add_parser('check', help='validate one application folder')
    p_check.add_argument('--folder', required=True, help='absolute path to the application folder')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    _, cfg = _config.load()
    findings = check(os.path.abspath(args.folder), cfg)
    failed = [f for f in findings if not f[1]]
    for check_id, ok, detail in findings:
        print(f"{check_id}  {'PASS' if ok else 'FAIL'}  {detail}")
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  {len(findings) - len(failed)}/{len(findings)} checks passed")
    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
