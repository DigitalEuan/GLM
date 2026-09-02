# `glm_universal/tests` — the test suite

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

## Structure

**2,872 tests across 61 of the 62 test files, 11,665 subtests, outside the document check**, zero failures at the last complete run. The per-file counts below are a `pytest --collect-only` run over this directory,
not an estimate; the file list and the totals are recomputed under *The test
suite* in [`../../FIGURES.md`](../../FIGURES.md), and `test_figures.py` fails
if this README drifts from them.

| File | Tests | What it checks | Added in |
|---|---|---|---|
| `test_substrate.py` | 96 | Golay code, Leech lattice, MOG trio/sextet, digit stack (multi-MOG-cube) | v0.4.0 |
| `test_data_objects.py` | 81 | Codec round-trips, carrier invariants, register sizes (726/118/22/95) | v0.4.0 |
| `test_reasoning.py` | 94 | Griess product, trilinear form, metric, analogy, verifier, dimension layers | v0.4.0 |
| `test_runtime.py` | 201 | Parser, session, TCT engine, `GLM.py` CLI, the formula fall-through every solver that takes a carrier now has, and the `report theta` template — that the solver claims every coefficient `theta_series` returns and that column 3 enumerates rather than hand-lists them, so the last coefficient cannot go unchecked again | v0.4.0 |
| `test_semantic_lexicon.py` | 39 | `SemanticConcept` codec, primitive vectors, antonym distances | v0.5.0 |
| `test_physics_expansion.py` | 9 | The 41 v0.5.0 physics concepts | v0.5.0 |
| `test_physics_expansion_v2.py` | 4 | The 19 v0.5.1 physics concepts | v0.5.1 |
| `test_semantic_lexicon_runtime.py` | 22 | Runtime wiring of the semantic lexicon | v0.5.0 |
| `test_lexicon_subspaces.py` | 8 | The `lexicon.primitives` and `lexicon.relations` subspaces | v0.5.1 |
| `test_substantive.py` | 27 | Actual query answers (`Li:Na::Be:Mg`, `hot:cold::fast:slow`, …) | v0.5.2 |
| `test_wiring.py` | 55 | The `project` / `trilinear` / `coherence` wiring, the cluster linkage option, re-solving an edited query through `session.solve`, the `pi_groups` query kind, and the package surface (`__version__` is `1.4.0`, and all nine subpackages are exported and importable) | v0.5.3, v1.0.0, v1.1.0, v1.2.0, v1.3.0 |
| `test_directive.py` | 31 | The five directive-mentioned modules (Moonshine, Niemeier, LLVQ, FWHT, Valorani) | v0.6.0 |
| `test_information_loss.py` | 60 | Layer resolution and loss counts, the boundaries, the cumulative repair of the refinement chain and the non-cumulative reading kept beside it, the closed refinement defect and the carrier pair that exposed it, congruence witnesses, and the `report information loss` query end to end | v0.7.0 |
| `test_phase1_migration.py` | 44 | The coset table and complete decoding, the `S(5,8,24)` proof that weight-5 miscorrection is a theorem, the `LEGACY_TO_CORE` permutation and its isometry, decoding legacy words through the audited decoder, bulk dataset migration, and the `report golay decoding` / `report migration` queries | v0.8.0 |
| `test_phase2_algebra.py` | 41 | The Construction A/B/C ladder (48 / 98,256 / 196,560), the necessity of each mod condition, the six-facet partition, linearity, orthogonality, Pythagoras and lattice indices, the ten-plane Monster stack, and the non-associativity of the Sakuma product against the associative XOR shortcut | v0.8.0 |
| `test_multires_tasks.py` | 40 | The `F_2^4 <-> GF(4) x Z_4` fibration, column sub-lattices, grid carriers and signatures, cross-level inner and tensor products, the scale-invariance boundary and its census collision, and both worked tasks end to end | v0.8.0 |
| `test_coherence.py` | 58 | The NRCI shells, the coherence regimes and the TAX decomposition | — |
| `test_physics_constants.py` | 12 | `Y`, `Q`, `TAX` and the constants table, as exact rationals | — |
| `test_fusion.py` | 23 | The Ising fusion layer: adjoint action, eigenspaces, the two Miyamoto involutions, and `report fusion` | — |
| `test_state_migration.py` | 64 | The frame audit (the stored data is in the canonical frame; `hexcolour` addresses are MSB-first), the literal migration of 4,680 concepts and 4,014 edges, `verify_canonical` re-deriving every field from the masks, the concept store, and the negative result that graph distance and Hamming distance do not agree | — |
| `test_reasoning_showcase.py` | 14 | The showcase transcript still reproduces | — |
| `test_benchmarks.py` | 67 | The benchmark harness: the tier discipline, exactness, each suite against its baseline, that every suite reports its findings, the written `results/` tree, and the `report benchmarks` query with its column-3 script | v1.0.0 |
| `test_exact_real.py` | 90 | Reals as processes: `x.at(k)` within `2⁻ᵏ` for `sqrt`, `nth_root`, `pi`, `e` and `phi`, each against a relation it must satisfy; exact arithmetic and the absence of any float; the written grammar of `real_expr.py`, including decimal literals read as rationals (`0.1+0.2` is `3/10`) and every refusal it makes; division only with a nonzero witness, and the refusal past `WITNESS_DEPTH`; the dyadic stand-ins and the level that exposes each; decided inequality and refused equality; the `1/N` law of the modulator at three run lengths and its determinism; the 24-D loop on a reachable target (deviation 0) and on the ramp target, with the separating certificate checked against all 4,096 codewords; and the `approximate` and `compare` query kinds and `report infinite values` end to end with column-3 verification | v1.2.0 |
| `test_capabilities.py` | 56 | The probe harness (registration, a probe that raises being reported rather than propagated, the known-area and known-expectation rules, the surprise rule), every one of the 33 probes run for real with its verdict matched against its declared expectation, that no probe errors and every break states where it stops, the counts adding up, every area being probed, the five theorem boundaries checked individually (repair radius 3, equality never claimed, the unreachable target's certificate, non-associativity, the refused 25th coordinate), the work items, the transcendental probe that now holds where it once broke, and the `report capabilities` query with its column-3 script | v1.2.0 |
| `test_transcendental.py` | 83 | `exp`, `log`, `sin`, `cos`, `tan` and the real power `x^y`: the first twenty decimal places of each against its classical expansion; every rational kernel checked to be within its stated `2⁻ᵏ` at four precisions and to return an exact `Fraction`; the identities an implementation could fail while still printing plausible digits (`exp` inverts `log`, `sin² + cos² = 1`, `tan = sin/cos`, `2^(1/3) = root(3, 2)`, `2^0.5 = sqrt(2)`, `log(2, 8) = 3`); the positivity witness — present for a positive value, absent at every depth for one that is zero, and required before a logarithm or a real power — and the refusal naming its depth; and the inverse and hyperbolic family refused by name from the explicit `UNBUILT_FUNCTIONS` list | v1.2.0 |
| `test_superposition.py` | 61 | Ambiguity held as a value: the six-fold tie at every weight-4 coset checked and its sextet partition of the 24 coordinates, the F₂ bundle proved constant (all ones) over 256 superpositions against the rational bundle that is injective and invertible, exactness (`int` and `Fraction` only, no float), contextual collapse in its three outcomes and the refusal to break a tie by member order, the wobble cycle whose time average is the rational bundle, the separating certificate for the unreachable target checked against all 4,096 codewords together with the 16-tick Leech cycle that reaches it, the coset census (`1, 24, 276, 2024, 1771`) and the exact mean coset weight `3433/1024` checked against the Lean figures, the perturbation chain pushed forward exactly (uniform law stationary, parity classes alternating, no limiting law, two-step average within `5819/181398528` of the stationary mean, correction returning the carrier to the code), and the `report superposition` query end to end with column-3 verification | v1.2.0 |
| `test_evaluation.py` | 20 | The end-to-end CLI evaluation: that the 131 cases cover every query kind and every report subject the runtime declares (checked against the runtime's own tables, so neither can be extended without a case), that every case declares a well-formed expectation and every refusal case is classified `boundary` or `gap`, the scoring asymmetry — a synthetic run of one confident wrong answer scores strictly below one of an unexpected refusal — the parsing of `ANSWER` / `UNSOLVED` / refusal markers, the report shape and its per-kind breakdown, and real CLI runs in a fresh interpreter for an answered case, a boundary refusal and the divide-by-an-exact-zero case that used to crash | v1.3.0 |
| `test_semantics.py` | 52 | The meaning space (exactness, the round trip, injectivity, a decoder that notices corruption, refusal of over-capacity and impossible formulae), notation invariance across numeral / word / Roman numeral / arithmetic / formula / register name, refusal with a reason for terms with no determinate referent and for ambiguous ones, every derived relation re-verified, the grounded graph, the audit of the inherited concept graph, the written documents, and the `meaning` query and `report semantics` end to end with column-3 verification | v1.1.0 |
| `test_analogy_models.py` | 53 | Analogy by named relation: each of the four models recognising the pairs it should and declining the ones it should not, the periodic step in derived table coordinates, the reciprocal and scale-shift narrowing filters and the ties they leave, `lexicon_relation` transporting a stated triple in either direction, the refusals that name where they looked, and `report analogies` end to end | v1.3.0 |
| `test_element_coverage.py` | 40 | The sparsity census (1,257 of 1,652 cells), the four derived attributes and their bases, the covalent-radius fit as exact rationals with its residuals, the cross-check that compares without merging and the four elements that disagree, that nothing is written back into the register, and `report chemistry coverage` end to end | v1.3.0 |
| `test_molecules.py` | 44 | The formula grammar (counts, nested brackets, hydrates, charges, refusal by name), the faithful bundle and the round trip back to a formula, the composite carrier and the collision search over all 51 species, missingness propagating from the element register rather than being imputed, and `report molecules` end to end | v1.3.0 |
| `test_units.py` | 24 | Every unit string parsed and checked against its EXT10 exponents, the quantities that disagree, the steradian case priced, and `report units` | v1.3.0 |
| `test_term_arithmetic.py` | 40 | Expressions over register names read into dimensions and back to the quantities carrying them | v1.3.0 |
| `test_fwht_decode.py` | 20 | The 4,096 coset costs as one Walsh–Hadamard transform, the operation counts, the certificate rates by regime, agreement with the syndrome decoder and the tie sets, and `report transform decoder` | v1.3.0 |
| `test_deep_holes.py` | 25 | Walking to a hole, climbing to the covering radius, the derived Niemeier catalogue, the certified reading, and `report deep holes` | v1.3.0 |
| `test_llvq_table.py` | 21 | The MOG class table: the three conditions on all 4,096 codewords, the 128 classes of 32, the 16-entry pattern bijection, the class minimum and its parity repair, the bounded search against the scan, the search cost and the whole Lean address corpus decoded both ways | v5.18.0 |
| `test_figures.py` | 25 | That `FIGURES.md` matches a fresh computation row by row, that each generated figure agrees with the module that produces it, that the READMEs quote the current counts rather than superseded ones, and that the register sizes quoted in the `runtime.session` and `data_objects.physics` module docstrings are the sizes the live registers have | v1.3.0 |
| `test_inherited_graph.py` | 7 | The recorded decision about the inherited concept graph — kept as evidence, never consulted for an answer — with its grounds recomputed from the audit, and an import walk proving no module on the answering path can reach the stored state | v1.3.0 |
| `test_blueprint.py` | 77 | The unification blueprint as a live claim ledger: the shape of a claim entry and its four verdicts, the source audit that settles Part I, the delta-sigma rate, the engine's seven stages and its measured precision figure, the Gray-code read channel and the halving that is *not* exact, the Toffoli and Fredkin gates and the kink invariant, the exact binary64 model (no float is ever constructed) and its bit spectrum, and `report blueprint`, `report engine`, `report mantissa` and `report reversible` end to end with column-3 verification | v1.3.0 |
| `test_noise_lab.py` | 50 | Noise as the computation: a signal-driven modulator tracking a two-tone input's running mean inside the `1/N` law, the closed orbit of a periodic input, the MASH 1-1 cascade against a single loop with the measured ratio `M − 1` on the triangular window and both Lean bounds checked numerically, the exact Walsh spectrum of an interacting pair and the tone strengths it reads, the subtractive-dither sweep and its monotone peak reduction with the bias it costs, exactness (`Fraction` only, no float, no `random`), the vector error-feedback loop (the `1/(2N)` law at the identity matrix, the dead zone at `A = 1/2`, equivariance under a permutation the matrix respects and its failure under one it does not), and `report noise` end to end with column-3 verification | v1.3.0 |
| `test_wobble.py` | 33 | The spectral signature of a constant: the ones count, run lengths, transition rate and entropy of the modulator's stream, each printed beside the closed form `RequestProject/GLM/Sturmian.lean` proves it takes, and `report signature` | v1.3.0 |
| `test_drift.py` | 26 | One recurrence over the odd primes in three arithmetic regimes — exact, an exact binary64 model, and binary64 truncated to a display precision — with the drift measured in exact arithmetic and no float constructed, and `report drift` | v1.3.0 |
| `test_catalog.py` | 31 | `glm_study_findings_catalog.md` as a live claim ledger: the code-to-lattice ladder and the generator step costs it leans on, that every claim is settled by a computation and carries one of the four verdicts, that a disagreement says what holds instead, and `report catalog` end to end | v1.3.0 |
| `test_containers.py` | 52 | The three containers of a constant: exact generators and the integer comparison that decides precision, the stream statistics against their closed forms, the certified period (decided from the target's denominator, so the 169-place near-repeat of `sqrt(2)`'s stream is not mistaken for one), and the hull census with both verdicts checked against all 196,560 minimal vectors | v1.4.0 |
| `test_companion.py` | 27 | The two companion preprints as a live claim ledger: the transcribed tables, that both studies are covered and every claim settled by a computation, that the hull verdicts are the census's rather than the ledger's, and `report companion` end to end | v1.4.0 |
| `test_lattice_high.py` | 30 | The two rungs above the Leech lattice: the nested Reed–Muller pair and the three-case minimum certificate that makes the 32-dimensional Construction D lattice extremal, its unimodularity and its 146,880 minimal vectors counted by shape; the binary route in 48 dimensions stopping at minimum 2 and the ternary Pless code `C(23)` reaching 6, with the weight enumerator summing to `3^24`; the numerical inputs the `HigherLattices.lean` theorems assume, checked to hold; the exhaustive searches opt-in | v1.5.0 |
| `test_shell_sigma.py` | 26 | Delta-sigma with a Leech shell as its alphabet: the matched rule against a covering alphabet at `rho/N`, the separating rule against a finite non-covering one at `B/N` given a hull margin, the closed-form support function agreed against a full sweep of all 196,560 shell vectors, the Gibbs weights and their deterministic realisation with no randomness, each recurrence run in exact `Fraction` arithmetic and matched to its `ShellSigma.lean` bound | v1.5.0 |
| `test_lean_address.py` | 54 | A deterministic Leech address for every declaration of the Lean development: the parser (block comments excluded, attributed declarations included, no duplicates), the 24-coordinate feature map and its determinism, the scale sweep, exact read-back for all 1072 declarations with the worst residual inside the covering radius, the injectivity census and the classes the feature map conflates, and the three-scheme separation measurement — structural against a digest control and a shuffled null — together with the audit that every `GLM.…` Lean name cited in the package resolves and the check that the documents state the corpus size the parser finds | v1.5.0 |
| `test_signoff.py` | 61 | The sign-off ledger: that a unit's closure contains its test file, everything it imports through the package, the data files those modules read, **the documents and Lean sources those modules name**, and the shared scaffolding; that the digest moves when any of that changes in content *or* name and not otherwise; that a signature is valid only for the digest and interpreter it was taken at; and that only a pass signs, a failure leaving the unit stale. The document rule is checked in both directions — editing `STATUS.md` makes `test_figures.py` stale and leaves `test_substrate.py` signed — and the seven non-pytest instruments are checked too: each has a command, a directory and a closure, the command is part of the digest, a Lean instrument depends on every `.lean` file, and the evaluation depends on the `GLM.py` it drives. Nothing here runs the suite — every case inspects a plan or a ledger in a temporary path | v1.6.0 |
| `test_pipeline.py` | 31 | The pipeline board, which cannot flatter: only the registry is declared and every stage is read off the tree at call time, so each stage is decided by evidence the test can also see; a missing document, a stub document, an unwired subject and a missing template each block their stage; the coverage index is computed with `ast`, so asking the board what is tested never imports a test; and the board's own row is in the registry | v1.5.0 |
| `test_harmonics.py` | 99 | The harmonic register and the harmony study: 28 intervals in lowest terms with every one of the 24 coordinates recomputed from the ratio and the codec's round trip exact even after a derived coordinate is corrupted; the nearest equal step decided by integer comparison and the tempering error exact — `1` at the unison and the octave and nowhere else, `531441/524288` at the fifth; no stack of fifths a stack of octaves to `n = 200`; Kendall's tau exact between Tenney height and Euler's gradus; and the catalogue's universality claim tested rather than asserted — the tuning vector deliberately not the carrier, the undecoded control it has to beat, the confirming branch of the verdict shown reachable, and the finding recorded rather than hidden | v1.7.0 |
| `test_escalation.py` | 34 | The layer audit at register scale: that the carrier set really is one per named object of every register with nothing sampled; that each layer's class key agrees with the layer's own `perceive` and `measure` on every pair of a fixed sample, with a deliberately broken key checked to fail the same test; the measured resolutions, boundary gains and zero refinement violations; the resolution ceiling and its within-register collision classes, attributed per register; where addition descends and the witness where it does not; the rejected SI7-only reading at scale; and the `report escalation` query end to end with its column-3 script | v1.7.0 |
| `test_name_coordinate.py` | 30 | A coordinate for the name, and what it buys: that the code is exact integer arithmetic on the entry's own name with the length bands checked to be disjoint and injectivity re-measured on the corpus rather than assumed; that the exact code lifts the ceiling from every layer including the 24-bit substrate (415 → 1,040), which the tests treat as an instrument check because `namedResolution_of_injective` forces it; the bit sweep as the actual measurement — 16 bits sufficient for the mixing reduction, no width sufficient for the tail-of-the-name one, the non-monotone row at 14 bits, and the seven-bit pigeonhole floor under both; the four control coordinates, with the register label recovering none of the 283 and the first letter and length recovering part; the admission rule enforced on all 25 rows by re-evaluating each coordinate in the opposite order, with a traversal-reading coordinate checked to fail it; and `report names` end to end with its column-3 script | v1.8.0 |
| `test_comparison_classes.py` | 40 | The comparison-class register: 45 classes over 11 quantities and 11 scales, the codec round trip, the degree-word lexicon and its agreement with the semantic lexicon (the shared words, the neutral one, and the pole pairs), and `register_summary` | v1.7.0 |
| `test_measure_words.py` | 51 | Measure words as relative measures: which adjectives carry a scale and which do not, reading a word against a comparison class as an exact rational, classifying a magnitude back to a word, comparison across classes, the measure layer refining the static one with no violation and the reading-only layer that does violate it, the widening audit, relation repair, and the `measure` query and `report measure` end to end with column-3 verification | v1.7.0 |
| `test_project_directives.py` | 20 | `PROJECT_DIRECTIVES.md` and its reader: that a table row with no section, a section with no row, or an instrument that does not resolve is reported as a defect; that the document as it stands has none, every instrument resolving and every rule explained rather than asserted; and the rules checkable here checked — the core computes no digests, the reasoning package constructs no floats, and every study document the pipeline registry names exists | v1.5.0 |
| `test_derived.py` | 32 | The derived-artefact layer: every memoised derivation checked against the uncached function that builds it, so a memo can never change an answer; the derived store answering only against a digest, with fresh, stale and absent distinguished and a stale artefact never handed back; and the `exhaustive` marker deselected by default and selected by `--exhaustive`, `GLM_EXHAUSTIVE=1` or the sign-off runner, checked by running pytest twice over a temporary test file | — |
| `test_comparative.py` | 69 | The comparative — *hotter than*, *as hot as* — over measure-word uses: that a comparison is refused unless both uses read as an exact rational of the *same* quantity, so a temperature and a velocity are declined by name; that the answer is the order on those rationals and not the order on the words, with `cold` for a stellar surface (8000 K) hotter than `hot` for a cup of tea (363 K); the audit over all 228 comparable pairs of the 56 measured uses, with 0 of the 24 same-class pairs and 151 of the 204 cross-class pairs disagreeing with word order; the comparative stems the register does and does not supply (`hotter → hot`, `bigger` refused), the direction each degree word points and the refusal at the exact midpoint; and the `comparative` query kind end to end with column-3 verification | v1.9.0 |
| `test_denotation.py` | 26 | What the undimensioned names denote: the register's form — every verdict one of the six, a `quantity` verdict naming an entry the physics register holds and supplying no coordinate of its own, an `ambiguous` one listing at least two candidates the register holds, no entry shadowing a registered quantity or an alias, none unjustified and none duplicated; that the decided names are exactly the residue's undimensioned endpoints, with nothing undecided and nothing idle; the second pass measured — 0 conversions, the 6 `names_process_of` repairs and the 33 declines by kind, with a `carrier` beside a quantity deliberately left unrepaired; the closure claim that no triple waits on a lookup; and `report denotations` end to end with column-3 verification | v1.10.0 |
| `test_economics.py` | 28 | The economic register — the third of the universality claim: the magnitude bucket computed by integer comparison alone and satisfying its defining inequality on prices no float represents (machine-checked in `LogBucket.lean`), the 21 quoted prices counted rather than quoted with their codec round trip, the price vectors and the scale sweep that separates every record at scale 1024, the verdict recorded as *not reproduced* because the undecoded control does exactly as well, and `report economics` solving with a float-free column-3 script that reproduces column 2 in a fresh interpreter | v1.8.0 |
| `test_recipe.py` | 87 | The recipe made into an object: that each of the three descriptions lays out a full 24-coordinate carrier with every coordinate saying what it derives from, that a coordinate described twice, a key that is not a coordinate, a reading of an underived coordinate and a refusal the description derives are each refused; the 25 shared primitives one at a time, their composition and the absence of any float; the register, the read-back and the labels generated from the description alone; the chain a refinement chain with what each widening gains checked to be exactly the pairs it splits (the comparison chain gains three, the other two none); the refusal boundary — every named refusal refused and every described coordinate answered; the query surface reaching all three domains with a judgement reported as one; regeneration — 94 of 94 carriers identical to the shipped registers, every object equal and every measured figure unchanged, the two slow ones included under `exhaustive`; and the `derive` query kind end to end through the parser, the session and the CLI, with `report recipe` verified in a fresh interpreter | v1.11.0 |
| `test_language.py` | 90 | The question shape made an object, and the parser branches it replaced: that each description opens with a phrasing, names its slots once, marks every optional slot at the tail and justifies every set of alternatives it treats as one; the generic matcher — the earliest separator taken, an optional tail left empty rather than swallowing the object; the refusal boundary, with every named boundary given a witness that reaches it and no boundary named that cannot be reached; the round trip; the described **preamble**, its order, its repeatable courtesy loop, and that skipping it leaves the match unchanged while an undescribed leading remainder is still declined; the **narrowing**, 15 witnesses declined here and misread by the branches; that the branches really are **gone** from `runtime/parser.py` and that nothing under `runtime/` imports the frozen copy; agreement with those frozen branches over a corpus of 846 questions generated from the registers — same kind and same options, 0 disagreements — and the false-positive half, all 114 evaluation questions of the other kinds declined; the **infix family**, its operator meanings, its inner operator, its described-but-not-carried operand, its refusals and its 174-question agreement with the parser it has not yet replaced; that the openings of different shapes are pairwise non-prefix; and `report language` end to end through the session, the CLI and column-3 verification | v1.13.0 |


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
   `test_element_coverage.py`, `test_evaluation.py`, `test_catalog.py`,
   `test_containers.py`, `test_companion.py`, `test_harmonics.py`):
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
declared `__version__`, and that each of the eleven subpackages named in
`glm_universal.__all__` — `substrate`, `data_objects`, `reasoning`,
`semantics`, `runtime`, `migration`, `benchmarks`, `capabilities`,
`evaluation`, `recipe`, `language` — imports and reports its own module name.
A version bump or a new subpackage is therefore not complete until this file
agrees with `glm_universal/__init__.py`.

## The suite totals used to be a fixed point

The headline row — how many test files, how many tests, how many subtests —
is measured by running the suite, and the suite contains `test_figures.py`,
which checks the documents that quote that row. While the row counted that
file, the figure counted a test file whose own size depended on what the
documents said, so two different things got called drift and only one of them
was cheap:

| | what changed | what it used to cost |
|---|---|---|
| **digit drift** | a documented figure changes value | one complete run: rewriting digits inside sentences that already exist does not change how many checks the document check performs, so the totals do not move again |
| **shape drift** | the *set* of documented sentences changes — a document added, a quoted phrase appearing or disappearing, a skipped test now running | two complete runs: the change moved `test_figures.py`'s own subtest count, which moved the totals, which are themselves quoted |

Neither case was unsound — the second run was what made the quoted number
true — but the second run was avoidable, and the first of the three remedies
named in the module docstring of `glm_universal/figures.py` is now **taken**:
the totals are measured over the suite *minus* the document-checking file.
`signoff.ledger.DOCUMENT_CHECKS` names the excluded files — `test_figures.py`,
and nothing else — `counted_units()` is the suite the totals are summed over,
and the recorded row carries the exclusion as an `"excludes"` key so a reader
can see what was left out rather than infer it. The sentence the documents
quote ends *", outside the document check"* for the same reason.

The loop is now closed by construction: nothing the documents say can move the
number the documents quote, so shape drift costs one complete run exactly as
digit drift does, and a release run reaches the fixed point in one pass.
`test_figures.py::test_the_totals_leave_this_file_out_of_the_count` is what
keeps that true — it fails if the exclusion is dropped or if the recorded row
stops declaring it. The two remedies not taken — quoting only the stable half
of the row, or summing the ledger's stored per-file counts — are still
described in `figures.py` as the alternatives they were.

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

The whole suite takes about fifteen minutes. The slowest fixtures are the
exhaustive 98,280-class type-2 table (about six seconds, cached per process),
the benchmark suites (about eight seconds per full run), the grounded
semantic graph (6,210 binary and 6,649 ternary edges, each re-derived) and the
full capability sweep (33 probes, several of which run a 200- or 400-tick
Golay quantiser loop in exact arithmetic), and the two study ledgers
(`test_containers.py` and `test_companion.py`, which chase eight constants
for ten thousand exact ticks apiece and take the support function of the
projection direction over all 196,560 minimal vectors).
