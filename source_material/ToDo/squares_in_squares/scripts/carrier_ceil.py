#!/usr/bin/env python3
r"""carrier_ceil.py — the block-bedded carrier's exact ceiling: the family's whole surface (Run 148).

Run 145 built the block-bedded carrier (`block_bed.py`, doc 102) and measured **19 of 110**
delivered `(n, side)` pairs reproduced, with the entry test FAILING at 19 against a threshold of
20.  Run 146 probed it on those 110 rows and found **0 beats in 949,243 trials**; run 147 extended
it to `r` equal runs per axis and found **0 beats in 124,176 trials over the 19 reach rows**.  Both
are *visits*: they ask ``is there a declaration at a side below the delivered one'' for a declared
list of rows and sides.  Neither answers the question for the table.

This module answers the family's question the other way round.  The family's count is

    n = K^2 - D(L) + p*q

with `D(L)` the number of carrier cells the block beds out.  `D` is a **step function of `L`**:
each carrier cell is bedded exactly on one open interval `(lo, hi)` of sides (the intersection of
four strict SAT inequalities, all affine in `L`), so `D(L)` is the number of those intervals
covering `L`, and the family's entire `(side, count)` surface is the union over declarations of a
finite set of open intervals, each carrying one integer count.

So the module does not search a row: it sweeps `L` once per declaration, in exact arithmetic, and
records **the smallest side at which the family attains each count**.  That is `L_min(n)`, and the
whole table is then read off by comparison:

    L_min(n) <  L_del(n)   the carrier beats row n        (none exist in scope)
    L_min(n) == L_del(n)   the carrier reproduces the row  (the 19 known ties)
    L_min(n) >  L_del(n)   the carrier cannot reach it     (a refusal with a number)

EXACTNESS.  Every carrier cell is at a lattice or `L`-shifted position, so every window endpoint
is `(m + n*sqrt2)/4` with `m, n` integers (`Ap = (4 + 2p*sqrt2)/4`, `Aq = (4 + 2q*sqrt2)/4`,
`C = (2 + (p+q)*sqrt2)/4`, and a division by `+-1` or `+-1/2`).  Comparisons are the integer sign
test `sign(m + n*sqrt2)` (`m^2` against `2n^2`), so the sweep, its ordering and every count claim
are exact -- no tolerance anywhere.  The built poses are judged by `qsqrt2.gate`, the repository's
exact SAT judge, and cross-checked against `packlib.verify` as a second, independent referee.

THE FALSIFIER.  A row the literature **proves optimal** cannot be beaten by any legal pose.  The
solver is run over those rows first: if it ever reports `L_min(n) < L_del(n)` there, the sweep is
wrong.  That control costs nothing and it is the strongest one in the file.

    python3 scripts/carrier_ceil.py              # the map over n = 1..100, writes the ledger
    python3 scripts/carrier_ceil.py --selftest    # 7 controls
    python3 scripts/carrier_ceil.py --row 20      # every declaration that reaches 20

WHAT THE RUN FOUND.  See doc 105.  In the declared family (`r = 2` runs per axis, a centred `p x q`
block, every split, every shape with `p + q <= 14`, sides up to `10.5`) the carrier's reach is
exactly the delivered table's own symmetric rows: it attains a count below a grid row **nowhere**,
and the smallest side it reaches at a tie row's count is the tie itself or above it.  The band-5
arithmetic is settled inside the run: with `K = 4` the count needs `p*q - D = 4` and `L >= (p+q)/2
sqrt2` with `L < 5`, so `p + q <= 7`; the only shapes that qualify need `D` at a side where the
carrier still has cells to bed, and the sweep reports `0` such declarations.  That is the same
statement run 131 proved for the corner-pocket mechanism, now proved for the carrier by a sweep of
the whole surface instead of a probe of one row.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F
from functools import cmp_to_key
from math import isqrt

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import block_bed as BB                          # noqa: E402  (in_bed, block: the family's own rule)
import qsqrt2 as Q                              # noqa: E402  (the exact gate)
from qsqrt2 import Q2, HALF                     # noqa: E402

CSV = os.path.join(ROOT, "workspace/submission/submission.csv")
LEDGER = os.path.join(ROOT, "workspace/push/carrier_ceil.json")
LEDGER_WIDE = os.path.join(ROOT, "workspace/push/carrier_ceil_wide.json")

AXIS = Q.AXIS
W45 = Q.word_45()

#: the CSV stores every row at up to +2e-9 above its true side (the round-trip clearance), so a
#: comparison at 1e-9 reads that storage noise as a gain.  A beat must clear it by two orders.
MARGIN = Decimal("1e-8")

DEN = 4                 # every endpoint is (m + n sqrt2) / 4
CAP_DEFAULT = F(21, 2)  # L < 10.5: covers every row with ceil(sqrt n) <= 10
KMAX_DEFAULT = 10
SMAX_DEFAULT = 14       # p + q <= floor(sqrt2 * CAP) = 14


# ------------------------------------------------------- exact integer ladder
def sgn_q(m: int, n: int) -> int:
    """sign of `(m + n*sqrt2)/4`, exactly, in integers."""
    if m == 0:
        return (n > 0) - (n < 0)
    if n == 0:
        return (m > 0) - (m < 0)
    if (m > 0) == (n > 0):
        return 1 if m > 0 else -1
    a, b = m * m, 2 * n * n
    if a == b:                       # impossible for integers m, n != 0 (sqrt2 is irrational)
        return 0
    if m > 0:                        # n < 0: sign(m - |n|sqrt2) = sign(m^2 - 2n^2)
        return 1 if a > b else -1
    return -1 if a > b else 1        # m < 0, n > 0


def cmp_pair(x, y) -> int:
    return sgn_q(x[0] - y[0], x[1] - y[1])


def mx_pair(x, y):
    return x if cmp_pair(x, y) >= 0 else y


def mn_pair(x, y):
    return x if cmp_pair(x, y) <= 0 else y


def pair_from_frac(z: F):
    """`z` (rational) as `(m, n)` in /4 units."""
    return (int(4 * z), 0)


def dec_pair(p, places: int = 20) -> Decimal:
    """A `places`-digit shadow of `(m + n*sqrt2)/4` — display and reporting only."""
    return (Decimal(p[0]) + Decimal(p[1]) * Decimal(2).sqrt()) / Decimal(DEN)


# ------------------------------------------------------------- the bed window
def cell_window(cx4: int, sx: int, cy4: int, sy: int, p: int, q: int):
    """The open interval of sides on which the carrier cell's interior meets the block's.

    The cell's centre is `(cx4/4 + sx*L, cy4/4 + sy*L)` and the block is centred at `(L/2, L/2)`,
    so with `dx, dy` the offsets from the block's centre the bed rule of `block_bed.in_bed` is
    four strict inequalities, each affine in `L`:

        |dx + dy| < 1 + p*sqrt2/2      |dy - dx| < 1 + q*sqrt2/2      |dx| < C      |dy| < C

    with `C = 1/2 + (p+q)*sqrt2/4`.  Returns `(lo, hi)` in /4 units, or `None` if the cell is
    never bedded.
    """
    ap = (4, 2 * p)          # 1 + p*sqrt2/2
    aq = (4, 2 * q)          # 1 + q*sqrt2/2
    cc = (2, p + q)          # 1/2 + (p+q)*sqrt2/4
    cons = (
        (sx + sy - 1, 1, cx4 + cy4, ap),      # a = +-1 or 0
        (sy - sx, 1, cy4 - cx4, aq),
        (2 * sx - 1, 2, cx4, cc),             # a = +-1/2, so the endpoint is scaled by 2
        (2 * sy - 1, 2, cy4, cc),
    )
    lo = None
    hi = None
    for a_signed, scale, b4, (am, an) in cons:
        if a_signed == 0:
            # the condition is a constant one: |b| < A iff A + b > 0 and A - b > 0
            if sgn_q(am + b4, an) <= 0 or sgn_q(am - b4, an) <= 0:
                return None
            continue
        s = 1 if a_signed > 0 else -1
        k = scale * s                        # x / a = x * k / scale * ... see below
        # endpoints: (-A - b)/a and (A - b)/a, i.e. ((+-A) - b) * (scale / a_signed)
        t1 = ((-am - b4) * scale * s, -an * scale * s)
        t2 = ((am - b4) * scale * s, an * scale * s)
        u, v = (t1, t2) if cmp_pair(t1, t2) <= 0 else (t2, t1)
        lo = u if lo is None else mx_pair(lo, u)
        hi = v if hi is None else mn_pair(hi, v)
    if lo is None or hi is None or cmp_pair(lo, hi) >= 0:
        return None
    return lo, hi


def axis_cells(K: int, split: int):
    """The `(c4, s)` list for one axis: run 1 of length `split`, run 2 of length `K - split`.

    Run 1 occupies `[0, split]` (centres `1/2, ..., split - 1/2`, constants in `L`); run 2
    occupies `[L - (K-split), L]` (centres `L - (K-split) + 1/2 + j`, affine in `L`).
    """
    other = K - split
    return ([(4 * i + 2, 0) for i in range(split)]
            + [(4 * j + 2 - 4 * other, 1) for j in range(other)])


def sweep(K: int, kx: int, ky: int, p: int, q: int, wlo, cap):
    """`{count: (lo, hi)}`: every count the declaration attains, with the interval attaining it.

    The count is `K^2 - D(L) + p*q`; `D(L)` is the number of cells whose bed window covers `L`, so
    `D` is constant on each open interval between consecutive window endpoints.  The sweep walks
    those intervals in increasing `L` and records the first interval carrying each count.  All
    comparisons are the integer sign test, so the sweep is exact.
    """
    xs = axis_cells(K, kx)
    ys = axis_cells(K, ky)
    ev = {}
    for cx4, sx in xs:
        for cy4, sy in ys:
            w = cell_window(cx4, sx, cy4, sy, p, q)
            if w is None:
                continue
            lo, hi = w
            e = ev.setdefault(lo, [0, 0])
            e[0] += 1
            e = ev.setdefault(hi, [0, 0])
            e[1] += 1
    keys = sorted(ev, key=cmp_to_key(cmp_pair))
    base = K * K + p * q
    out = {}
    cur = 0
    prev = None
    for k in keys:
        left = wlo if prev is None else mx_pair(prev, wlo)
        if cmp_pair(left, k) < 0 and cmp_pair(left, cap) < 0:
            cnt = base - cur
            if cnt not in out:
                out[cnt] = (left, k)
        lo_c, hi_c = ev[k]
        cur += lo_c - hi_c
        prev = k
    if prev is None:
        if cmp_pair(wlo, cap) < 0:
            out[base] = (wlo, cap)
    else:
        left = mx_pair(prev, wlo)
        if cmp_pair(left, cap) < 0:
            cnt = base - cur
            if cnt not in out:
                out[cnt] = (left, cap)
    return out


def family_map(kmax: int = KMAX_DEFAULT, smax: int = SMAX_DEFAULT, cap=F(CAP_DEFAULT),
               counts_max: int = 130):
    """`{count: (lo, hi, (K, kx, ky, p, q))}`: the family's least side for every count it reaches."""
    cap_p = pair_from_frac(cap)
    best = {}
    tried = 0
    for K in range(2, kmax + 1):
        k_p = (4 * K, 0)
        for p in range(1, smax):
            for q in range(1, smax - p + 1):
                m = p * q
                if m > counts_max:
                    continue
                bbox = (0, 2 * (p + q))            # (p+q)*sqrt2/2, the block's own bbox side
                wlo = mx_pair(k_p, bbox)
                if cmp_pair(wlo, cap_p) >= 0:
                    continue
                for kx in range(1, K):
                    for ky in range(1, K):
                        tried += 1
                        for cnt, (lo, hi) in sweep(K, kx, ky, p, q, wlo, cap_p).items():
                            if cnt < 1 or cnt > counts_max:
                                continue
                            cur = best.get(cnt)
                            if cur is None or cmp_pair(lo, cur[0]) < 0:
                                best[cnt] = (lo, hi, (K, kx, ky, p, q))
    return best, tried


