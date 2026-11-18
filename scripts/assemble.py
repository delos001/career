#!/usr/bin/env python3
"""
assemble.py - role-intake artifact assembler

Writes what the role-intake skill produces - the application folder, jd.md /
comms.md, and the session log - so the skill does mechanical file-writing
through a deterministic tool instead of by hand. One subcommand per write point:

  folder    Phase 4 - resolve the company's slug (company_slug.py; a new
            company needs --slug, asked for before any ID is claimed), take the
            month from today, claim the next APP-NNN (app_id.py) and create its
            folder; print the folder path, the ID, then the slug. Never run on a
            resume: the folder already exists.
  ingest    Phase 5 - write jd.md (plus comms.md if supplied) into the folder,
            headed by the confirmed title and company. Refuses a folder that was never
            created. Deletes its input files once saved, but only those inside
            temp/ (Phase 1's working files).
  init      Phase 6 - write the initial session log (metadata filled in, the
            research date and axis sections marked pending) into the folder.
            --replace rewrites it, refused once research or a later section
            exists.
  relabel   Correction - fix the company and/or title in place, keeping the
            APP-NNN, and rename the folder when the slug changes. Used by
            role-intake and role-research.

research.md is written by the role-research skill (role_research_assemble.py)
and the pending sections by role-classify (role_classify_assemble.py); both
import this file's section helpers.

Nothing repo-dependent is hardcoded here. Folder locations, filenames, and naming
patterns come from config.yaml (via _config); the artifact structures come from
the skeletons in the templates folder. Every write is section-scoped: the script
replaces only the sections role-intake owns and leaves anything else in place, so
re-runs and sections added by downstream skills are not clobbered.

Author    : Jason Delosh
Created   : 2026-05-14
Project   : career
Usage     : python scripts/assemble.py folder   --company ... [--slug ...]
            python scripts/assemble.py ingest   --folder ... --jd-text-file ... --title ... --company ... [--comms-text-file ...]
            python scripts/assemble.py init     --folder ... --company ... --role ... [--level ...] [--industry ...] --start-date ... --jd-source ... [--comms-source ...] [--replace]
            python scripts/assemble.py relabel  --folder ... [--company ... [--slug ...]] [--role ...]
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import app_id
import company_slug


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
    # Replacement via lambda so a section holding a backslash (a Windows path)
    # is not read as a regex replacement template.
    replacement = new_section.rstrip() + '\n\n'
    return pattern.sub(lambda _m: replacement, text)


def _app_folder(args, repo_root, cfg):
    """Return the application folder path named by slug, APP-NNN, and month."""
    stem = cfg['naming']['application_stem'].format(
        slug=args.slug.lower(), app_id=args.app_id, ym=args.ym)
    return os.path.join(repo_root, cfg['paths']['applications'], stem)


def _existing_folder(folder):
    """Return an application folder's absolute path; raise if it was never created."""
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        raise FileNotFoundError(
            f'application folder not found (run the folder step first): {folder}')
    return folder


def _stem_ids(folder, cfg):
    """Return (app_id, ym) read from an application folder's name.

    The name is '<slug>_<APP-NNN>_<YYYY-MM>' (naming.application_stem). The slug
    is everything before the ID, since a slug may itself hold an underscore.
    """
    prefix = re.escape(cfg['naming']['app_id_prefix'])
    m = re.fullmatch(rf'.+?_({prefix}\d+)_(\d{{4}}-\d{{2}})', os.path.basename(folder))
    if not m:
        raise ValueError(f'not an application folder name: {os.path.basename(folder)}')
    return m.group(1), m.group(2)


# ---------------------------------------------------------------------------
# Subcommand: folder  (role-intake Phase 4)
# Claims the next APP-NNN and creates its application folder in one call, so the
# ID never exists only in the conversation and nothing later creates the folder
# as a side effect. Every call is a new application; a resume finds its folder
# with paths.py and never runs this.
# ---------------------------------------------------------------------------

def cmd_folder(args, repo_root, cfg):
    # Slug first: a new company with no --slug stops here, before an ID is claimed.
    args.slug, is_new = company_slug.choose(repo_root, cfg, args.company, args.slug)
    if is_new:
        company_slug.record(repo_root, cfg, args.company, args.slug)
    args.ym = _util.today_iso()[:7]
    args.app_id = app_id.claim_app_id()
    app_folder = _app_folder(args, repo_root, cfg)
    # A fresh claim cannot have a folder yet; one existing means something is wrong.
    os.makedirs(app_folder, exist_ok=False)
    print(app_folder)
    print(args.app_id)
    print(args.slug)


