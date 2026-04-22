# Skills Registry

Used by `skills/control.md` to understand the available skill suite, route users to the correct skill, and assess current workflow state. When a skill is added, renamed, or its dependencies change, update this file — the control skill reads from here and should not require changes for routine skill updates.

---

## Workflow Sequence Overview

The typical end-to-end path from a standing start to interview follow-up:

```
[Bootstrap]
experience_inventory_bootstrap → career_narratives_builder → positioning_builder
                                                                      ↓
[Per Role]                                              role_evaluation
                                                       ↙              ↘
                                               cv_targeted       interview_prep
                                                                       ↓
                                                              interview_capture
                                                                       ↓
                                                             interview_followup

[Standalone — any point]
career_brief, cv_general, source_document_update_adhoc
```

Knowledge builder skills (experience_inventory_bootstrap, career_narratives_builder, positioning_builder) run once and are maintained over time. Role-specific skills (role_evaluation through interview_followup) run per application. Utility and standalone skills run on demand. Rules builder skills (archetype_creation, domain_creation) extend the repo itself — invoked only when the available archetype or domain coverage does not fit a target role; not part of per-role workflow.

---

## State Detection Guide

The control skill uses the following ordered checks to determine where a user is in the workflow. Check in order — the first failing condition identifies the gap.

1. **Knowledge base complete?**
   Check: `personal/knowledge/Experience_Inventory.md`, `personal/knowledge/Career_Narratives.md`, `personal/knowledge/Positioning.md` all exist with populated content.
   If no: route to the appropriate knowledge builder skill(s).

   1a. **Active Domain declared?**
   Check: `personal/knowledge/Experience_Inventory.md` header contains a populated `**Active Domain:** <slug>` line, and `<slug>` matches a registered domain in `rules/registry_domain.md`.
   If missing: instruct the user to add the pointer before proceeding. Downstream skills (`role_evaluation` Phase 2a, `cv_targeted` Phase 1a/2a, `cv_general` Phase 2a, `interview_prep` Phase 1a) load the active domain file by this pointer and will halt without it.
   If present but unregistered: flag the mismatch. Either the pointer is wrong (correct it) or the referenced domain file has not been built yet (route to `domain_creation`).

2. **Role target identified?**
   Check: User has provided or referenced a company name and role title.
   If no: ask the user what role or context they are working toward before proceeding.

3. **Role evaluation complete?**
   Check: `personal/sessions/[Company]_[Role]_[YYYY-MM]_GapAnalysis.md` exists for the target role.
   If no: route to `role_evaluation`.

4. **CV generated?**
   Check: A CV file matching `outputs/*CV*[Company]*[Role]*.docx` exists for the target role.
   If no: `cv_targeted` is available. Ask if the user wants to generate the CV.

5. **Interview prep complete?**
   Check: `InterviewPrep_[Company]_[Role]_[YYYY-MM].md`, `InterviewCompletion_[Company]_[Role]_[YYYY-MM].md`, and `InterviewScratch_[Company]_[Role]_[YYYY-MM].md` all exist in the user's application folder.
   If no: `interview_prep` is available if an interview is scheduled or approaching.

6. **Interview round captured?**
   Check: At least one round in `InterviewCompletion_[Company]_[Role]_[YYYY-MM].md` is populated (Interviewers and Questions and Responses sections contain captured content beyond hint-text HTML comments).
   If no and a round has been completed: `interview_capture` is available.
   If yes: `interview_followup` is available for any captured round.

---

## Skill Entries

---

### Experience Inventory Bootstrap

**File:** `skills/experience_inventory_bootstrap.md`
**Category:** Bootstrap
**Standalone:** Yes — no prior skills required

**Trigger:** User is starting from scratch with no structured experience documentation; has raw CVs, resumes, or career history documents and wants to build the Experience Inventory for the first time; `personal/knowledge/Experience_Inventory.md` does not exist or is empty.

