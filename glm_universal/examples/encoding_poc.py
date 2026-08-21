#!/usr/bin/env python3
"""Proof-of-concept: elements and words through the Griess algebra.

Tests whether normalized element carriers and meaning-based word carriers
can be reasoned about using the Griess metric, trilinear form, and product.

The directive says: words aren't letters or a name — they are symbols that
mean something.  If it's measurable, we can encode that meaning.

Elements:  normalized measured properties as rational coordinates.
Words:     semantic primitives as rational coordinates.
Both:      exact arithmetic, no floats, no RNG.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── substrate and reasoning ──────────────────────────────────────────────
from glm_universal.substrate import mog, leech2
from glm_universal.reasoning import metric, product, analogy

F = Fraction


# ═════════════════════════════════════════════════════════════════════════
# 1.  NORMALIZED ELEMENT CARRIERS
# ═════════════════════════════════════════════════════════════════════════

# Each element property is normalized to a dimensionless rational in [0, 1]
# by dividing by the maximum value in the register.  This preserves the
# *relative* meaning (hydrogen is lighter than uranium) while putting
# everything on the same scale.

# Load the element data
_DATA_DIR = Path(__file__).resolve().parent / "data_objects" / "_data"
_ELEMENTS_JSON = _DATA_DIR / "elements_118.json"

def _load_elements() -> List[dict]:
    with open(_ELEMENTS_JSON, "r") as f:
        data = json.load(f)
    return data["elements"]

def _as_frac(v) -> Optional[Fraction]:
    """Convert a value to Fraction, returning None for missing."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        if v != v:  # NaN
            return None
        return F(v)
    if isinstance(v, str):
        if v == "" or v == "None":
            return None
        return F(v)
    return F(str(v))

# Properties to use, with their normalization ranges
# Format: (json_key, max_value_for_normalization)
ELEMENT_PROPERTIES = [
    ("atomic_weight_u", F(300)),           # 1 to ~294
    ("electronegativity_pauling", F(4)),   # 0.7 to 3.98
    ("atomic_radius_pm", F(300)),          # 25 to 260 pm
    ("covalent_radius_pm", F(250)),        # 25 to 225 pm
    ("valence_electrons", F(9)),           # 0 to 8
    ("ionization_energy_eV", F(12)),       # 3.9 to 11.8 eV
    ("electron_affinity_eV", F(4)),        # 0 to 3.6 eV
    ("melting_point_K", F(4000)),          # 14 to 3823 K
    ("boiling_point_K", F(5000)),          # 20 to 4404 K
    ("density_g_per_cm3", F(23)),          # 0.00009 to 22.6 g/cm³
]

# The 24-coordinate layout for normalized elements:
#   0-9:   normalized properties (dimensionless rationals in [0,1])
#   10:    z/118 (atomic number, normalized)
#   11:    period/7 (period, normalized)
#   12:    group_block_code/18 (group, normalized)
#   13:    standard_state_code/3 (state, normalized)
#   14-17: Golay address (codeword bits, 0 or 1)
#   18-23: reserved (zeros for now)
ELEMENT_LAYOUT = (
    "weight_norm", "eneg_norm", "radius_norm", "covalent_norm",
    "valence_norm", "ionization_norm", "ea_norm", "mp_norm",
    "bp_norm", "density_norm",
    "z_norm", "period_norm", "group_norm", "state_norm",
    "golay_0", "golay_1", "golay_2", "golay_3",
    "reserved_0", "reserved_1", "reserved_2", "reserved_3",
    "reserved_4", "reserved_5",
)

def encode_element_normalized(record: dict) -> Tuple[str, Tuple[Fraction, ...]]:
    """Encode one element as a normalized 24-coordinate rational carrier.

    Returns (symbol, carrier).
    """
    symbol = record["symbol"]
    carrier = [F(0)] * 24

    # Normalized properties (coords 0-9)
    for i, (key, max_val) in enumerate(ELEMENT_PROPERTIES):
        raw = _as_frac(record.get(key))
        if raw is not None:
            carrier[i] = raw / max_val  # dimensionless, in [0, ~1]

    # Atomic number (coord 10)
    z = _as_frac(record.get("z"))
    if z is not None:
        carrier[10] = z / F(118)

    # Period (coord 11)
    period = _as_frac(record.get("period"))
    if period is not None:
        carrier[11] = period / F(7)

    # Group block code (coord 12)
    carrier[12] = F(record.get("group_block_code", 0)) / F(10)

    # Standard state (coord 13)
    carrier[13] = F(record.get("standard_state_code", 0)) / F(3)

    # Golay address (coords 14-17): use z as a seed for a deterministic codeword
    if z is not None:
        z_int = int(z)
        # Map z to a 12-bit message, encode to Golay codeword
        msg = [(z_int >> k) & 1 for k in range(12)]
        # Use the standard Golay generator
        cw = _golay_encode(msg)
        for i in range(4):
            carrier[14 + i] = F(cw[i])

    return symbol, tuple(carrier)

