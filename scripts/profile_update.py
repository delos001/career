#!/usr/bin/env python3
"""
profile_update.py - deterministic mutations for inventory.md and the staging file

Called by the profile-update skill. Owns every mechanical operation involved in
promoting a staged PU-NNN entry into the profile: reading what is pending,
assigning the next entry ID, placing a new entry at its correct position in
inventory.md, rebuilding the table of contents, and clearing the capture out of
the queue once its content is in the profile.

The staging file is a queue, not an archive. A capture sits in it only while it
is waiting to be promoted; once its content is in the inventory the capture is
removed, because the inventory is where the information persists. Nothing about
a capture is retained after promotion.

The skill owns the judgment (what the content should say, which entry it belongs
in, whether an existing entry should be enriched instead). This script owns
everything that must not be done by hand: ID assignment, placement order, ToC
integrity, and status bookkeeping.

Eight subcommands:

  pending   List the captures in the queue. Compact output (ID, capture date,
            label, source application) so the skill can plan a run without
            reading the whole staging file into context.
  show      Print one staging entry's full block, for the entry being worked.
  next-id   Print the next unused ID for a prefix, derived by scanning
            inventory.md. Informational; 'insert' assigns IDs itself.
  insert    Place a new entry block into inventory.md. The block file carries
            the entry WITHOUT its 'ID:' line; the script assigns the ID at write
            time so two inserts in one run cannot collide, then prints it.
  set       Replace one field's value on one existing entry. The enrichment
            path: the entry is found by its anchored 'ID:' line rather than by
            matching content, so an edit cannot land on a similar-looking
            neighbour, and the whole entry is re-validated afterwards.
  list-add  Append one item to a list line in a section that holds flat lists
            rather than ID-bearing entries. The third write path: 'insert'
            assigns an ID and 'set' resolves one, so neither can reach a
            section that has none.
  close     Verify where a capture's content landed, then remove the capture
            from the queue. A target is an entry ID or a list address; both are
            checked before anything is deleted.
  drop      Remove a capture that will not be promoted after all. The
            retraction path, and the user's decision alone.

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
            python scripts/profile_update.py set --id EX-060 --field Impact \\
                --value-file <path>
            python scripts/profile_update.py list-add \\
                --target "Technical Experience / Office & Collaboration" \\
                --item Miro
            python scripts/profile_update.py close --pu PU-004 \\
                --targets EX-210 --targets EX-211
            python scripts/profile_update.py drop --pu PU-004
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


def _skeleton_headings(template_text):
    """Return [(depth, heading, is_placeholder)] from the document skeleton.

    The unfiltered reading. Callers that want the section roster take
    template_sections; callers that need to know a section's shape - whether it
    carries sub-headings at all, and whether those are per-user placeholders -
    need the placeholders too, which is why this is separate.
    """
    body = _extract_section(template_text, 'Document skeleton')
    if body is None:
        raise ValueError('inventory template has no "## Document skeleton" section')
    fence = _FENCE_RE.search(body)
    if not fence:
        raise ValueError('inventory template document-skeleton block is not fenced')
    headings = []
    for line in fence.group(1).split('\n'):
        m = re.match(r'^(#{2,3})\s+(.+?)\s*$', line)
        if m:
            headings.append((len(m.group(1)), m.group(2), '{' in m.group(2)))
    return headings


def template_sections(template_text):
    """Return the literal section headings from the document-skeleton fence.

    Placeholder headings (those wrapped in braces, e.g. '### {Category}') are
    the per-user category mechanism and are excluded: their names are derived
    per user, so they are not part of the roster any document must carry.
    """
    return [(depth, heading)
            for depth, heading, placeholder in _skeleton_headings(template_text)
            if not placeholder]


def template_spans(template_text):
    """Return {section: [heading, ...]} - the spans a section is checked in.

    A section the template splits into literal sub-sections is checked per
    sub-section rather than as a whole: 'Entries: None' is a claim about the
    span it sits in, and Professional Training's Completed and In Progress can
    each be empty while the other is not. Placeholder sub-headings are dropped
    upstream by template_sections, so a per-user category set never becomes a
    span of its own. A section with no literal sub-sections is its own span.
    """
    spans = {}
    current = None
    for depth, heading in template_sections(template_text):
        if depth == 2:
            current = heading
            spans[current] = []
        elif current is not None:
            spans[current].append(heading)
    return {section: subs or [section] for section, subs in spans.items()}


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

    Every ATX heading is listed, the ToC's own heading included, indented two
    spaces per depth level below the document title. Returns the text unchanged
    when the document carries no ToC section.
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
            f'no "### {role}" group exists under Experience Entries. Insert the '
            f'{role} role record first; that creates the group.')
    start, end = bounds
    key = _ex_sort_key(field_map, new_number)
    # Walk the group's existing entries and stop at the first one that sorts
    # after the newcomer; its start line is the insertion point.
    group_text = '\n'.join(text.split('\n')[start:end])
    for entry in parse_entries(group_text):
        if entry['prefix'] != 'EX':
            continue
        if _ex_sort_key(entry['field_map'], entry['number']) > key:
            # Taking the successor's start line means taking its position after
            # the blank that separates it from the entry above, so the blank
            # goes below the newcomer.
            return _insert_lines(text, start + entry['start'],
                                 block.split('\n') + [''])
    # Nothing sorts after the newcomer, so it closes the group and needs its
    # own separating blank above. A group with no entries yet ends at its own
    # heading line, which is why the blank cannot be assumed to be there.
    at = start + _last_content_line(group_text) + 1
    return _insert_lines(text, at, [''] + block.split('\n'))


def _place_rl(text, block):
    """Return text with an RL record placed reverse-chronologically.

    A role that will carry EX entries also needs its '### RL-NNN' group under
    Experience Entries: that group is where EX entries land, and without it the
    next EX insert has nowhere to go. Both halves are written here so a new role
    is never left half-created. A background role - one asserting 'Entries:
    None' - is placed without a group, matching the existing background roles.
    """
    field_map = dict(
        re.match(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$', line).groups()
        for line in block.split('\n')
        if re.match(r'^([A-Za-z][A-Za-z &-]*):\s?(.*)$', line)
    )
    start_date = field_map.get('Start Date', '').strip()
    if not start_date:
        raise ValueError(
            'RL entry block has an empty "Start Date:"; placement is '
            'reverse-chronological and cannot be computed without it')
    bounds = _section_bounds(text, 'Employment & Role History')
    if bounds is None:
        raise ValueError('inventory has no "## Employment & Role History" section')
    start, end = bounds
    section_text = '\n'.join(text.split('\n')[start:end])
    at, lead = None, False
    for entry in parse_entries(section_text):
        if entry['field_map'].get('Start Date', '') < start_date:
            at = start + entry['start']
            break
    if at is None:
        # Oldest role on record: it closes the section and carries its own
        # separating blank above rather than below.
        at, lead = start + _last_content_line(section_text) + 1, True
    text = _insert_lines(
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
    bounds = _section_bounds(text, 'Experience Entries')
    if bounds is None:
        raise ValueError('inventory has no "## Experience Entries" section')
    hist = _section_bounds(text, 'Employment & Role History')
    lines = text.split('\n')
    order = [e['id'] for e in
             parse_entries('\n'.join(lines[hist[0]:hist[1]]))
             if e['prefix'] == 'RL']
    start, end = bounds
    for later in order[order.index(role_id) + 1:]:
        for i in range(start, end):
            if lines[i].strip() == f'### {later}':
                return _insert_lines(text, i, [f'### {role_id}', '', '---', ''])
    section_text = '\n'.join(lines[start:end])
    at = start + _last_content_line(section_text) + 1
    return _insert_lines(text, at, ['', '---', '', f'### {role_id}'])


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
# List sections
# Some sections of the inventory hold flat lists rather than ID-bearing entries.
# Having no IDs, they are unreachable by 'insert' (which assigns one) and by
# 'set' (which resolves one), so until 'list-add' existed the only way to add a
# tool was to hand-edit the document.
#
# Which sections these are is derived from the template, never named here, so a
# list section added to the template later needs no code change. An address is
# written '<Section> / <Category>', or '<Section> / <Category> / <Label>' when
# the category holds more than one line, and is split on ' / ' so a slash inside
# a name ('IRT/IXRS Systems') survives. The same string is what 'close' records
# in the audit line, so an address is both where the item went and how a later
# check re-finds it.
# ---------------------------------------------------------------------------

# The separator between the parts of a list address. Spaces on both sides, so a
# slash inside a category or label name is not an address boundary.
_ADDRESS_SEP = ' / '

# Regex: a bold-labelled list line, e.g. '**EDC Systems:** Medidata RAVE, ...'.
_BOLD_LABEL_RE = re.compile(r'^\*\*([^*]+):\*\*\s+(.*)$')

# Regex: a plain-labelled list line, e.g. 'Oncology: Multiple Myeloma, AML'.
# The label may hold only letters, digits, spaces, '&', '-' and '/', which is
# what keeps a prose line carrying an internal colon ('ICH-GCP (E6, E9); FDA:
# 21 CFR ...') from being misread as a label plus a value.
_PLAIN_LABEL_RE = re.compile(r'^([A-Za-z][A-Za-z0-9 &/-]*):\s+(.*)$')

# Item separators, tried in this order. A line mixing two of them ('IND, IDE,
# NIH-funded trials; randomized controlled trials; ...') splits on the coarser
# one, which is the one separating its top-level items.
_ITEM_DELIMITERS = (' | ', '; ', ', ')


def list_sections(template_text, schemas):
    """Return the template's top-level sections that hold lists, not entries.

    A section qualifies when no entry schema claims it and it carries
    sub-headings. The second half is a prerequisite rather than a heuristic: an
    address reads '<Section> / <Category>', so a section with no categories has
    nothing addressable in it. That is also what keeps the table of contents out
    without naming it - the ToC is generated from the headings and carries none
    of its own, so it excludes itself, as would any other section that holds a
    single generated or free-standing block.
    """
    owned = {schema['section'] for schema in schemas.values()}
    sections, current = [], None
    for depth, heading, _placeholder in _skeleton_headings(template_text):
        if depth == 2:
            current = None if heading in owned else heading
        elif depth == 3 and current and current not in sections:
            sections.append(current)
    return sections


def list_categories(text, section):
    """Return [(category, start_line, end_line)] for one list section."""
    bounds = _section_bounds(text, section)
    if bounds is None:
        return []
    start, end = bounds
    lines = text.split('\n')
    heads = [i for i in range(start + 1, end)
             if re.match(r'^###\s+\S', lines[i])]
    return [(re.match(r'^###\s+(.+?)\s*$', lines[i]).group(1),
             i, heads[n + 1] if n + 1 < len(heads) else end)
            for n, i in enumerate(heads)]


def _list_line_label(line):
    """Return (label, value, bold) for a list line; label is None when absent."""
    m = _BOLD_LABEL_RE.match(line)
    if m:
        return m.group(1), m.group(2), True
    m = _PLAIN_LABEL_RE.match(line)
    if m:
        return m.group(1), m.group(2), False
    return None, line, False


def _list_content_lines(text, start, end):
    """Return [(line_index, line)] for the content of one category span."""
    lines = text.split('\n')
    return [(i, lines[i]) for i in range(start + 1, end)
            if lines[i].strip() and lines[i].strip() != '---']


def item_delimiter(value):
    """Return the separator a list line already uses between its items."""
    return next((d for d in _ITEM_DELIMITERS if d in value),
                _ITEM_DELIMITERS[-1])


def split_items(value):
    """Return the individual items on a list line."""
    return [item.strip() for item in value.split(item_delimiter(value))
            if item.strip()]


def resolve_list_target(text, target, sections):
    """Return the line one list address names, or raise naming the options.

    Returns {'address', 'section', 'category', 'label', 'bold', 'line',
    'value'}. Raises ValueError with the valid choices spelled out at whichever
    part of the address failed, so a mistyped category never has to be found by
    reading the document.
    """
    parts = [p.strip() for p in target.split(_ADDRESS_SEP)]
    if len(parts) not in (2, 3):
        raise ValueError(
            f'"{target}" is not a list address; write it as '
            f'"<Section>{_ADDRESS_SEP}<Category>" or '
            f'"<Section>{_ADDRESS_SEP}<Category>{_ADDRESS_SEP}<Label>"')
    section, category = parts[0], parts[1]
    wanted = parts[2] if len(parts) == 3 else None

    if section not in sections:
        raise ValueError(
            f'"{section}" is not a list section; the template defines '
            f"{', '.join(f'{s!r}' for s in sections)}")
    categories = list_categories(text, section)
    match = next((c for c in categories if c[0] == category), None)
    if match is None:
        raise ValueError(
            f'"{section}" has no "{category}" category; it holds '
            f"{', '.join(repr(c[0]) for c in categories)}")

    content = _list_content_lines(text, match[1], match[2])
    if not content:
        raise ValueError(f'"{section}{_ADDRESS_SEP}{category}" holds no lines')
    labelled = [(i, *_list_line_label(line)) for i, line in content]

    if wanted is None:
        if len(labelled) > 1:
            raise ValueError(
                f'"{section}{_ADDRESS_SEP}{category}" holds more than one line; '
                f'name which one: '
                f"{', '.join(repr(l[1]) for l in labelled if l[1])}")
        i, label, value, bold = labelled[0]
    else:
        hit = next((l for l in labelled if l[1] == wanted), None)
        if hit is None:
            raise ValueError(
                f'"{section}{_ADDRESS_SEP}{category}" has no "{wanted}" line; '
                f"it holds {', '.join(repr(l[1]) for l in labelled if l[1])}")
        i, label, value, bold = hit

    return {
        'address': _ADDRESS_SEP.join(p for p in (section, category, label) if p),
        'section': section, 'category': category, 'label': label,
        'bold': bold, 'line': i, 'value': value.strip(),
    }


def render_list_line(label, value, bold):
    """Return a list line rebuilt from its parts, preserving the label form."""
    if not label:
        return value
    return f'**{label}:** {value}' if bold else f'{label}: {value}'


# ---------------------------------------------------------------------------
# Subcommand: list-add
# Appends one item to the line an address names, using the separator that line
# already uses. Deliberately additive: it cannot drop or reorder what is there,
# which is the failure mode a whole-line rewrite invites on a roster of thirty
# tool names.
# ---------------------------------------------------------------------------

def cmd_list_add(args, repo_root, cfg):
    """Append one item to a list line and print the address it landed under."""
    inventory_path = _inventory_path(repo_root, cfg)
    text = _util.read(inventory_path)
    template_text = _util.read(_template_path(repo_root, cfg))
    sections = list_sections(template_text, parse_template(template_text))

    found = resolve_list_target(text, args.target, sections)
    item = args.item.strip()
    if not item:
        raise ValueError('--item is empty; list-add writes an item')

    delimiter = item_delimiter(found['value'])
    if delimiter.strip() and delimiter.strip() in item:
        raise ValueError(
            f'"{item}" contains "{delimiter.strip()}", which separates items on '
            f'this line; add it as two items or write it without the separator')
    existing = split_items(found['value'])
    duplicate = next((e for e in existing if e.lower() == item.lower()), None)
    if duplicate is not None:
        raise ValueError(
            f'"{duplicate}" is already listed under "{found["address"]}"')

    lines = text.split('\n')
    lines[found['line']] = render_list_line(
        found['label'], found['value'] + delimiter + item, found['bold'])
    _util.write(inventory_path, '\n'.join(lines))
    print(found['address'])


# ---------------------------------------------------------------------------
# Staging file operations
# The staging file is the run's work list. 'pending' and 'show' read it;
# 'close' writes the status flip plus the audit line that records which profile
# IDs now carry the staged content.
# ---------------------------------------------------------------------------

# Regex: a staging entry heading, e.g. '### PU-004 - Oncology trial leadership'.
_PU_HEADING_RE = re.compile(r'^### (PU-\d+)\s+-\s+(.*?)\s*$', re.MULTILINE)


def parse_staging(staging_text):
    """Return every capture in the queue with its bounds and header fields.

    There is no status field to read: a capture is in the file because it is
    waiting, and it leaves the file when it is done.
    """
    lines = staging_text.split('\n')
    heads = [(i, m.group(1), m.group(2))
             for i, line in enumerate(lines)
             for m in [_PU_HEADING_RE.match(line)] if m]
    entries = []
    for idx, (start, pu_id, label) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        body = '\n'.join(lines[start:end])
        entries.append({
            'id': pu_id,
            'label': label,
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
# One line per capture. Everything in the file is waiting, so there is nothing
# to filter. Deliberately compact: the skill plans a run from this list and
# pulls full content per capture with 'show', so the staging file never enters
# context wholesale.
# ---------------------------------------------------------------------------

def cmd_pending(args, repo_root, cfg):
    """Print the captures waiting in the queue."""
    staging_path = _staging_path(repo_root, cfg)
    if not os.path.exists(staging_path):
        print('no staging file; nothing pending')
        return
    entries = parse_staging(_util.read(staging_path))
    if not entries:
        print('nothing pending')
        return
    for e in entries:
        print(f"{e['id']}  {e['captured']}  {e['label']}")
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
# Subcommand: set
# The enrichment path. An enrichment rewrites part of an entry that already
# exists, which by hand means matching a snippet of a 3000-line document and
# hoping it is unique. Here the entry is located by its anchored 'ID:' line and
# only the named field's span is replaced, so the edit cannot land on a
# neighbour, cannot drop a sibling field, and cannot reorder the roster. The
# whole entry is re-validated against the template before anything is written.
# ---------------------------------------------------------------------------

def cmd_set(args, repo_root, cfg):
    """Replace one field's value on one existing entry."""
    inventory_path = _inventory_path(repo_root, cfg)
    text = _util.read(inventory_path)
    schemas = parse_template(_util.read(_template_path(repo_root, cfg)))

    entry = next((e for e in parse_entries(text) if e['id'] == args.id), None)
    if entry is None:
        raise ValueError(f'entry not found in inventory: {args.id}')
    schema = schemas.get(entry['prefix'])
    if schema is None:
        raise ValueError(
            f'the template defines no schema for {entry["prefix"]} entries')
    roster = [label for label, _ in schema['fields']]
    if args.field == 'ID':
        raise ValueError('IDs are assigned once and are never rewritten')
    if args.field not in roster:
        raise ValueError(
            f'{entry["prefix"]} entries carry no "{args.field}:" field; the '
            f"template defines {', '.join(f for f in roster if f != 'ID')}")

    value = _util.read(args.value_file).rstrip()
    if not value:
        raise ValueError(
            f'{args.value_file} is empty; set writes a value, it does not '
            f'remove a field')
    # A value opening with a newline is a multi-line field (Coursework), whose
    # label sits alone on its line with the value indented beneath it.
    rendered = (f'{args.field}:{value}' if value.startswith('\n')
                else f'{args.field}: {value}').split('\n')

    lines = text.split('\n')
    body = lines[entry['start']:entry['end']]
    new_body = _set_field(body, args.field, rendered, roster)

    # Re-validate the whole entry, minus its ID line, exactly as an insert is
    # validated. A value that breaks the roster or the field order never lands.
    _validate_block(
        '\n'.join(l for l in new_body if not re.match(r'^ID:\s', l)).strip(),
        schema, entry['prefix'])
    _util.write(inventory_path,
                '\n'.join(lines[:entry['start']] + new_body
                          + lines[entry['end']:]))
    print(f'{args.id} {args.field} updated')


