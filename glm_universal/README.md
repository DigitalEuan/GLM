# `glm_universal` — GLM-3+, the Universal MOG-Cube Geometric Language Machine

**Version:** 1.3.0
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand
**Parent:** [`../README.md`](../README.md)

A self-contained, exact, deterministic implementation of the geometric
substrate the Monster group acts on, the reasoning layers built on it,
and the Three Column Thinking harness that runs queries through
language, mathematics, and executable script.

Standard library only. No float on any path that feeds a result. No
randomness anywhere. Every published number is recomputed on demand by
a `*_report` function rather than quoted.

---

## Status

| Step | Package | Tests | Status |
|---|---|---|---|
| 1 | `substrate/` — linalg, MOG, Leech, digit stack, Golay decoding, Leech construction, the legacy↔core isomorphism, superposition | 96 + 44 + 41 + 39 | ✓ complete |
| 2 | `data_objects/` — physics (**726 quantities**), chemistry (118 elements + 52 diatomics), **51 molecules**, mathematics (22), semantic lexicon (95), spatial (28) | 81 + 39 + 39 + 8 + 13 | ✓ complete |
| 3 | `reasoning/` — **27 modules**: product, metric, analogy, analogy_models, periodic_table, verifier, coherence, dimension_layers, information_loss, element_coverage, units, term_arithmetic, facets, monster_stack, multires, tasks, moonshine, niemeier, llvq, fwht, fwht_decode, voronoi_walk, deep_holes, valorani, exact_real, real_expr, transcendental | 94 + 90 + 83 + 58 + 53 + 53 + 40 + 40 + 40 + 31 + 25 + 24 + 23 + 20 + 14 | ✓ complete |
| 3½ | `semantics/` — the meaning space, reference resolution, derived relations, the grounded graph, the audit of the inherited concept graph | 52 | ✓ complete |
| 4 | `runtime/` — parser, session, TCT engine, and the `GLM.py` CLI; **18 query kinds**, **25 report subjects**, 6 registers | 181 + 55 + 27 + 22 | ✓ complete |
| 5 | `migration/` — the literal migration of the repository's stored state into canonical form | 47 | ✓ complete |
| 6 | `benchmarks/` — 5 suites, 2,390 scored tasks, published baselines and findings | 67 | ✓ complete |
| 7 | `capabilities/` — 33 capability probes: what the machine can do, and the exact place each thing it cannot do stops | 56 | ✓ complete |
| 8 | `evaluation/` — **83** end-to-end CLI cases over all 18 query kinds and all 25 report subjects, each in a fresh interpreter, scored with a refusal worth more than a confident wrong answer | 19 | ✓ complete |
| — | `examples/` — TCT demo, reasoning showcase, encoding POC, integrated NRCI, scaled carriers, semantic replacement | — | ✓ working |

**Total: 1,677 tests across 37 test files, 8,851 subtests, zero failures.**

Per-file counts and what each file checks are in
[`tests/README.md`](tests/README.md); every count quoted anywhere in the
documentation is recomputed in [`../FIGURES.md`](../FIGURES.md).

### Sub-package documentation

- [`substrate/README.md`](substrate/README.md)
- [`data_objects/README.md`](data_objects/README.md)
- [`reasoning/README.md`](reasoning/README.md)
- [`semantics/README.md`](semantics/README.md)
- [`runtime/README.md`](runtime/README.md)
- [`migration/README.md`](migration/README.md)
- [`benchmarks/README.md`](benchmarks/README.md)
- [`capabilities/README.md`](capabilities/README.md)
- [`evaluation/README.md`](evaluation/README.md)
- [`tests/README.md`](tests/README.md)
- [`examples/README.md`](examples/README.md)

---

## Changelog

**v0.4.0 → v0.5.x**
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
- v0.5.4: Added the `report <subject>` and `angle A B` query kinds.

**v0.6.0** — Implemented all five directive-mentioned mechanisms that had
no code: the Moonshine layer, the 23 Niemeier lattices, LLVQ, FWHT, and
Valorani's Buckingham-Pi. Added 31 directive tests.

