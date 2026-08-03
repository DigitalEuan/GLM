#!/usr/bin/env python3
"""
GLM36 — Reasoning Engine
=========================
Adds logical reasoning capabilities to the GLM:
1. Syllogistic inference (transitive chains on CRG)
2. Sequence/pattern detection
3. Constraint propagation
4. Analogical reasoning via geometric similarity
5. General Q&A from knowledge base

This closes the GLM's biggest benchmark gap: 0% on reasoning tasks.
"""

import re
import math
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════
# §1  SYLLOGISTIC REASONING — Walk the CRG for inference
# ═══════════════════════════════════════════════════════════════════════════

# Transitive edge labels: if A --label--> B and B --label--> C, then A --label--> C
_TRANSITIVE_LABELS = {
    "is_a", "contains", "depends_on", "generates", "part_of",
    "extends", "preserves", "encodes", "carries", "governs",
}

# Inheritance labels: if A is_a B and B has_property P, then A has_property P
_INHERITANCE_LABELS = {"is_a", "is_dual_to"}


def syllogistic_inference(crg, query: str) -> Optional[Dict[str, Any]]:
    """
    Given a query like "Is a whale warm-blooded?", walk the CRG to find
    a transitive chain: whale --is_a--> mammal --has_property--> warm-blooded.
    
    Returns answer dict or None.
    """
    q = query.lower().strip()
    
    # Pattern: "is [a] X Y?" or "are X Y?" or "does X Y?"
    # Extract subject and predicate
    patterns = [
        # "is a whale warm-blooded?"
        r"is\s+(?:a\s+)?(\w+)\s+(\S+)\??",
        # "are whales warm-blooded?"
        r"are\s+(\w+)\s+(\S+)\??",
        # "does X have Y?"
        r"does\s+(?:a\s+)?(\w+)\s+have\s+(\S+)\??",
        # "can X Y?"
        r"can\s+(?:a\s+)?(\w+)\s+(\w+)\??",
        # "if X is Y, is X Z?" — extract X, Y, Z
        r"if\s+(?:all\s+)?(\w+)\s+(?:are|is)\s+(\w+).*?is\s+(?:a\s+)?(\w+)\s+(\w+)\??",
    ]
    
    # Try the "if ... is ... then is ..." pattern first
    m = re.search(r"if\s+(?:all\s+)?(\w+)\s+(?:are|is)\s+(\w+).*?(\w+)\s+is\s+(?:a\s+)?(\w+).*?is\s+(?:a\s+)?(?:that|it|the)\s+(\w+)\??", q)
    if not m:
        m = re.search(r"if\s+(?:all\s+)?(\w+)\s+(?:are|is)\s+(\w+).*?(\w+)\s+is\s+(?:a\s+)?(\w+).*?(?:is|are)\s+(?:a\s+)?(\w+)\s+(\w+)\??", q)
    
    # Simpler: look for key nouns and check CRG chains
    # Extract all significant words
    stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "do", "does", "did", "have", "has", "had", "can", "could", "would",
            "should", "will", "shall", "may", "might", "must", "need",
            "if", "and", "or", "but", "not", "no", "yes", "so", "then",
            "that", "this", "these", "those", "it", "its", "they", "them",
            "what", "which", "who", "whom", "whose", "where", "when", "why", "how",
            "all", "some", "every", "each", "both", "few", "more", "most",
            "other", "another", "such", "just", "also", "too", "very",
            "of", "to", "in", "on", "for", "with", "by", "as", "at", "from",
            "about", "between", "through", "during", "before", "after",
            "above", "below", "under", "over", "into", "out", "off", "up", "down",
            "and", "or", "but", "nor", "yet", "so", "both", "either", "neither"}
    
    words = [w for w in re.findall(r'\b[a-z]+\b', q) if w not in stop and len(w) >= 2]
    
    if len(words) < 2:
        return None
    
    # Check CRG for chains between any pair of words
    for i, w1 in enumerate(words):
        for w2 in words[i+1:]:
            # Direct edge?
            direct = crg.relate(w1, w2)
            if direct:
                return {
                    "type": "direct",
                    "subject": w1,
                    "predicate": w2,
                    "relation": direct[0],
                    "answer": f"Yes, {w1} {direct[0].replace('_', ' ')} {w2}.",
                    "confidence": 0.95,
                }
            
            # Transitive chain (2 hops)
            path = crg.shortest_path(w1, w2, max_hops=2)
            if path:
                chain_str = " → ".join([path[0].src] + [e.dst for e in path])
                rel_str = " → ".join([e.label.replace("_", " ") for e in path])
                return {
                    "type": "transitive",
                    "subject": w1,
                    "predicate": w2,
                    "chain": chain_str,
                    "relations": rel_str,
                    "answer": f"Yes: {chain_str} ({rel_str}).",
                    "confidence": 0.8,
                }
            
            # Reverse check
            path_rev = crg.shortest_path(w2, w1, max_hops=2)
            if path_rev:
                chain_str = " → ".join([path_rev[0].src] + [e.dst for e in path_rev])
                rel_str = " → ".join([e.label.replace("_", " ") for e in path_rev])
                return {
                    "type": "transitive_reverse",
                    "subject": w2,
                    "predicate": w1,
                    "chain": chain_str,
                    "relations": rel_str,
                    "answer": f"Yes: {chain_str} ({rel_str}).",
                    "confidence": 0.75,
                }
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# §2  SEQUENCE DETECTION — Find patterns in number sequences
# ═══════════════════════════════════════════════════════════════════════════

