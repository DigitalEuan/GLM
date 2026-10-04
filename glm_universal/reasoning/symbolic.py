"""``glm_universal.reasoning.symbolic`` -- exact algebra over named
parameters (Phase 98, ``studies/SYMBOLIC_PARAMETERS_STUDY.md``).

Why it exists
-------------
Phase 89's outside question set located a boundary the exact layer could not
cross: thirteen questions whose answer is a *formula in letters* --
``a = (2/3) g sin(theta)``, ``M = m0 sqrt(2(1 + gamma))``,
``Y/D = Gd Gp / (1 + Gc Gv Gp Gm)``.  Every algebra of the machine computed
with numbers.  This module computes with letters, and with nothing else than
the substrate's own arithmetic: integers and :class:`fractions.Fraction`
(D7), no floats, no outside library.

What it holds
-------------
* :class:`Poly` -- a polynomial over the rationals in named variables, with
  exact division (:func:`divide_exact`) and a greatest common divisor
  (:func:`poly_gcd`, recursive primitive pseudo-remainder sequences).
* :class:`RF` -- a rational function, always stored in lowest terms, so two
  rational functions are equal exactly when their stored forms are.
* :class:`Context` and :func:`parse` -- a small reader for formulas written
  the way the questions write them (``M*g*sin(theta) - f``, ``1/R1 + 1/R2``,
  ``2^(-2/3)``).  ``sin``/``cos``/``tan`` of a term, ``exp``, ``ln`` and
  ``sqrt`` are *atoms*: variables the context remembers, with the relation or
  derivative each carries.  A rational power of a rational number is a
  *radical atom* with its defining relation ``r^q = c``, reduced on every
  product.
* :func:`solve_system` -- elimination by **declared substitution**: an
  equation that reads ``A u^k + B = 0`` with ``A`` free of every unknown and
  ``B`` free of ``u`` defines ``u^k``, provided every other occurrence of
  ``u`` is a power of ``u^k``; the definition is substituted everywhere, and
  the step is repeated.  Each step is an equivalence (given ``A != 0``,
  recorded as a condition), so the solution is the system's.  What cannot be
  isolated is refused by name: ``NONLINEAR``, ``UNDERDETERMINED``,
  ``INCONSISTENT``, ``OVERDETERMINED``, ``NOT_IN_SYSTEM``, ``UNREADABLE``.
* :func:`diff` -- differentiation through the atoms' declared derivatives.
* :func:`entails` -- a claimed relation follows from derived relations when
  its numerator is an exact multiple of one of them.
* :func:`system_script` -- the column-3 check of a solution: a stand-alone
  standard-library script that evaluates **the laws as written** at rational
  points, with every unknown that is only known through a root carried as a
  formal generator reduced by its own relation, and asserts every law and
  every answer.  It shares no code with this module.

``RequestProject/GLM/SymbolicParameters.lean`` proves the identities the
outside frames rest on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = ["Poly", "RF", "Context", "parse", "parse_equation", "SymbolicError",
           "solve_system", "Solution", "diff", "entails", "to_text",
           "to_python", "system_script", "radical_atom", "normalise_text",
           "poly_gcd", "divide_exact", "Lcg", "evaluate"]

Mono = Tuple[Tuple[str, int], ...]


class SymbolicError(Exception):
    """A refusal of the symbolic layer, with the machine's code."""

    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
# 1.  POLYNOMIALS
# ===========================================================================

def _mono_mul(a: Mono, b: Mono) -> Mono:
    if not a:
        return b
    if not b:
        return a
    d = dict(a)
    for v, e in b:
        d[v] = d.get(v, 0) + e
    return tuple(sorted((v, e) for v, e in d.items() if e))


def _mono_key(m: Mono):
    return (sum(e for _, e in m), tuple((v, e) for v, e in m))


class Poly:
    """A polynomial over the rationals in named variables (immutable)."""

    __slots__ = ("t",)

    def __init__(self, terms: Optional[Dict[Mono, Fraction]] = None):
        self.t: Dict[Mono, Fraction] = {}
        if terms:
            for m, c in terms.items():
                if c:
                    self.t[m] = Fraction(c)

    # -- construction -----------------------------------------------------
    @staticmethod
    def const(c) -> "Poly":
        return Poly({(): Fraction(c)})

    @staticmethod
    def var(name: str, e: int = 1) -> "Poly":
        return Poly({((name, e),): Fraction(1)}) if e else Poly.const(1)

    # -- queries ----------------------------------------------------------
    def is_zero(self) -> bool:
        return not self.t

    def is_const(self) -> bool:
        return not self.t or (len(self.t) == 1 and () in self.t)

    def const_value(self) -> Fraction:
        return self.t.get((), Fraction(0)) if self.is_const() else None

    def vars(self) -> set:
        return {v for m in self.t for v, _ in m}

    def deg(self, v: str) -> int:
        return max((dict(m).get(v, 0) for m in self.t), default=0)

    def total_degree(self) -> int:
        return max((sum(e for _, e in m) for m in self.t), default=0)

    def coeffs(self, v: str) -> Dict[int, "Poly"]:
        out: Dict[int, Dict[Mono, Fraction]] = {}
        for m, c in self.t.items():
            d = dict(m)
            e = d.pop(v, 0)
            rest = tuple(sorted(d.items()))
            out.setdefault(e, {})[rest] = c
        return {e: Poly(t) for e, t in out.items()}

    def lc(self, v: str) -> "Poly":
        return self.coeffs(v).get(self.deg(v), Poly())

    def leading(self) -> Tuple[Mono, Fraction]:
        m = max(self.t, key=_mono_key)
        return m, self.t[m]

    def exponents(self, v: str) -> set:
        return {dict(m).get(v, 0) for m in self.t}

    # -- arithmetic -------------------------------------------------------
    def __add__(self, o):
        o = _P(o)
        t = dict(self.t)
        for m, c in o.t.items():
            t[m] = t.get(m, 0) + c
        return Poly(t)

    __radd__ = __add__

    def __neg__(self):
        return Poly({m: -c for m, c in self.t.items()})

    def __sub__(self, o):
        return self + (-_P(o))

    def __rsub__(self, o):
        return _P(o) - self

    def __mul__(self, o):
        o = _P(o)
        t: Dict[Mono, Fraction] = {}
        for m1, c1 in self.t.items():
            for m2, c2 in o.t.items():
                m = _mono_mul(m1, m2)
                t[m] = t.get(m, 0) + c1 * c2
        return Poly(t)

    __rmul__ = __mul__

    def __pow__(self, n: int):
        if n < 0:
            raise ValueError("negative power of a polynomial")
        out, base = Poly.const(1), self
        while n:
            if n & 1:
                out = out * base
            base = base * base
            n >>= 1
        return out

    def scale(self, c) -> "Poly":
        c = Fraction(c)
        return Poly({m: v * c for m, v in self.t.items()})

    def __eq__(self, o):
        return isinstance(o, Poly) and self.t == o.t

    def __hash__(self):
        return hash(frozenset(self.t.items()))

    def __repr__(self):
        return f"Poly({to_text(RF(self))})"

    # -- evaluation and substitution --------------------------------------
    def evaluate(self, point: Dict[str, Fraction]):
        total = Fraction(0)
        for m, c in self.t.items():
            term = c
            for v, e in m:
                term = term * point[v] ** e
            total = total + term
        return total

    def subs_power(self, v: str, k: int, value: "RF") -> "RF":
        """Replace ``v^(k j)`` by ``value^j``; every exponent of ``v`` must be
        a multiple of ``k``."""
        out = RF(Poly())
        for e, c in self.coeffs(v).items():
            if e % k:
                raise SymbolicError("NONLINEAR", f"{v}^{e} is not a power of "
                                                 f"{v}^{k}")
            out = out + RF(c) * value ** (e // k)
        return out

    def reduce_power(self, v: str, k: int, value: "RF") -> "RF":
        """Reduce every ``v^e`` to ``value^(e // k) v^(e % k)``."""
        out = RF(Poly())
        for e, c in self.coeffs(v).items():
            q, r = divmod(e, k)
            out = out + RF(c * Poly.var(v, r)) * value ** q
        return out

    def content(self) -> Fraction:
        """The positive rational ``c`` with ``self / c`` integral and
        primitive."""
        if not self.t:
            return Fraction(1)
        num = 0
        den = 1
        for c in self.t.values():
            num = gcd(num, c.numerator)
            den = den * c.denominator // gcd(den, c.denominator)
        return Fraction(num, den)

    def monomial_content(self) -> Mono:
        if not self.t:
            return ()
        ms = list(self.t)
        common = dict(ms[0])
        for m in ms[1:]:
            d = dict(m)
            common = {v: min(e, d.get(v, 0)) for v, e in common.items()}
        return tuple(sorted((v, e) for v, e in common.items() if e))


def _P(o) -> Poly:
    if isinstance(o, Poly):
        return o
    if isinstance(o, (int, Fraction)):
        return Poly.const(o)
    raise TypeError(f"not a polynomial: {o!r}")


def divide_exact(a: Poly, b: Poly) -> Optional[Poly]:
    """``q`` with ``a == q * b``, or ``None`` when ``b`` does not divide
    ``a``."""
    if b.is_zero():
        raise ZeroDivisionError("division by the zero polynomial")
    if a.is_zero():
        return Poly()
    if b.is_const():
        return a.scale(1 / b.const_value())
    v = max(b.vars())
    if v not in a.vars():
        return None
    db, lb = b.deg(v), b.lc(v)
    q, r = Poly(), a
    while not r.is_zero() and r.deg(v) >= db:
        dr, lr = r.deg(v), r.lc(v)
        c = divide_exact(lr, lb)
        if c is None:
            return None
        t = c * Poly.var(v, dr - db)
        q = q + t
        r = r - t * b
    return q if r.is_zero() else None


def _monic(a: Poly) -> Poly:
    if a.is_zero():
        return a
    return a.scale(1 / a.leading()[1])


def _content_in(a: Poly, v: str) -> Poly:
    g = Poly()
    for c in a.coeffs(v).values():
        g = poly_gcd(g, c)
        if g.is_const() and not g.is_zero():
            return Poly.const(1)
    return g


def _prem(a: Poly, b: Poly, v: str) -> Poly:
    db, lb = b.deg(v), b.lc(v)
    r = a
    while not r.is_zero() and v in r.vars() and r.deg(v) >= db:
        dr, lr = r.deg(v), r.lc(v)
        r = lb * r - lr * Poly.var(v, dr - db) * b
    return r


def _uni(p: Poly, v: str, point: Dict[str, Fraction]) -> List[Fraction]:
    """``p`` with every variable but ``v`` set from ``point``, as dense
    coefficients (constant first)."""
    out: List[Fraction] = [Fraction(0)] * (p.deg(v) + 1)
    for m, c in p.t.items():
        e = 0
        term = c
        for x, k in m:
            if x == v:
                e = k
            else:
                term = term * point[x] ** k
        out[e] += term
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def _uni_gcd_degree(a: List[Fraction], b: List[Fraction]) -> int:
    """Degree of the gcd of two dense univariate polynomials over Q."""
    def trim(x):
        while len(x) > 1 and x[-1] == 0:
            x.pop()
        return x
    a, b = trim(list(a)), trim(list(b))
    if len(a) < len(b):
        a, b = b, a
    while not (len(b) == 1 and b[0] == 0):
        if len(b) == 1:
            return 0
        r = list(a)
        while len(r) >= len(b) and not (len(r) == 1 and r[0] == 0):
            f = r[-1] / b[-1]
            sh = len(r) - len(b)
            for i, c in enumerate(b):
                r[sh + i] -= f * c
            r = trim(r)
            if len(r) == 1 and r[0] == 0:
                break
        a, b = b, r
    return len(a) - 1


_GCD_POINTS = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)


