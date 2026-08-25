#!/usr/bin/env python3
"""
profile_update_qc.py - mechanical quality checks for the profile-update skill

Runs after the profile-update skill has written its changes. Owns every check a
script can settle: document structure, per-entry field rosters, ID integrity,
entry placement, cross-reference resolution, axis-value validity, table-of-
contents accuracy, empty-section markers, and staging-file bookkeeping.

Judgment checks are NOT here. Whether an entry's text honestly represents what
the user surfaced, whether a framing guard in the staged content was respected,
and whether the writing matches the document's voice belong to the
qc-profile-update sub-agent, which reads only the changed entries.

Every rule is derived at run time, never hardcoded: the section roster and the
field rosters come from templates/inventory.md, the axis vocabularies come from
the registries under rules/, and paths come from config.yaml. A schema change
is a template edit and this script follows it.

Checks:
  P1  Section roster and order match the template skeleton
  P2  Entry fields match the template roster for their prefix
  P3  IDs are unique and correctly formed
  P4  EX entries sit in their role's group, in sort order
  P5  Role and Recognizes references resolve
  P6  Axis values exist in their registry
  P7  Table of contents matches the document headings
  P8  Empty-section markers agree with actual content
  P9  Staging entries closed this run are marked processed with resolvable targets
  P10 Staging entries carry a Requirement anchor and a consistent status

Author    : Jason Delosh
Created   : 2026-08-24
Project   : career
Usage     : python scripts/profile_update_qc.py check
            python scripts/profile_update_qc.py check --processed-pu PU-004 --processed-pu PU-005
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import profile_update as pu


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
        """Return True when a finding must fail the run."""
        if not self.scope:
            return True
        return where is None or where in self.scope

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
    expected = [heading for _, heading in pu.template_sections(template_text)]
    lines = inventory_text.split('\n')
    fenced = pu._fence_mask(lines)
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
# An EX entry's Role field assigns it unambiguously to one group, and within
# that group entries sort by primary Orientation, then primary Specialty, then
# ID. Placement drift makes the document unreadable long before it breaks a
# parser, and it is invisible in a diff of a single added entry.
# ---------------------------------------------------------------------------

def check_ex_placement(findings, inventory_text):
    """P4: EX entries sit under their role's group, in sort order."""
    findings.mark('P4')
    bounds = pu._section_bounds(inventory_text, 'Experience Entries')
    if bounds is None:
        findings.add('P4', 'no "Experience Entries" section to check')
        return
    start, end = bounds
    lines = inventory_text.split('\n')
    group = None
    previous = None
    for i in range(start, end):
        m = re.match(r'^###\s+(RL-\d+)\s*$', lines[i])
        if m:
            group, previous = m.group(1), None
            continue
        if not re.match(r'^ID:\s+EX-\d+\s*$', lines[i]):
            continue
        entry = pu.parse_entries('\n'.join(lines[i:end]))[0]
        role = entry['field_map'].get('Role', '').strip()
        if group is None:
            findings.add('P4', f"{entry['id']} sits outside any role group",
                         entry['id'])
            continue
        if role != group:
            findings.add('P4', f"{entry['id']} carries Role: {role} but sits in "
                               f'the {group} group', entry['id'])
        key = pu._ex_sort_key(entry['field_map'], entry['number'])
        if previous is not None and key < previous:
            findings.add('P4', f"{entry['id']} is out of sort order within "
                               f'{group}', entry['id'])
        previous = key


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
            has_role = bool(entry['field_map'].get('Role', '').strip())
            has_company = bool(entry['field_map'].get('Company', '').strip())
            if has_role and has_company:
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
    if pu.rebuild_toc(inventory_text) != inventory_text:
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
            bounds = pu._section_bounds(inventory_text, heading)
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
# P9 / P10 - Staging bookkeeping
# The staging file is the audit trail from a surfaced fact to the profile IDs
# that now carry it. An entry left half-closed breaks that trail and will be
# reprocessed on a later run.
# ---------------------------------------------------------------------------

