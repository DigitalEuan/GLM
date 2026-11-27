#!/usr/bin/env python3
r"""snap_certify.py — STAGE 2: exact rational snap, repair and adjudication. Zero floats.

WHAT THIS IS.  Stage 1 (`proposal_anneal.py`) proposes; this module *decides*.  It reads the
proposals as decimal text, snaps every orientation to a **rational spinor** and every centre
to an exact rational, repairs the snapping residual by exact rational contact tightening, and
adjudicates the result with the float-free pipeline only:

    spinor     (cos, sin) = ((1 - t^2)/(1 + t^2), 2 t/(1 + t^2))  with  t = Fraction
    pose       centres and side in Q (Fractions), so the *whole* pose is rational
    gate       qsqrt2.gate(state, words, exact_field.Q)   -- exact SAT, no tolerance
    C1         a `verify_certificates` document, field "Q", re-verified
    C2         L < delivered(n) - 1e-8, decided in Decimal arithmetic
    C3/C4      only then the CSV is rendered (12 dp, with a rounding bound) and the guards run

WHY THE SNAP IS THE HARD PART.  A float angle is not a rational spinor, so snapping moves
each square by up to `L * 2/q^2` (q the spinor's denominator) — far more than the 1e-5 the
proposal was allowed.  `repair` therefore works in the exact pose: it finds the worst
overlapping pair, moves the *owner* of that pair's best separating axis by exactly the
penetration along that axis (so the pair lands in exact contact), clamps the square into the
box, and repeats.  It is a Gauss-Seidel projection in exact arithmetic: it either reaches a
zero-overlap pose inside `[0, L]^2` or it stalls, and stalling is a refusal, never a rounding
argument.

HONEST INPUTS.  A proposal enters only if Stage 1 marked it `qualifies` (max penetration
< 1e-5 at side <= k - 1e-4).  The near-misses are still snapped and repaired, but only to
report *conversion diagnostics* — how much the snap costs, and how far the repair gets.  They
cannot be promoted: `adjudicate` requires `gate.ok`, `L <= L_target` and `L < delivered - 1e-8`.

USAGE
    python3 scripts/snap_certify.py --selftest
    python3 scripts/snap_certify.py --run
    python3 scripts/snap_certify.py --run --write      # only if a candidate passes C1-C4
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from decimal import Decimal, localcontext
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402  (Q, the bytecode audit)
import qsqrt2 as QS              # noqa: E402  (the exact gate)
import true_geom as TG           # noqa: E402  (Decimal cos/sin, no float)
import verify_certificates as VC  # noqa: E402  (C1)

Q = EF.Q
SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
BACKUP = os.path.join(ROOT, "workspace/push/submission_before_snap.csv")
LEDGER = os.path.join(ROOT, "workspace/push/snap_certify.json")
PROPOSALS = os.path.join(ROOT, "workspace/push/anneal.jsonl")

MARGIN = Decimal("1e-8")
SHRINK = F(1, 10 ** 4)            # the target side is k - 1e-4, exactly
QMAX = 100_000                    # spinor denominator bound (CF convergents)
DENS = 10 ** 9                    # centre denominator bound
PLACES = 12                       # CSV decimals


# ------------------------------------------------------------------- spinors
def dec(q) -> Decimal:
    """A rational as a Decimal, at 30 significant digits (display only; never a decision)."""
    with localcontext() as ctx:
        ctx.prec = 30
        return Decimal(q.numerator) / Decimal(q.denominator)


def spinor(t: F):
    """The rational point of the unit circle with `t = tan(theta/2)`, exactly."""
    den = 1 + t * t
    return (1 - t * t) / den, (2 * t) / den


def cf_convergents(t: F, qmax: int = QMAX):
    """The continued-fraction convergents `p/q` of `t` with `q <= qmax`, in order.

    A convergent is the best rational approximation of its size, and two consecutive ones
    bracket `t`, so the last one returned is the best `t` can do inside the bound.  Run 154
    used `limit_denominator(32)`; at `k = 15` that is ~`1e-3` rad of angle, i.e. `1.5e-2` of
    positional slop — larger than the overlaps being chased.  At `q <= 1e5` the angle is good
    to `~1e-10` rad, and the snap costs nothing that matters.
    """
    p0, q0, p1, q1 = 0, 1, 1, 0
    out = []
    v = t
    for _ in range(64):
        a = v.numerator // v.denominator
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        if q1 > qmax:
            break
        out.append(F(p1, q1))
        rest = v - a
        if rest == 0:
            break
        v = 1 / rest
    return out


def snap_t(theta: Decimal, qmax: int = QMAX) -> F:
    """`tan(theta/2)` as the last continued-fraction convergent with denominator <= qmax.

    `t = sin / (1 + cos)` is used instead of `tan` so that a right angle does not divide by
    zero; the division is Decimal at 60 digits, so the only loss is the rational fit itself.
    """
    with localcontext() as ctx:
        ctx.prec = 60
        c, s = TG.cos_sin(theta)
        t = F(s / (1 + c))
    conv = cf_convergents(t, qmax)
    return conv[-1] if conv else F(0)


def snap_pos(v: Decimal, dens: int = DENS) -> F:
    """The decimal coordinate as an exact rational with denominator <= dens."""
    return F(v).limit_denominator(dens)


def snap_pose(proposal, qmax: int = QMAX, dens: int = DENS):
    """The proposal as a rational pose: `[(x, y)]`, `[(c, s)]`, all in Q."""
    cells, words = [], []
    for cell in proposal["cells"]:
        t = snap_t(Decimal(cell["a"]), qmax)
        c, s = spinor(t)
        cells.append((Q(snap_pos(Decimal(cell["x"]), dens)),
                      Q(snap_pos(Decimal(cell["y"]), dens))))
        words.append((Q(c), Q(s)))
    return cells, words


# -------------------------------------------------------------------- repair
def extent(cells, words):
    """The pose's box side, exactly (the gate computes the same thing)."""
    return QS.side(cells, words, Q)


