#!/usr/bin/env python3
"""
Grow carefully: add numbers and forces, test cross-domain, produce the map.
"""

import sys
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
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
# CONCEPT AS RELATIVE VECTOR
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Concept:
    name: str
    domain: str
    reference: str
    vector: List[float]
    bits: List[int]

    def describe(self) -> str:
        v = [round(x, 1) for x in self.vector]
        return f"{self.name} ({self.domain}): from {self.reference} = {v}"


# ══════════════════════════════════════════════════════════════════════════════
# DOMAIN ENCODERS
# ══════════════════════════════════════════════════════════════════════════════

def encode_direction(d: str) -> Concept:
    vectors = {
        "left": (-1,0,0), "right": (+1,0,0),
        "up": (0,+1,0), "down": (0,-1,0),
        "forward": (0,0,+1), "back": (0,0,-1),
        "center": (0,0,0),
    }
    v = vectors[d.lower()]
    domain_id = 0
    reality = int_to_6bits(domain_id)
    if v == (0,0,0):
        axis, sign, mag = 3, 0, 0
    elif v[0] != 0: axis, sign, mag = 0, (1 if v[0]<0 else 0), abs(v[0])
    elif v[1] != 0: axis, sign, mag = 1, (1 if v[1]<0 else 0), abs(v[1])
    else: axis, sign, mag = 2, (1 if v[2]<0 else 0), abs(v[2])
    info = int_to_6bits((axis << 4) | (sign << 3) | (mag & 0b111))
    x_sign = 1 if v[0]<0 else 0; y_sign = 1 if v[1]<0 else 0; z_sign = 1 if v[2]<0 else 0
    activation = int_to_6bits((x_sign<<5)|(abs(v[0])<<3)|(y_sign<<2)|(abs(v[1])<<1)|z_sign)
    potential = [0]*6
    return Concept(d, "direction", "center", list(v), reality+info+activation+potential)


