#!/usr/bin/env python3
"""
================================================================================
TGIC_v3.py — Golay filter plus optional 3-6-9 RuneCube simulator
================================================================================
This module has two deliberately separate layers:

1. A top-down Golay-code filter.  Codewords, syndromes, octads and correction
   all use ``ubp_unified_v5.GolayCodeEngine`` so there is one code convention.
2. A bottom-up, finite-state RuneCube simulator adapted from
   ``ubp_tgic_engine.py``.  It provides the older axis operations, internal
   interaction score, neighbourhood pressure and relational attraction without
   relying on the unavailable ``ubp_core_v5_3_merged`` module.

The Golay counts and round trips are exact finite computations.  The MOG search,
"Leech tax", Hodge terminology, energy, resonance and gravity are computational
models/analogs, not proofs of physical laws or complete constructions of the
Leech lattice or Hodge theory.  In particular, relational pull below is a
clearly stated inverse-distance scoring rule.

- 3 axes: a 24-bit state is divided into 8-bit X, Y, and Z blocks. The axis
  score is maximal when each pair has Hamming distance 4.
- 6 directed faces: three symmetric Boolean face transforms are counted in
  both directions: XY uses AND, XZ uses XOR, and YZ uses OR. Optionally, a result
  is corrected to a Golay codeword when the decoder certifies that it is within
  its correction radius.
- 9-neighbour limit: after nine other nodes within Hamming distance 8,
  each additional neighbour contributes a pressure penalty. The target no
  longer accidentally counts itself.

Relational pull uses both the integer-grid separation and state similarity.

A step deterministically proposes one bit flip using a digest of the complete
state and compares the old and candidate ,whole-system energies. The caller's
input dictionary and immutable nodes are not mutated.

The Golay code enumeration and weight counts are exact finite computations. The
GF(4)/MOG permutation search is only a deterministic bounded heuristic; its
“Hodge” and “holomorphic balance” labels are analogies, not a Hodge-theory
proof.

The checks cover the Golay count and weight distribution, encoding round trip,
3-axis score, face transforms, all eight possible local XYZ triples, spatial
and Hamming behaviour of relational pull, the 9-neighbour boundary,
deterministic transitions, empty states, and malformed-vector rejection.

The local interaction cost preserves the older nine terms at each of eight bit
positions. All score and energy arithmetic uses `fractions.Fraction`.

Dependencies: Python 3.8+ standard library and local ``ubp_unified_v5.py``.
================================================================================
"""

from __future__ import annotations
import sys
import os
import hashlib
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import List, Tuple, Dict, Optional, FrozenSet, Any, Union
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ubp_unified_v5 import (
    GolayCodeEngine,
    LeechLatticeEngine,
    UBPSourceCodeParticlePhysics,
)

# ═════════════════════════════════════════════════════════════════════════════
# §0. ALIGNED CODE ENGINE — uses the REAL GolayCodeEngine
# ═════════════════════════════════════════════════════════════════════════════

# Singleton engine (initialized once)
_G: Optional[GolayCodeEngine] = None
_L: Optional[LeechLatticeEngine] = None
_PP: Optional[UBPSourceCodeParticlePhysics] = None

def get_golay_engine() -> GolayCodeEngine:
    global _G
    if _G is None:
        _G = GolayCodeEngine()
    return _G

def get_leech_engine() -> LeechLatticeEngine:
    global _L
    if _L is None:
        _L = LeechLatticeEngine(get_golay_engine())
    return _L

def get_pp() -> UBPSourceCodeParticlePhysics:
    global _PP
    if _PP is None:
        _PP = UBPSourceCodeParticlePhysics()
    return _PP


# ═════════════════════════════════════════════════════════════════════════════
# §1. CODEWORD ACCESS — all from the real engine
# ═════════════════════════════════════════════════════════════════════════════

def get_all_codewords() -> List[List[int]]:
    """Get all 4096 Golay codewords from the real engine."""
    return get_golay_engine().get_all_codewords()

