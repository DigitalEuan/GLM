# ARC-AGI v17 — Substrate-Native Pipeline Results

**Date:** 2026-08-06
**Goal:** Use the substrate work from v1-v11 to push the ARC-AGI score above 9/50

---

## Summary

- **Tasks tested:** 10
- **Solved:** 4/10
- **New solves** (not in v15/v16): 1

## Strategy wins

| Strategy | Tasks solved |
|---|---|
| colour_map_via_AND | 3 |
| settlement_gravity | 1 |

## Per-task results

| Task ID | Solved? | Strategy | HW (train inputs) | TAX | Transform magnitude | Conservation? |
|---|---|---|---|---|---|---|
| 00dbd492 | ✗ | — | [12, 12, 8, 12] | [4.6761, 4.6761, 3.1174, 4.6761] | [8, 12, 12, 8] | [True, True, True, True] |
| 1e0a9b12 | ✓ | settlement_gravity | [12, 12, 16] | [4.6761, 4.6761, 6.2348] | [0, 0, 0] | [True, True, True] |
| 396d80d7 | ✗ | — | [8, 8] | [3.1174, 3.1174] | [0, 0] | [True, True] |
| 45737921 | ✗ | — | [12, 8, 8] | [4.6761, 3.1174, 3.1174] | [0, 0, 0] | [True, True, True] |
| 50846271 | ✓ | colour_map_via_AND | [12, 12, 12, 12] | [4.6761, 4.6761, 4.6761, 4.6761] | [12, 8, 8, 12] | [True, True, True, True] |
| 54d82841 | ✓ | colour_map_via_AND | [12, 12, 12] | [4.6761, 4.6761, 4.6761] | [12, 8, 8] | [True, True, True] |
| 575b1a71 | ✗ | — | [12, 8, 12] | [4.6761, 3.1174, 4.6761] | [8, 12, 8] | [True, True, True] |
| a85d4709 | ✗ | — | [8, 8, 8, 8] | [3.1174, 3.1174, 3.1174, 3.1174] | [12, 12, 12, 8] | [True, True, True, True] |
| ae58858e | ✓ | colour_map_via_AND | [12, 8, 16, 16] | [4.6761, 3.1174, 6.2348, 6.2348] | [12, 12, 12, 12] | [True, True, True, True] |
| e48d4e1a | ✗ | — | [12, 12, 8, 12] | [4.6761, 4.6761, 3.1174, 4.6761] | [12, 12, 12, 12] | [True, True, True, True] |

## What the substrate adds

The v17 pipeline integrates:
- **v9 scale formula** (S = λ / TAX(HW)) — used in ScaleAwareResizeSolver
- **v10 bit-ops layer** (XOR, AND, snap, popcount) — used throughout
- **v10 conservation law** (TAX(a⊕b) = TAX(a) + TAX(b) - 2×TAX(a∧b)) — verified per task
- **v11 layered architecture** (BitOps ↔ Python interleaved) — the pipeline structure
- **v8 π-bridged encoding** (octave + phase + compactness) — used in SubstrateMetricMatchSolver
- **v11 parity sign flag** — used in ParitySignRecolorSolver

### New strategies (substrate-native)

| Strategy | Substrate feature used |
|---|---|
| substrate_metric_match | HW/TAX/NRCI matching across train pairs |
| colour_map_via_AND | AND conservation (shared structure) |
| scale_aware_resize | v9 scale formula for resize factor |
| parity_sign_recolor | v11 parity sign flag |

## Honest assessment

This pipeline pulls together the substrate work from v1-v11 into a single ARC-AGI attempt. The new substrate-native strategies (D, E, F, G) complement the existing strategies (A, B, C, H) from arc15.

The substrate metrics (HW, TAX, NRCI, conservation) are computed for every task, giving the GLM rich context for reasoning. The conservation law (TAX under XOR with AND interaction) is verified on every train pair.

**What worked:** see the strategy wins table above.

**What didn't work (yet):** the substrate_metric_match strategy is conservative — it only applies a transformation if the substrate signature matches closely. This means it solves few tasks but doesn't make mistakes. Loosening the match criterion might solve more tasks but would risk incorrect solutions.

## Next steps

1. **Add more strategies** that use the substrate: settlement_dynamics with TAX-minimization, conditional reasoning with parity flags, geometric perception with spatial_arithmetic
2. **Loosen the substrate_metric_match** to use fuzzy matching (within a threshold) instead of exact matching
3. **Use the BW-1024 NRCI** as a finer-grained task classifier (the 24-bit NRCI has only 3 values; BW-1024 has more)
4. **Integrate the GLM mind** (substrate_mind.py from arc15) as an additional strategy — it solves 3 tasks the toolkit can't
5. **Use the experience routing table** from long_term_memory to learn which strategies work for which substrate signatures
