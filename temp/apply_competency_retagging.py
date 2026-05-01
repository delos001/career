"""Apply new Competency tags from competency_retagging_proposal.md to Experience_Inventory.md.

One-off migration script. Reads ID -> new-tags mapping from the proposal, walks the
inventory, replaces each entry's `Competency:` line value. Writes inventory back only
if proposal IDs and inventory IDs match exactly (1:1).
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROPOSAL = REPO / "temp" / "competency_retagging_proposal.md"
INVENTORY = REPO / "personal" / "knowledge" / "Experience_Inventory.md"

PROPOSAL_LINE = re.compile(r"^(EX-\d+|PR-\d+)\s*\|\s*OLD:.*?\|\s*NEW:\s*(.+?)\s*$")
ID_LINE = re.compile(r"^ID:\s*(EX-\d+|PR-\d+)\s*$")
COMPETENCY_LINE = re.compile(r"^Competency:\s*")


def parse_proposal(path: Path) -> dict[str, str]:
    new_tags: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = PROPOSAL_LINE.match(line)
        if m:
            entry_id, tags = m.group(1), m.group(2).strip()
            if entry_id in new_tags:
                print(f"WARNING: duplicate proposal entry {entry_id}", file=sys.stderr)
            new_tags[entry_id] = tags
    return new_tags


def apply(content: list[str], new_tags: dict[str, str]) -> tuple[list[str], set[str], set[str]]:
    inventory_ids: set[str] = set()
    applied_ids: set[str] = set()
    current_id: str | None = None
    out = list(content)
    for i, line in enumerate(out):
        id_match = ID_LINE.match(line)
        if id_match:
            current_id = id_match.group(1)
            inventory_ids.add(current_id)
            continue
        if current_id and COMPETENCY_LINE.match(line):
            if current_id in new_tags:
                out[i] = f"Competency: {new_tags[current_id]}"
                applied_ids.add(current_id)
            current_id = None
    return out, inventory_ids, applied_ids


def main() -> int:
    new_tags = parse_proposal(PROPOSAL)
    print(f"Proposal entries parsed: {len(new_tags)}")

    original_content = INVENTORY.read_text(encoding="utf-8").splitlines()
    updated_content, inventory_ids, applied_ids = apply(original_content, new_tags)

    print(f"Inventory entries (EX/PR): {len(inventory_ids)}")
    print(f"Updates applied: {len(applied_ids)}")

    proposal_only = set(new_tags) - inventory_ids
    inventory_only = inventory_ids - set(new_tags)
    if proposal_only:
        print(f"In proposal but not in inventory: {sorted(proposal_only)}")
    if inventory_only:
        print(f"In inventory but not in proposal: {sorted(inventory_only)}")

    if proposal_only or inventory_only or len(applied_ids) != len(new_tags):
        print("DISCREPANCIES FOUND — not writing inventory. Resolve and re-run.")
        return 1

    INVENTORY.write_text("\n".join(updated_content) + "\n", encoding="utf-8")
    print(f"Inventory updated: {INVENTORY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
