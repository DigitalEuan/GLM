#!/usr/bin/env python3
r"""seam_carrier.py — sparse/notched two-carrier interlock in Q(sqrt 2) (Run 144).

Doc 100 refused the full-block family for an exact reason: a full block fills its
own bounding box, so its cells tile it and two full blocks can only share the
*container*, never a bounding box.  Area sharing needs a carrier with voids: a
lattice made of a few translation domains, so the other carrier's cells can occupy
them (doc 100 §7, §10).

THE FAMILY.  Two axis runs per axis, the second offset by the seam width
`w = sqrt 2 / 2`, and a bar of `m` 45-degree cells set edge to edge along the main
diagonal of the box:

    X        = {1/2, ..., k1 - 1/2}  U  {k1 + s w - o + 1/2, ..., k1 + s w - o + k2 - 1/2}
    carrier  = X x Y                          (four corner blocks when o = 0)
    slots    = m diamonds at (L/2 + t w, L/2 + t w),  t = i - (m-1)/2
    L        = k1 + k2 + s w - o

`s >= 1` is the seam's width in units of `w = sqrt 2 / 2` -- one diamond row is
one unit wide, so `s` is the number of diamond rows the seam is cut for.  `o` is
the interlock: the number of cells by which the second run slides back into the
first.  At `o = 0` the two runs are butted across a bare seam; at `o > 0` the
runs' bounding boxes overlap and only the 45-degree bar separates them, which is
the area sharing doc 99 measured.

THE INSERTION RULE (the notch).  An axis cell that would overlap a slot is
removed: inserting a diamond *means* cutting its bed out of the carrier.  What
survives is sparse -- fill `n/L^2 < 1`, more than one translation domain -- so the
family is a *notched* carrier, not a rectangle.

EXACTNESS.  Every coordinate, extent and slack is `a + b sqrt 2` with `a, b` in Q
(`exact_field.Quad`), the judge is `qsqrt2.gate` (signs, never tolerances), the
side is the exact bbox, and the module names no `float` (bytecode audit, control 8).

THE ENTRY TEST (doc 99 §9, doc 100 §8).  Before any sweep, the family must
reproduce the delivered `(n, side)` pair of at least 20 of the 110 two-class
beating rows, with 0 overlaps under the exact gate.  If it cannot, the run
records the refusal and the measured reason instead of a sweep.

The bar size is searched over `m_hint - 2 .. m_hint + 2`, where `m_hint` is the
row's delivered tilted-class size: the hint bounds *which* declarations are
tried, never whether one is legal, so a refusal cannot be an artefact of one
bar size.  Legality has exactly one decision procedure -- `qsqrt2.gate`, called
from `check` -- and one counter (`counts_for`) that is a speedup of the same
computation, so every accepted pose is judged by the same exact SAT that
refuses every rejected one.

    python3 scripts/seam_carrier.py              # entry test, writes the ledger
    python3 scripts/seam_carrier.py --selftest    # 9 controls
"""
from __future__ import annotations

import bisect
import json
import os
import sys
from decimal import Decimal, getcontext, ROUND_FLOOR
from fractions import Fraction as F

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import qsqrt2 as Q                              # noqa: E402  (exact Q(sqrt 2) gate)
import sqscore as SQ                            # noqa: E402
import tilt_audit as TA                         # noqa: E402  (exact CSV reader)
from qsqrt2 import Q2, HALF                     # noqa: E402

LEDGER = os.path.join(ROOT, "workspace/push/seam_carrier.json")

W = Q2(0, F(1, 2))          # the seam width, sqrt 2 / 2
AXIS = Q.AXIS
W45 = Q.word_45()

MAX_SIDE = 34               # k1, k2 <= this
MAX_OVER = 2                # interlock o <= this
MAX_M = 330                 # slots per declaration: the largest delivered hinted
                            # class is 324, so this leaves every row's +-M_WINDOW
                            # search window non-empty (no zero-bar-size row)
MAX_SEAM = 30               # seam width s, in units of sqrt2/2
M_WINDOW = 2                # the bar size may differ from the hint by this much


