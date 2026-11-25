#!/usr/bin/env python3
r"""twin_boundary.py — commensurate twin-crystal constructor, zero overlap by design.

A "twin" here is two rigid square-lattice domains joined across one straight
interface.  Domain A is an `a1 x a2` block of unit cells; domain B is a
`b1 x b2` block rotated by the spinor angle

    tan(theta/2) = p/q   =>   cos theta = (q^2 - p^2)/(q^2 + p^2),
                              sin theta = 2pq/(q^2 + p^2),

which is **rational**: the "commensurate rational spinor" angles are exactly the
Pythagorean ones, so every centre, corner, separating axis and side in this
constructor is an exact `Fraction` and the gate is exact arithmetic, not a
tolerance.

Zero overlap is structural, not searched for: each domain is a lattice of unit
cells (disjoint by construction), and B's bounding box is placed at height
`a2 + g` above A, so the two domains are separated by the line gap `g >= 0`
whatever the twin angle.  `verify` re-decides it with the independent exact SAT
anyway, so a bug in the construction cannot pass silently.

Search: every split `a1*a2 + b1*b2 = n`, every spinor with `q <= QMAX`, every gap
on a small rational grid.  The family is also bounded in closed form for the
axis-aligned case: two blocks glued along a straight line need
`L >= max(a1, b1, a2 + b2)`, so a split whose bound already exceeds the
delivered side cannot be rescued by any gap or angle.

    python3 scripts/twin_boundary.py
    python3 scripts/twin_boundary.py --selftest
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import import_n090 as N9                      # noqa: E402  (exact SAT, corners)
import sqscore as SQ                          # noqa: E402

LEDGER = ROOT / "workspace/push/twin_boundary.json"
HALF = Fraction(1, 2)
QMAX = 6
GAPS = [Fraction(0), Fraction(1, 16), Fraction(1, 8), Fraction(1, 4), Fraction(1, 2)]


# ---------------------------------------------------------------- spinors ---
def spinor(p: int, q: int):
    d = q * q + p * p
    return Fraction(q * q - p * p, d), Fraction(2 * p * q, d)


def spinors(qmax: int = QMAX):
    out = []
    for q in range(1, qmax + 1):
        for p in range(0, q + 1):
            if p == 0 or _gcd(p, q) != 1:
                continue
            out.append((f"{p}/{q}", *spinor(p, q)))
    return out


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


# ------------------------------------------------------------- the blocks ---
def block(n1: int, n2: int, c: Fraction, s: Fraction):
    """Cell centres of an n1 x n2 block, its *corner* bbox min at the origin."""
    pts = []
    for i in range(n1):
        for j in range(n2):
            u, v = Fraction(2 * i + 1, 2), Fraction(2 * j + 1, 2)
            pts.append((u * c - v * s, u * s + v * c))
    cs = [p for x, y in pts for p in N9.corners(x, y, c, s)]
    mx = min(p[0] for p in cs)
    my = min(p[1] for p in cs)
    return [(x - mx, y - my, c, s) for x, y in pts]


def bbox(n1: int, n2: int, c: Fraction, s: Fraction):
    """Full block bbox (cell corners included) = n1*c + n2*s by n1*s + n2*c."""
    pts = block(n1, n2, c, s)
    xs = [p[0] for x, y, _, _ in pts for p in N9.corners(x, y, c, s)]
    ys = [p[1] for x, y, _, _ in pts for p in N9.corners(x, y, c, s)]
    return max(xs), max(ys)


def assemble(a1, a2, b1, b2, c, s, gap: Fraction):
    """A on the floor, B above it across a line gap.  Zero overlap by design."""
    A = block(a1, a2, Fraction(1), Fraction(0))
    wB, hB = bbox(b1, b2, c, s)
    B = block(b1, b2, c, s)
    B = [(x, y + a2 + gap, c, s) for x, y, _, _ in B]
    return A + B, max(Fraction(a1), wB, Fraction(a2) + gap + hB)


def side_of(pose):
    xs, ys = [], []
    for x, y, c, s in pose:
        for px, py in N9.corners(x, y, c, s):
            xs.append(px)
            ys.append(py)
    return max(max(xs) - min(xs), max(ys) - min(ys))


def verify(pose):
    """Independent exact SAT over every pair (should be 0 overlaps)."""
    n = len(pose)
    worst, pair = None, None
    for i in range(n):
        for j in range(i + 1, n):
            sl = N9.pair_slack(pose[i], pose[j])
            if worst is None or sl < worst:
                worst, pair = sl, (i, j)
    return {"overlaps": sum(1 for i in range(n) for j in range(i + 1, n)
                            if N9.pair_slack(pose[i], pose[j]) < 0),
            "min_slack": worst, "pair": pair}


def family_bound(n: int):
    """min over axis-aligned splits of max(a1, b1, a2 + b2)  (closed form)."""
    best = None
    for a1 in range(1, n):
        for a2 in range(1, n // a1 + 1):
            b = n - a1 * a2
            if b < 1:
                continue
            for b1 in range(1, b + 1):
                if b % b1:
                    continue
                b2 = b // b1
                lb = max(a1, b1, a2 + b2)
                if best is None or lb < best:
                    best = lb
    return best


# ------------------------------------------------------------------- main ---
def search(targets, delivered):
    """Side by closed form: W = b1*c + b2*s, H = b1*s + b2*c for a rotated block."""
    out = {}
    divisors = {b: [(d, b // d) for d in range(1, b + 1) if b % d == 0]
                for b in range(1, max(targets) + 1)}
    for n in targets:
        best, cands = None, 0
        for name, c, s in spinors():
            for a1 in range(1, n):
                for a2 in range(1, n // a1 + 1):
                    b = n - a1 * a2
                    if b < 1:
                        continue
                    for b1, b2 in divisors[b]:
                        wB, hB = b1 * c + b2 * s, b1 * s + b2 * c
                        for gap in GAPS:
                            cands += 1
                            side = max(Fraction(a1), wB, Fraction(a2) + gap + hB)
                            if best is None or side < best["side"]:
                                best = {"side": side, "a": (a1, a2), "b": (b1, b2),
                                        "spinor": name, "gap": gap,
                                        "spinor_cs": (c, s), "cands": 0}
        best["cands"] = cands
        c, s = best["spinor_cs"]
        pose, _ = assemble(*best["a"], *best["b"], c, s, best["gap"])
        v = verify(pose)
        best.pop("spinor_cs")
        best["bound"] = family_bound(n)
        best["verified"] = v
        best["side_built"] = side_of(pose)
        best["grid"] = SQ.grid(n)
        strictly = best["side"] < delivered[n]
        gain = (delivered[n] - best["side"]) / Fraction(n).limit_denominator(1).sqrt()             if False else (delivered[n] - best["side"]) / Fraction(n).__float__().__float__()
        best["strictly_smaller"] = strictly
        best["score_gain"] = float(gain)
        # C2: a gain below the 1e-8 score floor does not move the recorded total
        best["passes_c2_noise"] = strictly and float(gain) >= 1e-8
        best["promotable"] = bool(best["passes_c2_noise"])
        best["beats_delivered"] = best["promotable"]
        best["theorem_holds"] = best["side"] >= SQ.grid(n)
        best["delivered"] = delivered[n]
        out[n] = best
    return out


def main() -> int:
    per = SQ.load()
    delivered = {n: Fraction(str(SQ.extent(per[n]))) for n in per}
    targets = [11, 17, 18, 19, 51, 55, 68, 72, 83, 84, 85, 86, 88, 89]
    res = search(targets, delivered)
    wins = []
    print(f"{'n':>4} {'best':>12} {'delivered':>12} {'bound':>6} {'spinor':>7} {'gap':>6} "
          f"{'A':>7} {'B':>7} {'ovl':>4} {'beats':>6}")
    for n in targets:
        r = res[n]
        if r["beats_delivered"]:
            wins.append(n)
        print(f"{n:>4} {float(r['side']):>12.6f} {float(r['delivered']):>12.6f} "
              f"{r['bound']:>6} {r['spinor']:>7} {str(r['gap']):>6} "
              f"{str(r['a']):>7} {str(r['b']):>7} {r['verified']['overlaps']:>4} "
              f"{str(r['beats_delivered']):>6}")
    led = {"targets": targets,
           "angles": [name for name, _, _ in spinors()],
           "gaps": [str(g) for g in GAPS],
           "wins": wins,
           "results": {str(n): {k: (str(v) if isinstance(v, Fraction) else v)
                                for k, v in res[n].items()} for n in targets}}
    LEDGER.write_text(json.dumps(led, indent=1, default=str) + "\n")
    strict = [n for n in targets if res[n]["strictly_smaller"]]
    print(f"{len(led['angles'])} spinor angles x {len(GAPS)} gaps x every integer "
          f"split, {len(targets)} rows: {len(strict)} strictly smaller, "
          f"{len(wins)} above the C2 noise floor (so promotable)")
    ok = all(res[n]["theorem_holds"] for n in targets)
    print(f"family theorem (best side >= ceil(sqrt n), i.e. it can at best tie the "
          f"grid): {'holds on every row' if ok else 'VIOLATED'}")
    print(f"best spinor per row: "
          f"{sorted({res[n]['spinor'] for n in targets})} "
          f"(1/1 = 90 degrees, the degenerate twin = two plain grids)")
    print(f"wrote {LEDGER}")
    return 0


# --------------------------------------------------------------- selftest ---
def selftest() -> int:
    print("twin_boundary selftest")
    # 1. spinors are rational unit rotations
    for name, c, s in spinors():
        assert c * c + s * s == 1, (name, c, s)
    assert spinor(1, 1) == (Fraction(0), Fraction(1))       # 90 degrees
    assert spinor(1, 2) == (Fraction(3, 5), Fraction(4, 5))  # the 3-4-5 twin
    print(f"  1. {len(spinors())} rational spinors: c^2 + s^2 = 1 exactly; "
          f"p/q = 1/2 gives (3/5, 4/5)")

    # 2. a 2x2 block rotated by the 3-4-5 twin has an exact bbox of 14/5 x 14/5
    w, h = bbox(2, 2, *spinor(1, 2))
    assert (w, h) == (Fraction(14, 5), Fraction(14, 5)), (w, h)
    print(f"  2. 2x2 block at the 3-4-5 twin: bbox {w} x {h} exactly")

    # 3. the assembly is legal: a 3x2 axis block plus a 2x2 twin block, gap 0
    c, s = spinor(1, 2)
    pose, side = assemble(3, 2, 2, 2, c, s, Fraction(0))
    v = verify(pose)
    assert v["overlaps"] == 0 and v["min_slack"] == 0, v
    assert side == max(Fraction(3), Fraction(14, 5), Fraction(2) + Fraction(14, 5)), side
    print(f"  3. 3x2 + 2x2 twin at gap 0: 0 overlaps, min slack 0, side {side} exactly")

    # 4. a perturbed twin does overlap -- the gate is not vacuous
    bad = list(pose)
    x0, y0, c0, s0 = bad[0]
    bad[0] = (x0, y0 + Fraction(1, 2), c0, s0)
    v2 = verify(bad)
    assert v2["overlaps"] >= 1 and v2["min_slack"] < 0, v2
    print(f"  4. one cell displaced: {v2['overlaps']} overlap(s), min slack "
          f"{float(v2['min_slack']):+.3f}")

    # 5. the family bound is the closed form it claims to be
    assert family_bound(12) <= 4, family_bound(12)   # 3x2 + 3x2 -> max(3,3,4)
    print(f"  5. family bound at n = 12: {family_bound(12)} "
          f"(3x2 + 3x2 glued: max(a1, b1, a2 + b2))")
    print("selftest OK (5 controls)")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
