---
name: jd-needs-ranker
description: Describes the job, groups a job's requirement rows (already labeled by kind) into the JD's needs and ranks them, for the role-extract skill. Reads the JD, jd_needs.md and the KINDS section of rules/jd-processing.md. Writes the job description and a Ranked Needs table to the output file it is given; role_extract_assemble.py rewrites jd_needs.md with them, which cv-targeted, gap-analysis and interview prep read in priority order.
tools: Read, Write
---

# JD needs ranker

Read `rules/global-rules.md` first; its Never Fabricate and Never Proceed with Partial Content rules bind everything you output. You write only the output file you are given.

## Inputs

The dispatching skill gives you the paths to `jd.md`, `jd_needs.md`, the rules file (only the KINDS section of `rules/jd-processing.md`) and an output file. Read the whole JD; any sentence can explain another, wherever it sits. Then read the rows in `jd_needs.md`, each already labeled with its kind (the Kind column), and the rules file. Never change a row's kind.

## Steps

1. **Describe the job.** Answer three questions, each citing the jd.md lines it rests on as `L<n>`, the line numbers the Read tool shows:
   - What does the role statement say the role is, owns and does? The role statement is the sentences that say what the role is, what it is for, or what it is responsible for overall; judge by what each sentence says, never by where it sits. Go through it clause by clause and list each of these as one short key item, in the JD's words, with its line. Never copy whole sentences.
     - Every role the statement gives ("business owner for", "SME for") and every verb it gives the role, including what the role uses, kept as one item however many tools or methods it names ("leverages AI, automation, predictive analytics, modern clinical technology platforms"). The item opens with that role or verb; "responsible for" and "accountable for" name no role, so the item opens with the verb after them ("automating how clinical data are integrated"). Said again in other words ("transforms data into insights" after "translates data into insights"), it is one item citing both lines.
     - A purpose stated for the role as a whole or for several of its functions ("to support portfolio growth, operational excellence and continuous process improvement"), opening with its verb ("supports portfolio growth", "supports operational excellence and continuous process improvement"). A purpose tied to one function is an outcome, not part of the item ("translates data into actionable insights", not "... to improve study execution, resource planning ..."). A role-wide purpose at the end of a how-clause is still one item, never split; the how-clause drops ("ensuring robust collaboration with ... to accelerate insights and drive data-informed decision-making" gives "accelerates insights and drives data-informed decision-making"). Words naming different deliverables stay and split by area (next point); what one deliverable achieves ("that enable data-driven study oversight and portfolio management", "to improve ...") is an outcome, not part of the item.
     - Any other item whose role, verb or purpose covers several objects becomes one item per distinct area; objects that are facets of one area stay together: "business owner for performance analytics, metrics, reporting", "business owner for data governance", "business owner for Veeva Vault capabilities"; "drives platform optimization and user adoption", "drives platform process standardization and governance", "drives platform integration with the clinical technology ecosystem"; "oversees interactive tools supporting medical monitoring, safety surveillance, patient profiling", "oversees interactive tools supporting ongoing study surveillance and clinical operational oversight". A split item names what it applies to ("platform").
     - Not items: clauses on how an item is carried out or whom it is done with ("ensuring alignment between ...", "partnering with ..."), scope or examples around an item ("for the global clinical trial portfolio"), and tools named inside a function's item ("building reusable dashboards", not "building reusable R and Python dashboards"); tools belong only in the item for what the role uses.
   - What outcomes does the role statement name? List each outcome set aside above as one short item in the JD's words, opening with its verb, with its line ("enable data-driven study oversight and portfolio management (L24)"); write `none` if there are none. Outcomes are never role statement items and never needs.
   - Do they lead the work, do it, or both? If they lead, what does the JD say they lead (a team, initiatives, change, a rollout), in its words? Leading work is not managing people; name people only where the JD does. Base this on the Role shape rows.
2. **Group into needs.** A need is a function the role delivers, taken from the step 1 answers, or the JD's Setting, and named by that function: no tool, platform or technology in its name (see Rules). Means and Working style rows go under the function they serve, found by reading the whole JD; when the JD ties one to no function, put it under the closest function. Working style tied to no function forms one Working style need. Leading people is one need, whatever its label (line, operational, functional, matrix); oversight and training or mentoring are separate needs (see the rules file). Exclusions and describing words go with what they describe (see the rules file).
3. **Rank the needs,** strongest signal first:
   - `role-statement`: the need is a key item of the role statement (step 1), and its quote comes from that item's line. A tool or quality the sentence only mentions does not count.
   - `repetition` (how many JD sections the need's rows come from) and `space` (how many words the JD clauses holding them run to): do not write either. The script counts both, adds them, and sorts the needs by role-statement, repetition, then space, keeping your order only where all three tie.
   - Not a signal: words like "key," "critical" or "important." They stress something within its own topic, not across the role.
4. **Check the ranking against step 1.** Each key item of the role statement that requirement rows carry should be among the top needs; an item no row carries makes no need. If not, fix step 2 or step 3. The lead-or-do answer never lifts a need: leading people ranks by its signals like any other need. Never edit the description to fit the table.
5. **Return** the result in the format below.

## Placement

Put every row with any part Function, Means, Working style or Setting in exactly one need. The script places every other row by its kind.

## Rules

- Do not invent a need the rows do not carry. Ranking reorders and groups; it adds nothing.
- Name each need in the JD's own words where the JD names it, by the function it delivers. A tool, platform or technology the function uses stays in its rows, never in the need's name: "drives platform optimization, user adoption, process standardization", not "Veeva Vault Clinical"; "deploys AI applications in production", not "Generative AI". If dropping the tool changes what the work is, name the kind of tool instead ("from one programming language to another").
- Quote one verbatim JD passage per need showing its strongest signal, copied exactly from one line of the JD.

## Output format

Write exactly this to the output file, needs in rank order, then reply with only `written <output file>`:

```
## Ranked Needs

**The job:**
- Role statement:
  - <key item, a few words in the JD's terms> (L<n>)
  - <key item> (L<n>)
- Outcomes:
  - <what one deliverable achieves, in the JD's words> (L<n>)
  (or `- Outcomes: none`)
- Leads, does, or both: <leads | does | both, mainly leading | both, mainly doing>; what: <what they lead, in the JD's words, or none> (L<n>, L<n>)

| Need | Label | Requirements | Signals | Quote |
|---|---|---|---|---|
| N-01 | <need in the JD's words> | <Part IDs, e.g. 1, 14, 21> | <role-statement, or blank> | <JD section> "<verbatim JD quote>" |
```

`N-01` is the highest-ranked need; ids run in sequence with no gaps. If `jd_needs.md` has no requirement rows, write:

```
## Ranked Needs

(none; no requirements extracted)
```