def fits_box(cells, words, L) -> bool:
    """Every square inside `[0, L]^2` exactly (the container is anchored at the origin)."""
    for (x, y), (c, s) in zip(cells, words):
        hx = (abs(c) + abs(s)) / Q(2)
        if x - hx < Q(0) or x + hx > L or y - hx < Q(0) or y + hx > L:
            return False
    return True


def worst_pair(cells, words):
    """The pair with the largest penetration, with its best axis: `(pen, i, j, q)` or None."""
    worst = None
    n = len(cells)
    two = Q(2)
    for i in range(n):
        xi, yi = cells[i]
        for j in range(i + 1, n):
            if abs(cells[j][0] - xi) >= two or abs(cells[j][1] - yi) >= two:
                continue
            best = None
            for q, slack, _need, owner in QS.pair_axes(cells, words, i, j, Q):
                if best is None or slack > best[1]:
                    best = (q, slack, owner)
            if best is not None and best[1] < Q(0):
                pen = -best[1]
                if worst is None or pen > worst[0]:
                    worst = (pen, i, j, best[0], best[2])
    return worst


def clamp_into(cell, word, L):
    """Put a cell inside `[0, L]^2` exactly, or return it unchanged if it cannot fit."""
    c, s = word
    hx = (abs(c) + abs(s)) / Q(2)
    hy = hx
    x, y = cell
    if hx > L / Q(2):
        return cell
    x = min(max(x, hx), L - hx)
    y = min(max(y, hy), L - hy)
    return (x, y)


def violations(cells, words):
    """Every overlapping pair, exactly: `[(i, j, qx, qy, sign, pen)]`."""
    out = []
    n = len(cells)
    two = Q(2)
    for i in range(n):
        xi, yi = cells[i]
        for j in range(i + 1, n):
            if abs(cells[j][0] - xi) >= two or abs(cells[j][1] - yi) >= two:
                continue
            best = None
            for q, slack, _need, _owner in QS.pair_axes(cells, words, i, j, Q):
                # SAT: the pair is separated iff SOME axis separates, so the binding axis is
                # the one with the LARGEST slack and the penetration is its negative
                if best is None or slack > best[1]:
                    best = (q, slack)
            if best is None or best[1] >= Q(0):
                continue
            qx, qy = best[0]
            proj = (cells[j][0] - cells[i][0]) * qx + (cells[j][1] - cells[i][1]) * qy
            out.append((i, j, qx, qy, Q(1) if proj >= 0 else Q(-1), -best[1]))
    return out


EPS = F(1, 10 ** 18)              # the exact closure epsilon: 10 orders under the 1e-8 floor


