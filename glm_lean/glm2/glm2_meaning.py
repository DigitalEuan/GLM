#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 MEANING  —  the exact semantic module  M = Q^10 (+) Q (+) Z (+) (Z/2)^3
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Layer  :  Tier 1 — what a concept *means*, exactly.
  Deps   :  standard library only.

  ------------------------------------------------------------------------
  Why this layer is bigger than GLM-1's (Z^7, +)
  ------------------------------------------------------------------------

  GLM-1 carried the seven SI base exponents as integers.  That is already
  enough to kill the mod-2 ceiling (E = mc^4 is rejected), but it cannot
  express any of the following, all of which are ordinary scientific
  distinctions:

    * sqrt(E/m) — a *rational* exponent vector, not an integer one;
    * torque (N m/rad) versus energy (J) — a plane-angle exponent;
    * radiance (W/(m^2 sr)) versus irradiance (W/m^2) — solid angle;
    * bit rate (bit/s) versus frequency (Hz) — an information exponent;
    * kilometre versus metre — a decimal scale exponent;
    * a pseudovector (torque, angular velocity, B) versus a vector (force,
      velocity, E) — behaviour under space inversion;
    * a T-odd quantity (velocity) versus a T-even one (position);
    * a rank-2 tensor (stress) versus a scalar (pressure);
    * degrees Celsius versus kelvin — an affine, not linear, scale.

  GLM-2 carries all of them, exactly.  A *meaning* is an element of

        M  =  Q^10  (+)  Q  (+)  Z  (+)  (Z/2)^3  (+)  labels

  where the ten rational exponents are over the axes

        L  length          A  plane angle       (rad)
        M  mass            S  solid angle       (sr)
        T  time            B  information       (bit)
        I  electric current
        H  thermodynamic temperature
        N  amount of substance
        J  luminous intensity

  the extra Q is the decimal scale (the exponent of 10 folded into the unit),
  the Z is tensor rank, and the three Z/2's are the space-inversion (P),
  time-reversal (T) and charge-conjugation (C) parities.

  ------------------------------------------------------------------------
  Mod 2 appears exactly once, and honestly
  ------------------------------------------------------------------------

  GLM-1's central negative result is that an F_2 (XOR) carrier can only ever
  compare exponents modulo 2, so it confuses d with d + 2u for every u.  In
  GLM-2 *no exponent is ever reduced mod 2*: exponents live in Q and are
  compared by exact rational equality.

  The only Z/2's in the system are P, T and C, and those are genuinely
  Z/2-valued: a parity is a sign, (-1)^2 = 1 is a fact about physics, not a
  loss of information.  So the rule GLM-2 follows is:

      mod 2 is used where the mathematics is genuinely Z/2-valued,
      and nowhere else.

  `mod2_shadow` is still provided, but only in the appendix of §3 and only as
  a *diagnostic*: it reports what an F_2 substrate would have concluded, so
  the ceiling stays visible as a measurement.  It is a free function and not a
  method of `Meaning`, because a meaning does not have a mod-2 view: meaning
  is the primary object here and the carrier is derived from it, never the
  other way round.

  ------------------------------------------------------------------------
  Group law
  ------------------------------------------------------------------------

      meaning(A B)   = meaning(A) + meaning(B)      exponents add,
                                                    ranks add,
                                                    parities add in Z/2
      meaning(A/B)   = meaning(A) - meaning(B)
      meaning(A^q)   = q * meaning(A)               q in Q; legal only when
                                                    q*rank is an integer, and
                                                    when q is not an integer
                                                    only for P=T=C=0 and
                                                    rank 0.

  Addition (A + B, as in "E = K + U") is legal only between *identical*
  meanings, which is exactly the admissibility rule the reasoner enforces.

      python3 glm2_meaning.py       # self-audit
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction as F
from math import gcd
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "AXES", "AXIS_LONG", "N_AXES", "DENOM",
    "Meaning", "SCALAR", "axis", "meaning_of",
    "ParseError", "PARITY_NAMES",
    "mod2_shadow", "mod2_confusable",
]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  THE AXES
# ══════════════════════════════════════════════════════════════════════════════

