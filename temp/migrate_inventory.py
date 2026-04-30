"""One-time migration: restructure EX/PR entries in Experience_Inventory.md.

Idempotent — safe to re-run.

Operations:
- Split Role/Project compound string into Title-or-Project + Company.
- Move bold description, Context, Impact to end of block.
- Prefix bold description with `Description:` (preserve bold delimiters).
- Rename: Role Level -> Level; Org Context -> Work-state.
- Translate Level values (IC -> ic; Manager / Senior Manager / Director -> leadership).
- Translate Work-state values (Mature/Enterprise -> mature; Scaling -> scaling; Greenfield -> greenfield).
- Insert empty Industry, Specialty, Orientation fields.
- Reorder fields: ID, Title/Project, Company, axis tags (Industry, Specialty, Orientation, Level, Work-state),
  classifications (Outcome, Capability), provenance (Added, Last Used), prose (Description, Context, Impact).

NOT done here (queued for cleanup discussion): Outcome -> Purpose rename, Capability fate,
Independent work-state re-tagging on PR entries, per-entry axis value tagging.
"""
import re
from pathlib import Path

PATH = Path('personal/knowledge/Experience_Inventory.md')

LEVEL_MAP = {
    'IC': 'ic',
    'Manager': 'leadership',
    'Senior Manager': 'leadership',
    'Director': 'leadership',
}

WORK_STATE_MAP = {
    'Mature/Enterprise': 'mature',
    'Scaling': 'scaling',
    'Greenfield': 'greenfield',
    # Independent stays as-is; PR entries need per-entry re-tagging later.
}

NEW_AXIS_FIELDS = ['Industry', 'Specialty', 'Orientation']

FIELD_ORDER = [
    'Industry', 'Specialty', 'Orientation',
    'Level', 'Work-state',
    'Outcome', 'Capability',
    'Added', 'Last Used',
]


def restructure_entry(block: str) -> str:
    lines = block.split('\n')
    fields = {}
    bold_desc = None
    context = None
    impact = None
    role_value = None
    is_pr = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if line.startswith('Description:'):
            _, _, val = line.partition(':')
            bold_desc = val.strip()
            continue
        if stripped.startswith('**') and stripped.endswith('**'):
            bold_desc = stripped
            continue
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip()
        val = val.strip()
        if key == 'ID':
            fields['ID'] = val
            is_pr = val.startswith('PR-')
        elif key in ('Role', 'Project'):
            role_value = val
        elif key == 'Context':
            context = val
        elif key == 'Impact':
            impact = val
        else:
            fields[key] = val

    # Determine title/project and company.
    title = fields.pop('Title', None) or fields.pop('Project', None)
    company = fields.pop('Company', None)
    if role_value and '|' in role_value:
        legacy_title, _, legacy_company = role_value.partition('|')
        if not title:
            title = legacy_title.strip()
        if not company:
            company = legacy_company.strip()
    elif role_value and not title:
        title = role_value
    title = title or ''
    company = company or ''

    role_field = 'Project' if is_pr else 'Title'

    # Renames.
    if 'Role Level' in fields:
        fields['Level'] = fields.pop('Role Level')
    if 'Org Context' in fields:
        fields['Work-state'] = fields.pop('Org Context')

    # Value translations.
    if 'Level' in fields:
        fields['Level'] = LEVEL_MAP.get(fields['Level'], fields['Level'])
    if 'Work-state' in fields:
        fields['Work-state'] = WORK_STATE_MAP.get(fields['Work-state'], fields['Work-state'])

    # Add empty axis fields where missing.
    for nf in NEW_AXIS_FIELDS:
        if nf not in fields:
            fields[nf] = ''

    out = []
    out.append(f"ID: {fields['ID']}")
    out.append(f"{role_field}: {title}")
    out.append(f"Company: {company}")
    for f in FIELD_ORDER:
        if f in fields:
            v = fields[f]
            out.append(f"{f}: {v}" if v else f"{f}:")
    if bold_desc:
        out.append(f"Description: {bold_desc}")
    if context:
        out.append(f"Context: {context}")
    if impact:
        out.append(f"Impact: {impact}")
    return '\n'.join(out)


def main():
    with open(PATH, 'r', encoding='utf-8', newline='') as f:
        text = f.read()

    if '\r\n' in text:
        eol = '\r\n'
        text = text.replace('\r\n', '\n')
    else:
        eol = '\n'

    blocks = re.split(r'\n\n+', text)

    transformed = 0
    for i, block in enumerate(blocks):
        if re.match(r'^ID:\s*(EX|PR)-\d+', block):
            blocks[i] = restructure_entry(block)
            transformed += 1

    out_text = '\n\n'.join(blocks)
    if eol == '\r\n':
        out_text = out_text.replace('\n', '\r\n')

    with open(PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(out_text)

    print(f"Transformed {transformed} entries.")


if __name__ == '__main__':
    main()