**v0.7.0** — Restored the missing `GLM.py` CLI (it was absent from the
shipped archive, so 30 runtime tests errored on import). Added
`reasoning/information_loss.py`: the layered-projection thesis made
measurable — indistinguishability, resolution, loss count, boundaries,
refinement violations, congruence witnesses, capacity — wired as the
`report information loss` subject with a verifying column-3 template.
Its audit finding was that the substrate → integer step was **not** a
refinement (`refinement_chain_intact = False`).

**v0.8.0** — Three new substrate modules and three new reasoning modules,
with the phase work they support:
- `substrate/golay_decode.py`: the full 4,096-coset table, 12,951 minimum-weight
  leaders, complete decoding that reports `ambiguous` at the six leaders of a
  weight-4 sextet instead of silently choosing, and the `S(5,8,24)` proof that
  weight-5 miscorrection is a theorem about the code rather than a bug.
- `substrate/leech_construct.py`: the Construction A/B/C ladder, 48 → 98,256 →
  196,560, with a necessity report that drops each mod condition in turn.
- `substrate/superposition.py`: the six-fold tie at a deep hole of the Golay
  code, held as one value — bundled over F₂ (constant, hence information-free)
  and over Q (injective and invertible), and collapsed only by a context.
- `substrate/isomorphism.py`: the legacy ↔ canonical frame bridge, an isometry
  that is *not* a Golay automorphism; the two codes share exactly 8 codewords.
- `reasoning/facets.py`, `reasoning/monster_stack.py`, `reasoning/multires.py`:
  the six-facet partition, the ten-plane 2-adic Monster stack, and the
  `F₂⁴ ↔ GF(4) × Z₄` fibration with cross-level products.
- `reasoning/tasks.py` and the `task` query kind: three worked end-to-end tasks.
- New report subjects: `golay decoding`, `leech construction`, `facets`,
  `monster stack`, `multiresolution`, `migration`.

**Between v0.8.0 and v1.0.0** — The cumulative-layer repair, the Ising fusion
layer, and the literal state migration:
- `dimension_layers.LAYER_INTEGER` is now **cumulative**: it carries the SI7
  exponents *and* everything the substrate could already distinguish, so it
  refines the layer below it by construction. `refinement_chain_intact` is now
  `True`. The rejected non-cumulative reading is kept as `LAYER_INTEGER_RAW`,
  outside `LAYERS`, and `non_cumulative_report()` measures exactly what it
  costs — the claim is checked against the alternative, not asserted.
- `report fusion`: the adjoint action of an axis, its eigenspaces at the four
  Ising eigenvalues, and both Miyamoto involutions, all derived.
- `migration/`: the repository's persisted state brought in literally — 4,282
  concepts and 4,014 CRG edges in the canonical frame, 398 carriers minted for
  names the source referred to but never defined, `verify_canonical`
  re-deriving every field from the masks. New subjects `state migration` and
  `concept store`, and the `task concepts` walk.

**v1.0.0** — The last wiring gaps closed:
- `benchmarks/`: the reserved package implemented. Five suites, 2,390 scored
  tasks, every score against a published baseline, and eight findings —
  including the negative ones — reported beside the numbers. Wired as
  `report benchmarks`.
- `runtime.GeometricSession.solve(query, raw=None)`: the public entry point for
  solving an already-parsed query, so a query object can be edited and re-run
  without going back through the surface string. `ask()` now parses and
  delegates to it.
- The `pi_groups` query kind, wiring `valorani.buckingham_pi_groups`: the
  dimensionless groups of a set of quantities, from the exact rational
  nullspace of their EXT10 exponent matrix, each checked dimensionless in all
  ten axes.
- `glm_universal.__version__` is `1.0.0`, and `migration` and `benchmarks` are
  exported from the package root alongside the original four.

**v1.1.0** — `semantics/`: meaning as the thing that gets encoded.
- The inherited ARC-era concept graph was audited rather than described. Of
  its 4,282 concepts, **83** denote anything determinate; of its 4,015 edges,
  **2** state a relation between two determinate referents that can be
  re-derived. Its carriers are `sha256` of a spelling, and the measurement
  says so: related pairs sit at mean Hamming 4547/376 ≈ 12.09 and unrelated
  pairs at 12077/1009 ≈ 11.97, either side of the 12 that two random 24-bit
  words average. Notations for one subject sit 359/30 ≈ 11.97 apart.
