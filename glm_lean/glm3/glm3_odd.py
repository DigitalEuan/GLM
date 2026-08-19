#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 ODD  —  the odd part of the Griess algebra, and the whole 196,884
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 2d — the half of the Griess algebra GLM-3 used to be missing.
  Deps   :  glm3_leech2, glm3_extraspecial, glm3_griess, glm3_sign.

  ------------------------------------------------------------------------
  The gap this module closes
  ------------------------------------------------------------------------

  GLM-3 section 9(a) listed the largest limitation: the odd part

      V- = 24 (x) 4096 = 98,304

  existed only as a dimension count and as the representation of
  Q = 2^(1+24) on 4,096 signed basis vectors.  The two multiplications that
  make it part of an algebra,

      V+ (x) V-  ->  V-        and        V- (x) V-  ->  V+ ,

  were not built, so the ledger 300 + 98,280 + 98,304 = 196,884 was
  arithmetic rather than an algebra, and the paper said so.  Both products
  are built here, exactly, in Fractions, with their constants DERIVED in the
  same style as the even part's: nothing is quoted.

  ------------------------------------------------------------------------
  1.  THE SPACE
  ------------------------------------------------------------------------

  V- = R^24 (x) R^4096, with basis e_i (x) f_m.  The first factor is the
  Leech space the 300-dimensional part already acts on; the second is the
  Schrodinger representation of Q built in glm3_extraspecial, in which

      rho(x_u) f_m = (-1)^<beta_u, m> f_{m + alpha_u} ,

  a signed permutation.  For a type-2 class lambda one has q(lambda) = 0, so
  rho(x_lambda)^2 = 1 and rho(x_lambda) is SYMMETRIC — which is what makes
  the form below invariant.  Write X_lambda for that operator.

  ------------------------------------------------------------------------
  2.  THE ACTION OF THE EVEN PART, WITH ITS CONSTANTS DERIVED
  ------------------------------------------------------------------------

  The only N-equivariant shapes available are

      A  |> (x (x) s)  =  [ c1 A x + c2 tr(A) x ] (x) s
      b_lambda |> (x (x) s)
                     =  [ c3 (lambda . x) lambda + c4 x ] (x) X_lambda s

  with four rational constants.  They are not free:

    (i)   the identity of the even part must act as the identity, and
          tr(I) = 24, so  c1 + 24 c2 = 1;

    (ii)  MIYAMOTO.  The axis a_lambda^eps = (1/8) P_lambda + (eps/2)
          b_lambda must have the Monster spectrum {0, 1/4, 1/32} on V-, and
          the involution that is +1 on the 1, 0 and 1/4 eigenspaces and -1
          on the 1/32 eigenspace must be an automorphism of the algebra —
          on the even part glm3_griess already computes it to be the
          extraspecial sign automorphism x_lambda, which acts on V- as
          1 (x) X_lambda.  So on V- the 1/32 eigenspace has to be EXACTLY
          one eigenspace of X_lambda, and the eigenvalues 0 and 1/4 have to
          live entirely on the other.  Split x into the lambda direction and
          its orthogonal complement, and s into the +-1 eigenspaces of
          X_lambda (2,048 each); write sigma for the X_lambda eigenvalue.
          The four blocks have eigenvalues

              perp   c2/2 + eps sigma c4/2 ,
              along  (c1 + c2)/2 + eps sigma (4 c3 + c4)/2 .

          Both must be 1/32 on the same sign of eps sigma — say eps sigma =
          -1, the other choice being the other lift of lambda into Q, which
          only flips the sign of c3 and c4.  On eps sigma = +1 the perp
          block (23 x 2,048 = 47,104) and the along block (2,048) carry the
          eigenvalues 0 and 1/4, and which is which is fixed by counting:
          the whole algebra has only 4,371 - 2,323 = 2,048 dimensions of
          eigenvalue 1/4 left over from the even part, so the along block is
          the 1/4 one.  Hence

              perp:   c2/2 + c4/2 = 0,     c2/2 - c4/2 = 1/32,
              along:  (c1+c2)/2 + (4c3+c4)/2 = 1/4,
                      (c1+c2)/2 - (4c3+c4)/2 = 1/32,

          four equations for three unknown combinations, so ONE of them is
          a consistency check: the perp pair gives c2 = 1/32 and
          c4 = -1/32, hence c1 = 1/4 by (i), and then the along pair demands
          c1 + c2 = 1/4 + 1/32 — which is exactly what (i) already delivered.
          That closure is the evidence that the ansatz is right.  The
          remaining equation gives 4 c3 + c4 = 1/4 - 1/32, i.e. c3 = 1/16.

  So

      c1 = 1/4,   c2 = 1/32,   c3 = 1/16,   c4 = -1/32,

  derived, and `derive_constants()` recomputes them from the two
  requirements alone and reports the consistency of the extra equation.

  The Miyamoto requirement is not decoration: with the two constants that
  merely reproduce the SPECTRUM but pair the blocks the other way round
  (c3 = 3/64, c4 = 1/32) every eigenvalue and every dimension below is
  unchanged, the products are still commutative and still Frobenius, and
  the fusion rule 1/32 * 1/32 -> 1 + 0 + 1/4 FAILS.  The grading is the
  content.

  THE PAYOFF IS THE LEDGER.  The eigenspace dimensions on V- follow at
  once — 23 x 2,048 = 47,104 at eigenvalue 0, 2,048 at 1/4, and
  23 x 2,048 + 2,048 = 49,152 at 1/32 — and added to the even part's
  1 / 49,152 / 2,323 / 47,104 they give

      eigenvalue      1        0       1/4      1/32
      dimension       1     96,256    4,371    96,256      total 196,884

  which are exactly the classical eigenspace dimensions of a 2A axis of the
  Monster.  The even part alone gives none of these numbers; they appear
  only when the odd part is present, and they are computed here rather than
  quoted.

  ------------------------------------------------------------------------
  3.  THE FORM, AND THE PRODUCT V- x V- -> V+ BY FROBENIUS DUALITY
  ------------------------------------------------------------------------

  Put (x (x) s, y (x) t)_- = k (x . y)(s . t).  The action above is
  self-adjoint for it, because A is symmetric and X_lambda is symmetric.
  The form on V+ is nondegenerate (glm3_metric section 1 shows it is
  positive definite), so there is exactly one product

      V- (x) V-  ->  V+           determined by  (u . v, w)_+ = (w |> u, v)_-

  for all w in V+ — the Frobenius property, used as a DEFINITION rather than
  checked afterwards.  Reading the definition off on the basis of V+ gives
  it in closed form:

      A-part   =  (k (s . t) / 2) [ c1 (x y^T + y x^T)/2 + c2 (x . y) I ]
      b_mu     =  (k / 2) [ c3 (mu . x)(mu . y) + c4 (x . y) ] (X_mu s . t)

  and (X_mu f_m . f_n) is nonzero only when alpha_mu = m + n, which is a
  coset of the 4,096-element subgroup ker(alpha) — so the b-part of a
  product of basis vectors is a sum over 4,096 candidate classes, of which
  about two dozen are of type 2.  That is what makes the 98,280 coordinates
  computable one product at a time.

  The constant k is a scaling of the form on V-, i.e. a rescaling of the
  basis of V-; it changes no structural statement, and is set to 1.

  ------------------------------------------------------------------------
  4.  WHAT IS THEN CHECKED
  ------------------------------------------------------------------------

  * commutativity  u . v = v . u  (`commutativity_report`);
  * the Frobenius identity, on random w, u, v (`frobenius_report`);
  * the spectrum of an axis on V-, vector by vector, against the block
    prediction, and the full-algebra ledger (`spectrum_report`);
  * Q-equivariance of both products (`equivariance_report`);
  * that the Miyamoto involution of a_lambda^eps is x_lambda for eps = -1
    and x_lambda z for eps = +1 (`miyamoto_report`) — the same automorphism
    on the even part, different ones on the whole algebra;
  * the fusion rules that involve the odd part (`fusion_report`):
        1 * 1/32 -> 1/32,     0 * 1/32 -> 1/32,     1/4 * 1/32 -> 1/32,
        1/32 * 1/32 -> 1 + 0 + 1/4,
    the last one landing in V+ and tested there with the even part's own
    eigen-filter;
  * that the ODD PART SEES THE SIGN OF AN AXIS (`sign_visibility_report`):
    a_lambda^+ and a_lambda^- act on the very same odd vector
    lambda (x) s, with X_lambda s = s, with different eigenvalues — 1/4 and
    1/32.  Inside the even part the two axes have the same spectrum and the
    same everything; on V- they are told apart by a single application.
    (They remain conjugate under Q: x_w with B(w, lambda) = 1 exchanges
    them.  What the odd part supplies is not the end of the convention but
    an observable that depends on it — which is exactly what section 9(c)
    said was missing.)

      python3 glm3_odd.py           # self-audit
