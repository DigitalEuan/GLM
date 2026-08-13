"""
exp7_cube_surface.py -- the cube surface AS the MOG grid, and the stabiliser test.

Coordinate identification (Experiment 1 of the brief):

    a surface cell of the cube = (corner, axis)
        corner  in {-1,+1}^3            (8 of them)
        axis    in {x, y, z}            (3 faces meet at each corner)
    8 x 3 = 24 cells = 6 faces x 4 cells = the 4x6 MOG grid.

    face   = (axis, sign of the corner along that axis)   -> MOG column
    cell   = the signs of the other two axes              -> MOG row (GF(4) label)

The cube's surface symmetry group is the signed permutation group B3 = S3 x C2^3,
order 48 (24 rotations + 24 reflections).  It acts on the 24 cells.

Experiment 1: for each of the 48 symmetries, does the induced permutation of the
24 MOG cells map the Golay code to itself?
Experiment 2: face-erasure -- how many faces of a codeword can be destroyed and
still be repaired.
Experiment 3: is there ANY relabelling of the cube surface (any Golay code placed
on the cube's cells) that the whole cube group preserves?  Searched by enumerating
G-invariant subspaces of F2^24 rather than by enumerating 24! labellings.
"""
from __future__ import annotations

import itertools
import json
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from glm_clean.hexacode import MOG_CODE, cell, hexacode, decompose

AXES = (0, 1, 2)
SIGNS = (+1, -1)
CORNERS = [c for c in itertools.product(SIGNS, repeat=3)]


# ---------------------------------------------------------------- identification
def face_index(axis: int, sign: int) -> int:
    """MOG column of the face normal to `axis` on the `sign` side."""
    return 2 * axis + (0 if sign > 0 else 1)


def row_index(axis: int, corner: Tuple[int, int, int]) -> int:
    """MOG row of the quadrant of the face, from the other two coordinate signs."""
    b1, b2 = (axis + 1) % 3, (axis + 2) % 3
    return 2 * (0 if corner[b1] > 0 else 1) + (0 if corner[b2] > 0 else 1)


def cell_index(corner: Tuple[int, int, int], axis: int) -> int:
    return cell(row_index(axis, corner), face_index(axis, corner[axis]))


def check_identification() -> Dict[str, object]:
    seen = {}
    for c in CORNERS:
        for a in AXES:
            i = cell_index(c, a)
            assert i not in seen, "identification is not injective"
            seen[i] = (c, a)
    return {"bijective": len(seen) == 24}


# ---------------------------------------------------------------- the cube group
def group_elements() -> List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]:
    """(sigma, eps): x -> eps * P_sigma x, with (P_sigma x)[sigma(i)] = x[i]."""
    out = []
    for sigma in itertools.permutations(AXES):
        for eps in itertools.product(SIGNS, repeat=3):
            out.append((sigma, eps))
    return out


def act_corner(g, p):
    sigma, eps = g
    q = [0, 0, 0]
    for i in AXES:
        q[sigma[i]] = eps[sigma[i]] * p[i]
    return tuple(q)


def is_rotation(g) -> bool:
    sigma, eps = g
    # sign of the permutation times the product of the signs
    perm_sign = 1
    for i in range(3):
        for j in range(i + 1, 3):
            if sigma[i] > sigma[j]:
                perm_sign = -perm_sign
    return perm_sign * eps[0] * eps[1] * eps[2] > 0


def cell_permutation(g) -> List[int]:
    """perm[i] = image of cell i."""
    sigma, _ = g
    perm = [0] * 24
    for c in CORNERS:
        for a in AXES:
            perm[cell_index(c, a)] = cell_index(act_corner(g, c), sigma[a])
    assert sorted(perm) == list(range(24))
    return perm


def apply_perm(perm: List[int], v: int) -> int:
    out = 0
    for i in range(24):
        if (v >> i) & 1:
            out |= 1 << perm[i]
    return out


def cycle_type(perm: List[int]) -> Tuple[int, ...]:
    seen = [False] * 24
    lens = []
    for i in range(24):
        if not seen[i]:
            n, j = 0, i
            while not seen[j]:
                seen[j] = True
                j = perm[j]
                n += 1
            lens.append(n)
    return tuple(sorted(lens))


