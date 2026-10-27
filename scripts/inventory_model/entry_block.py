#!/usr/bin/env python3
"""
entry_block.py - one ID block of any entry type

Every inventory entry is an ID block: it opens at an 'ID: <PREFIX>-<NNN>' line
and runs until the next 'ID: ' line, the next heading, or the next topic-group
marker. This module finds
those blocks, reads their 'Field: value' lines, assigns the next free ID for a
prefix, and checks a block's fields against the template roster. It is the
behavior every type uses unless its own module (ex.py, pr.py, ...) replaces it.

Author    : Jason Delosh
Created   : 2026-10-21 (moved from profile_update.py, retrieval_payload.py and
            profile_slice.py, which each carried their own block parser)
Project   : career
Depends   : none
"""

import re

from inventory_model import document


# Regex: the line that opens an ID block. Groups: prefix, number.
_ID_LINE_RE = re.compile(r'^ID:\s+([A-Z]+)-(\d+)\s*$')

# Regex: a 'Field: value' line inside a block. Groups: label, value.
_FIELD_RE = re.compile(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$')

# Regex: any line that closes an open block - the next ID line or a heading.
# A topic-group marker closes one too (document.GROUP_MARKER_RE).
_ID_START_RE = re.compile(r'^ID:\s+')
_HEADING_RE = re.compile(r'^#{1,6}\s+')


# ---------------------------------------------------------------------------
# Reading blocks
# Blocks are matched anywhere in the text by their anchored ID line rather
# than by section position, so the parse stays correct across section
# reordering (inventory-section-denumbering-and-reorder-2026-07). Ending a
# block at any heading means a non-entry section can never bleed into the
# last block's fields. Ending it at a topic-group marker keeps the next
# group's label out of the last entry of the group above: without that, every
# slice of that entry carried the wrong label, and a set on its last field
# deleted the label or wrote the field below it.
# ---------------------------------------------------------------------------

def parse_blocks(text):
    """Return every ID block as a dict of position, ID, and fields.

    Keys: id, prefix, number (int), start and end (line indices, end
    exclusive), fields ([(label, value)] in document order, so a caller can
    compare them against the template roster), field_map (dict of the same).
    """
    lines = text.split('\n')
    blocks = []
    for i, line in enumerate(lines):
        m = _ID_LINE_RE.match(line)
        if not m:
            continue
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if (_ID_START_RE.match(lines[j]) or _HEADING_RE.match(lines[j])
                    or document.GROUP_MARKER_RE.match(lines[j])):
                end = j
                break
        fields = block_fields(lines[i:end])
        blocks.append({
            'id': f'{m.group(1)}-{m.group(2)}',
            'prefix': m.group(1),
            'number': int(m.group(2)),
            'start': i,
            'end': end,
            'fields': fields,
            'field_map': dict(fields),
        })
    return blocks


def block_fields(lines):
    """Return [(label, value)] for the 'Field: value' lines in a block."""
    fields = []
    for line in lines:
        m = _FIELD_RE.match(line)
        if m:
            fields.append((m.group(1), m.group(2).strip()))
    return fields


def find_block(text, block_id):
    """Return one block's text, trailing whitespace trimmed, or None."""
    lines = text.split('\n')
    for block in parse_blocks(text):
        if block['id'] == block_id:
            return '\n'.join(lines[block['start']:block['end']]).rstrip()
    return None


# ---------------------------------------------------------------------------
# Retired IDs
# inventory-ret.md logs every ID removed from the inventory as a table row,
# '| ID | Retired | Notes |'. IDs are never reused, so a retired ID stays a
# valid reference for records written before it retired.
# ---------------------------------------------------------------------------

def retired_rows(retired_text):
    """Return {id: (retired, notes)} from the retired file's table."""
    rows = {}
    for line in (retired_text or '').split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if (len(cells) >= 3 and re.fullmatch(r'[A-Z]+-\d+(?:\.\d+)?', cells[0])):
            rows[cells[0]] = (cells[1], ' | '.join(cells[2:]))
    return rows


# ---------------------------------------------------------------------------
# Numbering
# ---------------------------------------------------------------------------

def next_id(text, prefix, digits=3):
    """Return the next unused ID for a prefix by scanning the document.

    Derived from the document rather than from any recorded count, per
    feedback_no_count_snapshots_in_schemas. IDs are never reused, so the next
    ID is always max+1 even when lower numbers are free.
    """
    numbers = [b['number'] for b in parse_blocks(text) if b['prefix'] == prefix]
    return f'{prefix}-{(max(numbers) + 1) if numbers else 1:0{digits}d}'


# ---------------------------------------------------------------------------
# Placement
# The default for a type with no placement rule of its own (EX and RL have
# theirs): append to the end of the type's section.
# ---------------------------------------------------------------------------

def place_append(text, block, section, subsection=None):
    """Return text with a block appended to the end of a section's content.

    Replaces a lone 'Entries: None' line when the section is empty, so the
    observed-absence marker does not survive alongside real entries.
    """
    heading = subsection or section
    bounds = document.section_bounds(text, heading)
    if bounds is None:
        raise ValueError(f'inventory has no "{heading}" section')
    start, end = bounds
    lines = text.split('\n')
    for i in range(start, end):
        if lines[i].strip() == 'Entries: None':
            return '\n'.join(lines[:i] + block.split('\n') + lines[i + 1:])
    section_text = '\n'.join(lines[start:end])
    at = start + document.last_content_line(section_text) + 1
    return document.insert_lines(text, at, [''] + block.split('\n'))


# ---------------------------------------------------------------------------
# Validation against the template roster
# ---------------------------------------------------------------------------

def validate_block(block, schema, prefix):
    """Raise when a block's fields do not match the template roster.

    block is the block text without its ID line; schema is one entry of
    document.parse_template.
    """
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
