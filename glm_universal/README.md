# `glm_universal` — GLM-3+, the Universal MOG-Cube Geometric Language Machine

**Version:** 0.4.0 (21 August 2026)
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand
**Parent:** `../README.md`

A self-contained, exact, deterministic implementation of the geometric
substrate the Monster group acts on, the reasoning layers built on it,
and the Three Column Thinking harness that runs queries through
language, mathematics, and executable script.

---

## Status

| Step | Module | Tests | Status |
|---|---|---|---|
| 1 | `substrate/` — linalg, MOG, Leech, digit stack | 96 | ✓ complete |
| 2 | `data_objects/` — physics (660), chemistry (118), math (22), lexicon (10) | 177 | ✓ complete |
| 3 | `reasoning/` — product, metric, analogy, verifier, coherence, dimension_layers | 62+18+16 | ✓ complete |
| 4 | `runtime/` — parser, session, TCT engine | 181 | ✓ complete |
| 5 | `examples/` — TCT demo, encoding POC, integrated NRCI, scaled carriers | — | ✓ working |

**Total: 271 tests, 5,110 subtests, zero regressions.**

---

## Quick Start

```bash
cd /path/to/GLM
PYTHONPATH=. python3 glm_universal/examples/demo_tct.py
PYTHONPATH=. python3 -m pytest glm_universal/tests/ -q
```

---

## Architecture

```
glm_universal/
├── README.md                  ← you are here
├── __init__.py                ← package-level exports
├── substrate/                 ← Step 1: the algebraic + geometric foundation
│   ├── linalg.py              exact integer / F₂ linear algebra
│   ├── mog.py                 Golay code, hexacode, MOG trio, sextet, cubes
│   ├── leech2.py              Leech lattice, Λ/2Λ, Witt data, 2A axes
│   └── digit_stack.py         10-plane 2-adic stack, facet attribution
├── data_objects/              ← Step 2: typed carriers over the substrate
│   ├── base.py                DataObject, Codec, StackParameters
│   ├── physics.py             660 physics quantities (EXT10 + SI7)
│   ├── elements.py            118 elements (measured properties + Golay address)
│   ├── mathematics.py         RationalMatrix, Reflection, FieldElement
│   ├── lexicon.py             Vocabulary, Concept (index-based)
│   └── _data/                 frozen exact-rational JSON snapshots
├── reasoning/                 ← Step 3: algebraic and geometric reasoning
│   ├── product.py             Norton-Sakuma 2A algebra, trilinear form ⟨u·v, w⟩
│   ├── metric.py              Griess form on Q²⁴, exact distances, clustering
│   ├── analogy.py             proportional analogy A:B::C→D, lattice projection
│   ├── verifier.py            multi-plane equation audit, facet attribution
│   ├── coherence.py           NRCI (5-shell), Y constant, coherence regimes
│   └── dimension_layers.py    five-layer dimension projection
├── runtime/                   ← Step 4: query processing and TCT
│   ├── parser.py              natural language query parser
│   ├── session.py             Solution, Step, session management
│   └── tct_engine.py          Three Column Thinking trace generation
├── tests/                     ← test suite
│   ├── test_substrate.py      96 tests
│   ├── test_data_objects.py   177 tests
│   ├── test_reasoning.py      94 tests (incl. trilinear form + dimension layers)
│   ├── test_runtime.py        181 tests (GLM.py dependent, pre-existing failures)
│   └── __init__.py
└── examples/                  ← demonstrations
    ├── demo_tct.py            Three Column Thinking demo (7 queries)
    ├── encoding_poc.py        element + word encoding proof of concept
    ├── integrated_nrci.py     NRCI + Griess metric integrated test
    └── scaled_carriers.py     scaled carriers + carrier-space product
```

---

## What's Been Done

### The Substrate (Step 1)
- Golay [24,12,8] code: 4,096 codewords, 759 octads, complete coset table
- Leech lattice Λ₂₄: 196,560 minimal vectors, Λ/2Λ class census (98,280 type-2)
- MOG trio and sextet: 4×6 frame, cube coordinates, facet attribution
- 10-plane digit stack: lossless reconstruction for arbitrary rational carriers

### Data Objects (Step 2)
- Physics: 660 quantities with 10 rational EXT10 exponents + 7 SI7 + 7 metadata
- Elements: 118 with measured properties, Golay address, missingness mask
- Mathematics: 22 objects (rational matrices, reflections, field elements)
- Lexicon: 10 concepts (index-based, not meaning-based — known limitation)

### Reasoning (Step 3)
- **Griess metric**: exact rational distances on Q²⁴, positive definite
- **Norton-Sakuma 2A algebra**: Sakuma relation, Miyamoto involutions, fusion spectrum
- **Trilinear form ⟨u·v, w⟩**: the fundamental Griess invariant, 18 tests
- **NRCI (5-shell)**: coherence measurement with Y constant
  - Shell 0 (Golay): exact Fraction
  - Shell 1 (Sign-parity): exact Fraction
  - Shell 2 (Sextet-balance): float (sqrt) ⚠️
  - Shell 3 (Coset-type): exact Fraction
  - Shell 4 (Sextet-signed): float (sqrt) ⚠️
