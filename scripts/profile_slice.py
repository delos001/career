#!/usr/bin/env python3
"""
profile_slice.py - deterministic slicer for the candidate profile documents

Returns individual ID-keyed entries or named sections from the profile
documents in personal/profile/. Used by the retrieval skill (to fetch full
content for IDs listed in its manifest) and by every downstream skill that
needs to load specific profile content on demand without reading the whole
document into context.

Two subcommands:

  id      Fetch one or more entries by ID. Output is each block in sequence,
          separated by a blank line. ID prefix selects the file:
            EX/PR/PB/PS-NNN -> inventory.md entry blocks (Experience Entries,
                               Independent & Volunteer Projects, Publications,
                               Presentations)
            PR-NNN.NN       -> one PR element, with its block's header and
                               Objective
            RL-NNN          -> inventory.md Employment & Role History records
            ED/CERT/AFF/TR/AW -> inventory.md credential/reference blocks
            ST-NNN, DC-NNN  -> narratives.md '## Title' blocks
            TH-NNN          -> positioning.md '## TH-NNN ...' blocks
          An inventory ID missing from inventory.md is looked up in the retired
          file (inventory-ret.md) and returned marked RETIRED.

  section Fetch a named section from a profile file. Output is the raw
          section body on stdout, no JSON wrapper. <file> is one of
          'inventory', 'narratives', 'positioning', 'user-info'. <section>
          is the heading text normalised to lowercase-with-hyphens (a leading
          numeric prefix, if a heading carries one, is stripped), so
          '## Education' matches '--section education'.

  related Fetch the inventory entries a staged item might duplicate or extend,
          for the profile-update routing decision: every entry in the item's
          Work role, under its topic-group label, plus entries elsewhere
          sharing key words with what the item says the candidate did. Prints only the prose fields. A pull
          larger than config related_pull.max_chars splits into parts.

Nothing repo-dependent is hardcoded; folder locations and filenames come
from config.yaml. Sibling helper modules (_config, _util) provide the
generic I/O and path operations.

Author    : Jason Delosh
Created   : 2026-05-26
Project   : career
Usage     : python scripts/profile_slice.py id EX-149 EX-095 ST-003
            python scripts/profile_slice.py section inventory technical-experience
            python scripts/profile_slice.py section positioning signature-themes
            python scripts/profile_slice.py related --item "<label>" [--part 2]
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import profile_update as pu   # owns the staging file layout read by 'related'
from inventory_model import document, entry_block, ex, pr


# ---------------------------------------------------------------------------
# Path resolution helpers
# Map a logical file name ('inventory', 'narratives', 'positioning',
# 'user-info') to the absolute on-disk path of that file under
# personal/profile/. The mapping comes from config.yaml so a profile-folder
# rename or filename change is a config edit, not a code change.
# ---------------------------------------------------------------------------

# Map the subcommand <file> argument to the config.yaml filenames key.
_FILE_KEY_BY_NAME = {
    'inventory':   'inventory_file',
    'narratives':  'narratives_file',
    'positioning': 'positioning_file',
    'user-info':   'user_info_file',
}


def _profile_dir(repo_root, cfg):
    """Return absolute path of the profile folder per config.yaml."""
    return os.path.join(repo_root, cfg['paths']['profile'])


def _profile_file_path(repo_root, cfg, logical_name):
    """Return the absolute path of a profile file by its logical name."""
    key = _FILE_KEY_BY_NAME.get(logical_name)
    if key is None:
        raise ValueError(
            f'unknown profile file: {logical_name!r}; valid options: '
            f"{', '.join(sorted(_FILE_KEY_BY_NAME))}"
        )
    return os.path.join(_profile_dir(repo_root, cfg), cfg['filenames'][key])


# ---------------------------------------------------------------------------
# ID-prefix routing
# The ID prefix tells us which profile file the entry lives in and which
# block-extraction shape applies. Two shapes:
#   metadata-block (inventory EX, PR, PB, PS, RL, and credential/reference
#       entries ED, CERT, AFF, TR, AW): begins at 'ID: <id>' on its own
#       line; ends at the next 'ID: ' line or the next heading.
#   heading-block (narratives ST, DC; positioning TH): begins at a '## ...'
#       heading that either contains the ID directly (themes) or wraps a
#       'ID: <id>' line in its body (narratives); ends at the next heading
#       of equal or shallower depth.
# ---------------------------------------------------------------------------

# Map ID prefix to its profile file logical name.
_PREFIX_TO_FILE = {
    'EX': 'inventory',
    'PR': 'inventory',
    'PB': 'inventory',
    'PS': 'inventory',
    'RL': 'inventory',
    'ED': 'inventory',
    'CERT': 'inventory',
    'AFF': 'inventory',
    'TR': 'inventory',
    'AW': 'inventory',
    'ST': 'narratives',
    'DC': 'narratives',
    'TH': 'positioning',
}


def _file_for_id(entry_id):
    """Return the logical profile file name for a given ID."""
    prefix = entry_id.split('-', 1)[0]
    name = _PREFIX_TO_FILE.get(prefix)
    if name is None:
        raise ValueError(
            f'unknown ID prefix: {entry_id!r}; expected one of '
            f"{', '.join(sorted(_PREFIX_TO_FILE))}"
        )
    return name


# ---------------------------------------------------------------------------
# Heading-block extraction (narrative ST/DC, theme TH)
# A heading-block starts at a '## ...' heading that either contains the ID
# directly (themes: '## TH-001 Title here') or wraps a 'ID: <id>' line in
# its body (narratives: heading is '## <Title>', body contains 'ID: ST-001'
# below). The block ends just before the next '## ' heading or any '# '
# top-level heading at a shallower depth.
# ---------------------------------------------------------------------------

def _extract_heading_block_by_id(text, target_id):
    """Extract the '## ...' heading-block that contains or names the target ID.

    Returns the block text trimmed of trailing whitespace, or None if the
    ID is not found in any heading or any block body.
    """
    lines = text.split('\n')
    target_metadata_line = f'ID: {target_id}'
    # Index every '## ' heading position so we can determine sibling bounds.
    h2_indices = [i for i, line in enumerate(lines) if line.startswith('## ')]
    for idx, start in enumerate(h2_indices):
        # Initial end is the next '## ' heading (or end of file).
        end = (
            h2_indices[idx + 1]
            if idx + 1 < len(h2_indices)
            else len(lines)
        )
        # Tighten end at any '# ' top-level heading inside this range.
        # startswith('# ') matches '# X' but not '## X', so '# ' here
        # specifically means depth-1 headings.
        for k in range(start + 1, end):
            if lines[k].startswith('# ') and not lines[k].startswith('## '):
                end = k
                break
        # Match: target ID either in the heading itself or as a body line.
        heading_line = lines[start]
        if target_id in heading_line:
            return '\n'.join(lines[start:end]).rstrip()
        for body_line in lines[start + 1:end]:
            if body_line.strip() == target_metadata_line:
                return '\n'.join(lines[start:end]).rstrip()
    return None


# ---------------------------------------------------------------------------
# Single-ID dispatcher
# Routes the ID to the correct file and the correct extraction shape, then
# returns the block. Raises if the file is missing or the ID is not found.
# ---------------------------------------------------------------------------

def _fetch_id(entry_id, repo_root, cfg):
    """Return the extracted block for one ID; raise on file or ID not found."""
    logical_name = _file_for_id(entry_id)
    file_path = _profile_file_path(repo_root, cfg, logical_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'profile file missing: {file_path}')
    text = _util.read(file_path)
    prefix = entry_id.split('-', 1)[0]
    element = pr.ELEMENT_ID_RE.match(entry_id)
    if element:
        # A PR element comes with its block's header and Objective.
        block = entry_block.find_block(text, element.group(1))
        if block is not None:
            block = pr.slice_element(block, entry_id)
    elif prefix in ('EX', 'PR', 'PB', 'PS', 'RL', 'ED', 'CERT', 'AFF', 'TR', 'AW'):
        # Inventory ID blocks are read by the shared inventory data model.
        block = entry_block.find_block(text, entry_id)
    else:
        block = _extract_heading_block_by_id(text, entry_id)
    if block is None and logical_name == 'inventory':
        block = _retired_row(entry_id, repo_root, cfg)
    if block is None:
        raise ValueError(f'ID not found in {logical_name}: {entry_id}')
    return block


# ---------------------------------------------------------------------------
# Retired-ID fallback
# An entry or element removed from the inventory is logged in the retired file
# (inventory-ret.md) and its ID is never reused. A CV already sent can still
# cite it, so an ID missing from the inventory is looked up there and returned
# marked retired, rather than failing the lookup an interview-prep run makes.
# ---------------------------------------------------------------------------

def _retired_row(entry_id, repo_root, cfg):
    """Return a retired ID's log row as labelled lines, or None."""
    path = os.path.join(_profile_dir(repo_root, cfg),
                        cfg['filenames']['inventory_retired_file'])
    if not os.path.exists(path):
        return None
    row = entry_block.retired_rows(_util.read(path)).get(entry_id)
    if row is None:
        return None
    return f'ID: {entry_id}\nStatus: RETIRED {row[0]}\nNotes: {row[1]}'


