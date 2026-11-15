#!/usr/bin/env python3
r"""lattice_scan.py — run 20: the untested combination for the roots.

Evidence so far:
  - root_probe: settles at g-0.002 end ~1e-6 objective (≈1.7e-3
    penetration) — NEAR-MISS, not far-miss;
  - boundary_scan (RSA prior): 0 finds down to g-0.0002 — the diverse-
    angle prior is the wrong shape for near-grid optima;
  - engine selftests: lattice prior hits the GRID control 8/15.

So: lattice seeds (the near-grid structural prior) × fine deltas
(g-0.0002 .. g-0.002) × settle ramp, half the runs followed by the
transducer sweep (stress->strain relaxation, proposal_11/W20) + polish.

A find = packlib.finalize VERIFIED with L < grid - 1e-9 (a genuine
table improvement).  Honest ledger regardless of outcome; if 0 across
the board, that is (within this engine family's reach) evidence the
roots' grid values are optimal — a near-impossibility result.
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
from pressure_settle import obj_grad
from oracle_basin import ramp_settle, settle_to
from engine_variants import lattice_seed, transduce, finalize_gate

OUT = os.path.join(ROOT, "workspace/push/lattice_scan.json")

SCAN = {12: [0.002, 0.001, 0.0005, 0.0002],
        20: [0.002, 0.001, 0.0005, 0.0002],
        21: [0.002, 0.001, 0.0005, 0.0002],
        30: [0.002, 0.001, 0.0005],
        31: [0.002, 0.001, 0.0005],
        32: [0.002, 0.001, 0.0005]}
SEEDS = 10
ENGINES = ("L", "LT")


def one(n, L_t, seed, engine):
    rng = np.random.RandomState(seed)
    q0 = lattice_seed(n, L_t + 0.45, rng)
    q, f = ramp_settle(q0, L_t, steps=14)
    if engine == "LT" and 0 < f < 5e-2:
        q = transduce(q, L_t)
        q, f = settle_to(q, L_t, iters=400)
    return finalize_gate(q, L_t), f


def main():
    res = {"finds": [], "cells": {}}
    t0 = time.time()
    for n, deltas in SCAN.items():
        g = math.ceil(math.sqrt(n))
        for d in deltas:
            for eng in ENGINES:
                L_t = round(g - d, 7)
                cell = {"target": L_t, "engine": eng, "attempts": 0,
                        "finds": [], "best_f": None}
                for s in range(1, SEEDS + 1):
                    hit, f = one(n, L_t, 7919 * n + s + int(d * 1e5), eng)
                    cell["attempts"] += 1
                    cell["best_f"] = f if cell["best_f"] is None \
                        else min(cell["best_f"], f)
                    if hit:
                        cell["finds"].append({"seed": s, "L": hit["verified_L"],
                                              "state": hit["state"]})
                        res["finds"].append({"n": n, "L": hit["verified_L"],
                                             "engine": eng, "seed": s,
                                             "state": hit["state"]})
                res["cells"][f"n{n}_d{d}_{eng}"] = cell
                print(f"n={n} g-{d} {eng}: {len(cell['finds'])}/"
                      f"{cell['attempts']}"
                      f" best_f {cell['best_f']:.2e}"
                      + (f" BEST L {min(x['L'] for x in cell['finds']):.9f}"
                         if cell["finds"] else "")
                      + f" | {time.time()-t0:.0f}s", flush=True)
                json.dump(res, open(OUT, "w"), indent=1)
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"done {res['seconds']}s | finds: {len(res['finds'])}")


if __name__ == "__main__":
    main()
