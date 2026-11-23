#!/usr/bin/env python3
"""rat47.py — the `2k + 4/7` rung: a rational-t construction, gated exactly (run 103).

Doc 65 left one production named: the four relaxed rows whose container side is
exactly `2k + 4/7` (n = 680, 733, 788, 845, sides 186/7, 193/7, 200/7, 207/7, counts
`(2k)^2 + 4`).  Their side is cheap — a rational number — and their angles are the
expensive part.  A **rational-t** sentence would fix both: every angle a Pythagorean
word `((1 - t^2)/(1 + t^2), 2t/(1 + t^2))` with `t` rational, every coordinate in Q,
the whole sentence in Q(sqrt 2) with `b = 0`.

This script starts that construction and lets the exact gate arbitrate.  Three parts:

  1. **The strip lemma** (part 1, exact and exhaustive over the alphabet): every unit
     square's bounding-box width is `|cos| + |sin| >= 1`, with equality exactly at the
     axis word.  So no sentence of unit squares can put a square into a gap narrower
     than 1 — in particular a margin of `4/7` holds no square at all, and the `4/7`
     of these rows cannot be a seam width.  It has to be the side of a packing whose
     tilted band overhangs the margin, not a strip that contains squares.

  2. **The skeleton** (part 2, measured): the delivered pose of each target row, read
     exactly — how close its angles are to a rational-t word, how much of it is an
     integer lattice, and what the exact gate says about the *snapped* pose (delivered
     positions, every angle replaced by its nearest rational-t word).  That is the
     distance between the relaxed pose and the candidate sentence.

  3. **The attempt** (part 3, exact): lift the snapped pose with `qsqrt2.lift_sentence`
     — positions rebuilt from contacts in Q(sqrt 2), decimals used only as topology —
     and judge the result with the gate.  If it lifts, the sentence is certified at
     `2k + 4/7` and the rung is captured; if it refuses, the record says where.

No float decides anything: the angles are 70-digit Decimals, the words are Fractions,
the verdict is the exact gate.  A float appears only in the printed summary.

Usage:
    python3 scripts/rat47.py              # strip lemma + skeleton + attempt, ledger
    python3 scripts/rat47.py --selftest
"""
from __future__ import annotations

import collections
import json
import os
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction as F
from math import isqrt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import glm_wheels as W            # noqa: E402
import landscape65 as L           # noqa: E402
import qsqrt2 as Q                # noqa: E402
import verify_certificates as VC  # noqa: E402

getcontext().prec = 70

OUT = os.path.join(ROOT, "workspace/push/rat47.json")

#: the four rows doc 65 named: side `2k + 4/7`, count `(2k)^2 + 4`
TARGETS = (680, 733, 788, 845)
#: denominators tried for a rational t; a Pythagorean word beyond this has angles
#: the alphabet's own 1e-11 census would not accept as "one of ours"
QMAX = 16
SNAP_TOL = 1e-3           # a snap is accepted for *reporting* if it is this close
LIFT_TOL = F(1, 10 ** 7)  # the same declared acceptance tolerance as doc 65
RECOVER_BUDGET = L.RECOVER_BUDGET


# --------------------------------------------------------------- the alphabet
def alphabet(qmax=QMAX):
    """`(name, t, word)` for every rational-t word with `0 <= p <= q <= qmax`."""
    # the 45-degree word is *not* a rational-t word (t = tan(pi/8) = sqrt2 - 1),
    # so it is carried explicitly, as the certified families do
    out, seen = [("45", None, Q.word_45())], set()
    for q in range(1, qmax + 1):
        for p in range(0, q + 1):
            t = F(p, q)
            w = L._word_from_t(t)
            key = (w[0].a, w[0].b, w[1].a, w[1].b)
            if key in seen:
                continue
            seen.add(key)
            out.append((f"t={t}", t, w))
    return out


def width(word):
    """The bounding-box width of a unit square with this word: exactly `|c| + |s|`."""
    c, s = word
    return abs(c) + abs(s)


def strip_lemma(qmax=QMAX):
    """Part 1: the minimum bbox width over the alphabet, and who attains it.

    Exact: the minimum is the axis word's `1`, so a gap narrower than 1 (the
    `2k + 4/7` rows' margin is `4/7`) cannot contain a unit square at all.
    """
    best, at = None, []
    for name, _t, w in alphabet(qmax):
        bw = width(w)
        if best is None or bw < best:
            best, at = bw, [name]
        elif bw == best:
            at.append(name)
    return {"min_width": str(best), "attained_by": at,
            "margin": "4/7", "margin_is_narrower": best > F(4, 7)}


# --------------------------------------------------------------- the skeleton
def _dec_word(word):
    return L._word_dec(word)


