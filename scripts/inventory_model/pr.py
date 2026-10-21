#!/usr/bin/env python3
"""
pr.py - PR (independent and volunteer project) entries

What PR does differently from entry_block. A PR block carries one Objective
and an 'Elements:' list (pr-objective-elements-schema-2026-10):

    Objective: {one sentence}
    Elements:
      - PR-NNN.01: {element}
        Outcome: {observed result}
      - PR-NNN.02: {element}

Each element has its own stable ID, assigned max+1 within the block and never
reused. This module reads elements, assigns the next element ID, adds or edits
one element in the document text, and cuts a single element out of its block
for profile_slice.py. It also holds the Role/Company rule: a PR names its
employer through either 'Role: RL-NNN' or 'Company:', never both
(pr-role-reference-2026-07).

Author    : Jason Delosh
Created   : 2026-10-21
Project   : career
Depends   : none
"""

import re

from inventory_model import entry_block


# Regex: an element line, '  - PR-001.03: text'. Groups: block ID, number, text.
_ELEMENT_RE = re.compile(r'^  - (PR-\d+)\.(\d+):\s?(.*)$')

# Regex: an element's Outcome line, indented under it. Group: the result.
_OUTCOME_RE = re.compile(r'^    Outcome:\s?(.*)$')

# Regex: an element ID on its own, e.g. 'PR-001.03'. Groups: block ID, number.
ELEMENT_ID_RE = re.compile(r'^(PR-\d+)\.(\d+)$')


def role_company_conflict(field_map):
    """Return True when a PR block carries both Role: and Company:."""
    has_role = bool(field_map.get('Role', '').strip())
    has_company = bool(field_map.get('Company', '').strip())
    return has_role and has_company


# ---------------------------------------------------------------------------
# Reading elements
# The list starts after the 'Elements:' label and runs to the first line that
# is neither an element, its Outcome, nor an indented continuation of the
# element above (an element may wrap to a second line when it is too complex
# for one).
# ---------------------------------------------------------------------------

def parse_elements(block_lines):
    """Return [{'id', 'number', 'text', 'outcome', 'start', 'end'}] for a block.

    start and end are line indices into block_lines, end exclusive, covering the
    element line, any continuation line and its Outcome line.
    """
    label = next((i for i, line in enumerate(block_lines)
                  if line.startswith('Elements:')), None)
    if label is None:
        return []
    elements = []
    for i in range(label + 1, len(block_lines)):
        line = block_lines[i]
        m = _ELEMENT_RE.match(line)
        if m:
            elements.append({
                'id': f'{m.group(1)}.{m.group(2)}',
                'number': int(m.group(2)),
                'text': m.group(3).strip(),
                'outcome': '',
                'start': i,
                'end': i + 1,
            })
            continue
        if not elements or not line.startswith('    '):
            break
        o = _OUTCOME_RE.match(line)
        if o:
            elements[-1]['outcome'] = o.group(1).strip()
        else:
            elements[-1]['text'] += ' ' + line.strip()
        elements[-1]['end'] = i + 1
    return elements


def element_ids(inventory_text):
    """Return every element ID in the document."""
    lines = inventory_text.split('\n')
    ids = set()
    for block in entry_block.parse_blocks(inventory_text):
        if block['prefix'] == 'PR':
            body = lines[block['start']:block['end']]
            ids.update(e['id'] for e in parse_elements(body))
    return ids


# ---------------------------------------------------------------------------
# Structural checks (read by profile_update_qc.py, P13 and P14)
# ---------------------------------------------------------------------------

# Fields every block of one project must agree on.
SHARED_FIELDS = ('Role', 'Company', 'Orientation', 'Level', 'Work-state')


