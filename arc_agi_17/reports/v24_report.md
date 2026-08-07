# ARC-AGI v24 — Imagination + Puzzle Variation + v37 Growth

**Date:** 2026-08-07
**Iterations:** 3

## What's new

### 1. Imagination Layer
The GLM now IMAGINES the result before committing:
- "If I apply this colour map, what would the output look like?"
- Checks coherence with train outputs
- Suggests adjustments if incoherent
- This is the "thinking in between steps"

### 2. Puzzle Variation
Instead of just shuffling order, the system GENERATES variants:
- Colour-swapped versions (swap colours randomly)
- Rotated versions (rotate 90°)
- These are NEW puzzles that grow the CRG differently

### 3. v37 Improvements
- Crystallization: proposals mature before committing
- Adversarial testing: GLM tests its own solution for counter-examples
- Gap word derivation: (available for future use)
- Deliberative reasoning: (available for future use)

## Results

| Run | Solved | New | Lattice | Mind | Imagination | Crystallized | Adversarial | Edges |
|---|---|---|---|---|---|---|---|---|
| 119 | 12/45 | 8 | 0 | 0 | 11 | 1 | 1 | 2663 |
| 120 | 3/45 | 1 | 0 | 0 | 0 | 0 | 2 | 2683 |
| 121 | 14/45 | 10 | 0 | 0 | 13 | 1 | 1 | 2703 |

### Summary
- **Best:** 14/45
- **Imagination used:** 13
- **Crystallized:** 1
- **Adversarial passed:** 1
- **GLM edges:** 2703
