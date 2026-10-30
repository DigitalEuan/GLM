"""The meaning space: what a term denotes, encoded as 24 exact rationals.

Why this module exists
----------------------
The GLM's older lexical layers encode a *word*.  :mod:`..data_objects.lexicon`
interns its spelling into vocabulary indices; the ARC-era concept graph hashed
the spelling with SHA-256 and snapped the result near a Golay codeword.  Both
are stable identifiers of a **string**.  Neither is a measurement of the
**subject** the string is about, and no amount of geometry applied afterwards
can recover information that was never encoded: a carrier derived from letters
answers questions about letters.

This module encodes the other thing.  A :class:`Meaning` is a canonical,
notation-free, exactly-representable record of *what a term denotes*.  It is
built only from determinate data -- an atomic number, a dimension vector, an
exact rational, a chemical formula -- so two terms denote the same thing
exactly when their meanings are equal, and that equality is decidable by
comparing 24 rationals.

The six kinds, and why only these six
-------------------------------------
A meaning is admitted only when the subject has a *determinate* answer that
the repository can state exactly.  Six kinds qualify today:

===============  ===========================================================
kind             the determinate content
===============  ===========================================================
``number``       an exact rational.  ``"two"``, ``"2"``, ``"4/2"`` and
                 ``"1+1"`` all denote it, and so does ``"XII"`` for twelve;
                 ``"II"`` is refused, because it also reads as two iodine
                 atoms.
``dimension``    an EXT10 exponent vector ``(L M T I H N J A S B)``.  This is
                 what a physical *kind of quantity* is: ``speed`` is
                 ``L T^-1`` whatever it is called.
``quantity``     a dimension together with an exact magnitude in the coherent
                 SI unit: what a physical *constant* or *measurement* is.
``element``      a chemical element, pinned by its atomic number.
``compound``     a chemical species, pinned by its formula as a sorted
                 multiset of ``(Z, count)`` pairs.
``operation``    one of eight determinate operations on meanings (add,
                 subtract, multiply, divide, negate, reciprocal, power,
                 identity).
===============  ===========================================================

Everything else -- ``"beautiful"``, ``"ago"``, ``"abb"``, the 4,282 dictionary
words the ARC pipeline absorbed -- is **refused**, by :mod:`.reference`, with
a stated reason.  Refusal is the point.  A layer that admits a term it cannot
pin down has to invent the pin, and an invented pin is exactly the useless
data this package is replacing.

The 24-coordinate layout
------------------------
::

    0       kind            1..6, the table above in that order
    1..10   ext10           L M T I H N J A S B exponents (exact, may be
                            fractional); zero for the non-physical kinds
    11      magnitude       the rational a ``number`` is, or the coherent-SI
                            magnitude a ``quantity`` has; zero otherwise
    12..21  formula         five ``(Z, count)`` slots, ascending in Z,
                            zero-filled; an ``element`` uses slot 0 as
                            ``(Z, 1)``
    22      operation       operation index 1..8, else 0
    23      checksum        ``sum (i+1) * c_i`` over coordinates 0..22

Nothing is padded for cosmetic reasons and no coordinate is spare: the
layout is 1 + 10 + 1 + 10 + 1 + 1 = 24.

Contracts
---------
* **Exactness.**  Every coordinate is an ``int`` or a
  :class:`~fractions.Fraction`.  A float raises.
* **Round trip.**  :func:`decode` inverts :func:`encode` on every well-formed
  meaning, so the carrier loses nothing: ``decode(encode(m)) == m``.
* **Injectivity.**  Distinct well-formed meanings have distinct carriers.
  This is a theorem, not a hope -- it follows from the round trip -- and it is
  the property that makes carrier equality usable as meaning equality.
* **Notation-independence.**  :func:`encode` takes a :class:`Meaning`.  It has
  no parameter through which a name, a spelling or a language could enter, so
  the claim "the carrier does not depend on the notation" is enforced by the
  type of the function rather than asserted in a docstring.

The formal counterpart of the last two contracts is
``RequestProject/GLM/Semantics/Meaning.lean``, which proves the round trip and
injectivity for this exact layout, and proves that no encoding which
distinguishes notations can be a function of meaning.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from ..data_objects.base import (Carrier, Codec, DataObject, Scalar, as_exact,
                                 exact_vector)

__all__ = [
    "AXES_EXT10", "KINDS", "KIND_INDEX", "OPERATIONS", "OPERATION_INDEX",
    "MEANING_LAYOUT", "MAX_FORMULA_SLOTS", "MAX_Z",
    "Meaning", "MeaningCodec", "DecodeError", "encode", "decode",
    "meaning_object", "zero_exponents", "dimension_string", "formula_string",
]

#: The ten EXT10 axes, in carrier order.  Identical to the physics register's
#: convention, so a physics carrier and a meaning carrier agree coordinate by
#: coordinate on what an exponent means.
AXES_EXT10: Tuple[str, ...] = ("L", "M", "T", "I", "H", "N", "J",
                               "A", "S", "B")

#: The six meaning kinds, in index order (index = position + 1).
KINDS: Tuple[str, ...] = ("number", "dimension", "quantity", "element",
                          "compound", "operation")

KIND_INDEX: Dict[str, int] = {name: i + 1 for i, name in enumerate(KINDS)}

#: The eight determinate operations, in index order (index = position + 1).
OPERATIONS: Tuple[str, ...] = ("add", "subtract", "multiply", "divide",
                               "negate", "reciprocal", "power", "identity")

OPERATION_INDEX: Dict[str, int] = {name: i + 1
                                   for i, name in enumerate(OPERATIONS)}

#: How many ``(Z, count)`` slots a compound carrier has.
MAX_FORMULA_SLOTS = 5

#: The largest atomic number the chemistry register knows.
MAX_Z = 118

#: Per-coordinate names, in carrier order.
MEANING_LAYOUT: Tuple[str, ...] = (
    ("kind",)
    + tuple(f"ext10.{a}" for a in AXES_EXT10)
    + ("magnitude",)
    + tuple(part for slot in range(MAX_FORMULA_SLOTS)
            for part in (f"formula{slot}.z", f"formula{slot}.count"))
    + ("operation", "checksum")
)
assert len(MEANING_LAYOUT) == 24, MEANING_LAYOUT


def zero_exponents() -> Tuple[Fraction, ...]:
    """The dimensionless EXT10 exponent vector."""
    return tuple(Fraction(0) for _ in AXES_EXT10)


def _exact_exponents(values: Iterable[Any]) -> Tuple[Fraction, ...]:
    out = tuple(as_exact(v) for v in values)
    if len(out) != len(AXES_EXT10):
        raise ValueError(f"meaning: {len(AXES_EXT10)} EXT10 exponents "
                         f"required, got {len(out)}")
    return out


def _canonical_formula(parts: Iterable[Sequence[int]]
                       ) -> Tuple[Tuple[int, int], ...]:
    """Normalise a formula: merge repeats, sort by Z, reject the impossible."""
    totals: Dict[int, int] = {}
    for pair in parts:
        z, count = int(pair[0]), int(pair[1])
        if not 1 <= z <= MAX_Z:
            raise ValueError(f"meaning: atomic number {z} outside 1..{MAX_Z}")
        if count <= 0:
            raise ValueError(f"meaning: atom count {count} is not positive")
        totals[z] = totals.get(z, 0) + count
    if not totals:
        raise ValueError("meaning: a compound needs at least one element")
    if len(totals) > MAX_FORMULA_SLOTS:
        raise ValueError(
            f"meaning: {len(totals)} distinct elements exceeds the "
            f"{MAX_FORMULA_SLOTS} formula slots -- the carrier refuses to "
            f"truncate a formula")
    return tuple(sorted(totals.items()))


@dataclass(frozen=True)
class Meaning:
    """What a term denotes: canonical, notation-free, exactly comparable.

    Construct through the classmethods; the field layout is an implementation
    detail of the carrier and the constructors enforce canonicity, so two
    equal meanings are equal as dataclasses and have equal carriers.
    """

    kind: str
    exponents: Tuple[Fraction, ...] = ()
    magnitude: Fraction = Fraction(0)
    formula: Tuple[Tuple[int, int], ...] = ()
    operation: str = ""

    # -- construction ----------------------------------------------------

    def __post_init__(self) -> None:
        if self.kind not in KIND_INDEX:
            raise ValueError(f"meaning: unknown kind {self.kind!r}")
        object.__setattr__(self, "exponents",
                           _exact_exponents(self.exponents or
                                            zero_exponents()))
        object.__setattr__(self, "magnitude", as_exact(self.magnitude))
        object.__setattr__(self, "formula",
                           tuple((int(z), int(n)) for z, n in self.formula))
        if self.kind in ("number", "element", "compound", "operation"):
            if any(e != 0 for e in self.exponents):
                raise ValueError(f"meaning: a {self.kind} has no dimension")
        if self.kind in ("dimension", "element", "compound", "operation"):
            if self.magnitude != 0:
                raise ValueError(f"meaning: a {self.kind} has no magnitude")
        if self.kind in ("number", "dimension", "quantity", "operation"):
            if self.formula:
                raise ValueError(f"meaning: a {self.kind} has no formula")
        if self.kind == "operation":
            if self.operation not in OPERATION_INDEX:
                raise ValueError(f"meaning: unknown operation "
                                 f"{self.operation!r}")
        elif self.operation:
            raise ValueError(f"meaning: a {self.kind} carries no operation")
        if self.kind == "element":
            if len(self.formula) != 1 or self.formula[0][1] != 1:
                raise ValueError("meaning: an element is one atom of one Z")
        if self.kind == "compound":
            if not self.formula:
                raise ValueError("meaning: a compound needs a formula")
        if self.formula != tuple(sorted(self.formula)):
            raise ValueError("meaning: formula slots must ascend in Z")

    @classmethod
    def number(cls, value: Any) -> "Meaning":
        """The exact rational a numeral, number word or arithmetic denotes."""
        return cls(kind="number", magnitude=as_exact(value))

    @classmethod
    def dimension(cls, exponents: Iterable[Any]) -> "Meaning":
        """A kind of physical quantity, pinned by its EXT10 exponents."""
        return cls(kind="dimension", exponents=_exact_exponents(exponents))

    @classmethod
    def quantity(cls, exponents: Iterable[Any], magnitude: Any) -> "Meaning":
        """A physical quantity: a dimension with an exact coherent-SI value."""
        return cls(kind="quantity", exponents=_exact_exponents(exponents),
                   magnitude=as_exact(magnitude))

    @classmethod
    def element(cls, z: int) -> "Meaning":
        """A chemical element, pinned by its atomic number."""
        z = int(z)
        if not 1 <= z <= MAX_Z:
            raise ValueError(f"meaning: atomic number {z} outside 1..{MAX_Z}")
        return cls(kind="element", formula=((z, 1),))

    @classmethod
    def compound(cls, parts: Iterable[Sequence[int]]) -> "Meaning":
        """A chemical species, pinned by its formula."""
        return cls(kind="compound", formula=_canonical_formula(parts))

    @classmethod
    def op(cls, name: str) -> "Meaning":
        """One of the eight determinate operations."""
        return cls(kind="operation", operation=name)

    # -- views -----------------------------------------------------------

    @property
    def si7(self) -> Tuple[Fraction, ...]:
        """The SI7 projection: the first seven EXT10 exponents.

        Lossy exactly when one of ``A``, ``S`` or ``B`` is nonzero, which is
        why torque and energy separate in EXT10 and coincide in SI7.
        """
        return self.exponents[:7]

    @property
    def is_dimensionless(self) -> bool:
        """Whether every EXT10 exponent is zero."""
        return all(e == 0 for e in self.exponents)

    def describe(self) -> str:
        """A short, deterministic, notation-free rendering of the meaning."""
        if self.kind == "number":
            return f"number {self.magnitude}"
        if self.kind == "dimension":
            return f"dimension {dimension_string(self.exponents)}"
        if self.kind == "quantity":
            return (f"quantity {self.magnitude} "
                    f"{dimension_string(self.exponents)}")
        if self.kind == "element":
            return f"element Z={self.formula[0][0]}"
        if self.kind == "compound":
            return f"compound {formula_string(self.formula)}"
        return f"operation {self.operation}"

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view; rationals as ``"n/d"`` strings."""
        return {
            "kind": self.kind,
            "ext10": [f"{e.numerator}/{e.denominator}"
                      for e in self.exponents],
            "magnitude": (f"{self.magnitude.numerator}/"
                          f"{self.magnitude.denominator}"),
            "formula": [[z, n] for z, n in self.formula],
            "operation": self.operation,
            "describe": self.describe(),
        }


