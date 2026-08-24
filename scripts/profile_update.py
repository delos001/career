#!/usr/bin/env python3
"""
profile_update.py - deterministic mutations for inventory.md and the staging file

Called by the profile-update skill. Owns every mechanical operation involved in
promoting a staged PU-NNN entry into the profile: reading what is pending,
assigning the next entry ID, placing a new entry at its correct position in
inventory.md, rebuilding the table of contents, and closing the staging entry
with an audit line naming where the content landed.

The skill owns the judgment (what the content should say, which entry it belongs
in, whether an existing entry should be enriched instead). This script owns
everything that must not be done by hand: ID assignment, placement order, ToC
integrity, and status bookkeeping.

Five subcommands:

  pending   List the staging entries still awaiting processing. Compact output
            (ID, kind, label, source application) so the skill can plan a run
            without reading the whole staging file into context.
  show      Print one staging entry's full block, for the entry being worked.
  next-id   Print the next unused ID for a prefix, derived by scanning
            inventory.md. Informational; 'insert' assigns IDs itself.
  insert    Place a new entry block into inventory.md. The block file carries
            the entry WITHOUT its 'ID:' line; the script assigns the ID at write
            time so two inserts in one run cannot collide, then prints it.
  close     Flip a staging entry to processed and append the '**Processed:**'
            line naming the target IDs (or 'no change').

Nothing about the document's shape is hardcoded. The section roster, the
prefix-to-section mapping, and the per-prefix field rosters are all parsed from
templates/inventory.md at run time, so a schema change is a template edit.
Paths and filenames come from config.yaml.

Author    : Jason Delosh
Created   : 2026-08-24
Project   : career
Usage     : python scripts/profile_update.py pending
            python scripts/profile_update.py show --pu PU-004
            python scripts/profile_update.py next-id --prefix EX
            python scripts/profile_update.py insert --prefix EX --block-file <path>
            python scripts/profile_update.py close --pu PU-004 \\
                --targets EX-210,EX-211 --date 2026-08-24
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Template parsing - the schema authority
# templates/inventory.md carries two machine-read blocks: the '## Document
# skeleton' fence (section roster and order) and one '### <PREFIX> - <Section>'
# fence per entry type (field roster). Parsing them here means the script never
# holds its own copy of the schema, so adding a field or a section is a template
# edit rather than a code change.
# ---------------------------------------------------------------------------

# Regex: an entry-schema heading, e.g. '### EX - Experience Entries'.
_SCHEMA_HEADING_RE = re.compile(
    r'^###\s+([A-Z]+)\s+-\s+(.+?)\s*$', re.MULTILINE)

# Regex: a fenced block. Group 1 is the body.
_FENCE_RE = re.compile(r'```\n(.*?)\n```', re.DOTALL)

# Regex: a field line inside a schema fence, e.g. 'Role: RL-{NNN} {optional}'.
_SCHEMA_FIELD_RE = re.compile(r'^([A-Za-z][A-Za-z &-]*):(.*)$')


def parse_template(template_text):
    """Return {prefix: {'section': str, 'fields': [(label, optional)]}}.

    Parsed from the '### <PREFIX> - <Section>' fenced blocks. Raises when no
    schema block is found, so a template edit that breaks the contract fails
    loudly rather than silently validating nothing.
    """
    schemas = {}
    for m in _SCHEMA_HEADING_RE.finditer(template_text):
        prefix, section = m.group(1), m.group(2)
        fence = _FENCE_RE.search(template_text, m.end())
        if not fence:
            continue
        fields = []
        for line in fence.group(1).split('\n'):
            fm = _SCHEMA_FIELD_RE.match(line)
            if fm:
                fields.append((fm.group(1), '{optional}' in fm.group(2)))
        schemas[prefix] = {'section': section, 'fields': fields}
    if not schemas:
        raise ValueError(
            'inventory template carries no "### <PREFIX> - <Section>" schema '
            'blocks to read the field rosters from')
    return schemas


def template_sections(template_text):
    """Return the literal section headings from the document-skeleton fence.

    Placeholder headings (those wrapped in braces, e.g. '### {Category}') are
    the per-user category mechanism and are excluded: their names are derived
    per user, so they are not part of the roster any document must carry.
    """
    body = _extract_section(template_text, 'Document skeleton')
    if body is None:
        raise ValueError('inventory template has no "## Document skeleton" section')
    fence = _FENCE_RE.search(body)
    if not fence:
        raise ValueError('inventory template document-skeleton block is not fenced')
    sections = []
    for line in fence.group(1).split('\n'):
        m = re.match(r'^(#{2,3})\s+(.+?)\s*$', line)
        if m and '{' not in m.group(2):
            sections.append((len(m.group(1)), m.group(2)))
    return sections


# ---------------------------------------------------------------------------
# Document navigation
# Sections are located by heading text; entries are located by their 'ID:'
# line. Both use anchored line patterns rather than substring search, per the
# ID-matching convention in inventory-section-8-rl-grouping-2026-05.
# ---------------------------------------------------------------------------

def _fence_mask(lines):
    """Return a per-line flag marking lines that sit inside a fenced block.

    The inventory itself carries no fences, but the template does, and its
    skeleton fence contains heading-shaped lines. Without this mask a heading
    scan would treat the template's illustrative '## Education' as a real
    section boundary and cut the block in half.
    """
    inside = False
    mask = []
    for line in lines:
        if line.startswith('```'):
            mask.append(True)
            inside = not inside
            continue
        mask.append(inside)
    return mask


def _extract_section(text, heading):
    """Return the body of a '## <heading>' section, or None if absent."""
    bounds = _section_bounds(text, heading)
    if bounds is None:
        return None
    start, end = bounds
    return '\n'.join(text.split('\n')[start:end])


def _section_bounds(text, heading):
    """Return (start_line, end_line) for a section, heading line included.

    The section ends at the next heading of equal or shallower depth, or at the
    end of the document. Returns None when the heading is absent.
    """
    lines = text.split('\n')
    fenced = _fence_mask(lines)
    target = None
    depth = 0
    for i, line in enumerate(lines):
        if fenced[i]:
            continue
        m = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if m and m.group(2) == heading:
            target, depth = i, len(m.group(1))
            break
    if target is None:
        return None
    for j in range(target + 1, len(lines)):
        if fenced[j]:
            continue
        m = re.match(r'^(#{1,6})\s+', lines[j])
        if m and len(m.group(1)) <= depth:
            return (target, j)
    return (target, len(lines))


def parse_entries(text):
    """Return every inventory entry as a dict of position, ID, and fields.

    An entry begins at an 'ID: <PREFIX>-<NNN>' line and runs until the next
    'ID: ' line or the next heading. Field values are captured in document
    order so a caller can compare them against the template roster.
    """
    lines = text.split('\n')
    entries = []
    for i, line in enumerate(lines):
        m = re.match(r'^ID:\s+([A-Z]+)-(\d+)\s*$', line)
        if not m:
            continue
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if (re.match(r'^ID:\s+', lines[j])
                    or re.match(r'^#{1,6}\s+', lines[j])):
                end = j
                break
        fields = []
        for body_line in lines[i:end]:
            fm = re.match(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$', body_line)
            if fm:
                fields.append((fm.group(1), fm.group(2).strip()))
        entries.append({
            'id': f'{m.group(1)}-{m.group(2)}',
            'prefix': m.group(1),
            'number': int(m.group(2)),
            'start': i,
            'end': end,
            'fields': fields,
            'field_map': dict(fields),
        })
    return entries


def next_id(text, prefix, digits=3):
    """Return the next unused ID for a prefix by scanning the document.

    Derived from the document rather than from any recorded count, per
    feedback_no_count_snapshots_in_schemas. IDs are never reused, so the next
    ID is always max+1 even when lower numbers are free.
    """
    numbers = [e['number'] for e in parse_entries(text) if e['prefix'] == prefix]
    return f'{prefix}-{(max(numbers) + 1) if numbers else 1:0{digits}d}'


# ---------------------------------------------------------------------------
# Table of contents
# The ToC mirrors the document's headings exactly, so it is regenerated from
# them rather than patched. Anchors follow the GitHub slug rule: lowercase,
# non-alphanumerics dropped, spaces to hyphens. '&' drops out and leaves the
# surrounding spaces, which is why 'Employment & Role History' anchors as
# 'employment--role-history'.
# ---------------------------------------------------------------------------

def _github_slug(heading_text):
    """Return the GitHub-style anchor slug for a heading."""
    slug = heading_text.lower()
    slug = re.sub(r'[^a-z0-9 -]', '', slug)
    return slug.replace(' ', '-')


def rebuild_toc(text):
    """Return the document with its Table of Contents regenerated.

    Every ATX heading except the ToC's own is listed, indented two spaces per
    depth level below the document title. Returns the text unchanged when the
    document carries no ToC section.
    """
    bounds = _section_bounds(text, 'Table of Contents')
    if bounds is None:
        return text
    lines = text.split('\n')
    items = []
    for line in lines:
        m = re.match(r'^(#{1,6})\s+(.+?)\s*$', line)
        if not m:
            continue
        depth, heading = len(m.group(1)), m.group(2)
        indent = '  ' * (depth - 1)
        label = heading.replace('&', r'\&')
        items.append(f'{indent}- [{label}](#{_github_slug(heading)})')
    start, end = bounds
    # Replace only the contiguous run of list lines, never the whole section:
    # the blank line and horizontal rule that follow the list belong to the
    # document's layout, not to the generated content.
    list_lines = [i for i in range(start + 1, end)
                  if re.match(r'^\s*-\s+\[', lines[i])]
    if not list_lines:
        return '\n'.join(lines[:start + 1] + ['', *items] + lines[start + 1:])
    first, last = list_lines[0], list_lines[-1]
    return '\n'.join(lines[:first] + items + lines[last + 1:])


# ---------------------------------------------------------------------------
# Placement
# Where a new entry goes is fully determined by its type and its field values,
# so placement is computed rather than passed in. EX entries sort within their
# role group by primary Orientation, then primary Specialty, then ID ascending
# (inventory-section-8-rl-grouping-2026-05); RL records run reverse-chronological
# by Start Date; every other type appends to the end of its section.
# ---------------------------------------------------------------------------

def _primary(value):
    """Return the primary value of a possibly multi-value axis field."""
    return value.split('|')[0].strip()


def _ex_sort_key(field_map, entry_number):
    """Return the within-role sort key for an EX entry."""
    return (
        _primary(field_map.get('Orientation', '')),
        _primary(field_map.get('Specialty', '')),
        entry_number,
    )


def _rl_subheading_bounds(text, role_id):
    """Return (start, end) line bounds of a '### RL-NNN' group, or None."""
    return _section_bounds(text, role_id)


def _insert_lines(text, at_line, block_lines):
    """Return the text with block_lines spliced in at a line index."""
    lines = text.split('\n')
    return '\n'.join(lines[:at_line] + block_lines + lines[at_line:])


def _place_ex(text, block, new_number):
    """Return text with an EX block placed in its role group, sorted."""
    field_map = dict(
        re.match(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$', line).groups()
        for line in block.split('\n')
        if re.match(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$', line)
    )
    role = field_map.get('Role', '').strip()
    if not role:
        raise ValueError('EX entry block carries no "Role: RL-NNN" field')
    bounds = _rl_subheading_bounds(text, role)
    if bounds is None:
        raise ValueError(
            f'no "### {role}" group exists under Experience Entries. Create the '
            f'role record and its group before adding entries to it.')
    start, end = bounds
    key = _ex_sort_key(field_map, new_number)
    # Walk the group's existing entries and stop at the first one that sorts
    # after the newcomer; its start line is the insertion point.
    group_text = '\n'.join(text.split('\n')[start:end])
    at = None
    for entry in parse_entries(group_text):
        if entry['prefix'] != 'EX':
            continue
        if _ex_sort_key(entry['field_map'], entry['number']) > key:
            at = start + entry['start']
            break
    if at is None:
        at = start + _last_content_line(group_text) + 1
    return _insert_lines(text, at, block.split('\n') + [''])


def _place_rl(text, block):
    """Return text with an RL record placed reverse-chronologically."""
    field_map = dict(
        re.match(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$', line).groups()
        for line in block.split('\n')
        if re.match(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$', line)
    )
    start_date = field_map.get('Start Date', '')
    bounds = _section_bounds(text, 'Employment & Role History')
    if bounds is None:
        raise ValueError('inventory has no "## Employment & Role History" section')
    start, end = bounds
    section_text = '\n'.join(text.split('\n')[start:end])
    at = None
    for entry in parse_entries(section_text):
        if entry['field_map'].get('Start Date', '') < start_date:
            at = start + entry['start']
            break
    if at is None:
        at = start + _last_content_line(section_text) + 1
    return _insert_lines(text, at, block.split('\n') + [''])


def _place_append(text, block, section, subsection=None):
    """Return text with a block appended to the end of a section's content.

    Replaces a lone 'Entries: None' line when the section is empty, so the
    observed-absence marker does not survive alongside real entries.
    """
    heading = subsection or section
    bounds = _section_bounds(text, heading)
    if bounds is None:
        raise ValueError(f'inventory has no "{heading}" section')
    start, end = bounds
    lines = text.split('\n')
    for i in range(start, end):
        if lines[i].strip() == 'Entries: None':
            return '\n'.join(lines[:i] + block.split('\n') + lines[i + 1:])
    section_text = '\n'.join(lines[start:end])
    at = start + _last_content_line(section_text) + 1
    return _insert_lines(text, at, [''] + block.split('\n'))


def _last_content_line(section_text):
    """Return the index of the last non-blank, non-rule line in a section."""
    lines = section_text.split('\n')
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped and stripped != '---':
            return i
    return 0


# ---------------------------------------------------------------------------
# Staging file operations
# The staging file is the run's work list. 'pending' and 'show' read it;
# 'close' writes the status flip plus the audit line that records which profile
# IDs now carry the staged content.
# ---------------------------------------------------------------------------

# Regex: a staging entry heading, e.g. '### PU-004 - Oncology trial leadership'.
_PU_HEADING_RE = re.compile(r'^### (PU-\d+)\s+-\s+(.*?)\s*$', re.MULTILINE)


def parse_staging(staging_text):
    """Return every staging entry with its bounds, label, kind, and status."""
    lines = staging_text.split('\n')
    heads = [(i, m.group(1), m.group(2))
             for i, line in enumerate(lines)
             for m in [_PU_HEADING_RE.match(line)] if m]
    entries = []
    for idx, (start, pu_id, label) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        body = '\n'.join(lines[start:end])
        status = _bullet_value(body, 'Status') or 'pending'
        # A 'Closed requirement:' label alone does not make an entry a closure.
        # Entries captured before the closure/enrichment split (issue #58) used
        # that label for everything, including prep-surfaced facts anchored to
        # 'n/a'. Only a real CR-NNN anchor counts.
        closed = _bullet_value(body, 'Closed requirement') or ''
        kind = 'closure' if re.match(r'^CR-\d+', closed) else 'enrichment'
        entries.append({
            'id': pu_id,
            'label': label,
            'kind': kind,
            'status': status,
            'from': _bullet_value(body, 'From') or '',
            'captured': _bullet_value(body, 'Captured') or '',
            'start': start,
            'end': end,
            'body': body.rstrip(),
        })
    return entries


def _bullet_value(body, label):
    """Return the value of a '- **<label>:** value' bullet, or None."""
    m = re.search(rf'^-\s+\*\*{re.escape(label)}:\*\*\s*(.*?)\s*$',
                  body, re.MULTILINE)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Subcommand: pending
# One line per unprocessed entry. Deliberately compact: the skill plans a run
# from this list and pulls full content per entry with 'show', so the staging
# file never enters context wholesale.
# ---------------------------------------------------------------------------

def cmd_pending(args, repo_root, cfg):
    """Print the staging entries still awaiting processing."""
    staging_path = _staging_path(repo_root, cfg)
    if not os.path.exists(staging_path):
        print('no staging file; nothing pending')
        return
    entries = [e for e in parse_staging(_util.read(staging_path))
               if e['status'] != 'processed']
    if not entries:
        print('nothing pending')
        return
    for e in entries:
        print(f"{e['id']}  {e['kind']:<10}  {e['captured']}  {e['label']}")
        print(f"            from {e['from']}")
    print(f'\n{len(entries)} pending')


# ---------------------------------------------------------------------------
# Subcommand: show
# Full block for one entry, including the Content field the skill needs in
# order to judge what to write.
# ---------------------------------------------------------------------------

def cmd_show(args, repo_root, cfg):
    """Print one staging entry's full block."""
    staging_text = _util.read(_staging_path(repo_root, cfg))
    for e in parse_staging(staging_text):
        if e['id'] == args.pu:
            sys.stdout.write(e['body'] + '\n')
            return
    raise ValueError(f'staging entry not found: {args.pu}')


