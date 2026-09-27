"""``glm_universal.reasoning.term_arithmetic`` -- arithmetic over register names.

What it does
------------
Reads an expression written over the *names* of physics register quantities --
``energy divided by time``, ``mass times velocity``, ``length per time
squared`` -- and returns the exact EXT10 dimension of the result together with
every register quantity that has that dimension.

Why it is a separate layer
--------------------------
The dimensional algebra already exists: :mod:`glm_universal.reasoning.verifier`
turns a written expression into a :class:`~glm_universal.reasoning.verifier.Sense`
-- ten exact rational EXT10 exponents, a decimal scale, a tensor rank and the
``P``/``T``/``C`` gradings -- and it is exact.  What was missing is the step
before it: a user does not write ``energy / time``, they write ``energy divided
by time``.  This module is exactly that step, plus the step after it, which is
saying *what the answer is called*.

The two steps are kept apart on purpose.  :func:`normalise` is a pure string
rewrite over a frozen table of English operator words and does no arithmetic;
:func:`evaluate` does the arithmetic and never looks at English.  So a wrong
answer is attributable to one or the other.

Nothing here is approximate: exponents are :class:`fractions.Fraction`, and a
name is matched only when all ten exponents *and* the decimal scale agree.

Reachable as
------------
``describe <expression>`` in the runtime, when the expression names no carrier
of its own -- ``what is energy divided by time`` answers ``power``.  The
figures are recomputed by :func:`term_arithmetic_report`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..data_objects import physics as do_physics
from . import verifier as vf

__all__ = [
    "WORD_OPERATORS", "NAMES_SHOWN", "ArithmeticError_", "TermArithmetic",
    "normalise", "mentions_register_name", "evaluate",
    "REPORT_EXPRESSIONS", "term_arithmetic_report",
]


class ArithmeticError_(ValueError):
    """Raised when an expression is not arithmetic over register names."""


#: English operator words, longest surface form first so that ``multiplied by``
#: cannot be shadowed by ``by`` and ``divided by`` cannot be shadowed by
#: ``divided``.  Postfix powers are rewritten in place: ``length squared``
#: becomes ``length ^ 2``.
WORD_OPERATORS: Tuple[Tuple[str, str], ...] = (
    ("multiplied by", " * "),
    ("divided by", " / "),
    ("to the power of", " ^ "),
    ("squared", " ^ 2 "),
    ("cubed", " ^ 3 "),
    ("times", " * "),
    ("over", " / "),
    ("per", " / "),
)

#: Filler words a question can carry that say nothing about the arithmetic.
_FILLER: Tuple[str, ...] = ("the ", "a ", "an ")

#: How many register names a one-line answer lists before saying "and N more".
NAMES_SHOWN: int = 6


def normalise(text: str) -> str:
    """Rewrite English operator words into the verifier's ``* / ^`` grammar.

    A pure string rewrite: it does no arithmetic and knows no register names.

    >>> normalise("energy divided by time")
    'energy / time'
    >>> normalise("mass times velocity squared")
    'mass * velocity ^ 2'
    """
    out = " " + str(text).strip().lower() + " "
    for filler in _FILLER:
        out = out.replace(" " + filler, " ")
    for word, symbol in WORD_OPERATORS:
        out = re.sub(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])",
                     symbol, out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def mentions_register_name(text: str) -> bool:
    """Whether the normalised text names at least one register quantity.

    This is the guard that keeps the arithmetic path from claiming a term it
    has no business claiming: ``unobtainium`` names nothing, so it is refused
    rather than parsed.
    """
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", normalise(text)):
        if vf.resolve_name(token) is not None:
            return True
    return False


@dataclass(frozen=True)
class TermArithmetic:
    """The exact result of arithmetic over register names.

    Attributes
    ----------
    source
        The expression as written.
    normalised
        The expression after :func:`normalise`.
    sense
        The exact :class:`~glm_universal.reasoning.verifier.Sense`.
    ext10, si7
        The dimension, written in each basis.
    names
        Every register quantity whose ten EXT10 exponents *and* decimal scale
        equal the result's, in register order.  Empty when the dimension is
        not one the register names.
    """

    source: str
    normalised: str
    sense: vf.Sense
    ext10: str
    si7: str
    names: Tuple[str, ...]

    @property
    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.sense.exps)

    @property
    def name(self) -> Optional[str]:
        """The single register name for the result, or ``None`` if not unique."""
        return self.names[0] if len(self.names) == 1 else None

    def describe(self) -> str:
        """One line saying what the expression comes to.

        A dimension does not determine a name: the register holds several
        hundred dimensionless quantities and nineteen with the dimension of
        energy.  The line says so rather than picking one and calling it the
        answer.
        """
        if self.is_dimensionless:
            return (f"{self.source} is dimensionless; the register has "
                    f"{len(self.names)} dimensionless quantities and the "
                    f"arithmetic does not choose between them")
        if len(self.names) == 1:
            return f"{self.source} = {self.names[0]} ({self.ext10})"
        if self.names:
            shown = ", ".join(self.names[:NAMES_SHOWN])
            more = len(self.names) - NAMES_SHOWN
            return (f"{self.source} has dimension {self.ext10}, which the "
                    f"register names {len(self.names)} ways: {shown}"
                    + (f", and {more} more" if more > 0 else ""))
        return (f"{self.source} has dimension {self.ext10}; no register "
                f"quantity carries it")

    def as_dict(self) -> Dict[str, object]:
        """A JSON-able record.

        ``names`` is truncated to :data:`NAMES_SHOWN`; ``name_count`` is the
        full count.
        """
        return {
            "source": self.source,
            "normalised": self.normalised,
            "ext10": self.ext10,
            "si7": self.si7,
            "scale": str(self.sense.scale),
            "rank": self.sense.rank,
            "name_count": len(self.names),
            "names": list(self.names[:NAMES_SHOWN]),
            "is_dimensionless": self.is_dimensionless,
        }


def _names_with_sense(sense: vf.Sense) -> Tuple[str, ...]:
    """Every register quantity with these exponents and this decimal scale."""
    return tuple(q.name for q in do_physics.load_physics_register()
                 if tuple(q.exps_ext10) == tuple(sense.exps)
                 and q.scale == sense.scale)


def evaluate(text: str) -> TermArithmetic:
    """Evaluate arithmetic over register names, exactly.

    Raises
    ------
    ArithmeticError_
        If the expression names no register quantity at all, or the verifier's
        grammar refuses it.  Both refusals are deliberate: this path must not
        answer a question it has not understood.
    """
    source = str(text).strip()
    if not source:
        raise ArithmeticError_("term arithmetic: empty expression")
    normalised = normalise(source)
    if not mentions_register_name(source):
        raise ArithmeticError_(
            f"term arithmetic: {source!r} names no register quantity, so "
            f"there is no arithmetic to do")
    try:
        sense = vf.parse(normalised)
    except Exception as exc:                      # the verifier's own refusals
        raise ArithmeticError_(
            f"term arithmetic: {normalised!r} is not an expression over "
            f"register names: {exc}") from exc
    return TermArithmetic(
        source=source, normalised=normalised, sense=sense,
        ext10=do_physics.dimension_string(sense.exps, "EXT10"),
        si7=do_physics.dimension_string(sense.exps, "SI7"),
        names=_names_with_sense(sense))


#: The expressions the report recomputes.  Each is a question a user could ask
#: in words, and each is answered by running :func:`evaluate`.
REPORT_EXPRESSIONS: Tuple[str, ...] = (
    "energy divided by time",
    "length divided by time",
    "mass times acceleration",
    "force times length",
    "power times time",
    "length divided by time squared",
    "velocity divided by velocity",
)


def term_arithmetic_report() -> Dict[str, object]:
    """Recompute the arithmetic-over-names table.

    Every figure this package publishes about arithmetic inside a description
    comes from here rather than from a docstring.
    """
    rows: List[Dict[str, object]] = []
    for expression in REPORT_EXPRESSIONS:
        rows.append(evaluate(expression).as_dict())
    named = sum(1 for r in rows if r["name_count"])
    unique = sum(1 for r in rows if r["name_count"] == 1)
    return {
        "expressions": len(rows),
        "rows": rows,
        "named": named,
        "uniquely_named": unique,
        "operator_words": [w for w, _ in WORD_OPERATORS],
        "register_size": len(do_physics.load_physics_register()),
    }