def relax_simultaneous(cells, words, L, iters: int = 240, damping: F = F(1, 2),
                       closure: int = 400):
    """Simultaneous damped-residual relaxation, in exact `Fraction` arithmetic.

    Every violating pair contributes a displacement to *both* its squares before anything
    moves — the Jacobi step run 154's sequential sweep was not.  Sequential pushing hands one
    pair's overlap to its neighbour (18 of 20 rows got worse); here the residuals are summed
    and damped, and the container clamp is applied once per iteration to the whole pose.

    Returns `(cells, iterations, residual)` with the residual exact.
    """
    cells = [clamp_into(cells[i], words[i], L) for i in range(len(cells))]
    it = 0
    for it in range(1, iters + 1):
        bad = violations(cells, words)
        if not bad:
            return cells, it, Q(0)
        acc = [(Q(0), Q(0)) for _ in cells]
        for i, j, qx, qy, sgn, pen in bad:
            d = damping * pen
            acc[i] = (acc[i][0] - sgn * d * qx, acc[i][1] - sgn * d * qy)
            acc[j] = (acc[j][0] + sgn * d * qx, acc[j][1] + sgn * d * qy)
        cells = [clamp_into((cells[k][0] + acc[k][0], cells[k][1] + acc[k][1]), words[k], L)
                 for k in range(len(cells))]
    # Exact closure: damped Jacobi converges geometrically and leaves residuals at the 1e-24
    # scale.  The gate is exact, so a 1e-24 overlap is still an overlap; the last step
    # separates the worst pair by `pen + EPS` split between both cells, which lands the pose
    # on strict clearance (EPS = 1e-30) instead of asymptotically short of it.
    for _ in range(closure):
        bad = violations(cells, words)
        if not bad:
            break
        i, j, qx, qy, sgn, pen = max(bad, key=lambda v: v[5])
        d = (pen + EPS) / Q(2)
        cells[i] = clamp_into((cells[i][0] - sgn * d * qx, cells[i][1] - sgn * d * qy),
                              words[i], L)
        cells[j] = clamp_into((cells[j][0] + sgn * d * qx, cells[j][1] + sgn * d * qy),
                              words[j], L)
    bad = violations(cells, words)
    res = Q(0) if not bad else max(v[5] for v in bad)
    return cells, it, res


# --------------------------------------------------------------- adjudication
def certificate(cells, words, n: int, L):
    """A `verify_certificates` document for a rational pose (field "Q")."""
    out = {"id": f"snap-n{n}", "field": "Q", "N": n, "L": str(L),
           "origin": ["0", "0"], "family": "anneal-snap",
           "expected": {"ok": True, "violations": 0}, "cells": []}
    for (x, y), (c, s) in zip(cells, words):
        out["cells"].append({"x": str(x), "y": str(y),
                             "r": [str(c), str(-s), str(s), str(c)]})
    return out


def adjudicate(n: int, cells, words, target_L, delivered: Decimal) -> dict:
    """C1 and C2, exactly: the gate, the certificate, the box, and the delivered margin."""
    g = QS.gate(cells, words, Q)
    verdict = {"n": n, "ok": g["ok"], "L": str(g["L"]), "violations": g["violations"],
               "clearance": str(g["clearance"]) if g["clearance"] is not None else None,
               "contacts": g["contacts"], "inside": g["L"] <= target_L}
    if not g["ok"]:
        verdict["why"] = "the exact gate has overlaps"
        return verdict
    if g["L"] > target_L:
        verdict["why"] = "the pose needs a bigger box than the target side"
        return verdict
    if not fits_box(cells, words, target_L):
        verdict["why"] = "the pose escapes [0, L]^2"
        return verdict
    Ld = Decimal(g["L"].numerator) / Decimal(g["L"].denominator)
    verdict["L_dec"] = str(Ld)
    verdict["margin"] = str(delivered - Ld)
    if not (Ld + MARGIN <= delivered):
        verdict["why"] = f"no strict beat: L {Ld} vs delivered {delivered} at margin 1e-8"
        return verdict
    try:
        cert = certificate(cells, words, n, g["L"])
        summ = VC.verify_certificate(cert)
    except VC.Failure as e:                                   # noqa: BLE001
        verdict["why"] = f"C1 refused the certificate: {e}"
        return verdict
    verdict["C1"] = bool(summ["ok"])
    verdict["C2"] = True
    verdict["certificate"] = cert
    return verdict