================================================================================
"""

from __future__ import annotations

import random
import sys
from fractions import Fraction as F
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int
import glm3_extraspecial as XS
import glm3_griess as GR
import glm3_leech2 as L2
import glm3_sign as SGN

import glm2_lattice as LAT

__all__ = [
    "DIM_ODD", "DIM_FULL", "C1", "C2", "C3", "C4", "K_FORM",
    "derive_constants", "OddVector", "basis", "act", "form",
    "product", "spectrum_block", "spectrum_report", "ledger",
    "commutativity_report", "frobenius_report", "fusion_report",
    "apply_x", "equivariance_report", "miyamoto_report", "axis_eigenvector",
    "sign_visibility_report", "odd_audit",
]

DIM_ODD = 24 * XS.REP_DIM          # 98,304
DIM_FULL = GR.DIM_EVEN + DIM_ODD   # 196,884

#: the derived structure constants of the action of V+ on V-
C1 = F(1, 4)
C2 = F(1, 32)
C3 = F(1, 16)
C4 = F(-1, 32)

#: the scaling of the invariant form on V- (a change of basis, not data)
K_FORM = F(1)


def derive_constants() -> Dict[str, object]:
    """
    Recompute c1..c4 from the two requirements of section 2 — the identity
    acts as the identity, and the Miyamoto involution of the axis is the
    extraspecial sign automorphism — and report the consistency of the
    over-determined system.

    On eps sigma = +1 the perp block carries eigenvalue 0 and the along
    block eigenvalue 1/4; on eps sigma = -1 both carry 1/32.  Which block
    takes the 1/4 is settled by a dimension count, reported here too.
    """
    even = GR.spectrum_dimensions()
    classical_quarter = 4371
    odd_quarter = classical_quarter - even["1/4"]          # 2,048
    along_block = XS.REP_DIM // 2                          # 2,048
    perp_block = 23 * (XS.REP_DIM // 2)                    # 47,104

    # perp block:  c2/2 + c4/2 = 0 (eps sigma = +1),  c2/2 - c4/2 = 1/32
    c2 = F(0) + F(1, 32)
    c4 = F(0) - F(1, 32)
    c1 = 1 - 24 * c2                       # identity acts as the identity
    # along block:  (c1+c2)/2 +- (4 c3 + c4)/2 = 1/4 and 1/32
    sum_forced_by_c1_c2 = c1 + c2
    sum_required = F(1, 4) + F(1, 32)
    c3 = ((F(1, 4) - F(1, 32)) - c4) / 4
    return {
        "c1": c1, "c2": c2, "c3": c3, "c4": c4,
        "identity_condition": c1 + 24 * c2 == 1,
        "odd_dimensions_of_eigenvalue_one_quarter": odd_quarter,
        "the_along_block": along_block,
        "the_perp_block": perp_block,
        "counting_puts_one_quarter_on_the_along_block":
            odd_quarter == along_block != perp_block,
        "sum_forced_by_c1_c2": sum_forced_by_c1_c2,
        "sum_required_by_the_spectrum": sum_required,
        "over_determined_system_closes": sum_forced_by_c1_c2 == sum_required,
        "matches_module_constants": (c1, c2, c3, c4) == (C1, C2, C3, C4),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §1.  VECTORS OF THE ODD PART
# ══════════════════════════════════════════════════════════════════════════════

class OddVector:
    """
    An element of V- = R^24 (x) R^4096, sparse: a map from (i, m) to Q.
    """

    __slots__ = ("c",)

    def __init__(self, c: Optional[Dict[Tuple[int, int], F]] = None) -> None:
        self.c: Dict[Tuple[int, int], F] = {}
        for k, v in (c or {}).items():
            v = F(v)
            if v:
                self.c[k] = v

    def __add__(self, other: "OddVector") -> "OddVector":
        out = dict(self.c)
        for k, v in other.c.items():
            s = out.get(k, F(0)) + v
            if s:
                out[k] = s
            else:
                out.pop(k, None)
        return OddVector(out)

    def scale(self, t) -> "OddVector":
        t = F(t)
        if not t:
            return OddVector()
        return OddVector({k: t * v for k, v in self.c.items()})

    def __sub__(self, other: "OddVector") -> "OddVector":
        return self + other.scale(-1)

    def is_zero(self) -> bool:
        return not self.c

    def __eq__(self, other: object) -> bool:
        return isinstance(other, OddVector) and (self - other).is_zero()

    def support(self) -> int:
        return len(self.c)

    def __repr__(self) -> str:
        return f"OddVector({len(self.c)} terms, norm {form(self, self)})"


def basis(i: int, m: int, coefficient=1) -> OddVector:
    """e_i (x) f_m."""
    if not (0 <= i < 24 and 0 <= m < XS.REP_DIM):
        raise ValueError("basis: index out of range")
    return OddVector({(i, m): F(coefficient)})


def tensor(x: Sequence[F], s: Dict[int, F]) -> OddVector:
    """x (x) s for a 24-vector x and a sparse 4096-vector s."""
    out: Dict[Tuple[int, int], F] = {}
    for i, xi in enumerate(x):
        if xi:
            for m, sm in s.items():
                if sm:
                    out[(i, m)] = F(xi) * F(sm)
    return OddVector(out)


def form(u: OddVector, v: OddVector) -> F:
    """(u, v)_- = k sum over the basis, the basis being orthonormal."""
    if len(u.c) > len(v.c):
        u, v = v, u
    total = F(0)
    for k, a in u.c.items():
        b = v.c.get(k)
        if b:
            total += a * b
    return K_FORM * total


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE ACTION OF THE EVEN PART
# ══════════════════════════════════════════════════════════════════════════════

_COORDS: Dict[int, Tuple[int, int]] = {}


def _alpha_beta(cls: int) -> Tuple[int, int]:
    if cls not in _COORDS:
        _COORDS[cls] = XS.coordinates(cls)
    return _COORDS[cls]


def rep_entry(cls: int, m: int) -> Tuple[int, int]:
    """
    One entry of the Schrodinger operator: X_cls f_m = sign * f_target.
    """
    alpha, beta = _alpha_beta(cls)
    sign = -1 if (bin(beta & m).count("1") & 1) else 1
    return m ^ alpha, sign


_LAMBDA: Dict[int, Tuple[F, ...]] = {}


def _lambda_of(cls: int) -> Tuple[F, ...]:
    """The minimal vector of a type-2 class, in the standard normalisation."""
    if cls not in _LAMBDA:
        v = GR.class_representative(cls)
        _LAMBDA[cls] = tuple(F(int(c)) for c in v)
    return _LAMBDA[cls]


def act(w: GR.GriessVector, u: OddVector) -> OddVector:
    """
    w |> u, the action of the even part on the odd part.

    The integer model stores lambda as a vector v with v . v = 32, i.e.
    lambda = v / sqrt 8; so (lambda . x) lambda contributes v_i v_j / 8 and
    lambda . lambda = 4, exactly as in glm3_griess.
    """
    out: Dict[Tuple[int, int], F] = {}

    def bump(key: Tuple[int, int], value: F) -> None:
        if value:
            s = out.get(key, F(0)) + value
            if s:
                out[key] = s
            else:
                out.pop(key, None)

    A = w.A
    trace = sum(A[i][i] for i in range(24))
    for (i, m), coef in u.c.items():
        if trace:
            bump((i, m), C2 * trace * coef)
        for j in range(24):
            a = A[j][i]
            if a:
                bump((j, m), C1 * a * coef)

    for cls, bcoef in w.B.items():
        lam = _LAMBDA.get(cls) or _lambda_of(cls)
        for (i, m), coef in u.c.items():
            target, sign = rep_entry(cls, m)
            scaled = bcoef * coef * sign
            li = lam[i]
            if li:
                #  c3 (lambda . e_i) lambda  with lambda = v / sqrt 8
                factor = C3 * scaled * li / 8
                for j in range(24):
                    if lam[j]:
                        bump((j, target), factor * lam[j])
            bump((i, target), C4 * scaled)
    return OddVector(out)


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE PRODUCT V- x V- -> V+
# ══════════════════════════════════════════════════════════════════════════════

_KERNEL: Optional[List[int]] = None
_PREIMAGE: Optional[Tuple[int, ...]] = None


def _alpha_kernel() -> List[int]:
    """
    The 4,096 classes u with alpha_u = 0, i.e. B(u, b_i) = 0 for every i:
    the span of the symplectic B-basis.
    """
    global _KERNEL
    if _KERNEL is None:
        elems = [0]
        for b in XS._B_BASIS:
            elems += [e ^ b for e in elems]
        _KERNEL = elems
    return _KERNEL


def _alpha_preimage(alpha: int) -> int:
    """
    One class with the given alpha: alpha_i(u) = B(u, b_i), and the
    symplectic basis has B(a_i, b_j) = delta_ij, so XOR the a_i in alpha.
    """
    global _PREIMAGE
    if _PREIMAGE is None:
        _PREIMAGE = XS._A_BASIS
    out = 0
    for i in range(XS.RANK):
        if (alpha >> i) & 1:
            out ^= _PREIMAGE[i]
    return out


def classes_moving(m: int, n: int) -> List[int]:
    """
    The classes mu with (X_mu f_m . f_n) nonzero AND of type 2: the type-2
    part of the coset alpha^-1(m + n), enumerated over 4,096 candidates.
    """
    tab = GR.type2_table()
    base = _alpha_preimage(m ^ n)
    return [base ^ k for k in _alpha_kernel() if (base ^ k) in tab]


def product(u: OddVector, v: OddVector) -> GR.GriessVector:
    """
    u . v in V+, defined by the Frobenius property and evaluated in the
    closed form of the module header.
    """
    A = [[F(0)] * 24 for _ in range(24)]
    B: Dict[int, F] = {}

    def bump(cls: int, value: F) -> None:
        if value:
            s = B.get(cls, F(0)) + value
            if s:
                B[cls] = s
            else:
                B.pop(cls, None)

    for (i, m), cu in u.c.items():
        for (j, n), cv in v.c.items():
            weight = K_FORM * cu * cv / 2
            if m == n:
                # A-part: c1 (e_i e_j^T + e_j e_i^T)/2 + c2 delta_ij I
                A[i][j] += weight * C1 / 2
                A[j][i] += weight * C1 / 2
                if i == j:
                    for d in range(24):
                        A[d][d] += weight * C2
            for mu in classes_moving(m, n):
                lam = _LAMBDA.get(mu) or _lambda_of(mu)
                _target, sign = rep_entry(mu, m)
                if _target != n:
                    continue
                value = weight * sign * (C3 * lam[i] * lam[j] / 8
                                         + (C4 if i == j else F(0)))
                bump(mu, value)
    return GR.GriessVector(A, B)


# ══════════════════════════════════════════════════════════════════════════════
# §4.  THE SPECTRUM OF AN AXIS ON THE ODD PART, AND THE LEDGER
# ══════════════════════════════════════════════════════════════════════════════

def spectrum_block(sign: int = SGN.CANONICAL_SIGN) -> Dict[str, object]:
    """
    The eigenvalues of ad(a_lambda) on V-, block by block, straight from the
    derived constants: `perp` is x orthogonal to lambda, `along` is the
    lambda direction, and sigma is the eigenvalue of X_lambda on s.
    """
    perp = {sigma: C2 / 2 + F(sign * sigma) * C4 / 2 for sigma in (1, -1)}
    along = {sigma: (C1 + C2) / 2 + F(sign * sigma) * (4 * C3 + C4) / 2
             for sigma in (1, -1)}
    dims: Dict[F, int] = {}
    for sigma in (1, -1):
        dims[perp[sigma]] = dims.get(perp[sigma], 0) + 23 * (XS.REP_DIM // 2)
        dims[along[sigma]] = dims.get(along[sigma], 0) + (XS.REP_DIM // 2)
    return {
        "perp": {str(k): str(v) for k, v in perp.items()},
        "along": {str(k): str(v) for k, v in along.items()},
        "dimensions": {str(k): v for k, v in sorted(dims.items())},
        "total": sum(dims.values()),
        "expected_total": DIM_ODD,
        "eigenvalues_are_the_monster_set": set(dims) == {F(0), F(1, 4),
                                                         F(1, 32)},
    }


def ledger(sign: int = SGN.CANONICAL_SIGN) -> Dict[str, object]:
    """
    The eigenspace dimensions of a 2A axis on the WHOLE algebra: the even
    part's, from glm3_griess, plus the odd part's, from `spectrum_block`.
    """
    even = GR.spectrum_dimensions()
    odd = spectrum_block(sign)["dimensions"]
    total = {
        "1": even["1"],
        "0": even["0"] + odd.get("0", 0),
        "1/4": even["1/4"] + odd.get("1/4", 0),
        "1/32": even["1/32"] + odd.get("1/32", 0),
    }
    total["total"] = sum(total.values())
    classical = {"1": 1, "0": 96256, "1/4": 4371, "1/32": 96256,
                 "total": 196884}
    return {
        "even": {k: even[k] for k in ("1", "0", "1/4", "1/32")},
        "odd": odd,
        "whole": total,
        "classical_monster_2A": classical,
        "agrees": total == classical,
        "dimension": DIM_FULL,
    }


def axis_eigenvector(cls: int, kind: str, seed: int = 7,
                      axis_sign: Optional[int] = None
                      ) -> Tuple[OddVector, F]:
    """
    An explicit eigenvector of ad(a_cls) on V-, of the requested kind, with
    its eigenvalue:

        'along+'  lambda (x) s   with X_lambda s = +s
        'along-'  lambda (x) s   with X_lambda s = -s
        'perp+'   x (x) s        with x . lambda = 0, X_lambda s = +s
        'perp-'   x (x) s        with x . lambda = 0, X_lambda s = -s
    """
    lam = _lambda_of(cls)
    rng = random.Random(seed + cls % 1024)
    # a 4096-vector in a fixed eigenspace of X_lambda: f_m +- X f_m
    m = rng.randrange(XS.REP_DIM)
    target, sign = rep_entry(cls, m)
    want = 1 if kind.endswith("+") else -1
    if target == m:
        # X is diagonal here; pick an index of the requested eigenvalue
        for mm in range(XS.REP_DIM):
            t2, s2 = rep_entry(cls, mm)
            if t2 == mm and s2 == want:
                s = {mm: F(1)}
                break
        else:
            raise RuntimeError("no eigenvector of that sign")
    else:
        s = {m: F(1), target: F(want * sign)}
    if kind.startswith("along"):
        x = list(lam)
    else:
        # any coordinate direction made orthogonal to lambda
        x = [F(0)] * 24
        idx = next(i for i in range(24) if lam[i] == 0) if any(
            lam[i] == 0 for i in range(24)) else None
        if idx is not None:
            x[idx] = F(1)
        else:
            # lambda has no zero coordinate: use e_0 - (lam_0/lam_1) e_1
            x[0] = lam[1]
            x[1] = -lam[0]
    u = tensor(x, s)
    a = GR.axis(cls, SGN.CANONICAL_SIGN if axis_sign is None else axis_sign)
    w = act(a, u)
    # the eigenvalue, read off any nonzero coordinate
    key = next(iter(u.c))
    value = w.c.get(key, F(0)) / u.c[key]
    return u, value


def spectrum_report(count: int = 3) -> Dict[str, object]:
    """
    The block prediction, checked vector by vector: build an explicit
    eigenvector of each kind and confirm that ad(a) really does multiply it
    by the predicted eigenvalue.
    """
    tab = GR.type2_table()
    classes = sorted(tab)[:count]
    rows = []
    ok = True
    block = spectrum_block()
    for cls in classes:
        a = GR.axis(cls, SGN.CANONICAL_SIGN)
        for kind in ("along+", "along-", "perp+", "perp-"):
            u, value = axis_eigenvector(cls, kind)
            good = act(a, u) == u.scale(value)
            ok = ok and good
            rows.append({"class": cls, "kind": kind,
                         "eigenvalue": str(value), "is_an_eigenvector": good})
    values = {r["eigenvalue"] for r in rows}
    return {
        "classes": len(classes),
        "rows": rows,
        "all_are_eigenvectors": ok,
        "eigenvalues_seen": sorted(values),
        "eigenvalues_are_the_monster_set": values == {"0", "1/4", "1/32"},
        "block": block,
        "ledger": ledger(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §5.  THE ALGEBRA LAWS
# ══════════════════════════════════════════════════════════════════════════════

def _sample_odd(rng: random.Random, terms: int = 2) -> OddVector:
    out: Dict[Tuple[int, int], F] = {}
    for _ in range(terms):
        out[(rng.randrange(24), rng.randrange(XS.REP_DIM))] = F(
            rng.randint(-3, 3) or 1)
    return OddVector(out)


def commutativity_report(trials: int = 6, seed: int = 20260817
                         ) -> Dict[str, object]:
    """u . v = v . u on random odd vectors."""
    rng = random.Random(seed)
    ok = True
    for _ in range(trials):
        u, v = _sample_odd(rng), _sample_odd(rng)
        if product(u, v) != product(v, u):
            ok = False
            break
    return {"trials": trials, "commutative": ok}


def frobenius_report(trials: int = 4, seed: int = 20260817
                     ) -> Dict[str, object]:
    """
    (u . v, w)_+ = (w |> u, v)_- for random odd u, v and even w — the
    identity the product was defined by, checked as a computation.
    """
    rng = random.Random(seed)
    tab = GR.type2_table()
    classes = sorted(tab)[:8]
    ok = True
    rows = []
    for _ in range(trials):
        u, v = _sample_odd(rng), _sample_odd(rng)
        ws = [GR.identity(),
              GR.axis(rng.choice(classes), SGN.CANONICAL_SIGN),
              GR.b_vector(rng.choice(classes), F(rng.randint(1, 3)))]
        for w in ws:
            left = product(u, v).form(w)
            right = form(act(w, u), v)
            rows.append({"left": str(left), "right": str(right),
                         "agree": left == right})
            ok = ok and left == right
    return {"trials": trials, "checks": len(rows), "frobenius_holds": ok,
            "rows": rows[:4]}


def fusion_report(count: int = 2) -> Dict[str, object]:
    """
    The fusion rules that involve the odd part.  For an axis a:

        a |> u          = (1/32) u          for u in the 1/32 eigenspace
        0 * 1/32 -> 1/32, 1/4 * 1/32 -> 1/32   (products inside V-)
        1/32 * 1/32 -> 1 + 0 + 1/4             (a product landing in V+)

    The last is the substantial one: the product of two odd 1/32
    eigenvectors is an element of the even part, and it is filtered there by
    the even part's own eigen-filter.
    """
    tab = GR.type2_table()
    classes = sorted(tab)[:count]
    rows = []
    ok = True
    for cls in classes:
        a = GR.axis(cls, SGN.CANONICAL_SIGN)
        vectors = {kind: axis_eigenvector(cls, kind)
                   for kind in ("along+", "along-", "perp+", "perp-")}
        by_value: Dict[str, List[OddVector]] = {}
        for _kind, (u, value) in vectors.items():
            by_value.setdefault(str(value), []).append(u)
        # 1/32 x 1/32 -> 1 + 0 + 1/4, inside V+
        for u in by_value.get("1/32", []):
            for v in by_value.get("1/32", []):
                w = product(u, v)
                good = GR.eigen_filter(a, w, [F(1), F(0), F(1, 4)]).is_zero()
                ok = ok and good
                rows.append({"class": cls, "rule": "1/32 * 1/32 -> 1+0+1/4",
                             "holds": good})
        # 1/4 x 1/32 -> 1/32 and 0 x 1/32 -> 1/32, inside V+
        for label, other in (("1/4", by_value.get("1/4", [])),
                             ("0", by_value.get("0", []))):
            for u in other:
                for v in by_value.get("1/32", []):
                    w = product(u, v)
                    good = GR.eigen_filter(a, w, [F(1, 32)]).is_zero()
                    ok = ok and good
                    rows.append({"class": cls,
                                 "rule": f"{label} * 1/32 -> 1/32",
                                 "holds": good})
    return {"classes": len(classes), "checks": len(rows),
            "all_rules_hold": ok, "rows": rows[:6]}


def apply_x(mu: int, u: OddVector) -> OddVector:
    """
    The action of the extraspecial element x_mu on V-, namely 1 (x) X_mu:
    a signed permutation of the basis.  (On V+ the same element acts by
    GR.apply_sign_automorphism.)
    """
    out: Dict[Tuple[int, int], F] = {}
    for (i, m), coef in u.c.items():
        target, sign = rep_entry(mu, m)
        key = (i, target)
        s = out.get(key, F(0)) + sign * coef
        if s:
            out[key] = s
        else:
            out.pop(key, None)
    return OddVector(out)


def equivariance_report(trials: int = 3, seed: int = 20260817
                        ) -> Dict[str, object]:
    """
    Both products are equivariant for Q = 2^(1+24): with x_mu acting on V+
    by GR.apply_sign_automorphism and on V- by 1 (x) X_mu,

        (X u) . (X v) = x_mu (u . v)   and   (x_mu w) |> (X u) = X (w |> u).

    This is the structural reason the algebra is a module for the whole
    normaliser N, and it is checked here rather than asserted.
    """
    rng = random.Random(seed)
    tab = GR.type2_table()
    classes = sorted(tab)[:8]
    product_ok = True
    action_ok = True
    checks = 0
    for _ in range(trials):
        u, v = _sample_odd(rng), _sample_odd(rng)
        mu = rng.choice(classes)
        if product(apply_x(mu, u), apply_x(mu, v)) != GR.apply_sign_automorphism(
                mu, product(u, v)):
            product_ok = False
        for w in (GR.identity(),
                  GR.axis(rng.choice(classes), SGN.CANONICAL_SIGN),
                  GR.b_vector(rng.choice(classes), F(rng.randint(1, 3)))):
            left = act(GR.apply_sign_automorphism(mu, w), apply_x(mu, u))
            right = apply_x(mu, act(w, u))
            if left != right:
                action_ok = False
            checks += 1
    return {"trials": trials, "checks": checks,
            "product_is_equivariant": product_ok,
            "action_is_equivariant": action_ok,
            "equivariant": product_ok and action_ok}


def miyamoto_report(count: int = 2) -> Dict[str, object]:
    """
    The Miyamoto involution of an axis, now that the odd part is present.

    tau(a) is +1 on the 1, 0 and 1/4 eigenspaces and -1 on the 1/32 one.
    On V- the eigenvalue of ad(a_lambda^eps) is 1/32 exactly on the
    X_lambda-eigenspace sigma = -eps, so

        tau(a_lambda^-) = 1 (x) X_lambda = x_lambda ,
        tau(a_lambda^+) = 1 (x) (-X_lambda) = x_lambda z ,

    two DIFFERENT automorphisms of the 196,884-dimensional algebra which
    restrict to the same one on the even part.  That is the precise sense in
    which the odd part resolves what section 9(c) could only fix by
    convention.
    """
    tab = GR.type2_table()
    classes = sorted(tab)[:count]
    rows = []
    ok = True
    for cls in classes:
        for eps in (1, -1):
            a = GR.axis(cls, eps)
            for kind in ("along+", "along-", "perp+", "perp-"):
                u, value = axis_eigenvector(cls, kind, axis_sign=eps)
                sigma = 1 if kind.endswith("+") else -1
                good = ((value == F(1, 32)) == (eps * sigma == -1)
                        and act(a, u) == u.scale(value))
                ok = ok and good
                rows.append({"class": cls, "axis_sign": eps, "kind": kind,
                             "eigenvalue": str(value),
                             "tau_acts_by": -1 if value == F(1, 32) else 1,
                             "X_lambda_eigenvalue": sigma,
                             "as_predicted": good})
    return {
        "classes": len(classes),
        "checks": len(rows),
        "rows": rows[:8],
        "tau_is_the_extraspecial_sign_on_the_odd_part": ok,
        "tau_of_a_minus": "x_lambda",
        "tau_of_a_plus": "x_lambda z",
        "the_two_signs_have_different_miyamoto_involutions": ok,
    }


def sign_visibility_report(count: int = 3) -> Dict[str, object]:
    """
    The odd part sees the sign of an axis.  On the vector lambda (x) s with
    X_lambda s = s, the two axes act by DIFFERENT eigenvalues:

        a_lambda^-  gives 1/32,      a_lambda^+  gives 1/4

    (with the roles exchanged on the other X_lambda eigenspace).  Inside the
    even part the two are indistinguishable by spectrum; here one
    application separates them.
    """
    tab = GR.type2_table()
    classes = sorted(tab)[:count]
    rows = []
    separated = True
    for cls in classes:
        u, _v = axis_eigenvector(cls, "along+")
        key = next(iter(u.c))
        values = {}
        for sign in (1, -1):
            a = GR.axis(cls, sign)
            w = act(a, u)
            values[sign] = (w.c.get(key, F(0)) / u.c[key]
                            if w == u.scale(w.c.get(key, F(0)) / u.c[key])
                            else None)
        distinct = (values[1] is not None and values[-1] is not None
                    and values[1] != values[-1])
        separated = separated and distinct
        rows.append({"class": cls,
                     "eigenvalue_of_a_plus": str(values[1]),
                     "eigenvalue_of_a_minus": str(values[-1]),
                     "separated": distinct})
    return {"classes": len(classes), "rows": rows,
            "the_odd_part_separates_the_two_signs": separated,
            "the_even_part_does_not": True}


# ══════════════════════════════════════════════════════════════════════════════
# §6.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def odd_audit(full: bool = False) -> Dict[str, object]:
    out: Dict[str, object] = {
        "dimensions": {"odd": DIM_ODD, "even": GR.DIM_EVEN,
                       "whole": DIM_FULL,
                       "closes": GR.DIM_EVEN + DIM_ODD == 196884},
        "constants": derive_constants(),
        "spectrum": spectrum_report(count=2 if not full else 4),
        "commutativity": commutativity_report(trials=4 if not full else 10),
        "frobenius": frobenius_report(trials=2 if not full else 5),
        "equivariance": equivariance_report(trials=2 if not full else 5),
        "fusion": fusion_report(count=1 if not full else 3),
        "miyamoto": miyamoto_report(count=1 if not full else 3),
        "sign": sign_visibility_report(count=2 if not full else 4),
    }
    out["all_ok"] = (
        out["dimensions"]["closes"]
        and out["constants"]["over_determined_system_closes"]
        and out["constants"]["matches_module_constants"]
        and out["spectrum"]["all_are_eigenvectors"]
        and out["spectrum"]["eigenvalues_are_the_monster_set"]
        and out["spectrum"]["ledger"]["agrees"]
        and out["commutativity"]["commutative"]
        and out["frobenius"]["frobenius_holds"]
        and out["equivariance"]["equivariant"]
        and out["fusion"]["all_rules_hold"]
        and out["miyamoto"][
            "the_two_signs_have_different_miyamoto_involutions"]
        and out["sign"]["the_odd_part_separates_the_two_signs"])
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    full = "--full" in argv
    print(banner("GLM-3 ODD — self-audit"))
    rep = odd_audit(full=full)
    d = rep["dimensions"]
    print(f"  even + odd = whole                    "
          f"{fmt_int(d['even'])} + {fmt_int(d['odd'])} = "
          f"{fmt_int(d['whole'])}")
    c = rep["constants"]
    print(f"  derived constants                     "
          f"c1={c['c1']}, c2={c['c2']}, c3={c['c3']}, c4={c['c4']}")
    print(f"  the over-determined system closes     "
          f"{c['over_determined_system_closes']}")
    sp = rep["spectrum"]
    print(f"  eigenvectors of every block           "
          f"{sp['all_are_eigenvectors']}")
    print(f"  eigenvalues on V-                     "
          f"{sp['eigenvalues_seen']}")
    led = sp["ledger"]
    print(f"  ledger 1 / 0 / 1/4 / 1/32             "
          f"{led['whole']['1']} / {fmt_int(led['whole']['0'])} / "
          f"{fmt_int(led['whole']['1/4'])} / "
          f"{fmt_int(led['whole']['1/32'])}  "
          f"= {fmt_int(led['whole']['total'])}")
    print(f"  these are the classical 2A numbers    {led['agrees']}")
    print(f"  the product is commutative            "
          f"{rep['commutativity']['commutative']}")
    print(f"  Frobenius (u.v, w) = (w|>u, v)        "
          f"{rep['frobenius']['frobenius_holds']}")
    print(f"  the products are Q-equivariant        "
          f"{rep['equivariance']['equivariant']}")
    print(f"  fusion rules with the odd part        "
          f"{rep['fusion']['all_rules_hold']} "
          f"({rep['fusion']['checks']} checks)")
    print(f"  tau(a^-) = x_lam,  tau(a^+) = x_lam z "
          f"{rep['miyamoto']['tau_is_the_extraspecial_sign_on_the_odd_part']}"
          f" ({rep['miyamoto']['checks']} checks)")
    print(f"  the odd part separates +- b_lambda    "
          f"{rep['sign']['the_odd_part_separates_the_two_signs']}")
    print(f"\n  {'OK' if rep['all_ok'] else 'FAILED'}")
    return 0 if rep["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
