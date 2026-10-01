"""``glm_universal.runtime.quantity_units`` -- units written in words, read
exactly into the coherent SI unit of a wheel quantity.

Why this module exists
----------------------
Round one of the stepwise planner (``studies/STEPWISE_PLANNER_STUDY.md``
§4.1) refused *given voltage = 12 volts …* rather than guess a unit.  Round
two (``studies/STEPWISE_TWO_STUDY.md``, Phase 73) reads the unit, and this
module is what it reads it with.  Three declared things, nothing inferred:

* **Magnitudes.**  :data:`NAMED_UNITS` spells out every unit read, each as a
  unit *symbol* and an exact factor into the coherent SI unit of its
  dimension.  The planner's own table of length, mass and time units
  (:data:`glm_universal.runtime.semantic_plan.UNITS`, each row a definition)
  is read as it stands; :data:`PREFIXES` are the exact SI prefixes.
* **Dimensions.**  Never written down here: the symbol of each unit is parsed
  by :func:`glm_universal.reasoning.units.dimension_of_symbol`, which derives
  ``V = W/A``, ``W = J/s`` … from the register's own definitions.  The
  dimension compared is the first seven axes (the SI projection): the SI
  policy, under which a radian and a steradian carry no dimension.
* **What is refused.**  A unit whose SI factor is not an exact rational
  (:data:`INEXACT_UNITS` -- the revolution and the degree of angle carry π,
  the dalton is a measured mass) and a unit with an offset
  (:data:`OFFSET_UNITS` -- degrees Celsius and Fahrenheit, whose conversion
  depends on whether the quantity is a level or a difference) are named and
  refused, never approximated.

Words are spelled out: a lower-cased symbol is ambiguous (``mw`` is a
milliwatt or a megawatt), so symbols are not read.  :data:`SCALE_TO_SI`
carries the canonical unit of each quantity of the Phase 55 scale table
(``reasoning.scale_conversion.CANONICAL``) into SI, so a register value can
feed a wheel.  Exact throughout: ``int`` and ``Fraction``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

__all__ = ["UnitRefused", "ReadUnit", "NAMED_UNITS", "PREFIXES",
           "INEXACT_UNITS", "OFFSET_UNITS", "SCALE_TO_SI", "read_unit",
           "quantity_dimension", "check_dimension", "scale_into_si",
           "SI_AXES", "WIDE_PREFIXES", "prefixes"]

#: The axes compared: the SI projection of the EXT10 basis.
SI_AXES: Tuple[str, ...] = ("L", "M", "T", "I", "H", "N", "J")


class UnitRefused(Exception):
    """A unit, a scale or a dimension declined, with a named reason."""

    def __init__(self, name: str, reason: str):
        super().__init__(f"{name}: {reason}")
        self.name = name
        self.reason = reason


_SI = "exact by the SI prefix definitions"
_COHERENT = "a coherent SI unit"

#: ``name -> (plural, symbol, factor into the coherent SI unit, source)``.
#: The symbol is parsed for the dimension; the factor is the magnitude.
NAMED_UNITS: Dict[str, Tuple[str, str, Fraction, str]] = {
    "metre": ("metres", "m", Fraction(1), _COHERENT),
    "meter": ("meters", "m", Fraction(1), _COHERENT),
    "gram": ("grams", "kg", Fraction(1, 1000), _SI),
    "second": ("seconds", "s", Fraction(1), _COHERENT),
    "ampere": ("amperes", "A", Fraction(1), _COHERENT),
    "amp": ("amps", "A", Fraction(1), _COHERENT),
    "kelvin": ("kelvins", "K", Fraction(1), _COHERENT),
    "mole": ("moles", "mol", Fraction(1), _COHERENT),
    "candela": ("candelas", "cd", Fraction(1), _COHERENT),
    "newton": ("newtons", "N", Fraction(1), _COHERENT),
    "joule": ("joules", "J", Fraction(1), _COHERENT),
    "watt": ("watts", "W", Fraction(1), _COHERENT),
    "pascal": ("pascals", "Pa", Fraction(1), _COHERENT),
    "volt": ("volts", "V", Fraction(1), _COHERENT),
    "ohm": ("ohms", "Ohm", Fraction(1), _COHERENT),
    "coulomb": ("coulombs", "C", Fraction(1), _COHERENT),
    "farad": ("farads", "F", Fraction(1), _COHERENT),
    "henry": ("henries", "H", Fraction(1), _COHERENT),
    "hertz": ("hertz", "Hz", Fraction(1), _COHERENT),
    "weber": ("webers", "Wb", Fraction(1), _COHERENT),
    "siemens": ("siemens", "S", Fraction(1), _COHERENT),
    "tesla": ("teslas", "T", Fraction(1), _COHERENT),
    "radian": ("radians", "rad", Fraction(1), _COHERENT),
    "litre": ("litres", "L", Fraction(1, 1000),
              "exact by definition: one cubic decimetre"),
    "electronvolt": ("electronvolts", "J", Fraction(1602176634, 10 ** 28),
                     "exact by the 2019 SI definition of the elementary "
                     "charge"),
}

#: The exact SI prefixes read in front of a named unit.
PREFIXES: Dict[str, int] = {
    "giga": 9, "mega": 6, "kilo": 3, "centi": -2, "milli": -3, "micro": -6,
    "nano": -9,
}

#: The exact SI prefixes round three of the stepwise planner adds (Phase 84,
#: ``studies/STEPWISE_THREE_STUDY.md``): tera and pico.  Read only while
#: :data:`WIDEN` is on; round three's control switches it off.
WIDE_PREFIXES: Dict[str, int] = {"tera": 12, "pico": -12}

#: Whether :data:`WIDE_PREFIXES` are read.
WIDEN = True


def prefixes() -> Dict[str, int]:
    """The prefixes read: :data:`PREFIXES`, and :data:`WIDE_PREFIXES` while
    :data:`WIDEN` is on."""
    return dict(PREFIXES, **WIDE_PREFIXES) if WIDEN else dict(PREFIXES)

#: Units named and refused ``UNIT_INEXACT``, with the reason.
INEXACT_UNITS: Dict[str, str] = {
    "revolution": "a revolution is 2π radians, and π is not a rational",
    "revolutions": "a revolution is 2π radians, and π is not a rational",
    "degree": "a degree of angle is π/180 radians, and π is not a rational",
    "degrees": "a degree of angle is π/180 radians, and π is not a rational",
    "dalton": "the dalton is a measured mass in kilograms, not a defined one",
    "daltons": "the dalton is a measured mass in kilograms, not a defined "
               "one",
}

#: Units named and refused ``OFFSET_UNIT``.
OFFSET_UNITS: Tuple[str, ...] = (
    "degree celsius", "degrees celsius", "celsius", "degree centigrade",
    "degrees centigrade", "degree fahrenheit", "degrees fahrenheit",
    "fahrenheit",
)

#: The canonical unit of each quantity of the Phase 55 scale table, carried
#: into SI: ``unit -> (SI symbol, exact factor, source)`` or ``None`` when no
#: exact factor exists (with the reason in :data:`_SCALE_INEXACT`).
SCALE_TO_SI: Dict[str, Optional[Tuple[str, Fraction, str]]] = {
    "K": ("K", Fraction(1), "the kelvin is the SI unit of temperature"),
    "pm": ("m", Fraction(1, 10 ** 12), _SI),
    "kJ/mol": ("J/mol", Fraction(1000), _SI),
    "u": None,
}

_SCALE_INEXACT: Dict[str, str] = {
    "u": "the unified atomic mass unit is a measured mass in kilograms, not "
         "a defined one, so no exact factor carries it into SI",
}


@dataclass(frozen=True)
class ReadUnit:
    """A unit phrase read: its words, its exact SI factor, its dimension over
    :data:`SI_AXES`, and the definitions the factor came from."""

    phrase: str
    factor: Fraction
    dimension: Tuple[Fraction, ...]
    sources: Tuple[str, ...]


def _planner_units():
    from .semantic_plan import UNITS
    return UNITS


def _symbol_dimension(symbol: str) -> Tuple[Fraction, ...]:
    from ..reasoning.units import dimension_of_symbol
    return tuple(dimension_of_symbol(symbol, steradian=False)[:7])


def _one_word(word: str) -> Tuple[Fraction, Tuple[Fraction, ...], str]:
    """``(factor, dimension, source)`` of one unit word, or refuse."""
    if word in INEXACT_UNITS:
        raise UnitRefused("UNIT_INEXACT", INEXACT_UNITS[word])
    from . import measurand_register as mreg
    special = mreg.special_unit(word)
    if special is not None:                       # Phase 87: e, percent
        factor, symbol, source = special
        dim = (_symbol_dimension(symbol) if symbol
               else tuple(Fraction(0) for _ in SI_AXES))
        return factor, dim, source
    for unit in _planner_units():
        if word in (unit.name, unit.plural):
            symbol = {"length": "m", "mass": "kg", "time": "s"}[unit.quantity]
            return unit.factor, _symbol_dimension(symbol), unit.source
    for name, (plural, symbol, factor, source) in NAMED_UNITS.items():
        if word in (name, plural):
            return factor, _symbol_dimension(symbol), source
    for prefix, power in prefixes().items():
        if not word.startswith(prefix) or len(word) <= len(prefix):
            continue
        rest = word[len(prefix):]
        if rest in ("hm", "hms"):                     # kilohm, megohm
            rest = "ohm"
        for name, (plural, symbol, factor, source) in NAMED_UNITS.items():
            if rest in (name, plural):
                return (factor * Fraction(10) ** power,
                        _symbol_dimension(symbol), _SI)
    raise UnitRefused("UNKNOWN_UNIT", f"{word!r} is not a unit the declared "
                                      f"table holds (units are spelled out; "
                                      f"symbols are not read)")


def read_unit(phrase: str) -> ReadUnit:
    """A unit phrase -- ``kilovolts``, ``metres per second``, ``square
    metres``, ``newton metres``, ``kilometres per hour`` -- read exactly, or
    :class:`UnitRefused`."""
    text = re.sub(r"\s+", " ", phrase.strip().lower())
    if not text:
        raise UnitRefused("UNKNOWN_UNIT", "no unit")
    if text in OFFSET_UNITS or re.search(r"\b(celsius|centigrade|"
                                          r"fahrenheit)\b", text):
        raise UnitRefused("OFFSET_UNIT",
                          f"{text!r} has an offset: whether the quantity is a "
                          f"level or a difference decides the conversion, "
                          f"and the wheel does not say which")
    factor = Fraction(1)
    dim = [Fraction(0)] * 7
    sources: List[str] = []
    from . import measurand_register as mreg
    for g, group in enumerate(mreg.fold_units(text).split(" per ")):
        sign = 1 if g == 0 else -1
        words = group.split()
        if not words:
            raise UnitRefused("UNKNOWN_UNIT", f"{text!r} does not read")
        pending = 1
        last: Optional[Tuple[Fraction, Tuple[Fraction, ...]]] = None
        for w in words:
            if w in ("square", "squared", "cubic", "cubed"):
                p = 2 if w.startswith("squ") else 3
                if w in ("square", "cubic"):
                    pending = p
                    continue
                if last is None:
                    raise UnitRefused("UNKNOWN_UNIT", f"{text!r} does not "
                                                      f"read")
                f0, d0 = last                         # squared / cubed
                factor *= f0 ** (sign * (p - 1))
                for i in range(7):
                    dim[i] += d0[i] * sign * (p - 1)
                continue
            f, d, src = _one_word(w)
            sources.append(src)
            factor *= f ** (sign * pending)
            for i in range(7):
                dim[i] += d[i] * sign * pending
            last = (f ** pending, tuple(x * pending for x in d))
            pending = 1
    return ReadUnit(text, factor, tuple(dim), tuple(dict.fromkeys(sources)))


def quantity_dimension(quantity: str) -> Tuple[Fraction, ...]:
    """The SI projection of a wheel quantity's dimension, from the formula
    study's reference registry."""
    from ..engineering.wheels import REFERENCE_DIMENSIONS
    from . import measurand_register as mreg
    if mreg.ACTIVE and mreg.law_named(quantity) is not None:
        return tuple(Fraction(0) for _ in SI_AXES)   # an efficiency
    return tuple(REFERENCE_DIMENSIONS[quantity][:7])


