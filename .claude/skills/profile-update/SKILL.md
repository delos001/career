---
name: profile-update
description: Promote staged profile updates into the profile documents. Reads the items in personal/profile/profile_updates_pending.md, walks them with the user one at a time, and writes each into inventory.md as a new entry, as an addition to an existing one, or as an item on a list section. An item is deleted from the queue only after its written entry passes review. Runs standalone at any time, or inline at the end of a gap-analysis run. This is the only skill that writes to the profile documents.
---

# profile-update - promote staged updates into the profile

Writes the items in `personal/profile/profile_updates_pending.md` into the
inventory, one item at a time. Until an item is written, the fact is invisible
to retrieval, gap analysis, and CV creation.

The file's `## Entries` section is a queue. An item waits there and is deleted
once its entry passes review. Nothing records where it went: the profile is the
source.

**This skill is the only writer to `inventory.md`.** Every other skill reads.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases run in order; each has a declared input and output.
- Each phase opens with the **bold lead line** under its heading. Speak it
  verbatim before running the phase.
- **One item at a time, always.** Phase 3 walks a single item from proposal
  through write before naming the next one. Batching the proposals is a failure
  even when the items look identical, and the batch step of any other skill does
  not override this.
- **The staged item is the source, and its Limits field is binding.** A limit
  ("review and input, not authorship") is an instruction to this skill. Write
  nothing the item does not support, and carry every limit forward.
- **Never write a fact the user has not attested.** When the item is too thin
  to write an honest entry, ask the user for what is missing; if it does not
  arrive, leave the item in the queue rather than filling the gap with inference.
- **Rules come through `scripts/rules_slice.py`.** Never read a rules file
  whole when a slice is asked for.
- Script failures halt the phase per global rules.
- Run-scratch goes in `temp/`; this skill has no application folder.

## Mode

Ask at intake, or take the mode from the caller:

- **adhoc** - user-invoked. Phase 2 offers the full pending list.
- **inline** - invoked from gap-analysis Phase 8. Phase 2 defaults to the items
  that run just staged, and offers the rest once those are done.

## Resume check - run before Phase 0

The staging file is the resume state: an item is in it because it is waiting.
Run `python scripts/profile_update.py pending` and continue from what it returns.

## Phase 0 - Intro

