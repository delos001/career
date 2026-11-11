#!/usr/bin/env python3
"""
gap_assemble.py - assemble the gap analysis artifact from collected signals

Runs the deterministic portion of the gap-analysis pipeline (Phase 6 of the
gap-analysis skill): renders templates/gap_analysis.md from structured JSON
inputs the dispatching skill assembles from sub-agent output and Phase 4
user-loop results. Writes the artifact to the application folder.

Inputs (JSON files written by the dispatching skill):

  --requirements-file       per-requirement decisions: requirement_id, status,
                            evidence (flat ID list or {id,...} list), notes,
                            language_shift. Text, demand and need are resolved from
                            the application's jd_needs.md (via --folder), so
                            the JSON need not duplicate them.
  --eligibility-file        Phase 2 flags + user decisions.
  --themes-file             Phase 5 judgment: {themes: [{name, kind, requirements,
                            meaning}], depends_on: [condition, ...]}.

Plus header scalars (--recommendation-label, --recommendation-rationale-file,
--app-id, --date, --company, --role) and the application folder path (--folder)
where the artifact is written. The coverage table (one row per ranked need)
and the unmet core count are computed here from the statuses, never passed in.
Requirements are reported in need rank order.

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
                --recommendation-label ... --recommendation-rationale-file ... \\
                --requirements-file ... \\
                --eligibility-file ... --themes-file ...
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import requirement_kinds


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
# Requirements lookup
# The requirements JSON the skill passes carries only per-run decisions;
# static fields (text, demand, need) are resolved from jd_needs.md so they are
# not duplicated. The row number is the CR-NNN id: row 1 -> CR-001. The lookup
# is in need rank order, which is the order the artifact reports in.
# ---------------------------------------------------------------------------

def _requirements_lookup(app_folder, cfg):
    """Return {CR-NNN: info} in need rank order (requirement_kinds.requirement_info)."""
    requirement_kinds.ranked_rows(app_folder, cfg)  # raises when nothing is on file
    return requirement_kinds.requirement_info(app_folder, cfg)


def _in_need_order(requirements, req_lookup):
    """Return the per-run decisions sorted by need rank, unknown ids last."""
    order = {rid: i for i, rid in enumerate(req_lookup)}
    return sorted(requirements, key=lambda r: order.get(r.get('requirement_id', ''), len(order)))


# ---------------------------------------------------------------------------
# Block renderers
# Each of the four per-section blocks is rendered from structured JSON into
# the Markdown shape that the template's field-notes section specifies. The
# blocks render '_(none)_' when empty (per the template's optional-section
# convention). Requirements always renders content (never empty - every
# requirement appears).
# ---------------------------------------------------------------------------

# The fixed ending of an eligibility line, by decision. 'confirmed' was checked
# with the user and cleared; 'open' could not be checked because the JD does not
# state it, so it still needs asking. 'override' and 'stop' are the user's choice
# on a real flag. gap_qc.py G15 reads these same endings.
ELIGIBILITY_ENDINGS = {
    'confirmed': 'Confirmed, no conflict.',
    'open': 'Not stated in the JD; ask at the screen.',
    'override': 'User chose: override.',
    'stop': 'User chose: stop.',
}


def _render_eligibility(flags):
    """Render the Eligibility Flags block.

    `flags` is a list of {flag_type, evidence, decision} dicts. The block
    renders one bullet per flag; '_(none)_' when the list is empty. Raises on a
    decision outside ELIGIBILITY_ENDINGS, so an open question cannot be worded
    as settled by passing an improvised value.
    """
    if not flags:
        return '_(none)_'
    lines = []
    for flag in flags:
        flag_type = flag.get('flag_type', '')
        evidence = flag.get('evidence', '')
        decision = flag.get('decision', '')
        if decision not in ELIGIBILITY_ENDINGS:
            raise ValueError(f'eligibility decision {decision!r} for {flag_type!r} is not one of '
                             f"{', '.join(sorted(ELIGIBILITY_ENDINGS))}")
        lines.append(f'- **{flag_type}**: {evidence}. {ELIGIBILITY_ENDINGS[decision]}')
    return '\n'.join(lines)


def _render_requirements(requirements, req_lookup):
    """Render the Requirements block: one sub-section per requirement.

    `requirements` is a list of per-run decision dicts: requirement_id, status,
    evidence (flat ID strings or {id,...} dicts - both normalized to IDs here),
    notes, optional language_shift. Text, need and demand are resolved from
    req_lookup keyed by requirement_id; inline text is a fallback only. The
    heading carries the need and demand, e.g. '(N-01, required)', and the
    caller passes the requirements in need rank order.
    """
    if not requirements:
        return '_(no requirements)_'
    parts = []
    for req in requirements:
        rid = req.get('requirement_id', '')
        info = req_lookup.get(rid, {})
        rtext = info.get('text') or req.get('requirement_text', rid)
        rtype = ', '.join(v for v in (info.get('place'), info.get('demand')) if v)
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
    cite and the prose note. The note carries BOTH halves by design - the skill's
    Phase 4e requires a partial-match note to describe the transferable element
    and the gap that remains - so the field is labelled for both rather than for
    the gap alone. Text is resolved from req_lookup; inline requirement_text is a
    fallback. '_(none)_' when no cases.
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
            f'- **Transferable element and gap remaining:** {gap}'
        )
    if not parts:
        return '_(none)_'
    return '\n\n'.join(parts)


def _render_cv_notes(notes_text):
    """Render the CV Notes block.

    `notes_text` is free-form general framing guidance captured during the
    gap-closure loop. Returns the text as-is (stripped), or '_(none)_' when
    absent or empty.
    """
    notes = (notes_text or '').strip()
    return notes if notes else '_(none)_'


# ---------------------------------------------------------------------------
# Work-state coverage (GitHub #53)
# The role's work-state is classified at role-intake and then used only as a
# silent adjacency signal in retrieval. This block states, per classified
# value, which inventory entries match it exactly, or that none do and which
# adjacent values carry the role instead. Deterministic: tag counts only, read
# through retrieval's own inventory parser and adjacency lookup so the counts
# match what retrieval scores.
# ---------------------------------------------------------------------------

_ID_LIST_MAX = 8


def render_work_state_coverage(classified, entry_states, adjacency):
    """Render the Work-State Coverage block.

    classified   the role's work-state values (primary first)
    entry_states {entry id: [work-state values]}
    adjacency    {work-state value: [adjacent values]}
    """
    if not classified:
        return '_(none)_'
    lines = []
    for value in classified:
        exact = sorted(i for i, states in entry_states.items() if value in states)
        if exact:
            shown = ', '.join(exact[:_ID_LIST_MAX])
            more = f', and {len(exact) - _ID_LIST_MAX} more' if len(exact) > _ID_LIST_MAX else ''
            lines.append(f'- **{value}**: {len(exact)} entr{"y matches" if len(exact) == 1 else "ies match"} '
                         f'exactly ({shown}{more}).')
            continue
        carriers = []
        for neighbour in adjacency.get(value, []):
            n = sum(1 for states in entry_states.values() if neighbour in states)
            if n:
                carriers.append(f'{neighbour} ({n})')
        carried = (f' The closest experience is tagged {", ".join(carriers)} (adjacent work-states).'
                   if carriers else ' No adjacent work-state carries it either.')
        lines.append(f'- **{value}**: no entry matches exactly.{carried} The CV relies on adjacent '
                     'experience for this; expect the interview to probe it directly.')
    return '\n'.join(lines)


def _classified_work_states(session_log_path):
    """Return the role's work-state values from the session log, primary first."""
    text = _util.read(session_log_path)
    m = re.search(r'(?m)^- Work-state:[ \t]*(.+)$', text)
    if not m:
        return []
    values = re.split(r'[ \t]+-[ \t]+', m.group(1).strip(), maxsplit=1)[0]
    return [re.sub(r'\s*\((?:primary|secondary)\)', '', v).strip()
            for v in values.split(',') if v.strip()]