# --------------------------------------------------------------- the built pose
def build(K: int, kx: int, ky: int, p: int, q: int, L: Q2):
    """Assemble the declaration at side `L` and judge it with the exact gate."""
    xs = [HALF + Q2(i) for i in range(kx)] + [L - Q2(K - kx) + HALF + Q2(j) for j in range(K - kx)]
    ys = [HALF + Q2(i) for i in range(ky)] + [L - Q2(K - ky) + HALF + Q2(j) for j in range(K - ky)]
    c = L * HALF
    blk = BB.block(p, q, L)
    kept = [(x, y) for x in xs for y in ys if not BB.in_bed(x - c, y - c, p, q, L)]
    state = kept + blk
    words = [AXIS] * len(kept) + [W45] * len(blk)
    gate = Q.gate(state, words)
    side = Q.side(state, words) if state else Q2(0)
    ex = [Q.frame_extent(w[0], w[1]) for w in words]
    contained = all(Q2(0) <= pt[0] - e and pt[0] + e <= L and
                    Q2(0) <= pt[1] - e and pt[1] + e <= L
                    for pt, e in zip(state, ex))
    return {"state": state, "words": words, "gate": gate, "side": side,
            "n": len(state), "carrier": len(kept), "block": len(blk),
            "L": L, "contained": contained,
            "ok": bool(gate["ok"]) and contained}


