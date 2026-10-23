#!/usr/bin/env python3
"""
rules_slice.py - print the part of a profile writing-rules file a task needs

The writing rules for the profile documents live in rules/profile/, one file per
document. A file that covers several entry types gives each type its own
'## <KEY>: <name>' section (e.g. '## EX: Experience entries'); every '## '
section without a key applies to all types. Writing one EX entry should not load
the rules for ED, PR, and the rest, so this prints the file's opening text, the
shared sections, and only the requested type's section.

Without --type the whole file prints, which is the case for a file with no
typed sections (routing, staging). Asking for a type the file has no section
for is an error, never a silent fall back to the shared rules alone: a missing
section means the writer would be guessing.

This is the one way skills and the review agent read these files, so each rule
is written once and read from here.

Author    : Jason Delosh
Created   : 2026-10-22
Project   : career
Usage     : python scripts/rules_slice.py inventory-writing --type EX
            python scripts/rules_slice.py routing
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Section parsing
# A file is its opening text plus '## ' sections. A section heading of the form
# '## KEY: name', where KEY is upper-case letters, belongs to that type; any
# other '## ' heading is shared.
# ---------------------------------------------------------------------------

# Regex: a typed section heading, capturing its key.
_TYPED_RE = re.compile(r'^## ([A-Z]+): ')


def sections(text):
    """Return (opening, [(key or None, section text)]) for a rules file."""
    # Splitting before each '## ' line leaves the opening text first, empty
    # when the file starts with a section.
    opening, *body = re.split(r'(?m)^(?=## )', text)
    out = []
    for part in body:
        m = _TYPED_RE.match(part)
        out.append((m.group(1) if m else None, part))
    return opening, out


def type_keys(text):
    """Return the type keys a rules file has sections for."""
    return [key for key, _ in sections(text)[1] if key]


def slice_types(text, wanted):
    """Return the opening, the shared sections, and each wanted type's section.

    The shared rules appear once however many types are asked for, so a review
    of several entry types reads them once.
    """
    opening, parts = sections(text)
    missing = [key for key in wanted if key not in type_keys(text)]
    if missing:
        raise ValueError(
            f"no section for {', '.join(missing)}; this file has sections for "
            f"{', '.join(type_keys(text)) or 'no types'}")
    kept = [part for key, part in parts if key is None or key in wanted]
    return (opening + ''.join(kept)).rstrip() + '\n'


def slice_text(text, type_key=None):
    """Return the whole file, or the opening, shared sections, and one type."""
    return text if type_key is None else slice_types(text, [type_key])


def load(repo_root, cfg, name):
    """Return the text of one rules file in the profile rules folder."""
    path = os.path.join(repo_root, cfg['paths']['profile_rules'], f'{name}.md')
    if not os.path.exists(path):
        raise ValueError(f'no rules file at {path}')
    return _util.read(path)


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
