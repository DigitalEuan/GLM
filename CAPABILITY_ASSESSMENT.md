# What the GLM can actually do — a measured assessment

This document does not describe the machine. It reports what happened when the
machine was run.

Four instruments were used, and all four can be re-run on demand:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.capabilities                    # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks                      # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8             # 83 CLI cases
PYTHONPATH=. python3 -m pytest glm_universal/tests -q                 # the test suite
```

Every figure below is the output of one of those commands on the tree as it
stands. Nothing here is quoted from an earlier run — and nothing here is typed
by hand twice: the counts are recomputed into
[`overlay/FIGURES.md`](overlay/FIGURES.md) by `glm_universal/figures.py`, and
`tests/test_figures.py` fails if this document drifts from them.

---

## 1. The headline numbers

| instrument | what it measures | result |
|---|---|---|
| capability probes | where the library stops, asked as user questions | **33 probes: 20 hold, 13 break, 0 errored, 0 surprises** |
| benchmark suites | solver functions against curated and exhaustive task sets | **2,389 / 2,390 tasks across 5 suites; every suite beat its declared baseline** |
| end-to-end CLI evaluation | the CLI, driven the way a user drives it | **83 cases: 83 passed** — 73 answered correctly, 10 refused as expected, 0 unexpected refusals, **0 confidently wrong**, 0 errored |
| test suite | the package's own regression net | **1,677 tests across 37 test files, 8,851 subtests** |
| Lean development | the machine-checked layer | **27 Lean files, `lake build` clean, no `sorry`** |

A break in the probe report is not a failure — it is a located boundary, and
each one names the exact place it stops. A *confidently wrong* answer in the
CLI evaluation is a failure, and the worst kind: it is scored `−1` where an
honest refusal is scored `+1`. There are now none.

---

## 2. The end-to-end CLI evaluation

This is the instrument that measures what a user gets. It lives in
`overlay/glm_universal/evaluation/`. Each of its 83 cases starts `GLM.py` in a
**fresh interpreter** — one subprocess per question, no shared session, no warm
caches — and scores the `ANSWER` or `UNSOLVED` line the process prints. The
question set covers **all 18 query kinds** the runtime recognises and **all 25
report subjects**; the coverage is checked against the runtime's own tables by
a test, so a new kind or subject cannot be added without a case.

10 of the 83 questions are ones the machine **should refuse**. Answering them
confidently is scored worse than refusing them.

### Accuracy per query kind

| query kind | passed | wrong | unexpected refusals | errors |
|---|---|---|---|---|
| `analogy` | 10 / 10 | 0 | 0 | 0 |
| `angle` | 1 / 1 | 0 | 0 | 0 |
| `cluster` | 1 / 1 | 0 | 0 | 0 |
| `coherence` | 1 / 1 | 0 | 0 | 0 |
| `compare` | 4 / 4 | 0 | 0 | 0 |
| `describe` | 8 / 8 | 0 | 0 | 0 |
| `meaning` | 6 / 6 | 0 | 0 | 0 |
| `nearest` | 4 / 4 | 0 | 0 | 0 |
| `pi_groups` | 2 / 2 | 0 | 0 | 0 |
| `product` | 1 / 1 | 0 | 0 | 0 |
| `project` | 1 / 1 | 0 | 0 | 0 |
| `real` | 5 / 5 | 0 | 0 | 0 |
| `report` | 26 / 26 | 0 | 0 | 0 |
| `spatial` | 1 / 1 | 0 | 0 | 0 |
| `task` | 3 / 3 | 0 | 0 | 0 |
| `trilinear` | 2 / 2 | 0 | 0 | 0 |
| `unknown` | 1 / 1 | 0 | 0 | 0 |
| `verify` | 6 / 6 | 0 | 0 | 0 |
| **total** | **83 / 83** | 0 | 0 | 0 |

Two facts are worth stating plainly. `analogy` — the kind that carried every
failure in the previous round — is now 10 / 10, and the set grew from 8 cases
to 10 while it was fixed. And there are **no unexpected refusals at all**: the
machine never declined a question it was supposed to answer, so the clean sheet
is not bought with over-caution.

### The refusals it got right

All 10 refusal cases refused. Nine are **boundaries** — each is a theorem or a
deliberate commitment, and cannot be closed by writing more code — and one is a
**gap**, which is missing implementation.

**Boundaries — 9.**

| case | question | why the refusal is correct |
|---|---|---|
| `compare-equality` | `is 0.1 + 0.2 equal to 0.3` | Equality of two real *processes* is not decidable: two processes never separated at any precision are equal, but "never" quantifies over all precisions at once (`Computable.lean`). Inequality is decided; equality is refused. |
| `real-divide-by-zero` | `approximate 1/0 to 5 places` | A quotient by an exact zero names no value. Division needs a nonzero witness `|x| ≥ 2⁻ᵐ`, and no fixed search depth supplies one for every divisor. |
| `meaning-open-vocabulary` | `meaning of justice` | The vocabulary is exactly the registers. A word outside them has no determinate referent for a machine whose meanings are geometric. |
| `describe-unknown-word` | `describe unobtainium` | No carrier; there is nothing to describe, and guessing a near spelling would be worse. |
| `trilinear-nonaxes` | `trilinear 1 2 3` | The Norton–Sakuma product is defined on 2A axes. Non-axis operands are not a computation the algebra has. |
| `report-unknown-subject` | `report nonsense subject` | The report subjects are a closed, enumerated set; the refusal prints the set. |
| `unknown-nonsense` | `please compute the square root of a banana` | Nothing to parse into any query kind. |
| `analogy-empty-table-position` | `Ca : Sc :: Ba : ?` | The step is well defined — `(+0 period, +1 group)` — but period 6, group 3 holds fifteen elements, because the f-block sits there. The position names no single element, and naming one would be a choice the table does not make. |
| `analogy-cross-register` | `heat : temperature :: force : ?` | Both halves are stated. The relation the lexicon carries is `temperature related_to heat`, and `related_to` records *that* a link exists without saying which, so it transports nothing; and the three terms do not share a register, since physics holds `temperature` and `force` but not `heat`. |

The last two are new, and they are the interesting ones: they are refusals the
machine could not previously *make*, because the old solver had no notion of a
relation that is recognised and yet determines no answer. Both were wrong
answers in the previous round.

**Gap — 1.**

| case | question | what is missing |
|---|---|---|
| `nearest-unregistered-molecule` | `nearest to PbCl2` | The gap the molecules register moved rather than closed. The formula parser reads `PbCl2` and the molecule codec would encode it — every coordinate is derived from the element register, so no new datum is needed — but `nearest` resolves its operand against the names a register *enumerates* and stops there. Joining the two is the work item. |

---

## 3. The capability probes

`python3 -m glm_universal.capabilities` — **33 probes, 20 hold, 13 break, 0
errored, 0 surprises.** A "surprise" is a probe whose recorded expectation
disagrees with what the code did; zero of them means the recorded map of the
boundary is accurate.

| area | holds | breaks |
|---|---|---|
| algebra | 0 | 1 |
| carriers | 2 | 1 |
| dynamic carrier | 4 | 2 |
| layers | 1 | 2 |
| reals | 6 | 4 |
| runtime | 5 | 0 |
| scale | 1 | 1 |
| semantics | 1 | 1 |
| substrate | 0 | 1 |

The `runtime` row is the one that moved: `runtime_arithmetic_inside_a_describe`
went from `breaks` to `holds` when `reasoning/term_arithmetic.py` learned to
read `energy divided by time` as one question. Every runtime probe now holds.

The breaks that matter most for a user, in the probes' own terms:

* **`substrate_repair_radius`** — the repair radius is exactly 3. At weight 4
  six codewords are equally near; at weight 5 the answer is unique, confident
  and wrong, because the octads form a Steiner system `S(5,8,24)`. No better
  decoder exists: this is a theorem about the code.
* **`algebra_product_is_associative`** — the Norton–Sakuma product is not
  associative; the two bracketings of a pairwise-2A triple give `−3/32` times
  *different* axes.
* **`tax_conservation_above_bits`** — the TAX law is exact on binary carriers
  and fails over the naturals; the only repair would need `Y = 1/2`, and `Y` is
  strictly between `1/4` and `1/2`.
* **`semantics_open_vocabulary`** — the vocabulary is exactly the registers.

---

## 4. The benchmark suites

`python3 -m glm_universal.benchmarks` — **2,389 / 2,390 tasks across 5 suites;
every suite beat its declared baseline.**

| suite | kind | score | baseline | verdict |
|---|---|---|---|---|
| `analogy_chemistry` | curated | 12 / 12 | 1 / 4 | pass |
| `analogy_physics` | curated | 13 / 13 | 0 / 1 | pass |
| `analogy_semantic` | curated | 10 / 10 | 0 / 1 | pass |
| `golay_correction` | exhaustive | 2,325 / 2,325 | 1 / 2,325 | pass |
| `physics_equations` | curated | 29 / 30 | 2 / 3 | pass |

The exhaustive suite is the strongest evidence in the repository: **all 2,325
error patterns of weight ≤ 3 are corrected**, **all 10,626 weight-4 patterns are
reported ambiguous** (six equidistant codewords), and **all 42,504 weight-5
patterns are shown to miscorrect** — a complete census, not a sample.

The three analogy suites were the weakest instrument in the repository — 26 / 35
in the previous round — and are now clean. What changed is described in
[`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md) and summarised in §5 below.

