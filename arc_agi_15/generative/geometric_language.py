"""
geometric_language.py — the language of geometry
=================================================

The user's insight: "the language of geometry I think is just direction,
Time and rotation".  This module makes those three primitives
first-class citizens of the GLM.

Three primitives
----------------

  DIRECTION  — a vector in 24-bit address space.  Two cells have a
               direction between them: the XOR of their addresses,
               interpreted as a 24-bit signed displacement via the
               Gray-map lift (HDRB Pillar 2).  Directions live on the
               unit sphere S²³ ⊂ R²⁴ after normalisation.

  TIME       — a sequence index.  A train pair (input, output) is a
               2-step Time sequence: t=0 → t=1.  A chain of n train
               pairs is an n-step Time sequence.  Time lets us talk
               about "before" and "after" without committing to a
               clock — the clock IS the train sequence.

  ROTATION   — an element of the dihedral group D4 (the symmetry of
               the square), augmented with colour-permutation
               symmetries.  Rotations act on cells by permuting their
               (row, col) coordinates and optionally their colour
               palette.  There are 8 spatial rotations (D4) and 10!
               colour permutations, but for ARC we restrict to the
               rotations that appear in train.

The k-arm
---------

The k-NN is reframed as a sensory ARM:

  - SHOULDER: anchored at the test cell (its 24-bit address)
  - ELBOW:    a rotation in D4 (which way to orient the arm)
  - WRIST:    a Time step (how far forward to project)
  - FINGERTIPS: the K nearest train cells in 24-bit Hamming space

The arm is FREE — it is NOT anchored at Y (the observer constant).
Y is available as a diagnostic, but it does not constrain the arm's
motion.  This is the user's point: "if one end of the k are is always
anchored to the 'Y' Observer then the motion is limited".

The arm VOTES: each fingertip feels a delta (the train cell's
transformation).  The wrist decides the Time projection.  The elbow
decides the rotation.  The shoulder applies the voted, rotated,
projected delta to the test cell.

Geometric sentences
-------------------

A "sentence" in the geometric language is a sequence of (direction,
Time, rotation) triples that describes a transformation:

    "cell at (r,c) moved by direction d, over 1 Time step, under rotation ρ"

The GLM's job is to read the train pairs, write the sentence that
describes the transformation, and apply that sentence to the test
input.  This is what "language machine, not script pipeline" means.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import defaultdict, Counter
import sys, os, math, itertools

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
_VENDOR = os.path.join(_PARENT, "vendor")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

from arc_loader import Grid, ARCTask
from ubp_unified_v5 import GOLAY_ENGINE, ontological_position_to_vector
from GLM18_hex_colour import vector_to_colour

# Reuse the hex-cell address logic from hex_learner (don't duplicate)
from generative.hex_learner import (
    HexCell, address_cell, address_grid, _hamming_distance_int,
)


# ══════════════════════════════════════════════════════════════════════════════
# PRIMITIVE 1 — DIRECTION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Direction:
    """A direction in 24-bit address space.

    The direction from cell A to cell B is  addr_B XOR addr_A,
    interpreted as a 24-bit displacement.  We store:
      - delta_int:    the raw XOR
      - hamming:      the Hamming weight (number of bits moved)
      - unit_vector:  delta lifted to R^12 and L2-normalised
    """
    delta_int: int
    hamming: int
    unit_vector: Tuple[float, ...]

    @classmethod
    def between(cls, cell_a: HexCell, cell_b: HexCell) -> "Direction":
        delta = cell_a.address_int ^ cell_b.address_int
        hamming = bin(delta).count("1")
        # Lift to R^12 via Gray map (HDRB Pillar 2)
        v24 = [(delta >> (23 - i)) & 1 for i in range(24)]
        from hdrb import lift_to_real
        r12 = lift_to_real(v24)
        norm = math.sqrt(sum(x * x for x in r12))
        if norm < 1e-12:
            unit = tuple(0.0 for _ in range(12))
        else:
            unit = tuple(x / norm for x in r12)
        return cls(delta_int=delta, hamming=hamming, unit_vector=unit)

    def __repr__(self):
        return f"Direction(Δ={hex(self.delta_int)}, hw={self.hamming})"


# ══════════════════════════════════════════════════════════════════════════════
# PRIMITIVE 2 — TIME
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TimeSequence:
    """A sequence of grids representing a temporal evolution.

    For ARC, a train pair (input, output) is a 2-step Time sequence.
    Multiple train pairs concatenate into a longer Time sequence.
    The TIME primitive lets us talk about "step 0 → step 1" without
    committing to a clock — the train pairs ARE the clock.
    """
    grids: List[Grid] = field(default_factory=list)

    @classmethod
    def from_train_pairs(cls, train_pairs) -> "TimeSequence":
        """Build a Time sequence from train pairs.

        Each pair contributes (input, output) = (t=k, t=k+1).
        """
        grids = []
        for p in train_pairs:
            grids.append(p.input)
            grids.append(p.output)
        return cls(grids=grids)

    def step_count(self) -> int:
        return max(0, len(self.grids) - 1)

    def directions_at_step(self, t: int) -> List[Direction]:
        """Get the per-cell directions at Time step t → t+1.

        Returns one Direction per cell (row-major order).
        Requires that grid[t] and grid[t+1] have the same shape.
        """
        if t + 1 >= len(self.grids):
            return []
        g_in, g_out = self.grids[t], self.grids[t + 1]
        if g_in.shape != g_out.shape:
            return []
        in_cells = [c for row in address_grid(g_in) for c in row]
        out_cells = [c for row in address_grid(g_out) for c in row]
        return [Direction.between(a, b) for a, b in zip(in_cells, out_cells)]


# ══════════════════════════════════════════════════════════════════════════════
# PRIMITIVE 3 — ROTATION (D4 dihedral group + colour permutations)
# ══════════════════════════════════════════════════════════════════════════════

# The 8 elements of D4 (symmetries of the square)
D4_ROTATIONS = [
    ("identity", lambda r, c, h, w: (r, c)),
    ("rot90",    lambda r, c, h, w: (c, w - 1 - r)),
    ("rot180",   lambda r, c, h, w: (h - 1 - r, w - 1 - c)),
    ("rot270",   lambda r, c, h, w: (w - 1 - c, r)),
    ("flip_h",   lambda r, c, h, w: (r, w - 1 - c)),
    ("flip_v",   lambda r, c, h, w: (h - 1 - r, c)),
    ("transpose",lambda r, c, h, w: (c, r)),
    ("anti_transpose", lambda r, c, h, w: (w - 1 - c, h - 1 - r)),
]


def apply_rotation(grid: Grid, rotation_name: str) -> Grid:
    """Apply a D4 rotation to a grid."""
    h, w = grid.shape
    rot = next((fn for name, fn in D4_ROTATIONS if name == rotation_name), None)
    if rot is None:
        raise ValueError(f"unknown rotation: {rotation_name}")
    # For transpose/anti_transpose, dimensions swap
    if rotation_name in ("transpose", "anti_transpose"):
        new_h, new_w = w, h
    else:
        new_h, new_w = h, w
    out = [[0] * new_w for _ in range(new_h)]
    for r in range(h):
        for c in range(w):
            nr, nc = rot(r, c, h, w)
            out[nr][nc] = grid.cells[r][c]
    return Grid(out)


def infer_rotation(in_grid: Grid, out_grid: Grid) -> Optional[str]:
    """Infer which D4 rotation maps in → out.  Returns None if no match."""
    if in_grid.shape != out_grid.shape and not (
        (in_grid.shape[0] == out_grid.shape[1] and in_grid.shape[1] == out_grid.shape[0])
    ):
        return None
    for name, _ in D4_ROTATIONS:
        try:
            if apply_rotation(in_grid, name) == out_grid:
                return name
        except Exception:
            continue
    return None


# ══════════════════════════════════════════════════════════════════════════════
# GEOMETRIC SENTENCE — a transformation described in the language
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GeometricSentence:
    """A sentence in the geometric language.

    Describes a transformation as:
      - rotation:  the D4 rotation applied (or "identity")
      - time_steps: how many Time steps to project forward
      - direction_mode: the most common direction (as a delta_int)
      - direction_mode_hamming: the Hamming weight of that direction
      - per_colour_directions: dict {colour: (delta_int, count)}
      - per_position_directions: dict {(r_frac, c_frac): (delta_int, count)}

    The sentence is what the GLM "says" about the transformation.
    Applying the sentence to a test grid = predicting the test output.
    """
    rotation: str = "identity"
    time_steps: int = 1
    direction_mode: int = 0
    direction_mode_hamming: int = 0
    direction_confidence: float = 0.0
    per_colour_directions: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    per_position_directions: Dict[Tuple[float, float], Tuple[int, int]] = field(default_factory=dict)
    colour_mapping: Dict[int, int] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"GeometricSentence:",
            f"  rotation: {self.rotation}",
            f"  time_steps: {self.time_steps}",
            f"  direction_mode: Δ={hex(self.direction_mode)} (hw={self.direction_mode_hamming})",
            f"  direction_confidence: {self.direction_confidence:.2f}",
            f"  per_colour_directions: {len(self.per_colour_directions)} colours",
            f"  per_position_directions: {len(self.per_position_directions)} positions",
            f"  colour_mapping: {self.colour_mapping}",
        ]
        return "\n".join(lines)


def read_sentence(task: ARCTask) -> GeometricSentence:
    """Read the geometric sentence that describes a task's transformation.

    Walks the train pairs, computes the per-cell Direction at each
    Time step, and aggregates into a sentence.
    """
    sentence = GeometricSentence()

    # Check for a global rotation first
    rotations_seen = Counter()
    for pair in task.train:
        rot = infer_rotation(pair.input, pair.output)
        if rot:
            rotations_seen[rot] += 1
    if rotations_seen:
        sentence.rotation, _ = rotations_seen.most_common(1)[0]

    # Compute directions across all train pairs
    all_directions: List[Direction] = []
    colour_dirs: Dict[int, List[int]] = defaultdict(list)
    position_dirs: Dict[Tuple[float, float], List[int]] = defaultdict(list)
    colour_targets: Dict[int, List[int]] = defaultdict(list)

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        in_addrs = address_grid(pair.input)
        out_addrs = address_grid(pair.output)
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                in_cell = in_addrs[r][c]
                out_cell = out_addrs[r][c]
                d = Direction.between(in_cell, out_cell)
                all_directions.append(d)
                colour_dirs[in_cell.colour].append(d.delta_int)
                pos_key = (round(in_cell.row_frac * 4) / 4,
                           round(in_cell.col_frac * 4) / 4)
                position_dirs[pos_key].append(d.delta_int)
                if in_cell.colour != out_cell.colour:
                    colour_targets[in_cell.colour].append(out_cell.colour)

    # Mode direction
    if all_directions:
        delta_counts = Counter(d.delta_int for d in all_directions)
        sentence.direction_mode, top_count = delta_counts.most_common(1)[0]
        sentence.direction_mode_hamming = bin(sentence.direction_mode).count("1")
        sentence.direction_confidence = top_count / len(all_directions)

    # Per-colour mode direction
    for colour, deltas in colour_dirs.items():
        if deltas:
            mode_delta = Counter(deltas).most_common(1)[0][0]
            sentence.per_colour_directions[colour] = (mode_delta, len(deltas))

    # Per-position mode direction (quantised)
    for pos, deltas in position_dirs.items():
        if deltas:
            mode_delta = Counter(deltas).most_common(1)[0][0]
            sentence.per_position_directions[pos] = (mode_delta, len(deltas))

    # Colour mapping
    for colour, targets in colour_targets.items():
        if targets:
            mode_target = Counter(targets).most_common(1)[0][0]
            sentence.colour_mapping[colour] = mode_target

    return sentence


# ══════════════════════════════════════════════════════════════════════════════
# THE FREE K-ARM — apply a sentence to a test grid
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class KArmConfig:
    """Configuration for the k-arm sensory exploration."""
    k: int = 7                  # number of fingertips (train neighbours)
    uncertainty_threshold: float = 0.5  # below this confidence, fall back
    use_rotation: bool = True   # rotate test cell if rotation in sentence
    use_time: bool = True       # project through Time if sentence says so
    use_per_colour: bool = True # use per-colour directions if available
    use_per_position: bool = True  # use per-position directions if available
    use_neighbourhood: bool = True  # use per-(colour, neighbourhood) lookup
    # The arm is FREE: Y is not used to constrain the arm.  Y is only
    # available as a diagnostic after the fact.


def apply_sentence(test_input: Grid, sentence: GeometricSentence,
                   train_deltas: List[Tuple[HexCell, HexCell]],
                   config: KArmConfig = KArmConfig(),
                   neighbourhood_table: Optional[Dict] = None) -> Grid:
    """Apply a geometric sentence to a test grid using the free k-arm.

    The k-arm:
      1. SHOULDER: anchored at the test cell
      2. ELBOW:    applies the rotation from the sentence (if use_rotation)
      3. WRIST:    projects through Time (if use_time)
      4. FINGERTIPS: K nearest train cells, vote on delta

    The arm is NOT anchored at Y.  Y is available as a diagnostic only.

    Lookup priority (deeper learning first):
      1. Neighbourhood lookup (colour + 8 neighbours) — catches gravity, copy
      2. Per-position lookup — catches position-conditional recolour
      3. Per-colour lookup — catches plain recolour
      4. k-NN voting — the exploratory arm
      5. Colour mapping fallback — uncertain cells
    """
    # If the sentence has a rotation, apply it first
    rotated_input = test_input
    if config.use_rotation and sentence.rotation != "identity":
        try:
            rotated_input = apply_rotation(test_input, sentence.rotation)
        except Exception:
            rotated_input = test_input

    # Build the train address index
    train_in = [(in_cell.address_int, in_cell, out_cell)
                for in_cell, out_cell in train_deltas]
    train_out = [(out_cell.address_int, out_cell.colour)
                 for _, out_cell in train_deltas]

    h, w = rotated_input.shape
    out_cells = []
    n_uncertain = 0
    n_neighbourhood_hits = 0
    n_position_hits = 0
    n_colour_hits = 0
    n_knn_hits = 0
    n_soft_hits = 0

    for r in range(h):
        row = []
        for c in range(w):
            test_cell = address_cell(r, c, rotated_input.cells[r][c], h, w)
            test_addr = test_cell.address_int

            # ── 1. SOFT NEIGHBOURHOOD MATCHING (the deeper learning) ──
            # For each test cell, gather ALL train entries whose
            # neighbourhood is similar, weighted by similarity score.
            # Vote on output colour with confidence = weighted agreement.
            if (config.use_neighbourhood and neighbourhood_table is not None):
                sig = _neighbourhood_signature(rotated_input, r, c)

                # 1a. Exact neighbourhood match → high confidence
                key = (test_cell.colour, sig)
                if key in neighbourhood_table:
                    entries = neighbourhood_table[key]
                    from collections import Counter
                    colour_votes = Counter(oc for _, oc in entries)
                    out_colour, top_count = colour_votes.most_common(1)[0]
                    confidence = top_count / len(entries)
                    if confidence >= config.uncertainty_threshold:
                        row.append(out_colour)
                        n_neighbourhood_hits += 1
                        continue

                # 1b. SOFT match — weighted vote across all train entries
                #     with the same input colour.  Weight = (match_score/9)^2
                #     so a 9/9 match contributes 1.0, a 7/9 match contributes
                #     0.60, a 5/9 match contributes 0.31, etc.
                #     This is the "wobble" — we don't require exact context,
                #     we just prefer high-similarity contexts.
                colour_weights: Dict[int, float] = defaultdict(float)
                total_weight = 0.0
                for (nk_colour, nk_sig), entries in neighbourhood_table.items():
                    if nk_colour != test_cell.colour:
                        continue
                    score = _neighbourhood_match(sig, nk_sig)
                    if score < 4:  # at least 4/9 must match to contribute
                        continue
                    weight = (score / 9.0) ** 2  # quadratic falloff
                    for _, out_colour in entries:
                        colour_weights[out_colour] += weight
                        total_weight += weight

                if total_weight > 0 and colour_weights:
                    # Pick the colour with highest weighted vote
                    best_colour = max(colour_weights, key=colour_weights.get)
                    confidence = colour_weights[best_colour] / total_weight
                    if confidence >= config.uncertainty_threshold:
                        row.append(best_colour)
                        n_soft_hits += 1
                        continue
                    # Even below threshold, if one colour dominates clearly
                    # (e.g. ≥2× the next), use it — this catches cases where
                    # the vote is split but one option is strongly favoured.
                    if len(colour_weights) >= 2:
                        sorted_votes = sorted(colour_weights.values(), reverse=True)
                        if sorted_votes[0] >= 2.0 * sorted_votes[1]:
                            row.append(best_colour)
                            n_soft_hits += 1
                            continue

            # ── 2. Per-position lookup ──
            pos_key = (round(test_cell.row_frac * 4) / 4,
                       round(test_cell.col_frac * 4) / 4)
            if (config.use_per_position
                    and pos_key in sentence.per_position_directions):
                delta = sentence.per_position_directions[pos_key][0]
                predicted = _lookup_colour(test_cell, delta, train_out)
                if predicted is not None:
                    row.append(predicted)
                    n_position_hits += 1
                    continue

            # ── 3. Per-colour lookup ──
            if (config.use_per_colour
                    and test_cell.colour in sentence.per_colour_directions):
                delta = sentence.per_colour_directions[test_cell.colour][0]
                predicted = _lookup_colour(test_cell, delta, train_out)
                if predicted is not None:
                    row.append(predicted)
                    n_colour_hits += 1
                    continue

            # ── 4. k-arm: find K nearest train cells, vote on delta ──
            dists = [(_hamming_distance_int(test_addr, ta), ta, in_cell, out_cell)
                     for ta, in_cell, out_cell in train_in]
            dists.sort(key=lambda x: x[0])
            top_k = dists[:config.k]

            # Exact match (distance 0) → always use
            if top_k and top_k[0][0] == 0:
                top_delta = top_k[0][3].address_int ^ top_k[0][2].address_int
                confidence = 1.0
            else:
                # Vote on delta
                delta_votes = Counter(
                    out_cell.address_int ^ in_cell.address_int
                    for _, _, in_cell, out_cell in top_k
                )
                top_delta, top_count = delta_votes.most_common(1)[0]
                confidence = top_count / len(top_k)

            if confidence < config.uncertainty_threshold:
                # Uncertain — fall back to colour mapping
                n_uncertain += 1
                if test_cell.colour in sentence.colour_mapping:
                    row.append(sentence.colour_mapping[test_cell.colour])
                else:
                    row.append(test_cell.colour)
                continue

            row.append(_lookup_colour(test_cell, top_delta, train_out))
            n_knn_hits += 1

        out_cells.append(row)

    pred = Grid(out_cells)

    # If we rotated the input, rotate the output back
    if config.use_rotation and sentence.rotation != "identity":
        inverse_rot = _inverse_rotation(sentence.rotation)
        if inverse_rot != "identity":
            try:
                pred = apply_rotation(pred, inverse_rot)
            except Exception:
                pass

    return pred


def _lookup_colour(test_cell: HexCell, delta: int,
                   train_out: List[Tuple[int, int]]) -> int:
    """Apply delta to test_cell's address, then find nearest train output colour."""
    out_addr = test_cell.address_int ^ delta
    best_dist = 25
    best_colour = test_cell.colour
    for to_addr, to_colour in train_out:
        dist = _hamming_distance_int(out_addr, to_addr)
        if dist < best_dist:
            best_dist = dist
            best_colour = to_colour
            if dist == 0:
                break
    return best_colour