- `semantics/meaning.py`: a 24-coordinate carrier of *what a term denotes* —
  an exact rational, an EXT10 dimension, a magnitude, a chemical formula, an
  operation — with an exact round trip and injectivity. `encode` takes a
  meaning and nothing else, so no spelling can reach the carrier.
- `semantics/reference.py`: nine resolvers, notation → meaning or an explicit
  refusal with a reason. 1,705 notations resolve; ambiguous terms are refused
  rather than decided by resolver order.
- `semantics/relations.py`, `graph.py`: 15 binary and 4 ternary relations, each
  with the arithmetic that makes it true; the grounded graph is 357 meanings,
  6,210 binary and 6,649 ternary edges, every one re-derived on demand.
- `semantics/audit.py`, `export.py`: the measurements above, the purge plan
  (2 edges survive, 4,013 are dumped with a stated reason each), and both
  written out as documents beside the inherited state file — which is read
  and never written.
- The `meaning` query kind and the `report semantics` subject, both with
  verifying column-3 templates.
- `glm_universal.__version__` is `1.1.0`, and `semantics` is exported from the
  package root alongside the other six sub-packages.
  `test_wiring.py::TestPackageSurface` pins both, so the declared version and
  the declared surface cannot drift from the code again.
- `RequestProject/GLM/Semantics/`: the Lean proofs — the round trip,
  injectivity, that a spelling-derived encoding cannot be a function of
  meaning, that no proximity radius on the legacy carriers recovers synonymy,
  and that the EXT10 → SI7 step is a boundary in the study's sense.

**v1.2.0** — values that do not fit in a carrier, and the map of where the
machine stops.
- `reasoning/exact_real.py`: a real held as a **process**. `x.at(k)` returns an
  exact `Fraction` within `2⁻ᵏ`, for any `k`; roots of any degree, `pi`, `e`
  and `phi`; the dyadic tower of stand-ins and the level that exposes each;
  decided inequality and refused equality; the delta-sigma modulator, whose
  time average after `N` ticks is within `1/N` of any target — which is how a
  finite carrier that moves reaches every real. No float is constructed
  anywhere in the module.
- The 24-coordinate modulator over the Golay code, and the limit of it: every
  emitted state is a codeword, so the reachable set is the convex hull of the
  code. The all-½ target is held with deviation **0**; the ramp target `i/24`
  is outside the hull, and `hull_certificate` returns a linear functional —
  gap `13/5760`, verified against all 4,096 codewords — that proves no
  quantiser rule converges to it.
- `reasoning/real_expr.py`: written arithmetic over those processes —
  `(1+sqrt(5))/2`, `sqrt(2)+sqrt(3)`, `pi/4`, `root(3, 2)`. Decimal literals
  are read as the rationals they name, so `0.1+0.2` is exactly `3/10`.
  Division refuses a divisor that has not moved away from zero by
  `2⁻⁹⁶`, and names the depth: no algorithm produces that bound for an
  arbitrary process, because it would decide whether the process is zero.
- `reasoning/transcendental.py`: `exp`, `log` (natural, or `log(base, x)`),
  `sin`, `cos`, `tan` and a non-integer exponent `x^y`, each a process with a
  stated error budget, still with no float constructed anywhere. `exp(1)`
  agrees with `e` to `2⁻⁷⁸`, `sin² + cos² = 1`, and `2^(1/3)` is
  `root(3, 2)`. A logarithm needs a **positivity witness** for the reason a
  division needs a nonzero one, and `x^y = exp(y·log x)` inherits it, so
  `2^pi` computes and `0^pi` is refused; the inverse and hyperbolic family is
  refused by an explicit list, so the message names the missing function.
- Two new query kinds: `approximate <expr> to <n> places` and the comparison
  family (`is pi less than 355/113`, `compare sqrt(2) and 1.5`,
  `which is bigger e or pi`), each with a verifying column-3 template.
- `capabilities/`: the eighth sub-package. 33 probes, each phrased as a
  question a user would ask, each answered by running the real code, each
  reporting the exact place the capability stops — **19 hold, 14 break, 0
  errored, 0 surprises**. A break is a located boundary, not a failure; twelve
  of the fourteen are theorems, and the transcendental probe has already moved
  from `breaks` to `holds` now that the functions are built. Wired as
  `report capabilities` and runnable as
  `python3 -m glm_universal.capabilities`.
