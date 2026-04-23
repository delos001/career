# personal/ — Career Data Repository

This folder is not part of the framework repository. It holds master source documents and session artifacts used at runtime by the CV generation, role evaluation, and interview prep skills.

This file originates in the framework repo at `support/knowledge_repo_scaffolding/SETUP.md`. When you set up your own career data repo, copy this file (along with `README.md`, `.gitignore`, and `Contact_Info.md` from the same scaffolding folder) into `personal/knowledge/` in your cloned repo.

---

## What belongs here

`knowledge/`:
- `Experience_Inventory.md` — canonical source of all career experience entries, tagged and annotated for retrieval
- `Career_Narratives.md` — stories and decisions for interview preparation and CV anchor bullets
- `Positioning.md` — strategic framing statements, signature themes, recruiter pitch language
- `Contact_Info.md` — single source of truth for CV contact line values
- `Questions_Library.md` — reusable interview questions accumulated by `interview_prep`

`sessions/`:
- Session artifacts (GapAnalysis, ContentDecisions, InterviewPrep, InterviewCompletion, InterviewScratch) created per application cycle.

What does not belong here:
- Generated deliverables (CV `.docx`) live in `outputs/` and are not committed to this repo.

---

## Setup

**Steps:**

1. Create a private repository on GitHub (suggested name: `career_development_knowledge`).
2. From the framework repo root, clone the repo into `personal/`:
   ```
   git clone https://github.com/<your-github-username>/career_development_knowledge.git personal/
   ```
3. Create a `knowledge/` subdirectory inside the cloned repo and copy the contents of `support/knowledge_repo_scaffolding/` into it. This gives you a starting `README.md`, `SETUP.md`, `.gitignore`, and `Contact_Info.md` skeleton.
4. Create an empty `sessions/` subdirectory.
5. Commit and push the scaffolding files.
6. Use the framework skills (`experience_inventory_bootstrap`, `career_narratives_builder`, `positioning_builder`) to generate `Experience_Inventory.md`, `Career_Narratives.md`, and `Positioning.md`.
7. Fill in `Contact_Info.md` with your personal contact details.

**Two-repo workflow:**
- Framework changes (skills, rules, README): commit and push from `career_development/`
- Personal data changes: commit and push from `career_development/personal/`

---

## Why it is gitignored

The `career_development` framework repo gitignores the entire `personal/` directory to ensure personal career data is never accidentally committed to a public or shared repository. This means new users cannot read this file from a fresh clone of the framework repo; instead, the canonical copy is shipped in `support/knowledge_repo_scaffolding/` within the framework repo itself and copied into the knowledge repo during setup.
