#!/usr/bin/env python3
"""
prep_interview_qc.py - deterministic QC for the preparation-interview skill

Validates the cumulative interview_prep.md (main body + per-interview Appendix)
plus the prep-attributed research ledger and the post-screen session-log
sections. Scoped to what this skill owns; the recruiter-screen '## Interview:
Screen' section belongs to preparation-screen (prep_qc.py) and is not checked
here.

Structure is judged against the preparation-interview template (the skill-local
structure authority). Template headings that carry placeholder tokens (angle
brackets, e.g. '## <Audience> - <Interviewer(s)>') are patterns, not required
literals, and are excluded from the required-heading set.

Checks
  P1  frontmatter present; key set matches the template's key set exactly
  P2  every non-placeholder template heading present, in template order, at
      the template's depth (extras allowed)
  P3  heading depth never exceeds four (####)
  P4  no em dashes in the artifact
  P5  every frontmatter `sources` file exists (app folder or profile folder)
  X1  an APPENDIX region exists with at least one per-interview block
  X2  cross-ref integrity: every Q-label referenced anywhere (Q1, Q1a, ...)
      is defined in the Question Bank
  R1  each prep-attributed research.md section is dated, sourced, em-dash-free
  S1  each post-screen '## Interview: <audience>' session-log section has the
      required field labels and no em dashes
  S2  each such section's Outcome field is non-empty

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


# ---------------------------------------------------------------------------
# Markdown parsing helpers (self-contained; mirror prep_qc.py conventions)
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)
_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*\S)\s*$', re.MULTILINE)
_FRONTMATTER_RE = re.compile(r'\A---\s*\n(.*?)\n---\s*\n', re.DOTALL)
_FM_KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:', re.MULTILINE)


def _read(path):
    """Return the file's text, or None when the file does not exist."""
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _headings(text):
    """Return ordered (depth, text) heading tuples, comments stripped."""
    clean = _COMMENT_RE.sub('', text)
    return [(len(m.group(1)), m.group(2)) for m in _HEADING_RE.finditer(clean)]


def _frontmatter_keys(text):
    """Return the set of top-level frontmatter keys, or None if no block."""
    m = _FRONTMATTER_RE.match(text)
    return set(_FM_KEY_RE.findall(m.group(1))) if m else None


def _frontmatter_sources(text):
    """Return the filenames in the frontmatter 'sources: [...]' list."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return []
    sm = re.search(r'^sources\s*:\s*\[(.*?)\]', m.group(1), re.MULTILINE)
    return [s.strip() for s in sm.group(1).split(',') if s.strip()] if sm else []


def _sections(text):
    """Split on '## ' headings; return ordered (heading_text, body) tuples."""
    out = []
    matches = [m for m in _HEADING_RE.finditer(text) if len(m.group(1)) == 2]
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(2), text[start:end]))
    return out


def _is_placeholder(heading_text):
    """True when a heading carries an angle-bracket token, i.e. it is a pattern."""
    return '<' in heading_text and '>' in heading_text


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

    # P2: required = template headings WITHOUT placeholder tokens.
    tpl_heads = [(d, t) for d, t in _headings(template_text) if not _is_placeholder(t)]
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
# Checks: architecture integrity (Appendix presence, Q-label cross-refs)
# ---------------------------------------------------------------------------

_APPENDIX_RE = re.compile(r'^#\s+APPENDIX\b', re.MULTILINE)
_QLABEL_REF_RE = re.compile(r'\bQ\d+[a-z]?\b')
# A Question Bank entry defines its label as '- **Q1 ...' / '- **Q1a ...'.
_QLABEL_DEF_RE = re.compile(r'^-\s+\*\*(Q\d+[a-z]?)\b', re.MULTILINE)


def check_xrefs(artifact_text, findings):
    """Run X1 (Appendix block present) and X2 (Q-label cross-ref integrity)."""
    m = _APPENDIX_RE.search(artifact_text)
    if not m:
        findings.append(('X1', False, "no '# APPENDIX' region"))
    else:
        after = artifact_text[m.end():]
        blocks = [h for h, _ in _sections(after)]
        findings.append(('X1', bool(blocks),
                         f'{len(blocks)} per-interview block(s)' if blocks
                         else 'APPENDIX region has no per-interview block'))

    bank_body = next((b for h, b in _sections(artifact_text)
                      if h.startswith('Question Bank')), None)
    if bank_body is None:
        findings.append(('X2', False, 'no Question Bank section to resolve Q-labels against'))
        return
    defined = set(_QLABEL_DEF_RE.findall(bank_body))
    referenced = set(_QLABEL_REF_RE.findall(artifact_text))
    dangling = sorted(referenced - defined)
    findings.append(('X2', not dangling,
                     f'all Q-label references resolve ({len(defined)} defined)'
                     if not dangling
                     else f'Q-labels referenced but not defined in Question Bank: {dangling}'))


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

_INTERVIEW_FIELDS = ('Prep date:', 'Prep artifact:', 'Research added:',
                     'Interview date:', 'Outcome:')


def check_session_log(log_text, findings):
    """Run S1-S2 on '## Interview: <audience>' sections (Screen excluded)."""
    sections = [(h, b) for h, b in _sections(log_text)
                if h.startswith('Interview: ') and h != 'Interview: Screen']
    if not sections:
        findings.append(('S1', False, "no post-screen '## Interview: <audience>' section"))
        findings.append(('S2', False, 'outcome not checkable (no section)'))
        return
    problems = []
    outcomes_ok = True
    for h, b in sections:
        missing = [f for f in _INTERVIEW_FIELDS if f not in b]
        if missing:
            problems.append(f'{h}: missing {missing}')
        if '—' in b:
            problems.append(f'{h}: em dash found')
        m = re.search(r'Outcome:\s*(\S.*)', b)
        if not m:
            outcomes_ok = False
            problems.append(f'{h}: Outcome empty')
    findings.append(('S1', not problems,
                     f'{len(sections)} interview section(s) complete, em-dash-free'
                     if not problems else '; '.join(problems)))
    findings.append(('S2', outcomes_ok,
                     'outcome(s) recorded' if outcomes_ok else 'an Outcome is empty'))


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
        check_xrefs(artifact_text, findings)

    research_text = _read(os.path.join(app_folder, fn['research_file']))
    if research_text is None:
        findings.append(('R1', False, f"{fn['research_file']} not found"))
    else:
        check_research(research_text, findings)

    log_text = _read(os.path.join(app_folder, fn['session_log_file']))
    if log_text is None:
        findings.append(('S1', False, f"{fn['session_log_file']} not found"))
    else:
        check_session_log(log_text, findings)

    failed = [f for f in findings if not f[1]]
    for check, ok, detail in findings:
        print(f"{check}  {'PASS' if ok else 'FAIL'}  {detail}")
    print(f"RESULT  {'PASS' if not failed else 'FAIL'}  "
          f"{len(findings) - len(failed)}/{len(findings)} checks passed")
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
