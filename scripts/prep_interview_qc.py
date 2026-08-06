#!/usr/bin/env python3
"""
prep_interview_qc.py - deterministic QC for the preparation-interview skill

Validates the cumulative interview_prep.md (main body + per-interview Appendix)
plus the prep-attributed research ledger and the post-screen session-log
sections. Scoped to what this skill owns; the recruiter-screen '## Interview:
Recruiter Screen' section belongs to preparation-screen (prep_qc.py) and is not
checked here.

Structure is judged against the preparation-interview template (the skill-local
structure authority). Template headings that carry placeholder tokens (angle
brackets, e.g. '## <Audience> - <Interviewer(s)>') are patterns, not required
literals, and are excluded from the required-heading set.

Checks (FAIL blocks the build; WARN is advisory and leaves the exit code alone)
  P1  frontmatter present; key set matches the template's key set exactly
  P2  every required template heading present, in template order, at the
      template's depth (extras allowed). Required = template headings carrying
      neither a '<placeholder>' token nor an '{optional}' tag
  P3  heading depth never exceeds four (####)
  P4  no em dashes in the artifact
  P5  every frontmatter `sources` file exists (app folder or profile folder)
  P6  no bold connector tokens (**plus** / **and** / **+** / **&**) welding
      list items; use bullets
  P7  every heading is in the allowed set: every template heading (required and
      '{optional}' alike) plus the three dynamic families (Appendix per-interview
      '##' blocks, one '###' per Anticipated Question, one '#### Story ...' per
      Proof-points story). An invented sub-heading fails here; use the template's
      vocabulary or make it a bullet
  P8  no coaching brackets or citations inside a heading line
  X1  an APPENDIX region exists with at least one per-interview block
  X2  cross-ref integrity: every Q-label referenced anywhere (Q1, Q1a, ...)
      is defined in the Question Bank
  X3  each Appendix block carries only schema fields (Purpose / Interviewer /
      Emphasis); Outcome, Asked and other post-interview content fail here
  X4  no Appendix block heading carries a date or an event-status token. An
      interview's scheduling metadata lives only in session_log.md; a date in
      the prep doc goes stale the moment the interview moves
  R1  each prep-attributed research.md section is dated, sourced, em-dash-free
  S1  each post-screen '## Interview: <audience>' session-log section has the
      required field labels and no em dashes
  S2  each such section's Outcome field is non-empty
  W1  (warn) no prose line directly under a heading (meta-narration proxy)
  W2  (warn) no single bullet packing a ';'-series that also carries its own
      bracket or citation (should expand to sub-bullets)

Usage
  python prep_interview_qc.py check --folder <absolute-path-to-application-folder>

Exit code 0 when all checks pass, 1 otherwise. Findings print one per line as
'CHECK  PASS|FAIL  detail'.

Author    : Jason Delosh
Created   : 2026-07-02
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
# architecture checks (P6-P8, X1-X4) live in _prep_checks, shared with prep_qc
# so both entry points enforce the template identically.
from _prep_checks import (
    _COMMENT_RE, _read, _headings, _sections, _frontmatter_keys,
    _frontmatter_sources, _is_placeholder, _is_optional, check_connectors,
    check_headings, check_xrefs, check_appendix_fields, check_appendix_status)


# ---------------------------------------------------------------------------
# Checks: interview_prep.md against the template
# ---------------------------------------------------------------------------

def check_artifact(artifact_text, template_text, app_folder, profile_dir, findings):
    """Run P1-P5. Appends (check, ok, detail) tuples to findings."""
    art_keys = _frontmatter_keys(artifact_text)
    tpl_keys = _frontmatter_keys(template_text)
    if art_keys is None:
        findings.append(('P1', False, 'artifact has no frontmatter block'))
    else:
        missing = sorted(tpl_keys - art_keys)
        extra = sorted(art_keys - tpl_keys)
        findings.append(('P1', not (missing or extra),
                         'frontmatter keys match template' if not (missing or extra)
                         else f'frontmatter keys differ; missing={missing} extra={extra}'))

    # P2: required = template headings WITHOUT placeholder tokens and WITHOUT the
    # '{optional}' tag. Optional headings are still whitelisted by P7; they are
    # simply not demanded of every artifact.
    tpl_heads = [(d, t) for d, t in _headings(template_text)
                 if not _is_placeholder(t) and not _is_optional(t)]
    art_heads = _headings(artifact_text)
    missing = ['#' * d + ' ' + t for d, t in tpl_heads if (d, t) not in art_heads]
    if missing:
        findings.append(('P2', False, f'missing required headings: {missing}'))
    else:
        idx = 0
        for h in art_heads:
            if idx < len(tpl_heads) and h == tpl_heads[idx]:
                idx += 1
        ok = idx == len(tpl_heads)
        findings.append(('P2', ok,
                         'required headings present in template order' if ok
                         else 'required headings out of template order'))

    # P3: depth cap at four.
    too_deep = [t for d, t in art_heads if d > 4]
    findings.append(('P3', not too_deep,
                     'heading depth capped at ####' if not too_deep
                     else f'headings deeper than ####: {too_deep}'))

    # P4: no em dashes (product artifact).
    findings.append(('P4', '—' not in artifact_text,
                     'no em dashes' if '—' not in artifact_text
                     else 'em dash found in artifact'))

    # P5: frontmatter sources resolve to real files.
    bad = [s for s in _frontmatter_sources(artifact_text)
           if not (os.path.isfile(os.path.join(app_folder, s))
                   or os.path.isfile(os.path.join(profile_dir, s)))]
    findings.append(('P5', not bad,
                     'all frontmatter sources exist' if not bad
                     else f'frontmatter sources not found: {bad}'))


# ---------------------------------------------------------------------------
# Checks: research.md prep-attributed ledger sections only
# ---------------------------------------------------------------------------

_ADDED_RE = re.compile(r'\*\*Added:\*\*\s*(\d{4}-\d{2}-\d{2})\s*\(interview prep')
_URL_RE = re.compile(r'https?://\S+')


def check_research(research_text, findings):
    """Run R1 on the prep-attributed sections. Other sections out of scope."""
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
                     f'{len(prep_sections)} prep ledger section(s) dated, sourced, em-dash-free'
                     if not bad else '; '.join(bad)))


# ---------------------------------------------------------------------------
# Checks: post-screen session-log interview sections
# ---------------------------------------------------------------------------

# A bare ISO date is the only legal value of the 'Interview date:' field; the
# other scheduling facts each have their own field (templates/session_log.md).
_BARE_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def check_session_log(log_text, required_fields, findings):
    """Run S1-S2 on '## Interview: <audience>' sections (Recruiter Screen excluded).

    required_fields comes from templates/session_log.md's '## Interview section'
    block, so adding a field to the schema is a template edit, not a code edit.
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
    sections = [(h, b) for h, b in _sections(log_text)
                if h.startswith('Interview: ') and h != 'Interview: Recruiter Screen']
    if not sections:
        findings.append(('S1', False, "no post-screen '## Interview: <audience>' section"))
        findings.append(('S2', False, 'outcome not checkable (no section)'))
        return
    problems = []
    outcomes_ok = True
    for h, b in sections:
        missing = [f for f in required_fields if f not in b]
        if missing:
            problems.append(f'{h}: missing {missing}')
        if '—' in b:
            problems.append(f'{h}: em dash found')
        dm = re.search(r'^-\s+Interview date:\s*(.*)$', b, re.MULTILINE)
        if dm and not _BARE_DATE_RE.match(dm.group(1).strip()):
            problems.append(f'{h}: Interview date must be a bare YYYY-MM-DD '
                            f'(time / medium / interviewers have their own fields), '
                            f'got "{dm.group(1).strip()}"')
        # Outcome presence is S2's concern (below), not S1's; keeping it out of
        # `problems` leaves S1 = fields present + em-dash-free, matching prep_qc.py.
        m = re.search(r'Outcome:\s*(\S.*)', b)
        if not m:
            outcomes_ok = False
    findings.append(('S1', not problems,
                     f'{len(sections)} interview section(s) complete, em-dash-free'
                     if not problems else '; '.join(problems)))
    findings.append(('S2', outcomes_ok,
                     'outcome(s) recorded' if outcomes_ok else 'an Outcome is empty'))


