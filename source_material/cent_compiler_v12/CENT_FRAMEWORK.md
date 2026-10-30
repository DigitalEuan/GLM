# The £ → ¢ → ∆ Physical Compiler — Canonical Documentation

**Version:** 2.0  
**Date:** 2026-10-30  
**Codename:** `cent_compiler_v2`

---

## Overview

The £ → ¢ → ∆ framework is a **cross-domain physical compiler** with a **living knowledge base**. Given any abstract operation £, it:

1. **Decomposes** £ into a directed acyclic graph of atomic ¢ steps.
2. **Enumerates** all valid physical ∆ implementations across electrical, mechanical, fluidic, thermal, rotational, optical, digital, spintronic, and bio-chemical domains.
3. **Ranks** them by a 6-axis cost function.
4. **Escalates** each through 5 fidelity layers (ideal → parasitic → thermal → quantum → fabricated).
5. **Re-lifts** (conjecture loop) if a ∆ fails — tries the next-best substrate.
6. **Certifies** the result in a parametric ledger with exact parameter ranges.
7. **Emits** a SPICE netlist for the chosen ∆.
8. **Manages** knowledge state via the Cent Wheel (KNOWS / THINKS-TRUE / DOESN'T-KNOW / NEEDS / LANGUAGE).

Delta-sigma modulation is recognized as **one valid ∆ among many** — the canonical carrier for irrational numbers via temporal bitstream relaxation.

---

## 1. The ¢ Vocabulary (v2.0)

### 1.1 The 16 atomic primitives

| Primitive | Math | Canonical ∆ substrate | Carrier |
|-----------|------|----------------------|---------|
| `¢_sum` | y = a + b | KCL node; force sum | temporal |
| `¢_neg` | y = -a | inverting op-amp | temporal |
| `¢_mult` | y = a · b | Gilbert cell; DC motor | temporal |
| `¢_scale` | y = k · a | resistor divider; gear train | temporal |
| `¢_accum` | y = ∫a dt | capacitor; mass; microfluidic chamber; photonic cavity | temporal |
| `¢_rate` | y = da/dt | inductor; piezoelectric bimorph | temporal |
| `¢_wrap` | y = a mod 2π | rotary encoder; Mach-Zehnder interferometer | phase-wrap |
| `¢_spatial` | y = ∫a·dB | search coil; bifilar pendulum | spatial |
| `¢_exp` | y = e^a | BJT/diode; enzyme kinetic (Arrhenius) | temporal |
| `¢_log` | y = ln(a) | translinear log amplifier | temporal |
| `¢_sat` | y = tanh(a) | op-amp clipper with zeners | temporal |
| `¢_hysteresis` | y = H(a, state) | magnetic tunnel junction (MTJ) | static |
| `¢_grad` | y = ∇ψ | thermal conduction bar (Fourier) | spatial |
| `¢_div_spatial` | y = ∇·A | divergence (flux conservation) | spatial |
| `¢_curl` | y = ∇×A | Maxwell's equations; vorticity | spatial |
| `¢_delay` | y(t) = a(t-τ) | acoustic waveguide; optical fiber | temporal |

### 1.2 The 6 composite primitives

| Composite | Math | Built from |
|-----------|------|-----------|
| `¢_recip` | y = 1/a | `¢_eq` with `¢_mult` |
| `¢_div` | y = a/b | `¢_mult(a, ¢_recip(b))` |
| `¢_sqrt` | y = √a | `¢_eq` with `¢_mult` |
| `¢_eq` | y s.t. f(y)=target | `¢_mult + ¢_sum + ¢_feedback` |
| `¢_translinear` | y = a^b | `¢_log → ¢_mult → ¢_exp` |
| `¢_state_space` | ẋ = Ax + Bu | coupled `¢_accum + ¢_scale + ¢_sum` |

### 1.3 Which ¢ primitives appear in which wheels

The 31 wheels encode static monomial axioms. Only `¢_mult`, `¢_scale`, `¢_div`, and `¢_sqrt` appear in wheel spokes. The other primitives (`¢_sum`, `¢_accum`, `¢_rate`, `¢_wrap`, `¢_eq`, `¢_spatial`, `¢_exp`, `¢_log`, `¢_sat`, `¢_hysteresis`, `¢_grad`, `¢_div_spatial`, `¢_curl`, `¢_delay`) appear only in the £ test suite, which extends beyond wheel spokes to span the full vocabulary.

---

## 2. The Wheel Data Substrate (31 wheels)

All wheel data is loaded from JSON files in `wheels/` — the single source of truth. No hardcoded data in Python.

| Family | Wheels | Domains |
|--------|--------|---------|
| Original (Phase 66) | W1-W10 | DC circuits, AC impedance, capacitors, rotational, linear dynamics, fluids, acoustics, thermal, waves, photons |
| Domain (Phase 157) | W11-W15 | Uniform motion, density, oscillator, LC circuit, charge-time |
| Expanded (v2.0) | W16-W19 | Magnetic flux, gravitation, ideal gas, EM waves |
| Computational Depth | W20-W35 | Elasticity, fracture, chemical kinetics, electrochemistry, semiconductor, plasma, superconductivity, spintronics, capillarity, heat transfer, hemodynamics, electrophysiology |

**Totals:** 31 wheels, 72 axioms, 119 cases, 108 dimensional vectors, 33 junctions, 5 non-identities.

---

## 3. The ∆ Substrate Library

### 3.1 Expansion rules

Each ¢ primitive has multiple expansion rules across substrate domains. The cartesian product of expansion choices = all valid ∆ for a given £.

Total expansion rules: ~38 (including v2.0 additions for microfluidic chamber, photonic cavity, piezo bimorph, Mach-Zehnder, translinear BJT, enzyme kinetic, MTJ, thermal conduction bar, acoustic delay, optical fiber delay, translinear cell).

### 3.2 The 7 TIER 3 transducer analogies

| Transducer | Wheel pair | Convention |
|------------|-----------|------------|
| Paynter effort-flow | W1 ↔ W7 | impedance |
| Rotational-linear | W4 ↔ W5 | impedance |
| Capacitor-inductor duality | W3 ↔ W14 | impedance |
| Electromechanical (Piezo/Lorentz) | W1 ↔ W5 | mobility |
| Thermoelectric (Seebeck/Peltier) | W1 ↔ W8 | impedance |
| Optoelectronic (Photodiode/EOM) | W1 ↔ W19 | impedance |
| Electro-Hydrodynamic (Pump/Sense) | W1 ↔ W6 | impedance |

---

## 4. The Three-Tier Isomorphism Gate

| Tier | Label | Requirements | What it means |
|------|-------|-------------|---------------|
| 1 | CANDIDATE | Shape match only | Never a solution |
| 2 | ADMISSIBLE | + axiom-verified + dim-consistent + residual empty | Axiom transfer only |
| 3 | COMPILABLE | + declared analogy + transducer equations | Full hardware compilation |

---

## 5. The Delta-Sigma Signature

**Delta-Sigma is NOT a property of a single substrate.** It is a property of a COMPOSED LOOP:

```
¢_accum (integrator) + ¢_wrap (quantizer) + ¢_eq (feedback) + oversampling
```

A capacitor is a CONSTITUENT of delta-sigma, not delta-sigma itself. The `classify_delta()` function examines the full ∆ implementation and classifies it as `delta_sigma`, `equilibrium_seeking`, or `direct`.

**Core claim:** Delta-Sigma modulation is the physical process that carries irrational numbers without storing them.

---

## 6. The Hypothesis Bridge (Knowledge State Management)

Adopted from the GLM Hypothesis Engine v18:

### 6.1 The Cent Wheel (5 rings)

| Ring | What goes there |
|------|----------------|
| KNOWS | SPICE-verified AND physically fabricated ∆ |
| THINKS-TRUE | Passes simulation, not yet built |
| DOESN'T-KNOW | Theoretically valid, untested |
| NEEDS | "need:spice_verification", "need:physical_fabrication", "need:noise_analysis" |
| LANGUAGE | Safe to cite in safety-critical designs |

### 6.2 The 5-Layer Escalation

| Layer | What gets added |
|-------|----------------|
| ideal | Perfect components, no noise |
| parasitic | Finite gain, ESR, tolerance |
| thermal | Johnson noise, temperature drift |
| quantum | Shot noise, tunneling |
| fabricated | Manufacturing variation, aging |

### 6.3 The Conjecture Loop

If a ∆ fails at a fidelity layer, the compiler re-lifts with the next-best substrate from the cost-ranked list. The first ∆ that converges (passes all 5 layers) is returned.

### 6.4 The Parametric Ledger

Each ∆ is certified with exact parameters (voltage range, bandwidth, temperature, tolerance). This prevents overclaiming.

---

## 7. The ¢_cost Function

6 axes: component_count, domain_consistency, carrier_consistency, implementation_cost, precision, speed. Lower total = better ∆. Deduplication by (domain, carrier, ∆Σ) signature prunes the £_osc explosion (57,600 → 6 diverse picks).

---

## 8. Verified Results

- **7 of 7** core simulations pass (delta-sigma integrator, op-amp sqrt, PLL, capacitor differentiator, KCL summer, search coil, thermal relaxation)
- **3 of 3** delta-sigma showcase checks pass (√2 carrier, 36.9 dB noise suppression, 28.0 dB/dec NTF slope)
- **22 of 22** show-work proposals pass the full 8-step pipeline (decompose → enumerate → cost-rank → escalate → conjecture loop → emit .cir)
- **22 .cir files** written to disk (one per proposal, 9 SPICE templates)
- **6 of 7** original application proposals pass (1 dimensional check, honestly classified)
- **Total: 38/39 tests pass** (1 dimensional check)

---

## 9. Known Gaps

### Resolved
- Gap 1: £_osc pruning (57,600 → 6) — resolved by ¢_cost + deduplication
- Gap 4: model_convention handling — resolved by flagging convention cases

### Deferred to v3
- Gap 2: ¢_noise axis in cost function (partially addressed by escalation layers)
- Gap 3: Cross-domain netlisting (SPICE → Modelica → GDSII)
- Gap 5: Full native solver integration (ngspice, OpenModelica, OpenFOAM)
- Gap 6: Algorithmic £ synthesis (PID controllers, neural network crossbars)

---

## 10. File Layout

```
cent_compiler_v1/
├── README.md
├── CENT_FRAMEWORK.md            # this document
├── DELTA_SIGMA_DEMO.md           # standalone flagship demo
├── VALIDATION_REPORT.md         # honest test results
├── cent                         # CLI tool (5 subcommands)
├── cent_compiler/               # Python package (12 modules)
│   ├── __init__.py              # v2.0, 49 exports
│   ├── grammar.py               # 22 ¢ primitives + AST decomposer
│   ├── wheels.py                # 31 wheels loaded from JSON
│   ├── substrate_library.py     # ~38 ∆ expansion rules
│   ├── pattern_matcher.py       # 3-pattern clustering
│   ├── cost_function.py         # 6-axis ¢_cost + pruning
│   ├── isomorphism_gate.py      # 3-tier gate + ∆Σ classifier + 7 transducers
│   ├── simulator.py             # 7 verified simulations
│   ├── spice_emitter.py         # SPICE netlist generation + .cir file output
│   ├── delta_sigma.py           # ∆Σ engine + flagship demonstration
│   ├── pound_suite.py           # 8 £ test cases
│   └── hypothesis_bridge.py     # Cent Wheel + escalation + conjecture loop + ledger
├── applications/                # 7 application proposals
├── expansion/                   # roadmap documents + Hypothesis Engine reference
├── tests/                       # validation tests + wheel generators
├── wheels/                      # 32 JSON files (31 wheels + index) — single source of truth
└── examples/                    # 5 .cir files + demo output
```

---

## References

1. Paynter, H.M. (1961). *Analysis and Design of Engineering Systems*. MIT Press.
2. The GLM Wheel System: `github.com/DigitalEuan/GLM`
3. The GLM Hypothesis Engine v18 — the epistemology engine that inspired the Cent Wheel.
