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

## Trigger

Design when an application advances to a hiring-manager round (APP-008 is the
live candidate). Tracking entry: `interview-prep-skill-build-notes` in
`deferrals.md`.
