"""
The Snap — the base operation of the GLM.

Per user: "Our information comes from before and after a snap (when the snap
is used correctly). That provides the Syndrome TAX which calculates the cost
for NRCI — the base operation. It is about what happens during these processes
that matters so much."

THE SNAP PROCESS:
  1. BEFORE: a raw 24-bit pattern (the input, with history σ ≠ 0)
  2. THE SNAP: correct to the nearest Golay codeword (the MOG grammar)
  3. AFTER: a lawful 24-bit codeword (σ = 0, no history)
  4. THE DELTA: what bits changed (the correction)
  5. THE SYNDROME TAX: the cost of the snap (syndrome weight before)

The information IS this process. The (before, after, tax) triple captures:
  - What the input was (before)
  - What it snapped to (after — the lawful interpretation)
  - How much it cost (tax — the syndrome weight)

The snap is now FIXED (weight ≤ 4, full covering radius). Every 24-bit
pattern snaps to a codeword.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from fractions import Fraction

from .body import Body, Y, Z_STAR, B
from .data_object import DataObject


@dataclass
class SnapResult:
    """The result of a snap — the information triple (before, after, tax)."""
    # BEFORE: the raw input pattern
    before: DataObject
    before_int: int
    before_syndrome_weight: int       # σ(v) before snap — the history
    before_nrci: float                # NRCI before snap

    # THE SNAP: the correction
    correctable: bool                 # always True now (weight ≤ 4)
    correction_distance: int          # how many bits changed (0-4)
    correction_bits: List[int]        # which bits were flipped

    # AFTER: the lawful codeword
    after: DataObject
    after_int: int
    after_syndrome_weight: int        # should be 0 (lawful)
    after_nrci: float                 # NRCI after snap

    # THE SYNDROME TAX: the cost of the snap
    syndrome_tax: int                 # = before_syndrome_weight
    nrci_delta: float                 # after_nrci - before_nrci (usually negative)

    def describe(self) -> str:
        lines = [
            f"BEFORE:  int={self.before_int} syndrome_w={self.before_syndrome_weight} NRCI={self.before_nrci:.4f}",
            f"SNAP:    correctable={self.correctable} distance={self.correction_distance} bits_flipped={self.correction_bits}",
            f"AFTER:   int={self.after_int} syndrome_w={self.after_syndrome_weight} NRCI={self.after_nrci:.4f}",
            f"TAX:     syndrome_tax={self.syndrome_tax} nrci_delta={self.nrci_delta:.4f}",
        ]
        return "\n".join(lines)


class Snap:
    """The base operation: snap a pattern to the nearest Golay codeword.

    This IS the base operation of the GLM. Everything else builds on it.
    """

    def __init__(self, body: Body):
        self.body = body
        self.golay = body.golay

    def snap(self, v: DataObject) -> SnapResult:
        """The base operation. Snap v to the nearest codeword.

        Returns the full information triple: (before, after, tax).
        """
        # BEFORE
        before = v
        before_int = v.to_int()
        before_sw = self.body.syndrome_weight(v.bits)
        before_nrci = float(self.body.nrci(v.bits))

        # THE SNAP (now fixed — weight ≤ 4)
        snapped_bits, meta = self.golay.snap_to_codeword(v.bits)
        after = DataObject(bits=snapped_bits)
        after_int = after.to_int()
        after_sw = self.body.syndrome_weight(snapped_bits)
        after_nrci = float(self.body.nrci(snapped_bits))

        # THE DELTA
        correction_bits = [i for i, (a, b) in enumerate(zip(v.bits, snapped_bits)) if a != b]
        correction_distance = len(correction_bits)

        # THE TAX
        syndrome_tax = before_sw
        nrci_delta = after_nrci - before_nrci

        return SnapResult(
            before=before, before_int=before_int,
            before_syndrome_weight=before_sw, before_nrci=before_nrci,
            correctable=meta["correctable"],
            correction_distance=meta["anchor_distance"],
            correction_bits=correction_bits,
            after=after, after_int=after_int,
            after_syndrome_weight=after_sw, after_nrci=after_nrci,
            syndrome_tax=syndrome_tax, nrci_delta=nrci_delta,
        )

    def snap_many(self, vectors: List[DataObject]) -> List[SnapResult]:
        """Snap multiple vectors."""
        return [self.snap(v) for v in vectors]
