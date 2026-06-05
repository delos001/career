#!/usr/bin/env python3
"""
scratch_cleanup.py - delete a single application's run-scratch folder

Every pipeline skill (role-intake, retrieval, gap-analysis, cv-targeted,
cv-render) writes its working files into a per-application scratch subfolder,
<app-folder>/<scratch_subdir>/ (scratch_subdir is config-driven, default
"scratch"). Scratch is intentionally kept for the life of the application so an
interrupted skill can resume from what it already wrote; it is removed in one
shot when the application reaches a terminal state - the user declines to pursue
(gap-analysis) or the application is closed out (close-application skill). Both
triggers call this one script, so the cleanup interface is identical everywhere.

This is the single, uniform cleanup call, with two scopes:
    python scripts/scratch_cleanup.py --app-folder <abs path> [--apply]   # one application's scratch
    python scripts/scratch_cleanup.py --builder [--apply]                 # axis-builder scratch (rules/scratch/)
Application scratch is kept until the application is declined or closed;
axis-builder scratch is removed at the end of each build.

Dry-run by default: a plain run previews the scratch folder's contents (file
count, total size) and removes nothing. Pass --apply to delete the folder.

Safety: the script refuses any --app-folder that is not a direct child of the
configured applications/ directory, so it can never wipe a path outside an
application folder. It only ever removes the scratch subfolder, never the
application folder or its permanent artifacts (jd.md, research.md, retrieval.md,
gap_analysis.md, cv_content.md, ...).

Author  : Jason Delosh
Created : 2026-06-05
Project : career
Usage   : python scripts/scratch_cleanup.py (--app-folder <path> | --builder) [--apply]
Depends : pyyaml (via _config)
"""

import argparse
import os
import shutil
import sys

from _config import load


# ---------------------------------------------------------------------------
# Path resolution and safety
# ---------------------------------------------------------------------------

def _resolve_scratch_dir(repo_root, config, app_folder):
    """Validate app_folder and return the absolute path of its scratch subfolder.

    Refuses (raises ValueError) any app_folder that is not a direct child of the
    configured applications/ directory, so the deletion target can never escape
    an application folder.
    """
    applications_root = os.path.abspath(
        os.path.join(repo_root, config['paths']['applications'])
    )
    app_abs = os.path.abspath(app_folder)

    # Must sit directly under applications/ - guards against a stray path
    # wiping something outside an application folder.
    if os.path.dirname(app_abs) != applications_root:
        raise ValueError(
            f'--app-folder must be a direct child of {applications_root}; got {app_abs}'
        )

    scratch_subdir = config['filenames']['scratch_subdir']
    return os.path.join(app_abs, scratch_subdir)


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def _human_size(num_bytes):
    """Format a byte count as a short human-readable string."""
    size = float(num_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f'{size:.0f} {unit}' if unit == 'B' else f'{size:.1f} {unit}'
        size /= 1024


def _scratch_contents(scratch_dir):
    """Return (file_count, total_bytes) across the scratch tree."""
    count = 0
    total = 0
    for root, _dirs, files in os.walk(scratch_dir):
        for name in files:
            count += 1
            total += os.path.getsize(os.path.join(root, name))
    return count, total


# ---------------------------------------------------------------------------
# Cleanup logic
# ---------------------------------------------------------------------------

def run(scratch_dir, apply):
    """Preview (default) or delete (--apply) the scratch folder."""
    if not os.path.isdir(scratch_dir):
        print(f'No scratch folder to clean: {scratch_dir} does not exist.')
        return

    count, total = _scratch_contents(scratch_dir)
    verb = 'Deleting' if apply else 'Would delete'
    print(f'{verb} scratch folder {scratch_dir} ({count} file(s), {_human_size(total)}).')

    if not apply:
        print('\nDry run - nothing deleted. Re-run with --apply to delete.')
        return

    shutil.rmtree(scratch_dir)
    print('Deleted.')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="delete a run-scratch folder: an application's <app-folder>/scratch/, or the axis-builder rules/scratch/"
    )
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--app-folder',
                       help='absolute path to the application folder whose scratch to clean (pipeline skills)')
    scope.add_argument('--builder', action='store_true',
                       help='clean the axis-builder scratch (rules/scratch/)')
    parser.add_argument('--apply', action='store_true',
                        help='actually delete (default: dry-run preview only)')
    args = parser.parse_args()

    repo_root, config = load()

    try:
        if args.builder:
            # Fixed path under the repo, safe by construction.
            scratch_dir = os.path.join(
                repo_root, config['paths']['rules'], config['filenames']['scratch_subdir']
            )
        else:
            scratch_dir = _resolve_scratch_dir(repo_root, config, args.app_folder)
        run(scratch_dir, args.apply)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
