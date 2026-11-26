#!/usr/bin/env python3
r"""block_bed_r.py — the r-run block-bedded carrier: more translates per axis (Run 147).

Run 145's carrier (`block_bed.py`, doc 102) splits each axis into **two** runs anchored at the
two faces of the box: run 1 occupies `[0, kx]`, run 2 `[L - ky, L]`, and the seam gap
`g = L - K > 0` is what makes the two disjoint by arithmetic.  All 19 of its reproductions sit
at the symmetric split `kx = ky = K/2`.  The question this module answers is whether **more**
runs per axis — more translate domains for the same count — buy any reach.

THE FAMILY.  Each axis carries `r` **equal** runs of `u = K/r` unit cells with `r - 1` equal
gaps:

    gap  g = (L - K) / (r - 1)
    run J:  starts at J*(u + g), centres start + 1/2, ..., start + u - 1/2   (J = 0..r-1)

so run 0 begins at the face `x = 0` and run `r-1` ends at the face `x = L`: the carrier still
spans exactly `[0, L]` and the box is still the carrier's own bbox.  Any two cells on one axis
are separated by exactly `0` (adjacent in a run) or by `g > 0` (different runs), so
carrier-carrier overlap is still impossible by arithmetic, and the gap stays a free exact
number — which is what lets the box take the delivered irrational sides while the block cells
stay in `Q(sqrt 2)`.  `r = 2` is *exactly* run 145's symmetric split (`kx = ky = K/2`): control
1 asserts the positions and the gap agree with `block_bed.runs` element for element.

The two axes may carry different run counts (`rx`, `ry`), because nothing makes the pose x-y
symmetric and the delivered poses are not.

COUNT AND SIDE.  The side is the same closed law `L = a + (s/2)sqrt2`; the count is
`n = K^2 - D + p*q`, where `D` is the number of carrier cells the centred tilted block beds out.
`D` is counted *analytically* (a window per x cell, bisection over the y positions, exactly as
run 145's `split_counts` does), and — the discipline run 146's audit asked for — that count is
cross-checked against `assemble_r`, which builds the same set cell by cell and drops every cell
whose interior meets the block's interior.  Control 3 asserts the two agree on every declaration
it is tried on, and **no pose is accepted unless its own count equals the row's** (`r["ok"] and
r["n"] == n`), not merely because the gate passed.

    python3 scripts/block_bed_r.py             # entry test: r = 2..6, writes the ledger
    python3 scripts/block_bed_r.py --beat      # the beat probe over the same family
    python3 scripts/block_bed_r.py --beat --control   # r = 2 re-finds run 145's ties
    python3 scripts/block_bed_r.py --selftest  # 6 controls
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F
from functools import lru_cache

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import qsqrt2 as Q                              # noqa: E402  (exact Q(sqrt 2) gate)
import block_bed as B                           # noqa: E402  (side law, bed, block, rows)
import beat_probe as BP                         # noqa: E402  (the probe's side grid and rules)
import sqscore as SQ                            # noqa: E402

from qsqrt2 import Q2, HALF                     # noqa: E402

LEDGER = os.path.join(ROOT, "workspace/push/block_bed_r.json")
BED_LEDGER = os.path.join(ROOT, "workspace/push/block_bed.json")
BEAT_LEDGER = os.path.join(ROOT, "workspace/push/block_bed_r_beat.json")

MAX_R = 6                                       # runs per axis, inclusive
AXIS = B.AXIS
W45 = B.W45


# ------------------------------------------------------------------ the family
@lru_cache(maxsize=None)
def _runs_cached(a: int, s: int, K: int, r: int):
    return runs_r(a, s, K, r)


def runs_r(a: int, s: int, K: int, r: int):
    """(positions, L, g): r equal runs of `K/r` cells with `r-1` equal gaps, spanning [0, L].

    Returns None when the declaration does not exist: `r >= 2`, `r | K`, and the seam gap
    `(L - K)/(r - 1)` must be positive.  `r = 2` is run 145's symmetric split exactly.
    """
    if r < 2 or r > MAX_R or K % r or K < r:
        return None
    L = B.side_law(a, s)
    if not (Q2(K) < L):
        return None
    u = K // r
    g = (L - Q2(K)) * Q2(F(1, r - 1), F(0))     # (L - K)/(r-1), exact in Q(sqrt2)
    xs = []
    for J in range(r):
        start = Q2(J) * (Q2(u) + g)
        xs.extend(start + HALF + Q2(i) for i in range(u))
    return xs, L, g


def bed_profile_r(a: int, s: int, K: int, rx: int, p: int, q: int):
    """(windows, L, g): the bed's `dy` window for each x of the `rx`-run axis."""
    got = runs_r(a, s, K, rx)
    if got is None:
        return None
    xs, L, g = got
    c = L * HALF
    return [B.dy_window(x - c, p, q, L) for x in xs], L, g


