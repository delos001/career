#!/usr/bin/env python3
"""
role_extract_assemble.py - role-extract artifact writer

Writes jd_needs.md, the file the role-extract skill produces, from its two
agents' output, so none of it is written or composed by hand. Two
subcommands:

  requirements  Join the jd-splitter's parts (scratch/jd_split.md,
            '## Parts' with '| Unit ID | Part ID | Part |') to
            scratch/jd_sentences.md on Unit ID, writing scratch/jd_assemble.md
            as an outline under '## Requirements': one block per unit with its
            Line and Section, then each part with its Part ID (as the splitter
            numbered it; 'whole' replaced by the Unit text). It sets no Demand
            or Bar (2026-11-23). Re-extracting replaces the whole file.
  needs     Rewrite jd_needs.md with the jd-needs-ranker output: the job, each
            need with its requirements (copied from the file's own rows, kinds
            included), then the Qualifications and Not ranked rows. The
            repetition count and the order of the needs are set here, not
            by the ranker.

Both moved here from role_classify_assemble.py when role-extract was split
out of role-classify (2026-11-16). The kinds subcommand, which added the
jd-kind-labeler's kinds to the jd_assemble.md table, was removed 2026-11-23
when that file became an outline.

Author    : Jason Delosh
Created   : 2026-11-16
Project   : career
Usage     : python scripts/role_extract_assemble.py requirements --folder ... --requirements-file ...
            python scripts/role_extract_assemble.py needs        --folder ... --needs-file ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import jd_bar
import jd_demand
import jd_sentences
import jd_extraction_tables
from role_extract_qc import _clause_holding


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _research_path(folder, cfg):
    """Return research.md's path, failing if it is missing."""
    path = os.path.join(folder, cfg['filenames']['research_file'])
    if not os.path.exists(path):
        raise FileNotFoundError(f'{path} not found (run role-intake and role-research first)')
    return path


def _jd_text(folder, cfg):
    """Return jd.md's text; every JD reference is a line number in it."""
    path = os.path.join(folder, cfg['filenames']['jd_file'])
    if not os.path.isfile(path):
        raise FileNotFoundError(f'{path} not found (run role-intake first)')
    return _util.read(path)


def _title(research):
    """Return '<Company> | <Role>' from research.md's H1."""
    m = re.match(r'# Research: (.*)', _util.read(research))
    if not m:
        raise ValueError(f'{research} has no "# Research: <company> | <role>" heading')
    return m.group(1).strip()


# ---------------------------------------------------------------------------
# Subcommand: requirements
# The units come from scratch/jd_sentences.md, the file the splitter read, so
# each row carries the unit exactly as the splitter saw it. Wording against
# jd.md is role_extract_qc.py's 'requirements' check, run right after this write.
# ---------------------------------------------------------------------------

def _definitions(repo_root, cfg):
    """Return the lines of jd_needs.md's '## Definitions' appendix.

    Kind definitions come from the rules file (jd_extraction_tables.kind_definitions);
    Demand and Bar definitions sit beside the code that sets them (jd_demand,
    jd_bar). Nothing is typed here, so the appendix cannot drift from them.
    jd_assemble.md has no Kind, Demand or Bar, so it gets no appendix.
    """
    out = ['## Definitions', '',
           'For a person reviewing this file. Later skills read only the tables above.', '']
    out += [f"**Kind** (what a row asks for; full rules in the KINDS section of "
            f"`{cfg['paths']['rules']}/{cfg['filenames']['jd_rules_file']}`):", '']
    out += [f'- **{name}:** {text}' for name, text in jd_extraction_tables.kind_definitions(repo_root, cfg)]
    out += ['', '**Demand** (how firmly the job description asks):', '']
    out += [f'- **{name}:** {text}' for name, text in jd_demand.DEFINITIONS]
    out += ['', '**Bar** (what evidence meets it):', '']
    out += [f'- **{name}:** {text}' for name, text in jd_bar.DEFINITIONS]
    out += ['']
    return out


