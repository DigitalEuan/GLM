#!/usr/bin/env python3
"""Bulk-parse the fetched CFSG sporadic Lean files."""
import sys
sys.path.insert(0, '/home/z/my-project/aristotle')
from pathlib import Path
from monster_wheel import default_monster_wheel

w = default_monster_wheel()
print(f"Wheel has {len(w)} entries before absorption.")
total_added = 0
total_already_known = 0
for lean_file in sorted(Path('/tmp/cfsg_test').glob('*.lean')):
    entries = w.parse_cfsg_lean_file(lean_file)
    for e in entries:
        if e.oeis_id not in w:
            w.register(e)
            total_added += 1
        else:
            total_already_known += 1
    if entries:
        ids_orders = [(e.oeis_id, e.terms[0]) for e in entries]
        print(f"  {lean_file.name:12s}  -> {len(entries)} entries: {ids_orders}")
    else:
        print(f"  {lean_file.name:12s}  -> (no card_<X> declarations found)")

print(f"\nWheel has {len(w)} entries after absorption.")
print(f"  added {total_added} new; {total_already_known} already known (skipped).")
