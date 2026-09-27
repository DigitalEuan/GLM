"""A domain description, and the derivations a description is written in.

Why a description at all
------------------------
Every register in this package was built by hand from one recipe: carriers
whose coordinates are *derived* from something already held, a reading over
them, an audit of what the reading gains and gives up, a query that answers
where the register decides and refuses where it does not, and a machine-checked
statement of the part that is not a measurement.  Comparison classes, harmonics
and prices are that recipe applied three times.

This module makes the recipe's input an object.  A :class:`DomainSpec` is a
*description*: what the domain's objects are, which held quantity each
coordinate derives from, which coordinates recover the object, what a reading
of one object is, and what must be refused.  :mod:`glm_universal.recipe.build`
turns any such description into the carrier encoding, the layer chain, the
widening audit, the query surface and the refusal boundary, without knowing
what the domain is about.  ``RequestProject/GLM/Recipe.lean`` proves the part
of that path which is not a measurement.

Derivations and judgements
--------------------------
A description is written in :class:`Derivation`\\ s, and they compose: every
primitive takes either the name of a held fact or another derivation, so
``log_bucket(quotient("high", "low"), base=10)`` is a coordinate and not a
special case.  Two kinds are distinguished, and the distinction is *reported*
rather than hidden:

``derivation``
    A coordinate computed by one of the shared primitives listed in
    :data:`PRIMITIVES`.  These are the part of the recipe that generalises:
    the same primitive serves a frequency ratio, a quoted price and a
    comparison bracket.
``judgement``
    A rule specific to the domain, which has to be *stated*: that twelve-tone
    equal temperament is the tuning a step is measured against, that Euler's
    gradus weights a prime by ``p - 1``, that an interval within a tempered
    semitone of the unison is a comma.  A universal method should make these
    cheap to state and impossible to state twice; it should not pretend to
    eliminate them.  :func:`judgement` marks one, and the audit counts them
    against the derivations, so "this domain is described, not coded" is a
    measurement rather than a claim.

Exactness
---------
Every value a derivation produces is an ``int`` or a
:class:`fractions.Fraction`.  Nothing here constructs a float, and the
carriers the descriptions generate go through
:func:`glm_universal.data_objects.base.exact_vector`, which refuses one.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Union

__all__ = [
    "Facts", "Argument", "Derivation", "Coordinate", "Reading", "DomainSpec",
    "judgement", "value_of",
    "held", "numerator", "denominator", "product", "quotient", "difference",
    "midpoint", "affine_position", "p_adic_exponent", "prime_limit",
    "distinct_primes", "exponent_weight", "largest_exponent", "odd_part",
    "log_bucket", "vocabulary_index", "collection_size", "flag", "text_part",
    "maximum", "minimum", "indicator_equals", "indicator_between",
    "comparison_sign", "borrowed",
    "PRIMITIVES", "prime_exponents",
]

#: The held facts of one object: what the domain already has, before any
#: coordinate is derived.  Values are exact.
Facts = Mapping[str, Any]


# ===========================================================================
# 1.  A DERIVATION
# ===========================================================================

@dataclass(frozen=True)
class Derivation:
    """One rule for computing a coordinate from an object's held facts.

    ``primitive`` names the shared rule that produced it, or ``"judgement"``
    for a rule the domain has to state for itself.  ``argument`` renders the
    rule's arguments so a report can print the description rather than
    describe it.
    """

    primitive: str
    argument: str
    rule: Callable[[Facts], Any]

    def __call__(self, facts: Facts) -> Any:
        return self.rule(facts)

    @property
    def is_judgement(self) -> bool:
        return self.primitive == "judgement"

    def render(self) -> str:
        return (f"{self.primitive}({self.argument})" if self.argument
                else self.primitive)


#: What a primitive takes: the name of a held fact, or another derivation.
Argument = Union[str, Derivation]


def judgement(what: str, rule: Callable[[Facts], Any]) -> Derivation:
    """A rule this domain has to state for itself, named rather than hidden."""
    return Derivation(primitive="judgement", argument=what, rule=rule)


def value_of(argument: Argument, facts: Facts) -> Any:
    """Evaluate a primitive's argument against one object's held facts."""
    if isinstance(argument, Derivation):
        return argument(facts)
    try:
        return facts[argument]
    except KeyError as exc:
        raise KeyError(f"recipe: no held fact {argument!r} on this object; a "
                       f"description may only derive from what is held") \
            from exc


def _render(argument: Argument) -> str:
    return (argument.render() if isinstance(argument, Derivation)
            else str(argument))


def _exact(value: Any) -> Fraction:
    return Fraction(value)


def _collapse(value: Fraction) -> Any:
    return int(value) if value.denominator == 1 else value


# ===========================================================================
# 2.  THE SHARED PRIMITIVES
# ===========================================================================

def held(key: str) -> Derivation:
    """A held fact, taken as it stands."""
    return Derivation("held", key, lambda facts: value_of(key, facts))


def numerator(argument: Argument) -> Derivation:
    """The numerator of an exact rational, in lowest terms."""
    return Derivation("numerator", _render(argument),
                      lambda facts: _exact(value_of(argument,
                                                    facts)).numerator)


def denominator(argument: Argument) -> Derivation:
    """The denominator of an exact rational, in lowest terms."""
    return Derivation("denominator", _render(argument),
                      lambda facts: _exact(value_of(argument,
                                                    facts)).denominator)


def product(*arguments: Argument) -> Derivation:
    """The product of what its arguments derive."""
    def rule(facts: Facts) -> Any:
        out = Fraction(1)
        for argument in arguments:
            out *= _exact(value_of(argument, facts))
        return _collapse(out)
    return Derivation("product", ", ".join(_render(a) for a in arguments),
                      rule)


def quotient(top: Argument, bottom: Argument) -> Derivation:
    """One derived quantity over another."""
    def rule(facts: Facts) -> Any:
        return _collapse(_exact(value_of(top, facts))
                         / _exact(value_of(bottom, facts)))
    return Derivation("quotient", f"{_render(top)} / {_render(bottom)}", rule)


def difference(left: Argument, right: Argument) -> Derivation:
    """One derived quantity less another."""
    def rule(facts: Facts) -> Any:
        return _collapse(_exact(value_of(left, facts))
                         - _exact(value_of(right, facts)))
    return Derivation("difference", f"{_render(left)} - {_render(right)}",
                      rule)


def midpoint(low: Argument, high: Argument) -> Derivation:
    """Halfway between two derived quantities."""
    def rule(facts: Facts) -> Any:
        return _collapse((_exact(value_of(low, facts))
                          + _exact(value_of(high, facts))) / 2)
    return Derivation("midpoint", f"{_render(low)}, {_render(high)}", rule)


def affine_position(value: Argument, low: Argument,
                    high: Argument) -> Derivation:
    """Where a magnitude sits on the bracket ``[low, high]``, exactly.

    ``(value - low) / (high - low)``.  Unclamped: a magnitude outside the
    bracket has a position outside ``[0, 1]``, and the caller decides what
    that means rather than being handed a silently clipped number.
    """
    def rule(facts: Facts) -> Any:
        lo = _exact(value_of(low, facts))
        hi = _exact(value_of(high, facts))
        return _collapse((_exact(value_of(value, facts)) - lo) / (hi - lo))
    return Derivation("affine_position",
                      f"{_render(value)} in [{_render(low)}, "
                      f"{_render(high)}]", rule)


def prime_exponents(ratio: Fraction) -> Dict[int, int]:
    """The exponent of every prime in a positive exact rational."""
    ratio = Fraction(ratio)
    if ratio <= 0:
        raise ValueError("recipe: the ratio must be positive")
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


def p_adic_exponent(argument: Argument, prime: int) -> Derivation:
    """The exponent of one prime in an exact rational."""
    return Derivation("p_adic_exponent", f"{_render(argument)}, p = {prime}",
                      lambda facts: prime_exponents(
                          _exact(value_of(argument, facts))).get(prime, 0))


def prime_limit(argument: Argument) -> Derivation:
    """The largest prime dividing numerator or denominator; 1 for a unit."""
    def rule(facts: Facts) -> int:
        exponents = prime_exponents(_exact(value_of(argument, facts)))
        return max(exponents) if exponents else 1
    return Derivation("prime_limit", _render(argument), rule)


def distinct_primes(argument: Argument) -> Derivation:
    """How many primes divide numerator or denominator."""
    return Derivation("distinct_primes", _render(argument),
                      lambda facts: len(prime_exponents(
                          _exact(value_of(argument, facts)))))


def exponent_weight(argument: Argument) -> Derivation:
    """The sum of the absolute prime exponents of an exact rational."""
    return Derivation("exponent_weight", _render(argument),
                      lambda facts: sum(abs(e) for e in prime_exponents(
                          _exact(value_of(argument, facts))).values()))


def largest_exponent(argument: Argument) -> Derivation:
    """The largest absolute prime exponent of an exact rational."""
    def rule(facts: Facts) -> int:
        exponents = prime_exponents(_exact(value_of(argument, facts)))
        return max((abs(e) for e in exponents.values()), default=0)
    return Derivation("largest_exponent", _render(argument), rule)


def _odd_part(value: int) -> int:
    while value > 0 and value % 2 == 0:
        value //= 2
    return value


def odd_part(argument: Argument, part: str = "numerator") -> Derivation:
    """A rational's numerator or denominator with its factors of two removed."""
    if part not in ("numerator", "denominator"):
        raise ValueError("odd_part: part must be numerator or denominator")

    def rule(facts: Facts) -> int:
        ratio = _exact(value_of(argument, facts))
        return _odd_part(ratio.numerator if part == "numerator"
                         else ratio.denominator)
    return Derivation("odd_part", f"{_render(argument)}.{part}", rule)


