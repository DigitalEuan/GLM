"""``glm_universal.runtime.quintic_radical_report`` -- the marks of Phase 112.

The measurement of ``studies/QUINTIC_RADICAL_STUDY.md`` against the marks
R1-R7 of :mod:`glm_universal.evaluation.quintic_radical_cases`.  Every
answered reading's column-3 script is run in a fresh ``python3 -I``
interpreter, so the report lives in the runtime layer.  Nothing here uses a
float: a root's bracket is checked by evaluating the question's own
polynomial exactly at the bracket's rational ends.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..evaluation import quintic_radical_cases as C

__all__ = ["high_marks", "certificate_marks", "letter_marks",
           "planted_battery", "agreement_battery", "lean_mark",
           "quintic_radical_report", "LEAN_FILE", "LEAN_THEOREMS",
           "CERT_MARK", "LETTER_MARK"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "lean" /
             "RequestProject" / "GLM" / "QuinticRadicals.lean")

#: The theorems mark R7 names.
LEAN_THEOREMS = ("no_radical_root_of_prime_degree",
                 "card_complex_roots_of_irreducible",
                 "irreducible_trinomial", "gal_trinomial",
                 "trinomial_family_no_radical_root",
                 "trinomial_no_radical_root",
                 "quintic_in_letters_no_radical_formula")

#: The words that mark a reading as carrying the radical-free statement of
#: this round (complex conjugation).  Phase 113 added a second certificate
#: (one Frobenius element, ``studies/FROBENIUS_RADICAL_STUDY.md``) that now
#: reaches two of the controls of R3 and the septic letter case of R4, so
#: these marks read the conjugation certificate by its own words: "exactly
#: two non-real roots" here, and its Lean citation in R4.
CERT_MARK = "with exactly two non-real roots"
#: The words of this round's no-radical-formula reason (R4).
LETTER_MARK = "quintic_in_letters_no_radical_formula"

_ROOT = re.compile(r"root\(([^,]+), (-?\d+(?:/\d+)?), (-?\d+(?:/\d+)?)\)")


def _poly_of(question: str) -> List[Fraction]:
    """The question's own polynomial ``lhs - rhs`` in ``x``, coefficients
    from the constant up, read by the package's polynomial parser."""
    from ..reasoning import symbolic as S
    body = question.split(":", 1)[1]
    lhs, rhs = body.split("=")
    e = S.parse(lhs.strip()) - S.parse(rhs.strip())
    p = e.num.scale(1 / e.den.const_value())
    cs = p.coeffs("x")
    return [Fraction(cs[i].const_value()) if i in cs else Fraction(0)
            for i in range(p.deg("x") + 1)]


def _peval(p: List[Fraction], x: Fraction) -> Fraction:
    v = Fraction(0)
    for c in reversed(p):
        v = v * x + c
    return v


def _upoly(text: str, var: str) -> List[Fraction]:
    from ..reasoning import symbolic as S
    e = S.parse(text.strip())
    p = e.num.scale(1 / e.den.const_value())
    cs = p.coeffs(var)
    return [Fraction(cs[i].const_value()) if i in cs else Fraction(0)
            for i in range(p.deg(var) + 1)]


def _brackets_hold(question: str, value: str) -> Tuple[int, bool]:
    """``(roots read, every root is sound)`` for each ``root(f, lo, hi)`` of
    the answer: ``f`` divides the question's own polynomial exactly and
    changes sign on ``[lo, hi]``."""
    from ..reasoning import symbolic_algebraic as A
    p = _poly_of(question)
    got = _ROOT.findall(value)
    ok = True
    for ftext, lo, hi in got:
        f = _upoly(ftext, "t")
        divides = not A.pdivmod(p, f)[1]
        a, b = _peval(f, Fraction(lo)), _peval(f, Fraction(hi))
        ok = ok and divides and a * b < 0
    return len(got), ok


def high_marks(run_scripts: bool = True) -> Dict[str, object]:
    """R1."""
    from . import question_frames as qf
    from .symbolic_frames import read_system, solve_branches
    rows = []
    for cid, q, want in C.HIGH:
        rd = read_system(q)
        row = {"id": cid, "answered": rd.answered, "code": rd.code,
               "declared": want}
        if rd.answered:
            row["branches"] = len(solve_branches(q)[0].solutions)
            row["roots_read"], row["brackets"] = _brackets_hold(q, rd.value)
            if run_scripts:
                row["gate"] = qf.run_gate(rd.script)[0]
        row["ok"] = bool(rd.answered and row.get("branches") == want and
                         row.get("brackets") and row.get("gate", True))
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def _carries(q: str) -> bool:
    from .symbolic_frames import read_system
    rd = read_system(q)
    return rd.answered and CERT_MARK in rd.column2


def certificate_marks() -> Dict[str, object]:
    """R2 and R3."""
    cert = [{"question": q, "carries": _carries(q)} for q in C.CERTIFIED]
    ctrl = [{"question": q, "carries": _carries(q)} for q in C.UNCERTIFIED]
    r2 = sum(1 for r in cert if r["carries"])
    r3 = sum(1 for r in ctrl if not r["carries"])
    return {"R2": {"rows": cert, "passed": r2, "of": len(cert),
                   "met": r2 == len(cert)},
            "R3": {"rows": ctrl, "passed": r3, "of": len(ctrl),
                   "met": r3 == len(ctrl)}}


def letter_marks() -> Dict[str, object]:
    """R4."""
    from .symbolic_frames import read_system
    rows = []
    for cid, q, reason in C.LETTERS:
        rd = read_system(q)
        has = LETTER_MARK in (rd.value or "")
        rows.append({"id": cid, "code": rd.code, "reason": has,
                     "declared": reason,
                     "ok": (not rd.answered and rd.code == "NONLINEAR" and
                            has == reason)})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def _mul(a: List[int], b: List[int]) -> List[int]:
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


