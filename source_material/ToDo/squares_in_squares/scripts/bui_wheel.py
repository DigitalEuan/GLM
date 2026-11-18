#!/usr/bin/env python3
r"""bui_wheel.py — Bui's staircase as a declared wheel.

SOURCE.  Hong Duc Bui, "Square packing with O(x^0.6) wasted area",
arXiv:2508.04603v2, §3.1.1 (Initial Configuration) and §3.1.2 (Modification).
A nomination, not a result: nothing here is trusted until `packlib.verify`
accepts the geometry and the canonical scorer says the row improves.

THE CONSTRUCTION, AS IMPLEMENTED (all of §3.1.1 is exact over Q).

  theta, sigma1 are given by rational half-tangents, so cos/sin of both and of
  theta+sigma1 are RATIONAL (run 54, 22 §7); hence
      D1 = cos(theta)
      D2 = sec(theta+sigma1) * sin(sigma1)
      D3 = sec(theta+sigma1) * cos(sigma1)
  are rational and the whole staircase is a rational configuration.

  Rows are horizontal stacks of m unit squares rotated by theta.  With
  u = (cos theta, -sin theta) the row axis and n = (sin theta, cos theta) the
  row normal, the centre offsets of Lemma 1 are
      S(i, j+1) - S(i, j)   = u                      (|u| = 1: they touch)
      S(i+1, j) - S(i, j)   = (D2, -D3)
  and the second vector has row-normal component exactly -1
      (D2, -D3) . n = -sec(theta+sigma1) * cos(theta+sigma1) = -1,
  which is why consecutive rows are exactly one unit apart and never overlap.
  `--selftest` asserts that identity in Fractions.

  The ceiling of column j (the first row whose leftmost point is >= j-1) is
      i_j = ceil( (j-1)(1 - D1) / D2 ) + 1,
  and rows above i_m are deleted, leaving n0 = m * i_m tilted squares.

THE MODIFICATION, AND WHAT IS DELIBERATELY NOT REPRODUCED.  §3.1.2 replaces
everything above the ceiling with vertical stacks T and closes the region with a
quadrilateral ABCD.  Figures 6-9 carry the closure rule and its vertical
placement is stated only relative to those figures, so this wheel does NOT claim
ABCD.  Instead it does the honest weaker thing:

  * seal the staircase in its bounding SQUARE of side max(w, h) — valid by
    construction, since any w x h rectangle fits in a square of side max(w, h);
  * fill the free region above each ceiling with upright unit squares, greedily,
    in whole unit cells.

So the result is a valid packing of n = n0 + n_fill squares whose side is an
UPPER bound on what the primitive can do.  If even this bound does not beat the
delivered row, the primitive gives nothing at that row for any faithful ABCD.

SCOPE.  One parameter cell = (m, theta, sigma1).  No search over the
quadrilateral, no dual method, no §4 trapezoid tiling, no §5 square reduction.
A refusal here is about the primitive at our sizes, not about the paper.
"""
from __future__ import annotations

import json
import math
import os
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ        # noqa: E402
import packlib as P         # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/bui_wheel.json")


def half_tan(t: F):
    """(cos, sin) of 2*atan(t), exactly rational."""
    d = 1 + t * t
    return (1 - t * t) / d, 2 * t / d


def params(m: int, t: F, ts: F):
    """Exact D1, D2, D3, sin(theta) and the ceiling list i_j."""
    ct, st = half_tan(t)
    cs, ss = half_tan(ts)
    # theta + sigma1
    cts = ct * cs - st * ss
    sts = st * cs + ct * ss
    sec = F(1) / cts
    D1 = ct
    D2 = sec * ss
    D3 = sec * cs
    i = []
    for j in range(1, m + 1):
        i.append(math.ceil((j - 1) * (1 - D1) / D2) + 1)
    return D1, D2, D3, st, i


