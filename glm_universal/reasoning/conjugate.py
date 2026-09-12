"""``glm_universal.reasoning.conjugate`` -- transporting a relation across domains.

The question this closes
------------------------
``heat : temperature :: force : ?``  The analogy layer of
:mod:`glm_universal.reasoning.analogy_models` could say precisely why it had
no answer -- the lexicon's ``temperature drives heat`` reaches nothing from
``force``, and ``related_to`` says only that a link exists -- and a refusal
with a stated reason is a good answer to give.  It is not, though, the answer.

:mod:`glm_universal.data_objects.conjugate_pairs` supplies the missing half:
a register whose rows *span* the energy domains, each row an effort, an extent
and the transfer they make, checked against the physics register's own
exponents.  This module turns a row into an answer, and -- because that is the
part which generalises -- says under what rule it is allowed to.

When a relation may be transported
----------------------------------
A relation ``R`` recognised between ``A`` and ``B`` may be carried to ``C``
exactly when all four of these hold.  They are the criteria, not a description
of them: :func:`admissibility` returns this list, :func:`transport` checks each
one and names the first that fails, and nothing else in the module may refuse
for a reason that is not on it.

``determinate``
    ``R`` names a step, not the bare existence of a link.  ``related_to``
    fails here and is why it is in
    :data:`~glm_universal.reasoning.analogy_models.VAGUE_RELATIONS`: from
    ``heat related_to temperature`` there is nothing to carry.

``role_typed``
    ``R`` runs between two named columns of a register, so *which side* of the
    relation a term can occupy is decidable rather than a matter of reading.
    ``effort_of`` runs from ``effort`` to ``transfer``; ``force`` is an
    effort, ``entropy`` is neither.

``functional``
    ``R`` is single-valued in the direction it is used, so the transported
    position holds one name and the answer is *derived* rather than chosen.
    On this register the three relations are bijections between their two
    columns, which is stronger and is what makes the reverse direction
    legitimate as well.

``grounded``
    the register can check its own rows.  Here that is exact: effort and
    extent are physics quantities whose EXT10 exponents and decimal scales sum
    to those of ``energy``.  A row nobody can check is a row nobody should
    transport.

Direction, and why the reverse is not a guess
---------------------------------------------
``heat : temperature`` is recognised as ``temperature effort_of heat``: ``A``
occupies the ``transfer`` column and ``B`` the ``effort`` column.  ``force``
occupies the ``effort`` column, which is ``B``'s side, so the relation is
applied **in reverse**: the unique transfer whose effort is ``force``.  That
is ``work``, and the answer is unique because the relation is a bijection --
the ``functional`` criterion above, which is checked and not assumed.

The rule is stated once and applies to every question of the shape: transport
forward when ``C`` occupies ``A``'s column, in reverse when it occupies
``B``'s, and refuse when it occupies neither -- saying which column it *does*
occupy, which is a fact about ``C`` and not a report of a failed search.

What is still refused, and why that is right
--------------------------------------------
* ``heat : temperature :: entropy : ?`` -- ``entropy`` is an extent.  The
  relation runs between transfers and efforts, so there is nothing to apply,
  and the register says so rather than falling back on the nearest word.
* ``heat : temperature :: justice : ?`` -- ``justice`` occupies no column of
  any register here.  This is the open-vocabulary boundary, and it is the
  same refusal the rest of the system gives.
* ``heat : temperature :: entropy_flux : ?`` and every other ``C`` in the
  *same row* as ``A``: the transport returns an operand, which is no answer.

Exactness
---------
No metric is consulted and no coordinate is compared.  Everything here is a
table lookup over names, and the one arithmetic fact it rests on -- that a
row's effort times its extent is an energy -- is integer arithmetic on the
physics register's exponents, run by
:func:`~glm_universal.data_objects.conjugate_pairs.conjugate_audit`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..data_objects import conjugate_pairs as cp

__all__ = [
    "CRITERIA", "REPORT_CASES", "Transport",
    "admissibility", "transport", "conjugate_report",
]


#: The four criteria, each with the sentence that states it and the check that
#: decides it.  ``transport`` reports the first one a question fails.
CRITERIA: Tuple[Tuple[str, str, str], ...] = (
    ("determinate",
     "the relation names a step rather than the bare existence of a link",
     "a relation of conjugate_pairs.RELATIONS is named; related_to is not one"),
    ("role_typed",
     "the relation runs between two named columns of a register, so which "
     "side a term may occupy is decidable",
     "conjugate_pairs.role_of returns the column of each of A, B and C"),
    ("functional",
     "the relation is single-valued in the direction used, so the answer is "
     "derived rather than chosen",
     "each relation is a bijection between its two columns, which "
     "conjugate_audit checks by requiring every name to occupy one role"),
    ("grounded",
     "the register can check its own rows, so a row cannot be added without "
     "being checkable",
     "conjugate_audit: effort and extent are physics quantities whose EXT10 "
     "exponents and scales sum to those of energy"),
)


def admissibility() -> Tuple[Dict[str, str], ...]:
    """The criteria, as a mapping per criterion."""
    return tuple({"criterion": name, "statement": statement, "checked_by": how}
                 for name, statement, how in CRITERIA)


@dataclass(frozen=True)
class Transport:
    """What the conjugate register made of ``A : B :: C : ?``.

    ``answer`` is ``None`` exactly when ``refusal`` is set.  ``failed`` names
    the admissibility criterion that stopped it, and is empty when none did.
    """

    relation: str
    orientation: Tuple[str, str]
    direction: str = ""
    answer: Optional[str] = None
    candidates: Tuple[str, ...] = ()
    refusal: Optional[str] = None
    failed: str = ""
    steps: Tuple[Tuple[str, str], ...] = ()
    witness: Dict[str, str] = field(default_factory=dict)

    @property
    def unique(self) -> bool:
        """Whether exactly one candidate survived."""
        return len(self.candidates) == 1

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "relation": self.relation,
            "orientation": list(self.orientation),
            "direction": self.direction,
            "answer": self.answer,
            "candidates": list(self.candidates),
            "unique": self.unique,
            "refusal": self.refusal,
            "failed_criterion": self.failed,
            "witness": dict(self.witness),
        }


def _statement(relation: str, subject: str, other: str) -> str:
    """The register's own sentence for a relation between two names."""
    return f"{subject} {relation} {other}"


