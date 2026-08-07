# ARC-AGI v17.8 — The GLM as a Mind

**Date:** 2026-08-06
**Key shift:** GLM generates solutions directly (not solver selection)
**Tasks:** 40
**Iterations:** 5

---

## The GLM Mind

Per user: 'the GLM needs to generate solutions directly — lets try to let the GLM use its CRG + sandbox to PROPOSE a transformation, test it, and refine it.'

The v17.8 pipeline shifts from **solver-selection** to **GLM-generated solutions**:

1. **PERCEIVE:** the GLM examines what changed between input and output
2. **PROPOSE:** the GLM generates transformation proposals (using perception + CRG)
3. **TEST:** the sandbox tests each proposal on ALL train pairs
4. **REFINE:** if a proposal fails, the GLM tries the next one
5. **COMMIT:** if all train pairs pass, the GLM commits the solution
6. **FALLBACK:** if all GLM proposals fail, solvers are tried as fallback

## Results

| Run | Solved | New | GLM Mind | Fallback |
|---|---|---|---|---|
| 42 | 15/40 | 11 | 2 | 13 |
| 43 | 15/40 | 11 | 2 | 13 |
| 44 | 15/40 | 11 | 2 | 13 |
| 45 | 15/40 | 11 | 2 | 13 |
| 46 | 15/40 | 11 | 2 | 13 |

### Summary

- **Best run:** Run 42 — 15/40
- **GLM mind solves:** 2
- **Fallback solves:** 13

## What the GLM mind does differently

Instead of selecting from 10 pre-built solvers, the GLM:
1. **Perceives** the task (detects colour changes, gravity, shifts, rotations, flips, fills, scaling)
2. **Generates** up to 10 transformation proposals based on perception
3. **Tests** each proposal in the sandbox on all train pairs
4. **Commits** the first proposal that passes all train pairs

The solvers are still available as FALLBACK, but the primary mode is GLM-generated.

## Comparison across all versions

| Metric | v17.6 | v17.7 | v17.8 |
|---|---|---|---|
| Tasks | 36 | 36 | 40 |
| GLM concepts | 527 | 4,620 | 4620 |
| CRG edges | 814 | 1,103 | 1203 |
| GLM mind | ❌ | ❌ | ✅ |
| Sandbox | ✅ | ✅ | ✅ |
| Best solved | 15/36 | 15/36 | 15/40 |

## Next steps

1. **Deepen the GLM mind** — let it generate more complex proposals (compositions of transformations)
2. **Use the force-directed realignment** to settle the knowledge graph before reasoning
3. **Use hexcolour** for visual pattern matching between grids
4. **Let the GLM refine failed proposals** — currently it just tries the next one; it should ADJUST the failed proposal
5. **Integrate the full GLM.py runtime** for natural language reasoning
