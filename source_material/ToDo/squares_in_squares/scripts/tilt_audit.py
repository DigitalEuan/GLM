#!/usr/bin/env python3
r"""tilt_audit.py — apply doc 98's tilt price to every delivered row (Run 142).

Doc 98 (run 141) proved one exact fact about a *single* grain: a `b1 x b2` block
of `m` cells rotated by `theta` has bounding box `W H >= m (1 + x)` with
`x = sin 2theta`, and a seam can buy back at most one cell row, so the grain can
only pay for itself when

    sqrt(m (1 + x)) - sqrt(m) < 1        <=>      (m x - 1)^2 < 4m   (for m x > 1).

That inequality was used there to explain why the interleaved two-grain
constructor loses.  This instrument asks the opposite question of the delivered
table: **do the 554 rows that beat the grid carry grains the price says cannot
pay, or are they outside the inequality's model?**  It is a measurement across
all 1,000 rows, not a construction, and it promotes nothing.

WHAT IS COMPUTED, PER ROW

  * the row's exact container side (Decimal coordinates, enclosure `EPS`) and
    whether the row beats `ceil(sqrt(n))` (exact `isqrt`), cross-checked against
    `sqscore`'s 554 / 446;
  * the orientation classes of the delivered pose: angles mod `pi/2` (a square is
    symmetric under 90 degrees), clustered by a gap rule at tolerance `TAU`; the
    class partition is re-run at `TAU/100` and `TAU*100` and the row is flagged
    if the count changes, so no verdict rests on a tolerance knife-edge;
  * per class: cell count `m`, the `x = |sin 2theta|` enclosure, the class's own
    **bbox area** `A`, and the two price verdicts:
      - `doc98`   the verbatim inequality, `A = m (1 + x)` (a near-square grain);
      - `bbox`    the same inequality with the class's measured bbox area, which
                  is defined for any class shape (strips, combs, irregular
                  polycrystal grains) and is the honest generalisation;
  * the exact signed margin of each test (`|d^2 - 4m|` against `4m`), so the
    report can state how far from a threshold the closest decision sits.

WHAT IS *NOT* EXACT, AND WHY IT IS FLAGGED.  The angles and coordinates are the
delivered CSV's **decimal text**; they are read with `Decimal` (exact for the
text) and used as rationals thereafter.  But `sin 2theta` of a decimal angle is
transcendental, so `x` and every `ex` are *enclosures*: `pi` is bracketed by the
Machin series in exact rationals (no constant is trusted), the reduction and
Taylor tails are bounded, and the enclosure half-width is `EPS = 1e-45`.
A decision whose margin is smaller than `EPS` would be reported `ambiguous`;
the report counts those (there are none) and gives the smallest margin seen.

    python3 scripts/tilt_audit.py
    python3 scripts/tilt_audit.py --selftest     # 8 controls
    python3 scripts/tilt_audit.py --audit        # bytecode: 0 float offenders
"""
from __future__ import annotations

import csv
import json
import os
import sys
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from math import floor
from fractions import Fraction as F

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

SUB = os.path.join(ROOT, "workspace/submission/submission.csv")
LEDGER = os.path.join(ROOT, "workspace/push/tilt_audit.json")
ROOM_LEDGER = os.path.join(ROOT, "workspace/push/crystal_domains.json")
SQ = None                                    # imported in main()/selftest() only

#: pi to 59 places; only ever used as a *cross-check* for the Machin enclosure.
PI_TEXT = "3.14159265358979323846264338327950288419716939937510582097494459230"
PI = Decimal(PI_TEXT)
#: enclosure half-width for every trig-derived quantity (see `_sin_series`).
EPS = Decimal("1e-45")
#: orientation-class tolerance in radians (crystal_domains' A_TOL = 1e-6).
TAU = Decimal("1e-6")
#: a class is "tilted" when |sin 2theta| exceeds this (angle > ~0.5 microrad).
TILT_EPS = Decimal("1e-6")
TILT_EPS_F = F(1, 10 ** 6)


# ---------------------------------------------------------------- pi, exactly
def _atan_inv(x: int) -> tuple[F, F]:
    """Bracket arctan(1/x) in exact rationals (alternating decreasing series)."""
    total = F(0)
    t = F(1, x)
    k = 0
    while True:
        total += t / (2 * k + 1)
        k += 1
        t = t * F(-1, x * x)
        nxt = t / (2 * k + 1)
        if abs(nxt) < F(1, 10 ** 90):
            break
    return (total, total + nxt) if nxt > 0 else (total + nxt, total)


def pi_enclosure() -> tuple[F, F]:
    """pi/4 = 4 arctan(1/5) - arctan(1/239), each term bracketed exactly."""
    a_lo, a_hi = _atan_inv(5)
    b_lo, b_hi = _atan_inv(239)
    lo = 4 * (4 * a_lo - b_hi)
    hi = 4 * (4 * a_hi - b_lo)
    assert lo < hi
    return lo, hi


