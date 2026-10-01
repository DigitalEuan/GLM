"""``glm_universal.runtime.measurands`` -- kinds of quantity, declared.

Why this module exists
----------------------
The stepwise planner checks a unit by its **dimension** over the seven SI
axes (:mod:`glm_universal.runtime.quantity_units`).  Dimension is necessary
and not sufficient: quantities of different *kinds* share a dimension.  The
International Vocabulary of Metrology (VIM 1.2) and ISO/IEC 80000 call a
class of mutually comparable quantities a **kind of quantity**, and the SI
Brochure (9th edition, 2019, §2.3.4 and Table 4) restricts some special unit
names to one kind: the hertz is used only for periodic phenomena, never for
angular velocity (which is in radians per second, and ``omega = 2 pi f``
carries a π); the joule is not used for torque, which is written in newton
metres.  A reader that checks only dimensions answers *angular velocity = 50
hertz* as 50 rad/s, which is wrong by 2π.  ``studies/MEASURANDS_STUDY.md``
(Phase 86) declares the kinds this module holds.

Four declarations, nothing inferred:

* :data:`UNIT_FORBIDS` -- a unit phrase that names a special unit, and the
  wheel quantities of the same dimension it may not measure, with the SI
  Brochure's reason.  Refused ``KIND_MISMATCH``.
* **Temperature as a level or a difference** (ISO 80000-5: thermodynamic
  temperature ``T`` against a temperature difference ``ΔT``; the Celsius
  temperature ``t = T - 273.15 K`` is a level, and an *interval* of one
  degree Celsius is one kelvin).  :data:`SLOT_KINDS` says which wheel axiom
  reads its ``temperature`` as which: ``energy = mass *
  specific_heat_capacity * temperature`` reads a difference, ``entropy =
  energy / temperature`` a level.  :data:`DIFFERENCE_NAMES` are the names a
  question gives a difference by.  A given's kind comes from its source: a
  register temperature (a melting or boiling point) or a temperature written
  in degrees Celsius or Fahrenheit is a level; a name in
  :data:`DIFFERENCE_NAMES` is a difference; a bare number or kelvins on
  ``temperature`` is neutral (the kelvin is the unit of both).  A level read
  as a difference is ``LEVEL_AS_DIFFERENCE``, a difference read as a level
  ``DIFFERENCE_AS_LEVEL``, a neutral temperature read as both
  ``KIND_CONFLATION``; a level below 0 K is ``BELOW_ABSOLUTE_ZERO``.
* :data:`OFFSET_READINGS` -- the exact affine map of degrees Celsius and
  Fahrenheit into kelvins, for a level and for a difference.
* :data:`DEFINED_CONSTANTS` -- the wheel quantities that are defining
  constants of the SI since 2019 (``h`` and ``c``), with their exact values.
  The goal planner supplies them only when the givens alone derive nothing.

:data:`ACTIVE` switches all four off (the control of the study).  Exact
throughout: ``int`` and ``Fraction``.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, FrozenSet, Optional, Tuple

__all__ = ["ACTIVE", "UNIT_FORBIDS", "SLOT_KINDS", "DIFFERENCE_NAMES",
           "OFFSET_READINGS", "DEFINED_CONSTANTS", "TEMPERATURE",
           "unit_forbids", "offset_reading", "difference_name",
           "scale_kind", "slot_kind", "constant_value"]

#: Whether the kinds are read at all (off: the dimension check alone, as
#: rounds two to four had it).
ACTIVE = True

#: The one wheel quantity whose slots differ in kind.
TEMPERATURE = "temperature"

_BROCHURE = "the SI Brochure (9th edition, 2019), section 2.3.4 and Table 4"

#: ``unit pattern -> (quantities it may not measure, reason)``.  The pattern
#: is matched against the unit phrase with SI prefixes stripped from each
#: word; only a phrase that is exactly the special unit carries the
#: restriction (``joules per second`` does not).
UNIT_FORBIDS: Dict[str, Tuple[FrozenSet[str], str]] = {
    "hertz": (frozenset({"angular_velocity"}),
              "the hertz is used only for periodic phenomena; an angular "
              "velocity is in radians per second, and omega = 2 pi f carries "
              "a pi, so no exact factor carries hertz into it (" + _BROCHURE
              + ")"),
    "radian per second": (frozenset({"frequency"}),
                          "the radian per second is the unit of angular "
                          "velocity; a frequency is in hertz, and f = omega "
                          "/ (2 pi) carries a pi (" + _BROCHURE + ")"),
    "joule": (frozenset({"torque"}),
              "a torque (moment of force) is written in newton metres, never "
              "in joules: it is not an energy although it shares the "
              "dimension (" + _BROCHURE + ")"),
    "electronvolt": (frozenset({"torque"}),
                     "the electronvolt is an energy, and a torque is not an "
                     "energy although it shares the dimension (" + _BROCHURE
                     + ")"),
    "newton metre": (frozenset({"energy"}),
                     "the newton metre is the unit of torque (moment of "
                     "force); an energy is written in joules (" + _BROCHURE
                     + ")"),
}

_PREFIXES = ("tera", "giga", "mega", "kilo", "centi", "milli", "micro",
             "nano", "pico")
_SINGULAR = {"hertz": "hertz", "joules": "joule", "electronvolts":
             "electronvolt", "newtons": "newton", "metres": "metre",
             "meters": "metre", "meter": "metre", "radians": "radian",
             "seconds": "second"}


def _base_word(word: str) -> str:
    for p in _PREFIXES:
        if word.startswith(p) and len(word) > len(p) and \
                _SINGULAR.get(word[len(p):], word[len(p):]) in (
                    "hertz", "joule", "electronvolt", "newton", "metre"):
            word = word[len(p):]
            break
    return _SINGULAR.get(word, word)


def unit_forbids(phrase: str) -> Optional[Tuple[str, FrozenSet[str], str]]:
    """``(special unit, forbidden quantities, reason)`` when the unit phrase
    is exactly a restricted special unit, else ``None``."""
    words = re.sub(r"\s+", " ", phrase.strip().lower()).split(" ")
    norm = " ".join(_base_word(w) for w in words)
    if norm in UNIT_FORBIDS:
        forbidden, why = UNIT_FORBIDS[norm]
        return norm, forbidden, why
    return None


#: ``(wheel axiom, base name) -> "level" | "difference"``: which axioms read
#: a temperature as a thermodynamic temperature and which as a difference.
SLOT_KINDS: Dict[Tuple[str, str], str] = {
    ("energy = mass * specific_heat_capacity * temperature", TEMPERATURE):
        "difference",
    ("entropy = energy / temperature", TEMPERATURE): "level",
}

#: The names a question gives a temperature difference by, each read as the
#: wheel quantity ``temperature`` of kind difference.
DIFFERENCE_NAMES: Tuple[str, ...] = (
    "temperature_change", "temperature_difference", "temperature_rise",
    "temperature_increase", "temperature_drop", "change_in_temperature",
)

#: ``unit word -> {"level": (factor, offset), "difference": (factor, 0)}``
#: carrying degrees into kelvins: ``T = factor * t + offset``.
OFFSET_READINGS: Dict[str, Dict[str, Tuple[Fraction, Fraction]]] = {
    "celsius": {"level": (Fraction(1), Fraction(27315, 100)),
                "difference": (Fraction(1), Fraction(0))},
    "fahrenheit": {"level": (Fraction(5, 9), Fraction(45967, 180)),
                   "difference": (Fraction(5, 9), Fraction(0))},
}

_OFFSET_SOURCE = {
    "celsius": "t / degree Celsius = T / K - 273.15, and a Celsius interval "
               "is a kelvin (SI Brochure, 2.3.1)",
    "fahrenheit": "T / K = (t / degree Fahrenheit + 459.67) * 5/9, and a "
                  "Fahrenheit interval is 5/9 K (exact by definition)",
}


def offset_reading(phrase: str, kind: str
                   ) -> Optional[Tuple[Fraction, Fraction, str]]:
    """``(factor, offset, source)`` of an offset unit phrase read as a
    ``level`` or a ``difference``, or ``None`` when the phrase is not one."""
    text = re.sub(r"\s+", " ", phrase.strip().lower())
    m = re.fullmatch(r"(?:degrees?\s+)?(celsius|centigrade|fahrenheit)",
                     text)
    if not m:
        return None
    word = "celsius" if m.group(1) == "centigrade" else m.group(1)
    factor, offset = OFFSET_READINGS[word][kind]
    return factor, offset, _OFFSET_SOURCE[word]


def difference_name(name: Optional[str]) -> bool:
    """Whether ``name`` gives a temperature difference."""
    return name in DIFFERENCE_NAMES


def scale_kind(quantity: str) -> Optional[str]:
    """The kind of a register value by its declared scale's quantity: every
    temperature the register holds (a melting or a boiling point) is a
    level."""
    return "level" if quantity == "temperature" else None


def slot_kind(axiom_text: str, base: str) -> Optional[str]:
    """``level`` / ``difference`` for a temperature slot, else ``None``."""
    return SLOT_KINDS.get((axiom_text, base))


#: ``wheel quantity -> (exact value in the coherent SI unit, source)``.
DEFINED_CONSTANTS: Dict[str, Tuple[Fraction, str]] = {
    "planck_constant": (Fraction(662607015, 10 ** 42),
                        "h = 6.62607015e-34 J s, a defining constant of the "
                        "SI since 2019"),
    "speed_of_light": (Fraction(299792458),
                       "c = 299792458 m/s, a defining constant of the SI "
                       "since 1983"),
}


def constant_value(name: str) -> Fraction:
    """The exact value of a defined constant (``KeyError`` otherwise)."""
    return DEFINED_CONSTANTS[name][0]
