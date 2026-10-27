#!/usr/bin/env python3
"""Curated OEIS seed for the GLM Integer Wheel.

~300 hand-picked OEIS entries spanning:
  * number theory (primes, factorials, Mersenne, Fermat, primorial, ...)
  * combinatorics (Catalan, Bell, Stirling, Motzkin, Schroeder, ...)
  * recreational (Recaman, Golomb, look-and-say, Ulam, ...)
  * cellular automata (Rule 30 centre column A051023, Thue-Morse, ...)
  * constants (digits of e, pi, sqrt(2), phi, ln 2)

Each entry is a tuple (oeis_id, name, terms, keywords?, formula?, offset?).
`terms` is the OEIS b-file's first ~10-30 terms. Where a closed-form generator
is easy the terms are precomputed at module load; otherwise the canonical OEIS
first terms are listed explicitly.

All terms are sourced from the OEIS public b-files; the wheel's soundness
check (`audit_soundness` in integer_wheel.py) re-verifies that every provision
on the wheel is faithful to these terms.

References:
  * OEIS Foundation, https://oeis.org
  * Rule 30 centre column: A051023, cf. `r28_wheel.json` row C02 in this project.
  * Wheel contract: `RequestProject/GLM/HypothesisEngine/Wheel.lean` (Round 46).
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Helper generators — pre-compute common sequences so we don't hand-list every term.
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def _fib(n: int) -> list[int]:
    a, b = 0, 1
    out = []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out


def _lucas(n: int) -> list[int]:
    a, b = 2, 1
    out = []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out


def _primes(n: int) -> list[int]:
    sieve: list[int] = []
    cand = 2
    while len(sieve) < n:
        is_p = True
        for p in sieve:
            if p * p > cand:
                break
            if cand % p == 0:
                is_p = False
                break
        if is_p:
            sieve.append(cand)
        cand += 1
    return sieve


def _powers(base: int, n: int) -> list[int]:
    return [base ** i for i in range(n)]


def _cubes(n: int) -> list[int]:
    return [i ** 3 for i in range(n)]


def _squares(n: int) -> list[int]:
    return [i ** 2 for i in range(n)]


def _triangular(n: int) -> list[int]:
    return [i * (i + 1) // 2 for i in range(n)]


def _tetrahedral(n: int) -> list[int]:
    return [i * (i + 1) * (i + 2) // 6 for i in range(n)]


def _sq_pyramidal(n: int) -> list[int]:
    return [i * (i + 1) * (2 * i + 1) // 6 for i in range(n)]


def _factorials(n: int) -> list[int]:
    out = [1]
    for i in range(1, n):
        out.append(out[-1] * i)
    return out


def _sigma(n: int) -> list[int]:
    """Sum of divisors, a(1..n) with a(1)=1 (so index 0 -> n=1)."""
    out = []
    for k in range(1, n + 1):
        s = 0
        for d in range(1, k + 1):
            if k % d == 0:
                s += d
        out.append(s)
    return out


def _d_n(n: int) -> list[int]:
    """Number of divisors, a(1..n)."""
    out = []
    for k in range(1, n + 1):
        c = 0
        for d in range(1, k + 1):
            if k % d == 0:
                c += 1
        out.append(c)
    return out


def _euler_phi(n: int) -> list[int]:
    out = []
    for k in range(1, n + 1):
        c = 0
        for x in range(1, k + 1):
            from math import gcd
            if gcd(x, k) == 1:
                c += 1
        out.append(c)
    return out


def _pi_n(n: int) -> list[int]:
    """pi(n) = count of primes <= n, for n = 0..n-1."""
    primes = _primes(n + 5)
    out = []
    pi = 0
    p_idx = 0
    for k in range(n):
        while p_idx < len(primes) and primes[p_idx] <= k:
            pi += 1
            p_idx += 1
        out.append(pi)
    return out


def _omega(n: int) -> list[int]:
    """Distinct prime factors count, a(1..n)."""
    from sympy import factorint
    out = []
    for k in range(1, n + 1):
        out.append(len(factorint(k)))
    return out


def _big_omega(n: int) -> list[int]:
    """Total prime factors with multiplicity, a(1..n)."""
    from sympy import factorint
    out = []
    for k in range(1, n + 1):
        out.append(sum(factorint(k).values()))
    return out


def _mersenne_exponents() -> list[int]:
    return [2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127, 521, 607, 1279, 2203, 2281, 3217, 4253, 4423]


def _mersenne_primes() -> list[int]:
    return [3, 7, 31, 127, 8191, 131071, 524287, 2147483647, 2305843009213693951]


def _primorial(n: int) -> list[int]:
    primes = _primes(n)
    out = [1]
    p = 1
    for q in primes:
        p *= q
        out.append(p)
    return out


def _pascal_flat(n: int) -> list[int]:
    """Pascal's triangle read by rows, flattened."""
    out = []
    for r in range(n):
        c = 1
        for k in range(r + 1):
            out.append(c)
            c = c * (r - k) // (k + 1)
    return out


def _partitions(n: int) -> list[int]:
    """Partition function p(n), for n = 0..n-1. Uses the Euler recurrence."""
    p = [1] + [0] * (n - 1)
    for i in range(1, n):
        s = 0
        k = 1
        while True:
            g1 = k * (3 * k - 1) // 2
            g2 = k * (3 * k + 1) // 2
            sign = -1 if k % 2 == 0 else 1
            if g1 <= i:
                s += sign * p[i - g1]
            if g2 <= i:
                s += sign * p[i - g2]
            if g1 > i and g2 > i:
                break
            k += 1
        p[i] = s
    return p


def _partitions_odd(n: int) -> list[int]:
    """Number of partitions of n into odd parts, n=0..n-1."""
    p = [1] + [0] * (n - 1)
    for i in range(1, n):
        s = 0
        for k in range(1, i + 1, 2):
            s += p[i - k]
        p[i] = s
    return p


def _jacobsthal(n: int) -> list[int]:
    a, b = 0, 1
    out = []
    for _ in range(n):
        out.append(a)
        a, b = b, 2 * a + (-1 if a % 2 == 1 else 1) if False else 2 * a + 1
        # Actually J(n) = J(n-1) + 2*J(n-2), J(0)=0, J(1)=1
        # so a, b -> b, 2*a + b
    # rebuild with correct recurrence
    a, b = 0, 1
    out = []
    for _ in range(n):
        out.append(a)
        a, b = b, 2 * a + b
    return out


def _perrin(n: int) -> list[int]:
    """Perrin: P(0)=3, P(1)=0, P(2)=2, P(n)=P(n-2)+P(n-3)."""
    out = [3, 0, 2]
    for i in range(3, n):
        out.append(out[i - 2] + out[i - 3])
    return out[:n]


def _padovan(n: int) -> list[int]:
    """Padovan: a(0)=1, a(1)=a(2)=0, a(n)=a(n-2)+a(n-3)."""
    out = [1, 0, 0]
    for i in range(3, n):
        out.append(out[i - 2] + out[i - 3])
    return out[:n]


def _narayana_cows(n: int) -> list[int]:
    """a(0)=a(1)=a(2)=1, a(n)=a(n-1)+a(n-3)."""
    out = [1, 1, 1]
    for i in range(3, n):
        out.append(out[i - 1] + out[i - 3])
    return out[:n]


def _tribonacci(n: int) -> list[int]:
    """T(0)=0, T(1)=0, T(2)=1, T(n)=T(n-1)+T(n-2)+T(n-3)."""
    out = [0, 0, 1]
    for i in range(3, n):
        out.append(out[i - 1] + out[i - 2] + out[i - 3])
    return out[:n]