def log_bucket(argument: Argument, base: int = 10) -> Derivation:
    """The integer ``k`` with ``base**k <= value < base**(k+1)``, exactly.

    Decided by integer comparison against powers of the base: no logarithm is
    evaluated and no float is constructed.  This is the rule the economics
    register's magnitude bucket and the comparison register's decimal scale
    each wrote out by hand, and ``RequestProject/GLM/LogBucket.lean`` proves
    it well defined.
    """
    if base < 2:
        raise ValueError("log_bucket: the base must be at least 2")

    def rule(facts: Facts) -> int:
        value = _exact(value_of(argument, facts))
        if value <= 0:
            raise ValueError("log_bucket: the value must be positive")
        k = 0
        while value >= Fraction(base) ** (k + 1):
            k += 1
        while value < Fraction(base) ** k:
            k -= 1
        return k
    return Derivation("log_bucket", f"{_render(argument)}, base {base}", rule)


def vocabulary_index(argument: Argument,
                     vocabulary: Callable[[], Sequence[Any]],
                     rendered: str = "") -> Derivation:
    """The position of a name in a fixed vocabulary.

    The vocabulary is a callable, so a register that grows is read at
    derivation time rather than frozen into the description.
    """
    def rule(facts: Facts) -> int:
        value = value_of(argument, facts)
        listed = list(vocabulary())
        try:
            return listed.index(value)
        except ValueError as exc:
            raise KeyError(f"recipe: {value!r} is not in the vocabulary this "
                           f"description names") from exc
    return Derivation("vocabulary_index", rendered or _render(argument), rule)


