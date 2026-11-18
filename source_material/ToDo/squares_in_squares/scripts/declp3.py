#!/usr/bin/env python3
r"""declp3.py — the declared-axis LP for unit cubes in a cube (the 3D analogue of declp).

WHAT THIS IS
------------
`declp.py` decides, for a 2D state of unit squares with frozen angles, whether a
*declared* separating axis per pair survives a shrink of the container. This is
the same instrument one dimension up, for the problem the 2D table is a slice of:
n axis-parallel unit cubes in a cube of side L.

    state      centres c_i in R^3, container [-L/2, L/2]^3
    branch     one (axis q, sign s) per pair:  s * (c_j - c_i).e_q >= 1
    variables  a translation d_i in R^3 per cube, and t = L
    objective  minimise t

The LP is a *relaxation*: it enforces only the declared axis of each pair, so the
state it returns may be invalid on the axes it did not declare. Nothing here is a
result on its own — `gate` decides, exactly, and the side it reports is measured
from the state, never taken from the LP's `t`.

THE GATE IS EXACT
-----------------
The 2D gate rounds to 12 dp and calls `packlib.verify(tol=0)`, which is exact up
to float reading of the recorded decimals. This one goes further, because the
problem is small enough: coordinates are rounded to 12 dp and then read as
`Fraction`s, so pairwise separation, penetration and the container side are all
*rational arithmetic on the recorded numbers*. There is no tolerance constant in
the verdict; `worst_pen <= 0` is an exact statement about the state as written.

THE ONE THEOREM
---------------
Two axis-parallel unit cubes in a box of side L < 2 must intersect: in each axis
their intervals have length 1 inside an interval of length < 2, so they overlap
in every axis. Hence L(n) >= 2 for every n >= 2 (`lemma_two`). Combined with the
2x2x2 grid, which puts 8 cubes in L = 2, this pins L(n) = 2 exactly for 2 <= n <= 8.

CONTROLS (`--control`)
----------------------
1. degradation: with z pinned and only x/y declared, this LP must reproduce the
   2D row's own minimum side from `declp.max_shrink` — the 3D instrument has to
   reduce to the 2D one, or it is a different problem.
2. two cubes: all six branches must return 2, and the gate must refuse 1.9999.
3. the gate must refuse a state built to overlap by 0.4, and accept the grid.
"""
from __future__ import annotations

import json
import math
import os
import sys
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import declp as D          # noqa: E402
import sqscore as SQ       # noqa: E402

#: the six declared separations, per pair: (axis, sign)
AXES = ((0, 1.0), (0, -1.0), (1, 1.0), (1, -1.0), (2, 1.0), (2, -1.0))
#: shrink ladder, largest first (the project's convention)
EPS = (1e-2, 3e-3, 1e-3, 1e-4, 1e-6)


# ------------------------------------------------------------------ geometry
def extent3(state) -> float:
    """Container side of a cube state: the max of the three axis extents."""
    a = np.asarray(state, dtype=float)
    lo, hi = a.min(axis=0), a.max(axis=0)
    return float(np.max(hi - lo + 1.0))


def cube_gain(n: int, L: float) -> float:
    """The 3D analogue of `sqscore.row_gain`: L/cuberoot(n) - 1."""
    return L / (n ** (1.0 / 3.0)) - 1.0


def branch_of(state, i: int, j: int):
    """The declared axis for a pair: the one carrying the largest gap."""
    d = np.asarray(state[j], dtype=float) - np.asarray(state[i], dtype=float)
    q = int(np.argmax(np.abs(d)))
    return (q, 1.0 if d[q] >= 0.0 else -1.0)


def full_branch(state):
    """{(i, j): (axis, sign)} for every pair, from the state's own largest gaps."""
    n = len(state)
    return {(i, j): branch_of(state, i, j) for i in range(n) for j in range(i + 1, n)}


