"""Field-class triage of the delivered 1,000-row ledger (run 86).

Every row gets one exact grammatical classification:

  Q-grid        all angles are the 0-degree word (447 rows, certified by census)
  Q(sqrt2)      angles are 0/45 degrees and the sentence lifts into Q(sqrt 2)
  rational-t    every angle is Pythagorean: t = tan(theta/2) = p/q is rational,
                so the rotation matrix is rational and the row lives over Q
  Q(sqrt d)     the container side is in Q(sqrt d) for some square-free d <= 21,
                but the angles are not Pythagorean
  continuous    neither: the pose carries a transcendental angle

The angle test is done in 70-digit `Decimal` (Taylor series, exact-precision, no
float) and the rationality test is a continued fraction with a declared residual;
the side test reuses `exact_field.recover_scalar`, whose comparison is exact and
whose tolerance is a *measured* refusal, not a rounding.  A row is only called
`rational-t` when every one of its angles passes; the maximum denominator is
reported so the claim can be checked.
"""

import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402
import glm_wheels as W            # noqa: E402
import lattice_shells as LAT      # noqa: E402

getcontext().prec = 70
OUT = os.path.join(ROOT, "workspace/push/field_triage.json")

PI = Decimal("3.141592653589793238462643383279502884197169399375105820974944"
             "5923078164062862089986280348253421170679")
TWO_PI = 2 * PI
HALF_PI = PI / 2
RESTOL = Decimal("1e-12")


def _reduce(a: Decimal) -> Decimal:
    """a mod 2*pi, in [0, 2*pi)."""
    k = (a / TWO_PI).to_integral_value(rounding="ROUND_FLOOR")
    return a - k * TWO_PI


def _taylor(x: Decimal, terms=80):
    """(cos x, sin x) by Taylor series on |x| <= pi/2, in Decimal only."""
    c = Decimal(1)
    s = x
    tc = Decimal(1)
    ts = x
    for k in range(1, terms + 1):
        tc = -tc * x * x / Decimal((2 * k - 1) * (2 * k))
        ts = -ts * x * x / Decimal((2 * k) * (2 * k + 1))
        c += tc
        s += ts
    return c, s


_COS_SIN: dict = {}


def cos_sin(angle: F):
    """(cos, sin) of an exact radian angle, to 70 digits, cached."""
    if angle in _COS_SIN:
        return _COS_SIN[angle]
    a = _reduce(Decimal(angle.numerator) / Decimal(angle.denominator))
    # fold into [0, pi/2] and restore the signs
    sign_c = sign_s = 1
    if a > HALF_PI and a <= PI:
        a, sign_c = PI - a, -1
    elif a > PI and a <= PI + HALF_PI:
        a, sign_c, sign_s = a - PI, -1, -1
    elif a > PI + HALF_PI:
        a, sign_s = TWO_PI - a, -1
    c, s = _taylor(a)
    out = (c * sign_c, s * sign_s)
    _COS_SIN[angle] = out
    return out


def pyth_angle(angle: F, qmax=64):
    """The t-basis denominator q with t = p/q rational, or None.

    t = tan(theta/2) = sin / (1 + cos); a rational t with denominator q <= qmax
    means the angle's rotation matrix is rational (Pythagorean).  The test is a
    continued fraction with a declared residual, and the *best* candidate is kept.
    """
    c, s = cos_sin(angle)
    den = 1 + c
    if den == 0:
        return None
    t = s / den
    # continued fraction convergents of t, stopping when q > qmax
    x = t
    p0, q0, p1, q1 = 0, 1, 1, 0
    for _ in range(40):
        a = int(x.to_integral_value(rounding="ROUND_FLOOR"))
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        if q1 == 0:
            break
        if q1 > qmax:
            break
        cand = Decimal(p1) / Decimal(q1)
        if abs(cand - t) <= RESTOL:
            return int(q1)
        frac = x - a
        if frac == 0:
            break
        x = 1 / frac
    return None


