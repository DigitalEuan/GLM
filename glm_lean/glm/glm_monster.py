#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM UPPER TIERS  —  M24, the extraspecial group 2^(1+24), and a snap algebra
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  Tier 4 — optional.  Nothing in the codec, the metrology or the
            reasoner depends on this module.
  Deps   :  glm_substrate.py, standard library only.

  Status of the three sections, stated plainly:

    §1  M24 / MOG column symmetries      VERIFIED as a membership test:
        we exhibit and check coordinate permutations that preserve the Golay
        code.  The group itself is built in `glm_m24.py`, where a stabiliser
        chain shows the automorphism group has order 244,823,040 and an
        exhaustive stabiliser enumeration shows it is all of Aut(C) = M24.

    §2  The extraspecial group 2^(1+24)  VERIFIED EXACTLY:
        implemented as signed permutations of the 4096 basis vectors of the
        Schrodinger representation.  All defining relations, including the
        commutator [x_i, y_i] = z that CANNOT hold in the 24-dimensional
        "sign flip and swap" action, are checked as operator identities with
        exact integer arithmetic.

    §3  SnapAlgebra                      CORRECTED RESULT:
        earlier GLM versions defined a "snap-based Griess product" out of the
        Golay decoder and described it as commutative and NON-associative.
        Section 3 works out what that product actually is.  It collapses to
            v . w = snap(v) XOR snap(w),
        which is commutative, ASSOCIATIVE, and idempotent-free (v . v = 0);
        and the "non-associative correction term" B satisfies B(B(v,w),u) = 0
        identically.  Both statements are proved in the docstrings and checked
        by execution.  So the object is a retraction onto (C, XOR), not a
        Griess-like algebra.

      python3 glm_monster.py         # runs the upper-tier audit
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from glm_substrate import GOLAY, BitOps

__all__ = [
    "golay_permutation_check", "column_symmetry_report",
    "ExtraspecialElement", "SchrodingerRep", "extraspecial_relation_report",
    "NormaliserElement", "PairPerm", "IDENTITY_PERM", "permute_bits",
    "perm_inverse", "perm_compose", "act_on_element", "normaliser_report",
    "SnapAlgebra", "snap_algebra_report", "monster_tier_audit",
]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  CODE AUTOMORPHISMS  (membership testing; the group is in glm_m24.py)
# ══════════════════════════════════════════════════════════════════════════════

def golay_permutation_check(perm: Sequence[int]) -> bool:
    """
    Does the coordinate permutation `perm` map the Golay code to itself?

    Checked exhaustively against all 4096 codewords: automorphism or not, with
    no sampling.  The automorphism group of the code is computed in
    `glm_m24.py` and comes out as M24 (order 244,823,040); this predicate is
    the elementary way to certify a single membership.
    """
    if sorted(perm) != list(range(24)):
        raise ValueError("golay_permutation_check: not a permutation of 0..23")
    words = GOLAY.codeword_ints()
    for cw in GOLAY.all_codewords():
        image = [0] * 24
        for i, p in enumerate(perm):
            image[p] = cw[i]
        if BitOps.to_int(image) not in words:
            return False
    return True


def _generator_permutations() -> Dict[str, List[int]]:
    """
    A small stock of candidate permutations, described by what they do to the
    24 coordinates.  Which ones are automorphisms is decided by execution, not
    by assertion.
    """
    ident = list(range(24))
    # swap the two halves (message block <-> parity block)
    halves = [(i + 12) % 24 for i in range(24)]
    # rotate the parity block by one
    rot_parity = list(range(12)) + [12 + ((i + 1) % 12) for i in range(12)]
    # transpose coordinates 1 and 2
    swap12 = list(range(24))
    swap12[1], swap12[2] = swap12[2], swap12[1]
    # reverse all 24 coordinates
    reverse = list(range(23, -1, -1))
    return {
        "identity": ident,
        "swap_halves": halves,
        "rotate_parity_block": rot_parity,
        "transpose_1_2": swap12,
        "reverse_all": reverse,
    }


