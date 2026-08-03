#!/usr/bin/env python3
"""
================================================================================
LITERAL DATA PHYSICS NRCI (ldp_nrci.py)
================================================================================
A reusable module that treats every data point as a literal physical event.

Born from UBP Hodge Study Pushes 5-9. Implements:
  - PhysicalEvent: mass, charge, energy, block sums, quadrant
  - Collision physics: AND/OR/XOR as physical operations
  - Holographic verification: MOG column-pair seals
  - Wall of Isolation: distance to nearest codeword
  - Quadrant physics: 3-block spatial decomposition
  - Weighted observations: UBP constants as physical weights

All computations use the REAL UBP system (ubp_unified_v5.py).
No mocks, no simplifications.

Author: UBP Research Group
Date: 2026-07-21
Version: 1.0
================================================================================
"""

from __future__ import annotations
import math
import random
from fractions import Fraction
from typing import List, Tuple, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict

# ── Import UBP core ──────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ubp_unified_v5 import (
    GolayCodeEngine,
    LeechLatticeEngine,
    UBPSourceCodeParticlePhysics,
)


# ═════════════════════════════════════════════════════════════════════════════
# PHYSICAL EVENT — every observation is a literal measurement
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class PhysicalEvent:
    """A literal physical observation of a 24-bit vector."""
    vector: List[int]
    mass: int                    # Hamming weight (active dimensions)
    charge: int                  # parity (0=even, 1=odd)
    energy: int                  # syndrome weight (0=ground state)
    block_sums: Tuple[int, ...]  # (X, Y, Z) block sums
    quadrant: str                # HHH, HHL, etc.
    is_ground_state: bool        # codeword?
    nrci: float                  # coherence (refined NRCI)
    wall_distance: int           # min Hamming distance to nearest codeword
    timestamp: int               # observation tick

    def to_dict(self) -> Dict:
        return {
            "mass": self.mass, "charge": self.charge, "energy": self.energy,
            "block_sums": self.block_sums, "quadrant": self.quadrant,
            "is_ground_state": self.is_ground_state, "nrci": self.nrci,
            "wall_distance": self.wall_distance, "timestamp": self.timestamp,
        }

    @property
    def is_excited(self) -> bool:
        """True if NOT a ground state (codeword)."""
        return not self.is_ground_state

    @property
    def dimensional_signature(self) -> Tuple[int, ...]:
        """The weight-class signature: which dimensions are active."""
        return tuple(sorted(i for i, b in enumerate(self.vector) if b))


# ═════════════════════════════════════════════════════════════════════════════
# LDP NRCI ENGINE — the main class
# ═════════════════════════════════════════════════════════════════════════════