# ---------------------------------------------------------------------------
# Subcommand: next-id
# Informational only. 'insert' assigns IDs itself so that two inserts in one
# run cannot both claim the same number, which is the failure mode the
# application-ID counter hit.
# ---------------------------------------------------------------------------

def cmd_next_id(args, repo_root, cfg):
    """Print the next unused ID for a prefix."""
    text = _util.read(_inventory_path(repo_root, cfg))
    print(next_id(text, args.prefix))


# ---------------------------------------------------------------------------
# Subcommand: insert
# Assigns the ID, places the block, rebuilds the ToC, writes, and echoes the
# assigned ID so the caller can record it in the staging entry's audit line.
# ---------------------------------------------------------------------------

def cmd_insert(args, repo_root, cfg):
    """Place a new entry into inventory.md and print its assigned ID."""
    inventory_path = _inventory_path(repo_root, cfg)
    text = _util.read(inventory_path)
    schemas = parse_template(_util.read(_template_path(repo_root, cfg)))

    if args.prefix not in schemas:
        raise ValueError(
            f'unknown entry prefix: {args.prefix}; the template defines '
            f"{', '.join(sorted(schemas))}")

    block = _util.read(args.block_file).strip()
    if re.match(r'^ID:\s', block):
        raise ValueError(
            'block file carries its own "ID:" line; omit it. This command '
            'assigns the ID so concurrent inserts cannot collide.')

    # Validate the block against the template roster before touching the file.
    _validate_block(block, schemas[args.prefix], args.prefix)

    assigned = next_id(text, args.prefix)
    number = int(assigned.split('-')[1])
    block = f'ID: {assigned}\n{block}'

    if args.prefix == 'EX':
        text = _place_ex(text, block, number)
    elif args.prefix == 'RL':
        text = _place_rl(text, block)
    else:
        text = _place_append(text, block, schemas[args.prefix]['section'],
                             args.subsection)

    text = rebuild_toc(text)
    _util.write(inventory_path, text)
    print(assigned)


