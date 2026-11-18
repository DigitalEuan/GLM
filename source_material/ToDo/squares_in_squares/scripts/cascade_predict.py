#!/usr/bin/env python3
r"""cascade_predict.py — the residue-family cascade as a predictive model.

WHY.  `workspace/docs/05-original-methods.md` states the cascade planner as an
engineering fact: a base packing at (m, L) with L below the grid value extends
to a chain of rows, and "a base at k0^2 + r opens family k^2 + r for all k".
This script writes that claim down as arithmetic, derives it *backwards* (from
a target row to the base that serves it), and measures how much of the
delivered table it explains — and how much it says is still on the table.

THE MODEL.

  Write n = k^2 + r with k = floor(sqrt(n)) and 0 < r <= 2k, so the grid value
  is ceil(sqrt(n)) = k + 1.  Let the *slack* of a row be delta(n) = L(n) - k.

  A base is a row m = k0^2 + r packed with slack delta < 1 (it beats grid).

  Chain step: at container k + delta the free band around a full k x k block
  is 2k + 1 unit cells (k right, k above, 1 corner), and

      m_{j+1} = m_j + (2 k_j + 1),   k_{j+1} = k_j + 1,   delta unchanged.

  By induction m_j = k_j^2 + r exactly, at container k_j + delta.  Since
  k + delta < k + 1 for delta < 1, every chain member beats grid, by 1 - delta.

    THEOREM (ideal cascade).  If some row k0^2 + r has slack delta < 1, then
    for every k >= k0 the row k^2 + r is packed in container k + delta.

  (An earlier version of this script claimed container k, i.e. delta = 0.  That
  is false by the area bound — k^2 + r squares cannot fit in a k x k box for
  r >= 1 — and the documented chain 5@2.8 -> 10@3.8 -> 17@4.8 shows it: the
  invariant is (r, delta), with delta = 0.8 there.  The measurement caught it.)

BACKWARD USE.  For a target n: k = floor(sqrt(n)), r = n - k^2.  The cascade
predicts

      L(n) <= k + delta*(r),    delta*(r) = min over k0 <= k of delta(k0^2 + r).

  So the row to solve is not n but the *smallest base* in n's residue class,
  and one base serves that class for every larger k.  This turns 1000 targets
  into ~60 residuals, which is the predictive content of the planner.

THE TWO THINGS MEASURED.
  * how often the table already does at least as well as the cascade predicts
    (the model is a lower bound on what the planner can reach);
  * how much score is left where the table is *worse* than the prediction —
    those rows are reachable by applying the chain to a base we already have.

Read-only: never writes table.json or submission.csv.
"""
from __future__ import annotations

import argparse
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUB = os.path.join(ROOT, "workspace/submission")
OUT = os.path.join(ROOT, "workspace/push/cascade_predict.json")


def load_L(path: str) -> dict:
    with open(path) as f:
        tab = json.load(f)
    out = {}
    for k, v in tab.items():
        if isinstance(v, dict):
            out[int(k)] = float(v["L"])
        elif isinstance(v, (list, tuple)) and len(v) == 2:
            out[int(k)] = float(v[0])
        else:
            out[int(k)] = float(v)
    return out


def kr(n: int):
    k = int(math.floor(math.sqrt(n)))
    return k, n - k * k


