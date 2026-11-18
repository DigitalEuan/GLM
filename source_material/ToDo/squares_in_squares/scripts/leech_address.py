#!/usr/bin/env python3
r"""leech_address.py — 24 pockets as an address space for packings.

THE IDEA.  The Leech lattice is a set of points in Z^24 with a rigid legality
condition, and the repository already uses it that way: the extended Golay code
C (24 bits, 4096 words, minimum distance 8) generates the lattice, and
`src/lean/RequestProject/GLM/Escalation/LeechResidue.lean` states the exact
integer form — x is in sqrt(8)*Lambda_24 iff the coordinates share a parity m,
sum x = 4m mod 8, and each residue class mod 4 is a Golay codeword.
`leechlean/3_leech_bridge/out/codebook.json` is the same idea applied to text:
39,992 tokens, each a 24-pocket integer vector.

So the question is not whether 24 pockets can hold data — the repo already does
that — but whether they hold *this* data.  Two things must be true for a pocket
address to be a language rather than a decoration:

  1. it must be informative (different packings, different addresses), and
  2. it must be *stable* under the operation that physically matters here — a
     perturbation followed by relaxation.  An address that changes when the
     packing barely moves cannot be used to reason about packings.

BOTH ARE MEASURED HERE, and either may fail.  `LeechResidue.lean` is the
standing warning: residues mod 8, 144 and 256 carry *no* information about deep
holes, because they collapse into the lattice coset.  A coarse quantisation hits
exactly that wall, and the honest response is to report the mutual information
rather than to keep refining a decoration.

THE MAPPING.  Square symmetry means theta is taken mod pi/2, so

    pocket(i) = (angle bin, shell)   in   6 x 4 = 24

  * angle bin: 6 equal sectors of [0, pi/2) — the square's own symmetry group
    has order 8, and 6 divides the remaining freedom into the sector widths the
    CRAM study already used (6 angle x 3 distance bins);
  * shell: 4 radial shells of the square's centre relative to the container
    centre, in units of L/2.

A packing becomes a 24-count vector; normalising it gives a point of the simplex;
thresholding at the mean gives a 24-bit word; and the word is snapped to the
**nearest extended Golay codeword** (Hamming distance, 4096 candidates).  The
codeword is the address.  Minimum distance 8 is the error correction: words
within 4 bits of each other share an address.

REPORTED:
  * the pocket occupation profile (which of the 24 pockets this corpus uses);
  * distinct addresses, entropy, and mutual information with (a) whether the row
    beats grid, (b) its residue class r, (c) its band k — against a permutation
    null of the same marginals;
  * stability: Hamming distance of the address, and the energy increase, under
    the project's own perturbation at three amplitudes.

Read-only.  Uses the delivered placements in submission.csv.
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
OUT = os.path.join(ROOT, "workspace/push/leech_address.json")
sys.path.insert(0, HERE)
import sqscore as SQ

G23 = 0xC75          # x^11+x^10+x^6+x^5+x^4+x^2+1, the binary Golay generator


def golay_codewords() -> np.ndarray:
    """All 4096 words of the extended Golay code, as ints in [0, 2^24)."""
    out = []
    for m in range(1 << 12):
        c = m << 11
        # polynomial remainder of c mod G23 (degree 11)
        for bit in range(22, 10, -1):
            if (c >> bit) & 1:
                c ^= G23 << (bit - 11)
        w23 = (m << 11) | (c & 0x7FF)
        par = bin(w23).count("1") & 1
        out.append((par << 23) | w23)
    words = np.array(sorted(set(out)), dtype=np.int64)
    return words


def hamming(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise Hamming distance between integer bitmasks (broadcasting)."""
    d = np.zeros((a.shape[0], b.shape[0]), dtype=np.int16)
    for bit in range(24):
        d += (((a[:, None] >> bit) & 1) != ((b[None, :] >> bit) & 1))
    return d


def pockets(state: np.ndarray, L: float) -> np.ndarray:
    """24-pocket count vector for one packing (state = (x, y, theta))."""
    xy = state[:, :2]
    th = state[:, 2]
    ctr = xy.mean(axis=0)
    rel = xy - ctr
    # container centre is the bbox centre; for a centred state this is ctr
    t = np.mod(th, math.pi / 2)
    ang = np.clip((t / (math.pi / 2) * 6).astype(int), 0, 5)
    r = np.hypot(rel[:, 0], rel[:, 1]) / max(L * 0.5, 1e-12)
    shell = np.clip((r * 4).astype(int), 0, 3)
    idx = ang * 4 + shell
    return np.bincount(idx, minlength=24).astype(float)


def word_of(count: np.ndarray) -> int:
    """Threshold at the mean occupancy -> 24-bit word."""
    thr = count.mean()
    w = 0
    for j in range(24):
        if count[j] > thr:
            w |= 1 << j
    return w


def snap(w: int, cw: np.ndarray) -> tuple:
    d = hamming(np.array([w]), cw)[0]
    j = int(np.argmin(d))
    return int(cw[j]), int(d[j])


def entropy(labels) -> float:
    vals, cnt = np.unique(np.asarray(labels), return_counts=True)
    p = cnt / cnt.sum()
    return float(-(p * np.log2(p)).sum())


