from __future__ import annotations
"""
================================================================================
UBP SWARM ORCHESTRATOR — GENESIS EDITION v25.0
================================================================================
Integrates the Oracle Bridge (Two-Track Solve) and Lexical Genesis (Triple Delta).
"""

import json, logging, hashlib, os
from datetime import datetime
from fractions import Fraction

# UBP Core Imports
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from ubp_observer_dynamics import ObserverDynamicsEngine
from ubp_semantic_engine import UBPSemanticEngine
from ubp_semantic_sovereign import SovereignSemanticAuditor, TripleDeltaProjector
from ubp_v28_oracle import ValidationBridge, MathNetKernelExtractor
from ubp_moe_cortex_v2 import UBPMoECortexV2

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger("UBP_Swarm_v25")

def _golay_snap(v):
    decoded, _, _ = GOLAY_ENGINE.decode(v)
    return GOLAY_ENGINE.encode(decoded)

def _vec_to_pos(v):
    x = (sum(v[0:8]) - 4) * 2.0
    y = (sum(v[8:16]) - 4) * 2.0
    z = (sum(v[16:24]) - 4) * 2.0
    return [x, y, z]

class SemanticResonator:
    def __init__(self, engine: UBPSemanticEngine):
        self.engine = engine

    def vectorize_text(self, text: str) -> dict:
        matches = self.engine.query(text, top_k=5)
        if not matches:
            audit = SovereignSemanticAuditor.audit_value(text)
            return {
                "magnitude": float(audit["sw"]), 
                "vector": audit["vector"], 
                "neighbors": [],
                "phase_locked": audit["phase_locked"],
                "lattice_type": audit["lattice"]
            }

        bit_counts = [0] * 24
        total_sim = 0
        neighbors = []
        for m in matches:
            sim = getattr(m, 'score', getattr(m, 'resonance_score', 0.5))
            vec = self.engine._system_vectors.get(m.ubp_id)
            if vec:
                for i, bit in enumerate(vec):
                    bit_counts[i] += 1 if bit > 0 else -1
                total_sim += sim
                neighbors.append({"id": m.ubp_id, "vector": [(b + 1) // 2 for b in vec], "sim": sim})

        composite_vec = [1 if c >= 0 else 0 for c in bit_counts]
        comp_int = sum(b << (23 - i) for i, b in enumerate(composite_vec))
        audit = SovereignSemanticAuditor.audit_value(comp_int)
        magnitude = audit["sw"] * (total_sim / len(matches))

        return {
            "magnitude": float(magnitude), 
            "vector": audit["vector"], 
            "neighbors": neighbors[:3],
            "phase_locked": audit["phase_locked"],
            "lattice_type": audit["lattice"]
        }

class UBPSwarmGenesis_v25:
    def __init__(self):
        self.semantic = UBPSemanticEngine()
        self.semantic.load("ubp_system_kb.json", "ubp_lang_kb_combined_v4.json")
        self.bridge = ValidationBridge()
        self.resonator = SemanticResonator(self.semantic)
        self.moe = UBPMoECortexV2()
        self.observer = ObserverDynamicsEngine()
        self.extractor = MathNetKernelExtractor()

    def run_directive(self, directive: str, prob_id: str, expected: str = "") -> dict:
        log.info(f"[v25] Solving {prob_id}: {directive[:80]}...")

        # 1. Extract the Mathematical Kernel
        kernel_data = self.extractor.extract(directive, expected)
        clean_directive = kernel_data["ubp_directive"]

        # 2. Two-Track Solve (Oracle Bridge) using the clean directive
        solve_data = self.bridge.solve(clean_directive, expected)
        answer = solve_data["canonical"]
        agreement = solve_data["agreement"]

        # 2. Semantic Resonance
        res_data = self.resonator.vectorize_text(directive)
        res_vec = res_data["vector"]

        # 3. Lexical Genesis (Triple Delta)
        # If the concept isn't phase-locked in our dictionary, we invent a formula for it.
        lexical_genesis = "N/A (Phase-Locked)"
        if not res_data["phase_locked"]:
            lexical_genesis = TripleDeltaProjector.project_formula(str(answer), ["α", "β", "γ"])

        # 4. Observer Audit
        nrci = solve_data["fp_nrci"]
        read = self.observer.conscious_read(res_vec, Fraction(nrci).limit_denominator(1000000))

        res = {
            "answer": answer,
            "agreement": agreement,
            "nrci": nrci,
            "status": read['status'],
            "vector": res_vec,
            "neighbors": res_data["neighbors"],
            "lattice": solve_data["fp_lattice"],
            "lexical_genesis": lexical_genesis,
            "lang": self.moe.research(f"{directive} result={answer} nrci={nrci:.4f}", max_words=40),
            "directive": directive,
        }

        self._generate_manifold_map(prob_id, res)
        return res

    def _generate_manifold_map(self, prob_id: str, res: dict):
        q_h = int(hashlib.sha256(res['directive'].encode()).hexdigest(), 16)
        q_vec = [(q_h >> i) & 1 for i in range(23, -1, -1)]
        q_pos = _vec_to_pos(q_vec)
        r_pos = _vec_to_pos(res['vector'])

        spheres = [
            {"x": q_pos[0], "y": q_pos[1], "z": q_pos[2], "r": 0.6, "color": "#ff00ff", "label": "Question"},
            {"x": r_pos[0], "y": r_pos[1], "z": r_pos[2], "r": 1.0, "color": "#00ffff", "label": f"Answer: {res['answer']}"},
        ]
        lines = [{"start": q_pos, "end": r_pos, "color": "#ffffff", "label": f"Consensus: {res['agreement']}"}]

        for n in res['neighbors']:
            n_pos = _vec_to_pos(n['vector'])
            spheres.append({"x": n_pos[0], "y": n_pos[1], "z": n_pos[2], "r": 0.4, "color": "#ffff00", "label": n['id']})
            lines.append({"start": r_pos, "end": n_pos, "color": "#ffff00", "label": "Resonance"})

        with open(f'scene_3d_{prob_id}.json', 'w') as f:
            json.dump({"spheres": spheres, "lines": lines}, f)

    def run(self, problem_file: str):
        with open(problem_file, 'r') as f:
            problems = json.load(f)['problems']

        report = "# UBP TCT v25.0 — THE GENESIS SWARM REPORT\n\n"
        report += "> **v25 Evolution**: Integrated Oracle Bridge (Two-Track Solve) and Lexical Genesis.\n\n"

        for p in problems[:5]: # Run first 5 for demonstration
            log.info(f"Engaging {p['id']}...")
            res = self.run_directive(p['problem'], p['id'], p.get('expected', p.get('answer', '')))

            report += f"## Directive: {p['id']}\n\n"
            report += f"**Problem**: {p['problem']}\n\n"
            report += f"**[Tier 2: Oracle Bridge]** Result: `{res['answer']}` | Consensus: `{res['agreement']}`\n\n"
            report += f"**[Tier 3: Observer]** Status: `{res['status']}` | NRCI: `{res['nrci']:.4f}` | Lattice: `{res['lattice']}`\n\n"
            report += f"**[Tier 4: Lexical Genesis]** Invented Formula: `{res['lexical_genesis']}`\n\n"
            report += f"**[Tier 5: Scribe]**\n> *\"{res['lang']}\"*\n\n---\n\n"

        with open('v25_genesis_swarm_report.md', 'w') as f:
            f.write(report)
        log.info("🏆 Genesis Swarm v25 Complete. Report saved.")

if __name__ == "__main__":
    swarm = UBPSwarmGenesis_v25()
    pf = 'ubp_mathnet_problem_set.json'
    if os.path.exists(pf):
        swarm.run(pf)
    else:
        print(f"[v25] No problem file found at {pf}.")
