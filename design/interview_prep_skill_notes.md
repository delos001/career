# Interview-Prep Skill Notes: preparation-interview Design Inputs

The preparation-screen skill shipped 2026-06-11; its conventions now live in
their durable homes and are NOT restated here (single source):
- Artifact structure and body rules: `templates/interview_prep.md` (literal
  headings = required set; comments carry the drafting rules).
- Procedure, interaction contract, confirm-not-trust, research routing:
  `.claude/skills/preparation-screen/SKILL.md`.
- Architecture and rationale: `preparation-screen-architecture-2026-06` in
  `design/design_decisions.md`.

What remains here is the design input for the future **preparation-interview**
skill (hiring-manager and later rounds). Worked specimen for the family:
`personal/applications/medable_APP-008_2026-06/`.

## preparation-interview scope

- Owns ALL interview-format variation: panel size and composition, number of
  rounds, behavioral vs presentation vs case formats. Gathers the format at
  intake before drafting anything.
- Appends to the SAME per-application `interview_prep.md` that
  preparation-screen created (one artifact per application). Adds its own
  topic sections at population time (e.g., story bank, panel strategy,
  presentation plan) and deepens existing ones (Anticipated Questions; adds a
  `Questions to Ask > Hiring Manager` sibling under the existing divergence
  rule). Never pre-scaffolds blank sections.
- Reuses the screen skill's machinery: prep-research subagent (add targets as
  needed, e.g., panel-member bios), prep_qc.py (template additions extend the
  required set), qc-preparation-screen or a sibling judgment agent, the
  research-ledger pattern, and the confirm-not-trust rule.
- Session log: its own stage section `## Interview: Hiring Manager`, created
  when the stage begins; multiple rounds are dated line items within it.
- Questions held back from the recruiter screen (org design, reporting line,
  function newness) route here; read the screen's Questions to Ask notes.
- Probable research depth difference: deep product/strategy fluency and
  panel-member context, per the screen skill's process-intel finding that
  director-and-above rounds probe strategy, business impact, and innovation.

## Positioning-to-requirements routing (enhancement)

Applies to preparation-screen now; preparation-interview inherits at build.
Origin: APP-008 review (2026-06-12). The prep drafted the background arc and
strengths from inventory chronology while positioning.md, already a declared
skill input, was only routed to "why leave" and "what are you looking for."

Decisions:
- No new agent, no new artifact. positioning.md (~180 lines) is already read
  in the main session; the retrieval manifest already scores Signature Themes
  against the role's critical requirements. The fix is Phase 3 drafting-rule
  routing plus template comments.
- Strengths consume the retrieval manifest's theme-score table via a targeted
  read of that table only, never the whole manifest.
- Output format unchanged: short spoken-cue bullets, thesis-first. Positioning
  prose is compressed to cue level, never imported verbatim.

Routing map (positioning.md section -> prep entry):

| Section | Routes to |
|---|---|
| Positioning Statement, What Makes Me Unique, Elevator Statement | "Walk me through your background": open with the identity thesis, compress chronology to one sweep beat, land on the role |
| Experience Profile | Selector for the arc: pick the 1-2 role profiles the role maps to; that chooses which thesis the arc opens with |
| Signature Themes (via retrieval theme-score table) | Strengths to Lead With: top-scored themes contribute core message + proof point, mapped to the CRs they hit |
| Core Philosophy | "Leadership style" / "how would you approach this role" entries (add when format warrants); flex line (formal authority / matrix / hands-on) is the defense layer for direct-reports probes |
| Industry Trajectory and Where I Fit | "Why this company" and industry-outlook beats, matched to the company's strategic thesis |
| Why I Chose to Leave (+ layer beneath) | Already routed: "why did you leave" |

## Trigger

Design when an application advances to a hiring-manager round (APP-008 is the
live candidate). Tracking entry: `interview-prep-skill-build-notes` in
`deferrals.md`.
