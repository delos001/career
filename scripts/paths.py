#!/usr/bin/env python3
"""
paths.py - print a repo location resolved from config.yaml

Skills used to spell out folder paths in their instructions
('personal/applications/...', 'personal/profile/...') and find an application's
folder by hand. That breaks silently if the folders move, and the hand lookup
is a step the model can get wrong. This script does the lookup, so a skill
says 'run paths.py app <APP-NNN>' and holds no path of its own (GitHub #22).

  app <APP-NNN>  the application folder for that ID. Folders are named
                 <slug>_<APP-NNN>_<YYYY-MM> (config naming.application_stem);
                 an ID matching no folder, or more than one, is an error.
  profile        the profile folder (inventory, narratives, positioning,
                 user-info, staging file).

Paths follow CAREER_FIXTURE like every other script, so tests resolve into the
fixture corpus.

Author    : Jason Delosh
Created   : 2026-11-05
Project   : career
Usage     : python scripts/paths.py app APP-027
            python scripts/paths.py profile
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config


def app_folder(repo_root, cfg, app_id):
    """Return the one application folder whose name carries app_id."""
    applications = os.path.join(repo_root, cfg['paths']['applications'])
    prefix = re.escape(cfg['naming']['app_id_prefix'])
    if not re.fullmatch(prefix + r'\d+', app_id):
        raise ValueError(f'not an application ID: {app_id!r}')
    # The ID sits between underscores in the folder name, so APP-02 cannot match APP-027.
    token = f'_{app_id}_'
    matches = sorted(name for name in os.listdir(applications)
                     if token in name and os.path.isdir(os.path.join(applications, name)))
    if not matches:
        raise ValueError(f'no application folder for {app_id} under {applications}')
    if len(matches) > 1:
        raise ValueError(f'{app_id} matches more than one folder: {", ".join(matches)}')
    return os.path.join(applications, matches[0])


def main():
    parser = argparse.ArgumentParser(description='Print a repo location resolved from config.yaml.')
    sub = parser.add_subparsers(dest='what', required=True)
    p_app = sub.add_parser('app', help='the application folder for an APP-NNN')
    p_app.add_argument('app_id', help='e.g. APP-027')
    sub.add_parser('profile', help='the profile folder')
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    try:
        repo_root, cfg = _config.load()
        if args.what == 'app':
            print(app_folder(repo_root, cfg, args.app_id))
        else:
            print(os.path.join(repo_root, cfg['paths']['profile']))
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