- `glm_universal.__version__` is `1.2.0`, and `capabilities` is exported from
  the package root alongside the other seven sub-packages, both pinned by
  `test_wiring.py::TestPackageSurface`.
- Five Lean files, `RequestProject/GLM/DeltaSigma.lean`, `Irrational.lean`,
  `Reachable.lean`, `Computable.lean` and `Transcendental.lean` (13 → 18,
  still no `sorry`): the `1/N` law, the cardinality wall and the faithful
  tower, the convex hull with its separating certificate and the exact
  reachability of a periodic carrier, what is and is not computable about an
  approximated value, and the error budget each transcendental function pays
  together with the positivity witness as an equivalence.
- The write-up is `INFINITE_VALUES_STUDY.md` at the repository root.

**v1.3.0** — the machine measured from outside.

- `evaluation/`: the ninth sub-package, and the first instrument that goes
  through `GLM.py` rather than the library. **83 cases**, each starting the CLI
  in a **fresh interpreter** — one subprocess per question, no shared session,
  no warm caches — covering **all 18 query kinds** and **all 25 report
  subjects**, with the coverage checked against the runtime's own tables by a
  test. Scoring is asymmetric: `correct` and `refused_as_expected` are `+1`, an
  `unexpected_refusal` is `0`, and a `wrong_answer` or a crash is `−1`, because
  a refusal tells the user where the machine stops and a confident wrong answer
  does not. 10 of the questions are ones the machine *should* refuse, each
  labelled `boundary` or `gap`. Result: **83 of 83** — 73 correct, 10 refused
  as expected, 0 unexpected refusals, 0 confidently wrong, 0 errored.
  Runnable as `python3 -m glm_universal.evaluation`, exit code 0 only when
  every case passes.  The set opened at 72 cases scoring 67; the five wrong
  answers were all in the `analogy` kind and are what the named relation
  models of `reasoning/analogy_models.py` were built to fix.
- A gap closed with it: `approximate 1/0 to 5 places` escaped as an uncaught
  `ZeroDivisionError` traceback and now refuses, saying a quotient by an exact
  zero names no value — errored cases 1 → 0.
- One gap remains open and is labelled as such: `nearest to PbCl2` refuses
  because `nearest` resolves its operand against the names a register
  enumerates, so an unregistered formula cannot yet be ranked against the
  register.
- `glm_universal.__version__` is `1.3.0`, and `evaluation` is exported from the
  package root alongside the other eight sub-packages, pinned by
  `test_wiring.py::TestPackageSurface`.
- The write-up is `CAPABILITY_ASSESSMENT.md` at the repository root.

---

## Quick Start

The CLI entry point (`GLM.py`) lives at the **repo root**, not inside this
folder. From the directory containing `GLM.py`:

```bash
PYTHONPATH=. python3 GLM.py -q "report benchmarks" -c 1
PYTHONPATH=. python3 GLM.py -q "pi groups force, mass, acceleration, length, time"
PYTHONPATH=. python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 glm_universal/examples/demo_tct.py
PYTHONPATH=. python3 -m glm_universal.benchmarks
```

From Python:

```python
from glm_universal.runtime import GeometricSession

sess = GeometricSession()
print(sess.ask("velocity : acceleration :: momentum : ?").answer)
print(sess.ask("report information loss").answer)
```

---

## Architecture