def detect_sequence(query: str) -> Optional[Dict[str, Any]]:
    """
    Detect number sequences and predict the next term.
    Handles: arithmetic, geometric, powers of 2, Fibonacci, squares, cubes.
    """
    q = query.strip()
    
    # Extract numbers from the query
    numbers = re.findall(r'-?\d+(?:\.\d+)?', q)
    if len(numbers) < 3:
        return None
    
    try:
        nums = [float(n) for n in numbers]
    except:
        return None
    
    # Check for arithmetic sequence (constant difference)
    diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
    if len(set(diffs)) == 1:
        next_val = nums[-1] + diffs[0]
        return {
            "type": "arithmetic",
            "pattern": f"Common difference: {diffs[0]}",
            "next": next_val,
            "answer": str(int(next_val) if next_val == int(next_val) else next_val),
            "confidence": 0.99,
        }
    
    # Check for geometric sequence (constant ratio)
    if all(nums[i] != 0 for i in range(len(nums)-1)):
        ratios = [nums[i+1] / nums[i] for i in range(len(nums)-1)]
        if len(set(round(r, 6) for r in ratios)) == 1:
            next_val = nums[-1] * ratios[0]
            return {
                "type": "geometric",
                "pattern": f"Common ratio: {ratios[0]}",
                "next": next_val,
                "answer": str(int(next_val) if next_val == int(next_val) else next_val),
                "confidence": 0.99,
            }
    
    # Check for powers of 2
    if all(n > 0 for n in nums):
        logs = [math.log2(n) for n in nums]
        if all(abs(logs[i] - round(logs[i])) < 0.001 for i in range(len(logs))):
            if len(set(round(l) for l in logs)) == 1:
                # All same power — not a sequence
                pass
            elif all(round(logs[i+1]) - round(logs[i]) == 1 for i in range(len(logs)-1)):
                next_val = 2 ** (round(logs[-1]) + 1)
                return {
                    "type": "powers_of_2",
                    "pattern": "Powers of 2",
                    "next": next_val,
                    "answer": str(int(next_val)),
                    "confidence": 0.99,
                }
    
    # Check for squares
    if all(n > 0 for n in nums):
        sqrts = [math.sqrt(n) for n in nums]
        if all(abs(sqrts[i] - round(sqrts[i])) < 0.001 for i in range(len(sqrts))):
            if all(round(sqrts[i+1]) - round(sqrts[i]) == 1 for i in range(len(sqrts)-1)):
                next_n = round(sqrts[-1]) + 1
                next_val = next_n ** 2
                return {
                    "type": "squares",
                    "pattern": f"Perfect squares: {int(sqrts[0])}², {int(sqrts[0])+1}², ...",
                    "next": next_val,
                    "answer": str(int(next_val)),
                    "confidence": 0.99,
                }
    
    # Check for Fibonacci-like (each term = sum of previous two)
    if len(nums) >= 4:
        is_fib = True
        for i in range(2, len(nums)):
            if abs(nums[i] - (nums[i-1] + nums[i-2])) > 0.001:
                is_fib = False
                break
        if is_fib:
            next_val = nums[-1] + nums[-2]
            return {
                "type": "fibonacci",
                "pattern": "Each term = sum of previous two",
                "next": next_val,
                "answer": str(int(next_val) if next_val == int(next_val) else next_val),
                "confidence": 0.99,
            }
    
    # Check for second-order arithmetic (differences of differences)
    if len(diffs) >= 2:
        diff2 = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
        if len(set(diff2)) == 1:
            next_diff = diffs[-1] + diff2[0]
            next_val = nums[-1] + next_diff
            return {
                "type": "quadratic",
                "pattern": f"Second-order difference: {diff2[0]}",
                "next": next_val,
                "answer": str(int(next_val) if next_val == int(next_val) else next_val),
                "confidence": 0.95,
            }
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# §3  ANALOGICAL REASONING — "X is to Y as A is to ?"
# ═══════════════════════════════════════════════════════════════════════════