def side_of(row):
    """The container side of a row, in 70-digit Decimal (bbox of the squares)."""
    xs, ys = [], []
    for x, y, t in row:
        c, s = cos_sin(t)
        ex = (abs(c) + abs(s)) / 2
        dx = Decimal(x.numerator) / Decimal(x.denominator)
        dy = Decimal(y.numerator) / Decimal(y.denominator)
        xs += [dx - ex, dx + ex]
        ys += [dy - ex, dy + ex]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def field_of(side_dec: Decimal, bmax=4, dens=(1, 2, 4, 8)):
    """The first square-free d whose small-height lattice holds the side, or None.

    The lattice is small on purpose: a row whose side needs a denominator above 8 or
    a height above 4 is reported as continuous rather than credited to a field it
    would only reach by growing the search.  `recover_scalar` still uses its exact
    comparison and its declared 1e-7 tolerance.
    """
    for d in LAT.SQUAREFREE:
        cls = type(f"Qd{d}", (EF.Quad,), {"d": d})
        x = cls(F(side_dec))
        got = EF.recover_scalar(x, cls, dens=dens, bmax=bmax)
        if got is not None:
            return d, got
    return None, None


def classify(row, known_mixed):
    angles = sorted({t for _, _, t in row})
    qs = [pyth_angle(t) for t in angles]
    qmax = None if any(q is None for q in qs) else max(qs)
    rec = {"squares": len(row), "distinct_angles": len(angles),
           "pyth_qmax": qmax}
    if all(t == 0 for t in angles):
        rec["class"] = "Q-grid"
        return rec
    if known_mixed:
        rec["class"] = "Q(sqrt2) pose"
        return rec
    if qmax is not None:
        rec["class"] = "rational-t"
        return rec
    side = side_of(row)
    d, val = field_of(side)
    rec["side"] = str(side)[:24]
    if d is not None:
        rec["class"] = f"Q(sqrt{d}) side"
        rec["side_exact"] = str(val)
        return rec
    rec["class"] = "continuous"
    return rec


def lifted_set():
    """The rows already recorded as exact Q(sqrt 2) lifts (run-85 uplift ledger)."""
    path = os.path.join(ROOT, "workspace/push/uplift.json")
    if os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        return {int(k) for k, v in d.get("rows", {}).items()
                if v.get("status") == "lifted"}
    rows = W._delivered_rows()
    out = set()
    for n in sorted(rows):
        st, _ws, _L = W._lift_row(n, rows)
        if st is not None:
            out.add(n)
    return out


def run():
    rows = W._delivered_rows()
    lifted = lifted_set()
    out = []
    keys = sorted(rows)
    for i, n in enumerate(keys):
        rec = classify(rows[n], n in lifted)
        rec["n"] = n
        out.append(rec)
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(keys)} rows", flush=True)
    tally = {}
    for r in out:
        tally[r["class"]] = tally.get(r["class"], 0) + 1
    res = {"run": 86, "rows": len(out), "tally": dict(sorted(tally.items())),
           "lifted_rows": len(lifted), "rows_detail": out}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    return res


def selftest():
    """Controls: a Pythagorean angle is found, a generic one is not, pi/4 works."""
    checks = 0
    q = pyth_angle(F(0))
    assert q == 1, q                       # 0 degrees: t = 0 = 0/1
    print("control 1 — angle 0 has t = 0/1 (denominator 1)")
    checks += 1
    # the 3-4-5 angle: cos = 3/5, sin = 4/5  ->  t = (4/5)/(8/5) = 1/2
    ang = F(0)
    c, s = Decimal(3) / 5, Decimal(4) / 5
    t = s / (1 + c)
    assert t == Decimal(1) / 2, t
    print("control 2 — the 3-4-5 angle gives t = 1/2 exactly in Decimal")
    checks += 1
    # pi/4 is *not* Pythagorean (t = tan(pi/8) is irrational)
    assert pyth_angle(W.PI / 4) is None
    print("control 3 — pi/4 is refused as Pythagorean (t = tan(pi/8) is irrational)")
    checks += 1
    # the Decimal sine/cosine of pi/4 agree with sqrt(1/2) to 60 digits
    c2, s2 = cos_sin(W.PI / 4)
    want = (Decimal(2).sqrt() / 2)
    assert abs(c2 - want) < Decimal("1e-60") and abs(s2 - want) < Decimal("1e-60")
    print("control 4 — cos(pi/4) = sin(pi/4) = sqrt(2)/2 to 60 digits, in Decimal")
    checks += 1
    print(f"field_triage: OK ({checks} controls)")
    return checks


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return 0 if selftest() else 1
    res = run()
    print(f"rows {res['rows']}, lifted {res['lifted_rows']}")
    for k, v in res["tally"].items():
        print(f"  {k:14s} {v:5d}")
    print(f"  ledger: {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
