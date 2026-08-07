# 'arc_agi_17/' - ARC-AGI v17 — Substrate-Native Cognitive Architecture

**Version:** 17.35 (7 August 2026)  
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Parent:** `../README.md`  
**ARC AGI Score:** 105/181 total (23% ARC + 100% diverse types)  
**Cumulative Training Runs:** 217  
**CRG Edges:** 4,015 (target: 5,000 per major epoch)  
**Key File:** `scripts/arc_v35_pipeline.py` (latest) or `scripts/arc_v32_pipeline.py` (self-contained)

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- A substrate-native cognitive architecture for ARC-AGI. Not a solver pipeline — a GLM mind that perceives, imagines, reasons, and acts using the 24-dimensional Golay/Leech substrate. Solvers are fallback only; the primary mode is GLM-generated solutions.

---

## Role in the System

```
GMHGL/              ← provides Golay engine, TAX, NRCI (ubp_unified_v5.py)
  ↓ imported by
data_object/        ← provides encoding methods (warping, geometric work)
  ↓ encoding methods used by
glm_machine/        ← provides GLM vocabulary (4,256 words), CRG (597+250 edges), sandbox
  ↓ vocabulary + CRG + sandbox used by
arc_agi_17/ (this folder)
  ├── reads engine from → ../GMHGL/ubp_unified_v5.py (via /home/z/my-project/scripts/ubp_engine/)
  ├── reads vocabulary from → ../glm_machine/glm_unified_resource.json
  ├── reads CRG from → ../glm_machine/GLM_CRG_EXPANDED.py + GLM_CRG_MASSIVE.py
  ├── reads LTM from → ../long_term_memory/glm_training_data.json
  ├── writes results to → results/ (persistent state across runs)
  └── writes reports to → reports/
```

---

## What This Is

ARC-AGI v17 is the **17th iteration** of the ARC-AGI attempt, built on the UBP substrate. Unlike previous versions (v15 solvers, v16 experiments), v17 is a **growth system** — each run grows the GLM's vocabulary, CRG edges, and hexcolour addresses. The system does not rebuild between versions; it grows.

### Key Innovation: Growth, Not Rebuild

From v17 → v35, the system accumulated:
- **4,282 concepts** (from 0 → 26 → 527 → 4,620 → 4,282)
- **4,015 CRG edges** (from 0 → 30 → 98 → 763 → 3,003 → 4,015)
- **66 hexcolour addresses** (persistent lattice memory)
- **217 cumulative training runs** (state persists across all)
- **14 generative components** (0 passive)
- **11 puzzle types** (ARC + 10 diverse: symmetry, border, colour_cascade, conditional_region, connected_component, count_encode, diagonal, noise_clean, object_gravity, pattern_tile)
- **197 simplicial faces** (2-simplices in the CRG)

---

## Architecture (v26 — the current system)

### The 5-Layer Perception Pipeline (from 'reports/perception_1.txt')

```
ARC 2D Grid / Visual Input
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Encoding Frontend (SpatialEncoder)                       │
│    • Grid (r, c) + Color (0-9) → 24-bit (X, Y, Z)           │
│    • Gray-coded spatial channels (d²=1 for adjacent cells)  │
│    • Snapped to Golay codeword (noise damping)              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Active Perception (ActivePerception)                     │
│    • XZ XOR: boundary detection (row × color)               │
│    • XY AND: alignment detection (row × col)                │
│    • YZ OR:  object merging (col × color)                   │
│    • TAX-driven ROI: high-TAX regions trigger zoom          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Adaptive Resolution (future: MOG compression)            │
│    • Low-entropy background → macro-codewords               │
│    • High-entropy edges → full 24-bit resolution            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Perceptual Parity (Complete Golay Decoder)               │
│    • Covering radius 4 — all states snap to codewords       │
│    • Collapses ghost states / visual noise                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Differential Transition Engine (2Δv ∈ Λ₂₄)               │
│    • Input → Output mapped to Leech lattice vector          │
│    • Finding the rule = finding the invariant 2Δv           │
│    • Common operations = lattice translation vectors        │
└─────────────────────────────────────────────────────────────┘
```

### The GLM Mind (v25/v26)

The GLM mind is the primary problem-solving engine. Solvers are **fallback only**.

