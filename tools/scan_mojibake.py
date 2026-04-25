"""Scan and fix mojibake in enhanced_bedding_zone_predictor.py"""
import re, sys

TARGET = "enhanced_bedding_zone_predictor.py"

with open(TARGET, encoding="utf-8") as f:
    text = f.read()

# Identify unique multi-byte non-ASCII runs (likely mojibake)
pattern = re.compile(r"[\u2261\u0393\u2229\u2248\xc2\u00ac\u2264\u2265\u2192\u2534][\u0080-\uffff]+")
matches = sorted(set(pattern.findall(text)))
print(f"Found {len(matches)} unique mojibake tokens:")
for m in matches:
    print(repr(m))
