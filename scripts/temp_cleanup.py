#!/usr/bin/env python3
"""
temp_cleanup.py - clear per-application run scratch from the gitignored temp/ dir

The retrieval skill writes ~28 working files per application run into temp/
(scoring payloads, inventory chunks, per-narrative payloads, per-agent score
outputs, merged scores, the axis-classification JSON, and the session-log
staging file). No skill cleans up after itself, so these accumulate run over
run. This script is the single standalone cleanup tool that covers them all,
so no per-skill teardown step is needed.

Safety model - allowlist, not denylist. The script only ever considers files
whose name matches retrieval's run-scratch signature (see _is_run_scratch). The
reference material that also lives in temp/ (spec docs, example .docx, probe
scripts) and the subdirectories (support/, industry-builder-run/) never match,
so they are safe by construction - including reference files added in future.
The script also touches top-level files only; it never recurses into or removes
subdirectories.

Dry-run by default: a plain run previews what would be deleted (names, count,
total size) and removes nothing. Pass --apply to actually delete.

Scope is one of:
  --app-id APP-NNN   only that application's scratch (files containing APP-NNN)
  --all              every application's run scratch

Author  : Jason Delosh
Created : 2026-06-03
Project : career
Usage   : python scripts/temp_cleanup.py (--app-id APP-NNN | --all) [--apply]
Depends : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

from _config import load


# ---------------------------------------------------------------------------
# Scratch-file recognition
# ---------------------------------------------------------------------------

# A retrieval run-scratch filename matches at least one of:
#   _APP-NNN_  or  _APP-NNN.   -> any per-application payload/chunk/score file
#                                 (the APP-NNN token is unique per application and
#                                 never appears in reference material)
#   *_jd_axes.json             -> axis-classification file (spec form may omit the
#                                 APP-NNN token)
#   *_retrieval_section.md     -> session-log staging file (likewise)
_APP_TOKEN = re.compile(r'_APP-\d+[_.]')


def _is_run_scratch(name):
    """True if a top-level temp/ filename is retrieval run scratch (the --all set)."""
    return bool(
        _APP_TOKEN.search(name)
        or name.endswith('_jd_axes.json')
        or name.endswith('_retrieval_section.md')
    )


def _matches_scope(name, app_id):
    """True if name is in scope for the requested cleanup.

    --all (app_id is None): any run-scratch file.
    --app-id APP-NNN       : run-scratch files carrying that exact APP-NNN token.
    """
    if not _is_run_scratch(name):
        return False
    if app_id is None:
        return True
    return app_id in name


# ---------------------------------------------------------------------------
# Cleanup logic
# ---------------------------------------------------------------------------

def collect(temp_dir, app_id):
    """Return a sorted list of absolute paths of top-level scratch files in scope."""
    matches = []
    for entry in os.scandir(temp_dir):
        # Top-level files only; never recurse into or remove subdirectories.
        if not entry.is_file():
            continue
        if _matches_scope(entry.name, app_id):
            matches.append(entry.path)
    return sorted(matches)


def _human_size(num_bytes):
    """Format a byte count as a short human-readable string."""
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f'{size:.0f} {unit}' if unit == 'B' else f'{size:.1f} {unit}'
        size /= 1024


def run(temp_dir, app_id, apply):
    """Preview (default) or delete (--apply) the in-scope scratch files."""
    scope_label = f'application {app_id}' if app_id else 'all applications'
    paths = collect(temp_dir, app_id)

    if not paths:
        print(f'No run-scratch files found for {scope_label} in {temp_dir}.')
        return

    total = sum(os.path.getsize(p) for p in paths)
    verb = 'Deleting' if apply else 'Would delete'
    print(f'{verb} {len(paths)} run-scratch file(s) for {scope_label} '
          f'({_human_size(total)}):')
    for p in paths:
        print(f'  {os.path.basename(p)}')

    if not apply:
        print('\nDry run - nothing deleted. Re-run with --apply to delete.')
        return

    for p in paths:
        os.remove(p)
    print(f'\nDeleted {len(paths)} file(s).')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='clear per-application run scratch from the gitignored temp/ directory'
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--app-id', help='clean one application\'s scratch (e.g. APP-006)')
    scope.add_argument('--all', action='store_true',
                       help='clean every application\'s run scratch')
    parser.add_argument('--apply', action='store_true',
                        help='actually delete (default: dry-run preview only)')
    args = parser.parse_args()

    # Resolve the temp dir to an absolute path from config, so the script is
    # independent of the current working directory.
    repo_root, config = load()
    temp_dir = os.path.join(repo_root, config['paths']['temp'])

    if not os.path.isdir(temp_dir):
        print(f'Error: temp directory not found: {temp_dir}', file=sys.stderr)
        sys.exit(1)

    try:
        run(temp_dir, args.app_id, args.apply)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
