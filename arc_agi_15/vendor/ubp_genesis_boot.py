"""
UBP GENESIS BOOT ENGINE v7.0 (Topological Edition)
==================================================
Replaces the legacy TriadActivationEngine.
Boots the 24-bit universe from scratch using Gray Code Topological Identity.

PHASES:
1. Seeding: Injects the 24 base geometries and 26 Sporadic Groups.
2. Activation: Slides unstable objects along the Gray manifold until they 
   resonate at a stable Leech Lattice coordinate (Weight 8, NRCI 0.7-0.8).
3. Export: Generates the foundational genesis_atlas.json.

Author: UBP Research Cortex v4.2.7
Date: 01 April 2026
"""

import json
from fractions import Fraction
from datetime import datetime
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE, SUBSTRATE

def to_gray(n: int, bits: int) -> list:
    """Standard Binary to Gray Code conversion."""
    n = int(n) & ((1 << bits) - 1)
    gray = n ^ (n >> 1)
    return [(gray >> i) & 1 for i in range(bits - 1, -1, -1)]

class UBPBootObject:
    """A foundational entity during the Genesis Boot phase."""
    def __init__(self, uid: str, name: str, category: str, domain: int, magnitude: int, state: int):
        self.uid = uid
        self.name = name
        self.category = category
        self.domain = domain
        self.magnitude = magnitude
        self.state = state
        self.vector = []
        self.nrci = Fraction(0)
        self.tax = Fraction(0)
        self.weight = 0
        self.update_vector()

    def update_vector(self):
        """Generates the 24-bit coordinate via Gray Code UMS."""
        seed = to_gray(self.domain, 3) + to_gray(self.magnitude, 5) + to_gray(self.state, 4)
        self.vector = GOLAY_ENGINE.encode(seed)
        self.weight = sum(self.vector)
        self.tax = LEECH_ENGINE.calculate_symmetry_tax(self.vector)
        self.nrci = Fraction(10, 1) / (Fraction(10, 1) + self.tax)

    def is_stable(self) -> bool:
        if self.uid == "PRIMITIVE_POINT": return True
        # Stable Leech Anchor: NRCI between 0.70 and 0.80, Weight 8
        return Fraction(70, 100) <= self.nrci <= Fraction(80, 100) and self.weight == 8

    def decompose(self):
        """
        Topological Decomposition:
        Slides the object along the State/Magnitude axes to find a stable resonance.
        """
        self.state = (self.state + 1) % 16
        if self.state == 0:
            self.magnitude = (self.magnitude + 1) % 32
        self.update_vector()

    def to_dict(self):
        return {
            "ubp_id": self.uid,
            "name": self.name,
            "category": self.category,
            "metrics": {"domain": self.domain, "magnitude": self.magnitude, "state": self.state},
            "vector": self.vector,
            "nrci_score": round(float(self.nrci), 6),
            "tax": f"{self.tax.numerator}/{self.tax.denominator}",
            "is_stable": self.is_stable()
        }

