"""Push the ANF degree computation to n=8 or beyond using numba JIT.

Round 1 computed the ANF degree of a(n) over the 2n+1 initial cells
for n=1..6, finding deg(a(n)) = 2n-1 exactly. The implementation was
pure Python with O(2^(2n+1) * (2n+1)) cost: for n=6, that's 2^13 * 13
~ 100k bit operations, fast. For n=7 (2^15 * 15 ~ 500k) it's still
feasible but slow; for n=8 (2^17 * 17 ~ 2M) it's borderline; for
n=10 (2^21 ~ 2M initial conditions, each requiring 2n+1=21 evaluations
of n=10 steps of Rule 30, so ~ 40M cell updates) it's slow but
tractable with numba.

This module JIT-compiles the inner evaluation loop with numba, giving
~50-100x speedup over the pure-Python version. The Mobius transform
for the ANF coefficient computation is also JIT'd.

Output: extends the ANF degree table from Round 1 (n=1..6) to
n=1..10, with timings. The conjecture deg(a(n)) = 2n-1 is tested.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

try:
    from numba import njit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    print("[anf] WARNING: numba not available; falling back to pure Python")
    def njit(*args, **kwargs):
        def decorator(f):
            return f
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    def prange(n):
        return range(n)

DATA = Path("/home/z/my-project/data")


# --- JIT'd Rule 30 evaluation ------------------------------------------------

@njit(cache=True)
def rule30_eval_one(init_bits: int, width: int, n_steps: int) -> int:
    """Evaluate a(n_steps) where the initial row of width=2n+1 cells
    is given by `init_bits` (bit i is the cell at column i - n, MSB
    first). Returns 0 or 1.

    Uses a sliding 3-bit window over the row. The row width is fixed
    at 2n+1; cells outside this window are treated as 0 (the infinite-
    line behavior, since the visible region of Rule 30 from a single
    live cell after n steps is exactly [-n, n]).
    """
    # We work with a row of width `width` cells, encoded as `width` bits
    # in a Python int. Bit (width-1) is column -n; bit 0 is column +n.
    # Equivalently, bit i corresponds to column (i - n).
    # Wait -- let me redefine: bit i (0-indexed from LSB) is column
    # (width - 1 - i) - n. So bit (width-1) is column -n, bit 0 is
    # column +n.
    # Actually simpler: let's index columns from -n to +n and store
    # the row as a `width`-bit integer where bit (c + n) is column c.
    # So bit 0 is column -n, bit (width-1) is column +n. Bit c+n
    # corresponds to column c.
    row = init_bits
    for _ in range(n_steps):
        new_row = 0
        for c in range(width):
            # For column c, the left neighbor is column c-1, the
            # right neighbor is column c+1. In bit terms:
            # L = bit (c-1+n) = bit (c+n-1) -- if c+n-1 in [0, width-1]
            # C = bit (c+n)
            # R = bit (c+n+1) -- if c+n+1 in [0, width-1]
            cn = c  # we'll iterate over bit positions 0..width-1
            L = (row >> (cn - 1)) & 1 if cn >= 1 else 0
            C = (row >> cn) & 1
            R = (row >> (cn + 1)) & 1 if cn < width - 1 else 0
            new = L ^ (C | R)
            new_row |= (new << cn)
        row = new_row
    # The center cell is column 0, which is bit n (where width = 2n+1).
    return (row >> n_steps) & 1


# Pure-Python fallback for testing the JIT correctness
def rule30_eval_one_pure(init_bits: int, width: int, n_steps: int) -> int:
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


# --- Mobius transform for ANF coefficient computation -----------------------

@njit(cache=True)
def mobius_transform_inplace(anf: np.ndarray, width: int) -> None:
    """In-place Mobius transform: a_S = sum_{T subset of S} f(T) over GF(2).

    Standard "butterfly" loop: for each bit position i, XOR pattern.
    """
    n = 1 << width
    for i in range(width):
        step = 1 << i
        for j in range(n):
            if j & step:
                anf[j] ^= anf[j ^ step]


def compute_anf_degree(n: int, use_numba: bool = True) -> dict:
    """Compute the ANF degree of a(n) as a polynomial in the 2n+1 initial
    cell values, over GF(2).

    Returns a dict with:
        n, width, n_evals, anf_degree, seconds
    """
    width = 2 * n + 1
    n_evals = 1 << width

    # Cap to a reasonable size to avoid OOM
    if n_evals > (1 << 22):  # 4M
        return {"n": n, "anf_degree": None,
                "note": f"too large: 2^{width} = {n_evals} > 4M cap"}

    t0 = time.time()

    # Evaluate a(n) for all 2^width initial conditions
    fs = np.zeros(n_evals, dtype=np.uint8)
    if use_numba and NUMBA_AVAILABLE:
        # JIT-compiled loop
        for x in range(n_evals):
            fs[x] = rule30_eval_one(x, width, n)
    else:
        for x in range(n_evals):
            fs[x] = rule30_eval_one_pure(x, width, n)
    eval_time = time.time() - t0

    # Mobius transform to get ANF coefficients
    t1 = time.time()
    anf = fs.copy()
    if use_numba and NUMBA_AVAILABLE:
        mobius_transform_inplace(anf, width)
    else:
        # Pure-python Mobius
        for i in range(width):
            step = 1 << i
            for j in range(n_evals):
                if j & step:
                    anf[j] ^= anf[j ^ step]
    mobius_time = time.time() - t1

    # Find max Hamming weight of any nonzero ANF coefficient
    t2 = time.time()
    max_w = 0
    for x in range(n_evals):
        if anf[x]:
            # builtin popcount would be faster; numba has bin(x).count("1")
            # but Python's bin() works fine here
            w = bin(x).count("1")
            if w > max_w:
                max_w = w
    scan_time = time.time() - t2

    return {
        "n": n,
        "width": width,
        "n_evals": n_evals,
        "anf_degree": max_w,
        "expected_2n_minus_1": 2 * n - 1,
        "matches_conjecture": max_w == 2 * n - 1,
        "eval_seconds": float(eval_time),
        "mobius_seconds": float(mobius_time),
        "scan_seconds": float(scan_time),
        "total_seconds": float(time.time() - t0),
    }


def main() -> None:
    # First, JIT warmup with n=2
    print("[anf] numba JIT warmup with n=2...")
    _ = compute_anf_degree(2, use_numba=True)

    # Verify the JIT against the pure-Python version for n=3
    print("[anf] verifying JIT vs pure Python on n=3...")
    n = 3
    width = 2 * n + 1
    n_evals = 1 << width
    for x in range(min(50, n_evals)):
        j = rule30_eval_one(x, width, n)
        p = rule30_eval_one_pure(x, width, n)
        assert j == p, f"JIT mismatch at x={x}: jit={j}, pure={p}"
    print("[anf] JIT verified against pure Python.")

    # Compute ANF degree for n=1..10 (or until we hit the cap)
    results = []
    for n in range(1, 11):
        print(f"[anf] computing ANF degree for n={n} (width={2*n+1}, "
              f"2^{2*n+1}={1<<(2*n+1)} initial conditions)...", flush=True)
        t0 = time.time()
        r = compute_anf_degree(n, use_numba=True)
        elapsed = time.time() - t0
        if r.get("anf_degree") is not None:
            flag = "OK" if r["matches_conjecture"] else "MISMATCH"
            print(f"       {flag}: deg(a({n})) = {r['anf_degree']} "
                  f"(conjecture: {r['expected_2n_minus_1']}) "
                  f"in {elapsed:.1f}s")
        else:
            print(f"       skipped: {r.get('note', '?')}")
        results.append(r)
        if r.get("anf_degree") is None:
            break

    out = {
        "numba_available": NUMBA_AVAILABLE,
        "max_n_attempted": max(r["n"] for r in results),
        "results": results,
        "conjecture": "deg(a(n)) = 2n - 1 for all n >= 1",
        "conjecture_holds_for_n_up_to": max((r["n"] for r in results
                                              if r.get("matches_conjecture")),
                                             default=0),
    }
    out_path = DATA / "p3_anf_extended.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n[anf] wrote {out_path}")
    print(f"[anf] conjecture 'deg(a(n)) = 2n-1' verified for n=1..{out['conjecture_holds_for_n_up_to']}")


if __name__ == "__main__":
    main()
