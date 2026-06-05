#!/usr/bin/env python3
"""
_config.py - shared config loader for the career repo's scripts

Resolves the repo root from this file's own location and loads config.yaml (the
repo-structure config at the repo root). Imported by the other scripts so none
of them hardcode repo paths, filenames, or the ID scheme - a repo reorganization
is then a config.yaml edit, not a code change.

This is a helper module, not a standalone script: it is imported, never invoked
directly.

Author    : Jason Delosh
Created   : 2026-05-14
Project   : career
Depends   : pyyaml
"""

import os

import yaml

# This file lives in scripts/, so the repo root is one folder up from here.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(REPO_ROOT, 'config.yaml')


def load():
    """Load config.yaml and return (repo_root, config).

    repo_root is the absolute path to the repo root; config is the parsed
    config.yaml as a dict. Callers join the relative paths in config onto
    repo_root themselves.
    """
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    # Normalize the OS separator in the directory paths. config.yaml authors them
    # with forward slashes for cross-platform readability, but on Windows joining
    # an unnormalized value onto the backslash repo_root yields a mixed-separator
    # path (e.g. 'C:\repo\personal/applications\...') - cosmetically wrong and it
    # has tripped QC on stored path fields. normpath is a no-op on POSIX (keeps
    # '/') and converts '/' to '\' on Windows, so joins downstream stay clean.
    for key, value in config.get('paths', {}).items():
        if isinstance(value, str):
            config['paths'][key] = os.path.normpath(value)
    return REPO_ROOT, config