# ------------------------------------------------------------------ the family
def runs(k1: int, k2: int, o: int, s: int = 1) -> list[Q2]:
    """X: the two runs, the second slid back by `o` cells across an `s`-wide seam.

    The first run occupies centres `1/2 ... k1-1/2`; the second starts `s` seam
    widths past the first run's end, then slides back `o` cells, so that at
    `o = 0` the runs are butted and at `o >= 1` their boxes interlock.
    """
    first = [Q2(i) + HALF for i in range(k1)]
    start = Q2(k1) + Q2(0, F(s, 2)) - Q2(o) + HALF
    second = [start + Q2(i) for i in range(k2)]
    return first + second


def slots(m: int, L: Q2) -> list[tuple[Q2, Q2]]:
    """The bar: m diamonds edge to edge along the main diagonal, centred."""
    c = L * HALF
    return [(c + Q2(0, F(2 * i - (m - 1), 4)),
             c + Q2(0, F(2 * i - (m - 1), 4))) for i in range(m)]


_COLLIDE: dict = {}


def collide(cell, slot) -> bool:
    """True iff the axis cell and the 45-degree slot overlap (exact).

    The decision depends only on the centre offset, so it is memoised: the
    insertion rule asks the same few offsets thousands of times.
    """
    dx, dy = cell[0] - slot[0], cell[1] - slot[1]
    key = (dx.a, dx.b, dy.a, dy.b)
    hit = _COLLIDE.get(key)
    if hit is None:
        axes = Q.pair_axes([cell, slot], [AXIS, W45], 0, 1)
        hit = not any(sl.sign() >= 0 for _q, sl, _n, _o in axes)
        _COLLIDE[key] = hit
    return hit


def assemble(k1: int, k2: int, o: int, m: int, s: int = 1):
    """The declared pose: (kept axis cells, slots, L, dropped count).

    The declaration is generated from `(k1, k2, o, m, s)` alone.  The insertion
    rule is the notch: every carrier cell a slot would overlap is dropped, so the
    bar cuts its own bed out of the carrier and nothing else is removed.  Where
    the interlock leaves two carrier cells on top of each other the gate refuses
    the declaration -- that refusal is a result, and the entry test counts it.

    Only cells within two units of the diagonal can touch the bar (its cells are
    at most `(1 + sqrt2)/2 < 2` from their nearest carrier partner on either
    axis), so the scan is restricted to that band; the restriction is exact, not
    a tolerance: a cell outside the band is separated on the very axis the bound
    is taken on.
    """
    L = Q2(k1 + k2) + Q2(0, F(s, 2)) - Q2(o)
    xs = runs(k1, k2, o, s)
    bar = slots(m, L)
    cells = [(x, y) for x in xs for y in xs]
    band = [c for c in cells if abs(c[0] - c[1]) <= Q2(2)]
    bar_x = [q[0] for q in bar]
    kept = []
    dropped = 0
    for cell in band:
        lo = bisect.bisect_left(bar_x, cell[0] - Q2(2))
        hit = False
        for j in range(lo, m):
            if bar_x[j] > cell[0] + Q2(2):
                break
            if collide(cell, bar[j]):
                hit = True
                break
        if hit:
            dropped += 1
        else:
            kept.append(cell)
    kept_set = set(kept)
    kept = [c for c in cells
            if abs(c[0] - c[1]) > Q2(2) or c in kept_set]
    return kept, bar, L, len(band) - len(kept_set)


def check(k1: int, k2: int, o: int, m: int, s: int = 1, stop: bool = False) -> dict:
    """Assemble, gate exactly, and report the family's numbers for a declaration.

    This is the **only** legality decision in the module: `qsqrt2.gate` on the
    rebuilt pose, no pre-filter and no second predicate.  `stop=True` lets the
    gate return at its first overlapping pair -- the verdict `ok` is identical,
    only a refused pose's pair counts are cut short -- which is what keeps the
    873 count-matched declarations of the entry test affordable.
    """
    kept, bar, L, dropped = assemble(k1, k2, o, m, s)
    state = kept + bar
    words = [AXIS] * len(kept) + [W45] * len(bar)
    g = Q.gate(state, words, stop=stop)
    ex = [Q.frame_extent(*w) for w in words]
    contained = all(Q2(0) <= p[0] - e and p[0] + e <= L and
                    Q2(0) <= p[1] - e and p[1] + e <= L
                    for p, e in zip(state, ex))
    return {"k1": k1, "k2": k2, "o": o, "m": m, "s": s, "n": len(state), "L": L,
            "dropped": dropped, "carrier": len(kept), "gate": g,
            "ok": bool(g["ok"]) and contained, "contained": contained,
            "state": state, "words": words}