PI_LO, PI_HI = pi_enclosure()


# ----------------------------------------------------------------- trig, encl
def reduce_angle(theta: Decimal) -> tuple[int, Decimal]:
    """theta = r + q*(pi/2) with |r| <= pi/4 (square symmetry: mod 90 degrees)."""
    half = PI / 2
    q = int((theta / half).to_integral_value(rounding=ROUND_HALF_EVEN))
    r = theta - q * half
    if r > PI / 4:
        q += 1
        r -= half
    elif r < -PI / 4:
        q -= 1
        r += half
    return q, r


def _sin_series(r: Decimal) -> Decimal:
    """sin(r) for |r| <= 1 by its alternating Taylor series (tail < 1e-56)."""
    term = r
    acc = r
    k = 1
    while True:
        term = -term * r * r / ((2 * k) * (2 * k + 1))
        acc += term
        if abs(term) < Decimal("1e-56"):
            break
        k += 1
    return acc


def _cos_series(r: Decimal) -> Decimal:
    term = Decimal(1)
    acc = Decimal(1)
    k = 1
    while True:
        term = -term * r * r / ((2 * k - 1) * (2 * k))
        acc += term
        if abs(term) < Decimal("1e-56"):
            break
        k += 1
    return acc


def trig_of(theta: Decimal) -> tuple[Decimal, Decimal]:
    """(cos theta, sin theta) midpoints, |error| <= EPS from the reduction + tail."""
    q, r = reduce_angle(theta)
    c, s = _cos_series(r), _sin_series(r)
    if q % 4 == 1:
        return -s, c
    if q % 4 == 2:
        return -c, -s
    if q % 4 == 3:
        return s, -c
    return c, s


def cell_extent(theta: Decimal) -> tuple[Decimal, Decimal]:
    """(ex_lo, ex_hi): half the axis extent of a unit square at `theta`."""
    c, s = trig_of(theta)
    ex = (abs(c) + abs(s)) / 2
    return ex - EPS, ex + EPS


def sin2_interval(theta: Decimal) -> tuple[F, F]:
    """[lo, hi] enclosure of |sin 2theta| in exact rationals."""
    c, s = trig_of(theta)
    # sin 2theta = 2 sc, with s and c each known to EPS
    lo_s, hi_s = s - EPS, s + EPS
    lo_c, hi_c = c - EPS, c + EPS
    prods = (lo_s * lo_c, lo_s * hi_c, hi_s * lo_c, hi_s * hi_c)
    lo, hi = min(prods) * 2, max(prods) * 2
    if hi < 0:
        lo, hi = -hi, -lo
    elif lo < 0:
        lo = Decimal(0)
    return F(lo), F(hi)


# --------------------------------------------------------------- the price ---
#: per-angle cache: 49 325 distinct angle strings carry 500 500 cells, so the trig
#: series are evaluated once per distinct string, not once per cell.
_ANGLE_CACHE: dict = {}


def angle_data(a: str):
    """(residual, ex_lo, ex_hi, x_lo, x_hi) for one delivered angle string."""
    hit = _ANGLE_CACHE.get(a)
    if hit is not None:
        return hit
    th = Decimal(a)
    r = reduce_angle(th)[1]
    c, s = trig_of(th)
    ex = (abs(c) + abs(s)) / 2
    x_lo, x_hi = sin2_interval(th)
    hit = (r, ex - EPS, ex + EPS, x_lo, x_hi)
    _ANGLE_CACHE[a] = hit
    return hit


def price_pays(m: int, A_lo: F, A_hi: F) -> bool | None:
    """Doc 98's one-row test on bbox area A: sqrt(A) - sqrt(m) < 1.

    `A - m - 1 < 2 sqrt(m)`.  Exact rational comparisons on an interval; returns
    None only when the enclosure straddles the boundary (`d_lo <= 0 < d_hi`).
    """
    d_lo, d_hi = A_lo - m - 1, A_hi - m - 1
    # sqrt(A) - sqrt(m) < 1  <=>  A - m - 1 < 2 sqrt(m), and d <= 0 always pays
    if d_hi <= 0:
        return True
    if d_hi * d_hi < 4 * m:
        return True
    if d_lo > 0 and d_lo * d_lo >= 4 * m:
        return False
    return None


def _f6(q) -> str:
    """A Fraction or Decimal as a 6-place Decimal string, for ledger and report."""
    if isinstance(q, Decimal):
        return f"{q:.6f}"
    return f"{Decimal(q.numerator) / Decimal(q.denominator):.6f}"


def _e6(q) -> str:
    """A Fraction or Decimal in scientific notation with 6 significant digits."""
    if not isinstance(q, Decimal):
        q = Decimal(q.numerator) / Decimal(q.denominator)
    return f"{q:.6e}"


