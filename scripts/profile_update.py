#!/usr/bin/env python3
"""
profile_update.py - deterministic mutations for inventory.md and the staging file

Called by the profile-update skill. Owns every mechanical operation involved in
promoting a staged item into the profile: reading what is pending, assigning
the next entry ID, placing a new entry at its correct position in inventory.md,
rebuilding the table of contents, and deleting the item from the queue once its
written entry has passed review.

The staging file's '## Entries' section is a queue. An item sits in it only
while it is waiting; once its content is in the inventory and the entry has
passed review, the item is deleted. Nothing records where it went, when, or why
(#70): the profile is the source, and CV traceability cites inventory IDs.
An item is found by its label, which staging_append.py keeps unique.

The skill owns the judgment (what the content should say, which entry it belongs
in, whether an existing entry should be enriched instead). This script owns
everything that must not be done by hand: ID assignment, placement order, and
ToC integrity.

Seven subcommands:

  pending   List the items in the queue. Compact output (label, date, source
            application) so the skill can plan a run without reading the whole
            staging file into context.
  show      Print one item's full block, for the item being worked.
  insert    Place a new entry block into inventory.md. The block file carries
            the entry WITHOUT its 'ID:' line; the script assigns the ID at write
            time so two inserts in one run cannot collide, then prints it.
  set       Replace one field's value on one existing entry. The enrichment
            path: the entry is found by its anchored 'ID:' line rather than by
            matching content, so an edit cannot land on a similar-looking
            neighbour, and the whole entry is re-validated afterwards.
  element   Add one element to a PR entry (assigning PR-NNN.NN, max+1, never
            reused) or edit one element's text and/or Outcome. A PR's Elements
            list is never rewritten through set.
  list-add  Append one item to a list line in a section that holds flat lists
            rather than ID-bearing entries. The third write path: 'insert'
            assigns an ID and 'set' resolves one, so neither can reach a
            section that has none.
  remove    Delete one item from the queue and print what it held. Run after
            the item's entry passes review, so review fixes land while the item
            is still there; also the finish for an item that needed no write or
            that the user retracted.

Nothing about the document's shape is hardcoded. The section roster, the
prefix-to-section mapping, and the per-prefix field rosters are all parsed from
templates/inventory.md at run time, so a schema change is a template edit.
Paths and filenames come from config.yaml.

Author    : Jason Delosh
Created   : 2026-08-24
Project   : career
Usage     : python scripts/profile_update.py pending
            python scripts/profile_update.py show --item "<label>"
            python scripts/profile_update.py insert --prefix EX \\
                --block-file <path> --group "<label>" | --new-group "<label>"
            python scripts/profile_update.py set --id EX-060 \\
                --field Impact --value-file <path>
            python scripts/profile_update.py element --id PR-015 \\
                --text-file <path> [--outcome-file <path>]
            python scripts/profile_update.py element --id PR-015.03 \\
                [--text-file <path>] [--outcome-file <path>]
            python scripts/profile_update.py list-add \\
                --target "Technical Experience / Office & Collaboration" \\
                --item Miro
            python scripts/profile_update.py remove --item "<label>"
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
# Template parsing, section navigation, the table of contents, ID blocks, ID
# assignment and per-type placement live in the shared inventory data model.
from inventory_model import document, entry_block, ex, pr, rl


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
# a name ('IRT/IXRS Systems') survives. The same string is what list-add prints
# and what the QC script takes as a scope, so an address is both where the item
# went and how a later check re-finds it.
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
    for depth, heading, _placeholder in document.skeleton_headings(template_text):
        if depth == 2:
            current = None if heading in owned else heading
        elif depth == 3 and current and current not in sections:
            sections.append(current)
    return sections


def list_categories(text, section):
    """Return [(category, start_line, end_line)] for one list section."""
    bounds = document.section_bounds(text, section)
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
    sections = list_sections(template_text, document.parse_template(template_text))

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
# '## Entries' is the queue: 'pending' and 'show' read it and 'remove' takes an
# item out of it. Parsing is bounded to that section, so text after it can never
# be read as part of the last item.
# ---------------------------------------------------------------------------

# The queue's section heading, by the text document.section_bounds locates it with.
ENTRIES_HEADING = 'Entries'

# Regex: an item heading, e.g. '### Vendor management scope at Northwind'.
_ITEM_HEADING_RE = re.compile(r'^### (.+?)\s*$')

# The marker the queue carries in place of content when it holds none.
# staging_append.py replaces it on the first append, so 'remove' puts it back
# when it takes the last item: without it the next append would land in a
# section whose shape that replace no longer matches.
_EMPTY_MARKER = '_(none)_'


def parse_staging(staging_text):
    """Return every item in the queue with its bounds and header fields.

    Line indices are absolute against the whole file, so a caller that splices
    the text does not have to re-apply the section offset.
    """
    bounds = document.section_bounds(staging_text, ENTRIES_HEADING)
    if bounds is None:
        raise ValueError("staging file has no '## Entries' section")
    section_start, section_end = bounds
    lines = staging_text.split('\n')
    heads = [(i, m.group(1))
             for i in range(section_start + 1, section_end)
             for m in [_ITEM_HEADING_RE.match(lines[i])] if m]
    items = []
    for idx, (start, label) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else section_end
        body = '\n'.join(lines[start:end])
        items.append({
            'label': label,
            'from': bullet_value(body, 'From') or '',
            'captured': bullet_value(body, 'Captured') or '',
            'start': start,
            'end': end,
            'body': body.rstrip(),
        })
    return items


def bullet_value(body, label):
    """Return the value of a '- **<label>:** value' bullet, or None."""
    m = re.search(rf'^-\s+\*\*{re.escape(label)}:\*\*\s*(.*?)\s*$',
                  body, re.MULTILINE)
    return m.group(1) if m else None


def find_item(staging_text, label):
    """Return the queued item with this label, or raise naming the labels."""
    items = parse_staging(staging_text)
    match = next((i for i in items if i['label'] == label), None)
    if match is None:
        waiting = ', '.join(f'"{i["label"]}"' for i in items) or 'none'
        raise ValueError(f'no item labelled "{label}" is waiting; waiting: {waiting}')
    return match


# ---------------------------------------------------------------------------
# Subcommand: pending
# One line per item. Everything in the queue is waiting, so there is nothing to
# filter. Deliberately compact: the skill plans a run from this list and pulls
# full content per item with 'show', so the staging file never enters context
# wholesale.
# ---------------------------------------------------------------------------

def cmd_pending(args, repo_root, cfg):
    """Print the items waiting in the queue."""
    staging_path = _staging_path(repo_root, cfg)
    if not os.path.exists(staging_path):
        print('no staging file; nothing pending')
        return
    items = parse_staging(_util.read(staging_path))
    if not items:
        print('nothing pending')
        return
    for item in items:
        print(f"{item['captured']}  {item['label']}")
        print(f"            from {item['from']}")
    print(f'\n{len(items)} pending')


# ---------------------------------------------------------------------------
# Subcommand: show
# Full block for one item, including the capture fields the skill needs in
# order to judge what to write.
# ---------------------------------------------------------------------------

def cmd_show(args, repo_root, cfg):
    """Print one item's full block."""
    item = find_item(_util.read(_staging_path(repo_root, cfg)), args.item)
    sys.stdout.write(item['body'] + '\n')


