# Interview-Prep Skill Notes

Design inputs for the interview-prep skill build, accumulated from the manual APP-008 phone-screen prep (2026-06-11), which is the worked specimen. Consolidate into the skill spec at build time. Tracking entry: `interview-prep-skill-build-notes` in `deferrals.md`.

## Skill Split

Two discrete skills, not one broad skill:
- **interview-prep-screen**: recruiter/phone-screen prep. Comparatively uniform format.
- **interview-prep-hire**: hiring-manager and later rounds. Owns all format variation (panel size, rounds, behavioral vs presentation) and gathers that variation at intake.

Both write into ONE shared artifact per application. The screen skill creates it; the hire skill appends new topic sections and deepens existing ones. Sections are added at population time, never pre-scaffolded blank. Shared input pipeline (application artifacts, positioning, narratives) must live in a common place, not duplicated across the two SKILL.md files.

## Artifact: `interview_prep.md`

One per application folder. Prep content only; no interview-event facts (type, round, schedule, duration, interviewers); those belong to a different skill.

Header is minimal YAML frontmatter:

```yaml
---
application: APP-008
company: Medable
role_title: Leader of Clinical Monitoring (Digital & AI Transformation)
created: 2026-06-11
last_updated: 2026-06-11
sources: [research.md, gap_analysis.md, positioning.md, cv_content.md, jd.md]
---
```

Body organization rules:
- Topic-first `##` sections with stable, concise heading names (deterministic access for a future dashboard; quick lookup live in an interview).
- Interview-type subsections only where content genuinely diverges (e.g., Questions to Ask > Recruiter Screen).
- Heading depth caps at `####` (content chunks and question entries alike). Inside a `####` entry, bold labels only, never level-5 headings.
- No half-page paragraphs anywhere: content renders as short `####` chunks with bullets, easily scannable mid-call.
- Anticipated-question answers are concise spoken-cue arcs (bulleted beats the user can speak naturally), NOT paragraphs to memorize. Exception: language whose exact wording is the point (e.g., the comp stated-range line) stays verbatim.
- Strengths lists lead each bullet with a short memorable key phrase, then supporting detail after it.
- Orientation chunk vocabulary (populate only what research supports; generalized 2026-06-11):
  - Company: Identity | Ownership and Financials | Strategy | Products and Pipeline | Business Model | Leadership | Culture Signals | Recent Events | Talking Points
  - Role: Mandate | Org Context | Accountability | Level
  - Industry: Market | Competitors | Trends and Disruption | Regulatory
- Products and Pipeline + Business Model must capture the company's value-positioning axis, whatever it is: platform/products for a software vendor, therapeutic areas and pipeline assets for biotech/pharma, service lines for a CRO, payer/provider segments for health services. The research subagent is explicitly tasked with "what does this company sell or position as its value, on its own axis," not just news and funding. Don't let one strategic story (e.g., an AI pivot) crowd out the installed-base offerings that pay the bills.
- Question entries use generic durable names ("Why did you leave / looking to leave?"), never application-specific ones. Each carries **Answer:** and **If probed:** layers (any diplomatic answer has a defense layer beneath it).
- Single-home rule: when a question's answer is fact-recall rather than personal narrative, the facts live in Orientation (Company gets a "Talking Points" chunk); the question entry stays narrative-only. No fact duplication across sections.

