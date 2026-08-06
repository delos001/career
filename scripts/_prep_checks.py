#!/usr/bin/env python3
"""
_prep_checks.py - shared deterministic checks for the interview_prep.md template

Both prep_qc.py (preparation-screen) and prep_interview_qc.py
(preparation-interview) validate the SAME shared artifact,
templates/interview_prep.md. The template's formatting and architecture rules
are universal: they govern the main body AND the per-interview Appendix block
that both skills write. This module is the single home for those rules so the two
entry points enforce them identically; a rule added here fires at both the
recruiter-screen and the post-screen stage.

Owns
  markdown parsing helpers (headings, sections, frontmatter, comment stripping)
  P6  no bold connector tokens welding list items
  P7  every heading is in the allowed set (template headings + dynamic
      families), at its template depth, under its template section, and unique
  P8  no coaching brackets or citations inside a heading line
  X1  an APPENDIX region exists with at least one per-interview block
  X2  cross-ref integrity: every Q-label referenced is defined in the Question Bank
  X3  each Appendix block carries only schema fields (Purpose / Interviewer / Emphasis)
  X4  no Appendix block heading carries a date or an event-status token

Per-skill checks stay in each script because they differ in scope: frontmatter /
heading-order (P1-P5), the research ledger (R1), the session-log section each
skill owns (S1-S2), and the advisory warnings (W1-W2).

Author    : Jason Delosh
Created   : 2026-07-10
Project   : career
"""

import os
import re


# ---------------------------------------------------------------------------
# Markdown parsing helpers
# ---------------------------------------------------------------------------

# HTML comments in the template carry guidance, not structure. Strip them
# (multiline, non-greedy) before reading headings so commented examples are
# never treated as requirements.
_COMMENT_RE = re.compile(r'<!--.*?-->', re.DOTALL)

# A heading line: 1+ '#' then a space then text. Captured as (hashes, text).
_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*\S)\s*$', re.MULTILINE)

# Frontmatter: the block between the first two '---' lines at file start.
_FRONTMATTER_RE = re.compile(r'\A---\s*\n(.*?)\n---\s*\n', re.DOTALL)

# A top-level frontmatter key (simple 'key: value' lines; nested keys are not
# used by this artifact's schema).
_FM_KEY_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:', re.MULTILINE)


