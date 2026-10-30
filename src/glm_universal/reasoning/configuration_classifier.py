"""``glm_universal.reasoning.configuration_classifier`` -- the configuration
reading ``L5`` in the deep-hole answering path, with certified answers and
certified absences (Phase 123, part B).

The question
------------
Phase 122 showed ``L5`` separates every pair of reference holes, but it was a
study instrument: the deep-hole classifier still named a hole with the
ladder's readings, and ``GLM.DeepHoleFailure.per_type_absent`` was
instantiated nowhere.  ``studies/LATTICE_COMPLETION_STUDY.md`` §2.B makes
``L5`` the classifier's reading under a declared answer rule.

The answer rule
---------------
For a query profile ``x`` let ``T`` be the nearest reference and ``B_T`` the
distance from ``T``'s reference to the nearest other reference.  **Answer**
``T`` when ``2 d(x, p_T) < B_T``; otherwise **refuse**.  Where the rule
answers, ``T`` is provably the strict nearest reference
(``GLM.LatticeCompletion.config_answer_sound``).  ``r_T = B_T / 2`` is the
type's **certified radius**.

The absences
------------
For every type ``U`` other than the answer, "this hole is not of type ``U``"
is issued when ``d(x, p_U) > r_U`` -- ``per_type_absent`` at ``L5``
(``GLM.LatticeCompletion.config_absent``).  It is a theorem under
faithfulness of ``U`` at ``r_U``; that hypothesis is not measured here, it is
*tested* on held-out queries: a query outside its own type's radius would
draw a false absence, and :func:`classify_queries` counts them.

The profiles are read from :mod:`configuration_queries` (the 44 queries and
the ten references at 1920 starts) and, for the 23-reference table, from
:mod:`hole_census` -- twenty references from the census as it was
pre-registered, and all 23 once :mod:`patience_census` (a post-hoc follow-up)
supplies the three centres the census left uncertified.  Nothing here
decodes a lattice point.

Exactness
---------
Integers and :class:`~fractions.Fraction` only.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import configuration_queries as cq
from . import configuration_reading as cr
from . import hole_census as hc
from . import patience_census as pc
from . import share_ensemble as se

__all__ = [
    "LEAN_MODULE", "EXPECTED_JOINT", "certified_radii", "name",
    "reference_table", "census_table", "classify_queries",
    "configuration_classifier_report",
]

#: The Lean file the rule and the absences are proved in.
LEAN_MODULE: str = "RequestProject/GLM/LatticeCompletion.lean"

#: What the escalation round recorded at ``(joint, 1920)``: the stopping rule.
EXPECTED_JOINT: Tuple[int, int] = (40, 44)

Profile = Tuple[Tuple[Tuple[int, int], Fraction], ...]
Table = Sequence[Tuple[str, Profile]]


def certified_radii(table: Table) -> Dict[str, Fraction]:
    """``r_T = B_T / 2`` for each reference of the table."""
    out: Dict[str, Fraction] = {}
    for label, profile in table:
        nearest = min(cr.configuration_distance(profile, other)
                      for name, other in table if name != label)
        out[label] = nearest / 2
    return out


def name(profile: Profile, table: Table,
         radii: Optional[Dict[str, Fraction]] = None) -> Dict[str, object]:
    """The answer rule and the absences for one query profile."""
    radii = radii if radii is not None else certified_radii(table)
    distances = [(label, cr.configuration_distance(profile, reference))
                 for label, reference in table]
    best = min(d for _l, d in distances)
    nearest = [l for l, d in distances if d == best]
    label = nearest[0] if len(nearest) == 1 else None
    answer = (label if label is not None and best < radii[label] else None)
    absences = tuple(l for l, d in distances
                     if l != answer and d > radii[l])
    return {"nearest": label, "distance": best, "answer": answer,
            "radius": radii[label] if label is not None else None,
            "absences": absences, "distances": tuple(distances)}


def reference_table(data: Optional[Dict[str, object]] = None) -> Table:
    """The ten reference profiles at 1920 starts, at the reference seed."""
    data = data if data is not None else cq.current()
    if data is None:
        return ()
    return tuple((str(r["label"]), tuple(r["profile"]))
                 for r in data["references"])


def census_table(data: Optional[Dict[str, object]] = None,
                 follow_up: bool = True) -> Table:
    """The reference profiles at 1920 starts: the ten, the census's, and --
    with ``follow_up`` -- the post-hoc centres of :mod:`patience_census`."""
    data = data if data is not None else cq.current()
    census = hc.current()
    if data is None or census is None:
        return ()
    rows = dict(reference_table(data))
    holes = list(census["holes"])
    if follow_up:
        extra = pc.current()
        if extra is not None:
            holes += list(extra["holes"])
    for hole in holes:
        record = se.multiset(hole["reference"], cq.STARTS)
        rows[str(hole["label"])] = cr.configuration_profile(record)
    return tuple((label, rows[label]) for label in cr.NIEMEIER_TYPES
                 if label in rows)


def classify_queries(table: Table,
                     data: Optional[Dict[str, object]] = None
                     ) -> Dict[str, object]:
    """Every used query through the answer rule against ``table``."""
    data = data if data is not None else cq.current()
    radii = certified_radii(table)
    rows: List[Dict[str, object]] = []
    for query in data["queries"]:
        if not query["used"]:
            continue
        reading = name(tuple(query["profile"]), table, radii)
        truth = str(query["truth"])
        own = dict(reading["distances"])[truth]
        rows.append({
            "query": str(query["name"]), "kind": str(query["kind"]),
            "truth": truth, "nearest": reading["nearest"],
            "nearest_correct": reading["nearest"] == truth,
            "answer": reading["answer"],
            "verdict": ("refused" if reading["answer"] is None
                        else "correct" if reading["answer"] == truth
                        else "wrong"),
            "own_distance": own, "own_radius": radii[truth],
            "within_own_radius": own <= radii[truth],
            "false_absence": truth in reading["absences"],
            "absences": len(reading["absences"]),
            "joint_correct": bool(query["joint_correct"]),
        })
    others = len(table) - 1
    return {
        "references": len(table), "radii": radii,
        "rows": tuple(rows), "queries": len(rows),
        "answered": sum(1 for r in rows if r["answer"] is not None),
        "correct": sum(1 for r in rows if r["verdict"] == "correct"),
        "wrong": sum(1 for r in rows if r["verdict"] == "wrong"),
        "refused": sum(1 for r in rows if r["verdict"] == "refused"),
        "nearest_correct": sum(1 for r in rows if r["nearest_correct"]),
        "within_radius": sum(1 for r in rows if r["within_own_radius"]),
        "false_absences": sum(1 for r in rows if r["false_absence"]),
        "absences": sum(int(r["absences"]) for r in rows),
        "absence_slots": len(rows) * others,
        "joint_correct": sum(1 for r in rows if r["joint_correct"]),
    }


def configuration_classifier_report() -> Dict[str, object]:
    """B1--B4 and B6 from the stored profiles; B5 is the evaluation's."""
    data = cq.current()
    if data is None:
        return {"available": False, "lean": LEAN_MODULE, "reason": (
            "the query profiles are absent or stale; re-take them with "
            "python3 -m glm_universal.tools configuration-classifier "
            "--write")}
    ten = classify_queries(reference_table(data), data)
    table20 = census_table(data, follow_up=False)
    census_wide = classify_queries(table20, data) if table20 else None
    table23 = census_table(data)
    twenty_three = (classify_queries(table23, data)
                    if len(table23) == len(cr.NIEMEIER_TYPES) else None)
    b1 = (ten["joint_correct"], ten["queries"]) == EXPECTED_JOINT
    return {
        "available": True, "lean": LEAN_MODULE, "starts": cq.STARTS,
        "ten": ten, "census_wide": census_wide, "twenty_three": twenty_three,
        "marks": {
            "B1": b1,
            "B2": b1 and ten["answered"] >= 41 and ten["wrong"] == 0,
            "B3": b1 and ten["nearest_correct"] == ten["queries"],
            "B4": b1 and ten["false_absences"] == 0
                  and ten["within_radius"] == ten["queries"],
            "B6": twenty_three is not None and twenty_three["wrong"] == 0,
        },
    }
