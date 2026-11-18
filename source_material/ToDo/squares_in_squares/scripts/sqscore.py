#!/usr/bin/env python3
r"""sqscore.py — the ONE scorer. Every instrument imports this.

Two mistakes in the instruments made this file necessary (see
`10-LEECH-ADDRESS.md` §12 and `11-AREA-CEILING.md` §0):

  * scoring a row as `10/L`, where the repository scores `L/sqrt(n) - 1`;
  * computing the container side as `max(x) + max(ex) - (min(x) - min(ex))`,
    which inflates the box and mislabelled 253 of 553 beating rows as grid.

Both were silent. This module makes them loud: `guard()` recomputes the delivered
table from `workspace/submission/submission.csv` and **asserts** the result is
exactly the recorded 22.218056945 with 553 beats. Any script that imports this
file and calls `guard()` cannot print a score on a wrong scale or against a
mis-classified target — it raises instead.

Definitions (all exact where they can be):

    extent(state)  = max over axes of  (max_i(x_i + ex_i) - min_i(x_i - ex_i)),
                     ex_i = (|cos θ_i| + |sin θ_i|) / 2       [per square]
    grid(n)        = ceil(sqrt(n)),  exact via isqrt
    row_score(n,L) = L / sqrt(n) - 1                          lower is better
    row_gain(n,L)  = (grid(n) - L) / sqrt(n)                  positive = beats grid
    total          = sum over rows of row_score

The floor of `total` is 0 (L >= sqrt(n) by area) and the delivered table is
22.218056945 over n = 1..1000 with 553 rows beating grid.
"""
from __future__ import annotations

import csv
import math
import os
from decimal import Decimal, getcontext

getcontext().prec = 30

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")

#: delivered table, recomputed to 1.3e-10 by `leech_audit_fix.py`
DELIVERED_SCORE = Decimal("22.218056945")
DELIVERED_BEATS = 553
DELIVERED_ROWS = 1000
TOL = Decimal("1e-6")


# ---------------------------------------------------------------- geometry
def extent(state) -> float:
    """Correct container side. `state` is any sequence of (x, y, theta)."""
    import numpy as np
    a = np.asarray(state, dtype=float)
    ex = 0.5 * (np.abs(np.cos(a[:, 2])) + np.abs(np.sin(a[:, 2])))
    return max(float((a[:, 0] + ex).max() - (a[:, 0] - ex).min()),
               float((a[:, 1] + ex).max() - (a[:, 1] - ex).min()))


def grid(n: int) -> int:
    """ceil(sqrt(n)) exactly."""
    k = math.isqrt(n)
    return k if k * k == n else k + 1


def is_beat(n: int, L: float, tol: float = 1e-12) -> bool:
    return L < grid(n) - tol


def row_score(n: int, L: float) -> float:
    return 10.0 * 0 + (L / math.sqrt(n) - 1.0)


def row_gain(n: int, L: float) -> float:
    """Gain over grid at this row. Positive iff it beats."""
    return (grid(n) - L) / math.sqrt(n)


def gain_ceiling(n: int) -> float:
    """Largest possible gain at a row: zero-waste packing (never attained)."""
    return grid(n) / math.sqrt(n) - 1.0


def slack(n: int, L: float) -> float:
    return L - math.isqrt(n)


def marginal(n: int) -> float:
    """d(row_score)/dL, negated: the value of tightening L by one unit."""
    return 1.0 / math.sqrt(n)


# ---------------------------------------------------------------- tables
def load(path: str | None = None) -> dict:
    """n -> list of (x, y, angle) from a submission CSV."""
    per: dict = {}
    with open(path or SUBMISSION) as f:
        rd = csv.reader(f)
        hdr = next(rd)
        ix = {h: i for i, h in enumerate(hdr)}
        for r in rd:
            per.setdefault(int(r[ix["n"]]), []).append(
                (float(r[ix["x"]]), float(r[ix["y"]]), float(r[ix["angle"]])))
    return per


def summarise(per: dict) -> dict:
    """score, beats, rows for a per-n state map (fresh float L, exact counting)."""
    tot = Decimal(0)
    beats = 0
    for n in sorted(per):
        L = extent(per[n])
        tot += Decimal(repr(L)) / Decimal(n).sqrt() - Decimal(1)
        if is_beat(n, L):
            beats += 1
    return {"score": tot, "beats": beats, "rows": len(per),
            "grid": len(per) - beats}


def guard(per: dict | None = None, quiet: bool = False) -> dict:
    """Assert the delivered table scores 22.218056945 with 553 beats.

    Raises AssertionError (never returns a wrong number) if it does not.
    """
    if per is None:
        per = load()
    s = summarise(per)
    if abs(s["score"] - DELIVERED_SCORE) > TOL or s["beats"] != DELIVERED_BEATS:
        raise AssertionError(
            "SCORER GUARD FAILED: submission.csv gives score "
            f"{s['score']:.9f} with {s['beats']} beats over {s['rows']} rows; "
            f"the delivered table is {DELIVERED_SCORE} with {DELIVERED_BEATS}. "
            "Do not trust any number this script prints.")
    if s["rows"] != DELIVERED_ROWS:
        raise AssertionError(
            f"SCORER GUARD FAILED: {s['rows']} rows, expected {DELIVERED_ROWS}")
    if not quiet:
        print(f"[sqscore] guard OK: score {s['score']:.9f}, beats {s['beats']}, "
              f"grid {s['grid']}")
    return s


if __name__ == "__main__":
    r = guard()
    print(f"[sqscore] rows {r['rows']}, grid rows {r['grid']}")