**Prerequisites:**
- Raw career source documents provided by the user (old CVs, resumes, or equivalent)

**Completion Signal:** `personal/knowledge/Experience_Inventory.md` exists with populated role entries and tag annotations.

**Outputs:**
- `personal/knowledge/Experience_Inventory.md`

**Typical Next Steps:** `career_narratives_builder`, `positioning_builder`

---

### Career Narratives Builder

**File:** `skills/career_narratives_builder.md`
**Category:** Knowledge Builder
**Standalone:** Yes — can run independently, but Experience Inventory should exist first for best results

**Trigger:** User wants to build or update their stories and decisions library; preparing for interviews; `personal/knowledge/Career_Narratives.md` does not exist or needs new entries added.

**Prerequisites:**
- `personal/knowledge/Experience_Inventory.md` recommended but not blocking

**Completion Signal:** `personal/knowledge/Career_Narratives.md` exists with populated story and decision entries.

**Outputs:**
- `personal/knowledge/Career_Narratives.md`

**Typical Next Steps:** `positioning_builder`, `role_evaluation`

---

### Positioning Builder

**File:** `skills/positioning_builder.md`
**Category:** Knowledge Builder
**Standalone:** Yes — can run independently, but Experience Inventory and Career Narratives should exist first for best results

**Trigger:** User wants to build or update their strategic positioning, framing statements, and recruiter pitch; `personal/knowledge/Positioning.md` does not exist or needs updating.

**Prerequisites:**
- `personal/knowledge/Experience_Inventory.md` recommended
- `personal/knowledge/Career_Narratives.md` recommended

**Completion Signal:** `personal/knowledge/Positioning.md` exists with populated positioning statements and signature themes.

**Outputs:**
- `personal/knowledge/Positioning.md`

**Typical Next Steps:** `role_evaluation`, `career_brief`

---

### Role Evaluation

**File:** `skills/role_evaluation.md`
**Category:** Output Delivery
**Standalone:** No — requires knowledge source documents

**Trigger:** User has a job description and wants to evaluate fit before deciding whether to apply; assessing role alignment against established experience and positioning.

**Prerequisites:**
- `personal/knowledge/Experience_Inventory.md`
- `personal/knowledge/Career_Narratives.md`
- `personal/knowledge/Positioning.md`
- Job description provided by user

**Completion Signal:** `personal/sessions/[Company]_[Role]_[YYYY-MM]_GapAnalysis.md` exists for the target role.

**Outputs:**
- `personal/sessions/[Company]_[Role]_[YYYY-MM]_GapAnalysis.md`
- `personal/sessions/[Company]_[Role]_[YYYY-MM]_SessionLog.md` (temporary — deleted at skill close)

**Typical Next Steps:** `cv_targeted`, `interview_prep` (can proceed to either or both)

---

### CV Targeted

**File:** `skills/cv_targeted.md`
**Category:** Output Delivery
**Standalone:** No — requires GapAnalysis file from role_evaluation

**Trigger:** User has completed role evaluation and wants to generate a tailored CV for the target role.

**Prerequisites:**
- `personal/sessions/[Company]_[Role]_[YYYY-MM]_GapAnalysis.md`

**Completion Signal:** `outputs/[Name]_CV_[Company]_[AbbreviatedRole]_[YYYY-MM].docx` exists.

**Outputs:**
- Tailored CV `.docx` saved to `outputs/`
- `personal/knowledge/Experience_Inventory.md` — `Last Used: YYYY-MM` stamped on every entry cited in the accepted CV (Phase 3 closing, post user acceptance)

**Typical Next Steps:** `interview_prep`

---

### CV General

**File:** `skills/cv_general.md`
**Category:** Output Delivery
**Standalone:** Yes relative to role — no job description or GapAnalysis required, but knowledge source documents must exist

**Trigger:** User wants a generalized CV not tied to a specific role; recruiter outreach; broad job search distribution.

