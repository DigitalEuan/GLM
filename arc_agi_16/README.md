# ARC-AGI v16 — Next Iteration Experiments

**What it is:** Experimental ARC solvers using trained substrate knowledge.  
**Parent:** `../README.md`

---

## Role in the System

```
glm_machine/        ← provides mind architecture
data_object/        ← provides encoding + training data
long_term_memory/   ← provides experience routing table
  ↓ all used by
arc_agi_16/ (this folder)
  └── writes results to → ../long_term_memory/glm_training_data.json
```

---

## Dependencies

| Needs From | What |
|-----------|------|
| `../glm_machine/consolidated_mind.py` | Toolkit solvers |
| `../data_object/scripts/training_bond_geometry.py` | AND encoding, snap costs |
| `../long_term_memory/glm_training_data.json` | Experience, patterns |
| `../GMHGL/ubp_unified_v5.py` | Golay engine |

---

## Quick Start

```bash
# Basic substrate mind (1/50)
python3 arc_substrate_mind.py

# Enhanced mind (8/50)
python3 arc_enhanced_mind.py

# Learning mind (9/50)
python3 arc_learning_mind.py
```

---

## What's Here

| File | Score | Description |
|------|-------|-------------|
| `arc_substrate_mind.py` | 1/50 | Basic heuristics + Data Object encoding |
| `arc_enhanced_mind.py` | 8/50 | Toolkit + substrate ranking |
| `arc_learning_mind.py` | 9/50 | Experience-guided strategy selection |
