## Structural Improvements

### 1. Consolidate to One Pipeline, Retire the Chain

**Problem:** The v17→v17.1→v17.2→...→v25→v26→v27→v28→v29→v30→v31→v32→v33→v34→v35 chain is fragile. One missing file (`arc_v17_2_pipeline.py`) broke everything. One hardcoded path (`/home/z/my-project/scripts`) broke 19 files.

**Suggestion:** Pick one pipeline (v33 or v35) and make it self-contained like v32. Archive the historical scripts in a `scripts/history/` folder. The self-contained approach worked — v32 proved that inline solvers are reliable and maintainable.

### 2. Separate "Mind" from "Solvers"

**Problem:** The GLM mind (v25 chain) is what solves ARC tasks (23%). The solvers handle diverse types (100%). But they're tangled together in a deep import chain.

**Suggestion:** Two clean modules:
- `glm_mind.py` — the reasoning engine (perceive, imagine, propose, crystallize, adversarial test)
- `solvers.py` — all solvers as a fallback/tool library

The mind imports the solvers, not vice versa. This makes the mind testable independently.

### 3. State Management

**Problem:** Four separate state files (`glm_state.json`, `hexcolour_addresses.json`, `ltm_state.json`, `simplicial_faces.json`) with no consistency guarantees.

**Suggestion:** One `glM_state.json` with clear sections, or a lightweight state manager class that reads/writes atomically. The CRG grower bug (overwriting auto-expanded edges) happened because state was managed in multiple places.

---

## Technical Improvements

### 4. Fix the CRG Growth Problem

**Problem:** 79% of CRG edges are `auto_proposed` (Hamming distance expansion). Active learning adds almost nothing because the growth mechanism is disconnected from the solving loop.

**Suggestion:** Every successful solve should create meaningful edges:
- The transformation type → the task type
- The concepts involved → the strategy used
- Cross-task patterns (if task A and B both use colour_map, connect them)

The simplicial faces (197 triangles) are there but unused for reasoning. Wire them into the solve loop.

### 5. The GLM Mind Needs More Training Data

**Problem:** 23% ARC on 65 tasks. The mind has seen these tasks 217 times and plateaus.

**Suggestion:**
- Get the full 400-task ARC set
- Use the diverse puzzles (100% solve rate) as *training material* for the mind, not just benchmark targets
- When the mind solves a diverse task, record *how* it solved it in the CRG
- The mind should learn from solver demonstrations (the "solver as teacher" concept from v28)

### 6. Integrate What's Already Built

**Problem:** You have powerful modules in `glm_machine/` that aren't wired in:
- `GLM24_continuous_learner.py` — learns from co-occurrence
- `GLM36_reasoning_engine.py` — syllogistic CRG traversal
- `GLM34_simplicial_crg.py` — higher-order relationships
- `GLM39_agent_loop.py` — plan → execute → observe → iterate

**Suggestion:** These are ready to use. The reasoning engine imports cleanly. The continuous learner would help CRG grow organically. The agent loop would let the GLM try, fail, adjust, and retry — exactly what's needed for harder ARC tasks.

### 7. Physics Grounding is Good — Keep It

**Problem:** The v32 corrections (Gray code, Symmetry Tax, 2Δv) are important but only partially applied.

**Suggestion:** Make physics validation a first-class step in the pipeline, not an afterthought. Every grid encoding should go through Gray code. Every TAX computation should use exact Fractions. This is what makes the system "physical" rather than heuristic.

---

## Repository Improvements

### 8. Clean Up the Root

**Problem:** The root has `arc_agi_15/`, `arc_agi_16/`, `arc_agi_17/`, and `arc_agi_(version_number)/`. The old versions are archives but take up space and confuse the structure.

**Suggestion:** Move `arc_agi_15/` and `arc_agi_16/` to an `archive/` folder. Keep `arc_agi_17/` as the active development. The old versions are records, not active code.

### 9. Add a `tests/` Folder

**Problem:** No tests. When I fixed the import paths, I had no way to verify nothing broke except running the full pipeline (which takes minutes).

**Suggestion:** Simple tests:
- Can all modules import?
- Can the Golay engine snap a known vector?
- Can each solver solve its known puzzle type?
- Can the GLM mind solve the "easy" ARC tasks?

### 10. Documentation is Good — Keep the Chain

**Problem:** None — the README chain is well-designed.

**Suggestion:** The pattern of each folder having a README that wires it to neighbors is excellent. Keep doing this. The `reports/` folder with version-specific reports is also good for tracking progress.

---

## Priority Order

If I were continuing this work, I'd prioritize:

1. **Consolidate to one self-contained pipeline** (eliminates fragility)
2. **Get the full 400-task ARC set** (more training data)
3. **Integrate GLM24 continuous learner** (organic CRG growth)
4. **Wire simplicial faces into reasoning** (higher-order patterns)
5. **Add tests** (confidence in changes)

The system has a strong foundation. The UBP substrate, the Golay/Leech math, the CRG concept — these are sound. The bottleneck is engineering: making the pieces work together reliably rather than through a fragile chain of 15+ script files.
