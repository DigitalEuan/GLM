#!/usr/bin/env python3
r"""boundary_scan.py — the decisive follow-up to root_probe.

The probe showed settles at g-0.002 end within 1e-6..1e-5 of feasible.
Hypothesis: the roots' true optimum lies JUST below the grid (within
~1e-3), and the campaign's levels (g-0.1/0.05/0.002) were either too
deep (infeasible) or structurally far.  This scan maps the feasibility
boundary finely:

  for each root, levels delta in a fine log-ish grid (0.0001 .. 0.005),
  N seeds each, gate = packlib.finalize (the campaign's authority);
  a find is a VERIFIED feasible packing with L < grid - 1e-9 (a genuine
  table improvement), recorded with its state.

Outcome interpretations (reported honestly):
  finds at some delta  -> optimum < grid; apply to the table;
  zero finds at all deltas (with finalize absorbing ~1e-5) -> the
  optimum is within ~1e-5 of the grid: a (near-)impossibility result
  for the roots — the honest answer to "why 0 finds".
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from cent_discovery import attempt

OUT = os.path.join(ROOT, "workspace/push/boundary_scan.json")

# smallest roots first (fast, most tractable); extend on success
SCAN = {12: [0.005, 0.002, 0.001, 0.0005, 0.0002, 0.0001],
        20: [0.002, 0.001, 0.0005, 0.0002],
        21: [0.002, 0.001, 0.0005, 0.0002],
        30: [0.002, 0.001, 0.0005, 0.0002],
        31: [0.002, 0.001, 0.0005],
        32: [0.002, 0.001, 0.0005]}
SEEDS = 10


def main():
    res = {"finds": [], "levels": {}}
    t0 = time.time()
    for n, deltas in SCAN.items():
        g = math.ceil(math.sqrt(n))
        for d in deltas:
            L_t = round(g - d, 7)
            t1 = time.time()
            lvl = {"target": L_t, "attempts": 0, "finds": []}
            for s in range(1, SEEDS + 1):
                f = attempt(n, L_t, 7919 * n + s + int(d * 1e5),
                            ramp=14)
                lvl["attempts"] += 1
                if f:
                    lvl["finds"].append({"seed": f["seed"],
                                         "L": f["verified_L"],
                                         "state": f["state"]})
                    res["finds"].append({"n": n, "L": f["verified_L"],
                                         "seed": f["seed"],
                                         "state": f["state"]})
            res["levels"][f"n{n}_d{d}"] = lvl
            print(f"n={n} g-{d} (L_t={L_t}): {len(lvl['finds'])}/"
                  f"{lvl['attempts']}"
                  + (f" BEST {min(x['L'] for x in lvl['finds']):.9f}"
                     if lvl["finds"] else "")
                  + f" | {time.time()-t1:.0f}s", flush=True)
            json.dump(res, open(OUT, "w"), indent=1)
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"done {res['seconds']}s | total verified finds: {len(res['finds'])}")


if __name__ == "__main__":
    main()
