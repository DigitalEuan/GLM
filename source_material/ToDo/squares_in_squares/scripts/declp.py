#!/usr/bin/env python3
r"""declp.py — the ONE declared-axis LP, shared by sat_probe, branch_rot, t1_glide.

WHY THIS EXISTS (consolidation pass after run 70)
-------------------------------------------------
Three instruments had grown their own copy of the same constraint system:

    sat_probe.solve_lp      run 65, rebuilt at run 67 after three defects
    branch_rot.lp_feasible  run 69
    t1_glide.lp             run 70

They agreed, and they agreed only because someone read all three.  That is how
run 67's defect survived: the LP used `h_i + h_j` (each square's OWN half-extent)
where the separation on the owner's axis requires `0.5 + ext_q(the other
square)`.  A copy that drifts by one term is a wrong certificate that looks
exactly like a right one.  The builder now lives here, once.

THE MODEL (theta frozen, one separating axis declared per pair)
---------------------------------------------------------------
For a pair (i, j) with centres c_i, c_j and a declared branch

    a = 0: u_i     a = 1: v_i     a = 2: u_j     a = 3: v_j

let q be that axis, owner = i for a < 2 else j, and sgn = sign((c_j-c_i).q).  The
pair is separated on q iff

    sgn * ((c_j + D_j) - (c_i + D_i)) . q  >=  0.5 + ext_q(other)  (+ pad)

which is linear in the free translations D.  The half-extent is the OTHER
square's extent along the owner's axis -- never the owner's own (0.5 by
construction).  Containment is |x_i| + h_i <= L/2, |y_i| + h_i <= L/2.

A branch is `argmin` penetration unless the caller overrides it by name, which
is what `t1_glide` does.  The LP is a feasibility problem with every translation
free or a declared subset free.

WHAT IS A PARAMETER, NOT A DIFFERENCE
-------------------------------------
The three callers used to disagree on five knobs.  Each is now explicit:

    pad        separation demanded beyond touching.  0.0 = pure feasibility;
               5e-10 (PAD) = the row-search profile, which asks every declared
               axis for a strict gap before the gate sees the state.
    move       bound on the global translation.
    free_span  free squares' offsets are bounded by ±free_span * L.
    free       which squares may translate (sat_probe frees a subset; the row
               searches free everything).
    branch     {} = delivered argmin per pair; a {(i,j): a} map = flips.
    tol        the gate's tolerance (`gate`, `price`).  sat_probe certifies at
               1e-9 on its raw LP state; the row searches certify at 0.0 on the
               12-dp state.

FROZEN-FROZEN PAIRS
-------------------
A pair with neither endpoint free contributes no variables.  It is skipped, as
`sat_probe` always skipped it -- at the delivered state the declared branch
already separates it, so re-testing it only re-derives the input.  The one case
that would not be safe is a *flipped* branch on a pair with both ends frozen, so
that case is refused rather than assumed.

THE INVARIANT
-------------
`python3 scripts/declp.py --selftest` states what caught run 67: **the delivered
state must be feasible at its own side.**  It also checks that the corrected
separation bound is load-bearing (there are pairs where the own-extent version
would understate it) and that the pad actually enters the constraints.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import packlib as P         # noqa: E402
import sqscore as SQ        # noqa: E402

#: separation demanded of every declared axis by the row-search profile
PAD = 5e-10
#: a pair counts as a contact when its penetration is above this (>= -CONTACT).
#: The wrong predicate (pen <= +CONTACT) reported 100 % tight pairs; see run 70.
CONTACT = 1e-6
#: the side ladder, largest shrink first
EPS = (1e-2, 3e-3, 1e-3, 1e-4, 1e-6)
#: exact words: t = tan(theta/2), so cos = (1-t^2)/(1+t^2), sin = 2t/(1+t^2)
WORDS = (("axis", 0.0), ("p8", math.sqrt(2.0) - 1.0), ("atan2", 0.5),
         ("atan3", 1.0 / 3.0), ("atan4", 0.25))


# ------------------------------------------------------------------- geometry
def theta_of(t: float) -> float:
    """theta = 2 atan(t); t = 0 is the axis branch exactly."""
    return 0.0 if t == 0.0 else 2.0 * math.atan(t)


def frames(st):
    """xy, theta, cos(theta), sin(theta) for a state of (x, y, angle)."""
    xy = np.array([(float(s[0]), float(s[1])) for s in st])
    th = np.array([float(s[2]) for s in st])
    cs, sn = np.cos(th), np.sin(th)
    return xy, th, cs, sn


def _geometry(xy, cs, sn):
    """U, V, Eu, S, dU, dV -- the shared tables (see packlib's verify)."""
    U = np.stack([cs, sn], axis=1)
    V = np.stack([-sn, cs], axis=1)
    # Eu[o, k] = half-extent of square k along square o's own axes
    Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
    PU = U @ xy.T
    PV = V @ xy.T
    dU = np.diag(PU)[:, None] - PU
    dV = np.diag(PV)[:, None] - PV
    S = np.stack([0.5 + Eu - np.abs(dU), 0.5 + Eu - np.abs(dV),
                  0.5 + Eu.T - np.abs(dU.T), 0.5 + Eu.T - np.abs(dV.T)])
    return U, V, Eu, S, dU, dV


def tables(xy, th):
    """U, V, Eu, S for a state (S[a, i, j] = penetration of pair i,j on branch a)."""
    xy = np.asarray(xy, dtype=float)
    th = np.asarray(th, dtype=float)
    U, V, Eu, S, _, _ = _geometry(xy, np.cos(th), np.sin(th))
    return U, V, Eu, S


def pair_tables(xy, cs, sn):
    """(S, pen, win, sign) — the run-65/67 shape kept for `extreme_probe`."""
    U, V, Eu, S, dU, dV = _geometry(np.asarray(xy, dtype=float),
                                   np.asarray(cs, dtype=float),
                                   np.asarray(sn, dtype=float))
    pen = np.minimum(np.minimum(S[0], S[1]), np.minimum(S[2], S[3]))
    sign = np.sign(np.stack([dU, dV, dU.T, dV.T]))
    return S, pen, np.argmin(S, axis=0), sign


def branches(S):
    """The delivered branch per pair: the axis of least penetration."""
    return np.argmin(S, axis=0)


# ------------------------------------------------------------------------- LP
def solve(xy, th, L, free=None, branch=None, pad=0.0, move=0.6, free_span=2.0):
    """Feasibility at side L for the declared axes.  New centres, or None.

    Args:
        xy, th: centres and rotations (theta frozen; D is what moves).
        L: side being tested (containment).
        free: indices allowed to translate; None = all of them.
        branch: {(i, j): a} with i < j overrides the delivered argmin branch.
        pad: extra separation demanded of every declared axis.
        move: bound on the global translation.
        free_span: free offsets are bounded by ±free_span * L.

    Returns:
        np.ndarray of new centres, or None if the LP is infeasible.
    """
    xy = np.asarray(xy, dtype=float)
    th = np.asarray(th, dtype=float)
    n = len(xy)
    free = sorted(range(n) if free is None else (int(i) for i in free))
    idx = {i: k for k, i in enumerate(free)}
    U, V, Eu, S = tables(xy, th)
    h = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    nv = 2 + 2 * len(free)
    branch = branch or {}

    def var_of(i):
        """Column of square i's dx (dy is +1), or None if it is frozen."""
        return None if i not in idx else 2 + 2 * idx[i]

    A, b = [], []
    for i in range(n):
        for j in range(i + 1, n):
            flipped = (i, j) in branch
            a = int(branch[(i, j)]) if flipped else int(np.argmin(S[:, i, j]))
            owner = i if a < 2 else j
            other = j if a < 2 else i
            q = U[owner] if a % 2 == 0 else V[owner]
            # the separation constant: 0.5 for the owner (its own axis) plus the
            # OTHER square's half-extent along it -- run 67's defect was using
            # the other square's own extent here.
            hs = 0.5 + Eu[owner, other]
            t0 = float((xy[j] - xy[i]) @ q)
            sgn = 1.0 if t0 >= 0 else -1.0
            need = hs + pad - sgn * t0          # required left-hand side
            vi, vj = var_of(i), var_of(j)
            if vi is None and vj is None:
                if flipped and need > 0.0:
                    return None                 # a flip with nothing to move
                continue                        # already separated at L0
            row = np.zeros(nv)
            if vj is not None:
                row[vj] += sgn * q[0]
                row[vj + 1] += sgn * q[1]
            if vi is not None:
                row[vi] -= sgn * q[0]
                row[vi + 1] -= sgn * q[1]
            # the packing condition is  row.x >= need ; linprog asks for <=
            A.append(-row)
            b.append(-need)
    for i in range(n):
        v = var_of(i)
        for ax in (0, 1):
            for sg in (1.0, -1.0):
                row = np.zeros(nv)
                row[ax] = sg
                if v is not None:
                    row[v + ax] = sg
                A.append(row)
                b.append(L / 2 - h[i] - sg * float(xy[i][ax]))
    res = linprog(np.zeros(nv), A_ub=np.array(A), b_ub=np.array(b),
                  bounds=[(-move, move)] * 2
                  + [(-free_span * L, free_span * L)] * (2 * len(free)),
                  method="highs")
    if res.status != 0:
        return None
    x = res.x
    new = np.array(xy, dtype=float)
    new[:, 0] += x[0]
    new[:, 1] += x[1]
    for i in free:
        new[i, 0] += x[var_of(i)]
        new[i, 1] += x[var_of(i) + 1]
    return new


# ----------------------------------------------------------------------- gate
def gate(n, xy, th, L0, tol=0.0):
    """The exact gate: a 12-dp state, packlib SAT, the canonical score.

    `tol` is the SAT tolerance: 0.0 is the project's canonical gate (the state is
    rounded to 12 dp first); sat_probe's withdrawn probe certified its raw LP
    state at 1e-9 instead, and that is why the knob exists rather than a copy.
    """
    st = [(round(float(xy[i][0]), 12), round(float(xy[i][1]), 12),
           round(float(th[i]), 12)) for i in range(len(xy))]
    v = P.verify(st, tol=tol)
    L = SQ.extent(st)
    return {"ok": bool(v["ok"]), "worst_pen": float(v["worst_pen"]), "L": L,
            "gain": SQ.row_gain(n, L) - SQ.row_gain(n, L0),
            "state": st if v["ok"] else None}


def price(n, xy, th, L0, eps_list=EPS, tol=0.0, **solve_kw):
    """Largest admitted shrink on the eps ladder, gated.  Never a result alone.

    Returns the first cell whose state survives the gate at a strictly smaller
    side; otherwise the first LP-feasible cell at any eps; otherwise a refusal
    record.  LP feasibility by itself is reported as `lp` and nothing more.
    """
    first = None
    for eps in eps_list:
        new = solve(xy, th, L0 - eps, **solve_kw)
        if new is None:
            continue
        g = gate(n, new, th, L0, tol=tol)
        rec = {"eps": eps, "lp": True, "gate_ok": g["ok"], "L": g["L"],
               "worst_pen": g["worst_pen"], "gain": g["gain"]}
        if g["ok"] and g["L"] < L0 - 1e-9:
            rec["state"] = g["state"]
            return rec
        if first is None:
            first = rec
    return first or {"eps": None, "lp": False, "gate_ok": False}


def max_shrink(xy, th, L0, lo=1e-12, hi=1e-2, it=40, **solve_kw):
    """Largest eps at which the declared axes still admit a translation."""
    if solve(xy, th, L0 - lo, **solve_kw) is None:
        return 0.0
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        if solve(xy, th, L0 - mid, **solve_kw) is None:
            hi = mid
        else:
            lo = mid
    return lo


# ------------------------------------------------------------------- selftest
def selftest() -> int:
    """The invariant that caught run 67, plus the two checks that make it bite."""
    per = SQ.load()
    checks = 0
    for n in (10, 83, 294):
        st = per[n]
        xy, th, _, _ = frames(st)
        L0 = SQ.extent(st)
        for free in (set(range(min(8, n))), set(range(n))):
            ok = solve(xy, th, L0, free=free, pad=0.0,
                       move=1.0, free_span=1.0) is not None
            assert ok, f"delivered row {n} infeasible at L0, {len(free)} free"
            checks += 1
    print(f"selftest: {checks}/6 mandatory feasibility checks pass "
          "(delivered at L0)")

    # the separation bound must use the OTHER square's extent, and it must matter
    pairs = understated = 0
    for n in (10, 18, 83, 294):
        st = per[n]
        xy, th, _, _ = frames(st)
        U, V, Eu, S = tables(xy, th)
        for i in range(n):
            for j in range(i + 1, n):
                a = int(np.argmin(S[:, i, j]))
                owner, other = (i, j) if a < 2 else (j, i)
                q = U[owner] if a % 2 == 0 else V[owner]
                hs = 0.5 + Eu[owner, other]
                t0 = abs(float((xy[j] - xy[i]) @ q))
                assert t0 >= hs - 1e-9, (n, i, j, t0, hs)
                pairs += 1
                if Eu[owner, other] > 0.5 + 1e-9:
                    understated += 1
    assert understated > 0, "no tilted pair: the own-extent defect is invisible"
    print(f"selftest: {pairs} declared branches separate at L0; the own-extent "
          f"form would understate {understated} of them")

    # the pad is load-bearing: it buys a strict gap and refuses a real demand
    st = per[18]
    xy, th, _, _ = frames(st)
    L0 = SQ.extent(st)
    assert solve(xy, th, L0, pad=0.0, move=0.6, free_span=2.0) is not None
    assert solve(xy, th, L0, pad=0.5, move=0.6, free_span=2.0) is None
    print("selftest: pad enters the constraints (0.0 passes at L0, 0.5 refuses)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    print("declp.py --selftest    # the run-67 invariant for the shared builder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
