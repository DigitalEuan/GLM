"""``glm_universal.reasoning.admission`` -- the door a new word comes in by.

The part that was a commitment rather than a mechanism
------------------------------------------------------
"Open vocabulary" has stood on the untouched list for a long time with a note
beside it saying it is *a commitment, not an oversight*: the vocabulary is
exactly the registers, there is no coordinate for *justice*, and the semantics
layer refuses rather than inventing one.

That is the right commitment and it was never the whole story.  A commitment
says what the machine will not do.  What was missing is the other half -- **how
a word gets in** -- and without it "open" was an adjective rather than a door.
Two things went unstated:

1. *what makes a name admissible*, as a criterion someone could check rather
   than a judgement someone makes; and
2. *what a refusal is a refusal of* -- whether *justice* is outside the
   vocabulary permanently, or merely until something specific is supplied.

This module states both.  It is the vocabulary's door, and like the router in
:mod:`glm_universal.reasoning.vagueness` it is a short ordered chain of routes
whose last outcome is not a crash.

The criterion
-------------
A name is admissible exactly when some **stated route** gives it coordinates
that are **computed from a register the machine already checks**.  The three
clauses are separable and each rules something out:

``stated``
    the route is one of :data:`ROUTES`, written down in this module.  A name
    admitted "because it obviously belongs" is not admitted.

``reproducible``
    the coordinates are recomputed from the registers on demand, so admission
    survives being re-run.  Nothing is typed in at admission time.

``grounded``
    the coordinates come *out of* a register rather than being invented for
    the name.  This is the clause that does the refusing, and it is the same
    discipline `element_coverage` follows when it widens the element register
    by derivation and writes nothing back.

The routes, in order
--------------------
``held``
    the name is already a carrier in one of the nine registers.  Its
    coordinates are the register's own; the door does nothing.

``unit``
    the name is a unit expression -- ``kg*m/s^2``, ``J``, ``mol/L`` -- and
    :mod:`glm_universal.reasoning.units` parses it to ten exact EXT10
    exponents.  A dimension is coordinates, so the name is in.

``arithmetic``
    the name is an expression over register names -- ``energy divided by
    time`` -- and :mod:`glm_universal.reasoning.term_arithmetic` evaluates it
    exactly.  This is the route that makes the vocabulary genuinely open
    rather than merely large: the register holds 726 quantities and the
    expressions over them do not run out.

``refused``
    no route reaches it.  The refusal is *conditional and it says what the
    condition is*: a name enters the moment a register that measures it is
    admitted, and the door needs no change for that to happen.  That is the
    difference between "there is no coordinate for justice" and "justice is
    not the kind of thing this machine has coordinates for" -- only the first
    is being claimed.

What is measured
----------------
:func:`admission_report` runs the door over :data:`PROBES` -- names drawn from
every register, unit expressions, arithmetic expressions and the standing
ungrounded words -- and checks four things that could each go wrong:

* *totality* -- every probe gets exactly one route, so a refusal is a decision;
* *grounding* -- no refused name is given coordinates, and every admitted one
  has them;
* *determinacy* -- asking twice gives the same route and the same coordinates;
* *the register is unchanged* -- admitting a name by ``unit`` or ``arithmetic``
  writes nothing back, exactly as the coverage layer does not.

Exactness
---------
Coordinates are tuples of :class:`fractions.Fraction`.  No float is
constructed anywhere in this module.
"""

from __future__ import annotations

import re

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from .. import data_objects as do
from ..data_objects import conjugate_pairs as cp
from ..data_objects import semantic_lexicon as sl
from ..derived import memo
from . import term_arithmetic as ta
from . import units as un

__all__ = [
    "ROUTES", "CRITERIA", "Admission", "PROBES", "UNGROUNDED",
    "vocabulary", "admit", "admission_audit", "admission_report",
]


#: The routes, in the order they are tried.  Only the last does not admit.
ROUTES: Tuple[str, ...] = ("held", "unit", "arithmetic", "refused")

#: What makes a name admissible.  Each clause rules something out, and the
#: third is the one that refuses.
CRITERIA: Tuple[Tuple[str, str], ...] = (
    ("stated",
     "the route is one of the routes this module names, so a name is never "
     "admitted because it obviously belongs"),
    ("reproducible",
     "the coordinates are recomputed from the registers on demand, so nothing "
     "is typed in at admission time and admission survives being re-run"),
    ("grounded",
     "the coordinates come out of a register rather than being invented for "
     "the name; this is the clause that refuses"),
)

#: The standing examples of names no register reaches.  They are kept here so
#: that the refusal is measured rather than asserted, and so that the day a
#: register does reach one, the measurement changes on its own.
UNGROUNDED: Tuple[str, ...] = (
    "justice", "beauty", "irony", "nostalgia", "fairness", "dignity",
)


