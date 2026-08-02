"""
pattern_learner.py — learn-on-the-fly pattern induction
=========================================================

v0.3 key insight: instead of hardcoding 30+ DSL operators, LEARN the
transformation from the train pairs. The GLM's ContinuousLearner
(GLM24) does exactly this for natural language — we adapt the same
pattern to ARC grids.

The learner:
  1. ENCODES each train pair's input and output as 24-bit hex colours
     (using GLM18's vector_to_colour — every 24-bit vector IS a #RRGGBB)
  2. COMPUTES the "transformation colour" = output_colour XOR input_colour
     (bitwise diff in the 24-bit colour space — a native GLM operation)
  3. RECORDS co-occurrence patterns: which input-features map to which
     output-features, building a CRG (Concept Relation Graph) of
     learned transformations
  4. APPLIES the learned transformation to the test input by:
     a. Encoding the test input as a 24-bit colour
     b. Looking up the nearest learned transformation in the CRG
     c. Applying the transformation (XOR in colour space, then decode)

This is the GLM's native learning loop, adapted from words to grids.

Usage:
    from learner.pattern_learner import PatternLearner
    learner = PatternLearner()
    learner.learn_from_task(task)         # learn from train pairs
    predicted = learner.apply_to_test(task)  # apply to test input
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Any
from collections import defaultdict
import sys, os

# Make vendored dependencies importable
_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

# Make arc_loader, encoder, dsl importable
_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask
from encoder import encode_grid
from dsl import Ops, Operation, Program

# Import the live GLM colour module — every 24-bit vector IS a #RRGGBB colour
try:
    from GLM18_hex_colour import vector_to_colour, colour_distance
    _GLM_COLOUR_AVAILABLE = True
except ImportError:
    _GLM_COLOUR_AVAILABLE = False
    vector_to_colour = None
    colour_distance = None


# ══════════════════════════════════════════════════════════════════════════════
# TRANSFORMATION RECORD — what the learner stores per train pair
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TransformationRecord:
    """A single learned transformation, induced from one train pair."""
    pair_index: int
    # Input and output grid summaries (compact signatures)
    input_palette: frozenset
    output_palette: frozenset
    input_dominant: int
    output_dominant: int
    input_shape: Tuple[int, int]
    output_shape: Tuple[int, int]
    # 24-bit colour signatures (the GLM-native representation)
    input_colour_24bit: str     # "#RRGGBB"
    output_colour_24bit: str    # "#RRGGBB"
    # The transformation in colour space: output XOR input (bitwise diff)
    transform_colour_24bit: str  # "#RRGGBB" of the XOR
    # Refinement: did the transformation change shape? palette? dominant?
    shape_changed: bool
    palette_changed: bool
    dominant_changed: bool
    # Inferred transformation type (one of: identity, recolour, geometric, gravity, count, set, composite)
    inferred_type: str
    # The actual diff between input and output grids (for replay)
    cell_diffs: List[Tuple[int, int, int, int]] = field(default_factory=list)
    # cell_diffs: list of (row, col, old_value, new_value) for cells that changed


def _grid_to_colour_signature(grid: Grid) -> str:
    """Encode a grid as a 24-bit hex colour via the GLM encoder + GLM18.

    This is the colour-native encoding: the grid's 24-bit vector IS a colour.
    """
    v, _ = encode_grid(grid)
    if _GLM_COLOUR_AVAILABLE:
        return vector_to_colour(v)
    # Fallback: format the 24-bit vector as hex directly
    n = 0
    for i, bit in enumerate(v):
        if bit:
            n |= (1 << (23 - i))
    return f"#{n:06x}"


def _xor_colours(c1: str, c2: str) -> str:
    """XOR two #RRGGBB colours — the native GLM transformation in colour space."""
    n1 = int(c1[1:], 16)
    n2 = int(c2[1:], 16)
    return f"#{n1 ^ n2:06x}"


