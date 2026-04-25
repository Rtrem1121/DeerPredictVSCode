"""Scan Python source files in the repo for mojibake (garbled multi-byte sequences).

Usage:
    python tools/scan_mojibake.py              # scan entire repo
    python tools/scan_mojibake.py backend/     # scan a sub-tree
"""
import re
import sys
from pathlib import Path

# Multi-byte non-ASCII runs that look like double-encoded UTF-8 / CP437 escapes.
_PATTERN = re.compile(
    r"[\u2261\u0393\u2229\u2248\xc2\u00ac\u2264\u2265\u2192\u2534"
    r"\u2551\u255c\u2514\u252c\u255d\u2557\u2510\u2512\u256a\u25c0"
    r"\u2580\u2584\u2588\u2591\u2592\u2593][\u0080-\uffff]+"
)

_EXCLUDE_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    "htmlcov", ".mypy_cache", ".pytest_cache",
}

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

total_files = 0
total_hits = 0

for path in sorted(root.rglob("*.py")):
    # Skip excluded directories
    if any(part in _EXCLUDE_DIRS for part in path.parts):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        continue

    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        tokens = _PATTERN.findall(line)
        if tokens:
            hits.append((lineno, tokens, line.rstrip()))

    if hits:
        total_files += 1
        total_hits += sum(len(t) for _, t, _ in hits)
        print(f"\n{path}:")
        for lineno, tokens, line in hits:
            print(f"  line {lineno}: {[repr(t) for t in tokens]}")
            print(f"    {line[:120]}")

if total_hits == 0:
    print("No mojibake found.")
else:
    print(f"\n{total_hits} mojibake token(s) across {total_files} file(s).")