def _golay_encode(msg12: List[int]) -> List[int]:
    """Standard Golay [24,12,8] encoding."""
    B = [
        [0,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,0,1,1,1,0,0,0,1,0],
        [1,1,0,1,1,1,0,0,0,1,0,1],
        [1,0,1,1,1,0,0,0,1,0,1,1],
        [1,1,1,1,0,0,0,1,0,1,1,0],
        [1,1,1,0,0,0,1,0,1,1,0,1],
        [1,1,0,0,0,1,0,1,1,0,1,1],
        [1,0,0,0,1,0,1,1,0,1,1,1],
        [1,0,0,1,0,1,1,0,1,1,1,0],
        [1,0,1,0,1,1,0,1,1,1,0,0],
        [1,1,0,1,1,0,1,1,1,0,0,0],
        [1,0,1,1,0,1,1,1,0,0,0,1],
    ]
    cw = list(msg12)
    for j in range(12):
        p = 0
        for i in range(12):
            p ^= msg12[i] & B[j][i]
        cw.append(p)
    return cw

def build_element_carriers() -> Dict[str, Tuple[Fraction, ...]]:
    """Build normalized carriers for all 118 elements."""
    records = _load_elements()
    carriers = {}
    for rec in records:
        sym, carrier = encode_element_normalized(rec)
        carriers[sym] = carrier
    return carriers


# ═════════════════════════════════════════════════════════════════════════
# 2.  WORD CARRIERS WITH MEANING
# ═════════════════════════════════════════════════════════════════════════

# Words get meaning through measurable properties:
#   - Syntactic role (part of speech)
#   - Semantic primitives (abstract/concrete, animate/inanimate, etc.)
#   - Relational structure (what it connects to in the CRG)
#   - Physical dimension (if applicable — "energy" has L^2 M T^-2)
#
# The layout puts semantic primitives in coords 0-9, relational structure
# in coords 10-19, and syntactic/physical info in coords 20-23.

# Semantic primitive codes (dimensionless, exact)
SEMANTIC_PRIMITIVES = {
    # (abstract=0..concrete=1, animate=0..inanimate=1, etc.)
    "abstract_concrete": F(1, 2),   # default: 0.5 = neither
    "animate_inanimate": F(1, 2),
    "countable_mass": F(1, 2),
    "temporal_stable": F(1, 2),
    "spatial_local": F(1, 2),
    "causal_passive": F(1, 2),
    "positive_negative": F(1, 2),
    "singular_plural": F(1, 2),
    "active_stative": F(1, 2),
    "definite_indefinite": F(1, 2),
}

# Part of speech codes
POS_CODES = {
    "noun": F(1, 8), "verb": F(2, 8), "adjective": F(3, 8),
    "adverb": F(4, 8), "preposition": F(5, 8), "conjunction": F(6, 8),
    "determiner": F(7, 8), "pronoun": F(1),
}

