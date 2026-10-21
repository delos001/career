"""
inventory_model - the inventory's data model

One shared place for how inventory.md is read, validated, numbered and
extended. Every script that reads or writes the inventory goes through these
modules instead of carrying its own copy of the logic.

  document     the document as a whole: sections, the table of contents, and
               the field lists read from templates/inventory.md
  entry_block  one ID block of any type: find it, read its fields, assign the
               next ID, check it against the template
  ex, pr, pb, ps, rl
               what each entry type does differently from entry_block.
               Other types (ED, CERT, AFF, TR, AW) get a module when one first
               needs its own rule.

Nothing here writes to disk. Functions that place a new entry return the
updated text; profile_update.py is the only writer.

Author    : Jason Delosh
Created   : 2026-10-21
Project   : career
"""