def _infer_transform_type(rec_input: TransformationRecord,
                           output: Grid) -> str:
    """Infer the type of transformation from input→output."""
    if rec_input.input_shape == output.shape:
        if rec_input.input_palette == output.palette():
            if rec_input.input_dominant == output.dominant_colour():
                return "identity"
            return "recolour"
        return "recolour"
    else:
        # Shape changed — could be geometric, gravity, or count
        h_in, w_in = rec_input.input_shape
        h_out, w_out = output.shape
        if h_in == w_in and h_out == w_out and h_in != h_out:
            if h_out > h_in:
                return "scale_up"
            return "scale_down"
        if h_in == h_out and w_in != w_out:
            return "scale_wide"
        if w_in == w_out and h_in != h_out:
            return "scale_tall"
        return "geometric"


# ══════════════════════════════════════════════════════════════════════════════
# CRG-LITE — Concept Relation Graph for ARC transformations
# ══════════════════════════════════════════════════════════════════════════════
#
# Adapted from GLM03_crg.ConceptRelationGraph. Each "concept" is a
# 24-bit colour signature; each "edge" is a learned transformation.
# This is the ARC-specific analogue of the GLM's word-co-occurrence graph.

@dataclass
class CRGEdge:
    """A learned transformation edge: source_colour → transform → target_colour."""
    src: str           # source colour "#RRGGBB"
    label: str         # transformation type ("recolour", "gravity", etc.)
    dst: str           # target colour "#RRGGBB"
    weight: int = 1    # how many train pairs exhibited this transformation
    transform_colour: str = "#000000"  # the XOR colour of this transformation


