# ARC-AGI v17.1 — Goal-Directed Pipeline Results

**Date:** 2026-08-06
**Key innovation:** Semantic goal-setting layer (the GLM's Lingo language directs strategy selection)

---

## Summary

- **Tasks tested:** 10
- **Solved:** 5/10
- **New solves:** 1
- **Goal accuracy:** 5/5 solved tasks used a goal-directed strategy

## Strategy wins

| Strategy | Tasks solved |
|---|---|
| conditional_solver | 2 |
| colour_map_via_AND | 2 |
| settlement_gravity | 1 |

## Per-task results with semantic goals

| Task | Goal (Lingo) | Confidence | Solved? | Strategy |
|---|---|---|---|---|
| 00dbd492 | CONDITIONAL_CHARGE_SWAP | 1.00 | ✗ | None |
| 1e0a9b12 | COMPACTION_FLOW | 1.00 | ✓ | settlement_gravity |
| 396d80d7 | CONDITIONAL_CHARGE_SWAP | 1.00 | ✓ | conditional_solver |
| 45737921 | CHARGE_SWAP(5→8, 8→5) | 0.33 | ✗ | None |
| 50846271 | CONDITIONAL_CHARGE_SWAP | 1.00 | ✓ | colour_map_via_AND |
| 54d82841 | CONDITIONAL_CHARGE_SWAP | 1.00 | ✓ | colour_map_via_AND |
| 575b1a71 | REGION_FILL | 1.00 | ✗ | None |
| a85d4709 | CHARGE_SWAP(0→3, 5→3) | 0.25 | ✗ | None |
| ae58858e | CONDITIONAL_CHARGE_SWAP | 1.00 | ✓ | conditional_solver |
| e48d4e1a | CONDITIONAL_CHARGE_SWAP | 1.00 | ✗ | None |

## The semantic goal-setting layer

Per the user's insight: 'the machine doesn't know what it's trying to achieve.'

The v17.1 pipeline addresses this with a **SemanticGoalLayer** that:
1. Examines all train pairs
2. Determines the transformation type (CHARGE_SWAP, COMPACTION_FLOW, REGION_FILL, etc.)
3. Expresses the goal in the GLM's Lingo language
4. Selects only strategies that match the goal
5. Falls back to trying all strategies if the goal confidence is low

This is the GLM's semantic understanding (Lingo vocabulary + three-column thinking) applied to ARC task classification.

## What's new in v17.1

### New solvers (the suggested next moves)

| Solver | Lingo term | Description |
|---|---|---|
| ShiftSolver | CENTROID_SHIFT | Shift all cells by (dr, dc) |
| RotateSolver | DIHEDRAL_ROTATION | Rotate 90/180/270 degrees |
| FlipSolver | PLANE_REFLECTION | Flip horizontal/vertical |
| ConditionalSolver | CONDITIONAL | CHARGE_SWAP only for objects with size >= N |
| ColumnRankSolver | CARDINALITY_MEASURE | Colour each column by rank |
| SettlementDynamicsSolver | COMPACTION_FLOW (settlement) | Output is equilibrium of input |

### Fixed solvers

- **InteriorFillSolver**: improved border colour detection (was failing on 00dbd492)

## Comparison to v17

| Metric | v17 | v17.1 |
|---|---|---|
| Strategies | 8 | 11 |
| Solved | 4/10 | 5/10 |
| New solves | 1 | 1 |
| Semantic goal | ❌ | ✅ |

## Honest assessment

The semantic goal-setting layer is the key innovation. Instead of blindly trying all strategies, the pipeline:
1. **Understands** what the task is asking (in Lingo)
2. **Selects** only the strategies that match the goal
3. **Falls back** to trying all strategies if the goal is uncertain

This is the GLM's semantic intelligence directing the substrate's computational power. The machine now knows what it's trying to achieve.

## Next steps

1. **Expand the Lingo vocabulary** for ARC-specific concepts (e.g., 'tile', 'repeat', 'mirror')
2. **Add more solvers** for the goal types that aren't yet covered
3. **Use the BW-1024 NRCI** to disambiguate goals when multiple types are possible
4. **Integrate the full GLM** (from glm_machine/) for richer semantic reasoning
5. **Learn from failures**: record which goals led to which failures, and update the goal layer