# ---------------------------------------------------------------- Experiment 1
def experiment1() -> Dict[str, object]:
    words = MOG_CODE.wordset
    basis = MOG_CODE.basis
    preserved, broken = [], []
    detail = []
    for g in group_elements():
        perm = cell_permutation(g)
        ok = all(apply_perm(perm, b) in words for b in basis)
        rec = {
            "sigma": list(g[0]),
            "eps": list(g[1]),
            "rotation": is_rotation(g),
            "cycle_type": list(cycle_type(perm)),
            "preserves_code": ok,
        }
        detail.append(rec)
        (preserved if ok else broken).append(rec)
    return {
        "n_group": len(detail),
        "n_preserving": len(preserved),
        "n_preserving_rotations": sum(1 for r in preserved if r["rotation"]),
        "preserving": preserved,
        "cycle_types_present": sorted({tuple(r["cycle_type"]) for r in detail}),
        "detail": detail,
    }


# ---------------------------------------------------------------- Experiment 2
def popcount(x: int) -> int:
    return bin(x).count("1")


def face_mask(c: int) -> int:
    m = 0
    for r in range(4):
        m |= 1 << cell(r, c)
    return m


def experiment2() -> Dict[str, object]:
    """Face erasure: two codewords agreeing outside k faces."""
    words = sorted(MOG_CODE.wordset)
    res: Dict[str, object] = {}
    for k in (1, 2):
        bad = []
        for faces in itertools.combinations(range(6), k):
            mask = 0
            for c in faces:
                mask |= face_mask(c)
            # two codewords agree outside `faces` iff their sum is supported there
            amb = [w for w in words if w and (w & ~mask) == 0]
            if amb:
                bad.append({"faces": list(faces), "n_codewords_inside": len(amb),
                            "example_weight": popcount(amb[0])})
        res[f"{k}_face_ambiguities"] = bad
        res[f"{k}_face_always_correctable"] = (len(bad) == 0)
    # the two-full-columns word
    w = face_mask(0) | face_mask(1)
    res["two_columns_is_codeword"] = w in MOG_CODE.wordset
    res["two_columns_weight"] = popcount(w)
    # hexacode layer: single symbol correction
    H = hexacode()
    dmin = min(sum(1 for a, b in zip(x, y) if a != b) for x in H for y in H if x != y)
    res["hexacode_min_distance"] = dmin
    # a vector at distance 2 from two different hexacode words
    amb = None
    for x in itertools.product(range(4), repeat=6):
        near = [h for h in H if sum(1 for a, b in zip(x, h) if a != b) <= 2]
        if len(near) >= 2:
            amb = {"vector": list(x), "words": [list(h) for h in near[:2]]}
            break
    res["hexacode_distance2_ambiguity"] = amb
    return res


# ---------------------------------------------------------------- Experiment 3
def gspan(v: int, perms: List[List[int]]) -> Tuple[int, ...]:
    """Basis (row-reduced, as ints) of the smallest G-invariant space containing v."""
    basis: List[int] = []
    queue = [v]
    while queue:
        x = queue.pop()
        for b in basis:
            hi = b.bit_length() - 1
            if (x >> hi) & 1:
                x ^= b
        if x:
            basis.append(x)
            basis.sort(reverse=True)
            # re-reduce
            red: List[int] = []
            for b in sorted(basis, reverse=True):
                y = b
                for r in red:
                    hi = r.bit_length() - 1
                    if (y >> hi) & 1:
                        y ^= r
                if y:
                    red.append(y)
                    red.sort(reverse=True)
            basis = red
            for p in perms:
                queue.append(apply_perm(p, x))
    return tuple(sorted(basis, reverse=True))


def span_all(basis: Tuple[int, ...]) -> List[int]:
    out = [0]
    for b in basis:
        out += [x ^ b for x in out]
    return out


def reduce_basis(vs: List[int]) -> Tuple[int, ...]:
    red: List[int] = []
    for v in vs:
        x = v
        for r in red:
            hi = r.bit_length() - 1
            if (x >> hi) & 1:
                x ^= r
        if x:
            red.append(x)
            red.sort(reverse=True)
    # full reduction
    out: List[int] = []
    for i, r in enumerate(sorted(red, reverse=True)):
        x = r
        for s in out:
            hi = s.bit_length() - 1
            if (x >> hi) & 1:
                x ^= s
        out.append(x)
        out.sort(reverse=True)
    return tuple(sorted(out, reverse=True))


