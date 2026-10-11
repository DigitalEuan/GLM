"""``glm_universal.reasoning.maxent`` -- maximum-entropy densities and
their differential entropies, derived from the log-partition function
(Phase 107, ``studies/DERIVATION_TWO_STUDY.md``).

The principle
-------------
Among densities on a support ``S`` with ``E[T_i(X)] = c_i``, the candidate
is ``f*(x) = exp(l0 + sum l_i T_i(x))``.  For *any* density ``f`` meeting
the same constraints, ``-int f log f* = -l0 - sum l_i c_i = h(f*)`` because
``log f*`` is affine in the ``T_i``; hence

    ``h(f) = h(f*) - D(f || f*) <= h(f*)``,

with equality only for ``f = f*`` (Gibbs' inequality; the discrete form is
``gibbs_inequality`` in ``RequestProject/GLM/DerivationsTwo.lean``).  So the
whole derivation is: find multipliers with ``f*`` integrable and the
constraints met, and read off ``h(f*) = -l0 - sum l_i c_i``.

The multipliers come from the log-partition function
``A(l) = log int_S exp(sum l_i T_i)``, whose gradient is the vector of
moments.  Three families have ``A`` in closed form, and the module derives
from them:

* ``S = (-inf, inf)``, ``T = (x, x^2)``: ``A = (1/2) ln(pi/a) + b^2/(4a)``
  with ``a = -l2 > 0``, ``b = l1``; ``E X = b/(2a)``,
  ``E X^2 = 1/(2a) + b^2/(4a^2)``.  With only ``E X`` constrained there is
  no ``l2``, ``exp(l1 x)`` is not integrable, and the entropy is unbounded
  (Gaussians of growing variance): refused ``UNBOUNDED``.
* ``S = [0, inf)``, ``T = x``: ``A = -ln(-l1)`` for ``l1 < 0``;
  ``E X = -1/l1``.  A second-moment constraint there gives a truncated
  Gaussian whose partition function needs ``erf``: refused ``UNSUPPORTED``.
* ``S = [a, b]``, no ``T``: ``A = ln(b - a)``.  A mean constraint there gives
  ``E X = coth``-type equation in ``l1`` with no closed form: refused
  ``TRANSCENDENTAL``.

Every multiplier is a rational function of the constraint values, solved
with :mod:`glm_universal.reasoning.symbolic`; the logarithmic part of ``l0``
is carried as a symbol ``ln(...)``.  Integers and ``Fraction`` only (D7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import symbolic as S

__all__ = ["MaxEntError", "MaxEnt", "maximum_entropy"]


class MaxEntError(Exception):
    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


@dataclass
class MaxEnt:
    support: str
    constraints: Dict[str, str]
    family: str
    density: str
    entropy: str                    # nats
    entropy_bits: str
    multipliers: Dict[str, str]     # l0 (rational part), l1, l2 as text
    log_term: str                   # the ln(...) inside -l0
    partition: str
    moments: List[str]
    # for the column-3 script: rational parameters of the family
    params: Dict[str, str]


def _support(text: str) -> str:
    t = text.replace(" ", "").lower()
    if t in ("(-inf,inf)", "(-infinity,infinity)", "r", "(-oo,oo)"):
        return "R"
    if t in ("[0,inf)", "[0,infinity)", "[0,oo)"):
        return "R+"
    m = re.fullmatch(r"\[(\w+),(\w+)\]", t)
    if m:
        return f"[{m.group(1)},{m.group(2)}]"
    raise MaxEntError("UNREADABLE", f"cannot read the support {text!r}")


def _constraints(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    t = text.strip()
    if not t:
        return out
    for part in re.split(r"\s+and\s+|,\s*", t):
        m = re.fullmatch(r"(mean|variance|second moment)\s+(\S+)", part.strip())
        if not m:
            raise MaxEntError("UNREADABLE", f"cannot read {part!r}")
        out[m.group(1)] = m.group(2)
    return out


def maximum_entropy(support_text: str, constraint_text: str = "") -> MaxEnt:
    sup = _support(support_text)
    cons = _constraints(constraint_text)
    if sup == "R":
        return _real_line(cons, support_text)
    if sup == "R+":
        return _half_line(cons, support_text)
    a, b = sup[1:-1].split(",")
    if cons:
        if set(cons) == {"mean"}:
            raise MaxEntError(
                "TRANSCENDENTAL",
                f"on [{a}, {b}] with a mean the density is exp(l0 + l1*x) "
                f"and the mean constraint reads ({b}*e^(l1*{b}) - "
                f"{a}*e^(l1*{a}))/(e^(l1*{b}) - e^(l1*{a})) - 1/l1 = mu, an "
                f"equation in l1 with no closed-form root")
        raise MaxEntError("UNSUPPORTED", "only no constraint, or a mean, is "
                                         "declared on a bounded interval")
    w = f"{b} - {a}"
    return MaxEnt(f"[{a}, {b}]", {}, "uniform", f"1/({w})", f"ln({w})",
                  f"log2({w})", {"l0": f"-ln({w})"}, f"ln({w})",
                  f"A = ln(int_{a}^{b} dx) = ln({w})", [],
                  {"width": w})


def _real_line(cons: Dict[str, str], sup: str) -> MaxEnt:
    keys = set(cons)
    if keys == {"mean"} or not keys:
        raise MaxEntError(
            "UNBOUNDED",
            "on (-inf, inf) with only a mean fixed the candidate exp(l0 + "
            "l1*x) is not integrable for any l1, and Gaussians with that "
            "mean and growing variance have entropy (1/2)*ln(2*pi*e*v) -> "
            "infinity: there is no maximum")
    if keys == {"mean", "variance"}:
        mu, var = cons["mean"], cons["variance"]
        m_rf, v_rf = S.parse(mu), S.parse(var)
        second = v_rf + m_rf * m_rf
    elif keys == {"second moment"}:
        mu, var = "0", cons["second moment"]
        m_rf, v_rf = S.RF.of(0), S.parse(var)
        second = v_rf
    else:
        raise MaxEntError("UNSUPPORTED", f"constraints {sorted(keys)} on the "
                                         f"real line are not declared")
    # solve E X = b/(2a) = mu, E X^2 = 1/(2a) + b^2/(4a^2) = second:
    # second - mu^2 = 1/(2a)  ->  a = 1/(2*(second - mu^2)), b = 2*a*mu
    vv = second - m_rf * m_rf
    if vv.is_zero():                                     # pragma: no cover
        raise MaxEntError("UNBOUNDED", "zero variance")
    a = 1 / (2 * vv)
    b = 2 * a * m_rf
    l1, l2 = b, -a
    # l0 = -A = -(1/2) ln(pi/a) - b^2/(4a)
    l0_rat = -(b * b) / (4 * a)
    # h = -l0 - l1*mu - l2*second = (1/2) ln(pi/a) + b^2/(4a) - b*mu + a*second
    h_rat = -l0_rat - l1 * m_rf - l2 * second
    if not (h_rat - S.RF.of(1) / 2).is_zero():           # pragma: no cover
        raise MaxEntError("INCONSISTENT", "the entropy did not reduce")
    vt = _tt(vv)
    vp = _paren(vt)
    if mu == "0":
        dens = f"exp(-x^2/(2*{vp}))/sqrt(2*pi*{vp})"
    else:
        dens = f"exp(-(x - {mu})^2/(2*{vp}))/sqrt(2*pi*{vp})"
    # pi/a = 2*pi*v, so (1/2) ln(pi/a) + 1/2 = (1/2) ln(2*pi*e*v)
    return MaxEnt(
        "(-inf, inf)", cons, "gaussian", dens,
        f"(1/2)*ln(2*pi*e*{vp})", f"(1/2)*log2(2*pi*e*{vp})",
        {"l0": ("" if l0_rat.is_zero() else _tt(l0_rat) + " ") +
         f"- (1/2)*ln(2*pi*{vp})", "l1": _tt(l1),
         "l2": _tt(l2)},
        f"(1/2)*ln(2*pi*{vp})",
        "A(l1, l2) = (1/2)*ln(pi/a) + b^2/(4*a), a = -l2 > 0, b = l1",
        [f"E X = b/(2*a) = {mu}", f"E X^2 = 1/(2*a) + b^2/(4*a^2) = "
                                  f"{_tt(second)}",
         f"so a = {_tt(a)}, b = {_tt(b)}"],
        {"mu": mu, "var": vt})


def _half_line(cons: Dict[str, str], sup: str) -> MaxEnt:
    keys = set(cons)
    if not keys:
        raise MaxEntError("UNBOUNDED", "on [0, inf) with nothing fixed the "
                                       "entropy is unbounded")
    if keys != {"mean"}:
        raise MaxEntError(
            "UNSUPPORTED",
            "on [0, inf) with a second moment the candidate is a truncated "
            "Gaussian, whose partition function needs erf: not derived in "
            "closed form")
    mu = cons["mean"]
    m_rf = S.parse(mu)
    l1 = -1 / m_rf                  # E X = -1/l1 = mu
    h_rat = -l1 * m_rf              # h = -l0 - l1*mu, -l0 = A = -ln(-l1) = ln(mu)
    if not (h_rat - 1).is_zero():                         # pragma: no cover
        raise MaxEntError("INCONSISTENT", "the entropy did not reduce")
    return MaxEnt(
        "[0, inf)", cons, "exponential", f"exp(-x/{_paren(mu)})/{_paren(mu)}",
        f"1 + ln({mu})", f"log2(e) + log2({mu})",
        {"l0": f"-ln({mu})", "l1": _tt(l1)}, f"ln({mu})",
        "A(l1) = -ln(-l1) for l1 < 0", [f"E X = -1/l1 = {mu}"], {"mu": mu})


def _tt(rf: S.RF) -> str:
    return S.to_text(rf)


def _paren(t: str) -> str:
    return t if re.fullmatch(r"[A-Za-z_]\w*(\^\d+)?|\d+", t) else f"({t})"
