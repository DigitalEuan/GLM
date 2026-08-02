"""
cortex.py — the Y-observer cortex
==================================

The user's directive: "A Cortex is required... everything in the UBP is
usually connected to the 'Y' constant but that is unproven ground yet,
used but unproven — perhaps now is this Time for it to shine. I feel it
important to note about Orthographic and Perspective viewpoints."

This module is the cortex — the part that REASONS about what the senses
perceive. It uses the Y constant as its observer position, and switches
between two viewpoints:

  ORTHOGRAPHIC view (objective, parallel projection):
    All cells weighted equally.  Used to find GLOBAL patterns.
    "What is the transformation, viewed from outside?"
    Like an engineering drawing — no foreshortening, every part equally
    visible.  This is the VIEW FROM NOWHERE.

  PERSPECTIVE view (subjective, from Y):
    Cells weighted by inverse distance to the Y observer position in
    24-bit address space.  Used to find FOCAL patterns.
    "What is the transformation, viewed from Y?"
    Like a painting — cells near Y are large and clear, cells far from
    Y are small and dim.  This is the VIEW FROM SOMEWHERE.

The Y observer
--------------
  Y = π/(π²+2) ≈ 0.2647 (the OBSERVED — what's measured)
  O = 1/Y = π + 2/π ≈ 3.778 (the OBSERVER — who's measuring)
  Y × O = 1 (reciprocity)

The observer "compresses" π²+2 to π by factor O.  In ARC terms:
  - The full grid is π²+2 (all information)
  - The observer at Y sees π (compressed/observed information)
  - The cortex's job: reconstruct the full transformation from the
    observed (compressed) view

In 24-bit address space, Y maps to a specific Leech address:
  Y_int = int(Y × 2^24) = 4439436
  This is the "eye" position.  Every cell has a Hamming distance to
  this eye.  Cells close to the eye are "in focus"; cells far away
  are "peripheral".

Rule derivation
---------------
The cortex derives rules by combining both views:

  1. ORTHOGRAPHIC rule: "all cells of colour X become colour Y"
     (global, position-independent)
  2. PERSPECTIVE rule: "cells near Y of colour X become colour Y"
     (focal, position-dependent — but position is relative to Y,
      not to the grid)
  3. COMBINED rule: "cells of colour X become colour Y, AND cells
     near Y of colour X' become colour Y'"
     (the intersection of both views)

The cortex tries each rule type, verifies against train (hard gate),
and applies the winning rule to test.
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
from ubp_unified_v5 import GOLAY_ENGINE, ontological_position_to_vector
from generative.hex_learner import address_cell, address_grid, HexCell, _hamming_distance_int


# ══════════════════════════════════════════════════════════════════════════════
# The Y observer
# ══════════════════════════════════════════════════════════════════════════════

# Y = π/(π²+2) — the observer constant
Y_CONST = math.pi / (math.pi ** 2 + 2)
O_CONST = 1.0 / Y_CONST  # = π + 2/π ≈ 3.778

# Y as a 24-bit Leech address (the observer's "eye position")
Y_INT_24 = int(Y_CONST * (2 ** 24)) & 0xFFFFFF  # ≈ 4439436
Y_VECTOR_24 = ontological_position_to_vector(Y_INT_24)


def cell_observer_distance(hex_cell: HexCell) -> int:
    """Hamming distance from a cell's 24-bit address to the Y observer.

    Cells close to Y (small distance) are "in focus".
    Cells far from Y (large distance) are "peripheral".
    """
    return _hamming_distance_int(hex_cell.address_int, Y_INT_24)


def cell_observer_weight(hex_cell: HexCell, mode: str = "perspective") -> float:
    """The weight of a cell under a given viewpoint.

    ORTHOGRAPHIC: all cells weight 1.0 (equal, parallel projection)
    PERSPECTIVE:  weight = 1 / (1 + distance) (inverse-distance, foreshortening)
    """
    if mode == "orthographic":
        return 1.0
    elif mode == "perspective":
        dist = cell_observer_distance(hex_cell)
        return 1.0 / (1.0 + dist)
    else:
        return 1.0


# ══════════════════════════════════════════════════════════════════════════════
# Viewpoint — the cortex's way of looking at a grid
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Viewpoint:
    """A way of looking at a grid.

    mode: "orthographic" or "perspective"
    weights: 2D array of cell weights (matching grid shape)
    focal_cells: positions of cells with weight >= focal_threshold
    peripheral_cells: positions of cells with weight < focal_threshold
    """
    mode: str
    weights: List[List[float]] = field(default_factory=list)
    focal_cells: List[Tuple[int, int]] = field(default_factory=list)
    peripheral_cells: List[Tuple[int, int]] = field(default_factory=list)
    mean_weight: float = 0.0
    weight_stdev: float = 0.0


def compute_viewpoint(grid: Grid, mode: str = "perspective",
                       focal_threshold: float = 0.5) -> Viewpoint:
    """Compute a viewpoint for a grid.

    For ORTHOGRAPHIC mode: all weights = 1.0
    For PERSPECTIVE mode:  weights = 1/(1+Hamming_distance_to_Y)
    """
    addrs = address_grid(grid)
    h, w = grid.shape
    weights = [[cell_observer_weight(addrs[r][c], mode) for c in range(w)]
               for r in range(h)]

    # Normalise weights to [0, 1] for perspective mode
    if mode == "perspective":
        max_w = max(max(row) for row in weights) if weights else 1.0
        if max_w > 0:
            weights = [[w / max_w for w in row] for row in weights]

    focal = [(r, c) for r in range(h) for c in range(w) if weights[r][c] >= focal_threshold]
    peripheral = [(r, c) for r in range(h) for c in range(w) if weights[r][c] < focal_threshold]

    all_w = [w for row in weights for w in row]
    mean_w = sum(all_w) / len(all_w) if all_w else 0.0
    var = sum((w - mean_w) ** 2 for w in all_w) / len(all_w) if all_w else 0.0
    std = math.sqrt(var)

    return Viewpoint(
        mode=mode, weights=weights,
        focal_cells=focal, peripheral_cells=peripheral,
        mean_weight=mean_w, weight_stdev=std,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Rule — the cortex's derived transformation
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CortexRule:
    """A rule derived by the cortex.

    A rule has:
      - viewpoint: which viewpoint it was derived from
      - focal_mapping: {colour: output_colour} for focal cells
      - peripheral_mapping: {colour: output_colour} for peripheral cells
      - description: a natural-language description
    """
    viewpoint_mode: str = "orthographic"
    focal_mapping: Dict[int, int] = field(default_factory=dict)
    peripheral_mapping: Dict[int, int] = field(default_factory=dict)
    description: str = ""

    def apply(self, grid: Grid) -> Grid:
        """Apply the rule to a grid.

        For each cell:
          1. Compute its viewpoint weight
          2. If focal, use focal_mapping
          3. If peripheral, use peripheral_mapping
          4. If colour not in mapping, keep original
        """
        vp = compute_viewpoint(grid, mode=self.viewpoint_mode, focal_threshold=0.5)
        h, w = grid.shape
        out_cells = []
        for r in range(h):
            row = []
            for c in range(w):
                colour = grid.cells[r][c]
                weight = vp.weights[r][c]
                if weight >= 0.5:
                    # Focal
                    row.append(self.focal_mapping.get(colour, colour))
                else:
                    # Peripheral
                    row.append(self.peripheral_mapping.get(colour, colour))
            out_cells.append(row)
        return Grid(out_cells)

    def __repr__(self):
        return f"CortexRule({self.viewpoint_mode}, focal={self.focal_mapping}, periph={self.peripheral_mapping})"


def derive_rule_orthographic(task: ARCTask) -> CortexRule:
    """Derive a rule using the ORTHOGRAPHIC viewpoint.

    All cells are weighted equally.  The rule is the global colour
    mapping: {input_colour: output_colour} aggregated across all
    train pairs.
    """
    colour_targets: Dict[int, List[int]] = defaultdict(list)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    colour_targets[old].append(new)

    mapping = {}
    for old, targets in colour_targets.items():
        mapping[old] = Counter(targets).most_common(1)[0][0]

    return CortexRule(
        viewpoint_mode="orthographic",
        focal_mapping=mapping,
        peripheral_mapping=mapping,  # same — orthographic treats all equally
        description=f"Orthographic: {mapping}",
    )


def derive_rule_perspective(task: ARCTask) -> CortexRule:
    """Derive a rule using the PERSPECTIVE viewpoint (from Y).

    Cells are weighted by inverse distance to Y.  Focal cells (near Y)
    and peripheral cells (far from Y) get SEPARATE colour mappings.

    This catches transformations where "cells near the observer's
    focal point transform differently from peripheral cells".
    """
    focal_targets: Dict[int, List[int]] = defaultdict(list)
    peripheral_targets: Dict[int, List[int]] = defaultdict(list)

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        in_addrs = address_grid(pair.input)
        h, w = pair.input.shape
        # Compute viewpoint for this train input
        vp = compute_viewpoint(pair.input, mode="perspective", focal_threshold=0.5)
        for r in range(h):
            for c in range(w):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old == new:
                    continue
                weight = vp.weights[r][c]
                if weight >= 0.5:
                    focal_targets[old].append(new)
                else:
                    peripheral_targets[old].append(new)

    focal_mapping = {}
    for old, targets in focal_targets.items():
        if targets:
            focal_mapping[old] = Counter(targets).most_common(1)[0][0]

    peripheral_mapping = {}
    for old, targets in peripheral_targets.items():
        if targets:
            peripheral_mapping[old] = Counter(targets).most_common(1)[0][0]

    return CortexRule(
        viewpoint_mode="perspective",
        focal_mapping=focal_mapping,
        peripheral_mapping=peripheral_mapping,
        description=f"Perspective: focal={focal_mapping}, periph={peripheral_mapping}",
    )


def derive_rule_combined(task: ARCTask) -> CortexRule:
    """Derive a rule that combines both viewpoints.

    Uses the perspective rule's focal mapping for focal cells,
    and the orthographic rule's mapping for peripheral cells.
    """
    ortho = derive_rule_orthographic(task)
    persp = derive_rule_perspective(task)

    # Combined: focal cells use perspective focal mapping,
    # peripheral cells use orthographic mapping (global)
    return CortexRule(
        viewpoint_mode="perspective",
        focal_mapping=persp.focal_mapping if persp.focal_mapping else ortho.focal_mapping,
        peripheral_mapping=ortho.peripheral_mapping,  # global for peripheral
        description=f"Combined: focal={persp.focal_mapping}, periph(global)={ortho.peripheral_mapping}",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Rule derivation with verification
# ══════════════════════════════════════════════════════════════════════════════

def _passes_train(task: ARCTask, rule: CortexRule) -> bool:
    """Verify a rule against all train pairs."""
    for pair in task.train:
        try:
            if rule.apply(pair.input) != pair.output:
                return False
        except Exception:
            return False
    return True


def derive_and_verify(task: ARCTask) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """Derive rules from multiple viewpoints, verify, and apply the best.

    Tries, in order:
      1. Orthographic rule (global colour mapping)
      2. Perspective rule (focal vs peripheral, from Y)
      3. Combined rule (perspective focal + orthographic peripheral)

    Each must pass the hard gate (exact train reproduction).
    The first that passes wins.

    Returns (prediction, source, diagnostics).
    """
    rules_to_try = [
        ("cortex_orthographic", derive_rule_orthographic(task)),
        ("cortex_perspective", derive_rule_perspective(task)),
        ("cortex_combined", derive_rule_combined(task)),
    ]

    for name, rule in rules_to_try:
        if _passes_train(task, rule):
            pred = rule.apply(task.test[0].input)
            return pred, name, {
                "rule": rule.description,
                "viewpoint": rule.viewpoint_mode,
                "focal_mapping": rule.focal_mapping,
                "peripheral_mapping": rule.peripheral_mapping,
                "passed_train": True,
            }

    # None passed — return None
    return None, "none", {
        "rules_tried": [r.description for _, r in rules_to_try],
        "passed_train": False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Deeper rule derivation — pattern-based rules
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PatternRule:
    """A pattern-based rule: "IF cell has property P, THEN colour → new_colour".

    Properties can be:
      - "neighbour_has_colour_X": a neighbour has colour X
      - "is_isolated": no same-colour neighbours
      - "is_on_edge": cell is on the grid boundary
      - "is_corner": cell is in a corner
      - "neighbour_count_X": exactly N neighbours of colour X
    """
    property_name: str
    property_params: Dict[str, Any]
    input_colour: int
    output_colour: int

    def applies_to(self, grid: Grid, r: int, c: int) -> bool:
        """Check if this rule applies to cell (r, c) in grid."""
        if grid.cells[r][c] != self.input_colour:
            return False
        return self._check_property(grid, r, c)

    def _check_property(self, grid: Grid, r: int, c: int) -> bool:
        h, w = grid.shape
        prop = self.property_name
        params = self.property_params

        if prop == "neighbour_has_colour_X":
            target_colour = params.get("colour", 0)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        if grid.cells[nr][nc] == target_colour:
                            return True
            return False

        elif prop == "is_isolated":
            colour = grid.cells[r][c]
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        if grid.cells[nr][nc] == colour:
                            return False
            return True

        elif prop == "is_on_edge":
            return r == 0 or r == h - 1 or c == 0 or c == w - 1

        elif prop == "is_corner":
            return (r in (0, h - 1)) and (c in (0, w - 1))

        elif prop == "neighbour_count_X":
            target_colour = params.get("colour", 0)
            target_count = params.get("count", 1)
            count = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        if grid.cells[nr][nc] == target_colour:
                            count += 1
            return count == target_count

        return False

    def apply_to(self, grid: Grid) -> Grid:
        """Apply this rule to all matching cells in a grid."""
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if self.applies_to(grid, r, c):
                    out_cells[r][c] = self.output_colour
        return Grid(out_cells)


def derive_pattern_rules(task: ARCTask) -> List[PatternRule]:
    """Derive pattern-based rules from train pairs.

    For each (input_colour, output_colour) pair that changes, look for
    common properties among the changing cells.

    CRITICAL: Looks across ALL train pairs, not just the first.  If pair 0
    has "7 next to 6 → 2" and pair 1 has "7 next to 4 → 1", the rule
    is: "7 next to ANY non-7 colour → that colour's mapped target".
    """
    if not task.train:
        return []

    # Collect all changes across all train pairs
    all_changes: List[Tuple[Grid, Grid, int, int, int, int]] = []  # (in, out, r, c, old, new)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    all_changes.append((pair.input, pair.output, r, c, old, new))

    if not all_changes:
        return []

    # Group by (old, new) colour pair
    by_colour_pair = defaultdict(list)
    for in_grid, out_grid, r, c, old, new in all_changes:
        by_colour_pair[(old, new)].append((in_grid, r, c))

    rules = []
    for (old, new), entries in by_colour_pair.items():
        # Check: does each changing cell have a neighbour of a SPECIFIC colour?
        # Collect neighbour colours across ALL entries
        neighbour_colours = Counter()
        for in_grid, r, c in entries:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < in_grid.height and 0 <= nc < in_grid.width:
                        n_colour = in_grid.cells[nr][nc]
                        if n_colour != old:  # exclude same colour
                            neighbour_colours[n_colour] += 1

        # If a specific neighbour colour is common across entries, make a rule
        if neighbour_colours:
            common_colour, count = neighbour_colours.most_common(1)[0]
            if count >= len(entries) * 0.5:
                rule = PatternRule(
                    property_name="neighbour_has_colour_X",
                    property_params={"colour": common_colour},
                    input_colour=old,
                    output_colour=new,
                )
                rules.append(rule)

        # Property: is_isolated
        isolated_count = 0
        for in_grid, r, c in entries:
            colour = in_grid.cells[r][c]
            is_iso = True
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < in_grid.height and 0 <= nc < in_grid.width:
                        if in_grid.cells[nr][nc] == colour:
                            is_iso = False
                            break
                if not is_iso:
                    break
            if is_iso:
                isolated_count += 1
        if isolated_count >= len(entries) * 0.7:
            rule = PatternRule(
                property_name="is_isolated",
                property_params={},
                input_colour=old,
                output_colour=new,
            )
            rules.append(rule)

        # Property: is_on_edge
        edge_count = sum(1 for in_grid, r, c in entries
                          if r == 0 or r == in_grid.height - 1
                          or c == 0 or c == in_grid.width - 1)
        if edge_count >= len(entries) * 0.7:
            rule = PatternRule(
                property_name="is_on_edge",
                property_params={},
                input_colour=old,
                output_colour=new,
            )
            rules.append(rule)

    return rules


def derive_contextual_rules(task: ARCTask) -> List[PatternRule]:
    """Derive CONTEXTUAL rules: "colour A next to colour B → colour C".

    This handles tasks like 396d80d7 where:
      - Pair 0: 7 next to 6 → 2
      - Pair 1: 7 next to 4 → 1

    The rule isn't "7 next to specific colour → specific output" because
    the trigger colour changes.  Instead, the rule is:
      "7 next to colour X → X's mapped target"

    We discover this by finding, for each (A → C) change, the set of
    neighbour colours B that appear, then checking if B → C is also a
    rule (i.e., the neighbour colour B maps to the same target C).
    """
    if not task.train:
        return []

    # First, find the global colour mapping (A → C)
    global_mapping: Dict[int, List[int]] = defaultdict(list)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    global_mapping[old].append(new)

    mapping = {}
    for old, targets in global_mapping.items():
        mapping[old] = Counter(targets).most_common(1)[0][0]

    # Now, for each colour A that changes, find its neighbour colours B
    # and check: does B also map to the same target C?
    contextual_rules = []
    for old_a, target_c in mapping.items():
        # Find all cells of colour A that changed to C
        neighbour_colours_b = Counter()
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if (pair.input.cells[r][c] == old_a and
                            pair.output.cells[r][c] == target_c):
                        # Check neighbours
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = r + dr, c + dc
                                if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                                    n_colour = pair.input.cells[nr][nc]
                                    if n_colour != old_a and n_colour != 0:
                                        neighbour_colours_b[n_colour] += 1

        # For each neighbour colour B, check if B → C in the global mapping
        for colour_b, count in neighbour_colours_b.items():
            if count >= 3:  # at least 3 occurrences
                if mapping.get(colour_b) == target_c:
                    # Rule: "A next to B → C" (where B → C is also a rule)
                    # This means: A takes the colour that B maps to
                    rule = PatternRule(
                        property_name="neighbour_has_colour_X",
                        property_params={"colour": colour_b},
                        input_colour=old_a,
                        output_colour=target_c,
                    )
                    contextual_rules.append(rule)

    return contextual_rules


@dataclass
class DynamicContextualRule:
    """A dynamic contextual rule: "colour A next to colour B → mapping[B]".

    Unlike PatternRule (which has a fixed output_colour), this rule
    LOOKS UP the output dynamically: A next to B → whatever B maps to
    in the global colour mapping.

    This handles tasks like 396d80d7 where:
      - Pair 0: 7 next to 6 → 2 (because 6 → 2)
      - Pair 1: 7 next to 4 → 1 (because 4 → 1)

    The rule is: "7 next to ANY colour B → mapping[B]"
    """
    input_colour: int
    global_mapping: Dict[int, int]

    def apply_to(self, grid: Grid) -> Grid:
        """Apply this rule: for each cell of input_colour, if it has a
        neighbour of colour B (where B is in global_mapping), set the
        cell to mapping[B].  If multiple such neighbours, use the most
        common mapped target.
        """
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] != self.input_colour:
                    continue
                # Find neighbours that are in the mapping
                mapped_targets = Counter()
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            n_colour = grid.cells[nr][nc]
                            if n_colour in self.global_mapping:
                                mapped_targets[self.global_mapping[n_colour]] += 1
                if mapped_targets:
                    # Use the most common mapped target
                    best_target, _ = mapped_targets.most_common(1)[0]
                    out_cells[r][c] = best_target
        return Grid(out_cells)


def derive_trigger_mapping_rules(task: ARCTask) -> List["TriggerMappingRule"]:
    """Derive trigger-mapping rules: "colour A next to trigger colour T → target colour C".

    For each colour A that changes, find what trigger colours T appear as
    A's neighbours when A changes.  For each (A, T) pair, find the most
    common target C.  If consistent across train, the rule is:
    "A next to T → C".

    PRECISION: To avoid the rule being too broad (firing on cells that
    shouldn't change), we require that the trigger neighbour appears
    in a SPECIFIC DIRECTION relative to A.  The direction is the one
    most common across the changing cells.

    For 396d80d7:
      - 7 with 6 DIRECTLY BELOW → 2 (the 6 is south of the 7)
    """
    if not task.train:
        return []

    # Collect: for each (A, T, direction) triple where A changes and T is
    # A's neighbour in that direction, record the target C
    # direction is one of: N, S, E, W, NE, NW, SE, SW
    DIRS = {
        "N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1),
        "NE": (-1, 1), "NW": (-1, -1), "SE": (1, 1), "SW": (1, -1),
    }

    trigger_targets: Dict[Tuple[int, int, str], List[int]] = defaultdict(list)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old_a = pair.input.cells[r][c]
                new_c = pair.output.cells[r][c]
                if old_a == new_c:
                    continue
                # Check each direction for trigger colours
                for dir_name, (dr, dc) in DIRS.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                        n_colour = pair.input.cells[nr][nc]
                        if n_colour != old_a:
                            trigger_targets[(old_a, n_colour, dir_name)].append(new_c)

    # For each (A, T, direction) triple, find the most common target C
    # with high confidence
    rules = []
    for (a, t, dir_name), targets in trigger_targets.items():
        if len(targets) < 2:
            continue
        counter = Counter(targets)
        most_common_c, count = counter.most_common(1)[0]
        confidence = count / len(targets)
        if confidence >= 0.95:  # very high confidence required
            rules.append(TriggerMappingRule(
                input_colour=a,
                trigger_colour=t,
                target_colour=most_common_c,
                confidence=confidence,
                direction=dir_name,
            ))

    return rules


@dataclass
class TriggerMappingRule:
    """A trigger-mapping rule: "colour A with trigger T in direction D → target C".

    The trigger T is a colour that doesn't itself change, but its
    presence in a specific direction causes A to change to C.
    """
    input_colour: int
    trigger_colour: int
    target_colour: int
    confidence: float = 1.0
    direction: str = ""  # N, S, E, W, NE, NW, SE, SW, or "" (any direction)

    def apply_to(self, grid: Grid) -> Grid:
        """Apply: for each cell of input_colour, if it has a trigger_colour
        neighbour in the specified direction, set it to target_colour.
        """
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        DIRS = {
            "N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1),
            "NE": (-1, 1), "NW": (-1, -1), "SE": (1, 1), "SW": (1, -1),
        }
        if self.direction and self.direction in DIRS:
            dirs_to_check = [self.direction]
        else:
            dirs_to_check = list(DIRS.keys())

        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] != self.input_colour:
                    continue
                for dir_name in dirs_to_check:
                    dr, dc = DIRS[dir_name]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        if grid.cells[nr][nc] == self.trigger_colour:
                            out_cells[r][c] = self.target_colour
                            break
        return Grid(out_cells)


def derive_and_verify_trigger(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Derive and verify trigger-mapping rules."""
    rules = derive_trigger_mapping_rules(task)
    if not rules:
        return None, "none", {"n_trigger_rules": 0}

    # Apply ALL rules SIMULTANEOUSLY (in parallel, not sequentially).
    # Each rule only fires if its specific direction has the trigger.
    DIRS = {
        "N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1),
        "NE": (-1, 1), "NW": (-1, -1), "SE": (1, 1), "SW": (1, -1),
    }
    def apply_all_parallel(grid: Grid) -> Grid:
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                # Check each rule's trigger condition on the INPUT grid
                for rule in rules:
                    if grid.cells[r][c] != rule.input_colour:
                        continue
                    if rule.direction and rule.direction in DIRS:
                        dirs_to_check = [rule.direction]
                    else:
                        dirs_to_check = list(DIRS.keys())
                    for dir_name in dirs_to_check:
                        dr, dc = DIRS[dir_name]
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if grid.cells[nr][nc] == rule.trigger_colour:
                                out_cells[r][c] = rule.target_colour
                                break
                    if out_cells[r][c] == rule.target_colour:
                        break  # don't check more rules for this cell
        return Grid(out_cells)

    # Verify against train
    passes = True
    for pair in task.train:
        try:
            if apply_all_parallel(pair.input) != pair.output:
                passes = False
                break
        except Exception:
            passes = False
            break

    if passes:
        pred = apply_all_parallel(task.test[0].input)
        return pred, "cortex_trigger", {
            "n_trigger_rules": len(rules),
            "rules": [(r.input_colour, r.trigger_colour, r.target_colour, r.confidence) for r in rules],
            "passed_train": True,
        }

    return None, "none", {
        "n_trigger_rules": len(rules),
        "rules": [(r.input_colour, r.trigger_colour, r.target_colour, r.confidence) for r in rules],
        "passed_train": False,
    }


def derive_dynamic_contextual_rules(task: ARCTask) -> List[DynamicContextualRule]:
    """Derive dynamic contextual rules.

    For each colour A that changes, check if A's output matches the
    mapped target of its neighbour B.  If so, the rule is:
    "A next to B → mapping[B]".

    ENHANCED: Also discovers rules where A changes to colour C, and
    C is the colour that B (A's neighbour) becomes — even if A doesn't
    appear in the global mapping as A → C directly.

    For 396d80d7:
      - 7 next to 6 → 2 (because in pair 0, 6→2... but actually 6 doesn't
        change in pair 0 either; the rule is more like "7 takes the colour
        of its 6 neighbour's output", where 6→2 in pair 0 and 4→1 in pair 1)
    """
    if not task.train:
        return []

    # Build per-pair colour mappings (since the trigger colour may differ per pair)
    per_pair_mappings = []
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            per_pair_mappings.append({})
            continue
        targets = defaultdict(list)
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    targets[old].append(new)
        m = {old: Counter(t).most_common(1)[0][0] for old, t in targets.items()}
        per_pair_mappings.append(m)

    # For each colour A that changes in ANY pair, check if A's output
    # matches the per-pair-mapped target of its neighbour B
    rules = []
    # Find all colours that ever change
    changing_colours = set()
    for m in per_pair_mappings:
        changing_colours.update(m.keys())

    for old_a in changing_colours:
        match_count = 0
        total_count = 0
        for pair_idx, pair in enumerate(task.train):
            if pair.input.shape != pair.output.shape:
                continue
            mapping = per_pair_mappings[pair_idx]
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if (pair.input.cells[r][c] == old_a and
                            pair.output.cells[r][c] != old_a):
                        total_count += 1
                        target_c = pair.output.cells[r][c]
                        # Check if any neighbour B has mapping[B] == target_c
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = r + dr, c + dc
                                if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                                    n_colour = pair.input.cells[nr][nc]
                                    if mapping.get(n_colour) == target_c:
                                        match_count += 1
                                        break
                            else:
                                continue
                            break

        if total_count > 0 and match_count >= total_count * 0.7:
            # Build a unified mapping (union of all per-pair mappings)
            unified_mapping = {}
            for m in per_pair_mappings:
                unified_mapping.update(m)
            rule = DynamicContextualRule(
                input_colour=old_a,
                global_mapping=unified_mapping,
            )
            rules.append(rule)

    return rules


def derive_and_verify_dynamic(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Derive and verify dynamic contextual rules."""
    rules = derive_dynamic_contextual_rules(task)
    if not rules:
        return None, "none", {"n_dynamic_rules": 0}

    # Apply all dynamic rules together
    def apply_all(grid: Grid) -> Grid:
        result = grid
        for rule in rules:
            result = rule.apply_to(result)
        return result

    # Verify against train
    passes = True
    for pair in task.train:
        try:
            if apply_all(pair.input) != pair.output:
                passes = False
                break
        except Exception:
            passes = False
            break

    if passes:
        pred = apply_all(task.test[0].input)
        return pred, "cortex_dynamic", {
            "n_dynamic_rules": len(rules),
            "rules": [(r.input_colour, r.global_mapping) for r in rules],
            "passed_train": True,
        }

    return None, "none", {
        "n_dynamic_rules": len(rules),
        "passed_train": False,
    }


def derive_and_verify_patterns(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Derive pattern rules, verify, and apply the best combination."""
    rules = derive_pattern_rules(task)
    if not rules:
        return None, "none", {"n_rules": 0}

    # Try applying ALL rules together
    def apply_all(grid: Grid) -> Grid:
        result = grid
        for rule in rules:
            result = rule.apply_to(result)
        return result

    # Verify against train
    passes = True
    for pair in task.train:
        try:
            if apply_all(pair.input) != pair.output:
                passes = False
                break
        except Exception:
            passes = False
            break

    if passes:
        pred = apply_all(task.test[0].input)
        return pred, "cortex_pattern", {
            "n_rules": len(rules),
            "rules": [(r.property_name, r.input_colour, r.output_colour) for r in rules],
            "passed_train": True,
        }

    # Try subsets of rules
    # (For simplicity, try each rule individually)
    for i, rule in enumerate(rules):
        def apply_one(grid: Grid, r=rule):
            return r.apply_to(grid)
        passes = True
        for pair in task.train:
            try:
                if apply_one(pair.input) != pair.output:
                    passes = False
                    break
            except Exception:
                passes = False
                break
        if passes:
            pred = apply_one(task.test[0].input)
            return pred, "cortex_pattern_single", {
                "n_rules": 1,
                "rule": (rule.property_name, rule.input_colour, rule.output_colour),
                "passed_train": True,
            }

    return None, "none", {
        "n_rules": len(rules),
        "rules": [(r.property_name, r.input_colour, r.output_colour) for r in rules],
        "passed_train": False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Top-level cortex prediction
# ══════════════════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """The cortex's full prediction pipeline.

    Tries, in order:
      1. Trigger-mapping rules ("A next to T → C") — most powerful
      2. Dynamic contextual rules ("A next to B → mapping[B]")
      3. Pattern rules ("IF property P THEN transform")
      4. Orthographic rule (global colour mapping)
      5. Perspective rule (focal vs peripheral from Y)
      6. Combined rule
    """
    # Try trigger-mapping rules first (most specific)
    pred, src, diag = derive_and_verify_trigger(task)
    if pred is not None:
        return pred, src, diag

    # Try dynamic contextual rules
    pred, src, diag = derive_and_verify_dynamic(task)
    if pred is not None:
        return pred, src, diag

    # Try pattern rules
    pred, src, diag = derive_and_verify_patterns(task)
    if pred is not None:
        return pred, src, diag

    # Try viewpoint-based rules
    pred, src, diag = derive_and_verify(task)
    if pred is not None:
        return pred, src, diag

    return None, "none", {"cortex_tried": True, "passed_train": False}


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Cortex self-test")
    print("=" * 60)
    print(f"Y = π/(π²+2) = {Y_CONST:.10f}")
    print(f"O = 1/Y = π + 2/π = {O_CONST:.10f}")
    print(f"Y × O = {Y_CONST * O_CONST:.10f} (should be 1.0)")
    print(f"Y_int_24 = {Y_INT_24} (observer eye position in 24-bit space)")

    from arc_loader import TrainPair, TestInput

    # Test 1: orthographic rule (global recolour)
    print("\n[Test 1] Orthographic rule (global recolour 1→2, 2→3)")
    inp = Grid([[1, 2, 0], [1, 2, 0], [1, 2, 0]])
    out = Grid([[2, 3, 0], [2, 3, 0], [2, 3, 0]])
    test = Grid([[1, 2, 0], [1, 2, 0]])
    task = ARCTask(name="recolour",
                   train=[TrainPair(input=inp, output=out)],
                   test=[TestInput(input=test, expected_output=Grid([[2, 3, 0], [2, 3, 0]]))])
    pred, src, diag = predict(task)
    print(f"  src={src}")
    print(f"  pred: {pred.cells if pred else None}")
    print(f"  correct: {pred == task.test[0].expected_output if pred else False}")

    # Test 2: pattern rule (isolated cells change)
    print("\n[Test 2] Pattern rule (isolated 1 → 5)")
    inp2 = Grid([
        [0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0],
    ])
    out2 = Grid([
        [0, 0, 0, 0, 0],
        [0, 5, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 5, 0],
        [0, 0, 0, 0, 0],
    ])
    test2 = Grid([
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 1],
    ])
    expected2 = Grid([
        [0, 0, 0, 0],
        [0, 5, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 5],
    ])
    task2 = ARCTask(name="isolated",
                    train=[TrainPair(input=inp2, output=out2)],
                    test=[TestInput(input=test2, expected_output=expected2)])
    pred2, src2, diag2 = predict(task2)
    print(f"  src={src2}")
    print(f"  pred: {pred2.cells if pred2 else None}")
    print(f"  correct: {pred2 == expected2 if pred2 else False}")

    # Test 3: perspective view
    print("\n[Test 3] Perspective viewpoint on a 4x4 grid")
    grid3 = Grid([
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [1, 2, 3, 4],
        [5, 6, 7, 8],
    ])
    vp_ortho = compute_viewpoint(grid3, mode="orthographic")
    vp_persp = compute_viewpoint(grid3, mode="perspective")
    print(f"  Orthographic: mean_weight={vp_ortho.mean_weight:.3f}, stdev={vp_ortho.weight_stdev:.3f}")
    print(f"    focal_cells={len(vp_ortho.focal_cells)}, peripheral={len(vp_ortho.peripheral_cells)}")
    print(f"  Perspective:  mean_weight={vp_persp.mean_weight:.3f}, stdev={vp_persp.weight_stdev:.3f}")
    print(f"    focal_cells={len(vp_persp.focal_cells)}, peripheral={len(vp_persp.peripheral_cells)}")
    print(f"  Perspective weights (row 0): {[f'{w:.3f}' for w in vp_persp.weights[0]]}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
