# JD processing rules

Rules for each step that works on a job description after role-intake saves it. Each `## ` section is headed `## <KEY>: <name>`; the key names the step that reads it. Steps never read this file whole: `python scripts/jd_rules_slice.py --key <KEY>` prints this opening text and the sections for that key.

Keys:

- `SPLIT`: splitting each unit of `jd_sentences.md` into parts (the jd-splitter agent, role-extract Phase 2).
- `RANK`: describing the job, grouping the rows into needs and ranking them (the jd-needs-ranker agent). role-extract's QC reads it too.
- `KINDS`: the kinds of row. The jd-needs-ranker agent and role-extract's QC read it, and `scripts/jd_extraction_tables.py` reads the kind list and where each kind lands from the `### N. <name>` headings under `## KINDS: Kinds of row`.

## SPLIT: Units and slots

**Unit:** one sentence of the job description, or one part of a sentence that has semicolons; each part between semicolons is its own unit (S-046a, S-046b).

### Slot definitions

- **Function:** work or a subset of work the role is responsible for doing.
- **Result:** the state or change that is intended to be realized by the function or means.
- **Means:** a body of knowledge, method or tool used to perform a function or bring about a result.
- **Capability:** a trait or ability a person applies to a function or means or to bring about a result.
- **Bar:** the level of experience or competency the candidate must have for a function, means or capability.
- **Qualification:** a quantitative or tangible threshold the candidate holds or has met, such as a credential or stated length of experience.
- **Role shape:** whether the role does the work, operationally manages the people doing it, holds line management of them, influences the work without authority over it, or some combination of those.
- **Scope:** the reach of the role's work: its size or breadth, for whom it is done, with whom, from whom it originates, and where the role sits within the organization or relative to other groups or departments.
- **Setting:** the industry, type of organization, type of department, or other specific environment the work takes place in or the candidate's experience is expected to come from.
- **Employment condition:** a term of the job that the candidate accepts or is eligible for.
- **Boilerplate:** information about the organization, mission or values wording, generic company self-promotion, and legal text.
- **Other:** anything that does not fit the slots above.



