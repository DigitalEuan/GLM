# GLM Knowledge — Consolidated Training Record

**Started:** 2 August 2026  
**Author:** E R A Craig + AI Assistant  
**Data:** `glm_training_data.json` (single file, all calibration data)

---

## What This Is

The GLM (Geometric Language Machine) learns through experimentation. This document records what it has learned during ARC AGI iterations. The companion JSON file (`glm_training_data.json`) contains all training data — element encodings, bond predictions, molecule data, pattern solving results, and benchmarks.

Everything is geometry. Data Objects are positions and geometry in 24D Leech space. Spatial Arithmetic 'GMHGL/spatial_artithmetic.py' computes on those positions. The mind learns by encoding subjects, computing on them, and verifying against reality.

This GLM system build on and develops the initial implementation 'glm_machine/'

* GLM language unified resource (15MB): 
'glm_machine/glm_unified_resource.json'

* GLM Concept Relation Graph: 
'glm_machine/GLM_CRG_EXPANDED.py'

* Database of words and explanation: 
'long_term_memory/ubp_lang_kb_combined_v4.json'

* State Memory:
'glm_machine/glm_state/'

* Persistant Memory - needs a defined and continued solid method, this is the current attempt: 
'glm_machine/GLM_persistence.py'

---

## The Substrate

### Golay [24,12,8]
- 4,096 codewords, minimum distance 8
- Corrects 3 errors, detects 7
- Single-bit vectors snap to HW=0 (isolated bits = noise)
- Basis vectors all collapse to zero — the alphabet is full codewords

### MOG (Miracle Octad Generator)
- 4×6 grid: 4 rows (Reality, Info, Activation, Potential) × 6 columns
- Each row is 6 bits (Gray-coded, values 0-63)
- Projects 24D to 2D for observation
- Row 0 (Reality) has widest blast radius (11 bits per toggle)

### Leech Lattice (Λ₂₄)
- 196,560 minimal vectors, all norm²=32
- Class A: 1,104 (HW=2, NRCI=0.688)
- Class B: 97,152 (HW=8, NRCI=0.620)
- Class C: 98,304 (HW=24, NRCI=0.491)

### Y Constant
- Y = 1/(π + 2/π) ≈ 0.264675
- Entropic wobble — cost per active coordinate
- Activation quantum: Y + 1/8 = 0.389675

### TAX and NRCI
- TAX = HW·Y + ‖v‖²/8 (topological + geometric cost)
- NRCI = 10/(10 + TAX) (coherence measure, 0-1)
- NRCI=1.0 for zero vector (perfect coherence, vacuum)

---

## What We Learned — Element Training (Iterations 0-12)

### Best Element Encoding
- Properties: EN, BP, MP, Rho
- Scaling: EN×10, BP÷40, MP÷40, Rho×10
- r(ΔH) = −0.91

### Best Molecule Encoding
- Properties: M, MP (mass, melting point)
- r(ΔH) = +0.96
- 50 unique vectors for 82 molecules

### Bond Energy
- AND encoding: r(BE) = +0.90 with NRCI × bond_order
- Cross-validated: mean R = 0.82
- Bond-order inference from geometry: r(BO) = +0.52

### Key Findings
1. AND encoding captures shared structure (r(BE)=+0.90)
2. Pre-snap metrics carry more signal than post-snap
3. Snap cost (bits changed) is real signal
4. Noble gases are the vacuum state (HW=0, NRCI=1.0)
5. Same-element pairs are invisible (AND/XOR gives zero)
6. Compactness measures geometric regularity

### Benchmarks (Element/Geometry Training)
| Benchmark | Pass Rate | Metric |
|-----------|-----------|--------|
| triplet_nrci | 100% | r = +0.79 |
| shape_intersection | 67% | +0.28 |
| golay_error_correction | 60% | 0.40 |
| pair_geometry_r | 47% | r = +0.05 |

---

## What We Learned — Pattern Solving (Iterations 17-18)

### Pattern Mind v1 (no substrate knowledge)
- 17/29 (59%) synthetic patterns solved
- Resonant (tiling): 4/4, Geodesic (mirrors): 4/4, Flow (fill): 3/3

### Pattern Mind v2 (with substrate knowledge)
- **19/29 (66%)** synthetic patterns solved
- Gained 6 patterns (movement, rotation, crop)
- Lost 4 patterns (style misclassification)
- AND_NRCI metric helps classify tasks

