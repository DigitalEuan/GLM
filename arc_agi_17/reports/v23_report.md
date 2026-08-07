# ARC-AGI v23 — Lattice Perception

**Date:** 2026-08-07
**Key innovation:** 5-layer lattice perception from perception_1.txt
**Iterations:** 10

## The 5-Layer Perception Architecture (from perception_1.txt)

1. **Encoding Frontend** — Grid (r,c,color) → 24-bit (X,Y,Z) via Gray code
   - Adjacent cells have Hamming distance 1 (preserves spatial topology)
   - Snapped to Golay codeword (noise damping)

2. **Active Perception** — Face transforms (AND/XOR/OR) + TAX-driven ROI
   - XZ XOR: boundary detection
   - XY AND: alignment detection
   - YZ OR: object merging
   - High TAX → zoom in on ambiguous regions

3. **Adaptive Resolution** — MOG compression of uniform backgrounds

4. **Perceptual Parity** — Complete Golay decoding as noise damping
   - Covering radius 4: all states snap to valid codewords

5. **Differential Transition** — 2Δv ∈ Λ₂₄ (Leech lattice vector)
   - Input→Output mapped to algebraic difference vector
   - The transformation IS the vector
   - Finding the rule = finding the invariant 2Δv across all train pairs

## The Key Insight

"Inferring the ARC rule reduces to finding the shared Leech translation
vector 2Δv that satisfies all training examples!"

Instead of heuristic perception (detect "colour swap", "gravity", etc.),
the system computes the ALGEBRAIC difference between input and output.
The transformation IS the Leech lattice vector.

## Results

| Run | Solved | New | Lattice | Mind | Analogical | Fallback | Edges |
|---|---|---|---|---|---|---|---|
| 109 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2463 |
| 110 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2483 |
| 111 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2503 |
| 112 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2523 |
| 113 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2543 |
| 114 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2563 |
| 115 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2583 |
| 116 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2603 |
| 117 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2623 |
| 118 | 14/40 | 10 | 2 | 0 | 1 | 11 | 2643 |

### Summary
- **Best run:** Run 109 — 14/40
- **Lattice solves:** 2
- **GLM edges:** 2643
- **Known addresses:** 15

## What lattice perception adds

The DifferentialTransitionEngine computes the algebraic difference between
input and output. Instead of trying many heuristic perception types,
it computes the EXACT transformation:

1. If colour map is consistent → "colour_map" (the map IS the vector)
2. If gravity works → "gravity" (the compaction IS the vector)
3. If shift works → "shift" (the offset IS the vector)
4. If rotation works → "rotation" (the angle IS the vector)
5. If fill works → "fill" (the fill colour IS the vector)
6. If conditional → "conditional" (the threshold IS the vector)

The transition is computed ONCE (not per-proposal) and if it's consistent
across all train pairs, it's applied DIRECTLY — no need to try multiple proposals.

## The "Diffusion" mapping (from perception_1.txt)

- **Denoising = Golay snapping** — noise collapses to nearest codeword
- **Goal = geodesic vector 2Δv** — the transformation IS the vector
- **Iterative refinement = TAX-driven ROI** — high TAX triggers zoom

The system is a "deterministic diffusion model" — it finds the invariant
Leech lattice vector and applies it, using Golay decoding to snap away noise.
