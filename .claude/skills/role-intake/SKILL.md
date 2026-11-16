---
name: role-intake
description: Starts a new job application by ingesting a job description and relevant communication and creating a folder to hold application related documents and artifacts including the session log. This is the first skill run for a new role; role-research runs next.
---

# role-intake - start a new application

## Operating rules

- Read `rules/global-rules.md` first; operate under it throughout.
- Start each phase by saying "The next step is to" followed by the phase title after the dash, in lower case.

## Resume check - run before Phase 0

Ask: "Is this a new role, or are you resuming one?"

- **New:** go to Phase 0.
- **Resume:** ask for the APP-NNN and find its folder with `python scripts/paths.py app <APP-NNN>`; use it as `<app_folder>` and never run Phase 3. Find the first case that matches. For cases 2 to 4, tell the user in plain words which application this is (the folder name), what is already saved, and the step being picked up; then go there without asking.
  1. **No folder** (the lookup fails): the APP-NNN is probably wrong. Say so and ask for it again.
  2. **No `jd.md`:** go to Phase 1.
  3. **No session log:** run Phase 2 on `jd.md` and `comms.md`, then Phase 5. Ask the user where the JD and messages came from, since Phase 1's sources are not on disk.
  4. **Otherwise:** go to Phase 6.

## Phase 0 - Show the intro

- Run `python scripts/display/introduce.py role-intake` and show the output.

## Phase 1 - Read the JD

- Put the JD in `temp/intake/<YYYYMMDD-HHMMSS>_jd.txt`. For a file path or URL, run `python scripts/ingest/jd_extract.py <source> --out <that file>`. For pasted text, write the paste to that file unchanged.
- Ask the user for any role communications (e.g. a recruiter email) and put them in `..._comms.txt` the same way.
- Read the files to work from the text. Never echo the text back to the user.
- Output: the JD and comms file paths and each one's source (URL, original file path, or `"pasted"`), held in context.

## Phase 2 - Confirm title and company

- Take the title and company from the JD; ask the user for either one it does not name.
- Present for confirmation and re-present on corrections until confirmed:

  ```
  Confirm role metadata:
    Title:    <value>
    Company:  <value>
  Reply with corrections or "confirmed".
  ```

## Phase 3 - Create the application folder

- Run `python scripts/assemble.py folder --company "<confirmed company>"`. It prints `app_folder`, the APP-NNN and the slug; tell the user the slug. If it stops because the company has no slug, suggest a 3-5 letter lowercase slug drawn from the company name and ask the user to accept it or give their own; re-run with `--slug`. Once it succeeds, never run it again: each success claims a new APP-NNN. A later slug or company change goes through `relabel` (see *Fixes*).

## Phase 4 - Save the JD

- Run `python scripts/assemble.py ingest --folder <app_folder> --jd-text-file <Phase 1 JD file> --title "<confirmed title>" --company "<confirmed company>"`, plus `--comms-text-file <Phase 1 comms file>` if there is one.

## Phase 5 - Start the session log

- Run `python scripts/assemble.py init --folder <app_folder> --company "<confirmed company>" --role "<confirmed title>" --start-date <today>` with `--jd-source` (the URL if the JD came from one, otherwise the `jd.md` path) and, if there are messages, `--comms-source` (the URL, the `comms.md` path, or `"pasted"`).

## Phase 6 - Check the application files

- Run `python scripts/role_intake_qc.py check --folder <app_folder>`. Fix anything it reports per *Fixes*, then re-check.

## Phase 7 - Hand off to role-research

- Give the user the folder path and the `jd.md`, `comms.md` (if any) and session log paths. Ask them to review the files and raise anything wrong, or say "approved". Do not show the text.
- On a correction, fix it per *Fixes*, re-run Phase 6, and return here.
- On approval, tell the user to run `/role-research`.

## Fixes

| Wrong | Fix |
|---|---|
| JD or messages wrong or missing | Phase 1, Phase 4, then Phase 5 with `--replace` |
| Session log wrong (a source, the comms entry, a field) | Phase 5 with `--replace` |
| Title, company or slug | `python scripts/assemble.py relabel --folder <app_folder>` with `--role`, `--company` and/or `--slug` (it asks for `--slug` when a corrected company is new); the path it prints is `<app_folder>` from then on |
