"""``glm_universal.runtime.frobenius_radical_report`` -- the marks of Phase 113.

The measurement of ``studies/FROBENIUS_RADICAL_STUDY.md`` against the marks
F1-F9 of :mod:`glm_universal.evaluation.frobenius_radical_cases`.  It reads
the branch layer through the same frame the CLI uses
(:func:`glm_universal.runtime.symbolic_frames.read_system`), and Phase 112's
report for F9, so it lives in the runtime layer.  Nothing here uses a float.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional

from ..evaluation import frobenius_radical_cases as C

__all__ = ["case_marks", "letter_marks", "soundness_battery",
           "reach_battery", "ddf_agreement", "lean_mark",
           "frobenius_radical_report", "LEAN_FILE", "LEAN_THEOREMS",
           "FROBENIUS_MARK", "ANY_MARK"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "glm_lean" /
             "RequestProject" / "GLM" / "FrobeniusRadicals.lean")

#: The theorems mark F8 names.
LEAN_THEOREMS = ("not_solvable_of_alternating_le",
                 "exists_pow_cycleType_singleton",
                 "card_complex_roots",
                 "not_solvable_of_swap_or_three_cycle",
                 "no_radical_root_of_swap_or_three_cycle",
                 "no_radical_root_of_cycle_pattern",
                 "eq_one_of_two_fixed_of_solvable",
                 "exists_pow_two_fixed",
                 "no_radical_root_of_frobenius_shape")

#: The words of the Frobenius statement (its Lean citation).
FROBENIUS_MARK = "GLM.FrobeniusRadicals.no_radical_root_of_frobenius_shape"
#: The words every radical-free statement carries, of either certificate.
ANY_MARK = "no root of it is expressible in radicals"
#: The words of Phase 112's no-radical-formula reason.
CONJUGATION_LETTER_MARK = "quintic_in_letters_no_radical_formula"


def _read(q: str):
    from .symbolic_frames import read_system
    return read_system(q)


def case_marks() -> Dict[str, object]:
    """F1, F2 and F3."""
    f1 = []
    for q in C.FROBENIUS:
        rd = _read(q)
        c2 = rd.column2 or ""
        f1.append({"question": q, "answered": rd.answered,
                   "ok": bool(rd.answered and FROBENIUS_MARK in c2)})
    f2 = []
    for q in C.SOLVABLE:
        rd = _read(q)
        f2.append({"question": q, "answered": rd.answered,
                   "ok": ANY_MARK not in (rd.column2 or "")})
    f3 = []
    for q in C.LIMIT:
        rd = _read(q)
        # Phase 114 narrowed F3 to this certificate's own wording: the
        # composite-degree certificate (studies/PRIMITIVE_RADICAL_STUDY.md)
        # now reaches the declared sextic, as it should.
        f3.append({"question": q, "answered": rd.answered,
                   "ok": bool(rd.answered and
                              FROBENIUS_MARK not in (rd.column2 or ""))})
    out = {}
    for key, rows in (("F1", f1), ("F2", f2), ("F3", f3)):
        passed = sum(1 for r in rows if r["ok"])
        out[key] = {"rows": rows, "passed": passed, "of": len(rows),
                    "met": passed == len(rows)}
    return out


def letter_marks() -> Dict[str, object]:
    """F4."""
    rows = []
    for cid, q, want in C.LETTERS:
        rd = _read(q)
        v = rd.value or ""
        got = ("frobenius" if FROBENIUS_MARK in v else
               "conjugation" if CONJUGATION_LETTER_MARK in v else None)
        rows.append({"id": cid, "code": rd.code, "reason": got,
                     "declared": want,
                     "ok": (not rd.answered and rd.code == "NONLINEAR" and
                            got == want)})
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


def soundness_battery() -> Dict[str, object]:
    """F5: polynomials whose Galois group is solvable by construction (De
    Moivre's quintic at integer points, pure powers ``x^n - c``); the
    certificate must never be given."""
    from ..reasoning import symbolic_factor as Z
    polys = []
    ra, rb = C.SOUNDNESS_DE_MOIVRE
    for a in ra:
        for b in rb:
            if a and b:
                polys.append([-b, 5 * a * a, 0, -5 * a, 0, 1])
    degs, rc = C.SOUNDNESS_POWERS
    for n in degs:
        for c in rc:
            polys.append([-c] + [0] * (n - 1) + [1])
    counted = 0
    certified = []
    for f in polys:
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
        n = 5 if len(out) % 2 == 0 else 7
        f = [int(lcg.next() % (2 * bound + 1)) - bound for _ in range(n)] + [1]
        if f[0] == 0 or not _irreducible(f):
            continue
        out.append(f)
    return out


def reach_battery() -> Dict[str, object]:
    """F6: random irreducible quintics and septics (whose group is the full
    symmetric group in all but a vanishing share of cases)."""
    from ..reasoning import symbolic_algebraic as A
    from ..reasoning import symbolic_factor as Z
    polys = _reach_polys()
    frob = conj = both = 0
    missed = []
    for f in polys:
        fq = [Fraction(c) for c in f]
        c = Z.radical_free(fq, len(A.isolate_real_roots(fq))) is not None
        r = Z.radical_free_frobenius(fq) is not None
        frob += r
        conj += c
        both += c and r
        if not r:
            missed.append(f)
    num, den = C.REACH_SHARE
    return {"of": len(polys), "frobenius": frob, "conjugation": conj,
            "conjugation_also_frobenius": both, "missed": missed[:5],
            "met": frob * den >= num * len(polys) and both == conj}


def _partitions(n: int, top: Optional[int] = None):
    top = n if top is None else top
    if n == 0:
        yield []
        return
    for k in range(min(n, top), 0, -1):
        for rest in _partitions(n - k, k):
            yield [k] + rest


def _affine(degs: List[int]) -> bool:
    moved = [d for d in degs if d > 1]
    return (not moved or len(degs) == 1 or
            (degs.count(1) == 1 and len(set(moved)) == 1))


def ddf_agreement() -> Dict[str, object]:
    """F7: the distinct-degree reading of the factor degrees against the
    complete factorisation modulo each prime of the declared list; and the
    shape test on every cycle type of the declared degrees: it fires exactly
    off the affine shapes, with a power that fixes at least two points and
    moves at least one (counted from the cycle type, not from the test)."""
    from ..reasoning import symbolic_factor as Z
    rows = agree = 0
    for f in _reach_polys():
        for q in C.DDF_PRIMES:
            degs = Z.frobenius_degrees(f, q)
            if degs is None:
                continue
            full = sorted(len(g) - 1 for g in Z.factor_mod_p(f, q))
            rows += 1
            agree += degs == full
    shapes = shapes_ok = 0
    for n in C.SHAPE_DEGREES:
        for pa in _partitions(n):
            degs = sorted(pa)
            got = Z.non_affine_power(degs)
            shapes += 1
            if got is None:
                shapes_ok += _affine(degs)
                continue
            m, s = got
            fixed = sum(d for d in degs if m % d == 0)
            shapes_ok += (not _affine(degs) and fixed == s and 2 <= s < n)
    return {"of": rows, "agree": agree, "shapes": shapes,
            "shapes_ok": shapes_ok,
            "met": rows > 0 and agree == rows and shapes_ok == shapes}


def lean_mark() -> Dict[str, object]:
    """F8 (the source half; the build is ``lake build``)."""
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
    """F9: Phase 112's report, every mark."""
    from . import quintic_radical_report as qr
    rep = qr.quintic_radical_report(run_scripts=False, battery=True)
    return {"met_of": f"{rep['met']} of {rep['of']}",
            "met": rep["met"] == rep["of"]}


def frobenius_radical_report(battery: bool = True) -> Dict[str, object]:
    """Every mark, F1-F9 (``battery=False`` skips F5-F7 and F9)."""
    cm = case_marks()
    skip: Dict[str, Optional[bool]] = {"skipped": True, "met": None}
    marks = {"F1": cm["F1"], "F2": cm["F2"], "F3": cm["F3"],
             "F4": letter_marks(),
             "F5": soundness_battery() if battery else dict(skip),
             "F6": reach_battery() if battery else dict(skip),
             "F7": ddf_agreement() if battery else dict(skip),
             "F8": lean_mark(),
             "F9": regression_mark() if battery else dict(skip)}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
