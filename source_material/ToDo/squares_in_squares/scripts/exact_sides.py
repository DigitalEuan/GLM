#!/usr/bin/env python3
r"""exact_sides.py — item 3's leftover: the exact algebraic side of every row.

WHAT "EXACT" MEANS HERE, AND WHAT IT CANNOT MEAN.

The delivered table stores centres and angles as decimals.  A decimal angle is a
*rational* number, and cos of a non-zero rational is transcendental
(Lindemann-Weierstrass), so the side computed from the stored decimals is not
itself an algebraic number of low degree -- for any row containing a rotated
square.  The object that is algebraic is the **ideal** side: the side of the
construction whose angles are the exact ones (0, pi/4, arctan(p/q), ...) that the
stored decimals approximate.

So this instrument identifies, per row, the exact element of a declared
number field that the side lies in, using exact rational arithmetic throughout:

    every angle a multiple of pi/2      ex = 1/2                 L in Q
    every angle also a multiple of pi/4 ex = sqrt(2)/2           L in Q(sqrt 2)
    every angle Pythagorean (p,q,c)     ex = (|p|+|q|)/(2c)      L in Q

where ex is the square's half-extent.  For those rows the side is computed as

    L = A + B * sqrt(2)/2,        A, B rational (B an integer count)

with A built from the stored decimals *exactly* (`Fraction(str(x))`) and B an
integer, so the computation is exact: max/min over the four extremes are decided
by `q2_sign`, which compares `a + b*sqrt(2)/2` by squaring, never by a float.
`ideal` is the construction's own value, recovered by searching A' (denominator
<= 24) and B' (|B'| <= B_MAX) for the element closest to the stored side, and
`residual` is the distance between the two -- the table's 1e-9 clearance, not a
numerical error.  B' has to be searched rather than read off the state: the
state's B counts only the 45-degree squares that touch a wall (it is 0, +-1 or
+-2 always), while the construction's algebraic value can carry a larger
coefficient of sqrt(2).  n = 326 is the example: its stored side is rational
(B = 0) yet equals `15 + (5/2)sqrt(2)` to 4e-9.

Rows containing a generic angle are recorded as **not expressible**: their side is
not in Q(sqrt 2) at all, and this instrument says so with the count of generic
squares rather than inventing an expression.

CONTROLS.
  1  the delivered table reproduces (sqscore.guard);
  2  for every expressible row the exact side agrees with `sqscore.extent` (the
     float scorer) to better than 1e-9 -- exact arithmetic and the scorer that
     produces the published score cannot disagree;
  3  known values: n = 15 and n = 361 have ideal side 4 and 19 (grid rows), and
     n = 326 (angles only 0 and pi/4) is expressible in Q(sqrt 2);
  4  the classifier is calibrated: pi/4 -> 45 deg with ex = sqrt(2)/2,
     arctan(3/4) -> Pythagorean with ex = 7/10, 0.3 rad -> generic.

READ-ONLY apart from `workspace/push/exact_sides.json`.

    python3 scripts/exact_sides.py --selftest
    python3 scripts/exact_sides.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import sqscore as SQ         # noqa: E402

ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "workspace/push/exact_sides.json")
getcontext().prec = 50
#: declared height bound for the construction's own rational part
DEN_MAX = 24
#: and for its coefficient of sqrt(2)/2
B_MAX = 12
#: how far the stored decimals may sit from the construction's exact side
TOL = 1e-8


def dec_q2(a: Fraction, b: Fraction) -> Decimal:
    """a + b*sqrt(2)/2 to 40 digits (a display and a bound, not a decision)."""
    return Decimal(a.numerator) / Decimal(a.denominator) + (
        Decimal(b.numerator) / Decimal(b.denominator)) * Decimal(2).sqrt() / 2


def q2_sign(a: Fraction, b: Fraction) -> int:
    """Sign of a + b*sqrt(2)/2, exactly (no decimals, no floats)."""
    if a == 0 and b == 0:
        return 0
    if a == 0:
        return 1 if b > 0 else -1
    if b == 0:
        return 1 if a > 0 else -1
    if (a > 0) == (b > 0):
        return 1 if a > 0 else -1
    # opposite signs: |a| vs |b|*sqrt(2)/2, decided by squaring
    lhs, rhs = a * a, b * b / 2
    if lhs > rhs:
        return 1 if a > 0 else -1
    if lhs < rhs:
        return -1 if a > 0 else 1
    return 0


def class_ext(theta) -> tuple:
    """(class, a, b) with the square's half-extent = a + b*sqrt(2)/2."""
    t = float(theta)
    if abs(math.sin(2.0 * t)) < 1e-9:            # multiple of pi/2
        return "axis", Fraction(1, 2), Fraction(0)
    if abs(abs(math.sin(t)) - abs(math.cos(t))) < 1e-9:   # odd multiple of pi/4
        return "45", Fraction(0), Fraction(1)
    tn = math.tan(t)
    if abs(tn) < 1e6:
        fr = Fraction(tn).limit_denominator(1000)
        p, q = fr.numerator, fr.denominator
        c2 = p * p + q * q
        c = math.isqrt(c2)
        if c * c == c2 and abs(tn - p / q) < 1e-9:
            return "pyth", Fraction(abs(q) + abs(p), 2 * c), Fraction(0)
    return "generic", None, None