# ----------------------------------------------------------------------- gate
def gate(n: int, state, L0: float, tol=Fraction(0)):
    """The exact gate: 12-dp state, rational separation and side, no LP input.

    Returns dict with ok, worst_pen (exact, as float and as a string), L (the
    side measured from the state), gain against L0, and the recorded state.
    """
    arr = np.asarray(state, dtype=float)
    mid = 0.5 * (arr.min(axis=0) + arr.max(axis=0))       # centring is free
    st = [(round(float(c[0]), 12), round(float(c[1]), 12), round(float(c[2]), 12))
          for c in (arr - mid)]
    fr = [[Fraction(str(v)) for v in c] for c in st]
    worst = None
    for i in range(n):
        for j in range(i + 1, n):
            sep = max(abs(fr[j][q] - fr[i][q]) for q in range(3))
            pen = Fraction(1) - sep
            if worst is None or pen > worst:
                worst = pen
    if worst is None:                       # n = 1: nothing to separate
        worst = Fraction(0)
    L = max(max(c[q] for c in fr) - min(c[q] for c in fr) for q in range(3))
    L += Fraction(1)                        # a cube has side 1
    ok = worst <= tol
    return {"ok": bool(ok), "worst_pen": float(worst),
            "worst_pen_exact": str(worst), "L": float(L),
            "gain": cube_gain(n, float(L)) - cube_gain(n, L0),
            "fits": float(L) <= L0 + 1e-12,
            "state": st if ok else None}


# ------------------------------------------------------------------------- LP
def solve(state, branch, free_axes=(0, 1, 2), move=2.0, tmin=1.0):
    """Minimum side t for the declared axes; returns (t, new_state) or (None, None).

    `free_axes` pins the other coordinates at zero — that is how the degradation
    control reduces this to the 2D instrument.
    """
    st = np.asarray(state, dtype=float)
    st = st - 0.5 * (st.min(axis=0) + st.max(axis=0))    # the model is translation-free
    n = len(st)
    nv = 3 * n + 1
    A, b = [], []
    for (i, j), (q, s) in branch.items():
        s = float(s)
        dc = float(st[j][q] - st[i][q])
        need = 1.0 - s * dc
        row = np.zeros(nv)
        row[3 * j + q] += -s
        row[3 * i + q] += s
        A.append(row)
        b.append(-need)
    for i in range(n):
        for q in range(3):
            c = float(st[i][q])
            lo = np.zeros(nv)
            lo[3 * i + q] = 1.0
            lo[3 * n] = -0.5
            A.append(lo)
            b.append(-0.5 - c)          # c + d + 1/2 <= t/2  <=>  d - t/2 <= -1/2 - c
            hi = np.zeros(nv)
            hi[3 * i + q] = -1.0
            hi[3 * n] = -0.5
            A.append(hi)
            b.append(-0.5 + c)          # -(c + d) + 1/2 <= t/2  <=>  -d - t/2 <= c - 1/2
    bounds = []
    for i in range(n):
        for q in range(3):
            if q in free_axes:
                bounds.append((-move, move))
            else:
                bounds.append((0.0, 0.0))
    bounds.append((tmin, None))
    obj = np.zeros(nv)
    obj[3 * n] = 1.0
    res = linprog(obj, A_ub=np.array(A), b_ub=np.array(b), bounds=bounds,
                  method="highs")
    if res.status != 0:
        return None, None
    x = res.x
    new = st + x[:3 * n].reshape(n, 3)
    return float(x[3 * n]), new


def min_side(state, branch=None, **kw):
    """(t, state) for the state's own branch, or the declared one."""
    return solve(state, branch or full_branch(state), **kw)


# ---------------------------------------------------------------- descent
def descend(state, L0, rounds=6, tol=1e-9, **kw):
    """Declared-axis descent: LP proposes, the exact gate decides, repeat.

    Each accepted step is a gated state at a strictly smaller side. Returns
    (state, L, trace) where trace records every proposal and its verdict.
    """
    cur = [tuple(map(float, c)) for c in state]
    L = extent3(cur)
    trace = []
    for _ in range(rounds):
        t, new = min_side(cur, **kw)
        if new is None:
            trace.append({"t": None, "gate_ok": False, "note": "LP infeasible"})
            break
        g = gate(len(cur), new, L0)
        rec = {"t": t, "gate_ok": g["ok"], "L": g["L"], "worst_pen": g["worst_pen"]}
        trace.append(rec)
        if g["ok"] and g["L"] < L - tol:
            cur, L = [tuple(c) for c in g["state"]], g["L"]
        else:
            break
    return cur, L, trace


