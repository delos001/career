#!/usr/bin/env python3
"""
introduce.py - skill introduction printer

Prints the user-facing guidance shown at the start (Phase 0) of a skill, so the
user knows what the skill does and what to have ready before starting. The
guidance text lives in the introductions file (named in config.yaml), keyed by
skill name; this script's only job is to find the right entry and print it.

One introduce.py serves every skill - the skill name is passed in as an
argument, so there is no separate script per skill.

Author    : Jason Delosh
Created   : 2026-05-14
Project   : career
Usage     : python scripts/display/introduce.py <skill-name>
Depends   : pyyaml
"""

import os
import sys

# This script lives in scripts/display/. Add scripts/ to the import path so it
# can import the shared _config helper, which sits one folder up.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

import _config


# ---------------------------------------------------------------------------
# Reading one skill's introduction out of the introductions file
# Opens the introductions file (its name comes from config.yaml; it sits next
# to this script), finds the entry matching the requested skill, and returns
# that skill's introduction text. If the skill has no entry, it stops with a
# clear error rather than returning nothing.
# ---------------------------------------------------------------------------

def introduce(skill_name):
    """Return the introduction text for the given skill name.

    Opens the introductions file, looks for an entry whose key matches
    skill_name, and returns that entry's text. Raises KeyError if the skill has
    no entry.
    """
    _, cfg = _config.load()
    # The introductions file sits in the same folder as this script.
    intro_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              cfg['filenames']['introductions'])
    with open(intro_path, 'r', encoding='utf-8') as f:
        intros = yaml.safe_load(f)          # parse the YAML file into a dictionary
    if skill_name not in intros:
        raise KeyError(f'no introduction entry for skill: {skill_name}')
    return intros[skill_name].strip()


# ---------------------------------------------------------------------------
# Command-line entry point
# Runs when the script is called directly: checks that exactly one skill name
# was passed, fetches that skill's introduction, and prints it. Any problem
# (wrong arguments, or a skill with no entry) is reported to the error stream
# and the script exits non-zero so the calling skill knows it failed.
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # Expect exactly one argument - the skill name. Anything else is misuse.
    if len(sys.argv) != 2:
        print('Usage: python scripts/display/introduce.py <skill-name>',
              file=sys.stderr)
        sys.exit(1)
    try:
        text = introduce(sys.argv[1])
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
    # Force UTF-8 output so accented or special characters print correctly on
    # Windows, where the default console encoding is not UTF-8.
    sys.stdout.reconfigure(encoding='utf-8')
    print(text)