def bed_windows_r(a: int, s: int, K: int, r: int, p: int, q: int):
    """(windows, L): the bed's `dy` window per x position, with the per-shape terms hoisted.

    `beds`, `A*sqrt2` and `B*sqrt2` depend on `(p, q, L)` only, so they are computed once per
    shape instead of once per x cell -- the same numbers `B.dy_window` produces, at a third of
    the cost, which is what makes the beat probe over six run counts affordable.
    """
    got = runs_r(a, s, K, r)
    if got is None:
        return None
    xs, L, g = got
    c = L * HALF
    _A, _B, C = B.beds(p, q, L)
    ap = Q2(1, F(p, 2))
    bp = Q2(1, F(q, 2))
    out = []
    for x in xs:
        dx = x - c
        lo = max(-dx - ap, dx - bp, -C)
        hi = min(-dx + ap, dx + bp, C)
        out.append((lo, hi))
    return out, L


def count_r(a: int, s: int, K: int, rx: int, ry: int, p: int, q: int):
    """(posed, D, L, g): the analytic bed count; `assemble_r` is its independent cross-check."""
    wp = bed_windows_r(a, s, K, rx, p, q)
    yp = runs_r(a, s, K, ry)
    if wp is None or yp is None:
        return False, 0, None, None
    wins, L = wp
    ys, _L, _gy = yp
    return True, B.count_windows(wins, ys, L), L, min(wp[1], _gy)


def assemble_r(a: int, s: int, K: int, rx: int, ry: int, p: int, q: int):
    """The declared pose: (kept carrier cells, block cells, L, dropped, gap)."""
    gx = runs_r(a, s, K, rx)
    gy = runs_r(a, s, K, ry)
    if gx is None or gy is None:
        return None
    xs, L, g1 = gx
    ys, _L, g2 = gy
    c = L * HALF
    blk = B.block(p, q, L)
    kept, dropped = [], 0
    for x in xs:
        for y in ys:
            if B.in_bed(x - c, y - c, p, q, L):
                dropped += 1
            else:
                kept.append((x, y))
    return kept, blk, L, dropped, min(g1, g2)


def check_r(a: int, s: int, K: int, rx: int, ry: int, p: int, q: int,
            stop: bool = False) -> dict:
    """Assemble, gate exactly, and require the pose's own count and its declared box.

    The same decision as `block_bed.check`: `qsqrt2.gate` on the rebuilt pose, no pre-filter,
    plus containment and `L_pose == L`.  The count is *reported*, and every caller that calls
    this a hit must also assert `n == the row's n` -- gating alone is not a hit (run 146).
    """
    got = assemble_r(a, s, K, rx, ry, p, q)
    if got is None:
        return None
    kept, blk, L, dropped, g = got
    state = kept + blk
    words = [AXIS] * len(kept) + [W45] * len(blk)
    gate = Q.gate(state, words, stop=stop)
    ex = [Q.frame_extent(*w) for w in words]
    contained = all(Q2(0) <= pt[0] - e and pt[0] + e <= L and
                    Q2(0) <= pt[1] - e and pt[1] + e <= L
                    for pt, e in zip(state, ex))
    L_pose = Q.side(state, words) if state else Q2(0)
    span = L_pose == L
    return {"a": a, "s": s, "K": K, "rx": rx, "ry": ry, "p": p, "q": q, "g": g,
            "L": L, "L_pose": L_pose, "n": len(state), "dropped": dropped,
            "carrier": len(kept), "block": len(blk), "gate": gate,
            "contained": contained, "span": span,
            "ok": bool(gate["ok"]) and contained and span,
            "state": state, "words": words}


