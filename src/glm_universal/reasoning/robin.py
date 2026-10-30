"""``glm_universal.reasoning.robin`` -- eigenvalue problems with one Robin end
(Phase 118, ``studies/DERIVATION_THREE_STUDY.md``).

Why it exists
-------------
Phase 107's :mod:`~glm_universal.reasoning.spectral` solves ``y'' + lambda y
= 0`` with Dirichlet, Neumann or periodic conditions, where the determinant's
zero set is a lattice of multiples of ``pi``.  A Robin condition
``a y(e) + b y'(e) = 0`` makes the determinant ``k cos(kL) + h sin(kL)``
(or ``-k sin(kL) + h cos(kL)``), whose zeros have no closed form, and that
round refused it ``TRANSCENDENTAL``.  The zeros are still *derivable*: the
sign analysis puts exactly one root in each of a declared family of
intervals, decides whether a negative (or zero) eigenvalue exists, and on a
numeric interval every eigenvalue can be enclosed between two rationals at
which the characteristic function has opposite, rigorously computed signs.

The derivation
--------------
Write the Robin end as ``y'(L) + h y(L) = 0`` (``h = a/b``; a Robin end at
``0`` is moved to ``L`` by ``x -> L - x``, which turns ``a y(0) + b y'(0)``
into ``a u(L) - b u'(L)``).  With a Dirichlet end at ``0`` the eigenfunction
is ``sin(kx)`` and the equation ``f(k) = k cos(kL) + h sin(kL) = 0``, i.e.
``tan(kL) = -k/h``; with a Neumann end it is ``cos(kx)`` and ``f(k) =
-k sin(kL) + h cos(kL) = 0``, i.e. ``k tan(kL) = h``.  On each interval
between consecutive multiples of ``pi/(2L)`` one side of the equation is
monotone and the other has the opposite monotonicity, so there is at most
one root, and the signs of ``f`` at the ends (``+-h`` or ``+-k``) say
whether there is one:

* Dirichlet, ``h > 0``: one root in ``((n - 1/2) pi/L, n pi/L)``,
  ``n >= 1``; no eigenvalue ``<= 0``;
* Dirichlet, ``-1 < hL < 0``: one root in ``(0, pi/(2L))`` and one in
  ``((n - 1) pi/L, (n - 1/2) pi/L)`` for ``n >= 2``;
* Dirichlet, ``hL = -1``: ``lambda = 0`` with ``y = x``, then
  ``(n pi/L, (n + 1/2) pi/L)``, ``n >= 1``;
* Dirichlet, ``hL < -1``: one negative eigenvalue ``-mu^2`` with
  ``tanh(mu L) = -mu/h`` (``y = sinh(mu x)``), then
  ``(n pi/L, (n + 1/2) pi/L)``, ``n >= 1``;
* Neumann, ``h > 0``: ``((n - 1) pi/L, (n - 1/2) pi/L)``, ``n >= 1``;
* Neumann, ``h < 0``: one negative eigenvalue with ``mu tanh(mu L) = -h``
  (``y = cosh(mu x)``), then ``((n - 1/2) pi/L, n pi/L)``, ``n >= 1``.

``GLM.NonShannon.robin_root_exists`` and ``robin_eigenfunction`` prove the
first case.  The enclosures use exact rational partial sums of the Taylor
series with the remainder bounded, and a rational enclosure of ``pi``, so a
sign is never read from a float (D7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from . import spectral as SP

__all__ = ["RobinError", "Robin", "robin_problem", "PI_LO", "PI_HI",
           "sin_cos_bounds", "sinh_cosh_bounds", "interval_mults", "char_sign", "enclose_root",
           "decimal_text"]

#: A rational enclosure of pi (50 decimals).
PI_LO = Fraction("3.14159265358979323846264338327950288419716939937510")
PI_HI = Fraction("3.14159265358979323846264338327950288419716939937511")


class RobinError(Exception):
    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
# 1.  RIGOROUS SIGNS
# ===========================================================================

def _dyadic(x: Fraction, bits: int = 80) -> Tuple[Fraction, Fraction]:
    """``x`` rounded down and up to a multiple of ``2**-bits``."""
    s = 1 << bits
    lo = Fraction((x.numerator * s) // x.denominator, s)
    hi = lo if lo == x else lo + Fraction(1, s)
    return lo, hi


def sin_cos_bounds(x: Fraction, eps: Fraction = Fraction(1, 1 << 90)
                   ) -> Tuple[Tuple[Fraction, Fraction],
                              Tuple[Fraction, Fraction]]:
    """Rational bounds on ``sin x`` and ``cos x`` (Taylor, exact partial
    sums, Lagrange remainder ``|x|^(N+1)/(N+1)!``)."""
    x = Fraction(x)
    ax = abs(x)
    s, c = Fraction(0), Fraction(0)
    term = Fraction(1)                     # x^n / n!
    n = 0
    while True:
        if n % 4 == 0:
            c += term
        elif n % 4 == 1:
            s += term
        elif n % 4 == 2:
            c -= term
        else:
            s -= term
        n += 1
        term = term * x / n
        if n > ax + 2 and abs(term) < eps:
            break
    r = abs(term)
    return (s - r, s + r), (c - r, c + r)


def sinh_cosh_bounds(x: Fraction, eps: Fraction = Fraction(1, 1 << 90)
                     ) -> Tuple[Tuple[Fraction, Fraction],
                                Tuple[Fraction, Fraction]]:
    """Rational bounds on ``sinh x`` and ``cosh x`` for ``x >= 0``."""
    x = Fraction(x)
    assert x >= 0
    s, c = Fraction(0), Fraction(0)
    term = Fraction(1)
    n = 0
    while True:
        if n % 2 == 0:
            c += term
        else:
            s += term
        n += 1
        term = term * x / n
        if n > 2 * x + 2 and term < eps:
            break
    # tail of the exponential series after n terms: <= term / (1 - x/(n+1))
    r = term / (1 - x / (n + 1))
    return (s, s + r), (c, c + r)


def _mul(a: Tuple[Fraction, Fraction], k: Fraction) -> Tuple[Fraction,
                                                             Fraction]:
    lo, hi = a[0] * k, a[1] * k
    return (lo, hi) if lo <= hi else (hi, lo)


def char_sign(family: str, h: Fraction, L: Fraction, k: Fraction) -> int:
    """The sign of the characteristic function at a rational ``k`` (``0``
    when the enclosure straddles zero -- the caller refines)."""
    if family in ("D", "N"):
        (sl, sh), (cl, ch) = sin_cos_bounds(k * L)
        if family == "D":          # k cos(kL) + h sin(kL)
            a, b = _mul((cl, ch), k), _mul((sl, sh), h)
        else:                      # -k sin(kL) + h cos(kL)
            a, b = _mul((sl, sh), -k), _mul((cl, ch), h)
    else:
        (sl, sh), (cl, ch) = sinh_cosh_bounds(k * L)
        if family == "Dneg":       # mu cosh(mu L) + h sinh(mu L)
            a, b = _mul((cl, ch), k), _mul((sl, sh), h)
        else:                      # mu sinh(mu L) + h cosh(mu L)
            a, b = _mul((sl, sh), k), _mul((cl, ch), h)
    lo, hi = a[0] + b[0], a[1] + b[1]
    return 1 if lo > 0 else (-1 if hi < 0 else 0)


def _approx(x: Fraction, places: int = 6) -> str:
    """``x`` rounded down to ``places`` decimals, for a message only."""
    q = (x * 10 ** places).numerator // (x * 10 ** places).denominator
    sign = "-" if q < 0 else ""
    q = abs(q)
    return f"{sign}{q // 10 ** places}.{q % 10 ** places:0{places}d}"


def enclose_root(family: str, h: Fraction, L: Fraction, a: Fraction,
                 b: Fraction, width: Fraction = Fraction(1, 10 ** 13)
                 ) -> Tuple[Fraction, Fraction]:
    """``(lo, hi)`` with opposite certified signs of the characteristic
    function at the ends, ``hi - lo <= width``, inside ``[a, b]``."""
    a, _ = _dyadic(Fraction(a))
    _, b = _dyadic(Fraction(b))
    sa, sb = char_sign(family, h, L, a), char_sign(family, h, L, b)
    if sa == 0 or sb == 0 or sa == sb:
        raise RobinError("NO_BRACKET", f"no certified sign change on "
                         f"[{_approx(a)}, {_approx(b)}]")
    while b - a > width:
        m = (a + b) / 2
        sm = char_sign(family, h, L, m)
        if sm == 0:                         # pragma: no cover
            m = (a + 2 * b) / 3
            m, _ = _dyadic(m)
            sm = char_sign(family, h, L, m)
            if sm == 0:
                break
        if sm == sa:
            a = m
        else:
            b = m
    return a, b


def decimal_text(lo: Fraction, hi: Fraction, places: int = 6
                 ) -> Optional[str]:
    """The common rounding of ``lo`` and ``hi`` to ``places`` decimals, or
    ``None`` if they round apart."""
    def rnd(x: Fraction) -> str:
        s = 10 ** places
        n = x * s
        q = (n.numerator * 2 + n.denominator) // (2 * n.denominator)
        sign = "-" if q < 0 else ""
        q = abs(q)
        return f"{sign}{q // s}.{q % s:0{places}d}"
    a, b = rnd(lo), rnd(hi)
    return a if a == b else None


# ===========================================================================
# 2.  READING THE PROBLEM
# ===========================================================================

_NUM = r"(?:\d+(?:/\d+)?)"


def _robin_terms(text: str, y: str, x: str) -> Tuple[str, Fraction, Fraction]:
    """``(point, a, b)`` for ``a*y(P) + b*d(y)/dx(P) = 0``."""
    t = re.sub(r"\s+", "", text)
    if not t.endswith("=0"):
        raise RobinError("UNREADABLE", f"write the condition as ... = 0: "
                         f"{text!r}")
    body = t[:-2]
    pieces = re.findall(r"[+-]?[^+-]+", body)
    a = b = Fraction(0)
    point = None
    for p in pieces:
        sign = -1 if p.startswith("-") else 1
        p = p.lstrip("+-")
        m = re.fullmatch(rf"(?:({_NUM})\*)?(d\({y}\)/d{x}|{y})\(([^()]+)\)",
                         p)
        if not m:
            if re.fullmatch(rf"[A-Za-z_]\w*\*(d\({y}\)/d{x}|{y})\(([^()]+)\)",
                            p):
                raise RobinError("UNSUPPORTED", "a symbolic Robin coefficient: "
                                 "the spectrum's shape depends on its sign "
                                 "and size; give it a value")
            raise RobinError("UNREADABLE", f"cannot read {p!r}")
        coef = Fraction(m.group(1)) if m.group(1) else Fraction(1)
        if point is not None and m.group(3) != point:
            raise RobinError("UNREADABLE", "a condition at two points")
        point = m.group(3)
        if m.group(2) == y:
            a += sign * coef
        else:
            b += sign * coef
    if point is None or a == 0 or b == 0:
        raise RobinError("UNREADABLE", f"not a Robin condition: {text!r}")
    return point, a, b


@dataclass
class Robin:
    y: str
    x: str
    length: str                       # L as text
    L: Optional[Fraction]             # numeric length, or None
    family: str                       # D | N  (the condition at the far end
    h: Fraction                       #         after reflection is y' + h y)
    reflected: bool
    equation: str
    interval: str
    eigenfunction: str
    negative: Optional[str]           # the negative eigenvalue, in words
    negative_value: Optional[Tuple[Fraction, Fraction]] = None
    negative_mu: Optional[Tuple[Fraction, Fraction]] = None
    zero_eigen: bool = False
    roots: List[Tuple[Fraction, Fraction]] = field(default_factory=list)
    intervals: List[Tuple[Fraction, Fraction]] = field(default_factory=list)
    sign_text: str = ""
    case: str = ""                    # which of the six cases

    def eigenvalues(self) -> List[Tuple[Fraction, Fraction]]:
        return [(lo * lo, hi * hi) for lo, hi in self.roots]


def _kL(L: str, Lval: Optional[Fraction]) -> str:
    if Lval is None:
        return f"k*{L}"
    return "k" if Lval == 1 else f"{Lval}*k" if Lval.denominator == 1 \
        else f"({Lval})*k"


def _coef_k(c: Fraction) -> str:
    """``c*k`` printed: ``-k``, ``k/2``, ``2*k``, ``-k/3``."""
    sign = "-" if c < 0 else ""
    c = abs(c)
    num = "k" if c.numerator == 1 else f"{c.numerator}*k"
    return sign + num + ("" if c.denominator == 1 else f"/{c.denominator}")


def _pi_over(mult: str, L: str, Lval: Optional[Fraction]) -> str:
    """``mult*pi/L`` printed for symbolic or numeric ``L``."""
    base = "pi" if mult == "1" else f"{mult}*pi"
    if Lval is None:
        return f"{base}/{L}"
    if Lval == 1:
        return base
    return f"{base}/{Lval}" if Lval.denominator == 1 else f"{base}/({Lval})"


def _half_pi_over(L: str, Lval: Optional[Fraction]) -> str:
    if Lval is None:
        return f"pi/(2*{L})"
    d = 2 * Lval
    return f"pi/{d}" if d.denominator == 1 else f"pi/({d})"


def robin_problem(ode: str, conditions: Sequence[str],
                  first_roots: int = 3) -> Robin:
    m = SP._ODE.match(re.sub(r"\s+", "", ode.strip()))
    if not m or m.group(1) != m.group(3):
        if re.search(r"lambda\*\w+\*", re.sub(r"\s+", "", ode)):
            raise RobinError("UNSUPPORTED", "a coefficient that varies with "
                             "x: only y'' + lambda*y = 0 is solved")
        raise RobinError("UNREADABLE", "write d2(y)/dx2 + lambda*y = 0")
    y, x = m.group(1), m.group(2)
    if len(conditions) != 2:
        raise RobinError("UNDERDETERMINED" if len(conditions) < 2
                         else "UNREADABLE", "two conditions are needed")
    kinds = []
    for c in conditions:
        kind, pt = SP._condition(c, y, x)
        if kind == "R":
            pt, a, b = _robin_terms(c, y, x)
            kinds.append(("R", pt, a, b))
        elif kind in ("D", "N"):
            kinds.append((kind, pt, None, None))
        else:
            raise RobinError("UNREADABLE", "periodic and Robin conditions "
                             "together")
    robins = [k for k in kinds if k[0] == "R"]
    if len(robins) != 1:
        raise RobinError("TRANSCENDENTAL" if len(robins) == 2 else
                         "UNREADABLE",
                         "Robin conditions at both ends: the determinant mixes "
                         "k^2 sin, k cos and sin terms and the sign analysis "
                         "of this operation does not cover it")
    zero = [k for k in kinds if k[1] == "0"]
    far = [k for k in kinds if k[1] != "0"]
    if len(zero) != 1 or len(far) != 1:
        raise RobinError("UNREADABLE", "one condition at x = 0 and one at "
                         "the other end")
    L = far[0][1]
    try:
        Lval: Optional[Fraction] = Fraction(L)
    except ValueError:
        Lval = None
        if not re.fullmatch(r"[A-Za-z_]\w*", L):
            raise RobinError("UNREADABLE", f"cannot read the length {L!r}")
    if Lval is not None and Lval <= 0:
        raise RobinError("UNREADABLE", "the interval must have positive length")
    reflected = zero[0][0] == "R"
    if reflected:
        _, _, a, b = zero[0]
        family = far[0][0]
        h = a / (-b)                       # a u(L) - b u'(L) = 0
    else:
        _, _, a, b = far[0]
        family = zero[0][0]
        h = a / b
    arg = f"({L} - {x})" if reflected else x
    kL = _kL(L, Lval)
    n_pi = _pi_over("n", L, Lval)
    hlf = lambda m_: _pi_over(m_, L, Lval)
    out_neg = None
    zero_eigen = False
    hL = h * Lval if Lval is not None else None
    if family == "D":
        equation = f"tan({kL}) = {_coef_k(-1 / h)}"
        ef = f"sin(k_n*{arg})" if not reflected else f"sin(k_n*{arg})"
        if h > 0:
            case = "D+"
            interval = f"({hlf('(n - 1/2)')}, {n_pi}), n = 1, 2, 3, ..."
        else:
            if hL is None:
                raise RobinError("UNSUPPORTED", "with h < 0 the spectrum's "
                                 "shape depends on h*L; give L a value")
            if hL > -1:
                case = "D-weak"
                interval = (f"(0, {_half_pi_over(L, Lval)}) for n = 1; "
                            f"({hlf('(n - 1)')}, {hlf('(n - 1/2)')}), "
                            f"n = 2, 3, ...")
            else:
                case = "D-0" if hL == -1 else "D-neg"
                interval = f"({n_pi}, {hlf('(n + 1/2)')}), n = 1, 2, 3, ..."
                if hL == -1:
                    zero_eigen = True
                else:
                    out_neg = (f"one negative eigenvalue lambda = -mu^2 with "
                               f"tanh({kL.replace('k', 'mu')}) = "
                               f"{_coef_k(-1 / h).replace('k', 'mu')}, "
                               f"eigenfunction sinh(mu*{arg})")
    else:
        hs = f"{h}" if h.denominator == 1 else f"{h}"
        equation = f"k*tan({kL}) = {hs}"
        ef = f"cos(k_n*{arg})"
        if h > 0:
            case = "N+"
            interval = (f"({hlf('(n - 1)')}, {hlf('(n - 1/2)')}), "
                        f"n = 1, 2, 3, ...")
        else:
            case = "N-"
            interval = f"({hlf('(n - 1/2)')}, {n_pi}), n = 1, 2, 3, ..."
            out_neg = (f"one negative eigenvalue lambda = -mu^2 with "
                       f"mu*tanh({kL.replace('k', 'mu')}) = {-h}, eigenfunction "
                       f"cosh(mu*{arg})")
    r = Robin(y, x, L, Lval, family, h, reflected, equation, interval, ef,
              out_neg, zero_eigen=zero_eigen, case=case)
    r.sign_text = _sign_text(r)
    if Lval is not None:
        _enclose(r, first_roots)
    return r


def interval_mults(case: str, n: int) -> Tuple[Fraction, Fraction]:
    """The ``n``-th interval (1-based) of ``k`` as multiples of ``pi/L``."""
    if case == "D+":
        return Fraction(2 * n - 1, 2), Fraction(n)
    if case == "D-weak":
        return ((Fraction(0), Fraction(1, 2)) if n == 1 else
                (Fraction(n - 1), Fraction(2 * n - 1, 2)))
    if case in ("D-0", "D-neg"):
        return Fraction(n), Fraction(2 * n + 1, 2)
    if case == "N+":
        return Fraction(n - 1), Fraction(2 * n - 1, 2)
    return Fraction(2 * n - 1, 2), Fraction(n)


def _interval_bounds(r: Robin, n: int) -> Tuple[Fraction, Fraction]:
    """Rational bounds strictly inside the ``n``-th interval: lower end
    rounded up, upper end rounded down, from the pi enclosure."""
    a, b = interval_mults(r.case, n)
    lo_v = a * PI_HI / r.L if a > 0 else Fraction(0)
    return lo_v + Fraction(1, 10 ** 30), b * PI_LO / r.L - Fraction(1, 10 ** 30)


def _enclose(r: Robin, count: int) -> None:
    for n in range(1, count + 1):
        a, b = _interval_bounds(r, n)
        if r.case == "D-weak" and n == 1:
            # f(k) = k (1 + hL) + O(k^3) near 0: step in from 0 until the
            # sign is certified
            a = Fraction(1, 1 << 10)
            while char_sign(r.family, r.h, r.L, a) != 1:
                a /= 2
        r.intervals.append((a, b))
        r.roots.append(enclose_root(r.family, r.h, r.L, a, b))
    if r.negative is not None:
        fam = "Dneg" if r.family == "D" else "Nneg"
        a = Fraction(1, 10 ** 6)
        b = abs(r.h) + 1
        while char_sign(fam, r.h, r.L, b) <= 0:
            b *= 2
        if char_sign(fam, r.h, r.L, a) >= 0:          # pragma: no cover
            a = Fraction(1, 10 ** 12)
        lo, hi = enclose_root(fam, r.h, r.L, a, b)
        r.negative_mu = (lo, hi)
        r.negative_value = (-hi * hi, -lo * lo)


def _sign_text(r: Robin) -> str:
    L = r.length
    if r.family == "D":
        base = (f"lambda = k^2 > 0: y = A*cos(k*{r.x}) + B*sin(k*{r.x}); "
                f"y(0) = 0 kills A, and the far end gives "
                f"f(k) = k*cos(k*{L}) + ({r.h})*sin(k*{L}) = 0")
        mono = ("on each interval between consecutive multiples of "
                "pi/(2L) the two sides of tan(kL) = -k/h are monotone in "
                "opposite senses, so there is at most one root, and the signs "
                "of f at the ends (+-h at odd multiples, +-k at even ones) "
                "place exactly one root in each interval listed")
    else:
        base = (f"lambda = k^2 > 0: y = A*cos(k*{r.x}) + B*sin(k*{r.x}); "
                f"y'(0) = 0 kills B, and the far end gives "
                f"f(k) = -k*sin(k*{L}) + ({r.h})*cos(k*{L}) = 0")
        mono = ("on each interval between consecutive multiples of "
                "pi/(2L) k*tan(kL) is monotone, so there is at most one "
                "root, and the signs of f at the ends place exactly one root "
                "in each interval listed")
    if r.zero_eigen:
        z = "lambda = 0: y = x meets both conditions (h*L = -1): 0 is an eigenvalue"
    elif r.family == "D":
        z = "lambda = 0: y = A + B*x; y(0) = 0 and B*(1 + h*L) = 0 give y = 0"
    else:
        z = "lambda = 0: y = A; h*A = 0 gives y = 0"
    if r.negative is not None:
        n = ("lambda = -mu^2 < 0: " + r.negative +
             " (its left side runs from below the right side to above it "
             "exactly once)")
    else:
        n = ("lambda = -mu^2 < 0: the hyperbolic determinant keeps one sign "
             "for mu > 0, so there is no negative eigenvalue")
    refl = (" (the Robin end at x = 0 is moved to x = L by x -> L - x)"
            if r.reflected else "")
    return f"{base}{refl}; {mono}; {z}; {n}"
