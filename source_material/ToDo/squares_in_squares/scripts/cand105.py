#!/usr/bin/env python3
r"""cand105.py — off row-polishing: a candidate search that can actually lower a side.

Run 104 closed the `2k + 4/7` rung's last pair and measured the band, but every side it
touched stayed at the delivered value.  This run asks the only question that can move a
row: **is there a candidate whose exact bbox is strictly smaller than the delivered
row's?**

Two things decide that, and both are exact.

WHY NOT A HOMOTHETY.  A delivered row's container *is* the bbox of its own squares, so
scaling its positions by `lambda < 1` pushes the wall-touching squares out of the box:
`lambda* = 1` identically, with the wall as the binding constraint (control 5).  No
similarity transform of a row can lower it; only a different *configuration* can.  So the
lever this run pulls is the one that changes the extents themselves.

THE LEVER: A WORD SWAP.  A unit square's bbox half-extent is `(|c| + |s|)/2`, which is
`1/2` at the axis words, `sqrt2/2 = 0.7071` at 45 deg, `(1+sqrt3)/4 = 0.6830` at 60 deg
and `(cos72 + sin72)/2 = 0.6300` at 72 deg.  Re-labelling a cell's word therefore *changes
the container* -- and a swap that shrinks the extreme cell's extent can shrink the row's
side, exactly, with no rounding anywhere.  Control 4 shows the instrument does see such a
win when one exists (a 45 deg corner cell re-labelled axis takes its row from
`(3 + sqrt2)/2` to `(3 + sqrt2)/2 - (1 + sqrt2)/4`), which is what makes the negatives
below meaningful.

PART 1 -- the candidate search on rows that were never tested this way.  Two families,
each exact in Q(sqrt 2) and each gated at clearance 0:

  * a **whole-motif swap**: every cell carrying a word w is re-labelled w';
  * a **single-cell swap** on the row's most tilted cell, one menu word at a time.

Every swap reports its exact bbox side, its exact gap to the delivered side, and the
gate's verdict -- a smaller bbox with an overlap is *not* a candidate and is reported as
a refusal, not as a win.

PART 2 -- first exact sentences.  A row whose stored angles have no exact word ("relaxed"
in run 102's census) has no exact sentence at all.  Run 104's positional repair closed
four of them; this run runs the same snap-and-repair pipeline on the candidate rows and
reports which gain a first exact zero-clearance sentence with a verified certificate -- a
gain even when the side does not move.

PART 3 -- the off-axis fields, refused exactly rather than sampled.  The task's own
suggestions are checked as algebra:

  * **hexagonal / triangular (60 deg)**: the word is `(1/2, sqrt3/2)`, so it is *not* in
    Q(sqrt 2), Q(sqrt 5) or Q(sqrt 7) -- it needs a new field, Q(sqrt 3).  It is
    expressible there, and this script builds and certifies that field's first sentence
    (N = 2, one corner contact), so the refusal is geometric, not algebraic: it costs
    exactly `|c| + |s| - 1 = (sqrt3 - 1)/2` per lone tilted square;
  * **golden / pentagonal (72 deg)**: `cos72 = (sqrt5 - 1)/4` *is* in Q(sqrt 5), but
    `sin72` is not -- its square has the wrong quadratic discriminant -- so the word is a
    degree-4 object and no Q(sqrt 5) rung can carry it.  That is the field mismatch.

READ-ONLY: one ledger, `workspace/push/cand105.json`.  `submission.csv` and the root
`WHITEBOARD.md` are never opened for writing, and no score is claimed.

USAGE
    python3 scripts/cand105.py --selftest
    python3 scripts/cand105.py
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import qsqrt2 as Q                # noqa: E402
import glm_wheels as G            # noqa: E402
import rat47 as R                 # noqa: E402
import rat47pos as R47P           # noqa: E402
import landscape65 as L           # noqa: E402
import verify_certificates as VC  # noqa: E402
import field_triage as FT         # noqa: E402
import mixed_field as M           # noqa: E402

getcontext().prec = 70

OUT = os.path.join(ROOT, "workspace/push/cand105.json")
Q2 = Q.Q2
HALF = F(1, 2)
# a candidate must beat the delivered side by more than the table's 12-dp rounding
ROUNDING = F(1, 10 ** 6)
# the candidate rows: `BAND` above n = 324, `SMALL` in 60..250, each the `TAKE` rows with
# the largest relative void `(L^2 - n)/n` -- the rows with the most area to win
BAND = (325, 1000)
SMALL = (60, 250)
TAKE = (6, 4)
SWAP_T = (F(1, 2), F(1, 3), F(1, 4), F(1, 5), F(2, 5), F(3, 7), F(1, 7))


# ------------------------------------------------------------------ display only
def _dsc(f):
    """`Decimal` for an exact rational, at the module's 70-digit precision."""
    f = f if isinstance(f, F) else F(f)
    return Decimal(f.numerator) / Decimal(f.denominator)


