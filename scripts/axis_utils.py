#!/usr/bin/env python3
"""
axis_utils.py - shared helpers for the axis-builder script family

Helpers used by 2+ of the axis-builder concern scripts (axis_registry.py,
axis_qc.py, axis_apply.py). Three groups:

  Path resolution    Build absolute paths from config.yaml so no script
                     hardcodes repo state.
  Markdown sections  Locate '## Heading' bodies for slicing and editing.
                     Used by axis_registry's slice subcommand, axis_qc's
                     section-aware checks, and axis_apply's back-edge inserts.
  Frontmatter        Split the leading '---' fence block from the body so
                     keys can be edited without round-tripping YAML.
  Contract guarding  Accept both bare-list and self-describing-wrapper shapes
                     for subagent JSON outputs, so a reconciler/script
                     contract drift cannot surface as a Python traceback in
                     front of the end user.

Scope is the axis-builder family only. General I/O lives in scripts/_util.py;
config loading lives in scripts/_config.py.

Author    : Jason Delosh
Created   : 2026-05-19
Project   : career
Depends   : none (stdlib only)
"""

import os
import re


# ---------------------------------------------------------------------------
# Path resolution
# All paths derive from config.yaml's paths/filenames sections. Callers pass
# (repo_root, cfg) tuples returned by _config.load().
# ---------------------------------------------------------------------------

def axis_dir(repo_root, cfg, axis):
    """Return the absolute path to rules/<axis>/."""
    return os.path.join(repo_root, cfg['paths']['rules'], axis)


def registry_path(repo_root, cfg, axis):
    """Return the absolute path to rules/<axis>/registry.md."""
    return os.path.join(axis_dir(repo_root, cfg, axis), cfg['filenames']['axis_registry'])


def value_file_path(repo_root, cfg, axis, value_filename):
    """Return the absolute path to rules/<axis>/<value_filename>."""
    return os.path.join(axis_dir(repo_root, cfg, axis), value_filename)


# ---------------------------------------------------------------------------
# Markdown sections
# Axis value files use '## <Heading>' sections. Sibling back-edges (create
# mode) are inserted at the end of the target file's '## Adjacency' section;
# QC's section-aware checks resolve sections by heading.
# ---------------------------------------------------------------------------