def snap(angle, qmax=QMAX):
    """`(name, t, word, distance)` — the nearest rational-t word to a stored angle.

    The distance is the max of the two 70-digit Decimal coordinate gaps; it only
    *selects* the word, and it is recorded so the skeleton's jitter is visible.
    """
    dc, ds = L.FT.cos_sin(angle)
    best = None
    for name, t, w in alphabet(qmax):
        ec, es = _dec_word(w)
        d = max(abs(dc - ec), abs(ds - es))
        if best is None or d < best[3]:
            best = (name, t, w, d)
    return best


def ranked(angle, k=4, qmax=QMAX):
    """The `k` nearest rational-t words to a stored angle, nearest first."""
    dc, ds = L.FT.cos_sin(angle)
    scored = []
    for name, t, w in alphabet(qmax):
        ec, es = _dec_word(w)
        scored.append((max(abs(dc - ec), abs(ds - es)), name, w))
    scored.sort(key=lambda s: s[0])
    return [(name, w, d) for d, name, w in scored[:k]]


def skeleton(row):
    """Part 2: how far the delivered pose is from a rational-t sentence.

    Returns the snap histogram, the largest snap distance, the integer-lattice
    residual of the axis cells (max distance of a coordinate to the nearest
    multiple of 1/2, which is what an axis grid plus a 45-degree ring sits on),
    and the exact gate's verdict on the **snapped** pose.
    """
    snapnames, words, worst = collections.Counter(), [], Decimal(0)
    lattice_resid, n_axis = Decimal(0), 0
    for x, y, t in row:
        name, _t, w, d = snap(t)
        snapnames[name] += 1
        words.append(w)
        if d > worst:
            worst = d
        if w == Q.AXIS:
            n_axis += 1
            for v in (x, y):
                # distance to the nearest multiple of 1/2, in 70-digit Decimal
                dv = L._dec(v) * 2
                r = abs(dv - Decimal(int(dv.to_integral_value(rounding="ROUND_HALF_EVEN")))) / 2
                if r > lattice_resid:
                    lattice_resid = r
    pos = [(Q.Q2(x), Q.Q2(y)) for x, y, _t in row]
    g = Q.gate(pos, words)
    return {"snaps": dict(snapnames), "worst_snap": str(worst),
            "axis_cells": n_axis, "axis_lattice_residual": str(lattice_resid),
            "snapped_gate": {"ok": bool(g["ok"]), "contacts": g["contacts"],
                             "violations": g["violations"],
                             "clearance": str(g["clearance"])},
            "words": words}


def attempt(row, words, tol=LIFT_TOL, budget=RECOVER_BUDGET):
    """Part 3: lift the snapped pose exactly; the gate is the arbiter."""
    N = len(row)
    pos = [(Q.Q2(x), Q.Q2(y)) for x, y, _t in row]
    r = Q.lift_sentence(pos, words, tol=Q.Q2(tol), budget=budget)
    out = {"status": r["status"], "N": N,
           "contacts": r.get("contacts"), "violations": r.get("violations"),
           "clearance": None if r.get("clearance") is None else str(r["clearance"]),
           "placed": r.get("placed"), "recovered": r.get("recovered"),
           "unrecovered": r.get("unrecovered"),
           "budget_exhausted": r.get("budget_exhausted"),
           "side": None, "certificate": None}
    if r["status"] == "lifted":
        Lr = r["L"]
        out["side"] = str(Lr)
        out["side_dec"] = str(L._lift_side_dec(Lr))
        cert = L.certificate_of_lift(N, r, words)
        try:
            s = VC.verify_certificate(cert)
            out["certificate"] = {"status": s["status"], "N": s["N"],
                                  "contacts": s["contacts"], "L": s["L"],
                                  "clearance": s["clearance"]}
        except VC.Failure as f:
            out["certificate"] = {"status": "refused", "kind": f.kind,
                                  "check": f.check, "detail": f.detail}
    return out


# --------------------------------------------------------------- the repair
def neighbours(pos):
    """For each cell, the cells close enough for the gate to test a pair at all."""
    n = len(pos)
    out = [[] for _ in range(n)]
    two = Q.Q2(2)
    for i in range(n):
        xi, yi = pos[i]
        for j in range(i + 1, n):
            if abs(pos[j][0] - xi) >= two or abs(pos[j][1] - yi) >= two:
                continue
            out[i].append(j)
            out[j].append(i)
    return out


def pair_slack(pos, words, i, j):
    """A pair's clearance: the **largest** of its four SAT slacks (exactly)."""
    best = None
    for _q, slack, _need, _o in Q.pair_axes(pos, words, i, j):
        if best is None or slack > best:
            best = slack
    return best