def get_octads() -> List[List[int]]:
    """Get all 759 weight-8 codewords (octads)."""
    return [cw for cw in get_all_codewords() if sum(cw) == 8]

def get_dodecads() -> List[List[int]]:
    """Get all 2576 weight-12 codewords (dodecads)."""
    return [cw for cw in get_all_codewords() if sum(cw) == 12]

def is_codeword(vec: List[int]) -> bool:
    """Check whether a strictly validated 24-bit vector is a Golay codeword."""
    v = _validate_vector24(vec)
    return sum(get_golay_engine().syndrome(v)) == 0

def syndrome_weight(vec: List[int]) -> int:
    """Compute syndrome weight for a strictly validated 24-bit vector."""
    return sum(get_golay_engine().syndrome(_validate_vector24(vec)))


# ═════════════════════════════════════════════════════════════════════════════
# §2. GF(4) HEXACODE PROJECTION — preserved from tgic_v2.py
# ═════════════════════════════════════════════════════════════════════════════

# MOG permutation key (auto-hunted from tgic_v2.py)
_MOG_KEY: Optional[List[int]] = None

def auto_hunt_mog_key(codewords: List[List[int]]) -> List[int]:
    """
    Find a deterministic low-NOISE permutation candidate.

    This is a bounded heuristic over 100 permutations and a 100-word sample;
    it must not be interpreted as a proof of a canonical MOG alignment.
    """
    global _MOG_KEY
    # Use the first 100 codewords for speed
    sample = codewords[:100]
    best_key = list(range(24))
    best_noise = float('inf')

    # Try deterministic pseudo-random permutations so repeated studies agree.
    rng = random.Random(0x54474943)
    for _ in range(100):
        key = list(range(24))
        rng.shuffle(key)
        noise_count = 0
        for cw in sample:
            permuted = [cw[key[i]] for i in range(24)]
            cols = [[permuted[i], permuted[i+6], permuted[i+12], permuted[i+18]] for i in range(6)]
            for col in cols:
                wt = sum(col)
                if wt not in (0, 2, 4):
                    noise_count += 1
        if noise_count < best_noise:
            best_noise = noise_count
            best_key = key[:]

    _MOG_KEY = best_key
    return best_key

def get_mog_key() -> List[int]:
    """Get the current MOG permutation key."""
    global _MOG_KEY
    if _MOG_KEY is None:
        auto_hunt_mog_key(get_all_codewords())
    return _MOG_KEY

def apply_mog_permutation(vec: List[int]) -> List[int]:
    """Apply the candidate MOG permutation to a validated 24-bit vector."""
    v = _validate_vector24(vec)
    key = get_mog_key()
    return [v[key[i]] for i in range(24)]


# GF(4) elements and operations
_GF4_ADD = {
    ("0","0"):"0", ("0","1"):"1", ("0","W"):"W", ("0","W_BAR"):"W_BAR",
    ("1","0"):"1", ("1","1"):"0", ("1","W"):"W_BAR", ("1","W_BAR"):"W",
    ("W","0"):"W", ("W","1"):"W_BAR", ("W","W"):"0", ("W","W_BAR"):"1",
    ("W_BAR","0"):"W_BAR", ("W_BAR","1"):"W", ("W_BAR","W"):"1", ("W_BAR","W_BAR"):"0",
}

def _gf4_add(a: str, b: str) -> str:
    return _GF4_ADD.get((a, b), "NOISE")

def _gf4_eq(a: str, b: str) -> bool:
    return a == b


# Weight-2 patterns for GF(4) projection
_WEIGHT2_PATTERNS = [
    (1,1,0,0), (1,0,1,0), (1,0,0,1),
    (0,1,1,0), (0,1,0,1), (0,0,1,1),
]

