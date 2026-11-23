#!/usr/bin/env python3
"""rat47pos.py — run 104, part 1: an exact positional repair of the rung's last pair.

Run 103's word repair swapped nothing: the `2k + 4/7` rows miss being exact sentences
by one or two **pairs**, not by one or two angles.  n = 788 misses by `2e-11` on a
single pair (cells 195, 217), both axis words, at `dx = 1 - 2e-11` and
`dy = 1 - 2.9e-6`.  So the missing move is a *translation*, and this script tests the
one the brief asks for: move **one** cell of the offending pair, keep every
orientation, and let the exact gate and the verifier decide.

What is exact here
------------------
    the projection, the requirement, the slack   Fractions (the snapped words are
                                                 rational-t words, so b = 0)
    the feasible translation set                 a union of closed intervals with
                                                 rational endpoints, intersected
                                                 exactly; no tolerance appears
    the witness                                  the far endpoint of the interval
                                                 containing the first feasible
                                                 move, so some pair is in *exact*
                                                 contact and clearance is exactly 0
    the verdict                                  qsqrt2.gate, then
                                                 verify_certificates.verify_certificate
                                                 on a `galois-certificate/1`

`SPAN` is a declared search window (half a cell), not a tolerance: every candidate
outside it is simply not tried, and every candidate inside it is decided exactly.

The second question the brief asks — whether the rung closes *at* `2k + 4/7` — is
answered by comparing the witness's exact side with the rung as a Fraction, and by
the `compaction` block: to reach the rung, every cell on the offending wall has to
move inward by the exact excess, and each such cell has its own exact room.  The two
numbers are printed side by side.

Usage:
    python3 scripts/rat47pos.py              # the four rung rows, ledger
    python3 scripts/rat47pos.py --selftest
"""
from __future__ import annotations

import collections
import json
import math
import os
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import glm_wheels as W            # noqa: E402
import landscape65 as L           # noqa: E402
import qsqrt2 as Q                # noqa: E402
import rat47 as R                 # noqa: E402
import verify_certificates as VC  # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/rat47pos.json")

#: the four rows doc 65 named, and their rung side `m + 4/7` exactly
TARGETS = (680, 733, 788, 845)
RUNG = {680: F(186, 7), 733: F(193, 7), 788: F(200, 7), 845: F(207, 7)}
HALF = F(1, 2)
TWO = F(2)
SPAN = F(1, 2)          # the declared window for one cell's translation, in cells


# ------------------------------------------------------------- exact interval sets
# An interval set is a sorted list of disjoint closed intervals `(lo, hi)` of
# Fractions, always inside `[-SPAN, SPAN]`, so no infinity sentinel is needed.
def iset_union(a, b):
    """The union of two interval sets, merged."""
    merged = []
    for lo, hi in sorted(list(a) + list(b)):
        if merged and lo <= merged[-1][1]:
            if hi > merged[-1][1]:
                merged[-1] = (merged[-1][0], hi)
        else:
            merged.append((lo, hi))
    return merged


def iset_intersect(a, b):
    """The intersection of two interval sets, exactly."""
    out = []
    for lo1, hi1 in a:
        for lo2, hi2 in b:
            lo = lo1 if lo1 > lo2 else lo2
            hi = hi1 if hi1 < hi2 else hi2
            if lo <= hi:
                out.append((lo, hi))
    return iset_union(out, [])


def iset_min_from(s, t0=F(0)):
    """The smallest `t >= t0` in the set, or None."""
    best = None
    for lo, hi in s:
        if hi < t0:
            continue
        t = lo if lo > t0 else t0
        if best is None or t < best:
            best = t
    return best


def iset_component(s, t):
    """The interval of the set that contains `t`, or None."""
    for lo, hi in s:
        if lo <= t <= hi:
            return (lo, hi)
    return None