def violations(pos, words, nb=None):
    """Every pair with a negative clearance, as `(i, j, slack)`."""
    nb = nb if nb is not None else neighbours(pos)
    out = []
    for i in range(len(pos)):
        for j in nb[i]:
            if j <= i:
                continue
            s = pair_slack(pos, words, i, j)
            if s is not None and s < Q.Q2(0):
                out.append((i, j, str(s)))
    return out


def repair(row, words, k=4, rounds=6):
    """Re-choose *words* (never positions) to make the snapped pose gate exactly.

    The delivered pose is exact rational geometry; only its angles are off.  So the
    repair is a discrete search over the ranked rational-t words near each cell,
    scored by the exact per-pair clearance — a pair is bad iff its largest slack is
    negative, and no tolerance is used.  Positions are never moved: a gate that
    passes here is a gate on the delivered sentence itself, and it costs at most
    `k` word trials per cell on the offending pairs.
    """
    pos = [(Q.Q2(x), Q.Q2(y)) for x, y, _t in row]
    nb = neighbours(pos)
    zero = Q.Q2(0)
    cur = list(words)

    def local_bad(i):
        return sum(1 for j in nb[i] if pair_slack(pos, cur, i, j) < zero)

    bad = violations(pos, cur, nb)
    best_bad, best_state = len(bad), list(cur)
    rounds_used = 0
    for _ in range(rounds):
        if not bad:
            break
        rounds_used += 1
        hotspots = sorted({i for i, _j, _s in bad} | {j for _i, j, _s in bad})
        for i in hotspots:
            base = cur[i]
            best_w, best_here = None, local_bad(i)
            for _name, w, _d in ranked(row[i][2], k=k):
                if w == base:
                    continue
                cur[i] = w
                n_here = local_bad(i)
                if n_here < best_here:
                    best_w, best_here = w, n_here
            cur[i] = best_w if best_w is not None else base
        bad = violations(pos, cur, nb)
        if len(bad) < best_bad:
            best_bad, best_state = len(bad), list(cur)
    cur = best_state
    # stage 2: a bad pair may need *both* of its words changed.  A swap is taken
    # only when it clears the pair's own incident edges (locally) *and* lowers the
    # global violation count (checked exactly), so this stage never regresses.
    cache = {}

    def opts(i):
        if i not in cache:
            cache[i] = ranked(row[i][2], k=6)
        return cache[i]

    bad = violations(pos, cur, nb)
    for _round in range(3):
        if not bad:
            break
        accepted = False
        for i, j, _s in bad:
            base = (cur[i], cur[j])
            for _n1, w1, _d1 in opts(i):
                for _n2, w2, _d2 in opts(j):
                    if (w1, w2) == base:
                        continue
                    cur[i], cur[j] = w1, w2
                    local = 0
                    for a in (i, j):
                        for b in nb[a]:
                            s = pair_slack(pos, cur, a, b)
                            if s is not None and s < zero:
                                local += 1
                    if local == 0:
                        trial = violations(pos, cur, nb)
                        if len(trial) < best_bad:
                            best_bad, best_state = len(trial), list(cur)
                            accepted = True
                            break
                    cur[i], cur[j] = base
                if accepted:
                    break
            if accepted:
                break
        if not accepted:
            break
    cur = best_state
    bad = violations(pos, cur, nb)
    g = Q.gate(pos, cur)
    return {"violations_before": None, "violations_after": len(bad),
            "rounds": rounds_used, "gate_ok": bool(g["ok"]),
            "contacts": g["contacts"], "clearance": str(g["clearance"]),
            "L": str(g["L"]),
            "bad_pairs": [[i, j, s] for i, j, s in bad[:8]],
            "swapped": [i for i in range(len(cur)) if cur[i] != words[i]],
            "words": cur}


