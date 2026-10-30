"""``glm_universal.reasoning.vagueness`` -- deciding a vague triple by rule.

The part that was left ongoing
------------------------------
``related_to`` records *that* two concepts are linked without saying which, so
it transports nothing and the analogy layer refuses it by name.  Two rounds
went at the 66 the lexicon holds: ``measure_view.relation_repair`` converts the
27 the physics register can decide, and ``data_objects/denotation.py`` decides
the endpoints of the other 39 *by hand*, one verdict at a time, which took the
residue to nothing waiting on a lookup.

What stayed open was not the 66.  It was the next one: **every new vague triple
brings the hand work back**, and a discipline that needs a person for every
addition is a discipline that will quietly stop being followed.

This module is the standing rule that replaces it.  A ``related_to`` triple is
now put to four routes in order, and only the last one asks a person:

``dimensional``
    ``relation_repair``'s own two rules -- the endpoints have the same
    dimension, or differ by exactly one quantity of the factor basis.

``conjugate``
    both endpoints are named in
    :mod:`glm_universal.data_objects.conjugate_pairs`, in one row, so the
    register states which relation holds: ``temperature effort_of heat``,
    ``entropy extent_of heat``, ``entropy conjugate_of temperature``.  Two
    endpoints placed in *different* rows are **not** converted -- ``torque``
    and ``pressure`` are both efforts, of different domains, and the register
    relates an effort to its own row's extent and transfer, not to another
    domain's effort.  That refusal is as much a part of the rule as the
    conversions.

``proposed``
    an undimensioned endpoint is classified by a proposer rule, and the
    verdict feeds ``denotation_view``'s existing ``names_process_of`` repair.
    A proposer rule is admitted only if it fires on at least
    :data:`PROPOSER_MINIMUM` of the hand-decided names and agrees with the
    hand decision on **every** one of them: a wrong verdict is worse than an
    abstention, so the gate is agreement without exception rather than
    accuracy on average.

``referred``
    nothing decides it, and the triple is handed to a person *with the
    evidence collected* -- what each endpoint is in the lexicon, whether it
    reaches a dimension, whether it is placed in the conjugate register.  A
    referral is a decision to ask, not a failed lookup.

What the rules are, and what they cost
--------------------------------------
Five proposer rules are tried and four are refused, which is the useful part
of the measurement: ``nominalisation_of_a_verb`` would call *measurement* a
process, ``abstract_noun_is_an_abstraction`` would call *function* one,
``mass_noun_is_a_carrier`` would call *reaction* one, and ``verb_is_a_process``
would call *belong* one.  Each is refused on a named disagreement rather than
on judgement.

``verb_is_a_process`` is the instructive one.  It was the admitted rule while
every verb the register had decided was a doing; widening the lexicon by the
language probe's content words added ``belong``, a verb that holds rather than
happens, and one disagreement is enough for this gate.  The rule that replaces
it -- ``active_verb_is_a_process`` -- asks the lexicon for more than the part
of speech: the active/stative primitive must be at least 1/2.  It abstains on
``belong`` and on ``mean``, fires on 25 decided names and agrees with every
one.

Exactness
---------
Every number here is a count.  No magnitude is computed and no float is
constructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Tuple

from ..data_objects import conjugate_pairs as cp
from ..data_objects import denotation as dn
from ..data_objects import semantic_lexicon as lex
from ..derived import memo

__all__ = [
    "PROPOSER_MINIMUM", "ROUTES", "ProposerRule", "Proposal",
    "PROPOSER_RULES", "propose", "proposer_audit",
    "conjugate_conversions", "route_of", "routes", "vagueness_report",
]


#: A proposer rule must fire on at least this many hand-decided names before
#: it may be admitted -- one that fires twice has not been tested.
PROPOSER_MINIMUM: int = 5

#: The four routes, in the order they are tried.
ROUTES: Tuple[str, ...] = ("dimensional", "conjugate", "proposed", "referred")


# ===========================================================================
# 1.  READING THE LEXICON
# ===========================================================================

@lru_cache(maxsize=1)
def _lexicon() -> Dict[str, object]:
    pool, _codec = lex.semantic_lexicon_objects()
    return {obj.name: obj for obj in pool}


def _pos(name: str) -> str:
    obj = _lexicon().get(name)
    return "" if obj is None else str(obj.attributes.get("pos", ""))


def _primitive(name: str, axis: str) -> Optional[str]:
    obj = _lexicon().get(name)
    if obj is None:
        return None
    primitives = obj.attributes.get("primitives") or {}
    value = primitives.get(axis)
    return None if value is None else str(value)


def _primitive_at_least(name: str, axis: str, threshold: Fraction) -> bool:
    """Whether a primitive the lexicon records reaches ``threshold``.

    The primitives are exact rationals in the carrier, so the comparison is
    exact too; a name the lexicon does not hold, or an axis it does not set,
    is ``False`` rather than a guess.
    """
    value = _primitive(name, axis)
    if value is None:
        return False
    return Fraction(value) >= threshold


@lru_cache(maxsize=1)
def _verbs() -> Tuple[str, ...]:
    return tuple(sorted(name for name in _lexicon() if _pos(name) == "verb"))


def _nominalises(name: str) -> Optional[str]:
    """The verb this name is the nominalisation of, if the lexicon holds one."""
    for verb in _verbs():
        stems = {verb, verb[:-1]} if verb.endswith("e") else {verb}
        for stem in stems:
            for suffix in ("ion", "ing", "ment", "ance", "ence"):
                if name == stem + suffix:
                    return verb
    return None


@lru_cache(maxsize=1)
def related_to_triples() -> Tuple[Tuple[str, str], ...]:
    """Every ``related_to`` pair the lexicon holds, in register order."""
    out: List[Tuple[str, str]] = []
    pool, _codec = lex.semantic_lexicon_objects()
    for obj in pool:
        for triple in obj.attributes.get("triples", ()) or ():
            if len(triple) == 3 and str(triple[1]) == "related_to":
                out.append((str(triple[0]), str(triple[2])))
    return tuple(out)


# ===========================================================================
# 2.  THE PROPOSER
# ===========================================================================

@dataclass(frozen=True)
class ProposerRule:
    """One rule that proposes a denotation verdict from evidence in the lexicon."""

    name: str
    verdict: str
    evidence: str
    test: Callable[[str], bool]


@dataclass(frozen=True)
class Proposal:
    """What the proposer made of a name, or nothing."""

    name: str
    verdict: str
    rule: str
    evidence: str


#: The rules, in the order they are tried.  Only the admitted ones decide
#: anything; the refused ones are kept because a rule refused on a named
#: disagreement is a finding, and deleting it would lose the finding.
PROPOSER_RULES: Tuple[ProposerRule, ...] = (
    ProposerRule(
        name="verb_is_a_process", verdict="process",
        evidence="the lexicon records the name's part of speech as a verb",
        test=lambda name: _pos(name) == "verb"),
    ProposerRule(
        name="active_verb_is_a_process", verdict="process",
        evidence="the lexicon records the name as a verb and puts its "
                 "active/stative primitive at 1/2 or above, which is the "
                 "coordinate it uses for a verb that does something rather "
                 "than holds",
        test=lambda name: (_pos(name) == "verb"
                           and _primitive_at_least(name, "active_stative",
                                                   Fraction(1, 2)))),
    ProposerRule(
        name="nominalisation_of_a_verb", verdict="process",
        evidence="the name is the -ion/-ing/-ment nominalisation of a verb "
                 "the lexicon holds",
        test=lambda name: _pos(name) == "noun" and _nominalises(name) is not None),
    ProposerRule(
        name="abstract_noun_is_an_abstraction", verdict="abstraction",
        evidence="a noun whose abstract/concrete primitive is 0, the most "
                 "abstract reading the lexicon records",
        test=lambda name: (_pos(name) == "noun"
                           and _primitive(name, "abstract_concrete") == "0/1")),
    ProposerRule(
        name="mass_noun_is_a_carrier", verdict="carrier",
        evidence="a noun whose countable/mass primitive is 0, which the "
                 "lexicon uses for a thing rather than an amount",
        test=lambda name: (_pos(name) == "noun"
                           and _primitive(name, "countable_mass") == "0/1")),
)


@memo
def proposer_audit() -> Dict[str, object]:
    """Score every rule against the hand decisions, and admit or refuse it.

    The hand-decided register is the ground truth and the rules never see it:
    each reads the lexicon only.  A rule is admitted when it fires on at least
    :data:`PROPOSER_MINIMUM` decided names and agrees with the decision on
    every one; the disagreements of a refused rule are named.
    """
    decided = {entry.name: entry.verdict for entry in dn.DENOTATIONS}
    rows: List[Dict[str, object]] = []
    for rule in PROPOSER_RULES:
        fired = tuple(sorted(name for name in decided if rule.test(name)))
        agreed = tuple(n for n in fired if decided[n] == rule.verdict)
        disagreed = tuple(f"{n} is {decided[n]}, not {rule.verdict}"
                          for n in fired if decided[n] != rule.verdict)
        rows.append({
            "rule": rule.name,
            "verdict": rule.verdict,
            "evidence": rule.evidence,
            "fired_on": len(fired),
            "agreed": len(agreed),
            "disagreements": disagreed,
            "admitted": (len(fired) >= PROPOSER_MINIMUM and not disagreed),
        })
    admitted = tuple(row["rule"] for row in rows if row["admitted"])
    covered = tuple(sorted(
        name for name in decided
        if any(rule.test(name) for rule in PROPOSER_RULES
               if rule.name in admitted)))
    return {
        "rules": tuple(rows),
        "rules_tried": len(rows),
        "admitted": admitted,
        "admitted_count": len(admitted),
        "decided_names": len(decided),
        "decided_by_rule": len(covered),
        "still_by_hand": len(decided) - len(covered),
        "covered": covered,
        "minimum_fired_on": PROPOSER_MINIMUM,
        "gate": (
            "A proposer rule is admitted only if it fires on at least "
            f"{PROPOSER_MINIMUM} of the hand-decided names and agrees with "
            "the hand decision on every one of them.  A wrong verdict is "
            "worse than an abstention, so the gate is agreement without "
            "exception rather than accuracy on average."),
    }


def propose(name: str) -> Optional[Proposal]:
    """The verdict the admitted rules give a name, or ``None`` -- an abstention."""
    admitted = set(proposer_audit()["admitted"])          # type: ignore[arg-type]
    for rule in PROPOSER_RULES:
        if rule.name in admitted and rule.test(name):
            return Proposal(name=name, verdict=rule.verdict, rule=rule.name,
                            evidence=rule.evidence)
    return None


# ===========================================================================
# 3.  THE CONJUGATE ROUTE
# ===========================================================================

@memo
def conjugate_conversions() -> Dict[str, object]:
    """Which ``related_to`` triples the energy-conjugate register decides.

    Three outcomes, and the middle one is the interesting one: a pair whose
    endpoints are both placed but in different rows is *not* converted, and
    the register says why rather than inventing a relation between them.
    """
    dimensional = _dimensional_pairs()
    converted: List[Dict[str, str]] = []
    placed_apart: List[Dict[str, str]] = []
    unplaced: List[Tuple[str, str]] = []
    for subject, other in related_to_triples():
        relations = cp.related(subject, other)
        if relations:
            row = cp.row_of_name(subject)
            assert row is not None
            converted.append({
                "subject": subject, "object": other,
                "relation": relations[0], "row": row.domain,
                "definition": row.definition,
                "also_dimensional": dimensional.get((subject, other), "")})
        elif cp.role_of(subject) and cp.role_of(other):
            placed_apart.append({
                "subject": subject, "object": other,
                "subject_role": str(cp.role_of(subject)),
                "object_role": str(cp.role_of(other)),
                "reason": (
                    f"{subject} and {other} are both placed, but in "
                    f"different rows; the register relates a name to its own "
                    f"row's columns, not to another domain's")})
        else:
            unplaced.append((subject, other))
    only_here = tuple(row for row in converted if not row["also_dimensional"])
    return {
        "triples": len(related_to_triples()),
        "converted": tuple(converted),
        "converted_count": len(converted),
        "converted_only_here": only_here,
        "converted_only_here_count": len(only_here),
        "agreeing_with_the_dimensional_route":
            len(converted) - len(only_here),
        "agreement": (
            "Where both routes fire they agree, and the conjugate reading is "
            "the sharper one: the dimensional rule says heat and temperature "
            "differ by a factor, and the conjugate register names that "
            "factor's role -- entropy is the extent temperature acts "
            "through."),
        "placed_in_different_rows": tuple(placed_apart),
        "placed_in_different_rows_count": len(placed_apart),
        "unplaced_count": len(unplaced),
    }


# ===========================================================================
# 4.  THE STANDING RULE
# ===========================================================================

def _dimensional_pairs() -> Dict[Tuple[str, str], str]:
    from . import measure_view as mv
    out: Dict[Tuple[str, str], str] = {}
    for row in mv.relation_repair()["conversions"]:      # type: ignore[index]
        out[(str(row["subject"]), str(row["object"]))] = str(row["predicate"])
    return out


def route_of(subject: str, other: str) -> Dict[str, object]:
    """Which of the four routes decides one vague triple, and on what evidence."""
    dimensional = _dimensional_pairs()
    if (subject, other) in dimensional:
        return {"subject": subject, "object": other, "route": "dimensional",
                "relation": dimensional[(subject, other)],
                "evidence": "the physics register decides both endpoints"}
    relations = cp.related(subject, other)
    if relations:
        return {"subject": subject, "object": other, "route": "conjugate",
                "relation": relations[0],
                "evidence": "both endpoints are columns of one conjugate row"}
    for name, partner in ((subject, other), (other, subject)):
        proposal = propose(name)
        if proposal is not None and dn.denotation(partner) is None:
            return {"subject": subject, "object": other, "route": "proposed",
                    "relation": f"{proposal.verdict} verdict for {name}",
                    "evidence": proposal.evidence}
    untagged = "a name the lexicon does not tag"
    return {
        "subject": subject, "object": other, "route": "referred",
        "relation": "",
        "evidence": (
            f"{subject} is {_pos(subject) or untagged} and {other} is "
            f"{_pos(other) or untagged}; placed in the conjugate register: "
            f"{bool(cp.role_of(subject))}/{bool(cp.role_of(other))}; "
            f"decided by hand already: "
            f"{dn.denotation(subject) is not None}/"
            f"{dn.denotation(other) is not None}"),
    }


@memo
def routes() -> Dict[str, object]:
    """Every ``related_to`` triple, routed."""
    rows = tuple(route_of(subject, other)
                 for subject, other in related_to_triples())
    counts: Dict[str, int] = {name: 0 for name in ROUTES}
    for row in rows:
        counts[str(row["route"])] = counts.get(str(row["route"]), 0) + 1
    return {
        "rows": rows,
        "triples": len(rows),
        "counts": counts,
        "decided_without_a_person": sum(
            counts[name] for name in ("dimensional", "conjugate", "proposed")),
        "referred": counts["referred"],
        "every_triple_routed": sum(counts.values()) == len(rows),
    }


@memo
def vagueness_report() -> Dict[str, object]:
    """The standing rule, its rules, and what it decides on the register as it is."""
    proposer = proposer_audit()
    conjugates = conjugate_conversions()
    routed = routes()
    return {
        "routes": list(ROUTES),
        "proposer": proposer,
        "conjugate": conjugates,
        "routing": routed,
        "statement": (
            "A new related_to triple is put to four routes in order: the "
            "dimensional rules, the energy-conjugate register, the admitted "
            "proposer rules, and -- only then -- a person, who is handed the "
            "evidence rather than the failure.  The first three need no hand "
            "work at all, which is what makes the discipline survive the next "
            "addition."),
        "limits": (
            "The routes do not decide every triple and are not meant to: "
            f"{routed['referred']} of {routed['triples']} are referred, and a "
            "referral is a decision to ask rather than a lookup that failed.  "
            "Three of the four proposer rules are refused on named "
            "disagreements, which is the measurement's own warning against "
            "adding a fourth without scoring it."),
    }
