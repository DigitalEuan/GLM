# 'data_object/' - DATA OBJECT — Encoding System

**Version:** 5.2.0  (13 August 2026)
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand   
**Parent:** `../README.md`

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- How to encode any subject (element, molecule, word, number, shape) as a 24-bit Data Object in the Leech lattice.  

---

## Role in the System

```
GMHGL/              ← provides Golay engine, TAX, NRCI
  ↓ imported by
data_object/ (this folder)
  ├── reads KB from  → ../long_term_memory/ubp_system_kb.json
  ├── imports engine from → ../GMHGL/ubp_unified_v5.py
  ├── writes training data to → ../long_term_memory/glm_training_data.json
  └── provides encoding to
        ├── ../glm_machine/    (mind uses encoding to perceive subjects)
        ├── ../arc_agi_(version_number)/     (use encoding for grid Data Objects)
        └── ../long_term_memory/ (consolidated training data)
```

---

## What's Here

| Path | Purpose | Connects To |
|------|---------|-------------|
| `encoding_specification.md` | Experimental encoding spec | — |
| `elements.md` | Element encoding knowledge | sub-doc of README |
| `molecules.md` | Molecule encoding knowledge | sub-doc of README |
| `scripts/encoding_spec.py` | EncodingSpec dataclass + scoring | imports GMHGL |
| `scripts/kb_adapter.py` | KB parser (118 elements, 82 molecules) | to read from ../long_term_memory/ |
| `scripts/spatial_arithmetic.py` | R(n), EML, 3D geometry | — |
| `scripts/elements_data_object_system.py` | Complete Data Object system (Golay, encoding, interaction, prediction) | — |
| `scripts/training_*.py` | 15 training scripts | imports GMHGL |
| `scripts/training_accumulate.py` | Builds consolidated data | writes to long_term_memory/ |
| `encoding_definition_attempt_04.08.26/` | **Latest experiment — warping + geometric work + calibration** | — |
| `encoding_definition_attempt_03-08.26/` | Previous encoding attempt | — |
| `Elements encoding experiment:test_Barnes256.txt` | 256-D Barnes-Wall Macro-Lattice spec | — |
| `MOG_experiment_1.txt` | MOG Spatial Arithmetic + Geometric Interaction Primitives | — |
| `mog_cube_1/` | Mathlib development that puts measurable meaning on the 24-cell
MOG/Golay data object and builds a small language on top of it | — |

---

## Latest Results (13 August 2026)

**Experiment:** `mog_cube_1/`

A Lean 4 / Mathlib development that puts measurable meaning on the 24-cell
MOG/Golay data object and builds a small language on top of it: words with
physical dimension, sentences that are true, connectives (`and`, `but`, `so`)
with measured meanings, a conversation that remembers, and plans that say what
to do

---

## Results (4 August 2026)

**Experiment:** `encoding_definition_attempt_04.08.26/`

### Bond Energy Prediction (114 pairs, 5-fold CV)

| Method | BE r | BO Accuracy | Notes |
|--------|------|-------------|-------|
| Random Forest (identity) | 0.10 | 81.6% | Baseline |
| Flip activation all | 0.51 | 86.8% | Activation row warping |
| **rotate_3 + flip** | **0.55** | **86.8%** | **Best combined warp** |

### Element Property Prediction

| Property | r |
|----------|---|
| Electronegativity | 0.92 |
| Boiling Point | 0.95 |
| Melting Point | 0.87 |
| Density | 0.82 |

### Key Findings

1. **The Activation row is the bond formation layer** — diff_A r=0.50
2. **Warping the Activation row creates bond-order sectors** — r=0.55
3. **Geometric work (path integral) carries independent signal** — partial r=0.33
4. **The snap process is part of the interaction mechanism** — snap energy monotonic with BO
5. **Empirical calibration: 190 kJ/mol per work unit** — tick=2.10 fs, cell=17 μm
6. **The substrate operates at molecular scale** — explains chemistry mapping

### What This Enables

- Element Data Objects can predict bond energy (r=0.55) and bond order (86.8%)
- The same warping principle applies to language (Activation → Verbs)
- Geometric work provides a calibrated energy scale (190 kJ/mol per unit)
- The Three-Column Diagnostic inspects any bond with aligned Language/Math/Script

---

## Dependencies

| Needs From | What |
|-----------|------|
| `../GMHGL/ubp_unified_v5.py` | Golay snap, TAX, NRCI |
| `../long_term_memory/ubp_system_kb.json` | Element/molecule data |
| `scripts/ubp_kb_loader.py` | KB parser |

## Produces For

| Provides To | What |
|------------|------|
| `../long_term_memory/glm_training_data.json` | All training data |
| `../glm_machine/` | Encoding methods for subjects |
| `../arc_agi_(version_number)/` | Grid Data Object encoding |

---

## Subject Knowledge

