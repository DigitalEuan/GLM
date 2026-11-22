#!/usr/bin/env python3
"""landscape65.py — the relaxed rung's landscape, and exact lifting into it (run 102).

Three questions, answered from the delivered table with exact arithmetic only:

  1. **Coverage.**  Every one of the 1,000 rows gets one of three labels, from the
     run-86 field-class census and the run-85 uplift ledger: *certified* (an exact
     sentence at clearance 0 exists — the 447 axis rows and the 99 Q(sqrt 2) pose
     lifts), *side-only* (the container side lies in Q(sqrt d) or in a rational-t
     lattice, but the pose itself was never lifted) and *relaxed* (the 424
     `continuous` rows, whose side is in no small-height field we search).

  2. **Why the relaxed rung is relaxed.**  For each row the angle census is exact:
     the 0-degree word, the 45-degree word, a Pythagorean word (rational rotation, so
     it lives over Q), or **transcendental** — a 70-digit Decimal cos/sin that is not a
     unit word of Q at denominator <= 64.  A row with even one transcendental angle
     cannot be lifted as it stands: that is a law at the declared alphabet, not a
     search gap, and the run counts how many squares it costs.

  3. **What can be lifted anyway.**  Dropping the transcendental *carriers* leaves an
     algebraic **core**, which is lifted exactly (`qsqrt2.lift_sentence`: wall anchors,
     contact peeling by 2x2 Cramer, height-bounded recovery for the rest) and judged by
     the exact gate; every surviving sentence is written as a `galois-certificate/1`
     object and checked by `verify_certificates`.  Then carriers are put back where a
     word from the certified families fits at the same side — the seam/edge completion
     test — with every decision an exact comparison.

No float is used: the table's decimals are read as `Fraction`s, the trig is 70-digit
`Decimal`, and the two tolerances are declared — `1e-7` for a lift's acceptance and
`1e-9` for reading the delivered pose's own contacts — and they only *choose* topology.
The verdict is always the exact gate and the certificate.

Usage:
    python3 scripts/landscape65.py              # triage + lifting test + ledger
    python3 scripts/landscape65.py --selftest
"""
from __future__ import annotations

import collections
import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F
from math import gcd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import field_triage as FT         # noqa: E402
import glm_wheels as W            # noqa: E402
import qsqrt2 as Q                # noqa: E402
import verify_certificates as VC  # noqa: E402

getcontext().prec = 70

OUT = os.path.join(ROOT, "workspace/push/landscape65.json")
TRIAGE = os.path.join(ROOT, "workspace/push/field_triage.json")
UPLIFT = os.path.join(ROOT, "workspace/push/uplift.json")
LIFT_TOL = F(1, 10 ** 7)          # a lift's acceptance tolerance (declared)
PYTH_TOL = Decimal("1e-12")       # a continued fraction's residual (declared)
CAND_TOL = Decimal("1e-11")       # an exact word against the stored decimal cos/sin

#: the nominated targets: the three notches (already exact — the reference), the
#: continuous rows that bracket them, and small/medium relaxed rows with the most slack
NOTCHES = (677, 785, 901)
EDGE_BAND = (680, 689, 733, 788, 845, 904)
SMALL_MEDIUM = (11, 17, 39, 68, 86)


def _dec(z):
    """A Fraction as a 70-digit Decimal."""
    return Decimal(z.numerator) / Decimal(z.denominator)