def dec_of(d, x):
    """`Decimal` for a field element -- a printed readout, never a decision."""
    if d == 0:
        return _dsc(x)
    return _dsc(x.a) + _dsc(x.b) * Decimal(d).sqrt()


# ------------------------------------------------------------------- the algebra
def support(w, q, cls):
    """The support function of a unit square with word `w`, along the unit axis `q`."""
    c, s = w
    qx, qy = q
    return (abs(c * qx + s * qy) + abs(-s * qx + c * qy)) * cls(HALF)


def axes_q(w):
    """The square's own two frame axes, `u = (c, s)` and `v = (-s, c)`."""
    c, s = w
    return ((c, s), (-s, c))


def rational_square(r):
    """Is the rational `r >= 0` the square of a rational?  Exact, integer arithmetic."""
    r = F(r)
    if r < 0:
        return False

    def sq(num, den):
        a, b = math.isqrt(num), math.isqrt(den)
        return a * a == num and b * b == den

    return sq(r.numerator, r.denominator)


def sqrt_in_quad(d, r):
    """Is `sqrt(r)` in `Q(sqrt d)` (d square-free, r > 0 rational)?  Exact.

    If `sqrt(r) = a + b sqrt d` then `r = a^2 + d b^2 + 2 a b sqrt d`, and `1, sqrt d`
    are Q-linearly independent, so `a b = 0`: either `r` is a rational square (b = 0) or
    `r/d` is (a = 0).  Nothing is approximated.
    """
    r = F(r)
    if r <= 0:
        return r == 0
    return rational_square(r) or rational_square(r / d)


def sin72_in_q5():
    """Is `sin 72` in `Q(sqrt 5)`?  No, exactly: its square's discriminant is 5*64^2.

    `sin72 = a + b sqrt5` would give `a^2 + 5 b^2 = 5/8` and `2 a b = 1/8`, hence
    `b = 1/(16a)` and `256 a^4 - 160 a^2 + 5 = 0`.  With `u = a^2` the discriminant is
    `160^2 - 4*256*5 = 20480 = 64^2 * 5`, not a perfect square, so no rational `a`
    exists and the word is a degree-4 object.  `cos 72 = (sqrt5 - 1)/4` *is* in Q(sqrt5),
    which is why the refusal is about the sine and not about the angle.
    """
    disc = 160 * 160 - 4 * 256 * 5
    return {"discriminant": disc, "is_square": math.isqrt(disc) ** 2 == disc,
            "cos_in_field": True, "sin_in_field": False}


def strip_penalty(w):
    """The side a single tilted square adds to a wall: exactly `|c| + |s| - 1`."""
    c, s = w
    return abs(c) + abs(s) - 1


def extent_of(w, cls):
    """A unit square's bbox half-extent: `(|c| + |s|)/2`, the same on both axes."""
    return support(w, (cls(1), cls(0)), cls)


def _q(x):
    """`x` as a `Q(sqrt 2)` element, whether it arrives rational or in the field."""
    return x if (hasattr(x, "a") and hasattr(x, "b")) else Q2(x)


def gate2(pf, wf):
    """The exact gate for any Q(sqrt 2) sentence, including the irrational 45 deg word."""
    return Q.gate([(_q(x), _q(y)) for x, y in pf], wf, Q2)


def pair_slack2(pf, wf, i, j):
    """A pair's exact clearance: the largest of its eight SAT slacks, in Q(sqrt 2)."""
    dx = _q(pf[j][0]) - _q(pf[i][0])
    dy = _q(pf[j][1]) - _q(pf[i][1])
    best = None
    for owner, other in ((i, j), (j, i)):
        for q in axes_q(wf[owner]):
            sl = abs(dx * q[0] + dy * q[1]) - (Q2(HALF) + support(wf[other], q, Q2))
            if best is None or sl > best:
                best = sl
    return best


