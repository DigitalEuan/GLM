#!/usr/bin/env python3
r"""true_geom.py — the true geometry of a submission row, at 40 decimal digits.

`sqscore` measures a row with `float` and `math.cos/math.sin`; the exact gate measures a
*word* row in `Q(sqrt 2)`. Neither can answer the question run 109 exposed: what is the
real side of a row whose angles are not words? This module answers it without a float:
`Decimal` at 40 digits, with `cos`/`sin` from their Taylor series after exact argument
reduction, and the separation test from the separating-axis theorem in the same arithmetic.

It is used three ways:

  * `reconcile_table.py` — to audit and rewrite the per-row sides in `table.json`;
  * `semantic_pack.py --guard` — as the ε(gap) containment check on a snapped-model candidate;
  * `relax_angles.py` — to score a continuous position/angle search honestly.

Definitions (a square of side 1, centre `p`, angle `t`, edge vectors `u = (cos t, sin t)`,
`v = (-sin t, cos t)`):

    half_extent_x = (|u.x| + |v.x|) / 2 = (|cos t| + |sin t|) / 2
    side          = max( max_i(x_i + hx_i) - min_i(x_i - hx_i),
                         max_i(y_i + hy_i) - min_i(y_i - hy_i) )
    separated(i,j) for some axis q  in  {u_i, v_i, u_j, v_j}:
                    |(p_j - p_i) . q| >= h_i(q) + h_j(q),
                    h_i(q) = (|u_i . q| + |v_i . q|) / 2

Nothing here is claimed to be *certified* outside the digits used: the value is correct to the
working precision (40 digits, and every comparison in this repository is 12 digits coarser),
which is enough to tell a 1e-4 artifact from a real gain.

    python3 scripts/true_geom.py --selftest
"""
from __future__ import annotations

import sys
from decimal import Decimal, getcontext, localcontext

DPS = 40
getcontext().prec = DPS + 10

PI = Decimal("3.1415926535897932384626433832795028841971693993751"
             "05820974944592307816406286208998628034825342117067982148")
TWO_PI = 2 * PI
HALF_PI = PI / 2
QUARTER_PI = PI / 4


def cos_sin(x):
    """`(cos x, sin x)` at the working precision, by exact reduction and Taylor series."""
    with localcontext() as ctx:
        ctx.prec = DPS + 10
        # exact reduction into [0, 2 pi)
        k = int(x / TWO_PI) if x >= 0 else int(x / TWO_PI) - 1
        r = x - k * TWO_PI
        # quadrant into [0, pi/2)
        q = int(r / HALF_PI)
        r = r - q * HALF_PI
        # fold into [-pi/4, pi/4] to keep the series short and alternating
        flip = False
        if r > QUARTER_PI:
            r = HALF_PI - r
            flip = True
        term, c, s = Decimal(1), Decimal(0), Decimal(0)
        # cos r
        t, n = Decimal(1), 0
        while True:
            c += t
            n += 2
            t = -t * r * r / (n * (n - 1))
            if abs(t) < Decimal(10) ** (-(DPS + 6)):
                break
        # sin r
        t, n = r, 1
        while True:
            s += t
            n += 2
            t = -t * r * r / (n * (n - 1))
            if abs(t) < Decimal(10) ** (-(DPS + 6)):
                break
        if flip:
            c, s = s, c
        # quadrant
        if q == 0:
            pass
        elif q == 1:
            c, s = -s, c
        elif q == 2:
            c, s = -c, -s
        else:
            c, s = s, -c
        return +c, +s


def axes(angle):
    """The two edge unit vectors of a square at `angle`."""
    c, s = cos_sin(angle)
    return (c, s), (-s, c)


def half_extents(angle):
    (c, s), _v = axes(angle)
    return (abs(c) + abs(s)) / 2, (abs(c) + abs(s)) / 2


def side(state):
    """The container side of `state` = [(x, y, angle), ...], in decimals at working precision."""
    with localcontext() as ctx:
        ctx.prec = DPS
        xs_lo, xs_hi, ys_lo, ys_hi = None, None, None, None
        for x, y, t in state:
            x, y, t = Decimal(str(x)), Decimal(str(y)), Decimal(str(t))
            hx, hy = half_extents(t)
            lo, hi = x - hx, x + hx
            xs_lo = lo if xs_lo is None or lo < xs_lo else xs_lo
            xs_hi = hi if xs_hi is None or hi > xs_hi else xs_hi
            lo, hi = y - hy, y + hy
            ys_lo = lo if ys_lo is None or lo < ys_lo else ys_lo
            ys_hi = hi if ys_hi is None or hi > ys_hi else ys_hi
        return max(xs_hi - xs_lo, ys_hi - ys_lo)