def _gcd_is_trivial(a: Poly, b: Poly) -> bool:
    """A sound certificate that ``gcd(a, b)`` is a constant: for every
    variable ``v``, setting the others to values where neither leading
    coefficient in ``v`` vanishes leaves univariate polynomials with no
    common factor (specialisation cannot lower the gcd's degree in ``v``)."""
    vs = sorted(a.vars() | b.vars())
    point = {x: Fraction(_GCD_POINTS[i % len(_GCD_POINTS)] + i // 14, 1 +
                         (i % 3)) for i, x in enumerate(vs)}
    for v in vs:
        if v not in a.vars() or v not in b.vars():
            continue
        if a.lc(v).evaluate(point) == 0 or b.lc(v).evaluate(point) == 0:
            return False
        if _uni_gcd_degree(_uni(a, v, point), _uni(b, v, point)) > 0:
            return False
    return True


def poly_gcd(a: Poly, b: Poly) -> Poly:
    """A greatest common divisor, monic in the leading monomial."""
    if a.is_zero():
        return _monic(b)
    if b.is_zero():
        return _monic(a)
    if a.is_const() or b.is_const():
        return Poly.const(1)
    if not (a.vars() & b.vars()):
        # no shared variable: only a common factor in the shared-free
        # contents could remain, i.e. monomial-free polynomials are coprime
        pass
    elif _gcd_is_trivial(a, b):
        ma, mb = a.monomial_content(), b.monomial_content()
        if not ma or not mb:
            return Poly.const(1)
    v = max(a.vars() | b.vars())
    if v not in a.vars():
        return poly_gcd(a, _content_in(b, v))
    if v not in b.vars():
        return poly_gcd(_content_in(a, v), b)
    ca, cb = _content_in(a, v), _content_in(b, v)
    pa, pb = divide_exact(a, ca), divide_exact(b, cb)
    c = poly_gcd(ca, cb)
    if pa.deg(v) < pb.deg(v):
        pa, pb = pb, pa
    while not pb.is_zero():
        if v not in pb.vars():
            pa = Poly.const(1)
            break
        r = _prem(pa, pb, v)
        if not r.is_zero():
            if v not in r.vars():
                pa = Poly.const(1)
                break
            r = divide_exact(r, _content_in(r, v))
        pa, pb = pb, r
    g = divide_exact(pa, _content_in(pa, v)) if v in pa.vars() else \
        Poly.const(1)
    return _monic(c * g)


# ===========================================================================
# 2.  RATIONAL FUNCTIONS
# ===========================================================================

class RF:
    """A rational function in lowest terms: the denominator is integral,
    primitive and has a positive leading coefficient."""

    __slots__ = ("num", "den")

    def __init__(self, num, den=None, _reduced: bool = False):
        num = _P(num)
        den = Poly.const(1) if den is None else _P(den)
        if den.is_zero():
            raise ZeroDivisionError("rational function with zero denominator")
        if not _reduced:
            num, den = _reduce_radicals(num), _reduce_radicals(den)
            if num.is_zero():
                den = Poly.const(1)
            else:
                g = poly_gcd(num, den)
                if not g.is_const():
                    num, den = divide_exact(num, g), divide_exact(den, g)
            s = 1 / den.content()
            if den.leading()[1] < 0:
                s = -s
            num, den = num.scale(s), den.scale(s)
        self.num, self.den = num, den

    @staticmethod
    def of(x) -> "RF":
        return x if isinstance(x, RF) else RF(_P(x))

    def is_zero(self) -> bool:
        return self.num.is_zero()

    def is_const(self) -> bool:
        return self.num.is_const() and self.den.is_const()

    def const_value(self) -> Optional[Fraction]:
        if not self.is_const():
            return None
        return self.num.const_value() / self.den.const_value()

    def vars(self) -> set:
        return self.num.vars() | self.den.vars()

    def __add__(self, o):
        o = RF.of(o)
        return RF(self.num * o.den + o.num * self.den, self.den * o.den)

    __radd__ = __add__

    def __neg__(self):
        return RF(-self.num, self.den, _reduced=True)

    def __sub__(self, o):
        return self + (-RF.of(o))

    def __rsub__(self, o):
        return RF.of(o) - self

    def __mul__(self, o):
        o = RF.of(o)
        return RF(self.num * o.num, self.den * o.den)

    __rmul__ = __mul__

    def __truediv__(self, o):
        o = RF.of(o)
        if o.is_zero():
            raise ZeroDivisionError("division by zero")
        return RF(self.num * o.den, self.den * o.num)

    def __rtruediv__(self, o):
        return RF.of(o) / self

    def __pow__(self, n: int):
        if n >= 0:
            return RF(self.num ** n, self.den ** n)
        return RF(self.den ** (-n), self.num ** (-n))

    def __eq__(self, o):
        if not isinstance(o, RF):
            try:
                o = RF.of(o)
            except TypeError:
                return False
        return (self - o).is_zero()

    def __hash__(self):
        return hash((self.num, self.den))

    def __repr__(self):
        return f"RF({to_text(self)})"

    def evaluate(self, point: Dict[str, Fraction]) -> Fraction:
        d = self.den.evaluate(point)
        if d == 0:
            raise ZeroDivisionError("denominator vanishes at the point")
        return self.num.evaluate(point) / d