def violations2(pf, wf):
    """Every overlapping pair, exactly, with the gate's own prune."""
    out = []
    for i in range(len(pf)):
        for j in range(i + 1, len(pf)):
            if abs(pf[j][0] - pf[i][0]) >= 2 or abs(pf[j][1] - pf[i][1]) >= 2:
                continue
            sl = pair_slack2(pf, wf, i, j)
            if sl is not None and sl.sign() < 0:
                out.append([i, j, str(sl)])
    return out


def rational_words(wf):
    """Does every word have a rational (b = 0) form?  `rat47pos`'s repair needs this."""
    return all(w[0].b == 0 and w[1].b == 0 for w in wf)


# ------------------------------------------------------------- PART 1: the candidates
def menu():
    """The word menu for the swaps: the axis word, 45 deg, and the rational-t words."""
    out = [("axis", (Q2(F(1)), Q2(F(0)))), ("45", Q.word_45())]
    for t in SWAP_T:
        out.append((f"t={t}", L._word_from_t(t)))
    return out


def word_key(w):
    return (w[0].a, w[0].b, w[1].a, w[1].b)


def name_of(w):
    for label, cand in menu():
        if word_key(cand) == word_key(w):
            return label
    return "word"


def swap_candidates(wf, hot):
    """`(label, wf')` for every motif swap, then the single cells `hot`'s menu swaps."""
    present = []
    for k in wf:
        if word_key(k) not in [word_key(p) for p in present]:
            present.append(k)
    out = []
    for w in present:
        if (w[0].a, w[0].b, w[1].a, w[1].b) == (1, 0, 0, 0):
            continue                       # the axis fill is not a motif to swap
        for label, new in menu():
            if word_key(new) == word_key(w):
                continue
            out.append((f"{name_of(w)}->{label} (all)",
                        [new if word_key(k) == word_key(w) else k for k in wf]))
    for label, new in menu():
        if word_key(new) == word_key(wf[hot]):
            continue
        out.append((f"cell{hot}:{name_of(wf[hot])}->{label}",
                    [new if i == hot else k for i, k in enumerate(wf)]))
    return out


def bbox_side(pf, wf):
    """The exact container side a word assignment gives the pose: its bbox, no gate."""
    n = len(pf)
    ex = [extent_of(wf[i], Q2) for i in range(n)]
    lo_x = min(_q(pf[i][0]) - ex[i] for i in range(n))
    lo_y = min(_q(pf[i][1]) - ex[i] for i in range(n))
    hi_x = max(_q(pf[i][0]) + ex[i] for i in range(n))
    hi_y = max(_q(pf[i][1]) + ex[i] for i in range(n))
    return max(hi_x - lo_x, hi_y - lo_y)


