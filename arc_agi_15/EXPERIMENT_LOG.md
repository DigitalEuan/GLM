# Experiment Log — ARC AGI × UBP/GLM Study

**Date:** 29 July 2026
**Author:** E.R.A. Craig + AI Assistant

## Final Results

| Pipeline | Solved | Rate | New solves |
|----------|--------|------|------------|
| v029 (baseline) | 2/50 | 4% | — |
| + v032 distance rule | 3/50 | 6% | `396d80d7` |
| + v033 Minkowski sweep | 3/50 | 6% | (rediscovers 396d80d7 via p=1.5) |
| + v034 Totient Kinetics | 3/50 | 6% | (enriches feature space) |
| + v036 Cayley-Menger | 3/50 | 6% | (enables object identity) |

## Architecture Summary (8 modules built)

| Module | Purpose | Status |
|--------|---------|--------|
| v030 recolour | Consistent/conditional/positional recolour | Built, 0 solves |
| v030 pattern | Flood fill, spread, object grow | Built, 0 solves |
| v031 rules | General rule discovery | Built, 0 solves |
| v032 distance | Manhattan + diagonal filter | **SOLVES 396d80d7** |
| v033 Minkowski | Vectorized p-norm sweep | Built, 0 new |
| v034 totient | Geometric number theory | Built, 0 solves |
| v035 combined | Unified pipeline | Built, 0 new |
| v036 Cayley-Menger | Coordinate-free object identity | Built, 0 solves |

## Key Discovery: Minkowski p=1.5

The rule for 396d80d7: "bg cells at Minkowski p=1.5 distance ≈ 1.59 from objects → change to minority colour."

This expresses the composite Manhattan L₁=2 + Chebyshev L∞≤1 rule as a single fractional norm.

## Cayley-Menger Results

### What was built:
- Object segmentation (connected components)
- Pairwise distance matrix computation
- Cayley-Menger determinant (area/volume from distances)
- Menger hash (translation/rotation invariant object identity)
- Containment detection (betweenness property)
- Gram matrix eigenvalue signature

### Results:
- Menger identity found candidates for ae58858e and e509e548 (near-miss tasks)
- Containment detection found 0 interior cells for7acdf6d3 (9-shape is U, not frame)
- No new solves

### Why it didn't solve tasks:
1. ARC tasks don't primarily use object identity — they use spatial relationships
2. The9-shape in7acdf6d3 is a U-shape, not a complete frame — containment doesn't apply
3. Object identity (same shape → same transform) isn't a pattern in these tasks

## The Fundamental Challenge

**47/50 tasks produce zero candidates.** The bottleneck is candidate generation, not ranking or verification.

The approaches tried so far cover:
- **Geometric operations** (DSL): 1 task (gravity)
- **Distance-based rules** (Minkowski): 1 task (396d80d7)
- **Similarity matching** (k-arm): 1 task (45737921)

The remaining 47 tasks need:
1. **Conditional rules** — "if neighbour colour X then change to Y"
2. **Multi-step compositions** — "rotate then recolour"
3. **Object-level reasoning** — "extract object, transform, reinsert"
4. **Context-dependent modes** — "scattered vs frame arrangement"

## Next Steps (Prioritized)

1. **Per-colour Minkowski layers** — compute distance to each colour separately
2. **Neighbourhood conditional rules** — per-(colour, neighbour_sig) → output
3. **DSL pair compositions** — try all ~200 pairs of useful DSL ops
4. **Arrangement topology classifier** — detect scattered/frame/dense modes
5. **Weighted Manhattan** — row/column bias for anisotropic patterns

## For the UBP/GLM System

### What worked:
- Minkowski p-norm as parameterized distance primitive
- Composite metric intersections (L₁ + L∞)
- Vectorized distance field computation
- Automated rule discovery via truth table strategy

### What needs development:
- Conditional logic in the GLM grammar
- Multi-step program composition
- Object-level abstraction (segmentation)
- Mode detection (arrangement topology)

### The Cayley-Menger contribution:
Provides coordinate-free object identity and containment detection. Valuable as:
- Translation/rotation invariant object fingerprinting
- Intrinsic area/volume computation
- Distance geometry foundation for Leech lattice projection

But ARC tasks primarily use spatial relationships, not object identity. The Menger framework is better suited as a FEATURE LAYER for the Minkowski sweep than as a standalone solver.