def transport(a: str, b: str, c: str) -> Optional[Transport]:
    """``A : B :: C : ?`` through the energy-conjugate register.

    Returns ``None`` -- the model *declining*, which is different from
    refusing -- when the register states no relation between ``A`` and ``B``.
    Otherwise the relation is named, and the result either carries an answer
    or a refusal that says which admissibility criterion failed.
    """
    relations = cp.related(a, b)
    if not relations:
        return None
    if len(relations) > 1:          # pragma: no cover -- audited as empty
        raise AssertionError(
            f"conjugate: {a} and {b} stand in {relations}, which the audit "
            f"forbids")
    relation = relations[0]
    left, right = cp.RELATION_COLUMNS[relation]
    row_ab = cp.row_of_name(a)
    assert row_ab is not None
    role_a, role_b = cp.role_of(a), cp.role_of(b)
    assert role_a is not None and role_b is not None
    subject, other = (a, b) if (role_a, role_b) == (left, right) else (b, a)
    orientation = (str(role_a), str(role_b))
    witness = {
        "relation": relation,
        "statement": _statement(relation, subject, other),
        "a_role": str(role_a), "b_role": str(role_b),
        "row": row_ab.domain,
    }
    steps: List[Tuple[str, str]] = [
        ("relation",
         f"The conjugate register states the relation outright: "
         f"{_statement(relation, subject, other)}, in the {row_ab.domain} row "
         f"({row_ab.definition}).  {a} occupies the {role_a} column and {b} "
         f"the {role_b} column."),
    ]

    role_c = cp.role_of(c)
    witness["c_role"] = str(role_c)
    if role_c is None:
        return Transport(
            relation=relation, orientation=orientation,
            refusal=(f"{c} occupies no column of the conjugate register, so "
                     f"the relation has no side for it to enter on; the "
                     f"register's names are {list(cp.names())}"),
            failed="role_typed", steps=tuple(steps), witness=witness)
    if role_c not in (role_a, role_b):
        return Transport(
            relation=relation, orientation=orientation,
            refusal=(f"{c} occupies the {role_c} column, and {relation} runs "
                     f"between the {left} and {right} columns, so there is "
                     f"nothing to apply it to"),
            failed="role_typed", steps=tuple(steps), witness=witness)
    row_c = cp.row_of_name(c)
    assert row_c is not None
    if row_c.domain == row_ab.domain:
        return Transport(
            relation=relation, orientation=orientation,
            refusal=(f"{c} is in the same {row_ab.domain} row as {a} and {b}, "
                     f"so transporting the relation returns an operand rather "
                     f"than an answer"),
            failed="functional", steps=tuple(steps), witness=witness)

    if role_c == role_a:
        direction, target_role = "forward", str(role_b)
    else:
        direction, target_role = "reverse", str(role_a)
    answer = row_c.column(target_role)
    witness.update({"direction": direction, "target_role": target_role,
                    "target_row": row_c.domain, "answer": answer})
    steps.append((
        "direction",
        f"{c} occupies the {role_c} column, which is "
        f"{'A' if role_c == role_a else 'B'}'s side, so the relation is "
        f"applied {'forward' if direction == 'forward' else 'in reverse'}.  "
        f"It is a bijection between the {left} and "
        f"{right} columns -- every name of the register occupies exactly one "
        f"role -- so the {target_role} it reaches is unique and is derived, "
        f"not chosen."))
    steps.append((
        "answer",
        f"In the {row_c.domain} row ({row_c.definition}) the {target_role} "
        f"conjugate to {c} is {answer}, so "
        f"{_statement(relation, *((answer, c) if target_role == left else (c, answer)))}."))
    return Transport(
        relation=relation, orientation=orientation, direction=direction,
        answer=answer, candidates=(answer,), steps=tuple(steps),
        witness=witness)


