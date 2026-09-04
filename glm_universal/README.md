# `glm_universal` — GLM-3+, the Universal MOG-Cube Geometric Language Machine

**Version:** 1.15.0
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
| 1 | `substrate/` — linalg, MOG, Leech, digit stack, Golay decoding, Leech construction, the legacy↔core isomorphism, superposition, and the two rungs above 24 dimensions (`lattice32`, `lattice48`) | 272 | ✓ complete |
| 2 | `data_objects/` — physics (**726 quantities**), chemistry (118 elements + 52 diatomics), **51 molecules**, mathematics (22), semantic lexicon (95), spatial (28), **45 comparison classes** | 237 | ✓ complete |
| 3 | `reasoning/` — **49 modules**: product, metric, analogy, analogy_models, periodic_table, verifier, coherence, dimension_layers, information_loss, element_coverage, units, term_arithmetic, facets, monster_stack, multires, tasks, moonshine, niemeier, llvq, llvq_table, fwht, fwht_decode, voronoi_walk, deep_holes, valorani, exact_real, real_expr, transcendental, blueprint, engine, mantissa, reversible, noise_lab, wobble, drift, catalog, containers, companion, higher_lattices, shell_sigma, harmony, lean_address, directives, pipeline, measure_view, denotation_view, economics, escalation, name_coordinate | 1,474 | ✓ complete |
| 3½ | `semantics/` — the meaning space, reference resolution, derived relations, the grounded graph, the audit of the inherited concept graph | 59 | ✓ complete |
| 3¾ | `recipe/` — the recipe made into an object: a declarative **domain description**, the 25 shared primitives one is written in, and the single generic path from a description to the carriers, the readings, the widening audit, the query surface and the refusal boundary. Three domains built by hand in earlier rounds are described and regenerated from their descriptions alone | 87 | ✓ complete |
| 3⅞ | `language/` — the question shape made into an object: a declarative **question description** (an opening, named slots, the literal words that separate them, an optional tail, a described preamble and named refusal boundaries) plus a second **infix** form (an operator that cuts a string, for operands that are notations), and the two generic matchers that read them. Three of the runtime's query kinds are read off their descriptions with the hand-written branches deleted, three more are described and measured against the branches they have not yet replaced | 90 | ✓ complete |
| 4 | `runtime/` — parser, session, TCT engine, and the `GLM.py` CLI; **21 query kinds**, **51 report subjects**, 8 registers | 320 | ✓ complete |
| 5 | `migration/` — the literal migration of the repository's stored state into canonical form | 64 | ✓ complete |
| 6 | `benchmarks/` — 5 suites, 2,390 scored tasks, published baselines and findings | 67 | ✓ complete |
| 7 | `capabilities/` — 33 capability probes: what the machine can do, and the exact place each thing it cannot do stops | 56 | ✓ complete |
| 8 | `evaluation/` — **134** end-to-end CLI cases over all 21 query kinds and all 51 report subjects, each in a fresh interpreter, scored with a refusal worth more than a confident wrong answer | 20 | ✓ complete |
| 9 | `signoff/` — the sign-off ledger over 74 test files and 7 instruments, with `integrity.py` (the one place a digest is computed) and `tools.py` (the command line for the study instruments) beside it, and the guards on the generated figures and the derived-artefact layer (`figures.py`, `derived.py`) | 118 | ✓ complete |
| — | `examples/` — TCT demo, reasoning showcase, encoding POC, integrated NRCI, scaled carriers, semantic replacement | — | ✓ working |

The **Tests** column is the number of tests in the test files that cover
that package; the eleven rows partition the 74 test files, so the column adds
to the total below.

**Total: 3,163 tests across 73 of the 74 test files, 12,838 subtests, outside the document check, zero failures.**

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
- [`evaluation/README.md`](evaluation/README.md)
- [`tests/README.md`](tests/README.md)
- [`examples/README.md`](examples/README.md)

---

## Changelog

<!-- figures:history -->

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
  through `GLM.py` rather than the library. **92 cases**, each starting the CLI
  in a **fresh interpreter** — one subprocess per question, no shared session,
  no warm caches — covering **all 18 query kinds** and **all 25 report
  subjects**, with the coverage checked against the runtime's own tables by a
  test. Scoring is asymmetric: `correct` and `refused_as_expected` are `+1`, an
  `unexpected_refusal` is `0`, and a `wrong_answer` or a crash is `−1`, because
  a refusal tells the user where the machine stops and a confident wrong answer
  does not. 10 of the questions are ones the machine *should* refuse, each
  labelled `boundary` or `gap`. Result: **89 of 89** — 79 correct, 10 refused
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

