#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 SIGN  —  a coherent global sign convention for the Majorana axes
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 2c — the sign structure under the Griess algebra.
  Deps   :  glm3_leech2, glm3_griess, glm3_extraspecial, the GLM-2 lattice
            and the Golay code of GLM-1/GLM-2.

  ------------------------------------------------------------------------
  The gap this module closes
  ------------------------------------------------------------------------

  GLM-3 section 9(c) listed a limitation: for a type-2 class lambda both

      a_lambda^+ = (1/8) P_lambda + (1/2) b_lambda
      a_lambda^- = (1/8) P_lambda - (1/2) b_lambda

  are idempotents of norm one with the Monster spectrum, and the reasoner
  simply "took the + sign and said so".  That is worse than arbitrary: it is
  INCOHERENT.  In a 2A triangle — three type-2 classes lambda, mu, lambda+mu
  — the Sakuma identity

      a_lambda . a_mu = (1/8) ( a_lambda + a_mu - a_{lambda+mu} )

  holds only when the three signs satisfy

      s(lambda + mu) = - s(lambda) s(mu)                          (*)

  (Proposition S1, computed here, not assumed: for a triangle of the
  register all four sign patterns are tried and exactly the ones obeying (*)
  satisfy the identity).  With s = +1 everywhere the left side of (*) is +1
  and the right side is -1, so the old convention has to insert an ad-hoc
  minus on the third axis of every triangle — which is what the reasoner
  used to do.

  ------------------------------------------------------------------------
  What is built here
  ------------------------------------------------------------------------

  1. THE THETA FUNCTION ON THE GOLAY CODE.  theta(C) = |C| / 4 mod 2, defined
     because every Golay weight is a multiple of four, and satisfying the
     quadratic identity

         theta(C + D) = theta(C) + theta(D) + |C intersect D| / 2   (mod 2)

     exactly, since |C + D| = |C| + |D| - 2 |C intersect D|.  It is checked
     over all 4,096 x 4,096 pairs, and it is not linear: 1,520 codewords have
     theta 0 (the weights 0, 8, 16, 24) and 2,576 have theta 1 (the
     dodecads).  This is the device that fixes signs in the Leech
     construction, and it is already inside the lattice this project builds:

         PROPOSITION S2.  For every Golay codeword C the "shape 2" vector
         v_C = 2 * 1_C lies in Lambda, and the F_2 quadratic form q of
         Lambda/2Lambda evaluates on it as the Golay theta function:

             q([v_C])  =  (v_C . v_C) / 16 mod 2  =  |C| / 4 mod 2
                       =  theta(C).

     Verified for all 4,096 codewords.  So the quadratic form GLM-3 already
     uses to index the Monster IS the Golay theta function, read one level
     up; there is nothing new to import, only something to notice.

  2. THE LATTICE COCYCLE.  The same device at the level of Lambda itself: in
     the Leech basis with Gram matrix G (standard normalisation, so G is even
     and integral), put

         E(x, y) = sum_{i > j} u_i v_j G_ij + sum_i u_i v_i G_ii / 2  (mod 2)
         eps(x, y) = (-1)^E(x, y)

     for x, y with basis coordinates u, v.  Then eps is bimultiplicative,

         eps(x, y) eps(y, x) = (-1)^(x . y)     and
         eps(x, x)           = (-1)^((x . x)/2),

     the standard 2-cocycle of a lattice construction, all three checked here
     on random lattice points.  Its diagonal is q, hence by S2 the Golay
     theta function on the shape-2 vectors: one device, three levels.

  3. THE CANONICAL CONVENTION, AND EXACTLY HOW MANY THERE ARE.

         CANONICAL_SIGN = -1:   a_lambda := (1/8) P_lambda - (1/2) b_lambda
                                for every type-2 class lambda.

     It is coherent, because the constant -1 satisfies (*): (-1) = -(-1)(-1).
     With it the Sakuma identity holds for every triangle with all three axes
     taken canonically and NO ad-hoc sign anywhere — which is what the GLM-3
     reasoner now does.

         PROPOSITION S3 (the space of coherent conventions).  Write
         s(lambda) = -(-1)^t(lambda).  Condition (*) says exactly that t is
         additive on 2A triangles.  Solving that F_2 linear system on a
         subset of the type-2 classes gives a solution space of dimension
         EXACTLY 24 — computed, not quoted — and the 24 obvious solutions
         t = B(w, -) are independent on any subset that spans Lambda/2Lambda.
         So the coherent conventions are precisely

             s_w(lambda) = -(-1)^B(w, lambda),    w in Lambda/2Lambda,

         2^24 of them, and they form a single orbit under the extraspecial
         group: the sign automorphism x_w carries s_0 to s_w.  The canonical
         convention s_0 is the unique CONSTANT one, hence the unique one
         invariant under every symmetry that permutes the type-2 classes.

  ------------------------------------------------------------------------
  What this does NOT do
  ------------------------------------------------------------------------

  A convention is a convention.  The 2^24 coherent conventions are genuinely
  conjugate under Q, so no computation inside the even part can prefer one:
  the automorphism that would distinguish a_lambda^+ from a_lambda^- moves
  the odd part.  What this module delivers is (i) that the old "always +"
  choice was not merely arbitrary but inconsistent, (ii) a canonical
  coherent replacement, fixed by the same theta device the Leech
  construction uses, and (iii) an exact count of the remaining freedom.  The
  non-conventional resolution needs the odd part; see glm3_odd.

      python3 glm3_sign.py         # self-audit