def _set_field(body, field, rendered, roster):
    """Return an entry's lines with one field's span replaced or inserted.

    A field the entry already carries is replaced across its full span, which
    for a multi-line field runs to the next field label. A field it does not
    carry is an omitted optional one, and is inserted at its template position
    so the roster stays in canonical order.
    """
    label_re = re.compile(r'^([A-Za-z][A-Za-z &-]*):')
    at = next((i for i, line in enumerate(body)
               if line.startswith(f'{field}:')), None)
    if at is not None:
        stop = next((j for j in range(at + 1, len(body))
                     if label_re.match(body[j])), None)
        if stop is None:
            # Last field in the entry: stop at its final line of content so the
            # blank line separating this entry from the next one survives.
            stop = _last_content_line('\n'.join(body)) + 1
        return body[:at] + rendered + body[stop:]
    later = roster[roster.index(field) + 1:]
    at = next((i for i, line in enumerate(body)
               for m in [label_re.match(line)] if m and m.group(1) in later),
              None)
    if at is None:
        at = _last_content_line('\n'.join(body)) + 1
    return body[:at] + rendered + body[at:]


# ---------------------------------------------------------------------------
# Subcommand: close
# Takes a promoted capture out of the queue. The targets are verified first, so
# a typo is caught while the capture is still there to correct against rather
# than after it is gone; once they check out the capture is deleted, because the
# inventory now carries the information and the queue holds only what is
# waiting. 'no change' is a valid target list: deciding a capture needs no
# profile edit finishes it just as much as writing an entry does.
# ---------------------------------------------------------------------------