**Prerequisites:**
- `personal/knowledge/Experience_Inventory.md`
- `personal/knowledge/Career_Narratives.md`
- `personal/knowledge/Positioning.md`

**Completion Signal:** `outputs/CV_General_[descriptor]_[YYYY-MM].docx` exists.

**Outputs:**
- General CV `.docx` saved to `outputs/`
- `personal/knowledge/Experience_Inventory.md` — `Last Used: YYYY-MM` stamped on every entry cited in the accepted CV (Phase 5a closing, post user acceptance)

**Typical Next Steps:** None — standalone output

---

### Interview Prep

**File:** `skills/interview_prep.md`
**Category:** Output Delivery
**Standalone:** No — requires GapAnalysis file from role_evaluation

**Trigger:** User has an interview scheduled or approaching and wants to prepare; has completed role evaluation for the target role.

**Prerequisites:**
- `personal/sessions/[Company]_[Role]_[YYYY-MM]_GapAnalysis.md`

**Completion Signal:** `InterviewPrep_[Company]_[AbbreviatedRole]_[YYYY-MM].md`, `InterviewCompletion_[Company]_[AbbreviatedRole]_[YYYY-MM].md`, and `InterviewScratch_[Company]_[AbbreviatedRole]_[YYYY-MM].md` all exist in the user's application folder.

**Outputs:**
- `InterviewPrep_[Company]_[AbbreviatedRole]_[YYYY-MM].md` — reference document
- `InterviewCompletion_[Company]_[AbbreviatedRole]_[YYYY-MM].md` — blank round-tracking file; populated post-interview by `interview_capture`
- `InterviewScratch_[Company]_[AbbreviatedRole]_[YYYY-MM].md` — blank scratch file used during each round for anchor notes; header references prep and completion files
- `personal/knowledge/Questions_Library.md` updated
- `personal/knowledge/Career_Narratives.md` — `Last Used: YYYY-MM` stamped on every narrative cited in the Stories Bank, Alignment Map, or Gap Handling Language (Phase 4a closing, post user acceptance)
- `personal/knowledge/Experience_Inventory.md` — `Last Used: YYYY-MM` stamped on every inventory entry cited in the Alignment Map, Gap Handling Language, or supporting a Stories Bank entry (Phase 4a closing, post user acceptance)

**Typical Next Steps:** `interview_capture` (after each interview round completes)

---

### Interview Capture

**File:** `skills/interview_capture.md`
**Category:** Output Delivery
**Standalone:** No — requires InterviewScratch and InterviewCompletion files from interview_prep

**Trigger:** User has just completed an interview round and needs to capture interviewer details, questions asked, responses given, and round debrief into the InterviewCompletion file.

