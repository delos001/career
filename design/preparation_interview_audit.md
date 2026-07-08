# preparation-interview audit — open findings

Audit run 2026-07-08. Scope: the preparation-interview skill and everything it
touches (SKILL.md, templates/interview_prep.md, rules/interview-types/,
prep_interview_qc.py, interview_lifecycle.py, qc-preparation-interview,
and the shared session_log / follow-up / close-application seams).

Two findings are already resolved and are recorded in design_decisions.md
(2026-07-08, "Scheduling metadata has one home"):
- the lifecycle op vs QC X3 collision, and
- scheduling metadata moved to discrete session-log fields.

What follows is the REMAINDER, not yet actioned. Each was verified against the
files on the date above. Re-verify before acting; the code may have moved.
Ranked most to least concrete. Not yet walked one-by-one with the user, so each
still needs a decision, not just a fix.

---

## F2. SKILL.md Phase 5 describes QC checks the script does not run

`.claude/skills/preparation-interview/SKILL.md` Phase 5 (around line 161) says
`prep_interview_qc.py` checks: "cross-ref integrity across Concerns / Question
Bank / Appendix, citation IDs, no Appendix<->main-body duplication, core-section
length with Appendix exempt, format".

Verified against the script. What it ACTUALLY checks: Q-label cross-ref only
(X2), not Concerns cross-ref. It does NOT validate citation IDs resolve to real
inventory entries. It does NOT check Appendix-vs-main-body duplication. There is
NO length check anywhere in the file (grepped; confirmed absent).

So the SKILL over-promises four checks. Two ways to close it, user's call:
(a) trim the SKILL text to what the script does, or
(b) build the missing checks (at least core-section length looks intended and
    was referenced by design_decisions' 2026-07-07 "core-section length with
    Appendix exempt" line, so it may be a dropped feature, not just bad copy).
Lean (a) for the ones that were never real, and decide (b) only for length.

## F3. Stale "QC not finalized yet" hedge

Same Phase 5, ~line 163: "QC is finalized once the doc + skill are stable; run
the available checks until then." QC is finalized: design_decisions records it
validated end-to-end, COMPONENTS lists both QC components as Built. The hedge is
stale and tells the operator to run a partial pass. Remove it; state the QC step
plainly (run the script, dispatch the judgment agent, cap 3 iterations).

## F4. Points users to a "presentation skill" that does not exist

The SKILL description, the SKILL body (~line 14), Phase 4 (~line 138), the
template (Appendix block, "build via the separate presentation skill"), and all
three rules/interview-types files reference a separate presentation skill.
`.claude/skills/` has no presentation skill. It is a KNOWN deferral
(design_decisions refs `presentation-build-skill` as deferred), so this is not a
bug, but the skill currently hands the user a dead pointer when an interview has
a presentation format. Decide: soften the language to "presentation deliverable
(skill not yet built; prepare manually)" until the skill exists, or build it.
Check design/deferrals.md for the presentation deferral's current state first.

## F5. Two prep skills hand-write the session-log section shape in prose

Lower priority; partly mitigated by the 2026-07-08 change. The interview-section
FIELD SET is now single-authored in templates/session_log.md and read by the QC
scripts. But preparation-screen and preparation-interview SKILLs still instruct
the operator to write the section by pointing at the template rather than
handing a script the field values. Follow-up and close-application also edit it
by hand. This is the same drift risk the field-set change reduced but did not
eliminate: an operator can still write a malformed section that only QC catches.
Consider a small session_log.py helper that writes/updates an interview section
from field values (like the existing append-section op), so no skill hand-builds
the block. Evaluate whether it earns its keep before building.

---

## Notes / not-yet-findings (need more work before they are real)

- The audit was stopped after the scheduling-metadata work. The findings above
  are the ones reached and verified. A full pass was NOT completed; F5-adjacent
  seams (follow-up's reconcile step, close-application Phase 2b) are freshly
  written 2026-07-08 and have not themselves been audited or run end-to-end.
- Verify the follow-up "reconcile the date every run" instruction and the new
  close-application Phase 2b actually behave as written the first time each skill
  runs for real; they were specified this session but not exercised.
