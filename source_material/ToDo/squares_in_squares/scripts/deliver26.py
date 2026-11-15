#!/usr/bin/env python3
"""deliver26.py — run 26 deliverables.

Run 26 = the user's standing instruction: see NEXT_STEPS.md (which
likely needs updating) for the next steps.  Executed:
  P1(b) two-block — closed by pointwise grid domination;
  P1(c) census + n=50 decode — closed as a family (blob regime);
  P3 source watch — paid: T-263 s(299) imported exactly, +0.003559
  with cascade chain (n=334, 371);
  P4 fixpoint — confirmed;
  NEXT_STEPS.md — rewritten to the Run-26 state (all closures
  recorded, P1 replaced by P1' blob-regime insertion).

Produces:
  1. download/run26_outcomes.json — the run ledger
  2. README.md Run 26 section
  3. REPRODUCE.md A18
  4. RUN_NOTES.md + download/run26_NOTES.md refresh
  5. download/README.md top-level refresh (standing pattern)
  6. download/run26/ tree + MANIFEST.md
  7. ast.parse verification, no .pyc
"""
import ast
import json
import math
import os
import shutil

W = "/home/z/my-project"
DL = f"{W}/download/run26"
TAB = f"{W}/workspace/submission/table.json"

tab = json.load(open(TAB))
score = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())

tb = json.load(open(f"{W}/workspace/push/twoblock_run26.json"))
sc = json.load(open(f"{W}/workspace/push/seam_census26.json"))
i299 = json.load(open(f"{W}/workspace/push/import_s299.json"))
acc = {a["n"]: a for a in tb["acceptance"]}

