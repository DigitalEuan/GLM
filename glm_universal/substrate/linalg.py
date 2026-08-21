"""Exact integer / F_2 linear algebra used by the GLM-3+ substrate.

Every routine in this module is exact.  There is no floating-point arithmetic
anywhere: integer quantities are :class:`int`, rational quantities are
:class:`fractions.Fraction`.  This is a hard requirement of the substrate --
the Leech lattice congruences, the Golay syndromes and the 2-adic digit planes
are all statements about exact residues, and a single float would make them
unfalsifiable.

Contents
--------
``popcount`` / ``bits_of`` / ``mask_of``
    Bit-mask helpers for the 24 coordinates.
``hermite_normal_form``
    Row-style HNF, used once to turn a generating set of the Leech lattice
    into an upper-triangular Z-basis.
``det_int``
    Exact determinant (over Q, with an integrality assertion).
``solve_upper_triangular``
    Coordinates of a point in an upper-triangular Z-basis, or ``None`` when
    the point is outside the lattice.
``f2_independent`` / ``f2_rank``
    Gaussian elimination over F_2 on integers-as-bit-vectors.

Ported and refined from ``glm_lean/glm2/glm2_common.py``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence

__all__ = [
    "popcount",
    "bits_of",
    "mask_of",
    "hermite_normal_form",
    "det_int",
    "solve_upper_triangular",
    "f2_independent",
    "f2_rank",
]

Matrix = List[List[int]]


# ---------------------------------------------------------------------------
# bit helpers
# ---------------------------------------------------------------------------

def popcount(x: int) -> int:
    """Number of set bits in a non-negative integer."""
    return bin(x).count("1")


def bits_of(mask: int, n: int = 24) -> List[int]:
    """Ascending list of set-bit positions of ``mask`` below ``n``."""
    return [i for i in range(n) if (mask >> i) & 1]


def mask_of(positions: Sequence[int]) -> int:
    """The bit mask with exactly ``positions`` set."""
    m = 0
    for p in positions:
        m |= 1 << int(p)
    return m


# ---------------------------------------------------------------------------
# integer lattice linear algebra
# ---------------------------------------------------------------------------

def hermite_normal_form(rows: Sequence[Sequence[int]], ncols: int) -> Matrix:
    """Row-style Hermite normal form of the lattice spanned by ``rows``.

    Parameters
    ----------
    rows
        Generating set of a sublattice of ``Z^ncols``.
    ncols
        Ambient dimension.

    Returns
    -------
    list of list of int
        At most ``ncols`` rows in upper-triangular echelon form with positive
        pivots and entries above a pivot reduced modulo it.  The rows are a
        Z-basis of the same lattice.
    """
    work = [list(r) for r in rows if any(r)]
    basis: Matrix = []
    col = 0
    while col < ncols and work:
        pivot_rows = [r for r in work if r[col] != 0]
        if not pivot_rows:
            col += 1
            continue
        while len(pivot_rows) > 1:
            pivot_rows.sort(key=lambda r: abs(r[col]))
            p = pivot_rows[0]
            for r in pivot_rows[1:]:
                q = r[col] // p[col]
                for j in range(col, ncols):
                    r[j] -= q * p[j]
            pivot_rows = [r for r in pivot_rows if r[col] != 0]
        p = pivot_rows[0]
        if p[col] < 0:
            for j in range(ncols):
                p[j] = -p[j]
        basis.append(p)
        work = [r for r in work if r is not p and any(r[col:])]
        col += 1
    for i in range(len(basis) - 1, -1, -1):
        pc = next(j for j in range(ncols) if basis[i][j] != 0)
        piv = basis[i][pc]
        for k in range(i):
            q = basis[k][pc] // piv
            if q:
                for j in range(ncols):
                    basis[k][j] -= q * basis[i][j]
    return basis


def det_int(matrix: Sequence[Sequence[int]]) -> int:
    """Exact determinant of a square integer matrix, computed over Q."""
    n = len(matrix)
    m = [[Fraction(x) for x in row] for row in matrix]
    det = Fraction(1)
    for i in range(n):
        piv: Optional[int] = None
        for r in range(i, n):
            if m[r][i] != 0:
                piv = r
                break
        if piv is None:
            return 0
        if piv != i:
            m[i], m[piv] = m[piv], m[i]
            det = -det
        det *= m[i][i]
        inv = 1 / m[i][i]
        for r in range(i + 1, n):
            if m[r][i]:
                f = m[r][i] * inv
                for c in range(i, n):
                    m[r][c] -= f * m[i][c]
    if det.denominator != 1:
        raise AssertionError("det_int: non-integral determinant")
    return int(det)


def solve_upper_triangular(basis: Sequence[Sequence[int]],
                           target: Sequence[int]) -> Optional[List[int]]:
    """Solve ``u * basis = target`` over Z for an upper-triangular ``basis``.

    Returns ``None`` when ``target`` is not in the lattice spanned by
    ``basis`` -- which is the membership test the Leech substrate relies on.
    """
    n = len(basis)
    rhs = [int(t) for t in target]
    u = [0] * n
    for i in range(n):
        pc = next(j for j in range(len(rhs)) if basis[i][j] != 0)
        if rhs[pc] % basis[i][pc] != 0:
            return None
        q = rhs[pc] // basis[i][pc]
        u[i] = q
        if q:
            row = basis[i]
            for j in range(len(rhs)):
                if row[j]:
                    rhs[j] -= q * row[j]
    return u if all(x == 0 for x in rhs) else None


# ---------------------------------------------------------------------------
# F_2 linear algebra on integers-as-bit-vectors
# ---------------------------------------------------------------------------

def f2_independent(vectors: Sequence[int]) -> List[int]:
    """A maximal F_2-independent subset of ``vectors`` (bit-vector ints).

    Returns the original vectors that were accepted as pivots, in input
    order, so the result spans the same F_2 subspace.
    """
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


def f2_rank(vectors: Sequence[int]) -> int:
    """Dimension of the F_2 span of ``vectors``."""
    return len(f2_independent(vectors))
