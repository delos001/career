#!/usr/bin/env python3
"""
profile_update.py - deterministic mutations for inventory.md and the staging file

Called by the profile-update skill. Owns every mechanical operation involved in
promoting a staged PU-NNN entry into the profile: reading what is pending,
assigning the next entry ID, placing a new entry at its correct position in
inventory.md, rebuilding the table of contents, and clearing the PU
entry out of the queue once its content is in the profile.

The staging file's '## Entries' section is a queue. A PU entry sits in it only
while it is waiting to be promoted; once its content is in the inventory the
PU entry's body is removed, because the inventory is where the information
persists.

What is retained is one line under '## Migrated' recording that PU entry's
number and what became of it. Two things outlive a PU entry and need that
line: the PU-NNN counter, which would otherwise walk backwards as entries are
promoted and reissue a number a closed application already cites, and the
'Closure ref: PU-NNN' pointers written permanently into past gap_analysis.md
artifacts.

The skill owns the judgment (what the content should say, which entry it belongs
in, whether an existing entry should be enriched instead). This script owns
everything that must not be done by hand: ID assignment, placement order, ToC
integrity, and status bookkeeping.

Nine subcommands. The ones that change a profile document each take --pu and
leave a '- **Written:**' bullet on that PU entry naming what they changed, and
'close' builds its migrated line out of those bullets:

  pending   List the PU entries in the queue. Compact output (ID, date, label,
            source application) so the skill can plan a run without reading the
            whole staging file into context.
  show      Print one PU entry's full block, for the entry being worked.
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
  record    Leave a Written bullet for an edit this script did not make: an
            enrichment of narratives.md or positioning.md, which have no
            structure-authority template and so are edited by hand.
  close     Re-verify the targets a PU entry records having been written to,
            then move it out of the queue and record it under '## Migrated'
            against those targets. --duplicate finishes an entry that needed no
            write because the profile already carried the substance.
  drop      Move a PU entry that will not be promoted after all out of the
            queue, recording it as 'dropped'. The retraction path, and the
            user's decision alone.

Nothing about the document's shape is hardcoded. The section roster, the
prefix-to-section mapping, and the per-prefix field rosters are all parsed from
templates/inventory.md at run time, so a schema change is a template edit.
Paths and filenames come from config.yaml.

Author    : Jason Delosh
Created   : 2026-08-24
Project   : career
Usage     : python scripts/profile_update.py pending
            python scripts/profile_update.py show --pu PU-004
            python scripts/profile_update.py insert --prefix EX --pu PU-004 \\
                --block-file <path>
            python scripts/profile_update.py set --id EX-060 --pu PU-004 \\
                --field Impact --value-file <path>
            python scripts/profile_update.py element --id PR-015 --pu PU-004 \\
                --text-file <path> [--outcome-file <path>]
            python scripts/profile_update.py element --id PR-015.03 --pu PU-004 \\
                [--text-file <path>] [--outcome-file <path>]
            python scripts/profile_update.py list-add --pu PU-004 \\
                --target "Technical Experience / Office & Collaboration" \\
                --item Miro
            python scripts/profile_update.py record --pu PU-004 --target ST-011
            python scripts/profile_update.py close --pu PU-004
            python scripts/profile_update.py close --pu PU-004 --duplicate
            python scripts/profile_update.py drop --pu PU-004
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
    _record_write(repo_root, cfg, args.pu, found['address'])
    print(found['address'])


# ---------------------------------------------------------------------------
# Staging file operations
# The file carries two sections. '## Entries' is the queue: 'pending' and 'show'
# read it, and 'close' and 'drop' take PU entries out of it. '## Migrated' is
# the permanent record of every PU entry that has left, one line each, and is
# only ever appended to.
#
# The split is why both parsers work on section spans rather than on the whole
# file. A whole-file scan for entry headings would let the last PU entry's body
# run on into the migrated list, and a whole-file scan for the '_(none)_' marker
# could not tell which of the two empty sections it belonged to.
# ---------------------------------------------------------------------------

# The two section headings, by the text document.section_bounds locates them with.
ENTRIES_HEADING = 'Entries'
MIGRATED_HEADING = 'Migrated'

# Regex: a staging entry heading, e.g. '### PU-004 - Oncology trial leadership'.
_PU_HEADING_RE = re.compile(r'^### (PU-\d+)\s+-\s+(.*?)\s*$', re.MULTILINE)

# Regex: a migrated line, e.g. 'PU-005: EX-229; EX-230' or 'PU-008: dropped'.
_MIGRATED_LINE_RE = re.compile(r'^(PU-\d+):\s*(.+?)\s*$')


def parse_staging(staging_text):
    """Return every PU entry in the queue with its bounds and header fields.

    Bounded to '## Entries'. There is no status field to read: a PU entry is in
    that section because it is waiting, and it leaves when it is done.

    Line indices are absolute against the whole file, so a caller that splices
    the text does not have to re-apply the section offset.
    """
    bounds = document.section_bounds(staging_text,ENTRIES_HEADING)
    if bounds is None:
        raise ValueError("staging file has no '## Entries' section")
    section_start, section_end = bounds
    lines = staging_text.split('\n')
    heads = [(i, m.group(1), m.group(2))
             for i in range(section_start, section_end)
             for m in [_PU_HEADING_RE.match(lines[i])] if m]
    entries = []
    for idx, (start, pu_id, label) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else section_end
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


def parse_migrated(staging_text):
    """Return {PU-NNN: outcome} for every PU entry that has left the queue.

    The outcome is the targets its content landed in, 'dropped', or
    'duplicate'. Returns an empty mapping when the file predates the section,
    so a caller can tell "nothing has migrated" from "this file cannot record
    a migration" - which is what _record_migrated raises on.
    """
    bounds = document.section_bounds(staging_text, MIGRATED_HEADING)
    if bounds is None:
        return {}
    start, end = bounds
    lines = staging_text.split('\n')
    return {m.group(1): m.group(2)
            for i in range(start + 1, end)
            for m in [_MIGRATED_LINE_RE.match(lines[i])] if m}


def _bullet_value(body, label):
    """Return the value of a '- **<label>:** value' bullet, or None."""
    m = re.search(rf'^-\s+\*\*{re.escape(label)}:\*\*\s*(.*?)\s*$',
                  body, re.MULTILINE)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Written bullets - the record of what a run actually changed
# Every command that edits a profile document appends a '- **Written:**' bullet
# to the PU entry it was working, naming the entry ID or list address it just
# changed. 'close' then builds the migrated line out of those bullets instead of
# out of a target list typed at the end.
#
# The difference matters because only a newly inserted entry proves its own
# write: an enriched entry and a list category both existed before the run, so
# checking that they exist says nothing about whether anything reached them. A
# bullet is written by the command that did the work, so it cannot claim a write
# that did not happen.
#
# The bullets live on the PU entry and are deleted with it, so nothing is
# retained past the migrated line.
# ---------------------------------------------------------------------------

_WRITTEN_LABEL = 'Written'


def written_targets(entry_body):
    """Return every target a PU entry records having been written to."""
    return re.findall(
        rf'(?m)^-\s+\*\*{_WRITTEN_LABEL}:\*\*\s*(.+?)\s*$', entry_body)


def _record_write(repo_root, cfg, pu_id, target):
    """Append a '- **Written:** <target>' bullet to one PU entry.

    Called after the profile document has already been changed, so a failure
    here means the change landed but went unrecorded; the error says so rather
    than leaving the caller to guess. Repeating a target (two fields set on one
    entry) records it once.
    """
    staging_path = _staging_path(repo_root, cfg)
    text = _util.read(staging_path)
    entry = next((e for e in parse_staging(text) if e['id'] == pu_id), None)
    if entry is None:
        raise ValueError(
            f'the profile document was changed, but {pu_id} is not in the '
            f'staging queue so the change could not be recorded against it')
    if target in written_targets(entry['body']):
        return
    lines = text.split('\n')
    at = max(i for i in range(entry['start'], entry['end'])
             if lines[i].strip().startswith('- **')) + 1
    _util.write(staging_path, '\n'.join(
        lines[:at] + [f'- **{_WRITTEN_LABEL}:** {target}'] + lines[at:]))


# ---------------------------------------------------------------------------
# Subcommand: pending
# One line per PU entry. Everything in the file is waiting, so there is nothing
# to filter. Deliberately compact: the skill plans a run from this list and
# pulls full content per PU entry with 'show', so the staging file never enters
# context wholesale.
# ---------------------------------------------------------------------------

def cmd_pending(args, repo_root, cfg):
    """Print the PU entries waiting in the queue."""
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
# Subcommand: insert
# Assigns the ID, places the block, rebuilds the ToC, writes, and echoes the
# assigned ID so the caller can record it in the staging entry's audit line.
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
    number = int(assigned.split('-')[1])
    block = f'ID: {assigned}\n{block}'

    if args.prefix == 'EX':
        text = ex.place(text, block, number)
    elif args.prefix == 'RL':
        text = rl.place(text, block)
    else:
        text = entry_block.place_append(
            text, block, schemas[args.prefix]['section'], args.subsection)

    text = document.rebuild_toc(text)
    _util.write(inventory_path, text)
    _record_write(repo_root, cfg, args.pu, assigned)
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
    _record_write(repo_root, cfg, args.pu, args.id)
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
    _record_write(repo_root, cfg, args.pu, element_id)
    print(element_id)


# ---------------------------------------------------------------------------
# Subcommand: close
# Takes a promoted PU entry out of the queue, recording where its content went.
# The targets are not passed in: they are the '- **Written:**' bullets the edit
# commands left on the entry, so the migrated line reports what was actually
# changed rather than what the caller believed was changed. They are still
# re-verified before anything moves, catching a bullet whose target has since
# been renamed or removed by hand.
#
# --duplicate is the finish for a PU entry that needed no write because the
# profile already carried the substance, and it is refused on an entry that
# records writes, since those two claims cannot both be true.
# ---------------------------------------------------------------------------

# Separator between targets when several are reported together. A semicolon
# rather than a comma because a list address can itself carry one
# ('Programming, Data & Analytics').
TARGET_SEP = '; '

# The target list that finishes a PU entry without writing anything, and the
# outcome a retraction records. Both are whole target lists, never one target
# among several, so they read unambiguously on their migrated line.
DUPLICATE_TARGET = 'duplicate'
DROPPED_OUTCOME = 'dropped'

# Regex: an entry-ID-shaped target, as opposed to a list address.
_ID_RE = re.compile(r'^[A-Z]+-\d+$')

# Regex: an anchored 'ID:' line, used to read narratives.md's own ID roster.
# That document has no structure-authority template, but it does not need one
# to answer the only question asked of it here: does this ID exist.
_ID_LINE_RE = re.compile(r'^ID:\s+([A-Z]+-\d+)\s*$', re.MULTILINE)


def verify_targets(targets, inventory_text, narratives_text, template_text,
                   schemas, retired_text=''):
    """Return one plain-English problem per target that does not resolve.

    A target is either an entry ID or a list address. An ID must exist in
    inventory.md or narratives.md; neither needs a structure-authority template
    for this, because both carry real 'ID:' lines and that is all this check
    reads. An ID in neither is rejected rather than waved through, so a made-up
    ID cannot reach a migrated line that then validates forever.

    retired_text is the retired file (inventory-ret.md). A caller checking past
    records passes it, because an ID written then may have retired since and
    stays valid history; close leaves it out, since what it just wrote must
    exist now.

    positioning.md is deliberately absent. It is not a write target for this
    skill at all (positioning-content-is-hand-driven-2026-08-26), and it carries
    no 'ID:' lines to resolve against even if it were.
    """
    retired = set(entry_block.retired_rows(retired_text))
    known = ({entry['id'] for entry in entry_block.parse_blocks(inventory_text)}
             | set(_ID_LINE_RE.findall(narratives_text)) | retired)
    elements = pr.element_ids(inventory_text) | retired
    sections = list_sections(template_text, schemas)
    problems = []
    for target in targets:
        if pr.ELEMENT_ID_RE.match(target):
            if target not in elements:
                problems.append(f'{target} is not an element in inventory.md')
            continue
        if _ID_RE.match(target):
            if target not in known:
                problems.append(
                    f'{target} exists in neither inventory.md nor '
                    f'narratives.md; positioning.md is not a write target for '
                    f'this skill')
            continue
        try:
            resolve_list_target(inventory_text, target, sections)
        except ValueError as e:
            problems.append(str(e))
    return problems


def cmd_close(args, repo_root, cfg):
    """Verify where a PU entry's content landed, then migrate it off."""
    staging_path = _staging_path(repo_root, cfg)
    staging_text = _util.read(staging_path)
    entries = parse_staging(staging_text)
    match = next((e for e in entries if e['id'] == args.pu), None)
    if match is None:
        raise ValueError(f'staging entry not found: {args.pu}')

    targets = written_targets(match['body'])
    if args.duplicate:
        if targets:
            raise ValueError(
                f'{args.pu} records writes to {TARGET_SEP.join(targets)}, so it '
                f'is not a duplicate; close it without --duplicate')
        outcome = DUPLICATE_TARGET
    else:
        if not targets:
            raise ValueError(
                f'{args.pu} records no writes, so there is nothing to close it '
                f'against. Run insert, set, or list-add with --pu {args.pu}; '
                f'use "record" for an edit made by hand in narratives.md or '
                f'positioning.md; pass --duplicate when the profile already '
                f'carried the substance; or use "drop" to retract it.')
        problems = _verify(repo_root, cfg, targets)
        if problems:
            raise ValueError('unresolvable target(s): ' + '; '.join(problems))
        outcome = TARGET_SEP.join(targets)
    _util.write(staging_path,
                _migrate_entry(staging_text, match, len(entries), outcome))
    print(f'{args.pu} migrated; recorded as "{args.pu}: {outcome}"')