#: the ten exponent axes, in the order used everywhere in GLM-2
AXES: Tuple[str, ...] = ("L", "M", "T", "I", "H", "N", "J", "A", "S", "B")

AXIS_LONG: Tuple[str, ...] = (
    "length", "mass", "time", "electric current",
    "thermodynamic temperature", "amount of substance", "luminous intensity",
    "plane angle", "solid angle", "information",
)

N_AXES = len(AXES)

#: the global denominator of the encodable meaning module: every exponent and
#: the decimal scale live in (1/DENOM)Z.  DENOM = 12 covers halves, thirds,
#: quarters, sixths and twelfths, which is every fractional power that occurs
#: in dimensional analysis in practice.  Nothing in the algebra depends on it;
#: it is only the codec (glm2_codec) that needs a fixed lattice.
DENOM = 12

PARITY_NAMES = ("P", "T", "C")


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE MEANING MODULE
# ══════════════════════════════════════════════════════════════════════════════

class ParseError(ValueError):
    """Raised when an expression cannot be parsed or a name is unknown."""


def _frac(x) -> F:
    if isinstance(x, F):
        return x
    if isinstance(x, int):
        return F(x)
    if isinstance(x, str):
        return F(x)
    raise TypeError(f"expected an exact rational, got {type(x).__name__}")


