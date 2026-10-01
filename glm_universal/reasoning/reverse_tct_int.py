"""``glm_universal.reasoning.reverse_tct_int`` -- Reverse TCT over the integers.

Round three of ``studies/REVERSE_TCT_STUDY.md`` (§10, Phase 69): an integer
sort.  Two question forms, ``entails over the integers:`` and ``bounds over
the integers of x:``, read the sentences (or dialect sources) of round two
with every variable ranging over ℤ.  Over ℚ a floor quotient or remainder of
a term with a variable is not piecewise linear with finitely many pieces and
is refused ``NOT_POLYNOMIAL``; over ℤ, with a constant divisor ``b``, it is:

``A // b``, ``A % b``   a fresh integer ``q`` and one case per residue ``r``
                        (``0 .. b-1`` for ``b > 0``, ``b+1 .. 0`` for
                        ``b < 0``, Python's convention), with ``A = b*q + r``
                        joining the case.

Each case is then decided over ℤ: every row is scaled to integer
coefficients, a strict row ``e < 0`` becomes ``e + 1 <= 0``, and every row is
divided by the gcd of its coefficients with the constant rounded up (exact
over ℤ).  Elimination substitutes a variable with a unit coefficient in an
equation where it can and runs Fourier-Motzkin otherwise, tightening every
derived row the same way.  A derived ``0 + k <= 0`` with ``k > 0`` refutes the
case; the certificate is the derivation (each derived row: two earlier rows
and their positive multipliers).  Otherwise an integer witness is sought and
checked exactly.  Elimination with rounding is sound, not complete: a case it
leaves open goes to the complete decision of Phase 79
(``integer_decision``, the Omega test), whose refutation tree the script
checks step by step; ``INTEGER_UNDECIDED`` now means only that a case spent
more than that decision's declared limit of search steps.

``RequestProject/GLM/ReverseTCTThree.lean`` proves the residue split, the
tightening and the derivation step sound (and the split and tightening
exact).  Exact throughout: ``Fraction`` and ``int`` only.
"""

from __future__ import annotations

import itertools
import json
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import reverse_tct as rt
from .reverse_tct import Answer, ReverseRefusal

__all__ = ["entails_int", "bounds_int", "answer_int", "reads_int",
           "tighten", "int_cases", "decide_case", "render_script",
           "mutated_script", "int_report", "PREFIXES"]

#: The two question forms of the integer sort.
PREFIXES: Tuple[str, ...] = ("entails over the integers:",
                             "bounds over the integers of")

#: A divisor of absolute value above this is refused, not split.
RESIDUE_LIMIT = 64
#: Most steps a bound moves inward past refuted values.
BOUND_STEPS = 64
#: Most rows the elimination may hold.
ROW_LIMIT = 20000
#: Most points a bounded witness search visits.
SEARCH_POINTS = 20000
#: Phase 79: hand a case elimination leaves open to the complete decision
#: (``integer_decision``).  ``False`` is round three as it was -- the control
#: of ``studies/INTEGER_DECISION_STUDY.md``, never a setting in use.
COMPLETE = True

IntRow = Tuple[Tuple[Tuple[str, int], ...], int]   # sum(c*v) + k <= 0


def _undecided(msg: str) -> ReverseRefusal:
    return ReverseRefusal("INTEGER_UNDECIDED", msg)


# ===========================================================================
# 1.  THE RESIDUE SPLIT
# ===========================================================================

def _fd_node(t):
    """The innermost (post-order first) floor quotient or remainder over a
    variable in ``t``, or ``None``."""
    if not isinstance(t, tuple) or not t or t[0] in ("lit", "var", "mask"):
        return None
    for x in t[1:]:
        if isinstance(x, tuple):
            got = _fd_node(x)
            if got is not None:
                return got
    if t[0] in ("floordiv", "mod") and rt._variables(t):
        return t
    return None


def _divisor(n) -> int:
    """The divisor of a split node, checked: a nonzero integer constant of
    absolute value at most :data:`RESIDUE_LIMIT`; the dividend linear with
    integer coefficients and constant."""
    words = "floor quotient" if n[0] == "floordiv" else "remainder"
    if rt._variables(n[2]):
        raise ReverseRefusal("NOT_POLYNOMIAL", f"a {words} by a term with a "
                             "variable is not split into residues")
    b = rt.evaluate(n[2], {})
    if not isinstance(b, Fraction):
        raise rt._mismatch("a mask is not a number")
    if b == 0:
        raise ReverseRefusal("DIVISION_BY_ZERO", f"a {words} by zero")
    if b.denominator != 1:
        raise ReverseRefusal("NOT_INTEGER", f"a {words} by {b}, which is "
                             "not an integer")
    if abs(b) > RESIDUE_LIMIT:
        raise ReverseRefusal("NOT_IN_FRAGMENT", f"a {words} by {b}: more "
                             f"than {RESIDUE_LIMIT} residue cases")
    p = rt.poly_of(n[1])
    if rt.degree(p) > 1:
        raise ReverseRefusal("NONLINEAR", f"the dividend of a {words} has "
                             f"degree {rt.degree(p)}")
    if any(c.denominator != 1 for c in p.values()):
        raise ReverseRefusal("NOT_INTEGER", f"the dividend of a {words} is "
                             "not integer-valued")
    return b.numerator


def _residues(case, depth: int = 0):
    """Split ``case`` at its innermost floor quotient or remainder, one case
    per residue, recursively."""
    n = None
    for _, a, b in case:
        n = _fd_node(a) or _fd_node(b)
        if n is not None:
            break
    if n is None:
        return [case]
    b = _divisor(n)
    A, B = n[1], n[2]
    q = ("var", f"_q{depth + 1}")
    fl, md = ("floordiv", A, B), ("mod", A, B)
    out = []
    for r in (range(0, b) if b > 0 else range(b + 1, 1)):
        lit = ("lit", Fraction(r))
        new = [(op, rt._replace(rt._replace(x, fl, q), md, lit),
                rt._replace(rt._replace(y, fl, q), md, lit))
               for op, x, y in case]
        new.append(("=", A, ("add", ("mul", B, q), lit)))
        out += _residues(new, depth + 1)
        if len(out) > rt.CASE_LIMIT:
            raise rt._nf("the system splits into too many cases")
    return out