- **Analogy solver**: A:B::C→D with subspace restriction, lattice projection
- **Dimension layers**: 5-layer projection (substrate → integer → rational → griess → universal)
- **Equation verifier**: 222 scalar + 71 tensor relations, 31-facet attribution

### Reasoning Abilities (Current)
- Physics: 5,709 Griess product triples with physics third axes
- Physics: exact analogies (velocity:acceleration::momentum→force, exact hit)
- Elements: correct analogies (Li:Na::Be→Mg, He:Ne::Ne→Ar)
- Words: semantic distances (energy↔force = 1/128)
- Cross-domain: nearest element to "mass" = K (potassium)
- NRCI: mass=0.85 (OnBit), torque=0.49 (Transitional)
- Leech lattice: Class A/B/C shape classes correctly separated

### Three Column Thinking (TCT)
Every query is answered three times:
1. **Language**: reasoning chain in plain English
2. **Mathematics**: exact rational statements
3. **Script**: self-contained Python that recomputes and asserts

The TCT harness is in `examples/demo_tct.py`. Seven demo queries covering
distance, analogy, product, coherence, projection, and cross-domain reasoning.

---

## What's To Do

### Near-term
1. **Meaning-based lexicon**: replace index-based word encoding with semantic
   primitives that carry real meaning (abstract/concrete, animate/inanimate,
   temporal stability, causal role). The `examples/encoding_poc.py` shows the
   approach; it needs to be formalized into `data_objects/lexicon.py`.
2. **Element encoding refinement**: the scaled integer encoding works but
   the lattice projection doesn't reach 2A axes for most elements. Need to
   explore encoding strategies that align with the Golay code structure.
3. **Carrier-space product**: the coordinatewise product in
   `examples/scaled_carriers.py` converges to "velocity" for all word pairs.
   Need a better product that preserves semantic structure.
4. **NRCI shell integration**: Shells 2 and 4 use float for sqrt. Document
   this clearly and ensure all tests flag it.

### Medium-term
5. **Niemeier lattices**: the 23 deep-hole types for semantic disambiguation
   (see directive: `ubp_universal_1.txt`).
6. **FWHT for group actions**: Fast Walsh-Hadamard Transform for O(N log N)
   group operations instead of O(N²).
7. **Buckingham Pi via SVD**: Valorani's log-space SVD for automated concept
   discovery.
8. **Moonshine bridge**: V^♮ (the infinite-dimensional Moonshine module) is
   the next layer above the Griess algebra V₂.

### Long-term
9. **Full Griess algebra**: extend from the 2A subalgebra (3-dim) to the
   full 196,884-dimensional V₂.
10. **LLVQ**: Leech Lattice Vector Quantization for O(1) chemistry lookups.
11. **ARC-AGI integration**: apply the reasoning system to ARC-AGI tasks.

---

## Constants

| Symbol | Value | Meaning |
|---|---|---|
| Y | 1/(π + 2/π) ≈ 0.264675 | Read quantum (cost of one read) |
| Q | Y + 1/8 ≈ 0.389675 | Activation quantum (minimum tax) |
| B | 10 | Coherence budget |
| Δ | 2 | Primitive difference |
| Z★ | 1/8 | Zone-share cost |
| SCALE | 8 | Integer model scale (√8 presentation) |

---

## Design Invariants

| Invariant | Enforced by |
|---|---|
| Exact arithmetic only (`int`, `Fraction`) | `class_stack` raises `TypeError` on float |
| No randomness anywhere | AST scan of every module for `random` import |
| Standard library only | AST scan against allow-list |
| Facts computed, not quoted | `*_report` functions recompute on demand |
| Floats only in NRCI shells 2,4 (sqrt) | Documented, test excludes `coherence.py` |

---

## Provenance

Ported and unified from:
- `workflow/GLM/glm_lean/` — GLM-1, GLM-2, GLM-3 (43/58/64 claims)
- `workflow/GLM/glm_machine/` — GLM v37 (crystallization, adversarial, gap words)
- `workflow/GLM/GMHGL/` — UBP substrate engine (Golay, TAX, NRCI)
- `workflow/GLM/data_object/` — encoding experiments, MOG cube, spatial arithmetic
- `light/aristotle_01/` — Y constant, Lean4 verification

---

## Commands

```bash
# Run all tests
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_substrate.py glm_universal/tests/test_data_objects.py glm_universal/tests/test_reasoning.py -q

# Run TCT demo
PYTHONPATH=. python3 glm_universal/examples/demo_tct.py

# Run specific example
PYTHONPATH=. python3 glm_universal/examples/integrated_nrci.py
PYTHONPATH=. python3 glm_universal/examples/scaled_carriers.py
PYTHONPATH=. python3 glm_universal/examples/encoding_poc.py

# Check NRCI on a carrier
PYTHONPATH=. python3 -c "
from glm_universal.reasoning import coherence
print(coherence.nrci_breakdown([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]))
"
```
