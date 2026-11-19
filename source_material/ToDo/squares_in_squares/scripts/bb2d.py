#!/usr/bin/env python3
r"""bb2d.py — the branch-space MILP in 2D, solved by our own LP-guided branch
and bound.  Frozen angles, exact gate, one row at a time.

WHAT THE PROBLEM IS
-------------------
Orientations theta are frozen (the delivered row's own angles).  The only free
quantities are the n translations and the container side L.  For a pair of
convex unit squares the separating-axis theorem says

    they do not overlap  <=>  some q in {u_i, v_i, u_j, v_j} separates them,
                              i.e.  |(c_j - c_i).q| >= h_i(q) + h_j(q),

with h_k(q) = (|q.u_k| + |q.v_k|)/2 the half-extent of square k along q.  So
"is there *any* packing of these angles in side L" is a disjunction: choose one
(axis, sign) per pair, then the rest is a linear feasibility problem in the
translations.  Unlike `declp.solve`, which enforces one declared axis per pair
and therefore answers only for that declaration, this asks the disjunctive
question, so a `yes` is a packing and a `no` is a statement about the angle
multiset -- not about one branch structure.

THE MODEL AT A NODE
-------------------
    variables   d_i in R^2 (translations), t = L, w_{p,a} in [0,1]
    containment  c_i + d_i + h_i <= t/2 ,   -(c_i + d_i) + h_i <= t/2
    pair p, branch a = (q, sign):
                 sign*q.(d_j - d_i) + M (1 - w_{p,a}) >= h_i(q)+h_j(q) - sign*q.(c_j-c_i)
                 sum_a w_{p,a} = 1
    objective    min t

w integral selects exactly one separating axis per pair, and then the node's
state satisfies a true separating hyperplane for every pair: **a gated
integer solution is a packing**, not a relaxation of one.  That is the whole
difference from the declared-axis LP.

THE BRANCH AND BOUND
--------------------
The LP relaxation (w continuous) is a genuine lower bound on the best side over
every structure the node still allows, so it is the node bound.  Branch on the
pair whose w is least integral: one child *fixes* its most-favoured branch, the
other *forbids* it (bound 0) and lets the LP reallocate.  Depth-first with an
incumbent; a node whose bound reaches the incumbent is pruned; a leaf's state
goes through the exact gate (`declp.gate`: 12-dp state, packlib SAT, no
tolerance) and only a gated state may lower the incumbent.  When the stack
empties, `best` is attained *and* no structure does better than `best - TOL`.

That is the certificate the declared-axis probes could not give: run 71 flipped
6,684 single branches and found nothing; this either closes the whole space or
says how far it got.

THE BOUND IS EMPTY, AND THAT IS THE RESULT
------------------------------------------
Two consequences, both measured (run 74):

  * the cheap bound -- drop the undecided pairs -- leaves containment alone,
    whose optimum is `max_i 2h_i` at every node, and prunes nothing;
  * the disjunctive relaxation is no better: with `sum_a w_a = 1` over 4 or 8
    branches, a pair can put a fraction on each axis and on both signs, and the
    two signs cancel, so Delta c may be 0 while every branch is "a little"
    satisfied.  The measured root bounds equal `max_i 2h_i` exactly -- 1.414214
    (n = 5, 10), 1.409216 (n = 11), 1.322876 (n = 18) and 1.0 (the aligned
    rows, n = 6, 9, 13) -- against sides of 2.7-4.8.  So the relaxation carries no information, branch and bound
    degenerates into enumeration, and the structure counts are 8^4*4^6 = 16.8M
    at n = 5 and 8^9*4^36 at n = 10: nothing closes above n = 3.

That is a negative about the *method*, not about the model: the leaf is exact,
so the same machinery answers a finite family exactly, and `--flips k` does
that -- every structure within k declared-branch changes of the delivered one,
each solved to its own minimum side.  At k = 2 that is 19,477 structures at
n = 10 and 40,050 at n = 11, each solved exactly and each improvement still
judged by the gate, and it closes in under a minute.

An improvement is judged the way the table was made: `packlib.finalize` then
`declp.gate`.  A raw LP state is never gateable -- this file demands every
separation `PAD` short, so the 12-dp gate reads that shortfall as penetration at
every side, and the delivered row's own LP state is refused at pen 1.46e-9.
Gating raw, as the first version of `--flips` did, is a dead branch: a real
4e-3 improvement would have been certified as `False` and silently dropped.
`control 5` pins both the refusal and the certificate.

WHAT A RESULT MEANS
-------------------
Per row: `L` (gated side of the best structure), `closed` (stack exhausted),
`lower` (best side no structure beats), `nodes`, and the delivered `L0`.
  * closed and L == L0  -> the row's L is optimal *for its angle multiset*:
    no rearrangement of the delivered angles can improve it.  A conditional
    worth reading twice, because only n <= 3 close (see the section above).
  * L < L0 - 1e-6 -> a gated improvement at frozen angles.  It is reported as
    `candidates` in the ledger and **not** written to submission.csv: the table
    is the audited record and changes only by the project's own protocol.
  * open -> the bound is reported as a bound.  Nothing is claimed.
"""
from __future__ import annotations

