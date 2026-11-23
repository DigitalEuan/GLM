#!/usr/bin/env python3
r"""observer_chain.py — depth-two contact chains and a coupled multi-cell repair.

Run 106 certified 552 of 553 census rows and left two questions: whether a certified sentence
is jammed at *depth one* (doc 66 section 7's two-cell trade), and whether n = 330's three
coupled overlaps can be cleared by moving several cells at once (doc 67 sections 2-3).  Both
are asked here.  Two contracts from the Lean side are used as *structure*, never as authority:
their statements are re-computed exactly in Python and cross-referenced.

THE OBSERVER CONTRACT (`aristotle_01/RequestProject/ObserverY.lean`).

  * `readCost d t = 1/(t + d/t)` (`readCost`, `d` = difference state, `t` = loop-check),
    bounded above by `1/(2 sqrt d)` (`readCost_le_amgm`, equality only at `t = sqrt d`) and
    below by nothing (`readCost_le_inv`).  This script uses it exactly over `Q`: a depth-two
    chain is read with `d = 2` and loop-check `Pi` = the number of chains read in one pass, so
    `readCost(2, Pi) = 1/(Pi + 2/Pi)` is rational and the ceiling `1/(2 sqrt 2) = sqrt2/4` is
    a field element of `Q(sqrt 2)`.  The *scale balance* is the point: `readCost(2, 1) =
    readCost(2, 2) = 1/3`, and the ceiling is attained only at `Pi = sqrt 2`, which no chain
    count can be -- every integer loop-check pays exactly `2 sqrt2 / 3 = 0.9428` of it.  The
    read budget is flat below `sqrt 2` and falling above it, so reading one chain at a time
    (depth-first) is the coherent order, and that is the order the tracer uses.
  * `bitTax v = |v| Q`, `syndromePenalty v = |leader(syn v)| Q`, `taxMOG = bitTax +
    syndromePenalty`, zero exactly on lawful patterns and bounded by `4Q`
    (`syndromePenalty_le`, the covering radius).  A candidate move is scored the same way,
    exactly and without floats: `taxMOG / Q = (cells moved) + W * (violated pairs left)`,
    because every term is a multiple of the activation quantum `Q > 0`, so the quotient is an
    exact integer and its ordering is `taxMOG`'s own.

THE MOG CONTRACT (`mog_cube_1/RequestProject/GolaySemantics.lean`).

  * `syn` is the 12-bit syndrome of a 24-cell word against `H = [B | I12]`;
    `violation_unique_of_wt_le_three` says two violation patterns of weight `<= 3` with the
    same syndrome are equal, and `exists_two_wt_four_same_syndrome` says four is sharp (the
    two halves of an octad collide).  So **at most three simultaneous violations are uniquely
    diagnosable, four or more are ambiguous**.  This script re-implements the syndrome over
    GF(2) from the Lean file's own `Bmat`, re-checks both facts, and uses the consequence as a
    search rule: at three violated pairs the cluster is *named* exactly, so the repair
    enumerates moves on the named cells instead of speculating about which cells are at fault.

A CORRECTION CARRIED IN FROM RUN 106.  `cand106.wall_room` caps a pair by the maximum over
*narrowing* axes of `slack/|d.q|` and treats an axis with negative slack as an immediate
block.  But a pair is legal while **some** axis is separated, so a pair fails only when
*every* axis is negative: an axis that is constant or widening under the motion never fails,
and an axis already negative constrains nothing.  Control 1 pins the difference on an exact
knight pair (`dx = 1`, `dy = 2`, moving `+x`): the old rule reads `0`, the true cap is
unbounded.  `room_set` below is the corrected rule, and part 1 therefore re-tests depth one
as well as depth two -- a wall cell with positive room is not jammed, and L shrinks.

PART 1 -- the directed depth-two tracer on the certified n = 66 and n = 325 sentences.  The
contact graph is the *tight* graph (SAT slack exactly 0).  From every bounding-box wall cell
and every inward direction the tracer walks wall -> tight blocker 1 -> tight blocker 2,
pruning the moment blocker 2's required receding direction is itself blocked, keeping a chain
only when two interior cells can hold it.  Survivors get the exact `room_set`, the exact gate
and a canonical certificate, and the side is recomputed, so "shrinks L" is a measurement.

PART 2 -- the simultaneous multi-cell repair on n = 330's three-overlap cycle.  From run 106's
four-move state the remaining violated pairs are (184, 195), (216, 233) and (224, 247).  All
2-cell and 3-cell simultaneous `Q(sqrt 2)` translations of the coupled cluster are enumerated,
scored with `taxMOG`, and any 0-overlap candidate is passed through the exact gate and the
standalone verifier.

READ-ONLY: `workspace/push/observer_chain.json`.  `submission.csv` and the root
`WHITEBOARD.md` are never opened for writing here.

USAGE
    python3 scripts/observer_chain.py --selftest
    python3 scripts/observer_chain.py --chain
    python3 scripts/observer_chain.py --repair3
    python3 scripts/observer_chain.py            # both
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cand105 as C                # noqa: E402
import cand106 as K                # noqa: E402
import rat47 as R                  # noqa: E402

Q2 = C.Q2
ZERO, ONE = K.ZERO, K.ONE
HALF = F(1, 2)
OUT = os.path.join(ROOT, "workspace/push/observer_chain.json")
ROUNDING = F(1, 10 ** 6)
TAX_W = 1                          # the syndrome debt, in activation quanta
DIAG_LIMIT = 3                     # <= 3 violations are uniquely diagnosable (MOG contract)
REACH = F(1, 10 ** 6)              # near-contact filter for candidate generation
L_CERT = {66: F(4328427125631, 500000000000), 325: F(741421356313, 40000000000)}
PARTS_330 = ((14, 32), (28, 32), (80, 101), (195, 216))


# ============================================================== the observer contract
def read_cost(d, t):
    r"""`readCost d t = 1/(t + d/t)` of `ObserverY.lean`, exactly over `Q`."""
    d, t = F(d), F(t)
    if t == 0:
        raise ZeroDivisionError("the loop-check must be positive")
    return 1 / (t + d / t)


def read_cost_eq(d, t):
    """The identity `readCost d t = t/(t^2 + d)` (`readCost_eq`)."""
    return F(t) / (F(t) ** 2 + F(d))


def read_ceiling(d=2):
    """`1/(2 sqrt d)` for `d = 2`, exactly: `sqrt(2)/4` in `Q(sqrt 2)`."""
    if d != 2:
        raise ValueError("only d = 2 has an exact representative in Q(sqrt 2)")
    return Q2(F(0), F(1, 4))


def read_efficiency(d, t):
    """The read cost as a fraction of its AM-GM ceiling, exactly in `Q(sqrt 2)`."""
    return C._q(read_cost(d, t)) / read_ceiling(d)


# ================================================================== the MOG contract
# `Bmat` copied from GolaySemantics.lean (12 x 12 over Z/2), row for row.
BMAT = (
    (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    (1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0),
    (1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1),
    (1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1),
    (1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0),
    (1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1),
    (1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1),
    (1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1),
    (1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0),
    (1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0),
    (1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0),
    (1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1),
)
# `H = [B | I12]` as 24-bit masks: row i covers the cells j < 12 with Bmat[i][j] = 1, and 12 + i.
HMASK = tuple(
    sum(1 << j for j in range(12) if BMAT[i][j]) | (1 << (12 + i)) for i in range(12)
)


def mog_syndrome(bits):
    """The 12-bit syndrome of a 24-cell pattern, exactly in GF(2) (`GolaySemantics.syn`)."""
    return tuple(bin(bits & HMASK[i]).count("1") & 1 for i in range(12))


def weight(bits):
    return bin(bits).count("1")


def diagnosis_census(wmax=4):
    """The syndrome classes at each violation weight: the MOG's diagnosability statement."""
    out = {}
    for w in range(wmax + 1):
        seen = {}
        for comb in itertools.combinations(range(24), w):
            bits = sum(1 << j for j in comb)
            seen.setdefault(mog_syndrome(bits), []).append(bits)
        collisions = {s: v for s, v in seen.items() if len(v) > 1}
        out[w] = {"patterns": sum(len(v) for v in seen.values()),
                  "syndromes": len(seen),
                  "colliding_classes": len(collisions),
                  "first_collision": ([hex(b) for b in next(iter(collisions.values()))]
                                      if collisions else None)}
    return out


