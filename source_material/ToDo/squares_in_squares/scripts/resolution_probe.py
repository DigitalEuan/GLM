#!/usr/bin/env python3
r"""resolution_probe.py — can a coarser "resolution" find, or even HOLD, the answer?

The proposal: solve the packing on a coarse grid of admissible placements
(dithering / pixel-style resolution reduction), then refine back up.

This measures the cheapest possible version of that idea: take a DELIVERED row —
the answer — and ask how far it must move to lie on a lattice of spacing 1/m.
If even the exact solution cannot be represented at resolution m, no search at
resolution m could have found it.

For each row and each m:
  * snap every centre to the nearest point of the (1/m) lattice, keep theta;
  * snap theta to multiples of pi/(4m) as a second, independent test;
  * measure the penetration this introduces and the side growth needed to absorb
    it:  L_needed = L_del + max(0, pen_max),
    a lower bound, because an overlap of p needs at least p of extra separation.

Loss = row_gain(n, L_needed) - row_gain(n, L_del)  (negative = worse).
Compare the accumulated loss against the 0.163635 gap.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ   # noqa: E402
import packlib as P    # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/resolution_probe.json")
ROWS = [10, 25, 50, 83, 100, 150, 200, 290, 500, 1000]
MS = [2, 4, 8, 16, 32, 64, 128]


def snap(st, m, snap_theta):
    out = []
    for x, y, t in st:
        x, y, t = float(x), float(y), float(t)
        X = round(x * m) / m
        Y = round(y * m) / m
        if snap_theta:
            k = math.floor((t + math.pi / (8 * m)) / (math.pi / (2 * m)))
            t = k * (math.pi / (2 * m))
        out.append((X, Y, t))
    return out


def main() -> int:
    per = SQ.load()
    recs = []
    for n in ROWS:
        st = per[n]
        L0 = SQ.extent(st)
        base = SQ.row_gain(n, L0)
        for m in MS:
            for snap_theta in (False, True):
                s2 = snap(st, m, snap_theta)
                v = P.verify(s2, tol=0.0)
                pen = max(0.0, float(v["worst_pen"]))
                Ln = L0 + pen
                recs.append({
                    "n": n, "m": m, "snap_theta": snap_theta,
                    "L_delivered": L0, "pen": float(v["worst_pen"]),
                    "valid": bool(v["ok"]), "L_needed": Ln,
                    "loss": SQ.row_gain(n, Ln) - base})
    tot = {}
    for r in recs:
        key = (r["m"], r["snap_theta"])
        tot[key] = tot.get(key, 0.0) + r["loss"]
    print(f"{'m':>4} {'theta snapped?':>15} {'rows invalid':>13} "
          f"{'total loss':>12} {'vs gap 0.1636':>14}")
    for (m, st_), v in sorted(tot.items()):
        inv = sum(1 for r in recs if r["m"] == m and r["snap_theta"] == st_
                  and not r["valid"])
        print(f"{m:4d} {str(st_):>15} {inv:13d} {v:12.4f} "
              f"{'EXCEEDS GAP' if -v > 0.163635 else 'within gap':>14}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"run": 66, "schema": "resolution/1", "rows": ROWS, "m": MS,
                   "records": recs, "totals": {f"{m}|{t}": v for (m, t), v in tot.items()}},
                  f, indent=1)
    print(f"\nledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
