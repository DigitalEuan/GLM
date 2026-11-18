#!/usr/bin/env python3
r"""leech_audit_fix.py — the two instrument errors, and every number recomputed.

Run 47.  Two mistakes were found in the Leech instruments and they invalidate the
measured tables of parts 7-10, so nothing from those parts is quoted until this
file has re-measured it.

ERROR 1 — the score formula.  `scripts/leech_address.py` and
`scripts/area_ceiling.py` scored a row as 10/L.  The repository's score
(`build_table.py`, `cascade2.py`, `packlib`) is

    score = sum over n of (L_n / sqrt(n) - 1)          lower is better
    grid baseline = sum (ceil(sqrt(n)) / sqrt(n) - 1)
    gain from beating row n = (ceil(sqrt(n)) - L_n) / sqrt(n)

so 10/L produced a "score" of 593.279 where the delivered table scores
22.218056945.  The *structure* of the area argument survives (it is monotone in
L), but every absolute number in `11-AREA-CEILING.md` is on the wrong scale.

ERROR 2 — the bounding box.  The Leech instruments computed

    L = max(x) + max(ex) - (min(x) - min(ex))        <-- inflates L

where `ex` is the per-square half-extent.  The correct extent is per square:
`max(x_i + ex_i) - min(x_i - ex_i)`.  Inflating L reclassifies beating rows as
grid rows: 300 beats measured instead of the delivered 553.  Every "beats grid"
label in parts 7-9 is from that computation, so the mutual-information and AUC
numbers are contaminated by a mislabelled target.

WHAT THIS FILE DOES
  1. recomputes L per row with the correct per-square extent, and cross-checks a
     sample against `packlib.verify` (the project's gate) to confirm agreement;
  2. recomputes the snap statistics of part 8/9 against the corrected target:
     MI(gap; beats), AUC(gap), and the rotation control;
  3. recomputes the area ceiling on the correct score scale: ceiling gain per row
     = (ceil(sqrt(n)) - sqrt(n))/sqrt(n), marginal value of slack = 1/sqrt(n) per
     row, summed per column.

Read-only.  Fails loudly if the corrected beat count is not the delivered 553.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from decimal import Decimal, getcontext

import numpy as np

getcontext().prec = 30
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUB = os.path.join(ROOT, "workspace/submission")
OUT = os.path.join(ROOT, "workspace/push/leech_audit_fix.json")
sys.path.insert(0, HERE)
import sqscore as SQ

from leech_address import golay_codewords, pockets  # noqa: E402
from leech_measure import soft_profile  # noqa: E402
from leech_prior import auc  # noqa: E402

SCORE = 22.218056945     # delivered, from the CSV states
BEATS = 553


def extent(st: np.ndarray) -> float:
    """Delegates to the shared scorer: one implementation only."""
    return SQ.extent(st)


def H(a) -> float:
    _, c = np.unique(a, return_counts=True)
    p = c / c.sum()
    return float(-(p * np.log2(p)).sum())


def I(a, b, c=None) -> float:
    if c is None:
        return H(a) + H(b) - H([f"{x}|{y}" for x, y in zip(a, b)])
    t = 0.0
    for u in np.unique(c):
        m = c == u
        if m.sum() < 5:
            continue
        t += (m.mean()) * (H(a[m]) + H(b[m]) - H([f"{x}|{y}" for x, y in zip(a[m], b[m])]))
    return t


def q4(v):
    return np.searchsorted(np.quantile(v, [0.25, 0.5, 0.75]), v).tolist()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(SUB, "submission.csv"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", type=int, default=20)
    a = ap.parse_args()
    SQ.guard()

    cw = golay_codewords()
    signs = np.array([[(2 * ((int(w) >> j) & 1) - 1) for j in range(24)] for w in cw], float)
    bits = (signs + 1) / 2

    per: dict = {}
    with open(a.csv) as f:
        rd = csv.reader(f); hdr = next(rd)
        ix = {h: i for i, h in enumerate(hdr)}
        for r in rd:
            per.setdefault(int(r[ix["n"]]), []).append(
                (float(r[ix["x"]]), float(r[ix["y"]]), float(r[ix["angle"]])))

    # ---- 1. corrected L, and the gate cross-check
    import packlib as P
    rows, Lc, beats, resid, band, gap, rot, delta = [], [], [], [], [], [], [], []
    checked = 0
    for n in sorted(per):
        st = np.array(per[n], float)
        L = extent(st)
        k = math.isqrt(n); m = k if k * k == n else k + 1
        if checked < a.check:
            r = P.verify([tuple(map(float, s)) for s in st])
            assert abs(r["L"] - L) < 1e-9, f"n={n}: mine {L} vs packlib {r['L']}"
            checked += 1
        r1, r2, _ = soft_profile(pockets(st, L), signs, bits)
        rows.append(n); Lc.append(L)
        beats.append(1 if SQ.is_beat(n, L) else 0)
        resid.append(n - k * k); band.append(k)
        gap.append(r1 - r2)
        delta.append(L - k)
        rot.append(1 if np.abs(np.mod(st[:, 2], math.pi / 2)).max() > 1e-9 else 0)

    Lc = np.array(Lc); beats = np.array(beats); gap = np.array(gap)
    delta = np.array(delta); rot = np.array(rot); resid = np.array(resid)

    sc = float(sum(Lc[i] / math.sqrt(rows[i]) - 1.0 for i in range(len(rows))))
    print(f"1. corrected L (per-square extent), cross-checked {checked} rows "
          f"against packlib.verify")
    print(f"   score {sc:.9f}   (delivered {SCORE:.9f}, diff {abs(sc - SCORE):.2e})")
    print(f"   beats {int(beats.sum())}   (delivered {BEATS})")
    assert abs(sc - SCORE) < 1e-6 and int(beats.sum()) == BEATS, "corrected L still wrong"
    print("   MATCHES the delivered table")

    # ---- 2. snap statistics against the corrected target
    A = auc(gap, beats)
    print(f"\n2. snap statistics, corrected target")
    print(f"   AUC(gap -> beats) {A:.4f}   mean gap beating {gap[beats==1].mean():+.5f} "
          f"grid {gap[beats==0].mean():+.5f}")
    q = np.array(q4(gap))
    print(f"   MI(gapQ; beats) {I(q, beats):.4f}   MI(rot; beats) {I(rot, beats):.4f}"
          f"   MI(gapQ; beats|rot) {I(q, beats, rot):.4f}")
    print(f"   AUC(gap) rotated rows only {auc(gap[rot==1], beats[rot==1]):.4f}   "
          f"AUC(rot) {auc(rot, beats):.4f}")
    print(f"   rotated: beating {rot[beats==1].mean():.3f}  grid {rot[beats==0].mean():.3f}")

    # ---- 3. area ceiling on the correct score scale
    print(f"\n3. area ceiling (score = L/sqrt(n) - 1)")
    ceil = np.array([(math.isqrt(rows[i]) if math.isqrt(rows[i])**2 == rows[i]
                      else math.isqrt(rows[i]) + 1) / math.sqrt(rows[i]) - 1
                     for i in range(len(rows))])
    gains = np.array([(ceil[i] - (Lc[i] / math.sqrt(rows[i]) - 1)) for i in range(len(rows))])
    bar = np.array([1.0 / math.sqrt(n) for n in rows])

    base_res = sorted({int(resid[i]) for i in range(len(rows)) if beats[i]})
    bare = sorted(set(int(r) for r in resid) - set(base_res))
    g_bare = [i for i in range(len(rows)) if not beats[i] and int(resid[i]) in bare]
    g_base = [i for i in range(len(rows)) if not beats[i] and int(resid[i]) in base_res]
    print(f"   grid-row ceiling: base-less {len(g_bare)} rows {ceil[g_bare].sum():.6f} "
          f"({ceil[g_bare].mean():.6f}/row)")
    print(f"   grid-row ceiling: based     {len(g_base)} rows {ceil[g_base].sum():.6f} "
          f"({ceil[g_base].mean():.6f}/row)")
    print(f"   total grid-row ceiling {ceil[beats == 0].sum():.6f}; "
          f"headroom of beating rows to zero waste {(Lc[beats==1]/np.sqrt(np.array(rows)[beats==1]) - 1).sum():.6f}")
    print(f"   base-less residue count {len(bare)}, based {len(base_res)}")

    per_col = {}
    for r in sorted(set(int(x) for x in resid)):
        m = resid == r
        idx = np.where(m)[0]
        per_col[r] = {"rows": len(idx), "beating": int(beats[idx].sum()),
                      "marginal": float(bar[idx].sum()),
                      "slack_per_001": float(0.01 * bar[idx].sum()),
                      "ceiling": float(ceil[idx].sum())}
    top = sorted(per_col.items(), key=lambda kv: -kv[1]["marginal"])[:8]
    print("   per column (marginal = sum 1/sqrt(n) over the column):")
    for r, v in top:
        print(f"     r={r:>2} rows {v['rows']:>2} beat {v['beating']:>2} "
              f"margin {v['marginal']:.4f} (per 0.01 slack {v['slack_per_001']:.4f})")
    tot_marg = sum(v["marginal"] for v in per_col.values() if v["beating"] > 0)
    print(f"   total marginal over open columns {tot_marg:.4f} "
          f"-> 0.01 slack = {0.01*tot_marg:.4f} score")

    res = {"score": sc, "beats": int(beats.sum()), "auc_gap": A,
           "mi_gap_beats": I(q, beats), "mi_rot_beats": I(rot, beats),
           "mi_gap_beats_given_rot": I(q, beats, rot),
           "auc_gap_rotated": auc(gap[rot == 1], beats[rot == 1]),
           "auc_rot": auc(rot, beats),
           "ceil_bare": float(ceil[g_bare].sum()), "ceil_base": float(ceil[g_base].sum()),
           "bare_rows": len(g_bare), "base_rows": len(g_base),
           "bare_residues": bare, "base_residues": base_res,
           "ceil_grid_total": float(ceil[beats == 0].sum()),
           "headroom_beating": float((Lc[beats == 1] /
                                      np.sqrt(np.array(rows)[beats == 1]) - 1).sum()),
           "total_marginal_open": tot_marg,
           "per_column": {str(k): v for k, v in per_col.items()}}
    if a.json:
        json.dump(res, open(OUT, "w"), indent=1)
        print("\nwrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
