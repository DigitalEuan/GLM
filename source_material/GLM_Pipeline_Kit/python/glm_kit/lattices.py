"""Higher lattice layers (Lean: GLMKit/Lattices.lean, GLMKit/Pless.lean)."""
from __future__ import annotations
from typing import List, Sequence


def qr23(x: int) -> int:
    """Quadratic character of F_23 with values in F_3 (0, 1, 2 = -1)."""
    x %= 23
    if x == 0:
        return 0
    return 1 if any((y * y) % 23 == x for y in range(1, 23)) else 2


def pless_S() -> List[List[int]]:
    """Bordered Jacobsthal matrix S of the Pless symmetry code C(23) over F_3 (entries 0,1,2)."""
    S = [[0] * 24 for _ in range(24)]
    for j in range(1, 24):
        S[0][j] = 1
        S[j][0] = 2
    for i in range(1, 24):
        for j in range(1, 24):
            S[i][j] = qr23(j - i)
    return S


def pless_generator() -> List[List[int]]:
    """[I_24 | S]: generator (and, since C(23) is self-dual, also parity-check) matrix."""
    S = pless_S()
    return [[1 if j == i else 0 for j in range(24)] + S[i] for i in range(24)]


def in_construction_A(x: Sequence[int], p: int, check: Sequence[Sequence[int]]) -> bool:
    """x in Z^n with (x mod p) in the code {c : check . c = 0 mod p}."""
    return all(sum(h * (v % p) for h, v in zip(row, x)) % p == 0 for row in check)


def in_lambda48(x: Sequence[int]) -> bool:
    """Construction A over the self-dual Pless code C(23) (length 48)."""
    return in_construction_A(x, 3, pless_generator())


def snap_fixes_lattice_points_warning() -> str:
    return ("For a linear code, D* = C + (B - A) of three lattice points is already a lattice "
            "point, so every snap that fixes lattice points is a no-op on it "
            "(Lean: snap_analogy_noop).  A 'richer snap' cannot change the answer.")
