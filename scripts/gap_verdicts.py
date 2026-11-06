#!/usr/bin/env python3
"""
gap_verdicts.py - check the gap-detector's claims and derive its verdicts

The detector used to return one label per requirement, with free text a script
could not check, and it misstated the profile with the evidence in hand (GitHub
#72). It now answers per part of a requirement, with proof, and this script decides
the label. Requirements with a claim that fails its check are listed so the skill
can send them back once; --final turns anything still failing into a question for
the user, so an unproven claim never becomes a verdict.

  direct      evidence_id + quote            the quote must be in that entry
  reworded    evidence_id + quote + terms    same check
  absent      searched_terms                 no term may appear anywhere in the profile
  not-stated  not_stated                     becomes a question, never a gap

Verdict, where 'shown' counts direct and reworded parts:
  absent parts >= shown, with at least one absent     gap
  nothing shown and nothing absent                    not-stated
  some shown, some absent or not stated               partial
  all shown, reworded parts outnumber direct          language-shift
  all shown otherwise                                 covered
One weak part must not sink a requirement, because job descriptions list far more
than any one candidate holds. These cut-offs were tried on one APP-023 run only.

Reads gap_detector_output.json, gap_detector_context.md, and the evidence files from
--temp-dir. Writes gap_detector_verdicts.json in the shape the walk uses, with each
requirement's parts kept. Exit 0 when every requirement has a verdict, 1 when
requirements were rejected (the prompt to send back is printed), 2 on a broken file.

Author    : Jason Delosh
Created   : 2026-11-05
Project   : career
Usage     : python scripts/gap_verdicts.py derive --temp-dir <scratch> [--final]
Depends   : pyyaml (via _util)
"""

import argparse
import glob
import json
import os
import re
import sys

import _util


OUTPUT_FILE = 'gap_detector_output.json'
VERDICTS_FILE = 'gap_detector_verdicts.json'
CONTEXT_FILE = 'gap_detector_context.md'
REFERENCE_MARKER = '# Profile reference sections'
REFERENCE_ID = 'reference'

# Fields each answer must carry, and the only fields it may carry. Free text such
# as a 'reasoning' field is refused: it is where unchecked claims used to live.
_ANSWER_FIELDS = {
    'direct': {'evidence_id', 'quote'},
    'reworded': {'evidence_id', 'quote', 'role_term', 'candidate_term'},
    'absent': {'searched_terms'},
    'not-stated': {'not_stated'},
}


# ---------------------------------------------------------------------------
# Corpus
# What the detector was given to judge from: the evidence files plus the context
# file's reference sections. Its requirements and role summaries are excluded, or
# a term would always be 'found' in the requirement that names it.
# ---------------------------------------------------------------------------

def normalize(text):
    """Lowercase, straighten quotes and dashes, drop emphasis, collapse whitespace."""
    for fancy, plain in (('’', "'"), ('‘', "'"), ('“', '"'), ('”', '"'),
                         ('–', '-'), ('—', '-'), ('*', '')):
        text = text.replace(fancy, plain)
    return re.sub(r'\s+', ' ', text).strip().lower()


def load_corpus(temp_dir):
    """Return (reference text, evidence text, requirement count) from the temp dir."""
    context = _util.read(os.path.join(temp_dir, CONTEXT_FILE))
    if REFERENCE_MARKER not in context:
        raise ValueError(f'{CONTEXT_FILE} has no "{REFERENCE_MARKER}" part')
    head, reference = context.split(REFERENCE_MARKER, 1)
    rows = re.findall(r'(?m)^\|\s*\d+\s*\|', head)
    evidence = '\n'.join(_util.read(p) for p in sorted(glob.glob(os.path.join(temp_dir, 'gap_detector_evidence_*.md'))))
    if not evidence.strip():
        raise ValueError('no evidence files found')
    return reference, evidence, len(rows)


def entry_block(corpus, entry_id):
    """Return the text of one entry, from its ID line to the next, or None.

    A project element (PR-015.03) is read inside its project's block.
    """
    base = entry_id.split('.')[0]
    m = re.search(rf'(?m)^ID:\s+{re.escape(base)}\s*$', corpus)
    if not m:
        return None
    following = re.search(r'(?m)^ID:\s+\S', corpus[m.end():])
    return corpus[m.end():m.end() + following.start()] if following else corpus[m.end():]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def part_problems(part, reference, corpus):
    """Return what is wrong with one answered part."""
    answer = part.get('answer')
    name = part.get('part') or '(unnamed part)'
    if answer not in _ANSWER_FIELDS:
        return [f'"{name}": unknown answer {answer!r}']
    allowed = _ANSWER_FIELDS[answer] | {'part', 'answer'}
    problems = [f'"{name}": field {k!r} is not allowed on {answer}' for k in part if k not in allowed]
    problems += [f'"{name}": {answer} needs {k}' for k in sorted(_ANSWER_FIELDS[answer]) if not part.get(k)]
    if problems:
        return problems

    if answer in ('direct', 'reworded'):
        source = reference if part['evidence_id'] == REFERENCE_ID else entry_block(corpus, part['evidence_id'])
        if source is None:
            return [f'"{name}": {part["evidence_id"]} is not in the evidence you were given']
        if normalize(part['quote']) not in normalize(source):
            return [f'"{name}": the quote is not in {part["evidence_id"]}: {part["quote"][:60]}']
    elif answer == 'absent':
        for term in part['searched_terms']:
            if re.search(rf'(?<!\w){re.escape(normalize(term))}(?!\w)', normalize(corpus)):
                return [f'"{name}": claimed absent, but "{term}" is in the profile']
    return []