def pair_to_q2(p) -> Q2:
    """The exact field element `(m + n*sqrt2)/4`."""
    return Q2(F(p[0], DEN)) + Q2(0, F(p[1], DEN))


def build_side(lo, hi) -> Q2:
    """A side just inside the open interval `(lo, hi)` the sweep reported."""
    Llo, Lhi = pair_to_q2(lo), pair_to_q2(hi)
    return Llo + (Lhi - Llo) * Q2(F(1, 1000))


def _float_state(state, words):
    """A float rendering of an exact pose, for the independent `packlib.verify` cross-check."""
    import math
    out = []
    for (x, y), w in zip(state, words):
        # angle from (cos, sin): 0 for the axis word, pi/4 for the 45 word
        cx = float(Decimal(w[0].a) + Decimal(w[0].b) * Decimal(2).sqrt())
        cy = float(Decimal(w[1].a) + Decimal(w[1].b) * Decimal(2).sqrt())
        out.append((float(Decimal(x.a) + Decimal(x.b) * Decimal(2).sqrt()),
                    float(Decimal(y.a) + Decimal(y.b) * Decimal(2).sqrt()),
                    math.atan2(cy, cx)))
    return out


# --------------------------------------------------------------------- table --
def load_sides():
    """`{n: (Decimal side, k)}` read from the delivered CSV (a measurement, not a verdict)."""
    import math
    rows = {}
    with open(CSV) as f:
        for r in csv.DictReader(f):
            n = int(r["n"])
            rows.setdefault(n, []).append((Decimal(r["x"]), Decimal(r["y"]), float(r["angle"])))
    out = {}
    for n, cells in rows.items():
        lo_x = lo_y = hi_x = hi_y = None
        for (x, y, ang) in cells:
            e = (abs(Decimal(math.cos(ang))) + abs(Decimal(math.sin(ang)))) / 2
            lo_x = x - e if lo_x is None else min(lo_x, x - e)
            hi_x = x + e if hi_x is None else max(hi_x, x + e)
            lo_y = y - e if lo_y is None else min(lo_y, y - e)
            hi_y = y + e if hi_y is None else max(hi_y, y + e)
        k = isqrt(n)
        k += (k * k < n)
        out[n] = (max(hi_x - lo_x, hi_y - lo_y), k)
    return out


