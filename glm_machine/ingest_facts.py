#!/usr/bin/env python3
"""
General Knowledge Ingestion for GLM
=====================================
Ingests common facts, constants, and definitions to improve factual recall.
"""

import json
import sys
import os
import hashlib
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
SERVER_DIR = BASE_DIR / "server"
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(SERVER_DIR))
os.environ['UBP_CORE_PATH'] = str(DATA_DIR)

# ═══════════════════════════════════════════════════════════════════════════
# GENERAL KNOWLEDGE DATABASE
# ═══════════════════════════════════════════════════════════════════════════

FACTS = {
    # Physics constants
    "speed of light": "The speed of light in vacuum is approximately 299,792,458 meters per second (c ≈ 3×10⁸ m/s).",
    "planck constant": "Planck's constant (h) is approximately 6.626 × 10⁻³⁴ joule-seconds. It relates photon energy to frequency: E = hf.",
    "gravitational constant": "The gravitational constant (G) is approximately 6.674 × 10⁻¹¹ N⋅m²/kg². It appears in Newton's law of universal gravitation.",
    "boltzmann constant": "The Boltzmann constant (k_B) is approximately 1.381 × 10⁻²³ J/K. It relates temperature to energy.",
    "elementary charge": "The elementary charge (e) is approximately 1.602 × 10⁻¹⁹ coulombs. It is the charge of a single proton.",
    "avogadro number": "Avogadro's number (N_A) is approximately 6.022 × 10²³ mol⁻¹. It defines the number of particles in one mole.",
    "pi": "Pi (π) is approximately 3.14159265358979. It is the ratio of a circle's circumference to its diameter.",
    "euler number": "Euler's number (e) is approximately 2.71828182845904. It is the base of natural logarithms.",
    "golden ratio": "The golden ratio (φ) is approximately 1.61803398874989. It appears throughout nature, art, and mathematics.",
    "fine structure constant": "The fine structure constant (α) is approximately 1/137.036. It characterizes the strength of electromagnetic interaction.",
    
    # Common facts
    "earth": "Earth is the third planet from the Sun. It has one moon, a diameter of about 12,742 km, and orbits the Sun in 365.25 days.",
    "sun": "The Sun is a G-type main-sequence star at the center of our solar system. Its surface temperature is about 5,778 K.",
    "moon": "The Moon is Earth's only natural satellite. It has a diameter of about 3,474 km and orbits Earth every 27.3 days.",
    "mercury": "Mercury is the closest planet to the Sun and the smallest planet in our solar system. It has no atmosphere.",
    "venus": "Venus is the second planet from the Sun. It has a thick toxic atmosphere and is the hottest planet in our solar system.",
    "mars": "Mars is the fourth planet from the Sun. It has a thin atmosphere and is known as the Red Planet.",
    "jupiter": "Jupiter is the fifth planet from the Sun and the largest in our solar system. It has a Great Red Spot.",
    "saturn": "Saturn is the sixth planet from the Sun, famous for its prominent ring system.",
    "uranus": "Uranus is the seventh planet from the Sun. It rotates on its side.",
    "neptune": "Neptune is the eighth and farthest planet from the Sun.",
    
    # Chemistry
    "water": "Water (H₂O) is a molecule consisting of two hydrogen atoms and one oxygen atom. It is essential for life.",
    "oxygen": "Oxygen (O) is element 8. It makes up about 21% of Earth's atmosphere and is essential for respiration.",
    "hydrogen": "Hydrogen (H) is element 1, the lightest and most abundant element in the universe.",
    "carbon": "Carbon (C) is element 6. It is the basis of organic chemistry and all known life.",
    "nitrogen": "Nitrogen (N) is element 7. It makes up about 78% of Earth's atmosphere.",
    "iron": "Iron (Fe) is element 26. It is the most common element on Earth by mass.",
    "gold": "Gold (Au) is element 79. It is a precious metal used in jewelry and electronics.",
    "silver": "Silver (Ag) is element 47. It has the highest electrical conductivity of any element.",
    "copper": "Copper (Cu) is element 29. It is widely used in electrical wiring.",
    "helium": "Helium (He) is element 2. It is the second lightest element and is inert.",
    
    # Biology
    "dna": "DNA (deoxyribonucleic acid) is the molecule that carries genetic instructions for life. It has a double helix structure.",
    "rna": "RNA (ribonucleic acid) is a molecule similar to DNA. It plays key roles in protein synthesis.",
    "cell": "The cell is the basic structural and functional unit of all living organisms.",
    "mitochondria": "Mitochondria are organelles that generate most of a cell's ATP energy. They have their own DNA.",
    "photosynthesis": "Photosynthesis is the process by which plants convert light energy into chemical energy (glucose) using CO₂ and H₂O.",
    "evolution": "Evolution is the change in species over time through natural selection, mutation, and genetic drift.",
    "ecosystem": "An ecosystem is a community of living organisms interacting with their physical environment.",
    
    # Mathematics
    "pythagorean theorem": "The Pythagorean theorem states that in a right triangle, a² + b² = c², where c is the hypotenuse.",
    "prime number": "A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.",
    "fibonacci sequence": "The Fibonacci sequence starts 0, 1, 1, 2, 3, 5, 8, 13, ... where each number is the sum of the two preceding ones.",
    "imaginary number": "The imaginary unit i is defined as √(-1). Complex numbers have the form a + bi.",
    "infinity": "Infinity (∞) is not a number but a concept representing something without bound or end.",
    "zero": "Zero (0) is the additive identity. It represents nothing or the absence of quantity.",
    "one": "One (1) is the multiplicative identity. Any number multiplied by 1 remains unchanged.",
    
    # Technology
    "internet": "The Internet is a global network of interconnected computers using the TCP/IP protocol.",
    "computer": "A computer is an electronic device that processes data according to a set of instructions (programs).",
    "algorithm": "An algorithm is a step-by-step procedure for solving a problem or performing a computation.",
    "artificial intelligence": "Artificial intelligence (AI) is the simulation of human intelligence by machines.",
    "machine learning": "Machine learning is a subset of AI where systems learn from data without being explicitly programmed.",
    "quantum computing": "Quantum computing uses quantum bits (qubits) that can exist in superposition, enabling parallel computation.",
    
    # Geography
    "pacific ocean": "The Pacific Ocean is the largest and deepest ocean on Earth, covering about 63 million square miles.",
    "mount everest": "Mount Everest is the tallest mountain above sea level at 8,849 meters (29,032 feet).",
    "sahara desert": "The Sahara is the world's largest hot desert, covering about 9.2 million square kilometers in North Africa.",
    "amazon river": "The Amazon River is the largest river by discharge volume and the second longest river in the world.",
    "great wall of china": "The Great Wall of China is a series of fortifications stretching over 13,000 miles, built to protect against invasions.",
    
    # History
    "world war ii": "World War II (1939-1945) was the deadliest conflict in human history, involving most of the world's nations.",
    "roman empire": "The Roman Empire (27 BC - 476 AD) was one of the largest and most influential empires in history.",
    "industrial revolution": "The Industrial Revolution (1760-1840) was a period of major industrialization that transformed economies and societies.",
    "renaissance": "The Renaissance (14th-17th century) was a cultural movement that began in Italy, marking a rebirth of art and learning.",
    
    # Music
    "octave": "An octave is the interval between one musical pitch and another with double its frequency.",
    "chord": "A chord is a group of three or more notes played together in music.",
    "tempo": "Tempo is the speed or pace of a piece of music, measured in beats per minute (BPM).",
    
    # Philosophy
    "logic": "Logic is the study of valid reasoning and argumentation.",
    "ethics": "Ethics is the branch of philosophy that deals with morality and principles of right and wrong behavior.",
    "metaphysics": "Metaphysics is the branch of philosophy that examines the fundamental nature of reality.",
    "epistemology": "Epistemology is the branch of philosophy concerned with the nature and scope of knowledge.",
}


