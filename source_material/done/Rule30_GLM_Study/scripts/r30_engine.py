"""
Rule 30 bit-packed center-column engine.

Generates the center-column sequence of Wolfram's Rule 30 elementary cellular
automaton, starting from a single live cell, using a bit-packed uint64 numpy
representation with active-region tracking. The active region at step t spans
[center - t, center + t], so we only operate on the words actually in use,
which keeps the per-step cost proportional to t rather than to N. Total work
is O(N^2 / 64) word operations.

Reference: Wolfram, "Announcing the Rule 30 Prize Problems", 2019.
https://writings.stephenwolfram.com/2019/10/announcing-the-rule-30-prizes/

The Rule 30 update rule, in closed form, is:

    new[i] = L[i-1] XOR (L[i] OR L[i+1])

where L is the previous row. This is verified against the canonical truth
table for rule number 30 (binary 00011110).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np


# --- Rule 30 verification ----------------------------------------------------

RULE_TABLE = np.array(
    [0, 1, 1, 1, 1, 0, 0, 0], dtype=np.uint8
)  # new value for (L,C,R) -> bit index (L<<2)|(C<<1)|R


def rule30_naive(row: np.ndarray) -> np.ndarray:
    """Reference implementation on a uint8 array with zero boundary."""
    padded = np.zeros(row.size + 2, dtype=np.uint8)
    padded[1:-1] = row
    L = padded[:-2]
    C = padded[1:-1]
    R = padded[2:]
    idx = (L << 2) | (C << 1) | R
    return RULE_TABLE[idx]


def _check_truth_table() -> None:
    """Sanity check: confirm the closed form new = L XOR (C OR R)."""
    for L in (0, 1):
        for C in (0, 1):
            for R in (0, 1):
                idx = (L << 2) | (C << 1) | R
                expected = RULE_TABLE[idx]
                got = L ^ (C | R)
                assert expected == got, (L, C, R, expected, got)


_check_truth_table()


# --- Bit-packed engine -------------------------------------------------------

def rule30_center_column_packed(N: int, save_path: str | None = None,
                                 progress_every: int = 0) -> np.ndarray:
    """Generate the first N cells of Rule 30's center column.

    Returns a uint8 array of length N (values 0 or 1). The first cell is 1.

    Implementation:
      - Allocate a uint64 buffer of size (2N+1+63)//64 words, large enough to
        hold the full visible triangle.
      - The initial cell lives at bit position N (the center).
      - At each step, only the active region [N-t, N+t] is nonzero, so we slice
        the buffer to those words and run three numpy ops on the slice.
      - The new center bit (at position N) is read off and stored.

    Time:   O(N^2 / 64) word ops, ~seconds for N=1e6, ~minutes for N=1e7.
    Memory: O(N/8) bytes for the row buffer.
    """
    n_bits = 2 * N + 1
    n_words = (n_bits + 63) // 64
    # Add 2 guard words at each end so the boundary-carry logic is clean.
    buf = np.zeros(n_words + 4, dtype=np.uint64)
    base = 2  # logical word 0 sits at buffer index 2

    center_bit = N % 64
    center_word = N // 64

    # Plant the initial live cell at bit position N of the logical row.
    buf[base + center_word] = np.uint64(1) << np.uint64(center_bit)

    center_col = np.zeros(N, dtype=np.uint8)
    center_col[0] = 1

    t0 = time.time()
    for t in range(1, N):
        # Active region: columns [N-t, N+t] -> bits [N-t, N+t].
        lo_bit = N - t
        hi_bit = N + t
        lo_word = lo_bit // 64
        hi_word = hi_bit // 64

        # Include the left/right boundary words (for carries) at indices
        # lo_word-1 and hi_word+1, but stay inside the buffer.
        a = max(base + lo_word - 1, 0)
        b = min(base + hi_word + 2, buf.size)

        sub = buf[a:b]
        # In bit-index space, "left neighbor of bit b" is bit (b-1) and
        # "right neighbor of bit b" is bit (b+1).
        #
        # left[p] bit i = old at bit (p*64 + i - 1):
        #   for i=0  : bit (p*64 - 1) = old[p-1] bit 63  (MSB of previous word)
        #   for i>=1 : bit (p*64 + i - 1) = old[p] bit (i-1)  (shift LEFT by 1)
        # So: left[p] = (old[p] << 1) | (MSB of old[p-1]).
        carries_left = np.zeros_like(sub)
        carries_left[1:] = sub[:-1] >> np.uint64(63)
        left = (sub << np.uint64(1)) | carries_left

        # right[p] bit i = old at bit (p*64 + i + 1):
        #   for i=63 : bit (p*64 + 64) = old[p+1] bit 0  (LSB of next word)
        #   for i<63 : bit (p*64 + i + 1) = old[p] bit (i+1)  (shift RIGHT by 1)
        # So: right[p] = (old[p] >> 1) | (LSB of old[p+1] << 63).
        carries_right = np.zeros_like(sub)
        carries_right[:-1] = (sub[1:] & np.uint64(1)) << np.uint64(63)
        right = (sub >> np.uint64(1)) | carries_right

        new_sub = left ^ (sub | right)

        buf[a:b] = new_sub

        # Read off the center bit (still at logical position N).
        cw = base + center_word
        center_col[t] = np.uint8((buf[cw] >> np.uint64(center_bit)) & np.uint64(1))

        if progress_every and t % progress_every == 0:
            elapsed = time.time() - t0
            rate = t / elapsed if elapsed else 0.0
            eta = (N - t) / rate if rate else 0.0
            print(f"  [r30] t={t:>10d}/{N}  elapsed={elapsed:6.1f}s  "
                  f"rate={rate:8.1f}/s  eta={eta:6.1f}s", flush=True)

    if save_path:
        np.save(save_path, center_col)
        print(f"  [r30] saved {N} center column cells to {save_path} "
              f"({os.path.getsize(save_path)} bytes)", flush=True)

    return center_col


# --- Standalone smoke test ---------------------------------------------------

def _smoke() -> None:
    """Verify against OEIS A051023: Middle column of rule-30 1-D CA.

    Wolfram 2019 ("Announcing the Rule 30 Prize Problems") and OEIS A051023
    list the first 100 terms (Wolfram's published CellularAutomaton[30] output,
    cross-checked against the OEIS A051023 b-file from Zumkeller/Karttunen).

    OEIS A051023 also notes that the same sequence is the middle column of
    rule 86 (the mirror image of rule 30), which is consistent with the fact
    that the center column of any 1D CA is invariant under L<->R mirroring.
    """
    # Verbatim from OEIS A051023 (Antti Karttunen's b-file, n=0..100000):
    expected = np.array(
        [1,1,0,1,1,1,0,0,1,1,0,0,0,1,0,1,1,0,0,1,0,0,1,1,1,0,1,0,1,1,1,0,
         0,1,1,1,0,1,0,1,0,1,1,0,0,0,0,1,1,0,0,1,0,1,0,1,1,0,1,0,1,0,1,1,
         1,1,1,1,0,0,0,0,1,1,1,1,0,0,0,1,0,1,0,1,1,1,0,0,0,0,0,1,0,0,1,0,
         1,1,0,0,0,1,1], dtype=np.uint8
    )  # length 102
    small = rule30_center_column_packed(100)
    print("First 32 center-column cells:")
    print("  got: ", "".join(str(b) for b in small[:32]))
    print("  expt:", "".join(str(b) for b in expected[:32]))
    assert small.shape == (100,) and expected.shape[0] >= 100
    assert np.array_equal(small, expected[:100]), \
        f"Mismatch:\n  got: {list(small)}\n  expt: {list(expected[:100])}"
    print(f"  [smoke] first 100 cells match OEIS A051023 exactly. OK.")


if __name__ == "__main__":
    _smoke()