def project_to_hexacode(vec: List[int],
                         w_set: Optional[FrozenSet] = None,
                         wb_set: Optional[FrozenSet] = None) -> List[str]:
    """
    Project a 24-bit vector to a 6-element GF(4) hexacode word.
    Uses the MOG permutation and weight-2 pattern classification.
    """
    if w_set is None or wb_set is None:
        # Default assignment (first 3 patterns = W, last 3 = W_BAR)
        w_set = frozenset(_WEIGHT2_PATTERNS[:3])
        wb_set = frozenset(_WEIGHT2_PATTERNS[3:])

    v = apply_mog_permutation(vec)
    cols = [[v[i], v[i+6], v[i+12], v[i+18]] for i in range(6)]
    parities = [sum(c) % 2 for c in cols]

    # Top-row flip for odd-parity columns
    if all(p == 1 for p in parities):
        for i in range(6):
            cols[i][0] ^= 1

    word = []
    for c in cols:
        wt = sum(c)
        if wt == 0:
            word.append("0")
        elif wt == 4:
            word.append("1")
        elif tuple(c) in w_set:
            word.append("W")
        elif tuple(c) in wb_set:
            word.append("W_BAR")
        else:
            word.append("NOISE")
    return word


def holomorphic_balance(hex_word: List[str]) -> Dict[str, Any]:
    """
    Compute the holomorphic balance of a hexacode word.
    Balance = |count(W) - count(W_BAR)| / count(W + W_BAR)
    """
    w_count = hex_word.count("W")
    wb_count = hex_word.count("W_BAR")
    total = w_count + wb_count
    noise = hex_word.count("NOISE")

    if total == 0:
        balance = 0.0
    else:
        balance = abs(w_count - wb_count) / total

    return {
        "W": w_count, "W_BAR": wb_count, "NOISE": noise,
        "balance": balance, "total_nonzero": total,
    }


# ═════════════════════════════════════════════════════════════════════════════
# §3. BOOLEAN OPERATIONS — intersection, union, symmetric difference
# ═════════════════════════════════════════════════════════════════════════════

def _validate_binary_pair(a: List[int], b: List[int]) -> None:
    """Reject the length truncation that bare ``zip`` would otherwise hide."""
    if len(a) != len(b):
        raise ValueError("binary vectors must have equal lengths")
    if any(type(bit) is not int or bit not in (0, 1) for bit in a + b):
        raise ValueError("binary vectors may contain only integer bits 0 or 1")


def bitwise_and(a: List[int], b: List[int]) -> List[int]:
    """AND (intersection) of two equal-length binary vectors."""
    _validate_binary_pair(a, b)
    return [x & y for x, y in zip(a, b)]

def bitwise_or(a: List[int], b: List[int]) -> List[int]:
    """OR (union) of two equal-length binary vectors."""
    _validate_binary_pair(a, b)
    return [x | y for x, y in zip(a, b)]

def xor(a: List[int], b: List[int]) -> List[int]:
    """XOR (symmetric difference) of two equal-length binary vectors."""
    _validate_binary_pair(a, b)
    return [x ^ y for x, y in zip(a, b)]

def hamming_distance(a: List[int], b: List[int]) -> int:
    """Hamming distance between two equal-length binary vectors."""
    _validate_binary_pair(a, b)
    return sum(x ^ y for x, y in zip(a, b))


# ═════════════════════════════════════════════════════════════════════════════
# §4. TGIC EVOLUTION PRIMITIVES — preserved from tgic_v2.py
# ═════════════════════════════════════════════════════════════════════════════

class HomologyJumpOperator:
    """
    Octad XOR transition (historically called a "homology jump").

    Since an octad is itself a Golay codeword, XOR preserves the linear code;
    this changes codewords, not Golay cosets.
    """
    def __init__(self, octads: Optional[List[List[int]]] = None):
        self.octads = octads or get_octads()

    def jump(self, vec: List[int], octad_idx: Optional[int] = None) -> List[int]:
        """XOR with one octad; a Golay input therefore remains in the code."""
        _validate_vector24(vec)
        if not self.octads:
            raise ValueError("at least one octad is required")
        if octad_idx is None:
            octad_idx = random.randint(0, len(self.octads) - 1)
        if type(octad_idx) is not int or not 0 <= octad_idx < len(self.octads):
            raise IndexError("octad index out of range")
        return xor(vec, self.octads[octad_idx])


