# ARC-AGI v25 — Gap Words + Deliberative + Applied Imagination

**Date:** 2026-08-07
**Iterations:** 5

## What's new

### 1. Gap Word Derivation (from v37)
The GLM derives vectors for unknown concepts on-the-fly. When it encounters
a new pattern during ARC solving, it:
- Hashes the pattern to a 24-bit vector
- Snaps to nearest Golay codeword
- Checks proximity to existing concepts (Hamming ≤ 8)
- If close, ADDS it to the vocabulary — the GLM has LEARNED

### 2. Deliberative Reasoning (from v37)
The GLM breaks complex problems into steps:
1. Shape analysis (same? different? scaled?)
2. Colour analysis (which changed? which stayed?)
3. Position analysis (did cells move?)
4. Synthesis (what is the simplest rule?)

### 3. Applied Imagination
When imagination detects incoherence, it now CREATES a refined proposal:
- Colour mismatch → correct the colour map from train pairs
- Density low → add fill
- Shape mismatch → skip (can't fix)

### 4. More Puzzle Variation
- Colour-swapped variants
- Rotated variants
- Scaled variants (2×)
- Flipped variants

## Results

| Run | Solved | Lattice | Mind | Deliberative | Imagination | Gap Words | Edges |
|---|---|---|---|---|---|---|---|
| 122 | 8/45 | 0 | 0 | 3 | 4 | 0 | 2723 |
| 123 | 16/45 | 0 | 0 | 2 | 13 | 0 | 2743 |
| 124 | 4/45 | 0 | 0 | 2 | 1 | 0 | 2763 |
| 125 | 4/45 | 0 | 0 | 2 | 2 | 0 | 2783 |
| 126 | 7/45 | 0 | 0 | 3 | 2 | 0 | 2803 |

### Summary
- **Best:** 16/45
- **Gap words derived:** 0
- **Imagination used:** 2
- **Deliberative solves:** 3
- **GLM edges:** 2803