def domains(state, words) -> dict:
    """Translation domains per class, at a 1e-9 shadow of the exact coordinates.

    The projection is the same one doc 100 §6 used: centres reduced modulo one in
    the class's own lattice frame.  Here the frame is exact and the quantisation
    is a Decimal shadow (display), so the count is a measurement, not a verdict.
    """
    out = {}
    for tag, word in (("axis", AXIS), ("tilt", W45)):
        sub = [(p, w) for p, w in zip(state, words) if w == word]
        if not sub:
            out[tag] = 0
            continue
        c, s = word
        keys = set()
        for (x, y), _w in sub:
            u = x * c + y * s
            v = Q2(0) - x * s + y * c
            keys.add((_frac9(u), _frac9(v)))
        out[tag] = len(keys)
    return out


def _frac9(z: Q2) -> int:
    """`z mod 1`, quantised at 1e-9 through a 60-digit Decimal shadow."""
    d = (Decimal(z.a.numerator) / Decimal(z.a.denominator)
         + Decimal(z.b.numerator) / Decimal(z.b.denominator) * Decimal(2).sqrt())
    frac = d - d.to_integral_value(rounding=ROUND_FLOOR)
    return int((frac / Decimal("1e-9")).to_integral_value())


# --------------------------------------------------------------- entry test ---
def two_class_rows() -> list[tuple[int, Decimal, int, int]]:
    """(n, delivered side, grid k, tilted-class size) for the 110 rows.

    The tilted-class size is a *search hint*: it bounds which declarations are
    tried.  Every reproduction reported below is a pose rebuilt from the
    declaration and judged by the exact gate, so the hint cannot manufacture one.
    """
    led = json.load(open(os.path.join(ROOT, "workspace/push/tilt_audit.json")))
    out = []
    for key, r in led["rows"].items():
        if r["beat"] and r["classes"] == 2:
            tilt = max(r["cls"], key=lambda c: F(c["x"]))
            out.append((int(key), Decimal(r["side"]), r["grid"], tilt["m"]))
    return sorted(out)


def exact_side(dec: Decimal):
    """(L, a, s) for a delivered side `a + s*sqrt2/2`, or None.

    The parameters are read off the decimal (`s` in order, `a` the nearest
    integer in a +-1 window) and then *verified* exactly in Q(sqrt 2) to 1e-8.
    This is only a parameterisation step; every verdict below is the exact gate
    on a rebuilt pose.
    """
    for s in range(1, MAX_SEAM + 1):
        rest = dec - Decimal(s) * _shadow(W)
        for a in (int(rest), int(rest) + 1):
            if a < 1:
                continue
            L = Q2(a) + Q2(0, F(s, 2))
            if abs(_shadow(L) - dec) <= Decimal("1e-8"):
                return L, a, s
    return None


def _shadow(z: Q2) -> Decimal:
    """A 60-digit Decimal shadow of a field element (index windows only)."""
    return (Decimal(z.a.numerator) / Decimal(z.a.denominator)
            + Decimal(z.b.numerator) / Decimal(z.b.denominator) * Decimal(2).sqrt())


def band_cells(k1: int, k2: int, o: int, s: int):
    """The carrier cells within `|x - y| <= 2` of the diagonal, by integer index.

    Only these can touch the bar (a 45-degree cell's half-extent is `sqrt2/2`,
    so a carrier cell further than two units off the diagonal is separated from
    every slot on the axis it is off by).  The band is enumerated from the run
    indices, so no work is spent on the rest of the product.
    """
    spec = ((HALF, k1), (Q2(k1) + Q2(0, F(s, 2)) - Q2(o) + HALF, k2))
    out = []
    for base_x, nx in spec:
        for base_y, ny in spec:
            d0 = base_x - base_y
            for k in range(-(nx + ny), nx + ny + 1):
                if abs(d0 + Q2(k)) > Q2(2):
                    continue
                for i in range(nx):
                    j = i - k
                    if 0 <= j < ny:
                        out.append((base_x + Q2(i), base_y + Q2(j), i, j))
    return out


