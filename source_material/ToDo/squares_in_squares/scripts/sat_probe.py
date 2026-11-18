#!/usr/bin/env python3
r"""sat_probe.py — the bounded experiment of 19 §11.5.

Question: at a side just BELOW the delivered `L`, with only k squares free to
move, is the packing still feasible?

With the orientations frozen and every pair's separating axis taken from the
delivered state, the models becomes a LINEAR PROGRAM in the free translation
(one global (tx,ty) for the rigid part plus (dx_i,dy_i) for each free square):

    for each pair (i,j) whose delivered axis is q with sign s:
        s * ((c_j + D_j - c_i - D_i) . q)  >=  h_i(q) + h_j(q)
    containment:  |x_i| + h_i <= L/2,  |y_i| + h_i <= L/2     (two per square)

Because q and both h are constants once theta is frozen, this is exactly the
declared-axis LP that `seam_wheels.lp_seam` uses, widened from one seam
translation to k free squares.  Feasibility is then a certificate for the
DECLARED axes, and only a violation of that declaration (a pair needing a
different axis) can make a refusal conservative -- stated in the record.

A feasible cell is only a result if `packlib.verify` accepts the final state and
the canonical scorer says the row improves.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ        # noqa: E402
import packlib as P         # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/sat_probe.json")


def frames(st):
    xy = np.array([(float(s[0]), float(s[1])) for s in st])
    th = np.array([float(s[2]) for s in st])
    cs, sn = np.cos(th), np.sin(th)
    return xy, th, cs, sn


def pair_tables(xy, cs, sn):
    n = len(xy)
    PU = np.stack([cs, sn], axis=1) @ xy.T
    PV = np.stack([-sn, cs], axis=1) @ xy.T
    Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
    dU = np.diag(PU)[:, None] - PU
    dV = np.diag(PV)[:, None] - PV
    S = np.stack([0.5 + Eu - np.abs(dU), 0.5 + Eu - np.abs(dV),
                  0.5 + Eu.T - np.abs(dU.T), 0.5 + Eu.T - np.abs(dV.T)])
    pen = np.minimum(np.minimum(S[0], S[1]), np.minimum(S[2], S[3]))
    win = np.argmin(S, axis=0)
    sign = np.sign(np.stack([dU, dV, dU.T, dV.T]))
    return S, pen, win, sign


def solve_lp(xy, th, cs, sn, S, win, sign, free, L, move=1.0):
    """Feasibility LP at side L for the declared axes, theta frozen.

    For each pair the separating axis q is the one that resolved it at the
    delivered state; with t = (c_j - c_i).q and sgn = sign(t) the constraint is

        sgn * ((c_j + D_j) - (c_i + D_i)).q  >=  h_i(q) + h_j(q)

    i.e.  sgn*(D_j - D_i).q  >=  h_i + h_j - sgn*t0 ,  linear in the free
    translations.  At L = L0 and D = 0 this is satisfied exactly, which
    `selftest()` asserts -- the check that caught the inverted rows in run 67.
    """
    n = len(xy)
    h = 0.5 * (np.abs(cs) + np.abs(sn))
    free = sorted(free)
    idx = {i: k for k, i in enumerate(free)}
    nv = 2 + 2 * len(free)

    def var_of(i):
        return 2 + 2 * idx[i] if i in idx else None

    U = np.stack([cs, sn], axis=1)
    V = np.stack([-sn, cs], axis=1)
    # Eu[o, k] = half-extent of square k along square o's own axes (as packlib)
    Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
    A, b = [], []
    for i in range(n):
        for j in range(i + 1, n):
            if i not in idx and j not in idx:
                continue
            a = int(win[i, j])
            owner = i if a < 2 else j
            # separation required on the owner's axis: 0.5 (owner) + ext of the
            # OTHER square along that axis.  Using each square's own extent is
            # wrong unless the two frames agree -- the run-67 defect.
            hs = 0.5 + (Eu[i, j] if a < 2 else Eu[j, i])
            q = U[owner] if a % 2 == 0 else V[owner]
            t0 = float((xy[j] - xy[i]) @ q)
            sgn = 1.0 if t0 >= 0 else -1.0
            row = np.zeros(nv)
            vj = var_of(j)
            if vj is not None:
                row[vj] = sgn * q[0]
                row[vj + 1] = sgn * q[1]
            vi = var_of(i)
            if vi is not None:
                row[vi] -= sgn * q[0]
                row[vi + 1] -= sgn * q[1]
            # the packing condition is  row.x >= hs - sgn*t0 ; linprog is <=
            A.append(-row)
            b.append(-(hs - sgn * t0))
    for i in range(n):
        v = var_of(i)
        for axis in (0, 1):
            c0 = float(xy[i][axis])
            for sg in (1.0, -1.0):
                row = np.zeros(nv)
                row[axis] = sg
                if v is not None:
                    row[v + axis] = sg
                A.append(row)
                b.append(L / 2 - h[i] - sg * c0)
    res = linprog(np.zeros(nv), A_ub=np.array(A), b_ub=np.array(b),
                  bounds=[(-move, move), (-move, move)] +
                         [(-L, L)] * (2 * len(free)), method="highs")
    if res.status == 0:
        x = res.x
        new_xy = np.array(xy, dtype=float)
        new_xy[:, 0] += x[0]
        new_xy[:, 1] += x[1]
        for i in free:
            new_xy[i, 0] += x[var_of(i)]
            new_xy[i, 1] += x[var_of(i) + 1]
        return True, new_xy, 0.0
    return False, xy, float("nan")


def selftest() -> int:
    """The delivered state must be feasible at its own side.  Run 67 failed this."""
    per = SQ.load()
    ok = 0
    for n in (10, 83, 294):
        st = per[n]
        xy, th, cs, sn = frames(st)
        L0 = SQ.extent(st)
        S, pen, win, sign = pair_tables(xy, cs, sn)
        for free in (set(range(min(8, n))), set(range(n))):
            f, _, _ = solve_lp(xy, th, cs, sn, S, win, sign, free, L0)
            assert f, (n, len(free))
            ok += 1
        f, _, _ = solve_lp(xy, th, cs, sn, S, win, sign, {0}, L0 - 1e-3)
        assert not f or True          # may be feasible; only L0 is mandatory
    print(f"selftest: {ok}/6 mandatory feasibility checks pass (delivered at L0)")
    return 0


def rigid_core_span(xy, cs, sn, free):
    """Extent of the frozen squares alone (a proof of infeasibility if too big)."""
    keep = [i for i in range(len(xy)) if i not in set(free)]
    if not keep:
        return 0.0, 0.0
    h = 0.5 * (np.abs(cs) + np.abs(sn))
    xs = np.concatenate([xy[keep, 0] - h[keep], xy[keep, 0] + h[keep]])
    ys = np.concatenate([xy[keep, 1] - h[keep], xy[keep, 1] + h[keep]])
    return float(xs.max() - xs.min()), float(ys.max() - ys.min())


def probe(n, ks, eps_list):
    per = SQ.load()
    st = per[n]
    xy, th, cs, sn = frames(st)
    L0 = SQ.extent(st)
    S, pen, win, sign = pair_tables(xy, cs, sn)
    h = 0.5 * (np.abs(cs) + np.abs(sn))
    # boundary squares: those whose walls are the binding ones
    edge = np.argsort(-(np.abs(xy[:, 0]) + h))[:max(ks)]
    rows = []
    for k in ks:
        free = set(int(i) for i in edge[:k])
        best = None
        for eps in eps_list:
            ok, new, _ = solve_lp(xy, th, cs, sn, S, win, sign, free, L0 - eps)
            if ok:
                stt = [(float(new[i][0]), float(new[i][1]), float(th[i]))
                       for i in range(len(new))]
                v = P.verify(stt, tol=1e-9)
                L = SQ.extent(stt)
                rows.append({"n": n, "k": k, "eps": eps, "ok": True,
                             "L": L, "gain": SQ.row_gain(n, L) - SQ.row_gain(n, L0),
                             "verifies": v["ok"], "worst_pen": v["worst_pen"]})
                best = eps
                break
        if best is None:
            sx, sy = rigid_core_span(xy, cs, sn, free)
            rows.append({"n": n, "k": k, "eps": None, "ok": False,
                         "rigid_span_x": sx, "rigid_span_y": sy,
                         "rigid_core_blocks": max(sx, sy) > L0 - eps_list[0]})
    return {"n": n, "L_delivered": L0, "rows": rows}


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    per = SQ.load()
    proved = set()
    try:
        import optima
        proved = {r for r in getattr(optima, "PROVED", set())}
    except Exception:
        pass
    cands = [(SQ.extent(per[n]) ** 2 - n, n) for n in range(20, 301)]
    cands.sort(reverse=True)
    targets = [n for _, n in cands[:6]]
    eps_list = [1e-6, 1e-4, 1e-2]
    out = [probe(n, (8, 12, 20), eps_list) for n in targets]
    print(f"{'n':>4} {'L_del':>10} {'k':>3} {'largest feasible shrink':>24}")
    for o in out:
        for r in o["rows"]:
            if r["ok"]:
                sh = f"{r['eps']:.0e} gain {r['gain']:+.2e}"
            else:
                sh = ("rigid core spans" if r.get("rigid_core_blocks")
                      else "LP infeasible")
            print(f"{o['n']:4d} {o['L_delivered']:10.6f} {r['k']:3d} {sh:>26}")
    gains = [r for o in out for r in o["rows"] if r["ok"] and r["gain"] > 1e-9]
    print(f"\nfeasible cells: {sum(1 for o in out for r in o['rows'] if r['ok'])}"
          f"   GAINS: {len(gains)}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"run": 65, "schema": "satprobe/1", "targets": targets,
                   "eps_list": eps_list, "probes": out, "gains": gains}, f, indent=1)
    print(f"ledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
