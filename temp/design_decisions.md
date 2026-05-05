# Career Repo Design Decisions

Closed decisions only. Deferrals: `deferrals.md`. Open questions: `open_questions.md`. Cross-references slug-based. Session protocol in memory `process_session_protocol.md`.

## Cross-Cutting

### Architecture & Conventions

#### pattern-a-framework-native
Use Claude Code's official extension points. Skills at `.claude/skills/[name]/SKILL.md`, agents at `.claude/agents/[name].md`, both with YAML frontmatter. Auto-discovered. No custom skill_registry, no control.md dispatcher. `.claude/` travels with the repo.

#### top-level-containers
`.claude/`, `rules/`, `templates/`, `scripts/`, `outputs/`, `personal/`. Plus `CLAUDE.md` at root. Skills and sub-agents live inside `.claude/`.

#### scripts-centralized
Top-level `scripts/`, subdivided internally (retrieval, resolvers, format conversion). Not co-located with consumers; many scripts called by multiple consumers.

#### file-and-folder-naming
Folders: lowercase kebab-case. No underscores.
Files: lowercase. Underscore between semantic fields; kebab within a field. Compound document-type tokens count as one field.
Examples: `pfizer-001_session-log.md`, `gap-analysis_pfizer-001.md`, `interview-followup_r1_pfizer-001.md`. Attention files and ADRs are exceptions.

#### attention-files
All-caps signals "read me first." Applied set: `README.md`, `SETUP.md`, `COMPONENTS.md`. Future attention-tier files inherit capitalization.

#### adr-naming
MADR convention: zero-padded three-digit prefix + kebab-case title. Sequential, never reused. Supersession is a new record. Example: `001-base-overlay-pattern.md`. Location: `docs/decisions/` at formalization.
Refs: `adr-formalization-timing` (deferral).

#### orientation-file-names
Drop numeric prefix. Files in `rules/orientations/`: `transformation-strategy.md`, `data-analytics.md`, `process-operations.md`, `platform-technology.md`. Retrieval scripts look up by descriptive name.

#### level-file-names
Drop deliverable prefix. `ic.md` and `leadership.md`. Folder path provides context.

#### terminology-phase-skill-workflow
Phase = step within a single skill. Skill = one standalone skill. Workflow = project-level flow across skills. Phase reserved for sub-skill granularity.

#### template-vs-format-spec
Templates are physical carrier files (e.g., Word) that get filled in. Format specs are structural/rendering rules applied to free-form content.

### Composition Model

#### five-orthogonal-axes
- **Orientation** (renamed from prior Specialty / Archetype): governs deliverable structure. `rules/orientations/`. Values: transformation-strategy, data-analytics, process-operations, platform-technology.
- **Industry**: sector. Vocabulary, dialect, regulatory framing. `rules/industries/`. Values: pharma authored; others as built.
- **Specialty** (renamed from prior Skill): professional field of practice. Capability vocabulary and field-specific framing. `rules/specialties/`. Values: clinical-operations, data-engineering, ai-engineering, quality-compliance, people-leadership.
- **Level**: IC vs leadership. Voice and scope framing. `rules/levels/`.
- **Work-state**: operating state of the work environment. `rules/work-states/`. Values: greenfield, scaling, mature, turnaround, post-merger-integration, divestiture, pivot.

Industry/Specialty split replaces prior Domain axis. Axes are independent files. Overrides only where axes genuinely interact, narrow rules not mini-archetypes. Each axis is a discrete categorical dimension; partial-match scoring runs through the adjacency map in each value's frontmatter.

#### dual-orientation-asymmetric-authority
A role may map to two orientations. Primary governs most surfaces; secondary gets bounded explicitly-scoped slots. They do not compete over the same surface.
- CV: secondary in 2-3 achievements and 1-2 Core Competencies items. Summary primary-only.
- Other deliverables: per-deliverable composition rule as needed.
Existing CV dual-orientation rule transfers to `rules/orientations/cv_dual_orientation_composition.md`.

#### level-axis-two-buckets
IC and leadership only today. Expansion via `level_builder`. Level files are deliverable-agnostic; deliverable-specific concerns belong in the deliverable's format spec.
Refs: `level-axis-finer-grained-files`, `level-builder-design` (deferrals).

#### axes-composition-precedence
Each axis owns a primary surface for cv_targeted composition:
- **Orientation** → Section structure, Section emphasis, Summary lead framing.
- **Level** → Voice, verb selection, scope framing within bullets.
- **Specialty** → Capability vocabulary, field-specific terminology, capability surfacing in Professional Experience.
- **Industry** → Sector vocabulary, dialect (acronym recognition, non-preferred terms), sector-emphasis signal.
- **Work-state** → Achievement framing (signal verbs, before/after framing, off-spec patterns) within bullets.

Default conflict resolution: orientation governs structure; other axes govern content within that structure. The more-specific axis wins within its surface — specialty terminology supersedes industry vocabulary in capability descriptions; industry dialect supersedes specialty terminology for sector-recognized acronyms.

