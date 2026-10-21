"""Inventory exported top-level SCL objects without modifying the reference files."""
from pathlib import Path
import csv
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Reference_Project"
OUTPUT = ROOT / "docs" / "TIA_Reference_Inventory.csv"
objects = {}
for path in sorted(SOURCE.glob("*.scl")):
    text = path.read_text(encoding="utf-8-sig")
    pattern = r'^\s*(TYPE|FUNCTION_BLOCK|FUNCTION|DATA_BLOCK)\s+"([^"\n]+)".*?^\s*END_\1\b'
    for match in re.finditer(pattern, text, re.M | re.S):
        kind, name = match.group(1, 2)
        body = match.group(0).strip()
        # Preserve all source text in the hash; normalize only line endings.
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        objects.setdefault((kind, name), []).append((path.name, digest, len(body.splitlines())))

OUTPUT.parent.mkdir(exist_ok=True)
with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["Kind", "Name", "Copies", "DistinctVersions", "Lines", "SourceFiles", "SHA256"])
    for (kind, name), entries in sorted(objects.items()):
        hashes = sorted({entry[1] for entry in entries})
        writer.writerow([kind, name, len(entries), len(hashes), entries[0][2],
                         "; ".join(entry[0] for entry in entries), "; ".join(hashes)])

print(f"SCL files: {len(list(SOURCE.glob('*.scl')))}; unique objects: {len(objects)}")
for kind in ("TYPE", "DATA_BLOCK", "FUNCTION", "FUNCTION_BLOCK"):
    print(f"{kind}: {sum(key[0] == kind for key in objects)}")
conflicts = [name for (_, name), entries in objects.items() if len({e[1] for e in entries}) > 1]
print(f"Objects with differing copies: {conflicts}")
print(f"Empty files: {[p.name for p in SOURCE.iterdir() if p.is_file() and p.stat().st_size == 0]}")
print(f"Written: {OUTPUT}")