def build_rows(parts, units):
    """Return row dicts for the splitter's parts, for jd_assemble.md.

    parts: [(unit id, part id, part)] in the splitter's order, part 'whole'
    for an unsplit unit. units: jd_sentences.read() of scratch/jd_sentences.md.
    A part naming a unit the file does not have, or a unit with no part, stops
    the write: the splitter must account for every unit, or a requirement is
    silently lost. Each row gets its unit, the splitter's Part ID, the unit's
    heading and line, and the part (the Unit text for 'whole'). Part IDs are
    kept as written; role_extract_qc.py X1 reports any that do not run 1..N.
    """
    by_id = {u['id']: u for u in units}
    unknown = [uid for uid, _, _ in parts if uid not in by_id]
    if unknown:
        raise ValueError(f"parts name units jd_sentences.md does not have: {', '.join(dict.fromkeys(unknown))}; "
                         f"rerun jd_sentences.py and the splitter")
    covered = {uid for uid, _, _ in parts}
    missing = [u['id'] for u in units if u['id'] not in covered]
    if missing:
        raise ValueError(f"the splitter wrote no part for: {', '.join(missing)}; rerun the splitter")
    rows = []
    for uid, num, text in parts:
        unit = by_id[uid]
        # A part cut before the unit's next words can keep the comma that
        # joined them ('Strong process-design capability,'); the splitter
        # keeps or drops it from run to run, so it is dropped here.
        full = unit['text'] if text.strip().lower() == 'whole' else text.strip().rstrip(',').rstrip()
        rows.append(jd_extraction_tables._row(num, full, None, None, unit=uid,
                                           line=f"L{unit['line']}", section=unit['heading']))
    return rows


def cmd_requirements(args, cfg):
    """Join the splitter's parts to jd_sentences.md into jd_assemble.md, replacing any earlier file."""
    research = _research_path(args.folder, cfg)
    fn = cfg['filenames']
    sentences = os.path.join(args.folder, fn['scratch_subdir'], fn['jd_sentences_file'])
    if not os.path.isfile(sentences):
        raise FileNotFoundError(f'{sentences} not found (run jd_sentences.py and the splitter first)')
    units = jd_sentences.read(_util.read(sentences))
    if not units:
        raise ValueError(f'{sentences} holds no units; rerun jd_sentences.py')
    parts = jd_extraction_tables.parse_parts_table(_util.read(args.requirements_file))
    rows = build_rows(parts, units)
    path = os.path.join(args.folder, fn['scratch_subdir'], fn['jd_assemble_file'])
    _util.write(path, jd_extraction_tables.render_assemble(_title(research), rows))
    print(path)


# ---------------------------------------------------------------------------
# Subcommand: needs
# Structure and coverage are checked by role_extract_qc.py X3, not here, so a
# malformed ranking still lands where QC can name what is wrong with it. A row
# the ranker placed nowhere stays under '## Requirements' for X3 to report.
# ---------------------------------------------------------------------------


# The ranking is not left to the ranker's arithmetic or ordering. It judges
# only which needs carry role-statement. The script counts the rest from the
# need's rows (the ranker once wrote 4 sections for rows in 3, and once judged
# space on a need whose lead came from one clause split into three rows):
#   repetition N  distinct JD sections the rows come from
#   space N       words in the distinct JD clauses holding the rows, so rows
#                 split from one clause count it once
# and sorts by role-statement, repetition, space, the ranker's order last.

def _space(rows, jd_text, units):
    """Return the word count of the distinct JD clauses holding `rows`.

    A row with a Unit counts its unit's text (from jd_sentences.units), so
    parts split from one unit count it once. A row from a file written before
    2026-11-18 has no Unit and is found by its quote.
    """
    clauses = set()
    for r in rows:
        if r.get('unit') and r['unit'] in units:
            clauses.add(jd_extraction_tables.normalize(units[r['unit']]['text']))
        else:
            clauses.add(_clause_holding(jd_text, jd_extraction_tables.row_quote(r)))
    # Word tokens only, so a bullet's leading '-' or a stray '&' is not a word.
    return sum(len(re.findall(r"[\w']+", c)) for c in clauses - {None})


def _rank(needs, jd_text, units):
    """Return needs re-signalled and sorted, ids renumbered N-01.. in rank order."""
    keyed = []
    for pos, need in enumerate(needs):
        statement = 'role-statement' in {t.strip() for t in need['signals'].split(',')}
        sections = {jd_extraction_tables.jd_heading(r['source']) for r in need['rows']} - {''}
        space = _space(need['rows'], jd_text, units)
        signals = (['role-statement'] if statement else []) \
            + [f'repetition {len(sections)}', f'space {space}']
        keyed.append(((not statement, -len(sections), -space, pos),
                      {**need, 'signals': ', '.join(signals)}))
    ranked = [need for _, need in sorted(keyed, key=lambda k: k[0])]
    return [{**need, 'id': f'N-{n:02d}'} for n, need in enumerate(ranked, start=1)]


