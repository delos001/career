#!/usr/bin/env python3
"""
document.py - the inventory as a whole document

Section navigation, the table of contents, line splicing, and the schema read
from templates/inventory.md. Section navigation is plain Markdown, so the
staging file's callers use it too.

Nothing about the document's shape is hardcoded. The section roster, the
prefix-to-section mapping, and the per-prefix field rosters are all parsed from
templates/inventory.md at run time, so a schema change is a template edit.

Author    : Jason Delosh
Created   : 2026-10-21 (moved from profile_update.py)
Project   : career
Depends   : none
"""

import re


# ---------------------------------------------------------------------------
# Template parsing - the schema authority
# templates/inventory.md carries two machine-read blocks: the '## Document
# skeleton' fence (section roster and order) and one '### <PREFIX> - <Section>'
# fence per entry type (field roster). Parsing them here means no script holds
# its own copy of the schema, so adding a field or a section is a template
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


def skeleton_headings(template_text):
    """Return [(depth, heading, is_placeholder)] from the document skeleton.

    The unfiltered reading. Callers that want the section roster take
    template_sections; callers that need to know a section's shape - whether it
    carries sub-headings at all, and whether those are per-user placeholders -
    need the placeholders too, which is why this is separate.
    """
    body = extract_section(template_text, 'Document skeleton')
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
            for depth, heading, placeholder in skeleton_headings(template_text)
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
# Topic groups
# Under each '### RL-NNN' role heading, EX entries sit in topic groups, each
# opened by a '--- <label>' line (ex-topic-groups-2026-10; the skeleton in
# templates/inventory.md shows it). The marker is not a heading, so it is
# matched here rather than read from the skeleton: block parsing needs it on
# every read, and no read of the inventory carries the template text.
# ---------------------------------------------------------------------------

# Regex: a topic-group marker line. Group 1 is the label. A bare '---' rule
# has no label and does not match.
GROUP_MARKER_RE = re.compile(r'^--- (\S.*?)\s*$')


# ---------------------------------------------------------------------------
# Section navigation
# Sections are located by heading text with anchored line patterns rather
# than substring search, per the ID-matching convention in
# inventory-section-8-rl-grouping-2026-05.
# ---------------------------------------------------------------------------

def fence_mask(lines):
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


def extract_section(text, heading):
    """Return the body of a '## <heading>' section, or None if absent."""
    bounds = section_bounds(text, heading)
    if bounds is None:
        return None
    start, end = bounds
    return '\n'.join(text.split('\n')[start:end])


def section_bounds(text, heading):
    """Return (start_line, end_line) for a section, heading line included.

    The section ends at the next heading of equal or shallower depth, or at the
    end of the document. Returns None when the heading is absent.
    """
    lines = text.split('\n')
    fenced = fence_mask(lines)
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


def last_content_line(section_text):
    """Return the index of the last non-blank, non-rule line in a section."""
    lines = section_text.split('\n')
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped and stripped != '---':
            return i
    return 0


def insert_lines(text, at_line, block_lines):
    """Return the text with block_lines spliced in at a line index."""
    lines = text.split('\n')
    return '\n'.join(lines[:at_line] + block_lines + lines[at_line:])


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
    bounds = section_bounds(text, 'Table of Contents')
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
