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

For inventory and narratives alike, the script discovers the chunk count from
the payload-side chunk files written by the split subcommand, and validates
that the merged scores cover every item in that corpus's payload file exactly
once before writing.

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

def _merge_chunked(temp_dir, prefix, corpus, kind, score_kind):
    """Merge one corpus's chunk score files; return the validated score list.

    Chunking is byte-budgeted in split, so the chunk count is not derivable
    from the payload; it is discovered from the payload-side chunk files
    (<prefix>_<kind>_chunk{N}.json). The merged scores must then cover the
    corpus payload's IDs exactly once each. A duplicate ID in the inventory
    itself (two entries sharing one) surfaces here too, as a duplicate score.
    """
    payload = _load_json(os.path.join(temp_dir, f"{prefix}_{corpus}_payload.json"))
    expected = [e['id'] for e in payload['entries']]

    scores = []
    idx = 0
    while os.path.exists(os.path.join(temp_dir, f"{prefix}_{kind}_chunk{idx}.json")):
        data = _load_json(os.path.join(temp_dir, f"{prefix}_scores_{score_kind}{idx}.json"))
        scores.extend(data['scores'])
        idx += 1
    if idx == 0:
        raise FileNotFoundError(
            f'no {corpus} chunk files found ({prefix}_{kind}_chunk0.json missing); '
            'run retrieval_payload.py split first')

    scored = [s['id'] for s in scores]
    dupes = sorted({i for i in scored if scored.count(i) > 1}
                   | {i for i in expected if expected.count(i) > 1})
    if dupes:
        raise ValueError(f"duplicate {corpus} IDs across score chunks: {', '.join(dupes)} "
                         '(stale chunk file, or two entries sharing one ID?)')
    missing = sorted(set(expected) - set(scored))
    extra = sorted(set(scored) - set(expected))
    if missing or extra:
        problems = ([f"unscored: {', '.join(missing)}"] if missing else []) \
                 + ([f"unexpected: {', '.join(extra)}"] if extra else [])
        raise ValueError(f"{corpus} score coverage mismatch ({'; '.join(problems)})")
    return scores


def merge_scores(slug, app_id, temp_dir):
    """Discover, validate, merge, and write all three corpora score files."""
    prefix = f"{slug}_{app_id}"
    os.makedirs(temp_dir, exist_ok=True)  # scratch dir may not exist yet on a fresh run

    # --- Merge and validate both chunked corpora before writing either ---
    inv_scores = _merge_chunked(temp_dir, prefix, 'inventory', 'inv', 'inventory_chunk')
    nar_scores = _merge_chunked(temp_dir, prefix, 'narratives', 'narr', 'narr_chunk')

    inv_out = os.path.join(temp_dir, f"{prefix}_inventory_scores.json")
    _write_json(inv_out, {'scores': inv_scores})
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