# ------------------------------------------------------------------ angle words
def pyth_t(angle, qmax=64, tol=PYTH_TOL):
    """The rational `t = tan(theta/2)` of an angle, as a Fraction, or None.

    `t = sin / (1 + cos)` at 70 digits, then continued-fraction convergents: the
    first with `q <= qmax` and `|p/q - t| <= tol` is returned with its numerator —
    the numerator is what rebuilds the word, so a denominator alone is not enough
    (run 86's `pyth_angle` reported only `q`).
    """
    c, s = FT.cos_sin(angle)
    if 1 + c == 0:
        return None
    x = s / (1 + c)
    p0, q0, p1, q1 = 0, 1, 1, 0
    for _ in range(40):
        a = int(x.to_integral_value(rounding="ROUND_FLOOR"))
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        if q1 == 0 or q1 > qmax:
            return None
        cand = Decimal(p1) / Decimal(q1)
        if abs(cand - x) <= tol:
            return F(p1, q1)
        frac = x - a
        if frac == 0:
            return None
        x = 1 / frac
    return None


def _word_from_t(t):
    """The exact `(cos, sin)` of the rational t-basis point `t`, in Q(sqrt 2)."""
    c = (1 - t * t) / (1 + t * t)
    s = 2 * t / (1 + t * t)
    return (Q.Q2(c), Q.Q2(s))


def _word_dec(word):
    """An exact word's `(cos, sin)` as Decimals."""
    return (_dec(word[0].a) + _dec(word[0].b) * Decimal(2).sqrt(),
            _dec(word[1].a) + _dec(word[1].b) * Decimal(2).sqrt())


def exact_word(angle, tol=CAND_TOL):
    """The exact word of a stored angle, or `None` (transcendental).

    Three candidates, all exact: the 0-degree word, the 45-degree word, and the
    rational t-basis word.  Each is compared to the 70-digit cos/sin of the stored
    angle; the comparison only selects, the gate decides.
    """
    dc, ds = FT.cos_sin(angle)
    for word in (Q.AXIS, Q.word_45()):
        ec, es = _word_dec(word)
        if abs(dc - ec) <= tol and abs(ds - es) <= tol:
            return word
    t = pyth_t(angle)
    if t is not None:
        word = _word_from_t(t)
        ec, es = _word_dec(word)
        if abs(dc - ec) <= tol and abs(ds - es) <= tol:
            return word
    return None


def word_kind(word):
    """'axis', '45' or 'pyth' for an exact word (by its own exact values)."""
    c, s = word
    if c * c == 1 and s == 0 or c == 0 and s * s == 1:
        return "axis"
    half = Q.Q2(F(1, 2))
    if c == s and c * c == half:
        return "45"
    if c.b == 0 and s.b == 0:
        return "pyth"
    return "pyth"          # a Q(sqrt2) word with a rational t is still Pythagorean


def cell_words(row):
    """Per-cell exact word (or None), the carriers, and the angle census."""
    words, carriers, kinds = [], [], collections.Counter()
    for _x, _y, t in row:
        w = exact_word(t)
        words.append(w)
        if w is None:
            carriers.append(t)
            kinds["trans"] += 1
        else:
            kinds[word_kind(w)] += 1
    return words, carriers, dict(kinds)


# ------------------------------------------------------------------ lifting
def _lift_side_dec(L):
    return _dec(L.a) + _dec(L.b) * Decimal(2).sqrt()


def delivered_side(row):
    """The row's container side, 70-digit Decimal (bbox of the delivered pose)."""
    return FT.side_of(row)


def certificate_of_lift(n, r, words):
    """A `galois-certificate/1` object for a lifted Q(sqrt 2) sentence."""
    cells = []
    for (x, y), (c, s) in zip(r["state"], words):
        # row-major [ux, vx, uy, vy] with u = (c, s) and v = (-s, c); each entry
        # is the (a, b) pair of the field element, never its printed form
        rows = [(c.a, c.b), (-s.a, -s.b), (s.a, s.b), (c.a, c.b)]
        cells.append({"x": [str(x.a), str(x.b)], "y": [str(y.a), str(y.b)],
                      "r": [[str(a), str(b)] for a, b in rows]})
    L = r["L"]
    return {"id": f"landscape_n{n}", "family": "Relaxed core", "field": "Quad(2)",
            "N": len(cells), "L": [str(L.a), str(L.b)],
            "origin": [["0", "0"], ["0", "0"]], "cells": cells,
            "expected": {"ok": True, "contacts": r["contacts"], "violations": 0,
                         "clearance": ["0", "0"]}}


