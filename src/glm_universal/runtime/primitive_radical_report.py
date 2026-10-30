"""``glm_universal.runtime.primitive_radical_report`` -- the marks of Phase 114.

The measurement of ``studies/PRIMITIVE_RADICAL_STUDY.md`` against the marks
P1-P10 of :mod:`glm_universal.evaluation.primitive_radical_cases`.  It reads
the branch layer through the same frame the CLI uses
(:func:`glm_universal.runtime.symbolic_frames.read_system`), the chain
pendulums through :func:`glm_universal.runtime.question_frames.read`, and
Phase 113's report for P10, so it lives in the runtime layer.  Nothing here
uses a float.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional

from ..evaluation import primitive_radical_cases as C

__all__ = ["case_marks", "letter_marks", "soundness_battery",
           "reach_battery", "shape_marks", "lean_mark", "modes_marks",
           "regression_mark", "primitive_radical_report", "LEAN_FILE",
           "LEAN_THEOREMS", "PRIMITIVE_MARK", "ANY_MARK"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "lean" /
             "RequestProject" / "GLM" / "PrimitiveRadicals.lean")

#: The theorems mark P8 names.
LEAN_THEOREMS = ("isPreprimitive_of_isCycle_fixing_one",
                 "not_solvable_of_long_cycle_of_swap_or_three_cycle",
                 "no_radical_root_of_primitive_pattern")

#: The words of the composite-degree statement (its Lean citation).
PRIMITIVE_MARK = "GLM.PrimitiveRadicals.no_radical_root_of_primitive_pattern"
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
    """P1, P2 and P3."""
    return {
        "P1": _rows(C.PRIMITIVE, lambda rd: rd.answered and
                    PRIMITIVE_MARK in (rd.column2 or "")),
        "P2": _rows(C.SOLVABLE, lambda rd: ANY_MARK not in (rd.column2 or "")),
        # Narrowed at Phase 115: the composition certificate
        # (studies/COMPOSED_RADICAL_STUDY.md) now reaches the declared limit
        # x^10 - x^2 - 1; what P3 declared is that this round's certificate
        # is silent on it, which still holds.
        "P3": _rows(C.LIMIT, lambda rd: rd.answered and
                    PRIMITIVE_MARK not in (rd.column2 or "")),
    }


def letter_marks() -> Dict[str, object]:
    """P4."""
    rows = []
    for cid, q, want in C.LETTERS:
        rd = _read(q)
        text = (rd.value or "") + " " + (rd.column2 or "")
        got = "primitive" if PRIMITIVE_MARK in text else (
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


def _cyclotomic(m: int) -> List[int]:
    """The ``m``-th cyclotomic polynomial, constant first, by exact division
    of ``x^m - 1`` by the cyclotomic polynomials of the proper divisors."""
    from ..reasoning.symbolic_factor import _int_divmod
    f = [-1] + [0] * (m - 1) + [1]
    for d in range(1, m):
        if m % d == 0:
            q = _int_divmod(f, _cyclotomic(d))
            assert q is not None
            f = q
    return f


def _compose(g: List[int], k: int) -> List[int]:
    """``g(x^k)``, constant first."""
    out = [0] * ((len(g) - 1) * k + 1)
    for i, c in enumerate(g):
        out[i * k] = c
    return out


def soundness_polys() -> List[List[int]]:
    """Every polynomial of the soundness battery, before the irreducibility
    filter: pure powers, cyclotomic polynomials, compositions."""
    from ..reasoning import symbolic as S
    polys: List[List[int]] = []
    degs, rc = C.SOUNDNESS_POWERS
    for n in degs:
        for c in rc:
            polys.append([-c] + [0] * (n - 1) + [1])
    for m in C.SOUNDNESS_CYCLOTOMIC:
        polys.append(_cyclotomic(m))
    shapes, count, seed, bound = C.SOUNDNESS_COMPOSITIONS
    lcg = S.Lcg(seed)
    for e, k in shapes:
        for _ in range(count):
            g = [int(lcg.next() % (2 * bound + 1)) - bound
                 for _ in range(e)] + [1]
            if g[0] == 0:
                g[0] = 1
            polys.append(_compose(g, k))
    return polys


def soundness_battery() -> Dict[str, object]:
    """P5: composite-degree polynomials whose Galois group is solvable by
    construction; no certificate may be given."""
    from ..reasoning import symbolic_factor as Z
    counted = 0
    certified = []
    for f in soundness_polys():
        if not _irreducible(f):
            continue
        counted += 1
        if Z.certify_numeric_any(f) is not None:
            certified.append(f)
    return {"of": counted, "certified": len(certified),
            "examples": certified[:5], "met": counted > 0 and not certified}


def _reach_polys() -> List[List[int]]:
    from ..reasoning import symbolic as S
    count, seed, bound = C.REACH_BATTERY
    lcg = S.Lcg(seed)
    out: List[List[int]] = []
    while len(out) < count:
        n = C.REACH_DEGREES[len(out) % len(C.REACH_DEGREES)]
        f = [int(lcg.next() % (2 * bound + 1)) - bound for _ in range(n)] + [1]
        if f[0] == 0 or not _irreducible(f):
            continue
        out.append(f)
    return out


def reach_battery() -> Dict[str, object]:
    """P6: random irreducible monic polynomials of composite degree."""
    from ..reasoning import symbolic_factor as Z
    polys = _reach_polys()
    got = 0
    missed = []
    by_degree: Dict[int, List[int]] = {}
    for f in polys:
        r = Z.radical_free_primitive([Fraction(c) for c in f]) is not None
        got += r
        row = by_degree.setdefault(len(f) - 1, [0, 0])
        row[0] += r
        row[1] += 1
        if not r:
            missed.append(f)
    num, den = C.REACH_SHARE
    return {"of": len(polys), "certified": got,
            "by_degree": {d: f"{a}/{b}" for d, (a, b) in
                          sorted(by_degree.items())},
            "missed": missed[:5], "met": got * den >= num * len(polys)}


def _partitions(n: int, top: Optional[int] = None):
    top = n if top is None else top
    if n == 0:
        yield []
        return
    for k in range(min(n, top), 0, -1):
        for rest in _partitions(n - k, k):
            yield [k] + rest


def _power_type(degs: List[int], m: int) -> List[int]:
    """The cycle type of the ``m``-th power of a permutation of cycle type
    ``degs``: a ``d``-cycle splits into ``gcd(d, m)`` cycles of length
    ``d / gcd(d, m)``."""
    def gcd(a: int, b: int) -> int:
        while b:
            a, b = b, a % b
        return a

    out: List[int] = []
    for d in degs:
        g = gcd(d, m)
        out.extend([d // g] * g)
    return sorted(out)


def shape_marks() -> Dict[str, object]:
    """P7: the Jordan test and the long-cycle test on every cycle type of
    the declared degrees, each checked against the cycle type itself."""
    from ..reasoning import symbolic_factor as Z
    shapes = ok = 0
    for n in C.SHAPE_DEGREES:
        for pa in _partitions(n):
            degs = sorted(pa)
            shapes += 1
            want = None
            for ell in (2, 3):
                if degs.count(ell) == 1 and all(d % ell for d in degs
                                                if d != ell):
                    want = ell
                    break
            got = Z.jordan_power(degs)
            good = (got is None) == (want is None)
            if got is not None:
                ell, m = got
                good = good and ell == want and \
                    _power_type(degs, m) == sorted([ell] + [1] * (n - ell))
            good = good and Z.is_long_cycle(degs) == (degs == [1, n - 1])
            ok += good
    return {"shapes": shapes, "ok": ok, "met": shapes > 0 and ok == shapes}


def lean_mark() -> Dict[str, object]:
    """P8 (the source half; the build is ``lake build``)."""
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


def modes_marks() -> Dict[str, object]:
    """P9: the chain pendulums on the ``modes.higher`` route."""
    from . import question_frames as qf
    rows = []
    for n, q in C.MODES:
        rd = qf.read(q)
        text = (rd.column2 or "") + " " + (rd.value or "")
        rows.append({"question": q, "links": n, "answered": rd.answered,
                     "ok": bool(rd.answered and FORMULA_MARK in text and
                                ANY_MARK in text)})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def regression_mark() -> Dict[str, object]:
    """P10: Phase 113's report, every mark."""
    from . import frobenius_radical_report as fr
    rep = fr.frobenius_radical_report(battery=True)
    return {"met_of": f"{rep['met']} of {rep['of']}",
            "met": rep["met"] == rep["of"]}


def primitive_radical_report(battery: bool = True) -> Dict[str, object]:
    """Every mark, P1-P10 (``battery=False`` skips P5, P6 and P10)."""
    cm = case_marks()
    skip: Dict[str, Optional[bool]] = {"skipped": True, "met": None}
    marks = {"P1": cm["P1"], "P2": cm["P2"], "P3": cm["P3"],
             "P4": letter_marks(),
             "P5": soundness_battery() if battery else dict(skip),
             "P6": reach_battery() if battery else dict(skip),
             "P7": shape_marks(),
             "P8": lean_mark(),
             "P9": modes_marks(),
             "P10": regression_mark() if battery else dict(skip)}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
