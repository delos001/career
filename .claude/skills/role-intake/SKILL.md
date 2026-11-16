---
name: role-intake
description: Starts a new job application by ingesting a job description and relevant communication and creating a folder to hold application related documents and artifacts including the session log. This is the first skill run for a new role; role-research runs next.
---

# role-intake - start a new application

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Each phase opens with the **bold lead line** under its heading - speak it verbatim before running the phase.

## Resume check - run before Phase 0

Ask: "Is this a new role, or are you resuming one?"

- **New:** go to Phase 0.
- **Resume:** ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`; use it as `<app_folder>` and never run Phase 3. Find the first case that matches. For cases 2 and 3, tell the user in plain words which application this is (the folder name), what is already saved, and the step being picked up; then go there without asking.
  1. **No folder** (the lookup fails): the APP-NNN is probably wrong. Say so and ask for it again.
  2. **No `jd.md`:** go to Phase 1.
  3. **No session log:** run Phase 2 on `jd.md` and `comms.md`, then Phase 5. Ask the user where the JD and messages came from, since Phase 1's sources are not on disk.
  4. **Otherwise:** role-intake is done. Give the session log path and tell the user to run `/role-research`.

## Phase 0 - Intro

**Introducing the role-intake skill.**

- Run `python scripts/display/introduce.py role-intake` and show the output.

## Phase 1 - Read the JD

**Reading in the job description and any role communications.**

- Put the JD in `temp/intake/<YYYYMMDD-HHMMSS>_jd.txt`. For a file path or URL, run `python scripts/ingest/jd_extract.py <source> --out <that file>`. For pasted text, write the paste to that file unchanged.
- Ask the user for any role communications (e.g. a recruiter email) and put them in `..._comms.txt` the same way.
- Read the files to work from the text. Never echo the text back to the user.
- Output: the JD and comms file paths and each one's source (URL, original file path, or `"pasted"`), held in context.

## Phase 2 - Confirm title and company

**Confirming the role title and company.**

- Take the title and company from the JD; ask the user for either one it does not name.
- Present for confirmation and re-present on corrections until confirmed:

  ```
  Confirm role metadata:
    Title:    <value>
    Company:  <value>
  Reply with corrections or "confirmed".
  ```

## Phase 3 - Create the application folder

**Creating the application folder.**

- Run `python scripts/assemble.py folder --company "<confirmed company>"`. It prints `app_folder`, the APP-NNN and the slug; tell the user the slug. If it stops because the company has no slug, ask the user for a short lowercase one and re-run with `--slug`.

## Phase 4 - Save the JD

**Saving the job description.**

- Run `python scripts/assemble.py ingest --folder <app_folder> --jd-text-file <Phase 1 JD file> --title "<confirmed title>" --company "<confirmed company>"`, plus `--comms-text-file <Phase 1 comms file>` if there is one.
- Give the user the `jd.md` path (and `comms.md`) to review; do not show the text.

## Phase 5 - Start the session log

**Starting the session log.**

- Run `python scripts/assemble.py init --folder <app_folder> --company "<confirmed company>" --role "<confirmed title>" --start-date <today>` with `--jd-source` (the URL if the JD came from one, otherwise the `jd.md` path) and, if there are messages, `--comms-source` (the URL, the `comms.md` path, or `"pasted"`).

## Phase 6 - Hand off

**Handing off to role-research.**

- Give the user the session log path and ask for corrections or "approved".
- A corrected title or company: run `python scripts/assemble.py relabel --folder <app_folder>` with `--role` and/or `--company` (and `--slug` if it asks for one); the path it prints is `<app_folder>` from then on.
- On approval, tell the user to run `/role-research`.