def lift_core(row, keep, words, tol=LIFT_TOL):
    """Lift the kept cells exactly in Q(sqrt 2); returns `(lift, record)`."""
    state = [(Q.Q2(row[i][0]), Q.Q2(row[i][1])) for i in keep]
    ws = [words[i] for i in keep]
    r = Q.lift_sentence(state, ws, tol=Q.Q2(tol))
    rec = {"status": r["status"], "N": len(keep),
           "contacts": r.get("contacts"), "violations": r.get("violations"),
           "clearance": None if r.get("clearance") is None else str(r["clearance"]),
           "side": None, "side_dec": None,
           "used": r.get("used"), "placed": r.get("placed"),
           "recovered": r.get("recovered")}
    if r["status"] == "lifted":
        rec["side"] = str(r["L"])
        rec["side_dec"] = str(_lift_side_dec(r["L"]))
    return r, rec


# ------------------------------------------------------- completion of carriers
def alphabet():
    """`(name, word)` over every word the certified families use, in Q(sqrt 2)."""
    out = [("axis", Q.AXIS), ("45", Q.word_45())]
    for t in (F(1, 2), F(1, 3), F(3), F(2), F(1, 4), F(1, 5)):
        w = _word_from_t(t)
        if all(w != u for _n, u in out):
            out.append((f"t={t}", w))
    return out


def extent(word, q):
    """The half-extent of a square with this word along the unit vector `q`."""
    c, s = word
    return (abs(c * q[0] + s * q[1]) + abs(-s * q[0] + c * q[1])) * Q.Q2(F(1, 2))


def _place_from_two(word, eqs):
    """Solve two contact equations for a carrier's position; None if singular."""
    for a in range(len(eqs)):
        for b in range(a + 1, len(eqs)):
            q1, r1 = eqs[a]
            q2, r2 = eqs[b]
            det = q1[0] * q2[1] - q1[1] * q2[0]
            if det.sign() == 0:
                continue
            x = (r1 * q2[1] - r2 * q1[1]) / det
            y = (q1[0] * r2 - q2[0] * r1) / det
            return x, y
    return None


def _fdec(z):
    """An exact field element as a 70-digit Decimal."""
    return _dec(z.a) + _dec(z.b) * Decimal(2).sqrt()


def _contact_equations(pos, words, angle, x0, y0, tol=Decimal("1e-6")):
    """The core cells the carrier touches in the delivered pose, with the axis and side.

    A pair is a contact when the **largest** of the four SAT slacks is zero (a tight
    axis alone is not enough: two cells at the same height but far apart are separated,
    not touching).  Detection is 70-digit Decimal — the carrier's two axes come from its
    stored cos/sin, the core cell's two from its exact word — and only equations on the
    core cell's *exact* axes are emitted, because those are the ones the exact solve can
    use; the sign is the side the carrier lies on.
    """
    cx, cy = FT.cos_sin(angle)
    px, py = _dec(x0), _dec(y0)
    out = []
    for k in range(len(pos)):
        ck, sk = words[k]
        ckd, skd = _fdec(ck), _fdec(sk)
        cxd, cyd = _fdec(pos[k][0]), _fdec(pos[k][1])
        axes = [(cx, cy, None), (-cy, cx, None),
                (ckd, skd, (ck, sk)), (-skd, ckd, (-sk, ck))]
        tight, best = {}, None
        for qx, qy, exact in axes:
            e_carrier = (abs(cx * qx + cy * qy) + abs(-cy * qx + cx * qy)) / 2
            e_core = (abs(ckd * qx + skd * qy) + abs(-skd * qx + ckd * qy)) / 2
            proj = (px - cxd) * qx + (py - cyd) * qy
            slack = abs(proj) - (e_carrier + e_core)
            if best is None or slack > best:
                best = slack
            if abs(slack) <= tol and exact is not None:
                tight[exact] = 1 if proj >= 0 else -1
        # a tight axis is a contact only when the pair's LARGEST slack is zero: two
        # cells at the same height but far apart are separated, not touching
        if best is None or abs(best) > tol:
            continue
        for q, sg in tight.items():
            out.append((k, q, sg))
    return out


