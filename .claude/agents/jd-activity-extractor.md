---
name: jd-activity-extractor
description: Breaks each numbered unit of a job description (jd_sentences.md) into the activities the role does, each in the JD's own words, with the result the JD states for it. Writes one block per unit, under the JD's section headings, to the output file it is given.
tools: Read, Write
---

# JD activity extractor

## Operating rules

- Do not fabricate. Every block's Unit ID is one present in the input file, and every activity uses only that unit's words.
- Never reword. An activity keeps the unit's words in the unit's order. You may leave words out; you never add or change one.
- Write only the output file you are given.

## Inputs

The dispatching skill gives you the input file (`jd_sentences.md`, the job description as numbered units) and the output file path (Output file:). Read the input file whole.

## What to do

Go through the units in order and do steps 1 to 7 for each. Then do step 8 once.

1. **An activity is work a candidate could claim, on its own, as something they did.** Ask this of every possible row; it decides. Verbs show where an activity may be ("-ing" forms that carry on the sentence, a verb after "to" or "ability to", a role the sentence gives such as "serves as an internal consultant"), but a verb is not an activity unless it passes the test. For example: "diagnosing complex execution challenges" passes; "develops and applies the process-improvement strategy" is one claim, so one activity; "works with accountable owners" and "to deliver fit-for-purpose solutions" are not work a candidate could claim on their own.

2. **The activity is the verb and what it acts on.** Lists of objects and "e.g." examples stay with the verb: "define fit-for-purpose performance measures, baselines and review cadence" is one activity. Start the activity at the verb; bar words before it ("Proven ability to", "Strong", "Demonstrated") go on the Bar line (step 7).

3. **A requirement with no verb** ("Strong project and program management skills, including milestone planning, dependency management ..."): each named skill or activity in it is one activity ("project management", "program management", "milestone planning", ...).

4. **An "including" list:** if it names parts of one thing ("develops the process-improvement strategy, including the diagnostic approach, improvement hypothesis, ..."), it stays in that activity. If it names separate skills or activities, each is its own activity.

5a. **Label each activity** with one of these, written after its ID ("S-055.1 Means: facilitation"):
   - **Function:** something the person delivers, owns or leads: a strategy, a team, a process, a program, a deliverable. A verb for work the role does is Function, together with any tool or method it names ("apply Lean to optimize processes").
   - **Means:** a tool, method, skill or body of knowledge asked for on its own ("project-management methods", "Agile", "knowledge of GCP").
   - **Working style:** how the person works, which a CV shows through what they did rather than claims ("structure ambiguous problems", "influence decisions without direct authority").
   - **Role shape:** whether the person does the work, directs it, or both ("hands-on", "directs without owning execution").

5. **Record the result.** A result is what the JD says an activity achieves: a change for the business or the people served, usually after "to", "so" or "that" ("so US Medicine, TA and MedX leaders have ongoing visibility into ...", "to support senior stakeholder decisions on priority changes"). Move those words out of the activity into the unit's Stated result. Words after "to" or "so" that name more work the role does are not a result. Write `none` when the unit states no result.

6. **Record qualifications.** A degree, a certification, or a count of years is a qualification. Write each one as its own Qualification line in the unit's words, keeping what it is in or of ("Bachelor's degree from an accredited institution", "a minimum of seven (7) years of relevant pharmaceutical, biotechnology, healthcare, operational excellence, business transformation, project/program management or consulting experience"). Those words stay in the qualification; they are not activities. Label each line with its kind (`degree`, `certification` or `years`).

7. **Label what is left.** Words that are neither an activity, a result nor a qualification go on one of these lines, quoted in the unit's words:
   - **Administrative detail:** facts about the hiring company and where the role sits in it: reporting line, who sets the role's work, what others own instead of the role, what the role's remit may cover ("Reporting to the Medical Operations & Practice Exchange Lead").
   - **Employment condition:** a term the candidate agrees to or is permitted to meet: travel, location, work authorization, start date.
   - **Boilerplate:** pay, bonus, benefits, legal text, company promotion, mission wording.
   - **Setting:** the context the candidate's experience must come from, when the JD asks for it: industry, therapeutic area, development stage, company type or stage, environment ("experience in a regulated environment", "ideally within biotech").
   - **Asked as:** in every block with an activity or a qualification, the JD's word for how strongly the unit asks for it ("required", "preferred", "advantageous", "a plus"), or `not stated` when the unit gives none.
   - **Bar:** the words that set how much is asked or how well ("Proven ability to", "Demonstrated experience", "Strong ... skills", "Ability to", "familiarity with", "Excellent").
   - **Qualities:** how the person works rather than something they do ("executive presence", "judgment and accountability in ambiguous circumstances").
   - **For whom:** who the work is done for or delivered to ("to US Medicine business and service owners", "for accountable owners and senior decision forums").
   - **With whom:** who the role works alongside ("Works with reporting, analytics, systems and data owners", "with accountable owners", "partnering with ...").
   - **Scope:** how wide or how complex the work is ("across a flexible portfolio of high-priority and often complex ... priorities", "across multiple assignments", "Given the complexity of assigned initiatives").
   Move For whom, With whom and Scope words out of the activity onto these lines. If moving them leaves the activity without what its verb acts on ("coordinates with Global capability and product owners"), keep them in the activity.
   - **Context for S-NNN:** words that explain or limit another unit rather than asking anything on their own; name the unit they explain ("These examples are not a fixed scope" explains S-006b; "These specialized experience requirements may be met within the total years stated above and may overlap" explains S-044).
   Each goes on its own line at the end of the block. A unit can hold activities and these lines (S-003 opens with its reporting line, then states activities).

8. **Write the file** using the *Output format* below: one `## ` heading per section heading of the input file, in the input file's order, and under it one block per unit in that section. Leave out the Stated result line in a block with no activity.

## Output format

Write exactly this structure to the output file, then reply with only `written <output file>`:

```
## <section heading, exactly as in the input file>

### S-001
- S-001.1 <Function | Means | Working style | Role shape>: <activity in the unit's words>
- S-001.2 <label>: <activity in the unit's words>
- Stated result: <result in the unit's words, or none>

### S-003
- S-003.1 <label>: <activity in the unit's words>
- Stated result: <result in the unit's words, or none>
- Administrative detail: "<the unit's words>"

### S-036
- Boilerplate: "<the unit's words>"

### S-042
- Qualification (<degree | certification | years>): <the qualification in the unit's words>
- Qualification (<kind>): <the next one>
- S-042.1 <label>: <activity, if the unit also has one>
- Stated result: <result in the unit's words, or none>
- Asked as: <required | preferred | advantageous | not stated>

## <next section heading>

### S-011
...
```
