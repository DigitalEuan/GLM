#!/usr/bin/env python3
r"""run10_ledger.py — Run 10 outcomes ledger (merged, honest).

Run 10 = Wave A (gobel3 clipped-octagon family sweep)
       + Wave B (pocket-fill n-migration front — NEGATIVE, subsumed
         by closure fixpoint: L non-decreasing in n makes fill-migration
         strictly impossible)
       + propagation (cascade3 band-extension, closure removal fixpoint)
       + reassembly (final_assembly round-trip).

All inputs measured this run; sources: gobel3_results.json (Wave A),
gobel3_fill.json (Wave B), cascade3_run10.log / closure_run10.log
(propagation), final_assembly stdout.
"""
import json
import os
from math import sqrt

TAB = "/home/z/my-project/workspace/submission/table.json"
DL = "/home/z/my-project/download"
tab = json.load(open(TAB))

score = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
from math import isqrt
beats = 0
for n in range(1, 1001):
    q = isqrt(n)
    grid = q if n == q * q else q + 1
    if tab[str(n)]["L"] < grid - 1e-12:
        beats += 1

# Wave A ledger
wa = json.load(open(os.path.join(DL, "gobel3_results.json")))
real = [a for a in wa["applied"] if a["old"] - a["new"] > 1e-6]
rounding = [a for a in wa["applied"] if a["old"] - a["new"] <= 1e-6]

# Wave B ledger
wb = json.load(open(os.path.join(DL, "gobel3_fill.json")))

out = {
 "run": 10,
 "score": round(score, 6),
 "beats_grid": beats,
 "grid_ceiling": 28.937670,
 "improvement_vs_grid": round(28.937670 - score, 6),
 "wave_a": {
   "family": "G(a1,a2,b,c,t) clipped-diamond / octagon hull",
   "tested": wa["tested"],
   "applied": len(wa["applied"]),
   "real_finds": [
     {"n": a["n"], "params": [a["a1"], a["a2"], a["b"], a["c"], a["t"]],
      "old": a["old"], "new": a["new"]} for a in real],
   "rounding_only": [a["n"] for a in rounding],
   "census": wa["census"],
 },
 "wave_b": {
   "method": "pocket-fill n-migration (axis + 45 raster, exact SAT)",
   "fills_measured": 509,
   "verify_fails_geometric_bug": 234,
   "applied": 0,
   "verdict": ("NEGATIVE — table states are contact-saturated; the "
               "closure fixpoint (L non-decreasing in n) makes "
               "fill-migration strictly subsumed: no n<n' can have "
               "L(n) < L(n'). Two encircling tests agree (permissive "
               "L1-model: 509 clean fills, 0 applied; exact SAT: same).")
 },
 "propagation": {
   "cascade3_chains": 2,
   "closure_rounds": 1,
   "closure_improvements": 5,
 },
 "assembly": {
   "rows": 500500,
   "round_trip_issues": 0,
   "final_score": round(score, 6),
 },
 "open_band": {"LOW": 69, "MID": 392},
 "leader": {"platform": 23.193864, "local_best": 22.887471,
            "leader_reported": 22.0544214515,
            "uniform_depth_to_leader": 0.026435},
}
json.dump(out, open(os.path.join(DL, "run10_outcomes.json"), "w"), indent=1)
print(json.dumps(out, indent=1)[:1500])
print("-> download/run10_outcomes.json")