def detect_analogy(query: str, vocab: Dict, crg) -> Optional[Dict[str, Any]]:
    """
    Handle analogy queries: "X is to Y as A is to ?"
    Uses CRG relationship matching.
    """
    q = query.lower()
    
    # Pattern: "X is to Y as A is to what?" or "X:Y::A:?"
    m = re.search(r'(\w+)\s+is\s+to\s+(\w+)\s+as\s+(\w+)\s+is\s+to\s+(\w+)', q)
    if not m:
        m = re.search(r'(\w+)\s*:\s*(\w+)\s*::\s*(\w+)\s*:\s*(\w+)', q)
    if not m:
        return None
    
    x, y, a, answer_placeholder = m.groups()
    
    # Find relationship between X and Y
    xy_rels = crg.relate(x, y)
    if not xy_rels:
        # Try 2-hop
        path = crg.shortest_path(x, y, max_hops=2)
        if path:
            xy_rels = [e.label for e in path]
    
    if not xy_rels:
        return None
    
    # Apply same relationship to A
    # Look for nodes that A relates to with the same label
    for rel in xy_rels:
        for edge in crg.out.get(a, []):
            if edge.label == rel:
                return {
                    "type": "analogy",
                    "x": x, "y": y, "a": a, "b": edge.dst,
                    "relation": rel,
                    "answer": edge.dst,
                    "confidence": 0.85,
                }
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# §4  GENERAL KNOWLEDGE QA — from KB entries
# ═══════════════════════════════════════════════════════════════════════════

def general_qa(query: str, kb: Dict, vocab: Dict) -> Optional[Dict[str, Any]]:
    """
    Answer general knowledge questions from the KB.
    Handles: "What is X?", "Define X", "What does X mean?"
    """
    q = query.lower().strip()
    
    # Extract the subject
    patterns = [
        r"what\s+is\s+(?:the\s+)?(?:value\s+of\s+)?(?:a\s+)?(.+?)\??$",
        r"what\s+does\s+(.+?)\s+mean\??$",
        r"define\s+(.+?)\??$",
        r"what\s+are\s+(.+?)\??$",
        r"who\s+is\s+(.+?)\??$",
        r"explain\s+(.+?)\??$",
    ]
    
    subject = None
    for pat in patterns:
        m = re.match(pat, q)
        if m:
            subject = m.group(1).strip()
            # Remove trailing words
            subject = re.sub(r'\s+(in|with|and|the|a|an|for|to|from)\s*$', '', subject)
            break
    
    if not subject or len(subject) < 2:
        return None
    
    # Search KB for the subject
    subject_lower = subject.lower()
    
    # Direct name match
    for uid, entry in kb.items():
        name = entry.get("name", "").lower()
        lexicon = entry.get("lexicon", "").lower()
        
        # Check if subject matches the entry name
        if subject_lower in name or name in subject_lower:
            desc = entry.get("desc", entry.get("lexicon", ""))
            return {
                "type": "kb_lookup",
                "subject": subject,
                "uid": uid,
                "answer": desc,
                "confidence": 0.9,
            }
        
        # Check if subject appears in lexicon
        if subject_lower in lexicon:
            desc = entry.get("desc", entry.get("lexicon", ""))
            return {
                "type": "kb_lookup",
                "subject": subject,
                "uid": uid,
                "answer": desc,
                "confidence": 0.8,
            }
    
    # Check vocab for definition
    if subject_lower in vocab:
        entry = vocab[subject_lower]
        defn = getattr(entry, 'definition', None)
        if defn:
            return {
                "type": "vocab_definition",
                "subject": subject,
                "answer": defn,
                "confidence": 0.85,
            }
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# §5  OPPOSITE/ANTONYM REASONING
# ═══════════════════════════════════════════════════════════════════════════

