# ARC-AGI v21 — GLM Module Integration

**Date:** 2026-08-06
**Tasks:** 40
**Iterations:** 5

## GLM Modules Integrated

1. **GLM_geometric_compute** — GeometricNumber + GeometricArithmetic
   - Numbers as Golay codewords with NRCI, TAX, quadrant decomposition
   - Geometric addition via XOR + AND with conservation law verification
   - Every grid cell value gets a GeometricNumber

2. **math_atlas** — exact rational constants (π, e, φ) via continued fractions
   - No floats — all math is Fraction-based
   - The GLM's math is now exact

3. **physics** — UBPConstantsExact + UBPCoherenceExact
   - Exact NRCI computation (float-free)
   - CoherenceRegime classification (OnBit, Coherent, Transitional, Subcoherent)
   - Each grid gets a coherence regime label

4. **data_object encoding** — warping + geometric work
   - Encode each grid as a Data Object (domain + volume + compactness + parity)
   - Compute geometric work between input and output (transformation energy)
   - Activation row warping for bond-order-like transformations

## What the geometric work adds

The geometric work tells the GLM HOW MUCH the transformation costs:
- magnitude 0: input and output have same encoding (within resolution)
- magnitude ≤ 8: small change (likely colour swap or fill)
- magnitude > 8: large change (likely structural transformation)

This helps the GLM classify the transformation type before proposing solutions.

## Results

| Run | Solved | New | Mind | Analogical | Fallback | Addresses |
|---|---|---|---|---|---|---|
| 91 | 15/40 | 11 | 2 | 1 | 12 | 15 |
| 92 | 15/40 | 11 | 2 | 1 | 12 | 15 |
| 93 | 15/40 | 11 | 2 | 1 | 12 | 15 |
| 94 | 15/40 | 11 | 2 | 1 | 12 | 15 |
| 95 | 15/40 | 11 | 2 | 1 | 12 | 15 |

### Summary
- **Best run:** Run 91 — 15/40
- **GLM mind solves:** 3
- **Known addresses:** 15

## Comparison

| Version | Modules | Score | Mind |
|---|---|---|---|
| v17.8 | base | 15/40 | 2 |
| v18 | +hexcolour | 15/40 | 3 |
| v19 | +extended perception | 15/40 | 3 |
| v20 | +task-specific | 15/40 | 3 |
| **v21** | **+geometric compute + math atlas + physics + data_object** | **15/40** | **3** |

## What's been integrated (full list)

| Module | Source | Purpose |
|---|---|---|
| Full GLM vocabulary (4,620 concepts) | glm_unified_resource.json | Semantic reasoning |
| Full CRG (1,900+ edges) | GLM_CRG_EXPANDED + MASSIVE | Concept relation graph |
| GLM Sandbox | GLM_sandbox.py | Code execution + verification |
| GLM Mind | v17.8+ | Propose → test → refine → commit |
| Natural language reasoning | v17.9 | Three-column thinking in English |
| HexColour addressing | v18 | Lattice address for analogical reasoning |
| Extended perception | v19 | Marker, pattern, extraction, count |
| Task-specific perception | v20 | Two-swap, tiling, crop, row-colour |
| **Geometric compute** | **GLM_geometric_compute.py** | **Numbers as codewords, geometric arithmetic** |
| **Math atlas** | **math_atlas.py** | **Exact rational constants (π, e, φ)** |
| **Physics** | **physics.py** | **Exact NRCI, coherence regimes** |
| **Data Object encoding** | **data_object/README.md** | **Grid encoding + geometric work + warping** |
| Bit-Ops layer | v10/v11 | Native XOR, AND, snap, TAX conservation |
| Lean-verified decoder | v2-v4 | The snap bug fix |
| Persistent LTM | v17.3+ | Learning analysis, growth tracking |
| Task variation | v20 | Shuffled task order for training diversity |
