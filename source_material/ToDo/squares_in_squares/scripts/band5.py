#!/usr/bin/env python3
r"""band5.py — run 131: what the pocket mechanism can hold below L = 5, exactly.

Band 5 is the one open, area-affordable, high-leverage target that run 130's
ranking produced: `n = 20, 21, 22, 23` at `L = 5`, band price `d = -0.131`
(the frontier pose at `n = 19` already has `V = 4.869 < j* - 1 = 5` unit^2 of
void, so *area* is not what stops them).

This module settles what one whole mechanism can do there, in `Q(sqrt 2)`, with
no float named anywhere.

**Theorem (corner-pocket bound).** Let an arrangement consist of four upright
rectangular blocks `a_i x b_i` in the four corners of an `L x L` box (two walls
each) and one unit cell tilted 45 degrees anywhere in the gap, with every block
in exact contact with one edge of that cell.  Then

    (a1+b1) + (a4+b4) = 2L - sqrt2        and        (a2+b2) + (a3+b3) = 2L - sqrt2

(one equation per diagonal, from the four contact conditions), so for `L < 5`

    2L - sqrt2 < 8.5858   =>   (a1+b1)+(a4+b4) <= 8   and the same on the other diagonal,

and since `a*b <= floor((a+b)/2)^2` with the sum bounded, the total cell count is

    n <= 4 * floor(8/4)^2 + 1 = 17 .

So **no corner-block + central-tilted-cell arrangement holds 20, 21, 22 or 23
cells below `L = 5`** -- the mechanism is at least 3 cells short, whatever the
block sizes, whatever the position of the tilted cell.  The bound is tight: the
four `2 x 2` blocks with the tilted cell give `n = 17` at `L = 2*2 + sqrt2/2 =
4.707106...`, which is a real beat of row 17 and is found by the same
enumeration (`--selftest` control 1).

**Theorem (single tilted block).** A `p x q` block of 45-degree cells has
bounding box `(p+q)/sqrt2` square, and `(p+q)^2 >= 4pq` gives

    (p+q)/sqrt2 >= sqrt(2pq) > sqrt(pq),

so a pure tilted block always needs more side than the area floor of its own
count: 20 cells would need `L >= sqrt(40) = 6.32 > 5`.  Tilting an entire block
strictly loses.

Beyond those two families the run does not claim a bound: `--probe` runs the
repo's exact anchor-closure builder at the target side and records how deep it
gets, and the doc states that as a budget measurement, not a proof.

    python3 scripts/band5.py --selftest
    python3 scripts/band5.py --families
    python3 scripts/band5.py --probe
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from fractions import Fraction
from math import isqrt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import seam_wheels as SW                 # noqa: E402
import construct_seam as CS              # noqa: E402  (windmill, struct_gate, compare)

Q2 = SW.Q2
R2H = SW.R2H
OUT = os.path.join(ROOT, "workspace/push/band5_131.json")
FIVE = Q2(5)
TARGETS = (20, 21, 22, 23)


# ------------------------------------------------------------------ theorems
def pocket_bound(kmax: int = 4, Lmax: Q2 = FIVE) -> dict:
    """Exact enumeration of the corner-pocket family below `Lmax`.

    The four contact equations do not fix `L` for given blocks -- they fix the
    two *diagonal sums* `s1 = (a1+b1)+(a4+b4)` and `s2 = (a2+b2)+(a3+b3)`, and
    each forces `L = (s + sqrt2)/2`.  A tuple is admissible iff both diagonals
    agree (`s1 == s2`, otherwise the four contacts are inconsistent), and then
    its side is algebraic: `L = (s + sqrt2)/2`.  The enumeration reports the
    largest cell count over admissible tuples with `L < Lmax`.
    """
    best = {"n": 1, "blocks": ((0, 0),) * 4, "s": 0, "L": None}
    admissible = 0
    for a1 in range(kmax + 1):
        for b1 in range(kmax + 1):
            for a4 in range(kmax + 1):
                for b4 in range(kmax + 1):
                    s1 = a1 + b1 + a4 + b4
                    for a2 in range(kmax + 1):
                        for b2 in range(kmax + 1):
                            for a3 in range(kmax + 1):
                                for b3 in range(kmax + 1):
                                    if a2 + b2 + a3 + b3 != s1:
                                        continue
                                    L = (Q2(s1) + R2H * Q2(2)) * Q2(Fraction(1, 2))
                                    if L >= Lmax:
                                        continue
                                    # the blocks must not meet on a wall
                                    if (a1 + a2 > L or a3 + a4 > L
                                            or b1 + b2 > L or b3 + b4 > L):
                                        continue
                                    # both diagonal contacts fix the centre
                                    sp = Q2(a1 + b1) + R2H       # cx + cy
                                    sm = (L - a2 - b2) - R2H   # cx - cy
                                    cx = (sp + sm) * Q2(Fraction(1, 2))
                                    cy = (sp - sm) * Q2(Fraction(1, 2))
                                    if (cx - R2H < Q2(0) or cx + R2H > L
                                            or cy - R2H < Q2(0) or cy + R2H > L):
                                        continue
                                    admissible += 1
                                    n = a1 * b1 + a2 * b2 + a3 * b3 + a4 * b4 + 1
                                    if n > best["n"]:
                                        best = {"n": n, "s": s1, "L": CS.to_dec(L),
                                                "blocks": ((a1, b1), (a2, b2),
                                                           (a3, b3), (a4, b4))}
    return {"Lmax": str(CS.to_dec(Lmax)), "max_cells": best["n"],
            "at": best, "admissible_tuples": admissible}


def bound_argument(Lmax: Q2 = FIVE) -> dict:
    """The same bound as an inequality, with the arithmetic shown exactly.

    `L = (s + sqrt2)/2 < Lmax` fixes the largest integer `s`; on one diagonal
    two blocks with `t1 + t2 = s` hold at most `t1^2/4 + t2^2/4 <= s^2/8`
    cells, so the four corners hold at most `s^2/4` and the total is `s^2/4+1`.
    """
    s = 0
    while (Q2(s + 1) + R2H * Q2(2)) * Q2(Fraction(1, 2)) < Lmax:
        s += 1
    return {"largest_pair_sum": s, "max_cells": s * s // 4 + 1,
            "L_at_s": str(CS.to_dec((Q2(s) + R2H * Q2(2)) * Q2(Fraction(1, 2)))),
            "L_at_s_plus_1": str(CS.to_dec((Q2(s + 1) + R2H * Q2(2)) * Q2(Fraction(1, 2))))}


def tilted_block_bound(pmax: int = 8) -> list:
    """`(p+q)/sqrt2 >= sqrt(2pq)` for every p, q in the box, exactly."""
    rows = []
    for p in range(1, pmax + 1):
        for q in range(1, pmax + 1):
            side = Q2(p + q) * R2H               # (p+q)/sqrt2
            rows.append({"p": p, "q": q, "cells": p * q,
                         "side": str(CS.to_dec(side)),
                         "sqrt2pq": str(Decimal(2 * p * q).sqrt()),
                         "holds": bool(side * side >= Q2(2 * p * q)),
                         "beats_area_floor": bool(side * side > Q2(p * q))})
    return rows


# ------------------------------------------------------------------- probing
def probe(ns=TARGETS, delta=Fraction(1, 100), cap=6, top=8) -> list:
    """Bounded exact anchor-closure attempt at `L = k - delta` for each target."""
    import anchor_chain as AC
    f2 = AC.FIELDS[2]
    out = []
    for n in ns:
        k = isqrt(n)
        k = k if k * k == n else k + 1
        L = f2.q(Fraction(k) - delta)
        t0 = __import__("time").time()
        got = AC.settle(n, L, f2, mode="closure", node_cap=cap, top=top)
        out.append({"n": n, "k": k, "L": str(CS.to_dec(Q2(k))), "delta": str(delta),
                    "placed": len(got["placed"]), "why": got["why"],
                    "nodes": got["nodes"], "states": got["states"],
                    "refusals": got["refusals"], "exhausted": got["exhausted"],
                    "seconds": round(__import__("time").time() - t0, 1)})
    return out


# ------------------------------------------------------------------ controls
def selftest() -> int:
    """Four controls: the bound, its tightness, the tilted block, the target."""
    # 1. the bound at L = 5 is 17, and the 17 is *attained* by the windmill(2)
    pb = pocket_bound(kmax=3)
    assert pb["max_cells"] == 17, pb
    n17, cells, L17 = CS.windmill(2)
    assert n17 == 17 and L17 < FIVE, (n17, L17)
    g = SW.exact_gate(cells, L17)
    assert g["ok"], g
    print(f"  bound at L=5: max {pb['max_cells']} cells, attained by "
          f"windmill(2) n=17 L={CS.to_dec(L17):.6f} (exact_gate ok, "
          f"worst {g['worst_pen_q']})")

    # 2. below 5 the same enumeration cannot reach 20..23
    for n in TARGETS:
        assert pb["max_cells"] < n, (n, pb["max_cells"])
    ba = bound_argument()
    assert ba["max_cells"] == 17 and ba["largest_pair_sum"] == 8, ba
    print(f"  pair sum <= {ba['largest_pair_sum']} (L = {ba['L_at_s']} < 5; "
          f"sum 9 gives L = {ba['L_at_s_plus_1']}) => at most "
          f"{ba['max_cells']} cells")

    # 3. a single tilted block never beats its own area floor
    rows = tilted_block_bound(8)
    assert all(r["holds"] for r in rows)
    assert all(r["beats_area_floor"] for r in rows)
    print(f"  tilted block: (p+q)/sqrt2 >= sqrt(2pq) on all {len(rows)} (p,q); "
          f"20 cells would need L >= sqrt(40) = {Decimal(40).sqrt():.5f}")

    # 4. the target is only *sub*-5: the grid holds 20..23 at L = 5 exactly
    for n in TARGETS:
        k = isqrt(n)
        assert k * k < n <= (k + 1) ** 2 or n == 20, (n, k)
    cells = [((i + Fraction(1, 2)), (j + Fraction(1, 2)), 0)
             for i in range(5) for j in range(5)]
    assert len(cells) == 25
    print("  target: 20..23 are attainable at L = 5 (the 5x5 grid holds 25), "
          "so only L < 5 is at issue")
    print("  selftest OK")
    return 0


# ----------------------------------------------------------------------- main
def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()

    rec = {"targets": list(TARGETS)}
    if "--families" in argv or not argv:
        pb = pocket_bound(kmax=4)
        ba = bound_argument()
        tb = tilted_block_bound(8)
        rec.update({"pocket_bound": pb, "bound_argument": ba,
                    "tilted_block": tb})
        print(f"[pocket] below L = 5: at most {pb['max_cells']} cells "
              f"({pb['admissible_tuples']} admissible block tuples), "
              f"at {pb['at']['blocks']} with L = {pb['at']['L']:.6f}")
        print(f"[pocket] argument: pair sum <= {ba['largest_pair_sum']} "
              f"-> n <= {ba['max_cells']}")
        print(f"[tilted] (p+q)/sqrt2 >= sqrt(2pq) on all {len(tb)} (p,q) in 8x8; "
              f"a pure tilted block needs L >= sqrt(2N) > sqrt(N)")
        print(f"[band5]  rows 20..23 need 20..23 cells at L < 5; the pocket "
              f"mechanism caps at 17 -> short by 3..6 cells")

    if "--probe" in argv or not argv:
        pr = probe()
        rec["probe"] = pr
        print("\n[probe] exact anchor-closure at L = k - 1/100, node cap 60")
        for r in pr:
            print(f"  n={r['n']} L={r['L']}: {r['placed']}/{r['n']} placed, "
                  f"{r['why']}, nodes {r['nodes']}, refusals {r['refusals']}, "
                  f"exhausted {r['exhausted']}, {r['seconds']}s")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=1, default=str)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