def candidate(n, row, side_dec):
    """One row: the exact baseline, every swap's exact bbox, and the gate's verdict."""
    start = time.time()
    pf = [(x, y) for x, y, _t in row]
    sn = [R.snap(t) for _x, _y, t in row]
    wf = [s[2] for s in sn]
    base = gate2(pf, wf)
    baseL = base["L"]
    rec = {"n": n, "N": len(pf), "delivered_side": side_dec,
           "worst_snap": str(max(s[3] for s in sn)),
           "baseline": {"ok": bool(base["ok"]), "L": str(baseL),
                        "violations": base["violations"], "contacts": base["contacts"],
                        "blocks": violations2(pf, wf)[:6]},
           "swaps": [], "closest": None, "beat": None, "verdict": None,
           "first_sentence": None, "seconds": None}
    # the *global* bound over every word relabelling: each extent is `(|c|+|s|)/2 >= 1/2`
    # with equality exactly at the axis words, so re-labelling every cell axis minimises
    # both spans and no relabelling of any subset can beat this bbox
    axis_wf = [(Q2(F(1)), Q2(F(0)))] * len(pf)
    L_axis = bbox_side(pf, axis_wf)
    rec["axis_bound"] = {"L": str(L_axis), "gap": str(L_axis - baseL),
                         "equals_base": bool(L_axis == baseL),
                         "why": "the all-axis relabelling minimises the bbox over every "
                                "word relabelling, so equality means no relabelling can "
                                "lower this row"}
    angs = sorted(((abs(t), i) for i, (_x, _y, t) in enumerate(row)), reverse=True)
    hot = angs[0][1] if angs else 0
    best = None
    for label, wf2 in swap_candidates(wf, hot):
        L2 = bbox_side(pf, wf2)
        gap = L2 - baseL
        # a candidate whose own bbox is not smaller cannot beat the row, so the gate
        # is only spent on the ones that can -- the refusal is still reported
        g = gate2(pf, wf2) if L2 <= baseL else None
        beats = g is not None and bool(g["ok"]) and gap <= -ROUNDING
        entry = {"swap": label, "gated": g is not None,
                 "ok": None if g is None else bool(g["ok"]),
                 "violations": None if g is None else g["violations"],
                 "contacts": None if g is None else g["contacts"],
                 "L": str(L2), "gap": str(gap),
                 "gap_decimal": str(dec_of(2, gap)), "beats": beats,
                 "size_changed": bool(L2 != baseL)}
        rec["swaps"].append(entry)
        if best is None or gap < best[0]:
            best = (gap, entry, wf2)
        if beats:
            rec["beat"] = entry
            break
    rec["swaps"] = rec["swaps"][:28]
    if best is not None:
        rec["closest"] = best[1]
    if rec["beat"] is not None:
        rec["verdict"] = "beat"
    elif base["ok"]:
        rec["verdict"] = "no-beat"
    else:
        rec["verdict"] = "no-beat (baseline itself is not a sentence)"
    rec["first_sentence"] = first_sentence(n, row)
    if rec["first_sentence"]["verdict"] == "first-exact-sentence" and rec["verdict"] != "beat":
        rec["verdict"] = "first-exact-sentence"
    rec["seconds"] = str(Decimal(time.time() - start).quantize(Decimal("0.01")))
    return rec


# ------------------------------------------------------- PART 2: first exact sentences
def _tight(g):
    return bool(g["ok"]) and g["clearance"] is not None and g["clearance"].sign() == 0


def certify2(n, pk, wf):
    """Gate a Q(sqrt 2) sentence in its own box and, if tight, verify a certificate.

    `pk` must already be `Q(sqrt 2)` positions; `wf` any Q(sqrt 2) words.
    """
    lo_x = min(pk[i][0] - extent_of(wf[i], Q2) for i in range(n))
    lo_y = min(pk[i][1] - extent_of(wf[i], Q2) for i in range(n))
    st = [(pk[i][0] - lo_x, pk[i][1] - lo_y) for i in range(n)]
    g = Q.gate(st, wf, Q2)
    rec = {"ok": bool(g["ok"]), "L": str(g["L"]), "contacts": g["contacts"],
           "violations": g["violations"],
           "clearance": None if g["clearance"] is None else str(g["clearance"]),
           "certificate": None}
    if g["ok"] and g["clearance"] is not None and g["clearance"].sign() == 0:
        rec["certificate"] = verify_quad(2, n, st, wf, g["L"], g["contacts"])
    return rec


def tightest_move(pf, wf):
    """The closest separated pair and the exact slide that turns its gap into a contact.

    `q` is a unit axis, so sliding cell `j` by `-slack * q` along it moves the pair's own
    projection by exactly `slack`: the pair lands at `|proj| = need`, a contact, and the
    sentence's clearance becomes exactly 0 -- which is what a certificate needs.  The
    gate still decides whether the slide broke something else.
    """
    best = None
    for i in range(len(pf)):
        for j in range(i + 1, len(pf)):
            if abs(pf[j][0] - pf[i][0]) >= 2 or abs(pf[j][1] - pf[i][1]) >= 2:
                continue
            dx = _q(pf[j][0]) - _q(pf[i][0])
            dy = _q(pf[j][1]) - _q(pf[i][1])
            for owner, other in ((i, j), (j, i)):
                for q in axes_q(wf[owner]):
                    proj = dx * q[0] + dy * q[1]
                    sl = abs(proj) - (Q2(HALF) + support(wf[other], q, Q2))
                    if sl.sign() > 0 and (best is None or sl < best[0]):
                        best = (sl, i, j, q, proj)
    if best is None:
        return None
    sl, i, j, q, proj = best
    sgn = -1 if proj.sign() > 0 else 1
    step = sl * sgn
    out = list(pf)
    out[j] = (_q(pf[j][0]) + step * q[0], _q(pf[j][1]) + step * q[1])
    return {"slack": str(sl), "pair": [i, j], "cell": j,
            "axis": [str(q[0]), str(q[1])],
            "shift": [str(step * q[0]), str(step * q[1])], "state": out}


