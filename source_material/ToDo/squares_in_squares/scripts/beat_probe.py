#!/usr/bin/env python3
r"""beat_probe.py — can the block-bedded carrier ever *beat* a delivered row? (Run 146)

Run 145 built `block_bed.py` and asked whether the family can reproduce the delivered
table.  This script asks the other question, the one that decides whether the family is
worth a sweep: at the same count `n`, can it reach a side **strictly below** the delivered
one?  A tie explains the table; a beat moves the score.

THE ARITHMETIC THAT MAKES THE QUESTION SMALL.  Every cell has area 1, so any legal pose of
`n` cells needs `L*L >= n`: a beat can only sit in the group sides

    sqrt n  <=  L  <  L_delivered,

and the family needs `L > K` with `n = K*K - D + p*q` and `D >= 0`, so `K*K >= n - p*q`.
For the delivered sides (fill 0.90-0.97) that window is a few sides wide and the grid size
`K` is pinned to `sqrt n +-` a few.  What is left is the exact count equation and the gate.

THE TABLE.  For each `(side, K, p, q)` the bed count of *every* split `(kx, ky)` is needed,
and computing each split separately costs a pass.  `probe_table` computes the whole `K x K`
table in one O(K^2) pass.  All the geometry is `(A + B*sqrt2)/4` with `A, B` integers
(positions, the side, the window bounds), so the comparisons are **exact** integer
comparisons: a bisect on a shadow key `A*10^9 + B*round(sqrt2*10^9)` finds the boundary,
and `_sgn` walks it to the exact index.  Exactness matters here for a measured reason: the
windows very often end *exactly* on a lattice point (the block touches a cell corner), and a
rounded comparison then answers wrongly by one cell.  Run 145's first counter was wrong for
a neighbouring reason and reported 48 rows where the true number is 19.

Every count match is then rebuilt by `block_bed.check` and judged by `qsqrt2.gate`, and a
hit is recorded only when `r["n"] == n` too.  `--selftest` compares the table with
`block_bed.bed_count` on every split of six declarations.

    python3 scripts/beat_probe.py               # the 110 two-class rows
    python3 scripts/beat_probe.py --limit 5     # a sample, with timings
    python3 scripts/beat_probe.py --selftest    # table vs counter on every split
    python3 scripts/beat_probe.py --shapes vocab  # the 26 shapes the table actually uses
"""
from __future__ import annotations

import bisect
import json
import os
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction as F

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import block_bed as B                       # noqa: E402
import qsqrt2 as Q                          # noqa: E402
from qsqrt2 import Q2, HALF                 # noqa: E402

LEDGER = os.path.join(ROOT, "workspace/push/beat_probe.json")

S_FX = 10 ** 9                              # scale of the search key (not a decision)
SQ2_FX = 1414213562                         # round(sqrt 2 * S_FX)


# ------------------------------------------------- exact arithmetic on (A, B)/4 --
def _pair(z: Q2):
    """`z` as `(A, B)` with `z = (A + B*sqrt2)/4`; every quantity here has denominator 4."""
    a, b = z.a * 4, z.b * 4
    assert a.denominator == 1 and b.denominator == 1, z
    return int(a), int(b)


def _key(pair) -> int:
    """A monotone search key for `(A, B)`; two keys that are equal are re-tested exactly."""
    A, B = pair
    return A * S_FX + B * SQ2_FX


def _sgn(A: int, B: int) -> int:
    """The exact sign of `(A + B*sqrt2)/4` — integers only, never a tolerance."""
    if B == 0:
        return (A > 0) - (A < 0)
    if A == 0:
        return (B > 0) - (B < 0)
    if A > 0 and B > 0:
        return 1
    if A < 0 and B < 0:
        return -1
    aa, bb = A * A, 2 * B * B
    if aa == bb:                     # impossible for integers, kept as a guard
        return 0
    if A > 0:                        # B < 0: sign of A - |B|*sqrt2
        return 1 if aa > bb else -1
    return 1 if bb > aa else -1      # A < 0, B > 0


def _cmp(p, q) -> int:
    return _sgn(p[0] - q[0], p[1] - q[1])


def _bisect_exact(keys, pairs, key, pair, right: bool) -> int:
    """`bisect_left`/`bisect_right` in the exact order, using the key only as a hint."""
    i = bisect.bisect_right(keys, key) if right else bisect.bisect_left(keys, key)
    n = len(keys)
    # walk down while the exact order says the element belongs after `pair`
    while i > 0:
        c = _cmp(pairs[i - 1], pair)
        if (c > 0) if not right else (c >= 0):
            i -= 1
        else:
            break
    while i < n:
        c = _cmp(pairs[i], pair)
        if (c < 0) if not right else (c <= 0):
            i += 1
        else:
            break
    return i