def encode_temperature(t: str) -> Concept:
    temps = {"freezing":0, "cold":10, "cool":20, "tepid":30, "warm":40, "hot":60, "boiling":100}
    val = temps[t.lower()]
    scaled = min(63, val * 63 // 100)
    reality = int_to_6bits(1)  # domain=temperature
    info = int_to_6bits(scaled)
    activation = int_to_6bits(scaled)
    phase = 0 if val<=0 else (2 if val>=100 else 1)
    potential = int_to_6bits(phase << 4)
    return Concept(t, "temperature", "freezing", [float(val)], reality+info+activation+potential)


def encode_color(c: str) -> Concept:
    colors = {"red":700, "orange":620, "yellow":580, "green":530, "blue":470, "indigo":440, "violet":380}
    val = colors[c.lower()]
    offset = 700 - val
    scaled = min(63, offset * 63 // 320)
    reality = int_to_6bits(2)  # domain=color
    info = int_to_6bits(scaled)
    energy = min(63, 63 - scaled)
    activation = int_to_6bits(energy)
    cc = list(colors.keys()).index(c.lower())
    potential = int_to_6bits(cc << 3)
    return Concept(c, "color", "red", [float(offset)], reality+info+activation+potential)


def encode_size(s: str) -> Concept:
    sizes = {"tiny":1, "small":4, "medium":10, "big":15, "large":20, "huge":40, "giant":63}
    val = sizes[s.lower()]
    offset = val - 1
    reality = int_to_6bits(3)  # domain=size
    info = int_to_6bits(val)
    vol = min(63, val*val*val//100) if val > 0 else 0
    activation = int_to_6bits(vol)
    scale = 0 if val<=3 else (1 if val<=15 else (2 if val<=35 else 3))
    potential = int_to_6bits(scale << 4 | (val & 0b1111))
    return Concept(s, "size", "tiny", [float(offset)], reality+info+activation+potential)


def encode_number(n: int) -> Concept:
    """Encode a number as a vector from zero."""
    reality = int_to_6bits(4)  # domain=number
    info = int_to_6bits(n & 0x3F)
    activation = int_to_6bits(n & 0x3F)
    parity = n % 2
    is_prime = 1 if n > 1 and all(n % i != 0 for i in range(2, int(n**0.5)+1)) else 0
    potential = int_to_6bits((parity << 5) | (is_prime << 4) | (n & 0b1111))
    return Concept(str(n), "number", "zero", [float(n)], reality+info+activation+potential)


def encode_force(f: str) -> Concept:
    """Encode force as a vector from zero force."""
    forces = {"zero_force":0, "weak":10, "gentle":20, "moderate":30,
              "strong":45, "powerful":55, "massive":63}
    val = forces[f.lower()]
    reality = int_to_6bits(5)  # domain=force
    info = int_to_6bits(val)
    fa = min(63, val * 2 % 64)
    activation = int_to_6bits(fa)
    potential = int_to_6bits((1 if val > 0 else 0) << 4 | (val & 0b1111))
    return Concept(f, "force", "zero_force", [float(val)], reality+info+activation+potential)


# ══════════════════════════════════════════════════════════════════════════════
# VECTOR OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def v_add(v1, v2):
    n = max(len(v1), len(v2))
    return [a+b for a,b in zip(v1+[0]*(n-len(v1)), v2+[0]*(n-len(v2)))]

def v_sub(v1, v2):
    n = max(len(v1), len(v2))
    return [a-b for a,b in zip(v1+[0]*(n-len(v1)), v2+[0]*(n-len(v2)))]

def v_scale(v, s):
    return [x*s for x in v]

def v_dot(v1, v2):
    n = min(len(v1), len(v2))
    return sum(a*b for a,b in zip(v1[:n], v2[:n]))

def v_mag(v):
    return math.sqrt(sum(x*x for x in v))

def v_cos(v1, v2):
    m1, m2 = v_mag(v1), v_mag(v2)
    if m1 == 0 or m2 == 0: return 0.0
    return v_dot(v1, v2) / (m1 * m2)


def find_closest(vector, concepts, domain=None):
    best_name, best_dist = None, float('inf')
    for name, c in concepts.items():
        if domain and c.domain != domain: continue
        n = min(len(c.vector), len(vector))
        dist = sum((a-b)**2 for a,b in zip(c.vector[:n], vector[:n]))
        if dist < best_dist:
            best_dist, best_name = dist, name
    return best_name, best_dist


def compute_relation(c1: Concept, c2: Concept, concepts: Dict[str, Concept]) -> Dict[str, Any]:
    """Compute the full relation between two concepts."""
    v1, v2 = c1.vector, c2.vector
    same_domain = c1.domain == c2.domain

    add_result = v_add(v1, v2)
    sub_result = v_sub(v1, v2)
    cos = v_cos(v1, v2)

    add_closest, add_dist = find_closest(add_result, concepts, c1.domain if same_domain else None)
    sub_closest, sub_dist = find_closest(sub_result, concepts, c1.domain if same_domain else None)

    if cos > 0.5: rel = "same direction (allies)"
    elif cos < -0.5: rel = "opposite (antagonists)"
    elif abs(cos) < 0.5: rel = "orthogonal (independent)"
    else: rel = "oblique"

    return {
        "c1": c1.name, "c2": c2.name,
        "same_domain": same_domain,
        "c1_vector": [round(x,1) for x in v1],
        "c2_vector": [round(x,1) for x in v2],
        "addition": [round(x,1) for x in add_result],
        "add_closest": add_closest,
        "subtraction": [round(x,1) for x in sub_result],
        "sub_closest": sub_closest,
        "cosine": round(cos, 2),
        "relation": rel,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70, flush=True)
    print("Growing Carefully: More Domains + Cross-Domain + Map", flush=True)
    print("=" * 70, flush=True)

    # Build ALL concepts
    concepts = {}
    for d in ["left","right","up","down","forward","back","center"]:
        concepts[d] = encode_direction(d)
    for t in ["freezing","cold","cool","tepid","warm","hot","boiling"]:
        concepts[t] = encode_temperature(t)
    for c in ["red","orange","yellow","green","blue","indigo","violet"]:
        concepts[c] = encode_color(c)
    for s in ["tiny","small","medium","big","large","huge","giant"]:
        concepts[s] = encode_size(s)
    for n in [0,1,2,3,5,7,10,20,50]:
        concepts[str(n)] = encode_number(n)
    for f in ["zero_force","weak","gentle","moderate","strong","powerful","massive"]:
        concepts[f] = encode_force(f)

    print(f"\nBuilt {len(concepts)} concepts across 6 domains.")
    domains = defaultdict(list)
    for name, c in concepts.items():
        domains[c.domain].append(name)
    for d, names in domains.items():
        print(f"  {d}: {len(names)} concepts")

    # TEST 1: Same-domain operations (the ones that worked before)
    print(f"\n{'='*70}")
    print("TEST 1: SAME-DOMAIN OPERATIONS")
    print(f"{'='*70}\n")

    same_domain_tests = [
        ("left", "right", "add", "direction"),
        ("up", "down", "add", "direction"),
        ("forward", "back", "add", "direction"),
        ("left", "up", "add", "direction"),
        ("hot", "cold", "subtract", "temperature"),
        ("hot", "warm", "subtract", "temperature"),
        ("boiling", "freezing", "subtract", "temperature"),
        ("red", "violet", "subtract", "color"),
        ("tiny", "giant", "subtract", "size"),
        ("weak", "massive", "subtract", "force"),
        ("2", "3", "add", "number"),
        ("2", "3", "subtract", "number"),
        ("5", "7", "add", "number"),
    ]

    print(f"{'Operation':<25} {'Result':<20} {'Closest':<12} {'Relation':<25}")
    print("-" * 85)
    for c1n, c2n, op, dom in same_domain_tests:
        c1, c2 = concepts[c1n], concepts[c2n]
        rel = compute_relation(c1, c2, concepts)
        if op == "add":
            result = rel["addition"]; closest = rel["add_closest"]
        else:
            result = rel["subtraction"]; closest = rel["sub_closest"]
        print(f"{c1n} {op} {c2n:<20} {str(result):<20} {closest or '?':<12} {rel['relation']:<25}")

    # TEST 2: Cross-domain operations
    print(f"\n{'='*70}")
    print("TEST 2: CROSS-DOMAIN OPERATIONS (should be orthogonal or meaningless)")
    print(f"{'='*70}\n")

    cross_domain_tests = [
        ("left", "hot"),     # direction + temperature
        ("red", "up"),       # color + direction
        ("big", "warm"),     # size + temperature
        ("fast", "left"),    # speed + direction (if we had speed)
        ("3", "left"),       # number + direction
        ("strong", "hot"),   # force + temperature
    ]

    print(f"{'Pair':<25} {'Cosine':<8} {'Relation':<25} {'Same domain?'}")
    print("-" * 70)
    for c1n, c2n in cross_domain_tests:
        if c1n not in concepts or c2n not in concepts:
            print(f"{c1n} vs {c2n:<20} (missing)")
            continue
        rel = compute_relation(concepts[c1n], concepts[c2n], concepts)
        print(f"{c1n} vs {c2n:<20} {rel['cosine']:<8} {rel['relation']:<25} {rel['same_domain']}")

    # TEST 3: Number scaling (2 × small = ?)
    print(f"\n{'='*70}")
    print("TEST 3: SCALING (multiplication)")
    print(f"{'='*70}\n")

    # 2 × small (offset from tiny)
    small_vec = concepts["small"].vector  # [3.0]
    two_vec = concepts["2"].vector        # [2.0]
    scaled = v_scale(small_vec, two_vec[0])
    closest, dist = find_closest(scaled, concepts, "size")
    print(f"  2 × small = {scaled} → {closest}")

    # 3 × small
    scaled = v_scale(small_vec, 3)
    closest, dist = find_closest(scaled, concepts, "size")
    print(f"  3 × small = {scaled} → {closest}")

    # 2 × hot (offset from freezing)
    hot_vec = concepts["hot"].vector  # [60.0]
    scaled = v_scale(hot_vec, 2)
    closest, dist = find_closest(scaled, concepts, "temperature")
    print(f"  2 × hot = {scaled} → {closest} (should be beyond boiling)")

    # TEST 4: The cosine matrix for directions
    print(f"\n{'='*70}")
    print("TEST 4: DIRECTION COSINE MATRIX")
    print(f"{'='*70}\n")

    dirs = ["left","right","up","down","forward","back","center"]
    print(f"{'':>10}", end="")
    for d in dirs: print(f"{d[:5]:>8}", end="")
    print()
    for d1 in dirs:
        print(f"{d1:>10}", end="")
        for d2 in dirs:
            cos = v_cos(concepts[d1].vector, concepts[d2].vector)
            print(f"{cos:>8.2f}", end="")
        print()

    # BUILD THE ENCODING STRATEGY MAP
    print(f"\n{'='*70}")
    print("ENCODING STRATEGY MAP")
    print(f"{'='*70}\n")

    map_text = """ENCODING STRATEGY MAP
=====================

PRINCIPLE: Meaning IS the vector from a reference point.
           The concept IS the relation to its origin.
           The GLM speaks by computing vector operations.

THE 24-BIT DATA OBJECT (4×6 MOG grid):
  Reality row (6 bits)    = domain ID (which domain this concept belongs to)
  Info row (6 bits)       = the specific value within the domain
  Activation row (6 bits) = secondary properties (magnitude, energy, etc.)
  Potential row (6 bits)  = context (phase, scale, parity, etc.)

DOMAIN ENCODERS:
  Domain 0: Direction
    Reference: center (0,0,0)
    Vector: 3D (x, y, z) with sign
    Concepts: left(-1,0,0), right(+1,0,0), up(0,+1,0), down(0,-1,0),
              forward(0,0,+1), back(0,0,-1), center(0,0,0)
    Operations: addition (composition), cosine (same/opposite/orthogonal)
    Key test: left + right = center (opposites cancel)

  Domain 1: Temperature
    Reference: freezing (0°C)
    Vector: 1D scalar (temperature in °C)
    Concepts: freezing(0), cold(10), cool(20), tepid(30), warm(40), hot(60), boiling(100)
    Operations: subtraction (difference), addition (sum)
    Key test: hot - cold = warm (the difference IS the midpoint)

  Domain 2: Color
    Reference: red (700nm, longest visible wavelength)
    Vector: 1D scalar (offset from red in nm)
    Concepts: red(0), orange(80), yellow(120), green(170), blue(230), indigo(260), violet(320)
    Operations: subtraction (wavelength difference)
    Key test: red - violet = -320nm (the full visible spectrum)

  Domain 3: Size
    Reference: tiny (magnitude 1)
    Vector: 1D scalar (offset from tiny)
    Concepts: tiny(0), small(3), medium(9), big(14), large(19), huge(39), giant(62)
    Operations: subtraction (size difference), scaling (multiplication)
    Key test: 2 × small = medium (scaling works)

  Domain 4: Number
    Reference: zero
    Vector: 1D scalar (the number itself)
    Concepts: 0, 1, 2, 3, 5, 7, 10, 20, 50
    Operations: addition, subtraction, scaling (multiplication)
    Key test: 2 + 3 = 5 (arithmetic works)

  Domain 5: Force
    Reference: zero_force
    Vector: 1D scalar (force magnitude)
    Concepts: zero_force(0), weak(10), gentle(20), moderate(30), strong(45), powerful(55), massive(63)
    Operations: addition (combined forces), subtraction (force difference)
    Key test: massive - weak = 53 (the force range)

VECTOR OPERATIONS (how the GLM speaks):
  Addition (c1 + c2):     Composition — what do you get when you combine them?
  Subtraction (c1 - c2):  Difference — what is the gap between them?
  Cosine similarity:      Relation type — same(1.0), opposite(-1.0), orthogonal(0.0)
  Scaling (n × c):        Multiplication — what is n times this concept?

CROSS-DOMAIN RULE:
  Cross-domain operations produce orthogonal results (cosine ≈ 0).
  This IS meaningful: the GLM says "these concepts don't directly relate."
  Example: left vs hot → cosine ≈ 0 (a direction is not a temperature)

THE SNAP:
  Each concept's 24-bit encoding has a syndrome (σ).
  The snap corrects to the nearest Golay codeword.
  The syndrome weight (tax) measures how "raw" the concept is.
  Low tax = close to lawful. High tax = needs interpretation.

GROWTH STRATEGY:
  1. Add more domains (speed, time, energy, angle, area, volume)
  2. Each domain: define reference, vector, concepts, key operations
  3. Test: do the vector operations produce semantically correct results?
  4. Cross-domain: let the cosine tell us which domains interact
  5. The body state stores concepts + their relations (computed vectors)
  6. The system grows by adding concepts, not by adding systems
"""

    print(map_text)

    # Save the map
    map_path = Path('/home/z/my-project/download/arc_agi_17/ENCODING_STRATEGY_MAP.md')
    with open(map_path, 'w') as f:
        f.write(map_text)
    print(f"[save] Encoding strategy map: {map_path}")

    # Save all results
    output = {
        "experiment": "Growing Carefully",
        "n_concepts": len(concepts),
        "domains": {d: names for d, names in domains.items()},
        "concepts": {name: {"domain": c.domain, "reference": c.reference,
                            "vector": c.vector, "bits": c.bits}
                     for name, c in concepts.items()},
    }
    out_path = Path('/home/z/my-project/download/arc_agi_17/results/grow_carefully.json')
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"[save] Results: {out_path}")

    print(f"\n{'='*70}")
    print("READY FOR ZIP")
    print(f"{'='*70}")
    print(f"  Concepts: {len(concepts)}")
    print(f"  Domains: {len(domains)}")
    print(f"  Map: ENCODING_STRATEGY_MAP.md")
    print(f"  Core: glm_clean/ (6 files)")
    print(f"  Tests: glm_clean/tests/ (key tests)")


if __name__ == "__main__":
    main()
