"""``glm_universal.runtime.composed_radical_report`` -- the marks of Phase 115.

The measurement of ``studies/COMPOSED_RADICAL_STUDY.md`` against the marks
C1-C8 of :mod:`glm_universal.evaluation.composed_radical_cases`.  It reads the
branch layer through the same frame the CLI uses
(:func:`glm_universal.runtime.symbolic_frames.read_system`), and Phase 114's
and Phase 112's reports for C8, so it lives in the runtime layer.  Nothing
here uses a float.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..evaluation import composed_radical_cases as C

__all__ = ["case_marks", "letter_marks", "soundness_battery",
           "reach_battery", "decomposition_mark", "lean_mark",
           "regression_mark", "composed_radical_report", "LEAN_FILE",
           "LEAN_THEOREMS", "COMPOSED_MARK", "ANY_MARK"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "glm_lean" /
             "RequestProject" / "GLM" / "ComposedRadicals.lean")

#: The theorems mark C7 names.
LEAN_THEOREMS = ("no_radical_root_of_comp", "no_radical_root_of_comp_X_pow",
                 "decic_no_radical_root")

#: The words of the composition statement (its Lean citation).
COMPOSED_MARK = "GLM.ComposedRadicals.no_radical_root_of_comp"
#: The words every radical-free statement carries, of any certificate.
ANY_MARK = "no root of it is expressible in radicals"
#: The words of a no-radical-formula reason in letters.
FORMULA_MARK = "no formula in radicals of"


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
    """C1 and C2."""
    return {
        "C1": _rows([q for q, _, _ in C.COMPOSED],
                    lambda rd: rd.answered and
                    COMPOSED_MARK in (rd.column2 or "")),
        "C2": _rows(C.SOLVABLE, lambda rd: ANY_MARK not in (rd.column2 or "")),
    }


def letter_marks() -> Dict[str, object]:
    """C3."""
    rows = []
    for cid, q, want in C.LETTERS:
        rd = _read(q)
        text = (rd.value or "") + " " + (rd.column2 or "")
        got = "composed" if COMPOSED_MARK in text else (
            "other" if FORMULA_MARK in text or ANY_MARK in text else None)
        if want is None:
            ok = got is None
        else:
            ok = (not rd.answered and rd.code == "NONLINEAR" and got == want)
        rows.append({"id": cid, "answered": rd.answered, "code": rd.code,
                     "reason": got, "declared": want, "ok": ok})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def _irreducible(ints: List[int]) -> bool:
    from ..reasoning import symbolic_algebraic as A
    from ..reasoning import symbolic_factor as Z
    fq = [Fraction(c) for c in ints]
    if len(A.pgcd(fq, A.pderiv(fq))) > 1:
        return False
    facs = Z.zassenhaus(ints)
    return facs is not None and len(facs) == 1


def _compose_ints(g, h) -> List[int]:
    from ..reasoning import symbolic_factor as Z
    return [int(c) for c in Z.compose([Fraction(c) for c in g],
                                      [Fraction(c) for c in h])]


def _random_monic(lcg, degree: int, bound: int) -> List[int]:
    return [int(lcg.next() % (2 * bound + 1)) - bound
            for _ in range(degree)] + [1]


def soundness_compositions() -> List[Tuple[List[int], int]]:
    """``(f, inner degree)`` for every composition of the soundness battery,
    before the irreducibility filter."""
    from ..reasoning import symbolic as S
    degrees, per, seed, bound = C.SOUNDNESS_INNER
    lcg = S.Lcg(seed)
    out = []
    for g in C.SOLVABLE_QUINTICS:
        for k in degrees:
            for _ in range(per):
                h = _random_monic(lcg, k, bound)
                out.append((_compose_ints(g, h), k))
    return out


def soundness_battery() -> Dict[str, object]:
    """C4: compositions with a solvable outer quintic, and Phase 114's own
    soundness battery; no certificate may be given."""
    from ..reasoning import symbolic_factor as Z
    from . import primitive_radical_report as pr
    counted = 0
    certified = []
    polys = [f for f, _ in soundness_compositions()] + pr.soundness_polys()
    for f in polys:
        if not _irreducible(f):
            continue
        counted += 1
        if Z.certify_numeric_any(f) is not None:
            certified.append(f)
    return {"of": counted, "certified": len(certified),
            "examples": certified[:5], "met": counted > 0 and not certified}


def reach_compositions() -> List[Tuple[List[int], int]]:
    """``(f, inner degree)`` for the reach battery, irreducible ones only."""
    from ..reasoning import symbolic as S
    count, seed, bound = C.REACH_BATTERY
    lcg = S.Lcg(seed)
    out: List[Tuple[List[int], int]] = []
    while len(out) < count:
        e, k = C.REACH_SHAPES[len(out) % len(C.REACH_SHAPES)]
        g = _random_monic(lcg, e, bound)
        h = _random_monic(lcg, k, bound)
        if g[0] == 0:
            continue
        f = _compose_ints(g, h)
        if not _irreducible(f):
            continue
        out.append((f, k))
    return out


def reach_battery() -> Dict[str, object]:
    """C5: random irreducible compositions with a random outer polynomial."""
    from ..reasoning import symbolic_factor as Z
    polys = reach_compositions()
    got = 0
    missed = []
    by_shape: Dict[str, List[int]] = {}
    for f, k in polys:
        r = Z.radical_free_galois([Fraction(c) for c in f]) is not None
        got += r
        key = f"{(len(f) - 1) // k}x{k}"
        row = by_shape.setdefault(key, [0, 0])
        row[0] += r
        row[1] += 1
        if not r:
            missed.append(f)
    num, den = C.REACH_SHARE
    return {"of": len(polys), "certified": got,
            "by_shape": {s: f"{a}/{b}" for s, (a, b) in
                         sorted(by_shape.items())},
            "missed": missed[:5], "met": got * den >= num * len(polys)}


def decomposition_mark() -> Dict[str, object]:
    """C6: on every built composition, a decomposition with the inner degree
    used is found and recomposes to the polynomial."""
    from ..reasoning import symbolic_factor as Z
    cases = soundness_compositions() + reach_compositions()
    ok = 0
    failed = []
    for f, k in cases:
        fq = [Fraction(c) for c in f]
        got = Z.decompose(fq, k)
        good = got is not None and Z.compose(*got) == fq
        ok += good
        if not good:
            failed.append(f)
    return {"of": len(cases), "exact": ok, "failed": failed[:5],
            "met": len(cases) > 0 and ok == len(cases)}


def lean_mark() -> Dict[str, object]:
    """C7 (the source half; the build is ``lake build``)."""
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
    """C8: Phase 114's report and Phase 112's, every mark."""
    from . import primitive_radical_report as pr
    from . import quintic_radical_report as qr
    prim = pr.primitive_radical_report(battery=True)
    quin = qr.quintic_radical_report()
    return {"phase_114": f"{prim['met']} of {prim['of']}",
            "phase_112": f"{quin['met']} of {quin['of']}",
            "met": prim["met"] == prim["of"] and quin["met"] == quin["of"]}


def composed_radical_report(battery: bool = True) -> Dict[str, object]:
    """Every mark, C1-C8 (``battery=False`` skips C4, C5, C6 and C8)."""
    cm = case_marks()
    skip: Dict[str, Optional[bool]] = {"skipped": True, "met": None}
    marks = {"C1": cm["C1"], "C2": cm["C2"],
             "C3": letter_marks(),
             "C4": soundness_battery() if battery else dict(skip),
             "C5": reach_battery() if battery else dict(skip),
             "C6": decomposition_mark() if battery else dict(skip),
             "C7": lean_mark(),
             "C8": regression_mark() if battery else dict(skip)}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