def diagnosable(violations):
    """True when a violation pattern's weight is inside the MOG's exact-diagnosis range."""
    return len(violations) <= DIAG_LIMIT


# ============================================================ the taxMOG objective
def tax_mog_units(moved, remaining):
    """`taxMOG / Q`, exact: every term of `taxMOG` is a multiple of the activation quantum."""
    return F(moved) + F(TAX_W) * F(remaining)


# ================================================================ the exact geometry
def rate(dirs, i, j, q):
    """`d(proj)/dt` for the pair `(i, j)`, whose projection is `(x_j - x_i).q`."""
    d = ZERO
    if i in dirs:
        di = dirs[i]
        d = d - (di[0] * q[0] + di[1] * q[1])
    if j in dirs:
        dj = dirs[j]
        d = d + (dj[0] * q[0] + dj[1] * q[1])
    return d


def pair_slack(rows, dirs, i, j, t):
    """The pair's SAT slack at time `t`: the maximum over its eight axes, exactly."""
    best = None
    for proj, need, q in rows:
        val = abs(proj + t * rate(dirs, i, j, q)) - need
        if best is None or val > best:
            best = val
    return best


def room_set(pf, wf, dirs):
    """The largest exact `t` for which moving every cell of `dirs` by `t d` keeps every pair
    legal, or `None` when no pair bounds the motion.

    A pair is legal while *some* axis is separated, so it fails only once every axis has gone
    negative.  The set of `t` where one axis is negative is the interval between its two
    crossings of `|proj + t d| = need`; the pair's failure window is the intersection over its
    eight axes, and its cap is that window's start.  An axis outside its window for all
    `t >= 0` (constant and separated, or moving away while separated) empties the
    intersection, so the pair never fails and contributes no cap.
    """
    n = len(pf)
    caps = []
    for cell, dc in dirs.items():
        for k in range(n):
            if k in dirs:
                continue
            i, j = (k, cell) if k < cell else (cell, k)
            lo = hi = None
            never = False
            for proj, need, q in K.pair_axes(pf, wf, i, j):
                dq = dc[0] * q[0] + dc[1] * q[1]
                delta = dq if cell == j else -dq
                slack = abs(proj) - need
                if delta.sign() == 0:
                    if slack.sign() >= 0:
                        never = True
                        break
                    continue
                if slack.sign() >= 0 and (proj.sign() * delta.sign()) >= 0:
                    never = True                 # separated and moving away: never fails
                    break
                a = (-need - proj) / delta
                b = (need - proj) / delta
                if a > b:
                    a, b = b, a
                lo = a if lo is None or a > lo else lo
                hi = b if hi is None or b < hi else hi
            if never:
                continue
            if lo is None:
                caps.append(ZERO)                # every axis already negative: violated
                continue
            if hi is not None and lo > hi:
                continue                         # the windows miss: the pair never fails
            caps.append(lo if lo.sign() > 0 else ZERO)
    if not caps:
        return None
    return min(caps)


