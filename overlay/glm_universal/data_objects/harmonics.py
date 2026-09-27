"""Musical intervals as exact rational frequency ratios.

Why a harmonic register
-----------------------
The supplied study catalogue claims that chemical equilibria, musical harmony
and market price discovery all map to proximity in the Leech lattice.
``reasoning/catalog.py`` has recorded that claim as *not implemented* for
several rounds, for a plain reason: there was no musical register to test it
against, and a claim nothing can be run against is not a finding.  This module
supplies the cheapest third of it.  An interval is an exact ratio of two
positive integers -- ``3/2``, ``5/4``, ``81/80`` -- so a musical register needs
no measurement, no calibration and no float: it is arithmetic, and every
coordinate below is computed from the ratio rather than stored beside it.

What a coordinate means
-----------------------
The 24 coordinates of :data:`HARMONIC_LAYOUT` are all derived from the pair
``(n, d)`` in lowest terms, and only ``n`` and ``d`` are needed to recover the
interval, which is what makes the codec's round trip exact.  Three of them are
worth naming here.

``tet_step``
    The 12-tone-equal-tempered step the interval is nearest to, decided
    **exactly**: ``k`` is nearest to ``12 log2 (n/d)`` exactly when
    ``(n/d)^24 < 2^(2k+1)`` and ``(n/d)^24 > 2^(2k-1)``, and those are
    comparisons of integers.  No logarithm is evaluated and no float exists.
``tet_error``
    How far equal temperament misses, as the exact rational
    ``(n/d)^12 / 2^k``.  It is ``1`` exactly when the interval *is* an equal
    step -- which, for every interval here other than the unison and the
    octave, it never is (see ``RequestProject/GLM/Harmony.lean``).
``euler_gradus``
    Euler's *gradus suavitatis*: ``1 + sum over primes p^e || n*d of
    e * (p - 1)``.  An integer measure of how hard an interval is to hear as
    simple, and the classical rival of ``product_complexity = n * d`` (Tenney
    height without the logarithm).  Whether either of them agrees with
    proximity in the substrate is measured in
    :mod:`glm_universal.reasoning.harmony`, not assumed here.

Exactness
---------
Every value is an ``int`` or a :class:`fractions.Fraction`.  Nothing is
rounded, nothing is sampled, and no cent value is ever computed -- a cent is a
logarithm, and where the rest of this package would need one it compares
integers instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Mapping, Sequence, Tuple

from .base import Codec, DataObject, as_exact

__all__ = [
    "HARMONIC_LAYOUT",
    "Interval",
    "IntervalCodec",
    "COMMAS",
    "JUST_INTERVALS",
    "SEPTIMAL_INTERVALS",
    "euler_gradus",
    "harmonic_objects",
    "interval_by_name",
    "interval_register",
    "prime_exponents",
    "product_complexity",
    "tet_error",
    "tet_step",
]

#: What each of the 24 coordinates of an interval carrier holds.
HARMONIC_LAYOUT: Tuple[str, ...] = (
    "numerator",            # 0  n, in lowest terms
    "denominator",          # 1  d, in lowest terms
    "exponent_2",           # 2  the exponent of 2 in n/d
    "exponent_3",           # 3  the exponent of 3
    "exponent_5",           # 4  the exponent of 5
    "exponent_7",           # 5  the exponent of 7
    "prime_limit",          # 6  the largest prime dividing n*d
    "odd_limit",            # 7  the largest odd part of n and d
    "product_complexity",   # 8  n * d (Tenney height, unlogged)
    "euler_gradus",         # 9  Euler's gradus suavitatis
    "tet_step",             # 10 nearest 12-TET step, decided exactly
    "tet_error",            # 11 (n/d)^12 / 2^step, exactly 1 iff tempered
    "tet_sharper",          # 12 +1 sharp of the tempered step, -1 flat, 0 equal
    "superparticular",      # 13 1 when n = d + 1
    "within_octave",        # 14 1 when 1 <= n/d < 2
    "distinct_primes",      # 15 how many primes divide n * d
    "numerator_odd_part",   # 16 n with its factors of 2 removed
    "denominator_odd_part",  # 17 d with its factors of 2 removed
    "harmonic_index",       # 18 n when d is a power of two, else 0
    "subharmonic_index",    # 19 d when n is a power of two, else 0
    "exponent_weight",      # 20 sum of |exponents| over 2, 3, 5, 7
    "largest_exponent",     # 21 max |exponent| over 2, 3, 5, 7
    "diatonic_degree",      # 22 1..8 for a degree of the 5-limit major scale
    "is_comma",             # 23 1 when the ratio is within a semitone of 1
)

_PRIMES: Tuple[int, ...] = (2, 3, 5, 7)


# ===========================================================================
# 1.  ARITHMETIC ON A RATIO
# ===========================================================================

def _valuation(value: int, prime: int) -> int:
    """The exponent of ``prime`` in ``value``."""
    count = 0
    while value % prime == 0:
        value //= prime
        count += 1
    return count


def prime_exponents(ratio: Fraction) -> Dict[int, int]:
    """The exponent of each prime in a positive rational.

    Returned for every prime dividing numerator or denominator, not only the
    four the layout names, so a caller can see when an interval leaves the
    7-limit.
    """
    if ratio <= 0:
        raise ValueError("prime_exponents: the ratio must be positive")
    out: Dict[int, int] = {}
    for value, sign in ((ratio.numerator, 1), (ratio.denominator, -1)):
        remainder = value
        factor = 2
        while factor * factor <= remainder:
            if remainder % factor == 0:
                exponent = 0
                while remainder % factor == 0:
                    remainder //= factor
                    exponent += 1
                out[factor] = out.get(factor, 0) + sign * exponent
            factor += 1 if factor == 2 else 2
        if remainder > 1:
            out[remainder] = out.get(remainder, 0) + sign
    return {p: e for p, e in sorted(out.items()) if e != 0}


def product_complexity(ratio: Fraction) -> int:
    """``n * d`` -- Tenney height before anyone takes a logarithm."""
    return ratio.numerator * ratio.denominator


def euler_gradus(ratio: Fraction) -> int:
    """Euler's *gradus suavitatis* of a ratio.

    ``1 + sum e_p * (p - 1)`` over the primes of ``n * d``.  The unison is 1,
    the octave 2, the fifth 4, the major third 7.
    """
    total = 1
    for prime, exponent in prime_exponents(ratio).items():
        total += abs(exponent) * (prime - 1)
    return total


def tet_step(ratio: Fraction) -> int:
    """The nearest 12-tone equal-tempered step, decided by integer comparison.

    ``k`` is nearest to ``12 log2 r`` exactly when
    ``2^(2k-1) <= r^24 <= 2^(2k+1)``; both sides are integers once the ratio is
    cleared, so the decision is exact and no logarithm is evaluated.  A tie --
    ``r^24`` exactly a half-power -- rounds up, and is unreachable for a ratio
    of integers other than a power of two.
    """
    if ratio <= 0:
        raise ValueError("tet_step: the ratio must be positive")
    power = ratio ** 24
    two = Fraction(2)
    k = 0
    while power >= two ** (2 * k + 1):
        k += 1
    while power < two ** (2 * k - 1):
        k -= 1
    return k


def tet_error(ratio: Fraction) -> Fraction:
    """``(n/d)^12 / 2^k`` -- exactly 1 when the interval is an equal step."""
    return (ratio ** 12) / Fraction(2) ** tet_step(ratio)


# ===========================================================================
# 2.  THE INTERVAL
# ===========================================================================

@dataclass(frozen=True)
class Interval:
    """A named interval, held as an exact frequency ratio."""

    name: str
    ratio: Fraction
    #: ``1``..``8`` for a degree of the 5-limit major scale, ``0`` otherwise.
    degree: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "ratio", Fraction(as_exact(self.ratio)))
        if self.ratio <= 0:
            raise ValueError(f"Interval {self.name}: ratio must be positive")

    # -- derived quantities -------------------------------------------------

    @property
    def exponents(self) -> Dict[int, int]:
        return prime_exponents(self.ratio)

    @property
    def prime_limit(self) -> int:
        exponents = self.exponents
        return max(exponents) if exponents else 1

    @property
    def odd_limit(self) -> int:
        """The larger of the odd parts of numerator and denominator."""
        return max(_odd_part(self.ratio.numerator),
                   _odd_part(self.ratio.denominator))

    @property
    def is_superparticular(self) -> bool:
        return self.ratio.numerator == self.ratio.denominator + 1

    @property
    def within_octave(self) -> bool:
        return Fraction(1) <= self.ratio < Fraction(2)

    @property
    def is_comma(self) -> bool:
        """Within a tempered semitone of the unison, either side."""
        return tet_step(self.ratio) == 0 and self.ratio != 1

    def carrier(self) -> Tuple[object, ...]:
        """The 24 coordinates of :data:`HARMONIC_LAYOUT`."""
        ratio = self.ratio
        exponents = self.exponents
        step = tet_step(ratio)
        error = tet_error(ratio)
        listed = [exponents.get(p, 0) for p in _PRIMES]
        return (
            ratio.numerator,
            ratio.denominator,
            listed[0], listed[1], listed[2], listed[3],
            self.prime_limit,
            self.odd_limit,
            product_complexity(ratio),
            euler_gradus(ratio),
            step,
            error,
            1 if error > 1 else (-1 if error < 1 else 0),
            1 if self.is_superparticular else 0,
            1 if self.within_octave else 0,
            len(exponents),
            _odd_part(ratio.numerator),
            _odd_part(ratio.denominator),
            ratio.numerator if _is_power_of_two(ratio.denominator) else 0,
            ratio.denominator if _is_power_of_two(ratio.numerator) else 0,
            sum(abs(e) for e in exponents.values()),
            max((abs(e) for e in exponents.values()), default=0),
            self.degree,
            1 if self.is_comma else 0,
        )

    def as_object(self) -> DataObject:
        """This interval as a register carrier."""
        return DataObject(
            name=self.name,
            domain="harmonics",
            carrier=self.carrier(),
            attributes={
                "ratio": self.ratio,
                "numerator": self.ratio.numerator,
                "denominator": self.ratio.denominator,
                "degree": self.degree,
                "prime_limit": self.prime_limit,
                "euler_gradus": euler_gradus(self.ratio),
                "product_complexity": product_complexity(self.ratio),
                "tet_step": tet_step(self.ratio),
                "tet_error": tet_error(self.ratio),
            },
            layout=HARMONIC_LAYOUT,
            provenance={
                "source": "exact frequency ratio",
                "derivation": "every coordinate computed from n and d",
            },
        )


def _odd_part(value: int) -> int:
    while value % 2 == 0 and value > 0:
        value //= 2
    return value


def _is_power_of_two(value: int) -> bool:
    return value > 0 and value & (value - 1) == 0


# ===========================================================================
# 3.  THE CODEC
# ===========================================================================

class IntervalCodec(Codec):
    """Encode an interval to its carrier and read it back.

    The read-back uses coordinates 0 and 1 alone: everything else is derived,
    so the round trip cannot disagree with the derivation.
    """

    layout = HARMONIC_LAYOUT

    def encode(self, value: Interval) -> Tuple[object, ...]:
        return value.carrier()

    def decode(self, carrier: Sequence[object],
               name: str = "interval") -> Interval:
        numerator = int(Fraction(carrier[0]))
        denominator = int(Fraction(carrier[1]))
        degree = int(Fraction(carrier[22]))
        return Interval(name=name,
                        ratio=Fraction(numerator, denominator),
                        degree=degree)


# ===========================================================================
# 4.  THE REGISTER
# ===========================================================================

#: The 5-limit just scale, plus the intervals a 5-limit account needs.
JUST_INTERVALS: Tuple[Interval, ...] = (
    Interval("unison", Fraction(1, 1), degree=1),
    Interval("minor_second", Fraction(16, 15)),
    Interval("major_second", Fraction(9, 8), degree=2),
    Interval("minor_second_greater", Fraction(27, 25)),
    Interval("minor_third", Fraction(6, 5)),
    Interval("major_third", Fraction(5, 4), degree=3),
    Interval("perfect_fourth", Fraction(4, 3), degree=4),
    Interval("tritone", Fraction(45, 32)),
    Interval("perfect_fifth", Fraction(3, 2), degree=5),
    Interval("minor_sixth", Fraction(8, 5)),
    Interval("major_sixth", Fraction(5, 3), degree=6),
    Interval("minor_seventh", Fraction(16, 9)),
    Interval("major_seventh", Fraction(15, 8), degree=7),
    Interval("octave", Fraction(2, 1), degree=8),
    Interval("pythagorean_third", Fraction(81, 64)),
    Interval("pythagorean_sixth", Fraction(27, 16)),
    Interval("pythagorean_seventh", Fraction(243, 128)),
    Interval("whole_tone_minor", Fraction(10, 9)),
)

#: The 7-limit intervals, where the harmonic series and the keyboard part.
SEPTIMAL_INTERVALS: Tuple[Interval, ...] = (
    Interval("harmonic_seventh", Fraction(7, 4)),
    Interval("septimal_third", Fraction(9, 7)),
    Interval("septimal_minor_third", Fraction(7, 6)),
    Interval("septimal_tritone", Fraction(7, 5)),
    Interval("septimal_whole_tone", Fraction(8, 7)),
)

#: The intervals that measure how far two tunings disagree.
COMMAS: Tuple[Interval, ...] = (
    Interval("syntonic_comma", Fraction(81, 80)),
    Interval("pythagorean_comma", Fraction(531441, 524288)),
    Interval("septimal_comma", Fraction(64, 63)),
    Interval("diesis", Fraction(128, 125)),
    Interval("schisma", Fraction(32805, 32768)),
)


def interval_register() -> Tuple[Interval, ...]:
    """Every interval of the register, in a fixed order."""
    return JUST_INTERVALS + SEPTIMAL_INTERVALS + COMMAS


def interval_by_name(name: str) -> Interval:
    """One interval, by name."""
    for interval in interval_register():
        if interval.name == name:
            return interval
    raise KeyError(f"no such interval: {name}")


def harmonic_objects() -> Tuple[DataObject, ...]:
    """The harmonic register as carriers."""
    return tuple(interval.as_object() for interval in interval_register())


def register_summary() -> Mapping[str, object]:
    """What the register holds, for a report to quote."""
    intervals = interval_register()
    return {
        "count": len(intervals),
        "just": len(JUST_INTERVALS),
        "septimal": len(SEPTIMAL_INTERVALS),
        "commas": len(COMMAS),
        "prime_limits": tuple(sorted({i.prime_limit for i in intervals})),
        "superparticular": tuple(i.name for i in intervals
                                 if i.is_superparticular),
    }
