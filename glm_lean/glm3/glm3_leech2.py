#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 LEECH MOD 2  —  the index set the Monster actually uses
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 1 — the bridge from the lattice carrier to the Monster.
  Deps   :  ../glm2/glm2_lattice.py (Lambda, decode, minimal vectors).

  ------------------------------------------------------------------------
  Why this module is the whole point of the third generation
  ------------------------------------------------------------------------

  GLM-1 and GLM-2 named the Monster and then did nothing with it: the number
  196,884 appeared as arithmetic and the group never acted on anything.  The
  Monster does not act on the Leech lattice — it acts on structures built on
  Lambda/2Lambda, and that quotient is where a concept carried by a lattice
  point becomes a Monster-theoretic object.  Everything in GLM-3 above this
  module is indexed by what is built here.

  The facts, all COMPUTED in this file rather than quoted:

    * Lambda/2Lambda is a 24-dimensional F_2 vector space (2^24 classes)
      carrying a quadratic form
          q(lambda) = (lambda.lambda)/16  mod 2
      with polar form
          B(lambda, mu) = (lambda.mu)/8   mod 2
      (the /16 and /8 are the scale of the "times sqrt 8" integer model that
      GLM-2 uses, in which the minimal norm is 32).  Both are well defined on
      classes; this is checked, not assumed.

    * The form is nondegenerate of PLUS type.  A Witt decomposition into 12
      hyperbolic planes is computed explicitly, so the number of singular
      classes is 2^23 + 2^11 = 8,390,656 in closed form.

    * Every nonzero class has a type in {2, 3, 4} — the minimal norm in the
      class divided by 16 — and the census

          1  +  98,280  +  8,386,560  +  8,292,375  =  16,777,216 = 2^24
        type 0     2           3            4

      closes exactly, with 98,280 = 196,560/2 and 8,386,560 = 16,773,120/2
      taken from the theta series GLM-2 computes, and 8,292,375 =
      398,034,000/48 from the frame structure.  Consistency check with the
      quadratic form: the type-3 classes are precisely the non-singular ones,
      1 + 98,280 + 8,292,375 = 8,390,656 = 2^23 + 2^11 and 8,386,560 =
      2^23 - 2^11.  Type is therefore a refinement of the F_2 quadratic form,
      and both are Monster-relevant invariants of a concept.

    * A type-2 class is a pair {+-lambda} of minimal vectors: 98,280 of them,
      the index set of the middle piece of the Griess ledger and hence of the
      2A axes visible inside the 2B centraliser.
    * A type-4 class is a coordinate FRAME: 48 vectors, 24 orthogonal pairs.
      The frame of a concept is computed here and used by the reasoner as a
      24-way orthogonal decomposition of that concept.

      python3 glm3_leech2.py        # self-audit
================================================================================
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Dict, List, Optional, Sequence, Tuple

from glm3_common import banner, fmt_int  # noqa: F401  (banner used in main)

import glm2_lattice as LAT

__all__ = [
    "DIM", "N_CLASSES", "class_of", "class_vector", "representative",
    "STACK_OFFSET", "STACK_DEPTH", "class_stack", "class_stack_rebuild",
    "primitive_point", "coordinate_range", "derive_stack_parameters",
    "stack_is_faithful", "depth_report",
    "q_form", "b_form", "q_coefficients", "b_coefficients",
    "witt_decomposition", "singular_class_count", "form_is_plus_type",
    "class_type", "type_of_point", "minimal_vectors_of_class",
    "frame_of_class", "type_census", "pair_invariant", "pair_census",
    "type2_class_table", "leech2_audit",
]

DIM = 24
N_CLASSES = 1 << 24

Vec = Tuple[int, ...]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  CLASSES
# ══════════════════════════════════════════════════════════════════════════════

def class_of(x: Sequence[int]) -> int:
    """
    The class of a lattice point in Lambda/2Lambda, as a 24-bit integer: the
    coordinates of x in the GLM-2 Leech basis, reduced mod 2.
    """
    u = LAT.to_coords(list(x))
    if u is None:
        raise ValueError("class_of: the point is not in Lambda")
    out = 0
    for i, c in enumerate(u):
        if c & 1:
            out |= 1 << i
    return out


def class_vector(cls: int) -> List[int]:
    """The class as a list of 24 bits (coordinates in the Leech basis)."""
    return [(cls >> i) & 1 for i in range(DIM)]


