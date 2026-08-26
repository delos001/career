# Career Narratives

**Used by:** cv_targeted | cv_general | interview_prep | role_evaluation | positioning | career_brief

## Table of Contents

- [Career Narratives](#career-narratives)
  - [Table of Contents](#table-of-contents)
  - [STORIES: STAR / ATOLA](#stories-star--atola)
    - [Consolidating Per-Study Extracts](#consolidating-per-study-extracts)
  - [DECISIONS](#decisions)
    - [Choosing a Single Warehouse Over Federated Extracts](#choosing-a-single-warehouse-over-federated-extracts)

---

## STORIES: STAR / ATOLA

## Consolidating Per-Study Extracts

ID: ST-001
Role: RL-001
Framework: story_personal
Linked Inventory: EX-001

### Situation

- Every study maintained its own data extract, refreshed by hand on request.
- Portfolio-level questions took days to answer and the answers disagreed.

### Baseline

- No shared schema existed; each extract encoded its own conventions.
- Reconciliation was manual and repeated for each request.

### Action

- Modeled a shared schema against the three highest-volume studies.
- Built the load jobs and onboarded those studies one at a time.

### Outcome

- Three studies read from one warehouse instead of per-study extracts.

### Learnings

- Onboarding one study at a time surfaced schema gaps early enough to fix cheaply.

---

## DECISIONS

## Choosing a Single Warehouse Over Federated Extracts

ID: DC-001
Role: RL-001
Framework: decision
Linked Inventory: EX-001

### Decision

- Consolidate into one warehouse rather than standardize the per-study extracts in place.

### Options considered

- Standardize extract format, leave the extracts distributed.
- Consolidate into a single modeled warehouse.

### Rationale

- Standardizing the format would not have removed the reconciliation step.

### Tradeoff accepted

- A longer build before any study saw benefit.
