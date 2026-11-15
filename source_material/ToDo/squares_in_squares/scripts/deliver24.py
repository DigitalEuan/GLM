#!/usr/bin/env python3
"""deliver24.py — run 24 deliverables.

Run 24 = NEXT_STEPS.md execution (the updated upload/NEXT_STEPS.md):
  - archaeology + run-23 attribution correction (§6 cross-check)
  - P3 source watch (idempotent import + live register check + the
    Atlas-verified bounds: 6 at-grid rows now PROVEN optimal)
  - P2 family-seeded polish (the open experiment; A/B vs run 23)
  - P4 fixpoint propagation / confirmation pass
  - P1 decision (documented as the named next architecture)

Produces:
  1. download/run24_outcomes.json — the run ledger
  2. README.md Run 24 section (+ the run-23 correction note)
  3. REPRODUCE.md A16
  4. download/README.md top-level refresh (standing pattern)
  5. download/run24/ tree + MANIFEST.md
  6. ast.parse verification, no .pyc
"""
import ast
import json
import math
import os
import shutil
import subprocess

W = "/home/z/my-project"
DL = f"{W}/download/run24"
TAB = f"{W}/workspace/submission/table.json"

tab = json.load(open(TAB))
score = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())

# ------------------------------------------------ read sweep + P3 outcomes
p2_path = f"{W}/workspace/push/p2_seed_polish.json"
p2 = json.load(open(p2_path)) if os.path.exists(p2_path) else {}
p2_cells = p2.get("cells", [])
p2_finds = p2.get("finds", [])
p2_hard = sum(c.get("hard_checks", 0) for c in p2_cells)
p2_rows = sorted({c["n"] for c in p2_cells})

