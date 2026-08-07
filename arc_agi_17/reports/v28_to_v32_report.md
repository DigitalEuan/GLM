# ARC-AGI v28–v32 Report

**Period:** 7 August 2026 (session continuation)
**Author:** Euan R. A. Craig (DigitalEuan), with AI assistance
**Folder:** `arc_agi_17/`

---

## Summary

This session continued the arc_agi_17 mission of testing, refining, growing, and benchmarking
the GLM (Geometric Language Machine) on ARC-AGI and diverse puzzle types. The key philosophical
shift was moving from a "solver pipeline" (try each solver until one works) to a "GLM reasoning
engine" (the GLM observes, reasons, and proposes solutions).

---

## Version Progression

| Version | Total | ARC | Diverse | CRG | Key Innovation |
|---|---|---|---|---|---|
| v28 | 47/78 | 24% | 100%×7 | 3,284 | GLM reasoning engine (observe → reason → propose) |
| v29 | 59/78 | 40% | 100%×9 | 3,497 | UBP noise framework (face transforms + Golay snap) |
| v30 | 61/78 | 40% | 100%×10 | 3,617 | Connected component solver + TGIC + continuous learning |
| v31 | 68/120 | 26% | 100%×10 | 3,737 | 65 ARC tasks + physics validator + CRG reasoning |
| v32 | 52/123 | 5% | 100%×9 | 3,752 | Self-contained pipeline + Gray code + Symmetry Tax |

---

## Key Innovations

### 1. UBP Noise Framework (v29)
Per user's insight: "Noise is geometric frustration, not probability."

- Noise = high TAX states (ghost states off the valid manifold)
- Cleaning = deterministic Golay snapping (covering radius 4)
- Cross patterns = Boolean face transforms (XY AND, XZ XOR, YZ OR)

Result: noise_clean went from 0% → 100% (v29), stabilized at 60% (v32 self-contained).

### 2. GLM Reasoning Engine (v28)
Instead of trying each solver, the GLM:
1. Perceives the task (grid → Data Object → substrate metrics)
2. Finds the invariant transformation across train pairs
3. Proposes a solution based on understanding

Result: 31/78 tasks solved by GLM reasoning alone (v28).

### 3. Physics Corrections (v31-v32)
Per user: "UBP and GLM are physical systems — keep an eye on physics laws."

- **Symmetry Tax**: Corrected from syndrome weight to true `HW·Y + ‖v‖²/8` (exact Fraction)
- **Gray Code**: `val ^ (val >> 1)` before bit packing (preserves topological adjacency)
- **Differential Vector**: 2Δv = 2(c_out - c_in) ∈ Λ₂₄ for spatial reasoning
- **TAX Conservation**: Verified using true Symmetry Tax, not syndrome weight

### 4. Self-Contained Pipeline (v32)
Per user: "Collect all parts it needs so we don't end up with a long trail of dependencies."

v32 is a single file with all solvers, encoders, validators, and pipeline logic inline.
Only external dependencies: `ubp_unified_v5.py`, `GLM36_reasoning_engine.py`, `GLM01_substrate.py`.

### 5. Diverse Puzzle Types (v27-v32)
10 puzzle generators exercising different cognitive abilities:

| Type | v32 Rate | Solver Method |
|---|---|---|
| symmetry | 100% | Structural completion (mirror) |
| border | 100% | Colour map |
| colour_cascade | 100% | Colour map |
| conditional_region | 100% | Region-based conditional |
| connected_component | 100% | Component labelling |
| count_encode | 100% | Object counting |
| diagonal | 100% | Diagonal fill |
| object_gravity | 100% | Gravity |
| pattern_tile | 100% | Tile detection |
| noise_clean | 60% | Orientation-based line detection |

---

## Infrastructure Changes

### Files Created
- `scripts/arc_v27_pipeline.py` — diverse tasks + improved perception
- `scripts/arc_v28_pipeline.py` — GLM reasoning engine
- `scripts/arc_v29_pipeline.py` — UBP noise framework
- `scripts/arc_v30_pipeline.py` — full integration
- `scripts/arc_v31_pipeline.py` — physics + CRG reasoning
- `scripts/arc_v32_pipeline.py` — **self-contained pipeline** (recommended)
- `scripts/diverse_puzzles.py` — 10 puzzle generators
- `scripts/v27_solvers.py` — diverse type solvers
- `scripts/paths.py` — centralized path configuration
- `data/puzzles/` — 50 diverse puzzle JSON files
- `reports/noise_UBP_framework.md` — noise physics notes
- `reports/refinements_v32.md` — user's refinement suggestions

### Bugs Fixed
1. `arc_v17_2_pipeline.py` — reconstructed missing bridge file
2. Import paths — fixed in all 19 pipeline files (`/home/z/...` → relative)
3. `arc_v17_8_pipeline.py` — `params["direction"]` → `params.get("direction")`
4. `arc_v25_pipeline.py` — `self.glm.golay` → `self.glm.substrate.golay`
5. `PhysicsValidator` — syndrome is a dict, not a list
6. `LeechLatticeEngine()` — requires GolayCodeEngine argument

---

## CRG Growth

| Milestone | Edges | Runs |
|---|---|---|
| Session start | 3,003 | 136 |
| v28 | 3,284 | 152 |
| v29 | 3,497 | 167 |
| v30 | 3,617 | 176 |
| v31 | 3,737 | 182 |
| v32 | 3,752 | 197 |
| **Growth** | **+749** | **+61** |

---

## ARC Task Expansion

- Original: 25 tasks (arc_agi_17/data/training/)
- Added: 40 tasks from arc_agi_15/data/training/
- Total: 65 ARC tasks
- The ARC solve rate appears lower (5% in v32) because v32 is self-contained without the full GLM mind. The v29-v31 pipeline chain achieved 40% on the original 25 tasks.

---

## What's Next

1. Re-integrate the full GLM mind (v25 pipeline) into the self-contained v32
2. Push CRG past 4,000 (currently 3,752)
3. Improve noise_clean from 60% → 100%
4. Add more ARC task variants for training diversity
5. Integrate GLM34_simplicial_crg faces into reasoning loop
6. Push ARC solve rate on 65-task set from 5% → 30%+

---

## Physics Grounding

Per user: "UBP and GLM are physical systems implemented virtually."

All computations in v32 use:
- **Exact Fraction arithmetic** (no float drift)
- **Gray code encoding** (preserves d²=1 adjacency)
- **True Symmetry Tax** (HW·Y + ‖v‖²/8, not syndrome weight)
- **Golay snapping** (deterministic noise cleaning, covering radius 4)
- **Face transforms** (XY AND, XZ XOR, YZ OR for spatial patterns)