def element_problems(block_id, block_lines):
    """Return plain-English problems with one PR block's Elements list.

    Checks that every element belongs to this block and is two-digit padded,
    that every Outcome sits under an element, and that nothing else is in the
    list. Duplicate IDs across the document are checked by the caller.
    """
    problems = []
    label = next((i for i, line in enumerate(block_lines)
                  if line.startswith('Elements:')), None)
    if label is None:
        return problems
    previous = None   # 'element' | 'outcome' | None
    for line in block_lines[label + 1:]:
        if not line.strip() or line.strip() == '---':
            continue
        m = _ELEMENT_RE.match(line)
        if m:
            element_id = f'{m.group(1)}.{m.group(2)}'
            if m.group(1) != block_id:
                problems.append(f'{element_id} sits under {block_id}; an element '
                                f'carries its own block number')
            if len(m.group(2)) != 2:
                problems.append(f'{element_id} is not zero-padded to two digits')
            if not m.group(3).strip():
                problems.append(f'{element_id} has no text')
            previous = 'element'
            continue
        if _OUTCOME_RE.match(line):
            if previous != 'element':
                problems.append(f'{block_id} has an Outcome line that does not sit '
                                f'directly under an element')
            previous = 'outcome'
            continue
        if line.startswith('    ') and previous == 'element':
            continue   # the second line of an element too complex for one
        problems.append(f'{block_id} has a line in Elements that is not an '
                        f'element or an Outcome: "{line.strip()[:60]}"')
    return problems


def project_conflicts(pr_blocks):
    """Return problems where blocks sharing a Project disagree on SHARED_FIELDS.

    pr_blocks are entry_block.parse_blocks dicts for PR blocks. A project with
    a second objective is a second block with the same Project name; both
    describe one piece of work, so they cannot carry different employers or
    framing axes.
    """
    by_project = {}
    for block in pr_blocks:
        name = block['field_map'].get('Project', '').strip()
        if name:
            by_project.setdefault(name, []).append(block)
    problems = []
    for name, blocks in by_project.items():
        for field in SHARED_FIELDS:
            values = {b['field_map'].get(field, '').strip() for b in blocks}
            if len(values) > 1:
                ids = ', '.join(b['id'] for b in blocks)
                problems.append((blocks[0]['id'],
                                 f'blocks of project "{name}" ({ids}) disagree '
                                 f'on {field}'))
    return problems


# ---------------------------------------------------------------------------
# Writing elements
# Both functions return the updated document text; profile_update.py writes it.
# ---------------------------------------------------------------------------

def _render(element_id, text, outcome):
    """Return the lines for one element and its optional Outcome."""
    lines = [f'  - {element_id}: {text}']
    if outcome:
        lines.append(f'    Outcome: {outcome}')
    return lines


def _single_line(value, what):
    """Return value stripped; raise when it is empty or spans several lines."""
    value = value.strip()
    if not value:
        raise ValueError(f'{what} is empty')
    if '\n' in value:
        raise ValueError(f'{what} must be a single line')
    return value


def _find_pr_block(text, block_id):
    """Return the PR block dict for an ID; raise when absent or not a PR."""
    block = next((b for b in entry_block.parse_blocks(text)
                  if b['id'] == block_id), None)
    if block is None:
        raise ValueError(f'entry not found in inventory: {block_id}')
    if block['prefix'] != 'PR':
        raise ValueError(f'{block_id} is not a PR entry; only PR entries carry elements')
    return block


def add_element(text, block_id, element_text, outcome='', retired_ids=()):
    """Return (text, element_id) with a new element appended to a PR block.

    The number is max+1 over the block's current elements and any retired
    ones (retired_ids, from inventory-ret.md), so a retired number a sent CV
    may cite is never issued again.
    """
    element_text = _single_line(element_text, 'element text')
    outcome = _single_line(outcome, 'Outcome') if outcome.strip() else ''
    block = _find_pr_block(text, block_id)
    lines = text.split('\n')
    body = lines[block['start']:block['end']]
    label = next((i for i, line in enumerate(body)
                  if line.startswith('Elements:')), None)
    if label is None:
        raise ValueError(f'{block_id} has no "Elements:" field to add to')
    elements = parse_elements(body)
    retired = [int(m.group(2)) for m in map(ELEMENT_ID_RE.match, retired_ids)
               if m and m.group(1) == block_id]
    number = max([e['number'] for e in elements] + retired, default=0) + 1
    element_id = f'{block_id}.{number:02d}'
    at = block['start'] + (elements[-1]['end'] if elements else label + 1)
    new_lines = lines[:at] + _render(element_id, element_text, outcome) + lines[at:]
    return '\n'.join(new_lines), element_id


