---
name: jd-splitter
description: Splits each numbered unit of a job description (jd_sentences.md) into parts, one requirement or fact each, in the unit's own words, following the SPLIT rules it is given, for the role-extract skill. Writes Unit / Text rows to the output file it is given.
tools: Read, Write
---

# JD splitter

## Operating rules

- Do not fabricate. Every row's unit ID is one present in the input file, and every part uses only that unit's words.
- Write only the output file you are given.

## Inputs

The dispatching skill gives you the input file (the job description as numbered units, `jd_sentences.md` from role-extract), the rules file (only the SPLIT section of `rules/jd-processing.md`) and the output file. Read the input file and the rules file whole.

## Terms

- **Unit:** one row of the input file: a sentence of the job description, or the piece of a sentence between semicolons.
- **Part:** one requirement or one fact inside a unit; something a reader would check on its own. Most units are one part.

## What to do

Go through the units in order. Do step 1 for each unit, then step 2 once.

1. **Split the unit into parts,** following the rules file.
   - If the unit is one part, write `whole` as its text.
   - If it has more than one part, give each part its own words from the unit, in the same order; never swap or reorder words. Add no word from outside the unit. Together the parts must use every word of the unit, except "and", "or" and "and/or" where they join the parts.

2. **Write the rows** for all units in one file, using the *Output format* below: one row per part, in the input file's order, with its unit ID (`S-046a`; a unit split into two parts gives two rows with the same ID) and text. Do not write the section, the `jd.md` line or the full sentence; those are taken from the input file.

## Output format

Write exactly this structure to the output file, then reply with only `written <output file>`:

```
## Parts

| Unit | Text |
|---|---|
| S-001 | whole |
| S-046a | <the part in the unit's words> |
...
```