def _ids(parts):
    """Return the cited entry IDs of a requirement's parts, in order, without repeats."""
    out = []
    for p in parts:
        cited = p.get('evidence_id')
        if cited and cited != REFERENCE_ID and cited not in out:
            out.append(cited)
    return out


def derive_record(requirement_id, parts):
    """Return the walk's record for a requirement whose parts all passed."""
    answers = [p['answer'] for p in parts]
    direct, reworded_count = answers.count('direct'), answers.count('reworded')
    shown, absent = direct + reworded_count, answers.count('absent')
    record = {'requirement_id': requirement_id, 'parts': parts}
    if absent and absent >= shown:
        verdict = 'gap'
    elif not shown:
        verdict = 'not-stated'
    elif absent or 'not-stated' in answers:
        verdict = 'partial'
    elif reworded_count > direct:
        verdict = 'language-shift'
    else:
        verdict = 'covered'
    record['verdict'] = verdict
    if verdict == 'covered':
        record['evidence'] = _ids(parts)[:3]
        return record
    record['evidence'] = [] if verdict == 'gap' else [{'id': i, 'relevance': ''} for i in _ids(parts)]
    # What a partial shows and leaves open, so its note can say both plainly.
    record['shown_parts'] = [p['part'] for p in parts if p['answer'] in ('direct', 'reworded')]
    record['open_parts'] = [p['part'] for p in parts if p['answer'] in ('absent', 'not-stated')]
    record['missing'] = '; '.join(f"{p['part']}: not found" for p in parts if p['answer'] == 'absent') or None
    record['question'] = '; '.join(p['not_stated'] for p in parts if p['answer'] == 'not-stated') or None
    reworded = [p for p in parts if p['answer'] == 'reworded']
    record['language_shift'] = None if verdict != 'language-shift' else {
        'role_terminology': '; '.join(p['role_term'] for p in reworded),
        'candidate_terminology': '; '.join(p['candidate_term'] for p in reworded),
        'entries_to_reframe': _ids(reworded),
    }
    return record


def unproven_record(requirement_id, problems):
    """Return a question for the user about a requirement that kept failing its checks."""
    return {'requirement_id': requirement_id, 'parts': [], 'verdict': 'not-stated', 'evidence': [],
            'missing': None, 'language_shift': None, 'question': 'Could not be verified: ' + '; '.join(problems)}


def derive(assessments, reference, evidence, requirement_count, final=False):
    """Return (records, {requirement id: problems}) for the detector's output."""
    corpus = f'{reference}\n{evidence}'
    expected = [f'CR-{i:03d}' for i in range(1, requirement_count + 1)]
    by_id = {a.get('requirement_id'): a for a in assessments}
    rejected, records = {}, []
    for rid in expected:
        parts = (by_id.get(rid) or {}).get('parts') or []
        problems = [] if parts else ['no parts answered']
        for part in parts:
            problems += part_problems(part, reference, corpus)
        if not problems:
            records.append(derive_record(rid, parts))
        elif final:
            records.append(unproven_record(rid, problems))
        else:
            rejected[rid] = problems
    return records, rejected


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------

def main():
    """Parse argv, derive verdicts, report, and exit per the contract in the header."""
    parser = argparse.ArgumentParser(description="check the gap-detector's claims and derive its verdicts")
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('derive')
    p.add_argument('--temp-dir', required=True, help='the scratch folder holding the detector files')
    p.add_argument('--final', action='store_true',
                   help='turn requirements that still fail into questions for the user')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        reference, evidence, count = load_corpus(args.temp_dir)
        output = _util.load_json(os.path.join(args.temp_dir, OUTPUT_FILE))
        records, rejected = derive(output.get('assessments', []), reference, evidence, count, args.final)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(2)
    if rejected:
        print(f'{len(rejected)} requirement(s) rejected. Send this back to the same detector:')
        print('\n=== PROMPT ===')
        print(f'These requirements failed their checks. Re-answer only these, with the same rules, '
              f'and merge your new records into {os.path.join(args.temp_dir, OUTPUT_FILE)}:')
        for rid, problems in rejected.items():
            print(f'{rid}: ' + '; '.join(problems))
        print('=== END ===')
        sys.exit(1)
    _util.write(os.path.join(args.temp_dir, VERDICTS_FILE), json.dumps({'assessments': records}, indent=1))
    tally = {}
    for record in records:
        tally[record['verdict']] = tally.get(record['verdict'], 0) + 1
    print(f"Verdicts written: {os.path.join(args.temp_dir, VERDICTS_FILE)}")
    print('; '.join(f'{k}: {v}' for k, v in sorted(tally.items())))


if __name__ == '__main__':
    main()