# ---------------------------------------------------------------------------
# Section extraction by name
# Walks every Markdown ATX heading in the file. The first heading whose
# normalised slug equals the requested section slug marks the section start.
# The section ends just before the next heading at equal or shallower depth
# (or end of file). Normalisation strips a leading 'N.' numeric prefix,
# lowercases, replaces whitespace and forward-slashes with hyphens, and
# drops any remaining non-alphanumeric character except hyphens. This means
# '## 1. Education' and a section arg of 'education' match.
# ---------------------------------------------------------------------------

# Regex: ATX heading line. Group 1 is the '#' run (depth indicator), group 2
# is the heading text. Trailing whitespace on the line is tolerated.
_HEADING_RE = re.compile(r'^(#+)\s+(.*?)\s*$')


def _normalise_heading_slug(text):
    """Normalise a heading text to a lookup slug for section matching."""
    # Strip leading numeric prefix like '1. ' or '12. '.
    text = re.sub(r'^\d+\.\s*', '', text)
    text = text.lower()
    # Whitespace and forward-slash collapse to a single hyphen.
    text = re.sub(r'[\s/]+', '-', text)
    # Drop anything that is not alphanumeric or hyphen.
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Collapse runs of hyphens introduced by the previous substitutions.
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def _extract_section(text, target_slug):
    """Return the body of a named section from the file text.

    Includes the matched heading line at the top of the returned block.
    Returns None if no heading normalises to target_slug.
    """
    lines = text.split('\n')
    target_slug = target_slug.lower()
    # Pass 1: collect (line index, depth, normalised slug) for every heading.
    headings = []
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m:
            depth = len(m.group(1))
            slug = _normalise_heading_slug(m.group(2))
            headings.append((i, depth, slug))
    # Pass 2: locate target heading and bound by next heading at <= depth.
    for idx, (start, depth, slug) in enumerate(headings):
        if slug == target_slug:
            end = len(lines)
            for j in range(idx + 1, len(headings)):
                _, next_depth, _ = headings[j]
                if next_depth <= depth:
                    end = headings[j][0]
                    break
            return '\n'.join(lines[start:end]).rstrip()
    return None