```
1. PERCEIVE (three-column thinking + Data Object analysis)
   ↓
2. LATTICE PERCEPTION (compute 2Δv — algebraic transition vector)
   ↓ if consistent → apply directly
3. DELIBERATIVE REASONING (shape → colour → position → synthesis)
   ↓ if high confidence → apply directly
4. HEXCOLOUR ROUTING (compute lattice address, search for similar tasks)
   ↓ if similar task found → try same transformation (analogical)
5. IMAGINE (compute imagined output, check coherence with train pairs)
   ↓ if incoherent → create adjusted proposal
6. PROPOSE (perception + CRG traversal + LTM routing + compositional)
   ↓
7. CRYSTALLIZE (proposal matures: seed → form → crystallize → commit)
   ↓
8. ADVERSARIAL TEST (GLM tests its own solution for counter-examples)
   ↓ if passed
9. COMMIT (apply to test input)
   ↓
10. LEARN (record success to LTM, derive gap words, grow CRG)
```

### All 14 Generative Components

| # | Component | Source | What it generates |
|---|---|---|---|
| 1 | Full GLM vocabulary (4,620 concepts) | glm_unified_resource.json | Activated concepts drive CRG traversal |
| 2 | Full CRG (4,015 edges) | GLM_CRG_EXPANDED + MASSIVE + auto-expanded + active growth | Proposals via edge traversal |
| 3 | GLM Sandbox | GLM_sandbox.py | Verification results gate commits |
| 4 | GLM Mind | v17.8+ | Propose → imagine → test → refine → commit |
| 5 | Natural language reasoning | v17.9 | English reasoning traces (three-column thinking) |
| 6 | HexColour addressing | v18 | Analogical proposals from lattice proximity |
| 7 | Extended perception | v19 | Marker, pattern, extraction, count detection |
| 8 | Task-specific perception | v20 | Two-swap, tiling, crop, row-colour detection |
| 9 | Geometric compute | GLM_geometric_compute.py | NRCI, TAX, quadrant decomposition per number |
| 10 | Math atlas | math_atlas.py | Exact π, e, φ constants (no float drift) |
| 11 | Physics | physics.py | Coherence regime classification |
| 12 | Data Object encoding | data_object/README.md | Geometric work drives proposal prioritization |
| 13 | LTM routing | v22 | Strategy recommendations from routing table |
| 14 | Bit-Ops layer | v10/v11 | Native XOR, AND, snap, TAX conservation |

### v37 Improvements Integrated (from glm_machine/dev/glm_v37_grown.py)

| Feature | What it does |
|---|---|
| Crystallization | Ideas mature: seed → form → crystallize → commit → fade |
| Adversarial testing | GLM generates counter-examples to test its own solutions |
| Gap word derivation | Unknown concepts get derived vectors on-the-fly |
| Deliberative reasoning | Break problems into computational steps (shape → colour → position → synthesis) |
| Applied imagination | When imagination detects incoherence, creates adjusted proposals |
| Puzzle variation | Generates colour-swapped, rotated, scaled, flipped variants for training diversity |

---

## Version History

| Version | Key Innovation | Best Score | CRG Edges | Cumulative Runs |
|---|---|---|---|---|
| v17 | Base pipeline + Bit-Ops substrate | 4/10 | — | 1 |
| v17.1 | Semantic goal-setting (Lingo) | 5/10 | — | 2 |
| v17.2 | GLM semantic core + LTM | 5/10 | 30 | 3 |
| v17.3 | Growth layer (persistent state) | 5/10 | 98 | 5 |
| v17.4 | Unified pipeline (all parts cooperating) | 5/10 | 110 | 8 |
| v17.5 | Full GLM CRG (597 edges, 473 concepts) | 10/25 | 763 | 18 |
| v17.6 | Sandbox verification | 15/36 | 814 | 29 |
| v17.7 | Full 4,256-word vocabulary (real vectors) | 15/36 | 1,103 | 41 |
| v17.8 | GLM mind (propose → test → commit) | 15/40 | 1,203 | 46 |
| v17.9 | Natural language reasoning + refinement | 15/40 | 1,263 | 49 |
| v18 | HexColour analogical reasoning | 15/40 | 1,463 | 59 |
| v19 | Extended perception + threshold tuning | 15/40 | 1,883 | 80 |
| v20 | Task-specific perception + variation | 15/40 | 1,903 | 85 |
| v21 | GLM module integration (geometric compute, math atlas, physics, data_object) | 15/40 | 1,923 | 95 |
| v22 | All components generative (0 passive) | 14/40 | 2,263 | 98 |
| v23 | Lattice perception (5-layer architecture) | 14/40 | 2,643 | 118 |
| v24 | Imagination + puzzle variation + v37 features | 14/45 | 2,703 | 121 |
| v25 | Gap words + deliberative + applied imagination | **16/45** | 2,803 | 126 |
| v26 | Sustained growth training (10 iterations) | 15/47 | **3,003** | **136** |
| v27 | Diverse puzzles + object/symmetry detection + fixed paths | 24/78 | 3,103 | 141 |
| v28 | GLM reasoning engine (observe → reason → propose) | 47/78 | 3,284 | 152 |
| v29 | UBP noise framework (face transforms + Golay snap) | 59/78 | 3,497 | 167 |
| v30 | Connected component solver + TGIC + continuous learning | 61/78 | 3,617 | 176 |
| v31 | 65 ARC tasks + physics validator + CRG reasoning | 68/120 | 3,737 | 182 |
| v32 | Self-contained pipeline (no dependency chain) | 52/123 | 3,752 | 197 |
| v33 | Full GLM mind restored for ARC + diverse solvers | 66/118 | 3,812 | 200 |
| v34 | Active CRG growth + new puzzles + simplicial faces | 84/156 | 3,855 | 204 |
| v35 | Final push: CRG 4000+ / faces / puzzle variety | **105/181** | **4,015** | **217** |