# ---------------------------------------------------------------------------
# Subcommand: insert
# Assigns the ID, places the block, rebuilds the ToC, writes, and echoes the
# assigned ID so the caller can pass it to the QC script as a scope.
# ---------------------------------------------------------------------------

def cmd_insert(args, repo_root, cfg):
    """Place a new entry into inventory.md and print its assigned ID."""
    inventory_path = _inventory_path(repo_root, cfg)
    text = _util.read(inventory_path)
    schemas = document.parse_template(_util.read(_template_path(repo_root, cfg)))

    if args.prefix not in schemas:
        raise ValueError(
            f'unknown entry prefix: {args.prefix}; the template defines '
            f"{', '.join(sorted(schemas))}")

    block = _util.read(args.block_file).strip()
    if re.match(r'^ID:\s', block):
        raise ValueError(
            'block file carries its own "ID:" line; omit it. This command '
            'assigns the ID so concurrent inserts cannot collide.')
    if args.prefix == 'PR' and re.search(r'^  - ', block, re.MULTILINE):
        raise ValueError(
            'PR block carries element lines; insert it with an empty '
            '"Elements:" field, then add each element with the element command, '
            'which assigns its ID.')

    # Validate the block against the template roster before touching the file.
    entry_block.validate_block(block, schemas[args.prefix], args.prefix)

    assigned = entry_block.next_id(text, args.prefix)
    block = f'ID: {assigned}\n{block}'

    if args.prefix != 'EX' and (args.group or args.new_group):
        raise ValueError('--group and --new-group apply to EX entries only')
    if args.prefix == 'EX':
        text = ex.place(text, block, args.group, args.new_group)
    elif args.prefix == 'RL':
        text = rl.place(text, block)
    else:
        text = entry_block.place_append(
            text, block, schemas[args.prefix]['section'], args.subsection)

    text = document.rebuild_toc(text)
    _util.write(inventory_path, text)
    print(assigned)


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
    schemas = document.parse_template(_util.read(_template_path(repo_root, cfg)))

    entry = next((e for e in entry_block.parse_blocks(text)
                  if e['id'] == args.id), None)
    if entry is None:
        raise ValueError(f'entry not found in inventory: {args.id}')
    schema = schemas.get(entry['prefix'])
    if schema is None:
        raise ValueError(
            f'the template defines no schema for {entry["prefix"]} entries')
    roster = [label for label, _ in schema['fields']]
    if args.field == 'ID':
        raise ValueError('IDs are assigned once and are never rewritten')
    if args.field == 'Elements':
        raise ValueError(
            'Elements is edited one element at a time with the element command, '
            'so no element ID is lost or reused')
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
    entry_block.validate_block(
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
            stop = document.last_content_line('\n'.join(body)) + 1
        return body[:at] + rendered + body[stop:]
    later = roster[roster.index(field) + 1:]
    at = next((i for i, line in enumerate(body)
               for m in [label_re.match(line)] if m and m.group(1) in later),
              None)
    if at is None:
        at = document.last_content_line('\n'.join(body)) + 1
    return body[:at] + rendered + body[at:]


# ---------------------------------------------------------------------------
# Subcommand: element
# A PR's Elements field is a list, each item with its own permanent ID, so it
# is written one element at a time rather than through set: set would rewrite
# the whole list and could drop or renumber an element a sent CV cites. Adding
# assigns the next number in the block (max+1, never reused); editing replaces
# one element's text and/or Outcome and keeps its ID.
# ---------------------------------------------------------------------------

def cmd_element(args, repo_root, cfg):
    """Add an element to a PR block, or edit one, and print its element ID."""
    inventory_path = _inventory_path(repo_root, cfg)
    text = _util.read(inventory_path)
    element_text = _util.read(args.text_file) if args.text_file else None
    outcome = _util.read(args.outcome_file) if args.outcome_file else None

    if pr.ELEMENT_ID_RE.match(args.id):
        text = pr.edit_element(text, args.id, element_text, outcome)
        element_id = args.id
    else:
        if element_text is None:
            raise ValueError('adding an element needs --text-file')
        retired_path = _retired_path(repo_root, cfg)
        retired = (entry_block.retired_rows(_util.read(retired_path))
                   if os.path.exists(retired_path) else {})
        text, element_id = pr.add_element(text, args.id, element_text,
                                          outcome or '', retired)
    _util.write(inventory_path, text)
    print(element_id)


# ---------------------------------------------------------------------------
# Subcommand: remove
# Deletes one item from the queue. The skill runs it only after the item's
# written entry has passed review, so a fix the review asks for lands while the
# item is still there to work from (#70: removing first made every review fix
# fail). It is also the finish for an item whose substance the profile already
# carried, and for one the user retracted. Nothing is recorded; the block is
# printed so a removal is never silent.
# ---------------------------------------------------------------------------

def cmd_remove(args, repo_root, cfg):
    """Delete one item from the queue and print what it held."""
    staging_path = _staging_path(repo_root, cfg)
    staging_text = _util.read(staging_path)
    item = find_item(staging_text, args.item)
    lines = staging_text.split('\n')
    remaining = '\n'.join(lines[:item['start']] + lines[item['end']:])
    if not parse_staging(remaining):
        remaining = _restore_placeholder(remaining)
    _util.write(staging_path, remaining.rstrip() + '\n')
    print(f'removed "{args.item}"; it held:\n')
    sys.stdout.write(item['body'] + '\n')


def _restore_placeholder(staging_text):
    """Return the staging text with the queue's empty marker put back."""
    bounds = document.section_bounds(staging_text, ENTRIES_HEADING)
    if bounds is None:
        raise ValueError("staging file has no '## Entries' section")
    start, end = bounds
    lines = staging_text.split('\n')
    return '\n'.join(lines[:start + 1] + ['', _EMPTY_MARKER, ''] + lines[end:])


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _inventory_path(repo_root, cfg):
    """Return the absolute path of the user's inventory document."""
    return os.path.join(repo_root, cfg['paths']['profile'],
                        cfg['filenames']['inventory_file'])


def _narratives_path(repo_root, cfg):
    """Return the absolute path of the user's narratives document."""
    return os.path.join(repo_root, cfg['paths']['profile'],
                        cfg['filenames']['narratives_file'])


def _retired_path(repo_root, cfg):
    """Return the absolute path of the retired-ID log (inventory-ret.md)."""
    return os.path.join(repo_root, cfg['paths']['profile'],
                        cfg['filenames']['inventory_retired_file'])


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

    p_pending = sub.add_parser('pending',
                               help='list the items in the queue')
    p_pending.set_defaults(func=cmd_pending)

    p_show = sub.add_parser('show', help='print one staged item in full')
    p_show.add_argument('--item', required=True, help="the item's label")
    p_show.set_defaults(func=cmd_show)

    p_insert = sub.add_parser('insert', help='place a new entry into inventory.md')
    p_insert.add_argument('--prefix', required=True)
    p_insert.add_argument('--block-file', required=True,
                          help='entry block WITHOUT its ID: line')
    p_insert.add_argument('--subsection',
                          help='sub-section heading when the section has one '
                               '(e.g. Completed / In Progress for TR entries)')
    p_insert.add_argument('--group',
                          help='EX only: the existing topic group in the entry\'s '
                               'role that the entry closes')
    p_insert.add_argument('--new-group',
                          help='EX only: the label of a new topic group, opened '
                               'at the end of the role with this entry')
    p_insert.set_defaults(func=cmd_insert)

    p_set = sub.add_parser('set', help="replace one field's value on one entry")
    p_set.add_argument('--id', required=True, help='the entry to edit, e.g. EX-060')
    p_set.add_argument('--field', required=True, help='field label, e.g. Impact')
    p_set.add_argument('--value-file', required=True,
                       help='file holding the new value; open it with a newline '
                            'for a multi-line field such as Coursework')
    p_set.set_defaults(func=cmd_set)

    p_elem = sub.add_parser(
        'element', help='add an element to a PR entry, or edit one')
    p_elem.add_argument('--id', required=True,
                        help='PR-NNN to add a new element to, or PR-NNN.NN to '
                             'edit an existing one')
    p_elem.add_argument('--text-file',
                        help='file holding the element text (one line); '
                             'required when adding')
    p_elem.add_argument('--outcome-file',
                        help='file holding the observed Outcome (one line)')
    p_elem.set_defaults(func=cmd_element)

    p_list = sub.add_parser('list-add',
                            help='append one item to a list line')
    p_list.add_argument('--target', required=True,
                        help='"<Section> / <Category>", or '
                             '"<Section> / <Category> / <Label>" when the '
                             'category holds more than one line')
    p_list.add_argument('--item', required=True,
                        help='the item to append, exactly as it should read')
    p_list.set_defaults(func=cmd_list_add)

    p_remove = sub.add_parser(
        'remove', help='delete one item from the queue after review passes, '
                       'or when it needed no write or was retracted')
    p_remove.add_argument('--item', required=True, help="the item's label")
    p_remove.set_defaults(func=cmd_remove)

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
