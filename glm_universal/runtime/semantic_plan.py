"""``glm_universal.runtime.semantic_plan`` -- typed question plans.

Why this module exists
----------------------
The pre-registered language probe (:data:`glm_universal.reasoning.blockers.
PROBE`) asked through :meth:`GeometricSession.ask` scores two correct of
twenty, while the probe oracle and the field-surface, ordering and extremum
rounds showed that the system *holds* the answer to most of the other
eighteen behind its formal grammar: ``field atomic_weight_u of carbon``
answers where *what is the atomic weight of carbon?* is refused.  Widening the
vocabulary was measured and moved nothing.  What is missing is a typed bridge
from a phrasing to an operation the machine already has.

This module is that bridge, and it is deliberately *not* a parser that
answers.  It turns a question into zero or more **typed plans** and lets the
existing operations decide which of them hold:

1. **Frames.**  A fixed, ordered table of templates (:data:`FRAMES`), each of
   which recognises one *shape* of question and emits a :class:`Plan`: an
   intent, typed slots (a row, a field, a table, a number, a unit), and for
   every slot the words that licensed it and the grounding rule that turned
   them into a name.  A frame never guesses a slot it cannot ground.
2. **Grounding.**  A row slot is grounded against the field surface's own
   aliases, a field slot against the fields *that row actually answers to*
   (by the register's own field names read as words, and a small declared
   synonym table :data:`FIELD_SYNONYMS`), a unit against the declared exact
   unit table :data:`UNITS`.  A slot that grounds to nothing produces no plan.
3. **Licensing.**  Every plan is executed -- a formal query through the
   session, or an exact computation here -- and a plan is *licensed* when it
   solves.  The answer is given only when the licensed plans agree on one
   value; when two licensed plans disagree the question is refused as
   ambiguous with both readings named (:func:`accept`).  When no plan is
   licensed, the question falls through to the grammar exactly as
   :meth:`GeometricSession.ask` would have answered it, so the planned path
   never refuses what the bare path answered unless two readings disagree.

What it adds that is not a translation
--------------------------------------
Two frames compute rather than route, and they are the derivation half of the
round: exact integer arithmetic (sums, products, quotients as exact
rationals, primality with a factor as witness, gcd, lcm) and conversion
between units whose relation is an exact *definition* -- the 1959
international yard and pound, the SI prefixes -- declared with its source in
:data:`UNITS`.  A conversion between two dimensions, a division by zero, a
primality question about a non-integer, is refused with the precondition that
failed rather than answered.

Exactness
---------
No float is constructed.  Every number is an ``int`` or a
:class:`~fractions.Fraction`; a non-terminating quotient is rendered as
``n/d`` beside a decimal *rounded half-even to a stated number of places*, and
the rounding is said, never hidden.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Callable, Dict, List, Mapping, Optional, Sequence, Tuple)

from ..reasoning import certificates as _cert
from .fields import FieldError, exact_decimal
from .parser import normalise, parse_query
from .solution import Solution, Step

__all__ = [
    "Slot", "Plan", "Outcome", "Planned", "FIELD_SYNONYMS", "UNITS",
    "COMPARATIVES", "FRAMES", "clean", "decimal_places", "prime_witness",
    "accept", "candidate_plans", "plan_question", "ask_planned",
]


# ===========================================================================
# 1.  THE TYPED REPRESENTATION
# ===========================================================================

@dataclass(frozen=True)
class Slot:
    """One typed slot of a plan, and what licensed it.

    ``role`` is the slot's type (``row``, ``field``, ``table``, ``number``,
    ``unit``, ``end``, ``comparative``); ``value`` the grounded name;
    ``words`` the words of the question it was read from; ``rule`` the
    grounding rule that turned the words into the name.
    """

    role: str
    value: str
    words: str
    rule: str

    def as_dict(self) -> Dict[str, str]:
        return {"role": self.role, "value": self.value, "words": self.words,
                "rule": self.rule}


@dataclass(frozen=True)
class Plan:
    """One reading of a question as an operation the machine has.

    ``query`` is the formal query the plan compiles to when the operation is
    one of the session's own; ``compute`` names the exact computation of
    this module otherwise.  Exactly one of the two is set.
    """

    frame: str
    intent: str
    slots: Tuple[Slot, ...]
    query: Optional[str] = None
    compute: Optional[str] = None
    args: Tuple[object, ...] = ()
    render: str = ""

    def slot(self, role: str) -> Optional[Slot]:
        for s in self.slots:
            if s.role == role:
                return s
        return None

    def as_dict(self) -> Dict[str, object]:
        return {"frame": self.frame, "intent": self.intent,
                "slots": [s.as_dict() for s in self.slots],
                "query": self.query, "compute": self.compute}


@dataclass(frozen=True)
class Outcome:
    """What running one plan gave: licensed with a value, or refused."""

    plan: Plan
    licensed: bool
    value: str
    answer: str
    reason: str = ""
    kind: str = ""
    expected: Mapping[str, str] = field(default_factory=dict)
    faculty: str = "table"


@dataclass(frozen=True)
class Planned:
    """The planner's verdict on one question."""

    text: str
    verdict: str            # answered | ambiguous | refused | fallthrough
    outcomes: Tuple[Outcome, ...]
    chosen: Optional[Outcome]
    reason: str = ""


# ===========================================================================
# 2.  CLEANING, NUMBERS, AND THE EXACT RENDERING OF A RATIONAL
# ===========================================================================

_UNITS_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_TENS_WORDS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}


def _number_words(text: str) -> str:
    """Spelled-out integers below one hundred, rewritten as digits."""
    def tens(match: "re.Match[str]") -> str:
        value = _TENS_WORDS[match.group(1)]
        if match.group(2):
            value += _UNITS_WORDS[match.group(2)]
        return str(value)
    units = "|".join(sorted((k for k in _UNITS_WORDS if k != "zero"
                             and _UNITS_WORDS[k] < 10), key=len,
                            reverse=True))
    text = re.sub(r"\b(" + "|".join(_TENS_WORDS) + r")(?:[- ](" + units +
                  r"))?\b", tens, text)
    text = re.sub(r"\b(" + "|".join(sorted(_UNITS_WORDS, key=len,
                                           reverse=True)) + r")\b",
                  lambda m: str(_UNITS_WORDS[m.group(1)]), text)
    return text


def clean(text: str) -> str:
    """The question as the frames read it.

    Lowercase except for the words a frame must see as written (nothing is
    case-sensitive downstream: the field surface's aliases are normalised),
    trailing punctuation removed, whitespace collapsed, spelled-out integers
    rewritten as digits, the American spelling of the metre folded into the
    British one, and the typographic apostrophe into the plain one.
    """
    t = text.strip().replace("\u2019", "'").replace("\u00d7", " * ")
    t = re.sub(r"[?!.]+$", "", t).strip()
    t = re.sub(r"^(please|so|and)\s+", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).lower()
    t = re.sub(r"\bmeters?\b", lambda m: m.group(0).replace("meter",
                                                            "metre"), t)
    t = re.sub(r"\bcentimeters?\b", lambda m: m.group(0).replace(
        "centimeter", "centimetre"), t)
    t = re.sub(r"\bkilometers?\b", lambda m: m.group(0).replace(
        "kilometer", "kilometre"), t)
    t = re.sub(r"\bmillimeters?\b", lambda m: m.group(0).replace(
        "millimeter", "millimetre"), t)
    return _number_words(t)


_NUMBER = r"-?\d+(?:/\d+)?(?:\.\d+)?"


def parse_number(text: str) -> Optional[Fraction]:
    """An exact rational from ``12``, ``-3``, ``3/2`` or ``2.5``; else None."""
    text = text.strip()
    if not re.fullmatch(_NUMBER, text):
        return None
    if "/" in text:
        num, den = text.split("/")
        if int(den) == 0:
            return None
        return Fraction(int(num), int(den))
    if "." in text:
        whole, frac = text.split(".")
        sign = -1 if whole.startswith("-") else 1
        return sign * (abs(int(whole or "0")) + Fraction(int(frac),
                                                          10 ** len(frac)))
    return Fraction(int(text))


def decimal_places(value: Fraction, places: int) -> str:
    """``value`` rounded half-even to ``places`` decimals, by integer work."""
    scaled = value * 10 ** places
    q, r = divmod(scaled.numerator, scaled.denominator)
    twice = 2 * r
    if twice > scaled.denominator or (twice == scaled.denominator
                                      and q % 2 == 1):
        q += 1
    sign = "-" if q < 0 else ""
    digits = str(abs(q)).rjust(places + 1, "0")
    if places == 0:
        return sign + digits
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def render_exact(value: Fraction, places: int = 4) -> str:
    """``n`` for an integer, the exact decimal when one exists, and
    ``n/d`` with a stated rounding otherwise."""
    if value.denominator == 1:
        return str(value.numerator)
    decimal = exact_decimal(value)
    if decimal is not None:
        return decimal
    return (f"{value.numerator}/{value.denominator} "
            f"(= {decimal_places(value, places)} rounded to {places} places)")


