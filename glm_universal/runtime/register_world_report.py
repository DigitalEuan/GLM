"""``glm_universal.runtime.register_world_report`` -- the marks of Phase 93.

The measurement of round 6 of the order of work, the register against the
world (``studies/REGISTER_WORLD_STUDY.md``), against the marks R1-R8 declared
before any code at the head of
:mod:`glm_universal.evaluation.register_world_cases`.  Kept apart from
:mod:`glm_universal.runtime.register_world` so that the answering path never
imports the evaluation.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..evaluation import register_world_cases as rc
from . import register_world as rw

__all__ = ["judge", "question_cases", "earlier_interval_cases",
           "completion_gate", "register_world_report"]


def judge(expected: object, answered: bool, text: str) -> str:
    """``met``, ``wrong`` (an answer that is not the declared one) or
    ``missed`` (a refusal where an answer, or the wrong refusal, was
    declared)."""
    low = text.lower()
    if isinstance(expected, str):
        if not answered:
            return "missed"
        return "met" if low.startswith(expected) else "wrong"
    kind = expected[0]                                  # type: ignore[index]
    if kind == "refuse":
        if answered:
            return "wrong"
        return "met" if expected[1] in text else "missed"  # type: ignore[index]
    if kind == "list":
        if not answered:
            return "missed"
        want = tuple(expected[1])                        # type: ignore[index]
        if not want:
            return "met" if low.startswith("none") else "wrong"
        head = text.split(" -- ", 1)[0]
        got = tuple(x.strip() for x in head.split(":", 1)[-1].split(","))
        return "met" if got == want else "wrong"
    return "wrong"


def question_cases(session=None) -> Dict[str, object]:
    """R3: every declared question through the router, as ``GLM.py -q``
    reads it."""
    from .router import route
    from .session import GeometricSession
    session = session or GeometricSession()
    groups = {"weight": rc.WEIGHT_CASES, "energy": rc.ENERGY_CASES,
              "configuration": rc.CONFIGURATION_CASES,
              "molecule": rc.MOLECULE_CASES}
    out: Dict[str, object] = {}
    rows: List[Dict[str, object]] = []
    for name, cases in groups.items():
        met = 0
        wrong: List[str] = []
        missed: List[str] = []
        for key, question, expected, _note in cases:
            r = route(session, question)
            verdict = judge(expected, r.answered, r.text)
            met += verdict == "met"
            if verdict == "wrong":
                wrong.append(key)
            elif verdict == "missed":
                missed.append(key)
            rows.append({"key": key, "group": name, "verdict": verdict,
                         "answered": r.answered, "surface": r.surface,
                         "text": r.text})
        out[name] = {"cases": len(cases), "met": met, "wrong": tuple(wrong),
                     "missed": tuple(missed)}
    total = sum(g["cases"] for g in out.values())        # type: ignore[index]
    met = sum(g["met"] for g in out.values())            # type: ignore[index]
    wrong = sum(len(g["wrong"]) for g in out.values())   # type: ignore[index]
    return {"groups": out, "cases": total, "met": met, "wrong": wrong,
            "rows": tuple(rows)}


def earlier_interval_cases(session=None) -> Dict[str, object]:
    """R6: Phase 63's eight interval questions, with the one declared move."""
    from ..evaluation.cognition_heldout import INTERVAL_QUESTIONS
    from ..evaluation.heldout import score_answer
    from .router import route
    from .session import GeometricSession
    session = session or GeometricSession()
    rows = []
    for q in INTERVAL_QUESTIONS:
        r = route(session, q.question)
        outcome = score_answer(q, r.answered, r.text)
        rows.append({"key": q.key, "outcome": outcome,
                     "moved": q.key in rc.DECLARED_MOVES})
    return {"cases": len(rows),
            "correct": sum(1 for r in rows if r["outcome"] in
                           ("correct", "correct-refusal")),
            "moved": tuple(r["key"] for r in rows if r["moved"]),
            "rows": tuple(rows)}


def completion_gate() -> Dict[str, object]:
    """R7: the nested gate's declared outcome, and what it moved."""
    from ..reasoning import element_completion as ec
    report = ec.element_completion_report()
    admitted = ec.admitted_rules()
    first = ec.first_gate_rules()
    # Every empty cell the first gate alone would have estimated, and which
    # of them the nested gate leaves empty.
    from ..data_objects import elements as el
    first_estimated = lost_cells = 0
    for c in ec.completed_table():
        rule = first.get(c.field)
        if rule is None or c.provenance == "measured":
            continue
        if rule.family == "group":
            value = ec._group_estimate(c.field, c.symbol)
        else:
            x = ec._value(el.element_by_symbol(c.symbol), rule.predictor)
            value = None if x is None or rule.slope is None else \
                rule.slope * x + rule.intercept  # type: ignore[operator]
        if value is None:
            continue
        first_estimated += 1
        lost_cells += c.provenance != "estimated"
    kept_same = all(admitted.get(f) is not None
                    and admitted[f].skill == first[f].skill
                    and admitted[f].domain == ""
                    for f in rc.COMPLETION_KEPT)
    outcome = {
        "demoted": tuple(report["demoted"]),
        "narrowed": dict(report["narrowed"]),
        "kept_unchanged": kept_same,
    }
    declared = (outcome["demoted"] == rc.COMPLETION_DEMOTED
                and outcome["narrowed"] == rc.COMPLETION_NARROWED
                and kept_same)
    return {
        "outcome": outcome, "as_declared": declared,
        "coverage": report["coverage"],
        "dispositions": report["dispositions"]["counts"],
        "accounted": report["dispositions"]["accounted"],
        "safety": report["safety"]["holds"],
        "first_gate_estimated": first_estimated,
        "lost_cells": lost_cells,
        "nested_gate": report["nested_gate"],
    }


def register_world_report(session=None) -> Dict[str, object]:
    """Everything the round measures, against marks R1-R7 (R8 is the build)."""
    from .session import GeometricSession
    before = rw.register_digest()
    session = session or GeometricSession()
    world = rw.world_report()
    questions = question_cases(session)
    audit = rw.mutation_audit()
    earlier = earlier_interval_cases(session)
    gate = completion_gate()
    after = rw.register_digest()
    molecules = rw.molecule_table()
    mol_flag_without_element = [
        r["name"] for r in molecules if r["verdict"] == "discrepant"
        and not any(rw.cell(s, "atomic_weight_u").verdict == "discrepant"
                    for s in r["elements"])]   # type: ignore[union-attr]
    marks: Dict[str, Optional[bool]] = {
        "R1": bool(world["accounted"]) and world["cells"] == 354,
        "R2": before == after,
        "R3": questions["met"] == questions["cases"]
        and questions["wrong"] == 0,
        "R4": bool(audit["holds"]),
        "R5": all(r["verdict"] in rw.VERDICTS for r in molecules)
        and not mol_flag_without_element,
        "R6": earlier["correct"] == earlier["cases"]
        and earlier["moved"] == tuple(rc.DECLARED_MOVES),
        "R7": bool(gate["as_declared"]) and bool(gate["safety"])
        and bool(gate["accounted"])
        and gate["coverage"]["estimated"] + gate["lost_cells"]
        == gate["first_gate_estimated"],
        "R8": None,
    }
    return {"world": world, "questions": questions, "audit": audit,
            "earlier": earlier, "gate": gate,
            "register": {"before": before, "after": after},
            "marks": marks}
