"""
glm_m24.py — the Mathieu group M_24, constructed rather than invoked
====================================================================

The archive's upper-tier files (v10 onwards) all *name* `M_24`: they build a
"permutation engine", check that a handful of permutations preserve the Golay
code, and then speak of the group as if it had been produced.  It never was.
This module produces it, from our own code and with nothing assumed:

  §1  permutations of the 24 coordinates, as tuples;

  §2  the column matroid of the code.  Fix a basis `b_1..b_12` of the Golay
      code `C` and let `col(j)` in `F_2^12` be the column `(b_i[j])_i`.  A
      subset `S` of coordinates carries a linear dependency of columns exactly
      when `S` is the support of a codeword, because `C` is self-dual.  Hence a
      coordinate permutation preserves `C` if and only if it preserves every
      dependency among the columns — which is what the search below tests,
      incrementally, by simultaneous echelon reduction of the domain and image
      columns.  Twelve `F_2^12` words replace 4096 membership tests.

  §3  the automorphism search: all coordinate permutations preserving `C`,
      optionally with prescribed values.  Ordering is dynamic: at each node the
      next coordinate chosen is one whose column has become dependent on those
      already assigned, so that its image is forced; failing that, one lying in
      the octad with the most assigned points.

  §4  a stabiliser chain (Schreier–Sims) for a group of permutations: base,
      transversals, order, and membership testing.  Exact, deterministic.

  §5  the report.  Four automorphisms found by §3 generate a group `G` whose
      stabiliser chain has base `b_1..b_5` with orbit lengths
      `24, 23, 22, 21, 20` — so `G` is 5-transitive — and whose pointwise
      stabiliser of `b_1..b_5` has order 48, giving

          |G| = 24 x 23 x 22 x 21 x 20 x 48 = 244,823,040.

      Separately, §3 enumerates *exhaustively* every automorphism of `C` fixing
      those five coordinates: there are exactly 48 of them, the ones already in
      `G`.  Since the `G`-orbit of the ordered 5-tuple is already every ordered
      5-tuple, orbit–stabiliser gives

          |Aut(C)| = 24 x 23 x 22 x 21 x 20 x 48 = |G|,

      so `G = Aut(C) = M_24`, computed rather than quoted.  The group is also
      transitive on the 759 octads, the 2576 dodecads and the 1771 sextets, so
      orbit-stabiliser reads off the orders of the three classical maximal
      subgroups without constructing any of them by hand: `2^4 : A_8`
      (322,560), `M_12` (95,040) and `2^6 : 3.S_6` (138,240).

Exact integer arithmetic only; standard library only.  Runs standalone:

    python3 glm_m24.py            # full audit (~1 s)
    python3 glm_m24.py --quick    # skips the exhaustive stabiliser enumeration
"""

from __future__ import annotations

import sys
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from glm_substrate import GOLAY

__all__ = [
    "N_COORDS",
    "Perm",
    "compose",
    "inverse",
    "identity_perm",
    "permute_word",
    "preserves_code",
    "code_automorphisms",
    "StabChain",
    "schreier_sims",
    "M24_GENERATORS",
    "m24_report",
    "subgroup_census",
    "sextet_of",
]

N_COORDS = 24

Perm = Tuple[int, ...]


# ---------------------------------------------------------------------------
# §1.  PERMUTATIONS
# ---------------------------------------------------------------------------


def identity_perm(n: int = N_COORDS) -> Perm:
    return tuple(range(n))


def compose(p: Perm, q: Perm) -> Perm:
    """`compose(p, q)` applies `p` first, then `q`."""
    return tuple(q[x] for x in p)


def inverse(p: Perm) -> Perm:
    out = [0] * len(p)
    for i, x in enumerate(p):
        out[x] = i
    return tuple(out)


def cycles(p: Perm) -> List[List[int]]:
    seen = [False] * len(p)
    out: List[List[int]] = []
    for i in range(len(p)):
        if seen[i] or p[i] == i:
            seen[i] = True
            continue
        cyc = []
        j = i
        while not seen[j]:
            seen[j] = True
            cyc.append(j)
            j = p[j]
        out.append(cyc)
    return out


def permute_word(word: Sequence[int], p: Perm) -> Tuple[int, ...]:
    """Move the bit at coordinate `i` to coordinate `p[i]`."""
    out = [0] * len(word)
    for i, x in enumerate(word):
        out[p[i]] = x
    return tuple(out)


