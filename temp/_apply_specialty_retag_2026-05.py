#!/usr/bin/env python
"""Apply specialty retag per temp/specialty_retag_proposal_2026-05.md plus
the training-as-specialty-work clarification. Run with --apply to write."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INVENTORY = REPO_ROOT / "personal" / "knowledge" / "Experience_Inventory.md"

# EX-ID: (expected_old_specialty_value, target_new_specialty_value)
TARGETS: dict[str, tuple[str, str]] = {
    # data-science adds (some combined with removes of ai-engineering or data-engineering)
    "EX-024": ("clinical-operations | quality-compliance",
               "clinical-operations | quality-compliance | data-science"),
    "EX-072": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | data-science"),
    "EX-074": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | data-science"),
    "EX-075": ("data-engineering",
               "data-engineering | data-science"),
    "EX-076": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-079": ("clinical-operations | quality-compliance",
               "clinical-operations | quality-compliance | data-science"),
    "EX-080": ("clinical-operations | ai-engineering",
               "clinical-operations | data-science"),
    "EX-096": ("clinical-operations | quality-compliance | data-engineering",
               "clinical-operations | quality-compliance | data-engineering | data-science"),
    "EX-097": ("data-engineering",
               "data-science"),
    "EX-098": ("quality-compliance",
               "quality-compliance | data-science"),
    "EX-099": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | data-science"),
    "EX-100": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | data-science"),
    "EX-101": ("data-engineering",
               "data-engineering | data-science"),
    "EX-102": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-104": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-105": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | data-science"),
    "EX-106": ("clinical-operations | quality-compliance | data-engineering",
               "clinical-operations | quality-compliance | data-engineering | data-science"),
    "EX-107": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-108": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-109": ("clinical-operations | ai-engineering",
               "clinical-operations | data-science"),
    "EX-110": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-112": ("clinical-operations | data-engineering",
               "clinical-operations | data-science"),
    "EX-113": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-114": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-116": ("data-engineering",
               "data-engineering | data-science"),
    "EX-117": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-118": ("clinical-operations | quality-compliance",
               "clinical-operations | quality-compliance | data-science"),
    "EX-120": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | data-science"),
    "EX-121": ("clinical-operations | quality-compliance | data-engineering",
               "clinical-operations | quality-compliance | data-engineering | data-science"),
    "EX-122": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-127": ("clinical-operations",
               "clinical-operations | data-science | operations-strategy"),
    "EX-187": ("clinical-operations",
               "clinical-operations | data-science"),

    # operations-strategy adds (some combined with removes of ai-engineering, data-engineering, quality-compliance, people-leadership)
    "EX-041": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | operations-strategy"),
    "EX-045": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-046": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-047": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-048": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-049": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | operations-strategy"),
    "EX-085": ("clinical-operations | quality-compliance | data-engineering",
               "clinical-operations | quality-compliance | data-engineering | operations-strategy"),
    "EX-095": ("data-engineering | ai-engineering",
               "data-engineering | operations-strategy"),
    "EX-124": ("clinical-operations | data-engineering | quality-compliance",
               "clinical-operations | data-engineering | quality-compliance | operations-strategy"),
    "EX-125": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | operations-strategy"),
    "EX-126": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | operations-strategy"),
    "EX-128": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-132": ("quality-compliance | data-engineering",
               "quality-compliance | data-engineering | operations-strategy"),
    "EX-133": ("clinical-operations | data-engineering",
               "clinical-operations | data-engineering | operations-strategy"),
    "EX-137": ("data-engineering | quality-compliance",
               "data-engineering | quality-compliance | operations-strategy"),
    "EX-143": ("data-engineering",
               "operations-strategy"),
    "EX-144": ("data-engineering",
               "data-engineering | operations-strategy"),
    "EX-147": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-148": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-150": ("people-leadership",
               "operations-strategy"),
    "EX-151": ("people-leadership",
               "operations-strategy"),
    "EX-152": ("data-engineering",
               "data-engineering | operations-strategy"),
    "EX-157": ("clinical-operations | quality-compliance | people-leadership",
               "clinical-operations | quality-compliance | operations-strategy"),
    "EX-158": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-159": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-160": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-161": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-162": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-165": ("people-leadership | clinical-operations",
               "people-leadership | clinical-operations | operations-strategy"),
    "EX-168": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-170": ("people-leadership",
               "operations-strategy"),
    "EX-171": ("clinical-operations | quality-compliance",
               "clinical-operations | operations-strategy"),
    "EX-182": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-191": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-192": ("clinical-operations",
               "clinical-operations | operations-strategy"),
    "EX-202": ("data-engineering | clinical-operations",
               "data-engineering | clinical-operations | operations-strategy"),
    "EX-205": ("data-engineering | ai-engineering",
               "data-engineering | operations-strategy"),

    # people-leadership adds (where direct people-management or change-leadership was missing)
    "EX-166": ("clinical-operations",
               "clinical-operations | people-leadership"),
    "EX-174": ("clinical-operations",
               "clinical-operations | people-leadership"),
    "EX-176": ("clinical-operations",
               "clinical-operations | people-leadership"),
    "EX-184": ("clinical-operations",
               "clinical-operations | people-leadership"),

    # Training-as-specialty-work knock-ons
    "EX-016": ("clinical-operations",
               "clinical-operations | quality-compliance"),
    "EX-030": ("clinical-operations",
               "clinical-operations | quality-compliance"),
    "EX-183": ("clinical-operations",
               "clinical-operations | data-engineering"),
    "EX-188": ("clinical-operations",
               "clinical-operations | data-science"),
    "EX-189": ("clinical-operations",
               "clinical-operations | quality-compliance"),
}


def main(apply: bool) -> int:
    text = INVENTORY.read_text(encoding="utf-8")

    applied_count = 0
    skipped_count = 0
    failures: list[tuple[str, str]] = []

    for ex_id, (expected_old, target_new) in TARGETS.items():
        pattern = re.compile(
            r"(ID: " + re.escape(ex_id) + r"\n(?:[^\n]+\n)*?Specialty: )([^\n]+)"
        )
        m = pattern.search(text)
        if not m:
            failures.append((ex_id, "ID not found"))
            continue
        current = m.group(2).strip()
        if current == target_new:
            skipped_count += 1
            print(f"  SKIP   {ex_id}: already at target")
            continue
        if current != expected_old:
            failures.append(
                (ex_id, f"expected '{expected_old}' but found '{current}'")
            )
            continue
        text = text[: m.start()] + m.group(1) + target_new + text[m.end():]
        applied_count += 1
        print(f"  CHANGE {ex_id}: {expected_old}  ->  {target_new}")

    print()
    print(f"{applied_count} changes ready, {skipped_count} skipped, {len(failures)} failures")
    for ex_id, reason in failures:
        print(f"  FAIL {ex_id}: {reason}")

    if failures:
        print("\nFailures detected; refusing to write changes.")
        return 1

    if apply:
        INVENTORY.write_text(text, encoding="utf-8")
        print("\nChanges written to inventory.")
    else:
        print("\nDry run; no changes written. Use --apply to write.")
    return 0


if __name__ == "__main__":
    sys.exit(main(apply="--apply" in sys.argv))