@dataclass(frozen=True)
class Meaning:
    """
    An exact element of the GLM-2 meaning module.

    Fields
    ------
    exps    ten rational exponents, in AXES order
    scale   the decimal scale: the quantity is  10^scale x (SI coherent unit)
    rank    tensor rank (0 scalar, 1 vector, 2 second-rank tensor, ...)
    p       the space-inversion parity: 0 (even) or 1 (odd).  A quantity
            transforms under x -> -x by the sign (-1)^p, so a polar vector
            (force, position) has p = 1 and an axial one (torque, B) has
            p = 0.  P is genuinely independent of the exponents, which is
            why it is stored.
    t, c    the time-reversal and charge-conjugation ANOMALIES, 0 or 1.  By
            convention the T grading of a quantity is (e_T + e_I) mod 2 and
            the C grading is e_I mod 2 — both functions of the exponents,
            hence automatically additive and automatically consistent under
            products, quotients and rational powers.  A quantity whose real
            behaviour departs from that convention (the classic case is a
            particle's permanent electric dipole moment, which is T-odd
            although charge x length is T-even) records the departure in the
            anomaly, and `t_parity` / `c_parity` return the effective value.
            Anomalies are erased by fractional powers, since Z/2 has no
            square root.
    kind    a nominal-kind label: an integer >= 0 that separates quantities
            which are dimensionally identical but physically distinct
            (entropy vs heat capacity, say).  0 means "no nominal kind".
    domain  an integer >= 0 naming the discipline/namespace the concept was
            declared in; 0 is the shared namespace.

    Equality is exact and structural.  `same_dimension` compares only the ten
    exponents; `commensurable` compares everything a physicist would need to
    be equal before writing "=" between two quantities.
    """

    exps: Tuple[F, ...]
    scale: F = F(0)
    rank: int = 0
    p: int = 0
    t: int = 0
    c: int = 0
    kind: int = 0
    domain: int = 0

    # ── construction ─────────────────────────────────────────────────────────
    def __post_init__(self) -> None:
        if len(self.exps) != N_AXES:
            raise ValueError(f"Meaning: {N_AXES} exponents required")
        object.__setattr__(self, "exps", tuple(_frac(e) for e in self.exps))
        object.__setattr__(self, "scale", _frac(self.scale))
        for name in ("rank", "kind", "domain"):
            v = getattr(self, name)
            if not isinstance(v, int):
                raise TypeError(f"Meaning: {name} must be an int")
        for name in PARITY_NAMES:
            v = getattr(self, name.lower())
            if v not in (0, 1):
                raise ValueError(f"Meaning: parity {name} must be 0 or 1")
        if self.kind < 0 or self.domain < 0:
            raise ValueError("Meaning: kind and domain must be >= 0")

    @staticmethod
    def make(scale=0, rank: int = 0, p: int = 0, t: int = 0, c: int = 0,
             kind: int = 0, domain: int = 0, **exponents) -> "Meaning":
        """Keyword constructor: Meaning.make(L=2, M=1, T=-2) is an energy."""
        e = [F(0)] * N_AXES
        for key, value in exponents.items():
            if key not in AXES:
                raise ValueError(f"unknown axis {key!r}; axes are {AXES}")
            e[AXES.index(key)] = _frac(value)
        return Meaning(tuple(e), _frac(scale), rank, p, t, c, kind, domain)

    # ── group operations ─────────────────────────────────────────────────────
    def __add__(self, other: "Meaning") -> "Meaning":
        """
        The TENSOR product of two quantities: exponents, scale and rank add,
        parities add in Z/2, and the two nominal labels are dropped, because
        a derived quantity has no nominal kind of its own.  Contraction is a
        separate operation: see `contract` and `wedge`.
        """
        return Meaning(
            tuple(a + b for a, b in zip(self.exps, other.exps)),
            self.scale + other.scale,
            self.rank + other.rank,
            (self.p + other.p) % 2,
            (self.t + other.t) % 2,
            (self.c + other.c) % 2,
            0, 0,
        )

    def __neg__(self) -> "Meaning":
        return Meaning(tuple(-a for a in self.exps), -self.scale, -self.rank,
                       self.p, self.t, self.c, 0, 0)

    def contract(self, other: "Meaning") -> "Meaning":
        """
        The full contraction (dot product) of two tensor quantities: the
        tensor product with the rank reduced by two.  Energy is the
        contraction of force with displacement, not their tensor product,
        which is why `dot` exists in the expression language.
        """
        if self.rank < 1 or other.rank < 1:
            raise ParseError("contraction needs two quantities of rank >= 1")
        prod = self + other
        return Meaning(prod.exps, prod.scale, prod.rank - 2, prod.p, prod.t,
                       prod.c)

    def cross(self, other: "Meaning") -> "Meaning":
        """
        The plain cross product of two rank-1 quantities: rank 1 again, and
        the parities add, so the cross product of two polar vectors is axial.
        No angle appears: the Poynting vector E x H is an energy flux, not an
        energy flux per radian, and the curl equations of electromagnetism
        are exact in this operation.
        """
        if self.rank != 1 or other.rank != 1:
            raise ParseError("the cross product needs two rank-1 quantities")
        prod = self + other
        return Meaning(prod.exps, prod.scale, 1, prod.p, prod.t, prod.c)

    def moment(self, other: "Meaning") -> "Meaning":
        """
        The ROTATIONAL cross product: the plain cross product with one extra
        factor of inverse plane angle.

        Once the plane angle is a dimension in its own right, the two uses of
        `a x b` in physics stop being the same operation.  When the product
        converts between a rotation and a translation — torque r x F, which
        is an energy per radian; angular momentum r x p, which is an action
        per radian; the velocity omega x r of a rotating body — a radian is
        consumed, and the result carries A^-1.  When it does not — E x H —
        no radian appears.  GLM-2 gives the two operations different names
        instead of hiding the difference in a convention.
        """
        prod = self.cross(other)
        e = list(prod.exps)
        e[AXES.index("A")] -= 1
        return Meaning(tuple(e), prod.scale, 1, prod.p, prod.t, prod.c)

    def __sub__(self, other: "Meaning") -> "Meaning":
        return self + (-other)

    def power(self, q) -> "Meaning":
        """
        Raise to a rational power.  Fractional powers are legal only for
        rank-0, parity-even quantities: there is no square root of a
        pseudovector, and no square root of a rank-2 tensor.
        """
        q = _frac(q)
        if q.denominator != 1:
            if self.rank != 0:
                raise ParseError(
                    f"fractional power {q} of a rank-{self.rank} quantity")
            if self.p != 0:
                raise ParseError(f"fractional power {q} of a P-odd quantity")
            new_rank = 0
            par = (0, 0, 0)          # anomalies are erased: Z/2 has no root
        else:
            n = int(q)
            new_rank = self.rank * n
            par = ((self.p * n) % 2, (self.t * n) % 2, (self.c * n) % 2)
        return Meaning(tuple(a * q for a in self.exps), self.scale * q,
                       new_rank, par[0], par[1], par[2], 0, 0)

    def __mul__(self, q) -> "Meaning":
        return self.power(q)

    __rmul__ = __mul__

    # ── predicates ───────────────────────────────────────────────────────────
    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.exps)

    def is_pure_number(self) -> bool:
        """Dimensionless, unscaled, rank 0 and parity even: a plain number."""
        return (self.is_dimensionless() and self.scale == 0 and self.rank == 0
                and (self.p, self.t, self.c) == (0, 0, 0))

    def is_integral(self) -> bool:
        """True when every exponent is an integer."""
        return all(e.denominator == 1 for e in self.exps)

    def is_pseudo(self) -> bool:
        """
        True when the quantity picks up an extra sign under space inversion
        beyond the (-1)^rank its rank already implies: a pseudoscalar
        (rank 0, p = 1) or an axial vector (rank 1, p = 0).
        """
        return self.p != self.rank % 2

    def same_dimension(self, other: "Meaning") -> bool:
        return self.exps == other.exps

    def t_parity(self) -> Optional[int]:
        """The effective time-reversal grading, or None when the exponents
        are fractional and the convention does not apply."""
        eT, eI = self.exponent("T"), self.exponent("I")
        if eT.denominator != 1 or eI.denominator != 1:
            return None
        return (int(eT) + int(eI) + self.t) % 2

    def c_parity(self) -> Optional[int]:
        """The effective charge-conjugation grading, or None for fractional
        current exponents."""
        eI = self.exponent("I")
        if eI.denominator != 1:
            return None
        return (int(eI) + self.c) % 2

    def same_tensor_character(self, other: "Meaning") -> bool:
        return (self.rank, self.p, self.t_parity(), self.c_parity()) == \
               (other.rank, other.p, other.t_parity(), other.c_parity())

    def same_quantity(self, other: "Meaning") -> bool:
        """
        Equality of *physical content*: the ten exponents, the decimal scale
        and the tensor character (rank and the effective P, T, C gradings).
        The nominal labels `kind` and `domain` are deliberately ignored,
        because they are bookkeeping about where a name was declared, not
        part of the quantity.  Structural `==` compares those too; this is
        the predicate the reasoner and the laws use.
        """
        return (self.exps == other.exps and self.scale == other.scale
                and self.same_tensor_character(other))

    def commensurable(self, other: "Meaning") -> bool:
        """
        Everything that has to agree before an equals sign is legal:
        dimensions, decimal scale, tensor character and nominal kind (when
        both are labelled).
        """
        if not self.same_quantity(other):
            return False
        if self.kind and other.kind and self.kind != other.kind:
            return False
        return True

    def denominator(self) -> int:
        """The least common denominator of every rational field."""
        d = self.scale.denominator
        for e in self.exps:
            d = d * e.denominator // gcd(d, e.denominator)
        return d

    def encodable(self) -> bool:
        """True when the meaning lies in the (1/DENOM)Z lattice the codec uses."""
        return DENOM % self.denominator() == 0

    # ── views ────────────────────────────────────────────────────────────────
    def exponent(self, ax: str) -> F:
        return self.exps[AXES.index(ax)]

    def vector(self) -> Tuple[F, ...]:
        """The ten exponents plus the scale, as a rational 11-vector."""
        return self.exps + (self.scale,)

    def numerators(self) -> Tuple[int, ...]:
        """DENOM times the eleven rational fields, as integers (requires
        `encodable`)."""
        if not self.encodable():
            raise ValueError(f"meaning is not on the 1/{DENOM} lattice: {self}")
        return tuple(int(x * DENOM) for x in self.vector())

    def signature(self) -> str:
        """A short canonical string, e.g. 'L^2 M T^-2'."""
        parts = []
        for ax, e in zip(AXES, self.exps):
            if e == 0:
                continue
            parts.append(ax if e == 1 else f"{ax}^{_fmt(e)}")
        body = " ".join(parts) if parts else "1"
        if self.scale:
            body = f"10^{_fmt(self.scale)} {body}"
        tags = []
        if self.rank:
            tags.append(f"rank {self.rank}")
        for nm, v in zip(PARITY_NAMES, (self.p, self.t_parity(),
                                        self.c_parity())):
            if v:
                tags.append(f"{nm}-odd")
        if self.t:
            tags.append("T-anomaly")
        if self.c:
            tags.append("C-anomaly")
        if self.kind:
            tags.append(f"kind {self.kind}")
        if self.domain:
            tags.append(f"domain {self.domain}")
        return body + (f"  [{', '.join(tags)}]" if tags else "")

    def __str__(self) -> str:
        return self.signature()

    def __repr__(self) -> str:
        return f"Meaning({self.signature()})"


