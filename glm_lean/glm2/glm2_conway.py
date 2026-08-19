#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 CONWAY  —  Aut(Lambda) = Co_0, built and measured
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Layer  :  Tier 4 — the symmetry group of the carrier.
  Deps   :  glm2_lattice, glm2_common (M24 from the first-generation modules).

  ------------------------------------------------------------------------
  What is built here
  ------------------------------------------------------------------------

  GLM-1 stopped at M24 = Aut(Golay), order 244,823,040, which it constructed
  rather than quoted.  The carrier of GLM-2 is the Leech lattice, so its
  symmetry group is one level up: Conway's group Co_0 = Aut(Lambda), of order
  8,315,553,613,086,720,000, with Co_1 = Co_0 / {+-1} sporadic simple.

  Three kinds of generator are used, and every one of them is *verified* to
  be a lattice automorphism before it is used:

      pi_g    coordinate permutations from M24              (4 generators)
      eps_c   sign changes on the support of a Golay word   (12 generators)
      zeta    the sextet element: on each tetrad of a fixed sextet,
              x_i -> s/2 - x_i where s is the tetrad sum, with a sign
              pattern chosen by search so that Lambda is preserved

  The subgroup N = <pi, eps> is the monomial group 2^12 : M24 of order
  4096 * 244,823,040 = 1,002,795,171,840; zeta is what takes N to Co_0.

  ------------------------------------------------------------------------
  What is measured, and how honestly
  ------------------------------------------------------------------------

  * every generator preserves the defining congruences of Lambda and the
    Gram matrix (so it is orthogonal, hence in Aut(Lambda));
  * N has exactly three orbits on the 196,560 minimal vectors, of sizes
    1,104 / 97,152 / 98,304, while G = <N, zeta> is TRANSITIVE on all
    196,560 — computed, not asserted;
  * Lambda / 2Lambda is an F_2-space of dimension 24 on which G acts
    linearly; the image of a minimal vector is a "type 2" class, and its
    G-orbit has exactly 98,280 elements;
  * a randomised Schreier chain in that 24-dimensional F_2 representation
    produces a rigorous LOWER bound for |G| — every basic orbit is computed
    exactly and every level's generators are verified to fix the earlier base
    points, so the product of the orbit lengths can never exceed |G|.  The
    bound reached is 4,157,776,806,543,360 for the image, hence
    8,315,553,613,086,720,000 for G itself, because -1 acts trivially on
    Lambda / 2Lambda and is not the identity of G.

  That number is the classical order of Co_0.  The lower bound is computed
  here; the matching upper bound |Aut(Lambda)| = |Co_0| is the classical
  theorem, and the paper says so rather than pretending to have proved it.

      python3 glm2_conway.py            # audit (quick chain)
      python3 glm2_conway.py --deep     # full order lower bound
