---
name: profile-update
description: Promote staged profile updates into the profile documents. Reads the PU-NNN entries in personal/profile/profile_updates_pending.md, walks them with the user one at a time, and writes each into inventory.md as a new entry, as an enrichment of an existing one, or as an item on a list section, then closes that PU-NNN off the staging queue and records where its content landed. The queue holds what is waiting; the inventory is where the information persists and the migrated record is what keeps the PU-NNN traceable afterwards. Runs standalone at any time, or inline at the end of a gap-analysis run. This is the only skill that writes to the profile documents.
---

# profile-update - promote staged updates into the profile

Writes the `PU-NNN` entries in `personal/profile/profile_updates_pending.md`
into the profile documents, one entry at a time, then takes each one off the
queue. Until a `PU-NNN` is promoted, the fact is invisible to retrieval, gap
analysis, and CV creation.

The file's `## Entries` section is a **queue**. A `PU-NNN` entry waits in it and then
leaves; the inventory is where the information persists. What stays behind is
one line under `## Migrated` recording that entry's number and what became of
it, because the number outlives the entry: it is what the next `PU-NNN` is
counted from, and what a past application's `Closure ref:` points at.

**This skill is the only writer to `inventory.md`.** Every other skill reads.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Phases run in order; each has a declared input and output.
- Each phase opens with the **bold lead line** under its heading. Speak it
  verbatim before running the phase.
- **One entry at a time, always.** Phase 3 walks a single `PU-NNN` from
  proposal through write and close before naming the next one. Batching the
  proposals is a failure even when the entries look identical, and the batch
  step of any other skill does not override this.
