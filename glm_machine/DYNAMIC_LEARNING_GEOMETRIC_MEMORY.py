#!/usr/bin/env python3
"""
GLM v15.0: DYNAMIC LEARNING & GEOMETRIC MEMORY
==============================================
EXPERIMENT ID: GLM-DYNAMIC-LEARN-v1
STATUS: Experimental (clearly recorded per UBP mandate)

HYPOTHESIS:
  The GLM does not need a static dictionary. It can "geometricize" 
  unknown words on the fly based on structural heuristics (suffixes, 
  capitalization). These words are saved into Geometric Memory 
  (the latent space), allowing the engine to "learn" as it reads, 
  and later "recall" those words to generate novel sentences.
"""

from dataclasses import dataclass
from typing import List, Dict
from ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine, UBPSourceCodeParticlePhysics
from fractions import Fraction

# ═══════════════════════════════════════════════════════════════
# ENGINE INITIALISATION
# ═══════════════════════════════════════════════════════════════
g   = GolayCodeEngine()
l   = LeechLatticeEngine(g)
pp  = UBPSourceCodeParticlePhysics()

G_TOPO = (Fraction(39, 29) * (pp.Y ** 18)) / pp.wobble
ALL_OCTADS = g.get_octads()

# ═══════════════════════════════════════════════════════════════
# DYNAMIC GEOMETRICIZER (The "POS Tagger")
# ═══════════════════════════════════════════════════════════════
def geometricize_word(word: str) -> dict:
    """
    Infers grammatical math from the word's structure on the fly.
    This replaces the static dictionary.
    """
    w = word.lower()
    
    # 1. Infer Category
    if w in ["then", "and", "with", "due_to", "therefore"]:
        cat, layer, arm = "Connective", "Activation", "sto"
    elif w.endswith("s") or w.endswith("ed") or w.endswith("ing"):
        cat, layer, arm = "Action", "Information", "sto"
    elif w.endswith("ity") or w.endswith("ness") or w in ["gravity", "blue", "hot", "cold"]:
        cat, layer, arm = "State", "Potential", "sto"
    elif word[0].isupper():
        cat, layer, arm = "Object", "Reality", "det" # Treat proper nouns as discrete Objects
    else:
        cat, layer, arm = "Mass", "Reality", "sto" # Default to Mass/Matter

    return {"word": word, "layer": layer, "arm": arm, "category": cat}

# ═══════════════════════════════════════════════════════════════
# GLM LEARNING ENGINE
# ═══════════════════════════════════════════════════════════════
@dataclass
class WordMath:
    layer: str
    arm: str
    category: str
    phase: int
    word: str = ""

    @property
    def octant(self) -> int:
        lm = {'Reality': 0, 'Information': 1, 'Activation': 2, 'Potential': 3}
        return (lm[self.layer] << 1) | (0 if self.arm == 'det' else 1)

def encode_semantic_octad(wm: WordMath) -> List[int]:
    bits = [0] * 12
    octant = wm.octant
    for i in range(3): bits[i] = (octant >> i) & 1
    cat_map = {'Person': 0, 'Object': 1, 'Action': 2, 'Concept': 3, 
               'Mass': 4, 'Connective': 5, 'Metadata': 6, 'State': 7}
    cat_idx = cat_map.get(wm.category, 0)
    for i in range(3): bits[3 + i] = (cat_idx >> i) & 1
    for i in range(3): bits[6 + i] = (wm.phase >> i) & 1
    
    w = wm.word.lower()
    bits[9] = (len(w) % 4) & 1
    bits[10] = sum(1 for c in w if c in 'aeiou') % 2
    bits[11] = len(w) % 2
    
    base_cw = g.encode(bits)
    return min(ALL_OCTADS, key=lambda oct: sum(a != b for a, b in zip(base_cw, oct)))