# Word definitions with semantic content
# Each word is defined by its measurable properties
WORD_DEFINITIONS = {
    # Physics concepts (have physical dimensions)
    "energy": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "temporal_stable": F(3, 4), "causal_passive": F(1, 4),
        "physical_dims": (F(2), F(1), F(-2), F(0), F(0), F(0), F(0),
                          F(0), F(0), F(0)),  # L^2 M T^-2
        "relations": {"converts_to": "power", "measured_in": "joule",
                      "related_to": "force", "form_of": "work"},
    },
    "force": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "temporal_stable": F(1, 2), "causal_passive": F(1, 4),
        "physical_dims": (F(1), F(1), F(-2), F(0), F(0), F(0), F(0),
                          F(0), F(0), F(0)),  # L M T^-2
        "relations": {"causes": "acceleration", "measured_in": "newton",
                      "related_to": "energy", "form_of": "push"},
    },
    "mass": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "temporal_stable": F(1), "causal_passive": F(3, 4),
        "physical_dims": (F(0), F(1), F(0), F(0), F(0), F(0), F(0),
                          F(0), F(0), F(0)),  # M
        "relations": {"measured_in": "kilogram", "related_to": "force",
                      "property_of": "matter"},
    },
    "velocity": {
        "pos": "noun", "abstract_concrete": F(1, 2),
        "temporal_stable": F(1, 4), "causal_passive": F(1, 2),
        "physical_dims": (F(1), F(0), F(-1), F(0), F(0), F(0), F(0),
                          F(0), F(0), F(0)),  # L T^-1
        "relations": {"derivative_of": "position", "related_to": "speed",
                      "measured_in": "meter_per_second"},
    },
    "acceleration": {
        "pos": "noun", "abstract_concrete": F(1, 2),
        "temporal_stable": F(1, 4), "causal_passive": F(1, 2),
        "physical_dims": (F(1), F(0), F(-2), F(0), F(0), F(0), F(0),
                          F(0), F(0), F(0)),  # L T^-2
        "relations": {"derivative_of": "velocity", "related_to": "force",
                      "caused_by": "force"},
    },
    "torque": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "temporal_stable": F(1, 2), "causal_passive": F(1, 4),
        "physical_dims": (F(2), F(1), F(-2), F(0), F(0), F(0), F(0),
                          F(-1), F(0), F(0)),  # L^2 M T^-2 A^-1
        "relations": {"related_to": "force", "measured_in": "newton_meter",
                      "causes": "angular_acceleration"},
    },
    "power": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "temporal_stable": F(1, 2), "causal_passive": F(1, 4),
        "physical_dims": (F(2), F(1), F(-3), F(0), F(0), F(0), F(0),
                          F(0), F(0), F(0)),  # L^2 M T^-3
        "relations": {"derivative_of": "energy", "measured_in": "watt",
                      "related_to": "force"},
    },
    "momentum": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "temporal_stable": F(1, 2), "causal_passive": F(1, 2),
        "physical_dims": (F(1), F(1), F(-1), F(0), F(0), F(0), F(0),
                          F(0), F(0), F(0)),  # L M T^-1
        "relations": {"related_to": "velocity", "conserved_in": "collision",
                      "measured_in": "kilogram_meter_per_second"},
    },

    # Common nouns (no physical dimensions)
    "water": {
        "pos": "noun", "abstract_concrete": F(1),
        "animate_inanimate": F(1), "temporal_stable": F(3, 4),
        "physical_dims": None,
        "relations": {"is_a": "liquid", "contains": "hydrogen",
                      "contains": "oxygen", "essential_for": "life"},
    },
    "electron": {
        "pos": "noun", "abstract_concrete": F(1, 2),
        "animate_inanimate": F(1), "temporal_stable": F(1),
        "physical_dims": None,
        "relations": {"part_of": "atom", "has_property": "charge",
                      "has_property": "mass", "related_to": "electricity"},
    },
    "gravity": {
        "pos": "noun", "abstract_concrete": F(1, 4),
        "animate_inanimate": F(1), "temporal_stable": F(1),
        "physical_dims": None,
        "relations": {"causes": "acceleration", "related_to": "mass",
                      "related_to": "force", "described_by": "general_relativity"},
    },
    "light": {
        "pos": "noun", "abstract_concrete": F(1, 2),
        "animate_inanimate": F(1), "temporal_stable": F(1, 2),
        "physical_dims": None,
        "relations": {"is_a": "electromagnetic_radiation",
                      "has_property": "speed", "related_to": "photon"},
    },
    "heat": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "animate_inanimate": F(1), "temporal_stable": F(1, 4),
        "physical_dims": None,
        "relations": {"related_to": "temperature", "related_to": "energy",
                      "transferred_by": "conduction"},
    },
    "temperature": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "animate_inanimate": F(1), "temporal_stable": F(1, 2),
        "physical_dims": None,
        "relations": {"measured_in": "kelvin", "related_to": "heat",
                      "property_of": "matter"},
    },
    "charge": {
        "pos": "noun", "abstract_concrete": F(3, 4),
        "animate_inanimate": F(1), "temporal_stable": F(1),
        "physical_dims": None,
        "relations": {"property_of": "electron", "related_to": "electricity",
                      "measured_in": "coulomb"},
    },

    # Verbs
    "accelerate": {
        "pos": "verb", "abstract_concrete": F(1, 2),
        "temporal_stable": F(1, 4), "causal_passive": F(1, 4),
        "active_stative": F(1),
        "physical_dims": None,
        "relations": {"causes": "acceleration", "requires": "force"},
    },
    "measure": {
        "pos": "verb", "abstract_concrete": F(1, 2),
        "temporal_stable": F(1, 4), "causal_passive": F(1, 2),
        "active_stative": F(3, 4),
        "physical_dims": None,
        "relations": {"produces": "measurement", "requires": "instrument"},
    },

    # Adjectives
    "heavy": {
        "pos": "adjective", "abstract_concrete": F(3, 4),
        "temporal_stable": F(3, 4),
        "physical_dims": None,
        "relations": {"property_of": "mass", "opposite_of": "light_adj"},
    },
    "fast": {
        "pos": "adjective", "abstract_concrete": F(1, 2),
        "temporal_stable": F(1, 4),
        "physical_dims": None,
        "relations": {"property_of": "velocity", "opposite_of": "slow"},
    },
}

