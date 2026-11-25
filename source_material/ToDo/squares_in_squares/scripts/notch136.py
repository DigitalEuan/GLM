#!/usr/bin/env python3
r"""notch136.py — run 136: the two real corner notches, measured and priced.

Doc 75 left two structural openings in the table, and this is the run that goes
at both:

    k = 23   frontier n = 509 at L = 22.989777095, hole 0.7534 (price +0.530 unit^2)
    k = 32   frontier n = 998 at L = 31.986238620, hole 0.8394 (price +0.120 unit^2)

(the k = 32 figure is run 117's finer scan; doc 75 §3's 0.7171 was a coarse-grid
underestimate).  Both are *corner* notches: a genuine square hole, not a
squashed cell, which is why they are the only two bands where the frontier
pose's free space is a shape rather than a sliver.

A beat here means one legal cell inside the frontier pose's own bounding box:
the frontier side is already below `k`, so `n = 510` (or `999`) at any side
strictly below `k` inherits the frontier and beats the row.  Run 116/117 tried
this by *penalty descent* and by *single-cell exact slides + patch descent*, and
stalled at 6 violations with a 9.4e-2 bite.  What they did not do — and what
this run does — is ask the geometric question first:

    1. how big is the hole, exactly, and which cells bound it?
    2. how much *legal room* does every cell in the notch's neighbourhood have?
       (run 134 measured the delivered *beaten* rows' wall sets at <= 4.2e-10;
        the frontier poses have real slivers, so this is a different question)
    3. what is the crack worth, in score, exactly?

Answer 3 is the one that matters for where the budget goes, and it is computed
here before any search is spent: `row_score(n+1, L)` against the delivered
`L(n+1)`.

Everything that decides anything is exact (`Decimal` at 40 digits via
`p_screen.measure`, and `legal_slide`'s exact gate for moves); the free-square
scan is float discovery (`void_insert.hmax_scan` + `refine`, the instruments doc
75 and 117 used), and its finding is turned into an exact statement by placing
the cell and measuring the penetration it actually causes.

    python3 scripts/notch136.py --diagnose     # hole + neighbourhood + prize
    python3 scripts/notch136.py --room         # exact legal room, per cell
    python3 scripts/notch136.py --insert       # place the cell, gate it exactly
    python3 scripts/notch136.py --selftest
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from decimal import Decimal, getcontext

getcontext().prec = 45

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import legal_slide as LSL                # noqa: E402
import p_screen as PS                    # noqa: E402
import sqscore as SQ                     # noqa: E402
import void_insert as VI                 # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/notch136.json")
CSV = os.path.join(ROOT, "workspace/submission/submission.csv")

# Frame note (settled by measurement, run 136): `workspace/submission/table.json`
# stores each pose at its *construction* orientation, but the scored CSV holds it
# rotated to the orientation with the smallest axis-aligned bbox — for n = 509 the
# table pose's extent is 22.9935885 while the CSV pose's is 22.9897771 (= the
# table's own `L` field, = the certified side).  The container *is* that
# axis-aligned bbox (`sqscore.extent`), so every geometric statement about a notch
# has to be made in the delivered frame.  These loaders therefore read the CSV.

#: (k, frontier n, next row n, doc-75 hole side)
BANDS = ((23, 509, 510, 0.7534), (32, 998, 999, 0.8394))


def _csv_rows():
    with open(CSV) as f:
        out = {}
        for r in csv.DictReader(f):
            out.setdefault(int(r["n"]), []).append((r["x"], r["y"], r["angle"]))
    return out


_CSV_CACHE = {}


def pose_strings(n: int):
    """The delivered pose of row n, as exact decimal strings, in frame order."""
    if not _CSV_CACHE:
        _CSV_CACHE.update(_csv_rows())
    return list(_CSV_CACHE[n])


def table_side(n: int) -> str:
    """The delivered side of row n: `sqscore.extent` of the delivered pose."""
    st = [(float(x), float(y), float(t)) for x, y, t in pose_strings(n)]
    return str(SQ.extent(st))


def exact_measure(pose):
    """40-digit side, violations and exact depth of a pose (the judge)."""
    m = PS.measure(pose)
    return {"side": str(m["side"]), "p": str(m["p"]),
            "violations": m["violations"], "worst_pair": m.get("worst_pair")}


def hole(n: int, grid=100, angles=17, rounds=6):
    """Free square of the delivered pose: side, centre, angle (float discovery)."""
    x, y, t = csv_arrays(n)
    st, box = VI.hmax_scan(x, y, t, grid=grid, angles=angles)
    h, cx, cy, th = VI.refine(x, y, t, st, box, rounds=rounds)
    # `hfield` returns the HALF-size: at a wall the maximum equals the wall
    # distance exactly (0.3576 at the n = 998 wall notch), so the free square's
    # side is 2h — which is what doc 75's 0.7171/0.8394 and doc 117 report.
    return {"h": float(h), "side": 2.0 * float(h), "cx": float(cx),
            "cy": float(cy), "theta": float(th)}, box


def csv_arrays(n: int):
    st = pose_strings(n)
    x = np.array([float(r[0]) for r in st])
    y = np.array([float(r[1]) for r in st])
    t = np.array([float(r[2]) for r in st])
    return x, y, t


def bounders(n: int, cx: float, cy: float, reach: float = 2.5):
    """Cells whose exact slack to the hole centre is the smallest (the binders)."""
    x, y, t = csv_arrays(n)
    d = np.maximum(np.abs(x - cx), np.abs(y - cy))
    idx = np.argsort(d)[:12]
    return [{"i": int(i), "x": float(x[i]), "y": float(y[i]), "t": float(t[i]),
             "cheb": float(d[i])} for i in idx]


def legal_room(n: int, idx, dirs=((1, 0), (-1, 0), (0, 1), (0, -1)), cap=0.25):
    """Largest legal translation of cell `idx` along each axis (float bisection).

    Local: only pairs with the cell's neighbours (Chebyshev distance < 2.6) are
    tested, which is sound because a unit cell cannot touch anything further
    away in one move of <= cap.  Discovery only; the useful value is re-gated
    exactly below.
    """
    x, y, t = csv_arrays(n)
    xi, yi, ti = x[idx], y[idx], t[idx]
    near = np.nonzero(np.maximum(np.abs(x - xi), np.abs(y - yi)) < 2.6)[0]
    near = near[near != idx]
    out = {}
    for dx, dy in dirs:
        lo, hi = 0.0, cap
        ok = lambda s: float(VI.pen_vec(xi + dx * s, yi + dy * s, ti,  # noqa: E731
                                       x[near], y[near], t[near], eps=0.0).max()) <= 1e-12
        if not ok(lo):
            out[f"{dx},{dy}"] = 0.0
            continue
        if ok(hi):
            out[f"{dx},{dy}"] = cap
            continue
        for _ in range(40):
            mid = (lo + hi) / 2
            if ok(mid):
                lo = mid
            else:
                hi = mid
        out[f"{dx},{dy}"] = float(lo)
    return out


def slab_room(n: int, hl: dict, axis: int, side: int, depth: float = 1.6,
              tang: float = 2.6, cap: float = 0.5) -> dict:
    """Joint legal migration of the slab facing the hole, *away* from it.

    Single-cell room cannot see a band that moves as a rigid body: a row of cells
    locked against its neighbours one by one can still be free as a group if the
    freedom is shared.  This measures the largest common displacement `d` of all
    cells whose centre lies beyond the hole's `axis` boundary (within `tang`
    transversally) and that can move `d` without penetrating the complement.
    Discovery (float), with the extent consequence reported alongside.
    """
    x, y, t = csv_arrays(n)
    cx, cy, h = hl["cx"], hl["cy"], hl["h"]
    if axis == 0:
        along, across, c0, ac = x, y, cx, cy
    else:
        along, across, c0, ac = y, x, cy, cx
    mask = ((along - c0) * side > h - 1e-9) & (np.abs(across - ac) <= tang) \
        & (np.abs(along - c0) <= h + depth)
    idx = np.nonzero(mask)[0]
    if len(idx) == 0 or len(idx) == n:
        return {"axis": axis, "side": side, "cells": int(len(idx)), "room": 0.0}
    oth = np.nonzero(~mask)[0]
    d = np.zeros(2)
    d[axis] = float(side)
    # pen_vec is element-wise: build the |idx| x |oth| pair list explicitly
    A = np.repeat(idx, len(oth))
    B = np.tile(oth, len(idx))
    ok = lambda s: float(VI.pen_vec(x[A] + d[0] * s, y[A] + d[1] * s, t[A],  # noqa: E731
                                   x[B], y[B], t[B], eps=0.0).max()) <= 1e-12
    if not ok(0.0):
        return {"axis": axis, "side": side, "cells": int(len(idx)), "room": 0.0,
                "note": "slab not separable at d=0"}
    if ok(cap):
        room = cap
    else:
        lo, hi = 0.0, cap
        for _ in range(36):
            mid = (lo + hi) / 2
            if ok(mid):
                lo = mid
            else:
                hi = mid
        room = float(lo)
    ext = SQ.extent([(x[i] + d[0] * room, y[i] + d[1] * room, t[i]) for i in idx]
                    + [(x[i], y[i], t[i]) for i in oth])
    return {"axis": axis, "side": side, "cells": int(len(idx)), "room": room,
            "extent_after": ext, "extent0": SQ.extent(list(zip(x, y, t)))}


def prize(k: int, n_next: int, L_frontier: str, L_next: str) -> dict:
    """Exact score value of a beat at row n_next, at the frontier side.

    The row score is `L/sqrt(n) - 1` (`sqscore.row_score`), computed here in
    `Decimal` at 40 digits so the gain is exact; the float form agrees to 1e-15.
    """
    root = Decimal(n_next).sqrt()
    here = Decimal(L_next) / root - 1
    cand = Decimal(L_frontier) / root - 1
    rec = {"row": n_next, "k": k, "L_delivered": str(L_next),
           "L_candidate": str(L_frontier),
           "score_delivered": str(here), "score_candidate": str(cand),
           "gain": str(here - cand), "gain_if_31_9968": None}
    if k == 32:
        near = Decimal("31.99687596003605622186")
        rec["gain_if_31_9968"] = str(here - (near / root - 1))
    assert abs(float(here) - SQ.row_score(n_next, float(L_next))) < 1e-15
    return rec


def diagnose(bands=BANDS) -> list:
    out = []
    for k, n, nxt, doc_hole in bands:
        t0 = time.monotonic()
        hl, box = hole(n)
        L_front = table_side(n)
        L_next = table_side(nxt)
        rec = {"k": k, "n": n, "next": nxt,
               "L_frontier": L_front, "L_next": L_next,
               "hole": hl, "hole_side_doc75": doc_hole,
               "short_of_a_cell": 1.0 - hl["side"],
               "bounders": bounders(n, hl["cx"], hl["cy"]),
               "prize": prize(k, nxt, L_front, L_next),
               "seconds": round(time.monotonic() - t0, 1)}
        print(f"[k={k}] n={n}: L={L_front[:14]} hole side {hl['side']:.4f} "
              f"(doc 75: {doc_hole}), short {1.0 - hl['side']:.4f}; "
              f"row {nxt} at {L_next[:14]} -> prize "
              f"{Decimal(rec['prize']['gain']):.3e} ({rec['seconds']}s)", flush=True)
        out.append(rec)
    return out


def room(bands=BANDS, top=6) -> list:
    """Legal room of the cells nearest each notch's hole."""
    out = []
    for k, n, _nxt, _h in bands:
        hl, _box = hole(n, grid=84, angles=13, rounds=4)
        b = bounders(n, hl["cx"], hl["cy"])[:top]
        for rec in b:
            rec["room"] = legal_room(n, rec["i"])
            rec["max_room"] = max(rec["room"].values())
        best = max(b, key=lambda r: r["max_room"])
        out.append({"k": k, "n": n, "hole": hl, "cells": b,
                    "max_room": best["max_room"], "at": best["i"],
                    "free": bool(best["max_room"] >= 0.08)})
        print(f"[k={k}] n={n}: max legal room in the notch neighbourhood "
              f"{best['max_room']:.3e} (cell {best['i']}) -> "
              f"{'FREE' if out[-1]['free'] else 'LOCKED'}", flush=True)
    return out