def counts_for(k1: int, k2: int, o: int, ms, s: int = 1):
    """({m: n}, L) for every bar size in `ms`, insertion rule applied exactly.

    This is the counter, not a decision procedure: it reports the count the
    assembled pose would have, and legality is answered only by `check` ->
    `qsqrt2.gate`.  One band pass serves the whole window of bar sizes: the band
    is enumerated from run indices, the slot index window is located on a
    Decimal shadow (a *window*, padded by one on each side), and every actual
    overlap is then decided by the exact `collide`.  So the shadow can only cost
    a wasted comparison, never a wrong count.
    """
    L = Q2(k1 + k2) + Q2(0, F(s, 2)) - Q2(o)
    ms = sorted({m for m in ms if 1 <= m <= MAX_M})
    if not ms:
        return {}, L
    bars = {m: slots(m, L) for m in ms}
    x1 = HALF
    x2 = Q2(k1) + Q2(0, F(s, 2)) - Q2(o) + HALF
    specs = ((x1, k1), (x2, k2))
    step = _shadow(W)
    c_dec = _shadow(L) / 2
    half_m = {m: Decimal(m - 1) / 2 for m in ms}
    base_dec = [[_shadow(bx) for _by, ny in specs] for bx, nx in specs]
    gone = {m: 0 for m in ms}
    for a_i, (bx, nx) in enumerate(specs):
        for b_i, (by, ny) in enumerate(specs):
            d0 = bx - by
            xd0 = base_dec[a_i][b_i]
            for k in range(-(nx + ny), nx + ny + 1):
                if abs(d0 + Q2(k)) > Q2(2):
                    continue
                for i in range(nx):
                    j = i - k
                    if not (0 <= j < ny):
                        continue
                    x, y = bx + Q2(i), by + Q2(j)
                    u_dec = xd0 + Decimal(i)
                    for m in ms:
                        k0 = int((u_dec - c_dec) / step + half_m[m])
                        bar = bars[m]
                        for kk in (k0 - 1, k0, k0 + 1, k0 + 2):
                            if 0 <= kk < m and collide((x, y), bar[kk]):
                                gone[m] += 1
                                break
    return {m: (k1 + k2) ** 2 - gone[m] + m for m in ms}, L


