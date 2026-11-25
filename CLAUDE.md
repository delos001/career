# Career Repo — Project Instructions

## Purpose and Constraint

- The repo is for any user, not only its author: building profile documents from scratch is a primary mode (GitHub #27 to #29).
- Context budget is a first-class design criterion; the prior repo failed when skills outgrew the context window. Prefer slices over whole documents, scripts over LLM checks, composition over one file per combination.

## Where Things Live

- **Backlog:** GitHub issues in `delos001/career` (labels bug, enhancement, documentation, audit, decision; title prefix names the area). An issue states the action first, then what is needed to act on it.
- **`design/design_decisions.md`:** closed design decisions only; no audit logs or session state.
- **`design/deferrals.md`:** only items whose need is undecided, with a named trigger, and whose premise still exists. Decided-but-unbuilt work is an issue.
- **`design/open_questions.md`:** questions blocking current work.
- **Session resume** (memory `project_session_resume.md`): the next action only. Point at issues and files; never restate status.
- **Session start:** read the resume, `open_questions.md` and `deferrals.md`, then check the next action against the filesystem. **Close:** each new item in its file; the resume updated with a self-contained next action.
- **Outside the repo:** the job tracker sheet `JobSearch_Tracker_v1.0` (Drive folder `jobsearch`; rates on its Summary tab) and the job monitor at `C:\Users\delos\code\job_monitor`. The self-assessment (`personal/self-assessment/`, `/self-assessment`) is a separate project, not part of the career system.

## Building

- A skill phase does one activity. Script behavior lives in the script; rationale in `design_decisions.md`.
- Follow a skill exactly: dispatch agents with the printed prompt, pass every listed input, never substitute or reuse a prior run's output. SKILL.md names exact CLI flags. If calling a script takes more than a line or two of prose, fix the script's interface.
- Scripts: one concern per file; derive vocabularies (such as ID prefixes) from the source documents; no entry counts in schemas.
- A structural QC finding is fixed in the script or template that produced it, not in the artifact. Re-read a shared script first; a parallel session may have fixed it.
- Artifact skills fix QC findings inside a capped build loop; on failure they ship marked provisional and log to `design/build_issues.md`. The user never votes on QC checks.
- Test a pipeline change on several applications, never one. A rerun batch probes the process: lead each finding with its root cause, checked across applications. After an agent fails test cases twice, lay out its steps before patching rules. Define categories (definition, examples, tests) before an agent labels anything.
- Every addition must show yield; add one, cut one. A temporary fix gets no documentation. Do not widen a decided fix with edge cases.
- After any change, grep for references to what moved and sync `COMPONENTS.md`.
- Commit messages: what changed and a brief why.
- Em dashes are allowed in design docs, never in skills, agents, scripts, templates or user-facing content.

## Tool Usage

**Always use the PowerShell tool for running commands. Never use the Bash tool.**

This is a Windows machine. The Bash tool runs under a POSIX shell that does not support PowerShell syntax (backtick line continuation, `$env:` variables, etc.). Any command that would work in PowerShell will fail or behave unexpectedly in Bash. Use the PowerShell tool for every command: scripts, git, Python, file operations via CLI.

The one exception in the system prompt — "reserve Bash for POSIX scripts" — does not apply here. There are no POSIX scripts in this repo.

## Working Directory

Do not rely on the working directory. Always use absolute paths for both the script being run and any file path arguments passed to it. The scripts resolve the repo root from `__file__` internally, so they can be called from any directory — but argument paths must be absolute to be safe.

Example: `C:\Users\delos\miniconda3\envs\career\python.exe C:\Users\delos\code\career\scripts\gap_assemble.py assemble --folder C:\Users\delos\code\career\personal\applications\... --requirements-file C:\Users\delos\code\career\...`

## Talking to the User

Everything the user reads (status, prompts, findings, errors) is plain English: what they need to know to wait, decide, or act. No check IDs, route-back labels, or implementation terms (subagent, JSON, script names).

## Working Files

Every working file a skill writes, and every output file its subagents write, goes in the scratch folder for that work. Create it if absent.

- Application skills: `<scratch>` = `<app_folder>/scratch/`. It lasts for the life of the application (a resumed run reuses it) and is wiped when the application is closed or declined.
- Axis builders: `<bscratch>` = `rules/scratch/`. Wiped at the end of the build.
- Work with neither (profile-update): `temp/`.

## Skills

This repo contains Claude Code skills in `.claude/skills/`. Each skill has a `SKILL.md` that is the authoritative spec for how the skill runs. Read it before running the skill. Follow it exactly.

File paths inside a `SKILL.md` are repo-root-relative, not relative to the skill's own folder. A reference to `templates/session_log.md` means `<repo root>/templates/session_log.md`. Skills do not carry their own `templates/` directories; every template lives in the single root `templates/`.

## Scripts

All Python scripts live in `scripts/`. They resolve the repo root from `__file__` and read config from `config.yaml`. Nothing is hardcoded. Do not pass repo-root-relative paths from within scripts/ — use `../` or absolute paths.

Scripts have a header block, section markup, and comments on complex logic. This overrides the default minimal-comments stance.

## Testing

Test against the fixture corpus, never the live profile. `python tests\run_tests.py` runs the invariant checks in seconds; `--only <substring>` runs one. `CAREER_FIXTURE=tests/fixture` redirects every personal-rooted path onto an invented candidate, and the runner refuses to start if the resolved path is outside `tests/`.

The older pattern of backing up and restoring the real profile documents around a test is retired. Do not reintroduce it.

A check is only finished once it has been seen to fail: reintroduce the bug, watch it go red, restore.

## Tool and Environment Quirks

These have each cost a debugging cycle.

- **Run scripts with `C:\Users\delos\miniconda3\envs\career\python.exe`.** Bare `python` is the miniconda base environment, which has no `yaml`, so every script fails at `import _config`. Where a skill or this file writes `python`, use this path.

- **PowerShell has no heredoc.** `python - <<'PY'` is a parse error. Write the script to a file and run it.
- **The Edit tool fails on multi-line matches containing `→` (U+2192).** Use single-line edits, or splice around the glyph.
- **Validate `.drawio` XML after any edit:** `[xml]$x = Get-Content -Raw <path>`, then check `$x.mxfile.diagram.Count`.
- **`personal/` is a separate nested git repo**, gitignored by the career repo. Check `git -C C:\Users\delos\code\career\personal status` before treating a file there as untracked.
- **Glob is case-sensitive here.** If it finds nothing for a file you expect, list the folder with `Get-ChildItem`.
- **Only `Edit(path)` permission rules govern writes;** `Write(path)` rules are ignored. Subagent writes to `personal/` come from `Edit(...)` in `.claude/settings.local.json`. Do not recreate a committed `.claude/settings.json`.
- **If no shell tool loads,** check that `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` is still in the `env` block of `.claude/settings.local.json`.
- **GitHub MCP** creates, updates and closes issues and applies labels, but cannot create labels. `gh` is not installed.
- **Never bulk-replace text through PowerShell arrays.** A single-element nested array flattens, so `$e[0]`/`$e[1]` become characters rather than strings, and the replace rewrites the file a character at a time. This silently corrupted 383 lines of a script once. Use the Edit tool, and check `git diff --stat` before moving on.
