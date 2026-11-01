"""Compute the actual ANF polynomials (not just the degree) of a(n)
for small n, and identify the structure of the highest-degree
monomials. This is the data needed to formulate the inductive
hypothesis deg(a(n+1)) = deg(a(n)) + 2 (for n >= 2).

For each n in {1, 2, 3, 4, 5, 6}, we compute:
  * The full ANF coefficient vector (which of the 2^(2n+1) monomials
    have nonzero coefficient).
  * The degree (max Hamming weight of a nonzero monomial).
  * The list of highest-degree monomials (which subsets of variables
    appear at the top degree).
  * The pattern: how do the highest-degree monomials at n+1 relate
    to those at n?

The Rule 30 update rule over GF(2) is:
  f(L, C, R) = L XOR (C OR R) = L XOR C XOR R XOR (C AND R)
            = L + C + R + C*R   (over GF(2))

The key structural insight we're looking for: the substitution
P -> P_left + P_center + P_right + P_center * P_right increases
the degree by exactly 2 at each step (for n >= 2), because:
  * The linear part (P_left + P_center + P_right) has degree <= max(deg).
  * The product part (P_center * P_right) has degree <= deg(P_center) + deg(P_right)
    in the FREE polynomial ring, but in the BOOLEAN polynomial ring
    (where x_i^2 = x_i), the degree is bounded by the number of
    DISTINCT variables in the product, which is at most (2n+1) + 1 = 2n+2
    for the step from n to n+1.

The empirical pattern deg(a(n)) = 2n-1 means the product's degree
is EXACTLY 2n+1 (one less than the maximum 2n+2), suggesting a
specific structural constraint on how P_center and P_right share
variables.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    from numba import njit
    NUMBA = True
except ImportError:
    NUMBA = False
    def njit(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return args[0]
        def deco(f): return f
        return deco

DATA = Path("/home/z/my-project/data")


@njit(cache=True)
def rule30_eval_one(init_bits: int, width: int, n_steps: int) -> int:
    """Evaluate a(n_steps) where the initial row of width=2n+1 cells
    is given by `init_bits` (bit i is column i - n). Returns 0 or 1.
    """
    row = init_bits
    for _ in range(n_steps):
        new_row = 0
        for c in range(width):
            L = (row >> (c - 1)) & 1 if c >= 1 else 0
            C = (row >> c) & 1
            R = (row >> (c + 1)) & 1 if c < width - 1 else 0
            new = L ^ (C | R)
            new_row |= (new << c)
        row = new_row
    return (row >> n_steps) & 1


@njit(cache=True)
def mobius_transform_inplace(anf: np.ndarray, width: int) -> None:
    """In-place Mobius transform over GF(2)."""
    n = 1 << width
    for i in range(width):
        step = 1 << i
        for j in range(n):
            if j & step:
                anf[j] ^= anf[j ^ step]


def compute_anf_polynomial(n: int) -> dict:
    """Compute the full ANF of a(n) as a polynomial in 2n+1 variables
    over GF(2). Returns the ANF coefficient vector (length 2^(2n+1)),
    where anf[S] = 1 iff the monomial prod_{i in S} x_i has nonzero
    coefficient.
    """
    width = 2 * n + 1
    n_evals = 1 << width

    if n_evals > (1 << 19):  # cap at n=9 (2^19 = 524288)
        return {"n": n, "error": "too large"}

    # Evaluate a(n) for all 2^width initial conditions
    fs = np.zeros(n_evals, dtype=np.uint8)
    for x in range(n_evals):
        fs[x] = rule30_eval_one(x, width, n)

    # Mobius transform
    anf = fs.copy()
    mobius_transform_inplace(anf, width)

    # Find all nonzero monomials
    nonzero_monomials = [i for i in range(n_evals) if anf[i]]
    degrees = [bin(i).count("1") for i in nonzero_monomials]
    max_degree = max(degrees) if degrees else 0

    # Group monomials by degree
    by_degree: Dict[int, List[int]] = {}
    for m, d in zip(nonzero_monomials, degrees):
        by_degree.setdefault(d, []).append(m)

    # For the highest-degree monomials, identify which variables they involve
    # Variable i corresponds to bit i in the monomial index.
    # Variable 0 = column -n, variable n = column 0 (center), variable 2n = column +n.
    highest_degree_monomials = by_degree.get(max_degree, [])
    highest_degree_var_sets = []
    for m in highest_degree_monomials:
        var_set = tuple(i for i in range(width) if (m >> i) & 1)
        # Convert to column positions (variable i -> column i - n)
        col_set = tuple(v - n for v in var_set)
        highest_degree_var_sets.append({
            "monomial_index": m,
            "variables": var_set,
            "columns": col_set,
            "weight": len(var_set),
        })

    return {
        "n": n,
        "width": width,
        "n_evals": n_evals,
        "n_nonzero_monomials": len(nonzero_monomials),
        "max_degree": max_degree,
        "n_highest_degree_monomials": len(highest_degree_monomials),
        "highest_degree_monomials": highest_degree_var_sets[:20],  # cap for display
        "monomials_by_degree": {d: len(v) for d, v in sorted(by_degree.items())},
    }


def analyze_inductive_pattern(results: list) -> dict:
    """Analyze how the highest-degree monomials evolve from n to n+1."""
    pattern = []
    for i in range(len(results) - 1):
        r_n = results[i]
        r_n1 = results[i + 1]
        if "error" in r_n or "error" in r_n1:
            continue
        n = r_n["n"]
        deg_n = r_n["max_degree"]
        deg_n1 = r_n1["max_degree"]
        increment = deg_n1 - deg_n

        # Look at the column positions of the highest-degree monomials
        cols_n = set()
        for m in r_n["highest_degree_monomials"]:
            cols_n.update(m["columns"])
        cols_n1 = set()
        for m in r_n1["highest_degree_monomials"]:
            cols_n1.update(m["columns"])

        pattern.append({
            "n_to_n+1": f"{n} -> {n+1}",
            "deg_n": deg_n,
            "deg_n+1": deg_n1,
            "increment": increment,
            "expected_increment": 2,
            "matches_conjecture": increment == 2,
            "columns_in_highest_deg_monomials_n": sorted(cols_n),
            "columns_in_highest_deg_monomials_n+1": sorted(cols_n1),
            "new_columns": sorted(cols_n1 - cols_n),
            "dropped_columns": sorted(cols_n - cols_n1),
        })
    return pattern


def main() -> None:
    # JIT warmup
    print("[anf-poly] JIT warmup with n=2...")
    _ = compute_anf_polynomial(2)

    results = []
    for n in range(1, 7):
        print(f"\n[anf-poly] computing full ANF polynomial for n={n} "
              f"(width={2*n+1}, 2^{2*n+1}={1<<(2*n+1)} initial conditions)...",
              flush=True)
        t0 = time.time()
        r = compute_anf_polynomial(n)
        elapsed = time.time() - t0
        if "error" in r:
            print(f"  skipped: {r['error']}")
            continue
        print(f"  n={r['n']}: degree={r['max_degree']}, "
              f"{r['n_nonzero_monomials']} nonzero monomials, "
              f"{r['n_highest_degree_monomials']} at top degree, "
              f"in {elapsed:.2f}s")
        print(f"  monomials by degree: {r['monomials_by_degree']}")
        print(f"  highest-degree monomials (first 5):")
        for m in r["highest_degree_monomials"][:5]:
            print(f"    columns {m['columns']} (weight {m['weight']})")
        results.append(r)

    # Analyze the inductive pattern
    print("\n[anf-poly] inductive pattern analysis:")
    pattern = analyze_inductive_pattern(results)
    for p in pattern:
        print(f"  {p['n_to_n+1']}: deg {p['deg_n']} -> {p['deg_n+1']} "
              f"(increment {p['increment']}, expected 2: "
              f"{'OK' if p['matches_conjecture'] else 'MISMATCH'})")
        print(f"    columns at top degree (n):   {p['columns_in_highest_deg_monomials_n']}")
        print(f"    columns at top degree (n+1): {p['columns_in_highest_deg_monomials_n+1']}")
        print(f"    new columns: {p['new_columns']}")
        print(f"    dropped columns: {p['dropped_columns']}")

    out = {
        "results": results,
        "inductive_pattern": pattern,
        "conjecture": "deg(a(n+1)) = deg(a(n)) + 2 for n >= 2",
        "conjecture_holds_for_n_2_to_N": all(
            p["matches_conjecture"] for p in pattern if int(p["n_to_n+1"].split(" -> ")[0]) >= 2
        ),
    }
    out_path = DATA / "p3_anf_polynomials.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n[anf-poly] wrote {out_path}")


if __name__ == "__main__":
    main()
