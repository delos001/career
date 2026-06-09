#!/usr/bin/env python3
"""
retrieval_payload.py - build LLM-consumable payloads for the retrieval skill

Reads the candidate profile documents (inventory.md, narratives.md,
positioning.md) and emits the per-corpus payload that the retrieval-scorer
subagent consumes alongside the critical requirements list. Three subcommands:

  inventory   Read every EX/PR entry in inventory.md and emit a JSON list of
              chunks, each chunk containing up to N entries (default 50,
              configurable via --chunk-size). Each entry carries its ID, tag
              axes, and a concatenated 'Description + Impact' payload text.
              Chunking mitigates attention degradation when the LLM ranks long
              lists in a single prompt.
  narratives  Read narratives.md and emit a JSON list of every narrative
              (ST-NNN and DC-NNN) with its ID, Linked Inventory IDs, and a
              concatenated body payload. One LLM call sees the whole list.
  themes      Read positioning.md and emit a JSON list of every Signature
              Theme (TH-NNN) with Core message + Proof point + Use when
              triggers concatenated. One LLM call sees the whole list.
  split       Read the three payload files previously written to the temp
              directory, write one JSON file per inventory chunk, and print
              a plain-English summary (chunk count, sizes, narrative count,
              theme count). Eliminates the need for ad-hoc inline Python
              between Phase 2 (build payloads) and Phase 3 (score).

Nothing repo-dependent is hardcoded; folder locations and filenames come from
config.yaml. The script does not invoke any LLM itself: it only prepares
inputs and writes structured JSON to stdout.

Author    : Jason Delosh
Created   : 2026-05-26
Project   : career
Usage     : python scripts/retrieval_payload.py inventory [--chunk-size 50]
            python scripts/retrieval_payload.py narratives
            python scripts/retrieval_payload.py themes
            python scripts/retrieval_payload.py split --slug <slug> --app-id <APP-NNN> [--temp-dir temp]
Depends   : pyyaml (via _config)
"""

import argparse
import json
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Path helpers
# Resolve absolute paths of the three profile files we read here. Filenames
# come from config.yaml so a rename is a config edit, not a code change.
# ---------------------------------------------------------------------------

def _inventory_path(repo_root, cfg):
    return os.path.join(
        repo_root, cfg['paths']['profile'], cfg['filenames']['inventory_file']
    )


def _narratives_path(repo_root, cfg):
    return os.path.join(
        repo_root, cfg['paths']['profile'], cfg['filenames']['narratives_file']
    )


def _positioning_path(repo_root, cfg):
    return os.path.join(
        repo_root, cfg['paths']['profile'], cfg['filenames']['positioning_file']
    )


# ---------------------------------------------------------------------------
# Inventory entry parsing
# Retrievable entries (EX-NNN, PR-NNN) live in Section 8 (Experience Entries)
# and Section 9 (Independent & Volunteer Projects). Each entry begins with
# 'ID: <id>' and carries the axis-tag lines (Industry, Specialty, Orientation,
# Level, Work-state), the Description, and the Impact; PR entries also carry a
# 'Company:' line (no Role: RL reference). The parser scans the whole document
# by the anchored 'ID:' marker rather than a hardcoded section number, so it
# stays correct across section renumbering. It extracts the fields we need and
# concatenates Description + Impact into a 'payload' text the LLM judges.
# ---------------------------------------------------------------------------

# Regex: a line that opens an inventory entry. Captures the ID.
_ENTRY_RE = re.compile(r'^ID:\s+((?:EX|PR)-\d+)\s*$')

# Regex: a tag line (e.g. 'Industry: pharma', 'Specialty: clinical-operations | data-science').
_TAG_RE = re.compile(r'^(Industry|Specialty|Orientation|Level|Work-state):\s*(.*)$')

# Regex: the Description and Impact fields. The values may run for one line.
# Context is intentionally not captured; payload is Description + Impact per
# `retrieval-architecture-2026-05`.
_FIELD_RE = re.compile(r'^(Description|Impact):\s*(.*)$')

# Regex: the Role tag linking an entry to its RL role record (its employer).
_ROLE_RE = re.compile(r'^Role:\s+(RL-\d+)\s*$')