def _validate_block(block, schema, prefix):
    """Raise when a block's fields do not match the template roster."""
    present = [m.group(1) for line in block.split('\n')
               for m in [re.match(r'^([A-Za-z][A-Za-z &-]*):', line)] if m]
    required = [label for label, optional in schema['fields']
                if not optional and label != 'ID']
    missing = [label for label in required if label not in present]
    if missing:
        raise ValueError(
            f"{prefix} entry is missing required field(s): {', '.join(missing)}")
    known = {label for label, _ in schema['fields']}
    unknown = [label for label in present if label not in known]
    if unknown:
        raise ValueError(
            f"{prefix} entry carries field(s) not in the template schema: "
            f"{', '.join(unknown)}")
    # Template order is the written order; a reordered entry breaks the
    # field-order convention every consuming parser reads positionally.
    expected_order = [label for label, _ in schema['fields']
                      if label in present and label != 'ID']
    if present != expected_order:
        raise ValueError(
            f'{prefix} entry fields are out of template order. Expected: '
            f"{', '.join(expected_order)}")


# ---------------------------------------------------------------------------
# Subcommand: close
# Flips one staging entry to processed and appends the audit line naming the
# profile IDs that now carry the content. 'no change' is a valid target list:
# deciding an entry needs no profile edit still closes it.
# ---------------------------------------------------------------------------

