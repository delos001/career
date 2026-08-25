#!/usr/bin/env python3
"""
assemble.py - role-intake artifact assembler

Writes the two artifacts the role-intake skill produces - the session log and the
research file - so the skill does mechanical file-writing through a deterministic
tool instead of by hand. Four subcommands, one per write point in the skill:

  ingest    Phase 3a - create the application folder and write jd.md (plus
            comms.md if supplied) so raw inputs are persisted before the session
            log is written.
  init      Phase 3b - write the initial session log (metadata filled in, axis
            sections marked pending) into the folder created by ingest.
  research  Phase 5 - write (or, on a re-run, refresh) research.md from the four
            Phase-4 subagent output blocks (company, role, industry, critical
            requirements).
  finalize  Phase 7 - complete the session log: fill the research-completed date
            and replace the pending axis sections with the axis-classifier output.

Nothing repo-dependent is hardcoded here. Folder locations, filenames, and naming
patterns come from config.yaml (via _config); the artifact structures come from
the skeletons in the templates folder. Every write is section-scoped: the script
replaces only the sections role-intake owns and leaves anything else in place, so
re-runs and sections added by downstream skills are not clobbered.

Author    : Jason Delosh
Created   : 2026-05-14
Project   : career
Usage     : python scripts/assemble.py ingest   --slug ... --app-id ... --ym ... --jd-text-file ... [--comms-text-file ...]
            python scripts/assemble.py init     --slug ... --app-id ... --ym ... --company ... --role ... [--level ...] [--industry ...] --start-date ... --jd-source ... [--comms-source ...]
            python scripts/assemble.py research --folder ... --app-id ... --company ... --role ... --date ... --company-file ... --role-file ... --industry-file ... --critical-requirements-file ...
            python scripts/assemble.py finalize --session-log ... --date ... --axis-file ... [--research-file ...]
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Shared helpers
# Small utilities used by more than one subcommand: pulling the skeleton out
# of a template, substituting {{tokens}}, and replacing a single Markdown
# section in place. UTF-8 read/write live in scripts/_util.py.
# ---------------------------------------------------------------------------

def _skeleton(templates_dir, template_name):
    """Return the skeleton block from a template file in the templates folder.

    Each template documents its artifact in prose and carries the actual skeleton
    inside the first fenced code block. This pulls out the text between the first
    pair of triple-backtick fences.
    """
    text = _util.read(os.path.join(templates_dir, template_name))
    # Regex: capture everything between the first ``` fence and the next one.
    # re.DOTALL lets '.' span newlines so the whole block is captured.
    m = re.search(r'```\n(.*?)\n```', text, re.DOTALL)
    if not m:
        raise ValueError(f'no fenced skeleton found in template: {template_name}')
    return m.group(1)


def _fill(skeleton, values):
    """Substitute every {{token}} in a skeleton with its value.

    'values' maps token name -> replacement text. Every token in the skeleton
    must be supplied, and no {{...}} may remain afterwards - a mismatch is a bug,
    so it raises rather than writing a half-filled file.
    """
    result = skeleton
    for token, value in values.items():
        placeholder = '{{' + token + '}}'
        if placeholder not in result:
            raise ValueError(f'token not found in skeleton: {placeholder}')
        result = result.replace(placeholder, value)
    # Any {{...}} left over means the caller missed a token.
    leftover = re.findall(r'\{\{.*?\}\}', result)
    if leftover:
        raise ValueError(f'unfilled tokens remain: {leftover}')
    return result


def _replace_section(text, heading, new_section):
    """Replace one Markdown '## heading' section in text with new_section.

    Finds the line '## <heading>' and replaces from there up to (but not
    including) the next '## ' heading, or end of file if it is the last section.
    This keeps every write section-scoped: other sections - including any a
    downstream skill added - are untouched. Raises if the heading is absent.
    """
    # Regex: match the '## heading' line and everything after it, lazily, up to
    # the next '## ' line or the end of the string.
    pattern = re.compile(
        r'^##[ ]' + re.escape(heading) + r'[ \t]*\n.*?(?=^##[ ]|\Z)',
        re.DOTALL | re.MULTILINE,
    )
    if not pattern.search(text):
        raise ValueError(f'section not found: ## {heading}')
    # Normalise to one trailing blank line so sections stay visually separated.
    return pattern.sub(new_section.rstrip() + '\n\n', text)


# ---------------------------------------------------------------------------
# Critical-requirements Type normalization + validation
# The critical-requirements-extractor agent must tag each requirement's Type
# with one of four controlled values (see the agent spec and design decision
# role-intake-critical-requirements-extraction-2026-05). The agent is an LLM and
# deviates from that vocabulary in two distinct ways:
#
#   - Compound (recoverable): a category label is bolted onto a valid severity
#     token, e.g. "education (must-have)". The severity is unambiguous; the
#     decoration carries no weight in the gap-analysis fit-score formula and has
#     no schema field, so it is stripped and the bare token kept. A warning is
#     emitted so the deviation stays visible without halting the pipeline.
#   - Substitution / ambiguous (unrecoverable): the cell carries a "kind of
#     requirement" word with no severity token (Competency / Knowledge /
#     Experience / Credential / Behavior), or two-plus severity tokens. Severity
#     cannot be inferred without guessing, which would silently corrupt scoring,
#     so the write still fails loudly - the deviation is caught at generation
#     time instead of reaching gap-analysis unnoticed.
# ---------------------------------------------------------------------------

# The only Type values the downstream gap-analysis fit-score formula weights.
ALLOWED_REQUIREMENT_TYPES = {'must-have', 'preferred', 'duty-derived', 'contextual'}


def _normalize_requirement_types(block):
    """Normalize recoverable off-spec Type cells; raise on unrecoverable ones.

    'block' is the critical-requirements-extractor output: a Markdown table
    '| # | Text | Type | Source |', or the '(none extracted...)' sentinel when
    the JD is too thin (no rows, nothing to normalize). Returns the block with
    each requirement row's Type cell reduced to one of ALLOWED_REQUIREMENT_TYPES.

    Per row Type cell (see the module-level comment for the two deviation modes):
      - already valid                 -> left untouched.
      - exactly one allowed token
        present plus decoration       -> rewritten to the bare token (recovered);
                                         the change is collected for a warning.
      - zero or two-plus allowed
        tokens present                -> collected as an offender.

    All offenders are gathered before raising so the error lists them at once
    rather than failing on the first.
    """
    out_lines = []
    offenders = []
    changes = []
    for line in block.splitlines():
        stripped = line.strip()
        # Data rows are pipe-delimited; pass anything else through unchanged.
        if not stripped.startswith('|') or not stripped.endswith('|'):
            out_lines.append(line)
            continue
        cells = [c.strip() for c in stripped.strip('|').split('|')]
        # Need at least #, Text, Type. Structural malformation is the downstream
        # parser's concern; this guard only touches the Type cell.
        if len(cells) < 3:
            out_lines.append(line)
            continue
        # Pass through the header row ('#') and the '|---|---|' separator row.
        if cells[0] == '#' or cells[0].startswith('---'):
            out_lines.append(line)
            continue
        # A real requirement row has an integer in the '#' cell.
        try:
            int(cells[0])
        except ValueError:
            out_lines.append(line)
            continue
        type_value = cells[2]
        if type_value in ALLOWED_REQUIREMENT_TYPES:
            out_lines.append(line)
            continue
        # Off-spec cell. Recover only when exactly one severity token is present
        # (none of the four is a substring of another, so a substring scan is a
        # safe whole-token test). Zero present = substitution; two-plus = ambiguous.
        present = [tok for tok in sorted(ALLOWED_REQUIREMENT_TYPES)
                   if tok in type_value.lower()]
        if len(present) == 1:
            normalized = present[0]
            changes.append((cells[0], type_value, normalized))
            cells[2] = normalized
            out_lines.append('| ' + ' | '.join(cells) + ' |')
        else:
            offenders.append((cells[0], type_value))
            out_lines.append(line)
    if offenders:
        listed = ', '.join(f'row {n}: "{t}"' for n, t in offenders)
        allowed = ', '.join(sorted(ALLOWED_REQUIREMENT_TYPES))
        raise ValueError(
            f'critical-requirements Type column has unrecoverable off-spec values '
            f'({listed}); allowed: {allowed}. No single severity token could be '
            'recovered from these cells (substitution or ambiguous), so the severity '
            'cannot be inferred without corrupting the fit score. Re-run the extractor '
            'or correct the Type cells before assembling research.md.'
        )
    if changes:
        listed = '; '.join(f'row {n}: "{orig}" -> "{norm}"' for n, orig, norm in changes)
        print(
            f'WARNING: normalized {len(changes)} compound critical-requirements Type '
            f'value(s) to the controlled vocabulary ({listed}). The extractor bolted a '
            'category label onto a valid severity token; the token was kept and the '
            'decoration stripped.',
            file=sys.stderr,
        )
    return '\n'.join(out_lines)


# ---------------------------------------------------------------------------
# Subcommand: ingest  (role-intake Phase 3a)
# Creates the application folder and writes the JD (and comms if present) to
# disk immediately. Run this before 'init' so raw inputs are persisted before
# the session log is written - if the session closes between the two calls the
# inputs survive and the run can be resumed from the session-log step.
# ---------------------------------------------------------------------------

def cmd_ingest(args, repo_root, cfg):
    stem = cfg['naming']['application_stem'].format(
        slug=args.slug.lower(), app_id=args.app_id, ym=args.ym)
    app_folder = os.path.join(repo_root, cfg['paths']['applications'], stem)

    os.makedirs(app_folder, exist_ok=True)

    jd_file_name = cfg['filenames']['jd_file']
    jd_path = os.path.join(app_folder, jd_file_name)
    jd_text = _util.read(args.jd_text_file)
    # Prepend an identity header when the JD body does not name the role and/or
    # company. Some JDs carry no in-text identifiers; the header makes jd.md
    # traceable to its application even when read in isolation. The skill decides
    # presence (it read the JD) and passes only the missing value(s).
    header_lines = []
    if args.add_title:
        header_lines.append(f'**Role:** {args.add_title}')
    if args.add_company:
        header_lines.append(f'**Company:** {args.add_company}')
    if header_lines:
        jd_text = '\n'.join(header_lines) + '\n\n---\n\n' + jd_text
    _util.write(jd_path, jd_text)

    comms_file_name = cfg['filenames']['comms_file']
    comms_path = None
    if args.comms_text_file:
        comms_path = os.path.join(app_folder, comms_file_name)
        _util.write(comms_path, _util.read(args.comms_text_file))

    # Print written paths so the skill can capture them and pass jd_path
    # (and comms_path) as the --jd-source / --comms-source to 'init'.
    print(app_folder)
    print(jd_path)
    if comms_path is not None:
        print(comms_path)


# ---------------------------------------------------------------------------
# Subcommand: init  (role-intake Phase 3b)
# Writes the initial session log into an already-existing application folder.
# Run after 'ingest'. JD and comms are already on disk; this step only needs
# their canonical paths (for the session log) plus the confirmed metadata.
# ---------------------------------------------------------------------------

def cmd_init(args, repo_root, cfg):
    stem = cfg['naming']['application_stem'].format(
        slug=args.slug.lower(), app_id=args.app_id, ym=args.ym)
    app_folder = os.path.join(repo_root, cfg['paths']['applications'], stem)
    # The session log is a per-application artifact living in the app folder
    # alongside research.md / jd.md, under the fixed filename from config.
    session_log = os.path.join(app_folder, cfg['filenames']['session_log_file'])

    # Fail loudly rather than overwrite: an existing session log means this is
    # really a resume, which the skill's resume check should have caught.
    if os.path.exists(session_log):
        raise FileExistsError(f'session log already exists: {session_log}')
    # Folder must exist - ingest creates it; missing folder means ingest was skipped.
    if not os.path.exists(app_folder):
        raise FileNotFoundError(f'application folder not found (run ingest first): {app_folder}')

    jd_file_name = cfg['filenames']['jd_file']
    comms_file_name = cfg['filenames']['comms_file']
    # comms_source presence signals that comms were ingested.
    comms_file_value = comms_file_name if args.comms_source else ''
    comms_source_value = args.comms_source or ''

    templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
    skeleton = _skeleton(templates_dir, cfg['filenames']['session_log_template'])
    body = _fill(skeleton, {
        'company': args.company,
        'role': args.role,
        'ym': args.ym,
        'app_id': args.app_id,
        # Level and industry are deferred to the axis-classifier (Phase 6) and
        # written by finalize (Phase 7); init leaves them pending.
        'role_level': args.level or '_(pending)_',
        'industry': args.industry or '_(pending)_',
        'start_date': args.start_date,
        'jd_file': jd_file_name,
        'jd_source': args.jd_source,
        'comms_file': comms_file_value,
        'comms_source': comms_source_value,
        # Not known yet; finalize (Phase 7) fills these in.
        'research_completed_date': '_(pending)_',
        'axis_classification': '## Axis Classification\n\n_(pending)_',
        'axis_gaps': '## Axis Gaps\n\n_(pending)_',
    })
    _util.write(session_log, body)
    print(app_folder)
    print(session_log)


# ---------------------------------------------------------------------------
# Subcommand: research  (role-intake Phase 5)
# Writes research.md from the four Phase 4 subagent output blocks: company,
# role, industry, and critical requirements. On a re-run it replaces only
# role-intake's own sections, leaving anything else.
# ---------------------------------------------------------------------------

def cmd_research(args, repo_root, cfg):
    research_file = os.path.join(args.folder, cfg['filenames']['research_file'])
    company_block = _util.read(args.company_file).strip()
    role_block = _util.read(args.role_file).strip()
    industry_block = _util.read(args.industry_file).strip()
    critical_requirements_block = _util.read(args.critical_requirements_file).strip()
    # Guard: normalize recoverable off-spec Type values (compound cells like
    # "education (must-have)") and reject unrecoverable ones before they reach
    # research.md and silently corrupt gap-analysis scoring. Unrecoverable cases
    # fail loudly (non-zero exit) so the role-intake skill halts per global-rules.md.
    critical_requirements_block = _normalize_requirement_types(critical_requirements_block)

    if not os.path.exists(research_file):
        # First write: render the whole file from the template.
        templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
        skeleton = _skeleton(templates_dir, cfg['filenames']['research_file_template'])
        body = _fill(skeleton, {
            'company': args.company,
            'role': args.role,
            'app_id': args.app_id,
            'research_completed_date': args.date,
            'company_block': company_block,
            'role_block': role_block,
            'industry_block': industry_block,
            'critical_requirements_block': critical_requirements_block,
            # Filled at finalize (Phase 7) once axis-classifier has run.
            'axis_gaps': '## Axis Gaps\n\n_(pending)_',
        })
        _util.write(research_file, body)
    else:
        # Re-run: replace only role-intake's sections and the completed-date
        # line, so a current-state refresh does not clobber anything else.
        text = _util.read(research_file)
        text = re.sub(r'(?m)^\*\*Research completed:\*\* .*$',
                      f'**Research completed:** {args.date}', text)
        text = _replace_section(text, 'Company', company_block)
        text = _replace_section(text, 'Role', role_block)
        text = _replace_section(text, 'Industry', industry_block)
        # Critical Requirements is a newer section (added per
        # role-intake-critical-requirements-extraction-2026-05). Insert it on
        # research.md files that pre-date the addition; replace it on files
        # that already have it. The Axis-Gaps insert path uses string splice
        # rather than re.sub so the requirements text (verbatim subagent
        # output) is not interpreted as a regex replacement string.
        if re.search(r'(?m)^## Critical Requirements\b', text):
            text = _replace_section(text, 'Critical Requirements', critical_requirements_block)
        else:
            m_gaps = re.search(r'(?m)^## Axis Gaps\b', text)
            if m_gaps:
                text = (
                    text[:m_gaps.start()]
                    + critical_requirements_block.rstrip()
                    + '\n\n'
                    + text[m_gaps.start():]
                )
            else:
                text = text.rstrip() + '\n\n' + critical_requirements_block.rstrip() + '\n'
        _util.write(research_file, text)
    print(research_file)


# ---------------------------------------------------------------------------
# Subcommand: finalize  (role-intake Phase 7)
# Completes the session log: fills the research-completed date and replaces the
# pending axis sections with the axis-classifier subagent's output.
# ---------------------------------------------------------------------------

# Regex: an axis label in any form the classifier has emitted - with or without
# the leading bullet, with or without bold markers around the label.
_AXIS_LINE_RE = re.compile(
    r'^-?\s*\*{0,2}(Orientation|Industry|Specialty|Level|Work-state):\*{0,2}'
    r'\s*(.*)$')


def _normalize_axis_lines(body):
    """Return an axis block rewritten into the classifier's declared form.

    The classifier's return-format spec emits `- <Axis>: <values> - <rationale>`
    with a bare label and a plain-hyphen separator, but it has drifted to bolded
    labels, missing bullets, and em dash separators across runs. Normalizing on
    the way in means the session log always carries the spec form no matter what
    the subagent produced, so every downstream reader (staging_append.py,
    retrieval_qc.py, role_intake_qc.py check I5) has one shape to match. Fixing
    the generator rather than the artifact, per
    feedback_qc_structural_finding_script_seam.

    Lines carrying no axis label pass through untouched, so sub-bullets the
    classifier adds are preserved rather than silently dropped.
    """
    out = []
    for line in body.split('\n'):
        m = _AXIS_LINE_RE.match(line)
        if not m:
            out.append(line)
            continue
        # Only the FIRST em dash is the value/rationale separator; any later one
        # sits inside the rationale prose and is left alone.
        rest = m.group(2).replace(' — ', ' - ', 1)
        out.append(f'- {m.group(1)}: {rest}')
    return '\n'.join(out)


def cmd_finalize(args, repo_root, cfg):
    # repo_root and cfg are unused here by design: finalize only edits an existing
    # session log (path passed in), and the section headings it targets stay
    # inline rather than in config.
    text = _util.read(args.session_log)

    # Fill the research-completed date line in the Metadata section.
    text = re.sub(r'(?m)^- Research Completed Date: .*$',
                  f'- Research Completed Date: {args.date}', text)

    # Split the axis file into classification lines and gaps lines. The classifier
    # may emit either '## Axis Gaps' (heading form) or 'Axis gaps:' (inline form);
    # accept both so the split is reliable regardless of classifier output style.
    axis_text = _util.read(args.axis_file).strip()
    split_pat = re.compile(r'(?mi)^(?:##\s+)?Axis\s+Gaps:?\s*$')
    parts = split_pat.split(axis_text, maxsplit=1)

    classification_body = parts[0].strip()
    # The classifier emits its own '## Axis Classification' heading; strip a
    # leading one so the heading re-added below is not duplicated. (The gaps
    # half needs no equivalent strip: the split above already consumed its
    # 'Axis Gaps' heading.)
    classification_body = re.sub(
        r'(?i)\A##[ \t]+Axis[ \t]+Classification[ \t]*\n+', '', classification_body
    ).strip()
    # Normalize before anything reads or writes the block, so the value
    # extraction below and the session log itself both see the spec form.
    classification_body = _normalize_axis_lines(classification_body)
    if len(parts) > 1:
        gaps_body = _normalize_axis_lines(parts[1].strip())
        gaps_content = 'None' if not gaps_body or gaps_body.lower() == 'none' else gaps_body
    else:
        gaps_content = 'None'

    # Fill the deferred Level and Industry metadata lines from the axis result.
    # Level and industry are not inferred at JD read-in (unreliable from the JD
    # alone); the axis-classifier decides them after research, so init left both
    # '_(pending)_' and finalize writes the resolved axis values here.
    def _axis_value(axis_name):
        # classification_body has been normalized to the classifier's declared
        # form above, so only that form needs matching here.
        m = re.search(rf'(?m)^- {re.escape(axis_name)}:[ \t]*(.+)$',
                      classification_body)
        if not m:
            return None
        # The classifier line is '<value> - <rationale>'; keep only the value.
        return re.split(r'[ \t]+-[ \t]+', m.group(1).strip(), maxsplit=1)[0].strip()

    level_value = _axis_value('Level')
    industry_value = _axis_value('Industry')
    # Replacement via lambda so a value containing a backslash or group ref is
    # not interpreted as a regex replacement template.
    if level_value:
        text = re.sub(r'(?m)^- Role Level: .*$',
                      lambda _m: f'- Role Level: {level_value}', text)
    if industry_value:
        text = re.sub(r'(?m)^- Industry: .*$',
                      lambda _m: f'- Industry: {industry_value}', text)

    # _replace_section replaces the whole matched block including its '## Heading'
    # line, so each new_section must carry the heading itself.
    classification_section = f'## Axis Classification\n\n{classification_body}'
    gaps_section = f'## Axis Gaps\n\n{gaps_content}'

    text = _replace_section(text, 'Axis Classification', classification_section)
    text = _replace_section(text, 'Axis Gaps', gaps_section)
    _util.write(args.session_log, text)
    print(args.session_log)

    if args.research_file:
        research_text = _util.read(args.research_file)
        research_text = _replace_section(research_text, 'Axis Gaps', gaps_section)
        _util.write(args.research_file, research_text)
        print(args.research_file)


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses the subcommand and its arguments, loads config, runs the subcommand,
# and reports any failure to stderr with a non-zero exit so the calling skill
# halts per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='role-intake artifact assembler')
    sub = parser.add_subparsers(dest='command', required=True)

    p_ingest = sub.add_parser('ingest', help='Phase 3a: create folder and write JD + comms to disk')
    p_ingest.add_argument('--slug', required=True)
    p_ingest.add_argument('--app-id', required=True)
    p_ingest.add_argument('--ym', required=True, help='year-month, e.g. 2026-05')
    p_ingest.add_argument('--jd-text-file', required=True,
                          help='path to a file holding the extracted JD text')
    p_ingest.add_argument('--comms-text-file', default=None,
                          help='path to a file holding the extracted comms text (optional)')
    p_ingest.add_argument('--add-title', default=None,
                          help='prepend a Role: header to jd.md (pass only when the JD body does not name the role)')
    p_ingest.add_argument('--add-company', default=None,
                          help='prepend a Company: header to jd.md (pass only when the JD body does not name the company)')
    p_ingest.set_defaults(func=cmd_ingest)

    p_init = sub.add_parser('init', help='Phase 3b: write initial session log (run after ingest)')
    p_init.add_argument('--slug', required=True)
    p_init.add_argument('--app-id', required=True)
    p_init.add_argument('--ym', required=True, help='year-month, e.g. 2026-05')
    p_init.add_argument('--company', required=True)
    p_init.add_argument('--role', required=True)
    # Level and industry are deferred to the axis-classifier (Phase 6) and filled
    # by finalize (Phase 7); init writes them as pending if not supplied.
    p_init.add_argument('--level', default=None)
    p_init.add_argument('--industry', default=None)
    p_init.add_argument('--start-date', required=True, help='YYYY-MM-DD')
    p_init.add_argument('--jd-source', required=True,
                        help='app-folder path to jd.md (from ingest output), or URL')
    p_init.add_argument('--comms-source', default=None,
                        help='app-folder path to comms.md (from ingest output), URL, or "pasted"; omit if no comms')
    p_init.set_defaults(func=cmd_init)

    p_res = sub.add_parser('research', help='Phase 5: write research.md')
    p_res.add_argument('--folder', required=True, help='the application folder')
    p_res.add_argument('--app-id', required=True)
    p_res.add_argument('--company', required=True)
    p_res.add_argument('--role', required=True)
    p_res.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_res.add_argument('--company-file', required=True)
    p_res.add_argument('--role-file', required=True)
    p_res.add_argument('--industry-file', required=True)
    p_res.add_argument('--critical-requirements-file', required=True,
                       help='path to a file holding the critical-requirements-extractor output block')
    p_res.set_defaults(func=cmd_research)

    p_fin = sub.add_parser('finalize', help='Phase 7: complete the session log')
    p_fin.add_argument('--session-log', required=True)
    p_fin.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_fin.add_argument('--axis-file', required=True)
    p_fin.add_argument('--research-file', default=None,
                       help='path to research.md; when supplied, Axis Gaps is also written there')
    p_fin.set_defaults(func=cmd_finalize)

    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