class InformationFunctional:
    """
    Lead 2: Lyapunov Energy Functional.
    Measures the "energy" of a state — lower is more stable.
    """
    def __init__(self, leech: Optional[LeechLatticeEngine] = None):
        self.leech = leech or get_leech_engine()

    def energy(self, vec: List[int]) -> float:
        """Compute the energy of a vector."""
        try:
            tax = float(self.leech.calculate_symmetry_tax(vec))
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            tax = sum(vec) * 0.2647 + sum(x*x for x in vec) / 8.0
        return tax

    def nrci(self, vec: List[int]) -> float:
        """Compute NRCI of a vector."""
        try:
            return float(self.leech.calculate_nrci(vec))
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            return 0.0


class CanonicalEvolution:
    """
    Lead 6: Canonical Evolution.
    Evolves a state toward a codeword by iteratively snapping to the nearest codeword.
    """
    def __init__(self, engine: Optional[GolayCodeEngine] = None):
        self.engine = engine or get_golay_engine()

    def evolve(self, vec: List[int], max_ticks: int = 10) -> Tuple[List[int], int]:
        """
        Evolve a vector toward a codeword.
        Returns (final_vector, ticks_to_convergence).
        """
        current = list(vec)
        for tick in range(max_ticks):
            if is_codeword(current):
                return current, tick
            # Snap to nearest codeword
            snapped, _ = self.engine.snap_to_codeword(current)
            if list(snapped) == current:
                return current, tick
            current = list(snapped)
        return current, max_ticks


# ═════════════════════════════════════════════════════════════════════════════
# §5. 3-6-9 RUNECUBE MODEL — reviewed integration of ubp_tgic_engine.py
# ═════════════════════════════════════════════════════════════════════════════

Vector24 = Tuple[int, ...]
Coordinate3 = Tuple[int, int, int]


def _validate_vector24(vec: Union[List[int], Tuple[int, ...]]) -> List[int]:
    """Return a defensive list copy after strict 24-bit validation."""
    if len(vec) != 24:
        raise ValueError("a RuneCube state must contain exactly 24 bits")
    if any(type(bit) is not int or bit not in (0, 1) for bit in vec):
        raise ValueError("a RuneCube state may contain only integer bits 0 or 1")
    return list(vec)


@dataclass(frozen=True)
class RuneNode:
    """One immutable simulator node: a 24-bit RuneCube state and byte phase."""

    bits: Vector24
    phase: int = 0

    def __post_init__(self) -> None:
        _validate_vector24(self.bits)
        if type(self.phase) is not int or not 0 <= self.phase < 256:
            raise ValueError("phase must be an integer in [0, 255]")

    def updated(self, bits: Optional[List[int]] = None, phase_delta: int = 0) -> "RuneNode":
        new_bits = self.bits if bits is None else tuple(_validate_vector24(bits))
        return RuneNode(new_bits, (self.phase + phase_delta) % 256)


