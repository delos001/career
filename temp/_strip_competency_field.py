"""Strip Competency: lines from Experience_Inventory.md per cv-targeted-retrieval-architecture-2026-05 decision."""
from pathlib import Path

path = Path(r'C:\Users\delos\code\career\personal\knowledge\Experience_Inventory.md')
text = path.read_text(encoding='utf-8')
before = text.count('\n')
lines = text.splitlines(keepends=True)
out = [ln for ln in lines if not ln.startswith('Competency:')]
removed = len(lines) - len(out)
path.write_text(''.join(out), encoding='utf-8')
after = sum(1 for _ in (path.read_text(encoding='utf-8')).split('\n')) - 1
print(f'Removed {removed} Competency: lines')
print(f'Line count: {before} -> {after}')