# --------------------------------------------------------------- entry test ---
def entry_test(max_r: int = MAX_R, verbose: bool = True) -> dict:
    """Reproduce the delivered (n, side) of the 110 two-class rows with r = 2..max_r.

    A row counts only when a declaration builds a pose with **exactly the row's count**, the
    target side, and no overlap under the exact gate.  The analytic bed count only nominates;
    `check_r` rebuilds the pose and the count must match.
    """
    rows = B.two_class_rows()
    detail, hits = [], 0
    for n, dec, k, m in rows:
        got = B.exact_side(dec)
        rec = {"n": n, "target": str(dec), "grid": k, "m_hint": m,
               "exact": got is not None, "count_matched": False, "refused": 0}
        if got is None:
            rec.update({"reproduced": False, "why": "side is not a + (s/2)sqrt2"})
            detail.append(rec)
            continue
        L, a, s = got
        rec["target"], rec["a"], rec["s"] = str(L), a, s
        pts = [(p, q) for p, q in B.shapes(m) if Q2(0, F(p + q, 2)) <= L]
        k_lo = min([max(2, B._count_floor(n, p * q)) for p, q in pts] or [2])
        solved = None
        counted = refused = 0
        for K in range(k_lo, min(B.MAX_K, Q.floor_q2(L)) + 1):
            if solved:
                break
            if not (Q2(K) < L):
                continue
            rs = [r for r in range(2, max_r + 1) if K % r == 0]
            if not rs:
                continue
            ys_by = {ry: runs_r(a, s, K, ry)[0] for ry in rs}
            for p, q in pts:
                if solved:
                    break
                if max(2, B._count_floor(n, p * q)) > K:
                    continue
                wins_by = {}
                for rx in rs:
                    wp = bed_profile_r(a, s, K, rx, p, q)
                    if wp is not None:
                        wins_by[rx] = wp[0]
                for rx in wins_by:
                    if solved:
                        break
                    for ry in ys_by:
                        D = B.count_windows(wins_by[rx], ys_by[ry], L)
                        if K * K - D + p * q != n:
                            continue
                        counted += 1
                        r = check_r(a, s, K, rx, ry, p, q, stop=True)
                        if r is not None and r["ok"] and r["n"] == n:
                            solved = ((K, rx, ry, p, q), r)
                            break
                        refused += 1
        if solved is None:
            rec.update({"reproduced": False,
                        "why": "count matched, gate refused" if counted else
                               "no declaration reaches this count",
                        "count_matched": bool(counted), "refused": refused})
        else:
            (K, rx, ry, p, q), r = solved
            rec.update({"reproduced": True, "params": [K, rx, ry, p, q],
                        "count_matched": True, "family_L": str(r["L"]),
                        "family_n": r["n"], "dropped": r["dropped"],
                        "carrier": r["carrier"], "contacts": r["gate"]["contacts"]})
            hits += 1
        detail.append(rec)
        if verbose and (rec["reproduced"] or len(detail) % 25 == 0):
            print(f"  n={n:>4} reproduced={rec['reproduced']} "
                  f"{rec.get('params', '')} {rec.get('why', '')}", flush=True)
    res = {"rows": len(rows), "reproduced": hits, "threshold": 20,
           "passes": hits >= 20, "max_r": max_r,
           "exact_rows": sum(1 for d in detail if d["exact"]),
           "count_matched": sum(1 for d in detail if d.get("count_matched")),
           "refused": sum(1 for d in detail if d.get("refused")),
           "by_r": {r: sum(1 for d in detail if d.get("params", [0, 0])[1] == r)
                    for r in range(2, max_r + 1)},
           "detail": detail}
    print(f"entry test: {hits}/{len(rows)} two-class rows reproduced "
          f"(threshold 20, r = 2..{max_r}: {res['by_r']}) -> "
          f"{'PASS' if res['passes'] else 'FAIL'}", flush=True)
    return res


