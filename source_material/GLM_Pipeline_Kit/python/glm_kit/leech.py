"""Leech lattice layer (Lean: GLMKit/Leech.lean).

Integer model scaled by sqrt(8) (Conway & Sloane, SPLAG ch.4 s.11):
x in Z^24 is in Lambda_24 iff for some m in {0,1}
  * every x_i = m (mod 2),
  * {i : x_i = 2+m (mod 4)} is a Golay codeword,
  * sum(x) = 4m (mod 8).
"""
from __future__ import annotations
from typing import Callable, Sequence, Tuple

from . import golay

GLUE24 = (-3,) + (1,) * 23


def vec_to_mask(bits: Sequence[int]) -> int:
    m = 0
    for i, b in enumerate(bits):
        if b:
            m |= 1 << i
    return m


def word_to_bits(w: int, n: int = 24) -> Tuple[int, ...]:
    return tuple((w >> i) & 1 for i in range(n))


def in_leech_like(x: Sequence[int], is_codeword: Callable[[int], bool] = golay.is_codeword) -> bool:
    """Lean `LeechMem`: membership relative to any binary code (default: G24)."""
    s = sum(x)
    if all(v % 2 == 0 for v in x):
        return is_codeword(vec_to_mask([v % 4 == 2 for v in x])) and s % 8 == 0
    if all(v % 2 == 1 for v in x):
        return is_codeword(vec_to_mask([v % 4 == 3 for v in x])) and s % 8 == 4
    return False


def in_leech(x: Sequence[int]) -> bool:
    return in_leech_like(x)


def embed4(w: int) -> Tuple[int, ...]:
    """Iteration-3 embedding b -> 4b.  In Lambda_24 iff popcount(b) is even (`parity_wall`)."""
    return tuple(4 * b for b in word_to_bits(w))


def embed4_glue(w: int) -> Tuple[int, ...]:
    """Odd-coset candidate 4b + (-3,1^23).  Same rule (`parity_wall_glue`)."""
    return tuple(4 * b + g for b, g in zip(word_to_bits(w), GLUE24))


def embed8(w: int) -> Tuple[int, ...]:
    """FIX: b -> 8b is ALWAYS in Lambda_24 (`eight_mul_mem`) -- no escalation needed."""
    return tuple(8 * b for b in word_to_bits(w))


def hits_parity_wall(w: int) -> bool:
    """Exact replacement for the learned 'lattice head': the 4x embedding fails iff odd weight."""
    return golay.popcount(w) % 2 == 1


def junction_label(w: int) -> Tuple[int, int]:
    """Exact Lambda/2Lambda class of 4b (`junction_iff`): (Golay syndrome of b, wt(b) mod 4).

    Two 4x-embedded words are in the same junction iff their labels agree.
    """
    return golay.syndrome(w), golay.popcount(w) % 4


def same_class(x: Sequence[int], y: Sequence[int]) -> bool:
    """x = y (mod 2 Lambda): (x - y)/2 is an integer Leech vector."""
    d = [a - b for a, b in zip(x, y)]
    if any(v % 2 for v in d):
        return False
    return in_leech([v // 2 for v in d])
