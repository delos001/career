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
# The reconciler subagent emits self-describing objects
# ({'mode': 'create', 'sibling_edits': [...]} or
# {'mode': 'refresh', 'changes': [...]}); legacy callers and tests pass the
# bare list. Both shapes are accepted so a contract mismatch between the
# agent and the script cannot surface as a Python traceback in front of the
# end user (see deferral 'builder-contract-drift-guardrails').
# ---------------------------------------------------------------------------

def unwrap_list(parsed, key):
    """Return the inner list regardless of which contract shape the caller used."""
    if isinstance(parsed, dict) and isinstance(parsed.get(key), list):
        return parsed[key]
    if isinstance(parsed, list):
        return parsed
    raise ValueError(
        f'expected a JSON list or {{"{key}": [...]}}; got {type(parsed).__name__}'
    )
