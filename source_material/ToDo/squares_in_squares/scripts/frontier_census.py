#!/usr/bin/env python3
r"""frontier_census.py — the verified state of the band frontier, from the CSV.

Why this instrument exists
--------------------------
The wall documents (75, 114-117) measured the band-frontier poses from
`workspace/submission/table.json`'s `state` fields.  `reconcile_table.py`
rewrote `L` to the true 40-digit side but deliberately left `state` alone, so
for the rows whose delivered pose changed after table.json was written, the
`state` is a *different pose* from the one in `submission.csv`.  The census
below reads only the CSV (the file `sqscore` scores), and reports:

  * the deliverable: 1000/1000 rows legal at the project gate, the guard's
    score and beat count;
  * the score decomposition (beaten / locked ties / open ties / imports);
  * the band table in true geometry: frontier m*, j = k^2 - m*, L, delta,
    void V = L^2 - m*, the rigid-pose price d = V - (j - 1), and the tilt
    census of the frontier pose;
  * the provenance defect: how many table.json states differ from the CSV,
    by `src`, and which frontier rows are affected;
  * optionally, the free square of a frontier pose (`--pocket K`), with the
    cells that bind it — the object a higher-grid design has to move.

The distinction that matters: V = L^2 - m* is the pose's *actual* empty area,
and at n = m* + 1 the same side still has V - 1 > 0, so one added cell is
always area-feasible.  The obstacle is the largest contiguous square, not the
area; that is what `--pocket` measures.

Usage
-----
    python3 scripts/frontier_census.py                 # fast: no free-space scan
    python3 scripts/frontier_census.py --pocket 26     # one band, with binding cells
    python3 scripts/frontier_census.py --pocket 26 --write
    python3 scripts/frontier_census.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import numpy as np                               # noqa: E402

import packlib as P                              # noqa: E402
import sqscore as SQ                             # noqa: E402

SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
TABLE = os.path.join(ROOT, "workspace/submission/table.json")
AUDIT = os.path.join(ROOT, "workspace/push/target_audit.json")
OUT = os.path.join(ROOT, "workspace/push/frontier_census.json")


def load_csv(path=SUBMISSION):
    per = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            per.setdefault(int(row["n"]), []).append(
                (float(row["x"]), float(row["y"]), float(row["angle"])))
    return per


def tilt(a):
    t = a % (math.pi / 2)
    return t - math.pi / 2 if t > math.pi / 4 else t


def state_key(st):
    return tuple(sorted((round(float(x), 9), round(float(y), 9),
                         round(float(a), 9)) for x, y, a in st))


def band_frontiers(per):
    out = {}
    for k in range(2, 33):
        lo, hi = (k - 1) ** 2 + 1, min(k * k, 1000)
        beaten = [n for n in range(lo, hi + 1) if SQ.extent(per[n]) < k - 1e-12]
        if beaten:
            out[k] = max(beaten)
    return out


def verify_all(per):
    bad = []
    for n in sorted(per):
        v = P.verify(per[n])
        if not v["ok"]:
            bad.append((n, v["worst_pen"]))
    return bad


def provenance(per):
    tab = json.load(open(TABLE))
    diff = defaultdict(list)
    for n in sorted(per):
        rec = tab[str(n)]
        if state_key(rec["state"]) != state_key(per[n]):
            diff[rec.get("src", "?")].append(n)
    return tab, diff


def band_rows(per, frontiers, tab, diff_rows):
    rows = []
    stale = set(diff_rows)
    for k, m in frontiers.items():
        L = SQ.extent(per[m])
        j = k * k - m
        V = L * L - m
        st = per[m]
        tl = [abs(tilt(a)) for _, _, a in st]
        rows.append({
            "k": k, "frontier": m, "next": m + 1, "j": j,
            "L": L, "delta": k - L, "V": V, "V_over_j": V / j,
            "rigid_price": V - (j - 1),
            "area_at_next": L * L - (m + 1),
            "tilted_gt_1e-4": sum(1 for t in tl if t > 1e-4),
            "tilted_gt_1e-2": sum(1 for t in tl if t > 1e-2),
            "max_tilt_deg": math.degrees(max(tl)),
            "distinct_angles": len({round(a % (math.pi / 2), 9) for _, _, a in st}),
            "cells": len(st),
            "src": tab[str(m)].get("src", "?"),
            "state_stale": m in stale,
        })
    return rows


def evaluate_at(per, m, cx, cy, th):
    """Free square allowed at a *given* centre/angle, and the cells that bind it.

    The scan in `pocket()` is a local search and can settle on a smaller pocket
    than the global one; this evaluates a specified point exactly (the same
    closed-form SAT field the scan uses), so a published pocket is reproducible
    from its centre.
    """
    import void_insert as VI
    st = per[m]
    x = np.array([q[0] for q in st])
    y = np.array([q[1] for q in st])
    t = np.array([q[2] for q in st])
    x0, x1, y0, y1 = VI.half_ext(x, y, t)
    xmin, xmax = float(x0.min()), float(x1.max())
    ymin, ymax = float(y0.min()), float(y1.max())
    L = max(xmax - xmin, ymax - ymin)
    box = (xmin, xmin + L, ymin, ymin + L, L)
    h = float(VI.hfield(x, y, t, np.array([cx]), np.array([cy]), th, box)[0])
    ct, st_ = math.cos(th), math.sin(th)
    allowed = []
    for j in range(len(x)):
        cj, sj = math.cos(t[j]), math.sin(t[j])
        bound = -1e9
        for qx, qy in ((ct, st_), (-st_, ct), (cj, sj), (-sj, cj)):
            gA = abs(ct * qx + st_ * qy) + abs(-st_ * qx + ct * qy)
            hB = 0.5 * (abs(cj * qx + sj * qy) + abs(-sj * qx + cj * qy))
            proj = abs((cx - x[j]) * qx + (cy - y[j]) * qy)
            bound = max(bound, (proj - hB) / max(gA, 1e-12))
        allowed.append(bound)
    order = np.argsort(allowed)[:4]
    bind = [{"cell": int(i), "x": float(x[i]), "y": float(y[i]),
             "tilt_deg": math.degrees(tilt(t[i])),
             "allows_side": float(2 * allowed[i])} for i in order]
    return {"m": m, "L": float(L), "free_side": float(2 * h),
            "centre": [float(cx), float(cy)], "angle": float(th),
            "deficit": float(1 - 2 * h), "binding": bind}


def pocket(per, m, grid=84, angles=13, rounds=5):
    """Scan for a free square (a lower bound: the scan is a local search)."""
    import void_insert as VI
    st = per[m]
    x = np.array([q[0] for q in st])
    y = np.array([q[1] for q in st])
    t = np.array([q[2] for q in st])
    best, box = VI.hmax_scan(x, y, t, grid=grid, angles=angles)
    best = VI.refine(x, y, t, best, box, rounds=rounds, grid=61)
    return evaluate_at(per, m, best[1], best[2], best[3])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pocket", type=int, default=None, metavar="N")
    ap.add_argument("--at", type=float, nargs=3, default=None,
                    metavar=("N", "X", "Y"), help="direct pocket at (x, y), angle 0")
    ap.add_argument("--angle", type=float, default=0.0)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        per = load_csv()
        assert abs(SQ.extent(per[1]) - 1.0) < 1e-9
        assert len(per) == 1000
        # the score identity on a synthetic table: sides 1, 3, 5 at n = 1, 4, 9
        from decimal import Decimal, localcontext
        with localcontext() as ctx:
            ctx.prec = 40
            s = sum((Decimal(L) / Decimal(n).sqrt() - 1 for n, L in
                     ((1, 1), (4, 3), (9, 5))), Decimal(0))
            assert s == Decimal(7) / 6, s
        # a planted stale state is caught by the key
        st = per[1]
        planted = [(x + 1e-6, y, a) for x, y, a in st]
        assert state_key(planted) != state_key(st)
        # and the shipped table now has no stale state (D0, run 161)
        _tab, diff = provenance(per)
        assert not diff, diff
        print("frontier_census selftest: 4 controls OK (extent, score identity,"
              " planted stale state caught, shipped table has 0 stale)")
        return 0
    per = load_csv()
    bad = verify_all(per)
    guard = SQ.guard()
    tab, diff = provenance(per)
    stale_rows = sorted(n for v in diff.values() for n in v)
    frontiers = band_frontiers(per)
    rows = band_rows(per, frontiers, tab, stale_rows)
    rep = {
        "guard": {"score": str(guard["score"]), "beats": guard["beats"],
                  "rows": guard["rows"], "grid": guard["grid"]},
        "illegal_rows": bad,
        "stale": {"count": len(stale_rows), "by_src": {s: v for s, v in diff.items()},
                  "frontier_rows_stale": [r["k"] for r in rows if r["state_stale"]]},
        "frontiers": rows,
    }
    if os.path.exists(AUDIT):
        rep["score_split"] = json.load(open(AUDIT)).get("score")
    if args.pocket is not None:
        rep["pocket"] = pocket(per, args.pocket)
    if args.at is not None:
        rep["pocket_at"] = evaluate_at(per, int(args.at[0]), args.at[1],
                                       args.at[2], args.angle)
    if args.write:
        json.dump(rep, open(OUT, "w"), indent=1)
        print("wrote", OUT)

    print(f"delivered: score {guard['score']:.9f}, beats {guard['beats']}, "
          f"grid {guard['grid']}, rows {guard['rows']}; illegal {len(bad)}")
    if "score_split" in rep:
        s = rep["score_split"]
        print(f"split: beats {float(s['beats']):.6f} + ties {float(s['ties']):.6f}"
              f" = {float(s['all']):.6f}; locked {float(s['locked']):.6f},"
              f" open {float(s['open_ties']):.6f}, import {float(s['import']):.6f}")
    print(f"table.json states differing from CSV: {len(stale_rows)};"
          f" frontier rows stale (k): {rep['stale']['frontier_rows_stale']}")
    print("k  m*   j  L             delta      V      V/j   rigid  area@next  tilt>1e-4  stale")
    for r in rows:
        print(f"{r['k']:2d} {r['frontier']:4d} {r['j']:3d} {r['L']:.9f}"
              f" {r['delta']:.6f} {r['V']:6.2f} {r['V_over_j']:.3f}"
              f" {r['rigid_price']:+6.2f} {r['area_at_next']:8.2f}"
              f" {r['tilted_gt_1e-4']:9d}  {r['state_stale']}")
    for key in ("pocket", "pocket_at"):
        if key not in rep:
            continue
        p = rep[key]
        print(f"\n{key} n={p['m']} at ({p['centre'][0]:.4f},{p['centre'][1]:.4f}),"
              f" angle {p['angle']:.4f}: free side {p['free_side']:.6f},"
              f" deficit {p['deficit']:.6f}")
        for b in p["binding"]:
            print(f"  binds cell {b['cell']:4d} ({b['x']:.4f},{b['y']:.4f})"
                  f" tilt {b['tilt_deg']:+.2f} deg allows {b['allows_side']:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
