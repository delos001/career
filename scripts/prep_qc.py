#!/usr/bin/env python3
"""
prep_qc.py - deterministic QC for the preparation-screen skill's artifacts

Validates the three files the skill writes or appends to, scoped strictly to
what the skill owns (other skills' sections of shared files are not checked):

  interview_prep.md   structure against templates/interview_prep.md (the
                      single structure authority; nothing is hardcoded here)
  research.md         only the prep-attributed ledger sections
  session_log.md      only the '## Interview: Recruiter Screen' section

Checks (P6-P8 and X1-X4 are the universal template rules shared with
prep_interview_qc via _prep_checks, so screen-stage and post-screen artifacts
are held to the same formatting and architecture):
  P1  frontmatter present; key set matches the template's key set exactly
  P2  every template heading present, in template order and at the
      template's depth (extras allowed)
  P3  heading depth never exceeds four (####)
  P4  no em dashes in the artifact
  P5  every frontmatter `sources` file exists (app folder or profile folder)
  P6  no bold connector tokens welding list items
  P7  every heading is in the allowed set (template headings + dynamic families)
  P8  no coaching brackets or citations inside a heading line
  X1  an APPENDIX region exists with at least one per-interview block
  X2  every Q-label referenced is defined in the Question Bank
  X3  each Appendix block carries only schema fields (Purpose/Interviewer/Emphasis)
  X4  no Appendix block heading carries a date or an event-status token
  R1  each prep-attributed research.md section has a dated 'Added' line, at
      least one source URL, and no em dashes
  S1  session log has '## Interview: Recruiter Screen' with the required field labels
      (read from templates/session_log.md's '## Interview section' block, the
      single authority), a bare YYYY-MM-DD 'Interview date:', and no em dashes
  S2  the Outcome field is non-empty

Usage
  python prep_qc.py check --folder <absolute-path-to-application-folder>

Exit code 0 when all checks pass, 1 otherwise. Findings print one per line as
'CHECK  PASS|FAIL  detail'.

Author    : Jason Delosh
Created   : 2026-06-11
Project   : career
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
# Markdown parsing helpers and the universal interview_prep.md formatting /
# architecture checks (P6-P8, X1-X4) live in _prep_checks, the single home
# shared with prep_interview_qc so both entry points enforce them identically.
from _prep_checks import (
    _read, _headings, _sections, _frontmatter_keys, _frontmatter_sources,
    check_connectors, check_headings, check_xrefs, check_appendix_fields,
    check_appendix_status)


# ---------------------------------------------------------------------------
# Checks: interview_prep.md against the template
# ---------------------------------------------------------------------------

def check_artifact(artifact_text, template_text, app_folder, profile_dir, findings):
    """Run P1-P5. Appends (check, ok, detail) tuples to findings."""

    # P1: frontmatter key parity with the template.
    art_keys = _frontmatter_keys(artifact_text)
    tpl_keys = _frontmatter_keys(template_text)
    if art_keys is None:
        findings.append(('P1', False, 'artifact has no frontmatter block'))
    else:
        missing = sorted(tpl_keys - art_keys)
        extra = sorted(art_keys - tpl_keys)
        if missing or extra:
            findings.append(('P1', False,
                             f'frontmatter keys differ from template; '
                             f'missing={missing} extra={extra}'))
        else:
            findings.append(('P1', True, 'frontmatter keys match template'))

    # P2: template headings present, in order, at the template's depth. Extras
    # are allowed; order is judged on the required subsequence only. Headings
    # compare as (depth, text) pairs so a required heading at the wrong level
    # is a miss, not a match.
    # Template headings carrying '<...>' placeholder tokens are patterns, not
    # required literals (e.g. the Appendix block heading); exclude them.
    tpl_heads = [(d, t) for d, t in _headings(template_text) if '<' not in t]
    art_heads = _headings(artifact_text)
    missing = ['#' * d + ' ' + t for d, t in tpl_heads if (d, t) not in art_heads]
    if missing:
        findings.append(('P2', False, f'missing required headings: {missing}'))
    else:
        # Walk the artifact headings; required ones must appear in template order.
        idx = 0
        for h in art_heads:
            if idx < len(tpl_heads) and h == tpl_heads[idx]:
                idx += 1
        order_ok = idx == len(tpl_heads)
        findings.append(('P2', order_ok,
                         'required headings present in template order' if order_ok
                         else 'required headings out of template order'))

    # P3: depth cap at four.
    too_deep = [t for d, t in _headings(artifact_text) if d > 4]
    findings.append(('P3', not too_deep,
                     'heading depth capped at ####' if not too_deep
                     else f'headings deeper than ####: {too_deep}'))

    # P4: no em dashes (product artifact).
    findings.append(('P4', '—' not in artifact_text,
                     'no em dashes' if '—' not in artifact_text
                     else 'em dash found in artifact'))

    # P5: frontmatter sources resolve to real files (app folder or profile).
    bad = []
    for src in _frontmatter_sources(artifact_text):
        if not (os.path.isfile(os.path.join(app_folder, src))
                or os.path.isfile(os.path.join(profile_dir, src))):
            bad.append(src)
    findings.append(('P5', not bad,
                     'all frontmatter sources exist' if not bad
                     else f'frontmatter sources not found: {bad}'))


# ---------------------------------------------------------------------------
# Checks: research.md prep-attributed ledger sections only
# ---------------------------------------------------------------------------

# A section belongs to this skill when its body carries the attribution line
# written by the prep ledger pattern, e.g. '**Added:** 2026-06-11 (interview prep...'.
_ADDED_RE = re.compile(r'\*\*Added:\*\*\s*(\d{4}-\d{2}-\d{2})\s*\(interview prep')
_URL_RE = re.compile(r'https?://\S+')


def check_research(research_text, findings):
    """Run R1 on the prep-attributed sections. Other sections are out of scope."""
    prep_sections = [(h, b) for h, b in _sections(research_text)
                     if '(interview prep' in b]
    if not prep_sections:
        findings.append(('R1', True, 'no prep-attributed sections (nothing to check)'))
        return
    bad = []
    for heading, body in prep_sections:
        if not _ADDED_RE.search(body):
            bad.append(f'{heading}: missing dated **Added:** attribution')
        if not _URL_RE.search(body):
            bad.append(f'{heading}: no source URL')
        if '—' in body:
            bad.append(f'{heading}: em dash found')
    findings.append(('R1', not bad,
                     f'{len(prep_sections)} prep ledger section(s) dated, sourced, '
                     f'em-dash-free' if not bad else '; '.join(bad)))


# ---------------------------------------------------------------------------
# Checks: session log 'Interview: Recruiter Screen' section only
# ---------------------------------------------------------------------------

# A bare ISO date is the only legal value of the 'Interview date:' field; the
# other scheduling facts each have their own field (templates/session_log.md).
_BARE_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def check_session_log(log_text, required_fields, findings):
    """Run S1-S2 on the Interview: Recruiter Screen section. Other sections out of scope.

    required_fields comes from templates/session_log.md's '## Interview section'
    block, the single authority for an interview round's field set.
    """
    # 'Interview date' and 'Outcome' get value-level validation below via
    # hardcoded labels. The field SET is template-driven; guard that these labels
    # still exist in it so a template rename fails loud here instead of silently
    # skipping the value check.
    for lbl in ('Interview date:', 'Outcome:'):
        if lbl not in required_fields:
            raise ValueError(
                f"session-log validator references '{lbl}' but the template's "
                f"interview field set no longer contains it; update this check.")
    section = next((b for h, b in _sections(log_text) if h == 'Interview: Recruiter Screen'),
                   None)
    if section is None:
        findings.append(('S1', False, "no '## Interview: Recruiter Screen' section"))
        findings.append(('S2', False, 'outcome not checkable (section missing)'))
        return
    missing = [f for f in required_fields if f not in section]
    problems = [f'missing fields: {missing}'] if missing else []
    if '—' in section:
        problems.append('em dash found in section')
    dm = re.search(r'^-\s+Interview date:\s*(.*)$', section, re.MULTILINE)
    if dm and not _BARE_DATE_RE.match(dm.group(1).strip()):
        problems.append('Interview date must be a bare YYYY-MM-DD (time / medium / '
                        f'interviewers have their own fields), got "{dm.group(1).strip()}"')
    findings.append(('S1', not problems,
                     'Interview: Recruiter Screen fields present, em-dash-free' if not problems
                     else '; '.join(problems)))
    m = re.search(r'Outcome:\s*(\S.*)', section)
    findings.append(('S2', bool(m),
                     f'outcome recorded: {m.group(1).strip()}' if m
                     else 'Outcome field empty'))


# ---------------------------------------------------------------------------
# Subcommand: check
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Validate one application folder's prep artifacts. Returns exit code."""
    fn = cfg['filenames']
    app_folder = os.path.abspath(args.folder)
    profile_dir = os.path.join(repo_root, cfg['paths']['profile'])
    template_path = os.path.join(repo_root, cfg['paths']['templates'],
                                 fn['interview_prep_template'])

    findings = []

    template_text = _read(template_path)
    if template_text is None:
        print(f'FATAL  template not found: {template_path}')
        return 1

    artifact_text = _read(os.path.join(app_folder, fn['interview_prep_file']))
    if artifact_text is None:
        findings.append(('P1', False,
                         f"{fn['interview_prep_file']} not found in {app_folder}"))
    else:
        check_artifact(artifact_text, template_text, app_folder, profile_dir,
                       findings)
        check_connectors(artifact_text, findings)
        check_headings(artifact_text, template_text, findings)
        check_xrefs(artifact_text, findings)
        check_appendix_fields(artifact_text, findings)
        check_appendix_status(artifact_text, findings)

    research_text = _read(os.path.join(app_folder, fn['research_file']))
    if research_text is None:
        findings.append(('R1', False,
                         f"{fn['research_file']} not found in {app_folder}"))
    else:
        check_research(research_text, findings)

    log_text = _read(os.path.join(app_folder, fn['session_log_file']))
    if log_text is None:
        findings.append(('S1', False,
                         f"{fn['session_log_file']} not found in {app_folder}"))
    else:
        # The interview-section field set is defined once, in the session-log
        # template; both prep QC scripts read it from there.
        log_tpl = _read(os.path.join(repo_root, cfg['paths']['templates'],
                                     fn['session_log_template']))
        if log_tpl is None:
            print('FATAL  session log template not found')
            return 1
        check_session_log(log_text, _util.interview_section_fields(log_tpl), findings)

    failed = [f for f in findings if not f[1]]
    for check, ok, detail in findings:
        print(f"{check}  {'PASS' if ok else 'FAIL'}  {detail}")
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  "
          f"{len(findings) - len(failed)}/{len(findings)} checks passed")
    return 0 if not failed else 1


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic QC for preparation-screen artifacts.")
    sub = parser.add_subparsers(dest='command', required=True)
    p_check = sub.add_parser('check', help='validate one application folder')
    p_check.add_argument('--folder', required=True,
                         help='absolute path to the application folder')
    args = parser.parse_args()

    repo_root, cfg = _config.load()
    if args.command == 'check':
        sys.exit(cmd_check(args, repo_root, cfg))


if __name__ == '__main__':
    main()
