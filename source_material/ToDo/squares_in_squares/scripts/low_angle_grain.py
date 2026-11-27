#!/usr/bin/env python3
r"""low_angle_grain.py — the family the high-band poses actually resemble.

Why this instrument exists
--------------------------
The delivered band-frontier poses (k = 21..32, n = k^2 - j) are *not* 45-degree
block constructions: their tilted cells sit at 10-18 degrees (measured on
submission.csv; see scripts/frontier_census.py).  The families the project has
already priced -- Block45, Block45Half, the ridge, the 8-15-17 parametric block
-- are all high-angle, and a rotated b x b grain of unit cells at angle theta
has a bounding box of side b*w with w = cos(theta) + sin(theta), so its bbox
waste is

    waste(theta, b) = (w^2 - 1) * b^2

which is b^2 at 45 degrees (waste 1.0 b^2), 0.8 b^2 at atan(1/2), 0.6 b^2 at
atan(1/3) = 18.43 degrees, 0.47 b^2 at atan(1/4), 0.38 b^2 at atan(1/5).

At b = 6 that is 21.6 at 18.43 degrees against a band deficit j = 20..26: the
grain's own bbox waste is the size of the whole deficit, and the axis fill in
the two triangular corners is what can pay for it.  This instrument measures,
exactly and cheaply, what one corner grain plus an axis fill can reach.

It is a *discovery* instrument: the geometry is float, every candidate that
matters is handed to packlib (the project gate), and no pose is promoted here.

Family
------
  * a b x b grid of unit cells at theta = atan(1/q), q >= 2, corner-anchored so
    its bbox is exactly [0, W]^2 with W = b*w;
  * axis-aligned unit cells at every integer slot (i+1/2, j+1/2) in [0, L]^2
    that is disjoint from every grain cell (exact SAT test, four axes);
  * side L = k - eps, count = b^2 + number of disjoint slots.

Nothing is dropped from the grain and the fill is not greedy or randomised:
for a given (k, q, b) the count is a deterministic function of the geometry,
so the census is a decision, not a sample.

Usage
-----
    python3 scripts/low_angle_grain.py --selftest
    python3 scripts/low_angle_grain.py                 # k = 21..32 census
    python3 scripts/low_angle_grain.py --bands 16 20 26 32 --q 2 3 4 5
    python3 scripts/low_angle_grain.py --pose 26 3 6 --write
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import packlib as P                              # noqa: E402
import sqscore as SQ                             # noqa: E402

SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
OUT = os.path.join(ROOT, "workspace/push/low_angle_grain.json")


def load_truth():
    per = {}
    with open(SUBMISSION) as f:
        for row in csv.DictReader(f):
            per.setdefault(int(row["n"]), []).append(
                (float(row["x"]), float(row["y"]), float(row["angle"])))
    return per


def band_data(per):
    """k -> (frontier m*, next row, L(m*), j, deficit e = k - j)."""
    out = {}
    for k in range(2, 33):
        lo, hi = (k - 1) ** 2 + 1, min(k * k, 1000)
        beaten = [n for n in range(lo, hi + 1) if SQ.extent(per[n]) < k - 1e-12]
        if not beaten:
            continue
        m = max(beaten)
        out[k] = {"frontier": m, "next": m + 1, "L": SQ.extent(per[m]),
                  "j": k * k - m, "e": k - (k * k - m)}
    return out


def slots(L):
    """Integer axis slots whose full unit square lies inside [0, L]^2."""
    m = int(math.floor(L - 0.5))
    pts = [(i + 0.5, j + 0.5) for j in range(m + 1) for i in range(m + 1)
           if i + 1.0 <= L + 1e-12 and j + 1.0 <= L + 1e-12]
    return np.asarray(pts, dtype=float) if pts else np.zeros((0, 2))


def grain_state(b, q):
    """The b x b grain at theta = atan(1/q), corner-anchored in [0, W]^2."""
    th = math.atan2(1.0, q)
    c, s = math.cos(th), math.sin(th)
    W = b * (c + s)
    ij = np.asarray([(i + 0.5, j + 0.5) for j in range(b) for i in range(b)])
    rel = ij - np.asarray([b / 2.0, b / 2.0])
    R = np.asarray([[c, -s], [s, c]])
    return rel @ R.T + np.asarray([W / 2.0, W / 2.0]), th, W


def disjoint(slots_xy, gx, gy, gt):
    """Boolean mask: slot (axis) vs grain cell (angle gt) disjoint, SAT, 4 axes."""
    dx = slots_xy[:, 0] - gx
    dy = slots_xy[:, 1] - gy
    best = np.full(len(slots_xy), -1e9)
    ct, st = math.cos(gt), math.sin(gt)
    for qx, qy in ((1.0, 0.0), (0.0, 1.0), (ct, st), (-st, ct)):
        hA = 0.5 * (abs(qx) + abs(qy))
        hB = 0.5 * (abs(ct * qx + st * qy) + abs(-st * qx + ct * qy))
        proj = np.abs(dx * qx + dy * qy)
        best = np.maximum(best, proj - (hA + hB))
    return best > 1e-12


def build(k, q, b, eps=1e-6):
    """Return (state, count, side, W, nfill) or None if the grain cannot fit."""
    gx, th, W = grain_state(b, q)
    L = k - eps
    if W > L - 1e-9:
        return None
    pts = slots(L)
    ok = np.ones(len(pts), bool)
    for (x, y) in gx:
        ok &= disjoint(pts, x, y, th)
    fill = pts[ok]
    state = ([(float(x), float(y), th) for x, y in gx]
             + [(float(x), float(y), 0.0) for x, y in fill])
    ver = P.verify(state, tol=1e-9)          # a touch is legal at the family level
    return {"state": state, "count": len(state), "side": ver["L"],
            "grain_bbox": W, "nfill": int(ok.sum()), "gate": ver["ok"],
            "worst_pen": ver["worst_pen"]}


def census(ks, qs, bs, eps=1e-6):
    per = load_truth()
    bands = band_data(per)
    rows = []
    for k in ks:
        if k not in bands:
            continue
        bd = bands[k]
        need = bd["next"]
        best = None
        for q in qs:
            for b in bs:
                r = build(k, q, b, eps)
                if r is None:
                    continue
                if best is None or r["count"] > best["count"]:
                    best = dict(r, q=q, b=b)
        if best is None:
            rows.append({"k": k, "need": need, "best": None})
        else:
            rows.append({"k": k, "need": need, "frontier": bd["frontier"],
                         "L": bd["L"], "j": bd["j"],
                         "best": {"q": best["q"], "b": best["b"],
                                  "count": best["count"], "side": best["side"],
                                  "grain_bbox": best["grain_bbox"],
                                  "nfill": best["nfill"],
                                  "gate": best["gate"],
                                  "short": need - best["count"]}})
    return bands, rows


def selftest():
    """Controls with known answers."""
    # 1. the low-angle limit: the bbox waste vanishes as q -> infinity.
    c, s = math.cos(math.atan2(1, 10 ** 6)), math.sin(math.atan2(1, 10 ** 6))
    assert (c + s) ** 2 - 1 < 3e-6, (c + s) ** 2 - 1
    # 2. a single 45-degree cell in the corner (b=1, q=1) at L = 4: its bbox
    #    covers the four slots of the 2 x 2 corner, so the fill loses 4 slots
    #    and the count is 1 + 12 = 13.
    r = build(4, 1, 1, eps=0.0)
    assert r is not None and r["gate"], r
    assert r["count"] == 13, r["count"]
    # 3. the waste identity w^2 - 1 at the named words.
    for q, expect in ((2, 0.8), (3, 0.6), (4, 1 / 17 * 8), (5, 0.3846153846)):
        c, s = math.cos(math.atan2(1, q)), math.sin(math.atan2(1, q))
        w2 = (c + s) ** 2
        assert abs((w2 - 1) - expect) < 1e-9, (q, w2 - 1, expect)
    # 4. every emitted state passes the project gate; a planted overlap fails.
    r = build(26, 3, 6)
    assert r is not None and r["gate"] and r["worst_pen"] <= 1e-9, r
    bad = list(r["state"])
    bad[0] = (bad[1][0], bad[1][1], bad[1][2])
    assert not P.verify(bad)["ok"]
    print("low_angle_grain selftest: 4 controls OK (low-angle limit, 45-degree corner,"
          " waste identity, gate + planted overlap)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--bands", type=int, nargs="*", default=list(range(21, 33)))
    ap.add_argument("--q", type=int, nargs="*", default=[2, 3, 4, 5, 6, 7])
    ap.add_argument("--b", type=int, nargs="*", default=list(range(3, 13)))
    ap.add_argument("--eps", type=float, default=1e-6)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--pose", type=int, nargs=3, metavar=("K", "Q", "B"))
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    if args.pose:
        k, q, b = args.pose
        r = build(k, q, b, args.eps)
        if r is None:
            print("grain does not fit")
            return 1
        print(json.dumps({kk: vv for kk, vv in r.items() if kk != "state"},
                         indent=1))
        if args.write:
            json.dump({str(k): {"q": q, "b": b, "L": r["side"],
                                "count": r["count"], "state": r["state"]}},
                      open(OUT, "w"), indent=1)
            print("wrote", OUT)
        return 0
    bands, rows = census(args.bands, args.q, args.b, args.eps)
    print("k  frontier  need  best (q,b)  count  side      grain_bbox  fill  short")
    hits = 0
    for r in rows:
        if r["best"] is None:
            print(f"{r['k']:2d} {r.get('frontier','?'):>8} {r['need']:5d}  no grain fits")
            continue
        b = r["best"]
        hits += b["short"] <= 0
        print(f"{r['k']:2d} {r['frontier']:8d} {r['need']:5d}  ({b['q']},{b['b']})"
              f"      {b['count']:5d}  {b['side']:.6f}  {b['grain_bbox']:.4f}"
              f"     {b['nfill']:4d}  {b['short']:+d}")
    print(f"hits (count >= next row): {hits}/{len(rows)}")
    if args.write:
        json.dump({"bands": {str(k): v for k, v in bands.items()},
                   "census": rows, "q": args.q, "b": args.b,
                   "eps": args.eps}, open(OUT, "w"), indent=1)
        print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
