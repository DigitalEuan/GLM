#!/usr/bin/env python3
r"""grain_injection.py — heterogeneous nucleation: the basin jump (15 Nov 2026).

`recovery_probe.py` measured the real deficiency: from the grid start the
rotation LP plus contact rewiring recovers every puzzle whose optimum *is* the
grid (n = 6, 7, 13, 20) and misses every one whose optimum is off it
(n = 5, 10, 17, 26).  The engine can certify the grid and cannot leave it.  That
is a basin problem, not a parameter problem: continuous local moves cannot cross
from the lattice basin into a tilted one, however long they run.

Crystal growth supplies the missing move by inverting itself.  Homogeneous
nucleation (Voronoi impingement, `crystal_growth.py`) can only produce the
lattice, but real crystals also nucleate **heterogeneously on a substrate**: a
new orientation appears *inside* an existing grain and grows at its expense until
the boundary locks.  Here the substrate is the grid packing, the new grain is a
disc of squares rotated rigidly by φ about a seed, and the LP is the growth step
that lets the two orientations settle against each other.

A grain is accepted only if the exact verifier says the packing is valid and the
container side strictly fell.  So a grain that cannot survive impingement is
discarded by measurement, not by argument.

Usage:
    python3 scripts/grain_injection.py --n 5 10 17 26
    python3 scripts/grain_injection.py --n 5 --angles 45 --radii 1.0 1.5
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402
import rotation_lp as R                                  # noqa: E402


def inject(state, seed_idx: int, radius: float, phi: float):
    """Rotate the disc of squares within `radius` of the seed rigidly by phi."""
    st = np.array(state, dtype=float)
    c0 = st[seed_idx].copy()
    d = st[:, :2] - c0[:2]
    inside = np.hypot(d[:, 0], d[:, 1]) <= radius + 1e-12
    c, s = math.cos(phi), math.sin(phi)
    rot = np.stack([c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1]], axis=1)
    st[inside, 0] = c0[0] + rot[inside, 0]
    st[inside, 1] = c0[1] + rot[inside, 1]
    st[inside, 2] += phi
    return st


def grow_grain(state, phi: float, radius: float, rounds: int, budget: int,
               seed: int):
    """Inject a grain at the best seed, let it settle, return (state, verify)."""
    base = P.verify([tuple(map(float, q)) for q in state])
    best, best_state = base, np.asarray(state, dtype=float)
    for s_idx in range(len(state)):
        trial = inject(state, s_idx, radius, phi)
        cand, r, _ = R.compact(trial, rounds=rounds, touch=0.08, rot=0.05,
                               pos=0.12)
        if not r["ok"]:
            continue
        if budget:
            cand2, r2, _ = R.rewire(cand, trials=budget, rounds=2, touch=0.08,
                                    seed=seed + s_idx)
            if r2["ok"] and r2["L"] < r["L"] - 1e-12:
                cand, r = cand2, r2
        if r["ok"] and r["L"] < best["L"] - 1e-12:
            best, best_state = r, cand
    return best_state, best


def probe(targets, angles, radii, rounds: int, budget: int) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    rows, hits = [], 0
    for n in targets:
        k, grid = P.grid_packing(n)
        state = np.array([(x, y, t) for x, y, t in grid], dtype=float)
        start = P.verify([tuple(map(float, q)) for q in state])
        best, best_state, best_cfg = start, state, None
        for phi_deg in angles:
            for rad in radii:
                cand, r = grow_grain(state, math.radians(phi_deg), rad, rounds,
                                     budget, seed=n * 1000 + int(phi_deg))
                if r["ok"] and r["L"] < best["L"] - 1e-12:
                    best, best_state, best_cfg = r, cand, (phi_deg, rad)
        target = (P.verify(sub[n])["L"] if n in sub and len(sub[n]) == n
                  else P.grid_L(n))
        hit = bool(best["ok"] and best["L"] <= target + 1e-6)
        hits += hit
        rows.append({"n": n, "start": start["L"], "target": target,
                     "reached": best["L"], "hit": hit, "config": best_cfg,
                     "ok": bool(best["ok"])})
        print(f"  n={n:<4} grid {start['L']:.4f} -> {best['L']:.6f}"
              f"  target {target:.6f}  {'HIT' if hit else 'miss'}"
              f"  cfg {best_cfg}", flush=True)
    path = os.path.join(ROOT, "workspace/push/grain_injection.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"rows": rows, "hits": hits, "of": len(rows)}, open(path, "w"), indent=1)
    print(f"reached {hits}/{len(rows)} targets with an injected grain; wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, nargs="+", default=[5, 10, 17, 26])
    ap.add_argument("--angles", type=float, nargs="+", default=[45, 30, 15])
    ap.add_argument("--radii", type=float, nargs="+", default=[1.0, 1.6, 2.4])
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--budget", type=int, default=6)
    args = ap.parse_args()
    return probe(args.n, args.angles, args.radii, args.rounds, args.budget)


if __name__ == "__main__":
    raise SystemExit(main())
