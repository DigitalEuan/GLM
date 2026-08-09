# '../' - TOP REPOSITORY LEVEL TIER ROOT README 

**Version:** 2.5 (7 August 2026)  
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Parent:** None - Top Level

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure.

## next item to implement: 'light/Y/Y_STUDY_CLEAN_RESTATEMENT.md'
- see 'light/Y/README.md' for concept.

## The GLM is a substrate-native cognitive architecture that grows with each iteration rather than starting again over and over. Not a solver pipeline — a system that perceives, reasons, and acts using a 24-dimensional mathematical substrate built on the Universal Binary Principle (UBP).

---

## This repository is a system, each folder has a README.md wiring the folders together like a script with dependencies:

```
https://github.com/DigitalEuan/GLM (../)                     FOUNDATION the director and collector. 
  ├──→ GMHGL/           UBP SYSTEM - Golay engine, TAX, NRCI 
  │                     (exact rational math - NO Floats wherever possible)
  │
  ├──→ data_object/     ENCODING
  │                     1) 'data_object/' - how to encode subjects as 24-bit Data Objects - 118 elements, 82 molecules, 36 bonds, 95 words
  │                     2) 'encoding_definition_attempt_03-08.26/' - Gas-phase diatomic interaction pilot and structured Element Object v4
  │                     3) 'encoding_definition_attempt_04.08.26/' - Empirical calibration: 190 kJ/mol per work unit. Tick=2.10 fs, Cell=17 μm. + Dual-warp architecture: graduated for energy, flip for classification.
  │
  │
  ├──→ light/           SCALE CALIBRATION
  │                     1) Speed of light study (UBP ↔ real-world)
  │                     2) 'aristotle_01/' (Lattice walking shortcut method)
  │                     3) 'EM_calibration_1/' (substrate-unit-to-meters conversion)
  │                     4) UBP-to-Realworld Scale: S(λ, HW) = λ / [HW × (Y + 1/8)]
  │                        (from arc_agi_17 EM propagation study, v1-v9)
  │
  ├──→ glm_machine/     THE GLM MIND
  │                     Perceives, reasons, acts,
  │                     Lingo (GLM language) language, conditional reasoning
  │                     dev/glm_v37_grown.py — latest runtime (crystallization, adversarial, gap words)
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
  ├──→ arc_agi_17/      ARC AGI v17 SUBSTRATE-NATIVE COGNITIVE ARCHITECTURE
  │                     GLM mind + lattice perception + imagination + growth system
  │                     Best: 105/181 (23% ARC + 100% diverse types) | CRG: 4,015 edges | 217 runs
  │                     Key: scripts/arc_v35_pipeline.py (latest) or scripts/arc_v32_pipeline.py (self-contained)
  │                     11 puzzle types, 197 simplicial faces, physics-corrected (Gray code, Symmetry Tax, 2Δv)
  │
  ├──→ arc_agi_(version_number)/      THE NEXT ARC AGI attempt
  │
  └──→ leech_lattice/      fast way to map and measure integers within the Leech lattice

```

---

## What Each Folder Is