**v1.4.0** — the two companion preprints, and the last evaluation gap closed.

- `reasoning/containers.py` and `report containers`: the instrument behind the
  first companion study. Eight constants are profiled through three
  containers — the exact generator, with the steps it needs to reach 10, 30
  and 50 bits decided by integer comparison against a 200-bit reference (no
  logarithm, no float); the delta-sigma stream, with the closed form beside
  every measured column; and the projection `v_i = 4c/(i+1)` tested against
  the convex hull of the Leech minimal vectors. Both hull verdicts are
  certificates over all **196,560** vectors rather than a sample — a sample
  can establish *inside* and can never establish *outside* — so 7 of the 8
  rows are settled and the eighth is reported `undetermined`.
- `reasoning/companion.py` and `report companion`: both preprints as a live
  claim ledger. **49 testable sentences: 26 confirmed, 17 refuted, 5 not
  reproduced, 1 not implemented.** It is finer than `report catalog` because
  the preprints state the definitions their summary omits — the projection,
  the indexing, the alphabet — so several verdicts that the catalogue had to
  leave open are settled here.
- The stream period is now **decided** rather than searched for. The least
  period of the modulator's stream is the denominator of the target in lowest
  terms, so that is what is checked; a windowed search reports the
  denominator of a continued-fraction convergent instead, which is why
  `sqrt(2)` appeared to have period 169 over 400 places and disagrees with
  its own 169-shift at place 407. `near_period_coincidence` records the gap.
- **The evaluation's last gap is closed.** Every solver that takes a carrier
  and nothing else now hands an operand no register enumerates to the molecule
  formula parser before refusing, so `coherence PbCl2`, `spatial PbCl2`,
  `angle PbCl2 water` and `cluster PbCl2, water, ammonia` are answered from a
  carrier whose every coordinate is derived from the element register.
  Nothing is guessed: an unparseable formula still refuses. The set is
  **97 of 97**, with 9 boundary refusals and **no `gap` case**.
- `glm_universal.__version__` is `1.4.0`, pinned by
  `test_wiring.py::TestPackageSurface`.
- The write-up is `GLM_COMPANION_STUDIES_AUDIT.md` at the repository root.

---

**v1.5.0** — above 24 dimensions, the Lean development addressed, and the
standing rules made into instruments.

- `substrate/lattice32.py`, `substrate/lattice48.py` and
  `reasoning/higher_lattices.py`, wired as `report lattices`: the two rungs
  above the Leech lattice. The 32-dimensional Barnes–Wall lattice is built by
  Construction D over `RM(1,5) ⊂ RM(3,5)`, and its three levels are genuinely
  nested lattices of index `2^26` and `2^6` — so a 32-dimensional address has
  **three usable resolutions** where a Leech address has one. The
  48-dimensional rung reaches centre density exactly `(3/2)^24`, about
  **16,834 times** the Leech lattice's, and needs an `F_3` code and a
  neighbour step: no Golay code, no MOG, no octads.
- `reasoning/shell_sigma.py`, wired as `report shells`: the delta–sigma loop
  with its alphabet widened to a Leech shell, so the alphabet no longer covers
  its own hull. A target inside is tracked to the matched rule's `B/N` law, a
  target outside is certified unreachable by a separating functional, and the
  Gibbs-style rule is reached deterministically — greedy error feedback drives
  the visit frequencies to the Boltzmann weights inside the proved bound
  `(m−1)/N`, with no random number drawn.
- `reasoning/lean_address.py`, wired as `report lean`: every one of the
  **2764** declarations of the Lean development gets a deterministic Leech
  address computed from 24 integer counts of its statement. Read back exactly
  **2764/2764** with 0 coordinate errors; 2426 distinct addresses, exactly the
  number of distinct feature vectors, so the quantiser adds no conflation of
  its own; and nearest-by-address shares a file **560/2764** against 37 for a
  SHA-256-of-the-name control, 23 for a seeded reshuffle and a chance rate of
  `8878/636411`.
- `reasoning/escalation.py`, wired as `report escalation`: the layer audit run
  on **1,040 register carriers** rather than the seven of `report information
  loss`. Resolution climbs 415 → 544 → 757 and then stops, every boundary is a
  refinement with **zero violations**, and the ceiling the scale-up exposes is
  757 distinct carriers — 283 named entries share a carrier, in 104 collision
  classes all inside a single register, which no layer can separate because no
  layer sees anything but the carrier.