def collection_size(argument: Argument) -> Derivation:
    """How many items a collection has; ``0`` when it is absent."""
    def rule(facts: Facts) -> int:
        value = value_of(argument, facts)
        return 0 if value is None else len(value)
    return Derivation("collection_size", _render(argument), rule)


def flag(argument: Argument) -> Derivation:
    """A predicate as ``1`` or ``0``."""
    return Derivation("flag", _render(argument),
                      lambda facts: 1 if value_of(argument, facts) else 0)


def text_part(argument: Argument, separator: str, index: int) -> Derivation:
    """An integer read out of a name, by splitting it."""
    def rule(facts: Facts) -> int:
        return int(str(value_of(argument, facts)).split(separator)[index])
    return Derivation("text_part",
                      f"{_render(argument)}.split({separator!r})[{index}]",
                      rule)


def maximum(*arguments: Argument) -> Derivation:
    """The largest of what its arguments derive."""
    return Derivation("maximum", ", ".join(_render(a) for a in arguments),
                      lambda facts: max(value_of(a, facts)
                                        for a in arguments))


def minimum(*arguments: Argument) -> Derivation:
    """The smallest of what its arguments derive."""
    return Derivation("minimum", ", ".join(_render(a) for a in arguments),
                      lambda facts: min(value_of(a, facts)
                                        for a in arguments))


