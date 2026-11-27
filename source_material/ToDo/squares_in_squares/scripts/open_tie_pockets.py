#!/usr/bin/env python3
r"""open_tie_pockets.py — rank the 293 open grid ties by measured pocket headroom.

An *open tie* is a row at L = k = ceil(sqrt(n)) that is not locked by proof and
not an import.  Its own delivered pose is usually the k x k grid with holes, so
its free square is ~1 and seating a cell there only reproduces the tie.  The
score-positive object is the row immediately below it: if n-1 is a **beaten**
frontier pose with side L < k, then any legal unit cell inside that pose makes
row n a beat.  The ranking therefore reports both:

  own_free      largest free square in row n's own CSV pose (coarse scan);
  pre_free      largest free square in row n-1's pose, when n-1 is beaten;
  actionable    true iff n-1 is beaten and pre_free is in [0.5, 1);
  binds         number of cells whose allowed half-size at the pocket is < 0.5
                (the binding set a local module must move).

The coarse scan is discovery only (directors' note §1); the direct `--at`
values in doc 115 are the exact measurements at stated centres.

    python3 scripts/open_tie_pockets.py --write
    python3 scripts/open_tie_pockets.py --top 20
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ                # noqa: E402
import void_insert as VI            # noqa: E402

AUDIT = os.path.join(ROOT, "workspace/push/target_audit.json")
OUT = os.path.join(ROOT, "workspace/push/open_tie_pockets.json")
#: direct measured pockets from doc 115 (predecessor n, x, y, theta, free side)
DIRECT = {655: (2.38108, 8.38097, 0.0, 0.761940),
          998: (27.59, 0.40, 0.0, 0.732771)}


def measure(per, n, cx, cy, th):
    """Free side and binding count at a stated centre/angle."""
    x, y, t = (np.array([q[i] for q in per[n]], dtype=float) for i in range(3))
    x0, x1, y0, y1 = VI.half_ext(x, y, t)
    xmin, xmax = float(x0.min()), float(x1.max())
    ymin, ymax = float(y0.min()), float(y1.max())
    L = max(xmax - xmin, ymax - ymin)
    box = (xmin, xmin + L, ymin, ymin + L, L)
    h = float(VI.hfield(x, y, t, np.array([cx]), np.array([cy]), th, box)[0])
    ct, st = math.cos(th), math.sin(th)
    allows = []
    for j in range(len(x)):
        cj, sj = math.cos(t[j]), math.sin(t[j])
        bound = -1e9
        for qx, qy in ((ct, st), (-st, ct), (cj, sj), (-sj, cj)):
            gA = abs(ct * qx + st * qy) + abs(-st * qx + ct * qy)
            hB = 0.5 * (abs(cj * qx + sj * qy) + abs(-sj * qx + cj * qy))
            proj = abs((cx - x[j]) * qx + (cy - y[j]) * qy)
            bound = max(bound, (proj - hB) / max(gA, 1e-12))
        allows.append(bound)
    return 2 * h, sum(1 for a in allows if a < 0.5 - 1e-12), allows


def scan(per, n, grid=24, angles=5):
    x, y, t = (np.array([q[i] for q in per[n]], dtype=float) for i in range(3))
    st, box = VI.hmax_scan(x, y, t, grid=grid, angles=angles)
    h, cx, cy, th = st
    return 2 * h, cx, cy, th


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args(argv)
    per = SQ.load()
    audit = {int(k): v for k, v in json.load(open(AUDIT))["rows"].items()}
    opens = [n for n, rec in audit.items() if rec.get("class") == "open_tie"]
    rows = []
    for n in sorted(opens):
        k = SQ.grid(n)
        L = SQ.extent(per[n])
        own, cx, cy, th = scan(per, n)
        pre = n - 1
        pre_free, pre_binds, actionable = None, None, False
        if pre in audit and audit[pre].get("class") == "beaten":
            actionable = True
            if pre in DIRECT:
                px, py, pth, pre_free = DIRECT[pre]
                pre_free, pre_binds, _ = measure(per, pre, px, py, pth)
            else:
                pre_free, px, py, pth = scan(per, pre, grid=40, angles=9)
                _, pre_binds, _ = measure(per, pre, px, py, pth)
        rows.append({"n": n, "k": k, "r": k * k - n, "L": L,
                     "gap_to_k": k - L, "own_free": own,
                     "own_centre": [cx, cy, th], "actionable": actionable,
                     "pre": pre if actionable else None,
                     "pre_free": pre_free, "pre_binds": pre_binds})
    # actionable first, then pre_free (or own_free), then fewest binders
    rows.sort(key=lambda r: (not r["actionable"],
                             -(r["pre_free"] if r["actionable"] else r["own_free"]),
                             r["pre_binds"] if r["pre_binds"] is not None else 10 ** 9))
    print(f"open ties: {len(rows)}; actionable (n-1 beaten): "
          f"{sum(1 for r in rows if r['actionable'])}")
    print(f"{'n':>4} {'k':>2} {'r':>2} {'own':>6} {'pre':>6} {'binds':>5}  action")
    for r in rows[:a.top]:
        pre_s = "-" if r["pre_free"] is None else f"{r['pre_free']:.3f}"
        bind_s = "-" if r["pre_binds"] is None else str(r["pre_binds"])
        print(f"{r['n']:>4} {r['k']:>2} {r['r']:>2} {r['own_free']:>6.3f} "
              f"{pre_s:>6} {bind_s:>5}  {'YES' if r['actionable'] else ''}")
    if a.write:
        json.dump({"open_ties": len(rows), "rows": rows}, open(OUT, "w"), indent=1)
        print("wrote", os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
