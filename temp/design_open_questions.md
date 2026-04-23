# Open Design Questions — Experience_Inventory

Parking lot for user-raised questions. To be addressed after Claude's items 1 (tag source and scoping) and 2 (Active Domain at inventory scope) are settled, since those may inform how some of these resolve.

## Intra-document structure (user-raised, 2026-04-23)

1. **Section 6 (Therapeutic Area and Domain Exposure).** Mixes therapeutic areas, trial phases, study types, geographic scope, data modalities, regulatory frameworks, and functional domains in one section. Given the inventory's atomic-structure principle, split into discrete sections for retrieval?

2. **Section 4 (Professional Training).** Mixes completed training (Lean Six Sigma, GCP cert) with ongoing coursework (2025 AI/LLM courses). Split into two sections for retrieval (historical vs active)?

3. **Section 5 (Technical Experience).** Mixes pure technical tools (languages, databases, ML libraries, dev tools) with clinical-application systems (EDC, CTMS, IRT, central labs, IRBs). Split for retrieval?

4. **Section 7 (Employment & Role History).** Currently groups multiple roles under a company header. Retrieval-friendly to flatten (company as a field on each role record) vs keep grouped under company?

5. **Section ordering.** Section 10 (Independent & Volunteer Projects) should precede Section 9 (Academic Coursework Detail). Also: should Education (Section 1) move to the end adjacent to Academic Coursework Detail for coherence, or is TOC-based navigation sufficient?

6. **Tagging of reference sections (1-7).** Prior project decision was not to tag these as retrievable. That decision preceded Python retrieval scripts. Revisit?

## Overarching

7. **Tag aggregation reference.** Once tags and categories are defined across the inventory, domain packs, specialty axis, level axis, and any other rule files, should they be aggregated into a derived read-only reference document for quick lookup in later activities? Source of truth stays in authoritative files; the reference is a view.
