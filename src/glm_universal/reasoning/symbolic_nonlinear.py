"""``glm_universal.reasoning.symbolic_nonlinear`` -- systems in letters that
substitution cannot isolate (Phase 103,
``studies/NONLINEAR_ELIMINATION_STUDY.md``).

Why it exists
-------------
Phase 98's solver (:func:`glm_universal.reasoning.symbolic.solve_system`)
eliminates an unknown only where it appears alone, in one power, with a
coefficient free of every other unknown.  Anything else -- a product of two
unknowns, a quadratic with a linear term, two conics -- is refused
``NONLINEAR``, even when the system has a closed answer.  This module is the
next layer: it runs **only** on that refusal, so every answer Phase 98 gave
is unchanged.

What it does
------------
The working state is a list of polynomial equations, the values found so far,
and the **generators**: named square roots ``sqrt(R)`` (or a constant radical)
with the relation ``sqrt(R)^2 = R``.  Every value is kept with a denominator
free of generators (conjugates are multiplied through).  One action is taken
at a time, in this order:

1. **isolate** an unknown that appears in the first power with a coefficient
   free of unknowns (the coefficient may hold a generator);
2. **solve** an equation left in one unknown: strip its content, split off
   the root ``0``, take the squarefree part, split off rational roots when the
   coefficients are numbers, and solve what is left if it is linear or
   quadratic -- a quadratic with a square discriminant gives two rational
   **branches**, otherwise one branch with a new generator (its conjugate is
   the other).  A higher degree is refused ``NONLINEAR``; a quadratic with a
   negative constant discriminant has no real root;
3. **split** on a coefficient ``A`` that holds other unknowns: either
   ``A != 0`` and the unknown is isolated, or ``A = 0`` and the rest of the
   equation vanishes too -- both cases are followed;
4. **eliminate** an unknown between two equations by their **resultant**
   (Sylvester's determinant, by fraction-free elimination), keeping one of
   the two.

Every branch that survives is then **verified**: each original equation, with
every value substituted and every generator reduced, must vanish
identically.  A branch that fails (a resultant's extraneous pair, a root of a
discarded factor) is dropped, and the drop is counted.  The conjugate of a
branch -- every generator's sign flipped -- is a branch too, because the
derivation is an identity in the generators.

No float is used anywhere, and nothing is looked up.
``RequestProject/GLM/NonlinearElimination.lean`` proves what the layer rests
on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import product
from math import gcd
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import routes as R
from . import symbolic as S
from . import symbolic_algebraic as A
from .symbolic import RF, Poly, Solution, SymbolicError

__all__ = ["resultant", "poly_sqrt", "solve_nonlinear", "Branches",
           "ExtInfo", "approximate", "branch_script", "MAX_BRANCHES",
           "MAX_RESULTANTS", "modes_radical_reason"]

#: More solutions than this and the layer refuses (``NONLINEAR``).
MAX_BRANCHES = 16
#: Resultant eliminations allowed on one branch.
MAX_RESULTANTS = 6
#: Case splits on a coefficient that holds unknowns, on one branch.
MAX_SPLITS = 6


# ===========================================================================
# 1.  RESULTANT, SQUARE ROOT, RATIONAL ROOTS
# ===========================================================================

def resultant(p: Poly, q: Poly, x: str) -> Poly:
    """``Res_x(p, q)``: the determinant of the Sylvester matrix of ``p`` and
    ``q`` as polynomials in ``x`` (both of positive degree)."""
    m, n = p.deg(x), q.deg(x)
    if m == 0 or n == 0:
        raise ValueError("resultant needs both polynomials to hold x")
    pc, qc = p.coeffs(x), q.coeffs(x)
    a = [pc.get(m - i, Poly()) for i in range(m + 1)]
    b = [qc.get(n - i, Poly()) for i in range(n + 1)]
    size = m + n
    rows: List[List[Poly]] = []
    for i in range(n):
        row = [Poly() for _ in range(size)]
        for j, c in enumerate(a):
            row[i + j] = c
        rows.append(row)
    for i in range(m):
        row = [Poly() for _ in range(size)]
        for j, c in enumerate(b):
            row[i + j] = c
        rows.append(row)
    return S._bareiss_det(rows)


def _grlex(vs: Sequence[str]):
    def key(m):
        d = dict(m)
        return (sum(d.values()), tuple(d.get(v, 0) for v in vs))
    return key


def poly_sqrt(p: Poly) -> Optional[Poly]:
    """``r`` with ``r * r == p`` exactly, or ``None``.  Term by term in the
    graded lexicographic order: the leading term of ``p - r_k^2`` is twice
    the root's leading term times its next term."""
    if p.is_zero():
        return Poly()
    key = _grlex(sorted(p.vars()))
    m, c = max(p.t.items(), key=lambda kv: key(kv[0]))
    if any(e % 2 for _, e in m):
        return None
    rc = S.rational_root(c, 2) if c > 0 else None
    if rc is None:
        return None
    lm = tuple((v, e // 2) for v, e in m)
    root = Poly({lm: rc})
    low = min(sum(e for _, e in mm) for mm in p.t)
    for _ in range(4 * len(p.t) + 8):
        rem = p - root * root
        if rem.is_zero():
            return root
        mr, cr = max(rem.t.items(), key=lambda kv: key(kv[0]))
        d = dict(mr)
        for v, e in lm:
            d[v] = d.get(v, 0) - e
            if d[v] < 0:
                return None
        mono = tuple(sorted((v, e) for v, e in d.items() if e))
        if key(mono) >= key(lm) or 2 * sum(e for _, e in mono) < low:
            return None
        root = root + Poly({mono: cr / (2 * rc)})
    return None


def _divisors(n: int) -> List[int]:
    n = abs(n)
    out = [1]
    for pr, e in S._factor_int(n).items() if n > 1 else []:
        out = [d * pr ** k for d in out for k in range(e + 1)]
    return out


def _rational_root(p: Poly, u: str) -> Optional[Fraction]:
    """A rational root of ``p``, a polynomial in ``u`` alone with rational
    coefficients (the rational root theorem on its integral multiple)."""
    cs = p.coeffs(u)
    den = 1
    for c in cs.values():
        q = c.const_value()
        den = den * q.denominator // gcd(den, q.denominator)
    ints = {e: int(c.const_value() * den) for e, c in cs.items()}
    lead, const = ints[max(ints)], ints.get(0, 0)
    if const == 0:
        return Fraction(0)
    for a in _divisors(const):
        for b in _divisors(lead):
            for r in (Fraction(a, b), Fraction(-a, b)):
                if sum(c * r ** e for e, c in ints.items()) == 0:
                    return r
    return None


# ===========================================================================
# 2.  GENERATORS: REDUCTION, CONJUGATES AND INVERSES
# ===========================================================================
#
# A branch carries two kinds of generator.  A **root generator** ``g`` has
# the relation ``g^k = rels[g]`` (``k = kdeg.get(g, 2)``: a square root, or a
# cube root for Cardano's formula); its radicand may hold another generator
# (a tower, Phase 104).  An **algebraic number** (``algs``, Phase 104) is the
# root of a monic irreducible polynomial over the rationals in an isolating
# interval, and reduces modulo that polynomial.  Phase 103's branches carry
# only square roots of radicands free of generators, and for them every
# function below does exactly what it did then.

@dataclass
class _Alg:
    """A real algebraic number: the root of the monic irreducible ``m``
    (coefficients from the constant term up, degree at least 3) in the
    interval ``(lo, hi)``, which holds no other root of ``m``."""

    m: List[Fraction]
    lo: Fraction
    hi: Fraction


def _gen_names(st) -> set:
    return set(st.rels) | set(st.algs)


def _alg_reduce(p: Poly, g: str, a: _Alg) -> Poly:
    """``p`` with every power of ``g`` at or above ``deg m`` reduced modulo
    ``m``."""
    cs = p.coeffs(g)
    pw = A.powers_mod(a.m, max(cs))
    out = Poly()
    for e, c in cs.items():
        for i, t in enumerate(pw[e]):
            if t:
                out = out + c * Poly.var(g, i).scale(t)
    return out


def _reduce(p: Poly, st) -> Poly:
    """``p`` with every generator's relation applied until none applies: a
    root generator's ``k``-th power replaced by its radicand, an algebraic
    number reduced modulo its polynomial."""
    for _ in range(512):
        changed = False
        for g, d in st.rels.items():
            k = st.kdeg.get(g, 2)
            if g in p.vars() and p.deg(g) >= k:
                r = p.reduce_power(g, k, RF(d))
                p = r.num.scale(1 / r.den.const_value())
                changed = True
        for g, a in st.algs.items():
            if g in p.vars() and p.deg(g) >= len(a.m) - 1:
                p = _alg_reduce(p, g, a)
                changed = True
        if not changed:
            return p
    raise SymbolicError("NONLINEAR", "the relations of the generators do not "
                                     "reduce")


def _depth(st) -> Dict[str, int]:
    depth: Dict[str, int] = {}

    def dep(g: str, trail: Tuple[str, ...] = ()) -> int:
        if g in depth:
            return depth[g]
        if g in st.algs or g in trail:
            depth[g] = 0
            return 0
        inner = [h for h in st.rels[g].vars()
                 if h != g and (h in st.rels or h in st.algs)]
        depth[g] = 1 + max((dep(h, trail + (g,)) for h in inner), default=-1)
        return depth[g]

    for g in list(st.rels) + list(st.algs):
        dep(g)
    return depth


def _order(st) -> List[str]:
    """Every generator, a generator whose relation holds another before it
    (a tower is taken apart from the top); otherwise in the order made."""
    d = _depth(st)
    return sorted(list(st.rels) + list(st.algs), key=lambda g: -d[g])


def _flip(p: Poly, g: str) -> Poly:
    return Poly({m: (-c if dict(m).get(g, 0) % 2 else c)
                 for m, c in p.t.items()})


def _norm(v: RF, st) -> RF:
    return _rationalise(v, st)


def _is_zero(v: RF, st) -> bool:
    return _reduce(v.num, st).is_zero()


def _udivmod(a: Dict[int, RF], b: Dict[int, RF], st
             ) -> Tuple[Dict[int, RF], Dict[int, RF]]:
    """Division of polynomials in one letter whose coefficients lie in the
    field the other generators make."""
    a = dict(a)
    q: Dict[int, RF] = {}
    db = max(b)
    inv = _norm(RF(Poly.const(1)) / b[db], st)
    while a and max(a) >= db:
        da = max(a)
        c = _norm(a[da] * inv, st)
        q[da - db] = c
        for e, be in b.items():
            v = _norm(a.get(e + da - db, RF(Poly())) - c * be, st)
            if _is_zero(v, st):
                a.pop(e + da - db, None)
            else:
                a[e + da - db] = v
        a.pop(da, None)
    return q, a


def _umul(a: Dict[int, RF], b: Dict[int, RF], st) -> Dict[int, RF]:
    out: Dict[int, RF] = {}
    for i, x in a.items():
        for j, y in b.items():
            out[i + j] = out.get(i + j, RF(Poly())) + x * y
    return {e: _norm(v, st) for e, v in out.items() if not _is_zero(v, st)}


def _usub(a: Dict[int, RF], b: Dict[int, RF], st) -> Dict[int, RF]:
    out = dict(a)
    for e, v in b.items():
        out[e] = out.get(e, RF(Poly())) - v
    return {e: _norm(v, st) for e, v in out.items() if not _is_zero(v, st)}


def _inverse(den: Poly, g: str, st) -> RF:
    """``1/den`` with ``g`` (an algebraic number or a cube root) cleared
    from the denominator: the extended Euclidean algorithm modulo ``g``'s
    relation, over the field of the generators below it."""
    if g in st.algs:
        mod = {i: RF(Poly.const(c)) for i, c in enumerate(st.algs[g].m) if c}
    else:
        # g^k - R, R in lower powers of g (Phase 108: a Viete root's
        # relation holds g itself; for every earlier generator R is free of
        # g and this is {k: 1, 0: -R} as before)
        mod = {st.kdeg[g]: RF(Poly.const(1))}
        for e, c in st.rels[g].coeffs(g).items():
            mod[e] = mod.get(e, RF(Poly())) - RF(c)
        mod = {e: c for e, c in mod.items() if not c.is_zero()}
    r0, t0 = mod, {}
    r1 = {e: RF(c) for e, c in den.coeffs(g).items()}
    t1 = {0: RF(Poly.const(1))}
    while max(r1) > 0:
        q, r = _udivmod(r0, r1, st)
        if not r:
            raise SymbolicError("NONLINEAR", f"the relation of {g} is "
                                             f"reducible")
        r0, r1 = r1, r
        t0, t1 = t1, _usub(t0, _umul(q, t1, st), st)
    inv_c = _norm(RF(Poly.const(1)) / r1[0], st)
    out = RF(Poly())
    for e, c in t1.items():
        out = out + c * RF(Poly.var(g, e))
    return out * inv_c


def _rationalise(v: RF, st) -> RF:
    """The same value with a denominator free of every generator: a square
    root by its conjugate, an algebraic number or a cube root by its
    inverse, from the top of a tower down."""
    num, den = _reduce(v.num, st), _reduce(v.den, st)
    for g in _order(st):
        if g not in den.vars():
            continue
        if g in st.algs or st.kdeg.get(g, 2) != 2:
            w = RF(num) * _inverse(den, g, st)
            num, den = _reduce(w.num, st), _reduce(w.den, st)
        else:
            conj = _flip(den, g)
            num, den = _reduce(num * conj, st), _reduce(den * conj, st)
    return RF(num, den)


def _subs(v: RF, u: str, val: RF, st) -> RF:
    if u not in v.vars():
        return v
    return _rationalise(v.num.subs_power(u, 1, val) /
                        v.den.subs_power(u, 1, val), st)


def _flip_rf(v: RF, g: str) -> RF:
    return RF(_flip(v.num, g), _flip(v.den, g))


def _square_part(d: Poly) -> Tuple[RF, Poly]:
    """``(outer, R)`` with ``d = outer^2 * R`` up to the sign of ``outer``:
    the square part of the rational content and the even powers of the
    monomial content pulled out, ``R`` primitive with integer coefficients."""
    c = d.content()
    q = d.scale(1 / c)
    so = si = 1
    for pr, e in S._factor_int(c.numerator).items() if c.numerator > 1 \
            else []:
        so *= pr ** (e // 2)
        si *= pr ** (e % 2)
    sd = rd = 1
    for pr, e in S._factor_int(c.denominator).items() \
            if c.denominator > 1 else []:
        sd *= pr ** (e // 2)
        rd *= pr ** (e % 2)
    # c = (so / sd)^2 * si / rd and sqrt(si / rd) = sqrt(si * rd) / rd
    outer = RF(Poly.const(Fraction(so, sd * rd)))
    inner = Fraction(si * rd)
    mc = q.monomial_content()
    half = tuple((v, e // 2) for v, e in mc if e // 2)
    if half:
        hm = Poly({half: Fraction(1)})
        q = S.divide_exact(q, hm * hm)
        outer = outer * RF(hm)
    return outer, q.scale(inner)


# ===========================================================================
# 3.  THE WORKING STATE
# ===========================================================================

@dataclass
class _State:
    polys: List[Tuple[int, Poly]]
    values: Dict[str, RF] = field(default_factory=dict)
    rels: Dict[str, Poly] = field(default_factory=dict)
    conds: List[RF] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    resultants: int = 0
    splits: int = 0
    # Phase 104: the additions are on only when ``ext`` is
    ext: bool = False
    kdeg: Dict[str, int] = field(default_factory=dict)
    algs: Dict[str, _Alg] = field(default_factory=dict)
    fixed: set = field(default_factory=set)
    ineqs: List[str] = field(default_factory=list)
    origs: List[Tuple[int, Poly]] = field(default_factory=list)
    # Phase 108: the trigonometric (Viete) roots, name -> (k, M)
    trig: Dict[str, Tuple[int, Poly]] = field(default_factory=dict)

    def copy(self) -> "_State":
        return _State(list(self.polys), dict(self.values), dict(self.rels),
                      list(self.conds), list(self.steps), self.resultants,
                      self.splits, self.ext, dict(self.kdeg),
                      dict(self.algs), set(self.fixed), list(self.ineqs),
                      self.origs, dict(self.trig))


@dataclass
class _New:
    """The generators a root brings with it."""

    rels: Dict[str, Poly] = field(default_factory=dict)
    kdeg: Dict[str, int] = field(default_factory=dict)
    algs: Dict[str, _Alg] = field(default_factory=dict)
    fixed: set = field(default_factory=set)
    ineqs: List[str] = field(default_factory=list)
    note: str = ""
    trig: Dict[str, Tuple[int, Poly]] = field(default_factory=dict)

    def merge(self, o: "_New") -> "_New":
        return _New({**self.rels, **o.rels}, {**self.kdeg, **o.kdeg},
                    {**self.algs, **o.algs}, self.fixed | o.fixed,
                    self.ineqs + [i for i in o.ineqs if i not in self.ineqs],
                    "; ".join(n for n in (self.note, o.note) if n),
                    {**self.trig, **o.trig})

    def empty(self) -> bool:
        return not (self.rels or self.algs)


def _absorb(st: _State, new: _New) -> None:
    st.rels.update(new.rels)
    st.kdeg.update(new.kdeg)
    st.algs.update(new.algs)
    st.fixed |= new.fixed
    st.ineqs.extend(i for i in new.ineqs if i not in st.ineqs)
    st.trig.update(new.trig)


def _with(st: _State, new: _New) -> _State:
    s2 = st.copy()
    _absorb(s2, new)
    return s2


def _primitive(p: Poly, unknowns: set, st: _State) -> Poly:
    """Drop the rational content and any factor free of unknowns and
    generators (recorded as a nonzero condition)."""
    if p.is_zero():
        return p
    p = p.scale(1 / p.content())
    groups: Dict[tuple, Dict] = {}
    for m, c in p.t.items():
        key = tuple((v, e) for v, e in m if v in unknowns)
        rest = tuple((v, e) for v, e in m if v not in unknowns)
        groups.setdefault(key, {})[rest] = c
    if len(groups) > 1:
        g = Poly()
        for t in groups.values():
            g = S.poly_gcd(g, Poly(t))
            if g.is_const():
                break
        if not g.is_const() and not (g.vars() & _gen_names(st)):
            q = S.divide_exact(p, g)
            if q is not None:
                st.conds.append(RF(g))
                p = q.scale(1 / q.content())
    return p


def _substitute(st: _State, u: str, val: RF, unknowns: set) -> None:
    newp = []
    for j, q in st.polys:
        if u in q.vars():
            r = q.subs_power(u, 1, val)
            if not r.den.is_const():
                st.conds.append(RF(r.den))
            q = _reduce(r.num, st)
        newp.append((j, q))
    st.polys = newp
    for w in list(st.values):
        st.values[w] = _subs(st.values[w], u, val, st)
    st.values[u] = val


def _settle(st: _State, unknowns: set) -> None:
    keep = []
    for j, q in st.polys:
        q = _reduce(q, st)
        if q.is_zero():
            continue
        if not (q.vars() & unknowns):
            if q.is_const() or (st.ext and q.vars() <= set(st.algs)):
                raise SymbolicError("INCONSISTENT",
                                    f"equation {j + 1} reduces to "
                                    f"{S.to_text(RF(q))} = 0")
            raise SymbolicError("OVERDETERMINED",
                                f"equation {j + 1} forces a relation among "
                                f"the parameters: {S.to_text(RF(q))} = 0")
        keep.append((j, _primitive(q, unknowns, st)))
    st.polys = keep


def _choose_linear(st: _State, unknowns: set, targets: Sequence[str],
                   strict: bool):
    best = None
    for idx, (i, p) in enumerate(st.polys):
        live = p.vars() & unknowns
        for u in sorted(live):
            cs = p.coeffs(u)
            if set(cs) - {0} != {1}:
                continue
            a = cs[1]
            if bool(a.vars() & unknowns) == strict:
                continue
            # Phase 104: a constant coefficient first (no nonzero condition)
            rank = (len(live), st.ext and not a.is_const(), u in targets,
                    len(p.t), idx, u)
            if best is None or rank < best[0]:
                best = (rank, idx, u, a, cs.get(0, Poly()))
    return best


def _apply_linear(st: _State, choice, unknowns: set) -> None:
    _, idx, u, a, b = choice
    i, _ = st.polys.pop(idx)
    val = _rationalise(RF(-b) / RF(a), st)
    if not a.is_const():
        st.conds.append(RF(a))
    st.steps.append(f"from equation {i + 1}: {u} = {S.to_text(val)}")
    _substitute(st, u, val, unknowns)


def _choose_univariate(st: _State, unknowns: set):
    best = None
    for idx, (i, p) in enumerate(st.polys):
        live = p.vars() & unknowns
        if len(live) == 1:
            u = next(iter(live))
            rank = (p.deg(u), len(p.t), idx)
            if best is None or rank < best[0]:
                best = (rank, idx, u)
    return best


# -- roots of one equation in one unknown ----------------------------------

def _rf_poly(v: RF) -> Tuple[Poly, Poly]:
    return v.num, v.den


def _constant_gens(st: _State) -> set:
    """Generators whose value is a real constant: radical atoms, algebraic
    numbers, and roots of radicands built only from those."""
    out = set(st.algs) | {g for g in st.rels if g in S.RADICALS}
    grew = True
    while grew:
        grew = False
        for g, R in st.rels.items():
            if g not in out and R.vars() <= out:
                out.add(g)
                grew = True
    return out


def _gen_interval(g: str, st: _State, width: Fraction
                  ) -> Tuple[Fraction, Fraction]:
    """An interval with rational ends, narrower than about ``width``,
    holding the real value of the constant generator ``g``."""
    if g in st.algs:
        a = st.algs[g]
        return A.refine(a.m, a.lo, a.hi, width)
    if g in S.RADICALS:
        q, c = S.RADICALS[g]
        k, R = q, Poly.const(c)
    else:
        k, R = st.kdeg.get(g, 2), st.rels[g]
    lo, hi = _poly_interval(R, st, width / 4)
    if k % 2 == 0 and lo < 0:
        if hi < 0:
            raise ArithmeticError("an even root of a negative value")
        lo = Fraction(0)
    # bisect t^k - v on a bracket of [lo, hi]
    def root_bound(v: Fraction, up: bool) -> Fraction:
        sgn = -1 if v < 0 else 1
        av = abs(v)
        a, b = Fraction(0), max(Fraction(1), av)
        while b - a > width / 4:
            m = (a + b) / 2
            if m ** k < av:
                a = m
            else:
                b = m
        return sgn * (b if (up == (sgn > 0)) else a)
    return root_bound(lo, False), root_bound(hi, True)


def _poly_interval(p: Poly, st: _State, width: Fraction
                   ) -> Tuple[Fraction, Fraction]:
    ivs = {g: _gen_interval(g, st, width) for g in p.vars()}
    lo = hi = Fraction(0)
    for m, c in p.t.items():
        a = b = Fraction(c)
        for v, e in m:
            x, y = ivs[v]
            for _ in range(e):
                prods = (a * x, a * y, b * x, b * y)
                a, b = min(prods), max(prods)
        lo, hi = lo + a, hi + b
    return lo, hi


def _const_sign(p: Poly, st: _State) -> Optional[int]:
    """The sign of ``p`` when it holds only constant generators (no
    letter), decided by exact interval arithmetic on narrowing intervals;
    ``None`` when ``p`` holds a letter or the sign was not decided."""
    p = _reduce(p, st)
    if p.is_zero():
        return 0
    if not p.vars() <= _constant_gens(st):
        return None
    width = Fraction(1, 16)
    for _ in range(40):
        try:
            lo, hi = _poly_interval(p, st, width)
        except ArithmeticError:
            return None
        if lo > 0:
            return 1
        if hi < 0:
            return -1
        width /= 256
    return None


def _sqrt_of(d: Poly, st: _State) -> Optional[Tuple[RF, _New]]:
    """``(s, new)`` with ``s^2 = d`` once ``new`` is absorbed, or ``None``
    when ``d`` is negative (a constant, or an expression in one algebraic
    number whose sign is decided exactly)."""
    gens = _gen_names(st)
    if not (d.vars() & gens):
        sq = poly_sqrt(d)
        if sq is not None:
            return RF(sq), _New()
    outer, r = _square_part(d)
    if r.is_const():
        base = r.const_value()
        if base < 0:
            return None
        s = S.radical_atom(base, 1, 2)
        name = next(iter(s.num.vars()))
        return outer * s, _New({name: Poly.const(S.RADICALS[name][1])})
    if st.ext and _const_sign(r, st) == -1:
        # a radicand free of letters, negative: no real root (Phase 104)
        return None
    name = f"sqrt({S.to_text(RF(r))})"
    return outer * RF(Poly.var(name)), _New({name: r})


def _sqrt_rf(v: RF, st: _State) -> Optional[Tuple[RF, _New]]:
    """``sqrt(n/d) = sqrt(n*d)/d`` (``d`` free of generators)."""
    got = _sqrt_of(_reduce(v.num * v.den, st), st)
    if got is None:
        return None
    return got[0] / RF(v.den), got[1]


def _cbrt_rf(v: RF, st: _State) -> Tuple[RF, _New]:
    """``cbrt(n/d) = cbrt(n*d^2)/d``: a cube-root generator, or a rational
    or radical constant."""
    r = _reduce(v.num * v.den * v.den, st)
    if r.is_const():
        c = r.const_value()
        root = S.rational_root(abs(c), 3)
        if root is not None:
            val = RF(Poly.const(root if c > 0 else -root))
            return val / RF(v.den), _New()
        s = S.radical_atom(abs(c), 1, 3)
        name = next(iter(s.num.vars()))
        s = s if c > 0 else -s
        return s / RF(v.den), _New({name: Poly.const(S.RADICALS[name][1])},
                                   {name: 3}, fixed={name})
    name = f"cbrt({S.to_text(RF(r))})"
    return RF(Poly.var(name)) / RF(v.den), _New({name: r}, {name: 3},
                                                  fixed={name})


def _quadratic(a: Poly, b: Poly, c0: Poly, st: _State, notes: List[str],
               p: Poly) -> List[Tuple[RF, _New]]:
    """The real roots of ``a u^2 + b u + c0`` (Phase 103's rule; with the
    additions on, the coefficients may hold generators)."""
    roots: List[Tuple[RF, _New]] = []
    disc = _reduce(b * b - Poly.const(4) * a * c0, st)
    two_a = RF(a) * 2
    if disc.is_zero():
        return [(RF(-b) / two_a, _New())]
    if not (disc.vars() & _gen_names(st)):
        sq = poly_sqrt(disc)
        if sq is not None:
            return [((RF(-b) + RF(sq)) / two_a, _New()),
                    ((RF(-b) - RF(sq)) / two_a, _New())]
    got = _sqrt_of(disc, st)
    if got is None:
        notes.append(f"the factor {S.to_text(RF(p))} has no real root")
        return roots
    s, new = got
    if new.empty():
        return [((RF(-b) + s) / two_a, _New()), ((RF(-b) - s) / two_a,
                                                 _New())]
    return [((RF(-b) + s) / two_a, new)]


def _clear(*vs: RF) -> List[Poly]:
    """The same values times one common denominator, as polynomials."""
    den = Poly.const(1)
    for v in vs:
        den = den * v.den
    out = []
    for v in vs:
        w = v * RF(den)
        out.append(w.num.scale(1 / w.den.const_value()))
    return out


def _upoly_text(m: List[Fraction], var: str = "t") -> str:
    """``t^3 - 3*t + 1``: the terms from the highest power down."""
    out = ""
    for i in range(len(m) - 1, -1, -1):
        c = m[i]
        if not c:
            continue
        mono = "" if i == 0 else (var if i == 1 else f"{var}^{i}")
        a = abs(c)
        coef = _frac_text(a)
        if mono:
            body = mono if a == 1 else (f"({coef})*{mono}" if
                                        a.denominator != 1 else
                                        f"{coef}*{mono}")
        else:
            body = coef if a.denominator == 1 else f"({coef})"
        if not out:
            out = ("-" if c < 0 else "") + body
        else:
            out += (" - " if c < 0 else " + ") + body
    return out


def _frac_text(q: Fraction) -> str:
    return str(q.numerator) if q.denominator == 1 else \
        f"{q.numerator}/{q.denominator}"


def _numeric_roots(p: Poly, u: str, st: _State, notes: List[str]
                   ) -> List[Tuple[RF, _New]]:
    """Every real root of a polynomial with rational coefficients and no
    rational root, of degree 3 or more: its irreducible factors, a quadratic
    one by the quadratic rule and any other by real-root isolation, each
    root an algebraic number."""
    cs = p.coeffs(u)
    up = [cs[i].const_value() if i in cs else Fraction(0)
          for i in range(p.deg(u) + 1)]
    facs = A.factor_rational(up)
    if facs is None:
        raise SymbolicError("NONLINEAR", f"{u} is a root of a polynomial of "
                                         f"degree {p.deg(u)} whose factors "
                                         f"over the rationals were not "
                                         f"decided: {S.to_text(RF(p))} = 0")
    roots: List[Tuple[RF, _New]] = []
    for f in facs:
        fp = Poly()
        for i, c in enumerate(f):
            if c:
                fp = fp + Poly.var(u, i).scale(c)
        if len(f) == 3:
            roots.extend(_quadratic(Poly.const(f[2]), Poly.const(f[1]),
                                    Poly.const(f[0]), st, notes, fp))
            continue
        if len(f) == 2:
            roots.append((RF(Poly.const(-f[0] / f[1])), _New()))
            continue
        ivs = [A.refine(f, lo, hi, Fraction(1))
               for lo, hi in A.isolate_real_roots(f)]
        if not ivs:
            notes.append(f"the factor {S.to_text(RF(fp))} has no real root")
        # Phase 112: an irreducible factor of prime degree >= 5 with two
        # non-real roots has no root in radicals; say so, with the reason.
        from .symbolic_factor import radical_free, radical_free_galois
        cert = radical_free(list(f), len(ivs))
        if cert is None and ivs:
            # Phase 113: otherwise read the Galois group off one Frobenius
            # element (studies/FROBENIUS_RADICAL_STUDY.md); Phase 114: off
            # two in composite degree (studies/PRIMITIVE_RADICAL_STUDY.md).
            cert = radical_free_galois(list(f))
        for lo, hi in ivs:
            name = (f"root({_upoly_text(f)}, {_frac_text(lo)}, "
                    f"{_frac_text(hi)})")
            new = _New(algs={name: _Alg(list(f), lo, hi)})
            if cert:
                new.note = f"{_upoly_text(f)}: {cert}"
            roots.append((RF(Poly.var(name)), new))
    return roots


def _even_quartic(a4: Poly, b2: Poly, c0: Poly, st: _State,
                  notes: List[str], u: str, p: Poly) -> List[Tuple[RF, _New]]:
    """``a4 u^4 + b2 u^2 + c0`` in letters.  When ``c0/a4 = c^2`` it is
    ``(u^2 - g u + c)(u^2 + g u + c)`` with ``g^2 = 2c - b2/a4``, so its roots
    need only square roots free of each other; otherwise ``u^2`` is a root
    of a quadratic and ``u`` a square root of it (a tower)."""
    B, C = RF(b2) / RF(a4), RF(c0) / RF(a4)
    c = None
    sq = poly_sqrt(C.num * C.den)
    if sq is not None:
        c = RF(sq) / RF(C.den)
    if c is not None:
        for cc in (c, -c):
            g2 = cc * 2 - B
            if g2.is_zero():
                continue
            r = poly_sqrt(g2.num * g2.den)
            if r is not None:
                rr = RF(r) / RF(g2.den)
                out: List[Tuple[RF, _New]] = []
                for sgn in (1, -1):
                    qa, qb, qc = _clear(RF(Poly.const(1)), rr * (-sgn), cc)
                    out.extend(_quadratic(qa, qb, qc, st, notes, p))
                return out
        g2 = c * 2 - B
        got = _sqrt_rf(g2, st)
        h2 = -c * 2 - B
        goth = _sqrt_rf(h2, st)
        if got is None or goth is None:
            # u^2 -/+ g u + c with g or its partner imaginary
            notes.append(f"the factor {S.to_text(RF(p))} has no real root")
            return []
        (gv, gn), (hv, hn) = got, goth
        return [((gv + hv) / 2, gn.merge(hn))]
    out = []
    for wv, wn in _quadratic(a4, b2, c0, st, notes, p):
        if wv.is_zero():
            continue
        view = _with(st, wn)
        got = _sqrt_rf(wv, view)
        if got is None:
            notes.append(f"{u}^2 = {S.to_text(wv)} has no real root")
            continue
        out.append((got[0], wn.merge(got[1])))
    return out


def _cardano(cs: Dict[int, Poly], st: _State, u: str
             ) -> Tuple[List[Tuple[RF, _New]], List[RF]]:
    """The one real root of a cubic in letters when its discriminant makes
    it the only one: ``u = t - a2/(3 a3)`` with ``t^3 + P t + Q = 0``,
    ``t = A - P/(3A)``, ``A = cbrt(-Q/2 + sqrt(Q^2/4 + P^3/27))``, valid when
    ``Q^2/4 + P^3/27 > 0`` (stated)."""
    a3, a2, a1, a0 = (RF(cs.get(i, Poly())) for i in (3, 2, 1, 0))
    shift = a2 / (a3 * 3)
    P = (a3 * a1 * 3 - a2 * a2) / (a3 * a3 * 3)
    Q = (a2 * a2 * a2 * 2 - a3 * a2 * a1 * 9 + a3 * a3 * a0 * 27) / \
        (a3 * a3 * a3 * 27)
    conds: List[RF] = []
    if not a3.is_const():
        conds.append(RF(a3.num))
    if P.is_zero():
        t, new = _cbrt_rf(-Q, st)
        return [(t - shift, new)], conds
    D = Q * Q / 4 + P * P * P / 27
    if D.is_const():
        raise SymbolicError("NONLINEAR", f"{u} is a root of a cubic whose "
                                         f"discriminant is a constant")
    # Phase 108: a discriminant plainly below zero (minus it is a sum of
    # even powers with positive coefficients) is the casus irreducibilis
    # too; Phase 104 printed Cardano's root under "D > 0" here, a condition
    # no value of the letters meets
    #
    # Sharpening pass: which regime applies is a route choice
    # (``reasoning/routes.py``), not a switch.  ``TRIG`` off is Phase 104
    # exactly (Cardano or the refusal); on, the route is taken from what is
    # decided: real roots stated by the caller or a plainly negative
    # discriminant -> Viete; a plainly positive one -> Cardano; neither ->
    # both regimes, each under its own condition.
    free = not (D.num.vars() & _gen_names(st))
    dd = D.num * D.den
    neg = TRIG and free and _plainly_nonnegative(-dd) and not dd.is_const()
    pos = free and _plainly_nonnegative(dd)
    # Phase 109: the surface test reads only the expanded polynomial; a
    # discriminant that is a square times a plainly signed factor fails it.
    # Its square-free factorisation decides the sign when every factor to an
    # odd power is plainly signed (``reasoning/sign_factor.py``)
    by_factor = ""
    if TRIG and free and not (neg or pos) and not dd.is_const() and \
            R.decider_on("cubic.letters", "factor"):
        from .sign_factor import decided_sign
        sgn, why = decided_sign(dd)
        if sgn is not None:
            neg, pos = sgn < 0, sgn > 0
            by_factor = why
    stated = TRIG and bool(R.fact("real_roots")) and free
    got = None if (neg or stated) else _sqrt_rf(D, st)
    dec = R.choose("cubic.letters", [
        ("viete", TRIG and (neg or stated or got is None),
         "the caller states three real roots" if stated else
         (f"the discriminant is negative ({by_factor})" if by_factor else
          "the discriminant is plainly negative") if neg else
         "the square root of the discriminant is not real"),
        ("cardano", got is not None and (pos or not TRIG),
         (f"the discriminant is positive ({by_factor})" if by_factor else
          "the discriminant is plainly positive") if pos else
         "the Phase 104 reading (three-real routes off)"),
        ("cases", got is not None and TRIG,
         "the sign of the discriminant is not decided, so both regimes "
         "are given, each under its own condition"),
        # with the split disabled: Cardano's root under "D > 0" alone, as
        # Phases 104 and 108 shipped it
        ("cardano", got is not None,
         "the sign of the discriminant is not decided; the split is "
         "disabled, so Cardano's root is given under its condition"),
    ])
    if dec is None or (dec.route == "cardano" and got is None):
        raise SymbolicError("NONLINEAR", f"{u} is a root of a cubic in "
                                         f"letters with no real radical form "
                                         f"(three real roots)")
    if dec.route == "viete":
        # found in Phase 106 (a triple pendulum's modes): the square root of
        # the discriminant is not real, the casus irreducibilis -- three real
        # roots and no real radical form.  Phase 104 refused it; Phase 108
        # answers it (``studies/CUBIC_TRIG_STUDY.md``)
        out, cc = _three_real(a3, P, Q, shift, D, st, u, conds)
        for _, new in out:
            new.note = (dec.text() + "; " + new.note) if new.note else \
                dec.text()
        return out, cc
    s, sn = got
    view = _with(st, sn)
    W = -Q / 2 + s
    if _is_zero(W, view):
        W = -Q / 2 - s
    av, an = _cbrt_rf(_rationalise(W, view), view)
    new = sn.merge(an)
    new.fixed |= set(sn.rels) | set(an.rels)
    new.ineqs.append(f"{S.to_text(D)} > 0 (then it is the only real root)")
    new.note = (f"Cardano: with {u} = t - ({S.to_text(shift)}), "
                f"t^3 + ({S.to_text(P)})*t + ({S.to_text(Q)}) = 0 and "
                f"t = cbrt(W) - ({S.to_text(P)})/(3*cbrt(W)), "
                f"W = {S.to_text(-Q / 2)} + sqrt({S.to_text(D)}), the real "
                f"cube root; equivalently cbrt(W) + cbrt(W'), "
                f"W' = {S.to_text(-Q / 2)} - sqrt({S.to_text(D)})")
    conds.append(RF(P.num))
    t = av - P / (av * 3)
    new.note = dec.text() + "; " + new.note
    out = [(t - shift, new)]
    if dec.route == "cases":
        # the other regime: D <= 0 (P < 0), three real roots by Viete; at
        # D = 0 two of them coincide and Cardano's root is the third
        cc: List[RF] = []
        three, cc = _three_real(a3, P, Q, shift, D, st, u, cc)
        if any(nw.note.startswith("homogeneous") for _, nw in three):
            # P^3/Q^2 a number: the scaled route is exact whatever the sign
            for _, nw in three:
                nw.note = dec.text() + "; " + nw.note
            return three, conds[:-1] + cc
        for _, nw in three:
            nw.note = ("case D < 0 of the split; " + nw.note)
        out += three
    return out, conds


#: Phase 108's switch: off, a cubic in letters with three real roots is
#: refused exactly as Phase 104 refused it.
TRIG = True


def _three_real(a3: RF, P: RF, Q: RF, shift: RF, D: RF, st: _State, u: str,
                conds: List[RF]) -> Tuple[List[Tuple[RF, _New]], List[RF]]:
    """The three real roots of ``a3 u^3 + ...`` with ``u = t - shift``,
    ``t^3 + P t + Q = 0`` and ``D = Q^2/4 + P^3/27 < 0`` (Phase 108).

    * **homogeneous**: when ``P^3/Q^2`` is a number, ``t = s tau`` with
      ``s`` a ratio of the letters and ``tau`` a root of a cubic with
      rational coefficients -- every root found by the numeric route (an
      algebraic number, a square root or a rational);
    * **Viete** otherwise: ``t_k = 2 sqrt(-P/3) cos(acos(K)/3 - 2 pi k/3)``,
      ``K = (3Q/(2P)) sqrt(-3/P)``, ``k = 0, 1, 2`` in decreasing order,
      each a generator ``y = M t_k`` whose relation is the cubic itself.

    ``RequestProject/GLM/CubicTrig.lean`` proves both."""
    notes: List[str] = []
    if Q.is_zero():
        # t (t^2 + P): 0 and +-sqrt(-P)
        got = _sqrt_rf(-P, st)
        out = [(-shift, _New())]
        if got is not None:
            s, sn = got
            out += [(s - shift, sn), (-s - shift, sn)] if not sn.empty() \
                else [(s - shift, _New()), (-s - shift, _New())]
        return out, conds
    kappa = P * P * P / (Q * Q)
    if kappa.is_const():
        s1 = Q / P
        lc = Fraction(s1.num.leading()[1]) / Fraction(s1.den.leading()[1])
        s0 = s1 * RF(Poly.const(1 / lc))
        if not s0.den.is_const():
            conds.append(RF(s0.den))
        var = "t"
        sig = shift / s0
        c1, c0 = P / (s0 * s0), Q / (s0 * s0 * s0)
        if sig.is_const():
            # u = s0 * mu with mu a root of a cubic with rational
            # coefficients: tau = mu + sig, tau^3 + c1 tau + c0 = 0
            m = Poly.var(var) + sig.num.scale(1 / sig.den.const_value())
            f = m * m * m + m * c1.num.scale(1 / c1.den.const_value()) + \
                c0.num.scale(1 / c0.den.const_value())
            base = RF(Poly())
        else:
            m = Poly.var(var)
            f = m * m * m + m * c1.num.scale(1 / c1.den.const_value()) + \
                c0.num.scale(1 / c0.den.const_value())
            base = -shift
        got = _numeric_roots(f, var, st, notes)
        out = []
        for val, new in got:
            new.note = (f"homogeneous: {u} = ({S.to_text(s0)})*t + "
                        f"({S.to_text(base)}) with t a root of "
                        f"{S.to_text(RF(f))} = 0")
            out.append((s0 * val + base, new))
        return out, conds
    # Viete
    # y = M t with M the least common multiple of the denominators
    M = Poly.const(1)
    for v in (P, Q):
        if not v.den.is_const():
            M = S.divide_exact(M * v.den, S.poly_gcd(M, v.den))
    Mrf = RF(M)
    cP = P * Mrf * Mrf
    cQ = Q * Mrf * Mrf * Mrf
    if not (cP.den.is_const() and cQ.den.is_const()):
        raise SymbolicError("NONLINEAR", f"{u} is a root of a cubic in "
                                         f"letters with three real roots "
                                         f"whose coefficients were not "
                                         f"cleared")
    pP = cP.num.scale(1 / cP.den.const_value())
    pQ = cQ.num.scale(1 / cQ.den.const_value())
    r2 = -P / 3
    rt = S.to_text(r2)
    Kv = Q * 3 / (P * 2)
    sq = _sqrt_rf(RF(Poly.const(-3)) / P, st)
    K_text = (f"({S.to_text(Kv)})*sqrt({S.to_text(RF(Poly.const(-3)) / P)})"
              if sq is None or not sq[1].rels else
              S.to_text(_rationalise(Kv * sq[0], _with(st, sq[1]))))
    out = []
    for k in range(3):
        ang = "acos(K)/3" if k == 0 else f"acos(K)/3 - {2 * k}*pi/3"
        trig = (f"2*sqrt({rt})*cos({ang.replace('K', K_text)})")
        name = trig if M.is_const() and M.const_value() == 1 else \
            f"({S.to_text(Mrf)})*{trig}"
        y = Poly.var(name)
        rel = -(pP * y) - pQ
        new = _New({name: rel}, {name: 3}, fixed={name},
                   trig={name: (k, M)})
        new.ineqs.append(f"4*P^3 + 27*Q^2 = {S.to_text(D * 108)} < 0 "
                         f"(three real roots, k = 0, 1, 2 in decreasing "
                         f"order)")
        new.note = (f"Viete: with {u} = t - ({S.to_text(shift)}), "
                    f"t^3 + ({S.to_text(P)})*t + ({S.to_text(Q)}) = 0 has "
                    f"three real roots t_k = 2*sqrt(-P/3)*cos(acos(K)/3 - "
                    f"2*pi*k/3), K = (3*Q/(2*P))*sqrt(-3/P) = {K_text}")
        out.append((RF(y) / Mrf - shift, new))
    return out, conds


def _roots(p: Poly, u: str, st: _State) -> Tuple[List[Tuple[RF, _New]],
                                                 List[RF], List[str]]:
    """The real roots of ``p`` in ``u`` (other letters known), as
    ``(value, new generators)``, with the conditions and the notes."""
    notes: List[str] = []
    conds: List[RF] = []
    held = bool(p.vars() & _gen_names(st))
    if p.deg(u) >= 2 and held:
        if not st.ext or p.deg(u) > 2:
            raise SymbolicError("NONLINEAR", f"{u} is a root of a polynomial "
                                             f"whose coefficients hold a "
                                             f"square root (a nested "
                                             f"radical)")
        cs = p.coeffs(u)
        a = cs[2]
        conds.append(RF(a))
        return (_quadratic(a, cs.get(1, Poly()), cs.get(0, Poly()), st,
                           notes, p), conds, notes)
    c = S._content_in(p, u)
    if not c.is_const():
        p = S.divide_exact(p, c)
        conds.append(RF(c))
    roots: List[Tuple[RF, _New]] = []
    e0 = min(p.exponents(u))
    if e0 > 0:
        roots.append((RF(Poly()), _New()))
        p = S.divide_exact(p, Poly.var(u, e0))
    if p.deg(u) >= 2:
        g = S.poly_gcd(p, S._dpoly(p, u))
        if u in g.vars():
            p = S.divide_exact(p, g)
            notes.append(f"repeated factor {S.to_text(RF(g))} removed")
    while p.deg(u) > 2 and p.vars() == {u}:
        r = _rational_root(p, u)
        if r is None:
            break
        roots.append((RF(Poly.const(r)), _New()))
        p = S.divide_exact(p, Poly.var(u) - Poly.const(r))
    d = p.deg(u)
    cs = p.coeffs(u)
    if d == 1:
        roots.append((RF(-cs.get(0, Poly())) / RF(cs[1]), _New()))
        if not cs[1].is_const():
            conds.append(RF(cs[1]))
    elif d == 2:
        a, b, c0 = cs[2], cs.get(1, Poly()), cs.get(0, Poly())
        if not a.is_const():
            conds.append(RF(a))
        roots.extend(_quadratic(a, b, c0, st, notes, p))
    elif d > 2 and st.ext and p.vars() == {u}:
        roots.extend(_numeric_roots(p, u, st, notes))
    elif d == 4 and st.ext and set(cs) <= {0, 2, 4}:
        if not cs[4].is_const():
            conds.append(RF(cs[4]))
        roots.extend(_even_quartic(cs[4], cs.get(2, Poly()),
                                   cs.get(0, Poly()), st, notes, u, p))
    elif d == 3 and st.ext:
        got, cc = _cardano(cs, st, u)
        roots.extend(got)
        conds.extend(cc)
    elif d > 2:
        why = _no_radical_formula(p, u) if st.ext else None
        raise SymbolicError("NONLINEAR", f"{u} is a root of a polynomial of "
                                         f"degree {d} with no rational root: "
                                         f"{S.to_text(RF(p))} = 0" +
                            (f"; {why}" if why else ""))
    return roots, conds, notes


#: Values tried for each letter when a polynomial in letters is specialised
#: in search of a point with no root in radicals (Phase 112).
_SPECIALISE_VALUES = (1, -1, 2, -2, 3, -3, 4, -4, 5, -5)
#: Specialisations tried before the search gives up.
_SPECIALISE_BUDGET = 400


def _no_radical_formula(p: Poly, u: str) -> Optional[str]:
    """Phase 112, ``studies/QUINTIC_RADICAL_STUDY.md``: for a polynomial in
    ``u`` whose coefficients hold letters, a rational point of the letters at
    which it keeps its degree and no root is expressible in radicals
    (:func:`glm_universal.reasoning.symbolic_factor.certify_numeric`), stated
    as the reason no formula in radicals of the letters exists; ``None`` when
    the degree is below 5 or no point in the search qualifies.  Points are
    tried smallest first, in a fixed order.  The conjugation certificate
    needs prime degree; the Frobenius pass below covers composite degree too
    (Phase 114, ``studies/PRIMITIVE_RADICAL_STUDY.md``)."""
    from itertools import product as _product
    from .symbolic_factor import certify_numeric
    d = p.deg(u)
    letters = sorted(p.vars() - {u})
    if d < 5 or not letters or len(letters) > 3:
        return None
    combos = sorted(_product(_SPECIALISE_VALUES, repeat=len(letters)),
                    key=lambda c: (sum(abs(x) for x in c),
                                   [_SPECIALISE_VALUES.index(x) for x in c]))
    cs = p.coeffs(u)
    for combo in combos[:_SPECIALISE_BUDGET]:
        env = {v: Fraction(x) for v, x in zip(letters, combo)}
        vals = []
        for i in range(d + 1):
            c = cs.get(i, Poly())
            vals.append(Fraction(c.evaluate(env)))
        if vals[-1] == 0:
            continue
        den = 1
        for v in vals:
            den = den * v.denominator // gcd(den, v.denominator)
        ints = [int(v * den) for v in vals]
        cert = certify_numeric(ints)
        if cert is None:
            continue
        point = ", ".join(f"{v} = {x}" for v, x in zip(letters, combo))
        spec = _upoly_text([Fraction(c) for c in ints], u)
        return (f"no formula in radicals of {', '.join(letters)} exists: at "
                f"{point} the equation is {spec} = 0, and {cert}, so no "
                f"radical expression defined at that point gives a root "
                f"there (GLM.QuinticRadicals."
                f"quintic_in_letters_no_radical_formula is the case "
                f"x^5 + p*x = q)")
    # Phase 113 (studies/FROBENIUS_RADICAL_STUDY.md): no point passed the
    # conjugation certificate; try the Frobenius certificate on the same
    # points, with the smaller prime bound and point budget declared below.
    from .symbolic_factor import radical_free_galois, zassenhaus
    for combo in combos[:_FROBENIUS_POINT_BUDGET]:
        ints = _specialise_ints(cs, d, letters, combo)
        if ints is None:
            continue
        facs = zassenhaus(ints)
        if facs is None or len(facs) != 1:
            continue
        cert = radical_free_galois([Fraction(c) for c in ints],
                                   bound=_FROBENIUS_LETTER_PRIMES)
        if cert is None:
            continue
        point = ", ".join(f"{v} = {x}" for v, x in zip(letters, combo))
        spec = _upoly_text([Fraction(c) for c in ints], u)
        return (f"no formula in radicals of {', '.join(letters)} exists: at "
                f"{point} the equation is {spec} = 0, and {cert}, so no "
                f"radical expression defined at that point gives a root "
                f"there")
    return None


#: Points tried by the Frobenius pass of :func:`_no_radical_formula`, and the
#: bound on the primes tried at each (Phase 113).
_FROBENIUS_POINT_BUDGET = 100
_FROBENIUS_LETTER_PRIMES = 100


def _specialise_ints(cs, d: int, letters, combo) -> Optional[List[int]]:
    """The integer polynomial (constant first) of ``cs`` at the point
    ``combo`` of ``letters``, cleared of denominators; ``None`` when the
    leading coefficient vanishes there or the polynomial is not squarefree."""
    from .symbolic_algebraic import pderiv, pgcd
    env = {v: Fraction(x) for v, x in zip(letters, combo)}
    vals = [Fraction(cs.get(i, Poly()).evaluate(env)) for i in range(d + 1)]
    if vals[-1] == 0:
        return None
    if len(pgcd(vals, pderiv(vals))) > 1:
        return None
    den = 1
    for v in vals:
        den = den * v.denominator // gcd(den, v.denominator)
    return [int(v * den) for v in vals]


#: Points tried by :func:`modes_radical_reason`: every letter 1, then one
#: letter at a time raised to each of these values (Phase 114).
_MODES_RAISE = (2, 3)


def modes_radical_reason(cs: List[RF], u: str = "w2") -> Optional[str]:
    """Phase 114, ``studies/PRIMITIVE_RADICAL_STUDY.md``: the reason no
    formula in radicals gives the roots of ``sum cs[i] u^i`` (the
    characteristic polynomial of the ``modes.higher`` route, its letters the
    masses, lengths and the like, all positive), or ``None``.

    The letters are specialised to positive points -- all 1 first, then one
    letter at a time raised to 2 and to 3 -- and at the first point where the
    polynomial keeps its degree, is irreducible and passes a radical-free
    certificate (:func:`glm_universal.reasoning.symbolic_factor.
    certify_numeric_any`: complex conjugation, or Frobenius elements in prime
    or composite degree), that point is the reason: a radical expression in
    the letters defined there would give a root there.  With no letters the
    polynomial itself is certified."""
    from .symbolic_factor import certify_numeric_any
    d = len(cs) - 1
    if d < 5:
        return None
    letters = sorted(set().union(*(c.vars() for c in cs)))
    points: List[Dict[str, Fraction]] = [{v: Fraction(1) for v in letters}]
    for value in _MODES_RAISE:
        for v in letters:
            point = {w: Fraction(1) for w in letters}
            point[v] = Fraction(value)
            points.append(point)
    for env in points:
        try:
            vals = [Fraction(c.evaluate(env)) for c in cs]
        except ZeroDivisionError:
            continue
        if vals[-1] == 0:
            continue
        den = 1
        for v in vals:
            den = den * v.denominator // gcd(den, v.denominator)
        ints = [int(v * den) for v in vals]
        cert = certify_numeric_any(ints)
        if cert is None:
            continue
        spec = _upoly_text([Fraction(c) for c in ints], u)
        if not letters:
            return f"{spec}: {cert}"
        at = ", ".join(f"{v} = {env[v]}" for v in letters)
        return (f"no formula in radicals of {', '.join(letters)} gives these "
                f"roots: at {at} the equation is {spec} = 0, and {cert}, so "
                f"no radical expression defined at that point gives a root "
                f"there")
    return None


# -- the greatest common divisor of the equations left in one unknown -------

def _upoly_of(p: Poly, u: str) -> Dict[int, RF]:
    return {e: RF(c) for e, c in p.coeffs(u).items()}


def _ugcd(a: Dict[int, RF], b: Dict[int, RF], st: _State) -> Dict[int, RF]:
    while b:
        _, r = _udivmod(a, b, st)
        a, b = b, r
    return a


def _shrink(st: _State, idx: int, u: str, unknowns: set) -> None:
    """Phase 104: an equation left in ``u`` whose coefficients hold a
    generator is replaced by its greatest common divisor with every other
    equation, and every original equation, that is left in ``u`` alone.  A
    solution satisfies all of them, so it is a root of the divisor."""
    i, p = st.polys[idx]
    cands = [q for j, (_, q) in enumerate(st.polys)
             if j != idx and (q.vars() & unknowns) == {u}]
    for _, q in st.origs:
        v = RF(q)
        for w, val in st.values.items():
            v = _subs(v, w, val, st)
        qn = _reduce(v.num, st)
        if not qn.is_zero() and (qn.vars() & unknowns) == {u}:
            cands.append(qn)
    g = _upoly_of(p, u)
    for q in cands:
        g = _ugcd(g, _upoly_of(q, u), st)
        if max(g) <= 1:
            break
    if max(g) == 0:
        raise SymbolicError("INCONSISTENT", f"the equations left in {u} have "
                                            f"no common root")
    if max(g) >= p.deg(u):
        return
    den = Poly.const(1)
    for c in g.values():
        den = den * c.den
    newp = Poly()
    for e, c in g.items():
        w = c * RF(den)
        newp = newp + (w.num.scale(1 / w.den.const_value()) * Poly.var(u, e)
                       if e else w.num.scale(1 / w.den.const_value()))
    st.polys[idx] = (i, _reduce(newp, st))
    st.steps.append(f"the equations left in {u} share a factor of degree "
                    f"{max(g)} (their greatest common divisor)")


def _choose_resultant(st: _State, unknowns: set, targets: Sequence[str]):
    best = None
    for x in sorted(unknowns):
        holders = [(p.deg(x), len(p.t), idx) for idx, (_, p)
                   in enumerate(st.polys) if x in p.vars()]
        if len(holders) < 2:
            continue
        holders.sort()
        rank = (x in targets, holders[0][0] * holders[1][0], x)
        if best is None or rank < best[0]:
            best = (rank, x, holders[0][2], holders[1][2])
    return best


def _split_linear(st: _State, ch, unknowns: set, targets: Sequence[str],
                  dropped: List[str]) -> List[_State]:
    """``A u + B = 0`` with ``A`` holding other unknowns: either ``A != 0``
    and ``u = -B/A``, or ``A = 0`` and ``B = 0`` -- both cases are followed,
    so no solution on ``A = 0`` is lost (Phase 103's planted battery found
    two systems that lost one before this split)."""
    _, idx, u, a, b = ch
    if st.splits >= MAX_SPLITS:
        raise SymbolicError("NONLINEAR", "too many case splits")
    zero = st.copy()
    zero.splits += 1
    i, _ = zero.polys.pop(idx)
    zero.polys.extend([(i, a), (i, b)])
    zero.steps.append(f"from equation {i + 1}, the case "
                      f"{S.to_text(RF(a))} = 0")
    nonzero = st.copy()
    nonzero.splits += 1
    i, _ = nonzero.polys.pop(idx)
    val = _rationalise(RF(-b) / RF(a), nonzero)
    nonzero.steps.append(f"from equation {i + 1}, the case "
                         f"{S.to_text(RF(a))} != 0: {u} = {S.to_text(val)}")
    _substitute(nonzero, u, val, unknowns)
    out: List[_State] = []
    for case in (nonzero, zero):
        try:
            out.extend(_run(case, unknowns, targets, dropped))
        except SymbolicError as e:
            if e.code == "NONLINEAR":
                raise
            dropped.append(f"the case {case.steps[-1].split(', ', 1)[-1]} "
                           f"has no solution: {e.code}")
    if not out:
        raise SymbolicError("INCONSISTENT", "no case of the split has a "
                                            "solution")
    return out


def _run(st: _State, unknowns: set, targets: Sequence[str],
         dropped: List[str]) -> List[_State]:
    while True:
        _settle(st, unknowns)
        if not st.polys:
            return [st]
        ch = _choose_linear(st, unknowns, targets, strict=True)
        if ch is not None:
            _apply_linear(st, ch, unknowns)
            continue
        uni = _choose_univariate(st, unknowns)
        if uni is not None:
            _, idx, u = uni
            if st.ext and st.polys[idx][1].deg(u) >= 2 and \
                    st.polys[idx][1].vars() & _gen_names(st):
                _shrink(st, idx, u, unknowns)
                if st.polys[idx][1].deg(u) == 1:
                    continue
            i, p = st.polys[idx]
            roots, conds, notes = _roots(p, u, st)
            dropped.extend(notes)
            if not roots:
                raise SymbolicError("NO_REAL_ROOT",
                                    f"equation {i + 1} has no real root in "
                                    f"{u}")
            out: List[_State] = []
            errors: List[SymbolicError] = []
            for val, new in roots:
                st2 = st.copy()
                st2.polys.pop(idx)
                _absorb(st2, new)
                st2.conds.extend(conds)
                val = _rationalise(val, st2)
                kind = ""
                if new.algs:
                    kind = " (a real root, isolated)"
                elif new.trig:
                    kind = " (Viete's root of a cubic, three-real case)"
                elif any(k == 3 for k in new.kdeg.values()):
                    kind = " (Cardano's root of a cubic)"
                elif new.rels:
                    kind = " (a root of a quadratic)"
                if new.note:
                    st2.steps.append(new.note)
                st2.steps.append(f"from equation {i + 1}: {u} = "
                                 f"{S.to_text(val)}" + kind)
                _substitute(st2, u, val, unknowns)
                try:
                    out.extend(_run(st2, unknowns, targets, dropped))
                except SymbolicError as e:
                    if e.code == "NONLINEAR":
                        raise
                    errors.append(e)
                    dropped.append(f"branch {u} = {S.to_text(val)} "
                                   f"discarded: {e.code}")
                if len(out) > MAX_BRANCHES:
                    raise SymbolicError("NONLINEAR", "more than "
                                                     f"{MAX_BRANCHES} "
                                                     "solutions")
            if not out:
                raise errors[0]
            return out
        ch = _choose_linear(st, unknowns, targets, strict=False)
        if ch is not None:
            return _split_linear(st, ch, unknowns, targets, dropped)
        rs = _choose_resultant(st, unknowns, targets)
        if rs is not None and st.resultants < MAX_RESULTANTS:
            _, x, ip, iq = rs
            (i, p), (j, q) = st.polys[ip], st.polys[iq]
            r = _reduce(resultant(p, q, x), st)
            if r.is_zero():
                raise SymbolicError("NONLINEAR",
                                    f"equations {i + 1} and {j + 1} share a "
                                    f"factor in {x}")
            st.resultants += 1
            st.polys[iq] = (j, r)
            st.steps.append(f"{x} eliminated between equations {i + 1} and "
                            f"{j + 1} by their resultant")
            continue
        return [st]


# ===========================================================================
# 4.  THE ENTRY POINT
# ===========================================================================

@dataclass
class Branches:
    """The solutions of a system: one :class:`Solution` per branch, the
    derivation steps of each, and what was discarded on the way."""

    solutions: List[Solution]
    steps: List[List[str]]
    dropped: List[str]


@dataclass
class ExtInfo:
    """What a Phase 104 branch carries beyond a Phase 103 one: every
    generator's relation (``g^k = R``), the algebraic numbers, the order to
    reduce them in, the stated real conditions, and whether the branch needs
    the extended column-3 script (a tower, a cube root or an algebraic
    number)."""

    rels: Dict[str, Tuple[int, Poly]]
    algs: Dict[str, _Alg]
    order: List[str]
    real: List[str]
    needs_script: bool
    #: Phase 108: name -> (k, M) for a Viete root ``M t_k`` (its relation
    #: is the cubic itself; ``t_k`` is the ``k``-th largest real root)
    trig: Dict[str, Tuple[int, Poly]] = field(default_factory=dict)


def _verify(originals: List[Tuple[int, Poly]], st: _State) -> bool:
    for _, p in originals:
        v = RF(p)
        for u, val in st.values.items():
            v = _subs(v, u, val, st)
        if not _reduce(v.num, st).is_zero():
            return False
    return True


def _conditions(st: _State, unknowns: set) -> List[RF]:
    out: List[RF] = []
    for c in st.conds:
        for u, val in st.values.items():
            c = _subs(c, u, val, st)
        p = _reduce(c.num, st)
        if p.is_const() or p.vars() & (unknowns | _gen_names(st)):
            continue
        pieces = [Poly.var(v) for v, _ in p.monomial_content()]
        rest = S.divide_exact(p, Poly({p.monomial_content(): Fraction(1)}))
        if not rest.is_const():
            pieces.append(rest)
        for q in pieces:
            q = RF(q.scale(1 / q.leading()[1]))
            if all(q != d for d in out):
                out.append(q)
    return out


def _used(st: _State) -> List[str]:
    """The generators the values hold, with those their relations hold."""
    seen: List[str] = []
    todo = [g for v in st.values.values() for g in v.vars()
            if g in st.rels or g in st.algs]
    while todo:
        g = todo.pop()
        if g in seen:
            continue
        seen.append(g)
        if g in st.rels:
            todo.extend(h for h in st.rels[g].vars()
                        if (h in st.rels or h in st.algs) and h != g)
    return sorted(seen)


def _flippable(st: _State, used: List[str]) -> Tuple[List[str], List[str]]:
    """``(tops, inner)``: square roots whose sign may be flipped alone (no
    other generator's relation holds them), and square roots inside a tower
    (flipping one re-derives the generators above it)."""
    sq = [g for g in used if g in st.rels and st.kdeg.get(g, 2) == 2 and
          g not in st.fixed]
    held = {h for g in used if g in st.rels for h in st.rels[g].vars()}
    return ([g for g in sq if g not in held], [g for g in sq if g in held])


def _rename(v: RF, ren: Dict[str, RF]) -> RF:
    for g, val in ren.items():
        if g in v.vars():
            v = v.num.subs_power(g, 1, val) / v.den.subs_power(g, 1, val)
    return v


def _conjugate_inner(st: _State, g: str) -> Optional[_State]:
    """The branch with the inner square root ``g`` of a tower negated: every
    generator whose relation holds ``g`` is replaced by the root of the
    conjugate relation, bottom up (re-verified by the caller)."""
    nb = st.copy()
    ren: Dict[str, RF] = {g: -RF(Poly.var(g))}
    depth = _depth(st)
    rels: Dict[str, Poly] = {}
    kdeg: Dict[str, int] = {}
    for h in sorted(st.rels, key=lambda x: depth[x]):
        R = st.rels[h]
        k = st.kdeg.get(h, 2)
        R2 = _rename(RF(R), ren)
        R2p = R2.num.scale(1 / R2.den.const_value())
        if h == g or R2p == R:
            rels[h] = R
            if h in st.kdeg:
                kdeg[h] = k
            continue
        if k == 2 and _const_sign(R2p, nb) == -1:
            return None          # the conjugate is not real
        name = (f"sqrt({S.to_text(RF(R2p))})" if k == 2 else
                f"cbrt({S.to_text(RF(R2p))})")
        ren[h] = RF(Poly.var(name))
        rels[name] = R2p
        if k != 2:
            kdeg[name] = k
    nb.rels, nb.kdeg = rels, kdeg
    nb.values = {u: _rationalise(_rename(v, ren), nb)
                 for u, v in st.values.items()}
    return nb


def _plainly_nonnegative(R: Poly) -> bool:
    """Every term an even power with a positive coefficient."""
    return all(c > 0 and all(e % 2 == 0 for _, e in m)
               for m, c in R.t.items())


def _real_conditions(st: _State, used: List[str]) -> List[str]:
    """The conditions on the parameters under which the branch is real:
    every square root's radicand at least 0 (unless it plainly is), and
    Cardano's strict condition (it replaces the condition of its own square
    root)."""
    out: List[str] = []
    for g in used:
        if g in st.rels and st.kdeg.get(g, 2) == 2 and g not in st.fixed:
            R = st.rels[g]
            if not R.is_const() and not _plainly_nonnegative(R) and \
                    _const_sign(R, st) != 1:
                out.append(f"{S.to_text(RF(R))} >= 0")
    out.extend(i for i in st.ineqs if i not in out)
    return out


def _solution(st: _State, vals: Dict[str, RF], targets: Sequence[str],
              cs: List[RF], ext: bool) -> Solution:
    used = _used(_State([], vals, st.rels, ext=st.ext, kdeg=st.kdeg,
                        algs=st.algs))
    values = {u: (1, v) for u, v in vals.items()}
    gens = []
    for g in used:
        if g in st.rels and g not in S.RADICALS:
            values[g] = (st.kdeg.get(g, 2), RF(st.rels[g]))
            gens.append(g)
    sol = Solution(values, [], cs, tuple(targets), tuple(sorted(gens)))
    if ext:
        view = _State([], vals, st.rels, ext=True, kdeg=st.kdeg,
                      algs=st.algs, fixed=st.fixed, ineqs=st.ineqs)
        order = [g for g in reversed(_order(view)) if g in used]
        rels = {g: (st.kdeg.get(g, 2), st.rels[g]) for g in used
                if g in st.rels}
        algs = {g: st.algs[g] for g in used if g in st.algs}
        tower = any(rels[g][1].vars() & set(used) for g in rels)
        needs = bool(algs) or tower or any(k != 2 for k, _ in rels.values())
        sol.ext = ExtInfo(rels, algs, order, _real_conditions(view, used),
                          needs, {g: st.trig[g] for g in used
                                  if g in st.trig})
    return sol


def solve_nonlinear(equations: Sequence[Tuple[RF, RF]],
                    unknowns: Iterable[str], targets: Sequence[str],
                    extended: bool = True) -> Branches:
    """Every real solution of the system for ``targets``, as branches; see
    the module text.  ``extended=False`` is the layer exactly as Phase 103
    shipped it.  Raises :class:`SymbolicError` with the refusal code."""
    unknowns = (set(unknowns) | set(targets)) - S.CONSTANTS
    originals: List[Tuple[int, Poly]] = []
    conds: List[RF] = []
    for i, (lhs, rhs) in enumerate(equations):
        d = lhs - rhs
        if not d.den.is_const():
            conds.append(RF(d.den))
        originals.append((i, d.num))
    st = _State([(i, p) for i, p in originals if not p.is_zero()],
                conds=conds, ext=extended, origs=originals)
    dropped: List[str] = []
    finals = _run(st, unknowns, targets, dropped)
    sols: List[Solution] = []
    steps: List[List[str]] = []
    seen = set()
    for f in finals:
        missing = [t for t in targets if t not in f.values or
                   f.values[t].vars() & unknowns]
        if missing:
            # a branch with a free unknown is a family of solutions: the
            # other branches alone would lose it, so the system is refused
            if any(S._nonlinear(p, unknowns) for _, p in f.polys):
                raise SymbolicError("NONLINEAR",
                                    f"{', '.join(missing)} cannot be "
                                    f"isolated by elimination")
            raise SymbolicError("UNDERDETERMINED",
                                f"{', '.join(missing)} not fixed by the "
                                f"equations")
        if f.polys or not _verify(originals, f):
            dropped.append("a branch failed the substitution check "
                           "(extraneous) and was discarded")
            continue
        cs = _conditions(f, unknowns)
        if not extended:
            used = sorted(g for g in f.rels
                          if any(g in f.values[t].vars() for t in f.values))
            bases = [(f, used, [])]
        else:
            used = _used(f)
            tops, inner = _flippable(f, used)
            bases = [(f, tops, [])]
            for g in inner:
                more = []
                for b, _, note in bases:
                    nb = _conjugate_inner(b, g)
                    if nb is None:
                        dropped.append(f"the conjugate of {g} is not real "
                                       f"(a radicand below 0)")
                    elif _verify(originals, nb):
                        more.append((nb, _flippable(nb, _used(nb))[0],
                                     note + [g]))
                    else:
                        dropped.append(f"the conjugate of {g} failed the "
                                       f"substitution check")
                bases.extend(more)
        for b, flip, inner_note in bases:
            for signs in product((1, -1), repeat=len(flip)):
                vals = dict(b.values)
                for g, sg in zip(flip, signs):
                    if sg < 0:
                        vals = {u: _flip_rf(v, g) for u, v in vals.items()}
                key = tuple(S.to_text(vals[u]) for u in
                            (sorted(vals) if not extended else targets))
                if key in seen:
                    continue
                seen.add(key)
                if not extended:
                    values = {u: (1, v) for u, v in vals.items()}
                    gens = []
                    for g in flip:
                        if g not in S.RADICALS:
                            values[g] = (2, RF(b.rels[g]))
                            gens.append(g)
                    sols.append(Solution(values, [], cs, tuple(targets),
                                         tuple(sorted(gens))))
                else:
                    sols.append(_solution(b, vals, targets, cs, True))
                if not extended:
                    steps.append(list(b.steps) +
                                 ([f"the conjugate root (sign of "
                                   f"{', '.join(flip)} flipped)"]
                                  if any(s < 0 for s in signs) else []))
                    continue
                flipped = [g for g, s in zip(flip, signs) if s < 0]
                steps.append(list(b.steps) +
                             ([f"the conjugate root (sign of "
                               f"{', '.join(inner_note + flipped)} flipped)"]
                              if inner_note or flipped else []))
    if not sols:
        raise SymbolicError("NONLINEAR", "no branch survived the "
                                         "substitution check")
    if len(sols) > MAX_BRANCHES:
        raise SymbolicError("NONLINEAR", f"more than {MAX_BRANCHES} "
                                         f"solutions")
    return Branches(sols, steps, dropped)


# ===========================================================================
# 5.  APPROXIMATE VALUES AND THE EXTENDED COLUMN-3 SCRIPT
# ===========================================================================

def approximate(sol: Solution, t: str, digits: int = 6) -> Optional[str]:
    """A decimal for a target whose value is a polynomial in one algebraic
    number (exact interval arithmetic on a narrowed interval), else
    ``None``.  Shown beside the exact answer; it is not the answer."""
    ext = getattr(sol, "ext", None)
    if ext is None or not ext.algs:
        return None
    v = sol.values[t][1]
    held = v.vars()
    if len(held) > 1 or (held and not held <= set(ext.algs)):
        return None
    if not v.den.is_const():
        return None
    if not held:
        return None
    g = next(iter(held))
    a = ext.algs[g]
    lo, hi = A.refine(a.m, a.lo, a.hi, Fraction(1, 10 ** (digits + 6)))
    cs = v.num.coeffs(g)
    up = [cs[i].const_value() if i in cs else Fraction(0)
          for i in range(v.num.deg(g) + 1)]
    x = A.peval(up, (lo + hi) / 2) / v.den.const_value()
    scaled = round(x * 10 ** digits)
    sign = "-" if scaled < 0 else ""
    s = str(abs(scaled)).rjust(digits + 1, "0")
    return f"{sign}{s[:-digits]}.{s[-digits:]}"


EXT_PRELUDE = '''from fractions import Fraction as F


class G:
    """A polynomial in formal generators; REL[g] = (k, value) replaces g^k
    by value (which may hold g in lower powers, or other generators)."""
    REL = {}

    def __init__(self, t=None):
        self.t = {m: F(c) for m, c in (t or {}).items() if c}

    @staticmethod
    def c(x):
        return x if isinstance(x, G) else G({(): F(x)})

    @staticmethod
    def gen(name):
        return G({((name, 1),): 1})

    def raw_mul(self, o):
        t = {}
        for m1, c1 in self.t.items():
            for m2, c2 in o.t.items():
                d = dict(m1)
                for v, e in m2:
                    d[v] = d.get(v, 0) + e
                mm = tuple(sorted(d.items()))
                t[mm] = t.get(mm, 0) + c1 * c2
        return G(t)

    def red(self):
        t = dict(self.t)
        for _ in range(10000):
            out = {}
            hit = False
            for m, c in t.items():
                d = dict(m)
                rule = None
                for v, e in d.items():
                    if v in G.REL and e >= G.REL[v][0]:
                        rule = v
                        break
                if rule is None:
                    out[m] = out.get(m, 0) + c
                    continue
                hit = True
                k, val = G.REL[rule]
                d[rule] -= k
                if not d[rule]:
                    del d[rule]
                rest = G({tuple(sorted(d.items())): c}).raw_mul(val)
                for mm, cc in rest.t.items():
                    out[mm] = out.get(mm, 0) + cc
            t = {m: c for m, c in out.items() if c}
            if not hit:
                return G(t)
        raise ValueError("the relations do not reduce")

    def __add__(self, o):
        o = G.c(o)
        t = dict(self.t)
        for m, c in o.t.items():
            t[m] = t.get(m, 0) + c
        return G(t)

    __radd__ = __add__

    def __neg__(self):
        return G({m: -c for m, c in self.t.items()})

    def __sub__(self, o):
        return self + (-G.c(o))

    def __rsub__(self, o):
        return G.c(o) - self

    def __mul__(self, o):
        return self.raw_mul(G.c(o)).red()

    __rmul__ = __mul__

    def __truediv__(self, o):
        o = G.c(o).red()
        if set(o.t) - {()}:
            raise ValueError("division by a generator")
        return self * (1 / o.t[()])

    def __rtruediv__(self, o):
        return G.c(o) / self

    def __pow__(self, n):
        out = G.c(1)
        for _ in range(n):
            out = out * self
        return out

    def zero(self):
        return not self.red().t


ENV = {"F": F, "__builtins__": {}}


def ev(expr, point):
    return G.c(eval(expr, ENV, point))


def sturm_count(m, lo, hi):
    """Distinct real roots of the squarefree m in (lo, hi] (Sturm)."""
    def ev1(p, x):
        v = F(0)
        for c in reversed(p):
            v = v * x + c
        return v

    def rem(a, b):
        a = list(a)
        while len(a) >= len(b) and a:
            c = a[-1] / b[-1]
            s = len(a) - len(b)
            for i, y in enumerate(b):
                a[s + i] -= c * y
            while a and a[-1] == 0:
                a.pop()
        return a

    chain = [list(m), [i * m[i] for i in range(1, len(m))]]
    while True:
        r = rem(chain[-2], chain[-1])
        if not r:
            break
        chain.append([-c for c in r])

    def var(x):
        s = [ev1(p, x) for p in chain]
        s = [v for v in s if v != 0]
        return sum(1 for a, b in zip(s, s[1:]) if (a > 0) != (b > 0))

    return var(lo) - var(hi)
'''

EXT_CHECK = '''
for name, m, lo, hi in ALGS:
    assert sturm_count(m, lo, hi) == 1, name
checked = 0
for base in POINTS:
    G.REL = {}
    P = {k: G.c(v) for k, v in base.items()}
    for name, k, rel in GENS:
        P[name] = G.gen(name)
    for name, k, rel in GENS:
        G.REL[name] = (k, ev(rel, P).red())
    for name, expr in VALUES:
        P[name] = ev(expr, P)
    for lhs, rhs in LAWS:
        assert (ev(lhs, P) - ev(rhs, P)).zero(), (lhs, rhs)
    for name, expr in ANSWERS:
        assert (P[name] - ev(expr, P)).zero(), name
    checked += 1
assert checked >= min(3, len(POINTS)) and checked >= 1, checked
'''

# Phase 108: a Viete root's relation is its cubic ``y^3 + c1 y + c0``; at
# every point where the cubic's discriminant is positive, Sturm's theorem
# must count three real roots (the claim the trigonometric form rests on).
TRIG_CHECK = '''
trig_checked = 0
for base in TRIG_POINTS:
    for name, k, e1, e0 in TRIG:
        c1, c0 = F(eval(e1, ENV, dict(base))), F(eval(e0, ENV, dict(base)))
        disc = -(4 * c1 ** 3 + 27 * c0 ** 2)
        if disc > 0:
            bound = 1 + (c1 if c1 > 0 else -c1) + (c0 if c0 > 0 else -c0)
            assert sturm_count([c0, c1, F(0), F(1)], -bound, bound) == 3, name
            trig_checked += 1
assert trig_checked >= 1, trig_checked
'''


def branch_script(equation_texts: Sequence[str], sol: Solution, ctx,
                  params: Iterable[str], answer_texts: Dict[str, str],
                  label: str = "BRANCH", points: int = 6, seed: int = 104,
                  scale_first: Optional[Fraction] = None) -> str:
    """The column-3 check of a Phase 104 branch: a stand-alone script that
    carries every generator formally with its own relation (a square root
    or cube root whose radicand may hold a lower generator, an algebraic
    number reduced by its polynomial), checks by Sturm's theorem that each
    algebraic number's interval holds exactly one root of its polynomial,
    and asserts every law **as written** and every **printed** answer at
    rational points of the parameters."""
    ext: ExtInfo = sol.ext
    gens = list(ext.order)
    symbols = set(params) | set(sol.values) | set(ctx.atoms) | set(gens)
    for e in equation_texts:
        for lr in e.split("="):
            symbols |= S.parse(lr, S.Context()).vars()
    symbols |= set(S.RADICALS)
    names = S.py_names(symbols)
    # every radical atom a value or a relation holds is a generator too
    rad = set()
    for u, (k, v) in sol.values.items():
        rad |= v.vars() & set(S.RADICALS)
    for k, R in ext.rels.values():
        rad |= R.vars() & set(S.RADICALS)
    gen_rows = []
    for r in sorted(rad):
        q, b = S.RADICALS[r]
        gen_rows.append((names[r], q, f"F({b.numerator}, {b.denominator})"))
    for g in gens:
        if g in S.RADICALS:
            continue
        if g in ext.algs:
            a = ext.algs[g]
            d = len(a.m) - 1
            rel = Poly()
            for i, c in enumerate(a.m[:-1]):
                if c:
                    rel = rel + Poly.var(g, i).scale(-c)
            gen_rows.append((names[g], d, S.to_python(RF(rel), names)))
        else:
            k, R = ext.rels[g]
            gen_rows.append((names[g], k, S.to_python(RF(R), names)))
    free = sorted((set(params) | set(ctx.atoms)) - set(sol.values) -
                  set(gens) - set(S.RADICALS))
    lcg = S.Lcg(seed)
    pts = []
    tries = 0
    while len(pts) < (points if free else 1) and tries < 400:
        tries += 1
        P = {p: lcg.rational() for p in free}
        try:
            for u, (k, v) in sol.values.items():
                if v.den.vars() <= set(P) and v.den.evaluate(P) == 0:
                    raise ZeroDivisionError
            for c in sol.conditions:
                if c.vars() <= set(P) and c.evaluate(P) == 0:
                    raise ZeroDivisionError
            for k, R in ext.rels.values():
                if R.vars() <= set(P) and R.evaluate(P) == 0:
                    raise ZeroDivisionError
        except ZeroDivisionError:
            continue
        pts.append(P)
    vals = []
    for u in sorted(t for t in sol.values if sol.values[t][0] == 1):
        v = sol.values[u][1]
        if scale_first is not None and u == sol.targets[0]:
            v = v * scale_first
        vals.append((names[u], S.to_python(v, names)))
    tr_names = dict(names)
    ans = []
    for t in sol.targets:
        text = answer_texts[t]
        for g in sorted(gens, key=len, reverse=True):
            text = text.replace(g, names[g])
        for g in gens:
            tr_names[names[g]] = names[g]
        ans.append((names[t], S.transliterate(text, tr_names)))
    algs = []
    for g, a in ext.algs.items():
        algs.append(f"({names[g]!r}, [" + ", ".join(
            f"F({c.numerator}, {c.denominator})" for c in a.m) + "], "
            f"F({a.lo.numerator}, {a.lo.denominator}), "
            f"F({a.hi.numerator}, {a.hi.denominator}))")
    lines = [EXT_PRELUDE]
    lines.append("LAWS = " + repr([(S.transliterate(a, names),
                                    S.transliterate(b, names))
                                   for a, b in (e.split("=")
                                                for e in equation_texts)]))
    lines.append("GENS = " + repr(gen_rows))
    lines.append("ALGS = [" + ", ".join(algs) + "]")
    lines.append("VALUES = " + repr(vals))
    lines.append("ANSWERS = " + repr(ans))
    pt_lines = []
    for P in pts:
        pt_lines.append("    {" + ", ".join(
            f"{names[k]!r}: F({v.numerator}, {v.denominator})"
            for k, v in sorted(P.items()) if k in names) + "},")
    lines.append("POINTS = [\n" + "\n".join(pt_lines) + "\n]")
    lines.append(EXT_CHECK)
    if ext.trig:
        rows = []
        for g, (k, _M) in sorted(ext.trig.items()):
            cs = ext.rels[g][1].coeffs(g)
            rows.append((names[g], k,
                         S.to_python(-RF(cs.get(1, Poly())), names),
                         S.to_python(-RF(cs.get(0, Poly())), names)))
        lines.append("TRIG = " + repr(rows))
        # sharpening pass: the three-real regime may need letters below
        # zero (x^3 + p*x = q needs p < 0), which the positive points of
        # the formal check never reach -- signed points where every Viete
        # cubic's discriminant is positive are drawn for this check
        tpts = []
        tl = S.Lcg(seed + 1)
        tvars = sorted({v for g in ext.trig
                        for v in ext.rels[g][1].vars()} - {g for g in ext.trig}
                       - set(gens))
        for _ in range(600):
            if len(tpts) >= points:
                break
            Pt = {v: tl.rational() * (1 if tl.next() % 2 else -1)
                  for v in tvars}
            ok = True
            for g in ext.trig:
                cs = ext.rels[g][1].coeffs(g)
                try:
                    c1 = -cs.get(1, Poly()).evaluate(Pt)
                    c0 = -cs.get(0, Poly()).evaluate(Pt)
                except (KeyError, ZeroDivisionError):
                    ok = False
                    break
                if -(4 * c1 ** 3 + 27 * c0 ** 2) <= 0:
                    ok = False
                    break
            if ok:
                tpts.append(Pt)
        tp_lines = ["    {" + ", ".join(
            f"{names[k]!r}: F({v.numerator}, {v.denominator})"
            for k, v in sorted(Pt.items()) if k in names) + "},"
            for Pt in tpts]
        lines.append("TRIG_POINTS = POINTS + [\n" + "\n".join(tp_lines) +
                     "\n]")
        lines.append(TRIG_CHECK)
    lines.append(f"print(f'{label} POINTS={{checked}} LAWS={{len(LAWS)}} "
                 f"VERIFIED True')")
    return "\n".join(lines)