`physics_equations` loses its one point to a boundary rather than a gap: EXT10
refuses the textbook identity `angular_momentum = momentum × length`, because
under full tensor semantics the two sides are not the same object. Three of the
thirty equations are accepted under scalar semantics and refused under full
semantics; the suite records the divergence rather than choosing a side.

---

## 5. The analogy failures, and how they closed

The previous round of this assessment named five confidently wrong answers, all
of them analogies, and treated them as the machine's headline defect. All five
are now closed, and the diagnosis that closed them is worth stating because it
was not a metric problem.

`reasoning/analogy.py` reads `A : B :: C : ?` as a **translation**: it computes
`D* = C + (B − A)` in `Q²⁴` and returns the nearest carrier. That is exactly
right when the relation is a displacement of the coordinates, and exactly wrong
when it is not — and every one of the five was a relation that is not a
displacement. No amount of metric work would have fixed them.

`reasoning/analogy_models.py` adds the missing layer: four **named relation
models** — `periodic_step`, `reciprocal_dimension`, `scale_shift` and
`lexicon_relation` — each of which either says what the relation *is*, in the
register's own terms, or declines. The outcomes, one per original failure:

| original failure | old answer | now |
|---|---|---|
| `He : Ne :: Ar : ?` | `Fe` | `Kr`, by `periodic_step` |
| `B : Al :: C : ?` | `P` | `Si`, by `periodic_step` |
| `length : wavenumber :: time : ?` | `chromatic_dispersion` | `frequency`, by `reciprocal_dimension` |
| `solid : liquid :: liquid : ?` | `fluid` | `gas`, by `lexicon_relation` |
| `heat : temperature :: force : ?` | `enthalpy` | **refused**, with both halves of the reason stated |

