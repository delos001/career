#!/usr/bin/env python3
"""
retrieval_apply.py - assemble the retrieval manifest from collected signals

Runs the deterministic portion of the retrieval pipeline and writes the
retrieval manifest. Inputs (paths to JSON files written by the dispatching
skill from subagent output and from the role-intake research artifacts):

  --jd-axes-file              JD axis classification.
  --inventory-scores-file     LLM-judgment scores for the inventory corpus.
  --narrative-scores-file     LLM-judgment scores for the narratives corpus.
  --theme-scores-file         LLM-judgment scores for the themes corpus.
  --folder                    application folder where retrieval.md is written.
  --slug, --app-id, --date    manifest header metadata.

For each EX/PR entry that scored semantically OR matches at least one axis
exactly OR adjacently (the union of the semantic pass and the tag-pull
pass), compute axis exact-match count and axis adjacency-weighted score
using the per-axis-file Adjacency sections in rules/<axis>/<value>.md.

For narratives, union the LLM-judgment scored set with the deterministic
Linked-Inventory walk (every narrative whose Linked Inventory references
an inventory entry already in the manifest).

For themes, use the LLM-judgment scores directly.

Writes a Markdown manifest at <folder>/<retrieval_manifest> per
config.yaml. The manifest exposes raw signals; downstream consumers derive
their own tiers locally (gap analysis: strong/moderate/weak;
CV creation: primary/supporting/drop). See
`retrieval-architecture-2026-05` for the full design rationale.

Author    : Jason Delosh
Created   : 2026-05-26
Project   : career
Usage     : python scripts/retrieval_apply.py assemble --folder ... \\
                --slug ... --app-id ... --date ... \\
                --jd-axes-file ... --inventory-scores-file ... \\
                --narrative-scores-file ... --theme-scores-file ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import retrieval_payload


# ---------------------------------------------------------------------------
# Axis configuration
# Map between display-form axis names ('Industry', 'Specialty', etc.) and the
# folder names under rules/, plus the entry-dict keys used by
# retrieval_payload._parse_inventory_entries. Centralised here so the four
# pipelines (lookup, scoring, tag-pull, manifest write) all agree.
# ---------------------------------------------------------------------------

# (display name, rules folder, entry-dict key on parsed inventory entries).
_AXIS_CONFIG = [
    ('Industry',   'industries',  'industry'),
    ('Specialty',  'specialties', 'specialty'),
    ('Orientation','orientations','orientation'),
    ('Level',      'levels',      'level'),
    ('Work-state', 'work-states', 'work_state'),
]


# ---------------------------------------------------------------------------
# Adjacency lookup
# Each axis file (rules/<axis>/<value>.md) has an '## Adjacency' section
# with bullets of the form '- **<adjacent-value>**: <translation note>'.
# A '### Low or no adjacency' sub-section, if present, lists values that
# are explicitly NOT adjacent and must be excluded from the adjacency set.
# This lookup caches results per (axis-folder, value) to avoid re-reading
# files when the same value comes up across multiple entries.
# ---------------------------------------------------------------------------

# Regex: an adjacency bullet's bolded value name.
_ADJACENCY_BULLET_RE = re.compile(r'^\s*-\s+\*\*([^*]+)\*\*', re.MULTILINE)

# Regex: the '### Low or no adjacency' sub-section heading.
_LOW_ADJ_SUBHEADING_RE = re.compile(r'^###\s+Low\s+or\s+no\s+adjacency', re.MULTILINE)


def _read_adjacency(repo_root, axis_folder, value):
    """Return the list of values declared as adjacent in rules/<axis>/<value>.md.

    Empty list if the value file is missing (e.g. a registry-only or
    file-deferred value) or its Adjacency section is empty or absent.
    The value-file path is looked up against the rules folder; this script
    is intentionally tolerant of missing files so retrieval still runs when
    an axis registry includes deferred entries.
    """
    value_file = os.path.join(repo_root, 'rules', axis_folder, f'{value}.md')
    if not os.path.exists(value_file):
        return []
    text = _util.read(value_file)
    # Find the '## Adjacency' section bounds.
    m_start = re.search(r'(?m)^##\s+Adjacency\s*$', text)
    if not m_start:
        return []
    section_start = m_start.end()
    # Section ends at the next '## ' top-level heading (or end of file).
    m_end = re.search(r'(?m)^##\s+', text[section_start:])
    section_end = section_start + m_end.start() if m_end else len(text)
    section_body = text[section_start:section_end]
    # If there is a 'Low or no adjacency' subheading, cap the adjacent-bullets
    # scan there: bullets after that subheading are explicit non-adjacencies.
    m_low = _LOW_ADJ_SUBHEADING_RE.search(section_body)
    scan_body = section_body[:m_low.start()] if m_low else section_body
    return [m.group(1).strip() for m in _ADJACENCY_BULLET_RE.finditer(scan_body)]


# Cache: avoid re-reading the same value file for every entry that references it.
_ADJ_CACHE = {}


def _adjacency_for(repo_root, axis_folder, value):
    """Cached wrapper around _read_adjacency."""
    key = (axis_folder, value)
    if key not in _ADJ_CACHE:
        _ADJ_CACHE[key] = _read_adjacency(repo_root, axis_folder, value)
    return _ADJ_CACHE[key]


# ---------------------------------------------------------------------------
# Per-axis scoring
# Given a JD axis value (primary + optional secondary) and an entry's list of
# values for that axis, return (exact_match_bool, axis_score). axis_score is
# 1.0 for an exact match against primary or secondary, 0.5 for an adjacency
# match against primary or secondary, and 0.0 for no match. Multi-value
# entries take the max over their values.
# ---------------------------------------------------------------------------

# Default adjacency weight per `retrieval-architecture-2026-05`.
_ADJACENCY_WEIGHT = 0.5


def _score_axis(repo_root, axis_folder, jd_primary, jd_secondary, entry_values):
    """Return (exact_match, score) for one axis."""
    if not entry_values:
        return False, 0.0
    exact = False
    best = 0.0
    for jd_value in filter(None, (jd_primary, jd_secondary)):
        adjacency = set(_adjacency_for(repo_root, axis_folder, jd_value))
        for entry_value in entry_values:
            if entry_value == jd_value:
                exact = True
                best = 1.0
            elif entry_value in adjacency:
                # Only upgrade to adjacency-weight if no exact match has fired
                # for this entry's axis yet. The exact flag stays as-is.
                best = max(best, _ADJACENCY_WEIGHT)
    return exact, best


# ---------------------------------------------------------------------------
# Per-entry total axis signals
# Sum across all five axes to produce the two manifest columns:
#   exact_match_count (int 0..5): number of axes with at least one exact
#     match between an entry value and the JD primary or secondary value.
#   adjacency_weighted_score (float 0..5): sum of per-axis scores.
# ---------------------------------------------------------------------------

def _compute_entry_axis_signals(repo_root, jd_axes, entry):
    """Compute (exact_count, adjacency_weighted, per_axis_detail) for an entry."""
    exact_count = 0
    weighted_sum = 0.0
    detail = {}
    for display_name, axis_folder, entry_key in _AXIS_CONFIG:
        jd_block = jd_axes.get(display_name, {}) or {}
        jd_primary = jd_block.get('primary')
        jd_secondary = jd_block.get('secondary')
        entry_values = entry.get(entry_key, []) or []
        exact, score = _score_axis(
            repo_root, axis_folder, jd_primary, jd_secondary, entry_values
        )
        if exact:
            exact_count += 1
        weighted_sum += score
        detail[display_name] = {
            'exact': exact,
            'score': score,
            'entry_values': entry_values,
            'jd_primary': jd_primary,
            'jd_secondary': jd_secondary,
        }
    return exact_count, round(weighted_sum, 2), detail


# ---------------------------------------------------------------------------
# Manifest assembly
# Build the per-corpus tables in order: inventory, narratives, themes.
# Inventory takes the union of semantic-scored and tag-pull candidates.
# Narratives takes the union of semantic-scored and Linked-Inventory walk.
# Themes uses the semantic scores directly (no deterministic supplement).
# ---------------------------------------------------------------------------

def _build_inventory_rows(repo_root, jd_axes, inventory_entries, semantic_scores,
                          role_companies):
    """Build the inventory rows; returns list of dicts ready for table render.

    Each row carries: id, employer, semantic, exact_count, adjacency_score,
    in_semantic, in_tag_pull, axis_match_summary, reason. `employer` resolves the
    entry's Role tag to its company via role_companies so downstream consumers
    (CV creation especially) place each entry under the right employer.
    """
    # Index entries by ID for fast lookup.
    by_id = {e['id']: e for e in inventory_entries}
    # Index semantic scores by ID.
    semantic_by_id = {row['id']: row for row in semantic_scores}
    rows = []
    seen_ids = set()
    # First pass: every entry that scored semantically (regardless of axis match).
    for entry in inventory_entries:
        eid = entry['id']
        if eid not in semantic_by_id:
            continue
        seen_ids.add(eid)
        exact, weighted, detail = _compute_entry_axis_signals(
            repo_root, jd_axes, entry
        )
        rows.append({
            'id': eid,
            'employer': role_companies.get(entry.get('role', ''), ''),
            'semantic': semantic_by_id[eid].get('score'),
            'exact_count': exact,
            'adjacency_score': weighted,
            'in_semantic': True,
            'in_tag_pull': exact >= 1 or weighted >= _ADJACENCY_WEIGHT,
            'axis_summary': _axis_summary(detail),
            'reason': semantic_by_id[eid].get('reason', ''),
        })
    # Second pass: tag-pull entries that the semantic pass missed.
    # Inclusion criterion: at least one axis exact OR adjacent match.
    for entry in inventory_entries:
        eid = entry['id']
        if eid in seen_ids:
            continue
        exact, weighted, detail = _compute_entry_axis_signals(
            repo_root, jd_axes, entry
        )
        if exact >= 1 or weighted >= _ADJACENCY_WEIGHT:
            rows.append({
                'id': eid,
                'employer': role_companies.get(entry.get('role', ''), ''),
                'semantic': None,
                'exact_count': exact,
                'adjacency_score': weighted,
                'in_semantic': False,
                'in_tag_pull': True,
                'axis_summary': _axis_summary(detail),
                'reason': 'tag-pull only',
            })
    # Sort: primary by semantic score desc (None last), secondary by axis
    # exact-count desc, tertiary by adjacency-weighted score desc.
    rows.sort(key=lambda r: (
        -(r['semantic'] if r['semantic'] is not None else -1),
        -r['exact_count'],
        -r['adjacency_score'],
    ))
    return rows


def _axis_summary(detail):
    """Return a compact string summarising which axes matched and how."""
    parts = []
    for axis_name in ('Industry', 'Specialty', 'Orientation', 'Level', 'Work-state'):
        block = detail.get(axis_name, {})
        if block.get('exact'):
            parts.append(f'{axis_name}=exact')
        elif block.get('score', 0) >= _ADJACENCY_WEIGHT:
            parts.append(f'{axis_name}=adjacent')
    return ', '.join(parts) if parts else 'none'


def _build_narrative_rows(narratives, narrative_scores, inventory_ids_in_manifest):
    """Build narrative rows; union semantic-scored set with Linked-Inventory walk."""
    by_id = {n['id']: n for n in narratives}
    semantic_by_id = {row['id']: row for row in narrative_scores}
    in_manifest = set(inventory_ids_in_manifest)
    rows = []
    seen_ids = set()
    # Semantic-scored narratives first.
    for nar in narratives:
        nid = nar['id']
        if nid not in semantic_by_id:
            continue
        seen_ids.add(nid)
        linked = nar.get('linked_inventory', []) or []
        triggered_by = [eid for eid in linked if eid in in_manifest]
        rows.append({
            'id': nid,
            'semantic': semantic_by_id[nid].get('score'),
            'linked_from': triggered_by,
            'has_linkage': bool(triggered_by),
            'reason': semantic_by_id[nid].get('reason', ''),
        })
    # Linked-inventory walk: narratives whose Linked Inventory points to any
    # manifest inventory entry but did not score semantically above threshold.
    for nar in narratives:
        nid = nar['id']
        if nid in seen_ids:
            continue
        linked = nar.get('linked_inventory', []) or []
        triggered_by = [eid for eid in linked if eid in in_manifest]
        if triggered_by:
            rows.append({
                'id': nid,
                'semantic': None,
                'linked_from': triggered_by,
                'has_linkage': True,
                'reason': 'linkage-only',
            })
    # Sort: by semantic desc (None last), then by linkage count desc.
    rows.sort(key=lambda r: (
        -(r['semantic'] if r['semantic'] is not None else -1),
        -len(r['linked_from']),
    ))
    return rows


def _build_theme_rows(themes, theme_scores):
    """Build theme rows from semantic scores; no deterministic supplement."""
    by_id = {t['id']: t for t in themes}
    rows = []
    for row in theme_scores:
        tid = row.get('id')
        if tid not in by_id:
            # Score references a theme we did not find in positioning.md.
            # Surface it anyway so the user sees the inconsistency.
            rows.append({
                'id': tid,
                'semantic': row.get('score'),
                'title': '(not in positioning.md)',
                'reason': row.get('reason', ''),
            })
            continue
        rows.append({
            'id': tid,
            'semantic': row.get('score'),
            'title': by_id[tid].get('title', ''),
            'reason': row.get('reason', ''),
        })
    rows.sort(key=lambda r: -(r['semantic'] if r['semantic'] is not None else -1))
    return rows


# ---------------------------------------------------------------------------
# Markdown table rendering
# Renders the three tables (inventory, narratives, themes) into the manifest.
# Float formatting keeps columns aligned; None scores render as '-'.
# ---------------------------------------------------------------------------

def _fmt_score(value):
    """Format a 0..1 float as 0.NN, or '-' if None."""
    if value is None:
        return '-'
    return f'{value:.2f}'


def _render_inventory_table(rows):
    if not rows:
        return '_(no inventory entries surfaced)_'
    lines = [
        '| ID | Employer | Semantic | Axis exact | Axis adj | Source | Axis matches | Reason |',
        '|----|----------|----------|-----------|----------|--------|---------------|--------|',
    ]
    for r in rows:
        sources = []
        if r['in_semantic']:
            sources.append('semantic')
        if r['in_tag_pull']:
            sources.append('tag-pull')
        lines.append(
            f"| {r['id']} | {_escape_pipe(r.get('employer', ''))} | "
            f"{_fmt_score(r['semantic'])} | {r['exact_count']} | "
            f"{r['adjacency_score']:.2f} | {'+'.join(sources)} | "
            f"{r['axis_summary']} | {_escape_pipe(r['reason'])} |"
        )
    return '\n'.join(lines)


def _render_narrative_table(rows):
    if not rows:
        return '_(no narratives surfaced)_'
    lines = [
        '| ID | Semantic | Linked from | Reason |',
        '|----|----------|-------------|--------|',
    ]
    for r in rows:
        linked = ', '.join(r['linked_from']) if r['linked_from'] else '-'
        lines.append(
            f"| {r['id']} | {_fmt_score(r['semantic'])} | "
            f"{linked} | {_escape_pipe(r['reason'])} |"
        )
    return '\n'.join(lines)


def _render_theme_table(rows):
    if not rows:
        return '_(no themes triggered)_'
    lines = [
        '| ID | Semantic | Title | Reason |',
        '|----|----------|-------|--------|',
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {_fmt_score(r['semantic'])} | "
            f"{_escape_pipe(r['title'])} | {_escape_pipe(r['reason'])} |"
        )
    return '\n'.join(lines)


def _escape_pipe(text):
    """Escape '|' so it does not break Markdown table cells."""
    if text is None:
        return ''
    return text.replace('|', '\\|').replace('\n', ' ').strip()


# ---------------------------------------------------------------------------
# Manifest write
# Renders the complete retrieval.md file under the application folder. The
# manifest is a current-state document: re-running retrieval overwrites it,
# does not accumulate history. Path comes from config.yaml retrieval_manifest.
# ---------------------------------------------------------------------------

def _render_manifest(slug, app_id, date, jd_axes, inventory_rows, narrative_rows, theme_rows):
    """Render the complete manifest markdown."""
    axis_lines = []
    for display_name, _, _ in _AXIS_CONFIG:
        block = jd_axes.get(display_name, {}) or {}
        primary = block.get('primary') or '_(not classified)_'
        secondary = block.get('secondary')
        if secondary:
            axis_lines.append(f'- **{display_name}:** {primary} (primary), {secondary} (secondary)')
        else:
            axis_lines.append(f'- **{display_name}:** {primary}')
    axis_block = '\n'.join(axis_lines)
    parts = [
        f'# Retrieval Manifest: {slug} | {app_id}',
        '',
        f'**Generated:** {date}',
        '',
        '**JD axis classification (from research.md):**',
        axis_block,
        '',
        '**Signal columns:** `Employer` is the entry\'s company, resolved from its '
        'Role tag, so each entry can be placed under the right employer without '
        're-deriving it. `Semantic` is the LLM-judgment score against the '
        'critical requirements list (0.00 to 1.00; `-` means the entry was not '
        'in the semantic-scored set). `Axis exact` counts axes with an exact '
        'value match against the JD (0..5). `Axis adj` is the adjacency-weighted '
        'axis score (exact = 1.0; adjacent per axis file = 0.5; sum across the '
        'five axes). `Source` records which retrieval pass surfaced the entry. '
        'Downstream consumers (gap analysis, CV creation, interview prep) '
        'derive their own tiers from these raw signals.',
        '',
        '## Inventory candidates',
        '',
        _render_inventory_table(inventory_rows),
        '',
        '## Narratives',
        '',
        _render_narrative_table(narrative_rows),
        '',
        '## Triggered themes',
        '',
        _render_theme_table(theme_rows),
        '',
    ]
    return '\n'.join(parts)


# ---------------------------------------------------------------------------
# Subcommand: assemble
# Reads all input JSON files, runs deterministic computations, writes the
# manifest. Echoes the manifest path on stdout so the calling skill can
# display it to the user.
# ---------------------------------------------------------------------------

def cmd_assemble(args, repo_root, cfg):
    """Read inputs, compute signals, write the manifest, echo the path."""
    jd_axes = _util.load_json(args.jd_axes_file)
    inv_scores_doc = _util.load_json(args.inventory_scores_file)
    nar_scores_doc = _util.load_json(args.narrative_scores_file)
    th_scores_doc = _util.load_json(args.theme_scores_file)
    inv_scores = inv_scores_doc.get('scores', inv_scores_doc) if isinstance(inv_scores_doc, dict) else inv_scores_doc
    nar_scores = nar_scores_doc.get('scores', nar_scores_doc) if isinstance(nar_scores_doc, dict) else nar_scores_doc
    th_scores = th_scores_doc.get('scores', th_scores_doc) if isinstance(th_scores_doc, dict) else th_scores_doc

    # Re-parse the profile documents for full entry detail (the scores carry
    # only IDs + numbers; we need tags for axis scoring and Linked Inventory
    # for the narrative walk).
    inventory_text = _util.read(
        os.path.join(repo_root, cfg['paths']['profile'], cfg['filenames']['inventory_file'])
    )
    narratives_text = _util.read(
        os.path.join(repo_root, cfg['paths']['profile'], cfg['filenames']['narratives_file'])
    )
    positioning_text = _util.read(
        os.path.join(repo_root, cfg['paths']['profile'], cfg['filenames']['positioning_file'])
    )
    inventory_entries = retrieval_payload.parse_inventory_entries(inventory_text)
    role_companies = retrieval_payload.parse_role_companies(inventory_text)
    narratives = retrieval_payload.parse_narratives(narratives_text)
    themes = retrieval_payload.parse_themes(positioning_text)

    inventory_rows = _build_inventory_rows(
        repo_root, jd_axes, inventory_entries, inv_scores, role_companies
    )
    inv_ids_in_manifest = [r['id'] for r in inventory_rows]
    narrative_rows = _build_narrative_rows(
        narratives, nar_scores, inv_ids_in_manifest
    )
    theme_rows = _build_theme_rows(themes, th_scores)

    manifest = _render_manifest(
        args.slug, args.app_id, args.date, jd_axes,
        inventory_rows, narrative_rows, theme_rows,
    )

    manifest_path = os.path.join(args.folder, cfg['filenames']['retrieval_manifest'])
    _util.write(manifest_path, manifest)
    print(manifest_path)


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch the assemble subcommand."""
    parser = argparse.ArgumentParser(
        description='assemble the retrieval manifest from collected signals'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_asm = sub.add_parser('assemble', help='assemble and write retrieval.md')
    p_asm.add_argument('--folder', required=True,
                       help='application folder (where retrieval.md is written)')
    p_asm.add_argument('--slug', required=True)
    p_asm.add_argument('--app-id', required=True)
    p_asm.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_asm.add_argument('--jd-axes-file', required=True,
                       help='JSON: per-axis {primary, secondary} blocks')
    p_asm.add_argument('--inventory-scores-file', required=True,
                       help='JSON: scorer subagent output for the inventory corpus')
    p_asm.add_argument('--narrative-scores-file', required=True,
                       help='JSON: scorer subagent output for the narratives corpus')
    p_asm.add_argument('--theme-scores-file', required=True,
                       help='JSON: scorer subagent output for the themes corpus')
    p_asm.set_defaults(func=cmd_assemble)

    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
