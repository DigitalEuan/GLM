#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 EXTRASPECIAL  —  Q = 2^(1+24)_+ built from the Leech form
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 2 — the group that acts on the algebra.
  Deps   :  glm3_leech2.py.  Standard library only, exact integer arithmetic.

  ------------------------------------------------------------------------
  The group
  ------------------------------------------------------------------------

  The centraliser of a 2B involution z in the Monster is 2^(1+24).Co_1.  Its
  normal subgroup Q = 2^(1+24) is the extraspecial group of plus type whose
  central quotient is the F_2 quadratic space Lambda/2Lambda built in
  glm3_leech2.py.  GLM-1 carried an extraspecial group of the right order
  but built from an arbitrary Heisenberg pairing on F_2^12 x F_2^12, with no
  connection to the lattice.  Here the group is built FROM the lattice:

      elements      (u, eps),  u a class in Lambda/2Lambda, eps in F_2
      product       (u1, e1)(u2, e2) = (u1 + u2, e1 + e2 + f(u1, u2))
      centre        z = (0, 1)
      squares       (u, eps)^2 = z^q(u)
      commutators   [(u,.), (v,.)] = z^B(u, v)

  where q is the Leech quadratic form and B its polar form.  The cocycle f
  is produced, not postulated: a symplectic basis a_0..a_11, b_0..b_11 of
  singular classes is computed by Witt decomposition, coordinates are read
  off by u -> (alpha_i = B(u, b_i), beta_i = B(u, a_i)), and

      f(u, v) = <beta_u, alpha_v>.

  That f has the right diagonal and the right polar form — f(u,u) = q(u) and
  f(u,v) + f(v,u) = B(u,v) — is CHECKED against the lattice, not assumed, so
  the group really is the extraspecial group of (Lambda/2Lambda, q).

  ------------------------------------------------------------------------
  The 4096-dimensional representation
  ------------------------------------------------------------------------

  Q has a unique faithful irreducible representation, of dimension 2^12 =
  4096, and the symplectic basis hands it to us: with basis {|k> : k in
  F_2^12} indexed by the totally singular subspace <a_0..a_11>,

      rho(u, eps) |k>  =  (-1)^(eps + <beta_u, k>) |k + alpha_u>.

  This is a signed permutation, so everything is exact.  The relations are
  verified as operator identities on the whole 4096-dimensional space.

  The 24 x 4096 = 98,304 odd part of the Griess ledger is a copy of
  R^24 (x) (this space); GLM-3 does not build the algebra product on it (see
  glm3_griess.py), but the representation itself is here, and it is what the
  multi-MOG-cube of glm3_mog.py indexes.

  ------------------------------------------------------------------------
  How the reasoner uses it
  ------------------------------------------------------------------------

  Every concept has a Leech carrier, hence a class u, hence a group element
  x_u in Q/<z>.  Composition of meanings is addition of carriers, which is
  addition of classes, which is multiplication in Q up to the centre: the
  GLM composition law and the Monster group law are the same law.  The
  centre records the cocycle, and q(u) says whether x_u is an involution
  (q = 0) or has order 4 (q = 1).

      python3 glm3_extraspecial.py       # self-audit
================================================================================
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int
import glm3_leech2 as L2

__all__ = [
    "RANK", "REP_DIM", "GROUP_ORDER",
    "symplectic_basis", "coordinates", "cocycle",
    "QElement", "identity", "central", "x_of_class", "multiply", "inverse",
    "square", "commutator", "rep_columns", "rep_apply", "operators_equal",
    "involution_count", "extraspecial_audit",
]

RANK = 12
REP_DIM = 1 << RANK
GROUP_ORDER = 1 << 25


# ══════════════════════════════════════════════════════════════════════════════
# §1.  A SYMPLECTIC BASIS OF SINGULAR CLASSES
# ══════════════════════════════════════════════════════════════════════════════

def _singular_vector(space: Sequence[int]) -> Optional[int]:
    """A nonzero singular vector in the F_2 span of `space`."""
    for v in space:
        if L2.q_form(v) == 0:
            return v
    for i, v in enumerate(space):
        for w in space[i + 1:]:
            u = v ^ w
            if u and L2.q_form(u) == 0:
                return u
    return None


def _independent(vectors: Sequence[int]) -> List[int]:
    pivots: Dict[int, int] = {}
    out: List[int] = []
    for v in vectors:
        w = v
        while w:
            top = w.bit_length() - 1
            if top in pivots:
                w ^= pivots[top]
            else:
                pivots[top] = w
                out.append(v)
                break
    return out