# ---------------------------------------------------------------------------
# Soft checks (advisory WARN; do not change the exit code)
# ---------------------------------------------------------------------------

def check_leading_prose(artifact_text, findings):
    """W1: warn on a prose line directly under a heading (meta-narration proxy).

    A heading should be followed by bullets, a bold label, or another heading;
    a leading prose sentence is usually build/process narration.
    """
    lines = _COMMENT_RE.sub('', artifact_text).split('\n')
    warns = []
    for i, line in enumerate(lines):
        hm = re.match(r'^(#{1,6})\s+(.*\S)\s*$', line)
        if not hm:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and lines[j].strip()[:1] not in ('-', '*', '#', '<', '[', '>', ''):
            warns.append(f'{hm.group(2)}: "{lines[j].strip()[:48]}"')
    findings.append(('W1', True if not warns else 'warn',
                     'no prose preambles under headings'
                     if not warns
                     else 'prose directly under a heading (meta-narration?): '
                          + '; '.join(warns)))


_SRCID_RE = re.compile(r'\((?:CR|TH)-\d+')


def check_bullet_packing(artifact_text, findings):
    """W2: warn on a single bullet packing a ';'-series that also carries its
    own bracket or source ID (an element with its own weight belongs on its own
    sub-bullet)."""
    warns = []
    for line in _COMMENT_RE.sub('', artifact_text).split('\n'):
        s = line.strip()
        if not (s.startswith('- ') and ';' in s):
            continue
        ids = len(_SRCID_RE.findall(s))
        if (ids >= 1 and '[' in s) or ids >= 2:
            warns.append(s[:60] + ('...' if len(s) > 60 else ''))
    findings.append(('W2', True if not warns else 'warn',
                     'no obvious multi-element bullets'
                     if not warns
                     else 'bullet may pack discrete elements (expand?): '
                          + '; '.join(warns)))