def column_symmetry_report() -> Dict[str, bool]:
    """Which of the candidate permutations really preserve the Golay code."""
    return {name: golay_permutation_check(p)
            for name, p in _generator_permutations().items()}


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE EXTRASPECIAL GROUP 2^(1+24) AND ITS 4096-DIMENSIONAL REPRESENTATION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExtraspecialElement:
    """
    An element of the extraspecial 2-group of order 2^(1+24), written in
    Heisenberg coordinates (a, b, eps) with a, b in F_2^12 and eps in F_2:

        a   the "Z-type" part  (phase flips)
        b   the "X-type" part  (index translations)
        eps the central sign

    Multiplication is the Heisenberg cocycle

        (a1,b1,e1) * (a2,b2,e2) = (a1^a2, b1^b2, e1^e2^<a1,b2>)

    where <.,.> is the F_2 inner product.  The cocycle <a1,b2> is exactly the
    sign picked up when the Z-type part of the first factor meets the X-type
    translation of the second, so this convention is the one that makes the
    4096-dimensional action below a homomorphism (checked, not assumed).

    The generators are
        x_i = (e_i, 0, 0)    y_i = (0, e_i, 0)    z = (0, 0, 1),
    and the group has order 2^25 = 33,554,432.
    """

    a: int
    b: int
    eps: int

    def __mul__(self, other: "ExtraspecialElement") -> "ExtraspecialElement":
        cocycle = _parity(self.a & other.b)
        return ExtraspecialElement(self.a ^ other.a, self.b ^ other.b,
                                   self.eps ^ other.eps ^ cocycle)

    def inverse(self) -> "ExtraspecialElement":
        # every element squares into the centre; the inverse is g * (g^2)^-1
        sq = self * self
        return ExtraspecialElement(self.a, self.b, self.eps ^ sq.eps)

    def is_identity(self) -> bool:
        return self.a == 0 and self.b == 0 and self.eps == 0

    @staticmethod
    def x(i: int) -> "ExtraspecialElement":
        return ExtraspecialElement(1 << i, 0, 0)

    @staticmethod
    def y(i: int) -> "ExtraspecialElement":
        return ExtraspecialElement(0, 1 << i, 0)

    @staticmethod
    def z() -> "ExtraspecialElement":
        return ExtraspecialElement(0, 0, 1)

    @staticmethod
    def identity() -> "ExtraspecialElement":
        return ExtraspecialElement(0, 0, 0)


def _parity(n: int) -> int:
    return bin(n).count("1") & 1


class SchrodingerRep:
    """
    The faithful 4096-dimensional representation of 2^(1+24).

    A group element acts on the basis {|k> : k in F_2^12} of a 4096-dimensional
    space as a SIGNED PERMUTATION:

        rho(a, b, eps) |k>  =  (-1)^(<a,k> + eps) |k XOR b>

    which is stored compactly as (b, a, eps) and applied in O(4096) integer
    operations.  Nothing is approximated: the entries are +1 and -1 exactly.

    Why this matters: the 24-dimensional "sign flips and coordinate swaps"
    action used in early GLM versions cannot satisfy [x_i, y_i] = z, because
    those matrices commute.  In the 4096-dimensional representation the
    commutator really is the central element, and that is checked below on the
    whole space, not on a sample.
    """

    DIM = 4096

    @staticmethod
    def apply(g: ExtraspecialElement, vector: Sequence[int]) -> List[int]:
        out = [0] * SchrodingerRep.DIM
        for k, value in enumerate(vector):
            if value:
                sign = -1 if (_parity(g.a & k) ^ g.eps) else 1
                out[k ^ g.b] = sign * value
        return out

    @staticmethod
    def matrix_columns(g: ExtraspecialElement) -> List[Tuple[int, int]]:
        """
        The operator as 4096 (target index, sign) pairs — one per basis vector.
        Two group elements are represented by the same operator iff these lists
        agree, which is the test used for the relation checks.
        """
        return [(k ^ g.b, -1 if (_parity(g.a & k) ^ g.eps) else 1)
                for k in range(SchrodingerRep.DIM)]

    @staticmethod
    def operators_equal(g: ExtraspecialElement, h: ExtraspecialElement) -> bool:
        return SchrodingerRep.matrix_columns(g) == SchrodingerRep.matrix_columns(h)

    @staticmethod
    def is_identity_operator(g: ExtraspecialElement) -> bool:
        return SchrodingerRep.operators_equal(g, ExtraspecialElement.identity())