def fidelity(res: dict) -> dict:
    """The r = 2 control: the same rows, the same declarations as run 145's carrier.

    Run 145 reproduced 19 rows, every one at `kx = ky = K/2`.  The two-run member of this
    family must reproduce exactly those rows at exactly those declarations -- if it does not,
    the r-family is a different family and the comparison below means nothing.
    """
    with open(BED_LEDGER) as f:
        old = json.load(f)["entry_test"]["detail"]
    old_hits = {d["n"]: d["params"] for d in old if d["reproduced"]}
    new_hits = {d["n"]: d["params"] for d in res["detail"] if d["reproduced"]}
    r2 = {d["n"]: d["params"] for d in res["detail"]
          if d["reproduced"] and d["params"][1] == 2}
    same_ns = set(old_hits) == set(r2)
    # old params are [K, kx, ky, p, q]; the r-family's are [K, rx, ry, p, q] with
    # rx = ry = 2, and run 145's split is kx = ky = K/2 -- so compare K, p, q and the split
    same_params = all(r2[n][0] == old_hits[n][0] and r2[n][3] == old_hits[n][3]
                      and r2[n][4] == old_hits[n][4]
                      and old_hits[n][1] == old_hits[n][0] // 2
                      and old_hits[n][1] == old_hits[n][2]
                      for n in (set(old_hits) & set(r2)))
    out = {"block_bed_hits": len(old_hits), "r2_hits": len(r2),
           "same_rows": same_ns, "same_declarations": same_params,
           "extra_rows_beyond_r2": len(new_hits) - len(r2)}
    print(f"fidelity: r = 2 reproduces {len(r2)}/{len(old_hits)} of run 145's rows "
          f"(same rows {same_ns}, same declarations {same_params}); "
          f"r > 2 adds {out['extra_rows_beyond_r2']}", flush=True)
    return out


# --------------------------------------------------------------- the beat probe -
def probe_row_r(n, dec, sides, shapes_of, max_r=MAX_R, include=False, verbose=False):
    """Search every lower side for the row's count, in the same order as `beat_probe`.

    The rules are run 146's: the same side grid, only sides strictly below the delivered one
    (`include` adds the delivered side itself, for the control), `K` from the exact count floor,
    every `p x q` whose bbox fits, `need = K^2 + p*q - n` dropped cells, and the first gated
    pose with count `n` is the beat.  The only change is the family that supplies `D`.
    """
    got = B.exact_side(dec)
    rec = {"n": n, "delivered": str(dec), "in_group": got is not None,
           "sides": 0, "shapes": 0, "count_matches": 0, "refused": 0,
           "beat": None, "tie": None}
    if got is None:
        rec["why"] = "delivered side is not a + (s/2)sqrt2"
        return rec
    Ld, ad, sd = got
    pq_hi = min(B.MAX_M, n)
    Kmin = max(2, B._count_floor(n, pq_hi))
    for (a, s, L, dec_s) in sides:
        allowed = dec_s < B._shadow(Ld) or (include and a == ad and s == sd)
        if not allowed or L * L < Q2(n) or Q2(Kmin) >= L:
            continue
        rec["sides"] += 1
        for K in range(Kmin, min(B.MAX_K, Q.floor_q2(L)) + 1):
            if not (Q2(K) < L):
                continue
            pq_lo = max(1, n - K * K)
            if pq_lo > pq_hi:
                continue
            rs = [r for r in range(2, max_r + 1) if K % r == 0]
            if not rs:
                continue
            # the beat probe runs the equal-run family: the same r on both axes.  This
            # is the family the entry test priced (its 19 hits are all symmetric) and it
            # is what makes a six-run probe over every row affordable; the cross-r
            # (rx != ry) surface is left unsearched and declared so.
            ys_by = {}
            for r in rs:
                yr = _runs_cached(a, s, K, r)
                if yr is not None:
                    ys_by[r] = yr[0]
            for (p, q) in shapes_of(pq_lo, pq_hi, L):
                need = K * K + p * q - n
                if need < 0 or need > K * K:
                    continue
                rec["shapes"] += 1
                for r in rs:
                    wp = bed_windows_r(a, s, K, r, p, q)
                    if wp is None:
                        continue
                    wins, _L = wp
                    D = B.count_windows(wins, ys_by[r], L)
                    if D != need:
                        continue
                    rec["count_matches"] += 1
                    chk = check_r(a, s, K, r, r, p, q, stop=True)
                    if chk is not None and chk["ok"] and chk["n"] == n:
                        rec["tie"] = (chk["L"] == Ld)
                        rec["beat"] = {"a": a, "s": s, "L": str(chk["L"]),
                                       "delivered": str(Ld), "K": K,
                                       "rx": r, "ry": r, "p": p, "q": q,
                                       "dropped": chk["dropped"],
                                       "carrier": chk["carrier"],
                                       "contacts": chk["gate"]["contacts"]}
                        if verbose:
                            print(f"  {'TIE' if rec['tie'] else 'BEAT'} n={n}: "
                                  f"L {chk['L']} vs {Ld} (K={K}, r={r}, "
                                  f"{p}x{q})", flush=True)
                        return rec
                        rec["refused"] += 1
    return rec


