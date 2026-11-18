#!/usr/bin/env python3
r"""leech_prior.py — is the snap-decisiveness gap usable as a search prior?

Run 45.  PL-28.  The previous round established that the gap rho1 - rho2 between
the two best Golay codewords carries information about "does this row beat grid"
that survives conditioning on the residue column (excess ~0.081 bits, z = 9.87).

This file asks the two questions that decide whether that is *usable*:

  A. SIGN AND STRENGTH.  Are beating rows more or less decisive?  Measured by
     AUC (Mann-Whitney, no binning -- the quartile discretisation of the last
     round threw information away) overall and *within* columns.

  B. THE STRUCTURAL CATCH.  A base-less residue column has no beating row at
     all, by definition.  So a within-column ranking inside such a column has a
     constant target and is undefined: the gap cannot say which row of an
     unsolved column to attack.  What it can do is transfer a *level* -- if
     solved columns have a characteristic gap profile, then the unsolved rows
     whose profile matches it are the plausible first attempts.  So we also
     measure whether the gap tracks the *value* of a solution (the slack delta),
     which is what a prior would need to rank candidate rows at all.

Reported:
  * AUC(gap -> beats), overall and the per-column distribution;
  * Spearman(gap, delta) among beating rows -- more decisive = better packing?;
  * the target profile of beating rows, and for each base-less column the rows
    whose gap is closest to it (the PL-21 attack list, ranked).

Read-only.
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
SUB = os.path.join(ROOT, "workspace/submission")
OUT = os.path.join(ROOT, "workspace/push/leech_prior.json")
sys.path.insert(0, HERE)
import sqscore as SQ

from leech_address import golay_codewords, pockets  # noqa: E402
from leech_measure import soft_profile  # noqa: E402


def auc(scores, labels) -> float:
    """Mann-Whitney AUC: P(score of a positive > score of a negative)."""
    s = np.asarray(scores, float); y = np.asarray(labels, int)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), float)
    ranks[order] = np.arange(1, len(s) + 1)
    # average ranks for ties
    _uniq, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    sums = np.zeros(len(cnt)); np.add.at(sums, inv, ranks)
    ranks = (sums / cnt)[inv]
    return float((ranks[y == 1].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def spearman(a, b) -> float:
    a = np.asarray(a, float); b = np.asarray(b, float)
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    return float((ra * rb).sum() / math.sqrt((ra * ra).sum() * (rb * rb).sum()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(SUB, "submission.csv"))
    ap.add_argument("--json", action="store_true")
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

    rows, gap, delta, beats, resid, band, Ls = [], [], [], [], [], [], []
    for n in sorted(per):
        st = np.array(per[n], float)
        L = SQ.extent(st)
        r1, r2, _ = soft_profile(pockets(st, L), signs, bits)
        k = int(math.floor(math.sqrt(n)))
        rows.append(n); gap.append(r1 - r2); Ls.append(L)
        delta.append(L - k); resid.append(n - k * k); band.append(k)
        beats.append(1 if SQ.is_beat(n, L) else 0)

    gap = np.array(gap); delta = np.array(delta); beats = np.array(beats)
    resid = np.array(resid); band = np.array(band)

    A = auc(gap, beats)
    print(f"A. SIGN — AUC(gap -> beats) = {A:.4f}   (0.5 = none; >0.5 = beating rows "
          f"are MORE decisive)")
    print(f"   mean gap: beating {gap[beats == 1].mean():+.5f} "
          f"(n={int((beats == 1).sum())})   grid {gap[beats == 0].mean():+.5f} "
          f"(n={int((beats == 0).sum())})")
    rng = np.random.RandomState(7)
    null = [auc(gap, rng.permutation(beats)) for _ in range(400)]
    print(f"   permutation null: mean {np.mean(null):.4f} sd {np.std(null):.4f} "
          f"max {np.max(null):.4f}; z = {(A - np.mean(null)) / np.std(null):+.2f}")

    per_col = {}
    for r in np.unique(resid):
        m = resid == r
        if len(np.unique(beats[m])) < 2:
            continue
        per_col[int(r)] = auc(gap[m], beats[m])
    vals = np.array(list(per_col.values()))
    print(f"   per-column AUC over {len(per_col)} columns with both classes: "
          f"median {np.median(vals):.3f}, IQR {np.percentile(vals, 25):.3f}-"
          f"{np.percentile(vals, 75):.3f}, frac > 0.5 = "
          f"{(vals > 0.5).mean():.2f}")

    print("\nB. VALUE — does decisiveness predict how good the packing is?")
    bm = beats == 1
    print(f"   Spearman(gap, delta) among beating rows: {spearman(gap[bm], delta[bm]):+.3f} "
          f"(delta = slack above grid; lower is better)")
    within = [spearman(gap[resid == r], delta[resid == r]) for r in per_col]
    within = np.array([v for v in within if not math.isnan(v)])
    print(f"   within-column Spearman: median {np.median(within):+.3f} over {len(within)} "
          f"columns")

    print("\nC. TARGET PROFILE (from solved rows) and the PL-21 attack list")
    prof = gap[bm]
    med, lo, hi = float(np.median(prof)), float(np.percentile(prof, 25)), \
        float(np.percentile(prof, 75))
    print(f"   beating rows: gap median {med:.4f}, IQR {lo:.4f}-{hi:.4f}")
    print(f"   grid rows   : gap median {np.median(gap[~bm]):.4f}")
    base_res = set(int(r) for r in np.unique(resid[bm]))
    bare = [int(r) for r in np.unique(resid) if int(r) not in base_res]
    print(f"   base-less residues: {len(bare)} -> {bare}")
    print(f"   STRUCTURAL CATCH: {sum(1 for r in bare if len(np.unique(beats[resid == r])) < 2)}"
          f" of {len(bare)} base-less columns have zero variance in the target --")
    print("   no within-column ranking exists there. The gap can only be transferred")
    print("   as a LEVEL: attack the rows whose gap is nearest the beating-row profile.")

    attack = {}
    for r in bare:
        m = resid == r
        idx = np.where(m)[0]
        near = idx[np.argsort(np.abs(gap[idx] - med))][:3]
        attack[int(r)] = [{"n": int(rows[i]), "gap": float(gap[i]),
                           "delta": float(delta[i]),
                           "dist_to_profile": float(abs(gap[i] - med)),
                           "need_delta_below": 1.0} for i in near]
    print(f"   attack list built for {len(attack)} base-less columns "
          f"(3 rows each, nearest to profile {med:.4f})")
    best = sorted(((r, v[0]["dist_to_profile"]) for r, v in attack.items()),
                  key=lambda t: t[1])[:5]
    print("   most profile-like base-less columns: " +
          ", ".join(f"r={r} (d={d:.4f})" for r, d in best))

    res = {"auc_overall": A, "null_mean": float(np.mean(null)),
           "null_sd": float(np.std(null)), "null_max": float(np.max(null)),
           "z": float((A - np.mean(null)) / np.std(null)),
           "per_column_auc": {str(k): v for k, v in per_col.items()},
           "per_column_median_auc": float(np.median(vals)),
           "spearman_gap_delta_beating": spearman(gap[bm], delta[bm]),
           "spearman_within_median": float(np.median(within)),
           "profile_median": med, "profile_iqr": [lo, hi],
           "mean_gap_beating": float(gap[bm].mean()), "mean_gap_grid": float(gap[~bm].mean()),
           "base_less": bare, "attack": attack}
    if a.json:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(res, open(OUT, "w"), indent=1)
        print("\nwrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
