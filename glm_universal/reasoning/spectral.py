"""``glm_universal.reasoning.spectral`` -- eigenvalue problems and
one-point scattering, derived (Phase 107, ``studies/DERIVATION_TWO_STUDY.md``).

Eigenvalue problems
-------------------
``y'' + lambda y = 0`` on ``[0, L]`` with a Dirichlet (``y = 0``) or Neumann
(``y' = 0``) condition at each end, or periodic (``y(0) = y(P)``,
``y'(0) = y'(P)``).  :func:`eigenvalue_problem` works the way the textbook
does, in three cases of the sign of ``lambda``:

* ``lambda = -mu^2 < 0``: ``y = A cosh(mu x) + B sinh(mu x)``; the
  conditions are a 2x2 linear system whose determinant is a nonzero multiple
  of ``sinh(mu L)``, ``cosh(mu L)`` or ``1 - cosh(mu P)`` -- never zero for
  ``mu > 0`` -- so there is no negative eigenvalue;
* ``lambda = 0``: ``y = A + B x``; the determinant is a number or a multiple
  of ``L`` and decides whether ``0`` is an eigenvalue (the constants, for
  Neumann and periodic conditions);
* ``lambda = k^2 > 0``: ``y = A cos(k x) + B sin(k x)``; the determinant is
  a trigonometric polynomial in ``theta = k L`` (or ``k P``), and the
  machine recognises its zero set when it is a multiple of ``sin theta``
  (``theta = n pi``), ``cos theta`` (``theta = (n - 1/2) pi``) or
  ``1 - cos theta`` (``theta = 2 pi m``, a two-dimensional eigenspace).  Any
  other determinant -- a Robin condition gives ``k cos theta + c sin theta``
  -- has a transcendental zero set and is refused ``TRANSCENDENTAL``.

The eigenfunction is the null vector of the system, normalised by the
integral ``int_0^L sin^2(k x) dx = L/2 - sin(2 k L)/(4 k)`` (``= L/2`` at
every eigenvalue found here), and likewise for ``cos``.

Scattering at one point
-----------------------
:func:`transmission` -- a potential concentrated at ``x = 0``:
``alpha*delta(x)``, ``V0*step(x)``, or both.  With ``psi = e^{i k1 x} +
r e^{-i k1 x}`` on the left and ``t e^{i k2 x}`` on the right, continuity of
``psi`` and the jump ``psi'(0+) - psi'(0-) = g psi(0)``,
``g = 2 m alpha / hbar^2``, are two linear equations with complex
coefficients in ``r, t``, solved here by Cramer's rule over rational
functions in ``k1, k2, g``; ``T = (k2/k1) |t|^2``, ``R = |r|^2`` and
``R + T = 1`` is checked as an identity.  Below a step (``E < V0``) the
right-hand wave decays, it carries no current, ``T = 0``, and ``|r|^2 = 1``
is checked the same way.

Integers and ``Fraction`` only (D7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import symbolic as S

__all__ = ["SpectralError", "Eigen", "eigenvalue_problem", "Scattering",
           "transmission", "Cx"]


class SpectralError(Exception):
    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
# 1.  EIGENVALUE PROBLEMS
# ===========================================================================

@dataclass
class Eigen:
    y: str
    x: str
    length: str                        # L or P as text
    kinds: Tuple[str, str]             # (D|N, D|N) or (P, P)
    eigenvalue: str
    index: str
    eigenfunction: str
    zero_eigen: bool
    characteristic: str                # the determinant's zero set, in words
    negative: str                      # why no lambda < 0
    zero_text: str                     # the lambda = 0 case
    theta: str                         # the zero set in theta
    freq: Tuple[Fraction, Fraction]    # k L / pi = a*n + b (DN/N...) ; P: 2m
    normalisation: str


_ODE = re.compile(r"^d2\((\w+)\)/d(\w+)2\+lambda\*(\w+)=0$")


def _condition(text: str, y: str, x: str) -> Tuple[str, str]:
    """``(kind, point)`` for ``y(P) = 0`` / ``d(y)/dx(P) = 0`` or the two
    periodic forms (point ``"P"`` = the period)."""
    t = re.sub(r"\s+", "", text)
    m = re.fullmatch(rf"{y}\(([^()]+)\)=0", t)
    if m:
        return "D", m.group(1)
    m = re.fullmatch(rf"d\({y}\)/d{x}\(([^()]+)\)=0", t)
    if m:
        return "N", m.group(1)
    m = re.fullmatch(rf"{y}\(0\)={y}\(([^()]+)\)", t)
    if m:
        return "PV", m.group(1)
    m = re.fullmatch(rf"d\({y}\)/d{x}\(0\)=d\({y}\)/d{x}\(([^()]+)\)", t)
    if m:
        return "PD", m.group(1)
    if re.search(rf"{y}\(|d\({y}\)", t):
        return "R", t
    raise SpectralError("UNREADABLE", f"cannot read the condition {text!r}")


# Trigonometric polynomials in theta: {('s'|'c'|'1'): coefficient in k}
# with coefficients polynomials in k given as {power: Fraction}.
TP = Dict[str, Dict[int, Fraction]]


def _tp_add(a: TP, b: TP, sign: int = 1) -> TP:
    out = {key: dict(v) for key, v in a.items()}
    for key, poly in b.items():
        tgt = out.setdefault(key, {})
        for e, c in poly.items():
            tgt[e] = tgt.get(e, Fraction(0)) + sign * c
            if tgt[e] == 0:
                del tgt[e]
        if not tgt:
            del out[key]
    return out


def _tp_mul(a: TP, b: TP) -> TP:
    prod: TP = {}
    table = {("1", "1"): [("1", 1)], ("1", "s"): [("s", 1)],
             ("1", "c"): [("c", 1)], ("s", "s"): [("ss", 1)],
             ("c", "c"): [("cc", 1)], ("s", "c"): [("sc", 1)]}
    for ka, pa in a.items():
        for kb, pb in b.items():
            key = tuple(sorted((ka, kb), key="1sc".index))
            for kk, sgn in table[key]:
                poly: Dict[int, Fraction] = {}
                for ea, ca in pa.items():
                    for eb, cb in pb.items():
                        poly[ea + eb] = poly.get(ea + eb, Fraction(0)) + \
                            sgn * ca * cb
                prod = _tp_add(prod, {kk: {e: c for e, c in poly.items()
                                           if c}})
    # reduce s^2 = 1 - c^2 so that the forms are canonical
    if "ss" in prod:
        ss = prod.pop("ss")
        prod = _tp_add(prod, {"1": ss})
        prod = _tp_add(prod, {"cc": ss}, -1)
    return {k: v for k, v in prod.items() if v}


def _row(kind: str, at_end: bool) -> List[TP]:
    """The condition as a row over the basis (cos k x, sin k x): at ``x = 0``
    cos = 1, sin = 0, cos' = 0, sin' = k; at the far end cos(theta),
    sin(theta), -k sin(theta), k cos(theta)."""
    one: Dict[int, Fraction] = {0: Fraction(1)}
    kk: Dict[int, Fraction] = {1: Fraction(1)}
    if not at_end:
        return [{"1": one}, {}] if kind == "D" else [{}, {"1": kk}]
    if kind == "D":
        return [{"c": one}, {"s": one}]
    return [{"s": {1: Fraction(-1)}}, {"c": kk}]


def _det(m: List[List[TP]]) -> TP:
    return _tp_add(_tp_mul(m[0][0], m[1][1]), _tp_mul(m[0][1], m[1][0]), -1)


def _recognise(det: TP) -> Optional[str]:
    keys = set(det)
    if keys == {"s"}:
        return "sin"
    if keys == {"c"}:
        return "cos"
    if keys == {"1", "c"} and all(len(v) == 1 for v in det.values()):
        (e1, c1), = det["1"].items()
        (e2, c2), = det["c"].items()
        if e1 == e2 and c1 == -c2:
            return "1-cos"
    return None


def _tp_text(det: TP) -> str:
    def poly(p: Dict[int, Fraction]) -> str:
        terms = []
        for e in sorted(p, reverse=True):
            c = p[e]
            mono = "" if e == 0 else ("k" if e == 1 else f"k^{e}")
            if mono and c in (1, -1):
                terms.append(("-" if c < 0 else "") + mono)
            else:
                terms.append(f"{c}" + (f"*{mono}" if mono else ""))
        return " + ".join(terms).replace("+ -", "- ")
    names = {"1": "", "s": "sin(theta)", "c": "cos(theta)",
             "cc": "cos(theta)^2", "sc": "sin(theta)*cos(theta)"}
    parts = []
    for key in ("1", "c", "s", "cc", "sc"):
        if key in det:
            p = poly(det[key])
            if names[key]:
                p = f"({p})*{names[key]}" if "+" in p or " - " in p[1:] \
                    else (names[key] if p == "1" else
                          ("-" + names[key] if p == "-1" else
                           f"{p}*{names[key]}"))
            parts.append(p)
    return " + ".join(parts).replace("+ -", "- ") if parts else "0"


def _times(coef: str, var: str) -> str:
    return var if coef == "1" else f"{coef}*{var}"


def eigenvalue_problem(ode: str, conditions: Sequence[str]) -> Eigen:
    m = _ODE.match(re.sub(r"\s+", "", ode.strip()))
    if not m or m.group(1) != m.group(3):
        if re.search(r"lambda\*\w+\*\w+", re.sub(r"\s+", "", ode)) or \
                re.search(r"lambda\*\w+\*", re.sub(r"\s+", "", ode)):
            raise SpectralError("UNSUPPORTED",
                                "a coefficient that varies with x: only "
                                "y'' + lambda*y = 0 is solved in closed form")
        raise SpectralError("UNREADABLE",
                            "write d2(y)/dx2 + lambda*y = 0")
    y, x = m.group(1), m.group(2)
    if len(conditions) < 2:
        raise SpectralError("UNDERDETERMINED",
                            "a second-order problem needs two conditions")
    if len(conditions) > 2:
        raise SpectralError("UNREADABLE", "more than two conditions")
    conds = [_condition(c, y, x) for c in conditions]
    kinds = {k for k, _ in conds}
    if "R" in kinds:
        raise SpectralError(
            "TRANSCENDENTAL",
            "a condition mixing y and y' at one end makes the determinant "
            "k*cos(theta) + c*sin(theta): its zeros solve tan(theta) = "
            "-k/c, which has no closed form")
    if kinds <= {"PV", "PD"}:
        if kinds != {"PV", "PD"} or conds[0][1] != conds[1][1]:
            raise SpectralError("UNREADABLE",
                                "periodic conditions pair y and y' at the "
                                "same period")
        return _periodic(y, x, conds[0][1])
    if not kinds <= {"D", "N"}:
        raise SpectralError("UNREADABLE", "mixed periodic and end conditions")
    ends = {}
    for kind, pt in conds:
        ends.setdefault("0" if pt == "0" else pt, []).append(kind)
    if "0" not in ends or len(ends) != 2 or any(len(v) != 1
                                                for v in ends.values()):
        raise SpectralError("UNREADABLE",
                            "one condition at x = 0 and one at the other end")
    length = next(p for p in ends if p != "0")
    k0, kL = ends["0"][0], ends[length][0]
    det = _det([_row(k0, False), _row(kL, True)])
    shape = _recognise(det)
    if shape is None:                                  # pragma: no cover
        raise SpectralError("TRANSCENDENTAL", f"determinant {_tp_text(det)}")
    # lambda = 0: y = A + B x; rows (1, 0) for D at 0, (0, 1) for N; at L:
    # (1, L) for D, (0, 1) for N.
    r0 = (1, 0) if k0 == "D" else (0, 1)
    zero_eigen = (k0, kL) == ("N", "N")
    neg = {"sin": f"sinh(mu*{length})", "cos": f"cosh(mu*{length})"}[shape]
    neg_text = (f"lambda = -mu^2 < 0: y = A*cosh(mu*{x}) + B*sinh(mu*{x}); "
                f"the determinant is a nonzero multiple of {neg}, which is "
                f"never 0 for mu > 0, so no negative eigenvalue")
    zero_text = ("lambda = 0: y = A + B*" + x + "; " +
                 ("both conditions hold for every constant: lambda = 0 is an "
                  "eigenvalue" if zero_eigen else
                  "the only solution is y = 0, so 0 is not an eigenvalue"))
    L = length
    if shape == "sin":
        theta, idx = "n*pi", ("n = 0, 1, 2, ..." if zero_eigen
                              else "n = 1, 2, 3, ...")
        lam = f"(n*pi/{L})^2"
        arg = f"n*pi*{x}/{L}"
        freq = (Fraction(1), Fraction(0))
    else:
        theta, idx = "(n - 1/2)*pi", "n = 1, 2, 3, ..."
        lam = f"((2*n - 1)*pi/(2*{L}))^2"
        arg = f"(2*n - 1)*pi*{x}/(2*{L})"
        freq = (Fraction(1), Fraction(-1, 2))
    # the null vector: D at 0 kills cos, N at 0 kills sin
    fn = "sin" if k0 == "D" else "cos"
    ef = f"sqrt(2/{L})*{fn}({arg})"
    if zero_eigen:
        ef = f"1/sqrt({L}) for n = 0; {ef}"
    char = {"sin": f"sin(k*{L}) = 0", "cos": f"cos(k*{L}) = 0"}[shape]
    return Eigen(y, x, L, (k0, kL), lam, idx, ef, zero_eigen,
                 f"det = {_tp_text(det)} with theta = k*{L}: {char}",
                 neg_text, zero_text, theta, freq,
                 f"int_0^{L} {fn}^2(k*{x}) d{x} = {L}/2 at every eigenvalue")


def _up(P: str) -> str:
    return f"({P})" if re.search(r"[*/+-]", P) else P


def _kx(P: str) -> str:
    return f"k*({P})" if re.search(r"[*/+-]", P) else f"k*{P}"


def _periodic(y: str, x: str, period: str) -> Eigen:
    P = period
    one: Dict[int, Fraction] = {0: Fraction(1)}
    kk: Dict[int, Fraction] = {1: Fraction(1)}
    # rows over (cos, sin): y(0) - y(P) = (1 - cos th, -sin th);
    # y'(0) - y'(P) = (k sin th, k - k cos th)
    row1 = [{"1": one, "c": {0: Fraction(-1)}}, {"s": {0: Fraction(-1)}}]
    row2 = [{"s": kk}, {"1": kk, "c": {1: Fraction(-1)}}]
    det = _det([row1, row2])
    det = _tp_add(det, {})
    # (1-c)^2 + s^2 = 2 - 2c after s^2 = 1 - c^2 (cc cancels)
    shape = _recognise(det)
    if P.replace(" ", "") == "2*pi":
        lam, k, ef = "m^2", "m", f"exp(i*m*{x})/sqrt(2*pi)"
    elif P.replace(" ", "") == "pi":
        lam, k, ef = "4*m^2", "2*m", f"exp(2*i*m*{x})/sqrt(pi)"
    else:
        lam, k = f"(2*pi*m/{P})^2", f"2*pi*m/{P}"
        ef = f"exp(2*pi*i*m*{x}/{P})/sqrt({P})"
    return Eigen(
        y, x, P, ("P", "P"), lam, "m = 0, +-1, +-2, ...", ef, True,
        f"det = {_tp_text(det)} with theta = {_kx(P)}: cos({_kx(P)}) = 1, "
        f"and "
        f"there every entry vanishes, so cos and sin (equivalently "
        f"exp(+-i*k*{x})) are both eigenfunctions",
        f"lambda = -mu^2 < 0: the determinant is a nonzero multiple of "
        f"1 - cosh(mu*{P}), which is never 0 for mu > 0, so no negative "
        f"eigenvalue",
        f"lambda = 0: y = A + B*{x}; y(0) = y({P}) forces B = 0 and every "
        f"constant is periodic: lambda = 0 is an eigenvalue",
        "2*pi*m", (Fraction(2), Fraction(0)),
        f"int_0^{_up(P)} |exp(i*k*{x})|^2 d{x} = {P}")


# ===========================================================================
# 2.  SCATTERING AT ONE POINT
# ===========================================================================

class Cx:
    """A complex number with rational-function parts."""

    def __init__(self, re_: S.RF, im: S.RF):
        self.re, self.im = S.RF.of(re_), S.RF.of(im)

    def __add__(self, o: "Cx") -> "Cx":
        return Cx(self.re + o.re, self.im + o.im)

    def __sub__(self, o: "Cx") -> "Cx":
        return Cx(self.re - o.re, self.im - o.im)

    def __mul__(self, o: "Cx") -> "Cx":
        return Cx(self.re * o.re - self.im * o.im,
                  self.re * o.im + self.im * o.re)

    def conj(self) -> "Cx":
        return Cx(self.re, -self.im)

    def norm2(self) -> S.RF:
        return self.re * self.re + self.im * self.im

    def __truediv__(self, o: "Cx") -> "Cx":
        n = o.norm2()
        p = self * o.conj()
        return Cx(p.re / n, p.im / n)


def _r(text: str) -> S.RF:
    return S.parse(text)


@dataclass
class Scattering:
    potential: str
    below: bool
    has_delta: bool
    has_step: bool
    t: Optional[Cx]
    r: Cx
    T: S.RF                     # in k1, k2, g (or k, g)
    R: S.RF
    T_text: str
    T_energy: Optional[str]     # in m, E, hbar, alpha when it closes
    T_energy_rf: Optional[S.RF]
    strength: Optional[str]     # alpha (with its sign) in g = 2 m alpha/hbar^2
    equations: List[str] = field(default_factory=list)
    T_full: Optional[S.RF] = None   # with g = 2 m alpha / hbar^2 written out


_DELTA = re.compile(r"^([+-]?)\s*(\w+)\*delta\(x\)$")
_STEP = re.compile(r"^([+-]?)\s*(\w+)\*step\(x\)$")


def transmission(potential: str, relation: Optional[str] = None
                 ) -> Scattering:
    pot = potential.strip()
    terms, depth, cur = [], 0, ""
    for ch in pot.replace(" ", ""):
        if ch in "+-" and depth == 0 and cur:
            terms.append(cur)
            cur = ""
        depth += (ch == "(") - (ch == ")")
        cur += ch
    if cur:
        terms.append(cur)
    delta = step = None
    for t in terms:
        if re.search(r"delta\(x[-+]", t) or re.search(r"step\(x[-+]", t):
            raise SpectralError("UNSUPPORTED",
                                "a potential at more than one point: only "
                                "a delta and a step at x = 0 are derived")
        md, ms = _DELTA.match(t), _STEP.match(t)
        if md:
            if delta is not None:
                raise SpectralError("UNSUPPORTED", "two deltas")
            delta = ("-" if md.group(1) == "-" else "") + md.group(2)
        elif ms:
            if step is not None or ms.group(1) == "-":
                raise SpectralError("UNSUPPORTED", "a second or negative step")
            step = ms.group(2)
        else:
            raise SpectralError("UNREADABLE", f"cannot read the term {t!r}")
    rel = (relation or "").replace(" ", "")
    below = bool(step) and rel in (f"E<{step}",)
    if step and not below and rel not in (f"E>{step}",):
        raise SpectralError("UNREADABLE",
                            f"say whether E > {step} or E < {step}")
    k1 = _r("k1") if step else _r("k")
    k2 = (_r("kappa") if below else _r("k2")) if step else _r("k")
    g = _r("g") if delta else S.RF.of(0)
    r, t, R, T = _solve(k1, k2, g, below, bool(step))
    if not (R + T - 1).is_zero():                     # pragma: no cover
        raise SpectralError("INCONSISTENT", "R + T != 1")
    T_full = T
    if delta:
        T_full = _solve(k1, k2, S.parse(f"2*m*({delta})/hbar^2"), below,
                        bool(step))[3]
    eqs = ["psi continuous at 0: 1 + r = t",
           ("psi' jumps by g*psi(0): " +
            ("-kappa*t" if below else ("i*k2*t" if step else "i*k*t")) +
            f" - i*{'k1' if step else 'k'}*(1 - r) = g*t" if delta else
            "psi' continuous at 0: " +
            ("-kappa*t" if below else "i*k2*t") + " = i*k1*(1 - r)")]
    T_text, T_energy, T_e_rf = _t_text(T, step, delta, below)
    sc = Scattering(pot, below, bool(delta), bool(step), None if below
                    else t, r, T, R, T_text, T_energy, T_e_rf, delta, eqs)
    sc.T_full = T_full
    return sc


def _solve(k1: S.RF, k2: S.RF, g: S.RF, below: bool, step: bool):
    """Cramer's rule on the matching conditions; ``(r, t, R, T)``."""
    zero = S.RF.of(0)
    one = Cx(S.RF.of(1), zero)
    ik1 = Cx(zero, k1)
    # right-hand wave t e^{i k2 x} (derivative factor i k2), or below a
    # step t e^{-kappa x} (factor -kappa)
    d2 = Cx(-k2, zero) if below else Cx(zero, k2)
    # unknowns (r, t):
    #   r - t = -1                         (continuity)
    #   i k1 r + (d2 - g) t = i k1         (jump: d2 t - i k1 (1 - r) = g t)
    a11, a12, b1 = one, Cx(S.RF.of(-1), zero), Cx(S.RF.of(-1), zero)
    a21, a22, b2 = ik1, d2 - Cx(g, zero), ik1
    det = a11 * a22 - a12 * a21
    r = (b1 * a22 - a12 * b2) / det
    t = (a11 * b2 - b1 * a21) / det
    R = r.norm2()
    if below:
        T = S.RF.of(0)
    else:
        T = (k2 / k1) * t.norm2() if step else t.norm2()
    return r, t, R, T


