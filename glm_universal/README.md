# `glm_universal` — GLM-3+, the Universal MOG-Cube Geometric Language Machine

**Version:** 0.6.0 (21 August 2026)
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
| 1 | `substrate/` — linalg, MOG, Leech, digit stack (multi-MOG-cube) | 96 | ✓ complete |
| 2 | `data_objects/` — physics (720), chemistry (118), math (22), lexicon (95 semantic) | 177+39+9+5 | ✓ complete |
| 3 | `reasoning/` — product, metric, analogy, verifier, coherence, dimension_layers + moonshine, niemeier, llvq, fwht, valorani | 62+18+16+12+31 | ✓ complete |
| 4 | `runtime/` — parser, session, TCT engine, `GLM.py` CLI + 13 query kinds | 181+21+23+23 | ✓ complete |
| 5 | `examples/` — TCT demo, encoding POC, integrated NRCI, scaled carriers | — | ✓ working |

**Total: 610 tests, 5,877 subtests, zero failures.**

**Changelog (v0.4.0 → v0.5.0 → v0.5.1 → v0.5.2 → v0.5.3 → v0.6.0):**
- v0.5.0: Built the missing `GLM.py` CLI. Added `data_objects/semantic_lexicon.py`
  with meaning-based encoding. Physics register 660 → 701.
- v0.5.1: Dataset audit + growth. Fixed 5 physics dimensional bugs. Redesigned
  the semantic lexicon (40 → 95 concepts, zero primitive-vector collisions).
  Physics 701 → 720. Added `lexicon.primitives`/`lexicon.relations` subspaces.
- v0.5.2: Directive alignment. Fixed the Li/Na/Be alias collision regression.
  Fixed `slow`'s `active_stative` primitive. Added 23 substantive tests.
- v0.5.3: Wired four created-but-unused mechanisms: `escalate` (project A B),
  `griess_trilinear` (trilinear A B C), `nrci_breakdown` (coherence <concept>),
  `nearest_lattice_point` (augmented describe). Added 23 wiring tests.
- v0.6.0: Wired remaining lower-priority mechanisms (`report <subject>`,
  `angle A B`). Implemented all five directive-mentioned mechanisms that had
  no code: Moonshine layer, Niemeier lattices, LLVQ, FWHT, Valorani's SVD.
  Added 31 directive tests.

---

## Quick Start

This package is part of the larger GLM repository.  The CLI entry point
(`GLM.py`) lives at the **repo root**, not inside this folder.  Two test
files (`test_runtime.py`, `test_semantic_lexicon_runtime.py`) import it by
path, so running the full test suite from this folder alone will skip
those 30 tests.

To run everything:

```bash
cd /path/to/GLM                          # repo root, where GLM.py lives
PYTHONPATH=. python3 glm_universal/examples/demo_tct.py
PYTHONPATH=. python3 -m pytest glm_universal/tests/ -q
```

To run only the tests that don't need the CLI (substrate, data_objects,
reasoning, semantic_lexicon, physics_expansion, lexicon_subspaces):

