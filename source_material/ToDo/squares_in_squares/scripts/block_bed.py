#!/usr/bin/env python3
r"""block_bed.py — the block-bedded carrier: a seamed grid whose runs are disjoint by law (Run 145).

Run 144 (`seam_carrier.py`, doc 101) built a sparse carrier and refused it, and the refusal
was exact: the carrier was the product of two axis runs slid together by an interlock `o`, the
notch only removed the cells a *bar* covered, and so the carrier had no authority over
carrier-carrier overlap -- 28 rows reached the delivered side and count and were refused by the
gate because two of the carrier's own runs overlapped.  Doc 101 §6 names the cure: a carrier
that is sparse **by construction**, its translates disjoint by a law rather than by a drop rule.

THE LAW.  Each axis carries two runs separated by a **positive gap**, not an interlock:

    run 1 on an axis:  centres 1/2, 3/2, ..., kx - 1/2                (occupies [0, kx])
    run 2 on an axis:  centres L - ky + 1/2, ..., L - 1/2             (occupies [L-ky, L])
    K                  = kx + ky,     g = L - K > 0                   (the seam gap)

and the carrier is `X x Y` with `X` the runs on x and `Y` the runs on y -- the two axes' splits
are independent (`kx` and `ky` may differ), because nothing in the problem makes the pose
x-y symmetric and the delivered poses are not.  Every cell is on one unit lattice, and any two
are separated by at least `g` on one axis (different runs) or by exactly `0` (adjacent in one
run, an exact contact).  So *carrier-carrier overlap is impossible by arithmetic*: there is no
interlock parameter to search, no pair to test, and nothing for a notch to repair -- for any
`g > 0` and any split.  The seam's gap may be any positive number, which is what lets the box
take the delivered irrational sides `L = a + (s/2)*sqrt 2` while the cells stay on the integers.

THE BLOCK.  The tilted class is not a one-cell-wide bar (run 144's `m` diamonds in a chain) but
a **p x q block**: the closed rectangle R of side p and q whose edge normals are
`+- (sqrt2/2, +- sqrt2/2)`, centred at `(L/2, L/2)`.  Its cells are the product of p and q
translates by `(sqrt2/2, sqrt2/2)` and `(sqrt2/2, -sqrt2/2)`, so R is exactly their union and
its half-extents are `p/2` and `q/2` in the block's own frame.

THE BED (the only insertion rule).  A carrier cell is **dropped iff its interior meets R's
interior** -- the block cuts its own bed out of the grid, and nothing else is removed and nothing
is moved.  Because R *is* the union of the block's cells, this is the same predicate the gate
applies pair by pair, decided in one shot by the four exact SAT inequalities against R; control
7 checks that the two agree cell by cell.

COUNT AND SIDE.  The side is written in closed form, `L = a + (s/2)*sqrt 2` with `a >= 1` and
`1 <= s <= 30`; the carrier spans exactly `[0, L]^2` (run 1 from 0, run 2 to L), so the box is
the carrier's own bbox.  The count is `n = K^2 - dropped + p*q`, read off the assembled pose,
never assumed.

WHAT MAKES IT SPARSE.  The carrier has two translation domains per axis (the two run residues),
so four in the plane; its fill is `(K^2 - dropped)/L^2 < 1`; and its disjointness is the law
above, not a rule applied to overlapping cells.

EXACTNESS.  Every coordinate, extent and slack is `a + b*sqrt 2` with `a, b` in Q
(`exact_field.Quad`, `qsqrt2.Q2`), the judge is `qsqrt2.gate` (signs, never tolerances), and the
module names no `float` in any decision function (bytecode audit, control 8).

THE ENTRY TEST (doc 99 §9, doc 100 §8, doc 101 §6).  Before any sweep, the family must reproduce
the delivered `(n, side)` pair of at least 20 of the 110 two-class beating rows, with 0 overlaps
under the exact gate.  A row's declaration search is over `K`, the two run splits `kx`, `ky`, and
the block shape `p x q` with `p*q` equal to the row's delivered tilted-class size (the *hint*
bounds which declarations are tried; it never decides legality).  If the family cannot reach 20
the run records the refusal and the measured reason instead of a sweep.

    python3 scripts/block_bed.py              # entry test, writes the ledger
    python3 scripts/block_bed.py --selftest    # 10 controls
"""
from __future__ import annotations