# ---------------------------------------------------------------------------
# Subcommand: ingest  (role-intake Phase 5)
# Writes the JD (and comms if present) into the application folder. Run this
# before 'init' so raw inputs are persisted before the session log is written -
# if the session closes between the two calls the inputs survive and the run
# can be resumed from the session-log step. The folder must already exist:
# a missing one means the folder step was skipped.
# ---------------------------------------------------------------------------

def cmd_ingest(args, repo_root, cfg):
    app_folder = _existing_folder(args.folder)

    jd_file_name = cfg['filenames']['jd_file']
    jd_path = os.path.join(app_folder, jd_file_name)
    jd_text = _util.read(args.jd_text_file)
    # Always prepend the confirmed title and company as an identity header, so
    # every jd.md names its role the same way at the top. A name found somewhere
    # in the JD text does not identify the role, and relabel rewrites these lines.
    jd_text = f'**Role:** {args.title}\n**Company:** {args.company}\n\n---\n\n' + jd_text
    _util.write(jd_path, jd_text)

    comms_file_name = cfg['filenames']['comms_file']
    comms_path = None
    if args.comms_text_file:
        comms_path = os.path.join(app_folder, comms_file_name)
        _util.write(comms_path, _util.read(args.comms_text_file))

    # The inputs are Phase 1's working files; once saved they have no further
    # use. Only files inside temp/ are removed, so a file passed from anywhere
    # else is never deleted.
    temp_dir = os.path.abspath(os.path.join(repo_root, cfg['paths']['temp'])) + os.sep
    for used in (args.jd_text_file, args.comms_text_file):
        if used and os.path.abspath(used).startswith(temp_dir):
            os.remove(used)

    # Print written paths so the skill can capture them and pass jd_path
    # (and comms_path) as the --jd-source / --comms-source to 'init'.
    print(jd_path)
    if comms_path is not None:
        print(comms_path)


# ---------------------------------------------------------------------------
# Subcommand: init  (role-intake Phase 6)
# Writes the initial session log into an already-existing application folder.
# Run after 'ingest'. JD and comms are already on disk; this step only needs
# their canonical paths (for the session log) plus the confirmed metadata.
# ---------------------------------------------------------------------------

def cmd_init(args, repo_root, cfg):
    app_folder = _existing_folder(args.folder)
    app_id_value, ym = _stem_ids(app_folder, cfg)
    # The session log is a per-application artifact living in the app folder
    # alongside research.md / jd.md, under the fixed filename from config.
    session_log = os.path.join(app_folder, cfg['filenames']['session_log_file'])

    # Fail loudly rather than overwrite: an existing session log means this is
    # really a resume, which the skill's resume check should have caught.
    # --replace rewrites it to correct role-intake's own fields, but only while
    # nothing later has been added: once research has run, or another skill has
    # appended a section, rewriting would drop that work.
    if os.path.exists(session_log):
        if not args.replace:
            raise FileExistsError(f'session log already exists (pass --replace to correct it): {session_log}')
        if os.path.exists(os.path.join(app_folder, cfg['filenames']['research_file'])):
            raise ValueError('research has run for this application; correct the session log through '
                             'relabel or by hand, not --replace')
        sections = re.findall(r'(?m)^## (.+?)\s*$', _util.read(session_log))
        extra = [s for s in sections if s not in ('Metadata', 'Axis Classification', 'Axis Gaps')]
        if extra:
            raise ValueError(f'the session log has sections from later skills ({", ".join(extra)}); '
                             f'--replace would drop them')

    # A source records where the text came from (URL, original file path, or
    # "pasted"). Its copy in the application folder is already named by the
    # 'file' field, and a folder path goes stale when relabel renames the folder.
    folder_prefix = app_folder + os.sep
    for flag, value in (('--jd-source', args.jd_source), ('--comms-source', args.comms_source)):
        if value and os.path.isabs(value) and os.path.abspath(value).startswith(folder_prefix):
            raise ValueError(f'{flag} records where the text came from (a URL, the original file path, '
                             f'or "pasted"), not its copy in the application folder: {value}')

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
        'ym': ym,
        'app_id': app_id_value,
        # Level and industry are decided by the role-classify skill, which
        # writes them; init leaves them pending.
        'role_level': args.level or '_(pending)_',
        'industry': args.industry or '_(pending)_',
        'start_date': args.start_date,
        'jd_file': jd_file_name,
        'jd_source': args.jd_source,
        'comms_file': comms_file_value,
        'comms_source': comms_source_value,
        # Not known yet: the research step fills the date, role-classify the axes.
        'research_completed_date': '_(pending)_',
        'axis_classification': '## Axis Classification\n\n_(pending)_',
        'axis_gaps': '## Axis Gaps\n\n_(pending)_',
    })
    _util.write(session_log, body)
    print(app_folder)
    print(session_log)