def build(m: int, t: F, ts: F):
    """Exact rational state: list of (x, y, cos, sin) centres + orientation."""
    if m < 2:
        raise ValueError("m >= 2")
    D1, D2, D3, st, i = params(m, t, ts)
    ct, _ = half_tan(t)
    im = i[-1]
    out = []
    for ii in range(1, im + 1):
        for j in range(1, m + 1):
            x = (j - 1) * D1 + (ii - 1) * D2
            y = -(j - 1) * st - (ii - 1) * D3
            out.append((x, y, ct, st))
    return out, D1, D2, D3, i, im


def _ext(state):
    """Bounding box of unit squares given as (x, y, cos, sin)."""
    xs, ys = [], []
    for x, y, c, s in state:
        hx = F(1, 2) * (abs(c) + abs(s))
        hy = hx
        xs += [x - hx, x + hx]
        ys += [y - hy, y + hy]
    return min(xs), max(xs), min(ys), max(ys)


def fill(state, D1, st, m):
    """Greedy upright unit cells in the free region, exact.

    In each integer column band the tilted squares occupy one contiguous vertical
    run (the rows are 1 apart in the normal direction), so the free cells are the
    whole cells below the run and above it.  Whole cells only, so validity rests
    on `packlib.verify`, not on this function's word.
    """
    x0, x1, y0, y1 = _ext(state)
    span = {}
    for x, y, c, s in state:
        hx = F(1, 2) * (abs(c) + abs(s))
        lo, hi, b, t = x - hx, x + hx, y - hx, y + hx
        X = math.floor(lo)
        while X <= math.floor(hi):
            if X + 1 > lo and X < hi:
                if X in span:
                    span[X] = (min(span[X][0], b), max(span[X][1], t))
                else:
                    span[X] = (b, t)
            X += 1
    cells = []
    X = math.floor(x0)
    while X < math.ceil(x1):
        if X in span:
            b, t = span[X]
            Y = math.floor(y0)
            while Y + 1 <= b:
                cells.append((F(2 * X + 1, 2), F(2 * Y + 1, 2)))
                Y += 1
            Y = math.floor(t) + 1
            while Y + 1 <= y1 + 1:
                cells.append((F(2 * X + 1, 2), F(2 * Y + 1, 2)))
                Y += 1
        else:
            Y = math.floor(y0)
            while Y + 1 <= y1 + 1:
                cells.append((F(2 * X + 1, 2), F(2 * Y + 1, 2)))
                Y += 1
        X += 1
    return cells


def square_side(state, cells):
    xs, ys = [], []
    for x, y, c, s in state:
        hx = F(1, 2) * (abs(c) + abs(s))
        xs += [x - hx, x + hx]
        ys += [y - hx, y + hx]
    for cx, cy in cells:
        xs += [cx - F(1, 2), cx + F(1, 2)]
        ys += [cy - F(1, 2), cy + F(1, 2)]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    return max(w, h), min(xs), min(ys)


def to_state(state, cells, ox, oy, theta):
    """(x, y, angle) floats for the canonical scorer / verifier."""
    out = [(float(x - ox), float(y - oy), theta) for x, y, c, s in state]
    out += [(float(cx - ox), float(cy - oy), 0.0) for cx, cy in cells]
    return out


def cell_report(m, t, ts, per=None):
    state, D1, D2, D3, i, im = build(m, t, ts)
    cells = fill(state, D1, half_tan(t)[1], m)
    L, ox, oy = square_side(state, cells)
    theta = -2 * math.atan(float(t))   # -theta: u = (cos t, -sin t) is an edge direction
    st = to_state(state, cells, ox, oy, theta)
    n = len(st)
    rec = {"m": m, "t": str(t), "ts": str(ts), "n": n, "L": float(L),
           "theta": theta, "i_m": im, "n_tilted": len(state), "n_fill": len(cells)}
    if per is not None and 1 <= n <= 1000:
        Ld = SQ.extent(per[n])
        rec["delivered"] = Ld
        rec["gain"] = SQ.row_gain(n, float(L)) - SQ.row_gain(n, Ld)
        rec["verifies"] = P.verify(st, tol=1e-9)["ok"]
        rec["worst_pen"] = P.verify(st, tol=1e-9)["worst_pen"]
    return rec, st