# ---------------------------------------------------------------------------
# Subcommand: id
# Fetch one or more IDs and print each block on stdout, separated by a
# blank line. Different IDs may resolve to different files; the dispatcher
# handles that internally. Raises (and exits 1) on the first ID not found,
# so the calling skill sees the failure rather than a silent partial result.
# ---------------------------------------------------------------------------

def cmd_id(args, repo_root, cfg):
    """Fetch each requested ID and write the blocks to stdout."""
    blocks = []
    for entry_id in args.ids:
        blocks.append(_fetch_id(entry_id, repo_root, cfg))
    sys.stdout.write('\n\n'.join(blocks))
    sys.stdout.write('\n')


# ---------------------------------------------------------------------------
# Subcommand: section
# Print the body of one named section from the requested profile file.
# Raw text output, no JSON wrapper, so the caller can splice it directly
# into a downstream skill prompt or render it to the user.
# ---------------------------------------------------------------------------

def cmd_section(args, repo_root, cfg):
    """Print the body of one section from the requested profile file."""
    file_path = _profile_file_path(repo_root, cfg, args.file)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'profile file missing: {file_path}')
    text = _util.read(file_path)
    body = _extract_section(text, args.section)
    if body is None:
        raise ValueError(
            f'section not found in {args.file}: {args.section!r}'
        )
    sys.stdout.write(body)
    sys.stdout.write('\n')