def dimension_string(exponents: Sequence[Fraction]) -> str:
    """``L^2 M T^-2`` style rendering of an EXT10 exponent vector."""
    parts: List[str] = []
    for axis, e in zip(AXES_EXT10, exponents):
        if e == 0:
            continue
        parts.append(axis if e == 1 else f"{axis}^{e}")
    return " ".join(parts) if parts else "1"


def formula_string(formula: Sequence[Tuple[int, int]]) -> str:
    """``Z1_n1 Z2_n2`` rendering: the formula without depending on symbols."""
    return " ".join(f"Z{z}" if n == 1 else f"Z{z}_{n}" for z, n in formula)


# ===========================================================================
#  The carrier
# ===========================================================================

def _checksum(head: Sequence[Scalar]) -> Fraction:
    """A deterministic linear integrity coordinate over coordinates 0..22."""
    return sum((Fraction(i + 1) * as_exact(c) for i, c in enumerate(head)),
               Fraction(0))


def encode(meaning: Meaning) -> Carrier:
    """The 24 exact coordinates of a meaning.

    Takes a meaning and nothing else: there is no argument through which a
    spelling could reach the carrier.
    """
    head: List[Fraction] = [Fraction(KIND_INDEX[meaning.kind])]
    head.extend(meaning.exponents)
    head.append(meaning.magnitude)
    for slot in range(MAX_FORMULA_SLOTS):
        if slot < len(meaning.formula):
            z, n = meaning.formula[slot]
            head.extend((Fraction(z), Fraction(n)))
        else:
            head.extend((Fraction(0), Fraction(0)))
    head.append(Fraction(OPERATION_INDEX.get(meaning.operation, 0)))
    return exact_vector(list(head) + [_checksum(head)])


