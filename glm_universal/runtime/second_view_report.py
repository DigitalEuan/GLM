"""``glm_universal.runtime.second_view_report`` -- the marks of Phase 96.

The measurement of round 8 of the order of work, *second readings*
(``studies/SECOND_VIEW_STUDY.md``), against the marks V1-V9 declared before
any code in :mod:`glm_universal.evaluation.second_view_cases`.  The register
marks (V1-V7) are :func:`glm_universal.reasoning.second_view.second_view_report`;
this module adds the dialect (V8), whose column-3 scripts run in fresh
interpreters, and the regression checks (V9).
"""

from __future__ import annotations

from typing import Dict, List

from ..evaluation import second_view_cases as C
from ..reasoning import python_speech as sp
from ..reasoning import second_view as sv

__all__ = ["dialect_marks", "regression_marks", "second_view_full_report"]


def _cpython(src: str):
    return sp._cpython_reference(src)[1]


def dialect_marks(run_scripts: bool = True) -> Dict[str, object]:
    """V8: the declared programs and refusals of the two builtins."""
    rows: List[Dict[str, object]] = []
    for cid, src in C.DIALECT_CASES:
        p = sp.speak(src)
        row = {"id": cid, "answered": p.refusal is None,
               "refusal": p.refusal}
        if p.refusal is None:
            ref = _cpython(src)
            row["equal"] = type(ref) is type(p.value) and ref == p.value
            if run_scripts:
                row["verified"] = sp.verify_payload(p)["verified"]
                row["mutant_rejected"] = not sp.verify_payload(
                    p, sp.mutated_script(p))["verified"]
        rows.append(row)
    refusals = []
    for cid, src, name in C.DIALECT_REFUSALS:
        p = sp.speak(src)
        refusals.append({"id": cid, "refusal": p.refusal, "declared": name,
                         "as_declared": p.refusal == name})
    answered_ok = all(r["answered"] and r.get("equal")
                      and (not run_scripts
                           or (r.get("verified") and r.get("mutant_rejected")))
                      for r in rows)
    return {"cases": rows, "refusals": refusals,
            "met": answered_ok and all(r["as_declared"] for r in refusals)}


def regression_marks() -> Dict[str, object]:
    """V9: the carried-fork figures of Phase 65 that the register's code
    path touches, recomputed."""
    from ..reasoning import carried_fork as cf
    k2 = cf.k2_second_reading()
    return {"k2_answered": k2.get("answered"), "k2_wrong": k2.get("wrong"),
            "met": k2.get("answered") == 4224 and k2.get("wrong") == 0}


def second_view_full_report(full: bool = True,
                            run_scripts: bool = True) -> Dict[str, object]:
    """Every mark of the study, V1-V9."""
    out = sv.second_view_report(full=full)
    out["V8"] = dialect_marks(run_scripts)
    out["V9"] = regression_marks()
    out["marks"] = {k: bool(out[k]["met"]) for k in
                    ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9")}
    return out