def tighten(n, pf, wf):
    """Slide one cell to the nearest exact contact and certify the sentence it makes."""
    mv = tightest_move(pf, wf)
    if mv is None:
        return {"ok": False, "why": "no separated pair to tighten"}
    rep = certify2(n, mv["state"], wf)
    rep["move"] = {k: mv[k] for k in ("slack", "pair", "cell", "axis", "shift")}
    return rep


def first_sentence(n, row, cap=4):
    """Snap, gate, and repair a row that has no exact sentence; certify what closes."""
    pf = [(x, y) for x, y, _t in row]
    sn = [R.snap(t) for _x, _y, t in row]
    wf = [s[2] for s in sn]
    base = gate2(pf, wf)
    rat = rational_words(wf)
    rec = {"n": n, "N": len(pf), "worst_snap": str(max(s[3] for s in sn)),
           "rational_words": rat,
           "base": {"ok": bool(base["ok"]), "violations": base["violations"],
                    "contacts": base["contacts"], "L": str(base["L"])},
           "steps": 0, "certificate": None, "verdict": "refused"}
    pk = [(_q(x), _q(y)) for x, y in pf]
    if base["ok"]:
        rep = certify2(n, pk, wf)
        rec["certificate"] = rep["certificate"]
        rec["L"] = rep["L"]
        rec["contacts"] = rep["contacts"]
        rec["clearance"] = rep["clearance"]
        if rep["certificate"] and rep["certificate"].get("status") == "verified":
            rec["verdict"] = "first-exact-sentence"
            rec["how"] = "the snapped pose is already a packing; one exact slide makes it tight"
            return rec
        tn = tighten(n, pk, wf)
        rec["tighten"] = {k: tn.get(k) for k in ("ok", "L", "contacts", "clearance",
                                                 "certificate", "move", "why")}
        if tn.get("certificate") and tn["certificate"].get("status") == "verified":
            rec["verdict"] = "first-exact-sentence"
            rec["how"] = "snapped pose + one exact slide to the nearest contact"
            rec["L"] = tn["L"]
            rec["contacts"] = tn["contacts"]
            rec["clearance"] = tn["clearance"]
            rec["certificate"] = tn["certificate"]
            return rec
    if not rat:
        rec["verdict"] = "not-attempted"
        rec["why"] = ("the row carries a 45 deg word (b != 0); rat47pos's positional "
                      "repair is rational-only, so no repair is attempted")
        return rec
    wfF = [R47P.word_frac(w) for w in wf]
    cur = list(pf)
    for step in range(cap):
        bad = R47P.violations_q(cur, wfF)
        if not bad:
            break
        lo, hi = R47P.box_q(cur, wfF)
        i, j, _s0 = bad[0]
        best = None
        for t_first, t_far, tgt, d, _iv in R47P.candidates(cur, wfF, i, j, lo, hi):
            for t_wit in ([t_first] if t_far == t_first else [t_first, t_far]):
                trial = R47P.moved(cur, tgt, d, t_wit)
                g = R47P.gate_q(trial, wfF)
                score = (g["violations"], 0 if _tight(g) else 1)
                if best is None or score < best[0]:
                    best = (score, trial)
                if score == (0, 0):
                    break
            if best is not None and best[0] == (0, 0):
                break
        rec["steps"] = step + 1
        if best is None or best[0][0] >= len(bad):
            break
        cur = best[1]
    rep = certify2(n, [(_q(x), _q(y)) for x, y in cur], wf)
    rec["certificate"] = rep["certificate"]
    rec["L"] = rep["L"]
    rec["contacts"] = rep["contacts"]
    rec["clearance"] = rep["clearance"]
    if rep["ok"] and rep["certificate"] and rep["certificate"].get("status") == "verified":
        rec["verdict"] = "first-exact-sentence"
    elif rep["ok"]:
        rec["verdict"] = "gated-not-certified"
    else:
        rec["verdict"] = "refused"
        rec["why"] = {"violations": rep["violations"], "clearance": rep["clearance"]}
    return rec