**Introducing the profile-update skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py profile-update` and show the output.
- Output: user oriented.

## Phase 1 - Load the work list

**Reading what is staged and waiting.**

- Input: invocation.
- Run `python scripts/profile_update.py pending`. Each line carries the date,
  the label, and the source application.
- Do NOT read the staging file into context. Phase 3 pulls one item at a time
  with `show`.
- Report the count in plain English. Name how far back the oldest one goes,
  since a long backlog means the profile has been under-representing the
  candidate across every application run in that window.
- Output: the pending list.

## Phase 2 - Scope the run

**Agreeing which items this run will process.**

- Input: the pending list.
- Present the list and ask which items to process: all of them, a named subset,
  or the oldest N. In **inline** mode, default to the items the gap-analysis run
  just staged and say so.
- When more than ten items are pending, offer the three options before starting:
  process strictly one at a time, process in clusters the user approves per
  cluster, or stop after a named subset.
- Output: the ordered list of labels this run will walk.

## Phase 3 - Per-item loop

**Walking each staged item into the profile, one at a time.**

Repeat every step below for one item before naming the next.

- **Step 3a - Read the item.** Run
  `python scripts/profile_update.py show --item "<label>"`. Note its Work role,
  what others did, the stated outcome, and every limit.
- **Step 3b - Route it.** Run `python scripts/rules_slice.py routing` and follow
  it: it pulls the related entries with a script and names the one outcome to
  propose (new entry, addition, list item, duplicate, or the user's retraction).
- **Step 3c - Draft against the writing rules.** For an inventory write, run
  `python scripts/rules_slice.py inventory-writing --type <PREFIX>` (the entry
  type being written, e.g. `EX`; `LIST` for a list item) and draft to it.
- **Step 3d - Show the actual text.** Present the full proposed entry, or a
  before/after for an addition, inline in the response. Never describe an edit
  the user has to look up to evaluate. Wait for approval. Apply any correction
  and re-show before writing.
- **Step 3e - Write it.** Each command prints what it wrote; keep those IDs and
  addresses for Phase 4. Never hand-edit `inventory.md`.
  - New inventory entry: write the block WITHOUT its `ID:` line to
    `temp/pu_block.md`, then run
    `python scripts/profile_update.py insert --prefix <PREFIX> --block-file temp/pu_block.md`
    (add `--subsection "<heading>"` for a section that has sub-sections).
  - Addition to an inventory entry: write the approved value to
    `temp/pu_value.md`, then run
    `python scripts/profile_update.py set --id <ID> --field <Field> --value-file temp/pu_value.md`,
    once per field changed. Open the value with a newline for a multi-line
    field such as `Coursework`.
  - A project element: write its one-line text to `temp/pu_value.md`, then run
    `python scripts/profile_update.py element --id <ID> --text-file temp/pu_value.md`,
    with the project's `PR-NNN` to add an element or the element's `PR-NNN.NN`
    to change one; add `--outcome-file` for an observed result.
  - A tool, platform, or exposure item: run
    `python scripts/profile_update.py list-add --target "<Section> / <Category> / <Label>" --item "<item>"`,
    once per item. Drop the ` / <Label>` part only when the category holds a
    single line; a wrong part is answered with the valid choices.
- **Step 3f - Hold the item.** Do not remove it yet. It stays in the queue until
  Phase 4 passes, so a review fix is made against it. A **duplicate** writes
  nothing and is removed in Phase 4 with the rest. A **retracted** item is the
  user's decision; confirm it, then remove it now with
  `python scripts/profile_update.py remove --item "<label>"`.
- Output: per item, the outcome and the IDs or addresses written.

## Phase 4 - Review, then remove

**Reviewing what was written, then clearing it from the queue.**

- Input: the IDs and addresses written this run, and the labels processed.
- **Step 4a - Mechanical checks (script).** Run
  `python scripts/profile_update_qc.py check`, passing `--scope-id` once per
  inventory ID created or edited this run and per list address appended to. It
  covers structure, fields, IDs, placement, references, axis values, the table
  of contents, list sections, staging-item completeness, and the mechanical
  wording rules. Findings on entries this run did not touch are reported as
  pre-existing and do not fail the run; surface them in Phase 5 rather than
  fixing them here. On FAIL: translate to plain English, fix, re-run.
- **Step 4b - Judgment checks (subagent).** Only after Step 4a passes, run
  `python scripts/profile_update_qc.py context`, passing `--item "<label>"` once
  per item processed and `--scope-id` once per ID or address written. It writes
  the reviewer's context file and prints its prompt between `=== PROMPT ===` and
  `=== END ===`. Dispatch `qc-profile-update` with that prompt **exactly as
  printed**. It checks that each entry is supported by its item, that limits
  survived, and that each field holds what the writing rules say it holds.
  Loops on findings.
- Cap the loop at **3 iterations** across both steps. If findings remain, carry
  them into Phase 5 so the user sees them rather than stalling the run.
- **Step 4c - Remove.** Once the loop ends, run
  `python scripts/profile_update.py remove --item "<label>"` for each item this
  run wrote or found to be a duplicate. An item whose entry still carries an
  unresolved finding stays in the queue; say so in Phase 5.
- Output: PASS, or unresolved findings; the items removed.

## Phase 5 - Report

**Summarizing what changed and what is still waiting.**

- Input: outcomes, IDs written, review verdict, remaining items.
- Present, in plain English:
  - what was added, what was extended, what was a duplicate, and what the user
    retracted;
  - the items still waiting and why (narratives or positioning, thin content,
    unresolved finding, user deferral);
  - any pre-existing findings the run surfaced but did not fix;
  - unresolved review findings, if any.
- When new inventory entries were added, say plainly that applications evaluated
  before this run were scored against the older profile. Re-running them is the
  user's call; do not re-run anything.
- Output: the run summary.

## Phase routing on failure

Consumed by Phase 4. Route back, fix, re-run forward.

| Finding type | Route back to |
|---|---|
| Entry missing a required field, or fields out of order | Phase 3, Step 3e |
| Entry placed in the wrong role group or out of sort order | Phase 3, Step 3e |
| Axis value not in its registry | Phase 3, Step 3d |
| Dangling Role or Recognizes reference | Phase 3, Step 3e |
| Table of contents out of date | Phase 3, Step 3e (re-run insert; never hand-edit the ToC) |
| Item listed twice under one list category | Phase 3, Step 3e |
| Wording rule broken (first person, banned phrase, em dash, missing period) | Phase 3, Step 3d |
| Staging item missing a field | Re-stage it per `rules/profile/staging-writing.md` |
| Entry text overstates its staged item | Phase 3, Step 3d |
| Limit dropped | Phase 3, Step 3d |
| Content in the wrong field | Phase 3, Step 3c |