def inward_of(side, d):
    """Whether the direction pulls the cell off the given wall."""
    return {"lo_x": d[0].sign() > 0, "hi_x": d[0].sign() < 0,
            "lo_y": d[1].sign() > 0, "hi_y": d[1].sign() < 0}[side]


def tight_graph(pf, wf):
    """Every pair whose SAT slack is exactly 0, with the axis that witnesses it."""
    n = len(pf)
    g = [[] for _ in range(n)]
    for i in range(n):
        xi, yi = pf[i]
        for j in range(i + 1, n):
            if abs(pf[j][0] - xi) >= 2 or abs(pf[j][1] - yi) >= 2:
                continue
            best = None
            for proj, need, q in K.pair_axes(pf, wf, i, j):
                sl = abs(proj) - need
                if best is None or sl > best[0]:
                    best = (sl, proj, q)
            if best[0].sign() == 0:
                # each cell's own projection: moving `cell` by `t d` changes it by `+t (d.q)`
                g[i].append((j, best[2], -best[1]))
                g[j].append((i, best[2], best[1]))
    return g


def retighten(state, wf, g, cell):
    """The tight graph after translating one cell: only its own pairs can have changed."""
    n = len(state)
    out = [list(row) for row in g]
    out[cell] = []
    for k in range(n):
        if k == cell:
            continue
        out[k] = [e for e in out[k] if e[0] != cell]
        if abs(state[k][0] - state[cell][0]) >= 2 or abs(state[k][1] - state[cell][1]) >= 2:
            continue
        best = None
        for proj, need, q in K.pair_axes(state, wf, cell, k):
            sl = abs(proj) - need
            if best is None or sl > best[0]:
                best = (sl, proj, q)
        if best[0].sign() == 0:
            out[cell].append((k, best[2], -best[1]))
            out[k].append((cell, best[2], best[1]))
    return out


def blocked_by(g, cell, d, inside):
    """The first tight neighbour outside `inside` whose contact the move would narrow."""
    for other, q, proj in g[cell]:
        if other in inside:
            continue
        dq = d[0] * q[0] + d[1] * q[1]
        if (proj.sign() * dq.sign()) < 0:
            return other
    return None


def contact_survives(g, a, da, b, db):
    """Whether the tight contact `a - b` survives the joint move (the shear condition)."""
    for other, q, proj in g[a]:
        if other != b:
            continue
        dq = (da[0] - db[0]) * q[0] + (da[1] - db[1]) * q[1]
        return (proj * dq).sign() >= 0
    return True


def all_contacts_survive(g, dirs):
    for a, da in dirs.items():
        for other, _q, _p in g[a]:
            if other in dirs and other > a:
                if not contact_survives(g, a, da, other, dirs[other]):
                    return False
    return True


def move_cells(pf, dirs, t):
    out = list(pf)
    for cell, d in dirs.items():
        out[cell] = (C._q(pf[cell][0]) + t * d[0], C._q(pf[cell][1]) + t * d[1])
    return out


def quick_side(state, wf, dirs, t):
    """The exact side after the move, with no gate: the cheap filter for a probe."""
    st = move_cells(state, dirs, t)
    return C.bbox_side([(C._q(x), C._q(y)) for x, y in st], wf)


def probe(n, state, wf, dirs, t, base_L, full=True):
    """Move, gate, certify, and report the exact side change.

    `full=False` computes the side and stops: the gate plus the certificate cost an O(N^2)
    pass and are spent only on a move that would actually shrink the box (or on the first few,
    to record that the moves are legal at all).
    """
    L = quick_side(state, wf, dirs, t)
    if not full:
        return {"_L": L, "_t": t, "t": str(t), "cells": sorted(dirs), "L": str(L),
                "dL": str(L - base_L), "shrinks": bool(L < base_L),
                "beyond_rounding": bool(L <= base_L - ROUNDING), "ok": None,
                "violations": None, "clearance": None, "contacts": None,
                "certificate": None, "gated": False}
    st = move_cells(state, dirs, t)
    rep = K.certify_state(n, [(C._q(x), C._q(y)) for x, y in st], wf)
    cert = rep["certificate"] or {}
    return {"_L": L, "_t": t, "t": str(t), "cells": sorted(dirs), "L": str(L),
            "dL": str(L - base_L),
            "shrinks": bool(L < base_L), "beyond_rounding": bool(L <= base_L - ROUNDING),
            "ok": rep["ok"], "violations": rep["violations"],
            "clearance": rep["clearance"], "contacts": rep["contacts"],
            "certificate": cert.get("status"), "gated": True}


