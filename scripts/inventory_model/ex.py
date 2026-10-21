#!/usr/bin/env python3
"""
ex.py - EX (experience) entries

What EX does differently from entry_block: where a new entry is placed. EX
entries live in a '### RL-NNN' group under Experience Entries and sort within
it by primary Orientation, then primary Specialty, then ID ascending
(inventory-section-8-rl-grouping-2026-05).

Author    : Jason Delosh
Created   : 2026-10-21 (moved from profile_update.py)
Project   : career
Depends   : none
"""

from inventory_model import document, entry_block


def _primary(value):
    """Return the primary value of a possibly multi-value axis field."""
    return value.split('|')[0].strip()


def sort_key(field_map, entry_number):
    """Return the within-role sort key for an EX entry."""
    return (
        _primary(field_map.get('Orientation', '')),
        _primary(field_map.get('Specialty', '')),
        entry_number,
    )


def place(text, block, new_number):
    """Return text with an EX block placed in its role group, sorted."""
    field_map = dict(entry_block.block_fields(block.split('\n')))
    role = field_map.get('Role', '').strip()
    if not role:
        raise ValueError('EX entry block carries no "Role: RL-NNN" field')
    bounds = document.section_bounds(text, role)
    if bounds is None:
        raise ValueError(
            f'no "### {role}" group exists under Experience Entries. Insert the '
            f'{role} role record first; that creates the group.')
    start, end = bounds
    key = sort_key(field_map, new_number)
    # Walk the group's existing entries and stop at the first one that sorts
    # after the newcomer; its start line is the insertion point.
    group_text = '\n'.join(text.split('\n')[start:end])
    for entry in entry_block.parse_blocks(group_text):
        if entry['prefix'] != 'EX':
            continue
        if sort_key(entry['field_map'], entry['number']) > key:
            # Taking the successor's start line means taking its position after
            # the blank that separates it from the entry above, so the blank
            # goes below the newcomer.
            return document.insert_lines(text, start + entry['start'],
                                         block.split('\n') + [''])
    # Nothing sorts after the newcomer, so it closes the group and needs its
    # own separating blank above. A group with no entries yet ends at its own
    # heading line, which is why the blank cannot be assumed to be there.
    at = start + document.last_content_line(group_text) + 1
    return document.insert_lines(text, at, [''] + block.split('\n'))
