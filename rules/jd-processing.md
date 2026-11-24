# JD processing rules

Rules for each step that works on a job description after role-intake saves it. Each `## ` section is headed `## <KEY>: <name>`; the key names the step that reads it. Steps never read this file whole: `python scripts/jd_rules_slice.py --key <KEY>` prints this opening text and the sections for that key.

Keys:

- `SPLIT`: splitting each unit of `jd_sentences.md` into parts (the jd-splitter agent, role-extract Phase 2).
- `RANK`: describing the job, grouping the rows into needs and ranking them (the jd-needs-ranker agent). role-extract's QC reads it too.
- `KINDS`: the kinds of row. The jd-needs-ranker agent and role-extract's QC read it, and `scripts/jd_extraction_tables.py` reads the kind list and where each kind lands from the `### N. <name>` headings under `## KINDS: Kinds of row`.

## SPLIT: Splitting units into parts

**Unit:** one sentence of the job description, or one part of a sentence that has semicolons; each part between semicolons is its own unit (S-046a, S-046b).

**Part:** one requirement inside a unit: something a reader would check on its own. A unit that asks nothing is one part (rule 1). Most units are one part.

**Units that ask nothing**

1. **Nothing asked: one part.** A unit that asks nothing of the candidate (company, pay, benefits, legal text, how the role is set up) is one part.

**Lists.** Rules 2, 3 and 4 keep text whole and win over rule 5.

2. **Only the outer list splits.** A list inside an item or in parentheses stays with that item.
3. **Examples stay whole.** Words after "e.g." or "such as" stay in the part they illustrate.
4. **"Or" lists stay whole.** Items joined by "or" or "and/or" are one part, because any one meets it. "R, SAS, Python, or SQL" is one part.
5. **"And" lists split what a CV could claim alone.** This covers every "and" list, including one after "including". Split when each item is a named thing a CV could claim without the others: a skill, tool, standard, regulation, language, credential or field of knowledge. "Knowledge of ICH, GCP, FDA, and 21 CFR Part 11" is four parts; "CDISC standards, including SDTM, ADaM, and USDM" is three; "Excellent written and verbal communication skills" is two; "Strong judgment and accountability" is two. Keep whole when the items are activities, or the topics of one activity. "Define the problem, establish performance measures, identify root causes, and lead implementation" is one part; "Establish standards for data governance, quality, and traceability" is one part.
6. **An "including" tail of activities is its own part.** When "including" is followed by activities or details rather than named things, the words from "including" to the end of its list are one more part, whether they follow a skill, a list or a duty. Split any "and" list before it by rule 5 first. "Strong project and program management skills, including milestone planning, dependency management and vendor coordination" is three parts: project management skills, program management skills, and the "including" words.
7. **A "while" clause is its own part.** The words from "while" to the end of the unit are one more part, with or without a comma before "while". "Supports adoption of proven approaches while documenting where variation is intentional" is two parts.

**Separate requirements**

8. **Separate requirements split.** A degree, each year count, an experience requirement and a track record are each their own part. "Bachelor's degree required, with a minimum of seven (7) years of relevant experience" is two parts; "10 years in the industry, with at least 5 years in people management" is two parts. Qualifiers such as "with measurable results" stay.
9. **An optional add-on splits.** In "..., preferably in a pharmaceutical or biotech environment", the "preferably" words are their own part.

**Words every part keeps**

10. **Shared words go on each part.** Words that apply to every part go on each part. Examples: a label before a colon ("Clinical Data Knowledge:"), a lead-in ("Knowledge of", "Experience with"), a shared noun ("certifications"), a scope at the end ("within data, analytics, and reporting solutions"), a purpose at the end ("to support senior stakeholder decisions on priority changes"), a condition or purpose at the start ("Given the complexity of assigned initiatives,"). A condition or purpose at the start also goes on the "including" and "while" parts of rules 6 and 7; a lead-in such as "Expertise in" or "An understanding of" does not go on those parts; a label before a colon and a purpose at the end still do. A reporting line or other fact about how the role is set up ("Reporting to the Medical Operations & Practice Exchange Lead,") is not a condition and stays only on the part it opens. In "Given the complexity of assigned initiatives, the Process & Solutions Lead develops and applies the process-improvement strategy including the diagnostic approach, improvement hypothesis, ...", the "including" part starts "Given the complexity of assigned initiatives,". "Clinical Data Knowledge: Thorough understanding of clinical trial workflows, phases (Phase I–IV), data streams (EDC, eCOA/ePRO, lab data, biomarkers), and foundational clinical data structures (CDISC SDTM and ADaM)" is four parts, each starting "Clinical Data Knowledge: Thorough understanding of".
11. **Bar words stay with their part.** Bar words set how much the job description asks, or mark something optional. Keep each one with the part it belongs to. Examples: "familiarity with", "exposure to", "understanding of", "ability to", "N years", "preferred", "preferably", "ideally", "a plus", "nice to have", "desirable", "advantageous".
12. **Parts keep the unit's words in the unit's order.** Add, reword or move no word. Together the parts use every word of the unit, except "and", "or" and "and/or" where they join the parts. Shared words appear on each part (rule 10).

