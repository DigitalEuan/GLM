#!/usr/bin/env python3
r"""polish_ceiling.py — run 117: the *measured* polish ceiling on a sample of the
553 beaten rows, by the hard-projection repair itself.

`polish_pricing.py` priced a 1 % capture against run 111's legal-gap band.  That
was an argument by comparison.  This measures the same thing directly: take a
row's delivered pose, shrink the container by `delta`, clamp every cell into the
smaller box (a hard projection — the side constraint is never a penalty), run the
contact-graph repair, and ask at 40 digits whether the pose closes with zero
overlap.  The largest `delta` that closes is that row's ceiling; the sum over the
table is the empirical ceiling of the polish campaign.

The sample is stratified: every third of the capture range, across the bands.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ            # noqa: E402
import true_geom as TG          # noqa: E402
from notch32 import violations, clamp, repair, score   # noqa: E402
from void_insert import load_pose                      # noqa: E402

DELTAS = ("0.00003", "0.0001", "0.00033")
OUT = os.path.join(ROOT, "workspace/push/polish_ceiling117.json")


def sample(k=12):
    """A stratified sample of beaten rows: by capture `e`, spread over the bands."""
    per = SQ.load()
    rows = []
    for n in range(2, 1001):
        kk = SQ.grid(n)
        L = SQ.extent(per[n])
        if L >= kk - 1e-12:
            continue
        r = kk - math.sqrt(n)
        rows.append((n, kk, L, (kk - L) / r))
    rows.sort(key=lambda t: (t[3], t[0]))
    step = max(1, len(rows) // k)
    return [rows[i] for i in range(0, len(rows), step)][:k]


def _box(x, y, t, delta):
    h = 0.5 * (np.abs(np.cos(t)) + np.abs(np.sin(t)))
    xlo, xhi = float((x - h).min()), float((x + h).max())
    ylo, yhi = float((y - h).min()), float((y + h).max())
    return (xlo + delta / 2.0, xhi - delta / 2.0,
            ylo + delta / 2.0, yhi - delta / 2.0)


def shrink_boundary(x, y, t, delta):
    """Boundary-only clamp: move only the cells that protrude past a wall.

    The whole-box clamp of `shrink_once` is the worst case for a tight pose —
    every cell is pushed inward, so every contact is broken at once.  This
    control shrinks the box by `delta` and translates only the cells whose
    bounding box now crosses a wall, each by the exact minimal amount, and leaves
    every interior cell where it is.  Then the same repair runs.
    """
    lo_x, hi_x, lo_y, hi_y = _box(x, y, t, delta)
    h = 0.5 * (np.abs(np.cos(t)) + np.abs(np.sin(t)))
    X = np.array(x, dtype=float)
    Y = np.array(y, dtype=float)
    for i in range(len(X)):
        if X[i] - h[i] < lo_x:
            X[i] += lo_x - (X[i] - h[i])
        elif X[i] + h[i] > hi_x:
            X[i] -= (X[i] + h[i]) - hi_x
        if Y[i] - h[i] < lo_y:
            Y[i] += lo_y - (Y[i] - h[i])
        elif Y[i] + h[i] > hi_y:
            Y[i] -= (Y[i] + h[i]) - hi_y
    return X, Y


def shrink_once(x, y, t, delta):
    """Clamp the pose into a box `delta` smaller than its own, then repair."""
    lo_x, hi_x, lo_y, hi_y = _box(x, y, t, delta)
    X, Y = clamp(np.array(x, dtype=float), np.array(y, dtype=float), t,
                 min(lo_x, lo_y), max(hi_x, hi_y))
    X, Y, T = repair(X, Y, t, min(lo_x, lo_y), max(hi_x, hi_y),
                     passes=24, top=8)
    rows = [(repr(float(a)), repr(float(b)), repr(float(c)))
            for a, b, c in zip(X, Y, T)]
    chk = TG.check(rows)
    return chk, score(X, Y, T)


def boundary_once(x, y, t, delta):
    """The boundary-only control: move the protruding cells, then repair."""
    lo_x, hi_x, lo_y, hi_y = _box(x, y, t, delta)
    X, Y = shrink_boundary(x, y, t, delta)
    lo, hi = min(lo_x, lo_y), max(hi_x, hi_y)
    X, Y, T = repair(X, Y, t, lo, hi, passes=24, top=8)
    rows = [(repr(float(a)), repr(float(b)), repr(float(c)))
            for a, b, c in zip(X, Y, t)]
    chk = TG.check(rows)
    return chk, score(X, Y, T)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    boundary = "--control" in argv and "boundary" in argv
    per = SQ.load()
    records = []
    for n, k, L, e in sample():
        x, y, t = load_pose(n)
        L0 = SQ.extent(per[n])
        cell = {"n": n, "k": k, "L": L0, "e": e, "deltas": {}}
        for ds in DELTAS:
            d = float(ds)
            chk, sc = boundary_once(x, y, t, d) if boundary else shrink_once(x, y, t, d)
            cell["deltas"][ds] = {
                "violations40": len(chk["violations"]),
                "worst40": str(chk["worst"]) if chk["worst"] is not None else None,
                "side40": str(chk["side"]),
                "closed": len(chk["violations"]) == 0,
                "needed": d / math.sqrt(n),
            }
            print(f"  n={n:4d} k={k:2d} delta={ds}: viol40="
                  f"{len(chk['violations']):3d} side40={chk['side']}", flush=True)
        closed = [float(ds) for ds in DELTAS if cell["deltas"][ds]["closed"]]
        cell["ceiling"] = max(closed) if closed else 0.0
        records.append(cell)
        print(f"    -> ceiling {cell['ceiling']:.5f}  (e = {e:.3f})", flush=True)

    per_row = [r["ceiling"] for r in records]
    med = sorted(per_row)[len(per_row) // 2]
    # extrapolate: the same median ceiling on every beaten row
    beaten = [n for n in range(2, 1001) if SQ.extent(per[n]) < SQ.grid(n) - 1e-12]
    total = sum(med / math.sqrt(n) for n in beaten)
    print(f"\n  sample ceilings: min {min(per_row):.5f} median {med:.5f} "
          f"max {max(per_row):.5f}")
    print(f"  extrapolated to all {len(beaten)} beaten rows at the median: "
          f"+{total:.5f} score")
    out = OUT.replace(".json", "_boundary.json") if boundary else OUT
    rec = {"control": "boundary-only" if boundary else "whole-box",
           "deltas": DELTAS, "rows": records, "median_ceiling": med,
           "extrapolated": total, "n_beaten": len(beaten)}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rec, open(out, "w"), indent=1)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