# ---------------------------------------------------------------------------
# §2.  THE COLUMN MATROID OF THE GOLAY CODE
# ---------------------------------------------------------------------------

_CODE: List[Tuple[int, ...]] = [tuple(v) for v in GOLAY.all_codewords()]
_CODESET = set(_CODE)
_OCTAD_MASKS: List[int] = [
    sum(1 << j for j in range(N_COORDS) if c[j]) for c in _CODE if sum(c) == 8
]


def _code_basis() -> List[int]:
    """A basis of the code, as 24-bit integers, by Gaussian elimination."""
    basis: List[int] = []
    pivots: List[int] = []
    for c in _CODE:
        y = sum(1 << j for j in range(N_COORDS) if c[j])
        for p, b in zip(pivots, basis):
            if (y >> p) & 1:
                y ^= b
        if y:
            pivots.append(y.bit_length() - 1)
            basis.append(y)
    return basis


_BASIS = _code_basis()
assert len(_BASIS) == 12, "the Golay code must have dimension 12"

#: `_COLUMN[j]` is the `j`-th column of the generator matrix, as a 12-bit word.
_COLUMN: List[int] = [
    sum(((_BASIS[i] >> j) & 1) << i for i in range(12)) for j in range(N_COORDS)
]


def preserves_code(p: Perm) -> bool:
    """Exhaustive check: does `p` map every one of the 4096 codewords to a
    codeword?  Used to confirm the search's output independently of the
    matroid argument it relies on."""
    return all(permute_word(c, p) in _CODESET for c in _CODE)


def _popcount(x: int) -> int:
    return bin(x).count("1")


# ---------------------------------------------------------------------------
# §3.  THE AUTOMORPHISM SEARCH
# ---------------------------------------------------------------------------


def code_automorphisms(
    fixed: Optional[Dict[int, int]] = None,
    first_only: bool = False,
    limit: Optional[int] = None,
) -> List[Perm]:
    """Every coordinate permutation preserving the Golay code and agreeing
    with `fixed` (a partial map coordinate -> image).

    With `first_only=True` the search stops at the first solution; with
    `limit=k` it stops after `k`.  With no constraints the full group is far
    too large to enumerate, so callers should always constrain or limit.
    """
    fixed = dict(fixed or {})
    results: List[Perm] = []
    pivots: List[Tuple[int, int, int]] = []   # (pivot bit, domain word, image word)
    assigned: Dict[int, int] = {}
    used = set()
    prescribed = list(fixed.keys())

    def reduce_pair(a: int, b: int) -> Tuple[int, int]:
        for pb, da, ib in pivots:
            if (a >> pb) & 1:
                a ^= da
                b ^= ib
        return a, b

    def pick_next() -> int:
        amask = 0
        for d in assigned:
            amask |= 1 << d
        best_forced = -1
        for d in range(N_COORDS):
            if d in assigned:
                continue
            a, _ = reduce_pair(_COLUMN[d], 0)
            if a == 0:
                return d          # image is forced: branch factor 1
            if best_forced < 0:
                best_forced = d
        # otherwise: a coordinate in the octad with the most assigned points
        best_d, best_score = best_forced, -1
        for m in _OCTAD_MASKS:
            score = _popcount(m & amask)
            if score > best_score and (m & ~amask):
                rest = m & ~amask
                best_score = score
                best_d = (rest & -rest).bit_length() - 1
                if score == 7:
                    break
        return best_d

    def rec(depth: int) -> bool:
        if limit is not None and len(results) >= limit:
            return True
        if depth == N_COORDS:
            out = [0] * N_COORDS
            for d, v in assigned.items():
                out[d] = v
            results.append(tuple(out))
            return first_only
        d = prescribed[depth] if depth < len(prescribed) else pick_next()
        candidates: Iterable[int] = [fixed[d]] if d in fixed else range(N_COORDS)
        for v in candidates:
            if v in used:
                continue
            a, b = reduce_pair(_COLUMN[d], _COLUMN[v])
            if a == 0:
                if b != 0:
                    continue
                added = False
            else:
                if b == 0:
                    continue
                pivots.append((a.bit_length() - 1, a, b))
                added = True
            assigned[d] = v
            used.add(v)
            stop = rec(depth + 1)
            del assigned[d]
            used.discard(v)
            if added:
                pivots.pop()
            if stop:
                return True
        return False

    rec(0)
    return results


# ---------------------------------------------------------------------------
# §4.  STABILISER CHAINS (SCHREIER–SIMS)
# ---------------------------------------------------------------------------