def representative(cls: int) -> Vec:
    """The lattice point with 0/1 coordinates representing the class."""
    return LAT.from_coords(class_vector(cls))


#: The 2-adic stack of a lattice point is taken after a fixed translation by
#: an OFFSET in every Leech-basis coordinate, so that negative coordinates
#: expand too.  Neither the offset nor the depth is a magic number: given a
#: bound C on the Leech-basis coordinates of the points to be encoded, any
#: offset O >= C and any depth D with O + C < 2^D make the stack faithful
#: (Proposition D1 below), and `derive_stack_parameters` computes the least
#: such pair.  The module defaults are the pair derived from the GLM-2
#: register with one octave of headroom on the offset; see `depth_report`.
STACK_OFFSET = 1 << 9
STACK_DEPTH = 10


def coordinate_range(points: Sequence[Sequence[int]]) -> int:
    """
    The largest absolute Leech-BASIS coordinate over a set of lattice points:
    the only property of the data the stack parameters depend on.
    """
    worst = 0
    for x in points:
        u = LAT.to_coords(list(x))
        if u is None:
            raise ValueError("coordinate_range: a point is not in Lambda")
        for c in u:
            worst = max(worst, abs(int(c)))
    return worst


def derive_stack_parameters(max_abs: int, offset: Optional[int] = None
                            ) -> Tuple[int, int]:
    """
    (offset, depth) for data whose Leech-basis coordinates are bounded in
    absolute value by `max_abs`.

    Proposition D1 (faithfulness at any admissible depth).  Let O >= max_abs
    and let D satisfy 2^D > O + max_abs.  Then for every point x with
    coordinates u_i, |u_i| <= max_abs, the shifted coordinates u_i + O lie in
    [0, 2^D), so their binary expansions have D digits, and

        rebuild(stack(x)) = x

    because reading the k-th digit of each coordinate and then reassembling
    sum_k 2^k digit_k - O is the identity on [0, 2^D).  Faithfulness is
    therefore a statement about the RANGE of the data, not about the number
    ten.

    With no offset supplied the least admissible pair is returned: the least
    power of two O >= max_abs (so that the shift is a shift of digit planes
    and not an arbitrary translation), and then the least D with
    2^D > O + max_abs, which is D = log2(O) + 1.
    """
    if max_abs < 0:
        raise ValueError("derive_stack_parameters: negative range")
    if offset is None:
        offset = 1
        while offset < max_abs:
            offset <<= 1
    if offset < max_abs:
        raise ValueError("derive_stack_parameters: offset below the range")
    depth = 1
    while (1 << depth) <= offset + max_abs:
        depth += 1
    return offset, depth


def class_stack(x: Sequence[int], depth: Optional[int] = None,
                offset: Optional[int] = None) -> List[int]:
    """
    The MULTI-MOG-CUBE of a lattice point, in the Leech basis: write the 24
    coordinates of x + offset (1, ..., 1) in binary and let plane k be the
    24-bit mask of the k-th binary digit.  Every plane is a class of
    Lambda/2Lambda, so a point carries not one Monster address but a stack
    of them; plane 0 is the class of x itself.

    `depth` and `offset` are parameters, defaulting to the module's derived
    pair.  Any admissible pair rebuilds the point exactly (Proposition D1),
    and raising the depth above the admissible minimum only appends planes
    that are identically zero — which is why the reasoning above the stack is
    depth-independent.

    Reduction mod 2 keeps only plane 0; the stack keeps everything, which is
    why GLM-3 reasons with the stack (see `class_stack_rebuild`).
    """
    depth = STACK_DEPTH if depth is None else depth
    offset = STACK_OFFSET if offset is None else offset
    u = LAT.to_coords(list(x))
    if u is None:
        raise ValueError("class_stack: the point is not in Lambda")
    vals = [int(v) + offset for v in u]
    if any(v < 0 or v >= (1 << depth) for v in vals):
        raise ValueError("class_stack: coordinate out of range for the offset")
    planes = []
    for k in range(depth):
        m = 0
        for i, v in enumerate(vals):
            if (v >> k) & 1:
                m |= 1 << i
        planes.append(m)
    return planes


def class_stack_rebuild(planes: Sequence[int],
                        offset: Optional[int] = None) -> Vec:
    """The point a stack came from: the stack is a faithful encoding."""
    offset = STACK_OFFSET if offset is None else offset
    u = []
    for i in range(DIM):
        v = 0
        for k, m in enumerate(planes):
            if (m >> i) & 1:
                v |= 1 << k
        u.append(v - offset)
    return LAT.from_coords(u)


