#!/usr/bin/env python3
"""
profile_update_qc.py - mechanical quality checks for the profile-update skill

Runs after the profile-update skill has written its changes. Owns every check a
script can settle: document structure, per-entry field rosters, ID integrity,
entry placement, cross-reference resolution, axis-value validity, table-of-
contents accuracy, empty-section markers, staging-item completeness, and the
mechanical wording rules.

Judgment checks are NOT here. Whether an entry's text honestly represents what
the user surfaced, whether a framing limit in the staged item was respected,
and whether each field holds the right content belong to the qc-profile-update
sub-agent, which reads only the changed entries and the writing rules.

Every rule is derived at run time, never hardcoded: the section roster and the
field rosters come from templates/inventory.md, the axis vocabularies come from
the registries under rules/, and paths come from config.yaml. A schema change
is a template edit and this script follows it.

Checks:
  P1  Section roster and order match the template skeleton
  P2  Entry fields match the template roster for their prefix
  P3  IDs are unique and correctly formed
  P4  EX entries sit in a topic group under their role's group; group
      markers are well-formed, non-empty, and unique within a role
  P5  Role and Recognizes references resolve
  P6  Axis values exist in their registry
  P7  Table of contents matches the document headings
  P8  Empty-section markers agree with actual content
  P9  (retired with the PU numbering, #70)
  P10 Every item waiting in the staging queue carries every schema field,
      non-blank, under a unique label
  P11 List sections hold content and repeat no item within a category
  P12 (retired with the migrated record, #70)
  P13 PR elements are well-formed, sit in their own block, and are unique;
      every Outcome sits under an element
  P14 Blocks sharing a Project agree on Role/Company, Orientation, Level and
      Work-state
  P15 Prose fields carry no first person, banned phrase, em dash, or
      mechanical AI-tell, and end with a period

Author    : Jason Delosh
Created   : 2026-08-24
Project   : career
Usage     : python scripts/profile_update_qc.py check
            python scripts/profile_update_qc.py check --scope-id EX-240 --scope-id PR-016.04
            python scripts/profile_update_qc.py context --item "<label>" --scope-id EX-240
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import _wording
import profile_slice
import profile_update as pu
import rules_slice
import staging_append
from inventory_model import document, entry_block, pr


# ---------------------------------------------------------------------------
# Finding collection
# Each check appends plain-English findings. The skill translates them for the
# user, so the text here names what is wrong and where, not a rule ID alone.
# ---------------------------------------------------------------------------

class Findings:
    """Accumulates per-check findings and reports the overall verdict.

    Findings carry the entry they belong to. When the caller declares which
    entries a run touched (--scope-id), a finding on an entry the run did not
    touch is reported as an advisory rather than a failure: a pre-existing
    defect elsewhere in the document is real and worth surfacing, but it must
    not make it impossible for a run to reach PASS on its own work. With no
    scope declared the whole document is in scope and every finding fails.
    """

    def __init__(self, scope_ids=None):
        self.items = []
        self.ran = []
        self.scope = set(scope_ids or [])

    def add(self, check, message, where=None):
        """Record one failure under a check ID, optionally naming its entry."""
        self.items.append((check, message, where))

    def mark(self, check):
        """Record that a check ran, so the report can show full coverage."""
        self.ran.append(check)

    def _in_scope(self, where):
        """Return True when a finding must fail the run.

        A PR block and its elements are in scope together: a run that wrote
        PR-015.03 owns findings on PR-015, and the reverse.
        """
        if not self.scope:
            return True
        return where is None or pr.is_related(where, self.scope)

    def report(self):
        """Print the verdict and every finding; return the process exit code."""
        blocking = [f for f in self.items if self._in_scope(f[2])]
        advisory = [f for f in self.items if not self._in_scope(f[2])]
        failed_checks = {check for check, _, _ in blocking}
        print(f'{len(self.ran) - len(failed_checks)}/{len(self.ran)} checks passed')
        print('FAIL' if blocking else 'PASS')
        for check, message, _ in blocking:
            print(f'  [{check}] {message}')
        if advisory:
            print(f'\n{len(advisory)} pre-existing finding(s) outside this run:')
            for check, message, _ in advisory:
                print(f'  [{check}] {message}')
        return 1 if blocking else 0


# ---------------------------------------------------------------------------
# P1 - Section roster and order
# The template's document skeleton is the authority. Placeholder headings are
# excluded upstream by template_sections, so a per-user category set never
# counts as a missing section.
# ---------------------------------------------------------------------------

def check_sections(findings, inventory_text, template_text):
    """P1: every template section is present, in canonical order."""
    findings.mark('P1')
    expected = [heading for _, heading in document.template_sections(template_text)]
    lines = inventory_text.split('\n')
    fenced = document.fence_mask(lines)
    actual = [m.group(2) for i, line in enumerate(lines) if not fenced[i]
              for m in [re.match(r'^(#{2,3})\s+(.+?)\s*$', line)] if m]
    for heading in expected:
        if heading not in actual:
            findings.add('P1', f'section missing from inventory: "{heading}"')
    # Order check runs over the sections that are actually present, so a
    # missing section is reported once by the loop above rather than twice.
    present = [h for h in expected if h in actual]
    positions = [actual.index(h) for h in present]
    if positions != sorted(positions):
        findings.add('P1', 'sections are out of canonical order; expected '
                           + ' then '.join(f'"{h}"' for h in present))


# ---------------------------------------------------------------------------
# P2 / P3 - Entry field rosters and ID integrity
# Field order matters: consuming parsers read entries positionally, so a
# reordered entry is a real defect rather than a cosmetic one.
# ---------------------------------------------------------------------------

def check_entry_fields(findings, entries, schemas):
    """P2: each entry's fields match the template roster for its prefix."""
    findings.mark('P2')
    for entry in entries:
        schema = schemas.get(entry['prefix'])
        if schema is None:
            findings.add('P2', f"{entry['id']} uses a prefix the template does "
                               f'not define', entry['id'])
            continue
        labels = [label for label, _ in entry['fields']]
        known = {label for label, _ in schema['fields']}
        required = [label for label, optional in schema['fields'] if not optional]
        for label in required:
            if label not in labels:
                findings.add('P2', f"{entry['id']} is missing the required "
                                   f'"{label}:" field', entry['id'])
        unknown = [label for label in labels if label not in known]
        if unknown:
            findings.add('P2', f"{entry['id']} carries field(s) the template "
                               f"does not define: {', '.join(unknown)}",
                         entry['id'])
        ordered = [label for label, _ in schema['fields'] if label in labels]
        if [label for label in labels if label in known] != ordered:
            findings.add('P2', f"{entry['id']} has its fields out of template "
                               f'order', entry['id'])