def _check_numeric(s) -> None:
    for c in rt._clauses(s):
        for r in c:
            if r[1] in rt._REL_SORT and rt._REL_SORT[r[1]] != ("n", "n") or \
                    "m" in (rt.sort_of(r[2]), rt.sort_of(r[3])):
                raise rt._nf("a mask statement is closed: say decides it")


def int_cases(stmts: Sequence) -> List[List[Tuple[str, object, object]]]:
    """The case systems of ``stmts`` over ℤ: round two's cases (one relation
    per clause, ``!=`` split, ``abs``/``min``/``max`` split), each split
    further into residue cases; every side checked linear."""
    for s in stmts:
        _check_numeric(s)
    out = []
    for case in rt._cases(stmts):
        for c in _residues(case):
            for _, a, b in c:
                rt._linear(a)
                rt._linear(b)
            out.append(c)
            if len(out) > rt.CASE_LIMIT:
                raise rt._nf("the system splits into too many cases")
    return out


# ===========================================================================
# 2.  ROWS OVER ℤ -- TIGHTENING AND THE DERIVATION
# ===========================================================================

def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def _lcm(a: int, b: int) -> int:
    return a * b // _gcd(a, b)


def tighten(co: Dict[str, Fraction], k: Fraction, strict: bool) -> IntRow:
    """``sum(co*v) + k < 0`` (strict) or ``<= 0``, over integer ``v``, as an
    equivalent row ``sum(c*v) + k' <= 0`` with coprime integer
    coefficients."""
    den = 1
    for c in list(co.values()) + [Fraction(k)]:
        den = _lcm(den, Fraction(c).denominator)
    ic = {v: int(Fraction(c) * den) for v, c in co.items() if c}
    ik = int(Fraction(k) * den)
    if strict:
        ik += 1
    g = 0
    for c in ic.values():
        g = _gcd(g, c)
    if g > 1:
        ic = {v: c // g for v, c in ic.items()}
        ik = -((-ik) // g)
    return tuple(sorted(ic.items())), ik


def _combine(r: IntRow, a: int, s: IntRow, b: int) -> IntRow:
    co: Dict[str, Fraction] = {}
    for v, c in r[0]:
        co[v] = co.get(v, Fraction(0)) + a * c
    for v, c in s[0]:
        co[v] = co.get(v, Fraction(0)) + b * c
    return tighten({v: c for v, c in co.items() if c},
                   Fraction(a * r[1] + b * s[1]), False)


def _input_rows(case) -> List[IntRow]:
    return [tighten(dict(r.coeffs), r.const, r.strict)
            for r in rt._system(case)]


def _row_holds(row: IntRow, env: Dict[str, int]) -> bool:
    return sum(c * env.get(v, 0) for v, c in row[0]) + row[1] <= 0


def _refute(rows: List[IntRow]):
    """Eliminate over ℤ.  ``("unsat", derivation, index)`` -- ``derivation``
    a list of ``(i, a, j, b)`` appended after the input rows, the last row
    (``index``) a contradiction -- or ``("open", stages)``."""
    allrows = list(rows)
    parent: List[Optional[Tuple[int, int, int, int]]] = [None] * len(rows)
    for i, r in enumerate(rows):
        if not r[0] and r[1] > 0:
            return "unsat", [], i
    active = []
    seen = set()
    for i, r in enumerate(rows):
        if r[0] and r not in seen:
            seen.add(r)
            active.append(i)
    stages = []

    def add(r: IntRow, par) -> Optional[int]:
        allrows.append(r)
        parent.append(par)
        return len(allrows) - 1

    while True:
        vs = sorted({v for i in active for v, _ in allrows[i][0]})
        if not vs:
            return "open", stages
        # an equation with a unit coefficient: substitute exactly
        eq = None
        index = {allrows[i]: i for i in active}
        for i in active:
            r = allrows[i]
            opp = (tuple((v, -c) for v, c in r[0]), -r[1])
            j = index.get(opp)
            if j is None:
                continue
            for v, c in r[0]:
                if abs(c) == 1:
                    eq = (i, j, v)
                    break
            if eq:
                break
        new_active: List[int] = []
        if eq is not None:
            i, j, v = eq
            ci = dict(allrows[i][0])[v]
            stages.append(("eq", v, allrows[i]))
            for m in active:
                if m in (i, j):
                    continue
                cm = dict(allrows[m][0]).get(v, 0)
                if not cm:
                    new_active.append(m)
                    continue
                other = j if (cm > 0) == (ci > 0) else i
                r = _combine(allrows[m], 1, allrows[other], abs(cm))
                idx = add(r, (m, 1, other, abs(cm)))
                if not r[0]:
                    if r[1] > 0:
                        return "unsat", _prune(parent, len(rows), idx), None
                    continue
                new_active.append(idx)
        else:
            def cost(v):
                pos = sum(1 for i in active if dict(allrows[i][0]).get(v, 0)
                          > 0)
                neg = sum(1 for i in active if dict(allrows[i][0]).get(v, 0)
                          < 0)
                return (pos * neg - pos - neg, v)
            v = min(vs, key=cost)
            pos = [i for i in active if dict(allrows[i][0]).get(v, 0) > 0]
            neg = [i for i in active if dict(allrows[i][0]).get(v, 0) < 0]
            stages.append(("fm", v, [allrows[i] for i in pos + neg]))
            new_active = [i for i in active
                          if not dict(allrows[i][0]).get(v, 0)]
            for p in pos:
                for q in neg:
                    cp = dict(allrows[p][0])[v]
                    cq = -dict(allrows[q][0])[v]
                    g = _gcd(cp, cq)
                    a, b = cq // g, cp // g
                    r = _combine(allrows[p], a, allrows[q], b)
                    idx = add(r, (p, a, q, b))
                    if not r[0]:
                        if r[1] > 0:
                            return ("unsat", _prune(parent, len(rows), idx),
                                    None)
                        continue
                    new_active.append(idx)
                    if len(allrows) > ROW_LIMIT:
                        raise ReverseRefusal("NOT_IN_FRAGMENT", "the system "
                                             "is too large to eliminate")
        # de-duplicate
        active, seen = [], set()
        for i in new_active:
            if allrows[i] not in seen:
                seen.add(allrows[i])
                active.append(i)


def _prune(parent, n_inputs: int, last: int):
    """The derivation of row ``last``, pruned to its ancestry and renumbered
    after the ``n_inputs`` input rows."""
    need, stack = set(), [last]
    while stack:
        i = stack.pop()
        if i < n_inputs or i in need:
            continue
        need.add(i)
        _, _, j, _ = parent[i]
        stack += [parent[i][0], j]
    order = sorted(need)
    renum = {i: i for i in range(n_inputs)}
    out = []
    for k, i in enumerate(order):
        p, a, q, b = parent[i]
        out.append((renum[p], a, renum[q], b))
        renum[i] = n_inputs + k
    return out


def _back_substitute(stages) -> Optional[Dict[str, int]]:
    env: Dict[str, int] = {}
    for kind, v, data in reversed(stages):
        if kind == "eq":
            co = dict(data[0])
            c = co[v]
            rest = sum(co[w] * env.get(w, 0) for w in co if w != v) + data[1]
            env[v] = -rest // c if c > 0 else rest // (-c)
            if c * env[v] + rest != 0:
                return None
            continue
        lo, hi = None, None
        for row in data:
            co = dict(row[0])
            c = co[v]
            rest = sum(co[w] * env.get(w, 0) for w in co if w != v) + row[1]
            if c > 0:                      # c*v <= -rest
                b = (-rest) // c
                hi = b if hi is None else min(hi, b)
            else:                          # v >= rest / (-c)
                b = -((-rest) // (-c))
                lo = b if lo is None else max(lo, b)
        if lo is not None and hi is not None and lo > hi:
            return None
        val = 0
        if lo is not None and val < lo:
            val = lo
        if hi is not None and val > hi:
            val = hi
        env[v] = val
    return env


def _search(rows: List[IntRow], centre: Dict[str, int]) -> Optional[
        Dict[str, int]]:
    vs = sorted({v for r in rows for v, _ in r[0]})
    if not vs:
        return {} if all(_row_holds(r, {}) for r in rows) else None
    radius = 1
    while (2 * (radius + 1) + 1) ** len(vs) <= SEARCH_POINTS:
        radius += 1
    if (2 * radius + 1) ** len(vs) > SEARCH_POINTS:
        return None
    for d in itertools.product(range(-radius, radius + 1), repeat=len(vs)):
        env = {v: centre.get(v, 0) + x for v, x in zip(vs, d)}
        if all(_row_holds(r, env) for r in rows):
            return env
    return None


def decide_case(case):
    """``("unsat", certificate)``, ``("sat", env)`` (an integer point of the
    case, fresh quotients included) or ``("unknown", None)``."""
    rows = _input_rows(case)
    status, got, idx = (_refute(rows) + (None,))[:3]
    if status == "unsat":
        return "unsat", {"rows": [[op, rt._enc(a), rt._enc(b)]
                                  for op, a, b in case],
                         "derivation": [list(d) for d in got],
                         "contradiction": idx}
    env = _back_substitute(got)
    if env is not None and all(_row_holds(r, env) for r in rows):
        return "sat", env
    centres = [env or {}]
    fm = rt._fm(rt._system(case), sorted({v for r in rows for v, _ in r[0]}))
    if fm[0] == "sat":
        centres.append({v: int(x.__floor__()) for v, x in fm[1].items()})
    centres.append({})
    for c in centres:
        found = _search(rows, c)
        if found is not None:
            return "sat", found
    # Phase 79: the complete decision (the Omega test) on what is left open
    if not COMPLETE:
        return "unknown", None
    from . import integer_decision as idc
    try:
        status, got = idc.decide_rows(rows)
    except idc.DecisionLimit:
        return "unknown", None
    if status == "unsat":
        return "unsat", {"rows": [[op, rt._enc(a), rt._enc(b)]
                                  for op, a, b in case],
                         "omega": got}
    return "sat", got


def _user(env: Dict[str, int], vs: Sequence[str]) -> Dict[str, Fraction]:
    return {v: Fraction(env.get(v, 0)) for v in vs}


def _consistent(stmts: Sequence, vs: Sequence[str]):
    """``(True, witness)`` or ``(False, [certificate per case])`` over ℤ;
    ``INTEGER_UNDECIDED`` if some case is neither refuted nor witnessed."""
    certs, unknown = [], False
    for case in int_cases(stmts):
        status, got = decide_case(case)
        if status == "sat":
            w = _user(got, vs)
            if not all(rt.holds(s, w) for s in stmts):
                raise AssertionError("a case witness fails the statements")
            return True, w
        if status == "unsat":
            certs.append(got)
        else:
            unknown = True
    if unknown:
        w = _search_statements(stmts, vs)
        if w is not None:
            return True, w
        raise _undecided("a case spent more than the complete decision's "
                         "declared limit of search steps without being "
                         "refuted or witnessed")
    return False, certs


def _search_statements(stmts, vs) -> Optional[Dict[str, Fraction]]:
    radius = 1
    while (2 * (radius + 1) + 1) ** max(len(vs), 1) <= SEARCH_POINTS:
        radius += 1
    for d in itertools.product(range(-radius, radius + 1), repeat=len(vs)):
        env = {v: Fraction(x) for v, x in zip(vs, d)}
        try:
            if all(rt.holds(s, env) for s in stmts):
                return env
        except ZeroDivisionError:
            continue
    return None


# ===========================================================================
# 3.  THE OPERATIONS
# ===========================================================================

_OVER = "over the integers"


def _parse_statements(texts: Sequence[str]) -> List:
    out = []
    for t in texts:
        s, _ = rt.parse_any(t)
        if not rt._is_statement(s):
            raise rt._nf("a premise or conclusion is a statement, not a term")
        out.append(s)
    return out


def entails_int(premises: Sequence[str], conclusion: str) -> Answer:
    """``ENTAILS`` / ``CONTRADICTS`` / ``INDEPENDENT`` with every variable an
    integer."""
    op = "entails-int"
    try:
        ps = _parse_statements(premises)
        c = _parse_statements([conclusion])[0]
        for s in ps + [c]:
            int_cases([s])                  # refusals before any search
        vs = rt._variables((tuple(ps), c))
        base = {"kind": "entails-int", "premises": [rt._enc(s) for s in ps],
                "conclusion": rt._enc(c), "vars": vs}
        col1 = [rt.realise(s) for s in ps] + [rt.realise(c)]
        col2 = [rt._math(s) for s in ps] + [rt._math(c)] + [
            ", ".join(vs) + " ∈ ℤ" if vs else "ℤ"]
        ok, got = _consistent(ps, vs)
        if not ok:
            exc = ReverseRefusal("INCONSISTENT_PREMISES", "no integer point "
                                 "satisfies the premises, so every "
                                 "conclusion would follow")
            a = rt._refused(op, exc)
            a.column1 = [rt.realise(s) for s in ps] + a.column1
            a.certificate = dict(base, verdict="INCONSISTENT_PREMISES",
                                 inconsistent=got)
            return a
        certs, fails_at = [], None
        for clause in rt._clauses(c):
            negated = [rt._neg_rel(r) for r in clause]
            e_ok, e_got = _consistent(ps + negated, vs)
            if e_ok:
                fails_at = e_got
                break
            certs.append({"negated": [rt._enc(n) for n in negated],
                          "cases": e_got})
        if fails_at is None:
            verdict, cert = "ENTAILS", dict(base, entails=certs)
            word = "follows from the premises " + _OVER
        else:
            c_ok, c_got = _consistent(ps + [c], vs)
            if not c_ok:
                verdict = "CONTRADICTS"
                cert = dict(base, contradicts=c_got)
                word = "contradicts the premises " + _OVER
            else:
                verdict = "INDEPENDENT"
                cert = dict(base, holds_at=rt._enc_point(c_got),
                            fails_at=rt._enc_point(fails_at))
                word = ("neither follows from nor contradicts the premises "
                        + _OVER)
        cert["verdict"] = verdict
        return Answer(op, verdict, f"{rt.realise(c)} : {word}",
                      col1 + [word], col2, cert)
    except ReverseRefusal as exc:
        return rt._refused(op, exc)


def _rational_ends(ps, var):
    """Per case not refuted over ℤ: its status and rational bounds on
    ``var``."""
    out = []
    for case in int_cases(ps):
        status, got = decide_case(case)
        if status == "unsat":
            continue
        cvs = sorted(set(rt._variables(tuple(x for _, a, b in case
                                             for x in (a, b)))) | {var})
        lo, lo_s, hi, hi_s = rt._project(case, var, cvs)
        out.append((status, lo, lo_s, hi, hi_s))
    return out


def _int_end(v: Optional[Fraction], strict: bool, lower: bool):
    if v is None:
        return None
    if lower:
        c = -((-v.numerator) // v.denominator)          # ceil
        return c + 1 if strict and c == v else c
    c = v.numerator // v.denominator                    # floor
    return c - 1 if strict and c == v else c


def _pin(var: str, op: str, c: int):
    return ("rel", op, ("var", var), ("lit", Fraction(c)))


def _one_end(ps, var, vs, ends, lower: bool):
    """The tightest integer bound on one side, with its certificate, or
    ``None`` (unbounded)."""
    cands = []
    for status, lo, lo_s, hi, hi_s in ends:
        e = _int_end(lo, lo_s, True) if lower else _int_end(hi, hi_s, False)
        if e is None:
            if status == "sat":
                return None
            raise _undecided(f"a case not decided over ℤ is unbounded "
                             f"{'below' if lower else 'above'} over ℚ")
        cands.append(e)
    c0 = min(cands) if lower else max(cands)
    step = 1 if lower else -1
    beyond = _pin(var, "<=" if lower else ">=", c0 - step)
    ok, below = _consistent(ps + [beyond], vs)
    if ok:
        raise AssertionError("a projected integer bound is not a bound")
    gaps = []
    c = c0
    for _ in range(BOUND_STEPS):
        ok, got = _consistent(ps + [_pin(var, "=", c)], vs)
        if ok:
            return c, {"beyond": rt._enc(beyond), "refuted": below,
                       "gaps": gaps, "witness": rt._enc_point(got),
                       "bound": c}
        gaps.append({"value": c, "refuted": got})
        c += step
    raise _undecided("the bound moved more than "
                     f"{BOUND_STEPS} steps without being attained")


def bounds_int(var: str, premises: Sequence[str]) -> Answer:
    """The tightest integer bounds on ``var`` the premises imply over ℤ."""
    op = "bounds-int"
    try:
        ps = _parse_statements(premises)
        vs = sorted(set(rt._variables(tuple(ps))) | {var})
        ok, got = _consistent(ps, vs)
        if not ok:
            exc = ReverseRefusal("INCONSISTENT_PREMISES", "no integer point "
                                 "satisfies the premises")
            a = rt._refused(op, exc)
            a.column1 = [rt.realise(s) for s in ps] + a.column1
            a.certificate = {"kind": "bounds-int", "verdict":
                             "INCONSISTENT_PREMISES", "premises":
                             [rt._enc(s) for s in ps], "vars": vs,
                             "inconsistent": got}
            return a
        ends = _rational_ends(ps, var)
        low = _one_end(ps, var, vs, ends, True)
        high = _one_end(ps, var, vs, ends, False)
        x = ("var", var)
        parts = []
        if low and high and low[0] == high[0]:
            parts = [("rel", "=", x, ("lit", Fraction(low[0])))]
        else:
            if low:
                parts.append(("rel", ">=", x, ("lit", Fraction(low[0]))))
            if high:
                parts.append(("rel", "<=", x, ("lit", Fraction(high[0]))))
        if not parts:
            out = ("free", var)
        else:
            out = parts[0] if len(parts) == 1 else ("and", tuple(parts))
        cert = {"kind": "bounds-int", "premises": [rt._enc(s) for s in ps],
                "var": var, "vars": vs, "answer": rt._enc(out),
                "lower": low[1] if low else None,
                "upper": high[1] if high else None,
                "verdict": "BOUNDED" if parts else "FREE"}
        return Answer(op, cert["verdict"], rt.realise(out),
                      [rt.realise(s) for s in ps] + [rt.realise(out), _OVER],
                      [rt._math(s) for s in ps] + [rt._math(out),
                                                    ", ".join(vs) + " ∈ ℤ"],
                      cert)
    except ReverseRefusal as exc:
        return rt._refused(op, exc)


def reads_int(text: str) -> bool:
    t = text.strip().lower()
    if t.startswith(PREFIXES[0]):
        return True
    if t.startswith(PREFIXES[1] + " ") and ":" in t:
        return len(t.split(":", 1)[0].split()) == 6
    return False


def answer_int(text: str) -> Answer:
    t = text.strip()
    low = t.lower()
    if low.startswith(PREFIXES[0]):
        body = t[len(PREFIXES[0]):]
        if ";" not in body:
            return rt._refused("entails-int", ReverseRefusal(
                "UNREADABLE", "entails over the integers: PREMISES ; "
                "CONCLUSION"))
        parts = [x.strip() for x in body.split(";")]
        ps = [q for x in parts[:-1] for q in rt._premise_list(x)]
        return entails_int(ps, parts[-1])
    head, body = t.split(":", 1)
    var = head.split()[5]
    return bounds_int(var, [q for x in body.split(";")
                            for q in rt._premise_list(x)])


# ===========================================================================
# 4.  COLUMN 3 -- THE SCRIPT THAT CHECKS AN INTEGER ANSWER
# ===========================================================================

_SCRIPT = r'''"""Column 3 of a Reverse TCT answer over the integers -- generated.

Re-reads every column-1 sentence with the declared reader and compares it with
the column-2 structure; re-derives the case split (clauses, pieces, residues)
with its own code; re-checks every tightening, every combination and every
witness with its own exact arithmetic.  Prints VERIFIED True only if
everything holds.
"""
import itertools
import json
import sys
from fractions import Fraction

sys.path.insert(0, @@ROOT@@)
from glm_universal.reasoning import reverse_tct as rt

DATA = json.loads(@@DATA@@)
ZERO = ["lit", "0/1"]
NEG = {"=": "!=", "!=": "=", "<": ">=", "<=": ">", ">": "<=", ">=": "<"}


def F(s):
    n, d = s.split("/")
    return Fraction(int(n), int(d))


def ev(t, env):
    k = t[0]
    if k == "lit":
        return F(t[1])
    if k == "var":
        return env[t[1]]
    if k == "neg":
        return -ev(t[1], env)
    if k == "abs":
        return abs(ev(t[1], env))
    if k == "pow":
        b = ev(t[1], env)
        if t[2] < 0 and b == 0:
            raise ZeroDivisionError
        return b ** t[2]
    a, b = ev(t[1], env), ev(t[2], env)
    if k == "add":
        return a + b
    if k == "sub":
        return a - b
    if k == "mul":
        return a * b
    if k == "min":
        return a if a <= b else b
    if k == "max":
        return a if a >= b else b
    if b == 0:
        raise ZeroDivisionError
    if k == "div":
        return a / b
    if k == "floordiv":
        return Fraction((a / b).__floor__())
    if k == "mod":
        return a - b * (a / b).__floor__()
    raise ValueError(k)


def names(t, out):
    if isinstance(t, list):
        if len(t) == 2 and t[0] == "var":
            out.add(t[1])
        for x in t:
            names(x, out)
    return out


def holds(s, env):
    if s[0] == "and":
        return all(holds(r, env) for r in s[1])
    if s[0] == "or":
        return any(holds(r, env) for r in s[1])
    a, b = ev(s[2], env), ev(s[3], env)
    return {"=": a == b, "!=": a != b, "<": a < b, "<=": a <= b,
            ">": a > b, ">=": a >= b}[s[1]]


def clauses(s):
    if s[0] == "rel":
        return [[s]]
    if s[0] == "or":
        return [list(s[1])]
    return [c for x in s[1] for c in clauses(x)]


def replace(t, node, by):
    if t == node:
        return by
    if not isinstance(t, list) or not t or t[0] in ("lit", "var", "mask"):
        return t
    return [replace(x, node, by) if isinstance(x, list) else x for x in t]


def pw(t):
    if not isinstance(t, list) or not t or t[0] in ("lit", "var", "mask"):
        return None
    if t[0] in ("abs", "min", "max") and names(t, set()):
        return t
    for x in t[1:]:
        if isinstance(x, list):
            got = pw(x)
            if got is not None:
                return got
    return None


def pieces(case):
    n = None
    for op, a, b in case:
        n = pw(a) or pw(b)
        if n is not None:
            break
    if n is None:
        return [case]
    if n[0] == "abs":
        br = [([">=", n[1], ZERO], n[1]), (["<", n[1], ZERO], ["neg", n[1]])]
    elif n[0] == "min":
        br = [(["<=", n[1], n[2]], n[1]), ([">", n[1], n[2]], n[2])]
    else:
        br = [([">=", n[1], n[2]], n[1]), (["<", n[1], n[2]], n[2])]
    out = []
    for cond, by in br:
        out += pieces([[op, replace(a, n, by), replace(b, n, by)]
                       for op, a, b in case] + [cond])
    return out


def fd(t):
    if not isinstance(t, list) or not t or t[0] in ("lit", "var", "mask"):
        return None
    for x in t[1:]:
        if isinstance(x, list):
            got = fd(x)
            if got is not None:
                return got
    if t[0] in ("floordiv", "mod") and names(t, set()):
        return t
    return None


def residues(case, depth=0):
    n = None
    for op, a, b in case:
        n = fd(a) or fd(b)
        if n is not None:
            break
    if n is None:
        return [case]
    assert not names(n[2], set()), "a divisor with a variable"
    b = ev(n[2], {})
    assert b.denominator == 1 and b != 0 and abs(b) <= 64, "bad divisor"
    b = b.numerator
    q = ["var", "_q%d" % (depth + 1)]
    fl, md = ["floordiv", n[1], n[2]], ["mod", n[1], n[2]]
    out = []
    for r in (range(0, b) if b > 0 else range(b + 1, 1)):
        lit = ["lit", "%d/1" % r]
        new = [[op, replace(replace(x, fl, q), md, lit),
                replace(replace(y, fl, q), md, lit)] for op, x, y in case]
        new.append(["=", n[1], ["add", ["mul", n[2], q], lit]])
        out += residues(new, depth + 1)
    return out


def expected_cases(stmts):
    choices = []
    for s in stmts:
        for c in clauses(s):
            alts = []
            for r in c:
                if r[1] == "!=":
                    alts += [["<", r[2], r[3]], [">", r[2], r[3]]]
                else:
                    alts.append([r[1], r[2], r[3]])
            choices.append(alts)
    out = []
    for combo in itertools.product(*choices):
        for p in pieces([list(x) for x in combo]):
            out += residues(p)
    return out


def affine(t, vs):
    zero = {v: Fraction(0) for v in vs}
    c0 = ev(t, zero)
    co = {}
    for v in vs:
        e = dict(zero)
        e[v] = Fraction(1)
        co[v] = ev(t, e) - c0
    # affine exactly: agree with the interpolation on {0, 1, 2}^n
    for pt in itertools.product(range(3), repeat=len(vs)):
        e = dict(zip(vs, map(Fraction, pt)))
        assert ev(t, e) == c0 + sum(co[v] * e[v] for v in vs), "not affine"
    return co, c0


def gcd(a, b):
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def tight(co, k, strict):
    den = 1
    for c in list(co.values()) + [k]:
        d = Fraction(c).denominator
        den = den * d // gcd(den, d)
    ic = {v: int(c * den) for v, c in co.items() if c}
    ik = int(k * den) + (1 if strict else 0)
    g = 0
    for c in ic.values():
        g = gcd(g, c)
    if g > 1:
        ic = {v: c // g for v, c in ic.items()}
        ik = -((-ik) // g)
    return ic, ik


def rows_of(case):
    vs = sorted(set().union(*[names(a, set()) | names(b, set())
                              for _, a, b in case]))
    out = []
    for op, a, b in case:
        ca, ka = affine(a, vs)
        cb, kb = affine(b, vs)
        d = {v: ca[v] - cb[v] for v in vs}
        k = ka - kb
        n = {v: -c for v, c in d.items()}
        if op == "<":
            out.append(tight(d, k, True))
        elif op == "<=":
            out.append(tight(d, k, False))
        elif op == ">":
            out.append(tight(n, -k, True))
        elif op == ">=":
            out.append(tight(n, -k, False))
        else:
            assert op == "="
            out += [tight(d, k, False), tight(n, -k, False)]
    return out


def iscomb(r, a, s, b):
    co = {}
    for v, c in r[0].items():
        co[v] = co.get(v, 0) + a * c
    for v, c in s[0].items():
        co[v] = co.get(v, 0) + b * c
    return tight({v: Fraction(c) for v, c in co.items() if c},
                 Fraction(a * r[1] + b * s[1]), False)


def issubst(r, v, s, qs, q0):
    c = r[0].get(v, 0)
    if not c:
        return r
    co = {w: x for w, x in r[0].items() if w != v}
    co[s] = co.get(s, 0) + c
    for w, q in qs:
        co[w] = co.get(w, 0) + c * q
    return tight({w: Fraction(x) for w, x in co.items() if x},
                 Fraction(r[1] + c * q0), False)


def isint(x):
    return isinstance(x, int) and not isinstance(x, bool)


def omega_ok(rows, node):
    """The Omega refutation tree: combinations, substitutions of a fresh
    variable, and splits of a row into s = 0, ..., s = -K and s <= -K - 1."""
    rows = list(rows)
    for st in node["steps"]:
        if st[0] == "comb":
            _, i, a, j, b = st
            assert all(isint(x) for x in (i, a, j, b)) and a > 0 and b > 0
            assert 0 <= i < len(rows) and 0 <= j < len(rows)
            rows.append(iscomb(rows[i], a, rows[j], b))
        elif st[0] == "subst":
            _, v, s, qs, q0 = st
            held = set().union(*[set(r[0]) for r in rows]) if rows else set()
            assert isinstance(v, str) and isinstance(s, str) and v != s
            assert s not in held and isint(q0)
            assert all(isinstance(w, str) and w not in (v, s) and isint(q)
                       for w, q in qs)
            rows = [issubst(r, v, s, qs, q0) for r in rows]
        else:
            return False
    end = node["end"]
    if end[0] == "contra":
        assert isint(end[1]) and 0 <= end[1] < len(rows)
        r = rows[end[1]]
        return not r[0] and r[1] > 0
    if end[0] == "split":
        _, i, K, kids = end
        assert isint(i) and 0 <= i < len(rows) and isint(K) and K >= 0
        if len(kids) != K + 2:
            return False
        co, k = rows[i]
        neg = {v: -c for v, c in co.items()}
        for n in range(K + 1):
            extra = [tight({v: Fraction(c) for v, c in co.items()},
                           Fraction(k + n), False),
                     tight({v: Fraction(c) for v, c in neg.items()},
                           Fraction(-(k + n)), False)]
            if not omega_ok(rows + extra, kids[n]):
                return False
        tail = tight({v: Fraction(c) for v, c in co.items()},
                     Fraction(k + K + 1), False)
        return omega_ok(rows + [tail], kids[K + 1])
    return False


def refuted(case, cert):
    if cert["rows"] != case:
        return False
    rows = rows_of(case)
    if "omega" in cert:
        return omega_ok(rows, cert["omega"])
    for i, a, j, b in cert["derivation"]:
        assert isinstance(a, int) and isinstance(b, int) and a > 0 and b > 0
        co = {}
        for v, c in rows[i][0].items():
            co[v] = co.get(v, 0) + a * c
        for v, c in rows[j][0].items():
            co[v] = co.get(v, 0) + b * c
        rows.append(tight({v: Fraction(c) for v, c in co.items() if c},
                          Fraction(a * rows[i][1] + b * rows[j][1]), False))
    last = rows[-1] if cert["contradiction"] is None else \
        rows[cert["contradiction"]]
    return not last[0] and last[1] > 0


def refutes_all(stmts, certs):
    want = expected_cases(stmts)
    return len(want) == len(certs) and all(
        refuted(c, x) for c, x in zip(want, certs))


def integer_point(p, vs):
    e = {v: Fraction(0) for v in vs}
    e.update({v: F(x) for v, x in p.items()})
    assert all(x.denominator == 1 for x in e.values()), "not an integer point"
    return e


def pin(var, op, c):
    return ["rel", op, ["var", var], ["lit", "%d/1" % c]]


def end_ok(ps, var, vs, end, lower):
    step = 1 if lower else -1
    c0 = end["bound"] - step * len(end["gaps"])
    if end["beyond"] != pin(var, "<=" if lower else ">=", c0 - step):
        return False
    if not refutes_all(ps + [end["beyond"]], end["refuted"]):
        return False
    for k, g in enumerate(end["gaps"]):
        if g["value"] != c0 + step * k:
            return False
        if not refutes_all(ps + [pin(var, "=", g["value"])], g["refuted"]):
            return False
    w = integer_point(end["witness"], vs)
    return all(holds(s, w) for s in ps) and w[var] == end["bound"]


def check(c):
    ps = c["premises"]
    vs = c["vars"]
    if c["kind"] == "entails-int":
        if c["verdict"] == "INCONSISTENT_PREMISES":
            return refutes_all(ps, c["inconsistent"])
        concl = c["conclusion"]
        if c["verdict"] == "ENTAILS":
            cs = clauses(concl)
            if len(cs) != len(c["entails"]):
                return False
            for cl, x in zip(cs, c["entails"]):
                negated = [["rel", NEG[r[1]], r[2], r[3]] for r in cl]
                if x["negated"] != negated or not refutes_all(
                        ps + negated, x["cases"]):
                    return False
            return True
        if c["verdict"] == "CONTRADICTS":
            return refutes_all(ps + [concl], c["contradicts"])
        h = integer_point(c["holds_at"], vs)
        f = integer_point(c["fails_at"], vs)
        return (all(holds(s, h) for s in ps) and holds(concl, h)
                and all(holds(s, f) for s in ps) and not holds(concl, f))
    if c["verdict"] == "INCONSISTENT_PREMISES":
        return refutes_all(ps, c["inconsistent"])
    var, ans = c["var"], c["answer"]
    lo, hi = c["lower"], c["upper"]
    if lo is not None and not end_ok(ps, var, vs, lo, True):
        return False
    if hi is not None and not end_ok(ps, var, vs, hi, False):
        return False
    x = ["var", var]
    parts = []
    if lo is not None and hi is not None and lo["bound"] == hi["bound"]:
        parts = [["rel", "=", x, ["lit", "%d/1" % lo["bound"]]]]
    else:
        if lo is not None:
            parts.append(["rel", ">=", x, ["lit", "%d/1" % lo["bound"]]])
        if hi is not None:
            parts.append(["rel", "<=", x, ["lit", "%d/1" % hi["bound"]]])
    if not parts:
        want = ["free", var]
    else:
        want = parts[0] if len(parts) == 1 else ["and", parts]
    return ans == want


def claimed(c):
    """Every structure the certificate is about, which column 1 states."""
    out = list(c["premises"])
    if c["kind"] == "entails-int" and c["verdict"] != "INCONSISTENT_PREMISES":
        out.append(c["conclusion"])
    if c["kind"] == "bounds-int" and c["verdict"] != "INCONSISTENT_PREMISES":
        out.append(c["answer"])
    return out


ok = True
read = {}
for sentence, structure in DATA["read_back"]:
    got = json.loads(json.dumps(rt._enc(rt.read(sentence))))
    ok = ok and got == structure
    read[json.dumps(structure, sort_keys=True)] = sentence
for s in claimed(DATA["certificate"]):
    ok = ok and json.dumps(s, sort_keys=True) in read
try:
    ok = ok and bool(check(DATA["certificate"]))
except (AssertionError, KeyError, IndexError, TypeError, ValueError,
        ZeroDivisionError):
    ok = False
print("VERIFIED", ok)
'''


def _read_back_pairs(a: Answer) -> List[List[object]]:
    out = []
    for s in a.column1:
        try:
            out.append([s, rt._enc(rt.read(s))])
        except ReverseRefusal:
            continue
    return out


def render_script(a: Answer, root: str, certificate=None) -> str:
    data = {"read_back": _read_back_pairs(a),
            "certificate": a.certificate if certificate is None
            else certificate}
    return (_SCRIPT.replace("@@ROOT@@", repr(root))
            .replace("@@DATA@@", repr(json.dumps(data, sort_keys=True))))


def _case_certs(c):
    """Every case refutation certificate inside ``c``, in order."""
    out = []
    for key in ("inconsistent", "contradicts"):
        out += c.get(key) or []
    for x in c.get("entails") or []:
        out += x["cases"]
    for end in (c.get("lower"), c.get("upper")):
        if end:
            out += end["refuted"]
            for g in end["gaps"]:
                out += g["refuted"]
    return out


def _first_case_cert(c):
    """The first refutation certificate inside ``c``, or ``None``."""
    for key in ("inconsistent", "contradicts"):
        if c.get(key):
            return c[key][0]
    for x in c.get("entails") or []:
        if x["cases"]:
            return x["cases"][0]
    for end in (c.get("lower"), c.get("upper")):
        if end and end["refuted"]:
            return end["refuted"][0]
    return None


def _mutate(c):
    """A copy of certificate ``c`` that no longer proves its answer, or
    ``None``: a refutation loses the last step of its derivation (or its
    contradiction moves to a row that is not one), a witness moves off the
    integers, or a bound moves one step."""
    m = json.loads(json.dumps(c))
    omega = [x for x in _case_certs(m) if "omega" in x]
    if omega:                               # Phase 79: the Omega tree
        from . import integer_decision as idc
        omega[0]["omega"] = idc.mutate_node(omega[0]["omega"])
        return m
    if m["kind"] == "entails-int" and m["verdict"] == "INDEPENDENT":
        v = sorted(m["fails_at"])[0] if m["fails_at"] else None
        if v is None:
            return None
        n, d = map(int, m["fails_at"][v].split("/"))
        m["fails_at"][v] = f"{2 * n + d}/{2 * d}"
        return m
    if m["kind"] == "bounds-int" and m["verdict"] != "INCONSISTENT_PREMISES":
        end = m["lower"] or m["upper"]
        if end is None:                     # FREE: claim a bound instead
            m["answer"] = ["rel", ">=", ["var", m["var"]], ["lit", "0/1"]]
            return m
        end["bound"] += 1 if m["lower"] else -1
        return m
    cert = _first_case_cert(m)
    if cert is None:
        return None
    if cert["derivation"]:
        cert["derivation"].pop()
    elif cert["contradiction"] is not None:
        cert["contradiction"] = (cert["contradiction"] + 1) % max(
            1, len(_input_rows(tuple((op, rt._dec(a), rt._dec(b))
                                     for op, a, b in cert["rows"]))))
    return m


def mutated_script(a: Answer, root: str) -> Optional[str]:
    m = _mutate(a.certificate)
    if m is None or m == a.certificate:
        return None
    return render_script(a, root, m)


# ===========================================================================
# 5.  THE STUDY'S IN-PROCESS REPORT (X1, X2, X4, X5)
# ===========================================================================

def _brute(stmts, vs, box):
    pts = []
    for d in itertools.product(range(box[0], box[1] + 1), repeat=len(vs)):
        env = {v: Fraction(x) for v, x in zip(vs, d)}
        if all(rt.holds(s, env) for s in stmts):
            pts.append(env)
    return pts


def _box(vs, box) -> List[str]:
    return [f"{box[0]} <= {v} <= {box[1]}" for v in vs]


def battery(box=None) -> Dict[str, object]:
    """X4: every answered battery verdict and bound against enumeration of
    the box."""
    from ..evaluation import reverse_tct_int_cases as C
    box = box or C.BOX
    questions = []
    for atoms, vs in ((C.BATTERY_ATOMS_X, ["x"]),
                      (C.BATTERY_ATOMS_XY, ["x", "y"])):
        for p, q in itertools.permutations(atoms, 2):
            questions.append((vs, p, q))
    entail = {"questions": len(questions), "answered": 0, "undecided": 0,
              "disagree": [], "other_refusals": []}
    for vs, p, q in questions:
        ps = _box(vs, box) + [p]
        a = entails_int(ps, q)
        stmts = _parse_statements(ps)
        pts = _brute(stmts, vs, box)
        cs = _parse_statements([q])[0]
        if not pts:
            truth = "INCONSISTENT_PREMISES"
        else:
            h = [rt.holds(cs, e) for e in pts]
            truth = ("ENTAILS" if all(h) else
                     "CONTRADICTS" if not any(h) else "INDEPENDENT")
        if a.refusal == "INTEGER_UNDECIDED":
            entail["undecided"] += 1
            continue
        if a.refusal and a.refusal != "INCONSISTENT_PREMISES":
            entail["other_refusals"].append([p, q, a.refusal])
            continue
        entail["answered"] += 1
        if a.verdict != truth:
            entail["disagree"].append([p, q, a.verdict, truth])
    bnds = {"questions": 0, "answered": 0, "undecided": 0, "disagree": [],
            "other_refusals": []}
    for atoms, vs in ((C.BATTERY_ATOMS_X, ["x"]),
                      (C.BATTERY_ATOMS_XY, ["x", "y"])):
        for p in atoms:
            bnds["questions"] += 1
            ps = _box(vs, box) + [p]
            a = bounds_int("x", ps)
            pts = _brute(_parse_statements(ps), vs, box)
            if a.refusal == "INTEGER_UNDECIDED":
                bnds["undecided"] += 1
                continue
            if a.refusal and a.refusal != "INCONSISTENT_PREMISES":
                bnds["other_refusals"].append([p, a.refusal])
                continue
            bnds["answered"] += 1
            if not pts:
                truth = "INCONSISTENT_PREMISES"
            else:
                xs = [e["x"] for e in pts]
                lo, hi = min(xs), max(xs)
                truth = rt.realise(("rel", "=", ("var", "x"), ("lit", lo))
                                   if lo == hi else
                                   ("and", (("rel", ">=", ("var", "x"),
                                             ("lit", lo)),
                                            ("rel", "<=", ("var", "x"),
                                             ("lit", hi)))))
            got = a.refusal or a.sentence
            if got != truth:
                bnds["disagree"].append([p, got, truth])
    return {"entails": entail, "bounds": bnds}


def _verdict(a: Answer) -> str:
    return a.refusal or a.verdict


def int_report(with_battery: bool = True) -> Dict[str, object]:
    """X1, X2, X4 and X5 of ``studies/REVERSE_TCT_STUDY.md`` §10."""
    from ..evaluation import reverse_tct_int_cases as C
    ent = {"of": len(C.ENTAIL_CASES), "right": 0, "wrong": []}
    ctrl_e = {"of": len(C.ENTAIL_CASES), "not_polynomial": 0,
              "same": 0, "different": [], "other": []}
    for cid, ps, c, want in C.ENTAIL_CASES:
        got = _verdict(entails_int(list(ps), c))
        if got == want:
            ent["right"] += 1
        else:
            ent["wrong"].append([cid, got, want])
        q = _verdict(rt.entails(list(ps), c))
        if q == "NOT_POLYNOMIAL":
            ctrl_e["not_polynomial"] += 1
        elif q == want:
            ctrl_e["same"] += 1
        else:
            ctrl_e["different"].append([cid, q, want])
    bnd = {"of": len(C.BOUNDS_CASES), "right": 0, "wrong": []}
    ctrl_b = {"of": len(C.BOUNDS_CASES), "not_polynomial": 0, "same": 0,
              "different": []}
    for cid, v, ps, want in C.BOUNDS_CASES:
        a = bounds_int(v, list(ps))
        got = a.refusal or a.sentence
        if got == want:
            bnd["right"] += 1
        else:
            bnd["wrong"].append([cid, got, want])
        qa = rt.bounds(v, list(ps))
        q = qa.refusal or qa.sentence
        if q == "NOT_POLYNOMIAL":
            ctrl_b["not_polynomial"] += 1
        elif q == want:
            ctrl_b["same"] += 1
        else:
            ctrl_b["different"].append([cid, q, want])
    out = {"entails": ent, "bounds": bnd,
           "control": {"entails": ctrl_e, "bounds": ctrl_b}}
    if with_battery:
        out["battery"] = battery()
    return out


def declared_answers():
    """Every answered declared case, as ``(id, Answer)`` (for X3)."""
    from ..evaluation import reverse_tct_int_cases as C
    out = [(cid, entails_int(list(ps), c)) for cid, ps, c, _ in
           C.ENTAIL_CASES]
    out += [(cid, bounds_int(v, list(ps))) for cid, v, ps, _ in
            C.BOUNDS_CASES]
    return [(cid, a) for cid, a in out
            if a.answered or a.refusal == "INCONSISTENT_PREMISES"]
