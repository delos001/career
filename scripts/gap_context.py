#!/usr/bin/env python3
"""
gap_context.py - build the gap-detector's input file and dispatch prompt

Runs before the gap-detector sub-agent (gap-analysis Phase 3). Copies, byte
for byte, everything the detector must judge with into one context file, then
prints the complete dispatch prompt. The skill sends that prompt exactly as
printed, so no detector input is composed by hand.

The context file carries three parts:

  Critical Requirements      the ## Critical Requirements section of the
                             application's research.md.
  Role context               the ## Role, ## Company, ## Industry sections of
                             research.md (their ### Summary sub-block when one
                             exists, else the whole section body).
  Profile reference sections every inventory.md '## ' section that retrieval
                             does not score: role history, systems and tools,
                             industry exposure, credentials. Retrieval scores
                             only entry sections (EX/PR/PB/PS), so these reach
                             the detector through nothing else; leaving them to
                             the detector's own full-file read let it miss a
                             systems list and misstate the profile (APP-023).

Which sections count as reference is derived from the inventory itself: a
section holding no retrievable-entry ID line (retrieval_payload._ENTRY_RE) is
reference content. A new inventory section is therefore picked up without a
code change. The Table of Contents is skipped.

Every part must be present and non-empty, and the file must fit a single read;
any shortfall raises so the skill halts.

Beside it the script writes the evidence files, gap_detector_evidence_N.md:
every inventory entry and narrative the retrieval manifest lists, copied whole,
split into files that each fit a single read. The detector judges from these
instead of reading inventory.md and narratives.md, which outgrew one read
(2026-10-27), so no entry it was handed can go unread. A manifest ID with no
entry, or a manifest with no candidates, raises.

Author    : Jason Delosh
Created   : 2026-10-14
Project   : career
Usage     : python scripts/gap_context.py build --folder <app_folder> --temp-dir <scratch>
                [--max-bytes 45000] [--evidence-bytes 45000]
Depends   : pyyaml (via _config)
"""

import argparse
import glob
import os
import re
import sys

import _config
import _util
import retrieval_payload
from inventory_model import entry_block


# ---------------------------------------------------------------------------
# Section helpers
# research.md and inventory.md are both '## '-sectioned markdown. Sections are
# copied verbatim; only leading and trailing blank lines are trimmed.
# ---------------------------------------------------------------------------

ROLE_CONTEXT_SECTIONS = ('Role', 'Company', 'Industry')
TOC_HEADING = 'Table of Contents'


def _h2_sections(text):
    """Return [(heading_text, body)] for every '## ' section, in file order."""
    lines = text.split('\n')
    starts = [i for i, line in enumerate(lines) if line.startswith('## ')]
    sections = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        # A depth-1 heading closes the section too.
        for k in range(start + 1, end):
            if lines[k].startswith('# '):
                end = k
                break
        heading = lines[start][3:].strip()
        sections.append((heading, '\n'.join(lines[start + 1:end]).strip('\n')))
    return sections


def _summary_or_body(body):
    """Return a section's '### Summary' sub-block if it has one, else the body.

    The sub-block runs to the next '### ' heading. Older research files carry
    no sub-blocks, so the whole body is the summary there.
    """
    lines = body.split('\n')
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == '### Summary')
    except StopIteration:
        return body
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith('### ')), len(lines))
    summary = '\n'.join(lines[start + 1:end]).strip('\n')
    return summary if summary.strip() else body


def reference_sections(inventory_text):
    """Return [(heading, body)] for inventory sections retrieval does not score."""
    out = []
    for heading, body in _h2_sections(inventory_text):
        if heading == TOC_HEADING:
            continue
        scored = any(retrieval_payload._ENTRY_RE.match(line)
                     for line in body.split('\n'))
        if not scored:
            out.append((heading, body))
    return out


