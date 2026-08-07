# ARC-AGI v33 Report

**Date:** 2026-08-07
**Iterations:** 3
**Tasks:** 65 ARC + 50 diverse + variants

## Summary

v33 combines the full GLM mind (v29 pipeline) for ARC tasks with self-contained
solvers for diverse tasks. This restores the ARC solve rate while maintaining
100% on diverse types.

## Results

| Metric | Value |
|---|---|
| Best score | 66/118 |
| Final CRG edges | 3812 |
| CRG growth | +40 |

## Per-Run Results

| Run | Solved | Edges | +Edges |
|---|---|---|---|
| 198 | 66/118 | 3772 | +0 |
| 199 | 65/118 | 3792 | +0 |
| 200 | 65/118 | 3812 | +0 |

## Aggregate Per-Type

| Type | Solved | Total | Rate |
|---|---|---|---|
| arc | 45 | 195 | 23% |
| arc_variant | 1 | 9 | 11% |
| border | 15 | 15 | 100% |
| colour_cascade | 15 | 15 | 100% |
| conditional_region | 15 | 15 | 100% |
| connected_component | 15 | 15 | 100% |
| count_encode | 15 | 15 | 100% |
| diagonal | 15 | 15 | 100% |
| noise_clean | 15 | 15 | 100% |
| object_gravity | 15 | 15 | 100% |
| pattern_tile | 15 | 15 | 100% |
| symmetry | 15 | 15 | 100% |

## Architecture

- **ARC tasks**: Full v29 pipeline (GLM mind + imagination + crystallization + adversarial)
- **Diverse tasks**: Self-contained solvers (v32 inline solvers, fast and reliable)
- **Physics**: Gray code encoding, Symmetry Tax (exact Fraction), Golay snapping
- **State**: glm_state.json (3812 edges), hexcolour_addresses.json, ltm_state.json

## What's New

1. Restored full GLM mind for ARC tasks (was missing in v32)
2. Combined v29 ARC pipeline with v32 diverse solvers
3. Proper state management across all three state files
4. 65 ARC tasks (40 new from arc_agi_15)

## Next Steps

1. Push ARC solve rate higher (target: 30%+ on 65 tasks)
2. Push CRG past 4,000
3. Integrate simplicial CRG faces
4. More ARC task variants
