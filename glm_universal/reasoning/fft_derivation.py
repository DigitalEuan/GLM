"""``glm_universal.reasoning.fft_derivation`` -- the radix-2 Cooley-Tukey
FFT derived as a signal-flow graph (Phase 107,
``studies/DERIVATION_TWO_STUDY.md``).

Decimation in frequency
-----------------------
For ``N = 2M`` and ``W = W_N = e^{-2 pi i/N}``, split the *input* into its
first and second halves:

    ``X[k] = sum_{n<M} (x[n] + (-1)^k x[n+M]) W^{nk}``      (``W^{Mk} = (-1)^k``)

so the even outputs are the ``M``-point DFT of ``x[n] + x[n+M]`` and the odd
outputs the ``M``-point DFT of ``(x[n] - x[n+M]) W^n``:

    ``X[2r]   = sum_{n<M} (x[n] + x[n + N/2]) W_{N/2}^{rn}``
    ``X[2r+1] = sum_{n<M} (x[n] - x[n + N/2]) W_N^n W_{N/2}^{rn}``.

Repeating on each half gives ``log2 N`` stages of ``N/2`` butterflies
``(a, b) -> (a + b, (a - b) W^e)``, with the outputs in bit-reversed order.
Decimation in time splits the *outputs* instead (even- and odd-indexed
inputs), takes the inputs in bit-reversed order, and uses butterflies
``(a, b) -> (a + W^e b, a - W^e b)``.

:func:`derive_fft` builds the graph stage by stage; the column-3 script
re-applies it to symbolic inputs in ``Z[W]/(W^{N/2} + 1)`` -- exact integer
polynomial arithmetic, ``W^{N/2} = -1`` being the minimal relation of a
primitive ``N``-th root of unity when ``N`` is a power of two -- and compares
with the DFT entry by entry.  ``RequestProject/GLM/DerivationsTwo.lean``
proves the two split identities (``dif_even``, ``dif_odd``) over any
commutative ring.  Integers only (D7).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

__all__ = ["FFTError", "Butterfly", "FFT", "derive_fft", "bit_reverse",
           "SPLIT_EVEN", "SPLIT_ODD", "DIT_SPLIT"]

SPLIT_EVEN = ("X[2r] = sum_{n=0}^{N/2-1} (x[n] + x[n + N/2])*W_{N/2}^(r*n)")
SPLIT_ODD = ("X[2r+1] = sum_{n=0}^{N/2-1} (x[n] - x[n + N/2])*W_N^n*"
             "W_{N/2}^(r*n)")
DIT_SPLIT = ("X[k] = G[k] + W_N^k*H[k], X[k + N/2] = G[k] - W_N^k*H[k], with "
             "G, H the N/2-point DFTs of x[2n] and x[2n+1]")


class FFTError(Exception):
    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


@dataclass(frozen=True)
class Butterfly:
    stage: int
    top: int            # slot indices
    bottom: int
    twiddle: int        # exponent e of W_N^e


@dataclass
class FFT:
    n: int
    kind: str           # "dif" | "dit"
    stages: int
    butterflies: List[Butterfly]
    input_order: List[int]
    output_order: List[int]

    @property
    def nontrivial_twiddles(self) -> int:
        return sum(1 for b in self.butterflies if b.twiddle % self.n)

    def stage_lines(self) -> List[str]:
        out = []
        for s in range(1, self.stages + 1):
            bs = [b for b in self.butterflies if b.stage == s]
            tw = sorted({b.twiddle for b in bs})
            out.append(f"stage {s}: {len(bs)} butterflies, twiddles " +
                       ", ".join(f"W_{self.n}^{e}" for e in tw) + "; pairs " +
                       " ".join(f"({b.top},{b.bottom})" for b in bs[:8]) +
                       (" ..." if len(bs) > 8 else ""))
        return out


def bit_reverse(i: int, bits: int) -> int:
    out = 0
    for _ in range(bits):
        out = (out << 1) | (i & 1)
        i >>= 1
    return out


def derive_fft(n: int, kind: str = "dif") -> FFT:
    if n < 2 or n & (n - 1):
        raise FFTError("NOT_POWER_OF_TWO",
                       f"N = {n} is not a power of two: the radix-2 split "
                       f"needs N/2 at every stage")
    bits = n.bit_length() - 1
    fly: List[Butterfly] = []
    if kind == "dif":
        for s in range(1, bits + 1):
            size = n >> (s - 1)              # block length at this stage
            half = size // 2
            step = 1 << (s - 1)              # W_size^j = W_N^(j*step)
            for start in range(0, n, size):
                for j in range(half):
                    fly.append(Butterfly(s, start + j, start + j + half,
                                         j * step))
        order = [bit_reverse(i, bits) for i in range(n)]
        return FFT(n, kind, bits, fly, list(range(n)), order)
    for s in range(1, bits + 1):
        size = 1 << s
        half = size // 2
        step = n // size
        for start in range(0, n, size):
            for j in range(half):
                fly.append(Butterfly(s, start + j, start + j + half, j * step))
    order = [bit_reverse(i, bits) for i in range(n)]
    return FFT(n, kind, bits, fly, order, list(range(n)))
