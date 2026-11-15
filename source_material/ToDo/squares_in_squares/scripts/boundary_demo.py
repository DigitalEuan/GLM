#!/usr/bin/env python3
r"""boundary_demo.py — run 21, Q1: does the engine have an
'E ~ 0.01-0.05' floor, or does the floor track the boundary?

The run-20 probe showed: at targets 0.05-0.1 below the grid the
settle stalls at f ~ 4e-3..2e-1 (the band the user is asking about);
at g-0.002 it converges to f ~ 1e-6.  Hypothesis: the stall is not a
machinery floor — it is the correct report of infeasibility, and its
depth scales with the distance to the TRUE boundary.  Prediction this
demo tests: as the target crosses the boundary from above, the same
engine, same seeds, same gate goes

    feasible side (target > optimum): verified finds (f -> ~1e-13)
    infeasible side (target < optimum): 0 finds, f ~ (deficit)^2-ish

If the transition happens at ~g (+-1e-4), the engine's floor is AT
the boundary and there is nothing to 'design around' below it.
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
from oracle_basin import ramp_settle
from cent_discovery import rsa_seed
from engine_variants import finalize_gate

OUT = os.path.join(ROOT, "workspace/push/boundary_demo.json")

# targets relative to the grid g: crossing the boundary from above
OFFSETS = (0.02, 0.005, 0.002, 0.001, 0.0005, -0.001, -0.002)
SEEDS = 4


def main():
    res = {"cells": {}, "finds": []}
    t0 = time.time()
    for n in (12, 20):
        g = math.ceil(math.sqrt(n))
        for off in OFFSETS:
            L_t = round(g + off, 7)
            cell = {"target": L_t, "offset": off, "attempts": 0,
                    "finds": 0, "best_f": None, "verified_L": []}
            for s in range(1, SEEDS + 1):
                rng = np.random.RandomState(7919 * n + s * 17 + int(off * 1e5))
                q0 = rsa_seed(n, L_t + 0.45, rng)
                q, f = ramp_settle(q0, L_t, steps=14)
                hit = finalize_gate(q, L_t)
                cell["attempts"] += 1
                cell["best_f"] = f if cell["best_f"] is None \
                    else min(cell["best_f"], f)
                if hit:
                    cell["finds"] += 1
                    cell["verified_L"].append(hit["verified_L"])
                    res["finds"].append({"n": n, "target": L_t,
                                         "L": hit["verified_L"]})
                res["cells"][f"n{n}_off{off:+g}"] = cell
                json.dump(res, open(OUT, "w"), indent=1)
            print(f"n={n} target {L_t} (g{off:+g}): {cell['finds']}/"
                  f"{cell['attempts']} verified | best_f {cell['best_f']:.2e}"
                  + (f" | best verified L "
                     f"{min(cell['verified_L']):.9f}" if cell["finds"] else "")
                  + f" | {time.time()-t0:.0f}s", flush=True)
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"done {res['seconds']}s")


if __name__ == "__main__":
    main()