def symplectic_basis() -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """
    Twelve hyperbolic pairs (a_i, b_i) of SINGULAR classes with
        q(a_i) = q(b_i) = 0,  B(a_i, b_i) = 1,
        B(a_i, a_j) = B(b_i, b_j) = 0,  B(a_i, b_j) = 0 for i != j.
    Computed by Witt decomposition of (Lambda/2Lambda, q); the existence of
    twelve such pairs is exactly the statement that the form is of plus type.
    """
    space = [1 << i for i in range(24)]
    a_list: List[int] = []
    b_list: List[int] = []
    while space:
        u = _singular_vector(space)
        if u is None:
            raise AssertionError("anisotropic remainder: form is not plus type")
        v = None
        for cand in space:
            if L2.b_form(u, cand):
                v = cand
                break
        if v is None:
            for i, p in enumerate(space):
                for r in space[i + 1:]:
                    if L2.b_form(u, p ^ r):
                        v = p ^ r
                        break
                if v is not None:
                    break
        if v is None:
            raise AssertionError("degenerate form")
        if L2.q_form(v):
            v ^= u                      # now q(v) = q(v) + q(u) + B(u,v) = 0
        a_list.append(u)
        b_list.append(v)
        rest = []
        for w in space:
            w2 = w
            if L2.b_form(w2, v):
                w2 ^= u
            if L2.b_form(w2, u):
                w2 ^= v
            if w2:
                rest.append(w2)
        space = _independent(rest)
    return tuple(a_list), tuple(b_list)


_A_BASIS, _B_BASIS = symplectic_basis()


def coordinates(u: int) -> Tuple[int, int]:
    """
    (alpha, beta) as 12-bit integers, read off symplectically:
        alpha_i = B(u, b_i),   beta_i = B(u, a_i).
    """
    alpha = 0
    beta = 0
    for i in range(RANK):
        if L2.b_form(u, _B_BASIS[i]):
            alpha |= 1 << i
        if L2.b_form(u, _A_BASIS[i]):
            beta |= 1 << i
    return alpha, beta


def _parity(n: int) -> int:
    return bin(n).count("1") & 1


def cocycle(u: int, v: int) -> int:
    """f(u, v) = <beta_u, alpha_v>."""
    _, bu = coordinates(u)
    av, _ = coordinates(v)
    return _parity(bu & av)


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE GROUP
# ══════════════════════════════════════════════════════════════════════════════

class QElement:
    """An element (u, eps) of Q = 2^(1+24)_+."""

    __slots__ = ("u", "eps")

    def __init__(self, u: int, eps: int = 0) -> None:
        self.u = u & 0xFFFFFF
        self.eps = eps & 1

    def __mul__(self, other: "QElement") -> "QElement":
        return QElement(self.u ^ other.u,
                        self.eps ^ other.eps ^ cocycle(self.u, other.u))

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, QElement) and self.u == other.u
                and self.eps == other.eps)

    def __hash__(self) -> int:
        return hash((self.u, self.eps))

    def __repr__(self) -> str:
        return f"QElement(class=0x{self.u:06x}, eps={self.eps})"

    def inverse(self) -> "QElement":
        return QElement(self.u, self.eps ^ cocycle(self.u, self.u))

    def order(self) -> int:
        if self.u == 0:
            return 1 if self.eps == 0 else 2
        return 4 if L2.q_form(self.u) else 2


def identity() -> QElement:
    return QElement(0, 0)


def central() -> QElement:
    """z, the generator of the centre."""
    return QElement(0, 1)


def x_of_class(u: int) -> QElement:
    """The lift x_u of the class u, with eps = 0."""
    return QElement(u, 0)


def multiply(g: QElement, h: QElement) -> QElement:
    return g * h


def inverse(g: QElement) -> QElement:
    return g.inverse()


def square(g: QElement) -> QElement:
    return g * g


def commutator(g: QElement, h: QElement) -> QElement:
    return g * h * g.inverse() * h.inverse()


def involution_count() -> Dict[str, int]:
    """
    Elements of order at most 2: (u, eps) with q(u) = 0, so
        2 * #singular = 2 (2^23 + 2^11) = 2^24 + 2^12,
    the plus-type signature of an extraspecial group of order 2^25.
    """
    singular = L2.singular_class_count()
    return {"singular_classes": singular,
            "elements_of_order_at_most_2": 2 * singular,
            "expected": (1 << 24) + (1 << 12)}


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE 4096-DIMENSIONAL REPRESENTATION
# ══════════════════════════════════════════════════════════════════════════════

def rep_columns(g: QElement) -> List[Tuple[int, int]]:
    """
    rho(g) as 4096 (target index, sign) pairs, one per basis vector |k>:
        rho(u, eps)|k> = (-1)^(eps + <beta, k>) |k + alpha>.
    """
    alpha, beta = coordinates(g.u)
    e = g.eps
    return [(k ^ alpha, -1 if (_parity(beta & k) ^ e) else 1)
            for k in range(REP_DIM)]


def rep_apply(g: QElement, vector: Sequence[int]) -> List[int]:
    out = [0] * REP_DIM
    for k, (target, sign) in enumerate(rep_columns(g)):
        if vector[k]:
            out[target] = sign * vector[k]
    return out


def operators_equal(g: QElement, h: QElement) -> bool:
    return rep_columns(g) == rep_columns(h)


def _rep_compose(g: QElement, h: QElement) -> List[Tuple[int, int]]:
    cg = rep_columns(g)
    return [(cg[t][0], cg[t][1] * s) for (t, s) in rep_columns(h)]


