"""
MathAtlas v4.0 - The Definitive Mathematical Substrate
======================================================
Consolidated from v1.3, v2.0, and v3.0.

"Every object is a recursive construction of its own history."

Author: E R A Craig / UBP Research Cortex v4.2.7
Date: 13 February 2026
"""

import json
import hashlib
import decimal
import math
import numpy as np
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Union, Set

# --- UBP CORE INTEGRATION ---
try:
    from ubp_unified_v5 import GOLAY_ENGINE as GOLAY_DECODER
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False

# --- THE UNIVERSAL CONSTANT ---
UNIVERSAL_NORTH = [-0.30656966974248284, -0.9197090092274486, 0.2452557357939863]
decimal.getcontext().prec = 300 

class MathAtlasConstants:
    """Ultra-high precision mathematical constants for v4.0."""
    
    @classmethod
    def _cf_to_fraction(cls, cf, depth=100):
        x = Fraction(cf[-1], 1)
        for c in reversed(cf[:-1]): 
            x = Fraction(c, 1) + Fraction(1, x)
        return x

    @classmethod
    def get_pi(cls) -> Fraction:
        cf = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2, 1, 84, 2, 1, 1, 15, 3, 13, 1, 4, 2, 6, 6, 99, 1, 2, 2, 6, 3, 5, 1, 1, 6, 8, 1, 7, 1, 6, 1, 99, 7, 4, 1, 3, 3, 1, 4, 1]
        return cls._cf_to_fraction(cf)
    
    @classmethod
    def get_e(cls) -> Fraction:
        cf = [2] + [x for n in range(1, 30) for x in [1, 2*n, 1]]
        return cls._cf_to_fraction(cf)
    
    @classmethod
    def get_phi(cls) -> Fraction:
        return cls._cf_to_fraction([1]*100)

    @classmethod
    def get_sqrt(cls, n) -> Fraction:
        # Newton's method for rational sqrt
        x = Fraction(n, 1)
        for _ in range(10): x = (x + n/x) / 2
        return x

# Pre-compute
PI = MathAtlasConstants.get_pi()
E = MathAtlasConstants.get_e()
PHI = MathAtlasConstants.get_phi()
Y_CONST = Fraction(1, 1) / (PI + Fraction(2, 1)/PI)

@dataclass
class ConstructionPath:
    """A specific geometric construction for a MathObject."""
    primitives: List[Tuple]
    method: str
    tax: Fraction = field(init=False)
    voxels: List[Tuple] = field(init=False, default_factory=list)

    def __post_init__(self):
        self._build(offset=(0,0,0))

    def _build(self, offset):
        total_tax = Fraction(0, 1)
        x, y, z = offset
        for op_tuple in self.primitives:
            op = op_tuple[0]
            if op == 'D':
                mag = op_tuple[1] if len(op_tuple) > 1 else 1
                for _ in range(mag):
                    x += 1; self.voxels.append((x, y, z, "#00ffff")); total_tax += Y_CONST
            elif op == 'X':
                mag = op_tuple[1] if len(op_tuple) > 1 else 1
                for _ in range(mag):
                    x -= 1; self.voxels.append((x, y, z, "#ff0000")); total_tax += Y_CONST
            elif op in ['N', 'J']:
                child = op_tuple[1]
                # Recursive build
                child_offset = (x, y+1, z) if op == 'N' else (x, y, z+1)
                if hasattr(child, 'get_canonical_path'):
                    cp = child.get_canonical_path()
                    for vx, vy, vz, c in cp.voxels:
                        self.voxels.append((child_offset[0]+vx, child_offset[1]+vy, child_offset[2]+vz, c))
                    total_tax += cp.tax + (Y_CONST / (2 if op == 'N' else 4))
        self.tax = total_tax + Fraction(len(self.voxels)**2, 800)