def ray(s0, step, need, span=SPAN):
    """The `t` in `[-span, span]` with `|s0 + t*step| >= need`, as interval sets.

    One SAT axis of one pair, exactly: the two roots are rational, the set is the
    two outer rays clipped to the window.
    """
    if step == 0:
        return [(-span, span)] if abs(s0) >= need else []
    a = (-need - s0) / step
    b = (need - s0) / step
    if a > b:
        a, b = b, a
    out = []
    if -span <= a:
        out.append((-span, a if a < span else span))
    if b <= span:
        out.append((b if b > -span else -span, span))
    return [iv for iv in out if iv[0] <= iv[1]]


# ---------------------------------------------------------------- rational mirror
# The positional repair never leaves Q: every snapped word is a rational-t word, so
# cos, sin and every extent are Fractions.  These four helpers mirror
# qsqrt2.frame_extent / axis_extent / pair_axes in Q, and the selftest cross-checks
# them against that module row by row.
def word_frac(word):
    """A Q2 word as a Fraction pair, refusing a word with an irrational part."""
    if word[0].b != 0 or word[1].b != 0:
        raise ValueError("the positional repair runs on rational words only")
    return (word[0].a, word[1].a)


def extent(word):
    """The bbox half-extent of a unit square with this word (the same on both axes)."""
    c, s = word
    return (abs(c) + abs(s)) * HALF


def axes_of(word):
    """The square's own two frame axes, `u = (c, s)` and `v = (-s, c)`."""
    c, s = word
    return ((c, s), (-s, c))


def pair_axes_q(pf, wf, i, j):
    """The eight `(signed projection, need)` rows of pair `(i, j)`, in Q."""
    dx = pf[j][0] - pf[i][0]
    dy = pf[j][1] - pf[i][1]
    out = []
    for owner, other in ((i, j), (j, i)):
        oc, os_ = wf[other]
        for qx, qy in axes_of(wf[owner]):
            need = HALF + (abs(oc * qx + os_ * qy) + abs(oc * qy - os_ * qx)) * HALF
            out.append((dx * qx + dy * qy, need))
    return out


def pair_slack_q(pf, wf, i, j):
    """A pair's clearance in Q: the **largest** of its eight axis slacks."""
    best = None
    for proj, need in pair_axes_q(pf, wf, i, j):
        sl = abs(proj) - need
        if best is None or sl > best:
            best = sl
    return best


def constraints_q(pf, wf, i, j, d):
    """`(s0, step, need)` for pair `(i, j)` when cell `j` moves by `t*d`."""
    dx = pf[j][0] - pf[i][0]
    dy = pf[j][1] - pf[i][1]
    out = []
    for owner, other in ((i, j), (j, i)):
        oc, os_ = wf[other]
        for qx, qy in axes_of(wf[owner]):
            need = HALF + (abs(oc * qx + os_ * qy) + abs(oc * qy - os_ * qx)) * HALF
            out.append((dx * qx + dy * qy, d[0] * qx + d[1] * qy, need))
    return out


def box_q(pf, wf):
    """The sentence's exact container box `(lo, hi)`, as Fractions."""
    ex = [extent(wf[i]) for i in range(len(pf))]
    lo = (min(pf[i][0] - ex[i] for i in range(len(pf))),
          min(pf[i][1] - ex[i] for i in range(len(pf))))
    hi = (max(pf[i][0] + ex[i] for i in range(len(pf))),
          max(pf[i][1] + ex[i] for i in range(len(pf))))
    return lo, hi


def low_edge(pf, wf, i, axis):
    """The cell's bbox low edge along `axis` (x if 0, y if 1)."""
    return pf[i][axis] - extent(wf[i])


def violations_q(pf, wf):
    """Every overlapping pair, exactly, with the same prune the gate uses."""
    out = []
    n = len(pf)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(pf[j][0] - pf[i][0]) >= TWO or abs(pf[j][1] - pf[i][1]) >= TWO:
                continue
            s = pair_slack_q(pf, wf, i, j)
            if s is not None and s < 0:
                out.append((i, j, s))
    return out


