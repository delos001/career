#!/usr/bin/env python3
"""
jd_bar.py - set each JD part's Bar: how much it asks for

Bar tells gap analysis and the CV what kind of evidence meets a part. Two
levels (decided 2026-11-18; a third, 'expert', was dropped as a subjective
call that separates little, since "proven" and "demonstrated" appear in most
JDs):
  exposure  indirect or partial evidence can meet it ("Knowledge of GCP")
  working   needs direct evidence ("Experience with SQL", "Ability to ...")
  ''        no bar word: a duty, a degree, a fact; judged by the text itself

Set by rule, from word lists in config.yaml, checked in this order:
  1. a working word (bar_working_words) sets working;
  2. else an exposure word (bar_exposure_words) sets exposure, raised to
     working when a raise word (bar_raise_words) is also present: "Thorough
     knowledge of GCP" is working;
  3. else a praise word alone (bar_praise_words) sets working: "Strong
     judgment", "Strong process-design capability";
  4. else no bar.
Year counts stay in the text; role_extract_qc.py X2 guards them.

Tested 2026-11-18 on APP-029 (89 rows), APP-028 and APP-024: every level read
right except two APP-029 rows that the ranker sets aside as Not ranked (a pay
sentence naming "skills, experience", and a note on experience requirements).

Called by role_extract_assemble.py with Demand. No command line.

Author  : Jason Delosh
Created : 2026-11-18
Project : career
Depends : requirement_kinds (normalize)
"""

import re

import requirement_kinds


# ---------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------

EXPOSURE, WORKING, NONE = 'exposure', 'working', ''
ALLOWED_BARS = {EXPOSURE, WORKING, NONE}


# ---------------------------------------------------------------------------
# Bar
# ---------------------------------------------------------------------------

def _has(text, patterns):
    """True when any pattern matches from a word start in the normalized text."""
    return any(re.search(rf'\b(?:{p})', text) for p in patterns)


def bar_of(text, cfg):
    """Return one part's Bar: 'exposure', 'working' or ''."""
    low = requirement_kinds.normalize(text or '')
    if _has(low, cfg['bar_working_words']):
        return WORKING
    if _has(low, cfg['bar_exposure_words']):
        return WORKING if _has(low, cfg['bar_raise_words']) else EXPOSURE
    if _has(low, cfg['bar_praise_words']):
        return WORKING
    return NONE


def set_bar(texts, cfg):
    """Return the Bar of each part text, in order."""
    return [bar_of(t, cfg) for t in texts]
