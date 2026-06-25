#!/usr/bin/env python3
"""
cv_qc.py - mechanical QC for the cv-targeted skill's CV content artifact

Runs the deterministic correctness / integrity checks against a drafted
cv_content.md (per the cv-content-qc-scope design decision and the hard rules in
rules/cv/cv-structure.md). Report-only: unlike axis_qc.py, the CV checks are not
auto-fixable (every fix is a rewrite only the Drafter can do), so this script
reports findings and the calling skill loops them back to the Drafter.

Output: a JSON object on stdout with per-check entries:
  { "checks": [ { "id": "C1", "passed": bool, "detail": "<one-line>" }, ... ] }
The calling skill aggregates these with the qc-cv-targeted judgment subagent's
output (semantic traceability, acronym-expansion, per-claim summary support) to
build the unresolved-findings list it routes back to the Drafter.

Drafter -> QC output contract (cv_content.md):
  - Sections are '## <Section Name>' headings.
  - Within-role thematic subheadings are '### <CR text>' and carry a
    '<!-- cr: CR-NNN -->' marker naming the critical requirement they mirror.
  - Bullets are markdown list items ('- ' after optional indent). Every bullet
    ends with a citation comment '<!-- src: EX-12, EX-15 -->' naming the
    inventory/narrative entries it derives from.
  - Core Competencies items are a single-level bulleted list ('- ') or a
    pipe/comma-delimited run; each zone (or the section, if unzoned) carries at
    least one '<!-- src: ... -->'.
  - The Professional Summary is prose carrying at least one '<!-- src: ... -->'.
  - Company / role header lines are NOT list items (no leading '- ').

Checks (all report-only):
  C1   every experience / work-output bullet carries a src citation
  C2   Core Competencies and the summary carry a src citation
  C3   every cited EX/PR/ST id is well-formed and exists in the corpus
  C4   (with --gap-analysis) subheading cr markers name a real CR-NNN
  C5   experience bullets attributed to the right employer/role (per-block
       distinct Role tags do not exceed the block's role-title count)
  C6   independent project (PR-NNN) entries are not cited in Professional
       Experience (they belong in the Selected Projects work-output section)
  C7   every Professional Experience company block carries a role-title line
       (Selected Projects / work-output project headers are exempt)
  B1   one sentence per bullet
  B2   bullet within the line limit (<=3 estimated rendered lines)
  S1   section order valid (evidence band, then credentials tail; Tech last)
  S2   required sections present
  S3   Core Competencies item count within the level's range
  L1   total estimated pages within the level's ceiling
  F1   no em dash (U+2014) in the document
  F2   AI-tell phrasing matches (negation-contrast, buzzwords, copulas, intensifiers)
  N1   roles in reverse-chronological order; entry dates coherent
  N2   no duplicate standalone use of the same entry id

Acronym-expansion-on-first-use and per-claim summary support are judgment checks
owned by the qc-cv-targeted subagent, not this script (neither is reliably
determinable by regex).

Author    : Jason Delosh
Created   : 2026-05-29
Project   : career
Usage     : python scripts/cv_qc.py --cv-file <path> --inventory <path> \
                --narratives <path> --level <ic|leadership> \
                [--gap-analysis <path>]
Depends   : pyyaml (via _config); stdlib otherwise
"""

import argparse
import json
import math
import re
import sys
from collections import Counter

import _config
import _util


# ---------------------------------------------------------------------------
# Calibration and level constants
# Geometry guard constants are the cv-structure.md "Calibration guard
# constants" (US Letter, 0.75in margins, Calibri 11pt). They are a conservative
# estimate only; the render stage is authoritative. Bullet capacity is slightly
# below full width since bullets sit at a 0.25in indent.
# ---------------------------------------------------------------------------

USABLE_LINES_PAGE_1 = 47      # name + contact block consume page 1's top
USABLE_LINES_LATER = 50
CHARS_PER_LINE_BULLET = 95    # indented list item (0.25in indent)
CHARS_PER_LINE_FULL = 100     # full-width prose / competency line
BULLET_LINE_MAX = 3           # cv-structure.md hard rule: 4+ lines never

# Per-level Core Competencies item count range and page ceiling.
COMPETENCY_RANGE = {'ic': (8, 10), 'leadership': (8, 12)}
PAGE_CEILING = {'ic': 3, 'leadership': 3}