def gate_q(pf, wf):
    """The exact gate on a rational sentence (Q2 coordinates, b = 0)."""
    state = [(Q.Q2(pf[i][0]), Q.Q2(pf[i][1])) for i in range(len(pf))]
    words = [(Q.Q2(wf[i][0]), Q.Q2(wf[i][1])) for i in range(len(wf))]
    return Q.gate(state, words)


# ------------------------------------------------------------------- feasible moves
def feasible(pf, wf, j, d, lo, hi, span=SPAN):
    """The exact `t`-set in `[-span, span]` where moving cell `j` by `t*d` is legal.

    Legal means: every pair incident to `j` is separated on some SAT axis (exactly,
    as a union of rational intervals per pair, intersected over the pairs), and `j`
    still lies inside the container box `[lo, hi]` so the side cannot grow.

    Pairs the gate would prune for **every** `t` in the window are skipped: the gate
    skips a pair when `|dx| >= 2` or `|dy| >= 2`, so a pair can only matter here if
    `|dx| < 2 + span` and `|dy| < 2 + span`; anything else is skipped by both.
    """
    out = [(-span, span)]
    ex = extent(wf[j])
    for ax in (0, 1):
        if d[ax] == 0:
            continue
        a = (lo[ax] + ex - pf[j][ax]) / d[ax]
        b = (hi[ax] - ex - pf[j][ax]) / d[ax]
        if a > b:
            a, b = b, a
        out = iset_intersect(out, [(a, b)])
        if not out:
            return []
    for i in range(len(pf)):
        if i == j:
            continue
        if (abs(pf[j][0] - pf[i][0]) >= TWO + span
                and abs(pf[j][1] - pf[i][1]) >= TWO + span):
            continue
        pair = []
        for s0, step, need in constraints_q(pf, wf, i, j, d):
            pair = iset_union(pair, ray(s0, step, need, span))
        out = iset_intersect(out, pair)
        if not out:
            return []
    return out


def directions_q(wf, i, j):
    """The distinct SAT axis directions of the pair (both signs), in a fixed order."""
    out, seen = [], set()
    for owner in (i, j):
        for q in axes_of(wf[owner]):
            for d in (q, (-q[0], -q[1])):
                if d in seen:
                    continue
                seen.add(d)
                out.append(d)
    return out


def candidates(pf, wf, i, j, lo, hi, span=SPAN):
    """Every one-cell translation that separates the pair, shortest first.

    Each entry is `(t_first, t_far, target, direction, interval)`.  `t_first` is the
    first feasible move away from the delivered pose: it is the boundary at which the
    offending pair's own constraint turns non-negative, so the pair is in **exact**
    contact there and clearance is exactly 0.  `t_far` is the far end of the same
    feasible interval — the other tight point, when the interval is not clipped by
    the declared window.
    """
    out = []
    for target in (i, j):
        for d in directions_q(wf, i, j):
            fs = feasible(pf, wf, target, d, lo, hi, span)
            t = iset_min_from(fs, F(0))
            if t is None or t == 0:
                continue
            span_iv = iset_component(fs, t)
            out.append((t, span_iv[1], target, d, span_iv))
    out.sort(key=lambda c: (c[0], c[2], c[3]))
    return out


def moved(pf, target, d, t):
    """The sentence with cell `target` translated by `t*d` (exact)."""
    out = list(pf)
    out[target] = (pf[target][0] + d[0] * t, pf[target][1] + d[1] * t)
    return out


