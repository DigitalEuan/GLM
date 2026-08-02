"""
displacement_extrapolation.py — UBP substrate extrapolation via NoiseCellV3
============================================================================

The user's directive: "Lets go 'displacement-curve extrapolation' - could
be hiding there!"

The UBP substrate (NoiseCellV3) stores a base-12 digit with a known
displacement curve.  The curve maps k_bits → syndrome_displacement, and
the elastic_limit is the largest k where the curve is monotonic.

For ARC trigger→target extrapolation:
  - Each trigger colour T has a 24-bit Leech address
  - Each target colour C has a 24-bit Leech address
  - The "displacement" from T to C is the XOR difference in 24-bit space
  - We can encode this displacement as a NoiseCellV3 digit
  - The elastic_limit tells us how far we can extrapolate

Concretely:
  - For each (trigger, target) pair in train, compute the displacement
    vector (trigger_addr XOR target_addr)
  - Find the "average" displacement across all train pairs
  - For an unseen trigger, apply the average displacement to get the
    predicted target address, then decode to a colour

The displacement curve
----------------------
NoiseCellV3 has displacement_curve = {0:0, 1:4, 2:5, 3:6, 4:7, 5:6, 6:5,
7:4, 8:4, 9:4, 10:4, 11:4, 12:4} and elastic_limit = 12.

The curve is non-monotonic: it rises to 7 at k=4, then falls back to 4.
The elastic region (0-4) is where displacement is predictable; beyond
that, the curve plateaus.

For extrapolation:
  - If the unseen trigger's displacement from train triggers is within
    the elastic region (≤4 bits), we can predict the target
  - If it's beyond, we fall back to nearest-neighbour

Multi-curve extrapolation
-------------------------
Instead of one average displacement, we maintain a displacement curve
PER TRAIN PAIR.  For an unseen trigger, we find which train pair's
curve it fits best (smallest residual) and use that pair's target.

This is the "elastic extrapolation" — the substrate's known mathematical
properties bound our confidence in the extrapolation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import defaultdict, Counter
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask
from ubp_unified_v5 import (
    GOLAY_ENGINE, SubstrateLibrary, NoiseCellV3, ontological_position_to_vector,
)
from generative.hex_learner import address_cell, address_grid, _hamming_distance_int


# ══════════════════════════════════════════════════════════════════════════════
# Displacement curve extrapolation
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TriggerTargetPair:
    """A (trigger, target) pair from train, with their 24-bit addresses."""
    trigger_colour: int
    target_colour: int
    trigger_addr: int  # 24-bit Leech address of trigger
    target_addr: int   # 24-bit Leech address of target
    displacement: int  # trigger_addr XOR target_addr


@dataclass
class DisplacementCurve:
    """A displacement curve built from train (trigger, target) pairs.

    The curve maps a "distance from train" to a predicted target.
    The elastic_limit bounds how far we can extrapolate.
    """
    pairs: List[TriggerTargetPair] = field(default_factory=list)
    elastic_limit: int = 4  # from NoiseCellV3's elastic region (0-4)

    def add_pair(self, trigger_colour: int, target_colour: int,
                  grid_h: int, grid_w: int):
        """Add a (trigger, target) pair from train."""
        trigger_cell = address_cell(0, 0, trigger_colour, grid_h, grid_w)
        target_cell = address_cell(0, 0, target_colour, grid_h, grid_w)
        self.pairs.append(TriggerTargetPair(
            trigger_colour=trigger_colour,
            target_colour=target_colour,
            trigger_addr=trigger_cell.address_int,
            target_addr=target_cell.address_int,
            displacement=trigger_cell.address_int ^ target_cell.address_int,
        ))

    def extrapolate_target(self, unseen_trigger_colour: int,
                            grid_h: int, grid_w: int) -> Tuple[Optional[int], float]:
        """Extrapolate the target for an unseen trigger colour.

        Returns (predicted_target_colour, confidence).
        Confidence is high if the unseen trigger is within the elastic
        limit of a train trigger; low otherwise.

        Method:
          1. Compute the unseen trigger's 24-bit address
          2. Find the nearest train trigger (by Hamming distance)
          3. If within elastic_limit, apply that train trigger's displacement
          4. Decode the resulting address to a colour
          5. Confidence = 1 - (distance / elastic_limit)
        """
        unseen_cell = address_cell(0, 0, unseen_trigger_colour, grid_h, grid_w)
        unseen_addr = unseen_cell.address_int

        # Find nearest train trigger
        best_dist = 25
        best_pair = None
        for pair in self.pairs:
            dist = _hamming_distance_int(unseen_addr, pair.trigger_addr)
            if dist < best_dist:
                best_dist = dist
                best_pair = pair

        if best_pair is None:
            return None, 0.0

        # If within elastic limit, apply the displacement
        if best_dist <= self.elastic_limit:
            predicted_addr = unseen_addr ^ best_pair.displacement
            predicted_colour = _decode_address_to_colour(predicted_addr, grid_h, grid_w)
            confidence = 1.0 - (best_dist / max(self.elastic_limit, 1))
            return predicted_colour, confidence
        else:
            # Beyond elastic limit — fall back to nearest neighbour
            return best_pair.target_colour, 0.3

    def extrapolate_all(self, train_mapping: Dict[int, int],
                         unseen_triggers: Set[int],
                         grid_h: int, grid_w: int
                         ) -> Dict[int, Tuple[Optional[int], float]]:
        """Extrapolate targets for all unseen triggers.

        For triggers in train_mapping, use the known target (confidence 1.0).
        For unseen triggers, use displacement extrapolation.
        """
        result = {}
        for trigger in unseen_triggers:
            if trigger in train_mapping:
                result[trigger] = (train_mapping[trigger], 1.0)
            else:
                result[trigger] = self.extrapolate_target(trigger, grid_h, grid_w)
        return result


def _decode_address_to_colour(addr_int: int, grid_h: int, grid_w: int) -> int:
    """Decode a 24-bit Leech address back to a colour.

    The address encodes (colour, row, col, h, w).  To decode the colour,
    we need to find which colour's address is closest to the given address.
    """
    best_dist = 25
    best_colour = 0
    for colour in range(10):
        cell = address_cell(0, 0, colour, grid_h, grid_w)
        dist = _hamming_distance_int(addr_int, cell.address_int)
        if dist < best_dist:
            best_dist = dist
            best_colour = colour
    return best_colour


# ══════════════════════════════════════════════════════════════════════════════
# Build displacement curve from train
# ══════════════════════════════════════════════════════════════════════════════

def build_curve_from_train(task: ARCTask) -> DisplacementCurve:
    """Build a displacement curve from train pairs.

    For each train pair, find cells where the input colour changed.
    For each such cell, the trigger is a non-input-colour neighbour,
    and the target is the output colour.

    We collect (trigger, target) pairs across all train pairs.
    """
    curve = DisplacementCurve()

    # Find the grid dimensions (use the first train pair)
    if not task.train:
        return curve
    grid_h = task.train[0].input.height
    grid_w = task.train[0].input.width

    # Collect (trigger, target) pairs
    seen_pairs = set()
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old == new:
                    continue
                # Find trigger colours (non-old, non-zero neighbours)
                triggers = set()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                            n_colour = pair.input.cells[nr][nc]
                            if n_colour != old and n_colour != 0:
                                triggers.add(n_colour)
                # Record each (trigger, target) pair
                for t in triggers:
                    if (t, new) not in seen_pairs:
                        seen_pairs.add((t, new))
                        curve.add_pair(t, new, grid_h, grid_w)

    return curve


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Displacement-Curve Extrapolation self-test")
    print("=" * 60)

    from arc_loader import TrainPair, TestInput

    # Test: build a curve from train pairs
    # Pair 0: 7 next to 6 → 2
    # Pair 1: 7 next to 4 → 1
    inp1 = Grid([
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    out1 = Grid([
        [7, 7, 7, 7, 7],
        [7, 2, 7, 2, 7],
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    inp2 = Grid([
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [4, 7, 4, 7, 4],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    out2 = Grid([
        [7, 7, 7, 7, 7],
        [7, 1, 7, 1, 7],
        [4, 7, 4, 7, 4],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    task = ARCTask(name="extrap_test",
                   train=[TrainPair(input=inp1, output=out1),
                           TrainPair(input=inp2, output=out2)],
                   test=[TestInput(input=inp1, expected_output=out1)])

    curve = build_curve_from_train(task)
    print(f"\nBuilt curve with {len(curve.pairs)} (trigger, target) pairs:")
    for p in curve.pairs:
        print(f"  trigger {p.trigger_colour} (addr={hex(p.trigger_addr)}) "
              f"→ target {p.target_colour} (addr={hex(p.target_addr)}) "
              f"displacement={hex(p.displacement)}")

    # Extrapolate for unseen triggers
    print(f"\nExtrapolating for all 10 colours:")
    for trigger in range(10):
        if trigger == 0:
            continue
        target, conf = curve.extrapolate_target(trigger, 5, 5)
        in_train = any(p.trigger_colour == trigger for p in curve.pairs)
        marker = "TRAIN" if in_train else "EXTRAP"
        print(f"  trigger {trigger} → target {target} (conf={conf:.2f}) [{marker}]")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