def check_ids(findings, entries):
    """P3: IDs are unique across the document and zero-padded to three digits."""
    findings.mark('P3')
    seen = {}
    for entry in entries:
        if entry['id'] in seen:
            findings.add('P3', f"duplicate ID {entry['id']}", entry['id'])
        seen[entry['id']] = True
        number = entry['id'].split('-', 1)[1]
        if len(number) != 3:
            findings.add('P3', f"{entry['id']} is not zero-padded to three "
                               f'digits', entry['id'])


# ---------------------------------------------------------------------------
# P4 - EX placement
# An EX entry's Role field assigns it unambiguously to one role group, and
# within it the entry sits in a topic group opened by a '--- <label>' marker
# (ex-topic-groups-2026-10). Group and entry order are the user's, so nothing
# here checks order. What is checked is what the scripts rely on: insert
# addresses a group by its label, so labels must be unique within a role, and
# block parsing ends an entry at a well-formed marker, so a near-miss such as
# '---label' would silently fold into the entry above.
# ---------------------------------------------------------------------------

# Regex: a line that looks like a marker attempt: two or more leading dashes.
# A bare '---' rule and a well-formed marker are the two valid shapes.
_MARKER_LIKE_RE = re.compile(r'^-{2,}')


def check_ex_placement(findings, inventory_text):
    """P4: EX entries sit in a topic group under their role's group."""
    findings.mark('P4')
    bounds = document.section_bounds(inventory_text, 'Experience Entries')
    if bounds is None:
        findings.add('P4', 'no "Experience Entries" section to check')
        return
    start, end = bounds
    lines = inventory_text.split('\n')
    role_group = None
    labels = set()
    topic = None   # [label, entry count] of the topic group being walked

    def close_topic():
        if topic is not None and topic[1] == 0:
            findings.add('P4', f'{role_group} topic group "{topic[0]}" holds no entries')

    for i in range(start, end):
        m = re.match(r'^###\s+(RL-\d+)\s*$', lines[i])
        if m:
            close_topic()
            role_group, labels, topic = m.group(1), set(), None
            continue
        m = document.GROUP_MARKER_RE.match(lines[i])
        if m:
            close_topic()
            label = m.group(1)
            if label in labels:
                findings.add('P4', f'{role_group} repeats the topic group "{label}"')
            labels.add(label)
            topic = [label, 0]
            continue
        if _MARKER_LIKE_RE.match(lines[i]) and lines[i].rstrip() != '---':
            findings.add('P4', f'malformed topic-group marker at line {i + 1}: '
                               f'"{lines[i]}" (expected "--- <label>")')
            continue
        if not re.match(r'^ID:\s+EX-\d+\s*$', lines[i]):
            continue
        entry = entry_block.parse_blocks('\n'.join(lines[i:end]))[0]
        role = entry['field_map'].get('Role', '').strip()
        if role_group is None:
            findings.add('P4', f"{entry['id']} sits outside any role group",
                         entry['id'])
            continue
        if role != role_group:
            findings.add('P4', f"{entry['id']} carries Role: {role} but sits in "
                               f'the {role_group} group', entry['id'])
        if topic is None:
            findings.add('P4', f"{entry['id']} sits in {role_group} outside any "
                               f'topic group', entry['id'])
            continue
        topic[1] += 1
    close_topic()