class RuneCube369:
    """Exact-rational implementation of the older engine's 3-6-9 rules.

    ``3`` — split the 24 bits into X/Y/Z blocks and reward pairwise Hamming
    distance four (a balanced relation, called "orthogonality" historically).

    ``6`` — audit the six directed axis faces.  Each unordered face transform
    (XY=AND, XZ=XOR, YZ=OR) is counted in both directions, and the resulting
    vectors are scored by the reduced Leech symmetry-tax model already used by
    :mod:`ubp_unified_v5`.

    ``9`` — allow at most nine *other* nodes within Hamming distance eight;
    each excess neighbour adds exact-rational pressure.

    These are explicit simulation rules.  The labels do not make them physical
    laws, Euclidean orthogonality, or a full Leech-lattice construction.
    """

    def __init__(self, snap_faces: bool = True) -> None:
        self.y = get_leech_engine().Y
        self.interaction_weight = Fraction(5)
        self.snap_faces = snap_faces

    @staticmethod
    def _axes(vec: List[int]) -> Tuple[List[int], List[int], List[int]]:
        v = _validate_vector24(vec)
        return v[:8], v[8:16], v[16:]

    def _snap(self, vec: List[int]) -> List[int]:
        if not self.snap_faces:
            return vec
        snapped, metadata = get_golay_engine().snap_to_codeword(vec)
        # The Golay decoder guarantees correction only through distance three.
        # Do not pretend an uncorrectable vector was snapped.
        return snapped if metadata["correctable"] else vec

    def face_xy(self, vec: List[int]) -> List[int]:
        """XY resonance: replace X and Y by their bitwise AND."""
        x, y, z = self._axes(vec)
        xy = [a & b for a, b in zip(x, y)]
        return self._snap(xy + xy + z)

    def face_xz(self, vec: List[int]) -> List[int]:
        """XZ entanglement: replace Z by X XOR Z."""
        x, y, z = self._axes(vec)
        return self._snap(x + y + [a ^ b for a, b in zip(x, z)])

    def face_yz(self, vec: List[int]) -> List[int]:
        """YZ expansion: replace Y by Y OR Z."""
        x, y, z = self._axes(vec)
        return self._snap(x + [a | b for a, b in zip(y, z)] + z)

    def axis_score(self, vec: List[int]) -> Fraction:
        """The ``3`` score; one exactly when all three axis distances are four."""
        x, y, z = self._axes(vec)
        deviation = sum(
            abs(4 - hamming_distance(a, b)) for a, b in ((x, y), (x, z), (y, z))
        )
        return Fraction(1, 1) / (1 + deviation * self.y)

    def face_score(self, vec: List[int]) -> Fraction:
        """The ``6`` score from six directed faces (three symmetric pairs)."""
        transformed = (self.face_xy(vec), self.face_xz(vec), self.face_yz(vec))
        # Each result occurs twice because these Boolean face operations are
        # symmetric in the two named axes.  Writing six explicitly documents
        # what the historical "6-face" label counts.
        six_taxes = [get_leech_engine().calculate_symmetry_tax(v)
                     for v in transformed for _direction in range(2)]
        mean_tax = sum(six_taxes, Fraction(0)) / 6
        return Fraction(10) / (10 + mean_tax)

    def neighbour_pressure(
        self, coordinate: Coordinate3, vec: List[int], state: Dict[Coordinate3, RuneNode]
    ) -> Fraction:
        """The ``9`` penalty, excluding the target node itself."""
        v = _validate_vector24(vec)
        neighbours = sum(
            1 for other_coordinate, node in state.items()
            if other_coordinate != coordinate and hamming_distance(v, list(node.bits)) <= 8
        )
        return max(0, neighbours - 9) * self.y

    def stability(
        self, coordinate: Coordinate3, vec: List[int], state: Dict[Coordinate3, RuneNode]
    ) -> Fraction:
        """Mean axis/face/base score, less the nine-neighbour pressure."""
        v = _validate_vector24(vec)
        base = get_leech_engine().calculate_nrci(v)
        return (self.axis_score(v) + self.face_score(v) + base) / 3 - \
            self.neighbour_pressure(coordinate, v, state)

    def internal_cost(self, vec: List[int]) -> Fraction:
        """The nine historical local terms, evaluated at each of 8 bit positions."""
        x_axis, y_axis, z_axis = self._axes(vec)
        total = Fraction(0)
        for x, y, z in zip(x_axis, y_axis, z_axis):
            resonance_xy = Fraction(0) if x == y else self.y / 20
            resonance_yx = Fraction(0) if y == x else self.y / 20
            entangle_xz = Fraction(-1, 200) if x == z == 1 else Fraction(0)
            entangle_zx = Fraction(-1, 200) if z == x == 1 else Fraction(0)
            super_yz = (Fraction(y) + Fraction(z) + Fraction(y ^ z)) / 3
            super_zy = (Fraction(z) + Fraction(y) + Fraction(z ^ y)) / 3
            mixed_xyz = Fraction(min(x, y) * z)
            # These two expressions preserve the *actual positional behaviour*
            # of the older mixed_op(y,z,x,"yzx") and mixed_op(z,x,y,"zxy")
            # calls.  Naming the original X/Y/Z values explicitly removes the
            # confusing argument rotation in the legacy implementation.
            mixed_yzx = Fraction(abs(z - x) * y)
            mixed_zxy = Fraction(max(y, z) * x)
            total += (resonance_xy + resonance_yx + entangle_xz + entangle_zx +
                      super_yz + super_zy + mixed_xyz + mixed_yzx + mixed_zxy)
        return total * self.interaction_weight


