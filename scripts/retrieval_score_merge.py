#!/usr/bin/env python3
"""
retrieval_score_merge.py - merge per-agent score files into final score files

After Phase 3 of the retrieval skill, each scorer agent has written its
results to a per-chunk temp file. This script collects those files,
validates them, calibrates the chunks of each chunked corpus onto one scale,
merges them into the three final score files that retrieval_apply.py
expects, and prints a confirmation.

Conventions (derived from --slug and --app-id):
  Input chunk files  : temp/<slug>_<app-id>_scores_inventory_chunk{N}.json
  Input narrative    : temp/<slug>_<app-id>_scores_narr_chunk{N}.json
  Input themes file  : temp/<slug>_<app-id>_scores_themes.json
  Calibration anchors: temp/<slug>_<app-id>_calibration.json (split, then split-anchored)
  Output inventory   : temp/<slug>_<app-id>_inventory_scores.json
  Output narratives  : temp/<slug>_<app-id>_narrative_scores.json
  Output themes      : temp/<slug>_<app-id>_theme_scores.json

For inventory and narratives alike, the script discovers the chunk count from
the payload-side chunk files written by the split subcommand, and validates
that the merged scores cover every item in that corpus's payload file exactly
once (every calibration anchor exactly once per chunk) before writing.

Calibration: each chunk is scored by a separate scorer whose scale can drift
from the others. Every chunk of a multi-chunk corpus also scored the same
anchors; each anchor's consensus is the mean of its raw scores across chunks,
and each chunk is mapped onto that consensus with an outlier-resistant line
fit (Theil-Sen). The merged files carry the corrected scores plus a
'calibration' record (per-chunk fit, anchor disagreement before and after,
leave-one-out stability) that retrieval_apply.py writes into the manifest and
retrieval_qc.py checks. Raw per-chunk files are left untouched for audit.
Design and evidence: design/retrieval_calibration_plan.md.

Author  : Jason Delosh
Created : 2026-06-01
Project : career
Usage   : python scripts/retrieval_score_merge.py --slug <slug> --app-id <APP-NNN> [--temp-dir temp]
Depends : pyyaml (via _config)
"""

import argparse
import json
import os
import statistics
import sys

import _config


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


def _clamp(value):
    """Clamp a score to [0, 1] and round to the scorers' two decimals."""
    return round(min(1.0, max(0.0, value)), 2)


# ---------------------------------------------------------------------------
# Collect and validate
# ---------------------------------------------------------------------------

def _collect_chunks(temp_dir, prefix, corpus, kind, score_kind, anchors):
    """Return one score list per chunk, validated for coverage.

    Chunking is byte-budgeted in split, so the chunk count is not derivable
    from the payload; it is discovered from the payload-side chunk files
    (<prefix>_<kind>_chunk{N}.json). Every anchor must be scored exactly once
    in every chunk, and every other payload ID exactly once across all chunks.
    A duplicate ID in the inventory itself (two entries sharing one) surfaces
    here too, as a duplicate score.
    """
    payload = _load_json(os.path.join(temp_dir, f"{prefix}_{corpus}_payload.json"))
    expected = [e['id'] for e in payload['entries']]

    chunks = []
    while os.path.exists(os.path.join(temp_dir, f"{prefix}_{kind}_chunk{len(chunks)}.json")):
        data = _load_json(os.path.join(temp_dir, f"{prefix}_scores_{score_kind}{len(chunks)}.json"))
        chunks.append(data['scores'])
    if not chunks:
        raise FileNotFoundError(
            f'no {corpus} chunk files found ({prefix}_{kind}_chunk0.json missing); '
            'run retrieval_payload.py split first')

    anchor_set = set(anchors)
    for idx, chunk in enumerate(chunks):
        ids = [s['id'] for s in chunk]
        off = [f"{a} x{ids.count(a)}" for a in anchors if ids.count(a) != 1]
        if off:
            raise ValueError(f"{corpus} chunk {idx}: calibration anchor not scored exactly once "
                             f"({', '.join(off)}); re-score that chunk")

    scored = [s['id'] for chunk in chunks for s in chunk if s['id'] not in anchor_set]
    scored += [a for a in anchors if a in expected]
    dupes = sorted({i for i in scored if scored.count(i) > 1}
                   | {i for i in expected if expected.count(i) > 1})
    if dupes:
        raise ValueError(f"duplicate {corpus} IDs across score chunks: {', '.join(dupes)} "
                         '(stale chunk file, or two entries sharing one ID?)')
    missing = sorted(set(expected) - set(scored))
    extra = sorted(set(scored) - set(expected) | anchor_set - set(expected))
    if missing or extra:
        problems = ([f"unscored: {', '.join(missing)}"] if missing else []) \
                 + ([f"unexpected: {', '.join(extra)}"] if extra else [])
        raise ValueError(f"{corpus} score coverage mismatch ({'; '.join(problems)})")
    return chunks