---

## Solve Modes

The GLM can solve tasks through multiple modes, each representing a different level of reasoning:

| Mode | What it means | Example |
|---|---|---|
| `lattice_perception` | Algebraic: compute 2Δv, verify, apply | Colour swap, gravity, shift |
| `deliberative_reasoning` | Step-by-step: shape → colour → position → synthesis | Conditional swap, fill |
| `hexcolour_analogical` | Recognize task by lattice address, try same transformation | ae58858e |
| `glm_mind` | Full pipeline: perceive → imagine → propose → crystallize → commit | Flip, gravity |
| `glm_mind_refined` | Proposal failed → imagination adjusted → retested → committed | (ready for harder tasks) |
| `fallback_solver` | GLM couldn't solve → solver used as training material | Colour map, conditional |

---

## What's Here

| Path | Purpose | Connects To |
|------|---------|-------------|
| `scripts/arc_v35_pipeline.py` | **Latest pipeline** — final push with simplicial faces | Imports v34 |
| `scripts/arc_v34_pipeline.py` | Active CRG growth + new puzzles + simplicial faces | Imports v33 |
| `scripts/arc_v33_pipeline.py` | Full GLM mind (v29) + self-contained diverse solvers (v32) | Imports v29 + v32 |
| `scripts/arc_v32_pipeline.py` | **Self-contained pipeline** — all solvers inline, no dependency chain | Standalone |
| `scripts/arc_v31_pipeline.py` | Physics-grounded + CRG reasoning + 65 ARC tasks | Imports v30 |
| `scripts/arc_v30_pipeline.py` | Full integration: TGIC + continuous learning + reasoning | Imports v29 |
| `scripts/arc_v29_pipeline.py` | UBP noise framework + full ARC pipeline | Imports v25 |
| `scripts/arc_v28_pipeline.py` | GLM reasoning engine (observe → reason → propose) | Imports v25 |
| `scripts/arc_v27_pipeline.py` | Diverse puzzles + object/symmetry detection | Imports v25 |
| `scripts/arc_v26_pipeline.py` | Sustained growth training (10 iterations) | Imports v25 |
| `scripts/arc_v25_pipeline.py` | Gap words + deliberative + imagination | Imports v24 |
| `scripts/arc_v24_pipeline.py` | Imagination + puzzle variation + v37 | Imports v23 |
| `scripts/arc_v23_pipeline.py` | Lattice perception (5-layer architecture) | Imports v22 |
| `scripts/arc_v22_pipeline.py` | All components generative | Imports v21 |
| `scripts/arc_v21_pipeline.py` | GLM module integration | Imports v20 |
| `scripts/arc_v20_pipeline.py` | Task-specific perception + variation | Imports v19 |
| `scripts/arc_v19_pipeline.py` | Extended perception + threshold tuning | Imports v18 |
| `scripts/arc_v18_pipeline.py` | HexColour analogical reasoning | Imports v17.9 |
| `scripts/arc_v17_*.py` | v17 through v17.9 (base → GLM mind → NL reasoning) | Foundation |
| `scripts/diverse_puzzles.py` | 10 puzzle generators (50 tasks) | Used by v27+ |
| `scripts/v27_solvers.py` | Diverse type solvers (as teachers) | Used by v27+ |
| `scripts/paths.py` | Centralized path configuration | Replaces hardcoded paths |
| `scripts/loader.py` | ARC task loader (from arc_agi_15) | — |
| `data/training/` | 65 ARC training tasks (25 original + 40 from arc_agi_15) | — |
| `data/puzzles/` | 50 diverse puzzles (10 types × 5 each) | — |
| `data/puzzles/v34_new/` | 30 new puzzles (6 types × 5 each) | — |
| `data/puzzles/v35_extra/` | 25 extra puzzles (5 types × 5 each) | — |
| `data/glm_unified_vocab_compact.json` | 4,256-word GLM vocabulary with real vectors | From glm_machine/ |
| `data/glm_crg_expanded_edges.json` | 597 CRG edges from GLM_CRG_EXPANDED.py | From glm_machine/ |
| `data/glm_crg_massive_edges.json` | 250 MASSIVE CRG edges | From glm_machine/ |
| `data/glm_unified_relations.json` | 67 unified relations | From glm_machine/ |
| `results/glm_state.json` | **Persistent GLM state** (4,282 concepts, 4,015 edges, 217 runs) | Grows each run |
| `results/hexcolour_addresses.json` | **66 persistent lattice addresses** | Grows with variants |
| `results/ltm_state.json` | LTM learning patterns (persistent) | Grows each run |
| `results/simplicial_faces.json` | **197 simplicial 2-simplices** (3-cliques in CRG) | Grows with CRG |
| `results/v*_results.json` | Results from each version | — |
| `reports/v*_report.md` | Markdown reports from each version | — |
| `reports/v28_to_v32_report.md` | Session report covering v28-v32 progress | — |
| `reports/noise_UBP_framework.md` | UBP noise framework notes (from user) | — |
| `reports/refinements_v32.md` | Refinement suggestions (from user) | — |