# ---------------------------------------------------------------------------
# Context build
# Parts are joined under '# ' markers so the '## ' headings copied inside them
# stay verbatim without colliding with the file's own structure.
# ---------------------------------------------------------------------------

def build_context(app_folder, repo_root, cfg, max_bytes):
    """Return the detector context text; raise when any part is missing."""
    research_path = os.path.join(app_folder, cfg['filenames']['research_file'])
    inventory_path = os.path.join(repo_root, cfg['paths']['profile'],
                                  cfg['filenames']['inventory_file'])
    for path in (research_path, inventory_path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f'detector context source missing: {path}')
    research = _util.read(research_path)

    requirements = retrieval_payload.extract_section(
        research, retrieval_payload.CR_HEADING)
    if not requirements or not requirements.strip():
        raise ValueError(f'{research_path} has no "{retrieval_payload.CR_HEADING}" content')

    role_parts = []
    for name in ROLE_CONTEXT_SECTIONS:
        body = retrieval_payload.extract_section(research, f'## {name}')
        if not body or not body.strip():
            raise ValueError(f'{research_path} has no "## {name}" content')
        role_parts.append(f'## {name}\n\n{_summary_or_body(body)}')

    refs = reference_sections(_util.read(inventory_path))
    if not refs:
        raise ValueError(f'{inventory_path} has no reference sections '
                         f'(role history, systems, credentials)')
    ref_parts = [f'## {heading}\n\n{body}' for heading, body in refs]

    context = ('# Gap detector context\n\n'
               f'# Critical Requirements\n\n{requirements}\n\n'
               '# Role context\n\n' + '\n\n'.join(role_parts) + '\n\n'
               '# Profile reference sections\n\n' + '\n\n'.join(ref_parts) + '\n')
    size = len(context.encode('utf-8'))
    if size > max_bytes:
        raise ValueError(f'detector context is {size} bytes, over the {max_bytes}-byte '
                         f'read budget; the detector could not read it whole')
    return context, [heading for heading, _ in refs]


# ---------------------------------------------------------------------------
# Evidence build
# The manifest's two candidate tables name every entry the detector may cite.
# A project element (PR-NNN.NN) reaches it inside its project's block, so an
# element ID resolves to the project. Entries keep manifest order and are
# never split across files.
# ---------------------------------------------------------------------------

MANIFEST_TABLES = ('## Inventory candidates', '## Narratives')

# Regex: a manifest table row whose first cell is an entry ID. Group: the ID
# without any element suffix.
_MANIFEST_ROW_RE = re.compile(r'^\|\s*((?:EX|PR|PB|PS|ST|DC)-\d+)(?:\.\d+)?\s*\|')

EVIDENCE_PREFIX = 'gap_detector_evidence_'


def manifest_ids(manifest_text):
    """Return the entry IDs in the manifest's candidate tables, deduplicated."""
    ids = []
    for heading in MANIFEST_TABLES:
        for line in (retrieval_payload.extract_section(manifest_text, heading) or '').split('\n'):
            m = _MANIFEST_ROW_RE.match(line)
            if m and m.group(1) not in ids:
                ids.append(m.group(1))
    return ids


def build_evidence(manifest_text, inventory_text, narratives_text, max_bytes):
    """Return the evidence file texts; raise on a missing entry or no candidates."""
    ids = manifest_ids(manifest_text)
    if not ids:
        raise ValueError('retrieval manifest has no candidate entries to judge from')
    narratives = {n['id']: n['body']
                  for n in retrieval_payload._parse_narratives(narratives_text)}
    blocks, missing = [], []
    for entry_id in ids:
        block = narratives.get(entry_id) or entry_block.find_block(inventory_text, entry_id)
        if block is None:
            missing.append(entry_id)
        else:
            blocks.append((entry_id, block.strip('\n')))
    if missing:
        # Retired since retrieval ran, or never real; either way the manifest
        # no longer describes the profile.
        raise ValueError(f'manifest lists IDs with no profile entry: {", ".join(missing)}. '
                         f'Re-run retrieval so the manifest matches the profile.')

    # Pack whole entries into files under the byte budget.
    files, current = [], []
    for entry_id, block in blocks:
        if len(block.encode('utf-8')) > max_bytes:
            raise ValueError(f'{entry_id} alone is over the {max_bytes}-byte read budget')
        candidate = '\n\n'.join(current + [block]) + '\n'
        if current and len(candidate.encode('utf-8')) > max_bytes:
            files.append('\n\n'.join(current) + '\n')
            current = []
        current.append(block)
    files.append('\n\n'.join(current) + '\n')
    return files, len(blocks)