# ---------------------------------------------------------------------------
# Subcommand: record
# The one write path this script does not own is an enrichment of narratives.md
# or positioning.md, which have no structure-authority template to validate
# against and so are edited by hand. 'record' is how such an edit still leaves a
# Written bullet, keeping 'close' on a single rule - the migrated line comes
# from recorded writes, always - instead of needing an exception that would
# quietly re-open the hole this whole mechanism exists to close.
# ---------------------------------------------------------------------------

def cmd_record(args, repo_root, cfg):
    """Record a write this script did not make itself."""
    target = args.target.strip()
    if not target:
        raise ValueError('--target is empty; record names where the edit went')
    # Verified here rather than only at close, so a bad target is caught while
    # the edit is fresh instead of at the end of the entry's walk.
    problems = _verify(repo_root, cfg, [target])
    if problems:
        raise ValueError('; '.join(problems))
    _record_write(repo_root, cfg, args.pu, target)
    print(f'{args.pu} now records a write to {target}')


def _verify(repo_root, cfg, targets):
    """Return verify_targets' problems, loading the documents it reads."""
    template_text = _util.read(_template_path(repo_root, cfg))
    return verify_targets(
        targets,
        _util.read(_inventory_path(repo_root, cfg)),
        _util.read(_narratives_path(repo_root, cfg)),
        template_text, document.parse_template(template_text))


