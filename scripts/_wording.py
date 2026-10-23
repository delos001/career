#!/usr/bin/env python3
"""
_wording.py - shared mechanical wording checks

The deterministically detectable wording tells, held once so every QC script
that judges written prose applies the same list. cv_qc.py uses them on a CV
draft (F1, F2); profile_update_qc.py uses them on profile entries (P15).
Fuzzier tells stay with each artifact's judgment reviewer.

Author    : Jason Delosh
Created   : 2026-10-22
Project   : career
Usage     : import _wording; _wording.ai_tell_hits(text)
Depends   : stdlib
"""

import re
from collections import Counter


# ---------------------------------------------------------------------------
# Patterns
# Each entry is (label, compiled-regex). Reported, not fixed.
# ---------------------------------------------------------------------------

EM_DASH = '—'

AI_TELL_PATTERNS = [
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
AI_TELL_DOMAIN_USES = re.compile(
    r"\bpivotal[\s-]+(?:phase|stud(?:y|ies)|trials?|programs?|programmes?)\b",
    re.IGNORECASE)


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def ai_tell_hits(visible):
    """Return one 'label: term, term x2' string per pattern that matched.

    Terms are deduped, lowercased, and counted, so a finding is directly
    actionable and a false positive is visible without re-reading the text.
    Long spans (a negation-contrast clause) are truncated.
    """
    allow_spans = [m.span() for m in AI_TELL_DOMAIN_USES.finditer(visible)]

    def _allowed(start):
        return any(s <= start < e for s, e in allow_spans)

    hits = []
    for label, pattern in AI_TELL_PATTERNS:
        terms = [re.sub(r'\s+', ' ', m.group(0)).strip().lower()
                 for m in pattern.finditer(visible) if not _allowed(m.start())]
        if not terms:
            continue
        parts = []
        for term, n in Counter(terms).items():
            shown = term if len(term) <= 40 else term[:40] + '...'
            parts.append(f'{shown} x{n}' if n > 1 else shown)
        hits.append(f'{label}: {", ".join(parts)}')
    return hits