- `reasoning/directives.py` and `reasoning/pipeline.py`, wired as
  `report directives` and `report pipeline`: the standing rules of
  `PROJECT_DIRECTIVES.md` parsed rather than paraphrased, and the stage each
  piece of work has reached read off the tree rather than claimed in prose —
  **14 of 14 rows** through all six stages.
- `glm_universal/integrity.py` and `glm_universal/signoff/`: all SHA-256 use
  moved out of the six core sub-packages into one module above them, so
  directive D3 is enforced by the code layout and the purity audit; and a
  sign-off ledger that plans a run against recorded dependency digests
  computed from the source with `ast`. `glm_universal/tools.py` is their
  command line, kept out of the core for the same reason.

---

**v1.15.0** — the supplied archive, read to the end.

- The parts of `source_material/GLM-main.zip` the brief named were gone through
  script by script, and everything in them that could be stated as a theorem
  was retrieved as Lean: **25 files, 7,170 lines, 848 declarations**, building
  with no `sorry` — the MOG cube (`Cube/`), the lattice shortcut (`Shortcut/`),
  the three generations of the paper's formal companion, the electromagnetic
  calibration, the first-principles and projection sub-studies, the graded cost
  model, spatial arithmetic and the ARC-era reasoning loop.
- **Nine of the twenty-five are negative results** — the calibration chain
  returns the `c` it was given, `3, 6, 9` is generic, the forced number is 23
  rather than 24, the three-cube rules give a `[24,12,4]` code, the published
  directory's "even quantisation" is true by construction, the substrate's
  `snap_to_codeword` is not a decoder, consecutive integers are never a
  "geodesic jump", the electron-mass point's error bar is corrected, and
  `FitCapacity.lean` prices such agreements at all.
- The Lean corpus grew from 1,270 declarations across 48 files to **2,118
  across 73**, so the address book was rebuilt and
  `studies/LEAN_ADDRESS_STUDY.md` re-measured against the code: the separation
  signal rose to 13.2 times chance on the file test and 15.0 on the citation
  test. Nothing the system answers moved — the end-to-end evaluation is the
  same **131 / 131** with the same 16 boundary refusals.
- New: `tests/test_retrieved_lean.py` (the sixty-third test file) and the write-up
  `studies/RETRIEVED_LEAN_STUDY.md`. `glm_universal.__version__` 1.14.0 →
  **1.15.0**.

---

**v1.15.0, completed** — the dropped work, restored, and the archive's second
reading closed.

- The tree handed over at the end of the retrieval round was missing part of
  what that round had produced. Everything `dropped.zip` holds — Lean files,
  their test files and several study documents — is back, and **re-verified
  from the substrate rather than trusted**: the Lean sources build against the
  pinned Mathlib with no `sorry`, and every figure their tests pin was
  recomputed. The development stands at **95 Lean files, 27,548 lines, 2,764
  declarations**, and the two copies of the tree are byte-identical.
- The archive's **second reading** is eight results — the cube surface as the
  MOG grid, the read quantum as an operator, the Gray jump norm, the ARC grid
  metrics as interval bounds, the conditional lobe, the mode algebra, the free
  cube symmetries, and the parity count that caps them at 24
  (`Golay/CubeMirror.lean`, the one Lean file written new rather than
  restored). The two questions the first reading left open are both answered
  **no**: the archive's 44 balanced octads against a null census of all 735,471
  eight-subsets, and its relaxation shown to reach the code but not the nearest
  codeword.
- New reasoning modules `salvage.py`, `salvage_second.py`, `deep_dive.py`,
  `search_loop.py`, `combiner.py`, `tie_break.py`, `stability.py` and
  `exactness.py` (**57 modules**), each with its own test file (**72 test
  files**, 3,096 tests, 12,119 subtests).
- `report searchloop` is the **49 report subjects**' newest member and the
  evaluation's **132 CLI cases**' newest case; the end-to-end set is **132 /
  132** with the same 16 boundary refusals.
- The exactness clean-up is finished and enforced by a machine-checked
  inventory: every float site and every digest in the package is declared, and
  an undeclared one — or a declared one that has gone — fails the suite.