def _read(path):
    """Return the file's text, or None when the file does not exist."""
    if not os.path.isfile(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _headings(text):
    """Return ordered (depth, text) heading tuples, comments stripped."""
    clean = _COMMENT_RE.sub('', text)
    return [(len(m.group(1)), m.group(2)) for m in _HEADING_RE.finditer(clean)]


def _frontmatter_keys(text):
    """Return the set of top-level frontmatter keys, or None if no block."""
    m = _FRONTMATTER_RE.match(text)
    return set(_FM_KEY_RE.findall(m.group(1))) if m else None


def _frontmatter_sources(text):
    """Return the filenames in the frontmatter 'sources: [...]' list."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return []
    sm = re.search(r'^sources\s*:\s*\[(.*?)\]', m.group(1), re.MULTILINE)
    return [s.strip() for s in sm.group(1).split(',') if s.strip()] if sm else []


def _sections(text):
    """Split on '## ' headings; return ordered (heading_text, body) tuples."""
    out = []
    matches = [m for m in _HEADING_RE.finditer(text) if len(m.group(1)) == 2]
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(2), text[start:end]))
    return out


def _is_placeholder(heading_text):
    """True when a heading carries an angle-bracket token, i.e. it is a pattern."""
    return '<' in heading_text and '>' in heading_text


# A template heading tagged '{optional}' is part of the standard vocabulary but
# is not required in every artifact. It stays in the P7 allowed set (so the model
# cannot invent a substitute name) while being excluded from the P2 required set
# (so a section with no material is dropped rather than left as a bare heading).
# The tag is template-only; the artifact carries the bare heading text.
_OPTIONAL_RE = re.compile(r'\s*\{optional\}\s*$')


def _is_optional(heading_text):
    """True when a template heading is tagged '{optional}'."""
    return bool(_OPTIONAL_RE.search(heading_text))


def _strip_optional(heading_text):
    """Return the heading text with any trailing '{optional}' tag removed."""
    return _OPTIONAL_RE.sub('', heading_text)


# ---------------------------------------------------------------------------
# P6: connector tokens
# ---------------------------------------------------------------------------

_CONNECTOR_RE = re.compile(r'\*\*(plus|and|\+|&)\*\*')


def check_connectors(artifact_text, findings):
    """P6: no bold connector tokens welding list items (use bullets instead)."""
    clean = _COMMENT_RE.sub('', artifact_text)
    hits = sorted(set(_CONNECTOR_RE.findall(clean)))
    findings.append(('P6', not hits,
                     'no bold connector tokens'
                     if not hits
                     else 'bold connector tokens welding list items: '
                          + ', '.join(f'**{h}**' for h in hits)))


# ---------------------------------------------------------------------------
# P7 / P8: heading discipline
# ---------------------------------------------------------------------------

def _template_heading_map(template_text):
    """Return the template's fixed heading vocabulary, with placement.

    pairs   set of (depth, text) the template defines, '{optional}' stripped so
            the artifact's bare heading text matches
    parents {(depth, text): <depth-2 section it is written under>} for every
            depth-3+ heading, so a sub-heading is legal only under its own
            section. Matching on name alone would let 'Scale' or 'Financials'
            land under any section, or appear twice.
    """
    pairs, parents = set(), {}
    parent2 = None
    for d, raw in _headings(template_text):
        if _is_placeholder(raw):
            continue
        text = _strip_optional(raw)
        if d == 2:
            parent2 = text
        pairs.add((d, text))
        if d >= 3:
            parents[(d, text)] = parent2
    return pairs, parents


def check_headings(artifact_text, template_text, findings):
    """P7 (heading vocabulary and placement) and P8 (no coaching/citations).

    A heading passes P7 when it is a template heading AT the template's depth
    and UNDER the template's section for it, appearing once, or when it belongs
    to one of three dynamic families: any '##' block inside the APPENDIX region,
    one '###' per Anticipated Question, one '#### Story ...' per Proof-points
    story. Depth-1 headings (title / MAIN BODY / APPENDIX) are always allowed.

    Name-only matching was not enough once the template's sub-heading vocabulary
    grew: short generic labels (Scale, Financials, Posture, Miscellaneous) read
    as plausible under more than one section, so the depth, the parent, and
    uniqueness are all checked here.
    """
    tpl_pairs, tpl_parents = _template_heading_map(template_text)
    tpl_depths = {}
    for d, t in tpl_pairs:
        tpl_depths.setdefault(t, set()).add(d)
    in_appendix = False
    parent2 = parent3 = None
    seen = set()
    bad_wl = []
    bad_content = []
    for depth, text in _headings(artifact_text):
        # P8: a heading is a short label; coaching brackets and citations belong
        # in the body, never the heading line.
        if any(tok in text for tok in ('[', ']', '(CR-', '(TH-', '*(')):
            bad_content.append('#' * depth + ' ' + text)
        # Region / parent tracking, before the heading itself is judged.
        if depth == 1:
            parent2 = parent3 = None
            if text.strip().upper().startswith('APPENDIX'):
                in_appendix = True
        elif depth == 2:
            parent2, parent3 = text, None
        elif depth == 3:
            parent3 = text
        # The three dynamic families are named by their position, not by a
        # fixed label, so they are exempt from the vocabulary check.
        if (depth == 1
                or (in_appendix and depth == 2)
                or (depth == 3 and parent2 is not None
                    and parent2.startswith('Anticipated Questions'))
                or (depth == 4 and parent3 is not None
                    and parent3.startswith('Proof points'))):
            continue
        label = '#' * depth + ' ' + text
        pair = (depth, text)
        if pair not in tpl_pairs:
            if text in tpl_depths:
                bad_wl.append(f"{label} (template depth is "
                              f"{'/'.join('#' * d for d in sorted(tpl_depths[text]))})")
            else:
                bad_wl.append(f'{label} (not in the template vocabulary)')
            continue
        expected = tpl_parents.get(pair)
        if expected is not None and parent2 != expected:
            bad_wl.append(f"{label} (under '{parent2}', belongs under '{expected}')")
        if pair in seen:
            bad_wl.append(f'{label} (duplicate)')
        seen.add(pair)
    findings.append(('P7', not bad_wl,
                     'all headings in the allowed set, at their template depth '
                     'and section'
                     if not bad_wl
                     else 'heading vocabulary or placement (make these bullets?): '
                          + '; '.join(bad_wl)))
    findings.append(('P8', not bad_content,
                     'no coaching/citations in headings'
                     if not bad_content
                     else 'coaching/citations in a heading (move to the body): '
                          + '; '.join(bad_content)))


# ---------------------------------------------------------------------------
# X1 / X2: architecture integrity (Appendix presence, Q-label cross-refs)
# ---------------------------------------------------------------------------

_APPENDIX_RE = re.compile(r'^#\s+APPENDIX\b', re.MULTILINE)
_QLABEL_REF_RE = re.compile(r'\bQ\d+[a-z]?\b')
# A Question Bank entry defines its label as '- **Q1 ...' / '- **Q1a ...'.
_QLABEL_DEF_RE = re.compile(r'^-\s+\*\*(Q\d+[a-z]?)\b', re.MULTILINE)


def check_xrefs(artifact_text, findings):
    """Run X1 (Appendix block present) and X2 (Q-label cross-ref integrity)."""
    m = _APPENDIX_RE.search(artifact_text)
    if not m:
        findings.append(('X1', False, "no '# APPENDIX' region"))
    else:
        after = artifact_text[m.end():]
        blocks = [h for h, _ in _sections(after)]
        findings.append(('X1', bool(blocks),
                         f'{len(blocks)} per-interview block(s)' if blocks
                         else 'APPENDIX region has no per-interview block'))

    bank_body = next((b for h, b in _sections(artifact_text)
                      if h.startswith('Question Bank')), None)
    if bank_body is None:
        findings.append(('X2', False, 'no Question Bank section to resolve Q-labels against'))
        return
    defined = set(_QLABEL_DEF_RE.findall(bank_body))
    referenced = set(_QLABEL_REF_RE.findall(artifact_text))
    dangling = sorted(referenced - defined)
    findings.append(('X2', not dangling,
                     f'all Q-label references resolve ({len(defined)} defined)'
                     if not dangling
                     else f'Q-labels referenced but not defined in Question Bank: {dangling}'))


# ---------------------------------------------------------------------------
# X3: Appendix block schema (prep-forward only)
# ---------------------------------------------------------------------------

_BLOCK_FIELD_RE = re.compile(r'^\*\*([^*]+?)\*\*', re.MULTILINE)
_ALLOWED_BLOCK_FIELDS = ('Purpose', 'Interviewer', 'Emphasis')


def check_appendix_fields(artifact_text, findings):
    """X3: Appendix blocks carry only schema fields (prep-forward only).

    Outcome, Asked and other post-interview content belong in session_log.md
    and interview_notes.md, not the prep Appendix.
    """
    m = _APPENDIX_RE.search(artifact_text)
    if not m:
        findings.append(('X3', True, 'no APPENDIX region (nothing to check)'))
        return
    bad = []
    for h, body in _sections(artifact_text[m.end():]):
        for label in _BLOCK_FIELD_RE.findall(body):
            first = label.strip().split()[0].rstrip(':') if label.strip() else ''
            if first not in _ALLOWED_BLOCK_FIELDS:
                bad.append(f'{h}: **{label.strip()}**')
    findings.append(('X3', not bad,
                     'Appendix blocks carry only schema fields'
                     if not bad
                     else 'non-schema Appendix fields (belong in session_log/notes): '
                          + '; '.join(bad)))


# ---------------------------------------------------------------------------
# X4: no scheduling metadata in an Appendix heading
# ---------------------------------------------------------------------------

_HEADING_DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}')
# Status vocabulary per templates/session_log.md ("scheduled | held |
# cancelled <date> | no-show"). Keep in sync with that line; a later change may
# derive this from the template so it cannot drift.
_EVENT_STATUS_RE = re.compile(
    r'\b(scheduled|held|cancelled|no-show)\b', re.IGNORECASE)


def check_appendix_status(artifact_text, findings):
    """X4: Appendix headings carry no scheduling metadata.

    The prep doc is prep-forward: an Appendix heading names the round and its
    interviewer(s), nothing more. Dates and event statuses live in session_log.md
    (the record) and interview_notes.md (the capture surface). A date here goes
    stale the moment the interview moves, in the one doc the candidate reads
    immediately before walking into the room.
    """
    m = _APPENDIX_RE.search(artifact_text)
    if not m:
        findings.append(('X4', True, 'no APPENDIX region (nothing to check)'))
        return
    bad = []
    blocks = _sections(artifact_text[m.end():])
    for heading, _ in blocks:
        if _HEADING_DATE_RE.search(heading):
            bad.append(f'{heading}: carries a date (belongs in session_log.md)')
        sm = _EVENT_STATUS_RE.search(heading)
        if sm:
            bad.append(f'{heading}: carries event status "{sm.group(1)}" '
                       f'(belongs in session_log.md)')
    findings.append(('X4', not bad,
                     f'{len(blocks)} Appendix heading(s) free of scheduling metadata'
                     if not bad
                     else 'scheduling metadata in an Appendix heading: ' + '; '.join(bad)))