# ===========================================================================
# 3.  THE EXACT COMPUTATIONS -- the derivation half of the round
# ===========================================================================

#: The largest integer primality is decided for, by trial division.  Above it
#: the frame refuses rather than running unboundedly.
PRIME_LIMIT = 10 ** 12


def prime_witness(n: int) -> Optional[int]:
    """The least prime factor of ``n`` when ``n >= 2`` is composite, else
    ``None`` (``n`` prime).  Trial division, exact."""
    if n < 4:
        return None
    if n % 2 == 0:
        return 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return d
        d += 2
    return None


def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


class Refusal(ValueError):
    """A typed plan that ran and found a precondition unmet."""


def _compute_primality(n: Fraction) -> Tuple[str, str]:
    if n.denominator != 1:
        raise Refusal(f"primality is a property of integers, and {n} is not "
                      f"an integer")
    k = n.numerator
    if abs(k) > PRIME_LIMIT:
        raise Refusal(f"{k} is above the declared trial-division limit "
                      f"{PRIME_LIMIT}")
    if k < 2:
        return ("not prime",
                f"{k} is not prime: a prime is an integer above 1 whose only "
                f"divisors are 1 and itself")
    witness = prime_witness(k)
    if witness is None:
        return ("prime", f"yes, {k} is prime: no integer from 2 to its "
                         f"square root divides it")
    return ("not prime", f"no, {k} is not prime: {k} = {witness} x "
                         f"{k // witness}")


def _compute_gcd(*values: Fraction) -> Tuple[str, str]:
    if any(v.denominator != 1 for v in values):
        raise Refusal("a greatest common divisor is taken of integers")
    if all(v == 0 for v in values):
        raise Refusal("every integer divides 0, so a list of zeros has no "
                      "greatest common divisor")
    g = 0
    for v in values:
        g = _gcd(g, v.numerator)
    args = ", ".join(str(v) for v in values)
    return (str(g), f"gcd({args}) = {g}")


def _compute_lcm(*values: Fraction) -> Tuple[str, str]:
    if any(v.denominator != 1 for v in values):
        raise Refusal("a least common multiple is taken of integers")
    if any(v == 0 for v in values):
        raise Refusal("0 has no positive multiple, so no least common "
                      "multiple is defined")
    lcm = 1
    for v in values:
        x = abs(v.numerator)
        lcm = lcm * x // _gcd(lcm, x)
    args = ", ".join(str(v) for v in values)
    return (str(lcm), f"lcm({args}) = {lcm}")


_OPERATORS = {"+": "+", "plus": "+", "-": "-", "minus": "-", "*": "*",
              "x": "*", "times": "*", "multiplied by": "*", "/": "/",
              "divided by": "/", "over": "/"}


def _integer_args(where: str, *values: Fraction) -> Tuple[int, ...]:
    for v in values:
        if v.denominator != 1:
            raise Refusal(f"{where} is a question about integers, and {v} is "
                          f"not one")
    return tuple(v.numerator for v in values)


def _compute_linear(a: Fraction, b: Fraction, c: Fraction) -> Tuple[str, str]:
    """``a x + b y = c`` over the integers, with its certificate."""
    ia, ib, ic = _integer_args("a linear Diophantine equation", a, b, c)
    sol = _cert.solve_linear(ia, ib, ic)
    if sol.kind == "family":
        value = f"x={sol.x0}+{sol.sx}k,y={sol.y0}+{sol.sy}k"
    else:
        value = sol.kind
    return value, _cert.render_linear(sol)


def _compute_bezout(a: Fraction, b: Fraction) -> Tuple[str, str]:
    ia, ib = _integer_args("Bezout's identity", a, b)
    got = _cert.bezout(ia, ib)
    return f"{got.g}={got.x},{got.y}", _cert.render_bezout(got)


def _compute_factorise(n: Fraction) -> Tuple[str, str]:
    (k,) = _integer_args("a factorisation", n)
    try:
        got = _cert.factorise(k)
    except _cert.CertificateRefusal as why:
        raise Refusal(str(why)) from None
    return (",".join(f"{p}^{e}" for p, e in got.factors) or "1",
            _cert.render_factorisation(got))


def _compute_recognise(text: str) -> Tuple[str, str]:
    """The simplest fraction that rounds to a quoted decimal (round two, Y2)."""
    try:
        got = _cert.recognise_decimal(text)
    except _cert.CertificateRefusal as why:
        raise Refusal(str(why)) from None
    if not got.significant:
        raise Refusal(_cert.refusal_recognition(got))
    frac = f"{got.fraction.numerator}/{got.fraction.denominator}"
    return frac, _cert.render_recognition(got)


def _quantity(session, words: str) -> Tuple[str, Tuple[Fraction, ...]]:
    """A physical quantity's register key and its EXT10 exponents."""
    from ..data_objects import physics as _physics
    try:
        held = session.field_surface.field("dimension_ext10", words)
    except FieldError:
        raise Refusal(f"{words!r} is not a quantity of the physics "
                      f"register") from None
    try:
        q = _physics.quantity_by_name(held.row)
    except KeyError:
        raise Refusal(f"{words!r} is not a quantity of the physics "
                      f"register") from None
    return q.name, tuple(q.exps_ext10)


def _compute_monomial(session, basis: str, target: str,
                      given: Tuple[str, ...]) -> Tuple[str, str]:
    """``target = k * prod given^e`` on one basis (round two, Y3)."""
    from ..data_objects import physics as _physics
    axes = _physics.AXES_EXT10 if basis == "ext10" else _physics.AXES_SI7
    width = len(axes)
    tname, tvec = _quantity(session, target)
    cols = []
    for words in given:
        name, vec = _quantity(session, words)
        cols.append((name, vec[:width]))
    if len({n for n, _v in cols}) != len(cols):
        raise Refusal("a quantity is named twice")
    got = _cert.derive_monomial(tname, tvec[:width], cols, axes)
    text = _cert.render_monomial(got)
    if got.kind == "undetermined":
        raise Refusal(text)
    if got.kind == "impossible":
        return "impossible", text
    law = "*".join(f"{n}^{e}" for n, e in zip(got.given, got.exponents))
    return f"{tname}={law}", text


def _held_interval(value: object):
    """A held register value read at its stated precision, or ``None``."""
    from ..reasoning.intervals import Interval
    if isinstance(value, int) and not isinstance(value, bool):
        value = Fraction(value)
    if not isinstance(value, Fraction):
        return None
    return Interval.as_held(value, "register")


def _compute_consistent(session, field_name: str, row: str,
                        quoted: str) -> Tuple[str, str]:
    """Is a held value consistent with a quoted decimal, or with the
    declared standard table (round two, Y1)?"""
    from ..reasoning import intervals as _iv
    try:
        held = session.field_surface.field(field_name, row)
    except FieldError as error:
        raise Refusal(str(error)) from None
    mine = _held_interval(held.value)
    if mine is None:
        raise Refusal(f"{field_name} of {row} is not a held number")
    if quoted == "standard":
        if field_name != "atomic_weight_u":
            raise Refusal(f"a standard value is declared only for atomic "
                          f"weights, not for {field_name}")
        rows = {r[0]: r for r in _iv.IUPAC_WEIGHTS}
        if held.row not in rows:
            raise Refusal(f"no standard value is declared for {held.row}: "
                          f"the declared table holds {len(rows)} elements")
        other, _central = _iv.standard_interval(rows[held.row])
        what = (f"the declared standard value [{_cert._dec(other.lo)}, "
                f"{_cert._dec(other.hi)}] (transcribed from the IUPAC/CIAAW "
                f"table)")
    else:
        try:
            _v, lo, hi = _cert._decimal_interval(quoted)
        except _cert.CertificateRefusal as why:
            raise Refusal(str(why)) from None
        other = _iv.Interval(lo, hi, "quoted")
        what = (f"{quoted} as written, [{_cert._dec(lo)}, "
                f"{_cert._dec(hi)}]")
    held_text = (f"{field_name} of {held.row} is held as {held.rendered}, "
                 f"read at its stated precision as [{_cert._dec(mine.lo)}, "
                 f"{_cert._dec(mine.hi)}]")
    if mine.overlaps(other):
        inside = mine.lo == mine.hi and other.contains(mine.lo)
        how = "exactly" if inside else "at the register's stated precision"
        return "True", (f"yes, consistent {how} -- {held_text}, and it meets "
                        f"{what}")
    side = "below" if mine.hi < other.lo else "above"
    return "False", (f"no, inconsistent -- {held_text}, which lies wholly "
                     f"{side} {what}; no value both allow exists")