# ---------------------------------------------------------------------------
# P5 / P6 - Cross-references and axis vocabularies
# A dangling Role reference silently strips an entry's employer from the
# retrieval payload; an off-registry axis value silently never matches in the
# tag-pull pass. Both fail quietly downstream, so they are caught here.
# ---------------------------------------------------------------------------

def check_references(findings, entries):
    """P5: Role and Recognizes references resolve to real entries."""
    findings.mark('P5')
    known = {entry['id'] for entry in entries}
    for entry in entries:
        for label in ('Role', 'Recognizes'):
            ref = entry['field_map'].get(label, '').strip()
            if ref and ref not in known:
                findings.add('P5', f"{entry['id']} references {label}: {ref}, "
                                   f'which does not exist', entry['id'])
        if entry['prefix'] == 'PR':
            if pr.role_company_conflict(entry['field_map']):
                findings.add('P5', f"{entry['id']} carries both Role: and "
                                   f'Company:; they are mutually exclusive',
                             entry['id'])


def check_axis_values(findings, entries, repo_root, cfg):
    """P6: every axis value appears in that axis's registry."""
    findings.mark('P6')
    vocab = _axis_vocabularies(repo_root, cfg)
    for entry in entries:
        for label, values in vocab.items():
            raw = entry['field_map'].get(label, '').strip()
            if not raw:
                continue
            for value in [v.strip() for v in raw.split('|') if v.strip()]:
                if value not in values:
                    findings.add('P6', f"{entry['id']} has {label}: {value}, "
                                       f'which is not in the {label.lower()} '
                                       f'registry', entry['id'])


def _axis_vocabularies(repo_root, cfg):
    """Return {field label: set of registry values}, read from rules/."""
    vocab = {}
    for axis, spec in cfg['axes'].items():
        registry = os.path.join(repo_root, cfg['paths']['rules'], axis,
                                cfg['filenames']['axis_registry'])
        if not os.path.exists(registry):
            continue
        values = set(re.findall(r'^-\s+\*\*([A-Za-z0-9-]+)\*\*',
                                _util.read(registry), re.MULTILINE))
        key = spec['frontmatter_key']
        vocab[key[0].upper() + key[1:]] = values
    return vocab


# ---------------------------------------------------------------------------
# P7 / P8 - Table of contents and empty-section markers
# The ToC is generated from the headings, so any divergence means the document
# was hand-edited. 'Entries: None' is a claim about the document, so it has to
# agree with what the document actually holds.
# ---------------------------------------------------------------------------

def check_toc(findings, inventory_text):
    """P7: the table of contents matches the document's headings."""
    findings.mark('P7')
    if document.rebuild_toc(inventory_text) != inventory_text:
        findings.add('P7', 'the table of contents does not match the document '
                           'headings; regenerate it rather than editing it')