| Folder | Intended Purpose | Current ARC AGI Score | Current Key File | Experiment and Development Work Needed |
|--------|---------|-------|----------|----------|
| **ROOT Top Tier repository folder** | Collect, define and conduct use of all sub-folders, files within folders and scripts throughout the whole of this repository and system, to direct experiments and studies that use the UBP and or GLM systems | — | 'README.md' (this file) | Organise all folders and their contents so no scripts are repeated and all systems use a single source ('GMHGL/' and 'glm_machine/') for operations, 'data_object/' for encoding, 'light/' for scale calibration and 'long_term_memory/' for all GLM training and learning |
| **GMHGL/** | Foundation — Golay engine, TAX, NRCI | — | `ubp_unified_v5.py` | Extend existing capacity/capabilities if possible. Note: `snap_to_codeword` has a Lean-verified bug (only corrects weight ≤ 3, not 4). Fix documented in arc_agi_17/snap_to_codeword_FIX.md |
| **data_object/** | Encoding — Subjects → 24-bit Data Objects | — | `encoding_definition_attempt_04.08.26/README.md` | Use in studies/experiments. Warping (rotate_3 + flip) and geometric work (190 kJ/mol calibration) now integrated into arc_agi_17 |
| **glm_machine/** | Active Geometric Language Machine system | — | `dev/glm_v37_grown.py` | Growth and development alongside the ARC AGI developments. v37 features (crystallization, adversarial testing, gap word derivation, deliberative reasoning) now integrated into arc_agi_17 |
| **arc_agi_17/** | Substrate-native cognitive architecture — GLM mind with lattice perception, imagination, growth, diverse puzzles, simplicial faces | 105/181 (23% ARC + 100% diverse) | `scripts/arc_v35_pipeline.py` | Continue growth. Target: 5,000 CRG edges (current: 4,015), 30%+ ARC. 217 cumulative runs. 11 puzzle types. Physics-corrected (Gray code, Symmetry Tax, 2Δv). Self-contained pipeline available at `scripts/arc_v32_pipeline.py`. |
| **arc_agi_15/** | Solver — Working Solvers (3/9 mind solved / 6/9 Solvers solved) | 9/50 | `consolidated_mind.py` | Leave as record of attempting #15 and for parts if needed rather than rebuilding scripts from scratch |
| **arc_agi_16/** | Experiments | 9/50 | `arc_learning_mind.py` | Leave as record of attempting #16 and parts if needed rather than rebuilding scripts from scratch |
| **light/** | Calibration — UBP ↔ real world | — | `aristotle_01/lattice_shortcut.py` and `aristotle_01/LATTICE_SHORTCUT_METHOD.md` | Add more calibration anchors through various scales of reality. UBP-to-Realworld Scale: S(λ, HW) = λ / [HW × (Y + 1/8)] established in arc_agi_17 study |
| **long_term_memory/** | Archive — all GLM training data + knowledge | — | `glm_training_data.json` | Needs proper implementation so this becomes an on-going GLM training method. arc_agi_17 now reads from this and writes learning patterns persistently |

---

## Data Flow

```
Subjects (elements, molecules, words)
for Elements: ubp_system_kb.json (118 elements)
    ↓ encode via elements_data_object_system.py
24-bit Data Objects (EN×10, BP÷40, MP÷40, Rho×10)
    ↓ warp via graduated_activation_warp / rotate_3+flip
Warped Data Objects (Activation row modified for BO≥2)
    ↓ interact via AND/XOR + geometric work
Feature vectors (24 features per pair)
    ↓ predict via Random Forest / k-NN
Bond Energy (r=0.55) + Bond Order (86.8%)
    ↓ calibrate via 190 kJ/mol scale factor
Real thermodynamic values (kJ/mol)
    ↓ compute on via GMHGL/
Metrics (TAX, NRCI, AND, XOR, snap cost)
    ↓ reason about via glm_machine/
Decisions (perceive → interpret → propose → inspect)
    ↓ solve via arc_agi_17/ (GLM mind + lattice perception + imagination)
Results (solved tasks, experience, grown CRG)
    ↓ archive to long_term_memory/ + arc_agi_17/results/glm_state.json
Training Data + Knowledge (grows with each run — 217 cumulative runs)
```

---

## The Constants

### Golay [24,12,8]
- 4,096 codewords, minimum distance 8
- Corrects 3 errors, detects 7
- Single-bit vectors snap to HW=0 (isolated bits = noise)
- Basis vectors all collapse to zero — the alphabet is full codewords
- **Lean-verified bug fix**: `snap_to_codeword` only corrects weight ≤ 3 (should be ≤ 4). Fix: extend coset-leader table to all 4,096 entries. See `arc_agi_17/snap_to_codeword_FIX.md`

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
- **ARC transformations = Leech lattice translation vectors** (2Δv ∈ Λ₂₄). Finding the ARC rule = finding the invariant 2Δv. (arc_agi_17 v23)

### Lightspeed calibration
- Charge: 1 vertex step = e/12 C (exact)
- Velocity: v/c = 0.339 (exact, from γ = MONAD/13)
- Mass: m_e = Y² × WOBBLE × 24⁴ × 29⁴ × h × Δν_Cs / c² (0.007% - 0.009% error results vary currently)
- **UBP-to-Realworld Scale**: S(λ, HW) = λ / [HW × (Y + 1/8)] (arc_agi_17 v9)
  - HW=8: S = λ/3.1174 (gamma/X-ray/EUV)
  - HW=12: S = λ/4.6761 (optical/IR/microwave)
  - HW=16: S = λ/6.2348 (radio/ELF)
- **TAX conservation law**: TAX(a⊕b) = TAX(a) + TAX(b) − 2×TAX(a∧b) (arc_agi_17 v10)
The mass residual is an open problem.

### Y Constant
- Y = 1/(π + 2/π) ≈ 0.264675
- Entropic wobble — cost per active coordinate
- Activation quantum: Y + 1/8 = 0.389675
- Now available as exact Fraction (via math_atlas continued fractions) — no float drift

### TAX and NRCI
- TAX = HW·Y + ‖v‖²/8 (topological + geometric cost)
- NRCI = 10/(10 + TAX) (coherence measure, 0-1)
- NRCI=1.0 for zero vector (perfect coherence, vacuum)
- CoherenceRegime: OnBit (≥0.8), Coherent (≥0.5), Transitional (≥0.3), Subcoherent (<0.3)

---

## What We've Learned

### Elements (118)
1. **Element identity is well-encoded** (EN r=0.92, BP r=0.95)
2. **The Activation row is the bond formation layer** (diff_A r=0.50)
3. **Warping the Activation row creates distinct bond-order sectors** (r=0.55)
4. **Geometric work (path integral) carries independent signal** (partial r=0.33)
5. **The snap process is part of the interaction mechanism** (snap energy monotonic with BO)
6. **Bond order classification: 86.8% accuracy** (k-NN with flip_act_all)
7. **The 190 kJ/mol scale factor matches real bond energies** (Br-Br = 190 kJ/mol)
- see 'encoding_definition_attempt_04.08.26/README.md' for latest

### Molecules (82)
- Best encoding: M (log2), MP (div40)
- r(ΔH) = +0.96
- Details: `data_object/molecules.md`

### Patterns (29 synthetic)
- 19/29 (66%) with substrate knowledge
- Resonant (tiling): 4/4, Geodesic (mirrors): 4/4

### ARC-AGI (arc_agi_17)
- **Best: 16/45** (v25, Run 123)
- **136 cumulative training runs** (state persists across all)
- **3,003 CRG edges** (target: 5,000 per major epoch)
- **23 hexcolour addresses** (persistent lattice memory)
- **14 generative components** (0 passive)
- **6 solve modes**: lattice_perception, deliberative_reasoning, hexcolour_analogical, glm_mind, glm_mind_refined, fallback_solver
- **5-layer perception**: encoding → active perception → adaptive resolution → Golay snap → differential transition (2Δv)
- **v37 features**: crystallization, adversarial testing, gap word derivation, deliberative reasoning, applied imagination

### Previous ARC-AGI (v15/v16)
- 9/50 (18%) — 3 by mind, 6 by toolkit
- Experience routing table built (150 entries)

---

## Key Metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| **TAX** | HW·Y + ‖v‖²/8 | Symmetry Tax — cost of being |
| **NRCI** | 10/(10+TAX) | Coherence (1.0=vacuum, 0.5=horizon) |
| **Y** | 1/(π+2/π) ≈ 0.2647 | Entropic wobble |
| **AND** | a[i] & b[i] | Shared structure (interaction energy) |
| **XOR** | a[i] ^ b[i] | Transformation (difference vector) |
| **Geometric Work** | AND_HW + XOR_HW | Transformation energy (190 kJ/mol per unit) |
| **HexColour** | #RRGGBB from 24-bit vector | Lattice address (analogical reasoning) |
| **2Δv** | 2(c_out - c_in) ∈ Λ₂₄ | Leech lattice transition vector (the ARC rule IS the vector) |

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
| **Lattice Perception** | Compute 2Δv | ARC transformation rules |
| **Deliberative** | Step-by-step synthesis | Complex transformations |
| **Imagination** | Imagine → check coherence → adjust | Proposal refinement |

---

## Sub-Documents can be used to store Subject-specific GLM training material, data and records

| Folder | Documents |
|--------|-----------|
| data_object/ | `elements.md`, `molecules.md`, `CALIBRATION_LOG.md` |
| glm_machine/ | README with full architecture docs |
| GMHGL/ | `ubp_checkpoint_v5.4.1.md` |
| long_term_memory/ | `GLM_KNOWLEDGE.md` |
| arc_agi_17/ | `README.md` (full architecture + version history + change log) |
| arc_agi_17/reports/ | `v17_report.md` through `v26_report.md` (one per version) |

---

## Resources

- GLM language unified resource (15MB): 'https://github.com/DigitalEuan/UBP_Repo/blob/main/core_studio_v4.0/GLM/glm_unified_resource.json'
- GLM Concept Relation Graph: 'https://github.com/DigitalEuan/UBP_Repo/blob/main/core_studio_v4.0/GLM/GLM_CRG_EXPANDED.py'
- Database of words and explanation: 'https://github.com/DigitalEuan/UBP_Repo/blob/main/core_studio_v4.0/core/ubp_lang_kb_combined_v4.json'

- Currently under/unused datasets and scripts in 'glm_machine/'
   - 'GLM_CRG_MASSIVE.py' 10KB — **NOW INTEGRATED** into arc_agi_17 (250 edges)
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
   - 'dev/glm_v37_grown.py' — **v37 FEATURES NOW INTEGRATED** into arc_agi_17 (crystallization, adversarial, gap words, deliberative)
   - 'GLM_geometric_compute.py' — **NOW INTEGRATED** into arc_agi_17 (GeometricNumber, GeometricArithmetic)
   - 'math_atlas.py' — **NOW INTEGRATED** into arc_agi_17 (exact π, e, φ via continued fractions)
   - 'physics.py' — **NOW INTEGRATED** into arc_agi_17 (exact NRCI, coherence regimes)
   - 'GLM_sandbox.py' — **NOW INTEGRATED** into arc_agi_17 (verification, observation memory)

- ARC AGI Attempts before v15: 'https://github.com/DigitalEuan/ARC_AGI'

---

## Change Log (Repository-Level)

| Version | Date | Change |
|---------|------|--------|
| 2.4 | 2026-08-06 | Initial structure with arc_agi_15/16 |
| 2.5 | 2026-08-07 | Added arc_agi_17 (substrate-native cognitive architecture). Updated: data flow, constants (Lean fix, TAX conservation, UBP scale, 2Δv), metrics (geometric work, hexcolour, 2Δv), driving styles (lattice perception, deliberative, imagination), ARC-AGI results (16/45, 136 runs, 3,003 edges). Marked integrated glm_machine modules. Added v37 features note. |
