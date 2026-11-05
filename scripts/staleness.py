#!/usr/bin/env python3
"""
staleness.py - list rule files whose research is out of date

Stamped rule files (axis value files, axis registries, the CV rules) carry a
'last_researched: YYYY-MM' frontmatter field. A file is stale once that date is
at least the configured number of months old (config.yaml staleness_months,
decided at 9; design_decisions.md rule-staleness-threshold).

Before this script, the threshold lived only in prose, the one check that ran
used ~12 months, and 23 of 24 stamped files were never age-checked (GitHub #47).
A consuming skill now passes the rule files it is about to use and gets back
the stale ones, so it can offer one grouped "proceed or refresh?" choice.

Output: one line per stale file, '<path> | last researched YYYY-MM | N months',
or a single 'none stale' line. A file with no stamp is reported as such, since
its age cannot be judged. Exit 0 unless the script itself fails.

Author    : Jason Delosh
Created   : 2026-11-05
Project   : career
Usage     : python scripts/staleness.py --file <rule.md> [--file <rule.md> ...]
            python scripts/staleness.py --all      (every stamped file under rules/)
Depends   : pyyaml (via _config)
"""

import argparse
import glob
import os
import re
import sys

import _config
import _util

_STAMP_RE = re.compile(r'(?m)^last_researched:[ \t]*(\d{4})-(\d{2})[ \t]*$')


# ---------------------------------------------------------------------------
# Age arithmetic
# Whole calendar months between two YYYY-MM values; month granularity matches
# the stamp, so day-of-month never matters.
# ---------------------------------------------------------------------------

def months_old(stamp_ym, today=None):
    """Return whole months from stamp_ym (YYYY-MM) to today (YYYY-MM)."""
    today = today or _util.today_ym()
    sy, sm = (int(x) for x in stamp_ym.split('-'))
    ty, tm = (int(x) for x in today.split('-'))
    return (ty - sy) * 12 + (tm - sm)


def is_stale(stamp_ym, threshold_months, today=None):
    """True when the stamp is at least threshold_months old."""
    return months_old(stamp_ym, today) >= threshold_months


def stamp_of(path):
    """Return the file's last_researched as YYYY-MM, or None if unstamped."""
    m = _STAMP_RE.search(_util.read(path))
    return f'{m.group(1)}-{m.group(2)}' if m else None


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='List rule files whose research is out of date.')
    parser.add_argument('--file', action='append', help='a rule file to check (repeatable)')
    parser.add_argument('--all', action='store_true', help='check every stamped .md file under rules/')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        repo_root, cfg = _config.load()
        threshold = cfg['staleness_months']
        if args.all:
            files = sorted(f for f in glob.glob(os.path.join(repo_root, cfg['paths']['rules'], '**', '*.md'),
                                                recursive=True) if stamp_of(f))
        elif args.file:
            files = args.file
        else:
            parser.error('give --file or --all')
        lines = []
        for path in files:
            stamp = stamp_of(path)
            if stamp is None:
                lines.append(f'{path} | no last_researched stamp')
            elif is_stale(stamp, threshold):
                lines.append(f'{path} | last researched {stamp} | {months_old(stamp)} months')
        print('\n'.join(lines) if lines else f'none stale (threshold {threshold} months)')
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
