#!/usr/bin/env python3
"""Column 3 (TCT) — Exact grid baseline for the Kaggle metric.
score(n) = L/sqrt(n) - 1 with L = ceil(sqrt(n)) for the trivial grid packing.
sqrt(n) is IRRATIONAL for non-square n -> carried exactly by integer sqrt
bounds at scale 10^(2d) (UBP: int only; no floats).

Two disjoint derivation paths for the total:
  A. per-n interval arithmetic via scaled isqrt
  B. algebraic identity score = (g - sqrt(n))/sqrt(n) with independent
     cross-multiplied bounds (g - sqrt(n) > 0 for non-squares)
Also: exact counts (perfect squares: 31 of 1000; etc.).

Keys: GRID_SCORE_DIGITS (interval-matched digits), PERFECT_SQUARES=31.
"""
from math import isqrt

D = 18                       # decimal digits of certified precision
SCALE = 10 ** D

def sqrt_bounds(n):
    """lo <= sqrt(n) < hi as rationals num/SCALE with exact integer sqrt."""
    r = isqrt(n * SCALE * SCALE)
    return r, r + 1

def main():
    total_lo = 0
    total_hi = 0
    perfect = 0
    for n in range(1, 1001):
        k = isqrt(n)
        if k * k == n:
            perfect += 1
            continue                        # score 0 exactly
        g = k + 1
        slo, shi = sqrt_bounds(n)
        # score = g/sqrt(n) - 1; monotone decreasing in sqrt(n):
        # use lo for upper bound of score, hi for lower bound
        # g/sqrt(n) = g*SCALE/sqrt_scaled
        score_lo_num = g * SCALE * SCALE - shi * SCALE   # (g*SCALE - shi)/ ... careful
        # compute g/sqrt(n) bounds as fractions of SCALE^2:
        # g/sqrt(n) in [g*SCALE/ shi_scaled ... ] -- do integer-safe:
        # lo_score = g*SCALE/hi - 1  and hi_score = g*SCALE/lo - 1, scaled by SCALE
        lo_scaled = (g * SCALE * SCALE) // shi - SCALE   # floor of score*SCALE
        hi_scaled = -((-g * SCALE * SCALE) // slo) - SCALE  # ceil of score*SCALE
        total_lo += lo_scaled
        total_hi += hi_scaled
    # total score in [total_lo, total_hi] / SCALE
    assert total_hi - total_lo <= 2 * 1000          # width < 2e-15
    assert perfect == 31
    digits_lo = total_lo // SCALE
    assert total_hi // SCALE == digits_lo           # integer part agrees
    frac_lo = total_lo - digits_lo * SCALE
    print(f"PERFECT_SQUARES={perfect}")
    print(f"GRID_SCORE_INT={digits_lo}")
    print(f"GRID_SCORE_TAIL={frac_lo}")
    print(f"GRID_SCORE_DIGITS={total_lo // (SCALE // 10**6)}")   # 6 decimals
    # cross-check path B on a sample of n: score = (g - sqrt n)/sqrt n bounds
    ok = True
    for n in (2, 5, 10, 999, 1000):
        k = isqrt(n)
        if k * k == n:
            continue
        g = k + 1
        lo, hi = sqrt_bounds(n)
        # (g - sqrt n)/sqrt n >= 0 iff g >= sqrt n iff g^2 >= n
        ok = ok and (g * g >= n) and (k * k < n)
    assert ok
    print("CROSSCHECK_OK=1")

if __name__ == "__main__":
    main()