# ---------------------------------------------------------------------------
# Subcommand: drop
# The retraction path, and the only way a PU entry leaves the queue without its
# content reaching the profile. Both drop and close take the PU entry's
# body out and record its number under '## Migrated'; what separates them is the
# precondition and the outcome recorded. Close proves the content arrived
# somewhere first and records where; drop is the user deciding it should not,
# and records 'dropped'.
# ---------------------------------------------------------------------------

# The marker a staging file carries in place of content when a section holds
# none. staging_append.py replaces it on the first append, so a removal puts it
# back when it takes the last PU entry: without it the next one would append
# into a file whose shape that replace no longer matches.
_EMPTY_MARKER = '_(none)_'


def cmd_drop(args, repo_root, cfg):
    """Retract a PU entry that will not be promoted, echoing what it held."""
    staging_path = _staging_path(repo_root, cfg)
    staging_text = _util.read(staging_path)
    entries = parse_staging(staging_text)
    match = next((e for e in entries if e['id'] == args.pu), None)
    if match is None:
        raise ValueError(f'staging entry not found: {args.pu}')

    _util.write(staging_path,
                _migrate_entry(staging_text, match, len(entries),
                               DROPPED_OUTCOME))

    # Echo the withdrawn block. The retraction is deliberate, but the content
    # took a conversation to produce and the migrated line records only that it
    # was dropped, so the body is printed rather than vanishing silently.
    print(f'{args.pu} dropped; it held:\n')
    sys.stdout.write(match['body'] + '\n')