---

## Quick Start

```bash
cd scripts

# Run the latest pipeline (v35 — final push with simplicial faces)
python3 arc_v35_pipeline.py

# Run the self-contained pipeline (v32 — no dependency chain, recommended for learning)
python3 arc_v32_pipeline.py

# Run the full GLM mind pipeline (v33 — best ARC solve rate)
python3 arc_v33_pipeline.py

# Generate diverse puzzles
python3 diverse_puzzles.py
```

Each run:
1. Loads the previous GLM state (concepts + CRG edges + LTM) from `results/glm_state.json`
2. Runs on 65 ARC tasks + 50 diverse puzzles + 30 new puzzles + variants
3. Grows the CRG (~20 edges/run via auto-expansion + active growth)
4. Accumulates hexcolour addresses
5. Detects simplicial faces (3-cliques in CRG)
6. Saves the grown state for the next run

---

## Dependencies

| Needs From | What |
|-----------|------|
| `../GMHGL/ubp_unified_v5.py` | Golay engine, Leech lattice, TAX, NRCI, BarnesWallEngine |
| `../glm_machine/glm_unified_resource.json` | 4,256-word vocabulary with real 24-bit vectors |
| `../glm_machine/GLM_CRG_EXPANDED.py` | 597 curated CRG edges |
| `../glm_machine/GLM_CRG_MASSIVE.py` | 250 MASSIVE CRG edges |
| `../glm_machine/GLM_sandbox.py` | Sandbox for verification |
| `../glm_machine/GLM_geometric_compute.py` | Geometric arithmetic |
| `../glm_machine/math_atlas.py` | Exact rational constants |
| `../glm_machine/physics.py` | Exact NRCI, coherence regimes |
| `../glm_machine/GLM36_reasoning_engine.py` | Syllogistic CRG traversal, sequence detection |
| `../glm_machine/GLM01_substrate.py` | ConceptRelationGraph, CRGEdge construction |
| `../long_term_memory/glm_training_data.json` | LTM experience routing table |
| `../data_object/README.md` | Encoding methods (warping, geometric work) |

**Note:** `arc_v32_pipeline.py` is self-contained — it only imports `ubp_unified_v5.py`, `GLM36_reasoning_engine.py`, and `GLM01_substrate.py`. All solvers, encoders, and validators are inline.

## Produces For

| Provides To | What |
|------------|------|
| `results/glm_state.json` | Grown GLM state (concepts + CRG + run history) |
| `results/hexcolour_addresses.json` | Persistent lattice addresses |
| `results/ltm_state.json` | LTM learning patterns |
| `../long_term_memory/` | Training data (successes recorded for future runs) |

---

## The UBP-to-Realworld Scale (from this study)

The EM propagation calibration study (v1-v9) established:

```
S(λ, HW) = λ / [HW × (Y + 1/8)]

  HW=8:  S = λ / 3.1174  (gamma/X-ray/EUV regime)
  HW=12: S = λ / 4.6761  (optical/IR/microwave regime)
  HW=16: S = λ / 6.2348  (radio/ELF regime)
```

