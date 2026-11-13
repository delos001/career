#!/usr/bin/env python3
"""
dispatch_prompt.py - print a subagent's complete dispatch prompt

The skill sends the printed prompt exactly as printed, so no subagent input is
pasted, summarized, or selected by hand (GitHub #71). Hand-composed prompts drifted
silently: file paths instead of content, a summarized JD, a retyped JD. Agents get
source documents by file path, which cannot drift; each prompt names only files
that exist, and a required file that is missing stops the run. The retrieval
scorers, gap-detector, and qc-profile-update have their own scripts for the same
pattern.

Content the orchestrator itself produces during a run (stakeholder contributions,
QC findings, dispositions) goes in a file passed with --input-file. CV Notes, and
research.md's Company section for the ranker, are copied byte for byte into the
scratch folder.

Author    : Jason Delosh
Created   : 2026-11-05
Project   : career
Usage     : python scripts/dispatch_prompt.py <agent> --folder <app_folder>
                [--tier <tier>] [--mode draft|revise] [--input-file <path>] [--continued]
Depends   : pyyaml (via _config)
"""

import argparse
import os
import re
import sys

import _config
import _util
import retrieval_payload
import role_classify_qc
import role_intake_qc


# ---------------------------------------------------------------------------
# Who gets what
# Each file key resolves in _Sources.path. A key ending in '?' is optional and is
# left out when the file does not exist.
# ---------------------------------------------------------------------------

_AXIS_FOLDERS = {'Orientation': 'orientations', 'Industry': 'industries', 'Specialty': 'specialties',
                 'Level': 'levels', 'Work-state': 'work-states'}

_INDUSTRY_NOTE = ('Identify and research the industry this company actually operates in, using the '
                  'company name and the job description. No industry was inferred earlier in this '
                  'run, so establish the sector from scratch.')

AGENTS = {
    'company-research': {'facts': ['company', 'role'], 'files': ['jd']},
    'role-research': {'facts': ['company', 'role'], 'files': ['jd']},
    'industry-research': {'facts': ['company', 'role'], 'files': ['jd'], 'note': _INDUSTRY_NOTE},
    'critical-requirements-extractor': {'facts': ['company', 'role'], 'files': ['jd']},
    'jd-needs-ranker': {'files': ['jd', 'company_research', 'jd_needs']},
    'axis-classifier': {'files': ['jd', 'comms?', 'research', 'jd_needs']},
    'qc-role-intake': {'files': ['session_log', 'research', 'jd']},
    'qc-role-classify': {'files': ['session_log', 'research', 'jd_needs', 'jd']},
    'qc-gap-analysis': {'files': ['gap_analysis']},
    'qc-preparation-screen': {'folders': True},
    'qc-preparation-interview': {'folders': True},
    'cv-architect': {'facts': ['level', 'tier'], 'folders': True, 'axes': 'all',
                     'files': ['cv_structure', 'cv_writing', 'jd_needs', 'research', 'retrieval', 'gap_analysis', 'inventory',
                               'narratives', 'user_info', 'cv_notes']},
    'career-strategist': {'facts': ['level', 'tier'], 'axes': ['Level', 'Orientation'],
                          'files': ['cv_content', 'cv_structure', 'cv_writing', 'cv_best_practices', 'jd_needs', 'research']},
    'hiring-manager': {'facts': ['level'],
                       'files': ['cv_content', 'jd_needs', 'research', 'gap_analysis', 'retrieval', 'jd', 'comms?']},
    'candidate-advocate': {'facts': ['level'],
                           'files': ['cv_content', 'retrieval', 'gap_analysis', 'inventory', 'narratives', 'research']},
    'qc-cv-targeted': {'facts': ['level'],
                       'files': ['cv_content', 'inventory', 'narratives', 'gap_analysis', 'research']},
}

# Agents continued across rounds, which already hold their sources.
_CONTINUABLE = {'cv-architect', 'career-strategist', 'hiring-manager', 'candidate-advocate'}


# ---------------------------------------------------------------------------
# Resolving facts and files for one application
# ---------------------------------------------------------------------------