Surface ownership is the default precedence, not absolute authority. cv_targeted may implement cross-axis review or challenge mechanisms (e.g., per-axis sub-agents proposing content for their owned surface and reviewing peers' outputs) where converged outputs override default precedence. Mechanism deferred to cv_targeted skill design.

Refs: `five-orthogonal-axes`, `cv-targeted-content-rules-from-axes`, `cross-axis-composition-mechanism` (deferrals).

#### role-evaluation-axis-matching-protocol
role_evaluation matches a JD to each axis by axis-specific mechanism:
- **Framing axes** (orientations, work-states, levels): match via Identity + Selection rule. Read the JD, apply the rule, pick the value.
- **Vocabulary axes** (industries, specialties): match via vocabulary/terminology overlap against the file's existing data sections — Vocabulary + Dialect + Emphasis for industries; Capability vocabulary + Terminology for specialties.

The asymmetry reflects the matching task. Framing decisions require interpreting the JD's primary deliverable, scope, or organizational state (rule-driven). Vocabulary matches resolve via signal overlap (count-driven). Disambiguation between adjacent values within an axis falls to Adjacency rules + JD context.

Refs: `axes-composition-precedence`, `five-orthogonal-axes`, `role-evaluation-orientation-selection-from-axes` (deferral).

#### specialty-axis-tagging-by-work-nature
Specialty tags on inventory and narrative entries reflect the nature of the work performed, not the role's title or formal classification. An entry tags every specialty whose work was meaningfully present, regardless of whether the role was titled with that specialty.

Other axes (industry, orientation, level, work-state) tag by role context — the role's industry, primary deliverable, scope of authority, and organizational state respectively. Specialty is the exception because field-of-practice work can genuinely span within a single role; the other axes describe role-level attributes that do not span within a single role.

Rationale: titles in the wild are unreliable signals (Data Scientist, ML Engineer, Data Engineer overlap; titles drift by company and era). Work-nature tagging trades precision for recall at the inventory level. Precision is recovered at retrieval time when cv_targeted and role_evaluation rank entries by JD relevance.

Refs: `experience-inventory-domain-scoping`, `five-orthogonal-axes`.

#### axes-file-schema
Each axis carries a distinct file schema reflecting its purpose per `axes-composition-precedence`:

- **Industries** (`rules/industries/<value>.md`): frontmatter (industry, last_researched) + body sections: Vocabulary, Dialect, Emphasis, Adjacency.
- **Specialties** (`rules/specialties/<value>.md`): frontmatter (specialty, last_researched) + body sections: Capability vocabulary, Terminology, Adjacency.
- **Orientations** (`rules/orientations/<value>.md`): frontmatter (orientation, last_researched) + body sections: Identity, Summary lead, Section emphasis, Adjacency.
- **Levels** (`rules/levels/<value>.md`): frontmatter (level, last_researched) + body sections: Identity, Voice, Verb vocabulary, Scope signals, Adjacency.
- **Work-states** (`rules/work-states/<value>.md`): frontmatter (work-state, last_researched) + body sections: Identity, Achievement framing, Adjacency.

All axis files carry a `**Used by:**` metadata header below the title per `document-metadata-header-discipline`.

Per-section content authoring guidance (what each section should contain, depth expectations, framing rules) is per-axis-builder design territory and deferred to those skills.

Refs: `axes-composition-precedence`, `document-metadata-header-discipline`, `foundation-execution-order`.

#### skill-stability-loose-coupling
Skills reference rules by category/slug. Resolver script looks up the current file. Skill body does not hard-code paths.

#### retrieval-method-pure-tag-based
Every retrievable inventory entry tagged on every applicable axis (Industry, Specialty, Orientation, Level, Work-state). Pure tag-based as default retrieval mechanism; semantic retrieval can layer on later if cv_targeted needs it. Tagging is reversible; deferring foundation completion is not. Resolves the open question `retrieval-method-for-discrete-elements`.
**Superseded by `cv-targeted-retrieval-architecture-2026-05`.** Prototype testing on two real JDs (one off-corpus-center, one on-corpus-center) showed pure tag-based filtering reduced recall by excluding legitimately translatable entries — particularly IC-level entries with description text matching the JD when the target role was leadership. Semantic retrieval over Description text became the primary path; tags retained for composition-time framing and supplemental tag-pull driven by role_evaluation matched axis values.

#### cv-targeted-retrieval-architecture-2026-05
cv_targeted retrieval is a two-pass hybrid:
1. **Primary pass (semantic on Description):** Pre-extracted Description-only payload (one line per EX-NNN/PR-NNN with ID + Description text) ranked by semantic relevance to the JD. Returns a list of candidate IDs. Cheap on context (description-only is roughly one quarter the size of full entry blocks).
2. **Supplemental pass (tag-pull):** role_evaluation produces matched axis values for the JD. Those matched values drive targeted tag-pulls of inventory entries whose tags signal what their descriptions undersell (an entry whose description reads "designed accountability frameworks" doesn't say "this is governance work"; tags do). Specialty and Orientation are the natural supplemental triggers because they capture the kind-of-work; Level and Work-state are framing axes (used at composition, not retrieval). Industry weights ranking but rarely needs a hard supplemental pull.
3. **Merge and dedup** the two candidate sets. Full entry detail is loaded only for the merged candidate set.

Tags become composition-time data, not retrieval filter:
- **Inclusion:** semantic on Description text, supplemented by JD-driven tag-pulls. Tag filter is dropped.
- **Ranking:** semantic relevance score plus optional Industry/Specialty match weight.
- **Framing:** Level / Orientation / Work-state on each entry drive voice-translation rules at bullet composition time per the axis files.

Rationale: prototype testing showed (b) pure-semantic outperformed (a) tag-filter-plus-semantic on inclusion in both off-corpus-center (Insmed commercial data acquisition) and on-corpus-center (AstraZeneca process management) JDs. JDs vary too much for a fixed tag filter to handle edge cases. Semantic retrieval addresses the variability; tag supplements address the descriptions-undersell problem.

Supplemental tag selection is dynamic, not static — driven by role_evaluation's axis-matching output rather than a fixed "always pull Specialty + Orientation" rule. The matched axes for the role tell us which tags should trigger supplemental pulls for that role.

Refs: `competency-registry-runtime-value` (resolved here), `cv-targeted-hybrid-retrieval` (deferral, reshaped), `role-evaluation-axis-matching-protocol`, `axes-composition-precedence`, `cv-targeted-content-rules-from-axes` (deferral).

#### level-on-entries-effective-level
Level lives only on EX/PR entries (effective level). Captures the pattern of doing higher-than-title-level work within a titled role.
Prior version had Level on both RL-NNN role records (titled level) and EX/PR entries (effective level), with EX/PR defaulting from RL when missing. Removed RL Level after per-entry Level became fully populated on all 197 EX/PR entries: cv_targeted matches JD Level against entry effective level directly; RL Level was never read in retrieval and added no signal. If a future builder skill needs role-level defaulting for new EX entries, the field can be reintroduced.

### Knowledge Documents (Schemas)

#### knowledge-document-roster
Four documents: `User_Info`, `Experience_Inventory`, `Career_Narratives`, `Positioning`. `Questions_Library` eliminated.

#### user-info-rename-and-schema
Rename `Contact_Info.md` to `User_Info.md`.
- Name field source of truth: `User_Info.md`. Removed from `personal/config.yaml`. Format_spec rendering script reads name from `User_Info.md`.
- Drop "Usage Notes" section per data-only-discipline.
- Metadata header: `**Used by:**` per document-metadata-header-discipline. No Stamps or Generated by.
- Placeholder values in scaffolding template like `[Your Name]`.

Schema (revised 2026-05-04 after two generalization audits; original was single-value-only and lacked Location, profile extensibility, and any fields needed by role_evaluation / interview_prep / interview_followup):
- **Used by:** cv_targeted, cv_general, role_evaluation, interview_prep, interview_followup. User_Info holds durable personal data; per-application overrides (situational salary negotiation, role-specific items) live in application files.
- **Identity** section: Name (required), Preferred Name (optional), Pronouns (optional), Name Pronunciation (optional, useful for interview_prep).
- **Location** section: City, State / Region, Country, Time Zone. Split into fields; CV format spec renders the line. Time zone consumed by interview_prep / interview_followup for scheduling and send-timing.
- **Contact** section: Email and Phone as multi-value sub-bulleted lists, each entry labeled (Primary, Work, Mobile, etc.). Schema uniform whether one or many entries.
- **Online Presence** section: unified `Profiles:` labeled list (LinkedIn, GitHub, ORCID, Stack Overflow, Kaggle, Medium, Hugging Face, etc.) plus separate `Websites:` labeled list (Personal Site, Blog, Portfolio). CV format spec privileges LinkedIn/GitHub for contact line by label match; other profiles surface conditionally per CV format rules.
- **Languages** section: bullet list, format `Language — proficiency` (e.g., native, fluent, conversational, basic). Consumed by cv_targeted (CV inclusion when role-relevant) and interview_prep (small-talk anchors, multilingual role fit).
- **Work Authorization** section: Status, Sponsorship Required (Y/N). Consumed by role_evaluation as filter against role's sponsorship policy.
- **Geographic Preferences** section: Modality Preference (Remote/Hybrid/Onsite/Open), Willing to Relocate. Consumed by role_evaluation as fit signal. Travel Willingness intentionally excluded — case-by-case per role, not a static preference.
- **Exclusions** section: Industries / Company Types not under consideration. Consumed by role_evaluation as hard filter.
- Sections intentionally excluded: Availability (notice period, start date) and Compensation (target range, floor) — both change too often and are evaluated case-by-case at application time. They live in per-application files (gap_analysis or equivalent), not User_Info.
- All multi-value fields use bullet sub-list pattern; consumers iterate and select by label.
- Sensitive fields (compensation, authorization) acceptable in this file because `personal/` is gitignored.

Parser conventions (markdown is the storage format; structure is regular enough for regex parsing without semantic LLM). Guiding principle: **structure the file for natural human typing; the parser absorbs format variability.** The user does not carry separator conventions in their head; the parser knows how to read what a human naturally writes.

- Section headings: `## Section Name`.
- Single-value field: `**Field:** value`.
- Multi-value field: `**Field:**` header line followed by `- ...` bullets. Per-section rules:
  - **Email / Phone** bullets carry a label that is metadata for CV rendering (Primary, Work, Mobile). Form is `- Label: value`. Parser is tolerant of separator variants (`:`, ` - `, ` — `).
  - **Profiles** bullets are URLs only; parser auto-detects platform from URL domain (`linkedin.com` → LinkedIn, `github.com` → GitHub, `orcid.org` → ORCID, etc.). Labeled form (`- LinkedIn: <url>`) also tolerated for users who prefer it.
  - **Websites** bullets follow the same pattern as Profiles (URL-only, parser identifies category by domain heuristic or accepts user label).
  - **Languages** bullets are freeform strings displayed as-is in CV (e.g., `- English (native)`). No required separator structure.
  - **Exclusions** bullets are freeform strings.
- Empty marker is forgiving: parser accepts `none`, `*(none)*`, `(none)`, `n/a`, blank-after-colon. All map to null. Recommended canonical form is bare lowercase `none` but not required.
- Scaffolding placeholders: `[bracketed]` form (e.g., `[Your Name]`, `[Yes / No]`). Parser treats any `[...]`-enclosed content as unfilled and emits warnings if encountered at consumption time.
- Multi-value field with no entries: single bullet `- none` or any tolerated empty marker.

Tolerant-parser principle applies file-wide and to other knowledge documents where format conventions exist. Move cognitive burden off the human (every edit) onto the parser implementation (once).

Refs: `user-info-existing-data-migration` (deferral).

#### career-narratives-schema
- IDs: `ST-NNN` for stories (10 currently), `DC-NNN` for decisions (6 currently). First line of metadata block.
- Field renames: `Tags` → `Capability`; `Archetype` → `Orientation`.
- New fields: `Industry` (multi), `Specialty` (multi), `Role Level`, `Purpose` (optional). `Era` retained as company-specific.
- Final metadata block: ID, Capability, Industry, Specialty, Orientation, Role Level, Purpose, Framework, Linked Inventory (optional), Era, Added, Last Used.
- Orientation and Work-state per-entry fields pending `retrieval-method-for-discrete-elements` resolution.
- Header: `**Used by:** cv_targeted, cv_general, interview_prep, role_evaluation, positioning, career_brief`. `**Stamps:** Last Used (YYYY-MM)`.
- Tag Taxonomy section removed.
- Framework field: stories → `story_personal` (all 10); decisions → `decision_adr` (all 6). Migration: fold "Who Pushed Back" into Context; drop "What I'd Own Differently" subsections.
- APPENDIX removed; framework defs live in `rules/narratives/`.
- Empty subsections retained with `Not applicable` placeholder.
- `Linked Inventory:` field: multi-value, optional. Narrative → inventory only (asymmetric).
Refs: `career-narratives-existing-data-migration`, `career-narratives-cleanup-script`, `maintained-by-metadata-field` (deferrals).

#### positioning-schema
- Cut: Competencies (~30 bullets), Role-Targeted Accomplishments (~30 bullets). CV and role evaluation pull from Experience_Inventory directly.
- Retain: Positioning Statement + Focus Bullets, Core Philosophy, What Makes Me Unique (renamed from "What Makes This Different"), Industry Trajectory, Signature Themes, Elevator Statement, LinkedIn About Me, Why I Chose to Leave BioMarin.
- Reorder: Signature Themes follows Core Philosophy.
- IDs: `TH-NNN` on themes.
- APPENDIX removed entirely; `Linked Stories:` field added to themes.
- Customization Instructions move to `career_brief`.
- Recruiter Pitch Template moves to `templates/recruiter_pitch_template.md`.
- "Avoid:" line removed from WHY I LEFT (moves to `interview_prep`).
- "Last Revised" line kept as plain text at top.
- Typo fix: "INDUSTRY TRAGECTORY" → "INDUSTRY TRAJECTORY".
- Header: `**Used by:** cv_targeted, cv_general, role_evaluation, interview_prep, career_brief`.
Refs: `positioning-existing-data-migration` (deferral).

#### experience-inventory-domain-scoping
Every retrievable entry (EX-NNN, PR-NNN) carries `Industry:` and `Specialty:` fields. Multi-value, pipe-delimited. No document-level Active Domain.
- Industry validates against `rules/industries/registry.md`. May be empty.
- Specialty required. Validates against `rules/specialties/registry.md`. Identifies specialty pack for Capability validation.
- Capability validation: any-specialty rule.
- Reference sections (Education, Certifications, etc.) untagged.

Per-entry fields for Orientation and Work-state pending `retrieval-method-for-discrete-elements` resolution.

#### experience-inventory-entry-types
`EX-NNN` (employment, Section 8), `PR-NNN` (independent and volunteer, Section 10). Same field schema. Differ in ID prefix, descriptor field name (`Role:` vs `Project:`), section. New categories add new prefix ad hoc.

#### experience-inventory-section-6-rename
Renamed "Therapeutic Area and Domain Exposure" → "Industry Exposure Profile". `**Bold:**` lines → `### Sub-section` headings.
Sub-sections: Therapeutic Areas, Trial Phases, Study Types, Geographic Scope, Data Sources (renamed from Data Modalities), Standards (new), Regulatory Frameworks, Functional Experience (renamed from Functional Domains).
Data Modalities sub-section dropped — content folded; "Data Sources" carries the operative meaning (EDC, central lab, ePRO, IXRS, etc.).

#### experience-inventory-section-1-structured-fields
Section 1 (Education) entries carry structured fields, no IDs: Degree, Discipline, Institution, Start Date, End Date. Year-only date granularity (YYYY). Honors/GPA omitted. No retrieval tagging — section remains reference content per `experience-inventory-tagging-granularity`; structure exists to give cv_targeted's renderer reliable field handles instead of comma-parsing a flat line (which broke on disciplines containing commas).
Refs: `experience-inventory-tagging-granularity`.

#### experience-inventory-section-2-structured-fields
Section 2 (Professional Certifications) entries carry structured fields, no IDs: Certification, Issuer, Date Earned, Expiration Date, Status. Year-only date granularity. Expiration Date optional (blank for non-expiring or unknown). Status enum: Active | Inactive. No retrieval tagging — reference content. Schema designed for generalization (other users may hold active expiring certs); blank fields acceptable.
Refs: `experience-inventory-tagging-granularity`, `feedback_design_for_generalization`.

#### experience-inventory-section-3-structured-fields
Section 3 (Professional Affiliations) entries carry structured fields, no IDs: Affiliation, Role, Start Date, End Date, Status. Year-only date granularity. Role field accommodates Member through Board/Officer/Committee Chair (general-utility, not just current user's "Member"). Status enum: Active | Inactive (extensible). No retrieval tagging.
Refs: `experience-inventory-tagging-granularity`, `feedback_design_for_generalization`.

#### experience-inventory-section-4-restructure
Professional Training: Completed and In Progress sub-sections. Year dropped from In Progress sub-header.
Structured fields per entry, no IDs: Training, Provider, Format, Start Date, End Date. Date granularity YYYY-MM. Format optional (Online | In-Person | Hybrid). Sub-section split provides Status indicator (no separate Status field). No retrieval tagging — reference content. Schema designed for generalization.
Refs: `experience-inventory-tagging-granularity`, `feedback_design_for_generalization`.

#### experience-inventory-section-5-restructure
Technical Experience: three sub-sections.
- Programming, Data & Analytics (Languages & Data Engineering, ML & Analytics, Cloud & Platforms, Visualization & Reporting, Development Tools, Project Management Tools)
- Office & Collaboration (SharePoint, MS Teams, OneNote, Visio, Adobe Acrobat Pro, Adobe LiveCycle Designer)
- Clinical Application Systems (9 categories carried forward)
Methodologies sub-section dropped; items relocated. Recategorizations: Minitab → ML & Analytics; MS Access → Languages & Data Engineering; JIRA, MS Project → Project Management Tools. Oracle Apex dropped.

Tools-only discipline: Section 5 lists named tools, products, libraries, and platforms only. Capability descriptions, methods, algorithms, and work-scope descriptors do not belong here — that content lives in Section 8 (EX entries) or other sections. Cleanup pass stripped: ETL/ELT workflows, file parsing, ML methods (ARIMA, regression, clustering, PCA, NLP, EDA, etc.), simulation/optimization, decision analytics, Python/R viz libraries (generic), custom user-built apps, "(generic)" placeholders.

Flat-list convention: one tool/product per token, comma-separated. Sub-products enumerated separately (Jupyter Notebook, JupyterLab — not Jupyter (Notebooks, Lab); Git, GitHub — not Git/GitHub). Acronym-expansion parens permitted (eRT (e-Research Technology)) since JDs may use either form. Scope/role descriptors stripped from parens. Generic category mentions (ePRO platforms, eCOA platforms) retained when no specific named platform exists — supports JD category-level matching. Versions dropped from tool names (Minitab, not Minitab17).
Refs: `feedback_design_for_generalization`.

#### experience-inventory-section-7-flat-records
Flat records, each role self-contained, company as a field. Stable ID `RL-NNN`.
EX entries reference Section 7 via `Role: RL-NNN` field per `inventory-role-rl-reference-applied-2026-05`. RL Title and Company are canonical; EX entries do not carry duplicate Title/Company fields. Resolves the rebrand-resilience problem that motivated the original "Title | Company" coexistence design.

#### experience-inventory-section-ordering
Sections 9 and 10 swap. Independent & Volunteer Projects → 9. Academic Coursework Detail → 10. Education stays at top.

#### experience-inventory-tagging-granularity
Reference sections addressable at sub-section level via heading anchors. Per-item tagging not added.
Refs: `experience-inventory-existing-data-migration` (deferral).

#### narratives-placement
`rules/narratives/` with five files: `decision_adr`, `decision_personal`, `story_atola`, `story_star`, `story_personal`.

#### tag-taxonomy
`rules/tags.yaml` holds only global tag vocabularies that apply to every entry: Role Level, Purpose. YAML. Org Context absorbed into the Work-state axis.
Specialty-specific tags do not live here. Specialty-pack capability vocabulary (fine-grained, specialty-specific) in `rules/specialties/<specialty>.md` Capability vocabulary section. Industry packs hold industry content but not Capability lists.
Orientation values in `rules/orientations/`. Industry/Specialty registries: `rules/industries/registry.md`, `rules/specialties/registry.md`. (Competency registry previously lived at `rules/competencies/registry.md`; removed per `competency-field-and-registry-removed-2026-05`.)

#### initial-industry-pack-content-design
Pharma industry pack (`rules/industries/pharma.md`) content-validated through manual research against current practitioner sources (FDA, ICH, ACRP, regulatory publications, hiring keyword surveys). Vocabulary, dialect, emphasis, adjacency captured. Future industry packs trigger `industry_builder` build at that time; pharma serves as the worked example.
Refs: `temp/axis_research_notes.md`, `foundation-execution-order`, `five-orthogonal-axes`.

#### initial-specialty-pack-content-design
Five specialty packs (`rules/specialties/clinical-operations.md`, `data-engineering.md`, `ai-engineering.md`, `quality-compliance.md`, `people-leadership.md`) content-validated through manual research against current practitioner sources (industry frameworks, hiring keyword surveys, regulatory publications, framework authorities). Capability vocabulary, terminology, adjacency captured per specialty. Future refresh runs through `specialty_builder` if/when built.
Refs: `temp/axis_research_notes.md`, `foundation-execution-order`, `five-orthogonal-axes`, `tag-taxonomy`.

#### outcome-folded-into-impact
`Outcome:` field removed from inventory entries. Closed-enum value (Capability Building, Risk Reduction, Quality Improvement, Efficiency Gain, Cost Savings, Scalability/Growth Enablement) folded into `Impact:` field as a colon-delimited prefix: `Impact: <value-type>: <prose>` when prose exists, `Impact: <value-type>` when prose was absent.
Rationale: Outcome was not called out as a retrieval signal in `cv-targeted-content-rules-from-axes`; coverage was 64% (126/197) so it added a sparse field with no committed downstream consumer. Folding into Impact preserves the value-type signal (grep-extractable via the leading colon-delimited token) while collapsing schema. Reads as natural narrative — the value-type clause is not "wrong" as the leading word of impact prose.
Supersedes the prior `field-rename-outcome-purpose` decision (Outcome was to be renamed to Purpose; now removed entirely).
Refs: `inventory-entry-structure-applied`, `inventory-field-drift-cleanup` (deferral), `cv-targeted-content-rules-from-axes` (deferral).

#### competency-field-and-registry
Inventory entry field `Capability:` renamed to `Competency:`. Controlled vocabulary at `rules/competencies/registry.md`. Validator (deferred to script build) parses inventory Competency lines, splits on `|`, rejects unknown tokens; aliases auto-canonicalize near-misses.
Rationale: name-collision avoided with specialty-pack `Capability vocabulary` sections; "Competency" links semantically to CV format spec's "Core Competencies" section.
Initial 16-term registry derived from existing inventory tags. **Superseded by `competency-registry-bottom-up-redesign-2026-05`** which replaced the registry contents with 31 lowercase-kebab values via bottom-up phrase extraction across all 197 entries. The Capability→Competency rename and registry-as-controlled-vocabulary concept established here remain valid; only the value list was replaced. **Further superseded by `competency-field-and-registry-removed-2026-05`** which removed the field and registry entirely.
Refs: `tag-taxonomy`, `inventory-entry-structure-applied`, `competency-registry-bottom-up-redesign-2026-05`, `competency-field-and-registry-removed-2026-05`.

#### competency-registry-bottom-up-redesign-2026-05
Replaced prior 16-term coarse Competency registry with a 31-term granular registry. Format changed from Title Case to lowercase kebab to match other axis value formats. **Superseded by `competency-registry-activity-level-redesign-2026-05`**, which replaced the 31-term inventory-derived shape with a 36-term activity-level taxonomy. The bottom-up extraction approach was found to produce inventory-shaped clusters (over-fit to the specific texture of the user's work) rather than activity-level competencies that transcend industry and specialty.
Refs: `competency-field-and-registry`, `competency-registry-activity-level-redesign-2026-05`.

#### competency-retagging-applied-2026-05
Re-tagged all 197 EX/PR inventory entries (`Competency:` field) against the 36-term activity-level Competency registry. JD-blind authoring; consistency-validated against a tagging-pattern reference (site-monitoring lifecycle → `operations-management` + `regulatory-compliance`; safety surveillance / SAE handling → `risk-management`; specifications → `standards-and-specification-development`; SOP / form authoring → `procedure-authoring`; etc.). Prior 16-term and 31-term Competency values fully replaced. All 36 slugs used at least once. Apply executed via `temp/apply_competency_retagging.py` against `temp/competency_retagging_proposal.md` (both retained as evidence trail).
Resolves the work component of the prior `competency-retagging-step-5` deferral. Whether the registry remains in cv_targeted's runtime retrieval path is still pending prototype outcome (`competency-registry-runtime-value` open question); if semantic-only retrieval wins, the new Competency tags become informational rather than active retrieval signal but the labor is not wasted.
Registry-gap candidates surfaced and resolved during user QC: `regulatory-document-authoring` (dropped — re-framed as `risk-management` + `cross-functional-collaboration`), `clinical-operations-execution` (dropped — entries won't surface in any CV), `vendor-management` ↔ `technology-evaluation` (split confirmed: service vendors → vendor-management; tool/platform vendors → technology-evaluation), audit-conducting (no separate slug — sponsor-SME audit support belongs under `audit-and-inspection-response`).
**Superseded by `competency-field-and-registry-removed-2026-05`.** Prototype outcome was semantic-only wins; the retagging labor is not lost — it stress-tested the registry design and confirmed the orthogonality problem with Specialty. Field stripped from inventory.
Refs: `competency-registry-activity-level-redesign-2026-05`, `competency-registry-runtime-value` (resolved by `cv-targeted-retrieval-architecture-2026-05`), `inventory-section-8-subsection-reassignment` (deferral — Step 6 trigger fires here but action deferred pending prototype outcome), `competency-field-and-registry-removed-2026-05`.

#### inventory-role-rl-reference-applied-2026-05
Cluster C migration applied: EX entry `Title:` and `Company:` fields collapsed into a single `Role: RL-NNN` reference to Section 7. RL becomes canonical for role title and company; rebrand resilience is now one record's update instead of 192. PR entries unchanged (no RL counterpart).

Reconciliation produced two RL Title corrections (Section 7 was holding contracted/HR titles where EX entries held operational/working titles; user resolved each by adopting the operational title as canonical):
- RL-017: `Clinical Data Quality Consultant` → `Sr. Data Scientist, Data Management Sciences`.
- RL-012: `Central Statistical Monitoring Lead` → `Central Statistical Monitoring Deployment Lead`.

One compound EX Title (`Regional/Global Clinical Trial Manager`, Amgen-via-DOCS, 10 entries) split between RL-011 (Regional CTM) and RL-013 (Global CTM) per per-entry user assignment based on Description content. 7 → RL-011; 3 → RL-013 (EX-088, 089, 091).

Mapping logic (in `temp/_apply_role_rl_reference.py`): explicit per-EX-ID overrides for the compound-title cluster, then exact (Title, Company) match, then whitespace+slash-normalized title match within company, then EX-title-as-substring of RL Title within company. Whitespace+slash normalization handled `Clinical Research Associate I/II` (EX) vs `Clinical Research Associate I / II` (RL-005, 19 entries).

Apply executed via `temp/_apply_role_rl_reference.py --apply`. Line count 3045 → 2853 (delta -192). Script and dry-run output retained as evidence trail.

Closes the work component of `inventory-company-field-rl-reference` deferral and the Cluster C item in `experience-inventory-existing-data-migration`.

Refs: `experience-inventory-section-7-flat-records`, `inventory-entry-structure-applied`, `inventory-company-field-rl-reference` (deferral, closed here), `experience-inventory-existing-data-migration` (deferral, Cluster C closed here).

#### competency-field-and-registry-removed-2026-05
Inventory `Competency:` field removed from all 197 EX/PR entries. `rules/competencies/registry.md` deleted; `rules/competencies/` folder removed.

Removal driven by the `cv-targeted-retrieval-architecture-2026-05` decision: tags become composition-time data, not retrieval filter, and Industry/Specialty/Orientation/Level/Work-state already cover the framing and ranking signals cv_targeted needs. Competency added no orthogonal axis once the activity-level redesign was understood as overlapping with what Specialty already captures (specialty-pack capability vocabularies). The bottom-up and activity-level redesign attempts (16→31→36 terms) confirmed the registry could not stably partition the corpus without either over-fitting to inventory texture or duplicating Specialty content.

Strip executed via `temp/_strip_competency_field.py` (line count 3242 → 3045). Folder deletion via filesystem.

Supersedes: `competency-field-and-registry`, `competency-registry-bottom-up-redesign-2026-05`, `competency-registry-activity-level-redesign-2026-05`, `competency-retagging-applied-2026-05`. Closes the work component of all four. Historical proposals retained at `temp/competency_extraction.md`, `temp/competency_clustering_proposal.md`, `temp/competency_retagging_proposal.md`, `temp/apply_competency_retagging.py` as evidence trail; their referenced data state no longer matches the inventory.

Updates:
- `inventory-entry-structure-applied`: field list shortened (Competency removed). EX/PR entries now carry: ID, Title-or-Project, Company, Industry, Specialty, Orientation, Level, Work-state, Added, Last Used, Description, Impact, Context.
- `tag-taxonomy`: registry reference removed. `rules/tags.yaml` retains global tag vocabularies (Role Level, Purpose); axis files retain their own vocabularies. No entry-level coarse functional grouping field.

Refs: `cv-targeted-retrieval-architecture-2026-05`, `inventory-entry-structure-applied`, `tag-taxonomy`, `competency-registry-runtime-value` (resolved).

#### competency-registry-activity-level-redesign-2026-05
Replaced 31-term inventory-derived registry with 36-term top-down activity taxonomy. Each value names a unit of work that means the same thing across industries (e.g., `budget-management` is the same competency for a clinical PM and a small-business owner). Industry- and specialty-agnostic by design; industry/specialty context is captured by the dedicated axes.
Rationale: the bottom-up approach over-fit to the user's inventory texture, producing artificial splits like `vendor-and-cro-operational-management` vs `vendor-and-cro-selection-and-partnership-design`. JDs do not distinguish at this granularity, and granular splits prevent transferable-skill surfacing (vendor-selection experience IS relevant to a vendor-oversight JD; programming-in-R IS relevant to a Python JD). The activity-level reframe asks: "could a hiring manager in any industry write 'looking for someone with __ experience' and have it sound like a real ask?" Tools and clinical-specific terms (TMF, RBM, CSM, CSV, site monitoring, investigator training) leave the registry; tools live in `Experience_Inventory.md` Section 5; clinical-specific work is captured at the underlying activity level (RBM strategy → `risk-management` or `quality-management`; TMF reconciliation → `procedure-authoring` or `regulatory-compliance`; site monitoring → `operations-management`).
Format: lean. Each entry is `- **slug**: one-line scope phrase`. No `Aliases:` section in this iteration; JD-language → slug mapping deferred to cv_targeted matching layer (semantic vs alias-list approach undecided).
Process: top-down draft of activity categories validated against `temp/competency_extraction.md` for coverage (the user's 197 inventory entries should all map cleanly into the new taxonomy via Step 5).
Status: registry written. Step 5 (re-tag 197 entries against new 36-term registry) and Step 6 (Section 8 sub-section reassignment) remain deferred.
**Superseded by `competency-field-and-registry-removed-2026-05`.** Field and registry removed entirely.
Refs: `competency-registry-bottom-up-redesign-2026-05` (superseded), `competency-field-and-registry`, `tag-taxonomy`, `inventory-entry-structure-applied`, `competency-retagging-step-5` (deferral), `inventory-section-8-subsection-reassignment` (deferral), `cv-targeted-content-rules-from-axes` (deferral — owns JD-to-slug matching mechanism), `competency-field-and-registry-removed-2026-05`.

#### knowledge-document-scaffolding
`support/` folder at repo root holds scaffolding files; user copies into private personal repo on first clone. Career repo never holds user's personal data.
- Scaffolded: `User_Info.md` (placeholder), `README.md`, `SETUP.md`, `.gitignore` for personal repo.
- Not scaffolded (built by skills): `Experience_Inventory.md`, `Career_Narratives.md`, `Positioning.md`.
Refs: `scaffolding-folder-layout`, `scaffolding-content-updates` (deferrals).

#### questions-library-eliminated
Originally context-free interview question library; drifted to per-application questions. Eliminated. Per-application questions live in application folder.
Refs: `questions-library-deletion` (deferral).

#### knowledge-doc-update-mechanism-hand-edit
Existing knowledge documents (User_Info, Experience_Inventory, Career_Narratives, Positioning) updated by hand-edit. Builder skills become refresh tools later, only if refresh demand recurs. Mechanical sub-tasks may use one-off scripts (e.g., `temp/migrate_inventory.py`). Resolves the open question `knowledge-doc-update-mechanism`.

#### inventory-entry-structure-applied
EX-NNN entries carry, in order: ID, Role, Industry, Specialty, Orientation, Level, Work-state, Added, Last Used, Description (`Description:` label, bold preserved on value), Impact, Context.
PR-NNN entries carry, in order: ID, Project, Company, Industry, Specialty, Orientation, Level, Work-state, Added, Last Used, Description, Impact, Context.
Schemas diverge on the second field: EX uses `Role: RL-NNN` reference to Section 7 (per `inventory-role-rl-reference-applied-2026-05`); PR uses `Project:` + `Company:` since Independent & Volunteer projects have no RL counterpart. Title field on EX entries dropped; RL is canonical for role title and company.
Prose section order at end of block: Description (Action), then Impact (Result), then Context (Situation). Impact is sparse-permitted, may carry a colon-delimited value-type prefix per `outcome-folded-into-impact` (e.g., `Impact: Risk Reduction: <prose>` or `Impact: Risk Reduction`). Context is sparse-permitted, free prose.
Competency field removed per `competency-field-and-registry-removed-2026-05` (originally listed between Work-state and Added).
Refs: `experience-inventory-domain-scoping`, `experience-inventory-entry-types`, `outcome-folded-into-impact`, `impact-field-semantics-2026-05`, `competency-field-and-registry`, `inventory-role-rl-reference-applied-2026-05`, `inventory-field-drift-cleanup` (deferral).

#### impact-field-semantics-2026-05
Refines `outcome-folded-into-impact` based on 2026-05-04/05 reconciliation pass against existing entries.

**Multi-value-type prefix permitted.** Impact value-type prefix may be a single value or comma-delimited list (e.g., `Impact: Capability Building, Quality Improvement, Risk Reduction` or `Impact: Capability Building, Quality Improvement, Risk Reduction: <prose>`). The Impact field is free-text prose with structured value-type prefix; the prefix is grep-extractable in either single or multi-value form. Multi-value reflects that real work often produces value across multiple types.

**Bare-tag is the fallback, not drop.** When an entry has no recoverable residual outcome beyond the Description, the value-type tag stays bare (`Impact: <value-type>` or `Impact: <type>, <type>`). The "substantiate or drop" wording in earlier `inventory_builder_quality_checks.md` was too aggressive: substantiate where possible, otherwise keep bare. Dropping the Impact line entirely is not the convention.

**Strip-aggressively rules for Impact prose.** When prose is present, it must be only outcome content. Strip:
- Audit/diagnostic findings ("revealed that X was opaque"). Move to Description as activity output, or Context as situational state.
- Pattern descriptions ("a pattern that consumed significant effort"). Move to Context.
- Qualifiers and explanatory clauses ("from sample receipt to dataset exchange"). Move with the finding.
- Mechanism narratives ("CDISC-terminology standardization eliminated non-standard legacy terminology that had been creating downstream programming overhead"). Mechanism is in Description; outcome stays as the bare residual.
- Purpose/aspirational framing ("to support enterprise data quality and regulatory submission objectives"). Drop entirely; the value-type tag carries this.
- Attribution caveats ("Full attribution to the redesign alone is not claimed; concurrent improvements contributed"). Move to Context.
- Restatements of Description's purpose clause as Impact ("worked X to support Y" with Impact "supported Y"). Description's purpose is not residual.

**Context narrative trim rules.** Cut from Context:
- Granular numbers (step counts, person counts, function counts) when generic descriptors preserve the signal.
- Colorisms ("symbolic comfort", "concentrated risk") if they restate a plain claim already made.
- Implementation tactics (how skepticism was overcome, what filtering choices reduced noise).
- Designer-decision defenses unless the boundary itself is residual signal.

Keep in Context: prior state when it makes the outcome legible; constraint envelope (resource model, headcount, organizational positioning); deliberate scope decisions when the bound is load-bearing.

**Restructure license.** Status-reached outcomes mistakenly placed in Description (e.g., "Developed roadmaps that shaped functional priorities") should be moved to Impact. Activity verbs and methodology stay in Description; realized outcomes move to Impact.

Refs: `outcome-folded-into-impact`, `inventory-entry-structure-applied`, `temp/inventory_builder_quality_checks.md`.

#### industry-value-granularity
Industry registry values: pharma, biotech, cro, med-device, eclinical, generics, diagnostics. Discrete rule files for pharma, biotech, cro, med-device (all research-validated 2026-04). eclinical = registry-only (single inventory entry; pharma adjacency handles translation). generics, diagnostics = file authoring deferred.
Reasoning: GICS/NAICS treat pharma and biotech distinct; submission pathway (NDA via CDER vs BLA via CBER) is meaningful CV signal. CRO is service-side perspective with distinct hiring emphasis (cross-sponsor, contract delivery). Med-device has fundamentally different regulatory framework (510(k)/PMA/De Novo, ISO 13485, design controls).
Refs: `industry-files-full-enumeration`, `initial-industry-pack-content-design`.

#### industry-files-full-enumeration
Each industry file (`pharma.md`, `biotech.md`, `cro.md`, `med-device.md`) enumerates its full vocabulary, dialect, and stakeholder content. No `inherits from <other>.md` shorthand. Shorthand was attempted in initial biotech.md and cro.md drafts and broke `role-evaluation-axis-matching-protocol` (vocabulary axes match by overlap against the file's data sections; a matcher reading the file alone misses inherited terms). Resolution: full enumeration accepts cross-file content redundancy as the cost of discrete-industry granularity. Update propagation tracked via `registry-overlap-tracking`.
Refs: `axes-file-schema`, `role-evaluation-axis-matching-protocol`, `industry-value-granularity`, `registry-overlap-tracking` (deferral).

### Skills System

#### skill-registry-and-control-dissolved
Pattern A removes custom `skill_registry` and `control.md`. Framework discovery + slash-command picker. Per-skill metadata in SKILL.md frontmatter.

#### role-evaluation-and-cv-targeted-separate
Kept distinct. Shared inputs resolved by retrieval scripts (slice-level lookup). GapAnalysis is the handoff artifact and a stopping point. "Application" is a data-model concept (folder name), not a skill name.

#### knowledge-update-collapse
One skill with mode parameter, replacing `knowledge_update_adhoc` and `knowledge_update_inline`. Retrieval script fetches relevant slice at read time.

#### rule-builder-skills-inline-procedure
Builder skills (`orientation_builder`, `industry_builder`, `specialty_builder`, `level_builder`, `work_state_builder`) hold construction procedure inline in SKILL.md. No `rules/builders/` folder.

#### builders-axis-parity
One builder per axis. Each wired to its corresponding research sub-agent.

#### builder-mode-parameter
- `create`: drafts new rule file from research output. Greenfield.
- `refresh`: targets existing rule file, re-runs research, diffs against current, proposes updates.
Both invoke research sub-agent.
Refs: `builder-refresh-mechanics` (deferral).

#### research-sub-agents-roster
Seven sub-agents in `.claude/agents/`:
- `role_research` (used by role_evaluation)
- `organization_research` (used by interview_prep)
- `industry_research` (used by industry_builder)
- `specialty_research` (used by specialty_builder)
- `orientation_research` (used by orientation_builder)
- `level_research` (used by level_builder)
- `work_state_research` (used by work_state_builder)
All seven built (end-to-end testing requires all pieces).
Refs: `research-output-location-and-format` (deferral).

#### qc-organization
Specs in `rules/quality_control/`. Executors as sub-agents in `.claude/agents/`. Skills call QC; sub-agents execute in isolated context.
Naming: `qc_<scope>_<aspect>.md` for both specs and executors. Examples: `qc_cv_format`, `qc_cv_structural`, `qc_gap_analysis_completeness`. `qc_` prefix kept on both sides.

#### skill-authoring-template-library
Location: `engops/cheatsheets/skill-templates/`. First template: `human-gated-workflow.md`. Authored alongside the first skill that uses it. Conventions recorded here in the interim.

#### workflow-communication-conventions
Three communication points in skills.

**Introduction (skill start):**
- Full: multi-activity skills. Invokes `python scripts/display/introduce.py <skill_name>`. Reads from `scripts/display/introductions.yaml`. Ends with "Ready?" consent gate.
- Brief inline: single-activity skills. One-sentence declaration in SKILL.md.
Heuristic: name conveys arc → brief; otherwise → full.
Roster: full = role_evaluation, cv_targeted, interview_prep. Brief = career_brief, industry_builder, specialty_builder, orientation_builder, level_builder, work_state_builder, knowledge_update, positioning. Ambiguous (deferred): interview_capture, interview_followup, cv_general, experience_inventory, career_narratives.

**Mid-flight narration:** before tool calls > a few seconds, narrate What/Why (one clause)/Duration (optional). Skip for fast operations. On return, brief acknowledgment.

**Presentation (phase boundaries):** existing convention.

Folder: `scripts/display/`.
Refs: `introduce-py-implementation`, `introduction-roster-ambiguous-skills` (deferrals).

### Lineage & Traceability

Application lineage only. Knowledge-doc version history handled by git.

#### application-id-format
`<company-slug>-NNN`. Lowercase. Per-company counter. Examples: `pfizer-001`, `jnj-003`.

#### company-slug-registry
User enters slug at first encounter. Stored in `rules/organizations/company-slugs.yaml` with full company name. Counter increments on each ID issue.
Schema: YAML keyed by slug. Three fields: slug (key), `name`, `counter`.
```yaml
pfizer:
  name: Pfizer Inc.
  counter: 3
```
Cut fields: aliases, former_names, first_seen, applications list, access stamp.
Refs: `application-id-script-implementation` (deferral).

#### session-log-location-and-creation
Created at start of role_evaluation regardless of apply decision. `personal/sessions/<slug>-NNN_session-log.md`.

#### session-log-frontmatter-schema
YAML frontmatter, five fields:
```yaml
---
application_id: pfizer-001
company: Pfizer Inc.
role: Director, Clinical Data Operations
created: 2026-04-24
state: evaluating
---
```
- `application_id`: required. Mirrors filename prefix.
- `company`: snapshot at creation. Denormalized for self-containment and historical accuracy under rebrand.
- `role`: free-text.
- `created`: YYYY-MM-DD.
- `state`: enum `evaluating | applied | interviewing | do-not-pursue`. File location stays in `personal/sessions/`; closure signaled by state.
Cut fields: role_slug, last_updated, outcome/fit_verdict, access stamps.
Refs: `session-log-body-schema`, `session-log-parser-tests` (deferrals).

#### per-application-folder
`personal/applications/<slug>-NNN-<role-slug>-<yyyy-mm>/`. Created on apply decision. User enters role slug at application start. Files inside use `<slug>-NNN` alone.

#### do-not-pursue-folder
`personal/do-not-pursue/` for role_evaluations not advancing.

#### lineage-file-naming-convention
Per file-and-folder-naming. Compound application ID embedded. Examples: `gap-analysis_pfizer-001.md`, `cv_pfizer-001.docx`.

#### last-used-stamping
Skills stamping accepted outputs add `Last Used: YYYY-MM` to cited entries in `Experience_Inventory` and `Career_Narratives`.

#### state-detection
Ordered checks combine file existence and session log entries.
Refs: `state-detection-logic-and-location` (deferral).

#### tracker-integration-out-of-scope
External Google Drive tracker not in current scope.
Refs: `tracker-integration` (deferral).

### Documentation Discipline

#### component-documentation-discipline
Every skill, sub-agent, standalone script has a `COMPONENTS.md` entry: inputs, outputs, triggers, update triggers. Authored alongside the component. Component evolution requires entry update in same change.
Repo `CLAUDE.md` references `COMPONENTS.md`.

#### document-metadata-header-discipline
Every doc programmatically consumed by skills/sub-agents/scripts carries a metadata header below the title.
Scope in: knowledge documents, rule files, templates.
Scope out: skills/sub-agents (have YAML frontmatter and COMPONENTS.md entries), meta docs, outputs, scripts.
Format: plain markdown lines, `**Field:** value`, multi-value comma-separated. Selected over YAML frontmatter (renders invisibly in VS Code preview).
Fields v1, applied minimally:
1. **Used by**: required when consumed.
2. **Stamps**: optional, only where stamping happens.
3. **Generated by**: optional, only for script-generated docs.
Inline prose references to component names discouraged; named refs belong in metadata header.
Refs: `metadata-header-reconciliation-script`, `maintained-by-metadata-field` (deferrals).

#### data-only-discipline
Knowledge documents and rule files hold data and metadata only. No procedural instructions. Procedural logic lives in skills, format specs, scripts.
What belongs: data, metadata header, brief one-line purpose at top.
What does not: Usage Notes sections, field-level conditional logic, layout/composition rules, self-referential meta-instructions.

### Rule Refresh & Staleness

#### rule-refresh-user-triggered
Axis rule files refresh via builder in `refresh` mode. User-triggered. No automation.

#### rule-staleness-metadata
`last_researched: YYYY-MM` in YAML frontmatter. Builders stamp on every successful run.

#### rule-staleness-detection-at-use
Consuming skills read the stamp on load. If older than threshold, present binary choice:
> "Rule X was last researched N months ago. Proceed with existing information, or perform a research refresh first?"
On refresh: skill invokes builder in `refresh` mode, reloads, continues.

#### rule-staleness-grouped-prompt
Multiple stale rules at skill start: one grouped prompt, not a series.

#### rule-staleness-threshold
9 months as repo-wide constant.
Refs: `staleness-threshold-revisit`, `staleness-per-axis-overrides` (deferrals).

#### organizations-folder
`rules/organizations/`:
- `org_industry.md` (was `registry_company_type`): research scoping for interview_prep.
- `company-slugs.yaml`: slug registry.
Drop `registry_` prefix. Prior `org_maturity.md` plan superseded by Work-state axis (per-entry tagging supersedes org-level modifier).

### Templates & Format Specs

#### format-spec-cv-boundary
Format spec = rendering config (fonts, margins, spacing, bullet chars, file-naming). Deliverable-specific, axis-agnostic.
`temp/format_spec.md` transfers with two cleanups: (1) move embedded python-docx code (lines 95-123) to a script under `scripts/`; (2) parameterize hardcoded name in output filename (line 182), pull from `User_Info.md`.

#### interview-template-artifacts
`interview_completion` and `interview_scratch` exist as blank skeletons (in `templates/`, copied per round) and as populated instances (in application folder).

#### workflow-sequence-diagram-deleted
Old registry's ASCII diagram does not carry over.

### Stack & Infrastructure

#### stack-orchestration
Claude Code native for most workflow. LangGraph approved for the CV generation loop only as a bounded learning experiment.
Constraints:
1. No dual state management. One state model, one integration handoff.
2. If friction beyond initial learning curve materializes, the experiment stops at the CV loop; does not extend to other skills.

#### stack-retrieval
Mixed by content shape. Structured lookup (Python script) for structured documents. RAG reserved for genuinely unstructured content (interview_scratch). Default structured.

#### stack-execution
Skills are markdown. Deterministic logic = Python scripts via Bash. LLM-judgment in skill or LLM sub-agents. Build scripts alongside the skill that uses them. Never use an LLM where a script can verify deterministically.

#### configuration-file
`personal/config.yaml` in nested private repo. Holds key paths, output destinations, future tracker placeholder. YAML. The `name` field is removed (lives in `User_Info.md`).

### Operational Discipline

#### approach-foundation-first
Foundation-up order:
1. Lineage and traceability requirements.
2. Knowledge documents.
3. Session-log and application-ID.
4. Each workflow skill in sequence.
5. Remaining items.
Qualified by `feedback_build_incrementally.md`: per-skill detail at skill build time, not in advance.

#### foundation-execution-order
Hand-edit axis rule files first → finalize knowledge documents next → build axis_builder skills later, only if refresh demand recurs. Builder skills become refresh tools, not validation gates that block progress. Decision driven by avoiding the planning-paralysis pattern that killed the prior build (deferring real work because a hypothetical future skill might do it differently).
Refs: `initial-industry-pack-content-design`, `initial-specialty-pack-content-design`, `cross-axis-reconciliation` (deferral), `approach-foundation-first`, `builders-axis-parity`.

#### decision-filter
Order: value, friction, scalability, learning tiebreaker. Scope creep and gold plating route to "enhancements" list, not inline.

#### global-rules-minimized
`rules/global_rules.md` as single file. Three rules: never fabricate content; failure handling protocol; never proceed with partial content.

#### pacing-consolidation
User-level CLAUDE.md holds general response-shape pacing. Skill approval-gating lives in skill authoring template as Presentation Phase convention.

---

## Foundation Stage

Empty. Stage-specific items populate as builder skills surface them at build time.

## Application Workflow Stage

Empty. role_evaluation, cv_targeted, interview_prep, interview_capture, interview_followup designed at their build time.

## Career Workflow Stage

Empty. career_brief, cv_general, knowledge_update, positioning skill designed at their build time.