| Subject | Document | Best Encoding | Best Result |
|---------|----------|--------------|-------------|
| 118 elements | [elements.md](elements.md) | EN×10, BP÷40, MP÷40, Rho×10 | r(ΔH) = −0.91 |
| 82 molecules | [molecules.md](molecules.md) | M (log2), MP (div40) | r(ΔH) = +0.96 |
| 36 bonds | CALIBRATION_LOG.md | AND encoding | r(BE) = +0.90 |
| 114 pairs (warped) | encoding_definition_attempt_04.08.26/ | rotate_3 + flip | r(BE) = +0.55, BO acc = 86.8% |
| 95 words | CALIBRATION_LOG.md | length+POS+valence+vowels | 71 unique vectors |
| 256 numbers | CALIBRATION_LOG.md | MOG Gray code | 132 unique codewords |
| Shapes | CALIBRATION_LOG.md | Active-bit patterns | compactness → 1.0 |

---

## Quick Start

```bash
cd scripts

# Element training
python3 training_iteration.py

# Molecule training
python3 training_iteration_v3.py

# Bond geometry
python3 training_bond_geometry.py

# Pattern solving
python3 training_pattern_mind_v2.py

# Language
python3 training_language_v2.py

# Rebuild consolidated data → long_term_memory/
python3 training_accumulate.py

# Latest experiment (warping + geometric work)
cd ../encoding_definition_attempt_04.08.26/scripts
python3 geometric_work.py --full-test
python3 geometric_work.py --diagnose H O 1
python3 warp_optimizer.py --calibrate
```

---

## Scaling Presets

| Preset | Formula | Best For |
|--------|---------|----------|
| identity | int(abs(f)) & 0x3F | Z, BP, MP |
| div40 | int(abs(f)//40) & 0x3F | BP, MP |
| en_x10 | int(abs(f)*10) & 0x3F | EN |
| log2 | int(log2(max(abs(f),1))) & 0x3F | M |
| rho_x10 | int(abs(f)*10) & 0x3F | Rho |
| valence_redundant | (v&7)<<3 \| (v&7) | Valence_e |

---

## Warping Strategies (from encoding_definition_attempt_04.08.26)

| Strategy | BE r | BO Acc | Description |
|----------|------|--------|-------------|
| identity | 0.10 | 81.6% | No warping (baseline) |
| swap_2_3 | 0.21 | 81.6% | Swap MOG columns 2↔3 for BO≥2 |
| flip_act_half | 0.27 | — | Flip bits 12-14 for BO≥2 |
| swap_3_4 | 0.38 | — | Swap MOG columns 3↔4 for BO≥2 |
| rotate_3 | 0.47 | — | Rotate all columns by 3 for BO≥2 |
| flip_act_all | 0.51 | 86.8% | Flip bits 12-17 for BO≥2 |
| **rotate_3 + flip** | **0.55** | **86.8%** | **Rotate 3 + flip activation for BO≥2** |

---

## Geometric Work Calibration

| Quantity | Value | Physical Meaning |
|----------|-------|-----------------|
| Scale factor | 190 kJ/mol per work unit | Matches Br-Br bond energy |
| Tick duration | 2.10 femtoseconds | Molecular vibration timescale |
| Cell length | 17.0 micrometres | Molecular domain scale |
| Formula | BE_kJ = geometric_work × 190 | Direct thermodynamic output |

---

## Folder Structure

```
data_object/
├── README.md                          ← This document (v5.0.0)
├── encoding_specification.md          ← Formal spec
├── elements.md                        ← Element encoding knowledge
├── molecules.md                       ← Molecule encoding knowledge
├── CALIBRATION_LOG.md                 ← Full iteration log
├── BENCHMARKS.md                      ← Benchmark tracking
├── test_ledger.md                     ← Test records
├── scripts/
│   ├── encoding_spec.py               ← EncodingSpec + scoring harness
│   ├── kb_adapter.py                  ← KB parser
│   ├── spatial_arithmetic.py          ← 3D geometry
│   ├── elements_data_object_system.py ← Complete Data Object system (NEW)
│   ├── training_*.py                  ← Training scripts (15 files)
│   └── experiment/                    ← Original E0-E7 experiments
├── encoding_definition_attempt_04.08.26/  ← LATEST EXPERIMENT
│   ├── README.md                      ← Experiment spec + results
│   ├── scripts/ (9 scripts, ~8000 lines)
│   │   ├── elements_data_object_system.py  ← Base system
│   │   ├── expanded_element_system.py      ← 114 pairs, 5-fold CV
│   │   ├── refined_element_system.py       ← Snap dynamics
│   │   ├── glm_training_cycle.py           ← Settlement dynamics
│   │   ├── pair_bond_geometry.py           ← Bond as geometric object
│   │   ├── refined_warping.py              ← Warping strategy sweep
│   │   ├── three_directions.py             ← Nonlinear + understanding
│   │   ├── geometric_work.py               ← Geometric work + diagnostics
│   │   └── warp_optimizer.py               ← Permutation optimizer + calibration
│   ├── data/ (8 JSON result files)
│   └── results/ (6 report files)
├── encoding_definition_attempt_03-08.26/  ← Previous attempt
├── data/                              ← Results (JSON)
└── vis/                               ← Visualizations
```

---

## Change Log

| Version | Date | Change |
|---------|------|--------|
| 4.0.0 | 2026-08-03 | Initial structure with encoding spec, elements, molecules |
| 5.0.0 | 2026-08-04 | Added encoding_definition_attempt_04.08.26 with warping optimization, geometric work, empirical calibration. BE r=0.55, BO acc=86.8%, scale=190 kJ/mol. |
