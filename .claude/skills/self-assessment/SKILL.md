---
name: self-assessment
description: Run or rerun the behavioral self-assessment governed by rules/self-assessment/assessment-protocol.md. The protocol owns every method rule (evidence grading, questioning, conclusions, adversarial review, run modes, load limits); this skill is the thin orchestrator - intake, mode selection, filing, and the QC loop (deterministic script plus the qc-self-assessment judgment agent). Fresh runs and reruns are both first-class. Run when the user asks for a self-assessment, or when the annual rerun trigger fires.
---

# self-assessment - run the assessment per the protocol

Thin orchestrator. The single authority for HOW the assessment is conducted is
`rules/self-assessment/assessment-protocol.md`; this skill decides only
sequencing, filing, and QC dispatch. If this skill and the protocol ever seem
to disagree, the protocol wins.

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Read the protocol in full before anything else. It is deliberately short;
  there is no segmented loading. Its rules govern every phase below, including
  pacing (conclusions one at a time, count stated up front) and the load
  ceiling (a sitting ends when the subject says so).
- Plain English to the user. Halt and ask on any failure rather than guessing.
- Paths in commands are absolute (project rule); the runs folder and filenames
  come from `config.yaml` (`paths.self_assessment_runs`,
  `self_assessment` block), never hardcoded.

## Phase 1 - Intake and mode

**Setting up the run.**

- Run intake per the protocol's "Corpus and intake" section, one question at a
  time: evidence sources, source roles, prior runs, scope boundaries, working
  style and filing location (default: the configured runs folder).
- Derive the corpus-limitation statement and confirm the subject proceeds with
  those limits understood.
- Mode: a prior product in the runs folder means rerun; otherwise fresh run.
  The subject can override (a fresh run is always legitimate).
- Output: corpus list, limitation statement, mode, run folder
  (`<runs>/<YYYY-MM>/` for the trail; product at the runs root).

## Phase 2 - Conduct the run

**Running the assessment.**

- Follow the protocol's "Run modes" section for the chosen mode, end to end.
  Extensions (forward-looking pack, impressions forecast) run only when the
  subject's purpose calls for them.
- Working documents carry the trail in the dated subfolder; any subject-directed
  method or register change is logged there with its trigger (protocol rule 11).
- Question-heavy mechanisms get separate sittings (protocol rule 15). At each
  sitting's end, record where the run stands in the trail so the next sitting
  resumes without re-asking.
- Output: trail documents; the consolidated product draft
  `profile_<YYYY-MM>.md` at the runs root, stamped with the protocol version it
  ran under.

## Phase 3 - QC loop

**Checking the product.**

- Deterministic pass: `python <repo>/scripts/self_assessment_qc.py check
  --file <absolute path to the product>`. Fix script findings and re-run until
  clean; these are mechanical and stay internal.
- Judgment pass: dispatch the `qc-self-assessment` agent with the product path
  and the protocol path. For each finding that changes content, show the
  before/after to the user prior to applying (mechanical fills excepted), then
  re-run both passes.
- Bounded loop: after three fix rounds, ship the product marked provisional and
  log the unresolved findings to `design/build_issues.md`; never stall the
  user's workflow.
- Output: QC-clean (or provisional) product.

## Phase 4 - Close the cycle

**Closing out.**

- External check (protocol rule 13): record in the trail which independent
  instrument ran or is designated (cold read, second-user run, second-model
  blind pass); until one runs, the product's inferred conclusions stay marked
  externally unconfirmed.
- Instruments (protocol rule 14): confirm every finding closed in an instrument
  or designated test; registered predictions carry decidable criteria.
- Rerun trigger: check the subject's calendar for the annual rerun event; if
  absent, offer to create it via the connected Google Calendar tools, with the
  subject approving the event details before anything is written.
- State completion: product path, trail path, external-check status, next
  trigger date.
