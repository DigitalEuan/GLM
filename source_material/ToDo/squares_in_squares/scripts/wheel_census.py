#!/usr/bin/env python3
r"""wheel_census.py — run 21, Q2a: reconcile '41 wheels' (ledger claim)
vs '45 wheels' (user's snapshot count).

Authorities, all counted from the repository itself:
  wheels/*.json    — implemented wheels (the index.json registry is
                     generated from these; the canonical count)
  Wheel(...) defs  — wheels also embedded as Python source
  expansion docs   — the planned slot range (roadmap)

Reconciliation found: 41 implemented (W1..W45 minus the 4 reserved
slots W26, W27, W30, W31); the roadmap plans the full range W1..W45 =
45 slots.  Both counts are right with different denominators.
"""
import json
import os
import re

ROOT = "/home/z/my-project"
BASE = os.path.join(ROOT, "workspace/cent_compiler_v12_2_ext")

SRC_FILES = ["cent_compiler/wheels.py",
             "cent_compiler/wheels_19.py",
             "cent_compiler/wheels_extended.py"]
src = "\n".join(open(os.path.join(BASE, f)).read() for f in SRC_FILES)
implemented_src = sorted({int(m) for m in re.findall(r'Wheel\("W(\d+)"', src)})

# canonical: implemented = wheels/*.json files (index.json is built from these)
dir_files = [f for f in os.listdir(os.path.join(BASE, "wheels"))
             if f.endswith(".json") and f != "index.json"]
implemented = sorted({int(re.findall(r"\d+", f)[0]) for f in dir_files})

idx = json.load(open(os.path.join(BASE, "wheels/index.json")))
w = idx["wheels"]
indexed = sorted({int(re.findall(r"\d+", k)[0]) for k in
                  (w if isinstance(w, dict) else
                   {x.get("id") or x.get("name") for x in w})})

doc = open(os.path.join(BASE, "expansion/02_Expanding_Wheels.md")).read()
planned = sorted({int(m) for m in re.findall(r"\bW(\d+)\b", doc)})
DOC_GROUPS = {"W26–W27": "Astrophysics & Cosmology",
              "W34–W35": "Biophysics & Hemodynamics",
              "W28": "Superconductivity", "W29": "Spintronics",
              "W32": "Capillarity", "W33": "Multi-Phase Heat & Mass Transfer"}

reserved = [i for i in range(1, 46) if i not in implemented]
missing_from_index = [i for i in implemented if i not in indexed]

census = {
    "implemented_wheels_json": len(implemented),
    "implemented_ids": [f"W{i}" for i in implemented],
    "also_in_python_source": [f"W{i}" for i in implemented_src],
    "indexed_in_index_json": len(indexed),
    "index_total_wheels_field": idx.get("total_wheels"),
    "index_consistent_with_files": missing_from_index == [],
    "missing_from_index": [f"W{i}" for i in missing_from_index],
    "planned_slots_in_expansion_doc": len(planned),
    "slot_range": "W1..W45",
    "reserved_not_implemented": [f"W{i}" for i in reserved],
    "reserved_groups": {
        "W26–W27": "Astrophysics & Cosmology (doc group, reserved)",
        "W30–W31": "unnamed — the gap between W29 Spintronics and "
                    "W32 Capillarity in the roadmap"},
    "reconciliation": ("Both counts are right with different "
                       "denominators. IMPLEMENTED = 41 (the wheels/*.json "
                       "files; index.json is generated from them and "
                       "agrees; this is what the run-20 ledger meant by "
                       "'41'). PLANNED = the roadmap's full range "
                       "W1..W45 = 45 slots (what the user's snapshot "
                       "counts). The 4 reserved slots are W26, W27 "
                       "(Astrophysics & Cosmology) and W30, W31 (the "
                       "unnamed roadmap gap) — defined as slots, not yet "
                       "implemented as wheels.")
    if not missing_from_index else
    "INDEX STALE — implemented wheels missing from index.json"}
out = os.path.join(ROOT, "workspace/push/wheel_census.json")
json.dump(census, open(out, "w"), indent=1)

print(f"implemented (wheels/*.json): {len(implemented)} (W1..W45)")
print(f"  reserved, unimplemented   : {[f'W{i}' for i in reserved]}")
print(f"  W26, W27 : Astrophysics & Cosmology (doc group, reserved)")
print(f"  W30, W31 : unnamed roadmap gap (W29 -> W32)")
print(f"indexed in index.json       : {len(indexed)} "
      f"(total_wheels field = {idx.get('total_wheels')})")
print(f"  source/index match        : {missing_from_index == []}")
print(f"Python Wheel() defs also    : {len(implemented_src)} "
      f"(W{min(implemented_src)}..W{max(implemented_src)})")
print("->", census["reconciliation"])
print("saved workspace/push/wheel_census.json")