def cmd_close(args, repo_root, cfg):
    """Mark a staging entry processed and record where its content landed."""
    staging_path = _staging_path(repo_root, cfg)
    staging_text = _util.read(staging_path)
    entries = parse_staging(staging_text)
    match = next((e for e in entries if e['id'] == args.pu), None)
    if match is None:
        raise ValueError(f'staging entry not found: {args.pu}')
    if match['status'] == 'processed':
        raise ValueError(f'{args.pu} is already processed; nothing to close')

    targets = args.targets.strip()
    if targets != 'no change':
        ids = [t.strip() for t in targets.split(',') if t.strip()]
        inventory_text = _util.read(_inventory_path(repo_root, cfg))
        known = {e['id'] for e in parse_entries(inventory_text)}
        # Narrative and positioning IDs live in other files; this script only
        # verifies the ones it can see, and reports the rest as unverified
        # rather than failing a legitimate cross-document promotion.
        unverified = [i for i in ids
                      if i not in known and i.split('-')[0] in ('EX', 'PR', 'RL',
                                                                'PB', 'PS', 'AW',
                                                                'ED', 'TR', 'CERT',
                                                                'AFF')]
        if unverified:
            raise ValueError(
                f"target ID(s) not found in inventory: {', '.join(unverified)}")
        targets = ', '.join(ids)

    lines = staging_text.split('\n')
    body = match['body'].split('\n')
    out = []
    for line in body:
        if re.match(r'^-\s+\*\*Status:\*\*', line):
            out.append('- **Status:** processed')
            out.append(f'- **Processed:** {args.date} into {targets}')
        else:
            out.append(line)
    if not any(line.startswith('- **Processed:**') for line in out):
        raise ValueError(
            f'{args.pu} has no "- **Status:**" line to flip; the entry is '
            f'malformed and was not modified')

    staging_text = '\n'.join(
        lines[:match['start']] + out + [''] + lines[match['end']:])
    _util.write(staging_path, staging_text.rstrip() + '\n')
    print(f'{args.pu} processed into {targets}')


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _inventory_path(repo_root, cfg):
    """Return the absolute path of the user's inventory document."""
    return os.path.join(repo_root, cfg['paths']['profile'],
                        cfg['filenames']['inventory_file'])


