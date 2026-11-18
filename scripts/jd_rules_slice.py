#!/usr/bin/env python3
"""
jd_rules_slice.py - print the part of the JD processing rules a step needs

The rules for each step that works on a job description live in one file,
rules/jd-processing.md (config filenames.jd_rules_file). Each '## ' section is
headed '## <KEY>: <name>', where KEY names the step that reads it, and ALL
marks a section every step reads. A step reads only its own sections, so the
splitter never loads the rules for kinds or ranking.

Keys are the steps listed in STEPS below. A heading with no key or an unknown
key is an error (see _shared_slicer.py), so a forgotten key fails at the first
read instead of quietly sending a section to the wrong step. A known key with
no section in the file is also an error.

Without --key the whole file prints. With --out the slice is written to that
file instead of printed (dispatch_prompt.py uses this to hand a subagent its
rules by path).

Author    : Jason Delosh
Created   : 2026-11-18
Project   : career
Usage     : python scripts/jd_rules_slice.py --key SPLIT
            python scripts/jd_rules_slice.py --key SPLIT --out <path>
Depends   : pyyaml (via _config)
"""

import argparse
import os
import sys

import _config
import _shared_slicer
import _util


# ---------------------------------------------------------------------------
# Key vocabulary
# The steps a rules section can belong to. Add a step here when one gains a
# section in the rules file; a key not listed here fails the check.
# ---------------------------------------------------------------------------

SHARED_KEY = 'ALL'      # sections every step reads
STEPS = {
    'SPLIT': 'splits each unit of jd_sentences.md into parts (jd-splitter, role-extract Phase 1)',
    'KINDS': 'labels each jd_needs.md row with a kind (jd-kind-labeler, role-extract Phase 3; also read '
             'by jd-needs-ranker, qc-role-extract and requirement_kinds.load_kinds)',
    'RANK':  'describes the job, groups rows into needs and ranks them (jd-needs-ranker, role-extract '
             'Phase 4; also read by qc-role-extract)',
}


# ---------------------------------------------------------------------------
# Loading and slicing
# ---------------------------------------------------------------------------

def load(repo_root, cfg):
    """Return the text of the JD processing rules file."""
    path = os.path.join(repo_root, cfg['paths']['rules'], cfg['filenames']['jd_rules_file'])
    if not os.path.exists(path):
        raise ValueError(f'no rules file at {path}')
    return _util.read(path)


def slice_steps(text, wanted):
    """Return the opening, the ALL sections, and each wanted step's sections."""
    return _shared_slicer.slice_keys(text, wanted, STEPS, SHARED_KEY)


def write_slice(repo_root, cfg, wanted, out_path):
    """Write the wanted steps' slice to out_path and return the path."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    _util.write(out_path, slice_steps(load(repo_root, cfg), wanted))
    return out_path


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, print or write the requested slice."""
    parser = argparse.ArgumentParser(description='print the part of the JD processing rules a step needs')
    parser.add_argument('--key', dest='keys', action='append',
                        help=f"step key ({', '.join(STEPS)}); repeatable; omit to print the whole file")
    parser.add_argument('--out', default=None, help='write the slice to this file instead of printing it')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        if args.out:
            if not args.keys:
                raise ValueError('--out needs at least one --key')
            print(write_slice(repo_root, cfg, args.keys, os.path.abspath(args.out)))
        else:
            text = load(repo_root, cfg)
            sys.stdout.write(text if not args.keys else slice_steps(text, args.keys))
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
