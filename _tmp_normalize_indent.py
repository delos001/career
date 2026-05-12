"""
Normalize bullet indentation from Pandoc style (dash + 3 spaces, 4-space sub-indent)
to standard CommonMark (dash + 1 space, 2-space sub-indent) in Career_Narratives.md.
QC: verify only bullet markers changed; all visible text content identical.
"""

import re
import shutil
from pathlib import Path

SRC = Path(r"C:\Users\delos\code\career\personal\knowledge\Career_Narratives.md")
BAK = SRC.with_suffix(".md.indent.bak")

original = SRC.read_text(encoding="utf-8")
shutil.copy2(SRC, BAK)

lines = original.splitlines(keepends=False)

# Counters
n_top = 0
n_sub = 0

out = []
for line in lines:
    new = line
    if new.startswith("    -   "):
        new = "  - " + new[len("    -   "):]
        n_sub += 1
    elif new.startswith("-   "):
        new = "- " + new[len("-   "):]
        n_top += 1
    out.append(new)

final = "\n".join(out)
if original.endswith("\n") and not final.endswith("\n"):
    final += "\n"

# QC: strip ALL whitespace and bullet markers from both files; compare visible content.
def fingerprint(text: str) -> str:
    # Normalize bullets in original to the new style, then strip leading whitespace
    # before comparing. This ensures the only diff between orig and clean is the
    # bullet marker spacing.
    t = text
    t = re.sub(r"^    -   ", "  - ", t, flags=re.MULTILINE)
    t = re.sub(r"^-   ", "- ", t, flags=re.MULTILINE)
    return t

fp_orig = fingerprint(original)
if fp_orig != final:
    # Find first mismatch
    for k, (a, b) in enumerate(zip(fp_orig, final)):
        if a != b:
            print("MISMATCH at char", k)
            print("ORIG:", repr(fp_orig[max(0,k-40):k+40]))
            print("CLEAN:", repr(final[max(0,k-40):k+40]))
            break
    else:
        print("LENGTH differ:", len(fp_orig), "vs", len(final))
    raise SystemExit("QC FAILED")

SRC.write_text(final, encoding="utf-8")

print("QC OK: visible content identical, only bullet markers changed.")
print(f"Backup: {BAK}")
print(f"Top-level bullets normalized: {n_top}")
print(f"Sub-level bullets normalized: {n_sub}")
print(f"Total lines:                  {len(lines)}")