def _inverse_rotation(name: str) -> str:
    """Inverse of a D4 rotation."""
    inverses = {
        "identity": "identity",
        "rot90": "rot270",
        "rot180": "rot180",
        "rot270": "rot90",
        "flip_h": "flip_h",
        "flip_v": "flip_v",
        "transpose": "transpose",
        "anti_transpose": "anti_transpose",
    }
    return inverses.get(name, "identity")


def _neighbourhood_signature(grid: Grid, r: int, c: int) -> Tuple[int, ...]:
    """The 8-cell neighbourhood signature of (r, c).

    Returns a tuple of 9 colours: (NW, N, NE, W, center, E, SW, S, SE).
    Out-of-bounds cells are treated as 0 (background).
    """
    h, w = grid.shape
    sig = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                sig.append(grid.cells[nr][nc])
            else:
                sig.append(0)
    return tuple(sig)


def _collect_train_neighbourhoods(task: ARCTask
                                   ) -> Dict[Tuple[int, Tuple[int, ...]], List[Tuple[int, int]]]:
    """Collect per-(colour, neighbourhood) → list of (delta_int, output_colour).

    This is the "deeper learning": instead of just per-colour or per-position,
    we index train deltas by (input_colour, input_neighbourhood).  This
    captures contextual transformations like gravity (a cell becomes X
    because there's an X above it).
    """
    from generative.hex_learner import address_cell
    table: Dict[Tuple[int, Tuple[int, ...]], List[Tuple[int, int]]] = defaultdict(list)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        in_addrs = address_grid(pair.input)
        out_addrs = address_grid(pair.output)
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                in_cell = in_addrs[r][c]
                out_cell = out_addrs[r][c]
                sig = _neighbourhood_signature(pair.input, r, c)
                delta = in_cell.address_int ^ out_cell.address_int
                table[(in_cell.colour, sig)].append((delta, out_cell.colour))
    return table