def _render_dim(d: Tuple[Fraction, ...]) -> str:
    parts = [f"{a}^{e}" if e != 1 else a for a, e in zip(SI_AXES, d) if e]
    return " ".join(parts) or "dimensionless"


def check_dimension(quantity: str, dimension: Tuple[Fraction, ...],
                    what: str) -> None:
    """Refuse ``UNIT_MISMATCH`` unless ``dimension`` is the quantity's."""
    want = quantity_dimension(quantity)
    if tuple(dimension) != want:
        raise UnitRefused("UNIT_MISMATCH",
                          f"{what} has dimension {_render_dim(dimension)}, "
                          f"and {quantity.replace('_', ' ')} has "
                          f"{_render_dim(want)}")


def scale_into_si(scale: str) -> Tuple[Fraction, Tuple[Fraction, ...], str]:
    """``(factor, dimension, quantity)`` carrying a register scale (a
    ``table:field`` of the Phase 55 table) into SI, or refuse."""
    from ..reasoning.scale_conversion import declared
    row = declared(scale)
    if row is None:
        raise UnitRefused("SCALE_UNDECLARED",
                          f"{scale} is on no declared scale, so nothing says "
                          f"what it measures or in which unit")
    if row.offset != 0:                               # pragma: no cover
        raise UnitRefused("OFFSET_UNIT", f"{scale} has an offset")
    si = SCALE_TO_SI.get(row.unit)
    if si is None:
        raise UnitRefused("UNIT_INEXACT", _SCALE_INEXACT.get(
            row.unit, f"no exact factor carries {row.unit} into SI"))
    symbol, factor, _src = si
    from ..reasoning.units import parse_unit
    dim = tuple(parse_unit(symbol, steradian=False)[:7])
    return row.factor * factor, dim, row.quantity
