#!/usr/bin/env python3
"""
notes_assemble.py - scaffold the interview notes artifact for the interview-notes skill

Renders interview_notes.md from templates/interview_notes.md (the structure
authority; all three blocks - file shell, round block, interviewer block - are
parsed from the template, nothing structural is hardcoded here). The artifact
is an append-and-amend document: the user hand-writes notes into the scaffold
during interviews, so this script only ever creates the shell or appends a new
round section; it never rewrites existing content.

Subcommands

  init        create interview_notes.md in the application folder from the
              file-shell block. Refuses to overwrite an existing file.

  add-round   append one round section rendered from a JSON payload. Refuses
              to append when a section with the same stage + date heading
              already exists (the skill amends that section directly instead).
              Deletes the payload file on success; leaves it in place on
              failure so the run can be diagnosed and retried.

Payload (JSON, written by the dispatching skill, e.g. to <folder>/scratch/):

  {
    "stage": "Recruiter Screen",
    "date": "2026-06-12",
    "datetime": "2026-06-12 14:00 EST",
    "medium": "video",
    "format": "single",
    "cue_card": ["Opener: warm, name the mutual contact", "Lead with: turnaround record", "Top concerns: team runway; role scope"],
    "interviewers": [{"name": "Jane Doe", "title": "Senior Director"}],
    "questions": ["How is the team structured?"]
  }

  cue_card, interviewers and questions may be empty lists: no cue_card renders
  _(none)_; no interviewers renders one TBD block; no questions renders _(none)_.

Usage
  python notes_assemble.py init --folder <app-folder> --app-id APP-NNN
      --company <name> --role <title>
  python notes_assemble.py add-round --folder <app-folder> --payload <json-path>

Exit code 0 on success, 1 on any error (message on stderr).

Author    : Jason Delosh
Created   : 2026-06-11
Project   : career
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util


# ---------------------------------------------------------------------------
# Template block extraction and token filling
# The template defines three labeled sections (File shell, Round block,
# Interviewer block), each carrying one fenced block. _block pulls the fence
# under a named '## ' heading; _fill substitutes {{tokens}} strictly.
# ---------------------------------------------------------------------------

def _block(template_text, section_heading):
    """Return the fenced block under '## <section_heading>' in the template.

    Regex: anchor on the heading line, skip the prose between heading and
    fence non-greedily, capture the fence body. re.DOTALL lets '.' span
    newlines so the whole block is captured.
    """
    pattern = (r'^## ' + re.escape(section_heading)
               + r'\n.*?```\n(.*?)\n```')
    m = re.search(pattern, template_text, re.DOTALL | re.MULTILINE)
    if not m:
        raise ValueError(f'no fenced block under "## {section_heading}" in template')
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


def _load_template(repo_root, cfg):
    """Return the template text from the configured templates folder."""
    path = os.path.join(repo_root, cfg['paths']['templates'],
                        cfg['filenames']['interview_notes_template'])
    return _util.read(path)


# ---------------------------------------------------------------------------
# Payload rendering helpers
# ---------------------------------------------------------------------------

# Payload keys add-round requires. interviewers/questions must be present
# (empty lists allowed) so an omission is caught rather than silently skipped.
_PAYLOAD_KEYS = ('stage', 'date', 'datetime', 'medium', 'format',
                 'cue_card', 'interviewers', 'questions')


def _render_cue_card(cue_card):
    """Render the live cue-card as plain bullets; _(none)_ when empty.

    The interview-notes skill composes these lines from interview_prep.md
    (opener, lead framing, top concerns); the script only renders them.
    """
    if not cue_card:
        return '_(none)_'
    return '\n'.join(f'- {line}' for line in cue_card)


def _render_questions(questions):
    """Render the planned questions as checkbox bullets; _(none)_ when empty.

    Each question carries an indented answer line so the response can be
    typed directly beneath it during the call.
    """
    if not questions:
        return '_(none)_'
    return '\n'.join(f'- [ ] {q}\n    - Answer: ' for q in questions)


def _render_interviewers(interviewers, interviewer_block):
    """Render one interviewer block per attendee from the template block.

    The {{interviewer}} token gets '<name> (<title>)', or '<name>' when no
    title is known. An empty attendee list renders a single TBD block so the
    note space exists when names arrive late.
    """
    if not interviewers:
        return _fill(interviewer_block, {'interviewer': 'TBD'})
    parts = []
    for person in interviewers:
        name = (person.get('name') or '').strip()
        title = (person.get('title') or '').strip()
        if not name:
            raise ValueError('interviewer entry missing name')
        label = f'{name} ({title})' if title else name
        parts.append(_fill(interviewer_block, {'interviewer': label}))
    return '\n\n'.join(parts)


# ---------------------------------------------------------------------------
# Round identity
# A round heading is a level-2 line ending in a date, optionally prefixed with
# the ordinal ('## 2. ') and optionally suffixed with a bracketed status
# ('... [CANCELLED 2026-07-03]', written later by interview_lifecycle.py). The
# ordinal is derived here, never taken from the payload, so numbers are assigned
# in append order and never shift.
# ---------------------------------------------------------------------------

_ROUND_HEADING_RE = re.compile(r'^## .+ \| \d{4}-\d{2}-\d{2}\b', re.MULTILINE)


def _next_round_number(artifact):
    """Return the ordinal for the next appended round: existing count + 1."""
    return len(_ROUND_HEADING_RE.findall(artifact)) + 1


def _duplicate_exists(artifact, stage, date):
    """True if a round heading already carries this stage + date.

    Ignores the numeric prefix and any trailing status suffix so a re-run, or a
    cancelled-then-reused stage+date, is still caught.
    """
    pattern = re.compile(
        r'^## (?:\d+\.\s+)?' + re.escape(stage) + r' \| ' + re.escape(date)
        + r'\b', re.MULTILINE)
    return pattern.search(artifact) is not None


# ---------------------------------------------------------------------------
# Subcommand: init
# ---------------------------------------------------------------------------

def cmd_init(args, repo_root, cfg):
    """Create the file shell in the application folder; refuse to overwrite."""
    out_path = os.path.join(os.path.abspath(args.folder),
                            cfg['filenames']['interview_notes_file'])
    if os.path.exists(out_path):
        raise ValueError(f'already exists, refusing to overwrite: {out_path} '
                         f'(use add-round to append a section)')
    template = _load_template(repo_root, cfg)
    shell = _fill(_block(template, 'File shell'), {
        'app_id': args.app_id,
        'company': args.company,
        'role': args.role,
        'created': _util.today_iso(),
    })
    _util.write(out_path, shell + '\n')
    print(out_path)


# ---------------------------------------------------------------------------
# Subcommand: add-round
# ---------------------------------------------------------------------------

def cmd_add_round(args, repo_root, cfg):
    """Append one rendered round section; self-clean the payload on success."""
    out_path = os.path.join(os.path.abspath(args.folder),
                            cfg['filenames']['interview_notes_file'])
    if not os.path.isfile(out_path):
        raise ValueError(f'not found: {out_path} (run init first)')

    payload = _util.load_json(args.payload)
    missing = [k for k in _PAYLOAD_KEYS if k not in payload]
    if missing:
        raise ValueError(f'payload missing keys: {missing}')

    artifact = _util.read(out_path)
    if _duplicate_exists(artifact, payload['stage'], payload['date']):
        raise ValueError(
            f"section already exists: \"{payload['stage']} | {payload['date']}\" "
            f'(amend it directly instead of re-running add-round)')

    number = str(_next_round_number(artifact))

    template = _load_template(repo_root, cfg)
    section = _fill(_block(template, 'Round block'), {
        'number': number,
        'stage': payload['stage'],
        'date': payload['date'],
        'datetime': payload['datetime'],
        'medium': payload['medium'],
        'format': payload['format'],
        'cue_card_block': _render_cue_card(payload['cue_card']),
        'questions_block': _render_questions(payload['questions']),
        'interviewer_blocks': _render_interviewers(
            payload['interviewers'], _block(template, 'Interviewer block')),
    })

    # Append with exactly one blank line between the prior content and the
    # new section heading.
    _util.write(out_path, artifact.rstrip('\n') + '\n\n' + section + '\n')

    # Self-cleaning payload: the file is one-shot input; on success it has no
    # further use and a stale copy could confuse a later run. On failure we
    # never reach this line, so the payload survives for diagnosis.
    os.remove(args.payload)
    heading = f"## {number}. {payload['stage']} | {payload['date']}"
    print(f'{out_path}  appended: "{heading}"')


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch the subcommand."""
    parser = argparse.ArgumentParser(
        description='scaffold the interview notes artifact')
    sub = parser.add_subparsers(dest='command', required=True)

    p_init = sub.add_parser('init', help='create interview_notes.md from the template shell')
    p_init.add_argument('--folder', required=True,
                        help='absolute path to the application folder')
    p_init.add_argument('--app-id', required=True, help='e.g. APP-009')
    p_init.add_argument('--company', required=True)
    p_init.add_argument('--role', required=True)
    p_init.set_defaults(func=cmd_init)

    p_add = sub.add_parser('add-round', help='append one round section from a JSON payload')
    p_add.add_argument('--folder', required=True,
                       help='absolute path to the application folder')
    p_add.add_argument('--payload', required=True,
                       help='absolute path to the round-facts JSON payload')
    p_add.set_defaults(func=cmd_add_round)

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
