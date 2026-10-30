"""``glm_universal.reasoning.robin_two`` -- Robin problems past one numeric
Robin end (Phase 119, ``studies/DERIVATION_FOUR_STUDY.md``).

Why it exists
-------------
Phase 118's :mod:`~glm_universal.reasoning.robin` solves ``y'' + lambda y =
0`` with one Robin end of numeric coefficient and refuses three things: a
Robin condition at both ends (``TRANSCENDENTAL``), a symbolic coefficient
``h`` and a negative ``h`` on a symbolic interval (``UNSUPPORTED``, because
the *shape* of the spectrum depends on the sign and size of ``h`` or
``h*L``).  It also gives no number for a symbolic interval.  This module
answers all four.

The derivations
---------------
* **Both ends.**  ``y'(0) = a y(0)`` and ``y'(L) + b y(L) = 0`` with ``a, b
  > 0``.  With ``y = k cos(kx) + a sin(kx)`` the first holds identically
  and the second is ``F(k) = (ab - k^2) sin(kL) + k(a + b) cos(kL) = 0``.
  At ``k = m pi/L`` ``F = (-1)^m k (a + b)``, which alternates in sign, so
  each interval ``((n - 1) pi/L, n pi/L)`` holds a root (the first one
  because ``F(k) ~ k(a + b + abL) > 0`` near ``0``); ``tan(kL) = k(a +
  b)/(k^2 - ab)`` has one decreasing branch on each side of ``sqrt(ab)``
  against the increasing branches of ``tan``, so there is exactly one.  No
  eigenvalue ``<= 0``: ``lambda = 0`` forces ``A(a + b + abL) = 0``, and a
  negative ``lambda`` gives a hyperbolic determinant of one sign.  Coefficients
  of opposite or negative sign are refused ``UNSUPPORTED`` (the count of
  negative eigenvalues then depends on ``a``, ``b`` and ``L`` together).
  ``GLM.RobinBoth.robin_both_root_exists`` and ``robin_both_eigenfunction``
  prove the root in each interval and the eigenfunction.
* **Symbolic h.**  Phase 118's six cases are exactly a case split on the
  sign class of ``h`` (Dirichlet end: ``h > 0``, ``h = 0``, ``-1 < hL <
  0``, ``hL = -1``, ``hL < -1``; Neumann end: ``h > 0``, ``h = 0``, ``h <
  0``), with ``h = 0`` the Dirichlet-Neumann or Neumann-Neumann problem in
  closed form.  The answer is that case list.
* **Negative h, symbolic L.**  The same split read as a split on ``L``:
  ``hL > -1`` is ``L < -1/h``.
* **Bounds on a symbolic interval.**  For a Dirichlet end and ``h > 0``
  the root ``z = k_n L`` of ``tan z = -z/(hL)`` in ``((n - 1/2) pi, n pi)``
  satisfies ``z - (n - 1/2) pi = arctan(hL/z)``
  (``GLM.RobinBoth.robin_root_arctan``), and since ``arctan`` is increasing,
  ``(n - 1/2) pi + arctan(hL/(n pi)) < z < (n - 1/2) pi + arctan(hL/((n -
  1/2) pi))`` (``robin_root_bounds``).

Numbers are enclosed with the rigorous Taylor bounds of
:func:`~glm_universal.reasoning.robin.sin_cos_bounds` (D7: no float).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

from . import robin as RB
from . import spectral as SP

__all__ = ["RobinTwo", "RobinCase", "robin_two", "both_sign", "bounds_for",
           "enclose_both"]

RobinError = RB.RobinError


@dataclass
class RobinCase:
    condition: str
    interval: str
    nonpositive: str                  # "none" | "zero" | "negative"
    case: str                         # Phase 118's case name, or "h0"


@dataclass
class RobinTwo:
    kind: str                         # "both" | "symbolic"
    y: str
    x: str
    length: str
    L: Optional[Fraction]
    equation: str
    family: str = ""                  # "D" | "N" for "symbolic"
    h: Optional[Fraction] = None      # numeric h (negative h, symbolic L)
    a: Optional[Fraction] = None
    b: Optional[Fraction] = None
    interval: str = ""
    eigenfunction: str = ""
    cases: List[RobinCase] = field(default_factory=list)
    roots: List[Tuple[Fraction, Fraction]] = field(default_factory=list)
    sign_text: str = ""

    def eigenvalues(self) -> List[Tuple[Fraction, Fraction]]:
        return [(lo * lo, hi * hi) for lo, hi in self.roots]


# ===========================================================================
# 1.  BOTH ENDS: SIGNS AND ENCLOSURES
# ===========================================================================

def both_sign(a: Fraction, b: Fraction, L: Fraction, k: Fraction) -> int:
    """The certified sign of ``(ab - k^2) sin(kL) + k(a + b) cos(kL)``."""
    (sl, sh), (cl, ch) = RB.sin_cos_bounds(k * L)
    p = RB._mul((sl, sh), a * b - k * k)
    q = RB._mul((cl, ch), k * (a + b))
    lo, hi = p[0] + q[0], p[1] + q[1]
    return 1 if lo > 0 else (-1 if hi < 0 else 0)


def enclose_both(a: Fraction, b: Fraction, L: Fraction, n: int,
                 width: Fraction = Fraction(1, 10 ** 13)
                 ) -> Tuple[Fraction, Fraction]:
    """The ``n``-th root (1-based) between two rationals of opposite
    certified sign, inside ``((n - 1) pi/L, n pi/L)``."""
    if n == 1:
        lo = Fraction(1, 1 << 10)
        while both_sign(a, b, L, lo) != 1:
            lo /= 2
    else:
        lo = (n - 1) * RB.PI_HI / L + Fraction(1, 10 ** 30)
    hi = n * RB.PI_LO / L - Fraction(1, 10 ** 30)
    lo, _ = RB._dyadic(lo)
    _, hi = RB._dyadic(hi)
    if lo <= (n - 1) * RB.PI_HI / L and n > 1:
        lo += Fraction(1, 1 << 80)
    if hi >= n * RB.PI_LO / L:
        hi -= Fraction(1, 1 << 80)
    sa, sb = both_sign(a, b, L, lo), both_sign(a, b, L, hi)
    if sa == 0 or sb == 0 or sa == sb:
        raise RobinError("NO_BRACKET", f"no certified sign change in "
                         f"interval {n}")
    while hi - lo > width:
        m = (lo + hi) / 2
        sm = both_sign(a, b, L, m)
        if sm == 0:                            # pragma: no cover
            break
        if sm == sa:
            lo = m
        else:
            hi = m
    return lo, hi


# ===========================================================================
# 2.  READING
# ===========================================================================

def _frac_text(q: Fraction) -> str:
    return str(q)


def _coef_times(c: Fraction, what: str) -> str:
    """``c*what`` printed: ``k``, ``2*k``, ``5/2*k``."""
    return what if c == 1 else f"{c}*{what}"


def _length(L: str) -> Optional[Fraction]:
    try:
        v = Fraction(L)
    except ValueError:
        if not re.fullmatch(r"[A-Za-z_]\w*", L):
            raise RobinError("UNREADABLE", f"cannot read the length {L!r}")
        return None
    if v <= 0:
        raise RobinError("UNREADABLE", "the interval must have positive "
                         "length")
    return v


def _interval_text(case: str, L: str, Lval: Optional[Fraction]) -> str:
    hlf = lambda m_: RB._pi_over(m_, L, Lval)
    n_pi = RB._pi_over("n", L, Lval)
    if case == "D+":
        return f"({hlf('(n - 1/2)')}, {n_pi}), n = 1, 2, 3, ..."
    if case == "D-weak":
        return (f"(0, {RB._half_pi_over(L, Lval)}) for n = 1; "
                f"({hlf('(n - 1)')}, {hlf('(n - 1/2)')}), n = 2, 3, ...")
    if case in ("D-0", "D-neg"):
        return f"({n_pi}, {hlf('(n + 1/2)')}), n = 1, 2, 3, ..."
    if case == "N+":
        return f"({hlf('(n - 1)')}, {hlf('(n - 1/2)')}), n = 1, 2, 3, ..."
    if case == "N-":
        return f"({hlf('(n - 1/2)')}, {n_pi}), n = 1, 2, 3, ..."
    if case == "D0":
        return f"k_n = {hlf('(n - 1/2)')}, n = 1, 2, 3, ..."
    if case == "N0":
        return f"k_n = {hlf('(n - 1)')}, n = 2, 3, ..."
    raise ValueError(case)


def _symbolic_robin(text: str, y: str, x: str
                    ) -> Optional[Tuple[str, str]]:
    """``(point, h)`` for ``d(y)/dx(P) + h*y(P) = 0`` (either order)."""
    t = re.sub(r"\s+", "", text)
    d = rf"d\({y}\)/d{x}\(([^()]+)\)"
    v = rf"([A-Za-z_]\w*)\*{y}\(([^()]+)\)"
    m = re.fullmatch(rf"{d}\+{v}=0", t)
    if m and m.group(1) == m.group(3):
        return m.group(1), m.group(2)
    m = re.fullmatch(rf"{v}\+{d}=0", t)
    if m and m.group(2) == m.group(3):
        return m.group(2), m.group(1)
    return None


def _both(y: str, x: str, zero, far, first_roots: int) -> RobinTwo:
    _, _, A0, B0 = zero
    L, _, A1, B1 = far
    a = -A0 / B0                     # y'(0) = a y(0)
    b = A1 / B1                      # y'(L) + b y(L) = 0
    if a <= 0 or b <= 0:
        raise RobinError("UNSUPPORTED", "Robin conditions at both ends with "
                         "a coefficient of the other sign (y'(0) = a*y(0), "
                         "y'(L) + b*y(L) = 0 with a <= 0 or b <= 0): the number "
                         "of negative eigenvalues then depends on a, b and L "
                         "together, which this operation does not decide")
    Lval = _length(L)
    kL = RB._kL(L, Lval)
    eq = (f"({_frac_text(a * b)} - k^2)*sin({kL}) + "
          f"{_coef_times(a + b, 'k')}*cos({kL}) = 0")
    interval = (f"({RB._pi_over('(n - 1)', L, Lval)}, "
                f"{RB._pi_over('n', L, Lval)}), n = 1, 2, 3, ...")
    ef = f"k_n*cos(k_n*{x}) + " + (f"sin(k_n*{x})" if a == 1 else
                                   f"{a}*sin(k_n*{x})")
    r = RobinTwo("both", y, x, L, Lval, eq, a=a, b=b, interval=interval,
                 eigenfunction=ef)
    r.sign_text = (
        f"lambda = k^2 > 0: y = {ef.replace('k_n', 'k')} meets y'(0) = "
        f"{a}*y(0) for every k, and the far end gives F(k) = ({a * b} - "
        f"k^2)*sin(k*{L}) + {a + b}*k*cos(k*{L}) = 0; at k = m*pi/{L} F = "
        f"(-1)^m*k*{a + b}, alternating, and F(k) > 0 near k = 0, so each "
        f"interval ((n - 1)*pi/{L}, n*pi/{L}) holds a root, and only one: "
        f"tan(k*{L}) = {a + b}*k/(k^2 - {a * b}) has one decreasing branch "
        f"on each side of k^2 = {a * b} against the increasing branches of "
        f"tan; lambda = 0: y = A + B*x with B = {a}*A and "
        f"A*({a + b} + {a * b}*{L}) = 0 gives y = 0; lambda = -mu^2 < 0: "
        f"(mu^2 + {a * b})*sinh(mu*{L}) + {a + b}*mu*cosh(mu*{L}) > 0, so no "
        f"negative eigenvalue")
    if Lval is not None:
        r.roots = [enclose_both(a, b, Lval, n) for n in
                   range(1, first_roots + 1)]
    return r


def _symbolic(y: str, x: str, family: str, L: str, h: str) -> RobinTwo:
    Lval = _length(L)
    kL = RB._kL(L, Lval)
    if family == "D":
        eq = f"tan({kL}) = -k/{h}"
        if Lval is None:
            hL = f"{h}*{L}"
            conds = [f"{h} > 0", f"{h} = 0", f"-1 < {hL} < 0", f"{hL} = -1",
                     f"{hL} < -1"]
        else:
            c = 1 / Lval
            conds = [f"{h} > 0", f"{h} = 0", f"-{c} < {h} < 0",
                     f"{h} = -{c}", f"{h} < -{c}"]
        names = ["D+", "D0", "D-weak", "D-0", "D-neg"]
        nonpos = ["none", "none", "none", "zero", "negative"]
        ef = f"sin(k_n*{x})"
    else:
        eq = f"k*tan({kL}) = {h}"
        conds = [f"{h} > 0", f"{h} = 0", f"{h} < 0"]
        names = ["N+", "N0", "N-"]
        nonpos = ["none", "zero", "negative"]
        ef = f"cos(k_n*{x})"
    r = RobinTwo("symbolic", y, x, L, Lval, eq, family=family,
                 eigenfunction=ef)
    r.cases = [RobinCase(c, _interval_text(nm, L, Lval), np_, nm)
               for c, nm, np_ in zip(conds, names, nonpos)]
    r.sign_text = _symbolic_sign_text(family, h, L)
    return r


def _negative_symbolic_length(y: str, x: str, L: str, h: Fraction
                              ) -> RobinTwo:
    c = -1 / h
    eq = f"tan(k*{L}) = {RB._coef_k(-1 / h)}"
    r = RobinTwo("symbolic", y, x, L, None, eq, family="D", h=h,
                 eigenfunction=f"sin(k_n*{x})")
    for cond, nm, np_ in ((f"{L} < {c}", "D-weak", "none"),
                          (f"{L} = {c}", "D-0", "zero"),
                          (f"{L} > {c}", "D-neg", "negative")):
        r.cases.append(RobinCase(cond, _interval_text(nm, L, None), np_, nm))
    r.sign_text = (_symbolic_sign_text("D", str(h), L) +
                   f"; with h = {h} the condition on h*{L} is a condition on "
                   f"{L}: h*{L} > -1 exactly when {L} < {c}")
    return r


def _symbolic_sign_text(family: str, h: str, L: str) -> str:
    if family == "D":
        return (f"y = sin(k*x) and f(k) = k*cos(k*{L}) + {h}*sin(k*{L}); "
                f"Phase 118's sign analysis in each sign class: h > 0 gives "
                f"one root in each ((n - 1/2)*pi/{L}, n*pi/{L}) and nothing "
                f"<= 0; h = 0 is the Dirichlet-Neumann problem, k_n = (n - "
                f"1/2)*pi/{L}; -1 < h*{L} < 0 moves the first root into (0, "
                f"pi/(2*{L})); h*{L} = -1 makes y = x an eigenfunction for "
                f"lambda = 0; h*{L} < -1 gives one negative eigenvalue with "
                f"tanh(mu*{L}) = -mu/h (y = sinh(mu*x)); in the last two the "
                f"positive roots sit in (n*pi/{L}, (n + 1/2)*pi/{L})")
    return (f"y = cos(k*x) and f(k) = -k*sin(k*{L}) + {h}*cos(k*{L}); h > 0 "
            f"gives one root in each ((n - 1)*pi/{L}, (n - 1/2)*pi/{L}) and "
            f"nothing <= 0; h = 0 is the Neumann problem, lambda = 0 with y = "
            f"1 and k_n = (n - 1)*pi/{L}; h < 0 gives one negative eigenvalue "
            f"with mu*tanh(mu*{L}) = -h (y = cosh(mu*x)) and the positive "
            f"roots in ((n - 1/2)*pi/{L}, n*pi/{L})")


def robin_two(ode: str, conditions: Sequence[str],
              first_roots: int = 3) -> RobinTwo:
    """The Phase 119 reading; raises :class:`RobinError` (``UNSUPPORTED``
    for what stays out of reach, ``UNREADABLE``, ...)."""
    m = SP._ODE.match(re.sub(r"\s+", "", ode.strip()))
    if not m or m.group(1) != m.group(3):
        if re.search(r"lambda\*\w+\*", re.sub(r"\s+", "", ode)):
            raise RobinError("UNSUPPORTED", "a coefficient that varies with "
                             "x: only y'' + lambda*y = 0 is solved")
        raise RobinError("UNREADABLE", "write d2(y)/dx2 + lambda*y = 0")
    y, x = m.group(1), m.group(2)
    if len(conditions) != 2:
        raise RobinError("UNREADABLE", "two conditions are needed")
    kinds = []
    for c in conditions:
        sym = _symbolic_robin(c, y, x)
        if sym is not None:
            kinds.append(("S", sym[0], sym[1], None))
            continue
        kind, pt = SP._condition(c, y, x)
        if kind == "R":
            pt, a, b = RB._robin_terms(c, y, x)
            kinds.append(("R", pt, a, b))
        elif kind in ("D", "N"):
            kinds.append((kind, pt, None, None))
        else:
            raise RobinError("UNREADABLE", "periodic and Robin conditions "
                             "together")
    zero = [k for k in kinds if k[1] == "0"]
    far = [k for k in kinds if k[1] != "0"]
    if len(zero) != 1 or len(far) != 1:
        raise RobinError("UNREADABLE", "one condition at x = 0 and one at "
                         "the other end")
    z, f = zero[0], far[0]
    L = f[1]
    if z[0] == "R" and f[0] == "R":
        return _both(y, x, z, (L, None, f[2], f[3]), first_roots)
    if f[0] == "S" and z[0] in ("D", "N"):
        return _symbolic(y, x, z[0], L, f[2])
    if z[0] == "S" or f[0] == "S":
        raise RobinError("UNSUPPORTED", "a symbolic Robin coefficient is read "
                         "at the far end only, as d(y)/dx(L) + h*y(L) = 0, "
                         "with a Dirichlet or Neumann end at 0")
    if z[0] == "D" and f[0] == "R" and _length(L) is None:
        h = f[2] / f[3]
        if h < 0:
            return _negative_symbolic_length(y, x, L, h)
    raise RobinError("UNSUPPORTED", "not one of the Robin problems this "
                     "operation reads")


def bounds_for(r: "RB.Robin") -> Optional[Tuple[str, str]]:
    """For a Dirichlet end, ``h > 0`` and a symbolic interval: the printed
    lower and upper bound of ``k_n*L``; ``None`` otherwise."""
    if r.case != "D+" or r.L is not None:
        return None
    h = r.h
    c = r.length if h == 1 else (f"{h}*{r.length}" if h.denominator == 1
                                 else f"({h})*{r.length}")
    return (f"(n - 1/2)*pi + arctan({c}/(n*pi))",
            f"(n - 1/2)*pi + arctan({c}/((n - 1/2)*pi))")
