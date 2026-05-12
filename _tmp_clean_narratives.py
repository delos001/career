"""
One-off cleanup of Pandoc artifacts in Career_Narratives.md.
Writes a .bak backup, transforms in place, runs QC, and emits a report.
"""

import re
import shutil
from pathlib import Path

SRC = Path(r"C:\Users\delos\code\career\personal\knowledge\Career_Narratives.md")
BAK = SRC.with_suffix(".md.bak")

original = SRC.read_text(encoding="utf-8")
SRC.replace(BAK) if False else shutil.copy2(SRC, BAK)  # keep original at .bak

lines = original.splitlines(keepends=False)

# ---- Transformation pass over lines ----
out = []
removed_html_fence_blocks = 0
header_h3_with_colon = 0
header_h3_no_colon = 0
header_bold_outside = 0      # **[Name]{.underline}**:
header_bold_inside = 0       # **[Name]{.underline}:**
inline_underline_spans = 0
escape_apostrophe = 0
escape_dollar = 0

# Track every line's classification for QC
class_log = []  # list of (orig_idx, category, original_text, transformed_text_or_None)

i = 0
n = len(lines)
while i < n:
    line = lines[i]

    # 3-line html fence pattern (with possible surrounding blanks)
    if (line.strip() == "```{=html}"
        and i + 2 < n
        and lines[i + 1].strip() == "<!-- -->"
        and lines[i + 2].strip() == "```"):
        removed_html_fence_blocks += 1
        class_log.append((i, "fence_open", line, None))
        class_log.append((i + 1, "fence_comment", lines[i + 1], None))
        class_log.append((i + 2, "fence_close", lines[i + 2], None))
        i += 3
        continue

    new = line

    # ### [Name]{.underline}:
    m = re.match(r"^(#{1,6})\s+\[([^\]]+)\]\{\.underline\}:?\s*$", new)
    if m:
        hashes, name = m.group(1), m.group(2)
        had_colon = new.rstrip().endswith(":")
        new = f"{hashes} {name}"
        if had_colon:
            header_h3_with_colon += 1
            class_log.append((i, "h3_colon", line, new))
        else:
            header_h3_no_colon += 1
            class_log.append((i, "h3_no_colon", line, new))
    else:
        # **[Name]{.underline}**:
        m = re.match(r"^\*\*\[([^\]]+)\]\{\.underline\}\*\*:\s*$", new)
        if m:
            name = m.group(1)
            new = f"**{name}**:"
            header_bold_outside += 1
            class_log.append((i, "bold_outside", line, new))
        else:
            # **[Name]{.underline}:**
            m = re.match(r"^\*\*\[([^\]]+)\]\{\.underline\}:\*\*\s*$", new)
            if m:
                name = m.group(1)
                new = f"**{name}:**"
                header_bold_inside += 1
                class_log.append((i, "bold_inside", line, new))
            else:
                # inline residual `[Name]{.underline}` (no surrounding bold or heading)
                if "{.underline}" in new:
                    before = new
                    new = re.sub(r"\[([^\]]+)\]\{\.underline\}", r"\1", new)
                    inline_underline_spans += 1
                    class_log.append((i, "inline_underline", line, new))

    # escape fixes (apply to all lines — but only count when changed)
    if "\\'" in new:
        cnt = new.count("\\'")
        new = new.replace("\\'", "'")
        escape_apostrophe += cnt
    if "\\$" in new:
        cnt = new.count("\\$")
        new = new.replace("\\$", "$")
        escape_dollar += cnt

    out.append(new)
    i += 1

# Collapse 2+ consecutive blank lines to one
collapsed = []
prev_blank = False
collapsed_runs = 0
for line in out:
    is_blank = line.strip() == ""
    if is_blank and prev_blank:
        collapsed_runs += 1
        continue
    collapsed.append(line)
    prev_blank = is_blank

# Ensure trailing newline matches original convention
final = "\n".join(collapsed)
if original.endswith("\n") and not final.endswith("\n"):
    final += "\n"

# ---- QC: verify content preservation ----
# Build "content fingerprint" from the original by stripping all artifact patterns
# (without going through the transformation pipeline), then compare to cleaned content.

def fingerprint(text: str) -> str:
    t = text
    # strip 3-line html fence blocks
    t = re.sub(r"```\{=html\}\n<!-- -->\n```\n?", "", t)
    # strip header underline markup (keep heading body)
    t = re.sub(r"(#{1,6})\s+\[([^\]]+)\]\{\.underline\}:?", r"\1 \2", t)
    t = re.sub(r"\*\*\[([^\]]+)\]\{\.underline\}\*\*:", r"**\1**:", t)
    t = re.sub(r"\*\*\[([^\]]+)\]\{\.underline\}:\*\*", r"**\1:**", t)
    t = re.sub(r"\[([^\]]+)\]\{\.underline\}", r"\1", t)
    # escapes
    t = t.replace("\\'", "'").replace("\\$", "$")
    # whitespace normalize: collapse runs of blank lines, strip trailing spaces per line
    t = "\n".join(l.rstrip() for l in t.splitlines())
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

fp_orig = fingerprint(original)
fp_clean = fingerprint(final)

if fp_orig != fp_clean:
    # find first mismatch
    a, b = fp_orig, fp_clean
    for k, (ca, cb) in enumerate(zip(a, b)):
        if ca != cb:
            ctx_start = max(0, k - 60)
            print("FINGERPRINT MISMATCH at char", k)
            print("ORIG:", repr(a[ctx_start:k + 60]))
            print("CLEAN:", repr(b[ctx_start:k + 60]))
            break
    else:
        print("FINGERPRINT length differ:", len(a), "vs", len(b))
        if len(a) > len(b):
            print("ORIG tail:", repr(a[len(b):len(b) + 200]))
        else:
            print("CLEAN tail:", repr(b[len(a):len(a) + 200]))
    raise SystemExit("QC FAILED: content changed beyond declared transformations")

# Write cleaned content
SRC.write_text(final, encoding="utf-8")

# ---- Report ----
print("QC OK: content preserved (fingerprint match)")
print()
print(f"File: {SRC}")
print(f"Backup: {BAK}")
print(f"Original lines: {len(lines)}")
print(f"Cleaned  lines: {len(collapsed)}")
print(f"Lines removed: {len(lines) - len(collapsed)}")
print()
print("Transformations applied:")
print(f"  ### [Name]{{.underline}}: -> ### Name           x{header_h3_with_colon}")
print(f"  ### [Name]{{.underline}}  -> ### Name (no colon) x{header_h3_no_colon}")
print(f"  **[Name]{{.underline}}**: -> **Name**:          x{header_bold_outside}")
print(f"  **[Name]{{.underline}}:** -> **Name:**          x{header_bold_inside}")
print(f"  [Name]{{.underline}}      -> Name (inline)      x{inline_underline_spans}")
print(f"  3-line ```{{=html}} blocks removed             x{removed_html_fence_blocks}")
print(f"  \\' -> '  occurrences                           x{escape_apostrophe}")
print(f"  \\$ -> $  occurrences                           x{escape_dollar}")
print(f"  blank-line runs collapsed                      x{collapsed_runs}")
print()
print("Per-section breakdown of header transforms by name:")
from collections import Counter
names = Counter()
for _, cat, orig, new in class_log:
    if cat in ("h3_colon", "h3_no_colon", "bold_outside", "bold_inside"):
        m = re.search(r"\[([^\]]+)\]", orig)
        if m:
            names[m.group(1)] += 1
for name, cnt in sorted(names.items(), key=lambda x: (-x[1], x[0])):
    print(f"  {name}: {cnt}")