# ---------------------------------------------------------------------------
# Subcommand: check
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Validate one application folder's interview-prep artifacts."""
    fn = cfg['filenames']
    app_folder = os.path.abspath(args.folder)
    profile_dir = os.path.join(repo_root, cfg['paths']['profile'])
    # Structure authority: the shared repo-root template (config-driven).
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
        check_artifact(artifact_text, template_text, app_folder, profile_dir, findings)
        check_connectors(artifact_text, findings)
        check_headings(artifact_text, template_text, findings)
        check_xrefs(artifact_text, findings)
        check_appendix_fields(artifact_text, findings)
        check_appendix_status(artifact_text, findings)
        check_leading_prose(artifact_text, findings)
        check_bullet_packing(artifact_text, findings)

    research_text = _read(os.path.join(app_folder, fn['research_file']))
    if research_text is None:
        findings.append(('R1', False, f"{fn['research_file']} not found"))
    else:
        check_research(research_text, findings)

    log_text = _read(os.path.join(app_folder, fn['session_log_file']))
    if log_text is None:
        findings.append(('S1', False, f"{fn['session_log_file']} not found"))
    else:
        # The interview-section field set is defined once, in the session-log
        # template; both prep QC scripts read it from there.
        log_tpl = _read(os.path.join(repo_root, cfg['paths']['templates'],
                                     fn['session_log_template']))
        if log_tpl is None:
            print(f"FATAL  session log template not found")
            return 1
        check_session_log(log_text, _util.interview_section_fields(log_tpl), findings)

    failed = [f for f in findings if f[1] is False]
    warned = [f for f in findings if f[1] == 'warn']
    for check, ok, detail in findings:
        status = 'PASS' if ok is True else ('WARN' if ok == 'warn' else 'FAIL')
        print(f"{check}  {status}  {detail}")
    passed = len(findings) - len(failed) - len(warned)
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  "
          f"{passed}/{len(findings)} checks passed"
          + (f", {len(warned)} warning(s)" if warned else ""))
    return 0 if not failed else 1


def main():
    parser = argparse.ArgumentParser(
        description='Deterministic QC for preparation-interview artifacts.')
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