# Canonical section bands (cv-structure.md "Section order - two bands"). Members
# are matched case-insensitively on a normalized heading; relevance-gated
# members are optional, but when present must hold this relative order.
EVIDENCE_BAND = [
    'professional summary',
    'core competencies',
    'professional experience',
    'earlier professional roles',  # optional; compressed Company|Title|Dates tail of experience
    'work-output',          # Selected Projects / Publications / Research (matched loosely below)
]
CREDENTIALS_TAIL = [
    'education',
    'certifications & training',
    'professional affiliations',
    'technical proficiencies',
]
REQUIRED_SECTIONS = [
    'professional summary',
    'core competencies',
    'professional experience',
    'education',
]

# ---------------------------------------------------------------------------
# Regexes
# Citation markers, entry/requirement id forms, and the mechanical AI-tell
# patterns. The AI-tell set is the deterministically detectable subset of the
# cv-structure.md "No AI-tell phrasing" rule; fuzzier tells stay reviewer
# judgment.
# ---------------------------------------------------------------------------

SRC_RE = re.compile(r'<!--\s*src:\s*([^>]+?)\s*-->')
CR_MARK_RE = re.compile(r'<!--\s*cr:\s*([^>]+?)\s*-->')
ENTRY_ID_RE = re.compile(r'\b(?:EX|PR|ST)-\d+\b')
CR_ID_RE = re.compile(r'\bCR-\d+\b')
ANY_COMMENT_RE = re.compile(r'<!--.*?-->')
EM_DASH = '—'

# C5 attribution. _EX_ROLE_RE maps an inventory EX/PR entry to its RL role record
# (the Role tag sits on the line immediately after the ID line). The other two
# detect Professional Experience company lines (a location token, not bold) and
# role-title lines (bold) so bullets can be grouped into role blocks.
_EX_ROLE_RE = re.compile(
    r'^ID:\s+((?:EX|PR)-\d+)[ \t]*\n[ \t]*Role:\s+(RL-\d+)', re.MULTILINE)
_PE_LOCATION_RE = re.compile(
    r'\((?:remote|onsite|on-site|hybrid)\)|,\s*[A-Z]{2}\b', re.IGNORECASE)
_BOLD_LINE_RE = re.compile(r'^\*\*.+\*\*')

# Sentence-terminator heuristic: a '.', '!' or '?' followed by whitespace or
# end-of-string. Common abbreviations and decimals are masked before counting
# (see _sentence_count) so they do not inflate the count.
_SENT_END_RE = re.compile(r'[.!?](?:\s|$)')
_ABBREVIATIONS = ['e.g.', 'i.e.', 'etc.', 'vs.', 'U.S.', 'Ph.D.', 'approx.', 'No.']

# AI-tell patterns. Each entry is (label, compiled-regex). Reported, not fixed.
_AI_TELL_PATTERNS = [
    ('negation-contrast', re.compile(
        r"\bnot just\b.*?\bbut\b"
        r"|\bit'?s not\b.*?\bit'?s\b"
        r"|\bnot\b[^,.]*,\s*but\b"
        r"|\bless about\b.*?\bmore about\b", re.IGNORECASE)),
    ('marketing-copula', re.compile(
        r"\b(?:serves as|stands as|is designed to|designed to)\b", re.IGNORECASE)),
    ('vague-intensifier', re.compile(
        r"\b(?:significantly|greatly|successfully|substantially)\b", re.IGNORECASE)),
    ('buzzword', re.compile(
        r"\b(?:leverage[ds]?|robust|seamless(?:ly)?|pivotal|crucial|"
        r"foster(?:ed|ing)?|underscore[ds]?|showcase[ds]?|groundbreaking|"
        r"world-class|cutting-edge|transformative)\b", re.IGNORECASE)),
]

# Domain-legitimate uses of an AI-tell token: when the token appears in one of
# these phrase contexts it is professional terminology, not marketing fluff, and
# is not flagged. (E.g. "pivotal study/trial/Phase/program" is the registrational-
# trial sense, not "pivotal" used as a synonym for "crucial".) A flagged match
# whose position falls inside one of these spans is excluded. Extend as real
# collisions surface; do not add speculative entries.
_AI_TELL_DOMAIN_USES = re.compile(
    r"\bpivotal[\s-]+(?:phase|stud(?:y|ies)|trials?|programs?|programmes?)\b",
    re.IGNORECASE)