def _work_state_inputs(repo_root, cfg, folder):
    """Return (classified values, {entry id: states}, {value: adjacent values})."""
    import retrieval_apply
    import retrieval_payload
    classified = _classified_work_states(os.path.join(folder, cfg['filenames']['session_log_file']))
    inv_path = os.path.join(repo_root, cfg['paths']['profile'], cfg['filenames']['inventory_file'])
    entries = retrieval_payload._parse_inventory_entries(_util.read(inv_path))
    entry_states = {e['id']: e['work_state'] for e in entries if e['work_state']}
    adjacency = {v: retrieval_apply._adjacency_for(repo_root, 'work-states', v) for v in classified}
    return classified, entry_states, adjacency


# ---------------------------------------------------------------------------
# Coverage picture and gap themes (GitHub #59)
# The artifact leads with how the role maps to the candidate's experience, in
# place of the single fit score it used to lead with. The table is arithmetic on
# the statuses. The themes are per-run judgment, which this script only renders;
# gap_qc.py checks that every soft requirement landed in exactly one theme.
# ---------------------------------------------------------------------------

_COVERAGE_COLUMNS = [('covered', 'Covered'), ('closed', 'Closed'),
                     ('language-shift', 'Language-shift'), ('partial-match', 'Partial'),
                     ('interview-deferred', 'Interview-deferred'), ('unresolved', 'Unresolved')]

# Statuses that leave a requirement unmet.
UNMET_STATUSES = {'interview-deferred', 'unresolved'}


def coverage_items(req_lookup, status_by_id):
    """Return [{info..., status}] in need rank order for the requirements judged."""
    return [{**info, 'id': rid, 'status': status_by_id[rid]}
            for rid, info in req_lookup.items() if rid in status_by_id]


def _summary_line(label, statuses):
    shown = sum(statuses.count(s) for s in ('covered', 'closed', 'language-shift'))
    partly = statuses.count('partial-match')
    return (f'- **{label}:** {shown} of {len(statuses)} shown, {partly} partly shown, '
            f'{len(statuses) - shown - partly} open.')