# ===========================================================================
# THE REPORT
# ===========================================================================

#: The questions the report re-solves.  Each is a question a user could type;
#: the expectation is what the register requires, not a transcript.  An empty
#: expected answer is a refusal, and the fourth column names the criterion
#: that must fail.
REPORT_CASES: Tuple[Tuple[str, str, str, str, str], ...] = (
    # A, B, C, expected answer ("" = refusal), expected failed criterion
    ("heat", "temperature", "force", "work", ""),
    ("temperature", "heat", "voltage", "electrical_work", ""),
    ("heat", "temperature", "pressure", "flow_work", ""),
    ("temperature", "entropy", "force", "length", ""),
    ("pressure", "volume", "voltage", "charge", ""),
    ("heat", "entropy", "work", "length", ""),
    ("entropy", "heat", "area", "surface_work", ""),
    ("work", "force", "heat", "temperature", ""),
    ("heat", "temperature", "entropy", "", "role_typed"),
    ("heat", "temperature", "justice", "", "role_typed"),
    ("heat", "temperature", "temperature", "", "functional"),
)


def conjugate_report() -> Dict[str, object]:
    """The register, its audit, the admissibility rule, and the cases re-solved."""
    audit = cp.conjugate_audit()
    rows: List[Dict[str, object]] = []
    agree = 0
    for a, b, c, expected, expected_failure in REPORT_CASES:
        result = transport(a, b, c)
        answer = "" if result is None or result.answer is None else result.answer
        failed = "" if result is None else result.failed
        ok = (result is not None and answer == expected
              and failed == expected_failure)
        agree += int(ok)
        rows.append({
            "question": f"{a} : {b} :: {c} : ?",
            "relation": "" if result is None else result.relation,
            "direction": "" if result is None else result.direction,
            "answer": answer,
            "refusal": "" if result is None or result.refusal is None
                       else result.refusal,
            "failed_criterion": failed,
            "expected_answer": expected,
            "expected_failed_criterion": expected_failure,
            "as_expected": ok,
        })
    answered = tuple(row for row in rows if row["answer"])
    return {
        "audit": audit,
        "criteria": admissibility(),
        "criterion_names": [name for name, _, _ in CRITERIA],
        "cases": tuple(rows),
        "cases_total": len(rows),
        "cases_as_expected": agree,
        "answered": len(answered),
        "refused": len(rows) - len(answered),
        "headline": next(row for row in rows
                         if row["question"] == "heat : temperature :: force : ?"),
    }