# ------------------------------------------------------------------ the table --
def probe_table(a: int, s: int, K: int, p: int, q: int):
    """{kx: [D(ky) for ky in 0..K]} — the bed count of every split, exactly, in O(K^2).

    A split `kx` takes the first `kx` x candidates of the family `0.5+i` and the **last**
    `K-kx` of the family `L-K+0.5+j` (the runs are anchored at `0` and at `L`), and the same
    holds for `ky`, so the table is a bottom prefix in x plus a top suffix in x, each
    carrying its own y counts.
    """
    L = B.side_law(a, s)
    if L - Q2(K) <= Q2(0):
        return None
    if Q2(0, F(p + q, 2)) > L:                # the block's bbox must fit the box
        return None
    cp = _pair(L * HALF)
    bot = [_pair(HALF + Q2(i)) for i in range(K)]
    top = [_pair(L - Q2(K) + HALF + Q2(i)) for i in range(K)]
    bk = [_key(t) for t in bot]
    tk = [_key(t) for t in top]
    ap = _pair(Q2(1, F(p, 2)))                # A*sqrt 2
    bp = _pair(Q2(1, F(q, 2)))                # B*sqrt 2
    ca = _pair(HALF + Q2(0, F(p + q, 4)))     # C
    zero = [0] * (K + 1)

    def g_of(pos):
        # dx = pos - L/2, in pairs
        dx = (pos[0] - cp[0], pos[1] - cp[1])
        # lo = max(-dx - ap, dx - bp, -C),  hi = min(-dx + ap, dx + bp, C)
        lo = (-dx[0] - ap[0], -dx[1] - ap[1])
        v = (dx[0] - bp[0], dx[1] - bp[1])
        if _cmp(v, lo) > 0: lo = v
        v = (-ca[0], -ca[1])
        if _cmp(v, lo) > 0: lo = v
        hi = (-dx[0] + ap[0], -dx[1] + ap[1])
        v = (dx[0] + bp[0], dx[1] + bp[1])
        if _cmp(v, hi) < 0: hi = v
        if _cmp(ca, hi) < 0: hi = ca
        if _cmp(lo, hi) >= 0:
            return None
        lo = (lo[0] + cp[0], lo[1] + cp[1])   # back to absolute coordinates
        hi = (hi[0] + cp[0], hi[1] + cp[1])
        b0 = _bisect_exact(bk, bot, _key(lo), lo, True)
        b1 = _bisect_exact(bk, bot, _key(hi), hi, False)
        t0 = _bisect_exact(tk, top, _key(lo), lo, True)
        t1 = _bisect_exact(tk, top, _key(hi), hi, False)
        if b0 >= b1 and t0 >= t1:
            return None
        out = [0] * (K + 1)
        for ky in range(K + 1):
            nb = min(b1, ky) - b0
            if nb < 0: nb = 0
            nt = t1 - (t0 if t0 > ky else ky)
            if nt < 0: nt = 0
            out[ky] = nb + nt
        return out

    gb = [g_of(t) for t in bot]
    gt = [g_of(t) for t in top]
    PB = [[0] * (K + 1)]
    for g in gb:
        prev = PB[-1]
        PB.append(prev[:] if g is None else [u + v for u, v in zip(prev, g)])
    ST = [zero[:] for _ in range(K + 2)]
    for i in range(K - 1, -1, -1):
        g = gt[i]
        nxt = ST[i + 1]
        ST[i] = nxt[:] if g is None else [u + v for u, v in zip(nxt, g)]
    return {kx: [u + v for u, v in zip(PB[kx], ST[kx])] for kx in range(1, K)}


# ---------------------------------------------------------------------- the probe --
def group_sides():
    """Every declared side `a + (s/2) sqrt 2`, ascending, with its Decimal shadow."""
    out = []
    for s in range(1, B.MAX_SEAM + 1):
        for a in range(1, 40):
            L = B.side_law(a, s)
            out.append((a, s, L, B._shadow(L)))
    out.sort(key=lambda t: t[3])
    return out


def vocab_shapes():
    """The distinct block shapes the family's reproductions of the table actually use."""
    led = json.load(open(os.path.join(ROOT, "workspace/push/block_bed.json")))["entry_test"]
    out = set()
    for d in led["detail"]:
        if d.get("reproduced"):
            out.add(tuple(d["params"][3:]))
    return sorted(out)


