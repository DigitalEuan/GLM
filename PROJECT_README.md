This project was edited by [Aristotle](https://aristotle.harmonic.fun).

To cite Aristotle:
- Tag @Aristotle-Harmonic on GitHub PRs/issues
- Add as co-author to commits:
```
Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
```

# GLM system completion + the boundary studies

This repository holds the completed Geometric Language Machine package and two
studies that came out of finishing it: what is lost when one layer hands over
to the next, and what happens to a value that no carrier can hold.

The package lives in **`overlay/`** — the supplied archive, unpacked and
finished. The Lean 4 development lives in **`RequestProject/GLM/`** and builds
with `lake build`, with no `sorry`; the overlay keeps its own copy of the same
files under `overlay/glm_lean/`.

The package holds **8 registers** of carriers, reached through **21 query
kinds** one of which dispatches **48 report subjects**, and is checked by
**62 test files** alongside **48 Lean files**.

Every count in this repository's documentation is recomputed by
`overlay/glm_universal/figures.py` and written to
[`overlay/FIGURES.md`](overlay/FIGURES.md). Regenerate it with
`python -m glm_universal.figures --write` from `overlay/`;
`tests/test_figures.py` fails when a document and the code disagree, so no
figure below needs to be re-derived by hand. The shortest route to the
current state of the work is [`STATUS.md`](STATUS.md).

```bash
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q     # 62 test files
PYTHONPATH=. python3 GLM.py -q "report information loss" -c 1
PYTHONPATH=. python3 GLM.py -q "report infinite values"   -c 1
PYTHONPATH=. python3 GLM.py -q "report capabilities"      -c 1
PYTHONPATH=. python3 -m glm_universal.capabilities
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8
```

```bash
lake build          # RequestProject/GLM/*.lean, 48 Lean files, no sorry
```

## 1. The GLM system, completed

* **`GLM.py` was missing from the archive.** The READMEs document it and two
  test files import it by path, so 30 CLI tests errored on collection. It has
  been written against the behaviour those tests specify — batch and
  interactive modes, all documented flags and meta-commands, and the exit-code
  contract.
* **The legacy `snap` decoder is retired.** Complete syndrome decoding
  (`substrate/golay_decode.py`) returns *every* nearest codeword and a status;
  no tie is broken silently. Weight-5 miscorrection is shown, via the Steiner
  system `S(5,8,24)` verified over all 42,504 five-subsets, to be a theorem
  about the code rather than a defect of the decoder.
* **The full Leech lattice replaces Construction A**, restoring the true
  kissing number 196,560 from A's 48, with each construction condition shown
  necessary by what breaks without it; **the exact 2A Sakuma product replaces
  the XOR shortcut**; **the six facets are strict linear projections** with the
  exact lattice index that says what a facet reading loses.
* **The `LEGACY_TO_CORE` bridge is implemented and tested**: the two frames
  share exactly 8 of their 4,096 codewords, the permutation is an isometry and
  therefore safe to wrap around a decoder, and a dataset migrates through one
  call with round-trip and referential-integrity checks.
* **`semantics/` replaces spelling with meaning.** The inherited concept graph
  was audited rather than described — 83 of its 4,282 concepts denote anything
  determinate, and 2 of its 4,015 edges state a re-derivable relation — and the
  grounded graph that replaces it holds 357 meanings, 1,705 notations and
  12,859 edges, every one re-derived on demand.
* **`capabilities/` says where the machine stops.** 33 probes, each phrased as
  a question a user would ask, each answered by running the real code: 20 hold,
  13 break, 0 errored, 0 surprises. A break is a located boundary, not a
  failure — and when one is closed the probe flips to `holds` and says so, as
  the transcendental-function probe did.
* **A molecules register.** 51 molecules over 17 elements, each parsed from a
  formula into an exact composition and encoded losslessly into the same
  24-coordinate carrier; and `reasoning/element_coverage.py`, which measures
  how sparse the element table really is and widens it three ways, each
  labelled by provenance.
* **Zero failures across the suite**, and every published number is recomputed
  by a `*_report` function rather than quoted.

**[`MASTER_PLAN.md`](MASTER_PLAN.md)** tracks this work phase by phase, with
what was built, where it lives, and how to see it recompute itself.

## 2. The information-loss study

The write-up is **[`INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md)**.

It takes the thesis that a system is true up to a point, then is superseded by
a higher one which is true in its own right, and makes it precise enough to
prove. The central results, all machine-checked in Lean 4 under
`RequestProject/GLM/`:

* **Information lost at a boundary is exactly new expressive power**
  (`boundary_nonempty_iff_new_visible`).
* **Nothing true below becomes false above** — visible propositions survive
  every refinement (`Visible.mono`) — so the "becomes untrue" of the thesis is
  located precisely: not in propositions changing truth value, but in
  operations ceasing to be functions of what a layer sees
  (`descends_iff_congruent`).
* **The ascent is forced** by capacity below the carrier count
  (`exists_indist_of_capacity_lt`), and it is computable: `escalate` returns
  the least layer that separates two carriers, proved correct and minimal.
* **And it continues without end.** The dyadic tower is an explicit infinite
  ladder in which every step is a strict gain in expressive power
  (`dyadic_boundary_nonempty`, `dyadic_new_visible`), no step loses anything
  earlier (`dyadic_refines_of_le`), and every distinction is eventually made
  (`dyadic_separates`).

and four concrete, sharp boundaries: the layer stack over ℚ, addition ceasing
to descend, the TAX conservation law (exact on bits; above it, repairable only
if `Y = 1/2`, which is false), and Golay repair (unique at Hamming weight 3,
ambiguous at 4).

## 3. The infinite-values study

The write-up is **[`INFINITE_VALUES_STUDY.md`](studies/INFINITE_VALUES_STUDY.md)**. It
answers whether `cardinal_geometry_synthesis.md`,
[`DYNAMIC_CARRIER_STUDY.md`](source_material/DYNAMIC_CARRIER_STUDY.md) and
`geometric_substrate_study.py` provide what is needed to get the GLM working
with infinite values and irrational numbers. They do, and it has been built:

> A carrier is finite. A process is not. The GLM holds an irrational as the
> process, not as the carrier — and the process is a first-class object it can
> add, multiply, compare, print, refine and refuse.

* **The value layer.** `reasoning/exact_real.py` holds a real as a rule:
  `x.at(k)` returns an exact `Fraction` within `2⁻ᵏ`, for any `k`, with no
  float anywhere. `reasoning/real_expr.py` reads written expressions over those
  processes — `(1+sqrt(5))/2`, `sqrt(2)+sqrt(3)`, `pi/4`, `root(3, 2)` — and
  reads a decimal literal as the rational it names, so `0.1+0.2` is exactly
  `3/10`. `reasoning/transcendental.py` adds `exp`, `log`, `sin`, `cos`, `tan`
  and a non-integer exponent, so `2^pi` and `log(2, 8)` are values like the
  rest.
* **Two new query kinds.** `approximate <expr> to <n> places`, and the
  comparison family (`is pi less than 355/113`, `compare sqrt(2) and 1.5`,
  `which is bigger e or pi`), which reports the precision that settled the
  order — and refuses to claim equality, which is not decidable.
* **A carrier that moves reaches every real**, at a proved rate: after `N`
  ticks the modulator's time average is within `1/N` of the target
  (`dsAverage_error_le`, `dsAverage_tendsto`).
* **In 24 dimensions the geometry bounds it.** Every emitted state is a Golay
  codeword, so the reachable set is the convex hull of the code
  (`avgVec_mem_hull`), and for a target outside it the package computes a
  separating linear functional — verified against all 4,096 codewords, gap
  `13/5760` — which with `not_tendsto_avg_of_separating` proves no quantiser
  rule converges there. `avgVec_periodic` pins the set from the other side.
* **What is computable about an approximated value** is settled exactly in
  `Computable.lean`: a real is nonzero *iff* a witness `|x| ≥ 2⁻ᵐ` exists, so
  division needs precisely that witness; no fixed search depth works for every
  divisor; and two processes never separated are equal, but "never" quantifies
  over all precisions at once, which is why equality is refused and inequality
  is decided.

* **`exp`, `log`, `sin`, `cos`, `tan` and a real power `x^y`** are built on
  the same footing, in exact rational arithmetic with no float anywhere, and
  the error budget each one pays is machine-checked in `Transcendental.lean`.
  `log` needs a positivity witness for the reason division needs a nonzero
  one, and `pos_iff_witness` says such a witness is exactly what positivity
  is.

The study also names the capabilities that are absent rather than impossible,
with the exact place each stops: the inverse and hyperbolic functions in the
value grammar, a vocabulary that is exactly the registers, and no query kind
that does arithmetic over register names.

## 4. The geometric-ambiguity study

The write-up is **[`GEOMETRIC_AMBIGUITY_STUDY.md`](studies/GEOMETRIC_AMBIGUITY_STUDY.md)**.
It asks what the machine should do when the geometry does not name one answer,
and answers it by building the case out rather than by choosing a tie-break:

> An ambiguous reading is not a failed reading. At a deep hole of the Golay
> code there are exactly six nearest codewords, and which of the six is meant
> is information the received word does not contain — so the machine carries
> all six until a context supplies it.

* **The tie has an exact shape.** `Golay/Sextet.lean` proves, from exhaustive
  checks over all 4,096 syndromes, that the code has minimum distance 8 and
  covering radius 4, that a reading is unique up to weight 3, and that a
  weight-4 coset has **exactly six** nearest codewords whose supports partition
  the 24 coordinates into six tetrads — the sextet (`ties_card_eq_six`,
  `sextet_partition`). Every coset is either uniquely readable or a six-fold
  tie.
* **How ambiguity is carried decides whether it survives.** Bundling the six
  readings by XOR gives the all-ones vector *whatever the tie is*
  (`bundleF2_eq_one`), so the binary bundle of a superposition is
  information-free. The same bundle over the rationals is injective and
  invertible (`bundleQ_eq`, `bundleQ_recover`, `bundleQ_injective`). The
  package measures both: over 256 superpositions the F₂ bundle distinguishes 1
  input and the rational bundle distinguishes all 256.
* **Collapse is contextual.** `substrate/superposition.py` filters a
  superposition by a context predicate and reports `collapsed`, `superposed` or
  `refuted`; it never breaks a tie by member order, so a guess is never
  disguised as an answer.
* **Wobble is a lossless way to hold the tie.** A carrier cycling through the
  six readings is read back exactly as their rational bundle
  (`sextet_cycle_avgVec`), and that reading still determines which six they
  were.
* **When a wider alphabet is genuinely needed.** `HullExpansion.lean` exhibits
  a target separated from the hull of the available states by an explicit
  linear functional — so no schedule reaches it — and reaches it exactly in 16
  ticks once two Leech vectors are admitted: `alphabet_expansion_strictly_helps`
  is the statement that the gain is in the alphabet, not in the schedule.
* **Wired into the runtime** as the `report superposition` subject, with a
  Three Column Thinking template that recomputes every figure above in a fresh
  interpreter.
* **The dynamical reading is settled, and mostly negatively.** The
  perturbation chain on cosets has the uniform law as its unique stationary
  law but is periodic, so it has no limiting law at all; what converges is the
  time average, and `Golay/Cesaro.lean` proves that it does, at the explicit
  rate `|cesaro μ N f − 1/4096| ≤ 24/N`.

The study is explicit about what it does not settle — the Niemeier deep-hole
census is named as open, not glossed. The VOA state–field map it also named is
now partly built: `VOA.lean` constructs `Y(u, z)` at the Griess layer of the 2A
algebra, proves the structure that layer really carries — truncation,
skew-symmetry, a forced invariant form, self-adjoint modes, nondegeneracy and a
vacuum — and then proves the obstruction exactly, `borcherds_commutator_fails`,
so the infinite-dimensional half is shown to be necessary rather than assumed.

## 5. What the machine can actually do, measured

The write-up is **[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md)**. It
does not describe the machine; it reports what happened when the machine was
run, with every figure produced by a command that can be re-run.

* **A new instrument, `glm_universal/evaluation/`.** **131 cases**, each
  starting `GLM.py` in a **fresh interpreter** — one subprocess per question,
  no shared session, no warm caches — covering **all 21 query kinds** and all
  **48 report subjects**, with the coverage checked against the runtime's own
  tables by a test. 16 of the questions are ones the machine *should* refuse.
* **Scoring is asymmetric.** A refusal tells the user where the machine stops
  and a confident wrong answer does not, so `correct` and `refused_as_expected`
  score `+1`, an unexpected refusal `0`, and a wrong answer or a crash `−1`.
* **The result: 131 of 131.** 115 answered correctly, 16 refused as expected,
  **zero** unexpected refusals, **zero** confidently wrong, 0 errored. Every
  kind is clean, `analogy` included at 10/10; the five analogy failures the
  first assessment recorded were closed by the model-selection layer described
  in [`ANALOGY_LAYER_STUDY.md`](studies/ANALOGY_LAYER_STUDY.md).
* **Boundaries separated from gaps, and no gap is left.** All 15 correct
  refusals are boundaries — undecidable equality of real processes, a
  vocabulary that is exactly the registers, a quotient by an exact zero. The
  last gap was `coherence PbCl2`, and it is closed: every solver that takes a
  carrier and nothing else now hands an operand no register enumerates to the
  molecule formula parser before refusing, so a species the element register
  can encode is scored rather than declined. Nothing is guessed — an
  unparseable formula still refuses.
* **The other two instruments, re-run:** 33 probes (20 hold, 13 break, 0
  errored, 0 surprises) and 2,389 of 2,390 benchmark tasks across 5 suites,
  every suite above its baseline.

The document ends by naming what is untouched — the Niemeier deep-hole census, the
missing lexicon relation behind `heat : temperature :: force : ?`, the 32- and
48-dimensional lattices, open vocabulary, words as projections,
and the delta–sigma directions still not started (sigma–delta on the Leech
shells and the Gibbs-style rule; error feedback through a symmetry-commuting
rational matrix was on that list and is now built and proved) — so nothing is
implicitly claimed. The infinite-dimensional half of the VOA bridge was on that
list too and is now built: `RequestProject/GLM/Heisenberg.lean` carries the
Fock space, the Heisenberg commutator and the trace obstruction that rules out
any finite-dimensional model of it. The same
list is kept in `MASTER_PLAN_ARCHIVE.md` §7.9 and mirrored in
[`STATUS.md`](STATUS.md).

## 6. The two supplied documents, read as claim ledgers

Two of the supplied files record claims rather than code:
`glm_unification_blueprint.md`, a specification, and
`glm_study_findings_catalog.md`, a record of measurements from studies run
outside this package. A document that is only read drifts from the system it
describes, so each was turned into a **live ledger**: every testable sentence
restated as a claim, recomputed against the package as it stands, and given one
of four verdicts — `confirmed`, `refuted`, `not reproduced`, `not implemented`.

* **The blueprint.** `reasoning/blueprint.py`, `report blueprint`. Write-up:
  **[`GLM_UNIFICATION_BLUEPRINT_AUDIT.md`](studies/GLM_UNIFICATION_BLUEPRINT_AUDIT.md)**.
  Reaching verdicts needed three subjects built beside it —
  `reasoning/engine.py` (Part III's carrier engine), `reasoning/mantissa.py`
  (binary64 modelled exactly, with no float ever constructed) and
  `reasoning/reversible.py` (the Gray read channel, the Toffoli and Fredkin
  gates, the kink invariant) — with `Mantissa.lean` and `Reversible.lean` as
  the machine-checked half.
* **The study catalogue.** `reasoning/catalog.py`, `report catalog`. Write-up:
  **[`GLM_STUDY_CATALOG_AUDIT.md`](studies/GLM_STUDY_CATALOG_AUDIT.md)**. **58
  testable claims: 33 confirmed, 14 refuted, 7 not reproduced, 4 not
  implemented.** Where the catalogue reports a number produced by running a
  loop, the package reproduces it to the digit; where it reports that a
  measured column *is* a property of the thing measured, the column is usually
  a closed form of the input. The sharpest case is the "vibrational
  signature": `Sturmian.lean` proves that the modulator's stream is the
  mechanical word of its target, so entropy, run lengths, transition rate and
  one-density are all determined by the target before the loop is run
  (`reasoning/wobble.py`, `report signature`). `reasoning/drift.py`
  (`report drift`) reruns the prime-iteration stress test in three regimes —
  exact rationals, an exact binary64 model, and binary64 truncated to a fixed
  number of displayed digits — again with no float constructed anywhere.
* **The two companion preprints.** `reasoning/companion.py`,
  `report companion`. Write-up:
  **[`GLM_COMPANION_STUDIES_AUDIT.md`](studies/GLM_COMPANION_STUDIES_AUDIT.md)**.
  **49 testable claims: 26 confirmed, 17 refuted, 5 not reproduced, 1 not
  implemented.** The catalogue above summarises these two studies, and a
  summary loses the definitions — the projection, the indexing, the alphabet —
  so several verdicts the catalogue had to leave open are settled here. The
  instrument built beside it is `reasoning/containers.py`
  (`report containers`): eight constants through three containers, with both
  hull verdicts checked against all 196,560 Leech minimal vectors rather than
  a sample of 150, since a sample can establish *inside* and can never
  establish *outside*.

## 6b. The musical third of the catalogue's universality claim

Section 6.2 of the catalogue says chemical equilibria, musical harmony and
market price discovery all map to Leech proximity. Two thirds of that can now
be measured here. `data_objects/harmonics.py` holds **28 intervals** as exact
rational frequency ratios — every coordinate computed from the pair `(n, d)`,
no float anywhere — and `reasoning/harmony.py` (`report harmony`) tests the
sentence rather than repeating it: equal temperament's miss is the exact
rational `(n/d)^12 / 2^k`, `1` at the unison and the octave and nowhere else;
no stack of fifths is a stack of octaves, searched to `n = 200` and proved for
every `n` in `Harmony.lean`; and each interval is decoded to its nearest Leech
point through its prime exponents.

**The verdict is `not reproduced`.** Proximity does order the intervals by
consonance, at an exact Kendall tau of `53/63` — but the same distance taken
*before* the decoder runs scores `53/63` too, and the decoder reorders no
pair, so what is measured is the prime-exponent vector rather than the
geometry of the lattice. Write-up:
**[`HARMONY_STUDY.md`](studies/HARMONY_STUDY.md)**.

The economic third is now measured too. `data_objects/economics_register.py`
holds 21 quoted prices as exact rationals — seven instruments over three
consecutive quarters — read through an exact magnitude bucket decided by
integer comparison rather than by a logarithm, and proved well defined,
unique, monotone and scale-shifting in `RequestProject/GLM/LogBucket.lean`.
The lattice separates all 21 records at scale 1024 and every record's nearest
neighbour is another quarter of the same instrument, 21 of 21 against a chance
rate of `1/10` — but the undecoded control scores 21 of 21 as well, so this
third is **`not reproduced`** for the same reason the musical one is. Write-up:
**[`ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md)**.

## 7. Checking it, without checking it twice

The suite is about a quarter of an hour, and `lake build`, the end-to-end
evaluation, the benchmark suites, the capability probes and the figures check
cost more again. Almost none of it changes between one iteration and the next,
and re-running an unchanged check proves nothing — but "it is probably still
fine" is a guess, not a verification.

`overlay/.glm_signoff.json` makes the guess into a check. Each of the 61 test
files and each of the 7 instruments carries the SHA-256 of **everything its
last passing result depended on**: the file itself, every package module it
imports transitively, the frozen data those modules read, the documents and
Lean sources they name, the test scaffolding and the interpreter version. If
the digest still holds, the result still holds. If one byte anywhere in that
closure differs, the unit is stale and runs again.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.signoff --verify         # what still holds
PYTHONPATH=. python3 -m glm_universal.signoff --plan           # what would run, and why
PYTHONPATH=. python3 -m glm_universal.signoff --run-everything # run only that
PYTHONPATH=. python3 -m glm_universal.signoff --run-all        # ignore the ledger
```

Three things keep it honest: a failure is recorded as a failure and never
signs; the sign-off package's own sources are inside every closure, so changing
the rules invalidates every signature; and nothing is skipped silently —
`--plan` says what will be skipped before anything runs and `--verify` re-checks
every signature without running a test. The full run stays available and is
what a release check does. The rule is directive **D4** of
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md); the design is
[`MASTER_PLAN_ARCHIVE.md`](MASTER_PLAN_ARCHIVE.md) Phase 12.

## Layout

```
README.md                     this file
STATUS.md                     where the work stands now, and what is left
MASTER_PLAN.md                the wiring status: the header, the phase index, the open phase
MASTER_PLAN_ARCHIVE.md        the closed phases, kept as they were written
CAPABILITY_ASSESSMENT.md      what the machine can do, measured rather than described
PROJECT_DIRECTIVES.md         the standing rules, and the instrument that enforces each
DOCUMENTS.md                  the index: one line per document, wherever it lives
studies/                      the write-ups produced here
  INFORMATION_LOSS_STUDY.md   loss at the layer boundaries, and the refinement-chain decision
  ESCALATION_STUDY.md         the same audit at register scale, and the resolution ceiling it finds
  INFINITE_VALUES_STUDY.md    infinite values and irrational numbers
  GEOMETRIC_AMBIGUITY_STUDY.md  ambiguity, superposition and contextual collapse
  ANALOGY_LAYER_STUDY.md      how A : B :: C : D was made to work, and what it still cannot do
  RELATIVE_MEASURE_PROPOSAL.md  a proposal: measure words as relative measures, and what it needs
  NOISE_EXPERIMENT_STUDY.md   noise used as the computation: cascaded loops, closed orbits,
                              interacting tones and dither, all exact
  GLM_UNIFICATION_BLUEPRINT_AUDIT.md  the unification blueprint read as a live claim ledger
  GLM_STUDY_CATALOG_AUDIT.md  the external study findings, recomputed and given verdicts
  GLM_COMPANION_STUDIES_AUDIT.md  the two companion preprints, recomputed against the definitions they state
  HARMONY_STUDY.md            the harmonic register, and the claim it makes testable
  ECONOMICS_STUDY.md          the economic register, and the last third of the same claim
  HEXCOLOUR_STUDY.md          the hexcolour address layer, audited on the shipped data
  HIGHER_LATTICE_STUDY.md     the two rungs above the Leech lattice
  LEAN_ADDRESS_STUDY.md       a Leech address for every Lean declaration
  NAME_COORDINATE_STUDY.md    a coordinate for the name, and the ceiling it lifts
  RELATIVE_MEASURE_STUDY.md   measure words as relative measures, and the comparative
  DENOTATION_STUDY.md         what the undimensioned names denote, decided one at a time
  RECIPE_STUDY.md             the recipe made into an object: three domains regenerated
                              from their descriptions alone
  LANGUAGE_STUDY.md           the question shape made an object: seven query kinds matched
                              by shape, and measured against the parser they restate
  LLVQ_TABLE_STUDY.md         the quantiser's search replaced by the MOG's class table,
                              and every address in the corpus unchanged
source_material/              what was supplied, kept as received
  DYNAMIC_CARRIER_STUDY.md    the moving-carrier proposal these studies test
  cardinal_geometry_synthesis.md, geometric_substrate_study.py,
  glm_unification_blueprint.md, glm_study_findings_catalog.md, ToDo_01.txt,
  GLM_Generators_Containers (2).pdf, GLM_Iteration_Study (1).pdf
RequestProject/GLM/           the Lean 4 development (48 Lean files, no sorry)
  Constants.lean              Y, Q, TAX, NRCI, coherence regimes
  TaxConservation.lean        the conservation law and its boundary
  Layers.lean                 the abstract theory of layers and boundaries
  Cumulative.lean             how a stack is made a refinement chain
  Tower.lean                  the unbounded dyadic tower: "this continues"
  Stack.lean                  the concrete substrate/integer/rational stack
  LayerChain.lean             the shipped five-layer chain, proved a refinement on real carriers
  Escalation.lean             the same chain at register scale: the resolution ceiling, the
                              order of the stack, and where addition stops descending
  GolayBoundary.lean          the snap-radius boundary
  Permutation.lean            coordinate permutations are isometries
  Endianness.lean             MSB-first against LSB-first, as a frame choice
  Sakuma.lean                 the 2A product against the XOR shortcut
  Facets.lean                 the six-facet orthogonal decomposition
  DeltaSigma.lean             the 1/N law of the moving carrier
  Irrational.lean             the cardinality wall, and the faithful tower
  Reachable.lean              the convex hull, and the separating certificate
  Computable.lean             division, comparison and equality of processes
  Transcendental.lean         the error budget of exp, log, sin, cos and x^y
  Semantics/Meaning.lean      the meaning carrier, its round trip, its capacity
  Semantics/Grounding.lean    meaning against spelling; the EXT10 → SI7 boundary
  Golay/Code.lean             the concrete Golay code and its syndrome algebra
  Golay/Sextet.lean           covering radius 4, and the six-fold tie at a hole
  Golay/Census.lean           the coset census, and the mean coset weight 3433/1024
  Golay/Dynamics.lean         the perturbation chain: it averages, it does not settle
  Golay/Cesaro.lean           the Cesàro convergence of those averages, with rate 24/N
  Superposition.lean          the F2 bundle against the rational bundle
  Wobble.lean                 a carrier cycling through the six tied readings
  HullExpansion.lean          when a wider alphabet is what buys the reach
  VOA.lean                    the state-field map Y(u,z), and where the finite layer stops
  Heisenberg.lean             the Fock space past that layer: the Heisenberg relation, and the
                              trace obstruction that no finite-dimensional space can satisfy it
  Mantissa.lean               where a float's precision goes: the collapsing dyadic orbit
  Reversible.lean             the Gray read channel, the reversible gates, the kinks
  Cascade.lean                signal-driven and cascaded delta-sigma: O(1/M^2) against O(1/M)
  Feedback.lean               error feedback through a rational matrix, and the symmetry it keeps
  Sturmian.lean               the stream as a mechanical word: run lengths, transitions, entropy
  HigherLattices.lean         past 24: the 32- and 48-dimensional extremal rungs
  ShellSigma.lean             delta-sigma against a Leech shell rather than a scalar
  Address.lean                what a lattice address of a declaration can and cannot mean
  Harmony.lean                why no tuning ever closes, and no interval is ever tempered exactly
  LogBucket.lean              an exact magnitude without a logarithm, and the control it licenses
  MeasureView.lean            a measure word read as a measurement, as a widening of the concept
  Comparative.lean            *hotter than* as a relation between two uses, and what the words cannot decide
  NameCoordinate.lean         the coordinate that lifts the resolution ceiling, and its two bounds
  Denotation.lean             what a vocabulary decision can and cannot do to a repair
  Recipe.lean                 the recipe as an object: a domain description, and the path it forces
  Question.lean               a question's shape as an object: the matcher, and its round trip
  QuestionNested.lean         the list cut, the modifier frame, and a shape whose sides are shapes
  LLVQTable.lean              the class table under the quantiser: the least cost, and why the search may stop
overlay/                      the GLM repository, with the finished package
  GLM.py                      the CLI
  README.md                   the project's own top-level README
  glm_universal/              the package proper (eleven sub-packages)
  README_ARCHIVE.md           the archival half of that README: the change log
  glm_lean/                   the overlay's copy of the Lean development
```
