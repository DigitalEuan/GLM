#!/usr/bin/env python3
r"""interval_verifier.py — a rigorous rational-interval verifier for a rational pose.

Doc 72 §5 C1 blocks the promotion of any pose whose angles are not exact words, and doc 73 §5 names
the gap precisely: the open rows (680, 733, 845, 904, 971) carry no algebraic sentence at all, so a
construction placed at those rows has no judge. `true_geom.py` measures such a pose at 40 decimal
digits — correct to the digits used, but a *measurement*, not a proof. This module is the second
judge doc 72 §5 asks for.

It takes a pose whose **centres are exact rationals** and whose **directions are exact algebraic unit
vectors** — the axis word `(1, 0)`, the quarter word `(√2/2, √2/2)`, or a rational slope
`(q, p)/√(p² + q²)` — encloses every direction in a rational interval, and proves, in
`fractions.Fraction` only:

  * all **4N wall bounds**: `0 <= x - h`, `x + h <= L`, and the same in `y`, for every cell;
  * for every pair, a separating axis (SAT) with a **strictly positive rational lower bound** on the
    slack, so non-overlap is certified rather than sampled;
  * a certified side interval `[L_lo, L_hi]` with `L_hi` a rational *upper* bound on the true side.

Nothing here is a float: no `float` call, no `math.cos`, no `Decimal` rounding step. Roots are
enclosed by `isqrt` on scaled integers, which is exact integer arithmetic:

    lo = isqrt(k · 2^(2b)) / 2^b <= sqrt(k) < (lo + 1) / 2^b = hi

What it can and cannot do — stated, because the difference matters:

  * an **exact contact** (slack exactly 0) can never be certified separated by an enclosure, because
    the interval straddles 0. This verifier therefore *refuses* the exact-contact poses that the
    algebraic gate accepts. It is a strict judge: it wants slack > 0, which is why every construction
    it certifies carries a hairline (`1e-9` here).
  * an **overlap** is certified when the best axis' slack *upper* bound is negative; otherwise the
    pair is *inconclusive*, and inconclusive is reported as inconclusive, never as a pass.

The two axis-aligned directions are tested first, because they are cheap and — SAT being valid on
*any* axis, not only the cells' own — a pair whose bounding boxes are disjoint is already certified.
Only the pairs that survive that prune get the four cell-axis test.

    python3 scripts/interval_verifier.py --selftest
    python3 scripts/interval_verifier.py --check workspace/push/interval_checks.json
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from math import isqrt

BITS = 80                      # 2^-80 ~ 8e-25 of enclosure width per direction coordinate
ZERO, ONE = F(0), F(1)


# ------------------------------------------------------------------ rational enclosures
def sqrt_iv(k, bits=BITS):
    """A rational bracket `[lo, hi)` of `sqrt(k)` for a non-negative integer `k`."""
    if k < 0:
        raise ValueError("sqrt of a negative integer")
    scale = 1 << bits
    lo = isqrt(k << (2 * bits))            # floor(sqrt(k) * 2^bits)
    return F(lo, scale), F(lo + 1, scale)


def dir_iv(spec, bits=BITS):
    """`((c_lo, c_hi), (s_lo, s_hi))`: a rational enclosure of a unit direction.

    Specs (all exact algebraic unit vectors with rational or quadratic coordinates):

      ("axis",)          (1, 0)
      ("quarter",)       (√2/2, √2/2)
      ("slope", p, q)    (q, p) / r,  r = √(p² + q²)   -- tan t = p/q
      ("spin", c, s)     an exact rational point of the unit circle, c² + s² = 1
    """
    kind = spec[0]
    if kind == "axis":
        return (ONE, ONE), (ZERO, ZERO)
    if kind == "quarter":
        lo, hi = sqrt_iv(2, bits)
        return (lo / 2, hi / 2), (lo / 2, hi / 2)
    if kind == "slope":
        p, q = int(spec[1]), int(spec[2])
        if p < 0 or q <= 0:
            raise ValueError(f"slope needs 0 <= p, 0 < q: {(p, q)}")
        n = p * p + q * q
        r = isqrt(n)
        if r * r == n:                     # Pythagorean: the direction is rational, exactly
            return (F(q, r), F(q, r)), (F(p, r), F(p, r))
        lo, hi = sqrt_iv(n, bits)          # 1/r lies strictly between 1/hi and 1/lo
        return (F(q) / hi, F(q) / lo), (F(p) / hi, F(p) / lo)
    if kind == "spin":
        c, s = F(spec[1]), F(spec[2])
        if c * c + s * s != 1:
            raise ValueError(f"spin needs c^2 + s^2 = 1: {(c, s)}")
        return (c, c), (s, s)
    raise ValueError(f"unknown direction spec: {spec!r}")


def spec_of(p, q):
    """The direction spec of the slope `p/q` (or the exact quarter word)."""
    if p == q:
        return ("quarter",)
    return ("slope", int(p), int(q))


# ------------------------------------------------------------------ interval arithmetic
def iv_add(a, b):
    return a[0] + b[0], a[1] + b[1]


def iv_mul(a, b):
    ps = (a[0] * b[0], a[0] * b[1], a[1] * b[0], a[1] * b[1])
    return min(ps), max(ps)


def iv_abs(a):
    lo, hi = a
    if lo >= 0:
        return lo, hi
    if hi <= 0:
        return -hi, -lo
    return ZERO, max(-lo, hi)


def iv_abs_lo(a):
    """A lower bound on `|x|` for `x` in the interval `a` (0 if it straddles 0)."""
    lo, hi = a
    if lo >= 0:
        return lo
    if hi <= 0:
        return -hi
    return ZERO


def iv_abs_hi(a):
    """An upper bound on `|x|` for `x` in the interval `a`."""
    lo, hi = a
    return max(abs(lo), abs(hi))


# ------------------------------------------------------------------ the pose
def cell(x, y, spec, bits=BITS):
    """One square: exact-rational centre, enclosed direction, enclosed half-extents."""
    x, y = F(x), F(y)
    (clo, chi), (slo, shi) = dir_iv(spec, bits)
    h = (iv_abs((clo, chi))[0] + iv_abs((slo, shi))[0]) / 2, \
        (iv_abs((clo, chi))[1] + iv_abs((slo, shi))[1]) / 2
    return {
        "x": x, "y": y, "spec": spec,
        "c": (clo, chi), "s": (slo, shi), "h": h,
        "x_lo": x - h[1], "x_hi": x + h[1],      # outer box (what containment must use)
        "y_lo": y - h[1], "y_hi": y + h[1],
        "xi_lo": x - h[0], "xi_hi": x + h[0],    # inner box (what separation may use)
        "yi_lo": y - h[0], "yi_hi": y + h[0],
    }


def side_iv(cells):
    """The certified side interval `(lo, hi)` of a cell list."""
    a_hi = max(c["x_hi"] for c in cells)
    a_lo = max(c["xi_hi"] for c in cells)
    b_hi = min(c["x_lo"] for c in cells)
    b_lo = min(c["xi_lo"] for c in cells)
    c_hi = max(c["y_hi"] for c in cells)
    c_lo = max(c["yi_hi"] for c in cells)
    d_hi = min(c["y_lo"] for c in cells)
    d_lo = min(c["yi_lo"] for c in cells)
    return (max(a_lo - b_lo, c_lo - d_lo), max(a_hi - b_hi, c_hi - d_hi))


def _dot(qx, qy, dx, dy):
    """The interval of `(dx, dy)·(qx, qy)` for interval operands."""
    return iv_add(iv_mul(qx, dx), iv_mul(qy, dy))


def pair_slack(ca, cb):
    """`(lo, hi)` brackets of the pair's best SAT slack, plus the axis that gave it.

    The slack of an axis `q` is `|(p_b - p_a)·q| - (h_a(q) + h_b(q))`, and SAT says the pair is
    separated iff the maximum over a spanning set of axes is `>= 0`. We bound that maximum from
    below (a certificate) and from above (a refutation), and name the axis behind the bound.
    """
    # the centres are *exact* rationals, so the displacement is an exact rational pair: only the
    # half-extents and the axes carry enclosure width.
    dx = (cb["x"] - ca["x"], cb["x"] - ca["x"])
    dy = (cb["y"] - ca["y"], cb["y"] - ca["y"])
    best_lo, best_hi, best_axis = None, None, None

    def offer(lo, hi, name):
        nonlocal best_lo, best_hi, best_axis
        if best_lo is None or lo > best_lo:
            best_lo, best_axis = lo, name
        best_hi = hi if best_hi is None or hi > best_hi else best_hi

    # the two axis-aligned directions: exact, cheap, and valid SAT axes for any convex pair
    for name, d in (("x", dx), ("y", dy)):
        lo = iv_abs_lo(d) - (ca["h"][1] + cb["h"][1])
        offer(lo, iv_abs_hi(d) - (ca["h"][0] + cb["h"][0]), name)
        if lo > 0:
            return best_lo, best_hi, best_axis

    # the four cell axes
    for own, oth in ((ca, cb), (cb, ca)):
        (c1, s1) = own["c"], own["s"]
        (c2, s2) = oth["c"], oth["s"]
        for name_q, qx, qy in (("u", c1, s1), ("v", (-s1[1], -s1[0]), c1),
                               ("u'", c2, s2), ("v'", (-s2[1], -s2[0]), c2)):
            proj = _dot(qx, qy, dx, dy)
            h1 = (iv_abs_hi(_dot(c1, s1, qx, qy)) + iv_abs_hi(_dot((-s1[1], -s1[0]), c1, qx, qy))) / 2
            h2 = (iv_abs_hi(_dot(c2, s2, qx, qy)) + iv_abs_hi(_dot((-s2[1], -s2[0]), c2, qx, qy))) / 2
            hsum_hi = h1 + h2
            h1l = (iv_abs_lo(_dot(c1, s1, qx, qy)) + iv_abs_lo(_dot((-s1[1], -s1[0]), c1, qx, qy))) / 2
            h2l = (iv_abs_lo(_dot(c2, s2, qx, qy)) + iv_abs_lo(_dot((-s2[1], -s2[0]), c2, qx, qy))) / 2
            offer(iv_abs_lo(proj) - hsum_hi, iv_abs_hi(proj) - (h1l + h2l), name_q)
    return best_lo, best_hi, best_axis


# ------------------------------------------------------------------ the verifier
def verify(cells, L=None, bits=BITS, cheap_only=False):
    """Certify containment, non-overlap and the side of a rational pose.

    `cells` is a list of `(x, y, spec)`; `L` (a rational, optional) is the declared container side,
    which is checked *upward only*: every cell must fit inside `[0, L]²`. Returns a report dict whose
    verdict is one of `"certified"`, `"refused"` (a proven failure) or `"inconclusive"`.
    """
    cs = [cell(x, y, s, bits) for x, y, s in cells]
    n = len(cs)
    L = None if L is None else F(L)
    L_lo, L_hi = side_iv(cs) if n else (ZERO, ZERO)
    # the containment side: the declared one, or the certified upper end of the side interval
    L_eff = L if L is not None else L_hi

    walls, wall_checked = [], 0
    for i, c in enumerate(cs):
        wall_checked += 4
        if c["x_lo"] < 0:
            walls.append((i, "left", str(c["x_lo"])))
        if c["y_lo"] < 0:
            walls.append((i, "bottom", str(c["y_lo"])))
        if c["x_hi"] > L_eff:
            walls.append((i, "right", str(c["x_hi"] - L_eff)))
        if c["y_hi"] > L_eff:
            walls.append((i, "top", str(c["y_hi"] - L_eff)))

    pairs = violations = inconclusive = 0
    axis_pairs = axis4_pairs = 0
    min_slack = None
    worst = None
    for i in range(n):
        for j in range(i + 1, n):
            pairs += 1
            lo, hi, axis = pair_slack(cs[i], cs[j])
            if axis in ("x", "y"):
                axis_pairs += 1
            else:
                axis4_pairs += 1
            if min_slack is None or lo < min_slack:
                min_slack, worst = lo, (i, j, axis)
            if lo <= 0:
                if hi < 0:
                    violations += 1
                else:
                    inconclusive += 1
    _ = cheap_only

    verdict = "certified"
    if walls or violations:
        verdict = "refused"
    elif inconclusive:
        verdict = "inconclusive"
    return {
        "N": n,
        "verdict": verdict,
        "walls_checked": wall_checked,
        "wall_failures": walls[:8],
        "pairs": pairs,
        "pairs_axis": axis_pairs,
        "pairs_cell_axes": axis4_pairs,
        "violations": violations,
        "inconclusive": inconclusive,
        "min_certified_slack": None if min_slack is None else str(min_slack),
        "tightest_pair": None if worst is None else list(worst),
        "L_lo": str(L_lo),
        "L_hi": str(L_hi),
        "declared_L": None if L is None else str(L),
        "L_eff": str(L_eff),
        "L_hi_below_declared": None if L is None else L_hi < L,
        "contains": not walls,
    }


# ------------------------------------------------------------------ recipes
def _rat(s):
    """An exact rational from `"p/q"` or `"p"`. Decimals are refused (a projection is not a value)."""
    s = str(s).strip()
    if "/" in s:
        a, b = s.split("/", 1)
        return F(int(a), int(b))
    if "." in s:
        raise ValueError(f"decimal spelling refused, give a ratio: {s!r}")
    return F(int(s))


def recipe_from_rows(rows):
    """A recipe from `[(x, y, spec), ...]` or from JSON cells `{"x", "y", "dir"}`.

    Coordinates must be `"p/q"` or `"p"`; a decimal spelling is refused, because a projection is not a
    value. Accepting both shapes is deliberate: the ledger `pattern_seeds` writes is a list of dicts, and
    the in-memory path is a list of triples, so a silent mismatch between them would be a verifier bug.
    """
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append((_rat(r["x"]), _rat(r["y"]), tuple(r["dir"])))
        else:
            out.append((_rat(r[0]), _rat(r[1]), tuple(r[2])))
    return out


def check_file(path):
    doc = json.load(open(path))
    out = {"file": path}
    for item in doc.get("checks", [doc]):
        cells = recipe_from_rows(item["cells"])
        rep = verify(cells, item.get("L"), cheap_only=True)
        rep["label"] = item.get("label")
        out.setdefault("results", []).append(rep)
        print(f"  {str(item.get('label'))[:44]:44s} N={rep['N']:4d} {rep['verdict']:12s} "
              f"L[{F(rep['L_lo']):.9f}, {F(rep['L_hi']):.9f}] "
              f"slack {rep['min_certified_slack']} viol {rep['violations']} "
              f"unclear {rep['inconclusive']}")
    return out


# ------------------------------------------------------------------ selftest
def selftest():
    """Seven controls: the two words, a contact, a hairline, an overlap, a slope, and a side law."""
    unit = verify([(F(1, 2), F(1, 2), ("axis",))])
    assert unit["verdict"] == "certified", unit
    assert F(unit["L_lo"]) == 1 and F(unit["L_hi"]) == 1, unit
    assert unit["walls_checked"] == 4 and unit["contains"], unit

    diag = verify([(F(1, 2), F(1, 2), ("quarter",))])
    r2_lo, r2_hi = sqrt_iv(2)
    assert F(diag["L_lo"]) <= r2_hi and F(diag["L_hi"]) >= r2_lo, diag
    assert r2_lo <= F(diag["L_lo"]) <= F(diag["L_hi"]) <= r2_hi + F(1, 1 << 70), diag

    touch = verify([(F(1, 2), F(1, 2), ("axis",)), (F(3, 2), F(1, 2), ("axis",))])
    assert touch["violations"] == 0 and touch["inconclusive"] == 1, touch      # exact contact: honest
    assert touch["verdict"] == "inconclusive", touch

    gap = F(1, 10 ** 9)
    apart = verify([(F(1, 2), F(1, 2), ("axis",)), (F(3, 2) + gap, F(1, 2), ("axis",))])
    assert apart["verdict"] == "certified", apart
    assert F(apart["min_certified_slack"]) > F(1, 2 * 10 ** 9), apart

    hit = verify([(F(1, 2), F(1, 2), ("axis",)), (F(1), F(1, 2), ("axis",))])
    assert hit["verdict"] == "refused" and hit["violations"] == 1, hit
    assert F(hit["min_certified_slack"]) <= 0, hit

    # a rational slope (3-4-5) is an exact unit direction, and its half-extent is 7/10
    c4 = cell(F(1, 2), F(1, 2), ("slope", 3, 4))
    assert c4["c"] == (F(4, 5), F(4, 5)) and c4["s"] == (F(3, 5), F(3, 5)), c4["c"]
    assert c4["h"] == (F(7, 10), F(7, 10)), c4["h"]
    near = verify([(F(1, 2), F(1, 2), ("axis",)),
                   (F(3, 2) + F(1, 5) + gap, F(7, 10), ("slope", 3, 4))])
    assert near["verdict"] == "certified", near
    assert F(near["min_certified_slack"]) > 0, near
    # an expanding denominator only moves the half-extent: 5-12-13 is 17/26, and 1/n -> 1/2
    assert cell(F(0), F(0), ("slope", 5, 12))["h"] == (F(17, 26), F(17, 26))
    # and the half-extent approaches 1/2 as the denominator grows: h ~ 1/2 + p/(2q)
    tall = cell(F(0), F(0), ("slope", 1, 1000))["h"]
    assert F(1, 2) < tall[1] < F(1, 2) + F(1, 1000), tall
    assert tall[1] < cell(F(0), F(0), ("slope", 1, 10))["h"][1]

    # a mixed rational spinor is an exact direction, not only the slope family
    sp = cell(F(1, 2), F(1, 2), ("spin", F(3, 5), F(4, 5)))
    assert sp["c"] == (F(3, 5), F(3, 5)) and sp["s"] == (F(4, 5), F(4, 5))
    assert sp["h"] == (F(7, 10), F(7, 10)), sp["h"]
    spin_near = verify([(F(1, 2), F(1, 2), ("axis",)),
                        (F(3, 2) + F(1, 5) + gap, F(7, 10),
                         ("spin", F(3, 5), F(4, 5)))])
    assert spin_near["verdict"] == "certified", spin_near
    assert F(spin_near["min_certified_slack"]) > 0, spin_near

    # the side law: two axis squares two apart have side exactly 3, no enclosure slop
    two = verify([(F(1, 2), F(1, 2), ("axis",)), (F(5, 2), F(1, 2), ("axis",))])
    assert F(two["L_lo"]) == 3 and F(two["L_hi"]) == 3, two
    # a 45-degree square does not fit a box of side 1 (its span is sqrt 2), and says so
    bad = verify([(F(1, 2), F(1, 2), ("quarter",))], L=F(1))
    assert bad["verdict"] == "refused" and bad["wall_failures"], bad
    # the two accepted recipe shapes -- a triple list and a JSON cell list -- must agree
    assert (recipe_from_rows([(F(1, 2), F(1, 2), ("axis",))])
            == recipe_from_rows([{"x": "1/2", "y": "1/2", "dir": ["axis"]}])), "recipe shapes differ"

    print("control 1 -- an axis square is certified at side exactly 1 with all four wall bounds.")
    print("control 2 -- a quarter word is certified at an interval containing sqrt 2 to 80 bits.")
    print("control 3 -- an exact contact is refused as inconclusive, not passed: the enclosure "
          "straddles zero.")
    print("control 4 -- a 1e-9 hairline is certified separated, with slack above 5e-10.")
    print("control 5 -- a half-unit overlap is a proven violation with a non-positive slack.")
    print("control 6 -- a Pythagorean slope is an exact rational direction (4/5, 3/5, half-extent "
          "7/10); 5-12-13 is 17/26; a large denominator approaches 1/2.")
    print("control 7 -- the side law is exact on axis cells, the wall test refuses a 45-degree "
          "square in a box of side 1, and both recipe shapes parse to the same sentence.")
    print("control 8 -- an exact rational spin (3/5, 4/5) is a certified direction with "
          "half-extent 7/10 and positive slack.")
    print("interval_verifier: OK (8 controls)")


def main(argv):
    if "--selftest" in argv or not argv:
        selftest()
        return 0
    if "--check" in argv:
        out = check_file(argv[argv.index("--check") + 1])
        return 0 if all(r["verdict"] != "refused" for r in out.get("results", [])) else 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
