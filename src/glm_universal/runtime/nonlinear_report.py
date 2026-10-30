"""``glm_universal.runtime.nonlinear_report`` -- the marks of Phase 103.

It reads the operation as Phase 103 shipped it (``phase=103``), so its
figures stay the record; Phase 104's additions are scored by
:mod:`glm_universal.runtime.cubic_radical_report`.

The measurement of ``studies/NONLINEAR_ELIMINATION_STUDY.md`` against the
marks E1-E7 declared before any code in
:mod:`glm_universal.evaluation.nonlinear_cases`.  Every answered reading's
column-3 script (one per branch, run together) is run in a fresh
``python3 -I`` interpreter, and again with the first target of every branch
altered, so the report lives in the runtime layer.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional

from ..evaluation import nonlinear_cases as C

__all__ = ["system_marks", "refusal_marks", "regression_mark", "off_mark",
           "planted_battery", "lean_mark", "nonlinear_report", "LEAN_FILE",
           "LEAN_THEOREMS", "branch_matches"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "lean" /
             "RequestProject" / "GLM" / "NonlinearElimination.lean")

#: The theorems mark E7 names.
LEAN_THEOREMS = ("quadratic_branches", "conjugate_branch",
                 "resultant_eq_zero_of_common_root", "elastic_collision_iff",
                 "sum_product_iff")


def _same(a, b, rels: Dict[str, object]) -> bool:
    """``a == b`` as rational functions once every ``sqrt(R)`` is reduced by
    ``sqrt(R)^2 = R``."""
    from ..reasoning import symbolic as S
    d = a - b
    num = d.num
    for g, r in rels.items():
        if g in num.vars():
            num = num.reduce_power(g, 2, r).num
    return S.RF(num).is_zero()


def branch_matches(sols, declared: List[Dict[str, str]]) -> Dict[str, int]:
    """How many declared branches equal a machine branch (one to one)."""
    from ..reasoning import symbolic as S
    used = set()
    matched = 0
    for want in declared:
        ctx = S.Context()
        exp = {t: S.parse(e, ctx) for t, e in want.items()}
        rels = {a.name: a.arg for a in ctx.atoms.values() if a.kind == "sqrt"}
        for k, sol in enumerate(sols):
            if k in used:
                continue
            r2 = dict(rels)
            for g in sol.generators:
                r2[g] = sol.values[g][1]
            if all(t in sol.values and _same(sol.values[t][1], v, r2)
                   for t, v in exp.items()):
                used.add(k)
                matched += 1
                break
    return {"matched": matched, "declared": len(declared),
            "machine": len(sols)}


def system_marks(run_scripts: bool = True) -> Dict[str, object]:
    """E1 and E3: every declared system, its branches and its scripts."""
    from . import question_frames as qf
    from .symbolic_frames import (mutated, read_system, solve_branches,
                                  solve_text)
    rows = []
    for cid, q, declared in C.SYSTEMS:
        rd = read_system(q, phase=103)
        row = {"id": cid, "answered": rd.answered, "value": rd.value,
               "code": rd.code}
        row["layer"] = "nonlinear" if "symbolic_nonlinear" in rd.backing \
            else "substitution"
        if not rd.answered:
            m = {"matched": 0, "declared": len(declared), "machine": 0}
        elif row["layer"] == "nonlinear":
            m = branch_matches(solve_branches(q, phase=103)[0].solutions,
                              declared)
        else:
            # the substitution layer answered: its one solution is scored
            m = branch_matches([solve_text(q)[0]], declared)
        row.update(m)
        row["branches_ok"] = (rd.answered and m["matched"] == len(declared)
                              == m["machine"])
        if run_scripts and rd.answered:
            row["gate"] = qf.run_gate(rd.script)[0]
            row["mutant_rejected"] = not qf.run_gate(
                mutated(q, phase=103).script)[0]
        rows.append(row)
    e1 = sum(1 for r in rows if r["branches_ok"])
    out = {"rows": rows, "E1": {"passed": e1, "of": len(rows),
                                "met": e1 == len(rows)}}
    if run_scripts:
        g = sum(1 for r in rows if r.get("gate"))
        mr = sum(1 for r in rows if r.get("mutant_rejected"))
        ans = sum(1 for r in rows if r["answered"])
        out["E3"] = {"verified": g, "mutants_rejected": mr, "answered": ans,
                     "met": ans > 0 and g == ans and mr == ans}
    else:
        out["E3"] = {"met": None, "skipped": True}
    return out


def refusal_marks() -> Dict[str, object]:
    """E2: every declared refusal by its code, the layer on."""
    from .symbolic_frames import read_system
    rows = []
    for cid, q, code in C.REFUSALS:
        rd = read_system(q, phase=103)
        rows.append({"id": cid, "expected": code, "got": rd.code,
                     "ok": (not rd.answered) and rd.code == code})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def regression_mark() -> Dict[str, object]:
    """E4: every Phase 98 question reads as before unless Phase 98 refused it
    ``NONLINEAR``; and the Phase 98 refusal mark still holds with the layer
    off."""
    from ..evaluation import symbolic_cases as P
    from .symbolic_frames import read_system
    from .symbolic_report import refusal_marks as p98_refusals
    qs = [q for _, q, _ in P.SYSTEMS] + [q for _, q, _ in P.SYSTEMS_SQUARED] \
        + [q for _, q, _ in P.REFUSALS]
    same = changed = nonlinear = 0
    moved = []
    for q in qs:
        off, on = read_system(q, nonlinear=False), read_system(q, phase=103)
        if (off.answered, off.value, off.code) == (on.answered, on.value,
                                                   on.code):
            same += 1
        elif off.code == "NONLINEAR":
            nonlinear += 1
            moved.append(q)
        else:
            changed += 1
    p98 = p98_refusals()
    return {"questions": len(qs), "same": same, "nonlinear_now_read":
            nonlinear, "changed_otherwise": changed, "moved": moved,
            "phase98_refusals": f"{p98['passed']}/{p98['of']}",
            "met": changed == 0 and nonlinear == 2 and p98["met"]}


def off_mark() -> Dict[str, object]:
    """E6: with the layer off, every declared system is refused
    ``NONLINEAR`` (so the layer, and only it, answers them)."""
    from .symbolic_frames import read_system
    codes = {cid: read_system(q, nonlinear=False).code
             for cid, q, _ in C.SYSTEMS}
    ok = sum(1 for c in codes.values() if c == "NONLINEAR")
    return {"codes": codes, "refused_nonlinear": ok, "of": len(codes),
            "met": ok == len(codes)}


def _fr(q: Fraction) -> str:
    return str(q.numerator) if q.denominator == 1 else \
        f"({q.numerator}/{q.denominator})"


def planted_battery(count: int = 60, seed: int = 10301,
                    run_scripts: bool = True, phase: int = 103
                    ) -> Dict[str, object]:
    """E5: two random quadratic equations in ``x``, ``y`` through a chosen
    rational point.  An answer is wrong when its script fails or the planted
    point is not among its branches (a lost real solution)."""
    from ..reasoning import symbolic as S
    from . import question_frames as qf
    from .symbolic_frames import read_system, solve_branches
    lcg = S.Lcg(seed)
    monos = (("x^2", 2, 0), ("x*y", 1, 1), ("y^2", 0, 2), ("x", 1, 0),
             ("y", 0, 1))
    rows = []
    for n in range(count):
        x0 = Fraction(int(lcg.next() % 7) - 3, 1 + lcg.next() % 2)
        y0 = Fraction(int(lcg.next() % 7) - 3, 1 + lcg.next() % 2)
        eqs = []
        for _ in range(2):
            cs = [int(lcg.next() % 7) - 3 for _ in monos]
            if not any(cs[:3]):
                cs[0] = 1
            const = -sum(c * x0 ** a * y0 ** b
                         for c, (_, a, b) in zip(cs, monos))
            terms = " + ".join(f"{c}*{m}" for c, (m, _, _) in zip(cs, monos)
                               if c)
            eqs.append(f"{terms} + {_fr(const)} = 0")
        q = "solve symbolically for x, y: " + "; ".join(eqs)
        rd = read_system(q, phase=phase)
        row = {"n": n, "point": (str(x0), str(y0)), "answered": rd.answered,
               "code": rd.code, "question": q}
        if rd.answered:
            sols = solve_branches(q, phase)[0].solutions
            row["branches"] = len(sols)
            row["planted"] = any(
                s.values["x"][1].const_value() == x0 and
                s.values["y"][1].const_value() == y0 for s in sols)
            row["gate"] = qf.run_gate(rd.script)[0] if run_scripts else None
            row["wrong"] = (not row["planted"]) or row["gate"] is False
        rows.append(row)
    answered = [r for r in rows if r["answered"]]
    planted = sum(1 for r in answered if r["planted"])
    wrong = sum(1 for r in answered if r["wrong"])
    codes: Dict[str, int] = {}
    for r in rows:
        if not r["answered"]:
            codes[r["code"]] = codes.get(r["code"], 0) + 1
    return {"systems": count, "answered": len(answered), "planted": planted,
            "wrong": wrong, "refused": codes, "rows": rows,
            "met": wrong == 0 and planted >= 45}


def lean_mark() -> Dict[str, object]:
    """E7 (the source half; the build is ``lake build``)."""
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


def nonlinear_report(run_scripts: bool = True, battery: bool = True
                     ) -> Dict[str, object]:
    sm = system_marks(run_scripts)
    out: Dict[str, object] = {
        "systems": sm["rows"], "E1": sm["E1"], "E2": refusal_marks(),
        "E3": sm["E3"], "E4": regression_mark(),
        "E5": planted_battery(run_scripts=run_scripts) if battery else
        {"met": None, "skipped": True},
        "E6": off_mark(), "E7": lean_mark(),
    }
    out["marks"] = {k: out[k]["met"] for k in
                    ("E1", "E2", "E3", "E4", "E5", "E6", "E7")}
    return out


def _headline(report: Optional[Dict[str, object]] = None) -> str:
    r = report or nonlinear_report(run_scripts=False, battery=False)
    met = sum(1 for v in r["marks"].values() if v)
    return f"{met} of {len(r['marks'])} marks met"