# ---------------------------------------------------------------------- certification
def certify(n, pf, wf):
    """Gate the sentence in its own box and, if it is tight, verify a certificate."""
    lo, _hi = box_q(pf, wf)
    state = [(x - lo[0], y - lo[1]) for x, y in pf]
    g = gate_q(state, wf)
    rec = {"ok": bool(g["ok"]), "L": str(g["L"]), "contacts": g["contacts"],
           "violations": g["violations"],
           "clearance": None if g["clearance"] is None else str(g["clearance"]),
           "certificate": None}
    if g["ok"] and g["clearance"] is not None and g["clearance"].sign() == 0:
        qstate = [(Q.Q2(x), Q.Q2(y)) for x, y in state]
        qwords = [(Q.Q2(c), Q.Q2(s)) for c, s in wf]
        cert = L.certificate_of_lift(n, {"state": qstate, "L": g["L"],
                                         "contacts": g["contacts"]}, qwords)
        try:
            v = VC.verify_certificate(cert)
            rec["certificate"] = {"status": v["status"], "N": v["N"],
                                  "contacts": v["contacts"], "L": v["L"],
                                  "clearance": v["clearance"], "void": v["void"]}
        except VC.Failure as f:
            rec["certificate"] = {"status": "refused", "kind": f.kind,
                                  "check": f.check, "detail": f.detail}
    return rec


# ------------------------------------------------------------------- the compaction
def compaction(pf, wf, rung):
    """Could the delivered pose be shrunk to the rung by moving whole walls in?

    `L - rung` is the exact excess.  To remove it, **every** cell that realises the
    wide direction has to move inward by at least that much; each such cell has its
    own exact inward room from `feasible`.  The two numbers decide the question, and
    a single cell's room is *not* the whole story only if the wall cells disagree.
    """
    lo, hi = box_q(pf, wf)
    span = (hi[0] - lo[0]) if (hi[0] - lo[0]) > (hi[1] - lo[1]) else (hi[1] - lo[1])
    excess = span - rung
    rec = {"side": str(span), "rung": str(rung), "excess": str(excess),
           "excess_decimal": str(L._dec(excess)), "fits": excess <= 0, "walls": []}
    for ax, sign in ((0, -1), (1, -1), (0, 1), (1, 1)):
        edges = [low_edge(pf, wf, i, ax) if sign < 0 else
                 pf[i][ax] + extent(wf[i]) for i in range(len(pf))]
        extreme = (min(edges) if sign < 0 else max(edges))
        who = [i for i in range(len(pf)) if edges[i] == extreme]
        d = (-sign, F(0)) if ax == 0 else (F(0), -sign)
        rooms = []
        for i in who:
            fs = feasible(pf, wf, i, d, lo, hi)
            t = iset_min_from(fs, F(0))
            if t is None:
                rooms.append(None)
            else:
                iv = iset_component(fs, t)
                rooms.append(iv[1])
        known = [r for r in rooms if r is not None]
        rec["walls"].append({
            "axis": "x" if ax == 0 else "y", "side": "low" if sign < 0 else "high",
            "cells": len(who), "room_min": str(min(known)) if known else None,
            "room_max": str(max(known)) if known else None,
            "blocked": sum(1 for r in rooms if r is None)})
    wide = "x" if (hi[0] - lo[0]) >= (hi[1] - lo[1]) else "y"
    rooms = [w for w in rec["walls"] if w["axis"] == wide and w["side"] == "high"]
    rec["wide_axis"] = wide
    rec["wide_room_min"] = rooms[0]["room_min"] if rooms else None
    rec["wall_can_shrink"] = bool(rooms and rooms[0]["room_min"] is not None
                                 and F(rooms[0]["room_min"]) >= excess)
    return rec


# --------------------------------------------------------------------- the lattice
def grid(pf, rung):
    """The delivered pose's coordinate grid, and whether the rung sits on it.

    Every coordinate of the row is a Fraction; `D` is the lcm of their denominators,
    so every coordinate is an integer multiple of `1/D` by construction.  The rung's
    own side `m + 4/7` has denominator 7, and 7 does **not** divide `D` in any of the
    four rows: a sentence whose walls sit at the rung needs coordinates off the
    delivered grid.  Rounding this pose can therefore only make the moved pair
    *tight* at the delivered side; it cannot put the side at the rung.
    """
    D = 1
    for x, y in pf:
        for v in (x, y):
            D = D * v.denominator // _gcd(D, v.denominator)
    return {"D": D, "quantum": str(F(1, D)),
            "quantum_decimal": str(L._dec(F(1, D))),
            "rung_denominator": rung.denominator,
            "rung_on_grid": D % rung.denominator == 0}


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