def ingest_facts():
    """Ingest general knowledge facts into the GLM."""
    print("=" * 60)
    print("General Knowledge Ingestion")
    print("=" * 60)
    
    # Initialize GLM
    from GLM00_config import KB_SYSTEM_PATH, KB_LANG_PATH
    GLM00_config = __import__('GLM00_config')
    GLM00_config.KB_SYSTEM_PATH = DATA_DIR / "ubp_system_kb.json"
    GLM00_config.KB_LANG_PATH = DATA_DIR / "ubp_lang_kb_combined_v4.json"
    
    from GLM11_runtime import GLMRuntimeV37
    from GLM01_substrate import WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category
    
    print("\n[1] Initializing GLM...")
    rt = GLMRuntimeV37(auto_expand=True)
    print(f"    Vocab: {len(rt.vocab_dict)}, Edges: {len(rt.crg.edges)}")
    
    # Ingest facts
    print("\n[2] Ingesting general knowledge facts...")
    from GLM import TextMiner
    miner = TextMiner(rt.vocab_dict, rt.crg)
    
    facts_added = 0
    edges_added = 0
    
    for topic, fact in FACTS.items():
        # Add topic to vocabulary if not present
        if topic not in rt.vocab_dict:
            miner._create_word(topic)
        
        # Set the definition
        if topic in rt.vocab_dict:
            rt.vocab_dict[topic].definition = fact
            facts_added += 1
        
        # Extract relationships from the fact
        # Pattern: "X is Y" → is_a edge
        m = re.match(r'(\w+)\s+is\s+(?:a|an|the)\s+(.+?)(?:\.|,)', fact)
        if m:
            subject = m.group(1).lower()
            predicate = m.group(2).strip().lower()
            if subject in rt.vocab_dict:
                if predicate not in rt.vocab_dict:
                    miner._create_word(predicate)
                rt.crg.add_edge(subject, "is_a", predicate)
                edges_added += 1
        
        # Pattern: "X consists of Y" → contains edge
        m = re.search(r'consists?\s+of\s+(.+?)(?:\.|,)', fact)
        if m:
            target = m.group(1).strip().lower()
            if topic in rt.vocab_dict:
                if target not in rt.vocab_dict:
                    miner._create_word(target)
                rt.crg.add_edge(topic, "contains", target)
                edges_added += 1
        
        # Pattern: "X is essential for Y" → depends_on edge
        m = re.search(r'essential\s+for\s+(\w+)', fact)
        if m:
            target = m.group(1).lower()
            if topic in rt.vocab_dict:
                if target not in rt.vocab_dict:
                    miner._create_word(target)
                rt.crg.add_edge(target, "depends_on", topic)
                edges_added += 1
    
    # Add specific relationship edges
    print("\n[3] Adding relationship edges...")
    specific_edges = [
        ("earth", "orbits", "sun"),
        ("moon", "orbits", "earth"),
        ("mercury", "orbits", "sun"),
        ("venus", "orbits", "sun"),
        ("mars", "orbits", "sun"),
        ("jupiter", "orbits", "sun"),
        ("saturn", "orbits", "sun"),
        ("uranus", "orbits", "sun"),
        ("neptune", "orbits", "sun"),
        ("water", "contains", "hydrogen"),
        ("water", "contains", "oxygen"),
        ("photosynthesis", "uses", "light"),
        ("photosynthesis", "produces", "oxygen"),
        ("photosynthesis", "consumes", "carbon dioxide"),
        ("dna", "encodes", "genetic information"),
        ("cell", "contains", "dna"),
        ("cell", "contains", "mitochondria"),
        ("earth", "has", "atmosphere"),
        ("sun", "is_a", "star"),
        ("earth", "is_a", "planet"),
        ("moon", "is_a", "satellite"),
        ("pi", "is_a", "transcendental"),
        ("euler number", "is_a", "transcendental"),
        ("golden ratio", "is_a", "irrational"),
        ("prime number", "is_a", "number"),
        ("fibonacci sequence", "is_a", "sequence"),
        ("internet", "is_a", "network"),
        ("algorithm", "is_a", "procedure"),
        ("artificial intelligence", "is_a", "technology"),
        ("machine learning", "is_a", "artificial intelligence"),
        ("quantum computing", "is_a", "computing"),
        ("photosynthesis", "is_a", "biological process"),
        ("evolution", "is_a", "biological process"),
        ("cell", "is_a", "biological unit"),
        ("dna", "is_a", "molecule"),
        ("rna", "is_a", "molecule"),
        ("water", "is_a", "molecule"),
        ("oxygen", "is_a", "element"),
        ("hydrogen", "is_a", "element"),
        ("carbon", "is_a", "element"),
        ("nitrogen", "is_a", "element"),
        ("iron", "is_a", "element"),
        ("gold", "is_a", "element"),
        ("silver", "is_a", "element"),
        ("copper", "is_a", "element"),
        ("helium", "is_a", "element"),
        ("speed of light", "is_a", "physical constant"),
        ("planck constant", "is_a", "physical constant"),
        ("gravitational constant", "is_a", "physical constant"),
        ("boltzmann constant", "is_a", "physical constant"),
        ("elementary charge", "is_a", "physical constant"),
        ("avogadro number", "is_a", "physical constant"),
        ("fine structure constant", "is_a", "physical constant"),
    ]
    
    for src, label, dst in specific_edges:
        for w in [src, dst]:
            if w not in rt.vocab_dict:
                miner._create_word(w)
        rt.crg.add_edge(src, label, dst)
        edges_added += 1
    
    # Persist
    print("\n[4] Persisting...")
    from GLM_persistence import GLMPersistence
    persist = GLMPersistence(str(BASE_DIR / "glm_state"))
    
    for word, entry in rt.vocab_dict.items():
        defn = getattr(entry, 'definition', '')
        if defn:
            persist.save_vocab(word, defn, list(entry.vector), source="general_knowledge")
    
    for edge in rt.crg.edges:
        persist.save_edge(edge.src, edge.label, edge.dst, source="general_knowledge")
    
    print(f"\n{'=' * 60}")
    print(f"INGESTION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Facts added: {facts_added}")
    print(f"  Edges added: {edges_added}")
    print(f"  Final vocab: {len(rt.vocab_dict)}")
    print(f"  Final edges: {len(rt.crg.edges)}")
    print(f"{'=' * 60}")
    
    return rt


if __name__ == "__main__":
    rt = ingest_facts()
    
    # Quick test
    print("\n=== QUICK TESTS ===")
    for q in ["What is the speed of light?", "What is pi?", "What is water?", 
              "What is photosynthesis?", "What is the golden ratio?"]:
        rt.reset_idea()
        r = rt.chat(q)
        print(f"\nQ: {q}")
        print(f"A: {r[:300]}")