Section skeleton (screen skill's portion):

```markdown
## Orientation
### Company
### Role
### Industry

## Fit and Gaps
### Strengths to Lead With
### Gaps They May Screen For

## Questions
### Anticipated Questions
#### Walk me through your background
#### Why this company?
#### Why did you leave / looking to leave?
#### Other Anticipated Questions
### Questions to Ask
#### Recruiter Screen

## Compensation

## Logistics and Availability
```

Rationale notes: Orientation is full (Company/Role/Industry), not a glance-card, because screens can run at near-hiring-manager intensity. Fit and Gaps exists because recruiters screen against the must-have checklist for disqualifiers; each gap gets response language. Section order follows how a screen call actually flows.

## Research Ledger Pattern

`research.md` is the application's single research ledger, not just role-intake's output. Downstream skills append dated sections attributed to the producing activity (e.g., "**Added:** 2026-06-11 (interview prep, phone screen)") with Summary / Key facts / Sources shape. Prep artifacts cite the ledger rather than embedding research. Per-claim confidence hedges are carried into both the ledger and the user-facing relay.

## Research-Gap Procedure

Worked once on APP-008; reproduce at build time:

1. Evaluate existing research by PURPOSE-FIT against the prep task's information needs, never by artifact age. role-intake research carries over the strategic narrative; it was scoped for pursue/pass decisions, not live-conversation performance.
2. Enumerate the purpose-fit gaps up front, state the count, then present ONE gap per turn: what it is, why the screen needs it, expected confidence, and an honest value ranking. The user approves or skips each research run individually.
3. Each closed gap is appended to research.md immediately as a dated ledger section, then relayed to the user with hedges intact.
4. User-supplied data (target/floor comp numbers, their own interviewer lookup) folds into the same content rather than living separately. User decisions that become artifact content (e.g., stated-range language) are drafted back concretely for approval before entering the artifact.
5. Research execution should run as a research subagent that returns findings to the main skill before anything is written to file.

Phone-screen gap checklist that generalizes across applications:
- **Compensation calibration**: market percentiles for the inferred level; company-reported salaries; equity-risk posture (private/VC-backed caveats); posted-range and pay-transparency check. When the role's level is itself inferred (e.g., VP read from scope signals), calibrate against the conservative level too and say so.
- **Interview-process intel**: candidate-reported screen content, round structure, timeline. Carry sample-size and recency caveats.
- **JD internal-reference decode**: company shorthand the JD uses (e.g., Medable's "1:1:1" = one-day study start, one-day recruitment, one-year study conduct). If not publicly decodable, it converts to a prepared question to ask.
- **Interviewer context**: internal vs contract/embedded recruiter, which determines which questions they can answer authoritatively and which to hold for later rounds.

## Session Log Convention

Stage-scoped sections, created when the stage begins (never pre-scaffolded): `## Interview: Screen`, `## Interview: Hiring Manager`. Each holds prep date, prep-artifact pointer, research sections added, interview date(s)/duration/interviewer, and an outcome line (pending until known). Multiple hiring-manager rounds are dated line items within the one section. Maps 1:1 to the two skills; downstream consumers (interview follow-up, close-application) read a stage as one unit.

## Profile Inputs and Confirmation

- Conditional facts (availability, travel, modality, comp posture) are NOT static. Profile docs hold dated defaults (e.g., user-info.md "Remote preferred, open for the right role (as of 2026-06)"); truly static facts (citizenship) live there undated.
- Confirm-not-trust rule (user directive 2026-06-11): every element the skill pulls from another artifact or profile default and presents as current (logistics, comp target/floor, defense-layer language) must be SHOWN to the user with an "is this still accurate?" confirmation before it enters the artifact. Never silently reuse.
- Role-customized answers ("what are you looking for") are drafted per-role from positioning + role context, never generic. Anti-generic guard, user's words: a generic or other-role-shaped answer reads as "this guy is really looking for something else and is settling for this."
- Per-job answers memorialize in each application's interview_prep.md; positioning holds general truth only. Newly surfaced GENERAL facts route through the staging file (profile_updates_pending.md) for deliberate integration; nothing writes to positioning silently.
- Why-leave defense layer now lives in positioning.md ("The layer beneath"); resolved 2026-06-11.

## Gap-Analysis Input Contract (folded into this build)

- gap-analysis gains a logistics-constraints confirmation step (modality, travel, availability, comp floor vs posted range), checked against user-info.md dated defaults, feeding the existing `## Eligibility Flags` section of gap_analysis.md. Rationale: hard constraints are pursue/pass inputs; prep time is too late.
- preparation-screen reads constraints from gap_analysis.md when present, confirms currency with the user, and asks fresh only when absent (every pre-change application, e.g. APP-008, lacks them).

## Open Items

- Downstream consumers to design for: the interview itself (live reference), interview follow-up skill, future dashboard reading frontmatter + stable headings.