# ---------------------------------------------------------------------------
# Subcommand: related
# Before writing a staged item, the profile-update run has to know whether the
# inventory already covers it. That search used to be done by the model by
# hand, and it missed things. Here it is two fixed passes: every entry in the
# item's Work role, then entries in other roles that share at least
# related_pull.min_shared_words key words with the item's Did text. Only the
# prose fields are printed, since the decision turns on what the work was.
# A large role is split into parts so no single read exceeds max_chars.
# ---------------------------------------------------------------------------

# The fields printed for each entry, and the prefixes the pull searches.
_RELATED_FIELDS = ('Project', 'Description', 'Hands-on Tools', 'Impact', 'Context',
                   'Objective')
_RELATED_PREFIXES = ('EX', 'PR', 'PB', 'PS')

# Words too common to signal shared substance.
_STOPWORDS = {
    'with', 'from', 'into', 'that', 'this', 'their', 'there', 'were', 'which',
    'across', 'about', 'over', 'under', 'through', 'using', 'used', 'have',
    'also', 'each', 'other', 'than', 'then', 'when', 'where', 'while', 'study',
    'studies', 'data', 'team', 'teams', 'work', 'process', 'support',
}


def _key_words(text):
    """Return the distinct lowercase words of 4+ letters that are not stopwords."""
    return {w for w in re.findall(r'[a-z][a-z0-9-]{3,}', text.lower())
            if w not in _STOPWORDS}


def _render_related(entry, lines):
    """Return one entry as its ID plus prose fields (and PR element text)."""
    out = [f"ID: {entry['id']}"]
    out += [f'{label}: {entry["field_map"][label]}' for label in _RELATED_FIELDS
            if entry['field_map'].get(label)]
    if entry['prefix'] == 'PR':
        body = lines[entry['start']:entry['end']]
        out += [f"  - {el['id']}: {el['text']}" for el in pr.parse_elements(body)]
    return '\n'.join(out)


def related_entries(inventory_text, item_body, min_shared):
    """Return (role, same_role, by_words) for one staged item.

    same_role holds rendered entries whose Role is the item's Work role.
    by_words holds (rendered entry, shared words) for other entries sharing at
    least min_shared key words with the Did field, most shared first.
    """
    role = pu.bullet_value(item_body, 'Work role') or ''
    words = _key_words(pu.bullet_value(item_body, 'Did') or '')
    lines = inventory_text.split('\n')
    same_role, by_words = [], []
    for entry in entry_block.parse_blocks(inventory_text):
        if entry['prefix'] not in _RELATED_PREFIXES:
            continue
        rendered = _render_related(entry, lines)
        if role and entry['field_map'].get('Role', '').strip() == role:
            same_role.append(rendered)
            continue
        shared = sorted(words & _key_words(rendered))
        if len(shared) >= min_shared:
            by_words.append((rendered, shared))
    by_words.sort(key=lambda pair: -len(pair[1]))
    return role, same_role, by_words


