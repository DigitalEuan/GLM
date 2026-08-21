# '../' - TOP REPOSITORY LEVEL TIER ROOT README 

**Version:** 2.7 (20 August 2026)  
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Parent:** None - Top Level

## UPDATE THIS README
if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure.

## next item to implement: 
'light/aristotle_01/Y_STUDY_CLEAN_RESTATEMENT.md'

## The GLM is a substrate-native cognitive architecture. 
It grows with each iteration rather than starting again over and over. Not a solver pipeline — a system that perceives, reasons, and acts using a 24-dimensional mathematical substrate built on the Universal Binary Principle (UBP).

---

## This repository is a system 
each folder has a README.md wiring the folders together like a script with dependencies:

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
  │                     2) 'aristotle_01/' - Lattice walking shortcut method + Lean4 verified UBP including 'Y' constant, Symmetry TAX, NRCI +
  │                     3) 'EM_calibration_1/' (substrate-unit-to-meters conversion)
  │                     4) UBP-to-Realworld Scale: S(λ, HW) = λ / [HW × (Y + 1/8)]
  │                        (from arc_agi_17 EM propagation study, v1-v9)
  │                     5) light/aristotle_01/Y_STUDY_CLEAN_RESTATEMENT.md - Lean4 verified Y, TAX, NRCI +
  │
  ├──→ glm_machine/     THE GLM MIND
  │                     Perceives, reasons, acts,
  │                     Lingo (GLM language) language, conditional reasoning
  │                     dev/glm_v37_grown.py — latest runtime (crystallization, adversarial, gap words)
  │
  ├──→ glm_lean/        LEAN-VERIFIED GLM (3 generations)
  │                     GLM-1: 43 claims, integer exponents, Golay/MOG carrier
  │                     GLM-2: 58 claims, rational exponents, Leech carrier, Co₀
  │                     GLM-3: 64 claims, full Griess algebra (196,884 dims), Monster
  │                     Each: paper + reasoner + Lean 4 proofs (no sorry)
  │
  ├──→ glm_universal/        collective active version for development/growth
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
  ├──→ leech_lattice/      fast way to map and measure integers within the Leech lattice
  │
  └──→ CATALOG.md          full repository catalog (all files, all folders 20.08.26)

```

---

## What Each Folder Is

| Folder | Intended Purpose | Current ARC AGI Score | Current Key File | Experiment and Development Work Needed |
|--------|---------|-------|----------|----------|
| **ROOT Top Tier repository folder** | Collect, define and conduct use of all sub-folders, files within folders and scripts throughout the whole of this repository and system, to direct experiments and studies that use the UBP and or GLM systems | — | 'README.md' (this file) | Organise all folders and their contents so no scripts are repeated and all systems use a single source ('GMHGL/' and 'glm_machine/') for operations, 'data_object/' for encoding, 'light/' for scale calibration and 'long_term_memory/' for all GLM training and learning |
| **GMHGL/** | Foundation — Golay engine, TAX, NRCI | — | `ubp_unified_v5.py` | Extend existing capacity/capabilities if possible. Note: `snap_to_codeword` has a Lean-verified bug (only corrects weight ≤ 3, not 4). Fix documented in light/EM_calibration_1/reports/snap_to_codeword_FIX.md |
| **data_object/** | Encoding — Subjects → 24-bit Data Objects | — | `encoding_definition_attempt_04.08.26/README.md` | Use in studies/experiments. Warping (rotate_3 + flip) and geometric work (190 kJ/mol calibration) now integrated into arc_agi_17 |
| **glm_machine/** | Active Geometric Language Machine system | — | `dev/glm_v37_grown.py` | Growth and development alongside the ARC AGI developments. v37 features (crystallization, adversarial testing, gap word derivation, deliberative reasoning) now integrated into arc_agi_17 |
| **arc_agi_17/** | Substrate-native cognitive architecture — GLM mind with lattice perception, imagination, growth, diverse puzzles, simplicial faces | 105/181 (23% ARC + 100% diverse) | `scripts/arc_v35_pipeline.py` | Continue growth. Target: 5,000 CRG edges (current: 4,015), 30%+ ARC. 217 cumulative runs. 11 puzzle types. Physics-corrected (Gray code, Symmetry Tax, 2Δv). Self-contained pipeline available at `scripts/arc_v32_pipeline.py`. |
| **arc_agi_15/** | Solver — Working Solvers (3/9 mind solved / 6/9 Solvers solved) | 9/50 | `consolidated_mind.py` | Leave as record of attempting #15 and for parts if needed rather than rebuilding scripts from scratch |
| **arc_agi_16/** | Experiments | 9/50 | `arc_learning_mind.py` | Leave as record of attempting #16 and parts if needed rather than rebuilding scripts from scratch |
| **light/** | Calibration — UBP ↔ real world | — | `aristotle_01/lattice_shortcut.py` and `aristotle_01/LATTICE_SHORTCUT_METHOD.md`, 'Y_STUDY_CLEAN_RESTATEMENT.md' | Add more calibration anchors through various scales of reality. UBP-to-Realworld Scale: S(λ, HW) = λ / [HW × (Y + 1/8)] established in arc_agi_17 study |
| **long_term_memory/** | Archive — all GLM training data + knowledge | — | `glm_training_data.json` | Needs proper implementation so this becomes an on-going GLM training method. arc_agi_17 now reads from this and writes learning patterns persistently |
| **glm_lean/** | Lean-verified GLM — 3 generations of exact composable meaning on a lattice carrier | — | `glm3/glm3_paper.py` | Independent verification of GLM concepts via Lean 4 + Mathlib proofs (no sorry). GLM-1 (43 claims), GLM-2 (58 claims), GLM-3 (64 claims, full Griess algebra). See `CATALOG.md` for full file listing. |

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

| Structural term | Symbol | Type | Operational meaning |
|---|---|---|---|
| Perfect space | `0` | pattern | no active coordinate |
| Zero vector | `0` | pattern | no disturbance, no information |
| Raw information | `v` | `Fin n → ℤ` | an integer pattern on `n = 24` coordinates |
| Primitive difference "2" | `Δ` | `ℝ` = 2 | the numerator of the read operator |
| Capacity / zone-share | `Z★` | `ℝ` = 1/8 | cost of occupying a permitted zone |
| Body | 24 coordinates | index set | the coordinate space |
| Loop-check (numeric) | `Π` | `ℝ` = π | the argument of the read operator |
| Loop-check (structural) | `σ(v)` | 12 bits | the Golay syndrome |
| Not-quite-closed loop | `σ(v) ≠ 0` | — | history, gap, syndrome |
| MOG | nearest-codeword reading | — | the grammar that turns a pattern into a lawful one |
| Golay | `[24,12,8]` code | — | protection: minimum distance 8 |
| Leech | `Λ₂₄` | — | embodiment: the 24-dimensional geometry |
| Observer / read quantum | `Y` | `ℝ` | `1/(π + 2/π) = 0.2646754…` |
| Activation quantum | `Q` | `ℝ` | `Y + 1/8 = 0.3896754…` |
| TAX | `TAX(v)` | `ℝ` | `HW(v)·Y + ‖v‖²/8` |
| Coherence budget | `B` | `ℝ` = 10 | the unit in which tax is measured |
| NRCI | `NRCI(v)` | `ℝ` | `B/(B + TAX(v))` |
| CoherenceRegime | one of four | — | a band of `NRCI`, equivalently of `TAX` |

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

### (π calibrated) Y Constant
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
- **Best: 105/181** (v35, 23% ARC + 100% diverse types)
- **217 cumulative training runs** (state persists across all)
- **4,015 CRG edges** (target: 5,000 per major epoch)
- **66 hexcolour addresses** (persistent lattice memory)
- **197 simplicial faces** (2-simplices in CRG)
- **14 generative components** (0 passive)
- **11 puzzle types** (ARC + 10 diverse: symmetry, border, colour_cascade, conditional_region, connected_component, count_encode, diagonal, noise_clean, object_gravity, pattern_tile)
- **6 solve modes**: lattice_perception, deliberative_reasoning, hexcolour_analogical, glm_mind, glm_mind_refined, fallback_solver
- **5-layer perception**: encoding → active perception → adaptive resolution → Golay snap → differential transition (2Δv)
- **v37 features**: crystallization, adversarial testing, gap word derivation, deliberative reasoning, applied imagination

### Older ARC-AGI (v15/v16)
- 9/50 (18%) — 3 by mind, 6 by toolkit
- Experience routing table built (150 entries)

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
| arc_agi_17/reports/ | `v17_report.md` through `v35_report.md` (one per version) |
| glm_lean/glm/ | `DEVELOPMENT_CATALOG.md`, `glm_paper.py` (43 claims verified) |
| glm_lean/glm2/ | `glm2_paper.py` (58 claims verified) |
| glm_lean/glm3/ | `glm3_paper.py` (64 claims verified) |

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
| 2.5 | 2026-08-07 | Added arc_agi_17 (substrate-native cognitive architecture). Updated: data flow, constants (Lean fix, TAX conservation, UBP scale, 2Δv), metrics (geometric work, hexcolour, 2Δv), driving styles (lattice perception, deliberative, imagination), ARC-AGI results. Marked integrated glm_machine modules. Added v37 features note. |
| 2.6 | 2026-08-10 | Added next_steps_from_7Aug26.md. Minor restructuring notes. |
| 2.7 | 2026-08-20 | Full repository catalog (CATALOG.md). Added glm_lean/ to tree and folder table. Updated ARC-AGI stats to v35 final (105/181, 217 runs, 4,015 edges, 66 hexcolour, 197 simplicial faces, 11 puzzle types). Verified all README cross-references. Fixed missing folder references. |
| 2.8 | 2026-08-21 | GLM 3+ (see below) - pulling the variosu parts of the GLM system into one clean operational directory 'glm_universal'

============================================
GLM 3+ 21 August 2026
============================================

# GLM: Repository Audit and Unified Reasoner

Audit of the GLM project (`https://github.com/DigitalEuan/GLM.git`) and
construction of `glm_core`, a unified multi-domain reasoner with exact
arithmetic and full mathematical tracing.