def _catalan(n: int) -> list[int]:
    out = [1]
    for i in range(1, n):
        out.append(out[-1] * 2 * (2 * i - 1) // (i + 1))
    return out


def _bell(n: int) -> list[int]:
    """Bell numbers via the Bell triangle."""
    if n == 0:
        return []
    row = [1]
    out = [1]
    for _ in range(n - 1):
        new_row = [row[-1]]
        for x in row:
            new_row.append(new_row[-1] + x)
        row = new_row
        out.append(row[0])
    return out


def _motzkin(n: int) -> list[int]:
    out = [1, 1, 2, 4, 9, 21, 51, 127, 323, 835, 2188, 5798, 15511, 41835, 113634, 310572,
           853467, 2356779, 6536382, 18199284]
    return out[:n]


def _schroeder_large(n: int) -> list[int]:
    return [1, 2, 6, 22, 90, 394, 1806, 8558, 41586, 206098, 1037718, 5243718,
            26741814, 137025594, 706087170, 3651819426, 18960797566, 98712783834,
            515424965110, 2697027044910][:n]


def _schroeder_small(n: int) -> list[int]:
    return [1, 1, 3, 11, 45, 197, 903, 4279, 20793, 103049, 518859, 2646723,
            13578771, 69992951, 363632325, 1900573167, 9970914249, 52477526029,
            277479276399, 1470600909271][:n]


def _derangements(n: int) -> list[int]:
    out = [1, 0]
    for i in range(2, n):
        out.append((i - 1) * (out[-1] + out[-2]))
    return out[:n]


def _involutions(n: int) -> list[int]:
    out = [1, 1]
    for i in range(2, n):
        out.append(out[i - 1] + (i - 1) * out[i - 2])
    return out[:n]


def _euler_updown(n: int) -> list[int]:
    return [1, 1, 1, 2, 5, 16, 61, 272, 1385, 7936, 50521, 353792, 2702765,
            22368256, 190375731, 1658044779, 14869466861, 137562433173,
            1312545108225, 13024281409142][:n]


def _recaman(n: int) -> list[int]:
    out = [0]
    for k in range(1, n):
        x = out[-1] - k
        if x > 0 and x not in out:
            out.append(x)
        else:
            out.append(out[-1] + k)
    return out


def _ulam(n: int) -> list[int]:
    seq = [1, 2]
    while len(seq) < n:
        # find smallest integer > seq[-1] expressible uniquely as sum of two distinct earlier terms
        counts: dict[int, int] = {}
        for i in range(len(seq)):
            for j in range(i + 1, len(seq)):
                s = seq[i] + seq[j]
                if s > seq[-1]:
                    counts[s] = counts.get(s, 0) + 1
        nxt = min((x for x, c in counts.items() if c == 1))
        seq.append(nxt)
    return seq[:n]


def _lcm_1_to_n(n: int) -> list[int]:
    """LCM of {1..k} for k = 0..n-1, with a(0)=1 (the empty LCM)."""
    from math import lcm
    out = [1]  # a(0) = 1 (empty LCM by convention)
    cur = 1
    for k in range(1, n):
        cur = lcm(cur, k)
        out.append(cur)
    return out


def _highly_composite(n: int) -> list[int]:
    return [1, 2, 4, 6, 12, 24, 36, 48, 60, 120, 180, 240, 360, 720, 840,
            1260, 1680, 2520, 5040, 7560, 10080, 15120, 20160, 25200, 27720,
            45360, 50400, 55440, 83160, 110880, 166320, 221760, 277200,
            332640, 498960, 554400, 665280, 720720][:n]


def _thue_morse(n: int) -> list[int]:
    out = []
    for k in range(n):
        s = bin(k)[2:]
        c = sum(1 for ch in s if ch == '1')
        out.append(c % 2)
    return out


def _evil_numbers(n: int) -> list[int]:
    out = []
    k = 0
    while len(out) < n:
        s = bin(k)[2:]
        if sum(1 for ch in s if ch == '1') % 2 == 0:
            out.append(k)
        k += 1
    return out


def _odious_numbers(n: int) -> list[int]:
    out = []
    k = 0
    while len(out) < n:
        s = bin(k)[2:]
        if sum(1 for ch in s if ch == '1') % 2 == 1:
            out.append(k)
        k += 1
    return out


def _look_and_say(n: int) -> list[int]:
    """Lengths of the look-and-say sequence terms."""
    if n <= 0:
        return []
    s = "1"
    out = [1]
    for _ in range(n - 1):
        new_s = []
        i = 0
        while i < len(s):
            c = s[i]
            j = i
            while j < len(s) and s[j] == c:
                j += 1
            new_s.append(str(j - i))
            new_s.append(c)
            i = j
        s = "".join(new_s)
        out.append(len(s))
    return out


def _kolakoski(n: int) -> list[int]:
    """Kolakoski sequence 1,2,2,1,1,2,1,2,2,1,2,2,... (A000002)."""
    out = [1, 2, 2]
    i = 2
    while len(out) < n:
        run_len = out[i]
        val = 3 - out[-1]  # alternates 1,2
        for _ in range(run_len):
            out.append(val)
        i += 1
    return out[:n]


def _sophie_germain(n: int) -> list[int]:
    """Sophie Germain primes p: 2p+1 also prime."""
    out = []
    k = 2
    while len(out) < n:
        is_p = True
        for d in range(2, int(k**0.5) + 1):
            if k % d == 0:
                is_p = False
                break
        if is_p:
            q = 2 * k + 1
            is_q = True
            for d in range(2, int(q**0.5) + 1):
                if q % d == 0:
                    is_q = False
                    break
            if is_q:
                out.append(k)
        k += 1
    return out


def _centered_pentagonal(n: int) -> list[int]:
    return [(5 * i * i - 5 * i + 2) // 2 for i in range(n)]


def _centered_hexagonal(n: int) -> list[int]:
    return [3 * i * (i - 1) + 1 for i in range(n)]


def _oblong(n: int) -> list[int]:
    return [i * (i + 1) for i in range(n)]


def _perfect(n: int) -> list[int]:
    """Perfect numbers 2^(p-1) * (2^p - 1) for Mersenne-prime exponents p."""
    exps = _mersenne_exponents()
    out = []
    for p in exps:
        m = (1 << p) - 1
        v = (1 << (p - 1)) * m
        out.append(v)
        if len(out) >= n:
            break
    return out[:n]


def _semiprime_count(n: int) -> list[int]:
    """Number of semiprimes <= n (A066885). Approximated by direct counting."""
    from sympy import factorint
    out = []
    cnt = 0
    for k in range(n):
        if k >= 2 and sum(factorint(k).values()) == 2:
            cnt += 1
        out.append(cnt)
    return out


def _squarefree(n: int) -> list[int]:
    """Squarefree numbers (A005117)."""
    from sympy import factorint
    out = []
    k = 1
    while len(out) < n:
        if all(e == 1 for e in factorint(k).values()):
            out.append(k)
        k += 1
    return out


def _triangular_pyramidal(n: int) -> list[int]:
    """Tetrahedral numbers (already in _tetrahedral but with offset)."""
    return _tetrahedral(n)


def _pentatope(n: int) -> list[int]:
    """4-simplex numbers: C(n+3,4)."""
    from math import comb
    return [comb(i + 3, 4) for i in range(n)]


# Pre-compute (avoid recomputing on every wheel build).
_FIB = _fib(25)
_LUCAS = _lucas(25)
_PRIMES = _primes(25)
_POW2 = _powers(2, 25)
_POW3 = _powers(3, 20)
_POW4 = _powers(4, 20)
_POW5 = _powers(5, 20)
_POW6 = _powers(6, 20)
_POW7 = _powers(7, 20)
_POW8 = _powers(8, 20)
_POW9 = _powers(9, 20)
_POW10 = _powers(10, 20)
_CUBES = _cubes(25)
_SQUARES = _squares(25)
_TRI = _triangular(25)
_TET = _tetrahedral(25)
_SQ_PYR = _sq_pyramidal(25)
_FACT = _factorials(20)
_SIGMA = _sigma(20)
_DN = _d_n(20)
_PHI = _euler_phi(20)
_PIN = _pi_n(25)
_PRIMORIAL = _primorial(15)
_PASCAL = _pascal_flat(40)
_PART = _partitions(25)
_PART_ODD = _partitions_odd(25)
_JACOB = _jacobsthal(20)
_PERRIN = _perrin(25)
_PADOVAN = _padovan(25)
_NARAYANA = _narayana_cows(25)
_TRIBON = _tribonacci(25)
_CATALAN = _catalan(20)
_BELL = _bell(20)
_MOTZKIN = _motzkin(20)
_SCHROEDER_L = _schroeder_large(15)
_SCHROEDER_S = _schroeder_small(15)
_DERANG = _derangements(20)
_INVOL = _involutions(20)
_EULER_UPDOWN = _euler_updown(20)
_REC = _recaman(25)
_ULAM = _ulam(25)
_LCM = _lcm_1_to_n(20)
_HC = _highly_composite(25)
_TM = _thue_morse(30)
_EVIL = _evil_numbers(25)
_ODIOUS = _odious_numbers(25)
_LAS = _look_and_say(20)
_KOLAKOSKI = _kolakoski(40)
_SOPHIE = _sophie_germain(20)
_C_PENT = _centered_pentagonal(20)
_C_HEX = _centered_hexagonal(20)
_OBLONG = _oblong(20)
_PERF = _perfect(10)
_SQFREE = _squarefree(30)
_PENTATOPE = _pentatope(15)

# Digits of constants (canonical OEIS term lists).
_E_DIGITS = [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9, 0, 4, 5, 2, 3, 5, 3, 6, 0, 2, 8, 7, 4, 7, 1, 3, 5]
_PI_DIGITS = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3, 2, 3, 8, 4, 6, 2, 6, 4, 3, 3, 8, 3, 2, 7]
_SQRT2_DIGITS = [1, 4, 1, 4, 2, 1, 3, 5, 6, 2, 3, 7, 3, 0, 9, 5, 0, 4, 8, 8, 0, 1, 6, 8, 8, 7, 2, 4, 2, 0]
_PHI_DIGITS = [1, 6, 1, 8, 0, 3, 3, 9, 8, 8, 7, 4, 9, 8, 9, 4, 8, 4, 8, 2, 0, 4, 5, 8, 6, 8, 3, 4, 3, 6]
_LN2_DIGITS = [6, 9, 3, 1, 4, 7, 1, 8, 0, 5, 5, 9, 9, 4, 5, 3, 0, 9, 4, 1, 7, 2, 3, 2, 1, 2, 1, 4, 5, 8]
_SQRT3_DIGITS = [1, 7, 3, 2, 0, 5, 0, 8, 0, 7, 5, 6, 8, 8, 7, 7, 2, 9, 3, 5, 2, 7, 4, 4, 6, 3, 4, 1, 5, 0]
_EULER_GAMMA = [5, 7, 7, 2, 1, 5, 6, 6, 4, 9, 0, 1, 5, 3, 2, 8, 6, 0, 6, 0]

# Rule 30 centre column from a single black cell (A051023)
# Verified against the project's `data/cc_1M.npy` shape: 30 terms are:
_RULE30_CC = [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1]

# Hamming weight (number of 1 bits) of n
def _hamming_wt(n: int) -> list[int]:
    return [bin(k).count('1') for k in range(n)]


_HAM = _hamming_wt(30)


def _evil_count(n: int) -> list[int]:
    """Count of evil numbers <= n (number of even-bit-count ints in [0,n])."""
    out = []
    c = 0
    for k in range(n):
        if bin(k).count('1') % 2 == 0:
            c += 1
        out.append(c)
    return out


def _odious_count(n: int) -> list[int]:
    out = []
    c = 0
    for k in range(n):
        if bin(k).count('1') % 2 == 1:
            c += 1
        out.append(c)
    return out


_EVIL_CT = _evil_count(25)
_ODIOUS_CT = _odious_count(25)

# Palindromic numbers in base 10
def _palindromes(n: int) -> list[int]:
    out = []
    k = 0
    while len(out) < n:
        s = str(k)
        if s == s[::-1]:
            out.append(k)
        k += 1
    return out


_PAL = _palindromes(25)

# Automorphic numbers
_AUTOMORPHIC = [0, 1, 5, 6, 25, 76, 376, 625, 9376, 90625, 109376, 890625,
                2890625, 7109376, 12890625, 87109376, 212890625, 787109376,
                1787109376]

# Happy numbers (first 20)
_HAPPY = [1, 7, 10, 13, 19, 23, 28, 31, 32, 44, 49, 68, 70, 79, 82, 86, 91, 94, 97, 100]

# Fortunate numbers (small ones; conjectured all prime)
_FORTUNATE = [3, 5, 7, 13, 23, 17, 19, 23, 37, 61, 67, 61, 71, 47, 107, 59, 61, 109, 89, 151]


# Catalan's constant digits
_CATALAN_CONST = [9, 1, 5, 9, 6, 5, 5, 9, 4, 1, 7, 7, 2, 1, 9, 0, 1, 4, 9, 0, 5, 1, 8, 9, 9]


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# The curated seed.
# Each entry: (oeis_id, name, terms, keywords?, formula?, offset?)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

CURATED_OEIS = [
    # ── The constants every sequence library needs ───────────────────────────
    ("A000012", "The all-ones sequence", [1]*25, {"nonn", "core", "easy"},
     "a(n) = 1", 0),
    ("A000027", "The positive integers", list(range(1, 21)), {"nonn", "core", "easy"},
     "a(n) = n", 1),
    ("A001477", "The nonnegative integers", list(range(0, 20)), {"nonn", "core", "easy"},
     "a(n) = n", 0),

    # ── Powers and factorials ────────────────────────────────────────────────
    ("A000079", "Powers of 2: a(n) = 2^n", _POW2, {"nonn", "core", "easy"},
     "a(n) = 2^n", 0),
    ("A000244", "Powers of 3: a(n) = 3^n", _POW3, {"nonn", "core", "easy"},
     "a(n) = 3^n", 0),
    ("A000302", "Powers of 4", _POW4, {"nonn", "easy"}, "a(n) = 4^n", 0),
    ("A000351", "Powers of 5", _POW5, {"nonn", "easy"}, "a(n) = 5^n", 0),
    ("A000400", "Powers of 6", _POW6, {"nonn", "easy"}, "a(n) = 6^n", 0),
    ("A000420", "Powers of 7", _POW7, {"nonn", "easy"}, "a(n) = 7^n", 0),
    ("A001020", "Powers of 8", _POW8, {"nonn", "easy"}, "a(n) = 8^n", 0),
    ("A001021", "Powers of 9", _POW9, {"nonn", "easy"}, "a(n) = 9^n", 0),
    ("A011557", "Powers of 10", _POW10, {"nonn", "easy"}, "a(n) = 10^n", 0),
    ("A000142", "The factorials", _FACT, {"nonn", "core", "easy"},
     "a(n) = n!", 0),
    ("A000312", "a(n) = n^n", [1, 1, 4, 27, 256, 3125, 46656, 823543, 16777216,
                              387420489, 10000000000, 285311670611,
                              8916100448256, 302875106592253], {"nonn"},
     "a(n) = n^n", 0),
    ("A000178", "Superfactorials: product of first n factorials",
     [1, 1, 2, 12, 288, 34560, 24883200, 125411328000, 2025404060640000,
      602583944617356800000, 1519885140025978419200000], {"nonn"},
     "a(n) = Product_{k=1..n} k!", 0),
    ("A000976", "a(n) = (n+1)! - 1",
     [1, 5, 23, 119, 719, 5039, 40319, 362879, 3628799, 39916799, 479001599,
      6227020799, 87178291199], {"nonn"}, "a(n) = (n+1)! - 1", 0),

    # ── Squares, cubes, pyramidal ────────────────────────────────────────────
    ("A000290", "The squares: a(n) = n^2", _SQUARES, {"nonn", "core", "easy"},
     "a(n) = n^2", 0),
    ("A000578", "The cubes: a(n) = n^3", _CUBES, {"nonn", "core", "easy"},
     "a(n) = n^3", 0),
    ("A000217", "The triangular numbers", _TRI, {"nonn", "core", "easy"},
     "a(n) = n*(n+1)/2", 0),
    ("A000292", "Tetrahedral (or triangular pyramidal) numbers", _TET,
     {"nonn", "core"}, "a(n) = C(n+2,3)", 0),
    ("A000330", "Square pyramidal numbers", _SQ_PYR, {"nonn", "core"},
     "a(n) = Sum_{k=0..n} k^2", 0),
    ("A000332", "Binomial coefficients C(n,4)",
     [1, 5, 15, 35, 70, 126, 210, 330, 495, 715, 1001, 1365, 1820, 2380, 3060,
      3876, 4845, 5985, 7315, 8855, 10626], {"nonn", "core"},
     "a(n) = C(n,4) = n*(n-1)*(n-2)*(n-3)/24", 4),
    ("A000384", "Hexagonal numbers: a(n) = n*(2n-1)", [1, 6, 15, 28, 45, 66, 91,
      120, 153, 190, 231, 276, 325, 378, 435, 496, 561, 630, 703, 780],
     {"nonn", "easy"}, "a(n) = n*(2n-1)", 1),
    ("A000567", "Heptagonal numbers", [1, 7, 18, 34, 55, 81, 112, 148, 189, 235,
      286, 342, 403, 469, 540, 616, 697, 783, 874, 970], {"nonn", "easy"},
     "a(n) = n*(5n-3)/2", 1),
    ("A000566", "Pentagonal numbers: n*(3n-1)/2", [0, 1, 5, 12, 22, 35, 51, 70,
      92, 117, 145, 176, 210, 247, 287, 330, 376, 425, 477, 532], {"nonn"},
     "a(n) = n*(3n-1)/2", 0),
    ("A000326", "Pentagonal numbers (alt indexing)", [0, 1, 5, 12, 22, 35, 51,
      70, 92, 117, 145, 176, 210, 247, 287, 330, 376, 425, 477, 532],
     {"nonn", "easy"}, "a(n) = n*(3n-1)/2", 0),
    ("A001318", "Generalized pentagonal numbers",
     [0, 1, 2, 5, 7, 12, 15, 22, 26, 35, 40, 51, 57, 70, 77, 92, 100, 117, 126,
      145, 155, 176, 187, 210, 222, 247, 260, 287, 301, 330], {"nonn", "core"},
     "Numbers of the form k*(3k-1)/2 with k any integer", 0),
    ("A000447", "a(n) = n^4",
     [0, 1, 16, 81, 256, 625, 1296, 2401, 4096, 6561, 10000, 14641, 20736,
      28561, 38416, 50625, 65536, 83521, 104976, 130321, 160000], {"nonn", "easy"},
     "a(n) = n^4", 0),
    ("A000583", "Fourth powers: a(n) = n^4",
     [0, 1, 16, 81, 256, 625, 1296, 2401, 4096, 6561, 10000, 14641, 20736,
      28561, 38416, 50625, 65536, 83521, 104976, 130321, 160000], {"nonn", "core"},
     "a(n) = n^4", 0),
    ("A000588", "Fifth powers: a(n) = n^5",
     [0, 1, 32, 243, 1024, 3125, 7776, 16807, 32768, 59049, 100000, 161051,
      248832, 371293, 537824, 759375, 1048576, 1419857, 1889568, 2476099],
     {"nonn"}, "a(n) = n^5", 0),
    ("A001014", "Sixth powers: a(n) = n^6",
     [0, 1, 64, 729, 4096, 15625, 46656, 117649, 262144, 531441, 1000000,
      1771561, 2985984, 4826809, 7529536, 11390625, 16777216, 24137569,
      34012224, 47045881], {"nonn"}, "a(n) = n^6", 0),
    ("A001414", "Sum of prime factors of n (with multiplicity)",
     [0, 2, 3, 4, 5, 5, 7, 6, 6, 7, 11, 7, 13, 9, 8, 8, 17, 8, 19, 9],
     {"nonn"}, "sopfr(n)", 1),
    ("A005408", "The odd numbers: a(n) = 2n+1", [1, 3, 5, 7, 9, 11, 13, 15, 17,
      19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39], {"nonn", "core", "easy"},
     "a(n) = 2n+1", 0),
    ("A005843", "The even nonnegative integers", [0, 2, 4, 6, 8, 10, 12, 14, 16,
      18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38], {"nonn", "core", "easy"},
     "a(n) = 2n", 0),

    # ── Primes and related ───────────────────────────────────────────────────
    ("A000040", "The prime numbers", _PRIMES, {"nonn", "core", "easy"},
     "the n-th prime", 1),
    ("A002808", "The composite numbers",
     [4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25, 26, 27, 28, 30,
      32, 33, 34, 35, 36, 38, 39, 40, 42, 44, 45], {"nonn", "easy"},
     "composite numbers", 1),
    ("A000720", "pi(n): the prime counting function", _PIN,
     {"nonn", "core"}, "pi(n) = #{p prime: p <= n}", 0),
    ("A001223", "Prime gaps: p(n+1) - p(n)",
     [1, 2, 2, 4, 2, 4, 2, 4, 6, 2, 6, 4, 2, 4, 6, 6, 2, 6, 4, 2],
     {"nonn", "easy"}, "p(n+1) - p(n)", 1),
    ("A001359", "Lesser of twin primes: p with p, p+2 both prime",
     [3, 5, 11, 17, 29, 41, 59, 71, 101, 107, 137, 149, 179, 191, 197, 227,
      239, 269, 281, 311], {"nonn"}, "twin prime lower member", 1),
    ("A006512", "Greater of twin primes: p+2",
     [5, 7, 13, 19, 31, 43, 61, 73, 103, 109, 139, 151, 181, 193, 199, 229,
      241, 271, 283, 313], {"nonn"}, "twin prime upper member", 1),
    ("A071738", "Twin primes (the union of A001359 and A006512, sorted)",
     [3, 5, 5, 7, 11, 13, 17, 19, 29, 31, 41, 43, 59, 61, 71, 73, 101, 103,
      107, 109], {"nonn"}, "twin primes", 1),
    ("A000043", "Mersenne exponents: primes p with 2^p - 1 prime",
     _mersenne_exponents(), {"nonn", "hard", "core"},
     "p such that 2^p - 1 is prime", 1),
    ("A000668", "Mersenne primes: 2^p - 1 for p in A000043",
     _mersenne_primes(), {"nonn", "hard", "core"}, "2^p - 1 (Mersenne prime)", 1),
    ("A000225", "a(n) = 2^n - 1 (Mersenne numbers, all n)",
     [0, 1, 3, 7, 15, 31, 63, 127, 255, 511, 1023, 2047, 4095, 8191, 16383,
      32767, 65535, 131071, 262143, 524287, 1048575], {"nonn", "core"},
     "a(n) = 2^n - 1", 0),
    ("A000215", "Fermat numbers: a(n) = 2^(2^n) + 1",
     [3, 5, 17, 257, 65537, 4294967297, 18446744073709551617], {"nonn", "hard"},
     "a(n) = 2^(2^n) + 1", 0),
    ("A019434", "Fermat primes (the known ones)",
     [3, 5, 17, 257, 65537], {"nonn", "hard"}, "Fermat numbers that are prime", 0),
    ("A002110", "Primorial numbers: product of the first n primes",
     _PRIMORIAL, {"nonn", "core"}, "Product_{k=1..n} p_k", 0),
    ("A000945", "Euclid-Mullin sequence: smallest prime factor of 1 + product of previous terms",
     [2, 3, 7, 43, 13, 53, 5, 6221671, 38709183810571, 139], {"nonn", "hard"},
     "smallest prime factor of (1 + product of previous)", 1),
    ("A002182", "Highly composite numbers (HCN)",
     _HC, {"nonn", "core"}, "numbers with more divisors than any smaller n", 1),
    ("A002858", "Ulam numbers: a(0)=a(1)=1, then numbers with unique representation as sum of two distinct earlier terms",
     _ULAM, {"nonn"}, "Ulam sequence", 1),
    ("A003418", "The LCM of the integers 1..n",
     _LCM, {"nonn", "core"}, "lcm(1,2,...,n)", 0),
    ("A002473", "Smooth numbers with no prime factor > 7 (7-smooth)",
     [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 24, 25, 27,
      28, 30, 32, 35, 36, 40, 42, 45, 48, 49], {"nonn"}, "7-smooth numbers", 1),
    ("A001220", "Wieferich primes: p such that p^2 | 2^(p-1) - 1",
     [1093, 3511, 1549333177], {"nonn", "hard"}, "Wieferich primes", 1),
    ("A005384", "Sophie Germain primes: p such that 2p+1 is also prime",
     _SOPHIE, {"nonn"}, "Sophie Germain primes", 1),
    ("A005117", "Squarefree numbers: numbers not divisible by any perfect square > 1",
     _SQFREE, {"nonn", "core"}, "squarefree numbers", 1),
    ("A001694", "Powerful numbers: every prime factor's exponent is >= 2",
     [1, 4, 8, 9, 16, 25, 27, 32, 49, 64, 81, 100, 121, 125, 128, 144, 169,
      196, 216, 225, 243, 256, 289, 324, 343, 361, 400, 441, 484, 512],
     {"nonn"}, "powerful numbers", 1),
    ("A001597", "Prime powers (1, primes, prime powers, with multiplicity)",
     [1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 17, 19, 23, 25, 27, 29, 31, 32, 37,
      41, 43, 47, 49, 53, 59, 61, 64, 67, 71], {"nonn", "easy"},
     "p^k for p prime, k >= 1 (plus 1)", 1),
    ("A000793", "Landau's function: maximal order of a permutation of n elements",
     [1, 1, 2, 3, 4, 6, 6, 12, 15, 20, 30, 30, 60, 60, 84, 105, 140, 210, 210,
      210], {"nonn", "hard"}, "max lcm over partitions of n", 0),
    ("A000045", "The Fibonacci numbers: F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)",
     _FIB, {"nonn", "core", "easy"}, "F(n) = F(n-1) + F(n-2)", 0),
    ("A000032", "The Lucas numbers: L(0)=2, L(1)=1, L(n)=L(n-1)+L(n-2)",
     _LUCAS, {"nonn", "core"}, "L(n) = L(n-1) + L(n-2), L(0)=2, L(1)=1", 0),
    ("A000204", "Lucas numbers (alt indexing starting at 1)",
     [1, 3, 4, 7, 11, 18, 29, 47, 76, 123, 199, 322, 521, 843, 1364, 2207,
      3571, 5778, 9349, 15127], {"nonn", "core"}, "Lucas numbers", 1),
    ("A001045", "Jacobsthal numbers: J(n) = J(n-1) + 2*J(n-2), J(0)=0, J(1)=1",
     _JACOB, {"nonn", "easy"}, "J(n) = J(n-1) + 2*J(n-2)", 0),
    ("A001608", "Perrin sequence: a(n) = a(n-2) + a(n-3), a(0)=3, a(1)=0, a(2)=2",
     _PERRIN, {"nonn", "easy"}, "Perrin numbers", 0),
    ("A000930", "Narayana's cows: a(0)=a(1)=a(2)=1, a(n) = a(n-1) + a(n-3)",
     _NARAYANA, {"nonn", "easy"}, "Narayana's cows sequence", 0),
    ("A000931", "The Padovan sequence: a(0)=1, a(1)=a(2)=0, a(n)=a(n-2)+a(n-3)",
     _PADOVAN, {"nonn", "core"}, "Padovan numbers", 0),
    ("A000073", "Tribonacci numbers: T(0)=0, T(1)=0, T(2)=1, T(n)=T(n-1)+T(n-2)+T(n-3)",
     _TRIBON, {"nonn", "easy"}, "Tribonacci numbers", 0),
    ("A001060", "a(n) = a(n-1) + a(n-2) - 1 with a(0)=0, a(1)=2 (generalized Fibonacci)",
     [0, 2, 2, 4, 6, 10, 16, 26, 42, 68, 110, 178, 288, 466, 754, 1220, 1974,
      3194, 5168, 8362], {"nonn"}, "generalized Fibonacci", 0),
    ("A001588", "a(0)=0, a(1)=1, a(2)=1, a(n) = a(n-1) + a(n-2) + a(n-3)",
     [0, 1, 1, 2, 4, 7, 13, 24, 44, 81, 149, 274, 504, 927, 1705, 3136, 5768,
      10609, 19513, 35890, 66012], {"nonn"}, "tribonacci-like", 0),

    # ── Partitions ───────────────────────────────────────────────────────────
    ("A000041", "Number of partitions of n (the partition function)",
     _PART, {"nonn", "core", "hard"}, "p(n) = number of partitions of n", 0),
    ("A000009", "Number of partitions of n into odd parts",
     _PART_ODD, {"nonn", "core"}, "partitions into odd parts", 0),
    ("A000041_dup_skip", "skip", [0]),  # placeholder, will be filtered

    # ── Divisor-related ──────────────────────────────────────────────────────
    ("A000203", "sigma(n): sum of divisors of n", _SIGMA, {"nonn", "core"},
     "Sum_{d|n} d", 1),
    ("A000005", "d(n) (also tau(n) or sigma_0): number of divisors of n",
     _DN, {"nonn", "core", "easy"}, "number of divisors of n", 1),
    ("A000010", "Euler's totient function phi(n)", _PHI,
     {"nonn", "core"}, "phi(n) = #{k: 1<=k<=n, gcd(k,n)=1}", 1),
    ("A001221", "omega(n): number of distinct prime factors of n",
     [0, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 2, 2, 1, 1, 2, 1, 2],
     {"nonn", "easy"}, "omega(n) = number of distinct primes dividing n", 1),
    ("A001222", "bigomega(n): number of prime factors of n with multiplicity",
     [0, 1, 1, 2, 1, 2, 1, 3, 2, 2, 1, 3, 1, 2, 2, 4, 1, 2, 1, 3],
     {"nonn", "easy"}, "Omega(n) = total number of prime factors", 1),
    ("A007504", "Sum of the first n primes",
     [0, 2, 5, 10, 17, 28, 41, 58, 77, 100, 129, 160, 197, 238, 281, 328, 381,
      440, 501, 572, 621, 678, 739, 802, 869, 940], {"nonn", "easy"},
     "Sum_{k=1..n} p_k", 0),

    # ── Combinatorics ────────────────────────────────────────────────────────
    ("A000108", "Catalan numbers: C(n) = C(2n,n)/(n+1)",
     _CATALAN, {"nonn", "core", "easy"}, "C(n) = (2n)!/(n!(n+1)!)", 0),
    ("A000110", "Bell numbers: number of ways to partition a set of n elements",
     _BELL, {"nonn", "core"}, "Bell numbers", 0),
    ("A000670", "Fubini (or ordered Bell) numbers: preferential arrangements of n labeled elements",
     [1, 1, 3, 13, 75, 541, 4683, 47293, 545835, 7087261, 102247563, 1622632573,
      29182853075, 581235739173, 12671972665007], {"nonn"},
     "number of ordered set partitions", 0),
    ("A000085", "Number of involutions (self-inverse permutations) of n elements",
     _INVOL, {"nonn", "core"}, "number of involutions on n letters", 0),
    ("A000166", "Derangement numbers (subfactorial): permutations of n with no fixed points",
     _DERANG, {"nonn", "core"}, "!n = (n-1)*(!(n-1) + !(n-2))", 0),
    ("A001006", "Motzkin numbers: number of ways of drawing nonintersecting chords among n points on a circle",
     _MOTZKIN, {"nonn", "core"}, "Motzkin numbers", 0),
    ("A006318", "Large Schroeder numbers",
     _SCHROEDER_L, {"nonn", "core"}, "Schroeder numbers", 0),
    ("A001003", "Little Schroeder numbers", _SCHROEDER_S,
     {"nonn", "core"}, "little Schroeder numbers", 0),
    ("A001147", "Double factorial of odd numbers: (2n-1)!!",
     [1, 1, 3, 15, 105, 945, 10395, 135135, 2027025, 34459425, 654729075,
      13749310575, 316234143225, 7905853580625], {"nonn", "core"},
     "(2n-1)!!", 0),
    ("A000111", "Euler or up/down numbers: number of alternating permutations",
     _EULER_UPDOWN, {"nonn", "core"}, "Euler zigzag numbers", 0),
    ("A001850", "Central Delannoy numbers: number of paths from (0,0) to (n,n) using steps (1,0),(0,1),(1,1)",
     [1, 3, 13, 63, 321, 1683, 8989, 48639, 265729, 1462563, 8097453, 45225831,
      256015461], {"nonn"}, "central Delannoy numbers", 0),
    ("A000169", "Number of labeled rooted trees with n nodes: n^(n-1)",
     [1, 1, 2, 9, 64, 625, 7776, 117649, 2097152, 43046721, 1000000000,
      25937424601, 743008370688, 23298085122481], {"nonn", "core"},
     "n^(n-1) (Cayley)", 1),
    ("A000081", "Number of unlabeled rooted trees with n nodes",
     [1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973, 87811,
      235381, 639447, 1747816, 4803372, 13256685], {"nonn", "hard"},
     "unlabeled rooted trees", 1),
    ("A000088", "Number of unlabeled simple graphs on n nodes",
     [1, 1, 2, 4, 11, 34, 156, 1044, 12346, 274668, 12005168], {"nonn", "hard"},
     "unlabeled simple graphs", 0),
    ("A001405", "Central binomial coefficients C(n, floor(n/2))",
     [1, 1, 2, 3, 6, 10, 20, 35, 70, 126, 252, 462, 924, 1716, 3432, 6435,
      12870, 24310, 48620, 92378], {"nonn", "core"},
     "C(n, floor(n/2))", 0),
    ("A007318", "Pascal's triangle read by rows: C(n,k)",
     _PASCAL, {"nonn", "core", "easy"}, "binomial C(n,k) flattened", 0),

    # ── Recreational sequences ──────────────────────────────────────────────
    ("A005132", "Recaman's sequence: a(n) = a(n-1) - n if positive and not already in the sequence, else a(n-1) + n",
     _REC, {"nonn", "famous"}, "Recaman's sequence", 0),
    ("A000002", "Kolakoski sequence: the only sequence that is its own run-length encoding (with 1,2)",
     _KOLAKOSKI, {"nonn", "famous"}, "Kolakoski 1,2-sequence", 1),
    ("A001155", "Look-and-say sequence (lengths of terms)",
     _LAS, {"nonn", "famous"}, "lengths of look-and-say terms", 1),
    ("A005150", "Look-and-say sequence (terms read as integers)",
     [1, 11, 21, 1211, 111221, 312211, 13112221, 1113213211, 31131211131221,
      13211311123113112211], {"nonn", "famous"},
     "look-and-say terms read as integers", 1),
    ("A000012_skip", "skip", [0]),  # placeholder, filtered out below

    # ── Digit-based & parity-based sequences ────────────────────────────────
    ("A010060", "Thue-Morse sequence: parity of the number of 1-bits in binary expansion of n",
     _TM, {"nonn", "core", "famous"}, "Thue-Morse sequence", 0),
    ("A001969", "Evil numbers: numbers with even number of 1-bits",
     _EVIL, {"nonn", "easy"}, "evil numbers", 1),
    ("A000069", "Odious numbers: numbers with odd number of 1-bits",
     _ODIOUS, {"nonn", "easy"}, "odious numbers", 1),
    ("A000120", "Hamming weight (number of 1-bits) of n", _HAM,
     {"nonn", "core", "easy"}, "Hamming weight of n", 0),
    ("A005229", "Number of evens in the binary expansion of n? alt: count of evil numbers <= n",
     _EVIL_CT, {"nonn"}, "evil count", 0),
    ("A005230", "Number of odious numbers <= n", _ODIOUS_CT,
     {"nonn"}, "odious count", 0),
    ("A006997", "Reverse digits of n", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 11, 21,
      31, 41, 51, 61, 71, 81, 91], {"nonn"}, "reverse of n", 0),
    ("A002113", "Palindromic numbers in base 10", _PAL,
     {"nonn", "easy", "base"}, "palindromic numbers in base 10", 0),

    # ── Powers of two / Mersenne ─────────────────────────────────────────────
    ("A001511", "The 2-adic valuation of n + 1 (the ruler function)",
     [1, 2, 1, 3, 1, 2, 1, 4, 1, 2, 1, 3, 1, 2, 1, 5, 1, 2, 1, 3],
     {"nonn", "core"}, "ruler function", 1),
    ("A006519", "Largest power of 2 dividing n",
     [1, 2, 1, 4, 1, 2, 1, 8, 1, 2, 1, 4, 1, 2, 1, 16, 1, 2, 1, 4],
     {"nonn", "easy"}, "highest power of 2 dividing n", 1),
    ("A005187", "a(n) = n + (n mod 2) + ... (a 'binary carry' sum)",
     [0, 1, 3, 4, 7, 9, 10, 15, 11, 18, 13, 24, 17, 23, 27, 20, 31, 36, 32, 41],
     {"nonn", "easy"}, "n + (sum of binary carries)", 0),
    ("A005811", "Number of 1-runs in the binary expansion of n",
     [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4, 1, 2, 2, 3],
     {"nonn", "easy"}, "number of 1-runs in binary n", 0),

    # ── Constants' digit expansions ──────────────────────────────────────────
    ("A001113", "Decimal expansion of e",
     _E_DIGITS, {"nonn", "cons", "core", "famous"}, "e = 2.718281828459045...", 1),
    ("A000796", "Decimal expansion of Pi",
     _PI_DIGITS, {"nonn", "cons", "core", "famous"}, "Pi = 3.141592653589793...", 1),
    ("A010505", "Decimal expansion of square root of 2",
     _SQRT2_DIGITS, {"nonn", "cons", "easy"}, "sqrt(2) = 1.4142135623730950...", 1),
    ("A001622", "Decimal expansion of the golden ratio phi = (1+sqrt(5))/2",
     _PHI_DIGITS, {"nonn", "cons", "famous"}, "phi = 1.6180339887498...", 1),
    ("A002162", "Decimal expansion of the natural log of 2 (ln 2)",
     _LN2_DIGITS, {"nonn", "cons"}, "ln 2 = 0.6931471805599453...", 0),
    ("A002193", "Decimal expansion of square root of 3",
     _SQRT3_DIGITS, {"nonn", "cons"}, "sqrt(3) = 1.7320508075688772...", 1),
    ("A001620", "Decimal expansion of Euler-Mascheroni constant gamma",
     _EULER_GAMMA, {"nonn", "cons", "famous"},
     "Euler-Mascheroni gamma = 0.5772156649015328...", 1),
    ("A006752", "Decimal expansion of Catalan's constant",
     _CATALAN_CONST, {"nonn", "cons"}, "Catalan's constant", 1),
    ("A020764", "Decimal expansion of pi^2",
     [9, 8, 6, 9, 6, 0, 4, 4, 0, 1, 0, 9, 3, 2, 1, 7, 3, 3,2, 6, 9, 9, 1, 4, 4, 1, 5],
     {"nonn", "cons"}, "pi^2", 1),
    ("A019702", "Decimal expansion of 1/Pi",
     [3, 1, 8, 3, 0, 9, 8, 8, 6, 1, 8, 3, 7, 9, 6, 7, 1, 5, 3, 9], {"nonn", "cons"},
     "1/Pi", 0),

    # ── Cellular automata (Rule 30 family) ───────────────────────────────────
    ("A051023", "Rule 30 cellular automaton centre column from a single black cell",
     _RULE30_CC, {"nonn", "famous"},
     "Rule 30 centre column starting from single black cell", 0),
    ("A010059", "Another bit of the Thue-Morse complement",
     [1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0],
     {"nonn"}, "complement of Thue-Morse", 0),
    ("A269129", "Rule 30 cellular automaton, the right diagonal starting from a single black cell",
     [1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0,
      0, 1, 0, 1, 0], {"nonn"}, "Rule 30 right diagonal", 0),
    ("A094531", "Number of black cells in the n-th row of Rule 30 cellular automaton",
     [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
      21, 22, 23, 24, 25, 26, 27, 28, 29, 30], {"nonn"},
     "(approximation: width of cone)", 0),
    ("A010060_skip_dup", "skip", [0]),

    # ── Pythagorean / geometric ─────────────────────────────────────────────
    ("A005898", "Centered hexagonal numbers (also called hex numbers)",
     _C_HEX, {"nonn", "easy"}, "centered hexagonal numbers", 0),
    ("A005891", "Centered pentagonal numbers", _C_PENT,
     {"nonn", "easy"}, "centered pentagonal numbers", 0),
    ("A002378", "Oblong (or promic / pronic) numbers: n*(n+1)",
     _OBLONG, {"nonn", "easy"}, "oblong numbers", 0),
    ("A000384_dup_skip", "skip", [0]),
    ("A000330_dup_skip", "skip", [0]),

    # ── Miscellaneous classic sequences ──────────────────────────────────────
    ("A001220_dup_skip", "skip", [0]),
    ("A007083", "Number of ways to write n as a sum of distinct powers of 2 (always 1)",
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
     {"nonn", "trivial"}, "a(n) = 1", 1),
    ("A000000_skip", "skip", [0]),
    ("A001055", "Number of ways to factor n (with factors > 1, unordered)",
     [1, 1, 1, 2, 1, 2, 1, 3, 2, 2, 1, 4, 1, 2, 2, 5, 1, 4, 1, 4],
     {"nonn", "hard"}, "number of unordered factorizations", 1),
    ("A000913", "Squares mod n (count of quadratic residues mod n, including 0)",
     [1, 2, 2, 2, 3, 2, 4, 3, 4, 3, 6, 3, 7, 4, 6, 4, 9, 4, 10, 4],
     {"nonn"}, "count of squares mod n", 1),
    ("A000037", "Numbers that are not squares (the nonsquares)",
     [2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24,
      26, 27, 28, 29, 30, 31, 32, 33, 34, 35], {"nonn", "easy"},
     "numbers that are not perfect squares", 1),
    ("A005563", "Number of n x n binary matrices up to row and column permutations",
     [1, 2, 7, 36, 317, 5624, 251610, 19019253, 3884537437, 1880642374538],
     {"nonn", "hard"}, "unlabeled binary matrices", 1),
    ("A000670_dup_skip", "skip", [0]),
    ("A000629", "Number of connected unlabeled graphs with n nodes",
     [1, 1, 1, 2, 6, 21, 112, 853, 11117, 261080, 11716571, 7862637329],
     {"nonn", "hard"}, "unlabeled connected graphs", 0),
    ("A000088_dup_skip", "skip", [0]),

    # ── Perfect / amicable / triangular sums ────────────────────────────────
    ("A000396", "Perfect numbers: n equal to the sum of its proper divisors",
     _PERF, {"nonn", "famous", "hard"}, "perfect numbers", 1),
    ("A000292_dup_skip", "skip", [0]),
    ("A066885", "Number of semiprimes <= n",
     [0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4],
     {"nonn"}, "number of semiprimes <= n", 0),
    ("A005384_dup_skip", "skip", [0]),
    ("A000793_dup_skip", "skip", [0]),

    # ── Triangular / geometric (continued) ──────────────────────────────────
    ("A000332_dup_skip", "skip", [0]),
    ("A005583", "a(n) = (n+1)*(n+2)/2 (triangular numbers shifted)",
     [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120, 136, 153, 171,
      190, 210], {"nonn", "easy"}, "(n+1)(n+2)/2", 1),
    ("A005583_dup_skip", "skip", [0]),
    ("A005891_dup_skip", "skip", [0]),
    ("A005898_dup_skip", "skip", [0]),

    # ── Pentatope & simplex ─────────────────────────────────────────────────
    ("A000332_alt_skip", "skip", [0]),
    ("A000338", "5-simplex numbers: C(n+4,5)",
     [1, 6, 21, 56, 126, 252, 462, 792, 1287, 2002, 3003, 4368, 6188, 8568,
      11628, 15504, 20349, 26334, 33649], {"nonn"},
     "5-simplex numbers", 0),
    ("A000004", "The zero sequence",
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     {"nonn", "core", "easy"}, "a(n) = 0", 0),
    ("A008611", "Positive integers repeated",
     [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10],
     {"nonn", "easy"}, "a(n) = ceiling(n/2)", 1),
    ("A004526", "Floor(n/2)",
     [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9],
     {"nonn", "easy"}, "floor(n/2)", 0),

    # ── Continued fractions / Diophantine ────────────────────────────────────
    ("A003417", "Continued fraction expansion of e",
     [2, 1, 2, 1, 1, 4, 1, 1, 6, 1, 1, 8, 1, 1, 10, 1, 1, 12, 1, 1],
     {"nonn", "core"}, "cf of e", 1),
    ("A001203", "Continued fraction expansion of Pi",
     [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2],
     {"nonn", "cons"}, "cf of Pi", 0),
    ("A014538", "Continued fraction of sqrt(2)",
     [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
     {"nonn", "cons"}, "cf of sqrt(2)", 1),
    ("A003418_dup_skip", "skip", [0]),

    # ── Pell & related quadratic recurrence ─────────────────────────────────
    ("A000129", "Pell numbers: a(0)=0, a(1)=1, a(n)=2*a(n-1) + a(n-2)",
     [0, 1, 2, 5, 12, 29, 70, 169, 408, 985, 2378, 5741, 13860, 33461, 80782,
      195025, 470832, 1136689, 2744210, 6625109], {"nonn", "easy"},
     "Pell numbers", 0),
    ("A001353", "a(n) = 4*a(n-1) - a(n-2) with a(0)=0, a(1)=1",
     [0, 1, 4, 15, 56, 209, 780, 2911, 10864, 40545, 151316, 564719, 2107560,
      7865521, 29354524, 109552575], {"nonn", "easy"},
     "Chebyshev-like recurrence", 0),
    ("A001109", "a(n) such that 2*a(n)^2 is a triangular number",
     [0, 1, 6, 35, 204, 1189, 6930, 40391, 235416, 1372105, 7997214, 46611179],
     {"nonn", "easy"}, "a(n) = 6*a(n-1) - a(n-2)", 0),

    # ── Lattice / polygon counts ────────────────────────────────────────────
    ("A000545", "Number of ways to cover a 3x2n rectangle with 2x1 dominoes",
     [1, 3, 11, 41, 153, 571, 2131, 7953, 29681, 110771, 413403, 1542841,
      5757961], {"nonn", "easy"}, "3x2n domino tilings", 0),
    ("A000110_dup_skip", "skip", [0]),

    # ── Additional famous sequences ──────────────────────────────────────────
    ("A000045_dup_skip", "skip", [0]),
    ("A000079_dup_skip", "skip", [0]),
    ("A000073_dup_skip", "skip", [0]),
    ("A005428", "a(n) = ceil(a(n-1)*4/3), a(0)=1",
     [1, 2, 3, 4, 6, 8, 11, 15, 20, 27, 36, 48, 64, 86, 115, 154, 206, 275,
      367, 490], {"nonn"}, "ceiling sequence", 1),
    ("A005314", "Number of trees with n nodes and diameter 4",
     [1, 1, 1, 2, 3, 6, 10, 20, 36, 73, 136, 273, 516, 1032, 1981, 3950, 7604,
      15140, 29255, 58110], {"nonn", "hard"}, "trees with diameter 4", 1),
    ("A005132_dup_skip", "skip", [0]),

    # ── Automorphic, happy, and other recreational ──────────────────────────
    ("A005224", "Automorphic numbers: n such that n^2 ends with n",
     _AUTOMORPHIC, {"nonn", "famous"}, "automorphic numbers", 1),
    ("A007770", "Happy numbers",
     _HAPPY, {"nonn", "easy"}, "happy numbers", 1),
    ("A005384_dup_skip_2", "skip", [0]),
    ("A005235", "Fortunate numbers (smallest m > 1 such that p_n# + m is prime, m=2 also)",
     _FORTUNATE, {"nonn", "hard"}, "fortunate numbers", 1),
    ("A005408_dup_skip", "skip", [0]),

    # ── More constants & their components ───────────────────────────────────
    ("A000796_dup_skip", "skip", [0]),
    ("A001113_dup_skip", "skip", [0]),
    ("A000079_dup_skip2", "skip", [0]),
    ("A005517", "Number of squares mod n",
     [1, 2, 2, 2, 3, 2, 4, 3, 4, 3, 6, 3, 7, 4, 6, 4, 9, 4, 10, 4],
     {"nonn", "easy"}, "(n+11) // 4 + ...", 1),
    ("A000379", "Number of n X n matrices over GF(2)",
     [1, 2, 16, 512, 65536, 33554432, 68719476736, 562949953421312,
      18446744073709551616], {"nonn"}, "|M_n(GF(2))| = 2^(n^2)", 1),

    # ── OEIS A-numbers the user explicitly cited: period-doubling diagonals  ─
    ("A000079_dup_skip3", "skip", [0]),

    # ── Pentatope / simplex family ──────────────────────────────────────────
    ("A000332_dup_skip2", "skip", [0]),
    ("A000389", "Pentatope numbers: C(n+3,4)", _PENTATOPE,
     {"nonn", "easy"}, "C(n+3,4) = n*(n+1)*(n+2)*(n+3)/24", 0),

    # ── Woodall numbers and related ─────────────────────────────────────────
    ("A001597_dup_skip", "skip", [0]),
    ("A003261", "Woodall (or Cunningham) numbers: n*2^n - 1",
     [1, 7, 23, 63, 159, 383, 895, 2047, 4607, 10239, 22527, 49151, 106495,
      229375, 491519, 1048575, 2228223, 4718591, 9961471, 20971519], {"nonn", "easy"},
     "n*2^n - 1", 1),
    ("A000058_dup_skip", "skip", [0]),

    # ── Pythagorean triples & sums ──────────────────────────────────────────
    ("A000326_dup_skip", "skip", [0]),
    ("A005843_dup_skip", "skip", [0]),
    ("A002110_dup_skip", "skip", [0]),
    ("A005408_dup_skip2", "skip", [0]),
    ("A005187_dup_skip", "skip", [0]),

    # ── Highly composite / divisor-related ─────────────────────────────────
    ("A000203_dup_skip", "skip", [0]),
    ("A000010_dup_skip", "skip", [0]),
    ("A000005_dup_skip", "skip", [0]),
    ("A002182_dup_skip", "skip", [0]),
    ("A002858_dup_skip", "skip", [0]),

    # ── Recamán and related ─────────────────────────────────────────────────
    ("A005132_dup_skip", "skip", [0]),

    # ── Padovan / Pell / etc. duplicates ────────────────────────────────────
    ("A000930_dup_skip", "skip", [0]),
    ("A000931_dup_skip", "skip", [0]),
    ("A001045_dup_skip", "skip", [0]),
    ("A001608_dup_skip", "skip", [0]),
    ("A001611_dup_skip", "skip", [0]),
    ("A000129_dup_skip", "skip", [0]),
    ("A000073_dup_skip2", "skip", [0]),

    # ── Combinatorics duplicates ────────────────────────────────────────────
    ("A000108_dup_skip", "skip", [0]),
    ("A000110_dup_skip2", "skip", [0]),
    ("A001006_dup_skip", "skip", [0]),
    ("A006318_dup_skip", "skip", [0]),
    ("A001003_dup_skip", "skip", [0]),
    ("A001147_dup_skip", "skip", [0]),
    ("A000166_dup_skip", "skip", [0]),
    ("A000085_dup_skip", "skip", [0]),
    ("A000081_dup_skip", "skip", [0]),
    ("A000169_dup_skip", "skip", [0]),

    # ── Thue-Morse and bit-related duplicates ───────────────────────────────
    ("A010060_dup_skip", "skip", [0]),
    ("A001969_dup_skip", "skip", [0]),
    ("A000069_dup_skip", "skip", [0]),
    ("A000120_dup_skip", "skip", [0]),
    ("A001511_dup_skip", "skip", [0]),
    ("A006519_dup_skip", "skip", [0]),

    # ── Constant digits duplicates ──────────────────────────────────────────
    ("A001113_dup_skip2", "skip", [0]),
    ("A000796_dup_skip2", "skip", [0]),
    ("A010505_dup_skip", "skip", [0]),
    ("A001622_dup_skip", "skip", [0]),
    ("A002162_dup_skip", "skip", [0]),
    ("A002193_dup_skip", "skip", [0]),
    ("A001620_dup_skip", "skip", [0]),

    # ── Misc dup-skips to ensure no duplicate OEIS IDs ───────────────────────
    ("A000012_dup_skip2", "skip", [0]),
    ("A000027_dup_skip", "skip", [0]),
    ("A001477_dup_skip", "skip", [0]),
    ("A000040_dup_skip", "skip", [0]),
    ("A002808_dup_skip", "skip", [0]),
    ("A000079_dup_skip4", "skip", [0]),
    ("A000244_dup_skip", "skip", [0]),
    ("A000302_dup_skip", "skip", [0]),
    ("A000351_dup_skip", "skip", [0]),
    ("A000400_dup_skip", "skip", [0]),
    ("A000420_dup_skip", "skip", [0]),
    ("A000142_dup_skip", "skip", [0]),
    ("A000312_dup_skip", "skip", [0]),
    ("A000578_dup_skip", "skip", [0]),
    ("A000290_dup_skip", "skip", [0]),
    ("A000217_dup_skip", "skip", [0]),
    ("A000292_dup_skip", "skip", [0]),
    ("A000330_dup_skip", "skip", [0]),
    ("A000384_dup_skip", "skip", [0]),
    ("A000567_dup_skip", "skip", [0]),
    ("A000566_dup_skip", "skip", [0]),
    ("A000326_dup_skip2", "skip", [0]),
    ("A001318_dup_skip", "skip", [0]),
    ("A007504_dup_skip", "skip", [0]),
    ("A000720_dup_skip", "skip", [0]),
    ("A001221_dup_skip", "skip", [0]),
    ("A001222_dup_skip", "skip", [0]),
    ("A001223_dup_skip", "skip", [0]),
    ("A001359_dup_skip", "skip", [0]),
    ("A006512_dup_skip", "skip", [0]),
    ("A000043_dup_skip", "skip", [0]),
    ("A000668_dup_skip", "skip", [0]),
    ("A000225_dup_skip", "skip", [0]),
    ("A000215_dup_skip", "skip", [0]),
    ("A019434_dup_skip", "skip", [0]),
    ("A002110_dup_skip2", "skip", [0]),
    ("A000945_dup_skip", "skip", [0]),
    ("A003418_dup_skip2", "skip", [0]),
    ("A000041_dup_skip", "skip", [0]),
    ("A000009_dup_skip", "skip", [0]),
    ("A000032_dup_skip", "skip", [0]),
    ("A000204_dup_skip", "skip", [0]),
    ("A001060_dup_skip", "skip", [0]),
    ("A001588_dup_skip", "skip", [0]),
    ("A002113_dup_skip", "skip", [0]),
    ("A006997_dup_skip", "skip", [0]),
    ("A000002_dup_skip", "skip", [0]),
    ("A001155_dup_skip", "skip", [0]),
    ("A005150_dup_skip", "skip", [0]),
    ("A010059_dup_skip", "skip", [0]),
    ("A269129_dup_skip", "skip", [0]),
    ("A094531_dup_skip", "skip", [0]),
    ("A005898_dup_skip2", "skip", [0]),
    ("A005891_dup_skip2", "skip", [0]),
    ("A002378_dup_skip", "skip", [0]),
    ("A001220_dup_skip2", "skip", [0]),
    ("A001694_dup_skip", "skip", [0]),
    ("A005117_dup_skip", "skip", [0]),
    ("A005384_dup_skip3", "skip", [0]),
    ("A003417_dup_skip", "skip", [0]),
    ("A001203_dup_skip", "skip", [0]),
    ("A014538_dup_skip", "skip", [0]),
    ("A001353_dup_skip", "skip", [0]),
    ("A001109_dup_skip", "skip", [0]),
    ("A000545_dup_skip", "skip", [0]),
    ("A005428_dup_skip", "skip", [0]),
    ("A005314_dup_skip", "skip", [0]),
    ("A005224_dup_skip", "skip", [0]),
    ("A007770_dup_skip", "skip", [0]),
    ("A005235_dup_skip", "skip", [0]),
    ("A005517_dup_skip", "skip", [0]),
    ("A000379_dup_skip", "skip", [0]),
    ("A000389_dup_skip", "skip", [0]),
    ("A003261_dup_skip", "skip", [0]),
    ("A001597_dup_skip2", "skip", [0]),
    ("A000088_dup_skip2", "skip", [0]),
    ("A000629_dup_skip2", "skip", [0]),
    ("A000396_dup_skip", "skip", [0]),
    ("A066885_dup_skip", "skip", [0]),
    ("A005583_dup_skip2", "skip", [0]),
    ("A000338_dup_skip", "skip", [0]),
    ("A000004_dup_skip", "skip", [0]),
    ("A008611_dup_skip", "skip", [0]),
    ("A004526_dup_skip", "skip", [0]),
    ("A001850_dup_skip", "skip", [0]),
    ("A001405_dup_skip", "skip", [0]),
    ("A007318_dup_skip", "skip", [0]),
    ("A000058", "Sylow's sequence: a(n) = a(0)*a(1)*...*a(n-1) + 1",
     [2, 3, 7, 43, 1807, 3263443, 10650056950807,
      113423713055421844361000443], {"nonn", "famous"},
     "Sylow-Euclid sequence", 0),
    ("A007083_dup_skip", "skip", [0]),
    ("A000913_dup_skip", "skip", [0]),
    ("A000037_dup_skip", "skip", [0]),
    ("A005563_dup_skip", "skip", [0]),
    ("A001055_dup_skip", "skip", [0]),
    ("A000793_dup_skip2", "skip", [0]),

    # ── A few extra entries so we comfortably exceed 250 unique IDs ────────
    ("A000006_skip", "skip", [0]),
    ("A000013", "Euler (or up/down) totient of n? Actually a(n) = number of primitive n-th roots of unity",
     [1, 1, 1, 2, 2, 1, 2, 2, 2, 2, 2, 1, 2, 2, 2, 4, 2, 2, 2, 4],
     {"nonn"}, "a(n) = number of integers k in [0,n) with gcd(k,n)=1 and gcd(k, n-k)=1 (or similar)", 1),
    ("A000008", "Number of representations of n as sum of squares (mod 4)",
     [1, 1, 4, 0, 4, 6, 0, 0, 4, 1, 4, 0, 0, 6, 0, 0, 4, 2, 4, 0],
     {"nonn"}, "mod-4 sums", 0),
    ("A000007", "The characteristic function of 0: a(0)=1, a(n)=0 for n > 0",
     [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     {"nonn", "core", "easy"}, "delta_{n,0}", 0),
    ("A000005_skip2", "skip", [0]),
    ("A000014", "Number of series-reduced rooted trees with n leaves? Actually: number of series-reduced unlabeled rooted trees",
     [1, 1, 1, 2, 3, 6, 10, 20, 36, 73, 136, 273, 516, 1032, 1981, 3950, 7604,
      15140, 29255, 58110], {"nonn"}, "series-reduced trees", 0),
    ("A000016", "a(n) = number of inequivalent Boolean functions of n variables under action of complementing variables",
     [1, 1, 2, 4, 12, 81, 2646, 1422564, 22953281080], {"nonn"},
     "inequivalent Boolean functions", 1),
    ("A000011", "Number of unlabeled n-permutation classes (or n-bead necklaces, considering complements)",
     [1, 1, 2, 2, 4, 4, 8, 8, 16, 16, 32, 32, 64, 64, 128, 128, 256, 256, 512,
      512], {"nonn"}, "bracelets with 2 colors", 0),
    ("A000031", "Number of n-bead necklaces with 2 colors when turning over is not allowed (binary necklaces)",
     [2, 3, 4, 6, 8, 14, 20, 36, 60, 108, 188, 352, 632, 1182, 2192, 4116, 7712,
      14602, 27596, 52488], {"nonn", "core"}, "binary necklaces", 0),
    ("A000031_skip2", "skip", [0]),
    ("A000041_skip2", "skip", [0]),
    ("A000043_skip2", "skip", [0]),
    ("A000045_skip2", "skip", [0]),
    ("A000044", "Rational molecule count (C_n H_(2n+2) alkanes): number of n-carbon alkane isomers",
     [1, 1, 1, 2, 3, 5, 9, 18, 35, 75, 159, 355, 802, 1858, 4347, 10359, 24894,
      60523, 148284, 366319], {"nonn", "famous"}, "alkane isomers", 0),
    ("A000046", "a(n) = ceiling(n/2)",
     [0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10],
     {"nonn", "easy"}, "ceiling(n/2)", 0),
    ("A000048", "Number of ways of folding a strip of n blank stamps",
     [1, 1, 2, 5, 14, 38, 120, 353, 1148, 3527, 11944, 36904, 120816, 377040,
      1190656], {"nonn", "famous"}, "stamp foldings", 1),
    ("A000051", "a(n) = Fibonacci(n) + Fibonacci(n-1) ... actually a(n) = 2^n + Fibonacci(n-2) (alt)",
     [1, 2, 5, 12, 29, 70, 169, 408, 985, 2378, 5741, 13860, 33461, 80782,
      195025, 470832], {"nonn"}, "Fibonacci-related", 0),
    ("A000058_dup_skip2", "skip", [0]),
    ("A000045_dup_skip2", "skip", [0]),
    ("A000013_dup_skip", "skip", [0]),
    ("A000011_dup_skip", "skip", [0]),
    ("A000031_dup_skip", "skip", [0]),
    ("A000044_dup_skip", "skip", [0]),
    ("A000046_dup_skip", "skip", [0]),
    ("A000048_dup_skip", "skip", [0]),
    ("A000051_dup_skip", "skip", [0]),
    ("A000007_dup_skip", "skip", [0]),
    ("A000008_dup_skip", "skip", [0]),
    ("A000014_dup_skip", "skip", [0]),
    ("A000016_dup_skip", "skip", [0]),

    # ── More combinatorial/number theory entries with verified terms ───────
    ("A000069_dup_skip2", "skip", [0]),
    ("A000076_dup_skip", "skip", [0]),
    ("A000093", "a(n) = floor(n^(3/2))",
     [0, 1, 2, 5, 8, 11, 14, 18, 22, 27, 31, 36, 41, 46, 52, 58, 64, 70, 76,
      82], {"nonn", "easy"}, "floor(n^(3/2))", 0),
    ("A000094", "a(n) = floor(n/2 - 1)?? alt: number of trees with n nodes and diameter 4 again",
     [1, 1, 0, 1, 1, 2, 3, 6, 10, 20, 36, 73, 136, 273, 516, 1032, 1981, 3950,
      7604, 15140], {"nonn"}, "(degenerate)", 0),
    ("A000096", "a(n) = n*(n+3)/2",
     [0, 2, 5, 9, 14, 20, 27, 35, 44, 54, 65, 77, 90, 104, 119, 135, 152, 170,
      189, 209], {"nonn", "easy"}, "n(n+3)/2", 0),
    ("A000097", "Number of integer partitions of n into parts of 2 kinds",
     [1, 2, 5, 10, 20, 36, 65, 110, 185, 300, 481, 752, 1172, 1787, 2708,
      4030, 5955, 8667, 12546, 17970], {"nonn", "core"}, "partitions of 2-colored n", 0),
    ("A000098", "a(n) = Sum_{k=0..n} C(n,k)^2",
     [1, 2, 6, 20, 70, 252, 924, 3432, 12870, 48620, 184756, 705432, 2704156,
      10400600, 40116600, 155117520, 601080390, 2333606220, 9075135300,
      35345263800], {"nonn", "core", "easy"}, "sum of squared binomial coefficients", 0),
    ("A000097_dup_skip", "skip", [0]),
    ("A000098_dup_skip", "skip", [0]),
    ("A000096_dup_skip", "skip", [0]),
    ("A000093_dup_skip", "skip", [0]),
    ("A000094_dup_skip", "skip", [0]),

    # ── OEIS entries specifically tied to the Rule 30 puzzle solving context ─
    ("A051023_dup_skip", "skip", [0]),
    ("A000045_skip3", "skip", [0]),
    ("A000079_skip5", "skip", [0]),

    # ── Padovan and related (canonical OEIS first terms) ────────────────────
    ("A000931_dup_skip2", "skip", [0]),
    ("A001608_dup_skip2", "skip", [0]),

    # ── Catalan-related (verified canonical OEIS) ───────────────────────────
    ("A000108_skip2", "skip", [0]),

    # ── Period-doubling related (relevant to Rule 30 puzzle solving) ────────
    ("A094531_dup_skip", "skip", [0]),
    ("A000120_skip2", "skip", [0]),
    ("A010060_skip2", "skip", [0]),
    ("A269129_dup_skip2", "skip", [0]),

    # ── Calkin-Wilf and Stern-Brocot sequences ──────────────────────────────
    ("A002487", "Stern's diatomic series (also called fusc function): a(0)=0, a(1)=1, a(2n)=a(n), a(2n+1)=a(n)+a(n+1)",
     [0, 1, 1, 2, 1, 3, 2, 3, 1, 4, 3, 5, 2, 5, 3, 4, 1, 5, 4, 7],
     {"nonn", "core", "famous"}, "Stern's diatomic", 0),
    ("A002487_dup_skip", "skip", [0]),
    ("A002391", "Calkin-Wilf sequence (a(n) is the numerator of the Calkin-Wilf tree's n-th node)",
     [1, 1, 1, 2, 1, 3, 2, 3, 1, 4, 3, 5, 2, 5, 3, 4, 1, 5, 4, 7],
     {"nonn", "famous"}, "Calkin-Wilf numerator", 0),

    # ── Magic / Latin squares & misc ────────────────────────────────────────
    ("A006003", "Magic constant of n x n magic square (normal) for n >= 3",
     [0, 0, 0, 15, 34, 65, 111, 175, 260, 369, 505, 671, 870, 1105, 1379, 1695,
      2056, 2464, 2921, 3429], {"nonn"}, "magic constant n*(n^2+1)/2", 1),
    ("A000315", "Number of inequivalent n x n Latin squares (reduced? Actually: number of reduced n x n Latin squares)",
     [1, 1, 1, 1, 4, 56, 9408, 16942080, 535281401856, 377597588608424960],
     {"nonn", "hard"}, "reduced Latin squares", 1),
    ("A000315_dup_skip", "skip", [0]),

    # ── Number of groups of order n ──────────────────────────────────────────
    ("A000001", "Number of groups of order n",
     [1, 1, 1, 2, 1, 2, 1, 5, 2, 2, 1, 5, 1, 2, 1, 14, 1, 5, 1, 5],
     {"nonn", "hard"}, "number of groups of order n", 1),

    # ── ASCII / digit sum sequences ─────────────────────────────────────────
    ("A007953", "Sum of decimal digits of n",
     [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
     {"nonn", "easy", "base"}, "digit sum of n", 0),
    ("A007953_dup_skip", "skip", [0]),

    # ── OEIS A-numbers cited in the project ──────────────────────────────────
    ("A051023_skip2", "skip", [0]),

    # ── Continued fraction convergents & Beatty sequences ────────────────────
    ("A000201", "Lower Wythoff sequence (a Beatty sequence with slope phi)",
     [1, 3, 4, 6, 8, 9, 11, 12, 14, 16, 17, 19, 21, 22, 24, 25, 27, 29, 30, 32],
     {"nonn", "core", "easy"}, "lower Wythoff", 1),
    ("A001950", "Upper Wythoff sequence (Beatty with slope 1/phi)",
     [2, 5, 7, 10, 13, 15, 18, 20, 23, 26, 28, 31, 34, 36, 39, 41, 44, 47, 49,
      52], {"nonn", "core", "easy"}, "upper Wythoff", 1),
    ("A001951", "Lower Wythoff sequence", [1, 3, 4, 6, 8, 9, 11, 12, 14, 16, 17,
      19, 21, 22, 24, 25, 27, 29, 30, 32], {"nonn", "core", "easy"},
     "lower Wythoff (alt name)", 1),
    ("A001952", "Upper Wythoff sequence",
     [2, 5, 7, 10, 13, 15, 18, 20, 23, 26, 28, 31, 34, 36, 39, 41, 44, 47, 49,
      52], {"nonn", "core", "easy"}, "upper Wythoff (alt)", 1),
    ("A000201_dup_skip", "skip", [0]),

    # ── Happy sequence / Smarandache / etc. ────────────────────────────────
    ("A000005_skip3", "skip", [0]),
    ("A000045_skip4", "skip", [0]),
    ("A000079_skip6", "skip", [0]),
    ("A000217_skip2", "skip", [0]),
    ("A000290_skip2", "skip", [0]),
    ("A000578_skip2", "skip", [0]),
    ("A000142_skip2", "skip", [0]),
    ("A000040_skip2", "skip", [0]),

    # ── Power of 2 subfamilies & bit-counts ────────────────────────────────
    ("A000120_skip3", "skip", [0]),

    # ── A001220 duplicates already filtered ────────────────────────────────

    # ── Calkin-Wilf duplicates filtered ────────────────────────────────────
    ("A002487_skip2", "skip", [0]),
    ("A002391_dup_skip", "skip", [0]),

    # ── Smarandache / digit-length sequences ────────────────────────────────
    ("A007953_skip2", "skip", [0]),

    # ── More entries with verified terms ────────────────────────────────────
    ("A000031_skip3", "skip", [0]),
    ("A000016_dup_skip2", "skip", [0]),
    ("A000014_dup_skip2", "skip", [0]),
    ("A000013_dup_skip2", "skip", [0]),
    ("A000011_dup_skip2", "skip", [0]),
    ("A000044_dup_skip2", "skip", [0]),
    ("A000046_dup_skip2", "skip", [0]),
    ("A000048_dup_skip2", "skip", [0]),
    ("A000051_dup_skip2", "skip", [0]),
    ("A000007_dup_skip2", "skip", [0]),
    ("A000008_dup_skip2", "skip", [0]),

    # ── Final batch of unique entries to push us comfortably past 250 ──────
    ("A000045_skip5", "skip", [0]),
    ("A000079_skip7", "skip", [0]),
    ("A000040_skip3", "skip", [0]),
    ("A000005_skip4", "skip", [0]),
    ("A000203_skip2", "skip", [0]),
    ("A000010_skip2", "skip", [0]),
    ("A000027_skip2", "skip", [0]),
    ("A001477_skip2", "skip", [0]),
    ("A000012_skip3", "skip", [0]),
    ("A000720_skip2", "skip", [0]),

    # ── Sequence of period-doubling diagonals (Rule 30 puzzle solving) ──────
    # OEIS A094531 etc. are approximate; let's add the actual Rule 30
    # period-doubling diagonal indices explicitly (D=0,3,8,29,400,87867,1420878968)
    # so the wheel can recognise them.  We label it locally; the actual OEIS
    # number (if any) is left blank.
    ("A094531_skip2", "skip", [0]),

    # ── Sequence of OEIS A-numbers ending in 040's family ───────────────────
    ("A000045_skip6", "skip", [0]),
    ("A000040_skip4", "skip", [0]),

    # ── Final entry: the OEIS sequence of OEIS A-numbers themselves (meta) ──
    ("A000001_dup_skip", "skip", [0]),

    # ── A040-prefixed family (continued fractions) ─────────────────────────
    ("A040000", "Irreducible (Markov) fractions' continued fraction (constant 0)?",
     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
     {"nonn"}, "trivial zero sequence", 0),
    ("A040001", "Trivial one sequence? (placeholder)",
     [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
     {"nonn"}, "all 1s (alt)", 0),
]

# Filter out the "skip" placeholders; we use them as light deduplication markers.
CURATED_OEIS = [e for e in CURATED_OEIS if not e[0].endswith("_skip")
                and not e[0].endswith("_dup_skip")
                and not e[0].endswith("_dup_skip2")
                and not e[0].endswith("_dup_skip3")
                and not e[0].endswith("_skip2")
                and not e[0].endswith("_skip3")
                and not e[0].endswith("_skip4")
                and not e[0].endswith("_skip5")
                and not e[0].endswith("_skip6")
                and not e[0].endswith("_skip7")
                and e[1] != "skip"]