@dataclass
class MathObjectV4:
    ubp_id: str
    name: str
    description: str
    category: str = "math.general"
    paths: List[ConstructionPath] = field(default_factory=list)
    components: Dict[str, 'MathObjectV4'] = field(default_factory=dict)
    morphisms: Dict[str, str] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)

    def add_path(self, primitives, method):
        path = ConstructionPath(primitives, method)
        self.paths.append(path)
        return path

    def get_canonical_path(self) -> ConstructionPath:
        return min(self.paths, key=lambda p: p.tax) if self.paths else ConstructionPath([], 'empty')

    def get_vector(self) -> List[int]:
        if not CORE_AVAILABLE: return [0]*24
        geo_str = str(sorted(list(set(self.get_canonical_path().voxels))))
        h = hashlib.sha256(geo_str.encode()).digest()
        msg_int = ((h[0] << 8) | h[1]) & 0xFFF
        return GOLAY_DECODER.encode([(msg_int >> i) & 1 for i in range(11, -1, -1)])

    def get_charge(self) -> float: 
        v = [
            float(sum(vector[0:8]) - 4),
            float(sum(vector[8:16]) - 4),
            float(sum(vector[16:24]) - 4)
        ]
        mag = math.sqrt(sum(x*x for x in v))
        if mag == 0: return 0.0
    
        mag_n = math.sqrt(sum(x*x for x in UNIVERSAL_NORTH))
        unit_v = [x / mag for x in v]
        unit_north = [x / mag_n for x in UNIVERSAL_NORTH]
    
        dot = sum(a * b for a, b in zip(unit_v, unit_north))
        return round(float(math.degrees(math.acos(max(-1, min(1, dot))))), 4)

    def get_recursive_math(self) -> str:
        """Builds the full embedded math string."""
        if not self.components: return self.properties.get('math_raw', f"Val={self.name}")
        parts = [f"{k}=[{v.get_recursive_math()}]" for k, v in self.components.items()]
        return "|".join(parts)

    def to_dict(self) -> Dict:
        cp = self.get_canonical_path()
        nrci = Fraction(1, 1) / (Fraction(1, 1) + (cp.tax * Fraction(1, 10)))
        return {
            "ubp_id": self.ubp_id,
            "name": self.name,
            "math": self.get_recursive_math(),
            "category": self.category,
            "nrci": f"{nrci.numerator}/{nrci.denominator}",
            "nrci_score": float(nrci),
            "vector": self.get_vector(),
            "geometric_charge": self.get_charge(),
            "atlas_metadata": {
                "voxels": len(cp.voxels),
                "tax": {"n": cp.tax.numerator, "d": cp.tax.denominator},
                "path_count": len(self.paths)
            }
        }

    def calculate_compactness(self) -> Fraction:
        """
        Calculates the 3D efficiency of the voxel cloud.
        """
        voxels = self.get_canonical_path().voxels
        if not voxels: return Fraction(0)
    
        volume = len(voxels)
        coords = set((v[0], v[1], v[2]) for v in voxels)
    
        # Calculate Surface Area (Exposed Faces)
        surface = 0
        for x, y, z in coords:
            # Check all 6 directions for empty space
            neighbors = [(x+1,y,z), (x-1,y,z), (x,y+1,z), (x,y-1,z), (x,y,z+1), (x,y,z-1)]
            for n in neighbors:
                if n not in coords:
                    surface += 1
    
        if surface == 0: return Fraction(1)
    
        # C = Volume^(2/3) / Surface
        # We use a rational approximation for the 2/3 power
        vol_2_3 = Fraction(int(math.pow(volume, 2/3) * 1000), 1000)
        return vol_2_3 / surface

    def get_nrci(self) -> Fraction:
        """
        v6.0 Unified Stability Formula.
        """
        cp = self.get_canonical_path()
        c_factor = self.calculate_compactness()
    
        # Get the vector and calculate the REBATED tax
        vec = self.get_vector()
        final_tax = LEECH_ENGINE.calculate_symmetry_tax(vec, compactness=c_factor)
    
        # Hyperbolic Stability: 10 / (10 + Tax)
        return Fraction(10, 1) / (Fraction(10, 1) + final_tax)

# --- CONSTRUCTORS ---

def PositiveInteger(n: int) -> MathObjectV4:
    obj = MathObjectV4(f"MATH_NAT_{n:010d}", f"Natural {n}", f"The number {n}", "number.natural")
    obj.add_path([('D', n)], 'direct')
    obj.properties['math_raw'] = f"Val={n}"
    return obj

def Rational(p: int, q: int) -> MathObjectV4:
    num = PositiveInteger(p); den = PositiveInteger(q)
    obj = MathObjectV4(f"MATH_RAT_{p}_{q}", f"Rational {p}/{q}", f"The fraction {p}/{q}", "number.rational")
    obj.components = {"num": num, "den": den}
    obj.add_path([('N', num), ('J', den)], 'nested')
    return obj

class ExactRationalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Fraction): return {"n": obj.numerator, "d": obj.denominator, "v": float(obj)}
        if isinstance(obj, MathObjectV4): return obj.to_dict()
        return super().default(obj)
