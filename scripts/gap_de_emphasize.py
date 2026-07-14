#!/usr/bin/env python3
"""
gap_de_emphasize.py - deterministic candidate pre-filter for de-emphasize

The de-emphasize decision has three conditions (per the de-emphasize-identifier
agent spec): (1) the entry is not already cited as CV evidence, (2) the entry
is distant from the role's axes, (3) the entry's substance would dilute the
role's narrative. Conditions 1 and 2 are data lookups; only condition 3 needs
LLM judgment. This script applies 1 and 2 and writes a bounded candidates
file (id, axis tags, signals, payload) so the judgment agent reads only the
candidate bodies instead of the full manifest plus the full inventory.

Condition mechanics:
  1. Exclusion set = evidence IDs of every requirement whose status the CV
     cites (covered / closed / language-shift / partial-match), computed by
     the same function gap_assemble.py uses for its downstream safety net,
     so the two can never drift.
  2. Signal cutoffs come from config.yaml (gap_analysis.de_emphasize):
     candidate if axis exact-match <= max_axis_exact AND adjacency-weighted
     score <= max_axis_adj. An entry absent from the manifest has no signals
     (surfaced by neither retrieval pass) and counts as maximally distant.

Author  : Jason Delosh
Created : 2026-07-14
Project : career
Usage   : python scripts/gap_de_emphasize.py filter --folder <app_folder> --requirements-file <path> --out <path>
Depends : pyyaml (via _config)
"""

import argparse
import json
import os
import re
import sys

import _config
import _util
import gap_assemble
import retrieval_payload


# ---------------------------------------------------------------------------
# Manifest signal parsing
# The inventory table of retrieval.md carries the two axis signals per entry:
# | ID | Employer | Semantic | Axis exact | Axis adj | Source | Axis matches | Reason |
# ---------------------------------------------------------------------------

def _parse_manifest_signals(manifest_text):
    """Return {entry_id: (axis_exact int, axis_adj float)} from the manifest."""
    lines = manifest_text.split('\n')
    start = None
    for i, line in enumerate(lines):
        if line.strip() == '## Inventory candidates':
            start = i + 1
            break
    if start is None:
        raise ValueError('manifest has no ## Inventory candidates section')
    signals = {}
    for line in lines[start:]:
        if line.startswith('## '):
            break
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        # Skip the header and the |----| separator; data rows open with an ID.
        if len(cells) < 5 or not re.fullmatch(r'(?:EX|PR|PB|PS)-\d+', cells[0]):
            continue
        try:
            signals[cells[0]] = (int(cells[3]), float(cells[4]))
        except ValueError:
            raise ValueError(f'unparseable axis signals on manifest row {cells[0]}')
    return signals


# ---------------------------------------------------------------------------
# Subcommand: filter
# ---------------------------------------------------------------------------

def cmd_filter(args, repo_root, cfg):
    """Apply conditions 1 and 2; write the candidates file; print a summary."""
    fn = cfg['filenames']
    cutoffs = cfg['gap_analysis']['de_emphasize']
    max_exact = cutoffs['max_axis_exact']
    max_adj = cutoffs['max_axis_adj']

    inventory_text = _util.read(os.path.join(
        repo_root, cfg['paths']['profile'], fn['inventory_file']))
    manifest_text = _util.read(os.path.join(args.folder, fn['retrieval_manifest']))
    requirements = _util.load_json(args.requirements_file)
    if isinstance(requirements, dict):
        requirements = requirements.get('requirements', requirements.get('assessments', []))

    entries = retrieval_payload.parse_inventory_entries(inventory_text)
    signals = _parse_manifest_signals(manifest_text)
    cited = gap_assemble.cited_evidence_ids(requirements)

    candidates = []
    excluded_evidence = 0
    excluded_signals = 0
    for entry in entries:
        eid = entry['id']
        if eid in cited:
            excluded_evidence += 1
            continue
        sig = signals.get(eid)
        if sig is not None and not (sig[0] <= max_exact and sig[1] <= max_adj):
            excluded_signals += 1
            continue
        candidates.append({
            'id': eid,
            'industry': entry['industry'],
            'specialty': entry['specialty'],
            'orientation': entry['orientation'],
            'level': entry['level'],
            'work_state': entry['work_state'],
            'axis_exact': sig[0] if sig else None,
            'axis_adj': sig[1] if sig else None,
            'payload': entry['payload'],
        })

    out = {
        'cutoffs': {'max_axis_exact': max_exact, 'max_axis_adj': max_adj},
        'candidate_count': len(candidates),
        'candidates': candidates,
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)

    print(f'Inventory entries: {len(entries)}')
    print(f'Excluded as CV-cited evidence: {excluded_evidence}')
    print(f'Excluded by axis signals (exact > {max_exact} or adj > {max_adj}): {excluded_signals}')
    unsurfaced = sum(1 for c in candidates if c['axis_exact'] is None)
    print(f'De-emphasize candidates: {len(candidates)} ({unsurfaced} not in the manifest)')
    print(f'Candidates file: {args.out}')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Pre-filter de-emphasize candidates for the gap-analysis skill.')
    sub = parser.add_subparsers(dest='command', required=True)
    p_filter = sub.add_parser('filter', help='write the candidates file for one application')
    p_filter.add_argument('--folder', required=True,
                          help='absolute path to the application folder (holds retrieval.md)')
    p_filter.add_argument('--requirements-file', required=True,
                          help='path to the Phase 4 gap_requirements.json scratch file')
    p_filter.add_argument('--out', required=True,
                          help='output path for the candidates JSON (scratch)')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        if args.command == 'filter':
            cmd_filter(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
