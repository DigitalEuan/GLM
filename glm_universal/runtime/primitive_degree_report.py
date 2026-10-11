"""``glm_universal.runtime.primitive_degree_report`` -- the marks of Phase 116.

The measurement of ``studies/PRIMITIVE_DEGREE_STUDY.md`` against the marks
D1-D8 of :mod:`glm_universal.evaluation.primitive_degree_cases`.  It reads the
branch layer through the same frame the CLI uses
(:func:`glm_universal.runtime.symbolic_frames.read_system`), and Phase 115's
report for D8, so it lives in the runtime layer.  Nothing here uses a float.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..evaluation import primitive_degree_cases as C
from ..reasoning import primitive_degree_groups as G
from ..reasoning.primitive_degree_groups import projective_group, reach_polys

__all__ = ["case_marks", "group_mark", "projective_group", "soundness_battery",
           "reach_battery", "reach_polys", "degree_gate_mark", "lean_mark",
           "regression_mark", "primitive_degree_report", "LEAN_FILE",
           "LEAN_THEOREMS", "DEGREE_MARK", "ANY_MARK"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "glm_lean" /
             "RequestProject" / "GLM" / "PrimitiveDegree.lean")

#: The theorems mark D7 names.
LEAN_THEOREMS = ("exists_normal_comm_ne_bot", "exists_normal_pGroup_ne_bot",
                 "card_dvd_of_normal_ne_bot",
                 "isPrimePow_card_of_isPreprimitive_of_isSolvable",
                 "not_solvable_of_long_cycle_of_not_isPrimePow",
                 "no_radical_root_of_long_cycle_of_not_isPrimePow")

#: The words of the new statement (its Lean citation).
DEGREE_MARK = "GLM.PrimitiveDegree.no_radical_root_of_long_cycle_of_not_isPrimePow"
#: The words every radical-free statement carries, of any certificate.
ANY_MARK = "no root of it is expressible in radicals"


def _read(q: str):
    from .symbolic_frames import read_system
    return read_system(q)


def _rows(questions, ok) -> Dict[str, object]:
    rows = []
    for q in questions:
        rd = _read(q)
        rows.append({"question": q, "answered": rd.answered,
                     "ok": bool(ok(rd))})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def case_marks() -> Dict[str, object]:
    """D1 and D2."""
    return {
        "D1": _rows([q for q, _, _ in C.DEGREE],
                    lambda rd: rd.answered and
                    DEGREE_MARK in (rd.column2 or "")),
        "D2": _rows(C.SOLVABLE, lambda rd: ANY_MARK not in (rd.column2 or "")),
    }


# -- D3: the groups themselves -----------------------------------------------

def group_mark() -> Dict[str, object]:
    """D3: both groups have the declared order, are transitive, hold a
    ``(5, 1)`` element and no element Phase 114's Jordan reading accepts; and
    Phase 114's certificate is silent on the declared sextics."""
    from ..reasoning import symbolic_factor as Z
    rows = {}
    ok = True
    for name, special, order in (("PGL(2,5)", False, 120),
                                 ("PSL(2,5)", True, 60)):
        g = projective_group(special)
        types = sorted({tuple(G.cycle_degrees(s)) for s in g})
        transitive = {s[0] for s in g} == set(range(6))
        long_cycle = any(Z.is_long_cycle(list(t)) for t in types)
        jordan = [t for t in types if Z.jordan_power(list(t)) is not None]
        good = (len(g) == order and transitive and long_cycle and not jordan)
        ok = ok and good
        rows[name] = {"order": len(g), "transitive": transitive,
                      "cycle_types": [list(t) for t in types],
                      "long_cycle": long_cycle, "jordan": jordan, "ok": good}
    silent = []
    for q, (a, b), s in C.DEGREE:
        f = G.scaled_sextic(a, b, s)
        silent.append(Z.radical_free_primitive([Fraction(c) for c in f])
                      is None)
    ok = ok and all(silent)
    return {"groups": rows, "phase_114_silent": f"{sum(silent)} of "
            f"{len(silent)}", "met": ok}


# -- D4, D5: the batteries ---------------------------------------------------

