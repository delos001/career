#!/usr/bin/env python3
"""
company_slug.py - company-to-slug registry for cross-application slug reuse

Keeps one preferred folder slug per company so a repeat application for the same
company reuses the same slug (e.g. "thermofisher") instead of the user being
asked again and the slug drifting ("tfs" vs "thermofisher"). role-intake uses
it through assemble.py (folder in Phase 3, relabel for a corrected company),
which imports choose() and record(); the subcommands below remain for direct use.

The registry lives at <personal>/<company_slugs_file> (both from
config.yaml), at the root of the private nested personal/ repo, as YAML keyed
by slug:

    thermofisher:
      name: Thermo Fisher Scientific

Three subcommands:
  lookup    Print the slug mapped to a company name (case-insensitive, trimmed),
            or nothing if the company is not yet recorded. Never errors on a
            miss - a miss just means "ask the user".
  record    Add or update a company -> slug mapping. Warns (non-fatal) on a
            name/slug collision so drift is visible.
  backfill  Seed the registry from existing application folders: each folder name
            carries the slug, and its session_log.md carries the full company
            name. Idempotent; existing mappings are left in place.

Nothing repo-dependent is hardcoded here: the registry location and the
applications-folder location come from config.yaml via _config.

Author    : Jason Delosh
Created   : 2026-06-23
Project   : career
Usage     : python scripts/company_slug.py lookup   --company "Thermo Fisher Scientific"
            python scripts/company_slug.py record   --company "Thermo Fisher Scientific" --slug thermofisher
            python scripts/company_slug.py backfill
Depends   : pyyaml (via _config); _util
"""

import argparse
import os
import re
import sys

import yaml

import _config
import _util


# ---------------------------------------------------------------------------
# Registry path + load/save
# The file is YAML keyed by slug with a single `name` field per entry. A header
# comment is written on every save (yaml.safe_dump drops comments), so the file
# stays self-describing when opened by hand.
# ---------------------------------------------------------------------------

_HEADER = (
    '# Company -> preferred folder slug registry.\n'
    '#\n'
    '# One entry per company, keyed by the slug used in application folder names\n'
    '# (<slug>_APP-NNN_YYYY-MM). role-intake Phase 3 looks a company up here before\n'
    '# asking for a slug, so a repeat application reuses the same slug. Maintained\n'
    '# by scripts/company_slug.py; edit through the script rather than by hand.\n'
)


def _registry_path(repo_root, cfg):
    return os.path.join(repo_root, cfg['paths']['personal'],
                        cfg['filenames']['company_slugs_file'])


def _load(path):
    """Return the registry as a dict {slug: {'name': ...}}; empty if absent."""
    if not os.path.exists(path):
        return {}
    data = yaml.safe_load(_util.read(path))
    # An empty or comment-only file parses to None.
    return data or {}


def _save(path, data):
    """Write the registry with its header comment, slugs in stable order."""
    body = yaml.safe_dump(data, sort_keys=True, allow_unicode=True,
                          default_flow_style=False)
    _util.write(path, _HEADER + '\n' + body)


def _norm(name):
    """Normalize a company name for comparison: trimmed, case-folded."""
    return (name or '').strip().casefold()


# ---------------------------------------------------------------------------
# Lookup and record, importable
# assemble.py (folder, relabel) calls these directly, so the registry rules have
# one implementation; the subcommands below are thin wrappers.
# ---------------------------------------------------------------------------

def lookup(repo_root, cfg, company):
    """Return the slug recorded for a company, or None if it is new."""
    target = _norm(company)
    for slug, entry in _load(_registry_path(repo_root, cfg)).items():
        if _norm(entry.get('name')) == target:
            return slug
    return None


def record(repo_root, cfg, company, slug):
    """Add or update a company -> slug mapping; return the stored slug.

    Collisions (same slug pointing at a different company, or the company already
    under a different slug) are warned to stderr but not fatal - the latest record
    wins, and the warning surfaces drift for a human to reconcile.
    """
    path = _registry_path(repo_root, cfg)
    data = _load(path)
    slug = slug.strip().lower()
    company = company.strip()

    existing = data.get(slug)
    if existing and _norm(existing.get('name')) != _norm(company):
        print(f'WARNING: slug "{slug}" already maps to "{existing.get("name")}"; '
              f'overwriting with "{company}".', file=sys.stderr)
    for other_slug, entry in data.items():
        if other_slug != slug and _norm(entry.get('name')) == _norm(company):
            print(f'WARNING: company "{company}" already maps to slug '
                  f'"{other_slug}"; now also recording slug "{slug}".',
                  file=sys.stderr)

    data[slug] = {'name': company}
    _save(path, data)
    return slug


