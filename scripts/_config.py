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

# Set this to a repo-root-relative folder to run every script against a test
# corpus instead of the real profile. Each path under 'personal' is rebased onto
# it, so a script cannot read or write the candidate's own documents while it is
# set. Rebasing is done by prefix rather than by naming the keys, so a new
# personal-rooted path added to config.yaml is redirected without a code change.
# See tests/README.md.
FIXTURE_ENV = 'CAREER_FIXTURE'


def load():
    """Load config.yaml and return (repo_root, config).

    repo_root is the absolute path to the repo root; config is the parsed
    config.yaml as a dict. Callers join the relative paths in config onto
    repo_root themselves.

    When CAREER_FIXTURE names a folder, every path that lives under the
    'personal' root is rebased onto it before the config is returned.
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
    _apply_fixture(config)
    return REPO_ROOT, config


def _apply_fixture(config):
    """Rebase every personal-rooted path onto the fixture folder, if set."""
    fixture = os.environ.get(FIXTURE_ENV)
    if not fixture:
        return
    fixture = os.path.normpath(fixture)
    if not os.path.isdir(os.path.join(REPO_ROOT, fixture)):
        raise ValueError(
            f'{FIXTURE_ENV} is set to "{fixture}", which is not a folder under '
            f'the repo root. Unset it to run against the real profile.')
    base = config['paths']['personal']
    for key, value in config['paths'].items():
        if value == base or value.startswith(base + os.sep):
            config['paths'][key] = os.path.normpath(
                os.path.join(fixture, os.path.relpath(value, base)))