import itertools
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import declp as D          # noqa: E402
import packlib as P        # noqa: E402
import sqscore as SQ       # noqa: E402

ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "workspace/push/bb2d.json")

#: pruning tolerance on the side (the gate is exact; this is the LP's slack)
TOL = 1e-9
#: the LP is float, and a delivered contact is a tangency: a pair that touches
#: exactly can read as a 1e-16 violation, which makes a *rigid* structure
#: infeasible.  Every separation is therefore demanded 1e-9 short, so the LP's
#: side understates the true one by at most 1e-9 -- stated, never hidden.
PAD = 1e-9
#: default work limits per row -- a node cap and a wall-clock cap
NODES = 20000
SECONDS = 100.0
#: a certified improvement must survive `packlib.finalize`, which opens every
#: contact by ~2e-9 and so raises the side by ~3.4e-9.  The bar is therefore the
#: finalizer's own pad, not the LP's 1e-9: `seam_wheels.GAIN_MIN` makes the same
#: choice, for the same reason (a 2e-9 "gain" is the pad, not a gain).
GAIN_MIN = 4e-8
#: the rows this instrument is asked about by default: small n, and every one of
#: them a row whose delivered angle multiset is what would be certified
DEFAULT_ROWS = (5, 6, 9, 10, 11, 13)


# ------------------------------------------------------------------ geometry
def h_along(th: float, q) -> float:
    """Half-extent of a unit square rotated `th` along the unit direction q."""
    return 0.5 * (abs(math.cos(th) * q[0] + math.sin(th) * q[1])
                  + abs(-math.sin(th) * q[0] + math.cos(th) * q[1]))


def gate_state(n, st, th, L0):
    """Certify an LP state the way every delivered row was certified.

    A raw state from this file's LP is **not gateable**.  Every separation was
    demanded `PAD` short, so `declp.gate` -- 12 dp, tolerance 0.0 -- sees that
    shortfall as penetration and refuses, at every side; the delivered row's own
    LP state is refused at pen 1.46e-9.  Raising the side does not help, because
    the penetration is between squares and is independent of L.

    `packlib.finalize` scales the state up by ~2e-9 and rounds it, which is how
    the table itself was made.  Only the finalized state is a candidate, and its
    side (`SQ.extent`) is the number to compare with L0.  `control 5` pins both
    halves of this: the raw refusal and the finalized certificate.
    """
    stf, _ = P.finalize([(float(c[0]), float(c[1]), float(t))
                         for c, t in zip(st, th)])
    return D.gate(n, stf, th, L0)