def replace(repo_root, cfg, company, slug):
    """Make slug the company's only recorded slug; return it.

    Drops every entry naming the company, then records the new one. Used when
    the user changes an application's slug; the caller checks first that no
    other application folder still uses the old slug.
    """
    path = _registry_path(repo_root, cfg)
    data = {s: e for s, e in _load(path).items() if _norm(e.get('name')) != _norm(company)}
    _save(path, data)
    return record(repo_root, cfg, company, slug)


def choose(repo_root, cfg, company, slug=None):
    """Return (slug, is_new) for a company; write nothing.

    A recorded company reuses its slug; passing a different one is refused so a
    second slug never appears by accident. A new company needs a slug; without
    one this raises. The caller records a new slug with record() once its own
    checks pass, so a refused run leaves the registry untouched.
    """
    known = lookup(repo_root, cfg, company)
    if known:
        if slug and slug.strip().lower() != known:
            raise ValueError(f'"{company}" already uses the slug "{known}"; '
                             f'drop --slug to reuse it')
        return known, False
    if not slug:
        raise ValueError(f'"{company}" has no recorded slug; ask the user for a short '
                         f'lowercase slug and re-run with --slug')
    return slug.strip().lower(), True


# ---------------------------------------------------------------------------
# Subcommand: lookup
# Print the slug mapped to a company name, or nothing on a miss. A miss is a
# normal outcome (the company is new), not a failure, so exit stays 0.
# ---------------------------------------------------------------------------

def cmd_lookup(args, repo_root, cfg):
    slug = lookup(repo_root, cfg, args.company)
    if slug:
        print(slug)


# ---------------------------------------------------------------------------
# Subcommand: record
# ---------------------------------------------------------------------------

def cmd_record(args, repo_root, cfg):
    print(record(repo_root, cfg, args.company, args.slug))


# ---------------------------------------------------------------------------
# Subcommand: backfill
# Seed the registry from existing application folders. Each folder is named
# <slug>_<app_id>_<ym>; the slug is the leading segment, and the full company
# name is the '- Company:' line in that folder's session log. Existing registry
# entries are kept; only companies not already present are added.
# ---------------------------------------------------------------------------

def cmd_backfill(args, repo_root, cfg):
    path = _registry_path(repo_root, cfg)
    data = _load(path)

    apps_dir = os.path.join(repo_root, cfg['paths']['applications'])
    session_log_name = cfg['filenames']['session_log_file']
    app_id_prefix = cfg['naming']['app_id_prefix']
    # Folder name is "{slug}_{app_id}_{ym}"; the slug is everything before the
    # "_<app_id_prefix>" segment (slugs may themselves contain underscores).
    stem_pat = re.compile(r'^(.+?)_' + re.escape(app_id_prefix) + r'\d+_')

    added = 0
    known_companies = {_norm(e.get('name')) for e in data.values()}
    if not os.path.isdir(apps_dir):
        print('0 added (no applications folder yet)')
        return

    for folder in sorted(os.listdir(apps_dir)):
        folder_path = os.path.join(apps_dir, folder)
        if not os.path.isdir(folder_path):
            continue
        m = stem_pat.match(folder)
        if not m:
            continue
        slug = m.group(1).lower()
        log_path = os.path.join(folder_path, session_log_name)
        if not os.path.exists(log_path):
            continue
        cm = re.search(r'(?mi)^- Company:[ \t]*(.+?)[ \t]*$', _util.read(log_path))
        if not cm:
            continue
        company = cm.group(1).strip()
        if not company or company == '_(pending)_':
            continue
        # Keep existing entries: skip if this slug is already mapped or this
        # company is already known under some slug. The first folder seen for a
        # slug wins (folders are iterated in sorted order), so a later folder
        # with a drifted company name for the same slug does not overwrite it.
        if slug in data or _norm(company) in known_companies:
            continue
        data[slug] = {'name': company}
        known_companies.add(_norm(company))
        added += 1

    _save(path, data)
    print(f'{added} added; {len(data)} total')


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses the subcommand, loads config, runs it, and reports any failure to
# stderr with a non-zero exit so the calling skill halts per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='company-to-slug registry')
    sub = parser.add_subparsers(dest='command', required=True)

    p_lookup = sub.add_parser('lookup', help='print the slug for a company, or nothing on a miss')
    p_lookup.add_argument('--company', required=True)
    p_lookup.set_defaults(func=cmd_lookup)

    p_record = sub.add_parser('record', help='add or update a company -> slug mapping')
    p_record.add_argument('--company', required=True)
    p_record.add_argument('--slug', required=True)
    p_record.set_defaults(func=cmd_record)

    p_backfill = sub.add_parser('backfill', help='seed the registry from existing application folders')
    p_backfill.set_defaults(func=cmd_backfill)

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
