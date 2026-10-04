"""The ITS-90 fixed-point register: the first register holding a reading in
degrees Celsius.

The register
------------
The International Temperature Scale of 1990 (H. Preston-Thomas, *Metrologia*
27 (1990) 3, Table 1) assigns a temperature to seventeen defining fixed
points.  Fourteen of them are *points* -- a triple, melting or freezing point
of one pure substance -- and these are the register's fourteen rows.  The
other three (the helium vapour-pressure range and the two vapour-pressure
points of equilibrium hydrogen) are defined through a vapour-pressure
relation and are not held.

ITS-90 states each assigned value twice, as ``T90 / K`` and as
``t90 / degree Celsius``, related by the exact ``t90 = T90 - 273.15``.  **This
register holds the Celsius column only**, under the field name
``temperature_C``.  The kelvin value is not stored: it is what the declared
scale table's offset row (:mod:`glm_universal.reasoning.scale_conversion`,
``fixed_point:temperature_C``, factor ``1``, offset ``273.15``) derives, and
``studies/CELSIUS_REGISTER_STUDY.md`` mark C1 checks that derivation against
the kelvin column the same table states.

Every reading is held as an exact :class:`fractions.Fraction` parsed from the
decimal string ITS-90 prints, so ``0.01`` is ``1/100`` and nothing is a
binary float.

Why a separate register rather than a column of the element register
---------------------------------------------------------------------
A fixed point is a state of a substance (a triple point is not a melting
point at one atmosphere), its value is assigned rather than measured, and
water -- the scale's own anchor -- is not an element.  So the rows are keyed
by the point (``"zinc freezing point"``), not by the substance, and no row
carries a ``name`` or ``symbol`` that would make it answer to ``zinc``: the
element register keeps the element, and this register keeps the point.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Dict, Mapping, Tuple

__all__ = ["ACTIVE", "FixedPoint", "FIXED_POINTS", "SOURCE",
           "load_fixed_point_register", "fixed_point_rows"]

#: Whether the field surface holds the register (off: the machine before
#: Phase 99, for the study's control; read when a surface builds its tables).
ACTIVE = True

#: Where every number of the register was written down.
SOURCE = ("ITS-90: H. Preston-Thomas, 'The International Temperature Scale "
          "of 1990 (ITS-90)', Metrologia 27 (1990) 3-10, Table 1 (defining "
          "fixed points), column t90 / degree Celsius")


@dataclass(frozen=True)
class FixedPoint:
    """One defining fixed point of ITS-90, as the register holds it."""

    key: str              # 'zinc freezing point'
    substance: str        # 'Zn' -- the substance, by formula
    state: str            # 'triple point' / 'melting point' / 'freezing point'
    temperature_C: Fraction   # t90, in degrees Celsius, exact

    def fields(self) -> Mapping[str, object]:
        """The row as the field surface addresses it."""
        return {"fixed_point": self.key, "substance": self.substance,
                "state": self.state, "temperature_C": self.temperature_C}


def _row(key: str, substance: str, state: str, t90: str) -> FixedPoint:
    return FixedPoint(key, substance, state, Fraction(t90))


#: **The register.**  Fourteen rows, in ITS-90's order (increasing
#: temperature), each t90 copied from Table 1 as printed.
FIXED_POINTS: Tuple[FixedPoint, ...] = (
    _row("hydrogen triple point", "e-H2", "triple point", "-259.3467"),
    _row("neon triple point", "Ne", "triple point", "-248.5939"),
    _row("oxygen triple point", "O2", "triple point", "-218.7916"),
    _row("argon triple point", "Ar", "triple point", "-189.3442"),
    _row("mercury triple point", "Hg", "triple point", "-38.8344"),
    _row("water triple point", "H2O", "triple point", "0.01"),
    _row("gallium melting point", "Ga", "melting point", "29.7646"),
    _row("indium freezing point", "In", "freezing point", "156.5985"),
    _row("tin freezing point", "Sn", "freezing point", "231.928"),
    _row("zinc freezing point", "Zn", "freezing point", "419.527"),
    _row("aluminium freezing point", "Al", "freezing point", "660.323"),
    _row("silver freezing point", "Ag", "freezing point", "961.78"),
    _row("gold freezing point", "Au", "freezing point", "1064.18"),
    _row("copper freezing point", "Cu", "freezing point", "1084.62"),
)


@lru_cache(maxsize=1)
def load_fixed_point_register() -> Tuple[FixedPoint, ...]:
    """The fourteen rows."""
    return FIXED_POINTS


def fixed_point_rows() -> Dict[str, Mapping[str, object]]:
    """Row key -> fields, for :mod:`glm_universal.runtime.fields`."""
    return {row.key: dict(row.fields()) for row in load_fixed_point_register()}
