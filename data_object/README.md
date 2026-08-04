# DATA OBJECT — Encoding System

**Version:** 4.0.0  (3 August 2026)
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
| `encoding_specification.md` | Formal encoding spec | — |
| `elements.md` | Element encoding knowledge | sub-doc of README |
| `molecules.md` | Molecule encoding knowledge | sub-doc of README |
| `scripts/encoding_spec.py` | EncodingSpec dataclass + scoring | imports GMHGL |
| `scripts/kb_adapter.py` | KB parser (118 elements, 82 molecules) | to read from ../long_term_memory/ |
| `scripts/spatial_arithmetic.py` | R(n), EML, 3D geometry | — |
| `scripts/training_*.py` | 15 training scripts | imports GMHGL |
| `scripts/training_accumulate.py` | Builds consolidated data | writes to long_term_memory/ |
| `experiments/` | Various experiments to define and refine encoding | — |
| `data/` | Experiment results (JSON) | — |
| `vis/` | Renders of experiment findings | — |
| `encoding_definition_attempt_(DATE)/` | Attempts at defining and refining the exact encoding method for data input to the UBP/GLM system | — |
| `Elements encoding experiment/test_Barnes256.txt` | The next Elements encoding experiment to do | — |

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
| 95 words | CALIBRATION_LOG.md | length+POS+valence+vowels | 71 unique vectors |
| 256 numbers | CALIBRATION_LOG.md | MOG Gray code | 132 unique codewords |
| Shapes | CALIBRATION_LOG.md | Active-bit patterns (should be geometry defined by 'spatial_arithmetic.py' | compactness → 1.0 |

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

## Folder Structure

```
data_object/
├── README.md                    ← This document
├── encoding_specification.md    ← Formal spec
├── elements.md                  ← Element knowledge
├── molecules.md                 ← Molecule knowledge
├── CALIBRATION_LOG.md           ← Full iteration log (20 iterations)
├── BENCHMARKS.md                ← Benchmark tracking
├── scripts/
│   ├── encoding_spec.py         ← EncodingSpec + scoring harness
│   ├── kb_adapter.py            ← KB parser
│   ├── spatial_arithmetic.py    ← 3D geometry
│   ├── ubp_unified_v5.py       ← Copy of GMHGL engine
│   ├── training_*.py            ← Training scripts (15 files)
│   └── experiment/              ← Original E0-E7 experiments
├── data/                        ← Results (JSON)
└── vis/                         ← Visualizations
```