# ---------------------------------------------------------------------------
# Subcommand: relabel  (correction, role-intake or role-research)
# Corrects the company and/or title after the folder exists, keeping the
# APP-NNN. Going back to Phase 3 and running forward would repeat Phase 4,
# which claims a new APP-NNN and makes a second folder. Rewrites the session
# log's H1 and Company/Role lines, the research H1, and jd.md's identity header,
# then renames the folder when the slug changes. --slug on
# its own changes the company's registry slug, refused while another
# application folder uses the old one. Refuses a folder holding files a later
# skill wrote: those carry the old labels too.
# ---------------------------------------------------------------------------

def _relabel_h1(text, prefix, company, role):
    """Rewrite '# <prefix>: <company> | <role>[ | ...]', keeping any later parts."""
    def fix(m):
        parts = m.group(1).split(' | ')
        if company:
            parts[0] = company
        if role and len(parts) > 1:
            parts[1] = role
        return f'# {prefix}: ' + ' | '.join(parts)
    new, count = re.subn(rf'(?m)^# {re.escape(prefix)}: (.+)$', fix, text, count=1)
    if not count:
        raise ValueError(f'no "# {prefix}:" heading to correct')
    return new


def _relabel_field(text, pattern, value, what):
    """Replace one label line's value; raise when the line is absent."""
    new, count = re.subn(pattern, lambda m: m.group(1) + value, text, count=1)
    if not count:
        raise ValueError(f'no {what} line to correct')
    return new