# ----------------------------------------------------------- constructions
def grid3(n: int):
    """The most balanced kx*ky*kz >= n box of unit cubes, filled in order."""
    k = 1
    while True:
        cands = [(a + b + c, (a, b, c))
                 for a in range(1, k + 1) for b in range(1, k + 1)
                 for c in range(1, k + 1)
                 if a * b * c >= n and max(a, b, c) == k]
        if cands:
            _, (kx, ky, kz) = min(cands)
            break
        k += 1
    state, placed = [], 0
    for z in range(kz):
        for y in range(ky):
            for x in range(kx):
                if placed == n:
                    break
                state.append((x - (kx - 1) / 2.0, y - (ky - 1) / 2.0,
                              z - (kz - 1) / 2.0))
                placed += 1
    while len(state) < n:               # only if kx*ky*kz < n (cannot happen)
        state.append((0.0, 0.0, 0.0))
    return state


def extrude(n: int):
    """The delivered 2D row as a 3D state: same (x, y), z = 0, same container."""
    st = SQ.load()[n]
    L2 = SQ.extent(st)
    xy = np.array([(s[0], s[1]) for s in st], dtype=float)
    xy = xy - 0.5 * (xy.max(axis=0) + xy.min(axis=0))     # centre the container
    return [(float(p[0]), float(p[1]), 0.0) for p in xy], L2


# ------------------------------------------------------------------ lemma
def lemma_two(n: int) -> str:
    """Why L >= 2 whenever n >= 2, and what it pins."""
    return ("in each axis two unit intervals inside [0,L] with L < 2 must overlap, "
            "so two cubes in a box of side L < 2 intersect in all three axes; "
            "hence L(n) >= 2 for n >= 2, and the 2x2x2 grid gives L = 2 for n <= 8")


# ------------------------------------------------------------------ controls
def control() -> int:
    per = SQ.load()
    print("control 1 — degradation: z pinned, x/y declared, must match declp")
    print("  (axis-aligned rows only: a unit cube is a unit square only there)")
    aligned = [n for n in sorted(per) if all(abs(float(s[2])) < 1e-15 for s in per[n])]
    for n in (aligned[3], aligned[8], aligned[15], aligned[24]):
        st = per[n]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        z = np.zeros((n, 3))
        z[:, 0], z[:, 1] = xy[:, 0], xy[:, 1]
        br = {k: v for k, v in full_branch(z).items() if v[0] in (0, 1)}
        t3, _ = solve(z, br, free_axes=(0, 1), move=0.6)
        # the 2D reference: bisect declp.solve's own feasibility, wide window
        lo, hi = 1e-9, 0.6
        assert D.solve(xy, th, L0 - lo, move=0.6, free_span=2.0) is not None, n
        if D.solve(xy, th, L0 - hi, move=0.6, free_span=2.0) is not None:
            lo = hi
        else:
            for _ in range(40):
                mid = 0.5 * (lo + hi)
                if D.solve(xy, th, L0 - mid, move=0.6, free_span=2.0) is not None:
                    lo = mid
                else:
                    hi = mid
        assert t3 is not None, n
        assert abs(t3 - (L0 - lo)) < 1e-6, (n, t3, L0 - lo)
        print(f"  n={n:4d}  3D-with-z-pinned {t3:.9f}   2D declp {L0 - lo:.9f}"
              f"   diff {t3 - (L0 - lo):+.2e}")

    print("control 2 — two cubes: every branch returns 2, the gate refuses 1.9999")
    two = [(-0.5, 0.0, 0.0), (0.5, 0.0, 0.0)]
    for (q, s) in AXES:
        t, _ = solve(two, {(0, 1): (q, s)}, tmin=0.5)
        assert t is not None and abs(t - 2.0) < 1e-9, (q, s, t)
    print("  all six declared axes give t = 2 exactly")
    g = gate(2, two, 2.0)
    assert g["ok"] and abs(g["L"] - 2.0) < 1e-12, g
    bad = [(-0.5, 0.0, 0.0), (0.4999, 0.0, 0.0)]     # 0.9999 apart: 1e-4 overlap
    gb = gate(2, bad, 2.0)
    assert not gb["ok"] and abs(gb["worst_pen"] - 1e-4) < 1e-12, gb
    print(f"  gate: 2 cubes at L=2 ok ({g['worst_pen_exact']}); "
          f"0.9999 apart refused (pen {gb['worst_pen_exact']} = 1e-4)")

    print("control 3 — the gate refuses a deliberate 0.4 overlap, accepts the grid")
    ov = [(0.0, 0.0, 0.0), (0.6, 0.0, 0.0), (0.0, 1.5, 0.0)]
    go = gate(3, ov, 3.0)
    assert not go["ok"] and abs(go["worst_pen"] - 0.4) < 1e-12, go
    gg = gate(3, grid3(3), 2.0)
    assert gg["ok"] and abs(gg["L"] - 2.0) < 1e-12, gg
    for n, want in ((8, 2.0), (9, 3.0), (16, 3.0), (27, 3.0), (28, 4.0)):
        g2 = gate(n, grid3(n), want)
        assert g2["ok"] and abs(g2["L"] - want) < 1e-12, (n, g2["L"], want)
    print(f"  overlap refused (pen {go['worst_pen_exact']} = 2/5); grid3 knowns "
          "8->2, 9/16/27->3, 28->4 all gated")
    print("control: OK")
    return 0