def _fmt(x: F) -> str:
    return str(x.numerator) if x.denominator == 1 else f"({x})"


def axis(name: str) -> Meaning:
    """The unit meaning of one axis, e.g. axis('L') is a length."""
    return Meaning.make(**{name: 1})


SCALAR = Meaning((F(0),) * N_AXES)


def meaning_of(**kw) -> Meaning:
    return Meaning.make(**kw)


# ══════════════════════════════════════════════════════════════════════════════
# §3.  APPENDIX — THE REJECTED F_2 CARRIER
# ══════════════════════════════════════════════════════════════════════════════
#
#  Nothing below is part of the system.  These two functions measure the
#  design GLM-1 rejected — a bit pattern composed by XOR — so that the reason
#  for making the meaning primary and the carrier derived stays a measurement.
#  `Meaning` deliberately has no mod-2 method: the shadow is not a view a
#  meaning offers, and no verdict in GLM-2 can reach it.
# ──────────────────────────────────────────────────────────────────────────────

def mod2_shadow(m: Meaning) -> Optional[Tuple[int, ...]]:
    """The F_2 shadow, or None when the meaning is not even representable
    in a mod-2 system (fractional exponents)."""
    if not m.is_integral():
        return None
    return tuple(int(e) % 2 for e in m.exps)