# Regexes for Section 7 role records: the RL id line and its employer (Company).
_ROLE_ENTRY_RE = re.compile(r'^ID:\s+(RL-\d+)\s*$')
_COMPANY_RE = re.compile(r'^Company:\s*(.+?)\s*$')

# The five tag axes the retrieval pipeline cares about.
_AXES = ('Industry', 'Specialty', 'Orientation', 'Level', 'Work-state')


def _split_pipe_values(raw):
    """Split a pipe-delimited tag value into a list, trimmed of whitespace."""
    return [v.strip() for v in raw.split('|') if v.strip()]


def _section_bounds(text, heading_prefix):
    """Return (start, end) line indices of the section opened by heading_prefix.

    heading_prefix is the line text including the '## ' / '### ' prefix, e.g.
    '## 8. Experience Entries'. The section ends at the next heading at
    equal or shallower depth.
    """
    lines = text.split('\n')
    depth = len(heading_prefix) - len(heading_prefix.lstrip('#'))
    start = None
    for i, line in enumerate(lines):
        if line.startswith(heading_prefix):
            start = i
            break
    if start is None:
        raise ValueError(f'section not found: {heading_prefix!r}')
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r'^(#+)\s+', lines[j])
        if m and len(m.group(1)) <= depth:
            end = j
            break
    return start, end


def _parse_inventory_entries(inventory_text):
    """Walk every EX/PR entry in inventory.md, returning a list of entry dicts.

    Each dict carries: id, role (str; EX entries reference an RL record),
    company (str; PR entries carry their employer directly), industry (list),
    specialty (list), orientation (list), level (list), work_state (list),
    description (str), impact (str), payload (str = Description + ' ' + Impact,
    both trimmed).

    Entries are matched anywhere in the document by their anchored
    'ID: EX-NNN' / 'ID: PR-NNN' opener (currently Section 8 Experience Entries
    and Section 9 Independent & Volunteer Projects). Scanning by entry marker
    rather than a hardcoded section number keeps the parser stable across
    section renumbering (cf. the 9<->10 swap in
    `experience-inventory-section-ordering`). A new '## ' section heading
    closes the open entry, so a non-entry section (e.g. Academic Coursework
    Detail) cannot bleed into the last entry's fields.
    """
    lines = inventory_text.split('\n')
    entries = []
    current = None
    for line in lines:
        m = _ENTRY_RE.match(line)
        if m:
            # New entry starts; flush the previous one.
            if current is not None:
                entries.append(_finalise_entry(current))
            current = {
                'id': m.group(1),
                'role': '',
                'company': '',
                'industry': [],
                'specialty': [],
                'orientation': [],
                'level': [],
                'work_state': [],
                'description': '',
                'impact': '',
            }
            continue
        # A new section heading ('## ') closes the current entry and resets
        # state, bounding each entry to its own section without hardcoding a
        # section number. '### RL-NNN' role-grouping subheaders are h3 and do
        # not match, so they leave the open entry untouched.
        if line.startswith('## '):
            if current is not None:
                entries.append(_finalise_entry(current))
                current = None
            continue
        if current is None:
            # Before the first entry, or between an entry's section and the
            # next (e.g. the '### RL-NNN' role-grouping subheaders). Skip.
            continue
        m = _ROLE_RE.match(line)
        if m:
            current['role'] = m.group(1)
            continue
        m = _COMPANY_RE.match(line)
        if m:
            # PR entries name their employer directly; EX entries have no
            # Company line, so this only populates PR entries.
            current['company'] = m.group(1).strip()
            continue
        m = _TAG_RE.match(line)
        if m:
            axis_key = m.group(1).lower().replace('-', '_')
            current[axis_key] = _split_pipe_values(m.group(2))
            continue
        m = _FIELD_RE.match(line)
        if m:
            # Description and Impact are single-line in the current convention;
            # if a future schema spans multiple lines, this parser will need a
            # multi-line continuation rule.
            field = m.group(1).lower()
            current[field] = m.group(2).strip()
            continue
    # Flush the last entry.
    if current is not None:
        entries.append(_finalise_entry(current))
    return entries