def _compute_arith(op: str, a: Fraction, b: Fraction) -> Tuple[str, str]:
    if op == "+":
        value = a + b
    elif op == "-":
        value = a - b
    elif op == "*":
        value = a * b
    else:
        if b == 0:
            raise Refusal(f"{a} / 0 has no value: division by zero is "
                          f"undefined")
        value = a / b
    text = render_exact(value)
    return (f"{value.numerator}/{value.denominator}",
            f"{a} {op} {b} = {text}")


# -- the declared exact unit table -------------------------------------------

@dataclass(frozen=True)
class Unit:
    """One unit, exactly, in its quantity's canonical unit."""

    name: str
    plural: str
    quantity: str
    factor: Fraction
    source: str
    aliases: Tuple[str, ...] = ()


_YP = "exact by the 1959 international yard and pound agreement"
_SI = "exact by the SI prefix definitions"

#: Every unit the conversion frame knows, with the definition that makes its
#: factor exact.  Nothing here is a measurement: each row is a definition,
#: so a conversion is a computation over a stated fact, not a lookup of a
#: rounded one.  A unit outside this table is not converted.
UNITS: Tuple[Unit, ...] = (
    Unit("metre", "metres", "length", Fraction(1), "the SI base unit",
         ("m",)),
    Unit("kilometre", "kilometres", "length", Fraction(1000), _SI, ("km",)),
    Unit("centimetre", "centimetres", "length", Fraction(1, 100), _SI,
         ("cm",)),
    Unit("millimetre", "millimetres", "length", Fraction(1, 1000), _SI,
         ("mm",)),
    Unit("inch", "inches", "length", Fraction(254, 10000), _YP, ()),
    Unit("foot", "feet", "length", Fraction(3048, 10000), _YP, ("ft",)),
    Unit("yard", "yards", "length", Fraction(9144, 10000), _YP, ("yd",)),
    Unit("mile", "miles", "length", Fraction(1609344, 1000), _YP, ("mi",)),
    Unit("kilogram", "kilograms", "mass", Fraction(1), "the SI base unit",
         ("kg",)),
    Unit("gram", "grams", "mass", Fraction(1, 1000), _SI, ("g",)),
    Unit("tonne", "tonnes", "mass", Fraction(1000), _SI, ()),
    Unit("pound", "pounds", "mass", Fraction(45359237, 100000000), _YP,
         ("lb", "lbs")),
    Unit("ounce", "ounces", "mass", Fraction(45359237, 1600000000), _YP,
         ("oz",)),
    Unit("second", "seconds", "time", Fraction(1), "the SI base unit",
         ("s",)),
    Unit("minute", "minutes", "time", Fraction(60), "exact by definition",
         ("min",)),
    Unit("hour", "hours", "time", Fraction(3600), "exact by definition",
         ("h",)),
    Unit("day", "days", "time", Fraction(86400), "exact by definition", ()),
)


def unit_named(word: str) -> Optional[Unit]:
    w = word.strip().lower()
    for unit in UNITS:
        if w in (unit.name, unit.plural) + unit.aliases:
            return unit
    return None


def _compute_convert(amount: Fraction, source: Unit,
                     target: Unit) -> Tuple[str, str]:
    if source.quantity != target.quantity:
        raise Refusal(f"a {source.name} measures {source.quantity} and a "
                      f"{target.name} measures {target.quantity}; no "
                      f"conversion relates two different quantities")
    value = amount * source.factor / target.factor
    unit_word = target.name if value == 1 else target.plural
    src_word = source.name if amount == 1 else source.plural
    return (f"{value.numerator}/{value.denominator}",
            f"{render_exact(amount)} {src_word} = {render_exact(value)} "
            f"{unit_word} -- 1 {source.name} = {render_exact(source.factor)} "
            f"{_canonical(source.quantity)} ({source.source}) and 1 "
            f"{target.name} = {render_exact(target.factor)} "
            f"{_canonical(target.quantity)} ({target.source})")


def _canonical(quantity: str) -> str:
    return {"length": "metre", "mass": "kilogram", "time": "second"
            }[quantity]


# ===========================================================================
# 4.  GROUNDING -- words to names, or nothing
# ===========================================================================

#: Words a field slot may carry that the register's field names do not spell
#: out.  Each maps to an *ordered* list of field names; the first one the
#: grounded row actually answers to is taken, so ``weight`` is the atomic
#: weight of an element and the molar mass of a molecule, and is nothing for
#: a row that holds neither.
FIELD_SYNONYMS: Dict[str, Tuple[str, ...]] = {
    "atomic weight": ("atomic_weight_u",),
    "atomic mass": ("atomic_weight_u",),
    "standard atomic weight": ("atomic_weight_u",),
    "weight": ("atomic_weight_u", "molar_mass_u"),
    "mass": ("atomic_weight_u", "molar_mass_u"),
    "molar mass": ("molar_mass_u",),
    "molecular weight": ("molar_mass_u",),
    "molecular mass": ("molar_mass_u",),
    "block": ("group_block",),
    "group": ("group_block",),
    "family": ("group_block",),
    "kind of element": ("group_block",),
    "atomic number": ("z",),
    "proton number": ("z",),
    "name": ("name",),
    "element": ("name",),
    "dimension": ("dimension_si7",),
    "dimensions": ("dimension_si7",),
    "dimensional formula": ("dimension_si7",),
    "file": ("file",),
    "module": ("module", "file"),
    "number of rungs": ("rungs",),
    "melting point": ("melting_point_K",),
    "boiling point": ("boiling_point_K",),
    "formula": ("formula",),
    "unit": ("unit",),
    "symbol": ("symbol",),
}

#: Trailing tokens of a register field name that are its unit or its
#: encoding, not its meaning: ``atomic_weight_u`` is read as *atomic weight*.
_FIELD_SUFFIXES = frozenset({
    "u", "k", "pm", "ev", "g", "per", "cm3", "kj", "mol", "si7", "ext10",
    "pauling", "code",
})


def field_words(name: str) -> Tuple[str, ...]:
    """The phrasings the register's own field name licenses."""
    tokens = name.lower().split("_")
    out = [" ".join(tokens)]
    while len(tokens) > 1 and tokens[-1] in _FIELD_SUFFIXES:
        tokens = tokens[:-1]
        out.append(" ".join(tokens))
    # 'density_g_per_cm3' -> 'density'
    for i, token in enumerate(tokens):
        if token in _FIELD_SUFFIXES and i > 0:
            out.append(" ".join(tokens[:i]))
            break
    return tuple(dict.fromkeys(out))