class TGICSimulator:
    """Deterministic multi-node simulator built from :class:`RuneCube369`.

    Relational pull combines actual integer-grid separation with 24-bit state
    similarity.  For another node it contributes

    ``(24 - HammingDistance) / (24 * (1 + squaredSpatialDistance)) * Y/2``.

    Thus pull is bounded, decreases with spatial separation, is strongest for
    identical states, and is zero for complementary states.  This is a model
    definition rather than Newtonian gravity.  ``step`` chooses a node and bit
    from a SHA-256 state digest, so
    identical input states produce identical transitions.
    """

    def __init__(self, snap_faces: bool = True) -> None:
        self.rules = RuneCube369(snap_faces=snap_faces)

    @staticmethod
    def validate_state(state: Dict[Coordinate3, RuneNode]) -> None:
        if not isinstance(state, dict):
            raise TypeError("state must be a coordinate-to-RuneNode dictionary")
        for coordinate, node in state.items():
            if (not isinstance(coordinate, tuple) or len(coordinate) != 3 or
                    any(type(c) is not int for c in coordinate)):
                raise ValueError("coordinates must be triples of integers")
            if not isinstance(node, RuneNode):
                raise TypeError("every state value must be a RuneNode")

    def relational_pull(
        self, coordinate: Coordinate3, vec: List[int], state: Dict[Coordinate3, RuneNode]
    ) -> Fraction:
        self.validate_state(state)
        v = _validate_vector24(vec)
        pull = Fraction(0)
        for other_coordinate, node in state.items():
            if other_coordinate == coordinate:
                continue
            spatial_sq = sum((a - b) ** 2 for a, b in zip(coordinate, other_coordinate))
            bit_distance = hamming_distance(v, list(node.bits))
            pull += Fraction(24 - bit_distance, 24 * (1 + spatial_sq))
        return pull * self.rules.y / 2

    def node_energy(
        self, coordinate: Coordinate3, vec: List[int], state: Dict[Coordinate3, RuneNode]
    ) -> Fraction:
        stability = self.rules.stability(coordinate, vec, state)
        structural = (1 - stability) * 10
        return self.rules.internal_cost(vec) + structural - \
            self.relational_pull(coordinate, vec, state)

    def total_energy(self, state: Dict[Coordinate3, RuneNode]) -> Fraction:
        self.validate_state(state)
        return sum((self.node_energy(c, list(n.bits), state) for c, n in state.items()),
                   Fraction(0))

    def step(self, state: Dict[Coordinate3, RuneNode]) -> Tuple[Dict[Coordinate3, RuneNode], Dict[str, Any]]:
        """Propose one deterministic bit flip and accept within the legacy Y/4 tolerance."""
        self.validate_state(state)
        if not state:
            return {}, {"status": "empty"}
        ordered = sorted((coord, node.bits, node.phase) for coord, node in state.items())
        digest = hashlib.sha256(repr(ordered).encode("utf-8")).digest()
        coordinates = sorted(state)
        coordinate = coordinates[digest[0] % len(coordinates)]
        old_node = state[coordinate]
        flip_index = digest[1] % 24
        proposed_bits = list(old_node.bits)
        proposed_bits[flip_index] ^= 1
        # Compare whole-system energy.  A changed node alters every other
        # node's relational term, which the older local-only comparison missed.
        old_energy = self.total_energy(state)
        candidate = dict(state)
        candidate[coordinate] = old_node.updated(proposed_bits, phase_delta=1)
        new_energy = self.total_energy(candidate)
        delta = new_energy - old_energy
        if delta < self.rules.y / 4:
            return candidate, {"status": "accepted", "coordinate": coordinate,
                               "flip_index": flip_index, "delta": delta}
        return dict(state), {"status": "rejected", "coordinate": coordinate,
                             "flip_index": flip_index, "delta": delta}