import bisect
import json
import os
import sys
from decimal import Decimal, getcontext, ROUND_FLOOR
from fractions import Fraction as F
from math import isqrt

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import qsqrt2 as Q                              # noqa: E402  (exact Q(sqrt 2) gate)
import sqscore as SQ                            # noqa: E402
from qsqrt2 import Q2, HALF                     # noqa: E402

LEDGER = os.path.join(ROOT, "workspace/push/block_bed.json")

W = Q2(0, F(1, 2))          # sqrt 2 / 2: the 45-degree cell's own half-extent
AXIS = Q.AXIS
W45 = Q.word_45()

MAX_K = 34                  # grid positions per axis
MAX_SEAM = 30               # s in L = a + (s/2) sqrt 2
MAX_M = 330                 # p*q: the largest delivered tilted class is 324


# ------------------------------------------------------------------ the family
def side_law(a: int, s: int) -> Q2:
    """The declared side `a + (s/2)*sqrt 2`."""
    return Q2(a) + Q2(0, F(s, 2))


def runs(a: int, s: int, K: int, k: int):
    """(positions, L, g): the two runs on one axis, the side, and the seam gap.

    Run 1 occupies `[0, k]` and run 2 `[L-(K-k), L]`, so the two are separated by the gap
    `g = L - K` on *both* axes.  `positions` is sorted, run 1 first.
    """
    L = side_law(a, s)
    k2 = K - k
    xs = [HALF + Q2(i) for i in range(k)]
    xs += [L - Q2(k2) + HALF + Q2(i) for i in range(k2)]
    return xs, L, L - Q2(K)


def block(p: int, q: int, L: Q2) -> list[tuple[Q2, Q2]]:
    """The tilted block: p x q cells centred at (L/2, L/2), edge normals (1,1) and (1,-1)."""
    c = L * HALF
    out = []
    for i in range(p):
        for j in range(q):
            # + (i - (p-1)/2) * (sqrt2/2, sqrt2/2) + (j - (q-1)/2) * (sqrt2/2, -sqrt2/2)
            du = F(2 * i - (p - 1), 4)
            dv = F(2 * j - (q - 1), 4)
            out.append((c + Q2(0, du + dv), c + Q2(0, du - dv)))
    return out


def beds(p: int, q: int, L: Q2):
    """The four exact half-widths of the bed, in the two frames the SAT test needs.

    `A, B` are the half-extents of R in its own frame plus the axis cell's `W`; `C` is the
    half-extent of R along an axis plus the cell's `1/2`.  A cell whose centre offset is
    `(dx, dy)` lies inside the bed iff all four of `|u| < A`, `|v| < B`, `|dx| < C`,
    `|dy| < C` hold, with `u = (dx+dy)W`, `v = (dy-dx)W` -- the exact SAT of the cell
    against the whole block R, decided once instead of against each of its cells.
    """
    A = Q2(p) * HALF + W
    B = Q2(q) * HALF + W
    C = HALF + Q2(0, F(p + q, 4))
    return A, B, C


def in_bed(dx: Q2, dy: Q2, p: int, q: int, L: Q2) -> bool:
    """The insertion rule: True iff the cell's interior meets the block's interior."""
    A, B, C = beds(p, q, L)
    u = (dx + dy) * W
    v = (dy - dx) * W
    return abs(u) < A and abs(v) < B and abs(dx) < C and abs(dy) < C


