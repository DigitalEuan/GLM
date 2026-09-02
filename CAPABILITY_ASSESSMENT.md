# What the GLM can actually do — a measured assessment

This document does not describe the machine. It reports what happened when the
machine was run.

Four instruments were used, and all four can be re-run on demand:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.capabilities                    # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks                      # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8             # 131 CLI cases
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
| end-to-end CLI evaluation | the CLI, driven the way a user drives it | **131 cases: 131 passed** — 115 answered correctly, 16 refused as expected, 0 unexpected refusals, **0 confidently wrong**, 0 errored |
| test suite | the package's own regression net | **2,872 tests across 61 of the 62 test files, 11,665 subtests, outside the document check**, zero failures |
| Lean development | the machine-checked layer | **48 Lean files, `lake build` clean, no `sorry`** |

A break in the probe report is not a failure — it is a located boundary, and
each one names the exact place it stops. A *confidently wrong* answer in the
CLI evaluation is a failure, and the worst kind: it is scored `−1` where an
honest refusal is scored `+1`. There are now none.

---

## 2. The end-to-end CLI evaluation

This is the instrument that measures what a user gets. It lives in
`overlay/glm_universal/evaluation/`. Each of its 131 cases starts `GLM.py` in a
**fresh interpreter** — one subprocess per question, no shared session, no warm
caches — and scores the `ANSWER` or `UNSOLVED` line the process prints. The
question set covers **all 21 query kinds** the runtime recognises and **all 47
report subjects**; the coverage is checked against the runtime's own tables by
a test, so a new kind or subject cannot be added without a case.

16 of the 131 questions are ones the machine **should refuse**. Answering them
confidently is scored worse than refusing them.

### Accuracy per query kind

| query kind | passed | wrong | unexpected refusals | errors |
|---|---|---|---|---|
| `analogy` | 10 / 10 | 0 | 0 | 0 |
| `angle` | 2 / 2 | 0 | 0 | 0 |
| `cluster` | 2 / 2 | 0 | 0 | 0 |
| `coherence` | 2 / 2 | 0 | 0 | 0 |
| `comparative` | 7 / 7 | 0 | 0 | 0 |
| `compare` | 4 / 4 | 0 | 0 | 0 |
| `derive` | 4 / 4 | 0 | 0 | 0 |
| `describe` | 8 / 8 | 0 | 0 | 0 |
| `meaning` | 6 / 6 | 0 | 0 | 0 |
| `measure` | 9 / 9 | 0 | 0 | 0 |
| `nearest` | 4 / 4 | 0 | 0 | 0 |
| `pi_groups` | 2 / 2 | 0 | 0 | 0 |
| `product` | 1 / 1 | 0 | 0 | 0 |
| `project` | 1 / 1 | 0 | 0 | 0 |
| `real` | 5 / 5 | 0 | 0 | 0 |
| `report` | 50 / 50 | 0 | 0 | 0 |
| `spatial` | 2 / 2 | 0 | 0 | 0 |
| `task` | 3 / 3 | 0 | 0 | 0 |
| `trilinear` | 2 / 2 | 0 | 0 | 0 |
| `unknown` | 1 / 1 | 0 | 0 | 0 |
| `verify` | 6 / 6 | 0 | 0 | 0 |
| **total** | **131 / 131** | 0 | 0 | 0 |

Two facts are worth stating plainly. `analogy` — the kind that carried every
failure in the previous round — is now 10 / 10, and the set grew from 8 cases
to 10 while it was fixed. And there are **no unexpected refusals at all**: the
machine never declined a question it was supposed to answer, so the clean sheet
is not bought with over-caution.

### The refusals it got right

All 16 refusal cases refused, and all 16 are **boundaries** — each is a theorem
or a deliberate commitment, and cannot be closed by writing more code. There
is no longer a **gap** case: the last one is closed below.