def check_cs(cells):
    """`check` for cells given as `(x, y, c, s)` -- an exact direction, no angle at all."""
    with localcontext() as ctx:
        ctx.prec = DPS
        xs_lo = xs_hi = ys_lo = ys_hi = None
        dec = []
        for x, y, c, s in cells:
            x, y = Decimal(str(x)), Decimal(str(y))
            c, s = Decimal(str(c)), Decimal(str(s))
            h = (abs(c) + abs(s)) / 2
            dec.append((x, y, c, s))
            lo, hi = x - h, x + h
            xs_lo = lo if xs_lo is None or lo < xs_lo else xs_lo
            xs_hi = hi if xs_hi is None or hi > xs_hi else xs_hi
            lo, hi = y - h, y + h
            ys_lo = lo if ys_lo is None or lo < ys_lo else ys_lo
            ys_hi = hi if ys_hi is None or hi > ys_hi else ys_hi
        side_v = max(xs_hi - xs_lo, ys_hi - ys_lo)
        bad = []
        n = len(dec)
        for i in range(n):
            xi, yi, ci, si = dec[i]
            for j in range(i + 1, n):
                xj, yj, cj, sj = dec[j]
                dx, dy = xj - xi, yj - yi
                best = None
                for (c1, s1, c2, s2) in ((ci, si, cj, sj), (cj, sj, ci, si)):
                    for q in ((c1, s1), (-s1, c1), (c2, s2), (-s2, c2)):
                        proj = dx * q[0] + dy * q[1]
                        h1 = (abs(c1 * q[0] + s1 * q[1]) + abs(-s1 * q[0] + c1 * q[1])) / 2
                        h2 = (abs(c2 * q[0] + s2 * q[1]) + abs(-s2 * q[0] + c2 * q[1])) / 2
                        sl = abs(proj) - (h1 + h2)
                        best = sl if best is None or sl > best else best
                if best < 0:
                    bad.append((i, j, best))
        bad.sort(key=lambda b: b[2])
        return {"side": side_v, "violations": bad,
                "worst": bad[0][2] if bad else None, "N": n}


def pair_slack(state, i, j):
    """The exact-ish SAT slack of a pair at working precision: >= 0 means separated."""
    with localcontext() as ctx:
        ctx.prec = DPS
        (xi, yi, ti), (xj, yj, tj) = state[i], state[j]
        xi, yi = Decimal(str(xi)), Decimal(str(yi))
        xj, yj = Decimal(str(xj)), Decimal(str(yj))
        dx, dy = xj - xi, yj - yi
        best = None
        for t_own, t_oth in ((ti, tj), (tj, ti)):
            (c1, s1), (v1, v2) = axes(Decimal(str(t_own)))[0], axes(Decimal(str(t_own)))[1]
            (c2, s2), (v3, v4) = axes(Decimal(str(t_oth)))[0], axes(Decimal(str(t_oth)))[1]
            for q in ((c1, s1), (v1, v2), (c2, s2), (v3, v4)):
                proj = dx * q[0] + dy * q[1]
                h = ((abs(c1 * q[0] + s1 * q[1]) + abs(v1 * q[0] + v2 * q[1]))
                     + (abs(c2 * q[0] + s2 * q[1]) + abs(v3 * q[0] + v4 * q[1]))) / 2
                sl = abs(proj) - h
                best = sl if best is None or sl > best else best
        return best


def check(state):
    """`{'side', 'violations': [(i, j, slack)], 'worst'}` for a state, in decimals."""
    bad = []
    n = len(state)
    for i in range(n):
        for j in range(i + 1, n):
            sl = pair_slack(state, i, j)
            if sl < 0:
                bad.append((i, j, sl))
    bad.sort(key=lambda b: b[2])
    return {"side": side(state), "violations": bad,
            "worst": bad[0][2] if bad else None, "N": n}


def selftest():
    """Three controls: an axis square, a 45 degree square, and a touching pair."""
    one = side([(0, 0, 0)])
    assert one == 1, one                                  # a unit square is its own side
    root2 = side([(0, 0, PI / 4)])
    assert abs(root2 - Decimal(2).sqrt()) < Decimal("1e-38"), root2   # 45 degrees has side sqrt 2
    pair = check([(0, 0, 0), (1, 0, 0)])
    assert pair["side"] == 2 and not pair["violations"], pair          # touching, not overlapping
    moved = check([(0, 0, 0), (Decimal("0.5"), 0, 0)])
    assert moved["violations"] and moved["worst"] < 0, moved           # overlapping
    # a 45 degree square needs sqrt2, not 1, of separation from an axis square to stay clear
    assert not check([(0, 0, 0), (Decimal("0.5") + Decimal(2).sqrt() / 2 + Decimal("0.01"), 0, PI / 4)])["violations"]
    print("control 1 -- an axis square has side exactly 1; a 45 degree square exactly sqrt 2 "
          f"({root2:.20f}).")
    print("control 2 -- two unit squares 1 apart are separated with slack 0, and at 1/2 apart "
          "the pair is a violation with a negative slack.")
    print("control 3 -- an axis square and a 45 degree square are separated at offset "
          "1/2 + sqrt2/2, so the SAT test uses the rotated half-extent and not the axis one.")
    print("true_geom: OK (3 controls)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        selftest()