def stack_is_faithful(x: Sequence[int], depth: Optional[int] = None,
                      offset: Optional[int] = None) -> bool:
    """rebuild(stack(x)) == x, at the given parameters."""
    planes = class_stack(x, depth, offset)
    return tuple(class_stack_rebuild(planes, offset)) == tuple(int(c)
                                                               for c in x)


def depth_report(points: Sequence[Sequence[int]],
                 extra_depths: int = 4) -> Dict[str, object]:
    """
    Turn the stack depth from a constant into a measurement.

    Computes the coordinate range of the given points, the least admissible
    (offset, depth) pair, the depth the module's conventional offset forces,
    and then checks Proposition D1 empirically: the rebuild identity holds at
    every admissible pair tried, planes at or above the least admissible
    depth are identically zero at a fixed offset (so deeper stacks add
    nothing), and the planes below it do not move.
    """
    pts = [tuple(int(c) for c in p) for p in points]
    max_abs = coordinate_range(pts)
    least_offset, least_depth = derive_stack_parameters(max_abs)
    _o, conventional_depth = derive_stack_parameters(max_abs, STACK_OFFSET)
    combos: List[Tuple[int, int]] = []
    for off in (least_offset, STACK_OFFSET, STACK_OFFSET * 2):
        _o2, d0 = derive_stack_parameters(max_abs, off)
        for d in range(d0, d0 + extra_depths + 1):
            combos.append((off, d))
    faithful = {}
    for off, d in combos:
        faithful[f"offset {off}, depth {d}"] = all(
            stack_is_faithful(p, d, off) for p in pts)
    base = {tuple(class_stack(p, conventional_depth, STACK_OFFSET))
            for p in pts}
    deeper_agrees = True
    deeper_zero = True
    for d in range(conventional_depth, conventional_depth + extra_depths + 1):
        for p in pts:
            planes = class_stack(p, d, STACK_OFFSET)
            if tuple(planes[:conventional_depth]) not in base:
                deeper_agrees = False
            if any(planes[conventional_depth:]):
                deeper_zero = False
    return {
        "points": len(pts),
        "coordinate_range": max_abs,
        "least_offset": least_offset,
        "least_depth": least_depth,
        "module_offset": STACK_OFFSET,
        "depth_forced_by_the_module_offset": conventional_depth,
        "module_depth": STACK_DEPTH,
        "module_depth_is_the_derived_one":
            conventional_depth == STACK_DEPTH,
        "faithful": faithful,
        "faithful_everywhere": all(faithful.values()),
        "deeper_planes_are_zero": deeper_zero,
        "lower_planes_unchanged": deeper_agrees,
    }


