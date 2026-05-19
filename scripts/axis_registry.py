#!/usr/bin/env python3
"""
axis_registry.py - registry parsing and section slicing for axis-builder

Read-only operations against an axis's registry.md and value files. Three
subcommands:

  lookup  Phase 1 - inspect a single registry entry; returns state +
          value-file path as JSON. Kept for callers that only need one entry.
  list    Phase 1 - emit every registry entry for an axis as JSON, so the
          builder skill can identify the target's state AND build the
          siblings list in one call without parsing the registry itself.
  slice   Phase 4 - print the body of one '## Section' from a file-backed
          value file. Used to give the reconciler subagent just the
          Adjacency section content of each sibling, keeping its context
          cost bounded regardless of how many siblings an axis has.

Nothing repo-dependent is hardcoded; folder locations and filenames come
from config.yaml. Sibling helpers (_util, _config, axis_utils) provide the
generic operations; this script owns only registry-bullet parsing.

Author    : Jason Delosh
Created   : 2026-05-19
Project   : career
Usage     : python scripts/axis_registry.py lookup <axis> <value>
            python scripts/axis_registry.py list <axis>
            python scripts/axis_registry.py slice <axis> <value> --section <heading>
Depends   : pyyaml (via _config)
"""

import argparse
import json
import os
import re
import sys

import _config
import _util
import axis_utils


# ---------------------------------------------------------------------------
# Registry bullet parsing
# The registry is a Markdown file with a frontmatter block and a bullet list
# under a # heading. Each bullet is one of:
#   - **<value>** - <description>. File: <name>.md.
#   - **<value>** - <description>. File deferred.
#   - **<value>** - <description>. Registry-only; <reason>.
# Parse loosely so minor whitespace variation does not break lookup.
# ---------------------------------------------------------------------------

# Regex: capture an axis-registry bullet's value name (the bolded token) and
# the rest of the line. The bullet starts with '- **<value>**' on its own line.
_BULLET_RE = re.compile(
    r'^- \*\*(?P<value>[^*]+)\*\*(?P<rest>.*)$',
    re.MULTILINE,
)


def _classify_bullet(rest_of_line):
    """Decide registry state from the text after the bolded value token.

    Returns (state, value_filename_or_None). State is one of
    'file-backed', 'file-deferred', 'registry-only'. Raises ValueError on
    an unrecognised bullet so the user sees a typo in the registry rather
    than a downstream "refuse to build" with no explanation. Comparisons
    are exact; near-misses ('Files deferred', 'Registry only' without the
    hyphen, lowercase 'file deferred') all fail.
    """
    # File-backed entries name the file explicitly: 'File: <name>.md'.
    m = re.search(r'File:\s+`?([\w\-.]+\.md)`?', rest_of_line)
    if m:
        return 'file-backed', m.group(1)
    if re.search(r'File deferred', rest_of_line):
        return 'file-deferred', None
    if re.search(r'Registry-only', rest_of_line):
        return 'registry-only', None
    raise ValueError(
        'registry bullet does not match any of the three accepted shapes '
        "('File: <name>.md', 'File deferred', 'Registry-only'); "
        f'bullet rest-of-line: {rest_of_line.strip()!r}'
    )


def _find_registry_entry(registry_text, value):
    """Locate a value's bullet in the registry.

    Returns (match_object, state, value_filename) if found; (None, None, None)
    if the value is not in the registry.
    """
    for m in _BULLET_RE.finditer(registry_text):
        if m.group('value').strip() == value:
            state, value_filename = _classify_bullet(m.group('rest'))
            return m, state, value_filename
    return None, None, None


# ---------------------------------------------------------------------------
# Subcommand: lookup
# Inspect a registry entry; return state + value-file path. JSON output so
# the calling skill can parse a single line reliably.
# ---------------------------------------------------------------------------

def cmd_lookup(args, repo_root, cfg):
    """Inspect a registry entry and print {value, state, value_file_path} as JSON.

    State is one of 'not-in-registry', 'file-deferred', 'registry-only',
    'file-backed'. The calling skill uses this to decide create vs refresh
    and to refuse incoherent invocations (e.g. refresh on a missing file).
    """
    reg_path = axis_utils.registry_path(repo_root, cfg, args.axis)
    if not os.path.exists(reg_path):
        raise FileNotFoundError(f'registry not found: {reg_path}')
    text = _util.read(reg_path)
    _, state, value_filename = _find_registry_entry(text, args.value)
    if state is None:
        result = {
            'value': args.value,
            'state': 'not-in-registry',
            'value_file_path': None,
        }
    else:
        vf_path = (
            axis_utils.value_file_path(repo_root, cfg, args.axis, value_filename)
            if value_filename else None
        )
        result = {
            'value': args.value,
            'state': state,
            'value_file_path': vf_path,
        }
    print(json.dumps(result))


