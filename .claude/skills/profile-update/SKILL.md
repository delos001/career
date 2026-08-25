---
name: profile-update
description: Promote staged profile updates into the profile documents. Reads the PU-NNN entries in personal/profile/profile_updates_pending.md, walks them with the user one at a time, and writes each into inventory.md as a new entry or as an enrichment of an existing one, then closes the staging entry with an audit line naming where the content landed. Runs standalone at any time, or inline at the end of a gap-analysis run. This is the only skill that writes to the profile documents.
---

# profile-update - promote staged updates into the profile

Writes the `PU-NNN` captures in `personal/profile/profile_updates_pending.md`
into the profile documents, one entry at a time, and closes each capture with
an audit line naming the profile IDs that now carry it. Until a capture is
promoted, the fact is invisible to retrieval, gap analysis, and CV creation.

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
  the capture is an instruction to this skill, not commentary. Write nothing the
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

This skill has no artifact to probe, so resume state lives in the staging file
itself: an entry marked `processed` is done and is never reprocessed. Run
`python scripts/profile_update.py pending` and continue from what it returns.

## Phase 0 - Intro

**Introducing the profile-update skill.**

- Input: invocation.
- Run `python scripts/display/introduce.py profile-update` and show the output.
- Output: user oriented.

## Phase 1 - Load the work list

**Reading what is staged and waiting.**

- Input: invocation.
- Run `python scripts/profile_update.py pending`. Each line carries the
  `PU-NNN`, the capture date, the label, and the source application.
- Do NOT read the staging file into context. Phase 3 pulls one entry at a time
  with `show`.
- Report the count in plain English. Name how far back the oldest capture goes,
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
  A capture routinely bundles several distinct items into one sentence. Split
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
  - **No change** - the substance is already carried accurately. This is a
    valid outcome and still closes the staging entry.
  State the reasoning in one or two lines. Do not survey the alternatives.
- **Step 3d - Show the actual text.** Present the full proposed entry, or a
  before/after for an enrichment, inline in the response. Never describe an
  edit the user has to look up to evaluate, per [[feedback_concrete_proposals]]
  and [[feedback_show_qc_edits_before_after]]. Wait for approval. Apply any
  correction and re-show before writing.
- **Step 3e - Write it.**
  - New inventory entry: write the block WITHOUT its `ID:` line to
    `temp/pu_block.md`, then run
    `python scripts/profile_update.py insert --prefix <PREFIX> --block-file temp/pu_block.md`
    (add `--subsection "<heading>"` for a section that has sub-sections). The
    script assigns the ID, places the entry in sorted position, and rebuilds the
    table of contents. Capture the ID it prints.
  - Enrichment of an inventory entry: write the approved value to
    `temp/pu_value.md`, then run
    `python scripts/profile_update.py set --id <ID> --field <Field> --value-file temp/pu_value.md`,
    once per field changed. Open the value with a newline for a multi-line
    field such as `Coursework`. Never hand-edit `inventory.md`.
  - Enrichment of a narrative or positioning entry: apply with Edit against
    `narratives.md` or `positioning.md`. Those documents have no
    structure-authority template to validate against yet.
  - **Creating a new narrative or positioning entry is out of scope.** Those
    documents have no structure-authority template yet. Leave the entry pending,
    tell the user plainly that it needs the narratives or positioning builder,
    and move on.
- **Step 3f - Close the staging entry.** Run
  `python scripts/profile_update.py close --pu PU-NNN --targets <IDs> --date YYYY-MM-DD`,
  passing every ID the content landed in, or `--targets "no change"`. This flips
  the status and writes the audit line from the surfaced fact to the profile IDs
  that now carry it.
- Output: per entry, the disposition, the target IDs, and a closed staging entry.

## Phase 4 - QC

**Checking the profile documents and the staging bookkeeping.**

- Input: the IDs written this run and the `PU-NNN` closed this run.
- **Step 4a - Mechanical checks (script).** Run
  `python scripts/profile_update_qc.py check`, passing `--scope-id` once per
  inventory ID created or edited this run and `--processed-pu` once per staging
  entry closed. The script owns document structure, field rosters, ID integrity,
  entry placement, reference resolution, axis values, the table of contents,
  empty-section markers, and staging bookkeeping. Findings on entries this run
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
  - what was added, what was enriched, what was recorded as no change;
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
| Staging entry not closed, or closed with an unresolvable target | Phase 3, Step 3f |
| Entry text overstates its staged Content | Phase 3, Step 3d |
| Framing guard or hedge dropped | Phase 3, Step 3d |
