# Self-Assessment Protocol

**Used by:** self-assessment (skill), qc-self-assessment, scripts/self_assessment_qc.py (mechanical rules mirrored in config.yaml's `self_assessment` block)

**Version:** v2, 2026-07-10. v1 (2026-07-07, the version the 2026-07 profile ran under) is in the personal repo's git history (originally `operator/method.md`). Every v2 change traces to the 2026-07 run's trail: `personal/self-assessment/2026-07/yield_audit_2026-07.md` (internal audit) and `personal/self-assessment/2026-07/method_research_2026-07.md` (external research, adoption decisions).

The rules for conducting a behavioral self-assessment of a person (the subject) from corpora they designate plus direct questioning. Rules 1-12 were earned during the 2026-07 run; each exists because its absence produced a documented error. Rules 13-15 and the run modes were adopted 2026-07-10 from the research pass. This file is generic: it hardcodes no repositories, no file names, and no facts about any subject. Runs and their trails file per the dispatching skill or the subject's instruction.

## What this is

A profile of how the subject thinks, works, communicates, and changes, built from evidence rather than impressions: strengths, weaknesses, traits, tensions, trajectories, practical edges, and open moves. The assessor drives; the subject is a queryable evidence source and the final authority on ground truth only they can see.

## Corpus and intake

The subject points the assessor at one or more corpora, in effect: "this is work I do or interests I pursue that could be helpful describing me." Whatever those are become the inputs: repositories, folders, drives, apps, scripts, documents, collaboration records. The flex lives in intake and evidence grading only; there is no per-corpus-type machinery.

At intake the assessor derives a corpus-limitation statement: what this corpus can and cannot show about the subject (time window, life contexts covered, whether dated series exist for change-over-time analysis). The subject proceeding with those limits understood is the acceptance criterion. A thin corpus produces a smaller product, never more questions.

## Evidence classes

Every claim carries exactly one grade, stated with the claim:

1. **Observed**: visible in the record (files, version history, timestamps, work products, connected accounts).
2. **Attested**: stated by the subject under questioning, weighed before use.
3. **Inferred**: assessor judgment drawn from what is present, marked with a confidence level.
4. **Untested**: named as unknowable from the available channels.

There is no fifth class. Inference from absence is banned: a scan of any corpus proves only absence in that corpus, never absence in the person. Every would-be absence finding converts into a question to the subject instead.

Confidence levels on inferred claims are anchored, not impressionistic:

- **High**: multiple independent evidence lines converge and no rival reading survives the counter-case hunt.
- **Moderate**: the reading fits the evidence better than rivals, but a rival survives or corroboration is a single line.
- **Low**: plausible on one evidence line with rivals equally viable; floated as a probe or marked speculative, never load-bearing.

## Rules

1. **Record first, questions second.** Mine the dated evidence (version history, rule sequences, ledgers, artifacts) before asking anything. Queries are for what the record cannot show, not for what the assessor has not yet read. Queries ask for specific incidents (what happened, what the subject did, what came of it) rather than general self-characterization; one incident per claim, and an incident thread that runs long continues next sitting.
2. **Scan boundary must match claim boundary.** Before asserting "no X exists," confirm the scan covered everywhere X could live, including outside the visible corpus. If it cannot, ask.
3. **Attestation is data, never conclusion.** Triangulate the subject's statements against the record; corroborate where checkable (dates against ledgers, artifacts against claims). Never transcribe a self-account verbatim into a finding; that converts the assessment into one the subject authored. Credence premiums attach to the cost of a statement's original utterance, never to its valence alone: a contemporaneous admission made to another person at real social cost earns extra credence, while in-assessment self-criticism from a subject with a documented self-critical practice is identity-consistent record-completion and earns no automatic premium; its weight comes from corroboration. Self-favoring statements need corroboration. A single attested instance is an instance, never a disposition. Weight comes from substance and corroboration, never from fluency or length: an articulate answer does not outweigh a terse one of equal evidentiary content.
4. **The assessor owns every finding.** Findings are drawn from the whole evidence picture. The subject verifies facts; they do not draft conclusions and they do not approve them.
5. **Probes while the record is open; conclusions after it closes.** During evidence-gathering, tentative patterns may be floated to draw out missing context, labeled explicitly as probes, never as findings. Disconfirming evidence is sought during gathering, not only after synthesis. The subject's role at that stage is adding context and correcting facts. Once both agree the record is complete for the declared scope, the assessor draws conclusions: score the independent evidence pieces separately before composing any gestalt; before a pattern becomes a finding, hunt the corpus for cases that break it; a coherent story does not raise a confidence grade, only evidence strength does. Conclusions are then presented one at a time (for scrutiny, with the count stated up front). The response sought on each is "what factual error or missing information does this rest on," never approval. Per-conclusion sign-off creates assessor-side anticipatory shaping, which leaves no trace and cannot be self-audited; separating fact-verification from conclusion-drawing is the structural defense. Silence is never assent on a factual challenge left open.
6. **Re-derive under challenge; never reverse on pushback alone.** When the subject disputes a finding, rebuild it from first principles with the new input as data. Change the verdict only when evidence changes it, and say what changed.
7. **Repair over rebuild when defects are localized.** Discriminator: structural defects (the flaw infects everything built on it) justify a fresh start; enumerable, localized defects get repaired in place with the supersession recorded.
8. **Respect declared boundaries.** When the subject places a topic out of scope, mark dependent mechanisms "undisclosed by the subject" and never guess at the content or probe uninvited.
9. **Working documents carry the trail; the product is clean and readable.** Trail documents record supersessions, evidence grades on dead versions, and revision triggers. The product carries none of that: no revision notations, no process narration. Second-person voice. No em dashes. No "not X, it's Y" constructions. Written for a cold reader: short paragraphs in like-chunks, series promoted to bullets, no sentence that needs re-reading, and no coined shorthand the document has not first defined; the subject gets a pronoun, not a role-word.
10. **Verify before recording anything as done.** Checkable claims get checked (a named artifact gets looked for; a date gets matched to the ledger) before a finding is built on them.
11. **Neutral intake, owned conclusions.** The record and the subject's accounts enter without evaluative grading: no adjectives grading the subject's actions or artifacts, no success/failure verdicts on events, no unverified population comparisons. Attested feelings are data ("the subject reports pride in X") and are never extrapolated into performance judgments. Detail lists are summarized at category level and marked as summarized, because a partial enumeration reads as exhaustive. Identifying specifics (employers, named products) generalize in the product, with the record as the lookup path. Conclusions belong to the assessor and are never neutralized away; inferred conclusions carry tentative wording in the sentence as well as the grade, and forward-looking sections are framed as "may." Apply this standard at first drafting, never as a revision pass over a finished product: a retrofit leaves a subject-directed register change on the record and a superseded version underneath, both of which an adversarial read must then litigate. The standard trades direct falsifiability for neutrality (a hedged, generalized product verifies less directly), so the product must state that the trail and underlying record remain the verification path. Any subject-directed change to method or register is logged in the trail with its trigger.
12. **Adversarial passes obey the same evidence rules.** After synthesis, run deliberately hostile readings and grade each into what survives scrutiny and what does not. Hostility is a lens, never a license: a hostile framing may not conclude from absence, invent framing the record doesn't support, or drift from assessing the person into auditing their job performance or life choices. The adversary does not work in a vacuum: it interacts with the subject to complete its information before concluding, and every challenge must cite the specific profile content it disputes and state why an alternative reading exists or why that content may not contribute to an accurate profile. Grounded, never friendly. Also read the assessment process itself adversarially (who trained the assessor, who gated what); any finding the process cannot validate from inside gets marked provisional with an external test designated. The subject's live responses to the adversary are themselves evidence; mine them. The pass is hygiene, never independence: it shares the assessor's blind spots, and independence comes only from rule 13.
13. **One independent check per cycle.** A cycle is not complete until at least one instrument outside the assessor-subject pair has run: a cold read by an untrained reader, a run with a second user, or a blind pass by a different model over the same evidence with divergences flagged. Until one has run, every inferred conclusion is marked externally unconfirmed.
14. **Findings close in instruments.** Every confirmed finding ends with an instrument (a field that collects data, a ledger, a dated prediction) or a designated external test. A prediction registers only with a decidable pass/fail criterion written at registration; grading at the next run is against the criterion, never impression. A finding closing with neither is flagged unscoreable at drift time.
15. **The load ceiling is part of the method.** Question-heavy mechanisms get separate sittings; a sitting ends when the subject says so, not when a pack completes. Session burden is the documented top killer of practices like this one; when thoroughness and load conflict, load wins and the product shrinks.

## Run modes

**Fresh run** (first-class; never priced as the expensive path). Order: intake (corpus designation, limitation statement, scope boundaries, prior-run check) → mine the record → audit self-presentation against behavior, only if self-authored claims exist → complete the record and derive findings → synthesize (master traits, tensions, where the subject may thrive, practical edges, open moves, separating moves that close with a control from moves that close only by doing the uncontrolled thing) → adversarial pass → consolidate. The core should fit a small number of sittings; depth is earned over runs, not front-loaded.

Extensions, run only when the subject's purpose calls for them: a forward-looking pack (fixed core: pre-mortem, fail conditions, succeed conditions for the subject's next chapter, plus at most three record-derived avoidance candidates, hard-filtered against what the record already answers); an impressions forecast where received-feedback data and an evaluative context (such as interviews) exist to score it against.