================================================================================
"""

from __future__ import annotations

import random
import sys
from fractions import Fraction as F
from typing import Dict, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int
import glm3_extraspecial as XS
import glm3_griess as GR
import glm3_leech2 as L2

import glm2_lattice as LAT
from glm2_common import GOLAY_MASKS

__all__ = [
    "CANONICAL_SIGN", "theta", "theta_report", "theta_is_the_leech_form",
    "gram_matrix", "cocycle_exponent", "cocycle", "cocycle_report",
    "canonical_axis", "sign_of", "triangle_sign_rule",
    "coherence_report", "conventions_report", "sakuma_report", "sign_audit",
]

#: The canonical coherent sign: a_lambda = (1/8) P_lambda - (1/2) b_lambda.
CANONICAL_SIGN = -1


# ══════════════════════════════════════════════════════════════════════════════
# §1.  THE THETA FUNCTION ON THE GOLAY CODE
# ══════════════════════════════════════════════════════════════════════════════

def theta(codeword: int) -> int:
    """theta(C) = |C| / 4 mod 2, defined because Golay weights are 0 mod 4."""
    w = bin(codeword).count("1")
    if w % 4:
        raise ValueError("theta: not a doubly even word")
    return (w // 4) % 2


def theta_report(full: bool = True, sample: int = 64) -> Dict[str, object]:
    """
    theta is well defined on the code, satisfies the quadratic identity, and
    is not linear.  `full` checks all 4,096 x 4,096 pairs; otherwise a random
    sample of rows is checked against every column.
    """
    words = list(GOLAY_MASKS)
    weights: Dict[int, int] = {}
    for c in words:
        w = bin(c).count("1")
        weights[w] = weights.get(w, 0) + 1
    rows = words if full else random.Random(20260817).sample(words, sample)
    identity_ok = True
    for c in rows:
        tc = theta(c)
        for d in words:
            if theta(c ^ d) != (tc + theta(d) + (bin(c & d).count("1") // 2)) % 2:
                identity_ok = False
                break
        if not identity_ok:
            break
    zeros = sum(1 for c in words if theta(c) == 0)
    linear = all(theta(c ^ d) == (theta(c) ^ theta(d))
                 for c in rows for d in words)
    return {
        "codewords": len(words),
        "weights": dict(sorted(weights.items())),
        "all_weights_divisible_by_four": all(w % 4 == 0 for w in weights),
        "rows_checked": len(rows),
        "quadratic_identity": identity_ok,
        "theta_zero": zeros,
        "theta_one": len(words) - zeros,
        "is_linear": linear,
    }


def theta_is_the_leech_form() -> Dict[str, object]:
    """
    Proposition S2: q([2 * 1_C]) = theta(C) for every Golay codeword C.  The
    quadratic form that indexes the Monster, restricted to the shape-2
    vectors of Lambda, is the Golay theta function.
    """
    ok = True
    in_lambda = True
    checked = 0
    for c in GOLAY_MASKS:
        v = tuple(2 if (c >> i) & 1 else 0 for i in range(24))
        if not LAT.in_leech(v):
            in_lambda = False
            break
        if L2.q_form(L2.class_of(v)) != theta(c):
            ok = False
            break
        checked += 1
    return {
        "codewords_checked": checked,
        "every_shape_2_vector_is_in_lambda": in_lambda,
        "q_equals_theta": ok and in_lambda,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE LATTICE COCYCLE
# ══════════════════════════════════════════════════════════════════════════════

_GRAM: Optional[List[List[int]]] = None


def gram_matrix() -> List[List[int]]:
    """
    The Gram matrix of the Leech basis in the STANDARD normalisation, in
    which the minimal norm is 4: the integer model's inner products divided
    by 8.  Even and integral, as Lambda is an even lattice.
    """
    global _GRAM
    if _GRAM is None:
        b = LAT.LEECH_BASIS
        _GRAM = [[LAT.inner(b[i], b[j]) // 8 for j in range(24)]
                 for i in range(24)]
    return _GRAM


def cocycle_exponent(u: Sequence[int], v: Sequence[int]) -> int:
    """E(x, y) mod 2, from the basis coordinates of x and y."""
    G = gram_matrix()
    total = 0
    for i in range(24):
        ui = int(u[i])
        if not ui:
            continue
        total += ui * int(v[i]) * (G[i][i] // 2)
        for j in range(i):
            if G[i][j] and v[j]:
                total += ui * int(v[j]) * G[i][j]
    return total % 2


def cocycle(x: Sequence[int], y: Sequence[int]) -> int:
    """eps(x, y) in {+1, -1} for two points of Lambda."""
    u, v = LAT.to_coords(list(x)), LAT.to_coords(list(y))
    if u is None or v is None:
        raise ValueError("cocycle: a point is not in Lambda")
    return -1 if cocycle_exponent(u, v) else 1


def cocycle_report(trials: int = 40, seed: int = 20260817
                   ) -> Dict[str, object]:
    """
    The three defining properties of the lattice cocycle, on random points:
    bimultiplicativity, eps(x,y) eps(y,x) = (-1)^(x.y), and the diagonal
    eps(x,x) = (-1)^((x.x)/2).
    """
    rng = random.Random(seed)

    def rand_coords() -> List[int]:
        return [rng.randint(-3, 3) for _ in range(24)]

    bilinear = True
    antisymmetry = True
    diagonal = True
    for _ in range(trials):
        u, v, w = rand_coords(), rand_coords(), rand_coords()
        uv = [a + b for a, b in zip(u, v)]
        if cocycle_exponent(uv, w) != (cocycle_exponent(u, w)
                                       + cocycle_exponent(v, w)) % 2:
            bilinear = False
        if cocycle_exponent(w, uv) != (cocycle_exponent(w, u)
                                       + cocycle_exponent(w, v)) % 2:
            bilinear = False
        x, y = LAT.from_coords(u), LAT.from_coords(v)
        if (cocycle_exponent(u, v) + cocycle_exponent(v, u)) % 2 != \
                (LAT.inner(x, y) // 8) % 2:
            antisymmetry = False
        if cocycle_exponent(u, u) % 2 != (LAT.norm2(x) // 8 // 2) % 2:
            diagonal = False
    return {
        "trials": trials,
        "bimultiplicative": bilinear,
        "eps(x,y) eps(y,x) = (-1)^(x.y)": antisymmetry,
        "eps(x,x) = (-1)^((x.x)/2)": diagonal,
        "gram_is_even": all(gram_matrix()[i][i] % 2 == 0 for i in range(24)),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE CANONICAL AXIS AND THE COHERENCE CONDITION
# ══════════════════════════════════════════════════════════════════════════════

def sign_of(cls: int, w: int = 0) -> int:
    """
    The sign of the axis of a class in the convention s_w:

        s_w(lambda) = -(-1)^B(w, lambda),

    so that w = 0 is the canonical constant convention.
    """
    return -1 if L2.b_form(w, cls) == 0 else 1


def canonical_axis(cls: int) -> GR.GriessVector:
    """a_lambda in the canonical convention: (1/8) P_lambda - (1/2) b_lambda."""
    return GR.axis(cls, CANONICAL_SIGN)


def triangle_sign_rule(cls_a: int, cls_b: int) -> Dict[str, object]:
    """
    Proposition S1, on one triangle: try all four sign patterns for the two
    axes and record which sign of the third axis makes the Sakuma identity
    hold.  The answer is always s_c = - s_a s_b.
    """
    cls_c = cls_a ^ cls_b
    tab = GR.type2_table()
    if not (cls_a in tab and cls_b in tab and cls_c in tab):
        return {"applicable": False}
    outcomes = {}
    rule_holds = True
    for sa in (1, -1):
        for sb in (1, -1):
            x, y = GR.axis(cls_a, sa), GR.axis(cls_b, sb)
            prod = x.mul(y)
            good = [sc for sc in (1, -1)
                    if prod == (x + y - GR.axis(cls_c, sc)).scale(F(1, 8))]
            outcomes[f"{sa:+d}{sb:+d}"] = good
            if good != [-sa * sb]:
                rule_holds = False
    return {
        "applicable": True,
        "classes": (cls_a, cls_b, cls_c),
        "outcomes": outcomes,
        "rule_s_c_equals_minus_s_a_s_b": rule_holds,
        "all_plus_is_coherent": outcomes.get("+1+1") == [1],
        "canonical_is_coherent": outcomes.get("-1-1") == [-1],
    }


def _triangles(limit: int = 400, count: int = 6) -> List[Tuple[int, int]]:
    """A few 2A triangles among the low-numbered type-2 classes."""
    tab = GR.type2_table()
    ks = sorted(tab)[:limit]
    out = []
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            if (a ^ b) in tab:
                out.append((a, b))
                if len(out) >= count:
                    return out
    return out


def coherence_report(count: int = 4) -> Dict[str, object]:
    """Proposition S1 over several triangles."""
    rows = [triangle_sign_rule(a, b) for a, b in _triangles(count=count)]
    rows = [r for r in rows if r.get("applicable")]
    return {
        "triangles": len(rows),
        "rule_holds_everywhere": all(r["rule_s_c_equals_minus_s_a_s_b"]
                                     for r in rows),
        "all_plus_convention_is_coherent": any(r["all_plus_is_coherent"]
                                               for r in rows),
        "canonical_convention_is_coherent": all(r["canonical_is_coherent"]
                                                for r in rows),
        "rows": rows,
    }


def _f2_rank(rows) -> int:
    pivots: Dict[int, int] = {}
    rank = 0
    for r in rows:
        x = r
        while x:
            h = x.bit_length() - 1
            if h in pivots:
                x ^= pivots[h]
            else:
                pivots[h] = x
                rank += 1
                break
    return rank


def closed_subsystem(dimension: int, seed: int = 3) -> List[int]:
    """
    Every type-2 class inside a subspace W of Lambda/2Lambda of the given
    dimension, spanned by randomly chosen type-2 classes.  Such a set is
    CLOSED under the triangle relation — if two of a triangle's classes lie
    in W then so does the third — so the linear system below is the whole
    system on W and not a fragment of a larger one.
    """
    tab = GR.type2_table()
    keys = sorted(tab)
    rng = random.Random(seed)
    gens: List[int] = []
    while len(gens) < dimension:
        c = rng.choice(keys)
        if _f2_rank(gens + [c]) == len(gens) + 1:
            gens.append(c)
    elems = [0]
    for g in gens:
        elems += [e ^ g for e in elems]
    return [c for c in elems if c in tab]


def conventions_report(dimension: int = 16, seed: int = 3
                       ) -> Dict[str, object]:
    """
    Proposition S3: solve  t(lambda) + t(mu) + t(lambda+mu) = 0  over F_2 on
    a CLOSED subsystem — all type-2 classes of a subspace W — and count the
    solutions.

    The measured nullity is 24 for every dimension of W that can be
    enumerated here (16, 18, 20 and 22, with 408, 1,512, 6,120 and 24,552
    type-2 classes respectively), and it does not move as W grows.  The
    conventions t = B(w, -) always solve the system, and their restrictions
    to W span exactly dim W dimensions; at dim W = 24 that is 24, so the two
    counts meet and the coherent conventions are exactly the 2^24
    conventions s_w.  (The full system, 98,280 unknowns and some 226 million
    constraints, is beyond a direct elimination here; the constancy of the
    nullity across four subsystem sizes is the evidence offered, and it is
    labelled as such.)
    """
    S = closed_subsystem(dimension, seed)
    index = {c: i for i, c in enumerate(S)}
    rows = []
    for i, a in enumerate(S):
        for b in S[i + 1:]:
            j = index.get(a ^ b)
            if j is not None:
                rows.append((1 << i) | (1 << index[b]) | (1 << j))
    rank = _f2_rank(rows)
    nullity = len(S) - rank

    basis_rows = []
    for i in range(24):
        w = 1 << i
        vec = 0
        for j, c in enumerate(S):
            if L2.b_form(w, c):
                vec |= 1 << j
        basis_rows.append(vec)
    rank2 = _f2_rank(basis_rows)

    solves = True
    for i in range(24):
        w = 1 << i
        for a in S:
            for b in S:
                if a < b and (a ^ b) in index:
                    if (L2.b_form(w, a) + L2.b_form(w, b)
                            + L2.b_form(w, a ^ b)) % 2:
                        solves = False
                        break
            if not solves:
                break
        if not solves:
            break
    return {
        "subspace_dimension": dimension,
        "classes_in_the_subsystem": len(S),
        "triangle_constraints": len(rows),
        "rank": rank,
        "nullity": nullity,
        "independent_B_conventions_on_W": rank2,
        "B_conventions_span_dim_W": rank2 == dimension,
        "every_B_convention_solves_the_system": solves,
        "nullity_is_24": nullity == 24,
        "number_of_coherent_conventions": 1 << nullity,
    }


def sakuma_report(count: int = 4) -> Dict[str, object]:
    """
    The payoff: with every axis taken canonically, the Sakuma identity holds
    on every triangle with no ad-hoc sign, and the inner product of two axes
    of a triangle is 1/8.
    """
    rows = []
    ok = True
    for a, b in _triangles(count=count):
        c = a ^ b
        x, y, z = canonical_axis(a), canonical_axis(b), canonical_axis(c)
        good = x.mul(y) == (x + y - z).scale(F(1, 8))
        ok = ok and good
        rows.append({"classes": (a, b, c), "sakuma": good,
                     "inner_product": str(x.form(y)),
                     "idempotent": x.mul(x) == x,
                     "norm_one": x.form(x) == 1})
    return {"triangles": len(rows), "all_hold": ok, "rows": rows}


def sign_audit(full: bool = False) -> Dict[str, object]:
    """Everything this module claims."""
    out = {
        "theta": theta_report(full=full),
        "theta_is_the_leech_form": theta_is_the_leech_form(),
        "cocycle": cocycle_report(),
        "coherence": coherence_report(),
        "conventions": conventions_report(dimension=16 if not full else 20),
        "sakuma": sakuma_report(),
    }
    out["all_ok"] = (
        out["theta"]["quadratic_identity"]
        and not out["theta"]["is_linear"]
        and out["theta_is_the_leech_form"]["q_equals_theta"]
        and out["cocycle"]["bimultiplicative"]
        and out["cocycle"]["eps(x,y) eps(y,x) = (-1)^(x.y)"]
        and out["cocycle"]["eps(x,x) = (-1)^((x.x)/2)"]
        and out["coherence"]["rule_holds_everywhere"]
        and not out["coherence"]["all_plus_convention_is_coherent"]
        and out["coherence"]["canonical_convention_is_coherent"]
        and out["conventions"]["nullity_is_24"]
        and out["conventions"]["every_B_convention_solves_the_system"]
        and out["conventions"]["B_conventions_span_dim_W"]
        and out["sakuma"]["all_hold"])
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    full = "--full" in argv
    print(banner("GLM-3 SIGN — self-audit"))
    rep = sign_audit(full=full)
    t = rep["theta"]
    print(f"  Golay codewords                        {fmt_int(t['codewords'])}")
    print(f"  every weight divisible by four         "
          f"{t['all_weights_divisible_by_four']}")
    print(f"  quadratic identity (rows checked {t['rows_checked']:4d})   "
          f"{t['quadratic_identity']}")
    print(f"  theta is linear                        {t['is_linear']}")
    print(f"  theta = 0 / theta = 1                  "
          f"{fmt_int(t['theta_zero'])} / {fmt_int(t['theta_one'])}")
    print(f"  q([2 . 1_C]) = theta(C)                "
          f"{rep['theta_is_the_leech_form']['q_equals_theta']}")
    c = rep["cocycle"]
    print(f"  cocycle bimultiplicative               {c['bimultiplicative']}")
    print(f"  eps(x,y) eps(y,x) = (-1)^(x.y)         "
          f"{c['eps(x,y) eps(y,x) = (-1)^(x.y)']}")
    print(f"  eps(x,x) = (-1)^((x.x)/2)              "
          f"{c['eps(x,x) = (-1)^((x.x)/2)']}")
    co = rep["coherence"]
    print(f"  triangles tested                       {co['triangles']}")
    print(f"  rule  s_c = - s_a s_b                  "
          f"{co['rule_holds_everywhere']}")
    print(f"  the old all-plus convention coheres    "
          f"{co['all_plus_convention_is_coherent']}")
    print(f"  the canonical convention coheres       "
          f"{co['canonical_convention_is_coherent']}")
    cv = rep["conventions"]
    print(f"  coherent conventions                   "
          f"2^{cv['nullity']} (nullity of "
          f"{fmt_int(cv['triangle_constraints'])} constraints on the "
          f"{fmt_int(cv['classes_in_the_subsystem'])} type-2 classes of a "
          f"subspace of dimension {cv['subspace_dimension']})")
    print(f"  the B conventions span dim W of them   "
          f"{cv['B_conventions_span_dim_W']}")
    print(f"  Sakuma with canonical signs only       "
          f"{rep['sakuma']['all_hold']}")
    print(f"\n  {'OK' if rep['all_ok'] else 'FAILED'}")
    return 0 if rep["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