def by_topic_group(inventory_text, role, same_role):
    """Return the same-role entries with each topic group's label above its own.

    Routing a new EX entry means naming the topic group it joins
    (ex-topic-groups-2026-10), so the labels travel with the pull. Same-role
    entries outside the EX groups (PR, PB, PS) follow the last group.
    """
    if not role.startswith('RL-') or document.section_bounds(inventory_text, role) is None:
        return same_role
    # Each rendered entry opens with its 'ID: <id>' line.
    by_id = {text.split('\n', 1)[0][len('ID: '):]: text for text in same_role}
    out = []
    for group in ex.role_groups(inventory_text, role):
        out.append(f'--- {group["label"]}')
        out += [by_id.pop(entry_id) for entry_id in group['entries'] if entry_id in by_id]
    return out + list(by_id.values())


def split_parts(blocks, max_chars):
    """Greedily pack text blocks into parts of at most max_chars each."""
    parts, current, size = [], [], 0
    for block in blocks:
        if current and size + len(block) > max_chars:
            parts.append(current)
            current, size = [], 0
        current.append(block)
        size += len(block) + 2
    if current:
        parts.append(current)
    return parts or [[]]


def cmd_related(args, repo_root, cfg):
    """Print the inventory entries related to one staged item, one part at a time."""
    item =pu.find_item(_util.read(pu._staging_path(repo_root, cfg)), args.item)
    inventory_text = _util.read(_profile_file_path(repo_root, cfg, 'inventory'))
    settings = cfg['related_pull']
    role, same_role, by_words = related_entries(
        inventory_text, item['body'], settings['min_shared_words'])

    blocks = ([f'## Same role ({role or "none"}): {len(same_role)} entries']
              + by_topic_group(inventory_text, role, same_role))
    if not role.startswith('RL-'):
        blocks.append(f'Work role is "{role}", so no role group applies. For a '
                      f'tool or list item, read the list section with: '
                      f'python scripts/profile_slice.py section inventory '
                      f'technical-experience')
    blocks.append(f'## Shared key words, other roles: {len(by_words)} entries')
    blocks += [f'{text}\n(shared: {", ".join(shared)})' for text, shared in by_words]

    parts = split_parts(blocks, settings['max_chars'])
    if not 1 <= args.part <= len(parts):
        raise ValueError(f'--part {args.part} is out of range; the pull has {len(parts)} part(s)')
    if len(parts) > 1:
        print(f'Part {args.part} of {len(parts)}. Read every part before deciding.\n')
    sys.stdout.write('\n\n'.join(parts[args.part - 1]) + '\n')


# ---------------------------------------------------------------------------
# Command-line entry point
# Parses subcommand and arguments, loads config, runs the subcommand, and
# reports failure to stderr with exit 1 so the calling skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch to the selected subcommand."""
    parser = argparse.ArgumentParser(
        description='deterministic slicer for the candidate profile documents'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # --- Subparser: id ---
    p_id = sub.add_parser(
        'id',
        help='fetch one or more entries by ID (EX, PR, PB, PS, RL, ED, CERT, AFF, TR, AW, ST, DC, TH prefixes)',
    )
    p_id.add_argument(
        'ids', nargs='+',
        help='one or more IDs, e.g. EX-149 ST-003 TH-001',
    )
    p_id.set_defaults(func=cmd_id)

    # --- Subparser: section ---
    p_sec = sub.add_parser(
        'section',
        help='fetch a named section from a profile file',
    )
    p_sec.add_argument(
        'file',
        choices=sorted(_FILE_KEY_BY_NAME),
        help='which profile file to read',
    )
    p_sec.add_argument(
        'section',
        help='section name as a slug (e.g. education, technical-experience, '
             'signature-themes)',
    )
    p_sec.set_defaults(func=cmd_section)

    # --- Subparser: related ---
    p_rel = sub.add_parser(
        'related',
        help='fetch the inventory entries related to one staged item',
    )
    p_rel.add_argument('--item', required=True, help="the staged item's label")
    p_rel.add_argument('--part', type=int, default=1,
                       help='which part to print when the pull is split (default 1)')
    p_rel.set_defaults(func=cmd_related)

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