def probe_row(n, dec, sides, shapes_of, verbose=False, include=False):
    """Search every lower side for the row's count; stop at the first gated beat."""
    got = B.exact_side(dec)
    rec = {"n": n, "delivered": str(dec), "in_group": got is not None,
           "sides": 0, "shapes": 0, "count_matches": 0, "refused": 0,
           "beat": None, "exhausted": True}
    if got is None:
        rec["why"] = "delivered side is not a + (s/2)sqrt2 (the family cannot even tie it)"
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
            for (p, q) in shapes_of(pq_lo, pq_hi, L):
                need = K * K + p * q - n
                if need < 0 or need > K * K:
                    continue
                rec["shapes"] += 1
                tab = probe_table(a, s, K, p, q)
                if tab is None:
                    continue
                cand = []
                for kx in range(1, K):
                    row = tab[kx]
                    if need in row[1:K]:
                        for ky in range(1, K):
                            if row[ky] == need:
                                cand.append((kx, ky))
                for (kx, ky) in cand:
                    rec["count_matches"] += 1
                    r = B.check(a, s, K, kx, ky, p, q, stop=True)
                    if r["ok"] and r["n"] == n:
                        rec["tie"] = r["L"] == Ld
                        rec["beat"] = {"a": a, "s": s, "L": str(r["L"]),
                                       "delivered": str(Ld), "K": K, "kx": kx, "ky": ky,
                                       "p": p, "q": q, "dropped": r["dropped"],
                                       "carrier": r["carrier"],
                                       "contacts": r["gate"]["contacts"]}
                        if verbose:
                            print(f"  BEAT n={n}: L {r['L']} < {Ld} "
                                  f"(K={K}, kx={kx}, ky={ky}, {p}x{q})", flush=True)
                        return rec
                    rec["refused"] += 1
    return rec


def all_shapes(pq_lo, pq_hi, L):
    """Every `p x q` with `pq_lo <= p*q <= pq_hi` whose bbox fits the box."""
    out = []
    for pq in range(pq_lo, pq_hi + 1):
        for (p, q) in B.shapes(pq):
            if Q2(0, F(p + q, 2)) <= L:
                out.append((p, q))
    return out


def vocab_shapes_of(pq_lo, pq_hi, L, vocab):
    return [(p, q) for (p, q) in vocab if pq_lo <= p * q <= pq_hi and Q2(0, F(p + q, 2)) <= L]


def probe(limit=None, mode="all", verbose=True, path=None):
    import sqscore as _SQ
    getcontext().prec = 60
    _SQ.guard(quiet=True)
    rows = B.two_class_rows()
    if limit:
        rows = rows[:limit]
    sides = group_sides()
    if mode == "vocab":
        vocab = vocab_shapes()
        shapes_of = lambda lo, hi, L: vocab_shapes_of(lo, hi, L, vocab)
    else:
        shapes_of = all_shapes
    detail = []
    t0 = time.monotonic()
    for i, (n, dec, _k, _m) in enumerate(rows):
        rec = probe_row(n, dec, sides, shapes_of, verbose=verbose)
        detail.append(rec)
        if path:                                     # keep partial work if the run is cut
            with open(path, "w") as f:
                json.dump({"family": "seamed grid + centred block, bedded",
                           "question": "beat = same count at a strictly lower side",
                           "mode": mode, "partial": True, "done": len(detail),
                           "total": len(rows), "detail": detail}, f, indent=1)
        if verbose and (rec["beat"] or (i + 1) % 10 == 0):
            el = time.monotonic() - t0
            print(f"  [{i + 1}/{len(rows)}] n={n:>4} sides={rec['sides']} "
                  f"shapes={rec['shapes']} matches={rec['count_matches']} "
                  f"refused={rec['refused']} beat={bool(rec['beat'])} ({el:.0f}s)", flush=True)
    beats = [d for d in detail if d["beat"]]
    res = {"rows": len(rows), "beats": len(beats),
           "in_group": sum(1 for d in detail if d["in_group"]),
           "sides_searched": sum(d["sides"] for d in detail),
           "shapes_tried": sum(d["shapes"] for d in detail),
           "count_matches": sum(d["count_matches"] for d in detail),
           "refused": sum(d["refused"] for d in detail),
           "seconds": round(time.monotonic() - t0, 1),
           "mode": mode, "detail": detail}
    print(f"probe[{mode}]: {len(detail)} rows, {res['sides_searched']} (row, side) windows, "
          f"{res['shapes_tried']} (side, K, shape) trials, {res['count_matches']} count "
          f"matches, {res['refused']} gate refusals -> {len(beats)} beat(s) "
          f"in {res['seconds']:.0f}s")
    return res


