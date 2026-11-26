#!/usr/bin/env python3
r"""carrier_offset.py — the carrier's one free design parameter: where the block sits (Run 148).

`carrier_ceil.py` sweeps the block-bedded carrier exactly and returns **0 beats in 25,935
declarations**: at n <= 100 the family never reaches a row's count below the row's side.  But that
sweep declares the block **centred**, which is what runs 145-147 all used.  The block's position is
a free parameter the family has never spent, and it is the natural object of a motif design: the
carrier's count is `n = K^2 - D + p*q`, so the *only* thing the block's position can change is `D`,
the number of carrier cells it beds out.

The count law therefore turns the design into arithmetic.  For a row `n` and a declaration
`(K, p, q)` the block must bed exactly

    D* = K^2 + p*q - n

cells.  `D` is an integer that changes by one as the block slides (one carrier cell at a time
crosses the bed boundary), so the reachable `D` at a fixed `(K, split, side)` is a *range*, and the
question "can the family reach this row at a side below the delivered one" is "does some declaration
admit `D*` inside its range, below that side".

This module asks it for the open, **non-proved** tie rows only -- the rows whose delivered side is
the plain grid and where the literature has **not** proved the grid optimal:

    n = 12, 20, 30, 42, 56, 72, 91        (bands k = 4, 5, 6, 7, 8, 9, 10)

Every proved-optimal row (`glm_plan`'s 49-row set, e.g. 13-16, 21-25, 32-36, 45-49) is refused by
this instrument before it looks at any geometry: a proved optimum cannot be beaten, so spending a
search on it is the dead end doc 94 §3 named.  Row 6 is refused twice over (proved, `s(6) = 3`).

DISCOVERY vs. VERDICT.  The scan is float (numpy) and is allowed to be wrong -- it only nominates
`(L, K, kx, ky, p, q, tx, ty)` tuples.  Every nomination is rebuilt in `Q(sqrt 2)` with rational
offsets and judged by `qsqrt2.gate`; the count is recounted by `block_bed.in_bed` cell by cell; the
side is `qsqrt2.side`.  Nothing here is claimed on the float scan's word.

    python3 scripts/carrier_offset.py            # the seven open tie rows
    python3 scripts/carrier_offset.py --selftest  # 5 controls
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F

import numpy as np

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import block_bed as BB                          # noqa: E402
import qsqrt2 as Q                              # noqa: E402
from qsqrt2 import Q2, HALF                     # noqa: E402

LEDGER = os.path.join(ROOT, "workspace/push/carrier_offset.json")
AXIS = Q.AXIS
W45 = Q.word_45()
MARGIN = Decimal("1e-8")

#: the open tie rows: delivered side = ceil(sqrt n), not proved optimal, band decidable
ROWS = (12, 20, 30, 42, 56, 72, 91)


def ceil_sqrt(n: int) -> int:
    k = 1
    while k * k < n:
        k += 1
    return k


def proved_rows() -> set:
    """The published frontier's proved-optimal rows (`glm_plan.pub_table`)."""
    import glm_plan as GP
    _pub, proved = GP.pub_table()
    return set(proved)


# --------------------------------------------------------------- float scan --
def positions(K: int, split: int, L: float) -> np.ndarray:
    a = np.arange(split, dtype=float) + 0.5
    b = L - (K - split) + np.arange(K - split, dtype=float) + 0.5
    return np.concatenate([a, b])


def bed_count_float(xs, ys, p, q, L, tx, ty) -> int:
    """The bed size for one offset (discovery only)."""
    dx = (xs - L / 2 - tx)[:, None]
    dy = (ys - L / 2 - ty)[None, :]
    ap = 1.0 + p * np.sqrt(2) / 2.0
    aq = 1.0 + q * np.sqrt(2) / 2.0
    cc = 0.5 + (p + q) * np.sqrt(2) / 4.0
    m = ((np.abs(dx + dy) < ap) & (np.abs(dy - dx) < aq)
         & (np.abs(dx) < cc) & (np.abs(dy) < cc))
    return int(m.sum())


def bed_counts_float(cells, p, q, L, offs) -> np.ndarray:
    """The bed size for *every* offset in `offs` at once (discovery only).

    `cells` is an `(M, 2)` array of carrier centres; `offs` an `(O, 2)` array of block offsets
    from the box centre.  Returns an `(O,)` array of integer bed sizes.
    """
    dx = cells[:, 0][:, None] - L / 2 - offs[:, 0][None, :]
    dy = cells[:, 1][:, None] - L / 2 - offs[:, 1][None, :]
    ap = 1.0 + p * np.sqrt(2) / 2.0
    aq = 1.0 + q * np.sqrt(2) / 2.0
    cc = 0.5 + (p + q) * np.sqrt(2) / 4.0
    m = ((np.abs(dx + dy) < ap) & (np.abs(dy - dx) < aq)
         & (np.abs(dx) < cc) & (np.abs(dy) < cc))
    return m.sum(axis=0)