def exact_side(state):
    """(A, B, class counts) with L = A + B*sqrt(2)/2 exactly, or (None, ..)."""
    cls = {"axis": 0, "45": 0, "pyth": 0, "generic": 0}
    terms = []
    for x, y, t in state:
        c, a, b = class_ext(t)
        cls[c] += 1
        if c != "generic":
            terms.append((Fraction(str(float(x))), Fraction(str(float(y))), a, b))
    if cls["generic"]:
        return None, None, cls
    best = None
    for axis in (0, 1):
        hi = lo = None
        for term in terms:
            v = term[axis]
            a, b = term[2], term[3]
            up, dn = (v + a, b), (v - a, -b)
            if hi is None or q2_sign(up[0] - hi[0], up[1] - hi[1]) > 0:
                hi = up
            if lo is None or q2_sign(dn[0] - lo[0], dn[1] - lo[1]) < 0:
                lo = dn
        span = (hi[0] - lo[0], hi[1] - lo[1])
        if best is None or q2_sign(span[0] - best[0], span[1] - best[1]) > 0:
            best = span
    return best[0], best[1], cls


def mix_of(cls: dict) -> str:
    if cls["generic"]:
        return "generic"
    parts = [k for k in ("45", "pyth") if cls[k]]
    return "+".join(parts) if parts else "axis"


def expr_of(a: Fraction, b: Fraction) -> str:
    """A readable exact expression; a alone when the sqrt(2) part vanishes."""
    if b == 0:
        return str(a)
    head = "" if a == 0 else f"{a} "
    sign = "+" if b > 0 else "-"
    mag = abs(b)
    tail = "sqrt(2)/2" if mag == 1 else f"{mag}*sqrt(2)/2"
    return f"{head}{sign} {tail}".strip()


def row_record(n: int, state) -> dict:
    L_float = SQ.extent(state)
    A, B, cls = exact_side(state)
    rec = {"n": n, "L_float": L_float, "mix": mix_of(cls),
           "angles": dict(cls)}
    if A is None:
        rec.update(expressible=False,
                   why=f"{cls['generic']} of {len(state)} angles are generic")
        return rec
    best = None
    dec_a = Decimal(A.numerator) / Decimal(A.denominator)
    for bp in range(-B_MAX, B_MAX + 1):
        target = dec_a + dec_q2(Fraction(0), Fraction(B - bp))
        ap = Fraction(target).limit_denominator(DEN_MAX)
        mag = abs(float(dec_q2(A - ap, B - bp)))
        if best is None or mag < best[0]:
            best = (mag, ap, bp, A - ap, B - bp)
    mag, ap, bp, da, db = best
    rec.update(expressible=True, A=str(A),
               B=int(B) if B.denominator == 1 else str(B),
               expr=expr_of(A, B), ideal=expr_of(ap, bp),
               residual=mag,
               residual_exact=f"({da}) + ({db})*sqrt(2)/2",
               residual_ok=mag <= TOL,
               agrees_with_scorer=abs(float(dec_q2(A, B) - Decimal(repr(L_float))))
               <= 1e-9)
    return rec


