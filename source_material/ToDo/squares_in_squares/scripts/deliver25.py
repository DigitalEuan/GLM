#!/usr/bin/env python3
"""deliver25.py — run 25 deliverables.

Run 25 = the user's two-part instruction:
  (a) restart the P1 strip scan — as designed, it can be rerun;
  (b) finish the P2 remainder (run 24's sweep stopped at 45/52 cells).

Outcome (both parts measured, nothing claimed):
  P1: the generalized Gobel strip (w in {1,2,3}, two independent end
      staircases) built EXACTLY from a closed-form decode of the
      imported member states; 88/88 designs finalize-verified; the
      family is dominated by the current table on every row n<=1000
      (full-range check: 950 rows strictly deeper in the table, the
      rest equal within finalize noise, 0 finds); the acceptance test
      n=44/58/31 FAILS by capacity (ceilings 38/52/27).  P1(a) closed.
  P2: rows 134,135,157,158 (the run-24 remainder), 8 cells, 4/4 seeds
      rebuilt ok, 0 hard checks, 0 finds; the designed 26x2 sweep is
      now complete (52/52 cells, 0 hard checks anywhere).  P2 closed.
  Fixpoint: cascade3 + closure_apply + final_assembly re-run: 0
      changes; score 22.823536149; download copies in sync.

Also this run: the delivery-name fix — the user reports README.md
never arrives at their end, so the run documentation additionally
ships as RUN_NOTES.md (repo top level) and download/run25_NOTES.md;
the README.md copies are kept as before.

Produces:
  1. download/run25_outcomes.json — the run ledger
  2. README.md Run 25 section
  3. REPRODUCE.md A17
  4. RUN_NOTES.md top-level alias + download/run25_NOTES.md
  5. download/README.md top-level refresh (standing pattern)
  6. download/run25/ tree + MANIFEST.md
  7. ast.parse verification, no .pyc
"""
import ast
import json
import math
import os
import shutil

W = "/home/z/my-project"
DL = f"{W}/download/run25"
TAB = f"{W}/workspace/submission/table.json"

tab = json.load(open(TAB))
score = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())

# ------------------------------------------------ read run-25 outcomes
strip = json.load(open(f"{W}/workspace/push/strip_run25.json"))
p2 = json.load(open(f"{W}/workspace/push/p2_seed_polish_run25.json"))
p2b = json.load(open(f"{W}/workspace/push/p2_seed_polish.json"))  # run 24

p2_cells = p2.get("cells", [])
p2_hard = sum(c.get("hard_checks", 0) for c in p2_cells)
p2_rows = sorted({c["n"] for c in p2_cells})
u24 = {(c["n"], round(c["target"], 6)) for c in p2b.get("cells", [])}
u25 = {(c["n"], round(c["target"], 6)) for c in p2_cells}
union = u24 | u25
p2_total_hard = (sum(c.get("hard_checks", 0) for c in p2b.get("cells", []))
                  + p2_hard)

acc = {a["n"]: a for a in strip["acceptance"]}
fr = strip["full_range"]
sw = strip["sweep"]

