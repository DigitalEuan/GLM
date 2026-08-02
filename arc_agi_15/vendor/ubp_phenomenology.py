"""
UBP PHENOMENOLOGY ENGINE v5.5 (Modular Core Edition)
====================================================
Author: E R A Craig & UBP Research Cortex v4.2.7
Date: 26 March 2026
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Callable, Optional
from fractions import Fraction
import hashlib
import json

# --- 1. MODULAR CORE LINK ---
try:
    # Pointing to your new modular files
    from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE, BinaryLinearAlgebra, UBPUltimateSubstrate
    from physics import UBPMetricsExact
    CORE_AVAILABLE = True
    print("[Phenomenology] Modular Core Linked Successfully.")
except ImportError as e:
    print(f"[WARNING] Modular Core not found: {e}. Functionality limited.")
    CORE_AVAILABLE = False

# --- 2. DEFINITIONS ---

@dataclass
class PhenomenonDefinition:
    name: str
    domain: str
    bit_generator: Callable[[Dict[str, Any]], List[int]]
    tags: List[str] = field(default_factory=list)

class PhenomenologyEngine:
    def __init__(self):
        self.constants = UBPUltimateSubstrate.get_constants(50) if CORE_AVAILABLE else {}

    def _print_summary(self, res: Dict):
        """Helper to output scan results to console."""
        print(f"  [RESULT] NRCI: {res['metrics']['nrci']:.4f}")
        print(f"  [RESULT] Tax:  {res['metrics']['tax']:.4f}")
        print(f"  [HASH]   {res['hex_id'][:16]}...")

    def process_phenomenon(self, definition: PhenomenonDefinition, data: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n[PHENOMENOLOGY] Scanning: {definition.name}")
        
        bits = definition.bit_generator(data)
        
        if not CORE_AVAILABLE: 
            return {"status": "ERROR", "message": "Core unavailable."}

        # Calculate metrics using the new modular engines
        tax = LEECH_ENGINE.calculate_symmetry_tax(bits)
        nrci = Fraction(10, 1) / (Fraction(10, 1) + tax)
        hex_id = hashlib.sha256(str(bits).encode()).hexdigest()

        result = {
            "mode": "SCAN",
            "phenomenon": definition.name,
            "vector": bits,
            "metrics": {
                "nrci": float(nrci),
                "tax": float(tax),
                "stability": float(nrci)
            },
            "hex_id": hex_id
        }
        self._print_summary(result)
        return result

# --- 3. NOUMENOLOGY (The Projector) ---

class NoumenalProjector:
    def __init__(self):
        if not CORE_AVAILABLE: raise RuntimeError("Core required for Noumenology.")
        self.golay = GOLAY_ENGINE
        self.leech = LEECH_ENGINE
        self.B = [row[12:] for row in self.golay.G]
        self.Y = UBPUltimateSubstrate.get_constants(50)['Y']

    def manifest_intent(self, name: str, shadow_bits: List[int]) -> Dict[str, Any]:
        print(f"\n[NOUMENOLOGY] Projecting: {name}")
        required_matter = BinaryLinearAlgebra.matrix_vector_multiply(self.B, shadow_bits)
        full_vector = required_matter + shadow_bits
        tax = self.leech.calculate_symmetry_tax(full_vector)
        stability = Fraction(10, 1) / (Fraction(10, 1) + tax)

        return {
            "status": "MANIFESTED" if stability > 0.5 else "REJECTED",
            "matter": required_matter,
            "metrics": {"tax": float(tax), "stability": float(stability)}
        }

# --- 4. DEMO ---
if __name__ == "__main__":
    scanner = PhenomenologyEngine()
    
    # Example: RGB to Vector
    def rgb_gen(d): 
        val = (d['r']<<16)|(d['g']<<8)|d['b']
        return [(val>>i)&1 for i in range(23,-1,-1)]
    
    scanner.process_phenomenon(
        PhenomenonDefinition("Pure Cyan", "Optics", rgb_gen), 
        {"r":0, "g":255, "b":255}
    )