def evaluate(rf: RF, point: Dict[str, Fraction]) -> Fraction:
    return rf.evaluate(point)


# ===========================================================================
# 3.  ATOMS AND RADICALS
# ===========================================================================

#: radical atom name -> (q, c): the atom is the positive real c^(1/q).
RADICALS: Dict[str, Tuple[int, Fraction]] = {}


def _factor_int(n: int) -> Dict[int, int]:
    out: Dict[int, int] = {}
    p = 2
    while p * p <= n and p < 100000:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def _int_root(n: int, k: int) -> Optional[int]:
    if n < 0:
        if k % 2 == 0:
            return None
        r = _int_root(-n, k)
        return None if r is None else -r
    lo, hi = 0, 1
    while hi ** k <= n:
        hi *= 2
    while lo < hi:
        mid = (lo + hi) // 2
        if mid ** k < n:
            lo = mid + 1
        else:
            hi = mid
    return lo if lo ** k == n else None


def rational_root(c: Fraction, k: int) -> Optional[Fraction]:
    a, b = _int_root(c.numerator, k), _int_root(c.denominator, k)
    return None if a is None or b is None else Fraction(a, b)


def radical_atom(c: Fraction, p: int, q: int) -> RF:
    """``c^(p/q)`` for a positive rational ``c``, as a rational multiple of a
    power of the radical atom ``c0^(1/q0)`` (printed by primes)."""
    c = Fraction(c)
    if c <= 0:
        raise SymbolicError("UNSUPPORTED_POWER",
                            "a fractional power of a non-positive number")
    g = gcd(p, q)
    p, q = p // g, q // g
    if q < 0:
        p, q = -p, -q
    if q == 1:
        return RF(Poly.const(c ** p))
    # c^(p/q) = prod prime^(e p / q); split the integer part out
    fac = {pr: e for pr, e in _factor_int(c.numerator).items()}
    for pr, e in _factor_int(c.denominator).items():
        fac[pr] = fac.get(pr, 0) - e
    whole = Fraction(1)
    rest = {}
    for pr, e in fac.items():
        n = e * p
        w = n // q if n >= 0 else -((-n) // q)
        r = n - w * q
        whole *= Fraction(pr) ** w
        if r:
            rest[pr] = r
    if not rest:
        return RF(Poly.const(whole))
    # rest: prod pr^(r/q), 0 < r < q; reduce the common denominator
    g = q
    for r in rest.values():
        g = gcd(g, r)
    q2 = q // g
    base = Fraction(1)
    for pr, r in rest.items():
        base *= Fraction(pr) ** (r // g)
    if base < 1 and base.numerator != 1:
        pass
    name = _radical_name(base, q2)
    RADICALS[name] = (q2, base)
    return RF(Poly.var(name).scale(whole))


def _radical_name(base: Fraction, q: int) -> str:
    fac = dict(_factor_int(base.numerator))
    for pr, e in _factor_int(base.denominator).items():
        fac[pr] = fac.get(pr, 0) - e
    fac = {pr: e for pr, e in fac.items() if e}
    if len(fac) == 1:
        (pr, e), = fac.items()
        g = gcd(abs(e), q)
        return f"{pr}^({e // g}/{q // g})"
    return f"({base})^(1/{q})"


def _reduce_radicals(p: Poly) -> Poly:
    if not RADICALS or not (p.vars() & set(RADICALS)):
        return p
    t: Dict[Mono, Fraction] = {}
    for m, c in p.t.items():
        d = dict(m)
        for v in list(d):
            if v in RADICALS:
                q, base = RADICALS[v]
                e = d[v]
                if e >= q or e < 0:
                    w, r = divmod(e, q)
                    c = c * base ** w
                    if r:
                        d[v] = r
                    else:
                        del d[v]
        mm = tuple(sorted(d.items()))
        t[mm] = t.get(mm, 0) + c
    return Poly(t)


@dataclass
class Atom:
    """A named non-polynomial object: ``kind`` is ``sin``/``cos``/``exp``/
    ``ln``/``sqrt``/``func``; ``arg`` the argument as a rational function."""

    name: str
    kind: str
    arg: Optional[RF] = None


@dataclass
class Context:
    """The atoms a reading has met, by name."""

    atoms: Dict[str, Atom] = field(default_factory=dict)

    def atom(self, kind: str, arg: RF) -> RF:
        name = f"{kind}({to_text(arg)})"
        if name not in self.atoms:
            self.atoms[name] = Atom(name, kind, arg)
        return RF(Poly.var(name))

    def trig_pairs(self) -> List[Tuple[str, str]]:
        """``(sin name, cos name)`` for every argument with a sine or cosine
        atom (both atoms are created)."""
        out = []
        for a in list(self.atoms.values()):
            if a.kind == "sin":
                self.atom("cos", a.arg)
            elif a.kind == "cos":
                self.atom("sin", a.arg)
        for a in self.atoms.values():
            if a.kind == "sin":
                out.append((a.name, f"cos({to_text(a.arg)})"))
        return sorted(out)


# ===========================================================================
# 4.  READING FORMULAS
# ===========================================================================

_GREEK = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
          "ε": "epsilon", "ϵ": "epsilon", "θ": "theta", "λ": "lambda",
          "μ": "mu", "ν": "nu", "ρ": "rho", "σ": "sigma", "τ": "tau",
          "φ": "phi", "ϕ": "phi", "ω": "omega", "π": "pi", "Δ": "Delta",
          "Ω": "Omega", "η": "eta", "κ": "kappa", "ξ": "xi", "ψ": "psi",
          "χ": "chi", "ζ": "zeta"}
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def normalise_text(text: str) -> str:
    """Unicode operators, Greek letters and super/subscripts as ASCII."""
    t = text
    for a, b in (("−", "-"), ("–", "-"), ("×", "*"), ("·", "*"), ("⋅", "*")):
        t = t.replace(a, b)
    t = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+",
               lambda m: "^" + m.group(0).translate(_SUP), t)
    t = re.sub(r"[₀₁₂₃₄₅₆₇₈₉]+", lambda m: m.group(0).translate(_SUB), t)
    for g, n in _GREEK.items():
        t = re.sub(g + r"(?=[A-Za-z0-9_])", n + "_", t)
        t = t.replace(g, n)
    return t


_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|"
                    r"(\*\*|[-+*/^(),]))")
FUNCTIONS = ("sin", "cos", "tan", "exp", "ln", "sqrt")


def _tokens(text: str) -> List[Tuple[str, str, bool]]:
    """``(kind, text, spaced_before)`` tokens."""
    out = []
    i = 0
    text = text.rstrip()
    while i < len(text):
        m = _TOKEN.match(text, i)
        if not m or m.end() == i:
            raise SymbolicError("UNREADABLE", f"cannot read {text[i:i+12]!r}")
        spaced = m.start(0) != (m.start(1) if m.group(1) else
                                m.start(2) if m.group(2) else m.start(3))
        if m.group(1):
            out.append(("num", m.group(1), spaced))
        elif m.group(2):
            out.append(("name", m.group(2), spaced))
        else:
            out.append(("op", m.group(3), spaced))
        i = m.end()
    return out