# ---------------------------------------------------------------------------
# Report record
# ---------------------------------------------------------------------------

def _record(check_id, passed, detail):
    """Build one entry for the qc output report."""
    return {'id': check_id, 'passed': passed, 'detail': detail}


# ---------------------------------------------------------------------------
# Document parsing
# Split the CV into '## ' sections, then expose helpers for iterating bullets
# and pulling citations. Parsing is deliberately tolerant: it keys off list-item
# syntax and the citation-comment contract, not on exact heading spelling.
# ---------------------------------------------------------------------------

def _normalize_heading(h):
    """Lowercase, collapse whitespace; map work-output members to 'work-output'."""
    h = re.sub(r'\s+', ' ', h).strip().lower()
    if h in ('selected projects', 'publications', 'research', 'patents',
             'presentations'):
        return 'work-output'
    return h


def _split_sections(text):
    """Return an ordered list of (raw_heading, normalized_heading, body) tuples.

    Body is the text between this '## ' heading and the next one. Content above
    the first '## ' (title / contact block) is ignored for section checks.
    """
    sections = []
    matches = list(re.finditer(r'(?m)^##[ ]+(.+?)[ \t]*$', text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw = m.group(1).strip()
        sections.append((raw, _normalize_heading(raw), text[start:end]))
    return sections


def _bullets(body):
    """Yield each markdown list item ('- ' after optional indent) in body."""
    for line in body.splitlines():
        if re.match(r'^\s*-\s+', line):
            yield line


def _strip_markup(line):
    """Remove the leading list marker and any HTML comments from a bullet line."""
    line = re.sub(r'^\s*-\s+', '', line)
    line = ANY_COMMENT_RE.sub('', line)
    return line.strip()


def _estimate_lines(visible_text, per_line):
    """Estimate rendered line count for a unit (ceil of chars / capacity)."""
    n = len(visible_text)
    if n == 0:
        return 0
    return max(1, math.ceil(n / per_line))


def _sentence_count(visible_text):
    """Count sentences in a bullet, masking abbreviations and decimals first.

    Decimals (3.5) and known abbreviations (e.g., U.S.) carry internal periods
    that would otherwise read as sentence ends. Mask them to 'X' before
    counting '[.!?] (space|end)' occurrences. A trailing terminator counts as
    one sentence; the result is the number of terminators.
    """
    t = visible_text
    for abbr in _ABBREVIATIONS:
        t = t.replace(abbr, abbr.replace('.', 'X'))
    t = re.sub(r'(\d)\.(\d)', r'\1X\2', t)   # decimals
    return len(_SENT_END_RE.findall(t))


# ---------------------------------------------------------------------------
# Group C - Citations (traceability)
# C1/C2 enforce citation presence; C3 enforces that cited ids are real; C4
# (optional) enforces that subheading cr markers name a real critical
# requirement. C3 is the strongest mechanical anti-fabrication guard.
# ---------------------------------------------------------------------------

def _experience_sections(sections):
    """Return bodies of sections whose bullets must be cited (experience + work-output)."""
    out = []
    for raw, norm, body in sections:
        if norm == 'professional experience' or norm == 'work-output':
            out.append((raw, body))
    return out


def _check_c1_bullets_cited(sections):
    """C1: every experience / work-output bullet carries a src citation."""
    uncited = []
    for raw, body in _experience_sections(sections):
        for line in _bullets(body):
            if not SRC_RE.search(line):
                uncited.append(_strip_markup(line)[:50])
    if uncited:
        sample = '; '.join(uncited[:3])
        return _record('C1', False,
                       f'{len(uncited)} bullet(s) missing a src citation: {sample}')
    return _record('C1', True, 'all experience/work-output bullets carry a citation')


def _check_c2_competencies_summary_cited(sections):
    """C2: Core Competencies and the Professional Summary each carry a citation."""
    problems = []
    found = {'core competencies': False, 'professional summary': False}
    for raw, norm, body in sections:
        if norm in found:
            found[norm] = True
            if not SRC_RE.search(body):
                problems.append(raw)
    for norm, present in found.items():
        if not present:
            problems.append(f'{norm} (section absent)')
    if problems:
        return _record('C2', False,
                       f'missing citation in: {", ".join(problems)}')
    return _record('C2', True, 'Core Competencies and Summary carry citations')


def _check_c3_ids_exist(text, valid_ids):
    """C3: every cited EX/PR/ST id is well-formed and exists in the corpus."""
    cited = set()
    for m in SRC_RE.finditer(text):
        cited.update(ENTRY_ID_RE.findall(m.group(1)))
        # Flag malformed tokens inside a src marker (anything not an id/cr).
    bad = sorted(i for i in cited if i not in valid_ids)
    if bad:
        return _record('C3', False,
                       f'cited id(s) not found in inventory/narratives: {", ".join(bad)}')
    if not cited:
        return _record('C3', False, 'no src citations found in the document')
    return _record('C3', True, f'all {len(cited)} cited id(s) exist in the corpus')


def _check_c4_subheading_crs(text, valid_crs):
    """C4 (with --gap-analysis): subheading cr markers name a real CR-NNN."""
    cited = set()
    for m in CR_MARK_RE.finditer(text):
        cited.update(CR_ID_RE.findall(m.group(1)))
    bad = sorted(c for c in cited if c not in valid_crs)
    if bad:
        return _record('C4', False,
                       f'subheading cr marker(s) not in gap analysis: {", ".join(bad)}')
    return _record('C4', True,
                   f'{len(cited)} subheading cr marker(s) reconcile with gap analysis')


def _check_c5_role_attribution(sections, ex_to_rl):
    """C5: experience bullets are attributed to the right employer/role.

    Within each Professional Experience role block, the distinct Role tags of the
    cited EX/PR entries must not exceed the number of role-title lines in that
    block (1 for a normal role; N for a stacked multi-role block). An entry whose
    Role tag belongs to a different employer than the block it sits under is the
    misattribution this catches. ST narrative citations are ignored (cross-role
    by design); entries with no resolvable Role are skipped.
    """
    pe_body = next((body for _, norm, body in sections
                    if norm == 'professional experience'), None)
    if pe_body is None:
        return _record('C5', True, 'no Professional Experience section to check')

    blocks = []      # closed role blocks: {'titles': int, 'rls': set, 'label': str}
    cur = None       # block under construction
    prev = None      # 'company' | 'title' | 'bullet'

    def _close(block):
        if block is not None and block['titles'] >= 1:
            blocks.append(block)

    for raw_line in pe_body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r'^-\s+', line):
            if cur is not None:
                for m in SRC_RE.finditer(raw_line):
                    for cid in ENTRY_ID_RE.findall(m.group(1)):
                        if cid.startswith('ST-'):
                            continue
                        rl = ex_to_rl.get(cid)
                        if rl:
                            cur['rls'].add(rl)
            prev = 'bullet'
            continue
        visible = ANY_COMMENT_RE.sub('', line).strip()
        if _BOLD_LINE_RE.match(visible):
            # Role-title line. After bullets it opens a new block; consecutive
            # titles (after a company or another title) stack into one block.
            if prev == 'bullet' or cur is None:
                _close(cur)
                cur = {'titles': 1, 'rls': set(), 'label': visible[:40]}
            else:
                cur['titles'] += 1
            prev = 'title'
        elif _PE_LOCATION_RE.search(visible):
            # Company line: closes the prior block; role titles follow.
            _close(cur)
            cur = None
            prev = 'company'
        # any other plain line (e.g. a '### CR' subheading) is ignored
    _close(cur)

    bad = [b for b in blocks if len(b['rls']) > b['titles']]
    if bad:
        sample = '; '.join(
            f"{b['label']} ({len(b['rls'])} employers under {b['titles']} "
            f"title{'s' if b['titles'] > 1 else ''})" for b in bad[:3])
        return _record('C5', False,
                       f'{len(bad)} role block(s) cite entries from more employers '
                       f'than roles, likely misattribution: {sample}')
    return _record('C5', True,
                   'experience bullets attributed to the correct employer/role')


def _check_c6_no_project_in_experience(sections):
    """C6: independent project (PR-NNN) entries are not cited in Professional Experience.

    PR-NNN ids are inventory Section 9 independent / volunteer projects; per
    cv-structure.md they belong in the work-output (Selected Projects) section,
    placed after Professional Experience, not as roles or bullets inside it. A PR
    citation in the Professional Experience body signals project work misplaced as
    an experience role (e.g. a between-roles independent build elevated to the top
    of the experience section). EX/ST citations are unaffected.
    """
    pe_body = next((body for _, norm, body in sections
                    if norm == 'professional experience'), None)
    if pe_body is None:
        return _record('C6', True, 'no Professional Experience section to check')
    pr_cited = set()
    for line in _bullets(pe_body):
        for m in SRC_RE.finditer(line):
            pr_cited.update(re.findall(r'\bPR-\d+\b', m.group(1)))
    if pr_cited:
        return _record('C6', False,
                       'independent project entr(y/ies) cited in Professional Experience '
                       f'(belong in Selected Projects): {", ".join(sorted(pr_cited))}')
    return _record('C6', True,
                   'no independent project (PR) entries in Professional Experience')


def _check_c7_role_titles_present(sections):
    """C7: every Professional Experience company block carries a role-title line.

    cv-structure.md requires each company entry to be followed by its role
    title(s); a company line followed directly by bullets, with no bold title line
    between them, is a missing-title defect (the case that slips through when a
    within-threshold role is compressed to a scope summary). Company lines are
    bold header lines carrying a location/date token; title lines are bold lines
    without one (mirrors the C5 company-vs-title split). Selected Projects /
    work-output entries are exempt (project voice uses a project-name header, not
    a job title) and are not in this section.
    """
    pe_body = next((body for _, norm, body in sections
                    if norm == 'professional experience'), None)
    if pe_body is None:
        return _record('C7', True, 'no Professional Experience section to check')
    missing = []          # company labels whose bullets precede any title line
    cur_company = None     # label of the company block under construction
    has_title = False
    for raw_line in pe_body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r'^-\s+', line):
            if cur_company is not None and not has_title:
                missing.append(cur_company)
                cur_company = None   # report once per block
            continue
        visible = ANY_COMMENT_RE.sub('', line).strip()
        if not _BOLD_LINE_RE.match(visible):
            continue   # '### CR' subheadings and plain lines are not titles
        if _PE_LOCATION_RE.search(visible):
            cur_company = visible[:40]   # company line opens a new block
            has_title = False
        elif cur_company is not None:
            has_title = True             # bold non-company line = role title
    if missing:
        return _record('C7', False,
                       f'{len(missing)} company block(s) missing a role title: '
                       f'{"; ".join(missing[:3])}')
    return _record('C7', True,
                   'every Professional Experience company has a role title')