# Separator between targets when several are reported together. A semicolon
# rather than a comma because a list address can itself carry one
# ('Programming, Data & Analytics').
TARGET_SEP = '; '

# Regex: an entry-ID-shaped target, as opposed to a list address.
_ID_RE = re.compile(r'^[A-Z]+-\d+$')


def verify_targets(targets, inventory_text, template_text, schemas):
    """Return one plain-English problem per target that does not resolve.

    A target is either an entry ID or a list address. An ID whose prefix the
    inventory template does not define is a narrative or positioning ID living
    in a file this script cannot see, so it passes unverified rather than
    failing a legitimate cross-document promotion. Those documents have no
    structure-authority template yet; once they do, that branch becomes a real
    check (issue: narratives/positioning template).
    """
    known = {entry['id'] for entry in parse_entries(inventory_text)}
    sections = list_sections(template_text, schemas)
    problems = []
    for target in targets:
        if _ID_RE.match(target):
            if target.split('-')[0] in schemas and target not in known:
                problems.append(f'{target} does not exist in the inventory')
            continue
        try:
            resolve_list_target(inventory_text, target, sections)
        except ValueError as e:
            problems.append(str(e))
    return problems


def cmd_close(args, repo_root, cfg):
    """Verify where a capture's content landed, then take it off the queue."""
    staging_path = _staging_path(repo_root, cfg)
    staging_text = _util.read(staging_path)
    entries = parse_staging(staging_text)
    match = next((e for e in entries if e['id'] == args.pu), None)
    if match is None:
        raise ValueError(f'staging entry not found: {args.pu}')

    targets = [t.strip() for t in args.targets if t.strip()]
    if not targets:
        raise ValueError("--targets is empty; pass a target or 'no change'")
    if targets != ['no change']:
        if 'no change' in targets:
            raise ValueError(
                "'no change' is the whole target list or none of it; it cannot "
                'sit alongside a real target')
        template_text = _util.read(_template_path(repo_root, cfg))
        problems = verify_targets(
            targets, _util.read(_inventory_path(repo_root, cfg)),
            template_text, parse_template(template_text))
        if problems:
            raise ValueError('unresolvable target(s): ' + '; '.join(problems))

    _util.write(staging_path,
                _remove_entry(staging_text, match, len(entries)))
    print(f'{args.pu} cleared from staging; its content is in '
          f'{TARGET_SEP.join(targets)}')