# ------------------------------------------------------------- 1. ledger
led = {
 "run": 24, "date": "2026-11-05",
 "user_request": ("'NEXT_STEPS.md' has been updated since run 13, can we "
                   "see if there are things we can do in there to help "
                   "this grid puzzle project? - push on as logical."),
 "input": "upload/NEXT_STEPS.md (2026-11-04 22:35 delivery bundle)",
 "attribution_correction": {
   "issue": ("run-23 README/final reply claimed the Nov-5 08:03 table "
             "write (22.887471 -> 22.823536, -0.0639) was 'run 19's "
             "application of 6 run18-frontier rows'."),
   "correct_record": ("git + leech cross-check: the 08:03 write applied "
                      "109 rows ALL tagged run18-frontier = the community "
                      "import (76 records, +0.050264) + the cascade "
                      "propagation (33 conversions, +0.013671), total "
                      "+0.063934787 — exactly NEXT_STEPS §6's run-13 "
                      "session. The 6 rows my run-23 reply cited "
                      "(183, 211, 308, 343, 380, 419) are 6 of the 109 "
                      "(the only ones below their grid), not the whole "
                      "delta. The leech 'atlas' (08:02) is a snapshot of "
                      "our own table pre-write, so 'beat the atlas' was "
                      "circular — already retracted in run 23."),
   "applies_to": "README.md Run 23 section (corrected by this run's "
                 "section) and the leech_map.json reading of run 23."},
 "executed": {
   "P3_source_watch": {
     "local_lists": ("import_atlas.py re-run: idempotent — applied 0, "
                     "skipped 4 (table already <= atlas), rejected 320; "
                     "table is exactly at the certified frontier n<=324"),
     "live_register": ("github.com/evand/square-packing checked "
                       "2026-11-05: no record changes visible after "
                       "2026-10-17 (page snapshot predates; no commit "
                       "dates shown for lists/)"),
     "gained_bounds": {
       "proven_optimal_at_grid": {
         "13": 4, "21": 5, "32": 6, "45": 7, "60": 8, "61": 8},
       "families": "s(k^2-3)=k (k>=6), s(k^2-4)=k (k>=5) — proven",
       "lower_bound": "s(12) >= 15680/3951 = 3.9686 (proven; grid 4 row "
                      "now has a certified gap of only 0.0314)",
       "note": ("the 6 at-grid rows above are now PROVEN optimal at the "
                "trivial grid — excluded from all future sweeps; their "
                "src stays 'grid' and they leave the open set")}},
   "P2_family_seeded_polish": {
     "status": "executed (this run) — the open experiment",
     "design": ("26 rows (best per-n design from the gobel5 near-miss "
                "pool, gap<=0.002, minus the 6 proven-optimal) x targets "
                "(grid-0.0005, grid-0.002) x 2 seeds x 8 hops; the seed "
                "is the REBUILT gobel5 corner-band family state (verified "
                "count + extent + non-overlap), the hop loop and anneal "
                "streams identical to soft_relax.hop_search — the A/B "
                "against run 23 differs ONLY in the initial state"),
     "rebuild_gate": ("26/26 seeds rebuilt ok; gate fixed to worst_pen "
                      "<= 1e-9 (exact-geometry states show +4e-16 "
                      "float artifacts, not overlaps)"),
     "cells": len(p2_cells), "hard_checks": p2_hard,
     "finds": len(p2_finds),
     "rows": p2_rows,
     "reading": ("")},
   "P4_fixpoint": ("cascade3 + closure_apply re-run to fixpoint after "
                   "the sweep (mandatory loop order; no-change "
                   "confirmation included)"),
   "P1_decision": ("generalized Gobel strip (w in {1,2,3}, two "
                    "independent end staircases) NOT executed this run "
                    "(budget); it stays the named next architecture, "
                    "with the 8489-design near-miss pool as its seed map "
                    "and the acceptance test n=44/58/31 unchanged")},
 "score": {"before": 22.823536149, "after": round(score, 9)},
 "next": [
   "P1 generalized Gobel strip sweep (the named architecture)",
   "tier-1 infeasibility theorem for the small-n level-1 set (the "
   "empirical unanimity of runs 20-24 is now 4-run-deep)",
   "weekly import_atlas re-run (the register moves; 76 records appeared "
   "in ~7 weeks)"],
}
json.dump(led, open(f"{W}/download/run24_outcomes.json", "w"), indent=1)
print("1. ledger written; score after:", round(score, 9))

# ---------------------------------------------------- 2. README Run 24
sec = f"""

# Run 24 (2026-11-05): NEXT_STEPS.md execution

User: "NEXT_STEPS.md has been updated since run 13 — push on as logical."

## Correction of the Run 23 record

The Nov-5 08:03 table write (22.887471 -> 22.823536, -0.0639) was NOT
"run 19 applying 6 rows": it applied 109 rows, all tagged run18-frontier
— the community import (76 records, +0.050264) plus the cascade
propagation (33 conversions, +0.013671), exactly NEXT_STEPS S6.  The 6
rows run 23 cited were the 6 of the 109 that landed below their grid.

## P3 source watch (executed)

Local lists re-imported: idempotent (applied 0, skipped 4, rejected
320) — the table is exactly at the community's certified frontier for
n <= 324.  Live register (2026-11-05): no record changes visible after
2026-10-17.  Verified bounds gained: s(13)=4, s(21)=5, s(32)=6,
s(45)=7, s(60)=s(61)=8 PROVEN — six at-grid rows now proven optimal at
the trivial grid and excluded from all future sweeps; s(12) >= 15680/3951
= 3.9686 (the grid-4 row for n=12 has a certified gap of only 0.0314);
families s(k^2-3)=k, s(k^2-4)=k proven.

## P2 family-seeded polish (executed — the open experiment)

NEXT_STEPS P2 was still open: every previous sweep (runs 20-23) seeded
from random states.  This run rebuilt the 26 best per-n corner-band
family designs from the gobel5 near-miss pool (8489 entries, gap <=
0.002), verified each seed (count, extent, non-overlap), and ran the
identical hop loop as run 23 — same seeds, same anneal streams, ONLY
the initial state differs.

Result: {len(p2_cells)} cells, {p2_hard} hard checks, {len(p2_finds)}
finds.  (Details in workspace/push/p2_seed_polish.json.)

## P4 propagation + P1 decision

cascade3 + closure_apply re-run to fixpoint after the sweep (mandatory
order).  P1 (generalized Gobel strip) not executed this run — budget;
it remains the named next architecture, seed map = the near-miss pool.

Score: {score:.9f} (before 22.823536149).
"""
readme = open(f"{W}/README.md").read()
if "Run 24 (2026-11-05)" not in readme:
    open(f"{W}/README.md", "w").write(readme + sec)
    print("2. README Run 24 appended")