# ---------------------------------------------------------------- exhaustive
def exhaustive(n: int, limit=None):
    """Min over all declared branch structures of the LP's optimal side.

    A valid lower bound on L(n): the optimum has *some* branch, the LP relaxes
    the rest, and we take the minimum over every branch. Exponential — n <= 4.
    """
    import itertools
    st = [(0.0, 0.0, 0.0)] * n
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    best, count, best_br = None, 0, None
    for combo in itertools.product(AXES, repeat=len(pairs)):
        br = dict(zip(pairs, combo))
        t, _ = solve(st, br, tmin=0.5)
        count += 1
        if t is not None and (best is None or t < best):
            best, best_br = t, br
        if limit and count >= limit:
            break
    return best, count, best_br


# ---------------------------------------------------------------------- run
def run(ns, ledger=None, do_exh=True):
    out = {"lemma": lemma_two(2), "rows": []}
    print(f"{'n':>3} {'algn':>4} {'L2 2D':>7} {'extr':>7} {'grid3':>6} "
          f"{'desc(extr)':>10} {'desc(grid)':>10}  verdict")
    for n in ns:
        st2 = SQ.load()[n]
        aligned = all(abs(float(s[2])) < 1e-15 for s in st2)
        ext, L2 = extrude(n)
        g_ext = gate(n, ext, L2)
        e_state, e_L, e_trace = descend(ext, L2)
        gd = grid3(n)
        g_g = gate(n, gd, extent3(gd))
        g_state, g_L, g_trace = descend(gd, extent3(gd))
        if g_L < L2 - 1e-6:
            verdict = "3D strictly better"
        elif abs(g_L - L2) <= 1e-6:
            verdict = "tie: extrusion is optimal here"
        else:
            verdict = "extrusion better (grid not optimal)"
        print(f"{n:3d} {str(aligned):>4} {L2:7.4f} {g_ext['L']:7.4f} {g_g['L']:6.4f} "
              f"{e_L:10.4f} {g_L:10.4f}  {verdict}")
        out["rows"].append({
            "n": n, "row2d_aligned": aligned, "L2": L2,
            "extrude_ok": g_ext["ok"], "extrude_L": g_ext["L"],
            "grid_L": g_g["L"], "grid_ok": g_g["ok"],
            "descend_extrude_L": e_L, "descend_grid_L": g_L,
            "descend_extrude": e_trace, "descend_grid": g_trace,
            "verdict": verdict})
    if do_exh:
        print("\nexhaustive branch lower bounds (all 6^C(n,2) structures)")
        ex = {}
        for n in (2, 3, 4):
            lo, cnt, _ = exhaustive(n, limit=60000)
            ex[n] = {"lb": lo, "branches": cnt}
            print(f"  n={n}: {cnt:6d} branches, best LP side {lo:.6f}")
        out["exhaustive"] = {str(k): v for k, v in ex.items()}
    if ledger:
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nledger -> {os.path.relpath(ledger, os.path.dirname(os.path.dirname(HERE)))}")
    return 0


def main() -> int:
    if "--control" in sys.argv:
        return control()
    if "--exhaustive" in sys.argv:
        n = int(sys.argv[sys.argv.index("--exhaustive") + 1])
        lo, cnt, br = exhaustive(n, limit=int(sys.argv[sys.argv.index("--exhaustive") + 2])
                                 if len(sys.argv) > sys.argv.index("--exhaustive") + 2 else None)
        print(f"n={n}: {cnt} branches, best LP side {lo}")
        return 0
    ledger = os.path.join(os.path.dirname(HERE), "workspace/push/declp3.json")
    ns = [int(v) for v in sys.argv[1:]] if len(sys.argv) > 1 else \
        [2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 20]
    return run(ns, ledger=ledger)


if __name__ == "__main__":
    raise SystemExit(main())
