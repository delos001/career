#!/usr/bin/env python3
"""
jd_demand.py - set each JD part's Demand: required or preferred

The jd-splitter agent cuts each unit of jd_sentences.md into
parts. Demand says how firmly the JD asks for each part, and it is set here by
rule rather than by the agent: tested 2026-11-18 on nine extractor runs
(APP-024, APP-028, APP-029), these rules matched the agent on 530 of 533 parts,
and the three misses were a word-list fault since fixed in config.

A part is 'preferred' when, checked in this order:
  1. its own text holds an optional word (config requirement_optional_words),
     e.g. "Green Belt preferred", "SAS is a plus";
  2. its heading or subheading holds a preferred-heading word (config
     requirement_preferred_headings), e.g. everything under "Preferred
     Qualifications";
  3. it opens with "with" and the part before it, from the same unit, is
     'preferred': "Advanced degree preferred, | with a minimum of five (5)
     years" makes both parts preferred.
Every other part is 'required', including parts with bar words such as
"familiarity with" or "N years"; how high a bar is, is judged elsewhere.

Called by role_extract_assemble.py once the parts carry their full text and
heading. No command line: it has no input of its own.

Author  : Jason Delosh
Created : 2026-11-18
Project : career
Depends : jd_extraction_tables (optional_word, normalize)
"""

import re

import jd_extraction_tables


# ---------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------

REQUIRED, PREFERRED = 'required', 'preferred'

# What each value means, shown in jd_needs.md's Definitions appendix.
DEFINITIONS = [
    (REQUIRED, 'the job description asks for it without marking it optional.'),
    (PREFERRED, 'the job description marks it optional ("preferred", "a plus", "advantageous", or a '
                'preferred-qualifications heading).'),
]

# Regex: a part that continues the one before it with "with ..." (rule 3).
_WITH_RE = re.compile(r'^\W*with\b', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Demand
# ---------------------------------------------------------------------------

def _heading_is_preferred(heading, patterns):
    """True when a heading holds a preferred-heading word."""
    text = jd_extraction_tables.normalize(heading or '')
    return any(re.search(rf'\b(?:{p})\b', text) for p in patterns)


def set_demand(parts, cfg):
    """Return the Demand of each part, in order.

    parts: a list of dicts in JD order, each with 'unit' (S-046a), 'text' (the
    part's full text, never 'whole') and 'heading' (its section and subsection,
    as one string). Rule 3 looks only at the part just before, and only when
    it comes from the same unit.
    """
    demands, prev_unit, prev_demand = [], None, None
    for part in parts:
        if jd_extraction_tables.optional_word(part['text'], cfg['requirement_optional_words']):
            demand = PREFERRED
        elif _heading_is_preferred(part['heading'], cfg['requirement_preferred_headings']):
            demand = PREFERRED
        elif part['unit'] == prev_unit and prev_demand == PREFERRED and _WITH_RE.match(part['text']):
            demand = PREFERRED
        else:
            demand = REQUIRED
        demands.append(demand)
        prev_unit, prev_demand = part['unit'], demand
    return demands