else:
    print("2. README already has Run 24 (idempotent)")

# ---------------------------------------------------- 3. REPRODUCE A16
rep = open(f"{W}/REPRODUCE.md").read()
if "## A16." not in rep:
    rep += """

## A16. Run 24: NEXT_STEPS execution

```bash
python3 scripts/import_atlas.py      # P3: idempotent community import
python3 scripts/p2_seed_polish.py     # P2: family-seeded polish (~50 min)
python3 scripts/cascade3.py           # P4: fixpoint propagation
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py     # rebuilds submission.csv
```
"""
    open(f"{W}/REPRODUCE.md", "w").write(rep)
    print("3. REPRODUCE A16 appended")
else:
    print("3. REPRODUCE already has A16 (idempotent)")

# ------------------------------------------- 4. top-level download README
shutil.copy(f"{W}/README.md", f"{W}/download/README.md")
print("4. download/README.md refreshed (top level)")

# ---------------------------------------------------- 5. run24 tree
shutil.rmtree(DL, ignore_errors=True)
NEW = [
 ("scripts/p2_seed_polish.py", "NEW",
  "P2: family-seeded hop polish (A/B vs run 23; only the seed differs)"),
 ("scripts/deliver24.py", "NEW", "this build script"),
 ("workspace/push/p2_seed_polish.json", "NEW",
  f"{len(p2_cells)}-cell P2 results ledger"),
 ("README.md", "EDITED", "Run 24 section + run-23 correction"),
 ("REPRODUCE.md", "EDITED", "A16 section"),
 ("run24_outcomes.json", "NEW", "run 24 ledger (also at download/ top)"),
]
rows = []
for rel, st, what in NEW:
    dst = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(dst) or DL, exist_ok=True)
    src = (f"{W}/download/run24_outcomes.json"
           if rel == "run24_outcomes.json" else f"{W}/{rel}")
    if os.path.exists(src):
        shutil.copy(src, dst)
        rows.append((rel, st, os.path.getsize(dst), what))

man = ["# Run 24 deliverables — new/edited files only",
       "",
       "| Repository path | Status | Bytes | What it is |",
       "|---|---|---|---|"]
for rel, st, sz, what in rows:
    man.append(f"| {rel} | {st} | {sz} | {what} |")
man += ["",
        "P3 used scripts/import_atlas.py unchanged (idempotent re-run).",
        "P4 used scripts/cascade3.py, scripts/closure_apply.py, "
        "scripts/final_assembly.py unchanged.",
        "No .pyc (ast.parse verification only)."]
open(f"{DL}/MANIFEST.md", "w").write("\n".join(man) + "\n")
print("5. download/run24/ tree built:", len(rows), "files")

# ---------------------------------------------------- 6. verification
for rel, st, sz, what in rows:
    if rel.endswith(".py"):
        ast.parse(open(f"{DL}/{rel}").read())
    if rel.endswith(".json"):
        json.load(open(f"{DL}/{rel}"))
bad = [f for _, _, fs in os.walk(DL) for f in fs
       if f.endswith(".pyc")]
assert not bad, bad
print("6. verification clean")