def soundness_battery() -> Dict[str, object]:
    """D4: Phase 114's and Phase 115's soundness batteries, every polynomial
    with a solvable group; no certificate may be given."""
    from ..reasoning import symbolic_factor as Z
    from . import composed_radical_report as cr
    from . import primitive_radical_report as pr
    polys = pr.soundness_polys() + [f for f, _ in cr.soundness_compositions()]
    counted, certified = 0, []
    for f in polys:
        if not G.irreducible(f):
            continue
        counted += 1
        if Z.certify_numeric_any(f) is not None:
            certified.append(f)
    return {"of": counted, "certified": len(certified),
            "examples": certified[:5], "met": counted > 0 and not certified}


def reach_battery() -> Dict[str, object]:
    """D5: the Cayley sextics of random trinomial quintics with a
    non-solvable group: the new statement on at least 95 %, Phase 114's on
    none."""
    from ..reasoning import symbolic_factor as Z
    polys = reach_polys()
    got, by_114, missed = 0, 0, []
    for ab, f in polys:
        fq = [Fraction(c) for c in f]
        text = Z.radical_free_galois(fq) or ""
        hit = DEGREE_MARK in text
        got += hit
        by_114 += Z.PRIMITIVE_LEAN in text
        if not hit:
            missed.append(ab)
    num, den = C.REACH_SHARE
    return {"of": len(polys), "certified": got, "by_phase_114": by_114,
            "missed": missed[:5],
            "met": got * den >= num * len(polys) and by_114 == 0}


# -- D6: the degree gate -----------------------------------------------------

def degree_gate_mark() -> Dict[str, object]:
    """D6: the prime-power test against trial division, and silence on every
    degree-8 and degree-9 polynomial of Phase 114's reach battery."""
    from ..reasoning import symbolic_factor as Z
    from . import primitive_radical_report as pr
    wrong = [n for n in C.PRIME_POWER_RANGE
             if Z.is_prime_power(n) != G.prime_power_by_division(n)]
    counted, fired = 0, []
    for f in pr._reach_polys():
        if len(f) - 1 not in (8, 9):
            continue
        counted += 1
        if Z.radical_free_degree([Fraction(c) for c in f]) is not None:
            fired.append(f)
    return {"range": f"{len(C.PRIME_POWER_RANGE)} values, {len(wrong)} wrong",
            "prime_power_degree_polys": counted, "fired": len(fired),
            "met": not wrong and counted > 0 and not fired}


def lean_mark() -> Dict[str, object]:
    """D7 (the source half; the build is ``lake build``)."""
    if not LEAN_FILE.exists():
        return {"exists": False, "met": False}
    src = LEAN_FILE.read_text(encoding="utf-8")
    code = re.sub(r"/-.*?-/", "", src, flags=re.S)
    code = re.sub(r"--[^\n]*", "", code)
    missing = [t for t in LEAN_THEOREMS
               if not re.search(rf"theorem\s+{t}\b", code)]
    has_sorry = bool(re.search(r"\bsorry\b", code))
    return {"exists": True, "missing": missing, "sorry": has_sorry,
            "met": not missing and not has_sorry}


def regression_mark() -> Dict[str, object]:
    """D8: Phase 115's report, every mark."""
    from . import composed_radical_report as cr
    comp = cr.composed_radical_report(battery=True)
    return {"phase_115": f"{comp['met']} of {comp['of']}",
            "met": comp["met"] == comp["of"]}


def primitive_degree_report(battery: bool = True) -> Dict[str, object]:
    """Every mark, D1-D8 (``battery=False`` skips D4, D5, D6 and D8)."""
    cm = case_marks()
    skip: Dict[str, Optional[bool]] = {"skipped": True, "met": None}
    marks = {"D1": cm["D1"], "D2": cm["D2"],
             "D3": group_mark(),
             "D4": soundness_battery() if battery else dict(skip),
             "D5": reach_battery() if battery else dict(skip),
             "D6": degree_gate_mark() if battery else dict(skip),
             "D7": lean_mark(),
             "D8": regression_mark() if battery else dict(skip)}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
