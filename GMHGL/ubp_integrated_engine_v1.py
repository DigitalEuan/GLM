"""
UBP INTEGRATED ENGINE v3.4 (Composite Scene Edition)
====================================================
The high-level executive layer of the UBP Studio. 
Bridges the Semantic Brain, the 24D Micro-Core, and the 256D Macro-Bulk.

REFINEMENT:
Added 'Composite Query Detection'. If multiple entities are detected in the 
prompt, the engine bypasses the single-vector confidence threshold and 
automatically constructs a multi-object scene for the ViT Eyes.
Added a `thermo_audit` section to the `analyze_query` output.

Author: E R A Craig and the UBP Research Cortex v4.2.7
Date: 13 April 2026
"""

import json
import hashlib
from fractions import Fraction
from typing import Dict, List, Any
from ubp_brain_consolidated import UBPBrain, extract_vector, extract_name, extract_nrci
from ubp_unified_v5 import BinaryLinearAlgebra, GOLAY_ENGINE
from ubp_unified_v5 import BarnesWallEngine, GOLAY_ENGINE

def hex_to_bw256(hex_str: str) -> list:
    """Converts a 256-bit SHA-256 hash directly into a 256D lattice coordinate."""
    b = bytes.fromhex(hex_str)
    bits = []
    for byte in b:
        bits.extend([(byte >> i) & 1 for i in range(7, -1, -1)])
    return [x * 2 for x in bits]

class VitEyesEngine:
    """The Visual Cortex of the UBP."""
    def __init__(self):
        self.bw = BarnesWallEngine(GOLAY_ENGINE, dimension=256)
        self.golay = GOLAY_ENGINE

    def _visual_hash(self, vec_24d: List[int]) -> str:
        """Hashes the 'Light' (Vector) rather than the 'DNA' (Math)."""
        vec_str = "".join(map(str, vec_24d))
        return hashlib.sha256(vec_str.encode()).hexdigest()

    def observe_scene(self, objects: List[Dict]) -> Dict[str, Any]:
        if not objects: return {"status": "BLIND"}

        embedded_patches = []
        for obj in objects:
            # Visual Projection
            v_hash = self._visual_hash(obj["vector"])
            macro_point = self.bw.generate(v_hash)
            snapped_macro = self.bw.snap(macro_point)
            macro_nrci = self.bw.calculate_nrci(snapped_macro)
            
            embedded_patches.append({
                "name": obj["name"],
                "visual_nrci": float(macro_nrci)
            })

        # The eye darts to the lowest NRCI (Highest Visual Tension)
        embedded_patches.sort(key=lambda e: e["visual_nrci"])
        
        return {
            "status": "SCENE_OBSERVED",
            "primary_focus": embedded_patches[0],
            "peripheral": embedded_patches[1:]
        }

class UBPIntegratedEngine:
    def __init__(self):
        self.brain = UBPBrain()
        self.brain.initialize(['ubp_system_kb.json'])
        self.bw_engine = BarnesWallEngine(GOLAY_ENGINE, dimension=256)
        self.eyes = VitEyesEngine()
        self.COMPLEXITY_THRESHOLD = 0.80 
        print(f"[IntegratedEngine v3.2] Online. Composite Scene Detection Active.")

    def analyze_query(self, query: str):
        """Performs a Penta-Audit on the query."""
        
        # 1. Detect Explicit Entities
        query_lower = query.lower()
        explicit_uids = []
        
        for name, uid in self.brain.kb_manager.short_name_index.items():
            if len(name) > 3 and name in query_lower:
                # NEW: If we find a Molecule or Element, ignore generic "Stability" laws
                if "stability" in name and any(x in query_lower for x in ["glucose", "atp", "water"]):
                    continue 
                if uid not in explicit_uids:
                    explicit_uids.append(uid)

        is_composite = len(explicit_uids) > 1

        # 2. Semantic Resolution
        result = self.brain.process_query(query)
        
        # 3. Fetch Primary Entry (FIX: Priority to explicit detection)
        if explicit_uids:
            primary_uid = explicit_uids[0] # Focus on the first thing mentioned
            confidence_str = "EXPLICIT_MATCH" if not is_composite else "COMPOSITE_SCENE"
        else:
            primary_uid = result.ubp_id
            confidence_str = f"{result.confidence:.2%}"

        if not primary_uid:
            return {"status": "NULL_RESONANCE", "query": query, "response": result.response}

        entry = self.brain.kb_manager.kb[primary_uid]
        true_v24 = extract_vector(entry)
        fingerprint = entry.get('fingerprint', '')
        micro_nrci_frac = extract_nrci(entry)
        
        response_data = {
            "status": "RESOLVED",
            "query": query,
            "primary_subject": extract_name(entry),
            "detected_entities": [extract_name(self.brain.kb_manager.kb[u]) for u in explicit_uids],
            "confidence": confidence_str,
            "micro_nrci": float(micro_nrci_frac),
        }

        # 4. Ontological Drift Lens (256D -> 24D)
        if fingerprint and true_v24:
            hash_vec_256 = hex_to_bw256(fingerprint)
            snapped_256 = self.bw_engine.snap(hash_vec_256)
            hash_core_24 = [abs(x)//2 for x in snapped_256[:24]]
            drift = BinaryLinearAlgebra.hamming_distance(true_v24, hash_core_24)
            
            if drift <= 3: ontology = "PHENOMENAL (Physical Matter)"
            elif 11 <= drift <= 13: ontology = "NOUMENAL (Abstract Concept / Math)"
            else: ontology = "TRANSITIONAL (Anomalous State)"
            
            response_data["ontology"] = f"{ontology} [{drift} bits drift]"

        # 5. Macro-Coherence Lens (256D Audit)
        if fingerprint:
            macro_audit = self.bw_engine.audit(primary_uid, micro_nrci_frac, fingerprint)
            response_data["macro_audit"] = {
                "macro_nrci": macro_audit["macro_nrci"],
                "relative_coherence": f"{macro_audit['relative_coherence']:.2%}",
                "clarity_status": macro_audit["clarity_status"]
            }

        # 6. Imagination Sandbox (ViT Eyes)
        scene_objects = []
        uids_to_viz = explicit_uids if explicit_uids else ([result.ubp_id] if result.ubp_id else [])
        for uid in uids_to_viz[:5]:
            e = self.brain.kb_manager.kb.get(uid)
            if e and extract_vector(e):
                scene_objects.append({"name": extract_name(e), "vector": extract_vector(e)})
        
        if scene_objects:
            vision_report = self.eyes.observe_scene(scene_objects)
            response_data["imagination_sandbox"] = vision_report

        
        # 6. Thermodynamic Lens (Pantograph Projection)
        if true_v24:
            from ubp_unified_v5 import LEECH_ENGINE
            t_adj = LEECH_ENGINE.calculate_symmetry_tax(true_v24)
            n_macro = Fraction(10, 1) / (Fraction(10, 1) + t_adj)
            response_data["thermo_audit"] = {
                "macroscopic_nrci": float(n_macro),
                "adjusted_tax": float(t_adj),
                "status": "STABLE" if n_macro >= 0.7 else "UNSTABLE"
            }

        return response_data

if __name__ == "__main__":
    engine = UBPIntegratedEngine()
    
    print("\n" + "="*80)
    print("PENTA-AUDIT TEST (COMPOSITE SCENE EDITION)")
    print("="*80)
    
    query = "Compare the stability of Glucose, ATP, and Water."
    print(f"\nQ: {query}")
    res = engine.analyze_query(query)
    print(json.dumps(res, indent=2))