#!/usr/bin/env python3
"""
gap_assemble.py - assemble the gap analysis artifact from collected signals

Runs the deterministic portion of the gap-analysis pipeline (Phase 6 of the
gap-analysis skill): renders templates/gap_analysis.md from structured JSON
inputs the dispatching skill assembles from sub-agent output and Phase 4
user-loop results. Writes the artifact to the application folder.

Inputs (JSON files written by the dispatching skill):

  --requirements-file       per-requirement final records (gap-detector output
                            augmented with Phase 4 status / closure ref).
  --eligibility-file        Phase 2 flags + user decisions.
  --de-emphasize-file       de-emphasize-identifier output.

Plus header scalars (--fit-score, --unmet-must-haves, --recommendation-label,
--recommendation-rationale, --slug, --app-id, --date, --company, --role) and
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
                --folder ... --slug ... --app-id ... --date ... \\
                --company ... --role ... \\
                --fit-score ... --unmet-must-haves ... \\
                --recommendation-label ... --recommendation-rationale-file ... \\
                --requirements-file ... --eligibility-file ... \\
                --de-emphasize-file ...
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
    renders one bullet per flag; '_(none)_' when the list is empty.
    """
    if not flags:
        return '_(none)_'
    lines = []
    for flag in flags:
        flag_type = flag.get('flag_type', '')
        evidence = flag.get('evidence', '')
        decision = flag.get('decision', '')
        lines.append(f'- **{flag_type}**: {evidence}. User chose: {decision}.')
    return '\n'.join(lines)


def _render_requirements(requirements):
    """Render the Requirements block: one sub-section per requirement.

    `requirements` is a list of dicts with at least: requirement_id,
    requirement_text, requirement_type, status, evidence (list of {id}),
    notes (str). Optional: closure_ref (PU-NNN) - when present and the
    requirement closed via user input, appended to notes as 'Closure ref:'.
    """
    if not requirements:
        # Defensive: should never happen (a JD always has critical requirements).
        return '_(no requirements)_'
    parts = []
    for req in requirements:
        rid = req.get('requirement_id', '')
        rtext = req.get('requirement_text', '')
        rtype = req.get('requirement_type', '')
        status = req.get('status', '')
        evidence_items = req.get('evidence', []) or []
        evidence_ids = [e.get('id', '') for e in evidence_items if e.get('id')]
        evidence_str = ', '.join(evidence_ids) if evidence_ids else 'none'
        notes = req.get('notes', '').strip() or '—'
        closure_ref = req.get('closure_ref')
        if closure_ref and status == 'closed':
            notes_with_ref = notes if notes != '—' else ''
            sep = ' ' if notes_with_ref else ''
            notes = f'{notes_with_ref}{sep}Closure ref: {closure_ref}'.strip()
        parts.append(
            f'### {rid} — {rtext} ({rtype})\n'
            f'- **Status:** {status}\n'
            f'- **Evidence:** {evidence_str}\n'
            f'- **Notes:** {notes}'
        )
    return '\n\n'.join(parts)


def _render_language_shift(requirements):
    """Render the Language-Shift Cases block by filtering requirements.

    Only requirements with verdict/status `language-shift` and a populated
    `language_shift` object render here. '_(none)_' when no cases.
    """
    cases = []
    for req in requirements:
        ls = req.get('language_shift')
        if not ls or req.get('status') != 'language-shift':
            continue
        cases.append({
            'requirement_id': req.get('requirement_id', ''),
            'requirement_text_short': req.get('requirement_text', '')[:80],
            'role_terminology': ls.get('role_terminology', ''),
            'candidate_terminology': ls.get('candidate_terminology', ''),
            'entries_to_reframe': ls.get('entries_to_reframe', []) or [],
        })
    if not cases:
        return '_(none)_'
    parts = []
    for c in cases:
        entries_str = ', '.join(c['entries_to_reframe']) if c['entries_to_reframe'] else 'none'
        parts.append(
            f'### {c["requirement_id"]} — {c["requirement_text_short"]}\n'
            f'- **Role terminology:** {c["role_terminology"]}\n'
            f'- **Candidate terminology:** {c["candidate_terminology"]}\n'
            f'- **Entries to reframe for CV:** {entries_str}'
        )
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


def _render_recommendation(label, rationale):
    """Render the Recommendation block: '**<label>.** <rationale>'."""
    rationale = (rationale or '').strip()
    return f'**{label}.** {rationale}'


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

    # Render the per-section blocks.
    eligibility_block = _render_eligibility(flags)
    requirements_block = _render_requirements(requirements)
    language_shift_block = _render_language_shift(requirements)
    de_emphasize_block = _render_de_emphasize(de_emphasize_items)
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
        'de_emphasize_block': de_emphasize_block,
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
    p_asm.add_argument('--slug', required=True)
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
    p_asm.add_argument('--requirements-file', required=True,
                       help='JSON: per-requirement final records (gap-detector output + Phase 4 status/closure)')
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