# ================================================================== PART 1: chains
def certified_state(n):
    """Reproduce `cand106`'s certified sentence for a census row."""
    row = C.load_rows()[n]
    pf = [(x, y) for x, y, _t in row]
    wf = [R.snap(t)[2] for _x, _y, t in row]
    sv = K.survey_row(pf, wf)
    sl = K.slide_best(pf, wf, sv)
    st = [(C._q(x), C._q(y)) for x, y in (sl["state"] if sl is not None else pf)]
    rep = K.certify_state(n, st, wf)
    return {"n": n, "state": st, "wf": wf, "L": C.bbox_side(st, wf),
            "slide": None if sl is None else {k: sl[k] for k in ("cell", "direction", "t")},
            "rep": rep}


def cumulative(state, wf, cell, d, cap=4):
    """The total inward corridor of one cell: the sum of its successive rooms.

    Each step closes the next contact, so the sum is the largest translation that keeps every
    pair legal, and the stalled state is where the sentence finally blocks the cell.  This is
    what makes the depth-one question quantitative: a corridor the size of the table's polish
    shim means the sentence is jammed at the shim's scale, a corridor of real length does not.
    """
    cur, total, steps = list(state), ZERO, []
    for _ in range(cap):
        r = room_set(cur, wf, {cell: d})
        if r is None:
            steps.append({"room": "unbounded"})
            return None, cur, steps
        if r.sign() <= 0:
            steps.append({"room": "0"})
            return total, cur, steps
        steps.append({"room": str(r)})
        total = total + r
        cur = move_cells(cur, {cell: d}, r)
    return total, cur, steps


def chain_search(n, max_witness=16, verbose=True):
    """The directed depth-one/depth-two tracer on one certified row."""
    t0 = time.time()
    ctx = certified_state(n)
    st, wf = ctx["state"], ctx["wf"]
    L0 = ctx["L"]
    if n in L_CERT and L0 != L_CERT[n]:
        raise AssertionError(f"n={n}: certified side {L0} != run 106's {L_CERT[n]}")
    rec = {"n": n, "N": len(st), "L_certified": str(L0),
           "certificate": (ctx["rep"]["certificate"] or {}).get("status"),
           "slide": ctx["slide"], "wall_cells": 0, "depth1_probes": 0,
           "depth1_open": 0, "corridor_max": None, "corridor_min": None,
           "depth1_room": [], "depth2_walls": 0, "depth2_chains": 0,
           "chains2_open": 0, "pruned_blocker2": 0, "pruned_shear": 0,
           "survivors": 0, "witnesses": [], "best": None, "seconds": None}
    g_base = tight_graph(st, wf)
    rec["tight_pairs"] = sum(len(r) for r in g_base) // 2
    rec["wall_faces"] = {side: len(K.wall_cells(st, wf, side)) for side in K.SIDES}
    seen = set()
    for side in K.SIDES:
        for w in K.wall_cells(st, wf, side):
            rec["wall_cells"] += 1
            for kind in K.DIRS8:
                d = K.direction(kind)
                if not inward_of(side, d):
                    continue
                rec["depth1_probes"] += 1
                total, stalled, steps = cumulative(st, wf, w, d)
                entry = {"side": side, "wall": w, "kind": kind, "steps": steps,
                         "face_cells": len(K.wall_cells(st, wf, side)),
                         "corridor": None if total is None else str(total), "depth": 1}
                if total is not None and total.sign() > 0:
                    rec["depth1_open"] += 1
                    c = total
                    if rec["corridor_max"] is None or c > rec["_corridor_max"]:
                        rec["_corridor_max"], rec["corridor_max"] = c, str(c)
                    if rec["corridor_min"] is None or c < rec["_corridor_min"]:
                        rec["_corridor_min"], rec["corridor_min"] = c, str(c)
                    pr = probe(n, st, wf, {w: d}, total, L0,
                               full=(quick_side(st, wf, {w: d}, total) < L0
                                     or len(rec["depth1_room"]) < 3))
                    entry.update(pr)
                    rec["depth1_room"].append(entry)
                if total is None or total.sign() <= 0:
                    continue
                # depth two, from the stalled state: the chain must free what depth one cannot
                rec["depth2_walls"] += 1
                g = retighten(stalled, wf, g_base, w)
                b1 = blocked_by(g, w, d, {w})
                if b1 is None:
                    continue
                for k1 in K.DIRS8:
                    d1 = K.direction(k1)
                    pair = {w: d, b1: d1}
                    if not all_contacts_survive(g, pair):
                        rec["pruned_shear"] += 1
                        continue
                    b2 = blocked_by(g, b1, d1, pair)
                    if b2 is None:
                        key = (w, kind, b1, k1)
                        if key in seen:
                            continue
                        seen.add(key)
                        r2 = room_set(stalled, wf, pair)
                        if r2 is None or r2.sign() <= 0:
                            continue
                        rec["chains2_open"] += 1
                        rec["survivors"] += 1
                        if len(rec["witnesses"]) < max_witness:
                            pr = probe(n, stalled, wf, pair, r2, L0,
                                       full=(quick_side(stalled, wf, pair, r2) < L0
                                             or len(rec["witnesses"]) < 2))
                            pr.update({"depth": 2, "chain": [w, b1], "kinds": [kind, k1],
                                       "side": side, "corridor": str(total)})
                            rec["witnesses"].append(pr)
                        continue
                    for k2 in K.DIRS8:
                        d2 = K.direction(k2)
                        tri = {w: d, b1: d1, b2: d2}
                        if not all_contacts_survive(g, tri):
                            rec["pruned_shear"] += 1
                            continue
                        if blocked_by(g, b2, d2, tri) is not None:
                            rec["pruned_blocker2"] += 1
                            continue
                        rec["depth2_chains"] += 1
                        r3 = room_set(stalled, wf, tri)
                        if r3 is None or r3.sign() <= 0:
                            continue
                        rec["survivors"] += 1
                        if len(rec["witnesses"]) < max_witness:
                            pr = probe(n, stalled, wf, tri, r3, L0,
                                       full=(quick_side(stalled, wf, tri, r3) < L0
                                             or len(rec["witnesses"]) < 2))
                            pr.update({"depth": 3, "chain": [w, b1, b2],
                                       "kinds": [kind, k1, k2], "side": side,
                                       "corridor": str(total)})
                            rec["witnesses"].append(pr)
    cands = [p for p in rec["witnesses"] + rec["depth1_room"]
             if p["shrinks"] and (p["ok"] is not False)]
    if cands:
        cands.sort(key=lambda p: (p["_L"], p["_t"]))
        rec["best"] = cands[0]
    rec["seconds"] = str(F(int((time.time() - t0) * 100), 100))
    if verbose:
        best = rec["best"]
        print(f"  n={n}: walls={rec['wall_cells']} d1={rec['depth1_probes']} "
              f"d1_open={rec['depth1_open']} corridor=[{rec['corridor_min']},"
              f"{rec['corridor_max']}] d2_walls={rec['depth2_walls']} "
              f"chains2={rec['depth2_chains']} chains2_open={rec['chains2_open']} "
              f"pruned_b2={rec['pruned_blocker2']} shear={rec['pruned_shear']} "
              f"best_dL={None if best is None else best['dL']} ({rec['seconds']} s)")
    return rec