class _Sources:
    """Resolve the paths and facts of one application folder."""

    def __init__(self, folder, repo_root, cfg, tier):
        self.folder, self.root, self.cfg, self.tier = folder, repo_root, cfg, tier
        log_path = self.path('session_log')
        if not os.path.isfile(log_path):
            raise FileNotFoundError(f'session log missing: {log_path}')
        self.log = _util.read(log_path)
        self.meta = role_intake_qc._metadata_fields(self.log) or {}

    def path(self, key):
        """Return the absolute path for a file key."""
        fn, paths = self.cfg['filenames'], self.cfg['paths']
        profile = os.path.join(self.root, paths['profile'])
        cv_rules = os.path.join(self.root, paths['cv_rules'])
        table = {
            'jd': os.path.join(self.folder, fn['jd_file']),
            'comms': os.path.join(self.folder, fn['comms_file']),
            'research': os.path.join(self.folder, fn['research_file']),
            'jd_needs': os.path.join(self.folder, fn['jd_needs_file']),
            'session_log': os.path.join(self.folder, fn['session_log_file']),
            'retrieval': os.path.join(self.folder, fn['retrieval_manifest']),
            'gap_analysis': os.path.join(self.folder, fn['gap_analysis_file']),
            'cv_content': os.path.join(self.folder, fn['cv_content_file']),
            'drafting_plan': os.path.join(self.folder, fn['drafting_plan_file']),
            'cv_notes': os.path.join(self.folder, fn['scratch_subdir'], 'cv_notes.md'),
            'company_research': os.path.join(self.folder, fn['scratch_subdir'], 'company.md'),
            'inventory': os.path.join(profile, fn['inventory_file']),
            'narratives': os.path.join(profile, fn['narratives_file']),
            'user_info': os.path.join(profile, fn['user_info_file']),
            'cv_structure': os.path.join(cv_rules, fn['cv_structure_file']),
            'cv_writing': os.path.join(cv_rules, fn['cv_writing_file']),
            'cv_best_practices': os.path.join(cv_rules, 'cv-best-practices.md'),
        }
        return table[key]

    def fact(self, key):
        """Return a fact's value, or None when it does not apply to this role."""
        if key in ('company', 'role'):
            value = self.meta.get(key.capitalize())
            if not value:
                raise ValueError(f'session log metadata has no {key.capitalize()}')
            return value
        level = self.axis_values('Level')[0]
        if key == 'level':
            return level
        if level != 'leadership':
            return None
        m = re.search(r'(?m)^- Tier:[ \t]*(\S+)', self.log)
        tier = self.tier or (m.group(1) if m else None)
        if not tier:
            raise ValueError('this leadership role has no Tier line; ask the user which tier fits, '
                             'then pass --tier')
        return tier

    def axis_values(self, axis):
        """Return an axis's classified values from the session log, primary first."""
        raw = (role_classify_qc._axis_values(self.log) or {}).get(axis)
        if not raw:
            raise ValueError(f'session log has no {axis} classification')
        return [re.sub(r'\s*\([^)]*\)', '', v).strip() for v in raw.split(',') if v.strip()]

    def axis_files(self, axes):
        """Return (existing rule files, values with no file) for the named axes."""
        found, missing = [], []
        for axis in (_AXIS_FOLDERS if axes == 'all' else axes):
            for value in self.axis_values(axis):
                path = os.path.join(self.root, self.cfg['paths']['rules'], _AXIS_FOLDERS[axis], f'{value}.md')
                if os.path.isfile(path):
                    found.append(path)
                else:
                    missing.append(f'{axis}: {value}')
        return found, missing

    def write_cv_notes(self):
        """Copy the gap analysis's CV Notes section, byte for byte, to scratch."""
        gap_path = self.path('gap_analysis')
        if not os.path.isfile(gap_path):
            raise FileNotFoundError(f'required file missing: {gap_path}')
        notes = retrieval_payload.extract_section(_util.read(gap_path), '## CV Notes')
        if notes is None:
            raise ValueError(f'{gap_path} has no "## CV Notes" section')
        path = self.path('cv_notes')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _util.write(path, notes)

    def write_company_research(self):
        """Copy research.md's Company section to scratch.

        The ranker uses only the company's mission and values (to spot
        boilerplate), so it reads this slice, not the whole research file.
        """
        research_path = self.path('research')
        if not os.path.isfile(research_path):
            raise FileNotFoundError(f'required file missing: {research_path}')
        company = retrieval_payload.extract_section(_util.read(research_path), '## Company')
        if company is None:
            raise ValueError(f'{research_path} has no "## Company" section')
        path = self.path('company_research')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _util.write(path, '## Company\n\n' + company + '\n')


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

