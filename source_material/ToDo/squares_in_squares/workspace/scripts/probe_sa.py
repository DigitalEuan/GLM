#!/usr/bin/env python3
"""Parameter probe for the SA push engine.

Runs a grid of schedule/proposal configurations on the two archetype targets:
  n=325 (Stage A: compressed chain3 packing, residual ~2.6e-4, rigid contacts)
  n=350 (Stage B: grid seed at g-0.02, needs motif discovery)
Prints final obj / max_overlap / packlib-ok for each config.
"""
import json
import sys
import time
from math import ceil, sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

sys.path.insert(0, ROOT + "/scripts")
import numpy as np
import packlib as P
from sa_push import (anneal, final_max_overlap, grid_seed, hw_vals,
                     pair_pen_k, out_pen, total_pen, OUTW)

TAB = ROOT + "/workspace/submission/table.json"
tab = json.load(open(TAB))

def prep_A(n, shrink=0.004):
    rec = tab[str(n)]
    L0 = rec["L"]
    f = (L0 - shrink) / L0
    X = np.array([q[0] for q in rec["state"]]) * f
    Y = np.array([q[1] for q in rec["state"]]) * f
    TH = np.array([q[2] for q in rec["state"]])
    return X, Y, TH, L0 - shrink, L0

def prep_B(n, shrink=0.02):
    g = ceil(sqrt(n))
    L = g - shrink
    X, Y, TH = grid_seed(n, L, seed=7919 * n)
    return X, Y, TH, L, float(g)

def report(tag, X, Y, TH, Lt, L0, dt):
    mo, mx = final_max_overlap(X, Y, TH, Lt)
    st = [(float(x), float(y), float(t)) for x, y, t in zip(X, Y, TH)]
    r = P.verify(st, tol=1e-9)
    print(f"{tag}: L {L0:.4f}->{Lt:.4f} obj_end mo={mo:.2e} out={mx:.2e} "
          f"ok={r['ok']} pen={r['worst_pen']:.2e} ({dt:.0f}s)", flush=True)
    return r["ok"]

def main():
    cases = [
        ("A325", prep_A, dict(t0=3e-3, tend=1e-8, moves=60000)),
        ("A325", prep_A, dict(t0=1e-3, tend=1e-9, moves=60000)),
        ("A325", prep_A, dict(t0=3e-4, tend=1e-10, moves=60000)),
        ("A325", prep_A, dict(t0=1e-2, tend=1e-8, moves=60000)),
        ("A325", prep_A, dict(t0=3e-3, tend=1e-8, moves=150000)),
        ("B350", prep_B, dict(t0=1e-2, tend=1e-8, moves=60000)),
        ("B350", prep_B, dict(t0=3e-3, tend=1e-8, moves=60000)),
        ("B350", prep_B, dict(t0=1e-3, tend=1e-9, moves=60000)),
        ("B350", prep_B, dict(t0=3e-2, tend=1e-8, moves=150000)),
    ]
    for tag, prep, kw in cases:
        n = 325 if tag == "A325" else 350
        X, Y, TH, Lt, L0 = prep(n)
        t0 = time.time()
        fin = anneal(X, Y, TH, Lt, seed=1, **kw)
        ok = report(f"{tag} {kw}", X, Y, TH, Lt, L0, time.time() - t0)

if __name__ == "__main__":
    main()