def _parse_role_companies(inventory_text):
    """Walk Section 7 (Employment & Role History); return {RL-NNN: company}.

    Each role record opens with 'ID: RL-NNN' and carries a 'Company:' line. This
    resolves an entry's Role tag to its employer for the retrieval manifest. Empty
    dict if the section is absent.
    """
    try:
        sec_start, sec_end = _section_bounds(inventory_text, '## 7. ')
    except ValueError:
        return {}
    lines = inventory_text.split('\n')
    companies = {}
    current_rl = None
    for i in range(sec_start, sec_end):
        line = lines[i]
        m = _ROLE_ENTRY_RE.match(line)
        if m:
            current_rl = m.group(1)
            continue
        if current_rl is not None:
            m = _COMPANY_RE.match(line)
            if m:
                companies[current_rl] = m.group(1).strip()
                current_rl = None
    return companies


def _finalise_entry(entry):
    """Compute the LLM payload text and return the finalised entry dict."""
    # Strip Markdown bold markers from Description so the payload reads cleanly.
    description = re.sub(r'\*\*', '', entry['description']).strip()
    impact = entry['impact'].strip()
    parts = [description]
    if impact:
        parts.append(impact)
    entry['payload'] = ' '.join(parts).strip()
    return entry


# ---------------------------------------------------------------------------
# Inventory chunking
# Split the parsed entry list into chunks of up to chunk_size entries each.
# The retrieval skill dispatches one scorer subagent per chunk in parallel.
# Smaller chunks improve attention quality at the cost of more LLM calls.
# ---------------------------------------------------------------------------

def _chunk_entries(entries, chunk_size):
    """Yield successive sublists of length up to chunk_size."""
    for i in range(0, len(entries), chunk_size):
        yield entries[i:i + chunk_size]