# ------------------------------------------------------------------ rendering
def render(cells, words, places: int = PLACES):
    """The CSV cells at `places` decimals, with the worst shift the rounding can cause."""
    quantum = Decimal(1).scaleb(-places)
    out, worst = [], Decimal(0)
    for (x, y), (c, s) in zip(cells, words):
        xr = (Decimal(x.numerator) / Decimal(x.denominator)).quantize(quantum)
        yr = (Decimal(y.numerator) / Decimal(y.denominator)).quantize(quantum)
        worst = max(worst, abs(xr - Decimal(x.numerator) / Decimal(x.denominator)),
                    abs(yr - Decimal(y.numerator) / Decimal(y.denominator)))
        out.append({"x": xr, "y": yr, "angle": angle_of(c, s, quantum)})
    return out, worst * 2                       # a corner moves by at most twice the shift


def angle_of(c, s, quantum: Decimal) -> Decimal:
    """The rotation angle of a rational spinor, half-even at `quantum` (Decimal only)."""
    with localcontext() as ctx:
        ctx.prec = 60
        # theta = 2 atan2(s, c) via atan series on the smaller component ratio
        num, den = (s, c) if abs(c) >= abs(s) else (c, s)
        r = Decimal(num.numerator) / Decimal(num.denominator) / (
            Decimal(den.numerator) / Decimal(den.denominator))
        at = _atan_dec(r)
        theta = at if abs(c) >= abs(s) else (TG.HALF_PI - at)
        return (2 * theta).quantize(quantum)


def _atan_dec(r: Decimal, terms: int = 80) -> Decimal:
    """`atan(r)` for |r| <= 1 by its Taylor series in Decimal (no float)."""
    total, p, r2 = Decimal(0), r, r * r
    for k in range(terms):
        total += p / (2 * k + 1) if k % 2 == 0 else -p / (2 * k + 1)
        p *= r2
    return total


# --------------------------------------------------------------------- baseline
def clamped_grid(n, k):
    """The trivial pose: the k x k lattice, clamped into the target container."""
    L = Q(k) - Q(SHRINK)
    cells, words = [], []
    for j in range(k):
        for i in range(k):
            if len(cells) >= n:
                break
            cells.append((Q(i) + Q(F(1, 2)), Q(j) + Q(F(1, 2))))
            words.append((Q(1), Q(0)))
    cells = [clamp_into(c, w, L) for c, w in zip(cells, words)]
    return cells, words, L


def baseline(rows) -> list:
    """Every target row's floor: the clamped grid's exact penetration at `k - 1e-4`."""
    out = []
    for rec in rows:
        n, k = rec["n"], rec["k"]
        cells, words, L = clamped_grid(n, k)
        bad = violations(cells, words)
        pen = max((v[5] for v in bad), default=Q(0))
        g = QS.gate(cells, words, Q)
        out.append({"n": n, "k": k, "r": rec["r"], "tier": rec["tier"], "L": str(L),
                    "pen": str(pen), "ok": g["ok"], "violations": g["violations"],
                    "cells": len(cells)})
    return out


def do_baseline(path: str) -> int:
    with open(os.path.join(ROOT, "workspace/push/anneal_targets.json")) as f:
        rows = json.load(f)
    out = baseline(rows)
    dst = os.path.join(ROOT, path)
    with open(dst, "w") as f:
        json.dump(out, f, indent=1)
    print(f"{'n':>4} {'k':>2} {'r':>2} {'tier':>4} {'clamped-grid pen':>18} {'violations':>10}")
    for rec in out:
        print(f"{rec['n']:>4} {rec['k']:>2} {rec['r']:>2} {rec['tier']:>4} "
              f"{dec(Q(F(rec['pen']))):>18.3e} {rec['violations']:>10}")
    print(f"baseline: {path}")
    return 0