def _orbit_transversal(gens: Sequence[Perm], b: int, n: int) -> Dict[int, Perm]:
    transversal = {b: identity_perm(n)}
    frontier = [b]
    while frontier:
        nxt = []
        for pt in frontier:
            g0 = transversal[pt]
            for g in gens:
                img = g[pt]
                if img not in transversal:
                    transversal[img] = compose(g0, g)
                    nxt.append(img)
        frontier = nxt
    return transversal


class StabChain:
    """A base and strong generating set for a permutation group."""

    def __init__(self, n: int = N_COORDS) -> None:
        self.n = n
        self.base: List[int] = []
        self.gens: List[List[Perm]] = []
        self.transversals: List[Dict[int, Perm]] = []

    # -- construction ------------------------------------------------------
    def add_base_point(self, b: int) -> None:
        self.base.append(b)
        self.gens.append([])
        self.transversals.append({b: identity_perm(self.n)})

    def recompute(self, level: int) -> None:
        self.transversals[level] = _orbit_transversal(
            self.gens[level], self.base[level], self.n
        )

    # -- queries -----------------------------------------------------------
    def strip(self, g: Perm, level: int = 0) -> Tuple[Perm, int]:
        h = g
        for i in range(level, len(self.base)):
            t = self.transversals[i].get(h[self.base[i]])
            if t is None:
                return h, i
            h = compose(h, inverse(t))
        return h, len(self.base)

    def contains(self, g: Perm) -> bool:
        h, level = self.strip(g)
        return level == len(self.base) and h == identity_perm(self.n)

    def order(self) -> int:
        out = 1
        for t in self.transversals:
            out *= len(t)
        return out

    def orbit_lengths(self) -> List[int]:
        return [len(t) for t in self.transversals]

    def stabiliser_order(self, level: int) -> int:
        """Order of the pointwise stabiliser of `base[:level]`."""
        out = 1
        for t in self.transversals[level:]:
            out *= len(t)
        return out


def schreier_sims(
    gens: Sequence[Perm], n: int = N_COORDS, base_hint: Sequence[int] = ()
) -> StabChain:
    """Deterministic Schreier–Sims: exact order and membership test."""
    chain = StabChain(n)
    ident = identity_perm(n)
    for b in base_hint:
        chain.add_base_point(b)

    def add_generator(g: Perm) -> None:
        h, j = chain.strip(g)
        if h == ident:
            return
        if j == len(chain.base):
            chain.add_base_point(next(x for x in range(n) if h[x] != x))
        for level in range(0, j + 1):
            if level < len(chain.base):
                chain.gens[level].append(h)
        for level in range(0, min(j + 1, len(chain.base))):
            chain.recompute(level)

    for g in gens:
        if g != ident:
            add_generator(g)

    i = len(chain.base) - 1
    while i >= 0:
        restart = False
        for pt, tpt in list(chain.transversals[i].items()):
            for s in list(chain.gens[i]):
                sg = compose(tpt, s)
                t_img = chain.transversals[i].get(sg[chain.base[i]])
                if t_img is None:
                    raise RuntimeError("incomplete transversal")
                sg = compose(sg, inverse(t_img))
                if sg == ident:
                    continue
                h, j = chain.strip(sg, i + 1)
                if h != ident:
                    if j == len(chain.base):
                        chain.add_base_point(next(x for x in range(n) if h[x] != x))
                    for level in range(i + 1, j + 1):
                        chain.gens[level].append(h)
                        chain.recompute(level)
                    i = j
                    restart = True
                    break
            if restart:
                break
        if not restart:
            i -= 1
    return chain


# ---------------------------------------------------------------------------
# §5.  M_24
# ---------------------------------------------------------------------------

#: Four automorphisms of *this* Golay code, found by §3 (regenerate them with
#: `find_generators()`; they are cached so that the audit does not have to
#: search every time, and `verify_generators()` checks them exhaustively).
M24_GENERATORS: Tuple[Perm, ...] = (
    (1, 2, 3, 4, 5, 23, 14, 19, 21, 11, 16, 8, 0, 13, 22, 10, 6, 7, 9, 17, 12, 18, 20, 15),
    (5, 0, 7, 9, 11, 6, 2, 10, 12, 13, 23, 18, 1, 3, 21, 4, 14, 16, 19, 15, 8, 20, 22, 17),
    (23, 22, 0, 3, 6, 10, 13, 2, 15, 9, 8, 12, 1, 11, 7, 17, 14, 18, 19, 5, 16, 21, 4, 20),
    (12, 4, 17, 1, 20, 14, 22, 16, 19, 9, 5, 18, 0, 11, 15, 7, 2, 10, 3, 6, 23, 21, 8, 13),
)