- The address book was regenerated over the larger corpus and
  `studies/LEAN_ADDRESS_STUDY.md` re-measured rather than patched: **2,764 /
  2,764 read back exactly, 0 coordinate errors**, 2,426 distinct addresses, and
  nearest-by-address shares a file **560 / 2,764** against 37 for the digest
  control and 23 for the seeded reshuffle.

---

**v1.15.0, the address layer made to do work** — retrieval, and the first
loop.

- `reasoning/retrieval.py`, wired as `report retrieval`: the address book used
  as an index over the Lean corpus and measured against six controls on 202
  stride-selected queries, with chance in closed form. hit@5 **51.5 %** against
  **6.9 %** chance; the digest (3.5 %), the seeded reshuffle (6.9 %), the
  random ranking (5.9 %) and name search (34.2 %) below it, and a plain text
  search **above** it at 85.6 % with 57.7 % precision@5. The two ablations say
  the lattice is not what carries the signal: the same features unquantised
  score 51.0 %, and a lexical address 64.9 %.
- `RequestProject/GLM/Retrieval.lean`: the completeness bound behind the
  shortlist — **144,075** measured pairs, **0** violations — under which an
  empty shortlist is a proof of absence. At feature radius 2 the
  guaranteed-complete shortlist is 70.9 declarations, 2.5 % of the corpus.
- `reasoning/controller.py`, wired as `report controller`: propose–check–refuse
  over the ten EXT10 generators, every returned plan re-verified end to end by
  `verifier.verify_expression_pair` (**100 %**, every scorer). **127 of 726**
  register quantities are refused with an invariant proof and no node expanded;
  the address scorer solves **18 of 24** against 8 unguided and 17 for the same
  distance without the lattice, and falls to exactly 8 when decoded at scale 1.
- `RequestProject/GLM/Controller.lean`: the invariant refusal, the
  exact-distance descent, and the decided witness that a width-one beam can
  miss a plan that exists.
- Two new test files, `test_retrieval.py` (42) and `test_controller.py` (25);
  the reasoning package is **59 modules**; `report retrieval` and `report
  controller` are the newest of the **51 report subjects** and the newest two
  of the **134 CLI cases**, and the end-to-end set is **134 / 134** with the
  same 16 boundary refusals.
- The address book was regenerated over the 97-file tree: **2826/2826** read
  back exactly, 0 coordinate errors, 2486 distinct addresses, and
  nearest-by-address shares a file 578 / 2,826 against 35 for the digest
  control and 37 for the seeded reshuffle.
- The write-ups are `studies/ADDRESS_RETRIEVAL_STUDY.md` and
  `studies/CONTROLLER_STUDY.md`.

---

**v1.14.0** — the last four hand-written branches deleted, and the quantiser's
search replaced by a lookup.

- The four parts `v1.13.0` named as still hand-written are description language
  now: a **list** (a slot whose filling is a sequence, cut at described
  separators held in two ranks), a **modifier** (a word that directs how the
  operands are read without naming one, removed at the head and in the trailing
  frame and *nowhere else*), described **trailing options**, and a **nested**
  shape (an operator whose sides are themselves a shape, tightened). With them
  the equation, the analogy operator, both comparison forms and the comparative
  lose their branches, which are frozen beside the first three in
  `language/legacy.py`.
- `compare` needed no new family: given a list slot it is a fourth **slot**
  shape. Coverage is **7 of the 20 answerable query kinds across 3 families**,
  every one of them read off its description by the runtime, at **15**, **13**
  and **4** judgements. Measured: 947/947, 201/201 and 480/628 agreement
  against the frozen branches, 20 narrowing witnesses, 0 false positives, and
  one declared widening — 148 comparatives written with `relative to` on a
  side, which the branch's hand-copied side pattern never admitted —
  accounted for with 0 left over.
- `RequestProject/GLM/QuestionNested.lean` carries the three new parts as
  theorems: the list cut (`ListCut.cut_sep`, `ListCut.cut_two`), the modifier
  frame at the head and the tail and *not* in the middle
  (`ModifierFrame.strip_head`, `ModifierFrame.strip_frame`,
  `ModifierFrame.strip_middle`) and the nested shape with its round trip and
  its two refusals (`NestedSpec.run_rendered`, `NestedSpec.run_no_operator`,
  `NestedSpec.run_side_refused`).