class _Reader:
    def __init__(self, text: str, ctx: Context):
        self.toks = _tokens(normalise_text(text))
        self.i = 0
        self.ctx = ctx

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self, op: Optional[str] = None):
        t = self.peek()
        if t is None or (op is not None and t[1] != op):
            raise SymbolicError("UNREADABLE",
                                f"expected {op or 'a term'}, found "
                                f"{t[1] if t else 'the end'}")
        self.i += 1
        return t

    def expr(self) -> RF:
        if self.peek() and self.peek()[1] in "+-" and \
                self.peek()[0] == "op":
            sign = self.take()[1]
            v = self.term()
            v = -v if sign == "-" else v
        else:
            v = self.term()
        while self.peek() and self.peek()[0] == "op" and \
                self.peek()[1] in ("+", "-"):
            op = self.take()[1]
            w = self.term()
            v = v + w if op == "+" else v - w
        return v

    def _starts_factor(self) -> bool:
        t = self.peek()
        return t is not None and (t[0] in ("num", "name") or t[1] == "(")

    def term(self) -> RF:
        v = self.unary()
        while True:
            t = self.peek()
            if t and t[0] == "op" and t[1] in ("*", "/"):
                self.take()
                w = self.unary()
                if t[1] == "*":
                    v = v * w
                else:
                    if w.is_zero():
                        raise SymbolicError("UNREADABLE", "division by zero")
                    v = v / w
            elif self._starts_factor():
                v = v * self.unary()            # implicit product
            else:
                return v

    def unary(self) -> RF:
        t = self.peek()
        if t and t[0] == "op" and t[1] in ("-", "+"):
            self.take()
            v = self.unary()
            return -v if t[1] == "-" else v
        return self.power()

    def power(self) -> RF:
        base = self.atom()
        t = self.peek()
        if t and t[0] == "op" and t[1] in ("^", "**"):
            self.take()
            ex = self.unary()
            q = ex.const_value()
            if q is None:
                raise SymbolicError("UNSUPPORTED_POWER",
                                    "an exponent must be a rational number")
            if q.denominator == 1:
                if base.is_zero() and q < 0:
                    raise SymbolicError("UNREADABLE", "zero to a negative "
                                                      "power")
                return base ** int(q)
            c = base.const_value()
            if c is None:
                raise SymbolicError("UNSUPPORTED_POWER",
                                    "a fractional power of a letter; write "
                                    "it as an equation in the power")
            return radical_atom(c, q.numerator, q.denominator)
        return base

    def atom(self) -> RF:
        t = self.take()
        if t[0] == "num":
            return RF(Poly.const(Fraction(t[1])))
        if t[1] == "(":
            v = self.expr()
            self.take(")")
            return v
        if t[0] == "name":
            nxt = self.peek()
            if nxt and nxt[1] == "(" and not nxt[2]:
                if t[1] not in FUNCTIONS:
                    raise SymbolicError(
                        "UNREADABLE", f"unknown function {t[1]}; write "
                                      f"{t[1]}*(...) for a product")
                self.take("(")
                arg = self.expr()
                self.take(")")
                return apply_function(t[1], arg, self.ctx)
            if t[1] in FUNCTIONS:
                raise SymbolicError("UNREADABLE",
                                    f"{t[1]} needs a parenthesised argument")
            return RF(Poly.var(t[1]))
        raise SymbolicError("UNREADABLE", f"unexpected {t[1]!r}")


def apply_function(name: str, arg: RF, ctx: Context) -> RF:
    c = arg.const_value()
    if name == "tan":
        return apply_function("sin", arg, ctx) / apply_function("cos", arg,
                                                                ctx)
    if name in ("sin", "cos"):
        if c == 0:
            return RF(Poly.const(0 if name == "sin" else 1))
        a = ctx.atom(name, arg)
        ctx.trig_pairs()
        return a
    if name == "exp":
        if c == 0:
            return RF(Poly.const(1))
        return ctx.atom("exp", arg)
    if name == "ln":
        if c == 1:
            return RF(Poly())
        return ctx.atom("ln", arg)
    if name == "sqrt":
        if c is not None:
            if c < 0:
                raise SymbolicError("UNSUPPORTED_POWER", "sqrt of a negative")
            return radical_atom(c, 1, 2)
        return ctx.atom("sqrt", arg)
    raise SymbolicError("UNREADABLE", f"unknown function {name}")


def parse(text: str, ctx: Optional[Context] = None) -> RF:
    """A formula as a rational function (atoms recorded in ``ctx``)."""
    ctx = ctx if ctx is not None else Context()
    r = _Reader(text, ctx)
    if not r.toks:
        raise SymbolicError("UNREADABLE", "empty formula")
    v = r.expr()
    if r.peek() is not None:
        raise SymbolicError("UNREADABLE", f"unexpected {r.peek()[1]!r}")
    return v


def parse_equation(text: str, ctx: Optional[Context] = None
                   ) -> Tuple[RF, RF]:
    if text.count("=") != 1:
        raise SymbolicError("UNREADABLE", f"not one equation: {text!r}")
    a, b = text.split("=")
    return parse(a, ctx), parse(b, ctx)


# ===========================================================================
# 5.  PRINTING
# ===========================================================================

def _frac(c: Fraction) -> str:
    return str(c.numerator) if c.denominator == 1 else \
        f"{c.numerator}/{c.denominator}"


def _mono_text(m: Mono, py: Optional[Dict[str, str]] = None) -> str:
    parts = []
    m = tuple(sorted(m, key=lambda ve: ("(" in ve[0] or "^" in ve[0],
                                        ve[0])))
    for v, e in m:
        name = py.get(v, v) if py is not None else v
        if py is None and v in RADICALS and e == 1:
            parts.append(v)
            continue
        if e == 1:
            parts.append(name)
        else:
            parts.append(f"{name}**{e}" if py is not None else f"{name}^{e}")
    return "*".join(parts)


def _ordered(p: Poly) -> List[Tuple[Mono, Fraction]]:
    terms = sorted(p.t.items(), key=lambda kv: (-_mono_key(kv[0])[0],
                                                _mono_key(kv[0])[1]))
    # radical atoms after the plain terms of the same degree; constants last
    terms.sort(key=lambda kv: (-sum(e for v, e in kv[0]
                                    if v not in RADICALS),
                               any(v in RADICALS for v, _ in kv[0])))
    if len(terms) > 1 and terms[-1][0] == ():
        rest = terms[:-1]
        if all(sum(e for _, e in m) >= 2 or any(v in RADICALS for v, _ in m)
               for m, _ in rest):
            terms = [terms[-1]] + rest
    for i, (m, c) in enumerate(terms):
        if c > 0:
            return terms[i:] + terms[:i] if i else terms
    return terms


def _poly_text(p: Poly, py: Optional[Dict[str, str]] = None) -> str:
    if p.is_zero():
        return "0"
    out = []
    for i, (m, c) in enumerate(_ordered(p)):
        mono = _mono_text(m, py)
        a = abs(c)
        if py is not None:
            coef = f"F({a.numerator}, {a.denominator})" \
                if a.denominator != 1 else str(a.numerator)
        else:
            coef = _frac(a) if a.denominator == 1 else f"({_frac(a)})"
        if not mono:
            body = coef
        elif a == 1:
            body = mono
        else:
            body = f"{coef}*{mono}"
        if i == 0:
            out.append(("-" if c < 0 else "") + body)
        else:
            out.append((" - " if c < 0 else " + ") + body)
    return "".join(out)


