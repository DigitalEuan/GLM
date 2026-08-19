#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 METRIC  —  from an invariant pairing to an honest distance
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 2b — geometry of the register inside the Griess algebra.
  Deps   :  glm3_leech2, glm3_griess, and the GLM-2 lattice.

  ------------------------------------------------------------------------
  The gap this module closes
  ------------------------------------------------------------------------

  GLM-3 section 9(e) listed a limitation: the Monster SIMILARITY

      sim(a, b) = ( g(a), g(b) ),      g(c) = sum over axis planes
                                              of 2^-k a_{d_k}

  is an invariant bilinear pairing, not a distance.  Ranking by it is a
  heuristic: nothing guarantees a triangle inequality, and nothing
  guarantees that two different concepts are ever apart.

  Both halves of that gap are closed here, and they are closed differently,
  because they have different causes.

  (1) THE TRIANGLE INEQUALITY IS FREE.  The invariant form on the even part
      is, in the basis this project builds it in,

          (x, y) = 2 sum_{i,j} A^x_ij A^y_ij  +  2 sum_c B^x_c B^y_c ,

      so (x, x) is 2 times a SUM OF SQUARES of rational numbers.  It is
      therefore positive definite: (x, x) >= 0 always, and (x, x) = 0 only
      for x = 0.  A positive definite symmetric bilinear form is an inner
      product, so

          d(a, b) = sqrt( (g(a) - g(b), g(a) - g(b)) )

      already satisfies the triangle inequality, by Cauchy-Schwarz.  No
      normalisation, no tuning, no heuristic: d is a pseudometric on
      concepts the moment the form is positive definite.  Section 1 and
      section 2.

  (2) IT IS ONLY A PSEUDOMETRIC, BECAUSE g IS NOT INJECTIVE.  d(a, b) = 0
      says g(a) = g(b), not a = b.  Over the 660-concept register g takes
      only 162 distinct values: 70 concepts have no type-2 plane at all and
      so land on g = 0 together, and other fibres are as large as 90.  Two
      repairs, both carried out here.

      (2a) QUOTIENT.  "Same Griess vector" is an equivalence relation, and d
           descends to an honest METRIC on the 162 classes (section 3).
           Nearest-neighbour search in the quotient is exact: d = 0 now
           means "the same class", and the classes are printed, so nothing
           is hidden.

      (2b) RESTORE INJECTIVITY — the plane-graded embedding (section 4).
           g throws away two things: the planes that are not axes, and the
           plane index (everything is summed into one vector).  Put both
           back.  For a class c of Lambda/2Lambda define

               v(c) = a_c                       if c is of type 2
                    = eta * P^(c)               if c is of any other
                                                  nonzero type
                    = 0                         if c = 0,

           where P^(c) = r r^T / (r . r) is the rank-one ORTHOGONAL
           PROJECTOR onto the line through the canonical representative r of
           c (the lattice point whose Leech-basis coordinates are the 24 bits
           of c).  P^ lies in the 300-dimensional part of the even algebra,
           so v(c) is an element of the Griess algebra for every class, axis
           or not.  Then embed a concept as the whole graded word

               G(x) = ( 2^-k v(d_k) )_{k < depth}   in   (V+)^depth ,

           with the product form.  v is injective on all 2^24 classes
           (Proposition M3), the stack is faithful (C35), and the carrier is
           injective on meanings (C3), so G is INJECTIVE on concepts, and

               D(a, b) = sqrt( sum_k 4^-k ( v(d_k^a) - v(d_k^b),
                                            v(d_k^a) - v(d_k^b) ) )

           is a genuine METRIC on the register — positivity, symmetry,
           triangle inequality, and D(a, b) = 0 if and only if a and b have
           the same meaning.  Section 4.

  Everything is exact: distances are held as their rational SQUARES, and
  comparisons that would need a square root are done by the usual
  square-both-sides argument on rationals (`triangle_holds`).  No float
  arithmetic appears anywhere in this module except in the human-readable
  printing helper `approx`.

  ------------------------------------------------------------------------
  What the guarantees buy
  ------------------------------------------------------------------------

  Nearest neighbour and clustering stop being rankings and become
  computations in a metric space:

      * `nearest(name, k)` returns the k nearest concepts with exact squared
        distances, and the answer is stable under any monotone rescaling;
      * `cluster(threshold)` is single-linkage clustering, whose output is a
        partition determined by the metric alone (union-find over the pairs
        at distance <= threshold), with no dependence on order or seeding;
      * `separation_report()` measures the smallest nonzero distance in the
        register, so the resolution of the embedding is a number and not an
        impression.

      python3 glm3_metric.py            # self-audit
      python3 glm3_metric.py nearest energy
      python3 glm3_metric.py cluster 1/4
