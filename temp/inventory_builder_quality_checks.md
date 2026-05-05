# Experience Inventory Builder — Quality Checks

Cumulative quality checks from manual reconciliation passes of `personal/knowledge/Experience_Inventory.md`. The `experience_inventory` builder skill must encode these so future creation and refresh do not require manual reconciliation. Each check is a defect class observed during review; checks new to this file should be added inline as future reconciliation surfaces them.

## 1. Structural Integrity

- **PR Industry uses `independent`.** Independent / volunteer projects tag `Industry: independent`, not an industry-pack value (employer sector framing does not apply). Validation on PR-prefixed entries.
- **Empty optional fields render cleared.** `Last Used:` and similar render with no value, not `N/A` / `null` / placeholder text.
- **Type field is controlled vocabulary.** Enum: `{Direct, Contract, Freelance, Military}`.
- **Atomic inventory: one entry per role-context.** A task performed under multiple RLs creates a separate EX entry per RL. Dedup logic scopes within-RL only; cross-RL identical descriptions are intentional, not redundancy.

## 2. Content Quality Within Entries

- **Tense uniformly past.** Lead verb is past tense across all Description fields.
- **No unsupported quantification.** Numeric claims (dollars, percentages, counts, headcount) require user-provided substantiation; otherwise dropped, not estimated. Builder surfaces each numeric claim for verification at build.
- **No fluff phrasing.** Qualifier-heavy phrasing ("successfully delivered", "leveraged best-in-class", "spearheaded transformative") requires concrete substance behind it or gets cut.
- **Readability pass at draft.** Awkward sentence construction is rewritten at draft, not deferred to reconciliation.

## 3. Cross-Entry Quality

- **Redundancy detection scoped within-RL only.** Within a single RL, no two entries describe substantially the same work. Identical descriptions across different RLs are preserved per atomic inventory.
- **Impact ≠ Description restated.** The Impact line carries only what is beyond the Description. Strip from Impact (not outcomes): audit/diagnostic findings (move to Description or Context), pattern descriptions (Context), qualifier clauses (Context), mechanism narratives (Description), purpose/aspirational framing (drop; value-type tag carries it), attribution caveats (Context).
- **Impact has multiple legitimate forms.** Quantified outcome; bounded qualitative outcome; or strategy/research/roadmap impact (alignment, decision enablement, optionality created, risk surfaced, knowledge produced). Production deployment is not required for Impact to be present.
- **Context trimmed to CV altitude.** Cut mechanics (step/person/function counts when generic descriptors suffice), colorisms restating plain claims, implementation tactics, and designer-decision defenses. Keep prior state, constraint envelope (resource model, headcount, organizational positioning), and load-bearing scope bounds.
- **Bare-tag Impact: substantiate or keep bare.** An entry with `Impact: <value-type>` and no body must either gain a substantiating body at build time or stay bare. Dropping the Impact line entirely is not the convention. Builder flags bare-tag Impact for user resolution.
- **Multi-value-type Impact prefix permitted.** Impact value-type prefix may be a single value or comma-delimited list (e.g., `Impact: Capability Building, Quality Improvement, Risk Reduction` or `Impact: Capability Building, Risk Reduction: <prose>`). Multi-value reflects work that produces value across multiple types. Per `impact-field-semantics-2026-05`.
- **Restructure license at audit time.** Status-reached outcomes mistakenly placed in Description (e.g., "Developed roadmaps that shaped functional priorities") move to Impact during reconciliation. Activity verbs and methodology stay in Description; realized outcomes move to Impact. Same applies to outcomes mistakenly placed in Context — move to Impact when they describe a status reached, not a situational frame.
- **Per-RL completeness.** Every RL in Section 7 must produce at least one retrieved entry in any generated CV. Dropped roles read as employment gaps regardless of retrieval-relevance score. cv_targeted enforces minimum-one-per-RL; if retrieval surfaces no leadership-translatable bullets, include 1-2 bullets minimum framed as scope/context. Concurrent roles fold under one company header with title concatenation ("Title A / Title B (concurrent)"). "Earlier Professional Roles" section acceptable for older roles, but must list each role with company and dates. Apply at draft time, not post-hoc.
- **Concurrent-role tag drift.** When a role is concurrent with another role at the same employer, work specific to the concurrent role tends to drift into entries tagged to the primary role. Builder must check zero-entry RLs against entries tagged to concurrent peers for drift candidates (e.g., Infosario Business Champion work tagged to the concurrent Process Technology Specialist role). 2026-05-04 reconciliation: RL-008 had zero entries; relevant work was tagged to concurrent RL-009.

## 4. Voice Consistency

- **Lead-verb agency matches Level.** Leadership-level entries do not lead with hedging verbs (assisted, supported, participated in, contributed to). IC-level entries do not lead with claim-strong verbs (spearheaded, championed, pioneered) unless underlying work supports it. Builder validates lead-verb category against the Level field.
- **Implicit third-person, no first-person.** No "I", "we", "the team and I". Implicit subject + past-tense verb.
- **No em-dashes in prose fields.** Em-dash (—) prohibited in Description, Impact, Context. Aligns with global writing-style rule and CV format-spec rule (`cv-format-spec-from-axes`). Replacement principles when fixing existing content: clause-attaching connectors → comma; appositive expansions → colon; standalone clauses with semantic break → semicolon or period; parenthetical asides → parentheses.
- **Bold on Description only.** Description value wrapped in `**...**`; no other field bolded.
- **Parallel construction within sub-sections.** Entries within a single sub-section (e.g., Clinical Monitoring & Site Management) follow roughly parallel verb → object → modifier shape. Outliers flagged.

## 5. Coverage

- **Per-RL entry count proportional to role depth.** Each RL's entry count and content scope are proportional to tenure, scope, and seniority. Builder reports per-RL entry count + content-scope summary at build/refresh; flags outliers (sparse long roles, dense short roles).
- **Atomic decomposition of bundled umbrella entries.** When an umbrella entry packs multiple distinct activities into one Description (e.g., "led adoption through training, consultation, and liaison"), builder flags for decomposition into one entry per activity. Umbrella role-framing belongs in Context of one of the atomic entries, not as its own bundling Description. 2026-05-04 reconciliation: EX-155 ("Served as Business Champion: led adoption through training, end-user consultation, and liaison") decomposed into 4 atomic entries (create+deliver, support-architecture training, surfacing at meetings, feedback loop).
- **Leadership role coverage prompts.** For any leadership-tagged RL, builder prompts user for the dimensions that are commonly thin even when the role has moderate density: (a) people management of direct reports (size, role mix, accountability scope); (b) escalation handling; (c) sponsor/PI/cross-functional stakeholder communication; (d) approval and review work (regulatory documents, monitoring reports, study deliverables); (e) cross-region or cross-functional coordination. 2026-05-04 reconciliation: RL-011 (Regional CTM, 25 months) had 8 entries and was missing all five categories; user-prompted enumeration surfaced 9 additional atomic entries.
- **Sections 5 & 6 classified against axis vocabularies.** Tools (§5) and industry-exposure content (§6) classified against industry-pack and specialty-pack vocabularies for downstream retrieval. Tracked under deferral `inventory-builder-research-classification-sections-5-6`.
