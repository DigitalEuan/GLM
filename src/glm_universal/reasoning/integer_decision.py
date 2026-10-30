"""``glm_universal.reasoning.integer_decision`` -- the integer decision,
completed.

``studies/INTEGER_DECISION_STUDY.md`` (Phase 79).  Round three of Reverse
Three Column Thinking (``reverse_tct_int``) decides a case over ℤ by
elimination with rounding, which is sound and not complete; a case it can
neither refute nor witness was refused ``INTEGER_UNDECIDED``.  This module is
the Omega test behind that refusal: it decides every such case, returning an
integer point or a refutation tree whose every step a checker verifies by
arithmetic alone.

**Rows.**  A row is ``(coefficients, k)`` meaning ``sum(c*v) + k <= 0`` over
integer ``v``, with coprime integer coefficients (``tight``: divide by the
gcd, round the constant up -- exact over ℤ).

**The refutation tree.**  A node is ``{"steps": [...], "end": ...}``; the
steps act, in order, on the node's row list (the input rows, then every row a
step appends):

``["comb", i, a, j, b]``
    append ``tight(a*row_i + b*row_j)``, ``a, b`` positive integers;
``["subst", v, s, [[w, q], ...], q0]``
    replace ``v`` in every row by ``s + sum(q*w) + q0``, ``s`` a variable no
    row holds and no ``w`` equal to ``v`` or ``s`` -- a bijection of the
    integer points (``GLM.IntegerDecision.substitution_bijective``), so a
    refutation after it refutes before it.

The end is ``["contra", i]`` (row ``i`` has no variable and a positive
constant) or ``["split", i, K, children]``: row ``i`` reads ``s <= 0``, and
the ``K + 2`` children refute, on copies of the row list, ``s = 0``, ``s =
-1``, ..., ``s = -K`` (two rows each) and ``s <= -K - 1`` -- which together
cover every integer point the row allows (``GLM.IntegerDecision.split_cover``).

**The search** is the Omega test.  Equalities (a row and its opposite) are
solved exactly: a unit coefficient is eliminated by combination, otherwise
the floor-remainder substitution on the variable of smallest coefficient
shrinks the equation until one appears.  With no equality, a variable bounded
on one side only is dropped with its rows; a variable whose lower (or upper)
coefficients are all one is eliminated exactly
(``GLM.IntegerDecision.exact_shadow``); otherwise the real shadow is tried
(refuted: done), then the dark shadow (satisfied: an integer point exists,
``GLM.IntegerDecision.dark_shadow_gap``, and is built), and otherwise the
splinters -- the split above at each lower bound ``b*z >= beta`` with ``K =
floor((m*b - m - b)/m)``, ``m`` the largest upper coefficient -- and in the
last child every lower bound has moved past its splinters, so its real shadow
implies the dark shadow (``GLM.IntegerDecision.splinter_tail``) and is
refuted.

Exact throughout: ``int`` only.  A case that spends more than
:data:`NODE_LIMIT` search steps raises :class:`DecisionLimit`, which the
caller reports as ``INTEGER_UNDECIDED``.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["DecisionLimit", "NODE_LIMIT", "tight", "decide_rows",
           "check_node", "mutate_node", "node_size", "decision_report"]

#: Most search steps one case may spend (the declared limit of mark Z5).
NODE_LIMIT = 5000
#: Most rows one row list may hold.
ROW_LIMIT = 20000

Row = Tuple[Tuple[Tuple[str, int], ...], int]


class DecisionLimit(Exception):
    """The search spent more than :data:`NODE_LIMIT` steps on one case."""


# ===========================================================================
# 1.  ROWS
# ===========================================================================

def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def tight(co: Dict[str, int], k: int) -> Row:
    """``sum(co*v) + k <= 0`` as the equivalent row with coprime integer
    coefficients: divided by their gcd, the constant rounded up."""
    ic = {v: int(c) for v, c in co.items() if c}
    g = 0
    for c in ic.values():
        g = _gcd(g, c)
    k = int(k)
    if g > 1:
        ic = {v: c // g for v, c in ic.items()}
        k = -((-k) // g)
    return tuple(sorted(ic.items())), k


def _comb(r: Row, a: int, s: Row, b: int) -> Row:
    co: Dict[str, int] = {}
    for v, c in r[0]:
        co[v] = co.get(v, 0) + a * c
    for v, c in s[0]:
        co[v] = co.get(v, 0) + b * c
    return tight(co, a * r[1] + b * s[1])


def _subst(r: Row, v: str, s: str, qs: Sequence[Tuple[str, int]],
           q0: int) -> Row:
    co = dict(r[0])
    c = co.pop(v, 0)
    if not c:
        return r
    co[s] = co.get(s, 0) + c
    for w, q in qs:
        co[w] = co.get(w, 0) + c * q
    return tight(co, r[1] + c * q0)


def _coef(r: Row, v: str) -> int:
    for w, c in r[0]:
        if w == v:
            return c
    return 0


def _names(rows: Sequence[Row]) -> set:
    return {v for r in rows for v, _ in r[0]}


def _holds(r: Row, env: Dict[str, int]) -> bool:
    return sum(c * env.get(v, 0) for v, c in r[0]) + r[1] <= 0


# ===========================================================================
# 2.  THE SEARCH
# ===========================================================================

class _State:
    def __init__(self, taken: set):
        self.nodes = 0
        self.taken = set(taken)
        self.fresh = 0

    def tick(self) -> None:
        self.nodes += 1
        if self.nodes > NODE_LIMIT:
            raise DecisionLimit(f"more than {NODE_LIMIT} search steps")

    def new_name(self) -> str:
        while True:
            self.fresh += 1
            name = f"_s{self.fresh}"
            if name not in self.taken:
                self.taken.add(name)
                return name


def _pick(rows: Sequence[Row], z: str, env: Dict[str, int]) -> int:
    """An integer value of ``z`` satisfying every row in ``rows`` under
    ``env`` (every other variable of ``rows`` fixed first, 0 if unset)."""
    for r in rows:
        for v, _ in r[0]:
            if v != z:
                env.setdefault(v, 0)
    lo = hi = None
    for r in rows:
        c = _coef(r, z)
        rest = sum(cc * env[v] for v, cc in r[0] if v != z) + r[1]
        if c > 0:                                   # c*z <= -rest
            b = (-rest) // c
            hi = b if hi is None else min(hi, b)
        elif c < 0:                                 # (-c)*z >= rest
            b = -((-rest) // (-c))
            lo = b if lo is None else max(lo, b)
    if lo is not None and hi is not None and lo > hi:
        raise AssertionError("an elimination left no integer for " + z)
    return lo if lo is not None else (hi if hi is not None else 0)


def _solve(rows: List[Row], active: List[int], st: _State):
    """Decide the rows ``active`` of ``rows`` (appending to ``rows``).
    ``("unsat", node)`` or ``("sat", env)``."""
    st.tick()
    steps: List[list] = []

    def add(r: Row, step: list) -> int:
        rows.append(r)
        steps.append(step)
        if len(rows) > ROW_LIMIT:
            raise DecisionLimit("the row list grew past its limit")
        return len(rows) - 1

    def done(node):
        return "unsat", {"steps": steps + node["steps"], "end": node["end"]}

    # constant rows; the strongest row of each coefficient vector
    best: Dict[tuple, int] = {}
    for i in active:
        co, k = rows[i]
        if not co:
            if k > 0:
                return "unsat", {"steps": steps, "end": ["contra", i]}
            continue
        j = best.get(co)
        if j is None or rows[j][1] < k:
            best[co] = i
    active = sorted(best.values())
    if not active:
        return "sat", {}

    # opposite pairs: a contradiction, or an equality
    eq = None
    for i in active:
        co, k = rows[i]
        opp = tuple((v, -c) for v, c in co)
        j = best.get(opp)
        if j is None:
            continue
        if k + rows[j][1] > 0:
            idx = add(_comb(rows[i], 1, rows[j], 1), ["comb", i, 1, j, 1])
            return "unsat", {"steps": steps, "end": ["contra", idx]}
        if k + rows[j][1] < 0:
            continue
        unit = any(abs(c) == 1 for _, c in co)
        if eq is None or (unit and not eq[2]):
            eq = (i, j, unit)

    if eq is not None:
        i, j, unit = eq
        co = dict(rows[i][0])
        if unit:
            v = min((w for w, c in co.items() if abs(c) == 1))
            ci = co[v]
            new: List[int] = []
            for m in active:
                if m in (i, j):
                    continue
                cm = _coef(rows[m], v)
                if not cm:
                    new.append(m)
                    continue
                other = j if (cm > 0) == (ci > 0) else i
                new.append(add(_comb(rows[m], 1, rows[other], abs(cm)),
                               ["comb", m, 1, other, abs(cm)]))
            status, got = _solve(rows, new, st)
            if status == "unsat":
                return done(got)
            env = dict(got)
            for w, _ in rows[i][0]:
                if w != v:
                    env.setdefault(w, 0)
            rest = sum(c * env[w] for w, c in rows[i][0] if w != v) \
                + rows[i][1]
            env[v] = -rest * ci                     # ci is +1 or -1
            return "sat", env
        # floor-remainder substitution on the smallest coefficient
        v = min(co, key=lambda w: (abs(co[w]), w))
        a = co[v]
        s = st.new_name()
        qs = [[w, -(c // a)] for w, c in sorted(co.items()) if w != v]
        qs = [q for q in qs if q[1]]
        q0 = -(rows[i][1] // a)
        for n in range(len(rows)):
            rows[n] = _subst(rows[n], v, s, qs, q0)
        steps.append(["subst", v, s, qs, q0])
        status, got = _solve(rows, active, st)
        if status == "unsat":
            return done(got)
        env = dict(got)
        env.setdefault(s, 0)
        for w, _ in qs:
            env.setdefault(w, 0)
        env[v] = env[s] + sum(q * env[w] for w, q in qs) + q0
        return "sat", env

    names = sorted(_names([rows[i] for i in active]))
    info = {}
    for z in names:
        ups = [i for i in active if _coef(rows[i], z) > 0]
        los = [i for i in active if _coef(rows[i], z) < 0]
        info[z] = (ups, los)

    # a variable bounded on one side only: drop it with its rows
    for z in names:
        ups, los = info[z]
        if not ups or not los:
            mine = ups + los
            status, got = _solve(rows, [i for i in active if i not in mine],
                                 st)
            if status == "unsat":
                return done(got)
            env = dict(got)
            env[z] = _pick([rows[i] for i in mine], z, env)
            return "sat", env

    def exact(z):
        ups, los = info[z]
        return (all(_coef(rows[i], z) == 1 for i in ups)
                or all(_coef(rows[i], z) == -1 for i in los))

    def cost(z):
        ups, los = info[z]
        return (0 if exact(z) else 1, len(ups) * len(los),
                max(abs(_coef(rows[i], z)) for i in ups + los), z)

    z = min(names, key=cost)
    ups, los = info[z]
    rest = [i for i in active if not _coef(rows[i], z)]

    def shadow(rs: List[Row], sts: List[list], act: List[int],
               lower: List[int]) -> List[int]:
        out = list(act)
        for p in ups:
            for q in lower:
                cp, cq = _coef(rs[p], z), -_coef(rs[q], z)
                g = _gcd(cp, cq)
                rs.append(_comb(rs[p], cq // g, rs[q], cp // g))
                sts.append(["comb", p, cq // g, q, cp // g])
                out.append(len(rs) - 1)
        if len(rs) > ROW_LIMIT:
            raise DecisionLimit("the row list grew past its limit")
        return out

    if exact(z):
        new = shadow(rows, steps, rest, los)
        status, got = _solve(rows, new, st)
        if status == "unsat":
            return done(got)
        env = dict(got)
        env[z] = _pick([rows[i] for i in ups + los], z, env)
        return "sat", env

    # the real shadow, on a copy: refuted means refuted
    rrows, rsteps = list(rows), []
    new = shadow(rrows, rsteps, rest, los)
    status, got = _solve(rrows, new, st)
    if status == "unsat":
        return "unsat", {"steps": steps + rsteps + got["steps"],
                         "end": got["end"]}

    # the dark shadow, on a copy: satisfied means an integer point
    drows = list(rows)
    dark = list(rest)
    for p in ups:
        for q in los:
            a, b = _coef(rows[p], z), -_coef(rows[q], z)
            co: Dict[str, int] = {}
            for v, c in rows[p][0]:
                co[v] = co.get(v, 0) + b * c
            for v, c in rows[q][0]:
                co[v] = co.get(v, 0) + a * c
            drows.append(tight(co, b * rows[p][1] + a * rows[q][1]
                               + (a - 1) * (b - 1)))
            dark.append(len(drows) - 1)
    status, got = _solve(drows, dark, st)
    if status == "sat":
        env = dict(got)
        env[z] = _pick([rows[i] for i in ups + los], z, env)
        return "sat", env

    # the splinters
    m = max(_coef(rows[p], z) for p in ups)

    def chain(crows: List[Row], cact: List[int], lower: List[int], j: int):
        if j == len(los):
            tsteps: List[list] = []
            new = shadow(crows, tsteps, [i for i in cact
                                         if not _coef(crows[i], z)], lower)
            status, got = _solve(crows, new, st)
            if status == "sat":
                raise AssertionError("the last splinter's shadow is "
                                     "satisfiable although the dark shadow "
                                     "is not")
            return "unsat", {"steps": tsteps + got["steps"],
                             "end": got["end"]}
        q = los[j]
        b = -_coef(crows[q], z)
        K = (m * b - m - b) // m
        if K < 0:
            return chain(crows, cact, lower, j + 1)
        co, k = crows[q]
        kids = []
        for i in range(K + 1):
            st.tick()
            krows = list(crows)
            krows.append(tight(dict(co), k + i))
            krows.append(tight({v: -c for v, c in co}, -(k + i)))
            n = len(krows)
            status, got = _solve(krows, cact + [n - 2, n - 1], st)
            if status == "sat":
                return "sat", got
            kids.append(got)
        trows = list(crows)
        trows.append(tight(dict(co), k + K + 1))
        n = len(trows) - 1
        status, got = chain(trows, cact + [n], lower + [n], j + 1)
        if status == "sat":
            return "sat", got
        kids.append(got)
        return "unsat", {"steps": [], "end": ["split", q, K, kids]}

    status, got = chain(list(rows), list(active), list(los), 0)
    if status == "sat":
        return "sat", got
    return done(got)


def decide_rows(rows: Sequence[Row]):
    """Decide the rows over ℤ.  ``("unsat", node)`` -- a refutation tree over
    ``rows`` -- or ``("sat", env)``, an integer point satisfying every row
    (checked here).  Raises :class:`DecisionLimit` past the declared limit."""
    work = [tuple(r) for r in rows]
    if work != [tight(dict(r[0]), r[1]) for r in work]:
        raise ValueError("decide_rows takes tightened rows")
    st = _State(_names(work))
    status, got = _solve(list(work), list(range(len(work))), st)
    if status == "sat":
        env = {v: got.get(v, 0) for v in sorted(_names(work))}
        if not all(_holds(r, env) for r in work):
            raise AssertionError("the decision's point fails a row")
        return "sat", env
    if not check_node(work, got):
        raise AssertionError("the decision's refutation does not check")
    return "unsat", got


# ===========================================================================
# 3.  THE CHECKER (the script in reverse_tct_int carries a copy)
# ===========================================================================

def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def check_node(rows: Sequence[Row], node) -> bool:
    """Does ``node`` refute ``rows``?  Arithmetic only."""
    try:
        return _check(list(rows), node)
    except (AssertionError, KeyError, IndexError, TypeError, ValueError):
        return False


def _check(rows: List[Row], node) -> bool:
    for step in node["steps"]:
        if step[0] == "comb":
            _, i, a, j, b = step
            assert all(_is_int(x) for x in (i, a, j, b))
            assert a > 0 and b > 0 and 0 <= i < len(rows) \
                and 0 <= j < len(rows)
            rows.append(_comb(rows[i], a, rows[j], b))
        elif step[0] == "subst":
            _, v, s, qs, q0 = step
            names = _names(rows)
            assert isinstance(v, str) and isinstance(s, str) and v != s
            assert s not in names and _is_int(q0)
            for w, q in qs:
                assert isinstance(w, str) and w not in (v, s) and _is_int(q)
            rows = [_subst(r, v, s, [tuple(x) for x in qs], q0)
                    for r in rows]
        else:
            return False
    end = node["end"]
    if end[0] == "contra":
        i = end[1]
        assert _is_int(i) and 0 <= i < len(rows)
        return not rows[i][0] and rows[i][1] > 0
    if end[0] == "split":
        _, i, K, kids = end
        assert _is_int(i) and 0 <= i < len(rows) and _is_int(K) and K >= 0
        if len(kids) != K + 2:
            return False
        co, k = rows[i]
        for n in range(K + 1):
            extra = [tight(dict(co), k + n),
                     tight({v: -c for v, c in co}, -(k + n))]
            if not _check(rows + extra, kids[n]):
                return False
        return _check(rows + [tight(dict(co), k + K + 1)], kids[K + 1])
    return False


def node_size(node) -> Tuple[int, int]:
    """``(steps, splits)`` over the whole tree."""
    steps, splits = len(node["steps"]), 0
    if node["end"][0] == "split":
        splits += 1
        for kid in node["end"][3]:
            s, p = node_size(kid)
            steps += s
            splits += p
    return steps, splits


def _copy_tree(x):
    """A deep copy of a refutation tree: dicts, lists and tuples rebuilt,
    ints and fractions shared (they are immutable)."""
    if isinstance(x, dict):
        return {k: _copy_tree(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_copy_tree(v) for v in x]
    if isinstance(x, tuple):
        return tuple(_copy_tree(v) for v in x)
    return x


def mutate_node(node):
    """A copy of ``node`` that no longer refutes: the first split loses its
    last child, or else the last step goes, or else the contradiction moves
    to the row after it."""
    m = _copy_tree(node)
    queue = [m]
    while queue:
        n = queue.pop(0)
        if n["end"][0] == "split":
            n["end"][3].pop()
            return m
    if m["steps"]:
        m["steps"].pop()
        return m
    m["end"][1] += 1
    return m


# ===========================================================================
# 4.  THE STUDY'S REPORT
# ===========================================================================

def decision_answers():
    """The declared corpus (mark Z2), answered: ``(id, Answer, declared)``
    for every question of ``evaluation/integer_decision_cases.py``."""
    from ..evaluation import integer_decision_cases as C
    from . import reverse_tct_int as ri
    out = []
    for cid, ps, box, concl, want in C.ENTAIL_CASES:
        out.append((cid, ri.entails_int(list(C.boxed_premises(ps, box)),
                                        concl), want))
    for cid, ps, box, want in C.BOUNDS_CASES:
        out.append((cid, ri.bounds_int("x", list(C.boxed_premises(ps, box))),
                    want))
    return out


def _said(a) -> str:
    if a.refusal:
        return a.refusal
    return a.sentence if a.operation == "bounds-int" else a.verdict


def _enumerate(premises, conclusion, variables, box):
    """The truth of a boxed question by enumeration of the box: the
    ``entails`` verdict and the ``bounds`` answer of ``x``."""
    import itertools
    from fractions import Fraction
    from . import reverse_tct as rt
    ps = [rt.parse_any(p)[0] for p in premises]
    c = rt.parse_any(conclusion)[0]
    lo, hi = box
    points, xs = [], []
    for d in itertools.product(range(lo, hi + 1), repeat=len(variables)):
        env = {v: Fraction(x) for v, x in zip(variables, d)}
        if all(rt.holds(s, env) for s in ps):
            points.append(rt.holds(c, env))
            xs.append(env["x"])
    if not points:
        return "INCONSISTENT_PREMISES", "INCONSISTENT_PREMISES"
    verdict = ("ENTAILS" if all(points) else
               "CONTRADICTS" if not any(points) else "INDEPENDENT")
    return verdict, (int(min(xs)), int(max(xs)))


def _bounds_read(a):
    """The integer bounds a ``bounds-int`` answer claims, or its refusal."""
    if a.refusal:
        return a.refusal
    c = a.certificate
    lo = c["lower"]["bound"] if c.get("lower") else None
    hi = c["upper"]["bound"] if c.get("upper") else None
    return (lo, hi)


def _certs(c):
    from . import reverse_tct_int as ri
    return ri._case_certs(c)


def battery_report(complete: bool = True) -> Dict[str, object]:
    """Mark Z3: the declared battery against enumeration of the box, with
    the complete decision on (``complete``) or off (round three)."""
    from ..evaluation import integer_decision_cases as C
    from . import reverse_tct_int as ri
    saved = ri.COMPLETE
    ri.COMPLETE = complete
    try:
        out = {"entails": {"questions": 0, "agree": 0, "disagree": [],
                           "undecided": 0, "omega": 0},
               "bounds": {"questions": 0, "agree": 0, "disagree": [],
                          "undecided": 0, "omega": 0}}
        for qid, vs, ps, concl in C.battery_questions():
            verdict, span = _enumerate(ps, concl, vs, C.BATTERY["box"])
            for key, a, want in (
                    ("entails", ri.entails_int(list(ps), concl), verdict),
                    ("bounds", ri.bounds_int("x", list(ps)), span)):
                row = out[key]
                row["questions"] += 1
                got = _said(a) if key == "entails" else _bounds_read(a)
                if got == "INTEGER_UNDECIDED":
                    row["undecided"] += 1
                elif got == want:
                    row["agree"] += 1
                else:
                    row["disagree"].append([qid, str(got), str(want)])
                if any("omega" in x for x in _certs(a.certificate or {})):
                    row["omega"] += 1
        return out
    finally:
        ri.COMPLETE = saved


def decision_report(with_battery: bool = True) -> Dict[str, object]:
    """Marks Z1, Z2, Z3 and Z5 of ``studies/INTEGER_DECISION_STUDY.md``,
    recomputed in process (Z4, the fresh-interpreter scripts, is
    ``tools integer-decision``; Z6 is the Lean file)."""
    from ..evaluation import integer_decision_cases as C
    from . import reverse_tct_int as ri
    # Z1: round three's declared corpus, answered as declared, with no Omega
    # tree anywhere in its certificates
    three = ri.int_report(with_battery=with_battery)
    omega_in_three = 0
    for _, a in ri.declared_answers():
        if any("omega" in x for x in _certs(a.certificate or {})):
            omega_in_three += 1
    z1 = {"entails_right": three["entails"]["right"],
          "entails_of": three["entails"]["of"],
          "bounds_right": three["bounds"]["right"],
          "bounds_of": three["bounds"]["of"],
          "omega_certificates": omega_in_three}
    if with_battery:
        b = three["battery"]
        z1["x4_disagree"] = (len(b["entails"]["disagree"])
                             + len(b["bounds"]["disagree"]))
        z1["x4_questions"] = (b["entails"]["questions"]
                              + b["bounds"]["questions"])
    # Z2: the declared corpus; the control is round three
    right, wrong, refused, rows = 0, [], [], []
    before = 0
    saved = ri.COMPLETE
    for cid, a, want in decision_answers():
        got = _said(a)
        steps = splits = 0
        for x in _certs(a.certificate or {}):
            if "omega" in x:
                s, p = node_size(x["omega"])
                steps += s
                splits += p
        rows.append({"id": cid, "answer": got, "declared": want,
                     "omega_steps": steps, "splits": splits})
        if got == want:
            right += 1
        elif a.refusal:
            refused.append(cid)
        else:
            wrong.append(cid)
    try:
        ri.COMPLETE = False
        for cid, ps, box, concl, _ in C.ENTAIL_CASES:
            if _said(ri.entails_int(list(C.boxed_premises(ps, box)),
                                    concl)) == "INTEGER_UNDECIDED":
                before += 1
        for cid, ps, box, _ in C.BOUNDS_CASES:
            if _said(ri.bounds_int("x", list(C.boxed_premises(ps, box)))) \
                    == "INTEGER_UNDECIDED":
                before += 1
    finally:
        ri.COMPLETE = saved
    z2 = {"of": len(rows), "right": right, "wrong": wrong,
          "refused": refused, "undecided_before": before, "rows": rows}
    out = {"Z1": z1, "Z2": z2,
           "Z5": {"node_limit": NODE_LIMIT,
                  "declared_limit": C.NODE_LIMIT}}
    if with_battery:
        now = battery_report(True)
        then = battery_report(False)
        out["Z3"] = {"now": now, "round_three": then}
        out["Z5"]["undecided_now"] = (now["entails"]["undecided"]
                                      + now["bounds"]["undecided"])
    return out