class LearningEngine:
    def __init__(self):
        self.memory = [] # Geometric Memory
        self.results = []

    def read_and_learn(self, sentence: List[str]):
        """
        Reads a sentence, geometricizes unknown words, saves to memory,
        and validates the logical cascade.
        """
        self.results = []
        print(f"\n[ENGINE] Reading and learning: '{' '.join(sentence)}'")
        
        for i, word in enumerate(sentence):
            # 1. Geometricize on the fly
            tag = geometricize_word(word)
            wm = WordMath(tag["layer"], tag["arm"], tag["category"], i, word)
            
            # 2. Manifest into lattice
            snapped = encode_semantic_octad(wm)
            nrci = float(l.calculate_nrci(snapped))
            lock_pressure = l.calculate_nrci(snapped) * pp.Y if nrci >= 0.70 else Fraction(0)
            
            # 3. LEARN: Save to geometric memory if not already there
            if not any(m["word"] == word for m in self.memory):
                self.memory.append({"word": word, "wm": wm, "vec": snapped})
                print(f"  + Learned '{word}' as {wm.category}. Memory size: {len(self.memory)}")
            
            sextets = [sum(snapped[j:j+6]) for j in range(0, 24, 6)]
            dom_idx = sextets.index(max(sextets))
            
            self.results.append({
                "word": word, "wm": wm, "snapped": snapped, 
                "dom_idx": dom_idx, "dom_name": ["Reality", "Info", "Activation", "Potential"][dom_idx],
                "lock_pressure_frac": lock_pressure
            })

    def validate_transitions(self) -> List[dict]:
        CAUSAL_MAP = {
            "Mass": ["Action", "Connective"], "Object": ["Action", "Connective"],
            "Action": ["Mass", "Object", "State", "Connective"], "State": ["Connective"],
            "Connective": ["Mass", "Object", "Action", "State"], "Concept": ["Action", "State", "Connective"]
        }
        transitions = []
        for i in range(len(self.results) - 1):
            r1 = self.results[i]
            r2 = self.results[i+1]
            w1 = r1["word"]
            w2 = r2["word"]
            dist = sum(a != b for a, b in zip(r1["snapped"], r2["snapped"]))
            m1, m2 = r1["lock_pressure_frac"], r2["lock_pressure_frac"]

            allowed_next = CAUSAL_MAP.get(r1["wm"].category, [])
            causal_valid = r2["wm"].category in allowed_next
            shared_key = (r1["dom_idx"] == r2["dom_idx"])

            if not causal_valid:
                bond, valid, force = "SEVERED (Causal Violation)", False, 0.0
            elif shared_key:
                bond, valid, force = f"TUNNELED ({r1['dom_name']})", True, float(G_TOPO * (m1*m2) / (dist**2))
            else:
                bond, valid, force = "WEAK (Entropic Decay)", True, float(G_TOPO * (m1*m2) / (dist**2) * pp.wobble * Fraction(1,13))

            transitions.append({"trans": f"{w1} -> {w2}", "bond": bond, "valid": valid, "force": force})
        return transitions
    def generate_from_math(self, target_sequence: List[str]) -> List[str]:
        """
        Uses the accumulated Geometric Memory to generate a novel sentence
        based purely on a target mathematical structure.
        """
        generated = []
        for i, target_cat in enumerate(target_sequence):
            target_wm = WordMath("Information", "sto", target_cat, i, "placeholder")
            target_vec = encode_semantic_octad(target_wm)

            # Search MEMORY for closest learned word of the correct category
            best_word, best_dist = "unknown", 999
        for item in self.memory:
            if item["wm"].category != target_cat: continue
            dist = sum(a != b for a, b in zip(target_vec, item["vec"]))
            if dist < best_dist:
                    best_dist, best_word = dist, item["word"]
            generated.append(best_word)
        return generated

# ═══════════════════════════════════════════════════════════════
# RUN EXPERIMENT
# ═══════════════════════════════════════════════════════════════
engine = LearningEngine()

print("═" * 100)
print("PHASE 1: DYNAMIC LEARNING & LOGIC VALIDATION")
print("═" * 100)

# The engine has NEVER seen these words. It will geometricize them on the fly.
SENTENCES = [
    ["asteroid", "falls", "then", "impacts", "planet", "then", "shatters"],
    ["musician", "plays", "guitar", "then", "sings", "loudly"]
]

for sentence in SENTENCES:
    engine.read_and_learn(sentence)
    transitions = engine.validate_transitions()
    valid_count = sum(1 for t in transitions if t["valid"])
    
    print(f"\n  Validation:")
    for t in transitions:
        print(f"    {t['trans']:<30} | {t['bond']:<30} | {'✓' if t['valid'] else '✗'}")
    print(f"  Coherence: {valid_count}/{len(transitions)}")

print("\n" + "═" * 100)
print("PHASE 2: GENERATIVE RECALL FROM ACCUMULATED MEMORY")
print("═" * 100)
print(f"\n[ENGINE] Total vocabulary learned: {len(engine.memory)} words.")

# Ask the engine to generate a sentence based on pure math
TARGET_MATH_1 = ["Mass", "Action", "Object"]
gen_1 = engine.generate_from_math(TARGET_MATH_1)
print(f"Target Math: {TARGET_MATH_1}")
print(f"Generated:   {' '.join(gen_1)}")

TARGET_MATH_2 = ["Object", "Action", "State"]
gen_2 = engine.generate_from_math(TARGET_MATH_2)
print(f"\nTarget Math: {TARGET_MATH_2}")
print(f"Generated:   {' '.join(gen_2)}")