def delivered_branch(tab, p):
    """Our branch index that the delivered state already uses for pair p.

    `declp` numbers its branches by (owner, axis) and picks the least-penetration
    one; here the same branch is the one with the largest separation slack
    |t0| - hs, with the sign the delivered centre difference has.  The control
    uses this to compare like with like -- the branch *ordering* of the two
    instruments is not the same, and assuming it was is how a control fails.
    """
    br = tab[p]
    ok = [a for a in range(len(br)) if br[a][2] * br[a][4] >= -1e-15]
    return max(ok, key=lambda a: abs(br[a][4]) - br[a][3])


def half_extent(th) -> np.ndarray:
    """Per-square half-extent along the container axes (x and y are equal)."""
    a = np.asarray(th, dtype=float)
    return 0.5 * (np.abs(np.cos(a)) + np.abs(np.sin(a)))


def cand_table(xy, th):
    """Per pair, the distinct (axis, sign) branches with their constants.

    Entry: (qx, qy, sign, hs, t0, need) with
      hs   = h_i(q) + h_j(q)                the required separation,
      t0   = q.(c_j - c_i)                  at the delivered centres,
      need = hs - sign*t0                   the left-hand side the LP must reach.
    Directions are canonicalised (q and -q are one axis with opposite signs), so
    an axis-aligned pair has 4 branches and a tilted pair 8.
    """
    xy = np.asarray(xy, dtype=float)
    th = np.asarray(th, dtype=float)
    cs, sn = np.cos(th), np.sin(th)
    n = len(xy)
    tab = []
    for i in range(n):
        for j in range(i + 1, n):
            canon = {}
            for o in (i, j):
                for q in ((cs[o], sn[o]), (-sn[o], cs[o])):
                    if q[1] < -1e-12 or (abs(q[1]) <= 1e-12 and q[0] < 0.0):
                        q = (-q[0], -q[1])
                    canon[(round(q[0], 12), round(q[1], 12))] = q
            br = []
            for q in canon.values():
                hs = h_along(th[i], q) + h_along(th[j], q)
                t0 = float((xy[j] - xy[i]) @ np.array(q))
                for s in (1.0, -1.0):
                    br.append((q[0], q[1], s, hs, t0, hs - s * t0 - PAD))
            tab.append(br)
    return tab


# ------------------------------------------------------------------ node LP
def _offsets(tab):
    offs, k = [], 0
    for br in tab:
        offs.append(k)
        k += len(br)
    return offs, k


def dbox(xy, h, n, Lmax):
    """Per-square translation box implied by containment alone.

    The model's container is [-t/2, t/2] with t <= Lmax, so c_i + d_i lies in
    [h_i - t/2, t/2 - h_i] and d_i in [h_i - Lmax/2 - c_i, Lmax/2 - h_i - c_i].
    These are the *tight* bounds, and they are what the big-M is built from:
    a symmetric +/-L box instead makes every M several times looser, which is
    the difference between a bound that prunes and one that does not.
    """
    lo = np.empty((n, 2))
    hi = np.empty((n, 2))
    for i in range(n):
        for ax in (0, 1):
            lo[i, ax] = h[i] - 0.5 * Lmax - xy[i][ax]
            hi[i, ax] = 0.5 * Lmax - h[i] - xy[i][ax]
    return lo, hi


def _BigM(q, s, need, i, j, lo, hi):
    """Tight big-M: the largest the disabled constraint can be violated by."""
    vmin = 0.0                       # min over the box of s*q.(d_j - d_i)
    for ax in (0, 1):
        k = s * q[ax]
        if k >= 0.0:
            vmin += k * (lo[j, ax] - hi[i, ax])
        else:
            vmin += k * (hi[j, ax] - lo[i, ax])
    return max(0.0, need - vmin)