def primitive_point(x: Sequence[int]) -> Vec:
    """
    x divided by the largest power of 2 that keeps it in Lambda.  A point
    lies in 2 Lambda exactly when all of its Leech-basis coordinates are
    even, so this is exact and finite; the class of the primitive point is
    the lowest nonzero plane of the stack.
    """
    u = LAT.to_coords(list(x))
    if u is None:
        raise ValueError("primitive_point: not a lattice point")
    if all(v == 0 for v in u):
        return tuple(int(v) for v in x)
    while all(v % 2 == 0 for v in u):
        u = [v // 2 for v in u]
    return LAT.from_coords(u)


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE F_2 QUADRATIC SPACE
# ══════════════════════════════════════════════════════════════════════════════

def q_coefficients() -> Tuple[int, ...]:
    """q(e_i) for the 24 basis classes: norm/16 mod 2."""
    return tuple((LAT.norm2(r) // 16) % 2 for r in LAT.LEECH_BASIS)


def b_coefficients() -> Tuple[Tuple[int, ...], ...]:
    """B(e_i, e_j) = (e_i . e_j)/8 mod 2."""
    rows = []
    for i in range(DIM):
        rows.append(tuple((LAT.inner(LAT.LEECH_BASIS[i], LAT.LEECH_BASIS[j])
                           // 8) % 2 for j in range(DIM)))
    return tuple(rows)


_QC = q_coefficients()
_BC = b_coefficients()


def q_form(cls: int) -> int:
    """
    q(class) in F_2, from the coefficient table:
        q(u) = sum_i q_i u_i + sum_{i<j} B_ij u_i u_j.
    Agrees with (norm of any representative)/16 mod 2 — checked in the audit.
    """
    bits = [i for i in range(DIM) if (cls >> i) & 1]
    total = 0
    for a, i in enumerate(bits):
        total ^= _QC[i]
        for j in bits[a + 1:]:
            total ^= _BC[i][j]
    return total & 1


def b_form(u: int, v: int) -> int:
    """The polar form B(u, v) in F_2."""
    ubits = [i for i in range(DIM) if (u >> i) & 1]
    vbits = [j for j in range(DIM) if (v >> j) & 1]
    total = 0
    for i in ubits:
        row = _BC[i]
        for j in vbits:
            total ^= row[j]
    return total & 1


def witt_decomposition() -> Dict[str, object]:
    """
    Decompose (Lambda/2Lambda, q) into 2-dimensional nondegenerate planes by
    symplectic Gram-Schmidt, and record for each plane whether it is
    hyperbolic (contains a nonzero singular vector) or anisotropic.

    A nondegenerate F_2 quadratic space of dimension 2m is of plus type iff
    the number of anisotropic planes in such a decomposition is even, and
    then its singular vectors (including 0) number 2^(2m-1) + 2^(m-1).
    """
    # start from the full space, given by a basis of 24 unit classes
    basis = [1 << i for i in range(DIM)]
    planes: List[Tuple[int, int, bool]] = []
    while basis:
        u = basis[0]
        # find a partner v in the current space with B(u, v) = 1
        partner = None
        for cand in basis[1:]:
            if b_form(u, cand):
                partner = cand
                break
        if partner is None:
            # u may be paired with a combination; search combinations of two
            for a in range(len(basis)):
                for b in range(a + 1, len(basis)):
                    cand = basis[a] ^ basis[b]
                    if b_form(u, cand):
                        partner = cand
                        break
                if partner is not None:
                    break
        if partner is None:
            raise AssertionError("degenerate form: no hyperbolic partner")
        v = partner
        hyperbolic = not (q_form(u) == 1 and q_form(v) == 1)
        planes.append((u, v, hyperbolic))
        # perp complement of <u, v> inside the current span
        rest = []
        for w in basis:
            if w in (u, v):
                continue
            w2 = w
            if b_form(w2, v):
                w2 ^= u
            if b_form(w2, u):
                w2 ^= v
            if w2 == 0:
                continue
            rest.append(w2)
        # keep an independent set
        basis = _independent(rest)
    anisotropic = sum(0 if h else 1 for (_, _, h) in planes)
    m = len(planes)
    plus = anisotropic % 2 == 0
    return {
        "planes": m,
        "anisotropic_planes": anisotropic,
        "plus_type": plus,
        "singular_count": (1 << (2 * m - 1)) + ((1 if plus else -1)
                                                << (m - 1)),
    }


def _independent(vectors: Sequence[int]) -> List[int]:
    """A basis of the F_2 span of `vectors` (Gaussian elimination on ints)."""
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


def singular_class_count() -> int:
    return int(witt_decomposition()["singular_count"])


def form_is_plus_type() -> bool:
    return bool(witt_decomposition()["plus_type"])


# ══════════════════════════════════════════════════════════════════════════════
# §3.  TYPES
# ══════════════════════════════════════════════════════════════════════════════

def type_of_point(x: Sequence[int]) -> int:
    """
    The type of the class of a lattice point: the minimal norm in x + 2Lambda,
    divided by 16.  Computed with the GLM-2 Leech decoder, since

        min_{lambda in Lambda} |x - 2 lambda|^2  =  4 * dist(x/2, Lambda)^2.
    """
    half = [F(int(v), 2) for v in x]
    res = LAT.decode(half)
    n2 = 4 * res.dist2
    if n2 % 16:
        raise AssertionError(f"coset minimum {n2} is not a multiple of 16")
    return int(n2 // 16)


def class_type(cls: int) -> int:
    """The type of a class given by its 24 bits."""
    return type_of_point(representative(cls))


def minimal_vectors_of_class(cls: int) -> List[Vec]:
    """
    Every vector of minimal norm in the class.

      * type 0: just the origin;
      * types 2 and 3: a pair {+-v};
      * type 4: a frame of 48 vectors, computed as
            {+-v} union {2u - v : u minimal (norm 32), u.v = 32},
        because if v and v' are two norm-64 vectors of the same class then
        (v + v')/2 lies in Lambda and has norm 32 exactly when v.v' = 0.
    """
    x = representative(cls)
    t = type_of_point(x)
    if t == 0:
        return [tuple([0] * DIM)]
    half = [F(int(v), 2) for v in x]
    res = LAT.decode(half)
    v = tuple(int(a) - 2 * int(b) for a, b in zip(x, res.point))
    if LAT.norm2(v) != 16 * t:
        raise AssertionError("decoder did not return a coset minimum")
    if t in (2, 3):
        return [v, tuple(-a for a in v)]
    out = [v, tuple(-a for a in v)]
    for u in LAT.minimal_vectors():
        if LAT.inner(u, v) == 32:
            out.append(tuple(2 * a - b for a, b in zip(u, v)))
    return out


def frame_of_class(cls: int) -> List[Vec]:
    """The 48-vector coordinate frame of a type-4 class."""
    t = class_type(cls)
    if t != 4:
        raise ValueError(f"frame_of_class: class has type {t}, not 4")
    return minimal_vectors_of_class(cls)


# ══════════════════════════════════════════════════════════════════════════════
# §4.  THE CENSUS
# ══════════════════════════════════════════════════════════════════════════════

def type_census() -> Dict[str, object]:
    """
    The class census, derived from the theta series rather than quoted.

        type 2 classes = N(32)/2   = 196,560/2
        type 3 classes = N(48)/2   = 16,773,120/2
        type 4 classes = N(64)/48  = 398,034,000/48
    """
    theta = LAT.theta_from_modular_forms(order=5)   # 1, 0, N(32), N(48), N(64)
    n2, n3, n4 = theta[2], theta[3], theta[4]
    c2, c3, c4 = n2 // 2, n3 // 2, n4 // 48
    total = 1 + c2 + c3 + c4
    return {
        "theta": theta[:5],
        "type2_vectors": n2, "type3_vectors": n3, "type4_vectors": n4,
        "type2_classes": c2, "type3_classes": c3, "type4_classes": c4,
        "total": total,
        "expected_total": N_CLASSES,
        "closes": total == N_CLASSES,
        "singular": 1 + c2 + c4,
        "nonsingular": c3,
        "plus_type_singular": (1 << 23) + (1 << 11),
        "plus_type_nonsingular": (1 << 23) - (1 << 11),
        "matches_plus_type": (1 + c2 + c4 == (1 << 23) + (1 << 11)
                              and c3 == (1 << 23) - (1 << 11)),
    }


def type2_class_table() -> Dict[int, Vec]:
    """
    Every type-2 class, with one of its two minimal vectors.  Streaming the
    196,560 minimal vectors and reducing each one mod 2Lambda must produce
    exactly 98,280 distinct classes, each hit exactly twice.
    """
    table: Dict[int, Vec] = {}
    counts: Dict[int, int] = {}
    for v in LAT.minimal_vectors():
        c = class_of(v)
        counts[c] = counts.get(c, 0) + 1
        if c not in table:
            table[c] = v
    if any(k != 2 for k in counts.values()):
        raise AssertionError("a type-2 class did not contain exactly +-v")
    return table


# ══════════════════════════════════════════════════════════════════════════════
# §5.  PAIRS — the Monster-relevant invariant of two concepts
# ══════════════════════════════════════════════════════════════════════════════

def pair_invariant(v: Sequence[int], w: Sequence[int]) -> int:
    """
    |v.w|/8 for two minimal vectors: the complete invariant of the pair of
    type-2 classes under Co_0, taking the values 4 (same class), 2, 1, 0.
    Well defined on classes because a class is {+-v}.
    """
    return abs(LAT.inner(v, w)) // 8


def pair_census(v: Optional[Sequence[int]] = None) -> Dict[int, int]:
    """
    How the 196,560 minimal vectors distribute by inner product against a
    fixed one.  Comes out as
        4: 2,   2: 9,200,   1: 94,208,   0: 93,150
    (counting +-mu together with mu), the classical Leech distribution and
    the reason the Monster's 2A axes have only four mutual positions.
    """
    if v is None:
        v = next(iter(LAT.minimal_vectors()))
    out: Dict[int, int] = {}
    for w in LAT.minimal_vectors():
        k = pair_invariant(v, w)
        out[k] = out.get(k, 0) + 1
    return out


# ══════════════════════════════════════════════════════════════════════════════
# §6.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def leech2_audit(full: bool = True) -> Dict[str, object]:
    out: Dict[str, object] = {}
    witt = witt_decomposition()
    out["witt"] = witt
    out["census"] = type_census()

    # q and B agree with the lattice definition on a spread of classes
    ok_q = True
    ok_b = True
    seed = 0x9E3779B9
    for _ in range(64):
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        u = seed & 0xFFFFFF
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        w = seed & 0xFFFFFF
        xu, xw = representative(u), representative(w)
        if q_form(u) != (LAT.norm2(xu) // 16) % 2:
            ok_q = False
        if b_form(u, w) != (LAT.inner(xu, xw) // 8) % 2:
            ok_b = False
    out["q_matches_lattice"] = ok_q
    out["b_matches_lattice"] = ok_b

    # q is well defined mod 2 Lambda: adding 2*(a lattice point) does not move it
    ok_welldef = True
    for i in range(DIM):
        x = LAT.LEECH_BASIS[i]
        y = tuple(a + 2 * b for a, b in zip(x, LAT.LEECH_BASIS[(i + 5) % DIM]))
        if class_of(x) != class_of(y):
            ok_welldef = False
        if (LAT.norm2(x) // 16) % 2 != (LAT.norm2(y) // 16) % 2:
            ok_welldef = False
    out["q_well_defined"] = ok_welldef

    # the type of a few named classes
    frame_point = tuple([8] + [0] * 23)
    out["frame_point_in_lambda"] = LAT.in_leech(frame_point)
    out["frame_point_type"] = type_of_point(frame_point)
    if full:
        fr = frame_of_class(class_of(frame_point))
        out["frame_size"] = len(fr)
        out["frame_is_orthogonal_pairs"] = _frame_is_orthogonal(fr)
        t2 = type2_class_table()
        out["type2_classes_found"] = len(t2)
        out["pair_census"] = pair_census()
    return out


def _frame_is_orthogonal(frame: Sequence[Sequence[int]]) -> bool:
    """48 vectors of norm 64 forming 24 orthogonal +- pairs."""
    if len(frame) != 48:
        return False
    if any(LAT.norm2(v) != 64 for v in frame):
        return False
    seen = set(tuple(v) for v in frame)
    for v in frame:
        if tuple(-a for a in v) not in seen:
            return False
    for i, v in enumerate(frame):
        for w in frame[i + 1:]:
            ip = LAT.inner(v, w)
            if ip not in (0, -64):
                return False
    return True


def main() -> None:
    print(banner("GLM-3  LEECH MOD 2  —  self-audit"))
    a = leech2_audit(full=True)
    w = a["witt"]
    print(f"\n[the F_2 quadratic space Lambda/2Lambda]")
    print(f"  hyperbolic planes            : {w['planes']}")
    print(f"  anisotropic planes           : {w['anisotropic_planes']}")
    print(f"  plus type                    : {w['plus_type']}")
    print(f"  singular classes             : {fmt_int(w['singular_count'])}")
    print(f"  q matches the lattice        : {a['q_matches_lattice']}")
    print(f"  B matches the lattice        : {a['b_matches_lattice']}")
    print(f"  q well defined mod 2 Lambda  : {a['q_well_defined']}")
    c = a["census"]
    print(f"\n[the class census]")
    print(f"  type 2 : {fmt_int(c['type2_classes'])}"
          f"   (from {fmt_int(c['type2_vectors'])} vectors / 2)")
    print(f"  type 3 : {fmt_int(c['type3_classes'])}"
          f"   (from {fmt_int(c['type3_vectors'])} vectors / 2)")
    print(f"  type 4 : {fmt_int(c['type4_classes'])}"
          f"   (from {fmt_int(c['type4_vectors'])} vectors / 48)")
    print(f"  total  : {fmt_int(c['total'])} = 2^24 : {c['closes']}")
    print(f"  matches the plus-type counts : {c['matches_plus_type']}")
    if "frame_size" in a:
        print(f"\n[frames and pairs]")
        print(f"  frame of the class of 8e_1   : {a['frame_size']} vectors,"
              f" orthogonal pairs = {a['frame_is_orthogonal_pairs']}")
        print(f"  type-2 classes enumerated    : {fmt_int(a['type2_classes_found'])}")
        print(f"  inner-product census         : "
              f"{ {k: fmt_int(v) for k, v in sorted(a['pair_census'].items())} }")
    print()


if __name__ == "__main__":
    main()
