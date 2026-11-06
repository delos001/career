#!/usr/bin/env python3
"""
axis_dispatch.py - print an axis builder subagent's complete dispatch prompt

Shared by all five axis builders, whose reconciler and QC agents used to receive
the draft, research block, and sibling text pasted by the orchestrator (GitHub #71).
The orchestrator now writes its own run output once, to fixed names in the builder
scratch folder; this script copies each sibling's Adjacency section verbatim beside
them and prints a prompt of paths. The skill sends it exactly as printed. A required
file that is missing stops the run.

Files the skill writes to --scratch-dir before dispatching:
  value_file.md         the drafted value file (reconciler, qc)
  research_findings.md  the research agent's block, verbatim (reconciler in refresh, qc)
  sibling_edits.json    the reconciler's back-edges (qc in create)
  registry_entry.md     the proposed registry line (qc in create)
  qc_result.json        axis_qc.py's stdout, for its acronym suggestions (qc)

Author    : Jason Delosh
Created   : 2026-11-05
Project   : career
Usage     : python scripts/axis_dispatch.py research <axis> <value> --scratch-dir <dir>
            python scripts/axis_dispatch.py reconciler|qc <axis> <value>
                --mode create|refresh --scratch-dir <dir>
Depends   : pyyaml (via _config)
"""

import argparse
import json
import os
import sys

import _config
import _util
import axis_registry
import axis_utils


SIBLING_FILE = 'sibling_adjacency.md'


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def _siblings(repo_root, cfg, axis, value):
    """Return [(value, value file path or None)] for every other registry entry."""
    path = axis_utils.registry_path(repo_root, cfg, axis)
    if not os.path.exists(path):
        raise FileNotFoundError(f'registry not found: {path}')
    out = []
    for m in axis_registry.BULLET_RE.finditer(_util.read(path)):
        name = m.group('value').strip()
        if name == value:
            continue
        state, filename = axis_registry.classify_bullet(m.group('rest'))
        backed = state == 'file-backed' and filename
        out.append((name, axis_utils.value_file_path(repo_root, cfg, axis, filename) if backed else None))
    return out


def write_sibling_adjacency(siblings, path):
    """Copy each file-backed sibling's Adjacency section, verbatim, to one file."""
    parts = []
    for name, value_file in siblings:
        if not value_file:
            continue
        if not os.path.exists(value_file):
            raise FileNotFoundError(f'value file missing: {value_file}')
        body = _util.read(value_file)
        start, end = axis_utils.find_section_bounds(body, 'Adjacency')
        parts.append(f'# Sibling: {name}\n\n{body[start:end]}')
    _util.write(path, '\n\n'.join(parts) + '\n')


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def _required(scratch, name):
    """Return the path of a run file, or stop when the skill has not written it."""
    path = os.path.join(scratch, name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f'required file missing: {path}')
    return path


def _acronym_suggestions(qc_result_path):
    """Return the H2 check's suggestions from axis_qc.py's saved stdout."""
    checks = json.loads(_util.read(qc_result_path)).get('checks', [])
    # Only axes with an acronym catalog run H2, so its absence is not an error.
    h2 = next((c for c in checks if c.get('id') == 'H2'), None)
    return None if h2 is None else h2.get('suggestions', [])


def build_prompt(kind, axis, value, mode, scratch, repo_root, cfg):
    """Return the complete prompt for one builder dispatch."""
    siblings = _siblings(repo_root, cfg, axis, value)
    lines = [f'axis: {axis}', f'value: {value}']
    if kind == 'research':
        lines.append('siblings: ' + ', '.join(name for name, _ in siblings))
        return '\n'.join(lines)

    lines.append(f'mode: {mode}')
    if kind == 'reconciler':
        lines.append(f'drafted_value_file: {_required(scratch, "value_file.md")}')
        if mode == 'create':
            path = os.path.join(scratch, SIBLING_FILE)
            write_sibling_adjacency(siblings, path)
            lines.append(f'siblings: {path}')
        else:
            registry = _util.read(axis_utils.registry_path(repo_root, cfg, axis))
            _, _, filename = axis_registry.find_registry_entry(registry, value)
            existing = axis_utils.value_file_path(repo_root, cfg, axis, filename or f'{value}.md')
            if not os.path.isfile(existing):
                raise FileNotFoundError(f'value file missing: {existing}')
            lines.append(f'current_value_file: {existing}')
            lines.append(f'research_findings: {_required(scratch, "research_findings.md")}')
        return '\n'.join(lines)

    # qc
    lines.append(f'value_file_text: {_required(scratch, "value_file.md")}')
    lines.append(f'research_findings: {_required(scratch, "research_findings.md")}')
    lines += [f'sibling {name}: {path}' for name, path in siblings if path]
    if mode == 'create':
        lines.append(f'sibling_edits: {_required(scratch, "sibling_edits.json")}')
        lines.append(f'registry_entry: {_required(scratch, "registry_entry.md")}')
    suggestions = _acronym_suggestions(_required(scratch, 'qc_result.json'))
    if suggestions is not None:
        lines.append('acronym_suggestions: ' + (', '.join(suggestions) or 'none'))
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Command-line entry point
# Reports failure to stderr with exit 1 so the calling skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv and print the prompt between markers."""
    parser = argparse.ArgumentParser(description="print an axis builder subagent's dispatch prompt")
    parser.add_argument('kind', choices=['research', 'reconciler', 'qc'])
    parser.add_argument('axis', help='axis folder name under rules/ (e.g. industries)')
    parser.add_argument('value', help='registry key being built')
    parser.add_argument('--mode', choices=['create', 'refresh'], default=None)
    parser.add_argument('--scratch-dir', required=True, help='the builder scratch folder')
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        if args.kind != 'research' and not args.mode:
            raise ValueError(f'{args.kind} needs --mode')
        repo_root, cfg = _config.load()
        prompt = build_prompt(args.kind, args.axis, args.value, args.mode,
                              os.path.abspath(args.scratch_dir), repo_root, cfg)
        print('=== PROMPT ===')
        print(prompt)
        print('=== END ===')
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