def cmd_relabel(args, repo_root, cfg):
    if not (args.company or args.role or args.slug):
        raise ValueError('pass --company, --role, --slug, or a combination')
    fn = cfg['filenames']
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f'application folder not found: {folder}')

    # Only role-intake's and role-research's files may be present.
    own = {fn['jd_file'], fn['comms_file'], fn['session_log_file'], fn['research_file'],
           fn['scratch_subdir']}
    later = sorted(set(os.listdir(folder)) - own)
    if later:
        raise ValueError(f'later skills have written {", ".join(later)}; relabel corrects role-intake '
                         f'and role-research files only, so those would keep the old labels')

    # Session log: H1 plus the Company / Role metadata lines.
    log_path = os.path.join(folder, fn['session_log_file'])
    log = _relabel_h1(_util.read(log_path), 'Session Log', args.company, args.role)
    if args.company:
        log = _relabel_field(log, r'(?m)^(- Company: ).*$', args.company, 'session log Company')
    if args.role:
        log = _relabel_field(log, r'(?m)^(- Role: ).*$', args.role, 'session log Role')
    m = re.search(r'(?m)^- APP-NNN: (\S+)', log)
    if not m:
        raise ValueError('session log has no APP-NNN line')
    app_id = m.group(1)

    # Research file, if research has run.
    research_path = os.path.join(folder, fn['research_file'])
    research = None
    if os.path.isfile(research_path):
        research = _relabel_h1(_util.read(research_path), 'Research', args.company, args.role)

    # jd.md identity header: the Role and Company lines ingest wrote before its
    # '---' rule. A jd.md written before 2026-11-17 may carry one line or none;
    # a line it lacks is not added.
    jd_path = os.path.join(folder, fn['jd_file'])
    jd = _util.read(jd_path)
    head, sep, body = jd.partition('\n\n---\n\n')
    if sep and re.fullmatch(r'(\*\*(Role|Company):\*\* .+\n?)+', head + '\n'):
        if args.role:
            head = re.sub(r'(?m)^(\*\*Role:\*\* ).*$', lambda m: m.group(1) + args.role, head)
        if args.company:
            head = re.sub(r'(?m)^(\*\*Company:\*\* ).*$', lambda m: m.group(1) + args.company, head)
        jd = head + sep + body

    # Folder name: same APP-NNN and month, the company's slug.
    name = os.path.basename(folder)
    target = folder
    at = name.find('_' + app_id)
    if (args.company or args.slug) and at < 0:
        raise ValueError(f'folder name {name} does not carry {app_id}')
    registry_write = None
    if args.company or args.slug:
        company = args.company or re.search(r'(?m)^- Company: (.+?)\s*$', log).group(1)
        known = company_slug.lookup(repo_root, cfg, company)
        if known and args.slug and args.slug.strip().lower() != known:
            # Changing a recorded company's slug. Refused while any other
            # application folder carries the old slug, since the company would
            # then live under two slugs.
            apps_dir = os.path.dirname(folder)
            prefix = re.escape(cfg['naming']['app_id_prefix'])
            users = sorted(f for f in os.listdir(apps_dir) if f != name
                           and re.match(rf'{re.escape(known)}_{prefix}\d+_', f))
            if users:
                raise ValueError(f'other applications use the slug "{known}" ({", ".join(users)}); '
                                 f'changing it would split "{company}" across two slugs')
            slug = args.slug.strip().lower()
            registry_write = lambda: company_slug.replace(repo_root, cfg, company, slug)
        else:
            # The registry decides the slug; a new company with no --slug stops here.
            slug, is_new = company_slug.choose(repo_root, cfg, company, args.slug)
            if is_new:
                registry_write = lambda: company_slug.record(repo_root, cfg, company, slug)
        target = os.path.join(os.path.dirname(folder), slug + name[at:])
        if target != folder and os.path.exists(target):
            raise FileExistsError(f'a folder already exists at {target}')

    # All checks passed: update the registry, write, then rename.
    if registry_write:
        registry_write()
    _util.write(log_path, log)
    if research is not None:
        _util.write(research_path, research)
    _util.write(jd_path, jd)
    if target != folder:
        os.rename(folder, target)
    print(target)


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses the subcommand and its arguments, loads config, runs the subcommand,
# and reports any failure to stderr with a non-zero exit so the calling skill
# halts per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='role-intake artifact assembler')
    sub = parser.add_subparsers(dest='command', required=True)

    p_folder = sub.add_parser('folder', help='Phase 4: claim the next APP-NNN and create its folder; '
                                             'prints the folder path, the APP-NNN, then the slug')
    p_folder.add_argument('--company', required=True, help='the confirmed company name')
    p_folder.add_argument('--slug', default=None,
                          help='only for a company with no recorded slug; recorded for reuse')
    p_folder.set_defaults(func=cmd_folder)

    p_ingest = sub.add_parser('ingest', help='Phase 5: write JD + comms into the application folder')
    p_ingest.add_argument('--folder', required=True, help='the application folder printed by the folder step')
    p_ingest.add_argument('--jd-text-file', required=True,
                          help='path to a file holding the extracted JD text')
    p_ingest.add_argument('--comms-text-file', default=None,
                          help='path to a file holding the extracted comms text (optional)')
    p_ingest.add_argument('--title', required=True,
                          help='confirmed title; written as the jd.md Role header line')
    p_ingest.add_argument('--company', required=True,
                          help='confirmed company; written as the jd.md Company header line')
    p_ingest.set_defaults(func=cmd_ingest)

    p_init = sub.add_parser('init', help='Phase 6: write initial session log (run after ingest); '
                                         'the APP-NNN and month come from the folder name')
    p_init.add_argument('--folder', required=True, help='the application folder')
    p_init.add_argument('--company', required=True)
    p_init.add_argument('--role', required=True)
    # Level and industry are decided and written by the role-classify skill;
    # init writes them as pending if not supplied.
    p_init.add_argument('--level', default=None)
    p_init.add_argument('--industry', default=None)
    p_init.add_argument('--start-date', required=True, help='YYYY-MM-DD')
    p_init.add_argument('--jd-source', required=True,
                        help='where the JD came from: URL, original file path, or "pasted"')
    p_init.add_argument('--comms-source', default=None,
                        help='where the messages came from: URL, original file path, or "pasted"; omit if no comms')
    p_init.add_argument('--replace', action='store_true',
                        help='rewrite an existing session log; refused once research or a later section exists')
    p_init.set_defaults(func=cmd_init)

    p_rel = sub.add_parser('relabel', help='correct company and/or title, keeping the APP-NNN')
    p_rel.add_argument('--folder', required=True, help='the application folder')
    p_rel.add_argument('--company', default=None)
    p_rel.add_argument('--role', default=None)
    p_rel.add_argument('--slug', default=None,
                       help='a new company\'s slug, or a changed slug for this company; refused while '
                            'another application uses the old one')
    p_rel.set_defaults(func=cmd_relabel)

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
