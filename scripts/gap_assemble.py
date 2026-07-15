#!/usr/bin/env python3
"""
gap_assemble.py - assemble the gap analysis artifact from collected signals

Runs the deterministic portion of the gap-analysis pipeline (Phase 6 of the
gap-analysis skill): renders templates/gap_analysis.md from structured JSON
inputs the dispatching skill assembles from sub-agent output and Phase 4
user-loop results. Writes the artifact to the application folder.

Inputs (JSON files written by the dispatching skill):

  --research-file           research.md for this application; provides
                            requirement text and type keyed by CR-NNN so the
                            requirements JSON need not duplicate that data.
  --requirements-file       per-requirement decisions: requirement_id, status,
                            evidence (flat ID list or {id,...} list), notes,
                            closure_ref, language_shift. Text and type are
                            resolved from --research-file.
  --eligibility-file        Phase 2 flags + user decisions.
  --de-emphasize-file       de-emphasize-identifier output.

Plus header scalars (--fit-score, --unmet-must-haves, --recommendation-label,
--recommendation-rationale, --app-id, --date, --company, --role) and
the application folder path (--folder) where the artifact is written.

The script renders the artifact wholesale (it does not section-edit an
existing file): gap_analysis.md is a current-state document and re-running
gap-analysis overwrites it. The session log and staging file carry durable
cross-run state separately.

Nothing repo-dependent is hardcoded. Paths, filenames, and template names
come from config.yaml via _config.

Author    : Jason Delosh
Created   : 2026-05-27
Project   : career
Usage     : python scripts/gap_assemble.py assemble \\
                --folder ... --app-id ... --date ... \\
                --company ... --role ... \\
                --fit-score ... --unmet-must-haves ... \\
                --recommendation-label ... --recommendation-rationale-file ... \\
                --research-file ... --requirements-file ... \\
                --eligibility-file ... --de-emphasize-file ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Template helpers
# Pull the fenced skeleton out of templates/gap_analysis.md and fill {{tokens}}.
# Same pattern as scripts/assemble.py; kept inline here so this script does not
# import from a sibling assembler.
# ---------------------------------------------------------------------------

def _skeleton(templates_dir, template_name):
    """Return the skeleton block from a template file (first fenced block)."""
    text = _util.read(os.path.join(templates_dir, template_name))
    # Regex: capture everything between the first ``` fence pair. re.DOTALL
    # lets '.' span newlines so the whole block is captured.
    m = re.search(r'```\n(.*?)\n```', text, re.DOTALL)
    if not m:
        raise ValueError(f'no fenced skeleton found in template: {template_name}')
    return m.group(1)


def _fill(skeleton, values):
    """Substitute every {{token}} in a skeleton with its value.

    Raises if any token is missing or any {{...}} remains after substitution -
    a mismatch is a bug and would otherwise produce a half-filled file.
    """
    result = skeleton
    for token, value in values.items():
        placeholder = '{{' + token + '}}'
        if placeholder not in result:
            raise ValueError(f'token not found in skeleton: {placeholder}')
        result = result.replace(placeholder, value)
    leftover = re.findall(r'\{\{.*?\}\}', result)
    if leftover:
        raise ValueError(f'unfilled tokens remain: {leftover}')
    return result


# ---------------------------------------------------------------------------
# Research.md parser
# Reads the ## Critical Requirements table to get {CR-NNN: {text, type}}.
# The requirements JSON the skill passes carries only per-run decisions;
# static fields (text, type) are resolved here so they are not duplicated.
# ---------------------------------------------------------------------------

def _parse_requirements_from_research(research_path):
    """Return {CR-NNN: {text, type}} parsed from the ## Critical Requirements section.

    Row position determines the CR-NNN key: row 1 -> CR-001, row 2 -> CR-002,
    matching the gap-detector's positional ID assignment.

    Handles two formats produced by different role-intake versions:
    - Table format:  | # | Text | Type | Source |  (newer)
    - Bullet format: - Text: ...\n  Type: ...      (older)
    """
    text = _util.read(research_path)
    # Capture the ## Critical Requirements section up to the next ## heading or EOF.
    section_match = re.search(
        r'## Critical Requirements\n(.*?)(?=\n## |\Z)', text, re.DOTALL
    )
    if not section_match:
        raise ValueError('## Critical Requirements section not found in research file')
    section = section_match.group(1)

    # --- Table format ---
    lookup = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) < 3:
            continue
        # Skip header row ('#') and separator rows ('---').
        if cells[0] == '#' or cells[0].startswith('---'):
            continue
        try:
            num = int(cells[0])
        except ValueError:
            continue
        cr_id = f'CR-{num:03d}'
        lookup[cr_id] = {'text': cells[1], 'type': cells[2]}
    if lookup:
        return lookup

    # --- Bullet-list format ---
    # Each entry: "- Text: <text>" followed by "  Type: <type>" (then "  Source: ...").
    # A new "- Text:" line flushes the previous entry.
    current = {}
    num = 0
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith('- Text:'):
            if current.get('text') and current.get('type'):
                num += 1
                lookup[f'CR-{num:03d}'] = {'text': current['text'], 'type': current['type']}
            current = {'text': stripped[len('- Text:'):].strip()}
        elif stripped.startswith('Type:') and 'text' in current:
            current['type'] = stripped[len('Type:'):].strip()
    # Flush the last entry.
    if current.get('text') and current.get('type'):
        num += 1
        lookup[f'CR-{num:03d}'] = {'text': current['text'], 'type': current['type']}

    if not lookup:
        raise ValueError('no requirement rows parsed from ## Critical Requirements section')
    return lookup


# ---------------------------------------------------------------------------
# Block renderers
# Each of the four per-section blocks is rendered from structured JSON into
# the Markdown shape that the template's field-notes section specifies. The
# blocks render '_(none)_' when empty (per the template's optional-section
# convention). Requirements always renders content (never empty - every
# requirement appears).
# ---------------------------------------------------------------------------

def _render_eligibility(flags):
    """Render the Eligibility Flags block.

    `flags` is a list of {flag_type, evidence, decision} dicts. The block
    renders one bullet per flag; '_(none)_' when the list is empty. A decision
    of 'confirmed' marks a constraint that was checked with the user and
    cleared (recorded so downstream skills, e.g. preparation-screen, read it
    instead of re-asking); it renders as a confirmation, not a flag.
    """
    if not flags:
        return '_(none)_'
    lines = []
    for flag in flags:
        flag_type = flag.get('flag_type', '')
        evidence = flag.get('evidence', '')
        decision = flag.get('decision', '')
        if decision == 'confirmed':
            lines.append(f'- **{flag_type}**: {evidence}. Confirmed, no conflict.')
        else:
            lines.append(f'- **{flag_type}**: {evidence}. User chose: {decision}.')
    return '\n'.join(lines)


def _render_requirements(requirements, req_lookup):
    """Render the Requirements block: one sub-section per requirement.

    `requirements` is a list of per-run decision dicts: requirement_id, status,
    evidence (flat ID strings or {id,...} dicts - both normalized to IDs here),
    notes, optional closure_ref and language_shift. Text and type are resolved
    from req_lookup keyed by requirement_id; inline fields are a fallback only.
    """
    if not requirements:
        return '_(no requirements)_'
    parts = []
    for req in requirements:
        rid = req.get('requirement_id', '')
        info = req_lookup.get(rid, {})
        rtext = info.get('text') or req.get('requirement_text', rid)
        rtype = info.get('type') or req.get('requirement_type', '')
        status = req.get('status', '')
        # Normalize evidence: flat ID strings (compact shape) or {id,...} dicts (full shape).
        raw_evidence = req.get('evidence', []) or []
        evidence_ids = []
        for e in raw_evidence:
            if isinstance(e, str):
                evidence_ids.append(e)
            elif isinstance(e, dict) and e.get('id'):
                evidence_ids.append(e['id'])
        evidence_str = ', '.join(evidence_ids) if evidence_ids else 'none'
        notes = (req.get('notes') or '').strip() or '_(none)_'
        closure_ref = req.get('closure_ref')
        if closure_ref and status == 'closed':
            notes_with_ref = notes if notes != '_(none)_' else ''
            sep = ' ' if notes_with_ref else ''
            notes = f'{notes_with_ref}{sep}Closure ref: {closure_ref}'.strip()
        parts.append(
            f'### {rid} - {rtext} ({rtype})\n'
            f'- **Status:** {status}\n'
            f'- **Evidence:** {evidence_str}\n'
            f'- **Notes:** {notes}'
        )
    return '\n\n'.join(parts)


def _render_language_shift(requirements, req_lookup):
    """Render the Language-Shift Cases block by filtering requirements.

    Only requirements with status `language-shift` and a populated
    `language_shift` object render here. '_(none)_' when no cases.
    Text is resolved from req_lookup; inline requirement_text is a fallback.
    """
    cases = []
    for req in requirements:
        ls = req.get('language_shift')
        if not ls or req.get('status') != 'language-shift':
            continue
        rid = req.get('requirement_id', '')
        info = req_lookup.get(rid, {})
        rtext = info.get('text') or req.get('requirement_text', rid)
        # language_shift may be a plain string (translation note) or a dict
        # with role_terminology / candidate_terminology / entries_to_reframe.
        if isinstance(ls, str):
            ls_role = ''
            ls_candidate = ls
            ls_entries = list(req.get('evidence') or [])
        else:
            ls_role = ls.get('role_terminology', '')
            ls_candidate = ls.get('candidate_terminology', '')
            ls_entries = ls.get('entries_to_reframe', []) or []
        cases.append({
            'requirement_id': rid,
            'requirement_text_short': rtext,
            'role_terminology': ls_role,
            'candidate_terminology': ls_candidate,
            'entries_to_reframe': ls_entries,
        })
    if not cases:
        return '_(none)_'
    parts = []
    for c in cases:
        entries_str = ', '.join(c['entries_to_reframe']) if c['entries_to_reframe'] else 'none'
        parts.append(
            f'### {c["requirement_id"]} - {c["requirement_text_short"]}\n'
            f'- **Role terminology:** {c["role_terminology"]}\n'
            f'- **Candidate terminology:** {c["candidate_terminology"]}\n'
            f'- **Entries to reframe for CV:** {entries_str}'
        )
    return '\n\n'.join(parts)


def _render_partial_match(requirements, req_lookup):
    """Render the Partial-Match Cases block by filtering requirements.

    A partial-match requirement has genuine transferable experience but a real
    gap remaining. This block gives the CV architect, per case, the evidence to
    cite and the gap to avoid overclaiming. Text is resolved from req_lookup;
    inline requirement_text is a fallback. '_(none)_' when no cases.
    """
    parts = []
    for req in requirements:
        if req.get('status') != 'partial-match':
            continue
        rid = req.get('requirement_id', '')
        info = req_lookup.get(rid, {})
        rtext = info.get('text') or req.get('requirement_text', rid)
        # Evidence to cite: prefer language_shift.entries_to_reframe when present
        # (partial-match downgraded from a language-shift), else the evidence IDs.
        ls = req.get('language_shift') or {}
        entries = list(ls.get('entries_to_reframe') or [])
        if not entries:
            for e in req.get('evidence', []) or []:
                if isinstance(e, str):
                    entries.append(e)
                elif isinstance(e, dict) and e.get('id'):
                    entries.append(e['id'])
        evidence_str = ', '.join(entries) if entries else 'none'
        gap = (req.get('notes') or '').strip() or '_(none)_'
        parts.append(
            f'### {rid} - {rtext}\n'
            f'- **Transferable evidence to cite:** {evidence_str}\n'
            f'- **Gap remaining:** {gap}'
        )
    if not parts:
        return '_(none)_'
    return '\n\n'.join(parts)


def _render_de_emphasize(items):
    """Render the De-emphasize block.

    `items` is a list of {entry_id, rationale}. One bullet per item;
    '_(none)_' when empty.
    """
    if not items:
        return '_(none)_'
    lines = []
    for it in items:
        entry_id = it.get('entry_id', '')
        rationale = it.get('rationale', '')
        lines.append(f'- **{entry_id}**: {rationale}')
    return '\n'.join(lines)


def _render_cv_notes(notes_text):
    """Render the CV Notes block.

    `notes_text` is free-form general framing guidance captured during the
    gap-closure loop. Returns the text as-is (stripped), or '_(none)_' when
    absent or empty.
    """
    notes = (notes_text or '').strip()
    return notes if notes else '_(none)_'


def _render_recommendation(label, rationale):
    """Render the Recommendation block: '**<label>.** <rationale>'."""
    rationale = (rationale or '').strip()
    return f'**{label}.** {rationale}'


# Statuses whose evidence the CV actually cites. An entry serving as evidence for
# one of these has a job in the CV, so it must never appear in the de-emphasize
# list (de-emphasizing an entry the CV cites is contradictory). interview-deferred
# and unresolved are excluded: the CV cites no evidence for them.
_CV_CITED_STATUSES = {'covered', 'closed', 'language-shift', 'partial-match'}


def _cited_evidence_ids(requirements):
    """Return the set of inventory IDs cited as evidence by any CV-citing requirement.

    Evidence is either a flat list of ID strings (compact shape) or a list of
    {id, ...} dicts (full shape); both are normalized to plain IDs here.
    """
    cited = set()
    for req in requirements:
        if req.get('status') not in _CV_CITED_STATUSES:
            continue
        for e in req.get('evidence', []) or []:
            if isinstance(e, str):
                cited.add(e)
            elif isinstance(e, dict) and e.get('id'):
                cited.add(e['id'])
    return cited


# Cross-script alias: gap_de_emphasize.py imports this so its candidate
# pre-filter excludes exactly the same entries this module's safety net drops.
cited_evidence_ids = _cited_evidence_ids


# ---------------------------------------------------------------------------
# Subcommand: assemble
# Reads structured inputs, renders the artifact wholesale, writes to disk.
# ---------------------------------------------------------------------------

def cmd_assemble(args, repo_root, cfg):
    """Render and write gap_analysis.md, then echo its path."""
    # Load the structured inputs the skill prepared.
    requirements_doc = _util.load_json(args.requirements_file)
    requirements = (
        requirements_doc.get('requirements', requirements_doc)
        if isinstance(requirements_doc, dict)
        else requirements_doc
    )

    eligibility_doc = _util.load_json(args.eligibility_file)
    flags = (
        eligibility_doc.get('flags', eligibility_doc)
        if isinstance(eligibility_doc, dict)
        else eligibility_doc
    )

    de_emphasize_doc = _util.load_json(args.de_emphasize_file)
    de_emphasize_items = (
        de_emphasize_doc.get('de_emphasize', de_emphasize_doc)
        if isinstance(de_emphasize_doc, dict)
        else de_emphasize_doc
    )

    rationale = _util.read(args.recommendation_rationale_file).strip()
    cv_notes_text = _util.read(args.cv_notes_file).strip() if args.cv_notes_file else ''
    req_lookup = _parse_requirements_from_research(args.research_file)

    # Deterministic safety net: an entry cited as CV evidence has a job in the CV,
    # so it can never be de-emphasized. Drop any such collision regardless of what
    # the de-emphasize-identifier returned - the sub-agent is an LLM and cannot be
    # trusted to enforce this set-membership constraint perfectly (see design
    # decision de-emphasize-cited-evidence-filter-2026-06).
    cited_ids = _cited_evidence_ids(requirements)
    dropped = [d.get('entry_id') for d in de_emphasize_items
               if d.get('entry_id') in cited_ids]
    if dropped:
        de_emphasize_items = [d for d in de_emphasize_items
                              if d.get('entry_id') not in cited_ids]
        plural = 'y' if len(dropped) == 1 else 'ies'
        print(f'Dropped {len(dropped)} de-emphasize entr{plural} also cited as '
              f'CV evidence: {", ".join(dropped)}')

    # Render the per-section blocks.
    eligibility_block = _render_eligibility(flags)
    requirements_block = _render_requirements(requirements, req_lookup)
    language_shift_block = _render_language_shift(requirements, req_lookup)
    partial_match_block = _render_partial_match(requirements, req_lookup)
    de_emphasize_block = _render_de_emphasize(de_emphasize_items)
    cv_notes_block = _render_cv_notes(cv_notes_text)
    recommendation_block = _render_recommendation(args.recommendation_label, rationale)

    # Substitute tokens into the template skeleton.
    templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
    skeleton = _skeleton(templates_dir, cfg['filenames']['gap_analysis_template'])
    body = _fill(skeleton, {
        'company': args.company,
        'role': args.role,
        'app_id': args.app_id,
        'date': args.date,
        'fit_score_pct': args.fit_score,
        'unmet_must_haves_count': str(args.unmet_must_haves),
        'recommendation_label': args.recommendation_label,
        'eligibility_flags_block': eligibility_block,
        'requirements_block': requirements_block,
        'language_shift_block': language_shift_block,
        'partial_match_block': partial_match_block,
        'de_emphasize_block': de_emphasize_block,
        'cv_notes_block': cv_notes_block,
        'recommendation_block': recommendation_block,
    })

    # Write to the application folder.
    out_path = os.path.join(args.folder, cfg['filenames']['gap_analysis_file'])
    _util.write(out_path, body)
    print(out_path)


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch the assemble subcommand."""
    parser = argparse.ArgumentParser(
        description='assemble the gap analysis artifact from collected signals'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_asm = sub.add_parser('assemble', help='assemble and write gap_analysis.md')
    p_asm.add_argument('--folder', required=True,
                       help='application folder (where gap_analysis.md is written)')
    p_asm.add_argument('--app-id', required=True)
    p_asm.add_argument('--date', required=True, help='YYYY-MM-DD')
    p_asm.add_argument('--company', required=True)
    p_asm.add_argument('--role', required=True)
    p_asm.add_argument('--fit-score', required=True,
                       help='percentage with one decimal place, e.g. 78.3%%')
    p_asm.add_argument('--unmet-must-haves', required=True, type=int,
                       help='integer count of must-haves with status interview-deferred or unresolved')
    p_asm.add_argument('--recommendation-label', required=True,
                       choices=['Proceed', 'Proceed with caution', 'Do not pursue'])
    p_asm.add_argument('--recommendation-rationale-file', required=True,
                       help='path to a file holding the 1-2 sentence rationale text')
    p_asm.add_argument('--cv-notes-file', required=False, default=None,
                       help='path to a file holding general CV framing notes (optional; renders _(none)_ if absent)')
    p_asm.add_argument('--research-file', required=True,
                       help='path to research.md; provides requirement text and type keyed by CR-NNN')
    p_asm.add_argument('--requirements-file', required=True,
                       help='JSON: per-requirement decisions (status, evidence IDs, notes, language_shift, closure_ref)')
    p_asm.add_argument('--eligibility-file', required=True,
                       help='JSON: Phase 2 flags + decisions')
    p_asm.add_argument('--de-emphasize-file', required=True,
                       help='JSON: de-emphasize-identifier output')
    p_asm.set_defaults(func=cmd_assemble)

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
