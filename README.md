# TOP REPOSITORY LEVEL TIER ROOT README 

**Version:** 2.2 (3 August 2026)  
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Parent:** None - Top Level

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- A substrate-native cognitive architecture. Not a solver pipeline — a system that perceives, reasons, and acts using a 24-dimensional mathematical substrate built on the Universal Binary Principle (UBP).

---

## This repository is a system, each folder has a README.md wiring the folders together like a script with dependencies:

```
https://github.com/DigitalEuan/GLM (../)                     FOUNDATION the director and collector. 
  ├──→ GMHGL/           UBP SYSTEM - Golay engine, TAX, NRCI 
  │                     (exact rational math - NO Floats wherever possible)
  │
  ├──→ data_object/     ENCODING
  │                     How to encode subjects as 24-bit Data Objects
  │                     118 elements, 82 molecules, 36 bonds, 95 words
  │
  ├──→ light/           SCALE CALIBRATION
  │                     Speed of light study (UBP ↔ real-world)
  │
  ├──→ glm_machine/     THE GLM MIND
  │                     Perceives, reasons, acts,
  │                     Lingo (GLM language) language, conditional reasoning
  │
  ├──→ long_term_memory/   THE GLM MEMORY
  │                        glm_training_data.json (all GLM training data)
  │                        GLM_KNOWLEDGE.md (all GLM knowledge from training)
  │     
  ├──→ arc_agi_15/      ARC AGI v15 SOLVER EDITION 
  │                     Leaves off at 'FOR_USER_v065.md'
  │          
  ├──→ arc_agi_16/      ARC AGI v16 EXPERIMENTS EDITION 
  │                     Focussed on training the GLM, perhaps doesn't use this system well
  │
  └──→ arc_agi_(version_number)/      THE NEXT ARC AGI attempt

```

---

## What Each Folder Is