def find_section_bounds(text, heading):
    """Return (start, end) character offsets of a '## heading' section body.

    Body excludes the heading line itself; start is the offset just after the
    heading line's trailing newline; end is the offset of the next '## ' line
    or the end of file. Raises ValueError if the heading is absent.
    """
    pattern = re.compile(
        r'^##[ ]+' + re.escape(heading) + r'[ \t]*\n',
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        raise ValueError(f'section not found: ## {heading}')
    body_start = m.end()
    next_heading = re.search(r'^##[ ]', text[body_start:], re.MULTILINE)
    body_end = body_start + next_heading.start() if next_heading else len(text)
    return body_start, body_end


# ---------------------------------------------------------------------------
# Frontmatter
# YAML frontmatter is the text from the first '---' line to the next '---'
# line, inclusive of both fences. Edit line-by-line rather than round-tripping
# YAML to preserve whatever formatting the file already has.
# ---------------------------------------------------------------------------

def split_frontmatter(text):
    """Return (frontmatter_block_with_fences, body) or (None, text) if absent.

    Frontmatter is recognized as the text from the first '---' line to the
    next '---' line, inclusive of both fences.
    """
    if not text.startswith('---\n'):
        return None, text
    # Find the closing fence.
    rest = text[4:]
    m = re.search(r'^---\n', rest, re.MULTILINE)
    if not m:
        return None, text
    end = 4 + m.end()
    return text[:end], text[end:]


# ---------------------------------------------------------------------------
# Contract guarding
# Subagent outputs cross a typed boundary into the script. If the subagent
# emits an unexpected shape (wrong top-level type, missing required key,
# bad enum value), the script must fail with a categorized error the
# dispatching SKILL can translate to plain English, never a raw Python
# traceback in front of the end user.
#
# Two pieces:
#   - ContractError: distinct exception class so the CLI entry point in
#     each script can recognize the failure category and emit a
#     'ContractError:' stderr line (exit code 2). Any other failure
#     becomes 'Error:' (exit code 1).
#   - validate_list_of_dicts(): one validator that enforces top-level
#     shape, required keys, optional keys, string-type per field, and
#     enum constraints. Centralized so every script speaks the same
#     contract language and every future axis builder inherits the
#     protection without re-implementing it.
#
# Shape constants are declared below as module-level dicts. Scripts
# import and pass them; they do not redefine shapes inline.
# ---------------------------------------------------------------------------

class ContractError(Exception):
    """Raised when a JSON input does not match the declared shape.

    Distinct from ValueError so the CLI entry point in each script can
    recognize the failure category, emit a 'ContractError:' stderr line,
    and exit with code 2. The dispatching SKILL recognizes the prefix
    and translates the technical detail into a user-facing message,
    appending the full message to design/build_issues.md for dev triage.
    """


def unwrap_list(parsed, key):
    """Return the inner list regardless of which contract shape the caller used.

    Accepts both the bare-list shape (`[...]`) and the self-describing
    wrapper shape (`{"<key>": [...]}`). Raises ContractError on any
    other shape so the failure category is recognizable downstream.
    """
    if isinstance(parsed, dict) and isinstance(parsed.get(key), list):
        return parsed[key]
    if isinstance(parsed, list):
        return parsed
    raise ContractError(
        f'expected a JSON list or {{"{key}": [...]}}; got {type(parsed).__name__}'
    )


# Shape constants. Each is the schema for one subagent output type that
# crosses the subagent/script boundary. Adding a new axis builder?
# Add the new shapes here, not inline at the call site.
SIBLING_EDIT_SHAPE = {
    'required_keys': ('sibling_file', 'section', 'bullet'),
    'optional_keys': (),
    'enums': {},
}
CHANGE_SHAPE = {
    'required_keys': ('section', 'type', 'current', 'proposed', 'reasoning'),
    'optional_keys': (),
    'enums': {'type': ('add', 'remove', 'modify')},
}
ISSUE_SHAPE = {
    'required_keys': ('check', 'detail'),
    'optional_keys': ('attempted',),
    'enums': {},
}


def validate_list_of_dicts(items, *, input_name, shape):
    """Verify items is a list of dicts matching the declared shape.

    Raises ContractError with a precise message naming the input, the
    element index, and the offending field/type on first mismatch. Does
    not aggregate errors; first failure stops validation so the error
    text stays short and actionable for dev triage.

    Parameters
    ----------
    items : object
        The parsed JSON (already unwrapped via unwrap_list if applicable).
    input_name : str
        Human-readable name of the input ('sibling_edits', 'changes',
        'issues'), used in error messages.
    shape : dict
        One of SIBLING_EDIT_SHAPE / CHANGE_SHAPE / ISSUE_SHAPE.
    """
    required = shape['required_keys']
    optional = shape['optional_keys']
    enums = shape['enums']
    allowed = set(required) | set(optional)

    if not isinstance(items, list):
        raise ContractError(
            f'{input_name}: expected a JSON list at top level; '
            f'got {type(items).__name__}'
        )
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ContractError(
                f'{input_name}[{i}]: expected an object; got {type(item).__name__}'
            )
        missing = [k for k in required if k not in item]
        if missing:
            raise ContractError(
                f'{input_name}[{i}]: missing required key(s): {", ".join(missing)}'
            )
        extra = [k for k in item if k not in allowed]
        if extra:
            raise ContractError(
                f'{input_name}[{i}]: unexpected key(s): {", ".join(extra)}'
            )
        for k in required:
            if not isinstance(item[k], str):
                raise ContractError(
                    f'{input_name}[{i}].{k}: expected string; '
                    f'got {type(item[k]).__name__}'
                )
        for k in optional:
            if k in item and not isinstance(item[k], str):
                raise ContractError(
                    f'{input_name}[{i}].{k}: expected string; '
                    f'got {type(item[k]).__name__}'
                )
        for k, allowed_values in enums.items():
            if k in item and item[k] not in allowed_values:
                raise ContractError(
                    f'{input_name}[{i}].{k}: expected one of '
                    f'{list(allowed_values)}; got {item[k]!r}'
                )
