"""``glm_universal.runtime.cubic_trig_report`` -- the marks of Phase 108.

The measurement of ``studies/CUBIC_TRIG_STUDY.md`` against the marks T1-T9
declared before any code in :mod:`glm_universal.evaluation.cubic_trig_cases`:
a cubic in letters with three real roots, answered by the homogeneous route
(``s`` times an algebraic number) or by Viete's trigonometric form.

The instrument evaluates an exact branch in fixed point (the package is
float-free, directive D7).  A Viete root ``M t_k`` is evaluated as the
``k``-th largest real root of its cubic at the point (Sturm isolation, then
bisection); the declared value ``shift + 2 r c_k`` is evaluated separately,
``c_k`` the ``k``-th largest root of ``4c^3 - 3c = K`` found by bisection on
``[1/2, 1]``, ``[-1/2, 1/2]`` and ``[-1, -1/2]`` -- the intervals the Lean
theorem ``vieta_cos_strictly_ordered`` puts them in.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..evaluation import cubic_trig_cases as C
from ..reasoning import symbolic as S
from ..reasoning import symbolic_algebraic as A
from ..reasoning import symbolic_nonlinear as N
from .cubic_radical_report import _root, _rnd, _run_scripts, _sqrt

__all__ = ["approx", "homogeneous_marks", "viete_marks", "script_mark",
           "motion_marks", "regression_mark", "viete_battery",
           "homogeneous_battery", "lean_mark", "outside_mark",
           "outside_readings",
           "cubic_trig_report", "LEAN_FILE", "LEAN_THEOREMS"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "glm_lean" /
             "RequestProject" / "GLM" / "CubicTrig.lean")

LEAN_THEOREMS: Tuple[str, ...] = (
    "vieta_root", "vieta_arg_le_one", "vieta_arg_lt_one",
    "vieta_cos_strictly_ordered", "cubic_three_roots_complete",
    "vieta_roots_iff", "scaled_root", "scaled_root_iff")

TOL = Fraction(1, 10 ** 9)
WIDTH = Fraction(1, 1 << 80)


def _close(a: Fraction, b: Fraction) -> bool:
    return abs(a - b) < TOL * max(Fraction(1), abs(b))


def _kth_largest(m: List[Fraction], k: int) -> Fraction:
    """The ``k``-th largest real root of the squarefree ``m`` (constant
    term first), by Sturm isolation and bisection."""
    ivs = sorted(A.isolate_real_roots(m), key=lambda iv: iv[0], reverse=True)
    lo, hi = A.refine(m, ivs[k][0], ivs[k][1], WIDTH)
    return (lo + hi) / 2


def approx(sol, t: str, point: Dict[str, Fraction]) -> Fraction:
    """The value of target ``t`` of a branch at ``point`` in fixed point:
    a letter by its value, an algebraic number by its narrowed interval, a
    radical atom or root generator by the real root of its radicand, a
    Viete root by the ``k``-th largest real root of its cubic."""
    ext = getattr(sol, "ext", None)
    cache: Dict[str, Fraction] = {}

    def gen(g: str) -> Fraction:
        if g in cache:
            return cache[g]
        if g in point:
            return Fraction(point[g])
        if ext is not None and g in ext.trig:
            k, _M = ext.trig[g]
            cs = ext.rels[g][1].coeffs(g)
            c1 = -poly(cs.get(1, S.Poly()))
            c0 = -poly(cs.get(0, S.Poly()))
            cache[g] = _kth_largest([c0, c1, Fraction(0), Fraction(1)], k)
            return cache[g]
        if ext is not None and g in ext.algs:
            a = ext.algs[g]
            lo, hi = A.refine(a.m, a.lo, a.hi, Fraction(1, 10 ** 24))
            cache[g] = _rnd((lo + hi) / 2)
            return cache[g]
        if g in S.RADICALS:
            q, b = S.RADICALS[g]
            cache[g] = _root(b, q)
            return cache[g]
        if ext is not None and g in ext.rels:
            k, R = ext.rels[g]
            r = poly(R)
        else:
            k, v = sol.values[g]
            r = rf(v)
        cache[g] = _root(r, k)
        return cache[g]

    def poly(p) -> Fraction:
        total = Fraction(0)
        for m, c in p.t.items():
            term = Fraction(c)
            for v, e in m:
                term *= gen(v) ** e
            total += term
        return total

    def rf(v) -> Fraction:
        d = poly(v.den)
        if d == 0:
            raise ZeroDivisionError
        return poly(v.num) / d

    k, v = sol.values[t]
    x = rf(v)
    return x if k == 1 else _root(x, k)


def _expr(text: str, point: Dict[str, Fraction]) -> Fraction:
    """A declared expression (decimals read exactly, ``sqrt`` real)."""
    py = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)",
                lambda m: f"F('{m.group(1)}')", text.replace("^", "**"))
    env = {"sqrt": _sqrt, "F": Fraction, "__builtins__": {}}
    env.update(point)
    return Fraction(eval(py, env))


def _viete_declared(shift: str, r2: str, K: str, k: int,
                    point: Dict[str, Fraction]) -> Fraction:
    Kv = _expr(K, point)
    lo, hi = ((Fraction(1, 2), Fraction(1)), (Fraction(-1, 2), Fraction(1, 2)),
              (Fraction(-1), Fraction(-1, 2)))[k]
    f = lambda c: 4 * c ** 3 - 3 * c - Kv
    # f(lo) and f(hi) differ in sign on each interval when |K| < 1
    flo = f(lo)
    while hi - lo > WIDTH:
        mid = (lo + hi) / 2
        if (f(mid) > 0) == (flo > 0):
            lo, flo = mid, f(mid)
        else:
            hi = mid
    c = (lo + hi) / 2
    return _expr(shift, point) + 2 * _sqrt(_expr(r2, point)) * c


def _points(letters: Sequence[str], seed: int, want: int = 3
            ) -> List[Dict[str, Fraction]]:
    lcg = S.Lcg(seed)
    return [{x: lcg.rational(1, 9) * (1 if lcg.next() % 3 else -1)
             for x in letters} for _ in range(want)]


def _branches(q: str):
    from .symbolic_frames import _setup, solve_branches
    return solve_branches(q)[0].solutions, _setup(q)[5]


def _match(sols, declared: List[Dict[str, object]], pts) -> int:
    """Declared branches matched one-to-one by machine branches; a declared
    value is a callable of the point."""
    used, matched = set(), 0
    for want in declared:
        for k, sol in enumerate(sols):
            if k in used:
                continue
            try:
                ok = all(_close(approx(sol, t, P), f(P))
                         for P in pts for t, f in want.items())
            except (ValueError, ZeroDivisionError, KeyError, IndexError):
                ok = False
            if ok:
                used.add(k)
                matched += 1
                break
    return matched


# ---------------------------------------------------------------------------
# T1, T2, T3
# ---------------------------------------------------------------------------

def homogeneous_marks(run_scripts: bool = True) -> Dict[str, object]:
    from .symbolic_frames import read_system
    rows = []
    for n, (cid, q, declared) in enumerate(C.HOMOGENEOUS):
        rd = read_system(q)
        row = {"id": cid, "answered": rd.answered, "code": rd.code,
               "value": rd.value}
        if rd.answered:
            sols, pars = _branches(q)
            pts = _points(pars, 10810 + n)
            want = [{t: (lambda P, e=e: _expr(e, P)) for t, e in d.items()}
                    for d in declared]
            row.update(matched=_match(sols, want, pts), machine=len(sols))
            if run_scripts:
                row["gate"], row["mutant_rejected"] = _run_scripts(q)
        else:
            row.update(matched=0, machine=0)
        row["declared"] = len(declared)
        row["ok"] = rd.answered and row["matched"] == len(declared) == \
            row["machine"]
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def viete_marks(run_scripts: bool = True) -> Dict[str, object]:
    from .symbolic_frames import read_system
    rows = []
    for n, (cid, q, u, shift, r2, K) in enumerate(C.VIETE):
        rd = read_system(q)
        row = {"id": cid, "answered": rd.answered, "code": rd.code,
               "value": rd.value}
        if rd.answered:
            sols, pars = _branches(q)
            pts = [P for P in _points(pars, 10820 + n, 12)
                   if abs(_expr(K, P)) < 1][:3]
            want = [{u: (lambda P, k=k: _viete_declared(shift, r2, K, k, P))}
                    for k in range(3)]
            row.update(matched=_match(sols, want, pts) if len(pts) == 3
                       else 0, machine=len(sols), points=len(pts))
            row["states"] = ("4*P^3 + 27*Q^2" in rd.value and
                             "cos(acos(" in rd.value)
            if run_scripts:
                row["gate"], row["mutant_rejected"] = _run_scripts(q)
        else:
            row.update(matched=0, machine=0, states=False)
        row["ok"] = rd.answered and row["matched"] == 3 == row["machine"] \
            and row["states"]
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def script_mark(*parts) -> Dict[str, object]:
    rows = [r for p in parts for r in p["rows"] if "gate" in r]
    ok = sum(1 for r in rows if r["gate"])
    mr = sum(1 for r in rows if r.get("mutant_rejected"))
    return {"answered": len(rows), "verified": ok, "mutants_rejected": mr,
            "met": bool(rows) and ok == len(rows) == mr}


# ---------------------------------------------------------------------------
# T4
# ---------------------------------------------------------------------------

def _motion_of(text: str):
    """``(lagrangian, coords)`` of a MOTION case."""
    from . import derivation_frames as DF
    t = text.strip()
    if t.lower().startswith(DF.MOTION):
        head, body = t.split(":", 1)
        spec = re.sub(r",\s*small oscillations\s*$", "",
                      head[len(DF.MOTION):], flags=re.I)
        return body.split("=", 1)[1].strip(), \
            [c.strip() for c in spec.split(",") if c.strip()]
    g = DF._m_chain_pendulum(t.lower())
    return DF.chain_lagrangian(g["n"], g["masses"], g["lengths"]), \
        [f"th{i + 1}" for i in range(g["n"])]


def _read_motion(text: str, mutate: bool = False):
    from . import derivation_frames as DF
    from . import question_frames as qf
    DF.MUTATE[0] = mutate
    try:
        if text.strip().lower().startswith(DF.MOTION):
            return DF.read_operation(text)
        return qf.read(text)
    finally:
        DF.MUTATE[0] = False


def motion_marks() -> Dict[str, object]:
    from ..reasoning import derivation as D
    from . import question_frames as qf
    rows = []
    for n, (cid, text, declared) in enumerate(C.MOTION):
        rd = _read_motion(text)
        lag, coords = _motion_of(text)
        mo = D.equations_of_motion(lag, coords, True)
        freqs = mo.frequencies or []
        letters = sorted(set().union(*(f.vars() for f in freqs)) -
                         set(mo.frequency_algs) - set(S.RADICALS)) \
            if freqs else []
        pts = _points(letters, 10840 + n)

        def fval(f, P):
            env = dict(P)
            for g, (m, lo, hi) in mo.frequency_algs.items():
                a, b = A.refine(m, lo, hi, WIDTH)
                env[g] = (a + b) / 2
            for g in f.vars() & set(S.RADICALS):
                q, c = S.RADICALS[g]
                env[g] = _root(c, q)
            return Fraction(f.num.evaluate(env)) / Fraction(f.den.evaluate(env))
        used, matched = set(), 0
        for e in declared:
            for k, f in enumerate(freqs):
                if k not in used and all(_close(fval(f, P), _expr(e, P))
                                         for P in pts):
                    used.add(k)
                    matched += 1
                    break
        mut = _read_motion(text, mutate=True)
        rows.append({"id": cid, "answered": bool(rd.answered),
                     "frequencies": [S.to_text(f) for f in freqs],
                     "matched": matched, "declared": len(declared),
                     "gate": bool(rd.answered and
                                  qf.run_gate(rd.script)[0]),
                     "mutant_rejected": not (mut.answered and
                                             qf.run_gate(mut.script)[0])})
    ok = all(r["answered"] and r["gate"] and r["mutant_rejected"] and
             r["matched"] == r["declared"] == len(r["frequencies"])
             for r in rows)
    return {"rows": rows, "met": ok}


# ---------------------------------------------------------------------------
# T5, T9: the switch off is Phase 104 exactly
# ---------------------------------------------------------------------------

def _with_trig(on: bool, fn):
    """``fn()`` with the switch as given and the layer as Phase 108 shipped
    it: the later case split (sharpening pass, ``reasoning/routes.py``,
    route ``cubic.letters:cases``) is disabled for the measurement, so the
    round's marks are read on the round's own code."""
    from ..reasoning import routes as RT
    saved = N.TRIG
    N.TRIG = on
    # Phase 109's factorisation of the discriminant is later than the round
    # too, so it is off for the measurement as well
    try:
        with RT.disabled("cubic.letters:cases", "cubic.letters:factor"):
            return fn()
    finally:
        N.TRIG = saved


def regression_mark(phase104: bool = True) -> Dict[str, object]:
    from ..evaluation import derivation_cases as DC
    from . import derivation_frames as DF
    from .symbolic_frames import read_system
    moved = []
    for q in C.UNCHANGED:
        a = _with_trig(False, lambda: read_system(q).value)
        b = _with_trig(True, lambda: read_system(q).value)
        if a != b:
            moved.append(q)
    motion_moved = []
    for row in DC.MOTION:
        q = row[1]
        a = _with_trig(False, lambda: DF.read_operation(q).value)
        b = _with_trig(True, lambda: DF.read_operation(q).value)
        if a != b:
            motion_moved.append(row[0])
    out: Dict[str, object] = {"unchanged_moved": moved,
                              "motion_moved": motion_moved,
                              "motion_checked": len(DC.MOTION)}
    if phase104:
        from .cubic_radical_report import cubic_radical_report
        rep = cubic_radical_report(run_scripts=True, battery=True)
        keep = ("K1", "K2", "K3", "K4", "K5", "K8")
        out["phase104"] = {k: rep["marks"][k] for k in keep}
        out["met"] = not moved and not motion_moved and \
            all(out["phase104"].values())
    else:
        out["met"] = not moved and not motion_moved
    return out


def _outside_texts() -> List[Tuple[str, str]]:
    from ..evaluation import question_set_b_cases as qc
    from ..evaluation.cases import CASES
    return [(f"O{it.index:03d}", it.text) for it in qc.outside()] + \
        [(it.id, it.query) for it in qc.set_b()] + \
        [(c.id, c.question) for c in CASES]


def outside_readings(on: bool) -> Dict[str, Optional[str]]:
    """Every outside text, Set B question and evaluation case read in
    order with the switch ``on`` or off: ``frame|answered|value``."""
    from . import question_frames as qf

    def reading(text: str) -> Optional[str]:
        if qf.frame_of(text) is None:
            return None
        rd = qf.read(text)
        return f"{rd.frame}|{rd.answered}|{rd.value}" if rd else None
    return _with_trig(on, lambda: {k: reading(t)
                                   for k, t in _outside_texts()})


def _fresh_readings(on: bool) -> Dict[str, Optional[str]]:
    """:func:`outside_readings` in a fresh interpreter: some frames carry
    state from one reading to the next (the rate grid's observation
    stream), so the two passes must each start from nothing."""
    import json
    import subprocess
    import sys
    root = Path(__file__).resolve().parent.parent.parent
    code = ("import json; from glm_universal.runtime.cubic_trig_report "
            f"import outside_readings; print(json.dumps(outside_readings({on})))")
    out = subprocess.run([sys.executable, "-c", code], cwd=str(root),
                         capture_output=True, text=True, check=True,
                         env={"PYTHONPATH": str(root), "PATH": ""})
    return json.loads(out.stdout.strip().splitlines()[-1])


def outside_mark() -> Dict[str, object]:
    """T9: the outside texts, Set B and the evaluation cases read with the
    switch off and on, each pass in a fresh interpreter; only the texts
    naming OUTSIDE_MOVED may change."""
    from ..evaluation.cases import CASES
    texts = _outside_texts()
    before, after = _fresh_readings(False), _fresh_readings(True)
    moved = [k for k, _ in texts if before.get(k) != after.get(k)]
    allowed = [k for k, t in texts if k in moved and
               any(m in t.lower() for m in C.OUTSIDE_MOVED)]
    return {"texts_checked": len(texts), "moved": moved,
            "moved_allowed": allowed, "evaluation_cases": len(CASES),
            "met": set(moved) == set(allowed)}


# ---------------------------------------------------------------------------
# T6, T7: batteries
# ---------------------------------------------------------------------------

def _monomial(lcg: S.Lcg) -> str:
    return ("a", "b", "a*b", "a^2", "b^2", "a^2*b")[lcg.next() % 6]


def viete_cubic(lcg: S.Lcg) -> Tuple[str, str, str]:
    """``(question, A, B)`` for one cubic of the Viete battery: ``y^3 - 3 A
    y + 2 B A`` with ``x = y + h``."""
    c = int(lcg.next() % 4) + 1
    B = f"{c if lcg.next() % 2 else -c}*{_monomial(lcg)}"
    d1, d0 = int(lcg.next() % 3) + 1, int(lcg.next() % 4) + 1
    m2 = _monomial(lcg)
    Cs = f"{d1}*({m2})^2 + {d0}"
    Ap = f"(({B})^2 + {Cs})"
    h = int(lcg.next() % 7) - 3
    y = f"(x - ({h}))"
    q = (f"solve symbolically for x in terms of a, b: "
         f"{y}^3 - 3*{Ap}*{y} + 2*({B})*{Ap} = 0")
    return q, Ap, B


def viete_battery(count: Optional[int] = None,
                  run_scripts: bool = True) -> Dict[str, object]:
    from .symbolic_frames import read_system, _setup
    n, seed = C.VIETE_BATTERY
    n = count or n
    lcg = S.Lcg(seed)
    rows = []
    for i in range(n):
        q, _A, _B = viete_cubic(lcg)
        rd = read_system(q)
        row = {"question": q, "answered": rd.answered, "code": rd.code}
        if rd.answered:
            sols, pars = _branches(q)
            P = _points(["a", "b"], 10860 + i, 1)[0]
            eqs = _setup(q)[0]
            lhs = eqs[0][0] - eqs[0][1]
            vals = []
            for sol in sols:
                x = approx(sol, "x", P)
                vals.append(x)
            res_ok = True
            for x in vals:
                env = dict(P)
                env["x"] = x
                num = Fraction(lhs.num.evaluate(env))
                scale = 1 + sum(abs(Fraction(c)) * max(Fraction(1), abs(x)) ** 3
                                for c in lhs.num.t.values())
                res_ok = res_ok and abs(num) < TOL * scale
            distinct = len(vals) == 3 and len({_rnd(v) for v in vals}) == 3 \
                and min(abs(a - b) for a in vals for b in vals if a != b) > \
                Fraction(1, 10 ** 6)
            row.update(branches=len(sols), residual_ok=res_ok,
                       distinct=distinct)
            if run_scripts:
                row["gate"], row["mutant_rejected"] = _run_scripts(q)
        rows.append(row)
    ok = [r for r in rows if r["answered"] and r.get("branches") == 3 and
          r.get("residual_ok") and r.get("distinct") and
          (not run_scripts or r.get("gate"))]
    return {"count": n, "seed": seed, "passed": len(ok),
            "failed": [r for r in rows if r not in ok][:5],
            "met": len(ok) == n}


def _rational_root_free(cs: List[int]) -> bool:
    """The monic integer cubic ``cs`` (constant first) has no rational
    root (so no integer root, it being monic)."""
    c0 = cs[0]
    if c0 == 0:
        return False
    for d in range(1, abs(c0) + 1):
        if c0 % d == 0:
            for r in (d, -d):
                if r ** 3 + cs[2] * r ** 2 + cs[1] * r + c0 == 0:
                    return False
    return True


def homogeneous_battery(count: Optional[int] = None,
                        run_scripts: bool = True) -> Dict[str, object]:
    from .symbolic_frames import read_system
    n, seed = C.HOMOGENEOUS_BATTERY
    n = count or n
    lcg = S.Lcg(seed)
    rows = []
    made = 0
    while made < n:
        c2, c1, c0 = (int(lcg.next() % 19) - 9 for _ in range(3))
        disc = (18 * c2 * c1 * c0 - 4 * c2 ** 3 * c0 + c2 ** 2 * c1 ** 2 -
                4 * c1 ** 3 - 27 * c0 ** 2)
        if disc <= 0 or not _rational_root_free([c0, c1, c2]):
            continue
        made += 1
        q = (f"solve symbolically for u in terms of a, b: "
             f"b^3*u^3 + ({c2})*a*b^2*u^2 + ({c1})*a^2*b*u + ({c0})*a^3 = 0")
        rd = read_system(q)
        row = {"question": q, "answered": rd.answered, "code": rd.code}
        if rd.answered:
            sols, _ = _branches(q)
            P = _points(["a", "b"], 10880 + made, 1)[0]
            m = [Fraction(c0), Fraction(c1), Fraction(c2), Fraction(1)]
            want = [{"u": (lambda P, k=k: P["a"] / P["b"] *
                           _kth_largest(m, k))} for k in range(3)]
            row.update(branches=len(sols), matched=_match(sols, want, [P]))
            if run_scripts:
                row["gate"], row["mutant_rejected"] = _run_scripts(q)
        rows.append(row)
    ok = [r for r in rows if r["answered"] and r.get("branches") == 3 and
          r.get("matched") == 3 and (not run_scripts or r.get("gate"))]
    return {"count": n, "seed": seed, "passed": len(ok),
            "failed": [r for r in rows if r not in ok][:5],
            "met": len(ok) == n}


# ---------------------------------------------------------------------------
# T8
# ---------------------------------------------------------------------------

def lean_mark() -> Dict[str, object]:
    """T8 (the source half; the build is ``lake build``)."""
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


def cubic_trig_report(run_scripts: bool = True, battery: bool = True,
                      outside: bool = True) -> Dict[str, object]:
    t1 = homogeneous_marks(run_scripts)
    t2 = viete_marks(run_scripts)
    marks: Dict[str, Dict[str, object]] = {
        "T1": t1, "T2": t2,
        "T3": script_mark(t1, t2) if run_scripts else {"met": None},
        "T4": motion_marks(),
        "T5": regression_mark(phase104=battery),
        "T6": viete_battery(run_scripts=run_scripts) if battery else
        {"met": None, "skipped": True},
        "T7": homogeneous_battery(run_scripts=run_scripts) if battery else
        {"met": None, "skipped": True},
        "T8": lean_mark(),
        "T9": outside_mark() if outside else {"met": None, "skipped": True},
    }
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"marks": marks, "met": met, "of": len(marks)}
