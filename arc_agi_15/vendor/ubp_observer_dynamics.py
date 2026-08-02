"""
UBP OBSERVER DYNAMICS ENGINE v7.1 (Columnar Compatible)
=======================================================
Fixed AttributeError by implementing Columnar Hydration for v9.9 KB.
"""

import json
import math
from fractions import Fraction
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE, SUBSTRATE

class ObserverDynamicsEngine:
    def __init__(self):
        self.constants = SUBSTRATE.get_constants(50)
        self.Y = self.constants['Y']
        self.Y_INV = self.constants['Y_INV']
        self.C_CELERITAS = Fraction(299792458, 1)
        self.F_MAX = 10**12  # 1 THz Wall of Reality
        self.CONSCIOUS_THRESHOLD = Fraction(70, 100)

    def split_ontology_layers(self, vector: list) -> dict:
        return {
            "Reality": vector[0:6],
            "Information": vector[6:12],
            "Activation": vector[12:18],
            "Potential": vector[18:24]
        }

    def conscious_read(self, vector: list, nrci: Fraction) -> dict:
        is_conscious = nrci >= self.CONSCIOUS_THRESHOLD
        layers = self.split_ontology_layers(vector)
        if is_conscious:
            return {"status": "MANIFESTED", "is_conscious": True, "new_reality": layers["Potential"]}
        return {"status": "SUBLIMINAL", "is_conscious": False, "new_reality": [0]*6}

    def calculate_soc_energy(self, vector: list, nrci: Fraction, toggle_rate_hz: float = 1.0) -> float:
        weight = sum(vector)
        penalty = 1.0
        if toggle_rate_hz > self.F_MAX:
            penalty = math.exp(-((toggle_rate_hz - self.F_MAX)**2) / (2 * (1e11)**2))
        return float(weight) * float(self.C_CELERITAS) * float(self.Y) * float(nrci) * penalty

def run_observer_audit():
    print("="*75)
    print("UBP OBSERVER DYNAMICS ENGINE v7.1 (COLUMNAR)")
    print("="*75)
    
    engine = ObserverDynamicsEngine()
    
    with open('ubp_system_kb.json', 'r') as f:
        kb_data = json.load(f)

    # Hydrate Columnar Mapping
    fields = kb_data["_fields"]
    idx = {f: i for i, f in enumerate(fields)}
    entries = kb_data["entries"]

    test_ids = ["ELEM_H_001", "PARTICLE_QUARK_TOP_001", "LAW_FOCAL_PIVOT_001"]

    for target_id in test_ids:
        # Find entry in the flat list
        entry_data = next((v for v in entries.values() if v[idx["ubp_id"]] == target_id), None)
        
        if not entry_data:
            print(f"⚠️ Warning: {target_id} not found.")
            continue
            
        uid = entry_data[idx["ubp_id"]]
        vector = entry_data[idx["vector"]]
        nrci_val = entry_data[idx["nrci_val"]]
        nrci = Fraction(nrci_val).limit_denominator(1000000)

        print(f"\n--- Subject: {uid} ---")
        print(f"NRCI: {float(nrci):.6f}")
        
        read = engine.conscious_read(vector, nrci)
        print(f"  [OBSERVER] Status: {read['status']}")
            
        soc = engine.calculate_soc_energy(vector, nrci)
        print(f"  [ENERGY]   SOC:    {soc:,.2f} CU")

    print("\n" + "="*75)
    print("WALL OF REALITY TEST (1 THz Limit)")
    print("="*75)
    
    top_quark = next((v for v in entries.values() if v[idx["ubp_id"]] == "PARTICLE_QUARK_TOP_001"), None)
    if top_quark:
        vec = top_quark[idx["vector"]]
        nrci = Fraction(top_quark[idx["nrci_val"]]).limit_denominator(1000000)
        for f in [1e9, 1e12, 1.2e12]:
            e = engine.calculate_soc_energy(vec, nrci, toggle_rate_hz=f)
            print(f"Freq: {f:.1e} Hz | SOC: {e:,.2f} CU | {'COLLAPSE' if f > 1e12 else 'STABLE'}")

if __name__ == "__main__":
    run_observer_audit()