def analyze_cycle(vec: List[int]) -> Dict[str, Any]:
    """Top-down single-state filter, kept independent from multi-node dynamics."""
    v = _validate_vector24(vec)
    hex_word = project_to_hexacode(v)
    snapped, correction = get_golay_engine().snap_to_codeword(v)
    return {
        "is_golay_codeword": is_codeword(v),
        "syndrome_weight": syndrome_weight(v),
        "golay_weight": sum(v),
        "hexacode_projection": hex_word,
        "holomorphic_balance_analog": holomorphic_balance(hex_word),
        "nearest_correctable_codeword": snapped if correction["correctable"] else None,
        "correction": correction,
    }


# ═════════════════════════════════════════════════════════════════════════════
# §6. VERIFICATION — executable finite checks
# ═════════════════════════════════════════════════════════════════════════════

def verify_alignment() -> Dict[str, Any]:
    """
    Verify that TGIC_v3 is properly aligned with ubp_unified_v5.py.
    """
    engine = get_golay_engine()
    codewords = get_all_codewords()

    # Test 1: All codewords have syndrome weight 0
    all_zero_syn = all(syndrome_weight(cw) == 0 for cw in codewords)

    # Test 2: Codeword count
    cw_count = len(codewords)

    # Test 3: Octad count
    octads = get_octads()
    octad_count = len(octads)

    # Test 4: Weight distribution
    wt_dist = defaultdict(int)
    for cw in codewords:
        wt_dist[sum(cw)] += 1

    # Test 5: Encode/decode roundtrip
    msg = [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    encoded = engine.encode(msg)
    decoded, _, n_err = engine.decode(encoded)
    roundtrip_ok = (decoded == msg)

    return {
        "all_zero_syndrome": all_zero_syn,
        "codeword_count": cw_count,
        "octad_count": octad_count,
        "weight_distribution": dict(sorted(wt_dist.items())),
        "encode_decode_roundtrip": roundtrip_ok,
        "alignment_status": "ALIGNED" if all_zero_syn and cw_count == 4096 else "MISALIGNED",
    }


def run_self_tests() -> Dict[str, bool]:
    """Run deterministic regression checks for both the filter and simulator."""
    alignment = verify_alignment()
    assert alignment["alignment_status"] == "ALIGNED"
    assert alignment["octad_count"] == 759
    assert alignment["weight_distribution"] == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}
    assert alignment["encode_decode_roundtrip"]

    rules = RuneCube369(snap_faces=False)
    balanced = [0, 0, 0, 0, 0, 0, 0, 0] + \
               [1, 1, 1, 1, 0, 0, 0, 0] + \
               [1, 1, 0, 0, 1, 1, 0, 0]
    assert rules.axis_score(balanced) == 1
    assert rules.face_xy(balanced) == bitwise_and(balanced[:8], balanced[8:16]) * 2 + balanced[16:]
    assert len(rules.face_xz(balanced)) == len(rules.face_yz(balanced)) == 24

    # Exhaust all eight local XYZ triples.  This reference spells out the
    # legacy call order and protects the non-obvious rotated mixed terms.
    for x in (0, 1):
        for y in (0, 1):
            for z in (0, 1):
                repeated = [x] * 8 + [y] * 8 + [z] * 8
                resonance = (Fraction(0) if x == y else rules.y / 20) * 2
                entangle = (Fraction(-1, 200) if x == z == 1 else Fraction(0)) * 2
                superposition = (Fraction(y) + Fraction(z) + Fraction(y ^ z)) * 2 / 3
                legacy_mixed = (Fraction(min(x, y) * z) +
                                Fraction(abs(z - x) * y) + Fraction(max(y, z) * x))
                expected = (resonance + entangle + superposition + legacy_mixed) * 8 * 5
                assert rules.internal_cost(repeated) == expected

    zero = RuneNode(tuple([0] * 24))
    one = RuneNode(tuple([1] * 24))
    close_state = {(0, 0, 0): zero, (1, 0, 0): zero}
    far_state = {(0, 0, 0): zero, (10, 0, 0): zero}
    simulator = TGICSimulator(snap_faces=False)
    assert simulator.relational_pull((0, 0, 0), list(zero.bits), close_state) > \
           simulator.relational_pull((0, 0, 0), list(zero.bits), far_state) > 0
    dissimilar_state = {(0, 0, 0): zero, (1, 0, 0): one}
    assert simulator.relational_pull((0, 0, 0), list(zero.bits), dissimilar_state) == 0

    ten_neighbours = {(0, 0, 0): zero}
    for index in range(1, 11):
        ten_neighbours[(index, 0, 0)] = zero
    assert rules.neighbour_pressure((0, 0, 0), list(zero.bits), ten_neighbours) == rules.y

    first_state, first_meta = simulator.step(close_state)
    second_state, second_meta = simulator.step(close_state)
    assert first_state == second_state and first_meta == second_meta
    assert simulator.step({}) == ({}, {"status": "empty"})

    invalid_rejected = False
    try:
        RuneNode(tuple([0] * 23))
    except ValueError:
        invalid_rejected = True
    assert invalid_rejected
    return {"golay_filter": True, "three_six_nine": True,
            "relational_simulator": True, "validation": True}