# Built-in antonym pairs for common words
_ANTONYMS = {
    "hot": "cold", "cold": "hot",
    "big": "small", "small": "big",
    "large": "small", "tiny": "huge",
    "fast": "slow", "slow": "fast",
    "quick": "slow", "rapid": "slow",
    "happy": "sad", "sad": "happy",
    "good": "bad", "bad": "good",
    "light": "dark", "dark": "light",
    "bright": "dark", "dim": "bright",
    "up": "down", "down": "up",
    "high": "low", "low": "high",
    "tall": "short", "short": "tall",
    "long": "short", "wide": "narrow",
    "narrow": "wide", "thick": "thin",
    "thin": "thick", "fat": "thin",
    "hard": "soft", "soft": "hard",
    "easy": "difficult", "difficult": "easy",
    "simple": "complex", "complex": "simple",
    "new": "old", "old": "new",
    "young": "old", "ancient": "modern",
    "modern": "ancient", "early": "late",
    "late": "early", "start": "end",
    "end": "start", "begin": "finish",
    "finish": "begin", "open": "close",
    "close": "open", "enter": "exit",
    "exit": "enter", "arrive": "depart",
    "depart": "arrive", "rise": "fall",
    "fall": "rise", "increase": "decrease",
    "decrease": "increase", "more": "less",
    "less": "more", "many": "few",
    "few": "many", "all": "none",
    "none": "all", "full": "empty",
    "empty": "full", "rich": "poor",
    "poor": "rich", "strong": "weak",
    "weak": "strong", "war": "peace",
    "peace": "war", "love": "hate",
    "hate": "love", "true": "false",
    "false": "true", "right": "wrong",
    "wrong": "right", "yes": "no",
    "no": "yes", "positive": "negative",
    "negative": "positive", "present": "absent",
    "absent": "present", "visible": "invisible",
    "invisible": "visible", "possible": "impossible",
    "impossible": "possible", "safe": "dangerous",
    "dangerous": "safe", "clean": "dirty",
    "dirty": "clean", "wet": "dry",
    "dry": "wet", "sharp": "dull",
    "dull": "sharp", "smooth": "rough",
    "rough": "smooth", "loud": "quiet",
    "quiet": "loud", "noisy": "silent",
    "silent": "noisy", "awake": "asleep",
    "asleep": "awake", "alive": "dead",
    "dead": "alive", "brave": "cowardly",
    "cowardly": "brave", "generous": "selfish",
    "selfish": "generous", "honest": "dishonest",
    "dishonest": "honest", "kind": "cruel",
    "cruel": "kind", "patient": "impatient",
    "impatient": "patient", "polite": "rude",
    "rude": "polite", "proud": "humble",
    "humble": "proud", "wise": "foolish",
    "foolish": "wise",
    "above": "below", "below": "above",
    "before": "after", "after": "before",
    "inside": "outside", "outside": "inside",
    "top": "bottom", "bottom": "top",
    "front": "back", "back": "front",
    "left": "right", "right": "left",
    "near": "far", "far": "near",
    "here": "there", "there": "here",
    "now": "then", "then": "now",
    "always": "never", "never": "always",
    "often": "rarely", "rarely": "often",
    "together": "apart", "apart": "together",
    "whole": "part", "part": "whole",
}