def beat(limit=None, max_r=MAX_R, include=False, verbose=True, path=BEAT_LEDGER,
         ns=None) -> dict:
    SQ.guard(quiet=True)
    rows = B.two_class_rows()
    if ns:
        rows = [r for r in rows if r[0] in ns]
    if limit:
        rows = rows[:limit]
    sides = BP.group_sides()
    detail = []
    t0 = __import__("time").time()
    for i, (n, dec, k, m) in enumerate(rows):
        detail.append(probe_row_r(n, dec, sides, BP.all_shapes, max_r=max_r,
                                  include=include, verbose=verbose))
        if verbose:
            print(f"  [{i + 1}/{len(rows)}] n={n} "
                  f"({__import__('time').time() - t0:.0f}s)", flush=True)
    beats = [d for d in detail if d["beat"] and not d["tie"]]
    ties = [d for d in detail if d["beat"] and d["tie"]]
    res = {"rows": len(detail), "in_group": sum(1 for d in detail if d["in_group"]),
           "sides_searched": sum(d["sides"] for d in detail),
           "shapes_tried": sum(d["shapes"] for d in detail),
           "count_matches": sum(d["count_matches"] for d in detail),
           "refused": sum(d["refused"] for d in detail),
           "beats": len(beats), "ties": len(ties), "max_r": max_r,
           "include_delivered": include,
           "beat_rows": [{"n": d["n"], **d["beat"]} for d in beats],
           "detail": detail}
    print(f"beat probe: {len(detail)} rows, {res['count_matches']} count matches, "
          f"{res['beats']} beats, {res['ties']} ties -> "
          f"{'REACH BOUGHT' if beats else 'no beat'}", flush=True)
    if path:
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        print(f"wrote {os.path.relpath(path, ROOT)}", flush=True)
    return res


def tie_control(ns=None) -> dict:
    """r = 2 must re-find run 145's ties at exactly their delivered sides."""
    with open(BED_LEDGER) as f:
        old = json.load(f)["entry_test"]["detail"]
    hits = sorted(d["n"] for d in old if d["reproduced"])
    rows = {n: (dec, k, m) for n, dec, k, m in B.two_class_rows()}
    ns = ns or hits
    sides = BP.group_sides()
    out = []
    for n in ns:
        dec, k, m = rows[n]
        out.append(probe_row_r(n, dec, sides, BP.all_shapes, max_r=2,
                               include=True, verbose=True))
    found = sum(1 for d in out if d["beat"] and d["tie"])
    print(f"tie control: {found}/{len(ns)} of run 145's rows re-found as ties at r = 2",
          flush=True)
    return {"expected": len(ns), "found": found, "rows": out}