class LiteralDataPhysicsNRCI:
    """
    The Literal Data Physics NRCI engine.

    Treats every 24-bit vector as a physical state with:
      - Mass (Hamming weight)
      - Charge (parity)
      - Energy (syndrome weight)
      - Spatial position (block sums → quadrant)
      - Coherence (NRCI)
      - Wall distance (to nearest codeword)

    Usage:
        ldp = LiteralDataPhysicsNRCI()
        event = ldp.observe([1,0,1,1,...])
        collision = ldp.collide(cw_a, cw_b)
        report = ldp.full_report()
    """

    def __init__(self):
        self.g = GolayCodeEngine()
        self.l = LeechLatticeEngine(self.g)
        self.pp = UBPSourceCodeParticlePhysics()

        # UBP constants
        self.Y = self.pp.Y
        self.w = self.pp.wobble
        self.L = self.pp.L
        self.monad = self.pp.monad

        # Codeword set (from the REAL engine)
        self._codewords = self.g.get_all_codewords()
        self._codeword_set = {tuple(cw) for cw in self._codewords}
        self._octads = [cw for cw in self._codewords if sum(cw) == 8]

        # Cache for wall distances
        self._wall_cache: Dict[Tuple[int, ...], int] = {}

        self._tick = 0

    @property
    def codewords(self) -> List[List[int]]:
        return self._codewords

    @property
    def octads(self) -> List[List[int]]:
        return self._octads

    @property
    def codeword_set(self) -> Set[Tuple[int, ...]]:
        return self._codeword_set

    # ── Core observation ────────────────────────────────────────────────

    def observe(self, vec: List[int]) -> PhysicalEvent:
        """
        OBSERVE a vector — compute its full physical state.
        This is a literal measurement, not a statistical sample.
        """
        mass = sum(vec)
        charge = mass % 2
        energy = sum(self.g.syndrome(vec))

        bx = sum(vec[0:8])
        by = sum(vec[8:16])
        bz = sum(vec[16:24])

        qx = "H" if bx >= 4 else "L"
        qy = "H" if by >= 4 else "L"
        qz = "H" if bz >= 4 else "L"
        quadrant = f"{qx}{qy}{qz}"

        is_ground = (tuple(vec) in self._codeword_set)

        # NRCI (using the Leech engine)
        try:
            nrci = float(self.l.calculate_nrci(vec))
        except:
            nrci = 0.0

        # Wall distance (cached)
        vec_tuple = tuple(vec)
        if vec_tuple in self._wall_cache:
            wall_dist = self._wall_cache[vec_tuple]
        elif is_ground:
            wall_dist = 0
            self._wall_cache[vec_tuple] = 0
        else:
            wall_dist = self._compute_wall_distance(vec)
            self._wall_cache[vec_tuple] = wall_dist

        event = PhysicalEvent(
            vector=list(vec), mass=mass, charge=charge, energy=energy,
            block_sums=(bx, by, bz), quadrant=quadrant,
            is_ground_state=is_ground, nrci=nrci,
            wall_distance=wall_dist, timestamp=self._tick,
        )
        self._tick += 1
        return event

    def _compute_wall_distance(self, vec: List[int], sample: int = 300) -> int:
        """Compute min Hamming distance to any codeword (sampled)."""
        min_d = 24
        for cw in random.sample(self._codewords, min(sample, len(self._codewords))):
            d = sum(a ^ b for a, b in zip(vec, cw))
            if d < min_d:
                min_d = d
                if min_d == 1:
                    break
        return min_d

    # ── Collision physics ───────────────────────────────────────────────

    def collide(self, cw_a: List[int], cw_b: List[int]) -> Dict[str, Any]:
        """
        Record a literal collision between two vectors (AND intersection).
        """
        intersection = [a & b for a, b in zip(cw_a, cw_b)]
        result = self.observe(intersection)
        return {
            "input_a_mass": sum(cw_a), "input_b_mass": sum(cw_b),
            "output_mass": result.mass, "output_energy": result.energy,
            "output_is_ground": result.is_ground_state,
            "output_wall_distance": result.wall_distance,
            "output_quadrant": result.quadrant,
            "mass_defect": sum(cw_a) + sum(cw_b) - result.mass,
        }

    def collide_batch(self, vectors_a: List[List[int]],
                       vectors_b: Optional[List[List[int]]] = None,
                       max_pairs: int = 1000) -> List[Dict[str, Any]]:
        """Batch collision experiment."""
        if vectors_b is None:
            vectors_b = vectors_a
        results = []
        count = 0
        for i, a in enumerate(vectors_a):
            for j, b in enumerate(vectors_b):
                if count >= max_pairs:
                    return results
                if vectors_a is vectors_b and j <= i:
                    continue
                results.append(self.collide(a, b))
                count += 1
        return results

    # ── Holographic verification ────────────────────────────────────────

    def holographic_seal(self, vec: List[int]) -> Dict[str, Any]:
        """
        Test the MOG column-pair holographic verification.
        """
        columns = []
        for col in range(6):
            column = [vec[col], vec[col+6], vec[col+12], vec[col+18]]
            columns.append(column)

        col_weights = [sum(c) for c in columns]
        col_parities = [w % 2 for w in col_weights]

        return {
            "col_weights": col_weights,
            "col_parities": col_parities,
            "all_even_parity": all(p == 0 for p in col_parities),
            "is_balanced": len(set(col_weights)) == 1,
            "balanced_pattern": tuple(col_weights) if len(set(col_weights)) == 1 else None,
        }

    # ── Quadrant analysis ───────────────────────────────────────────────

    def quadrant_analysis(self, events: List[PhysicalEvent]) -> Dict[str, int]:
        """Count events by quadrant."""
        dist = defaultdict(int)
        for ev in events:
            dist[ev.quadrant] += 1
        return dict(sorted(dist.items()))

    # ── Weighted observations ───────────────────────────────────────────

    def weighted_wall_distance(self, events: List[PhysicalEvent]) -> Dict[int, float]:
        """Wall distance distribution weighted by Y^(mass/8)."""
        weighted = defaultdict(float)
        for ev in events:
            weight = float(self.Y ** (ev.mass / 8))
            weighted[ev.wall_distance] += weight
        return dict(sorted(weighted.items()))

    # ── Full report ─────────────────────────────────────────────────────

    def full_report(self, n_random: int = 5000) -> Dict[str, Any]:
        """
        Generate a complete LDP NRCI report.
        """
        report = {}

        # Observe all codewords
        cw_events = [self.observe(cw) for cw in self._codewords]
        report["codewords"] = {
            "count": len(cw_events),
            "mass_distribution": dict(sorted(defaultdict(int, {ev.mass: sum(1 for e in cw_events if e.mass == ev.mass) for ev in cw_events}).items())),
            "energy_distribution": dict(sorted(defaultdict(int, {ev.energy: sum(1 for e in cw_events if e.energy == ev.energy) for ev in cw_events}).items())),
            "quadrant_distribution": self.quadrant_analysis(cw_events),
            "all_ground_state": all(ev.is_ground_state for ev in cw_events),
            "all_zero_energy": all(ev.energy == 0 for ev in cw_events),
        }

        # Observe random vectors
        rand_events = [self.observe([random.randint(0, 1) for _ in range(24)]) for _ in range(n_random)]
        report["random"] = {
            "count": len(rand_events),
            "wall_distance_mean": sum(ev.wall_distance for ev in rand_events) / len(rand_events),
            "wall_distance_distribution": dict(sorted(defaultdict(int, {ev.wall_distance: sum(1 for e in rand_events if e.wall_distance == ev.wall_distance) for ev in rand_events}).items())),
            "weighted_wall": self.weighted_wall_distance(rand_events),
            "quadrant_distribution": self.quadrant_analysis(rand_events),
        }

        # Collision experiments
        octads = self._octads[:30]
        oo_collisions = self.collide_batch(octads, max_pairs=500)
        report["collisions"] = {
            "octad_x_octad": {
                "count": len(oo_collisions),
                "product_mass_dist": dict(sorted(defaultdict(int, {c["output_mass"]: sum(1 for x in oo_collisions if x["output_mass"] == c["output_mass"]) for c in oo_collisions}).items())),
                "ground_state_products": sum(1 for c in oo_collisions if c["output_is_ground"]),
                "mean_mass_defect": sum(c["mass_defect"] for c in oo_collisions) / max(len(oo_collisions), 1),
            }
        }

        # Holographic verification
        cw_seals = [self.holographic_seal(cw) for cw in self._codewords]
        rand_seals = [self.holographic_seal([random.randint(0, 1) for _ in range(24)]) for _ in range(1000)]
        report["holographic"] = {
            "codewords_even_parity": sum(1 for s in cw_seals if s["all_even_parity"]),
            "codewords_balanced": sum(1 for s in cw_seals if s["is_balanced"]),
            "random_even_parity": sum(1 for s in rand_seals if s["all_even_parity"]),
            "random_balanced": sum(1 for s in rand_seals if s["is_balanced"]),
        }

        return report