# ---------------------------------------------------------------------------
# Group B - Bullet rules
# B1 (one sentence) and B2 (line limit) are cv-structure.md hard rules.
# ---------------------------------------------------------------------------

def _check_b1_one_sentence(sections):
    """B1: each experience / work-output bullet is exactly one sentence."""
    multi = []
    for raw, body in _experience_sections(sections):
        for line in _bullets(body):
            visible = _strip_markup(line)
            if _sentence_count(visible) > 1:
                multi.append(visible[:50])
    if multi:
        sample = '; '.join(multi[:3])
        return _record('B1', False,
                       f'{len(multi)} multi-sentence bullet(s): {sample}')
    return _record('B1', True, 'all bullets are single-sentence')


def _check_b2_bullet_length(sections):
    """B2: each bullet renders within the line limit (<=3 estimated lines)."""
    over = []
    for raw, body in _experience_sections(sections):
        for line in _bullets(body):
            visible = _strip_markup(line)
            if _estimate_lines(visible, CHARS_PER_LINE_BULLET) > BULLET_LINE_MAX:
                over.append(visible[:50])
    if over:
        sample = '; '.join(over[:3])
        return _record('B2', False,
                       f'{len(over)} bullet(s) over {BULLET_LINE_MAX} estimated lines: {sample}')
    return _record('B2', True, f'all bullets within {BULLET_LINE_MAX} estimated lines')