# ---------------------------------------------------------------------------
# Subcommand: drop
# The retraction path, and the only way a capture leaves the queue without its
# content reaching the profile. Both drop and close delete the capture; what
# separates them is the precondition, not the outcome. Close proves the content
# arrived somewhere first; drop is the user deciding it should not.
# ---------------------------------------------------------------------------

# The marker a staging file carries in place of entries when it holds none.
# staging_append.py replaces it on the first append, so a removal puts it back
# when it takes the last capture: without it the next capture would append into
# a file whose shape that replace no longer matches.
_EMPTY_MARKER = '_(none)_'


def cmd_drop(args, repo_root, cfg):
    """Remove a capture that will not be promoted, echoing what it held."""
    staging_path = _staging_path(repo_root, cfg)
    staging_text = _util.read(staging_path)
    entries = parse_staging(staging_text)
    match = next((e for e in entries if e['id'] == args.pu), None)
    if match is None:
        raise ValueError(f'staging entry not found: {args.pu}')

    _util.write(staging_path,
                _remove_entry(staging_text, match, len(entries)))

    # Echo the withdrawn block. The delete is deliberate, but the content took a
    # conversation to produce and nothing else holds it, so it is printed rather
    # than vanishing silently.
    print(f'{args.pu} dropped; it held:\n')
    sys.stdout.write(match['body'] + '\n')