The snap_to_codeword bug fix (Lean-verified) is documented in `snap_to_codeword_FIX.md` (in parent download/).

### Key Substrate Properties

| Property | Value | Source |
|---|---|---|
| Y constant | 1/(π + 2/π) ≈ 0.2647 | Exact (continued fraction) |
| TAX conservation | TAX(a⊕b) = TAX(a) + TAX(b) − 2×TAX(a∧b) | Proven (tautology of binary arithmetic) |
| Golay covering radius | 4 (all 24-bit words snap to codewords) | Lean-verified |
| Leech minimal norm | 32 (norm² = 4·d², d² ∈ {0,8,12,16,24}) | Lean-verified |
| HW distribution | {0:1, 8:759, 12:2576, 16:759, 24:1} | Exhaustive sweep |

---

## Change Log

| Version | Date | Change |
|---------|------|--------|
| v17.0 | 2026-08-06 | Initial pipeline: Bit-Ops substrate, 8 solvers, semantic goal layer |
| v17.1 | 2026-08-06 | Semantic goal-setting (Lingo vocabulary) |
| v17.2 | 2026-08-06 | GLM semantic core + LTM integration |
| v17.3 | 2026-08-06 | Growth layer (persistent state, broad CRG, learning analysis) |
| v17.4 | 2026-08-06 | Unified pipeline (all parts cooperating, CRG reasoning engine) |
| v17.5 | 2026-08-06 | Full GLM CRG (597 edges, 473 concepts, dynamic expansion) |
| v17.6 | 2026-08-06 | Sandbox verification + 36 ARC tasks |
| v17.7 | 2026-08-06 | Full 4,256-word vocabulary with real corpus-derived vectors |
| v17.8 | 2026-08-06 | GLM mind (propose → test → refine → commit), solvers as fallback |
| v17.9 | 2026-08-06 | Natural language reasoning + proposal refinement + conditional perception |
| v18 | 2026-08-06 | HexColour analogical reasoning (lattice addresses) |
| v19 | 2026-08-06 | Extended perception (marker, pattern, extraction, count) + threshold tuning |
| v20 | 2026-08-06 | Task-specific perception + puzzle variation |
| v21 | 2026-08-06 | GLM module integration (geometric compute, math atlas, physics, data_object) |
| v22 | 2026-08-06 | All 14 components generative (0 passive) |
| v23 | 2026-08-07 | 5-layer lattice perception (2Δv ∈ Λ₂₄) |
| v24 | 2026-08-07 | Imagination layer + puzzle variation + v37 crystallization/adversarial |
| v25 | 2026-08-07 | Gap word derivation + deliberative reasoning + applied imagination |
| v26 | 2026-08-07 | Sustained growth training (10 iterations, CRG past 3,000) |
| v27 | 2026-08-07 | Diverse puzzles (10 types, 50 tasks) + object/symmetry detection + fixed import paths |
| v28 | 2026-08-07 | GLM reasoning engine (observe → reason → propose), solvers as teachers |
| v29 | 2026-08-07 | UBP noise framework (face transforms + Golay snap → 100% noise_clean) |
| v30 | 2026-08-07 | Connected component solver + TGIC analyzer + continuous learning tracker |
| v31 | 2026-08-07 | 65 ARC tasks (40 new from arc_agi_15) + physics validator + CRG reasoning |
| v32 | 2026-08-07 | Self-contained pipeline (all solvers inline, Gray code, Symmetry Tax, 2Δv) |
| v33 | 2026-08-07 | Full GLM mind restored for ARC + self-contained diverse solvers |
| v34 | 2026-08-07 | Active CRG growth + 6 new puzzle types + simplicial face detection |
| v35 | 2026-08-07 | Final push: CRG past 4,000 + face reasoning + 5 more puzzle types |

---

## What's Next

1. **Full 400-task ARC set** — more training data for broader learning
2. **Simplicial face reasoning refinement** — use 2-simplices for higher-order inference
3. **Continuous learner integration** (GLM24) — co-occurrence learning from task patterns
4. **CRG target: 5,000 edges** — currently 4,015 (~50 more runs at current growth rate)
5. **ARC target: 30%+** on 65-task set (currently 23%)
6. **More puzzle variety** — continue adding new puzzle types for broader CRG growth
7. **Implement Layer 3** (adaptive resolution / MOG compression) for large grids
8. **Integrate full GLM.py chat()** for richer natural language reasoning
9. Keep the README.md chain connected and updated throughout the repository folders