# ---------------------------------------------------------------------------
# Group S - Structure / banding
# S1 verifies the two-band order; S2 required sections; S3 competency count.
# ---------------------------------------------------------------------------

def _check_s1_section_order(sections):
    """S1: sections follow the two-band canonical order; Tech Proficiencies last.

    Build the canonical index for each recognized heading (evidence band before
    credentials tail), ignoring unrecognized headings, and verify the recognized
    headings appear in non-decreasing canonical order.
    """
    canonical = {name: i for i, name in enumerate(EVIDENCE_BAND + CREDENTIALS_TAIL)}
    seen = [(norm, canonical[norm]) for _, norm, _ in sections if norm in canonical]
    order_idx = [idx for _, idx in seen]
    if order_idx != sorted(order_idx):
        names = ' -> '.join(n for n, _ in seen)
        return _record('S1', False, f'section order violates the two-band order: {names}')
    # Technical Proficiencies, if present, must be the last recognized section.
    if seen and 'technical proficiencies' in [n for n, _ in seen]:
        if seen[-1][0] != 'technical proficiencies':
            return _record('S1', False, 'Technical Proficiencies is present but not last')
    return _record('S1', True, 'section order valid')


def _check_s2_required_sections(sections):
    """S2: the required sections are all present."""
    present = {norm for _, norm, _ in sections}
    missing = [s for s in REQUIRED_SECTIONS if s not in present]
    if missing:
        return _record('S2', False, f'missing required section(s): {", ".join(missing)}')
    return _record('S2', True, 'all required sections present')


