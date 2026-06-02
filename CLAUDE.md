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

## Scripts

All Python scripts live in `scripts/`. They resolve the repo root from `__file__` and read config from `config.yaml`. Nothing is hardcoded. Do not pass repo-root-relative paths from within scripts/ — use `../` or absolute paths.

Scripts have a header block, section markup, and comments on complex logic. This overrides the default minimal-comments stance.
