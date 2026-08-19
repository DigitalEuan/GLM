#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM EXACT INTEGER LINEAR ALGEBRA  —  Smith normal form over Z
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  support for Tier 3 (the reasoner).
  Deps   :  standard library only.

  The reasoner has to answer questions of the form

      "which integer powers of these quantities produce that quantity?"

  i.e. solve  A x = t  over the integers, where the columns of A are the
  dimension vectors of the inputs and t is the dimension vector of the target.
  Over Q this is Gaussian elimination; over Z it needs the Smith normal form,
  which also hands us an integer basis of the kernel — and the kernel of A is
  precisely the set of dimensionless (Buckingham-Pi) groups of the inputs.

  Everything is exact integer arithmetic on small matrices (7 x k), so the
  naive algorithms below are entirely adequate and stay readable.

      python3 glm_linalg.py       # runs a randomised self-check
================================================================================
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Sequence, Tuple

__all__ = ["Matrix", "identity", "matmul", "matvec", "transpose",
           "smith_normal_form", "solve_integer_system", "kernel_basis",
           "solve_rational_system"]

Matrix = List[List[int]]


# ══════════════════════════════════════════════════════════════════════════════
#  basic matrix helpers
# ══════════════════════════════════════════════════════════════════════════════

def identity(n: int) -> Matrix:
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def transpose(A: Sequence[Sequence[int]]) -> Matrix:
    return [list(col) for col in zip(*A)] if A else []


def matmul(A: Sequence[Sequence[int]], B: Sequence[Sequence[int]]) -> Matrix:
    inner = len(B)
    cols = len(B[0]) if B else 0
    return [[sum(A[i][k] * B[k][j] for k in range(inner)) for j in range(cols)]
            for i in range(len(A))]


def matvec(A: Sequence[Sequence[int]], v: Sequence[int]) -> List[int]:
    return [sum(a * b for a, b in zip(row, v)) for row in A]


# ══════════════════════════════════════════════════════════════════════════════
#  Smith normal form
# ══════════════════════════════════════════════════════════════════════════════