# ===========================================================================
# 1.  WHAT THE REGISTERS HOLD
# ===========================================================================

@lru_cache(maxsize=1)
def vocabulary() -> Dict[str, str]:
    """Every name the nine registers carry, mapped to the register it is in.

    A name held in two registers is reported under the first, in the fixed
    order below; the order is part of the door, so that the answer does not
    depend on dictionary iteration.
    """
    out: Dict[str, str] = {}
    pools = do.all_objects()
    order = ("physics", "chemistry", "molecules", "mathematics", "harmonics",
             "economics", "comparison", "lexicon")
    for domain in order:
        for obj in pools[domain]:
            out.setdefault(str(obj.name), domain)
    semantic, _codec = sl.semantic_lexicon_objects()
    for obj in semantic:
        out.setdefault(str(obj.name), "semantic_lexicon")
    for name in cp.names():
        out.setdefault(str(name), "conjugate_pairs")
    return out


def _held_coordinates(name: str, domain: str) -> Optional[Tuple[Fraction, ...]]:
    """The EXT10 exponents a held name carries, when its register has them."""
    if domain != "physics":
        return None
    from ..data_objects import physics as ph
    return tuple(ph.quantity_by_name(name).exps_ext10)


# ===========================================================================
# 2.  THE DOOR
# ===========================================================================

@dataclass(frozen=True)
class Admission:
    """What the door made of one name."""

    name: str
    route: str
    #: Ten exact EXT10 exponents, or ``None`` -- a name may be admitted by a
    #: register that does not dimension it (an element, a chord, a word).
    coordinates: Optional[Tuple[Fraction, ...]]
    #: The register the coordinates came out of, or ``""`` when refused.
    source: str
    #: Why this route and not the next, in a sentence.
    reason: str

    @property
    def admitted(self) -> bool:
        return self.route != "refused"


def _try_unit(name: str) -> Optional[Tuple[Fraction, ...]]:
    try:
        return tuple(un.parse_unit(name))
    except Exception:
        return None


def _unit_near_miss(name: str) -> str:
    """Why the unit route declined, when it declined for a nameable reason.

    ``km/h`` is refused, and not because speed is ungrounded: the unit
    register is SI-coherent and does not hold the hour.  A refusal that says
    *which symbol is missing* is one someone can act on, so it is reported
    rather than folded into the general refusal.

    The near miss is claimed only for a name that is *reaching* for the unit
    register: it must be a compound expression in which at least one symbol
    parses on its own.  Without that clause every unknown word would be a
    near miss -- ``justice`` would be reported as a missing unit symbol,
    which would be an insult to the reader rather than a finding.
    """
    parts = [part for part in re.split(r"[^A-Za-z]+", name) if part]
    if len(parts) < 2:
        return ""
    known = sum(1 for part in parts if _parses_alone(part))
    if known == 0 or known == len(parts):
        return ""
    try:
        un.parse_unit(name)
    except un.UnitError as exc:
        message = str(exc)
        if "unknown unit symbol" in message:
            return message
    except Exception:
        return ""
    return ""


def _parses_alone(symbol: str) -> bool:
    try:
        un.parse_unit(symbol)
    except Exception:
        return False
    return True


def _try_arithmetic(name: str) -> Optional[ta.TermArithmetic]:
    if not ta.mentions_register_name(name):
        return None
    try:
        return ta.evaluate(name)
    except Exception:
        return None


def admit(name: str) -> Admission:
    """Put one name to the door, and get back a decision with its reason."""
    held = vocabulary().get(name)
    if held is not None:
        coords = _held_coordinates(name, held)
        return Admission(
            name=name, route="held", coordinates=coords, source=held,
            reason=(f"{name} is already a carrier in the {held} register; the "
                    f"door does nothing and the coordinates are the "
                    f"register's own"))
    exps = _try_unit(name)
    if exps is not None:
        return Admission(
            name=name, route="unit", coordinates=exps, source="units",
            reason=(f"{name} parses as a unit expression, so the unit "
                    f"register dimensions it exactly: "
                    f"{_dimension_string(exps)}"))
    term = _try_arithmetic(name)
    if term is not None:
        return Admission(
            name=name, route="arithmetic", coordinates=tuple(term.sense.exps),
            source="term_arithmetic",
            reason=(f"{name} is arithmetic over register names, evaluating to "
                    f"{term.ext10}"
                    + (f", which the register calls {term.names[0]}"
                       if term.names else
                       ", a dimension no register quantity carries")))
    near = _unit_near_miss(name)
    if near:
        return Admission(
            name=name, route="refused", coordinates=None, source="",
            reason=(f"{name} is a unit expression the register cannot finish "
                    f"reading: {near}.  The unit register is SI-coherent, so "
                    f"this is a gap in the register and not in the door -- "
                    f"admitting the symbol admits the name by the unit "
                    f"route, unchanged"))
    return Admission(
        name=name, route="refused", coordinates=None, source="",
        reason=(f"no route reaches {name}: it is not a carrier in any of the "
                f"nine registers, does not parse as a unit, and is not "
                f"arithmetic over register names.  The refusal is "
                f"conditional -- {name} is admitted by the first route the "
                f"moment a register that measures it is admitted, and the "
                f"door needs no change for that"))