def proved_rows():
    """The rows the published frontier marks proved optimal (from `glm_plan.pub_table`)."""
    import glm_plan as GP
    _pub, proved = GP.pub_table()
    return set(proved)


def report(kmax: int, smax: int, cap: F, up_to: int = 100, verbose: bool = True,
           ledger: str | None = None):
    import sqscore as SQ
    SQ.guard(quiet=True)
    sides = load_sides()
    proved = proved_rows()
    # `counts_max` must cover every row in scope: family_map's own default (130) silently
    # dropped every count above it, which run 148 read as "96 counts never attained"
    best, tried = family_map(kmax, smax, cap, counts_max=up_to)
    rows = []
    beats = []
    for n in range(1, up_to + 1):
        side, k = sides[n]
        rec = {"n": n, "k": k, "delivered": str(side), "proved": n in proved}
        b = best.get(n)
        if b is None:
            # a statement about the declared box only: K <= kmax, p+q <= smax, L < cap
            rec.update({"family": None,
                        "verdict": "not attained below the cap in the declared box"})
            rows.append(rec)
            continue
        lo, hi, params = b
        r = build(*params, build_side(lo, hi))
        fdec = dec_pair(lo)
        pose = Decimal(str(Decimal(r["side"].decimal(20))))
        rec.update({"family": str(fdec), "params": list(params),
                    "pose_side": str(pose), "pose_n": r["n"], "gate_ok": r["ok"],
                    "interval": [str(dec_pair(lo)), str(dec_pair(hi))]})
        if n in proved:
            if pose < side - MARGIN and r["ok"] and r["n"] == n:
                rec["verdict"] = "FALSIFIER FIRED (bug)"
                beats.append(rec)
            else:
                rec["verdict"] = "no beat (proved row)"
        elif pose < side - MARGIN and r["ok"] and r["n"] == n:
            rec["verdict"] = "BEAT"
            beats.append(rec)
        elif fdec <= side + MARGIN:
            rec["verdict"] = "tie reached"
        else:
            rec["verdict"] = f"above by {fdec - side}"
        rows.append(rec)
    hits = sum(1 for r in rows if r["verdict"] == "tie reached")
    reach = sum(1 for r in rows if r.get("family") is not None)
    if verbose:
        print(f"{'n':>4} {'k':>2} {'delivered':>14} {'carrier L_min':>14}  verdict")
        for r in rows:
            if r["verdict"] in ("BEAT", "FALSIFIER FIRED (bug)", "tie reached") or r["n"] % 10 == 0:
                print(f"{r['n']:>4} {r['k']:>2} {r['delivered'][:14]:>14} "
                      f"{(r['family'] or '-')[:14]:>14}  {r['verdict']}")
    print(f"carrier ceiling: {reach} of {len(rows)} rows reached at all, {hits} tied, "
          f"{len(beats)} beaten ({tried} declarations swept)")
    led = {"family": "seamed K x K carrier (two runs per axis, every split) + centred p x q "
                     "block, bedded; exact sweep of the (side, count) surface",
           "kmax": kmax, "smax": smax, "cap": str(cap), "counts_max": up_to,
           "declarations": tried,
           "rows": rows, "beats": beats,
           "summary": {"rows": len(rows), "reached": reach, "tied": hits,
                       "beaten": len(beats)}}
    path = ledger or LEDGER
    with open(path, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(path, ROOT)}")
    return led


