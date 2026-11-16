#!/usr/bin/env python3
"""
cv_rules_slice.py - print the part of a CV rules file a drafting step needs

The CV rules live in rules/cv/ (cv-structure, cv-sections, cv-section-content,
cv-writing). Each '## ' section is headed '## <KEY>: <name>', where KEY names
the drafting step that reads it, and ALL marks a section every drafting step
reads. A step that writes the summary should not load the rules for
Professional Experience, so this prints the file's opening text, the ALL
sections, and only the requested steps' sections.

Keys here are CV drafting steps (DRAFTING_STEPS below). ALL means every
drafting step. A heading with no key or an unknown key is an error (see
_shared_slicer.py), so a forgotten key fails at the first read instead of
quietly sending a section to every step.

Without --key the whole file prints.

Author    : Jason Delosh
Created   : 2026-11-16
Project   : career
Usage     : python scripts/cv_rules_slice.py cv-structure --key SUM
            python scripts/cv_rules_slice.py cv-writing --key EXP --key PROJ
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
# The CV drafting steps a rules section can belong to. Add a step here when the
# cv-targeted skill gains one; a key not listed here fails the check.
# ---------------------------------------------------------------------------

SHARED_KEY = 'ALL'      # sections every drafting step reads
DRAFTING_STEPS = {
    'PLAN': 'plan step: chooses the content and records it in drafting_plan.md',
    'SUM':  'writes the Professional Summary',
    'COMP': 'writes Core Competencies',
    'EXP':  'writes Professional Experience and Earlier Professional Roles',
    'PROJ': 'writes Independent Projects',
    'CRED': 'writes the header and the credential sections',
}


# ---------------------------------------------------------------------------
# Loading and slicing
# ---------------------------------------------------------------------------

def load(repo_root, cfg, name):
    """Return the text of one rules file in the CV rules folder."""
    path = os.path.join(repo_root, cfg['paths']['cv_rules'], f'{name}.md')
    if not os.path.exists(path):
        raise ValueError(f'no rules file at {path}')
    return _util.read(path)


def check(text):
    """Raise ValueError if any heading has no key or an unknown key."""
    _shared_slicer.check_keys(text, DRAFTING_STEPS, SHARED_KEY)


def slice_steps(text, wanted):
    """Return the opening, the ALL sections, and each wanted step's sections."""
    return _shared_slicer.slice_keys(text, wanted, DRAFTING_STEPS, SHARED_KEY)


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, print the requested slice."""
    parser = argparse.ArgumentParser(
        description='print the part of a CV rules file a drafting step needs')
    parser.add_argument('name', help='rules file name without .md, e.g. cv-structure')
    parser.add_argument('--key', dest='keys', action='append',
                        help=f"drafting step key ({', '.join(DRAFTING_STEPS)}); repeatable; omit to print the whole file")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        text = load(repo_root, cfg, args.name)
        sys.stdout.write(text if not args.keys else slice_steps(text, args.keys))
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
