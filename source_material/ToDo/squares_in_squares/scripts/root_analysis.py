#!/usr/bin/env python3
"""root_analysis.py — run 20 quantitative synthesis.

Answers, with computed numbers (no head arithmetic):
  1. Score impact of the 23 roots: what would the score gain be if
     each root improved by d (for d in 0.002/0.001/0.005)?
  2. The stall law: collect best_f per (n, delta, prior) from the
     scan ledgers; convert to implied penetration; compare with the
     deficit (g - L_t) — the ratio ~O(1) across deltas supports
     "optimum at grid".
  3. Coverage report: which (root, delta, prior) cells completed.
"""
import json
import math
import os

ROOT = "/home/z/my-project"
PUSH = os.path.join(ROOT, "workspace/push")
tab = json.load(open(os.path.join(ROOT, "workspace/submission/table.json")))
ROOTS = [12, 20, 21, 30, 31, 32, 42, 43, 44, 45, 56, 57, 58, 59, 60,
         73, 74, 75, 76, 77, 133, 157, 158]

# 1. score impact
cur = sum(tab[str(n)]["L"] / math.sqrt(n) - 1 for n in range(1, 1001))
print(f"current score: {cur:.6f}")
for d in (0.005, 0.002, 0.001):
    gain = sum(d / math.sqrt(n) for n in ROOTS)
    print(f"  if every root improved by {d}: score {cur-gain:.6f} "
          f"(gain {gain:.6f}, {gain/cur*100:.3f}%)")
# also: best case if roots went to the theoretical area bound sqrt(n)
area_gain = sum((math.sqrt(n) - tab[str(n)]["L"]) / math.sqrt(n)
                for n in ROOTS)
print(f"  area-lower-bound headroom on the roots: {area_gain:.4f} "
      f"(score {cur-area_gain:.6f}) — an ABSOLUTE ceiling, "
      "not achievable")

# 2. stall law from ledgers
print("\nstall law (penetration = sqrt(best_f); deficit = g - L_t):")
rows = []
bscan = json.load(open(os.path.join(PUSH, "boundary_scan.json")))
lscan = json.load(open(os.path.join(PUSH, "lattice_scan.json")))
# fine_probe log-recorded values (script timed out on CPU contention;
# printed results preserved here with provenance)
fine_probe = {"L@3.999": 4.50e-07, "L@3.9995": 1.95e-07}
for key, cell in sorted(bscan["levels"].items()):
    n = int(key.split("_")[0][1:])
    g = math.ceil(math.sqrt(n))
    rows.append((n, "RSA", cell["target"], None))
for key, cell in sorted(lscan["cells"].items()):
    parts = key.split("_")
    n = int(parts[0][1:])
    eng = parts[2]
    d = float(parts[1][1:])
    g = math.ceil(math.sqrt(n))
    if cell["best_f"] is not None:
        pen = math.sqrt(cell["best_f"])
        rows.append((n, f"lat-{eng}", cell["target"], pen / (g - cell["target"])))
for k, f in fine_probe.items():
    L_t = float(k.split("@")[1])
    rows.append((12, "lat-fine", L_t, math.sqrt(f) / (4.0 - L_t)))
ratios = [r[3] for r in rows if r[3] is not None]
for n, prior, L_t, ratio in rows:
    print(f"  n={n:3d} {prior:8s} @ {L_t:.6f}: "
          + (f"pen/deficit = {ratio:.3f}" if ratio else "0 finds (gate)"))
if ratios:
    import statistics
    print(f"  ratio stats: n={len(ratios)} min={min(ratios):.3f} "
          f"median={statistics.median(ratios):.3f} max={max(ratios):.3f}")

# 3. coverage
done_l = sum(1 for c in lscan["cells"].values())
print(f"\ncoverage: boundary_scan levels done: {len(bscan['levels'])}; "
      f"lattice cells done: {done_l} (finds {len(lscan['finds'])}); "
      f"bscan finds {len(bscan['finds'])}")
json.dump({"score": cur,
           "root_gain_0.002": sum(0.002 / math.sqrt(n) for n in ROOTS),
           "area_headroom_roots": area_gain,
           "stall_ratios": [round(r, 3) for r in ratios if r]},
          open(os.path.join(PUSH, "root_analysis.json"), "w"), indent=1)
print("saved workspace/push/root_analysis.json")