def node_lp(xy, tab, fixed, forbidden, h, n, Lmax, tmin=1.0):
    """LP relaxation of one node.  Returns (t, state, w) or (None, None, None).

    `fixed[p] = a` pins branch a of pair p; `forbidden[p]` is a set of pinned-off
    branches.  Every remaining w is continuous in [0,1]: a valid lower bound.
    """
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    lo_b, hi_b = dbox(xy, h, n, Lmax)      # once per node, not once per pair
    offs, nw = _offsets(tab)
    ti = 2 * n
    base = 2 * n + 1
    nv = base + nw
    c = np.zeros(nv)
    c[ti] = 1.0
    ur, ub_, er, eb = [], [], [], []
    for i in range(n):
        for ax in (0, 1):
            c0 = float(xy[i][ax])
            r = np.zeros(nv)
            r[2 * i + ax] = 1.0
            r[ti] = -0.5
            ur.append(r)
            ub_.append(-c0 - h[i])                      # c + d + h <= t/2
            r = np.zeros(nv)
            r[2 * i + ax] = -1.0
            r[ti] = -0.5
            ur.append(r)
            ub_.append(c0 - h[i])                       # -(c+d) + h <= t/2
    for p, (i, j) in enumerate(pairs):
        eq = np.zeros(nv)
        for a, (qx, qy, s, hs, t0, need) in enumerate(tab[p]):
            if p in fixed and fixed[p] != a:
                continue
            if a in forbidden.get(p, ()):
                continue
            w = base + offs[p] + a
            M = _BigM((qx, qy), s, need, i, j, lo_b, hi_b) + 1e-9
            r = np.zeros(nv)
            r[2 * j] += -s * qx
            r[2 * j + 1] += -s * qy
            r[2 * i] += s * qx
            r[2 * i + 1] += s * qy
            r[w] = M
            # -(s q.(d_j - d_i)) + M w <= M - need
            ur.append(r)
            ub_.append(M - need)
            eq[w] = 1.0
        if not eq.any():
            return None, None, None             # every branch of p forbidden
        er.append(eq)
        eb.append(1.0)
    lb = np.empty(nv)
    ub = np.empty(nv)
    lb[:2 * n] = lo_b.reshape(-1)
    ub[:2 * n] = hi_b.reshape(-1)
    lb[ti] = tmin
    ub[ti] = Lmax
    lb[base:] = 0.0
    ub[base:] = 1.0
    for p, a in fixed.items():
        lb[base + offs[p]:base + offs[p] + len(tab[p])] = 0.0
        ub[base + offs[p]:base + offs[p] + len(tab[p])] = 0.0
        lb[base + offs[p] + a] = ub[base + offs[p] + a] = 1.0
    for p, forb in forbidden.items():
        for a in forb:
            lb[base + offs[p] + a] = ub[base + offs[p] + a] = 0.0
    res = linprog(c, A_ub=np.array(ur), b_ub=np.array(ub_),
                  A_eq=np.array(er), b_eq=np.array(eb),
                  bounds=list(zip(lb, ub)), method="highs")
    if res.status != 0:
        return None, None, None
    x = res.x
    st = np.asarray(xy, dtype=float) + x[:2 * n].reshape(n, 2)
    w = [np.array([x[base + offs[p] + a] for a in range(len(tab[p]))])
         for p in range(len(pairs))]
    return float(x[ti]), st, w


def leaf_lp(xy, tab, fixed, h, n, Lmax):
    """The structure's own minimum side: every pair fixed, no w left to choose."""
    return node_lp(xy, tab, fixed, {}, h, n, Lmax)


def structure_lp(xy, tab, fixed, h, n, Lmax):
    """Minimum side for ONE complete structure, with no w variables at all.

    Much smaller than the relaxation (2n+1 columns), so it is the workhorse of
    the finite family sweep.  `--selftest` checks it against `leaf_lp`.
    """
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    ti = 2 * n
    nv = 2 * n + 1
    c = np.zeros(nv)
    c[ti] = 1.0
    ur, ub_ = [], []
    lo_b, hi_b = dbox(xy, h, n, Lmax)
    for i in range(n):
        for ax in (0, 1):
            c0 = float(xy[i][ax])
            r = np.zeros(nv)
            r[2 * i + ax] = 1.0
            r[ti] = -0.5
            ur.append(r)
            ub_.append(-c0 - h[i])
            r = np.zeros(nv)
            r[2 * i + ax] = -1.0
            r[ti] = -0.5
            ur.append(r)
            ub_.append(c0 - h[i])
    for p, (i, j) in enumerate(pairs):
        qx, qy, s, _, _, need = tab[p][fixed[p]]
        r = np.zeros(nv)
        r[2 * j] += -s * qx
        r[2 * j + 1] += -s * qy
        r[2 * i] += s * qx
        r[2 * i + 1] += s * qy
        ur.append(r)
        ub_.append(-need)
    lb = np.empty(nv)
    ub = np.empty(nv)
    lb[:2 * n] = lo_b.reshape(-1)
    ub[:2 * n] = hi_b.reshape(-1)
    lb[ti] = 1.0
    ub[ti] = Lmax
    res = linprog(c, A_ub=np.array(ur), b_ub=np.array(ub_),
                  bounds=list(zip(lb, ub)), method="highs")
    if res.status != 0:
        return None, None
    x = res.x
    return float(x[ti]), np.asarray(xy, dtype=float) + x[:2 * n].reshape(n, 2)