def probe_carrier(pos, words, angle, x0, y0, L, tol=Decimal("1e-6")):
    """Try to replace one carrier exactly, from its delivered contacts.

    `pos`/`words` are the lifted core.  The carrier's contacts in the delivered pose
    (see `_contact_equations`) give the axes and the sides; each alphabet word then
    turns every pair of those equations into a 2x2 solve with the *exact* need of the
    two words, and a candidate is kept only if the exact per-pair predicate clears the
    whole core, the walls hold, and the full gate accepts the completed sentence.
    """
    contacts = _contact_equations(pos, words, angle, x0, y0, tol)
    if len(contacts) < 2:
        return None
    ex, ey = (Q.Q2(1), Q.Q2(0)), (Q.Q2(0), Q.Q2(1))
    for name, w in alphabet():
        e = extent(w, ex)
        eqs = []
        for k, q, sg in contacts:
            need = extent(w, q) + extent(words[k], q)
            base = pos[k][0] * q[0] + pos[k][1] * q[1]
            eqs.append((q, base + need if sg > 0 else base - need))
            eqs.append((q, base - need if sg > 0 else base + need))
        # the delivered cell also rests on a wall: that is another exact equation
        if _dec(x0) - _dec(e.a) - _dec(e.b) * Decimal(2).sqrt() <= tol:
            eqs.append((ex, e))
        if _fdec(L) - _dec(x0) - _dec(e.a) - _dec(e.b) * Decimal(2).sqrt() <= tol:
            eqs.append((ex, L - e))
        if _dec(y0) - _dec(e.a) - _dec(e.b) * Decimal(2).sqrt() <= tol:
            eqs.append((ey, e))
        if _fdec(L) - _dec(y0) - _dec(e.a) - _dec(e.b) * Decimal(2).sqrt() <= tol:
            eqs.append((ey, L - e))
        p = _place_from_two(w, eqs)
        if p is None:
            continue
        exw = extent(w, (Q.Q2(1), Q.Q2(0)))
        if not (p[0] - exw >= Q.Q2(0) and p[1] - exw >= Q.Q2(0)
                and p[0] + exw <= L and p[1] + exw <= L):
            continue
        trial_pos = list(pos) + [p]
        trial_words = list(words) + [w]
        worst, j = None, len(pos)
        for k in range(len(pos)):
            if abs(pos[k][0] - p[0]) >= Q.Q2(2) or abs(pos[k][1] - p[1]) >= Q.Q2(2):
                continue
            # a pair's clearance is its LARGEST slack over the four axes
            best = None
            for _q, slack, _need, _o in Q.pair_axes(trial_pos, trial_words, j, k):
                if best is None or slack > best:
                    best = slack
            if best is not None and (worst is None or best < worst):
                worst = best
        if worst is None or worst < Q.Q2(0):
            continue
        g = Q.gate(trial_pos, trial_words)
        if g["ok"]:
            return {"word": name, "pos": [str(p[0]), str(p[1])],
                    "clearance": str(g["clearance"]), "contacts": g["contacts"]}
    return None


# ------------------------------------------------------------------ the stages
def load():
    with open(TRIAGE) as f:
        triage = {r["n"]: r for r in json.load(f)["rows_detail"]}
    lifted = set()
    if os.path.exists(UPLIFT):
        with open(UPLIFT) as f:
            lifted = {int(k) for k, v in json.load(f).get("rows", {}).items()
                      if v.get("status") == "lifted"}
    return W._delivered_rows(), triage, lifted