## KINDS: Kinds of row

Every requirement row, or each part of a row that mixes kinds, gets exactly one kind. The kind decides where the row goes in the ranked needs (`jd_needs.md`). Label by what the words do in the JD sentence, not by the topic they are about. Read the whole JD: a row's meaning can depend on another sentence.

The wording lists come from the requirement rows of past applications. They show typical wording; they do not limit a kind. When wording is not listed, apply the definitions and tests.

### 1. Function

Something the person delivers, owns or leads. Leading people is a function. Each function is a need, ranked.

- **Strategy and roadmap:** define, own or execute a strategy, vision or roadmap (analytics, AI, data, product, technology, monitoring, inspection readiness); strategic planning; portfolio planning; set priorities and goals; align investments with company priorities; translate strategy into execution
- **Building a function or capability:** build a team or function from scratch; build a Center of Excellence; scale a function; operating models, playbooks, intake frameworks, service levels; repeatable approaches
- **Leading people:** directing the work of people on the role's own team, whoever pays them (employees, or FSP staff working in-house as team members). Line, operational, functional and matrix leadership and people management are all this one function; never split by those labels. Wording: lead, manage, develop a team; recruit; line management; direct reports; performance management; manager of managers; develop future leaders; foster a culture of accountability, innovation or improvement; train or mentor the role's own team
- **Training and mentoring:** train, mentor, coach or give technical guidance to people the JD does not place on the role's team. Not leading people: training and mentoring carry no authority over the person.
- **Analytics, reporting and visualization:** design and deliver dashboards, patient profile tools, data review tools, monitoring and safety tools; executive and portfolio dashboards; KPI and metrics frameworks; self-service analytics; reporting frameworks; translate business or clinical questions into analytics; predictive analytics; decision-support tools
- **Data engineering and platforms:** data pipelines; automated ingestion, transformation, validation; data models; data integration and standardization; data migration; data products; reusable libraries, packages, templates; governed data access; business ownership or administration of a platform
- **AI and machine learning delivery:** design, deploy, maintain models and platforms; take AI applications from proof of concept to production; LLM applications, RAG pipelines, agents; identify, pilot, scale use cases; AI business cases; AI governance and model validation
- **Quality, standards, governance, compliance:** SOPs, work instructions, standards; data governance; inspection and audit readiness; root cause analysis, CAPA; validation; risk management frameworks
- **Oversight:** oversee the work of an external vendor, CRO, FSP provider, consultant or partner, or of in-house staff the role does not lead; the need names who is overseen. Not leading people. Vendor oversight models and KPIs; vendor selection, RFPs, bid defense, SOW review; alliance and partnership management
- **Program and project management:** manage a portfolio of projects; lead cross-functional initiatives; manage workstreams end to end; track timelines and risks; lessons learned
- **Process improvement:** drive process improvement, standardization, simplification; continuous improvement; automation for productivity
- **Change management and adoption:** lead organizational change; drive adoption of processes, tools, platforms; training and enablement; champion or super-user networks; communities of practice; raise data literacy
- **Technology evaluation:** evaluate and select technologies, platforms, AI solutions; define requirements and adoption criteria; modernize platforms
- **Executive advisory:** recommendations to senior leadership; present to executive teams; trusted partner or advisor to executives; support leadership decisions; influence strategic decisions through data
- **Representation:** represent the function in committees and forums; represent the company in industry groups; represent the function in audits and inspections; serve as subject matter expert
- **Financial management:** budget; P&L; resource forecasting; resourcing models; investment planning
- **Customer implementation and consulting:** lead customer implementations; onboarding; configuration; integrations; consultative discovery
- **Strategy analysis:** analyses of R&D priorities and portfolio; benchmarking; competitive intelligence; market assessments
- **Clinical operations delivery:** risk-based and centralized monitoring; build a monitoring workforce; monitor study performance; data cleaning and database lock
- **Scope words** describe a function and stay with it: global; enterprise-wide; portfolio-wide; cross-study; across therapeutic areas or franchises; large-scale