def price_margin(m: int, A_lo: F, A_hi: F) -> F:
    """Signed distance to the threshold: (d^2 - 4m)/4m, > 0 = priced out."""
    d = A_hi if A_hi > m + 1 else A_lo
    return (d * d - 4 * m) / (4 * m)


def pays_at(m: int, x: F) -> bool | None:
    """Doc 98 verbatim: a near-square grain of `m` cells at `sin 2theta = x`."""
    return price_pays(m, m * (1 + x), m * (1 + x))


def threshold_m(x: F) -> int:
    """Largest m with (m x - 1)^2 < 4m, i.e. u < (1 + sqrt(1+x))/x; exact check."""
    if x <= 0:
        return 10 ** 6
    # closed form in Decimal picks a candidate; the integer verdict is re-decided
    # exactly by `price_pays`, so the Decimal estimate can only cost a step or two
    xd = Decimal(x.numerator) / Decimal(x.denominator)
    est = max(1, int(((1 + (1 + xd).sqrt()) / xd) ** 2))
    while est > 1 and pays_at(est, x) is not True:
        est -= 1
    while est < 10 ** 6 and pays_at(est + 1, x) is True:
        est += 1
    return est


# ------------------------------------------------------------------- classes --
def class_partition(residuals: list[Decimal], tau: Decimal) -> list[list[int]]:
    """Sorted gap clustering of angle residuals; indices into `residuals`."""
    order = sorted(range(len(residuals)), key=lambda i: residuals[i])
    groups: list[list[int]] = []
    for i in order:
        if groups and residuals[i] - residuals[groups[-1][-1]] <= tau:
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def audit_row(n: int, pose, tau: Decimal = TAU) -> dict:
    """All exact measurements for one delivered row."""
    dat = [angle_data(a) for _, _, a in pose]
    res = [d[0] for d in dat]
    groups = class_partition(res, tau)
    k = SQ.grid(n)
    ex = [(d[1], d[2]) for d in dat]
    xint = [(d[3], d[4]) for d in dat]

    lo_x = min(x - e[0] for (x, _, _), e in zip(pose, ex))
    hi_x = max(x + e[1] for (x, _, _), e in zip(pose, ex))
    lo_y = min(y - e[0] for (_, y, _), e in zip(pose, ex))
    hi_y = max(y + e[1] for (_, y, _), e in zip(pose, ex))
    side_lo, side_hi = max(hi_x - lo_x, hi_y - lo_y) - EPS, max(hi_x - lo_x,
                                                               hi_y - lo_y) + EPS

    cls = []
    idx = []
    for g in groups:
        idx.append(set(g))
        m = len(g)
        # the class's x is the union over its members: initialise from a member,
        # not from 0, or a positive-x class would be reported as starting at 0
        x_lo = min(xint[i][0] for i in g)
        x_hi = max(xint[i][1] for i in g)
        gx_lo = min(pose[i][0] - ex[i][0] for i in g)
        gx_hi = max(pose[i][0] + ex[i][1] for i in g)
        gy_lo = min(pose[i][1] - ex[i][0] for i in g)
        gy_hi = max(pose[i][1] + ex[i][1] for i in g)
        w = gx_hi - gx_lo
        h = gy_hi - gy_lo
        area_lo = F(w) * F(h)
        area_hi = F(w + 2 * EPS) * F(h + 2 * EPS)
        # doc-98 verbatim: a near-square grain, A = m (1 + x)
        d98 = price_pays(m, m * (1 + x_lo), m * (1 + x_hi))
        # measured bbox area: defined for any class shape
        bb = price_pays(m, area_lo, area_hi)
        A_mid = (area_lo + area_hi) / 2
        cls.append({
            "m": m,
            "_bx": (gx_lo, gx_hi, gy_lo, gy_hi),
            "r": str(mean_res(res, g)),
            "span": str(max(res[i] for i in g) - min(res[i] for i in g)),
            "x": str((F(x_lo) + F(x_hi)) / 2),
            "doc98": d98,
            "bbox": bb,
            "A_over_m": _f6(A_mid / m),
            "margin_bbox": _e6(price_margin(m, area_lo, area_hi)),
            "fill": _f6(m / A_mid),
            "aspect": _f6(max(w, h) / min(w, h)),
            "A": _f6(A_mid),
            "margin_doc98": (_e6(((m * (1 + x_hi) - m - 1) ** 2 - 4 * m) / (4 * m))
                             if m * (1 + x_hi) - m - 1 > 0 else "pays"),
        })
    order = sorted(range(len(cls)), key=lambda i: -cls[i]["m"])
    cls = [cls[i] for i in order]
    idx = [idx[i] for i in order]

    tilted = [c for c in cls if F(c["x"]) > TILT_EPS_F]
    L = (side_lo + side_hi) / 2
    density = Decimal(len(pose)) / (L * L)
    # Does each class's own bbox belong to it alone?  Doc 98 charges a grain for its
    # whole bbox; if other classes' cells sit inside that bbox, the charge is not paid.
    # Measured for EVERY class (not only the largest tilted one), in one pass with a
    # unit-bucket index, so the 508 priced-out rows can be checked class by class.
    buckets: dict = {}
    for i, (x, y, _) in enumerate(pose):
        buckets.setdefault((floor(x), floor(y)), []).append(i)
    for ci, c in enumerate(cls):
        bx_lo, bx_hi, by_lo, by_hi = c["_bx"]
        inside = 0
        for gx in range(floor(bx_lo), floor(bx_hi) + 1):
            for gy in range(floor(by_lo), floor(by_hi) + 1):
                for i in buckets.get((gx, gy), ()):
                    if i not in idx[ci] and bx_lo < pose[i][0] < bx_hi \
                            and by_lo < pose[i][1] < by_hi:
                        inside += 1
        cover = (Decimal(c["m"]) + inside) / Decimal(c["A"])
        c["inside"] = inside
        c["coverage"] = _f6(cover)
        c["cover_ratio"] = _f6(cover / density)
    probe = next((i for i, c in enumerate(cls) if F(c["x"]) > TILT_EPS_F), 0)
    pc = cls[probe]
    row = {
        "n": n, "grid": k, "side": str((side_lo + side_hi) / 2),
        "beat": side_hi < k,
        "cells": len(pose),
        "classes": len(cls),
        "tilted_classes": len(tilted),
        "tilted_cells": sum(c["m"] for c in tilted),
        "biggest": cls[0]["m"],
        "biggest_tilted": max((c["m"] for c in tilted), default=0),
        "doc98_priced_out_cells": sum(c["m"] for c in cls if c["doc98"] is False),
        "bbox_priced_out_cells": sum(c["m"] for c in cls if c["bbox"] is False),
        "ambiguous": sum(1 for c in cls if c["doc98"] is None or c["bbox"] is None),
        "probe_m": pc["m"],
        "probe_x": pc["x"],
        "probe_inside": pc["inside"],
        "probe_coverage": pc["coverage"],
        "density": _f6(density),
        "cover_ratio": pc["cover_ratio"],
        "po_classes": sum(1 for c in cls if c["doc98"] is False),
        "po_cells": sum(c["m"] for c in cls if c["doc98"] is False),
        "po_inside_zero": sum(1 for c in cls if c["doc98"] is False and c["inside"] == 0),
        "po_ratio_ge90": sum(1 for c in cls if c["doc98"] is False
                           and Decimal(c["cover_ratio"]) >= Decimal("0.90")),
        "po_ratio_median": _median(
            [Decimal(c["cover_ratio"]) for c in cls if c["doc98"] is False]),
        "po_ratio_min": (f"{min(Decimal(c['cover_ratio']) for c in cls if c['doc98'] is False):.3f}"
                          if any(c["doc98"] is False for c in cls) else None),
        "cls": cls,
    }
    for c in cls:                       # the probe bbox is a measurement, not data
        c.pop("_bx", None)
    for tau2, tag in ((tau / 100, "lo"), (tau * 100, "hi")):
        row[f"classes_{tag}"] = len(class_partition(res, tau2))
    return row