def _t_text(T: S.RF, step, delta, below) -> Tuple[str, Optional[str],
                                                   Optional[S.RF]]:
    if below:
        return "0", None, None
    if step:
        k1, k2, g = _r("k1"), _r("k2"), _r("g")
        rest = (1 / T) * 4 * k1 * k2 - (k1 + k2) * (k1 + k2)
        if rest.is_zero():
            return "4*k1*k2/(k1 + k2)^2", None, None
        if (rest - g * g).is_zero():
            a = delta.lstrip("-")
            return (f"4*k1*k2/((k1 + k2)^2 + (2*m*{a}/hbar^2)^2)", None,
                    None)
        return S.to_text(T), None, None              # pragma: no cover
    # delta only: T = 1/(1 + g^2/(4 k^2)); g = 2 m alpha/hbar^2,
    # k^2 = 2 m E / hbar^2  ->  g^2/(4 k^2) = m alpha^2/(2 hbar^2 E)
    k, g = _r("k"), _r("g")
    x = 1 / T - 1
    if not (x - g * g / (4 * k * k)).is_zero():       # pragma: no cover
        return S.to_text(T), None, None
    a = delta.lstrip("-")
    energy = f"1/(1 + m*{a}^2/(2*hbar^2*E))"
    substituted = 1 / (1 + S.parse(f"(2*m*{a}/hbar^2)^2/(4*(2*m*E/hbar^2))"))
    if not (substituted - S.parse(energy)).is_zero():  # pragma: no cover
        return f"1/(1 + g^2/(4*k^2))", None, None
    return f"1/(1 + g^2/(4*k^2))", energy, substituted