- `reasoning/llvq_table.py` is the **`O(1)` LLVQ lookup table** the original
  brief asked for, built out of the MOG: a codeword's six GF(4) column labels
  form a hexacode word, its six column parities agree and its top row carries
  that parity — all three checked over all 4,096 codewords — so the code is
  **128 classes of 32**, and `(label, parity, top bit)` fixes a column's
  pattern, which is the whole table at **16 entries**. A class minimum is a
  six-term min-sum under one parity constraint and the search is bounded, both
  proved in `RequestProject/GLM/LLVQTable.lean`
  (`isLeast_cost_of_parity_eq`, `isLeast_cost_of_parity_ne`,
  `card_parity_class`, `isLeast_of_bounded_search`).
- The subtractive test: `lean_address.quantise` decodes through the table, the
  scan stays in `analogy.py` as the thing to agree with, and the whole address
  book comes out unchanged — **2,118 declarations, 0 addresses changed**, with
  107 vectors agreeing point for point. The claim is stated as
  **constant-bounded, not constant**: 96.8 codeword costs per call against the
  scan's 8,192, worst case the whole code.
- New: the `report llvq` subject (**48 subjects**) with its Three Column
  Thinking template, `tests/test_llvq_table.py` (21 tests), an evaluation case
  for it (**131 cases**, 131/131) and the write-up
  `studies/LLVQ_TABLE_STUDY.md`. `glm_universal.__version__` 1.13.0 →
  **1.14.0**.

---

**v1.13.0** — the question shapes put in place of the branches, and a second
shape family measured.

- The three hand-written parser branches for `derive`, `measure` and `task` are
  **deleted**. `parse_query` dispatches those kinds through their descriptions
  (`if kind in DESCRIBED_KINDS: return _described_query(...)`), so the surface
  language for them is data rather than code.
- `language/question.py` gains a **`Preamble`** — an ordered list of word
  families that may be skipped before the opening, `repeatable` for the
  courtesies the parser stripped in a loop and once for the interrogative
  opener it stripped once. That is what let the branches go, and it is a
  narrowing: **15 witnesses** carrying a leading remainder the preamble does
  not admit are declined here and were answered there, in every case with the
  stray words inside an option. The two pieces are counted as judgements, which
  takes the slot shapes from **6 to 12**.
- `language/legacy.py` holds the three deleted branches verbatim, so the
  agreement audit still has something to measure against. It is imported by the
  measurement and by nothing in the runtime, and both halves of that are tested.
- `language/infix.py` is the **second shape family**: an operator that cuts a
  *string*, for questions whose operands are notations rather than runs of
  words. It describes `verify`, `analogy` and the relational half of `compare`
  — **8 operands, 34 surface forms, 9 judgements, 11 boundaries** — with an
  operator alternative able to carry a *meaning*, an *inner* operator for the
  analogy's four terms, and an operand that is described but not carried.
- Measured: **846 / 846** slot questions agree with the deleted branches (kind
  *and* options, 0 declined, 0 disagreed) and round-trip; **174 / 174** infix
  questions agree with the parser they have not yet replaced; **114** and
  **110** questions of other kinds are declined rather than misread. Coverage
  is **6 of the 20 answerable query kinds across 2 shape families**, 3 of them
  read off by the runtime. Verdict `described`.
- What is *not* done is named rather than implied:
  `language.build.UNDESCRIBED_PARTS` lists the four parts still hand-written —
  a modifier, a list, trailing options and a nested shape — each with the piece
  of description language it needs.
- `RequestProject/GLM/Question.lean` gains `runPre_of_skipped` (skipping a
  described preamble leaves the match unchanged), `runPre_refuses_undescribed`
  (an undescribed leading remainder is still refused), `skipPiece_once`,
  `skipPiece_twice` and `skipMany_of_le`, with five more questions of the
  shipped `derive` shape settled by `decide`.
- The write-up is `studies/LANGUAGE_STUDY.md` §3.1 and §10;
  `tests/test_language.py` is now a 90-test net.
  `glm_universal.__version__` 1.12.0 → **1.13.0**.

---

**v1.12.0** — the question every capability answers, made into an object.

- `language/` is the eleventh sub-package: `question.py` (a `QuestionSpec` — an
  opening, named slots with roles, the literal phrasings that separate them, an
  optional tail and the named boundaries the shape must refuse at, with every
  set of alternatives carrying the sentence that justifies treating it as one
  set), `descriptions.py` (three shapes and no code), `build.py` (the single
  generic matcher, the generated corpus and the four audits) and `report.py`.