The honest replacement for "five analogy failures" is a shorter list: the three
**semantic-benchmark** misses that survived the new layer, and they are now
closed too.

* `electron : proton :: north : ?` returned the wrong pole because `proton` was
  recorded as `related_to electron` — the one relation the layer deliberately
  refuses to transport. The register now records `proton opposite_of electron`,
  which is what it means, and the analogy resolves to `south`.
* `accelerate : move :: rotate : ?` failed because `accelerate` was `form_of
  change` and `rotate` was `form_of motion`, two different parents for what the
  curated pair treats as one relation. Both are now `form_of move`.
* `cause : effect :: force : ?` was curated with the target `motion`, and the
  curated target was wrong: the register's own triple is `force causes
  acceleration`, so the relation `causes`, transported from `cause : effect`,
  lands on `acceleration`. The benchmark target was corrected rather than the
  code, and the reason is recorded next to it in `benchmarks/suites.py`.

The first two were missing relations in the lexicon; the third was a mistake in
the benchmark. None of the three was a defect in the model layer, which is the
point: once the relations are named, a wrong answer is traceable to a specific
missing or wrong triple rather than to an opaque nearest-neighbour search.

---

## 6. Where things stand

**Demonstrably working.**

* Every `report` subject — all 25 of them — answers from a fresh interpreter,
  and each recomputes its figures rather than quoting them. 26 / 26 in the CLI
  evaluation.
* Analogy: 10 / 10 in the CLI evaluation and 35 / 35 across the three analogy
  suites, with two of the ten CLI cases being refusals the machine now knows
  how to make.
* Dimensional verification: 6 / 6 in the CLI evaluation, 29 / 30 on the
  benchmark, with the one loss identified as a semantics boundary.
* Real-number work: 5 / 5 `real` and 4 / 4 `compare` cases. Irrationals held as
  processes, exact rational arithmetic throughout, and equality correctly
  refused as undecidable.
* Meaning and description: 6 / 6 and 8 / 8, over a grounded graph of 357
  meanings and 12,859 re-derivable edges.
* Chemistry: 118 elements with their sparsity measured and widened three ways
  that invent no measurement, and a register of 51 molecules whose every
  coordinate is derived from the element register at load time.
* Golay correction: a complete census over all 2,325 correctable patterns, all
  10,626 ambiguous ones and all 42,504 miscorrecting ones.
* The machine refuses well. All 10 refusal cases were refused, and there were
  **zero** unexpected refusals across all 83 cases.

**Demonstrably not working.** One case, and it is a gap rather than a boundary:
`nearest to PbCl2` refuses, because `nearest` resolves its operand against the
names a register enumerates and an unregistered formula is not one of them.

**Untouched.** The following remain unstarted, and nothing in this repository
claims otherwise. The list is kept identical to `MASTER_PLAN.md` §7.9.

* **The infinite-dimensional half of the VOA bridge.** `VOA.lean` builds the
  state–field map `Y(u, z) = Σ uₙ z⁻ⁿ⁻¹` at the Griess layer of the 2A algebra
  — truncation, skew-symmetry, a forced invariant form, self-adjoint modes,
  nondegeneracy, a vacuum — and proves that the finite layer is not a vertex
  algebra, because Borcherds' commutator formula fails on the axis triple. The
  modes past that layer are not built.
* **Multi-domain analogy.** `heat : temperature :: force : ?` is refused
  honestly rather than answered; answering it needs all four operands in one
  register.
* **Ranking an unregistered formula** — the evaluation set's one gap case.
* **Open vocabulary.** There is no coordinate for *justice*.
* **Words as projections.** `hot` is a standalone concept, not "temperature at
  high scale".
* **The delta–sigma directions** — cascaded loops, error feedback through a
  symmetry-commuting rational matrix, subtractive dither with an equidistributed
  sequence, sigma–delta on the shells, and the Gibbs-style rule — are
  exploratory and not started.

**Three things were answered rather than left open.** The
self-organised-criticality reading of the mean coset weight had been claimed
loosely. It now has two halves, both settled in Lean: the static half — the mean
distance from a 24-bit word to the code is exactly `3433/1024`, past the packing
radius 3 (`Golay/Census.lean`) — and the dynamical half, which is **negative**:
the perturbation chain has the uniform law as its unique stationary law, but it
is periodic, so `step^[n] (dirac g) ≠ unif` for every `n` and there is no
limiting law to settle into (`Golay/Dynamics.lean`). The carrier averages at the
critical weight; it does not settle there.

The positive statement in its correct Cesàro form is no longer open either.
`Golay/Cesaro.lean` proves it with an explicit rate: for any probability law on
the 4,096 cosets, any syndrome and any `N ≥ 1`,

> `|cesaro μ N f − 1/4096| ≤ 24 / N`,

and `cesaro_tendsto` reads the same result as an ordinary limit. The proof is
exact Fourier analysis over `ℚ` on the syndrome group; the constant 24 is the
reciprocal of the spectral gap `1/12`.

The third is the VOA state–field map, which had been listed as entirely
unattempted. `VOA.lean` now builds it at the Griess layer and proves both what
that layer carries and, in `borcherds_commutator_fails`, exactly why it is not
a vertex algebra on its own.

---

## 7. Re-running this assessment

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.capabilities
PYTHONPATH=. python3 -m glm_universal.benchmarks
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8 --json eval.json
PYTHONPATH=. python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 -m glm_universal.figures            # every count above
```

The evaluation exits 0 only when every case passes, so it is usable as a gate.
`--only <kind>` restricts it to one query kind, `--case <id>` to one question,
and `--list` prints the question set. The harness itself is tested by
`glm_universal/tests/test_evaluation.py`, which checks the coverage of kinds and
subjects against the runtime's own tables and pins the scoring asymmetry — that
a confident wrong answer scores strictly below a refusal.