### Style Classification
| Style | Solved | Best For |
|-------|--------|----------|
| resonant | 4/4 | Tiling, pattern repetition |
| geodesic | 11/18 | Mirrors, rotation, movement |
| machining | 2/2 | Crop, extraction |
| differential | 2/4 | Colour swaps |
| flow | 0/1 | Flood fill |
| entropic | 0/4 | Simplification |

### ARC-AGI Results
- Basic run: 1/50 (gravity only)
- Enhanced mind: 8/50 (toolkit + substrate)
- Learning mind: 9/50 (+ concentric nesting)
- Experience routing table built (150 entries)

---

## Driving Styles 

The mind selects a driving style based on task topology:

| Style | Physics Analogy | Goal Metric | Best For |
|-------|----------------|-------------|----------|
| Machining | Ohmic geometry | Minimise TAX | High noise |
| Resonant | Cymatics | Maximise NRCI | Patterns, repetition |
| Differential | Capacitor | Minimise Δ | Movement, colour change |
| Geodesic | Relativity | Shortest path | Rotation, reflection |
| Entropic | Thermodynamics | Equilibrium | Simplification |
| Flow | Fluid dynamics | Vector field | Expansion, fill |

---

## What We Learned — Language (Iteration 19)

### Word Encoding

| Method | Unique Vectors | Discrimination |
|--------|---------------|----------------|
| hash | 108/109 | Best — almost unique per word |
| structural | 88/109 | Good — captures word shape |
| letters | 67/109 | Poor — many collisions (shared letters, incorrect approach) |

### Within-Group vs Cross-Group (hash encoding)

| Metric | AND_NRCI |
|--------|----------|
| Same group (animals, colours, etc.) | 0.79 |
| Different group | 0.76 |
| Opposites | 0.81 |
| Related/Synonyms | 0.82 |

**Separation: +0.034** — weak but positive. Same-group words are slightly more similar in the substrate than cross-group words.

### More Deterministic Approach

Use MOG Data Object structure to denote Nouns, Verbs and other grammatical information. The GLM needs to also encode word **relationships** (how words combine, modify, relate to each other) not just individual words so providing a word with Leech geometry allows us to construct relationships similar to 'GMHGL/spatial_artithmetic.py' so words can calculate like numbers can when they are polygons.

---

## What We Learned — Language v2 (Iteration 20)

### Words as Data Objects with Meaning

Each word encoded as a 24-bit Data Object using measurable properties:
- Row 0 (Reality): word length
- Row 1 (Info): POS (3 bits) + semantic domain (3 bits)
- Row 2 (Activation): emotional valence (5 bits) + concreteness (1 bit)
- Row 3 (Potential): vowel count (3 bits) + consonant count (3 bits)

### Results

- 71 unique vectors for 95 words
- Within-group AND_NRCI: 0.73-0.81
- Cross-group AND_NRCI: 0.77-0.85
- Separation (same - diff): −0.011 — slightly negative

### Key Finding

**Structural properties dominate semantic properties.** Words with similar length and consonant count get high AND_NRCI regardless of meaning. The semantic information (domain, valence, concreteness) is encoded but gets overwhelmed by structural similarity.

This is different from elements, where properties (Z, EN, Rad) carry distinct physical meaning. For words, the "physical" properties (length, syllables) are less meaningful than the "chemical" properties (valence, domain).

### Implication

Language encoding needs **interaction-based meaning**, not isolated word properties. The spec says: "words may have meaning when compared relative to other words and known Subjects." The next step is encoding word **relationships** — how words combine in phrases and sentences — not just individual words.

---

## Open Questions

1. Can we predict bond order from geometry alone (r > 0.7)?
2. Can the substrate distinguish single/double/triple bonds?
3. What happens when we encode ARC grids as Data Objects?
4. Can Spatial Arithmetic compute transformations (not just static metrics)?
5. Can the mind learn to generate solutions, not just select from templates?

---

## Data File Structure

All data in `glm_training_data.json`:

```
{
  "version": 1,
  "generated": "...",
  "elements": {118 elements × 3 specs, 354 Data Objects},
  "bonds": {36 bonds, AND encoding, predictions},
  "molecules": {82 molecules, M/MP encoding},
  "patterns": {10 learned patterns with confidence},
  "pattern_solving": {v1 and v2 results},
  "arc_agi": {basic, enhanced, learning runs},
  "experience": {routing table},
  "benchmarks": {pattern solving across runs},
  "training_log": {all runs with timestamps}
}
```
