#!/usr/bin/env python3
r"""leech_measure.py — snapping as a measurement, not an action.

The previous instrument snapped each packing's 24-pocket word to the nearest
Golay codeword and kept the codeword.  That treats snapping as an *action*: the
word is thrown away and replaced by a legal one, and with minimum distance 8
every distinct result is 8 bits from every other, so nothing graded survives.

Treat snapping as a *measurement* instead and the object of interest is the
statistic of the snap:

  * hard distance  d(w, C) = min_{c in C} |w xor c|   -- how illegal is the word
  * soft profile   rho(c) = <s, 2c-1> / <s, 1>         -- correlation of the
    (continuous!) pocket shares with each codeword's +-1 pattern
  * rho1 = max rho, rho2 = runner-up, gap = rho1 - rho2 -- how *decisively* the
    corpus sits near one legal pattern

The soft profile is the graded version of the snap: it uses the real-valued
shares rather than the thresholded bit, so it cannot be annihilated by the
code's minimum distance.  If the address-space idea has any content here, it
shows up as variance in these statistics and as their correlation with the
quantities that matter (does the row beat grid; how much energy a perturbation
adds).

So this file measures, for the 1000 delivered rows:
  1. the hard-distance histogram -- and whether it is constant (if it is, the
     hard measurement has zero variance and cannot be a language, full stop);
  2. the soft statistics rho1, gap: their spread, and mutual information with
     "beats grid" against a permutation null;
  3. the falsifier from PL-26 in its soft form: does gap track the energy
     increase of a perturbation?  Spearman over 3 rows x 3 amplitudes x 20 seeds.

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
OUT = os.path.join(ROOT, "workspace/push/leech_measure.json")
sys.path.insert(0, HERE)
import sqscore as SQ

from leech_address import golay_codewords, hamming, pockets, word_of  # noqa: E402


def entropy(labels) -> float:
    vals, cnt = np.unique(np.asarray(labels), return_counts=True)
    p = cnt / cnt.sum()
    return float(-(p * np.log2(p)).sum())


def mutual_info(x, y) -> float:
    x = np.asarray(x); y = np.asarray(y)
    return float(entropy(x) + entropy(y) - entropy([f"{a}|{b}" for a, b in zip(x, y)]))


def quantile_bins(v: np.ndarray, q: int = 4) -> list:
    edges = np.quantile(v, np.linspace(0, 1, q + 1)[1:-1])
    return np.searchsorted(edges, v).tolist()


def spearman(a, b) -> float:
    a = np.asarray(a, float); b = np.asarray(b, float)
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan")
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    return float((ra * rb).sum() / math.sqrt((ra * ra).sum() * (rb * rb).sum()))


def soft_profile(count: np.ndarray, cw_signs: np.ndarray, cw_bits: np.ndarray) -> tuple:
    """Graded snap statistics for one packing's pocket counts.

    Returns (rho1, rho2, euclid) where
      * rho is the *centred* correlation of the shares with a codeword's +-1
        pattern.  Centring matters: without it every packing whose support fits
        inside one codeword scores exactly 1 (measured: all 1000 rows at
        rho1 = 1.0000 before this fix), which is a coverage test, not a
        similarity.
      * euclid is the Euclidean distance from the share vector to the nearest
        codeword point of {0,1}^24 -- the graded version of the hard Hamming
        snap, and the honest analogue of the lattice distance.
    """
    s = count / max(count.sum(), 1e-12) * 24.0           # mean 1 per pocket
    sc = s - s.mean()
    den = float(np.linalg.norm(sc)) * math.sqrt(24.0)
    rho = (cw_signs @ sc / den) if den > 0 else np.zeros(len(cw_signs))
    rho_sorted = np.sort(rho)[::-1]
    d2 = ((s[None, :] - cw_bits) ** 2).sum(axis=1)
    return float(rho_sorted[0]), float(rho_sorted[1]), float(math.sqrt(d2.min()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(SUB, "submission.csv"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--seeds", type=int, default=20)
    a = ap.parse_args()
    SQ.guard()

    cw = golay_codewords()
    signs = np.array([[(2 * ((int(w) >> j) & 1) - 1) for j in range(24)] for w in cw],
                     dtype=float)
    cw_bits = ((signs + 1) / 2)
    print(f"Golay {len(cw)} words; signs {signs.shape}")

    per: dict = {}
    with open(a.csv) as f:
        rd = csv.reader(f); hdr = next(rd)
        idx = {h: i for i, h in enumerate(hdr)}
        for row in rd:
            per.setdefault(int(row[idx["n"]]), []).append(
                (float(row[idx["x"]]), float(row[idx["y"]]), float(row[idx["angle"]])))
    rows = sorted(per)
    print(f"rows {len(rows)}")

    def L_of(st):
        L = SQ.extent(st)

    hard_d, rho1, gaps, eucl, beats, resid = [], [], [], [], [], []
    dists = {n: None for n in rows}
    for n in rows:
        st = np.array(per[n], dtype=float)
        L = L_of(st)
        cnt = pockets(st, L)
        w = word_of(cnt)
        d = int(hamming(np.array([w]), cw)[0].min())
        r1, r2, e = soft_profile(cnt, signs, cw_bits)
        hard_d.append(d); rho1.append(r1); gaps.append(r1 - r2); eucl.append(e)
        beats.append(1 if SQ.is_beat(n, L) else 0)
        k = int(math.floor(math.sqrt(n))); resid.append(n - k * k)

    hist = {int(v): int(c) for v, c in zip(*np.unique(hard_d, return_counts=True))}
    print("\n1. HARD distance to the code (covering radius of the extended Golay "
          "code is 4)")
    print(f"   histogram: {hist}")
    const = len(hist) == 1
    print(f"   variance of the hard measurement: {np.var(hard_d):.6f} -> "
          f"{'CONSTANT, zero information' if const else 'graded'}")

    rho1 = np.array(rho1); gaps = np.array(gaps); eucl = np.array(eucl)
    print("\n2. SOFT profile statistics")
    print(f"   rho1: min {rho1.min():.4f}  median {np.median(rho1):.4f}  "
          f"max {rho1.max():.4f}  sd {rho1.std():.4f}  distinct "
          f"{len(np.unique(np.round(rho1, 9)))}")
    print(f"   gap : min {gaps.min():.4f}  median {np.median(gaps):.4f}  "
          f"max {gaps.max():.4f}  sd {gaps.std():.4f}")
    mi_rho = mutual_info(quantile_bins(rho1), beats)
    mi_gap = mutual_info(quantile_bins(gaps), beats)
    mi_hard = mutual_info(hard_d, beats)
    mi_eucl = mutual_info(quantile_bins(eucl), beats)
    print(f"   euclid: min {eucl.min():.4f} median {np.median(eucl):.4f} "
          f"max {eucl.max():.4f} sd {eucl.std():.4f}")
    print(f"   MI(hard distance; beats) {mi_hard:.4f}   "
          f"MI(euclid quartile; beats) {mi_eucl:.4f}")
    print(f"   MI(rho1 quartile; beats) {mi_rho:.4f}   "
          f"MI(gap quartile; beats) {mi_gap:.4f}   (H(beats) = {entropy(beats):.3f})")
    mi_r = mutual_info(quantile_bins(gaps), resid)
    print(f"   MI(gap quartile; residue r) {mi_r:.4f}")
    rng = np.random.RandomState(0)
    null = [mutual_info(quantile_bins(gaps), list(rng.permutation(beats)))
            for _ in range(20)]
    print(f"   permutation null: mean {np.mean(null):.4f} max {np.max(null):.4f}")

    import cram_relax as CR
    tab = CR.load_table()
    print(f"\n3. does the snap statistic track energy? "
          f"({a.seeds} seeds x 3 amps x 3 rows)")
    allg, allde = [], []
    per_n = {}
    for n in (60, 240, 961):
        st0 = tab[n]; L0 = CR.record_L(st0)
        g0 = gaps[rows.index(n)]
        gs, des = [], []
        for amp in (0.005, 0.02, 0.08):
            for s in range(a.seeds):
                rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 7)
                sp = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
                r1, r2, _ = soft_profile(pockets(sp, L0), signs, cw_bits)
                gs.append((r1 - r2) - g0)
                des.append(CR.energy(sp, L0))
        per_n[n] = (spearman(gs, des), float(np.mean(des)))
        allg += gs; allde += des
        print(f"   n={n:<4} Spearman(dgap, dE) = {per_n[n][0]:+.3f}   "
              f"mean dE {per_n[n][1]:.3e}")
    print(f"   pooled Spearman(dgap, dE) = {spearman(allg, allde):+.3f}")

    res = {"hard_histogram": hist, "hard_constant": bool(const),
           "rho1": {"min": float(rho1.min()), "max": float(rho1.max()),
                    "sd": float(rho1.std()), "distinct": int(len(np.unique(np.round(rho1, 9))))},
           "gap": {"min": float(gaps.min()), "max": float(gaps.max()),
                   "sd": float(gaps.std())},
           "mi_rho_beats": mi_rho, "mi_gap_beats": mi_gap, "mi_gap_residue": mi_r,
           "mi_hard_beats": mi_hard, "mi_euclid_beats": mi_eucl,
           "euclid": {"min": float(eucl.min()), "max": float(eucl.max()),
                      "sd": float(eucl.std())},
           "null_mean": float(np.mean(null)), "null_max": float(np.max(null)),
           "spearman_pooled": spearman(allg, allde),
           "spearman_per_n": {str(k): v[0] for k, v in per_n.items()}}
    if a.json:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(res, f, indent=1)
        print("\nwrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