```
glm_universal/
├── README.md                  ← you are here
├── __init__.py                ← package-level exports, __version__
├── substrate/                 ← Step 1: the algebraic + geometric foundation
│   ├── linalg.py              exact integer / F₂ linear algebra
│   ├── mog.py                 Golay code, hexacode, MOG trio, sextet, cubes
│   ├── leech2.py              Leech lattice, Λ/2Λ, Witt data, 2A axes
│   ├── digit_stack.py         10-plane 2-adic stack, facet attribution
│   ├── golay_decode.py        coset table, complete decoding, honest ambiguity
│   ├── leech_construct.py     the Construction A/B/C ladder to 196,560
│   ├── isomorphism.py         the legacy ↔ canonical frame bridge
│   └── superposition.py       the six-fold tie held as one value, bundled, collapsed
├── data_objects/              ← Step 2: typed carriers over the substrate
│   ├── base.py                DataObject, Codec, StackParameters
│   ├── physics.py             726 physics quantities (EXT10 + SI7)
│   ├── elements.py            118 elements + 52 diatomics, Golay addresses
│   ├── molecules.py           51 molecules and ions: faithful bundle + composite
│   ├── mathematics.py         RationalMatrix, Reflection, FieldElement
│   ├── lexicon.py             Vocabulary, Concept (index-based, legacy)
│   ├── semantic_lexicon.py    95 meaning-based concepts, 10 primitives each
│   └── _data/                 frozen exact-rational JSON snapshots
├── reasoning/                 ← Step 3: algebraic and geometric reasoning
│   ├── product.py             Norton-Sakuma 2A algebra, trilinear form ⟨u·v, w⟩
│   ├── metric.py              Griess form on Q²⁴, exact distances, clustering
│   ├── analogy.py             proportional analogy A:B::C→D, lattice projection
│   ├── verifier.py            multi-plane equation audit, 31-facet attribution
│   ├── coherence.py           NRCI (5-shell), Y constant, regimes, RefinedNRCI
│   ├── dimension_layers.py    five cumulative dimension layers + escalate()
│   ├── information_loss.py    loss at the layer boundaries, measured
│   ├── facets.py              the six-facet partition of the 24 coordinates
│   ├── monster_stack.py       the ten-plane 2-adic Monster stack
│   ├── multires.py            F₂⁴ ↔ GF(4) × Z₄, cross-level products
│   ├── tasks.py               three worked end-to-end tasks
│   ├── moonshine.py           graded dimensions V₀..V₁₀ + j-function
│   ├── niemeier.py            23 Niemeier ADE root systems + deep holes
│   ├── llvq.py                Leech Lattice Vector Quantization (shells)
│   ├── fwht.py                Fast Walsh-Hadamard Transform (O(N log N))
│   ├── valorani.py            Buckingham-Pi via exact rational nullspace
│   ├── exact_real.py          a real as a process; the delta-sigma modulator
│   ├── real_expr.py           written arithmetic over those processes
│   └── transcendental.py      exp, log, sin, cos, tan, and a real power x^y
├── semantics/                 ← Step 3½: meaning as the encoded thing
│   ├── meaning.py             the 24-coordinate meaning carrier, exact
│   ├── reference.py           notation → meaning, or a refusal with a reason
│   ├── relations.py           relations derived from meanings, with witnesses
│   ├── graph.py               the grounded graph, every edge re-derivable
│   ├── audit.py               what the inherited concept graph contains
│   └── export.py              the graph and the purge plan, as documents
├── runtime/                   ← Step 4: query processing and TCT
│   ├── parser.py              natural language query parser (17 kinds)
│   ├── session.py             GeometricSession: ask, solve, registers, history
│   └── tct_engine.py          Three Column Thinking trace generation
├── migration/                 ← Step 5: the stored state, brought in literally
│   ├── frames.py              which frame and bit order the stored data uses
│   ├── state.py               the migration itself, and its verification
│   └── store.py               the consumer: paths, neighbourhoods, cross-links
├── benchmarks/                ← Step 6: scored task suites
│   ├── harness.py             EvidenceTier, Suite, run_suite, benchmark_report
│   ├── suites.py              the five suites
│   ├── __main__.py            CLI
│   └── results/               suite scores and claims, written as data
├── capabilities/              ← Step 7: where the machine stops
│   ├── harness.py             Outcome, Probe, the registry, capability_report
│   ├── probes.py              22 numeric and structural probes
│   ├── probes_language.py     11 probes through grammar, semantics, runtime
│   └── __main__.py            CLI, with --area and --probe
├── evaluation/                ← Step 8: the machine measured from outside
│   ├── cases.py               the 83 CLI cases, every query kind and report subject
│   ├── harness.py             run_case, run_all, evaluation_report, the scoring
│   └── __main__.py            CLI, with --only, --case, --jobs, --json, --list
├── tests/                     ← 1,677 tests across 37 test files
└── examples/                  ← demonstrations
    ├── demo_tct.py            Three Column Thinking demo (7 queries)
    ├── reasoning_showcase.py  29 probes, refusals included; writes the transcript
    ├── encoding_poc.py        element + word encoding proof of concept
    ├── integrated_nrci.py     NRCI + Griess metric integrated test
    ├── scaled_carriers.py     scaled carriers + carrier-space product
    └── semantic_replacement.py  the CRG audit and the graph that replaces it
```

