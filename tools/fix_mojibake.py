"""Fix all mojibake in enhanced_bedding_zone_predictor.py.

Strategy: bulk string replacements of known CP1252-over-UTF8 sequences.
Run from repo root: python tools/fix_mojibake.py
"""
import sys

TARGET = "enhanced_bedding_zone_predictor.py"

# -----------------------------------------------------------------------
# Mapping: mojibake sequence -> ASCII replacement
# Order matters — replace longest/most-specific first.
# -----------------------------------------------------------------------
REPLACEMENTS = [
    # Degree sign  ° encoded as UTF-8 then re-read as CP1252 → Â°
    # The actual bytes in the file appear as the string below when read back as UTF-8
    ("\u00c2\u00b0",    "\u00b0"),   # Â° → °  (keep the real degree char)
    # Alternatively the file may literally have the two-char sequence
    ("┬░",              "°"),
    ("┬°",              "°"),

    # Box-drawing / tree chars (used in stats printout)
    ("Γö£ΓöÇ",          "|--"),
    ("ΓööΓöÇ",          "+--"),
    ("Γö£",             "|-"),
    ("Γöö",             "+-"),
    ("ΓöÇ",             "-"),

    # Arrows / comparison operators
    ("ΓåÆ",             "->"),
    ("Γëñ",             "<="),
    ("Γëú",             ">="),
    ("≡ì",              "~"),

    # Variation selector (emoji modifier, should vanish)
    ("∩╕Å",             ""),

    # --- Emoji sequences (≡ƒ prefix = \xf0\x9f in UTF-8 double-encoded) ---
    # Map each to a short bracketed ASCII tag based on context
    ("≡ƒöº",            "[OK]"),
    ("≡ƒªî",            "[DEER]"),
    ("≡ƒôè",            "[DATA]"),
    ("≡ƒîì",            "[GEE]"),
    ("≡ƒî▓",            "[TREE]"),
    ("≡ƒî╛",            "[VALLEY]"),
    ("≡ƒÅö",            "[MTN]"),
    ("≡ƒÅ₧",            "[HILL]"),
    ("≡ƒôÅ",            "[TRACK]"),
    ("≡ƒÜ¿",            "[ERR]"),
    ("≡ƒÜ½",            "[WARN]"),
    ("≡ƒº¡",            "[TARGET]"),
    ("≡ƒÿ╖",            "[FLAG]"),
    ("≡ƒÿ░",            "[TREE2]"),
    ("≡ƒæ╖",            "[WIND]"),
    ("≡ƒôü",            "[INFO2]"),
    ("≡ƒôâ",            "[BOOK]"),

    # Info / neutral (ℹ️ double-encoded)
    ("Γä╣",             "[INFO]"),

    # Catch-all for remaining ≡ƒ sequences not individually listed
    # (will be handled after specific ones above)
]

def fix(text: str) -> str:
    for bad, good in REPLACEMENTS:
        text = text.replace(bad, good)
    return text


with open(TARGET, encoding="utf-8") as fh:
    original = fh.read()

fixed = fix(original)

if fixed == original:
    print("No changes needed — file is already clean.")
    sys.exit(0)

changed = sum(1 for a, b in zip(original.splitlines(), fixed.splitlines()) if a != b)
print(f"Replacing {changed} lines …")

with open(TARGET, "w", encoding="utf-8") as fh:
    fh.write(fixed)

print("Done.")