```bash
cd /path/to/glm_universal                  # this folder
PYTHONPATH=.. python3 -m pytest tests/ -q \
    --ignore=tests/test_runtime.py \
    --ignore=tests/test_semantic_lexicon_runtime.py
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
│   ├── physics.py             720 physics quantities (EXT10 + SI7)
│   ├── elements.py            118 elements (measured properties + Golay address)
│   ├── mathematics.py         RationalMatrix, Reflection, FieldElement
│   ├── lexicon.py             Vocabulary, Concept (index-based, legacy)
│   ├── semantic_lexicon.py    SemanticConcept, SemanticLexiconCodec (meaning-based, 95 concepts)
│   └── _data/                 frozen exact-rational JSON snapshots
├── reasoning/                 ← Step 3: algebraic and geometric reasoning
│   ├── product.py             Norton-Sakuma 2A algebra, trilinear form ⟨u·v, w⟩
│   ├── metric.py              Griess form on Q²⁴, exact distances, clustering
│   ├── analogy.py             proportional analogy A:B::C→D, lattice projection
│   ├── verifier.py            multi-plane equation audit, facet attribution
│   ├── coherence.py           NRCI (5-shell), Y constant, coherence regimes
│   ├── dimension_layers.py    five-layer dimension projection + escalate()
│   ├── moonshine.py           v0.6.0: graded dimensions V_0..V_10 + j-function
│   ├── niemeier.py            v0.6.0: 23 Niemeier ADE root systems + deep holes
│   ├── llvq.py                v0.6.0: Leech Lattice Vector Quantization (shells)
│   ├── fwht.py                v0.6.0: Fast Walsh-Hadamard Transform (O(N log N))
│   └── valorani.py           v0.6.0: Buckingham-Pi via rational nullspace
├── runtime/                   ← Step 4: query processing and TCT
│   ├── parser.py              natural language query parser (13 query kinds)
│   ├── session.py             Solution, Step, session management (13 solvers)
│   └── tct_engine.py          Three Column Thinking trace generation
├── tests/                     ← test suite
│   ├── test_substrate.py      96 tests
│   ├── test_data_objects.py   177 tests (sizes pinned at 720/118/etc.)
│   ├── test_reasoning.py      94 tests (incl. trilinear form + dimension layers)
│   ├── test_runtime.py         181 tests (was 26 failing pre-v0.5.0)
│   ├── test_semantic_lexicon.py            39 tests (v0.5.0)
│   ├── test_physics_expansion.py           9 tests (v0.5.0)
│   ├── test_physics_expansion_v2.py        5 tests (v0.5.1)
│   ├── test_semantic_lexicon_runtime.py    21 tests (v0.5.0)
│   ├── test_lexicon_subspaces.py           12 tests (v0.5.1)
│   ├── test_substantive.py                 23 tests (v0.5.2)
│   ├── test_wiring.py                     23 tests (v0.5.3 — new query kinds)
│   ├── test_directive.py                  31 tests (v0.6.0 — directive modules)
│   └── __init__.py
└── examples/                  ← demonstrations
    ├── demo_tct.py            Three Column Thinking demo (7 queries)
    ├── encoding_poc.py        element + word encoding proof of concept
    ├── integrated_nrci.py     NRCI + Griess metric integrated test
    └── scaled_carriers.py     scaled carriers + carrier-space product

The CLI entry point at the repo root (`../GLM.py`) is also part of this
package's surface; it is a thin shell over `runtime/`.
```

---

## What's Been Done

### The Substrate (Step 1)
- Golay [24,12,8] code: 4,096 codewords, 759 octads, complete coset table
- Leech lattice Λ₂₄: 196,560 minimal vectors, Λ/2Λ class census (98,280 type-2)
- MOG trio and sextet: 4×6 frame, cube coordinates, facet attribution
- 10-plane digit stack: lossless reconstruction for arbitrary rational carriers

### Data Objects (Step 2)
- Physics: **720 quantities** (was 660 in v0.4.0, 701 in v0.5.0) with 10
  rational EXT10 exponents + 7 SI7 + 7 metadata. The 60 added concepts
  span acoustics, photometry, radiometry, base, geophysics, information,
  statistical mechanics, astronomy, signals and control (v0.5.0), and
  optics, quantum, materials, electrochemistry, plasma, meteorology,
  biophysics (v0.5.1).  All pass `PhysicsCodec.check()` and a dimensional
  audit against their SI unit strings.
- Elements: 118 with measured properties, Golay address, missingness mask
- Mathematics: 22 objects (rational matrices, reflections, field elements)
- Lexicon (legacy `lexicon.py`): 10 interned-index concepts — still
  importable, still tested by `TestLexicon`, but **no longer loaded by
  the runtime**.
- Lexicon (new `semantic_lexicon.py`, v0.5.0 + v0.5.1): **95 meaning-based
  concepts** across 11 topics (physics 12, matter 10, thermal 5, waves 4,
  chemistry 6, math 8, verbs 12, adjectives 12, abstract 8, states 5,
  electromagnetism 5, misc 8).  Each carries 10 semantic primitives
  (abstract/concrete, animate/inanimate, countable/mass, temporal_stable,
  spatial_local, causal_passive, positive_negative, singular/plural,
  active/stative, definite/indefinite) as Fractions with 1/8 gradations,
  plus POS, arity, up to four (predicate, object) relation slots, a
  `has_physical_dim` flag, primitive/relation counts, and a 20-bit
  checksum.  **All 95 primitive vectors are unique** (v0.5.1 audit
  confirmed zero collisions).

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