def cmd_inventory(args, repo_root, cfg):
    """Build inventory payload chunks and write JSON to stdout."""
    inventory_text = _util.read(_inventory_path(repo_root, cfg))
    entries = _parse_inventory_entries(inventory_text)
    chunks = []
    for chunk_index, sublist in enumerate(_chunk_entries(entries, args.chunk_size)):
        chunks.append({
            'index': chunk_index,
            'entries': sublist,
        })
    payload = {
        'corpus': 'inventory',
        'chunk_size': args.chunk_size,
        'entry_count': len(entries),
        'chunk_count': len(chunks),
        'chunks': chunks,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write('\n')


# ---------------------------------------------------------------------------
# Narratives parsing
# Walk narratives.md and emit one record per ST-NNN / DC-NNN. Each record
# carries ID, Linked Inventory IDs (parsed from the 'Linked Inventory:' line),
# and a payload text built from the narrative body (title + sections up to
# but not including 'Value Translation' / 'Outcome' which can over-emphasise
# specific phrasing). The retrieval skill sends the whole list to one
# scorer subagent invocation (narratives corpus is small).
# ---------------------------------------------------------------------------

# Regex: a '## <Title>' heading marks the start of a narrative.
_NARRATIVE_HEADING_RE = re.compile(r'^##\s+(.+?)\s*$')

# Regex: the 'ID: ST-NNN' or 'ID: DC-NNN' line inside a narrative.
_NARRATIVE_ID_RE = re.compile(r'^ID:\s+((?:ST|DC)-\d+)\s*$')

# Regex: the 'Linked Inventory: EX-NNN | PR-NNN | ...' line.
_LINKED_RE = re.compile(r'^Linked Inventory:\s*(.*)$')


def _parse_narratives(narratives_text):
    """Walk narratives.md, returning a list of narrative dicts.

    Each dict carries: id, title, linked_inventory (list of EX/PR IDs),
    body (full text of the narrative block from heading through next
    heading), payload (the body, used as semantic input).
    """
    lines = narratives_text.split('\n')
    # Index every '## ' heading position so we know the bounds of each narrative.
    h2_indices = [i for i, line in enumerate(lines) if line.startswith('## ')]
    narratives = []
    for idx, start in enumerate(h2_indices):
        # Initial end is the next '## ' heading; tighten on intervening '# ' too.
        end = (
            h2_indices[idx + 1]
            if idx + 1 < len(h2_indices)
            else len(lines)
        )
        for k in range(start + 1, end):
            if lines[k].startswith('# ') and not lines[k].startswith('## '):
                end = k
                break
        # Extract metadata fields from the block.
        block_lines = lines[start:end]
        nid = None
        linked = []
        title = ''
        m = _NARRATIVE_HEADING_RE.match(lines[start])
        if m:
            title = m.group(1).strip()
        for body_line in block_lines[1:]:
            m = _NARRATIVE_ID_RE.match(body_line)
            if m:
                nid = m.group(1)
                continue
            m = _LINKED_RE.match(body_line)
            if m:
                linked = _split_pipe_values(m.group(1))
                continue
        # Skip section blocks under '## ' that do not carry a narrative ID
        # (e.g. the '## Table of Contents' under '# Career Narratives').
        if nid is None:
            continue
        body_text = '\n'.join(block_lines).strip()
        narratives.append({
            'id': nid,
            'title': title,
            'linked_inventory': linked,
            'body': body_text,
            'payload': body_text,
        })
    return narratives


def cmd_narratives(args, repo_root, cfg):
    """Build narratives payload and write JSON to stdout."""
    narratives_text = _util.read(_narratives_path(repo_root, cfg))
    narratives = _parse_narratives(narratives_text)
    payload = {
        'corpus': 'narratives',
        'entry_count': len(narratives),
        'entries': narratives,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write('\n')


# ---------------------------------------------------------------------------
# Themes parsing
# Walk positioning.md and emit one record per TH-NNN. Each record carries
# ID, title, Core message, Proof point, Use when triggers, and a payload
# string that concatenates Core message + Proof point + Use when (per the
# OR-semantics decision in retrieval-architecture-2026-05).
# ---------------------------------------------------------------------------

# Regex: a '## TH-NNN <title>' heading marks the start of a theme.
_THEME_HEADING_RE = re.compile(r'^##\s+(TH-\d+)\s+(.+?)\s*$')

# Regex: the bolded labelled fields inside a theme block.
_BOLD_LABEL_RE = re.compile(r'^[-\s]*\*\*(Core message|Proof point|Use when):\*\*\s*(.*)$')


def _parse_themes(positioning_text):
    """Walk positioning.md, returning a list of Signature Theme dicts."""
    lines = positioning_text.split('\n')
    h2_indices = [i for i, line in enumerate(lines) if line.startswith('## ')]
    themes = []
    for idx, start in enumerate(h2_indices):
        m = _THEME_HEADING_RE.match(lines[start])
        if not m:
            continue
        tid = m.group(1)
        title = m.group(2).strip()
        end = (
            h2_indices[idx + 1]
            if idx + 1 < len(h2_indices)
            else len(lines)
        )
        for k in range(start + 1, end):
            if lines[k].startswith('# ') and not lines[k].startswith('## '):
                end = k
                break
        fields = {'core_message': '', 'proof_point': '', 'use_when': ''}
        for body_line in lines[start + 1:end]:
            m = _BOLD_LABEL_RE.match(body_line)
            if m:
                label = m.group(1).lower().replace(' ', '_')
                fields[label] = m.group(2).strip()
        payload_parts = [fields['core_message'], fields['proof_point'], fields['use_when']]
        payload = ' | '.join(p for p in payload_parts if p)
        themes.append({
            'id': tid,
            'title': title,
            **fields,
            'payload': payload,
        })
    return themes


def cmd_themes(args, repo_root, cfg):
    """Build themes payload and write JSON to stdout."""
    positioning_text = _util.read(_positioning_path(repo_root, cfg))
    themes = _parse_themes(positioning_text)
    payload = {
        'corpus': 'themes',
        'entry_count': len(themes),
        'entries': themes,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write('\n')


# ---------------------------------------------------------------------------
# Split subcommand
# After the three payload files are written, this subcommand splits them into
# one JSON file per inventory chunk and one JSON file per narrative entry, then
# prints a summary so the calling skill knows exactly which files to pass to
# scorer agents. Eliminates ad-hoc inline Python between Phase 2 and Phase 3
# and guarantees each scorer reads a bounded file rather than a large payload.
# ---------------------------------------------------------------------------

def cmd_split(args, repo_root, cfg):
    """Split payload files into per-chunk and per-narrative files; print summary."""
    prefix = f"{args.slug}_{args.app_id}"
    temp_dir = args.temp_dir
    os.makedirs(temp_dir, exist_ok=True)  # scratch dir may not exist yet on a fresh run

    inv_path = os.path.join(temp_dir, f"{prefix}_inventory_payload.json")
    nar_path = os.path.join(temp_dir, f"{prefix}_narratives_payload.json")
    th_path  = os.path.join(temp_dir, f"{prefix}_themes_payload.json")

    with open(inv_path, encoding='utf-8') as f:
        inv_data = json.load(f)
    with open(nar_path, encoding='utf-8') as f:
        nar_data = json.load(f)
    with open(th_path, encoding='utf-8') as f:
        th_data = json.load(f)

    # Write one file per inventory chunk.
    chunk_paths = []
    for chunk in inv_data['chunks']:
        idx = chunk['index']
        out_path = os.path.join(temp_dir, f"{prefix}_inv_chunk{idx}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(
                {'corpus': 'inventory', 'chunk_index': idx, 'entries': chunk['entries']},
                f,
                ensure_ascii=False,
            )
        chunk_paths.append((out_path, len(chunk['entries'])))

    # Write one file per narrative entry. Narrative bodies can be large enough
    # that a single payload file exceeds the Read tool token cap; individual
    # files guarantee each scorer invocation reads a bounded amount.
    narrative_paths = []
    for entry in nar_data['entries']:
        nid = entry['id']
        out_path = os.path.join(temp_dir, f"{prefix}_narrative_{nid}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump({'corpus': 'narratives', 'entry': entry}, f, ensure_ascii=False)
        narrative_paths.append(out_path)

    # Print summary.
    sizes = '+'.join(str(n) for _, n in chunk_paths)
    print(f"Inventory: {inv_data['chunk_count']} chunks written ({sizes} = {inv_data['entry_count']} entries)")
    for path, size in chunk_paths:
        print(f"  {path} ({size} entries)")
    print(f"Narratives: {nar_data['entry_count']} entries written")
    for path in narrative_paths:
        print(f"  {path}")
    print(f"Themes: {th_data['entry_count']} entries (use {prefix}_themes_payload.json)")


# ---------------------------------------------------------------------------
# Cross-script helpers
# retrieval_apply.py imports these parsers to re-resolve full entry detail
# at manifest-assembly time (the scorer subagent's JSON output carries only
# IDs and numbers; tags and linkage live in the profile documents).
# ---------------------------------------------------------------------------

parse_inventory_entries = _parse_inventory_entries
parse_role_companies = _parse_role_companies
parse_narratives = _parse_narratives
parse_themes = _parse_themes


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses the subcommand and arguments, loads config, runs the subcommand,
# and reports failure to stderr with exit 1 so the calling skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch to the selected subcommand."""
    parser = argparse.ArgumentParser(
        description='build LLM payloads for the retrieval skill'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # --- Subparser: inventory ---
    p_inv = sub.add_parser('inventory', help='build chunked inventory payload')
    p_inv.add_argument(
        '--chunk-size', type=int, default=50,
        help='maximum entries per chunk (default 50)',
    )
    p_inv.set_defaults(func=cmd_inventory)

    # --- Subparser: narratives ---
    p_nar = sub.add_parser('narratives', help='build narratives payload')
    p_nar.set_defaults(func=cmd_narratives)

    # --- Subparser: themes ---
    p_th = sub.add_parser('themes', help='build Signature Themes payload')
    p_th.set_defaults(func=cmd_themes)

    # --- Subparser: split ---
    p_split = sub.add_parser(
        'split', help='split payload files into per-chunk files and print summary'
    )
    p_split.add_argument('--slug', required=True, help='role slug (e.g. takeda)')
    p_split.add_argument('--app-id', required=True, help='application ID (e.g. APP-006)')
    p_split.add_argument('--temp-dir', default='temp', help='temp directory (default: temp)')
    p_split.set_defaults(func=cmd_split)

    args = parser.parse_args()

    # --- Dispatch ---
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
