"""``glm_universal.runtime.derivation_four_report`` -- the marks of Phase 119.

The measurement of ``studies/DERIVATION_FOUR_STUDY.md`` against the marks
P1-P10 declared before any code in
:mod:`glm_universal.evaluation.derivation_four_cases`.  The marks that stay
below the router are :mod:`.derivation_four_marks`; this module adds the ones
that read through the frames the CLI uses:

* **P4** (frames half) -- every declared refusal is refused with its code
  through :func:`~.derivation_two_frames.read_operation`;
* **P5** -- every answered reading of P1-P3 (and every refutation, which
  carries a script too) is run through its column-3 script in a fresh
  ``python3 -I`` interpreter, and again with its claim altered;
* **P9** -- Phase 118's report, with ``PHASE_118_NARROWED`` applied, still
  meets all its marks; and no outside question, Set B question or evaluation
  case reads differently with the Phase 119 readings on and off.

Nothing here makes a float (D7).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..evaluation import derivation_four_cases as C
from . import derivation_four_frames as D4
from . import derivation_four_marks as M
from . import derivation_two_frames as DF
from .question_frames import run_gate

__all__ = ["gate_mark", "refusal_mark", "phase_118_mark", "unmoved_mark",
           "derivation_four_report"]


def _gate(script: str) -> bool:
    return run_gate(script, seconds=180)[0]


def gate_mark() -> Dict[str, object]:
    """P5."""
    rows = []
    for group in (C.INEQUALITIES, C.RATE_DISTORTION, C.ROBIN,
                  C.ROBIN_SYMBOLIC, C.ROBIN_BOUNDS):
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
    """P4 through the frames."""
    rows = []
    for cid, text, code in C.REFUSALS:
        rd = DF.read_operation(text)
        rows.append({"id": cid, "code": rd.code, "want": code,
                     "as_declared": (not rd.answered) and rd.code == code})
    return {"rows": rows, "as_declared": sum(r["as_declared"] for r in rows),
            "of": len(rows), "met": all(r["as_declared"] for r in rows)}


def phase_118_mark(battery: Optional[int] = None) -> Dict[str, object]:
    """Phase 118's report with PHASE_118_NARROWED applied; its own N9
    (Phase 107's report and the outside texts) only on the full run."""
    from . import derivation_three_report as R3
    full = battery is None
    rep = R3.derivation_three_report(battery=battery, outside=full)
    want = rep["of"] if full else rep["of"] - 1
    return {"met_marks": rep["met"], "of": want,
            "missed": [k for k, v in rep["marks"].items()
                       if v.get("met") is False],
            "met": rep["met"] == want}


def unmoved_mark() -> Dict[str, object]:
    """P9, second half: frame and reading of every other text, with the
    Phase 119 readings on and off."""
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
    saved = D4.ENABLED[0]
    try:
        D4.ENABLED[0] = False
        before = {key: look(text) for key, text in texts}
        D4.ENABLED[0] = True
        for key, text in texts:
            after = look(text)
            if after is not None and len(after) > 1:
                read_both += 1
            if after != before[key]:
                moved.append(key)
    finally:
        D4.ENABLED[0] = saved
    return {"texts_checked": len(texts), "read_both_ways": read_both,
            "moved": moved, "met": not moved}


def derivation_four_report(battery: Optional[int] = None,
                           outside: bool = True) -> Dict[str, object]:
    p1 = M.inequality_marks()
    p2 = M.rd_marks()
    p3 = M.robin_marks()
    low = M.refusal_marks_low()
    high = refusal_mark()
    p4 = {"layer": low, "frames": high, "met": low["met"] and high["met"]}
    p5 = gate_mark()
    five = M.inequality_battery(battery)
    p118 = M.phase_118_battery()
    p6 = {"five": five, "phase_118": p118,
          "met": five["met"] and p118["met"]}
    p7 = M.rd_battery(battery)
    p8 = M.robin_battery(battery)
    if outside:
        ph = phase_118_mark(30 if battery else None)
        um = unmoved_mark()
        p9 = {"phase_118": ph, "unmoved": um, "met": ph["met"] and um["met"]}
    else:
        p9 = {"met": None}
    p10 = M.lean_mark()
    marks = {"P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6,
             "P7": p7, "P8": p8, "P9": p9, "P10": p10}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