## Status

**Step 1 complete** - repository audited, all six defects (D1-D6) empirically
confirmed by executing the repository's own code.

**Step 2 complete** - `glm_core` built and verified: 8 modules, 96/96
architectural checks passing, all four reasoning domains behind one Three
Column Thinking interface. See [Step 2](#step-2---the-unified-glm_core-engine)
below.

**Step 3 complete** - benchmarked across all four domains against external
ground truth. Physics 18/18 and 16/16, chemistry 13/13 reactions, 65/65 real
ARC tasks ingested, 19/19 symbolic checks, 9/9 TCT scripts executing and
matching. One hypothesis was **refuted**: geometric work does not predict bond
dissociation energy (r^2 = 0.0011). See
[Step 3](#step-3---multi-domain-benchmark) below.

**Step 5 complete** - three targeted enhancements built and re-benchmarked.
Bond-energy prediction went from r^2 = -0.19 to **0.813 under leave-one-out
cross-validation**; the legacy Golay coordinate permutation was derived and
verified, taking silent corruptions **65 -> 0**; the spatial hypothesis class
widened 8 -> 35 candidates but **did not improve the ARC score** - a negative
result, reported as such. 107 new tests pass, no regressions. See
[Step 5](#step-5---algorithmic-hardening) below.

**Step 4 complete** - every Step 3 boundary traced to its algebraic cause.
`glm_core/tracing.py` records exact derivations; four diagnoses came out of it,
including a positive control proving the chemistry failure is the encoding
rather than the task, and the discovery that the legacy and unified Golay
constructions are **different subspaces**. See
[Step 4](#step-4---mathematical-traces-and-failure-diagnostics) below.

## Running

`uv` is not on the default `PATH` in this session; it lives in `.uvbin/`.
This is why the previous iteration produced no results: the scripts were never
successfully executed.

```bash
cd /app/sandbox/session_20260820_113734_a0d8466bd805
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/00_static_scan.py          # AST/static census -> data/
uv run python workflow/01_subsystem_audit.py      # subsystem audit    -> results/
uv run python workflow/02_defect_verification.py  # defect probes      -> results/
```

Total runtime is roughly three minutes, dominated by subprocess-isolated
imports of repository modules that do substantial work at import time.

## Layout

| Path | Contents |
|---|---|
| `workflow/GLM/` | Cloned repository, commit `92b8bad` |
| `workflow/00_static_scan.py` | AST scan: syntax errors, imports, side effects |
| `workflow/01_subsystem_audit.py` | Five-subsystem audit and Golay reference code |
| `workflow/02_defect_verification.py` | Empirical probes for the six flagged defects |
| `workflow/probes/` | Generated probe scripts, one per defect (regenerated each run) |
| `data/static_scan.json` | Raw static scan output |
| `results/step1_subsystem_audit.{json,md}` | Subsystem audit |
| `results/step1_defect_verification.{json,md}` | Defect verification |
| `results/claims.json` | Claim ledger - every headline number with its source |
| `logs/` | Execution logs |

## Repository scope

549 Python files, 294,266 lines across ten subsystems. Three files fail to
parse. Representative modules import cleanly at rates from 1.00 (`glm_3.1`)
down to 0.083 (`arc_agi_17`), the latter because 33 files import `ubp_engine`,
a module present neither in the repository nor on PyPI.

## Architectural gap analysis

The repository is a sequence of architectural generations that were **added
alongside** one another rather than superseding one another. Nothing was
retired, so several generations of the same primitive coexist and are selected
by whichever directory happens to be on `sys.path`. This is the single
structural fact behind five of the six defects below.

| ID | Defect | Status | Key measurement |
|---|---|---|---|
| D1 | Two incompatible Buckingham-Pi solvers | confirmed | Pi group counts differ on 2 of 6 quantity sets |
| D2 | Golay decoding beyond the correction radius | confirmed, and refined | w=4 fails safe; **w=5 silently miscorrects** |
| D3 | Competing NRCI formulations | confirmed | 5 implementations, 3 distinct values, one input |
| D4 | Bond-energy scale incoherence | confirmed | unitless work, no conversion constant defined |
| D5 | Unseeded sampling in wall distance | confirmed | 3 distinct values from 12 identical calls |
| D6 | Knowledge-base ingestion contract broken | confirmed | `AttributeError` at module import |

Supporting census across the 549 files: **113** functions defining an
NRCI-named metric, **45** symmetry-TAX definitions, **15** Pi/nullspace
solvers, **142** Golay-related definitions, **241** bare `except:` handlers,
and **8** `random.*` call sites in modules that never set a seed.

### Where the review's framing was refined by measurement

Two findings differ from the review's description, in both directions:

**D2 is worse than described, and at a different error weight.** Review flagged
weight >= 4 as silent degradation. Measurement separates two distinct
behaviours. At weight 4 the decoder fails *safe*: the syndrome is never in the
weight-<=3 table, so the input is returned unchanged with `corrected=False` in
200/200 trials - loud, detectable, and the nearest codeword is genuinely
ambiguous there (mean 6.0 codewords tie, consistent with covering radius 4). At
weight 5 the decoder fails *silently*: the coset leader has weight <= 3, so the
lookup succeeds and a valid codeword is returned with `corrected=True` in
200/200 trials, but it is the wrong codeword in 200/200. Weight 5, not weight
4, is where corruption is reported to callers as success.

Separately, the repository has *already* addressed the weight-4 case: it
documents the limitation as its own audit item B8 and ships `nearest_codeword`
and `decode_complete`, which return a codeword in 200/200 weight-4 trials. The
remaining gap is that the legacy `snap_to_codeword` is still the routine the
rest of the codebase calls.

**D1's mechanism is not the one described.** Review attributed the divergence
to Gauss-Jordan rational nullspace versus Smith normal form. The measured cause
is the axis basis: `glm2` carries 11 exponent components (10 axes plus scale)
including a separate angle axis, while `glm` uses 7-axis SI. The two engines
share their vocabulary - 17 of 18 quantity names resolve in both - but assign
different dimensions to the same name. Torque and energy are distinct under
`glm2` and identical under `glm`, so `{torque, energy, angle}` yields 1 Pi group
versus 2, and `{action, angular_momentum}` yields 0 versus 1. The four sets
built only from mechanical L/M/T quantities agree. Whether an angle axis is
carried is a modelling choice, not a bug, but the two choices cannot both feed
one reasoner.

### The remaining four

**D3.** One fixed 24-bit vector of Hamming weight 12, pushed through every
loadable NRCI implementation, returns values spanning 0.211 to 0.748 - a spread
of 0.537 across 5 implementations, 3 of them distinct. Two of the five return
exact `Fraction` values with ~60-digit numerators; a third returns a float.
Neither the name nor the return type identifies which formulation was applied.

**D4.** `geometric_work()` returns pure counts (Hamming steps, NRCI-weighted
sums; `total_work: 12.0` on the seeded probe trajectory). The module mentions
kJ/mol but defines no Avogadro or joule conversion constant. The step to
physical energy is taken in a sibling module by
`predicted_bond_strength = and_nrci_val * bond_order_proxy * 1000`. The gap is
a missing dimensional conversion, not an arithmetic error.

**D5.** Twelve repeated calls to `_compute_wall_distance` on one fixed vector
returned `[5, 3, 3, 3, 7, 5, 5, 5, 5, 3, 7, 7]` - 3 distinct values. The method
samples 300 of 4,096 codewords (7.3% of the space) with unseeded `random`. The
exhaustive minimum distance for that vector is 3; the sampled call matched it
in 4 of 12 attempts. The metric is therefore both irreproducible and biased
upward, since sampling can only ever miss the true nearest codeword.

**D6.** `ubp_system_kb.json` stores 752 records as positional lists against a
declared 8-field schema (`_fields`), while `ubp_kb_loader.py` indexes them as
dicts. The module calls `load_kb()` at import, so it raises
`AttributeError: 'list' object has no attribute 'get'` before any consumer runs.
A working `kb_adapter.py` that handles the list schema is already present in the
same directory and imports cleanly - the remediation path exists.

## Corrections made to the audit itself

The audit's own reference Golay construction was wrong in the previous
iteration. A bordered quadratic-residue circulant was used, and it produced a
code with minimum weight **7**, i.e. not the Golay code. It has been replaced
by the extended cyclic [23,12] construction from the generator polynomial,
which is validated by exhaustive enumeration to `d = 8`. The reference now
recovers 200/200 at error weights 1-3, 25/200 at weight 4 and 0/200 at weight
5, matching the theoretical bounded-distance limit of `floor((8-1)/2) = 3`.
This is what makes the repository's own minimum weight of 8 a cross-validated
rather than a single-source claim.

## Evidence and limits

- Every figure in `results/` is **computed** in a single run (Tier 1), except
  the Golay minimum weight of 8, which is **cross-validated**: derived once by
  the repository's `GolayCodeEngine` and once by this audit's independent
  cyclic construction, which agree.
- The audit harness is seeded (`random.Random(20260820)`), so re-running
  reproduces the same trial draws. That is a property of the harness, not
  evidence that the audited code is deterministic - D5 shows it is not.
- The import smoke test covers up to 12 representative modules per subsystem,
  not all 549 files. Import success rates are estimates over that sample.
- D3 reports only implementations that could be **instantiated and called**; 5
  of the 113 NRCI definition sites cleared that bar. The true spread across all
  113 is unmeasured and is very unlikely to be smaller.
- D5 demonstrates non-determinism within one process. Cross-process variation
  was not separately measured.
- D4 executes `geometric_work()` and inspects constants; the end-to-end
  bond-energy pipeline was **not** run to completion, so no predicted energy in
  kJ/mol is reported here and the ~1e42 figure quoted in review is **not**
  confirmed by this audit.
- The census matches function names via AST; a function implementing one of
  these concepts under an unrelated name is not counted.
- Symmetry-TAX, Griess algebra, CRG, dual-warp classification and the Lean
  bindings were located and counted but **not** numerically validated.
- No repository defect has been fixed. This step characterises the codebase;
  remediation belongs to later steps.

---

# Step 2 - The unified `glm_core` engine

A standalone package that consolidates the four reasoning domains behind one
interface and remediates each Step 1 defect at the architectural level.

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/03_test_unified_core.py   # 96 checks, ~1 min
```

| Module | Role | Remediates |
|---|---|---|
| `glm_core/linear_algebra.py` | Exact RREF, nullspace, integer kernel, Smith normal form over Q and Z | D1 |
| `glm_core/dimensional.py` | Tagged dimensional bases (SI7 / EXT10), Buckingham Pi | D1 |
| `glm_core/golay.py` | [24,12,8] code, complete decoding, total coset table | D2, D5 |
| `glm_core/coherence.py` | One versioned NRCI and Symmetry TAX, exact | D3, D5 |
| `glm_core/chemistry.py` | 118-element ingestion, stoichiometry, labelled energy scale | D4, D6 |
| `glm_core/spatial.py` | Grids, D4 symmetry, simplicial faces, CRG | (drops `ubp_engine`) |
| `glm_core/tct.py` | Three Column Thinking across all four domains | - |

Package-level guarantees, checked by AST scan in the suite: **no `random`
import anywhere** (the audited tree had 8 unseeded call sites), **no
third-party import** (standard library only), and exact arithmetic
(`Fraction`/`int`) for every quantity that feeds a result - floats appear only
in `*_float` display fields.

## How each defect was closed

**D1 - divergent dimensional bases.** Rather than picking a winner, the basis
is now a required, explicit tag on every `Dimension` and every `PiResult`.
`Basis.SI7` treats angle as dimensionless (torque **is** energy);
`Basis.EXT10` carries angle, solid angle and information axes (torque is
**not** energy). Mixing bases raises. `DimensionalEngine.compare_bases()`
makes the Step 1 divergence a first-class diagnostic: for
`{torque, energy, angle}` it reports 2 groups under SI7 versus 1 under EXT10
and names the cause. Both answers are correct for their basis; what was wrong
before was that neither engine said which basis it used.

**D2 - Golay miscorrection.** The decoder is now complete (a total coset-leader
table over all 4096 syndromes) and returns a status rather than a boolean:
`CODEWORD`, `CORRECTED`, or `AMBIGUOUS_TIE`. Measured across error weights 0-7:
w<=3 always `CORRECTED` and always recovers the transmitted word; w=4 always
`AMBIGUOUS_TIE` with exactly 6 tied codewords, never silently resolved; and
**no success status ever returns a non-codeword** (0 occurrences).

One point of honesty, and it is the important one: the Step 2 brief asked for
`w>=5 -> UNCORRECTABLE`. **That is not achievable by any decoder for this
code, and this package does not pretend otherwise.** A weight-5 error produces
a received word bit-for-bit identical to one produced by a weight-3 error on a
different codeword; the two cases are information-theoretically
indistinguishable. The suite measures this directly - at w=5 the decoder
returns `CORRECTED` with the wrong codeword in 40 of 40 trials. What was fixed
is the *claim*: every result carries a `guarantee` string reading "correct if
at most 3 errors occurred", which is true, in place of the legacy
`corrected=True`, which was not.

**D3 - 113 competing NRCI definitions.** One definition, versioned
(`nrci-1.0.0`): `NRCI(v) = 1 - d(v, C) / 4`, exact `Fraction`, where d is the
distance to the Golay code and 4 is the covering radius. The normalisation is a
stated **convention**, not a derived result - the audited formulations were not
so much wrong as unlabelled, and the version constant is what fixes that.

**D5 - unseeded sampling.** The wall distance is an O(1) lookup in the complete
coset table, replacing the 300-of-4096 unseeded sample. 100 identical calls
return **1 distinct value**, variance exactly 0, and the value matches an
exhaustive minimum over all 4096 codewords. The audited version returned 3
distinct values in 12 calls.

**D6 - broken ingestion.** `KnowledgeBase` reads the `_fields` schema from the
file and zips it against each positional row, so the schema comes from the data
instead of being assumed. All **118** elements ingest, Z contiguous 1..118,
118 distinct 24-bit carriers. The 119th record is dropped for having no
parseable atomic number, and that drop is counted in the ingestion report
rather than passing silently.

**D4 - energy scale.** The dimensionless quantity and the physical one are now
separate and separately labelled. `geometric_work()` returns a dimensionless
count; `WORK_UNIT_KJ_PER_MOL = 190` is marked an empirical calibration anchor;
conversion is explicit and Avogadro's number is exact. Every estimate carries a
`basis` field recording that it rests on the fitted anchor.

## Two findings that the build surfaced

Both are reported rather than smoothed over, and both bear on later steps.

**No element carrier is a Golay codeword.** Of the 118 carriers, 0 are
codewords and 107 sit at the covering radius (NRCI = 0). Their Hamming weights
(8, 12, 16) coincide with Golay codeword weights, but the vectors themselves
are not in the code. The element encoding is therefore not Golay-aligned. This
is why the NRCI-weighted form of geometric work is degenerate for most pairs,
and why the energy conversion uses raw path length instead.

**The 190 kJ/mol anchor overshoots measured bond energies by 5.4x to 8.8x.**
Against CRC bond dissociation energies for 5 heteronuclear pairs, the mean
absolute error is 2745.6 kJ/mol. A further 4 homonuclear pairs (H-H, O-O, N-N,
C-C) are **undefined** under this work measure - identical carriers give a
zero-length trajectory - and return no energy rather than 0 kJ/mol, so a
non-result cannot be mistaken for a computed zero. The anchor is not fitted to
these data and this suite does not fit it; on the evidence, the carrier
encoding rather than the constant is the likely source of the discrepancy.

## Evidence and limits (Step 2)

- Every Step 2 number is **computed** in a single run (Tier 1), except the
  Golay minimum weight of 8, which is **cross-validated**: `glm_core/golay.py`
  builds the code from the cyclic generator polynomial and enumerates all 4096
  codewords, independently of the Step 1 reference in
  `workflow/01_subsystem_audit.py`, and the two agree.
- The Golay boundary table uses a deterministic enumeration - the first 40
  combinations of error positions per weight - not an exhaustive sweep of all
  error patterns at each weight.
- "0 silent miscorrections" is a statement about the module's **contract**, not
  a claim that weight-5 errors are detected. See D2 above.
- Element properties (Z, valence, tension, phase) are parsed from KB lexicon
  text by regular expression. They were checked for parseability; their
  chemical **correctness** was not verified against an external periodic table.
- The 24-bit carriers are taken from the knowledge base as given. Their format
  and distinctness are verified; that they encode any particular chemistry is
  not.
- No ARC-AGI task set was solved or scored. The spatial module's operations are
  verified against their own algebraic invariants only.
- `glm_core` does not import from the audited tree at runtime except to read
  the knowledge base JSON; no legacy module was modified, and the legacy call
  sites still using `snap_to_codeword` were **not** migrated.

---

# Step 3 - Multi-domain benchmark

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/04_multidomain_benchmark.py   # ~4 s
```

Full results in `results/step3_benchmark_results.json` and
`results/step3_benchmark_scorecard.md`. Each domain is scored against an
external or formal ground truth, not against the engine's own output.

| Domain | Metric | Result |
|---|---|---|
| Physics | Pi-group count vs textbook | **18/18** |
| Physics | Dimensional homogeneity (SI7) | **16/16** |
| Chemistry | Reaction balancing vs published coefficients | **13/13** |
| Chemistry | Work vs bond energy, r^2 | **0.0011** |
| Spatial | Real ARC tasks ingested | **65/65** |
| Spatial | ARC tasks solved (single-D4 class) | **1/65** |
| Symbolic | Exact-algebra checks | **19/19** |
| TCT | Column 3 executes and matches Column 2 | **9/9** |

## The headline result is a refutation

Step 2 reported that the 190 kJ/mol anchor overshoots measured bond energies
by 5-9x and suggested recalibrating it. Step 3 tested that suggestion properly,
against 24 tabulated bond dissociation energies, and it does not survive.

Least-squares refitting the scale factor drops the mean absolute error from
3019 to 110 kJ/mol - which looks like a fix until it is compared against the
right baseline. **Simply predicting the mean of the reference set gives an MAE
of 81 kJ/mol.** The refitted model is worse than a constant. The correlation
between dimensionless path length and bond energy is r = 0.033, r^2 = 0.0011.

So the anchor was never the problem. The dimensionless geometric work carries
essentially no information about bond dissociation energy, and **no choice of
calibration constant can rescue it**. This closes the question Step 2 left
open: the defect is in the carrier encoding, not in the constant. It is
consistent with the Step 2 finding that none of the 118 carriers is a Golay
codeword - the encoding is not capturing the chemistry it is supposed to.

Reported as a refutation rather than buried, because an in-sample refit
showing a 27x error reduction is exactly the kind of number that would look
like a success if the baseline were left out.

## A basis inconsistency the benchmark caught and fixed

Scoring dimensional homogeneity in EXT10 initially failed on `E = h f` while
`L = I omega` passed - an internal contradiction in the basis, not a fact
about physics. The cause was inconsistent angular bookkeeping: `frequency`
(cycles/s) carried no angle while `angular_velocity` (rad/s) did, though both
are angle per time.

Two corrections closed it, and both are now documented in
`glm_core/dimensional.py`:

- **A per-cycle convention.** Frequency carries `A=+1`; quantities defined per
  cycle - wavelength (metres per cycle), the Planck constant (joule-seconds
  per cycle) - carry `A=-1`.
- **Moment of inertia carries `A=-2`.** This is what makes `E = I omega^2` and
  `L = I omega = tau t` agree; assigning it `A=0` leaves the two definitions of
  angular momentum differing by `A^2`, the classic inconsistency of
  angle-as-a-dimension systems.

After the fix, all 16 laws are homogeneous in **both** bases, zero laws are
basis-sensitive, and EXT10 still separates torque from energy and angular
momentum from action while a negative control confirms it does **not**
over-separate cycle frequency from angular velocity. The visible cost is that
`f^2 L / g` is no longer dimensionless in EXT10, which is correct - the
pendulum relation holds for angular frequency.

## ARC-AGI: an honest floor

65 real training tasks from `arc_agi_17/data/training/` were ingested and the
spatial module was scored on whether it reproduces each held-out test output
exactly. Under a deliberately narrow hypothesis class - one global D4
operation, consistent across all training pairs - **1 of 65** tasks is solved,
at 1/1 precision within the class.

A synthetic control confirms the D4 detector itself finds all 8 operations, so
the low rate measures the hypothesis class, not a broken implementation. Most
ARC tasks need compositional reasoning far beyond a single rigid motion. This
is a floor for the spatial module, and it is reported rather than omitted.

## Evidence and limits (Step 3)

- All Step 3 numbers are **computed** in a single run (Tier 1), except the
  TCT Column 2 / Column 3 agreement, which is **cross-validated**: the value
  is computed once in-process and re-derived in a separate subprocess from the
  generated script.
- The refitted anchor is fitted on the same 16 pairs it is scored on. Its
  110 kJ/mol MAE is an optimistic **in-sample** figure with no held-out split;
  it is reported to bound what any constant could achieve, and it still loses
  to the baseline.
- Bond dissociation energies are standard tabulated **mean** values, not
  molecule-specific, so scatter against them is expected even for a good model.
- Physics ground truth is the textbook Pi-group count entered as a literal in
  the benchmark source. It encodes the standard result; it is not
  independently re-derived.
- The ARC figure is on 65 tasks from the repository's training directory. It
  is **not** the official ARC-AGI evaluation set and is not comparable to
  published ARC scores.
- Column 2 / Column 3 agreement requires the decisive value to appear in
  stdout. That is substantive but is not a full symbolic equivalence proof.
- Latency figures include interpreter startup per subprocess and do not
  measure engine speed.
- The legacy `snap_to_codeword` call sites were **not** migrated; no file under
  `workflow/GLM/` was modified in this step.

---

# Step 4 - Mathematical traces and failure diagnostics

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/05_mathematical_tracing.py   # ~10 s
```

`glm_core/tracing.py` adds four tracers that record intermediate algebra, not
just answers: `DimensionalTracer` (exponents, RREF, pivots, nullspace,
primitive kernel, with `A·k = 0` residuals recorded), `GolayTracer` (syndrome,
coset leaders, error bit positions, full distance profile to all 4096
codewords), `CoherenceTracer` (TAX term by term, NRCI with wall-distance
provenance) and `ConstructionATracer`. Full traces in
`results/step4_mathematical_traces.json`; the readable ledger is
`results/step4_failure_diagnostics.md`.

## The chemistry failure, finally pinned down

Step 3 refuted the bond-energy hypothesis but could not say whether the
encoding was at fault or the task was simply hard. Step 4 answers that with a
**positive control** - the same 22 bonds, regressed against standard chemical
descriptors:

| Predictor | r^2 | OLS in-sample MAE |
|---|---|---|
| Carrier path length | **0.0001** | 76.09 kJ/mol |
| Carrier Hamming distance | 0.0318 | 74.85 kJ/mol |
| Electronegativity difference | 0.5109 | 52.12 kJ/mol |
| Inverse bond length | 0.3303 | 55.45 kJ/mol |
| **Pauling's rule** | **0.8937** | **22.59 kJ/mol** |

Baseline (predict the mean): 76.18 kJ/mol. The carrier reaches 76.09 - it is
indistinguishable from a constant. Pauling's rule reaches r^2 = 0.89 on the
identical bonds. **The task is learnable; this encoding cannot learn it.**
Without this control, r^2 ~ 0 would have been ambiguous.

**And the encoding's structure is now exactly characterised.** The 118 carriers
have Hamming weights only on 8, 12 and 16 - precisely the Golay code's
non-trivial weights - so they were built to reproduce its weight enumerator.
They occupy just **64** distinct syndromes (vs ~116 expected under arbitrary
placement). Those 64 are **not** a linear subspace, but they **are a coset** of
one. The carrier set is a clean linear object uniformly displaced off the code.

Testing the obvious remediation shows it is insufficient: a single fixed XOR
offset takes 0 → 2 carriers into the code and mean wall distance 3.81 → 3.59.
One translation can send exactly one of the 64 syndrome classes to zero, so
only the carriers sharing that syndrome land in the code. Full alignment needs
a **redesign**, not a translation - and even a fully aligned encoding would not
help chemically, since XOR by a constant preserves every pairwise Hamming
distance and so cannot move any number in the table above.

## Legacy migration is a data migration, not a search-and-replace

279 legacy snap-style call sites remain, across 9 subsystems. Tracing the
legacy decoder against `glm_core` over a deterministic weight 0-7 sweep gives
**65 silent corruptions for the legacy decoder and 0 for the unified one**, and
locates the boundary precisely: weight 4 returns a non-codeword while flagging
`corrected=False` (detectable), weight 5 flags `corrected=True` and returns a
valid but wrong codeword (not detectable).

The more consequential finding is structural. The two implementations build
**different codes**:

| Property | Legacy | glm_core |
|---|---|---|
| Codewords | 4096 | 4096 |
| Weight distribution | identical | identical |
| Codewords in common | **8 of 4096** | |
| Same subspace | **No** | |

Both are valid [24,12,8] extended Golay codes with the same weight enumerator,
but they are different subspaces of GF(2)^24 - equivalent under a coordinate
permutation, not equal. So a call site **cannot** be migrated by swapping
`snap_to_codeword` for `decode_complete`: any 24-bit state persisted under the
legacy generator must also be mapped through the permutation relating the two
codes, or every stored vector silently changes meaning. This was invisible from
the call-site census alone and changes the shape of the migration task.

## A naming correction: Construction A is not the Leech lattice

The audited repository refers to "Leech lattice" coordinates while what is
directly constructible from the Golay code is Construction A,
`Lambda_A = { x in Z^24 : x mod 2 in C }`. These are not the same lattice:

| | Construction A | Leech |
|---|---|---|
| Minimum squared norm | 4 | 4 |
| Minimal vectors (kissing number) | **48** | **196560** |

Construction A admits the 48 vectors `(±2, 0, ..., 0)`, which the Leech lattice
excludes. Obtaining Leech requires Construction B plus a coordinate-sum
congruence that Construction A does not impose. Any invariant quoted as a Leech
property - the kissing number above all - does not follow from this
construction.

## ARC: all 65 tasks classified

Every task is now labelled with the narrowest transformation family a fixed
detector set can identify. 9 families; 1 single-D4 solvable, matching Step 3.

| Family | Tasks | | Family | Tasks |
|---|---|---|---|---|
| `same_shape_palette_subset` | 18 | | `inconsistent_across_pairs` | 6 |
| `same_shape_palette_extended` | 15 | | `same_shape_rearrangement` | 3 |
| `shape_expansion_other` | 9 | | `crop_subgrid` | 3 |
| `shape_reduction_other` | 9 | | `d4:flipud` | 1 |
| | | | `upscale_varying_parameter` | 1 |

The `*_other`, `*_subset`, `*_extended` and `inconsistent` labels are residual:
they record that **no detector matched**, so those 48 tasks are unexplained
rather than explained. That is the honest reading, and the table is the
work-list for widening the hypothesis class.

## Electromagnetic closure

Step 3's per-cycle convention was validated only on mechanics. Extending to 15
electromagnetic and electrodynamic relations (Faraday, capacitive and inductive
energy, `c^2 = 1/(eps mu)`, and others): **15/15 homogeneous in both bases, 0
basis-sensitive**. The EM quantities carry no angular exponent, so the
convention neither helps nor harms them - confirming it is correctly confined
to the rotational and wave sectors.

## Evidence and limits (Step 4)

- All values **computed** in a single run (Tier 1), except the carrier
  path-length r^2, which is **cross-validated**: re-derived here on 22 bonds
  against Step 3's 16, both giving r^2 ~ 0.
- Traced quantities are exact `Fraction`/`int`. The correlations in the
  chemistry section are computed in floating point because the reference
  chemical data are themselves decimal measurements.
- The regression fits are **in-sample** with no held-out split. They bound what
  each predictor could achieve; the comparison between them is the point, not
  the absolute numbers.
- Chemical reference values (electronegativity, covalent radii, bond energies)
  are standard tabulated means entered as literals, not re-derived. Mean BDEs
  are not molecule-specific.
- The ARC classifier reports the narrowest family its fixed detector set can
  find; residual labels mark absence of a match, not a positive finding.
- The CRG growth trace uses a lossy per-row parity projection - a structural
  probe, not evidence that grid rows are meaningful lattice vectors.
- The legacy sweep uses the first 30 error-position combinations per weight
  against one base codeword per code. Deterministic, but not exhaustive.
- The 196560 Leech kissing number is quoted from the literature; Construction
  A's 48 is derived here from the construction and the code's weight
  enumerator.
- **No file under `workflow/GLM/` was modified.** Legacy call sites are counted
  and characterised, not migrated.
- Step 2 (96/96) and Step 3 were re-run after these changes: no regressions.
  The Step 2 module-set assertion was updated for the new `tracing.py` module -
  it correctly caught the addition.

---

# Step 5 - Algorithmic hardening

```bash
export PATH="$PWD/.uvbin:$PATH"
uv run python workflow/06_remediation_benchmarks.py   # ~2 min
uv run pytest -q tests/test_step5_enhancements.py     # 107 tests
```

Three new modules act on Step 4's diagnoses: `glm_core/physical_carriers.py`,
`glm_core/isomorphism.py` and `glm_core/crg.py`, plus a hypothesis engine in
`glm_core/spatial.py` and legacy translation in `glm_core/golay.py`.

| Enhancement | Baseline | Enhanced |
|---|---|---|
| Bond energy, **LOOCV** r^2 | -0.193 | **0.813** |
| Bond energy, **LOOCV** MAE | 83.6 kJ/mol | **32.8 kJ/mol** |
| Carriers that are Golay codewords | 0 / 118 | **22 / 22** |
| Golay silent corruptions | 65 | **0** |
| Spatial hypothesis candidates | 8 | **35** (8 families) |
| ARC tasks solved | 1 / 65 | **1 / 65** |
| Physics Pi-group regression | 8/8 | 8/8 |

## Chemistry: the carrier redesign worked

Step 4 concluded the encoding had to be redesigned, not translated. Each
element is now four measured properties - Pauling electronegativity, covalent
radius, valence electrons, homonuclear bond energy - each quantised to 3 bits,
and the 12 resulting information bits are **Golay-encoded**. Two consequences
follow by construction: every carrier is a codeword (the alignment defect Step
4 found is closed), and a carrier corrupted by up to 3 bit flips still decodes
to the correct properties, which the legacy encoding could never do since its
vectors were not codewords at all.

Prediction is scored by **leave-one-out cross-validation** - a four-parameter
model on 22 bonds would otherwise flatter itself - and the regression is solved
exactly over Q with `Fraction`. LOOCV r^2 = **0.813**, MAE **32.8 kJ/mol**
against a predict-the-mean baseline of 76.2.

**What this does and does not show.** The gain comes from grounding the
encoding in measured chemistry. It is *not* lattice geometry discovering
chemistry and must not be read that way. The honest question answered is how
much predictive power survives quantisation to 24 bits, between two reference
points: the legacy carrier at r^2 ~ 0 below, and the continuous Pauling rule at
r^2 = 0.894 (Step 4) above. Most of it survives.

## Golay: the permutation was found, and it is the right kind of map

Step 4 showed the legacy and canonical codes share only 8 of 4096 codewords.
Step 5 derives the coordinate permutation relating them by searching the
Steiner system S(5,8,24) formed by each code's 759 octads, anchored on five
fixed points - legitimate because M24 is 5-transitive, so if any isomorphism
exists then one exists fixing five coordinates.

```
LEGACY_TO_CORE = (0,1,2,3,4,5,7,16,8,19,22,9,13,12,10,18,14,15,21,6,11,20,23,17)
```

Verified exhaustively over all 4096 codewords of each code: bijective,
round-trip identity, and **weight preserving**. That last property is the one
that matters. `glm_core/isomorphism.py` also builds a general linear
isomorphism, which maps the code onto the code but **scrambles Hamming
distance** and therefore cannot be wrapped around a decoder - it is retained
only for codeword translation, with that caveat attached in code. Only the
permutation commutes with decoding.

`decode_legacy()` uses it to route legacy words through the audited-correct
decoder: over the same weight 0-7 sweep, silent corruptions go from **65 to 0**.

## Spatial: a negative result

The hypothesis class was widened from 8 candidates (single global D4) to 35
across 8 families - colour permutation, D4 composed with colour permutation,
translation, bounding-box crop, integer upscaling, plain and alternating
tiling, component selection, compression, colour reduction, constant output.

**It did not improve the ARC score: 1/65 before, 1/65 after.** This misses the
Step 5 target of a measurable increase, and is reported without adjustment.

Synthetic capability controls confirm the engine really does solve the families
it added (6/6 controls, against 2/6 for the D4-only baseline), so the ceiling is
the corpus rather than the implementation. Step 4's classification is the
explanation: 33 of 65 tasks sit in the residual `palette_subset` /
`palette_extended` classes needing object-level compositional reasoning, and
none of the added families expresses that. Widening along the rigid-motion axis
was simply the wrong axis for this corpus - which is useful to know, and is
what the classification was for.

`glm_core/crg.py` does add real machinery here regardless: connected
components, component adjacency graphs, simplicial triangles, cycle rank, and
Euler characteristic as an exact hole count, all verified invariant under D4.

## Evidence and limits (Step 5)

- All values **computed** in a single run (Tier 1), except the Golay
  permutation's losslessness, which is **cross-validated**: derived by the
  Steiner search in `isomorphism.py` and independently re-verified in the
  benchmark against the legacy engine's own codeword set.
- Chemistry figures are **leave-one-out**, not in-sample. The quantisation
  edges and level midpoints were fixed before fitting and not tuned against the
  bond targets - but they were chosen by the same author as the model, so this
  is not a blind protocol.
- The 22 bonds carry tabulated **mean** dissociation energies, not
  molecule-specific values, so some residual scatter is irreducible.
- The corrupted-word sweep uses the first 30 error-position combinations per
  weight against one base codeword. Deterministic, not exhaustive.
- The spatial capability controls are synthetic tasks built by the same code
  paths the engine searches; they demonstrate wiring, not generalisation.
- The ARC corpus is 65 repository training tasks, not the official ARC-AGI
  evaluation set.
- **No file under `workflow/GLM/` was modified.** The 279 legacy call sites
  remain unmigrated; what Step 5 adds is the verified translation layer that
  would make migrating them correct.
- Two runs of the benchmark are byte-identical after stripping timestamps.

## Next steps

1. **Migrate the 279 legacy call sites** using `decode_legacy` and the verified
   permutation. The blocker Step 4 identified is now removed.
2. **Attack ARC along the right axis**: object-level and compositional rules
   for the 33 `palette_subset` / `palette_extended` tasks. Rigid motions are
   exhausted.
3. **Validate the carrier model out of family** - the current LOOCV is over 22
   bonds from one tabulation; a held-out set from a different source would test
   whether the quantisation generalises.
4. **Extend physical carriers to all 118 elements**; only 22 have the full
   property set tabulated here.

---
---

# GLM-3+ · Step 1 — `glm_universal` substrate and MOG-cube engine

A new plan begins here. The five steps above audited and remediated the
existing GLM repository; what follows is the **Universal MOG-Cube Geometric
Language Machine (`GLM-3+`)**, a clean re-founding in a self-contained package
`glm_universal/`. Step 1 builds the substrate: the algebraic, geometric and
Monster-group foundation everything else will be indexed by.

## What was built

```
glm_universal/
├── README.md              architecture, mathematical principles, provenance
├── __init__.py
├── substrate/
│   ├── README.md          per-module contracts and known limits
│   ├── linalg.py      203  exact integer / F_2 linear algebra
│   ├── mog.py         616  Golay code, hexacode, MOG trio, sextet, cubes
│   ├── leech2.py      621  Leech lattice, Λ/2Λ, Witt data, 2A axis detection
│   ├── digit_stack.py 621  10-plane 2-adic stack, facet attribution
│   └── __init__.py     80
├── data_objects/README.md  reserved — empty scaffold, contract only
├── reasoning/README.md     reserved — empty scaffold, contract only
├── benchmarks/README.md    reserved — empty scaffold, contract only
└── tests/test_substrate.py 735  73 test functions, 96 cases with parametrics
```

Dependency direction is strictly downward, `linalg → mog → leech2 →
digit_stack`, with no import cycle. The package imports **only** the Python
standard library and does not depend on `glm_core` or on anything under
`workflow/GLM/`.

## What the substrate computes

Every number below was produced by
`workflow/07_step1_substrate_verification.py` in this run and is readable back
from `results/step1_substrate_verification.json`.

| Fact | Computed | How |
|---|---|---|
| Golay codewords / octads | 4096 / 759 | enumerated from `G = [I₁₂ \| B]` |
| Weight enumerator | 1 + 759z⁸ + 2576z¹² + 759z¹⁶ + z²⁴ | enumerated |
| Hexacode alignment | 0 failures / 4096 codewords | exhaustive shadow check |
| MOG trio | 3 disjoint octads covering all 24 | validated at import |
| MOG sextet | 6 tetrads, all 15 pairs are octads | validated at import |
| Trios in the code | 3795 | exhaustive octad-pair search |
| Leech basis determinant | 2³⁶ = [Z²⁴ : Λ] | HNF of a checked generating set |
| Witt decomposition of Λ/2Λ | 12 planes, plus type | symplectic Gram-Schmidt |
| Singular classes | 8,390,656 = 2²³ + 2¹¹ | closed form from the Witt data |
| Theta series | 1, 0, 196560, 16773120, 398034000 | `E₄³ − 720Δ`, exact integers |
| Class census | 1 + 98,280 + 8,386,560 + 8,292,375 = 2²⁴ | closes exactly |
| **Type-2 (2A axis) classes** | **98,280** | all 196,560 minimal vectors reduced mod 2Λ |
| Co₀ pair census | {4: 2, 2: 9200, 1: 94208, 0: 93150} | 196,560 inner products |

The type-2 count is the one result that arrived by **two independent paths in
this session**: exhaustive enumeration of the minimal vectors (each class hit
exactly twice, asserted) and the theta coefficient `N(32)/2`. They agree.

## The three headline capabilities

**2A axis detection.** `is_2a_axis(point)` reduces a lattice point mod 2Λ and
looks the class up in the exhaustively enumerated 98,280-class table. Because
the enumeration is complete, a *negative* answer is as much a proof as a
positive one. Controls in this run: 2000/2000 minimal vectors detected as
axes, 200/200 doubled vectors correctly rejected, 200/200 verdicts unchanged
under adding 2·(a lattice point), the origin correctly rejected.

**MOG trio and sextet geometry.** One fixed labelling of the 24 coordinates as
a 4×6 frame makes the six columns a sextet and the three 4×2 bricks a trio of
octads. Bijective reshaping between the linear 24-vector and its 4×6 and 3×8
presentations round-trips for any payload — bits, integers, `Fraction`s,
strings — because it is a pure permutation of positions.

**Lossless 10-plane reconstruction.** `class_stack_rebuild(class_stack(v)) ==
v` held exactly across **366 round trips** in this run, over integer carriers,
rational carriers with mixed denominators, out-of-range rationals at derived
depths, and genuine Leech points in both the standard and Leech bases, each at
the default `(offset 512, depth 10)` pair and at two deeper admissible pairs.
Rational carriers are cleared by their least common denominator, which travels
in the stack and is reapplied on rebuild; no float is constructed at any step.

## Failing-facet attribution — new in this port

The reference implementation could say an equation failed. This one says
*where*. `verify_equation(lhs, rhs)` compares the two stacks plane by plane and
attributes each discrepancy to the MOG facets containing it — 31 named
subsets: 3 trio bricks, 6 sextet tetrads, 4 frame rows, 18 cube faces.

Worked example from this run: perturbing the single coordinate at cube address
`(brick 2, x 1, y 0, z 1)` by +1 produced

```
holds            : false
failing planes   : [0, 1]
difference mask  : 0x002000  (identical at both planes)
blamed facets    : brick2, col5, row1, cube2.x1, cube2.y0, cube2.z1
```

which is exactly the six facets that contain that coordinate, and no others.

## Why ten planes — Proposition D1

"Ten" is not a magic number, it is a measurement. If the offset `O ≥ max_abs`
and the depth `D` satisfies `2^D > O + max_abs`, then every shifted coordinate
lies in `[0, 2^D)` and reassembly is the identity. `derive_stack_parameters`
returns the least admissible pair for any range; `depth_report` confirmed in
this run that reconstruction is exact at every admissible pair tried, that
planes above the least admissible depth are identically zero, and that the
planes below it do not move. The defaults `2⁹`/10 are the least admissible pair
for `|c| ≤ 511`. The bound is two-sided and so conservative: `−512` encodes
fine, but a dataset reaching `|c| = 512` derives depth 11. That asymmetry is
asserted in a test so a later change to the formula cannot pass silently.

## Design invariants, enforced by tests rather than intended

| Invariant | Enforced by |
|---|---|
| Exact arithmetic only (`int`, `Fraction`) | `class_stack` raises `TypeError` on a float |
| No randomness anywhere in the package | AST scan of every substrate module for a `random` import |
| Standard library only | AST scan of every module's imports against an allow-list |
| Deterministic | reports compared for equality across repeated calls |

Test fixtures needing "arbitrary" vectors use an explicit seeded LCG written
out in the test file, so every input is a literal function of its seed.

## Corrections made during the port

* The reference audit checked the Leech basis for **unimodularity**, which is
  false in the ×√8 integer model. Corrected to the index `[Z²⁴ : Λ] = 2³⁶`,
  which is what the determinant actually equals and what the test now asserts.
* Type-2 detection no longer routes through the lattice decoder. Removing the
  decoder from the trusted base means an axis claim rests only on an
  exhaustive, self-validating enumeration.
* The digit stack is generalised from integer lattice points to arbitrary
  carriers over Q.

## Commands run

```bash
uv run pytest glm_universal/tests/test_substrate.py -q
uv run python workflow/07_step1_substrate_verification.py
```

## Output files

| Path | Contents |
|---|---|
| `glm_universal/` | the package (see tree above) |
| `workflow/07_step1_substrate_verification.py` | the verification driver |
| `results/step1_substrate_verification.json` | every recomputed fact, the reconstruction sweep, the depth report, the facet demonstration, the pytest summary, and the nine success-criteria booleans |
| `results/claims.json` | eight `glm3plus_substrate_*` claims merged in by id |

## Evidence and limits (GLM-3+ Step 1)

**Checked, and at which tier.**

- *Cross-validated (two independent paths in this session):* the 98,280
  type-2 class count — exhaustive reduction of all 196,560 minimal vectors
  versus the theta coefficient `N(32)/2` from `E₄³ − 720Δ`. Also the
  8,390,656 singular-class count — closed form from the Witt decomposition
  versus the theta-series census `1 + 98,280 + 8,292,375`.
- *Computed (single run, this session):* every other number in the tables
  above. All are readable back from
  `results/step1_substrate_verification.json`.
- *Checked against file:* the nine success-criteria booleans and the pytest
  summary line were re-read from the written JSON after the run.

**Not checked.**

- **The pipeline was not re-run end to end from a clean process to confirm
  byte-identical output.** Determinism is argued from the absence of any RNG
  import (AST-scanned) and from repeated-call equality of the report
  functions, not from a full replication.
- **`is_2a_axis` positive controls covered 2000 of the 196,560 minimal
  vectors**, not all of them; the 98,280-class table itself is exhaustive and
  self-validating, but the detection wrapper was spot-checked.
- **No Leech decoder is implemented.** Types 3 and 4 of an arbitrary class are
  not computed pointwise — only their counts appear, from the theta series.
  There is no `type_of_point`. A later step needing per-class type 3/4
  resolution must add one.
- **One alignment only.** `ALIGNED_BITS` fixes a single labelling of the 24
  coordinates, and every trio, sextet and facet name is relative to it. M₂₄ is
  not implemented, so there is no way yet to move between alignments, and no
  claim here is invariant-under-M₂₄.
- **Facet attribution is bit-level, not semantic.** It localises *where* two
  carriers differ in the MOG geometry; it says nothing about why.
- **`data_objects/`, `reasoning/` and `benchmarks/` are empty scaffolds.** They
  contain a README stating a contract and no code. Nothing in this step
  exercises them.
- The GPU on this instance was **not used and is not applicable**: the
  substrate is exact integer and `Fraction` arithmetic, where floating-point
  acceleration would forfeit the exactness the whole layer rests on. The full
  verification takes 30 seconds on one core.

## Next steps (after GLM-3+ Step 1)

1. **Step 2 — `data_objects/`**: typed carriers wrapping real data as
   substrate points, with round-trip tests as the acceptance criterion.
   *(Completed — see below.)*
2. **Add a Leech decoder** to `substrate/leech2.py` if per-class type 3/4
   resolution is needed; it is the one gap in the current type theory.
3. **Implement M₂₄** so that trio, sextet and facet statements can be made
   alignment-independent.
4. **Persist the 98,280-class table** to `data/` if a 5-second cold start per
   process becomes a bottleneck; it is currently rebuilt per process.

---

# GLM-3+ · Step 2 — `data_objects` universal multi-domain carrier engine

Four domains, one carrier shape. Every object is a point of **Q²⁴** with an
exact 2-adic digit stack fitted to it. Full submodule documentation lives in
`glm_universal/data_objects/README.md`; the numbers below were computed by
`workflow/08_step2_data_objects_verification.py` and are in
`results/step2_data_objects_verification.json`.

## The losslessness contract has two legs

A codec is lossless only if **both** hold:

| Leg | Statement | Whose property |
|---|---|---|
| substrate | `class_stack_rebuild(class_stack(v)) == v` | the digit stack |
| semantic | `decode(encode(x)) == x` | the codec |

The first can hold while the second fails — a codec that drops a field still
produces a perfectly faithful stack *of the truncated carrier*. Checking only
the substrate leg would make the losslessness claim vacuous, so both are
asserted separately for every object.

| Domain | Objects | Substrate leg | Semantic leg |
|---|---|---|---|
| physics | 660 | 660/660 | 660/660 |
| chemistry | 118 | 118/118 | 118/118 |
| mathematics | 22 | 22/22 | 22/22 |
| lexicon | 10 | 10/10 | 10/10 |

## Dynamic stack depth is load-bearing, not decorative

The module default `STACK_DEPTH = 10` is **not** used on the codec path and
would fail on every element. Depth is derived per carrier from its actual
coordinate range, with no ceiling:

| Carrier | Denominator | Depth |
|---|---|---|
| physics register (660 concepts) | ≤ 2 | 2–7 |
| element register (118 elements) | ≤ 25,000,000 | **24–41** |
| hydrogen (density drives it) | 25,000,000 | 39 |
| 10⁴⁰ in one coordinate | 1 | **134** |
| 10²⁵ and 10⁻²⁵ together | 10²⁵ | **168** |

Each depth was checked to be the *least* admissible: one plane fewer raises.

## Three results worth stating

**EXT10 resolves 3,018 concept pairs that SI7 cannot.** Over the 660-concept
register, SI7 leaves 14,245 dimensionally colliding pairs and EXT10 leaves
11,227. Sixty concepts carry a nonzero plane-angle, solid-angle or information
exponent — exactly the ones the SI projection loses. Torque (`L² M T⁻² A⁻¹`)
and energy (`L² M T⁻²`) are the canonical pair.

**The periodic table inherits an error-correcting separation.** Mapping *z* to
a Golay codeword gives 118 distinct addresses whose minimum pairwise Hamming
separation over all 6,903 pairs is **8** — exactly the `[24,12,8]` code's
minimum distance.

**395 missing element attributes were restored as `None`, not as zeros.** In
the source, covalent radius is present for 24/118 elements and homonuclear BDE
for 21/118. Each absent field is coordinate `0` *and* has its bit set in the
missingness mask, so a measured zero and an absent measurement stay
distinguishable. Nothing was imputed.

## Commands run

```bash
uv run python workflow/08a_ingest_registers.py               # freeze sources
uv run python -m pytest glm_universal/tests -q               # 177 passed
uv run python workflow/08_step2_data_objects_verification.py # 12/12 criteria
```

Tests: **81 tests / 5,110 subtests passed, 0 failed, 0 skipped** for
`test_data_objects.py`; **177 passed** for the full package, confirming no
Step 1 regression.

## Evidence and limits (GLM-3+ Step 2)

**Checked, and at which tier.** All round-trip counts, stack depths, collision
figures and the Golay separation are **Tier 1 (computed)** — produced by a
single run of `workflow/08_step2_data_objects_verification.py` in this session
and read back from
`results/step2_data_objects_verification.json`. The test-suite summary lines
are the harness's own capture of `pytest` output, so the pass counts are
Tier 2 with respect to the JSON report.

**Not checked.**

- **No independent re-derivation.** Nothing here is cross-validated: there is
  one implementation and one run. A second implementation of the codecs was
  not written, so a shared-assumption bug would not have been caught.
- **Source data was ingested, not audited.** The 660-concept register and the
  PubChem periodic table were converted to exact rationals faithfully — the
  conversion is exact and tested — but the underlying *physical values* were
  taken on trust from the in-repo sources. No value was checked against an
  external authority in this session.
- **Covalent radius (24/118) and homonuclear BDE (21/118) are sparse** because
  those are the only entries in the session's own tables. They were
  deliberately **not** topped up from recall; a fuller table must come with a
  citation.
- **The plan's dyadic offset does not exist for this data.** The plan asks for
  minimal *O* with 2ᴼ·v ∈ Z²⁴; denominators of 3, 12 and 2.5 × 10⁷ are not
  powers of two, so no such *O* exists. The codecs clear the general least
  common denominator instead — strictly more general, always defined — and
  `dyadic_exponent()` returns `None` in those cases rather than pretending.
  This is a documented departure from the plan text, not an oversight.
- **The lexicon is a 10-concept sample**, built to exercise the codec, not a
  corpus. Its carriers are unreadable without the `Vocabulary` that produced
  them.
- **Redundant coordinates are not independent evidence.** Physics coordinates
  10–16 and element coordinates 18–23 are functions of other coordinates; they
  are decode-time consistency checks, and a carrier that satisfies them has
  not thereby been validated against the world.
- The GPU was **not used and is not applicable**: exact `int`/`Fraction`
  arithmetic has no CUDA path, and reaching one would require the floats this
  step exists to exclude. The full sweep takes well under a minute on one core.

## Next steps (after GLM-3+ Step 2)

1. **Step 3 — `reasoning/`**: inference over stacks with facet-level failure
   attribution, using the 222 scalar and 71 tensor relations that accompany
   the 660-concept register as the first test corpus. **Done — see below.**
2. **Widen the chemistry sources** so covalent radius and BDE reach full
   coverage from a cited external table rather than staying at 24/118 and
   21/118.
3. **Cross-validate the codecs** with an independent second implementation, to
   move the round-trip claims off Tier 1.

# GLM-3+ Step 3 — Algebraic & Geometric Reasoning Kernel

`glm_universal/reasoning/` is implemented: four modules, a frozen relation
snapshot, 62 unit tests and a runnable audit. Package documentation lives in
`glm_universal/reasoning/README.md`; the results of this run are in
`results/step3_reasoning_kernel.json` and `results/step3_reasoning_kernel.md`.

## What was built

| file | contents |
| --- | --- |
| `glm_universal/reasoning/product.py` | Norton–Sakuma `2A` algebra over the 98,280 type-2 classes: `a·b = (1/8)(a + b − a_ab)`, the Griess form on axes, the 3-dimensional subalgebra with checked closure, exact Ising fusion spectrum, Miyamoto `τ` and `σ` |
| `glm_universal/reasoning/metric.py` | positive-definite Griess form on `Q^24`, exact squared distances, float-free angular comparison, triangle inequality by clearing the square root, exact single/complete linkage |
| `glm_universal/reasoning/analogy.py` | `D* = C + (B − A)` with projection onto candidates, the Golay code, or `Λ` by a provably optimal nearest-point decoder |
| `glm_universal/reasoning/verifier.py` | operator algebra, expression parser, and the multi-plane audit with 31-facet attribution |
| `glm_universal/reasoning/_data/physics_relations.json` | the 222 + 71 relation *statements* (frozen data, not an oracle) |
| `glm_universal/tests/test_reasoning.py` | 62 tests, including AST scans for float literals, `float()` calls, `random` and third-party imports |

## Results of this run

| check | result | source |
| --- | --- | --- |
| type-2 classes enumerated | 98,280 | `results/step3_reasoning_kernel.json` |
| `2A` pairs audited: closed, commutative, non-associative, Gram `1`/`1/8` | 8 / 8 | same |
| pair census against one axis (`1A`/`2A`/unmodelled/`2B`) | 2 / 9,200 / 94,208 / 93,150 | same |
| fusion spectrum dims at `1, 0, 1/4, 1/32` | 1, 1, 1, **0** | same |
| Griess form positive definite (2 independent proofs) | yes; Leech Gram determinant 1 | same |
| triangle inequality | 210 / 210 triples | same |
| physics analogies reaching the expected concept | 6 / 6 | same |
| element group/period analogies exactly and uniquely correct | 5 / 5 | same |
| perturbed Leech points decoded back to origin | 4 / 4 | same |
| scalar relations under scalar semantics | 222 / 222 | same |
| tensor relations under full semantics | 71 / 71 | same |
| scalar relations under full semantics | 186 / 222 | same |
| MOG facets carrying blame for the 36 strict failures | 12 of 31 | same |
| test suite | 62 passed (reasoning), 239 passed + 5,110 subtests (package) | pytest output |

Three results worth stating:

- **`τ_a` is the identity on the `2A` subalgebra, and that is derived rather
  than assumed.** The `1/32`-eigenspace of `ad_a` comes out empty when
  `(ad_a − λI)x = 0` is solved exactly over `Q^3`, and `τ` is by definition
  `−1` there. The axis swap people expect from `τ` actually belongs to `σ`
  (`−1` on the `1/4`-eigenspace), which the module checks is an automorphism
  and an isometry.
- **36 statements a units table gets right are wrong at full meaning.**
  `acceleration = speed / time` fails on rank and parity; the discrepancy lands
  in coordinates 18 and 19, and the verdict blames exactly the facets
  containing them (`brick2/col5/row3/cube2.*` and `brick1/col3/row0/cube1.*`).
  That is the facet attribution doing real work rather than decorating a
  boolean.
- **The additive analogy model has a visible boundary.**
  `time : frequency :: length : ?` is an inversion, not a translation, so the
  model answers acceleration rather than wavenumber. Recorded in the report as
  a boundary case, not quietly dropped.

## Commands run

```bash
uv run python workflow/09_extract_physics_relations.py   # freeze 222 + 71 + 40 aliases
uv run pytest glm_universal/tests/test_reasoning.py -q   # 62 passed
uv run pytest glm_universal/tests/ -q                    # 239 passed, 5110 subtests
uv run python workflow/10_reasoning_audit.py             # results + claim ledger
uv run python workflow/11_update_manifest.py             # provenance
```

## Evidence and limits (GLM-3+ Step 3)

**Checked, and at what tier.**

- Tier 1 (computed this run): every number in the table above is the return
  value of a function in `glm_universal.reasoning`, called by
  `workflow/10_reasoning_audit.py`, and re-read from
  `results/step3_reasoning_kernel.json`.
- Tier 3 (cross-validated by two independent paths): the relation tallies
  222 / 71 / 186. This kernel's own parser and operator algebra over
  `glm_universal`'s frozen 660-concept register produce those three numbers;
  the upstream `glm2_library.library_audit()`, a separate implementation over a
  separate copy of the register, produces the same three. The two paths share
  no code — only the statements, which are data.
- Positive definiteness is established twice within this run: by the diagonal
  of the form on the standard basis, and by Sylvester's criterion on all 24
  leading minors of the Leech Gram matrix in integer arithmetic.

**Not checked.**

- The `2A` audit covers **8 pairs** drawn deterministically from one seed
  class, not all 9,200 partners of that axis and not all 98,280 classes. The
  closure argument is uniform; the verification is a sample.
- The **pair-invariant-1 position is not modelled**. No Norton–Sakuma type is
  claimed for it and every product there raises. Whether it is 3A, 4A or
  another type is outside what this substrate decides.
- Identifying pair invariant 2 with the Norton–Sakuma `2A` position is an
  **operational definition** grounded in the substrate (it is the unique
  position where `u XOR v` is again type 2, hence the unique position where the
  Sakuma triple exists here). This run verifies the `2A` relations close there;
  it does not prove a correspondence with the Monster's `2A` conjugacy class.
- Analogy accuracy is reported on 6 physics and 5 chemistry items **chosen by
  hand** to probe specific structure. That is a demonstration, not a benchmark:
  no held-out set, no randomised sampling, and physics answers are usually tie
  classes (4–11 members) rather than single concepts.
- The nearest-lattice-point decoder is optimal **by construction**. This run
  checks that claim against explicit rivals on one query and on four perturbed
  minimal vectors; it is not an exhaustive proof by enumeration.
- Clustering ran on one hand-picked slice of 14 physical quantities, with no
  stability analysis over subsamples.
- The GPU was **not used and is not applicable**, for the same reason as
  Steps 1 and 2: exact `int`/`Fraction`/`F_2` arithmetic has no CUDA path, and
  reaching one would require the floats these steps exist to exclude. The whole
  audit takes about ten seconds on one core.

## Next steps (after GLM-3+ Step 3)

1. **Widen the `2A` audit** from 8 sampled pairs toward the full 9,200-partner
   orbit of one axis, which is affordable and would move the closure claim from
   a sample to a census.
2. **Decide the invariant-1 position** — identify which Norton–Sakuma type it
   carries, or establish that this substrate cannot see it.
3. **Benchmark the analogy solver** on a held-out item set rather than
   hand-chosen demonstrations, and report tie-class size as a first-class
   metric.
4. **Widen the chemistry sources** (carried over from Step 2): covalent radius
   and BDE remain at 24/118 and 21/118.


# GLM-3+ Step 1 (runtime) — Interactive Geometric Language Runtime and the Three Column Thinking Engine

The reasoning kernel of Step 3 can answer questions, but nothing could *ask*
it one. This step builds that layer: `glm_universal/runtime/` and the
top-level `GLM.py`, which together turn a typed or piped string into a
verified **Three Column Thinking** trace.

## What was built

| File | Lines | What it does |
|---|---|---|
| `glm_universal/runtime/parser.py` | ~640 | Deterministic semantic query parsing: a fixed grammar, a fixed keyword table, and six classification rules applied in a fixed priority order. No language model, no embedding, no sampling. |
| `glm_universal/runtime/session.py` | ~950 | `GeometricSession`: five lazily-loaded registers, the concept index over them, the active basis, the inference history, and one solver per query kind. |
| `glm_universal/runtime/tct_engine.py` | ~630 | The Three Column Thinking generator, the script renderer, the AST exactness check, and the subprocess verifier. |
| `GLM.py` | ~430 | CLI and API entry point: `--query`, `--domain`, `--interactive`, `--verify-tct`, `--export-trace`, plus `--format`, `--columns`, `--basis`, `--list-domains`. |
| `glm_universal/tests/test_runtime.py` | ~900 | 181 tests over the parser, the session, the TCT engine, the CLI, and package-wide exactness. |

## The three columns, and why the third one is not a printout

A trace states one solved query three times over. **Column 1** is the
reasoning chain in English. **Column 2** is the same chain as exact statements
over `Q`, `Z` and `F_2` — rational equations, digit-stack parameters, Griess
forms, Norton–Sakuma products, every rational as a canonical `"n/d"` string.
Both columns are read off the *same* `Step` objects, so entry *i* of each is
the same step; they cannot drift apart.

What they could still share is a bug in the solver. So **column 3** is a
generated, self-contained Python script that does not repeat the solver's
steps: it re-enters the package at its public API, in a fresh interpreter,
with column 2's values embedded as literals, and exits non-zero if anything
differs. Verification is then two independent comparisons — the script's own
exit code, and the parent process re-reading the script's JSON and comparing
key by key. A trace counts as verified only when both agree.

**This is a same-session cross-check between two code paths, not an
independent reproduction of the mathematics.** Both paths call the same
`glm_universal` functions, so a defect in those functions would be invisible
to it. What it does catch is the solver mis-transcribing, mis-rounding or
mis-labelling a result, and any dependence of an answer on interpreter state,
import order or a cached table — since the subprocess shares none of those.

## The spatial register

The plan called for a spatial/ARC domain. Rather than invent a dataset, the
`spatial` register is built from the MOG's own structures: the trio's three
octads, the sextet's six tetrads, the four rows of the `4 x 6` frame, and the
fifteen octads obtained as unions of tetrad pairs — 28
carriers, every one of them a presentation of the substrate. The octad
property of the bricks and of all fifteen tetrad-pair unions is *checked*
against the Golay code every time the register is built, so the sextet
property is verified rather than assumed.

## Results of this run

Registers loaded: physics 660, chemistry 118,
mathematics 22, lexicon 10, spatial
28 — 1481 distinct surface forms in the
concept index.

| Measure | Value |
|---|---|
| Battery queries | 20 |
| Parsed to the expected kind | 20/20 |
| Solved | 20/20 |
| Column 3 ran and matched column 2 | 20/20 |
| Solver kinds covered | 7 of 7 |
| Registers covered | 5 of 5 |
| Generated scripts float-free (AST) | True |
| Queries correctly refused | 6/6 |
| CLI invocations with the expected exit code | 7/7 |
| float literals in runtime sources | 0 |
| `float()` calls in runtime sources | 0 |
| RNG imports in runtime sources | 0 |
| Wall-clock imports in runtime sources | 0 |

### Negative controls

A verifier that always reported success would pass every positive check above,
so two deliberate falsifications were run:

- **A wrong exact value.** One claim in column 2 was replaced with `1/1`. The
  script exited 1 and the
  parent's comparison flagged exactly
  ['griess_norm2']. Caught:
  **True**.
- **A claim nothing recomputes.** A claim absent from every script template
  was added to column 2. It was reported as a missing key rather than passed
  over. Caught: **True**.

### One real defect this audit found

The first audit run failed on `check tensor force = mass * acceleration`. The
parser detected the semantics qualifier `tensor` and switched to `full`
semantics correctly, but left the word in the expression, so the left side
parsed as the unknown concept `tensor force`. Fixed in
`_strip_semantics_qualifier`, which removes a qualifier only in the two
positions where it is unambiguously a directive — leading, or in a trailing
`under <word> semantics` phrase — and leaves it alone mid-expression, where
deleting it would silently change the equation being audited. Four regression
tests cover the fix.

## Design invariants, enforced by tests rather than intended

- **No float anywhere**, in the runtime sources *or* in the scripts they
  generate. `script_is_exact` checks generated source by AST, so a `float` in
  a string or a comment is correctly ignored while a real one is caught.
- **No RNG and no wall clock.** A trace must be byte-identical between runs,
  which a test asserts by building the same trace from two fresh sessions and
  comparing the rendered Markdown.
- **XOR only where it is addition.** `sakuma_third_axis` combines two classes
  by `^` because on the `F_2` module `Lambda / 2 Lambda` that *is* vector
  addition, and both the language and the mathematics columns say so. Nowhere
  is `^` used as a stand-in for arithmetic on rationals.
- **Failures are results.** An unsolved query returns a `Solution` with
  `ok=False`, is recorded in the history, and still explains itself. Only a
  structurally malformed string raises.

## Commands run

```bash
uv run pytest glm_universal/tests/ -q                       # 420 passed, 5110 subtests
uv run python workflow/12_runtime_tct_audit.py              # AUDIT PASSED
uv run python GLM.py --list-domains
uv run python GLM.py -q "force = mass * acceleration" --verify-tct
printf 'describe carbon\n:quit\n' | uv run python GLM.py --interactive
```

## Output files

| Path | Contents |
|---|---|
| `glm_universal/runtime/{__init__,parser,session,tct_engine}.py` | The runtime package |
| `GLM.py` | CLI and API entry point |
| `glm_universal/tests/test_runtime.py` | 181 tests |
| `results/step1_runtime_tct.json` | Full machine-readable audit |
| `results/step1_runtime_tct.md` | Human-readable scorecard |
| `reports/tct_examples.md` | Three worked traces, all three columns |
| `workflow/12_runtime_tct_audit.py` | The audit script |

## Evidence and limits (GLM-3+ Step 1 runtime)

**Checked, and at which tier.**

- Every figure in the table above was computed by
  `workflow/12_runtime_tct_audit.py` in a single run and read back from
  `results/step1_runtime_tct.json` (Tier 1, computed; Tier 2 for the values
  restated here, which were re-read from that file).
- The 20/20 verification count is a
  Tier 3 cross-validation **in a narrow sense**: each value was derived twice,
  once by the in-process solver and once by a generated script in a separate
  interpreter. Named paths: `GeometricSession._solve_*` and the corresponding
  `tct_engine` template. Both call the same `glm_universal` functions, so this
  does not test those functions.
- The full suite reports 420 passed and 5,110 subtests passed, up from 239 and
  5,110 before this step; no previously passing test changed status.

**Not checked.**

- **Natural-language coverage.** The parser was exercised on 20 battery
  queries, 6 refusals and the parser tests. There is no held-out corpus of
  phrasings, so the rate at which a plausible user query is misclassified is
  unmeasured. The rules are transparent and the parse trace is always
  available, which bounds the cost of a misclassification but does not
  bound its frequency.
- **Solver correctness beyond the kernel's own tests.** The runtime is a
  routing and presentation layer; the mathematics it reports is Step 1–3's,
  under those steps' own limits.
- **Analogy quality.** The default subspaces
  (`physics.dimension`, `chemistry.position`) are inherited choices, not
  results of a tuning study, and no accuracy figure is claimed for the
  analogy solver here.
- **Performance.** Wall-clock figures are deliberately not recorded as data,
  so the artefacts stay byte-stable between runs; no throughput claim is made.
- **The `product` solver's pair selection** takes the first 2A partner in
  sorted class order. That is deterministic and checked, but it is one pair,
  not a census over the 9,200-partner orbit — the widening carried over from
  Step 3.

## Next steps (after GLM-3+ Step 1 runtime)

1. **A held-out query corpus** with per-rule precision, so parser
   misclassification becomes a measured quantity rather than an unmeasured
   one.
2. **Widen column 3's independence.** Today it re-enters the same API. A
   second template family that recomputes from the substrate primitives alone
   would turn the cross-check into something closer to a real reproduction.
3. **ARC-style spatial tasks.** The spatial register presents MOG structures;
   the next step is grid-to-grid transformation queries over it.
4. **A `benchmarks` suite** wiring the runtime to scored task sets, which is
   what `glm_universal/benchmarks` is reserved for.



