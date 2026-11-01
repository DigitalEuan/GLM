"""Problem 1: Periodicity analysis of the Rule 30 center column.

The first Rule 30 Prize Problem asks:

    Does the center column of Rule 30, starting from a single live cell,
    ever become periodic -- i.e. does there exist T > 0 and N0 such that
    for all n >= N0, a(n + T) = a(n)?

Wolfram's blog post notes the center column is empirically verified
non-periodic for the first billion cells (Xiangdong Wen's computation,
2019). We cannot match that scale, but we can apply a battery of
statistical and combinatorial tests for non-periodicity on the first N
cells we have computed.

Tests performed:

1. **Period search**. For every candidate period T in [1, T_max], check
   whether the center column actually satisfies a(n + T) == a(n) for all n
   in [N - T_max, N - 1]. We compute the Hamming disagreement rate.

2. **Discrete autocorrelation**. The autocorrelation
       rho(T) = sum_n (-1)^{a(n) XOR a(n+T)}
   normalised by N. For a random Bernoulli(1/2) sequence we expect rho(T)
   ~ N(0, 1/N); for a periodic sequence with period T, rho(T) -> +/- 1.

3. **Birthday-paradox test on n-grams**. If the sequence were periodic
   with period T, the n-grams of width n would repeat in lockstep. We
   measure the time-to-first-collision of each n-gram width w in
   {2, 3, 4, 6, 8} and compare against the birthday bound for a uniform
   random source.

4. **Linear complexity profile**. The Berlekamp-Massey algorithm on the
   GF(2) sequence returns the shortest LFSR that reproduces the prefix.
   For a periodic sequence of period T, the linear complexity stabilises
   at <= T. For a random sequence it grows ~ n/2.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

DATA = Path("/home/z/my-project/data")


def load_cc(name: str = "cc_1M.npy") -> np.ndarray:
    return np.load(DATA / name).astype(np.uint8)


# --- 1. Period search --------------------------------------------------------

def hamming_period_scan(cc: np.ndarray, T_max: int) -> dict:
    """For each T in [1, T_max], compute disagreement rate vs period T."""
    N = cc.shape[0]
    out = np.zeros(T_max + 1, dtype=np.float64)
    for T in range(1, T_max + 1):
        # Compare cc[n] vs cc[n+T] for n in [0, N-1-T]
        a = cc[:N - T]
        b = cc[T:]
        out[T] = float(np.mean(a != b))
    return {
        "T_max": T_max,
        "min_disagreement": float(out[1:].min()),
        "T_at_min": int(1 + int(out[1:].argmin())),
        "max_disagreement": float(out[1:].max()),
        "mean_disagreement": float(out[1:].mean()),
        # Disagreement-rate distribution
        "p05": float(np.percentile(out[1:], 5)),
        "p50": float(np.percentile(out[1:], 50)),
        "p95": float(np.percentile(out[1:], 95)),
        "disagreement_at_T_list": [
            (T, float(out[T])) for T in [1, 2, 4, 8, 16, 32, 64, 128,
                                          256, 512, 1024, 2048, 4096]
            if T <= T_max
        ],
    }


# --- 2. Discrete autocorrelation --------------------------------------------

def autocorrelation(cc: np.ndarray, lags: list[int]) -> dict:
    """rho(T) = (1/N) sum_n s(n) s(n+T), where s(n) = (-1)^cc[n]."""
    s = 1 - 2 * cc.astype(np.int64)  # 0 -> +1, 1 -> -1
    N = s.shape[0]
    out = []
    for T in lags:
        if T >= N:
            continue
        rho = float(np.mean(s[:N - T] * s[T:]))
        out.append((T, rho))
    return {"lags": lags, "values": out,
            "max_abs_rho": max(abs(r) for _, r in out),
            "lag_at_max": max(out, key=lambda x: abs(x[1]))[0]}


# --- 3. Birthday-paradox n-gram test -----------------------------------------

def ngram_collision_times(cc: np.ndarray, widths: list[int]) -> dict:
    """For each w, find the first n where the n-gram cc[n:n+w] has been
    seen before (i.e. the time of first repeat)."""
    N = cc.shape[0]
    out = {}
    for w in widths:
        if N < 2 ** w + 10:
            # Too few samples to test this width
            out[w] = {"first_collision_at": None,
                      "n_unique": 0,
                      "birthday_bound": 2 ** (w / 2),
                      "note": "insufficient samples"}
            continue
        seen = {}
        first_collision = None
        for n in range(N - w + 1):
            ng = int(np.packbits(cc[n:n + w])[0] >> (8 - w)) if w <= 8 else \
                 hash(cc[n:n + w].tobytes())
            if ng in seen:
                first_collision = n
                break
            seen[ng] = n
        out[w] = {"first_collision_at": int(first_collision) if first_collision else None,
                  "n_unique": len(seen),
                  "birthday_bound": 2 ** (w / 2),
                  "universe_size": 2 ** w}
    return out


# --- 4. Linear complexity profile (Berlekamp-Massey over GF(2)) -------------

def berlekamp_massey(seq: np.ndarray) -> list[int]:
    """Return the linear complexity profile: L(n) = shortest LFSR length
    that produces the first n+1 bits of seq. Returns a list of length len(seq).
    """
    n = len(seq)
    L = 0
    C = [1] + [0] * n  # connection polynomial
    B = [1] + [0] * n  # last C before length change
    x = 1  # number of iterations since L last changed
    profile = []
    for i in range(n):
        # Compute discrepancy
        d = 0
        for j in range(L + 1):
            d ^= (C[j] & seq[i - j])
        if d == 0:
            x += 1
        else:
            T = C[:]
            # C = C - (d * x^(-1)) * x^(L) * B  -- here, just XOR B shifted
            for j in range(n - i + L + 1 if i - L >= 0 else 0):
                pass
            # Simpler: implement standard BM
            coef = 1  # over GF(2), d/1 = 1
            # C = C XOR (B shifted left by x positions, then times x^L later)
            for j in range(L + 1):
                if j + x < n + 1:
                    C[j + x] ^= B[j]
            if 2 * L <= i:
                L = i + 1 - L
                B = T
                x = 1
            else:
                x += 1
        profile.append(L)
    return profile


def linear_complexity_profile(cc: np.ndarray, sample_at: list[int]) -> dict:
    """Sample the linear complexity at a few milestones; full BM is O(N^2)
    in the worst case so we cap to a few thousand bits."""
    N = min(cc.shape[0], 5000)  # BM is O(N^2) in our naive impl
    profile = berlekamp_massey(cc[:N].astype(np.int8).tolist())
    return {
        "N_analysed": N,
        "L_at": [(n, profile[n - 1]) for n in sample_at if n <= N],
        "final_L": profile[-1],
        "expected_random_L": N / 2,  # for random sequence, L ~ N/2
    }


# --- main -------------------------------------------------------------------

def main() -> None:
    cc = load_cc("cc_1M.npy")
    N = cc.shape[0]
    print(f"[p1] loaded {N} center column cells from data/cc_1M.npy")

    t0 = time.time()
    period_scan = hamming_period_scan(cc, T_max=min(8192, N // 4))
    print(f"[p1] period scan (T_max={period_scan['T_max']}) done in "
          f"{time.time()-t0:.1f}s")
    print(f"     min disagreement = {period_scan['min_disagreement']:.6f} "
          f"at T={period_scan['T_at_min']}")
    print(f"     mean disagreement = {period_scan['mean_disagreement']:.6f} "
          f"(random expectation = 0.5)")

    t1 = time.time()
    ac = autocorrelation(cc, lags=[1, 2, 4, 8, 16, 32, 64, 128, 256, 512,
                                    1024, 2048, 4096, 8192])
    print(f"[p1] autocorrelation done in {time.time()-t1:.1f}s")
    print(f"     max |rho(T)| = {ac['max_abs_rho']:.4f} at T={ac['lag_at_max']}")
    print(f"     expected |rho| under H0 (random) ~ {1/np.sqrt(N):.4f}")

    t2 = time.time()
    coll = ngram_collision_times(cc, widths=[2, 3, 4, 6, 8, 12, 16])
    print(f"[p1] n-gram collisions done in {time.time()-t2:.1f}s")
    for w, v in coll.items():
        print(f"     w={w}: first collision at n={v['first_collision_at']}, "
              f"birthday bound={v['birthday_bound']:.0f}, "
              f"universe={v['universe_size']}")

    t3 = time.time()
    lcp = linear_complexity_profile(cc, sample_at=[100, 500, 1000, 2000, 5000])
    print(f"[p1] linear complexity profile done in {time.time()-t3:.1f}s")
    print(f"     final L = {lcp['final_L']} (random expectation = "
          f"{lcp['expected_random_L']:.0f})")

    out = {
        "N": N,
        "period_scan": period_scan,
        "autocorrelation": ac,
        "ngram_collisions": coll,
        "linear_complexity": lcp,
    }
    out_path = DATA / "p1_periodicity.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[p1] wrote {out_path}")


if __name__ == "__main__":
    main()