def _factored(p: Poly, py: Optional[Dict[str, str]] = None
              ) -> Tuple[Fraction, str]:
    """``(numeric factor, text of the rest)`` with the monomial content and
    the rational content pulled out of a sum."""
    if p.is_zero():
        return Fraction(0), ""
    c = p.content()
    if p.leading()[1] < 0 and all(v < 0 for v in p.t.values()):
        c = -c
    q = p.scale(1 / c)
    mc = q.monomial_content()
    if mc and len(q.t) > 1:
        inv = {m: v for m, v in q.t.items()}
        rest = Poly({tuple(sorted(
            (var, e - dict(mc).get(var, 0)) for var, e in m
            if e - dict(mc).get(var, 0))): v for m, v in inv.items()})
        inner = _poly_text(rest, py)
        head = _mono_text(mc, py)
        return c, f"{head}*({inner})"
    if len(q.t) > 1:
        return c, f"({_poly_text(q, py)})" if c != 1 else _poly_text(q, py)
    m, v = next(iter(q.t.items()))
    mono = _mono_text(m, py)
    return c * v, mono


def to_text(rf: RF) -> str:
    """A readable formula: ``(2/3)*g*sin(theta)``, ``V*R2/(R1 + R2)``."""
    return _render(rf, None)


def to_python(rf: RF, names: Dict[str, str]) -> str:
    """The same formula as a Python expression over ``F`` (Fraction) and the
    identifiers of ``names``."""
    return _render(rf, names)


def _render(rf: RF, py: Optional[Dict[str, str]]) -> str:
    rf = RF.of(rf)
    if rf.is_zero():
        return "0"
    cn, tn = _factored(rf.num, py)
    cd, td = _factored(rf.den, py)
    c = cn / cd
    if py is not None:
        coef = f"F({abs(c).numerator}, {abs(c).denominator})"
        num = coef if not tn else f"{coef}*({tn})"
        if td:
            num = f"{num}/({td})"
        return f"-({num})" if c < 0 else num
    sign = "-" if c < 0 else ""
    a = abs(c)
    if not tn:
        num = _frac(a) if a.denominator == 1 else f"({_frac(a)})"
    elif a == 1:
        num = tn
    elif a.denominator == 1:
        num = f"{a.numerator}*{tn}"
    elif td:
        num = f"{a.numerator}*{tn}" if a.numerator != 1 else tn
        # the denominator's numeric factor must multiply all of ``td``:
        # ``2*r^2 - p`` would silently read as ``(2*r^2) - p``
        td = f"{a.denominator}*({td})" if _top_level_sum(td) else \
            f"{a.denominator}*{td}"
    else:
        num = f"({_frac(a)})*{tn}"
    if td:
        den = td
        if not (num.startswith("(") and num.endswith(")") and
                _balanced(num[1:-1])) and _top_level_sum(num):
            num = f"({num})"
        if not (den.startswith("(") and den.endswith(")") and
                _balanced(den[1:-1])) and ("*" in den or " " in den):
            den = f"({den})"
        return f"{sign}{num}/{den}"
    return f"{sign}{num}"


def _top_level_sum(s: str) -> bool:
    d = 0
    for i, ch in enumerate(s):
        d += ch == "("
        d -= ch == ")"
        if d == 0 and ch in "+-" and i > 0 and s[i - 1] == " ":
            return True
    return False


def _balanced(s: str) -> bool:
    d = 0
    for ch in s:
        d += ch == "("
        d -= ch == ")"
        if d < 0:
            return False
    return d == 0


# ===========================================================================
# 6.  SOLVING BY DECLARED SUBSTITUTION
# ===========================================================================

@dataclass
class Step:
    unknown: str
    power: int
    value: RF
    equation: int                 # index of the equation it came from
    divisor: RF                   # the coefficient divided by (!= 0)

    def text(self) -> str:
        lhs = self.unknown if self.power == 1 else \
            f"{self.unknown}^{self.power}"
        return f"from equation {self.equation + 1}: {lhs} = " \
               f"{to_text(self.value)}"


@dataclass
class Solution:
    """Each solved unknown ``u`` with ``u^k = value`` (``values[u] = (k,
    value)``); ``value`` may still hold unknowns that are only known through
    a root (the generators)."""

    values: Dict[str, Tuple[int, RF]]
    steps: List[Step]
    conditions: List[RF]
    targets: Tuple[str, ...]
    generators: Tuple[str, ...]
    rooted: Tuple[str, ...] = ()

    def positive_roots(self) -> Tuple[str, ...]:
        """Targets given as a positive even root (a convention, stated)."""
        return tuple(t for t in self.targets
                     if t in self.rooted or (self.values[t][0] > 1 and
                                             self.values[t][0] % 2 == 0))

    def answer(self, t: str) -> Tuple[int, RF]:
        return self.values[t]

    def root_text(self, t: str) -> str:
        k, v = self.values[t]
        if k == 1:
            return f"{t} = {to_text(v)}"
        return f"{t} = {root_form(v, k)}"


def root_form(v: RF, k: int) -> str:
    """``v^(1/k)`` with the k-th powers pulled out of the monomial and
    numeric contents: ``m0*sqrt(2*(gamma + 1))``."""
    out_parts: List[str] = []
    num, den = v.num, v.den
    inner_num, inner_den = num, den
    pulled: Dict[str, int] = {}
    for side, sgn in ((num, 1), (den, -1)):
        mc = side.monomial_content()
        for var, e in mc:
            w = e // k
            if w:
                pulled[var] = pulled.get(var, 0) + sgn * w
    outer = RF(Poly.const(1))
    for var, w in pulled.items():
        outer = outer * RF(Poly.var(var)) ** w
    inner = v / outer ** k
    c = inner.num.content() / inner.den.content()
    # pull perfect k-th powers out of the rational content
    cw = Fraction(1)
    for part, sgn in ((c.numerator, 1), (c.denominator, -1)):
        for pr, e in _factor_int(part).items():
            w = e // k
            if w:
                cw *= Fraction(pr) ** (sgn * w)
    outer = outer * cw
    inner = inner / Fraction(cw) ** k
    fn = "sqrt" if k == 2 else ("cbrt" if k == 3 else f"root{k}")
    ins = to_text(inner)
    if inner.is_const() and inner.const_value() == 1:
        return to_text(outer)
    body = f"{fn}({ins})"
    if outer.is_const() and outer.const_value() == 1:
        return body
    return f"{to_text(outer)}*{body}"


def _isolate(p: Poly, u: str, unknowns: set) -> Optional[Tuple[int, RF, RF]]:
    """If ``p = A u^k + B`` with ``A`` free of unknowns and ``B`` free of
    ``u``: ``(k, -B/A, A)``."""
    cs = p.coeffs(u)
    ks = [e for e in cs if e > 0]
    if len(ks) != 1:
        return None
    k = ks[0]
    A = cs[k]
    if A.vars() & unknowns:
        return None
    B = cs.get(0, Poly())
    return k, RF(-B) / RF(A), RF(A)


#: Letters that always name a known constant, never an unknown.
CONSTANTS = frozenset({"pi"})