- Described: `derive`, `measure` and `task` — **3 of the 20 answerable query
  kinds**, in **6 slots** and **44 surface forms** at **6 judgements**, with
  **14 openings** and **5 named refusal boundaries**. Each opening is exactly
  the set `parser.VERBS` maps to that kind and each separator exactly the set
  the branch it restates splits on, so nothing here extends the shipped
  surface.
- The test is a comparison and it is run: over a corpus of **692 questions**
  generated from the registers, the descriptions produce the same kind and the
  same options as the shipped parser **692 / 692**, with **0 declined and 0
  disagreed**; all **114** evaluation questions of the seventeen undescribed
  kinds are declined rather than misread (**0 false positives**); every one of
  the 5 boundaries has a witness that reaches it; every written question
  round-trips back to the slots it was written from (**692 / 692**); and the 14
  openings are pairwise non-prefix (**0 clashes**), so the shapes are a set and
  not a priority list. Verdict `described`.
- `report language` is the 47th report subject.
  `RequestProject/GLM/Question.lean` states the part that is not a measurement
  — `matchPieces_rendered` (writing and matching are inverse),
  `matchPieces_required_nonempty` (no silent empty slot),
  `matchPieces_adjacent_holes`, `matchPieces_no_separator`,
  `matchPieces_lit_none` and `matchPieces_not_both` (disjoint openings decide
  the shape) — and settles four questions of the shipped `derive` shape by
  `decide`.
- The write-up is `studies/LANGUAGE_STUDY.md`; `tests/test_language.py` is the
  51-test net. `glm_universal.__version__` 1.11.0 → **1.12.0**.
- **The report solvers moved out of the session.** `report language` was the
  47th subject answered by one dispatcher, and `runtime/session.py` had reached
  8,439 lines. The 47 solvers now live in `runtime/reports/` as eleven mixin
  modules — `substrate`, `lattice_geometry`, `registers`, `resolution`,
  `signal`, `ledgers`, `semantics`, `migration`, `development`, `recipe`,
  `language` — each named for the sub-package whose subjects it answers, with
  `Solution` and the payload helpers split out into `runtime/solution.py` and
  `runtime/payload.py`. `GeometricSession` composes the eleven, the session
  module is a third of its former size, and `tests/test_runtime.py` pins the
  split: no `_report_` method left in `session.py`, 47 across the mixins, every
  module registered in `REPORT_MIXINS`. Nothing about the query surface moved:
  the same 47 subjects answer with the same text.
- **The suite totals are no longer a fixed point.** They are now measured over
  the suite *minus* the document check itself (`tests/test_figures.py`, named
  in `signoff.ledger.DOCUMENT_CHECKS`), so nothing a document says can move the
  number that document quotes, and a release run reaches the fixed point in one
  pass by construction rather than by iterating.

---

**v1.11.0** — the recipe every capability follows, made into an object.

- `recipe/` is the tenth sub-package: `spec.py` (a `DomainSpec` — the facts a
  domain's objects hold, one derivation per coordinate, the keys the object is
  recovered from, the named readings of its layer chain, and the coordinates it
  must decline — written in **25** composable primitives, **23** of them used),
  `build.py` (the single generic path from a description to the carriers, the
  read-back audit, the readings as `Layer`s, the widening audit and the query
  surface with its refusal boundary), `descriptions.py` (the three descriptions
  and no code) and `report.py`.
- Measured over the three descriptions: **94 objects**, all 24-coordinate,
  **72 coordinates** of which **66** are shared derivations and **6** are
  judgements — the musical conventions, all in one domain. Read-back
  94 / 94, distinct carriers 94 / 94, and 3 named refusals refused per domain.
  The comparison chain gains: 42 → 43 → 45 classes; the other two gain nothing,
  because a ratio and a price already separate every object those registers
  hold.
- The test is subtractive: each domain is deleted and rebuilt from its
  description alone — **94 / 94 carriers identical**, the objects agree, and
  **9** figures the reasoning modules measure come back unchanged (11 with the
  two exhaustive ones). Verdict `regenerated`, 3 of 3.
- `derive <coordinate> of <object>` is the 21st query kind, answered off
  whichever description derives the coordinate, and `report recipe` is the 46th
  report subject. `RequestProject/GLM/Recipe.lean` states the path itself —
  `readingOn_mono`, `readingOn_append_least`, `boundary_readingOn_nonempty_iff`,
  `lossless_readingOn_iff`, `encode_injective_of_keys`, `rebuild_encode`,
  `answer_eq_none_iff`, and `encode_congr` / `indist_congr` / `answer_congr`,
  which is regeneration stated formally.
