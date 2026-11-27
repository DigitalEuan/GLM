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
zero overlap and `true_geom.check` at 40 digits for the real side.  A pack-legal
candidate is then handed to `snap_certify`: every angle is snapped to the exact
rational spinor `t = sin/(1+cos)` and every centre to a rational, and the pose
is adjudicated by the exact `field: "Q"` certificate.  That route needs no
0°/45° `Quad(d)` word; `snap_certify --selftest` control 9 is its mixed-angle
positive control.  No candidate in this run reached that step.

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


def _pair_terms(ax, ay, at, bx, by, bt, eps=1e-10):
    """Penetration and its analytic gradient for a batch of pairs.

    The SAT penetration is `max(0, eps - max_k slack_k)`.  For the active axis k the
    derivative is exact away from axis ties: translations use `sign(proj) * q`, and the
    angle terms use the support's derivative, including `q'(theta)` when the axis belongs
    to that cell.  This is discovery arithmetic (float); the exact gate is still
    `packlib`/`true_geom`.
    """
    ax, ay, at, bx, by, bt = (np.asarray(v, dtype=float)
                              for v in (ax, ay, at, bx, by, bt))
    zero = np.zeros_like(ax)
    ca, sa = np.cos(at), np.sin(at)
    cb, sb = np.cos(bt), np.sin(bt)
    # qx, qy, dq/dta, dq/dtb -- only the owner's angle moves its own axes
    axes = [
        (ca, sa, -sa, ca, zero, zero),
        (-sa, ca, -ca, -sa, zero, zero),
        (cb, sb, zero, zero, -sb, cb),
        (-sb, cb, zero, zero, -cb, -sb),
    ]
    best = []
    deriv = []
    for qx, qy, dqx_a, dqy_a, dqx_b, dqy_b in axes:
        # support of each square along q, and its derivative in each angle
        ua, va = ca * qx + sa * qy, -sa * qx + ca * qy
        ub, vb = cb * qx + sb * qy, -sb * qx + cb * qy
        ha = 0.5 * (np.abs(ua) + np.abs(va))
        hb = 0.5 * (np.abs(ub) + np.abs(vb))
        dua_a = -sa * qx + ca * dqx_a + ca * qy + sa * dqy_a
        dva_a = -ca * qx - sa * dqx_a - sa * qy + ca * dqy_a
        dha_a = 0.5 * (np.sign(ua) * dua_a + np.sign(va) * dva_a)
        dua_b = ca * dqx_b + sa * dqy_b
        dva_b = -sa * dqx_b + ca * dqy_b
        dha_b = 0.5 * (np.sign(ua) * dua_b + np.sign(va) * dva_b)
        dub_b = -sb * qx + cb * dqx_b + cb * qy + sb * dqy_b
        dvb_b = -cb * qx - sb * dqx_b - sb * qy + cb * dqy_b
        dhb_b = 0.5 * (np.sign(ub) * dub_b + np.sign(vb) * dvb_b)
        dub_a = cb * dqx_a + sb * dqy_a
        dvb_a = -sb * dqx_a + cb * dqy_a
        dhb_a = 0.5 * (np.sign(ub) * dub_a + np.sign(vb) * dvb_a)
        proj = (ax - bx) * qx + (ay - by) * qy
        best.append(np.abs(proj) - ha - hb)
        sgn = np.sign(proj)
        deriv.append({
            "qx": qx, "qy": qy, "sgn": sgn,
            "dta": sgn * ((ax - bx) * dqx_a + (ay - by) * dqy_a) - dha_a - dhb_a,
            "dtb": sgn * ((ax - bx) * dqx_b + (ay - by) * dqy_b) - dha_b - dhb_b,
        })
    best = np.stack(best)
    k = np.argmax(best, axis=0)
    idx = k[None, :]
    qx = np.take_along_axis(np.stack([d["qx"] for d in deriv]), idx, axis=0)[0]
    qy = np.take_along_axis(np.stack([d["qy"] for d in deriv]), idx, axis=0)[0]
    sgn = np.take_along_axis(np.stack([d["sgn"] for d in deriv]), idx, axis=0)[0]
    dta = np.take_along_axis(np.stack([d["dta"] for d in deriv]), idx, axis=0)[0]
    dtb = np.take_along_axis(np.stack([d["dtb"] for d in deriv]), idx, axis=0)[0]
    best_k = np.take_along_axis(best, idx, axis=0)[0]
    pen = np.clip(eps - best_k, 0.0, None)
    two_p = 2.0 * pen
    return (pen, -two_p * sgn * qx, -two_p * sgn * qy, -two_p * dta,
            two_p * sgn * qx, two_p * sgn * qy, -two_p * dtb, qx, qy, sgn)


