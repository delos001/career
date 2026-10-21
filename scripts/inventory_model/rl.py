#!/usr/bin/env python3
"""
rl.py - RL (role) records

What RL does differently from entry_block: where a new record is placed.
Role records run reverse-chronologically by Start Date under Employment & Role
History, and a role that will carry EX entries also gets its '### RL-NNN'
group under Experience Entries.

Author    : Jason Delosh
Created   : 2026-10-21 (moved from profile_update.py)
Project   : career
Depends   : none
"""

from inventory_model import document, entry_block


def place(text, block):
    """Return text with an RL record placed reverse-chronologically.

    A role that will carry EX entries also needs its '### RL-NNN' group under
    Experience Entries: that group is where EX entries land, and without it the
    next EX insert has nowhere to go. Both halves are written here so a new role
    is never left half-created. A background role - one asserting 'Entries:
    None' - is placed without a group, matching the existing background roles.
    """
    field_map = dict(entry_block.block_fields(block.split('\n')))
    start_date = field_map.get('Start Date', '').strip()
    if not start_date:
        raise ValueError(
            'RL entry block has an empty "Start Date:"; placement is '
            'reverse-chronological and cannot be computed without it')
    bounds = document.section_bounds(text, 'Employment & Role History')
    if bounds is None:
        raise ValueError('inventory has no "## Employment & Role History" section')
    start, end = bounds
    section_text = '\n'.join(text.split('\n')[start:end])
    at, lead = None, False
    for entry in entry_block.parse_blocks(section_text):
        if entry['field_map'].get('Start Date', '') < start_date:
            at = start + entry['start']
            break
    if at is None:
        # Oldest role on record: it closes the section and carries its own
        # separating blank above rather than below.
        at, lead = start + document.last_content_line(section_text) + 1, True
    text = document.insert_lines(
        text, at,
        [''] + block.split('\n') if lead else block.split('\n') + [''])

    if field_map.get('Entries', '').strip() == 'None':
        return text
    return _add_role_group(text, field_map.get('ID', '').strip())


def _add_role_group(text, role_id):
    """Return text with a '### <role_id>' group added under Experience Entries.

    Groups run in the same order as the role records, so the new group goes
    immediately before the group of the next role record that has one. Roles
    without a group (background roles) are skipped over. When no later role has
    a group, the new group closes the section.
    """
    if not role_id:
        raise ValueError('RL entry block carries no "ID:" line to name its group')
    bounds = document.section_bounds(text, 'Experience Entries')
    if bounds is None:
        raise ValueError('inventory has no "## Experience Entries" section')
    hist = document.section_bounds(text, 'Employment & Role History')
    lines = text.split('\n')
    order = [e['id'] for e in
             entry_block.parse_blocks('\n'.join(lines[hist[0]:hist[1]]))
             if e['prefix'] == 'RL']
    start, end = bounds
    for later in order[order.index(role_id) + 1:]:
        for i in range(start, end):
            if lines[i].strip() == f'### {later}':
                return document.insert_lines(
                    text, i, [f'### {role_id}', '', '---', ''])
    section_text = '\n'.join(lines[start:end])
    at = start + document.last_content_line(section_text) + 1
    return document.insert_lines(text, at, ['', '---', '', f'### {role_id}'])