**Prerequisites:**
- `InterviewScratch_[Company]_[AbbreviatedRole]_[YYYY-MM].md`
- `InterviewCompletion_[Company]_[AbbreviatedRole]_[YYYY-MM].md` (referenced from the scratch file's header)

**Completion Signal:** The target round in `InterviewCompletion_[Company]_[AbbreviatedRole]_[YYYY-MM].md` is populated (Interviewers and Q&A sections contain captured content, hint-text HTML comments replaced for captured fields).

**Outputs:**
- Updated `InterviewCompletion_[Company]_[AbbreviatedRole]_[YYYY-MM].md` — one round populated per invocation

**Typical Next Steps:** `interview_followup` for the round just captured

---

### Interview Follow-Up

**File:** `skills/interview_followup.md`
**Category:** Output Delivery
**Standalone:** No — requires a populated InterviewCompletion file for the target round

**Trigger:** User has captured an interview round via `interview_capture` and wants to write a follow-up letter.

**Prerequisites:**
- `InterviewScratch_[Company]_[AbbreviatedRole]_[YYYY-MM].md` (header references the completion file)
- `InterviewCompletion_[Company]_[AbbreviatedRole]_[YYYY-MM].md` with at least the target round populated by `interview_capture`

**Completion Signal:** `InterviewFollowup_[Company]_[AbbreviatedRole]_R[N]_[YYYY-MM].md` exists in the user's application folder.

**Outputs:**
- Follow-up letter `.md` saved to application folder (one per round; individual files per recipient if multiple letters generated, with recipient last name appended to filename)

**Typical Next Steps:** `interview_capture` for the next interview round; `interview_followup` again after that round is captured

---

### Career Brief

**File:** `skills/career_brief.md`
**Category:** Output Delivery
**Standalone:** Yes

**Trigger:** User needs a short professional bio or summary paragraph for recruiter outreach, networking introductions, speaker profiles, or similar contexts where a standalone written summary is needed.

**Prerequisites:**
- `personal/knowledge/Positioning.md`

**Completion Signal:** Output is plain text displayed in chat — no file is generated.

**Outputs:**
- Plain text short bio (150-200 words, third-person) or professional summary paragraph (4-6 lines, implicit first-person) displayed in chat for copy-paste

**Typical Next Steps:** None — standalone output

---

### Source Document Update — Workflow

**File:** `skills/source_document_update_workflow.md`
**Category:** Utility
**Standalone:** No — invoked only from the close of another workflow skill
**Direct routing by control skill:** Never. This skill is triggered from within `role_evaluation`, `cv_targeted`, `cv_general`, `interview_prep`, `career_narratives_builder`, or `positioning_builder` at session close. The control skill does not route to it directly.

**Trigger:** A calling workflow skill is closing and has defined a session scope; new experience language, framing decisions, gap resolutions, or corrections surfaced during that session should be captured in source documents before the session closes.

**Prerequisites:**
- Active calling-skill session with defined session scope available in context
- At least one target source document exists: `personal/knowledge/Experience_Inventory.md`, `personal/knowledge/Career_Narratives.md`, or `personal/knowledge/Positioning.md`

**Completion Signal:** No specific file signal — source documents are updated in place.

**Outputs:**
- Updated `personal/knowledge/Experience_Inventory.md`, `personal/knowledge/Career_Narratives.md`, or `personal/knowledge/Positioning.md` as applicable

**Shared Core:** Procedural content (Active Domain Load, Criteria for Capture, Format Requirements, Steps 1-5) lives in `rules/source_document_update_core.md`. This skill establishes session scope and delegates execution to the core file.

**Typical Next Steps:** None — returns to the calling skill or closes

---

### Source Document Update — Ad-Hoc

**File:** `skills/source_document_update_adhoc.md`
**Category:** Utility
**Standalone:** Yes — user-invoked entry point for source document updates outside any workflow session

**Trigger:** User wants to capture new information (recent work, revisited stories, corrections) or enrich existing entries (Context, Impact, tags, narrative body content) in the source documents ad-hoc; also the destination for post-bootstrap inventory enrichment of entries flagged during `experience_inventory_bootstrap` and for inventory review passes before a domain switch recommended by `domain_creation`.

**Prerequisites:**
- At least one target source document exists: `personal/knowledge/Experience_Inventory.md`, `personal/knowledge/Career_Narratives.md`, or `personal/knowledge/Positioning.md`

**Completion Signal:** No specific file signal — source documents are updated in place.

**Outputs:**
- Updated `personal/knowledge/Experience_Inventory.md`, `personal/knowledge/Career_Narratives.md`, or `personal/knowledge/Positioning.md` as applicable

**Shared Core:** Procedural content (Active Domain Load, Criteria for Capture, Format Requirements, Steps 1-5) lives in `rules/source_document_update_core.md`. This skill prompts the user to establish session scope and then delegates execution to the core file.

**Typical Next Steps:** None — standalone entry point

---

### Archetype Creation

**File:** `skills/archetype_creation.md`
**Category:** Rules Builder
**Standalone:** No — internally triggered only
**Direct routing by control skill:** Never. This skill is triggered from within `role_evaluation` or `cv_general` when no existing archetype matches the target role. The control skill does not route to it directly.

**Trigger:** No existing archetype in `rules/registry_archetype.md` fits the target role; `role_evaluation` or `cv_general` has stalled at archetype selection.

**Scope:** Produces a single domain-agnostic, level-agnostic archetype file. Archetypes reference the active domain file for vocabulary and calibration and reference the content rules files for level voice; no per-domain or per-level authoring is needed. The new archetype is usable by CV generation immediately after creation.

**Prerequisites:**
- Active `role_evaluation` or `cv_general` session, or independent invocation with job description in hand
- All existing archetypes reviewed and confirmed as poor fits

**Completion Signal:** New archetype file created at `rules/archetypes/Archetype_<N>_<Name>.md`; `rules/registry_archetype.md` updated with new entry.

**Outputs:**
- New archetype file at `rules/archetypes/Archetype_<N>_<Name>.md`
- Updated `rules/registry_archetype.md`

**Typical Next Steps:** Resume `role_evaluation` or `cv_general` from archetype selection step. Optionally add a STRONG calibration example for the new archetype to the active domain file's Section 5.

---

### Domain Creation

**File:** `skills/domain_creation.md`
**Category:** Rules Builder
**Standalone:** Yes — invoked when a new career domain is needed
**Direct routing by control skill:** Never. This skill is triggered when a domain scope mismatch is flagged during `role_evaluation`, when the user pivots to a career domain not currently covered, or when the repo is being extended to support a new tester. The control skill does not route to it directly.

**Trigger:** No existing domain in `rules/registry_domain.md` covers the target roles; `role_evaluation` flagged a domain scope mismatch; the user is extending the repo to a new career domain or new tester.

**Scope:** Produces a single flat file at `rules/domains/<slug>.md` containing taxonomy, vocabulary, selection criteria, tech stack, and per-archetype calibration examples. Does not create or modify archetype files; those are domain-agnostic and governed by `archetype_creation`. Does not flip the Active Domain pointer in `personal/knowledge/Experience_Inventory.md`; activation is an explicit user action after the skill completes.

**Prerequisites:**
- User-supplied scope motivation (what domain and why)
- Access to representative job descriptions and practitioner sources (research phase is gated; source plan must be approved before research executes)

**Completion Signal:** `rules/domains/<slug>.md` exists with all required sections; `rules/registry_domain.md` updated with new entry.

**Outputs:**
- New domain file at `rules/domains/<slug>.md`
- Updated `rules/registry_domain.md`

**Typical Next Steps:** Inventory migration review (if existing inventory entries use tags not present in the new domain's taxonomy), then user edits the Active Domain pointer in `personal/knowledge/Experience_Inventory.md` to activate the new domain

---

### Control

**File:** `skills/control.md`
**Category:** Navigation
**Standalone:** Yes — entry point at any stage of the workflow
**Direct routing by control skill:** The control skill does not route to itself. It is the router.

**Trigger:** User is starting fresh and does not know where to begin; user wants to know where they are in an active workflow; user wants to be routed to the right skill based on current state.

**Prerequisites:**
- None — can be invoked at any point including before any other skill has run

**Completion Signal:** No file produced — output is a routing decision and handoff.

**Outputs:**
- Workflow state summary presented to user
- Routing decision and handoff to the appropriate skill

**Typical Next Steps:** Whichever skill the user is routed to

---

## Adding New Skills

When a new skill is added to the workflow:
1. Add a full entry to this registry following the structure above
2. Update the Workflow Sequence Overview diagram if the skill fits into the sequence
3. Update the State Detection Guide if the skill produces a file-based completion signal that should be checked
4. Update `CLAUDE.md` skills table and `README.md` skills table and loading map
5. Do not modify `skills/control.md` unless the routing logic itself needs to change — skill knowledge lives here, not there