# ---------------------------------------------------------------------------
# Migration
# One operation, shared by close and drop: lift the PU entry's body out of the
# queue and write its number under '## Migrated' against what became of it.
# Doing both in one function is what keeps them inseparable - a PU entry can
# never leave the queue without leaving its number behind, which is the whole
# reason the section exists.
# ---------------------------------------------------------------------------

def _migrate_entry(staging_text, match, total, outcome):
    """Return the staging text with one PU entry removed and recorded.

    Removal runs first and recording second, so the recorded line's position is
    computed against the text it actually lands in rather than against indices
    taken before the splice. Both happen inside one returned string, so a caller
    that writes the result cannot persist half of it: if recording raises,
    nothing is written and the PU entry is still in the queue.
    """
    lines = staging_text.split('\n')
    remaining = '\n'.join(lines[:match['start']] + lines[match['end']:])
    if total == 1:
        remaining = _restore_placeholder(remaining)
    return _record_migrated(remaining, match['id'], outcome).rstrip() + '\n'


def _record_migrated(staging_text, pu_id, outcome):
    """Return the staging text with one 'PU-NNN: outcome' line recorded.

    Written in PU order rather than in the order entries happen to be worked,
    so the section stays scannable however a run picks its way through the
    backlog. Recording runs before the removal and both share one write, so a
    PU entry cannot lose its body without gaining its line.
    """
    bounds = document.section_bounds(staging_text,MIGRATED_HEADING)
    if bounds is None:
        raise ValueError(
            "staging file has no '## Migrated' section to record the PU entry "
            'in; add it from templates/profile_updates_pending.md')
    if pu_id in parse_migrated(staging_text):
        raise ValueError(
            f'{pu_id} is already recorded under "## Migrated"; a PU entry '
            f'migrates once')

    start, end = bounds
    lines = staging_text.split('\n')
    new_line = f'{pu_id}: {outcome}'
    number = int(pu_id.split('-')[1])
    content = [i for i in range(start + 1, end)
               if lines[i].strip() and lines[i].strip() != _EMPTY_MARKER]
    if not content:
        # Section holds only its placeholder; the new line replaces it.
        return '\n'.join(lines[:start + 1] + ['', new_line] + lines[end:])
    for i in content:
        m = _MIGRATED_LINE_RE.match(lines[i])
        if m and int(m.group(1).split('-')[1]) > number:
            return '\n'.join(lines[:i] + [new_line] + lines[i:])
    at = content[-1] + 1
    return '\n'.join(lines[:at] + [new_line] + lines[at:])


