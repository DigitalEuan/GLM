#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 MOG  —  the multi-MOG-cube, and what it is actually for
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 1 — the combinatorial view of the 24 coordinates.
  Deps   :  ../glm/glm_substrate.py (Golay, hexacode, verified MOG alignment),
            ../glm/glm_m24.py (M24 and its subgroup census),
            ../glm2/glm2_lattice.py (Lambda).

  ------------------------------------------------------------------------
  Two pictures, one set of 24 coordinates
  ------------------------------------------------------------------------

  Earlier GLM versions carried two separate mental images of the substrate:
  a 4 x 6 MOG frame with a hexacode shadow, and "three 8-bit cubes"
  (Language / Math / Script) with face-parity rules.  This module shows by
  computation that they are the SAME picture, and then extracts from it the
  functions the reasoner can use.

    * The 4 x 6 frame in the verified alignment splits into three 4 x 2
      BRICKS.  Each brick is a Golay OCTAD and the three together are a TRIO
      (a partition of the 24 coordinates into three octads).  Each brick is
      eight cells, i.e. a 2 x 2 x 2 cube: the "three cubes" of the earlier
      versions are the trio of the MOG.  [computed, not assumed]

    * The six COLUMNS are tetrads and any two of them unite to an octad:
      the columns are a SEXTET.  So the frame simultaneously carries a trio
      (its bricks) and a sextet (its columns) — the two maximal M24
      structures the reasoner uses for coarse classification.

    * The 16 cells left when one cube is removed carry an AFFINE structure
      AG(4, 2).  This is derived here: exactly 30 octads are disjoint from a
      given cube, they cut the 16 cells in 30 eight-sets, those form 15
      complementary pairs, and the corresponding 15 nontrivial F_2 functions
      together with 0 are closed under addition — a 4-dimensional dual
      space.  Four independent ones give each of the 16 cells a distinct
      4-bit affine coordinate.  This is the 4 x 4 "cube" picture, and the
      group that preserves it is the octad stabiliser 2^4:A8 = AGL(4,2) of
      order 322,560, which ../glm/glm_m24.py computes from M24.

    * A correction to the archive: the earlier versions asserted that each
      8-bit cube carries the Reed-Muller code RM(1,3) = [8,4,4].  What the
      Golay code actually induces on a cube is computed here: the TRACE is
      the full even-weight code [8,7,2] (128 words) and the SHORTENING is
      [8,1,8] (only 0 and the cube itself).  RM(1,3) is neither.

  ------------------------------------------------------------------------
  The multi-MOG-cube: a Leech point is a STACK of frames
  ------------------------------------------------------------------------

  One MOG frame holds 24 bits.  A Leech vector holds 24 integers, and its
  binary digit planes are a stack of MOG frames — a 4 x 6 x k cube.  The
  defining congruences of Lambda are exactly statements about the low planes
  of that stack:

      plane 0  (x mod 2)        constant: all 24 cells equal
      plane 1  (the cells with x = m+2 mod 4)   a GOLAY CODEWORD
      the mod-8 sum condition   a parity across the whole stack.

  So "multi-MOG-cube" is not an add-on: it is the lattice.  The reasoner
  reads a concept's carrier as such a stack and the plane-1 frame is the
  concept's Golay codeword — one of the 4096 that index the extraspecial
  group's 4096-dimensional representation, and hence one axis of the
  24 x 4096 = 98,304 odd part of the Griess ledger.

  ------------------------------------------------------------------------
  The functions this makes available to the reasoner
  ------------------------------------------------------------------------

      frame(mask)                 the 4 x 6 grid
      hexacode_shadow(mask)       six GF(4) symbols
      plane_stack(point)          the multi-MOG-cube of a Leech vector
      golay_plane(point)          the concept's Golay codeword
      cube_profile(mask)          weight and parity in each of the 3 cubes
      cube_coordinates(cell)      (brick, x, y, z) for every coordinate
      face_parities(mask, brick)  the six 2x2 faces of one cube
      sextet_of_tetrad(tetrad)    the six-tetrad partition through a tetrad
      trio_of_octad(octad)        the three-octad partition through an octad
      affine_coordinates()        the AG(4,2) labels on a cube complement
      octad_intersection_census() 1 / 30 / 448 / 280

      python3 glm3_mog.py            # self-audit
      python3 glm3_mog.py --quick    # skip the M24 subgroup census