def flip_family(n, xy, th, L0, k=1, seconds=SECONDS):
    """Exact minimum side over every structure within k declared-branch changes.

    k = 1 is the same single-flip space `run 71` sampled, solved instead of
    sampled: each structure gets its own minimum side, so the answer is a number
    (and any improvement is gated), not a yes/no at one eps.  k = 2 is new.
    """
    xy = np.asarray(xy, dtype=float)
    th = np.asarray(th, dtype=float)
    h = half_extent(th)
    tab = cand_table(xy, th)
    npair = len(tab)
    base = {p: delivered_branch(tab, p) for p in range(npair)}
    alt = {p: [a for a in range(len(tab[p])) if a != base[p]] for p in range(npair)}
    Lmax = L0 + 0.5
    changers = []
    for p in range(npair):
        for a in alt[p]:
            changers.append(((p, a),))
    if k >= 2:
        for p in range(npair):
            for q in range(p + 1, npair):
                for a in alt[p]:
                    for b in alt[q]:
                        changers.append(((p, a), (q, b)))
    #: a changed structure only says something if its LP optimum actually moves:
    #: flipping a pair that is already slack in both branches is a no-op, and
    #: counting those as "tested" would inflate the family.  `moved` counts the
    #: structures whose own minimum side differs from L0 by more than 1e-6, and
    #: `min_other` is the nearest of them -- the record's margin in this family.
    t_start = time.time()
    best, where, count, gated = L0, None, 0, 0
    min_other, moved, infeas = math.inf, 0, 0
    stop = False
    for ch in changers:
        if time.time() - t_start > seconds:
            stop = True
            break
        fixed = dict(base)
        for p, a in ch:
            fixed[p] = a
        t, st = structure_lp(xy, tab, fixed, h, n, Lmax)
        count += 1
        if t is None:                    # not even the Lmax box admits it
            infeas += 1
            continue
        if t > L0 + 1e-6:
            moved += 1
            min_other = min(min_other, t)
        if t < best - GAIN_MIN:
            g = gate_state(n, st, th, L0)
            if g["ok"]:
                gated += 1
                if g["L"] < best - GAIN_MIN:
                    best, where = g["L"], ch
    return {"n": n, "k": k, "L0": L0, "L": best, "count": count,
            "total": len(changers), "gated": gated, "truncated": stop,
            "moved": moved, "infeasible": infeas,
            "min_other": None if not math.isfinite(min_other) else min_other,
            "where": None if where is None else [list(x) for x in where],
            "seconds": round(time.time() - t_start, 2)}


# ------------------------------------------------------------------ branch
def allowed(p, nbr, fixed, forbidden):
    """Branches of pair p the node still permits."""
    return [a for a in range(nbr)
            if a not in forbidden.get(p, ()) and (p not in fixed or fixed[p] == a)]