| Folder | Intended Purpose | Current ARC AGI Score | Current Key File | Experiment and Development Work Needed |
|--------|---------|-------|----------|----------|
| **ROOT Top Tier repository folder** | Collect, define and conduct use of all sub-folders, files within folders and scripts throughout the whole of this repository and system, to direct experiments and studies that use the UBP and or GLM systems | — | 'README.md' (this file) | Organise all folders and their contents so no scripts are repeated and all systems use a single source ('GMHGL/' and 'glm_machine/') for operations, 'data_object/' for encoding, 'light/' for scale calibration and 'long_term_memory/' for all GLM training and learning |
| **GMHGL/** | Foundation — Golay engine, TAX, NRCI | — | `ubp_unified_v5.py` | Extend existing capacity/capabilities if possible |
| **data_object/** | Encoding — Subjects → 24-bit Data Objects | — | `encoding_specification.md` | Find best Data-Object encoding for every Subject Domain, develop encoding strategy, refine and define Data Object encoding |
| **glm_machine/** | Active Geometric Language Machine system | — | `GLM11_runtime.py` | Growth and development alongside the ARC AGI developments |
| **arc_agi_(version_number)/** | running attempts at ARC AGI | Running Score | README.md | Operating the UBP + GLM systems through the correct pipeline in full, trying various experiments to solve ARC AGI challenges as well as a range of tests/challenges to widen the problem-solving abilities of the natural system through training MOG grids with yes/no feedback loop, to avoid using Solvers to find solutions - rather the aim is to enable the UBP-GLM systems to gain understanding through structured and calibrated input then calculating solutions natively. Future editions need to use scripts from the 'GMHGL/'' and 'data_object/' folders/systems and consolidate training/knowledge |
| **arc_agi_15/** | Solver — Working Solvers (3/9 mind solved / 6/9 Solvers solved) | 9/50 | `consolidated_mind.py` | Leave as record of attempting #15 and for parts if needed rather than rebuilding scripts from scratch |
| **arc_agi_16/** | Experiments — next iteration | 9/50 | `arc_learning_mind.py` | Leave as record of attempting #16 and parts |
| **light/** | Calibration — UBP ↔ real world | — | `reports/` | More experimenting to try to derive the Speed of Light, more calibration anchors through various scales of reality |
| **long_term_memory/** | Archive — all GLM training data + knowledge | — | `glm_training_data.json` | Needs proper implementation so this becomes an on-going GLM training method to save re-training the GLM each iteration, refinement and formalisation of structure, further training, building and benchmarking |

---

## Data Flow

```
Subjects (elements, molecules, words)
    ↓ encode via data_object/
Data Objects (24-bit vectors in Leech space)
    ↓ compute on via GMHGL/
Metrics (TAX, NRCI, AND, XOR, snap cost)
    ↓ reason about via glm_machine/
Decisions (perceive → interpret → propose → inspect)
    ↓ solve via arc_agi_(version number)
Results (solved tasks, experience)
    ↓ archive to long_term_memory/
Training Data + Knowledge (grows with each run)
```

---

## The Constants

### Golay [24,12,8]
- 4,096 codewords, minimum distance 8
- Corrects 3 errors, detects 7
- Single-bit vectors snap to HW=0 (isolated bits = noise)
- Basis vectors all collapse to zero — the alphabet is full codewords

### MOG (Miracle Octad Generator)
- 4×6 grid: 4 rows (Reality, Info, Activation, Potential) × 6 columns
- Each row is 6 bits (Gray-coded, values 0-63)
- Projects 24D to 2D for observation
- Row 0 (Reality) has widest blast radius (11 bits per toggle)

1. Domain: Bits 0-2 (Prefix)
2. Volume: Bits 3-7 (Voxel Count, Gray Coded)
3. Compactness: Bits 8-11 (Surface Area Proxy, Gray Coded)
4. Parity: Bits 12-23 (Golay [24,12,8])

### Leech Lattice (Λ₂₄)
- 196,560 minimal vectors, all norm²=32
- Class A: 1,104 (HW=2, NRCI=0.688)
- Class B: 97,152 (HW=8, NRCI=0.620)
- Class C: 98,304 (HW=24, NRCI=0.491)

### Y Constant
- Y = 1/(π + 2/π) ≈ 0.264675
- Entropic wobble — cost per active coordinate
- Activation quantum: Y + 1/8 = 0.389675

### TAX and NRCI
- TAX = HW·Y + ‖v‖²/8 (topological + geometric cost)
- NRCI = 10/(10 + TAX) (coherence measure, 0-1)
- NRCI=1.0 for zero vector (perfect coherence, vacuum)

---

## What We've Learned

### Elements (118)
- Best encoding: EN×10, BP÷40, MP÷40, Rho×10
- r(ΔH) = −0.91 (enthalpy prediction)
- Noble gases = vacuum state (HW=0, NRCI=1.0)
- Details: `data_object/elements.md`

### Molecules (82)
- Best encoding: M (log2), MP (div40)
- r(ΔH) = +0.96
- Details: `data_object/molecules.md`

### Bonds (36)
- AND encoding: r(BE) = +0.90 with NRCI × bond_order
- Cross-validated: mean R = 0.82

### Patterns (29 synthetic)
- 19/29 (66%) with substrate knowledge
- Resonant (tiling): 4/4, Geodesic (mirrors): 4/4

### ARC-AGI (50 tasks)
- 9/50 (18%) — 3 by mind, 6 by toolkit
- Experience routing table built (150 entries)

---

## Key Metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| **TAX** | HW·Y + ‖v‖²/8 | Symmetry Tax — cost of being |
| **NRCI** | 10/(10+TAX) | Coherence (1.0=vacuum, 0.5=horizon) |
| **Y** | 1/(π+2/π) ≈ 0.2647 | Entropic wobble |
| **AND** | a[i] & b[i] | Shared structure |

---

## Driving Styles

| Style | Goal | Best For |
|-------|------|----------|
| Machining | Minimise TAX | High noise |
| Resonant | Maximise NRCI | Patterns, tiling |
| Differential | Minimise Δ | Movement, colour |
| Geodesic | Shortest path | Rotation, reflection |
| Entropic | Equilibrium | Simplification |
| Flow | Vector field | Expansion, fill |

---

## Sub-Documents can be used to store Subject-specific GLM training material, data and records

| Folder | Documents |
|--------|-----------|
| data_object/ | `elements.md`, `molecules.md`, `CALIBRATION_LOG.md` |
| glm_machine/ | README with full architecture docs |
| GMHGL/ | `ubp_checkpoint_v5.4.1.md` |
| long_term_memory/ | `GLM_KNOWLEDGE.md` |

---

## Resources

- GLM language unified resource (15MB): 'https://github.com/DigitalEuan/UBP_Repo/blob/main/core_studio_v4.0/GLM/glm_unified_resource.json'
- GLM Concept Relation Graph: 'https://github.com/DigitalEuan/UBP_Repo/blob/main/core_studio_v4.0/GLM/GLM_CRG_EXPANDED.py'
- Database of words and explanation: 'https://github.com/DigitalEuan/UBP_Repo/blob/main/core_studio_v4.0/core/ubp_lang_kb_combined_v4.json'

- Currently under/unused datasets and scripts in 'glm_machine/'
   - 'GLM_CRG_MASSIVE.py' 10KB
   - 'GLM15_physics_pack.py' 33KB - physics definitions
   - 'color_space_data.json' 183KB
   - 'corpus.txt' 500KB chat conversation for language training
   - 'glm_learned_state.json' 12KB
   - 'GLM21_generator.py' - GENERATION loop — it produces novel sequences, not just recalled templates.
   - 'GLM22_ontological_grammar.py' - UBP ontological layers (Reality, Information, Activation, Potential) map to grammatical categories:
1. Reality    (M_*)  → NOUN      (concrete things that exist)
2. Information (I_*) → ADJECTIVE  (relational qualities)
3. Activation (A_*)  → VERB       (processes, actions)
4. Potential  (P_*)  → OPERATOR   (logical/abstract relations)
   - 'GLM39_agent_loop.py'
   - 'golden_cases.json' 13KB
   - 'idea_meta_graph.json' 77KB

- ARC AGI Attempts before v15: 'https://github.com/DigitalEuan/ARC_AGI'

