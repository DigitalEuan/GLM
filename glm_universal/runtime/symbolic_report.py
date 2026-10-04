"""``glm_universal.runtime.symbolic_report`` -- the marks of Phase 98.

The measurement of ``studies/SYMBOLIC_PARAMETERS_STUDY.md`` against the marks
S1-S8 declared before any code in
:mod:`glm_universal.evaluation.symbolic_cases`.  Every answered reading's
column-3 script is run in a fresh ``python3 -I`` interpreter (the gate), and
again with the claimed value altered (the control), so the report lives in
the runtime layer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..evaluation import symbolic_cases as C

__all__ = ["outside_marks", "variant_marks", "system_marks", "refusal_marks",
           "regression_mark", "crossover_mark", "lean_mark", "new_frame_reads",
           "symbolic_report", "random_battery", "LEAN_FILE", "LEAN_THEOREMS"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "glm_lean" /
             "RequestProject" / "GLM" / "SymbolicParameters.lean")

#: The theorems mark S8 names.
LEAN_THEOREMS = ("rolling_acceleration", "rolling_friction_ratio",
                 "invariant_mass_sq", "disturbance_transfer",
                 "interface_tangent_ratio", "ar1_autocorrelation",
                 "poly_eq_of_agree", "cramer_solves")


def _outside_text(i: int) -> str:
    from ..evaluation import question_set_b_cases as qc
    return qc.outside()[i].text


def _mutant_rejected(frame_name: str, text: str) -> bool:
    """The reading of ``text`` with its claimed value altered fails its own
    column-3 script."""
    from . import question_frames as qf
    from .symbolic_frames import mutated
    from .symbolic_outside import mutated_reading
    if frame_name == "symbolic_system":
        m = mutated(text)
    else:
        got = qf.frame_of(text)
        if got is None:
            return False
        m = mutated_reading(*got)
    return not qf.run_gate(m.script)[0]


def outside_marks(run_scripts: bool = True) -> Dict[str, object]:
    """S1 (and the S1 half of S5): every class-S outside question through the
    router."""
    from . import router
    from .session import GeometricSession
    session = GeometricSession()
    rows = []
    for i, frag in sorted(C.OUTSIDE_S.items()):
        r = router.route(session, _outside_text(i))
        rd = r.payload if r.surface == "frames" else None
        answered = bool(rd and rd.answered)
        gate = bool(rd and rd.gate and rd.gate[0])
        hit = bool(rd and frag and frag in rd.value)
        row = {"index": i, "surface": r.surface,
               "frame": rd.frame if rd else None, "answered": answered,
               "gate": gate, "fragment": hit,
               "headline": (rd.value if rd else r.text or "")[:200]}
        if run_scripts and answered and gate:
            row["mutant_rejected"] = _mutant_rejected(rd.frame,
                                                      _outside_text(i))
        rows.append(row)
    correct = sum(1 for r in rows if r["answered"] and r["gate"]
                  and r["fragment"])
    wrong = sum(1 for r in rows if r["answered"] and not r["fragment"])
    return {"rows": rows, "correct": correct, "of": len(rows),
            "wrong": wrong, "met": correct >= 10 and wrong == 0}


def variant_marks(run_scripts: bool = True) -> Dict[str, object]:
    """S2: every declared variant answered with its own fragment."""
    from . import question_frames as qf
    rows = []
    for i, items in sorted(C.VARIANTS.items()):
        for text, frag in items:
            rd = qf.read(text)
            ok = bool(rd and rd.answered and rd.gate and rd.gate[0]
                      and frag in rd.value)
            row = {"index": i, "fragment": frag, "ok": ok,
                   "frame": rd.frame if rd else None,
                   "headline": rd.value[:160] if rd else None}
            if run_scripts and ok:
                row["mutant_rejected"] = _mutant_rejected(rd.frame, text)
            rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def system_marks(run_scripts: bool = True) -> Dict[str, object]:
    """S3: the declared systems, each target an identity with the declared
    expression (squares for roots)."""
    from ..reasoning import symbolic as S
    from . import question_frames as qf
    from .symbolic_frames import read_system, solve_text
    rows = []
    for squared, cases in ((False, C.SYSTEMS), (True, C.SYSTEMS_SQUARED)):
        for cid, q, expected in cases:
            row = {"id": cid, "squared": squared}
            try:
                sol, ctx, _, _ = solve_text(q)
            except S.SymbolicError as e:
                row.update(ok=False, refused=e.code)
                rows.append(row)
                continue
            same = True
            for t, exp in expected.items():
                k, v = sol.values[t]
                want = S.parse(exp, ctx)
                if squared:
                    got = v if k == 2 else v * v
                else:
                    got = v if k == 1 else None
                same = same and got is not None and got == want
            rd = read_system(q)
            gate = qf.run_gate(rd.script) if run_scripts else (True, "")
            row.update(ok=same and gate[0], identity=same, gate=gate[0],
                       answer=rd.value[:200])
            if run_scripts:
                row["mutant_rejected"] = _mutant_rejected("symbolic_system",
                                                          q)
            rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def refusal_marks() -> Dict[str, object]:
    """S4: every declared refusal by its code."""
    from .symbolic_frames import read_system
    rows = []
    for cid, q, code in C.REFUSALS:
        rd = read_system(q)
        rows.append({"id": cid, "expected": code, "got": rd.code,
                     "ok": (not rd.answered) and rd.code == code})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def mutation_mark(s1, s2, s3) -> Dict[str, object]:
    """S5: every answered reading's script rejects its altered copy."""
    rows = [r for part in (s1, s2, s3) for r in part["rows"]
            if "mutant_rejected" in r]
    rejected = sum(1 for r in rows if r["mutant_rejected"])
    verified = all(r.get("gate", r.get("ok")) for r in rows)
    return {"mutants": len(rows), "rejected": rejected,
            "met": bool(rows) and rejected == len(rows) and verified}


