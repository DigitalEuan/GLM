"""Relations between meanings: derived, witnessed, and re-checkable.

What a relation is here
-----------------------
A relation is **not** a stored assertion.  It is a predicate on meanings that
:func:`derive` computes and :func:`verify` can recompute from the two meanings
alone.  Nothing is remembered that cannot be re-derived, so the graph in
:mod:`.graph` has no capacity to be wrong in the way the inherited concept
graph was wrong: there, ``auto_proposed`` edges recorded that two SHA-256
hashes happened to land within a Hamming radius of each other, which is a fact
about the two spellings and about nothing else.

Every relation below is a fact about the subjects.  ``energy`` and ``torque``
are related because their exponent vectors are related; ``water`` and
``oxygen`` are related because the formula of the one contains the other;
``twelve`` and ``three`` are related because 3 divides 12.  A word, a formula,
an expression and a register symbol enter this module only after
:mod:`.reference` has replaced them by what they denote.

The relations
-------------
*Binary*, over ordered pairs of meanings:

===========================  =================================================
``same_meaning``             identical meanings (different notations, one
                             referent)
``same_dimension``           equal EXT10 exponents, different meanings --
                             the conflation the dimension layer performs
``si7_conflates``            different EXT10 exponents, equal SI7 projection:
                             the exact boundary where dropping the angle and
                             information axes loses a distinction
``reciprocal_dimension``     exponent vectors are negatives of each other
``magnitude_of``             a quantity and the dimension it has
``successor``                integers ``n`` and ``n + 1``
``divides``                  integers ``a | b``
``reciprocal``               rationals ``a = 1 / b``
``square``                   rationals ``a = b^2``
``less_than``                rationals ``a < b``
``contains_element``         a compound and an element in its formula
``same_group_block``         two elements of the same periodic group block
``same_period``              two elements of the same period
``next_element``             elements ``Z`` and ``Z + 1``
``atom_count``               a number and the compound it counts an atom of
                             (cross-domain: word/numeral meets chemistry)
===========================  =================================================

*Ternary*, over ordered triples, since a product is irreducibly three-place:

===========================  =================================================
``product_of``               ``dim a = dim b + dim c``   (``energy = force *
                             length``)
``quotient_of``              ``dim a = dim b - dim c``   (``speed = length /
                             time``)
``sum_is``                   ``a = b + c`` on numbers
``product_is``               ``a = b * c`` on numbers
===========================  =================================================

Each derivation returns a :class:`Claim` carrying the relation name, the
meanings it holds between, and a witness: the arithmetic that makes it true.
:func:`verify` recomputes the predicate and returns whether the claim stands,
so a claim that has been transported, serialised or edited can be audited
without trusting its provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..data_objects.elements import load_element_register, period_of
from .meaning import Meaning, dimension_string, formula_string

__all__ = [
    "Claim", "BINARY_RELATIONS", "TERNARY_RELATIONS",
    "derive", "derive_ternary", "verify", "verify_all", "relation_names",
    "has_dimension", "exponents_of",
]


@dataclass(frozen=True)
class Claim:
    """One derived relation, with the arithmetic that makes it true."""

    relation: str
    meanings: Tuple[Meaning, ...]
    witness: str

    @property
    def arity(self) -> int:
        """How many meanings the relation holds between."""
        return len(self.meanings)

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "relation": self.relation,
            "arity": self.arity,
            "meanings": [m.describe() for m in self.meanings],
            "witness": self.witness,
        }


# ===========================================================================
# 1.  HELPERS
# ===========================================================================

def has_dimension(meaning: Meaning) -> bool:
    """Whether a meaning carries EXT10 exponents at all."""
    return meaning.kind in ("dimension", "quantity")


def exponents_of(meaning: Meaning) -> Optional[Tuple[Fraction, ...]]:
    """The EXT10 exponents of a meaning, or ``None`` if it has none."""
    return meaning.exponents if has_dimension(meaning) else None


def _is_integer(meaning: Meaning) -> bool:
    return meaning.kind == "number" and meaning.magnitude.denominator == 1


@lru_cache(maxsize=1)
def _element_facts() -> Dict[int, Tuple[Optional[int], int]]:
    """``Z -> (group block code, period)`` from the frozen register."""
    return {el.z: (el.group_block_code, period_of(el.z))
            for el in load_element_register()}


def _elements_in(meaning: Meaning) -> Tuple[Tuple[int, int], ...]:
    """The ``(Z, count)`` pairs of an element or compound meaning."""
    return meaning.formula if meaning.kind in ("element", "compound") else ()


# ===========================================================================
# 2.  BINARY RELATIONS
# ===========================================================================

def _same_meaning(a: Meaning, b: Meaning) -> Optional[str]:
    if a != b:
        return None
    return f"identical meanings: {a.describe()}"


def _same_dimension(a: Meaning, b: Meaning) -> Optional[str]:
    if a == b or not (has_dimension(a) and has_dimension(b)):
        return None
    if a.exponents != b.exponents:
        return None
    return (f"equal EXT10 exponents {dimension_string(a.exponents)}; "
            f"the dimension layer cannot tell these apart")


def _si7_conflates(a: Meaning, b: Meaning) -> Optional[str]:
    if not (has_dimension(a) and has_dimension(b)):
        return None
    if a.exponents == b.exponents or a.si7 != b.si7:
        return None
    return (f"EXT10 separates them ({dimension_string(a.exponents)} vs "
            f"{dimension_string(b.exponents)}) and SI7 does not: the angle "
            f"and information axes are the whole difference")


def _reciprocal_dimension(a: Meaning, b: Meaning) -> Optional[str]:
    if not (has_dimension(a) and has_dimension(b)):
        return None
    if a.is_dimensionless or any(x + y != 0 for x, y in
                                 zip(a.exponents, b.exponents)):
        return None
    return (f"exponent vectors sum to zero: "
            f"{dimension_string(a.exponents)} and "
            f"{dimension_string(b.exponents)}")


def _magnitude_of(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "quantity" or b.kind != "dimension":
        return None
    if a.exponents != b.exponents:
        return None
    return (f"{a.magnitude} is a magnitude of "
            f"{dimension_string(b.exponents)}")


def _successor(a: Meaning, b: Meaning) -> Optional[str]:
    if not (_is_integer(a) and _is_integer(b)):
        return None
    if b.magnitude != a.magnitude + 1:
        return None
    return f"{b.magnitude} = {a.magnitude} + 1"


def _divides(a: Meaning, b: Meaning) -> Optional[str]:
    if not (_is_integer(a) and _is_integer(b)):
        return None
    x, y = int(a.magnitude), int(b.magnitude)
    if x == 0 or y % x != 0 or x == y:
        return None
    return f"{x} divides {y}: {y} = {x} * {y // x}"


def _reciprocal(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "number" or b.kind != "number":
        return None
    if b.magnitude == 0 or a.magnitude * b.magnitude != 1:
        return None
    return f"{a.magnitude} = 1 / {b.magnitude}"


def _square(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "number" or b.kind != "number":
        return None
    if a.magnitude != b.magnitude ** 2 or b.magnitude in (0, 1):
        return None
    return f"{a.magnitude} = {b.magnitude}^2"


def _less_than(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "number" or b.kind != "number":
        return None
    if a.magnitude >= b.magnitude:
        return None
    return f"{a.magnitude} < {b.magnitude}"


def _contains_element(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "compound" or b.kind != "element":
        return None
    z = b.formula[0][0]
    for zz, count in a.formula:
        if zz == z:
            return (f"{formula_string(a.formula)} contains {count} atom(s) "
                    f"of Z {z}")
    return None


def _same_group_block(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "element" or b.kind != "element" or a == b:
        return None
    facts = _element_facts()
    ga = facts[a.formula[0][0]][0]
    gb = facts[b.formula[0][0]][0]
    if ga is None or gb is None or ga != gb:
        return None
    return f"both elements have group block code {ga}"


def _same_period(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "element" or b.kind != "element" or a == b:
        return None
    facts = _element_facts()
    pa = facts[a.formula[0][0]][1]
    pb = facts[b.formula[0][0]][1]
    if pa != pb:
        return None
    return f"both elements are in period {pa}"


def _next_element(a: Meaning, b: Meaning) -> Optional[str]:
    if a.kind != "element" or b.kind != "element":
        return None
    za, zb = a.formula[0][0], b.formula[0][0]
    if zb != za + 1:
        return None
    return f"Z {zb} = Z {za} + 1"


def _atom_count(a: Meaning, b: Meaning) -> Optional[str]:
    """A number and a species in whose formula that number is a count."""
    if a.kind != "number" or b.kind not in ("compound", "element"):
        return None
    if a.magnitude.denominator != 1:
        return None
    n = int(a.magnitude)
    for z, count in b.formula:
        if count == n and n > 1:
            return (f"{n} is the atom count of Z {z} in "
                    f"{formula_string(b.formula)}")
    return None


#: Every binary relation, by name.  A predicate returns the witness when the
#: relation holds and ``None`` when it does not.
BINARY_RELATIONS: Dict[str, object] = {
    "same_meaning": _same_meaning,
    "same_dimension": _same_dimension,
    "si7_conflates": _si7_conflates,
    "reciprocal_dimension": _reciprocal_dimension,
    "magnitude_of": _magnitude_of,
    "successor": _successor,
    "divides": _divides,
    "reciprocal": _reciprocal,
    "square": _square,
    "less_than": _less_than,
    "contains_element": _contains_element,
    "same_group_block": _same_group_block,
    "same_period": _same_period,
    "next_element": _next_element,
    "atom_count": _atom_count,
}


# ===========================================================================
# 3.  TERNARY RELATIONS
# ===========================================================================

def _product_of(a: Meaning, b: Meaning, c: Meaning) -> Optional[str]:
    if not all(has_dimension(m) for m in (a, b, c)):
        return None
    if any(x != y + z for x, y, z in
           zip(a.exponents, b.exponents, c.exponents)):
        return None
    return (f"{dimension_string(a.exponents)} = "
            f"{dimension_string(b.exponents)} * "
            f"{dimension_string(c.exponents)} (exponents add)")


def _quotient_of(a: Meaning, b: Meaning, c: Meaning) -> Optional[str]:
    if not all(has_dimension(m) for m in (a, b, c)):
        return None
    if any(x != y - z for x, y, z in
           zip(a.exponents, b.exponents, c.exponents)):
        return None
    return (f"{dimension_string(a.exponents)} = "
            f"{dimension_string(b.exponents)} / "
            f"{dimension_string(c.exponents)} (exponents subtract)")


def _sum_is(a: Meaning, b: Meaning, c: Meaning) -> Optional[str]:
    if any(m.kind != "number" for m in (a, b, c)):
        return None
    if a.magnitude != b.magnitude + c.magnitude:
        return None
    return f"{a.magnitude} = {b.magnitude} + {c.magnitude}"


def _product_is(a: Meaning, b: Meaning, c: Meaning) -> Optional[str]:
    if any(m.kind != "number" for m in (a, b, c)):
        return None
    if a.magnitude != b.magnitude * c.magnitude:
        return None
    return f"{a.magnitude} = {b.magnitude} * {c.magnitude}"


#: Every ternary relation, by name.
TERNARY_RELATIONS: Dict[str, object] = {
    "product_of": _product_of,
    "quotient_of": _quotient_of,
    "sum_is": _sum_is,
    "product_is": _product_is,
}


def relation_names() -> Tuple[str, ...]:
    """Every relation this module can derive, sorted."""
    return tuple(sorted(set(BINARY_RELATIONS) | set(TERNARY_RELATIONS)))


# ===========================================================================
# 4.  DERIVATION AND VERIFICATION
# ===========================================================================

def derive(a: Meaning, b: Meaning,
           relations: Optional[Sequence[str]] = None) -> Tuple[Claim, ...]:
    """Every binary relation that holds from ``a`` to ``b``, in name order."""
    names = (tuple(sorted(BINARY_RELATIONS)) if relations is None
             else tuple(relations))
    out: List[Claim] = []
    for name in names:
        predicate = BINARY_RELATIONS[name]
        witness = predicate(a, b)           # type: ignore[operator]
        if witness is not None:
            out.append(Claim(relation=name, meanings=(a, b),
                             witness=witness))
    return tuple(out)


def derive_ternary(a: Meaning, b: Meaning, c: Meaning,
                   relations: Optional[Sequence[str]] = None
                   ) -> Tuple[Claim, ...]:
    """Every ternary relation that holds of ``(a, b, c)``, in name order."""
    names = (tuple(sorted(TERNARY_RELATIONS)) if relations is None
             else tuple(relations))
    out: List[Claim] = []
    for name in names:
        predicate = TERNARY_RELATIONS[name]
        witness = predicate(a, b, c)        # type: ignore[operator]
        if witness is not None:
            out.append(Claim(relation=name, meanings=(a, b, c),
                             witness=witness))
    return tuple(out)


def verify(claim: Claim) -> bool:
    """Recompute a claim's predicate from its meanings alone.

    A claim is worth exactly what its re-derivation is worth: this is the
    check that separates a derived graph from a remembered one.
    """
    if claim.relation in BINARY_RELATIONS:
        if claim.arity != 2:
            return False
        predicate = BINARY_RELATIONS[claim.relation]
        return predicate(*claim.meanings) is not None  # type: ignore[operator]
    if claim.relation in TERNARY_RELATIONS:
        if claim.arity != 3:
            return False
        predicate = TERNARY_RELATIONS[claim.relation]
        return predicate(*claim.meanings) is not None  # type: ignore[operator]
    return False


def verify_all(claims: Iterable[Claim]) -> Tuple[int, Tuple[Claim, ...]]:
    """``(how many verified, the claims that failed)``."""
    materialised = tuple(claims)
    failures = tuple(claim for claim in materialised if not verify(claim))
    return len(materialised) - len(failures), failures