# -------------------------------------------------------------------------- one row
def target(n, row):
    """One rung row: the delivered pose, its pair(s), the exact repair, the verdict."""
    start = time.time()
    pf = [(x, y) for x, y, _t in row]
    sn = [R.snap(t) for _x, _y, t in row]
    names = [s[0] for s in sn]
    wf = [word_frac(s[2]) for s in sn]
    lo, hi = box_q(pf, wf)
    base_gate = gate_q(pf, wf)
    bad = violations_q(pf, wf)
    rec = {"n": n, "N": len(pf), "m": math.isqrt(len(pf) - 4), "rung": str(RUNG[n]),
           "delivered_side": str(base_gate["L"]),
           "grid": grid(pf, RUNG[n]),
           "base": {"ok": bool(base_gate["ok"]), "contacts": base_gate["contacts"],
                    "violations": base_gate["violations"],
                    "clearance": str(base_gate["clearance"])},
           "pairs": [], "steps": [], "repair": None, "compaction": None,
           "verdict": None, "seconds": None}
    for i, j, s in bad:
        rows = []
        seen = set()
        for proj, need in pair_axes_q(pf, wf, i, j):
            key = (proj, need)
            if key in seen:
                continue
            seen.add(key)
            rows.append([str(proj), str(need), str(abs(proj) - need)])
        rec["pairs"].append({
            "cells": [i, j], "words": [names[i], names[j]],
            "dx": str(pf[j][0] - pf[i][0]), "dy": str(pf[j][1] - pf[i][1]),
            "slack": str(s), "slack_decimal": str(L._dec(s)),
            "axes": rows})

    # repair the pairs one at a time: each accepted move is gated and, if tight,
    # certified; the next pair is then read off the *repaired* pose
    cur = list(pf)
    for step in range(4):
        lo, hi = box_q(cur, wf)
        bad = violations_q(cur, wf)
        if not bad:
            break
        i, j, s0 = bad[0]
        cands = candidates(cur, wf, i, j, lo, hi)
        best = None
        # a row with two offending pairs cannot be closed by one move, so a candidate
        # is judged by the *whole* gate: the one that leaves the fewest overlaps is
        # taken, and a tight one (clearance exactly 0) wins any tie.  The gate is the
        # only judge; `violations_q` only orders the candidates.
        for t_first, t_far, tgt, d, iv in cands:
            points = [t_first] if t_far == t_first else [t_first, t_far]
            for t_wit in points:
                trial = moved(cur, tgt, d, t_wit)
                g = gate_q(trial, wf)
                tight = bool(g["ok"]) and g["clearance"] is not None \
                    and g["clearance"].sign() == 0
                entry = {"pair": [i, j], "slack_before": str(s0),
                         "target": tgt, "direction": [str(d[0]), str(d[1])],
                         "t_first": str(t_first),
                         "t_first_decimal": str(L._dec(t_first)),
                         "t_witness": str(t_wit),
                         "t_witness_decimal": str(L._dec(t_wit)),
                         "interval": [str(iv[0]), str(iv[1])],
                         "tight": tight,
                         "gate": {"ok": bool(g["ok"]), "violations": g["violations"],
                                  "contacts": g["contacts"],
                                  "clearance": str(g["clearance"]),
                                  "L": str(g["L"])}}
                rec["steps"].append(entry)
                score = (g["violations"], 0 if tight else 1, len(rec["steps"]))
                if best is None or score < best[0]:
                    best = (score, entry, trial)
                if score[0] == 0 and score[1] == 0:
                    break
            if best is not None and best[0][0] == 0 and best[0][1] == 0:
                break
        if best is None or best[0][0] >= len(bad):
            break
        cur = best[2]

    rec["repair"] = certify(n, cur, wf)
    lo, hi = box_q(cur, wf)
    side = (hi[0] - lo[0]) if (hi[0] - lo[0]) > (hi[1] - lo[1]) else (hi[1] - lo[1])
    excess = side - RUNG[n]
    rec["side"] = str(side)
    rec["side_decimal"] = str(L._dec(side))
    rec["side_excess"] = str(excess)
    rec["side_excess_decimal"] = str(L._dec(excess))
    rec["position"] = "at" if excess == 0 else ("above" if excess > 0 else "below")
    rec["compaction"] = compaction(pf, wf, RUNG[n])
    if not rec["repair"]["ok"]:
        rec["verdict"] = "refused"
    elif (rec["repair"].get("certificate") or {}).get("status") == "verified":
        rec["verdict"] = "closed-" + rec["position"] + "-rung"
    else:
        rec["verdict"] = "closed-" + rec["position"] + "-rung-uncertified"
    rec["seconds"] = round(time.time() - start, 1)
    return rec