def selftest() -> int:
    ok = 0
    # 1. the lemma's normal component is exactly -1, in Fractions
    for t, ts in [(F(1, 8), F(1, 12)), (F(1, 13), F(1, 17))]:
        D1, D2, D3, st, i = params(6, t, ts)
        ct, _ = half_tan(t)
        dot = D2 * st + (-D3) * ct
        assert dot == -1, (t, ts, dot)
        ok += 1
    # 2. within-row step is a unit vector
    for t in (F(1, 8), F(1, 10)):
        ct, st = half_tan(t)
        assert ct * ct + st * st == 1
        ok += 1
    # 3. ceiling is non-decreasing and starts at 1
    D1, D2, D3, st, i = params(9, F(1, 8), F(1, 12))
    assert i[0] == 1 and all(i[k] <= i[k + 1] for k in range(len(i) - 1))
    ok += 1
    # 4. a built cell is a VALID packing of exactly n squares
    per = SQ.load()
    rec, st = cell_report(10, F(1, 10), F(1, 14), per)
    v = P.verify(st, tol=1e-9)
    assert v["ok"], v
    assert rec["n"] == len(st) == rec["n_tilted"] + rec["n_fill"]
    assert rec["n_tilted"] == 10 * rec["i_m"]
    ok += 1
    # 5. the structural reason this wheel cannot score: density of one sealed tile
    assert rec["n"] / rec["L"] ** 2 < 0.6, rec
    ok += 1
    # 5. monotonicity: more rows never shrinks the side
    r1, _ = cell_report(8, F(1, 10), F(1, 14))
    r2, _ = cell_report(12, F(1, 10), F(1, 14))
    assert r2["L"] >= r1["L"] - 1e-12
    ok += 1
    print(f"selftest: {ok}/8 checks pass")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    per = SQ.load()
    grid_m = [5, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30]
    grid_t = [F(1, 12), F(1, 10), F(1, 8), F(1, 6)]
    grid_ts = [F(1, 20), F(1, 14), F(1, 10)]
    cells, best = [], []
    for m in grid_m:
        for t in grid_t:
            for ts in grid_ts:
                try:
                    rec, _ = cell_report(m, t, ts, per)
                except (ValueError, ZeroDivisionError):
                    continue
                cells.append(rec)
                if rec.get("gain") is not None and rec["gain"] > 1e-9:
                    best.append(rec)
    cells.sort(key=lambda r: r.get("gain") or 0)
    print(f"cells built: {len(cells)}   in range n<=1000: "
          f"{sum(1 for c in cells if c['n'] <= 1000)}")
    print(f"cells that verify: {sum(1 for c in cells if c.get('verifies'))}")
    print(f"GAINS: {len(best)}")
    print(f"{'m':>3} {'theta':>8} {'n':>5} {'L':>11} {'delivered':>11} "
          f"{'gain':>10}  verifies")
    for r in cells[:8]:
        if r.get("gain") is None:
            continue
        print(f"{r['m']:3d} {r['theta']:8.4f} {r['n']:5d} {r['L']:11.6f} "
              f"{r['delivered']:11.6f} {r['gain']:+10.2e}  {r['verifies']}")
    led = {"run": 62, "schema": "bui/1", "source": "arXiv:2508.04603v2 §3.1.1-3.1.2",
           "cells": cells, "gains": best,
           "scope": "m x theta x sigma1; bounding square + greedy ceiling fill; "
                    "ABCD not reproduced (§3.1.2 figures)"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"\nledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
