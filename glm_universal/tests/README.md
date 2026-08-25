# `glm_universal/tests` — the test suite

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

## Structure

**37 test files**, 1,677 collected tests, 8,851 subtests, zero failures. The
per-file counts below are a `pytest --collect-only` run over this directory,
not an estimate; the file list and the totals are recomputed under *The test
suite* in [`../../FIGURES.md`](../../FIGURES.md), and `test_figures.py` fails
if this README drifts from them.

| File | Tests | What it checks | Added in |
|---|---|---|---|
| `test_substrate.py` | 96 | Golay code, Leech lattice, MOG trio/sextet, digit stack (multi-MOG-cube) | v0.4.0 |
| `test_data_objects.py` | 81 | Codec round-trips, carrier invariants, register sizes (726/118/22/95) | v0.4.0 |
| `test_reasoning.py` | 94 | Griess product, trilinear form, metric, analogy, verifier, dimension layers | v0.4.0 |
| `test_runtime.py` | 184 | Parser, session, TCT engine, `GLM.py` CLI, and the `report theta` template — that the solver claims every coefficient `theta_series` returns and that column 3 enumerates rather than hand-lists them, so the last coefficient cannot go unchecked again | v0.4.0 |
| `test_semantic_lexicon.py` | 39 | `SemanticConcept` codec, primitive vectors, antonym distances | v0.5.0 |
| `test_physics_expansion.py` | 9 | The 41 v0.5.0 physics concepts | v0.5.0 |
| `test_physics_expansion_v2.py` | 4 | The 19 v0.5.1 physics concepts | v0.5.1 |
| `test_semantic_lexicon_runtime.py` | 22 | Runtime wiring of the semantic lexicon | v0.5.0 |
| `test_lexicon_subspaces.py` | 8 | The `lexicon.primitives` and `lexicon.relations` subspaces | v0.5.1 |
| `test_substantive.py` | 27 | Actual query answers (`Li:Na::Be:Mg`, `hot:cold::fast:slow`, …) | v0.5.2 |
| `test_wiring.py` | 55 | The `project` / `trilinear` / `coherence` wiring, the cluster linkage option, re-solving an edited query through `session.solve`, the `pi_groups` query kind, and the package surface (`__version__` is `1.3.0`, and all nine subpackages are exported and importable) | v0.5.3, v1.0.0, v1.1.0, v1.2.0, v1.3.0 |
| `test_directive.py` | 31 | The five directive-mentioned modules (Moonshine, Niemeier, LLVQ, FWHT, Valorani) | v0.6.0 |
| `test_information_loss.py` | 53 | Layer resolution and loss counts, the boundaries, the cumulative repair of the refinement chain and the non-cumulative reading kept beside it, congruence witnesses, and the `report information loss` query end to end | v0.7.0 |
| `test_phase1_migration.py` | 44 | The coset table and complete decoding, the `S(5,8,24)` proof that weight-5 miscorrection is a theorem, the `LEGACY_TO_CORE` permutation and its isometry, decoding legacy words through the audited decoder, bulk dataset migration, and the `report golay decoding` / `report migration` queries | v0.8.0 |
| `test_phase2_algebra.py` | 41 | The Construction A/B/C ladder (48 / 98,256 / 196,560), the necessity of each mod condition, the six-facet partition, linearity, orthogonality, Pythagoras and lattice indices, the ten-plane Monster stack, and the non-associativity of the Sakuma product against the associative XOR shortcut | v0.8.0 |
| `test_multires_tasks.py` | 40 | The `F_2^4 <-> GF(4) x Z_4` fibration, column sub-lattices, grid carriers and signatures, cross-level inner and tensor products, the scale-invariance boundary and its census collision, and both worked tasks end to end | v0.8.0 |
| `test_coherence.py` | 58 | The NRCI shells, the coherence regimes and the TAX decomposition | — |
| `test_physics_constants.py` | 12 | `Y`, `Q`, `TAX` and the constants table, as exact rationals | — |
| `test_fusion.py` | 23 | The Ising fusion layer: adjoint action, eigenspaces, the two Miyamoto involutions, and `report fusion` | — |
| `test_state_migration.py` | 47 | The frame audit (the stored data is in the canonical frame; `hexcolour` addresses are MSB-first), the literal migration of 4,680 concepts and 4,014 edges, `verify_canonical` re-deriving every field from the masks, the concept store, and the negative result that graph distance and Hamming distance do not agree | — |
| `test_reasoning_showcase.py` | 14 | The showcase transcript still reproduces | — |
| `test_benchmarks.py` | 67 | The benchmark harness: the tier discipline, exactness, each suite against its baseline, that every suite reports its findings, the written `results/` tree, and the `report benchmarks` query with its column-3 script | v1.0.0 |
| `test_exact_real.py` | 90 | Reals as processes: `x.at(k)` within `2⁻ᵏ` for `sqrt`, `nth_root`, `pi`, `e` and `phi`, each against a relation it must satisfy; exact arithmetic and the absence of any float; the written grammar of `real_expr.py`, including decimal literals read as rationals (`0.1+0.2` is `3/10`) and every refusal it makes; division only with a nonzero witness, and the refusal past `WITNESS_DEPTH`; the dyadic stand-ins and the level that exposes each; decided inequality and refused equality; the `1/N` law of the modulator at three run lengths and its determinism; the 24-D loop on a reachable target (deviation 0) and on the ramp target, with the separating certificate checked against all 4,096 codewords; and the `approximate` and `compare` query kinds and `report infinite values` end to end with column-3 verification | v1.2.0 |
| `test_capabilities.py` | 56 | The probe harness (registration, a probe that raises being reported rather than propagated, the known-area and known-expectation rules, the surprise rule), every one of the 33 probes run for real with its verdict matched against its declared expectation, that no probe errors and every break states where it stops, the counts adding up, every area being probed, the five theorem boundaries checked individually (repair radius 3, equality never claimed, the unreachable target's certificate, non-associativity, the refused 25th coordinate), the work items, the transcendental probe that now holds where it once broke, and the `report capabilities` query with its column-3 script | v1.2.0 |
| `test_transcendental.py` | 83 | `exp`, `log`, `sin`, `cos`, `tan` and the real power `x^y`: the first twenty decimal places of each against its classical expansion; every rational kernel checked to be within its stated `2⁻ᵏ` at four precisions and to return an exact `Fraction`; the identities an implementation could fail while still printing plausible digits (`exp` inverts `log`, `sin² + cos² = 1`, `tan = sin/cos`, `2^(1/3) = root(3, 2)`, `2^0.5 = sqrt(2)`, `log(2, 8) = 3`); the positivity witness — present for a positive value, absent at every depth for one that is zero, and required before a logarithm or a real power — and the refusal naming its depth; and the inverse and hyperbolic family refused by name from the explicit `UNBUILT_FUNCTIONS` list | v1.2.0 |
| `test_superposition.py` | 61 | Ambiguity held as a value: the six-fold tie at every weight-4 coset checked and its sextet partition of the 24 coordinates, the F₂ bundle proved constant (all ones) over 256 superpositions against the rational bundle that is injective and invertible, exactness (`int` and `Fraction` only, no float), contextual collapse in its three outcomes and the refusal to break a tie by member order, the wobble cycle whose time average is the rational bundle, the separating certificate for the unreachable target checked against all 4,096 codewords together with the 16-tick Leech cycle that reaches it, the coset census (`1, 24, 276, 2024, 1771`) and the exact mean coset weight `3433/1024` checked against the Lean figures, the perturbation chain pushed forward exactly (uniform law stationary, parity classes alternating, no limiting law, two-step average within `5819/181398528` of the stationary mean, correction returning the carrier to the code), and the `report superposition` query end to end with column-3 verification | v1.2.0 |
| `test_evaluation.py` | 19 | The end-to-end CLI evaluation: that the 83 cases cover every query kind and every report subject the runtime declares (checked against the runtime's own tables, so neither can be extended without a case), that every case declares a well-formed expectation and every refusal case is classified `boundary` or `gap`, the scoring asymmetry — a synthetic run of one confident wrong answer scores strictly below one of an unexpected refusal — the parsing of `ANSWER` / `UNSOLVED` / refusal markers, the report shape and its per-kind breakdown, and real CLI runs in a fresh interpreter for an answered case, a boundary refusal and the divide-by-an-exact-zero case that used to crash | v1.3.0 |
| `test_semantics.py` | 52 | The meaning space (exactness, the round trip, injectivity, a decoder that notices corruption, refusal of over-capacity and impossible formulae), notation invariance across numeral / word / Roman numeral / arithmetic / formula / register name, refusal with a reason for terms with no determinate referent and for ambiguous ones, every derived relation re-verified, the grounded graph, the audit of the inherited concept graph, the written documents, and the `meaning` query and `report semantics` end to end with column-3 verification | v1.1.0 |
| `test_analogy_models.py` | 53 | Analogy by named relation: each of the four models recognising the pairs it should and declining the ones it should not, the periodic step in derived table coordinates, the reciprocal and scale-shift narrowing filters and the ties they leave, `lexicon_relation` transporting a stated triple in either direction, the refusals that name where they looked, and `report analogies` end to end | v1.3.0 |
| `test_element_coverage.py` | 40 | The sparsity census (1,257 of 1,652 cells), the four derived attributes and their bases, the covalent-radius fit as exact rationals with its residuals, the cross-check that compares without merging and the four elements that disagree, that nothing is written back into the register, and `report chemistry coverage` end to end | v1.3.0 |
| `test_molecules.py` | 39 | The formula grammar (counts, nested brackets, hydrates, charges, refusal by name), the faithful bundle and the round trip back to a formula, the composite carrier and the collision search over all 51 species, missingness propagating from the element register rather than being imputed, and `report molecules` end to end | v1.3.0 |
| `test_units.py` | 24 | Every unit string parsed and checked against its EXT10 exponents, the quantities that disagree, the steradian case priced, and `report units` | v1.3.0 |
| `test_term_arithmetic.py` | 40 | Expressions over register names read into dimensions and back to the quantities carrying them | v1.3.0 |
| `test_fwht_decode.py` | 20 | The 4,096 coset costs as one Walsh–Hadamard transform, the operation counts, the certificate rates by regime, agreement with the syndrome decoder and the tie sets, and `report transform decoder` | v1.3.0 |
| `test_deep_holes.py` | 25 | Walking to a hole, climbing to the covering radius, the derived Niemeier catalogue, the certified reading, and `report deep holes` | v1.3.0 |
| `test_figures.py` | 19 | That `FIGURES.md` matches a fresh computation row by row, that each generated figure agrees with the module that produces it, that the READMEs quote the current counts rather than superseded ones, and that the register sizes quoted in the `runtime.session` and `data_objects.physics` module docstrings are the sizes the live registers have | v1.3.0 |
| `test_inherited_graph.py` | 7 | The recorded decision about the inherited concept graph — kept as evidence, never consulted for an answer — with its grounds recomputed from the audit, and an import walk proving no module on the answering path can reach the stored state | v1.3.0 |

**Total: 1,677 tests across 37 test files, 8,851 subtests, zero failures.**

## Substantive vs structural tests

The test suite has two categories:

1. **Structural tests**: check that codecs round-trip, the parser classifies
   correctly, scripts are float-free, layouts have 24 coordinates, and so on.
   These catch implementation bugs but not semantic ones.

2. **Substantive tests** (`test_substantive.py`, `test_wiring.py`,
   `test_directive.py`, `test_phase1_migration.py`, `test_phase2_algebra.py`,
   `test_multires_tasks.py`, `test_information_loss.py`,
   `test_state_migration.py`, `test_benchmarks.py`, `test_semantics.py`,
   `test_exact_real.py`, `test_transcendental.py`, `test_capabilities.py`,
   `test_analogy_models.py`, `test_molecules.py`,
   `test_element_coverage.py`, `test_evaluation.py`):
   check actual query *answers* — does `Li:Na::Be:?` return `Mg`? Does
   `hot:cold::fast:?` return `slow`? Does `trilinear 127 432 463` give
   `T = -3/32`? Is the kissing number 196,560? Do the two Golay frames share
   exactly 8 codewords? Does `task grid` find `rotate180`? Do all 2,325 error
   patterns inside the packing radius decode correctly? Do `2`, `two`, `II`
   and `1 + 1` reach the same meaning carrier? These catch the kind of
   regression that adding 60 physics concepts can introduce.

`test_benchmarks.py` is the one file that tests a *claim* rather than a
mechanism: it checks that the benchmark suites cannot report a score without
a declared evidence tier, cannot report a float, and cannot report only their
wins.

`test_semantics.py` is the one file that tests a *refusal*: several of its
cases assert that the system declines to answer — an ambiguous notation, a
term with no determinate referent, a formula past the carrier's capacity —
and that it gives the reason. A system that answered those would be measuring
spelling, which is the failure the semantics layer exists to correct.

## The package surface

`test_wiring.py::TestPackageSurface` pins the package's public surface: the
declared `__version__`, and that each of the nine subpackages named in
`glm_universal.__all__` — `substrate`, `data_objects`, `reasoning`,
`semantics`, `runtime`, `migration`, `benchmarks`, `capabilities`,
`evaluation` — imports and reports its own module name. A version bump or a
new subpackage is therefore not complete until this file agrees with
`glm_universal/__init__.py`.

## Running

```bash
cd /path/to/GLM                          # repo root, where GLM.py lives
PYTHONPATH=. python3 -m pytest glm_universal/tests/ -q
```

To run only the tests that don't need the CLI:

```bash
cd /path/to/glm_universal
PYTHONPATH=.. python3 -m pytest tests/ -q \
    --ignore=tests/test_runtime.py \
    --ignore=tests/test_semantic_lexicon_runtime.py
```

The whole suite takes about seven minutes. The slowest fixtures are the
exhaustive 98,280-class type-2 table (about six seconds, cached per process),
the benchmark suites (about eight seconds per full run), the grounded
semantic graph (6,210 binary and 6,649 ternary edges, each re-derived) and the
full capability sweep (33 probes, several of which run a 200- or 400-tick
Golay quantiser loop in exact arithmetic).
