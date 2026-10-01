"""The ``related_to`` residue, decided by name rather than left as a lookup.

Where this sits
---------------
:func:`~.measure_view.relation_repair` converts the ``related_to`` triples the
physics register can decide -- 27 of the 66 -- and reports the other 39 with
the reason each was declined.  Thirty-eight of those reasons are the same one:
an endpoint *reaches no dimension the physics register holds*.  That sentence
records a failed lookup and nothing more.  It cannot distinguish a name the
register merely spells differently from a name that denotes no magnitude at
all, and until the difference is written down the residue is open in a way
that no amount of searching would close.

:mod:`glm_universal.data_objects.denotation` writes it down: a verdict per
name, each with its justification.  This module is the second pass that reads
those verdicts back over the residue and **measures what they change**:

* which triples now convert -- a name decided to denote a registered quantity
  is dimensioned from that entry, and the two rules of ``relation_repair``
  apply again unchanged;
* which triples are repaired to a relation that is decided but not
  dimensional (see :data:`DECIDED_RELATIONS`);
* which remain declined, now with a reason that names what the endpoint *is*
  rather than what the lookup did.

The claim the pass is here to support is :func:`closure`: **no triple is
declined any longer for want of an entry**.  Every undimensioned endpoint of
the residue has been decided, and the declines are decisions.

What is deliberately not done
-----------------------------
Only one repair rule is applied beyond the two dimensional ones, and it is
applied because it follows from the verdicts rather than from a reading of
each triple:

``names_process_of``
    one endpoint is a ``process`` and the other reaches a dimension, so the
    triple links something that happens to a quantity that quantifies it --
    *rotate* to an angle, *move* to a velocity.

A ``carrier`` beside a dimensioned endpoint is *not* repaired the same way,
although the shape is identical.  It would be wrong half the time: a magnet
does bear a magnetic flux density, and a photon does not bear an illuminance
-- the lexicon's ``photon related_to light`` is about what light is made of,
not about what a photon has.  A rule that is right half the time is a guess,
and the register's whole discipline is that a guess is worse than a refusal.

Exactness
---------
Dimensions are tuples of :class:`fractions.Fraction`, read from the physics
register.  No float is constructed here.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Tuple

from ..data_objects import denotation as dn
from ..data_objects import physics as ph
from ..derived import memo
from . import measure_view as mv

__all__ = [
    "DECIDED_RELATIONS",
    "dimension_of", "second_pass", "coverage", "closure",
    "denotation_report",
]


#: The relations this pass may write, beside ``relation_repair``'s own
#: ``same_dimension_as`` and ``differs_by``.  One entry, and it is one on
#: purpose: see the module docstring.
DECIDED_RELATIONS: Tuple[str, ...] = ("names_process_of",)


def dimension_of(name: str) -> Optional[Tuple[Fraction, ...]]:
    """The dimension a name reaches, the denotation register included.

    Identical to ``measure_view``'s own lookup wherever that succeeds; a name
    the lexicon and the aliases do not reach is then tried against the
    denotation register, and reaches a dimension exactly when it has been
    decided to denote a registered quantity.
    """
    direct = mv._dimension_of(name)
    if direct is not None:
        return direct
    denoted = dn.denotes_quantity(name)
    if denoted is None:
        return None
    try:
        return ph.quantity_by_name(denoted).exps_ext10
    except KeyError:            # pragma: no cover -- the audit forbids this
        return None


def _undecided_endpoints() -> Tuple[str, ...]:
    """Residue endpoints that reach no dimension and have no verdict."""
    missing: List[str] = []
    for row in mv.relation_repair()["residue_rows"]:      # type: ignore[index]
        for role in ("subject", "object"):
            name = row[role]
            if mv._dimension_of(name) is None and dn.denotation(name) is None:
                if name not in missing:
                    missing.append(name)
    return tuple(missing)


def _residue_endpoint_names() -> Tuple[str, ...]:
    """Every residue endpoint the physics register does not dimension."""
    names: List[str] = []
    for row in mv.relation_repair()["residue_rows"]:      # type: ignore[index]
        for role in ("subject", "object"):
            name = row[role]
            if mv._dimension_of(name) is None and name not in names:
                names.append(name)
    return tuple(names)


@memo
def coverage() -> Dict[str, object]:
    """That the decided names are exactly the residue's undimensioned ones.

    Two failures are possible and both are reported: a name the residue needs
    and the register does not decide, and a name the register decides that no
    residue triple asks about.  The second is not harmless -- an idle entry is
    a judgement made about nothing, and the register is meant to answer
    questions the data actually poses.
    """
    needed = set(_residue_endpoint_names())
    decided = set(dn.decided_names())
    return {
        "needed": len(needed),
        "decided": len(decided),
        "undecided": tuple(sorted(needed - decided)),
        "idle": tuple(sorted(decided - needed)),
        "complete": needed == decided,
    }


@memo
def second_pass() -> Dict[str, object]:
    """Re-run the repair over the residue with the denotations in hand."""
    repair = mv.relation_repair()
    converted: List[Dict[str, object]] = []
    decided: List[Dict[str, object]] = []
    declined: List[Dict[str, str]] = []

    for row in repair["residue_rows"]:                    # type: ignore[index]
        subject, other = row["subject"], row["object"]
        source, target = dimension_of(subject), dimension_of(other)

        if source is not None and target is not None:
            if source == target:
                converted.append({"subject": subject, "object": other,
                                  "predicate": "same_dimension_as",
                                  "factor": "", "direction": ""})
                continue
            hits = mv._factor_between(source, target)
            names = sorted({name for name, _ in hits})
            if len(names) == 1:
                factor, direction = hits[0]
                converted.append({"subject": subject, "object": other,
                                  "predicate": "differs_by",
                                  "factor": factor, "direction": direction})
                continue
            declined.append({
                "subject": subject, "object": other,
                "kind": "ambiguous_factor" if names else "no_single_factor",
                "reason": ("more than one quantity of the factor basis "
                           "carries one dimension to the other"
                           if names else
                           "no single quantity of the factor basis carries "
                           "one dimension to the other")})
            continue

        # Exactly one side undimensioned, and the other is a process: the
        # triple links a happening to a quantity that quantifies it.
        pairs = ((subject, other, source, target), (other, subject, target,
                                                    source))
        repaired = False
        for name, partner, own, partner_dim in pairs:
            if own is None and partner_dim is not None \
                    and dn.verdict_of(name) == "process":
                decided.append({"subject": name, "object": partner,
                                "predicate": "names_process_of",
                                "swapped": name != subject})
                repaired = True
                break
        if repaired:
            continue

        verdicts = tuple(sorted(
            dn.verdict_of(name) or "undecided"
            for name, dim in ((subject, source), (other, target))
            if dim is None))
        declined.append({
            "subject": subject, "object": other,
            "kind": "+".join(verdicts),
            "reason": _decline_reason(subject, other, source, target)})

    by_verdict: Dict[str, int] = {}
    for row in declined:
        by_verdict[row["kind"]] = by_verdict.get(row["kind"], 0) + 1
    return {
        "residue": int(repair["residue"]),               # type: ignore[arg-type]
        "converted": len(converted),
        "conversions": tuple(converted),
        "decided": len(decided),
        "decided_relations": tuple(decided),
        "declined": len(declined),
        "declined_rows": tuple(declined),
        "declined_by_kind": dict(sorted(by_verdict.items())),
        "newly_dimensioned": dn.register_summary()["dimensional"],
    }


def _decline_reason(subject: str, other: str,
                    source: Optional[Tuple[Fraction, ...]],
                    target: Optional[Tuple[Fraction, ...]]) -> str:
    """Why a triple is declined, in terms of what its endpoints denote."""
    parts: List[str] = []
    for name, dim in ((subject, source), (other, target)):
        if dim is not None:
            continue
        entry = dn.denotation(name)
        if entry is None:       # pragma: no cover -- coverage forbids this
            parts.append(f"{name} is undecided")
        else:
            parts.append(f"{name} {_VERDICT_PHRASE[entry.verdict](entry)}")
    return "; ".join(parts)


#: How each verdict reads in a refusal, so that a declined triple says what
#: its endpoint *is* rather than repeating the verdict's name.
_VERDICT_PHRASE = {
    "ambiguous": lambda e: (f"ranges over {', '.join(e.candidates)} and the "
                            f"word does not choose"),
    "polymorphic": lambda e: ("takes the dimension of whatever it is applied "
                              "to, so it has none of its own"),
    "carrier": lambda e: "denotes a thing that bears quantities, not one",
    "process": lambda e: "denotes something that happens, not a quantity",
    "abstraction": lambda e: "denotes no magnitude at all",
}


@memo
def closure() -> Dict[str, object]:
    """The claim the round is here to earn.

    ``decided`` is true when every residue triple has been *decided* -- either
    converted, repaired, or declined for a reason that names what its
    endpoints denote -- and no triple is any longer waiting on a lookup.
    """
    passed = second_pass()
    cover = coverage()
    accounted = (int(passed["converted"]) + int(passed["decided"])
                 + int(passed["declined"]))
    lookup_failures = tuple(
        f"{row['subject']} related_to {row['object']}"
        for row in passed["declined_rows"]              # type: ignore[union-attr]
        if "undecided" in row["kind"])
    return {
        "residue": passed["residue"],
        "accounted": accounted,
        "undecided_endpoints": _undecided_endpoints(),
        "lookup_failures": lookup_failures,
        "decided": (accounted == passed["residue"]
                    and bool(cover["complete"])
                    and not lookup_failures),
    }


@memo
def denotation_report() -> Dict[str, object]:
    """Everything the vocabulary decision is: register, coverage, effect."""
    return {
        "register": dn.register_summary(),
        "coverage": coverage(),
        "second_pass": second_pass(),
        "closure": closure(),
    }