**Rerun** (light by design). Triggered by a fixed calendar event, not memory. Order: grade the registered predictions against their criteria and read the accumulated instrument data (mechanical, order-free) → read only the new evidence since the prior run and draft what it shows, before opening the prior product → open the prior product and drift-compare: which findings held, which moved, whether the open moves were taken. The rerun product leads with the drift comparison; that comparison is the felt payoff that makes a third run happen. A light year is a valid year. A rerun that produces nothing genuinely new is the signal to shrink or change the method, never to keep performing it.

## Product structure

How to read it (evidence classes and confidence anchors, corpus-limitation statement, neutrality standard, and three plain labels: this assessment was requested and run by the person it describes, with no independent party ordering or reviewing it, and findings that favor the subject carry that tilt; the corpus is self-chosen and cannot show what was never put in it; the adversarial pass is hygiene, not independence) / who the subject is / core pattern / cognitive style / how they relate to people / master traits / verified strengths / where they may thrive / weaknesses / tensions / how they have changed / where it may bite (practical edges) / open moves / one line. The product names the protocol version it ran under.

## Filing

Each run gets a dated subfolder for its trail; the product lands at the run folder's root with the date in the filename, beside prior products. The rerun is itself the scheduled drift check on the subject.

## Amendments

The protocol must not grow without demonstrated yield; prefer add-one-cut-one; subject time per run is the binding constraint. An amendment bumps the version and is logged in the current run's trail with its trigger.
