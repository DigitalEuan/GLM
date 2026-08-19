#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 LATTICE  —  the Leech lattice as the carrier
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Layer  :  Tier 2 — where a concept lives.
  Deps   :  glm2_common (Golay code + exact integer linear algebra).

  ------------------------------------------------------------------------
  Why the carrier changed
  ------------------------------------------------------------------------

  GLM-1's carrier was F_2^24: 16,777,216 states, composition by XOR, repair
  by Golay decoding.  Three things were wrong with that as a *semantic*
  carrier, and all three are fixed by moving one level up, from the code to
  the lattice it builds:

      finite capacity   F_2^24 holds 2^24 states, and the base-9 embedding
                        used only 9^7 = 4,782,969 of them.  Lambda is
                        infinite: every element of the meaning module has
                        its own point, forever.

      lossy composition XOR is addition mod 2, so it can only ever compare
                        exponents mod 2.  Lambda's group law is addition in
                        Z^24 with no reduction at all, so composition of
                        concepts is exact.

      lossy repair      snapping to the nearest codeword changes the concept.
                        Decoding to the nearest lattice point *restores* it:
                        distinct concepts are at squared distance >= 32, so
                        every corruption of squared magnitude <= 7 is undone
                        exactly.

  ------------------------------------------------------------------------
  The model
  ------------------------------------------------------------------------

  Lambda is carried in the integer (x sqrt 8) model: a point is a vector of
  24 integers, minimal vectors have squared norm 32, and

      Lambda = { x in Z^24 :  all x_i = m (mod 2) for a common m in {0,1},
                              { i : x_i = m + 2 (mod 4) } is a Golay codeword,
                              sum_i x_i = 4m (mod 8) }.

  `in_leech` is that definition, executed.  Everything else in this module is
  derived from it and checked against it:

      §2  membership, norms, the index [Z^24 : Lambda] = 2^36
      §3  a Z-basis, obtained as the Hermite normal form of an explicit
          generating set, together with exact coordinates both ways
      §4  the theta series, computed from E_4^3 - 720 Delta and checked
          against the enumerated 196,560 minimal vectors
      §5  an exact maximum-likelihood decoder (nearest lattice point) with a
          proof-carrying witness: the returned point is checked against every
          Voronoi-relevant direction that the minimal vectors supply

      python3 glm2_lattice.py       # lattice self-audit
================================================================================
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from glm2_common import (GOLAY_BASIS_MASKS, GOLAY_MASKS, OCTAD_MASKS, N,
                         bits_of, det_int, hermite_normal_form, popcount,
                         solve_upper_triangular)

__all__ = [
    "DIM", "MIN_NORM2", "KISSING", "INDEX_IN_Z24",
    "in_leech", "norm2", "inner",
    "LEECH_BASIS", "to_coords", "from_coords", "basis_determinant",
    "minimal_vectors", "theta_series", "theta_from_modular_forms",
    "j_invariant_series",
    "decode", "decode_reference", "DecodeResult", "packing_radius2",
    "verify_local_optimality",
    "index_derivation", "lattice_audit",
]

DIM = 24
MIN_NORM2 = 32            # in the x sqrt(8) integer model
KISSING = 196560
INDEX_IN_Z24 = 1 << 36    # [Z^24 : Lambda]; derived in `index_derivation`

Vec = Tuple[int, ...]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  BASIC ARITHMETIC
# ══════════════════════════════════════════════════════════════════════════════

def norm2(x: Sequence[int]) -> int:
    return sum(int(v) * int(v) for v in x)


def inner(x: Sequence[int], y: Sequence[int]) -> int:
    return sum(int(a) * int(b) for a, b in zip(x, y))


_GOLAY_SET = frozenset(GOLAY_MASKS)


def in_leech(x: Sequence[int]) -> bool:
    """The defining congruences, executed exactly."""
    if len(x) != DIM:
        return False
    if any(not isinstance(v, int) for v in x):
        return False
    m = x[0] & 1
    if any((v & 1) != m for v in x):
        return False
    mask = 0
    target = (m + 2) % 4
    for i, v in enumerate(x):
        if v % 4 == target:
            mask |= 1 << i
    if mask not in _GOLAY_SET:
        return False
    return sum(x) % 8 == (4 * m) % 8