# ==================================================== PART 2: the coupled multi-cell move
def replay_330():
    """Run 106's four moves, exactly, and hand back the 3-overlap state."""
    row = C.load_rows()[330]
    pf = [(x, y) for x, y, _t in row]
    wf = [R.snap(t)[2] for _x, _y, t in row]
    cur, moves = pf, []
    for i, j in PARTS_330:
        mv = K.repair_step(cur, wf, i, j)
        if mv is None:
            raise AssertionError(f"the replay lost the move on pair {(i, j)}")
        moves.append({"pair": [i, j], "cell": mv["cell"], "direction": mv["direction"],
                      "t": mv["t"]})
        cur = mv["state"]
    return [(C._q(x), C._q(y)) for x, y in cur], wf, moves


def near_pairs(pf, wf, cells, reach=REACH):
    """The pairs incident to `cells` whose tightest slack is under `reach` (violations too)."""
    out = {}
    n = len(pf)
    for a in cells:
        for b in range(n):
            if b == a:
                continue
            i, j = (a, b) if a < b else (b, a)
            if (i, j) in out:
                continue
            rows = K.pair_axes(pf, wf, i, j)
            tightest = max(abs(p) - need for p, need, _q in rows)
            if tightest <= reach:
                out[(i, j)] = (rows, tightest)
    return out


def exit_time(proj, need, delta):
    """The smallest `t >= 0` at which `|proj + t d| >= need` on the separating branch."""
    if delta.sign() == 0:
        return None
    target = need if delta.sign() > 0 else -need
    t = (target - proj) / delta
    return None if t.sign() < 0 else t


def local_violations(state, wf, dirs, t, detail=False):
    """The violated pairs of the moved state, exactly.

    Pairs of two unmoved cells cannot change, so only the pairs that touch a moved cell need
    computing -- and the prune is applied on the *moved* coordinates, exactly as the gate's own
    scan does, so this count is the gate's count and not an estimate.
    """
    st = move_cells(state, dirs, t)
    seen, count, out = set(), 0, []
    n = len(st)
    for m in dirs:
        xm, ym = st[m]
        for k in range(n):
            if k == m:
                continue
            if abs(st[k][0] - xm) >= 2 or abs(st[k][1] - ym) >= 2:
                continue
            i, j = (k, m) if k < m else (m, k)
            if (i, j) in seen:
                continue
            seen.add((i, j))
            rows = K.pair_axes(st, wf, i, j)
            slack = max(abs(p) - need for p, need, _q in rows)
            if slack.sign() < 0:
                count += 1
                if detail:
                    out.append({"pair": [i, j], "slack": str(slack)})
    return out if detail else count


def joint_move(pf, wf, dirs, viol, rel):
    """The smallest exact `t` clearing every violated pair, and the debt of the moved state.

    The clearing time of a violated pair is the last of its axes to leave the overlap; the
    joint step is the largest of those times, so the binding pair lands exactly on contact.
    The debt is then *counted*, not filtered: `local_violations` evaluates every pair that
    touches a moved cell at the moved coordinates, which is exactly what the gate will see.
    """
    lower = []
    for a, b, _s in viol:
        i, j = (a, b) if a < b else (b, a)
        best = None
        for proj, need, q in K.pair_axes(pf, wf, i, j):
            t = exit_time(proj, need, rate(dirs, i, j, q))
            if t is not None and (best is None or t < best):
                best = t
        if best is None:
            return None, None              # this violated pair cannot be cleared by the motion
        lower.append(best)
    if not lower:
        return None, None
    t = max(lower)
    if t.sign() <= 0:
        return None, None
    return t, local_violations(pf, wf, dirs, t)