# ---------------------------------------------------------------------------
# Calibration
# Theil-Sen: slope = median of the slopes between every pair of anchors,
# offset = median of the residual intercepts. One anchor the scorers truly
# disagree on moves a least-squares line; it barely moves a median. When a
# chunk's anchors span too little score range to fix a slope, only the offset
# is corrected.
# ---------------------------------------------------------------------------

def _fit(xs, ys, min_span):
    """Return (slope, offset, mode) mapping a chunk's raw anchor scores onto consensus."""
    if max(xs) - min(xs) < min_span:
        slope, mode = 1.0, 'offset'
    else:
        pair_slopes = [(ys[j] - ys[i]) / (xs[j] - xs[i])
                       for i in range(len(xs)) for j in range(i + 1, len(xs))
                       if abs(xs[j] - xs[i]) > 1e-9]
        slope, mode = statistics.median(pair_slopes), 'fit'
    offset = statistics.median(y - slope * x for x, y in zip(xs, ys))
    return slope, offset, mode


def calibrate(corpus, chunks, anchors, cal_cfg):
    """Return (merged score list, calibration record) for one chunked corpus."""
    if not anchors:
        return ([s for chunk in chunks for s in chunk],
                {'status': 'not needed', 'chunks': len(chunks), 'anchors': []})

    raw = [{s['id']: s for s in chunk} for chunk in chunks]
    consensus = {a: statistics.mean(r[a]['score'] for r in raw) for a in anchors}
    ys = [consensus[a] for a in anchors]
    lo, hi = cal_cfg['slope_bounds']

    merged, per_chunk = [], []
    for idx, (chunk, r) in enumerate(zip(chunks, raw)):
        xs = [r[a]['score'] for a in anchors]
        slope, offset, mode = _fit(xs, ys, cal_cfg['min_anchor_span'])
        if not lo <= slope <= hi:
            raise ValueError(
                f'{corpus} chunk {idx}: calibration slope {slope:.2f} is outside '
                f'{lo}-{hi}; this scorer ranked the anchors inconsistently with the '
                'other chunks, so its scores cannot be mapped. Re-score that chunk.')

        # Leave-one-out stability: the largest change in this chunk's corrected
        # scores when any single anchor is dropped from the fit.
        loo = 0.0
        if len(anchors) >= 3:
            for k in range(len(anchors)):
                s2, o2, _ = _fit(xs[:k] + xs[k + 1:], ys[:k] + ys[k + 1:], cal_cfg['min_anchor_span'])
                loo = max(loo, max(abs((slope * s['score'] + offset) - (s2 * s['score'] + o2))
                                   for s in chunk))

        # Slope and offset are stored unrounded so a reader can reproduce
        # every corrected score from the record exactly.
        per_chunk.append({
            'chunk': idx, 'mode': mode, 'slope': slope, 'offset': offset,
            'before': round(statistics.mean(abs(x - y) for x, y in zip(xs, ys)), 3),
            'after': round(statistics.mean(abs(_clamp(slope * x + offset) - y)
                                           for x, y in zip(xs, ys)), 3),
            'leave_one_out': round(loo, 3),
        })
        merged += [{**s, 'score': _clamp(slope * s['score'] + offset)}
                   for s in chunk if s['id'] not in consensus]

    # Each anchor keeps its consensus score and the reason from the chunk whose
    # raw score sat closest to it.
    for a in anchors:
        closest = min((r[a] for r in raw), key=lambda s: abs(s['score'] - consensus[a]))
        merged.append({**closest, 'score': _clamp(consensus[a])})

    record = {
        'status': 'applied', 'chunks': len(chunks), 'anchors': list(anchors),
        'before': round(statistics.mean(c['before'] for c in per_chunk), 3),
        'after': round(statistics.mean(c['after'] for c in per_chunk), 3),
        'leave_one_out': max(c['leave_one_out'] for c in per_chunk),
        'per_chunk': per_chunk,
    }
    return merged, record