def solve_system(equations: Sequence[Tuple[RF, RF]], unknowns: Iterable[str],
                 targets: Sequence[str],
                 mentioned: Optional[Iterable[str]] = None,
                 relations: Optional[List[RF]] = None,
                 name_roots: bool = True) -> Solution:
    """Solve for ``targets`` by declared substitution; see the module text.
    ``mentioned`` is every letter the equations were written with (a target
    written but cancelled is ``UNDERDETERMINED``, one never written
    ``NOT_IN_SYSTEM``).  Raises :class:`SymbolicError` with the refusal
    code."""
    unknowns = (set(unknowns) | set(targets)) - CONSTANTS
    polys: List[Tuple[int, Poly]] = []
    conditions: List[RF] = []
    seen = set()
    for i, (lhs, rhs) in enumerate(equations):
        d = lhs - rhs
        seen |= d.vars()
        if not d.den.is_const():
            conditions.append(RF(d.den))
        polys.append((i, d.num))
    values: Dict[str, Tuple[int, RF]] = {}
    steps: List[Step] = []

    def check_constant(i: int, p: Poly) -> None:
        if p.is_zero() or p.vars() & unknowns:
            return
        if p.is_const():
            raise SymbolicError("INCONSISTENT",
                                f"equation {i + 1} reduces to "
                                f"{to_text(RF(p))} = 0")
        if relations is not None:
            relations.append(RF(p))
            return
        raise SymbolicError("OVERDETERMINED",
                            f"equation {i + 1} forces a relation among the "
                            f"parameters: {to_text(RF(p))} = 0")

    written = set(mentioned) if mentioned is not None else seen
    for t in targets:
        if t not in written:
            raise SymbolicError("NOT_IN_SYSTEM", f"{t} appears in no "
                                                 f"equation")
    for i, p in polys:
        check_constant(i, p)
    polys = [(i, p) for i, p in polys
             if not p.is_zero() and p.vars() & unknowns]
    for t in targets:
        if t not in seen:
            raise SymbolicError("UNDERDETERMINED", f"{t} cancels from "
                                                   f"every equation")
    polys = [(i, p) for i, p in polys if not p.is_zero()]
    pivots: List[Poly] = []
    fast = _cramer_linear(polys, unknowns)
    if fast is not None:
        det, vals = fast
        conditions.append(RF(det))
        for u in sorted(vals):
            values[u] = (1, vals[u])
            steps.append(Step(u, 1, vals[u], 0, RF(det)))
        polys = []
    while polys:
        best = None
        for idx, (i, p) in enumerate(polys):
            live = p.vars() & unknowns
            for u in sorted(live):
                got = _isolate(p, u, unknowns)
                if got is None:
                    continue
                k = got[0]
                ok = all(e % k == 0 for j, (_, q) in enumerate(polys)
                         if j != idx for e in q.exponents(u))
                if not ok:
                    continue
                rank = (k, len(live), u not in targets, idx)
                if best is None or rank < best[0]:
                    best = (rank, idx, u, got)
        if best is None:
            break
        _, idx, u, (k, val, A) = best
        i, _ = polys.pop(idx)
        if not A.is_const():
            conditions.append(A)
        steps.append(Step(u, k, val, i, A))
        if not A.is_const():
            pivots.append(A.num)
        newp = []
        for j, q in polys:
            r = q.subs_power(u, k, val)
            if not r.den.is_const():
                conditions.append(RF(r.den))
            rn = _strip_pivots(r.num, pivots, unknowns)
            check_constant(j, rn)
            if not rn.is_zero() and rn.vars() & unknowns:
                newp.append((j, rn))
        polys = newp
        for w, (kw, vw) in list(values.items()):
            values[w] = (kw, vw.num.reduce_power(u, k, val) /
                         vw.den.reduce_power(u, k, val))
        values[u] = (k, val)
    rooted: List[str] = []
    if name_roots:
        for u in sorted(values):
            k, v = values[u]
            if k == 1 or len(v.num.t) != 1 or len(v.den.t) != 1 or \
                    v.vars() & unknowns:
                continue
            (mn, cn), = v.num.t.items()
            (md, cd), = v.den.t.items()
            if any(e % k for _, e in mn + md) or cn / cd <= 0:
                continue
            root = RF(Poly({tuple((x, e // k) for x, e in mn): Fraction(1)}),
                      Poly({tuple((x, e // k) for x, e in md): Fraction(1)}))
            root = root * radical_atom(cn / cd, 1, k)
            for w, (kw, vw) in list(values.items()):
                if w != u:
                    values[w] = (kw, vw.num.reduce_power(u, 1, root) /
                                 vw.den.reduce_power(u, 1, root))
            values[u] = (1, root)
            if k % 2 == 0:
                rooted.append(u)
            steps.append(Step(u, 1, root, steps[-1].equation if steps else 0,
                              RF(Poly.const(1))))
    missing = [t for t in targets if t not in values]
    gens = tuple(sorted(u for u, (k, _) in values.items() if k > 1))
    if not missing:
        for t in targets:
            k, v = values[t]
            bad = (v.vars() & unknowns) - set(gens)
            if bad:
                missing.append(t)
    if missing:
        live = [p for _, p in polys if p.vars() & unknowns]
        if any(_nonlinear(p, unknowns) for p in live):
            raise SymbolicError("NONLINEAR",
                                f"{', '.join(missing)} cannot be isolated: "
                                f"an unknown appears in a product or in "
                                f"more than one power")
        raise SymbolicError("UNDERDETERMINED",
                            f"{', '.join(missing)} not fixed by the "
                            f"equations")
    # generators that a target's value still holds must be roots we can
    # name: their value is then free of unknowns
    for t in targets:
        k, v = values[t]
        for g in v.vars() & set(gens):
            if values[g][1].vars() & unknowns:
                raise SymbolicError("NONLINEAR",
                                    f"{t} depends on {g}, which is only "
                                    f"known through another unknown")
    conds: List[RF] = []
    for c in conditions:
        p = c.num
        if p.is_const():
            continue
        pieces = [Poly.var(v) for v, _ in p.monomial_content()]
        rest = divide_exact(p, Poly({p.monomial_content(): Fraction(1)}))
        if not rest.is_const():
            pieces.append(rest)
        for q in pieces:
            q = RF(q.scale(1 / q.leading()[1]))
            if all(q != d for d in conds):
                conds.append(q)
    return Solution(values, steps, conds, tuple(targets), gens,
                    tuple(rooted))


def _bareiss_det(m: List[List[Poly]]) -> Poly:
    """Determinant of a square matrix of polynomials by fraction-free
    (Bareiss) elimination: every division is exact."""
    m = [list(r) for r in m]
    n = len(m)
    sign = 1
    prev = Poly.const(1)
    for k in range(n - 1):
        if m[k][k].is_zero():
            for i in range(k + 1, n):
                if not m[i][k].is_zero():
                    m[k], m[i] = m[i], m[k]
                    sign = -sign
                    break
            else:
                return Poly()
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                num = m[i][j] * m[k][k] - m[i][k] * m[k][j]
                q = divide_exact(num, prev)
                if q is None:            # pragma: no cover - Bareiss is exact
                    raise ArithmeticError("Bareiss division not exact")
                m[i][j] = q
        prev = m[k][k]
    d = m[n - 1][n - 1]
    return d if sign == 1 else -d


#: Square linear systems at least this large go through Cramer's rule with
#: Bareiss determinants instead of substitution (whose intermediate
#: rational functions need multivariate gcds that grow too fast).
CRAMER_MIN = 4


def _cramer_linear(polys: List[Tuple[int, Poly]], unknowns: set
                   ) -> Optional[Tuple[Poly, Dict[str, RF]]]:
    """For a square system linear in the unknowns with
    ``len >= CRAMER_MIN`` and a nonzero determinant: ``(det, values)``.
    Otherwise ``None`` (the substitution path then decides, including
    every refusal)."""
    if len(polys) < CRAMER_MIN:
        return None
    us = sorted(set().union(*(p.vars() for _, p in polys)) & unknowns)
    if len(us) != len(polys):
        return None
    rows: List[List[Poly]] = []
    rhs: List[Poly] = []
    for _, p in polys:
        if _nonlinear(p, unknowns):
            return None
        row = [Poly() for _ in us]
        const = Poly()
        for mono, c in p.t.items():
            hit = [v for v, _ in mono if v in unknowns]
            term = Poly({mono: c})
            if not hit:
                const = const + term
            else:
                v = hit[0]
                rest = tuple((x, e) for x, e in mono if x != v)
                row[us.index(v)] = row[us.index(v)] + Poly({rest: c})
        rows.append(row)
        rhs.append(-const)
    det = _bareiss_det(rows)
    if det.is_zero():
        return None
    vals: Dict[str, RF] = {}
    for j, u in enumerate(us):
        mj = [r[:j] + [rhs[i]] + r[j + 1:] for i, r in enumerate(rows)]
        vals[u] = RF(_bareiss_det(mj), det)
    return det, vals


def _strip_pivots(p: Poly, pivots: List[Poly], unknowns: set) -> Poly:
    """Divide ``p`` (an equation set to zero) exactly by earlier non-constant
    pivot coefficients, which are already declared nonzero conditions.
    This is the Bareiss step for substitution: after eliminating with
    pivot ``A`` the next equations carry the previous pivot as an exact
    factor, and keeping it makes the coefficients grow without bound.
    Only factors free of unknowns are removed, so no solution is lost."""
    if p.is_zero():
        return p
    for a in pivots:
        if a.is_const() or a.vars() & unknowns:
            continue
        while True:
            q = divide_exact(p, a)
            if q is None or q.is_const() and not (p.vars() - a.vars()):
                break
            p = q
    return p


def _nonlinear(p: Poly, unknowns: set) -> bool:
    for m in p.t:
        hit = [(v, e) for v, e in m if v in unknowns]
        if len(hit) > 1 or any(e > 1 for _, e in hit):
            return True
    return False


# ===========================================================================
# 7.  DERIVATIVES AND ENTAILMENT
# ===========================================================================

def _dpoly(p: Poly, v: str) -> Poly:
    t: Dict[Mono, Fraction] = {}
    for m, c in p.t.items():
        d = dict(m)
        e = d.get(v, 0)
        if not e:
            continue
        if e == 1:
            del d[v]
        else:
            d[v] = e - 1
        mm = tuple(sorted(d.items()))
        t[mm] = t.get(mm, 0) + c * e
    return Poly(t)


def diff(rf: RF, var: str, ctx: Context) -> RF:
    """``d rf / d var`` through every atom's declared derivative."""
    rf = RF.of(rf)

    def dp(p: Poly) -> RF:
        out = RF(_dpoly(p, var))
        for name in p.vars():
            if name == var or name not in ctx.atoms:
                continue
            a = ctx.atoms[name]
            da = diff(a.arg, var, ctx)
            if da.is_zero():
                continue
            if a.kind == "sin":
                inner = ctx.atom("cos", a.arg)
            elif a.kind == "cos":
                inner = -ctx.atom("sin", a.arg)
            elif a.kind == "exp":
                inner = RF(Poly.var(name))
            elif a.kind == "ln":
                inner = 1 / a.arg
            elif a.kind == "sqrt":
                inner = 1 / (2 * RF(Poly.var(name)))
            else:
                raise SymbolicError("UNSUPPORTED", f"no derivative for "
                                                   f"{name}")
            out = out + RF(_dpoly(p, name)) * inner * da
        return out

    return (dp(rf.num) * RF(rf.den) - RF(rf.num) * dp(rf.den)) / \
        RF(rf.den * rf.den)


def entails(relations: Sequence[RF], claim: Tuple[RF, RF]
            ) -> Optional[Tuple[str, RF]]:
    """Whether a claimed relation follows from derived relations ``r = 0``.

    ``("multiple", q)``: the claim's numerator is ``q`` times a relation, so
    the claim holds wherever its denominator is nonzero.  ``("factor", q)``:
    a relation is ``q`` times the claim's numerator, so the claim holds
    wherever ``q`` is also nonzero (``q`` is the stated condition).
    ``None``: neither, so nothing is claimed."""
    d = claim[0] - claim[1]
    if d.is_zero():
        return ("multiple", RF(Poly.const(0)))
    for r in relations:
        if r.is_zero():
            continue
        q = divide_exact(d.num, r.num)
        if q is not None:
            return ("multiple", RF(q))
    for r in relations:
        if r.is_zero():
            continue
        q = divide_exact(r.num, d.num)
        if q is not None:
            return ("factor", RF(q))
    return None


# ===========================================================================
# 8.  THE COLUMN-3 SCRIPT OF A SOLVED SYSTEM
# ===========================================================================

class Lcg:
    """A small integer generator (no ``random`` in the package): the points
    of a column-3 check are deterministic."""

    def __init__(self, seed: int = 20260):
        self.s = seed

    def next(self) -> int:
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) \
            % (1 << 64)
        return self.s >> 33

    def rational(self, lo: int = 1, hi: int = 9) -> Fraction:
        a = lo + self.next() % (hi - lo + 1)
        b = 1 + self.next() % 5
        return Fraction(a, b)


def py_names(symbols: Iterable[str]) -> Dict[str, str]:
    """A Python identifier for every symbol and atom name."""
    out: Dict[str, str] = {}
    used = set()
    for s in sorted(symbols):
        base = re.sub(r"[^A-Za-z0-9_]+", "_", s).strip("_") or "v"
        if base[0].isdigit():
            base = "r_" + base
        if base in ("F", "G", "lambda", "def", "class", "in", "is", "or",
                    "and", "not", "if", "for", "E_", "pi_"):
            base = base + "_"
        name = base
        n = 2
        while name in used:
            name = f"{base}_{n}"
            n += 1
        used.add(name)
        out[s] = name
    return out


GENERATOR_PRELUDE = '''from fractions import Fraction as F


class G:
    """A polynomial in formal generators, reduced by g^k = value."""
    REL = {}

    def __init__(self, t=None):
        self.t = {}
        for m, c in (t or {}).items():
            if c:
                self.t[m] = F(c)

    @staticmethod
    def c(x):
        return x if isinstance(x, G) else G({(): F(x)})

    @staticmethod
    def gen(name):
        return G({((name, 1),): 1})

    def red(self):
        out = {}
        for m, c in self.t.items():
            d = dict(m)
            for v in list(d):
                k, val = G.REL[v]
                w, r = divmod(d[v], k)
                c = c * val ** w
                if r:
                    d[v] = r
                else:
                    del d[v]
            mm = tuple(sorted(d.items()))
            out[mm] = out.get(mm, 0) + c
        return G(out)

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
        o = G.c(o)
        t = {}
        for m1, c1 in self.t.items():
            for m2, c2 in o.t.items():
                d = dict(m1)
                for v, e in m2:
                    d[v] = d.get(v, 0) + e
                mm = tuple(sorted(d.items()))
                t[mm] = t.get(mm, 0) + c1 * c2
        return G(t).red()

    __rmul__ = __mul__

    def __truediv__(self, o):
        o = G.c(o)
        if set(o.t) - {()}:
            raise ValueError("division by a generator")
        return self * (1 / o.t[()])

    def __rtruediv__(self, o):
        return G.c(o) / self

    def __pow__(self, n):
        if n < 0:
            return G.c(1) / (self ** (-n))
        out = G.c(1)
        for _ in range(n):
            out = out * self
        return out

    def zero(self):
        return not self.red().t


ENV = {"F": F, "__builtins__": {}}


def ev(expr, point):
    return G.c(eval(expr, ENV, point))
'''


# -- an independent transliteration of formula text into Python -----------

class _Translit:
    """Formula text -> Python text over ``F`` and the point's identifiers,
    token by token (it builds no rational function: the only thing it shares
    with the reader is the naming of atoms)."""

    def __init__(self, text: str, names: Dict[str, str]):
        self.toks = _tokens(normalise_text(text))
        self.i = 0
        self.names = names

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self, op=None):
        t = self.peek()
        if t is None or (op is not None and t[1] != op):
            raise SymbolicError("UNREADABLE", "transliteration")
        self.i += 1
        return t

    def span(self, start: int, end: int) -> str:
        return " ".join(t[1] for t in self.toks[start:end])

    def expr(self) -> str:
        out = []
        t = self.peek()
        if t and t[0] == "op" and t[1] in "+-":
            self.take()
            out.append(t[1])
        out.append(self.term())
        while self.peek() and self.peek()[0] == "op" and \
                self.peek()[1] in ("+", "-"):
            out.append(f" {self.take()[1]} ")
            out.append(self.term())
        return "(" + "".join(out) + ")"

    def term(self) -> str:
        out = [self.unary()]
        while True:
            t = self.peek()
            if t and t[0] == "op" and t[1] in ("*", "/"):
                self.take()
                out.append(t[1])
                out.append(self.unary())
            elif t is not None and (t[0] in ("num", "name") or t[1] == "("):
                out.append("*")
                out.append(self.unary())
            else:
                return "(" + "".join(out) + ")"

    def unary(self) -> str:
        t = self.peek()
        if t and t[0] == "op" and t[1] in ("-", "+"):
            self.take()
            return f"({t[1]}{self.unary()})"
        return self.power()

    def power(self) -> str:
        start = self.i
        base = self.atom()
        mid = self.i
        t = self.peek()
        if t and t[0] == "op" and t[1] in ("^", "**"):
            self.take()
            es = self.i
            self.unary()
            q = parse(self.span(es, self.i)).const_value()
            if q.denominator == 1:
                return f"({base})**({int(q)})"
            c = parse(self.span(start, mid)).const_value()
            return "(" + to_python(radical_atom(c, q.numerator,
                                                q.denominator),
                                   self.names) + ")"
        return base

    def atom(self) -> str:
        t = self.take()
        if t[0] == "num":
            q = Fraction(t[1])
            return f"F({q.numerator}, {q.denominator})"
        if t[1] == "(":
            v = self.expr()
            self.take(")")
            return v
        nxt = self.peek()
        if nxt and nxt[1] == "(" and not nxt[2]:
            self.take("(")
            st, depth = self.i, 1
            while depth:
                tok = self.take()
                depth += (tok[1] == "(") - (tok[1] == ")")
            argtext = self.span(st, self.i - 1)
            canon = to_text(parse(argtext))
            fn = t[1]
            if fn == "tan":
                return (f"({self.names['sin(' + canon + ')']}/"
                        f"{self.names['cos(' + canon + ')']})")
            key = f"{fn}({canon})"
            if key in self.names:
                return self.names[key]
            c = parse(argtext).const_value()
            if fn == "sqrt" and c is not None:
                return "(" + to_python(radical_atom(c, 1, 2), self.names) + \
                    ")"
            arg = transliterate(argtext, self.names)
            if fn in ("sqrt", "cbrt"):
                return f"rt({arg}, {2 if fn == 'sqrt' else 3})"
            if fn.startswith("root"):
                return f"rt({arg}, {int(fn[4:])})"
            raise SymbolicError("UNREADABLE", f"no point value for {key}")
        return self.names[t[1]]


def transliterate(text: str, names: Dict[str, str]) -> str:
    """Formula text as a Python expression (see :class:`_Translit`)."""
    tr = _Translit(text, names)
    out = tr.expr()
    if tr.peek() is not None:
        raise SymbolicError("UNREADABLE", "transliteration left text over")
    return out


SCRIPT_CHECK = '''
_fresh = [0]


def rt(x, k):
    """A fresh generator for the k-th root of a value constant at the
    point."""
    x = G.c(x).red()
    if set(x.t) - {()}:
        raise ValueError("root of a non-constant")
    _fresh[0] += 1
    name = "root_" + str(_fresh[0])
    G.REL[name] = (k, x.t.get((), F(0)))
    return G.gen(name)


ENV["rt"] = rt
checked = 0
for base, gens in POINTS:
    G.REL = {r: (q, b) for r, q, b in RADICALS}
    P = {k: G.c(v) for k, v in base.items()}
    for s, c in PAIRS:
        assert base[s] ** 2 + base[c] ** 2 == 1
    for r, q, b in RADICALS:
        P[r] = G.gen(r)
    for g, (k, v) in gens.items():
        G.REL[g] = (k, v)
        P[g] = G.gen(g)
    for name, k, expr in VALUES:
        if k == 1:
            P[name] = ev(expr, P)
    for law in LAWS:
        lhs, rhs = law
        assert (ev(lhs, P) - ev(rhs, P)).zero(), law
    for name, k, expr in ANSWERS:
        assert (P[name] ** k - ev(expr, P) ** k).zero(), name
    for lhs, rhs in CLAIMS:
        assert (ev(lhs, P) - ev(rhs, P)).zero(), (lhs, rhs)
    checked += 1
assert checked >= 3, checked
'''


def system_script(equation_texts: Sequence[str], sol: Solution,
                  ctx: Context, params: Iterable[str],
                  answer_texts: Dict[str, str], label: str = "SYSTEM",
                  points: int = 6, seed: int = 98,
                  scale_first: Optional[Fraction] = None,
                  claims: Sequence[str] = ()) -> str:
    """The stand-alone check: every law **as written** holds at ``points``
    rational points when the unknowns take the solution's values, and every
    target equals its **printed** answer (``answer_texts``: the right-hand
    side as printed, transliterated -- for a root, compared through its k-th
    power).  ``scale_first`` alters the first target's value (the mutation
    control)."""
    symbols = set(params) | set(sol.values) | set(ctx.atoms) | \
        set(RADICALS)
    for e in equation_texts:
        for lr in e.split("="):
            symbols |= parse(lr, Context()).vars()
    names = py_names(symbols)
    lcg = Lcg(seed)
    pairs = ctx.trig_pairs()
    free = sorted((set(params) | set(ctx.atoms) | symbols) -
                  set(sol.values) - set(RADICALS) -
                  {x for pr in pairs for x in pr})
    pts = []
    tries = 0
    while len(pts) < points and tries < 400:
        tries += 1
        P: Dict[str, Fraction] = {}
        for sn, cn in pairs:
            t = lcg.rational(1, 7) / 3
            while t == 1:
                t = lcg.rational(1, 7) / 3
            P[sn] = 2 * t / (1 + t * t)
            P[cn] = (1 - t * t) / (1 + t * t)
        for p in free:
            P[p] = lcg.rational()
        try:
            row = {}
            for u, (k, v) in sol.values.items():
                if k > 1:
                    w = v.evaluate(P)
                    if w == 0:
                        raise ZeroDivisionError
                    row[u] = (k, w)
            ext = dict(P)
            for u, (k, v) in sol.values.items():
                if k == 1 and not (v.vars() - set(P)):
                    ext[u] = v.evaluate(P)
            for c in sol.conditions:
                if not (c.vars() - set(ext)) and c.evaluate(ext) == 0:
                    raise ZeroDivisionError
            pts.append((P, row))
        except (ZeroDivisionError, KeyError):
            continue
    vals = []
    for i, (u, (k, v)) in enumerate(sorted(sol.values.items(),
                                           key=lambda kv: kv[0])):
        if scale_first is not None and u == sol.targets[0] and k == 1:
            v = v * scale_first
        vals.append((names[u], k, to_python(v, names)))
    if scale_first is not None and sol.values[sol.targets[0]][0] > 1:
        pts = [(P, {u: ((k, w * scale_first) if u == sol.targets[0]
                        else (k, w)) for u, (k, w) in row.items()})
               for P, row in pts]
    ans = [(names[t], sol.values[t][0], transliterate(answer_texts[t], names))
           for t in sol.targets]
    rad = [(names[r], q, b) for r, (q, b) in RADICALS.items() if r in symbols]
    lines = [GENERATOR_PRELUDE]
    lines.append("LAWS = " + repr([(transliterate(a, names),
                                    transliterate(b, names))
                                   for a, b in (e.split("=")
                                                for e in equation_texts)]))
    lines.append("CLAIMS = " + repr([(transliterate(a, names),
                                      transliterate(b, names))
                                     for a, b in (c.split("=")
                                                  for c in claims)]))
    lines.append("VALUES = " + repr(vals))
    lines.append("ANSWERS = " + repr(ans))
    lines.append("RADICALS = [" + ", ".join(
        f"({r!r}, {q}, F({b.numerator}, {b.denominator}))"
        for r, q, b in rad) + "]")
    lines.append("PAIRS = " + repr([(names[a], names[b]) for a, b in pairs]))
    pt_lines = []
    for P, row in pts:
        d = ", ".join(f"{names[k]!r}: F({v.numerator}, {v.denominator})"
                      for k, v in sorted(P.items()) if k in names)
        g = ", ".join(f"{names[u]!r}: ({k}, F({w.numerator}, "
                      f"{w.denominator}))" for u, (k, w) in row.items())
        pt_lines.append("    ({" + d + "}, {" + g + "}),")
    lines.append("POINTS = [\n" + "\n".join(pt_lines) + "\n]")
    lines.append(SCRIPT_CHECK)
    lines.append(f"print(f'{label} POINTS={{checked}} LAWS={{len(LAWS)}} "
                 f"VERIFIED True')")
    return "\n".join(lines)