def dy_window(dx: Q2, p: int, q: int, L: Q2):
    """The open interval of `dy` at which a cell with offset `dx` is in the bed.

    Each of the four SAT inequalities is an interval in `dy` once `dx` is fixed, and the bed
    is convex, so the window is the intersection.  `|u| < A` becomes
    `|dx + dy| < A*sqrt2 = 1 + p*sqrt2/2`, and `|v| < B` becomes `|dy - dx| < 1 + q*sqrt2/2`.
    The window is in *offsets* from the centre; the counters below shift it by `L/2`.
    """
    A, B, C = beds(p, q, L)
    ap = Q2(1, F(p, 2))                     # A * sqrt 2
    bp = Q2(1, F(q, 2))                     # B * sqrt 2
    lo = max(-dx - ap, dx - bp, -C)
    hi = min(-dx + ap, dx + bp, C)
    return lo, hi


def bed_profile(a: int, s: int, K: int, kx: int, p: int, q: int):
    """(windows, L, g): the bed's `dy` window for each x of one axis.

    The windows do not depend on the *y* split, so the search computes them once per
    `(K, kx)` and counts against every `ky` by bisection -- the count of a declaration whose
    y-axis is different is a bisection away, not a fresh scan.
    """
    xs, L, g = runs(a, s, K, kx)
    c = L * HALF
    return [dy_window(x - c, p, q, L) for x in xs], L, g


def split_counts(windows, L: Q2, K: int):
    """(ca, cb, D): the bed size for every y split, from the x windows alone.

    The y positions a split can use are always drawn from the two full families
    `0.5 + i` (run 1) and `L - K + 0.5 + j` (run 2), so the number of x windows containing
    each of those `2K` positions decides the bed for *every* split at once:
    `D(ky) = sum(ca[:ky]) + sum(cb[:K-ky])`.  That is the whole reason the two axes' splits
    can be searched independently at a cost of one pass, not one pass per split.
    """
    A = [HALF + Q2(i) for i in range(K)]
    B = [L - Q2(K) + HALF + Q2(i) for i in range(K)]
    ca = [sum(1 for lo, hi in windows if lo < y < hi) for y in A]
    cb = [sum(1 for lo, hi in windows if lo < y < hi) for y in B]
    pa = [0]
    for v in ca:
        pa.append(pa[-1] + v)
    pb = [0]
    for v in cb:
        pb.append(pb[-1] + v)
    return {ky: pa[ky] + pb[K - ky] for ky in range(1, K)}


def count_windows(windows, ys, L: Q2) -> int:
    """The number of (x, y) cell pairs inside the bed, given the x windows and the y positions."""
    c = L * HALF
    D = 0
    for lo, hi in windows:
        if lo < hi:
            D += bisect.bisect_left(ys, c + hi) - bisect.bisect_right(ys, c + lo)
    return D


def bed_count(a: int, s: int, K: int, kx: int, ky: int, p: int, q: int):
    """(posed, D, L): the number of cells the block removes.

    This is the counter, not a decision procedure: `assemble` builds the same set cell by
    cell, and control 9 asserts the two agree on every declaration it is tried on.
    """
    windows, L, g = bed_profile(a, s, K, kx, p, q)
    if g <= Q2(0):
        return False, 0, L
    ys, _L, _g = runs(a, s, K, ky)
    return True, count_windows(windows, ys, L), L


def assemble(a: int, s: int, K: int, kx: int, ky: int, p: int, q: int):
    """The declared pose: (kept carrier cells, block cells, L, dropped count, g).

    The declaration is generated from `(a, s, K, kx, ky, p, q)` alone.  The insertion rule is
    the bed: every carrier cell whose interior meets the block is dropped, so the block cuts
    its own bed and nothing else is removed.
    """
    xs, L, g = runs(a, s, K, kx)
    ys, _L, _g = runs(a, s, K, ky)
    c = L * HALF
    blk = block(p, q, L)
    kept = []
    dropped = 0
    for x in xs:
        for y in ys:
            if in_bed(x - c, y - c, p, q, L):
                dropped += 1
            else:
                kept.append((x, y))
    return kept, blk, L, dropped, g


