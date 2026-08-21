"""``glm_universal.reasoning.verifier`` -- multi-plane equation audit.

What it does
------------
Decides the 222 scalar-magnitude and 71 full-meaning tensor relations of the
660-concept physics register, **not** as a boolean but as a localisation: each
relation is turned into a pair of exact 24-coordinate carriers, the two
carriers are expanded into their 2-adic digit planes, and any disagreement is
attributed to the 31 named MOG facets that contain the differing bits.

The three layers, kept separate on purpose
------------------------------------------
1. **The operator algebra** (:class:`Sense`).  A physical quantity is ten
   exact rational EXT10 exponents, a decimal scale, a tensor rank, and the
   ``P``, ``T``, ``C`` gradings.  Products add exponents; ``dot`` contracts two
   ranks away; ``moment`` is the cross product with one radian consumed; the
   differential operators are all built from a single ``nabla`` with
   ``L^-1``, rank 1, ``P``-odd, so their rank and parity bookkeeping is forced
   rather than tabulated.
2. **The parser** (:func:`parse`).  A small recursive-descent grammar over
   ``* / ^ ( ) ,`` plus named operators, with exact rational exponents and
   numeric literals restricted to powers of ten (the register tracks the
   decimal scale exactly and refuses to absorb any other constant).
3. **The substrate audit** (:func:`verify_relation`).  Both sides become
   carriers in the physics layout; ``substrate.digit_stack.verify_equation``
   compares them plane by plane and blames facets.

Layer 3 is the point.  Layers 1 and 2 could in principle be replaced by a
single ``==``; running them through the digit stack is what makes a failure
*addressable* -- it says which digit plane and which brick, column, row or
cube face the discrepancy lives in, which is the granularity the rest of
GLM-3+ reasons at.

Two semantics, both exact
-------------------------
``"scalar"``
    the ten EXT10 exponents and the decimal scale must agree.  This is what a
    table of units asserts.
``"full"``
    additionally the tensor rank and the effective ``P``, ``T``, ``C``
    gradings must agree.  ``energy = force * position`` is true in the scalar
    sense and false in the full sense (the right-hand side is a rank-2
    tensor); ``energy = dot(force, position)`` is true in both.

The relation statements are read from the frozen snapshot
``reasoning/_data/physics_relations.json``.  Only the statements are frozen:
every verdict below is recomputed here from ``glm_universal``'s own
660-concept register.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from math import gcd
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..data_objects import physics as do_physics
from ..substrate import digit_stack

__all__ = [
    "RelationError", "Sense", "SCALAR_SENSE", "NABLA", "OPERATORS",
    "RELATION_LAYOUT", "SEMANTICS",
    "tokenise", "parse", "resolve_name", "sense_of_quantity",
    "sense_carrier", "load_relations", "relation_table",
    "RelationVerdict", "verify_relation", "verify_expression_pair",
    "verify_all", "facet_attribution_census", "verifier_report",
]

_DATA = Path(__file__).resolve().parent / "_data" / "physics_relations.json"

#: EXT10 axis order, taken from the register rather than restated.
AXES: Tuple[str, ...] = do_physics.AXES_EXT10
N_AXES = len(AXES)

#: The 24 coordinates a relation side occupies.  The first 17 mirror the
#: physics data-object layout exactly, so a relation carrier and a register
#: carrier are comparable coordinate by coordinate; the tensor character
#: occupies four further slots and the remainder is reserved zero.  The
#: nominal ``kind`` and ``domain`` labels of the register are deliberately
#: absent: the operator algebra does not propagate them, so including them
#: would make every derived expression differ from every named quantity for a
#: reason that is bookkeeping rather than physics.
RELATION_LAYOUT: Tuple[str, ...] = (
    tuple(f"ext10.{a}" for a in AXES)
    + tuple(f"si7.{a}" for a in do_physics.AXES_SI7)
    + ("scale", "rank", "p", "t_parity", "c_parity", "reserved0", "reserved1")
)
assert len(RELATION_LAYOUT) == 24

#: The two comparison semantics and the coordinates each one compares.
SEMANTICS: Dict[str, Tuple[str, ...]] = {
    "scalar": RELATION_LAYOUT[:17] + ("scale",),
    "full": RELATION_LAYOUT[:22],
}


class RelationError(ValueError):
    """Raised on a malformed expression or an unknown concept name."""


# ===========================================================================
# 1.  THE OPERATOR ALGEBRA
# ===========================================================================

@dataclass(frozen=True)
class Sense:
    """The exact physical content of an expression.

    Attributes
    ----------
    exps
        Ten rational EXT10 exponents, in :data:`AXES` order.
    scale
        The decimal scale: the quantity is ``10^scale`` SI coherent units.
    rank
        Tensor rank: 0 scalar, 1 vector, 2 second-rank, and so on.
    p
        Space-inversion parity, 0 or 1.
    t, c
        Time-reversal and charge-conjugation *anomalies*, 0 or 1.  The
        gradings themselves are functions of the exponents (see
        :meth:`t_parity`); the anomaly records a quantity whose real behaviour
        departs from that convention.
    """

    exps: Tuple[Fraction, ...]
    scale: Fraction = Fraction(0)
    rank: int = 0
    p: int = 0
    t: int = 0
    c: int = 0

    def __post_init__(self) -> None:
        if len(self.exps) != N_AXES:
            raise ValueError(f"Sense: {N_AXES} exponents required")
        object.__setattr__(self, "exps", tuple(Fraction(e) for e in self.exps))
        object.__setattr__(self, "scale", Fraction(self.scale))
        for name in ("p", "t", "c"):
            if getattr(self, name) not in (0, 1):
                raise ValueError(f"Sense: {name} must be 0 or 1")

    # -- construction -------------------------------------------------------

    @staticmethod
    def make(scale=0, rank: int = 0, p: int = 0, t: int = 0, c: int = 0,
             **exponents) -> "Sense":
        """Keyword constructor: ``Sense.make(L=2, M=1, T=-2)`` is an energy."""
        e = [Fraction(0)] * N_AXES
        for key, value in exponents.items():
            if key not in AXES:
                raise ValueError(f"Sense.make: unknown axis {key!r}")
            e[AXES.index(key)] = Fraction(value)
        return Sense(tuple(e), Fraction(scale), rank, p, t, c)

    def exponent(self, axis: str) -> Fraction:
        """One exponent, by axis name."""
        return self.exps[AXES.index(axis)]

    # -- the group operations ----------------------------------------------

    def __add__(self, other: "Sense") -> "Sense":
        """The tensor product: exponents, scale and rank add; parities add mod 2."""
        return Sense(tuple(a + b for a, b in zip(self.exps, other.exps)),
                     self.scale + other.scale, self.rank + other.rank,
                     (self.p + other.p) % 2, (self.t + other.t) % 2,
                     (self.c + other.c) % 2)

    def __neg__(self) -> "Sense":
        return Sense(tuple(-a for a in self.exps), -self.scale, -self.rank,
                     self.p, self.t, self.c)

    def __sub__(self, other: "Sense") -> "Sense":
        return self + (-other)

    def contract(self, other: "Sense") -> "Sense":
        """Full contraction (``dot``): the tensor product with rank ``- 2``."""
        if self.rank < 1 or other.rank < 1:
            raise RelationError("dot needs two quantities of rank >= 1")
        prod = self + other
        return Sense(prod.exps, prod.scale, prod.rank - 2, prod.p, prod.t,
                     prod.c)

    def cross(self, other: "Sense") -> "Sense":
        """The plain cross product of two rank-1 quantities; result rank 1."""
        if self.rank != 1 or other.rank != 1:
            raise RelationError("cross needs two rank-1 quantities")
        prod = self + other
        return Sense(prod.exps, prod.scale, 1, prod.p, prod.t, prod.c)

    def moment(self, other: "Sense") -> "Sense":
        """The rotational cross product: :meth:`cross` with one radian consumed.

        Torque ``r x F`` is an energy *per radian* and angular momentum
        ``r x p`` an action per radian, while ``E x H`` consumes no radian.
        Once the plane angle is a dimension in its own right the two uses of
        ``a x b`` stop being the same operation, and this is the one that
        carries ``A^-1``.
        """
        prod = self.cross(other)
        e = list(prod.exps)
        e[AXES.index("A")] -= 1
        return Sense(tuple(e), prod.scale, 1, prod.p, prod.t, prod.c)

    def power(self, q) -> "Sense":
        """Raise to an exact rational power.

        A fractional power is legal only for a rank-0, ``P``-even quantity:
        there is no square root of a pseudovector or of a rank-2 tensor, and
        the ``Z/2`` anomalies have no square root either, so they are erased.
        """
        q = Fraction(q)
        if q.denominator != 1:
            if self.rank != 0:
                raise RelationError(
                    f"fractional power {q} of a rank-{self.rank} quantity")
            if self.p != 0:
                raise RelationError(f"fractional power {q} of a P-odd quantity")
            new_rank, par = 0, (0, 0, 0)
        else:
            n = int(q)
            new_rank = self.rank * n
            par = ((self.p * n) % 2, (self.t * n) % 2, (self.c * n) % 2)
        return Sense(tuple(a * q for a in self.exps), self.scale * q, new_rank,
                     par[0], par[1], par[2])

    # -- gradings -----------------------------------------------------------

    def t_parity(self) -> Optional[int]:
        """Effective ``T`` grading ``(e_T + e_I + t) mod 2``, or ``None``.

        ``None`` when the ``T`` or ``I`` exponent is fractional, where the
        convention does not apply -- reported rather than silently rounded.
        """
        et, ei = self.exponent("T"), self.exponent("I")
        if et.denominator != 1 or ei.denominator != 1:
            return None
        return (int(et) + int(ei) + self.t) % 2

    def c_parity(self) -> Optional[int]:
        """Effective ``C`` grading ``(e_I + c) mod 2``, or ``None``."""
        ei = self.exponent("I")
        if ei.denominator != 1:
            return None
        return (int(ei) + self.c) % 2

    def denominator(self) -> int:
        """Least common denominator of the scale and the ten exponents."""
        d = self.scale.denominator
        for e in self.exps:
            d = d * e.denominator // gcd(d, e.denominator)
        return d


#: The dimensionless, unscaled, rank-0, parity-even element.
SCALAR_SENSE = Sense((Fraction(0),) * N_AXES)

#: The gradient operator: one inverse length, rank 1, ``P``-odd.  Every
#: differential operator below is built from it.
NABLA = Sense.make(L=-1, rank=1, p=1)

_TIME = Sense.make(T=1)
_VOLUME = Sense.make(L=3)


def _laplacian(x: Sense) -> Sense:
    return NABLA.contract(NABLA + x)


#: name -> (arity, implementation).  The set matches the frozen snapshot's
#: ``operators`` block, which :func:`load_relations` checks.
OPERATORS: Dict[str, Tuple[int, Callable[..., Sense]]] = {
    "dot":         (2, lambda a, b: a.contract(b)),
    "cross":       (2, lambda a, b: a.cross(b)),
    "moment":      (2, lambda a, b: a.moment(b)),
    "grad":        (1, lambda x: NABLA + x),
    "div":         (1, lambda x: NABLA.contract(x)),
    "curl":        (1, lambda x: NABLA.cross(x)),
    "rot":         (1, lambda x: NABLA.moment(x)),
    "laplacian":   (1, _laplacian),
    "ddt":         (1, lambda x: x - _TIME),
    "integral_dt": (1, lambda x: x + _TIME),
    "integral_dV": (1, lambda x: x + _VOLUME),
}


# ===========================================================================
# 2.  THE REGISTER AND THE PARSER
# ===========================================================================

@lru_cache(maxsize=1)
def load_relations() -> Dict[str, object]:
    """The frozen relation statements, with their aliases and operator list.

    The snapshot's operator names are checked against :data:`OPERATORS`, so a
    statement using an operator this module does not implement is caught at
    load time rather than being silently mis-parsed.
    """
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    listed = set(raw["operators"])
    ours = set(OPERATORS)
    if listed != ours:
        raise AssertionError(
            f"verifier: the frozen snapshot lists operators {sorted(listed)} "
            f"but this module implements {sorted(ours)}")
    for name, arity in raw["operators"].items():
        if OPERATORS[name][0] != arity:
            raise AssertionError(f"verifier: arity mismatch for {name!r}")
    if len(raw["scalar_relations"]) != raw["scalar_count"]:
        raise AssertionError("verifier: scalar relation count mismatch")
    if len(raw["tensor_relations"]) != raw["tensor_count"]:
        raise AssertionError("verifier: tensor relation count mismatch")
    return raw


def relation_table(kind: str) -> Tuple[Tuple[str, str], ...]:
    """``"scalar"`` or ``"tensor"`` relation statements, as ``(lhs, rhs)``."""
    raw = load_relations()
    if kind == "scalar":
        return tuple((a, b) for a, b in raw["scalar_relations"])
    if kind == "tensor":
        return tuple((a, b) for a, b in raw["tensor_relations"])
    raise KeyError(f"relation_table: kind must be 'scalar' or 'tensor', "
                   f"got {kind!r}")


@lru_cache(maxsize=1)
def _alias_table() -> Mapping[str, str]:
    return dict(load_relations()["aliases"])       # type: ignore[arg-type]


def resolve_name(name: str) -> Optional[do_physics.Quantity]:
    """A register quantity by name or by frozen alias; ``None`` if unknown."""
    try:
        return do_physics.quantity_by_name(name)
    except KeyError:
        pass
    target = _alias_table().get(name)
    if target is None:
        return None
    try:
        return do_physics.quantity_by_name(target)
    except KeyError:
        return None


def sense_of_quantity(q: do_physics.Quantity) -> Sense:
    """The :class:`Sense` of a register quantity."""
    return Sense(tuple(q.exps_ext10), q.scale, q.rank, q.p, q.t, q.c)


_PUNCT = set("*/^(),")


def tokenise(text: str) -> List[str]:
    """Split an expression into names, numbers, operators and punctuation."""
    out: List[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch in _PUNCT or ch in "+-":
            out.append(ch)
            i += 1
        elif ch.isdigit() or ch == ".":
            j = i
            while j < n and (text[j].isdigit() or text[j] == "."):
                j += 1
            out.append(text[i:j])
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            out.append(text[i:j])
            i = j
        else:
            raise RelationError(f"unexpected character {ch!r} in {text!r}")
    return out


class _Parser:
    """Recursive descent over ``expr := term (('*'|'/') term)*``."""

    def __init__(self, tokens: Sequence[str]) -> None:
        self.tokens = list(tokens)
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> str:
        tok = self.peek()
        if tok is None:
            raise RelationError("unexpected end of expression")
        self.pos += 1
        return tok

    def expect(self, tok: str) -> None:
        got = self.next()
        if got != tok:
            raise RelationError(f"expected {tok!r}, found {got!r}")

    def expr(self) -> Sense:
        value = self.term()
        while self.peek() in ("*", "/"):
            op = self.next()
            rhs = self.term()
            value = value + rhs if op == "*" else value - rhs
        return value

    def term(self) -> Sense:
        value = self.atom()
        while self.peek() == "^":
            self.next()
            value = value.power(self.exponent())
        return value

    def atom(self) -> Sense:
        tok = self.next()
        if tok == "(":
            value = self.expr()
            self.expect(")")
            return value
        if tok in ("-", "+"):
            raise RelationError(
                "a leading sign is not a dimensional operation; use an "
                "exponent such as ^-1")
        if tok[0].isdigit() or tok[0] == ".":
            return _numeric(tok)
        if tok in OPERATORS and self.peek() == "(":
            return self.call(tok)
        q = resolve_name(tok)
        if q is None:
            raise RelationError(f"unknown concept {tok!r}")
        return sense_of_quantity(q)

    def call(self, name: str) -> Sense:
        arity, fn = OPERATORS[name]
        self.expect("(")
        args = [self.expr()]
        while self.peek() == ",":
            self.next()
            args.append(self.expr())
        self.expect(")")
        if len(args) != arity:
            raise RelationError(
                f"{name} takes {arity} argument(s), {len(args)} given")
        return fn(*args)

    def exponent(self) -> Fraction:
        tok = self.next()
        sign = Fraction(1)
        while tok in ("-", "+"):
            if tok == "-":
                sign = -sign
            tok = self.next()
        if tok == "(":
            value = self._rational_inside()
            self.expect(")")
            return sign * value
        return sign * _rational(tok)

    def _rational_inside(self) -> Fraction:
        tok = self.next()
        sign = Fraction(1)
        while tok in ("-", "+"):
            if tok == "-":
                sign = -sign
            tok = self.next()
        value = sign * _rational(tok)
        while self.peek() in ("/", "*"):
            op = self.next()
            nxt = self.next()
            s2 = Fraction(1)
            while nxt in ("-", "+"):
                if nxt == "-":
                    s2 = -s2
                nxt = self.next()
            r = s2 * _rational(nxt)
            value = value / r if op == "/" else value * r
        return value


def _rational(tok: str) -> Fraction:
    try:
        return Fraction(tok)
    except (ValueError, ZeroDivisionError):
        raise RelationError(f"{tok!r} is not an exact rational exponent") from None


def _power_of_ten(value: Fraction) -> Optional[int]:
    if value == 1:
        return 0
    if value > 1:
        n, v = 0, value
        while v % 10 == 0:
            v //= 10
            n += 1
        return n if v == 1 else None
    inv = 1 / value
    n = _power_of_ten(inv)
    return None if n is None else -n


def _numeric(tok: str) -> Sense:
    """A numeric literal, legal only when it is an exact power of ten.

    The register tracks the decimal scale exactly; absorbing any other
    constant would turn an exact statement into an approximate one.
    """
    try:
        value = Fraction(tok)
    except ValueError:
        raise RelationError(f"{tok!r} is not a number") from None
    if value <= 0:
        raise RelationError(f"numeric factor {tok} must be positive")
    exponent = _power_of_ten(value)
    if exponent is None:
        raise RelationError(
            f"numeric factor {tok} is not a power of ten; the register tracks "
            f"the decimal scale exactly and refuses to absorb other constants")
    return Sense(SCALAR_SENSE.exps, Fraction(exponent))


def parse(text: str) -> Sense:
    """Parse an expression into an exact :class:`Sense`."""
    tokens = tokenise(text)
    if not tokens:
        raise RelationError("empty expression")
    p = _Parser(tokens)
    value = p.expr()
    if p.peek() is not None:
        raise RelationError(f"trailing tokens in {text!r}: {p.tokens[p.pos:]}")
    return value


# ===========================================================================
# 3.  CARRIERS AND THE MULTI-PLANE AUDIT
# ===========================================================================

def sense_carrier(sense: Sense, semantics: str = "full") -> Tuple[Fraction, ...]:
    """The 24-coordinate carrier of a :class:`Sense`, in :data:`RELATION_LAYOUT`.

    Under ``"scalar"`` semantics the tensor-character slots are zeroed, so the
    audit compares exactly what a scalar-magnitude relation asserts and the
    facet attribution of a scalar failure cannot be polluted by a rank or
    parity difference that the statement never claimed.

    A ``None`` grading -- which happens when a fractional ``T`` or ``I``
    exponent puts the quantity outside the convention -- is encoded as ``-1``,
    a value no genuine grading takes, so the two cases stay distinguishable.
    """
    if semantics not in SEMANTICS:
        raise KeyError(f"sense_carrier: semantics must be one of "
                       f"{sorted(SEMANTICS)}, got {semantics!r}")
    carrier: List[Fraction] = []
    carrier.extend(sense.exps)                                    # 0..9
    carrier.extend(sense.exps[:7])                                # 10..16
    carrier.append(sense.scale)                                   # 17
    if semantics == "full":
        tp, cp = sense.t_parity(), sense.c_parity()
        carrier.append(Fraction(sense.rank))                      # 18
        carrier.append(Fraction(sense.p))                         # 19
        carrier.append(Fraction(-1 if tp is None else tp))        # 20
        carrier.append(Fraction(-1 if cp is None else cp))        # 21
    else:
        carrier.extend([Fraction(0)] * 4)
    carrier.extend([Fraction(0), Fraction(0)])                    # 22, 23
    assert len(carrier) == 24
    return tuple(carrier)


def _joint_stack_parameters(lhs: Sequence[Fraction],
                            rhs: Sequence[Fraction]) -> Tuple[int, int]:
    """``(offset, depth)`` admissible for both sides over a common denominator.

    ``verify_equation`` pre-scales both carriers by their common denominator
    before stacking, so the parameters must be fitted to the *scaled*
    coordinates, not the raw ones.
    """
    den = 1
    for v in list(lhs) + list(rhs):
        den = den * Fraction(v).denominator // gcd(den, Fraction(v).denominator)
    # verify_equation clears each side separately and multiplies the two
    # denominators through their lcm, which is the lcm computed above.
    max_abs = 0
    for v in list(lhs) + list(rhs):
        scaled = Fraction(v) * den
        max_abs = max(max_abs, abs(int(scaled)))
    return digit_stack.derive_stack_parameters(max_abs)


@dataclass(frozen=True)
class RelationVerdict:
    """The audit of one physical relation, plane by plane and facet by facet."""

    lhs: str
    rhs: str
    semantics: str
    holds: bool
    parse_error: Optional[str]
    lhs_dimension: Optional[str] = None
    rhs_dimension: Optional[str] = None
    lhs_rank: Optional[int] = None
    rhs_rank: Optional[int] = None
    failing_planes: Tuple[int, ...] = ()
    first_failing_plane: Optional[int] = None
    blamed_facets: Tuple[str, ...] = ()
    difference_coordinates: Tuple[str, ...] = ()
    depth: Optional[int] = None
    offset: Optional[int] = None

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "lhs": self.lhs, "rhs": self.rhs, "semantics": self.semantics,
            "holds": self.holds, "parse_error": self.parse_error,
            "lhs_dimension": self.lhs_dimension,
            "rhs_dimension": self.rhs_dimension,
            "lhs_rank": self.lhs_rank, "rhs_rank": self.rhs_rank,
            "failing_planes": list(self.failing_planes),
            "first_failing_plane": self.first_failing_plane,
            "blamed_facets": list(self.blamed_facets),
            "difference_coordinates": list(self.difference_coordinates),
            "depth": self.depth, "offset": self.offset,
        }


def verify_expression_pair(lhs_text: str, rhs_text: str,
                           semantics: str = "full") -> RelationVerdict:
    """Audit one equation given as two expression strings.

    Either side may be a bare concept name or a full expression, which is how
    a field equation such as ``ddt(temperature) = thermal_diffusivity *
    laplacian(temperature)`` is stated.
    """
    if semantics not in SEMANTICS:
        raise KeyError(f"verify_expression_pair: unknown semantics "
                       f"{semantics!r}")
    try:
        left = parse(lhs_text)
        right = parse(rhs_text)
    except RelationError as exc:
        return RelationVerdict(lhs=lhs_text, rhs=rhs_text, semantics=semantics,
                               holds=False, parse_error=str(exc))

    lc = sense_carrier(left, semantics)
    rc = sense_carrier(right, semantics)
    offset, depth = _joint_stack_parameters(lc, rc)
    verdict = digit_stack.verify_equation(lc, rc, depth=depth, offset=offset,
                                          basis="standard")

    differing = tuple(RELATION_LAYOUT[i] for i in range(24) if lc[i] != rc[i])
    return RelationVerdict(
        lhs=lhs_text, rhs=rhs_text, semantics=semantics,
        holds=verdict.holds, parse_error=None,
        lhs_dimension=do_physics.dimension_string(left.exps, "EXT10"),
        rhs_dimension=do_physics.dimension_string(right.exps, "EXT10"),
        lhs_rank=left.rank, rhs_rank=right.rank,
        failing_planes=verdict.failing_planes,
        first_failing_plane=verdict.first_failing_plane,
        blamed_facets=verdict.blamed_facets,
        difference_coordinates=differing,
        depth=depth, offset=offset)


def verify_relation(relation: Tuple[str, str],
                    semantics: str = "full") -> RelationVerdict:
    """Audit one ``(lhs, rhs)`` statement from the frozen tables."""
    return verify_expression_pair(relation[0], relation[1], semantics)


def verify_all(kind: str = "scalar",
               semantics: Optional[str] = None) -> Dict[str, object]:
    """Audit a whole relation table and summarise.

    ``semantics`` defaults to the one the table is stated in: ``"scalar"`` for
    the 222 scalar-magnitude laws, ``"full"`` for the 71 tensor laws.  Passing
    ``"full"`` for the scalar table is the interesting cross-check -- it asks
    how many unit-table statements are also exact at the level of rank and
    parity, and the answer is fewer, which is the point of having two
    semantics.
    """
    table = relation_table(kind)
    if semantics is None:
        semantics = "scalar" if kind == "scalar" else "full"
    verdicts = [verify_relation(r, semantics) for r in table]
    failures = [v for v in verdicts if not v.holds]
    parse_errors = [v for v in verdicts if v.parse_error]
    return {
        "kind": kind,
        "semantics": semantics,
        "checked": len(verdicts),
        "held": len(verdicts) - len(failures),
        "failed": len(failures),
        "parse_errors": len(parse_errors),
        "all_hold": not failures,
        "verdicts": verdicts,
        "failures": [v.as_dict() for v in failures],
    }


def facet_attribution_census(kind: str = "scalar",
                             semantics: Optional[str] = None
                             ) -> Dict[str, object]:
    """How the discrepancies of a table distribute over the 31 MOG facets.

    Every one of the 31 named facets appears in the output, with count zero
    when nothing was attributed to it, so a reader can tell "no discrepancy
    there" from "facet not considered".
    """
    result = verify_all(kind, semantics)
    counts = {name: 0 for name in digit_stack.FACETS}
    plane_counts: Dict[int, int] = {}
    for verdict in result["verdicts"]:                # type: ignore[union-attr]
        for facet in verdict.blamed_facets:
            counts[facet] += 1
        for plane in verdict.failing_planes:
            plane_counts[plane] = plane_counts.get(plane, 0) + 1
    return {
        "kind": result["kind"],
        "semantics": result["semantics"],
        "checked": result["checked"],
        "held": result["held"],
        "failed": result["failed"],
        "n_facets": len(counts),
        "facets_blamed": sum(1 for v in counts.values() if v),
        "facet_counts": dict(sorted(counts.items())),
        "failing_plane_counts": dict(sorted(plane_counts.items())),
    }


def verifier_report() -> Dict[str, object]:
    """Both tables under both semantics, computed on demand.

    Four numbers, none of them quoted: the scalar table under scalar
    semantics, the scalar table under full semantics (strictly harder), the
    tensor table under full semantics, and the facet census of whichever runs
    produced discrepancies.
    """
    out: Dict[str, object] = {}
    for kind, semantics in (("scalar", "scalar"), ("scalar", "full"),
                            ("tensor", "full")):
        key = f"{kind}_relations_under_{semantics}_semantics"
        result = verify_all(kind, semantics)
        out[key] = {
            "checked": result["checked"],
            "held": result["held"],
            "failed": result["failed"],
            "parse_errors": result["parse_errors"],
            "failures": result["failures"][:20],
        }
    out["facet_census_scalar_table_full_semantics"] = \
        facet_attribution_census("scalar", "full")
    out["n_named_facets"] = len(digit_stack.FACETS)
    return out