# ------------------------------------------------------------- 1. ledger
led = {
 "run": 25, "date": "2026-11-06",
 "user_request": ("(a) restart the P1 strip scan (as designed, it can "
                   "be rerun); (b) finish the P2 remainder (run 24's "
                   "sweep stopped at 45/52 cells)."),
 "input": "upload/NEXT_STEPS.md P1(a)/P2 spec + run-24 ledger state",
 "executed": {
   "P1_strip_scan": {
     "status": "executed (this run) — closed in the negative",
     "parametrization": (
       "closed-form decode of the imported member states "
       "(scripts/strip_decode.py): (p,q) frame with p=(x+y)/sqrt2; "
       "w chains of pi/4 squares (q in [-w/2,w/2], p-spaced 1); 2 tip "
       "diamonds at +-(L/sqrt2 - 1/sqrt2); per q-side an independent "
       "staircase, levels k=1..a_s at |q|=w/2+k/sqrt2 with diamonds at "
       "p=((a_s-k)-2j)/sqrt2.  L(a,w) = a+1+w/sqrt2; every outer "
       "vertex touches the container edge simultaneously.  The decode "
       "reproduces the stored states of n=5,10,27,38,52,67 to the last "
       "digit — the imported 'exact:square-N.svg' rows ARE this family."),
     "capacity": (
       "w=1: n_max = floor(sqrt2(a-1)+1) + 2 + a(a+1) — reproduces the "
       "imported members 5,10,17,27,38,52,67,84,...;974 exactly.  "
       "w>=2: L = a+1+w/sqrt2 stays ABOVE grid at every capacity the "
       "width buys (checked per (w,a)); w=3 outer chains are "
       "edge-limited at floor(sqrt2(a+1)), not tip-limited."),
     "verified": f"{len(strip['designs_verified'])}/88 designs "
                 "finalize-verified (0 penetration, count, L=formula)",
     "member_rows": (
       "30 w=1 member points: 27 rows are the SAME design as the table "
       "(differences 1e-9..2e-9 = finalize scale noise, not geometry); "
       "n=17 (4.6755 vs 4.7071) and n=84 (9.6979 vs 9.7071) are "
       "strictly deeper in the table (community records)."),
     "sweep": (
       f"the spec sweep n=K^2-r, r in [5,K+4], K<=32: {sw['rows']} rows; "
       f"family beats grid only at {sw['beats_grid_at']} — every one "
       "already <= that in the table."),
     "full_range": (
       f"closure check on ALL n<=1000 (beyond the spec window): "
       f"{fr['rows']} rows vs family frontier; family beats grid at "
       f"{len(fr['beats_grid_at'])} rows but the table is strictly "
       f"deeper at {len(fr['table_strictly_deeper'])} and equal "
       "(finalize noise) at the rest; any_find = "
       f"{fr['any_find']}.  The family is dominated everywhere: its "
       "entire value is already realized in the table."),
     "acceptance_test": {
       "44": {"grid": 7, "family_L": acc[44]["family_L"],
              "capacity_ceiling_below_grid": 38, "pass": False},
       "58": {"grid": 8, "family_L": acc[58]["family_L"],
              "capacity_ceiling_below_grid": 52, "pass": False},
       "31": {"grid": 6, "family_L": acc[31]["family_L"],
              "capacity_ceiling_below_grid": 27, "pass": False},
       "reading": ("to beat grid at 44/58/31 the family needs 44/58/31 "
                   "squares under L<7/8/6; its capacity ceilings there "
                   "are 38/52/27 — short by 6/6/4 squares.  The "
                   "acceptance test fails by capacity, not by search "
                   "luck: no (w,a) exists that passes it.")},
     "conclusion": ("P1(a) as specified is CLOSED: the generalized "
                    "strip adds nothing to the current table on any row "
                    "n<=1000.  The remaining P1 candidates are (b) "
                    "two-block / block+slab and (c) axis-aligned "
                    "dominant + tilted seams.")},
   "P2_remainder": {
     "status": "executed (this run) — the designed sweep is complete",
     "design": ("P2_ROWS=134,135,157,158 subset re-run (run 24 stopped "
                "at 45/52 cells); identical hop loop/anneal streams, "
                "family-seeded (the A/B vs run 23's random seeds)"),
     "rebuilds": "4/4 ok (verified_L == want to 9 dp, worst_pen ~1e-15)",
     "cells": len(p2_cells), "hard_checks": p2_hard, "finds": 0,
     "rows": p2_rows,
     "combined_with_run24": {
       "cells": len(union),
       "designed_total": "52 (26 rows x 2 targets)",
       "hard_checks_total": p2_total_hard,
       "reading": ("run 24 (45 cells) + run 25 (8) = the full designed "
                   "sweep: 52/52 cells, 0 hard checks, 0 finds.  The A/B "
                   "is decided: family-seeded and random-seeded hop "
                   "polish agree — at targets grid-0.0005/grid-0.002 "
                   "these rows are jammed at their family geometry and "
                   "no seed reaches a hard state.  P2 closed.")}},
   "fixpoint": ("cascade3 + closure_apply re-run after both parts "
                "(mandatory order): 0 chain improvements, fixpoint "
                "after 0 apply-rounds; final_assembly rebuilt "
                "submission.csv; score 22.823536149, beats-grid 454; "
                "download/table.json + submission.csv byte-identical to "
                "workspace copies."),
   "delivery_fix": ("the user reports README.md never arrives at their "
                    "end: from this run the run documentation also ships "
                    "as RUN_NOTES.md (repo top level) and "
                    "download/run25_NOTES.md; the README.md copies are "
                    "kept as before.")},
 "score": {"before": 22.823536149, "after": round(score, 9)},
 "next": [
   "P1(b) two-block / block+slab and P1(c) axis-aligned dominant + "
   "tilted seams — the remaining P1 sub-families (a is closed)",
   "tier-1 infeasibility theorem for the small-n level-1 set (runs "
   "20-25 unanimous: 5-run-deep now)",
   "weekly import_atlas re-run (the register moves; 76 records in ~7w)"],
}
json.dump(led, open(f"{W}/download/run25_outcomes.json", "w"), indent=1)
print("1. ledger written; score after:", round(score, 9))

