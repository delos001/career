#!/usr/bin/env python3
"""
_shared_slicer.py - split a keyed rules file into sections and slice it by key

Shared parsing for the rules slicers (profile_rules_slice.py, cv_rules_slice.py).
A keyed rules file is its opening text plus '## ' sections, each headed
'## KEY: name' with KEY in upper-case letters. This module knows nothing about
what a key means; each slicer passes its own list of valid keys and its own
shared key (the key whose sections every reader gets).

Every '## ' heading must carry a valid key. A heading with no key, or with a
key the slicer does not list, is an error: a forgotten or mistyped key would
otherwise route a section to the wrong readers without anyone noticing.

Author    : Jason Delosh
Created   : 2026-11-16
Project   : career
Usage     : imported by the slicers; not run directly
Depends   : (stdlib only)
"""

import re


# ---------------------------------------------------------------------------
# Section parsing
# ---------------------------------------------------------------------------

# Regex: a keyed section heading, capturing its key.
_KEYED_RE = re.compile(r'^## ([A-Z]+): ')


def sections(text):
    """Return (opening, [(key or None, heading line, section text)])."""
    # Splitting before each '## ' line leaves the opening text first, empty
    # when the file starts with a section.
    opening, *body = re.split(r'(?m)^(?=## )', text)
    out = []
    for part in body:
        m = _KEYED_RE.match(part)
        out.append((m.group(1) if m else None, part.splitlines()[0], part))
    return opening, out


def keys(text):
    """Return the keys a rules file has sections for, in file order."""
    return [key for key, _, _ in sections(text)[1] if key]


# ---------------------------------------------------------------------------
# Validation and slicing
# ---------------------------------------------------------------------------

def check_keys(text, valid, shared):
    """Raise ValueError naming every heading with no key or an unknown key."""
    allowed = set(valid) | {shared}
    problems = []
    for key, heading, _ in sections(text)[1]:
        if key is None:
            problems.append(f'no key: {heading}')
        elif key not in allowed:
            problems.append(f'unknown key {key}: {heading}')
    if problems:
        raise ValueError(
            'rules file has headings that cannot be routed; valid keys are '
            f"{', '.join(sorted(allowed))}:\n  " + '\n  '.join(problems))


def slice_keys(text, wanted, valid, shared):
    """Return the opening, the shared sections, and each wanted key's sections.

    The file is checked first, so a slice is never taken from a file whose
    routing is broken. A wanted key the file has no section for is an error,
    never a silent fall back to the shared sections alone.
    """
    check_keys(text, valid, shared)
    unknown = [k for k in wanted if k not in valid]
    if unknown:
        raise ValueError(f"unknown key {', '.join(unknown)}; valid keys are {', '.join(sorted(valid))}")
    present = keys(text)
    missing = [k for k in wanted if k not in present]
    if missing:
        raise ValueError(
            f"no section for {', '.join(missing)}; this file has sections for "
            f"{', '.join(k for k in present if k != shared) or 'no keys'}")
    opening, parts = sections(text)
    kept = [part for key, _, part in parts if key == shared or key in wanted]
    return (opening + ''.join(kept)).rstrip() + '\n'
