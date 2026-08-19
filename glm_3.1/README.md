# glm_new/ — The Unified Geometric Language Machine

**Version:** 5.0.0 (20 August 2026)
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand
**Parent:** `../README.md`

---

## What This Is

A clean, unified GLM that combines the best of all four systems:

| Component | Source | What It Does |
|-----------|--------|-------------|
| **Reasoning** | `glm_lean/glm3/` | Exact equation verification, formula discovery, Buckingham Pi, 660-concept library, Griess algebra (196,884 dims) |
| **Language** | `glm_machine/` (concept) | Three Column Thinking: every answer has Language + Math + Script |
| **Learning** | new | Text ingestion → definition extraction → CRG growth |
| **Carrier** | `glm_lean/glm2/` | Leech lattice point derived from meaning (never primary) |

**Key design principle:** Meaning is primary. The carrier is derived. All reasoning is exact (Fraction arithmetic, no floats).

---

## Quick Start

```bash
cd glm_new

# Chat
python3 GLM.py --chat "What is energy?"
python3 GLM.py --chat "What is torque?"

# Verify equations
python3 GLM.py --verify energy "mass*speed^2"       # PASS
python3 GLM.py --verify energy "mass*speed^4"       # FAIL

# Derive formulas
python3 GLM.py --solve speed energy mass             # speed = √(E/m)

# Inspect concepts
python3 GLM.py --meaning energy
python3 GLM.py --nearest energy
python3 GLM.py --list
python3 GLM.py --domains

# Learn from text
python3 GLM.py --learn "Energy is mass times speed squared."

# Run tests
python3 test_glm.py

# Interactive mode
python3 GLM.py --interactive
```

---

## Architecture

```
                    ┌─────────────────────┐
                    │     GLM.py          │
                    │   (main entry)      │
                    └────────┬────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐ ┌──▼──────────┐ ┌▼──────────┐
     │   reasoner.py   │ │   tct.py    │ │learner.py │
     │ (glm3 wrapper)  │ │ (3-column)  │ │(learning) │
     └────────┬────────┘ └─────────────┘ └───────────┘
              │
     ┌────────▼────────────────────────────┐
     │        glm_lean/glm3/               │
     │  MonsterReasoner (660 concepts)     │
     │  Griess algebra (196,884 dims)      │
     │  Exact Fraction arithmetic          │
     └─────────────────────────────────────┘
```

### Data Flow

```
Query: "What is energy?"
  │
  ├─ reasoner.meaning("energy")
  │    → {L: 2, M: 1, T: -2}  (exact rational exponents)
  │
  ├─ reasoner.carrier("energy")
  │    → (1,0,1,1,0,0,...)  (24-bit Leech point, DERIVED)
  │
  ├─ reasoner.address("energy")
  │    → type_word: 2244344444, norm²: 6467552
  │
  ├─ reasoner.nearest("energy", 5)
  │    → [kinetic_energy, potential_energy, ...]
  │
  └─ tct.format(query, [definition, relationships, geometry, resolution])
       → Three Column output (Language + Math + Script)
```

---

## What Each Component Does

### reasoner.py — Exact Reasoning

Wraps `glm_lean/glm3/MonsterReasoner`. All math is exact Fractions.

| Method | What It Does | Example |
|--------|-------------|---------|
| `audit(lhs, rhs)` | Verify dimensions match | `audit("energy", "mass*speed^2")` → PASS |
| `solve(target, sources)` | Derive formula via Smith normal form | `solve("speed", ["energy","mass"])` → `√(E/m)` |
| `meaning(concept)` | Get exact rational exponents | `meaning("energy")` → `{L:2, M:1, T:-2}` |
| `carrier(concept)` | Get Leech lattice point | `carrier("energy")` → 24-bit tuple |
| `address(concept)` | Get Monster address | 10-plane stack, type word, axis planes |
| `nearest(concept, n)` | Griess algebra neighbours | Closest concepts by similarity |
| `pi_groups(names)` | Buckingham Pi groups | Dimensionless combinations |
| `relation(a, b)` | 10-letter type code | Algebraic relationship type |

### tct.py — Three Column Thinking

Every response has three aligned columns:

```
Step: DEFINITION
  LANGUAGE: energy is a physical quantity with dimensions [L² M T⁻²].
  MATH:     meaning(energy) = L² M T⁻², scale=0, rank=0
  SCRIPT:   m = reasoner.meaning('energy')
```

### learner.py — Text Learning

Extracts definitions and relations from text:

```python
glm.learn("Energy is mass times speed squared.")
# → learns definition, infers meaning from dimensional analysis
glm.learn("Force causes acceleration.")
# → learns CRG edge: force →causes→ acceleration
```

---

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `GLM.py` | ~300 | Main entry point + CLI + interactive mode |
| `reasoner.py` | ~250 | Wraps glm3's MonsterReasoner |
| `tct.py` | ~500 | Three Column Thinking engine |
| `learner.py` | ~200 | Text learning + CRG growth |
| `test_glm.py` | ~200 | Test suite (7 tests) |
| `README.md` | this | Documentation |

**Total: ~1,450 lines** (vs 1,297 files in the full repo)

---

## The 660 Concepts

The library contains 660 named physical quantities across 26 domains:

| Domain | Examples |
|--------|----------|
| Mechanics | energy, force, torque, momentum, power |
| Electromagnetism | electric_field, magnetic_flux, capacitance |
| Thermodynamics | entropy, heat_capacity, temperature |
| Optics | luminous_flux, illuminance, radiance |
| Quantum | planck_constant, bohr_magneton, fine_structure_constant |
| Information | shannon_entropy, bit_rate, channel_capacity |
| Dimensionless | reynolds_number, mach_number, pi |

Each concept has:
- **Exact meaning**: 10 rational exponents over L, M, T, I, H, N, J, A, S, B
- **Derived carrier**: Leech lattice point (24-bit, from meaning)
- **Monster address**: 10-plane stack in Λ/2Λ
- **Griess position**: location in 196,884-dimensional algebra

---

## Integration with Other Systems

This system is designed to be the **core** that other systems build on:

```
glm_new/ (this)
  ├── imports → glm_lean/glm3/ (exact reasoning)
  ├── could wrap → glm_machine/ (sandbox, persistence, corpus learning)
  ├── could verify → arc_agi_17/ (CRG edge dimensional consistency)
  └── could use → arc_agi_15/ (driving styles for strategy selection)
```

### Potential Integrations (not yet wired)

1. **glm_machine sandbox**: Add code execution capability
2. **arc_agi_17 CRG**: Verify solver-proposed transformation rules dimensionally
3. **arc_agi_15 styles**: Import driving styles for problem-solving strategy
4. **Corpus learning**: Use glm_machine's SVD vocabulary as a word→concept bridge

---

## Dependencies

- **Python ≥ 3.10**
- **No pip installs** — stdlib only (Fraction, json, re, pathlib)
- **Requires** `glm_lean/glm3/`, `glm_lean/glm2/`, `glm_lean/glm/` in parent directory

---

## License

Part of the GLM research initiative by Euan R. A. Craig. Experimental — verify results independently.