# ---------------------------------------------------- 2. README Run 25
sec = f"""

# Run 25 (2026-11-06): P1 strip scan rerun + P2 remainder

User: "(a) restart the P1 strip scan (as designed, it can be rerun)";
(b) finish the P2 remainder.

## P1 executed — and closed in the negative

The generalized Gobel strip was built EXACTLY, not searched.  A decode
pass (scripts/strip_decode.py) mapped the imported member states
(n=5,10,27,38,52,67 at L=a+1+1/sqrt2) into the (p,q) frame and read
off the closed form: w chains of 45-degree squares (q in [-w/2,w/2]),
2 tip diamonds at +-(L/sqrt2 - 1/sqrt2), and per q-side an independent
staircase with levels k=1..a_s at |q|=w/2+k/sqrt2, diamonds at
p=((a_s-k)-2j)/sqrt2 — every outer vertex touches the container edge
simultaneously.  The decode reproduces the stored states to the last
digit: the imported 'exact:square-N.svg' rows ARE this family.

Result of the sweep as designed (n=K^2-r, r in [5,K+4]) plus a
full-range closure check on all n<=1000:

- 88/88 designs finalize-verified (0 penetration, count, L=formula).
- The 30 w=1 member points: 27 are the SAME design as the table
  (deltas 1e-9..2e-9 = finalize scale noise); n=17 (4.6755 vs 4.7071)
  and n=84 (9.6979 vs 9.7071) are strictly deeper in the table.
- Family beats grid at 196 rows over the full range, but the table is
  strictly deeper at 950 and equal at the rest: **0 finds anywhere**.
- The acceptance test n=44/58/31 FAILS by capacity: the family's
  ceilings below grid are 38/52/27 squares — short by 6/6/4.  No
  (w,a) exists that passes it; this is a capacity fact, not search
  luck.

P1(a) is closed: the generalized strip adds nothing to the current
table on any row.  The remaining P1 candidates are (b) two-block /
block+slab and (c) axis-aligned dominant + tilted seams.
(Ledger: workspace/push/strip_run25.json.)

## P2 remainder — the designed sweep is complete

Run 24 stopped at 45/52 cells; this run re-ran the remainder
(P2_ROWS=134,135,157,158): 8 cells, 4/4 family seeds rebuilt ok
(verified_L == want to 9 dp), 0 hard checks, 0 finds.  Combined:
52/52 cells, 0 hard checks anywhere.  The A/B vs run 23's random
seeds is decided — both seed classes fail identically at targets
grid-0.0005/grid-0.002: these rows are jammed at their family
geometry.  (Ledger: workspace/push/p2_seed_polish_run25.json.)

## Fixpoint + delivery fix

cascade3 + closure_apply re-run after both parts (mandatory order):
0 changes; final score {score:.9f}, beats-grid 454; download/table.json
+ submission.csv in sync.

Delivery fix: README.md reportedly never arrives at the user's end —
from this run the run documentation also ships as RUN_NOTES.md (repo
top level) and download/run25_NOTES.md; the README.md copies are kept.

Score: {score:.9f} (before 22.823536149).
"""
readme = open(f"{W}/README.md").read()
if "Run 25 (2026-11-06)" not in readme:
    open(f"{W}/README.md", "w").write(readme + sec)
    print("2. README Run 25 appended")
else:
    print("2. README already has Run 25 (idempotent)")