# ------------------------------------------------------------- 1. ledger
led = {
 "run": 26, "date": "2026-11-06",
 "user_request": ("continue the project - see NEXT_STEPS.md (which "
                   "likely needs updating) for the next steps"),
 "executed": {
   "P1b_two_block": {
     "status": "closed by domination",
     "family": ("45deg m x m corner block (lower-left face on x+y=D, "
                "integer D) + maximal integer-lattice axis fill; "
                "L=(D+(3/2)sqrt2*m)/2, n = m^2 + |cells|, all exact"),
     "measured": (f"{tb['designs']['enumerated']} designs enumerated "
                  f"(m<=24, D<=139, L<=34), {tb['designs']['verified_sample']} "
                  "finalize-verified sample (284): 0 penetration, count, "
                  "L=formula everywhere",
                  "pointwise domination vs plain grid capacity at the "
                  f"same L: 0 designs beat it (min gap 0 at the tie "
                  f"m={tb['domination']['at']['m']} D={tb['domination']['at']['D']})",
                  "acceptance n=44/58/31 FAILS by capacity: ceilings "
                  "36/49/25 below their grids - short by 8/9/6")},
   "P1c_census": {
     "status": "closed as a family (blob regime)",
     "measured": (
       f"census over all {sc['census']['sub_grid_rows']} sub-grid rows: "
       f"{sc['census']['by_class']['strip-45']} strip-45 (= P1(a), closed "
       f"run 25), {sc['census']['by_class']['pyth-exact']} Pythagorean-exact, "
       f"{sc['census']['by_class']['drift']} drifted",
       "n=50 decoded exactly: L=53/7 (dev 1.7e-9), angle arctan(3/4) "
       "(dev 1.6e-11 deg), tilted centers on the 1/50 lattice "
       "(maxdev 8.1e-8), axis grid at 2/7 mod 1 (offsets 1.3e-8), "
       "105 contacts at zero, packs grid-capacity+1 (49+1) at L=53/7: "
       "the K^2+1 architecture",
       "conclusion: the blob rows are isostatic hand-polished "
       "arrangements, not members of a low-dimensional parametric "
       "family; decode->closed-form->sweep does not transfer; follow-up "
       "named as P1' in NEXT_STEPS.md")},
   "P3_source_watch": {
     "status": "paid — the only score gain of runs 14-26",
     "import_atlas": "idempotent (applied 0, skipped 4, rejected 320)",
     "register_check": (
       "jlevy/squares #824 (Oct 25-31) + #893 (Nov 3-4): T-248 -> "
       "T-258 (Evan Daniel, fault-line DP seeded from Deotte's s(334)) "
       "-> T-263 (Doega Oezden rearrangement, -1.54e-8): "
       "s(299) <= 17.8012385339790622, superseding the catalogue's "
       "33/2 + sqrt(7)/2 = 17.822875655533"),
     "import": {
       "source": ("retained packet kenaznia-doga/s299-upper-bound, "
                  "n-299-candidate.yaml (packing.squares:Witness/v2, "
                  "exact rationals; registry VERIFIED 44,551 pairs + "
                  "independent checker VALID) -> fetched to "
                  "workspace/sources/s299_T263.yaml"),
       "verify": ("parsed exact rationals; packlib.verify: ok=True, "
                  "L=side exactly (|L-side|=0), worst_pen=0.0; "
                  "finalize: ok, L=17.801238535867 (the +2e-9 finalize "
                  "scale), count=299"),
       "applied": (f"{i299['old_L']:.12f} -> {i299['new_L']:.12f}, "
                   f"row gain {i299['row_gain']:.9f}")},
     "provenance_recorded": i299["provenance"]},
   "P4_fixpoint": {
     "status": "confirmed",
     "measured": ("cascade3: 2 chain improvements (n=334: "
                  "18.822875659 -> 18.801238538, n=371: 19.822875659 -> "
                  "19.801238538; both src=chain3); chain correctly stops "
                  "where gobel2 designs are deeper (410: 20.778 < 20.801; "
                  "453, 498) and the c=10 tail (810, 869, 930, 993) "
                  "stays at grid; closure_apply: fixpoint after 0 more "
                  "rounds; final_assembly: round-trip 0 issues"),
     "score": "22.823536149 -> 22.819977568 (-0.003558581)"},
   "NEXT_STEPS_update": {
     "status": "rewritten to the Run-26 state",
     "changes": ("new section 0 (execution status of runs 14-26, all "
                 "closures with numbers); gap recomputed (0.765556); "
                 "tie structure recomputed (546 rows, 9.02 headroom); "
                 "section 3 extended with failures 8-10; P1 replaced by "
                 "P1' (blob-regime insertion campaign, first targets the "
                 "at-grid c=10 tail 810/869/930/993); P2 marked done; "
                 "P3 upgraded to weekly-with-register-watch; value "
                 "ladder updated with the T-263 measured value"),
     "copies": ("upload/NEXT_STEPS.md (the upload is treated as input; "
                "the update is also at NEXT_STEPS.md top level and "
                "download/NEXT_STEPS.md")}},
 "score": {"before": 22.823536149, "after": round(score, 9),
           "delta": round(score - 22.823536149, 9)},
 "next": [
   "P1' blob-regime insertion campaign (NEXT_STEPS section 4): seed "
   "from record states, insert one square at fixed L, pressure-settle; "
   "first targets the at-grid c=10 tail (810, 869, 930, 993)",
   "P3 weekly watch (the only item that paid in runs 14-26); watch for "
   "T-numbers >= 263 and the Deotte fault-DP line (s(334) seeds)",
   "P5 certification backlog (Lean; T-263 Fraction replay)"],
}
json.dump(led, open(f"{W}/download/run26_outcomes.json", "w"), indent=1)
print("1. ledger written; score:", round(score, 9))