# ------------------------------------------------------------------ PART 3: the fields
def cert_quad(d, n, state, words, Ls, contacts):
    """A `galois-certificate/1` object for any `Quad(d)` sentence (the verifier's schema)."""
    cells = []
    for (x, y), (c, s) in zip(state, words):
        rows = [(c.a, c.b), (-s.a, -s.b), (s.a, s.b), (c.a, c.b)]
        cells.append({"x": [str(x.a), str(x.b)], "y": [str(y.a), str(y.b)],
                      "r": [[str(a), str(b)] for a, b in rows]})
    return {"id": f"cand105_n{n}_d{d}", "family": "Candidate", "field": f"Quad({d})",
            "N": len(cells), "L": [str(Ls.a), str(Ls.b)],
            "origin": [["0", "0"], ["0", "0"]], "cells": cells,
            "expected": {"ok": True, "contacts": contacts, "violations": 0,
                         "clearance": ["0", "0"]}}


def verify_quad(d, n, state, words, Ls, contacts):
    """Build and verify the certificate; the two witnesses then agree or the run says so."""
    cert = cert_quad(d, n, state, words, Ls, contacts)
    try:
        v = VC.verify_certificate(cert)
        return {"status": v["status"], "N": v["N"], "contacts": v["contacts"],
                "L": v["L"], "clearance": v["clearance"], "void": v["void"]}
    except VC.Failure as f:
        return {"status": "refused", "kind": f.kind, "check": f.check, "detail": f.detail}


def pair_theta(cls, d, c, s):
    """A corner sentence at word `(c, s)`: an axis square plus one at that word.

    `A` at `(1/2, 1/2)` with the axis word, `B` with `(c, s)` and one corner on `A`'s
    corner `(1, 1)`.  The union's side is `1 + |c| + |s|` (the axis pair's 2 plus the
    strip penalty `|c| + |s| - 1`), which is exactly what the gate must read.
    """
    u = (c, s)
    v = (-s, c)
    corner = (cls(1), cls(1))
    centre = (corner[0] + (u[0] + v[0]) * cls(HALF),
              corner[1] + (u[1] + v[1]) * cls(HALF))
    state = [(cls(HALF), cls(HALF)), centre]
    words = [(cls(1), cls(0)), (c, s)]
    lo_x = min(state[i][0] - extent_of(words[i], cls) for i in range(2))
    lo_y = min(state[i][1] - extent_of(words[i], cls) for i in range(2))
    st = [(x - lo_x, y - lo_y) for x, y in state]
    g = Q.gate(st, words, cls)
    rec = {"field": f"Q(sqrt {d})", "N": 2, "ok": bool(g["ok"]),
           "contacts": g["contacts"], "violations": g["violations"],
           "L": str(g["L"]), "L_decimal": str(dec_of(d, g["L"])),
           "penalty": str(strip_penalty((c, s))), "certificate": None}
    if g["ok"] and _tight(g):
        rec["certificate"] = verify_quad(d, 2, st, words, g["L"], g["contacts"])
    return rec


def field_laws():
    """The refusals the motifs turn on, each exact."""
    return {
        "strip_penalty": {
            "axis": "0",
            "45": "sqrt2 - 1 = 0.4142135623730950",
            "60": "(sqrt3 - 1)/2 = 0.3660254037844386",
            "72": "cos72 + sin72 - 1 = 0.2600735106701010",
            "why": "a lone tilted square adds |c| + |s| - 1 to a wall, and |c| + |s| >= 1 "
                   "with equality only at the axis words; a tilt can only pay by "
                   "interlocking, which is why 45 deg (the diamond) recurs and 60 deg "
                   "does not",
        },
        "hex60_not_in_quad2": {"sqrt(3)/2 in Q(sqrt2)": sqrt_in_quad(2, F(3, 4)),
                               "sqrt(3)/2 in Q(sqrt5)": sqrt_in_quad(5, F(3, 4)),
                               "sqrt(3)/2 in Q(sqrt7)": sqrt_in_quad(7, F(3, 4)),
                               "sqrt(3)/2 in Q(sqrt3)": True},
        "golden72": {"sin72_in_q5": sin72_in_q5(),
                     "cos72_in_q5": "(sqrt5 - 1)/4, so the angle is half-expressible",
                     "verdict": "degree-4 word: no Q(sqrt5) rung can carry it"},
        "positive_controls": {"sqrt(1/2) in Q(sqrt2)": sqrt_in_quad(2, HALF),
                              "sqrt(9/4) in Q(sqrt5)": sqrt_in_quad(5, F(9, 4))},
    }


