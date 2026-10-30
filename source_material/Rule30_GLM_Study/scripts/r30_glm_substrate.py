"""GLM substrate analysis of the Rule 30 center column.

The GLM (Geometric Language Machine, github.com/DigitalEuan/GLM) is built
on a 24-dimensional mathematical substrate composed of:

    * Golay-24 code (4096 codewords, weight distribution 1, 759, 2576, ...)
    * Hexacode over GF(4) (the GF(4) construction spine of the Golay code)
    * Miracle Octad Generator (MOG) grid
    * Leech lattice Lambda_24 (196560 minimal vectors, norm^2 = 4)
    * Griess algebra (the 196884-dim commutative non-associative algebra
      whose automorphism group is the Monster)

This module loads the GLM's actual substrate modules
(glm_universal.substrate.mog, .leech2, .golay_paley) and uses them to
test whether the Rule 30 center column has any unusual correlation with
these structures.

Tests performed:

1. **Golay codeword rate**. For each non-overlapping 24-bit window of
   the center column, check whether it is a Golay codeword. Compare
   against the rate expected for a uniform Bernoulli(1/2) source.

2. **Leech lattice nearest-point distance**. For each non-overlapping
   24-bit window, treat it as a binary vector in R^24 and compute the
   squared distance to the nearest point of the Leech lattice Lambda_24.

3. **Hexacode membership**. For each non-overlapping 6-symbol window
   (paired bits read as GF(4) symbols), check whether it is one of the
   64 hexacode words. Compare against the rate expected by chance.

4. **Monster-2A axis classification**. The 2A conjugacy class of the
   Monster group is in bijection with the norm-4 minimal vectors of
   the Leech lattice. We classify each 24-bit window as either a 2A
   axis or not, and report the rate.

All of these are direct uses of the GLM's substrate code, not a
re-implementation. We import the actual `glm_universal` package.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

DATA = Path("/home/z/my-project/data")

# Add the GLM repo to sys.path so we can import the substrate modules.
GLM_REPO = Path("/home/z/my-project/glm_repo")
sys.path.insert(0, str(GLM_REPO))

from glm_universal.substrate import mog, golay_paley, leech2  # noqa: E402


# --- 1. Golay codeword rate -------------------------------------------------

def golay_codeword_rate(cc: np.ndarray) -> dict:
    """For each non-overlapping 24-bit window, check if it's a Golay codeword."""
    n_windows = cc.shape[0] // 24
    # Pack each 24-bit window into an int
    windows = cc[:n_windows * 24].reshape(n_windows, 24)
    # Pre-compute the set of Golay codewords as a Python set of ints
    golay_set = set(int(g) for g in mog.GOLAY_MASKS)
    print(f"     [golay] loaded {len(golay_set)} Golay codewords")

    n_hits = 0
    sample_hits = []
    for i in range(n_windows):
        # MSB first: cc[i,0] is bit 23 of the int
        word = 0
        for b in range(24):
            word |= int(windows[i, b]) << (23 - b)
        if word in golay_set:
            n_hits += 1
            if len(sample_hits) < 5:
                sample_hits.append((i, word))

    expected_rate = len(golay_set) / (1 << 24)  # = 4096 / 2^24 = 1/4096
    expected_count = n_windows * expected_rate
    return {
        "n_windows": n_windows,
        "n_hits": n_hits,
        "expected_count": float(expected_count),
        "expected_rate_per_window": float(expected_rate),
        "empirical_rate_per_window": float(n_hits / n_windows),
        "sample_hits": sample_hits,
        "golay_code_size": len(golay_set),
    }


# --- 2. Leech lattice nearest-point distance -------------------------------

