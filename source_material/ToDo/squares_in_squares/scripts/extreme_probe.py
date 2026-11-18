#!/usr/bin/env python3
r"""extreme_probe.py — the §11.5 probe with an EARNED free set (run 67).

Run 65 freed "the k squares that touch walls", and every cell refused because the
frozen remainder still spanned the full side: the free set was chosen so that the
refusal was built in.

This version chooses the free set the way the geometry does:

  1. SEEDS: the squares that actually achieve the four extremes
     min(x-h), max(x+h), min(y-h), max(y+h) at the delivered state;
  2. GROWTH: repeatedly adjoin the tight-pair partners (pen <= 1e-9) of every
     free square, one ring at a time;
  3. STOP when the frozen core stops spanning the side in BOTH axes, i.e. when
     max(span_x, span_y) < L - eps for the eps tested -- only then can a shrink
     exist at all;
  4. PRICE: at that k (and every smaller ring), solve the declared-axis LP at
     L - eps for eps in {1e-6, 1e-4, 1e-2}, certify with packlib.verify, score
     with the canonical scorer.

Reported: the smallest k at which the core stops spanning, and the smallest k at
which the LP actually becomes feasible / gains.  If the core only stops spanning
when nearly everything is free, that is the result -- it says the side is a
whole-wall property, and a k-neighbourhood cannot be a lever.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ        # noqa: E402
import packlib as P         # noqa: E402
from sat_probe import frames, pair_tables, solve_lp  # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/extreme_probe.json")
EPS = [1e-6, 1e-4, 1e-2]
TIGHT = 1e-9


def tight_adj(pen):
    n = len(pen)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if abs(pen[i, j]) <= TIGHT:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def span_of(xy, h, idx):
    idx = list(idx)
    if not idx:
        return 0.0, 0.0
    xs = np.concatenate([xy[idx, 0] - h[idx], xy[idx, 0] + h[idx]])
    ys = np.concatenate([xy[idx, 1] - h[idx], xy[idx, 1] + h[idx]])
    return float(xs.max() - xs.min()), float(ys.max() - ys.min())


def run_row(n):
    per = SQ.load()
    st = per[n]
    xy, th, cs, sn = frames(st)
    L0 = SQ.extent(st)
    S, pen, win, sign = pair_tables(xy, cs, sn)
    h = 0.5 * (np.abs(cs) + np.abs(sn))
    adj = tight_adj(pen)
    seeds = {int(np.argmin(xy[:, 0] - h)), int(np.argmax(xy[:, 0] + h)),
             int(np.argmin(xy[:, 1] - h)), int(np.argmax(xy[:, 1] + h))}
    free = set(seeds)
    rings, first_unspanned, first_feasible, best = [], None, None, None
    for r in range(len(xy)):
        comp = set(range(len(xy))) - free
        sx, sy = span_of(xy, h, comp)
        ring = {"ring": r, "k": len(free), "core_span_x": sx, "core_span_y": sy,
                "core_blocks": max(sx, sy) >= L0 - EPS[0]}
        if not ring["core_blocks"] and first_unspanned is None:
            first_unspanned = len(free)
        # price this k (only when the core could allow a shrink, or at ring 0)
        if not ring["core_blocks"]:
            for eps in EPS:
                ok, new, _ = solve_lp(xy, th, cs, sn, S, win, sign, free, L0 - eps)
                if not ok:
                    continue
                stt = [(float(new[i][0]), float(new[i][1]), float(th[i]))
                       for i in range(len(new))]
                v = P.verify(stt, tol=1e-9)
                L = SQ.extent(stt)
                gain = SQ.row_gain(n, L) - SQ.row_gain(n, L0)
                ring.setdefault("feasible", []).append(
                    {"eps": eps, "L": L, "gain": gain,
                     "verifies": v["ok"], "worst_pen": v["worst_pen"]})
                if first_feasible is None:
                    first_feasible = len(free)
                if gain > 1e-9 and (best is None or gain > best["gain"]):
                    best = {"k": len(free), "eps": eps, "L": L, "gain": gain,
                            "verifies": v["ok"]}
        rings.append(ring)
        # grow: seeds -> tight partners
        nxt = set(free)
        for s in free:
            nxt |= adj[s]
        if nxt == free:
            break
        free = nxt
    return {"n": n, "L_delivered": L0, "seed_size": len(seeds),
            "first_unspanned_k": first_unspanned,
            "first_feasible_k": first_feasible,
            "best_gain": best, "rings": rings}


def main() -> int:
    per = SQ.load()
    cands = sorted(((SQ.extent(per[n]) ** 2 - n, n) for n in range(20, 301)),
                   reverse=True)
    targets = [n for _, n in cands[:4]]
    out = [run_row(n) for n in targets]
    print(f"{'n':>4} {'L_del':>9} {'k(unspan)':>10} {'k(feasible)':>12} "
          f"{'gain':>10}  rings")
    for o in out:
        kc = "never" if o["first_unspanned_k"] is None else str(o["first_unspanned_k"])
        kf = "never" if o["first_feasible_k"] is None else str(o["first_feasible_k"])
        g = "—" if not o["best_gain"] else f"{o['best_gain']['gain']:+.2e}"
        print(f"{o['n']:4d} {o['L_delivered']:9.6f} {kc:>10} {kf:>12} {g:>10}  "
              f"{[r['k'] for r in o['rings']]}")
    gains = [o["best_gain"] for o in out if o["best_gain"]]
    print(f"\nrows probed: {len(out)}   rows with a certified gain: {len(gains)}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"run": 67, "schema": "extremeprobe/1", "eps": EPS,
                   "tight_tol": TIGHT, "rows": out}, f, indent=1)
    print(f"ledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