def repair3(max_report=24, verbose=True):
    """Simultaneous 2-cell and 3-cell repair of n = 330's three-overlap cycle."""
    t0 = time.time()
    st, wf, moves = replay_330()
    L0 = C.bbox_side(st, wf)
    sv0 = K.survey_row([(x, y) for x, y in st], wf)
    viol = [(v[0], v[1], v[2]) for v in sv0["violations"]]
    pairs = [tuple(sorted((a, b))) for a, b, _s in viol]
    g = tight_graph(st, wf)
    seeds = sorted({c for a, b, _s in viol for c in (a, b)})
    cluster = sorted(set(seeds) | {o for c in seeds for o, _q, _p in g[c]})
    rel = near_pairs(st, wf, cluster, reach=F(1))
    mobj = {"n": 330, "N": len(st), "L_certified": str(L0), "moves": moves,
            "violations": [{"pair": [a, b], "slack": s} for a, b, s in viol],
            "diagnosable": diagnosable(viol), "violation_weight": len(viol),
            "seeds": seeds, "cluster": cluster, "near_pairs": len(rel),
            "candidates": {"2": 0, "3": 0}, "feasible": {"2": 0, "3": 0},
            "zero_overlap": {"2": 0, "3": 0}, "gated": 0, "gate_zero": 0,
            "min_debt": None, "debt_hist": {}, "nearest": None,
            "gate_certified": 0, "best": None, "attempts": [],
            "hitting_sets": {}, "seconds": None}
    for k in (2, 3):
        mobj["hitting_sets"][str(k)] = sum(
            1 for c in itertools.combinations(cluster, k)
            if all(set(p) & set(c) for p in pairs))
    for k in (2, 3):
        for sub in itertools.combinations(cluster, k):
            if not all(set(p) & set(sub) for p in pairs):
                continue                   # a moved cell that addresses no violation is wasted
            for kinds in itertools.product(K.DIRS8, repeat=k):
                dirs = {sub[i]: K.direction(kinds[i]) for i in range(k)}
                mobj["candidates"][str(k)] += 1
                t, remaining = joint_move(st, wf, dirs, viol, rel)
                if t is None:
                    continue
                mobj["feasible"][str(k)] += 1
                mobj["debt_hist"][str(remaining)] = mobj["debt_hist"].get(str(remaining), 0) + 1
                if mobj["min_debt"] is None or remaining < mobj["min_debt"]:
                    mobj["min_debt"] = remaining
                if remaining:
                    nd = mobj["nearest"]
                    if nd is None or (remaining, t) < (nd["debt"], nd["_t"]):
                        mobj["nearest"] = {
                            "debt": remaining, "_t": t, "k": k, "cells": sorted(sub),
                            "kinds": list(kinds), "t": str(t),
                            "blocked": local_violations(st, wf, dirs, t, detail=True),
                            "L": str(quick_side(st, wf, dirs, t)),
                            "dL": str(quick_side(st, wf, dirs, t) - L0)}
                    continue               # the move leaves debt: not a 0-overlap candidate
                mobj["zero_overlap"][str(k)] += 1
                pr = probe(330, st, wf, dirs, t, L0,
                           full=(mobj["gated"] < 24
                                 or quick_side(st, wf, dirs, t) < L0))
                if pr["gated"]:
                    mobj["gated"] += 1
                    if pr["violations"] == 0:
                        mobj["gate_zero"] += 1
                    if pr["certificate"] == "verified":
                        mobj["gate_certified"] += 1
                pr["tax_mog"] = str(tax_mog_units(k, 0))
                pr["k"] = k
                pr["kinds"] = list(kinds)
                if len(mobj["attempts"]) < max_report:
                    mobj["attempts"].append(pr)
                key = (F(pr["tax_mog"]), pr["_t"])
                if mobj["best"] is None or key < (F(mobj["best"]["tax_mog"]),
                                                  mobj["best"]["_t"]):
                    mobj["best"] = pr
    mobj["seconds"] = str(F(int((time.time() - t0) * 100), 100))
    if verbose:
        b = mobj["best"]
        print(f"  n=330: viol={len(viol)} cluster={cluster} near={len(rel)} "
              f"cands={mobj['candidates']} feas={mobj['feasible']} "
              f"zero={mobj['zero_overlap']} best_tax={None if b is None else b['tax_mog']} "
              f"({mobj['seconds']} s)")
    return mobj


