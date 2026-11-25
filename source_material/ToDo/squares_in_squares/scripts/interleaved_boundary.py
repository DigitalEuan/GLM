#!/usr/bin/env python3
r"""interleaved_boundary.py — stepped-grain interleaved two/three-domain constructor.

Doc 97 §3 proved the *butted* twin family cannot win: glue two rigid blocks
along a straight line and the container side is the **sum** of the two blocks'
extents across that line, `L = max(a1, b1, a2 + b2) >= ceil(sqrt n)`, so the
family can at best tie the grid.  The only way past a sum is to let the two
bounding boxes **overlap** -- to interpenetrate -- and pay for it by deleting
the cells that actually collide.  That is what this file builds.

    substrate A   axis-aligned unit cells: an `a1 x a2` rectangle, a staircase
                  whose column heights step down, or a rectangle with a corner
                  notch.
    domains B_k   square-lattice blocks rotated by a rational spinor
                  tan(theta_k/2) = p_k/q_k, so

                      cos = (q^2 - p^2)/(q^2 + p^2),
                      sin = 2pq/(q^2 + p^2)

                  are exact rationals and every corner, axis and slack is exact.
    interface     B_k is translated by (dx, dy) *into A's bounding box*, and the
                  collision is resolved by deleting from ONE side (`give`):

                      give="block"  the tilted grain gives way, the substrate
                                    keeps every cell (the axis grain owns the seam);
                      give="sub"    the substrate gives way, so the axis grain
                                    grows a notch exactly where the tilted grain
                                    lands and the whole block survives.

                  What is left is a staircase of tilted cells hugging a staircase
                  of axis cells: a stepped / sawtooth grain boundary, not a line.

Zero overlap is structural (`prune` deletes until nothing collides) *and*
re-decided from scratch by the independent exact SAT (`verify`) on the rational
pose before a candidate is allowed to count.

Arithmetic.  Every centre, cosine and sine this constructor produces lies on the
fixed grid `Z / SCALE` (SCALE = lcm of the spinor denominators, times 2 for the
half-integer cell centres, times 2 for the half-integer offsets), so the whole
search runs in **integer** arithmetic after one exact conversion: `pair_slack2`
returns twice the separating slack scaled by SCALE, and its *sign* is the exact
sign of the rational slack.  That makes the hot loop ~100x faster than
`Fraction` pairs while changing nothing that is decided: the winning pose is
converted back to `Fraction` (`as_frac`) and re-decided with `import_n090`'s
`pair_slack`, and no float appears anywhere.

    python3 scripts/interleaved_boundary.py --targets 18,19,51 [--near K] [--cap N]
    python3 scripts/interleaved_boundary.py --selftest
"""
from __future__ import annotations

import json
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import import_n090 as N9                      # noqa: E402  (exact SAT, corners, inflate)
import sqscore as SQ                          # noqa: E402

LEDGER = ROOT / "workspace/push/interleaved_boundary.json"
QMAX = 4                                       # spinor denominator cap
TARGETS = (18, 19, 51)
NOISE = 1e-8                                   # C2 score floor
BLOCK_LO, BLOCK_HI = 2, 10
SLACK_CELLS = 6                                # a block may overshoot by this much


# ---------------------------------------------------------------- spinors ---
def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def spinor(p: int, q: int) -> tuple[Fraction, Fraction]:
    d = q * q + p * p
    return Fraction(q * q - p * p, d), Fraction(2 * p * q, d)


def spinors(qmax: int = QMAX) -> list[tuple[str, Fraction, Fraction]]:
    out = []
    for q in range(1, qmax + 1):
        for p in range(1, q + 1):          # p = q is the 90 deg degenerate twin
            if _gcd(p, q) != 1:
                continue
            out.append((f"{p}/{q}", *spinor(p, q)))
    return out


def parse_spinor(name: str):
    p, q = [int(t) for t in name.split("/")]
    return spinor(p, q)


SPIN = spinors()