def classify_row(n, row, triage, lifted):
    cls = triage[n]["class"]
    if cls == "Q-grid" or (n in lifted and cls == "Q(sqrt2) pose"):
        kind = "certified"
    elif cls == "continuous":
        kind = "relaxed"
    else:
        kind = "side-only"
    _words, carriers, kinds = cell_words(row)
    side = delivered_side(row)
    return {"n": n, "N": len(row), "class": cls, "kind": kind, "angles": kinds,
            "carriers": len(carriers), "side": str(side),
            "slack": str(side - Decimal(n).sqrt()),
            "trans_angles": [str(t) for t in sorted(set(carriers))]}


def triage_all(rows, triage, lifted):
    out = [classify_row(n, rows[n], triage, lifted) for n in sorted(rows)]
    bands = collections.Counter()
    for r in out:
        c = r["carriers"]
        bands["none" if c == 0 else "1-10" if c <= 10 else
              "11-100" if c <= 100 else ">100"] += 1
    return {"rows": out, "tally": dict(collections.Counter(r["kind"] for r in out)),
            "by_class": dict(collections.Counter(r["class"] for r in out)),
            "carrier_bands": dict(bands)}


def lift_target(n, row, probed=2, tol=LIFT_TOL):
    """The lifting test for one row: the whole pose if algebraic, else its core."""
    words, carriers_at, kinds = cell_words(row)
    side = delivered_side(row)
    keep = [i for i, w in enumerate(words) if w is not None]
    rec = {"n": n, "N": len(row), "angles": kinds, "carriers": len(carriers_at),
           "delivered_side": str(side), "core_N": len(keep)}
    r, core = lift_core(row, keep, words, tol)
    rec["core"] = core
    if r["status"] == "lifted":
        cert = certificate_of_lift(n, r, [words[i] for i in keep])
        try:
            s = VC.verify_certificate(cert)
            rec["certificate"] = {"status": s["status"], "N": s["N"],
                                  "contacts": s["contacts"], "L": s["L"],
                                  "clearance": s["clearance"]}
        except VC.Failure as f:
            rec["certificate"] = {"status": "refused", "kind": f.kind,
                                  "check": f.check, "detail": f.detail}
        rec["core_gap"] = str(_lift_side_dec(r["L"]) - side)
        rec["beat"] = Decimal(rec["core_gap"]) < 0
        if carriers_at:
            slots = [i for i in range(len(row)) if words[i] is None]
            placements = []
            for slot in slots[:probed]:
                x0, y0 = row[slot][0], row[slot][1]
                got = probe_carrier(r["state"], [words[i] for i in keep],
                                    row[slot][2], x0, y0, r["L"])
                placements.append({"cell": slot, "placed": got is not None,
                                   "detail": got})
            rec["completion"] = placements
            rec["replaced"] = sum(1 for p in placements if p["placed"])
    else:
        rec["certificate"] = None
    return rec