- The write-up is `studies/RECIPE_STUDY.md`; `tests/test_recipe.py` is the
  87-test net. `glm_universal.__version__` 1.10.0 → **1.11.0**.

---

**v1.10.0** — what the undimensioned names denote, decided rather than searched.

- `basis_sweep()` exhausts the automatic half first: of the **713** quantities
  the physics register holds and the factor basis does not, 571 change nothing,
  125 would make an attribution ambiguous and are refused, and the 17 that
  strictly convert more occupy four dimensions — so the data decides three
  factors and nothing further is available by search.
- `data_objects/denotation.py` decides the residue's **36** undimensioned
  endpoints one name at a time, each with a written justification, under six
  verdicts (1 `quantity`, 3 `ambiguous`, 4 `polymorphic`, 9 `carrier`,
  11 `process`, 8 `abstraction`); `denotation_audit()` refuses an entry that
  names a quantity the register does not hold, shadows one it does, or carries
  no justification.
- `reasoning/denotation_view.py` measures what the decisions changed: of the 39
  declined triples, **0** convert, 6 are repaired to `names_process_of` and 33
  are declined by a reason that names what the endpoint is; coverage is exact
  both ways and `closure()` reports 39 of 39 accounted for. The repairs carry —
  12 of the 22 analogies the converted triples license are answered, against 1
  for the unrepaired control.
- `report denotations`, `RequestProject/GLM/Denotation.lean` and
  `studies/DENOTATION_STUDY.md`. `glm_universal.__version__` 1.9.0 → **1.10.0**.

---

**v1.9.0** — the measure-word round's open items closed, and the factor basis
measured instead of asserted.

- `data_objects/comparison_classes.py` gained volume, illuminance and luminous
  intensity: 33 classes over 8 quantities → **45 over 11**, 47 degree words over
  8 scales → **64 over 11**, and 12 words shared with the semantic lexicon,
  still agreeing on quantity, polarity side and the six opposite-pole pairs.
  The widening audit runs over 56 uses: the static reading resolves 12, the
  widened one all 56, gaining 108 pairs with 0 refinement violations.
- `FACTOR_BASIS` is 13 → **16** on the evidence of the sweep, and `related_to`
  conversion 15 → **27** of 66, residue 51 → **39**.
- `comparative` is a query kind of its own, recognised structurally rather than
  by keyword: of the 56 uses, 228 pairs are comparable, word order decides
  24 of 24 within a class and gets 151 of 204 backwards across classes.
  `RequestProject/GLM/Comparative.lean` is the machine-checked half.
  `glm_universal.__version__` 1.8.0 → **1.9.0**.

---

**v1.8.0** — an economic register, and the last third of that claim.

- `data_objects/economics_register.py`: **21 quoted prices** as exact
  rationals — seven instruments over three consecutive quarters, four sectors,
  six currency pairs — every price stored as a fraction of integers and read
  as a `Fraction`, never as a float, and every non-currency instrument naming
  a physical denominator. Loaded by the runtime as the eighth register,
  `economics`.
- `reasoning/economics.py` and `report economics`: the magnitude a price is
  read through is `⌊log_b x⌋` computed by integer comparison rather than by a
  logarithm, and the catalogue's universality claim is then measured for
  markets. The lattice separates all 21 records at scale 1024, orders them by
  magnitude at tau `39/70`, and every record's nearest neighbour is another
  quarter of the same instrument — 21 of 21 against a chance rate of `1/10`.
  **The verdict is `not reproduced`**: the undecoded control scores 21 of 21
  as well, so what is measured is the price vector rather than the geometry of
  the lattice — the same answer the musical third reached by the same
  instrument.
- `reasoning/catalog.py`: section 6.2's economic half is no longer
  `not implemented`; both halves now read their verdict off their own study at
  call time. The ledger is 58 claims: 33 confirmed, 14 refuted, 8 not
  reproduced, 3 not implemented.
- `migration/state.py` and `migration/store.py`: the hexcolour address layer is
  audited rather than merely carried — 4,680 concepts, 4,680 distinct
  addresses, 0 read-back failures, 0 disagreements with the stored masks, 0
  failures to commute with the legacy-to-core relabelling, and the 15 legacy
  per-task addresses all Golay codewords — and the concept store now supports
  lookup *by* address, with every concept tested to round-trip through it.