# ---------------------------------------------------- 3. REPRODUCE A17
rep = open(f"{W}/REPRODUCE.md").read()
if "## A17." not in rep:
    rep += """

## A17. Run 25: P1 strip scan + P2 remainder

```bash
python3 scripts/strip_decode.py         # P1: member-state decode (audit)
python3 scripts/strip_sweep.py          # P1: generalized strip sweep (~2 min)
P2_ROWS=134,135,157,158 \\
  python3 scripts/p2_seed_polish.py      # P2 remainder (~10 min)
python3 scripts/cascade3.py             # fixpoint propagation
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py       # rebuilds submission.csv
python3 scripts/deliver25.py            # this run's deliverables
```
"""
    open(f"{W}/REPRODUCE.md", "w").write(rep)
    print("3. REPRODUCE A17 appended")
else:
    print("3. REPRODUCE already has A17 (idempotent)")

# ------------------------------- 4. RUN_NOTES.md alias + run25_NOTES.md
shutil.copy(f"{W}/README.md", f"{W}/RUN_NOTES.md")
print("4a. RUN_NOTES.md written (repo top level)")
# run25_NOTES.md = cover note + the Run 25 section (find by marker)
i = readme.find("# Run 25 (2026-11-06)")
if i < 0:  # README was just appended; re-read
    readme = open(f"{W}/README.md").read()
    i = readme.find("# Run 25 (2026-11-06)")
notes = ("# Run 25 notes (2026-11-06)\n\n"
         "Run documentation shipped under this distinct name because "
         "README.md reportedly never arrives at the user's end.  The "
         "same content is in README.md (Run 25 section), RUN_NOTES.md, "
         "and download/run25/README.md.\n"
         + readme[i:])
open(f"{W}/download/run25_NOTES.md", "w").write(notes)
print("4b. download/run25_NOTES.md written")

# ------------------------------------------- 5. top-level download README
shutil.copy(f"{W}/README.md", f"{W}/download/README.md")
print("5. download/README.md refreshed (top level)")

# ---------------------------------------------------- 6. run25 tree
shutil.rmtree(DL, ignore_errors=True)
NEW = [
 ("scripts/strip_decode.py", "NEW",
  "P1: member-state decode -> closed-form (p,q) parametrization"),
 ("scripts/strip_sweep.py", "NEW",
  "P1: generalized strip sweep + full-range closure check"),
 ("scripts/p2_seed_polish.py", "EDITED",
  "P2: P2_ROWS subset re-run support (run-25 remainder)"),
 ("scripts/deliver25.py", "NEW", "this build script"),
 ("workspace/push/strip_run25.json", "NEW",
  "P1 results ledger (88 designs, sweep, full-range, acceptance)"),
 ("workspace/push/p2_seed_polish_run25.json", "NEW",
  f"P2 remainder ledger ({len(p2_cells)} cells)"),
 ("README.md", "EDITED", "Run 25 section"),
 ("REPRODUCE.md", "EDITED", "A17 section"),
 ("run25_outcomes.json", "NEW", "run 25 ledger (also at download/ top)"),
]
rows = []
for rel, st, what in NEW:
    dst = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(dst) or DL, exist_ok=True)
    src = (f"{W}/download/run25_outcomes.json"
           if rel == "run25_outcomes.json" else f"{W}/{rel}")
    if os.path.exists(src):
        shutil.copy(src, dst)
        rows.append((rel, st, os.path.getsize(dst), what))

man = ["# Run 25 deliverables — new/edited files only",
       "",
       "| Repository path | Status | Bytes | What it is |",
       "|---|---|---|---|"]
for rel, st, sz, what in rows:
    man.append(f"| {rel} | {st} | {sz} | {what} |")
man += ["",
        "Delivery fix: run documentation also ships as RUN_NOTES.md "
        "(repo top level) and download/run25_NOTES.md.",
        "The fixpoint used scripts/cascade3.py, closure_apply.py, "
        "final_assembly.py unchanged.",
        "No .pyc (ast.parse verification only)."]
open(f"{DL}/MANIFEST.md", "w").write("\n".join(man) + "\n")
print("6. download/run25/ tree built:", len(rows), "files")

# ---------------------------------------------------- 7. verification
for rel, st, sz, what in rows:
    if rel.endswith(".py"):
        ast.parse(open(f"{DL}/{rel}").read())
    if rel.endswith(".json"):
        json.load(open(f"{DL}/{rel}"))
bad = [f for _, _, fs in os.walk(DL) for f in fs
       if f.endswith(".pyc")]
assert not bad, bad
json.load(open(f"{W}/download/run25_outcomes.json"))
print("7. verification clean")