# ---------------------------------------------------- 2. README Run 26
sec = f"""

# Run 26 (2026-11-06): P1 closed; the source watch pays

User: continue - see NEXT_STEPS.md (which likely needs updating).

## P1(b) two-block — closed by domination

The exact version of the named design: a 45-degree m x m corner block
(lower-left face on the line x+y=D, D integer) plus the maximal
integer-lattice axis-aligned fill.  L = (D + (3/2)sqrt(2) m)/2 and
n = m^2 + |cells|, all exact integer/radical arithmetic.
{tb['designs']['enumerated']} designs enumerated (m<=24, D<=139, L<=34),
{tb['designs']['verified_sample']} finalize-verified: 0 penetration,
count, L=formula everywhere.  Result: the family never exceeds the
plain grid capacity floor(L)^2 at the same L (0 designs beat it; min
gap 0 at the single tie m=1, D=3, L=2.5607, n=4=gridcap).  The
acceptance test n=44/58/31 fails by capacity: ceilings 36/49/25 below
their grids - short by 8/9/6 squares.  P1(b) is closed.
(Ledger: workspace/push/twoblock_run26.json.)

## P1(c) tilted seams — closed as a family; the blob regime named

Census over all {sc['census']['sub_grid_rows']} sub-grid rows:
{sc['census']['by_class']['strip-45']} are strip-45 (P1(a), closed run 25),
{sc['census']['by_class']['pyth-exact']} are Pythagorean-exact,
{sc['census']['by_class']['drift']} are drifted.  The cleanest record,
n=50, decodes exactly: L=53/7 (dev 1.7e-9), angle arctan(3/4) (dev
1.6e-11 deg), tilted centers on the 1/50 lattice (maxdev 8.1e-8),
axis grid at 2/7 mod 1 (offsets 1.3e-8), 105 contacts at zero - it
packs grid-capacity+1 (49+1 squares) into L=53/7.  These are
isostatic hand-polished arrangements on rational lattices, not
members of a parametric family: the decode->closed-form->sweep method
does not transfer.  P1(c) is closed as a family; the follow-up (P1'
in NEXT_STEPS.md) is a blob-regime insertion campaign seeded from the
records themselves.  (Ledger: workspace/push/seam_census26.json.)

## P3 source watch — T-263 s(299) imported; the only score gain of runs 14-26

The weekly register check found jlevy/squares #824/#893: s(299) <=
17.8012385339790622 (T-263; finder Evan Daniel via fault-line DP
seeded from Deotte's s(334), improved by Doega Oezden by 1.54e-8),
superseding the catalogue's 33/2 + sqrt(7)/2.  The retained packet
(kenaznia-doga/s299-upper-bound) carries the certificate as exact
rationals; fetched, parsed, and verified: packlib.verify ok=True with
L = side EXACTLY and worst_pen = 0.0.  Applied: 17.822875657 ->
17.801238536 (row gain {i299['row_gain']:.9f}), provenance recorded in
the row src.  (Ledger: workspace/push/import_s299.json.)

## P4 fixpoint — the chain propagates T-263

cascade3 converted n=334 (18.822875659 -> 18.801238538) and n=371
(19.822875659 -> 19.801238538) by the chain law; it correctly stops
where the gobel2 designs are already deeper (410: 20.778 < 20.801;
453; 498).  closure_apply: fixpoint after 0 more rounds;
final_assembly: round-trip 0 issues.  Score 22.823536149 ->
{score:.9f} (-{abs(score-22.823536149):.9f}); beats-grid 454 (334 and
371 are the new sub-grid members); submission.csv rebuilt and all
1000 rows re-verified independently from the CSV.

## NEXT_STEPS.md rewritten

Now current with runs 14-26: new section 0 (execution status, every
closure with its numbers), the gap recomputed (0.765556), P1 replaced
by P1' (blob-regime insertion, first targets the at-grid c=10 tail
810/869/930/993), P2 marked done, P3 upgraded to weekly register
watch, value ladder updated with the measured T-263 return.  Copies:
NEXT_STEPS.md (top level) and download/NEXT_STEPS.md.
"""
readme = open(f"{W}/README.md").read()
if "Run 26 (2026-11-06)" not in readme:
    open(f"{W}/README.md", "w").write(readme + sec)
    print("2. README Run 26 appended")
else:
    print("2. README already has Run 26 (idempotent)")

# ---------------------------------------------------- 3. REPRODUCE A18
rep = open(f"{W}/REPRODUCE.md").read()
if "## A18." not in rep:
    rep += """

## A18. Run 26: P1(b)/(c) closures + T-263 import

```bash
python3 scripts/twoblock_sweep.py       # P1(b): two-block sweep (~2 min)
python3 scripts/seam_census.py          # P1(c): census + n=50 decode
python3 scripts/import_atlas.py         # P3: idempotent (may fetch)
python3 scripts/import_s299.py          # P3: T-263 s(299) (needs network)
python3 scripts/cascade3.py             # P4: fixpoint propagation
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py       # rebuilds submission.csv
python3 scripts/deliver26.py            # this run's deliverables
```
"""
    open(f"{W}/REPRODUCE.md", "w").write(rep)
    print("3. REPRODUCE A18 appended")