def _count_competencies(body):
    """Count Core Competencies items: bulleted items, else pipe-delimited tokens.

    A bulleted list counts list items. A pipe-delimited run counts the pipe-
    separated tokens across the section's non-blank, non-heading lines (after
    stripping comments and bold zone labels). The pipe (or a bulleted list) is
    the only item delimiter; commas are within-item punctuation (parenthetical
    enumerations like "(CDASH, SDTM, CDISC LAB)", tool lists) and never separate
    items, so a within-item comma cannot inflate the count.
    """
    bullet_items = [l for l in body.splitlines() if re.match(r'^\s*-\s+', l)]
    if bullet_items:
        # Zone-bullets: when the bullet lines carry pipe-delimited items (2-3
        # coherent zones, each a bullet, items separated by '|' per cv-structure
        # Core Competencies), the items are the pipe tokens, not the bullets. Only
        # when no bullet carries a pipe is each bullet itself a single item.
        if any('|' in ANY_COMMENT_RE.sub('', l) for l in bullet_items):
            count = 0
            for line in bullet_items:
                line = ANY_COMMENT_RE.sub('', line)
                line = re.sub(r'^\s*-\s+', '', line).strip()
                tokens = [t for t in re.split(r'\|', line) if t.strip()]
                count += len(tokens)
            return count
        return len(bullet_items)
    count = 0
    for line in body.splitlines():
        line = ANY_COMMENT_RE.sub('', line).strip()
        if not line or line.startswith('#') or re.fullmatch(r'\*\*.+\*\*', line):
            continue
        tokens = [t for t in re.split(r'\|', line) if t.strip()]
        count += len(tokens)
    return count


def _check_s3_competency_count(sections, level):
    """S3: Core Competencies item count within the level's range."""
    lo, hi = COMPETENCY_RANGE[level]
    for _, norm, body in sections:
        if norm == 'core competencies':
            n = _count_competencies(body)
            if n < lo or n > hi:
                return _record('S3', False,
                               f'Core Competencies has {n} items; expected {lo}-{hi} for {level}')
            return _record('S3', True, f'Core Competencies count {n} within {lo}-{hi}')
    return _record('S3', False, 'Core Competencies section absent')


# ---------------------------------------------------------------------------
# Group L - Length guard
# L1 is the document-level geometry estimate vs the level's page ceiling. A
# conservative guard only; the render stage measures actual pagination.
# ---------------------------------------------------------------------------