def render_coverage_picture(items):
    """Render the coverage table: one row per need in rank order, counted by status.

    Core needs (role-statement signal) and Qualifications are marked core; their
    required rows are the ones the recommendation counts. The two summary lines
    split those from everything else.
    """
    lines = ['| Need | ' + ' | '.join(label for _, label in _COVERAGE_COLUMNS) + ' |',
             '|---|' + '---|' * len(_COVERAGE_COLUMNS)]
    places = []
    for item in items:
        if item['place'] not in places:
            places.append(item['place'])
    for place in places:
        group = [i for i in items if i['place'] == place]
        statuses = [i['status'] for i in group]
        name = ' '.join(v for v in (place if place != 'Qual' else '', group[0]['label']) if v)
        core = ', core' if group[0]['core'] else ''
        counts = [str(statuses.count(status)) for status, _ in _COVERAGE_COLUMNS]
        lines.append(f'| {name} ({len(statuses)}{core}) | ' + ' | '.join(counts) + ' |')
    lines.append('')
    counted = [i['status'] for i in items if i['core'] and i['demand'] == 'required']
    other = [i['status'] for i in items if not (i['core'] and i['demand'] == 'required')]
    lines.append(_summary_line('Core, required', counted))
    lines.append(_summary_line('Everything else', other))
    return '\n'.join(lines)


def count_unmet_core(items):
    """Return how many required core rows carry a status that leaves them unmet.

    Only these move the recommendation label: a core need's work or a hard
    qualification the profile does not show. Other unmet rows are listed under
    their need and do not move it.
    """
    return sum(1 for i in items
               if i['core'] and i['demand'] == 'required' and i['status'] in UNMET_STATUSES)


def render_gap_themes(themes):
    """Render the Gap Themes block, one sub-section per theme."""
    if not themes:
        return '_(none)_'
    parts = []
    for theme in themes:
        parts.append(
            f"### {theme.get('name', '')} ({theme.get('kind', '')})\n"
            f"- **Requirements:** {', '.join(theme.get('requirements') or [])}\n"
            f"- **What it means:** {(theme.get('meaning') or '').strip()}"
        )
    return '\n\n'.join(parts)


def _render_recommendation(label, rationale, depends_on):
    """Render the Recommendation block: the label, its rationale, its conditions."""
    rationale = (rationale or '').strip()
    conditions = '\n'.join(f'- {c.strip()}' for c in depends_on or [])
    return f'**{label}.** {rationale}\n\n**Depends on:**\n{conditions}'


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

    rationale = _util.read(args.recommendation_rationale_file).strip()
    cv_notes_text = _util.read(args.cv_notes_file).strip() if args.cv_notes_file else ''
    req_lookup = _requirements_lookup(args.folder, cfg)
    judgment = _util.load_json(args.themes_file)
    requirements = _in_need_order(requirements, req_lookup)
    items = coverage_items(req_lookup, {req.get('requirement_id', ''): req.get('status', '')
                                        for req in requirements})

    # Render the per-section blocks.
    coverage_block = render_coverage_picture(items)
    themes_block = render_gap_themes(judgment.get('themes'))
    eligibility_block = _render_eligibility(flags)
    requirements_block = _render_requirements(requirements, req_lookup)
    language_shift_block = _render_language_shift(requirements, req_lookup)
    partial_match_block = _render_partial_match(requirements, req_lookup)
    cv_notes_block = _render_cv_notes(cv_notes_text)
    work_state_block = render_work_state_coverage(*_work_state_inputs(repo_root, cfg, args.folder))
    recommendation_block = _render_recommendation(args.recommendation_label, rationale,
                                                  judgment.get('depends_on'))

    # Substitute tokens into the template skeleton.
    templates_dir = os.path.join(repo_root, cfg['paths']['templates'])
    skeleton = _skeleton(templates_dir, cfg['filenames']['gap_analysis_template'])
    body = _fill(skeleton, {
        'company': args.company,
        'role': args.role,
        'app_id': args.app_id,
        'date': args.date,
        'unmet_core_count': str(count_unmet_core(items)),
        'recommendation_label': args.recommendation_label,
        'coverage_picture_block': coverage_block,
        'gap_themes_block': themes_block,
        'eligibility_flags_block': eligibility_block,
        'requirements_block': requirements_block,
        'language_shift_block': language_shift_block,
        'partial_match_block': partial_match_block,
        'work_state_coverage_block': work_state_block,
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
    p_asm.add_argument('--recommendation-label', required=True,
                       choices=['Proceed', 'Proceed with caution', 'Do not pursue'])
    p_asm.add_argument('--recommendation-rationale-file', required=True,
                       help='path to a file holding the 1-2 sentence rationale text')
    p_asm.add_argument('--cv-notes-file', required=False, default=None,
                       help='path to a file holding general CV framing notes (optional; renders _(none)_ if absent)')
    p_asm.add_argument('--requirements-file', required=True,
                       help='JSON: per-requirement decisions (status, evidence IDs, notes, language_shift)')
    p_asm.add_argument('--eligibility-file', required=True,
                       help='JSON: Phase 2 flags + decisions')
    p_asm.add_argument('--themes-file', required=True,
                       help='JSON: Phase 5 gap themes and the conditions the recommendation depends on')
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