def edit_element(text, element_id, element_text=None, outcome=None):
    """Return text with one element's text and/or Outcome replaced."""
    m = ELEMENT_ID_RE.match(element_id)
    if not m:
        raise ValueError(f'not an element ID: {element_id}')
    if element_text is None and outcome is None:
        raise ValueError('nothing to change: give new element text, an Outcome, or both')
    block = _find_pr_block(text, m.group(1))
    lines = text.split('\n')
    body = lines[block['start']:block['end']]
    element = next((e for e in parse_elements(body) if e['id'] == element_id), None)
    if element is None:
        raise ValueError(f'element not found: {element_id}')
    new_text = (_single_line(element_text, 'element text')
                if element_text is not None else element['text'])
    new_outcome = (_single_line(outcome, 'Outcome')
                   if outcome is not None else element['outcome'])
    start = block['start'] + element['start']
    end = block['start'] + element['end']
    new_lines = lines[:start] + _render(element_id, new_text, new_outcome) + lines[end:]
    return '\n'.join(new_lines)


# ---------------------------------------------------------------------------
# Retrieval items
# A PR block is scored as one item for its Objective (ID PR-NNN) and one per
# element (ID PR-NNN.NN), all inheriting the block's employer and axes. Every
# payload leads with the project name, because an element read alone does not
# say which project it belongs to.
# ---------------------------------------------------------------------------

def retrieval_items(base, block_lines):
    """Return the retrieval items for one PR block.

    base is the block's item dict as retrieval_payload builds it (id, employer
    and axis keys, empty description and impact); each item is a copy of it
    with its own id, description (the Objective or element text), impact (the
    element's Outcome) and payload.
    """
    field_map = dict(entry_block.block_fields(block_lines))
    project = field_map.get('Project', '').strip()
    objective = field_map.get('Objective', '').strip()
    items = [dict(base, description=objective, impact='',
                  payload=f'{project}: {objective}'.strip())]
    for element in parse_elements(block_lines):
        payload = f"{project}: {element['text']}"
        if element['outcome']:
            payload += f" Outcome: {element['outcome']}"
        items.append(dict(base, id=element['id'], description=element['text'],
                          impact=element['outcome'], payload=payload.strip()))
    return items


# ---------------------------------------------------------------------------
# Parent and child IDs
# An element is cited alongside its objective, so a citation of either one
# protects the other: neither may be de-emphasized while the CV uses its
# partner.
# ---------------------------------------------------------------------------

def parent_id(entry_id):
    """Return the block ID of an element ID, or None for any other ID."""
    m = ELEMENT_ID_RE.match(entry_id or '')
    return m.group(1) if m else None


def is_cited(entry_id, cited_ids):
    """Return True when an ID, its parent block, or one of its elements is cited."""
    if entry_id in cited_ids:
        return True
    if parent_id(entry_id) in cited_ids:
        return True
    return any(parent_id(c) == entry_id for c in cited_ids)


# ---------------------------------------------------------------------------
# Slicing one element
# A cited element is read with its block's header and Objective, because an
# element is only meaningful inside the project it belongs to.
# ---------------------------------------------------------------------------

def slice_element(block_text, element_id):
    """Return the block's lines up to 'Elements:' plus one element, or None."""
    body = block_text.split('\n')
    element = next((e for e in parse_elements(body) if e['id'] == element_id), None)
    if element is None:
        return None
    label = next(i for i, line in enumerate(body) if line.startswith('Elements:'))
    return '\n'.join(body[:label + 1] + body[element['start']:element['end']])
