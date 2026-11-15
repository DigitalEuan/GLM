#!/usr/bin/env python3
r"""recovery_probe.py — can the move set *find* a known optimum cold? (15 Nov 2026)

Every other script here asks "can we beat the record".  This one asks the
question the failures actually raise: **from a cold, wrong start, can the engine
walk to a value we already know is achievable?**  A search that cannot recover a
known answer has a move-set problem, not a budget problem, and that distinction
transfers — a Rule-30 or ARC engine that cannot rediscover a rule it has already
seen is failing for the same structural reason.

Protocol: start every target from its grid packing (L = ceil(sqrt n), the worst
sensible start), run the rotation-relaxed compaction LP plus contact rewiring
with a fixed budget, and compare with the frontier value in our own submission.

    python3 scripts/recovery_probe.py --n 5 6 7 10 13 17 20 26 --budget 20
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


def probe(targets, budget: int, rounds: int, seed: int = 0) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    rows, recovered = [], 0
    for n in targets:
        k, grid = P.grid_packing(n)
        start = np.array([(x, y, t) for x, y, t in grid], dtype=float)
        cand, r, _ = R.compact(start, rounds=rounds, touch=0.06, rot=0.05)
        cand, r, _ = R.rewire(cand, trials=budget, rounds=2, touch=0.06, seed=seed + n)
        L = r["L"] if r["ok"] else float("nan")
        target = P.verify(sub[n])["L"] if n in sub and len(sub[n]) == n else P.grid_L(n)
        hit = bool(r["ok"] and L <= target + 1e-6)
        recovered += hit
        rows.append({"n": n, "start": P.grid_L(n), "target": target,
                     "recovered_L": L, "hit": hit, "ok": bool(r["ok"])})
        print(f"  n={n:<4} start {P.grid_L(n):.4f}  target {target:.6f}"
              f"  engine {L:.6f}  {'HIT' if hit else 'miss'}", flush=True)
    path = os.path.join(ROOT, "workspace/push/recovery_probe.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"rows": rows, "recovered": recovered, "of": len(rows)},
              open(path, "w"), indent=1)
    print(f"recovered {recovered}/{len(rows)} known optima from the grid start; wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, nargs="+", default=[5, 6, 7, 10, 13, 17, 20, 26])
    ap.add_argument("--budget", type=int, default=20)
    ap.add_argument("--rounds", type=int, default=4)
    args = ap.parse_args()
    return probe(args.n, args.budget, args.rounds)


if __name__ == "__main__":
    raise SystemExit(main())