def check_processed(findings, staging_entries, entries, processed_pu, prefixes):
    """P9: entries closed this run are marked processed with real targets.

    `prefixes` is the inventory's entry-type set, read from the template. A
    target outside it is a narrative or positioning ID; those documents have no
    structure-authority template yet, so their IDs are skipped rather than
    checked (issue: narratives/positioning template).
    """
    findings.mark('P9')
    by_id = {entry['id']: entry for entry in staging_entries}
    known = {entry['id'] for entry in entries}
    for pu_id in processed_pu:
        entry = by_id.get(pu_id)
        if entry is None:
            findings.add('P9', f'{pu_id} was reported as processed but does not '
                               f'exist in the staging file')
            continue
        if entry['status'] != 'processed':
            findings.add('P9', f'{pu_id} was reported as processed but its '
                               f'Status still reads "{entry["status"]}"')
        line = pu._bullet_value(entry['body'], 'Processed')
        if not line:
            findings.add('P9', f'{pu_id} has no "Processed:" line recording '
                               f'where its content landed')
            continue
        targets = line.split(' into ', 1)[-1]
        if targets.strip() == 'no change':
            continue
        for target in [t.strip() for t in targets.split(',') if t.strip()]:
            if target.split('-')[0] not in prefixes:
                continue
            if target not in known:
                findings.add('P9', f'{pu_id} names target {target}, which does '
                                   f'not exist in the inventory')


def check_staging_integrity(findings, staging_entries):
    """P10: every entry is anchored, and status matches the audit line."""
    findings.mark('P10')
    for entry in staging_entries:
        if not pu._bullet_value(entry['body'], 'Requirement'):
            findings.add('P10', f"{entry['id']} carries no Requirement line "
                                f'naming where the fact surfaced', entry['id'])
        has_processed = bool(pu._bullet_value(entry['body'], 'Processed'))
        if has_processed and entry['status'] != 'processed':
            findings.add('P10', f"{entry['id']} has a Processed line but its "
                                f'Status reads "{entry["status"]}"', entry['id'])
        if entry['status'] == 'processed' and not has_processed:
            findings.add('P10', f"{entry['id']} is marked processed but records "
                                f'no target IDs', entry['id'])


# ---------------------------------------------------------------------------
# Subcommand: check
# Loads the documents once, runs every check, prints the verdict, and exits
# non-zero on any finding so the calling skill halts per global-rules.md.
# ---------------------------------------------------------------------------

def cmd_check(args, repo_root, cfg):
    """Run every mechanical check and report the verdict."""
    inventory_text = _util.read(pu._inventory_path(repo_root, cfg))
    template_text = _util.read(pu._template_path(repo_root, cfg))
    schemas = pu.parse_template(template_text)
    entries = pu.parse_entries(inventory_text)

    findings = Findings(args.scope_id + args.processed_pu)
    check_sections(findings, inventory_text, template_text)
    check_entry_fields(findings, entries, schemas)
    check_ids(findings, entries)
    check_ex_placement(findings, inventory_text)
    check_references(findings, entries)
    check_axis_values(findings, entries, repo_root, cfg)
    check_toc(findings, inventory_text)
    check_empty_markers(findings, inventory_text, schemas,
                        pu.template_spans(template_text))

    staging_path = pu._staging_path(repo_root, cfg)
    if os.path.exists(staging_path):
        staging_entries = pu.parse_staging(_util.read(staging_path))
        check_processed(findings, staging_entries, entries, args.processed_pu,
                        set(schemas))
        check_staging_integrity(findings, staging_entries)

    sys.exit(findings.report())


def main():
    """Parse argv, load config, run the checks."""
    parser = argparse.ArgumentParser(
        description='mechanical quality checks for the profile-update skill')
    sub = parser.add_subparsers(dest='command', required=True)

    p_check = sub.add_parser('check', help='run every check')
    p_check.add_argument('--processed-pu', action='append', default=[],
                         help='PU-NNN closed this run; repeatable')
    p_check.add_argument('--scope-id', action='append', default=[],
                         help='an inventory ID this run created or edited; '
                              'repeatable. Findings on entries outside the '
                              'declared scope are reported as advisories rather '
                              'than failures. Omit to audit the whole document.')
    p_check.set_defaults(func=cmd_check)

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