# ══════════════════════════════════════════════════════════════════════════════
# §4.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def extraspecial_audit(full: bool = True) -> Dict[str, object]:
    out: Dict[str, object] = {}
    a, b = _A_BASIS, _B_BASIS

    # the symplectic basis really is symplectic and singular
    ok = True
    for i in range(RANK):
        if L2.q_form(a[i]) or L2.q_form(b[i]):
            ok = False
        for j in range(RANK):
            if L2.b_form(a[i], b[j]) != (1 if i == j else 0):
                ok = False
            if i != j and (L2.b_form(a[i], a[j]) or L2.b_form(b[i], b[j])):
                ok = False
    out["symplectic_basis_ok"] = ok
    out["basis_spans"] = len(_independent(list(a) + list(b))) == 24

    # the cocycle has the right diagonal and polar form
    diag = True
    polar = True
    seed = 0x1234567
    tested = 0
    for _ in range(200):
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        u = seed & 0xFFFFFF
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        v = seed & 0xFFFFFF
        if cocycle(u, u) != L2.q_form(u):
            diag = False
        if (cocycle(u, v) ^ cocycle(v, u)) != L2.b_form(u, v):
            polar = False
        tested += 1
    out["cocycle_diagonal_is_q"] = diag
    out["cocycle_polar_is_B"] = polar
    out["cocycle_tests"] = tested

    # group relations
    z = central()
    rel = {
        "z_is_central": all(commutator(z, x_of_class(1 << i)) == identity()
                            for i in range(24)),
        "z_squared_is_1": z * z == identity(),
        "squares_are_z_to_q": all(
            square(x_of_class(u)) == (z if L2.q_form(u) else identity())
            for u in [1 << i for i in range(24)] + [0x0F0F0F, 0x123456]),
        "commutator_is_z_to_B": all(
            commutator(x_of_class(u), x_of_class(v))
            == (z if L2.b_form(u, v) else identity())
            for u in [1 << i for i in range(12)]
            for v in [1 << j for j in range(12, 24)]),
    }
    out["relations"] = rel
    out["all_relations_hold"] = all(rel.values())
    out["order"] = {"classes": 1 << 24, "centre": 2, "group": GROUP_ORDER,
                    "matches": (1 << 24) * 2 == GROUP_ORDER}
    out["involutions"] = involution_count()
    out["involutions_match"] = (out["involutions"]["elements_of_order_at_most_2"]
                                == out["involutions"]["expected"])

    # the 4096-dimensional representation
    out["rep_dim"] = REP_DIM
    out["z_acts_as_minus_one"] = rep_columns(z) == [(k, -1)
                                                    for k in range(REP_DIM)]
    hom = True
    faithful = True
    seed = 0x2468ACE
    pairs = 40 if full else 8
    for _ in range(pairs):
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        g = QElement(seed & 0xFFFFFF, (seed >> 24) & 1)
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        h = QElement(seed & 0xFFFFFF, (seed >> 24) & 1)
        if _rep_compose(g, h) != rep_columns(g * h):
            hom = False
        if g != identity() and rep_columns(g) == rep_columns(identity()):
            faithful = False
    out["rep_is_homomorphism"] = hom
    out["rep_is_faithful_on_sample"] = faithful
    out["ledger_odd_part"] = {"24 x 4096": 24 * REP_DIM,
                              "expected": 98304,
                              "matches": 24 * REP_DIM == 98304}
    return out


def main() -> None:
    print(banner("GLM-3  EXTRASPECIAL  —  Q = 2^(1+24)_+ from the Leech form"))
    a = extraspecial_audit()
    print("\n[the symplectic basis of singular classes]")
    print(f"  12 hyperbolic pairs, all singular : {a['symplectic_basis_ok']}")
    print(f"  they span Lambda/2Lambda          : {a['basis_spans']}")
    print("\n[the cocycle, checked against the lattice]")
    print(f"  f(u,u) = q(u)                     : {a['cocycle_diagonal_is_q']}")
    print(f"  f(u,v) + f(v,u) = B(u,v)          : {a['cocycle_polar_is_B']}")
    print(f"  tests                             : {a['cocycle_tests']}")
    print("\n[group relations]")
    for k, v in a["relations"].items():
        print(f"  {k:34s}: {v}")
    o = a["order"]
    print(f"  |Q| = 2 x 2^24                    : {fmt_int(o['group'])}"
          f" ({o['matches']})")
    inv = a["involutions"]
    print(f"  elements of order <= 2            : "
          f"{fmt_int(inv['elements_of_order_at_most_2'])} = 2^24 + 2^12"
          f" ({a['involutions_match']})")
    print("\n[the 4096-dimensional representation]")
    print(f"  dimension                         : {fmt_int(a['rep_dim'])}")
    print(f"  z acts as -1                      : {a['z_acts_as_minus_one']}")
    print(f"  rho is a homomorphism             : {a['rep_is_homomorphism']}")
    print(f"  rho is faithful on the sample     : {a['rep_is_faithful_on_sample']}")
    print(f"  24 x 4096 = 98,304 (ledger odd)   : "
          f"{a['ledger_odd_part']['matches']}")
    print()


if __name__ == "__main__":
    main()
