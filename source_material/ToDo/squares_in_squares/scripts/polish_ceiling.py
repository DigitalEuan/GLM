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


def shrink_once(x, y, t, delta):
    """Clamp the pose into a box `delta` smaller than its own, then repair."""
    h = 0.5 * (np.abs(np.cos(t)) + np.abs(np.sin(t)))
    xlo, xhi = float((x - h).min()), float((x + h).max())
    ylo, yhi = float((y - h).min()), float((y + h).max())
    lo_x, hi_x = xlo + delta / 2.0, xhi - delta / 2.0
    lo_y, hi_y = ylo + delta / 2.0, yhi - delta / 2.0
    X, Y = clamp(np.array(x, dtype=float), np.array(y, dtype=float), t,
                 min(lo_x, lo_y), max(hi_x, hi_y))
    X, Y, T = repair(X, Y, t, min(lo_x, lo_y), max(hi_x, hi_y),
                     passes=24, top=8)
    rows = [(repr(float(a)), repr(float(b)), repr(float(c)))
            for a, b, c in zip(X, Y, T)]
    chk = TG.check(rows)
    return chk, score(X, Y, T)


def main():
    per = SQ.load()
    records = []
    for n, k, L, e in sample():
        x, y, t = load_pose(n)
        L0 = SQ.extent(per[n])
        cell = {"n": n, "k": k, "L": L0, "e": e, "deltas": {}}
        for ds in DELTAS:
            d = float(ds)
            chk, sc = shrink_once(x, y, t, d)
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
    rec = {"deltas": DELTAS, "rows": records, "median_ceiling": med,
           "extrapolated": total, "n_beaten": len(beaten)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rec, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