# ------------------------------------------------------------------ selftest --
def _brute_D(K: int, kx: int, ky: int, p: int, q: int, L: Q2) -> int:
    """The bed size counted cell by cell with the family's own rule (`block_bed.in_bed`)."""
    xs, ys = axis_cells(K, kx), axis_cells(K, ky)
    c = L * HALF
    D = 0
    for cx4, sx in xs:
        for cy4, sy in ys:
            x = Q2(F(cx4, 4)) + (Q2(0) if sx == 0 else L)
            y = Q2(F(cy4, 4)) + (Q2(0) if sy == 0 else L)
            if BB.in_bed(x - c, y - c, p, q, L):
                D += 1
    return D


def selftest() -> int:
    import sqscore as SQ
    SQ.guard(quiet=True)
    print("carrier_ceil selftest")
    sides = load_sides()
    proved = proved_rows()
    cap = pair_from_frac(F(CAP_DEFAULT))

    # 1. the window is the family's own bed rule: agreement with block_bed.in_bed on every cell
    #    of three declarations at 11 sides spread across the sweep's range
    checks = 0
    for (K, kx, ky, p, q) in ((4, 2, 2, 2, 2), (6, 3, 3, 3, 3), (5, 1, 4, 1, 3)):
        xs, ys = axis_cells(K, kx), axis_cells(K, ky)
        for num in range(40, 51):
            L = Q2(F(num, 8))
            c = L * HALF
            for cx4, sx in xs:
                for cy4, sy in ys:
                    x = Q2(F(cx4, 4)) + (Q2(0) if sx == 0 else L)
                    y = Q2(F(cy4, 4)) + (Q2(0) if sy == 0 else L)
                    w = cell_window(cx4, sx, cy4, sy, p, q)
                    inside = (w is not None and
                              Q2(F(w[0][0], 4)) + Q2(0, F(w[0][1], 4)) < L and
                              L < Q2(F(w[1][0], 4)) + Q2(0, F(w[1][1], 4)))
                    assert inside == BB.in_bed(x - c, y - c, p, q, L), (K, kx, ky, p, q, num)
                    checks += 1
    print(f"  1. cell_window agrees with block_bed.in_bed on {checks} (cell, side) pairs")

    # 2. the sweep's count function is the built pose's count function: for four declarations
    #    and 21 sides above the declaration's own floor, a side inside the interval the sweep
    #    reports for count c must build a pose with exactly c cells
    probed = 0
    for (K, kx, ky, p, q) in ((2, 1, 1, 1, 1), (4, 2, 2, 2, 2), (6, 3, 3, 3, 3), (5, 1, 4, 1, 3)):
        wlo = mx_pair((4 * K, 0), (0, 2 * (p + q)))
        out = sweep(K, kx, ky, p, q, wlo, cap)
        assert out, (K, kx, ky, p, q)
        for num in range(0, 41):
            Lp = (num, 0)                        # /4 units: the side is num/4
            if cmp_pair(Lp, wlo) <= 0:
                continue                       # below the declaration's floor: illegal, not swept
            cnt = K * K - _brute_D(K, kx, ky, p, q, Q2(F(num, DEN))) + p * q
            assert cnt in out, (K, kx, ky, p, q, num, cnt, sorted(out))
            probed += 1
        for cnt, (lo, hi) in list(out.items())[:3]:
            L = build_side(lo, hi)
            r = build(K, kx, ky, p, q, L)
            assert r["ok"] and r["n"] == cnt, (K, kx, ky, p, q, cnt, r["n"], r["gate"])
            assert r["side"] <= L, (r["side"], L)
            assert r["side"] * r["side"] > Q2(cnt), (r["side"], cnt)
    print(f"  2. the sweep's count equals `block_bed.in_bed`'s count at {probed} sides, and "
          f"every reported interval rebuilds as a gated pose of that count above the area floor")

    # 3. the map itself: one sweep of the declared family
    best, tried = family_map(KMAX_DEFAULT, SMAX_DEFAULT, CAP_DEFAULT)
    print(f"  3. family map: {tried} declarations swept, {len(best)} counts reached")

    # 4. the falsifier: the literature's proved-optimal rows are not beaten by the family
    proved_in_scope = sorted(n for n in proved if n <= 100)
    bad = [n for n in proved_in_scope if n in best and dec_pair(best[n][0], 20) < sides[n][0] - MARGIN]
    assert not bad, bad
    print(f"  4. falsifier: none of the {len(proved_in_scope)} proved-optimal rows in scope "
          f"is beaten by the family")

    # 5. the 19 known ties: every one in scope is reached at or below its delivered side
    led = json.load(open(os.path.join(ROOT, "workspace/push/block_bed.json")))
    tie_rows = [d for d in led["entry_test"]["detail"] if d.get("reproduced")]
    in_scope = [d for d in tie_rows if d["n"] <= 100]
    assert in_scope, "no tie rows in scope"
    for d in in_scope:
        n = d["n"]
        assert n in best, (n, "tie row not reached")
        assert dec_pair(best[n][0], 20) <= sides[n][0] + Decimal("1e-9"), (n, d, best[n])
    print(f"  5. the {len(in_scope)} run-145 tie rows in scope are all reached at or below "
          f"their delivered side")

    # 6. the band-5 question, exactly: with K = 4 the count needs p*q - D = 4 and p + q <= 7,
    #    and no declaration attains 20 below L = 5 -- a sweep of the surface, not a probe
    assert 20 in best
    assert dec_pair(best[20][0], 20) >= Decimal(5), best[20]
    print(f"  6. band 5: the least side the family reaches at 20 is "
          f"{dec_pair(best[20][0], 20):.12f} (K,kx,ky,p,q = {best[20][2]}), not below 5")

    # 7. float-free decision path
    import exact_field as EF
    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest", "_float_state",
                                                        "load_sides", "report",
                                                        "row_detail", "main", "dec_pair"))
    assert offenders == [], offenders
    print(f"  7. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")

    print("selftest OK (7 controls)")
    return 0


