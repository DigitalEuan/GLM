#!/usr/bin/env python3
r"""block_swap.py — run 115: the block-substitution campaign on the
compressed-lattice band tops.

The move: the frontier pose of band k is (to 0.03 %) a k x k lattice squeezed by
delta = k - L.  Pick a p x q block of that lattice, count the c cells it holds
(it has h = pq - c holes), and try to place c + 1 cells in the same block box.
If that works, the whole pose gains a cell at (nearly) unchanged side and row
m* + 1 is beaten.

Fast filter.  The block box is W x H with W = (q-1)*pitch + 1, so a substitute
needs a packing of c + 1 unit squares at side <= min(W, H).  The best known
side for c + 1 cells is our own table's (which is at or ahead of the published
record on every row it covers, runs 114).  `shortfall = L_best(c+1) - min(W,H)`
is therefore the gap between the record and what the block needs; positive
means no known packing of that count fits the block, i.e. the substitution
would itself have to be a new record.

Actual attempt.  For each band's best block the optimiser packs c + 1 cells into
the block box (penetration + wall hinge, multi-restart), and if it finds a legal
box packing the cells are spliced into the frontier pose and the whole pose is
judged by true_geom at 40 digits.

Float use: discovery, like relax_angles.py / void_insert.py.  Verdicts are
true_geom's.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ          # noqa: E402
import true_geom as TG        # noqa: E402
from void_insert import load_pose, pen_vec, frontier_rows   # noqa: E402

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/block_swap115.json")


def sites(x, y, L, k):
    """The pose as a k x k site lattice: (i, j) -> cell index."""
    pitch = L / k
    x0 = float(x.min()) - 0.5
    y0 = float(y.min()) - 0.5
    out = {}
    for idx in range(len(x)):
        i = int(round((float(x[idx]) - 0.5 - x0) / pitch))
        j = int(round((float(y[idx]) - 0.5 - y0) / pitch))
        out.setdefault((i, j), idx)
    return out, pitch


def boxes(S, k, lo=3, hi=7, max_holes=3, min_cells=4):
    """Near-full p x q blocks: the only ones a substitution can gain a cell in.

    A full block (h = 0) can never take one more cell (area), and a mostly empty
    block is degenerate - replacing one lonely cell proves nothing.  The move
    only means something when the block is nearly full and has a hole or two to
    spend, so those are the blocks enumerated.
    """
    out = []
    for p in range(lo, hi + 1):
        for q in range(p, hi + 1):
            for a in range(-p + 1, k):
                for b in range(-q + 1, k):
                    idx = [S[(a + i, b + j)] for i in range(p) for j in range(q)
                           if (a + i, b + j) in S]
                    h = p * q - len(idx)
                    if not (1 <= h <= max_holes) or len(idx) < min_cells:
                        continue
                    out.append({"p": p, "q": q, "a": a, "b": b,
                                "c": len(idx), "h": h, "cells": idx})
    return out


def pack_box(c, W, H, restarts=4, iters=900, seed=115):
    """Largest-side packing of c unit cells in a W x H box (hinge, multi-restart)."""
    from scipy.optimize import minimize
    rng = np.random.RandomState(seed)
    best = None
    n = c
    for r in range(restarts):
        if r == 0:
            m = int(math.ceil(math.sqrt(n)))
            xs, ys = [], []
            for t in range(n):
                xs.append((t % m + 0.5) * W / m)
                ys.append((t // m + 0.5) * H / m)
            z0 = np.concatenate([np.array(xs), np.array(ys),
                                 np.zeros(n)])
        else:
            z0 = np.concatenate([rng.uniform(0.5, W - 0.5, n),
                                 rng.uniform(0.5, H - 0.5, n),
                                 rng.uniform(0, math.pi / 2, n)])
        ix, iy = np.triu_indices(n, k=1)

        def obj(z):
            X, Y, T = z[:n], z[n:2 * n], z[2 * n:]
            pen = pen_vec(X[ix], Y[ix], T[ix], X[iy], Y[iy], T[iy], eps=1e-9)
            hx = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
            over = (np.clip(X + hx - W, 0, None) ** 2 + np.clip(-X + hx, 0, None) ** 2
                    + np.clip(Y + hx - H, 0, None) ** 2 + np.clip(-Y + hx, 0, None) ** 2)
            return float((pen ** 2).sum() + 1e4 * over.sum())

        res = minimize(obj, z0, method="L-BFGS-B",
                       options={"maxiter": iters, "ftol": 1e-18, "gtol": 1e-14})
        val = obj(res.x)
        if best is None or val < best[0]:
            best = (val, res.x)
        if val < 1e-14:
            break
    return best


def run(grid=100, angles=17, verbose=True):
    per = SQ.load()
    tab = json.load(open(TAB))
    res = []
    for k, m in frontier_rows(per):
        if k < 21:                     # the compressed-lattice regime
            continue
        x, y, t = load_pose(m)
        L = SQ.extent(per[m])
        S, pitch = sites(x, y, L, k)
        cands = boxes(S, k)
        for b in cands:
            W = (b["q"] - 1) * pitch + 1.0
            H = (b["p"] - 1) * pitch + 1.0
            b["T"] = min(W, H)
            b["n_new"] = b["c"] + 1
            b["L_best"] = SQ.extent(per[b["n_new"]])
            b["shortfall"] = b["L_best"] - b["T"]
        if not cands:
            continue
        cands.sort(key=lambda b: b["shortfall"])
        best = cands[0]
        rec = {"k": k, "frontier_n": m, "L": L, "pitch": pitch,
               "blocks": len(cands),
               "negatives": sum(1 for b in cands if b["shortfall"] <= 0),
               "best": {kk: best[kk] for kk in ("p", "q", "a", "b", "c", "h",
                                                "T", "n_new", "L_best", "shortfall")}}
        if verbose:
            print(f"  k={k:2d} n={m:4d} L={L:.9f}  blocks {len(cands):5d}  "
                  f"fit-now {rec['negatives']:4d}  best: {best['p']}x{best['q']} "
                  f"block, c={best['c']} cells ({best['h']} holes) -> c+1="
                  f"{best['n_new']} in {best['T']:.6f}: record "
                  f"{best['L_best']:.6f}  shortfall {best['shortfall']:+.6f}", flush=True)
        res.append(rec)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")
    return res


def attempt(k, m, box, iters=1500):
    """Pack the block, splice it, and judge the whole pose at 40 digits."""
    per = SQ.load()
    tab = json.load(open(TAB))
    x, y, t = load_pose(m)
    L = SQ.extent(per[m])
    S, pitch = sites(x, y, L, k)
    p, q, a, b = box["p"], box["q"], box["a"], box["b"]
    W = (q - 1) * pitch + 1.0
    H = (p - 1) * pitch + 1.0
    val, z = pack_box(box["c"] + 1, W, H, iters=iters)
    rec = {"k": k, "frontier_n": m, "box": [p, q, a, b], "c_plus_1": box["c"] + 1,
           "T": min(W, H), "pen": float(val), "legal_box_packing": bool(val < 1e-12)}
    if not rec["legal_box_packing"]:
        return rec
    # splice: drop the block's cells, insert the new ones at the same origin
    keep = [i for i in range(len(x)) if i not in set(box["cells"])]
    xlo = min(float(x[i]) - 0.5 for i in box["cells"])
    ylo = min(float(y[i]) - 0.5 for i in box["cells"])
    rows = [(str(float(x[i])), str(float(y[i])), str(float(t[i]))) for i in keep]
    nn = box["c"] + 1
    for i in range(nn):
        rows.append((str(float(xlo + z[i])), str(float(ylo + z[nn + i])),
                     str(float(z[2 * nn + i]))))
    chk = TG.check(rows)
    rec["spliced_n"] = len(rows)
    rec["side"] = str(+chk["side"])
    rec["violations"] = len(chk["violations"])
    rec["beat"] = bool(len(chk["violations"]) == 0 and chk["side"] < SQ.grid(len(rows)))
    return rec


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--attempt":
        per = SQ.load()
        fr = dict(frontier_rows(per))
        out = []
        for a in args[1:]:
            k = int(a)
            recs = [r for r in json.load(open(OUT)) if r["k"] == k]
            if not recs:
                continue
            rec = attempt(k, fr[k], {**recs[0]["best"], "cells": []})
            print(json.dumps(rec, indent=1))
            out.append(rec)
        json.dump(out, open(os.path.join(ROOT, "workspace/push/block_swap115_attempt.json"), "w"), indent=1)
    else:
        run()