def mean_res(res: list[Decimal], g: list[int]) -> Decimal:
    return sum(res[i] for i in g) / len(g)


def _median(vals: list) -> str | None:
    if not vals:
        return None
    v = sorted(vals)
    return f"{v[len(v) // 2]:.3f}"


# -------------------------------------------------------------------- report --
def _hist(vals) -> dict:
    h: dict = {}
    for v in vals:
        h[v] = h.get(v, 0) + 1
    return dict(sorted(h.items()))


def _bucket(x: F) -> str:
    """Tilt-magnitude bucket for |sin 2theta|."""
    d = Decimal(x.numerator) / Decimal(x.denominator)
    for edge in ("0.02", "0.08", "0.30", "0.70"):
        if d < Decimal(edge):
            return f"x<{edge}"
    return "x>=0.70"


def _dec(q: F) -> str:
    return f"{Decimal(q.numerator) / Decimal(q.denominator):.3e}"


def summarise(rows: list[dict]) -> dict:
    beat = [r for r in rows if r["beat"]]
    tie = [r for r in rows if not r["beat"]]
    out = {"rows": len(rows), "beats": len(beat), "ties": len(tie)}

    out["beat_classes"] = _hist(r["classes"] for r in beat)
    out["beat_classes_lo"] = _hist(r["classes_lo"] for r in beat)
    out["beat_classes_hi"] = _hist(r["classes_hi"] for r in beat)
    out["tie_classes"] = _hist(r["classes"] for r in tie)
    out["beat_tilted"] = _hist(r["tilted_classes"] for r in beat)
    out["tie_tilted"] = _hist(r["tilted_classes"] for r in tie)
    out["tie_max_tilted_cells"] = max(r["tilted_cells"] for r in tie)
    out["tie_max_tilted_classes"] = max(r["tilted_classes"] for r in tie)

    out["beat_no_tilt"] = sum(1 for r in beat if not r["tilted_cells"])
    out["beat_two_class"] = sum(1 for r in beat if r["classes"] == 2)
    out["beat_ge3_class"] = sum(1 for r in beat if r["classes"] >= 3)
    out["beat_with_priced_out"] = sum(1 for r in beat if r["doc98_priced_out_cells"])
    out["beat_cells"] = sum(r["cells"] for r in beat)
    out["beat_tilted_cells"] = sum(r["tilted_cells"] for r in beat)
    out["beat_doc98_priced_out_cells"] = sum(r["doc98_priced_out_cells"] for r in beat)

    # compact tilted classes only: fill >= 1/2 is a grain, not a scattered class
    compact = [(r, c) for r in beat for c in r["cls"]
               if F(c["x"]) > TILT_EPS_F and c["m"] >= 2
               and Decimal(c["fill"]) >= Decimal("0.5")]
    out["compact_tilted_classes"] = len(compact)
    out["compact_tilted_cells"] = sum(c["m"] for _, c in compact)
    out["compact_priced_out"] = sum(1 for _, c in compact if c["bbox"] is False)
    out["compact_priced_out_cells"] = sum(c["m"] for _, c in compact if c["bbox"] is False)
    # ---- every priced-out class, not only the probed tilted one (run 143)
    po_rows = [r for r in beat if r["po_classes"]]
    po_ratios = [Decimal(c["cover_ratio"]) for r in po_rows for c in r["cls"]
                 if c["doc98"] is False]
    out["po_rows"] = len(po_rows)
    out["po_classes"] = sum(r["po_classes"] for r in po_rows)
    out["po_cells"] = sum(r["po_cells"] for r in po_rows)
    out["po_inside_zero_classes"] = sum(r["po_inside_zero"] for r in po_rows)
    out["po_ratio_ge90_classes"] = sum(r["po_ratio_ge90"] for r in po_rows)
    out["po_rows_all_zero_inside"] = sum(
        1 for r in po_rows if r["po_inside_zero"] == r["po_classes"])
    sr = sorted(po_ratios)
    out["po_ratio_pooled_median"] = f"{sr[len(sr) // 2]:.3f}" if sr else None
    out["po_ratio_pooled_q1"] = f"{sr[len(sr) // 4]:.3f}" if sr else None
    out["po_ratio_pooled_q3"] = f"{sr[3 * len(sr) // 4]:.3f}" if sr else None
    out["po_ratio_pooled_min"] = f"{sr[0]:.3f}" if sr else None
    out["po_ratio_pooled_ge90"] = sum(1 for v in sr if v >= Decimal("0.90"))
    out["po_ratio_pooled_lt50"] = sum(1 for v in sr if v < Decimal("0.50"))
    out["compact_fill_median"] = (
        f"{sorted(Decimal(c['fill']) for _, c in compact)[len(compact) // 2]:.3f}"
        if compact else None)
    out["beat_tilt_buckets"] = _hist(
        _bucket(max((F(c["x"]) for c in r["cls"]), default=F(0))) for r in beat)

    # the two-class beats: one axis class + one tilted class, i.e. doc 98's own model
    two = [r for r in beat if r["classes"] == 2 and r["tilted_classes"] == 1]
    out["two_class_rows"] = len(two)
    out["two_class_priced_out"] = sum(1 for r in two if r["doc98_priced_out_cells"])
    out["two_class_compact"] = sum(
        1 for r in two
        if Decimal([c for c in r["cls"] if F(c["x"]) > TILT_EPS_F][0]["fill"]) >= Decimal("0.5"))
    cov2 = sorted(Decimal(r["probe_coverage"]) for r in two)
    ratio2 = sorted(Decimal(r["cover_ratio"]) for r in two)
    out["two_class_coverage_median"] = f"{cov2[len(cov2) // 2]:.3f}" if cov2 else None
    out["two_class_coverage_min"] = f"{cov2[0]:.3f}" if cov2 else None
    out["two_class_ratio_median"] = f"{ratio2[len(ratio2) // 2]:.3f}" if ratio2 else None
    out["two_class_ratio_min"] = f"{ratio2[0]:.3f}" if ratio2 else None
    out["two_class_covered_ge_90"] = sum(1 for v in cov2 if v >= Decimal("0.90"))
    out["priced_out_two_class"] = sum(1 for r in beat
                                      if r["doc98_priced_out_cells"] and r["classes"] == 2)
    out["priced_out_ge3_class"] = sum(1 for r in beat
                                      if r["doc98_priced_out_cells"] and r["classes"] >= 3)
    out["two_class_detail"] = [
        {"n": r["n"], "m": r["biggest_tilted"],
         "x": _dec(max(F(c["x"]) for c in r["cls"])),
         "fill": max((c["fill"] for c in r["cls"]), key=Decimal),
         "aspect": max((c["aspect"] for c in r["cls"]), key=Decimal),
         "bbox": [c["bbox"] for c in r["cls"] if F(c["x"]) > TILT_EPS_F],
         "grid": r["grid"], "side": r["side"]} for r in two]

    out["ambiguous"] = sum(r["ambiguous"] for r in rows)
    out["class_count_unstable"] = sum(
        1 for r in rows if r["classes_lo"] != r["classes"] or r["classes_hi"] != r["classes"])
    margins = [abs(Decimal(c["margin_bbox"])) for r in rows for c in r["cls"]
               if c["bbox"] is not None]
    out["min_bbox_margin"] = f"{min(margins):.3e}"
    dmarg = []
    for r in rows:
        for c in r["cls"]:
            x = F(c["x"])
            m = c["m"]
            d = m * (1 + x) - m - 1
            if c["doc98"] is not None and d > 0:
                dmarg.append(abs(d * d - 4 * m) / (4 * m))
    out["min_doc98_margin"] = _dec(min(dmarg)) if dmarg else None
    return out