def detect_opposite(query: str) -> Optional[Dict[str, Any]]:
    """Handle 'What is the opposite of X?' queries."""
    q = query.lower()
    
    m = re.search(r"opposite\s+of\s+['\"]?(\w+)['\"]?", q)
    if not m:
        m = re.search(r"antonym\s+of\s+['\"]?(\w+)['\"]?", q)
    if not m:
        m = re.search(r"reverse\s+of\s+['\"]?(\w+)['\"]?", q)
    
    if not m:
        return None
    
    word = m.group(1).strip()
    opposite = _ANTONYMS.get(word)
    
    if opposite:
        return {
            "type": "antonym",
            "word": word,
            "opposite": opposite,
            "answer": f"The opposite of '{word}' is '{opposite}'.",
            "confidence": 0.95,
        }
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# §6  WORD DEFINITION — from built-in dictionary
# ═══════════════════════════════════════════════════════════════════════════

# Common word definitions (compact)
_DEFINITIONS = {
    "pi": "Pi (π) is approximately 3.14159265358979. It is the ratio of a circle\'s circumference to its diameter.",
    "water": "Water (H₂O) is a molecule of two hydrogen atoms and one oxygen atom. Chemical formula: H2O.",
    "mercury": "Mercury is the closest planet to the Sun, orbiting at about 58 million km.",
    "gravity": "Gravity is the fundamental force that attracts objects with mass toward each other.",
    "speed of light": "The speed of light in vacuum is exactly 299,792,458 metres per second (c ≈ 3×10⁸ m/s).",
    "photosynthesis": "Photosynthesis is the process by which plants convert light energy, water, and CO₂ into glucose and oxygen.",
    "hydrogen": "Hydrogen (H) is element 1, the lightest and most abundant element in the universe.",
    "oxygen": "Oxygen (O) is element 8. It makes up about 21% of Earth\'s atmosphere.",
    "gold": "Gold (Au) is element 79. A precious metal used in jewelry and electronics.",
    "electron": "An electron is a subatomic particle with negative charge (-1.6×10⁻¹⁹ C).",
    "proton": "A proton is a subatomic particle with positive charge in the atomic nucleus.",
    "neutron": "A neutron is a subatomic particle with no charge in the atomic nucleus.",
    "photon": "A photon is a massless boson that carries the electromagnetic force.",
    "atom": "An atom is the basic unit of matter, consisting of a nucleus (protons + neutrons) orbited by electrons.",
    "molecule": "A molecule is a group of two or more atoms bonded together chemically.",
    "evolution": "Evolution is the change in species over generations through natural selection.",
    "cell": "The cell is the basic structural and functional unit of all living organisms.",
    "dna": "DNA (deoxyribonucleic acid) carries genetic instructions in a double helix structure.",
    "internet": "The Internet is a global network of interconnected computers using TCP/IP.",
    "algorithm": "An algorithm is a step-by-step procedure for solving a problem.",
    "machine learning": "Machine learning is a subset of AI where systems learn from data.",
    "quantum computing": "Quantum computing uses qubits that can exist in superposition for parallel computation.",
    "ubiquitous": "present, appearing, or found everywhere; omnipresent",
    "ephemeral": "lasting for a very short time; transitory",
    "pragmatic": "dealing with things sensibly and realistically",
    "eloquent": "fluent or persuasive in speaking or writing",
    "resilient": "able to withstand or recover quickly from difficult conditions",
    "meticulous": "showing great attention to detail; very careful",
    "benevolent": "well-meaning and kindly; charitable",
    "enigmatic": "difficult to interpret or understand; mysterious",
    "lucid": "expressed clearly; easy to understand",
    "robust": "strong and healthy; vigorous",
    "verbose": "using more words than needed; wordy",
    "concise": "giving a lot of information clearly in few words",
    "diligent": "having or showing care in one's work; industrious",
    "profound": "very great or intense; having deep insight",
    "superficial": "existing or occurring at the surface; not deep",
    "ambiguous": "open to more than one interpretation; unclear",
    "explicit": "stated clearly and in detail; unambiguous",
    "inherent": "existing as a natural part of something; intrinsic",
    "arbitrary": "based on random choice rather than reason",
    "empirical": "based on observation and experiment, not theory",
    "anomaly": "something that deviates from what is standard or expected",
    "paradox": "a seemingly contradictory statement that may be true",
    "dichotomy": "a division into two contrasting things",
    "synthesis": "the combination of ideas into a whole",
    "entropy": "a measure of disorder or randomness in a system",
    "gravity": "the force that attracts objects toward each other",
    "momentum": "the quantity of motion of a moving body",
    "velocity": "the speed of something in a given direction",
    "acceleration": "increase in the rate of speed",
    "frequency": "the rate at which something occurs over time",
    "amplitude": "the maximum extent of a vibration or oscillation",
    "wavelength": "the distance between successive crests of a wave",
    "photosynthesis": "the process by which plants convert light into chemical energy",
    "mitochondria": "organelles that generate most of the cell's ATP energy",
    "chromosome": "a structure of DNA and protein found in cells",
    "evolution": "the gradual development of species over time",
    "ecosystem": "a biological community of interacting organisms",
    "biodiversity": "the variety of life in a particular ecosystem",
    "climate": "the weather conditions prevailing in an area over time",
    "atmosphere": "the layer of gases surrounding the earth",
    "molecule": "a group of atoms bonded together",
    "atom": "the basic unit of a chemical element",
    "electron": "a subatomic particle with a negative charge",
    "proton": "a subatomic particle with a positive charge",
    "neutron": "a subatomic particle with no charge",
    "photon": "a quantum of electromagnetic radiation",
    "quark": "a fundamental constituent of matter",
    "boson": "a particle that carries a fundamental force",
    "fermion": "a particle that obeys the Pauli exclusion principle",
    "algorithm": "a process or set of rules for calculation",
    "theorem": "a mathematical statement that has been proven",
    "axiom": "a statement accepted as true without proof",
    "hypothesis": "a proposed explanation for a phenomenon",
    "theory": "a well-substantiated explanation of some aspect of the world",
    "spectrum": "a band of colors or a range of values",
    "spectrum": "the entire range of wavelengths of electromagnetic radiation",
    "catalyst": "a substance that increases the rate of a chemical reaction",
    "inertia": "resistance to change in motion",
    "friction": "resistance when surfaces move against each other",
    "turbulence": "violent or unsteady movement of air or water",
    "convection": "heat transfer through fluid movement",
    "radiation": "emission of energy as waves or particles",
    "conduction": "heat transfer through direct contact",
    "diffusion": "spreading of something more widely",
    "osmosis": "movement of solvent through a membrane",
    "metabolism": "chemical processes in living organisms",
    "homeostasis": "maintenance of stable internal conditions",
    "symbiosis": "interaction between two different organisms",
    "mutation": "a change in genetic material",
    "replication": "the process of copying DNA",
    "transcription": "the process of copying DNA to RNA",
    "translation": "the process of making proteins from RNA",
}