#: The five coordinates whose pointwise stabiliser is enumerated exhaustively.
BASE_POINTS: Tuple[int, ...] = (0, 1, 2, 3, 4)


def find_generators(
    targets: Sequence[Dict[int, int]] = (
        {0: 1, 1: 2, 2: 3, 3: 4, 4: 5},
        {0: 5, 1: 0, 2: 7, 3: 9, 4: 11},
        {0: 23, 1: 22, 2: 0, 3: 3, 4: 6},
        {0: 12, 1: 4, 2: 17, 3: 1, 4: 20},
    ),
) -> List[Perm]:
    """Re-derive the cached generators: for each prescribed image of five
    coordinates, the first automorphism the search finds."""
    out: List[Perm] = []
    for spec in targets:
        found = code_automorphisms(spec, first_only=True)
        if found:
            out.append(found[0])
    return out


def verify_generators(gens: Sequence[Perm] = M24_GENERATORS) -> bool:
    """Every cached generator really is a code automorphism (checked on all
    4096 codewords, not via the matroid shortcut)."""
    return all(preserves_code(g) for g in gens)


def _orbit_of_mask(gens: Sequence[Perm], start: int) -> int:
    """Size of the orbit of a coordinate subset (given as a bit mask)."""
    seen = {start}
    frontier = [start]
    while frontier:
        nxt = []
        for m in frontier:
            for g in gens:
                img = 0
                for j in range(N_COORDS):
                    if (m >> j) & 1:
                        img |= 1 << g[j]
                if img not in seen:
                    seen.add(img)
                    nxt.append(img)
        frontier = nxt
    return len(seen)


def sextet_of(tetrad: int) -> frozenset:
    """The sextet containing a 4-element subset: the six tetrads into which the
    24 points fall, obtained from the five octads through the given tetrad
    (a 4-set lies in exactly five octads of the Steiner system S(5,8,24))."""
    parts = {tetrad}
    for m in _OCTAD_MASKS:
        if m & tetrad == tetrad:
            parts.add(m & ~tetrad)
    return frozenset(parts)