def smith_normal_form(A_in: Sequence[Sequence[int]]) -> Tuple[Matrix, Matrix, Matrix, int]:
    """
    Compute D, U, V, rank with  U . A . V = D,  D diagonal, U and V unimodular.

    The divisibility chain d_1 | d_2 | ... is NOT enforced (it is irrelevant for
    solving systems and for extracting a kernel basis), so this is really a
    "diagonalisation over Z" — every statement made about it below holds.
    """
    A: Matrix = [list(row) for row in A_in]
    m = len(A)
    n = len(A[0]) if m else 0
    U = identity(m)
    V = identity(n)

    def swap_rows(i: int, j: int) -> None:
        A[i], A[j] = A[j], A[i]
        U[i], U[j] = U[j], U[i]

    def swap_cols(i: int, j: int) -> None:
        for row in A:
            row[i], row[j] = row[j], row[i]
        for row in V:
            row[i], row[j] = row[j], row[i]

    def add_row(target: int, source: int, factor: int) -> None:
        if factor == 0:
            return
        A[target] = [a - factor * b for a, b in zip(A[target], A[source])]
        U[target] = [a - factor * b for a, b in zip(U[target], U[source])]

    def add_col(target: int, source: int, factor: int) -> None:
        if factor == 0:
            return
        for row in A:
            row[target] -= factor * row[source]
        for row in V:
            row[target] -= factor * row[source]

    def negate_row(i: int) -> None:
        A[i] = [-a for a in A[i]]
        U[i] = [-a for a in U[i]]

    t = 0
    while t < min(m, n):
        # pivot: smallest nonzero absolute value in the remaining submatrix
        pivot: Optional[Tuple[int, int]] = None
        best = 0
        for i in range(t, m):
            for j in range(t, n):
                a = abs(A[i][j])
                if a and (pivot is None or a < best):
                    pivot, best = (i, j), a
        if pivot is None:
            break
        swap_rows(t, pivot[0])
        swap_cols(t, pivot[1])
        while True:
            # clear the column below the pivot
            changed = False
            for i in range(t + 1, m):
                if A[i][t]:
                    add_row(i, t, A[i][t] // A[t][t])
                    if A[i][t]:
                        swap_rows(t, i)
                        changed = True
            # clear the row right of the pivot
            for j in range(t + 1, n):
                if A[t][j]:
                    add_col(j, t, A[t][j] // A[t][t])
                    if A[t][j]:
                        swap_cols(t, j)
                        changed = True
            if not changed and all(A[i][t] == 0 for i in range(t + 1, m)) \
                    and all(A[t][j] == 0 for j in range(t + 1, n)):
                break
        if A[t][t] < 0:
            negate_row(t)
        t += 1

    rank = sum(1 for i in range(min(m, n)) if A[i][i] != 0)
    return A, U, V, rank


def kernel_basis(A: Sequence[Sequence[int]]) -> Matrix:
    """
    An integer basis of  {x in Z^n : A x = 0},  returned as a list of vectors.

    For a dimension matrix A whose columns are the dimensions of a set of
    quantities, this is exactly a complete set of independent Buckingham-Pi
    groups, and its size is  n - rank(A)  (the Pi theorem).
    """
    if not A or not A[0]:
        return []
    _D, _U, V, rank = smith_normal_form(A)
    n = len(A[0])
    return [[V[i][j] for i in range(n)] for j in range(rank, n)]


def solve_integer_system(A: Sequence[Sequence[int]],
                         t: Sequence[int]) -> Optional[Tuple[List[int], Matrix]]:
    """
    Solve  A x = t  over Z.

    Returns (particular solution, kernel basis) or None when there is no
    integer solution.  Together they describe the complete solution set

        { x0 + sum_i c_i k_i  :  c in Z^(n - rank) }.
    """
    if not A or not A[0]:
        return None
    D, U, V, rank = smith_normal_form(A)
    m, n = len(A), len(A[0])
    c = matvec(U, list(t))
    y = [0] * n
    for i in range(rank):
        d = D[i][i]
        if c[i] % d:
            return None                      # rational but not integral
        y[i] = c[i] // d
    for i in range(rank, m):
        if c[i] != 0:
            return None                      # inconsistent
    x = matvec(V, y)
    return x, kernel_basis(A)


def solve_rational_system(A: Sequence[Sequence[int]],
                          t: Sequence[int]) -> Optional[List[Fraction]]:
    """
    Solve  A x = t  over Q by Gaussian elimination, taking all free variables
    to be zero.  Returns None when the system is inconsistent.

    This is the "fractional powers allowed" version of the deduction problem:
    speed = sqrt(energy/mass) is a rational solution (exponents 1/2, -1/2) but
    not an integer one, and the reasoner must be able to tell the two apart.
    """
    m = len(A)
    n = len(A[0]) if m else 0
    aug: List[List[Fraction]] = [
        [Fraction(A[i][j]) for j in range(n)] + [Fraction(t[i])] for i in range(m)
    ]
    pivots: List[int] = []
    row = 0
    for col in range(n):
        piv = next((r for r in range(row, m) if aug[r][col] != 0), None)
        if piv is None:
            continue
        aug[row], aug[piv] = aug[piv], aug[row]
        lead = aug[row][col]
        aug[row] = [x / lead for x in aug[row]]
        for r in range(m):
            if r != row and aug[r][col] != 0:
                factor = aug[r][col]
                aug[r] = [x - factor * y for x, y in zip(aug[r], aug[row])]
        pivots.append(col)
        row += 1
        if row == m:
            break
    for r in range(row, m):
        if aug[r][n] != 0 and all(aug[r][c] == 0 for c in range(n)):
            return None                      # inconsistent
    x = [Fraction(0)] * n
    for r, col in enumerate(pivots):
        x[col] = aug[r][n]
    return x


# ══════════════════════════════════════════════════════════════════════════════
#  self-check
# ══════════════════════════════════════════════════════════════════════════════

def _self_check(trials: int = 400) -> Tuple[int, int]:
    """Randomised (but deterministic) check of SNF, kernel and solver."""
    state = 12345
    def rnd(lo: int, hi: int) -> int:
        nonlocal state
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        return lo + state % (hi - lo + 1)

    ok = 0
    for _ in range(trials):
        m = rnd(1, 5)
        n = rnd(1, 5)
        A = [[rnd(-4, 4) for _ in range(n)] for _ in range(m)]
        D, U, V, rank = smith_normal_form(A)
        assert matmul(matmul(U, A), V) == D, "U A V = D failed"
        assert all(D[i][j] == 0 for i in range(m) for j in range(n) if i != j), \
            "D not diagonal"
        for k in kernel_basis(A):
            assert all(x == 0 for x in matvec(A, k)), "kernel vector not in kernel"
        x_true = [rnd(-3, 3) for _ in range(n)]
        t = matvec(A, x_true)
        sol = solve_integer_system(A, t)
        assert sol is not None, "solvable system reported unsolvable"
        x0, _ker = sol
        assert matvec(A, x0) == t, "particular solution wrong"
        xq = solve_rational_system(A, t)
        assert xq is not None, "solvable system reported inconsistent over Q"
        assert [sum(Fraction(a) * b for a, b in zip(row, xq)) for row in A] == \
            [Fraction(v) for v in t], "rational solution wrong"
        ok += 1
    return ok, trials


if __name__ == "__main__":
    passed, total = _self_check()
    print(f"glm_linalg self-check: {passed}/{total} random systems verified "
          f"(SNF identity, kernel membership, integer solving)")
