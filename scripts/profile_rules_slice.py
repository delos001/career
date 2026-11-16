#!/usr/bin/env python3
"""
profile_rules_slice.py - print the part of a profile writing-rules file a task needs

The writing rules for the profile documents live in rules/profile/, one file per
document. A file that covers several entry types gives each type its own
'## <KEY>: <name>' section (e.g. '## EX: Experience entries'), and the rules
every entry type shares sit under '## ALL: <name>'. Writing one EX entry should
not load the rules for ED, PR, and the rest, so this prints the file's opening
text, the ALL sections, and only the requested type's section.

Keys here are inventory entry types: the ID prefixes the inventory template
defines (read at run time), plus LIST for the list sections. ALL means every
entry type. A heading with no key or an unknown key is an error (see
_shared_slicer.py).

Without --type the whole file prints, which is the case for a file with no
keyed sections (routing, staging). Asking for a type the file has no section
for is an error, never a silent fall back to the shared rules alone: a missing
section means the writer would be guessing.

This is the one way skills and the review agent read these files, so each rule
is written once and read from here.

Author    : Jason Delosh
Created   : 2026-10-22 (as rules_slice.py; split by reader 2026-11-16)
Project   : career
Usage     : python scripts/profile_rules_slice.py inventory-writing --type EX
            python scripts/profile_rules_slice.py routing
Depends   : pyyaml (via _config)
"""

import argparse
import os
import sys

import _config
import _shared_slicer
import _util
from inventory_model import document


# ---------------------------------------------------------------------------
# Key vocabulary
# ---------------------------------------------------------------------------

SHARED_KEY = 'ALL'      # sections every entry type reads
LIST_KEY = 'LIST'       # the inventory's list sections, which have no ID prefix


def valid_keys(repo_root, cfg):
    """Return the entry-type keys: the template's ID prefixes plus LIST."""
    path = os.path.join(repo_root, cfg['paths']['templates'], cfg['filenames']['inventory_template'])
    return set(document.parse_template(_util.read(path))) | {LIST_KEY}


# ---------------------------------------------------------------------------
# Loading and slicing
# ---------------------------------------------------------------------------

def load(repo_root, cfg, name):
    """Return the text of one rules file in the profile rules folder."""
    path = os.path.join(repo_root, cfg['paths']['profile_rules'], f'{name}.md')
    if not os.path.exists(path):
        raise ValueError(f'no rules file at {path}')
    return _util.read(path)


def type_keys(text):
    """Return the entry-type keys a rules file has sections for."""
    return [k for k in _shared_slicer.keys(text) if k != SHARED_KEY]


def slice_types(text, wanted, repo_root=None, cfg=None):
    """Return the opening, the ALL sections, and each wanted type's section."""
    if cfg is None:
        repo_root, cfg = _config.load()
    return _shared_slicer.slice_keys(text, wanted, valid_keys(repo_root, cfg), SHARED_KEY)


def slice_text(text, type_key=None):
    """Return the whole file, or the opening, ALL sections, and one type."""
    return text if type_key is None else slice_types(text, [type_key])


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, print the requested slice."""
    parser = argparse.ArgumentParser(
        description='print the part of a profile writing-rules file a task needs')
    parser.add_argument('name', help='rules file name without .md, e.g. inventory-writing')
    parser.add_argument('--type', dest='type_key',
                        help='entry type key, e.g. EX; omit to print the whole file')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        sys.stdout.write(slice_text(load(repo_root, cfg, args.name), args.type_key))
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
