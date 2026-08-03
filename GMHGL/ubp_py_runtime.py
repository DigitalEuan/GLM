import json
import hashlib
import re
from fractions import Fraction
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE, BinaryLinearAlgebra, SUBSTRATE
from ubp_kb_architect import KBArchitect

# System Constants
CONST = SUBSTRATE.get_constants(50)
Y_CONST = CONST['Y']

@dataclass
class CortexAtom:
    label: str
    value: Fraction
    vector: List[int]
    nrci: Fraction
    tax: Fraction
    tilt: float
    tier: int
    category: str
    hierarchy: str
    dqi: float = 1.0
    params: Dict[str, float] = field(default_factory=dict)
    parents: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "label": self.label, "value": str(self.value), "vector": self.vector,
            "nrci": str(self.nrci), "tax": str(self.tax), "tilt": self.tilt,
            "tier": self.tier, "category": self.category, "hierarchy": self.hierarchy,
            "dqi": self.dqi, "params": self.params
        }

class MOGOntology:
    @staticmethod
    def calculate_health(vector):
        """LAW_SUBSTRATE_005: Tetradic MOG partition health (4x6 Array)."""
        return {
            'Reality': round(sum(vector[0:6]) / 6.0, 2),
            'Info': round(sum(vector[6:12]) / 6.0, 2),
            'Activation': round(sum(vector[12:18]) / 6.0, 2),
            'Potential': round(sum(vector[18:24]) / 6.0, 2)
        }

class UBPPyVM:
    def __init__(self, kb_path='ubp_system_kb.json', lattice_path='ubp_py_lattice.json'):
        self.env = {}
        self.kb_path = kb_path
        self.lattice_path = lattice_path
        self._load_kb()

    def _load_kb(self):
        try:
            with open(self.kb_path, 'r') as f: self.kb_cache = json.load(f)
        except: self.kb_cache = {}

    def let(self, label, val_str, tier=0, category="QUANTITY"):
        math_dna = f"Val={val_str}|Cat={category}"
        vec = KBArchitect.generate_vector(math_dna)
        tax, nrci = KBArchitect.calculate_metrics(math_dna, vec)
        self.env[label] = CortexAtom(
            label=label, value=Fraction(val_str), vector=vec,
            nrci=nrci, tax=tax, tilt=KBArchitect.calculate_tilt(vec), 
            tier=tier, category=category, hierarchy="atomic", dqi=float(nrci)
        )
        print(f"[VM] LET {label} = {val_str}")

    def synth(self, label, recipe_str, u_score=1.0):
        components = re.findall(r'(\d+)x([A-Za-z0-9_]+)', recipe_str)
        z24_accumulator = [0.0] * 24
        total_val = Fraction(0)

        for count_str, comp_label in components:
            count = int(count_str)
            if comp_label in self.env:
                atom = self.env[comp_label]
                for _ in range(count):
                    for i in range(24):
                        bit_val = (atom.vector[i] * 2) - 1
                        z24_accumulator[i] += bit_val * float(u_score)
                    total_val += atom.value

        collapsed_vec = [1 if x < 0 else 0 for x in z24_accumulator]
        decoded, _, _ = GOLAY_ENGINE.decode(collapsed_vec)
        snapped = GOLAY_ENGINE.encode(decoded)

        tax = LEECH_ENGINE.calculate_symmetry_tax(snapped)
        nrci = Fraction(10, 1) / (Fraction(10, 1) + tax)
        dqi_final = round(float(nrci) * float(u_score), 4)

        self.env[label] = CortexAtom(
            label=label, value=total_val, vector=snapped,
            nrci=nrci, tax=tax, tilt=KBArchitect.calculate_tilt(snapped),
            tier=1, category="SYNTHESIS", hierarchy=recipe_str, dqi=dqi_final
        )
        print(f"[VM] SYNTH {label} (DQI: {dqi_final})")

    def audit(self, label):
        atom = self.env.get(label)
        if not atom: return
        mog = MOGOntology.calculate_health(atom.vector)
        print(f"--- AUDIT: {atom.label} ---")
        print(f"  NRCI: {float(atom.nrci):.4f} | DQI: {atom.dqi:.4f} | Tilt: {atom.tilt:.2f}°")
        print(f"  [MOG Health] R:{mog['Reality']} I:{mog['Info']} A:{mog['Activation']} P:{mog['Potential']}")

    def to_scene_3d(self) -> dict:
        """Projects 24-bit vectors into 3D space for visualization."""
        spheres = []
        for label, atom in self.env.items():
            # Use 8-bit blocks to determine X, Y, Z
            # We map the sum of bits to a coordinate range [-5, 5]
            x = (sum(atom.vector[0:8]) - 4) * 1.5
            y = (sum(atom.vector[8:16]) - 4) * 1.5
            z = (sum(atom.vector[16:24]) - 4) * 1.5
            
            # Color based on NRCI (Blue = Stable, Red = Unstable)
            hue = int(float(atom.nrci) * 240) # 240 is Blue in HSL
            color = f"hsl({hue}, 100%, 50%)"
            
            spheres.append({
                "x": x, "y": y, "z": z,
                "r": 0.5 + (atom.tier * 0.2),
                "color": "#00ffff" if atom.nrci > 0.7 else "#ff00ff",
                "label": f"{label} (NRCI: {float(atom.nrci):.2f})"
            })
        return {"spheres": spheres}

    def commit(self):
        data = {k: v.to_dict() for k, v in self.env.items()}
        with open(self.lattice_path, 'w') as f: json.dump(data, f, indent=2)
        print(f"[VM] Lattice committed to {self.lattice_path}")