### 2. Means

A tool, method, skill or body of subject knowledge, asked for on its own. Goes under the function it serves; if the JD ties it to none, under the closest function.

- **Programming:** R (Shiny, tidyverse, package development, Quarto); Python (pandas, NumPy); SQL; SAS
- **Analytics and visualization tools:** Spotfire; Tableau; Power BI; JReview; Smartsheet; risk-based monitoring tools
- **Data and cloud platforms:** AWS; Azure; Databricks; Snowflake; Dataiku; Posit; data warehouse; data lake; relational databases
- **Clinical systems:** EDC; Medidata Rave; Veeva Vault (CTMS, eTMF, study start-up); clinical data management systems; clinical data repositories
- **Data standards:** CDISC SDTM, ADaM, USDM; metadata-driven programming; data modeling; data architecture
- **Data types:** EDC, eCOA/ePRO, lab, biomarker, imaging, IRT, wearables, safety data; claims; EHR; real-world data; omics
- **Regulatory and quality knowledge:** GCP, ICH; 21 CFR Part 11; FDA and EMA requirements; GxP; computer system validation; data privacy; pharmacovigilance; TMF requirements
- **Industry and development knowledge:** clinical trial workflows and phases; drug development process; R&D value chain; commercial operations
- **AI and ML methods:** machine learning; deep learning; generative AI; LLMs; RAG; prompt engineering; fine-tuning; MLOps
- **Statistical and analytic methods:** statistics; data science; predictive modeling; experimentation
- **Software practice:** Git; CI/CD; automated testing; APIs; SDLC; low-code; workflow automation
- **Project, process and change methods:** agile; project management methods; Lean; Six Sigma; change management methods; Quality by Design; risk-based approaches

### 3. Qualification

A fixed threshold the candidate holds or does not, shown by a credential or a career record. All go into one Qualifications group after the functions, not ranked.

- **Education:** bachelor's, master's, PhD, MBA, PharmD, named fields; equivalent experience accepted
- **Certification or license:** PMP; Lean Six Sigma; agile; change management certification; professional licenses
- **Years of experience:** total, industry, or naming a function ("8 years leading analytics teams"); a row that names a function records which one

### 4. Working style

A quality of how the person works, which a CV can show through what they did. Under the function it serves when the JD ties it to one; otherwise one Working style group, ranked.

- **Communication as a quality:** strong communicator; clear written and verbal communication; adapts to the audience; explains technical work to non-technical people
- **Influence and relationships:** influence without authority; builds trust; manages expectations; negotiation; conflict resolution
- **Collaboration:** collaborative; cross-functional teamwork; gives and seeks feedback; inclusive
- **Thinking and judgment:** problem solving; critical thinking; analytical; systems thinking; sound judgment; data-driven decisions; strategic thinking; first-principles thinking; attention to detail
- **Managing workload:** competing priorities; deadlines; works under pressure; works with limited supervision; drives work to completion
- **Adaptability and initiative:** handles ambiguity and change; flexible; proactive; initiative; entrepreneurial
- **Presence:** executive presence; credibility; emotional intelligence

### 5. Setting

The context the candidate's experience must come from, when the JD asks for it ("experience in," "background in," "exposure to," "ability to operate within," "ideally within"). Its own need, ranked.

- **Industry:** pharma; biotech; CRO; medical device; healthcare; life sciences; SaaS
- **Therapeutic area or research domain:** oncology; neuroscience; cell therapy; discovery; translational research
- **Development stage:** Phase 1 to 3; global Phase 3; early-stage to commercial
- **Company type or stage:** startup; fast-paced; high-growth; lean; mid-size CRO
- **Environment:** regulated; matrixed; global; geographically dispersed teams; multi-program portfolio
- **Structure the candidate worked within:** Center of Excellence; transformation office; peer team of leads

### 6. Role shape

Whether the person does the work, directs it, or both. Not a need; it sets the job description's lead-or-do answer. The rows then go on the Not ranked list.