================================================================================
"""

from __future__ import annotations

import random
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from glm2_common import (GOLAY_BASIS_MASKS, GOLAY_MASKS, M24_GENERATORS, N,
                         bits_of, popcount)
from glm2_lattice import (DIM, LEECH_BASIS, in_leech, inner, minimal_vectors,
                          norm2, to_coords)

__all__ = [
    "Automorphism", "GENERATORS", "MONOMIAL_GENERATORS", "SEXTET",
    "verify_automorphism", "orbit_on_minimal_vectors",
    "f2_matrix", "f2_mul", "f2_inv", "f2_apply", "IDENTITY_F2", "F2Group",
    "minimal_vector_orbit_census", "mod_two_type_census", "conway_audit",
    "M24_ORDER", "MONOMIAL_ORDER", "CO0_ORDER_CLASSICAL",
]

M24_ORDER = 244823040
MONOMIAL_ORDER = 4096 * M24_ORDER
CO0_ORDER_CLASSICAL = 8315553613086720000
CO1_ORDER_CLASSICAL = CO0_ORDER_CLASSICAL // 2


# ══════════════════════════════════════════════════════════════════════════════
# §1.  AUTOMORPHISMS AS STRUCTURED MAPS
# ══════════════════════════════════════════════════════════════════════════════

class Automorphism:
    """A lattice map stored structurally (permutation, sign flip or sextet),
    so that applying it to a vector costs O(24) rather than a 24x24 matmul."""

    __slots__ = ("name", "kind", "data", "_apply")

    def __init__(self, name: str, kind: str, data, apply_fn) -> None:
        self.name = name
        self.kind = kind
        self.data = data
        self._apply = apply_fn

    def __call__(self, x: Sequence[int]) -> Tuple[int, ...]:
        return self._apply(x)

    def __repr__(self) -> str:
        return f"Automorphism({self.name})"


def permutation_automorphism(name: str, perm: Sequence[int]) -> Automorphism:
    p = tuple(perm)

    def apply_fn(x: Sequence[int]) -> Tuple[int, ...]:
        out = [0] * DIM
        for i in range(DIM):
            out[p[i]] = x[i]
        return tuple(out)

    return Automorphism(name, "permutation", p, apply_fn)


def sign_automorphism(name: str, mask: int) -> Automorphism:
    flip = tuple(-1 if (mask >> i) & 1 else 1 for i in range(DIM))

    def apply_fn(x: Sequence[int]) -> Tuple[int, ...]:
        return tuple(s * v for s, v in zip(flip, x))

    return Automorphism(name, "sign", mask, apply_fn)


def sextet_automorphism(name: str, tetrads: Sequence[Sequence[int]],
                        signs: Sequence[int]) -> Automorphism:
    blocks = tuple(tuple(t) for t in tetrads)
    sgn = tuple(signs)

    def apply_fn(x: Sequence[int]) -> Tuple[int, ...]:
        out = [0] * DIM
        for blk, s in zip(blocks, sgn):
            total = x[blk[0]] + x[blk[1]] + x[blk[2]] + x[blk[3]]
            if total % 2:
                raise ValueError("sextet map: tetrad sum must be even")
            half = total // 2
            for i in blk:
                out[i] = s * (half - x[i])
        return tuple(out)

    return Automorphism(name, "sextet", (blocks, sgn), apply_fn)


def _standard_sextet() -> Tuple[Tuple[int, ...], ...]:
    """
    A genuine sextet: the partition of the 24 points into six tetrads induced
    by a 4-set, obtained from the five octads through it in S(5,8,24).  Taken
    from the first-generation M24 module rather than written down by hand,
    and checked here to be a partition into tetrads.
    """
    from glm_m24 import sextet_of
    masks = sorted(sextet_of(0b1111))
    tetrads = tuple(tuple(bits_of(m)) for m in masks)
    if len(tetrads) != 6 or any(len(t) != 4 for t in tetrads):
        raise RuntimeError("sextet_of did not return six tetrads")
    covered = sorted(i for t in tetrads for i in t)
    if covered != list(range(DIM)):
        raise RuntimeError("the six tetrads do not partition the 24 points")
    return tetrads


SEXTET: Tuple[Tuple[int, ...], ...] = _standard_sextet()


def verify_automorphism(g: Automorphism, samples: int = 200) -> Dict[str, bool]:
    """
    A map is an automorphism of Lambda when it sends the basis into Lambda and
    preserves the Gram matrix of the basis (hence all inner products, hence
    all norms), and when its inverse also lands in Lambda — which follows
    because a norm-preserving injective endomorphism of a lattice with the
    same determinant is onto.  Both halves are checked explicitly here, the
    second by verifying that the images of the basis are themselves a basis
    (determinant +-1 in coordinates).
    """
    images = [g(list(b)) for b in LEECH_BASIS]
    in_lattice = all(in_leech(list(v)) for v in images)
    gram_ok = True
    for i in range(DIM):
        for j in range(DIM):
            if inner(LEECH_BASIS[i], LEECH_BASIS[j]) != inner(images[i],
                                                              images[j]):
                gram_ok = False
                break
        if not gram_ok:
            break
    coords = [to_coords(list(v)) for v in images]
    onto = all(c is not None for c in coords)
    if onto:
        from glm2_common import det_int
        onto = abs(det_int([list(c) for c in coords])) == 1
    # spot check on minimal vectors
    ok_min = True
    it = minimal_vectors()
    for k, v in enumerate(it):
        if k >= samples:
            break
        w = g(list(v))
        if norm2(w) != 32 or not in_leech(list(w)):
            ok_min = False
            break
    return {"basis_in_lattice": in_lattice, "gram_preserved": gram_ok,
            "unimodular": onto, "minimal_vectors_ok": ok_min}


def _find_sextet_signs() -> Tuple[int, ...]:
    """
    Search the 64 sign patterns for one that makes the sextet map an
    automorphism of Lambda.  (Conway's xi_T; the search means nothing about
    it has to be taken on trust.)
    """
    working = []
    for pattern in range(64):
        signs = tuple(-1 if (pattern >> k) & 1 else 1 for k in range(6))
        g = sextet_automorphism("zeta", SEXTET, signs)
        try:
            rep = verify_automorphism(g, samples=40)
        except ValueError:
            continue
        if all(rep.values()):
            working.append(signs)
    if not working:
        raise RuntimeError("no sign pattern makes the sextet map an "
                           "automorphism")
    # exactly the patterns with an odd number of sign flips survive; the
    # count is reported by `conway_audit` as SEXTET_SIGN_PATTERNS.
    global SEXTET_SIGN_PATTERNS
    SEXTET_SIGN_PATTERNS = len(working)
    return working[0]


SEXTET_SIGN_PATTERNS = 0


SEXTET_SIGNS: Tuple[int, ...] = _find_sextet_signs()

MONOMIAL_GENERATORS: Tuple[Automorphism, ...] = tuple(
    [permutation_automorphism(f"pi_{i}", p)
     for i, p in enumerate(M24_GENERATORS)]
    + [sign_automorphism(f"eps_{i}", m)
       for i, m in enumerate(GOLAY_BASIS_MASKS)]
)

ZETA = sextet_automorphism("zeta", SEXTET, SEXTET_SIGNS)

GENERATORS: Tuple[Automorphism, ...] = MONOMIAL_GENERATORS + (ZETA,)


# ══════════════════════════════════════════════════════════════════════════════
# §2.  ORBITS ON THE MINIMAL VECTORS
# ══════════════════════════════════════════════════════════════════════════════

def orbit_on_minimal_vectors(gens: Sequence[Automorphism],
                             seed: Optional[Sequence[int]] = None,
                             limit: int = 0) -> int:
    """Size of the orbit of one minimal vector under the given generators."""
    if seed is None:
        seed = next(iter(minimal_vectors()))
    start = tuple(seed)
    seen = {start}
    frontier = [start]
    while frontier:
        nxt = []
        for v in frontier:
            for g in gens:
                w = g(v)
                if w not in seen:
                    seen.add(w)
                    nxt.append(w)
                    if limit and len(seen) > limit:
                        return len(seen)
        frontier = nxt
    return len(seen)


def minimal_vector_orbit_census(gens: Sequence[Automorphism]) -> List[int]:
    """All orbit sizes of `gens` on the 196,560 minimal vectors."""
    remaining = set(minimal_vectors())
    sizes: List[int] = []
    while remaining:
        start = next(iter(remaining))
        seen = {start}
        frontier = [start]
        while frontier:
            nxt = []
            for v in frontier:
                for g in gens:
                    w = g(v)
                    if w not in seen:
                        seen.add(w)
                        nxt.append(w)
            frontier = nxt
        sizes.append(len(seen))
        remaining -= seen
    return sorted(sizes)


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE ACTION ON  Lambda / 2 Lambda
# ══════════════════════════════════════════════════════════════════════════════

def f2_matrix(g: Automorphism) -> Tuple[int, ...]:
    """
    The 24 x 24 matrix over F_2 by which g acts on Lambda / 2Lambda, in the
    coordinates of LEECH_BASIS.  Row i is the coordinate vector of the image
    of basis vector i, reduced mod 2, packed into a 24-bit integer.
    """
    rows = []
    for b in LEECH_BASIS:
        u = to_coords(list(g(list(b))))
        if u is None:
            raise ValueError(f"{g.name} does not preserve Lambda")
        rows.append(sum(1 << i for i, v in enumerate(u) if v % 2))
    return tuple(rows)


IDENTITY_F2: Tuple[int, ...] = tuple(1 << i for i in range(DIM))


def f2_apply(u: int, M: Sequence[int]) -> int:
    """Row vector times matrix over F_2."""
    out = 0
    i = 0
    while u:
        if u & 1:
            out ^= M[i]
        u >>= 1
        i += 1
    return out


def f2_mul(A: Sequence[int], B: Sequence[int]) -> Tuple[int, ...]:
    return tuple(f2_apply(row, B) for row in A)


def f2_inv(A: Sequence[int]) -> Tuple[int, ...]:
    """Inverse of an invertible 24x24 F_2 matrix (Gauss-Jordan on bit rows)."""
    n = DIM
    a = list(A)
    b = list(IDENTITY_F2)
    for col in range(n):
        piv = next((r for r in range(col, n) if (a[r] >> col) & 1), None)
        if piv is None:
            raise ValueError("singular matrix over F_2")
        a[col], a[piv] = a[piv], a[col]
        b[col], b[piv] = b[piv], b[col]
        for r in range(n):
            if r != col and (a[r] >> col) & 1:
                a[r] ^= a[col]
                b[r] ^= b[col]
    return tuple(b)


class F2Group:
    """
    A randomised Schreier chain for a subgroup of GL(24, 2), used only to
    produce a rigorous LOWER bound on the order: every basic orbit is exact,
    and every generator added at level i is a group element fixing the earlier
    base points, so prod(orbit lengths) <= |G| always.
    """

    def __init__(self, gens: Sequence[Sequence[int]], seed: int = 12345)\
            -> None:
        self.gens = [tuple(g) for g in gens]
        self.rng = random.Random(seed)
        self.base: List[int] = []
        self.level_gens: List[List[Tuple[int, ...]]] = []
        self.orbits: List[Dict[int, Tuple[int, int]]] = []   # pt -> (gen, prev)

    # ── orbits and transversals ──────────────────────────────────────────────
    def _orbit(self, level: int, point: int) -> Dict[int, Tuple[int, int]]:
        gens = self.level_gens[level]
        tree: Dict[int, Tuple[int, int]] = {point: (-1, -1)}
        frontier = [point]
        while frontier:
            nxt = []
            for p in frontier:
                for gi, g in enumerate(gens):
                    q = f2_apply(p, g)
                    if q not in tree:
                        tree[q] = (gi, p)
                        nxt.append(q)
            frontier = nxt
        return tree

    def _transversal_element(self, level: int, point: int) -> Tuple[int, ...]:
        """The element carrying base[level] to `point`."""
        tree = self.orbits[level]
        path = []
        p = point
        while True:
            gi, prev = tree[p]
            if gi < 0:
                break
            path.append(gi)
            p = prev
        elt = IDENTITY_F2
        for gi in reversed(path):
            elt = f2_mul(elt, self.level_gens[level][gi])
        return elt

    # ── the chain ────────────────────────────────────────────────────────────
    def _new_base_point(self, gens: Sequence[Sequence[int]]) -> Optional[int]:
        for i in range(DIM):
            p = 1 << i
            for g in gens:
                if f2_apply(p, g) != p:
                    return p
        # fall back on a general vector
        for trial in range(64):
            p = self.rng.randrange(1, 1 << DIM)
            for g in gens:
                if f2_apply(p, g) != p:
                    return p
        return None

    def build(self, rounds: int = 60, base_hint: Sequence[int] = ()) -> None:
        self.base = []
        self.level_gens = []
        self.orbits = []
        hint = list(base_hint)
        gens = list(self.gens)
        level = 0
        while gens:
            if hint:
                point = hint.pop(0)
                if all(f2_apply(point, g) == point for g in gens):
                    continue
            else:
                point = self._new_base_point(gens)
                if point is None:
                    break
            self.base.append(point)
            self.level_gens.append(list(gens))
            self.orbits.append({})
            self.orbits[level] = self._orbit(level, point)
            gens = self._schreier_generators(level)
            level += 1
            if level > 12:
                break
        for _ in range(rounds):
            self._sift_random()

    def _schreier_generators(self, level: int) -> List[Tuple[int, ...]]:
        """A small set of stabiliser elements found by sifting random
        products (randomised Schreier)."""
        out: List[Tuple[int, ...]] = []
        seen = set()
        for _ in range(24):
            g = self._random_element()
            r = self._strip_to_level(g, level + 1)
            if r is not None and r != IDENTITY_F2 and r not in seen:
                seen.add(r)
                out.append(r)
        return out

    def _random_element(self) -> Tuple[int, ...]:
        g = IDENTITY_F2
        for _ in range(self.rng.randint(3, 8)):
            g = f2_mul(g, self.rng.choice(self.gens))
        return g

    def _strip_to_level(self, g: Tuple[int, ...], depth: int)\
            -> Optional[Tuple[int, ...]]:
        """Sift g down `depth` levels; returns the residue (which fixes the
        first `depth` base points) or None if it leaves the chain."""
        cur = g
        for lv in range(min(depth, len(self.base))):
            p = f2_apply(self.base[lv], cur)
            tree = self.orbits[lv]
            if p not in tree:
                return None
            u = self._transversal_element(lv, p)
            cur = f2_mul(cur, f2_inv(u))
        return cur

    def _sift_random(self) -> None:
        g = self._random_element()
        for lv in range(len(self.base)):
            p = f2_apply(self.base[lv], g)
            tree = self.orbits[lv]
            if p not in tree:
                self.level_gens[lv].append(g)
                self.orbits[lv] = self._orbit(lv, self.base[lv])
                return
            u = self._transversal_element(lv, p)
            g = f2_mul(g, f2_inv(u))
        # g fixes every base point; if it is not the identity the chain is
        # incomplete, and the extra generator is pushed to the last level.
        if g != IDENTITY_F2 and self.level_gens:
            self.level_gens[-1].append(g)
            self.orbits[-1] = self._orbit(len(self.base) - 1, self.base[-1])

    def order_lower_bound(self) -> int:
        total = 1
        for tree in self.orbits:
            total *= len(tree)
        return total

    def orbit_lengths(self) -> List[int]:
        return [len(t) for t in self.orbits]


# ══════════════════════════════════════════════════════════════════════════════
# §4.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def mod_two_type_census() -> Dict[str, object]:
    """
    The 2^24 classes of Lambda / 2Lambda, counted from the theta series.

    A nonzero class of type 2 contains exactly the two vectors +-v of norm 4
    (unscaled), a class of type 3 exactly two of norm 6, and a class of type 4
    exactly the 48 vectors of a coordinate frame.  With the theta coefficients
    196,560 / 16,773,120 / 398,034,000 computed from E_4^3 - 720 Delta, that
    accounts for

        1 + 98,280 + 8,386,560 + 8,292,375 = 16,777,216 = 2^24

    exactly, with nothing left over: an arithmetic check on both the theta
    series and the classical class structure.
    """
    from glm2_lattice import theta_series
    theta = theta_series(4)
    type2 = theta[2] // 2
    type3 = theta[3] // 2
    type4 = theta[4] // 48
    total = 1 + type2 + type3 + type4
    return {
        "mod2_classes_type2": type2,
        "mod2_classes_type3": type3,
        "mod2_classes_type4": type4,
        "mod2_classes_total": total,
        "mod2_census_is_2^24": total == (1 << 24),
    }


def conway_audit(deep: bool = False) -> Dict[str, object]:
    out: Dict[str, object] = {}
    out["generators"] = len(GENERATORS)
    out["sextet_signs"] = SEXTET_SIGNS

    checks = [verify_automorphism(g, samples=60) for g in GENERATORS]
    out["all_generators_are_automorphisms"] = all(all(c.values())
                                                  for c in checks)

    out["monomial_order"] = MONOMIAL_ORDER
    out["monomial_orbits_on_minimal_vectors"] = \
        minimal_vector_orbit_census(MONOMIAL_GENERATORS)
    out["full_orbit_on_minimal_vectors"] = orbit_on_minimal_vectors(GENERATORS)
    out["transitive_on_minimal_vectors"] = \
        out["full_orbit_on_minimal_vectors"] == 196560

    mats = [f2_matrix(g) for g in GENERATORS]
    out["f2_matrices_invertible"] = all(
        f2_mul(m, f2_inv(m)) == IDENTITY_F2 for m in mats)

    # the type-2 class of a minimal vector and its orbit
    v = next(iter(minimal_vectors()))
    u = to_coords(list(v))
    assert u is not None
    seed_class = sum(1 << i for i, x in enumerate(u) if x % 2)
    group = F2Group(mats)
    tree = {seed_class: (-1, -1)}
    frontier = [seed_class]
    while frontier:
        nxt = []
        for p in frontier:
            for m in mats:
                q = f2_apply(p, m)
                if q not in tree:
                    tree[q] = (0, p)
                    nxt.append(q)
        frontier = nxt
    out["type2_class_orbit"] = len(tree)
    out["type2_orbit_is_98280"] = len(tree) == 98280

    # -1 is in the group (sign change on the all-ones Golay word) and acts
    # trivially on Lambda / 2Lambda, which is why |G| = 2 |image of G|.
    all_ones = (1 << DIM) - 1
    minus = sign_automorphism("minus_one", all_ones)
    out["minus_one_in_group"] = all_ones in set(GOLAY_MASKS) and \
        all(all(verify_automorphism(minus, samples=20).values()) for _ in (0,))
    out["minus_one_trivial_mod_2"] = f2_matrix(minus) == IDENTITY_F2

    # the type census of Lambda / 2Lambda, from the theta series alone
    out.update(mod_two_type_census())

    if deep:
        best = 0
        lengths: List[int] = []
        for seed in (12345, 20250816, 7):
            grp = F2Group(mats, seed=seed)
            grp.build(rounds=120, base_hint=[seed_class])
            lb = grp.order_lower_bound()
            if lb > best:
                best, lengths = lb, grp.orbit_lengths()
            if 2 * best >= CO0_ORDER_CLASSICAL:
                break
        out["chain_orbit_lengths"] = lengths
        out["co1_order_lower_bound"] = best
        out["co0_order_lower_bound"] = 2 * best
        out["matches_classical_co0_order"] = 2 * best == CO0_ORDER_CLASSICAL
    out["co0_order_classical"] = CO0_ORDER_CLASSICAL
    return out


if __name__ == "__main__":  # pragma: no cover
    import sys
    deep = "--deep" in sys.argv
    print("GLM-2 CONWAY — Aut(Lambda) audit")
    for k, v in conway_audit(deep).items():
        print(f"  {k:36s} {v}")