def new_frame_reads() -> Dict[str, object]:
    """Which earlier declared question the new frames read (should be
    none): the router's declared sets, Set B and every outside question
    outside classes S and T."""
    from ..evaluation import question_set_b_cases as qc
    from . import question_frames as qf
    from .router import _declared_sets
    from .symbolic_outside import OUTSIDE_S_FRAMES
    new = {f.name for f in OUTSIDE_S_FRAMES} | {"symbolic_system"}
    texts: List[Tuple[str, str]] = []
    for name, items in _declared_sets().items():
        texts += [(name, t) for t in items]
    texts += [("set_b", it.query) for it in qc.set_b()]
    texts += [("outside", it.text) for it in qc.outside()
              if it.index not in C.OUTSIDE_S and it.index not in C.OUTSIDE_T]
    hits = []
    for name, t in texts:
        got = qf.frame_of(t)
        if got is not None and got[0].name in new:
            hits.append((name, t[:80], got[0].name))
    return {"texts": len(texts), "read_by_new": hits}


def regression_mark() -> Dict[str, object]:
    """S6: the Phase 89 framed answers and Set B verdicts unchanged, and the
    new frames read no earlier declared question."""
    from ..evaluation import question_set_b as qb
    from ..evaluation import question_set_b_cases as qc
    o = qb.run_outside()
    framed = [r for r in o if r["index"] in qb.OUTSIDE_AUDITED]
    framed_ok = sum(1 for r in framed if r["class"] == "F")
    b = qb.run_set_b()
    audited = sum(r["audited_score"] for r in b)
    plus = sum(1 for r in b if r["audited_score"] == 1)
    reads = new_frame_reads()
    newly = sorted(r["index"] for r in o
                   if r["index"] not in qb.OUTSIDE_AUDITED
                   and r["frame"] is not None)
    return {"framed_ok": framed_ok, "framed_of": len(framed),
            "set_b_audited": audited, "set_b_audited_plus": plus,
            "set_b_of": len(b), "outside_newly_framed": newly,
            "new_frame_reads": reads,
            "met": (framed_ok == len(framed) == 27 and plus == len(b) == 14
                    and not reads["read_by_new"]),
            "outside_classes": {k: sum(1 for r in o if r["class"] == k)
                                for k in sorted(set(r["class"] for r in o))},
            "total_outside": len(qc.outside())}


def crossover_mark(run_scripts: bool = True) -> Dict[str, object]:
    """S7: the class-T question bracketed to 1/10000 by exact bounds."""
    from fractions import Fraction
    from . import router
    from .session import GeometricSession
    i = next(iter(C.OUTSIDE_T))
    r = router.route(GeometricSession(), _outside_text(i))
    rd = r.payload if r.surface == "frames" else None
    m = re.search(r"omega_co in \[(\d+\.\d+), (\d+\.\d+)\]",
                  rd.value if rd else "")
    width = (Fraction(m.group(2)) - Fraction(m.group(1))) if m else None
    ok = bool(rd and rd.answered and rd.gate and rd.gate[0] and width
              is not None and width <= Fraction(1, 10000))
    out = {"index": i, "answered": bool(rd and rd.answered),
           "gate": bool(rd and rd.gate and rd.gate[0]),
           "width": str(width), "headline": rd.value if rd else None,
           "met": ok}
    if run_scripts and ok:
        out["mutant_rejected"] = _mutant_rejected(rd.frame, _outside_text(i))
        out["met"] = ok and out["mutant_rejected"]
    return out