def branch_and_bound(n, xy, th, L0, node_cap=NODES, seconds=SECONDS, log=False):
    """Close the branch space for one row, or say how far it got."""
    xy = np.asarray(xy, dtype=float)
    th = np.asarray(th, dtype=float)
    h = half_extent(th)
    tab = cand_table(xy, th)
    npair = len(tab)
    Lmax = L0 + 0.5
    g0 = D.gate(n, xy, th, L0)
    best = {"L": g0["L"] if g0["ok"] else L0, "state": g0["state"],
            "branch": None, "gated": bool(g0["ok"]), "worst_pen": g0["worst_pen"]}
    t_start = time.time()
    stack = [({}, {})]
    nodes = leaves = 0
    closed = True
    while stack:
        if nodes >= node_cap or time.time() - t_start > seconds:
            closed = False
            break
        fixed, forbidden = stack.pop()
        nodes += 1
        t, st, w = node_lp(xy, tab, fixed, forbidden, h, n, Lmax)
        if t is None or t >= best["L"] - TOL:
            continue
        und = [p for p in range(npair)
               if len(allowed(p, len(tab[p]), fixed, forbidden)) > 1]
        if not und:
            leaves += 1
            g = gate_state(n, st, th, L0)
            if g["ok"] and g["L"] < best["L"] - 1e-12:
                best = {"L": g["L"], "state": g["state"], "branch": dict(fixed),
                        "gated": True, "worst_pen": g["worst_pen"]}
            continue
        # the pair whose branch choice is least decided, and its favourite
        def frac(p):
            al = allowed(p, len(tab[p]), fixed, forbidden)
            return 1.0 - max(w[p][a] for a in al)
        p = max(und, key=frac)
        al = allowed(p, len(tab[p]), fixed, forbidden)
        a_star = max(al, key=lambda a: w[p][a])
        # child 1: fix the favourite; child 2: forbid it and let the LP reallocate
        f2 = dict(fixed)
        f2[p] = a_star
        stack.append((f2, dict(forbidden)))
        fb = {q: set(v) for q, v in forbidden.items()}
        fb.setdefault(p, set()).add(a_star)
        stack.append((dict(fixed), fb))
        if log and nodes % 500 == 0:
            print(f"  n={n} nodes={nodes} best={best['L']:.6f} stack={len(stack)}",
                  flush=True)
    bound = best["L"]
    if not closed:
        pend = []
        for fixed, forbidden in stack[:400]:
            t, _, _ = node_lp(xy, tab, fixed, forbidden, h, n, Lmax)
            if t is not None:
                pend.append(t)
        bound = min([best["L"]] + pend) if pend else best["L"]
    return {"n": n, "L0": L0, "L": best["L"], "best_state": best["state"],
            "gated": best["gated"],
            "branch": {f"{k[0]},{k[1]}": int(v)
                       for k, v in (best["branch"] or {}).items()},
            "nodes": nodes, "leaves": leaves, "closed": closed,
            "lower": best["L"] if closed else round(bound, 9),
            "seconds": round(time.time() - t_start, 2),
            "worst_pen": best["worst_pen"]}


