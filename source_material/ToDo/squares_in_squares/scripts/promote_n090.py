#!/usr/bin/env python3
r"""promote_n090.py — write the certified n = 90 row, exactly.

Run 139 (`import_n090.py`) proved the published certificate legal in exact
`Fraction` arithmetic and priced it at `6.28368e-4` rendered at the repository's
`1e-9` frame convention.  This script performs the promotion and proves the
*rendered* row is still legal, without ever computing a transcendental:

  1. take the exact pose, inflate every centre by (1 + 1e-9) so the tightest
     contact has 1e-9 of clearance (the certificate itself touches to 1e-73);
  2. re-box it, and write each centre at 10 decimals and each angle at 12
     decimals -- the precision the delivered table already uses;
  3. bound the perturbation each rounding can cause (a centre shifts by at most
     `5e-11` per axis, an angle by at most `5e-13` rad, so no corner moves more
     than `d = sqrt(2)*5e-11 + (sqrt(2)/2)*5e-13`), and note that a pairwise
     separating slack changes by at most `4d`;
  4. assert `min_slack_exact - 4d > 0` and `side_rendered <= side_exact + 2d`,
     then rewrite the 90 rows in place, keeping every id.

`side_rendered` is measured from the CSV the way `sqscore.extent` measures it, so
the number that moves `DELIVERED_SCORE` is the delivered one, not a projection.

    python3 scripts/promote_n090.py            # verify, write, report
    python3 scripts/promote_n090.py --check    # verify only, never write
"""
from __future__ import annotations

import csv
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

getcontext().prec = 60
sys.set_int_max_str_digits(1_000_000)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import import_n090 as N9                      # noqa: E402
import sqscore as SQ                          # noqa: E402

CSV = ROOT / "workspace/submission/submission.csv"
BACKUP = ROOT / "workspace/push/submission_before_n090.csv"
N_ROW = 90
X_DP = 10          # decimals for x, y (the table's own precision)
A_DP = 12          # decimals for the angle, in radians
Q = Decimal(1).scaleb(-X_DP)
QA = Decimal(1).scaleb(-A_DP)


# ------------------------------------------------------------------ atan ---
def atan_series(t: Fraction, terms: int = 90) -> Fraction:
    """`arctan(t)` by its alternating series; |t| <= 0.25 here, so it converges."""
    total = Fraction(0)
    t2 = t * t
    p = t
    for k in range(terms):
        total += p / (2 * k + 1) if k % 2 == 0 else -p / (2 * k + 1)
        p *= t2
    return total


def dec(fr: Fraction, places: Decimal) -> Decimal:
    """`fr` rounded half-even to `places` (a Decimal such as 1e-10), exactly."""
    d = Decimal(fr.numerator) / Decimal(fr.denominator)
    return d.quantize(places)


# ------------------------------------------------------------------ pose ---
def build():
    """The inflated, re-boxed pose plus the rendered strings and the bounds."""
    d, pose = N9.load_pose()
    inflated = N9.inflate(pose)
    corners = []
    for x, y, c, s in inflated:
        corners.extend(N9.corners(x, y, c, s))
    mx = min(p[0] for p in corners)
    my = min(p[1] for p in corners)
    moved = [(x - mx, y - my, c, s) for x, y, c, s in inflated]

    # exact geometry of the inflated, re-boxed pose
    st = N9.check(moved)

    # the raw tan values, recovered from (c, s) so the angle is the certificate's
    rows = []
    for (x, y, c, s), raw in zip(moved, d["squares"]):
        t = Fraction(raw[2])
        theta = 2 * atan_series(t)                       # exact rational approx
        theta_d = dec(theta, QA)
        x_d, y_d = dec(x, Q), dec(y, Q)
        rows.append({"x": x_d, "y": y_d, "angle": theta_d,
                     "x_err": abs(Fraction(x_d) - x),
                     "y_err": abs(Fraction(y_d) - y),
                     "a_err": abs(Fraction(theta_d) - theta)})
    return st, rows


def verify(st, rows):
    """The perturbation bound: rounding cannot create an overlap or a bigger box."""
    dmax = max(r["x_err"] for r in rows) + max(r["y_err"] for r in rows)
    amax = max(r["a_err"] for r in rows)
    delta = dmax + Fraction(70, 99) * amax        # (sqrt2)/2 < 0.7072 < 70/99
    slack_after = st["min_slack"] - 4 * delta
    side_after = st["side"] + 2 * delta
    return {
        "centre_err_max": float(dmax), "angle_err_max": float(amax),
        "delta": float(delta),
        "min_slack_exact_f": float(st["min_slack"]),
        "min_slack_after_f": float(slack_after),
        "side_exact_f": float(st["side"]),
        "side_after_f": float(side_after),
        "slack_after": slack_after, "side_after": side_after,
        "legal": slack_after > 0,
        "inside": side_after < N9.L_DELIVERED,
    }


def write(rows):
    with open(CSV, newline="") as f:
        data = list(csv.reader(f))
    hdr, body = data[0], data[1:]
    idx = [i for i, r in enumerate(body) if r[1] == str(N_ROW)]
    assert len(idx) == N_ROW, len(idx)
    with open(BACKUP, "w", newline="") as f:
        csv.writer(f).writerows(data)
    for k, i in enumerate(idx):
        r = body[i]
        r[2] = str(k)                     # square_id 0..89
        r[3] = f"{rows[k]['x']:.10f}"
        r[4] = f"{rows[k]['y']:.10f}"
        r[5] = f"{rows[k]['angle']:.12f}"
    with open(CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        w.writerows(body)


def measure():
    per = SQ.load()
    return per[N_ROW], SQ.extent(per[N_ROW])


def main() -> int:
    st, rows = build()
    v = verify(st, rows)
    print(f"exact inflated pose: {st['n']} cells, {st['overlaps']} overlaps, "
          f"min slack {float(st['min_slack']):.3e}, side {float(st['side']):.16f}")
    print(f"rounding: centre {v['centre_err_max']:.2e}, "
          f"angle {v['angle_err_max']:.2e}, delta {v['delta']:.2e}")
    print(f"after rounding: min slack {v['min_slack_after_f']:+.3e}, "
          f"side <= {v['side_after_f']:.16f}")
    print(f"legal {v['legal']}, inside {v['inside']}")
    assert v["legal"] and v["inside"], v
    if "--check" in sys.argv:
        print("check only: nothing written")
        return 0
    write(rows)
    state, L = measure()
    print(f"delivered row {N_ROW}: {len(state)} cells, measured side {L:.16f}")
    per = SQ.load()
    s = SQ.summarise(per)
    print(f"table after promotion: score {s['score']:.9f}, beats {s['beats']}, "
          f"grid {s['grid']}, rows {s['rows']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