def entry_test(verbose: bool = True) -> dict:
    """Doc 99 §9's gate: reproduce >= 20 of the 110 delivered (n, side) pairs.

    A row counts only when a declaration builds a pose with exactly that count,
    exactly that side in Q(sqrt 2), and no overlap under the exact gate.  A
    zero-gap declaration the gate *refuses* does not count, and the search keeps
    looking for a legal one.
    """
    rows = two_class_rows()
    detail = []
    hits = 0
    for n, dec, k, m_tilt in rows:
        got = exact_side(dec)
        window = [m for m in range(m_tilt - M_WINDOW, m_tilt + M_WINDOW + 1)
                  if 1 <= m <= MAX_M]
        rec = {"n": n, "target": str(dec) if got is None else str(got[0]),
               "exact": got is not None, "m_hint": m_tilt, "window": window}
        solved = None
        near = None
        if got is not None:
            target, ai, st = got                    # a: integer part of the side
            if 1 <= ai <= 2 * MAX_SIDE:
                for k1 in range(1, ai + 1):
                    if solved:
                        break
                    for o in range(0, min(MAX_OVER, k1 + ai - 1) + 1):
                        k2 = ai + o - k1
                        if not (1 <= k2 <= MAX_SIDE):
                            continue
                        counts, L = counts_for(k1, k2, o, window, st)
                        for m in window:
                            if counts[m] != n:
                                continue
                            gap = abs(L - target)
                            if near is None or gap < near[1]:
                                near = ((k1, k2, o, m, st), gap, L)
                            if gap == Q2(0):
                                r = check(k1, k2, o, m, st, stop=True)
                                if r["ok"]:
                                    solved = ((k1, k2, o, m, st), L, r)
                                    break
                        if solved:
                            break
        if solved is None:
            rec.update({"reproduced": False,
                        "why": "no legal declaration with this count",
                        "near": (near[0] if near else None),
                        "near_gap": (str(near[1]) if near else None)})
        else:
            (k1, k2, o, m, st), L, r = solved
            rec.update({"reproduced": True, "params": [k1, k2, o, m, st],
                        "m_delta": m - m_tilt,
                        "family_L": str(L), "family_n": r["n"],
                        "dropped": r["dropped"], "contacts": r["gate"]["contacts"]})
            hits += 1
        detail.append(rec)
        if verbose and (rec["reproduced"] or len(detail) % 25 == 0):
            print(f"  n={n:>4} reproduced={rec['reproduced']} "
                  f"{rec.get('params', '')} {rec.get('family_L', '')}")
    res = {"rows": len(rows), "reproduced": hits, "threshold": 20,
           "passes": hits >= 20, "max_side": MAX_SIDE, "max_over": MAX_OVER,
           "max_seam": MAX_SEAM, "max_m": MAX_M, "m_window": M_WINDOW,
           "exact_rows": sum(1 for d in detail if d["exact"]),
           "count_matched": sum(1 for d in detail if d.get("near")),
           "gated": sum(1 for d in detail if d["reproduced"]),
           "detail": detail}
    print(f"entry test: {hits}/{len(rows)} two-class rows reproduced "
          f"(threshold 20, {res['exact_rows']} sides exact in Q(sqrt2), "
          f"{res['count_matched']} declarations matched a count) -> "
          f"{'PASS' if res['passes'] else 'FAIL'}")
    return res


# -------------------------------------------------------------------- report --
def main() -> int:
    import sqscore as _SQ
    globals()["SQ"] = _SQ
    getcontext().prec = 60
    SQ.guard(quiet=True)
    print("seam_carrier — sparse/notched two-carrier interlock, Q(sqrt 2)")
    res = entry_test()
    led = {"family": "two shifted axis runs + centred 45-degree bar, notched",
           "seam_width": str(W), "max_side": MAX_SIDE, "max_over": MAX_OVER,
           "max_m": MAX_M, "m_window": M_WINDOW, "entry_test": res}
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}")
    return 0