The CLI entry point at the repo root (`../GLM.py`) is also part of this
package's surface; it is a thin shell over `runtime/`.

---

## What the system does

### The substrate (Step 1)
- Golay [24,12,8] code: 4,096 codewords, 759 octads, complete coset table
  (12,951 minimum-weight leaders), decoding that refuses rather than guessing
  when the coset weight exceeds the packing radius
- Leech lattice Λ₂₄: 196,560 minimal vectors built three ways (Construction
  A/B/C) and cross-checked, Λ/2Λ class census (98,280 type-2)
- MOG trio and sextet: 4×6 frame, cube coordinates, facet attribution
- 10-plane digit stack: lossless reconstruction for arbitrary rational carriers

### Data objects (Step 2)
- Physics: **726 quantities** with 10 rational EXT10 exponents + 7 SI7 + 7
  metadata. EXT10 resolves thousands of concept pairs that SI7 conflates —
  torque is `L² M T⁻² A⁻¹`, energy is `L² M T⁻²`.
- Elements: 118 with measured properties, a Golay address whose minimum
  pairwise Hamming separation is exactly 8, and a missingness mask so an
  absent measurement never decodes as a fabricated zero. Plus 52 diatomics.
  The register is sparse — 1,257 of 1,652 cells — and
  `reasoning/element_coverage.py` says so and widens it three ways without
  inventing a measurement (`report chemistry coverage`).
- Molecules: **51 molecules** and ions, held twice — as the faithful bundle of
  element carriers with multiplicities, and as one composite summary carrier,
  with 0 collisions of either kind measured over the register. Nothing is
  stored but a name and a formula; all 19 fields are derived from the element
  register, and a gap there stays a gap here (`report molecules`).
- Mathematics: 22 objects (rational matrices, reflections, field elements)
- Semantic lexicon: **95 meaning-based concepts**, 10 primitives each in 1/8
  gradations, all 95 primitive vectors distinct
- Spatial: 28 MOG structures (trio, sextet, frame rows)

### Reasoning (Step 3)
- **Griess metric**: exact rational distances on Q²⁴, positive definite by
  Sylvester's criterion on all 24 leading minors in integer arithmetic
- **Norton-Sakuma 2A algebra**: closure, commutativity, an explicit
  non-associativity witness, the Ising eigenspaces and both Miyamoto maps —
  all derived rather than tabulated
- **Trilinear form ⟨u·v, w⟩**: the fundamental Griess invariant
- **NRCI (5 shells)**: coherence with the Y constant; shells 2 and 4 use a
  float only for `sqrt`, which is documented and tested for
- **Analogy**: A:B::C→D with subspace restriction and exact, provably optimal
  nearest-point decoding in Λ
- **Dimension layers**: five cumulative layers, substrate → integer → rational
  → griess → universal, with the loss at each boundary measured
- **Equation verifier**: 222 scalar + 71 tensor relations, 31-facet attribution

### Semantics (Step 3½)
A term is admitted only when the registers pin down a determinate referent,
and then it is encoded *as that referent*: `water`, `H2O` and `dihydrogen
monoxide` are one node; `two`, `2`, `4/2` and `1+1` are one number;
`beautiful` is not a node at all, because the repository cannot say what it
would be a node *of*. 1,705 notations collapse onto 357 meanings joined by
12,859 edges, each carrying the arithmetic that re-derives it. See
[`semantics/README.md`](semantics/README.md).

### The runtime (Step 4)
**18 query kinds** and **25 report subjects** over **6 registers** — see
[`runtime/README.md`](runtime/README.md) for all three tables.

Every query is answered three times (Three Column Thinking):
1. **Language**: the reasoning chain in plain English
2. **Mathematics**: exact rational statements
3. **Script**: self-contained Python that recomputes the answer in a fresh
   interpreter and asserts it against column 2

### The migration (Step 5)
The repository's persisted state brought in literally: 4,282 stored concepts
and 4,014 CRG edges in the canonical frame, 398 carriers minted for names the
source referred to but never defined, every field re-derived from the masks by
`verify_canonical`. Nothing is re-generated from a model or invented.