# ═════════════════════════════════════════════════════════════════════════════
# SELF-TEST / EXAMPLE
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 72)
    print("TGIC_v3 — Golay Filter + 3-6-9 RuneCube Simulator")
    print("=" * 72)

    # Verify alignment
    status = verify_alignment()
    print(f"\n  Alignment status: {status['alignment_status']}")
    print(f"  All zero syndrome: {status['all_zero_syndrome']}")
    print(f"  Codeword count: {status['codeword_count']}")
    print(f"  Octad count: {status['octad_count']}")
    print(f"  Weight dist: {status['weight_distribution']}")
    print(f"  Encode/decode roundtrip: {status['encode_decode_roundtrip']}")

    # Test intersection closure
    codewords = get_all_codewords()
    octads = get_octads()
    cw_set = {tuple(cw) for cw in codewords}

    and_pass = 0
    and_total = 0
    sample = random.Random(0x54474943).sample(octads, min(50, len(octads)))
    for i, a in enumerate(sample):
        for j, b in enumerate(sample):
            if j <= i:
                continue
            intersection = bitwise_and(a, b)
            and_total += 1
            if tuple(intersection) in cw_set:
                and_pass += 1

    print(f"\n  AND closure (octads): {and_pass}/{and_total} = {and_pass/max(and_total,1):.4f}")

    # Test hexacode projection
    cw = codewords[0]
    hex_word = project_to_hexacode(cw)
    balance = holomorphic_balance(hex_word)
    print(f"\n  Hexacode projection of first codeword: {hex_word}")
    print(f"  Balance: {balance}")

    tests = run_self_tests()
    simulator = TGICSimulator()
    example_state = {
        (0, 0, 0): RuneNode(tuple(codewords[1])),
        (1, 0, 0): RuneNode(tuple(codewords[2])),
    }
    next_state, transition = simulator.step(example_state)
    print(f"\n  Integrated checks: {tests}")
    example_energy = simulator.total_energy(example_state)
    print(f"  Example total energy: {float(example_energy):.8f} (stored as Fraction)")
    print(f"  Example deterministic transition: {transition['status']}")
    print("\n  TGIC_v3 ready for top-down filtering and optional node simulation.")
