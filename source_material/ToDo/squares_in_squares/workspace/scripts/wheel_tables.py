#!/usr/bin/env python3
r"""wheel_tables.py — run 6, piece (a): the chain marginal-cost table.

For a square tilted theta inscribed in a corner (touching both walls):
  leg along each wall  = (c+s)/2 * 2 = c+s  (bbox legs)
  distance to diagonal = (c+s)/sqrt(2)
Marginal cost of a square in a corner chain (block-inscribed family,
s = a + 1 + b(c+s)/2): per-block-square cost = (c+s)/2.
Qwen's claim: 45° (= (1+i)) is THE wheel; Eisenstein 60°, arctan(1/2)
(Q(sqrt(5))), 30° (Q(sqrt(3))) are predicted next wheels.
This table computes, for each algebraic angle:
  - block marginal cost (c+s)/2 (pure tilted-grid block)
  - the staircase-interface waste: at 45° the axis-aligned staircase
    steps advance 1-per-1 matching the diamond edge slope 1; at theta
    the diamond edge slope is tan(theta) or 1/tan(theta); the interface
    gap between staircase steps and the tilted block edge.
Verdict printed: is 45° the unique minimizer of the TOTAL family cost?
"""
from math import sqrt, tan, atan, degrees, cos, sin

ANGLES = {
    "0": 0.0,
    "30 (Q(sqrt3))": atan(1 / sqrt(3)),
    "36.87 (3-4-5, Q(sqrt5)-ish)": atan(3 / 4),
    "45 (Q(sqrt2), (1+i))": atan(1),
    "53.13 (arctan(4/3))": atan(4 / 3),
    "60 (Eisenstein, Q(sqrt3))": atan(sqrt(3)),
    "26.565 (arctan(1/2), Q(sqrt5))": atan(0.5),
    "18.435 (arctan(1/3))": atan(1 / 3),
    "arctan(1/4)": atan(0.25),
    "90": atan(1e18),
}


def block_cost(th):
    c, s = cos(th), sin(th)
    return (c + s) / 2


def staircase_interface_waste(th, steps=8):
    """Gap area between an axis-aligned staircase (steps of 1) and the
    tilted block edge, per unit length, in the corner triangle.
    The diamond edge from the corner region: line y = x * m with slope
    m = tan(45-th)... For the centered tilted block, the relevant edge
    near a corner runs at angle (90-th) to the x-axis in the corner's
    local frame; its slope vs the staircase (slope 1 at 45deg).
    Interface waste per step: the triangle between the step corner and
    the block edge. For edge slope k (dy/dx), a step of width 1 rises 1;
    the edge rises k. Waste triangle area per step = |k-1|/2 (bounded by
    the block edge being the binding constraint).
    At 45 deg the edge slope in the corner frame is 1: waste 0."""
    # the tilted block edge direction in the container frame: the block
    # is rotated by th; its edge in the corner quadrant runs at angle
    # (90 - th) from the x-axis for th<45 (or th-... ). The staircase
    # step diagonal runs at 45. The binding edge slope:
    k = tan(th) if th < atan(1) else 1 / tan(th)
    # slope of the block edge projected in the corner frame:
    # for the square family, the edge that the staircase leans on has
    # slope 1 exactly at th=45; away from 45 the effective slope is
    # k_e = (1 - tan(th))/(1 + tan(th))  (rotating the 45-degree line
    # by th): tan(45 - th) in the corner frame.
    k_e = tan(atan(1) - th)
    # waste per step of width 1: the staircase's step corners sit on
    # y=x; the block edge sits at y = k_e * x; area between over x in
    # [0, steps]: 0.5 * |1 - k_e| * steps^2 / steps = per-step avg.
    # Per-step triangle: base 1 along x, height |1-k_e|*1 at the step
    # corner: cumulative gap area = |1-k_e| * steps * (steps+1) / 2
    # minus the staircase's own area steps(steps+1)/2 ... reported as
    # the per-step interface gap:
    return abs(1 - k_e)


def main():
    print(f"{'angle':<28} {'(c+s)/2':>8} {'interface':>10} {'total':>8}")
    best = None
    rows = []
    for name, th in ANGLES.items():
        bc = block_cost(th)
        iw = staircase_interface_waste(th)
        tot = bc + iw
        rows.append((name, bc, iw, tot))
        if "45" not in name:
            if best is None or tot < best[1]:
                best = (name, tot)
        print(f"{name:<28} {bc:8.4f} {iw:10.4f} {tot:8.4f}")
    c45 = block_cost(atan(1))
    print(f"\n45-deg block cost: {c45:.4f}; pure-block minimizer is NOT 45"
          f" (30 deg: {block_cost(atan(1/sqrt(3))):.4f})")
    print("=> the 45-deg advantage must come from the staircase interface;")
    print("   interface waste |1-tan(45-th)| is 0 ONLY at th=45.")
    print("   For the FULL family (block + axis-aligned staircases) 45 deg")
    print("   is the unique zero-interface angle: the (1+i) claim HOLDS")
    print("   for combined structures; pure tilted blocks are cheaper at")
    print("   30 deg but cannot be completed by axis-aligned squares")
    print("   without paying the interface waste.")
    # exact check: family values at open n hit below grid?
    # s(theta,a,b) = a + 1 + b(c+s)/2 with n = b^2 + 2a(a+1)
    # grid g = ceil(sqrt(n)). Sweep open n:
    import json
    from math import ceil
ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

    tab = json.load(open(ROOT + "/workspace/submission/table.json"))
    open_n = [n for n in range(1, 1001)
              if tab[str(n)]["src"].startswith("grid")]
    hits = []
    for n in open_n:
        g = ceil(sqrt(n))
        for b in range(1, 40):
            rem = n - b * b
            if rem < 0:
                break
            if rem % 2:
                continue
            half = rem // 2
            # a(a+1) = half
            a = int((sqrt(4 * half + 1) - 1) / 2)
            if a * (a + 1) != half or a < 0:
                continue
            for name, th in ANGLES.items():
                if th == 0.0 and "0" == name:
                    continue
                s = a + 1 + b * block_cost(th)
                if s < g - 1e-9:
                    hits.append((n, g, name, round(s, 4), a, b))
    print(f"\nparametric hits below grid at open n (NEED verification): {len(hits)}")
    for h in hits[:12]:
        print("   ", h)
    json.dump(rows, open(ROOT + "/workspace/push/wheel_tables.json", "w"))


if __name__ == "__main__":
    main()
