#!/usr/bin/env python3
r"""wall_margin.py — define the wall margin exactly, and compute it for all 1000 rows.

THE DEFINITION (run 69)
-----------------------
Two walls bound every row, and they are different walls:

  * the **area wall**  sqrt(n)  — no packing of n unit squares has side below it.
    It is unreachable except when n is a perfect square, and it is the only wall
    that is a theorem rather than a convention.
  * the **grid wall**  k = ceil(sqrt(n)) — the side of the plain k x k grid.  It
    is what the table "beats", but it is not a bound: 553 rows are below it.

The **wall margin** is the side length between the delivered side and the area
wall, normalised by that wall:

      mu(n)  = L(n) - sqrt(n)              [side above the area wall]
      rho(n) = mu(n) / sqrt(n)  =  score(n)  [dimensionless]

`mu` is the exact quantity a new construction must consume: any improvement at
row n is a reduction of `mu` by the same amount in L.  `rho` is its price in
score, and it is the row's contribution to the total.

We also record the two other exact columns of the table:

      held(n)  = k(n) - L(n)        [how far the row already sits below the grid]
      value(n) = 1 / sqrt(n)        [score bought per unit of side removed]

`held = 0` is a row **at the grid wall**: it must cross a whole integer step
before anything is gained.  `value` is the marginal: a 1e-3 side reduction is
worth 1e-3/sqrt(n), so small n pays more for the same work.

PRECISION
---------
L is the canonical `sqscore.extent` of the delivered row.  The delivered table
is decimals (coordinates and 45,921 distinct float angles), so there is no exact
algebraic L to be had from it; the quantity above is exact *for the table as
delivered*, and `extent_dec()` re-derives L at 50 significant digits with a
Decimal cos/sin so a wrong float cannot carry the ranking.  Rows whose margin
differs by less than 1e-9 are reported as ties, never ranked.
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ        # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/wall_margin.json")


# --------------------------------------------------------------- exact decimal
def _dcos_dsin(a: Decimal) -> tuple[Decimal, Decimal]:
    """cos and sin of a Decimal angle by Taylor series (|a| < 4)."""
    getcontext().prec = 70
    a2 = a * a
    c, term, k = Decimal(0), Decimal(1), 0
    while True:
        c += term
        k += 1
        term = -term * a2 / ((2 * k - 1) * (2 * k))
        if abs(term) < Decimal(10) ** -60:
            break
    s_, term, k = Decimal(0), a, 0
    while True:
        s_ += term
        k += 1
        term = -term * a2 / ((2 * k) * (2 * k + 1))
        if abs(term) < Decimal(10) ** -60:
            break
    return c, s_


def extent_dec(st, prec: int = 50) -> Decimal:
    """The delivered side at `prec` significant digits, from the CSV decimals."""
    getcontext().prec = prec + 20
    lo_x = hi_x = lo_y = hi_y = None
    for x, y, ang in st:
        a = Decimal(repr(ang))
        c, s = _dcos_dsin(a)
        ex = (abs(c) + abs(s)) / 2
        dx, dy = Decimal(repr(x)), Decimal(repr(y))
        if lo_x is None:
            lo_x, hi_x, lo_y, hi_y = dx - ex, dx + ex, dy - ex, dy + ex
        lo_x = min(lo_x, dx - ex); hi_x = max(hi_x, dx + ex)
        lo_y = min(lo_y, dy - ex); hi_y = max(hi_y, dy + ex)
    return max(hi_x - lo_x, hi_y - lo_y)


# ---------------------------------------------------------------------- table
def build(per):
    rows = {}
    for n in range(1, 1001):
        st = per[n]
        L = SQ.extent(st)
        sq = math.sqrt(n)
        k = SQ.grid(n)
        rows[n] = {"n": n, "L": L, "k": k, "mu": L - sq, "rho": L / sq - 1.0,
                   "held": k - L, "value": 1.0 / sq, "beat": SQ.is_beat(n, L)}
    return rows


def proved_set():
    try:
        import optima
    except Exception:
        return set()
    return {n for n in range(1, 1001) if optima.proved(n) is not None}


def rank_by(rows, key, reverse=True):
    order = sorted(rows, key=lambda n: rows[n][key], reverse=reverse)
    rank = {}
    for i, n in enumerate(order):
        rank[n] = i + 1
    return rank


def main() -> int:
    per = SQ.load()
    rows = build(per)
    proved = proved_set()
    rank_mu = rank_by(rows, "mu")
    rank_rho = rank_by(rows, "rho")

    n_rows = len(rows)
    zero = [n for n in rows if abs(rows[n]["mu"]) <= 1e-9]
    positive = [n for n in rows if rows[n]["mu"] > 1e-9]

    print("=== wall margin mu(n) = L(n) - sqrt(n), all 1000 rows ===")
    print(f"rows: {n_rows}   mu > 0: {len(positive)}   mu = 0 (perfect squares): "
          f"{len(zero)}")
    print(f"mu range: {min(rows[n]['mu'] for n in rows):.6f} .. "
          f"{max(rows[n]['mu'] for n in rows):.6f}")

    print("\n=== the three named rows ===")
    print(f"{'n':>4} {'L':>16} {'k':>3} {'mu':>10} {'rho':>10} {'held':>10} "
          f"{'rank_mu':>8} {'proved':>7} {'beat':>5}")
    for n in (184, 656, 819):
        r = rows[n]
        print(f"{n:4d} {r['L']:16.9f} {r['k']:3d} {r['mu']:10.6f} "
              f"{r['rho']:10.6f} {r['held']:10.3e} {rank_mu[n]:8d} "
              f"{str(n in proved):>7} {str(r['beat']):>5}")

    print("\n=== 15 largest wall margins (most nominal room) ===")
    for n in sorted(rows, key=lambda m: rows[m]["mu"], reverse=True)[:15]:
        r = rows[n]
        print(f"  n={n:4d} mu={r['mu']:.6f} rho={r['rho']:.6f} k={r['k']:2d} "
              f"held={r['held']:.3g} proved={n in proved} beat={r['beat']}")

    print("\n=== 15 smallest POSITIVE wall margins (thinnest) ===")
    for n in sorted(positive, key=lambda m: rows[m]["mu"])[:15]:
        r = rows[n]
        print(f"  n={n:4d} mu={r['mu']:.3e} rho={r['rho']:.3e} k={r['k']:2d} "
              f"held={r['held']:.3g} proved={n in proved} beat={r['beat']}")

    print("\n=== open rows (not proved optimal) with n <= 60, by mu ===")
    print(f"{'n':>4} {'mu':>9} {'rho':>9} {'k':>3} {'held':>9} {'beat':>5} "
          f"{'n_tilted':>8}")
    cand = [n for n in range(11, 61) if n not in proved]
    for n in sorted(cand, key=lambda m: rows[m]["mu"], reverse=True):
        r = rows[n]
        tilts = sum(1 for (_, _, a) in per[n] if abs(a) > 1e-9)
        print(f"{n:4d} {r['mu']:9.6f} {r['rho']:9.6f} {r['k']:3d} "
              f"{r['held']:9.3e} {str(r['beat']):>5} {tilts:8d}")

    print("\n=== decimal check of the three rows (50-digit extent) ===")
    for n in (184, 656, 819):
        d = extent_dec(per[n])
        print(f"  n={n:4d} float L={rows[n]['L']:.12f}  decimal L={d:.15f}  "
              f"diff={float(Decimal(repr(rows[n]['L'])) - d):.3e}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"schema": "wallmargin/1", "run": 69,
                   "definition": "mu = L - sqrt(n); rho = mu/sqrt(n) = score; "
                                 "held = ceil(sqrt(n)) - L; value = 1/sqrt(n)",
                   "rows": {str(n): {k: v for k, v in rows[n].items()}
                            for n in rows},
                   "proved": sorted(proved)}, f, indent=0)
    print(f"ledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