# ------------------------------------------------------------------- selftest
def selftest() -> int:
    checks = 0
    c, s = spinor(F(1, 2))
    assert (c, s) == (F(3, 5), F(4, 5)) and c * c + s * s == 1
    c0, s0 = spinor(F(1))
    assert (c0, s0) == (F(0), F(1))
    print("  1. the spinor: t = 1/2 gives (3/5, 4/5) and t = 1 gives (0, 1), "
          "both exactly on the circle")
    checks += 1

    th = Decimal("0.927295218001612")
    t = snap_t(th)
    c1, s1 = spinor(t)
    assert t == F(1, 2) and (c1, s1) == (F(3, 5), F(4, 5)), (t, c1, s1)
    print(f"  2. snap of the CSV angle 0.927295218001612: t = {t}, word ({c1}, {s1}) — the "
          f"3-4-5 spinor recovered from the decimal alone")
    checks += 1

    cells = [(Q(i) + Q(F(1, 2)), Q(j) + Q(F(1, 2))) for j in range(3) for i in range(3)]
    words = [(Q(1), Q(0))] * 9
    g = QS.gate(cells, words, Q)
    assert g["ok"] and g["L"] == Q(3) and g["contacts"] == 20
    v = adjudicate(9, cells, words, Q(3), Decimal("3.5"))
    assert v["C1"] and v["C2"], v
    print("  3. a rational 3x3 grid gates (L = 3, 20 contacts), its certificate passes C1, "
          "and C2 accepts it against a delivered 3.5")
    checks += 1

    bad = [(Q(F(1, 2)), Q(F(1, 2))), (Q(F(14, 10)), Q(F(1, 2))),
           (Q(F(23, 10)), Q(F(1, 2)))]
    bw = [(Q(1), Q(0))] * 3
    gb = QS.gate(bad, bw, Q)
    assert not gb["ok"], gb
    fixed, it, res = relax_simultaneous(bad, bw, Q(F(7, 2)))
    gf = QS.gate(fixed, bw, Q)
    assert gf["ok"] and res == 0, (it, res, gf["violations"])
    print(f"  4. simultaneous relaxation: three unit cells at 0.9 spacing overlap by 0.1; the "
          f"damped Jacobi step reaches 0 residual in {it} iterations and the gate passes")
    checks += 1

    big = [(Q(F(1, 2)), Q(F(1, 2))), (Q(F(14, 10)), Q(F(1, 2))),
           (Q(F(23, 10)), Q(F(1, 2))), (Q(F(1, 2)), Q(F(14, 10)))]
    gb2 = QS.gate(big, [(Q(1), Q(0))] * 4, Q)
    assert not gb2["ok"]
    v2 = adjudicate(4, big, [(Q(1), Q(0))] * 4, Q(F(7, 2)), Decimal("3.5"))
    assert not v2["ok"] and "overlaps" in v2["why"], v2
    print("  5. a pose with an overlap is refused by the gate before the margin is even "
          "consulted — the adjudicator cannot pass an illegal pose")
    checks += 1

    v3 = adjudicate(9, cells, words, Q(3), Decimal("3"))
    assert v3["ok"] and "C1" not in v3 and "no strict beat" in v3["why"], v3
    print("  6. a legal pose that only ties the delivered side fails C2 (no strict beat at "
          "the 1e-8 margin)")
    checks += 1

    # control 8: the continued fraction recovers an exact word, and bounds the slop
    t345 = snap_t(Decimal("0.927295218001612"))
    assert t345 == F(1, 2), t345          # atan(4/3): the 3-4-5 word has t = sin/(1+cos) = 1/2
    half = TG.HALF_PI / 2
    t45 = snap_t(half)
    c45, s45 = spinor(t45)
    assert c45 * c45 + s45 * s45 == 1
    err = abs(F(Decimal(half).__str__()) if False else F(2) - F(0))
    with localcontext() as ctx:
        ctx.prec = 60
        cdec, sdec = TG.cos_sin(half)
        tdec = sdec / (1 + cdec)
        err = abs(tdec - (Decimal(t45.numerator) / Decimal(t45.denominator)))
    assert err < Decimal("1e-10"), err
    assert Decimal(15) * 2 * err < Decimal("3e-9"), err
    print(f"  8. continued fractions at q <= 100000: the 3-4-5 angle gives t = 1/2 exactly, the "
          f"45-degree angle gives q = {t45.denominator} with |t - p/q| = {err:.2e} (< 1e-10), "
          f"i.e. under 3e-9 of positional slop at k = 15")
    checks += 1

    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  7. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")
    checks += 1
    print(f"snap_certify selftest OK ({checks} controls)")
    return 0


# ----------------------------------------------------------------------- run
def load_delivered():
    import scale_motifs as SM
    return {n: s for n, (s, _cells) in SM.load_delivered().items()}