### Near-term (after v0.6.0 directive mechanisms)
1. ~~**Meaning-based lexicon**~~ — done in v0.5.0
2. **Element encoding refinement**: the scaled integer encoding works but
   the lattice projection doesn't reach 2A axes for most elements.
3. **Carrier-space product**: converges to "velocity" for all word pairs.
4. **NRCI shell integration**: Shells 2 and 4 use float for sqrt.
5. ~~**Grow the semantic lexicon beyond 40 concepts.**~~ — done in v0.5.1
6. ~~**Cross-domain analogies involving the lexicon.**~~ — partly done
7. **Multi-domain analogy mode.** Let `heat : temperature :: force : ?`
   resolve by allowing each operand to come from its own domain.
8. ~~**Wire `escalate()` into the runtime.**~~ — done in v0.5.3
9. ~~**Use the trilinear form `⟨u·v, w⟩` for semantic similarity.**~~ —
   done in v0.5.3
10. ~~**Moonshine layer.**~~ — **done in v0.6.0** (graded dimensions +
    j-function + Leech-to-Moonshine bridge).  The VOA state-field map
    is still future work.
11. **Audit script's unit parser.** Treats `sr` as dimensionless.
12. ~~**Niemeier lattices**~~ — **done in v0.6.0** (catalogue of 23 ADE
    root systems).  Deep-hole finding via the Voronoi cell is future work.
13. ~~**LLVQ**~~ — **done in v0.6.0** (shell classification).  The full
    O(1) lookup table is future work.
14. ~~**FWHT**~~ — **done in v0.6.0** (O(N log N) transform).  Wiring
    into substrate-level group actions is future work.
15. ~~**Valorani's SVD**~~ — **done in v0.6.0** (rational nullspace).
    Wiring as a `pi_groups` query kind is future work.
16. **Words as projections of physics concepts.** The directive says
    "many words may be just projections of existing physics or math
    concepts".  `hot` is not yet encoded as "temperature at high scale"
    -- it is a standalone concept.  Future work: encode words as
    projections, with primitives carrying scale information.
17. **Molecules domain.** No `molecules.py` exists yet, despite the
    root README mentioning "82 molecules" elsewhere in the repo.
18. **Benchmarks suite.** `glm_universal/benchmarks/` is reserved but
    empty.  Wiring the runtime to scored task sets (ARC-AGI, held-out
    query corpus) is the next major step.

### Still-unwired reasoning mechanisms (lower priority)
* `fusion_spectrum`, `miyamoto_tau/sigma`, `adjoint_matrix`,
  `is_automorphism`, `preserves_form`, `apply_map`, `class_translation`
  (Griess algebra introspection — deep algebraic queries that need a
  different surface than the natural-language parser)
* `complete_linkage` as a `linkage=complete` option to the cluster query
* `RefinedNRCI` (configurable multi-shell NRCI with per-shell weights)

### Honest gaps (updated v0.6.0)
* The multi-MOG-cube IS operational (verified on a Leech basis vector).
* The pipeline Golay → Leech → Griess → **Moonshine** is now wired
  (v0.6.0 added the Moonshine layer; the VOA state-field map is still
  future work).
* ~~The dimension-projection layers exist but the runtime never
  escalates.~~ Fixed in v0.5.3.
* ~~The trilinear form exists but is not used for semantic queries.~~
  Fixed in v0.5.3.
* ~~The coherence module exists but is not used by any runtime query.~~
  Fixed in v0.5.3.
* ~~`nearest_lattice_point` exists but is not used by any runtime
  query.~~ Fixed in v0.5.3.
* ~~All five directive-mentioned mechanisms are absent.~~ Fixed in
  v0.6.0: Moonshine, Niemeier, LLVQ, FWHT, Valorani all implemented.
* Many existing tests are structural rather than substantive.  The
  v0.5.2/v0.5.3/v0.6.0 substantive test suites check actual answers.

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