def tie_control(ns=None, verbose=True):
    """Sensitivity: with the delivered side *included*, the probe must re-find the tie.

    A null beat result is only worth something if the same search can find the tie it is
    supposed to find.  This runs the identical `probe_row` over the recorded reproductions
    with `include=True` and requires the hit to be at exactly the delivered side — a tie,
    never below — which exercises the whole chain (table, count, gate, `r["n"] == n`).
    """
    led = json.load(open(os.path.join(ROOT, "workspace/push/block_bed.json")))["entry_test"]
    rep = [d for d in led["detail"] if d.get("reproduced")]
    if ns:
        rep = [d for d in rep if d["n"] in ns]
    decs = {n: dec for (n, dec, _k, _m) in B.two_class_rows()}
    sides = group_sides()
    ok = 0
    for d in rep:
        rec = probe_row(d["n"], decs[d["n"]], sides, all_shapes, include=True)
        hit = rec["beat"]
        assert hit is not None, (d["n"], "the probe did not re-find its own tie")
        assert hit["L"] == hit["delivered"], (d["n"], hit["L"], hit["delivered"])
        assert rec["tie"] is True, (d["n"], rec.get("tie"))
        ok += 1
        if verbose:
            print(f"  tie n={d['n']:>4}: re-found at exactly the delivered side "
                  f"(K={hit['K']}, kx={hit['kx']}, ky={hit['ky']}, "
                  f"{hit['p']}x{hit['q']})", flush=True)
    print(f"  tie control: {ok} reproductions re-found at exactly their delivered side")
    return ok


# ------------------------------------------------------------------ selftest ------
def selftest() -> int:
    getcontext().prec = 60
    print("beat_probe selftest")
    assert probe_table(2, 1, 2, 4, 4) is None      # a block far too large for its box
    print("  0. an oversized block is refused by the table (bbox bound)")
    cases = ((6, 8, 10, 8, 8), (5, 5, 8, 5, 5), (5, 5, 8, 1, 1),
             (21, 13, 30, 18, 18), (2, 1, 2, 1, 1), (20, 13, 29, 13, 13))
    total = 0
    for (a, s, K, p, q) in cases:
        tab = probe_table(a, s, K, p, q)
        assert tab is not None, (a, s, K, p, q)
        for kx in range(1, K):
            for ky in range(1, K):
                _posed, D, _L = B.bed_count(a, s, K, kx, ky, p, q)
                assert tab[kx][ky] == D, (a, s, K, kx, ky, p, q, tab[kx][ky], D)
                total += 1
        print(f"  1.{a}.{s}.{K}.{p}x{q}: table == bed_count on all {K - 1} x {K - 1} splits")
    print(f"  1. {total} splits agree with the exact counter")

    led = json.load(open(os.path.join(ROOT, "workspace/push/block_bed.json")))["entry_test"]
    rep = [d for d in led["detail"] if d.get("reproduced")]
    for d in rep[:5]:
        K, kx, ky, p, q = d["params"]
        tab = probe_table(d["a"], d["s"], K, p, q)
        assert tab[kx][ky] == d["dropped"], (d["n"], tab[kx][ky], d["dropped"])
        print(f"  2.n={d['n']} table[{kx}][{ky}] = {d['dropped']} = the recorded drop count")
    print(f"  2. {min(5, len(rep))} recorded declarations reproduced by the table")

    sides = group_sides()
    for d in rep[:5]:
        K, kx, ky, p, q = d["params"]
        n = d["n"]
        bad = 0
        for (a, s, L, dec_s) in sides:
            if not (dec_s < B._shadow(B.side_law(d["a"], d["s"]))) or Q2(K) >= L:
                continue
            posed, D, _L = B.bed_count(a, s, K, kx, ky, p, q)
            if posed and K * K - D + p * q == n:
                bad += 1
        assert bad == 0, (n, d["params"], bad)
    print("  3. the same shape at a lower side never keeps the count (0 matches)")

    # 4. sensitivity: the identical search, with the delivered side allowed, re-finds the tie
    tie_control(ns={5, 124, 688}, verbose=False)
    print("  4. sensitivity control: 3 recorded ties are re-found at exactly their side")
    print("selftest OK (4 controls)")
    return 0


def main() -> int:
    import sqscore as _SQ
    getcontext().prec = 60
    _SQ.guard(quiet=True)
    limit = None
    mode = "all"
    if "--control" in sys.argv:
        getcontext().prec = 60
        tie_control()
        return 0
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    if "--shapes" in sys.argv:
        mode = sys.argv[sys.argv.index("--shapes") + 1]
    res = probe(limit=limit, mode=mode, path=LEDGER)
    led = {"family": "seamed K x K grid (independent x/y splits) + centred p x q block, bedded",
           "question": "can the family reach a row's count at a side strictly below the "
                       "delivered one (a beat, not a tie)?",
           "method": "group sides in [sqrt n, L_del), K with K*K >= n - p*q and K < L, shapes "
                     "p*q <= 330 with the bbox inside the box, every split, exact integer "
                     "count table; every count match is rebuilt and gated by block_bed.check "
                     "and must report n",
           "result": res}
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
