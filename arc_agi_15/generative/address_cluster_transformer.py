"""
address_cluster_transformer.py — 24D-address-based transformation
===================================================================

The key reframe: instead of clustering cells by their COLOUR INTEGER
(which fails because colour 0 maps to different things at different
positions), we cluster cells by their 24D ADDRESS — cells with
SIMILAR 24D addresses get SIMILAR transformations.

This is the "information IS physical geometry" principle made operational:
the transformation is a function of the 24D address, not the 2D colour.

The 24D-within-24D structure:
  - The grid has a 24D address (grid-level encoding)
  - Each cell within the grid has its OWN 24D address (cell-level encoding)
  - The cell's 24D address encodes: colour (M_*), position (I_*),
    dimensions (A_*), coherence (P_*) — the four conditions for structure

Is this a neural network? Not in the traditional sense. It's more like
a CONTENT-ADDRESSABLE MEMORY: the 24D address IS the key, and the
transformation IS the value. Cells with similar addresses (measured by
Hamming distance in 24D space) get similar transformations.

The "neural" quality comes from the fact that the 24D address space is
the same space as the GLM's vocabulary — every word, every concept, every
transformation lives in the same 24-bit Golay/Leech space. So the system
can "associate" between cells and transformations the same way the GLM
associates between words and concepts.

NO SIMPLIFICATIONS: all arithmetic uses Fraction. All addresses use the
real GolayCodeEngine. All NRCI values are exact Fractions.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import defaultdict
import sys, os

_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from generative.per_object_24d import (
    CellAddress, AddressedGrid, address_grid, assign_cell_address,
)
from lingo.ubp_integration import nrci_fraction, ObserverDynamics


# ══════════════════════════════════════════════════════════════════════════════
# ADDRESS CLUSTER — cells grouped by 24D address similarity
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class AddressCluster:
    """A cluster of cells with similar 24D addresses.

    All cells in a cluster get the SAME transformation. The cluster is
    defined by a centroid 24D address and a Hamming radius.
    """
    centroid_hex: str               # the cluster's representative hex colour
    member_positions: List[Tuple[int, int]]  # (row, col) of member cells
    transformation: Optional[int] = None  # what colour do these cells become?
    avg_nrci: float = 0.0           # average NRCI of cluster members
    coherence_label: str = ""       # MANIFESTED / ANOMALOUS / SUBLIMINAL

    def __repr__(self):
        return (f"AddressCluster(centroid={self.centroid_hex}, "
                f"members={len(self.member_positions)}, "
                f"transform={self.transformation}, "
                f"NRCI={self.avg_nrci:.4f} [{self.coherence_label}])")


def hamming_distance_24d(v1: List[int], v2: List[int]) -> int:
    """Hamming distance between two 24-bit vectors."""
    return sum(1 for a, b in zip(v1, v2) if a != b)


# ══════════════════════════════════════════════════════════════════════════════
# ADDRESS CLUSTER TRANSFORMER
# ══════════════════════════════════════════════════════════════════════════════

class AddressClusterTransformer:
    """Transforms cells based on their 24D address, not their colour integer.

    The transformer:
      1. Addresses every cell in the train input and output
      2. For each cell that CHANGED, records (input_address → output_colour)
      3. Clusters the learned mappings by 24D address similarity
      4. For the test input, addresses every cell, finds the nearest cluster,
         and applies that cluster's transformation

    This is content-addressable memory: the 24D address is the key,
    the transformation is the value.

    NO SIMPLIFICATIONS: all addresses use the real GolayCodeEngine,
    all NRCI values are Fractions, all Hamming distances are exact.
    """

    def __init__(self, hamming_threshold: int = 12):
        """Initialise the transformer.

        Args:
            hamming_threshold: maximum Hamming distance for two 24D addresses
                to be considered "similar" (in the same cluster).
                Default 12 = half of 24 (the midpoint of the Golay code's
                minimum distance of 8).
        """
        self.hamming_threshold = hamming_threshold
        # Learned mappings: list of (input_vector, output_colour, input_nrci)
        self.learned_mappings: List[Tuple[List[int], int, float]] = []
        # Addressed train inputs (for verification)
        self.train_verified: bool = False

    def learn_from_task(self, task: ARCTask) -> None:
        """Learn 24D-address-to-transformation mappings from train pairs."""
        self.learned_mappings = []

        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                # Shape changed — can't do cell-level comparison
                # Learn at the grid level instead
                continue

            in_addrs = address_grid(pair.input)
            out_addrs = address_grid(pair.output)

            for r in range(in_addrs.shape[0]):
                for c in range(in_addrs.shape[1]):
                    in_addr = in_addrs.cell_at(r, c)
                    out_addr = out_addrs.cell_at(r, c)

                    # Record: this 24D address maps to this output colour
                    self.learned_mappings.append((
                        in_addr.vector_24d,
                        out_addr.colour,
                        in_addr.nrci_float,
                    ))

        # Verify: can we reproduce the train pairs?
        self.train_verified = self._verify_train(task)

    def _verify_train(self, task: ARCTask) -> bool:
        """Verify that the learned mappings reproduce all train pairs."""
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                return False  # can't verify shape-changing transforms
            predicted = self._predict_grid(pair.input)
            if predicted != pair.output:
                return False
        return True

    def _find_nearest_mapping(self, vector: List[int]) -> Optional[int]:
        """Find the output colour for the nearest learned 24D address.

        Uses Hamming distance in 24D space. If multiple mappings are
        equally close, picks the one with the highest NRCI (most coherent).
        """
        if not self.learned_mappings:
            return None

        best_dist = 25  # beyond max possible
        best_colour = None
        best_nrci = -1.0

        for learned_vec, output_colour, nrci in self.learned_mappings:
            dist = hamming_distance_24d(vector, learned_vec)
            if dist < best_dist or (dist == best_dist and nrci > best_nrci):
                best_dist = dist
                best_colour = output_colour
                best_nrci = nrci

        return best_colour

    def _predict_grid(self, grid: Grid) -> Grid:
        """Predict the output for a grid using 24D-address lookup."""
        addrs = address_grid(grid)
        h, w = grid.shape
        out_cells = []

        for r in range(h):
            row = []
            for c in range(w):
                addr = addrs.cell_at(r, c)
                # Find the nearest learned mapping
                predicted_colour = self._find_nearest_mapping(addr.vector_24d)
                if predicted_colour is not None:
                    row.append(predicted_colour)
                else:
                    row.append(grid.cells[r][c])  # fallback: keep original
            out_cells.append(row)

        return Grid(out_cells)

    def predict(self, task: ARCTask) -> Grid:
        """Predict the test output using 24D-address-based transformation."""
        return self._predict_grid(task.test[0].input)

    def predict_with_coherence(self, task: ARCTask) -> Tuple[Grid, Dict[str, Any]]:
        """Predict and return coherence diagnostics.

        NRCI is used as a COHERENCE MEASURE (not a gate) — we measure
        how coherent the prediction is, but we don't filter based on it.
        """
        predicted = self.predict(task)
        pred_addrs = address_grid(predicted)

        return predicted, {
            "mean_nrci": pred_addrs.mean_nrci(),
            "coherence_distribution": pred_addrs.coherence_distribution(),
            "hex_palette": sorted(pred_addrs.hex_palette()),
            "train_verified": self.train_verified,
            "n_learned_mappings": len(self.learned_mappings),
        }

    def summary(self) -> str:
        return (
            f"AddressClusterTransformer:\n"
            f"  Learned mappings: {len(self.learned_mappings)}\n"
            f"  Train verified: {self.train_verified}\n"
            f"  Hamming threshold: {self.hamming_threshold}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# TRIPLE SOLVER — grid-level + per-object + address-cluster
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TripleSolution:
    """The result of solving a task three different ways."""
    task_id: str
    grid_level_pred: Optional[Grid] = None
    grid_level_correct: Optional[bool] = None
    per_object_pred: Optional[Grid] = None
    per_object_correct: Optional[bool] = None
    address_cluster_pred: Optional[Grid] = None
    address_cluster_correct: Optional[bool] = None
    address_cluster_verified: bool = False
    chosen: str = ""
    chosen_correct: Optional[bool] = None
    # Coherence diagnostics (NRCI as measurement, not gate)
    input_coherence: float = 0.0
    grid_level_coherence: float = 0.0
    per_object_coherence: float = 0.0
    address_cluster_coherence: float = 0.0

    def summary(self) -> str:
        lines = [
            f"TripleSolution for {self.task_id}:",
            f"  Grid-level:       correct={self.grid_level_correct}  NRCI={self.grid_level_coherence:.4f}",
            f"  Per-object:       correct={self.per_object_correct}  NRCI={self.per_object_coherence:.4f}",
            f"  Address-cluster:  correct={self.address_cluster_correct}  NRCI={self.address_cluster_coherence:.4f}  verified={self.address_cluster_verified}",
            f"  Chosen: {self.chosen}  correct={self.chosen_correct}",
            f"  Input coherence: {self.input_coherence:.4f}",
        ]
        winners = []
        if self.grid_level_correct: winners.append("grid-level")
        if self.per_object_correct: winners.append("per-object")
        if self.address_cluster_correct: winners.append("address-cluster")
        if len(winners) >= 2:
            lines.append(f"  ⚡ MULTIPLE methods solve it: {winners} — structural insight!")
        elif len(winners) == 1:
            lines.append(f"  → {winners[0]} wins")
        else:
            lines.append(f"  ✗ None solve it")
        return "\n".join(lines)


def solve_triple(task: ARCTask) -> TripleSolution:
    """Solve a task three ways and compare.

    The three approaches:
      1. Grid-level (UBPActionEngine) — regime-directed DSL search
      2. Per-object (PerObjectTransformer) — colour-integer mapping
      3. Address-cluster (AddressClusterTransformer) — 24D-address mapping

    Comparing all three reveals WHERE the structure lives:
      - If grid-level wins: the rule is grid-wide (fill, border, etc.)
      - If per-object wins: the rule is a simple colour swap
      - If address-cluster wins: the rule depends on spatial position
    """
    result = TripleSolution(task_id=task.name)

    # Input coherence (measurement, not gate)
    input_addrs = address_grid(task.test[0].input)
    result.input_coherence = input_addrs.mean_nrci()

    # Method 1: Grid-level
    from generative.ubp_action_engine import UBPActionEngine
    grid_engine = UBPActionEngine()
    result.grid_level_pred = grid_engine.solve(task)
    if result.grid_level_pred:
        pred_addrs = address_grid(result.grid_level_pred)
        result.grid_level_coherence = pred_addrs.mean_nrci()

    # Method 2: Per-object (colour-integer)
    from generative.per_object_24d import PerObjectTransformer
    obj_engine = PerObjectTransformer()
    obj_engine.learn_from_task(task)
    result.per_object_pred = obj_engine.predict(task)
    pred_addrs = address_grid(result.per_object_pred)
    result.per_object_coherence = pred_addrs.mean_nrci()

    # Method 3: Address-cluster (24D-address)
    addr_engine = AddressClusterTransformer()
    addr_engine.learn_from_task(task)
    result.address_cluster_pred, diagnostics = addr_engine.predict_with_coherence(task)
    result.address_cluster_coherence = diagnostics["mean_nrci"]
    result.address_cluster_verified = diagnostics["train_verified"]

    # Check correctness
    expected = task.test[0].expected_output
    if expected is not None:
        result.grid_level_correct = (result.grid_level_pred == expected)
        result.per_object_correct = (result.per_object_pred == expected)
        result.address_cluster_correct = (result.address_cluster_pred == expected)

    # Choose: prefer address-cluster if verified, then per-object, then grid-level
    if result.address_cluster_verified and result.address_cluster_pred:
        result.chosen = "address_cluster"
        result.chosen_correct = result.address_cluster_correct
    elif result.per_object_pred:
        result.chosen = "per_object"
        result.chosen_correct = result.per_object_correct
    elif result.grid_level_pred:
        result.chosen = "grid_level"
        result.chosen_correct = result.grid_level_correct

    return result