- hands-on individual contributor; hands-on leader; thought leader and hands-on driver; directs without owning execution; roll up sleeves alongside the team; operate as a senior leader

### 7. Administrative detail

Facts about the hiring company's organization, how it operates, and where the role sits in it. Never work the person does ("administer the platform" is Function). Not a need; the ranker and the axis classifier read it only for seniority and reach. The rows then go on the Not ranked list.

- reporting line; department or organization name; team membership; internal program or group names; job grade or level ("Associate Director level"); requisition details; newly created function; how the company's function operates ("lean, embedded in asset decisions"); the role's influence on company decisions

### 8. Boilerplate or attitude

Mission or values wording, generic company self-promotion, benefits, legal text, and feelings or beliefs no CV line can show. Goes on the Not ranked list.

- **Mission and values:** text that repeats or rewords the mission and values in the research file's Company section; commitment to the company's cause; "passion for fighting cancer"
- **Feelings and beliefs:** passion for; love of; enjoys; curiosity; growth mindset; self-awareness; culture fit
- **Self-promotion:** about-us text; awards; "a great place to work"
- **Benefits and terms:** pay, benefits, perks, relocation, team events
- **Legal text:** equal opportunity; accommodation; data privacy notices

### 9. Employment condition

A term of the job the candidate accepts or is permitted to meet, never shown by a CV line. Gap analysis checks each against the candidate's eligibility details (its Phase 2), so it goes on the Not ranked list.

- work authorization or sponsorship; remote, hybrid, on-site or location; travel percentage; background check; drug screen; security clearance; vaccination; physical requirements; start date

## KINDS: Tests

- **Function or Working style:** an activity the role performs, usually with an audience or output, is Function ("present to senior leadership"). A quality of how the person does it is Working style ("strong executive presence"). The same topic can be either.
- **Working style or attitude:** if a CV line can show it through something the person did, Working style. If not, attitude. "Mindset" does not decide it; the word before it does.
- **Means or Function:** a row with a verb for work the role does (optimize, build, apply ... to, lead, present) is Function, and any tool, method or knowledge it names for that work goes with it, not split off. Word order and wording do not change this: "apply Lean to optimize processes" and "optimize processes using Lean" are both Function, as is "experience building dashboards." A row asking only to have a tool, method, skill or knowledge is Means ("strong SQL proficiency," "knowledge of GCP"); "experience with" a thing stays Means even when the thing names an area of work ("experience with platforms and reporting").
- **Means or Setting:** "knowledge of," "understanding of," "familiarity with" is Means. "Experience in," "background in," "exposure to" a context (industry, therapeutic area, company type) is Setting. "Experience in" an activity is Function.
- **Setting or Administrative detail:** background the JD asks the candidate to bring is Setting. A description of the hiring company is Administrative detail; the company's industry and operating state are covered by the axis classification.
- **Qualification or Employment condition:** if a degree, certificate or career record shows it, Qualification. If the candidate meets it by agreeing to or being permitted to (travel, work location, authorization), Employment condition.
- **Administrative detail or Boilerplate:** if the text would read the same in any JD this company posts, Boilerplate. If it is specific to this role's setup, Administrative detail.

## KINDS: Words that go with what they describe

These never form a need or a kind of their own.

- **Exclusions** ("not a traditional BI role," "rather than one-off deliverables") go with the function or role shape they limit.
- **Seniority words** ("senior," "seasoned") go with what they describe. A formal grade is Administrative detail.
- **Amount words** ("significant," "extensive," "exposure to," "proven track record") stay in the row's text and go with what they describe. They do not affect ranking.
- **"Recognized," "master"** describe the standard for a function and add no weight.
- **Person labels** ("a facilitator," "a strategist") are read as the activity they name.
- **"Comfortable," "willing"** are read as what follows them: "willing to work hands-on" is Role shape; "comfortable in a fast-paced environment" is Setting.

## RANK: Describing the job