def _remove_entry(staging_text, match, total):
    """Return the staging text with one capture's block taken out."""
    lines = staging_text.split('\n')
    remaining = '\n'.join(lines[:match['start']] + lines[match['end']:])
    if total == 1:
        remaining = _restore_placeholder(remaining)
    return remaining.rstrip() + '\n'


def _restore_placeholder(staging_text):
    """Return the staging text with the empty-file marker put back."""
    m = re.search(r'(?m)^##\s+Entries\s*$', staging_text)
    if not m:
        raise ValueError("staging file has no '## Entries' section")
    tail = staging_text[m.end():].lstrip('\n')
    head = f'{staging_text[:m.end()].rstrip()}\n\n{_EMPTY_MARKER}\n'
    return f'{head}\n{tail}' if tail else head


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

    p_pending = sub.add_parser('pending', help='list the captures in the queue')
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

    p_set = sub.add_parser('set', help="replace one field's value on one entry")
    p_set.add_argument('--id', required=True, help='the entry to edit, e.g. EX-060')
    p_set.add_argument('--field', required=True, help='field label, e.g. Impact')
    p_set.add_argument('--value-file', required=True,
                       help='file holding the new value; open it with a newline '
                            'for a multi-line field such as Coursework')
    p_set.set_defaults(func=cmd_set)

    p_list = sub.add_parser('list-add',
                            help='append one item to a list line')
    p_list.add_argument('--target', required=True,
                        help='"<Section> / <Category>", or '
                             '"<Section> / <Category> / <Label>" when the '
                             'category holds more than one line')
    p_list.add_argument('--item', required=True,
                        help='the item to append, exactly as it should read')
    p_list.set_defaults(func=cmd_list_add)

    p_close = sub.add_parser('close',
                             help='clear a promoted capture off the queue')
    p_close.add_argument('--pu', required=True, help='PU-NNN')
    p_close.add_argument('--targets', action='append', required=True,
                         help="one target per flag, repeatable: an entry ID, a "
                              "list address, or 'no change' on its own")
    p_close.set_defaults(func=cmd_close)

    p_drop = sub.add_parser('drop',
                            help='remove a capture that will not be promoted')
    p_drop.add_argument('--pu', required=True, help='PU-NNN')
    p_drop.set_defaults(func=cmd_drop)

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