def check(a: int, s: int, K: int, kx: int, ky: int, p: int, q: int,
          stop: bool = False) -> dict:
    """Assemble, gate exactly, and report the family's numbers for a declaration.

    This is the only legality decision in the module: `qsqrt2.gate` on the rebuilt pose, no
    pre-filter and no second predicate.  `ok` also requires the pose to fill its declared box
    (`L_pose == L`) and every cell to be inside it: a declaration whose block eats a whole run
    would otherwise report a smaller box than it declares.
    """
    kept, blk, L, dropped, g = assemble(a, s, K, kx, ky, p, q)
    state = kept + blk
    words = [AXIS] * len(kept) + [W45] * len(blk)
    gate = Q.gate(state, words, stop=stop)
    ex = [Q.frame_extent(*w) for w in words]
    contained = all(Q2(0) <= pt[0] - e and pt[0] + e <= L and
                    Q2(0) <= pt[1] - e and pt[1] + e <= L
                    for pt, e in zip(state, ex))
    L_pose = Q.side(state, words) if state else Q2(0)
    span = L_pose == L
    return {"a": a, "s": s, "K": K, "kx": kx, "ky": ky, "p": p, "q": q, "g": g,
            "L": L, "L_pose": L_pose, "n": len(state), "dropped": dropped,
            "carrier": len(kept), "block": len(blk), "gate": gate,
            "contained": contained, "span": span,
            "ok": bool(gate["ok"]) and contained and span,
            "state": state, "words": words}


def domains(state, words) -> dict:
    """Translation domains per class, at a 1e-9 shadow of the exact coordinates (display)."""
    out = {}
    for tag, word in (("axis", AXIS), ("tilt", W45)):
        sub = [pt for pt, w in zip(state, words) if w == word]
        if not sub:
            out[tag] = 0
            continue
        c, s = word
        keys = set()
        for (x, y) in sub:
            u = x * c + y * s
            v = Q2(0) - x * s + y * c
            keys.add((_frac9(u), _frac9(v)))
        out[tag] = len(keys)
    return out


def _shadow(z: Q2) -> Decimal:
    """A 60-digit Decimal shadow of a field element (display and index windows only)."""
    return (Decimal(z.a.numerator) / Decimal(z.a.denominator)
            + Decimal(z.b.numerator) / Decimal(z.b.denominator) * Decimal(2).sqrt())


def _frac9(z: Q2) -> int:
    """`z mod 1`, quantised at 1e-9 through a 60-digit Decimal shadow."""
    d = _shadow(z)
    frac = d - d.to_integral_value(rounding=ROUND_FLOOR)
    return int((frac / Decimal("1e-9")).to_integral_value())


# --------------------------------------------------------------- entry test ---
def two_class_rows() -> list[tuple[int, Decimal, int, int]]:
    """(n, delivered side, grid k, tilted-class size) for the 110 two-class rows.

    The tilted-class size is a *search hint*: it says which block shapes `p x q` to try
    (`p*q` equal to it).  Every reproduction is a pose rebuilt from the declaration and judged
    by the exact gate, so the hint cannot manufacture one.
    """
    led = json.load(open(os.path.join(ROOT, "workspace/push/tilt_audit.json")))
    out = []
    for key, r in led["rows"].items():
        if not (r["beat"] and r["classes"] == 2):
            continue
        if "cls" in r:
            tilt = max(r["cls"], key=lambda c: F(c["x"]))
            out.append((int(key), Decimal(r["side"]), r["grid"], tilt["m"]))
        else:
            out.append((int(key), Decimal(r["side"]), r["grid"],
                        max(r.get("class_sizes", [1]))))
    return sorted(out)


def exact_side(dec: Decimal):
    """(L, a, s) for a delivered side `a + (s/2)*sqrt2`, or None.

    The parameters are read off the decimal and then *verified* exactly in Q(sqrt2) to 1e-8.
    This is only a parameterisation step; every verdict below is the exact gate on a rebuilt
    pose.  Rows whose side is not of this form cannot be reached by the family at all, and are
    counted separately.
    """
    for s in range(1, MAX_SEAM + 1):
        rest = dec - Decimal(s) * _shadow(W)
        for a in (int(rest), int(rest) + 1):
            if a < 1:
                continue
            L = side_law(a, s)
            if abs(_shadow(L) - dec) <= Decimal("1e-8"):
                return L, a, s
    return None