def indicator_equals(argument: Argument, target: Any) -> Derivation:
    """``1`` when a derived quantity equals a stated value, else ``0``."""
    return Derivation("indicator_equals", f"{_render(argument)} = {target}",
                      lambda facts: 1 if value_of(argument,
                                                  facts) == target else 0)


def indicator_between(argument: Argument, low: Any, high: Any,
                      include_high: bool = False) -> Derivation:
    """``1`` when a derived quantity lies in a stated bracket, else ``0``."""
    def rule(facts: Facts) -> int:
        value = _exact(value_of(argument, facts))
        upper = (value <= _exact(high)) if include_high \
            else (value < _exact(high))
        return 1 if (_exact(low) <= value and upper) else 0
    bracket = f"[{low}, {high}{']' if include_high else ')'}"
    return Derivation("indicator_between", f"{_render(argument)} in {bracket}",
                      rule)


def comparison_sign(argument: Argument, pivot: Any) -> Derivation:
    """``+1`` above a stated value, ``-1`` below it, ``0`` at it."""
    def rule(facts: Facts) -> int:
        value = _exact(value_of(argument, facts))
        target = _exact(pivot)
        return 1 if value > target else (-1 if value < target else 0)
    return Derivation("comparison_sign", f"{_render(argument)} vs {pivot}",
                      rule)


def borrowed(argument: Argument, read: Callable[[Any], Any],
             rendered: str) -> Derivation:
    """A coordinate read out of a register this domain does not own.

    This is the primitive that keeps the rule *nothing dimensional is typed
    twice*: a description may not restate a dimension, a domain index or a
    scale -- it names the held quantity and the register the value is read
    from, and ``rendered`` records which.
    """
    return Derivation("borrowed", rendered,
                      lambda facts: read(value_of(argument, facts)))


#: The shared primitives, by name.  A coordinate outside this list must be
#: stated with :func:`judgement`, and the audit counts it.
PRIMITIVES: Tuple[str, ...] = (
    "held", "numerator", "denominator", "product", "quotient", "difference",
    "midpoint", "affine_position", "p_adic_exponent", "prime_limit",
    "distinct_primes", "exponent_weight", "largest_exponent", "odd_part",
    "log_bucket", "vocabulary_index", "collection_size", "flag", "text_part",
    "maximum", "minimum", "indicator_equals", "indicator_between",
    "comparison_sign", "borrowed",
)


# ===========================================================================
# 3.  A COORDINATE, A READING, A DESCRIPTION
# ===========================================================================

@dataclass(frozen=True)
class Coordinate:
    """One coordinate of a domain: its name, its rule, and where it came from.

    ``source`` names the held quantity or the register the value is read out
    of.  It is prose, but prose with a job: the rule that nothing dimensional
    is typed twice is only checkable if every coordinate says what it derives
    from.
    """

    name: str
    rule: Derivation
    source: str

    @property
    def kind(self) -> str:
        return "judgement" if self.rule.is_judgement else "derivation"

    def of(self, facts: Facts) -> Any:
        return self.rule(facts)


@dataclass(frozen=True)
class Reading:
    """A reading of an object: the coordinates one layer of the domain sees."""

    name: str
    coordinates: Tuple[str, ...]
    gloss: str = ""


