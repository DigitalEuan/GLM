#!/usr/bin/env python3
r"""crosswalk.py — open rows against the published record.

The question (run 57 review): for each UNPROVED row, does the table already
reach the best published construction, or is there something to import?  A row
where a published construction is strictly smaller than the delivered side is a
real target; a row where the table already matches or beats it has nothing to
import, whatever the lower bound leaves open.

Sources, all cited per row:
  Friedman, "Packing Unit Squares in Squares: A Survey and New Results",
  Electron. J. Combin. DS7 (2009), Table 1 (best known upper bounds, with author
  and figure) and Table 2 (best known non-trivial lower bounds, with author).
  Stromquist, EJC 10 (2003) #R8, Theorem 2, for s(11) >= 2 + 4/sqrt5.

Table 1 gives exact closed forms for several rows; where the form lies in
Q(sqrt2) the comparison is exact, otherwise (sqrt5, sqrt7, sqrt10) it is a float
comparison at the printed precision and is labelled as such.

A large gap between the published best and the published lower bound is NOT room:
run 56 showed a general bound missing the true optimum at n = 10 by 0.5145.  The
gap column is a screening quantity only.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ        # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/crosswalk.json")

R2, R5, R7, R10 = (math.sqrt(2), math.sqrt(5), math.sqrt(7), math.sqrt(10))

# n: (formula string, value, exact-in-Q(sqrt2)?, author, figure)
PUB = {
    11: ("3.8771 (4 dp)", 3.8770836, False, "Trump 1979", "Fig 6"),
    12: ("4", 4.0, True, "grid (Table 1: 4 for 12-13)", "-"),
    17: ("4.6756 (4 dp)", 4.6756, False, "Bidwell 1998 (3 angles)", "Fig 12"),
    18: ("7/2 + sqrt7/2", 3.5 + R7 / 2, False, "Hamalainen 1980", "Fig 7"),
    19: ("3 + 4*sqrt2/3", 3 + 4 * R2 / 3, True, "Wainwright 1979", "Fig 4"),
    20: ("5", 5.0, True, "grid", "-"),
    26: ("7/2 + 3*sqrt2/2", 3.5 + 1.5 * R2, True, "Friedman 2009", "Fig 9"),
    27: ("5 + 1/sqrt2", 5 + 1 / R2, True, "Gobel 1979", "Fig 1"),
    28: ("3 + 2*sqrt2", 3 + 2 * R2, True, "Gobel 1979", "Fig 3"),
    29: ("5.9344 (4 dp)", 5.9344, False, "Gensane/Ryckelynck 2004 (6 angles)", "Fig 12"),
    30: ("6", 6.0, True, "grid", "-"),
    31: ("6", 6.0, True, "grid", "-"),
}
LB = {
    11: ("2 + 4/sqrt5", 2 + 4 / R5, "Stromquist 2003 Thm 2"),
    12: ("2 + 4/sqrt5", 2 + 4 / R5, "Stromquist 2003"),
    17: ("(40*sqrt2 + 19)/17", (40 * R2 + 19) / 17, "Green 2000"),
    18: ("(40*sqrt2 + 19)/17", (40 * R2 + 19) / 17, "Green 2000"),
    19: ("6*sqrt2 - 4", 6 * R2 - 4, "Friedman 2009"),
    20: ("6*sqrt2 - 4", 6 * R2 - 4, "Friedman 2009"),
    26: ("2*sqrt2 + (27+2*sqrt10)/13", 2 * R2 + (27 + 2 * R10) / 13, "Green 2000"),
    27: ("2*sqrt2 + (27+2*sqrt10)/13", 2 * R2 + (27 + 2 * R10) / 13, "Green 2000"),
    28: ("2*sqrt2 + 6/sqrt5", 2 * R2 + 6 / R5, "Green 2000"),
    29: ("2*sqrt2 + 6/sqrt5", 2 * R2 + 6 / R5, "Green 2000"),
    30: ("2*sqrt2 + 6/sqrt5", 2 * R2 + 6 / R5, "Green 2000"),
    31: ("5.6415 (4 dp)", 5.6415, "Green 2000"),
}


def row(per, n):
    L = SQ.extent(per[n])
    k = math.isqrt(n)
    form, pub, exact, who, fig = PUB[n]
    lform, lb, lwho = LB[n]
    tol = 1e-6 if exact else 1e-4
    d = L - pub
    if d < -tol:
        status = "beats_published"
    elif d <= tol:
        status = "at_published"
    else:
        status = "above_published"       # a real import target
    # forward-only value of a base exactly at the PUBLISHED side, over the
    # column's suffix (declared (r, delta) invariant, labelled as such)
    delta = pub - k
    r = n - k * k
    fwd, rows = 0.0, 0
    for kk in range(k, 32):
        nn = kk * kk + r
        if nn > 1000 or nn not in per or nn - math.isqrt(nn) ** 2 != r:
            continue
        Lk = SQ.extent(per[nn])
        if kk > k:
            fwd += max(0.0, (Lk - (kk + delta)) / math.sqrt(nn))
            rows += 1
    return {"n": n, "k": k, "r": r, "delivered": L,
            "published": pub, "published_form": form, "published_by": who,
            "figure": fig, "published_exact_in_Q2": exact,
            "delta_to_published": d, "status": status,
            "lower_bound": lb, "lower_bound_form": lform, "lower_bound_by": lwho,
            "unresolved": pub - lb,
            "fwd_value_if_at_published": fwd, "fwd_rows": rows}


def main() -> int:
    per = SQ.load()
    rows = [row(per, n) for n in sorted(PUB)]
    print(f"{'n':>3} {'r':>2} {'delivered':>12} {'published':>12} {'d(L-pub)':>10} "
          f"{'status':>16} {'gap pub-LB':>10} {'fwd':>9}")
    for r in rows:
        print(f"{r['n']:3d} {r['r']:2d} {r['delivered']:12.9f} {r['published']:12.9f} "
              f"{r['delta_to_published']:+10.2e} {r['status']:>16} "
              f"{r['unresolved']:10.6f} {r['fwd_value_if_at_published']:9.6f}")
    tally = {}
    for r in rows:
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    print("\nstatus tally:", tally)
    above = [r for r in rows if r["status"] == "above_published"]
    if above:
        print("\nIMPORT TARGETS (published construction strictly better than the "
              "delivered row):")
        for r in above:
            print(f"  n={r['n']} delivered {r['delivered']:.9f} vs published "
                  f"{r['published_form']} = {r['published']:.9f} "
                  f"({r['published_by']}); fwd value {r['fwd_value_if_at_published']:+.6f}")
    else:
        print("\nno import target: on every open row listed here the table already "
              "matches or beats the best published construction")
    # the n = 11 focused check
    r11 = next(r for r in rows if r["n"] == 11)
    raw = [tuple(map(float, s)) for s in per[11]]
    ang = sorted({t for _, _, t in raw if abs(t % (math.pi / 2)) > 1e-9})
    degs = [round(math.degrees(t), 4) for t in ang]
    print(f"\nn=11 focused check: delivered {r11['delivered']:.9f} vs Trump "
          f"{r11['published']:.7f} -> {r11['status']}")
    print(f"  tilt angles {degs} deg; Trump's middle squares are 'about 40.182 deg', "
          f"and a square's orientation is mod 90: "
          f"{[round(90 - d, 4) for d in degs]} deg equivalent")
    print(f"  proved lower bound {r11['lower_bound_form']} = {r11['lower_bound']:.9f} "
          f"(Stromquist Thm 2); unresolved {r11['unresolved']:.6f} in side")
    led = {"run": 57, "schema": "crosswalk/1", "rows": rows, "tally": tally,
           "n11": {"delivered": r11["delivered"], "published": r11["published"],
                   "angles_deg": degs, "lower_bound": r11["lower_bound"]}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"\nledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
