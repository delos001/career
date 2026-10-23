# Staging writing rules

**Used by:** gap-analysis, preparation-screen, preparation-interview. Any skill
that writes down a new fact about the candidate.

A staged item is a record of what the candidate said, kept for the
profile-update run that writes it into the inventory later. That run cannot
ask the questions this capture skipped, so the capture records who did what,
where, and with what result, or says plainly that it was not stated.

## When to stage

- A gap closed by something the candidate surfaced.
- A partial match where the candidate described experience the inventory
  under-represents.
- A covered requirement that surfaced under-represented experience.
- In interview prep: a general fact about the candidate (not an answer specific
  to this role) that the candidate agrees to stage.

Do not stage what the profile already carries accurately, or an answer that
only makes sense for this role.

## How to stage

Write the capture file, one `Label: value` line per field below, then run:

```
python scripts/staging_append.py --folder <app_folder> --requirement <CR-NNN> --requirement-text-short "<text>" --capture-file <path> --label "<3-5 word label>"
```

With no requirement to anchor it, pass `--requirement "n/a (<short reason>)"`
and drop `--requirement-text-short`. The script fills the date, application,
and job context, and refuses a capture with a field missing or blank. Never
write into the staging file by hand. A better fact arriving before promotion
replaces the item: remove it with `profile_update.py remove --item "<label>"`
and stage again.

## Fields

Every field is required. The "none" forms are answers, not blanks.

- **Work role:** the role where the work happened, as its `RL-NNN`. Not the
  job being applied for. A role the inventory does not hold yet:
  `new: <employer>, <title>`. A tool or credential with no single role:
  `n/a (<reason>)`.
- **Did:** what the candidate did, in plain words. One piece of work per item.
  When the candidate describes several, split them into separate items and show
  the candidate the list before working any of them.
- **Others did:** who did which other part (a team, a vendor, IT), or `none`.
- **Outcome:** the result the candidate stated, or `none stated`. Never write
  an outcome you inferred: "reviewed for X" does not mean "X issues were found".
- **Limits:** any framing limit ("review and input, not authorship") and any
  uncertainty ("unsure of the exact product name"), in the candidate's terms,
  or `none`.

Each value is one line. No first person. Record the fact, not CV wording:
the profile-update run writes the entry.

## Ask before writing

Ask the candidate, and wait for the answer, when:

- the work role is not clear;
- the candidate uses group language ("we", "helped with", "part of a team"):
  ask which part was theirs;
- the description credits someone else for part of the work: ask who did
  which part;
- you are about to write an outcome the candidate did not say;
- the capture would hold only a limit ("don't claim X") with nothing the
  candidate did.

Ask with the source attached: quote what the candidate said, never ask them to
recall it.