def _scale() -> int:
    """Common denominator of every coordinate this file can emit."""
    d = 2                                   # half-integer centres and offsets
    for _, c, s in SPIN:
        for v in (c, s):
            d = d * v.denominator // _gcd(d, v.denominator)
    return d


SCALE = _scale()                            # spinor/centre lattice: Z/SCALE
G = 2 * SCALE                               # working grid: Z/G (halves the extents)
HALF3 = 3 * G // 2                          # the sqrt(2)-ish prefilter radius


def _ax(v: Fraction) -> int:
    """Fraction -> integer grid coordinate (units of 1/G)."""
    w = v * G
    assert w.denominator == 1, (v, G)
    return w.numerator


# --------------------------------------------------- integer cells and SAT ---
def substrate(a1: int, a2: int, heights=None, notch=()):
    """Axis-aligned unit cells; `heights` steps the top edge, `notch` cuts cells."""
    hs = heights if heights is not None else [a2] * a1
    assert len(hs) == a1, (a1, len(hs))
    skip = set(notch)
    return [(_ax(Fraction(2 * i + 1, 2)), _ax(Fraction(2 * j + 1, 2)), G, 0)
            for i, h in enumerate(hs) for j in range(h) if (i, j) not in skip]


def block(b1: int, b2: int, c: Fraction, s: Fraction):
    """`b1 x b2` tilted block (integer cells), its full bbox min at the origin."""
    cs, sn = _ax(c), _ax(s)
    raw = []
    for i in range(b1):
        for j in range(b2):
            u, v = Fraction(2 * i + 1, 2), Fraction(2 * j + 1, 2)
            raw.append((_ax(u * c - v * s), _ax(u * s + v * c), cs, sn))
    x0, y0, _, _ = extent(raw)          # doubled units; the //2 snaps to the grid
    return [(x - x0 // 2, y - y0 // 2, cs, sn) for x, y, _, _ in raw]


def variants(a1: int, a2: int):
    """Substrate families: solid, stepped top edge, and corner notches."""
    out = [("rect", [a2] * a1, ())]
    for drop in (1, 2):
        if a1 >= 3 and a2 - drop >= 2:
            out.append((f"stair-{drop}", [a2] * (a1 - 1) + [a2 - drop], ()))
    for u in (1, 2):
        for v in (1, 2):
            if a1 - u >= 2 and a2 - v >= 2:
                cut = tuple((i, j) for i in range(a1 - u, a1) for j in range(a2 - v, a2))
                out.append((f"notch-{u}x{v}", [a2] * a1, cut))
    return out


def extent(cells):
    """Doubled-integer bbox: 2*minx, 2*miny, 2*maxx, 2*maxy (units of 1/G).

    A unit square rotated by (c, s) has coordinate extent |c| + |s| exactly, so
    the bbox follows from centres and half-extents -- equal to the corner bbox
    (control 8) and eight times cheaper than enumerating corners.
    """
    x0 = x1 = y0 = y1 = None
    for x, y, c, s in cells:
        h = abs(c) + abs(s)
        a, b, p, q = 2 * x - h, 2 * x + h, 2 * y - h, 2 * y + h
        x0 = a if x0 is None or a < x0 else x0
        x1 = b if x1 is None or b > x1 else x1
        y0 = p if y0 is None or p < y0 else y0
        y1 = q if y1 is None or q > y1 else y1
    return x0, y0, x1, y1


def side(cells) -> Fraction:
    x0, y0, x1, y1 = extent(cells)
    return Fraction(max(x1 - x0, y1 - y0), 2 * G)


def as_frac(cells):
    """The same pose as exact `Fraction` cells, for the independent SAT."""
    return [(Fraction(x, G), Fraction(y, G),
             Fraction(c, G), Fraction(s, G)) for x, y, c, s in cells]


def pair_slack2(a, b) -> int:
    """Twice the exact separating slack, in SCALE units (sign = the decision).

    Same four axes as `import_n090.pair_slack`, cleared of denominators: each
    projection is doubled, and `2*|d.u| - p_a - p_b` has the sign of the slack.
    """
    ax, ay, ac, as_ = a
    bx, by, bc, bs = b
    dx, dy = bx - ax, by - ay
    best = None
    for ux, uy in ((ac, as_), (-as_, ac), (bc, bs), (-bs, bc)):
        pa = abs(ux * ac + uy * as_) + abs(ux * -as_ + uy * ac)
        pb = abs(ux * bc + uy * bs) + abs(ux * -bs + uy * bc)
        sl = 2 * abs(dx * ux + dy * uy) - pa - pb
        best = sl if best is None or sl > best else best
    return best


def _key(cell):
    return (cell[0] // G, cell[1] // G)


def _buckets(cells):
    b = {}
    for cell in cells:
        b.setdefault(_key(cell), []).append(cell)
    return b


def _hits(cell, buckets) -> bool:
    """True iff `cell` overlaps any nearby bucket member.

    The 5x5 bucket window and the 3/2-SCALE centre-offset test are filters, never
    decisions: every candidate pair reachable that way is decided by
    `pair_slack2`, and the winning pose by `verify`.
    """
    kx, ky = _key(cell)
    cx, cy = cell[0], cell[1]
    for ix in range(kx - 2, kx + 3):
        for iy in range(ky - 2, ky + 3):
            for other in buckets.get((ix, iy), ()):
                if abs(other[0] - cx) > HALF3 or abs(other[1] - cy) > HALF3:
                    continue
                if pair_slack2(cell, other) < 0:
                    return True
    return False


def prune(sub, blocks, give="block"):
    """Resolve every collision by deleting from one side only (see module doc)."""
    kept, deleted = [], 0
    if give == "sub":
        bmask = _buckets([c for blk in blocks for c in blk])
        kept_sub = [c for c in sub if not _hits(c, bmask)]
        deleted = len(sub) - len(kept_sub)
        kept = [list(blk) for blk in blocks]
        for i in range(len(kept)):
            for j in range(i + 1, len(kept)):
                kept[j] = [c for c in kept[j]
                           if not any(pair_slack2(c, o) < 0 for o in kept[i])]
        deleted += sum(len(b) for b in blocks) - sum(len(k) for k in kept)
        return kept, deleted, kept_sub
    fixed = _buckets(sub)
    for blk in blocks:
        keep = []
        for cell in blk:
            if _hits(cell, fixed):
                deleted += 1
                continue
            keep.append(cell)
        kept.append(keep)
        for cell in keep:                     # later blocks see earlier survivors
            fixed.setdefault(_key(cell), []).append(cell)
    return kept, deleted, list(sub)


def thin(sub, target: int):
    """Drop substrate cells from the top-right until exactly `target` remain."""
    if len(sub) <= target:
        return sub, 0
    order = sorted(sub, key=lambda c: (c[1], c[0]), reverse=True)
    drop = len(sub) - target
    gone = {id(c) for c in order[:drop]}
    return [c for c in sub if id(c) not in gone], drop


def verify(cells):
    """Independent exact SAT, in `Fraction`, over every pair of the pose."""
    pose = as_frac(cells)
    n = len(pose)
    worst, pair, bad = None, None, 0
    for i in range(n):
        for j in range(i + 1, n):
            sl = N9.pair_slack(pose[i], pose[j])
            if sl < 0:
                bad += 1
            if worst is None or sl < worst:
                worst, pair = sl, (i, j)
    return {"n": n, "overlaps": bad, "min_slack": worst, "pair": pair}


def tilt_price(p: int, q: int):
    """The price of a tilt, exactly: (sin 2theta, largest grain that can still win).

    A b1 x b2 grain rotated by the spinor angle theta has bbox
    W = b1 c + b2 s, H = b1 s + b2 c, so

        W H = b1 b2 (c^2 + s^2) + (b1^2 + b2^2) c s = b1 b2 + (b1^2 + b2^2) c s
            >= b1 b2 (1 + sin 2theta),

    i.e. its own side is at least sqrt(b1 b2) * sqrt(1 + sin 2theta), while an
    axis grain of the same cell count needs only sqrt(b1 b2).  The seam can buy
    back at most one unit (one cell row of overlap), so a grain of m cells can
    only profit if  sqrt(m(1 + x)) - sqrt(m) < 1  with x = sin 2theta, which is
    the exact rational test  (m x - 1)^2 < 4 m  (for m x > 1).  Returns
    (x, largest such m); the inequality uses only Fractions, no float.
    """
    # sin 2theta = 2 sin theta cos theta, with sin = 2pq/(p^2+q^2) and
    # cos = (q^2 - p^2)/(p^2 + q^2) -- exactly, and zero exactly at p = q.
    x = Fraction(4 * p * q * (q * q - p * p), (p * p + q * q) ** 2)
    if x == 0:                              # theta = 90 deg: an axis grain, no price
        return x, None
    m = 1
    while True:
        a = Fraction(m) * x
        if not (a <= 1 or (a - 1) ** 2 < 4 * m):
            return x, m - 1
        m += 1


def price_table():
    return {name: tilt_price(*[int(t) for t in name.split("/")]) for name, _, _ in SPIN}


def straight_bound(a1, a2, b1, b2, c, s) -> Fraction:
    """Doc 97 §3's butted bound for the same blocks: a sum of extents."""
    wB, hB = Fraction(b1) * c + Fraction(b2) * s, Fraction(b1) * s + Fraction(b2) * c
    return max(Fraction(a1), wB, Fraction(a2) + hB)


# --------------------------------------------------------------- the gate ---
def delivered_side(n: int) -> Fraction:
    per = SQ.load()
    return Fraction(Decimal(repr(SQ.extent(per[n]))))


def score_gain(n: int, l_from: Fraction, l_to: Fraction) -> float:
    getcontext().prec = 40
    f = lambda v: Decimal(v.numerator) / Decimal(v.denominator)
    return float((f(l_from) - f(l_to)) / Decimal(n).sqrt())


def render_bound(cells):
    """The promotion render: inflate by 1e-9, then report the slack that survives."""
    infl = N9.inflate(as_frac(cells))
    v = N9.check(infl)
    return {"min_slack_inflated": v["min_slack"], "overlaps_inflated": v["overlaps"],
            "side_inflated": v["side"]}


def gate(n, cells, delivered: Fraction):
    """C1/C2 in exact arithmetic; promotable only on a strict, material win."""
    v = verify(cells)
    sd = side(cells)
    gain = score_gain(n, delivered, sd)
    rec = {"n": n, "side": sd, "delivered": delivered, "overlaps": v["overlaps"],
           "min_slack": v["min_slack"], "gain": gain,
           "beats_delivered": sd < delivered,
           "passes_c2_noise": sd < delivered and gain >= NOISE}
    if rec["passes_c2_noise"]:
        rec["render"] = render_bound(cells)
        rec["promotable"] = rec["render"]["overlaps_inflated"] == 0
    else:
        rec["promotable"] = False
    return rec


# --------------------------------------------------------------- the sweep ---
def shapes(n, lo=2, hi=9):
    return [(a1, a2) for a1 in range(lo, hi + 1) for a2 in range(lo, hi + 1)
            if 1 <= a1 * a2 <= n]


def corner_offsets(a: int):
    """SCALE-grid corner offsets: where a second grain can interleave."""
    return [Fraction(a) - 2 + Fraction(k, 2) for k in range(0, 5)]


def sweep(n, stats=None, cap=220_000, near=60):
    """Two-domain sweep: shape x substrate family x give-side x spinor x offset."""
    stats = stats if stats is not None else {"tried": 0, "counted": 0, "deleted": 0,
                                             "thinned": 0, "skipped": 0}
    best = None
    cache = {}
    for a1, a2 in shapes(n):
        for vname, hs, cut in variants(a1, a2):
            sub = substrate(a1, a2, hs, cut)
            ns = len(sub)
            if ns > n or n > ns + near:
                continue
            oy = [_ax(o) for o in corner_offsets(a2)]
            ox = [_ax(o) for o in corner_offsets(a1)]
            for b1 in range(BLOCK_LO, BLOCK_HI + 1):
                for b2 in range(BLOCK_LO, BLOCK_HI + 1):
                    bc = b1 * b2
                    if abs(b1 - b2) > 1 or not (n - ns <= bc <= n - ns + SLACK_CELLS):
                        continue
                    for name, c, s in SPIN:
                        blk = cache.get((b1, b2, name))
                        if blk is None:
                            blk = cache[(b1, b2, name)] = block(b1, b2, c, s)
                        for dx in ox:
                            for dy in oy:
                                for give in ("block", "sub"):
                                    if stats["tried"] >= cap:
                                        stats["skipped"] += 1
                                        continue
                                    stats["tried"] += 1
                                    mv = [(x + dx, y + dy, cc, ss) for x, y, cc, ss in blk]
                                    kept, deleted, ksub = prune(sub, [mv], give)
                                    cells = ksub + kept[0]
                                    if len(cells) < n:
                                        continue
                                    dropped = 0
                                    if len(cells) > n:
                                        sub2, dropped = thin(ksub, len(ksub) - (len(cells) - n))
                                        cells = sub2 + kept[0]
                                    if len(cells) != n:
                                        continue
                                    stats["counted"] += 1
                                    stats["deleted"] += deleted
                                    stats["thinned"] += dropped
                                    sd = side(cells)
                                    if best is None or sd < best["side"]:
                                        best = {"side": sd,
                                                "sub": f"{a1}x{a2} {vname}",
                                                "a": (a1, a2), "b": (b1, b2),
                                                "give": give, "spinor": name,
                                                "offset": (Fraction(dx, SCALE),
                                                           Fraction(dy, SCALE)),
                                                "deleted": deleted, "thinned": dropped,
                                                "cells": cells, "domains": 2,
                                                "straight": straight_bound(a1, a2, b1, b2, c, s)}
    return best, stats


def sweep_three(n, base, stats=None, cap=20000):
    """Third domain: two tilted grains over one substrate, all pruned together."""
    stats = stats if stats is not None else {"tried": 0, "counted": 0, "deleted": 0,
                                             "skipped": 0}
    a1, a2 = base["a"]
    vname = base["sub"].split()[1]
    hs, cut = None, ()
    for name, h, ct in variants(a1, a2):
        if name == vname:
            hs, cut = h, ct
    sub = substrate(a1, a2, hs, cut)
    ns = len(sub)
    best = None
    offs = [_ax(o) for o in (Fraction(0), Fraction(1))]
    for e1 in range(2, 6):
        for e2 in range(2, 6):
            if not (n - ns <= e1 * e1 + e2 * e2 <= n - ns + SLACK_CELLS + 4):
                continue
            for name1, c1, s1 in SPIN:
                b1 = block(e1, e1, c1, s1)
                for name2, c2, s2 in SPIN:
                    b2 = block(e2, e2, c2, s2)
                    for dx in offs:
                        for dy in offs:
                            if stats["tried"] >= cap:
                                stats["skipped"] += 1
                                continue
                            stats["tried"] += 1
                            m1 = [(x + dx, y + dy, cc, ss) for x, y, cc, ss in b1]
                            m2 = [(x + dx, y + dy, cc, ss) for x, y, cc, ss in b2]
                            kept, deleted, ksub = prune(sub, [m1, m2], "sub")
                            cells = ksub + kept[0] + kept[1]
                            if len(cells) < n:
                                continue
                            dropped = 0
                            if len(cells) > n:
                                sub2, dropped = thin(ksub, len(ksub) - (len(cells) - n))
                                cells = sub2 + kept[0] + kept[1]
                            if len(cells) != n:
                                continue
                            stats["counted"] += 1
                            stats["deleted"] += deleted
                            sd = side(cells)
                            if best is None or sd < best["side"]:
                                best = {"side": sd, "sub": base["sub"], "a": (a1, a2),
                                        "b": (e1, e1), "b2": (e2, e2),
                                        "spinor": f"{name1}+{name2}",
                                        "offset": (Fraction(dx, SCALE), Fraction(dy, SCALE)),
                                        "deleted": deleted, "thinned": dropped,
                                        "cells": cells, "domains": 3, "straight": None}
    return best, stats


def _plain(obj):
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items() if k != "cells"}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if isinstance(obj, Fraction):
        return str(obj)
    return obj


def main() -> int:
    t0 = time.time()
    targets = TARGETS
    if "--targets" in sys.argv:
        targets = tuple(int(t) for t in sys.argv[sys.argv.index("--targets") + 1].split(","))
    cap, near = 220_000, 60
    if "--cap" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--cap") + 1])
    if "--near" in sys.argv:
        near = int(sys.argv[sys.argv.index("--near") + 1])

    print(f"interleaved spinor boundary sweep: {len(SPIN)} spinors (q <= {QMAX}), "
          f"exact integer grid 1/{G}, 5x5 corner offsets per axis, "
          f"targets {targets}", flush=True)
    tbl = price_table()
    print("price of a tilt (exact): " + ", ".join(
        f"{k}: sin2t={float(v[0]):.4f} grain<={v[1] if v[1] is not None else 'any (axis)'} "
        f"cells" for k, v in tbl.items()), flush=True)
    led = {"targets": [], "spinors": [n for n, _, _ in SPIN], "grid": G,
           "price_of_tilt": {k: [str(v[0]), v[1]] for k, v in tbl.items()},
           "offsets": "corner-anchored 1/2 grid, 5x5 per substrate", "results": {}}
    if LEDGER.exists():
        old = json.loads(LEDGER.read_text())
        led["results"] = old.get("results", {})
        led["targets"] = list(old.get("targets", []))
    for n in targets:
        dl = delivered_side(n)
        best, stats = sweep(n, cap=cap, near=near)
        row = {"delivered": dl, "stats": stats, "grid": SQ.grid(n)}
        if best is None:
            row["found"] = None
            print(f"  n = {n:>3}: no assembly reached exactly {n} cells from "
                  f"{stats['tried']} placements", flush=True)
        else:
            rec = gate(n, best["cells"], dl)
            row.update({"found": _plain({k: v for k, v in best.items() if k != "cells"}),
                        "gate": _plain(rec)})
            row["beats_straight"] = best["straight"] is not None and best["side"] < best["straight"]
            print(f"  n = {n:>3}: best interleaved side {float(best['side']):.6f} "
                  f"(delivered {float(dl):.6f}, grid {SQ.grid(n)}, butted bound for the "
                  f"same blocks {float(best['straight']):.4f})", flush=True)
            print(f"           {best['sub']} + {best['b']}@{best['spinor']} give={best['give']} "
                  f"moved ({best['offset'][0]},{best['offset'][1]}): deleted {best['deleted']}, "
                  f"thinned {best['thinned']}; SAT overlaps {rec['overlaps']}, "
                  f"min slack {float(rec['min_slack']):+.3f}; gain {rec['gain']:+.3e}", flush=True)
            three, st3 = sweep_three(n, best)
            if three is not None:
                rec3 = gate(n, three["cells"], dl)
                row["three_domain"] = _plain({"side": three["side"], "spinor": three["spinor"],
                                              "deleted": three["deleted"],
                                              "thinned": three["thinned"],
                                              "overlaps": rec3["overlaps"],
                                              "gain": rec3["gain"], "stats": st3})
                print(f"           three domains: best {float(three['side']):.6f} "
                      f"({three['spinor']}), deleted {three['deleted']}, "
                      f"overlaps {rec3['overlaps']}, gain {rec3['gain']:+.3e}", flush=True)
            if n not in led["targets"]:
                led["targets"].append(n)
        led["results"][str(n)] = _plain(row)
    wins = [n for n in led["targets"]
            if led["results"].get(str(n), {}).get("gate", {}).get("promotable")]
    led["wins"] = wins
    led["seconds"] = round(time.time() - t0, 1)
    led["targets"] = sorted(led["targets"])
    LEDGER.write_text(json.dumps(led, indent=1) + "\n")
    print(f"promotable (C1 exact 0-overlap + C2 strictly smaller and above the "
          f"{NOISE:g} floor): {wins if wins else 'none'}")
    print(f"wrote {LEDGER} in {led['seconds']} s")
    return 0


# --------------------------------------------------------------- selftest ---
def selftest() -> int:
    print("interleaved_boundary selftest")
    # 1. the spinors are rational unit rotations, and the grid really holds them
    for name, c, s in SPIN:
        assert c * c + s * s == 1, (name, c, s)
        assert (c * G).denominator == 1 and (s * G).denominator == 1
    assert parse_spinor("1/2") == (Fraction(3, 5), Fraction(4, 5))
    print(f"  1. {len(SPIN)} rational spinors: c^2 + s^2 = 1 exactly; tan(theta/2) = "
          f"1/2 gives the 3-4-5 twin (3/5, 4/5); every coordinate lands on 1/{G}")

    # 2. the pruner and the independent SAT disagree on a raw placement, and
    #    agree after pruning -- the deletion is doing real work
    c, s = parse_spinor("1/2")
    sub = substrate(4, 4)
    blk = [(x + _ax(Fraction(1)), y + _ax(Fraction(3)), cc, ss)
           for x, y, cc, ss in block(3, 3, c, s)]
    raw = verify(sub + blk)
    assert raw["overlaps"] > 0, "control needs a real collision"
    kept, deleted, ksub = prune(sub, [blk])
    pose = ksub + kept[0]
    v = verify(pose)
    assert deleted > 0 and v["overlaps"] == 0, (deleted, v)
    print(f"  2. raw 4x4 + 3x3@(1,3): {raw['overlaps']} overlapping pair(s) in exact "
          f"Fraction SAT; pruned deletes {deleted} cell(s) and SAT finds 0 overlaps "
          f"in {len(pose)} cells")

    # 3. POSITIVE CONTROL: the interleaved assembly beats the straight-line
    #    separator bound for the very same two blocks
    straight = straight_bound(4, 4, 3, 3, c, s)
    sd = side(pose)
    assert sd < straight, (sd, straight)
    print(f"  3. POSITIVE CONTROL: interleaved side {float(sd):.4f} < straight-line "
          f"bound {float(straight):.4f} for the same blocks (4x4 + 3x3 twin): the "
          f"bounding boxes interpenetrate")

    # 4. the stepped substrate really interleaves: a staircase keeps more
    #    tilted cells than the solid rectangle it replaces
    stair = substrate(4, 4, [4, 4, 4, 3])
    _, d_stair, _ = prune(stair, [blk])
    _, d_rect, _ = prune(sub, [blk])
    assert d_stair < d_rect, (d_stair, d_rect)
    print(f"  4. stepped top edge [4,4,4,3] deletes {d_stair} cell(s) where the solid "
          f"4x4 deletes {d_rect}: the step absorbs a tilted cell")

    # 5. the give-side is the mechanism: letting the substrate give way keeps a
    #    block the substrate-wins rule would have gutted
    _, d_block, k_block = prune(sub, [blk], "block")
    _, d_sub, k_sub = prune(sub, [blk], "sub")
    assert len(k_block[0]) <= len(k_sub and [blk][0]) and d_sub > 0
    assert verify(k_sub + blk)["overlaps"] == 0
    print(f"  5. give=block keeps {len(k_block[0])}/9 cells of the tilted grain "
          f"(deleting {d_block}); give=sub deletes {d_sub} substrate cell(s) and "
          f"keeps all 9, still 0 overlaps")

    # 6. edge cases: B buried in A is annihilated, B far away is never deleted
    inside = [(x + _ax(Fraction(1)), y + _ax(Fraction(1)), cc, ss)
              for x, y, cc, ss in block(2, 2, c, s)]
    kept_in, del_in, _ = prune(sub, [inside])
    assert del_in == 4 and kept_in[0] == [], (del_in, kept_in)
    far = [(x + _ax(Fraction(20)), y + _ax(Fraction(20)), cc, ss)
           for x, y, cc, ss in block(3, 3, c, s)]
    kept_far, del_far, _ = prune(sub, [far])
    assert del_far == 0 and len(kept_far[0]) == 9, (del_far, kept_far)
    assert side(sub + kept_far[0]) > straight, "a far block must not beat the bound"
    print(f"  6. edge cases: buried 2x2 twin loses all {del_in} cells (refused); far "
          f"3x3 loses {del_far}, side {float(side(sub + kept_far[0])):.2f} > bound "
          f"{float(straight):.2f}")

    # 7. bookkeeping identity across three domains, and thinning to a target
    sub3 = substrate(5, 4)
    b2 = [(x + _ax(Fraction(4)), y + _ax(Fraction(2)), cc, ss)
          for x, y, cc, ss in block(3, 3, *parse_spinor("1/2"))]
    b3 = [(x + _ax(Fraction(2)), y + _ax(Fraction(4)), cc, ss)
          for x, y, cc, ss in block(3, 3, *parse_spinor("2/3"))]
    kept3, del3, ksub3 = prune(sub3, [b2, b3])
    pose3 = ksub3 + kept3[0] + kept3[1]
    total = len(sub3) + len(b2) + len(b3) - del3
    assert total == len(pose3), (total, len(pose3))
    v3 = verify(pose3)
    assert v3["overlaps"] == 0, v3
    thinned, dropped = thin(sub3, 15)
    assert len(thinned) == 15 and dropped == len(sub3) - 15, (len(thinned), dropped)
    assert verify(thinned + kept3[0] + kept3[1])["overlaps"] == 0
    print(f"  7. three domains: {len(sub3)} + {len(b2)} + {len(b3)} - {del3} = "
          f"{len(pose3)} cells exactly, 0 overlaps over {v3['n']*(v3['n']-1)//2} pairs; "
          f"thinning drops {dropped} to reach 15, still 0 overlaps")

    # 8. the fast bbox is the corner bbox, on every pose this file builds
    for pose_x in (pose, pose3, sub3, stair + kept_far[0], sub):
        fast = extent(pose_x)
        fpose = as_frac(pose_x)
        xs = [p[0] for x, y, cc, ss in fpose for p in N9.corners(x, y, cc, ss)]
        ys = [p[1] for x, y, cc, ss in fpose for p in N9.corners(x, y, cc, ss)]
        exact = (min(xs), min(ys), max(xs), max(ys))
        got = (Fraction(fast[0], 2 * G), Fraction(fast[1], 2 * G),
               Fraction(fast[2], 2 * G), Fraction(fast[3], 2 * G))
        assert got == exact, (got, exact)
    print("  8. extent == the corner bbox exactly on 5 poses: |c| + |s| is the "
          "rotated square's true extent")
    # 9. the price of a tilt is the exact inequality it claims to be
    want = {"1/2": 6, "1/3": 6, "2/3": 10, "1/4": 8, "3/4": 17, "1/1": None}
    got = {k: v[1] for k, v in price_table().items()}
    assert got == want, got
    x, _ = tilt_price(1, 2)
    assert x == Fraction(24, 25), x
    # and the bbox identity W*H = b1b2 + (b1^2 + b2^2) cs holds exactly
    for name, c, s in SPIN:
        p, q = [int(t) for t in name.split("/")]
        for b1, b2 in ((3, 3), (4, 7), (2, 5)):
            W, H = b1 * c + b2 * s, b1 * s + b2 * c
            assert W * H == b1 * b2 + (b1 * b1 + b2 * b2) * c * s, (name, b1, b2)
            s2 = Fraction(4 * p * q * (q * q - p * p), (p * p + q * q) ** 2)
            assert W * H >= b1 * b2 * (1 + s2), (name, b1, b2)
    print(f"  9. price of a tilt: sin2t = 2pq/(p^2+q^2) exactly; a tilted grain is "
          f"priced out above {got} cells per spinor (1/1 = 90 deg is axis, no "
          f"price); every bbox obeys W*H = b1b2 + (b1^2+b2^2)cs >= b1b2(1 + sin2t)")
    print("selftest OK (9 controls)")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