# ====================================================================== the controls
def selftest():
    ok = 0

    # 1. the corrected pair rule, against the knight pair that exposed run 106's
    pf = [(Q2(HALF), Q2(HALF)), (Q2(F(3, 2)), Q2(F(5, 2)))]      # dx = 1, dy = 2
    wf = [(ONE, ZERO), (ONE, ZERO)]
    d = K.direction("x")
    moving = [(str(abs(p) - n), str(rate({0: d}, 0, 1, q))) for p, n, q in
              K.pair_axes(pf, wf, 0, 1) if rate({0: d}, 0, 1, q).sign() != 0]
    assert room_set(pf, wf, {0: d}) is None, "the knight pair must not cap an x-move"
    old = K.wall_room(pf, wf, 0, d)
    assert old is not None and old == ZERO, f"run 106's rule reads 0 here, got {old}"
    print("control 1 -- the corrected pair rule: a knight pair (dx = 1, dy = 2) is separated "
          f"along y and stays so under any x-move (its moving-axis rows are {moving}), so its "
          "cap is unbounded; run 106's `wall_room` reads 0 because a narrowing axis sits at "
          "slack 0.  `room_set` says None where `wall_room` says 0 -- the difference every "
          "part-1 verdict is read against.")
    ok += 1

    # 2. readCost: exact values, the AM-GM ceiling, and the irrational optimum
    assert read_cost(2, 1) == F(1, 3) and read_cost(2, 2) == F(1, 3)
    assert read_cost(2, 1) == read_cost_eq(2, 1) == read_cost_eq(2, 2)
    ceiling = read_ceiling(2)
    assert ceiling == Q2(F(0), F(1, 4)), "the ceiling must be sqrt2/4 exactly"
    eff = read_efficiency(2, 1)
    assert eff == Q2(F(0), F(2, 3)), f"the efficiency must be 2sqrt2/3, got {eff}"
    assert eff < ONE, "no integer loop-check reaches the ceiling"
    for t in (F(1, 3), F(1, 2), F(1), F(2), F(5, 2), F(7), F(22, 7)):
        assert C._q(read_cost(2, t)) < ceiling, f"readCost above its ceiling at t = {t}"
        assert (C._q(t) - Q2(F(0), ONE.a)) * (C._q(t) - Q2(F(0), ONE.a)) > 0
    print(f"control 2 -- the observer contract: `readCost(2, Pi) = 1/(Pi + 2/Pi)` is exactly "
          f"1/3 at Pi = 1 and at Pi = 2, the AM-GM ceiling 1/(2 sqrt 2) = sqrt2/4 is the "
          f"field element {ceiling}, and every integer loop-check pays exactly 2 sqrt2/3 = "
          f"{eff} of it -- the ceiling is attained only at Pi = sqrt 2, which no chain count "
          f"can be, so the tracer reads one chain at a time.")
    ok += 1

    # 3. taxMOG: vanishes on a clean unmoved sentence, bounded debt, and its own tie
    assert tax_mog_units(0, 0) == 0, "taxMOG must vanish on a lawful, unmoved sentence"
    assert tax_mog_units(1, 0) > 0 and tax_mog_units(0, 1) > 0
    assert tax_mog_units(2, 1) == tax_mog_units(3, 0) == 3, \
        "a 2-cell repair leaving one pair ties a 3-cell repair that clears all three"
    assert tax_mog_units(0, 5) == F(5) and TAX_W == 1
    print("control 3 -- the syndrome-penalized tax: `taxMOG/Q = (cells moved) + (violated "
          "pairs left)` vanishes exactly on an unmoved lawful sentence, its debt term is the "
          "covering radius (4 quanta), and it is *blind* between a 2-cell repair that leaves "
          "one pair and a 3-cell repair that clears all three -- both 3 units.  The tie is "
          "real, so the exact gate, not the tax, has to decide.")
    ok += 1

    # 4. the MOG contract: <= 3 violations uniquely diagnosable, 4 ambiguous
    cen = diagnosis_census(4)
    assert cen[0]["syndromes"] == 1 and cen[1]["syndromes"] == 24
    for w in (1, 2, 3):
        assert cen[w]["colliding_classes"] == 0, f"weight {w} must be injective"
        assert cen[w]["syndromes"] == cen[w]["patterns"]
    assert cen[4]["colliding_classes"] > 0, "weight 4 must collide"
    # the Lean file's own witnesses, as the `Fin 24` cell indices it writes them with
    u = sum(1 << j for j in (1, 12, 13, 14))
    v = sum(1 << j for j in (16, 17, 18, 22))
    assert u != v and weight(u) == weight(v) == 4 and mog_syndrome(u) == mog_syndrome(v)
    assert diagnosable([1, 2, 3]) and not diagnosable([1, 2, 3, 4])
    print(f"control 4 -- the MOG contract, recomputed over GF(2) from the Lean file's own "
          f"Bmat: weights 0-3 map injectively to syndromes (1, 24, {cen[2]['syndromes']}, "
          f"{cen[3]['syndromes']} classes), weight 4 collides in "
          f"{cen[4]['colliding_classes']} classes, and the Lean witnesses {hex(u)} and "
          f"{hex(v)} share one -- so three violated pairs are named exactly, four would be "
          f"ambiguous, and the n = 330 repair is inside the diagnosable range.")
    ok += 1

    # 5. a sentence jammed at depth one that opens at depth two and shrinks L
    pf5 = [(Q2(HALF), Q2(HALF)), (Q2(F(3, 2)), Q2(HALF)), (Q2(F(7, 2)), Q2(F(5, 2)))]
    wf5 = [(ONE, ZERO), (ONE, ZERO), (ONE, ZERO)]
    g5 = tight_graph(pf5, wf5)
    assert blocked_by(g5, 0, K.direction("x"), {0}) == 1, \
        "the low-x wall cell must be blocked by its right neighbour"
    r1 = room_set(pf5, wf5, {0: K.direction("x")})
    assert r1 is not None and r1 == ZERO, f"depth one must be jammed, got {r1}"
    chain = {0: K.direction("x"), 1: K.direction("x")}
    assert contact_survives(g5, 0, chain[0], 1, chain[1]), "the pair must translate rigidly"
    assert room_set(pf5, wf5, chain) is None, "no pair caps the rigid pair"
    L0 = C.bbox_side(pf5, wf5)
    pr = probe(3, pf5, wf5, chain, ONE, L0)
    assert pr["ok"] and pr["clearance"] == "0" and pr["certificate"] == "verified", pr
    assert pr["shrinks"] and F(pr["L"]) == L0 - 1, (pr["L"], L0)
    print(f"control 5 -- depth one jammed, depth two open: three squares in a row plus one "
          f"cell setting the far wall.  The low-x wall cell has exactly 0 room (its right "
          f"neighbour is a tight contact), the two-cell chain {{0, 1}} has no cap at all (the "
          f"pair translates rigidly), and the probe at t = 1 shrinks the box from {L0} to "
          f"{pr['L']}, gates clean and certifies -- the mechanism part 1 looks for.")
    ok += 1

    # 6. three coupled overlaps: two cells cannot hit three pairs, three can, simultaneously
    pf6, wf6 = [], [(ONE, ZERO)] * 6
    for row_y in (HALF, F(5, 2), F(9, 2)):
        pf6.append((Q2(HALF), Q2(row_y)))
        pf6.append((Q2(F(7, 5)), Q2(row_y)))          # dx = 9/10: a 1/10 overlap
    sv6 = K.survey_row([(x, y) for x, y in pf6], wf6)
    v6 = [(v[0], v[1], v[2]) for v in sv6["violations"]]
    assert len(v6) == 3, f"three overlaps must be seen, got {v6}"
    assert diagnosable(v6), "three violations are inside the MOG's diagnosis range"
    pairs6 = [tuple(sorted((a, b))) for a, b, _s in v6]
    hitting2 = [sub for sub in itertools.combinations(range(6), 2)
                if all(set(p) & set(sub) for p in pairs6)]
    assert not hitting2, "no two cells can hit three disjoint pairs"
    partial, _debt = joint_move(pf6, wf6, {1: K.direction("x"), 3: K.direction("x")}, v6,
                                near_pairs(pf6, wf6, (1, 3)))
    assert partial is None, "a 2-cell move cannot clear the third, untouched pair"
    dirs6 = {1: K.direction("x"), 3: K.direction("x"), 5: K.direction("x")}
    t6, debt6 = joint_move(pf6, wf6, dirs6, v6, near_pairs(pf6, wf6, (1, 3, 5)))
    assert debt6 == 0, "the three-cell step must leave no debt"
    assert t6 is not None and t6 == F(1, 10), f"the joint step must be exactly 1/10, got {t6}"
    pr6 = probe(6, pf6, wf6, dirs6, t6, C.bbox_side(pf6, wf6))
    assert pr6["ok"] and pr6["violations"] == 0 and pr6["certificate"] == "verified", pr6
    print(f"control 6 -- three coupled overlaps: three disjoint 1/10 violations (the MOG's "
          f"diagnosable weight, so the fault set is named exactly).  Two cells cannot hit "
          f"three disjoint pairs ({len(hitting2)} hitting sets of size 2, and a 2-cell move "
          f"leaves the third pair broken), while moving one cell of each pair by exactly 1/10 "
          f"clears all three at once, gates at clearance 0 with {pr6['contacts']} contacts "
          f"and certifies -- at taxMOG 3 units, tying the 2-cell alternative of control 3.")
    ok += 1

    print(f"observer_chain: OK ({ok} controls)")
    return ok