- `RequestProject/GLM/LogBucket.lean`: the magnitude bucket proved well
  defined, unique, monotone and scale-shifting, with the scaling lemma that
  makes the study's control one set of numbers rather than a sweep.
  `RequestProject/GLM/Heisenberg.lean`: the infinite-dimensional half of the
  VOA bridge — the Fock space, the Heisenberg relation, state truncation,
  Borcherds' commutator formula, and the trace obstruction that no nonzero
  finite-dimensional rational space admits the relation at all.
- `glm_universal.__version__` was `1.8.0` at this round, pinned by
  `test_wiring.py::TestPackageSurface`.
- The write-ups are `studies/ECONOMICS_STUDY.md` and
  `studies/HEXCOLOUR_STUDY.md`.

---

**v1.7.0** — a musical register, and the third of a claim it makes testable.

- `data_objects/harmonics.py`: **28 musical intervals** as exact rational
  frequency ratios — 18 just, 5 septimal, 5 commas — every one of the 24
  coordinates computed from the pair `(n, d)` rather than stored beside it, so
  the register needs no measurement, no calibration and no float. Loaded by the
  runtime as the seventh register, `harmonics`.
- `reasoning/harmony.py` and `report harmony`: the catalogue's universality
  claim — chemical equilibria, musical harmony and market price discovery all
  said to be Leech proximity — tested for the musical third of it instead of
  repeated. Equal temperament's error is the exact rational `(n/d)^12 / 2^k`;
  the stack of fifths never closes; Tenney height and Euler's gradus are
  compared at an exact Kendall tau; and each interval is decoded to its nearest
  Leech point through its prime exponents, deliberately not through its carrier.
  **The verdict is `not reproduced`**: proximity does order the intervals, at
  tau `53/63`, but the same distance taken *before* the decoder runs scores
  `53/63` too and the decoder reorders no pair, so what is measured is the
  prime-exponent vector rather than the geometry of the lattice.
- `reasoning/catalog.py`: section 6.2 is now carried as **two** claims — the
  musical half, whose verdict is read off the harmony study, and the economic
  half, which stays an open gap because there is no economic register. The
  ledger is 58 claims: 33 confirmed, 14 refuted, 7 not reproduced, 4 not
  implemented.
- `RequestProject/GLM/Harmony.lean`: why no tempering error can be zero.
  `odd_prime_ratio_ne_two_zpow` — a ratio in lowest terms carrying any odd
  prime is not a step of *any* equal division of the octave, for every number
  of divisions at once — with `fifth_never_closes` and the two commas exact.
- `glm_universal.__version__` is `1.7.0`, pinned by
  `test_wiring.py::TestPackageSurface`.
- The write-up is `HARMONY_STUDY.md` at the repository root.

---

**v1.6.0** — the sign-off ledger made sound, and every instrument in it.

- `signoff/ledger.py`: a unit's closure now also carries the **documents and
  Lean sources its modules name**, found by parsing each module's string
  constants. Without that, `tests/test_figures.py` — whose whole job is to
  catch a stale count in `STATUS.md` — stayed signed off while `STATUS.md` was
  being rewritten, which is a saving bought with a false statement. A `.lean`
  mention pulls in the whole development and its build files. The schema is
  bumped 1 → 2, discarding every signature written under the old rule.
- `signoff/checks.py`: seven non-pytest instruments — `lean-build`,
  `lean-sorry-free`, `lean-copies-identical`, `capabilities`, `benchmarks`,
  `evaluation`, `figures` — signed off by the same rule, in the same ledger,
  with the command itself part of the digest. `--run-checks`,
  `--run-everything` and `--run-checks-all` on the sign-off command line;
  `python -m glm_universal.tools signoff` is the read-only summary.
- `figures.py --check` compares `FIGURES.md` with a fresh computation, prints a
  unified diff and exits 1 if they differ.
- `glm_universal.__version__` is `1.6.0`, pinned by
  `test_wiring.py::TestPackageSurface`.
- The write-ups are `HIGHER_LATTICE_STUDY.md` and `LEAN_ADDRESS_STUDY.md` at
  the repository root.

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
│   ├── cases.py               the 134 CLI cases, every query kind and report subject
│   ├── harness.py             run_case, run_all, evaluation_report, the scoring
│   └── __main__.py            CLI, with --only, --case, --jobs, --json, --list
├── tests/                     ← 74 test files
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
**21 query kinds** and **51 report subjects** over **8 registers** — see
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