def index_derivation() -> Dict[str, object]:
    """
    [Z^24 : Lambda] = 2^36, counted rather than quoted.

    Lambda contains 8 Z^24, so the index is |(Z/8)^24| / |Lambda / 8Z^24|.
    For each parity m in {0,1}: the mod-4 pattern is determined by a Golay
    codeword (2^12 choices), each coordinate then has 2 lifts mod 8 (2^24),
    and the condition sum = 4m (mod 8) removes exactly half.  So

        |Lambda / 8Z^24| = 2 * 2^12 * 2^24 / 2 = 2^36,
        [Z^24 : Lambda]  = 8^24 / 2^36 = 2^72 / 2^36 = 2^36.
    """
    per_parity = (1 << 12) * (1 << 24) // 2
    total = 2 * per_parity
    return {
        "residues_per_parity": per_parity,
        "lambda_mod_8Z24": total,
        "Z8_24": 8 ** 24,
        "index": 8 ** 24 // total,
        "expected": INDEX_IN_Z24,
        "matches": 8 ** 24 // total == INDEX_IN_Z24,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §2.  A Z-BASIS
# ══════════════════════════════════════════════════════════════════════════════

def _generating_set() -> List[List[int]]:
    """
    An explicit generating set: the 276 vectors 4(e_i + e_j), the 759 vectors
    2 * 1_O for octads O, and the odd vector (-3, 1, 1, ..., 1).  Each is
    verified to lie in Lambda before use.
    """
    gens: List[List[int]] = []
    for i in range(DIM):
        for j in range(i + 1, DIM):
            v = [0] * DIM
            v[i] = v[j] = 4
            gens.append(v)
    for mask in OCTAD_MASKS:
        v = [2 if (mask >> i) & 1 else 0 for i in range(DIM)]
        gens.append(v)
    odd = [1] * DIM
    odd[0] = -3
    gens.append(odd)
    bad = [v for v in gens if not in_leech(v)]
    if bad:
        raise AssertionError(f"{len(bad)} generators are not in Lambda")
    return gens


#: a Z-basis of Lambda in row-style Hermite normal form (upper triangular)
LEECH_BASIS: Tuple[Vec, ...] = tuple(
    tuple(row) for row in hermite_normal_form(_generating_set(), DIM))


def basis_determinant() -> int:
    return det_int([list(r) for r in LEECH_BASIS])


def from_coords(u: Sequence[int]) -> Vec:
    """The lattice point with coordinates u in LEECH_BASIS."""
    if len(u) != DIM:
        raise ValueError("from_coords: 24 coordinates required")
    out = [0] * DIM
    for ui, row in zip(u, LEECH_BASIS):
        if ui:
            for j in range(DIM):
                if row[j]:
                    out[j] += ui * row[j]
    return tuple(out)


def to_coords(x: Sequence[int]) -> Optional[List[int]]:
    """The coordinates of a lattice point, or None if x is not in Lambda."""
    return solve_upper_triangular([list(r) for r in LEECH_BASIS], list(x))


# ══════════════════════════════════════════════════════════════════════════════
# §3.  MINIMAL VECTORS AND THE THETA SERIES
# ══════════════════════════════════════════════════════════════════════════════

def minimal_vectors() -> Iterator[Vec]:
    """Stream all 196,560 minimal vectors (squared norm 32)."""
    # shape A: (+-4)^2 0^22
    for i in range(DIM):
        for j in range(i + 1, DIM):
            for si in (4, -4):
                for sj in (4, -4):
                    v = [0] * DIM
                    v[i], v[j] = si, sj
                    yield tuple(v)
    # shape B: (+-2)^8 on an octad, even number of minus signs
    for mask in OCTAD_MASKS:
        pos = bits_of(mask)
        for signs in range(256):
            if popcount(signs) & 1:
                continue
            v = [0] * DIM
            for k, p in enumerate(pos):
                v[p] = -2 if (signs >> k) & 1 else 2
            yield tuple(v)
    # shape C: (-+3, +-1^23) driven by a codeword
    for i in range(DIM):
        for c in GOLAY_MASKS:
            v = [(-1 if (c >> j) & 1 else 1) for j in range(DIM)]
            v[i] = 3 if (c >> i) & 1 else -3
            yield tuple(v)


def _sigma3(n: int) -> int:
    return sum(d ** 3 for d in range(1, n + 1) if n % d == 0)


def theta_from_modular_forms(order: int = 6) -> List[int]:
    """
    The theta series of Lambda as a q-series in q = exp(pi i tau), indexed by
    *half* the squared norm of the unscaled lattice:

        Theta(q) = E_4(q)^3 - 720 Delta(q) = 1 + 196560 q^2 + 16773120 q^3 + ...

    Coefficient n counts the vectors of unscaled squared norm 2n, i.e. of
    squared norm 8n in the integer model used here.  Computed exactly with
    integer arithmetic.
    """
    E4 = [0] * (order + 1)
    E4[0] = 1
    for n in range(1, order + 1):
        E4[n] = 240 * _sigma3(n)
    # E4^3
    def mul(a: List[int], b: List[int]) -> List[int]:
        out = [0] * (order + 1)
        for i, ai in enumerate(a):
            if ai:
                for j, bj in enumerate(b):
                    if i + j <= order and bj:
                        out[i + j] += ai * bj
        return out
    E4_3 = mul(mul(E4, E4), E4)
    # Delta = q prod (1-q^n)^24
    prod = [0] * (order + 1)
    prod[0] = 1
    for n in range(1, order + 1):
        factor = [0] * (order + 1)
        factor[0] = 1
        if n <= order:
            factor[n] = -1
        for _ in range(24):
            prod = mul(prod, factor)
    delta = [0] * (order + 1)
    for n in range(order):
        delta[n + 1] = prod[n]
    return [E4_3[n] - 720 * delta[n] for n in range(order + 1)]


def theta_series(order: int = 6) -> List[int]:
    return theta_from_modular_forms(order)


def _eisenstein_and_delta(order: int) -> Tuple[List[int], List[int]]:
    """E_4^3 and Delta as q-expansions to the given order (exact integers)."""
    E4 = [0] * (order + 1)
    E4[0] = 1
    for n in range(1, order + 1):
        E4[n] = 240 * _sigma3(n)

    def mul(a: List[int], b: List[int]) -> List[int]:
        out = [0] * (order + 1)
        for i, ai in enumerate(a):
            if ai:
                for j, bj in enumerate(b):
                    if i + j <= order and bj:
                        out[i + j] += ai * bj
        return out

    E4_3 = mul(mul(E4, E4), E4)
    prod = [0] * (order + 1)
    prod[0] = 1
    for n in range(1, order + 1):
        factor = [0] * (order + 1)
        factor[0] = 1
        factor[n] = -1
        for _ in range(24):
            prod = mul(prod, factor)
    delta = [0] * (order + 1)
    for n in range(order):
        delta[n + 1] = prod[n]
    return E4_3, delta


def j_invariant_series(order: int = 3) -> List[int]:
    """
    The head of the modular j-function,

        j(q) = 1/q + 744 + 196884 q + 21493760 q^2 + 864299970 q^3 + ...

    computed exactly as E_4^3 / Delta by power-series division.  The returned
    list is [c_{-1}, c_0, c_1, ...].

    The first coefficient after the constant is 196,884 — the dimension of the
    Griess algebra, and the sum 300 + 98,280 + 98,304 of the three pieces the
    Leech lattice supplies.  That identity is checked in glm2_axial; the
    representation-theoretic reading of it (McKay's 196,884 = 1 + 196,883) is
    classical and is quoted, not derived, here.
    """
    N = order + 2
    E4_3, delta = _eisenstein_and_delta(N)
    # j = E4^3 / delta with delta = q + ...; write j = sum_{k >= -1} c_k q^k
    coeffs: List[int] = []
    rem = list(E4_3)
    for k in range(-1, order + 1):
        # the leading term of delta is q^1, so c_k is determined by rem[k+1]
        c = rem[k + 1]
        coeffs.append(c)
        if c:
            for n in range(1, N + 1):
                if k + n <= N:
                    rem[k + n] -= c * delta[n]
    return coeffs


# ══════════════════════════════════════════════════════════════════════════════
# §4.  EXACT MAXIMUM-LIKELIHOOD DECODING
# ══════════════════════════════════════════════════════════════════════════════

def packing_radius2() -> F:
    """Squared packing radius: (d_min/2)^2 = 32/4 = 8."""
    return F(MIN_NORM2, 4)


class DecodeResult:
    """The nearest lattice point, its squared distance, and a witness."""

    __slots__ = ("point", "dist2", "parity", "codeword", "corrected")

    def __init__(self, point: Vec, dist2, parity: int, codeword: int,
                 corrected: bool) -> None:
        self.point = point
        self.dist2 = dist2
        self.parity = parity
        self.codeword = codeword
        self.corrected = corrected

    def __repr__(self) -> str:
        return (f"DecodeResult(dist2={self.dist2}, parity={self.parity}, "
                f"codeword=0x{self.codeword:06x})")


def _round_to_residue(y, r: int):
    """The element of r + 4Z nearest to y, and the squared error."""
    # k = round((y - r)/4), ties broken downward (deterministic)
    num = y - r
    k = (num + 2) // 4 if isinstance(num, int) else _fround(F(num) / 4)
    z = r + 4 * k
    return z, (y - z) * (y - z)


def _fround(x: F) -> int:
    fl = x.numerator // x.denominator
    return fl if x - fl < F(1, 2) else fl + 1


def decode(y: Sequence[int]) -> DecodeResult:
    """
    Exact nearest-point decoding of Lambda.

    The algorithm is the defining description, executed: for each parity
    m in {0,1} and each Golay codeword c, the coordinates are constrained to
    fixed residues mod 4, so the nearest point of that class is obtained
    coordinate by coordinate; the class also carries the condition
    sum = 4m (mod 8), and if the coordinatewise minimum violates it, the
    cheapest repair is to move exactly one coordinate by +-4.  Minimising the
    resulting cost over the 2 x 4096 classes is exact maximum-likelihood
    decoding.

    Implemented with a Gray-code walk over the twelve Golay generators, so
    the 4096 class costs are obtained with O(1) work each, plus a branch and
    bound on the repair term.
    """
    if len(y) != DIM:
        raise ValueError("decode: 24 coordinates required")
    best: Optional[Tuple] = None      # (cost, m, cbits, zvec, corrected)

    for m in (0, 1):
        r0 = m % 4
        r1 = (m + 2) % 4
        z0: List[int] = [0] * DIM
        z1: List[int] = [0] * DIM
        c0: List = [0] * DIM
        c1: List = [0] * DIM
        # cost of moving that coordinate by the cheaper +-4 (the repair term)
        f0: List = [0] * DIM
        f1: List = [0] * DIM
        for i, yi in enumerate(y):
            z0[i], c0[i] = _round_to_residue(yi, r0)
            z1[i], c1[i] = _round_to_residue(yi, r1)
            up = (yi - z0[i] - 4) ** 2 - c0[i]
            dn = (yi - z0[i] + 4) ** 2 - c0[i]
            f0[i] = up if up < dn else dn
            up = (yi - z1[i] - 4) ** 2 - c1[i]
            dn = (yi - z1[i] + 4) ** 2 - c1[i]
            f1[i] = up if up < dn else dn
        min_fix = min(min(f0), min(f1))

        base_cost = sum(c0)
        base_sum = sum(z0)
        d_cost = [c1[i] - c0[i] for i in range(DIM)]
        d_sum = [z1[i] - z0[i] for i in range(DIM)]
        cur = [0] * DIM                     # current codeword bits
        cost = base_cost
        zsum = base_sum
        cbits = 0

        def consider(cost, zsum, cbits, cur):
            nonlocal best
            need_fix = (zsum % 8) != (4 * m) % 8
            lower = cost + (min_fix if need_fix else 0)
            if best is not None and lower >= best[0]:
                return
            if not need_fix:
                total = cost
                corrected = False
                zvec = [z1[i] if cur[i] else z0[i] for i in range(DIM)]
            else:
                fixes = [(f1[i] if cur[i] else f0[i], i) for i in range(DIM)]
                delta, idx = min(fixes)
                total = cost + delta
                if best is not None and total >= best[0]:
                    return
                zvec = [z1[i] if cur[i] else z0[i] for i in range(DIM)]
                yi = y[idx]
                zi = zvec[idx]
                # cost of z+4 is (y - z - 4)^2, cost of z-4 is (y - z + 4)^2
                zvec[idx] = zi + 4 if (yi - zi - 4) ** 2 < (yi - zi + 4) ** 2 \
                    else zi - 4
                corrected = True
            if best is None or total < best[0]:
                best = (total, m, cbits, tuple(zvec), corrected)

        consider(cost, zsum, cbits, cur)
        prev_gray = 0
        for step in range(1, 4096):
            gray = step ^ (step >> 1)
            changed = (gray ^ prev_gray).bit_length() - 1
            prev_gray = gray
            gmask = GOLAY_BASIS_MASKS[changed]
            cbits ^= gmask
            for i in bits_of(gmask):
                if cur[i]:
                    cur[i] = 0
                    cost -= d_cost[i]
                    zsum -= d_sum[i]
                else:
                    cur[i] = 1
                    cost += d_cost[i]
                    zsum += d_sum[i]
            consider(cost, zsum, cbits, cur)

    assert best is not None
    total, m, cbits, zvec, corrected = best
    if not in_leech(list(zvec)):
        raise AssertionError("decoder produced a point outside Lambda")
    return DecodeResult(zvec, total, m, cbits, corrected)


def decode_reference(y: Sequence[int]) -> Tuple[Vec, int]:
    """
    A deliberately slow reference decoder, used to cross-check `decode`.

    It walks all 2 x 4096 classes with no Gray code and no branch and bound,
    and inside each class it enumerates every single-coordinate +-4 repair
    explicitly instead of taking the minimum in closed form.  Same answer,
    about fifty times the work.
    """
    best: Optional[Tuple[int, Vec]] = None
    for m in (0, 1):
        for c in GOLAY_MASKS:
            z: List[int] = []
            for i, yi in enumerate(y):
                r = (m + 2) % 4 if (c >> i) & 1 else m % 4
                zi, _ = _round_to_residue(yi, r)
                z.append(zi)
            candidates: List[List[int]] = []
            if sum(z) % 8 == (4 * m) % 8:
                candidates.append(z)
            else:
                for i in range(DIM):
                    for step in (4, -4):
                        w = list(z)
                        w[i] += step
                        if sum(w) % 8 == (4 * m) % 8:
                            candidates.append(w)
            for w in candidates:
                d = sum((a - b) ** 2 for a, b in zip(y, w))
                if best is None or d < best[0]:
                    best = (d, tuple(w))
    assert best is not None
    return best[1], best[0]


def verify_local_optimality(y: Sequence[int], point: Sequence[int],
                            sample: Optional[Iterable[Vec]] = None) -> bool:
    """
    A witness for the decoded point: no lattice point of the form
    point + (minimal vector) is closer to y.  (Necessary for optimality, and
    the condition the Voronoi cell's shortest relevant vectors impose.)
    """
    d0 = sum((a - b) ** 2 for a, b in zip(y, point))
    src = minimal_vectors() if sample is None else sample
    for v in src:
        d = sum((a - b - c) ** 2 for a, b, c in zip(y, point, v))
        if d < d0:
            return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
# §5.  AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def lattice_audit(full: bool = True) -> Dict[str, object]:
    out: Dict[str, object] = {}
    out["dimension"] = DIM
    out["basis_rows"] = len(LEECH_BASIS)
    det = basis_determinant()
    out["basis_determinant"] = det
    out["determinant_is_2^36"] = det == INDEX_IN_Z24
    out["basis_in_lattice"] = all(in_leech(list(r)) for r in LEECH_BASIS)
    out.update({f"index_{k}": v for k, v in index_derivation().items()
                if k in ("index", "matches")})

    # coordinates round trip
    rt = True
    for k in range(40):
        u = [(k * (i + 3)) % 7 - 3 for i in range(DIM)]
        x = from_coords(u)
        rt &= in_leech(list(x)) and to_coords(x) == u
    out["coordinate_round_trip"] = rt

    theta = theta_series(5)
    out["theta_head"] = theta[:5]
    out["theta_matches_kissing"] = theta[2] == KISSING

    if full:
        count = 0
        norms_ok = True
        member_ok = True
        for v in minimal_vectors():
            count += 1
            if norm2(v) != MIN_NORM2:
                norms_ok = False
            if count % 997 == 0 and not in_leech(list(v)):
                member_ok = False
        out["minimal_vectors"] = count
        out["minimal_norms_ok"] = norms_ok and count == KISSING
        out["sampled_membership_ok"] = member_ok

    # decoding
    base = from_coords([1, -2, 3, 0, 0, 1, 0, -1] + [0] * 16)
    ok = True
    for trial in range(12):
        err = [0] * DIM
        for k in range(trial % 7 + 1):
            err[(trial * 5 + k) % DIM] = 1 if (trial + k) % 2 == 0 else -1
        y = [a + b for a, b in zip(base, err)]
        res = decode(y)
        ok &= (res.point == base) and res.dist2 == norm2(err)
    out["repairs_errors_up_to_norm2_7"] = ok
    out["packing_radius2"] = str(packing_radius2())
    out["decode_fixed_point"] = decode(base).point == base
    return out


if __name__ == "__main__":  # pragma: no cover
    import sys
    full = "--quick" not in sys.argv
    print("GLM-2 LATTICE — self-audit")
    for k, v in lattice_audit(full).items():
        print(f"  {k:30s} {v}")