def _staging_path(repo_root, cfg):
    """Return the absolute path of the cross-application staging file."""
    return os.path.join(repo_root, cfg['paths']['profile'],
                        cfg['filenames']['staging_file'])


def _template_path(repo_root, cfg):
    """Return the absolute path of the inventory structure-authority template."""
    return os.path.join(repo_root, cfg['paths']['templates'],
                        cfg['filenames']['inventory_template'])


# ---------------------------------------------------------------------------
# Command-line entry point
# Non-zero exit on any failure so the calling skill halts per global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch to the selected subcommand."""
    parser = argparse.ArgumentParser(
        description='deterministic mutations for inventory.md and the staging file')
    sub = parser.add_subparsers(dest='command', required=True)

    p_pending = sub.add_parser('pending', help='list unprocessed staging entries')
    p_pending.set_defaults(func=cmd_pending)

    p_show = sub.add_parser('show', help='print one staging entry in full')
    p_show.add_argument('--pu', required=True, help='PU-NNN')
    p_show.set_defaults(func=cmd_show)

    p_next = sub.add_parser('next-id', help='print the next unused ID for a prefix')
    p_next.add_argument('--prefix', required=True, help='EX, PR, RL, PB, PS, AW, ...')
    p_next.set_defaults(func=cmd_next_id)

    p_insert = sub.add_parser('insert', help='place a new entry into inventory.md')
    p_insert.add_argument('--prefix', required=True)
    p_insert.add_argument('--block-file', required=True,
                          help='entry block WITHOUT its ID: line')
    p_insert.add_argument('--subsection',
                          help='sub-section heading when the section has one '
                               '(e.g. Completed / In Progress for TR entries)')
    p_insert.set_defaults(func=cmd_insert)

    p_close = sub.add_parser('close', help='mark a staging entry processed')
    p_close.add_argument('--pu', required=True, help='PU-NNN')
    p_close.add_argument('--targets', required=True,
                         help="comma-separated target IDs, or 'no change'")
    p_close.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_close.set_defaults(func=cmd_close)

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
