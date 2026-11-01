"""Round 14: the bit sequences compared in the shortcut-network and jump-rule studies.

Rule 30 centre column (from r14_centre.c) and controls with known status:
  * prng      - numpy PCG64 pseudo-random bits (a no-pattern reference)
  * sqrt2     - binary digits of sqrt(2) (believed normal; not proved)
  * lfsr31    - m-sequence of x^31 + x^28 + 1: statistically flat, but it HAS an exact jump rule
                s(t) = s(t-31) xor s(t-28) (a hidden 'shortcut path')
  * thue      - Thue-Morse word (aperiodic, structured)
  * fib       - Fibonacci (Sturmian) word (aperiodic, structured)
  * period7   - 1101000 repeated (periodic)
"""
import math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

def rule30(n):
    for name in ("centre4M.bin", "centre.bin"):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            c = np.fromfile(p, dtype=np.uint8)
            if len(c) >= n:
                return c[:n].copy()
    raise FileNotFoundError("run ./r14_centre N centre.bin first")

def prng(n, seed=2026):
    return np.random.default_rng(seed).integers(0, 2, n, dtype=np.uint8)

def sqrt2(n):
    r = math.isqrt(2 << (2 * n))          # floor(sqrt(2) * 2^n)
    s = bin(r)[2:]                          # leading '1' is the integer part
    return np.frombuffer(s[1:n + 1].encode(), dtype=np.uint8) - ord("0")

def lfsr31(n, skip=10000):
    n += skip
    s = np.zeros(n + 31, dtype=np.uint8); s[:31] = 1
    t = 31
    while t < n + 31:
        k = min(28, n + 31 - t)
        s[t:t + k] = s[t - 31:t - 31 + k] ^ s[t - 28:t - 28 + k]
        t += k
    return s[31 + skip:]

def thue(n):
    i = np.arange(n, dtype=np.int64)
    c = np.zeros(n, dtype=np.uint8)
    while i.any():
        c ^= (i & 1).astype(np.uint8); i >>= 1
    return c

def fib(n):
    phi = (1 + 5 ** 0.5) / 2
    k = np.arange(1, n + 1, dtype=np.float64)
    return (np.floor((k + 1) / phi) - np.floor(k / phi)).astype(np.uint8)

def period7(n):
    return np.resize(np.array([1, 1, 0, 1, 0, 0, 0], dtype=np.uint8), n)

ALL = {"rule30": rule30, "prng": prng, "sqrt2": sqrt2, "lfsr31": lfsr31,
       "thue": thue, "fib": fib, "period7": period7}
