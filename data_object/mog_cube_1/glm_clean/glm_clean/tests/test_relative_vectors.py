#!/usr/bin/env python3
"""
The Path: concepts as relative vectors + relation operations.

THE INSIGHT: meaning IS relation to a reference.
- "left" = the vector FROM center TO left = (-1, 0, 0)
- "hot" = the vector FROM freezing TO hot = +60
- The concept IS the vector. The reference IS the origin.

THE PATH:
1. Each concept is a VECTOR from its domain's origin
2. Relations between concepts are VECTOR OPERATIONS:
   - left + right = (0,0,0) = center (addition → composition)
   - hot - cold = +50 (subtraction → difference)
   - 2 × small = medium (scaling → multiplication)
3. The snap finds the "lawful interpretation" of each vector
4. The tax measures how "raw" the concept is
5. The triple (vector, snap, tax) is the full information

The system SPEAKS by computing vector operations and checking if the
results snap to meaningful codewords.
"""

import sys
import json
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/download/arc_agi_17')

from glm_clean import Mind, Body, DataObject
from ubp_unified_v5 import GOLAY_ENGINE


def int_to_6bits(n: int) -> List[int]:
    n = n & 0x3F
    return [(n >> (5 - i)) & 1 for i in range(6)]


# ══════════════════════════════════════════════════════════════════════════════
# CONCEPTS AS RELATIVE VECTORS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Concept:
    """A concept defined by its relation to a reference point.

    The meaning IS the vector from the reference to the concept.
    """
    name: str
    domain: str
    reference: str           # the origin/reference point
    vector: List[float]      # the vector FROM reference TO this concept
    bits: List[int]          # 24-bit encoding of the vector

    def describe(self) -> str:
        return (f"{self.name} ({self.domain}): "
                f"vector from {self.reference} = {self.vector}")


def encode_direction_vector(d: str) -> Concept:
    """Encode a direction as a vector from center."""
    vectors = {
        "left":    (-1, 0, 0), "right":   (+1, 0, 0),
        "up":      (0, +1, 0), "down":    (0, -1, 0),
        "forward": (0, 0, +1), "back":    (0, 0, -1),
        "center":  (0, 0, 0),
    }
    v = vectors[d.lower()]
    # Encode the vector in the bits:
    # Reality (6 bits): domain ID (0 = direction)
    # Info (6 bits): axis (2 bits) + sign (1 bit) + magnitude (3 bits)
    # Activation (6 bits): the vector components packed
    # Potential (6 bits): the reference (center = 0)

    domain_id = 0  # direction
    reality = int_to_6bits(domain_id)

    # Axis: 0=X, 1=Y, 2=Z, 3=center
    if v == (0, 0, 0):
        axis, sign, mag = 3, 0, 0
    elif v[0] != 0:
        axis, sign, mag = 0, (1 if v[0] < 0 else 0), abs(v[0])
    elif v[1] != 0:
        axis, sign, mag = 1, (1 if v[1] < 0 else 0), abs(v[1])
    else:
        axis, sign, mag = 2, (1 if v[2] < 0 else 0), abs(v[2])

    info = int_to_6bits((axis << 4) | (sign << 3) | (mag & 0b111))

    # Activation: the full vector packed (x_sign, x_mag, y_sign, y_mag, z_sign, z_mag)
    x_sign = 1 if v[0] < 0 else 0
    y_sign = 1 if v[1] < 0 else 0
    z_sign = 1 if v[2] < 0 else 0
    activation = int_to_6bits((x_sign << 5) | (abs(v[0]) << 3) | (y_sign << 2) | (abs(v[1]) << 1) | z_sign)

    # Potential: the reference (center = all zeros for direction domain)
    potential = [0] * 6

    bits = reality + info + activation + potential
    return Concept(name=d, domain="direction", reference="center",
                   vector=list(v), bits=bits)


