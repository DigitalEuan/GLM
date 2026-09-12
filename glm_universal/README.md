# `glm_universal` — GLM-3+, the Universal MOG-Cube Geometric Language Machine


## Tier 0 — the coarse read

**Question.** What is in the package, and what state is each sub-package in?

**Verdict.** No float on any path that feeds a result.

**Deciding figure.** Eleven sub-packages, every published number recomputed on demand by a `*_report` function rather than quoted.

**Recomputed by.** `glm_universal.figures.package_figures`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Version:** 1.17.0
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
| 1 | `substrate/` — linalg, MOG, Leech, digit stack, Golay decoding, Leech construction, the legacy↔core isomorphism, superposition, and the two rungs above 24 dimensions (`lattice32`, `lattice48`) | 298 | ✓ complete |
| 2 | `data_objects/` — physics (**726 quantities**), chemistry (118 elements + 52 diatomics), **51 molecules**, mathematics (22), semantic lexicon (95), spatial (28), **45 comparison classes** | 373 | ✓ complete |
| 3 | `reasoning/` — **65 modules**: admission, analogy, analogy_models, blueprint, catalog, coherence, combiner, companion, conjugate, containers, controller, deep_dive, deep_holes, denotation_view, dimension_layers, directives, drift, economics, element_completion, element_coverage, engine, escalation, exact_real, exactness, facets, fwht, fwht_decode, generative, harmony, higher_lattices, information_loss, lean_address, llvq, llvq_table, mantissa, measure_view, metric, monster_stack, moonshine, multires, name_coordinate, niemeier, noise_lab, periodic_table, pipeline, product, real_expr, retrieval, reversible, salvage, salvage_second, search_loop, shell_sigma, stability, tasks, term_arithmetic, tie_break, transcendental, units, vagueness, valorani, verifier, voronoi_walk, wobble, wobble_landscape | 1,676 | ✓ complete |
| 3½ | `semantics/` — the meaning space, reference resolution, derived relations, the grounded graph, the audit of the inherited concept graph | 59 | ✓ complete |
| 3¾ | `recipe/` — the recipe made into an object: a declarative **domain description**, the 25 shared primitives one is written in, and the single generic path from a description to the carriers, the readings, the widening audit, the query surface and the refusal boundary. Three domains built by hand in earlier rounds are described and regenerated from their descriptions alone | 87 | ✓ complete |
| 3⅞ | `language/` — the question shape made into an object: a declarative **question description** (an opening, named slots, the literal words that separate them, an optional tail, a described preamble and named refusal boundaries) plus a second **infix** form (an operator that cuts a string, for operands that are notations), and the two generic matchers that read them. Three of the runtime's query kinds are read off their descriptions with the hand-written branches deleted, three more are described and measured against the branches they have not yet replaced | 122 | ✓ complete |
| 4 | `runtime/` — parser, session, TCT engine, and the `GLM.py` CLI; **21 query kinds**, **63 report subjects**, 8 registers | 326 | ✓ complete |
| 5 | `migration/` — the literal migration of the repository's stored state into canonical form | 108 | ✓ complete |
| 6 | `benchmarks/` — 5 suites, 2,390 scored tasks, published baselines and findings | 67 | ✓ complete |
| 7 | `capabilities/` — 33 capability probes: what the machine can do, and the exact place each thing it cannot do stops | 56 | ✓ complete |
| 8 | `evaluation/` — **<!--figure:evaluation-case-count-->147<!--/figure-->** end-to-end CLI cases over all 21 query kinds and every report subject, each in a fresh interpreter, scored with a refusal worth more than a confident wrong answer | 20 | ✓ complete |
| 9 | `signoff/` — the sign-off ledger over <!--figure:test-files-->89 test files<!--/figure--> and 7 instruments, with `integrity.py` (the one place a digest is computed) and `tools.py` (the command line for the study instruments) beside it, the generator of the Lean tree's second copy (`mirror.py`, `python3 -m glm_universal.tools lean-mirror`), and the guards on the generated figures and the derived-artefact layer (`figures.py`, `derived.py`) | 144 | ✓ complete |
| 10 | `corpus/` — the documents held the way the substrate holds data: an inventory that classifies every document by rule, the generated `DIGEST.md`, the in-document generated blocks and the inline figures that emit a number inside a sentence, a Leech address for every section of the corpus with a certified-absence shortlist, the measurement cache the address study's tables are emitted from, the cost of one rebuild in exact counts (`cost.py`), the ordered `--refresh` that rebuilds all of it, and the checks that fail when any of it drifts | 55 | ✓ complete |
| — | `examples/` — TCT demo, reasoning showcase, encoding POC, integrated NRCI, scaled carriers, semantic replacement | — | ✓ working |

