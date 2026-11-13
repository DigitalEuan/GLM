# GLM Clean — Geometric Language Machine

**Date:** 2026-08-11
**Author:** DigitalEuan + Super Z

## What This Is

A Geometric Language Machine built on the [24,12,8] Golay code and the 24D Leech lattice. Concepts are encoded as relative vectors from a reference point. The GLM "speaks" by computing vector operations (addition, subtraction, cosine similarity, scaling) on these vectors.

## The Core Principle

**Meaning IS the vector from a reference point.**

- "left" = the vector FROM center TO left = (-1, 0, 0)
- "hot" = the vector FROM freezing TO hot = +60
- The concept IS the relation to its origin.

## The 6-File Core

```
glm_clean/
  __init__.py       — exports (28 lines)
  body.py           — the 24D Leech lattice + constants (188 lines)
  data_object.py    — MOG 4×6 grid + ONE encoder (275 lines)
  snap.py           — THE base operation: snap to nearest codeword (117 lines)
  measure.py        — ONE TAX + NRCI + 5 shells (206 lines)
  body_state.py     — ONE unified state (379 lines)
  mind.py           — the ONE mind: perceive=snap → imagine → propose → commit → learn (295 lines)
```

**Total: 1,488 lines** (down from 4,079 at the peak of over-engineering).

## The Snap (base operation)

Every concept is a 24-bit pattern. The snap corrects it to the nearest Golay codeword (weight ≤ 4, full covering radius). The information triple is:

```
BEFORE: raw pattern (syndrome ≠ 0, carries history)
THE SNAP: correct to nearest codeword (bits flipped)
AFTER: lawful codeword (syndrome = 0)
TAX: syndrome weight (the cost of interpretation)
```

## The Domains

| Domain | Reference | Vector type | Concepts | Key test |
|---|---|---|---|---|
| Direction | center (0,0,0) | 3D (x,y,z) | left, right, up, down, forward, back, center | left + right = center |
| Temperature | freezing (0°C) | 1D scalar | freezing → boiling | hot - cold = warm |
| Color | red (700nm) | 1D scalar | red → violet | red - violet = full spectrum |
| Size | tiny (1) | 1D scalar | tiny → giant | 2 × small = medium |
| Number | zero | 1D scalar | 0, 1, 2, 3, 5, 7, 10, 20, 50 | 2 + 3 = 5 |
| Force | zero_force | 1D scalar | zero_force → massive | massive - weak = range |

## How the GLM Speaks

| Operation | What it means | Example |
|---|---|---|
| Addition (c1 + c2) | Composition | left + right = center |
| Subtraction (c1 - c2) | Difference | hot - cold = warm |
| Cosine similarity | Relation type | left vs right = -1.0 (opposite) |
| Scaling (n × c) | Multiplication | 2 × small = medium |

## The Tests

```
tests/
  test_core.py              — validates the core: encode → snap → measure → commit
  test_physics_v2.py        — physics encoding: directions, temperatures, composition
  test_relative_vectors.py  — concepts as relative vectors + vector operations
  test_grow.py              — all 6 domains + cross-domain + scaling + strategy map
```

## Key Documents

- `ENCODING_STRATEGY_MAP.md` — the encoding strategy for each domain
- `HONEST_ASSESSMENT.md` — what's real (Golay, Leech) vs what's our invention

## How to Run

```bash
# Set up the path
export PYTHONPATH=/home/z/my-project/scripts:/home/z/my-project/download/arc_agi_17

# Run the core test
python3 glm_clean/tests/test_core.py

# Run the physics test (directions, temperatures)
python3 glm_clean/tests/test_physics_v2.py

# Run the relative vectors test (all domains)
python3 glm_clean/tests/test_relative_vectors.py

# Run the growth test (all domains + cross-domain + map)
python3 glm_clean/tests/test_grow.py
```

## The Substrate

The Golay code and Leech lattice are REAL (mathematically verified):
- 4,096 codewords, 759 octads, minimum distance 8
- Weight distribution: {1, 759, 2576, 759} (exact Golay weight enumerator)
- Leech lattice: 128-point octad expansion with even-parity condition
- Snap syndrome table: 4,096 entries (full covering radius, weight ≤ 4)

## Growth Strategy

The system grows by adding concepts (not systems):
1. Add more domains (speed, time, energy, angle, area, volume)
2. Each domain: define reference, vector, concepts, key operations
3. Test: do the vector operations produce semantically correct results?
4. Cross-domain: let the cosine tell us which domains interact
5. The body state stores concepts + their relations