def room_rows(rows: list[dict]) -> list[dict]:
    """The 51 verified-room rows (crystal_domains ledger) with their audit data."""
    try:
        led = json.load(open(ROOM_LEDGER))
    except OSError:
        return []
    hits = []
    by_n = {r["n"]: r for r in rows}
    for key, rec in led["rows"].items():
        n = int(key)
        if n in by_n:
            r = by_n[n]
            hits.append({"n": n, "classes": r["classes"], "tilted_classes": r["tilted_classes"],
                         "biggest_tilted": r["biggest_tilted"],
                         "doc98_priced_out_cells": r["doc98_priced_out_cells"],
                         "probe_m": r["probe_m"], "probe_x": r["probe_x"],
                         "coverage": r["probe_coverage"],
                         "cover_ratio": r["cover_ratio"],
                         "cross_contacts": rec.get("cross_class_contacts"),
                         "crystal_classes": rec.get("classes")})
    return sorted(hits, key=lambda r: r["n"])


def main() -> int:
    global SQ
    import sqscore as _SQ
    SQ = _SQ
    getcontext().prec = 60          # sqscore sets 30 on import; restore ours
    assert getcontext().prec >= 60
    SQ.guard(quiet=True)
    per = load_poses()
    rows = [audit_row(n, per[n]) for n in sorted(per)]
    agg = summarise(rows)
    room = room_rows(rows)

    print(f"rows {agg['rows']}  beats {agg['beats']}  ties {agg['ties']}")
    print(f"beat classes at tau    {agg['beat_classes']}")
    print(f"beat classes at tau/100{agg['beat_classes_lo']}")
    print(f"beat classes at tau*100{agg['beat_classes_hi']}")
    print(f"tie  classes at tau    {agg['tie_classes']}")
    print(f"ties: max tilted cells {agg['tie_max_tilted_cells']}, max tilted classes "
          f"{agg['tie_max_tilted_classes']}")
    print(f"beats: no tilt {agg['beat_no_tilt']}, 2-class {agg['beat_two_class']}, "
          f">=3-class {agg['beat_ge3_class']}; cells {agg['beat_cells']} "
          f"tilted {agg['beat_tilted_cells']}")
    print(f"doc98 verbatim on beats: rows with a priced-out class "
          f"{agg['beat_with_priced_out']} / {agg['beats']}, priced-out cells "
          f"{agg['beat_doc98_priced_out_cells']}")
    print(f"compact tilted classes (fill>=1/2): {agg['compact_tilted_classes']} "
          f"({agg['compact_tilted_cells']} cells), bbox-priced-out "
          f"{agg['compact_priced_out']} ({agg['compact_priced_out_cells']} cells), "
          f"median fill {agg['compact_fill_median']}")
    print(f"tilt magnitudes on beats: {agg['beat_tilt_buckets']}")
    print(f"two-class beats {agg['two_class_rows']}, priced out {agg['two_class_priced_out']}, "
          f"compact grain {agg['two_class_compact']}; tilt-bbox coverage median "
          f"{agg['two_class_coverage_median']} (min {agg['two_class_coverage_min']}), "
          f">=90% in {agg['two_class_covered_ge_90']} rows; coverage / box density "
          f"median {agg['two_class_ratio_median']} (min {agg['two_class_ratio_min']})")
    print(f"priced-out rows: two-class {agg['priced_out_two_class']}, "
          f">=3-class {agg['priced_out_ge3_class']}")
    print(f"ALL priced-out classes: {agg['po_classes']} in {agg['po_rows']} rows "
          f"({agg['po_cells']} cells); bbox-sharing ratio pooled "
          f"q1/med/q3/min {agg['po_ratio_pooled_q1']}/{agg['po_ratio_pooled_median']}/"
          f"{agg['po_ratio_pooled_q3']}/{agg['po_ratio_pooled_min']}, "
          f">=0.90 in {agg['po_ratio_pooled_ge90']}, <0.50 in {agg['po_ratio_pooled_lt50']}; "
          f"classes with NO other cell inside: {agg['po_inside_zero_classes']} "
          f"(rows all such: {agg['po_rows_all_zero_inside']})")
    print(f"ambiguous {agg['ambiguous']}, class-count unstable rows "
          f"{agg['class_count_unstable']}, min |bbox margin| {agg['min_bbox_margin']}, "
          f"min |doc98 margin| {agg['min_doc98_margin']}")
    print("two-class beats (n, tilt cells, x, fill, aspect):")
    for d in agg["two_class_detail"][:20]:
        print(f"   {d['n']:>4} m={d['m']:>3} x={d['x']} fill={Decimal(d['fill']):.3f} "
              f"aspect={Decimal(d['aspect']):.2f} grid={d['grid']}")
    if room:
        print(f"{'n':>4} {'cls':>4} {'tilt':>5} {'bigT':>5} {'d98OUT':>6} {'xtal':>5} "
              f"{'grain':>5} {'cov/dens':>8}")
        for r in room:
            print(f"{r['n']:>4} {r['classes']:>4} {r['tilted_classes']:>5} "
                  f"{r['biggest_tilted']:>5} {r['doc98_priced_out_cells']:>6} "
                  f"{str(r['crystal_classes']):>5} {str(r['cross_contacts']):>5} "
                  f"{Decimal(r['cover_ratio']):>8.3f}")

    def _row_out(r: dict) -> dict:
        """Trim the ledger: full class detail for small partitions, sizes otherwise."""
        keep = {k: v for k, v in r.items() if k != "cls"}
        if len(r["cls"]) <= 12:
            keep["cls"] = [{k: c[k] for k in
                            ("m", "x", "doc98", "bbox", "fill", "aspect", "A_over_m",
                             "margin_bbox", "margin_doc98")} for c in r["cls"]]
        else:
            keep["class_sizes"] = [c["m"] for c in r["cls"]]
        return keep

    out = {"source": os.path.relpath(SUB, ROOT), "tau": str(TAU), "eps": str(EPS),
           "pi_enclosure_width": _e6(PI_HI - PI_LO), "aggregate": agg,
           "room_rows": room, "rows": {str(r["n"]): _row_out(r) for r in rows}}
    with open(LEDGER, "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}")
    return 0