def lean_mark() -> Dict[str, object]:
    """S8 (the source half; the build is ``lake build``)."""
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


def _det(rows: List[List]) -> object:
    """Determinant by fraction-exact elimination."""
    from fractions import Fraction
    m = [[Fraction(x) for x in r] for r in rows]
    n = len(m)
    det = Fraction(1)
    for c in range(n):
        piv = next((r for r in range(c, n) if m[r][c] != 0), None)
        if piv is None:
            return Fraction(0)
        if piv != c:
            m[c], m[piv] = m[piv], m[c]
            det = -det
        det *= m[c][c]
        for r in range(c + 1, n):
            f = m[r][c] / m[c][c]
            for k in range(c, n):
                m[r][k] -= f * m[c][k]
    return det


def random_battery(count: int = 90, seed: int = 9803,
                   run_scripts: bool = True) -> Dict[str, object]:
    """A post-hoc battery (evidence, not a mark): random linear systems in
    2-4 unknowns whose coefficients are small integers times letters.  A
    system is singular exactly when its coefficient determinant vanishes as
    a polynomial; the check evaluates the determinant at three rational
    points.  Every answer must pass its gate; every refusal must be of a
    singular system."""
    from fractions import Fraction
    from ..reasoning import symbolic as S
    from . import question_frames as qf
    from .symbolic_frames import read_system
    lcg = S.Lcg(seed)
    letters = ["p", "q", "r", "s"]
    rows = []
    for i in range(count):
        n = 2 + i % 3
        coefs = []
        eqs = []
        for _ in range(n):
            row = []
            terms = []
            for j in range(n):
                c = int(lcg.next() % 5) - 2
                lt = letters[lcg.next() % 4] if lcg.next() % 3 == 0 else None
                row.append((c, lt))
                if c:
                    coef = f"{c}*{lt}" if lt else f"{c}"
                    terms.append(f"({coef})*x{j + 1}")
            rhs = letters[lcg.next() % 4]
            coefs.append(row)
            eqs.append((" + ".join(terms) or "0") + f" = {rhs}")
        xs = [f"x{j + 1}" for j in range(n)]
        q = f"solve symbolically for {', '.join(xs)}: " + "; ".join(eqs)
        singular = True
        for pt in ({"p": 2, "q": 3, "r": 5, "s": 7},
                   {"p": Fraction(1, 3), "q": 4, "r": Fraction(-2, 7),
                    "s": 11}, {"p": 13, "q": Fraction(5, 2), "r": 1,
                               "s": Fraction(-3, 4)}):
            m = [[c * (pt[lt] if lt else 1) for c, lt in row]
                 for row in coefs]
            if _det(m) != 0:
                singular = False
        rd = read_system(q)
        gate = qf.run_gate(rd.script)[0] if (run_scripts and
                                              rd.answered) else None
        rows.append({"n": n, "singular": singular, "answered": rd.answered,
                     "code": rd.code, "gate": gate})
    answered = [r for r in rows if r["answered"]]
    return {
        "systems": len(rows),
        "nonsingular": sum(1 for r in rows if not r["singular"]),
        "answered": len(answered),
        "answered_verified": sum(1 for r in answered if r["gate"]),
        "answered_singular": sum(1 for r in answered if r["singular"]),
        "refused_nonsingular": sum(1 for r in rows if not r["answered"]
                                   and not r["singular"]),
        "refusal_codes": {c: sum(1 for r in rows if r["code"] == c)
                          for c in sorted({r["code"] for r in rows
                                           if r["code"]})},
    }


def symbolic_report(run_scripts: bool = True,
                    regression: bool = True) -> Dict[str, object]:
    s1 = outside_marks(run_scripts)
    s2 = variant_marks(run_scripts)
    s3 = system_marks(run_scripts)
    out: Dict[str, object] = {
        "S1": s1, "S2": s2, "S3": s3, "S4": refusal_marks(),
        "S5": mutation_mark(s1, s2, s3) if run_scripts else
        {"met": None, "skipped": True},
        "S6": regression_mark() if regression else
        {"met": None, "skipped": True},
        "S7": crossover_mark(run_scripts), "S8": lean_mark(),
    }
    out["marks"] = {k: out[k]["met"] for k in
                    ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")}
    return out
