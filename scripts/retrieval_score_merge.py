#!/usr/bin/env python3
"""
retrieval_score_merge.py - merge per-agent score files into final score files

After Phase 3 of the retrieval skill, each scorer agent has written its
results to a per-chunk temp file. This script collects those files,
validates them, merges them into the three final score files that
retrieval_apply.py expects, and prints a confirmation.

Conventions (derived from --slug and --app-id):
  Input chunk files  : temp/<slug>_<app-id>_scores_inventory_chunk{N}.json
  Input narrative    : temp/<slug>_<app-id>_scores_narr_chunk{N}.json
  Input themes file  : temp/<slug>_<app-id>_scores_themes.json
  Output inventory   : temp/<slug>_<app-id>_inventory_scores.json
  Output narratives  : temp/<slug>_<app-id>_narrative_scores.json
  Output themes      : temp/<slug>_<app-id>_theme_scores.json

The script reads the inventory payload file (written by retrieval_payload.py)
to discover the expected inventory chunk count, discovers narrative chunk
count from the payload-side chunk files written by the split subcommand, and
validates that the merged narrative scores exactly cover the narrative IDs in
the narratives payload before writing.

Author  : Jason Delosh
Created : 2026-06-01
Project : career
Usage   : python scripts/retrieval_score_merge.py --slug <slug> --app-id <APP-NNN> [--temp-dir temp]
Depends : standard library only
"""

import argparse
import json
import os
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path):
    """Load and return JSON from path, raising with a clear message on failure."""
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f'expected score file not found: {path}')
    except json.JSONDecodeError as e:
        raise ValueError(f'invalid JSON in {path}: {e}')


def _write_json(path, data):
    """Write data as JSON to path."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------

def merge_scores(slug, app_id, temp_dir):
    """Discover, validate, merge, and write all three corpora score files."""
    prefix = f"{slug}_{app_id}"
    os.makedirs(temp_dir, exist_ok=True)  # scratch dir may not exist yet on a fresh run

    # --- Discover expected inventory chunks from payload file ---
    inv_payload_path = os.path.join(temp_dir, f"{prefix}_inventory_payload.json")
    inv_payload = _load_json(inv_payload_path)
    chunk_count = inv_payload['chunk_count']

    # --- Discover expected narrative IDs from payload file ---
    nar_payload_path = os.path.join(temp_dir, f"{prefix}_narratives_payload.json")
    nar_payload = _load_json(nar_payload_path)
    narrative_ids = [e['id'] for e in nar_payload['entries']]

    # --- Merge inventory chunks ---
    inv_scores = []
    for i in range(chunk_count):
        path = os.path.join(temp_dir, f"{prefix}_scores_inventory_chunk{i}.json")
        data = _load_json(path)
        inv_scores.extend(data['scores'])

    inv_out = os.path.join(temp_dir, f"{prefix}_inventory_scores.json")
    _write_json(inv_out, {'scores': inv_scores})

    # --- Merge narrative chunks ---
    # Narrative chunking is byte-budgeted, so the chunk count is not derivable
    # from the payload alone; discover it from the payload-side chunk files
    # written by retrieval_payload.py split.
    nar_scores = []
    chunk_index = 0
    while os.path.exists(os.path.join(temp_dir, f"{prefix}_narr_chunk{chunk_index}.json")):
        score_path = os.path.join(temp_dir, f"{prefix}_scores_narr_chunk{chunk_index}.json")
        data = _load_json(score_path)
        nar_scores.extend(data['scores'])
        chunk_index += 1
    if chunk_index == 0:
        raise FileNotFoundError(
            f'no narrative chunk files found ({prefix}_narr_chunk0.json missing); '
            'run retrieval_payload.py split first'
        )

    # Validate: merged scores must exactly cover the payload's narrative IDs.
    scored_ids = {s['id'] for s in nar_scores}
    if len(nar_scores) != len(scored_ids):
        raise ValueError('duplicate narrative IDs across score chunks (stale chunk file?)')
    expected_ids = set(narrative_ids)
    if scored_ids != expected_ids:
        problems = []
        missing = sorted(expected_ids - scored_ids)
        extra = sorted(scored_ids - expected_ids)
        if missing:
            problems.append(f"unscored: {', '.join(missing)}")
        if extra:
            problems.append(f"unexpected: {', '.join(extra)}")
        raise ValueError(f"narrative score coverage mismatch ({'; '.join(problems)})")

    nar_out = os.path.join(temp_dir, f"{prefix}_narrative_scores.json")
    _write_json(nar_out, {'scores': nar_scores})

    # --- Copy themes (single file, no merge needed) ---
    th_in = os.path.join(temp_dir, f"{prefix}_scores_themes.json")
    th_data = _load_json(th_in)
    th_out = os.path.join(temp_dir, f"{prefix}_theme_scores.json")
    _write_json(th_out, {'scores': th_data['scores']})

    # --- Print confirmation ---
    print(f"Merged inventory: {len(inv_scores)} entries → {inv_out}")
    print(f"Merged narratives: {len(nar_scores)} entries → {nar_out}")
    print(f"Themes: {len(th_data['scores'])} entries → {th_out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='merge per-agent score files into final score files for retrieval_apply.py'
    )
    parser.add_argument('--slug', required=True, help='role slug (e.g. takeda)')
    parser.add_argument('--app-id', required=True, help='application ID (e.g. APP-006)')
    parser.add_argument('--temp-dir', default='temp', help='temp directory (default: temp)')
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        merge_scores(args.slug, args.app_id, args.temp_dir)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