The **Tests** column is the number of tests in the test files that cover that
package, grouped by hand from the per-file counts. It is a breakdown and not a
partition: `test_figures.py`, the document check, is left out of the total
below so that nothing a document says can move a number a document quotes, and
the test files of the most recent rounds — the sandbox planner and the PCGS
study among them — are counted per file in
[`tests/README.md`](tests/README.md) rather than folded into a row here, so the
column adds to less than the total. The per-file table is the authoritative
one: it is checked against a collection run, and the total below is the
sign-off ledger's own count from the last complete run.

**Total: <!--figure:suite-->3,631 tests across 88 of the 89 test files, 13,777 subtests, outside the document check<!--/figure-->, zero failures.**

Per-file counts and what each file checks are in
[`tests/README.md`](tests/README.md); every count quoted anywhere in the
documentation is recomputed in [`../FIGURES.md`](../FIGURES.md).

### Sub-package documentation

- [`substrate/README.md`](substrate/README.md)
- [`data_objects/README.md`](data_objects/README.md)
- [`reasoning/README.md`](reasoning/README.md)
- [`semantics/README.md`](semantics/README.md)
- [`runtime/README.md`](runtime/README.md)
- [`recipe/README.md`](recipe/README.md)
- [`language/README.md`](language/README.md)
- [`migration/README.md`](migration/README.md)
- [`benchmarks/README.md`](benchmarks/README.md)
- [`capabilities/README.md`](capabilities/README.md)
- [`corpus/README.md`](corpus/README.md)
- [`evaluation/README.md`](evaluation/README.md)
- [`tests/README.md`](tests/README.md)
- [`examples/README.md`](examples/README.md)

---

## Changelog

<!-- figures:history -->

The package's version history — every round from v0.4.0 to the
present, with what it built and what it measured — is in
[`../../archive/PACKAGE_README_ARCHIVE.md`](../../archive/PACKAGE_README_ARCHIVE.md),
under *The `glm_universal` package README's own changelog*. It was
moved there rather than trimmed: a record of a round is not deleted,
it is filed. The change log of the round in progress is kept in
[`../README.md`](../README.md).

<!-- figures:current -->

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
│   ├── llvq_table.py          the MOG class table on the quantiser's hot path
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
├── recipe/                    ← Step 3¾: the recipe made into an object
│   ├── spec.py                a DomainSpec, and the 25 shared primitives
│   ├── build.py               description → carriers, readings, audit, query
│   ├── descriptions.py        three domains, described and nothing else
│   └── report.py              the measured result, and `ask`
├── language/                  ← Step 3⅞: the question shape made an object
│   ├── question.py            a QuestionSpec: preamble, opening, slots, separators
│   ├── infix.py               an InfixSpec: an operator that cuts a string
│   ├── descriptions.py        six question shapes, described and nothing else
│   ├── build.py               the two generic matchers, the corpora, the audits
│   ├── legacy.py              the three deleted parser branches, frozen
│   └── report.py              the measured result, and `ask`
├── runtime/                   ← Step 4: query processing and TCT
│   ├── parser.py              natural language query parser (21 kinds)
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
│   ├── cases.py               the 147 CLI cases, every query kind and report subject
│   ├── harness.py             run_case, run_all, evaluation_report, the scoring
│   └── __main__.py            CLI, with --only, --case, --jobs, --json, --list
├── tests/                     ← <!--figure:test-files-->89 test files<!--/figure-->
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
- Conjugate pairs: **7 energy domains**, each an effort, an extent and the
  transfer their product makes, every row checked against the physics register
  in exact integer arithmetic. It is what carries an analogy across registers:
  `heat : temperature :: force : work` (`report conjugates`).
- The element register's empty cells are **decided** rather than blank: a rule
  is admitted only if its leave-one-out error is at most half the field mean's,
  scored on at least 20 elements; 185 cells are filled by estimate, taking
  coverage to 1,442 of 1,652, and each cell still empty carries one of three
  stated reasons. Nothing is written back (`report completion`).
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
- **The Lean development, addressed**: `lean_address.py` gives every
  declaration of `RequestProject/GLM/` a deterministic 24-coordinate Leech
  address computed from its statement, read back **3187/3187** with 0
  coordinate errors, and `retrieval.py` makes the book an index whose
  completeness bound is proved in `RequestProject/GLM/Retrieval.lean`.
  `report lean`, `report retrieval`