def _neighbourhood_match(sig_a: Tuple[int, ...], sig_b: Tuple[int, ...]) -> int:
    """How many of the 9 neighbourhood cells match between two signatures.

    Returns 0-9.  Higher = better match.  Used as a soft similarity
    metric when an exact neighbourhood match isn't found.
    """
    return sum(1 for a, b in zip(sig_a, sig_b) if a == b)

def _passes_train(task: ARCTask, pred_fn) -> bool:
    for pair in task.train:
        try:
            if pred_fn(pair.input) != pair.output:
                return False
        except Exception:
            return False
    return True


def collect_train_deltas(task: ARCTask) -> List[Tuple[HexCell, HexCell]]:
    """Collect all (input, output) cell pairs from train."""
    deltas = []
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        in_addrs = address_grid(pair.input)
        out_addrs = address_grid(pair.output)
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                deltas.append((in_addrs[r][c], out_addrs[r][c]))
    return deltas


def predict_with_free_arm(task: ARCTask,
                          config: KArmConfig = KArmConfig()
                          ) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """Predict using the free k-arm driven by a geometric sentence.

    Decision tree:
      1. If sentence.rotation explains every train pair exactly → apply rotation
         to the test input.  Done.  (The rotation IS the transformation.)
      2. If sentence.direction_mode == 0 with confidence 1.0 → identity.  Return
         test input unchanged.
      3. Otherwise → run the full k-arm (rotation as view alignment + per-cell
         delta lookup).
    """
    sentence = read_sentence(task)
    train_deltas = collect_train_deltas(task)

    if not train_deltas:
        return None, "none", {"reason": "no same-shape train pairs"}

    # ── Decision 1: rotation alone explains train ──
    if config.use_rotation and sentence.rotation != "identity":
        all_match = True
        for pair in task.train:
            try:
                if apply_rotation(pair.input, sentence.rotation) != pair.output:
                    all_match = False
                    break
            except Exception:
                all_match = False
                break
        if all_match:
            try:
                pred = apply_rotation(task.test[0].input, sentence.rotation)
                return pred, "rotation_only", {
                    "sentence": sentence.__dict__,
                    "decision": "rotation_explains_train",
                    "passed_train": True,
                }
            except Exception:
                pass

    # ── Decision 2: identity (mode delta = 0, confidence 1.0) ──
    if (sentence.direction_mode == 0
            and sentence.direction_confidence >= 0.99):
        # Verify identity against train
        all_identity = True
        for pair in task.train:
            if pair.input != pair.output:
                all_identity = False
                break
        if all_identity:
            pred = task.test[0].input.copy()
            return pred, "identity", {
                "sentence": sentence.__dict__,
                "decision": "identity",
                "passed_train": True,
            }

    # ── Decision 3: full k-arm ──
    # Build the neighbourhood table (deeper learning)
    neighbourhood_table = None
    if config.use_neighbourhood:
        neighbourhood_table = _collect_train_neighbourhoods(task)

    def pred_fn(grid: Grid) -> Grid:
        return apply_sentence(grid, sentence, train_deltas, config, neighbourhood_table)

    if _passes_train(task, pred_fn):
        pred = pred_fn(task.test[0].input)
        return pred, "free_k_arm", {
            "sentence": sentence.__dict__,
            "config": config.__dict__,
            "decision": "full_k_arm",
            "passed_train": True,
            "neighbourhood_entries": len(neighbourhood_table) if neighbourhood_table else 0,
        }

    # Try without rotation
    if config.use_rotation:
        config2 = KArmConfig(**{**config.__dict__, "use_rotation": False})
        def pred_fn2(grid: Grid) -> Grid:
            return apply_sentence(grid, sentence, train_deltas, config2, neighbourhood_table)
        if _passes_train(task, pred_fn2):
            pred = pred_fn2(task.test[0].input)
            return pred, "free_k_arm_no_rot", {
                "sentence": sentence.__dict__,
                "config": config2.__dict__,
                "decision": "full_k_arm_no_rot",
                "passed_train": True,
                "neighbourhood_entries": len(neighbourhood_table) if neighbourhood_table else 0,
            }

    # Try per-position only (no neighbourhood, no rotation)
    config3 = KArmConfig(
        k=config.k, use_rotation=False, use_time=False,
        use_per_colour=False, use_per_position=True, use_neighbourhood=False,
    )
    def pred_fn3(grid: Grid) -> Grid:
        return apply_sentence(grid, sentence, train_deltas, config3, None)
    if _passes_train(task, pred_fn3):
        pred = pred_fn3(task.test[0].input)
        return pred, "free_k_arm_pos_only", {
            "sentence": sentence.__dict__,
            "config": config3.__dict__,
            "decision": "pos_only",
            "passed_train": True,
        }

    # Try neighbourhood-only (no per-position, no per-colour, no k-NN)
    if config.use_neighbourhood and neighbourhood_table:
        config4 = KArmConfig(
            k=config.k, use_rotation=False, use_time=False,
            use_per_colour=False, use_per_position=False, use_neighbourhood=True,
        )
        def pred_fn4(grid: Grid) -> Grid:
            return apply_sentence(grid, sentence, train_deltas, config4, neighbourhood_table)
        if _passes_train(task, pred_fn4):
            pred = pred_fn4(task.test[0].input)
            return pred, "free_k_arm_neighbourhood", {
                "sentence": sentence.__dict__,
                "config": config4.__dict__,
                "decision": "neighbourhood_only",
                "passed_train": True,
                "neighbourhood_entries": len(neighbourhood_table),
            }

    return None, "none", {
        "sentence": sentence.__dict__,
        "decision": "no_train_pass",
        "passed_train": False,
        "neighbourhood_entries": len(neighbourhood_table) if neighbourhood_table else 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Geometric Language self-test")
    print("=" * 60)

    # Test 1: read a sentence from a simple recolour task
    print("\n[Test 1] Read sentence from a recolour task")
    from arc_loader import TrainPair, TestInput
    inp = Grid([[1, 2, 0], [1, 2, 0], [1, 2, 0]])
    out = Grid([[2, 3, 0], [2, 3, 0], [2, 3, 0]])
    test = Grid([[1, 2, 0], [1, 2, 0]])
    task = ARCTask(name="recolour",
                   train=[TrainPair(input=inp, output=out)],
                   test=[TestInput(input=test, expected_output=Grid([[2, 3, 0], [2, 3, 0]]))])
    sentence = read_sentence(task)
    print(f"  {sentence.summary()}")
    pred, src, diag = predict_with_free_arm(task)
    print(f"  Source: {src}")
    print(f"  Predicted: {pred.cells if pred else None}")
    print(f"  Correct: {pred == task.test[0].expected_output if pred else False}")

    # Test 2: identity
    print("\n[Test 2] Identity transformation")
    inp2 = Grid([[1, 2], [3, 4]])
    out2 = Grid([[1, 2], [3, 4]])
    test2 = Grid([[5, 6], [7, 8]])
    task2 = ARCTask(name="identity",
                    train=[TrainPair(input=inp2, output=out2)],
                    test=[TestInput(input=test2, expected_output=test2)])
    sentence2 = read_sentence(task2)
    print(f"  rotation={sentence2.rotation}, mode={hex(sentence2.direction_mode)}, conf={sentence2.direction_confidence:.2f}")
    pred2, src2, _ = predict_with_free_arm(task2)
    print(f"  Source: {src2}, correct: {pred2 == test2 if pred2 else False}")

    # Test 3: rotation (90 degrees)
    print("\n[Test 3] Rotation 90°")
    inp3 = Grid([[1, 0], [0, 0]])
    out3 = Grid([[0, 1], [0, 0]])  # 90° rotation
    test3 = Grid([[2, 0], [0, 0]])
    expected3 = Grid([[0, 2], [0, 0]])
    task3 = ARCTask(name="rot90",
                    train=[TrainPair(input=inp3, output=out3)],
                    test=[TestInput(input=test3, expected_output=expected3)])
    sentence3 = read_sentence(task3)
    print(f"  rotation={sentence3.rotation}")
    pred3, src3, _ = predict_with_free_arm(task3)
    print(f"  Source: {src3}")
    print(f"  Predicted: {pred3.cells if pred3 else None}")
    print(f"  Expected:  {expected3.cells}")
    print(f"  Correct: {pred3 == expected3 if pred3 else False}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
