"""
UBP KB ARCHITECT v2.2 (SOP_002 Standard + Gray Code)
===================================================
Now uses Binary-Reflected Gray Code for the 24-bit vector.
"""

import hashlib
import json
import math
import numpy as np
from fractions import Fraction
from typing import Tuple, List

# Core imports
from ubp_unified_v5 import LEECH_ENGINE, UBPUltimateSubstrate

# Universal Constants
CONST = UBPUltimateSubstrate.get_constants(50)
UNIVERSAL_NORTH = np.array([-0.30656966974248284, -0.9197090092274486, 0.2452557357939863])

MOG_CATEGORIES = [
    "M_Mass", "M_Charge", "M_Space", "M_Time", "M_Thermal", "M_Count",
    "I_Topology", "I_Symmetry", "I_Density", "I_Connectivity", "I_Dimension", "I_Complexity",
    "A_Energy", "A_Force", "A_Velocity", "A_Flux", "A_Resonance", "A_Spin",
    "P_Probability", "P_Ratio", "P_Limit", "P_Tax", "P_Coherence", "P_Phase"
]

def to_gray_code(n: int, bits: int = 24) -> List[int]:
    """Convert integer to n-bit binary-reflected Gray code."""
    gray = n ^ (n >> 1)
    return [(gray >> i) & 1 for i in range(bits - 1, -1, -1)]

class KBArchitect:
    @staticmethod
    def calculate_metrics(math_dna: str, vector: List[int]) -> Tuple[Fraction, Fraction]:
        tax = LEECH_ENGINE.calculate_symmetry_tax(vector)
        ten = Fraction(10, 1)
        nrci = ten / (ten + tax)
        return tax, nrci

    @staticmethod
    def calculate_tilt(vector: List[int]) -> float:
        v = np.array([
            sum(vector[0:8]) - 4,
            sum(vector[8:16]) - 4,
            sum(vector[16:24]) - 4
        ], dtype=float)
        mag = np.linalg.norm(v)
        if mag == 0:
            return 0.0
        unit_v = v / mag
        unit_north = UNIVERSAL_NORTH / np.linalg.norm(UNIVERSAL_NORTH)
        dot = np.dot(unit_v, unit_north)
        return round(float(math.degrees(math.acos(max(-1, min(1, dot))))), 4)

    @staticmethod
    def generate_vector(math_dna: str, ubp_id: str = None) -> List[int]:
        if ubp_id and ubp_id.startswith("ELEM_"):
            try:
                parts = ubp_id.split("_")
                z = int(parts[2])
                offset = 1000 if len(parts) > 3 and parts[3] else 0
                index = ((z * 0x111111) + offset) & 0xFFFFFF
            except:
                index = 0
        else:
            h = int(hashlib.sha256(math_dna.encode()).hexdigest(), 16)
            index = h & 0xFFFFFF
        return to_gray_code(index)

    def create_entry(self, ubp_id, lexicon_name, definition, math_dna, hierarchy, tags):
        fingerprint = hashlib.sha256(math_dna.encode()).hexdigest()
        vector = self.generate_vector(math_dna, ubp_id)
        tax, nrci = self.calculate_metrics(math_dna, vector)
        tilt = self.calculate_tilt(vector)

        entry = {
            "ubp_id": ubp_id,
            "lexicon": f"{lexicon_name}, {definition}",
            "math": math_dna,
            "atlas": {
                "hierarchy": hierarchy,
                "vector": vector,
                "nrci": f"{nrci.numerator}/{nrci.denominator}",
                "nrci_score": round(float(nrci), 6),
                "tax": f"{tax.numerator}/{tax.denominator}",
                "weight": sum(vector),
                "tilt": tilt
            },
            "tags": sorted(list(set(tags + ["SOP_002", "HARDENED", "TOPOLOGICAL_V8"]))),
            "fingerprint": fingerprint
        }
        return fingerprint, entry