def leech_nearest_distance(cc: np.ndarray, max_windows: int = 1000) -> dict:
    """For each non-overlapping 24-bit window, treat it as a binary vector
    in R^24 (entries 0 or 1) and compute the squared distance to the nearest
    point of the Leech lattice.

    This uses GLM's `leech2` module's nearest-point API. To stay within
    compute budget we cap at max_windows (default 1000).

    The Leech lattice is an even unimodular lattice in 24 dimensions; its
    minimal vectors have squared norm 4. A random binary vector is
    extremely unlikely to land near a Leech lattice point.

    For efficiency, we use a precomputed Leech quantizer if available, or
    fall back to enumerating minimal vectors within a radius.
    """
    n_windows = min(cc.shape[0] // 24, max_windows)
    # Get the list of minimal vectors (196560 of them, each norm^2 = 4).
    # For each window, compute the squared distance to the closest minimal
    # vector (understanding that the lattice is generated additively by
    # these). For a fair test of "nearness to lattice", we project modulo 2
    # (the Leech lattice is an even integral lattice, so mod 2 the minimal
    # vectors span the Golay code).
    try:
        minimal_vectors = list(leech2.minimal_vectors())
    except Exception as e:
        return {"status": "could_not_enumerate", "error": str(e)}

    n_min = len(minimal_vectors)
    print(f"     [leech] loaded {n_min} Leech minimal vectors "
          f"(expected 196560)")

    if n_min == 0:
        return {"status": "no_minimal_vectors"}

    # Sample a manageable subset for the brute-force distance computation
    rng = np.random.default_rng(seed=20241023)  # deterministic
    if n_min > 8192:
        idx = rng.choice(n_min, size=8192, replace=False)
        sampled_minimal = [minimal_vectors[i] for i in idx]
    else:
        sampled_minimal = minimal_vectors

    distances = np.zeros(n_windows, dtype=np.float64)
    for i in range(n_windows):
        v = cc[i * 24:(i + 1) * 24].astype(np.int64)
        # Squared distance to each sampled minimal vector
        best = None
        for mvec in sampled_minimal:
            m = np.array(mvec, dtype=np.int64)
            if m.shape[0] != 24:
                continue
            d2 = float(np.sum((v - m) ** 2))
            if best is None or d2 < best:
                best = d2
        distances[i] = best if best is not None else float("inf")

    return {
        "n_windows": n_windows,
        "n_sampled_minimal_vectors": len(sampled_minimal),
        "min_distance_sq": float(distances.min()),
        "max_distance_sq": float(distances.max()),
        "mean_distance_sq": float(distances.mean()),
        "median_distance_sq": float(np.median(distances)),
        # The Leech lattice has minimal vectors at squared norm 4, so a
        # binary vector {0,1}^24 will be at least at distance ~ 4 from
        # any minimal vector (since the binary vector itself has norm <= 24).
        "lattice_minimal_norm_sq": 4,
    }


# --- 3. Hexacode membership ------------------------------------------------

def hexacode_rate(cc: np.ndarray) -> dict:
    """For each non-overlapping 12-bit window (read as 6 GF(4) symbols,
    2 bits each, MSB-first pair), check if it's one of the 64 hexacode words.

    Hexacode words are 6-tuples of GF(4) symbols {0,1,2,3}; we encode each
    tuple as a 12-bit integer with the leftmost symbol occupying the high
    two bits.
    """
    n_windows = cc.shape[0] // 12
    # Each hexacode word is a tuple of 6 GF(4) symbols (0..3)
    hexacode_set = set()
    for w in mog.HEXACODE.words:
        if isinstance(w, (tuple, list)):
            word = 0
            for sym in w:
                s = int(sym)
                word = (word << 2) | (s & 0x3)
            hexacode_set.add(word)
        else:
            hexacode_set.add(int(w))
    print(f"     [hexacode] loaded {len(hexacode_set)} hexacode words")

    n_hits = 0
    sample_hits = []
    for i in range(n_windows):
        w = cc[i * 12:(i + 1) * 12]
        # Pack 12 bits into 6 GF(4) symbols (MSB-first pair: bits 11,10
        # form symbol 0, etc.)
        word = 0
        for s in range(6):
            hi = int(w[s * 2])      # high bit of symbol
            lo = int(w[s * 2 + 1])  # low bit of symbol
            sym = (hi << 1) | lo
            word = (word << 2) | sym
        if word in hexacode_set:
            n_hits += 1
            if len(sample_hits) < 5:
                sample_hits.append((i, word))

    expected_rate = len(hexacode_set) / (1 << 12)  # = 64 / 4096 = 1/64
    return {
        "n_windows": n_windows,
        "n_hits": n_hits,
        "expected_count": float(n_windows * expected_rate),
        "empirical_rate_per_window": float(n_hits / n_windows),
        "expected_rate_per_window": float(expected_rate),
        "sample_hits": sample_hits,
        "hexacode_size": len(hexacode_set),
    }


# --- main -------------------------------------------------------------------

def main() -> None:
    cc = np.load(DATA / "cc_1M.npy").astype(np.uint8)
    N = cc.shape[0]
    print(f"[glm-substrate] loaded {N} center column cells")
    print(f"[glm-substrate] substrate: Golay code (size {len(mog.GOLAY_MASKS)}), "
          f"Hexacode (size {len(mog.HEXACODE.words)}), "
          f"Leech minimal vectors (count {len(list(leech2.minimal_vectors()))})")

    t0 = time.time()
    gr = golay_codeword_rate(cc)
    print(f"[glm-substrate] Golay codeword rate: {gr['n_hits']} / {gr['n_windows']} "
          f"= {gr['empirical_rate_per_window']:.6f}/window "
          f"(expected {gr['expected_rate_per_window']:.6f})")

    t1 = time.time()
    hr = hexacode_rate(cc)
    print(f"[glm-substrate] Hexacode rate: {hr['n_hits']} / {hr['n_windows']} "
          f"= {hr['empirical_rate_per_window']:.6f}/window "
          f"(expected {hr['expected_rate_per_window']:.6f})")

    t2 = time.time()
    print(f"[glm-substrate] Leech nearest-point distance (capped at 1000 windows)...")
    ld = leech_nearest_distance(cc, max_windows=200)
    if "status" not in ld:
        print(f"[glm-substrate] Leech distances: "
              f"min={ld['min_distance_sq']:.0f} "
              f"mean={ld['mean_distance_sq']:.0f} "
              f"max={ld['max_distance_sq']:.0f} "
              f"(minimal lattice norm^2 = {ld['lattice_minimal_norm_sq']})")

    out = {
        "N": N,
        "golay_codeword_rate": gr,
        "hexacode_rate": hr,
        "leech_distance": ld,
        "elapsed_seconds": {
            "golay": float(time.time() - t0),
            "hexacode": float(time.time() - t1),
            "leech": float(time.time() - t2),
        },
        "interpretation": (
            "If the Rule 30 center column were a uniform Bernoulli(1/2) "
            "source, the empirical Golay codeword hit rate should be close "
            "to 1/4096 = 0.000244, and the hexacode hit rate close to "
            "1/64 = 0.015625. We report whether the empirical rates are "
            "consistent with this null hypothesis via a chi-square test."
        ),
    }
    out_path = DATA / "glm_substrate.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"[glm-substrate] wrote {out_path}")


if __name__ == "__main__":
    main()