def _describe(corpus, record):
    """Return plain-English lines describing one corpus's calibration."""
    if record['status'] != 'applied':
        return [f"Calibration ({corpus}): not needed, single chunk."]
    lines = [f"Calibration ({corpus}): {record['chunks']} chunks, {len(record['anchors'])} anchors. "
             f"Anchors disagreed by {record['before']:.3f} on average before correction, "
             f"{record['after']:.3f} after. Dropping any one anchor moves a score by at most "
             f"{record['leave_one_out']:.3f}."]
    for c in record['per_chunk']:
        lines.append(f"  chunk {c['chunk']}: corrected = {c['slope']:.2f} x raw "
                     f"{c['offset']:+.2f} ({'offset only' if c['mode'] == 'offset' else 'line fit'}); "
                     f"anchor gap {c['before']:.3f} -> {c['after']:.3f}")
    return lines


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def merge_scores(slug, app_id, temp_dir):
    """Discover, validate, calibrate, merge, and write all three corpora score files."""
    prefix = f"{slug}_{app_id}"
    os.makedirs(temp_dir, exist_ok=True)  # scratch dir may not exist yet on a fresh run
    _, cfg = _config.load()
    cal_cfg = cfg['retrieval_calibration']
    anchors = _load_json(os.path.join(temp_dir, f"{prefix}_calibration.json"))
    pending = [c for c in ('inventory', 'narratives') if anchors[c]['anchors'] is None]
    if pending:
        raise ValueError(f"calibration anchors pending for {', '.join(pending)}: "
                         'split-anchored has not run, so the chunks after the seed were '
                         'never given anchors (or never scored)')

    # --- Validate and calibrate both chunked corpora before writing either ---
    inv_scores, inv_cal = calibrate('inventory', _collect_chunks(
        temp_dir, prefix, 'inventory', 'inv', 'inventory_chunk', anchors['inventory']['anchors']),
        anchors['inventory']['anchors'], cal_cfg)
    nar_scores, nar_cal = calibrate('narratives', _collect_chunks(
        temp_dir, prefix, 'narratives', 'narr', 'narr_chunk', anchors['narratives']['anchors']),
        anchors['narratives']['anchors'], cal_cfg)

    inv_out = os.path.join(temp_dir, f"{prefix}_inventory_scores.json")
    _write_json(inv_out, {'scores': inv_scores, 'calibration': inv_cal})
    nar_out = os.path.join(temp_dir, f"{prefix}_narrative_scores.json")
    _write_json(nar_out, {'scores': nar_scores, 'calibration': nar_cal})

    # --- Copy themes (single file, no merge or calibration needed) ---
    th_in = os.path.join(temp_dir, f"{prefix}_scores_themes.json")
    th_data = _load_json(th_in)
    th_out = os.path.join(temp_dir, f"{prefix}_theme_scores.json")
    _write_json(th_out, {'scores': th_data['scores']})

    # --- Print confirmation ---
    print(f"Merged inventory: {len(inv_scores)} entries → {inv_out}")
    print(f"Merged narratives: {len(nar_scores)} entries → {nar_out}")
    print(f"Themes: {len(th_data['scores'])} entries → {th_out}")
    for line in _describe('inventory', inv_cal) + _describe('narratives', nar_cal):
        print(line)


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
