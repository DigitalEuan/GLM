# 'long_term_memory/ - The Long-Term Memory and Training Data

**Version:** 1.1.0  (7 August 2026) 
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand 
**Parent:** `../README.md`

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- Single source of truth for all GLM training data and learned knowledge.  

- GLM training builds glm_training_data.json and GLM_KNOWLEDGE.md with successful input 

- Failed training tests and data aren't recorded in glm_training_data.json and GLM_KNOWLEDGE.md. 

---

## Role in the System

```
GMHGL/              ─┐
data_object/        ─┤── all training data flows here
glm_machine/        ─┤
arc_agi_15/         ─┤
arc_agi_16/         ─┘
        ↓
long_term_memory/ (this folder)
├── glm_training_data.json   ← consolidated data from GLM training
└── GLM_KNOWLEDGE.md         ← consolidated knowledge from all folders
```

This folder **receives** from everywhere. It serves other folders.

---

## Files

| File | Size | Content |
|------|------|---------|
| `glm_training_data.json` | ~780KB | ALL training data in one JSON |
| `GLM_KNOWLEDGE.md` | ~7KB | ALL learned knowledge in one document |
| `ubp_system_kb.json` | ~1.7MB | UBP knowledge bank - 'Law' and 'LAW_' entries are UBP study findings, also includes full Table of Elements data and other deterministic data for active studies |

---

## What's in glm_training_data.json

| Section | Source | Content |
|---------|--------|---------|
| `elements` | data_object/ | 118 elements × 3 specs, 354 Data Objects |
| `bonds` | data_object/ | 36 bonds, AND encoding, r(NRCI×BO,BE)=0.90 |
| `molecules` | data_object/ | 82 molecules, M/MP encoding, 50 unique vectors |
| `patterns` | data_object/ | 10 learned patterns with confidence |
| `pattern_solving` | data_object/ | v1: 17/29, v2: 19/29 synthetic patterns |
| `arc_agi` | arc_agi_15/16 | basic: 1/50, enhanced: 8/50, learning: 9/50 |
| `experience` | arc_agi_16/ | Routing table (150 entries) |
| `benchmarks` | data_object/ | Pattern solving across runs |
| `training_log` | all | All runs with timestamps |

---

## How to Update

```bash
# After any training run, rebuild from source:
cd ../data_object/scripts
python3 training_accumulate.py
```

The script reads from `data_object/data/` and writes here - the training testing area.

---

## What's in GLM_KNOWLEDGE.md

1. The Substrate (Golay, MOG, Leech, Y, TAX, NRCI)
2. Element Training (r(ΔH)=−0.91)
3. Bond Training (r(BE)=+0.90)
4. Pattern Solving (19/29 synthetic)
5. ARC-AGI (9/50, experience routing)
6. Language (words as Data Objects)
7. Open Questions

---

## Quick Start