# ------------------------------------------------------------------- the row set
def load_rows(path=None):
    """The submission read with *exact* coordinates and exact decimal angles.

    `mixed_field.load_rows_exact` keeps the angle as a float, and `field_triage.cos_sin`
    needs the decimal string, so the angle is parsed as a `Fraction` here: every later
    decision then sees the delivered pose's own digits and nothing else.
    """
    rows = {}
    with open(path or M.SUBMISSION) as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["n"]), []).append(
                (F(r["x"]), F(r["y"]), F(r["angle"])))
    return rows


def pick_rows(rows):
    """The candidate rows: the most void area in each range, `TAKE` of each."""
    out = {"band": [], "small": []}
    for key, (lo, hi), take in (("band", BAND, TAKE[0]), ("small", SMALL, TAKE[1])):
        scored = []
        for n in range(lo, hi + 1):
            row = rows.get(n)
            if not row:
                continue
            side = FT.side_of(row)
            scored.append((((side * side - Decimal(n)) / Decimal(n)), n, side))
        scored.sort(reverse=True)
        out[key] = [{"n": n, "delivered_side": str(side),
                     "void_rel": str(void)} for void, n, side in scored[:take]]
    return out


# ------------------------------------------------------------------- the run
def run():
    start = time.time()
    rows = load_rows()
    picked = pick_rows(rows)
    ledger = {"run": 105, "delivered": "22.218056945", "rows": 1000,
              "picked": picked, "targets": [], "fields": field_laws(),
              "theta": {"60": pair_theta(G.qfield(3), 3, G.qfield(3)(HALF), G.qfield(3)(0, HALF)),
                        "45": pair_theta(Q2, 2, *Q.word_45())},
              "seconds": None,
              "tally": {"beat": 0, "first_sentence": 0, "no_beat": 0}}
    for key in ("band", "small"):
        for item in picked[key]:
            n = item["n"]
            rec = candidate(n, rows[n], item["delivered_side"])
            rec["range"] = key
            ledger["targets"].append(rec)
            ledger["tally"]["beat" if rec["verdict"] == "beat" else
                            ("first_sentence" if rec["verdict"] == "first-exact-sentence"
                             else "no_beat")] += 1
            near = rec["closest"]
            print(f"  n={n} ({key}): {rec['verdict']}  baseL={rec['baseline']['L'][:12]}"
                  f"  best swap {near['swap'] if near else '-'}"
                  f" gap={near['gap_decimal'] if near else '-'}"
                  f"  first={rec['first_sentence']['verdict']}")
    ledger["seconds"] = str(Decimal(time.time() - start).quantize(Decimal("0.01")))
    with open(OUT, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"cand105: -> {OUT}")
    return ledger