def insert(n: int, hl: dict, angles=(0.0, math.pi / 4), tag="") -> dict:
    """Place one unit cell at the hole centre and gate the result exactly."""
    pose = pose_strings(n)
    out = []
    for th in angles:
        cand = pose + [(repr(float(hl["cx"])), repr(float(hl["cy"])), repr(float(th)))]
        m = exact_measure(cand)
        out.append({"theta": th, "side": m["side"], "violations": m["violations"],
                    "p": m["p"], "worst_pair": m["worst_pair"]})
        print(f"  n={n + 1} cell at ({hl['cx']:.6f},{hl['cy']:.6f}) theta={th:.4f}: "
              f"side {m['side'][:14]} violations {m['violations']} depth {Decimal(m['p']):.3e}",
              flush=True)
    return {"n": n, "next": n + 1, "holes": hl, "attempts": out, "tag": tag}


def selftest() -> int:
    """Three controls: the prize arithmetic, the frontier side, the hole scan."""
    # 1. the prize is sqscore arithmetic, checked on a known row
    k, n, nxt, _ = BANDS[1]
    p = prize(k, nxt, table_side(n), table_side(nxt))
    assert Decimal(p["gain"]) > 0
    print(f"  1. prize arithmetic on row {nxt}: delivered "
          f"{Decimal(p['score_delivered']):.12f} vs frontier side "
          f"{Decimal(p['score_candidate']):.12f} -> {Decimal(p['gain']):.3e}")

    # 2. the frontier poses are legal at their delivered side, exactly
    for k2, n2, _n2, _h2 in BANDS:
        m = exact_measure(pose_strings(n2))
        assert m["violations"] == 0, (n2, m["violations"])
        print(f"  2. n={n2}: {len(pose_strings(n2))} cells, 0 violations at "
              f"L={m['side'][:16]}")

    # 3. the scan finds a real hole, and it is short of a cell
    hl, _box = hole(BANDS[1][1], grid=84, angles=13, rounds=4)
    assert 0.5 < hl["side"] < 1.0, hl
    print(f"  3. k=32 hole side {hl['side']:.4f} at ({hl['cx']:.4f},{hl['cy']:.4f}), "
          f"{1.0 - hl['side']:.4f} short of a unit cell")
    print("  selftest OK (3 controls)")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    rec = {}
    if os.path.exists(OUT):
        try:
            with open(OUT) as f:
                rec = json.load(f)
        except (OSError, ValueError):
            rec = {}
    if "--diagnose" in argv or not argv:
        rec["diagnose"] = diagnose()
    if "--room" in argv:
        rec["room"] = room()
    if "--strips" in argv:
        rec["strips"] = []
        for i, (k, n, _x, _h) in enumerate(BANDS):
            hl = rec["diagnose"][i]["hole"] if rec.get("diagnose") else hole(n)[0]
            for axis in (0, 1):
                for side in (1, -1):
                    r = slab_room(n, hl, axis, side)
                    r.update({"k": k, "n": n})
                    rec["strips"].append(r)
                    print(f"[k={k}] slab axis={'xy'[axis]} side={side:+d} "
                          f"cells={r['cells']:4d} room={r['room']:.3e} "
                          f"extent {r.get('extent0', 0):.6f} -> {r.get('extent_after', 0):.6f}",
                          flush=True)
    if "--insert" in argv:
        rec["insert"] = [insert(n, rec["diagnose"][i]["hole"], tag="axis+45")
                         for i, (k, n, _x, _h) in enumerate(BANDS)
                         if rec.get("diagnose")]
    rec["schema"] = "notch136/1"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=1, default=str)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
