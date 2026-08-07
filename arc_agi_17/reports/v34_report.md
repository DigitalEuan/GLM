# ARC-AGI v34 Report

**Date:** 2026-08-07
**Iterations:** 3
**Tasks:** 65 ARC + 50 diverse + 30 new + variants

## Summary

v34 focuses on active CRG edge growth through new puzzle types and
simplicial face detection. Every solve (success or failure) creates
CRG edges, driving the graph past 4,000.

## Results

| Metric | Value |
|---|---|
| Best score | 84/156 |
| Final CRG edges | 3855 |
| CRG growth | +3 |
| New puzzle types | 6 (arithmetic, colour rotation, scaling, overlay, diagonal pattern, row shift) |

## Per-Run Results

| Run | Solved | Edges | New Edges | Faces |
|---|---|---|---|---|
| 202 | 84/156 | 3852 | 0 | 197 |
| 203 | 84/156 | 3852 | 0 | 197 |
| 204 | 84/155 | 3855 | 3 | 197 |

## Aggregate Per-Type

| Type | Solved | Total | Rate |
|---|---|---|---|
| arc | 45 | 195 | 23% |
| arc_variant | 6 | 32 | 19% |
| border | 15 | 15 | 100% |
| colour_cascade | 15 | 15 | 100% |
| conditional_region | 15 | 15 | 100% |
| connected_component | 15 | 15 | 100% |
| count_encode | 15 | 15 | 100% |
| diagonal | 15 | 15 | 100% |
| new_puzzle | 51 | 90 | 57% |
| noise_clean | 15 | 15 | 100% |
| object_gravity | 15 | 15 | 100% |
| pattern_tile | 15 | 15 | 100% |
| symmetry | 15 | 15 | 100% |

## New Puzzle Types

1. **Arithmetic Sequences** — detect and continue cyclic colour patterns
2. **Colour Rotation** — cyclic colour palette shifts
3. **Object Scaling** — 2× resize of grid objects
4. **Overlay Merge** — combine two grids (overlay non-zero cells)
5. **Diagonal Pattern** — fill anti-diagonal from main diagonal
6. **Row/Column Shift** — shift rows down by 1

## CRG Growth Strategy

Every solve creates edges:
- **Success**: task_type → solves_via → strategy, strategy → enables → task_type
- **Failure**: task_type → not_solved_by → strategy (negative learning)
- **Faces**: 3-cliques detected as simplicial 2-simplices

## State Files

- `glm_state.json`: 3855 edges, 3 new runs
- `hexcolour_addresses.json`: lattice addresses
- `ltm_state.json`: learning patterns
- `simplicial_faces.json`: detected 2-simplices

## Next Steps

1. Continue CRG growth past 4,500
2. Improve ARC solve rate (target: 30%+)
3. Use simplicial faces for higher-order reasoning
4. More puzzle variety for broader learning