def encode_word(name: str, definition: dict) -> Tuple[str, Tuple[Fraction, ...]]:
    """Encode a word as a 24-coordinate rational carrier.

    Layout (24 coords):
      0: abstract_concrete  (0=abstract, 1=concrete)
      1: animate_inanimate  (0=animate, 1=inanimate)
      2: countable_mass     (0=countable, 1=mass noun)
      3: temporal_stable    (0=ephemeral, 1=permanent)
      4: spatial_local      (0=global, 1=local)
      5: causal_passive     (0=active cause, 1=passive)
      6: positive_negative  (0=negative, 1=positive)
      7: singular_plural    (0=singular, 1=plural)
      8: active_stative     (0=stative, 1=active)
      9: definite_indefinite(0=indefinite, 1=definite)
      10-19: relation slots (count of relations / 10)
      20: pos code (fraction)
      21: number of semantic primitives set / 10
      22: has physical dimensions (1 if yes, 0 if no)
      23: number of relations / 10
    """
    carrier = [F(0)] * 24

    # Semantic primitives (coords 0-9)
    primitive_keys = [
        "abstract_concrete", "animate_inanimate", "countable_mass",
        "temporal_stable", "spatial_local", "causal_passive",
        "positive_negative", "singular_plural", "active_stative",
        "definite_indefinite",
    ]
    n_set = 0
    for i, key in enumerate(primitive_keys):
        if key in definition:
            carrier[i] = definition[key]
            n_set += 1

    # Relation slots (coords 10-19): encode relation count as a density
    relations = definition.get("relations", {})
    n_rels = len(relations)
    for i in range(min(n_rels, 10)):
        carrier[10 + i] = F(1)

    # Part of speech (coord 20)
    carrier[20] = POS_CODES.get(definition.get("pos", ""), F(0))

    # Semantic richness (coord 21)
    carrier[21] = F(n_set, 10)

    # Has physical dimensions (coord 22)
    carrier[22] = F(1) if definition.get("physical_dims") else F(0)

    # Relation count (coord 23)
    carrier[23] = F(n_rels, 10)

    return name, tuple(carrier)


def build_word_carriers() -> Dict[str, Tuple[Fraction, ...]]:
    """Build carriers for all defined words."""
    carriers = {}
    for name, defn in WORD_DEFINITIONS.items():
        n, c = encode_word(name, defn)
        carriers[n] = c
    return carriers


# ═════════════════════════════════════════════════════════════════════════
# 3.  TESTING
# ═════════════════════════════════════════════════════════════════════════

def test_elements():
    """Test element carriers through the Griess metric."""
    print("=" * 70)
    print("ELEMENT CARRIERS — Normalized Measured Properties")
    print("=" * 70)

    carriers = build_element_carriers()
    print(f"\nLoaded {len(carriers)} element carriers")

    # Show a few carriers
    for sym in ['H', 'C', 'O', 'Fe', 'Au']:
        c = carriers[sym]
        nonzero = [(i, v) for i, v in enumerate(c) if v != 0]
        print(f"\n{sym}: {len(nonzero)} nonzero coords")
        for i, v in nonzero[:8]:
            print(f"  coord {i:2d} = {v}")

    # Distances between related elements
    print("\n--- Distances (related elements should be close) ---")
    groups = [
        ("Alkali metals", ["Li", "Na", "K", "Rb"]),
        ("Noble gases", ["He", "Ne", "Ar", "Kr"]),
        ("Halogens", ["F", "Cl", "Br", "I"]),
        ("Carbon group", ["C", "Si", "Ge", "Sn"]),
        ("Transition metals", ["Fe", "Co", "Ni", "Cu"]),
    ]
    for group_name, syms in groups:
        print(f"\n  {group_name}:")
        for i, s1 in enumerate(syms):
            for s2 in syms[i+1:]:
                if s1 in carriers and s2 in carriers:
                    d2 = metric.distance2(carriers[s1], carriers[s2])
                    print(f"    d^2({s1:2s}, {s2:2s}) = {d2}")

    # Cross-group distances
    print("\n--- Cross-group distances ---")
    cross = [("H", "He"), ("C", "N"), ("Fe", "Au"), ("Li", "F")]
    for s1, s2 in cross:
        if s1 in carriers and s2 in carriers:
            d2 = metric.distance2(carriers[s1], carriers[s2])
            print(f"  d^2({s1:2s}, {s2:2s}) = {d2}")

    # Lattice projection
    print("\n--- Lattice projection ---")
    for sym in ['H', 'C', 'O', 'Fe', 'Au', 'U']:
        c = carriers[sym]
        lp = analogy.nearest_lattice_point(c)
        print(f"  {sym:2s}: d2={lp.distance2}, norm2={lp.norm2}, "
              f"is_2a={lp.is_2a_axis}")

    return carriers