def scan_row(n: int, ns: int = 40, grid: int = 3):
    """Nominate `(L, K, kx, ky, p, q, tx, ty)` with the row's count below its grid side."""
    k = ceil_sqrt(n)
    Ls = np.linspace(np.sqrt(n) * (1 + 1e-9), k * (1 - 1e-6), ns)
    hits = []
    tried = 0
    dmin = None
    for L in Ls:
        Lf = float(L)
        for K in range(2, int(np.floor(Lf - 1e-9)) + 1):
            for kx in range(1, K):
                xs = positions(K, kx, Lf)
                for ky in range(1, K):
                    ys = positions(K, ky, Lf)
                    cells = np.stack(np.meshgrid(xs, ys, indexing="ij"), axis=-1).reshape(-1, 2)
                    for p in range(1, 20):
                        for q in range(1, 20):
                            m = p * q
                            if m < n - K * K or m > n:
                                continue
                            bbox = (p + q) / np.sqrt(2.0)
                            if bbox > Lf * (1 - 1e-12):
                                continue
                            dtar = K * K + m - n
                            if dtar < 0 or dtar > K * K:
                                continue
                            h = (Lf - bbox) / 2.0
                            a = np.linspace(-h, h, 2 * grid + 1)
                            offs = np.stack(np.meshgrid(a, a, indexing="ij"), axis=-1).reshape(-1, 2)
                            D = bed_counts_float(cells, p, q, Lf, offs)
                            tried += 1
                            low = int(D.min())
                            dmin = low if dmin is None else min(dmin, low)
                            j = np.argmax(D == dtar)
                            if D[j] == dtar:
                                hits.append((Lf, K, kx, ky, p, q,
                                             float(offs[j][0]), float(offs[j][1]), h))
    return k, hits, tried, dmin


# ------------------------------------------------------------- exact verdict --
def exact_build(K: int, kx: int, ky: int, p: int, q: int, L: Q2, tx: Q2, ty: Q2):
    """Rebuild one declaration with the block moved by `(tx, ty)` and judge it exactly."""
    xs = [HALF + Q2(i) for i in range(kx)] + [L - Q2(K - kx) + HALF + Q2(j) for j in range(K - kx)]
    ys = [HALF + Q2(i) for i in range(ky)] + [L - Q2(K - ky) + HALF + Q2(j) for j in range(K - ky)]
    cx, cy = L * HALF + tx, L * HALF + ty
    blk = [(x + tx, y + ty) for (x, y) in BB.block(p, q, L)]
    kept = [(x, y) for x in xs for y in ys if not BB.in_bed(x - cx, y - cy, p, q, L)]
    state = kept + blk
    words = [AXIS] * len(kept) + [W45] * len(blk)
    gate = Q.gate(state, words)
    side = Q.side(state, words) if state else Q2(0)
    ex = [Q.frame_extent(w[0], w[1]) for w in words]
    contained = all(Q2(0) <= pt[0] - e and pt[0] + e <= L and
                    Q2(0) <= pt[1] - e and pt[1] + e <= L
                    for pt, e in zip(state, ex))
    return {"state": state, "words": words, "gate": gate, "side": side, "n": len(state),
            "carrier": len(kept), "block": len(blk), "L": L, "contained": contained,
            "ok": bool(gate["ok"]) and contained}


def certify(n: int, hit, tries: int = 4):
    """Exact rebuild around a nominated offset; returns the smallest gated pose of count `n`.

    The count is decided first (cheap, `in_bed` cell by cell) and the exact gate is called only on
    the poses that already carry the row's count -- the gate is the verdict, the count is the
    filter.
    """
    Lf, K, kx, ky, p, q, tx, ty, h = hit
    Lq = Q2(F(Lf).limit_denominator(10 ** 9))
    if Lq * Lq <= Q2(n):
        return None
    hq = F(h).limit_denominator(10 ** 6)
    best = None
    for i in range(-tries, tries + 1):
        for j in range(-tries, tries + 1):
            txq = Q2(F(tx).limit_denominator(10 ** 6) + F(i, 4000) * hq)
            tyq = Q2(F(ty).limit_denominator(10 ** 6) + F(j, 4000) * hq)
            r = exact_build(K, kx, ky, p, q, Lq, txq, tyq)
            if r["n"] != n or not r["ok"]:
                continue
            dec = Decimal(r["side"].decimal(20))
            if best is None or dec < best[0]:
                best = (dec, r["side"], (K, kx, ky, p, q, str(txq), str(tyq)), r)
    if best is None:
        return None
    return best[1], best[2], best[3]