# ------------------------------------------------------------------ selftest --
def selftest() -> int:
    import sqscore as _SQ
    globals()["SQ"] = _SQ
    getcontext().prec = 60
    print("seam_carrier selftest")

    # 1. the seam width is the diagonal cell's own half-extent, exactly
    assert W * W * Q2(2) == Q2(1), W          # (sqrt2/2)^2 * 2 = 1
    assert Q.frame_extent(*W45) == W, Q.frame_extent(*W45)
    print(f"  1. seam width {W} = the 45° cell's half-extent: w^2*2 = 1 exactly")

    # 2. n = 5: one cell per corner and one diamond -- the delivered atom
    r = check(1, 1, 0, 1)
    assert r["n"] == 5 and r["L"] == Q2(2) + W, (r["n"], r["L"])
    assert r["ok"] and r["gate"]["violations"] == 0, r["gate"]
    assert r["gate"]["contacts"] >= 1
    print(f"  2. (k1,k2,o,m) = (1,1,0,1): n = 5, L = {r['L']} = 2+√2/2, "
          f"0 overlaps, {r['gate']['contacts']} exact contacts")

    # 3. the side is the contact side: one nanometre below it the gate refuses
    st, ws, L = r["state"], r["words"], r["L"]
    short = [(x * (L - Q2(F(1, 10 ** 9))) / L, y * (L - Q2(F(1, 10 ** 9))) / L)
             for x, y in st]
    assert not Q.gate(short, ws)["ok"], "a shrunken box must be refused"
    print("  3. shrinking that box by 1e-9 of side is refused by the exact gate")

    # 4. the insertion rule is load-bearing: keeping the collided cells overlaps
    for (k1, k2, o, m) in ((2, 2, 1, 2), (3, 3, 0, 4)):
        kept, bar, L, dropped = assemble(k1, k2, o, m)
        assert dropped > 0, (k1, k2, o, m)
        xs = runs(k1, k2, o)
        full = [(x, y) for x in xs for y in xs]
        bad = Q.gate(full + bar, [AXIS] * len(full) + [W45] * len(bar))
        assert not bad["ok"], (k1, k2, o, m)
        print(f"  4.{k1}.{k2}.{o}.{m} drops {dropped} carrier cells; keeping them "
              f"gives {bad['violations']} overlapping pairs")

    # 5. the carrier is sparse: fill < 1 and at least two translation domains
    for (k1, k2, o, m) in ((1, 1, 0, 1), (2, 2, 1, 2), (2, 2, 1, 3), (3, 3, 0, 4)):
        r = check(k1, k2, o, m)
        fill = Q2(r["n"]) / (r["L"] * r["L"])
        dom = domains(r["state"], r["words"])
        assert fill < Q2(1), (k1, k2, o, m, fill)
        assert dom["axis"] >= 2 and dom["tilt"] == 1, dom
        print(f"  5.{k1}.{k2}.{o}.{m} n = {r['n']}, fill = {fill.decimal(4)} < 1, "
              f"domains axis {dom['axis']} / tilt {dom['tilt']}")

    # 6. containment, and the family's own refusal of a declaration that overfills
    for (k1, k2, o, m) in ((1, 1, 0, 1), (2, 2, 1, 2), (2, 2, 1, 3)):
        r = check(k1, k2, o, m)
        assert r["contained"] and r["ok"], (k1, k2, o, m, r["gate"])
        print(f"  6.{k1}.{k2}.{o}.{m} n = {r['n']}, L = {r['L']}, every cell "
              f"inside the box exactly")
    bad = check(2, 3, 1, 3)
    assert not bad["ok"] and bad["gate"]["violations"] > 0, bad["gate"]
    print(f"  6.refusal (2,3,1,3) is refused by the gate: "
          f"{bad['gate']['violations']} overlapping pairs")

    # 7. the exact side agrees with an independent 60-digit Decimal bbox
    for (k1, k2, o, m) in ((1, 1, 0, 1), (2, 2, 1, 2), (2, 2, 1, 3)):
        r = check(k1, k2, o, m)
        ex = [Q.frame_extent(*w) for w in r["words"]]
        dx = max(p[0] + e for p, e in zip(r["state"], ex)) - \
            min(p[0] - e for p, e in zip(r["state"], ex))
        assert dx == r["L"], (dx, r["L"])
        dec = Decimal(dx.a.numerator) / Decimal(dx.a.denominator) \
            + Decimal(dx.b.numerator) / Decimal(dx.b.denominator) * Decimal(2).sqrt()
        assert abs(dec - Decimal(r["L"].decimal(40))) < Decimal("1e-38"), dec
        print(f"  7.{k1}.{k2}.{o}.{m} exact side {r['L']} = {dec:.12f}")

    # 8. float-free decision path
    import exact_field as EF
    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  8. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")

    # 9. one counter, one gate: the batched counter agrees with `assemble`, and
    #    `check` reports exactly the raw gate's verdict (no second SAT path)
    assert "quick_ok" not in globals(), "the old pre-filter must be gone"
    for (k1, k2, o, m) in ((1, 1, 0, 1), (2, 2, 1, 2), (2, 2, 1, 3), (2, 3, 1, 3),
                           (3, 3, 0, 4), (5, 4, 2, 7)):
        counts, L = counts_for(k1, k2, o, [m - 1, m, m + 1], 1)
        kept, bar, L2, _d = assemble(k1, k2, o, m)
        assert L == L2 and counts[m] == len(kept) + m, (k1, k2, o, m, counts)
        r = check(k1, k2, o, m)
        g = Q.gate(kept + bar, [AXIS] * len(kept) + [W45] * len(bar))
        assert r["ok"] == (bool(g["ok"]) and r["contained"]), (k1, k2, o, m)
        print(f"  9.{k1}.{k2}.{o}.{m} counter n = {counts[m]} = assemble, "
              f"check ok = {r['ok']} = the raw gate's verdict")
    print("selftest OK (9 controls)")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