def check_empty_markers(findings, inventory_text, schemas, spans):
    """P8: 'Entries: None' appears on empty sections and nowhere else.

    Checked per span, not per section: a section the template splits into
    sub-sections can have one side populated and the other legitimately empty,
    so scanning the whole section both misreports the marked-empty side and
    hides an unmarked-empty one.
    """
    findings.mark('P8')
    for prefix, schema in schemas.items():
        for heading in spans.get(schema['section'], [schema['section']]):
            bounds = document.section_bounds(inventory_text, heading)
            if bounds is None:
                continue
            start, end = bounds
            body = '\n'.join(inventory_text.split('\n')[start:end])
            marked = bool(re.search(r'(?m)^Entries: None\s*$', body))
            populated = bool(re.search(r'(?m)^ID:\s+' + prefix + r'-\d+\s*$',
                                       body))
            # RL is the exception: there 'Entries: None' is a per-record field
            # asserting a background role, so it appears legitimately inside a
            # populated section.
            if populated and marked and prefix != 'RL':
                findings.add('P8', f'"{heading}" carries "Entries: None" but '
                                   f'holds entries')
            if not populated and not marked:
                findings.add('P8', f'"{heading}" is empty but carries no '
                                   f'"Entries: None" marker')


# ---------------------------------------------------------------------------
# P10 - Staging items
# staging_append.py refuses an incomplete capture, so an item missing a field
# was written by hand or by an older schema. Either way the profile-update run
# would have to guess the missing fact, which is the failure the fields exist
# to prevent. Labels are how items are found, so a repeated label makes one of
# them unreachable.
# ---------------------------------------------------------------------------

def check_staging_items(findings, staging_items, schema_labels):
    """P10: every queued item carries every schema field under a unique label."""
    findings.mark('P10')
    seen = set()
    for item in staging_items:
        label = item['label']
        if label in seen:
            findings.add('P10', f'two items in the staging queue share the label '
                                f'"{label}"')
        seen.add(label)
        missing = [field for field in schema_labels
                   if not pu.bullet_value(item['body'], field)]
        if missing:
            findings.add('P10', f'staging item "{label}" is missing '
                                f"{', '.join(missing)}")


# ---------------------------------------------------------------------------
# P11 - List sections
# The two sections holding flat lists rather than entries carry no IDs, so
# nothing above reaches them: P2's field roster, P3's ID integrity and P8's
# empty-section marker all key off an 'ID:' line. That left the tool roster and
# the industry-exposure profile unchecked entirely. Two things are worth
# settling mechanically: a category that has quietly gone empty, and the same
# item listed twice, which is what repeated appends over time actually produce.
# Findings carry their list address, so a pre-existing duplicate elsewhere in
# the document is an advisory rather than a block on this run's work.
# ---------------------------------------------------------------------------

def check_list_sections(findings, inventory_text, template_text, schemas):
    """P11: each list category holds content and repeats no item."""
    findings.mark('P11')
    for section in pu.list_sections(template_text, schemas):
        categories = pu.list_categories(inventory_text, section)
        if not categories:
            findings.add('P11', f'"{section}" holds no categories', section)
        for category, start, end in categories:
            address = f'{section}{pu._ADDRESS_SEP}{category}'
            content = pu._list_content_lines(inventory_text, start, end)
            if not content:
                findings.add('P11', f'"{address}" holds no items', address)
                continue
            seen = {}
            for _, line in content:
                label, value, _bold = pu._list_line_label(line)
                where = f'{address}{pu._ADDRESS_SEP}{label}' if label else address
                for item in pu.split_items(value):
                    if item.lower() in seen:
                        findings.add(
                            'P11', f'"{item}" is listed twice under '
                                   f'"{address}"', where)
                    seen[item.lower()] = True


# ---------------------------------------------------------------------------
# P13 / P14 - PR elements and project agreement
# An element ID is cited by CVs on its own, so it must be well-formed, belong
# to the block it sits in, and be unique across the document; an Outcome is
# an element's observed result and means nothing detached from one. A project
# split into several objective blocks is still one piece of work, so its
# blocks agree on employer and framing.
# ---------------------------------------------------------------------------

def check_elements(findings, inventory_text, entries):
    """P13: every PR element is well-formed, in its own block, and unique."""
    findings.mark('P13')
    lines = inventory_text.split('\n')
    seen = set()
    for entry in entries:
        if entry['prefix'] != 'PR':
            continue
        body = lines[entry['start']:entry['end']]
        for problem in pr.element_problems(entry['id'], body):
            findings.add('P13', problem, entry['id'])
        for element in pr.parse_elements(body):
            if element['id'] in seen:
                findings.add('P13', f"duplicate element ID {element['id']}",
                             element['id'])
            seen.add(element['id'])


