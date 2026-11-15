#!/usr/bin/env python3
r"""contact_lp.py — compaction over a fixed contact graph (GLM round, 15 Nov 2026).

The idea the owner asked for: stop searching arrangements, and ask the
arrangement's own *contact graph* for the smallest container it admits.

With every angle frozen (the phase-change reading: Δθ = 0 while the spatial
projection runs), "square i and square j do not overlap" becomes linear: pick
the axis a_ij on which the pair is currently best separated, take the sign of
its projection σ_ij, and require

    σ_ij · (c_j − c_i) · a_ij  ≥  e_i + e_j          e = half-width at that angle

and the walls are linear too:  c_i − e_i ≥ 0,  c_i + e_i ≤ L  (both axes).
Minimising L over that polytope is a linear program, and any feasible point is
a *valid packing* by construction — the constraints imply separation on the
chosen axis.  The current state is a feasible point, so the LP can only improve
it; after solving, the exact verifier decides whether the improvement is real.

This is the same linearisation `lp_closure.py` uses for feasibility at a target
side, read the other way round: here the side is the objective.

Usage:
    python3 scripts/contact_lp.py --run --max-n 200 --rounds 4
    python3 scripts/contact_lp.py --run --max-n 1000 --touch 0.05
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402


def extents(theta: float) -> float:
    return 0.5 * (abs(math.cos(theta)) + abs(math.sin(theta)))


def axes_of(theta: float):
    c, s = math.cos(theta), math.sin(theta)
    return ((c, s), (-s, c))


def compact_lp(state, rounds: int = 4, touch: float = 0.05, iters: int = 1):
    """Solve the compaction LP for a fixed contact graph; return the new state."""
    cur = np.array(state, dtype=float)
    n = len(cur)
    e = np.array([extents(t) for t in cur[:, 2]])
    for _ in range(rounds):
        # variables: x_0..x_{n-1}, y_0..y_{n-1}, L
        c = np.zeros(2 * n + 1)
        c[-1] = 1.0
        A, b = [], []
        # walls:  x + e - L <= 0 ;  -x + e <= 0   (and the same for y)
        for i in range(n):
            row = np.zeros(2 * n + 1)
            row[i] = 1.0
            row[-1] = -1.0
            A.append(row)
            b.append(-e[i])
            row = np.zeros(2 * n + 1)
            row[i] = -1.0
            A.append(row)
            b.append(-e[i])
            row = np.zeros(2 * n + 1)
            row[n + i] = 1.0
            row[-1] = -1.0
            A.append(row)
            b.append(-e[i])
            row = np.zeros(2 * n + 1)
            row[n + i] = -1.0
            A.append(row)
            b.append(-e[i])
        # pair constraints on near pairs only (all four axis families)
        cx, cy, ct = cur[:, 0], cur[:, 1], cur[:, 2]
        cth, sth = np.cos(ct), np.sin(ct)
        pts = np.stack([cx, cy], axis=0)
        PU = np.stack([cth, sth], axis=1) @ pts          # PU[i,j] = c_j . u_i
        PV = np.stack([-sth, cth], axis=1) @ pts         # PV[i,j] = c_j . v_i
        Aui = np.diag(PU)[:, None] - PU                  # (c_i - c_j) . u_i
        Avi = np.diag(PV)[:, None] - PV
        Auj = -Aui.T                                     # (c_i - c_j) . u_j
        Avj = -Avi.T
        fams = np.stack([Aui, Avi, Auj, Avj])
        marg = np.abs(fams) - (e[:, None] + e[None, :])
        best = np.argmax(marg, axis=0)
        margin = np.take_along_axis(marg, best[None], 0)[0]
        dval = np.take_along_axis(fams, best[None], 0)[0]
        tri = np.triu(margin, 1) <= touch
        ii, jj = np.where(tri)
        for i, j in zip(ii, jj):
            f = best[i, j]
            if f == 0:
                ax, ay = float(cth[i]), float(sth[i])
            elif f == 1:
                ax, ay = float(-sth[i]), float(cth[i])
            elif f == 2:
                ax, ay = float(cth[j]), float(sth[j])
            else:
                ax, ay = float(-sth[j]), float(cth[j])
            sigma = math.copysign(1.0, float(dval[i, j]))
            row = np.zeros(2 * n + 1)
            row[i] += sigma * ax
            row[j] -= sigma * ax
            row[n + i] += sigma * ay
            row[n + j] -= sigma * ay
            A.append(-row)
            b.append(-(e[i] + e[j]))
        res = linprog(c, A_ub=np.array(A), b_ub=np.array(b),
                      bounds=[(None, None)] * (2 * n) + [(0, None)],
                      method="highs")
        if not res.success:
            break
        new = np.empty_like(cur)
        new[:, 0] = res.x[:n]
        new[:, 1] = res.x[n:2 * n]
        new[:, 2] = cur[:, 2]
        ok, worst, L = _verify(new)
        if not ok or L >= _bbox(cur) - 1e-12:
            break
        cur = new
    return cur


def _verify(state):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in state])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def _bbox(state):
    xs, ys = state[:, 0], state[:, 1]
    e = np.array([extents(t) for t in state[:, 2]])
    return float(max(np.max(xs + e) - np.min(xs - e), np.max(ys + e) - np.min(ys - e)))


def run(max_n: int, rounds: int, touch: float, only=None) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    tab = {n: P.verify(sub[n])["L"] for n in range(1, 1001) if n in sub
           and len(sub[n]) == n}
    wins = []
    t0 = time.time()
    todo = [n for n in sorted(tab) if n <= max_n and (only is None or n in only)]
    for n in todo:
        state = np.array([(x, y, t) for x, y, t in sub[n]], dtype=float)
        before = tab[n]
        new = compact_lp(state, rounds=rounds, touch=touch)
        ok, worst, L = _verify(new)
        if not ok:
            continue
        if L < before - 1e-9:
            fin, r = P.finalize([(float(a), float(b), float(c)) for a, b, c in new])
            if r["ok"] and r["L"] < before - 1e-9:
                gain = (before - r["L"]) / math.sqrt(n)
                wins.append({"n": n, "L_before": before, "L_after": r["L"],
                             "gain": gain,
                             "state": [[float(a), float(b), float(c)] for a, b, c in fin]})
                print(f"  WIN n={n}: {before:.9f} -> {r['L']:.9f}  gain {gain:.3e}"
                      f"  ({time.time()-t0:.0f} s)", flush=True)
    path = os.path.join(ROOT, "workspace/push/contact_lp_results.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"found": wins, "rows_tried": len(todo),
               "score_gain": sum(w["gain"] for w in wins)}, open(path, "w"), indent=1)
    print(f"rows tried: {len(todo)}; wins: {len(wins)}; gain "
          f"{sum(w['gain'] for w in wins):.9f}; wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--max-n", type=int, default=200)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--touch", type=float, default=0.05)
    args = ap.parse_args()
    if args.run:
        return run(args.max_n, args.rounds, args.touch)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