def mutual_info(x, y) -> float:
    x = np.asarray(x); y = np.asarray(y)
    hx, hy = entropy(x), entropy(y)
    pair = [f"{a}|{b}" for a, b in zip(x, y)]
    return float(hx + hy - entropy(pair))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(SUB, "submission.csv"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--nmax", type=int, default=1000)
    a = ap.parse_args()
    SQ.guard()

    cw = golay_codewords()
    nz = [bin(int(w)).count("1") for w in cw if int(w) != 0]
    print(f"Golay: {len(cw)} codewords, min nonzero weight {min(nz)}, "
          f"max {max(nz)}")
    assert len(cw) == 4096 and min(nz) == 8, "not the extended Golay code"

    # ---- load placements
    per: dict = {}
    idx = {}
    with open(a.csv) as f:
        rd = csv.reader(f)
        hdr = next(rd)
        idx = {h: i for i, h in enumerate(hdr)}
        for row in rd:
            n = int(row[idx["n"]])
            per.setdefault(n, []).append((float(row[idx["x"]]), float(row[idx["y"]]),
                                          float(row[idx["angle"]])))
    rows = sorted(k for k in per if k <= a.nmax)
    print(f"rows {len(rows)}")

    # ---- addresses
    addr, hd, prof = {}, {}, np.zeros(24)
    for n in rows:
        st = np.array(per[n], dtype=float)
        L = SQ.extent(st)
        cnt = pockets(st, L)
        prof += cnt / max(cnt.sum(), 1)
        w = word_of(cnt)
        code, dist = snap(w, cw)
        addr[n] = code
        hd[n] = dist

    A = [addr[n] for n in rows]
    beats = []
    resid = []
    bands = []
    for n in rows:
        st = np.array(per[n], dtype=float)
        L = SQ.extent(st)
        beats.append(1 if SQ.is_beat(n, L) else 0)
        k = int(math.floor(math.sqrt(n)))
        resid.append(n - k * k)
        bands.append(k)

    print(f"addresses: {len(set(A))} distinct over {len(A)} rows, "
          f"entropy {entropy(A):.3f} bits (max 12)")
    print(f"snap distance to a codeword: median {np.median(list(hd.values())):.0f}, "
          f"max {max(hd.values())}, exact {sum(1 for v in hd.values() if v == 0)}")
    mi_beats = mutual_info(A, beats)
    mi_res = mutual_info(A, resid)
    mi_band = mutual_info(A, bands)
    print(f"MI(address; beats grid) {mi_beats:.4f} bits   (H(beats) = {entropy(beats):.3f})")
    print(f"MI(address; residue r)  {mi_res:.4f} bits    (H(r) = {entropy(resid):.3f})")
    print(f"MI(address; band k)     {mi_band:.4f} bits   (H(k) = {entropy(bands):.3f})")

    rng = np.random.RandomState(0)
    null = []
    for _ in range(20):
        null.append(mutual_info(A, list(rng.permutation(beats))))
    print(f"permutation null for MI(address; beats): mean {np.mean(null):.4f} "
          f"max {np.max(null):.4f}")

    print("\npocket occupation (6 angle sectors x 4 shells), fraction per pocket:")
    P = prof / prof.sum()
    for sec in range(6):
        row = " ".join(f"{P[sec*4+sh]:.3f}" for sh in range(4))
        print(f"  sector {sec} ({sec*15}-{sec*15+15} deg): {row}")
    print(f"  most-used pocket {int(np.argmax(P))} ({P.max():.3f}), "
          f"least-used {int(np.argmin(P))} ({P.min():.4f})")

    # ---- stability under the project's own perturbation
    import cram_relax as CR
    tab = CR.load_table()
    stab = []
    print("\nstability: perturb a record state, recompute the address")
    for n in (60, 240, 961):
        st0 = tab[n]
        L0 = CR.record_L(st0)
        base_w = word_of(pockets(st0, L0))
        base_a, _ = snap(base_w, cw)
        for amp in (0.005, 0.02, 0.08):
            rng = np.random.RandomState(7919 * n + 104729 + 3)
            s0 = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
            w = word_of(pockets(s0, L0))
            code, _ = snap(w, cw)
            d = int(hamming(np.array([base_a]), np.array([code]))[0][0])
            stab.append({"n": n, "amp": amp,
                         "hamming_word": int(hamming(np.array([base_w]),
                                                     np.array([w]))[0][0]),
                         "same_address": bool(code == base_a),
                         "dhamming": d,
                         "dE": float(CR.energy(s0, L0))})
            print(f"  n={n:<4} amp={amp:<6} word dist "
                  f"{hamming(np.array([base_w]), np.array([w]))[0][0]:>2}  "
                  f"address {'SAME' if code == base_a else f'moves {d} bits'}  "
                  f"dE={CR.energy(s0, L0):.3e}")

    res = {"codewords": len(cw), "distinct_addresses": len(set(A)),
           "address_entropy": entropy(A), "median_snap": float(np.median(list(hd.values()))),
           "mi_beats": mi_beats, "mi_residue": mi_res, "mi_band": mi_band,
           "null_beats_mean": float(np.mean(null)), "null_beats_max": float(np.max(null)),
           "pockets": P.tolist(), "stability": stab}
    if a.json:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(res, f, indent=1)
        print("\nwrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