# ------------------------------------------------------------------ control
def control() -> int:
    per = SQ.load()
    print("control 1 — degradation: the delivered structure's LP is declp's own optimum")
    for n in (5, 10, 18):
        st = per[n]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        h = half_extent(th)
        tab = cand_table(xy, th)
        fixed = {p: delivered_branch(tab, p) for p in range(len(pairs))}
        t, _, _ = leaf_lp(xy, tab, fixed, h, n, L0 + 0.5)
        assert t is not None, n
        lo, hi = 0.0, 0.5
        if D.solve(xy, th, L0 - hi) is not None:
            lo = hi
        else:
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                if D.solve(xy, th, L0 - mid) is not None:
                    lo = mid
                else:
                    hi = mid
        ref = L0 - lo
        assert abs(t - ref) < 1e-6, (n, t, ref)
        print(f"  n={n:3d}  this LP {t:.9f}   declp {ref:.9f}   diff {t - ref:+.2e}")
        t_drop, _, _ = node_lp(xy, tab, {}, {}, h, n, L0 + 0.5)
        print(f"        root relaxation {t_drop:.6f}; containment alone bounds "
              f"max 2h = {float(2 * h.max()):.6f}")

    print("control 2 — the lean structure LP agrees with the full leaf LP")
    for n in (5, 10):
        st = per[n]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        h = half_extent(th)
        tab = cand_table(xy, th)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        base = {p: delivered_branch(tab, p) for p in range(len(pairs))}
        for label, fixed in (("delivered", base),
                             ("one flip", {**base, 0: next(a for a in range(len(tab[0]))
                                                           if a != base[0])})):
            t1, _ = structure_lp(xy, tab, fixed, h, n, L0 + 0.5)
            t2, _, _ = leaf_lp(xy, tab, fixed, h, n, L0 + 0.5)
            assert t1 is not None and t2 is not None
            assert abs(t1 - t2) < 1e-7, (n, label, t1, t2)
        print(f"  n={n:3d}: structure LP and leaf LP agree on the delivered "
              f"structure and on one flip ({t1:.9f})")

    print("control 3 — exhaustive: every structure at n = 2, 3 against the B&B")
    for n in (2, 3):
        st = per[n]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        h = half_extent(th)
        tab = cand_table(xy, th)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        best, cnt = None, 0
        for combo in itertools.product(*[range(len(tab[p])) for p in range(len(pairs))]):
            t, _, _ = leaf_lp(xy, tab, {p: a for p, a in enumerate(combo)}, h, n, L0 + 0.5)
            cnt += 1
            if t is not None and (best is None or t < best):
                best = t
        rec = branch_and_bound(n, xy, th, L0)
        assert abs(rec["L"] - best) < 1e-6, (n, rec["L"], best)
        assert rec["closed"], n
        print(f"  n={n}: {cnt} structures, exhaustive min {best:.9f}, "
              f"B&B {rec['L']:.9f} (closed, {rec['nodes']} nodes)")

    print("control 4 — the gate is the judge")
    st = per[5]
    xy, th, _, _ = D.frames(st)
    L0 = SQ.extent(st)
    g = D.gate(5, xy, th, L0)
    assert g["ok"], g
    bad = np.array(xy, dtype=float).copy()
    bad[1] = bad[0] + 0.25 * (bad[1] - bad[0])
    gb = D.gate(5, bad, th, L0)
    assert not gb["ok"] and gb["worst_pen"] > 0, gb
    print(f"  delivered n=5 gates at {g['L']:.9f}; a 25%-moved copy is refused "
          f"(pen {gb['worst_pen']:.6f})")

    print("control 5 — an LP state is certified through packlib.finalize, not raw")
    for label, flip in (("delivered", None), ("near miss (49,0)", (49, 0))):
        st = per[11]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        h = half_extent(th)
        tab = cand_table(xy, th)
        pairs = [(i, j) for i in range(11) for j in range(i + 1, 11)]
        fixed = {p: delivered_branch(tab, p) for p in range(len(pairs))}
        if flip is not None:
            fixed[flip[0]] = flip[1]
        t, s = structure_lp(xy, tab, fixed, h, 11, L0 + 0.5)
        raw = D.gate(11, s, th, t)
        fin = gate_state(11, s, th, L0)
        assert not raw["ok"] and raw["worst_pen"] > 0, raw
        assert fin["ok"], (label, fin)
        print(f"  n=11 {label:16s}: LP {t:.12f}  raw gate refuses (pen "
              f"{raw['worst_pen']:.2e}); finalized -> {fin['L']:.12f} "
              f"({fin['L'] - L0:+.3e} vs L0)")
    print("control: OK")
    return 0