def subgroup_census(gens: Sequence[Perm] = M24_GENERATORS) -> Dict[str, object]:
    """Orbits of the classical objects, and the stabiliser orders they force.

    Given `|G| = 244,823,040` from the stabiliser chain, orbit-stabiliser turns
    each measured orbit length into the order of a maximal subgroup: the octad
    stabiliser `2^4 : A_8` (322,560), the dodecad stabiliser `M_12` (95,040)
    and the sextet stabiliser `2^6 : 3.S_6` (138,240).
    """
    order = schreier_sims(list(gens), N_COORDS, base_hint=BASE_POINTS).order()
    octad = _OCTAD_MASKS[0]
    dodecads = [sum(1 << j for j in range(N_COORDS) if c[j])
                for c in _CODE if sum(c) == 12]
    tetrad = 0b1111
    sextet = sextet_of(tetrad)
    seen = {sextet}
    frontier = [sextet]
    while frontier:
        nxt = []
        for s in frontier:
            for g in gens:
                img = frozenset(
                    sum(1 << g[j] for j in range(N_COORDS) if (m >> j) & 1)
                    for m in s)
                if img not in seen:
                    seen.add(img)
                    nxt.append(img)
        frontier = nxt
    octad_orbit_len = _orbit_of_mask(gens, octad)
    dodecad_orbit_len = _orbit_of_mask(gens, dodecads[0])
    return {
        "group_order": order,
        "sextet_parts": len(sextet),
        "octads": len(_OCTAD_MASKS),
        "octad_orbit": octad_orbit_len,
        "octad_stabiliser_order": order // octad_orbit_len,
        "dodecads": len(dodecads),
        "dodecad_orbit": dodecad_orbit_len,
        "dodecad_stabiliser_order": order // dodecad_orbit_len,
        "sextet_orbit": len(seen),
        "sextet_stabiliser_order": order // len(seen),
        "matches_expected": (
            octad_orbit_len == 759 and order // octad_orbit_len == 322560
            and dodecad_orbit_len == 2576 and order // dodecad_orbit_len == 95040
            and len(seen) == 1771 and order // len(seen) == 138240),
    }


def octad_orbit(chain_gens: Sequence[Perm]) -> Tuple[int, int]:
    """(orbit length of one octad, number of octads).  Transitivity on octads
    is the classical `M_24` fact; here it is measured."""
    start = _OCTAD_MASKS[0]
    seen = {start}
    frontier = [start]
    while frontier:
        nxt = []
        for m in frontier:
            for g in chain_gens:
                img = 0
                for j in range(N_COORDS):
                    if (m >> j) & 1:
                        img |= 1 << g[j]
                if img not in seen:
                    seen.add(img)
                    nxt.append(img)
        frontier = nxt
    return len(seen), len(_OCTAD_MASKS)


def m24_report(quick: bool = False) -> Dict[str, object]:
    """Everything this module claims, as data."""
    gens = list(M24_GENERATORS)
    chain = schreier_sims(gens, N_COORDS, base_hint=BASE_POINTS)
    orbits = chain.orbit_lengths()
    orbit_len, n_octads = octad_orbit(gens)
    report: Dict[str, object] = {
        "generators_preserve_code": verify_generators(gens),
        "order": chain.order(),
        "order_expected": 244823040,
        "base": list(chain.base),
        "orbit_lengths": orbits,
        "five_transitive": orbits[:5] == [24, 23, 22, 21, 20],
        "point_stabiliser_chain_order": chain.stabiliser_order(5),
        "octad_orbit_length": orbit_len,
        "octad_count": n_octads,
        "octad_transitive": orbit_len == n_octads,
        "octad_stabiliser_order": chain.order() // orbit_len if orbit_len else 0,
        "subgroup_census": subgroup_census(gens),
        "exhaustive_stabiliser": None,
        "aut_order_from_orbit_stabiliser": None,
        "is_full_automorphism_group": None,
    }
    if not quick:
        stab = code_automorphisms({b: b for b in BASE_POINTS})
        report["exhaustive_stabiliser"] = len(stab)
        report["stabiliser_all_in_group"] = all(chain.contains(p) for p in stab)
        aut_order = 24 * 23 * 22 * 21 * 20 * len(stab)
        report["aut_order_from_orbit_stabiliser"] = aut_order
        report["is_full_automorphism_group"] = aut_order == chain.order()
    return report


def _self_audit(quick: bool = False) -> None:
    t0 = time.time()
    print("=" * 78)
    print("  glm_m24.py — the automorphism group of the Golay code, computed")
    print("=" * 78)
    rep = m24_report(quick=quick)
    print("  generators preserve all 4096 codewords : %s" % rep["generators_preserve_code"])
    print("  stabiliser chain base                  : %s" % rep["base"])
    print("  orbit lengths                          : %s" % rep["orbit_lengths"])
    print("  5-transitive                           : %s" % rep["five_transitive"])
    print("  |G|                                    : %s" % f"{rep['order']:,}")
    print("  |M_24|                                 : %s" % f"{rep['order_expected']:,}")
    print("  pointwise stabiliser of %s in the chain: %s"
          % (list(BASE_POINTS), rep["point_stabiliser_chain_order"]))
    print("  octad orbit / octads                   : %s / %s"
          % (rep["octad_orbit_length"], rep["octad_count"]))
    print("  octad stabiliser order                 : %s"
          % f"{rep['octad_stabiliser_order']:,}")
    census = rep["subgroup_census"]
    print("  dodecads / dodecad stabiliser          : %s / %s  (= |M_12|)"
          % (census["dodecads"], f"{census['dodecad_stabiliser_order']:,}"))
    print("  sextets  / sextet stabiliser           : %s / %s"
          % (census["sextet_orbit"], f"{census['sextet_stabiliser_order']:,}"))
    print("  census matches 2^4:A_8, M_12, 2^6:3.S_6: %s"
          % census["matches_expected"])
    if not quick:
        print("  exhaustive stabiliser of five points   : %s"
              % rep["exhaustive_stabiliser"])
        print("  all of them already in G               : %s"
              % rep["stabiliser_all_in_group"])
        print("  |Aut(C)| by orbit-stabiliser           : %s"
              % f"{rep['aut_order_from_orbit_stabiliser']:,}")
        print("  therefore G = Aut(C) = M_24            : %s"
              % rep["is_full_automorphism_group"])
    print("-" * 78)
    print("  audit completed in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    _self_audit(quick="--quick" in sys.argv)
