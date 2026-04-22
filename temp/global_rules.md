# Global Rules

Shared rules that govern all skills in this workflow. Every skill loads this file at execution start before taking any other action.

---

## Skill Adherence

Follow the active skill exactly. Explicit user approval is required before deviating from any instructions, or applying judgement or inference.
When in a phase, complete only steps from that phase. Do not perform steps or volunteer analysis from future phases.

---

## Pacing: One Item Per Exchange

Items, concepts, framing, requests for input, requests for sign-off or agrerement, etc will be presented to the user one item at a time for the user to review and / or approve.  Do not bundle multiple input-requiring items. Do no proceed to subsequent items without approval or an explicit response to do so.  Silent non-response is not approval.

---

## Application Unique ID (APP-NNN)

Every role evaluation is assigned a unique application ID in the form `APP-NNN`, where NNN is zero-padded to three digits minimum and widens past 999 naturally. The `APP-` prefix keeps the ID string-stable across tools that coerce numeric-looking strings to integers (e.g., Smartsheet).

Assignment procedure:
1. Scan `personal/sessions/` for files matching `*_SessionLog.md`.
2. Extract the numeric portion from each filename's `APP-NNN` token.
3. Find the maximum and increment by 1. Zero-pad to three digits minimum.
4. If no matching SessionLog files exist, start at `APP-001`.

The ID is assigned at the start of `role_evaluation` Phase 1a, held in working memory until Phase 1c close, then recorded when the SessionLog file is created. It carries forward into application and do_not_pursue folder names and any downstream artifacts for that application.

---

## Workflow Context Check

Before performing any skill directives, determine whether this is a fresh invocation or a continuation of a prior session or parent workflow.

- **Fresh invocation:** proceed to Phase 1a (or the equivalent session setup phase for this skill).
- **Triggered from within another skill** (e.g., `source_document_update_workflow` triggered by `cv_targeted`): confirm the parent session context is available. The calling skill should have defined the scope of "this session." If that scope is not present in context, flag the gap before proceeding — do not infer what the session covered.
- **Resuming a prior session:** if the active skill has a Session Continuity rule, that rule governs resumption. If no Session Continuity rule is defined, start from Phase 1a

---

## Document Load Instructions

Document load instructions apply at any point in the active skill.

This is a just-in-time loading workflow. Load documents at the phase and step specified in the active skill — not earlier or later.

A document is loaded completely when all content is present with identifiable structure. A document returning only fragments without structure must be flagged as a load failure regardless.

If any document fails loading, do not proceed using partial content:
- Run bash with `cat [filepath]` for each failed document
- Confirm the full document content is readable before proceeding
- If the bash fallback also fails, report the specific file and error — do NOT proceed until resolved

NEVER silently proceed with degraded source material.

---

## QC Failure Recovery

If a QC phase identifies that a step was incomplete, non-compliant, or that output does not conform to skill instructions, do not proceed. State the specific failure clearly, identify which step or output is affected, and present the user with options: (a) return to the prior phase and re-run the failed step, (b) accept the gap with explicit acknowledgment and proceed, or (c) stop the session. Do not invent a resolution or silently continue. Wait for explicit user direction before taking any action.

---

## Standard QC Document Verification

If any documents were loaded in a previous phase, verify the documents were completely loaded, state the load verification status (pass/fail/fallback used), and specify the structural element confirmed. All documents must pass verification before proceeding.

---

## Phases:

### Action Phase

Does the substantive work: loads documents, derives, records, gathers input where required.

- Silent execution. No drafts, narration, or summaries produced during the phase.
- User input-gathering is permitted when the activity genuinely requires information only the user holds. This is distinct from presenting completed work back for review, which belongs in presentation
phases.
- Work products are recorded and held for presentation phases to surface.

---

## Action Phase Closing

Applies to all action phases listed in the active skill.

At the close of an action phase:
- Produce the closing output in the format specified by the active skill for this phase. Do not list internal steps; silent execution applies through close unless specicifed otherwise in that phase.
- Append to the session log per the active skill's session continuity rule (if the sesssion log has been created).

---

### QC Phase

Runs checks against the preceding action phase's work products.

- Checks run internally.
- Failures are routed through QC Failure Recovery.

---

  ## QC Phase Closing

Applies to all QC phases.

At the close of a QC phase:
- Output to user in one of the following formats:
  - List all checks performed concisely in single line bullets.
  - On pass: single line reading `Phase [N]b QC: pass.`
  - On fail: one line per failed check, in the form `Phase [N]b QC fail: <check name>. Resolution: <applied resolution | awaiting user decision>.`
- Do not list checks that passed.
- Obtain explicit user approval before proceeding to the next phase.
- Append to the session log per the active skill's session continuity rule, in the form `Phase [N]b complete, YYYY-MM-DD. QC outcome: <pass | fail; brief resolution>.`

---

### Presentation Phase

Surfaces completed work products to the user for agreement, correction, or rejection.

- One item per exchange. Each item is presented, the user responds explicitly, then the next item.
- Silent non-response is not approval.
- No new substantive work is performed in a presentation phase.

---

## Presentation Phase Closing

Applies to presentation phases.

At the close of a presentation phase:
- Verify every presented item has a recorded user response (agreement, correction, or rejection). If any item does not, return to that item before closing.
- Verify any deliverables specified by the active skill for this phase (file writes, session log appends) have been completed.
- Obtain explicit user approval before proceeding to the next phase.
- Append to the session log per the active skill's session continuity rule.

Other places in the repo that reference "Standard Phase Closing" by name will need to be updated to "Action Phase Closing" or "Presentation Phase Closing" depending on which phase type they close. The
cleanest way to find them is a repo-wide grep for the old phrase.

---

### Transition Phase

Hands off control to another skill or to application next steps. Coordinates the move; does not produce new work.

Applies to transition phases in the active skill.

  At the close of each transition phase:
  - Confirm the handoff target has completed, or the flow has ended.
  - Perform any session cleanup specified by the skill (e.g., delete session logs).
  - State that the skill is complete.