def cmd_needs(args, cfg):
    """Rewrite jd_needs.md from the ranker's output and the file's own rows.

    The ranker returns '## Ranked Needs' (the job lines and the needs table).
    Each row's kind is already in jd_needs.md (the kinds step). Rows outside
    the needs go to Qualifications or Not ranked by their kinds
    (jd_extraction_tables.placement), so the ranker never places them. Every
    row's cells are copied from jd_needs.md's existing rows, never from the
    ranker, so the requirements are never reworded by ranking. A row number the file does not have stops the write; a row whose
    kinds put it in a need the ranker left it out of, or with no known kind, is
    kept under '## Requirements' for X3 to report.
    """
    _research_path(args.folder, cfg)
    path = jd_extraction_tables.needs_path(args.folder, cfg)
    if not os.path.isfile(path):
        raise FileNotFoundError(f'{path} not found (extract the requirements first)')
    current = jd_extraction_tables.read_needs(_util.read(path))
    jd = _jd_text(args.folder, cfg)
    by_num = {row['num']: row for row in jd_extraction_tables.all_rows(current)}
    text = _util.read(args.needs_file).strip()
    m = re.search(r'(?m)^## Ranked Needs[ \t]*$', text)
    if not m:
        raise ValueError('needs file has no "## Ranked Needs" heading')
    block = text[m.start():]
    placed = set()

    def rows(nums):
        unknown = [n for n in nums if n not in by_num]
        if unknown:
            raise ValueError(f"row(s) {', '.join(map(str, unknown))} are not in {path}")
        placed.update(nums)
        return [dict(by_num[n]) for n in nums]

    # The job lines, with the role statement's and outcomes' nested items kept in place.
    job = []
    for line in block.split('\n'):
        if re.match(r'^- (Role statement|Outcomes|Leads, does, or both):', line.strip()) and not line.startswith(' '):
            job.append(line.strip())
        elif job and re.match(r'^\s+- \S', line):
            job.append('  - ' + line.strip()[2:])
    needs = []
    for line in block.split('\n'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 5 or not re.fullmatch(r'N-\d+', cells[0]):
            continue
        nums = [int(t) for t in re.split(r'[,\s]+', cells[2]) if t.isdigit()]
        quote = jd_extraction_tables.jd_ref(jd, '', ' | '.join(cells[4:]))
        needs.append({'id': cells[0], 'label': cells[1],
                      'signals': cells[3], 'quote': quote, 'rows': rows(nums)})
    needs = _rank(needs, jd, {u['id']: u for u in jd_sentences.units(jd)})
    # Place every row the needs did not take by its kinds.
    kinds = jd_extraction_tables.load_kinds(args.repo_root, cfg)
    by_place = {jd_extraction_tables.QUALIFICATIONS: [], jd_extraction_tables.NOT_RANKED: []}
    for num in sorted(set(by_num) - placed):
        names = jd_extraction_tables.parse_kind_cell(by_num[num].get('kind') or '')
        place = jd_extraction_tables.placement(names, kinds)
        if names and all(n in kinds for n in names) and place in by_place:
            by_place[place] += rows([num])
    qualifications = by_place[jd_extraction_tables.QUALIFICATIONS]
    not_ranked = by_place[jd_extraction_tables.NOT_RANKED]
    unplaced = [dict(row) for num, row in sorted(by_num.items()) if num not in placed]
    out = jd_extraction_tables.render_needs(current['title'], job, needs, qualifications,
                                         not_ranked, unplaced, _definitions(args.repo_root, cfg))
    _util.write(path, out)
    print(path)


# ---------------------------------------------------------------------------
# Command-line entry point
# A failure goes to stderr with a non-zero exit so the skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='role-extract artifact writer')
    sub = parser.add_subparsers(dest='command', required=True)

    p_req = sub.add_parser('requirements', help="write the jd-splitter's parts to scratch/jd_assemble.md")
    p_req.add_argument('--folder', required=True, help='the application folder')
    p_req.add_argument('--requirements-file', required=True,
                       help="path to the jd-splitter's output (scratch/jd_split.md)")
    p_req.set_defaults(func=cmd_requirements)

    p_needs = sub.add_parser('needs', help="rewrite jd_needs.md with the ranker's output")
    p_needs.add_argument('--folder', required=True, help='the application folder')
    p_needs.add_argument('--needs-file', required=True,
                         help='path to a file holding the jd-needs-ranker output block')
    p_needs.set_defaults(func=cmd_needs)

    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        args.repo_root, cfg = _config.load()
        args.func(args, cfg)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
