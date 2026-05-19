#!/usr/bin/env python3
"""
axis_apply.py - file-writing operations for axis-builder

Phase 6 of the axis-builder skill family. Two subcommands:

  create   Write a new value file, apply per-sibling Adjacency back-edges,
           replace or append the registry entry, and (optionally) mark
           provisional + log unresolved QC issues to design/build_issues.md.
  refresh  Overwrite an existing value file with the post-QC drafted text,
           bump last_researched, and (optionally) mark provisional + log
           unresolved QC issues.

Both subcommands are transactional in spirit: create stages all writes in
memory before touching disk and rolls back any partial state on failure;
refresh writes the primary artifact before the append-only build-issues log
so a phantom log entry cannot survive a failed primary write.

Author    : Jason Delosh
Created   : 2026-05-19
Project   : career
Usage     : python scripts/axis_apply.py create <axis> <value> \
                --value-file ... --sibling-edits ... --registry-entry ... \
                [--provisional --issues ...]
            python scripts/axis_apply.py refresh <axis> <value> \
                --value-file ... [--provisional --issues ...]
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import axis_qc
import axis_registry
import axis_utils


# ---------------------------------------------------------------------------
# Section editing
# Sibling back-edges are inserted at the end of the target file's
# '## Adjacency' section. Refresh overwrites whole files, so no in-section
# modify/remove helper is needed beyond append.
# ---------------------------------------------------------------------------

def _insert_bullet_in_section(text, heading, bullet_text):
    """Append a bullet line at the end of a named section.

    The bullet is inserted just before the section-ending blank line (or just
    before the next '## ' heading if no trailing blank line). Preserves any
    existing trailing whitespace structure.
    """
    body_start, body_end = axis_utils.find_section_bounds(text, heading)
    body = text[body_start:body_end]
    # Strip trailing whitespace/newlines from the body, append the bullet, then
    # add one trailing blank line so section separation is preserved.
    new_body = body.rstrip() + '\n' + bullet_text.rstrip() + '\n\n'
    return text[:body_start] + new_body + text[body_end:]


# ---------------------------------------------------------------------------
# Frontmatter mutation - refresh-specific
# Bumping last_researched only fires in refresh mode; create starts with a
# freshly drafted frontmatter whose last_researched is already current.
# ---------------------------------------------------------------------------

def _bump_last_researched(text, ym):
    """Update last_researched: <YYYY-MM> in frontmatter."""
    frontmatter, body = axis_utils.split_frontmatter(text)
    if frontmatter is None:
        raise ValueError('cannot bump last_researched: file has no frontmatter')
    new_frontmatter = re.sub(
        r'(?m)^last_researched:[ \t].*$',
        f'last_researched: {ym}',
        frontmatter,
    )
    return new_frontmatter + body


# ---------------------------------------------------------------------------
# Subcommand: create
# Write the new value file, apply per-sibling Adjacency back-edges, replace
# the registry entry, and (optionally) mark provisional + log issues.
#
# Input file shapes:
#   --value-file       full Markdown text of the new value file.
#   --sibling-edits    JSON list of {"sibling_file": "<name>.md",
#                                    "section": "Adjacency",
#                                    "bullet": "- **<value>**: <translation>."},
#                      OR the reconciler's self-describing wrapper
#                      {"mode": "create", "sibling_edits": [...]}.
#                      Either is accepted (see axis_utils.unwrap_list).
#   --registry-entry   one-line Markdown bullet for the registry entry, e.g.
#                      "- **generics** - generic and 505(b)(2) ... File: generics.md."
#   --issues           JSON list of {"check": "...", "detail": "...",
#                                    "attempted": "..."} (provisional only)
# ---------------------------------------------------------------------------

def cmd_create(args, repo_root, cfg):
    """Write a new value file, apply sibling Adjacency back-edges, update the registry.

    Refuses if the value file already exists. With --provisional, marks the
    file's frontmatter and appends a record to design/build_issues.md after
    the main writes succeed.

    Two-stage protection against half-modified state:
    - All transformations (sibling reads, Adjacency-section locate, bullet
      insert) run in memory before any disk write. A missing sibling file or
      malformed input fails the run without touching disk.
    - The write loop snapshots each target's prior content (or "did not
      exist") up front. If any write raises mid-loop, every write that
      already landed is rolled back: pre-existing files are restored to
      their prior content; new files (only the value file) are deleted.
      The original exception then propagates. If rollback itself fails
      (disk still full, file just became locked), both errors are reported
      and the user must reconcile by hand.

    Prints every path written, one per line, as it is written (not at the
    end), so the calling skill and user see partial-write state if the
    rollback path itself fails.
    """
    axis = args.axis
    value = args.value
    reg_path = axis_utils.registry_path(repo_root, cfg, axis)

    # --- Resolve target paths and refuse if the value file already exists ---
    # Filename convention: <value>.md. If a custom filename is ever needed, add
    # a --filename arg rather than parsing it out of the registry-entry text.
    value_filename = f'{value}.md'
    vf_path = axis_utils.value_file_path(repo_root, cfg, axis, value_filename)
    if os.path.exists(vf_path):
        raise FileExistsError(
            f'value file already exists: {vf_path}. Use refresh, not create.')

    # --- Read all inputs upfront ---
    # Every JSON input is validated against its declared shape at this
    # boundary. A mismatch raises ContractError, which the CLI entry
    # point translates into a categorized exit (code 2 / stderr prefix
    # 'ContractError:') the dispatching SKILL recognizes.
    value_text = _util.read(args.value_file)
    sibling_edits = axis_utils.unwrap_list(
        _util.load_json(args.sibling_edits), 'sibling_edits')
    axis_utils.validate_list_of_dicts(
        sibling_edits,
        input_name='sibling_edits',
        shape=axis_utils.SIBLING_EDIT_SHAPE,
    )
    registry_entry_line = _util.read(args.registry_entry).strip()
    issues = None
    if args.provisional:
        issues = axis_utils.unwrap_list(
            _util.load_json(args.issues), 'issues')
        axis_utils.validate_list_of_dicts(
            issues,
            input_name='issues',
            shape=axis_utils.ISSUE_SHAPE,
        )

    # --- Re-enforce G1 at the apply step ---
    # QC's 3-iteration loop can give up and ship a provisional build with
    # unresolved findings, but a registry entry whose 'File:' pointer does
    # not match the value file is structural corruption (downstream
    # consumers would follow the pointer to a missing file), not a
    # triage-able content issue. Refuse the apply rather than write a
    # broken pointer.
    g1 = axis_qc.check_g1_registry_entry_filename(registry_entry_line, value_filename)
    if not g1['passed']:
        raise ValueError(f"registry entry mismatch (G1): {g1['detail']}")

    # --- Provisional marking on the value text (in-memory only) ---
    if args.provisional:
        value_text = axis_qc.apply_provisional(value_text, issues)

    # --- Stage all overwrite writes ---
    # Build a list of (path, text) pairs. Nothing is written to disk yet.
    # If any transformation below raises (missing sibling file, missing
    # Adjacency section, malformed input), the repo is unchanged.
    staged = [(vf_path, value_text)]

    # Sibling Adjacency back-edges.
    for edit in sibling_edits:
        sibling_path = axis_utils.value_file_path(repo_root, cfg, axis, edit['sibling_file'])
        if not os.path.exists(sibling_path):
            raise FileNotFoundError(f'sibling file missing: {sibling_path}')
        sibling_text = _util.read(sibling_path)
        sibling_text = _insert_bullet_in_section(
            sibling_text, edit.get('section', 'Adjacency'), edit['bullet'])
        staged.append((sibling_path, sibling_text))

    # Registry: replace existing bullet or append new one.
    registry_text = _util.read(reg_path)
    existing, _, _ = axis_registry.find_registry_entry(registry_text, value)
    if existing:
        # Replace the matched bullet line (and only that line).
        line_start = registry_text.rfind('\n', 0, existing.start()) + 1
        line_end = registry_text.find('\n', existing.end())
        if line_end == -1:
            line_end = len(registry_text)
        registry_text = (
            registry_text[:line_start] + registry_entry_line + registry_text[line_end:])
    else:
        # Append as a new bullet at the end of the file, preserving trailing newline.
        if not registry_text.endswith('\n'):
            registry_text += '\n'
        registry_text += registry_entry_line + '\n'
    staged.append((reg_path, registry_text))

    # --- Snapshot pre-write state for transactional rollback ---
    # For each staged target, remember either its prior content (existed
    # before) or None (did not exist). On a mid-loop write failure we use
    # this to put the repo back to its pre-run state.
    originals = {}
    for path, _ in staged:
        originals[path] = _util.read(path) if os.path.exists(path) else None

    # --- Apply staged writes with rollback on failure ---
    written_paths = []
    try:
        for path, text in staged:
            _util.write(path, text)
            written_paths.append(path)
            # Print as we go (flushed) so any partial state is visible if
            # the rollback path itself fails below.
            print(path, flush=True)
    except Exception:
        # Roll back in reverse order: undo most recent writes first. For
        # pre-existing files restore the prior text; for newly-created
        # files delete them. Best-effort: if a rollback step itself
        # raises, log it to stderr and continue so the rest of the rollback
        # still runs, then re-raise the original exception.
        for path in reversed(written_paths):
            try:
                original = originals[path]
                if original is None:
                    os.remove(path)
                else:
                    _util.write(path, original)
                print(f'rolled back: {path}', file=sys.stderr)
            except Exception as rollback_err:
                print(
                    f'rollback FAILED for {path}: {rollback_err}',
                    file=sys.stderr,
                )
        raise

    # --- Provisional: append to build-issues log (last; append-only) ---
    if args.provisional:
        log_path = axis_qc.append_build_issues(repo_root, cfg, axis, value, 'create', issues)
        print(log_path, flush=True)


# ---------------------------------------------------------------------------
# Subcommand: refresh
# Overwrite an existing value file with the post-QC drafted text, bump
# last_researched, and (optionally) mark provisional + log issues.
#
# Input file shapes:
#   --value-file  full Markdown text of the refreshed value file (the same
#                 temp file qc was run against, with any auto-fixes carried
#                 through). The reconciler's change list is informational
#                 for QC only; the apply step writes the drafted file
#                 wholesale so Phase 5 auto-fixes are preserved.
#   --issues      JSON list of {"check": "...", "detail": "...",
#                               "attempted": "..."} (provisional only)
# ---------------------------------------------------------------------------

def cmd_refresh(args, repo_root, cfg):
    """Overwrite an existing value file with the drafted text and bump last_researched.

    Refuses if the value file is missing. With --provisional, marks the
    file's frontmatter and appends a record to design/build_issues.md.
    Prints every path touched, one per line.
    """
    axis = args.axis
    value = args.value
    value_filename = f'{value}.md'
    vf_path = axis_utils.value_file_path(repo_root, cfg, axis, value_filename)

    # --- Refuse if the value file does not already exist ---
    if not os.path.exists(vf_path):
        raise FileNotFoundError(
            f'value file missing: {vf_path}. Use create, not refresh.')

    # --- Load drafted text (the post-QC --value-file temp) ---
    text = _util.read(args.value_file)

    # --- Bump last_researched (always; the research run happened) ---
    text = _bump_last_researched(text, _util.today_ym())

    # --- Load issues and apply provisional flag to the in-memory text ---
    # Validate against ISSUE_SHAPE at the boundary so a malformed issues
    # array fails with a categorized ContractError instead of corrupting
    # the file's YAML frontmatter downstream.
    issues = None
    if args.provisional:
        issues = axis_utils.unwrap_list(
            _util.load_json(args.issues), 'issues')
        axis_utils.validate_list_of_dicts(
            issues,
            input_name='issues',
            shape=axis_utils.ISSUE_SHAPE,
        )
        text = axis_qc.apply_provisional(text, issues)

    # --- Write the value file first (primary artifact) ---
    _util.write(vf_path, text)
    written_paths = [vf_path]

    # --- Append the build-issues log only after the primary write succeeds ---
    # Inverted order would leave a phantom log entry if the value-file write
    # failed (disk full, permissions); the log is append-only and not rolled
    # back. Mirrors the order in cmd_create.
    if args.provisional:
        log_path = axis_qc.append_build_issues(repo_root, cfg, axis, value, 'refresh', issues)
        written_paths.append(log_path)

    for p in written_paths:
        print(p)


# ---------------------------------------------------------------------------
# Command-line entry point
# Two subcommands (create, refresh) with identical --provisional/--issues
# semantics. Cross-cutting validation lives in main() since argparse cannot
# express "--provisional requires --issues" natively.
# ---------------------------------------------------------------------------

def main():
    """Parse argv, load config, dispatch to the selected subcommand."""
    parser = argparse.ArgumentParser(
        description='axis-builder file-writing operations (Phase 6)')
    sub = parser.add_subparsers(dest='command', required=True)

    # --- Subparser: create ---
    p_cre = sub.add_parser(
        'create',
        help='write a new value file + sibling Adjacency back-edges + registry entry',
    )
    p_cre.add_argument('axis')
    p_cre.add_argument('value')
    p_cre.add_argument('--value-file', required=True,
                       help='path to a file holding the new value-file Markdown')
    p_cre.add_argument('--sibling-edits', required=True,
                       help='path to a JSON file of per-sibling Adjacency edits')
    p_cre.add_argument('--registry-entry', required=True,
                       help='path to a file holding the one-line registry bullet')
    p_cre.add_argument('--provisional', action='store_true',
                       help='mark the value file provisional and log unresolved QC issues')
    p_cre.add_argument('--issues', default=None,
                       help='path to a JSON file of unresolved QC issues (required with --provisional)')
    p_cre.set_defaults(func=cmd_create)

    # --- Subparser: refresh ---
    p_ref = sub.add_parser(
        'refresh',
        help='overwrite an existing value file with drafted text and bump last_researched',
    )
    p_ref.add_argument('axis')
    p_ref.add_argument('value')
    p_ref.add_argument('--value-file', required=True,
                       help='path to the drafted (post-QC) value-file Markdown to write')
    p_ref.add_argument('--provisional', action='store_true',
                       help='mark the value file provisional and log unresolved QC issues')
    p_ref.add_argument('--issues', default=None,
                       help='path to a JSON file of unresolved QC issues (required with --provisional)')
    p_ref.set_defaults(func=cmd_refresh)

    # --- Cross-cutting validation argparse cannot express natively ---
    args = parser.parse_args()
    if getattr(args, 'provisional', False) and not args.issues:
        parser.error('--provisional requires --issues')

    # --- Dispatch ---
    # ContractError gets its own categorized exit code (2) and stderr
    # prefix so the dispatching SKILL can recognize input-shape failures
    # and translate them into a user-facing message distinct from
    # generic build failures.
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        args.func(args, repo_root, cfg)
    except axis_utils.ContractError as e:
        print(f'ContractError: {e}', file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