class CRGLite:
    """Lightweight Concept Relation Graph for ARC transformations.

    Nodes are 24-bit colour signatures; edges are learned transformations.
    Adapted from GLM03_crg.ConceptRelationGraph.
    """

    def __init__(self):
        self.out: Dict[str, List[CRGEdge]] = defaultdict(list)
        self.in_edges: Dict[str, List[CRGEdge]] = defaultdict(list)
        self.nodes: Set[str] = set()

    def add_edge(self, src: str, label: str, dst: str,
                 transform_colour: str = "#000000") -> None:
        """Add (or reinforce) a transformation edge."""
        # Check if edge already exists
        for e in self.out[src]:
            if e.dst == dst and e.label == label:
                e.weight += 1
                return
        edge = CRGEdge(src=src, label=label, dst=dst, weight=1,
                       transform_colour=transform_colour)
        self.out[src].append(edge)
        self.in_edges[dst].append(edge)
        self.nodes.add(src)
        self.nodes.add(dst)

    def find_nearest_transform(self, src_colour: str,
                                max_colour_distance: int = 50) -> Optional[CRGEdge]:
        """Find the nearest learned transformation for a given source colour.

        Uses GLM18's colour_distance to find the closest learned source node,
        then returns its highest-weight outgoing edge.
        """
        if not self.out:
            return None
        if src_colour in self.out:
            # Direct hit — return highest-weight edge
            edges = self.out[src_colour]
            return max(edges, key=lambda e: e.weight)

        # Find nearest node by colour distance
        best_edge = None
        best_distance = float('inf')
        for node_colour, edges in self.out.items():
            if _GLM_COLOUR_AVAILABLE:
                d = colour_distance(src_colour, node_colour)
            else:
                # Fallback: hamming distance on hex
                n1 = int(src_colour[1:], 16)
                n2 = int(node_colour[1:], 16)
                d = bin(n1 ^ n2).count('1') * 1000
            if d < best_distance and d <= max_colour_distance:
                best_distance = d
                best_edge = max(edges, key=lambda e: e.weight)
        return best_edge

    def stats(self) -> Dict[str, int]:
        return {
            "nodes": len(self.nodes),
            "edges": sum(len(es) for es in self.out.values()),
        }


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN LEARNER — the main v0.3 class
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PatternLearner:
    """Learns ARC transformations from train pairs using GLM-native colour space.

    This is the v0.3 alternative to the v0.2 hardcoded DSL. Instead of
    enumerating 26 operators, the learner:
      1. Encodes each train pair's input+output as 24-bit hex colours
      2. Records the transformation as an edge in a CRG (colour relation graph)
      3. When asked to predict, finds the nearest learned transformation
         and replays it on the test input

    The learner also detects COMMON patterns across train pairs:
      - If all pairs show the same recolour mapping, learn that mapping
      - If all pairs show the same geometric transform, learn that transform
      - If all pairs show gravity, learn gravity
      - If no common pattern, fall back to per-cell diff replay
    """
    # The CRG of learned transformations
    crg: CRGLite = field(default_factory=CRGLite)
    # Per-pair transformation records
    records: List[TransformationRecord] = field(default_factory=list)
    # Learned common patterns (populated by _detect_common_patterns)
    learned_recolour_mapping: Dict[int, int] = field(default_factory=dict)
    learned_geometric_op: Optional[Ops] = None
    learned_gravity_direction: Optional[str] = None  # "down", "up", "left", "right"
    learned_count_value: Optional[int] = None
    learned_pattern_type: str = "unknown"  # "recolour", "geometric", "gravity", "count", "identity", "composite", "unknown"
    # Cell-level diff patterns (for replay)
    learned_cell_diffs: List[List[Tuple[int, int, int, int]]] = field(default_factory=list)

    def learn_from_task(self, task: ARCTask) -> None:
        """Learn transformation patterns from the task's train pairs."""
        self.records.clear()
        self.learned_cell_diffs.clear()
        self._task = task  # store for pattern testing

        for i, pair in enumerate(task.train):
            # Encode input and output as 24-bit colours
            in_colour = _grid_to_colour_signature(pair.input)
            out_colour = _grid_to_colour_signature(pair.output)
            transform_colour = _xor_colours(in_colour, out_colour)

            # Compute cell-level diffs
            cell_diffs = []
            h = min(pair.input.height, pair.output.height)
            w = min(pair.input.width, pair.output.width)
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] != pair.output.cells[r][c]:
                        cell_diffs.append((r, c, pair.input.cells[r][c], pair.output.cells[r][c]))

            rec = TransformationRecord(
                pair_index=i,
                input_palette=pair.input.palette(),
                output_palette=pair.output.palette(),
                input_dominant=pair.input.dominant_colour(),
                output_dominant=pair.output.dominant_colour(),
                input_shape=pair.input.shape,
                output_shape=pair.output.shape,
                input_colour_24bit=in_colour,
                output_colour_24bit=out_colour,
                transform_colour_24bit=transform_colour,
                shape_changed=pair.input.shape != pair.output.shape,
                palette_changed=pair.input.palette() != pair.output.palette(),
                dominant_changed=pair.input.dominant_colour() != pair.output.dominant_colour(),
                inferred_type=_infer_transform_type(
                    TransformationRecord(
                        pair_index=i,
                        input_palette=pair.input.palette(),
                        output_palette=pair.output.palette(),
                        input_dominant=pair.input.dominant_colour(),
                        output_dominant=pair.output.dominant_colour(),
                        input_shape=pair.input.shape,
                        output_shape=pair.output.shape,
                        input_colour_24bit=in_colour,
                        output_colour_24bit=out_colour,
                        transform_colour_24bit=transform_colour,
                        shape_changed=False, palette_changed=False, dominant_changed=False,
                        inferred_type="identity",
                    ),
                    pair.output,
                ),
                cell_diffs=cell_diffs,
            )
            self.records.append(rec)
            self.learned_cell_diffs.append(cell_diffs)

            # Add to CRG
            self.crg.add_edge(in_colour, rec.inferred_type, out_colour,
                              transform_colour=transform_colour)

        # Detect common patterns across all train pairs
        self._detect_common_patterns()

    def _detect_common_patterns(self) -> None:
        """Detect common transformation patterns across all train pairs."""
        if not self.records:
            return

        # Check for identity (all pairs unchanged)
        if all(rec.inferred_type == "identity" and not rec.cell_diffs for rec in self.records):
            self.learned_pattern_type = "identity"
            return

        # Check for recolour: all pairs have same shape, palette changed, and
        # the recolour mapping is consistent across pairs
        if all(not rec.shape_changed for rec in self.records):
            # Build the union of all recolour mappings
            mapping_votes: Dict[Tuple[int, int], int] = defaultdict(int)
            for diffs in self.learned_cell_diffs:
                pair_mapping: Dict[int, int] = {}
                for r, c, old, new in diffs:
                    if old != new:
                        pair_mapping[old] = new
                for old, new in pair_mapping.items():
                    mapping_votes[(old, new)] += 1

            # If there's a consistent mapping (appears in all pairs), learn it
            n_pairs = len(self.records)
            consistent_mapping = {}
            for (old, new), count in mapping_votes.items():
                if count >= n_pairs * 0.6:  # 60% threshold for consistency
                    consistent_mapping[old] = new

            if consistent_mapping:
                self.learned_recolour_mapping = consistent_mapping
                self.learned_pattern_type = "recolour"
                return

        # Check for gravity (all pairs same shape, cells compacted)
        if all(not rec.shape_changed for rec in self.records):
            # Test each gravity direction
            for direction, op in [("down", Ops.GRAVITY_DOWN),
                                  ("up", Ops.GRAVITY_UP),
                                  ("left", Ops.GRAVITY_LEFT),
                                  ("right", Ops.GRAVITY_RIGHT)]:
                if self._test_gravity_pattern(direction):
                    self.learned_gravity_direction = direction
                    self.learned_geometric_op = op
                    self.learned_pattern_type = "gravity"
                    return

        # Check for geometric transforms — test ALL geometric ops on all pairs
        # (some ops like flip don't change shape, so we test them regardless)
        for op in [Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
                   Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
                   Ops.SCALE_2X, Ops.SCALE_HALF, Ops.CROP_TO_NONZERO]:
            if self._test_geometric_pattern(op):
                self.learned_geometric_op = op
                self.learned_pattern_type = "geometric"
                return

        # Check for count_fill (all pairs same shape, bottom row gets filled)
        if all(not rec.shape_changed for rec in self.records):
            if self._test_geometric_pattern(Ops.COUNT_FILL):
                self.learned_geometric_op = Ops.COUNT_FILL
                self.learned_pattern_type = "count"
                return

        # Fallback: composite pattern (cell-level replay)
        self.learned_pattern_type = "composite"

    def _test_gravity_pattern(self, direction: str) -> bool:
        """Test if all train pairs exhibit the given gravity direction."""
        if not hasattr(self, '_task') or self._task is None:
            return False
        op_map = {"down": Ops.GRAVITY_DOWN, "up": Ops.GRAVITY_UP,
                  "left": Ops.GRAVITY_LEFT, "right": Ops.GRAVITY_RIGHT}
        op = Operation(op_map[direction])
        for pair in self._task.train:
            if op.apply(pair.input) != pair.output:
                return False
        return True

    def _test_geometric_pattern(self, op: Ops) -> bool:
        """Test if all train pairs exhibit the given geometric op."""
        if not hasattr(self, '_task') or self._task is None:
            return False
        op_obj = Operation(op)
        for pair in self._task.train:
            if op_obj.apply(pair.input) != pair.output:
                return False
        return True

    def predict(self, task: ARCTask) -> Optional[Grid]:
        """Predict the test output by applying the learned transformation.

        v0.4: when no pattern is detected, use the CRG's find_nearest_transform
        to find the nearest learned transformation and apply it via colour-space
        XOR — the GLM's native transformation in 24-bit colour space.

        Returns the predicted Grid, or None if no pattern was learned.
        """
        if self.learned_pattern_type == "identity":
            return task.test[0].input.copy()

        if self.learned_pattern_type == "recolour":
            # Apply the learned recolour mapping
            return Program([Operation(Ops.RECOLOUR,
                                       params={"mapping": self.learned_recolour_mapping})]
                           ).apply(task.test[0].input)

        if self.learned_pattern_type == "gravity":
            if self.learned_geometric_op:
                return Program([Operation(self.learned_geometric_op)]
                               ).apply(task.test[0].input)

        if self.learned_pattern_type == "geometric":
            if self.learned_geometric_op:
                return Program([Operation(self.learned_geometric_op)]
                               ).apply(task.test[0].input)

        if self.learned_pattern_type == "count":
            if self.learned_geometric_op:
                return Program([Operation(self.learned_geometric_op)]
                               ).apply(task.test[0].input)

        if self.learned_pattern_type == "composite":
            # v0.4: try CRG-based prediction first, then fall back to cell replay
            crg_pred = self._predict_via_crg(task)
            # Only use CRG prediction if it actually changed something
            # (if it returns the input unchanged but the task is composite, there
            # ARE changes — fall through to cell replay)
            if crg_pred is not None and crg_pred != task.test[0].input:
                return crg_pred
            return self._replay_cell_diffs(task)

        return None

    def _predict_via_crg(self, task: ARCTask) -> Optional[Grid]:
        """v0.4: use the CRG to find the nearest learned transformation.

        Encodes the test input as a 24-bit colour, finds the nearest learned
        source colour in the CRG, and applies that transformation's colour
        XOR to predict the output colour. Then decodes the colour back to a grid.

        This is the GLM's native transformation mechanism: the 24-bit vector
        IS a colour, and transformations are XOR operations in colour space.
        """
        if not self.crg.nodes:
            return None

        test_input = task.test[0].input
        test_colour = _grid_to_colour_signature(test_input)

        # Find the nearest learned transformation
        edge = self.crg.find_nearest_transform(test_colour, max_colour_distance=100000)
        if edge is None:
            return None

        # Apply the transformation: XOR the test colour with the transform colour
        # This gives us the predicted output colour signature
        predicted_colour = _xor_colours(test_colour, edge.transform_colour)

        # v0.4: we can't directly decode a 24-bit colour back to a grid (the
        # encoding is lossy — many grids map to the same colour). Instead,
        # we use the transformation TYPE from the CRG edge to pick a DSL op
        # and apply it to the test input.
        #
        # This is the key insight: the CRG tells us WHAT transformation to apply
        # (by label), and we apply it via the DSL. The colour-space XOR is the
        # signature that lets us find the nearest match.

        transform_label = edge.label
        if transform_label == "identity":
            return test_input.copy()
        if transform_label == "recolour":
            # Apply the most common recolour mapping from train pairs
            if self.learned_recolour_mapping:
                return Program([Operation(Ops.RECOLOUR,
                                           params={"mapping": self.learned_recolour_mapping})]
                               ).apply(test_input)
            return None
        if transform_label == "gravity":
            # Try all 4 gravity directions
            for op in [Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT]:
                result = Program([Operation(op)]).apply(test_input)
                # Check if this gravity direction is consistent with train pairs
                if self._task and all(
                    Program([Operation(op)]).apply(p.input) == p.output
                    for p in self._task.train
                ):
                    return result
            return None
        if transform_label == "geometric":
            # Try all geometric ops
            for op in [Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
                       Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE]:
                if self._test_geometric_pattern(op):
                    return Program([Operation(op)]).apply(test_input)
            return None
        # For other types, fall back to cell replay
        return None

    def _replay_cell_diffs(self, task: ARCTask) -> Grid:
        """Replay cell-level diffs from train pairs onto the test input.

        v0.3.1: instead of positional replay (which fails when test input
        has different values), we detect the PATTERN of diffs:
          - "swap cells at positions P1 and P2" (symmetric swap)
          - "recolour cells at positions P" (specific positions recoloured)
          - "fill cells at positions P with colour C" (positional fill)

        We detect the pattern by looking at the diff POSITIONS (ignoring
        values) across all train pairs. If all pairs have diffs at the same
        positions, we apply the same positional transformation to the test.
        """
        test_input = task.test[0].input

        # Check if all train pairs have diffs at the same positions
        if not self.learned_cell_diffs:
            return test_input.copy()

        # Get the diff positions for each pair
        all_diff_positions = []
        for diffs in self.learned_cell_diffs:
            positions = frozenset((r, c) for r, c, _, _ in diffs)
            all_diff_positions.append(positions)

        # If all pairs have the same diff positions, apply the pattern
        if len(set(all_diff_positions)) == 1 and all_diff_positions[0]:
            # All pairs agree on which positions change
            # Detect what kind of change: swap or recolour
            positions = all_diff_positions[0]
            # For each position, check if the change is consistent (same old→new)
            # or if it's a swap (old at pos A = new at pos B)
            # Build the value mapping per position across all pairs
            pos_values: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
            for diffs in self.learned_cell_diffs:
                for r, c, old, new in diffs:
                    pos_values[(r, c)].append((old, new))

            # Check for swap pattern: exactly 2 positions, and old at A = new at B
            if len(positions) == 2:
                pos_list = sorted(positions)
                p1, p2 = pos_list[0], pos_list[1]
                # Check if old at p1 == new at p2 and old at p2 == new at p1 (swap)
                is_swap = True
                for i in range(len(self.learned_cell_diffs)):
                    vals_p1 = pos_values[p1][i]  # (old, new) at p1 for pair i
                    vals_p2 = pos_values[p2][i]  # (old, new) at p2 for pair i
                    if vals_p1[0] != vals_p2[1] or vals_p2[0] != vals_p1[1]:
                        is_swap = False
                        break
                if is_swap:
                    # Apply swap to test input
                    out = test_input.copy()
                    if (0 <= p1[0] < out.height and 0 <= p1[1] < out.width
                            and 0 <= p2[0] < out.height and 0 <= p2[1] < out.width):
                        out.cells[p1[0]][p1[1]], out.cells[p2[0]][p2[1]] = \
                            out.cells[p2[0]][p2[1]], out.cells[p1[0]][p1[1]]
                    return Grid(out.cells)

            # Check for consistent recolour at specific positions
            # (same old→new mapping at each position across all pairs)
            consistent_recolour: Dict[Tuple[int, int], Tuple[int, int]] = {}
            for pos, vals_list in pos_values.items():
                first_old, first_new = vals_list[0]
                if all(old == first_old and new == first_new for old, new in vals_list):
                    consistent_recolour[pos] = (first_old, first_new)

            if consistent_recolour and len(consistent_recolour) == len(positions):
                # Apply consistent recolour at specific positions
                out = test_input.copy()
                for (r, c), (old, new) in consistent_recolour.items():
                    if (0 <= r < out.height and 0 <= c < out.width
                            and out.cells[r][c] == old):
                        out.cells[r][c] = new
                return Grid(out.cells)

        # Fallback: positional replay from best-matching train pair
        best_idx = 0
        best_score = -1
        for i, pair in enumerate(task.train):
            score = 0
            if pair.input.shape == test_input.shape:
                score += 10
            score += len(pair.input.palette() & test_input.palette())
            if pair.input.dominant_colour() == test_input.dominant_colour():
                score += 5
            if score > best_score:
                best_score = score
                best_idx = i

        diffs = self.learned_cell_diffs[best_idx]
        out = test_input.copy()
        for r, c, old, new in diffs:
            if (0 <= r < out.height and 0 <= c < out.width
                    and out.cells[r][c] == old):
                out.cells[r][c] = new
        return Grid(out.cells)

    def summary(self) -> str:
        """Human-readable summary of what was learned."""
        lines = [
            f"PatternLearner summary:",
            f"  records:           {len(self.records)}",
            f"  pattern type:      {self.learned_pattern_type}",
            f"  CRG stats:         {self.crg.stats()}",
        ]
        if self.learned_recolour_mapping:
            lines.append(f"  recolour mapping:  {self.learned_recolour_mapping}")
        if self.learned_geometric_op:
            lines.append(f"  geometric op:      {self.learned_geometric_op.value}")
        if self.learned_gravity_direction:
            lines.append(f"  gravity direction: {self.learned_gravity_direction}")
        return "\n".join(lines)
