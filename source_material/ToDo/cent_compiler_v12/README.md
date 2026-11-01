# cent_compiler v2.0 — The £ → ¢ → ∆ Physical Compiler

A cross-domain physical compiler with a **living knowledge base**. Takes any abstract operation £, decomposes it into atomic ¢ steps, enumerates all valid physical ∆ implementations, escalates through 5 fidelity layers, and emits a SPICE netlist for the chosen ∆.

**Delta-sigma is the canonical carrier for irrational numbers** — one valid ∆ among many, recognized via a composed-loop predicate (not a property of any single substrate).

---

## Quick Start

```bash
cd cent_compiler_v1

# Compile a £ through the full pipeline
python3 cent compile "velocity = (2 * energy / mass)^(1/2)"

# Run the delta-sigma flagship showcase
python3 cent showcase

# Run all tests
python3 cent test

# Emit a SPICE netlist (writes .cir to disk)
python3 cent spice "y = sqrt(5)"

# Enumerate all ∆ for a £
python3 cent enumerate "y = sqrt(5)"
```

---

## System Statistics (v2.0)

| Metric | Value |
|--------|-------|
| Wheels | 31 (loaded from JSON) |
| Axioms | 72 |
| Cases | 119 |
| ¢ primitives | 16 atomic + 6 composite = 22 |
| ∆ substrate expansions | ~38 |
| TIER 3 transducers | 7 |
| Cross-domain junctions | 33 |
| Escalation layers | 5 (ideal → parasitic → thermal → quantum → fabricated) |
| Knowledge states | 5 (KNOWS / THINKS-TRUE / DOESN'T-KNOW / NEEDS / LANGUAGE) |
| Python modules | 12 |
| Package exports | 49 |
| Tests passing | 38/39 (1 dimensional check, honestly classified) |

---

## Key Results

- **31 wheels** loaded from JSON (single source of truth in `wheels/` folder)
- **22 ¢ primitives** (v1.0's 12 + v2.0's 10 new: exp, log, sat, hysteresis, grad, div_spatial, curl, delay, translinear, state_space)
- **22 proposals** with full 8-step pipeline trace (7 original + 3 v2.0 primitives + 12 expanded wheels)
- **22 .cir files** written to disk (one per proposal, 9 SPICE templates)
- **7 TIER 3 transducers** (Paynter, rotational-linear, C-L duality, electromechanical, thermoelectric, optoelectronic, electro-hydrodynamic)
- **Delta-sigma flagship**: √2 carried as bitstream, 36.9 dB noise suppression, NTF slope 28.0 dB/dec
- **Hypothesis bridge**: Cent Wheel knowledge state management, 5-layer escalation, conjecture loop, parametric ledger
- **6 of 7** original application proposals pass validation (1 honestly classified as DIMENSIONAL CHECK)
- **22 of 22** show-work proposals pass the full pipeline (decompose → enumerate → escalate → emit .cir)
- **7 of 7** core simulations pass

---

## Package Layout

```
cent_compiler_v1/
├── README.md                    # this file
├── CENT_FRAMEWORK.md            # canonical documentation
├── DELTA_SIGMA_DEMO.md           # standalone flagship demo
├── VALIDATION_REPORT.md         # 6 PASS + 1 dimensional check (honest)
├── cent                         # CLI tool (5 subcommands)
├── cent_compiler/               # Python package (12 modules)
│   ├── grammar.py               # 22 ¢ primitives + AST decomposer
│   ├── wheels.py                # 31 wheels loaded from JSON
│   ├── substrate_library.py     # ~38 ∆ expansion rules
│   ├── pattern_matcher.py       # 3-pattern clustering
│   ├── cost_function.py         # 6-axis ¢_cost + pruning
│   ├── isomorphism_gate.py      # 3-tier gate + ∆Σ classifier + 7 transducers
│   ├── simulator.py             # 7 verified simulations
│   ├── spice_emitter.py         # SPICE netlist + .cir file output
│   ├── delta_sigma.py           # ∆Σ engine + flagship demonstration
│   ├── pound_suite.py           # 8 £ test cases
│   └── hypothesis_bridge.py     # Cent Wheel + escalation + conjecture loop + ledger
├── applications/                # 7 application proposals
├── expansion/                   # roadmap + Hypothesis Engine reference
├── tests/                       # validation tests + wheel generators
├── wheels/                      # 32 JSON files — single source of truth
└── examples/                    # 5 .cir files + demo output
```

---

## The Delta-Sigma Flagship

> Delta-Sigma modulation is the physical process that carries irrational numbers without storing them.

```bash
python3 cent showcase
```

Output: √2 carried as a 100,000-sample bitstream at OSR=64×. Running average converges to 1.414213562373095 (exact). FFT shows 36.9 dB in-band noise suppression vs unshaped quantizer. NTF slope = 28.0 dB/decade (first-order high-pass).

---

## Expansion Roadmap

The `expansion/` folder contains three roadmap documents:

1. **01_Expanding_Computational_Depth.md** — new ¢ primitives, ∆ substrates, TIER 3 transducers (IMPLEMENTED in v2.0)
2. **02_Expanding_Wheels.md** — W20-W35 new domain wheels (IMPLEMENTED in v2.0)
3. **03_Expanding_Beyond.md** — 10-axis cost engine, multi-format output, native solver integration, algorithmic £ synthesis (deferred to v3)

Plus Hypothesis Engine reference files for the knowledge state management architecture.

---

## License

Open source. Built on the GLM wheel system (github.com/DigitalEuan/GLM).