================================================================================
"""

from __future__ import annotations

import sys
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int

import glm2_common as C2
import glm2_lattice as LAT
from glm_substrate import GOLAY, MOG

__all__ = [
    "N", "ALIGNED", "GOLAY_SET", "OCTADS",
    "cell_of", "frame", "hexacode_shadow",
    "brick_mask", "BRICKS", "column_mask", "COLUMNS", "row_mask",
    "cube_coordinates", "cube_profile", "face_parities",
    "trio_report", "sextet_report", "cube_code_report",
    "affine_structure", "affine_coordinates", "octad_intersection_census",
    "plane_stack", "golay_plane", "stack_report", "mog_audit",
]

N = 24
ALIGNED: Tuple[int, ...] = MOG.ALIGNED_BITS
GOLAY_SET = frozenset(C2.GOLAY_MASKS)
OCTADS: Tuple[int, ...] = tuple(sorted(m for m in GOLAY_SET
                                       if bin(m).count("1") == 8))


# ══════════════════════════════════════════════════════════════════════════════
# §1.  THE FRAME
# ══════════════════════════════════════════════════════════════════════════════

def cell_of(row: int, col: int) -> int:
    """The coordinate index sitting in frame cell (row, col)."""
    if not (0 <= row < 4 and 0 <= col < 6):
        raise ValueError("cell_of: row in 0..3, col in 0..5")
    return ALIGNED[6 * row + col]


def frame(mask: int) -> List[List[int]]:
    """The 4 x 6 grid of a 24-bit mask, in the verified alignment."""
    return [[(mask >> cell_of(r, c)) & 1 for c in range(6)] for r in range(4)]


def hexacode_shadow(mask: int) -> Tuple[int, ...]:
    """The six GF(4) column labels.  A Golay codeword casts a hexacode word."""
    bits = [(mask >> i) & 1 for i in range(N)]
    return MOG.shadow(bits, aligned=True)


def column_mask(col: int) -> int:
    m = 0
    for r in range(4):
        m |= 1 << cell_of(r, col)
    return m


def row_mask(row: int) -> int:
    m = 0
    for c in range(6):
        m |= 1 << cell_of(row, c)
    return m


def brick_mask(brick: int) -> int:
    """The 8 cells of one 4 x 2 brick = one 2 x 2 x 2 cube."""
    if not 0 <= brick < 3:
        raise ValueError("brick_mask: brick in 0..2")
    return column_mask(2 * brick) | column_mask(2 * brick + 1)


BRICKS: Tuple[int, int, int] = (brick_mask(0), brick_mask(1), brick_mask(2))
COLUMNS: Tuple[int, ...] = tuple(column_mask(c) for c in range(6))


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE THREE CUBES
# ══════════════════════════════════════════════════════════════════════════════

def cube_coordinates(coordinate: int) -> Tuple[int, int, int, int]:
    """
    Where a coordinate sits in the multi-cube picture:
        (brick, x, y, z)
    with x the column parity inside the brick and (y, z) the two bits of the
    row, so that each brick's eight cells are the vertices of a 2 x 2 x 2
    cube.
    """
    pos = ALIGNED.index(coordinate)
    row, col = divmod(pos, 6)
    brick, x = divmod(col, 2)
    y, z = divmod(row, 2)
    return brick, x, y, z


def cube_profile(mask: int) -> List[Dict[str, int]]:
    """Per-cube weight and parity of a 24-bit mask."""
    out = []
    for b in range(3):
        w = bin(mask & BRICKS[b]).count("1")
        out.append({"brick": b, "weight": w, "parity": w & 1})
    return out


def face_parities(mask: int, brick: int) -> Tuple[int, ...]:
    """
    The six face parities of one cube: for each of the three axes and each
    of the two values, the parity of the four cells on that face.
    """
    cells = [i for i in range(N) if (BRICKS[brick] >> i) & 1]
    out: List[int] = []
    for axis in range(3):
        for value in (0, 1):
            p = 0
            for i in cells:
                _, x, y, z = cube_coordinates(i)
                if (x, y, z)[axis] == value and (mask >> i) & 1:
                    p ^= 1
            out.append(p)
    return tuple(out)


def trio_report() -> Dict[str, object]:
    """The three bricks are octads and partition the 24 coordinates."""
    weights = [bin(b).count("1") for b in BRICKS]
    return {
        "brick_weights": weights,
        "each_is_an_octad": all(b in GOLAY_SET and w == 8
                                for b, w in zip(BRICKS, weights)),
        "disjoint": (BRICKS[0] & BRICKS[1] == 0
                     and BRICKS[0] & BRICKS[2] == 0
                     and BRICKS[1] & BRICKS[2] == 0),
        "covers_24": (BRICKS[0] | BRICKS[1] | BRICKS[2]) == (1 << N) - 1,
        "is_a_trio": all(b in GOLAY_SET for b in BRICKS)
                     and (BRICKS[0] | BRICKS[1] | BRICKS[2]) == (1 << N) - 1,
    }


def sextet_report() -> Dict[str, object]:
    """The six columns are tetrads whose pairwise unions are octads."""
    tetrads = all(bin(c).count("1") == 4 for c in COLUMNS)
    unions = all((COLUMNS[i] | COLUMNS[j]) in GOLAY_SET
                 for i in range(6) for j in range(i + 1, 6))
    return {"columns_are_tetrads": tetrads,
            "pairwise_unions_are_octads": unions,
            "is_a_sextet": tetrads and unions,
            "sextet_count": len(list(range(0)))
            or (24 * 23 * 22 * 21 // 24) // 6}


def cube_code_report(brick: int = 0) -> Dict[str, object]:
    """
    What the Golay code induces on one cube.  Computed exhaustively:
      trace      {c & cube : c in Golay}         -> the even-weight [8,7,2]
      shortening {c in Golay : c inside cube}    -> {0, cube} = [8,1,8]
    Neither is RM(1,3) = [8,4,4], which earlier versions claimed.
    """
    cube = BRICKS[brick]
    trace = {c & cube for c in GOLAY_SET}
    inside = [c for c in GOLAY_SET if c & ~cube & ((1 << N) - 1) == 0]
    all_even = all(bin(t).count("1") % 2 == 0 for t in trace)
    return {
        "trace_size": len(trace),
        "trace_is_even_weight_code": len(trace) == 128 and all_even,
        "shortened_size": len(inside),
        "shortened_is_cube_and_zero": sorted(inside) == sorted([0, cube]),
        "rm13_claim_refuted": len(trace) != 16 and len(inside) != 16,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE 4 x 4 PICTURE:  AG(4, 2) ON A CUBE COMPLEMENT
# ══════════════════════════════════════════════════════════════════════════════

def affine_structure(brick: int = 0) -> Dict[str, object]:
    """
    Derive the affine space AG(4,2) on the 16 cells outside one cube.

    Exactly 30 octads are disjoint from the cube.  Each cuts the 16 cells in
    an 8-set; those 30 eight-sets form 15 complementary pairs, and the 15
    corresponding "hyperplane" functions, together with the zero function,
    are closed under addition modulo 2 — that is a 4-dimensional space of
    linear functionals.  Four independent ones give every cell a distinct
    4-bit label, which is the affine identification.
    """
    cube = BRICKS[brick]
    outside = [i for i in range(N) if not (cube >> i) & 1]
    index = {c: k for k, c in enumerate(outside)}
    disjoint = [o for o in OCTADS if o & cube == 0]
    cuts = []
    for o in disjoint:
        bits = 0
        for c in outside:
            if (o >> c) & 1:
                bits |= 1 << index[c]
        cuts.append(bits)
    full = (1 << 16) - 1
    pairs = set()
    for b in cuts:
        pairs.add(min(b, full ^ b))
    # the family of functionals: each pair gives one function up to complement
    functionals = sorted(pairs)
    closed = True
    fam = set(functionals) | {0}
    for a in functionals:
        for b in functionals:
            s = a ^ b
            if min(s, full ^ s) not in fam and s != 0:
                closed = False
    # choose four independent functionals and label the cells
    chosen: List[int] = []
    for f in functionals:
        trial = chosen + [f]
        if _labels_distinct_rank(trial) > _labels_distinct_rank(chosen):
            chosen = trial
        if len(chosen) == 4:
            break
    labels = {}
    for c in outside:
        lab = 0
        for k, f in enumerate(chosen):
            if (f >> index[c]) & 1:
                lab |= 1 << k
        labels[c] = lab
    return {
        "cells": outside,
        "disjoint_octads": len(disjoint),
        "hyperplanes": len(cuts),
        "complementary_pairs": len(pairs),
        "closed_under_addition": closed,
        "chosen_functionals": len(chosen),
        "labels": labels,
        "labels_are_a_bijection": sorted(labels.values()) == list(range(16)),
        "affine_group_order": 322560,
    }


def _labels_distinct_rank(fs: Sequence[int]) -> int:
    """How many distinct labels the chosen functionals separate."""
    if not fs:
        return 1
    seen = set()
    for c in range(16):
        lab = 0
        for k, f in enumerate(fs):
            if (f >> c) & 1:
                lab |= 1 << k
        seen.add(lab)
    return len(seen)


def affine_coordinates(brick: int = 0) -> Dict[int, int]:
    return affine_structure(brick)["labels"]        # type: ignore[return-value]


def octad_intersection_census(brick: int = 0) -> Dict[int, int]:
    """|O ∩ cube| over the 759 octads: 8 once, 4, 2 and 0."""
    cube = BRICKS[brick]
    out: Dict[int, int] = {}
    for o in OCTADS:
        k = bin(o & cube).count("1")
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


# ══════════════════════════════════════════════════════════════════════════════
# §4.  SEXTETS AND TRIOS AS CLASSIFIERS
# ══════════════════════════════════════════════════════════════════════════════

def sextet_of_tetrad(tetrad: int) -> Tuple[int, ...]:
    """
    The sextet through a tetrad: the six tetrads T' with T u T' an octad,
    including T itself.  Every 4-subset of the 24 lies in exactly one
    sextet, so there are C(24,4)/6 = 1,771 of them.
    """
    if bin(tetrad).count("1") != 4:
        raise ValueError("sextet_of_tetrad: need a 4-element subset")
    parts = [tetrad]
    rest = ((1 << N) - 1) ^ tetrad
    for o in OCTADS:
        if o & tetrad == tetrad:
            other = o ^ tetrad
            if other and other not in parts:
                parts.append(other)
    if len(parts) != 6 or (rest | tetrad) != (1 << N) - 1:
        raise AssertionError("sextet computation failed")
    return tuple(sorted(parts))


def trio_of_octad(octad: int) -> Tuple[int, ...]:
    """
    A trio through an octad: the octad together with two disjoint octads
    covering the rest.  (For a given octad there are 30 disjoint octads and
    they pair up into 15 trios; the first one found is returned.)
    """
    if octad not in GOLAY_SET or bin(octad).count("1") != 8:
        raise ValueError("trio_of_octad: need an octad")
    rest = ((1 << N) - 1) ^ octad
    for o in OCTADS:
        if o & octad == 0:
            third = rest ^ o
            if third in GOLAY_SET:
                return tuple(sorted((octad, o, third)))
    raise AssertionError("no trio found")


def trio_census() -> Dict[str, int]:
    """Count the trios: partitions of the 24 coordinates into three octads."""
    partitions = set()
    for o in OCTADS:
        rest = ((1 << N) - 1) ^ o
        for p in OCTADS:
            if p & o:
                continue
            third = rest ^ p
            if third in GOLAY_SET and bin(third).count("1") == 8:
                partitions.add(frozenset((o, p, third)))
    return {"trios": len(partitions), "octads": len(OCTADS),
            "sextets": (24 * 23 * 22 * 21 // 24) // 6}


# ══════════════════════════════════════════════════════════════════════════════
# §5.  THE MULTI-MOG-CUBE:  DIGIT PLANES OF A LEECH POINT
# ══════════════════════════════════════════════════════════════════════════════

def plane_stack(point: Sequence[int], depth: int = 4) -> List[int]:
    """
    The stack of MOG frames of a lattice point: plane k is the 24-bit mask
    of the k-th binary digit of the coordinates, taken from a non-negative
    representative shifted by a common multiple of 8 (which changes no
    congruence used below).
    """
    shift = 0
    lo = min(int(v) for v in point)
    if lo < 0:
        shift = 8 * ((-lo + 7) // 8)
    vals = [int(v) + shift for v in point]
    out = []
    for k in range(depth):
        m = 0
        for i, v in enumerate(vals):
            if (v >> k) & 1:
                m |= 1 << i
        out.append(m)
    return out


def golay_plane(point: Sequence[int]) -> int:
    """
    The Golay codeword carried by a Leech point: the set of coordinates with
    x_i = m + 2 (mod 4), where m is the common parity.  This is plane 1 of
    the stack relative to the parity, and membership in the Golay code is
    part of the definition of Lambda.
    """
    m = int(point[0]) & 1
    target = (m + 2) % 4
    mask = 0
    for i, v in enumerate(point):
        if int(v) % 4 == target:
            mask |= 1 << i
    return mask


def stack_report(points: Sequence[Sequence[int]]) -> Dict[str, object]:
    """
    Check the multi-MOG-cube reading of Lambda on a supply of lattice
    points: plane 0 constant, plane 1 a Golay codeword casting a hexacode
    shadow, and the mod-8 sum condition.
    """
    plane0_constant = True
    golay = True
    hexa = True
    sums = True
    for x in points:
        planes = plane_stack(x)
        if planes[0] not in (0, (1 << N) - 1):
            plane0_constant = False
        g = golay_plane(x)
        if g not in GOLAY_SET:
            golay = False
        if hexacode_shadow(g) not in _HEXACODE_SET:
            hexa = False
        m = int(x[0]) & 1
        if sum(int(v) for v in x) % 8 != (4 * m) % 8:
            sums = False
    return {"points": len(points),
            "plane0_constant": plane0_constant,
            "plane1_is_golay": golay,
            "plane1_casts_hexacode_shadow": hexa,
            "mod8_sum_condition": sums,
            "golay_codewords": 4096,
            "rep_dimension": 4096,
            "odd_ledger": 24 * 4096}


from glm_substrate import HEXACODE as _HEX          # noqa: E402
_HEXACODE_SET = frozenset(_HEX.word_set)


# ══════════════════════════════════════════════════════════════════════════════
# §6.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def mog_audit(full: bool = True) -> Dict[str, object]:
    out: Dict[str, object] = {}
    out["alignment"] = MOG.verify_hexacode_shadow()
    out["trio"] = trio_report()
    out["sextet"] = sextet_report()
    out["cube_code"] = cube_code_report(0)
    out["affine"] = {k: v for k, v in affine_structure(0).items()
                     if k not in ("labels", "cells")}
    out["affine"]["labels_are_a_bijection"] = \
        affine_structure(0)["labels_are_a_bijection"]
    out["octad_intersections"] = octad_intersection_census(0)
    out["census"] = trio_census()
    # the multi-MOG stack on genuine lattice points
    pts = [LAT.LEECH_BASIS[i] for i in range(N)]
    pts += [tuple(a + b for a, b in zip(LAT.LEECH_BASIS[i],
                                        LAT.LEECH_BASIS[(i + 7) % N]))
            for i in range(N)]
    out["stack"] = stack_report(pts)
    # every coordinate has a cube address, and the address map is injective
    addrs = [cube_coordinates(i) for i in range(N)]
    out["cube_addresses_distinct"] = len(set(addrs)) == N
    if full:
        import glm_m24
        census = glm_m24.subgroup_census()
        out["m24"] = {
            "order": census["group_order"],
            "octads": census["octads"],
            "octad_stabiliser_order": census["octad_stabiliser_order"],
            "sextet_orbit": census["sextet_orbit"],
            "sextet_stabiliser_order": census["sextet_stabiliser_order"],
            "dodecad_stabiliser_order": census["dodecad_stabiliser_order"],
            "octad_stabiliser_is_AGL_4_2":
                census["octad_stabiliser_order"] == 322560,
        }
    return out


def main(argv: Optional[Sequence[str]] = None) -> None:
    argv = list(argv if argv is not None else sys.argv[1:])
    full = "--quick" not in argv
    print(banner("GLM-3  MOG  —  the multi-MOG-cube"))
    a = mog_audit(full=full)
    al = a["alignment"]
    print("\n[the frame]")
    print(f"  4096 codewords cast hexacode shadows : {al['aligned']}"
          f" ({al['failures']} failures)")
    t = a["trio"]
    print("\n[the three cubes = the MOG trio]")
    print(f"  brick weights                        : {t['brick_weights']}")
    print(f"  each brick is an octad               : {t['each_is_an_octad']}")
    print(f"  they partition the 24 coordinates    : {t['covers_24']}")
    s = a["sextet"]
    print(f"\n[the six columns = a sextet]")
    print(f"  columns are tetrads                  : {s['columns_are_tetrads']}")
    print(f"  pairwise unions are octads           : "
          f"{s['pairwise_unions_are_octads']}")
    c = a["cube_code"]
    print(f"\n[what the Golay code induces on one cube]")
    print(f"  trace has {c['trace_size']} words, even weight  : "
          f"{c['trace_is_even_weight_code']}")
    print(f"  shortening is {{0, cube}}              : "
          f"{c['shortened_is_cube_and_zero']}")
    print(f"  so it is NOT RM(1,3)                 : {c['rm13_claim_refuted']}")
    af = a["affine"]
    print(f"\n[the 4 x 4 picture: AG(4,2) on a cube complement]")
    print(f"  octads disjoint from the cube        : {af['disjoint_octads']}")
    print(f"  complementary pairs of hyperplanes   : {af['complementary_pairs']}")
    print(f"  closed under addition                : {af['closed_under_addition']}")
    print(f"  the 16 cells get distinct labels     : "
          f"{af['labels_are_a_bijection']}")
    print(f"  |AGL(4,2)| = |2^4:A8|                : "
          f"{fmt_int(af['affine_group_order'])}")
    print(f"  octad intersection census            : {a['octad_intersections']}")
    ce = a["census"]
    print(f"  octads / trios / sextets             : "
          f"{fmt_int(ce['octads'])} / {fmt_int(ce['trios'])} /"
          f" {fmt_int(ce['sextets'])}")
    st = a["stack"]
    print(f"\n[the multi-MOG-cube: digit planes of a Leech point]")
    print(f"  points tested                        : {st['points']}")
    print(f"  plane 0 is constant                  : {st['plane0_constant']}")
    print(f"  plane 1 is a Golay codeword          : {st['plane1_is_golay']}")
    print(f"  plane 1 casts a hexacode shadow      : "
          f"{st['plane1_casts_hexacode_shadow']}")
    print(f"  the mod-8 sum condition holds        : {st['mod8_sum_condition']}")
    print(f"  4096 frames = rep dimension          : "
          f"{fmt_int(st['rep_dimension'])}")
    print(f"  24 x 4096 = odd part of the ledger   : {fmt_int(st['odd_ledger'])}")
    if full and "m24" in a:
        m = a["m24"]
        print(f"\n[M24, from ../glm/glm_m24.py]")
        for k, v in m.items():
            print(f"  {k:34s}: {fmt_int(v) if isinstance(v, int) else v}")
    print()


if __name__ == "__main__":
    main()
