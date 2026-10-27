"""Round 6 common code: exact Rule 30 generators and the control sequences.

Standard library only (numpy optional for loading the supplied 1M-bit file).
Conventions match the Lean package: cells are bits, Rule 30 is
new(c) = old(c-1) XOR (old(c) OR old(c+1)), the seed is a single black cell
at position 0, and centre bit n is bit n of rowStep^n(1), where
rowStep(r) = (r << 2) ^ ((r << 1) | r)   (Lean: `Compute.lean`, `centerCol_eq_fast`).
"""
from __future__ import annotations

import hashlib


def row_step(r: int) -> int:
    return (r << 2) ^ ((r << 1) | r)


def centre_column(n_bits: int) -> list[int]:
    """Exact centre column a(0..n_bits-1) of Rule 30 from the single-cell seed."""
    out = []
    r = 1
    for n in range(n_bits):
        out.append((r >> n) & 1)
        r = row_step(r)
    return out


def column_of_row(bits_right_to_left: dict[int, int], T: int) -> list[int]:
    """Centre column (position 0) for T steps of a finite row given as {position: bit}.

    Positions must be >= -T (we encode position p as bit p + T)."""
    r = 0
    for p, b in bits_right_to_left.items():
        if b:
            r |= 1 << (p + T)
    out = []
    for t in range(T):
        out.append((r >> (T + t)) & 1)  # bit k of rowStep^t holds position k - T - t
        r = row_step(r)
    return out


def column_inverse_row(target: list[int]) -> dict[int, int]:
    """A row white on (0, oo) whose centre column is `target` (Lean: `column_inverse_exists`).

    Cone separation: a(t)(0) = x(-t) XOR g_t(x(-t+1..t)), so x(-t) is forced step by step."""
    T = len(target)
    row: dict[int, int] = {}
    for t in range(T):
        row[-t] = 0
        g = column_of_row(row, t + 1)[t] if t > 0 else 0
        row[-t] = target[t] ^ g
    return row


# ----- control sequences ---------------------------------------------------

def periodic(n: int, pattern=(1, 0, 0, 1, 0, 1, 1)) -> list[int]:
    return [pattern[i % len(pattern)] for i in range(n)]


def biased_third(n: int) -> list[int]:
    return [1 if i % 3 == 0 else 0 for i in range(n)]


def champernowne_binary(n: int) -> list[int]:
    """Concatenation of 1, 10, 11, 100, ... (a deterministic normal sequence)."""
    out: list[int] = []
    k = 1
    while len(out) < n:
        out.extend(int(c) for c in bin(k)[2:])
        k += 1
    return out[:n]


def sha256_stream(n: int, key: bytes = b"rule30-round6") -> list[int]:
    """'Fair coin' control: SHA-256 in counter mode.  It is itself a fixed rule;
    it plays the role of independent fair bits for every observer considered here."""
    out: list[int] = []
    ctr = 0
    while len(out) < n:
        h = hashlib.sha256(key + ctr.to_bytes(8, "big")).digest()
        for byte in h:
            for j in range(8):
                out.append((byte >> (7 - j)) & 1)
        ctr += 1
    return out[:n]