def run(write: bool = False) -> int:
    if not os.path.exists(PROPOSALS):
        print(f"no proposals at {os.path.relpath(PROPOSALS, ROOT)}")
        return 0
    deliv = load_delivered()
    rows = []
    with open(PROPOSALS) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    print(f"proposals read: {len(rows)}")
    results = []
    poses = {}
    for rec in rows:
        n = rec["n"]
        k = rec["k"]
        target_L = Q(k) - Q(SHRINK)
        cells, words = snap_pose(rec)
        pre = QS.gate(cells, words, Q)
        pen_before = None
        if not pre["ok"]:
            wp = worst_pair(cells, words)
            pen_before = str(wp[0]) if wp else "0"
        fixed, iters, res = relax_simultaneous(cells, words, target_L)
        poses[n] = (fixed, words, target_L)
        v = adjudicate(n, fixed, words, target_L, deliv[n])
        out = {"n": n, "k": k, "rank": rec["rank"], "tier": rec["tier"],
               "anneal_pen": rec["pen"], "anneal_side": rec["side"],
               "target_L": str(target_L), "snap_pen": pen_before,
               "repair_iters": iters, "repair_residual": str(res),
               "verdict": v}
        results.append(out)
        print(f"  n={n:4d} k={k:2d} anneal pen {Decimal(rec['pen']):.2e} side "
              f"{Decimal(rec['side']):.9f} -> snap pen {pen_before} -> repair residual "
              f"{dec(res):.2e} :: "
              f"{'PASS' if out['verdict'].get('C2') else out['verdict'].get('why', 'refused')}")
    passed = [r for r in results if r["verdict"].get("C2")]
    ledger = {"instrument": "snap_certify.py", "schema": "snap-certify/1",
              "proposals": len(rows), "passed": len(passed), "results": results}
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"passed C1-C2: {len(passed)}; ledger {os.path.relpath(LEDGER, ROOT)}")
    if passed and write:
        return promote(passed, deliv, poses)
    if passed:
        print("a candidate passed: re-run with --write to render and promote it")
    return 0


def promote(passed, deliv, poses) -> int:
    """C4: render at 12 dp, re-gate the rendered row exactly, write the CSV, run the guards."""
    import shutil
    import subprocess
    rec = passed[0]
    n = rec["n"]
    cells, words, target_L = poses[n]
    rendered, shift = render(cells, words)
    # C4a: the printed angle must re-snap to the same rational spinor
    rwords = [spinor(snap_t(cell["angle"])) for cell in rendered]
    if rwords != list(words):
        print(f"n={n}: the 12-dp angle does not re-snap to its spinor; refusing to promote")
        return 1
    # C4b: the printed centres, taken as exact decimals, must still gate inside the target
    rcells = [(Q(snap_pos(cell["x"])), Q(snap_pos(cell["y"]))) for cell in rendered]
    g = QS.gate(rcells, rwords, Q)
    Ld = Decimal(g["L"].numerator) / Decimal(g["L"].denominator)
    if not g["ok"] or g["L"] > target_L or not (Ld + MARGIN <= deliv[n]):
        print(f"n={n}: the rendered row fails C4 (ok={g['ok']}, L={Ld}, delivered "
              f"{deliv[n]}, rounding shift {shift}); refusing to promote")
        return 1
    print(f"n={n}: C1-C4 pass, L = {Ld} < delivered {deliv[n]} (rounding shift {shift})")
    shutil.copy2(SUBMISSION, BACKUP)
    with open(SUBMISSION, newline="") as f:
        rows = list(csv.reader(f))
    names, body = rows[0], rows[1:]
    ix = {h: i for i, h in enumerate(names)}
    block = [r for r in body if int(r[ix["n"]]) == n]
    if len(block) != n:
        print(f"n={n}: the CSV holds {len(block)} rows for this n, expected {n}; refusing")
        return 1
    fresh = list(body)
    at = 0
    for i, row in enumerate(body):
        if int(row[ix["n"]]) != n:
            continue
        cell = rendered[at]
        fresh[i] = [row[ix["id"]], str(n), row[ix["square_id"]],
                    str(cell["x"]), str(cell["y"]), str(cell["angle"])]
        at += 1
    with open(SUBMISSION, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(names)
        w.writerows(fresh)
    print("  running sqscore and record_guard")
    ok = True
    for cmd in (["python3", "scripts/sqscore.py"], ["python3", "scripts/record_guard.py"]):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        print((r.stdout or r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else "")
        ok = ok and r.returncode == 0
    if not ok:
        shutil.copy2(BACKUP, SUBMISSION)
        print("  a guard refused the promotion: the CSV is restored")
        return 1
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--baseline" in sys.argv:
        path = (sys.argv[sys.argv.index("--baseline") + 1]
                if sys.argv.index("--baseline") + 1 < len(sys.argv) else
                "workspace/push/clamped_baseline.json")
        return do_baseline(path)
    return run(write="--write" in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
