# Career Repo — Project Instructions

## Tool Usage

**Always use the PowerShell tool for running commands. Never use the Bash tool.**

This is a Windows machine. The Bash tool runs under a POSIX shell that does not support PowerShell syntax (backtick line continuation, `$env:` variables, etc.). Any command that would work in PowerShell will fail or behave unexpectedly in Bash. Use the PowerShell tool for every command: scripts, git, Python, file operations via CLI.

The one exception in the system prompt — "reserve Bash for POSIX scripts" — does not apply here. There are no POSIX scripts in this repo.

## Working Directory

Do not rely on the working directory. Always use absolute paths for both the script being run and any file path arguments passed to it. The scripts resolve the repo root from `__file__` internally, so they can be called from any directory — but argument paths must be absolute to be safe.

Example: `python C:\Users\delos\code\career\scripts\gap_assemble.py assemble --folder C:\Users\delos\code\career\personal\applications\... --requirements-file C:\Users\delos\code\career\...`

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

- **PowerShell has no heredoc.** `python - <<'PY'` is a parse error. Write the script to a file and run it.
- **The Edit tool fails on multi-line matches containing `→` (U+2192).** Use single-line edits, or splice around the glyph.
- **Validate `.drawio` XML after any edit:** `[xml]$x = Get-Content -Raw <path>`, then check `$x.mxfile.diagram.Count`.
- **Never bulk-replace text through PowerShell arrays.** A single-element nested array flattens, so `$e[0]`/`$e[1]` become characters rather than strings, and the replace rewrites the file a character at a time. This silently corrupted 383 lines of a script once. Use the Edit tool, and check `git diff --stat` before moving on.
