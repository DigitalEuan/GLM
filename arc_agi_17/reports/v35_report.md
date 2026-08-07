# ARC-AGI v35 Report — Final Push

**Date:** 2026-08-07
**Iterations:** 5
**Tasks:** 65 ARC + 50 diverse + 30 v34 + 25 v35 + variants

## Summary

v35 is the final push for this session. It adds simplicial face reasoning,
more puzzle types, and runs until CRG approaches 4,000.

## Results

| Metric | Value |
|---|---|
| Best score | 105/181 |
| Final CRG edges | 3935 |
| CRG growth | +80 |

## Per-Run Results

| Run | Solved | Edges |
|---|---|---|
| 210 | 104/181 | 3855 |
| 211 | 104/181 | 3875 |
| 212 | 104/180 | 3895 |
| 213 | 105/181 | 3915 |
| 214 | 103/181 | 3935 |

## Aggregate Per-Type

| Type | Solved | Total | Rate |
|---|---|---|---|
| arc | 75 | 325 | 23% |
| arc_variant | 10 | 54 | 19% |
| border | 25 | 25 | 100% |
| colour_cascade | 25 | 25 | 100% |
| conditional_region | 25 | 25 | 100% |
| connected_component | 25 | 25 | 100% |
| count_encode | 25 | 25 | 100% |
| diagonal | 25 | 25 | 100% |
| new_puzzle | 185 | 275 | 67% |
| noise_clean | 25 | 25 | 100% |
| object_gravity | 25 | 25 | 100% |
| pattern_tile | 25 | 25 | 100% |
| symmetry | 25 | 25 | 100% |

## New in v35

1. **Simplicial Face Reasoner**: Uses 3-cliques in CRG to suggest transformations
2. **5 new puzzle types**: checkerboard, border extract, fill interior, colour cycle, mirror extend
3. **25 extra puzzles** generated
4. **CRG target**: Run until edges > 4,000

## Session Summary (v28–v35)

| Version | Total | ARC | Diverse | CRG | Key |
|---|---|---|---|---|---|
| v28 | 47/78 | 24% | 100%×7 | 3,284 | GLM reasoning |
| v29 | 59/78 | 40% | 100%×9 | 3,497 | UBP noise |
| v30 | 61/78 | 40% | 100%×10 | 3,617 | Connected component |
| v31 | 68/120 | 26% | 100%×10 | 3,737 | Physics + 65 ARC |
| v32 | 52/123 | 5% | 100%×9 | 3,752 | Self-contained |
| v33 | 66/118 | 23% | 100%×10 | 3,812 | GLM mind restored |
| v34 | 84/156 | 23% | 100%×10 | 3,855 | New puzzles + faces |
| **v35** | — | — | — | **~4,000** | **Final push** |

## State Files

- `glm_state.json`: concepts + CRG edges + run history
- `hexcolour_addresses.json`: lattice addresses
- `ltm_state.json`: learning patterns
- `simplicial_faces.json`: 2-simplices

## Next Session

1. Full 400-task ARC set
2. Simplicial face reasoning refinement
3. Continuous learner integration
4. CRG target: 5,000 edges
