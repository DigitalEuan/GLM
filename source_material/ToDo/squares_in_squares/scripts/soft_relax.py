#!/usr/bin/env python3
r"""soft_relax.py — run 22: soft-relaxation hop search (v2 hybrid).

USER REQUEST (run 22): "soft relaxation may be worth a try also."

Why: both engines are soft during search (squared overlaps + squared
container violation).  What was missing is (a) reheating cycles that
let squares pass THROUGH each other into a different arrangement
class — hard dynamics cannot cross arrangement classes — and (b)
exact bookkeeping of an arrangement's own requirement.  v1 (SA-only,
20k moves/hop) was uniformly underpowered: 0/16 hard hops on all 8
cells INCLUDING the controls where packings exist — kept as
soft_relax_v1_sa.json.  v2 is the hybrid:

  hop = SA hot shuffle at fixed L_t (t0 0.30/0.45, overlaps allowed —
        the pass-through homotopy) followed by settle_to (L-BFGS-B,
        ftol 1e-14) — gradient re-hardening.

  Score: a hop counts as HARD when the polished state is pairwise
  non-overlapping (P.verify worst_pen <= -1e-10); its value is the
  state's OWN extent L (P.verify's L = max(w,h)), which may exceed
  L_t — that is the honest requirement of the arrangement.  A find =
  finalize-verified L < grid-1e-9.

Matrix (8 cells, 4 seeds x 8 hops each):
  controls (below-grid optima EXIST -> method validation):
    n=5  (grid 3, known 2.7071) at known+0.001 and known+0.05
    n=11 (grid 4, known 3.8771) at known+0.001 and known+0.05
  roots (the remaining puzzle; expected infeasible below grid):
    n=12 (grid 4) and n=20 (grid 5) at g-0.002 and g-0.02
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
from sa_push import anneal
from cent_discovery import rsa_seed
from engine_variants import finalize_gate
from oracle_basin import settle_to
import packlib as P

OUT = "/home/z/my-project/workspace/push/soft_relax.json"

SEEDS = 4
HOPS = 8
MOVES = 20000
PHI = math.pi / 2


def unpack(q):
    n = q.size // 3
    return q[:n].copy(), q[n:2 * n].copy(), q[2 * n:] % PHI


def hop_search(n, L_t, seed):
    """One seed: gradient cold-settle, then alternating SA hot shuffles
    (soft space, overlaps allowed — basin escape by pass-through) and
    gradient re-hardening polishes (settle_to, L-BFGS-B, ftol 1e-14).
    A hop is HARD when the polished state is pairwise non-overlapping
    (P.verify worst_pen <= -1e-10); its score is the state's own
    extent (P.verify L), which may exceed L_t.
    Returns (best (L_hard, q) or None, hard_hops, states_checked)."""
    rng = np.random.RandomState(seed)
    q = rsa_seed(n, L_t + 0.45, rng)
    best = None
    hard_hops = 0
    checked = 0
    for h in range(HOPS):
        if h == 0:
            q, f = settle_to(q, L_t, iters=250)          # cold settle
        elif h % 2 == 1:                                 # hot shuffle
            X, Y, TH = unpack(q)
            anneal(X, Y, TH, L_t, MOVES, seed * 1009 + h,
                   t0=0.30 if (h // 2) % 2 == 0 else 0.45,
                   tend=0.02, rotate_frac=0.5)
            q = np.concatenate([X, Y, TH])
            continue
        else:
            q, f = settle_to(q, L_t, iters=250)          # re-harden
        checked += 1
        THn = q[2 * n:] % PHI
        st = [(float(q[i]), float(q[n + i]), float(THn[i]))
              for i in range(n)]
        r = P.verify(st, tol=1e-9)
        if r["worst_pen"] <= -1e-10:                     # pairwise hard
            hard_hops += 1
            if best is None or r["L"] < best[0]:
                best = (float(r["L"]), q.copy())
    return best, hard_hops, checked


def run_cell(n, grid, label, L_t, seeds, t0=time.time()):
    cell = {"label": label, "n": n, "grid": grid, "target": L_t,
            "attempts": 0, "hard_hops": 0, "best_hard_L": None,
            "verified": None}
    best_state = None
    for s in range(1, seeds + 1):
        seed = 7919 * n + 104729 * s + int(round((L_t % 1) * 1e6))
        best, hh, ck = hop_search(n, L_t, seed)
        cell["attempts"] += 1
        cell["hard_hops"] += hh
        if best and (cell["best_hard_L"] is None
                     or best[0] < cell["best_hard_L"]):
            cell["best_hard_L"] = round(best[0], 12)
            best_state = best[1]
    if best_state is not None:
        hit = finalize_gate(best_state, cell["best_hard_L"] + 1e-6)
        if hit:
            cell["verified"] = hit["verified_L"]
    return cell


def main():
    res = {"cells": [], "finds": [], "started": time.strftime("%H:%M:%S")}
    t0 = time.time()
    matrix = [
        # controls: below-grid optima exist (method validation)
        (5, 3, "control n=5 tight", 2.707106781 + 0.001),
        (5, 3, "control n=5 loose", 2.707106781 + 0.05),
        (11, 4, "control n=11 tight", 3.877083590 + 0.001),
        (11, 4, "control n=11 loose", 3.877083590 + 0.05),
        # roots: the remaining puzzle (below grid expected infeasible)
        (12, 4, "root n=12 near", 4 - 0.002),
        (12, 4, "root n=12 far", 4 - 0.02),
        (20, 5, "root n=20 near", 5 - 0.002),
        (20, 5, "root n=20 far", 5 - 0.02),
    ]
    for n, grid, label, L_t in matrix:
        cell = run_cell(n, grid, label, L_t, SEEDS)
        res["cells"].append(cell)
        if cell["verified"] and cell["verified"] < grid - 1e-9:
            res["finds"].append({"n": n, "grid": grid,
                                 "verified_L": cell["verified"],
                                 "target": L_t})
        verdict = ("VERIFIED %.9f" % cell["verified"]
                   if cell["verified"] else
                   ("hard %.9f (not below grid)" % cell["best_hard_L"]
                    if cell["best_hard_L"] else "no hard state"))
        print(f"{label:22s} n={n:2d} target {L_t:.6f}: "
              f"hard_hops {cell['hard_hops']}/{cell['attempts']*4} | {verdict}"
              f" | {time.time()-t0:.0f}s", flush=True)
        json.dump(res, open(OUT, "w"), indent=1)
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(OUT, "w"), indent=1)
    print("finds:", res["finds"] or "none")
    print(f"done {res['seconds']}s")


if __name__ == "__main__":
    main()
