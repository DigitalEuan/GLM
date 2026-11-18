#!/usr/bin/env python3
r"""optima.py — the delivered table against PROVED optimal sides.

Motivation (run 56): a general lower bound with a large numerical gap is not
evidence of unclaimed space.  At n = 10 Karakus gives 3.192582 while Stromquist
PROVED s(10) = 3 + 1/sqrt2 = 3.707106781186..., so the 0.5145 "gap" was bound
looseness and the delivered row sits exactly at the optimum.  This script applies
the same test to every row whose exact optimum is published, so that

  * "at"    the delivered row is the proved optimum (a control, not a result);
  * "above" is a REAL target: a proved smaller side exists;
  * "below" is impossible and would indict the table, not the bound.

Proved values used (all exactly representable, so the comparison is exact):

  s(1)=1, s(2)=s(3)=s(4)=2, s(5)=2+sqrt2/2, s(6..9)=3, s(10)=3+sqrt2/2
      Stromquist, "Packing 10 or 11 Unit Squares in a Square", Electron. J.
      Combin. 10 (2003) #R8, doi:10.37236/1701 (Theorem 1; the paper's opening
      paragraph states the smaller values).
  s(n)=sqrt(n) for square n; s(14)=s(15)=4, s(24)=5, s(35)=6
      Friedman, "Packing Unit Squares in Squares: A Survey and New Results",
      Electron. J. Combin. DS7 (2005), Section 1.

No other value is asserted here: for every other n the best known side is a
float from a catalogue, and a float is a nomination, not a certificate.
"""
from __future__ import annotations

import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ        # noqa: E402
import seam_wheels as SW    # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/optima.json")
TOL = 1e-6      # the stored rows carry finalize's ~2e-9 contact pad


def proved(n: int):
    """The proved exact s(n) as a Q2, or None.  See the module docstring."""
    r = Fraction(1, 2)
    table = {1: SW.Q2(Fraction(1)), 2: SW.Q2(Fraction(2)),
             3: SW.Q2(Fraction(2)), 4: SW.Q2(Fraction(2)),
             5: SW.Q2(Fraction(2)) + SW.R2H,
             6: SW.Q2(Fraction(3)), 7: SW.Q2(Fraction(3)),
             8: SW.Q2(Fraction(3)), 9: SW.Q2(Fraction(3)),
             10: SW.Q2(Fraction(3)) + SW.R2H,
             14: SW.Q2(Fraction(4)), 15: SW.Q2(Fraction(4)),
             24: SW.Q2(Fraction(5)), 35: SW.Q2(Fraction(6))}
    if n in table:
        return table[n]
    k = round(n ** 0.5)
    if k * k == n and k <= 31:
        return SW.Q2(Fraction(k))
    return None


def main() -> int:
    per = SQ.load()
    rows, at, above, below = [], [], [], []
    for n in sorted(per):
        s = proved(n)
        if s is None:
            continue
        L = SQ.extent(per[n])
        d = L - float(s)
        rec = {"n": n, "L_del": L, "s_proved": s.pretty(),
               "s_proved_float": float(s), "delta": d}
        if d > TOL:
            rec["status"] = "above"
            above.append(rec)
            rec["dscore_gain"] = (SQ.row_gain(n, float(s))
                                  - SQ.row_gain(n, L))
        elif d < -TOL:
            rec["status"] = "below"
            below.append(rec)
        else:
            rec["status"] = "at"
            at.append(rec)
        rows.append(rec)
    print(f"proved rows checked: {len(rows)}   at={len(at)} above={len(above)} "
          f"below={len(below)}")
    if above:
        print("\nrows with PROVED room (real targets):")
        tot = 0.0
        for r in above:
            print(f"  n={r['n']:4d} delivered {r['L_del']:.9f} > s(n) "
                  f"{r['s_proved_float']:.9f} = {r['s_proved']}   "
                  f"+{r['delta']:.3e}  worth {r['dscore_gain']:+.6f}")
            tot += r["dscore_gain"]
        print(f"  total banked by hitting every proved side: {tot:+.6f}")
    else:
        print("\nno proved row has room: the table sits at every published "
              "exact optimum")
    if below:
        print("\nIMPOSSIBLE rows (table below a proved optimum — a defect):")
        for r in below:
            print(f"  n={r['n']} delivered {r['L_del']:.9f} < {r['s_proved']}")
    # the n=10 control, spelled out
    c = next((r for r in rows if r["n"] == 10), None)
    if c:
        print(f"\nn=10 control: delivered {c['L_del']:.12f}, proved "
              f"{c['s_proved']} = {c['s_proved_float']:.12f}, "
              f"delta {c['delta']:+.2e} -> {c['status']}")
        print(f"  Karakus floor {SW.bound_karakus(10):.9f}; the "
              f"{SW.bound_karakus(10) - float(c['s_proved_float']):+.6f} gap is "
              "BOUND LOOSENESS, not packing space")
    led = {"run": 56, "schema": "optima/1", "tol": TOL, "rows": rows,
           "counts": {"at": len(at), "above": len(above), "below": len(below)}}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"\nledger: {OUT}")
    return 1 if below else 0


if __name__ == "__main__":
    raise SystemExit(main())