def _commutator(g: ExtraspecialElement, h: ExtraspecialElement) -> ExtraspecialElement:
    return g * h * g.inverse() * h.inverse()


# Signed permutation of R^24 stored as (perm, signs), acting by
#     (M v)[perm[j]] = signs[j] * v[j].
SignedPerm = Tuple[Tuple[int, ...], Tuple[int, ...]]


def _sp_compose(A: SignedPerm, B: SignedPerm) -> SignedPerm:
    """A after B."""
    permA, signA = A
    permB, signB = B
    perm = tuple(permA[permB[j]] for j in range(24))
    sign = tuple(signA[permB[j]] * signB[j] for j in range(24))
    return perm, sign


def _sp_inverse(A: SignedPerm) -> SignedPerm:
    perm, sign = A
    inv = [0] * 24
    isign = [1] * 24
    for j, p in enumerate(perm):
        inv[p] = j
        isign[p] = sign[j]
    return tuple(inv), tuple(isign)


def visual_24d_commutator_check(pairs: int = 12) -> bool:
    """
    Can the 24-dimensional "sign flip / axis swap" action realise the
    extraspecial relation [x_i, y_i] = z?

    x_i flips the sign of coordinate 2i, y_i swaps coordinates 2i and 2i+1,
    z = -Id.  The answer is computed here, not assumed: it is False, which is
    the reason the 4096-dimensional representation above is needed.
    """
    minus_id: SignedPerm = (tuple(range(24)), (-1,) * 24)
    for i in range(pairs):
        signs = [1] * 24
        signs[2 * i] = -1
        x: SignedPerm = (tuple(range(24)), tuple(signs))
        perm = list(range(24))
        perm[2 * i], perm[2 * i + 1] = perm[2 * i + 1], perm[2 * i]
        y: SignedPerm = (tuple(perm), (1,) * 24)
        comm = _sp_compose(_sp_compose(x, y),
                           _sp_compose(_sp_inverse(x), _sp_inverse(y)))
        if comm != minus_id:
            return False
    return True


def _compose_operators(g: ExtraspecialElement, h: ExtraspecialElement
                       ) -> List[Tuple[int, int]]:
    """The operator product rho(g) rho(h), as (target index, sign) pairs."""
    cols_h = SchrodingerRep.matrix_columns(h)
    cols_g = SchrodingerRep.matrix_columns(g)
    return [(cols_g[t][0], cols_g[t][1] * s) for (t, s) in cols_h]