class GenesisBootEngine:
    GOLAY_THRESHOLD = 12
    LEECH_THRESHOLD = 24
    MONSTER_THRESHOLD = 26

    def __init__(self):
        self.atlas = {}
        self.triad_state = {
            'golay_active': False,
            'leech_active': False,
            'monster_active': False,
            'stable_count': 0,
            'sporadic_count': 0
        }

    def seed_primitives(self):
        print("="*72)
        print("PHASE 1: SEEDING TOPOLOGICAL PRIMITIVES")
        print("="*72)
        
        # Domain 0: Quantity/Math
        configs = [
            ("POINT", "Point", "primitive", 0, 0),
            ("SEG_1", "Segment 1", "geometry.1d", 1, 1),
            ("SEG_2", "Segment 2", "geometry.1d", 2, 1),
            ("SEG_3", "Segment 3", "geometry.1d", 3, 1),
            ("SQUARE", "Square", "geometry.2d", 4, 2),
            ("CIRCLE", "Circle", "geometry.2d", 8, 2),
            ("TRIANGLE", "Triangle", "geometry.2d", 3, 2),
            ("PENTAGON", "Pentagon", "geometry.2d", 5, 2),
            ("HEXAGON", "Hexagon", "geometry.2d", 6, 2),
            ("I", "Imaginary Unit", "constant.fundamental", 1, 0),
            ("PHI", "Golden Ratio", "constant.fundamental", 8, 0),
            ("E", "Euler's Number", "constant.fundamental", 4, 0),
            ("GOLAY_12", "Golay 12", "coding_theory.golay", 12, 0),
            ("GOLAY_24", "Golay 24", "coding_theory.golay", 24, 0),
            ("CUBE", "Cube", "geometry.3d", 12, 3),
            ("TETRA", "Tetrahedron", "geometry.3d", 12, 3),
            ("OCTA", "Octahedron", "geometry.3d", 8, 3),
            ("LINE_1", "Line 1", "geometry.1d", 10, 1),
            ("LINE_2", "Line 2", "geometry.1d", 12, 1),
            ("WAVE_1", "Wave 1", "geometry.curve", 5, 1),
            ("WAVE_2", "Wave 2", "geometry.curve", 10, 1),
            ("LOOP_1", "Loop 1", "geometry.topology", 8, 2),
            ("LOOP_2", "Loop 2", "geometry.topology", 16, 2),
            ("KNOT_1", "Knot 1", "geometry.topology", 18, 3),
            ("KNOT_2", "Knot 2", "geometry.topology", 6, 3),
        ]
        
        for suffix, name, cat, mag, state in configs:
            obj = UBPBootObject(f"MATH_{suffix}", name, cat, domain=0, magnitude=mag, state=state)
            self.atlas[obj.uid] = obj
            print(f"  Seeded: {obj.uid:<15} (Weight={obj.weight:02d}, NRCI={float(obj.nrci):.4f})")

        # Domain 3: Algorithm/Group Theory (Sporadic Groups)
        sporadic_names = [
            'M11', 'M12', 'M22', 'M23', 'M24', 'Co1', 'Co2', 'Co3', 'Fi22', 'Fi23', 
            "Fi24'", 'HS', 'McL', 'He', 'Suz', 'J1', 'J2', 'J3', 'J4', 'Ly', 'ON', 
            'Ru', 'Th', 'HN', 'B', 'M'
        ]
        
        for i, name in enumerate(sporadic_names, 1):
            obj = UBPBootObject(f"GROUP_{i:02d}_{name}", name, "group_theory.sporadic", domain=3, magnitude=i, state=0)
            self.atlas[obj.uid] = obj

        print(f"\nTotal seeded: {len(self.atlas)} objects")
        self._update_triad_state()

    def activate(self, max_iter=50):
        print("\n" + "="*72)
        print("PHASE 2: TOPOLOGICAL TRIAD ACTIVATION")
        print("="*72)
        
        for i in range(1, max_iter + 1):
            self._update_triad_state()
            
            if self._is_fully_active():
                print(f"\n✅ TRIAD FULLY ACTIVATED AT ITERATION {i}!")
                self._print_status()
                return True
            
            unstable = [obj for obj in self.atlas.values() if not obj.is_stable() and obj.uid != "PRIMITIVE_POINT"]
            if unstable:
                for obj in unstable:
                    obj.decompose() # Slide along the Gray manifold
                    
        print("\n⚠️ WARNING: Max iterations reached before full stabilization.")
        self._print_status()
        return False

    def _update_triad_state(self):
        stable = sum(1 for obj in self.atlas.values() if obj.is_stable())
        sporadic = sum(1 for obj in self.atlas.values() if 'sporadic' in obj.category and obj.is_stable())
        self.triad_state.update({
            'golay_active': stable >= self.GOLAY_THRESHOLD,
            'leech_active': stable >= self.LEECH_THRESHOLD,
            'monster_active': sporadic >= self.MONSTER_THRESHOLD,
            'stable_count': stable,
            'sporadic_count': sporadic
        })

    def _is_fully_active(self):
        return all([self.triad_state['golay_active'], self.triad_state['leech_active'], self.triad_state['monster_active']])

    def _print_status(self):
        s = self.triad_state
        print(f"  Golay: {s['stable_count']}/{self.GOLAY_THRESHOLD} | " +
              f"Leech: {s['stable_count']}/{self.LEECH_THRESHOLD} | " +
              f"Monster: {s['sporadic_count']}/{self.MONSTER_THRESHOLD}")

    def export(self):
        data = {
            'metadata': {
                'version': 'UBP Genesis Boot v7.0',
                'timestamp': datetime.now().isoformat(),
                'triad_state': self.triad_state,
                'schema': 'Gray Code Topological Identity [Dom:3|Mag:5|State:4]'
            },
            'objects': {k: v.to_dict() for k, v in self.atlas.items()}
        }
        with open('genesis_atlas.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\n💾 Exported foundational anchors to genesis_atlas.json")

if __name__ == "__main__":
    boot = GenesisBootEngine()
    boot.seed_primitives()
    boot.activate()
    boot.export()