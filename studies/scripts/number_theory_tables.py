#!/usr/bin/env python3
"""Regenerate every numeric table of ``GLM_Complete_Number_Theory_Evidence.md``.

Three tables, all exact:

1. **coherence** -- TAX, NRCI and the regime of the all-ones carrier at each
   Golay weight, computed from ``glm_universal.reasoning.coherence`` (which
   carries ``Y`` as an exact 15-digit rational, never a float);
2. **the Sturmian census** -- for each odd prime below 100, the number of ones
   the modulator emits in 500 ticks against the closed form ``floor(500/p)``
   of ``Sturmian.dsOnes_eq_floor``, and the longest zero run against its bound;
3. **the binary-period census** -- the multiplicative order of 2 mod p, whether
   p is full reptend, and the wobble entropy H(1/p);
4. **the three periods of 1/n** -- for each n from 3 to 30, the least period
   of the delta-sigma bitstream of 1/n found by search against the ``n`` that
   ``EngineeringWheels.ds_rational_period_iff`` predicts, the eventual period
   of the binary expansion of 1/n, and the polygon's closed sub-cycles counted
   by walking every stride against the closed form ``n/2 - totient(n)/2`` of
   ``Totient.subCycles_eq``.

Run it from the repository root::

    PYTHONPATH=overlay python3 studies/scripts/number_theory_tables.py

Only the entropy column is printed as a decimal, and it is computed from the
exact rational density by the package's own ``entropy_bits``.  No float is
constructed anywhere in this script -- the sieve bound is ``math.isqrt`` rather
than ``limit ** 0.5`` -- which is directive D7, and
``tests/test_number_theory_evidence.py`` checks it by parsing this file.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, isqrt
from typing import List

from glm_universal.reasoning import coherence as coh
from glm_universal.reasoning import wobble as wb

TICKS = 500


def primes_below(limit: int) -> List[int]:
    sieve = [True] * limit
    sieve[0] = sieve[1] = False
    for n in range(2, isqrt(limit) + 1):
        if sieve[n]:
            for m in range(n * n, limit, n):
                sieve[m] = False
    return [n for n in range(limit) if sieve[n]]


def multiplicative_order_of_two(p: int) -> int:
    order, value = 1, 2 % p
    while value != 1:
        value = value * 2 % p
        order += 1
    return order


def coherence_table() -> None:
    print("## 1  TAX, NRCI and regime, by Hamming weight "
          "(all coordinates 0 or 1)")
    print()
    print("| weight | TAX | NRCI | regime |")
    print("|---|---|---|---|")
    for weight in (0, 1, 2, 8, 12, 16, 24):
        tax = weight * coh.Y + Fraction(weight, 8)
        nrci = coh.B / (coh.B + tax)
        if tax <= Fraction(5, 2):
            regime = "OnBit"
        elif tax <= Fraction(10):
            regime = "Coherent"
        elif tax <= Fraction(70, 3):
            regime = "Transitional"
        else:
            regime = "Subcoherent"
        print(f"| {weight} | {coh.decimal_str(tax, 6)} | "
              f"{coh.decimal_str(nrci, 6)} | {regime} |")
    print()


def sturmian_table() -> None:
    primes = [p for p in primes_below(100) if p != 2]
    print(f"## 2  The Sturmian census: {len(primes)} odd primes, "
          f"{TICKS} ticks each")
    print()
    print("| p | floor(500/p) | measured ones | match | longest 0-run | "
          "longest run the bound permits |")
    print("|---|---|---|---|---|---|")
    matches = 0
    for p in primes:
        target = Fraction(1, p)
        bits = wb.stream_bits(target, TICKS)
        law = wb.ones_count_law(target, TICKS)
        matches += bool(law["law_holds"])
        print(f"| {p} | {law['predicted']} | {law['measured']} | "
              f"{'yes' if law['law_holds'] else 'NO'} | "
              f"{wb.longest_run(bits, 0)} | {wb.run_bound(target)} |")
    print()
    print(f"**{matches}/{len(primes)} exact matches.**")
    print()


def period_table() -> None:
    primes = [p for p in primes_below(100) if p != 2]
    print("## 3  The binary period as a fingerprint")
    print()
    print("| p | ord_p(2) | full reptend | H(1/p) |")
    print("|---|---|---|---|")
    for p in primes:
        order = multiplicative_order_of_two(p)
        entropy = wb.entropy_bits(Fraction(1, p))["value"]
        print(f"| {p} | {order} | "
              f"{'yes' if order == p - 1 else 'no'} | "
              f"{coh.decimal_str(entropy, 3)} |")
    print()


def least_stream_period(target: Fraction, horizon: int) -> int:
    """The least P with bit(i + P) = bit(i) over the whole window, by search."""
    bits = wb.stream_bits(target, horizon)
    for period in range(1, horizon // 2 + 1):
        if all(bits[i + period] == bits[i] for i in range(horizon - period)):
            return period
    raise ValueError("no period inside the window")


def binary_period(n: int) -> int:
    """The eventual period of the base-2 expansion of 1/n."""
    odd = n
    while odd % 2 == 0:
        odd //= 2
    return 1 if odd == 1 else multiplicative_order_of_two(odd)


def totient(n: int) -> int:
    return sum(1 for k in range(1, n + 1) if gcd(n, k) == 1)


def closes_early(n: int, stride: int) -> bool:
    """Walk the n-gon by ``stride`` and report whether it returns early."""
    position, steps = stride % n, 1
    while position != 0:
        position = (position + stride) % n
        steps += 1
    return steps < n


def three_periods_table() -> None:
    print("## 4  The three periods of 1/n")
    print()
    print("| n | stream period (measured) | stream period (Lean) | "
          "binary period | totient | sub-cycles (walked) | "
          "n/2 - totient/2 | prime |")
    print("|---|---|---|---|---|---|---|---|")
    for n in range(3, 31):
        measured = least_stream_period(Fraction(1, n), 4 * n)
        walked = sum(1 for k in range(1, n // 2 + 1) if closes_early(n, k))
        phi = totient(n)
        is_prime = n in primes_below(n + 1)
        print(f"| {n} | {measured} | {n} | {binary_period(n)} | {phi} | "
              f"{walked} | {n // 2 - phi // 2} | "
              f"{'yes' if is_prime else 'no'} |")
    print()


def main() -> None:
    coherence_table()
    sturmian_table()
    period_table()
    three_periods_table()


if __name__ == "__main__":
    main()