else:
    print("3. REPRODUCE already has A18 (idempotent)")

# ------------------------------- 4. RUN_NOTES.md alias + run26_NOTES.md
shutil.copy(f"{W}/README.md", f"{W}/RUN_NOTES.md")
print("4a. RUN_NOTES.md refreshed")
readme = open(f"{W}/README.md").read()
i = readme.find("# Run 26 (2026-11-06)")
notes = ("# Run 26 notes (2026-11-06)\n\n"
         "Run documentation under the distinct name (README.md "
         "reportedly never arrives at the user's end).  The same "
         "content is in README.md (Run 26 section), RUN_NOTES.md, and "
         "download/run26/README.md.\n"
         + readme[i:])
open(f"{W}/download/run26_NOTES.md", "w").write(notes)
print("4b. download/run26_NOTES.md written")

# ------------------------------------------- 5. top-level download README
shutil.copy(f"{W}/README.md", f"{W}/download/README.md")
print("5. download/README.md refreshed")

# ---------------------------------------------------- 6. run26 tree
shutil.rmtree(DL, ignore_errors=True)
NEW = [
 ("scripts/twoblock_sweep.py", "NEW",
  "P1(b): exact two-block family, sweep + domination check"),
 ("scripts/seam_census.py", "NEW",
  "P1(c): census of sub-grid rows + exact n=50 decode"),
 ("scripts/import_s299.py", "NEW",
  "P3: T-263 s(299) import (exact-rational verify)"),
 ("scripts/deliver26.py", "NEW", "this build script"),
 ("workspace/sources/s299_T263.yaml", "NEW",
  "T-263 certificate as fetched (exact rationals)"),
 ("workspace/push/twoblock_run26.json", "NEW", "P1(b) ledger"),
 ("workspace/push/seam_census26.json", "NEW", "P1(c) ledger"),
 ("workspace/push/import_s299.json", "NEW", "P3 import ledger"),
 ("README.md", "EDITED", "Run 26 section"),
 ("REPRODUCE.md", "EDITED", "A18 section"),
 ("NEXT_STEPS.md", "EDITED",
  "rewritten to Run-26 state (P1 closed; P1' named)"),
 ("run26_outcomes.json", "NEW", "run 26 ledger (also at download/ top)"),
]
rows = []
for rel, st, what in NEW:
    dst = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(dst) or DL, exist_ok=True)
    src = (f"{W}/download/run26_outcomes.json"
           if rel == "run26_outcomes.json" else f"{W}/{rel}")
    if os.path.exists(src):
        shutil.copy(src, dst)
        rows.append((rel, st, os.path.getsize(dst), what))

man = ["# Run 26 deliverables — new/edited files only",
       "",
       "| Repository path | Status | Bytes | What it is |",
       "|---|---|---|---|"]
for rel, st, sz, what in rows:
    man.append(f"| {rel} | {st} | {sz} | {what} |")
man += ["",
        "The fixpoint used scripts/cascade3.py, closure_apply.py, "
        "final_assembly.py unchanged.",
        "download copies of table.json/submission.csv/NEXT_STEPS.md "
        "refreshed in sync.",
        "No .pyc (ast.parse verification only)."]
open(f"{DL}/MANIFEST.md", "w").write("\n".join(man) + "\n")
print("6. download/run26/ tree built:", len(rows), "files")

# ---------------------------------------------------- 7. verification
for rel, st, sz, what in rows:
    if rel.endswith(".py"):
        ast.parse(open(f"{DL}/{rel}").read())
    if rel.endswith(".json"):
        json.load(open(f"{DL}/{rel}"))
bad = [f for _, _, fs in os.walk(DL) for f in fs if f.endswith(".pyc")]
assert not bad, bad
print("7. verification clean")