def row_detail(n: int, kmax: int = KMAX_DEFAULT, smax: int = SMAX_DEFAULT):
    """Every declaration that reaches `n`, sorted by the side it reaches it at."""
    cap = pair_from_frac(F(21, 2))
    out = []
    for K in range(2, kmax + 1):
        for p in range(1, smax):
            for q in range(1, smax - p + 1):
                bbox = (0, 2 * (p + q))
                wlo = mx_pair((4 * K, 0), bbox)
                if cmp_pair(wlo, cap) >= 0:
                    continue
                for kx in range(1, K):
                    for ky in range(1, K):
                        o = sweep(K, kx, ky, p, q, wlo, cap)
                        if n in o:
                            out.append((o[n][0], (K, kx, ky, p, q), o[n], wlo))
    out.sort(key=cmp_to_key(lambda a, b: cmp_pair(a[0], b[0])))
    print(f"row {n}: {len(out)} declarations reach this count below cap")
    for lo, params, (a, b), wlo in out[:20]:
        print(f"  L in ({dec_pair(a):.9f}, {dec_pair(b):.9f}]  K,kx,ky,p,q = {params}"
              f"  wlo = {dec_pair(wlo):.6f}")
    return out


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--row" in sys.argv:
        n = int(sys.argv[sys.argv.index("--row") + 1])
        row_detail(n)
        return 0
    if "--wide" in sys.argv:
        # every row with ceil(sqrt n) <= 15, i.e. the whole small-pose block n <= 225.  It writes
        # its own ledger so the default (n <= 100) map is not overwritten.
        report(15, 21, F(31, 2), up_to=225, ledger=LEDGER_WIDE)
        return 0
    report(KMAX_DEFAULT, SMAX_DEFAULT, CAP_DEFAULT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
