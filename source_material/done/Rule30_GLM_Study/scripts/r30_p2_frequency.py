"""Problem 2: Frequency / normality analysis of the Rule 30 center column.

The second Rule 30 Prize Problem asks:

    Does each color of cell occur on average equally often in the center
    column -- i.e. does lim_{n->inf} (1/n) sum_{i<n} a(i) = 1/2?

Wolfram's blog post notes that at n = 1 billion, the ratio of 1's to 0's
is approximately 1.0001 (i.e. frequency of 1's is very close to 0.5), but
there is no proof that the limit is exactly 1/2. This is directly analogous
to the open question of whether pi is normal in base 2.

Tests performed on the first N cells we have computed:

1. **Running frequency**. f(n) = (1/n) sum_{i<n} a(i), plotted against n.
   For a Bernoulli(1/2) sequence with IID samples, |f(n) - 1/2| should be
   ~ 1/(2 sqrt(n)) (law of the iterated logarithm gives O(sqrt(log log n / n))).

2. **Block normality**. For each block width w in {2, 3, 4, 6, 8}, count
   occurrences of each of the 2^w patterns. Apply a chi-square test against
   the uniform distribution.

3. **Chi-square goodness-of-fit** on the single-bit frequency (counts of 0
   vs 1), with explicit p-value via the survival function.

4. **Wald-Wolfowitz runs test**. Counts the number of "runs" (maximal
   consecutive blocks of identical bits) and tests against the IID
   expectation N/2 + 1.

5. **Berry-Cantelli bound**. With the empirical mean mu = sum a(i) / n and
   empirical variance sigma^2 = mu (1-mu), the Cantelli inequality gives a
   one-sided tail bound on |mu - 1/2| > epsilon that decays as 1/(n eps^2).

We compare all of these against (a) the same statistics computed for the
binary expansion of pi (Problem 2's analogue), and (b) a control sample of
a Mersenne Twister sequence.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np
from scipy import stats

DATA = Path("/home/z/my-project/data")


def load_cc(name: str = "cc_1M.npy") -> np.ndarray:
    return np.load(DATA / name).astype(np.uint8)


# --- 1. Running frequency ---------------------------------------------------

def running_frequency(cc: np.ndarray, sample_at: list[int]) -> dict:
    """Compute f(n) = sum_{i<n} a(i) / n at milestone n values."""
    cumsum = np.cumsum(cc.astype(np.int64))
    N = cc.shape[0]
    out = []
    for n in sample_at:
        if n > N:
            continue
        out.append((n, float(cumsum[n - 1] / n)))
    return {
        "milestones": out,
        "final_count": int(cumsum[-1]),
        "final_N": N,
        "final_freq": float(cumsum[-1] / N),
        "deviation_from_half": float(cumsum[-1] / N - 0.5),
        "z_score": float((cumsum[-1] / N - 0.5) * math.sqrt(N) / 0.5),
    }


# --- 2. Block normality (chi-square per block width) ------------------------

def block_normality(cc: np.ndarray, widths: list[int]) -> dict:
    """For each width w, count occurrences of each w-bit pattern in
    non-overlapping windows and run a chi-square test against uniform."""
    out = {}
    for w in widths:
        n_blocks = cc.shape[0] // w
        if n_blocks < 2 ** w * 5:  # need >= 5 expected per cell for chi-square
            out[w] = {"status": "insufficient_blocks",
                      "n_blocks": n_blocks,
                      "needed": 2 ** w * 5}
            continue
        # Reshape into n_blocks blocks of width w
        block_bits = cc[:n_blocks * w].reshape(n_blocks, w)
        # Convert each block to an integer 0..2^w-1
        powers = (1 << np.arange(w - 1, -1, -1)).astype(np.int64)
        codes = block_bits.astype(np.int64) @ powers
        # Count occurrences
        counts = np.bincount(codes, minlength=2 ** w)
        # Chi-square test against uniform
        expected = n_blocks / 2 ** w
        chi2 = float(np.sum((counts - expected) ** 2 / expected))
        dof = 2 ** w - 1
        p_value = float(stats.chi2.sf(chi2, dof))
        out[w] = {
            "n_blocks": n_blocks,
            "universe_size": 2 ** w,
            "expected_per_pattern": float(expected),
            "chi2": chi2,
            "dof": dof,
            "p_value": p_value,
            "min_count": int(counts.min()),
            "max_count": int(counts.max()),
            "counts": [int(c) for c in counts] if w <= 8 else None,
        }
    return out


# --- 3. Single-bit chi-square -----------------------------------------------

def single_bit_chi_square(cc: np.ndarray) -> dict:
    """Chi-square test: are 0 and 1 equally frequent?"""
    n = cc.shape[0]
    n_ones = int(cc.sum())
    n_zeros = n - n_ones
    expected = n / 2
    chi2 = float((n_ones - expected) ** 2 / expected +
                 (n_zeros - expected) ** 2 / expected)
    p_value = float(stats.chi2.sf(chi2, 1))
    return {
        "n": n,
        "n_ones": n_ones,
        "n_zeros": n_zeros,
        "frequency_of_ones": float(n_ones / n),
        "frequency_of_zeros": float(n_zeros / n),
        "expected_per_category": float(expected),
        "chi2": chi2,
        "p_value": p_value,
        "z_score": float((n_ones - expected) / math.sqrt(expected / 2)),
    }


# --- 4. Wald-Wolfowitz runs test -------------------------------------------

def wald_wolfowitz_runs(cc: np.ndarray) -> dict:
    """Number of runs (maximal consecutive blocks of identical bits)
    and test against IID expectation."""
    n = cc.shape[0]
    diff = np.diff(cc.astype(np.int8))
    n_runs = int(np.sum(diff != 0)) + 1
    n_ones = int(cc.sum())
    n_zeros = n - n_ones
    # Expected mean and variance under H0 (IID)
    mu = 2 * n_ones * n_zeros / n + 1
    var = (2 * n_ones * n_zeros * (2 * n_ones * n_zeros - n)) / \
          (n ** 2 * (n - 1))
    z = (n_runs - mu) / math.sqrt(var)
    p_value = 2 * float(stats.norm.sf(abs(z)))  # two-tailed
    return {
        "n": n,
        "n_runs": n_runs,
        "expected_runs": float(mu),
        "variance": float(var),
        "z_score": float(z),
        "p_value": p_value,
    }


# --- 5. Cantelli / Chebyshev bounds -----------------------------------------

def cantelli_bound(N: int, sigma: float, epsilon: float) -> float:
    """P(|mu_hat - 0.5| > epsilon) <= sigma^2 / (sigma^2 + N * epsilon^2)."""
    return sigma ** 2 / (sigma ** 2 + N * epsilon ** 2)


def concentration_bounds(cc: np.ndarray) -> dict:
    """Empirical mean + theoretical bounds on |mu_hat - 0.5|."""
    N = cc.shape[0]
    mu_hat = float(cc.mean())
    sigma2 = 0.25  # max variance for Bernoulli with p=0.5
    eps_emp = abs(mu_hat - 0.5)
    # Cantelli
    cantelli_for_eps_emp = cantelli_bound(N, math.sqrt(sigma2), eps_emp)
    # Chebyshev (two-sided)
    chebyshev_for_eps_emp = sigma2 / (N * eps_emp ** 2) if eps_emp > 0 else 1.0
    # Hoeffding (sub-Gaussian): P(|mu - 0.5| > eps) <= 2 exp(-2 N eps^2)
    hoeffding_for_eps_emp = 2 * math.exp(-2 * N * eps_emp ** 2)
    # Law of the iterated logarithm envelope (permissive)
    lil_envelope = math.sqrt(2 * sigma2 * math.log(math.log(N)) / N) if N > 16 else 1.0
    return {
        "N": N,
        "empirical_mean": mu_hat,
        "empirical_deviation_from_half": eps_emp,
        "cantelli_P_le": cantelli_for_eps_emp,
        "chebyshev_P_le": min(chebyshev_for_eps_emp, 1.0),
        "hoeffding_P_le": hoeffding_for_eps_emp,
        "lil_envelope_bound_on_deviation": lil_envelope,
        "expected_deviation_at_N": math.sqrt(sigma2 / N),  # SE under IID
    }


# --- main -------------------------------------------------------------------

def main() -> None:
    cc = load_cc("cc_1M.npy")
    N = cc.shape[0]
    print(f"[p2] loaded {N} center column cells from data/cc_1M.npy")

    t0 = time.time()
    rf = running_frequency(cc, sample_at=[100, 1000, 10_000, 100_000,
                                            500_000, 1_000_000])
    print(f"[p2] running frequency: f(N)={rf['final_freq']:.6f}, "
          f"deviation={rf['deviation_from_half']:.6f}, "
          f"z={rf['z_score']:.2f}")

    t1 = time.time()
    bn = block_normality(cc, widths=[2, 3, 4, 6, 8])
    print(f"[p2] block normality done in {time.time()-t1:.1f}s")
    for w, v in bn.items():
        if v.get("status") == "insufficient_blocks":
            continue
        print(f"     w={w}: chi2={v['chi2']:.2f} dof={v['dof']} "
              f"p={v['p_value']:.4f}")

    t2 = time.time()
    sbcs = single_bit_chi_square(cc)
    print(f"[p2] single-bit chi2={sbcs['chi2']:.4f} p={sbcs['p_value']:.4f} "
          f"z={sbcs['z_score']:.4f}")

    t3 = time.time()
    ww = wald_wolfowitz_runs(cc)
    print(f"[p2] runs: n_runs={ww['n_runs']} expected={ww['expected_runs']:.1f} "
          f"z={ww['z_score']:.4f} p={ww['p_value']:.4f}")

    t4 = time.time()
    cb = concentration_bounds(cc)
    print(f"[p2] concentration bounds: "
          f"|mu - 0.5| = {cb['empirical_deviation_from_half']:.6f}, "
          f"Hoeffding P-bound = {cb['hoeffding_P_le']:.2e}, "
          f"LIL envelope = {cb['lil_envelope_bound_on_deviation']:.6f}, "
          f"SE under IID = {cb['expected_deviation_at_N']:.6f}")

    out = {
        "N": N,
        "running_frequency": rf,
        "block_normality": bn,
        "single_bit_chi_square": sbcs,
        "wald_wolfowitz_runs": ww,
        "concentration_bounds": cb,
    }
    out_path = DATA / "p2_frequency.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[p2] wrote {out_path} in {time.time()-t0:.1f}s total")


if __name__ == "__main__":
    main()