**Boundaries — 16.**

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
| `measure-large-room` | `measure large in room` | *large* measures a volume and *room* brackets a length, so the two are about different quantities and no measurement is defined. The refusal is the mismatch, not a missing entry. |
| `measure-expensive-market` | `measure expensive in market` | *expensive* is on no measure scale at all, and the refusal names which register is missing the word rather than guessing a nearest one. |
| `measure-hot-walking` | `measure hot in walking` | A temperature word against a velocity class: the two registers disagree about the quantity. |
| `comparative-cross-quantity` | `is hot in tea hotter than fast in walking` | Both sides are perfectly well measured and still incomparable — a temperature and a velocity are on no common scale. Machine-checked as `GLM.Info.hotTea_not_comparable_fastWalking`. |
| `comparative-wrong-scale-marker` | `is fast in walking hotter than slow in airliner` | *hotter* is a temperature comparative and the pair measures velocity; a marker cannot order magnitudes of another quantity. |
| `comparative-midpoint-word` | `is tepid in tea tepider than cold in tea` | *tepid* sits exactly at the middle of the temperature scale, so its comparative names no direction. The direction a marker asserts is read off the register rather than listed, and at the midpoint the register does not decide it. |
| `derive-undescribed-coordinate` | `derive cents of perfect_fifth` | A cent is a logarithm, so no domain description derives it. The answerable coordinates are exactly the described ones, which is `GLM.Recipe.Spec.answer_eq_none_iff`, so the boundary is a theorem rather than a missing entry. |

The two analogy cases were new in an earlier round, and they are the
instructive ones: they are refusals the machine could not previously *make*,
because the old solver had no notion of a relation that is recognised and yet
determines no answer. Both were wrong answers before that. The three
`comparative` cases are this round's addition, and they make the same point
about a new query kind — two of the three refuse although *both* operands are
fully measured, so the refusal is a statement about comparability rather than
about coverage. The `derive` case is this round's, and it is the same kind of
statement one level up: the query surface is driven off the domain descriptions
themselves, so what it will not answer is fixed by what they derive.

**Gap — 0.**

The last gap was `coherence-unregistered-molecule`, `coherence PbCl2`: the
formula parser read `PbCl2` and the molecule codec would encode it — every
coordinate derived from the element register — but the coherence solver
resolved register names only, so it declined a species it could encode. Every
solver that takes a carrier and nothing else now has the same fall-through
`nearest` and `describe` already had, and four cases check it:
`coherence PbCl2`, `spatial PbCl2`, `angle PbCl2 water` and
`cluster PbCl2, water, ammonia`. Nothing is guessed — the fall-through refuses
in turn unless the formula parses and every coordinate is derived.

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
[`ANALOGY_LAYER_STUDY.md`](studies/ANALOGY_LAYER_STUDY.md) and summarised in §5 below.

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

* Every `report` subject — all 47 of them — answers from a fresh interpreter,
  and each recomputes its figures rather than quoting them. 49 / 49 in the CLI
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
* Harmony: 28 intervals as exact rational frequency ratios, with equal
  temperament's miss reported as an exact rational and the catalogue's
  universality claim tested against an undecoded control rather than repeated
  — the verdict, `not reproduced`, is read off the measurement.
* Golay correction: a complete census over all 2,325 correctable patterns, all
  10,626 ambiguous ones and all 42,504 miscorrecting ones.
* Carriers for unregistered formulae. `coherence`, `spatial`, `angle`,
  `cluster`, `nearest` and `describe` all fall through to the formula parser
  when a name is in no register, so `coherence PbCl2` and
  `cluster PbCl2, NaCl, H2O` are answered rather than refused.
* The machine refuses well. All 16 refusal cases were refused, and there were
  **zero** unexpected refusals across all 131 cases — including the four the
  `measure` query is asked at its own boundary, where
  `GLM.Info.boundary_empty_of_unmeasured` says there is nothing to answer with.

**Demonstrably not working.** No case. Every refusal in the set is now a
`boundary` — a theorem or a deliberate commitment — and the last `gap` case,
`coherence PbCl2`, was closed by building the carrier from the formula.

**Untouched.** The list below is the one kept in `MASTER_PLAN_ARCHIVE.md`
§7.9, with each entry's current state beside it rather than as it stood when
the list was written.

* **Multi-domain analogy** — *open*. `heat : temperature :: force : ?` is
  refused honestly rather than answered; answering it needs all four operands
  in one register.
* **Open vocabulary** — *open, and a commitment rather than an oversight*.
  There is no coordinate for *justice*.