### The benchmarks (Step 6)
Five suites, 2,390 scored tasks, each against a published baseline:

| Suite | Score | Baseline |
|---|---|---|
| `physics_equations` | 29 / 30 | 20 / 30 |
| `golay_correction` | 2,325 / 2,325 | 1 / 2,325 |
| `analogy_chemistry` | 9 / 12 | 3 / 12 |
| `analogy_semantic` | 5 / 10 | 0 / 10 |
| `analogy_physics` | 12 / 13 | 0 / 13 |
| **overall** | **2,380 / 2,390** | |

with eight findings reported beside the scores, including the failures: the
10,626 weight-4 patterns where decoding is ambiguous, the 42,504 weight-5
patterns that miscorrect (a theorem about the code, not a bug), EXT10's refusal
of `angular_momentum = momentum * length`, and reciprocal relations lying
outside the additive analogy model.

---

## What is left

These are mathematical extensions, not wiring gaps: every module in the
package is reachable from the runtime, and every mechanism the directive
names has an implementation.

1. **Deep-hole finding via the Leech Voronoi cell.** `niemeier.py` catalogues
   the 23 lattices and their deep-hole types; computing the holes from the
   Voronoi cell directly is not done.
2. **An O(1) LLVQ lookup table.** `llvq.py` classifies by shell; the full
   codebook-free constant-time table is not built.
3. **FWHT inside the substrate group actions.** `fwht.py` is exact and
   verified (`fwht(fwht(v)) = N·v`) but the substrate still applies group
   elements directly.
4. **The VOA state-field map** `Y(u, z) = Σ uₙ z⁻ⁿ⁻¹`, the
   infinite-dimensional half of the Moonshine bridge.
5. **Multi-domain analogy.** `heat : temperature :: force : ?` still needs all
   four operands in one register.
6. **Words as projections.** `hot` is a standalone concept, not "temperature
   at high scale".
7. **The audit script's unit parser** treats `sr` as dimensionless.
8. ~~**A molecules domain.**~~ **Done.** `data_objects/molecules.py` is the
   sixth register: 51 molecules and ions, a formula grammar that reads
   `Ca(OH)2` and `CuSO4.5H2O`, a faithful bundle beside a composite carrier,
   and every coordinate derived from the element register. What remains is
   narrower and is the evaluation set's one open gap: `nearest to PbCl2`
   refuses, because the `nearest` search resolves its operand against the
   names a register enumerates, so a formula that is not *in* the register
   cannot yet be ranked against it.

Known model boundaries, recorded rather than hidden:
- `D* = C + (B − A)` expresses translations of the exponent vector and nothing
  else, so `time : frequency :: length : ?` answers `L T⁻²` and not `L⁻¹`.
- The coordinatewise carrier-space product converges to "velocity" for all word
  pairs (`examples/scaled_carriers.py`).
- 36 of the 222 scalar relations that a units table gets right are wrong once
  tensor rank and parity are included. That is a result, not a failure.

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

## Design invariants

| Invariant | Enforced by |
|---|---|
| Exact arithmetic only (`int`, `Fraction`) | `class_stack` raises `TypeError` on float |
| No randomness anywhere | AST scan of every module for `random` import |
| Standard library only | AST scan against an allow-list |
| Facts computed, not quoted | `*_report` functions recompute on demand |
| Generated column-3 scripts are float-free | `script_is_exact` scans them by AST |
| Floats only in NRCI shells 2, 4 (sqrt) | Documented, test excludes `coherence.py` |
| A benchmark cannot report a score without a declared evidence tier | `benchmarks/harness.py` |

---

## Provenance

Ported and unified from:
- `workflow/GLM/glm_lean/` — GLM-1, GLM-2, GLM-3 (43/58/64 claims)
- `workflow/GLM/glm_machine/` — GLM v37 (crystallization, adversarial, gap words)
- `workflow/GLM/GMHGL/` — UBP substrate engine (Golay, TAX, NRCI)
- `workflow/GLM/data_object/` — encoding experiments, MOG cube, spatial arithmetic
- `light/aristotle_01/` — Y constant, Lean4 verification

The formal counterpart — the same definitions stated and proved as theorems in
Lean 4 — is in `RequestProject/GLM/` at the repository root, with its own
README. The information-loss write-up is `INFORMATION_LOSS_STUDY.md`.
