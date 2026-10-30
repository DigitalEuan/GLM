"""``glm_universal.runtime.unpacking_report`` -- the marks of Phase 97.

The measurement of ``studies/UNPACKING_RESCORE_STUDY.md`` against the marks
U1-U5 and R1-R7 declared before any code in
:mod:`glm_universal.evaluation.unpacking_cases`.  The dialect marks (U1-U5)
run column-3 scripts in fresh interpreters, so they live in the runtime
layer; the register marks (R1-R7) are
:func:`glm_universal.reasoning.second_view.on_demand_report`.

The no-regression mark reads a baseline frozen at the declarations' commit,
before the dialect was widened: every earlier declared dialect program's
outcome (its value literal or its refusal name), and the declared programs of
this round as the old dialect answered them (:data:`BASELINE`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from ..evaluation import unpacking_cases as C
from ..reasoning import python_speech as sp

__all__ = ["BASELINE", "earlier_programs", "outcome", "freeze_baseline",
           "program_marks", "refusal_marks", "rescore_mark", "no_regression",
           "unpacking_report"]

#: The outcomes before the round (mark U5, and the "before" column).
BASELINE = (Path(__file__).resolve().parent.parent / "reasoning" / "_data"
            / "unpacking_baseline.json")


def earlier_programs() -> List[Tuple[str, str]]:
    """``(key, source)`` for every dialect program an earlier round
    declared."""
    from ..evaluation import imperative_cases as I
    from ..evaluation import planner_loop_cases as L
    from ..evaluation import python_speech_cases as P
    from ..evaluation import second_view_cases as S
    from ..evaluation import third_sort_cases as T
    from ..reasoning import confidence_floor_marks as CF
    from ..reasoning import decoder_confidence_marks as DC
    out: List[Tuple[str, str]] = []
    out += [(f"p64-value:{c}", s) for c, s in P.VALUE_CASES]
    out += [(f"p64-refusal:{c}", s) for c, s, _ in P.PHASE64_REFUSAL_CASES]
    for name in ("STRING_METHOD_CASES", "LIST_CASES", "DICT_CASES"):
        out += [(f"p94-{name}:{c}", s) for c, s in getattr(T, name)]
    out += [(f"p94-refusal:{c}", s) for c, s, _ in T.DIALECT_REFUSALS]
    out += [(f"p95-program:{c}", s) for c, s in I.PROGRAM_CASES]
    out += [(f"p95-say:{c}", s) for c, s, _ in I.SAY_CASES]
    out += [(f"p95-say-refusal:{c}", s) for c, s, _ in I.SAY_REFUSALS]
    for name in ("DERIVE_CASES", "ASK_CASES", "SOLVE_CASES", "LOOP_CASES"):
        out += [(f"p89-{name}:{c}", s) for c, s, _ in getattr(L, name)]
    out += [(f"p96-case:{c}", s) for c, s in S.DIALECT_CASES]
    out += [(f"p96-refusal:{c}", s) for c, s, _ in S.DIALECT_REFUSALS]
    out += [(f"p83-confidence:{i}", s)
            for i, (s, _) in enumerate(DC.DECLARED_PROGRAMS)]
    out += [(f"p84-floor:{i}", s)
            for i, (s, _) in enumerate(CF.DECLARED_PROGRAMS)]
    return out


def this_round_programs() -> List[Tuple[str, str]]:
    """``(key, source)`` for every program this round declared."""
    out = [(f"U1:{C.RESCORED[0]}", C.RESCORED[1])]
    out += [(f"U2:{c}", s) for c, s in C.CALL_CASES]
    out += [(f"U3:{c}", s) for c, s in C.VARARG_CASES]
    out += [(f"U4:{c}", s) for c, s, _ in C.UNPACK_REFUSALS]
    return out


def outcome(src: str) -> List[str]:
    """``["value", literal]`` or ``["refusal", name]`` for one program."""
    p = sp.speak(src)
    if p.refusal is None:
        return ["value", p.value_literal]
    return ["refusal", p.refusal]


def freeze_baseline() -> Dict[str, object]:
    """Take the baseline (run once, at the declarations' commit)."""
    data = {"earlier": {k: outcome(s) for k, s in earlier_programs()},
            "before": {k: outcome(s) for k, s in this_round_programs()},
            "battery": _battery_summary()}
    BASELINE.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    return data


#: The one earlier program U1 moves by declaration: Phase 96's
#: ``views-clean`` is the very source U1 re-scores.
DECLARED_MOVES: Tuple[str, ...] = ("p96-case:views-clean",)


def _battery_summary() -> Dict[str, int]:
    b = sp.differential_battery()
    return {k: v for k, v in b.items() if isinstance(v, int)}


def _cpython(src: str):
    return sp._cpython_reference(src)[1]


def _program_row(cid: str, src: str, run_scripts: bool) -> Dict[str, object]:
    p = sp.speak(src)
    row: Dict[str, object] = {"id": cid, "answered": p.refusal is None,
                              "refusal": p.refusal}
    if p.refusal is None:
        ref = _cpython(src)
        row["value"] = p.value_literal
        row["equal"] = type(ref) is type(p.value) and ref == p.value
        if run_scripts:
            row["verified"] = sp.verify_payload(p)["verified"]
            row["mutant_rejected"] = not sp.verify_payload(
                p, sp.mutated_script(p))["verified"]
    row["ok"] = bool(row["answered"] and row.get("equal")
                     and (not run_scripts or (row.get("verified")
                                              and row.get("mutant_rejected"))))
    return row


def program_marks(cases, run_scripts: bool = True) -> Dict[str, object]:
    """U2 or U3: each program equal to CPython, script verified, mutant
    rejected."""
    rows = [_program_row(cid, src, run_scripts) for cid, src in cases]
    return {"cases": rows, "passed": sum(r["ok"] for r in rows),
            "of": len(rows), "met": all(r["ok"] for r in rows)}


def rescore_mark(run_scripts: bool = True) -> Dict[str, object]:
    """U1: the refused Phase 96 program, and the whole of Phase 96's V8."""
    from .second_view_report import dialect_marks
    row = _program_row(C.RESCORED[0], C.RESCORED[1], run_scripts)
    v8 = dialect_marks(run_scripts)
    return {"case": row, "phase96_v8_met": v8["met"],
            "phase96_cases": sum(bool(r["answered"] and r.get("equal"))
                                 for r in v8["cases"]),
            "phase96_refusals": sum(r["as_declared"] for r in v8["refusals"]),
            "met": row["ok"] and v8["met"]}


def refusal_marks() -> Dict[str, object]:
    """U4: each declared refusal by its declared name."""
    rows = []
    for cid, src, name in C.UNPACK_REFUSALS:
        p = sp.speak(src)
        rows.append({"id": cid, "refusal": p.refusal, "declared": name,
                     "as_declared": p.refusal == name})
    return {"cases": rows, "passed": sum(r["as_declared"] for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def no_regression() -> Dict[str, object]:
    """U5: no earlier declared program moves; the battery is unchanged."""
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    moved, moved_as_declared = [], []
    programs = earlier_programs()
    for key, src in programs:
        if outcome(src) != base["earlier"][key]:
            (moved_as_declared if key in DECLARED_MOVES
             else moved).append(key)
    battery = _battery_summary()
    return {"programs": len(programs), "moved": moved,
            "moved_as_declared": moved_as_declared,
            "battery": battery, "battery_before": base["battery"],
            "met": (not moved and battery == base["battery"]
                     and sorted(moved_as_declared) == sorted(DECLARED_MOVES))}


def before() -> Dict[str, object]:
    """The declared programs as the dialect answered them before the
    round."""
    base = json.loads(BASELINE.read_text(encoding="utf-8"))["before"]
    answered = sorted(k for k, v in base.items() if v[0] == "value")
    return {"programs": len(base), "answered_before": len(answered),
            "refusals_before": sorted({v[1] for v in base.values()
                                       if v[0] == "refusal"})}


def unpacking_report(full: bool = True,
                     run_scripts: bool = True) -> Dict[str, object]:
    """Every mark of the study, U1-U5 and R1-R7."""
    from ..reasoning import second_view as sv
    out: Dict[str, object] = {
        "U1": rescore_mark(run_scripts),
        "U2": program_marks(C.CALL_CASES, run_scripts),
        "U3": program_marks(C.VARARG_CASES, run_scripts),
        "U4": refusal_marks(),
        "U5": no_regression(),
        "before": before(),
    }
    out.update(sv.on_demand_report(full=full))
    out["marks"] = {k: bool(out[k]["met"]) for k in
                    ("U1", "U2", "U3", "U4", "U5", "R1", "R2", "R3", "R4",
                     "R5", "R6", "R7")}
    return out
