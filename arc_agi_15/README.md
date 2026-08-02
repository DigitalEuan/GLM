# ARC_AGI — UBP/GLM Experiments

**Author:** E. R. A. Craig  
**Date:** 31 July 2026  
**Score:** 9/50 (18%) on ARC-AGI-2 training subset

---

## What This Is

A substrate-native cognitive architecture for ARC-AGI, built on the Universal Binary Principle (UBP) and the Geometric Language Model (GLM). Not a solver pipeline — a mind that perceives, reasons, and acts using the 24D Leech lattice as its computational substrate.

## The Architecture

```
PERCEIVE (4 MOG channels)
    │
    ▼
INTERPRET (task type, complexity, colour semantics)
    │
    ▼
PROPOSE (multiple strategies ranked by confidence)
    │
    ▼
INSPECT (verify on train pairs — hard gate, sacred)
    │
    ▼
SOLVED (best verified proposal)
```

## Current Score: 9/50 (18%)

| Task | Solver | How the Mind Solved It |
|---|---|---|
| `00dbd492` | toolkit_interior | Enclosed region fill |
| `1e0a9b12` | **settlement_gravity** | Mind detected gravity from train pairs |
| `396d80d7` | toolkit_distance | Minkowski distance rule |
| `45737921` | **settlement_cell_rules** | Mind learned per-cell context rules |
| `54d82841` | toolkit_center | Object centre projection |
| `575b1a71` | toolkit_col_rank | Column rank fill |
| `a85d4709` | toolkit_marker | Marker fill |
| `ae58858e` | **conditional_size_threshold** | Mind induced: `CHARGE_SWAP(2→6) IF NODE_CARDINALITY ≥ 4` |
| `e48d4e1a` | toolkit_cross | Cross shift by markers |

**3 tasks solved by the mind itself** (settlement dynamics + conditional reasoning).  
**6 tasks solved by toolkit solvers** (v064 heritage).

## Key Components

### The Mind (substrate_mind.py)
The core cognitive architecture. Learns settlement dynamics from train pairs (Y-observations), predicts equilibrium for test input, verifies on train pairs.

### Conditional Reasoning (conditional_lobe.py)
The mind induces conditional transformation patterns and expresses them in Lingo:
```
CHARGE_SWAP(2→6) IF NODE_CARDINALITY ≥ 4
"change colour 2 to 6 only for components with size ≥ 4"
```

### Semantic Layer (semantic_layer.py)
The mind's inner monologue in UBP-Lingo. Describes what it sees, what changed, and what needs to happen.

### Reasoning Loop (reasoning_loop.py)
The complete cognitive cycle: PERCEIVE → GOAL → GAP → PROPOSE → INSPECT.

### Geometric Perception (geometric_perception.py)
Objects as polygons with UBP properties (node_count, circumradius, NRCI). Grounded in the lightspeed study calibration.

### Lightspeed Calibration (ubp_calibration_engine.py)
UBP-to-Reality scale from the 20-phase study:
- Charge: 1 vertex step = e/12 (exact)
- Velocity: v/c = 0.339 (exact)
- Mass ratio: m_μ/m_e = 169/WOBBLE (0.03%)
- Mass: m_e via Y²×WOBBLE×24⁴×29⁴×h×Δν_Cs/c² (0.007%)

## The Y-Observer Connection

Train pairs are Y-observations: the observer (Y constant) makes a copy of the perturbation→equilibrium path. Each observation costs Y per active bit. The mind learns by observing how the substrate settles from perturbation to equilibrium.

```
Substrate starts perfect (lowest TAX)
    → Input disturbs it (increases TAX)
    → Output is equilibrium (lowest achievable TAX)
    → Mind learns by observing perturbation→equilibrium pairs
```

## Synthetic Tests: 7/9 Pass

| Test | Result | Solver |
|---|---|---|
| Gravity | ✓ | settlement_gravity |
| Recolour | ✓ | settlement_cell_rules |
| Fill | ✓ | settlement_colour_map |
| Component conditional | ✓ | settlement_cell_rules |
| Size crop | ✗ | (no size-change dynamics) |
| Neighbour identity | ✓ | settlement_gravity |
| Shift right | ✗ | (positional, not context-dependent) |
| Colour flip | ✓ | settlement_cell_rules |
| Border fill | ✓ | settlement_cell_rules |

## How to Run

```bash
# The reasoning loop (complete cognitive cycle)
python3 reasoning_loop.py

# The substrate mind (settlement dynamics)
python3 substrate_mind.py

# Synthetic validation tests
python3 substrate_test.py

# The consolidated mind (all styles)
python3 consolidated_mind.py

# Lightspeed calibration
python3 ubp_calibration_engine.py

# Single task explanation
python3 reasoning_loop.py  # (edit main() to target specific task)
```

## File Map

```
├── reasoning_loop.py          ← The mind's complete cognitive cycle
├── substrate_mind.py          ← Settlement dynamics + prediction
├── conditional_lobe.py        ← Conditional reasoning in Lingo
├── semantic_layer.py          ← Lingo descriptions + consistency checks
├── geometric_perception.py    ← Objects as polygons (spatial_arithmetic)
├── ubp_calibration_engine.py  ← Lightspeed study calibration
├── substrate_test.py          ← Synthetic validation tests (9 tests)
├── consolidated_mind.py       ← All driving styles + toolkit
├── mog_mind.py                ← Earlier iteration
├── mog_attention_learner.py   ← MOG-attention over train pairs
├── mog_attention.py           ← First attempt (superseded)
├── mog_transformer.py         ← MOG-as-attention transformer
├── v065_ubp_glm.py            ← Extended solver set
├── v064_ubp_glm_operational.py← Original operational system
├── v062_unified_learning.py   ← Unified learning system
├── v032_distance_rule.py      ← Distance rule solver
├── spatial_arithmetic.py      ← Geometric arithmetic codec
├── lingo/                     ← GLM language system
│   ├── geometric_translator.py
│   ├── lingo_translator.py
│   └── lingo_chat.py
├── arc_loader/                ← ARC task loader
├── data/training/             ← 50 ARC training tasks
├── REPORTS/                   ← Benchmark reports
├── LIGHTSPEED_STUDY_SYNTHESIS.md  ← 20-phase study synthesis
├── SUBSTRATE_MIND_STATE.md    ← Current state documentation
├── MOG_MIND_STATE.md          ← Architecture documentation
├── METHODS_TRIED.md           ← What was tried and what worked
├── EXPERIMENT_TRACKER.md      ← Experiment history
└── ubp_study_package/         ← Lightspeed study (20 phases)
    ├── scripts/
    ├── reports/
    └── source_documents/
```

## What's Next

1. **Further Development:** - see 'FOR_USER_v065.md'
2. **Experience accumulation** — the mind should learn from failed proposals and remember why they failed
3. **Size-change dynamics** — the mind needs to handle crop/pad/tile
4. **Position-dependent rules** — cell rules that depend on absolute position, not just context
5. **Conditional colour maps** — detect when a colour map is conditional (only some cells change)
6. **Geometric perception integration** — use spatial_arithmetic for object-level understanding
7. **More Lingo operations** — expand the vocabulary of operations the mind can propose
8. **Address the "unused GLM modules" problem** named in METHODS_TRIED.md section E — lingo chat, geometric translator, and HDRB are described as producing reasoning traces but not driving candidate generation.

## License

MIT.
