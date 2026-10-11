"""``glm_universal.runtime.derivation_three_report`` -- the marks of Phase 118.

The measurement of ``studies/DERIVATION_THREE_STUDY.md`` against the marks
N1-N10 declared before any code in
:mod:`glm_universal.evaluation.derivation_three_cases`.  The marks that stay
below the frames are :mod:`.derivation_three_marks`; this module adds the
two that read through the frames the CLI uses:

* **N5** -- every answered reading of N1-N3 (and the refutations, which
  carry a script too) is run through its column-3 script in a fresh
  ``python3 -I`` interpreter, and again with its claim altered;
* **N9** -- Phase 107's report, with :data:`PHASE_107_NARROWED` applied,
  still meets all its marks; and no outside question, Set B question or
  evaluation case reads differently with the Phase 118 readings on and off
  (every text is framed as before, and every text that reaches a Phase 107
  frame is read both ways and compared).

Nothing here makes a float (D7).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..evaluation import derivation_three_cases as C
from . import derivation_three_frames as D3
from . import derivation_three_marks as M
from . import derivation_two_frames as DF
from .question_frames import run_gate

__all__ = ["gate_mark", "phase_107_mark", "unmoved_mark",
           "derivation_three_report"]


def _gate(script: str) -> bool:
    return run_gate(script, seconds=60)[0]


def gate_mark() -> Dict[str, object]:
    """N5."""
    rows = []
    for group in (C.INEQUALITIES, C.RATE_DISTORTION, C.ROBIN):
        for case in group:
            cid, q = case[0], case[1]
            rd = DF.read_operation(q)
            mut = DF.mutated_operation(q)
            rows.append({"id": cid, "answered": rd.answered, "code": rd.code,
                         "gate": _gate(rd.script),
                         "mutant_rejected": not _gate(mut.script)})
    ok = sum(1 for r in rows if r["gate"])
    mr = sum(1 for r in rows if r["mutant_rejected"])
    return {"rows": rows, "readings": len(rows), "verified": ok,
            "mutants_rejected": mr,
            "met": bool(rows) and ok == len(rows) == mr}


def refusal_mark() -> Dict[str, object]:
    """N4 through the frames: the reading is refused with the code.
    Narrowed by Phase 119 (``derivation_four_cases.PHASE_118_NARROWED``,
    declared before that round's code): a refusal the later round answers
    instead is met when the reading is answered with the declared
    fragment."""
    from ..evaluation import derivation_four_cases as C4
    narrowed = dict(C4.PHASE_118_NARROWED)
    rows = []
    for cid, text, code in C.REFUSALS:
        rd = DF.read_operation(text)
        if cid in narrowed:
            rows.append({"id": cid, "code": rd.code, "want": code,
                         "narrowed_by": "Phase 119",
                         "as_declared": rd.answered and
                         narrowed[cid] in rd.value})
            continue
        rows.append({"id": cid, "code": rd.code, "want": code,
                     "as_declared": (not rd.answered) and rd.code == code})
    return {"rows": rows, "as_declared": sum(r["as_declared"] for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def phase_107_mark(battery: Optional[int] = None) -> Dict[str, object]:
    from . import derivation_two_report as R2
    rep = R2.derivation_two_report(run_scripts=True, battery=battery)
    return {"met_marks": rep["met"], "of": rep["of"],
            "missed": [k for k, v in rep["marks"].items() if not v.get("met")],
            "met": rep["met"] == rep["of"]}


def unmoved_mark() -> Dict[str, object]:
    """N9, second half: frame and reading of every other text, with the
    Phase 118 readings on and off."""
    from ..evaluation import question_set_b_cases as qc
    from ..evaluation.cases import CASES
    from . import question_frames as qf
    texts = [(f"O{it.index:03d}", it.text) for it in qc.outside()] + \
        [(it.id, it.query) for it in qc.set_b()] + \
        [(c.id, c.question) for c in CASES]

    def look(text: str):
        got = qf.frame_of(text)
        if got is None:
            return None
        frame, givens = got
        if frame.source != "P2":
            return (frame.name,)
        rd = frame.answer(givens)
        return (frame.name, rd.answered, rd.code, rd.value)
    moved: List[str] = []
    read_both = 0
    saved = D3.ENABLED[0]
    try:
        D3.ENABLED[0] = False
        before = {key: look(text) for key, text in texts}
        D3.ENABLED[0] = True
        for key, text in texts:
            after = look(text)
            if after is not None and len(after) > 1:
                read_both += 1
            if after != before[key]:
                moved.append(key)
    finally:
        D3.ENABLED[0] = saved
    return {"texts_checked": len(texts), "read_both_ways": read_both,
            "moved": moved, "met": not moved}


def derivation_three_report(battery: Optional[int] = None,
                            outside: bool = True) -> Dict[str, object]:
    n1 = M.inequality_marks()
    n2 = M.rd_marks()
    n3 = M.robin_marks()
    low = M.refusal_marks_low()
    high = refusal_mark()
    n4 = {"layer": low, "frames": high, "met": low["met"] and high["met"]}
    n5 = gate_mark()
    n6 = M.inequality_battery(battery)
    n7 = M.rd_battery(battery)
    n8 = M.robin_battery(battery)
    if outside:
        p107 = phase_107_mark(100 if battery else None)
        um = unmoved_mark()
        n9 = {"phase_107": p107, "unmoved": um,
              "met": p107["met"] and um["met"]}
    else:
        n9 = {"met": None}
    n10 = M.lean_mark()
    marks = {"N1": n1, "N2": n2, "N3": n3, "N4": n4, "N5": n5, "N6": n6,
             "N7": n7, "N8": n8, "N9": n9, "N10": n10}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