### Semantics (Step 3½)
A term is admitted only when the registers pin down a determinate referent,
and then it is encoded *as that referent*: `water`, `H2O` and `dihydrogen
monoxide` are one node; `two`, `2`, `4/2` and `1+1` are one number;
`beautiful` is not a node at all, because the repository cannot say what it
would be a node *of*. 1,705 notations collapse onto 357 meanings joined by
12,859 edges, each carrying the arithmetic that re-derives it. See
[`semantics/README.md`](semantics/README.md).

### The runtime (Step 4)
**21 query kinds** and **63 report subjects** over **8 registers** — see
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
| `analogy_chemistry` | 12 / 12 | 3 / 12 |
| `analogy_semantic` | 10 / 10 | 0 / 10 |
| `analogy_physics` | 13 / 13 | 0 / 13 |
| **overall** | **2,389 / 2,390** | |

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
2. ~~**An O(1) LLVQ lookup table.**~~ **Done, with the claim narrowed.**
   `llvq_table.py` reads the code off the MOG — 16 pattern entries, 64
   hexacode words, 128 classes of 32 — proves the class minimum and the
   bounded search in `RequestProject/GLM/LLVQTable.lean`, and is what
   `lean_address.quantise` now decodes through: 2,118 corpus addresses
   unchanged, 107 vectors agreeing with the frozen scan point for point.
   What the measurement supports is *constant-bounded*, not constant — 96.8
   codeword costs per call against the scan's 8,192, worst case the whole
   code. `report llvq`; `studies/LLVQ_TABLE_STUDY.md`.
3. **FWHT inside the substrate group actions.** `fwht.py` is exact and
   verified (`fwht(fwht(v)) = N·v`) but the substrate still applies group
   elements directly.
4. **The VOA state-field map** `Y(u, z) = Σ uₙ z⁻ⁿ⁻¹`, the
   infinite-dimensional half of the Moonshine bridge.
5. ~~**Multi-domain analogy.**~~ **Done.** `heat : temperature :: force : ?`
   needed a register the four operands could share, and
   `data_objects/conjugate_pairs.py` is it: 7 energy domains, each row checked
   against the physics register, three relations that transport along it, and
   four stated criteria a transportable relation must meet — so `force`
   reaches `work` and a refusal names the criterion it failed.
   `report conjugates`; `studies/CONJUGATE_STUDY.md`.
6. **Words as projections.** `hot` is a standalone concept, not "temperature
   at high scale".
6b. ~~**Open vocabulary as a bare commitment.**~~ **Closed as far as it can
   be.** `reasoning/admission.py` states what makes a name admissible — a
   stated route giving it coordinates computed from a register the machine
   already checks — and refuses by one route of four. `justice` is still
   refused, but conditionally and with the condition named, which is a
   different claim from the one the silence used to make.
   `report admission`; `studies/ADMISSION_STUDY.md`.
6c. ~~**A vague `related_to` triple needing a person every time.**~~ **Done.**
   `reasoning/vagueness.py` tries four routes in order and only the last asks
   one: 34 of the lexicon's 66 vague triples are decided without a person, and
   a referral carries the evidence collected. `report vagueness`;
   `studies/VAGUENESS_STUDY.md`.
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
README; the overlay keeps a byte-identical copy under `glm_lean/`. The
write-ups are in `studies/` at the repository root, indexed by `ENTRY.md`; the
information-loss one is `studies/INFORMATION_LOSS_STUDY.md`.

This README is one link of a chain that the corpus system holds: it names its
parent (`../README.md`) and every sub-package README below it, each of those
carries a tier-0 block, and all of them appear as rows of the generated
`DIGEST.md`. `python3 -m glm_universal.corpus --check` fails if a link in the
chain points at nothing or if a README cannot be reached from `ENTRY.md`, and
`python3 -m glm_universal.corpus --refresh` rebuilds everything derived — the
two address books, the measurement cache, `DIGEST.md`, the generated blocks and
the inline figures — in the one order that converges. The byte-identical Lean
copy under `glm_lean/` is generated too:
`python3 -m glm_universal.tools lean-mirror --write`.
