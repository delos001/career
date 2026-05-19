#!/usr/bin/env python3
"""
_util.py - shared I/O and date helpers for the career repo's scripts

UTF-8 text read/write, JSON loading, and date formatting helpers used by
multiple scripts. Lives alongside _config.py as a sibling helper module; the
leading underscore signals "imported, never invoked directly."

Consolidating these helpers here keeps each script's own file focused on its
concern (registry parsing, QC, apply, document assembly, etc.) and prevents
the duplication that previously had _read / _write defined separately in
each script.

Author    : Jason Delosh
Created   : 2026-05-19
Project   : career
Depends   : none (stdlib only)
"""

import datetime
import json
import os


# ---------------------------------------------------------------------------
# Text file I/O
# UTF-8 throughout. _write creates parent folders if missing so callers do
# not need to scaffold directory structure ahead of time.
# ---------------------------------------------------------------------------

def read(path):
    """Read a UTF-8 text file and return its contents (raises if missing)."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write(path, text):
    """Write text to a UTF-8 file, creating parent folders if they do not exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


# ---------------------------------------------------------------------------
# JSON loading
# Thin wrapper so callers don't have to repeat the UTF-8 open/json.load idiom.
# ---------------------------------------------------------------------------

def load_json(path):
    """Load a JSON file and return its parsed content."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Date formatting
# YYYY-MM is the canonical granularity for frontmatter last_researched fields;
# YYYY-MM-DD is used for build-issues log entries.
# ---------------------------------------------------------------------------

def today_ym():
    """Return the current year-month as YYYY-MM."""
    return datetime.date.today().strftime('%Y-%m')


def today_iso():
    """Return the current date as YYYY-MM-DD."""
    return datetime.date.today().strftime('%Y-%m-%d')