# --------------------------------------------------------------- the run
def target(n, row):
    """One target row: its rung arithmetic, its skeleton, and the attempt."""
    N = len(row)
    m = isqrt(N - 4) if N >= 4 else 0
    side = L.delivered_side(row)
    k = (m // 2) if m else 0
    pred = F(m, 1) + F(4, 7) if m else None
    rec = {"n": n, "N": N, "m": m, "k": k, "delivered_side": str(side),
           "predicted_side": None if pred is None else str(pred),
           "side_matches_2k_plus_4_7": (pred is not None and
                                        abs(L._dec(pred) - side) <= Decimal("1e-6"))}
    sk = skeleton(row)
    words = sk.pop("words")
    rec["skeleton"] = sk
    rep = repair(row, words)
    rep_words = rep.pop("words")
    rep["violations_before"] = sk["snapped_gate"]["violations"]
    rec["repair"] = rep
    rec["certificate"] = None
    if rep["gate_ok"]:
        pos = [(Q.Q2(x), Q.Q2(y)) for x, y, _t in row]
        g = Q.gate(pos, rep_words)
        cert = L.certificate_of_lift(n, {"state": pos, "L": g["L"],
                                         "contacts": g["contacts"]}, rep_words)
        try:
            v = VC.verify_certificate(cert)
            rec["certificate"] = {"status": v["status"], "N": v["N"],
                                  "contacts": v["contacts"], "L": v["L"],
                                  "clearance": v["clearance"]}
        except VC.Failure as f:
            rec["certificate"] = {"status": "refused", "kind": f.kind,
                                  "check": f.check, "detail": f.detail}
        certified = L._lift_side_dec(g["L"])
        rec["certified_side"] = str(g["L"])
        rec["side_gap"] = str(certified - side)
        rec["beats_delivered"] = certified < side
    rec["attempt"] = attempt(row, words)
    return rec


def run():
    rows = W._delivered_rows()
    lemma = strip_lemma()
    recs = []
    for n in TARGETS:
        print(f"  n = {n}: skeleton + attempt …", flush=True)
        start = time.time()
        r = target(n, rows[n])
        r["seconds"] = round(time.time() - start, 1)
        recs.append(r)
    res = {"run": 103, "targets": list(TARGETS), "strip_lemma": lemma,
           "runs": recs,
           "tally": dict(collections.Counter(r["attempt"]["status"] for r in recs)),
           "identity": ("rat47: side = 2k + 4/7 with N = (2k)^2 + 4; the strip lemma "
                        "is exact over the rational-t alphabet; the skeleton reads the "
                        "delivered pose at 70 digits and snaps angles to the nearest "
                        "rational-t word; the attempt lifts the snapped pose in "
                        "Q(sqrt2) and the exact gate is the only arbiter")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    return res


def selftest():
    """Four controls: the lemma, the alphabet, a snap, and the skeleton's honesty."""
    print("rat47 selftest")
    lem = strip_lemma()
    assert lem["min_width"] == "1", lem
    assert lem["margin_is_narrower"], lem
    print(f"  control 1 — the narrowest unit-square bbox over the rational-t alphabet "
          f"is {lem['min_width']} (the axis word); 4/7 is narrower, so no square fits "
          f"a 4/7 seam")
    # width 1 is exactly the unrotated square: t = 0 and t = 1 are the same two
    # axis orientations, and every other word is strictly wider
    assert sorted(lem["attained_by"]) == ["t=0", "t=1"], lem["attained_by"]
    print(f"  control 2 — width 1 is attained only by the axis words "
          f"{lem['attained_by']} over {len(alphabet())} words")
    name, t, w, d = snap(W.PI / 4)
    assert name == "45", (name, d)     # tan(pi/8) is irrational: the 45 word is not t-basis
    assert w == Q.word_45(), w
    print(f"  control 3 — pi/4 snaps to {name} (the 45-degree word) at {float(d):.1e}")
    name, t, w, d = snap(F(0))
    assert name == "t=0" and w == Q.AXIS
    print(f"  control 4 — 0 degrees snaps to {name} exactly")
    print("rat47: OK (4 controls)")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    res = run()
    lem = res["strip_lemma"]
    print(f"strip lemma: min bbox width {lem['min_width']} at {lem['attained_by']}, "
          f"so a {lem['margin']} margin holds no square")
    for r in res["runs"]:
        a, s, rp = r["attempt"], r["skeleton"], r["repair"]
        cert = (r.get("certificate") or {}).get("status")
        print(f"  n = {r['n']:4d} N = {r['N']:4d} m = {r['m']:2d} "
              f"side {r['delivered_side'][:10]} = 2k+4/7? {r['side_matches_2k_plus_4_7']}")
        print(f"      skeleton: worst snap {s['worst_snap'][:8]}, "
              f"gate ok={s['snapped_gate']['ok']} viol={s['snapped_gate']['violations']}")
        print(f"      repair: viol {rp['violations_before']} -> {rp['violations_after']} "
              f"swapped {len(rp['swapped'])} gate_ok={rp['gate_ok']} "
              f"L={rp['L']} cert={cert} side_gap={r.get('side_gap')}")
        print(f"      lifted-from-scratch: {a['status']}")
    print(f"tally (lift of the snapped pose): {res['tally']}")
    print(f"certified by word repair: "
          f"{sum(1 for r in res['runs'] if (r.get('certificate') or {}).get('status') == 'verified')}"
          f" of {len(res['runs'])}")
    print(f"ledger: {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