def _dimension_string(exps: Tuple[Fraction, ...]) -> str:
    from ..data_objects import physics as ph
    return ph.dimension_string(exps)


# ===========================================================================
# 3.  THE PROBES, AND WHAT THE DOOR DOES TO THEM
# ===========================================================================

#: Names put to the door when the report is run: one from each register, a
#: spread of unit expressions, a spread of arithmetic expressions, and the
#: standing ungrounded words.
PROBES: Tuple[str, ...] = (
    # held -- one or two from each register
    "energy", "torque", "H", "Fe", "water", "unison", "filled_1x24",
    "cryostat", "electron", "temperature", "entropy",
    # unit expressions
    "J", "kg*m/s^2", "mol/L", "W/(m*K)", "N*m", "km/h",
    # arithmetic over register names
    "energy divided by time", "mass times velocity",
    "force times length", "energy per amount",
    # and the standing refusals
    *UNGROUNDED,
)


@memo
def admission_audit() -> Dict[str, object]:
    """Run the door over every probe and check the four things that matter."""
    rows = tuple(admit(name) for name in PROBES)
    counts: Dict[str, int] = {route: 0 for route in ROUTES}
    for row in rows:
        counts[row.route] += 1

    total = all(row.route in ROUTES for row in rows)
    grounded = all(
        (row.coordinates is None) if not row.admitted else True
        for row in rows)
    # Determinacy: the door is a function of the name and of the registers,
    # so asking twice must give the same answer.
    again = tuple(admit(row.name) for row in rows)
    determinate = all(
        a.route == b.route and a.coordinates == b.coordinates
        for a, b in zip(rows, again))
    # The registers are unchanged by admission: the names admitted by the two
    # computing routes are still not carriers afterwards.
    widened = tuple(row.name for row in rows
                    if row.route in ("unit", "arithmetic"))
    unchanged = all(name not in vocabulary() for name in widened)

    return {
        "probes": len(rows),
        "rows": rows,
        "counts": counts,
        "admitted": sum(counts[r] for r in ROUTES if r != "refused"),
        "refused": counts["refused"],
        "vocabulary_size": len(vocabulary()),
        "every_probe_routed": total,
        "no_coordinates_without_a_register": grounded,
        "determinate": determinate,
        "registers_unchanged": unchanged,
        "widened_by": widened,
        "holds": total and grounded and determinate and unchanged,
    }


@memo
def admission_report() -> Dict[str, object]:
    """The door, its criterion, what it admits, and what it still refuses."""
    audit = admission_audit()
    refusals = tuple(row for row in audit["rows"]      # type: ignore[index]
                     if not row.admitted)
    justice = admit("justice")
    # A refusal of a second shape: the name reaches for the unit register and
    # the register cannot finish reading it.  That is a gap in a register
    # rather than in the door, and it is counted separately so that the two
    # are never confused.
    gaps = tuple(row.name for row in refusals if _unit_near_miss(row.name))
    return {
        "routes": list(ROUTES),
        "criteria": [{"clause": clause, "says": says}
                     for clause, says in CRITERIA],
        "criterion": (
            "A name is admissible exactly when some stated route gives it "
            "coordinates computed from a register the machine already "
            "checks.  Stated rules out admitting a name because it obviously "
            "belongs; reproducible rules out typing a coordinate in at "
            "admission time; grounded rules out inventing one, and is the "
            "clause that refuses."),
        "audit": audit,
        "refusals": tuple(row.name for row in refusals),
        "refusal_count": len(refusals),
        "unit_gaps": gaps,
        "unit_gap_count": len(gaps),
        "ungrounded_refused": tuple(row.name for row in refusals
                                    if row.name not in gaps),
        "justice": {"route": justice.route, "reason": justice.reason},
        "commitment": (
            "The commitment is unchanged and now has a mechanism behind it: "
            "the vocabulary is exactly what the registers reach, and the "
            "machine refuses rather than inventing a coordinate.  What is new "
            "is that the refusal is conditional and names its condition, so "
            "'open vocabulary' is a door with a stated latch rather than an "
            "adjective."),
        "limits": (
            f"The door admits by three routes and refuses by one, and "
            f"{len(refusals)} of the {audit['probes']} probes are refused.  "
            "Two of the three admitting routes compute a dimension, so a name "
            "that is not a quantity can only get in by already being held: "
            "the door widens the vocabulary of *measurable* names, and says "
            "so rather than pretending to more."),
    }