Answer three questions, each citing the jd.md lines it rests on as `L<n>`, the line numbers the Read tool shows:
- What does the role statement say the role is, owns and does? The role statement is the sentences that say what the role is, what it is for, or what it is responsible for overall; judge by what each sentence says, never by where it sits. Go through it clause by clause and list each of these as one short key item, in the JD's words, with its line. Never copy whole sentences.
  - Every role the statement gives ("business owner for", "SME for") and every verb it gives the role, including what the role uses, kept as one item however many tools or methods it names ("leverages AI, automation, predictive analytics, modern clinical technology platforms"). The item opens with that role or verb; "responsible for" and "accountable for" name no role, so the item opens with the verb after them ("automating how clinical data are integrated"). Said again in other words ("transforms data into insights" after "translates data into insights"), it is one item citing both lines.
  - A purpose stated for the role as a whole or for several of its functions ("to support portfolio growth, operational excellence and continuous process improvement"), opening with its verb ("supports portfolio growth", "supports operational excellence and continuous process improvement"). A purpose tied to one function is an outcome, not part of the item ("translates data into actionable insights", not "... to improve study execution, resource planning ..."). A role-wide purpose at the end of a how-clause is still one item, never split; the how-clause drops ("ensuring robust collaboration with ... to accelerate insights and drive data-informed decision-making" gives "accelerates insights and drives data-informed decision-making"). Words naming different deliverables stay and split by area (next point); what one deliverable achieves ("that enable data-driven study oversight and portfolio management", "to improve ...") is an outcome, not part of the item.
  - Any other item whose role, verb or purpose covers several objects becomes one item per distinct area; objects that are facets of one area stay together: "business owner for performance analytics, metrics, reporting", "business owner for data governance", "business owner for Veeva Vault capabilities"; "drives platform optimization and user adoption", "drives platform process standardization and governance", "drives platform integration with the clinical technology ecosystem"; "oversees interactive tools supporting medical monitoring, safety surveillance, patient profiling", "oversees interactive tools supporting ongoing study surveillance and clinical operational oversight". A split item names what it applies to ("platform").
  - Not items: clauses on how an item is carried out or whom it is done with ("ensuring alignment between ...", "partnering with ..."), scope or examples around an item ("for the global clinical trial portfolio"), and tools named inside a function's item ("building reusable dashboards", not "building reusable R and Python dashboards"); tools belong only in the item for what the role uses.
- What outcomes does the role statement name? List each outcome set aside above as one short item in the JD's words, opening with its verb, with its line ("enable data-driven study oversight and portfolio management (L24)"); write `none` if there are none. Outcomes are never role statement items and never needs.
- Do they lead the work, do it, or both? If they lead, what does the JD say they lead (a team, initiatives, change, a rollout), in its words? Leading work is not managing people; name people only where the JD does. Base this on the Role shape rows.

## RANK: Grouping rows into needs

A need is a function the role delivers, taken from the description of the job, or the JD's Setting, and named by that function: no tool, platform or technology in its name (see Rules). Means and Working style rows go under the function they serve, found by reading the whole JD; when the JD ties one to no function, put it under the closest function. Working style tied to no function forms one Working style need. Leading people is one need, whatever its label (line, operational, functional, matrix); oversight and training or mentoring are separate needs (see the rules file). Exclusions and describing words go with what they describe (see the rules file).

Put every row with any part Function, Means, Working style or Setting in exactly one need. The script places every other row by its kind.

## RANK: Ranking the needs

Rank the needs, strongest signal first:
- `role-statement`: the need is a key item of the role statement (the description of the job), and its quote comes from that item's line. A tool or quality the sentence only mentions does not count.
- `repetition` (how many JD sections the need's rows come from) and `space` (how many words the JD clauses holding them run to): do not write either. The script counts both, adds them, and sorts the needs by role-statement, repetition, then space, keeping your order only where all three tie.
- Not a signal: words like "key," "critical" or "important." They stress something within its own topic, not across the role.

Check the ranking against the description of the job. Each key item of the role statement that requirement rows carry should be among the top needs; an item no row carries makes no need. If not, fix the grouping or the ranking. The lead-or-do answer never lifts a need: leading people ranks by its signals like any other need. Never edit the description to fit the table.

## RANK: Naming and quoting needs

- Do not invent a need the rows do not carry. Ranking reorders and groups; it adds nothing.
- Name each need in the JD's own words where the JD names it, by the function it delivers. A tool, platform or technology the function uses stays in its rows, never in the need's name: "drives platform optimization, user adoption, process standardization", not "Veeva Vault Clinical"; "deploys AI applications in production", not "Generative AI". If dropping the tool changes what the work is, name the kind of tool instead ("from one programming language to another").
- Quote one verbatim JD passage per need showing its strongest signal, copied exactly from one line of the JD.