def _container_terms(X, Y, T, lo_x, hi_x, lo_y, hi_y, scale=1e6):
    """Box penalty and its gradient (the box is fixed during a restart)."""
    hx = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    dhx = 0.5 * (-np.sin(T) * np.sign(np.cos(T)) + np.cos(T) * np.sign(np.sin(T)))
    right = np.clip(X + hx - hi_x, 0.0, None)
    left = np.clip(lo_x - X + hx, 0.0, None)
    top = np.clip(Y + hx - hi_y, 0.0, None)
    bottom = np.clip(lo_y - Y + hx, 0.0, None)
    val = scale * (right ** 2 + left ** 2 + top ** 2 + bottom ** 2).sum()
    gx = scale * (2.0 * right - 2.0 * left)
    gy = scale * (2.0 * top - 2.0 * bottom)
    gt = scale * 2.0 * (right + left + top + bottom) * dhx
    return float(val), gx, gy, gt


def repair_local(X, Y, T, var, lo_x, hi_x, lo_y, hi_y, iters=320, damping=0.5):
    """Damped Jacobi projection over pairs incident to the moved module.

    Fixed cells never move: their delivered pose is the evidence.  The module and the new
    cell are pushed apart along the active SAT axis and clamped into the box after every
    sweep.  The float result is only a proposal; `packlib.verify` remains the gate.
    """
    n = len(X)
    var = set(var)
    pairs = set()
    for a in var:
        for b in range(n):
            if a != b:
                pairs.add((min(a, b), max(a, b)))
    if not pairs:
        return X, Y, T, 0, 0.0
    ia = np.array([p[0] for p in pairs])
    ib = np.array([p[1] for p in pairs])
    for it in range(1, iters + 1):
        pen, _gax, _gay, _gat, _gbx, _gby, _gbt, qx, qy, sgn = _pair_terms(
            X[ia], Y[ia], T[ia], X[ib], Y[ib], T[ib])
        worst = float(pen.max()) if len(pen) else 0.0
        if worst <= 1e-12:
            return X, Y, T, it, worst
        dX = np.zeros(n)
        dY = np.zeros(n)
        for t in range(len(ia)):
            if pen[t] <= 0:
                continue
            d = damping * float(pen[t])
            i, j = int(ia[t]), int(ib[t])
            if i in var and j in var:
                dX[i] -= sgn[t] * d * qx[t] / 2
                dY[i] -= sgn[t] * d * qy[t] / 2
                dX[j] += sgn[t] * d * qx[t] / 2
                dY[j] += sgn[t] * d * qy[t] / 2
            elif i in var:
                dX[i] -= sgn[t] * d * qx[t]
                dY[i] -= sgn[t] * d * qy[t]
            else:
                dX[j] += sgn[t] * d * qx[t]
                dY[j] += sgn[t] * d * qy[t]
        X, Y = X + dX, Y + dY
        for i in var:
            h = 0.5 * (abs(math.cos(T[i])) + abs(math.sin(T[i])))
            if hi_x - lo_x >= 2 * h:
                X[i] = min(max(X[i], lo_x + h), hi_x - h)
            if hi_y - lo_y >= 2 * h:
                Y[i] = min(max(Y[i], lo_y + h), hi_y - h)
    pen, *_ = _pair_terms(X[ia], Y[ia], T[ia], X[ib], Y[ib], T[ib])
    return X, Y, T, iters, float(pen.max()) if len(pen) else 0.0