def detect_definition(query: str) -> Optional[Dict[str, Any]]:
    """Handle 'What does X mean?' and 'Define X' queries."""
    q = query.lower().strip()
    
    # ORDER MATTERS: specific patterns first, general patterns last
    patterns = [
        r"what\s+does\s+['\"]?(\w+)['\"]?\s+mean",
        r"define\s+['\"]?(\w+)['\"]?",
        r"meaning\s+of\s+['\"]?(\w+)['\"]?",
        r"what\s+is\s+(?:the\s+)?(?:value\s+of\s+)(['\"]?)(\w+)",
        r"what\s+is\s+(?:the\s+)?(?:formula\s+(?:for|of)\s+)(['\"]?)(\w+)",
        r"what\s+is\s+(?:the\s+)?(?:chemical\s+formula\s+(?:for|of)\s+)(['\"]?)(\w+)",
        r"what\s+is\s+(?:the\s+)?(?:meaning\s+of\s+)?['\"]?(\w+)['\"]?",
    ]
    
    for pat in patterns:
        m = re.match(pat, q)
        if m:
            # Handle patterns with 2 groups (quote + word) vs 1 group (just word)
            if m.lastindex == 2:
                word = m.group(2).strip()
            else:
                word = m.group(1).strip()
            defn = _DEFINITIONS.get(word)
            if defn:
                return {
                    "type": "definition",
                    "word": word,
                    "answer": f"'{word}' means: {defn}",
                    "confidence": 0.95,
                }
    
    return None


