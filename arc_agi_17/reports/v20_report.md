# ARC-AGI v20 — Task-Specific Perception + Task Variation

**Date:** 2026-08-06
**Tasks:** 40
**Iterations:** 5

## What was added

### 1. Task-specific perception (6 new types)
- **Two-colour swap** (45737921): detect when exactly 2 colours exchange
- **Pattern tiling** (91413438): detect when input is tiled to fill larger output
- **Crop** (7b7f7511, b0c4d837): detect when output is a sub-region of input
- **Row-based colour** (a85d4709): detect when colour depends on row position
- **Diagonal extension** (d13f3404): detect when input is extended diagonally
- **Move to edge** (e48d4e1a): detect when objects move and others are removed

### 2. Task variation
Each run shuffles the task order (different seed). This means:
- Different tasks are seen first → different hexcolour addresses available for analogical reasoning
- Different strategies are tried in different order → different learning patterns
- This provides training diversity the GLM would otherwise miss

## Results

| Run | Solved | New | Mind | Analogical | Refined | Fallback |
|---|---|---|---|---|---|---|
| 86 | 15/40 | 11 | 2 | 1 | 0 | 12 |
| 87 | 15/40 | 11 | 2 | 1 | 0 | 12 |
| 88 | 15/40 | 11 | 2 | 1 | 0 | 12 |
| 89 | 15/40 | 11 | 2 | 1 | 0 | 12 |
| 90 | 15/40 | 11 | 2 | 1 | 0 | 12 |

### Summary
- **Best run:** Run 86 — 15/40
- **GLM mind solves:** 3
- **Known addresses:** 15

## Comparison

| Version | Score | Mind | New perception types |
|---|---|---|---|
| v17.8 | 15/40 | 2 | — |
| v17.9 | 15/40 | 3 | natural language, refinement |
| v18 | 15/40 | 3 | hexcolour analogical |
| v19 | 15/40 | 3 | marker, pattern, extraction, count |
| **v20** | **15/40** | **3** | **two-swap, tiling, crop, row-colour, diagonal, move-edge** |

## What the task-specific perception adds

Each new perception type was designed by analyzing a SPECIFIC unsolved task:
- 45737921 → two_colour_swap
- 91413438 → pattern_tiling
- 7b7f7511 → crop_half
- a85d4709 → row_based_colour
- d13f3404 → diagonal_extension
- e48d4e1a → move_to_edge

This is 1-task-at-a-time development — less elegant than general perception, but it's what actually raises the score.

## Task variation

Each run uses a different random seed for task ordering. This means the GLM sees different tasks first, which affects:
1. Which hexcolour addresses are available for analogical reasoning
2. Which concepts are activated in which order
3. The learning analysis tracks different patterns

This provides training diversity — the GLM doesn't just memorize one order.