def mod2_confusable(a: Meaning, b: Meaning) -> bool:
    """
    True when a mod-2 (XOR) substrate would accept `a = b` although GLM-2
    rejects it.  This is exactly the failure mode GLM-1 characterised and
    GLM-2 never exhibits: it is reported, never acted on.
    """
    if a == b:
        return False
    sa, sb = mod2_shadow(a), mod2_shadow(b)
    return sa is not None and sa == sb


# ══════════════════════════════════════════════════════════════════════════════
# §4.  SELF-AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def _self_audit() -> Dict[str, object]:
    energy = Meaning.make(L=2, M=1, T=-2)
    mass = Meaning.make(M=1)
    speed = Meaning.make(L=1, T=-1)
    torque = Meaning.make(L=2, M=1, T=-2, A=-1, p=0, rank=1)

    out: Dict[str, object] = {}
    out["axes"] = N_AXES
    out["E=mc^2"] = (mass + speed.power(2)) == energy
    out["E=mc^4"] = (mass + speed.power(4)) == energy
    out["mod2 would accept E=mc^4"] = mod2_confusable(mass + speed.power(4), energy)
    out["sqrt(E/m) = speed"] = (energy - mass).power(F(1, 2)) == speed
    out["torque != energy"] = torque != energy
    out["torque vs energy: angle axis"] = torque.exponent("A") - energy.exponent("A")
    out["km != m"] = Meaning.make(L=1, scale=3) != Meaning.make(L=1)
    out["encodable(sqrt)"] = (energy - mass).power(F(1, 2)).encodable()
    return out


if __name__ == "__main__":  # pragma: no cover
    print("GLM-2 MEANING — self-audit")
    for k, v in _self_audit().items():
        print(f"  {k:34s} {v}")