import sqscore as SQ

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=os.path.join(SUB, "table.json"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--nmax", type=int, default=1000)
    a = ap.parse_args()
    SQ.guard()

    L = load_L(a.table)
    rows = [n for n in range(1, a.nmax + 1) if n in L]
    score = sum(SQ.row_score(n, L[n]) for n in rows)
    beats = sum(1 for n in rows if SQ.is_beat(n, L[n]))
    print(f"rows {len(rows)}, score {score:.9f}, beats grid {beats}")

    # slack per row; residue -> running min slack over k0 <= k
    slack = {}
    for n in rows:
        k, r = kr(n)
        if r > 0:
            slack[n] = L[n] - k
    # Causal accumulation: a base can only serve rows *after* it, so the
    # running minimum is taken over rows in ascending k, comparing first and
    # only then admitting the current row as a base for later ones.
    best = {}          # r -> (smallest slack seen, the n achieving it)
    running = {}       # r -> smallest slack available at this k
    at_least, worse, better = 0, 0, 0
    gain_left = 0.0
    gain_better = 0.0
    missed = []
    improved = []
    for n in sorted(rows):
        k, r = kr(n)
        if r == 0:
            continue
        if r in running:
            pass            # handled below
        else:
            running[r] = None
        r_prev = running[r]
        if r_prev is not None:
            pred0 = k + r_prev
            if L[n] <= pred0 + 1e-9:
                at_least += 1
            else:
                worse += 1
                g = (L[n] - pred0) / math.sqrt(n)
                gain_left += g
                missed.append((round(g, 9), n, k, r, round(pred0, 6),
                               round(L[n], 6)))
            if L[n] < pred0 - 1e-9:
                better += 1
                gain_better += (pred0 - L[n]) / math.sqrt(n)
                improved.append((n, k, r, round(L[n], 6), round(pred0, 6)))
        d = slack[n]
        if d < 1.0 - 1e-12:
            cur = best.get(r)
            if cur is None or d < cur[0] - 1e-12:
                best[r] = (d, n)
            running[r] = d if r_prev is None else min(r_prev, d)
    # second pass: the loop above already compared each row against the slack
    # available before it, so nothing more is needed here.
    for n in []:
        k, r = kr(n)
        if r == 0:
            continue
        if r not in running:
            continue
        pred = k + running[r]                      # predicted container
        if L[n] <= pred + 1e-9:
            at_least += 1
        else:
            worse += 1
            g = (L[n] - pred) / math.sqrt(n)
            gain_left += g
            missed.append((round(g, 9), n, k, r, round(pred, 6), round(L[n], 6)))
        if L[n] < pred - 1e-9:
            better += 1
            gain_better += (pred - L[n]) / math.sqrt(n)
            improved.append((n, k, r, round(L[n], 6), round(pred, 6)))

    covered = at_least + worse + better
    print()
    print("cascade prediction (rows whose residue has a base with k0 <= k):")
    print(f"  rows covered by the model        {covered}")
    print(f"  table at least as good (>= pred) {at_least}")
    print(f"  table worse than prediction      {worse}")
    print(f"  table better than prediction     {better}")
    print(f"  residues with a usable base      {len(best)} "
          f"of {len({kr(n)[1] for n in rows if kr(n)[1]})}")
    print()
    print(f"score reachable by applying the chain where the table is worse: "
          f"{gain_left:.9f}")
    print(f"score by which construction beats the chain prediction:          "
          f"{gain_better:.9f}")
    if missed:
        print("\ntop reachable rows (by score gain):")
        for g, n, k, r, pred, cur in sorted(missed, reverse=True)[:12]:
            print(f"  n={n:<4} r={r:<4} k={k:<3} L={cur:<10.6f} -> {pred:<9.6f} "
                  f"gain {g:.6f}")
    if improved:
        print("\nrows where construction beats the chain prediction:")
        for n, k, r, cur, pred in sorted(improved, key=lambda z: -z[3])[:8]:
            print(f"  n={n:<4} r={r:<4} L={cur:<10.6f} (chain predicts {pred})")

    res = {"table": a.table, "rows": len(rows), "score": score, "beats_grid": beats,
           "covered": covered, "at_least": at_least, "worse": worse,
           "better": better, "residues_with_base": len(best),
           "residues_total": len({kr(n)[1] for n in rows if kr(n)[1]}),
           "gain_left": gain_left, "gain_beats_chain": gain_better,
           "base_slack": {str(r): [round(best[r][0], 9), best[r][1]] for r in best},
           "missed": sorted(missed, reverse=True)[:60],
           "beats_chain": improved[:60]}
    if a.json:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(res, f, indent=1)
        print("\nwrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
