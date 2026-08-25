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

The package holds **6 registers** of carriers, reached through **18 query
kinds** one of which dispatches **25 report subjects**, and is checked by
**37 test files** alongside **27 Lean files**.

Every count in this repository's documentation is recomputed by
`overlay/glm_universal/figures.py` and written to
[`overlay/FIGURES.md`](overlay/FIGURES.md). Regenerate it with
`python -m glm_universal.figures --write` from `overlay/`;
`tests/test_figures.py` fails when a document and the code disagree, so no
figure below needs to be re-derived by hand. The shortest route to the
current state of the work is [`STATUS.md`](STATUS.md).

```bash
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q     # 37 test files
PYTHONPATH=. python3 GLM.py -q "report information loss" -c 1
PYTHONPATH=. python3 GLM.py -q "report infinite values"   -c 1
PYTHONPATH=. python3 GLM.py -q "report capabilities"      -c 1
PYTHONPATH=. python3 -m glm_universal.capabilities
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8
```

```bash
lake build          # RequestProject/GLM/*.lean, 27 Lean files, no sorry
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

The write-up is **[`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md)**.

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

The write-up is **[`INFINITE_VALUES_STUDY.md`](INFINITE_VALUES_STUDY.md)**. It
answers whether `cardinal_geometry_synthesis.md`,
[`DYNAMIC_CARRIER_STUDY.md`](DYNAMIC_CARRIER_STUDY.md) and
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

The write-up is **[`GEOMETRIC_AMBIGUITY_STUDY.md`](GEOMETRIC_AMBIGUITY_STUDY.md)**.
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

* **A new instrument, `glm_universal/evaluation/`.** **83 cases**, each
  starting `GLM.py` in a **fresh interpreter** — one subprocess per question,
  no shared session, no warm caches — covering **all 18 query kinds** and all
  **25 report subjects**, with the coverage checked against the runtime's own
  tables by a test. 10 of the questions are ones the machine *should* refuse.
* **Scoring is asymmetric.** A refusal tells the user where the machine stops
  and a confident wrong answer does not, so `correct` and `refused_as_expected`
  score `+1`, an unexpected refusal `0`, and a wrong answer or a crash `−1`.
* **The result: 83 of 83.** 73 answered correctly, 10 refused as expected,
  **zero** unexpected refusals, **zero** confidently wrong, 0 errored. Every
  kind is clean, `analogy` included at 10/10; the five analogy failures the
  first assessment recorded were closed by the model-selection layer described
  in [`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md).
* **Boundaries separated from gaps.** 9 of the 10 correct refusals are
  boundaries — undecidable equality of real processes, a vocabulary that is
  exactly the registers, a quotient by an exact zero — and **1** is a gap that
  more code would close: `nearest to PbCl2`, a formula the parser reads and the
  codec encodes but the nearest-neighbour search cannot look up, because that
  search resolves register names only.
* **The other two instruments, re-run:** 33 probes (20 hold, 13 break, 0
  errored, 0 surprises) and 2,389 of 2,390 benchmark tasks across 5 suites,
  every suite above its baseline.

The document ends by naming what is untouched — the infinite-dimensional half
of the VOA bridge, the `O(1)` LLVQ table, the Niemeier deep-hole census, multi-domain analogy, ranking
an unregistered formula, open vocabulary, words as projections, and the
exploratory delta–sigma directions — so nothing is implicitly claimed. The same
list is kept in `MASTER_PLAN.md` §7.9 and mirrored in
[`STATUS.md`](STATUS.md).

## Layout

```
README.md                     this file
MASTER_PLAN.md                the wiring status, phase by phase
INFORMATION_LOSS_STUDY.md     loss at the layer boundaries
INFINITE_VALUES_STUDY.md      infinite values and irrational numbers
GEOMETRIC_AMBIGUITY_STUDY.md  ambiguity, superposition and contextual collapse
ANALOGY_LAYER_STUDY.md        how A : B :: C : D was made to work, and what it still cannot do
CAPABILITY_ASSESSMENT.md      what the machine can do, measured rather than described
STATUS.md                     where the work stands now, and what is left
DYNAMIC_CARRIER_STUDY.md      the moving-carrier proposal these studies test
cardinal_geometry_synthesis.md, geometric_substrate_study.py
                              the supplied source material
RequestProject/GLM/           the Lean 4 development (27 Lean files, no sorry)
  Constants.lean              Y, Q, TAX, NRCI, coherence regimes
  TaxConservation.lean        the conservation law and its boundary
  Layers.lean                 the abstract theory of layers and boundaries
  Cumulative.lean             how a stack is made a refinement chain
  Tower.lean                  the unbounded dyadic tower: "this continues"
  Stack.lean                  the concrete substrate/integer/rational stack
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
overlay/                      the GLM repository, with the finished package
  GLM.py                      the CLI
  README.md                   the project's own top-level README
  glm_universal/              the package proper (nine sub-packages)
  glm_lean/                   the overlay's copy of the Lean development
```
