#!/usr/bin/env python3
"""
ex.py - EX (experience) entries

What EX does differently from entry_block: where a new entry is placed. EX
entries live in a '### RL-NNN' role group under Experience Entries, and within
it in topic groups, each opened by a '--- <label>' marker line
(ex-topic-groups-2026-10). The order of topic groups within a role, and of
entries within a topic group, is the user's; no sort rule applies. A new entry
closes the topic group it names, and a new topic group closes its role.

Author    : Jason Delosh
Created   : 2026-10-21 (moved from profile_update.py)
Project   : career
Depends   : none
"""

import re

from inventory_model import document, entry_block


# Regex: the line that opens an EX entry. Group 1 is the ID.
_EX_ID_RE = re.compile(r'^ID:\s+(EX-\d+)\s*$')


# ---------------------------------------------------------------------------
# Reading topic groups
# A topic group runs from its marker line to the next marker or the end of the
# role group. Labels are unique within a role (P4 enforces it), which is what
# lets a caller address a group by its label alone.
# ---------------------------------------------------------------------------

def _groups(text, role):
    """Return a role's topic groups with their line spans.

    Each dict: label, marker (line index of the marker), end (line index,
    exclusive), entries (EX IDs in document order). Raises when the role has no
    group under Experience Entries.
    """
    bounds = document.section_bounds(text, role)
    if bounds is None:
        raise ValueError(
            f'no "### {role}" group exists under Experience Entries. Insert the '
            f'{role} role record first; that creates the group.')
    start, end = bounds
    lines = text.split('\n')
    groups = []
    for i in range(start, end):
        m = document.GROUP_MARKER_RE.match(lines[i])
        if m:
            if groups:
                groups[-1]['end'] = i
            groups.append({'label': m.group(1), 'marker': i, 'end': end,
                           'entries': []})
        elif groups:
            m = _EX_ID_RE.match(lines[i])
            if m:
                groups[-1]['entries'].append(m.group(1))
    return groups


def role_groups(text, role):
    """Return [{'label', 'entries'}] for a role's topic groups, in order."""
    return [{'label': g['label'], 'entries': g['entries']}
            for g in _groups(text, role)]


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

def place(text, block, group=None, new_group=None):
    """Return text with an EX block placed in a topic group of its role.

    Exactly one of group (an existing label: the entry closes that group) or
    new_group (a new label: the group is opened at the end of the role and the
    entry is its first) must be given.
    """
    if (group is None) == (new_group is None):
        raise ValueError(
            'an EX insert needs exactly one of --group "<label>" (an existing '
            'topic group in its role) or --new-group "<label>"')
    field_map = dict(entry_block.block_fields(block.split('\n')))
    role = field_map.get('Role', '').strip()
    if not role:
        raise ValueError('EX entry block carries no "Role: RL-NNN" field')
    groups = _groups(text, role)
    labels = [g['label'] for g in groups]
    lines = text.split('\n')

    if new_group is not None:
        if new_group in labels:
            raise ValueError(
                f'{role} already has a "{new_group}" topic group; insert into '
                f'it with --group')
        # The role group closes at its last content line; the new topic group
        # goes after it, behind a separating blank.
        start, end = document.section_bounds(text, role)
        at = start + document.last_content_line('\n'.join(lines[start:end])) + 1
        return document.insert_lines(
            text, at, ['', f'--- {new_group}', ''] + block.split('\n'))

    target = next((g for g in groups if g['label'] == group), None)
    if target is None:
        listed = '; '.join(labels) or 'none'
        raise ValueError(
            f'{role} has no "{group}" topic group. Its groups: {listed}. Use '
            f'--new-group to open one.')
    span = '\n'.join(lines[target['marker']:target['end']])
    at = target['marker'] + document.last_content_line(span) + 1
    return document.insert_lines(text, at, [''] + block.split('\n'))
