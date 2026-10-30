"""``glm_universal.reasoning.units`` -- unit strings read as dimensions.

Why this module exists
----------------------
Every quantity in the physics register carries two independent statements
of what it is: a **unit string** (``W/(m^2*sr)``) written for a reader, and
a vector of **EXT10 exponents** used by the machine.  Nothing checked that
the two agreed.  This module parses the first and compares it with the
second, so a typo in either is a failure rather than a silent
disagreement.

The steradian
-------------
The reason it matters here is a specific defect, recorded in the project's
own to-do list: a unit parser that treats the steradian ``sr`` as
dimensionless.  In SI the steradian *is* dimensionless -- it is
``m^2/m^2`` -- and a parser that follows SI to the letter reads the lumen
``lm = cd*sr`` as plain ``cd``, the lux ``lx = lm/m^2`` as ``cd/m^2``, and
so conflates luminous flux with luminous intensity and illuminance with
luminance.

The register does not follow SI to the letter: its EXT10 basis carries an
``A`` axis for plane angle and an ``S`` axis for solid angle precisely so
that these stay apart.  The parser here does the same, and
:func:`register_audit` will run either way -- with the steradian carried or
dropped -- so the cost of dropping it is *measured* rather than asserted.
That is the same principle the rest of the package works to: a layer may
add to the one below it, never quietly conflate what the layer below keeps
apart.

What is stored and what is derived
----------------------------------
Ten base units, one per EXT10 axis, are stored: there is nothing to derive
them from.  Everything else is a *definition in terms of other units* --
``N = kg*m/s^2``, ``J = N*m``, ``W = J/s``, ``lm = cd*sr``, ``lx = lm/m^2``
-- and its exponents are obtained by parsing that definition, recursively.
No derived unit's exponent vector is written down anywhere.  Prefixes are
handled by stripping, and are recorded as powers of ten: they change the
magnitude, never the dimension, and this module makes no claim about
magnitude.

Everything is exact ``Fraction`` arithmetic; nothing here is a float.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..data_objects import physics as do_physics

__all__ = [
    "AXES",
    "BASE_UNITS",
    "DERIVED_UNITS",
    "DIMENSIONLESS_UNITS",
    "PREFIXES",
    "UnitError",
    "parse_unit",
    "unit_exponents",
    "dimension_of_symbol",
    "register_audit",
    "steradian_case",
    "units_report",
]

AXES: Tuple[str, ...] = do_physics.AXES_EXT10

#: The ten base units, one per EXT10 axis.  ``A`` is the radian and ``S``
#: the steradian: this basis keeps plane and solid angle, which SI treats
#: as dimensionless, as dimensions of their own.
BASE_UNITS: Dict[str, str] = {
    "m": "L", "kg": "M", "s": "T", "A": "I", "K": "H", "mol": "N",
    "cd": "J", "rad": "A", "sr": "S", "bit": "B",
}

#: Every other unit the register uses, defined in terms of units already
#: defined.  These are *definitions*, not exponent vectors: the exponents
#: are obtained by parsing the right-hand side.
DERIVED_UNITS: Dict[str, str] = {
    # mechanics
    "g": "kg",                     # dimension only; the prefix is magnitude
    "t": "kg",                     # tonne
    "N": "kg*m/s^2",
    "J": "N*m",
    "W": "J/s",
    "Pa": "N/m^2",
    "bar": "Pa",
    "L": "m^3",
    "ha": "m^2",
    "angstrom": "m",
    "Hz": "1/s",
    # electromagnetism
    "C": "A*s",
    "V": "W/A",
    "F": "C/V",
    "Ohm": "V/A",
    "S": "A/V",                    # siemens; note the axis letter S is solid
    "Wb": "V*s",                   # angle, the unit symbol S is siemens
    "T": "Wb/m^2",
    "H": "Wb/A",
    # photometry -- the reason this module exists
    "lm": "cd*sr",
    "lx": "lm/m^2",
    # radioactivity, dose, catalysis
    "Bq": "1/s",
    "Gy": "J/kg",
    "Sv": "J/kg",
    "kat": "mol/s",
    # information
    "dit": "bit",                  # a decimal digit of information
}

#: Units that name a ratio or a level and carry no dimension at all.
DIMENSIONLESS_UNITS: Tuple[str, ...] = ("dB", "phon", "param", "1", "")

#: Decimal prefixes, as powers of ten.  They are stripped before lookup and
#: never affect the dimension.
PREFIXES: Dict[str, int] = {
    "T": 12, "G": 9, "M": 6, "k": 3, "h": 2, "da": 1,
    "d": -1, "c": -2, "m": -3, "u": -6, "n": -9, "p": -12, "f": -15,
    "a": -18,
}

_ZERO: Tuple[Fraction, ...] = tuple(Fraction(0) for _ in AXES)


class UnitError(ValueError):
    """Raised when a unit string names something this module cannot read."""


# ===========================================================================
# 1.  SYMBOLS
# ===========================================================================

def _axis_vector(axis: str) -> Tuple[Fraction, ...]:
    index = AXES.index(axis)
    return tuple(Fraction(1) if i == index else Fraction(0)
                 for i in range(len(AXES)))


def dimension_of_symbol(symbol: str, steradian: bool = True,
                        _seen: Optional[Tuple[str, ...]] = None
                        ) -> Tuple[Fraction, ...]:
    """The EXT10 exponents of one unit symbol, prefixes allowed.

    ``steradian=False`` reproduces the SI reading in which the steradian is
    dimensionless, so the cost of that reading can be measured.
    """
    seen = _seen or ()
    if symbol in seen:
        raise UnitError(f"unit definitions are circular at {symbol!r}")
    if symbol in DIMENSIONLESS_UNITS:
        return _ZERO
    if symbol == "sr" and not steradian:
        return _ZERO
    if symbol in BASE_UNITS:
        return _axis_vector(BASE_UNITS[symbol])
    if symbol in DERIVED_UNITS:
        return parse_unit(DERIVED_UNITS[symbol], steradian=steradian,
                          _seen=seen + (symbol,))
    # A decimal prefix on a known symbol.  Longest prefix first so that
    # "da" is tried before "d"; a symbol that is itself known (kg, kat) has
    # already been taken above, so no prefix can shadow one.
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        if symbol.startswith(prefix) and len(symbol) > len(prefix):
            rest = symbol[len(prefix):]
            if rest in BASE_UNITS or rest in DERIVED_UNITS \
                    or rest in DIMENSIONLESS_UNITS:
                return dimension_of_symbol(rest, steradian=steradian,
                                           _seen=seen)
    raise UnitError(f"unknown unit symbol {symbol!r}")


# ===========================================================================
# 2.  THE PARSER
# ===========================================================================

def _tokenise(text: str) -> List[str]:
    tokens: List[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
        elif char in "*/()^":
            tokens.append(char)
            index += 1
        elif char == "-" or char.isdigit():
            start = index
            index += 1
            while index < len(text) and text[index].isdigit():
                index += 1
            tokens.append(text[start:index])
        elif char.isalpha() or char == "_":
            start = index
            index += 1
            while index < len(text) and (text[index].isalpha()
                                         or text[index] == "_"):
                index += 1
            tokens.append(text[start:index])
        else:
            raise UnitError(f"unit string has an unreadable character "
                            f"{char!r} in {text!r}")
    return tokens


def parse_unit(text: str, steradian: bool = True,
               _seen: Optional[Tuple[str, ...]] = None
               ) -> Tuple[Fraction, ...]:
    """Parse a unit string into EXT10 exponents.

    The grammar is the one the register writes in: symbols joined by ``*``
    and ``/``, integer powers with ``^``, and parentheses.  Division is
    left-associative, so ``J*s/rad`` is ``(J*s)/rad`` and a denominator with
    more than one factor is parenthesised, as the register writes it.
    """
    tokens = _tokenise(text)
    position = 0

    def peek() -> Optional[str]:
        return tokens[position] if position < len(tokens) else None

    def take() -> str:
        nonlocal position
        token = tokens[position]
        position += 1
        return token

    def factor() -> Tuple[Fraction, ...]:
        token = peek()
        if token is None:
            raise UnitError(f"unit string ends early: {text!r}")
        if token == "(":
            take()
            value = expression()
            if peek() != ")":
                raise UnitError(f"unit string has an unclosed bracket: "
                                f"{text!r}")
            take()
            return value
        take()
        if token.lstrip("-").isdigit():
            if token != "1":
                raise UnitError(f"unit string has a numeric factor {token!r} "
                                f"that is not 1: {text!r}")
            return _ZERO
        return dimension_of_symbol(token, steradian=steradian, _seen=_seen)

    def power() -> Fraction:
        """An exponent: an integer, or a bracketed rational like ``(1/2)``."""
        token = peek()
        if token == "(":
            take()
            numerator = peek()
            if numerator is None or not numerator.lstrip("-").isdigit():
                raise UnitError(f"unit string has a malformed power: {text!r}")
            take()
            exponent = Fraction(int(numerator))
            if peek() == "/":
                take()
                denominator = peek()
                if denominator is None or not denominator.isdigit():
                    raise UnitError(f"unit string has a malformed power: "
                                    f"{text!r}")
                take()
                exponent = Fraction(int(numerator), int(denominator))
            if peek() != ")":
                raise UnitError(f"unit string has an unclosed power: {text!r}")
            take()
            return exponent
        if token is None or not token.lstrip("-").isdigit():
            raise UnitError(f"unit string has a malformed power: {text!r}")
        take()
        return Fraction(int(token))

    def term() -> Tuple[Fraction, ...]:
        value = factor()
        if peek() == "^":
            take()
            exponent = power()
            value = tuple(x * exponent for x in value)
        return value

    def _starts_a_factor(token: Optional[str]) -> bool:
        """Implicit multiplication: ``1/(rad s)`` means ``1/(rad*s)``."""
        if token is None or token in ("*", "/", "^", ")"):
            return False
        return True

    def expression() -> Tuple[Fraction, ...]:
        value = term()
        while True:
            token = peek()
            if token in ("*", "/"):
                operator = take()
            elif _starts_a_factor(token):
                operator = "*"
            else:
                break
            right = term()
            if operator == "*":
                value = tuple(value[i] + right[i] for i in range(len(AXES)))
            else:
                value = tuple(value[i] - right[i] for i in range(len(AXES)))
        return value

    if not tokens:
        return _ZERO
    result = expression()
    if position != len(tokens):
        raise UnitError(f"unit string has trailing text: {text!r}")
    return result


def unit_exponents(text: str, steradian: bool = True
                   ) -> Optional[Tuple[Fraction, ...]]:
    """:func:`parse_unit`, returning ``None`` instead of raising."""
    try:
        return parse_unit(text, steradian=steradian)
    except UnitError:
        return None


# ===========================================================================
# 3.  THE AUDIT
# ===========================================================================

def register_audit(steradian: bool = True) -> Dict[str, object]:
    """Parse every quantity's unit and compare it with its EXT10 exponents.

    Two things can go wrong and they are reported separately: a unit string
    this module cannot read at all, and one it reads into exponents that
    disagree with the register's own.  Both are listed by name.
    """
    quantities = do_physics.load_physics_register()
    unreadable: List[Tuple[str, str, str]] = []
    mismatched: List[Dict[str, object]] = []
    agreed = 0
    for quantity in quantities:
        try:
            parsed = parse_unit(quantity.unit, steradian=steradian)
        except UnitError as error:
            unreadable.append((quantity.name, quantity.unit, str(error)))
            continue
        declared = tuple(Fraction(e) for e in quantity.exps_ext10)
        if parsed == declared:
            agreed += 1
        else:
            mismatched.append({
                "name": quantity.name,
                "unit": quantity.unit,
                "declared": do_physics.dimension_string(declared, "EXT10"),
                "parsed": do_physics.dimension_string(parsed, "EXT10"),
            })
    return {
        "steradian_carried": steradian,
        "quantities": len(quantities),
        "readable": len(quantities) - len(unreadable),
        "unreadable": tuple(unreadable),
        "unreadable_count": len(unreadable),
        "agreed": agreed,
        "mismatched": tuple(mismatched),
        "mismatched_count": len(mismatched),
        "every_unit_readable": not unreadable,
        "every_unit_agrees": not mismatched and not unreadable,
    }


def steradian_case() -> Dict[str, object]:
    """The defect, reproduced and measured, then repaired and measured.

    Running the same audit twice -- once with the steradian carried as a
    dimension and once with it dropped, as SI has it -- says exactly what
    dropping it costs, and names the quantities that pay.
    """
    carried = register_audit(steradian=True)
    dropped = register_audit(steradian=False)
    broken = tuple(entry["name"] for entry in dropped["mismatched"])
    quantities = do_physics.load_physics_register()
    by_name = {q.name: q for q in quantities}
    axis = AXES.index("S")
    solid_angle_quantities = tuple(
        sorted(q.name for q in quantities if q.exps_ext10[axis] != 0))
    conflations: List[Dict[str, object]] = []
    seen: Dict[Tuple[Fraction, ...], List[str]] = {}
    for quantity in quantities:
        key = parse_unit(quantity.unit, steradian=False)
        seen.setdefault(key, []).append(quantity.name)
    for name in broken:
        quantity = by_name[name]
        key = parse_unit(quantity.unit, steradian=False)
        partners = sorted(other for other in seen[key] if other != name)
        conflations.append({"name": name, "unit": quantity.unit,
                            "conflated_count": len(partners),
                            "conflated_with": tuple(partners[:8])})
    photometric = tuple(sorted(
        q.name for q in quantities
        if any(symbol in _tokenise(q.unit) for symbol in ("lm", "lx"))))
    return {
        "with_steradian": {
            "mismatched": carried["mismatched_count"],
            "agreed": carried["agreed"],
            "every_unit_agrees": carried["every_unit_agrees"],
        },
        "without_steradian": {
            "mismatched": dropped["mismatched_count"],
            "agreed": dropped["agreed"],
            "every_unit_agrees": dropped["every_unit_agrees"],
        },
        "quantities_broken_by_dropping_it": broken,
        "broken_count": len(broken),
        "quantities_with_a_solid_angle": solid_angle_quantities,
        "solid_angle_count": len(solid_angle_quantities),
        "conflations": tuple(conflations),
        "photometric_quantities": photometric,
        "photometric_count": len(photometric),
        "statement": (
            "Read the SI way, the steradian is dimensionless, the lumen is "
            "the candela and the lux is the candela per square metre.  The "
            "register's EXT10 basis keeps a solid-angle axis so that they "
            "stay apart, and the parser here reads the register's way.  The "
            "count above is what the SI reading costs, recomputed by "
            "running the audit both ways rather than quoted.  The "
            "quantities whose unit is written with the lumen or the lux are "
            "listed separately: those are the ones the project's own note "
            "called the luminous concepts, and they are a subset of the "
            "larger set that a dimensionless steradian breaks."),
    }


def units_report() -> Dict[str, object]:
    """Everything this module knows, recomputed on call."""
    audit = register_audit()
    case = steradian_case()
    derived: Dict[str, str] = {}
    for symbol in sorted(DERIVED_UNITS):
        derived[symbol] = do_physics.dimension_string(
            dimension_of_symbol(symbol), "EXT10")
    return {
        "base_units": tuple(sorted(BASE_UNITS)),
        "base_unit_count": len(BASE_UNITS),
        "derived_units": tuple(sorted(DERIVED_UNITS)),
        "derived_unit_count": len(DERIVED_UNITS),
        "derived_dimensions": derived,
        "prefix_count": len(PREFIXES),
        "audit": audit,
        "steradian": case,
        "method": (
            "Ten base units are stored, one per EXT10 axis; every other "
            "unit is a definition in terms of units already defined and its "
            "exponents are obtained by parsing that definition.  No derived "
            "unit's exponent vector is written down.  Decimal prefixes are "
            "stripped and recorded as powers of ten: they change the "
            "magnitude, never the dimension, and this module makes no claim "
            "about magnitude."),
    }