def solve(per, m, cells=16, restarts=12, margin=1e-5, seconds=20.0, seed=1):
    from scipy.optimize import minimize

    x, y, t = (np.array([q[i] for q in per[m]], dtype=float) for i in range(3))
    n = len(x)
    k = SQ.grid(m + 1)
    # the insertion is into the frontier pose m, so its own pocket is the seed;
    # the target row m+1 is the row being beaten, not the pose being edited
    cx, cy, th, free = SEEDS.get(m) or pocket_seed(per, m)
    chosen, dist = pick_cells(x, y, t, cx, cy, cells)
    ns = len(chosen)
    x0, x1, y0, y1 = bbox(x, y, t)
    Lbox = k - margin
    xmid, ymid = (float(x0.min()) + float(x1.max())) / 2, (float(y0.min()) + float(y1.max())) / 2
    lo_x, hi_x = xmid - Lbox / 2, xmid + Lbox / 2
    lo_y, hi_y = ymid - Lbox / 2, ymid + Lbox / 2
    # The scan reports the largest square of *any* size; a unit cell may not fit its
    # centre.  Clamp the seed into the container and start it axis-aligned (h = 1/2),
    # so the first objective is overlap-only rather than a six-figure box penalty.
    cx = min(max(cx, lo_x + 0.5), hi_x - 0.5)
    cy = min(max(cy, lo_y + 0.5), hi_y - 0.5)
    th = 0.0

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

    def fg(z):
        X, Y, T = state(z)
        pen, gax, gay, gat, gbx, gby, gbt, _qx, _qy, _sgn = _pair_terms(
            X[jA], Y[jA], T[jA], X[jB], Y[jB], T[jB], eps=1e-10)
        gX = np.zeros(n + 1)
        gY = np.zeros(n + 1)
        gT = np.zeros(n + 1)
        np.add.at(gX, jA, gax)
        np.add.at(gX, jB, gbx)
        np.add.at(gY, jA, gay)
        np.add.at(gY, jB, gby)
        np.add.at(gT, jA, gat)
        np.add.at(gT, jB, gbt)
        cval, cgx, cgy, cgt = _container_terms(X, Y, T, lo_x, hi_x, lo_y, hi_y)
        gX += cgx
        gY += cgy
        gT += cgt
        f = float((pen ** 2).sum() + cval)
        g = np.concatenate([gX[chosen], gY[chosen], gT[chosen],
                            [gX[n], gY[n], gT[n]]])
        return f, g

    def obj(z):
        return fg(z)[0]

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
            res = minimize(fg, z0, method="L-BFGS-B", jac=True,
                           options={"maxiter": 800, "ftol": 1e-16, "gtol": 1e-12,
                                    "maxls": 30},
                           callback=cb)
            z = res.x
            X, Y, T = state(z)
            pre = P.verify([(float(X[i]), float(Y[i]), float(T[i])) for i in range(n + 1)])
            z_pre = z.copy()
            X, Y, T, rit, rres = repair_local(
                X, Y, T, chosen + [n], lo_x, hi_x, lo_y, hi_y)
            z = np.concatenate([X[chosen], Y[chosen], T[chosen],
                                [X[n], Y[n], T[n]]])
            post = P.verify([(float(X[i]), float(Y[i]), float(T[i])) for i in range(n + 1)])
            reverted = False
            if not post["ok"] and (pre["ok"] or pre["worst_pen"] < post["worst_pen"]):
                z = z_pre
                X, Y, T = state(z)
                post = pre
                reverted = True
            pen = obj(z)
        except Exception as e:                       # noqa: BLE001
            trials.append({"restart": r, "timeout": True,
                           "error": e.__class__.__name__})
            continue
        chk = P.verify([(float(X[i]), float(Y[i]), float(T[i])) for i in range(n + 1)])
        exact = None
        if chk["ok"] and chk["L"] < k:
            exact = TG.check([(float(X[i]), float(Y[i]), float(T[i])) for i in range(n + 1)])
        rec = {"restart": r, "obj": float(pen), "pack_ok": bool(chk["ok"]),
               "message": str(getattr(res, "message", "")),
               "pre_worst": float(pre["worst_pen"]), "post_worst": float(post["worst_pen"]),
               "repair_reverted": reverted,
               "repair_iters": rit, "repair_residual": float(rres),
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
    # analytic gradient against central differences (discovery arithmetic only)
    ax = np.array([0.5, 0.5, 0.2])
    ay = np.array([0.5, 0.5, 0.8])
    at = np.array([0.0, 0.5, 0.9])
    bx = np.array([0.65, 0.7, 0.2])
    by = np.array([0.55, 0.6, 0.5])
    bt = np.array([0.3, 0.1, 1.1])
    pen, gax, gay, gat, gbx, gby, gbt, _qx, _qy, _sgn = _pair_terms(
        ax, ay, at, bx, by, bt)
    assert pen.max() > 0, pen
    h = 1e-6
    checks = [(ax, gax), (ay, gay), (at, gat), (bx, gbx), (by, gby), (bt, gbt)]
    for arr, grad in checks:
        for i in range(len(arr)):
            old = arr[i]
            arr[i] = old + h
            fp = float((_pair_terms(ax, ay, at, bx, by, bt)[0] ** 2).sum())
            arr[i] = old - h
            fm = float((_pair_terms(ax, ay, at, bx, by, bt)[0] ** 2).sum())
            arr[i] = old
            fd = (fp - fm) / (2 * h)
            assert abs(fd - grad[i]) < 2e-4 * (1 + abs(fd)), (fd, grad[i])
    cval, cgx, cgy, cgt = _container_terms(
        np.array([0.1, 0.9]), np.array([0.2, 0.8]), np.array([0.0, 0.4]),
        0.0, 1.0, 0.0, 1.0)
    assert cval > 0
    print("pocket_insert selftest: planted 3x3-minus-centre accepts the ninth cell "
          "(module selection + packlib gate), and the analytic pair/box gradient "
          "matches central differences")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--targets", default="655,509,998")
    ap.add_argument("--cells", type=int, default=16)
    ap.add_argument("--restarts", type=int, default=12)
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    per = SQ.load()
    ledger = json.load(open(OUT)) if os.path.exists(OUT) else []
    # keep the 4-cell baseline and the 16-cell module as separate records
    index = {(r.get("frontier_n"), (r.get("params") or {}).get("cells")): r
             for r in ledger}
    for m in [int(s) for s in a.targets.split(",")]:
        free = (SEEDS.get(m) or pocket_seed(per, m))[3]
        print(f"n={m} -> {m + 1}: pocket {free:.6f}, "
              f"module {a.cells}, {a.restarts} restarts", flush=True)
        rec = solve(per, m, cells=a.cells, restarts=a.restarts,
                    seconds=a.seconds, seed=a.seed)
        rec["params"] = {"cells": a.cells, "restarts": a.restarts,
                         "seconds": a.seconds, "seed": a.seed}
        rec["c1"] = ("not reached: no pack-legal candidate; snap_certify's rational-spinor "
                     "Q certificate is the adjudicator")
        index[(m, a.cells)] = rec
        b = rec["best"] or {}
        print(f"  best obj {b.get('obj')} pack_ok {b.get('pack_ok')} "
              f"L {b.get('L_pack')} exact_viol {b.get('exact_violations')} "
              f"side {b.get('exact_side')} beat {b.get('beat')}", flush=True)
    json.dump(sorted(index.values(),
                      key=lambda r: (r["frontier_n"], (r.get("params") or {}).get("cells", 0))),
              open(OUT, "w"), indent=1)
    print("wrote", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
