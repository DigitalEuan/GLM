#!/usr/bin/env python3
r"""crystal_growth.py — the mineral framework (GLM round, 15 November 2026).

The owner's observation: the only natural system that optimises square packing
is mineral growth — crystals nucleate, grow, and *impinge* on one another, and
the frozen rock records the impingement pattern.  This file reads that as an
engine, with three stages and one honest limit.

* **Nucleation** — n sites in the container.
* **Growth and impingement** — each site grows a cell until it meets its
  neighbours: the cells are the Voronoi (equal-growth, equal-time) regions of
  the sites, clipped to the container.  A grain's *habit* is the square; the
  grain's orientation is its cell's principal axis, which is the only
  orientation freedom the habit allows.
* **Ripening** — a coarsening move: perturb the nucleation field, regrow, keep
  the change if the largest inscribed grains grew.  This is the Ostwald reading
  (small grains dissolve, large ones take their space) with the acceptance rule
  made deterministic.

The limit is the one that decides everything: a packing made this way is valid
**by construction** (each square lies inside its own cell, and cells do not
overlap), so nothing here needs a repair step — but the density is capped by the
impingement geometry, not by the packing problem.  What this framework can do
is generate arrangements no motif family reaches; what it cannot do is certify
optimality, and it says so.

Every emitted packing still goes through `packlib.finalize` + `packlib.verify`.

Usage:
    python3 scripts/crystal_growth.py --n 17 --restarts 60
    python3 scripts/crystal_growth.py --probe
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


# ------------------------------------------------------------ half-plane work
def clip_halfplane(poly, nx, ny, d):
    """Keep the part of the polygon with  n . x <= d."""
    out = []
    m = len(poly)
    for i in range(m):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % m]
        da = nx * ax + ny * ay - d
        db = nx * bx + ny * by - d
        if da <= 0:
            out.append((ax, ay))
        if (da < 0 < db) or (db < 0 < da):
            t = da / (da - db)
            out.append((ax + t * (bx - ax), ay + t * (by - ay)))
    return out


def cell_of(sites, i, box=1.0):
    """Voronoi cell of site i, clipped to [0, box]^2 (equal growth rate)."""
    poly = [(0.0, 0.0), (box, 0.0), (box, box), (0.0, box)]
    xi, yi = sites[i]
    for j, (xj, yj) in enumerate(sites):
        if i == j:
            continue
        # bisector: points closer to i than to j ->  (x - m).(j - i) <= 0
        nx, ny = xj - xi, yj - yi
        d = nx * (xi + xj) / 2.0 + ny * (yi + yj) / 2.0
        poly = clip_halfplane(poly, nx, ny, d)
        if len(poly) < 3:
            return poly
    return poly


def inscribed(poly, x, y):
    """(half-size t, orientation) of the largest square at (x, y) inside poly."""
    if len(poly) < 3:
        return 0.0, 0.0
    # principal axis of the cell: the edge direction with the smallest spread
    pts = np.array(poly)
    cen = pts.mean(axis=0)
    u, s, vt = np.linalg.svd(pts - cen)
    th = math.atan2(vt[0, 1], vt[0, 0])
    best = None
    for deg in (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, th, th + math.pi / 4):
        t = math.radians(deg)
        c, sn = math.cos(t), math.sin(t)
        e = 0.5 * (abs(c) + abs(sn)) / 0.5          # extent per unit half-size
        tt = 1e18
        for k in range(len(pts)):
            ax, ay = pts[k]
            bx, by = pts[(k + 1) % len(pts)]
            # inward edge normal
            nx, ny = by - ay, -(bx - ax)
            norm = math.hypot(nx, ny)
            if norm < 1e-12:
                continue
            nx, ny = nx / norm, ny / norm
            dist = (ax - x) * nx + (ay - y) * ny     # > 0 when (x,y) is inside
            if dist <= 0:
                return 0.0, t
            ext = 0.5 * (abs(c * nx + sn * ny) + abs(-sn * nx + c * ny))
            if ext > 1e-12:
                tt = min(tt, dist / (2.0 * ext))
        if best is None or tt > best[0]:
            best = (tt, t)
    return best if best else (0.0, 0.0)


def evaluate(sites, box=1.0):
    """(container side for unit squares, states) from the impingement pattern."""
    states = []
    tmin = 1e18
    for i, (x, y) in enumerate(sites):
        poly = cell_of(sites, i, box)
        t, th = inscribed(poly, x, y)
        tmin = min(tmin, t)
        states.append((x, y, th, t))
    if tmin <= 0:
        return float("inf"), []
    scale = 0.5 / tmin
    out = [(x * scale, y * scale, th) for x, y, th, _t in states]
    return scale * box, out


# --------------------------------------------------------------- the engine
def grow(n: int, restarts: int = 40, seed: int = 0, box: float = 1.0):
    rng = np.random.default_rng(seed)
    k = int(math.ceil(math.sqrt(n)))
    best = None
    # stage 1: nucleation on a jittered lattice, then ripening by random moves
    for r in range(restarts):
        sites = []
        for i in range(n):
            gx, gy = i % k, i // k
            jx = rng.normal(0, 0.06 if r else 0.0)
            jy = rng.normal(0, 0.06 if r else 0.0)
            sites.append(((gx + 0.5) / k + jx / k, (gy + 0.5) / k + jy / k))
        sites = [(min(max(x, 1e-3), 1 - 1e-3), min(max(y, 1e-3), 1 - 1e-3))
                 for x, y in sites]
        L, _ = evaluate(sites, box)
        if best is None or L < best[0]:
            best = (L, sites)
    L, sites = best
    # stage 2: ripening -- perturb one nucleation site at a time, keep the gain
    step = 0.02
    for it in range(60 * n):
        i = int(rng.integers(0, n))
        trial = list(sites)
        x, y = trial[i]
        trial[i] = (min(max(x + rng.normal(0, step), 1e-3), 1 - 1e-3),
                    min(max(y + rng.normal(0, step), 1e-3), 1 - 1e-3))
        L2, _ = evaluate(trial, box)
        if L2 < L - 1e-12:
            L, sites = L2, trial
        elif it % (50 * n) == 0:
            step *= 0.8
    return L, sites


def probe(targets=(5, 7, 10, 13, 17, 20, 26, 30), restarts=12):
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    tab = {n: P.verify(sub[n])["L"] for n in range(1, 1001) if n in sub
           and len(sub[n]) == n}
    rows = []
    wins = []
    for n in targets:
        bestL, bestState = float("inf"), None
        for seed in range(2):
            L, sites = grow(n, restarts=restarts, seed=seed)
            _, states = evaluate(sites)
            if states and L < bestL:
                bestL, bestState = L, states
        if bestState is None:
            rows.append({"n": n, "L": None, "table": tab.get(n)})
            continue
        fin, r = P.finalize(bestState)
        ok = r["ok"]
        L = r["L"] if ok else float("nan")
        rows.append({"n": n, "L": L, "table": tab.get(n), "ok": ok})
        if ok and n in tab and L < tab[n] - 1e-9:
            wins.append({"n": n, "L_before": tab[n], "L_after": L,
                         "gain": (tab[n] - L) / math.sqrt(n),
                         "state": [[float(a), float(b), float(c)] for a, b, c in fin]})
        print(f"  n={n:<4} impingement L={L:.6f}  table {tab.get(n, float('nan')):.6f}"
              f"  grid {P.grid_L(n):.4f}  ok={ok}", flush=True)
    path = os.path.join(ROOT, "workspace/push/crystal_growth_results.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"rows": rows, "found": wins,
               "score_gain": sum(w["gain"] for w in wins)}, open(path, "w"), indent=1)
    print(f"wins: {len(wins)}; gain {sum(w['gain'] for w in wins):.6f}; wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--n", type=int, default=17)
    ap.add_argument("--restarts", type=int, default=30)
    args = ap.parse_args()
    if args.probe:
        return probe(restarts=args.restarts)
    if args.n:
        L, sites = grow(args.n, restarts=args.restarts)
        _, states = evaluate(sites)
        fin, r = P.finalize(states)
        print(f"n={args.n}: L={r['L']:.6f} ok={r['ok']}  (design {L:.6f})")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
