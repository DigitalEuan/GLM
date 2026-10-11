"""``glm_universal.runtime.cubic_radical_report`` -- the marks of Phase 104.

The measurement of ``studies/CUBIC_RADICAL_STUDY.md`` against the marks
K1-K9 declared before any code in
:mod:`glm_universal.evaluation.cubic_radical_cases`.  Every answered
reading's column-3 script is run in a fresh ``python3 -I`` interpreter, and
again with the first target of every branch doubled, so the report lives in
the runtime layer.

The matchers compare **numbers**: a branch's exact value (an algebraic
number, a square root, a tower, a cube root) is evaluated in fixed point
(rationals rounded to 2^-96) at sample points and compared with the declared
value.  That is an instrument of the report, never of the answer.  Nothing
here, in the answer or in its script uses a float (directive D7).
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..evaluation import cubic_radical_cases as C
from ..reasoning.routes import as_shipped

__all__ = ["approx_value", "algebraic_marks", "radical_marks",
           "refusal_marks", "dual_marks", "regression_mark",
           "planted_marks", "cubic_battery", "lean_mark",
           "cubic_radical_report", "LEAN_FILE", "LEAN_THEOREMS",
           "independent_count", "HARD_SYSTEMS", "exploration"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "glm_lean" /
             "RequestProject" / "GLM" / "CubicRadicals.lean")

#: The theorems mark K9 names.
LEAN_THEOREMS = ("cardano_root", "depressed_cubic_unique_real_root",
                 "biquadratic_iff", "even_quartic_factor",
                 "cubic_irreducible_of_no_rational_root",
                 "root_of_sign_change")


# ---------------------------------------------------------------------------
# approximate evaluation of an exact branch (the report's instrument)
# ---------------------------------------------------------------------------
#
# The package is float-free (directive D7), so the instrument works in fixed
# point: rationals rounded to a multiple of 2^-BITS after every root and
# division.  Its tolerances are far coarser than its rounding.

BITS = 96
SCALE = 1 << BITS
TOL = Fraction(1, 10 ** 9)


#: The Phase 104 marks are read on the layer as Phase 104 shipped it: the
#: later case split for a cubic whose discriminant's sign is not decided
#: (sharpening pass, ``reasoning/routes.py``) is disabled while they run,
#: and so is Phase 109's factorisation of the discriminant.
_AS_SHIPPED = as_shipped("cubic.letters:cases", "cubic.letters:factor")


def _rnd(x) -> Fraction:
    x = Fraction(x)
    return Fraction(round(x * SCALE), SCALE)


def _iroot(n: int, k: int) -> int:
    """The integer ``k``-th root of ``n >= 0`` (floor)."""
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + k - 1) // k)
    while True:
        y = ((k - 1) * x + n // x ** (k - 1)) // k
        if y >= x:
            break
        x = y
    while x ** k > n:
        x -= 1
    while (x + 1) ** k <= n:
        x += 1
    return x


def _root(x, k: int) -> Fraction:
    """The real ``k``-th root in fixed point; an even root of a negative
    number raises ``ValueError``."""
    x = Fraction(x)
    if x < 0:
        if k % 2 == 0:
            raise ValueError("a negative radicand")
        return -_root(-x, k)
    n = (x.numerator * SCALE ** k) // x.denominator
    return Fraction(_iroot(n, k), SCALE)


def _sqrt(x) -> Fraction:
    return _root(x, 2)


def _cbrt(x) -> Fraction:
    return _root(x, 3)


def approx_value(sol, t: str, point: Dict[str, Fraction]) -> Fraction:
    """The value of target ``t`` of a branch at ``point`` (letters to
    rationals), in fixed point: every generator replaced by its real value
    (an algebraic number by its narrowed interval, a square root or cube
    root by the real root of its radicand, a positive root by the
    convention it was given under)."""
    from ..reasoning import symbolic as S
    from ..reasoning import symbolic_algebraic as A
    ext = getattr(sol, "ext", None)
    cache: Dict[str, Fraction] = {}

    def gen(g: str) -> Fraction:
        if g in cache:
            return cache[g]
        if g in point:
            return Fraction(point[g])
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
        return _rnd(total)

    def rf(v) -> Fraction:
        d = poly(v.den)
        if d == 0:
            raise ZeroDivisionError
        return _rnd(poly(v.num) / d)

    k, v = sol.values[t]
    x = rf(v)
    return x if k == 1 else _root(x, k)


def _close(a: Fraction, b: Fraction, tol: Fraction = TOL) -> bool:
    return abs(a - b) < tol * max(Fraction(1), abs(b))


def _expr_value(text: str, point: Dict[str, Fraction]) -> Fraction:
    """A declared expression in fixed point (``sqrt`` and ``cbrt`` real);
    every integer literal is read as a ``Fraction``."""
    py = re.sub(r"\b(\d+)\b", r"F(\1)", text.replace("^", "**"))
    env = {"sqrt": _sqrt, "cbrt": _cbrt, "F": Fraction,
           "__builtins__": {}}
    env.update(point)
    return Fraction(eval(py, env))


def _points(letters: Sequence[str], seed: int, want: int = 3
            ) -> List[Dict[str, Fraction]]:
    from ..reasoning import symbolic as S
    lcg = S.Lcg(seed)
    return [{x: lcg.rational(1, 9) * (1 if lcg.next() % 3 else -1)
             for x in letters} for _ in range(want * 40)]


# ---------------------------------------------------------------------------
# K1 -- ALGEBRAIC
# ---------------------------------------------------------------------------

@_AS_SHIPPED
def _run_scripts(q: str) -> Tuple[bool, bool]:
    from . import question_frames as qf
    from .symbolic_frames import mutated, read_system
    rd = read_system(q)
    return qf.run_gate(rd.script)[0], not qf.run_gate(mutated(q).script)[0]


@_AS_SHIPPED
def algebraic_marks(run_scripts: bool = True) -> Dict[str, object]:
    from .symbolic_frames import read_system, solve_branches
    rows = []
    for cid, q, declared in C.ALGEBRAIC:
        rd = read_system(q)
        row = {"id": cid, "answered": rd.answered, "code": rd.code,
               "value": rd.value}
        if rd.answered:
            sols = solve_branches(q)[0].solutions
            used, matched = set(), 0
            for want in declared:
                for k, sol in enumerate(sols):
                    if k in used:
                        continue
                    try:
                        ok = all(abs(approx_value(sol, t, {}) -
                                     Fraction(x)) < Fraction(1, 10 ** 4)
                                 for t, x in want.items())
                    except (ValueError, ZeroDivisionError, KeyError):
                        ok = False
                    if ok:
                        used.add(k)
                        matched += 1
                        break
            row.update(matched=matched, declared=len(declared),
                       machine=len(sols))
            if run_scripts:
                row["gate"], row["mutant_rejected"] = _run_scripts(q)
        else:
            row.update(matched=0, declared=len(declared), machine=0)
        row["ok"] = rd.answered and row["matched"] == row["declared"] == \
            row["machine"]
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


# ---------------------------------------------------------------------------
# K2 -- RADICAL
# ---------------------------------------------------------------------------

@_AS_SHIPPED
def radical_marks(run_scripts: bool = True) -> Dict[str, object]:
    from .symbolic_frames import _setup, read_system, solve_branches
    rows = []
    for n, (cid, q, declared) in enumerate(C.RADICAL):
        rd = read_system(q)
        row = {"id": cid, "answered": rd.answered, "code": rd.code,
               "value": rd.value}
        if not rd.answered:
            row.update(matched=0, declared=len(declared), machine=0,
                       ok=False)
            rows.append(row)
            continue
        sols = solve_branches(q)[0].solutions
        pars = _setup(q)[5]
        # sample points at which every declared and machine value is real
        pts = []
        for P in _points(pars, 1040 + n):
            try:
                for want in declared:
                    for t, e in want.items():
                        _expr_value(e, P)
                for sol in sols:
                    for t in sol.targets:
                        approx_value(sol, t, P)
            except (ValueError, ZeroDivisionError):
                continue
            pts.append(P)
            if len(pts) == 3:
                break
        used, matched = set(), 0
        for want in declared:
            for k, sol in enumerate(sols):
                if k in used:
                    continue
                ok = len(pts) == 3 and all(
                    _close(approx_value(sol, t, P), _expr_value(e, P))
                    for P in pts for t, e in want.items())
                if ok:
                    used.add(k)
                    matched += 1
                    break
        row.update(matched=matched, declared=len(declared),
                   machine=len(sols), points=len(pts))
        if run_scripts:
            row["gate"], row["mutant_rejected"] = _run_scripts(q)
        row["ok"] = matched == len(declared) == len(sols)
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


# ---------------------------------------------------------------------------
# K3 -- REFUSALS
# ---------------------------------------------------------------------------

@_AS_SHIPPED
def refusal_marks() -> Dict[str, object]:
    from .symbolic_frames import read_system
    rows = []
    for cid, q, code in C.REFUSALS:
        rd = read_system(q)
        rows.append({"id": cid, "expected": code, "got": rd.code,
                     "why": rd.value,
                     "ok": (not rd.answered) and rd.code == code})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


# ---------------------------------------------------------------------------
# K5 -- DUAL
# ---------------------------------------------------------------------------

@_AS_SHIPPED
def dual_marks(run_scripts: bool = True) -> Dict[str, object]:
    from .symbolic_frames import (_setup, convention, read_system,
                                  solve_branches, solve_text)
    rows = []
    for n, (cid, q, want) in enumerate(C.DUAL):
        rd = read_system(q)
        sol98 = solve_text(q)[0]
        row = {"id": cid, "answered": rd.answered, "value": rd.value,
               "convention": convention(sol98)}
        sols = solve_branches(q)[0].solutions if rd.answered else []
        row["branches"] = len(sols)
        row["kept"] = "by substitution alone" in rd.value
        pars = _setup(q)[5]
        contained = False
        for P in _points(pars, 2040 + n):
            try:
                v98 = {t: approx_value(sol98, t, P) for t in sol98.targets}
                vb = [{t: approx_value(s, t, P) for t in s.targets}
                      for s in sols]
            except (ValueError, ZeroDivisionError, KeyError):
                continue
            contained = any(all(_close(b[t], v98[t]) for t in v98)
                            for b in vb)
            break
        row["contains_substitution_answer"] = contained
        if run_scripts and rd.answered:
            row["gate"], row["mutant_rejected"] = _run_scripts(q)
        row["ok"] = (rd.answered and len(sols) == want and row["kept"] and
                     contained and bool(row["convention"]))
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


# ---------------------------------------------------------------------------
# K6 -- REGRESSION
# ---------------------------------------------------------------------------

@_AS_SHIPPED
def regression_mark() -> Dict[str, object]:
    """With Phase 104's additions off, every Phase 103 declared case reads
    as Phase 103 recorded it; with them on, every Phase 98 reading without
    a convention is unchanged and every Phase 103 answered system keeps its
    declared branch set."""
    from ..evaluation import nonlinear_cases as N
    from ..evaluation import symbolic_cases as P
    from .nonlinear_report import branch_matches
    from .symbolic_frames import convention, read_system, solve_branches, \
        solve_text
    from ..reasoning import symbolic as S
    # (a) Phase 103 as shipped: 9 of 10 declared branch sets (circle and
    # line is read by substitution) and 5 of 5 refusals
    rec_sys = 0
    for cid, q, declared in N.SYSTEMS:
        rd = read_system(q, phase=103)
        if "symbolic_nonlinear" in rd.backing:
            m = branch_matches(solve_branches(q, phase=103)[0].solutions,
                               declared)
            rec_sys += m["matched"] == len(declared) == m["machine"]
    rec_ref = sum(1 for _, q, code in N.REFUSALS
                  if read_system(q, phase=103).code == code)
    # (b) Phase 98 questions without a convention, unchanged by 104
    qs = [q for _, q, _ in P.SYSTEMS] + [q for _, q, _ in P.SYSTEMS_SQUARED] \
        + [q for _, q, _ in P.REFUSALS]
    same = moved_conv = moved_other = 0
    for q in qs:
        a, b = read_system(q, phase=103), read_system(q)
        if (a.answered, a.value, a.code, a.script) == \
                (b.answered, b.value, b.code, b.script):
            same += 1
            continue
        try:
            conv = bool(convention(solve_text(q)[0]))
        except S.SymbolicError:
            conv = False
        if conv:
            moved_conv += 1
        else:
            moved_other += 1
    # (c) Phase 103's answered systems keep their branch sets under 104
    kept = 0
    for cid, q, declared in N.SYSTEMS:
        m = branch_matches(solve_branches(q)[0].solutions, declared)
        kept += m["matched"] == len(declared) == m["machine"]
    out = {"phase103_systems": f"{rec_sys}/{len(N.SYSTEMS)}",
           "phase103_refusals": f"{rec_ref}/{len(N.REFUSALS)}",
           "phase98_questions": len(qs), "phase98_same": same,
           "phase98_moved_by_convention": moved_conv,
           "phase98_moved_otherwise": moved_other,
           "phase103_branch_sets_kept": f"{kept}/{len(N.SYSTEMS)}"}
    out["met"] = (rec_sys == len(N.SYSTEMS) - 1 and
                  rec_ref == len(N.REFUSALS) and moved_other == 0 and
                  kept == len(N.SYSTEMS))
    return out


# ---------------------------------------------------------------------------
# K7 -- PLANTED BATTERIES, with an independent count of the real solutions
# ---------------------------------------------------------------------------

class _Cx:
    """A complex number in fixed point (two rounded rationals)."""

    __slots__ = ("re", "im")

    def __init__(self, re_, im=0):
        self.re, self.im = _rnd(re_), _rnd(im)

    def __add__(self, o):
        return _Cx(self.re + o.re, self.im + o.im)

    def __sub__(self, o):
        return _Cx(self.re - o.re, self.im - o.im)

    def __mul__(self, o):
        return _Cx(self.re * o.re - self.im * o.im,
                   self.re * o.im + self.im * o.re)

    def __truediv__(self, o):
        n = o.re * o.re + o.im * o.im
        return _Cx((self.re * o.re + self.im * o.im) / n,
                   (self.im * o.re - self.re * o.im) / n)

    def size(self) -> Fraction:
        return max(abs(self.re), abs(self.im))


def _complex_roots(cs: List[Fraction]) -> List[_Cx]:
    """All complex roots of ``sum cs[i] x^i`` (Durand-Kerner in fixed
    point) -- the report's own instrument, sharing nothing with the exact
    layer."""
    while cs and cs[-1] == 0:
        cs = cs[:-1]
    n = len(cs) - 1
    if n < 1:
        return []
    a = [_Cx(c / cs[-1]) for c in cs]
    seed = _Cx(Fraction(2, 5), Fraction(9, 10))
    roots = [_Cx(1)]
    for _ in range(n - 1):
        roots.append(roots[-1] * seed)
    stop = Fraction(1, 2 ** 70)

    def f(z):
        v = _Cx(0)
        for c in reversed(a):
            v = v * z + c
        return v

    for _ in range(600):
        new = []
        for i, z in enumerate(roots):
            d = _Cx(1)
            for j, w in enumerate(roots):
                if j != i:
                    d = d * (z - w)
            if d.re == 0 and d.im == 0:
                new.append(z + _Cx(Fraction(1, 10 ** 9)))
            else:
                new.append(z - f(z) / d)
        delta = max((x - y).size() for x, y in zip(new, roots))
        roots = new
        if delta < stop:
            break
    return roots


def independent_count(question: str) -> Optional[int]:
    """The number of real solutions ``(x, y)`` of a system of two conics,
    counted numerically without the exact layer: the real roots of the
    resultant in ``x`` (Durand-Kerner in fixed point), each with the real
    ``y`` of either conic that also satisfies both."""
    from ..reasoning import symbolic as S
    from ..reasoning.symbolic_nonlinear import resultant
    body = question.split(":", 1)[1]
    eqs = [S.parse_equation(e.strip()) for e in body.split(";")]
    ps = [(l - r).num for l, r in eqs]
    if "y" not in ps[0].vars():
        ps = [ps[1], ps[0]]
    if "y" not in ps[0].vars():
        return None
    res = ps[1] if "y" not in ps[1].vars() else resultant(ps[0], ps[1], "y")
    if res.is_zero() or res.vars() - {"x"}:
        return None
    cs = res.coeffs("x")
    deg = max(cs)
    coeffs = [Fraction(cs[i].const_value()) if i in cs else Fraction(0)
              for i in range(deg + 1)]
    xs = [z.re for z in _complex_roots(coeffs)
          if abs(z.im) < Fraction(1, 10 ** 7)]
    sols = []
    small = Fraction(1, 10 ** 9)

    def ev(p, x, y):
        return sum((Fraction(c) * x ** dict(m).get("x", 0) *
                    y ** dict(m).get("y", 0) for m, c in p.t.items()),
                   Fraction(0))

    def ys_of(p, x):
        cy = p.coeffs("y")
        a2, a1, a0 = (ev(cy[i], x, 0) if i in cy else Fraction(0)
                      for i in (2, 1, 0))
        if abs(a2) > small:
            d = a1 * a1 - 4 * a2 * a0
            if d < -small:
                return []
            d = _sqrt(max(d, Fraction(0)))
            return [_rnd((-a1 + d) / (2 * a2)), _rnd((-a1 - d) / (2 * a2))]
        if abs(a1) > small:
            return [_rnd(-a0 / a1)]
        return None          # no condition on y at this x

    near = Fraction(1, 10 ** 6)
    for x in xs:
        cands = []
        free = True
        for p in ps:
            if "y" not in p.vars():
                continue
            got = ys_of(p, x)
            if got is not None:
                free = False
                cands.extend(got)
        if free:
            return None      # a whole line of solutions
        for y in cands:
            if all(abs(ev(p, x, y)) < near * (1 + abs(x) + abs(y)) ** 2
                   for p in ps):
                if all(abs(x - u) > near or abs(y - v) > near
                       for u, v in sols):
                    sols.append((x, y))
    return len(sols)


@_AS_SHIPPED
def planted_marks(run_scripts: bool = True) -> Dict[str, object]:
    from .nonlinear_report import planted_battery
    from .symbolic_frames import solve_branches
    out: Dict[str, object] = {}
    met = True
    for seed in C.BATTERY_SEEDS:
        b = planted_battery(seed=seed, run_scripts=run_scripts, phase=104)
        agree = disagree = undecided = 0
        for r in b["rows"]:
            if not r["answered"]:
                continue
            n = independent_count(r["question"])
            if n is None:
                undecided += 1
            elif n == r["branches"]:
                agree += 1
            else:
                disagree += 1
                r["independent"] = n
        b["independent_agree"] = agree
        b["independent_disagree"] = disagree
        b["independent_undecided"] = undecided
        b["met"] = b["wrong"] == 0 and b["planted"] >= 45
        met = met and b["met"]
        out[str(seed)] = {k: v for k, v in b.items() if k != "rows"}
        out[str(seed)]["disagreeing"] = [r for r in b["rows"]
                                         if "independent" in r]
    out["met"] = met
    return out


# ---------------------------------------------------------------------------
# K8 -- RANDOM CUBICS
# ---------------------------------------------------------------------------

@_AS_SHIPPED
def cubic_battery(run_scripts: bool = True) -> Dict[str, object]:
    """Random integer cubics with no rational root: three branches when the
    discriminant is positive, one when it is negative (the discriminant is
    computed here from the coefficients, not by the layer)."""
    from ..reasoning import symbolic as S
    from . import question_frames as qf
    from .symbolic_frames import read_system, solve_branches
    count, seed = C.CUBIC_BATTERY
    lcg = S.Lcg(seed)
    rows = []
    while len(rows) < count:
        a = 1 + lcg.next() % 3
        b, c, d = (int(lcg.next() % 19) - 9 for _ in range(3))
        if d == 0:
            continue
        if any(a * r ** 3 + b * r ** 2 * s + c * r * s ** 2 + d * s ** 3 == 0
               for s in range(1, a + 1) if a % s == 0
               for r0 in range(1, abs(d) + 1) if d % r0 == 0
               for r in (r0, -r0)):
            continue
        disc = (18 * a * b * c * d - 4 * b ** 3 * d + b * b * c * c -
                4 * a * c ** 3 - 27 * a * a * d * d)
        if disc == 0:
            continue
        q = (f"solve symbolically for x: {a}*x^3 + {b}*x^2 + {c}*x + {d} "
             f"= 0")
        want = 3 if disc > 0 else 1
        rd = read_system(q)
        row = {"question": q, "discriminant": disc, "expected": want,
               "answered": rd.answered, "code": rd.code}
        if rd.answered:
            row["branches"] = len(solve_branches(q)[0].solutions)
            if run_scripts:
                row["gate"] = qf.run_gate(rd.script)[0]
        row["ok"] = rd.answered and row.get("branches") == want and \
            row.get("gate", True)
        rows.append(row)
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "three": sum(1 for r in rows if r["expected"] == 3),
            "met": passed == len(rows)}


# ---------------------------------------------------------------------------
# K9 and the report
# ---------------------------------------------------------------------------

def lean_mark() -> Dict[str, object]:
    """K9 (the source half; the build is ``lake build``)."""
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


def _k4(*parts) -> Dict[str, object]:
    rows = [r for p in parts for r in p["rows"] if "gate" in r]
    ok = sum(1 for r in rows if r["gate"])
    mr = sum(1 for r in rows if r.get("mutant_rejected"))
    return {"answered": len(rows), "verified": ok, "mutants_rejected": mr,
            "met": bool(rows) and ok == len(rows) == mr}


#: Post hoc, not a mark: harder systems tried after the marks were declared.
HARD_SYSTEMS: Tuple[str, ...] = (
    "solve symbolically for x, y: x^2 = 2; y^2 = x",
    "solve symbolically for x: x^4 - 2*x^2 - 1 = 0",
    "solve symbolically for x, y in terms of p, q: x^3 + p*x = q; y = x^2",
    "solve symbolically for x, y, z: x + y + z = 6; x*y*z = 6; "
    "x*y + y*z + z*x = 11",
    "solve symbolically for x, y: x^2 + y^2 = 1; x^3 + y^3 = 1",
    "solve symbolically for x, y in terms of a: x^2 + y^2 = a; x*y = 1",
    "solve symbolically for x in terms of a: x^4 - 4*a*x^2 + 2*a^2 = 0",
    "solve symbolically for x: x^6 - 2 = 0",
    "solve symbolically for x: x^5 - x - 1 = 0",
    "solve symbolically for x in terms of a: x^3 - 3*a*x + 1 = 0",
    "solve symbolically for x, y: y = x^3 - 2*x; x = y^3 - 2*y",
)


@_AS_SHIPPED
def exploration(seed: int = 777, pairs: int = 100) -> Dict[str, object]:
    """Post hoc, not a mark.  (a) The harder systems of
    :data:`HARD_SYSTEMS`: answered, branch count, script verified, mutant
    rejected.  (b) ``pairs`` random pairs of general conics (integer
    coefficients in -9..9, *not* planted, so many have no real point):
    how each is read, and whether the branch count agrees with the
    independent numeric count."""
    from ..reasoning import symbolic as S
    from . import question_frames as qf
    from .symbolic_frames import mutated, read_system, solve_branches
    hard = []
    for q in HARD_SYSTEMS:
        rd = read_system(q)
        row = {"question": q, "answered": rd.answered, "code": rd.code}
        if rd.answered:
            row["branches"] = len(solve_branches(q)[0].solutions)
            row["gate"] = qf.run_gate(rd.script)[0]
            row["mutant_rejected"] = not qf.run_gate(mutated(q).script)[0]
        hard.append(row)
    lcg = S.Lcg(seed)
    monos = ("x^2", "x*y", "y^2", "x", "y")
    readings: Dict[str, int] = {}
    agree = disagree = undecided = gate_failed = 0
    for _ in range(pairs):
        eqs = []
        for _ in range(2):
            cs = [int(lcg.next() % 19) - 9 for _ in monos]
            if not any(cs[:3]):
                cs[0] = 1
            c0 = int(lcg.next() % 19) - 9
            eqs.append(" + ".join(f"{c}*{m}" for c, m in zip(cs, monos)
                                  if c) + f" + {c0} = 0")
        q = "solve symbolically for x, y: " + "; ".join(eqs)
        rd = read_system(q)
        key = "answered" if rd.answered else str(rd.code)
        readings[key] = readings.get(key, 0) + 1
        if rd.answered:
            nb = len(solve_branches(q)[0].solutions)
            gate_failed += not qf.run_gate(rd.script)[0]
        elif rd.code in ("NO_REAL_ROOT", "INCONSISTENT"):
            nb = 0
        else:
            continue
        ind = independent_count(q)
        if ind is None:
            undecided += 1
        elif ind == nb:
            agree += 1
        else:
            disagree += 1
    return {"hard": hard,
            "hard_answered": sum(1 for r in hard if r["answered"]),
            "hard_verified": sum(1 for r in hard if r.get("gate")),
            "hard_mutants_rejected": sum(1 for r in hard
                                         if r.get("mutant_rejected")),
            "random": {"seed": seed, "pairs": pairs, "readings": readings,
                       "gate_failed": gate_failed, "independent_agree": agree,
                       "independent_disagree": disagree,
                       "independent_undecided": undecided}}


@_AS_SHIPPED
def cubic_radical_report(run_scripts: bool = True, battery: bool = True
                         ) -> Dict[str, object]:
    k1 = algebraic_marks(run_scripts)
    k2 = radical_marks(run_scripts)
    k5 = dual_marks(run_scripts)
    out: Dict[str, object] = {
        "K1": k1, "K2": k2, "K3": refusal_marks(),
        "K4": _k4(k1, k2, k5) if run_scripts else
        {"met": None, "skipped": True},
        "K5": k5, "K6": regression_mark(),
        "K7": planted_marks(run_scripts) if battery else
        {"met": None, "skipped": True},
        "K8": cubic_battery(run_scripts) if battery else
        {"met": None, "skipped": True},
        "K9": lean_mark(),
    }
    out["marks"] = {k: out[k]["met"] for k in
                    ("K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9")}
    return out