================================================================================
"""

from __future__ import annotations

import sys
from fractions import Fraction as F
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int
import glm3_griess as GR
import glm3_leech2 as L2
import glm3_sign as SGN

import glm2_lattice as LAT

__all__ = [
    "ETA", "form_is_sum_of_squares", "positive_definite_report",
    "norm2_of", "griess_key", "pseudo_distance2", "triangle_holds",
    "quotient_classes", "quotient_report",
    "plane_vector", "plane_vector_norm2", "plane_distance2",
    "graded_embedding", "distance2", "distance2_of_stacks",
    "injectivity_report", "separation_report",
    "nearest", "cluster", "metric_audit", "approx",
]

#: The weight given to a plane that carries no Majorana axis.  Any positive
#: value gives a metric; the default keeps a non-axis plane's contribution the
#: same order as an axis plane's (an axis has norm 1, a projector norm sqrt 2).
ETA = F(1)


def approx(x: F, places: int = 6) -> str:
    """A decimal approximation of a rational, for printing only."""
    q = F(x)
    neg = q < 0
    q = -q if neg else q
    scaled = (q * (10 ** places)).__round__()
    s = str(scaled).rjust(places + 1, "0")
    return ("-" if neg else "") + s[:-places] + "." + s[-places:]


def _isqrt_floor(n: int) -> int:
    if n < 0:
        raise ValueError("negative")
    import math
    return math.isqrt(n)


def sqrt_approx(x: F, places: int = 6) -> str:
    """A decimal approximation of sqrt(x) for a nonnegative rational."""
    if x < 0:
        raise ValueError("sqrt_approx: negative")
    scale = 10 ** (2 * places)
    n = (F(x) * scale).__floor__()
    return approx(F(_isqrt_floor(int(n)), 10 ** places), places)


# ══════════════════════════════════════════════════════════════════════════════
# §1.  THE FORM IS POSITIVE DEFINITE
# ══════════════════════════════════════════════════════════════════════════════

def form_is_sum_of_squares(x: GR.GriessVector) -> Tuple[F, F]:
    """
    (x, x) recomputed as an explicit sum of squares:

        (x, x) = FORM_A * sum_ij (A_ij)^2  +  FORM_B * sum_c (B_c)^2 ,

    with FORM_A = FORM_B = 2 > 0.  Returns the pair (recomputed, form value)
    so a caller can check that the two agree; every caller here does.
    """
    sa = sum(x.A[i][j] * x.A[i][j] for i in range(GR.N) for j in range(GR.N))
    sb = sum(v * v for v in x.B.values())
    return GR.FORM_A * sa + GR.FORM_B * sb, x.form(x)


def norm2_of(x: GR.GriessVector) -> F:
    """(x, x), which by section 1 is >= 0 with equality only at x = 0."""
    return x.form(x)


def positive_definite_report(samples: Optional[Sequence[GR.GriessVector]] = None
                             ) -> Dict[str, object]:
    """
    The evidence that the invariant form is positive definite on the even
    part.  The argument is structural — the form is twice a sum of squares of
    the coordinates in the (A, B) basis, and both coefficients are positive —
    so the report checks the structure, not a random sample: for each supplied
    vector, that the sum-of-squares recomputation agrees with `form`, that the
    norm is nonnegative, and that it vanishes exactly for the zero vector.
    """
    if samples is None:
        tab = GR.type2_table()
        classes = sorted(tab)[:6]
        samples = [GR.zero(), GR.identity()]
        samples += [GR.axis(c) for c in classes]
        samples += [GR.axis(classes[0]) - GR.axis(classes[1]),
                    GR.b_vector(classes[2], F(-3, 7)),
                    GR.identity().scale(F(5, 2)) - GR.axis(classes[3])]
    rows = []
    ok = True
    for x in samples:
        recomputed, direct = form_is_sum_of_squares(x)
        zero = x.is_zero()
        good = (recomputed == direct and direct >= 0
                and (direct == 0) == zero)
        ok = ok and good
        rows.append({"norm2": str(direct), "is_zero": zero, "agrees": good})
    return {
        "form_a": str(GR.FORM_A), "form_b": str(GR.FORM_B),
        "both_coefficients_positive": GR.FORM_A > 0 and GR.FORM_B > 0,
        "sum_of_squares": True,
        "samples": rows,
        "all_ok": ok,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE PSEUDOMETRIC OF THE COLLAPSED EMBEDDING
# ══════════════════════════════════════════════════════════════════════════════

def pseudo_distance2(ga: GR.GriessVector, gb: GR.GriessVector) -> F:
    """d(a, b)^2 = (g(a) - g(b), g(a) - g(b)), exactly."""
    d = ga - gb
    return d.form(d)


def triangle_holds(d2_ab: F, d2_bc: F, d2_ac: F) -> bool:
    """
    Is  sqrt(d2_ac) <= sqrt(d2_ab) + sqrt(d2_bc)?  Decided exactly over the
    rationals: the inequality is equivalent to

        d2_ac - d2_ab - d2_bc <= 2 sqrt(d2_ab * d2_bc),

    which is automatic when the left side is nonpositive and otherwise
    equivalent to (d2_ac - d2_ab - d2_bc)^2 <= 4 * d2_ab * d2_bc.
    """
    lhs = F(d2_ac) - F(d2_ab) - F(d2_bc)
    if lhs <= 0:
        return True
    return lhs * lhs <= 4 * F(d2_ab) * F(d2_bc)


def griess_key(g: GR.GriessVector) -> Tuple[object, ...]:
    """A hashable key identifying a Griess vector exactly."""
    return (tuple(tuple(row) for row in g.A), tuple(sorted(g.B.items())))


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE QUOTIENT BY "SAME GRIESS VECTOR"
# ══════════════════════════════════════════════════════════════════════════════

def quotient_classes(vectors: Dict[str, GR.GriessVector]
                     ) -> Dict[Tuple[object, ...], List[str]]:
    """Group names by their Griess vector: the fibres of g."""
    out: Dict[Tuple[object, ...], List[str]] = {}
    for name, g in vectors.items():
        out.setdefault(griess_key(g), []).append(name)
    for names in out.values():
        names.sort()
    return out


def quotient_report(vectors: Dict[str, GR.GriessVector]) -> Dict[str, object]:
    """
    The honest metric on the quotient: how many classes there are, how big
    the fibres are, which concepts collapse to the zero vector (those with no
    axis plane at all), and a verification that on the quotient the distance
    separates points.
    """
    classes = quotient_classes(vectors)
    reps = {k: names[0] for k, names in classes.items()}
    sizes = sorted((len(v) for v in classes.values()), reverse=True)
    zero_key = griess_key(GR.zero())
    order = sorted(reps.values())
    separates = True
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            if pseudo_distance2(vectors[a], vectors[b]) == 0:
                separates = False
                break
        if not separates:
            break
    return {
        "concepts": len(vectors),
        "classes": len(classes),
        "largest_fibre": sizes[0] if sizes else 0,
        "singleton_classes": sum(1 for s in sizes if s == 1),
        "no_axis_at_all": len(classes.get(zero_key, [])),
        "fibre_sizes": sizes[:10],
        "distance_separates_classes": separates,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §4.  THE PLANE-GRADED EMBEDDING, AND A GENUINE METRIC
# ══════════════════════════════════════════════════════════════════════════════
#
#  Proposition M3 (injectivity of the plane vector).  The map
#
#      v : Lambda/2Lambda -> V+,      v(c) as defined in the header,
#
#  is injective, and v(c) = 0 only for c = 0.
#
#  Proof.  A type-2 class c has v(c) = (1/8) P_lam + (1/2) b_c, whose B-part
#  is the single coordinate b_c; the class is read straight off the support.
#  A class of any other nonzero type has v(c) = eta P^(c) with zero B-part, so
#  no type-2 class collides with it.  Among those, P^(c) is the orthogonal
#  projector onto the line R r(c); it determines that line, hence the pair
#  +- r(c); and r(c) is the lattice point whose Leech-basis coordinates are
#  the 24 bits of c, so its coordinate vector is a 0/1 vector.  Two 0/1
#  vectors that span the same line are equal (a positive multiple of a 0/1
#  vector has an entry outside {0, 1} unless the multiple is 1, and the
#  negative of a nonzero 0/1 vector has a negative entry), so the line
#  determines c.  Finally P^ has trace 1, so v(c) = 0 forces c = 0.       []
#
#  Corollary M4.  G(x) = (2^-k v(d_k(x)))_k is injective on the lattice points
#  the encoder produces, because the stack x -> (d_k(x)) is (C35), and the
#  form on (V+)^depth is positive definite because each summand is; so
#  D(x, y) = ||G(x) - G(y)|| is a metric.

_REP_CACHE: Dict[int, Tuple[Tuple[int, ...], int, bool]] = {}


def _rep_of_class(cls: int) -> Tuple[Tuple[int, ...], int, bool]:
    """
    (integer representative vector, its squared norm, is-it-an-axis) for a
    class: the minimal vector of the class when the class is of type 2, and
    otherwise the 0/1-coordinate representative.
    """
    if cls not in _REP_CACHE:
        if cls == 0:
            _REP_CACHE[cls] = ((0,) * 24, 0, False)
        else:
            tab = GR.type2_table()
            if cls in tab:
                v = tuple(int(c) for c in tab[cls])
                _REP_CACHE[cls] = (v, LAT.norm2(v), True)
            else:
                v = tuple(int(c) for c in L2.representative(cls))
                _REP_CACHE[cls] = (v, LAT.norm2(v), False)
    return _REP_CACHE[cls]


def plane_vector(cls: int, eta: F = ETA) -> GR.GriessVector:
    """
    The canonical Griess-algebra vector of ONE class — the axis when the
    class has one, and otherwise the rank-one orthogonal projector onto the
    line of the class's canonical representative, scaled by eta.
    """
    rep, n2, is_axis = _rep_of_class(cls)
    if cls == 0:
        return GR.zero()
    if is_axis:
        return SGN.canonical_axis(cls)
    # P^ = r r^T / (r . r); GR.outer uses the "times sqrt 8" model, in which
    # LAT.norm2 is 8 times the standard norm, so the two factors of 8 cancel.
    scale = F(eta * 8, n2)
    return GR.a_matrix([[scale * x for x in row] for row in GR.outer(rep)])


def plane_vector_norm2(cls: int, eta: F = ETA) -> F:
    """(v(c), v(c)): 1 for an axis, 2 eta^2 for a projector, 0 for c = 0."""
    if cls == 0:
        return F(0)
    _rep, _n2, is_axis = _rep_of_class(cls)
    return F(1) if is_axis else 2 * eta * eta


_PLANE_D2: Dict[Tuple[int, int], F] = {}


def plane_distance2(c1: int, c2: int, eta: F = ETA) -> F:
    """
    (v(c1) - v(c2), v(c1) - v(c2)), computed in O(24) from inner products
    rather than by building the 300-dimensional matrices:

        (P_u/8, P_w/8)  =  2 (u . w)^2 / 64^2  in the integer model,
        (P^u,   P^w)    =  2 (u . w)^2 / ((u.u)(w.w)),
        (P_u/8, P^w)    =  2 (u . w)^2 / (64 (w.w)),
        b-parts         =  2 * sum of squares of the differences.
    """
    if c1 == c2:
        return F(0)
    key = (c1, c2) if c1 <= c2 else (c2, c1)
    if eta == ETA and key in _PLANE_D2:
        return _PLANE_D2[key]
    u, nu, axis_u = _rep_of_class(c1)
    w, nw, axis_w = _rep_of_class(c2)
    uw = LAT.inner(u, w) if (c1 and c2) else 0

    def a_self(n2: int, is_axis: bool) -> F:
        if n2 == 0:
            return F(0)
        return F(n2 * n2, 4096) if is_axis else eta * eta

    def a_cross() -> F:
        if nu == 0 or nw == 0:
            return F(0)
        s = F(uw * uw)
        if axis_u and axis_w:
            return s / 4096
        if axis_u and not axis_w:
            return eta * s / (64 * F(nw))
        if axis_w and not axis_u:
            return eta * s / (64 * F(nu))
        return eta * eta * s / (F(nu) * F(nw))

    a_part = GR.FORM_A * (a_self(nu, axis_u) + a_self(nw, axis_w)
                          - 2 * a_cross())
    b_part = GR.FORM_B * (F(1, 4) * ((1 if axis_u else 0)
                                     + (1 if axis_w else 0)))
    out = a_part + b_part
    if eta == ETA:
        _PLANE_D2[key] = out
    return out


def graded_embedding(planes: Sequence[int], eta: F = ETA
                     ) -> List[GR.GriessVector]:
    """G(x): the word of plane vectors, weighted by 2^-k."""
    return [plane_vector(c, eta).scale(F(1, 1 << k))
            for k, c in enumerate(planes)]


def distance2_of_stacks(pa: Sequence[int], pb: Sequence[int],
                        eta: F = ETA) -> F:
    """D(a, b)^2 for two stacks of classes."""
    if len(pa) != len(pb):
        raise ValueError("distance2: the two stacks have different depths")
    total = F(0)
    for k, (ca, cb) in enumerate(zip(pa, pb)):
        if ca != cb:
            total += F(1, 1 << (2 * k)) * plane_distance2(ca, cb, eta)
    return total


def distance2(x: Sequence[int], y: Sequence[int], eta: F = ETA,
              depth: Optional[int] = None) -> F:
    """D(x, y)^2 for two lattice points."""
    kw = {} if depth is None else {"depth": depth}
    return distance2_of_stacks(L2.class_stack(x, **kw),
                               L2.class_stack(y, **kw), eta)


def injectivity_report(stacks: Dict[str, Sequence[int]],
                       eta: F = ETA) -> Dict[str, object]:
    """
    The metric separates the register: every pair of concepts with different
    carriers is at positive distance, and concepts with the same carrier are
    at distance zero.  Checked against the exact rational distances.
    """
    names = sorted(stacks)
    by_stack: Dict[Tuple[int, ...], List[str]] = {}
    for n in names:
        by_stack.setdefault(tuple(stacks[n]), []).append(n)
    collisions = 0
    zero_but_different = []
    positive_but_equal = []
    for i, a in enumerate(names):
        sa = stacks[a]
        for b in names[i + 1:]:
            d2 = distance2_of_stacks(sa, stacks[b], eta)
            same = tuple(sa) == tuple(stacks[b])
            if d2 == 0 and not same:
                zero_but_different.append((a, b))
            if d2 != 0 and same:
                positive_but_equal.append((a, b))
            if same:
                collisions += 1
    return {
        "concepts": len(names),
        "distinct_stacks": len(by_stack),
        "pairs_with_equal_carriers": collisions,
        "distance_zero_yet_different": len(zero_but_different),
        "examples_of_failure": zero_but_different[:3],
        "distance_positive_yet_equal": len(positive_but_equal),
        "is_a_metric_on_the_register": (not zero_but_different
                                        and not positive_but_equal),
    }


def separation_report(stacks: Dict[str, Sequence[int]], eta: F = ETA
                      ) -> Dict[str, object]:
    """The resolution of the embedding: the extreme distances it realises."""
    names = sorted(stacks)
    best: Optional[Tuple[F, str, str]] = None
    worst: Optional[Tuple[F, str, str]] = None
    for i, a in enumerate(names):
        sa = stacks[a]
        for b in names[i + 1:]:
            d2 = distance2_of_stacks(sa, stacks[b], eta)
            if d2 == 0:
                continue
            if best is None or d2 < best[0]:
                best = (d2, a, b)
            if worst is None or d2 > worst[0]:
                worst = (d2, a, b)
    return {
        "closest_pair": None if best is None else (best[1], best[2]),
        "closest_distance2": None if best is None else str(best[0]),
        "closest_distance": None if best is None else sqrt_approx(best[0]),
        "farthest_pair": None if worst is None else (worst[1], worst[2]),
        "farthest_distance2": None if worst is None else str(worst[0]),
        "farthest_distance": None if worst is None else sqrt_approx(worst[0]),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §5.  NEAREST NEIGHBOURS AND CLUSTERING, WITH GUARANTEES
# ══════════════════════════════════════════════════════════════════════════════

def nearest(name: str, stacks: Dict[str, Sequence[int]], count: int = 8,
            eta: F = ETA) -> List[Tuple[str, F]]:
    """The `count` nearest concepts to `name`, by exact squared distance."""
    if name not in stacks:
        raise KeyError(name)
    sa = stacks[name]
    scored = [(distance2_of_stacks(sa, s, eta), n)
              for n, s in stacks.items() if n != name]
    scored.sort(key=lambda t: (t[0], t[1]))
    return [(n, d) for d, n in scored[:count]]


def cluster(stacks: Dict[str, Sequence[int]], threshold: F,
            eta: F = ETA) -> List[List[str]]:
    """
    Single-linkage clustering at a threshold on the DISTANCE (not its
    square): the partition generated by the relation D(a, b) <= threshold.
    Because D is a metric, the output depends on the data and the threshold
    alone — not on an order of visits, an initial seeding or a tie-break.
    """
    names = sorted(stacks)
    t2 = F(threshold) * F(threshold)
    parent = {n: n for n in names}

    def find(a: str) -> str:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, a in enumerate(names):
        sa = stacks[a]
        for b in names[i + 1:]:
            if distance2_of_stacks(sa, stacks[b], eta) <= t2:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb
    groups: Dict[str, List[str]] = {}
    for n in names:
        groups.setdefault(find(n), []).append(n)
    out = [sorted(v) for v in groups.values()]
    out.sort(key=lambda g: (-len(g), g[0]))
    return out


# ══════════════════════════════════════════════════════════════════════════════
# §6.  SELF-AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def metric_audit(stacks: Optional[Dict[str, Sequence[int]]] = None,
                 vectors: Optional[Dict[str, GR.GriessVector]] = None,
                 triples: int = 200) -> Dict[str, object]:
    """
    Everything this module claims, checked: positive definiteness, the
    triangle inequality on sampled triples of both distances, the quotient,
    injectivity of the plane vector, and the metric axioms on the register.
    """
    import random

    out: Dict[str, object] = {}
    out["positive_definite"] = positive_definite_report()

    tab = GR.type2_table()
    classes = sorted(tab)[:24]
    # v is injective on the classes it is offered
    sample = classes + [0] + [c for c in range(1, 4000) if c not in tab][:60]
    keys = {}
    injective = True
    for c in sample:
        k = griess_key(plane_vector(c))
        if k in keys:
            injective = False
        keys[k] = c
    out["plane_vector_injective_on_sample"] = injective
    out["plane_vector_zero_only_at_zero"] = all(
        (plane_vector(c).is_zero()) == (c == 0) for c in sample)
    # the O(24) distance agrees with the honest one
    rng = random.Random(20260817)
    agree = True
    for _ in range(60):
        c1, c2 = rng.choice(sample), rng.choice(sample)
        fast = plane_distance2(c1, c2)
        slow = pseudo_distance2(plane_vector(c1), plane_vector(c2))
        if fast != slow:
            agree = False
            break
    out["fast_distance_agrees_with_the_algebra"] = agree

    if stacks:
        names = sorted(stacks)
        out["injectivity"] = injectivity_report(stacks)
        ok = True
        for _ in range(triples):
            a, b, c = (rng.choice(names), rng.choice(names),
                       rng.choice(names))
            dab = distance2_of_stacks(stacks[a], stacks[b])
            dbc = distance2_of_stacks(stacks[b], stacks[c])
            dac = distance2_of_stacks(stacks[a], stacks[c])
            if not triangle_holds(dab, dbc, dac):
                ok = False
                break
        out["triangle_inequality_on_triples"] = ok
        out["symmetric"] = all(
            distance2_of_stacks(stacks[a], stacks[b])
            == distance2_of_stacks(stacks[b], stacks[a])
            for a, b in [(rng.choice(names), rng.choice(names))
                         for _ in range(50)])
    if vectors:
        out["quotient"] = quotient_report(vectors)
        names = sorted(vectors)
        ok = True
        for _ in range(triples):
            a, b, c = (rng.choice(names), rng.choice(names),
                       rng.choice(names))
            if not triangle_holds(pseudo_distance2(vectors[a], vectors[b]),
                                  pseudo_distance2(vectors[b], vectors[c]),
                                  pseudo_distance2(vectors[a], vectors[c])):
                ok = False
                break
        out["pseudometric_triangle_inequality"] = ok
    return out


def _register() -> Tuple[Dict[str, List[int]], Dict[str, GR.GriessVector]]:
    """The register's stacks and collapsed Griess vectors (lazy import)."""
    from glm3_reasoner import REASONER as R
    stacks: Dict[str, List[int]] = {}
    vectors: Dict[str, GR.GriessVector] = {}
    for n in R.list_concepts():
        try:
            stacks[n] = R.stack(n)
        except Exception:
            continue
        vectors[n] = R.griess_vector(n)
    return stacks, vectors


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] == "nearest":
        stacks, _ = _register()
        name = argv[1] if len(argv) > 1 else "energy"
        print(banner(f"GLM-3 METRIC — nearest to {name}"))
        for n, d2 in nearest(name, stacks, 10):
            print(f"  {n:32s} d = {sqrt_approx(d2)}   d^2 = {d2}")
        return 0
    if argv and argv[0] == "cluster":
        stacks, _ = _register()
        threshold = F(argv[1]) if len(argv) > 1 else F(1, 4)
        groups = cluster(stacks, threshold)
        print(banner(f"GLM-3 METRIC — single linkage at {threshold}"))
        print(f"  {len(groups)} clusters over {len(stacks)} concepts")
        for g in groups[:10]:
            print(f"  {len(g):4d}  {', '.join(g[:6])}"
                  f"{' ...' if len(g) > 6 else ''}")
        return 0

    print(banner("GLM-3 METRIC — self-audit"))
    stacks, vectors = _register()
    report = metric_audit(stacks, vectors)
    pd = report["positive_definite"]
    print(f"  the form is a sum of squares          {pd['sum_of_squares']}")
    print(f"  both coefficients positive            "
          f"{pd['both_coefficients_positive']}")
    print(f"  positive definiteness checks          {pd['all_ok']}")
    print(f"  v is injective on the sample          "
          f"{report['plane_vector_injective_on_sample']}")
    print(f"  the O(24) distance is the algebra's   "
          f"{report['fast_distance_agrees_with_the_algebra']}")
    q = report["quotient"]
    print(f"  concepts / distinct Griess vectors    "
          f"{q['concepts']} / {q['classes']}")
    print(f"  concepts with no axis at all          {q['no_axis_at_all']}")
    print(f"  the quotient distance separates       "
          f"{q['distance_separates_classes']}")
    inj = report["injectivity"]
    print(f"  the graded metric separates           "
          f"{inj['is_a_metric_on_the_register']}")
    print(f"  triangle inequality (graded)          "
          f"{report['triangle_inequality_on_triples']}")
    print(f"  triangle inequality (collapsed)       "
          f"{report['pseudometric_triangle_inequality']}")
    sep = separation_report(stacks)
    print(f"  closest pair                          "
          f"{sep['closest_pair']}  d = {sep['closest_distance']}")
    print(f"  farthest pair                         "
          f"{sep['farthest_pair']}  d = {sep['farthest_distance']}")
    ok = (pd["all_ok"] and report["plane_vector_injective_on_sample"]
          and report["fast_distance_agrees_with_the_algebra"]
          and inj["is_a_metric_on_the_register"]
          and report["triangle_inequality_on_triples"]
          and report["pseudometric_triangle_inequality"])
    print(f"\n  {'OK' if ok else 'FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
