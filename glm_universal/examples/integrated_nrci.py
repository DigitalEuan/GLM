#!/usr/bin/env python3
"""Integrated test: NRCI coherence + Griess distance on all three domains.

Tests the "both perspectives" approach:
- Griess metric measures DISTANCE between carriers.
- NRCI measures COHERENCE — how structured each carrier is.
- Together they give a complete picture: stability + proximity.

Elements: normalized measured properties.
Words: semantic primitives.
Physics: dimensional exponents.

All values are exact: the carriers are rationals, and so is the NRCI --
its square roots are taken at the declared resolution of
``coherence.rational_sqrt`` rather than in floating point.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple

from glm_universal.reasoning import metric, product, analogy, coherence

F = Fraction


# ═════════════════════════════════════════════════════════════════════════
# 1.  LOAD PHYSICS (already in glm_universal)
# ═════════════════════════════════════════════════════════════════════════

def load_physics() -> Dict[str, Tuple[Fraction, ...]]:
    from glm_universal.data_objects import physics as DP
    return {o.name: o.carrier for o in DP.physics_objects()}


# ═════════════════════════════════════════════════════════════════════════
# 2.  NORMALIZED ELEMENT CARRIERS
# ═════════════════════════════════════════════════════════════════════════

#: The packaged data lives beside ``data_objects``, one level up from the
#: examples directory -- resolve it from the package, not from this file's
#: own directory, so the example runs from anywhere.
_DATA_DIR = (Path(__file__).resolve().parent.parent
             / "data_objects" / "_data")

def _load_elements() -> List[dict]:
    with open(_DATA_DIR / "elements_118.json") as f:
        return json.load(f)["elements"]

def _as_frac(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return None if v != v else F(v)
    if isinstance(v, str):
        if v in ("", "None"):
            return None
        return F(v)
    return F(str(v))

ELEMENT_PROPS = [
    ("atomic_weight_u", F(300)), ("electronegativity_pauling", F(4)),
    ("atomic_radius_pm", F(300)), ("covalent_radius_pm", F(250)),
    ("valence_electrons", F(9)), ("ionization_energy_eV", F(12)),
    ("electron_affinity_eV", F(4)), ("melting_point_K", F(4000)),
    ("boiling_point_K", F(5000)), ("density_g_per_cm3", F(23)),
]

def _golay_encode(msg12):
    B = [
        [0,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,0,1,1,1,0,0,0,1,0],
        [1,1,0,1,1,1,0,0,0,1,0,1],[1,0,1,1,1,0,0,0,1,0,1,1],
        [1,1,1,1,0,0,0,1,0,1,1,0],[1,1,1,0,0,0,1,0,1,1,0,1],
        [1,1,0,0,0,1,0,1,1,0,1,1],[1,0,0,0,1,0,1,1,0,1,1,1],
        [1,0,0,1,0,1,1,0,1,1,1,0],[1,0,1,0,1,1,0,1,1,1,0,0],
        [1,1,0,1,1,0,1,1,1,0,0,0],[1,0,1,1,0,1,1,1,0,0,0,1],
    ]
    cw = list(msg12)
    for j in range(12):
        p = 0
        for i in range(12):
            p ^= msg12[i] & B[j][i]
        cw.append(p)
    return cw

def encode_element(rec):
    sym = rec["symbol"]
    c = [F(0)] * 24
    for i, (key, mx) in enumerate(ELEMENT_PROPS):
        raw = _as_frac(rec.get(key))
        if raw is not None:
            c[i] = raw / mx
    z = _as_frac(rec.get("z"))
    if z is not None:
        c[10] = z / F(118)
        msg = [(int(z) >> k) & 1 for k in range(12)]
        cw = _golay_encode(msg)
        for j in range(4):
            c[14 + j] = F(cw[j])
    period = _as_frac(rec.get("period"))
    if period is not None:
        c[11] = period / F(7)
    c[12] = F(rec.get("group_block_code", 0)) / F(10)
    c[13] = F(rec.get("standard_state_code", 0)) / F(3)
    return sym, tuple(c)

def build_elements():
    return {sym: c for sym, c in (encode_element(r) for r in _load_elements())}


# ═════════════════════════════════════════════════════════════════════════
# 3.  WORD CARRIERS (semantic primitives)
# ═════════════════════════════════════════════════════════════════════════

POS = {"noun": F(1,8), "verb": F(2,8), "adjective": F(3,8), "adverb": F(4,8)}

WORDS = {
    "energy":      {"a":F(3,4),"i":F(1,4),"t":F(3,4),"c":F(1,4),"p":"noun","r":4,"d":1},
    "force":       {"a":F(3,4),"i":F(1,4),"t":F(1,2),"c":F(1,4),"p":"noun","r":4,"d":1},
    "mass":        {"a":F(3,4),"i":F(1,4),"t":1,  "c":F(3,4),"p":"noun","r":3,"d":1},
    "velocity":    {"a":F(1,2),"i":F(1,4),"t":F(1,4),"c":F(1,2),"p":"noun","r":3,"d":1},
    "acceleration":{"a":F(1,2),"i":F(1,4),"t":F(1,4),"c":F(1,2),"p":"noun","r":3,"d":1},
    "torque":      {"a":F(3,4),"i":F(1,4),"t":F(1,2),"c":F(1,4),"p":"noun","r":3,"d":1},
    "power":       {"a":F(3,4),"i":F(1,4),"t":F(1,2),"c":F(1,4),"p":"noun","r":3,"d":1},
    "momentum":    {"a":F(3,4),"i":F(1,4),"t":F(1,2),"c":F(1,2),"p":"noun","r":3,"d":1},
    "water":       {"a":1,  "i":1,  "t":F(3,4),"c":1,  "p":"noun","r":4,"d":0},
    "electron":    {"a":F(1,2),"i":1,  "t":1,  "c":F(1,2),"p":"noun","r":4,"d":0},
    "gravity":     {"a":F(1,4),"i":1,  "t":1,  "c":F(1,4),"p":"noun","r":4,"d":0},
    "light":       {"a":F(1,2),"i":1,  "t":F(1,2),"c":F(1,2),"p":"noun","r":3,"d":0},
    "heat":        {"a":F(3,4),"i":1,  "t":F(1,4),"c":F(3,4),"p":"noun","r":3,"d":0},
    "temperature": {"a":F(3,4),"i":1,  "t":F(1,2),"c":F(3,4),"p":"noun","r":3,"d":0},
    "charge":      {"a":F(3,4),"i":1,  "t":1,  "c":F(3,4),"p":"noun","r":3,"d":0},
    "heavy":       {"a":F(3,4),"i":1,  "t":F(3,4),"c":1,  "p":"adjective","r":2,"d":0},
    "fast":        {"a":F(1,2),"i":1,  "t":F(1,4),"c":F(1,2),"p":"adjective","r":2,"d":0},
    "accelerate":  {"a":F(1,2),"i":1,  "t":F(1,4),"c":F(1,4),"p":"verb","r":2,"d":0},
    "measure":     {"a":F(1,2),"i":1,  "t":F(1,4),"c":F(1,2),"p":"verb","r":2,"d":0},
}

def encode_word(name, d):
    c = [F(0)] * 24
    # Semantic primitives (coords 0-3): abstract, inanimate, temporal, concrete
    c[0] = F(d["a"])
    c[1] = F(d["i"])
    c[2] = F(d["t"])
    c[3] = F(d["c"])
    # Part of speech (coord 4)
    c[4] = POS.get(d["p"], F(0))
    # Relation density (coord 5)
    c[5] = F(d["r"], 10)
    # Has physical dimensions (coord 6)
    c[6] = F(d["d"])
    return name, tuple(c)

def build_words():
    return {n: encode_word(n, d)[1] for n, d in WORDS.items()}


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE INTEGRATED TEST
# ═════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("INTEGRATED TEST: NRCI Coherence + Griess Distance")
    print("=" * 72)
    print(f"\nY = {coherence.Y_DECIMAL}")
    print(f"Q = Y + 1/8 = {coherence.decimal_str(coherence.Q, 10)}")
    print(f"B = {coherence.decimal_str(coherence.B, 4)}")

    # Load all three domains
    physics = load_physics()
    elements = build_elements()
    words = build_words()

    print(f"\nPhysics:  {len(physics)} carriers")
    print(f"Elements: {len(elements)} carriers")
    print(f"Words:    {len(words)} carriers")

    # ── Physics ────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("PHYSICS — NRCI + Griess Distance")
    print("=" * 72)

    test_physics = ['energy', 'torque', 'force', 'power', 'momentum',
                    'velocity', 'acceleration', 'mass']

    print("\n--- NRCI (coherence of each carrier) ---")
    for name in test_physics:
        if name in physics:
            bd = coherence.nrci_breakdown(physics[name])
            print(f"  {name:15s}: NRCI={coherence.decimal_str(bd['nrci'], 4)} ({bd['regime']:12s}) "
                  f"tax0={bd['shell0_golay']}")

    print("\n--- Griess distances (selected pairs) ---")
    pairs = [('energy','torque'), ('force','momentum'), ('velocity','acceleration'),
             ('energy','force'), ('force','velocity')]
    for n1, n2 in pairs:
        d2 = metric.distance2(physics[n1], physics[n2])
        print(f"  d^2({n1:12s}, {n2:12s}) = {d2}")

    # ── Elements ───────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("ELEMENTS — NRCI + Griess Distance")
    print("=" * 72)

    test_elems = ['H', 'C', 'O', 'Fe', 'Au', 'He', 'Ne', 'Li', 'Na', 'F', 'Cl']

    print("\n--- NRCI (coherence of each carrier) ---")
    for sym in test_elems:
        if sym in elements:
            bd = coherence.nrci_breakdown(elements[sym])
            print(f"  {sym:3s}: NRCI={coherence.decimal_str(bd['nrci'], 4)} ({bd['regime']:12s}) "
                  f"tax0={bd['shell0_golay']}")

    print("\n--- Griess distances (within groups) ---")
    groups = [("Alkali", ["Li","Na","K"]), ("Noble", ["He","Ne","Ar"]),
              ("Halogens", ["F","Cl","Br"]), ("Carbon group", ["C","Si","Ge"])]
    for gname, syms in groups:
        for i, s1 in enumerate(syms):
            for s2 in syms[i+1:]:
                if s1 in elements and s2 in elements:
                    d2 = metric.distance2(elements[s1], elements[s2])
                    print(f"  d^2({s1:2s}, {s2:2s}) = {d2}  [{gname}]")

    # ── Words ──────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("WORDS — NRCI + Griess Distance")
    print("=" * 72)

    test_words = ['energy', 'force', 'mass', 'velocity', 'acceleration',
                  'torque', 'power', 'momentum', 'water', 'electron',
                  'gravity', 'light', 'heat', 'temperature', 'charge',
                  'heavy', 'fast']

    print("\n--- NRCI (coherence of each carrier) ---")
    for name in test_words:
        if name in words:
            bd = coherence.nrci_breakdown(words[name])
            print(f"  {name:15s}: NRCI={coherence.decimal_str(bd['nrci'], 4)} ({bd['regime']:12s})")

    print("\n--- Griess distances (physics words) ---")
    pw = ['energy', 'force', 'mass', 'velocity', 'acceleration', 'torque', 'power']
    for i, w1 in enumerate(pw):
        for w2 in pw[i+1:]:
            if w1 in words and w2 in words:
                d2 = metric.distance2(words[w1], words[w2])
                if d2 < F(1, 8):  # only show close pairs
                    print(f"  d^2({w1:12s}, {w2:12s}) = {d2}")

    # ── Cross-domain: NRCI + distance together ─────────────────────────
    print("\n" + "=" * 72)
    print("CROSS-DOMAIN — NRCI × Distance")
    print("=" * 72)

    # Find elements with highest NRCI (most coherent)
    print("\n--- Top 10 most coherent elements ---")
    elem_nrci = []
    for sym, c in elements.items():
        n = coherence.nrci(list(c))
        elem_nrci.append((sym, n))
    elem_nrci.sort(key=lambda x: -x[1])
    for sym, n in elem_nrci[:10]:
        print(f"  {sym:3s}: NRCI = {coherence.decimal_str(n, 4)}")

    print("\n--- Top 10 most coherent words ---")
    word_nrci = []
    for name, c in words.items():
        n = coherence.nrci(list(c))
        word_nrci.append((name, n))
    word_nrci.sort(key=lambda x: -x[1])
    for name, n in word_nrci[:10]:
        print(f"  {name:15s}: NRCI = {coherence.decimal_str(n, 4)}")

    # ── The combined view: distance + coherence ────────────────────────
    print("\n--- Combined: element nearest to 'mass' with NRCI ---")
    if 'mass' in words:
        mass_c = words['mass']
        ranked = []
        for sym, ec in elements.items():
            d2 = metric.distance2(mass_c, ec)
            n = coherence.nrci(list(ec))
            ranked.append((sym, d2, n))
        ranked.sort(key=lambda x: x[1])
        print("  Rank  Sym  d^2(word,element)    NRCI(element)")
        for i, (sym, d2, n) in enumerate(ranked[:5]):
            print(f"  {i+1:4d}  {sym:3s}  "
                  f"{coherence.decimal_str(d2, 10):>18s}  "
                  f"{coherence.decimal_str(n, 4)}")

    # ── Leech lattice axes: NRCI on physical points ────────────────────
    print("\n" + "=" * 72)
    print("LEECH LATTICE — NRCI on minimal vectors")
    print("=" * 72)

    from glm_universal.substrate import leech2
    print("\n--- Shape classes of minimal vectors ---")
    shown = {"A": 0, "B": 0, "C": 0}
    for v in leech2.minimal_vectors():
        hw = sum(1 for x in v if x != 0)
        if hw == 2 and shown["A"] < 2:
            n = coherence.nrci(list(v))
            bd = coherence.nrci_breakdown(list(v))
            print(f"  Class A (±4, 0^22): HW={hw}, NRCI={coherence.decimal_str(n, 4)}, "
                  f"regime={bd['regime']}, shell4={coherence.decimal_str(bd['shell4_sextet_signed'], 4)}")
            shown["A"] += 1
        elif hw == 8 and shown["B"] < 2:
            n = coherence.nrci(list(v))
            bd = coherence.nrci_breakdown(list(v))
            print(f"  Class B (±2^8, 0^16): HW={hw}, NRCI={coherence.decimal_str(n, 4)}, "
                  f"regime={bd['regime']}, shell4={coherence.decimal_str(bd['shell4_sextet_signed'], 4)}")
            shown["B"] += 1
        elif hw == 24 and shown["C"] < 2:
            n = coherence.nrci(list(v))
            bd = coherence.nrci_breakdown(list(v))
            print(f"  Class C (±3, ±1^23): HW={hw}, NRCI={coherence.decimal_str(n, 4)}, "
                  f"regime={bd['regime']}, shell4={coherence.decimal_str(bd['shell4_sextet_signed'], 4)}")
            shown["C"] += 1
        if all(v >= 2 for v in shown.values()):
            break

    print("\n" + "=" * 72)
    print("DONE — All values exact rationals, NRCI included; the roots in "
          "shells 2 and 4 are taken at a declared rational resolution.")
    print("=" * 72)


if __name__ == "__main__":
    main()