# ---------------------------------------------------------------------- run
def run(ns, ledger=None, node_cap=NODES, seconds=SECONDS, log=False):
    per = SQ.load()
    out = {"note": "frozen angles; branch space closed by own LP-guided B&B",
           "rows": [], "candidates": []}
    print(f"{'n':>4} {'L0':>9} {'L':>9} {'dL':>10} {'closed':>6} {'nodes':>7} "
          f"{'leaves':>7} {'s':>6}  verdict")
    for n in ns:
        st = per[n]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        rec = branch_and_bound(n, xy, th, L0, node_cap=node_cap,
                               seconds=seconds, log=log)
        d = rec["L"] - L0
        if rec["closed"] and d > -1e-6:
            verdict = "optimal for its angle multiset"
        elif d < -1e-6:
            verdict = f"IMPROVEMENT at frozen angles ({d:+.3e})"
            out["candidates"].append({"n": n, "L": rec["L"], "L0": L0,
                                      "state": rec["best_state"]})
        else:
            verdict = f"open: no structure beats {rec['lower']:.6f}"
        print(f"{n:4d} {L0:9.6f} {rec['L']:9.6f} {d:+10.2e} {str(rec['closed']):>6} "
              f"{rec['nodes']:7d} {rec['leaves']:7d} {rec['seconds']:6.1f}  {verdict}")
        rec["verdict"] = verdict
        rec["angle_words"] = sorted({round(float(t), 9) for t in th})
        out["rows"].append(rec)
    if ledger:
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nledger -> {os.path.relpath(ledger, ROOT)}")
    return 0


def flips_report(ns, k, ledger=None, seconds=SECONDS):
    """Exact minimum side over every structure within k branch changes."""
    per = SQ.load()
    out = {"note": f"every structure within {k} declared-branch change(s) of the "
                   f"delivered one, each solved to its own minimum side",
           "rows": []}
    print(f"{'n':>4} {'L0':>9} {'min L':>9} {'moved':>7} {'infeas':>7} {'nearest':>9} "
          f"{'structures':>11} {'of':>9} {'gated':>5} {'s':>6}  verdict")
    for n in ns:
        st = per[n]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        rec = flip_family(n, xy, th, L0, k=k, seconds=seconds)
        if rec["truncated"]:
            verdict = f"TRUNCATED at {rec['count']} of {rec['total']}"
        elif abs(rec["L"] - L0) < 1e-9:
            verdict = f"no structure within {k} change(s) beats L0"
        else:
            verdict = f"IMPROVEMENT {rec['L']:.9f} at {rec['where']}"
        near = rec["min_other"] if rec["min_other"] is not None else L0
        print(f"{n:4d} {L0:9.6f} {rec['L']:9.6f} {rec['moved']:7d} "
              f"{rec['infeasible']:7d} {near - L0:+9.2e} "
              f"{rec['count']:11d} {rec['total']:9d} {rec['gated']:5d} "
              f"{rec['seconds']:6.1f}  {verdict}")
        rec["verdict"] = verdict
        out["rows"].append(rec)
    if ledger:
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        with open(ledger, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nledger -> {os.path.relpath(ledger, ROOT)}")
    return 0


def _args(argv):
    """One parser for both modes: rows, --flips K, --nodes K, --seconds S, --log."""
    ns, k, node_cap, seconds, log = [], 1, NODES, SECONDS, False
    i = 0
    while i < len(argv):
        v = argv[i]
        if v in ("--flips", "--nodes", "--seconds") and i + 1 < len(argv):
            val = argv[i + 1]
            if v == "--flips":
                k = int(val)
            elif v == "--nodes":
                node_cap = int(val)
            else:
                seconds = float(val)
            i += 2
            continue
        if v == "--log":
            log = True
        elif v.isdigit() and not v.startswith("0"):
            ns.append(int(v))
        i += 1
    return ns, k, node_cap, seconds, log


def main() -> int:
    argv = sys.argv[1:]
    if "--control" in argv or "--selftest" in argv:
        return control()
    ns, k, node_cap, seconds, log = _args(argv)
    if "--flips" in argv:
        return flips_report(ns or list(DEFAULT_ROWS), k,
                            ledger=os.path.join(ROOT,
                                                f"workspace/push/bb2d_flips{k}.json"),
                            seconds=seconds)
    return run(ns or list(DEFAULT_ROWS), ledger=LEDGER, node_cap=node_cap,
               seconds=seconds, log=log)


if __name__ == "__main__":
    raise SystemExit(main())
