#!/usr/bin/env python3
r"""template_sweep.py — run 20: structured template coverage for the roots.

The scans so far sample SEEDS randomly; this sweeps STRUCTURES
exhaustively-ish: the k x (k+1)-style grid with a chosen subset of
squares pre-tilted by theta from a crystallographic + small-angle set
(the "mostly aligned, a few tilted" hypothesis for near-grid optima).

For each template (subset, angle):
  seed = centered grid layout, chosen squares at +theta (others at 0),
  positions jittered; ramp-settle at L_target = g - d; gate.

This covers the structured near-grid space far more systematically
than random restarts; with 0 finds across all templates, the
near-optimality evidence for the roots becomes strong.
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
from engine_variants import finalize_gate

OUT = os.path.join(ROOT, "workspace/push/template_sweep.json")


def grid_layout(n, L0):
    """Closest-to-square integer grid layout centered in L0."""
    best = None
    for a in range(1, n + 1):
        b = math.ceil(n / a)
        if a * b >= n and (best is None or max(a, b) < max(best)):
            best = (a, b)
    rows, cols = best
    cell = min(1.0, L0 / max(rows, cols))
    ox = (L0 - cols * cell) / 2
    oy = (L0 - rows * cell) / 2
    pts = []
    k = 0
    for r in range(rows):
        for c in range(cols):
            if k >= n:
                break
            pts.append((ox + (c + 0.5) * cell, oy + (r + 0.5) * cell))
            k += 1
    return pts


def template_seed(n, L0, tilt_idx, theta_rad, rng, jitter=0.02):
    pts = grid_layout(n, L0)
    q = []
    for i, (x, y) in enumerate(pts):
        th = theta_rad if i in tilt_idx else 0.0
        q += [x + rng.uniform(-jitter, jitter),
              y + rng.uniform(-jitter, jitter),
              th + rng.uniform(-jitter, jitter)]
    return np.array(q, dtype=float)


def main():
    res = {"finds": [], "cells": {}}
    t0 = time.time()
    n = 12
    g = 4
    # singles over all 12 squares + the 10 corner/edge pairs
    subsets = [(i,) for i in range(12)]
    subsets += [(i, j) for i in range(0, 12, 3)
                for j in range(1, 12, 3) if j > i]
    angles_deg = (8.21, 26.565, 45.0)
    deltas = (0.001, 0.0002)
    for d in deltas:
        L_t = round(g - d, 7)
        cell = {"target": L_t, "attempts": 0, "finds": [],
                "best_f": None, "templates": 0}
        res["cells"][f"n{n}_d{d}"] = cell
        for sub in subsets:
            for adeg in angles_deg:
                th = math.radians(adeg)
                for s in range(2):
                    rng = np.random.RandomState(
                        7919 * n + s + int(d * 1e5) + int(adeg * 100))
                    q0 = template_seed(n, L_t + 0.45, set(sub), th, rng)
                    q, f = ramp_settle(q0, L_t, steps=14)
                    cell["attempts"] += 1
                    cell["best_f"] = f if cell["best_f"] is None \
                        else min(cell["best_f"], f)
                    hit = finalize_gate(q, L_t)
                    if hit:
                        cell["finds"].append(
                            {"subset": sub, "angle": adeg, "seed": s,
                             "L": hit["verified_L"], "state": hit["state"]})
                        res["finds"].append(
                            {"n": n, "L": hit["verified_L"], "subset": sub,
                             "angle": adeg, "seed": s, "state": hit["state"]})
                cell["templates"] += 1
                # fine checkpoint: survives a stop at any moment
                json.dump(res, open(OUT, "w"), indent=1)
            print(f"n=12 g-{d} subset {sub} angle {adeg}: "
                  f"running {cell['attempts']} attempts, best_f "
                  f"{cell['best_f']:.2e}, {len(cell['finds'])} finds "
                  f"| {time.time()-t0:.0f}s", flush=True)
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"done {res['seconds']}s | finds: {len(res['finds'])}")


if __name__ == "__main__":
    main()
