"""
cortex_v2.py — the cortex with Y as external observer + wobble + relational rules
==================================================================================

Three corrections from the user:

1. Y is EXTERNAL.  It's the "read" position — between us experiencing
   the results and the mechanisms making the results.  It's NOT inside
   the 24-bit address space.  Using Y_int as a spatial eye position was
   wrong.  Y is the position from which the grid is VIEWED, not a point
   IN the grid.

2. Y needs WOBBLE.  A fixed Y gives deterministic (rigid) observation.
   But ARC tasks are non-deterministic — multiple valid transformations
   can pass train.  The wobble in Y is the source of indeterminism.
   Y is not Y_int = 4440516; Y is a REGION around Y_int, and the
   wobble is the radius of that region.  The cortex samples multiple
   Y positions within the wobble, giving multiple perspectives.

3. Cardinal direction rules.  The cortex needs to express relational
   conditions like "6 in diagonal AND NOT 6 in cardinal".  This is
   what 396d80d7 needs.

The wobble
----------
Y = π/(π²+2) ≈ 0.2646754304...
Y_int = int(Y × 2²⁴) = 4440516

The wobble is derived from Y's own structure:
  Y is transcendental (infinite, non-repeating binary expansion).
  The "wobble" is the part of Y beyond 24 bits — the bits we TRUNCATE
  when we write Y_int.  Concretely:

    Y_exact = Y_int / 2²⁴ + Y_residual
    where Y_residual = Y - Y_int/2²⁴ ≈ 0.0000000... (the truncated tail)

  The wobble radius is |Y_residual| × 2²⁴ — the number of Leech
  addresses that Y "could be" given the truncation.  This is small
  but non-zero, giving the cortex a small region to sample from.

  In practice: the cortex samples K positions within Hamming distance
  wobble_radius of Y_int, computes the perspective view from each,
  and takes the consensus.

Viewpoint comparison via Jaccard
--------------------------------
The user suggested Jaccard similarity to compare viewpoints.

  Jaccard(A, B) = |A ∩ B| / |A ∪ B|

For two viewpoints:
  - Focal cell sets: Jaccard of focal cells
  - If Jaccard ≈ 1: perspectives agree (no new information)
  - If Jaccard < 1: perspectives disagree (new information from Y)

When perspectives disagree, the cortex knows the cells in the
symmetric difference are the "interesting" ones — they're sensitive
to the observer's position.

Relational rules
----------------
Rules that combine multiple conditions:

  AND:  "A has T in direction D1 AND T' in direction D2 → C"
  NOT:  "A has T in direction D1 AND NOT T in direction D2 → C"
  XOR:  "A has T in D1 XOR T in D2 → C"
  CARD: "A has T in cardinal direction (N/S/E/W) → C"
  DIAG: "A has T in diagonal direction (NE/NW/SE/SW) → C"
  CARD_NOT_DIAG: "A has T in cardinal AND NOT in diagonal → C"
  DIAG_NOT_CARD: "A has T in diagonal AND NOT in cardinal → C"

The DIAG_NOT_CARD rule is exactly what 396d80d7 needs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import defaultdict, Counter
import sys, os, math, random

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
# Y as external observer with wobble
# ══════════════════════════════════════════════════════════════════════════════

# Y = π/(π²+2) — the observer constant (EXTERNAL to the system)
Y_CONST = math.pi / (math.pi ** 2 + 2)
O_CONST = 1.0 / Y_CONST  # the observer

# Y in 24-bit space (truncated)
Y_INT_24 = int(Y_CONST * (2 ** 24)) & 0xFFFFFF

# The WOBBLE: Y is transcendental, so its binary expansion is infinite.
# When we truncate to 24 bits, we lose the "tail".  The wobble is the
# region of 24-bit space that Y "could be" given this truncation.
#
# Y_exact = Y_int_24 / 2^24 + Y_residual
# where 0 < Y_residual < 1/2^24 (the truncated tail)
#
# The wobble radius (in Hamming distance) is derived from Y_residual:
#   wobble_radius = ceil(-log2(Y_residual)) bits
#
# Since Y_residual < 1/2^24, wobble_radius >= 24 bits — but that's the
# whole space.  In practice we use a SMALLER wobble derived from Y's
# mathematical structure:
#
# Y's continued fraction has a large term (27) at position 7, meaning
# the 7th convergent (248/937) is a very good rational approximation.
# The "wobble" is the difference between Y and this convergent:
#   Y - 248/937 ≈ 1.6 × 10^-6
#
# Scaled to 24-bit: wobble ≈ 1.6e-6 × 2^24 ≈ 27 Leech addresses
#
# So the wobble radius is ~27 in integer space, which corresponds to
# ~3-4 bits of Hamming distance (since 2^4 = 16, 2^5 = 32).
Y_CONVERGENT = 248.0 / 937.0  # 7th convergent of Y's continued fraction
Y_WOBBLE_ABSOLUTE = abs(Y_CONST - Y_CONVERGENT)  # ≈ 1.6e-6
Y_WOBBLE_24BIT = Y_WOBBLE_ABSOLUTE * (2 ** 24)  # ≈ 27 Leech addresses
Y_WOBBLE_HAMMING = max(1, int(math.log2(max(Y_WOBBLE_24BIT, 2))))  # ~4-5 bits

# Direction constants
CARDINAL_DIRS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
DIAGONAL_DIRS = {"NE": (-1, 1), "NW": (-1, -1), "SE": (1, 1), "SW": (1, -1)}
ALL_DIRS = {**CARDINAL_DIRS, **DIAGONAL_DIRS}


def y_observer_positions(n_samples: int = 5, seed: int = 42) -> List[int]:
    """Sample n positions within the Y wobble region.

    Each position is a 24-bit Leech address within Hamming distance
    Y_WOBBLE_HAMMING of Y_INT_24.  The cortex views the grid from
    each of these positions and takes the consensus.

    The wobble is the source of indeterminism — different Y positions
    give different perspective views, and the cortex explores all of
    them to find robust rules.
    """
    rng = random.Random(seed)
    positions = [Y_INT_24]  # always include the center
    Y_bits = [(Y_INT_24 >> (23 - i)) & 1 for i in range(24)]

    for _ in range(n_samples - 1):
        # Flip 1 to Y_WOBBLE_HAMMING random bits
        n_flips = rng.randint(1, Y_WOBBLE_HAMMING)
        bits = Y_bits[:]
        for _ in range(n_flips):
            idx = rng.randint(0, 23)
            bits[idx] ^= 1
        pos = 0
        for i, b in enumerate(bits):
            if b:
                pos |= (1 << (23 - i))
        positions.append(pos)

    return positions


def cell_weight_from_position(hex_cell: HexCell, observer_pos: int,
                                mode: str = "perspective") -> float:
    """Weight of a cell when viewed from a specific observer position."""
    if mode == "orthographic":
        return 1.0
    dist = _hamming_distance_int(hex_cell.address_int, observer_pos)
    return 1.0 / (1.0 + dist)


# ══════════════════════════════════════════════════════════════════════════════
# Viewpoint with Jaccard comparison
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class WobblyViewpoint:
    """A viewpoint that accounts for Y's wobble.

    Computes perspective views from MULTIPLE Y positions (within the
    wobble) and takes the consensus.  Also computes the orthographic
    view and the Jaccard similarity between them.
    """
    ortho_focal: Set[Tuple[int, int]] = field(default_factory=set)
    persp_focal_consensus: Set[Tuple[int, int]] = field(default_factory=set)
    persp_focal_union: Set[Tuple[int, int]] = field(default_factory=set)
    jaccard_ortho_persp: float = 0.0
    sensitive_cells: Set[Tuple[int, int]] = field(default_factory=set)
    n_observer_samples: int = 0


def compute_wobbly_viewpoint(grid: Grid, focal_threshold: float = 0.5,
                              n_samples: int = 5) -> WobblyViewpoint:
    """Compute a viewpoint that samples multiple Y positions within the wobble.

    Returns:
      - ortho_focal: cells focal under orthographic view (all cells)
      - persp_focal_consensus: cells focal under ALL perspective samples
      - persp_focal_union: cells focal under ANY perspective sample
      - jaccard: similarity between ortho and persp consensus
      - sensitive_cells: cells in the symmetric difference (orthogonal
        to consensus) — these are the "interesting" cells whose focal
        status depends on the observer's position
    """
    addrs = address_grid(grid)
    h, w = grid.shape
    all_cells = {(r, c) for r in range(h) for c in range(w)}

    # Orthographic: all cells are focal
    ortho_focal = all_cells.copy()

    # Sample multiple Y positions within the wobble
    observer_positions = y_observer_positions(n_samples)

    # For each observer position, compute the perspective focal set
    persp_focal_sets = []
    for obs_pos in observer_positions:
        focal = set()
        max_weight = 0.0
        # Find max weight for normalisation
        for r in range(h):
            for c in range(w):
                w_val = cell_weight_from_position(addrs[r][c], obs_pos, "perspective")
                if w_val > max_weight:
                    max_weight = w_val
        # Normalise and threshold
        for r in range(h):
            for c in range(w):
                w_val = cell_weight_from_position(addrs[r][c], obs_pos, "perspective")
                if max_weight > 0 and w_val / max_weight >= focal_threshold:
                    focal.add((r, c))
        persp_focal_sets.append(focal)

    # Consensus: cells focal under ALL samples
    persp_consensus = persp_focal_sets[0].copy() if persp_focal_sets else set()
    for s in persp_focal_sets[1:]:
        persp_consensus &= s

    # Union: cells focal under ANY sample
    persp_union = set()
    for s in persp_focal_sets:
        persp_union |= s

    # Jaccard between ortho and persp consensus
    if ortho_focal or persp_consensus:
        intersection = ortho_focal & persp_consensus
        union = ortho_focal | persp_consensus
        jaccard = len(intersection) / len(union) if union else 0.0
    else:
        jaccard = 0.0

    # Sensitive cells: in symmetric difference
    sensitive = ortho_focal.symmetric_difference(persp_consensus)

    return WobblyViewpoint(
        ortho_focal=ortho_focal,
        persp_focal_consensus=persp_consensus,
        persp_focal_union=persp_union,
        jaccard_ortho_persp=jaccard,
        sensitive_cells=sensitive,
        n_observer_samples=len(observer_positions),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Relational rules
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RelationalRule:
    """A relational rule combining multiple directional conditions.

    Conditions are grouped:
      - has_conditions: list of (colour, direction) — cell must have
        AT LEAST ONE of these (OR semantics)
      - not_conditions: list of (colour, direction_group) — cell must
        NOT have any of these (AND semantics on absence)

    The rule fires if:
      (any has_condition matches) AND (all not_conditions match)

    This handles edge cases where one direction is out of bounds —
    the OR semantics means the rule still fires if at least one
    good direction has the trigger.
    """
    input_colour: int
    has_conditions: List[Tuple[int, str]] = field(default_factory=list)  # OR: any match
    not_conditions: List[Tuple[int, str]] = field(default_factory=list)  # AND: all match
    target_colour: int = 0
    confidence: float = 1.0
    # Legacy field for backward compat
    conditions: List[Tuple[str, int, str]] = field(default_factory=list)

    def applies_to(self, grid: Grid, r: int, c: int) -> bool:
        if grid.cells[r][c] != self.input_colour:
            return False

        # Check has_conditions (OR: at least one must match)
        if self.has_conditions:
            any_match = False
            for colour, direction in self.has_conditions:
                if self._check_has(grid, r, c, colour, direction):
                    any_match = True
                    break
            if not any_match:
                return False

        # Check not_conditions (AND: all must be absent)
        for colour, direction in self.not_conditions:
            if self._check_has(grid, r, c, colour, direction):
                return False  # found where it shouldn't be

        return True

    def _check_has(self, grid: Grid, r: int, c: int,
                    colour: int, direction: str) -> bool:
        h, w = grid.shape
        if direction == "cardinal":
            dirs_to_check = CARDINAL_DIRS
        elif direction == "diagonal":
            dirs_to_check = DIAGONAL_DIRS
        elif direction in ALL_DIRS:
            dirs_to_check = {direction: ALL_DIRS[direction]}
        else:
            dirs_to_check = ALL_DIRS

        for _, (dr, dc) in dirs_to_check.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                if grid.cells[nr][nc] == colour:
                    return True
        return False

    def apply_to(self, grid: Grid) -> Grid:
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if self.applies_to(grid, r, c):
                    out_cells[r][c] = self.target_colour
        return Grid(out_cells)


def derive_relational_rules(task: ARCTask) -> List[RelationalRule]:
    """Derive relational rules from train pairs.

    For each colour A that changes, try to find a combination of
    directional conditions that uniquely identifies the changing cells.

    Strategy:
      1. For each (A → C) change, collect the changing cells and
         unchanged cells of colour A.
      2. For each potential trigger colour T, check specific directions.
      3. Find the combination that separates changing from unchanged.

    Key insight: "diagonal" is too broad.  A cell with 6 in SE is
    different from a cell with 6 in NE.  We check each specific
    direction individually.
    """
    if not task.train:
        return []

    # Collect changing and unchanged cells per (A, C) pair
    changing_cells: Dict[Tuple[int, int], List[Tuple[Grid, int, int]]] = defaultdict(list)
    unchanged_cells: Dict[int, List[Tuple[Grid, int, int]]] = defaultdict(list)

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    changing_cells[(old, new)].append((pair.input, r, c))
                else:
                    unchanged_cells[old].append((pair.input, r, c))

    rules = []
    for (old_a, new_c), changed in changing_cells.items():
        if len(changed) < 2:
            continue

        # Find all trigger colours (non-A neighbours of changing cells)
        trigger_colours = set()
        for grid, r, c in changed:
            for _, (dr, dc) in ALL_DIRS.items():
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    n_colour = grid.cells[nr][nc]
                    if n_colour != old_a:
                        trigger_colours.add(n_colour)

        n_changed = len(changed)
        unchanged = unchanged_cells.get(old_a, [])
        n_unchanged = len(unchanged)

        # For each trigger colour, check EACH SPECIFIC DIRECTION
        for t in trigger_colours:
            # Filter: only consider changed cells that have T as a neighbour
            # (different pairs may have different trigger colours)
            changed_with_t = [(grid, r, c) for grid, r, c in changed
                               if _has_in_directions(grid, r, c, t, ALL_DIRS)]
            unchanged_with_t = [(grid, r, c) for grid, r, c in unchanged
                                 if _has_in_directions(grid, r, c, t, ALL_DIRS)]

            n_changed_t = len(changed_with_t)
            n_unchanged_t = len(unchanged_with_t)
            if n_changed_t < 2:
                continue

            # Count changing cells with T in each specific direction
            changed_in_dir = {d: sum(1 for grid, r, c in changed_with_t
                                       if _has_in_directions(grid, r, c, t, {d: ALL_DIRS[d]}))
                              for d in ALL_DIRS}
            unchanged_in_dir = {d: sum(1 for grid, r, c in unchanged_with_t
                                          if _has_in_directions(grid, r, c, t, {d: ALL_DIRS[d]}))
                                for d in ALL_DIRS}

            # Find directions where changing cells consistently have T
            # but unchanged cells don't
            good_dirs = []
            for d in ALL_DIRS:
                if (changed_in_dir[d] >= n_changed_t * 0.8
                        and unchanged_in_dir[d] <= max(n_unchanged_t * 0.3, 2)):
                    good_dirs.append(d)

            if good_dirs:
                # Create a rule: "A has T in ANY good_dir (OR) → C"
                has_conds = [(t, d) for d in good_dirs]
                rule = RelationalRule(
                    input_colour=old_a,
                    has_conditions=has_conds,
                    not_conditions=[],
                    target_colour=new_c,
                    confidence=min(changed_in_dir[d] / max(n_changed, 1) for d in good_dirs),
                )
                rules.append(rule)

            # Also check: "A has T in cardinal AND NOT in cardinal' → C"
            # (specific cardinal directions)
            changed_card = {d: changed_in_dir[d] for d in CARDINAL_DIRS}
            unchanged_card = {d: unchanged_in_dir[d] for d in CARDINAL_DIRS}
            changed_diag = {d: changed_in_dir[d] for d in DIAGONAL_DIRS}
            unchanged_diag = {d: unchanged_in_dir[d] for d in DIAGONAL_DIRS}

            # Rule: "A has T in ANY diagonal AND NOT in any cardinal"
            # This is the 396d80d7 rule: changed 7s have 6 in diagonal
            # (different specific dirs per cell) but NOT in cardinal.
            changed_any_diag = sum(1 for grid, r, c in changed_with_t
                                     if _has_in_directions(grid, r, c, t, DIAGONAL_DIRS))
            changed_any_card = sum(1 for grid, r, c in changed_with_t
                                     if _has_in_directions(grid, r, c, t, CARDINAL_DIRS))
            unchanged_any_diag = sum(1 for grid, r, c in unchanged_with_t
                                        if _has_in_directions(grid, r, c, t, DIAGONAL_DIRS))
            unchanged_any_card = sum(1 for grid, r, c in unchanged_with_t
                                         if _has_in_directions(grid, r, c, t, CARDINAL_DIRS))

            # If most changed cells have T in diagonal AND NOT in cardinal
            if (changed_any_diag >= n_changed_t * 0.8
                    and changed_any_card <= n_changed_t * 0.2
                    and unchanged_any_card >= n_unchanged_t * 0.5):
                # Rule: "A has T in diagonal (any) AND NOT in cardinal"
                rule = RelationalRule(
                    input_colour=old_a,
                    has_conditions=[(t, "diagonal")],
                    not_conditions=[(t, "cardinal")],
                    target_colour=new_c,
                    confidence=changed_any_diag / max(n_changed_t, 1),
                )
                rules.append(rule)

            # If most changed cells have T in cardinal AND NOT in diagonal
            if (changed_any_card >= n_changed_t * 0.8
                    and changed_any_diag <= n_changed_t * 0.2
                    and unchanged_any_diag >= n_unchanged_t * 0.5):
                rule = RelationalRule(
                    input_colour=old_a,
                    has_conditions=[(t, "cardinal")],
                    not_conditions=[(t, "diagonal")],
                    target_colour=new_c,
                    confidence=changed_any_card / max(n_changed_t, 1),
                )
                rules.append(rule)

            # Rule: "A has T in specific diagonal dirs (OR) AND NOT in any cardinal"
            good_diag = [d for d in DIAGONAL_DIRS
                          if changed_in_dir[d] >= n_changed_t * 0.8
                          and unchanged_in_dir[d] <= max(n_unchanged_t * 0.3, 2)]
            if good_diag:
                has_any_card = sum(1 for grid, r, c in changed_with_t
                                     if _has_in_directions(grid, r, c, t, CARDINAL_DIRS))
                if has_any_card <= n_changed_t * 0.2:  # most changed cells DON'T have T in cardinal
                    has_conds = [(t, d) for d in good_diag]
                    not_conds = [(t, "cardinal")]
                    rule = RelationalRule(
                        input_colour=old_a,
                        has_conditions=has_conds,
                        not_conditions=not_conds,
                        target_colour=new_c,
                        confidence=0.95,
                    )
                    rules.append(rule)

            # Rule: "A has T in specific cardinal dirs (OR) AND NOT in any diagonal"
            good_card = [d for d in CARDINAL_DIRS
                          if changed_in_dir[d] >= n_changed_t * 0.8
                          and unchanged_in_dir[d] <= max(n_unchanged_t * 0.3, 2)]
            if good_card:
                has_any_diag = sum(1 for grid, r, c in changed_with_t
                                     if _has_in_directions(grid, r, c, t, DIAGONAL_DIRS))
                if has_any_diag <= n_changed_t * 0.2:
                    has_conds = [(t, d) for d in good_card]
                    not_conds = [(t, "diagonal")]
                    rule = RelationalRule(
                        input_colour=old_a,
                        has_conditions=has_conds,
                        not_conditions=not_conds,
                        target_colour=new_c,
                        confidence=0.95,
                    )
                    rules.append(rule)

    return rules


def _has_in_directions(grid: Grid, r: int, c: int, colour: int,
                        dirs: Dict[str, Tuple[int, int]]) -> bool:
    """Check if cell (r, c) has a neighbour of `colour` in any of the given directions."""
    h, w = grid.shape
    for _, (dr, dc) in dirs.items():
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            if grid.cells[nr][nc] == colour:
                return True
    return False


def derive_and_verify_relational(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Derive and verify relational rules."""
    rules = derive_relational_rules(task)
    if not rules:
        return None, "none", {"n_relational_rules": 0}

    # Apply ALL rules in parallel (check input grid, write atomically)
    def apply_all_parallel(grid: Grid) -> Grid:
        h, w = grid.shape
        out_cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                for rule in rules:
                    if rule.applies_to(grid, r, c):
                        out_cells[r][c] = rule.target_colour
                        break  # first matching rule wins
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
        return pred, "cortex_relational", {
            "n_relational_rules": len(rules),
            "rules": [(r.input_colour, r.conditions, r.target_colour, r.confidence) for r in rules],
            "passed_train": True,
        }

    # Try subsets of rules
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
            return pred, "cortex_relational_single", {
                "n_relational_rules": 1,
                "rule": (rule.input_colour, rule.conditions, rule.target_colour),
                "passed_train": True,
            }

    return None, "none", {
        "n_relational_rules": len(rules),
        "rules": [(r.input_colour, r.conditions, r.target_colour, r.confidence) for r in rules],
        "passed_train": False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Top-level cortex v2 prediction
# ══════════════════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """The cortex v2 prediction pipeline.

    Tries, in order:
      1. Relational rules (cardinal/diagonal AND/OR NOT) — most powerful
      2. Trigger-mapping rules (directional)
      3. Pattern rules
      4. Orthographic rule
      5. Perspective rule (with wobble — samples multiple Y positions)
    """
    # Compute the wobbly viewpoint for diagnostics
    try:
        vp = compute_wobbly_viewpoint(task.test[0].input)
        jaccard = vp.jaccard_ortho_persp
        n_sensitive = len(vp.sensitive_cells)
    except Exception:
        jaccard = 1.0
        n_sensitive = 0

    # Try relational rules first
    pred, src, diag = derive_and_verify_relational(task)
    if pred is not None:
        diag["jaccard_ortho_persp"] = jaccard
        diag["n_sensitive_cells"] = n_sensitive
        diag["y_wobble_hamming"] = Y_WOBBLE_HAMMING
        return pred, src, diag

    # Fall back to v1 cortex rules
    from vendor.cortex import (
        derive_and_verify_trigger, derive_and_verify_dynamic,
        derive_and_verify_patterns, derive_and_verify,
    )

    for fn, name in [
        (derive_and_verify_trigger, "trigger"),
        (derive_and_verify_dynamic, "dynamic"),
        (derive_and_verify_patterns, "pattern"),
        (derive_and_verify, "viewpoint"),
    ]:
        try:
            pred, src, diag = fn(task)
            if pred is not None:
                diag["jaccard_ortho_persp"] = jaccard
                diag["n_sensitive_cells"] = n_sensitive
                diag["y_wobble_hamming"] = Y_WOBBLE_HAMMING
                return pred, src, diag
        except Exception:
            continue

    return None, "none", {
        "jaccard_ortho_persp": jaccard,
        "n_sensitive_cells": n_sensitive,
        "y_wobble_hamming": Y_WOBBLE_HAMMING,
        "passed_train": False,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Cortex v2 self-test")
    print("=" * 60)
    print(f"Y = π/(π²+2) = {Y_CONST:.10f}")
    print(f"Y_int_24 = {Y_INT_24}")
    print(f"Y convergent (248/937) = {Y_CONVERGENT:.10f}")
    print(f"Y wobble (absolute) = {Y_WOBBLE_ABSOLUTE:.2e}")
    print(f"Y wobble (24-bit) = {Y_WOBBLE_24BIT:.1f} Leech addresses")
    print(f"Y wobble (Hamming) = {Y_WOBBLE_HAMMING} bits")

    # Test observer positions
    positions = y_observer_positions(5)
    print(f"\nSampled {len(positions)} observer positions:")
    for i, p in enumerate(positions):
        dist = _hamming_distance_int(p, Y_INT_24)
        print(f"  pos[{i}]: {p}, Hamming distance from Y = {dist}")

    from arc_loader import TrainPair, TestInput

    # Test 1: relational rule (diagonal NOT cardinal) — the 396d80d7 pattern
    # Grid:
    #   7 7 7 7 7     row 0
    #   7 7 7 7 7     row 1
    #   6 7 6 7 6     row 2  (6s at cols 0, 2, 4)
    #   7 7 7 7 7     row 3
    #   7 7 7 7 7     row 4
    #
    # (1,1): SE=(2,2)=6, SW=(2,0)=6 → diagonal only ✓
    # (1,2): S=(2,2)=6 → cardinal ✗
    # (1,3): SE=(2,4)=6, SW=(2,2)=6 → diagonal only ✓
    # So (1,1) and (1,3) should change; (1,2) should NOT
    print("\n[Test 1] Relational rule: 7 with 6 in diagonal AND NOT cardinal → 2")
    inp = Grid([
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    out = Grid([
        [7, 7, 7, 7, 7],
        [7, 2, 7, 2, 7],  # (1,1) and (1,3) change
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    test = Grid([
        [7, 7, 7, 7],
        [7, 7, 7, 7],
        [6, 7, 6, 7],
        [7, 7, 7, 7],
    ])
    expected = Grid([
        [7, 7, 7, 7],
        [7, 2, 7, 2],  # (1,1) and (1,3) change
        [6, 7, 6, 7],
        [7, 7, 7, 7],
    ])
    task = ARCTask(name="diag_not_card",
                   train=[TrainPair(input=inp, output=out)],
                   test=[TestInput(input=test, expected_output=expected)])
    pred, src, diag = predict(task)
    print(f"  src={src}")
    print(f"  pred: {pred.cells if pred else None}")
    print(f"  expected: {expected.cells}")
    print(f"  correct: {pred == expected if pred else False}")
    if diag.get("n_relational_rules"):
        print(f"  rules: {diag['n_relational_rules']}")
        for r in diag.get("rules", []):
            print(f"    {r}")

    # Test 2: wobbly viewpoint
    print("\n[Test 2] Wobbly viewpoint")
    grid = Grid([
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [1, 2, 3, 4],
        [5, 6, 7, 8],
    ])
    vp = compute_wobbly_viewpoint(grid, n_samples=5)
    print(f"  ortho focal: {len(vp.ortho_focal)}")
    print(f"  persp consensus: {len(vp.persp_focal_consensus)}")
    print(f"  persp union: {len(vp.persp_focal_union)}")
    print(f"  Jaccard(ortho, persp): {vp.jaccard_ortho_persp:.3f}")
    print(f"  sensitive cells: {len(vp.sensitive_cells)}")
    print(f"  n observer samples: {vp.n_observer_samples}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