def _restore_placeholder(staging_text):
    """Return the staging text with the queue's empty marker put back.

    Scoped to '## Entries' by splicing at that section's own bounds: a
    whole-file marker search would not know which of the two sections an empty
    marker belonged to.
    """
    bounds = document.section_bounds(staging_text,ENTRIES_HEADING)
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
                               help='list the PU entries in the queue')
    p_pending.set_defaults(func=cmd_pending)

    p_show = sub.add_parser('show', help='print one staging entry in full')
    p_show.add_argument('--pu', required=True, help='PU-NNN')
    p_show.set_defaults(func=cmd_show)

    # --pu on every write command: the PU entry being worked is what the write
    # gets recorded against, and close builds its migrated line from those
    # records rather than from a target list typed afterwards.
    p_insert = sub.add_parser('insert', help='place a new entry into inventory.md')
    p_insert.add_argument('--prefix', required=True)
    p_insert.add_argument('--pu', required=True,
                          help='PU-NNN this write is being made for')
    p_insert.add_argument('--block-file', required=True,
                          help='entry block WITHOUT its ID: line')
    p_insert.add_argument('--subsection',
                          help='sub-section heading when the section has one '
                               '(e.g. Completed / In Progress for TR entries)')
    p_insert.set_defaults(func=cmd_insert)

    p_set = sub.add_parser('set', help="replace one field's value on one entry")
    p_set.add_argument('--id', required=True, help='the entry to edit, e.g. EX-060')
    p_set.add_argument('--pu', required=True,
                       help='PU-NNN this write is being made for')
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
    p_elem.add_argument('--pu', required=True,
                        help='PU-NNN this write is being made for')
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
    p_list.add_argument('--pu', required=True,
                        help='PU-NNN this write is being made for')
    p_list.add_argument('--item', required=True,
                        help='the item to append, exactly as it should read')
    p_list.set_defaults(func=cmd_list_add)

    p_record = sub.add_parser(
        'record', help='record an edit made by hand in narratives.md or '
                       'positioning.md')
    p_record.add_argument('--pu', required=True, help='PU-NNN')
    p_record.add_argument('--target', required=True,
                          help='the entry ID the hand edit went into')
    p_record.set_defaults(func=cmd_record)

    p_close = sub.add_parser('close',
                             help='migrate a promoted PU entry off the queue')
    p_close.add_argument('--pu', required=True, help='PU-NNN')
    p_close.add_argument('--duplicate', action='store_true',
                         help='finish a PU entry that needed no write because '
                              'the profile already carried the substance')
    p_close.set_defaults(func=cmd_close)

    p_drop = sub.add_parser('drop',
                            help='retract a PU entry not being promoted')
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
