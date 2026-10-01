"""Exact rational intervals, and the declared standard atomic weights.

A closed interval ``[lo, hi]`` of ``Fraction`` bounds, the reading of a held
decimal at the precision it was written to (:meth:`Interval.as_held`), and the
ordering that refuses when two intervals overlap (:func:`compare_intervals`).
Item E1 of ``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md``: measured as X6
in :mod:`glm_universal.reasoning.substrate_cognition` and reached by a
question through the interval frames of
:mod:`glm_universal.runtime.semantic_plan` (Y1).

Kept in a module of its own, with no import beyond the standard library, so
that the planner on the answering path can use it without reading the
experiments module and everything it measures.  The overlap refusal is
proved in ``RequestProject/GLM/CognitionRoundTwo.lean``
(``closed_overlap_iff``).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Optional, Tuple

__all__ = ["Interval", "compare_intervals", "IUPAC_WEIGHTS", "standard_interval"]


class Interval:
    """A closed exact interval ``[lo, hi]`` with the source it came from."""

    __slots__ = ("lo", "hi", "source")

    def __init__(self, lo: Fraction, hi: Fraction, source: str = "") -> None:
        if not (isinstance(lo, Fraction) and isinstance(hi, Fraction)):
            raise TypeError("Interval: bounds must be Fractions")
        if lo > hi:
            raise ValueError("Interval: lo > hi")
        self.lo, self.hi, self.source = lo, hi, source

    @classmethod
    def plus_minus(cls, value: str, uncertainty: str,
                   source: str = "") -> "Interval":
        v, u = Fraction(value), Fraction(uncertainty)
        return cls(v - u, v + u, source)

    @classmethod
    def as_held(cls, value: Fraction, source: str = "") -> "Interval":
        """A held decimal read at its stated precision: half a unit either side.

        The register keeps each decimal as an exact ``Fraction``, so the
        number of places it was quoted to is the least ``p`` with
        ``10**p`` divisible by the denominator. A trailing zero cannot be
        recovered, so this is the *widest* reading of the held value. A
        denominator with a prime factor other than 2 and 5 is not a decimal,
        and it is read as the exact point.
        """
        den = value.denominator
        places = 0
        while (10 ** places) % den and places <= 40:
            places += 1
        if (10 ** places) % den:
            return cls(value, value, source)
        half = Fraction(1, 2 * 10 ** places)
        return cls(value - half, value + half, source)

    def contains(self, x: Fraction) -> bool:
        return self.lo <= x <= self.hi

    def overlaps(self, other: "Interval") -> bool:
        return self.lo <= other.hi and other.lo <= self.hi

    def __repr__(self) -> str:
        return f"Interval({self.lo}, {self.hi})"


def compare_intervals(a: Interval, b: Interval) -> str:
    """``lt``, ``gt``, ``eq`` (both the same single point) or ``overlap``.

    ``overlap`` is a refusal: some values the two intervals allow are ordered
    one way and some the other (``GLM.SubstrateCognition.interval_overlap_undecided``).
    """
    if a.hi < b.lo:
        return "lt"
    if b.hi < a.lo:
        return "gt"
    if a.lo == a.hi == b.lo == b.hi:
        return "eq"
    return "overlap"


#: Standard atomic weights, transcribed by hand from the IUPAC/CIAAW table
#: (2021 values): ``("interval", lo, hi)`` for the elements the table gives
#: as an interval, ``("pm", value, uncertainty)`` for the others.  They are
#: transcribed rather than fetched, so they are a declared input to this
#: experiment and should be checked against ciaaw.org before anything else
#: relies on them.
IUPAC_WEIGHTS: Tuple[Tuple[str, str, str, str], ...] = (
    ("H", "interval", "1.00784", "1.00811"),
    ("He", "pm", "4.002602", "0.000002"),
    ("Li", "interval", "6.938", "6.997"),
    ("Be", "pm", "9.0121831", "0.0000005"),
    ("B", "interval", "10.806", "10.821"),
    ("C", "interval", "12.0096", "12.0116"),
    ("N", "interval", "14.00643", "14.00728"),
    ("O", "interval", "15.99903", "15.99977"),
    ("F", "pm", "18.998403162", "0.000000005"),
    ("Ne", "pm", "20.1797", "0.0006"),
    ("Na", "pm", "22.98976928", "0.00000002"),
    ("Mg", "interval", "24.304", "24.307"),
    ("Al", "pm", "26.9815384", "0.0000003"),
    ("Si", "interval", "28.084", "28.086"),
    ("P", "pm", "30.973761998", "0.000000005"),
    ("S", "interval", "32.059", "32.076"),
    ("Cl", "interval", "35.446", "35.457"),
    ("Ar", "interval", "39.792", "39.963"),
    ("K", "pm", "39.0983", "0.0001"),
    ("Ca", "pm", "40.078", "0.004"),
    ("Ti", "pm", "47.867", "0.001"),
    ("V", "pm", "50.9415", "0.0001"),
    ("Cr", "pm", "51.9961", "0.0006"),
    ("Fe", "pm", "55.845", "0.002"),
    ("Co", "pm", "58.933194", "0.000003"),
    ("Ni", "pm", "58.6934", "0.0004"),
    ("Cu", "pm", "63.546", "0.003"),
    ("Zn", "pm", "65.38", "0.02"),
    ("Br", "interval", "79.901", "79.907"),
    ("Tl", "interval", "204.382", "204.385"),
)

def standard_interval(row: Tuple[str, str, str, str]) -> Tuple[Interval, Optional[Fraction]]:
    symbol, kind, x, y = row
    if kind == "interval":
        return Interval(Fraction(x), Fraction(y), "IUPAC"), None
    return Interval.plus_minus(x, y, "IUPAC"), Fraction(x)