def invariant_codes(perms: List[List[int]], dim: int = 12) -> List[Tuple[int, ...]]:
    """All G-invariant subspaces of F2^24 of dimension exactly `dim`.

    Every invariant subspace is the sum of the cyclic (G-)modules of its
    elements, so we enumerate cyclic modules of dimension <= dim and close
    under sums, discarding anything of dimension > dim.
    """
    cyclic = {}
    for v in range(1, 1 << 24):
        # one representative per orbit: skip if some image is smaller
        skip = False
        for p in perms:
            if apply_perm(p, v) < v:
                skip = True
                break
        if skip:
            continue
        b = gspan(v, perms)
        if len(b) <= dim:
            cyclic[b] = None
    mods = list(cyclic)
    frontier = {(): None}
    seen = {(): None}
    found = []
    while frontier:
        nxt = {}
        for s in frontier:
            for m in mods:
                b = reduce_basis(list(s) + list(m))
                if len(b) > dim or b in seen:
                    continue
                seen[b] = None
                if len(b) == dim:
                    found.append(b)
                else:
                    nxt[b] = None
        frontier = nxt
    return found


def is_golay(basis: Tuple[int, ...]) -> bool:
    words = span_all(basis)
    if len(set(words)) != 4096:
        return False
    return min(popcount(w) for w in words if w) == 8


def experiment3(subgroup_perms: List[List[int]], label: str) -> Dict[str, object]:
    codes = invariant_codes(subgroup_perms)
    golay = [c for c in codes if is_golay(c)]
    return {"group": label, "n_invariant_dim12": len(codes), "n_golay": len(golay),
            "example": list(golay[0]) if golay else None}


if __name__ == "__main__":
    rep: Dict[str, object] = {"identification": check_identification()}
    rep["experiment1_stabiliser"] = experiment1()
    rep["experiment2_faces"] = experiment2()
    print(json.dumps(rep, indent=1, default=str))


# ------------------------------------------------- Experiment 3 (fast version)
def perm_tables(perm: List[int]):
    """Byte lookup tables so a permutation can be applied with 3 lookups."""
    tabs = []
    for blk in range(3):
        t = [0] * 256
        for b in range(256):
            out = 0
            for k in range(8):
                if (b >> k) & 1:
                    out |= 1 << perm[8 * blk + k]
            t[b] = out
        tabs.append(t)
    return tabs


def make_apply(tabs):
    t0, t1, t2 = tabs

    def f(v: int) -> int:
        return t0[v & 255] | t1[(v >> 8) & 255] | t2[v >> 16]
    return f


ALLOWED_WEIGHTS = frozenset({0, 8, 12, 16, 24})


def gspan_fast(v: int, applies) -> Tuple[int, ...]:
    basis: List[int] = []
    queue = [v]
    while queue:
        x = queue.pop()
        for b in basis:
            if (x >> (b.bit_length() - 1)) & 1:
                x ^= b
        if x:
            basis.append(x)
            basis.sort(reverse=True)
            for f in applies:
                queue.append(f(x))
        if len(basis) > 12:
            return ()
    return reduce_basis(basis)


def good_module(basis: Tuple[int, ...]) -> bool:
    """dim <= 12 and every word has a Golay-legal weight."""
    if not basis or len(basis) > 12:
        return False
    words = [0]
    for b in basis:
        words += [x ^ b for x in words]
        if len(words) > 4096:
            return False
    return all(popcount(w) in ALLOWED_WEIGHTS for w in words)


def invariant_golay_codes(perms: List[List[int]], verbose: bool = False):
    """All G-invariant Golay codes on the 24 cube-surface cells.

    A Golay code is spanned by its octads, so it is the sum of the cyclic
    G-modules generated by weight-8 vectors; only modules all of whose words
    have weight in {0,8,12,16,24} can occur.  Enumerate those, close under
    sums with the same pruning, and keep the 12-dimensional results.
    """
    applies = [make_apply(perm_tables(p)) for p in perms]
    seen_vec = set()
    mods = set()
    for v in range(1 << 24):
        if popcount(v) != 8 or v in seen_vec:
            continue
        orb = {f(v) for f in applies}
        seen_vec |= orb
        b = gspan_fast(v, applies)
        if good_module(b):
            mods.add(b)
    if verbose:
        print(f"  cyclic modules kept: {len(mods)}", flush=True)
    mods = sorted(mods, key=len)
    found = []
    frontier = {m: None for m in mods}
    seen = dict(frontier)
    for m in mods:
        if len(m) == 12:
            found.append(m)
    while frontier:
        nxt = {}
        for s in frontier:
            if len(s) == 12:
                continue
            for m in mods:
                b = reduce_basis(list(s) + list(m))
                if b in seen or not good_module(b):
                    continue
                seen[b] = None
                if len(b) == 12:
                    found.append(b)
                else:
                    nxt[b] = None
        frontier = nxt
    return [c for c in found if is_golay(c)]