def run():
    rows, triage, lifted = load()
    land = triage_all(rows, triage, lifted)
    targets = list(NOTCHES) + list(EDGE_BAND) + list(SMALL_MEDIUM)
    recs = []
    for n in targets:
        print(f"  lifting n = {n} …", flush=True)
        recs.append(lift_target(n, rows[n]))
    res = {"run": 102, "landscape": land, "targets": targets, "lifted": recs,
           "lift_tally": dict(collections.Counter(r["core"]["status"] for r in recs)),
           "note": ("landscape: field classes from the run-86 census and the run-85 "
                    "uplift ledger, carriers from the exact angle census; lifting: "
                    "qsqrt2.lift_sentence in Q(sqrt2) with the certificate checked by "
                    "verify_certificates; completion: the certified families' words, "
                    "each candidate decided by the exact gate")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    return res


def selftest():
    """Five controls: the angle census, the words, and one lifted certificate."""
    print("landscape65 selftest")
    assert exact_word(F(0)) == Q.AXIS
    assert exact_word(W.PI / 4) == Q.word_45()
    print("  control 1 — 0 degrees is the axis word, pi/4 is the 45-degree word")
    t = pyth_t(W.PI / 4)
    assert t is None                       # tan(pi/8) is not rational
    assert pyth_t(F(0)) == F(0)            # 0 degrees: t = 0
    print("  control 2 — pi/8 has no rational t-basis; 0 degrees has t = 0")
    w = Q.word_45()
    assert w[0] * w[0] + w[1] * w[1] == Q.Q2(1) and w[0] == w[1]
    print("  control 3 — the 45-degree word is a unit vector with cos = sin = sqrt2/2")
    rows = W._delivered_rows()
    rec = lift_target(677, rows[677], probed=0)
    assert rec["carriers"] == 0, rec["carriers"]
    assert rec["core"]["status"] == "lifted", rec["core"]["status"]
    assert rec["certificate"]["status"] == "verified", rec["certificate"]
    assert rec["core"]["contacts"] == 2375, rec["core"]["contacts"]
    print(f"  control 4 — n = 677 lifts at clearance 0 with "
          f"{rec['core']['contacts']} contacts, certificate verified, "
          f"side {rec['core']['side']}")
    bad = [t for _x, _y, t in rows[680] if exact_word(t) is None]
    assert bad, "n = 680 is expected to carry transcendental angles"
    print(f"  control 5 — n = 680 carries {len(bad)} squares at a transcendental "
          "angle: no word, so no lift of the whole pose")
    # 6. the completion machinery, on a sentence that does lift: take one cell out of
    # the certified n = 677 sentence and ask the alphabet to put one back at the same
    # side.  A probe that cannot do this would be unable to certify any completion.
    got = completion_control(677, rows[677])
    assert got is not None and got["word"] == "axis", got
    assert got["clearance"] == "0", got
    print(f"  control 6 — one cell removed from n = 677 is replaced by the "
          f"{got['word']} word at the same side, clearance 0 "
          f"({got['contacts']} contacts)")
    print("landscape65: OK (6 controls)")
    return 0


def completion_control(n, row, tol=LIFT_TOL):
    """Delete one cell from a certified sentence and put it back with the alphabet.

    The positive control for `probe_carrier`: it must be able to recover a placement
    that is known to exist.  The deleted cell keeps its index (the lists are rebuilt
    over the remaining cells), and the probe is given the *delivered* position to
    find its neighbours by.
    """
    words, _carriers, _kinds = cell_words(row)
    keep = [i for i in range(len(row)) if words[i] is not None]
    if len(keep) < 4:
        return None
    out = keep.pop()                      # the cell to remove (a 45-degree one here)
    r, _rec = lift_core(row, keep, words, tol)
    if r["status"] != "lifted":
        return None
    return probe_carrier(r["state"], [words[i] for i in keep], row[out][2],
                         row[out][0], row[out][1], r["L"])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    res = run()
    land = res["landscape"]
    print(f"landscape: {len(land['rows'])} rows")
    for k, v in sorted(land["tally"].items()):
        print(f"  {k:12s} {v:5d}")
    for k, v in sorted(land["by_class"].items()):
        print(f"  {k:16s} {v:5d}")
    print(f"  carriers per row: {land['carrier_bands']}")
    print("lifting test:")
    for r in res["lifted"]:
        c = r["core"]
        print(f"  n = {r['n']:4d} carriers {r['carriers']:3d} core {c['N']:4d} "
              f"{c['status']:16s} side {str(c['side'])[:20]:20s} "
              f"gap {str(r.get('core_gap'))[:24]:24s} "
              f"cert {str((r.get('certificate') or {}).get('status'))}")
    print(f"  lift tally: {res['lift_tally']}")
    print(f"  ledger: {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