# ========================================================================= the runs
def strip_private(obj):
    """Drop the exact-object keys (`_L`, `_t`) that JSON cannot carry."""
    if isinstance(obj, dict):
        return {k: strip_private(v) for k, v in obj.items()
                if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(obj, list):
        return [strip_private(v) for v in obj]
    return obj


def merge(section, data):
    data = strip_private(data)
    led = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            led = json.load(f)
    led.setdefault("run", 107)
    led.setdefault("delivered", "22.218056945")
    led["sections"] = sorted(set(led.get("sections", [])) | {section})
    led[section] = data
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"observer_chain: {section} -> {OUT}")


def run_chain():
    out = {"rows": {}, "contracts": {
        "read_cost_Pi1": str(read_cost(2, 1)),
        "read_cost_Pi2": str(read_cost(2, 2)),
        "read_ceiling": str(read_ceiling(2)),
        "read_efficiency": str(read_efficiency(2, 1)),
        "tax_units": {"2cell_1left": str(tax_mog_units(2, 1)),
                      "3cell_0left": str(tax_mog_units(3, 0))},
        "diagnosis": diagnosis_census(4)}}
    for n in (66, 325):
        out["rows"][str(n)] = chain_search(n)
    merge("chain", out)
    return out


def run_repair3():
    out = repair3()
    out["contracts"] = {"tax_tie": str(tax_mog_units(2, 1)),
                        "diagnosis_limit": DIAG_LIMIT,
                        "read_efficiency": str(read_efficiency(2, 1))}
    merge("repair3", out)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return 0
    if "--chain" in argv:
        run_chain()
        return 0
    if "--repair3" in argv:
        run_repair3()
        return 0
    run_chain()
    run_repair3()
    return 0


if __name__ == "__main__":
    sys.exit(main())