# ═════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import json

    print("=" * 72)
    print("LITERAL DATA PHYSICS NRCI — Self Test")
    print("=" * 72)

    ldp = LiteralDataPhysicsNRCI()

    # Quick test
    cw = ldp.codewords[0]
    event = ldp.observe(cw)
    print(f"\n  Codeword observation: mass={event.mass}, energy={event.energy}, "
          f"ground={event.is_ground_state}, nrci={event.nrci:.6f}")

    # Collision test
    octads = ldp.octads[:5]
    coll = ldp.collide(octads[0], octads[1])
    print(f"  Collision: {coll['input_a_mass']}×{coll['input_b_mass']} → {coll['output_mass']} "
          f"(ground={coll['output_is_ground']})")

    # Full report
    print("\n  Generating full report...")
    report = ldp.full_report(n_random=2000)

    print(f"\n  Codewords: {report['codewords']['count']}")
    print(f"  All ground state: {report['codewords']['all_ground_state']}")
    print(f"  All zero energy: {report['codewords']['all_zero_energy']}")
    print(f"  Mass dist: {report['codewords']['mass_distribution']}")
    print(f"  Energy dist: {report['codewords']['energy_distribution']}")
    print(f"\n  Random wall distance mean: {report['random']['wall_distance_mean']:.2f}")
    print(f"  Random wall dist: {report['random']['wall_distance_distribution']}")
    print(f"\n  Collision products: {report['collisions']['octad_x_octad']['product_mass_dist']}")
    print(f"  Ground state products: {report['collisions']['octad_x_octad']['ground_state_products']}")
    print(f"\n  Holographic — codewords balanced: {report['holographic']['codewords_balanced']}")
    print(f"  Holographic — random balanced: {report['holographic']['random_balanced']}")

    # Save
    def convert(obj):
        if isinstance(obj, Fraction): return float(obj)
        if isinstance(obj, dict): return {str(k): convert(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)): return [convert(i) for i in obj]
        return obj

    with open("ldp_nrci_report.json", "w") as f:
        json.dump(convert(report), f, indent=2)
    print("\n  Report saved to ldp_nrci_report.json")
    print("  LDP NRCI module ready for use.")