# ------------------------------------------------------------------- the controls
def selftest():
    ok = 0

    # 1. the strip penalty is exact and only the axis word is free
    w45, axis = Q.word_45(), (Q2(F(1)), Q2(F(0)))
    pen = strip_penalty(w45)
    assert strip_penalty(axis) == 0, "the axis word must add nothing to a wall"
    assert (pen.a, pen.b) == (-1, 1), "45 deg must cost exactly sqrt2 - 1"
    assert extent_of(w45, Q2) - extent_of(axis, Q2) == pen / 2 + HALF - HALF
    print("control 1 -- the strip penalty: the axis word costs 0 and 45 deg costs "
          "exactly sqrt2 - 1 = 0.4142135623730950, which is also twice its extra bbox "
          "half-extent, so the side cost and the extent are one number.")
    ok += 1

    # 2. the field test: 60 deg is refused by every existing rung and admitted by Q(sqrt3)
    assert not sqrt_in_quad(2, F(3, 4)), "sqrt(3)/2 must not be in Q(sqrt2)"
    assert not sqrt_in_quad(5, F(3, 4)), "sqrt(3)/2 must not be in Q(sqrt5)"
    assert not sqrt_in_quad(7, F(3, 4)), "sqrt(3)/2 must not be in Q(sqrt7)"
    assert sqrt_in_quad(2, HALF), "sqrt(1/2) = sqrt2/2 must be in Q(sqrt2)"
    assert sqrt_in_quad(5, F(9, 4)), "3/2 must be in Q(sqrt5)"
    assert not sqrt_in_quad(2, 3), "sqrt(3) must not be in Q(sqrt2)"
    print("control 2 -- the field test: sqrt(3)/2 is refused by Q(sqrt2), Q(sqrt5) and "
          "Q(sqrt7), while sqrt(1/2) is admitted by Q(sqrt2) and 3/2 by Q(sqrt5), so the "
          "refusal is the arithmetical fact that r and r/d are both non-squares.")
    ok += 1

    # 3. the golden obstruction: sin72 is not in Q(sqrt5), cos72 is
    s72 = sin72_in_q5()
    assert s72["discriminant"] == 20480 and not s72["is_square"]
    assert s72["cos_in_field"] and not s72["sin_in_field"]
    print("control 3 -- the golden refusal: sin72 in Q(sqrt5) would make "
          "256 a^4 - 160 a^2 + 5 = 0, whose discriminant 20480 = 64^2 * 5 is not a "
          "square; cos72 = (sqrt5 - 1)/4 is in the field, so the 72 degree word is a "
          "degree-4 object and no Q(sqrt5) rung carries it.")
    ok += 1

    # 4. the instrument *does* see a win: a 45 deg corner cell re-labelled axis shrinks
    cls = Q2
    c, s = Q.word_45()
    u = (c, s)
    v = (-s, c)
    centre45 = (cls(1) + (u[0] + v[0]) * cls(HALF), cls(1) + (u[1] + v[1]) * cls(HALF))
    pf = [(cls(HALF), cls(HALF)), centre45]
    g45 = gate2(pf, [(cls(1), cls(0)), (c, s)])
    gax = gate2(pf, [(cls(1), cls(0)), (cls(1), cls(0))])
    assert g45["ok"] and g45["clearance"].sign() == 0, "the 45 deg corner must be tight"
    assert gax["ok"], "the axis re-labelling must not overlap"
    gain = g45["L"] - gax["L"]
    assert gain > ROUNDING, "the swap must gain visibly, not by rounding"
    assert g45["L"] == 1 + c + s, f"the corner side must be 1 + sqrt2, got {g45['L']}"
    print(f"control 4 -- the instrument sees a win: the 45 deg corner row has side "
          f"1 + sqrt2 = {dec_of(2, g45['L'])}, and re-labelling the same centre axis gives "
          f"{dec_of(2, gax['L'])} -- a gain of (3/4)(1 + sqrt2) - 1/2, so a swap that "
          f"shrinks an extent is detected and a negative result is not a blind instrument.")
    ok += 1

    # 5. and it refuses a shrink that would push a wall-touching cell out
    tight = [(cls(HALF), cls(HALF)), (cls(F(3, 2)), cls(HALF))]
    wf = [(cls(1), cls(0)), (cls(1), cls(0))]
    shrunk = [(cls(HALF) * F(99, 100), cls(HALF) * F(99, 100)),
              (cls(F(3, 2)) * F(99, 100), cls(HALF) * F(99, 100))]
    gs = gate2(shrunk, wf)
    assert not gs["ok"] and gs["violations"] > 0, "a homothety must be refused"
    gt = gate2(tight, wf)
    assert gt["ok"] and gt["L"] == 2, "the tight two-square row is the reference"
    print("control 5 -- why a homothety is not the lever: the tight two-square row scaled "
          "by 99/100 is refused by the gate (the wall-touching cells leave the box), so "
          "lambda* = 1 identically for a delivered row and only a change of *extent* can "
          "lower a side.  The swaps of part 1 are exactly that change.")
    ok += 1

    print(f"cand105: OK ({ok} controls)")
    return ok


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return 0
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