def encode_temperature_vector(t: str) -> Concept:
    """Encode temperature as a vector from freezing (0°C)."""
    temps = {"freezing": 0, "cold": 10, "cool": 20, "tepid": 30,
             "warm": 40, "hot": 60, "boiling": 100}
    val = temps[t.lower()]
    # The vector is just the scalar temperature value
    # Encode in 6 bits (scaled 0-63)
    scaled = min(63, val * 63 // 100)

    domain_id = 1  # temperature
    reality = int_to_6bits(domain_id)
    info = int_to_6bits(scaled)  # the value itself
    activation = int_to_6bits(scaled)  # redundant for robustness
    # Potential: phase (0=solid, 1=liquid, 2=gas)
    phase = 0 if val <= 0 else (2 if val >= 100 else 1)
    potential = int_to_6bits(phase << 4)

    bits = reality + info + activation + potential
    return Concept(name=t, domain="temperature", reference="freezing",
                   vector=[float(val)], bits=bits)


def encode_color_vector(c: str) -> Concept:
    """Encode color as a vector from red (longest wavelength)."""
    colors = {"red": 700, "orange": 620, "yellow": 580, "green": 530,
              "blue": 470, "indigo": 440, "violet": 380}
    val = colors[c.lower()]
    # Vector = offset from red (700nm)
    offset = 700 - val  # positive = shorter wavelength
    scaled = min(63, offset * 63 // 320)

    domain_id = 2  # color
    reality = int_to_6bits(domain_id)
    info = int_to_6bits(scaled)
    # Energy = inversely proportional to wavelength
    energy = min(63, 63 - scaled)
    activation = int_to_6bits(energy)
    # Color class (rainbow order)
    cc = list(colors.keys()).index(c.lower())
    potential = int_to_6bits(cc << 3)

    bits = reality + info + activation + potential
    return Concept(name=c, domain="color", reference="red",
                   vector=[float(offset)], bits=bits)


def encode_size_vector(s: str) -> Concept:
    """Encode size as a vector from tiny (smallest)."""
    sizes = {"tiny": 1, "small": 4, "medium": 10, "big": 15,
             "large": 20, "huge": 40, "giant": 63}
    val = sizes[s.lower()]
    offset = val - 1  # vector from tiny

    domain_id = 3  # size
    reality = int_to_6bits(domain_id)
    info = int_to_6bits(val)
    vol = min(63, val * val * val // 100) if val > 0 else 0
    activation = int_to_6bits(vol)
    scale = 0 if val <= 3 else (1 if val <= 15 else (2 if val <= 35 else 3))
    potential = int_to_6bits(scale << 4 | (val & 0b1111))

    bits = reality + info + activation + potential
    return Concept(name=s, domain="size", reference="tiny",
                   vector=[float(offset)], bits=bits)


# ══════════════════════════════════════════════════════════════════════════════
# VECTOR OPERATIONS (the GLM "speaking")
# ══════════════════════════════════════════════════════════════════════════════

def vector_add(v1: List[float], v2: List[float]) -> List[float]:
    """Vector addition (extend to same length)."""
    n = max(len(v1), len(v2))
    v1_ext = v1 + [0] * (n - len(v1))
    v2_ext = v2 + [0] * (n - len(v2))
    return [a + b for a, b in zip(v1_ext, v2_ext)]

def vector_sub(v1: List[float], v2: List[float]) -> List[float]:
    n = max(len(v1), len(v2))
    v1_ext = v1 + [0] * (n - len(v1))
    v2_ext = v2 + [0] * (n - len(v2))
    return [a - b for a, b in zip(v1_ext, v2_ext)]

def vector_scale(v: List[float], s: float) -> List[float]:
    return [x * s for x in v]

def vector_dot(v1: List[float], v2: List[float]) -> float:
    n = min(len(v1), len(v2))
    return sum(a * b for a, b in zip(v1[:n], v2[:n]))

def vector_mag(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))

def vector_cosine(v1: List[float], v2: List[float]) -> float:
    """Cosine similarity: 1=same direction, -1=opposite, 0=orthogonal."""
    m1, m2 = vector_mag(v1), vector_mag(v2)
    if m1 == 0 or m2 == 0:
        return 0.0
    return vector_dot(v1, v2) / (m1 * m2)


# ══════════════════════════════════════════════════════════════════════════════
# THE GLM SPEAKS: computing relations
# ══════════════════════════════════════════════════════════════════════════════

def compute_relation(c1: Concept, c2: Concept) -> Dict[str, Any]:
    """Compute the relation between two concepts.

    This is the GLM "speaking" — it computes:
    1. Vector addition (composition: c1 + c2 = ?)
    2. Vector subtraction (difference: c1 - c2 = ?)
    3. Cosine similarity (are they same/opposite/orthogonal?)
    4. Hamming distance (bit-level comparison)
    5. Snap tax (how raw is each concept?)
    """
    v1, v2 = c1.vector, c2.vector

    # Vector operations
    addition = vector_add(v1, v2)
    subtraction = vector_sub(v1, v2)
    cosine = vector_cosine(v1, v2)

    # Bit-level
    hamming = sum(1 for a, b in zip(c1.bits, c2.bits) if a != b)

    # Snap
    sw1 = GOLAY_ENGINE.syndrome_weight(c1.bits)
    sw2 = GOLAY_ENGINE.syndrome_weight(c2.bits)

    # Interpret the cosine
    if cosine > 0.5:
        relation = "same direction (allies)"
    elif cosine < -0.5:
        relation = "opposite (antagonists)"
    elif abs(cosine) < 0.5:
        relation = "orthogonal (independent)"
    else:
        relation = "oblique (related but different)"

    return {
        "c1": c1.name, "c2": c2.name,
        "v1": v1, "v2": v2,
        "addition": addition,
        "subtraction": subtraction,
        "cosine": cosine,
        "relation": relation,
        "hamming": hamming,
        "tax_c1": sw1, "tax_c2": sw2,
    }


def find_concept_by_vector(vector: List[float], concepts: Dict[str, Concept],
                            domain: Optional[str] = None) -> Optional[str]:
    """Find the concept whose vector is closest to the given vector."""
    best_name = None
    best_dist = float('inf')
    for name, concept in concepts.items():
        if domain and concept.domain != domain:
            continue
        # Compare vectors
        v = concept.vector
        n = min(len(v), len(vector))
        dist = sum((a - b) ** 2 for a, b in zip(v[:n], vector[:n]))
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70, flush=True)
    print("The Path: Concepts as Relative Vectors", flush=True)
    print("=" * 70, flush=True)
    print()
    print("Per user: 'In relation to my spine (Y origin), this concept is X.'")
    print("The meaning IS the vector from the reference to the concept.")
    print("The GLM speaks by computing vector operations.")
    print()

    # Build all concepts
    concepts = {}
    for d in ["left", "right", "up", "down", "forward", "back", "center"]:
        concepts[d] = encode_direction_vector(d)
    for t in ["freezing", "cold", "cool", "tepid", "warm", "hot", "boiling"]:
        concepts[t] = encode_temperature_vector(t)
    for c in ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]:
        concepts[c] = encode_color_vector(c)
    for s in ["tiny", "small", "medium", "big", "large", "huge", "giant"]:
        concepts[s] = encode_size_vector(s)

    print(f"Built {len(concepts)} concepts as relative vectors.")
    print()

    # Show the concepts
    print("=" * 70)
    print("CONCEPTS (vectors from reference)")
    print("=" * 70)
    for name, concept in concepts.items():
        print(f"  {concept.describe()}")

    # TEST 1: Vector operations on directions
    print()
    print("=" * 70)
    print("TEST 1: DIRECTION VECTOR OPERATIONS")
    print("=" * 70)
    print()

    # left + right = center?
    result = compute_relation(concepts["left"], concepts["right"])
    print(f"left + right = {result['addition']} → {find_concept_by_vector(result['addition'], concepts, 'direction')}")
    print(f"  cosine = {result['cosine']:.2f} → {result['relation']}")

    # up + down = center?
    result = compute_relation(concepts["up"], concepts["down"])
    print(f"up + down = {result['addition']} → {find_concept_by_vector(result['addition'], concepts, 'direction')}")
    print(f"  cosine = {result['cosine']:.2f} → {result['relation']}")

    # left + up = ? (should NOT be center)
    result = compute_relation(concepts["left"], concepts["up"])
    print(f"left + up = {result['addition']} → {find_concept_by_vector(result['addition'], concepts, 'direction')}")
    print(f"  cosine = {result['cosine']:.2f} → {result['relation']}")

    # left - right = ? (should be (-2,0,0))
    result = compute_relation(concepts["left"], concepts["right"])
    print(f"left - right = {result['subtraction']}")

    # TEST 2: Temperature vector operations
    print()
    print("=" * 70)
    print("TEST 2: TEMPERATURE VECTOR OPERATIONS")
    print("=" * 70)
    print()

    # hot - cold = ? (should be 50)
    result = compute_relation(concepts["hot"], concepts["cold"])
    print(f"hot - cold = {result['subtraction']}°C")
    print(f"  cosine = {result['cosine']:.2f} → {result['relation']}")

    # hot + cold = ? (should be 70)
    result = compute_relation(concepts["hot"], concepts["cold"])
    print(f"hot + cold = {result['addition']}°C → closest: {find_concept_by_vector(result['addition'], concepts, 'temperature')}")

    # boiling - freezing = ? (should be 100)
    result = compute_relation(concepts["boiling"], concepts["freezing"])
    print(f"boiling - freezing = {result['subtraction']}°C")

    # hot vs warm (adjacent)
    result = compute_relation(concepts["hot"], concepts["warm"])
    print(f"hot vs warm: cosine = {result['cosine']:.2f} → {result['relation']}")
    print(f"  hot - warm = {result['subtraction']}°C")

    # TEST 3: Color vector operations
    print()
    print("=" * 70)
    print("TEST 3: COLOR VECTOR OPERATIONS")
    print("=" * 70)
    print()

    # red + violet (opposite ends of spectrum)
    result = compute_relation(concepts["red"], concepts["violet"])
    print(f"red vs violet: cosine = {result['cosine']:.2f} → {result['relation']}")

    # red vs orange (adjacent)
    result = compute_relation(concepts["red"], concepts["orange"])
    print(f"red vs orange: cosine = {result['cosine']:.2f} → {result['relation']}")
    print(f"  red - orange = {result['subtraction']}nm offset")

    # TEST 4: The GLM speaks — generate sentences via vector ops
    print()
    print("=" * 70)
    print("TEST 4: THE GLM SPEAKS (vector operations as sentences)")
    print("=" * 70)
    print()

    sentences = [
        ("left", "right", "add", "direction"),
        ("up", "down", "add", "direction"),
        ("forward", "back", "add", "direction"),
        ("left", "up", "add", "direction"),
        ("hot", "cold", "subtract", "temperature"),
        ("boiling", "freezing", "subtract", "temperature"),
        ("hot", "warm", "subtract", "temperature"),
        ("red", "violet", "add", "color"),
        ("tiny", "giant", "subtract", "size"),
    ]

    print(f"{'Operation':<30} {'Result':<25} {'Closest concept':<15} {'Relation':<25}")
    print("-" * 100)

    for c1_name, c2_name, op, domain in sentences:
        c1, c2 = concepts[c1_name], concepts[c2_name]
        rel = compute_relation(c1, c2)

        if op == "add":
            result_vec = rel["addition"]
            op_str = f"{c1_name} + {c2_name}"
        elif op == "subtract":
            result_vec = rel["subtraction"]
            op_str = f"{c1_name} - {c2_name}"

        closest = find_concept_by_vector(result_vec, concepts, domain)
        result_str = str([round(x, 1) for x in result_vec])

        print(f"{op_str:<30} {result_str:<25} {closest or '?':<15} {rel['relation']:<25}")

    # TEST 5: Cosine similarity matrix for directions
    print()
    print("=" * 70)
    print("TEST 5: DIRECTION COSINE SIMILARITY (the relation matrix)")
    print("=" * 70)
    print()

    dirs = ["left", "right", "up", "down", "forward", "back", "center"]
    print(f"{'':>10}", end="")
    for d in dirs:
        print(f"{d[:5]:>8}", end="")
    print()

    for d1 in dirs:
        print(f"{d1:>10}", end="")
        for d2 in dirs:
            cos = vector_cosine(concepts[d1].vector, concepts[d2].vector)
            print(f"{cos:>8.2f}", end="")
        print()

    print()
    print("1.0 = same, -1.0 = opposite, 0.0 = orthogonal")
    print("This matrix IS the physics of direction relations.")

    # Save
    output = {
        "experiment": "The Path: Concepts as Relative Vectors",
        "n_concepts": len(concepts),
        "concepts": {name: {"vector": c.vector, "domain": c.domain, "reference": c.reference}
                     for name, c in concepts.items()},
    }
    out_path = Path('/home/z/my-project/download/arc_agi_17/results/relative_vectors.json')
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n[save] Results saved: {out_path}")


if __name__ == "__main__":
    main()