def shapes(m: int) -> list[tuple[int, int]]:
    """Every block shape p x q with p*q = m (both orientations)."""
    return [(p, m // p) for p in range(1, m + 1) if m % p == 0]


def _count_floor(n: int, m: int) -> int:
    """ceil(sqrt(n - m)): the smallest `K` whose bed can still hold the count.

    `n = K^2 - D + m` with `D >= 0` forces `K^2 >= n - m`; the bound is integer arithmetic
    and exact, and it is what keeps the declaration search to a handful of grid sizes.
    """
    lo = isqrt(max(0, n - m))
    while lo * lo < n - m:
        lo += 1
    return lo


def entry_test(verbose: bool = True) -> dict:
    """Doc 99 §9's gate: reproduce >= 20 of the 110 delivered (n, side) pairs.

    A row counts only when a declaration builds a pose with exactly that count, exactly that
    side, and no overlap under the exact gate.  The search is over the grid size `K`, the two
    run splits `kx` and `ky`, and the block shape `p x q`; `K` is pruned from below by
    `K^2 >= n - p*q` (the bed cannot have a negative size), which is exact.
    """
    rows = two_class_rows()
    detail = []
    hits = 0
    for n, dec, k, m in rows:
        got = exact_side(dec)
        rec = {"n": n, "target": str(dec), "grid": k, "m_hint": m,
               "exact": got is not None, "count_matched": False, "refused": 0}
        if got is None:
            rec.update({"reproduced": False, "why": "side is not a + (s/2)sqrt2"})
            detail.append(rec)
            continue
        L, a, s = got
        rec["target"] = str(L)
        rec["a"], rec["s"] = a, s
        solved = None
        refused = counted = 0
        pts = [(p, q) for p, q in shapes(m)
               if Q2(0, F(p + q, 2)) <= L]      # the block's bbox must fit the box
        k_lo = min([max(2, _count_floor(n, p * q)) for p, q in pts] or [2])
        for K in range(k_lo, min(MAX_K, Q.floor_q2(L)) + 1):
            if solved:
                break
            if L - Q2(K) <= Q2(0):
                continue
            axes = {k: runs(a, s, K, k)[0] for k in range(1, K)}   # both splits, built once
            for p, q in pts:
                if solved:
                    break
                if max(2, _count_floor(n, p * q)) > K:
                    continue
                c = L * HALF
                for kx in range(1, K):
                    if solved:
                        break
                    wins = [dy_window(x - c, p, q, L) for x in axes[kx]]
                    Ds = split_counts(wins, L, K)
                    for ky in [kx] + [k for k in range(1, K) if k != kx]:
                        if K * K - Ds[ky] + p * q != n:
                            continue
                        counted += 1
                        r = check(a, s, K, kx, ky, p, q, stop=True)
                        if r["ok"]:
                            solved = ((K, kx, ky, p, q), r)
                            break
                        refused += 1
        if solved is None:
            rec.update({"reproduced": False,
                        "why": "count matched, gate refused" if counted else
                               "no declaration reaches this count",
                        "count_matched": bool(counted), "refused": refused})
        else:
            (K, kx, ky, p, q), r = solved
            rec.update({"reproduced": True, "params": [K, kx, ky, p, q],
                        "count_matched": True,
                        "family_L": str(r["L"]), "family_n": r["n"],
                        "dropped": r["dropped"], "carrier": r["carrier"],
                        "contacts": r["gate"]["contacts"]})
            hits += 1
        detail.append(rec)
        if verbose and (rec["reproduced"] or len(detail) % 25 == 0):
            print(f"  n={n:>4} reproduced={rec['reproduced']} "
                  f"{rec.get('params', '')} {rec.get('why', '')}")
    res = {"rows": len(rows), "reproduced": hits, "threshold": 20,
           "passes": hits >= 20, "max_k": MAX_K, "max_seam": MAX_SEAM, "max_m": MAX_M,
           "exact_rows": sum(1 for d in detail if d["exact"]),
           "count_matched": sum(1 for d in detail if d.get("count_matched")),
           "refused": sum(1 for d in detail if d.get("refused")),
           "detail": detail}
    print(f"entry test: {hits}/{len(rows)} two-class rows reproduced "
          f"(threshold 20, {res['exact_rows']} sides exact in Q(sqrt2), "
          f"{res['count_matched']} rows matched a count) -> "
          f"{'PASS' if res['passes'] else 'FAIL'}")
    return res


# -------------------------------------------------------------------- report --
def main() -> int:
    import sqscore as _SQ
    globals()["SQ"] = _SQ
    getcontext().prec = 60
    SQ.guard(quiet=True)
    print("block_bed — seamed grid with a centred tilted block, Q(sqrt 2)")
    res = entry_test()
    led = {"family": "seamed K x K grid (independent x/y splits) + centred p x q block, bedded",
           "gap_law": "g = L - K > 0 on both axes; runs disjoint by arithmetic",
           "max_k": MAX_K, "max_seam": MAX_SEAM, "max_m": MAX_M, "entry_test": res}
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}")
    return 0


# ------------------------------------------------------------------ selftest --
def selftest() -> int:
    import sqscore as _SQ
    globals()["SQ"] = _SQ
    getcontext().prec = 60
    print("block_bed selftest")

    # 1. the law: the two runs are separated by exactly g > 0, adjacent cells touch, and the
    #    carrier on its own is legal for every gap and every x/y split -- disjointness is
    #    arithmetic, not a search, and it survives the axes being split differently
    for (a, s, K, kx, ky) in ((2, 1, 2, 1, 1), (5, 5, 8, 4, 4), (5, 5, 8, 1, 7),
                              (6, 8, 10, 3, 7), (4, 4, 6, 3, 2)):
        xs, L, g = runs(a, s, K, kx)
        ys, _L, _g = runs(a, s, K, ky)
        assert g > Q2(0), (a, s, K, kx, g)
        for w, kw in ((xs, kx), (ys, ky)):
            base, top = w[:kw], w[kw:]
            sep = min(t - b for t in top for b in base) - Q2(1)
            assert sep == g, (sep, g)
            adj = [w[i + 1] - w[i] for i in range(len(w) - 1)]
            assert all(d == Q2(1) for i, d in enumerate(adj) if i != kw - 1)
            assert adj[kw - 1] == Q2(1) + g, adj[kw - 1]
        state = [(x, y) for x in xs for y in ys]
        gr = Q.gate(state, [AXIS] * len(state))
        assert gr["ok"] and gr["violations"] == 0, gr
        print(f"  1.{a}.{s}.{K}.{kx}.{ky} gap g = {g} > 0 on both axes, cells within a run "
              f"touch, carrier alone gates ok ({len(state)} cells, {gr['contacts']} contacts)")

    # 2. the bed is load-bearing: keeping the dropped cells makes the gate refuse
    for (a, s, K, kx, ky, p, q) in ((5, 5, 8, 4, 4, 5, 5), (6, 8, 10, 5, 5, 8, 8),
                                    (5, 5, 8, 1, 7, 5, 5)):
        kept, blk, L, dropped, g = assemble(a, s, K, kx, ky, p, q)
        assert dropped > 0, (a, s, K, kx, ky, p, q)
        xs, _L, _g = runs(a, s, K, kx)
        ys, _L, _g = runs(a, s, K, ky)
        full = [(x, y) for x in xs for y in ys]
        bad = Q.gate(full + blk, [AXIS] * len(full) + [W45] * len(blk), stop=True)
        assert not bad["ok"], (a, s, K, kx, ky, p, q)
        print(f"  2.{a}.{s}.{K}.{kx}.{ky}.{p}x{q} the block removes {dropped} cells; keeping "
              f"them is refused by the gate ({bad['violations']} overlapping pair(s))")

    # 3. the atom: n = 5 at 2 + (1/2)sqrt2 from four cells and one diamond
    r = check(2, 1, 2, 1, 1, 1, 1)
    assert r["n"] == 5 and r["L"] == Q2(2) + W and r["ok"], (r["n"], r["L"], r["gate"])
    assert r["gate"]["contacts"] >= 1
    print(f"  3. (a,s,K,kx,ky,p,q) = (2,1,2,1,1,1,1): n = 5, L = {r['L']} = 2+√2/2, "
          f"0 overlaps, {r['gate']['contacts']} exact contacts")

    # 4. the side is the contact side: one part in 1e9 below it the gate refuses
    st, ws, L = r["state"], r["words"], r["L"]
    short = [(x * (L - Q2(F(1, 10 ** 9))) / L, y * (L - Q2(F(1, 10 ** 9))) / L)
             for x, y in st]
    assert not Q.gate(short, ws)["ok"], "a shrunken box must be refused"
    print("  4. shrinking that box by 1e-9 of side is refused by the exact gate")

    # 5. sparseness: fill < 1 and two translation domains per axis (four in the plane)
    for (a, s, K, kx, ky, p, q) in ((2, 1, 2, 1, 1, 1, 1), (4, 4, 6, 3, 3, 4, 4),
                                    (5, 5, 8, 4, 4, 5, 5), (6, 8, 10, 5, 5, 8, 8),
                                    (5, 5, 8, 1, 7, 5, 5)):
        r = check(a, s, K, kx, ky, p, q)
        fill = Q2(r["n"]) / (r["L"] * r["L"])
        car = Q2(r["carrier"]) / (r["L"] * r["L"])
        dom = domains(r["state"], r["words"])
        assert fill < Q2(1) and car < Q2(1), (a, s, K, kx, ky, p, q, fill, car)
        assert dom["axis"] == 4 and dom["tilt"] == 1, dom
        print(f"  5.{a}.{s}.{K}.{kx}.{ky}.{p}x{q} n = {r['n']}, fill = {fill.decimal(4)} < 1 "
              f"(carrier {car.decimal(4)}), domains axis {dom['axis']} / tilt {dom['tilt']}")

    # 6. containment, the span, and the family's own refusal of a block that leaves its box
    for (a, s, K, kx, ky, p, q) in ((2, 1, 2, 1, 1, 1, 1), (4, 4, 6, 3, 3, 4, 4),
                                    (5, 5, 8, 4, 4, 5, 5), (5, 5, 8, 1, 7, 5, 5)):
        r = check(a, s, K, kx, ky, p, q)
        assert r["contained"] and r["span"] and r["ok"], (a, s, K, kx, ky, p, q, r["gate"])
        print(f"  6.{a}.{s}.{K}.{kx}.{ky}.{p}x{q} n = {r['n']}, L = {r['L']}, every cell "
              f"inside the box and the pose fills it exactly")
    big = check(2, 1, 2, 1, 1, 4, 4)          # a block far too large for a 2.7 box
    assert not big["ok"] and (not big["contained"] or not big["span"]), big["gate"]
    print(f"  6.refusal (2,1,2,1,1,4x4) is refused by the family: contained = "
          f"{big['contained']}, span = {big['span']}")

    # 7. the bed rule *is* the gate's pairwise predicate: dropped cells are exactly the cells
    #    some block cell is refused against, and kept cells are exactly those none refuses
    for (a, s, K, kx, ky, p, q) in ((5, 5, 8, 4, 4, 5, 5), (6, 8, 10, 5, 5, 8, 8),
                                    (4, 4, 6, 3, 3, 4, 4), (5, 5, 8, 1, 7, 5, 5)):
        xs, L, g = runs(a, s, K, kx)
        ys, _L, _g = runs(a, s, K, ky)
        c = L * HALF
        blk = block(p, q, L)
        bad = 0
        for x in xs:
            for y in ys:
                cell = (x, y)
                hit = any(not Q.gate([cell, b], [AXIS, W45])["ok"] for b in blk)
                assert hit == in_bed(x - c, y - c, p, q, L), (a, s, K, kx, ky, p, q, cell)
                bad += hit
        _k, _b, _L, dropped, _g = assemble(a, s, K, kx, ky, p, q)
        assert bad == dropped, (bad, dropped)
        print(f"  7.{a}.{s}.{K}.{kx}.{ky}.{p}x{q} the bed rule agrees with the raw gate on all "
              f"{K * K} cells ({dropped} dropped)")

    # 8. float-free decision path
    import exact_field as EF
    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  8. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")

    # 9. one counter, one gate: `bed_count` agrees with `assemble`, and `check` reports
    #    exactly the raw gate's verdict
    for (a, s, K, kx, ky, p, q) in ((2, 1, 2, 1, 1, 1, 1), (4, 4, 6, 3, 3, 4, 4),
                                    (5, 5, 8, 4, 4, 5, 5), (6, 8, 10, 5, 5, 8, 8),
                                    (5, 5, 8, 1, 7, 5, 5), (2, 1, 2, 1, 1, 4, 4)):
        posed, D, L = bed_count(a, s, K, kx, ky, p, q)
        kept, blk, L2, dropped, g = assemble(a, s, K, kx, ky, p, q)
        assert posed and L == L2 and D == dropped and len(kept) == K * K - D, \
            (a, s, K, kx, ky, p, q, D, dropped)
        r = check(a, s, K, kx, ky, p, q)
        raw = Q.gate(kept + blk, [AXIS] * len(kept) + [W45] * len(blk))
        assert r["ok"] == (bool(raw["ok"]) and r["contained"] and r["span"]), \
            (a, s, K, kx, ky, p, q)
        print(f"  9.{a}.{s}.{K}.{kx}.{ky}.{p}x{q} counter D = {D} = assemble's drops, "
              f"check ok = {r['ok']} = the raw gate's verdict")

    # 10. the family rebuilds the delivered pose, not merely its numbers: for three rows the
    #     built pose equals the CSV's pose up to translation and the square's symmetries
    import tilt_audit as TA
    poses = TA.load_poses()
    for n, params in ((5, (2, 1, 2, 1, 1, 1, 1)), (65, (5, 5, 8, 4, 4, 5, 5)),
                      (124, (6, 8, 10, 5, 5, 8, 8))):
        r = check(*params)
        assert r["n"] == n, (n, r["n"])
        want = [(Decimal(x), Decimal(y)) for x, y, _ang in poses[n]]
        got = [(_shadow(x), _shadow(y)) for x, y in r["state"]]
        if not _pose_equal(got, want, r["L"]):
            raise AssertionError(f"n = {n}: the built pose is not the delivered pose")
        print(f"  10.n={n} {params}: the built pose is the delivered pose up to symmetry")

    print("selftest OK (10 controls)")
    return 0


def _pose_equal(got, want, L: Q2, tol: str = "1e-6") -> bool:
    """Pose identity up to translation and the square's eight symmetries (display shadow).

    Both sets are compared as multisets of centres normalised to the lower-left corner, under
    the four rotations and the four reflections of the box.  This is a *display* comparison
    (1e-6 on a 60-digit shadow), never a verdict: the verdicts in this module are exact.
    """
    t = Decimal(tol)
    sides = _shadow(L)

    def norm(pts):
        mx = min(p[0] for p in pts)
        my = min(p[1] for p in pts)
        return [(p[0] - mx, p[1] - my) for p in pts]

    a = norm(got)
    b = norm(want)
    for k in range(4):
        for flip in (False, True):
            cand = []
            for (x, y) in a:
                for _ in range(k):
                    x, y = sides - y, x
                if flip:
                    x = sides - x
                cand.append((x, y))
            cc = sorted(norm(cand))
            if len(cc) == len(b):
                if all(abs(u[0] - v[0]) < t and abs(u[1] - v[1]) < t
                       for u, v in zip(cc, sorted(b))):
                    return True
    return False


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
