#!/usr/bin/env python3
r"""group_structure.py — the puzzle set as families (GLM round, 15 Nov 2026).

The owner's reading of the set: rows come in groups — trivial, angle, motif, and
on — and the answer to a row is *outlined by the set above it*.  This script test
that reading against the frontier itself, in the only currency that matters:
the excess  e(n) = L(n) - k  above the k x k grid, where k = floor(sqrt n), and
the discrete offset d = n - k^2 inside the block.

What the frontier actually looks like (measured below):

* d = 0 — the grid.  A perfect k x k block, e = 0, one angle, nothing to find.
* d = 1 — the **angle** group.  One square changes orientation: at k = 2 the
  packing is four corner squares around a single 45-degree diamond at the centre,
  and e = 1/sqrt 2.  As k grows the inner cluster grows and the tilt drifts off
  45 degrees (39.805 deg at k = 4, 36.87 deg at k = 7), while e falls.
* d = 2..2k — the **motif** group: a ring of axis-aligned squares around a
  rotated inner cluster, or a tilted band; several angles at once.
* e ~ 1 — the plateau: rows that are still one row of grid away from the block
  above them.  These are where an extra square must be paid for in full.

The "outlined by the set above it" claim is then a testable statement about
e(k, d): if a row's form is inherited from the block above, e(k, d) for fixed d
should vary smoothly in k, and a row whose e sits *above* its own trend is a row
where the frontier is behind the family's own outline — a target.

    python3 scripts/group_structure.py            # groups + targets
    python3 scripts/group_structure.py --table    # the e(k, d) table
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402


def load():
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    rows = {}
    for n in range(1, 1001):
        st = sub.get(n)
        if not st or len(st) != n:
            continue
        r = P.verify(st)
        k = math.isqrt(n)
        d = n - k * k
        angs = Counter(round(math.degrees(t) % 90.0, 3) for _x, _y, t in st)
        rot = sum(c for a, c in angs.items() if abs(a) > 1e-9 and abs(a - 90.0) > 1e-9)
        rows[n] = {"n": n, "k": k, "d": d, "L": r["L"], "e": r["L"] - k,
                   "rot": rot, "angles": len(angs), "ok": r["ok"]}
    return rows


def group_of(rec) -> str:
    if rec["rot"] == 0:
        return "grid" if rec["d"] == 0 else "plateau"
    if rec["d"] == 1:
        return "angle"
    return "motif"


def table(rows, kmax: int = 14, dmax: int = 8):
    print("e(k,d) = L - k, '.' = no such row")
    print("   k " + "".join(f"    d={d}" for d in range(0, dmax + 1)))
    for k in range(2, kmax + 1):
        cells = []
        for d in range(0, dmax + 1):
            n = k * k + d
            if n > k * k + 2 * k or n not in rows:
                cells.append("      .")
            else:
                cells.append(f"{rows[n]['e']:7.4f}")
        print(f"  {k:2d} " + "".join(cells))
    print()
    counts = Counter(group_of(r) for r in rows.values())
    print("groups:", dict(counts))
    print()


def ladder(rows, digits: int = 4, min_count: int = 3):
    """The motif alphabet: which excess values the frontier actually uses."""
    from collections import Counter
    vals = Counter(round(r["e"], digits) for r in rows.values())
    print(f"excess ladder ({len(vals)} distinct values, showing those used >= {min_count} times):")
    for e, c in sorted(vals.items()):
        if c >= min_count:
            print(f"   e={e:<8} used {c:>3} times")
    print()
    for d in range(0, 9):
        col = sorted((r["k"], round(r["e"], 4)) for r in rows.values() if r["d"] == d)
        if col:
            print(f"   d={d}: best e {min(v for _k, v in col):.4f} at k={min(col, key=lambda q: q[1])[0]}"
                  f"   (k, e) = {col[:9]}")
    print()


def targets(rows, tol: float = 0.01):
    """Rows whose excess sits above the trend of the same d at other k."""
    byd = {}
    for r in rows.values():
        byd.setdefault(r["d"], []).append(r)
    out = []
    for d, group in byd.items():
        if len(group) < 3:
            continue
        ks = np.array([g["k"] for g in group], dtype=float)
        es = np.array([g["e"] for g in group], dtype=float)
        # local trend: linear fit e ~ a + b/k over the whole d-column
        A = np.stack([np.ones_like(ks), 1.0 / ks], axis=1)
        coef, *_ = np.linalg.lstsq(A, es, rcond=None)
        pred = A @ coef
        for g, p in zip(group, pred):
            if g["e"] > p + tol and g["k"] >= 3:
                out.append({"n": g["n"], "k": g["k"], "d": d, "e": g["e"],
                            "trend": float(p), "above": float(g["e"] - p),
                            "rot": g["rot"]})
    out.sort(key=lambda r: -r["above"])
    print(f"rows above their own d-column trend (tol {tol}): {len(out)}")
    for r in out[:15]:
        print(f"   n={r['n']:<4} k={r['k']:<3} d={r['d']:<3} e={r['e']:.4f}"
              f" trend {r['trend']:.4f} above +{r['above']:.4f} rot={r['rot']}")
    print()
    # the 'outlined by the set above' test: does e(k,d) predict e(k+1,d)?
    err = []
    for d, group in byd.items():
        group = sorted(group, key=lambda g: g["k"])
        for a, b in zip(group, group[1:]):
            if b["k"] == a["k"] + 1:
                err.append(abs(b["e"] - a["e"]))
    if err:
        err = np.array(err)
        print(f"one-block-out inheritance: |e(k+1,d) - e(k,d)| median {np.median(err):.4f},"
              f" mean {err.mean():.4f}, max {err.max():.4f} over {len(err)} pairs")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--tol", type=float, default=0.01)
    args = ap.parse_args()
    rows = load()
    table(rows)
    ladder(rows)
    targets(rows, args.tol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
