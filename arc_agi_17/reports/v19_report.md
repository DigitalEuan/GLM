# ARC-AGI v19 — Push the Score Higher

**Date:** 2026-08-06
**Tasks:** 40
**Iterations:** 3

---

## What was added to raise the score

1. **Extended perception** — 4 new detection types:
   - Marker fill (a marker colour indicates where to fill)
   - Pattern extension (a pattern repeats and needs extending)
   - Object extraction (output keeps only a sub-region)
   - Count and label (objects labelled by their size)

2. **Extended proposals** — the GLM generates proposals for each new perception type

3. **Hexcolour task routing** — tasks are routed by lattice address, not just task type

4. **Threshold tuning** — the analogical reasoning tries multiple Hamming distance thresholds (4, 6, 8, 10, 12, 16, 20)

5. **20 iterations** — hexcolour addresses accumulate across runs

## Results

| Run | Solved | New | Mind | Analogical | Refined | Fallback | Addresses |
|---|---|---|---|---|---|---|---|
| 78 | 15/40 | 11 | 2 | 1 | 0 | 12 | 15 |
| 79 | 15/40 | 11 | 2 | 1 | 0 | 12 | 15 |
| 80 | 15/40 | 11 | 2 | 1 | 0 | 12 | 15 |

### Summary

- **Best run:** Run 78 — 15/40
- **GLM mind solves (last run):** 3
- **Fallback solves (last run):** 12
- **Known hexcolour addresses:** 15

## Comparison across ALL versions

| Version | Tasks | GLM concepts | CRG edges | Mind solves | Best solved |
|---|---|---|---|---|---|
| v17 | 10 | — | — | 0 | 4/10 (40%) |
| v17.5 | 25 | 527 | 763 | 0 | 10/25 (40%) |
| v17.8 | 40 | 4,620 | 1,203 | 2 | 15/40 (38%) |
| v17.9 | 40 | 4,620 | 1,263 | 3 | 15/40 (38%) |
| v18 | 40 | 4,620 | 1,463 | 3 | 15/40 (38%) |
| v19 | 40 | 4620 | 1883 | 3 | 15/40 (38%) |

## What it takes to raise the score

From here, raising the score requires:

1. **More perception types** — the 25 unsolved tasks need transformations the GLM can't detect yet. Each new perception type unlocks a batch of tasks.

2. **More hexcolour addresses** — the analogical reasoning improves as more addresses accumulate. 50-100 runs would give enough addresses for meaningful analogical matching.

3. **Working compositional proposals** — the compositional proposals (flip THEN recolour, etc.) are currently stubs for most types. Making them actually work would handle multi-step tasks.

4. **The full GLM.py chat()** — richer natural language reasoning would let the GLM 'think through' harder tasks, not just perceive and propose.

5. **More ARC tasks** — testing on the full 400-task ARC AGI-1 set would give a more accurate score and more opportunities for analogical matching.
