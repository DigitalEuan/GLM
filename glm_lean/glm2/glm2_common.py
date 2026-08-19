#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 COMMON  —  shared substrate access and exact integer linear algebra
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Deps   :  the first-generation modules in ../glm (Golay code, M24), which
            GLM-2 reuses rather than re-deriving.

  What lives here
  ---------------
    §1  path shim + re-exports:  GOLAY, GOLAY_MASKS, OCTAD_MASKS, M24_GENERATORS
    §2  exact integer linear algebra the lattice layer needs:
        Hermite normal form, determinant, triangular solve, matrix inverse
        over Q, and a rational linear solver.

  Everything is exact: Python ints and fractions.Fraction only.
================================================================================
"""

from __future__ import annotations

import os
import sys
from fractions import Fraction as F
from typing import Iterable, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_GLM1 = os.path.join(os.path.dirname(_HERE), "glm")
if _GLM1 not in sys.path:
    sys.path.insert(0, _GLM1)

from glm_substrate import GOLAY                    # noqa: E402
from glm_m24 import M24_GENERATORS                 # noqa: E402

__all__ = [
    "GOLAY", "GOLAY_MASKS", "GOLAY_BASIS_MASKS", "OCTAD_MASKS",
    "M24_GENERATORS", "N", "popcount", "bits_of",
    "hermite_normal_form", "det_int", "solve_upper_triangular",
    "mat_inverse_q", "matvec", "matmul", "identity",
]

N = 24


def popcount(x: int) -> int:
    return bin(x).count("1")


def bits_of(mask: int, n: int = N) -> List[int]:
    return [i for i in range(n) if (mask >> i) & 1]


def _mask(word: Sequence[int]) -> int:
    return sum(1 << i for i, b in enumerate(word) if b)


#: all 4096 Golay codewords as 24-bit masks (bit i = coordinate i)
GOLAY_MASKS: Tuple[int, ...] = tuple(_mask(w) for w in GOLAY.all_codewords())

#: the twelve generator rows of G = [I | B], as masks
GOLAY_BASIS_MASKS: Tuple[int, ...] = tuple(_mask(row) for row in GOLAY.G)

#: the 759 octads, as masks
OCTAD_MASKS: Tuple[int, ...] = tuple(_mask(w) for w in GOLAY.octads())


# ══════════════════════════════════════════════════════════════════════════════
# §2.  EXACT INTEGER LINEAR ALGEBRA
# ══════════════════════════════════════════════════════════════════════════════

Matrix = List[List[int]]


def identity(n: int) -> Matrix:
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def matmul(A: Sequence[Sequence[int]], B: Sequence[Sequence[int]]) -> Matrix:
    n, k, m = len(A), len(B), len(B[0])
    return [[sum(A[i][t] * B[t][j] for t in range(k)) for j in range(m)]
            for i in range(n)]


def matvec(A: Sequence[Sequence[int]], v: Sequence[int]) -> List[int]:
    return [sum(a * x for a, x in zip(row, v)) for row in A]


def hermite_normal_form(rows: Sequence[Sequence[int]], ncols: int) -> Matrix:
    """
    Row-style Hermite normal form of the lattice spanned by `rows`.

    Returns a list of at most `ncols` rows in upper-triangular echelon form
    with positive pivots and entries above a pivot reduced modulo it.  The
    returned rows are a Z-basis of the same lattice.
    """
    work = [list(r) for r in rows if any(r)]
    basis: List[List[int]] = []
    col = 0
    while col < ncols and work:
        # find a row with a nonzero entry in this column
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
    # reduce entries above each pivot
    for i in range(len(basis) - 1, -1, -1):
        pc = next(j for j in range(ncols) if basis[i][j] != 0)
        piv = basis[i][pc]
        for k in range(i):
            q = basis[k][pc] // piv
            if q:
                for j in range(ncols):
                    basis[k][j] -= q * basis[i][j]
    return basis


def det_int(A: Sequence[Sequence[int]]) -> int:
    """Exact determinant of a square integer matrix (fraction-free)."""
    n = len(A)
    M = [[F(x) for x in row] for row in A]
    det = F(1)
    for i in range(n):
        piv = None
        for r in range(i, n):
            if M[r][i] != 0:
                piv = r
                break
        if piv is None:
            return 0
        if piv != i:
            M[i], M[piv] = M[piv], M[i]
            det = -det
        det *= M[i][i]
        inv = 1 / M[i][i]
        for r in range(i + 1, n):
            if M[r][i]:
                f = M[r][i] * inv
                for c in range(i, n):
                    M[r][c] -= f * M[i][c]
    assert det.denominator == 1
    return int(det)


def solve_upper_triangular(basis: Sequence[Sequence[int]],
                           target: Sequence[int]) -> Optional[List[int]]:
    """
    Solve  u * basis = target  for integer u, where `basis` is the row-style
    HNF (upper triangular, square).  Returns None when target is not in the
    lattice.
    """
    n = len(basis)
    rhs = list(target)
    u = [0] * n
    for i in range(n):
        pc = next(j for j in range(len(rhs)) if basis[i][j] != 0)
        if rhs[pc] % basis[i][pc] != 0:
            return None
        q = rhs[pc] // basis[i][pc]
        u[i] = q
        if q:
            for j in range(len(rhs)):
                rhs[j] -= q * basis[i][j]
    return u if all(x == 0 for x in rhs) else None


def mat_inverse_q(A: Sequence[Sequence[int]]) -> List[List[F]]:
    """Exact inverse over Q of a square integer matrix."""
    n = len(A)
    M = [[F(x) for x in row] + [F(1 if i == j else 0) for j in range(n)]
         for i, row in enumerate(A)]
    for i in range(n):
        piv = next((r for r in range(i, n) if M[r][i] != 0), None)
        if piv is None:
            raise ValueError("matrix is singular")
        M[i], M[piv] = M[piv], M[i]
        inv = 1 / M[i][i]
        M[i] = [x * inv for x in M[i]]
        for r in range(n):
            if r != i and M[r][i]:
                f = M[r][i]
                M[r] = [a - f * b for a, b in zip(M[r], M[i])]
    return [row[n:] for row in M]


if __name__ == "__main__":  # pragma: no cover
    print("GLM-2 COMMON — shared substrate")
    print(f"  Golay codewords      {len(GOLAY_MASKS)}")
    print(f"  Golay basis rows     {len(GOLAY_BASIS_MASKS)}")
    print(f"  octads               {len(OCTAD_MASKS)}")
    print(f"  M24 generators       {len(M24_GENERATORS)}")
    B = hermite_normal_form([[2, 0], [1, 3]], 2)
    print(f"  HNF sample           {B}  det {det_int(B)}")