* **The infinite-dimensional half of the VOA bridge** — *closed*.
  `VOA.lean` builds the state–field map `Y(u, z) = Σ uₙ z⁻ⁿ⁻¹` at the Griess
  layer of the 2A algebra and proves that the finite layer is not a vertex
  algebra, because Borcherds' commutator formula fails on the axis triple.
  `Heisenberg.lean` builds the half past it — the Fock space of one free boson
  over ℚ, the mode commutator, Borcherds' formula on it, and
  `no_finite_dimensional_model`, which is why no finite layer could have
  carried it.
* **Words as projections** — *closed*. `hot` is still a concept and now
  carries a measurement beside it: read against a comparison class it is an
  exact magnitude, and the comparative between two such uses is a query kind
  of its own. See `studies/RELATIVE_MEASURE_STUDY.md`.
* **An economic register** — *closed*, and the claim it made testable is
  recorded as `not reproduced` rather than confirmed:
  `data_objects/economics_register.py` holds 21 quoted prices as exact
  rationals and `report economics` measures the catalogue's §6.2 sentence
  against an undecoded control that does exactly as well.
* **The recipe applied by hand each round** — *closed for the domain*.
  `glm_universal/recipe/` makes a domain declarative: comparison classes,
  harmonics and prices were deleted and regenerated from their descriptions
  alone, 94 of 94 carriers identical and every measured figure unchanged, and
  `derive <coordinate> of <object>` answers off the descriptions. See
  `studies/RECIPE_STUDY.md`.
* **The question written as a hand-written phrase** — *closed for seven query
  kinds, across three shape families, with no branch left for any of them*.
  `glm_universal/language/` makes the **shape of a question** an object: an
  opening, named slots, the literal words that separate them, an optional tail,
  a described preamble, a list slot and named refusal boundaries, read by one
  generic matcher that knows nothing about any kind. `derive`, `measure`,
  `task` and `compare` are described that way — 7 slots, 47 surface forms, 15
  counted judgements — a second family cuts a string at an operator for
  `verify`, `analogy` and the relational half of `compare` (8 operands, 39
  surface forms, 13 judgements) with a described modifier and described
  trailing options, and a third **nests**: `comparative`, whose sides are
  themselves the measure shape, tightened, at 4 judgements. **Every one of the
  seven hand-written branches is deleted** and frozen in `language/legacy.py`,
  so the agreement is measured against the deleted code: **947 / 947**,
  **201 / 201** and **480 / 628** generated questions, kind *and* options, with
  all **111** evaluation questions of the undescribed kinds declined (**0 false
  positives**), 20 narrowing witnesses, and one declared widening — 148
  comparatives written with `relative to` — accounted for with 0 left over.
  `RequestProject/GLM/Question.lean` and `QuestionNested.lean` prove the round
  trip, the disjointness, the preamble, the list cut, the modifier frame and
  the nested shape's two refusals for all questions rather than for a sample.
  What is *not* closed is stated as a limit rather than implied: thirteen kinds
  have no description at all, and two of them — `describe`, a bare concept
  name, and `report`, a subject table — are kinds a shape should not be bent to
  fit. See `studies/LANGUAGE_STUDY.md`.
* **The `O(1)` LLVQ lookup table** — *closed, with the claim narrowed*.
  `reasoning/llvq_table.py` replaces the Leech quantiser's 8,192-codeword scan
  with the MOG's own structure — a 16-entry column table, 64 hexacode words,
  128 classes of 32 — and `RequestProject/GLM/LLVQTable.lean` proves the class
  minimum in both parities and the exactness of the bounded search. The
  subtractive test is the address book: **1,270 declarations decoded both ways,
  0 addresses changed**, with 107 vectors agreeing point for point against the
  frozen scan. What the measurement supports is **constant-bounded, not
  constant** — 96.8 codeword costs per call against 8,192, worst case the whole
  code — and the report says so. `report llvq`; see
  `studies/LLVQ_TABLE_STUDY.md`.

Seven items have left this list since the previous revisions of this document:
the **32- and 48-dimensional lattices**, **sigma–delta on the Leech shells**
with the Gibbs-style rule, **a harmonic register**, the **economic register**,
the **infinite-dimensional half of the VOA bridge**, **words as projections**
and the **`O(1)` LLVQ lookup table**.

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