def check_project_agreement(findings, entries):
    """P14: blocks sharing a Project agree on Role/Company and framing axes."""
    findings.mark('P14')
    for where, problem in pr.project_conflicts(
            [e for e in entries if e['prefix'] == 'PR']):
        findings.add('P14', problem, where)


# ---------------------------------------------------------------------------
# P15 - Mechanical wording
# The writing rules a script can settle without judgment, so the review model
# spends its attention on what it alone can judge (rules/profile/
# inventory-writing.md names this check as the owner of these rules). Applied
# to the prose fields only: a role title like 'Analyst I' is not first person.
# Element lines are phrases, not sentences, so they skip the period rule.
# ---------------------------------------------------------------------------

# The single-line fields that hold written prose, all written as sentences.
# PR element text and Outcome lines are read through pr.parse_elements.
SENTENCE_FIELDS = ('Description', 'Impact', 'Context', 'Objective')

# Regex: first person. 'us' is lowercase only so 'US' (the country) passes.
# A capital I joined to a slash or hyphen ('PI/sub-I') is an abbreviation.
_FIRST_PERSON_RE = re.compile(r'(?<![-/])\b(?:I|[Mm]y|[Mm]e|[Ww]e|[Oo]ur|us)\b(?![-/])')

# Regex: a roman-numeral I after a word that takes one ('Phase I', 'Class I').
# Matches inside these spans are not first person. Extend as real collisions
# surface; do not add speculative entries.
_ROMAN_I_RE = re.compile(r'\b(?:Phase|Class|Tier|Type|Grade|Level|Schedule)\s+I\b')

# Phrases the inventory review struck: an emphasis word that adds nothing,
# an alignment claim posing as an outcome, and a work-state restated in prose.
BANNED_PHRASES = re.compile(r'\b(?:personally|positioned for|from greenfield)\b',
                            re.IGNORECASE)


def _prose_units(entry, inventory_lines):
    """Yield (where, value, is_sentence) for every prose unit of one entry."""
    for field in SENTENCE_FIELDS:
        value = entry['field_map'].get(field, '').strip()
        if value:
            yield f"{entry['id']} {field}", value, True
    if entry['prefix'] == 'PR':
        body = inventory_lines[entry['start']:entry['end']]
        for element in pr.parse_elements(body):
            yield element['id'], element['text'], False
            if element['outcome']:
                yield f"{element['id']} Outcome", element['outcome'], True


def wording_problems(value, is_sentence):
    """Return the mechanical wording problems in one prose value."""
    problems = []
    roman = [m.span() for m in _ROMAN_I_RE.finditer(value)]
    person = sorted({m.group(0) for m in _FIRST_PERSON_RE.finditer(value)
                     if not any(s <= m.start() < e for s, e in roman)})
    if person:
        problems.append(f"first person ({', '.join(person)})")
    banned = sorted({m.group(0).lower() for m in BANNED_PHRASES.finditer(value)})
    if banned:
        problems.append(f"banned phrase ({', '.join(banned)})")
    if _wording.EM_DASH in value:
        problems.append('em dash')
    problems += _wording.ai_tell_hits(value)
    if is_sentence and not value.rstrip('*').endswith('.'):
        problems.append('does not end with a period')
    return problems


def check_wording(findings, entries, inventory_text):
    """P15: prose fields pass the mechanical wording rules."""
    findings.mark('P15')
    lines = inventory_text.split('\n')
    for entry in entries:
        for where, value, is_sentence in _prose_units(entry, lines):
            for problem in wording_problems(value, is_sentence):
                findings.add('P15', f'{where}: {problem}', entry['id'])