def _check_l1_page_estimate(text, level):
    """L1: estimated total pages within the level's ceiling.

    Estimate each non-blank, non-comment-only line's wrapped length (bullets at
    the bullet capacity, everything else at full width), sum, then convert to
    pages with the page-1 / later usable-line constants.
    """
    total_lines = 0
    for raw_line in text.splitlines():
        line = ANY_COMMENT_RE.sub('', raw_line).strip()
        if not line:
            continue
        if re.match(r'^-\s+', line):
            total_lines += _estimate_lines(re.sub(r'^-\s+', '', line), CHARS_PER_LINE_BULLET)
        else:
            total_lines += _estimate_lines(line, CHARS_PER_LINE_FULL)

    if total_lines <= USABLE_LINES_PAGE_1:
        pages = 1
    else:
        pages = 1 + math.ceil((total_lines - USABLE_LINES_PAGE_1) / USABLE_LINES_LATER)

    ceiling = PAGE_CEILING[level]
    if pages > ceiling:
        return _record('L1', False,
                       f'estimated {pages} pages (~{total_lines} lines) exceeds the '
                       f'{ceiling}-page ceiling for {level}')
    return _record('L1', True, f'estimated {pages} page(s) within the {ceiling}-page ceiling')


# ---------------------------------------------------------------------------
# Group F - Format (report-only flags)
# F1 em dashes; F2 the mechanical AI-tell subset. Both report matches for the
# Drafter to rewrite.
# ---------------------------------------------------------------------------

def _check_f1_no_em_dash(text):
    """F1: no em dash (U+2014) anywhere in the document."""
    count = text.count(EM_DASH)
    if count:
        return _record('F1', False, f'{count} em dash(es) (U+2014) present; use pipe/hyphen or rewrite')
    return _record('F1', True, 'no em dashes')


def _check_f2_ai_tells(text):
    """F2: flag mechanical AI-tell phrasing matches (report-only).

    Reports the actual matched terms (deduped, lowercased, with per-term counts)
    rather than a bare category count, so a flagged finding is directly
    actionable and a false positive (e.g. a domain term like "pivotal") is
    visible in the output without re-grepping the document. Long spans (e.g. a
    negation-contrast clause) are truncated to keep the line readable.
    """
    # Strip comments so citation/cr markers do not get scanned for tells.
    visible = ANY_COMMENT_RE.sub('', text)
    # Character spans covered by a domain-legitimate use (e.g. "pivotal trial");
    # a flagged token whose start falls inside one of these is professional
    # terminology, not fluff, and is excluded.
    allow_spans = [m.span() for m in _AI_TELL_DOMAIN_USES.finditer(visible)]

    def _allowed(start):
        return any(s <= start < e for s, e in allow_spans)

    hits = []
    for label, pattern in _AI_TELL_PATTERNS:
        # Collapse internal whitespace and lowercase so casing/spacing variants
        # of the same term collapse into one count; drop domain-legitimate uses.
        terms = [re.sub(r'\s+', ' ', m.group(0)).strip().lower()
                 for m in pattern.finditer(visible) if not _allowed(m.start())]
        if not terms:
            continue
        counts = Counter(terms)
        parts = []
        for term, n in counts.items():
            shown = term if len(term) <= 40 else term[:40] + '...'
            parts.append(f'{shown} x{n}' if n > 1 else shown)
        hits.append(f'{label}: {", ".join(parts)}')
    if hits:
        return _record('F2', False, 'AI-tell phrasing flagged: ' + '; '.join(hits))
    return _record('F2', True, 'no mechanical AI-tell phrasing flagged')


# ---------------------------------------------------------------------------
# Group N - Consistency
# N1 reverse-chronological role order + date coherence; N2 no duplicate
# standalone use of an entry id. Both are best-effort over the experience body.
# ---------------------------------------------------------------------------

def _check_n1_chronology(sections):
    """N1: roles run reverse-chronological; each date range has start <= end.

    Years are read from 4-digit tokens on header lines (lines that are not list
    items and carry a year). Uses each header's end-year as the sort key. Best
    effort: lines without a parseable year are skipped.
    """
    end_years = []
    for raw, norm, body in sections:
        if norm != 'professional experience':
            continue
        for line in body.splitlines():
            if re.match(r'^\s*-\s+', line) or line.startswith('#'):
                continue
            # Non-capturing group so findall returns the whole year, not '19'/'20'.
            years = [int(y) for y in re.findall(r'\b(?:19|20)\d{2}\b', line)]
            if not years:
                continue
            start, end = years[0], years[-1]
            if start > end:
                return _record('N1', False,
                               f'date range start after end on a header line: {line.strip()[:50]}')
            end_years.append(end)
    if end_years and end_years != sorted(end_years, reverse=True):
        return _record('N1', False, 'roles are not in reverse-chronological order')
    return _record('N1', True, 'role chronology and date ranges coherent')


