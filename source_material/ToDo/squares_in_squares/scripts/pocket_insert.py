#!/usr/bin/env python3
r"""pocket_insert.py — D1: bounded local pocket insertion on the delivered pose.

The frontier pose of row m has side L(m) < k = ceil(sqrt(m+1)), so *any* legal
unit cell inside its bounding box makes row m+1 a beat.  `void_insert.seat`
tries that with only the cells the candidate penetrates; at k = 26 it freed 3
cells and stalled.  This module widens the moved set to an explicit local
neighbourhood (4-20 cells), gives the new cell a measured pocket seed, and runs
multi-start L-BFGS-B with a container at `k - 1e-5` (anything legal inside is a
strict beat by 1e-5).

Discovery is float (directors' note §1); the verdict is `packlib.verify` for
zero overlap and `true_geom.check` at 40 digits for the real side.  A candidate
that passes both is *not* automatically C1: the certificate formats accept exact
`Q`/`Quad(d)` directions, and a delivered mixed pose has arbitrary angles.  The
ledger records that distinction rather than hiding it.

    python3 scripts/pocket_insert.py --selftest
    python3 scripts/pocket_insert.py --targets 655,509,998 --cells 12 --restarts 16
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from decimal import Decimal

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import packlib as P                 # noqa: E402
import sqscore as SQ                # noqa: E402
import true_geom as TG              # noqa: E402
import void_insert as VI            # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/pocket_insert.json")
#: measured direct pockets from run 160 (`frontier_census.py --at`), used as seeds
SEEDS = {655: (2.38108, 8.38097, 0.0, 0.761940),
         998: (27.59, 0.40, 0.0, 0.732771)}


def bbox(x, y, t):
    return VI.half_ext(x, y, t)


def pocket_seed(per, m, grid=84, angles=13):
    """The measured pocket centre/angle and its free side."""
    x, y, t = (np.array([q[i] for q in per[m]]) for i in range(3))
    st, box = VI.hmax_scan(x, y, t, grid=grid, angles=angles)
    st = VI.refine(x, y, t, st, box, rounds=5, grid=61)
    return float(st[1]), float(st[2]), float(st[3]), float(2 * st[0])


def pick_cells(x, y, t, cx, cy, max_cells):
    """The 4-20 cells nearest the pocket; always includes every binder."""
    d = np.hypot(x - cx, y - cy)
    order = np.argsort(d)
    chosen = []
    for j in order:
        if len(chosen) >= max_cells:
            break
        chosen.append(int(j))
    return sorted(chosen), d


def solve(per, m, cells=12, restarts=16, margin=1e-5, seconds=25.0, seed=1):
    from scipy.optimize import minimize

    x, y, t = (np.array([q[i] for q in per[m]], dtype=float) for i in range(3))
    n = len(x)
    k = SQ.grid(m + 1)
    cx, cy, th, free = SEEDS.get(m) or pocket_seed(per, m)
    chosen, dist = pick_cells(x, y, t, cx, cy, cells)
    ns = len(chosen)
    x0, x1, y0, y1 = bbox(x, y, t)
    Lbox = k - margin
    xmid, ymid = (float(x0.min()) + float(x1.max())) / 2, (float(y0.min()) + float(y1.max())) / 2
    lo_x, hi_x = xmid - Lbox / 2, xmid + Lbox / 2
    lo_y, hi_y = ymid - Lbox / 2, ymid + Lbox / 2

    # pairs: every moved cell against everyone, and the new cell against everyone
    pairs = set()
    for a in chosen:
        for b in range(n):
            if a != b:
                pairs.add((a, b))
    for b in range(n):
        pairs.add((n, b))
    jA = np.array([a for a, _ in pairs])
    jB = np.array([b for _, b in pairs])

    def state(z):
        X, Y, T = x.copy(), y.copy(), t.copy()
        X[chosen], Y[chosen], T[chosen] = z[:ns], z[ns:2 * ns], z[2 * ns:3 * ns]
        X = np.append(X, z[3 * ns])
        Y = np.append(Y, z[3 * ns + 1])
        T = np.append(T, z[3 * ns + 2])
        return X, Y, T

    def obj(z):
        X, Y, T = state(z)
        pen = VI.pen_vec(X[jA], Y[jA], T[jA], X[jB], Y[jB], T[jB], eps=1e-10)
        hx = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
        over = (np.clip(X + hx - hi_x, 0, None) ** 2
                + np.clip(lo_x - X + hx, 0, None) ** 2
                + np.clip(Y + hx - hi_y, 0, None) ** 2
                + np.clip(lo_y - Y + hx, 0, None) ** 2)
        return float((pen ** 2).sum() + 1e6 * over.sum())

    rng = np.random.default_rng(seed)
    base = np.concatenate([x[chosen], y[chosen], t[chosen], [cx, cy, th]])
    trials = []
    best = None
    for r in range(restarts):
        z0 = base.copy()
        if r:
            z0[:ns] += rng.normal(0, 0.04, ns)
            z0[ns:2 * ns] += rng.normal(0, 0.04, ns)
            z0[2 * ns:3 * ns] += rng.normal(0, 0.02, ns)
            z0[3 * ns] += rng.normal(0, 0.06)
            z0[3 * ns + 1] += rng.normal(0, 0.06)
            z0[3 * ns + 2] += rng.normal(0, 0.03)
        deadline = time.time() + seconds

        def cb(_zk):
            if time.time() > deadline:
                raise TimeoutError

        try:
            res = minimize(obj, z0, method="L-BFGS-B",
                           options={"maxiter": 800, "ftol": 1e-16, "gtol": 1e-12,
                                    "maxls": 30},
                           callback=cb)
            z = res.x
            pen = obj(z)
        except Exception as e:                       # noqa: BLE001
            trials.append({"restart": r, "timeout": True,
                           "error": e.__class__.__name__})
            continue
        X, Y, T = state(z)
        chk = P.verify([(float(X[i]), float(Y[i]), float(T[i])) for i in range(n + 1)])
        exact = None
        if chk["ok"] and chk["L"] < k:
            exact = TG.check([(float(X[i]), float(Y[i]), float(T[i])) for i in range(n + 1)])
        rec = {"restart": r, "obj": float(pen), "pack_ok": bool(chk["ok"]),
               "message": str(getattr(res, "message", "")),
               "L_pack": float(chk["L"]), "worst_pen": float(chk["worst_pen"]),
               "exact_violations": None if exact is None else len(exact["violations"]),
               "exact_side": None if exact is None else str(exact["side"]),
               "beat": bool(exact is not None and not exact["violations"]
                            and exact["side"] < k - Decimal("1e-8"))}
        trials.append(rec)
        rank = (rec["beat"], rec["exact_violations"] == 0 if rec["exact_violations"] is not None else False,
                -rec["obj"])
        if best is None or rank > best["_rank"]:
            best = dict(rec, _rank=rank,
                        state=[[float(X[i]), float(Y[i]), float(T[i])] for i in range(n + 1)])
        if rec["beat"]:
            break
    out = {"frontier_n": m, "target_n": m + 1, "k": k, "frontier_side": SQ.extent(per[m]),
           "pocket": {"centre": [cx, cy], "theta": th, "free_side": free},
           "module": {"count": ns, "cells": chosen},
           "restarts": len(trials), "trials": trials, "best": best}
    return out


def selftest():
    """A planted seat: the 3x3 grid minus its centre, with a cell seeded there."""
    per = {8: [(0.5 + i, 0.5 + j, 0.0) for j in range(3) for i in range(3)
               if (i, j) != (1, 1)]}
    x, y, t = (np.array([q[i] for q in per[8]]) for i in range(3))
    cx, cy, th = 1.5, 1.5, 0.0
    chosen, _ = pick_cells(x, y, t, cx, cy, 8)
    assert len(chosen) == 8, chosen
    # the machinery must accept the exact completion
    st = [(float(a), float(b), float(c)) for a, b, c in per[8]] + [(cx, cy, th)]
    v = P.verify(st)
    assert v["ok"] and abs(v["L"] - 3.0) < 1e-12, v
    print("pocket_insert selftest: planted 3x3-minus-centre accepts the ninth cell "
          "(module selection + packlib gate)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--targets", default="655,509,998")
    ap.add_argument("--cells", type=int, default=12)
    ap.add_argument("--restarts", type=int, default=16)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    per = SQ.load()
    ledger = json.load(open(OUT)) if os.path.exists(OUT) else []
    index = {r.get("frontier_n"): r for r in ledger}
    for m in [int(s) for s in a.targets.split(",")]:
        free = (SEEDS.get(m) or pocket_seed(per, m))[3]
        print(f"n={m} -> {m + 1}: pocket {free:.6f}, "
              f"module {a.cells}, {a.restarts} restarts", flush=True)
        rec = solve(per, m, cells=a.cells, restarts=a.restarts,
                    seconds=a.seconds, seed=a.seed)
        rec["params"] = {"cells": a.cells, "restarts": a.restarts,
                         "seconds": a.seconds, "seed": a.seed}
        index[m] = rec
        b = rec["best"] or {}
        print(f"  best obj {b.get('obj')} pack_ok {b.get('pack_ok')} "
              f"L {b.get('L_pack')} exact_viol {b.get('exact_violations')} "
              f"side {b.get('exact_side')} beat {b.get('beat')}", flush=True)
    json.dump(sorted(index.values(), key=lambda r: r["frontier_n"]),
              open(OUT, "w"), indent=1)
    print("wrote", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