class DecodeError(ValueError):
    """Raised when a carrier is not the carrier of any meaning."""


def decode(carrier: Sequence[Scalar]) -> Meaning:
    """The meaning of a carrier, or :class:`DecodeError`.

    Inverts :func:`encode` exactly.  The checksum on coordinate 23 is checked
    first, so a perturbed carrier is rejected rather than resolving quietly to
    a different meaning.
    """
    values = [as_exact(c) for c in carrier]
    if len(values) != 24:
        raise DecodeError(f"meaning: 24 coordinates required, "
                          f"got {len(values)}")
    if _checksum(values[:23]) != values[23]:
        raise DecodeError("meaning: checksum mismatch -- the carrier is not "
                          "the carrier of any meaning")
    kind_index = values[0]
    if kind_index.denominator != 1 or not 1 <= kind_index <= len(KINDS):
        raise DecodeError(f"meaning: coordinate 0 is not a kind index "
                          f"({kind_index})")
    kind = KINDS[int(kind_index) - 1]
    exponents = tuple(values[1:11])
    magnitude = values[11]
    formula: List[Tuple[int, int]] = []
    for slot in range(MAX_FORMULA_SLOTS):
        z, n = values[12 + 2 * slot], values[13 + 2 * slot]
        if z == 0 and n == 0:
            continue
        if z.denominator != 1 or n.denominator != 1:
            raise DecodeError("meaning: formula slots must be integral")
        formula.append((int(z), int(n)))
    op_index = values[22]
    if op_index.denominator != 1 or not 0 <= op_index <= len(OPERATIONS):
        raise DecodeError(f"meaning: coordinate 22 is not an operation index "
                          f"({op_index})")
    operation = OPERATIONS[int(op_index) - 1] if op_index != 0 else ""
    try:
        return Meaning(kind=kind, exponents=exponents, magnitude=magnitude,
                       formula=tuple(formula), operation=operation)
    except ValueError as exc:
        raise DecodeError(f"meaning: {exc}") from None


class MeaningCodec(Codec):
    """The meaning codec, under the package's two-legged round-trip contract.

    ``domain`` is ``"semantics"``: a meaning is not owned by physics or by
    chemistry, it is the thing those registers are registers *of*.
    """

    domain = "semantics"
    layout = MEANING_LAYOUT

    def encode(self, source: Meaning) -> DataObject:   # type: ignore[override]
        if not isinstance(source, Meaning):
            raise TypeError("MeaningCodec: source must be a Meaning")
        return DataObject(
            name=source.describe(),
            domain=self.domain,
            carrier=encode(source),
            attributes=source.as_dict(),
            layout=self.layout,
            provenance={"source": "glm_universal.semantics.meaning",
                        "notation_free": True},
        )

    def decode(self, obj: DataObject) -> Meaning:      # type: ignore[override]
        return decode(obj.carrier)


def meaning_object(meaning: Meaning) -> DataObject:
    """The meaning as a checked :class:`~..data_objects.base.DataObject`."""
    return MeaningCodec().check(meaning)