# ------------------------------------------------------------------ selftest ---
def selftest() -> int:
    SQ.guard(quiet=True)
    print("block_bed_r selftest")

    # 1. r = 2 is run 145's symmetric split: same positions, same gap, element for element
    for (a, s, K) in ((3, 4, 4), (2, 2, 2), (5, 7, 8), (4, 3, 6)):
        L = B.side_law(a, s)
        if not (Q2(K) < L) or K % 2:
            continue
        xs2, _L, g2 = runs_r(a, s, K, 2)
        xb, _Lb, gb = B.runs(a, s, K, K // 2)
        assert xs2 == xb, (a, s, K)
        assert g2 == gb, (a, s, K, g2, gb)
    print("  1. r = 2 == block_bed's two runs at kx = ky = K/2 (positions and gap)")

    # 2. the law: for every r, the carrier alone is disjoint (g > 0) and spans [0, L]
    tried = 0
    for (a, s, K) in ((3, 4, 4), (2, 2, 3), (5, 7, 8), (5, 7, 6), (4, 3, 6), (2, 5, 4)):
        L = B.side_law(a, s)
        for r in range(2, MAX_R + 1):
            got = runs_r(a, s, K, r)
            if got is None:
                continue
            xs, Lr, g = got
            assert g > Q2(0), (a, s, K, r, g)
            assert Q2(0) == Q2(0) and xs[0] - HALF == Q2(0), (a, s, K, r)
            assert xs[-1] + HALF == L, (a, s, K, r, xs[-1], L)
            state = [(x, y) for x in xs for y in xs]
            gate = Q.gate(state, [AXIS] * len(state), stop=True)
            assert gate["ok"], (a, s, K, r, gate)
            tried += 1
    print(f"  2. gap > 0 and the carrier alone gates for {tried} (K, r) declarations, r = 2..6")

    # 3. the analytic count against the assembly on every declaration tried
    decls = [(3, 4, 4, 2, 2, 2, 2), (3, 4, 4, 4, 4, 1, 2), (2, 2, 3, 3, 3, 1, 2),
             (5, 7, 8, 2, 4, 2, 3), (5, 7, 6, 3, 6, 1, 1), (4, 3, 6, 6, 6, 2, 5),
             (2, 5, 4, 2, 4, 1, 1), (3, 4, 4, 2, 2, 3, 3)]
    checked = 0
    for (a, s, K, rx, ry, p, q) in decls:
        posed, D, L, g = count_r(a, s, K, rx, ry, p, q)
        if not posed:
            continue
        got = assemble_r(a, s, K, rx, ry, p, q)
        assert got is not None
        kept, blk, L2, dropped, g2 = got
        assert L == L2 and D == dropped, (a, s, K, rx, ry, p, q, D, dropped)
        r = check_r(a, s, K, rx, ry, p, q)
        assert r["n"] == K * K - D + p * q, (a, s, K, rx, ry, p, q, r["n"])
        assert r["span"], (a, s, K, rx, ry, p, q)
        checked += 1
        print(f"  3.{a},{s},{K},{rx}x{ry},{p}x{q}: D = {D} = assembled drops, "
              f"n = {r['n']} = K^2 - D + pq, gate ok = {r['ok']}")
    assert checked >= 5, checked

    # 4. the declared box is exact: a block that does not fit it is refused, and the
    #    carrier spans [0, L] to the last half-cell (so `span` cannot pass by accident)
    a, s, K, rx, ry, p, q = 3, 4, 4, 2, 2, 2, 2
    L = B.side_law(a, s)
    good = check_r(a, s, K, rx, ry, p, q)
    assert good is not None and good["ok"] and good["span"], good
    xs, _L, _g = runs_r(a, s, K, rx)
    assert xs[0] - HALF == Q2(0) and xs[-1] + HALF == L, (xs[0], xs[-1], L)
    # a block whose bbox is wider than the box puts cells outside: contained = False
    big = check_r(a, s, K, rx, ry, 11, 11)
    assert big is not None and not big["ok"] and not big["contained"], big["contained"]
    print(f"  4. box exact: carrier spans [0, L] to the half-cell; an 11x11 block in "
          f"L = {L} is refused (contained = {big['contained']})")

    # 5. the block is bedded, not appended: the count is K^2 - D + pq with D > 0
    r = check_r(a, s, 4, 2, 2, 3, 3)
    assert r["dropped"] > 0 and r["carrier"] == 4 * 4 - r["dropped"]
    print(f"  5. bed: {r['dropped']} of {4*4} carrier cells dropped, {r['carrier']} kept, "
          f"{r['block']} block cells, n = {r['n']}")

    # 6. float-free decision path
    import exact_field as EF
    mod = sys.modules[__name__]
    nfun, offenders, skipped = EF.audit_module(mod, exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  6. bytecode audit: {nfun} decision functions, 0 naming float "
          f"(exempt {skipped})")
    print("selftest OK (6 controls)")
    return 0


# -------------------------------------------------------------------- report ---
def main(argv) -> int:
    SQ.guard(quiet=True)
    if "--selftest" in argv:
        return selftest()
    if "--beat" in argv:
        if "--control" in argv:
            tie_control()
            return 0
        lim = None
        for f in argv:
            if f.startswith("--limit="):
                lim = int(f.split("=")[1])
        ns = None
        if "--hits" in argv:
            # the rows the family reaches at the delivered side (the entry test's 19):
            # a probe below it is only plausible there, and the full 110-row sweep over
            # five run counts is ~2 h -- this is the reach subset, declared in the ledger
            with open(LEDGER) as f:
                ns = {d["n"] for d in json.load(f)["entry_test"]["detail"]
                      if d["reproduced"]}
        beat(limit=lim, ns=ns)
        return 0
    print("block_bed_r — r equal runs per axis with a centred tilted block, Q(sqrt 2)")
    res = entry_test()
    led = {"family": "r equal runs per axis (r = 2..6) + centred p x q block, bedded",
           "gap_law": "r runs of K/r cells, r-1 equal gaps (L-K)/(r-1) > 0; disjoint by arithmetic",
           "max_r": MAX_R, "entry_test": res, "fidelity": fidelity(res)}
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