# ------------------------------------------------------------------------- the run
def run():
    rows = W._delivered_rows()
    recs = []
    for n in TARGETS:
        print(f"  n = {n}: pairs, exact repair, certificate …", flush=True)
        r = target(n, rows[n])
        print(f"      {r['verdict']}  side {r['side_decimal'][:18]} "
              f"({r['side_excess_decimal'][:10]} vs rung)", flush=True)
        recs.append(r)
    res = {"run": 104, "part": 1, "targets": list(TARGETS),
           "rung": {str(k): str(v) for k, v in RUNG.items()},
           "span": str(SPAN), "runs": recs,
           "tally": dict(collections.Counter(r["verdict"] for r in recs)),
           "identity": ("rat47pos: the rung's missing move is positional; one cell of "
                        "the offending pair is translated along a SAT axis of the pair, "
                        "the feasible set is an exact interval union in Q, the witness is "
                        "its far endpoint (clearance exactly 0), and the certificate is "
                        "verified by verify_certificates; the side is compared with "
                        "m + 4/7 as a Fraction")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    return res


# ------------------------------------------------------------------------ selftest
def selftest():
    """Five controls: the mirror, the interval algebra, the repair, a refusal, the rung."""
    print("rat47pos selftest")
    # 1. the rational mirror agrees with qsqrt2 on a four-cell rational sentence
    pf = [(F(0), F(0)), (F(1), F(0)), (F(11, 10), F(0)), (F(0), F(3, 2))]
    wf = [word_frac(Q.AXIS), word_frac(Q.AXIS),
          word_frac(L._word_from_t(F(1, 2))), word_frac(L._word_from_t(F(1, 3)))]
    qstate = [(Q.Q2(x), Q.Q2(y)) for x, y in pf]
    qwords = [(Q.Q2(c), Q.Q2(s)) for c, s in wf]
    for i in range(len(pf)):
        for j in range(i + 1, len(pf)):
            mine = pair_slack_q(pf, wf, i, j)
            theirs = max(s for _q, s, _n, _o in Q.pair_axes(qstate, qwords, i, j))
            assert Q.Q2(mine) == theirs, (i, j, mine, theirs)
    print("  control 1 — the Q mirror of pair_axes agrees with qsqrt2.pair_axes on all "
          "6 pairs (8 axes each), exactly")
    # 2. interval algebra against hand-computed sets
    a = [(F(-1, 2), F(-1, 4)), (F(1, 4), F(1, 2))]
    b = [(F(-1, 2), F(0)), (F(1, 5), F(1, 2))]
    assert iset_intersect(a, b) == [(F(-1, 2), F(-1, 4)), (F(1, 4), F(1, 2))]
    assert iset_union([(F(0), F(1, 4))], [(F(1, 4), F(1, 3))]) == [(F(0), F(1, 3))]
    assert iset_min_from(a, F(0)) == F(1, 4)
    assert iset_component(a, F(-1, 3)) == (F(-1, 2), F(-1, 4))
    assert ray(F(0), F(1), F(1, 4), F(1)) == [(F(-1), F(-1, 4)), (F(1, 4), F(1))]
    print("  control 2 — interval union/intersection, the first move, the component and "
          "a ray are exact on hand-computed sets")
    # 3. a pair short by 1/100 is closed by one exact translation, at clearance 0
    pf2 = [(F(0), F(0)), (F(1) - F(1, 100), F(0)), (F(3), F(0))]
    wf2 = [word_frac(Q.AXIS)] * 3
    lo, hi = box_q(pf2, wf2)
    cands = candidates(pf2, wf2, 0, 1, lo, hi)
    assert cands, "no candidate for a pair that is short by 1/100"
    t_first, t_far, tgt, d, iv = cands[0]
    assert t_first == F(1, 100), t_first
    rep = certify(3, moved(pf2, tgt, d, t_first), wf2)
    assert rep["ok"] and rep["clearance"] == "0", rep
    assert (rep["certificate"] or {}).get("status") == "verified", rep["certificate"]
    print(f"  control 3 — a pair short by 1/100 is closed by one translation of {t_first} "
          f"(cell {tgt}, interval to {t_far}), at clearance exactly 0, and the "
          f"certificate verifies at L = {rep['L'][:8]} with {rep['contacts']} contact")
    # 4. a neighbour packed at exactly one cell blocks the move: nothing is taken
    pf3 = [(F(0), F(0)), (F(1) - F(1, 100), F(0)), (F(2) - F(1, 100), F(0))]
    wf3 = [word_frac(Q.AXIS)] * 3
    lo, hi = box_q(pf3, wf3)
    assert not candidates(pf3, wf3, 0, 1, lo, hi), "a blocked move was accepted"
    print("  control 4 — with a third square packed one cell from the free side, every "
          "feasible interval is empty and no move is taken")
    # 5. the rung arithmetic on the delivered 788: the side misses 200/7 by a grid step
    rows = W._delivered_rows()
    row = rows[788]
    pf5 = [(x, y) for x, y, _t in row]
    wf5 = [word_frac(R.snap(t)[2]) for _x, _y, t in row]
    g5 = gate_q(pf5, wf5)
    side = g5["L"]
    assert side.b == 0
    excess = side.a - RUNG[788]
    assert excess == F(13513, 7 * 10 ** 12), excess
    gr = grid(pf5, RUNG[788])
    assert gr["D"] == 10 ** 12, gr
    assert gr["rung_on_grid"] is False, gr
    print(f"  control 5 — 788's delivered side misses 200/7 by exactly {excess} "
          f"(one grid step is {gr['quantum']}), and 7 does not divide the pose's "
          f"denominator {gr['D']}")
    print("rat47pos: OK (5 controls)")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    res = run()
    print(f"span (declared search window): {res['span']}")
    for r in res["runs"]:
        print(f"  n = {r['n']:4d} N = {r['N']:4d} rung {r['rung']:>8}  "
              f"pairs {len(r['pairs'])}  {r['verdict']}")
        for p in r["pairs"]:
            print(f"      pair {p['cells']} {p['words']} slack {p['slack_decimal'][:12]} "
                  f"dx {p['dx'][:14]} dy {p['dy'][:14]}")
        for s in r["steps"]:
            print(f"      move cell {s['target']} by {s['t_witness_decimal'][:12]} along "
                  f"{s['direction']}: gate ok={s['gate']['ok']} "
                  f"clearance {s['gate']['clearance'][:12]} "
                  f"contacts {s['gate']['contacts']} L {s['gate']['L'][:16]}")
        rep = r["repair"]
        cert = (rep.get("certificate") or {}).get("status")
        print(f"      repaired: ok={rep['ok']} clearance {str(rep['clearance'])[:12]} "
              f"contacts {rep['contacts']} cert {cert} L {rep['L'][:18]}")
        print(f"      side {r['side_decimal'][:18]} = rung + {r['side_excess_decimal'][:10]}"
              f" ({r['position']}); wall room {r['compaction']['wide_room_min']} "
              f"vs excess {r['side_excess'][:12]}")
    print(f"tally: {res['tally']}")
    print(f"ledger: {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