def _label(key):
    """Return a file key as a readable prompt label."""
    words = key.rstrip('?').replace('_', ' ').capitalize()
    return words.replace('Jd', 'JD').replace('Cv ', 'CV ')


def build_prompt(agent, src, mode=None, input_file=None, continued=False):
    """Return the complete prompt for one dispatch; raise on any missing input."""
    spec = AGENTS[agent]
    if input_file and not os.path.isfile(input_file):
        raise FileNotFoundError(f'input file missing: {input_file}')
    if continued:
        if agent not in _CONTINUABLE:
            raise ValueError(f'{agent} is not continued across rounds')
        if not input_file:
            raise ValueError('--continued needs --input-file')
        action = ('Apply this input to the existing cv_content.md and drafting_plan.md.' if agent == 'cv-architect'
                  else 'Read these dispositions, re-read the revised cv_content.md, and re-assess. '
                       'Do not re-read your other sources.')
        return f'Input file: {input_file}\nCV content: {src.path("cv_content")}\n{action}'
    if agent == 'cv-architect':
        mode = mode or 'draft'
        if mode == 'revise' and not input_file:
            raise ValueError('cv-architect in revise mode needs --input-file')
        src.write_cv_notes()
    if 'company_research' in spec.get('files', []):
        src.write_company_research()

    lines = []
    if agent == 'cv-architect':
        lines.append(f'Mode: {mode}')
    for key in spec.get('facts', []):
        value = src.fact(key)
        if value:
            lines.append(f'{key.capitalize()}: {value}')
    if spec.get('folders'):
        lines.append(f'Application folder: {src.folder}')
        if agent != 'cv-architect':
            lines.append(f'Profile folder: {os.path.join(src.root, src.cfg["paths"]["profile"])}')
    if spec.get('axes'):
        found, missing = src.axis_files(spec['axes'])
        lines += [f'Axis file: {path}' for path in found]
        lines += [f'No rule file for: {value}' for value in missing]
    for key in spec.get('files', []):
        optional = key.endswith('?')
        path = src.path(key.rstrip('?'))
        if os.path.isfile(path):
            lines.append(f'{_label(key)}: {path}')
        elif not optional:
            raise FileNotFoundError(f'required file missing: {path}')
    if input_file:
        lines.append(f'Input file: {input_file}')
    if spec.get('note'):
        lines.append(spec['note'])
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Command-line entry point
# Reports failure to stderr with exit 1 so the calling skill halts per
# global-rules.md.
# ---------------------------------------------------------------------------

def main():
    """Parse argv and print the prompt between markers."""
    parser = argparse.ArgumentParser(description="print a subagent's complete dispatch prompt")
    parser.add_argument('agent', choices=sorted(AGENTS))
    parser.add_argument('--folder', required=True, help='absolute path to the application folder')
    parser.add_argument('--tier', default=None, help='leadership tier, when the session log has none')
    parser.add_argument('--mode', choices=['draft', 'revise'], default=None, help='cv-architect only')
    parser.add_argument('--input-file', default=None,
                        help='file holding contributions, findings, or dispositions from this run')
    parser.add_argument('--continued', action='store_true',
                        help='for an agent continued across rounds: send only the new input')
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        repo_root, cfg = _config.load()
        src = _Sources(os.path.abspath(args.folder), repo_root, cfg, args.tier)
        prompt = build_prompt(args.agent, src, args.mode, args.input_file, args.continued)
        print('=== PROMPT ===')
        print(prompt)
        print('=== END ===')
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
