#!/usr/bin/env python3
"""
app_id.py - next application ID claim

Claims the next application ID (e.g. APP-004) for a new role-intake session
and prints it. Used by the role-intake skill, Phase 3 (session init).

Every evaluated job has a folder under the applications directory, named with
the application ID embedded (e.g. PFM_APP-003_2026-05). The ID is a running
counter shared across all companies.

The folder is created several steps after the ID is drawn, so a bare max+1 over
the folders let two sessions started back to back draw the same ID (two APP-015
folders, 2026-07-14). The ID is therefore claimed before it is printed: an empty
marker file per ID is created with an exclusive create, which the OS makes
atomic, so exactly one caller wins each number. Markers are permanent, so an ID
is never reissued even if its folder is later removed. A claimed ID whose run
is abandoned is simply skipped.

The applications-folder location, the claims subfolder, and the ID scheme
(prefix, digit width) are read from config.yaml - nothing repo-dependent is
hardcoded here.

Author    : Jason Delosh
Created   : 2026-05-14
Modified  : 2026-11-05 (claim the ID atomically; GitHub #3)
Project   : career
Usage     : python scripts/app_id.py
Depends   : pyyaml (via _config)
"""

import os
import re
import sys

import _config


# ---------------------------------------------------------------------------
# Highest ID in use
# An ID is in use if an application folder carries it or a claim marker holds
# it. Folders created before claiming existed have no marker, so both are read.
# ---------------------------------------------------------------------------

def _highest_in_use(applications_dir, claims_dir, prefix):
    """Return the highest counter found in folder names and claim markers."""
    # The pattern looks for the configured ID prefix followed by one or more
    # digits, and captures just the digits (e.g. '003' in 'PFM_APP-003_2026-05').
    pattern = re.compile(re.escape(prefix) + r'(\d+)')
    highest = 0
    if os.path.isdir(applications_dir):
        for name in os.listdir(applications_dir):
            # Applications are folders; skip over any stray files.
            if not os.path.isdir(os.path.join(applications_dir, name)):
                continue
            m = pattern.search(name)
            if m:
                highest = max(highest, int(m.group(1)))
    if os.path.isdir(claims_dir):
        for name in os.listdir(claims_dir):
            m = pattern.fullmatch(name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest


# ---------------------------------------------------------------------------
# Claim
# Starts one past the highest ID in use and tries to create that ID's marker.
# O_CREAT | O_EXCL fails if the file already exists, so a concurrent caller
# that got there first makes this one move on to the next number.
# ---------------------------------------------------------------------------

def claim_app_id():
    """Claim and return the next application ID (e.g. 'APP-004').

    Returns the first ID (e.g. 'APP-001') when nothing is in use yet.
    """
    repo_root, cfg = _config.load()
    applications_dir = os.path.join(repo_root, cfg['paths']['applications'])
    claims_dir = os.path.join(applications_dir, cfg['naming']['app_id_claims_dir'])
    prefix = cfg['naming']['app_id_prefix']
    digits = cfg['naming']['app_id_digits']

    os.makedirs(claims_dir, exist_ok=True)
    counter = _highest_in_use(applications_dir, claims_dir, prefix) + 1
    while True:
        # Zero-padded to the configured digit width so the result matches the
        # ID convention (e.g. APP-004, not APP-4).
        app_id = f'{prefix}{counter:0{digits}d}'
        try:
            fd = os.open(os.path.join(claims_dir, app_id),
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            counter += 1
            continue
        os.close(fd)
        return app_id


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(claim_app_id())
