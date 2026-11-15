#!/usr/bin/env python3
r"""notch_engine.py — discrete insertion into the notch (GLM round, 15 Nov 2026).

The measurements left one move untried.  The rotation LP proved every record row
is tight in (position, rotation) — no continuous step lowers the side — and the
recovery probe proved the same move set cannot leave the lattice basin.  What is
left is the *discrete* step: put one more square into the arrangement, in a place
the current contact graph does not describe, and let the LP settle it.  That is
the notch insertion, and the frontier's own geometry says where it goes: the
existing rows are nested — an axis-aligned ring around a rotated inner cluster
(n=5 is four corner squares around a single 45-degree diamond at the centre;
n=10 is eight ring squares around two diamonds; n=17 is ten ring squares around a
seven-square cluster at 39.8 degrees).

Two modes, both read the arrangement as the owner reads the puzzle set: **the
answer to a row is outlined by the row above it**.

* `--recover` — the capability test.  Build n = k^2 + 1 from the grid for k^2 by
  inserting a single 45-degree square at the centre, then repair and let the LP
  settle.  If this reaches the known side (2.707107 for n=5, 3.707107 for n=10,
  4.675530 for n=17, ...) the discrete step works and the earlier misses were a
  move-set failure, not a search failure.
* `--grow` — the scoring test.  For each row n, take the arrangement of row n-1,
  search the free area for a placement (a coarse candidate grid at 0 and 45
  degrees), insert, repair, settle with the rotation LP plus rewiring, and gate.
  A row improves only if the exact verifier says so.

Every candidate goes through `packlib.finalize` + `packlib.verify`.

Usage:
    python3 scripts/notch_engine.py --recover
    python3 scripts/notch_engine.py --grow --max-n 120
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


def normalise(state):
    """Shift so the bbox min corner sits at (0,0); returns (state, L)."""
    st = np.array(state, dtype=float)
    e = np.array([R.support(t) for t in st[:, 2]])
    st[:, 0] -= float(np.min(st[:, 0] - e))
    st[:, 1] -= float(np.min(st[:, 1] - e))
    return st, R.bbox_L([tuple(map(float, q)) for q in st])


def fits(state, cand) -> bool:
    """Exact pair check of one candidate against an arrangement."""
    trial = [tuple(map(float, q)) for q in state] + [tuple(map(float, cand))]
    r = P.verify(trial)
    # verify's worst_pen covers every pair, so a single-pair test is enough here
    return r["worst_pen"] <= 0.0


def candidate_grid(L: float, steps: int, angles):
    out = []
    for i in range(steps + 1):
        for j in range(steps + 1):
            x = L * i / steps
            y = L * j / steps
            for a in angles:
                out.append((x, y, math.radians(a)))
    return out


def settle(state, rounds: int = 8, budget: int = 4, seed: int = 0):
    cand, r, _ = R.compact(state, rounds=rounds, touch=0.10, rot=0.06, pos=0.15)
    if not r["ok"] and r["worst_pen"] <= 1e-9:
        # exact touch: contacts are jammed to floating noise, so open them the
        # way the pipeline always does and let the verifier judge the result
        fin, rf = P.finalize([tuple(map(float, q)) for q in cand])
        if rf["ok"]:
            return np.array(fin, dtype=float), rf
    if not r["ok"]:
        # the linearised step can overshoot by the linearisation error; push the
        # residual overlaps apart geometrically, then judge again
        sep, r2 = R.separate(cand, iters=200, step=0.3)
        r2 = P.verify([tuple(map(float, q)) for q in sep])
        if r2["ok"]:
            c2, r3, _ = R.compact(sep, rounds=3, touch=0.10, rot=0.04, pos=0.05)
            if r3["ok"] and r3["L"] <= r2["L"] + 1e-12:
                return c2, r3
            return sep, r2
        return cand, r
    if budget:
        cand2, r2, _ = R.rewire(cand, trials=budget, rounds=2, touch=0.10, seed=seed)
        if r2["ok"] and r2["L"] < r["L"] - 1e-12:
            return cand2, r2
    return cand, r


def grow_row(base_state, steps: int, angles, rounds: int, budget: int, seed: int):
    """Insert one square into `base_state` and settle; returns (state, verify)."""
    st, L = normalise(base_state)
    best, best_state = None, None          # only a state that really has +1 square counts
    for cand in candidate_grid(L, steps, angles):
        if not fits(st, cand):
            continue
        trial = np.vstack([st, np.array([cand], dtype=float)])
        s, r = settle(trial, rounds=rounds, budget=budget, seed=seed)
        if not r["ok"] or len(s) != len(st) + 1:
            continue
        if best is None or r["L"] < best["L"] - 1e-12:
            best, best_state = r, s
    if best is None:
        return st, P.verify([tuple(map(float, q)) for q in st])
    return best_state, best


def recover(ks, rounds: int = 10, budget: int = 4, steps: int = 4,
            angles=(0, 45, 39.805)) -> int:
    """n = k^2 + 1 from the grid plus one 45-degree square at the centre."""
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    rows, hits = [], 0
    for k in ks:
        n = k * k + 1
        _, grid = P.grid_packing(k * k)
        st = np.array([(x, y, t) for x, y, t in grid], dtype=float)
        st, L = normalise(st)
        # the insertion searches the free area: centre first, then the grid
        cand, r = settle(np.vstack([st, np.array([[L / 2.0, L / 2.0, math.pi / 4.0]])]),
                         rounds=rounds, budget=budget, seed=n)
        alt, ra = grow_row(st, steps, angles, rounds, budget, n)
        if (ra["ok"] and len(alt) == n and
                not (r["ok"] and len(cand) == n and r["L"] <= ra["L"] + 1e-12)):
            cand, r = alt, ra
        target = (P.verify(sub[n])["L"] if n in sub and len(sub[n]) == n
                  else P.grid_L(n))
        hit = bool(r["ok"] and len(cand) == n and r["L"] <= target + 1e-6)
        hits += hit
        rows.append({"n": n, "k": k, "target": target,
                     "reached": r["L"], "hit": hit, "ok": bool(r["ok"])})
        print(f"  n={n:<5} grid {P.grid_L(n):.4f} + centre diamond -> {r['L']:.6f}"
              f"  target {target:.6f}  {'HIT' if hit else 'miss'}", flush=True)
    path = os.path.join(ROOT, "workspace/push/notch_recover.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"rows": rows, "hits": hits, "of": len(rows)}, open(path, "w"), indent=1)
    print(f"recovered {hits}/{len(rows)} known sides from a single insertion; wrote {path}")
    return 0


def grow(max_n: int, min_n: int, steps: int, angles, rounds: int, budget: int) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    tab = {n: P.verify(sub[n])["L"] for n in range(1, 1001)
           if n in sub and len(sub[n]) == n}
    wins, tried = [], 0
    for n in sorted(tab):
        if n > max_n or n < min_n or (n - 1) not in sub:
            continue
        tried += 1
        base = [(x, y, t) for x, y, t in sub[n - 1]]
        st, r = grow_row(np.array(base), steps, angles, rounds, budget, seed=n)
        if r["ok"] and len(st) == n and r["L"] < tab[n] - 1e-9:
            fin, rr = P.finalize([tuple(map(float, q)) for q in st])
            if rr["ok"] and rr["L"] < tab[n] - 1e-9:
                gain = (tab[n] - rr["L"]) / math.sqrt(n)
                wins.append({"n": n, "L_before": tab[n], "L_after": rr["L"],
                             "gain": gain,
                             "state": [[float(a), float(b), float(c)] for a, b, c in fin]})
                print(f"  WIN n={n}: {tab[n]:.9f} -> {rr['L']:.9f} gain {gain:.3e}",
                      flush=True)
    path = os.path.join(ROOT, "workspace/push/notch_grow.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"found": wins, "rows_tried": tried,
               "score_gain": sum(w["gain"] for w in wins)}, open(path, "w"), indent=1)
    print(f"rows grown from the row below: {tried}; wins: {len(wins)}; gain "
          f"{sum(w['gain'] for w in wins):.9f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--recover", action="store_true")
    ap.add_argument("--grow", action="store_true")
    ap.add_argument("--ks", type=int, nargs="+", default=[2, 3, 4, 5, 6, 7])
    ap.add_argument("--min-n", type=int, default=2)
    ap.add_argument("--max-n", type=int, default=120)
    ap.add_argument("--steps", type=int, default=6)
    ap.add_argument("--angles", type=float, nargs="+", default=[0, 45])
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--budget", type=int, default=4)
    args = ap.parse_args()
    if args.recover:
        return recover(args.ks, args.rounds, args.budget, args.steps, args.angles)
    if args.grow:
        return grow(args.max_n, args.min_n, args.steps, args.angles,
                    args.rounds, args.budget)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
