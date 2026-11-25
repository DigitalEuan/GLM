#!/usr/bin/env python3
r"""import_n090.py — the n = 90 published candidate, decided exactly (C1/C2).

The published record (squaremath.org/cases/90.html, `s(90) = 9.9940387665828706`,
jazivxt 2026, improved by de Winter, T-338) carries an **exact rational** reading
copy: each of the 90 rows is

    [cx_numerator, cy_numerator, tan_half_angle]

with a global integer `center_scale`, so the centre is `(cx/scale, cy/scale)` and
the orientation is `2*arctan(t)`.  The key arithmetic fact: for a rational `t`,

    cos(2 arctan t) = (1 - t^2)/(1 + t^2),   sin(2 arctan t) = 2t/(1 + t^2),

so the rotation is **rational** and the whole certificate lives in `Q`: corners,
separations and the bounding box are exact `Fraction`s.  There is no float, no
`Decimal` and no interval anywhere in the decision path.

C1 (proof): every pair of unit squares is separated along one of the four
orientation axes by a non-negative exact rational slack (touching = slack 0 is
legal, the repository's own convention: `legal_slide` calls `0E-39` legal).
C2 (margin): the exact bounding-box side is strictly below the delivered row-90
side, and the score gain is the exact rational `(L_ours - L_cand)/sqrt(90)`
evaluated in `Decimal` at 40 digits.

Run: `python3 scripts/import_n090.py [--selftest]`
Writes `workspace/push/import_n090.json`.
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "workspace/push/n090_candidate-reading-copy.json"
OUT = ROOT / "workspace/push/import_n090.json"

# delivered row 90 (workspace/submission/submission.csv, n = 90, the 10x10 house)
L_DELIVERED = Fraction(100000000019, 10000000000)  # 10.0000000019
N_ROW = 90


# ---------------------------------------------------------------- the pose ---
def rotation(t: Fraction) -> tuple[Fraction, Fraction]:
    """(cos, sin) of 2*arctan(t), exactly."""
    d = 1 + t * t
    return (1 - t * t) / d, 2 * t / d


def corners(x: Fraction, y: Fraction, c: Fraction, s: Fraction):
    """The four corners of the unit square centred at (x, y) rotated by (c, s)."""
    out = []
    for u, v in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        u, v = Fraction(u, 2), Fraction(v, 2)
        out.append((x + u * c - v * s, y + u * s + v * c))
    return out


def load_pose(path: Path = CAND):
    d = json.loads(path.read_text())
    scale = Fraction(d["provenance"]["center_scale"])  # "A/B"
    assert scale > 0, scale
    pose = []
    for row in d["squares"]:
        x = Fraction(row[0]) / scale   # exact scalar strings ("A/B")
        y = Fraction(row[1]) / scale
        c, s = rotation(Fraction(row[2]))
        pose.append((x, y, c, s))
    return d, pose


# ------------------------------------------------------------- the checker ---
def pair_slack(a, b) -> Fraction:
    """max over the four orientation axes of the exact separating slack.

    slack >= 0 on any axis  <=>  the closed squares are disjoint on that axis.
    """
    xa, ya, ca, sa = a
    xb, yb, cb, sb = b
    dx, dy = xb - xa, yb - ya
    best = None
    for ux, uy in ((ca, sa), (-sa, ca), (cb, sb), (-sb, cb)):
        proj_a = (abs(ux * ca + uy * sa) + abs(ux * -sa + uy * ca)) / 2
        proj_b = (abs(ux * cb + uy * sb) + abs(ux * -sb + uy * cb)) / 2
        sl = abs(dx * ux + dy * uy) - proj_a - proj_b
        best = sl if best is None or sl > best else best
    return best


def check(pose) -> dict:
    n = len(pose)
    slacks = {}
    for i in range(n):
        for j in range(i + 1, n):
            slacks[(i, j)] = pair_slack(pose[i], pose[j])
    bad = sum(1 for v in slacks.values() if v < 0)
    argmin = min(slacks, key=lambda k: slacks[k]) if slacks else None
    min_slack = slacks[argmin] if slacks else None
    touching = sum(1 for v in slacks.values() if v == 0)
    xs, ys = [], []
    for x, y, c, s_ in pose:
        for px, py in corners(x, y, c, s_):
            xs.append(px)
            ys.append(py)
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    return {
        "n": n,
        "pairs": n * (n - 1) // 2,
        "overlaps": bad,
        "min_slack": min_slack,
        "min_slack_pair": list(argmin) if argmin else None,
        "width": w,
        "height": h,
        "side": max(w, h),
        "touching_pairs": touching,
    }


DELTA = Fraction(1, 10 ** 9)   # our own frame convention (submission pads by 1e-9)


def inflate(pose, delta: Fraction = DELTA):
    """Scale every centre by (1 + delta): each pair's clearance grows by >= delta.

    The published certificate touches to 1e-73; a CSV rendered in decimals cannot
    keep that, so this is the pose an actual delivered row would carry.  The cost
    is `delta` times the radial extent, ~1e-8 of side -- eight orders of magnitude
    below the 5.96e-3 margin.
    """
    mu = 1 + delta
    return [(x * mu, y * mu, c, s_) for (x, y, c, s_) in pose]


def gain(n: int, l_from: Fraction, l_to: Fraction) -> str:
    """Exact (l_from - l_to)/sqrt(n) as a 12-digit string, in Decimal."""
    from decimal import Decimal, getcontext

    getcontext().prec = 50
    num = Decimal(l_from.numerator) / Decimal(l_from.denominator)
    den = Decimal(l_to.numerator) / Decimal(l_to.denominator)
    return str((num - den) / Decimal(n).sqrt())


# --------------------------------------------------------------- selftest ---
def selftest() -> None:
    print("import_n090 selftest")

    # 1. the 5x5 grid at side 5: legal, side exactly 5, 40 touching pairs
    grid = []
    for i in range(5):
        for j in range(5):
            grid.append((Fraction(2 * i + 1, 2), Fraction(2 * j + 1, 2),
                         Fraction(1), Fraction(0)))
    st = check(grid)
    assert st["overlaps"] == 0 and st["side"] == 5 and st["min_slack"] == 0, st
    print(f"  1. 5x5 grid: legal at side exactly 5, {st['touching_pairs']} touching "
          f"pairs, min slack 0")

    # 2. planted overlap: displace one square by 1/2 in x -> a negative slack
    bad_pose = list(grid)
    x, y, c, s = bad_pose[7]
    bad_pose[7] = (x + Fraction(1, 2), y, c, s)
    st2 = check(bad_pose)
    assert st2["overlaps"] >= 1 and st2["min_slack"] < 0, st2
    print(f"  2. displaced square: {st2['overlaps']} overlapping pair(s), "
          f"min slack {float(st2['min_slack']):+.6f} -- the checker is not vacuous")

    # 3. rotation algebra: t = 1/2 gives the Pythagorean (3/5, 4/5); the unit
    #    square at that angle has bounding box 7/5 x 7/5, exactly
    c, s = rotation(Fraction(1, 2))
    assert (c, s) == (Fraction(3, 5), Fraction(4, 5)), (c, s)
    assert c * c + s * s == 1
    one = (Fraction(0), Fraction(0), c, s)
    st3 = check([one])
    assert st3["side"] == Fraction(7, 5), st3["side"]
    print(f"  3. t=1/2 -> (cos,sin) = (3/5,4/5) exactly; unit square bbox 7/5 x 7/5")

    # 4. the published candidate: legal, and strictly better than our row 90
    d, pose = load_pose()
    st4 = check(pose)
    assert st4["n"] == 90 and st4["overlaps"] == 0, st4
    assert st4["side"] < L_DELIVERED, (st4["side"], L_DELIVERED)
    g = gain(N_ROW, L_DELIVERED, st4["side"])
    assert 6.28e-4 < float(g) < 6.29e-4, g
    print(f"  4. candidate: 90 cells, 0 overlaps, {st4['touching_pairs']} touching "
          f"pairs, side {float(st4['side']):.16f} < {float(L_DELIVERED)}, "
          f"gain {float(g):.9e}")
    st5 = check(inflate(pose))
    assert st5["overlaps"] == 0 and st5["min_slack"] > 0, st5["min_slack"]
    assert st5["side"] < L_DELIVERED, st5["side"]
    print(f"  5. rendered at our 1e-9 frame convention: 0 overlaps, min slack "
          f"{float(st5['min_slack']):.3e}, side {float(st5['side']):.16f} still "
          f"below {float(L_DELIVERED)}")
    print("selftest OK (5 controls)")


# ------------------------------------------------------------------- main ---
def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
        return
    d, pose = load_pose()
    st = check(pose)
    st["published_s_exact"] = d["s_exact"]
    st["published_side_decimal"] = float(Fraction(d["s_exact"]))
    st["L_delivered"] = float(L_DELIVERED)
    st["side_float"] = float(st["side"])
    st["gain_over_delivered"] = gain(N_ROW, L_DELIVERED, st["side"])
    st["gain_float"] = float(st["gain_over_delivered"])
    st["c1_exact"] = st["overlaps"] == 0
    dense = check(inflate(pose))
    st["render_delta"] = "1e-9"
    st["render_overlaps"] = dense["overlaps"]
    st["render_min_slack"] = str(dense["min_slack"])
    st["render_side"] = str(dense["side"])
    st["render_gain"] = gain(N_ROW, L_DELIVERED, dense["side"])
    st["render_gain_float"] = float(st["render_gain"])
    st["c2_margin"] = str(Fraction(L_DELIVERED) - st["side"])
    st["source"] = str(CAND.relative_to(ROOT))
    OUT.write_text(json.dumps(
        {k: (str(v) if isinstance(v, Fraction) else v) for k, v in st.items()},
        indent=1, sort_keys=True) + "\n")
    print(f"n = {st['n']}: {st['pairs']} pairs, {st['overlaps']} overlaps, "
          f"min slack {float(st['min_slack']):+.3e} at {st['min_slack_pair']}")
    print(f"touching pairs exactly 0 slack: {st['touching_pairs']}")
    print(f"bbox  {float(st['width']):.16f} x {float(st['height']):.16f}")
    print(f"side  {float(st['side']):.16f}   (published exact "
          f"{st['published_side_decimal']:.16f})")
    print(f"ours  {float(L_DELIVERED):.16f}")
    print(f"margin {float(Fraction(st['c2_margin'])):+.6e}; "
          f"gain {st['gain_float']:.9e}")
    print(f"rendered (centres x 1+1e-9): {dense['overlaps']} overlaps, min slack "
          f"{float(dense['min_slack']):.3e}, side {float(dense['side']):.16f}, "
          f"gain {st['render_gain_float']:.9e}")
    print(f"C1 exact: {'PASS' if st['c1_exact'] else 'FAIL'}; "
          f"C2 margin: {'PASS' if st['side'] < L_DELIVERED else 'FAIL'}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