def detector_prompt(context_path, retrieval_path, evidence_paths):
    """Return the complete prompt for the gap-detector dispatch."""
    return (f'Context file: {context_path}\n'
            f'retrieval.md: {retrieval_path}\n'
            + ''.join(f'Evidence file: {path}\n' for path in evidence_paths)).rstrip('\n')


# ---------------------------------------------------------------------------
# Subcommand: build
# ---------------------------------------------------------------------------

def cmd_build(args, repo_root, cfg):
    """Write the context and evidence files and print the dispatch prompt."""
    context, ref_headings = build_context(args.folder, repo_root, cfg, args.max_bytes)

    profile_dir = os.path.join(repo_root, cfg['paths']['profile'])
    retrieval_path = os.path.join(args.folder, cfg['filenames']['retrieval_manifest'])
    narratives_path = os.path.join(profile_dir, cfg['filenames']['narratives_file'])
    for path in (retrieval_path, narratives_path):
        if not os.path.isfile(path):
            raise FileNotFoundError(f'detector evidence source missing: {path}')
    evidence, entry_count = build_evidence(
        _util.read(retrieval_path),
        _util.read(os.path.join(profile_dir, cfg['filenames']['inventory_file'])),
        _util.read(narratives_path), args.evidence_bytes)

    # Write only after every part has built, and clear evidence files left by
    # an earlier run so a shorter run cannot leave a stale file behind.
    os.makedirs(args.temp_dir, exist_ok=True)
    context_path = os.path.join(args.temp_dir, 'gap_detector_context.md')
    _util.write(context_path, context)
    for stale in glob.glob(os.path.join(args.temp_dir, f'{EVIDENCE_PREFIX}*.md')):
        os.remove(stale)
    evidence_paths = []
    for i, text in enumerate(evidence):
        path = os.path.join(args.temp_dir, f'{EVIDENCE_PREFIX}{i}.md')
        _util.write(path, text)
        evidence_paths.append(path)

    print(f'Detector context: {context_path}')
    print(f'Profile reference sections included: {", ".join(ref_headings)}')
    print(f'Evidence: {entry_count} entries in {len(evidence_paths)} file(s)')
    print('\nDetector prompt. Dispatch exactly as printed:')
    print('\n=== PROMPT ===')
    print(detector_prompt(context_path, retrieval_path, evidence_paths))
    print('=== END ===')


# ---------------------------------------------------------------------------
# Command-line entry point
# Reports failure to stderr with exit 1 so the calling skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch the subcommand."""
    parser = argparse.ArgumentParser(
        description="build the gap-detector's input file and dispatch prompt")
    sub = parser.add_subparsers(dest='command', required=True)

    p_build = sub.add_parser('build', help='write the detector context file and print the prompt')
    p_build.add_argument('--folder', required=True,
                         help='application folder holding research.md and retrieval.md')
    p_build.add_argument('--temp-dir', required=True, help='the application scratch folder')
    p_build.add_argument('--max-bytes', type=int, default=45000,
                         help='maximum bytes for the context file (default 45000)')
    p_build.add_argument('--evidence-bytes', type=int, default=45000,
                         help='maximum bytes per evidence file (default 45000)')
    p_build.set_defaults(func=cmd_build)

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