def test_words():
    """Test word carriers through the Griess metric."""
    print("\n" + "=" * 70)
    print("WORD CARRIERS — Semantic Primitives")
    print("=" * 70)

    carriers = build_word_carriers()
    print(f"\nLoaded {len(carriers)} word carriers")

    # Show a few carriers
    for name in ['energy', 'force', 'water', 'electron', 'heavy']:
        c = carriers[name]
        nonzero = [(i, v) for i, v in enumerate(c) if v != 0]
        print(f"\n{name}: {len(nonzero)} nonzero coords")
        for i, v in nonzero[:8]:
            print(f"  coord {i:2d} = {v}")

    # Physics word distances
    print("\n--- Physics word distances ---")
    physics_words = ['energy', 'force', 'mass', 'velocity', 'acceleration',
                     'torque', 'power', 'momentum']
    for i, w1 in enumerate(physics_words):
        for w2 in physics_words[i+1:]:
            if w1 in carriers and w2 in carriers:
                d2 = metric.distance2(carriers[w1], carriers[w2])
                print(f"  d^2({w1:12s}, {w2:12s}) = {d2}")

    # Cross-domain distances
    print("\n--- Cross-domain distances ---")
    cross = [("energy", "heavy"), ("force", "fast"), ("water", "electron"),
             ("gravity", "light"), ("heat", "temperature")]
    for w1, w2 in cross:
        if w1 in carriers and w2 in carriers:
            d2 = metric.distance2(carriers[w1], carriers[w2])
            print(f"  d^2({w1:12s}, {w2:12s}) = {d2}")

    # Lattice projection
    print("\n--- Lattice projection ---")
    for name in ['energy', 'force', 'water', 'electron', 'heavy']:
        c = carriers[name]
        lp = analogy.nearest_lattice_point(c)
        print(f"  {name:12s}: d2={lp.distance2}, norm2={lp.norm2}, "
              f"is_2a={lp.is_2a_axis}")

    return carriers


def test_cross_domain(element_carriers, word_carriers):
    """Test cross-domain reasoning: can the system relate elements to words?"""
    print("\n" + "=" * 70)
    print("CROSS-DOMAIN REASONING — Elements ↔ Words")
    print("=" * 70)

    # Can we find the element closest to a physics concept?
    print("\n--- Element nearest to physics word 'mass' ---")
    if 'mass' in word_carriers:
        mass_c = word_carriers['mass']
        # Compare mass carrier to all element carriers
        # (using only the first 10 coords since that's where the meaning is)
        ranked = []
        for sym, ec in element_carriers.items():
            # Pad element carrier to 24 coords (it already is 24)
            d2 = metric.distance2(mass_c, ec)
            ranked.append((sym, d2))
        ranked.sort(key=lambda x: x[1])
        print("  Top 5 nearest elements to 'mass':")
        for sym, d2 in ranked[:5]:
            print(f"    {sym:3s}: d^2 = {d2}")

    # Can we find the word closest to an element?
    print("\n--- Word nearest to element 'Fe' (iron) ---")
    if 'Fe' in element_carriers:
        fe_c = element_carriers['Fe']
        ranked = []
        for name, wc in word_carriers.items():
            d2 = metric.distance2(fe_c, wc)
            ranked.append((name, d2))
        ranked.sort(key=lambda x: x[1])
        print("  Top 5 nearest words to iron:")
        for name, d2 in ranked[:5]:
            print(f"    {name:15s}: d^2 = {d2}")


def main():
    print("GLM Universal — Element & Word Encoding Proof of Concept")
    print("All values are exact fractions. No floats. No RNG.\n")

    element_carriers = test_elements()
    word_carriers = test_words()
    test_cross_domain(element_carriers, word_carriers)

    print("\n" + "=" * 70)
    print("DONE — All distances computed with exact Fraction arithmetic.")
    print("=" * 70)


if __name__ == "__main__":
    main()