def _text(c: List[int]) -> str:
    out = ""
    for i in range(len(c) - 1, -1, -1):
        if not c[i]:
            continue
        mono = "" if i == 0 else ("x" if i == 1 else f"x^{i}")
        a = abs(c[i])
        body = (mono if a == 1 and mono else
                (f"{a}*{mono}" if mono else str(a)))
        out += (("-" if c[i] < 0 else "") + body if not out else
                (" - " if c[i] < 0 else " + ") + body)
    return out


def _planted(lcg, lo: int, hi: int) -> Optional[Tuple[List[List[int]], int]]:
    """Two to four random integer factors whose degrees sum to between
    ``lo`` and ``hi``, each of degree 2 or more (no linear factor, so no
    rational root to split off first)."""
    k = 2 + lcg.next() % 3
    facs = []
    for _ in range(k):
        d = 2 + lcg.next() % 5
        f = [int(lcg.next() % 15) - 7 for _ in range(d)] + [1]
        if f[0] == 0:
            f[0] = 1
        facs.append(f)
    total = sum(len(f) - 1 for f in facs)
    if not lo <= total <= hi:
        return None
    return facs, total


def planted_battery(run_scripts: bool = True) -> Dict[str, object]:
    """R5: products of planted factors.  The expected branch count is the
    number of distinct real roots of the product, counted by a Sturm chain
    on the product itself (not by the layer's factoring); a product that is
    not squarefree or has a rational root is skipped, since the layer splits
    those off by other means."""
    from ..reasoning import symbolic as S
    from ..reasoning import symbolic_algebraic as A
    from . import question_frames as qf
    from .symbolic_frames import read_system, solve_branches
    count, seed, lo, hi = C.PLANTED_BATTERY
    lcg = S.Lcg(seed)
    rows = []
    while len(rows) < count:
        got = _planted(lcg, lo, hi)
        if got is None:
            continue
        facs, deg = got
        prod = [1]
        for f in facs:
            prod = _mul(prod, f)
        pq = [Fraction(c) for c in prod]
        if len(A.pgcd(pq, A.pderiv(pq))) > 1:
            continue
        lead, const = prod[-1], prod[0]
        if const == 0 or any(_peval(pq, Fraction(s * r, t)) == 0
                             for r in range(1, abs(const) + 1)
                             if const % r == 0
                             for t in range(1, abs(lead) + 1)
                             if lead % t == 0 for s in (1, -1)):
            continue
        want = len(A.isolate_real_roots(pq))
        if want == 0:
            continue
        q = f"solve symbolically for x: {_text(prod)} = 0"
        rd = read_system(q)
        row = {"question": q, "degree": deg, "expected": want,
               "answered": rd.answered, "code": rd.code}
        if rd.answered:
            row["branches"] = len(solve_branches(q)[0].solutions)
            if run_scripts:
                row["gate"] = qf.run_gate(rd.script)[0]
        row["wrong"] = rd.answered and (row.get("branches") != want or
                                        not row.get("gate", True))
        rows.append(row)
    answered = sum(1 for r in rows if r["answered"])
    wrong = sum(1 for r in rows if r["wrong"])
    num, den = C.ANSWERED_SHARE
    return {"rows": rows, "of": len(rows), "answered": answered,
            "wrong": wrong,
            "met": wrong == 0 and answered * den >= num * len(rows)}


def agreement_battery() -> Dict[str, object]:
    """R6: Zassenhaus against Kronecker on random polynomials of degree 4
    to 6 with no rational root (Kronecker's precondition)."""
    from ..reasoning import symbolic as S
    from ..reasoning import symbolic_algebraic as A
    from ..reasoning import symbolic_factor as Z
    count, seed = C.AGREEMENT_BATTERY
    lcg = S.Lcg(seed)
    rows = 0
    agree = 0
    split = 0
    while rows < count:
        k = 1 + lcg.next() % 2
        f = [1]
        for _ in range(k):
            d = 2 + lcg.next() % 3
            f = _mul(f, [int(lcg.next() % 11) - 5 for _ in range(d)] + [1])
        if not 4 <= len(f) - 1 <= 6 or f[0] == 0:
            continue
        fq = [Fraction(c) for c in f]
        if len(A.pgcd(fq, A.pderiv(fq))) > 1:
            continue
        zs = Z.zassenhaus(f)
        if zs is None or any(len(g) == 2 for g in zs):
            continue
        ref = A.factor_rational(fq)
        if ref is None:
            continue
        rows += 1
        mine = sorted(tuple(A.monic([Fraction(c) for c in g])) for g in zs)
        theirs = sorted(tuple(g) for g in ref)
        agree += mine == theirs
        split += len(zs) > 1
    return {"of": rows, "agree": agree, "split": split,
            "met": agree == rows}


def lean_mark() -> Dict[str, object]:
    """R7 (the source half; the build is ``lake build``)."""
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


def quintic_radical_report(run_scripts: bool = True, battery: bool = True
                           ) -> Dict[str, object]:
    """Every mark, R1-R7."""
    cm = certificate_marks()
    marks = {"R1": high_marks(run_scripts), "R2": cm["R2"], "R3": cm["R3"],
             "R4": letter_marks(),
             "R5": planted_battery(run_scripts) if battery else
             {"skipped": True, "met": None},
             "R6": agreement_battery() if battery else
             {"skipped": True, "met": None},
             "R7": lean_mark()}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