def _check_n2_no_duplicate_ids(sections):
    """N2: no entry id is the sole src on more than one bullet (likely duplicate)."""
    sole_use = {}
    for raw, body in _experience_sections(sections):
        for line in _bullets(body):
            m = SRC_RE.search(line)
            if not m:
                continue
            ids = ENTRY_ID_RE.findall(m.group(1))
            if len(ids) == 1:
                sole_use[ids[0]] = sole_use.get(ids[0], 0) + 1
    dups = sorted(i for i, c in sole_use.items() if c > 1)
    if dups:
        return _record('N2', False, f'entry id(s) used as a sole-source bullet more than once: {", ".join(dups)}')
    return _record('N2', True, 'no duplicate standalone entry use')


# ---------------------------------------------------------------------------
# QC orchestrator
# Runs each check group in order against the drafted CV. Report-only: nothing is
# written back. C4 runs only when --gap-analysis is supplied. The result is a
# per-check JSON report the calling skill aggregates with the judgment subagent.
# ---------------------------------------------------------------------------

def run_qc(args):
    """Run mechanical QC checks against --cv-file and print a per-check JSON report."""
    text = _util.read(args.cv_file)
    sections = _split_sections(text)

    # Valid id universe for C3: all EX/PR ids in the inventory plus all ST ids
    # in narratives. Membership only; references and definitions both count.
    inv_text = _util.read(args.inventory)
    valid_ids = set(ENTRY_ID_RE.findall(inv_text))
    valid_ids.update(ENTRY_ID_RE.findall(_util.read(args.narratives)))
    # EX/PR -> RL map for C5 (employer/role attribution).
    ex_to_rl = dict(_EX_ROLE_RE.findall(inv_text))

    checks = []

    # --- Group C: citations / traceability ---
    checks.append(_check_c1_bullets_cited(sections))
    checks.append(_check_c2_competencies_summary_cited(sections))
    checks.append(_check_c3_ids_exist(text, valid_ids))
    if args.gap_analysis:
        valid_crs = set(CR_ID_RE.findall(_util.read(args.gap_analysis)))
        checks.append(_check_c4_subheading_crs(text, valid_crs))
    checks.append(_check_c5_role_attribution(sections, ex_to_rl))
    checks.append(_check_c6_no_project_in_experience(sections))
    checks.append(_check_c7_role_titles_present(sections))

    # --- Group B: bullet rules ---
    checks.append(_check_b1_one_sentence(sections))
    checks.append(_check_b2_bullet_length(sections))

    # --- Group S: structure / banding ---
    checks.append(_check_s1_section_order(sections))
    checks.append(_check_s2_required_sections(sections))
    checks.append(_check_s3_competency_count(sections, args.level))

    # --- Group L: length guard ---
    checks.append(_check_l1_page_estimate(text, args.level))

    # --- Group F: format ---
    checks.append(_check_f1_no_em_dash(text))
    checks.append(_check_f2_ai_tells(text))

    # --- Group N: consistency ---
    checks.append(_check_n1_chronology(sections))
    checks.append(_check_n2_no_duplicate_ids(sections))

    print(json.dumps({'checks': checks}))


# ---------------------------------------------------------------------------
# Command-line entry point
# Required: --cv-file, --inventory, --narratives, --level. Optional:
# --gap-analysis (enables C4). Exit codes mirror axis_qc.py: 0 ok, 1 error.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, run QC, emit JSON report."""
    parser = argparse.ArgumentParser(
        description='cv-targeted mechanical QC (report-only)')
    parser.add_argument('--cv-file', required=True, help='path to the drafted cv_content.md')
    parser.add_argument('--inventory', required=True, help='path to inventory.md (id validation)')
    parser.add_argument('--narratives', required=True, help='path to narratives.md (ST id validation)')
    parser.add_argument('--level', required=True, choices=['ic', 'leadership'])
    parser.add_argument('--gap-analysis', default=None,
                        help='path to gap_analysis.md; enables the CR-NNN subheading check (C4)')

    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding='utf-8')
        _config.load()   # validates config is loadable / repo root resolves
        run_qc(args)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