- **The staged Content field is the source, and its limits are binding.**
  Several entries carry explicit framing guards ("frame as review and SME input,
  not authoring ownership"; "do not derive a multiplier such as 8x"). A guard in
  the staged entry is an instruction to this skill, not commentary. Write nothing the
  Content field does not support, and carry every hedge forward.
- **Never write a fact the user has not attested.** Per
  [[feedback_no_fabricated_facts]]. When the staged content is too thin to
  write an honest entry, ask the user for what is missing; if it does not
  arrive, leave the entry pending rather than filling the gap with inference.
- Script failures halt the phase per global rules.
- Run-scratch goes in `temp/`; this skill has no application folder.

## Mode

Ask at intake, or take the mode from the caller:

- **adhoc** - user-invoked. Phase 2 offers the full pending list.
- **inline** - invoked from gap-analysis Phase 8. Phase 2 defaults to the
  entries that run just staged, and offers the rest of the backlog once those
  are done.

## Resume check - run before Phase 0

This skill has no artifact to probe, so resume state is the staging file itself.
It is a queue: a `PU-NNN` is in it because it is waiting, and it leaves once
its content is in the profile. Run `python scripts/profile_update.py pending`
and continue from what it returns.

## Phase 0 - Intro

**Introducing the profile-update skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py profile-update` and show the output.
- Output: user oriented.

## Phase 1 - Load the work list

**Reading what is staged and waiting.**

- Input: invocation.
- Run `python scripts/profile_update.py pending`. Each line carries the
  `PU-NNN`, the date it was staged, the label, and the source application.
- Do NOT read the staging file into context. Phase 3 pulls one entry at a time
  with `show`.
- Report the count in plain English. Name how far back the oldest one goes,
  since a long backlog means the profile has been under-representing the
  candidate across every application run in that window.
- Output: the pending list.

## Phase 2 - Scope the run

**Agreeing which entries this run will process.**

- Input: the pending list.
- Present the list and ask which entries to process: all of them, a named
  subset, or the oldest N. In **inline** mode, default to the entries the
  gap-analysis run just staged and say so.
- A long backlog is high-volume homogeneous work. When more than ten entries
  are pending, offer the three options before starting: process strictly one at
  a time, process in clusters the user approves per cluster, or stop after a
  named subset.
- Output: the ordered list of `PU-NNN` this run will walk.

## Phase 3 - Per-entry disposition loop

**Walking each staged entry into the profile, one at a time.**

Repeat every step below for one `PU-NNN` before naming the next.

- **Step 3a - Read the entry.** Run
  `python scripts/profile_update.py show --pu PU-NNN`. Read the Content field
  and note every framing guard, hedge, and suggested action it carries.
  A staged entry routinely bundles several distinct items into one sentence. Split
  them out and show the user the list before working any of them. They cannot
  judge the third item if they were never told there was a third.
- **Step 3b - Check what already exists.** The Content field often names the
  entries it relates to. Pull them with
  `python scripts/profile_slice.py id EX-NNN ...`. When it names none, search
  the inventory for the same substance before concluding nothing covers it, per
  [[feedback_comprehensive_coverage_scan]]. Paste the full text of every entry
  you name. Never cite an entry by ID alone and never summarize one the user is
  being asked to compare against, per [[feedback_concrete_proposals]]; a summary
  makes them go find it themselves.
- **Step 3c - Propose one disposition.** Exactly one of:
  - **New entry** - the substance is not represented anywhere. Name the entry
    type and the role it belongs to.
  - **Enrichment** - an existing entry covers the substance but under-states or
    mis-frames it. Name the entry.
  - **List item** - the substance is a named tool, platform, or exposure item
    rather than a piece of work. Name the list address it belongs under.
  - **Duplicate** - the substance is already carried accurately, so nothing
    needs writing. This is a valid outcome and still takes the `PU-NNN` off the
    queue.
  - **Retract** - the substance should not go into the profile after all.
    Staging holds facts the user already judged to belong there, so this is
    the user's call and never the skill's. Surface the doubt, take the
    decision from them, and do not propose it as a way to clear a backlog.
  State the reasoning in one or two lines. Do not survey the alternatives.
- **Step 3d - Show the actual text.** Present the full proposed entry, or a
  before/after for an enrichment, inline in the response. Never describe an
  edit the user has to look up to evaluate, per [[feedback_concrete_proposals]]
  and [[feedback_show_qc_edits_before_after]]. Wait for approval. Apply any
  correction and re-show before writing.
- **Step 3e - Write it.** Every command below takes `--pu PU-NNN` and records
  what it changed on that `PU-NNN` entry. Step 3f closes the entry from those
  records, so there is no target list to keep track of and none to type.
  - New inventory entry: write the block WITHOUT its `ID:` line to
    `temp/pu_block.md`, then run
    `python scripts/profile_update.py insert --prefix <PREFIX> --pu PU-NNN --block-file temp/pu_block.md`
    (add `--subsection "<heading>"` for a section that has sub-sections). The
    script assigns the ID, places the entry in sorted position, and rebuilds the
    table of contents.
  - Enrichment of an inventory entry: write the approved value to
    `temp/pu_value.md`, then run
    `python scripts/profile_update.py set --id <ID> --pu PU-NNN --field <Field> --value-file temp/pu_value.md`,
    once per field changed. Open the value with a newline for a multi-line
    field such as `Coursework`. Never hand-edit `inventory.md`.
  - A tool, platform, or exposure item: some sections hold flat lists rather
    than entries, so they carry no ID for `insert` to assign or `set` to
    resolve. Run
    `python scripts/profile_update.py list-add --pu PU-NNN --target "<Section> / <Category> / <Label>" --item "<item>"`,
    once per item. Drop the ` / <Label>` part only when the category holds a
    single line; a wrong or missing part is answered with the valid choices.
    The command appends and never rewrites, so nothing already listed can be
    lost, and it refuses an item that is already there.
  - Enrichment of a narrative entry: apply with Edit against `narratives.md`,
    which has no structure-authority template to validate against yet, then run
    `python scripts/profile_update.py record --pu PU-NNN --target <ID>` so the
    hand edit is recorded like any other write. The ID must be a real `ST-NNN`
    or `DC-NNN`; the command checks.
  - **Creating a new narrative entry is out of scope.** That document has no
    structure-authority template yet. Leave the entry in the queue, tell the
    user plainly that it needs the narratives builder, and move on.
  - **`positioning.md` is never written by this skill**, neither a new entry nor
    an enrichment. Positioning is abstract framing content, and deciding what
    belongs there is a judgment the user drives with the model assisting, not a
    write a skill run performs. When a `PU-NNN`'s substance belongs in
    positioning, say so plainly, leave the entry in the queue, and move on; it
    waits there until the user handles it. Per
    `positioning-content-is-hand-driven-2026-08-26`.
- **Step 3f - Close the entry.** Run
  `python scripts/profile_update.py close --pu PU-NNN`. The command reads what
  Step 3e recorded, re-verifies each target still resolves, removes the
  `PU-NNN` entry from the queue, and writes `PU-NNN: <targets>` under
  `## Migrated`. It refuses an entry that recorded no writes, which is what
  catches a write that failed or was skipped.
  A **duplicate** takes `--duplicate` instead, and is refused if the entry
  recorded any writes.
  A **retracted** entry is dropped instead: run
  `python scripts/profile_update.py drop --pu PU-NNN`, which records
  `PU-NNN: dropped` and prints the block it removed. Retraction is the user's
  call and never the skill's; confirm it with them before running it.
  Never hand-edit either section. The commands keep the removal and the
  migrated line together, and a `PU-NNN` that loses its body without gaining its
  line takes its number out of circulation - the next one staged is then issued
  a number an old application already cites.
- Output: per entry, the disposition, the targets, and a closed `PU-NNN`.

## Phase 4 - QC

**Checking the profile documents and the staging bookkeeping.**

- Input: the IDs written this run and the `PU-NNN` closed this run.
- **Step 4a - Mechanical checks (script).** Run
  `python scripts/profile_update_qc.py check`, passing `--scope-id` once per
  inventory ID created or edited this run and per list address appended to, and
  `--processed-pu` once per staging entry closed. The script owns document
  structure, field rosters, ID integrity, entry placement, reference resolution,
  axis values, the table of contents, empty-section markers, list-section
  content, and staging bookkeeping including the migrated record. Findings on
  entries this run
  did not touch are reported as pre-existing advisories and do not fail the run;
  surface them to the user at Phase 5 rather than fixing them here.
  On FAIL: translate to plain English, fix, re-run.
- **Step 4b - Judgment checks (subagent).** Only after Step 4a passes, dispatch
  `qc-profile-update` with the staging IDs and the target IDs. It verifies what
  a script cannot: that each written entry is supported by its staged Content,
  that framing guards and hedges survived, and that the writing matches the
  document's voice. Loops on findings.
- Cap the loop at **3 iterations** across both steps. If findings remain, carry
  them into Phase 5 so the user sees them rather than stalling the run, per
  [[feedback_artifact_qc_internal]].
- Output: PASS, or unresolved findings.

## Phase 5 - Report

**Summarizing what changed and what is still waiting.**

- Input: dispositions, target IDs, QC verdict, remaining pending entries.
- Present, in plain English:
  - what was added, what was enriched, what was recorded as a duplicate, and
    what the user retracted;
  - the entries still pending and why (out-of-scope target, thin content,
    user deferral);
  - any pre-existing QC advisories the run surfaced but did not fix;
  - unresolved QC findings, if any.
- When new inventory entries were added, say plainly that applications
  evaluated before this run were scored against the older profile. Re-running
  them is the user's call; do not re-run anything.
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
| PU-NNN still in the queue after its content was written | Phase 3, Step 3f |
| PU-NNN gone from the queue with no `## Migrated` line, or a migrated line naming a target that does not exist | Phase 3, Step 3f |
| Entry text overstates its staged Content | Phase 3, Step 3d |
| Framing guard or hedge dropped | Phase 3, Step 3d |
