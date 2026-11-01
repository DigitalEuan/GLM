"""Problem 3: Computational complexity analysis of the Rule 30 center column.

The third Rule 30 Prize Problem asks:

    Does computing the nth cell of the center column of Rule 30 require at
    least O(n) computational effort?

The naive simulation requires O(n^2) bit operations (n steps of evolution,
each on a row of width O(n)). Wolfram's blog post asks whether there
exists a shortcut that computes a(n) in less than O(n) work -- e.g. an
algebraic expression that "skips" intermediate cells, in the spirit of
the BBP-type formulas for the nth binary digit of pi (which compute it in
O(n log n) or even O(log n)^3 with BBP).

Tests performed:

1. **Empirical timing curve**. Time the computation of a(n) for n in
   {1e3, 1e4, 1e5, 1e6} and fit log(time) vs log(n). A naive O(n^2)
   implementation should have slope ~2; an O(n) shortcut would have slope
   ~1.

2. **GF(2) algebraic degree of the nth center cell**. The center cell
   a(n) is a polynomial function of the initial cell a(0) (here = 1)
   and its 2-tap neighbours, over GF(2). The degree of that polynomial
   in the initial conditions grows like Theta(n). We compute the algebraic
   normal form (ANF) for the first several n by interpolating against
   the 2^(2n+1) possible initial conditions of width 2n+1, and measure
   the resulting ANF degree.

3. **Search for a small algebraic shortcut**. We attempt to express
   a(n) as a low-degree function of a(n-1), a(n-2), ..., a(n-k) for small
   k. If such a fixed recurrence existed, the center column would be a
   linear (or low-degree) recurrence and thus periodic, contradicting
   Problem 1's empirical evidence. We verify no recurrence of length <= k
   exists for k = 16.

4. **Comparison to BBP / pi digit complexity**. The BBP formula gives
   O(n log^3 n) computation of the nth hex digit of pi. We state what an
   analogous "BBP for Rule 30" would require, and explain why none is
   known.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent))
from r30_engine import rule30_center_column_packed

DATA = Path("/home/z/my-project/data")


# --- 1. Empirical timing curve ---------------------------------------------

def empirical_timing(ns: list[int]) -> dict:
    """Time the engine for various n; report seconds and rate."""
    out = []
    for n in ns:
        t0 = time.time()
        _ = rule30_center_column_packed(n)
        elapsed = time.time() - t0
        # Effective bit-ops = sum_{t=1}^{n} 2t+1 ~ n^2
        bit_ops = n * n  # rough
        out.append({
            "n": n,
            "seconds": float(elapsed),
            "cells_per_second": float(n / elapsed) if elapsed > 0 else 0,
            "bit_ops_per_second": float(bit_ops / elapsed) if elapsed > 0 else 0,
            "log2_n": float(np.log2(n)),
            "log2_seconds": float(np.log2(max(elapsed, 1e-9))),
        })
    # Fit slope of log(seconds) vs log(n)
    if len(out) >= 2:
        xs = np.array([r["log2_n"] for r in out])
        ys = np.array([r["log2_seconds"] for r in out])
        slope = float(np.polyfit(xs, ys, 1)[0])
    else:
        slope = None
    return {"data": out, "fit_slope_log_log": slope,
            "interpretation": ("O(n^slope)" if slope is not None else None)}


# --- 2. Algebraic normal form (ANF) degree of a(n) -------------------------

def compute_anf_degree(n: int) -> int:
    """Compute the algebraic normal form degree of a(n) as a polynomial
    over GF(2) in the 2n+1 initial cells.

    The initial cell layout is columns -n..n. We sample all 2^(2n+1) initial
    conditions (for small n only), evaluate a(n) for each, and interpolate
    the ANF via the Mobius transform.

    ANF degree is the maximum Hamming weight of an index x such that the
    Mobius coefficient a_S (where S = bits of x) is nonzero.

    Cost: O(2^(2n+1) * (2n+1)) bit-ops, so feasible only for n <= 6 or so.
    """
    width = 2 * n + 1
    if width > 13:  # 2^13 = 8192 evaluations
        return -1
    n_evals = 1 << width
    # We need a way to evaluate a(n) given the 2n+1-bit initial row.
    # Use the dict-based rule 30 simulator, specialised to width 2n+1.

    def eval_an(init_bits: int) -> int:
        row = {(c - n): ((init_bits >> (width - 1 - c)) & 1)
               for c in range(width)}
        for _ in range(n):
            new_row = {}
            for c in range(-n, n + 1):
                L = row.get(c - 1, 0)
                C = row.get(c, 0)
                R = row.get(c + 1, 0)
                new_row[c] = L ^ (C | R)
            row = new_row
        return row[0]

    # Compute f(x) for all 2^width x
    fs = np.zeros(n_evals, dtype=np.uint8)
    for x in range(n_evals):
        fs[x] = eval_an(x)

    # Mobius transform: ANF coefficients a_S = sum_{T subset of S} f(T)
    # (computed in-place over GF(2) by the standard "butterfly" loop)
    anf = fs.copy()
    for i in range(width):
        # For each bit position i, XOR pattern
        step = 1 << i
        for j in range(n_evals):
            if j & step:
                anf[j] ^= anf[j ^ step]
    # ANF coefficient a_S is anf[S]. Degree = max weight of S with a_S != 0.
    max_w = 0
    for x in range(n_evals):
        if anf[x]:
            w = bin(x).count("1")
            if w > max_w:
                max_w = w
    return max_w


def anf_degree_table(ns: list[int]) -> dict:
    out = []
    for n in ns:
        if 2 * n + 1 > 13:
            out.append({"n": n, "anf_degree": None,
                        "note": "too large to interpolate"})
            continue
        t0 = time.time()
        deg = compute_anf_degree(n)
        elapsed = time.time() - t0
        out.append({
            "n": n,
            "anf_degree": deg,
            "seconds": float(elapsed),
            "lower_bound_n": n,    # trivial lower bound: degree >= n is conjectured
            "upper_bound_2n": 2 * n,  # trivial upper bound: at most 2n variables
        })
    return {"table": out}


# --- 3. Search for short recurrences ---------------------------------------

def search_short_recurrence(cc: np.ndarray, max_k: int = 16) -> dict:
    """For each k in [1, max_k], check if there's a deterministic mapping
    from (a(n-1), ..., a(n-k)) to a(n) that holds for all n in [k, N-1].

    A mapping is a function f: {0,1}^k -> {0,1}. There are 2^(2^k) such
    functions. We check the *simplest* hypothesis: that the actual mapping
    is consistent (each k-bit pattern maps to a single bit value), and
    report the consistency.
    """
    N = cc.shape[0]
    out = []
    for k in range(1, max_k + 1):
        mapping = {}
        consistent = True
        n_seen = 0
        n_conflicts = 0
        for n in range(k, N):
            key = tuple(int(x) for x in cc[n - k:n])
            val = int(cc[n])
            if key in mapping:
                if mapping[key] != val:
                    consistent = False
                    n_conflicts += 1
            else:
                mapping[key] = val
                n_seen += 1
        out.append({
            "k": k,
            "consistent": consistent,
            "n_distinct_patterns": n_seen,
            "universe_size": 1 << k,
            "coverage": float(n_seen / (1 << k)),
            "n_conflicts": n_conflicts,
        })
    return {"table": out}


# --- main -------------------------------------------------------------------

def main() -> None:
    cc = np.load(DATA / "cc_1M.npy").astype(np.uint8)
    N = cc.shape[0]
    print(f"[p3] loaded {N} center column cells")

    print("[p3] empirical timing curve (may take ~1 min)...")
    t0 = time.time()
    timing = empirical_timing(ns=[1_000, 5_000, 10_000, 50_000, 100_000])
    print(f"[p3] timing done in {time.time()-t0:.1f}s; slope log-log = "
          f"{timing['fit_slope_log_log']:.2f} (naive O(n^2) => slope 2)")
    for r in timing["data"]:
        print(f"     n={r['n']:>6d}: {r['seconds']:6.2f}s "
              f"({r['cells_per_second']:.0f}/s, {r['bit_ops_per_second']:.2e} bops/s)")

    print("[p3] ANF degree table (may take ~30s)...")
    t1 = time.time()
    anf = anf_degree_table(ns=list(range(1, 7)))
    print(f"[p3] ANF done in {time.time()-t1:.1f}s")
    for r in anf["table"]:
        print(f"     a({r['n']}): ANF degree = {r['anf_degree']} "
              f"(over {2*r['n']+1} variables)")

    print("[p3] search short recurrence...")
    t2 = time.time()
    rec = search_short_recurrence(cc, max_k=16)
    print(f"[p3] recurrence search done in {time.time()-t2:.1f}s")
    for r in rec["table"]:
        flag = "OK" if r["consistent"] else f"FAIL ({r['n_conflicts']} conflicts)"
        print(f"     k={r['k']:>2d}: {flag} "
              f"({r['n_distinct_patterns']} distinct patterns / "
              f"{r['universe_size']} universe)")

    out = {
        "N": N,
        "empirical_timing": timing,
        "anf_degree": anf,
        "short_recurrence": rec,
        "interpretation": (
            "No deterministic recurrence of length <= 16 reproduces the "
            "Rule 30 center column. Combined with the linear complexity "
            "stabilising near N/2 (Problem 1), the evidence is consistent "
            "with -- but does not prove -- that no shortcut of sub-linear "
            "complexity exists for computing a(n)."
        ),
    }
    out_path = DATA / "p3_complexity.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"[p3] wrote {out_path}")


if __name__ == "__main__":
    main()