# ---------------------------------------------------------------------------
# Subcommand: list
# Emit every registry entry as a single JSON object. The calling skill uses
# this in Phase 1 to identify the target value's state AND to build the
# siblings list in one call, without parsing the registry itself.
# ---------------------------------------------------------------------------

def cmd_list(args, repo_root, cfg):
    """Print {"entries": [...]} for every bullet in the axis registry.

    Each entry is {value, state, value_file_path}. State is one of
    'file-backed', 'file-deferred', 'registry-only'. value_file_path is
    the absolute path for file-backed entries, None otherwise.
    """
    reg_path = axis_utils.registry_path(repo_root, cfg, args.axis)
    if not os.path.exists(reg_path):
        raise FileNotFoundError(f'registry not found: {reg_path}')
    text = _util.read(reg_path)
    entries = []
    for m in _BULLET_RE.finditer(text):
        value = m.group('value').strip()
        state, value_filename = _classify_bullet(m.group('rest'))
        vf_path = (
            axis_utils.value_file_path(repo_root, cfg, args.axis, value_filename)
            if value_filename else None
        )
        entries.append({
            'value': value,
            'state': state,
            'value_file_path': vf_path,
        })
    print(json.dumps({'entries': entries}))


# ---------------------------------------------------------------------------
# Subcommand: slice
# Return the body of a named '## Section' from a file-backed axis value file.
# Used by the industry-builder skill's Phase 4 to give the reconciler subagent
# just the Adjacency section content of each sibling, rather than the full
# file. Keeps the reconciler's context cost bounded regardless of how many
# siblings an axis registry contains.
# ---------------------------------------------------------------------------

def cmd_slice(args, repo_root, cfg):
    """Print the body text of '## <section>' from a file-backed value's file.

    Requires the value to be file-backed (otherwise there is no file to
    slice). Output is the raw section body on stdout, no JSON wrapper, so
    the caller can splice it directly into a subagent prompt.
    """
    reg_path = axis_utils.registry_path(repo_root, cfg, args.axis)
    if not os.path.exists(reg_path):
        raise FileNotFoundError(f'registry not found: {reg_path}')
    text = _util.read(reg_path)
    _, state, value_filename = _find_registry_entry(text, args.value)
    if state != 'file-backed' or not value_filename:
        raise ValueError(
            f'slice requires a file-backed value; {args.value} is {state}')
    vf_path = axis_utils.value_file_path(repo_root, cfg, args.axis, value_filename)
    if not os.path.exists(vf_path):
        raise FileNotFoundError(f'value file missing: {vf_path}')
    body = _util.read(vf_path)
    start, end = axis_utils.find_section_bounds(body, args.section)
    sys.stdout.write(body[start:end])


# ---------------------------------------------------------------------------
# Cross-script helpers
# Other axis-builder scripts (axis_qc, axis_apply) re-use _BULLET_RE and
# _find_registry_entry. Expose them at module scope so importers can call
# axis_registry.find_registry_entry(...) without duplicating the regex.
# ---------------------------------------------------------------------------

BULLET_RE = _BULLET_RE
classify_bullet = _classify_bullet
find_registry_entry = _find_registry_entry


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses subcommand and arguments, loads config, runs the subcommand, and
# reports failure to stderr with a non-zero exit so the calling skill halts
# per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch to the selected subcommand."""
    parser = argparse.ArgumentParser(
        description='axis-builder registry parsing and section slicing')
    sub = parser.add_subparsers(dest='command', required=True)

    # --- Subparser: lookup ---
    p_look = sub.add_parser('lookup', help='Phase 1: inspect a single registry entry')
    p_look.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    p_look.add_argument('value', help='registry key (e.g. generics)')
    p_look.set_defaults(func=cmd_lookup)

    # --- Subparser: list ---
    p_list = sub.add_parser('list', help='Phase 1: list every registry entry for an axis')
    p_list.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    p_list.set_defaults(func=cmd_list)

    # --- Subparser: slice ---
    p_slice = sub.add_parser(
        'slice',
        help='Phase 4: print the body of one section from a file-backed value file',
    )
    p_slice.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    p_slice.add_argument('value', help='registry key of the file-backed value to slice')
    p_slice.add_argument(
        '--section', required=True,
        help='heading (without ## prefix) of the section to extract, e.g. Adjacency',
    )
    p_slice.set_defaults(func=cmd_slice)

    args = parser.parse_args()

    # --- Dispatch ---
    # ContractError exit categorization is consistent across the axis-builder
    # script family even though axis_registry does not currently consume
    # subagent JSON; future subcommands or composition uses might, and
    # the dispatching SKILL relies on a uniform exit-code contract.
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except axis_utils.ContractError as e:
        print(f'ContractError: {e}', file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