def report(rows=ROWS):
    import sqscore as SQ
    SQ.guard(quiet=True)
    proved = proved_rows()
    out = []
    for n in rows:
        k = ceil_sqrt(n)
        rec = {"n": n, "k": k, "proved": n in proved}
        if n in proved:
            rec.update({"verdict": "REFUSED: proved optimal -- no search"})
            print(f"n={n:>4} k={k}: REFUSED (proved optimal, the literature fixes the side)")
            out.append(rec)
            continue
        kk, hits, tried, dmin = scan_row(n)
        rec["nominations"] = len(hits)
        rec["declarations_scanned"] = tried
        rec["least_bed_at_any_offset"] = dmin
        best = None
        for hit in hits[:24]:
            c = certify(n, hit)
            if c is None:
                continue
            dec = Decimal(c[0].decimal(20))
            if best is None or dec < best[0]:
                best = (dec, c[0], c[1], c[2])
        if best is None:
            rec.update({"verdict": "no gated pose of this count below the grid side"})
        else:
            dec, side, params, r = best
            rec.update({"verdict": "GATED POSE", "side": str(dec), "params": list(params),
                        "margin": str(Decimal(k) - dec)})
        print(f"n={n:>4} k={k}: {rec['verdict']}"
              + (f" side {rec['side']} (grid {k}, margin {rec['margin']})" if "side" in rec else "")
              + f"  [{rec['nominations']} nominations]")
        out.append(rec)
    led = {"family": "block-bedded carrier with the block's position free (rational offsets)",
           "rows": out,
           "note": "the float scan only nominates; every verdict is an exact Q(sqrt2) gate call"}
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}")
    return led


# ------------------------------------------------------------------ selftest --
def selftest() -> int:
    import sqscore as SQ
    SQ.guard(quiet=True)
    print("carrier_offset selftest")
    import carrier_ceil as CC

    # 1. the float scan's bed count agrees with the exact rule at the centred offset
    checks = 0
    for (K, kx, ky, p, q) in ((4, 2, 2, 2, 2), (5, 1, 3, 2, 2), (6, 3, 3, 3, 3)):
        for num in (20, 24, 28, 32):
            L = num / 4.0
            xs, ys = positions(K, kx, L), positions(K, ky, L)
            d_f = bed_count_float(xs, ys, p, q, L, 0.0, 0.0)
            d_e = CC._brute_D(K, kx, ky, p, q, Q2(F(num, 4)))
            assert d_f == d_e, (K, kx, ky, p, q, num, d_f, d_e)
            checks += 1
    print(f"  1. float scan = exact bed rule at the centred offset on {checks} declarations")

    # 2. sliding the block moves the count, and the reachable set is *not* assumed contiguous:
    #    a symmetric declaration skips every other value, which is exactly why the scan
    #    enumerates offsets instead of interpolating between two extremes
    K, kx, ky, p, q, L, h = 4, 2, 2, 3, 3, 4.9, 0.32
    xs, ys = positions(K, kx, L), positions(K, ky, L)
    seen = [bed_count_float(xs, ys, p, q, L, tx, 0.0) for tx in np.linspace(-h, h, 401)]
    assert min(seen) < max(seen), "the block's position must move the count"
    cells = np.stack(np.meshgrid(xs, ys, indexing="ij"), axis=-1).reshape(-1, 2)
    a = np.linspace(-h, h, 31)
    offs = np.stack(np.meshgrid(a, a, indexing="ij"), axis=-1).reshape(-1, 2)
    vals = sorted({int(v) for v in bed_counts_float(cells, p, q, L, offs)})
    assert len(vals) >= 2 and vals[0] >= 0
    print(f"  2. sliding the block: D ranges over [{min(seen)}, {max(seen)}] on a line and the "
          f"reachable set on the offset grid is {vals} (not contiguous -- offsets are enumerated)")

    # 3. a proved-optimal row is refused before any geometry is looked at
    proved = proved_rows()
    assert 13 in proved and 22 in proved
    print("  3. proved-optimal rows (13, 22) are in the refuse list")

    # 4. the centred member is the published family: offset 0 reproduces the count law exactly
    for (K, kx, ky, p, q, num) in ((4, 2, 2, 2, 2, 20), (5, 1, 1, 1, 2, 20)):
        r = exact_build(K, kx, ky, p, q, Q2(F(num, 4)), Q2(0), Q2(0))
        d_e = CC._brute_D(K, kx, ky, p, q, Q2(F(num, 4)))
        assert r["n"] == K * K - d_e + p * q, (K, kx, ky, p, q, r["n"], d_e)
        assert abs(d_e - float(bed_count_float(positions(K, kx, num / 4.0),
                                              positions(K, ky, num / 4.0), p, q, num / 4.0,
                                              0.0, 0.0))) == 0
    print("  4. offset 0 reproduces the centred family's count law exactly")

    # 5. every certified pose is legal and above the area floor
    n = 20
    k, hits, tried, dmin = scan_row(n, ns=24, grid=3)
    assert tried > 0
    c = None
    for hit in hits[:16]:
        c = certify(n, hit)
        if c:
            break
    if c is None:
        print(f"  5. n = 20: {tried} declarations over the offset grid, {len(hits)} nominate the "
              f"row's count below 5 (least bed seen {dmin}) -- nothing to certify")
    else:
        side, params, r = c
        assert r["ok"] and r["n"] == n and side * side > Q2(n), (side, r["n"])
        print(f"  5. a nomination at n = 20 certifies: side {side.decimal(12)}, count {r['n']}, "
              f"gate ok = {r['ok']}, params {params}")
    print("selftest OK (5 controls)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