@dataclass(frozen=True)
class DomainSpec:
    """The declarative description of one domain.

    Parameters
    ----------
    name
        The domain's name, which becomes the carriers' ``domain`` tag.
    facts
        Returns the held facts of every object, in register order.  Each
        mapping must carry ``"name"``.
    coordinates
        The coordinates, in carrier order.  There must be 24: the carrier
        dimension is fixed by the Leech lattice, not by convention.
    keys
        The coordinates that recover an object.
    rebuild
        From the key coordinates' values, together with the labels, back to the
        held facts.  This is what makes a description a *codec* rather than a
        projection.
    labels
        Held facts the carrier does **not** hold -- the object's name, and any
        prose beside it.  They are carried, not derived, and the audit reports
        them: a register's names are not recoverable from its carriers, which
        is the missing coordinate ``NameCoordinate.lean`` is about, not an
        omission in the description.
    readings
        The layer chain, coarsest first.  The audit checks that each reading
        refines the one below it and reports what it gains.
    refuses
        Coordinate names this domain does **not** hold, kept as witnesses so
        the refusal boundary is exercised rather than asserted.
    native
        From held facts back to the domain's own object -- an ``Interval``, a
        ``PriceRecord``, a ``ComparisonClass``.
    natives
        The shipped register as the domain's own objects: what the rebuilt
        ones are compared against.
    shipped
        The register's carriers as the hand-written module produces them.
    figures
        Named figure functions, recomputed against the regenerated register.
    figures_exhaustive
        Further figures, run only when the exhaustive cases are asked for --
        the ones that cost minutes rather than milliseconds.
    install
        A context manager factory: given the regenerated objects, put them
        where the shipped reasoning modules read from, and restore afterwards.
    """

    name: str
    facts: Callable[[], Tuple[Facts, ...]]
    coordinates: Tuple[Coordinate, ...]
    keys: Tuple[str, ...]
    rebuild: Callable[[Mapping[str, Any], Mapping[str, Any]], Facts]
    readings: Tuple[Reading, ...]
    labels: Tuple[str, ...] = ("name",)
    refuses: Tuple[str, ...] = ()
    native: Optional[Callable[[Facts], Any]] = None
    natives: Optional[Callable[[], Tuple[Any, ...]]] = None
    shipped: Optional[Callable[[], Tuple[Tuple[Any, ...], ...]]] = None
    figures: Tuple[Tuple[str, Callable[[], Any]], ...] = ()
    figures_exhaustive: Tuple[Tuple[str, Callable[[], Any]], ...] = ()
    install: Optional[Callable[[Sequence[Any]], Any]] = None
    gloss: str = ""

    def __post_init__(self) -> None:
        names = [c.name for c in self.coordinates]
        if len(set(names)) != len(names):
            raise ValueError(f"{self.name}: a coordinate is described twice")
        for key in self.keys:
            if key not in names:
                raise ValueError(f"{self.name}: key {key!r} is not a "
                                 f"coordinate of the description")
        for reading in self.readings:
            for coordinate in reading.coordinates:
                if coordinate not in names:
                    raise ValueError(
                        f"{self.name}: reading {reading.name!r} names "
                        f"{coordinate!r}, which the description does not "
                        f"derive")
        for refused in self.refuses:
            if refused in names:
                raise ValueError(f"{self.name}: {refused!r} is listed as "
                                 f"refused but is derived")

    # -- the description, read ---------------------------------------------

    @property
    def layout(self) -> Tuple[str, ...]:
        """The coordinate names, in carrier order."""
        return tuple(c.name for c in self.coordinates)

    def coordinate(self, name: str) -> Coordinate:
        for c in self.coordinates:
            if c.name == name:
                return c
        raise KeyError(f"{self.name}: no coordinate {name!r}")

    def derives(self, name: str) -> bool:
        """Whether this description holds a coordinate -- the refusal test."""
        return name in self.layout

    @property
    def judgements(self) -> Tuple[str, ...]:
        """The coordinates this domain had to state for itself."""
        return tuple(c.name for c in self.coordinates
                     if c.kind == "judgement")

    @property
    def primitives_used(self) -> Tuple[str, ...]:
        """Which shared primitives the description is written in."""
        return tuple(sorted({c.rule.primitive for c in self.coordinates
                             if c.kind == "derivation"}))