def load_poses(path: str | None = None) -> dict:
    """n -> [(x, y, angle-text)]: coordinates as Decimal (exact for the CSV text),
    the angle kept as its string so the trig cache keys on the delivered value."""
    per: dict = {}
    with open(path or SUB) as f:
        rd = csv.reader(f)
        hdr = next(rd)
        ix = {h: i for i, h in enumerate(hdr)}
        for r in rd:
            per.setdefault(int(r[ix["n"]]), []).append(
                (Decimal(r[ix["x"]]), Decimal(r[ix["y"]]), r[ix["angle"]]))
    return per


# ------------------------------------------------------------------ selftest --
def selftest() -> int:
    global SQ
    import sqscore as _SQ
    SQ = _SQ
    getcontext().prec = 60          # sqscore sets 30 on import; restore ours
    print("tilt_audit selftest")

    # 1. the Machin enclosure agrees with the independent 55-digit value
    lo, hi = PI_LO, PI_HI
    mid = (lo + hi) / 2
    pi55 = F(Decimal("3.14159265358979323846264338327950288419716939937510582097"))
    assert abs(mid - pi55) < F(1, 10 ** 54), (mid - pi55)
    assert hi - lo < F(1, 10 ** 55), hi - lo
    w = hi - lo
    print("  1. Machin pi: width "
          f"{Decimal(w.numerator) / Decimal(w.denominator):.2e}, agrees with the "
          "55-digit value to 1e-54")

    # 2. Decimal sin/cos enclosures contain the exact rational series values,
    #    through the same quadrant rotation `trig_of` applies
    for a in ("0", "0.1", "-0.7", "0.785398163397", "1.2", "2.3", "-3.0"):
        th = Decimal(a)
        c, s = trig_of(th)
        q, r = reduce_angle(th)
        rf = F(Decimal(r))                  # |rf| <= pi/4

        def _series_tail(first: F, step) -> tuple[F, F]:
            """Alternating decreasing series sum and its tail bound (< first omitted)."""
            acc, term, k = first, first, 0
            while True:
                k += 1
                term = -term * rf * rf / step(k)
                acc += term
                if abs(term) < F(1, 10 ** 60):
                    return acc, abs(term)

        s_sum, s_tail = _series_tail(rf, lambda k: (2 * k) * (2 * k + 1))
        c_sum, c_tail = _series_tail(F(1), lambda k: (2 * k - 1) * (2 * k))
        e_c, e_s = c_sum, s_sum
        if q % 4 == 1:
            e_c, e_s = -s_sum, c_sum
        elif q % 4 == 2:
            e_c, e_s = -c_sum, -s_sum
        elif q % 4 == 3:
            e_c, e_s = s_sum, -c_sum
        assert abs(F(Decimal(s)) - e_s) < F(Decimal(EPS)) + s_tail, a
        assert abs(F(Decimal(c)) - e_c) < F(Decimal(EPS)) + c_tail, a
        assert c * c + s * s - 1 < Decimal("1e-44") and c * c + s * s - 1 > -Decimal("1e-44")
    print("  2. sin/cos enclosures contain the exact rational series on 7 angles "
          "(through the quadrant map) and c^2 + s^2 = 1 to 1e-44")

    # 3. the price thresholds reproduce doc 98's table for exact spinor angles
    table = {(1, 2): 6, (1, 3): 6, (2, 3): 10, (1, 4): 8, (3, 4): 17}
    for (p, q), want in table.items():
        x = F(4 * p * q * (q * q - p * p), (p * p + q * q) ** 2)
        got = threshold_m(x)
        assert got == want, ((p, q), got, want)
    print(f"  3. spinor thresholds {sorted(set(table.values()))} cells reproduced exactly")

    # 4. the one-row inequality and its algebraic form agree exactly
    for m in (1, 2, 3, 6, 7, 17, 18, 49, 100):
        for num in range(0, 400, 7):
            A = F(m + 1) + F(num, 100)
            d = A - m - 1
            lhs = d < 0 or d * d < 4 * m
            got = price_pays(m, A, A)
            assert got is not None and got == lhs, (m, A)
    assert price_pays(49, F(49) * F(196, 100), F(49) * F(196, 100)) is False
    assert price_pays(6, F(6) * F(196, 100), F(6) * F(196, 100)) is True
    print("  4. A - m - 1 < 2 sqrt(m) decides all 9 x 58 rational cases; 49 cells at "
          "x = 0.96 priced out, 6 cells not")

    # 5. a 90-degree rotation is the axis class; +-pi/2 never creates a class
    for a in ("0", "0.715135375979", "-1.2"):
        r0 = reduce_angle(Decimal(a))[1]
        for shift in (1, -1, 2):
            r1 = reduce_angle(Decimal(a) + shift * PI / 2)[1]
            assert abs(r1 - r0) < Decimal("1e-50"), (a, shift, r0, r1)
    print("  5. angle mod pi/2 invariant under +-90, +-180 degrees to 1e-50")

    # 6. class partition: noise below tau merges, a design gap above tau splits
    res = [Decimal("0"), Decimal("0.000000004"), Decimal("-0.000000001"),
           Decimal("0.715135375979"), Decimal("0.7151353764")]
    g = class_partition(res, TAU)
    assert len(g) == 2 and sorted(len(x) for x in g) == [2, 3], g
    print(f"  6. partition: 1e-9 noise merged, gap 4e-10 kept inside one class: {sorted(len(x) for x in g)}")

    # 7. delivered-table cross-check: 554 beats / 446 ties, sides match sqscore
    per = load_poses()
    rows = [audit_row(n, per[n]) for n in sorted(per)]
    beats = sum(1 for r in rows if r["beat"])
    assert beats == SQ.DELIVERED_BEATS == 554, beats
    assert len(rows) - beats == 446, len(rows) - beats
    by_n = {r["n"]: r for r in rows}
    for n in (11, 18, 51, 90, 72):
        L = F(Decimal(by_n[n]["side"]))
        ref = F(Decimal(repr(SQ.extent(per[n]))))
        assert abs(L - ref) < F(1, 10 ** 8), (n, L, ref)
    print(f"  7. delivered table: {beats} beats / {446} ties; sides agree with "
          f"sqscore to 1e-8 on 5 rows")

    # 8. the audit itself is float-free
    import exact_field as EF
    checked, offenders, skipped = EF.audit_module(sys.modules[__name__],
                                                  exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  8. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")
    print("selftest OK (8 controls)")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--audit" in sys.argv:
        import exact_field as EF
        c, o, s = EF.audit_module(sys.modules[__name__], exempt=EF.AUDIT_EXEMPT)
        print(f"tilt_audit: {c} decision functions, {len(o)} offenders {o}")
        sys.exit(0 if not o else 1)
    sys.exit(main())