def extraspecial_relation_report(pairs: int = 12) -> Dict[str, object]:
    """
    Check every defining relation of 2^(1+24), as operator identities on the
    full 4096-dimensional space.

    Relations checked, for all i, j in [0, pairs):
        x_i^2 = y_i^2 = z^2 = 1
        z is central
        [x_i, y_i] = z                      (the extraspecial relation)
        [x_i, x_j] = [y_i, y_j] = 1         (i != j)
        [x_i, y_j] = 1                      (i != j)
    Plus a faithfulness probe: no non-identity element of a deterministic
    sample acts as the identity operator.
    """
    ident = ExtraspecialElement.identity()
    z = ExtraspecialElement.z()
    results: Dict[str, object] = {}
    ok = True

    def check(name: str, value: bool) -> None:
        nonlocal ok
        results[name] = value
        ok = ok and value

    check("z_squared_is_identity", SchrodingerRep.operators_equal(z * z, ident))
    check("x_squared_is_identity", all(
        SchrodingerRep.operators_equal(ExtraspecialElement.x(i) * ExtraspecialElement.x(i), ident)
        for i in range(pairs)))
    check("y_squared_is_identity", all(
        SchrodingerRep.operators_equal(ExtraspecialElement.y(i) * ExtraspecialElement.y(i), ident)
        for i in range(pairs)))
    check("z_is_central", all(
        SchrodingerRep.operators_equal(_commutator(z, g), ident)
        for i in range(pairs)
        for g in (ExtraspecialElement.x(i), ExtraspecialElement.y(i))))
    check("commutator_x_y_is_z", all(
        SchrodingerRep.operators_equal(
            _commutator(ExtraspecialElement.x(i), ExtraspecialElement.y(i)), z)
        for i in range(pairs)))
    check("distinct_pairs_commute", all(
        SchrodingerRep.operators_equal(_commutator(g, h), ident)
        for i in range(pairs) for j in range(pairs) if i != j
        for g, h in ((ExtraspecialElement.x(i), ExtraspecialElement.x(j)),
                     (ExtraspecialElement.y(i), ExtraspecialElement.y(j)),
                     (ExtraspecialElement.x(i), ExtraspecialElement.y(j)))))
    check("z_is_not_the_identity_operator",
          not SchrodingerRep.is_identity_operator(z))

    # rho is a homomorphism: rho(g)rho(h) = rho(gh), checked on a spread of pairs
    state = 0x2468ACE
    homomorphic = True
    for _ in range(200):
        state = (1103515245 * state + 12345) & 0x1FFFFFF
        g = ExtraspecialElement(state & 0xFFF, (state >> 12) & 0xFFF, (state >> 24) & 1)
        state = (1103515245 * state + 12345) & 0x1FFFFFF
        h = ExtraspecialElement(state & 0xFFF, (state >> 12) & 0xFFF, (state >> 24) & 1)
        if _compose_operators(g, h) != SchrodingerRep.matrix_columns(g * h):
            homomorphic = False
            break
    check("representation_is_a_homomorphism", homomorphic)

    # faithfulness probe over a deterministic spread of elements
    state = 0x1234567
    faithful = True
    for _ in range(512):
        state = (1103515245 * state + 12345) & 0xFFFFFF
        g = ExtraspecialElement(state & 0xFFF, (state >> 12) & 0xFFF, state & 1)
        if not g.is_identity() and SchrodingerRep.is_identity_operator(g):
            faithful = False
            break
    check("faithful_on_sample", faithful)

    # the 24-dimensional "visual" action, for contrast -- measured, not assumed
    results["24d_action_realises_commutator"] = visual_24d_commutator_check(pairs)
    results["group_order"] = 2 ** 25
    results["representation_dimension"] = SchrodingerRep.DIM
    results["all_relations_hold"] = ok
    return results


# ══════════════════════════════════════════════════════════════════════════════
# §3.  SNAP ALGEBRA  (exploratory)
# ══════════════════════════════════════════════════════════════════════════════

class SnapAlgebra:
    """
    The algebra earlier GLM versions built out of the Golay decoder, and what
    it actually is.

    Definitions (as published in GLM v10 - v17):
        B(v, w) = snap(v XOR w) XOR snap(v) XOR snap(w) XOR snap(0)
        v . w   = snap(v XOR w) XOR B(v, w)

    Write snap(v) = v XOR L(sigma(v)), where sigma is the syndrome map and L
    the coset-leader table; note snap(0) = 0.  Then:

      (1)  B(v, w) = L(sigma(v) XOR sigma(w)) XOR L(sigma(v)) XOR L(sigma(w)).
           B depends only on the two syndromes, and sigma(B(v,w)) = 0, i.e.
           B(v, w) is ALWAYS a codeword.

      (2)  v . w = snap(v) XOR snap(w).
           Substituting (1) into the definition cancels the v XOR w term.

      (3)  The product is commutative and ASSOCIATIVE, with
           (v.w).u = snap(v) XOR snap(w) XOR snap(u) = v.(w.u),
           because a XOR of codewords is a codeword and snap fixes codewords.
           The zero word is a two-sided identity modulo snap, and v . v = 0.

      (4)  B(B(v,w), u) = 0 = B(v, B(w,u)) identically, by (1) and the fact
           that B(v,w) has zero syndrome.

    So the construction is a retraction of F_2^24 onto (C, XOR) — a perfectly
    good object, but an abelian group, not a commutative non-associative
    algebra.  The earlier claim of non-associativity (and hence of a
    Griess-like structure) does not hold; `snap_algebra_report` checks each of
    (1) - (4) by execution.

    NOT claimed anywhere here: a relationship to the Griess algebra, to the
    Monster, or to any 196,884-dimensional structure.
    """

    @staticmethod
    def snap_word(v: Sequence[int]) -> List[int]:
        return GOLAY.snap(v)[0]

    @staticmethod
    def bilinear_defect(v: Sequence[int], w: Sequence[int]) -> List[int]:
        """B(v, w): the failure of `snap` to be F_2-linear."""
        s_vw = SnapAlgebra.snap_word(BitOps.xor(v, w))
        s_v = SnapAlgebra.snap_word(v)
        s_w = SnapAlgebra.snap_word(w)
        s_0 = SnapAlgebra.snap_word([0] * 24)
        return BitOps.xor(BitOps.xor(s_vw, s_v), BitOps.xor(s_w, s_0))

    @staticmethod
    def product(v: Sequence[int], w: Sequence[int]) -> List[int]:
        s_vw = SnapAlgebra.snap_word(BitOps.xor(v, w))
        return BitOps.xor(s_vw, SnapAlgebra.bilinear_defect(v, w))