def selftest(per: dict) -> int:
    print("control 1 — the delivered table reproduces")
    s = SQ.guard(per, quiet=True)
    print(f"  score {s['score']:.9f}, {s['beats']} beats, {s['grid']} grid rows")

    print("control 2 — the exact side agrees with the float scorer")
    worst, n_ok, n_ex = 0.0, 0, 0
    for n in sorted(per):
        A, B, cls = exact_side(per[n])
        if A is None:
            continue
        n_ex += 1
        d = abs(float(dec_q2(A, B)) - SQ.extent(per[n]))
        worst = max(worst, d)
        assert d <= 1e-9, (n, d)
        n_ok += 1
    print(f"  {n_ok} of {n_ex} expressible rows agree with sqscore.extent "
          f"(worst {worst:.2e})")

    print("control 3 — known rows")
    for n, want in ((15, 4.0), (361, 19.0)):
        rec = row_record(n, per[n])
        assert rec["expressible"], rec
        assert abs(float(dec_q2(Fraction(rec["ideal"].split()[0]), Fraction(0))) - want) < 1e-6, \
            (n, rec["ideal"])
    r326 = row_record(326, per[326])
    assert r326["expressible"] and "45" in r326["mix"], r326
    print(f"  n=15 and n=361 have ideal sides 4 and 19; n=326 is {r326['mix']} "
          f"with exact side {r326['expr']}")

    print("control 4 — the classifier is calibrated")
    c, a, b = class_ext(math.pi / 4)
    assert c == "45" and a == 0 and b == 1, (c, a, b)
    c, a, b = class_ext(math.atan(3 / 4))
    assert c == "pyth" and a == Fraction(7, 10), (c, a, b)
    c, a, b = class_ext(0.3)
    assert c == "generic", (c, a, b)
    print("  pi/4 -> 45 deg (ex = sqrt2/2); arctan(3/4) -> Pythagorean "
          "(ex = 7/10); 0.3 rad -> generic")
    print("selftest: OK")
    return 0


def run(per: dict, write: bool = True) -> int:
    SQ.guard(per, quiet=True)
    rows = [row_record(n, per[n]) for n in sorted(per)]
    ex = [r for r in rows if r["expressible"]]
    nx = [r for r in rows if not r["expressible"]]
    by_mix: dict[str, int] = {}
    for r in rows:
        by_mix[r["mix"]] = by_mix.get(r["mix"], 0) + 1

    print(f"rows {len(rows)}: {len(ex)} expressible exactly, {len(nx)} not")
    print("\nby angle mix (the field the side lies in):")
    for k in ("axis", "45", "pyth", "45+pyth", "generic"):
        if k in by_mix:
            where = {"axis": "Q", "45": "Q(sqrt2)", "pyth": "Q",
                     "45+pyth": "Q(sqrt2)", "generic": "-"}[k]
            print(f"  {k:9s} {by_mix[k]:4d}   L in {where}")

    bad = [r for r in ex if not r.get("residual_ok", True)]
    print(f"\nresidual |ideal - stored side| over the {len(ex)} expressible rows:")
    if ex:
        res = sorted(abs(r["residual"]) for r in ex)
        print(f"  median {res[len(res)//2]:.3e}, max {res[-1]:.3e}, "
              f"over TOL({TOL:g}): {len(bad)}")
    disagree = [r["n"] for r in ex if not r.get("agrees_with_scorer", True)]
    print(f"  exact vs float scorer disagreements: {len(disagree)}")

    print("\nexamples:")
    for n in (5, 11, 15, 50, 290, 326, 344, 345, 982):
        if n in per:
            r = row_record(n, per[n])
            if r["expressible"]:
                print(f"  n={n:4d} {r['mix']:9s} L = {r['expr']}  "
                      f"(ideal {r['ideal']}, residual {r['residual']:+.2e})")
            else:
                print(f"  n={n:4d} {r['mix']:9s} not expressible: {r['why']}")

    out = {"note": "exact algebraic side per row: L = A + B*sqrt(2)/2 in the "
                   "declared angle classes, exact rational arithmetic; rows with "
                   "a generic angle are recorded as not expressible",
           "den_max": DEN_MAX, "tol": TOL,
           "summary": {"rows": len(rows), "expressible": len(ex),
                       "not_expressible": len(nx), "by_mix": by_mix,
                       "residual_over_tol": [r["n"] for r in bad],
                       "scorer_disagreements": disagree},
           "rows": rows}
    if write:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nledger -> {os.path.relpath(LEDGER, ROOT)}")
    return 0


def main() -> int:
    per = SQ.load()
    if "--selftest" in sys.argv:
        return selftest(per)
    return run(per, write="--no-write" not in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