def _singular(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") \
        and not word.endswith("ss") else word


#: Leading words of a row slot that name its *class*, not the row:
#: *the element C*, *the ratio 3/2*, *the function rung_audit*.
_CLASS_WORDS = (
    "the", "a", "an", "element", "chemical element", "ratio", "interval",
    "function", "declaration", "theorem", "lemma", "definition", "number",
    "word", "term", "molecule", "compound", "quantity", "constant",
    "musical interval", "one mole of", "1 mole of", "a mole of", "mole of",
)


def _strip_class(words: str) -> List[str]:
    """``words`` with leading class words removed, one at a time, and with
    a trailing ``atom`` or possessive removed -- every stage kept, longest
    first, so the grounding tries the words as written before it tries
    less."""
    out = [words.strip()]
    w = words.strip()
    changed = True
    while changed:
        changed = False
        for lead in sorted(_CLASS_WORDS, key=len, reverse=True):
            if w.startswith(lead + " "):
                w = w[len(lead) + 1:].strip()
                out.append(w)
                changed = True
                break
    for tail in (" atom", " atoms", "'s"):
        if w.endswith(tail):
            out.append(w[: -len(tail)].strip())
    return [x for x in dict.fromkeys(out) if x]


@dataclass(frozen=True)
class RowRef:
    """A grounded row: the surface form to ask with, and how it was found."""

    name: str
    rule: str


class Grounder:
    """Row, field and table grounding against one session's field surface."""

    def __init__(self, session) -> None:
        self.session = session
        self.surface = session.field_surface
        self._function_rows: Optional[Tuple[str, ...]] = None
        self._ratio_index: Optional[Dict[Fraction, List[str]]] = None
        self._relations: Optional[frozenset] = None

    # -- rows ------------------------------------------------------------

    def function_rows(self) -> Tuple[str, ...]:
        if self._function_rows is None:
            self._function_rows = tuple(
                self.surface.table_by_name("function").rows())
        return self._function_rows

    def ratio_index(self) -> Dict[Fraction, List[str]]:
        """Rows by the value of a declared ``ratio`` field."""
        if self._ratio_index is None:
            index: Dict[Fraction, List[str]] = {}
            for table in self.surface.tables():
                if table.kind != "carrier":
                    continue
                for key, fields in table.rows().items():
                    value = fields.get("ratio")
                    if isinstance(value, Fraction):
                        index.setdefault(value, []).append(key)
            self._ratio_index = index
        return self._ratio_index

    def rows(self, words: str) -> Tuple[RowRef, ...]:
        """Every row the words can name, each with its rule.

        Tried in order, and the first stage that grounds anything wins:
        the words as written (then with class words stripped), the words
        joined with underscores, a rational literal read against the
        declared ``ratio`` fields, and a module component of a declared
        function surface.
        """
        for form in _strip_class(words):
            if not form or len(form) > 120:
                continue
            if self.surface.matches(form):
                return (RowRef(form, "alias"),)
            joined = re.sub(r"\s+", "_", form)
            if joined != form and self.surface.matches(joined):
                return (RowRef(joined, "underscore-join"),)
            number = parse_number(form)
            if number is not None and "/" in form:
                hits = self.ratio_index().get(number, [])
                if hits:
                    return tuple(RowRef(h, f"ratio-value {form}")
                                 for h in hits)
            parts = joined.split("_")
            component = "_".join(parts)
            hits = [row for row in self.function_rows()
                    if component in row.split(".")]
            if hits:
                return tuple(RowRef(h, f"module-component {component}")
                             for h in hits)
        return ()

    def function_row(self, words: str) -> Tuple[RowRef, ...]:
        """A declared function surface named by its dotted name or by its
        last component."""
        for form in _strip_class(words):
            if form in self.function_rows():
                return (RowRef(form, "dotted-name"),)
            hits = [row for row in self.function_rows()
                    if row.split(".")[-1] == form]
            if hits:
                return tuple(RowRef(h, "last-component") for h in hits)
        return ()

    def relation_fields(self) -> frozenset:
        """Every ``<relation>_of`` field some carrier table holds."""
        if self._relations is None:
            names = set()
            for table in self.surface.tables():
                if table.kind != "carrier":
                    continue
                for fields in table.rows().values():
                    names.update(n for n in fields if n.endswith("_of"))
            self._relations = frozenset(names)
        return self._relations

    # -- fields ----------------------------------------------------------

    def row_fields(self, row: str) -> Tuple[str, ...]:
        try:
            return self.surface.fields(row).names
        except FieldError:
            return ()

    def field(self, words: str, row: str) -> Optional[Slot]:
        """The one field of ``row`` the words name, or ``None``."""
        held = self.row_fields(row)
        if not held:
            return None
        w = re.sub(r"^(the|its|a|an)\s+", "", words.strip())
        forms = list(dict.fromkeys([w, _singular(w),
                                    " ".join(_singular(t)
                                             for t in w.split())]))
        for form in forms:
            if form in FIELD_SYNONYMS:
                for name in FIELD_SYNONYMS[form]:
                    if name in held:
                        return Slot("field", name, words, "synonym")
        for form in forms:
            for name in held:
                if form in field_words(name) or form.replace(" ", "_") \
                        == name.lower():
                    return Slot("field", name, words, "field-name")
        return None


# ===========================================================================
# 5.  THE FRAMES
# ===========================================================================

Frame = Callable[[str, Grounder], List[Plan]]


def _row_slots(g: Grounder, words: str) -> List[Tuple[RowRef, Slot]]:
    return [(ref, Slot("row", ref.name, words, ref.rule))
            for ref in g.rows(words)]


def _field_plans(frame: str, g: Grounder, field_words_: str,
                 row_words: str) -> List[Plan]:
    plans: List[Plan] = []
    for ref, row_slot in _row_slots(g, row_words):
        fslot = g.field(field_words_, ref.name)
        if fslot is None:
            continue
        plans.append(Plan(frame, "field", (fslot, row_slot),
                          query=f"field {fslot.value} of {ref.name}"))
    return plans


def frame_arithmetic(t: str, g: Grounder) -> List[Plan]:
    body = re.sub(r"^(what is|what's|compute|calculate|evaluate|work out|"
                  r"what do you get if you|what do you get when you)\s+",
                  "", t)
    n = _NUMBER
    ops = r"(\+|-|\*|x|/|plus|minus|times|multiplied by|divided by|over)"
    m = re.fullmatch(rf"({n})\s*{ops}\s*({n})", body)
    if m:
        a, op, b = m.group(1), _OPERATORS[m.group(2)], m.group(3)
    else:
        m = re.fullmatch(rf"(?:add|sum)\s+({n})\s+(?:and|to)\s+({n})", body) \
            or re.fullmatch(rf"the sum of ({n}) and ({n})", body)
        if m:
            a, op, b = m.group(1), "+", m.group(2)
        else:
            m = re.fullmatch(rf"(?:multiply|the product of)\s+({n})\s+"
                             rf"(?:and|by)\s+({n})", body)
            if m:
                a, op, b = m.group(1), "*", m.group(2)
            else:
                m = re.fullmatch(rf"subtract ({n}) from ({n})", body)
                if not m:
                    return []
                a, op, b = m.group(2), "-", m.group(1)
    x, y = parse_number(a), parse_number(b)
    if x is None or y is None:
        return []
    return [Plan("arithmetic", "compute",
                 (Slot("number", str(x), a, "literal"),
                  Slot("operator", op, body, "operator-word"),
                  Slot("number", str(y), b, "literal")),
                 compute="arith", args=(op, x, y))]


def frame_prime(t: str, g: Grounder) -> List[Plan]:
    m = re.fullmatch(rf"(?:is|tell me whether|tell me if|check whether|"
                     rf"check if|whether)\s+(?:the number\s+)?({_NUMBER})\s+"
                     rf"(?:is\s+)?(?:a\s+)?prime(?:\s+number)?", t)
    if not m:
        return []
    x = parse_number(m.group(1))
    if x is None:
        return []
    return [Plan("prime", "compute",
                 (Slot("number", str(x), m.group(1), "literal"),),
                 compute="prime", args=(x,))]


def frame_gcd_lcm(t: str, g: Grounder) -> List[Plan]:
    names = {"gcd": "gcd", "greatest common divisor": "gcd",
             "highest common factor": "gcd", "hcf": "gcd",
             "greatest common factor": "gcd", "lcm": "lcm",
             "least common multiple": "lcm", "lowest common multiple": "lcm"}
    alternation = "|".join(sorted(names, key=len, reverse=True))
    m = re.search(rf"\b({alternation}) of ((?:{_NUMBER})(?:(?:,| and|, and) "
                  rf"(?:{_NUMBER}))+)$", t)
    if not m:
        return []
    words = re.findall(_NUMBER, m.group(2))
    values = [parse_number(w) for w in words]
    if any(v is None for v in values) or len(values) < 2:
        return []
    fn = names[m.group(1)]
    return [Plan("gcd-lcm", "compute",
                 (Slot("function", fn, m.group(1), "function-word"),) +
                 tuple(Slot("number", str(v), w, "literal")
                       for v, w in zip(values, words)),
                 compute=fn, args=tuple(values))]


_LINEAR_TERM = r"(-?\s*(?:\d+(?:/\d+)?(?:\.\d+)?)?)"


def _coefficient(text: str) -> Optional[Fraction]:
    text = text.replace(" ", "")
    if text in ("", "+"):
        return Fraction(1)
    if text == "-":
        return Fraction(-1)
    return parse_number(text)


def frame_certificate(t: str, g: Grounder) -> List[Plan]:
    """Derivations that carry a certificate (experiment X7).

    ``solve <a>x + <b>y = <c> in integers``, ``can ... be solved in
    integers``, ``bezout coefficients of <a> and <b>`` and ``factorise <n>``.
    An equation asked "in integers" that is not linear in ``x`` and ``y``
    reads as a plan that refuses, so it is declined rather than handed on.
    """
    m = re.fullmatch(r"(?:solve|can)\s+(.+?)\s+(?:be solved\s+)?"
                     r"(?:in|over) (?:the )?integers", t)
    if m:
        eq = m.group(1)
        lin = re.fullmatch(rf"{_LINEAR_TERM}\s*x\s*([+-])\s*"
                           rf"((?:\d+(?:/\d+)?(?:\.\d+)?)?)\s*y\s*=\s*"
                           rf"({_NUMBER})", eq)
        if lin:
            a = _coefficient(lin.group(1))
            b = _coefficient(lin.group(3))
            c = parse_number(lin.group(4))
            if a is not None and b is not None and c is not None:
                if lin.group(2) == "-":
                    b = -b
                return [Plan("certificate", "compute",
                             (Slot("equation", eq, eq, "linear-two-unknowns"),),
                             compute="linear", args=(a, b, c))]
        return [Plan("certificate", "compute",
                     (Slot("equation", eq, eq, "not-linear"),),
                     compute="not-linear", args=(eq,))]
    m = re.fullmatch(rf"(?:the )?bezout (?:coefficients|identity) (?:of|for) "
                     rf"({_NUMBER}) and ({_NUMBER})", t)
    if m:
        a, b = parse_number(m.group(1)), parse_number(m.group(2))
        if a is None or b is None:
            return []
        return [Plan("certificate", "compute",
                     (Slot("number", str(a), m.group(1), "literal"),
                      Slot("number", str(b), m.group(2), "literal")),
                     compute="bezout", args=(a, b))]
    m = re.fullmatch(rf"(?:factori[sz]e|(?:the )?prime factori[sz]ation of)"
                     rf" ({_NUMBER})", t)
    if m:
        n = parse_number(m.group(1))
        if n is None:
            return []
        return [Plan("certificate", "compute",
                     (Slot("number", str(n), m.group(1), "literal"),),
                     compute="factorise", args=(n,))]
    return []


def frame_recognise(t: str, g: Grounder) -> List[Plan]:
    """*What fraction rounds to 0.142857?* -- rational recognition (Y2)."""
    m = re.fullmatch(r"(?:what|which) (?:simple )?fraction (?:rounds to|is "
                     r"rounded to|gives) (-?\d+(?:\.\d+)?)", t)
    if not m:
        m = re.fullmatch(r"recogni[sz]e (-?\d+(?:\.\d+)?) as a fraction", t)
    if not m:
        return []
    return [Plan("recognise", "compute",
                 (Slot("number", m.group(1), m.group(1), "decimal-as-written"),),
                 compute="recognise", args=(m.group(1),))]


def _quantity_list(words: str) -> List[str]:
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", words.strip())
    return [re.sub(r"^(?:the|a|an)\s+", "", p.strip()) for p in parts
            if p.strip()]


def frame_dimensional(t: str, g: Grounder) -> List[Plan]:
    """*How does period depend on length and acceleration?* (Y3).

    Read on two bases, the extended ten-axis vector and the SI seven-axis
    projection, as :func:`_verify_two_terms` reads a dimension check: where
    the two disagree the licensing rule refuses.
    """
    patterns = (
        r"how does (?:the )?(.+?) depend on (.+)",
        r"express (?:the )?(.+?) in terms of (.+)",
        r"derive (?:a formula for )?(?:the )?(.+?) from (.+)",
        r"what formula (?:gives|relates) (?:the )?(.+?) (?:from|to) (.+)",
    )
    for pattern in patterns:
        m = re.fullmatch(pattern, t)
        if not m:
            continue
        target, given = m.group(1).strip(), tuple(_quantity_list(m.group(2)))
        if not given:
            return []
        slots = (Slot("quantity", target, target, "target"),) + tuple(
            Slot("quantity", w, w, "given") for w in given)
        return [Plan(f"dimensional-{basis}", "compute",
                     slots + (Slot("basis", basis, basis, "declared basis"),),
                     compute=f"monomial-{basis}", args=(basis, target, given))
                for basis in ("ext10", "si7")]
    return []


def frame_consistent(t: str, g: Grounder) -> List[Plan]:
    """*Is the atomic weight of iron consistent with 55.845?* (Y1)."""
    target = (r"(?:the )?(?:standard (?:value|atomic weight)|iupac value|"
              r"declared standard)|-?\d+(?:\.\d+)?")
    patterns = (
        (rf"is (?:the )?(.+?) of (.+?) (?:consistent|compatible) with "
         rf"({target})", 1, 2),
        (rf"is (.+?)'s (.+?) (?:consistent|compatible) with ({target})", 2, 1),
        (rf"does (?:the )?(.+?) of (.+?) agree with ({target})", 1, 2),
    )
    for pattern, ifield, irow in patterns:
        m = re.fullmatch(pattern, t)
        if not m:
            continue
        quoted = m.group(3)
        if not re.fullmatch(r"-?\d+(?:\.\d+)?", quoted):
            quoted = "standard"
        plans = []
        for ref, row_slot in _row_slots(g, m.group(irow)):
            fslot = g.field(m.group(ifield), ref.name)
            if fslot is None:
                continue
            plans.append(Plan("consistent", "compute",
                              (fslot, row_slot,
                               Slot("number", quoted, m.group(3),
                                    "decimal-as-written")),
                              compute="consistent",
                              args=(fslot.value, ref.name, quoted)))
        return plans
    return []


def frame_convert(t: str, g: Grounder) -> List[Plan]:
    n = _NUMBER
    u = r"([a-z]+)"
    patterns = (
        (rf"convert ({n}) {u} (?:to|into|in) {u}", (1, 2, 3)),
        (rf"how many {u} (?:are |is )?(?:there )?in ({n}) {u}", (2, 3, 1)),
        (rf"how many {u} (?:is|are|make) ({n}) {u}", (2, 3, 1)),
        (rf"(?:what is|what's|express) ({n}) {u} (?:in|as) {u}", (1, 2, 3)),
    )
    for pattern, (ia, isrc, idst) in patterns:
        m = re.fullmatch(pattern, t)
        if not m:
            continue
        amount = parse_number(m.group(ia))
        src, dst = unit_named(m.group(isrc)), unit_named(m.group(idst))
        if amount is None or src is None or dst is None:
            return []
        return [Plan("convert", "compute",
                     (Slot("number", str(amount), m.group(ia), "literal"),
                      Slot("unit", src.name, m.group(isrc), "unit-table"),
                      Slot("unit", dst.name, m.group(idst), "unit-table")),
                     compute="convert", args=(amount, src, dst))]
    return []


def frame_meaning(t: str, g: Grounder) -> List[Plan]:
    patterns = (
        r"what (?:does|do) (?:the (?:word|term) )?(.+?) mean",
        r"(?:what is |what's |explain |give |tell me )?the meaning of "
        r"(?:the (?:word|term) )?(.+)",
        r"define (?:the (?:word|term) )?(.+)",
    )
    for pattern in patterns:
        m = re.fullmatch(pattern, t)
        if m:
            words = m.group(1)
            refs = g.rows(words)
            if not refs:
                return []
            return [Plan("meaning", "meaning",
                         (Slot("row", refs[0].name, words, refs[0].rule),),
                         query=f"meaning of {refs[0].name}")]
    return []


def frame_verify(t: str, g: Grounder) -> List[Plan]:
    rel = (r"(?:dimensionally )?(?:equal to|equals?|have the same "
           r"dimensions? as|has the same dimensions? as|have the dimensions? "
           r"of|has the dimensions? of|the same as)")
    ops = r"(times|multiplied by|divided by|over|per)"
    m = re.fullmatch(rf"(?:is|does|check (?:whether|that|if)|verify that) "
                     rf"(.+?) {rel} (.+?) {ops} (.+?)(?: dimensionally)?", t)
    if not m:
        return _verify_two_terms(t, g, rel)
    names: List[Tuple[str, str]] = []
    for words in (m.group(1), m.group(2), m.group(4)):
        refs = g.rows(words)
        if not refs:
            return []
        names.append((refs[0].name, words))
    op = "*" if m.group(3) in ("times", "multiplied by") else "/"
    (a, aw), (b, bw), (c, cw) = names
    return [Plan("verify", "verify",
                 (Slot("row", a, aw, "alias"), Slot("row", b, bw, "alias"),
                  Slot("operator", op, m.group(3), "operator-word"),
                  Slot("row", c, cw, "alias")),
                 query=f"{a} = {b} {op} {c}")]


def _verify_two_terms(t: str, g: Grounder, rel: str) -> List[Plan]:
    """*Does A have the same dimensions as B?* -- read at two layers.

    The session's ``verify`` reads the extended dimension vector, which
    keeps the plane angle; the ``dimension_si7`` field is the SI projection,
    which drops it.  The two are both licensed readings of the question, and
    where they disagree (torque against energy) the question is refused as
    ambiguous with both named rather than answered at whichever layer came
    first.
    """
    m = re.fullmatch(rf"(?:is|does|check (?:whether|that|if)|verify that) "
                     rf"(.+?) {rel} (.+?)(?: dimensionally)?", t)
    if not m:
        return []
    a_refs, b_refs = g.rows(m.group(1)), g.rows(m.group(2))
    if len(a_refs) != 1 or len(b_refs) != 1:
        return []
    a, b = a_refs[0].name, b_refs[0].name
    slots = (Slot("row", a, m.group(1), a_refs[0].rule),
             Slot("row", b, m.group(2), b_refs[0].rule))
    return [
        Plan("verify", "verify", slots, query=f"{a} = {b}"),
        Plan("verify-si7", "same-field", slots + (
            Slot("field", "dimension_si7", "dimensions", "layer SI7"),),
            compute="same-field", args=("dimension_si7", a, b)),
    ]


def frame_inverse_relation(t: str, g: Grounder) -> List[Plan]:
    """*The derivative of position* -- the row whose relation points here.

    The lexicon holds ``velocity derivative_of position``; *what is the
    derivative of position?* asks for the row at the other end.  The answer
    is addressed by value: every carrier row whose ``<relation>_of`` field
    names the grounded row.  One such row is an answer; several are a set,
    and are refused as such.
    """
    m = re.fullmatch(r"(?:what is |what's |give |find )?the ([a-z ]+?) of "
                     r"(.+)", t)
    if not m:
        return []
    rel = m.group(1).strip().replace(" ", "_") + "_of"
    if rel not in g.relation_fields():
        return []
    refs = g.rows(m.group(2))
    if len(refs) != 1:
        return []
    return [Plan("inverse-relation", "inverse",
                 (Slot("field", rel, m.group(1), "relation-inverse"),
                  Slot("row", refs[0].name, m.group(2), refs[0].rule)),
                 compute="inverse", args=(rel, refs[0].name))]


def frame_relation(t: str, g: Grounder) -> List[Plan]:
    patterns = (
        (r"what is (.+?) the ([a-z ]+?) of", 1, 2),
        (r"(.+?) is the ([a-z ]+?) of (?:what|which [a-z]+)", 1, 2),
        (r"of what is (.+?) the ([a-z ]+)", 1, 2),
        (r"which [a-z]+ has (.+?) as its ([a-z ]+)", 1, 2),
    )
    for pattern, irow, irel in patterns:
        m = re.fullmatch(pattern, t)
        if not m:
            continue
        rel = m.group(irel).strip().replace(" ", "_") + "_of"
        plans = _field_plans("relation", g, rel, m.group(irow))
        if plans:
            return plans
    return []


def frame_dimension(t: str, g: Grounder) -> List[Plan]:
    patterns = (
        r"(?:what (?:is|are) |give (?:me )?|state )?the (?:dimensions?|"
        r"dimensional formula) of (.+)",
        r"what dimensions? does (.+?) have",
    )
    for pattern in patterns:
        m = re.fullmatch(pattern, t)
        if m:
            return _field_plans("dimension", g, "dimension", m.group(1))
    return []


def frame_returns(t: str, g: Grounder) -> List[Plan]:
    patterns = (
        r"what (?:fields |keys )?does (.+?) return",
        r"what is returned by (.+)",
        r"describe what (.+?) returns",
    )
    for pattern in patterns:
        m = re.fullmatch(pattern, t)
        if m:
            refs = g.function_row(m.group(1))
            return [Plan("returns", "fields",
                         (Slot("row", ref.name, m.group(1), ref.rule),),
                         query=f"fields of {ref.name}") for ref in refs]
    return []


def frame_field(t: str, g: Grounder) -> List[Plan]:
    """The field of a row, in the shapes English asks it."""
    out: List[Plan] = []
    specific = (
        # (pattern, field words or group index, row group)
        (r"how heavy is (.+)", "weight", 1),
        (r"how much does (?:a|one|1) mole of (.+?) weigh", "molar mass", 1),
        (r"what does (?:a|one|1) mole of (.+?) weigh", "molar mass", 1),
        (r"(?:which|what) (?:block|group)(?: of the periodic table)? "
         r"(?:is|does) (.+?) (?:in|belong to)", "block", 1),
        (r"what kind of element is (.+)", "block", 1),
        (r"(?:which|what) element (?:has the symbol|is) (.+)", "name", 1),
        (r"(?:which|what) file (?:is )?(.+?)(?: in| declared| written| "
         r"proved)?", "file", 1),
        (r"in (?:which|what) file is (.+?)(?: declared| written| proved)?",
         "file", 1),
        (r"(?:which|what) file is (.+?) (?:declared|written|proved|stated) "
         r"in", "file", 1),
        (r"what file (?:declares|contains|holds) (.+)", "file", 1),
        (r"where is (.+?) (?:declared|written|proved|stated)", "file", 1),
        (r"(?:which|what) module (?:defines|contains) (?:the function )?"
         r"(.+)", "module", 1),
        (r"(?:in )?(?:which|what) module is (?:the function )?(.+?)"
         r"(?: defined)?(?: in)?", "module", 1),
        (r"where is (?:the function )?(.+?) defined", "module", 1),
        (r"where does (.+?) live", "module", 1),
    )
    for pattern, fwords, irow in specific:
        m = re.fullmatch(pattern, t)
        if m:
            out.extend(_field_plans("field", g, fwords, m.group(irow)))
            if out:
                return out
    counting = (
        (r"how many ([a-z_ ]+?) (?:are in|are there in|does|do) (.+?)"
         r"(?: have)?", 1, 2),
        (r"(?:what is )?the number of ([a-z_ ]+?) (?:of|in) (.+)", 1, 2),
        (r"(.+?) has how many ([a-z_ ]+)", 2, 1),
        (r"count the ([a-z_ ]+?) of (.+)", 1, 2),
    )
    for pattern, ifield, irow in counting:
        m = re.fullmatch(pattern, t)
        if m:
            out.extend(_field_plans("count", g, m.group(ifield),
                                    m.group(irow)))
            if out:
                return out
    general = (
        (r"(?:what is|what's|what are|give|give me|tell me|find|state)?\s*"
         r"(?:the )?([a-z_ ]+?) of (.+)", 1, 2),
        (r"(.+?)'s ([a-z_ ]+)", 2, 1),
        (r"what ([a-z_ ]+?) does (.+?) have", 1, 2),
    )
    for pattern, ifield, irow in general:
        m = re.fullmatch(pattern, t)
        if m:
            out.extend(_field_plans("field", g, m.group(ifield),
                                    m.group(irow)))
            if out:
                return out
    return out


# -- comparison: two rows, one declared comparative ---------------------------

@dataclass(frozen=True)
class Comparative:
    """A comparative word: the fields it reads and which end it wants."""

    word: str
    fields: Tuple[str, ...]
    wants: str          # "high" or "low"


#: The comparatives the ordering frame understands.  ``more <pole>`` and
#: ``less <pole>`` are read generically against any ``<a>_<b>`` coordinate
#: with its declared poles (0 is the first pole), so they are not listed.
COMPARATIVES: Tuple[Comparative, ...] = (
    Comparative("heavier", ("atomic_weight_u", "molar_mass_u"), "high"),
    Comparative("lighter", ("atomic_weight_u", "molar_mass_u"), "low"),
    Comparative("more massive", ("atomic_weight_u", "molar_mass_u"), "high"),
    Comparative("less massive", ("atomic_weight_u", "molar_mass_u"), "low"),
)


def _comparative_field(g: Grounder, word: str, row: str
                       ) -> Optional[Tuple[str, str, str]]:
    """``(field, wants, rule)`` for a comparative word on one row."""
    held = g.row_fields(row)
    for comp in COMPARATIVES:
        if comp.word == word:
            for name in comp.fields:
                if name in held:
                    return name, comp.wants, "comparative-table"
            return None
    m = re.fullmatch(r"(more|less) ([a-z ]+)", word)
    if not m:
        return None
    from ..reasoning.coordinate_order import POLES
    pole = m.group(2).strip()
    for name in sorted(POLES):
        low, high = POLES[name]
        if pole not in (low, high):
            continue
        more = m.group(1) == "more"
        wants = "low" if (pole == low) == more else "high"
        return name, wants, f"declared poles {low}=0, {high}=1"
    return None


def frame_compare(t: str, g: Grounder) -> List[Plan]:
    adj = r"(heavier|lighter|more massive|less massive|more [a-z]+|less [a-z]+)"
    patterns = (
        (rf"is (.+?) {adj} than (.+)", 1, 2, 3, True),
        (rf"(?:which|what)(?: [a-z]+)? is (?:the )?{adj}[,:]? (.+?) or (.+)",
         2, 1, 3, False),
        (rf"what's (?:the )?{adj}[,:]? (.+?) or (.+)", 2, 1, 3, False),
        (rf"which of (.+?) and (.+?) is (?:the )?{adj}", 1, 3, 2, False),
        (rf"between (.+?) and (.+?),? which is (?:the )?{adj}", 1, 3, 2,
         False),
        (rf"which is {adj}: (.+?) or (.+)", 2, 1, 3, False),
    )
    for pattern, ia, iadj, ib, polar in patterns:
        m = re.fullmatch(pattern, t)
        if not m:
            continue
        a_words, word, b_words = m.group(ia), m.group(iadj), m.group(ib)
        a_refs, b_refs = g.rows(a_words), g.rows(b_words)
        if len(a_refs) != 1 or len(b_refs) != 1:
            return []
        a, b = a_refs[0].name, b_refs[0].name
        fa = _comparative_field(g, word, a)
        fb = _comparative_field(g, word, b)
        if fa is None or fb is None or fa[1] != fb[1]:
            return []
        if fa[0] == fb[0]:
            query = f"order {fa[0]} of {a} and {b}"
        else:
            query = f"order {fa[0]} of {a} and {fb[0]} of {b}"
        return [Plan("compare", "ordering",
                     (Slot("row", a, a_words, a_refs[0].rule),
                      Slot("comparative", word, word, fa[2]),
                      Slot("field", fa[0], word, fa[2]),
                      Slot("row", b, b_words, b_refs[0].rule)),
                     query=query,
                     args=(fa[1], polar, a_words, b_words, word, a, fa[0],
                           b, fb[0]))]
    return []


_TABLE_NOUNS = {"element": "element", "elements": "element",
                "molecule": "molecule", "molecules": "molecule",
                "compound": "molecule", "compounds": "molecule"}
_SUPERLATIVES = {"largest": "largest", "highest": "largest",
                 "greatest": "largest", "biggest": "largest",
                 "maximum": "largest", "smallest": "smallest",
                 "lowest": "smallest", "least": "smallest",
                 "minimum": "smallest"}


def frame_extremum(t: str, g: Grounder) -> List[Plan]:
    sup = "|".join(_SUPERLATIVES)
    nouns = "|".join(_TABLE_NOUNS)
    m = re.fullmatch(rf"(?:which|what) ({nouns}) has the ({sup}) ([a-z ]+)",
                     t)
    if m:
        table, end, fwords = _TABLE_NOUNS[m.group(1)], \
            _SUPERLATIVES[m.group(2)], m.group(3)
    else:
        m = re.fullmatch(rf"(?:which|what) is the (heaviest|lightest) "
                         rf"({nouns})", t)
        if m:
            table = _TABLE_NOUNS[m.group(2)]
            end = "largest" if m.group(1) == "heaviest" else "smallest"
            fwords = "weight"
        else:
            m = re.fullmatch(rf"(?:what is )?the ({sup}) ([a-z ]+?) "
                             rf"(?:of|among) (?:any |all )?(?:the )?"
                             rf"({nouns})", t)
            if not m:
                return []
            table, end, fwords = _TABLE_NOUNS[m.group(3)], \
                _SUPERLATIVES[m.group(1)], m.group(2)
    rows = g.surface.table_by_name(table).rows()
    sample = next(iter(rows))
    fslot = g.field(fwords, sample)
    if fslot is None:
        return []
    return [Plan("extremum", "extremum",
                 (Slot("end", end, end, "superlative-word"), fslot,
                  Slot("table", table, table, "table-noun")),
                 query=f"{end} {fslot.value} in {table}")]


def frame_describe(t: str, g: Grounder) -> List[Plan]:
    m = re.fullmatch(r"(?:describe|tell me about|what is|what's|who is|"
                     r"profile)\s+(.+)", t)
    if not m:
        return []
    words = m.group(1)
    if re.search(r"\b(of|than|in|to)\b", words):
        return []
    refs = g.rows(words)
    if len(refs) != 1:
        return []
    return [Plan("describe", "describe",
                 (Slot("row", refs[0].name, words, refs[0].rule),),
                 query=f"describe {refs[0].name}")]


#: The frames, in the order they are tried.  Every frame is tried; the order
#: only fixes the order candidates are listed in, never which one wins --
#: :func:`accept` is independent of it.
FRAMES: Tuple[Tuple[str, Frame], ...] = (
    ("arithmetic", frame_arithmetic),
    ("prime", frame_prime),
    ("gcd-lcm", frame_gcd_lcm),
    ("certificate", frame_certificate),
    ("recognise", frame_recognise),
    ("dimensional", frame_dimensional),
    ("consistent", frame_consistent),
    ("convert", frame_convert),
    ("meaning", frame_meaning),
    ("verify", frame_verify),
    ("relation", frame_relation),
    ("inverse-relation", frame_inverse_relation),
    ("dimension", frame_dimension),
    ("returns", frame_returns),
    ("compare", frame_compare),
    ("extremum", frame_extremum),
    ("field", frame_field),
    ("describe", frame_describe),
)


def candidate_plans(text: str, grounder: Grounder) -> Tuple[Plan, ...]:
    """Every plan any frame reads the question as, deduplicated."""
    t = clean(text)
    seen: Dict[Tuple[Optional[str], Optional[str], Tuple[object, ...]],
               Plan] = {}
    for _name, frame in FRAMES:
        for plan in frame(t, grounder):
            key = (plan.query, plan.compute, tuple(map(str, plan.args)))
            seen.setdefault(key, plan)
    return tuple(seen.values())


# ===========================================================================
# 6.  EXECUTION AND LICENSING
# ===========================================================================

def _identity(session, row: str) -> str:
    """The row's own name or gloss, when it holds one that says more."""
    for label in ("name", "gloss"):
        try:
            value = session.field_surface.field(label, row)
        except FieldError:
            continue
        if isinstance(value.value, str) and value.value \
                and value.value.lower() != row.lower():
            return f"{label} = {value.value} (from the {value.table} table)"
    return ""


def _run_surface_compute(session, plan: Plan) -> Outcome:
    """The two computations that read the field surface themselves."""
    surface = session.field_surface
    if plan.compute == "same-field":
        name, a, b = plan.args                          # type: ignore[misc]
        try:
            va, vb = surface.field(name, a), surface.field(name, b)
        except FieldError as error:
            return Outcome(plan, False, "", "", reason=str(error),
                           kind="compute:same-field", faculty="derive")
        same = va.value == vb.value
        return Outcome(
            plan, True, "True" if same else "False",
            f"{name}: {a} = {va.rendered} and {b} = {vb.rendered}; "
            f"{'the same' if same else 'different'} at this layer",
            kind="compute:same-field",
            expected={"holds": "True" if same else "False",
                      "layer": name}, faculty="derive")
    rel, target = plan.args                              # type: ignore[misc]
    wanted = {normalise(target)}
    for _table, key in surface.matches(target):
        wanted.add(normalise(key))
    hits: List[Tuple[str, str]] = []
    for table in surface.tables():
        if table.kind != "carrier":
            continue
        for key, fields in table.rows().items():
            value = fields.get(rel)
            items = value if isinstance(value, (tuple, list)) else (value,)
            if any(isinstance(v, str) and normalise(v) in wanted
                   for v in items):
                hits.append((table.name, key))
    names = sorted(dict.fromkeys(k for _t, k in hits))
    if not names:
        return Outcome(plan, False, "", "",
                       reason=f"no row holds {rel} = {target}",
                       kind="compute:inverse", faculty="address")
    if len(names) > 1:
        return Outcome(plan, False, "", "",
                       reason=f"{len(names)} rows hold {rel} = {target} "
                              f"({', '.join(names)}); a set is not one "
                              f"answer", kind="compute:inverse",
                       faculty="address")
    table_name = hits[0][0]
    return Outcome(plan, True, names[0],
                   f"{names[0]} -- the {table_name} table holds "
                   f"({names[0]}, {rel}, {target}), so {names[0]} is the "
                   f"{rel[:-3].replace('_', ' ')} of {target}",
                   kind="compute:inverse",
                   expected={"value": names[0], "relation": rel},
                   faculty="address")


def _held_overlap(session, *refs: str) -> str:
    """Why an ordering must be refused: the two held values overlap.

    ``refs`` is ``(row_a, field_a, row_b, field_b)``.  Each held value is
    read at its stated precision (round two, Y1c); overlapping intervals
    admit both orders (``GLM.SubstrateCognition.interval_overlap_undecided``),
    so an ordering between them is refused.  Returns ``""`` when there is
    nothing to refuse.
    """
    if len(refs) != 4:
        return ""
    a, fa, b, fb = refs
    try:
        va = session.field_surface.field(fa, a)
        vb = session.field_surface.field(fb, b)
    except FieldError:
        return ""
    ia, ib = _held_interval(va.value), _held_interval(vb.value)
    if ia is None or ib is None or not ia.overlaps(ib):
        return ""
    return (f"{fa} of {va.row} ({va.rendered}) and {fb} of {vb.row} "
            f"({vb.rendered}) overlap at their stated precision, so either "
            f"order is possible")


def run_plan(session, plan: Plan) -> Outcome:
    """Execute one plan and say whether it is licensed."""
    if plan.compute in ("same-field", "inverse"):
        return _run_surface_compute(session, plan)
    if plan.compute is not None:
        try:
            if plan.compute == "arith":
                value, answer = _compute_arith(*plan.args)       # type: ignore[arg-type]
            elif plan.compute == "prime":
                value, answer = _compute_primality(*plan.args)   # type: ignore[arg-type]
            elif plan.compute == "gcd":
                value, answer = _compute_gcd(*plan.args)         # type: ignore[arg-type]
            elif plan.compute == "lcm":
                value, answer = _compute_lcm(*plan.args)         # type: ignore[arg-type]
            elif plan.compute == "convert":
                value, answer = _compute_convert(*plan.args)     # type: ignore[arg-type]
            elif plan.compute == "linear":
                value, answer = _compute_linear(*plan.args)      # type: ignore[arg-type]
            elif plan.compute == "bezout":
                value, answer = _compute_bezout(*plan.args)      # type: ignore[arg-type]
            elif plan.compute == "factorise":
                value, answer = _compute_factorise(*plan.args)   # type: ignore[arg-type]
            elif plan.compute == "recognise":
                value, answer = _compute_recognise(*plan.args)   # type: ignore[arg-type]
            elif plan.compute.startswith("monomial-"):
                value, answer = _compute_monomial(session, *plan.args)  # type: ignore[arg-type]
            elif plan.compute == "consistent":
                value, answer = _compute_consistent(session, *plan.args)  # type: ignore[arg-type]
            elif plan.compute == "not-linear":
                raise Refusal(f"{plan.args[0]} is not a linear equation in "
                              f"x and y, and only those are solved here")
            else:                                   # pragma: no cover
                raise Refusal(f"no computation {plan.compute!r}")
        except Refusal as refusal:
            return Outcome(plan, False, "", "", reason=str(refusal),
                           kind=f"compute:{plan.compute}",
                           faculty="derive")
        return Outcome(plan, True, value, answer,
                       kind=f"compute:{plan.compute}",
                       expected={"value": value, "computation":
                                 plan.compute},
                       faculty="derive")
    assert plan.query is not None
    solution = session.ask(plan.query)
    expected = {str(k): str(v) for k, v in solution.expected.items()}
    if not solution.ok:
        return Outcome(plan, False, "", "", reason=solution.error or "",
                       kind=solution.kind, expected=expected)
    answer = solution.answer
    value = expected.get("value", answer)
    faculty = "table"
    if plan.intent == "ordering":
        verdict = expected.get("verdict", "")
        wants, polar, a_words, b_words, word = plan.args[:5]  # type: ignore[misc]
        overlap = _held_overlap(session, *plan.args[5:])
        if verdict in ("lt", "gt") and overlap:
            return Outcome(plan, False, "", "", reason=overlap,
                           kind=solution.kind, expected=expected,
                           faculty="derive")
        if verdict == "eq":
            value = "equal"
            lead = f"neither: {a_words} and {b_words} read the same"
        elif verdict in ("lt", "gt"):
            a_high = verdict == "gt"
            a_wins = a_high if wants == "high" else not a_high
            winner, loser = (a_words, b_words) if a_wins \
                else (b_words, a_words)
            value = f"winner={winner}"
            lead = (f"{'yes' if a_wins else 'no'}, " if polar else "") + \
                f"{winner} is {word} than {loser}"
        else:
            return Outcome(plan, False, "", "",
                           reason=f"the ordering gave no verdict: {answer}",
                           kind=solution.kind, expected=expected)
        answer = f"{lead} -- {answer}"
        faculty = "derive"
    elif plan.intent == "describe":
        row = plan.slots[0].value
        extra = _identity(session, row)
        if extra:
            answer = f"{answer}; {extra}"
        value = f"describe={row}"
    elif plan.intent == "extremum":
        value = expected.get("winners", answer)
        faculty = "derive"
    elif plan.intent == "verify":
        value = expected.get("holds", answer)
        faculty = "derive"
    elif plan.intent == "fields":
        value = expected.get("fields", answer)
    elif plan.intent == "meaning":
        value = answer
    elif expected.get("derived") == "yes":
        faculty = "derive"
    return Outcome(plan, True, value, answer, kind=solution.kind,
                   expected=expected, faculty=faculty)


def accept(outcomes: Sequence[Outcome]) -> Tuple[str, Optional[Outcome], str]:
    """The licensing rule: answer only on one agreed value.

    Returns ``(verdict, chosen, reason)``.  ``answered`` when every licensed
    outcome carries the same value (the chosen one is the first of them in
    frame order, and any of them would give the same value); ``ambiguous``
    when two licensed outcomes disagree; ``refused`` when plans ran and none
    was licensed; ``fallthrough`` when there was no plan at all.  The verdict
    and the value do not depend on the order of ``outcomes``;
    ``RequestProject/GLM/SemanticPlan.lean`` proves it.
    """
    if not outcomes:
        return "fallthrough", None, "no frame read the question"
    licensed = [o for o in outcomes if o.licensed]
    if not licensed:
        reasons = "; ".join(dict.fromkeys(o.reason for o in outcomes
                                          if o.reason))
        return "refused", None, reasons
    values = list(dict.fromkeys(o.value for o in licensed))
    if len(values) > 1:
        readings = "; ".join(f"{o.plan.query or o.plan.compute} -> "
                             f"{o.value}" for o in licensed)
        return "ambiguous", None, (f"{len(values)} licensed readings "
                                   f"disagree: {readings}")
    return "answered", licensed[0], ""


def plan_question(session, text: str,
                  grounder: Optional[Grounder] = None) -> Planned:
    """Every candidate plan for ``text``, run, and the licensing verdict."""
    g = grounder if grounder is not None else _grounder(session)
    plans = candidate_plans(text, g)
    outcomes = tuple(run_plan(session, plan) for plan in plans)
    verdict, chosen, reason = accept(outcomes)
    return Planned(text, verdict, outcomes, chosen, reason)


def _grounder(session) -> Grounder:
    cached = getattr(session, "_semantic_grounder", None)
    if cached is None:
        cached = Grounder(session)
        try:
            session._semantic_grounder = cached
        except AttributeError:                       # pragma: no cover
            pass
    return cached


def _trace(planned: Planned) -> Tuple[Dict[str, object], ...]:
    return tuple({**o.plan.as_dict(), "licensed": o.licensed,
                  "value": o.value, "reason": o.reason,
                  "faculty": o.faculty} for o in planned.outcomes)


def ask_planned(session, text: str) -> Solution:
    """Answer ``text`` through the typed planner, or through the grammar.

    * a unique licensed value -- that plan's answer, with the plan, its
      slots and their provenance in the payload;
    * two licensed values -- a refusal naming both readings;
    * no licensed plan -- the grammar's own answer to ``text``, exactly as
      :meth:`GeometricSession.ask` gives it, with the refused plans'
      reasons added to the payload (and to the error, when the grammar also
      refuses).
    """
    planned = plan_question(session, text)
    trace = _trace(planned)
    query = parse_query(text, session.index)
    if planned.verdict == "answered" and planned.chosen is not None:
        o = planned.chosen
        steps = (
            Step("plan", f"Read as the {o.plan.frame} frame: intent "
                         f"{o.plan.intent}, slots " +
                 ", ".join(f"{s.role}={s.value!r} from {s.words!r} "
                           f"({s.rule})" for s in o.plan.slots),
                 f"plan: {o.plan.query or o.plan.compute}"),
            Step("license", f"{sum(1 for x in planned.outcomes if x.licensed)}"
                            f" of {len(planned.outcomes)} candidate plans "
                            f"solved, and every one that solved agrees",
                 f"value = {o.value}"),
        )
        expected = dict(o.expected)
        expected.setdefault("value", o.value)
        expected["plan"] = str(o.plan.query or o.plan.compute)
        expected["plan_kind"] = "query" if o.plan.query is not None \
            else "compute"
        expected["faculty"] = o.faculty
        return Solution(query=query, kind=o.kind or o.plan.intent,
                        answer=o.answer, steps=steps, expected=expected,
                        payload={"plan": trace, "verdict": "answered"},
                        ok=True)
    if planned.verdict == "ambiguous":
        return Solution(query=query, kind="plan", answer=f"refused: "
                        f"{planned.reason}", ok=False,
                        error=f"ambiguous: {planned.reason}",
                        payload={"plan": trace, "verdict": "ambiguous"},
                        steps=(Step("ambiguous", planned.reason,
                                    "|values| > 1"),))
    solution = session.ask(text)
    if planned.verdict == "refused":
        payload = dict(solution.payload)
        payload["plan"] = trace
        payload["verdict"] = "refused"
        error = solution.error
        if not solution.ok:
            error = f"{planned.reason} (and the grammar: {solution.error})"
        return Solution(query=solution.query, kind=solution.kind,
                        answer=solution.answer if solution.ok
                        else f"unsolved: {error}", steps=solution.steps,
                        expected=solution.expected,
                        script_spec=solution.script_spec, payload=payload,
                        ok=solution.ok, error=error)
    return solution
