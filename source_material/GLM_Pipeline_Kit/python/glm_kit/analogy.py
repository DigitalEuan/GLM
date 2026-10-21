"""Analogy / operator primitives (Lean: GLMKit/Analogy.lean, GLMKit/Permutation.lean)."""
from __future__ import annotations
from typing import List, Sequence


def xor_analogy(a: int, b: int, c: int) -> int:
    """F_2 analogy A:B::C:D with D = C xor (A xor B).  Exact iff the displacement x xor f(x)
    is the same for A and C (`xor_analogy_exact_iff`); always exact for toggle / XOR-mask rules."""
    return c ^ a ^ b


def threshold_analogy(a: Sequence[int], b: Sequence[int], c: Sequence[int]) -> List[int]:
    """Iteration 8's Lambda_48 dual snap (kept for reference -- BUGGY): bit = [3(c+b-a) >= 2].
    On toggle it is exact only when A == C (`threshold_analogy_toggle_iff`)."""
    return [1 if 3 * (ci + bi - ai) >= 2 else 0 for ai, bi, ci in zip(a, b, c)]


def parity_analogy(a: Sequence[int], b: Sequence[int], c: Sequence[int]) -> List[int]:
    """FIX: decode the integer analogy by parity -- equals xor_analogy (`parity_decode_eq_xor`)."""
    return [(ci + bi - ai) % 2 for ai, bi, ci in zip(a, b, c)]


def permute_op(bits: Sequence[int], perm: Sequence[int]) -> List[int]:
    """FIX for DI1/DI3: out[i] = bits[perm[i]].  Permutations preserve weight, hence parity and
    the lattice layer (`wt_comp_perm`, `leech_layer_perm`)."""
    return [bits[perm[i]] for i in range(len(perm))]


def reflect_v_perm(h: int, w: int) -> List[int]:
    """Cell permutation of the vertical-axis mirror on a row-major h x w grid (`reflectV`)."""
    return [r * w + (w - 1 - c) for r in range(h) for c in range(w)]


def reflect_h_perm(h: int, w: int) -> List[int]:
    return [(h - 1 - r) * w + c for r in range(h) for c in range(w)]


def rotate180_perm(h: int, w: int) -> List[int]:
    return [(h - 1 - r) * w + (w - 1 - c) for r in range(h) for c in range(w)]


def shift_perm(h: int, w: int, dy: int, dx: int, rows: int | None = None) -> List[int]:
    """Cyclic shift by (dy, dx) of the top `rows` rows (default all); other rows stay fixed.
    out[r][c] = in[r - dy][c - dx]."""
    rows = h if rows is None else rows
    perm = []
    for r in range(h):
        for c in range(w):
            if r < rows:
                perm.append(((r - dy) % rows) * w + (c - dx) % w)
            else:
                perm.append(r * w + c)
    return perm


def permutation_library(h: int, w: int):
    """Candidate geometric cell permutations (the hypothesis space for permute_op)."""
    lib = {"identity": list(range(h * w)), "reflect_v": reflect_v_perm(h, w),
           "reflect_h": reflect_h_perm(h, w), "rotate180": rotate180_perm(h, w)}
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if (dy, dx) != (0, 0):
                lib[f"shift({dy},{dx})"] = shift_perm(h, w, dy, dx)
                lib[f"shift({dy},{dx})_keep_last_row"] = shift_perm(h, w, dy, dx, rows=h - 1)
    return lib


def consistent_permutations(pairs, h: int, w: int):
    """All library permutations consistent with every demo pair: a superposition of hypotheses
    that further demonstrations collapse."""
    return {name: p for name, p in permutation_library(h, w).items()
            if all(permute_op(x, p) == list(y) for x, y in pairs)}


def learn_permutation(pairs) -> List[int] | None:
    """Infer a cell permutation consistent with all demo pairs (x, y) (lists of bits), if one is
    determined uniquely by them; returns None if ambiguous or inconsistent."""
    n = len(pairs[0][0])
    perm = []
    for i in range(n):
        cands = [j for j in range(n) if all(y[i] == x[j] for x, y in pairs)]
        if len(cands) != 1:
            return None
        perm.append(cands[0])
    return perm