def snap_algebra_report(samples: int = 400) -> Dict[str, object]:
    """Check statements (1) - (4) of `SnapAlgebra` on a deterministic sweep."""
    state = 0xABCDEF

    def draw() -> List[int]:
        nonlocal state
        state = (1103515245 * state + 12345) & 0xFFFFFF
        return BitOps.from_int(state, 24)

    zero = [0] * 24
    commutative = True
    identity_ok = True
    defect_nonzero = 0
    defect_is_codeword = True
    defect_syndrome_only = True
    product_is_snap_xor_snap = True
    assoc_failures = 0
    triple_defect_nonzero = 0
    square_nonzero = 0
    leaders = GOLAY.leader_table()

    for _ in range(samples):
        v, w, u = draw(), draw(), draw()
        prod = SnapAlgebra.product(v, w)
        if prod != SnapAlgebra.product(w, v):
            commutative = False
        if SnapAlgebra.product(v, zero) != SnapAlgebra.snap_word(v):
            identity_ok = False
        defect = SnapAlgebra.bilinear_defect(v, w)
        if any(defect):
            defect_nonzero += 1
        if not GOLAY.is_codeword(defect):
            defect_is_codeword = False
        # statement (1): B is a function of the two syndromes alone
        sv, sw = GOLAY.syndrome_int(v), GOLAY.syndrome_int(w)
        predicted = BitOps.xor(
            BitOps.xor(BitOps.from_int(leaders[sv ^ sw], 24),
                       BitOps.from_int(leaders[sv], 24)),
            BitOps.from_int(leaders[sw], 24))
        if predicted != defect:
            defect_syndrome_only = False
        # statement (2)
        if prod != BitOps.xor(SnapAlgebra.snap_word(v), SnapAlgebra.snap_word(w)):
            product_is_snap_xor_snap = False
        # statement (3)
        if SnapAlgebra.product(SnapAlgebra.product(v, w), u) != \
                SnapAlgebra.product(v, SnapAlgebra.product(w, u)):
            assoc_failures += 1
        if any(SnapAlgebra.product(v, v)):
            square_nonzero += 1
        # statement (4)
        if any(SnapAlgebra.bilinear_defect(defect, u)):
            triple_defect_nonzero += 1

    return {
        "samples": samples,
        "commutative": commutative,
        "zero_is_identity_up_to_snap": identity_ok,
        "nonlinear_defect_nonzero_count": defect_nonzero,
        "defect_is_always_a_codeword": defect_is_codeword,
        "defect_depends_only_on_syndromes": defect_syndrome_only,
        "product_equals_snap_xor_snap": product_is_snap_xor_snap,
        "associativity_failures": assoc_failures,
        "associative": assoc_failures == 0,
        "squares_are_zero": square_nonzero == 0,
        "triple_defect_nonzero_count": triple_defect_nonzero,
        "earlier_non_associativity_claim_holds": assoc_failures > 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §4.  THE SEMIDIRECT PRODUCT  2^(1+24) : S_12
# ══════════════════════════════════════════════════════════════════════════════
#
#  GLM v19 asked for "2^(1+24) semidirect Co_1" and implemented the outer
#  factor as permutations of the 12 Heisenberg pairs.  That construction is
#  sound but it is NOT Co_1: permuting the pairs gives the symmetric group
#  S_12, of order 479,001,600, whereas |Co_1| is about 4.16 x 10^18.  Both are
#  subgroups of the outer automorphism group O^+(24,2) of the extraspecial
#  group, and S_12 is the piece a small machine can carry exactly.  So this
#  section ships the honest object under its own name.
#
#  A pair permutation sigma acts on Heisenberg coordinates by permuting the
#  twelve bits of a and of b simultaneously.  That preserves the F_2 inner
#  product <a, b>, hence the cocycle, hence it is an automorphism fixing the
#  centre - verified below rather than asserted.

PairPerm = Tuple[int, ...]        # a permutation of {0, ..., 11}

IDENTITY_PERM: PairPerm = tuple(range(12))


def permute_bits(mask: int, perm: PairPerm) -> int:
    """Send bit i of `mask` to bit perm[i]."""
    out = 0
    for i in range(12):
        if (mask >> i) & 1:
            out |= 1 << perm[i]
    return out


def perm_inverse(perm: PairPerm) -> PairPerm:
    inv = [0] * 12
    for i, p in enumerate(perm):
        inv[p] = i
    return tuple(inv)


def perm_compose(sigma: PairPerm, tau: PairPerm) -> PairPerm:
    """sigma after tau."""
    return tuple(sigma[tau[i]] for i in range(12))


def act_on_element(sigma: PairPerm, g: ExtraspecialElement) -> ExtraspecialElement:
    """The automorphism induced by a pair permutation."""
    return ExtraspecialElement(permute_bits(g.a, sigma),
                               permute_bits(g.b, sigma), g.eps)


@dataclass(frozen=True)
class NormaliserElement:
    """
    An element (g, sigma) of 2^(1+24) : S_12, multiplying by

        (g, sigma) * (h, tau) = (g * sigma(h), sigma tau).
    """

    g: ExtraspecialElement
    sigma: PairPerm = IDENTITY_PERM

    def __mul__(self, other: "NormaliserElement") -> "NormaliserElement":
        return NormaliserElement(self.g * act_on_element(self.sigma, other.g),
                                 perm_compose(self.sigma, other.sigma))

    def inverse(self) -> "NormaliserElement":
        inv = perm_inverse(self.sigma)
        return NormaliserElement(act_on_element(inv, self.g.inverse()), inv)

    def is_identity(self) -> bool:
        return self.g.is_identity() and self.sigma == IDENTITY_PERM

    @staticmethod
    def identity() -> "NormaliserElement":
        return NormaliserElement(ExtraspecialElement.identity(), IDENTITY_PERM)

    def columns(self) -> List[Tuple[int, int]]:
        """
        The element as a signed permutation of the 4096 basis vectors:

            rho(g, sigma) |k> = rho(g) |sigma . k>,

        where sigma . k permutes the twelve bits of the index k (bit i of k
        becomes bit sigma(i)).  Storing the operator as 4096 (target, sign)
        pairs makes the homomorphism check an exact comparison of integer
        lists rather than a numerical one.
        """
        cols_g = SchrodingerRep.matrix_columns(self.g)
        return [cols_g[permute_bits(k, self.sigma)]
                for k in range(SchrodingerRep.DIM)]


def _sample_pair_perms() -> List[PairPerm]:
    """A small deterministic set of pair permutations, including generators."""
    swap01 = (1, 0) + tuple(range(2, 12))
    cycle3 = (1, 2, 0) + tuple(range(3, 12))
    reverse = tuple(range(11, -1, -1))
    shift = tuple((i + 5) % 12 for i in range(12))
    return [IDENTITY_PERM, swap01, cycle3, reverse, shift]


def normaliser_report() -> Dict[str, object]:
    """
    Verify the semidirect product 2^(1+24) : S_12 exactly:

      * pair permutations act by automorphisms of the extraspecial group;
      * the product is associative, unital and has inverses;
      * conjugation moves the generators as it should: (1,s) x_i (1,s)^-1 =
        x_{s(i)};
      * the product is genuinely non-commutative;
      * (g, sigma) -> signed permutation of the 4096 basis vectors is a
        homomorphism, checked as an operator identity on the whole space.
    """
    perms = _sample_pair_perms()
    elements = [ExtraspecialElement(a, b, e)
                for a, b, e in ((0b101101, 0b011010, 0),
                                (0b111000111, 0b000111000, 1),
                                (1 << 3, 1 << 7, 0),
                                (0xFFF, 0xAAA, 1))]

    automorphic = all(act_on_element(s, g * h)
                      == act_on_element(s, g) * act_on_element(s, h)
                      for s in perms for g in elements for h in elements)
    centre_fixed = all(act_on_element(s, ExtraspecialElement.z())
                       == ExtraspecialElement.z() for s in perms)

    units = [NormaliserElement(g, s) for g in elements for s in perms]
    ident = NormaliserElement.identity()
    associative = all(((u * v) * w) == (u * (v * w))
                      for u in units[:6] for v in units[:6] for w in units[:6])
    unital = all((ident * u) == u and (u * ident) == u for u in units)
    inverses = all((u * u.inverse()).is_identity()
                   and (u.inverse() * u).is_identity() for u in units)

    conjugation_ok = True
    for s in perms:
        s_elem = NormaliserElement(ExtraspecialElement.identity(), s)
        for i in range(12):
            conj = s_elem * NormaliserElement(ExtraspecialElement.x(i)) \
                * s_elem.inverse()
            conjugation_ok = conjugation_ok and \
                conj == NormaliserElement(ExtraspecialElement.x(s[i]))

    non_commuting = sum(1 for u in units[:8] for v in units[:8]
                        if (u * v) != (v * u))

    homomorphic = True
    for u in units[:5]:
        for v in units[:5]:
            lhs = (u * v).columns()
            cols_u, cols_v = u.columns(), v.columns()
            rhs = [(cols_u[t][0], cols_u[t][1] * sgn) for (t, sgn) in cols_v]
            homomorphic = homomorphic and lhs == rhs

    return {
        "outer_factor": "S_12 (pair permutations), order 479001600",
        "not_co1": "Co_1 is not implemented; S_12 < O^+(24,2) is",
        "pair_perms_are_automorphisms": automorphic,
        "centre_fixed": centre_fixed,
        "associative": associative,
        "unital": unital,
        "inverses": inverses,
        "conjugation_moves_generators": conjugation_ok,
        "non_commuting_pairs": non_commuting,
        "action_is_homomorphism_on_4096": homomorphic,
        "group_order": (1 << 25) * 479001600,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def monster_tier_audit() -> Dict[str, object]:
    return {
        "code_automorphisms": column_symmetry_report(),
        "extraspecial": extraspecial_relation_report(),
        "normaliser": normaliser_report(),
        "snap_algebra": snap_algebra_report(),
    }


def _print_audit() -> Dict[str, object]:
    a = monster_tier_audit()
    print("=" * 78)
    print("  GLM UPPER-TIER AUDIT")
    print("=" * 78)
    print("\n[Golay code automorphisms, tested on all 4096 words; see glm_m24.py]")
    for name, ok in a["code_automorphisms"].items():
        print(f"    {name:<24}{'IS an automorphism' if ok else 'is NOT an automorphism'}")
    print("\n[Extraspecial 2^(1+24) in its 4096-dimensional representation]")
    for key, value in a["extraspecial"].items():
        print(f"    {key:<38}{value}")
    print("\n[Semidirect product 2^(1+24) : S_12]")
    for key, value in a["normaliser"].items():
        print(f"    {key:<38}{value}")
    print("\n[Snap algebra (exploratory)]")
    for key, value in a["snap_algebra"].items():
        print(f"    {key:<38}{value}")
    print("=" * 78)
    return a


if __name__ == "__main__":
    _print_audit()
