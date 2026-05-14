#!/usr/bin/env python3
"""
app_id.py - next application ID generator

Works out the next application ID (e.g. APP-004) for a new role-intake session
and prints it. Used by the role-intake skill, Phase 3 (session init).

Every evaluated job has a folder under the applications directory, named with
the application ID embedded (e.g. PFM_APP-003_2026-05). The ID is a running
counter shared across all companies. This script reads the existing folders,
finds the highest counter in use, and prints the next one. It returns the first
ID (e.g. APP-001) when no application folders exist yet.

The applications-folder location and the ID scheme (prefix, digit width) are
read from config.yaml - nothing repo-dependent is hardcoded here.

Author    : Jason Delosh
Created   : 2026-05-14
Project   : career
Usage     : python scripts/app_id.py
Depends   : pyyaml (via _config)
"""

import os
import re
import sys

import _config


# ---------------------------------------------------------------------------
# ID computation
# Scans the existing application folders, reads the counter out of each folder
# name, and returns the next number in sequence.
# ---------------------------------------------------------------------------

def next_app_id():
    """Return the next application ID by inspecting the folders that exist.

    Reads the applications directory named in config.yaml, finds the highest
    application counter currently in use, and returns the next one as a string
    (e.g. 'APP-004'). Returns the first ID (e.g. 'APP-001') if there are no
    application folders yet.
    """
    repo_root, cfg = _config.load()
    applications_dir = os.path.join(repo_root, cfg['paths']['applications'])
    prefix = cfg['naming']['app_id_prefix']
    digits = cfg['naming']['app_id_digits']

    highest = 0
    if os.path.isdir(applications_dir):
        for name in os.listdir(applications_dir):
            # Applications are folders; skip over any stray files.
            if not os.path.isdir(os.path.join(applications_dir, name)):
                continue
            # Pull the counter out of the folder name. The pattern looks for the
            # configured ID prefix followed by one or more digits, and captures
            # just the digits (e.g. the '003' in 'PFM_APP-003_2026-05').
            m = re.search(re.escape(prefix) + r'(\d+)', name)
            if m:
                highest = max(highest, int(m.group(1)))
    # Add one for the next session, zero-padded to the configured digit width
    # so the result matches the ID convention (e.g. APP-004, not APP-4).
    return f'{prefix}{highest + 1:0{digits}d}'


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(next_app_id())
