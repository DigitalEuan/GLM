#!/usr/bin/env python3
r"""swap_scan.py — move a square, not the arrangement (GLM round, 15 Nov 2026).

The ladder says the frontier's excess e = L - k is essentially a function of the
row's position in its block, with a small alphabet of motif values reused across
k.  The rows worth attacking are therefore the ones sitting just UNDER the unit
plateau (e = 0.95..1.0 at k >= 8): they are nearly-grid arrangements where the
last row almost fits, and a small construction gain moves the score.

The move is a swap, which insertion alone cannot make: delete one square, then
re-insert a unit square (at 0, 30 or 45 degrees) in the best free position, then
repair and settle with the rotation-relaxed LP plus contact rewiring.  It changes
which squares touch which — the graph-level move — while keeping the count fixed,
so it can improve a row without needing room for a new square.

A candidate counts only if `finalize` + `verify` accept it: right count, smaller
side.

    python3 scripts/swap_scan.py --near-grid 8 --budget 12
    python3 scripts/swap_scan.py --n 110 109 132 --budget 20
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
import notch_engine as NE                                # noqa: E402


def swap_row(state, steps: int, angles, rounds: int, budget: int, seed: int,
             sample: int):
    st = np.array(state, dtype=float)
    n = len(st)
    base = P.verify([tuple(map(float, q)) for q in st])
    best, best_state = base, st
    rng = np.random.default_rng(seed)
    idxs = (np.arange(n) if n <= sample else
            rng.choice(n, size=sample, replace=False))
    for i in idxs:
        survivors = np.delete(st, i, axis=0)
        survivors, L = NE.normalise(survivors)
        for cand in NE.candidate_grid(L, steps, angles):
            if not NE.fits(survivors, cand):
                continue
            trial = np.vstack([survivors, np.array([cand], dtype=float)])
            s, r = NE.settle(trial, rounds=rounds, budget=budget, seed=seed + int(i))
            if not r["ok"] or len(s) != n:
                continue
            if r["L"] < best["L"] - 1e-12:
                best, best_state = r, s
    return best_state, best


def run(targets, steps: int, angles, rounds: int, budget: int, sample: int,
        near_grid: int) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    tab = {n: P.verify(sub[n])["L"] for n in range(1, 1001)
           if n in sub and len(sub[n]) == n}
    if near_grid >= 0:
        picked = []
        for n, L in sorted(tab.items()):
            k = math.isqrt(n)
            e = L - k
            if k >= near_grid and 0.90 <= e < 1.0:
                picked.append(n)
        targets = picked if not targets else targets
    wins = []
    for n in targets:
        if n not in tab:
            continue
        st, r = swap_row(np.array(sub[n], dtype=float), steps, angles, rounds,
                         budget, seed=n, sample=sample)
        if r["ok"] and len(st) == n and r["L"] < tab[n] - 1e-9:
            fin, rr = P.finalize([tuple(map(float, q)) for q in st])
            if rr["ok"] and rr["L"] < tab[n] - 1e-9:
                gain = (tab[n] - rr["L"]) / math.sqrt(n)
                wins.append({"n": n, "L_before": tab[n], "L_after": rr["L"],
                             "gain": gain,
                             "state": [[float(a), float(b), float(c)] for a, b, c in fin]})
                print(f"  WIN n={n}: {tab[n]:.9f} -> {rr['L']:.9f} gain {gain:.3e}",
                      flush=True)
    path = os.path.join(ROOT, "workspace/push/swap_scan.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"found": wins, "targets": len(targets),
               "score_gain": sum(w["gain"] for w in wins),
               "params": {"steps": steps, "rounds": rounds, "budget": budget,
                          "sample": sample}}, open(path, "w"), indent=1)
    print(f"targets: {len(targets)}; wins {len(wins)}; gain "
          f"{sum(w['gain'] for w in wins):.9f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, nargs="*", default=[])
    ap.add_argument("--near-grid", type=int, default=-1)
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--angles", type=float, nargs="+", default=[0, 45])
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--budget", type=int, default=6)
    ap.add_argument("--sample", type=int, default=10)
    args = ap.parse_args()
    return run(args.n, args.steps, args.angles, args.rounds, args.budget,
               args.sample, args.near_grid)


if __name__ == "__main__":
    raise SystemExit(main())
