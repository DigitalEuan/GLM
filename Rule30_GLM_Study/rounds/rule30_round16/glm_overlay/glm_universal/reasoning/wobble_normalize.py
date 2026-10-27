"""``glm_universal.reasoning.wobble_normalize`` -- the normalisation operator for wobble carriers
(Rule 30 study, Round 16).

A raw wobble accumulator ``D(N) = #ones - #zeros`` cannot be compared across different sample
sizes: over all ``2^N`` words of length ``N`` its mean square is exactly ``N``
(Lean: ``sum_wordWobble_sq``, ``RequestProject/GLM/Rule30/WobbleNormalized.lean``).  The
normalised carrier ``z(N) = D(N) / sqrt(N)`` has mean square exactly ``1`` for every ``N``
(``mean_sq_zScore``), so readings at different ``N`` live on one scale.  At most a fraction
``1 / lam^2`` of words have ``|z| >= lam`` (``card_large_zScore_le``).

Everything is exact: ``z`` is carried as its sign and its square ``z^2 = D^2 / N``, a
``Fraction``; a float is produced only on request for display.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import sqrt
from typing import Iterable, List, Sequence

__all__ = ["wobble", "ZReading", "normalise", "carrier", "chebyshev_fraction", "compare",
           "check_fair_coin_moments"]


def wobble(bits: Iterable[int]) -> int:
    """``D(N)``: number of ones minus number of zeros."""
    return sum(1 if b else -1 for b in bits)


@dataclass(frozen=True)
class ZReading:
    """A normalised wobble reading: ``z = sign * sqrt(z2)`` with ``z2 = D^2 / N`` exact."""
    N: int
    D: int
    z2: Fraction

    @property
    def sign(self) -> int:
        return (self.D > 0) - (self.D < 0)

    def at_least(self, lam: Fraction) -> bool:
        """``|z| >= lam``, decided exactly (``lam >= 0``)."""
        return self.z2 >= Fraction(lam) ** 2

    def as_float(self) -> float:
        return self.sign * sqrt(self.z2)

    def __str__(self) -> str:
        return f"N={self.N} D={self.D} z={self.as_float():+.3f} (z^2 = {self.z2})"


def normalise(D: int, N: int) -> ZReading:
    """The normalisation operator ``D(N) -> D(N)/sqrt(N)`` (``N >= 1``)."""
    if N < 1:
        raise ValueError("N must be at least 1")
    return ZReading(N, D, Fraction(D * D, N))


def carrier(bits: Sequence[int], checkpoints: Sequence[int]) -> List[ZReading]:
    """Normalised readings of a bit sequence at the given prefix lengths."""
    out, d, k = [], 0, 0
    marks = sorted(set(checkpoints))
    for i, b in enumerate(bits, start=1):
        d += 1 if b else -1
        while k < len(marks) and marks[k] == i:
            out.append(normalise(d, i))
            k += 1
    return out


def chebyshev_fraction(lam: Fraction) -> Fraction:
    """Upper bound on the fraction of words of any length with ``|z| >= lam`` (``lam > 0``)."""
    return min(Fraction(1), 1 / Fraction(lam) ** 2)


def compare(a: ZReading, b: ZReading) -> int:
    """Compare two readings by ``|z|`` (scale-free); ``-1``, ``0`` or ``1``."""
    return (a.z2 > b.z2) - (a.z2 < b.z2)


def check_fair_coin_moments(N: int) -> bool:
    """Brute-force check of the Lean identities for one small ``N``:
    ``sum D = 0`` and ``sum D^2 = N * 2^N`` over all ``2^N`` words."""
    s1 = s2 = 0
    for w in product((0, 1), repeat=N):
        d = wobble(w)
        s1 += d
        s2 += d * d
    return s1 == 0 and s2 == N * 2 ** N