# ---------------------------------------------------------------------------
# Subcommand: check
# Loads the documents once, runs every check, prints the verdict, and exits
# non-zero on any finding so the calling skill halts per global-rules.md.
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Run every mechanical check and report the verdict."""
    inventory_text = _util.read(pu._inventory_path(repo_root, cfg))
    template_text = _util.read(pu._template_path(repo_root, cfg))
    schemas = document.parse_template(template_text)
    entries = entry_block.parse_blocks(inventory_text)

    findings = Findings(args.scope_id)
    check_sections(findings, inventory_text, template_text)
    check_entry_fields(findings, entries, schemas)
    check_ids(findings, entries)
    check_ex_placement(findings, inventory_text)
    check_references(findings, entries)
    check_axis_values(findings, entries, repo_root, cfg)
    check_toc(findings, inventory_text)
    check_empty_markers(findings, inventory_text, schemas,
                        document.template_spans(template_text))
    check_list_sections(findings, inventory_text, template_text, schemas)
    check_elements(findings, inventory_text, entries)
    check_project_agreement(findings, entries)
    check_wording(findings, entries, inventory_text)

    staging_path = pu._staging_path(repo_root, cfg)
    if os.path.exists(staging_path):
        _, schema = staging_append.load_schema(repo_root, cfg)
        check_staging_items(findings,
                            pu.parse_staging(_util.read(staging_path)),
                            staging_append.schema_labels(schema))

    sys.exit(findings.report())


# ---------------------------------------------------------------------------
# Subcommand: context
# The judgment reviewer needs three things and nothing else: the staged items,
# the entries they became, and the writing rules for those entry types. This
# writes them verbatim into one file and prints the dispatch prompt, so the
# skill sends the prompt unchanged instead of composing one by hand (the
# pattern the retrieval scorers and the gap-detector already follow).
# ---------------------------------------------------------------------------

# The rules key a list-section write is reviewed against.
LIST_RULES_KEY = 'LIST'


def build_context(repo_root, cfg, labels, scope_ids):
    """Return the review context text for one run's items and writes."""
    staging_text = _util.read(pu._staging_path(repo_root, cfg))
    inventory_text = _util.read(pu._inventory_path(repo_root, cfg))
    template_text = _util.read(pu._template_path(repo_root, cfg))
    sections = pu.list_sections(template_text, document.parse_template(template_text))

    out = ['# Profile-update review context', '', '## Staged items', '']
    out += [pu.find_item(staging_text, label)['body'] + '\n' for label in labels]

    out += ['## Written entries', '']
    keys = []
    for target in scope_ids:
        if pu._ADDRESS_SEP in target:
            found = pu.resolve_list_target(inventory_text, target, sections)
            out.append(f"{found['address']}: {found['value']}\n")
            key = LIST_RULES_KEY
        else:
            out.append(profile_slice._fetch_id(target, repo_root, cfg) + '\n')
            key = target.split('-', 1)[0]
        if key not in keys:
            keys.append(key)

    out += ['## Writing rules', '']
    out.append(rules_slice.slice_types(
        rules_slice.load(repo_root, cfg, 'inventory-writing'), keys))
    return '\n'.join(out)


def cmd_context(args, repo_root, cfg):
    """Write the review context file and print the dispatch prompt."""
    if not args.item or not args.scope_id:
        raise ValueError('context needs at least one --item and one --scope-id')
    path = args.out or os.path.join(repo_root, cfg['paths']['temp'],
                                    'qc_profile_update_context.md')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _util.write(path, build_context(repo_root, cfg, args.item, args.scope_id))
    print('=== PROMPT ===')
    print(f'Context file: {path}')
    print('Review the written entries in the context file against the staged '
          'items and the writing rules it holds, per your checks. Return your '
          'standard format.')
    print('=== END ===')


def main():
    """Parse argv, load config, run the checks."""
    parser = argparse.ArgumentParser(
        description='mechanical quality checks for the profile-update skill')
    sub = parser.add_subparsers(dest='command', required=True)

    p_check = sub.add_parser('check', help='run every check')
    p_check.add_argument('--scope-id', action='append', default=[],
                         help='an inventory ID this run created or edited, or a '
                              'list address it appended to; repeatable. Findings '
                              'outside the declared scope are reported as '
                              'advisories rather than failures. Omit to audit '
                              'the whole document.')
    p_check.set_defaults(func=cmd_check)

    p_ctx = sub.add_parser('context',
                           help='write the judgment reviewer\'s context file '
                                'and print its dispatch prompt')
    p_ctx.add_argument('--item', action='append', default=[],
                       help='label of a staged item processed this run; repeatable')
    p_ctx.add_argument('--scope-id', action='append', default=[],
                       help='an ID or list address written this run; repeatable')
    p_ctx.add_argument('--out', help='context file path (default: temp/qc_profile_update_context.md)')
    p_ctx.set_defaults(func=cmd_context)

    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except SystemExit:
        raise
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