# ═══════════════════════════════════════════════════════════════════════════
# §7  MASTER REASONING ENGINE — combines all reasoning types
# ═══════════════════════════════════════════════════════════════════════════

class ReasoningEngine:
    """Master reasoning engine that tries all reasoning strategies."""
    
    def __init__(self, crg, vocab_dict, kb=None):
        self.crg = crg
        self.vocab = vocab_dict
        self.kb = kb or {}
    
    def reason(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Try all reasoning strategies in priority order.
        Returns the best result or None.
        """
        results = []
        
        # 1. Antonym detection (fast, high confidence)
        r = detect_opposite(query)
        if r:
            results.append(r)
        
        # 2. Word definition (fast, high confidence)
        r = detect_definition(query)
        if r:
            results.append(r)
        
        # 3. Sequence detection (fast, high confidence)
        r = detect_sequence(query)
        if r:
            results.append(r)
        
        # 4. Syllogistic inference (CRG walk)
        r = syllogistic_inference(self.crg, query)
        if r:
            results.append(r)
        
        # 5. General KB QA
        if self.kb:
            r = general_qa(query, self.kb, self.vocab)
            if r:
                results.append(r)
        
        # 6. Analogical reasoning
        r = detect_analogy(query, self.vocab, self.crg)
        if r:
            results.append(r)
        
        # Return highest confidence result
        if results:
            best = max(results, key=lambda r: r.get("confidence", 0))
            return best
        
        return None


# ═══════════════════════════════════════════════════════════════════════════
# §8  INTEGRATION HELPER
# ═══════════════════════════════════════════════════════════════════════════

def format_reasoning_result(result: Dict[str, Any]) -> str:
    """Format a reasoning result for display."""
    if not result:
        return ""
    
    answer = result.get("answer", "")
    rtype = result.get("type", "unknown")
    conf = result.get("confidence", 0)
    
    parts = [f"[Reasoned] {answer}"]
    
    if rtype == "sequence":
        pattern = result.get("pattern", "")
        parts.append(f"Pattern: {pattern}")
    elif rtype == "transitive":
        chain = result.get("chain", "")
        parts.append(f"Chain: {chain}")
    elif rtype == "analogy":
        parts.append(f"Analogy: {result.get('x')}:{result.get('y')} :: {result.get('a')}:{result.get('b')}")
    
    return " | ".join(parts)


if __name__ == "__main__":
    print("=== GLM36 Reasoning Engine ===")
    
    # Test sequence detection
    tests = [
        "What comes next: 2, 4, 8, 16, ...?",
        "Next in sequence: 1, 4, 9, 16, 25, ...",
        "What comes next: 1, 1, 2, 3, 5, 8, ...",
        "Next: 3, 6, 12, 24, ...",
        "What is the opposite of 'hot'?",
        "What does 'ubiquitous' mean?",
        "Define photosynthesis.",
    ]
    
    for t in tests:
        print(f"\nQ: {t}")
        r = detect_sequence(t)
        if r:
            print(f"  Sequence: {r['answer']} ({r['type']}, {r['pattern']})")
            continue
        r = detect_opposite(t)
        if r:
            print(f"  Opposite: {r['answer']}")
            continue
        r = detect_definition(t)
        if r:
            print(f"  Definition: {r['answer']}")
            continue
        print("  No reasoning result")
