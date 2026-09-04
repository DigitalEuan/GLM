# Master plan: wiring status

> ### Positioning — read this before starting a round
>
> **We are not claiming that the lattice generates the universe.** The claim is
> narrower, and it is testable: there is an *exact* substrate — the Golay code,
> the Leech lattice and the arithmetic on them, integer and `Fraction` exact
> throughout (D7) — and reality maps onto it with unusual fidelity, measured
> against a control every time it is asserted.
>
> The **Geometric Language Machine** is the experimental implementation of that
> mapping. Can language, mathematics and program text be mapped onto the Leech
> lattice using the Golay code and the other systems built here? Can the GLM
> reason with what that mapping gives it? Can it be generative, and solve
> problems, and return results that are real, accurate and checkable?
>
> Some of what the substrate holds is hidden by the layer it is read at. Every
> carrier here is a **projection at a stated resolution** — the 24-bit word, the
> syndrome, the MOG cell, the Leech point, the shell — so a correspondence that
> is invisible at one layer can be exact one layer up. **Check a claim from
> several layers and resolutions before calling it absent.**
> [`studies/COMBINER_STUDY.md`](studies/COMBINER_STUDY.md) and
> [`studies/INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md)
> measure what each step down actually discards.
>
> The full note, with what follows from it in practice, is
> [`POSITIONING.md`](POSITIONING.md).

This document tracks the plan to fully wire the Geometric Language Machine,
eliminate the architectural simplifications, and implement multi-resolution
addressing. Each item says what was built, where it lives, and how to see it
recompute itself.

Everything below is reachable from the package's public API and from the query
runtime — **21 query kinds**, **51 report subjects** and **8 registers** — is
covered by the test suite (74 test files),
and — where it is a report or a task — has a generated column-3 script that
recomputes the claim in a **fresh interpreter** and fails if anything differs.

No count in this document is typed by hand twice: every one of them is
recomputed by `glm_universal/figures.py` into
[`overlay/FIGURES.md`](overlay/FIGURES.md), and
`tests/test_figures.py` fails if a document drifts from it.

```bash
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 GLM.py -q "report migration"          -c 1
PYTHONPATH=. python3 GLM.py -q "report leech construction" -c 1
PYTHONPATH=. python3 GLM.py -q "task grid"                 -c 1
PYTHONPATH=. python3 GLM.py -q "report infinite values"    -c 1
PYTHONPATH=. python3 GLM.py -q "report capabilities"       -c 1
PYTHONPATH=. python3 GLM.py -q "report superposition"      -c 1
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8
```

---

## The phases

Phases 1–13 are closed; each is recorded, as it was written, in
[`MASTER_PLAN_ARCHIVE.md`](MASTER_PLAN_ARCHIVE.md).

| phase | what it closed |
|---|---|
| 1 | core migration and substrate unification |
| 2 | algebra completion and simplification removal |
| 3 | the value layer, and the map of where the machine stops |
| 4 | meaning, not spelling |
| 5 | ambiguity as a value |
| 6 | measuring what the machine can actually do |
| 7 | closing what the evaluation found |
| 8 | the blueprint tested, and noise used as the computation |
| 9 | the external study catalogue, tested |
| 10 | the two companion preprints, and the last carrier gap |
| 11 | above 24 dimensions, addressing the Lean development, and the standing rules made into instruments |
| 12 | the sign-off ledger made sound, and every instrument in it |
| 13 | a harmonic register, and the third of a claim it makes testable |

The archive also holds three interstitial sections written between phases:
*Directive — multi-resolution Leech addressing*, *A task for the system* and
*Runtime surface added*.

Phases 14–27 below are closed. **Phase 28 is proposed and is where the next
round starts** — not a fourth shape family, but the two candidates the closed
rounds have left standing: the Niemeier deep holes classified from a trajectory
distribution, and the semantic half of the analogy. The third that used to
stand with them, a stability measurement under declared exact perturbation, was
closed by Phase 26. It is §3.4 of [`STATUS.md`](STATUS.md). Phase 27, closed
below, took neither candidate but the question underneath them: whether the
substrate can do work rather than hold a table — retrieval, and steering a
loop. Before it are the restoration and the archive's second reading (Phase
26), reading the supplied archive to the end (Phase 25), the `O(1)` LLVQ lookup
table (Phase 24) and the four undescribed parts of the described question kinds
(Phase 23).

---

## Phase 14 — the layer chain made a real refinement, and the repository tidied

**Status: closed.**

### 14.1 The organisation pass

The repository root held eleven study write-ups, the supplied source material
and the documents that describe the project, all mixed together. The study
write-ups now live in `studies/`, the supplied material — archives, PDFs, the
original brief — in `source_material/`, and only `README.md`, `STATUS.md`,
`MASTER_PLAN.md`, `CAPABILITY_ASSESSMENT.md`, `PROJECT_DIRECTIVES.md` and the
new index `DOCUMENTS.md` remain at the root. Every link that moved was
repointed, including the ones the Python modules and tests quote:
`reasoning/pipeline.py` and `reasoning/directives.py` now look for a document
in `studies/` and `source_material/` as well as at the root, and
`tests/test_lean_address.py` names `studies/LEAN_ADDRESS_STUDY.md`. Compiled
bytecode was removed from the index and ignored. Two over-long documents were
split at the `<!-- figures:history -->` marker into companions that keep the
archive as written: `overlay/README_ARCHIVE.md` and `MASTER_PLAN_ARCHIVE.md`.
No module name, package structure, query surface or Lean file changed.

*What recomputes it:* the whole suite, `python3 -m glm_universal.tools
pipeline` (21 of 21 rows complete) and `tests/test_figures.py`, which reads
only the current-state half of each split document.

### 14.2 The refinement chain, decided and closed

`INFORMATION_LOSS_STUDY.md` had carried an open audit finding for several
rounds: run against the shipped layer definitions rather than an idealisation
of them, `refinement_chain_intact` was `False`, because the substrate's 24-bit
parity view separates a unit on coordinate 10 from the vacuum while an integer
layer reading only the seven SI7 exponents conflates them.

Two fixes were possible — widen the integer layer's view, or narrow the
substrate's. The project's own account of a layer is a cumulative ascent in
which no step loses anything earlier, so **widening** is what it commits to;
narrowing would buy the invariant by making the machine less able. The
reasoning is recorded in the study (§3.1), not in a commit message.

Carried through: `dimension_layers.LAYER_INTEGER` is cumulative over the
substrate, the Griess view carries the carrier beside the algebra element, and
the rejected narrow reading is kept beside the stack as `LAYER_INTEGER_RAW`
with its cost still measured. `RequestProject/GLM/LayerChain.lean` states and
proves the chain on the real 24-coordinate carriers, with no `sorry`:
`GLM.Info.glmChain_refines_of_le` is `refinement_chain_intact` as a theorem,
`GLM.Info.glmSi7Layer_not_refines_glmSubstrateLayer` is the defect as a
theorem, and `GLM.Info.glmIntegerLayer_separates_unitOutside` is the exact
carrier pair that exposed it. `tests/test_information_loss.py` grew a
`TestTheClosedRefinementDefect` class that fails if any part of this regresses.

**Measured after the change** (`report information loss`, 7 carriers):

| Layer | resolves | loses | addition descends |
|---|---|---|---|
| substrate | 3 / 7 | 4 | no |
| integer | 5 / 7 | 2 | no |
| rational | 7 / 7 | 0 | yes |
| griess | 7 / 7 | 0 | yes |
| universal | 7 / 7 | 0 | yes |

| Boundary | pairs gained | is a refinement |
|---|---|---|
| substrate → integer | 8 | yes |
| integer → rational | 2 | yes |
| rational → griess | 0 | yes |
| griess → universal | 0 | yes |

`refinement_chain_intact : True`. The rejected reading, measured beside it:
`LAYER_INTEGER_RAW` resolves 4 / 7, loses 3, and violates refinement on the
two pairs `(0,4)` and `(1,4)`.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report information
loss" -c 1`, `tests/test_information_loss.py`, and `lake build`.

---

## Phase 15 — the layer chain audited at register scale

**Status: step 1 of five closed; steps 2–5 open.**

### 15.1 Seven carriers were not a measurement

Phase 14 closed the refinement chain on the seven carriers of `report
information loss`, and each of those seven was chosen *because* it exhibited a
boundary. A stack that refines on carriers picked to make it refine has not
been tested. [`studies/RELATIVE_MEASURE_PROPOSAL.md`](studies/RELATIVE_MEASURE_PROPOSAL.md)
§4 names running the audit on the registers themselves as the single
highest-value next step, and that is what `reasoning/escalation.py` does: one
carrier per named object of every register the package ships — physics 726,
chemistry 118, molecules 51, mathematics 22, harmonics 28, lexicon 95, **1,040
in all** — with nothing sampled.

The naive audit is quadratic in the carriers for resolution and quartic for
congruence, which at a thousand carriers is not affordable. It is not needed.
Every layer's measure here is a sum of non-negative exact terms that vanishes
exactly when a small reading of the two carriers agrees — parity bits at the
substrate, the SI7 exponents beside them at the integer layer, the exact
carrier at the three above. Grouping carriers by that **class key** replaces
both scans with one pass. The key is checked rather than trusted:
`key_agreement` re-derives every verdict from the layers' own `perceive` and
`measure` on an 18-carrier sample — 918 pairs, zero disagreements — and a test
deliberately breaks a key to confirm the check would notice.

### 15.2 What the registers said

| Layer | resolves (of 1,040) |
|---|---|
| substrate | 415 |
| integer | 544 |
| rational | 757 |
| griess | 757 |
| universal | 757 |
| *integer_raw (rejected reading)* | *359* |

| Boundary | pairs gained | is a refinement |
|---|---|---|
| substrate → integer | 5,883 | yes |
| integer → rational | 5,475 | yes |
| rational → griess | 0 | yes |
| griess → universal | 0 | yes |

**Zero refinement violations; `chain intact : True`** — the Phase 14 result
survives being asked a hundred and fifty times as many questions, and it was
not arranged to.

The scale-up also produced a result the seven carriers could not: a
**resolution ceiling**. 757 distinct carriers means **283 of the 1,040 named
entries share a carrier with another entry**, in **104 collision classes,
every one of them inside a single register** (275 physics, 8 mathematics); the
largest class is 78 dimensionless physics quantities (absorptance, albedo,
archimedes_number, …). No layer sees anything but the carrier, so no layer
separates them. What the machine is missing there is not resolution but a
coordinate for the name — which is what steps 2–5 of the proposal are about.
Addition still descends only to the three layers whose view is the carrier
itself, and the rejected `LAYER_INTEGER_RAW` reading, which cost one pair on
seven carriers, conflates **11,176** pairs the substrate already separates.

### 15.3 What holds however the registers grow

`RequestProject/GLM/Escalation.lean` proves the parts that are not
measurements, with no `sorry`: `GLM.Info.entryResolution_le_distinct` is the
ceiling (no layer resolves more entries than there are distinct carriers),
`GLM.Info.entryResolution_mono` is the order of the stack (a finer layer never
resolves fewer), `GLM.Info.glmRationalLayer_congruentOn` and its two
companions are addition descending on a lossless view, and
`GLM.Info.substrate_addition_not_congruent` is the half-unit witness for why
it does not descend below.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report escalation"
-c 1` (aliases: `report scale`, `report registers`, `report ceiling`),
`tests/test_escalation.py`, `lake build`, and the write-up
[`studies/ESCALATION_STUDY.md`](studies/ESCALATION_STUDY.md).

### 15.4 What it left open, and where that went

Steps 2–5 of `RELATIVE_MEASURE_PROPOSAL.md` were left open by this phase and
are closed in Phase 16 below.

---

## Phase 16 — measure words as relative measures

**Status: closed.**

Steps 2–5 of
[`studies/RELATIVE_MEASURE_PROPOSAL.md`](studies/RELATIVE_MEASURE_PROPOSAL.md),
of which Phase 15 was step 1. The write-up is
[`studies/RELATIVE_MEASURE_STUDY.md`](studies/RELATIVE_MEASURE_STUDY.md).

### 16.1 The comparison-class register (step 3)

`data_objects/comparison_classes.py`: **45 comparison classes over 11
quantities** (temperature 6, length 5, mass 5, velocity 5, volume 5, density 4,
illuminance 4, force 3, luminous intensity 3, pressure 3, frequency 2), each an
exact bracket `[low, high]` in the SI base unit of its quantity with a typical
magnitude inside it, and **11 measure scales carrying 64 degree words** at exact
positions in `[0, 1]`. (The register was closed at 33 classes over 8 quantities
and grown to these in Phase 18; the figures here are the current ones, as the
head of this document requires.) Nothing dimensional is typed twice: the unit,
the dimension and the ten EXT10 exponents of a class carrier are read out of
the physics register at load time, and a class naming a quantity the register
does not hold fails to load. `ComparisonClassCodec` round-trips all 45.
`lexicon_agreement()` checks the 12 words the scales share with the semantic
lexicon — quantity, polarity side and opposite-pole sum — and reports
`agrees: True`, with `heavy` flagged as the one word whose polarity is the
neutral `1/2`.

### 16.2 The widening, measured (step 4)

`reasoning/measure_view.py` reads a word against a class as an exact rational —
*hot* in tea is **363 K**, *hot* for a stellar surface **44 000 K** — and
audits three views over the **56 uses** the registers admit (each of 12 words
against each of the 32 classes of its quantity):

| view | resolves | refines the static reading |
|---|---|---|
| `static` — the concept carrier | 12 / 56 | — |
| `measure` — the concept and the measurement | **56 / 56** | **yes**, gaining 108 pairs, 0 violations |
| `measure_only` — the measurement alone | 56 / 56 | **not in general** — see §18.1 |

The static view is checked against `dimension_layers`' rational layer on the
concept carrier over all 1,540 pairs rather than idealised.
`RequestProject/GLM/MeasureView.lean` states the same on `Cumulative.lean`:
`GLM.Info.measureLayer_refines_staticLayer`, `GLM.Info.measureLayer_least`,
`GLM.Info.boundary_measureLayer_staticLayer` with
`GLM.Info.hot_tea_star_mem_boundary` for non-emptiness,
`GLM.Info.measureReading_not_refines_staticLayer` for the rejected
replacement, and `GLM.Info.magnitude_strictMono` for the scale order.

### 16.3 The `related_to` residue (step 2)

**27 of the 66 `related_to` triples** are converted by the physics register
alone — 6 `same_dimension_as` and 21 `differs_by`, each naming the basis
quantity that carries one dimension to the other — and the remaining **39**
are reported with the reason each was declined. An attribution that could be
made in more than one way is refused rather than guessed. (15 and 51 when the
phase closed, over a 13-quantity factor basis; `basis_sweep` then measured what
every other candidate would do and grew the basis to 16 — §18.2.)

### 16.4 The query, and its tested refusal (step 5)

`measure` is a query kind of its own: `measure hot in tea` (an exact
magnitude), `measure hot` (the same word against every class of its quantity)
and `measure 300 in tea` (the inverse reading). It **refuses** at the
boundary — `measure large in room`, `measure dark in room`,
`measure hot in walking`, `measure expensive in market` — and
`GLM.Info.boundary_empty_of_unmeasured` says the refusal is forced by the
registers rather than missing from the code. All four refusals are exercised,
as unit tests and as `boundary` cases in the end-to-end evaluation.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report measure" -c 1`
(aliases: `report measure words`, `report measure view`,
`report relative measure`, `report comparison classes`, `report scales`),
`tests/test_comparison_classes.py`, `tests/test_measure_words.py`,
`python3 -m glm_universal.evaluation --only measure`, and `lake build`.

### 16.5 What it left open

Two items, both closed in Phase 18: `large`, `small` and `dark` named
quantities — *size*, *light* — the physics register did not hold, so 3 of the 12
lexicon adjectives had no measurement; and there was no comparative query
(`hotter_than`, `as_hot_as`), although `GLM.Info.above_on_magnitude_lt` already
proved the scale order survives into magnitudes.

---

## Phase 17 — the last third of the universality claim, the address layer
## audited, and the infinite-dimensional half of the VOA bridge

**Status: closed.**

Three items that had each been named as untouched, and one gap found while
auditing.

### 17.1 An economic register (`report economics`)

`data_objects/economics_register.py` is the eighth register: **21 quoted
prices** as exact rationals — seven instruments over three consecutive
quarters, four sectors, six currency pairs — every price stored as a fraction
of integers in the shipped CSV and read as a `Fraction`, never as a float, and
every non-currency instrument naming a physical denominator.

The magnitude a price is read through is `⌊log_b x⌋` computed **without a
logarithm**: `k` is the unique integer with `b ^ k ≤ x < b ^ (k + 1)`, decided
for `x = p / q` by integer multiplication alone.
`RequestProject/GLM/LogBucket.lean` is the specification of that function —
`bucket_spec` and `bucket_unique` (hence `exists_unique_bucket`),
`le_iff_num_le` for the comparisons the code performs, `bucket_mono`,
`mantissa_mem_Ico`, `bucket_zpow` and `mantissa_zpow_eq_one` — together with
`distSq_smul` and `order_preserved_by_scaling`, which are what make the study's
control a single set of numbers rather than one per scale.

`reasoning/economics.py` (`report economics`) then measures the catalogue's
§6.2 sentence for markets. Decoded through buckets, mantissas, EXT10 exponents
and a currency flag, the lattice first separates **all 21 records at scale
1024**, orders them by magnitude at an exact tau of `39/70`, and **every
record's nearest neighbour is another quarter of the same instrument — 21 of
21 against a chance rate of `1/10`**. The verdict is nevertheless
**`not reproduced`**, because the undecoded control scores 21 of 21 as well:
what is measured is the price vector, not the geometry of the lattice. That is
the same answer the musical third reached by the same instrument, and the
agreement across two unrelated domains is itself the finding.

Section 6.2 of the catalogue ledger now reads **both** halves off their studies
at call time; neither is carried as `not implemented`. The write-up is
[`studies/ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md), and both the
economic and the harmonic registers are describable through the CLI, which
closed a pre-existing gap where the harmonic register could not be described
at all.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report economics" -c 1`
and `--verify-tct`, `tests/test_economics.py` (28 tests),
`python3 -m glm_universal.evaluation --only report`, and `lake build`.

### 17.2 The hexcolour address layer, audited (`report state migration`)

A hexcolour is the six-hex-digit rendering of a 24-bit carrier, one digit per
four coordinates: an address in the sense of directive D3 and nothing more.
The layer existed and was displayed; what it lacked was a measurement that it
does its job on the shipped data. `report state migration` now carries a sixth
step that supplies one: **4,680 concepts carry an address, all 4,680 distinct
(zero collisions), zero fail to read back to their own mask, zero disagree
with the mask stored beside them, zero fail to commute with the
legacy-to-core relabelling**, and the **15** legacy per-task addresses the
supplied ARC pipeline left behind are all Golay codewords and all round-trip.

The audit also found a real gap: nothing ever looked anything *up* by an
address, which is weaker than the word claims. The concept store now has
lookup by address, and every one of the 4,680 concepts is tested to round-trip
through it. One stale figure was annotated rather than deleted — the legacy
ARC-AGI results block says "66 hexcolour addresses" where the shipped table
holds 15, so it is kept as the upstream run's own count with a correction
beside it. The write-up is
[`studies/HEXCOLOUR_STUDY.md`](studies/HEXCOLOUR_STUDY.md).

*What recomputes it:*
`PYTHONPATH=. python3 GLM.py -q "report state migration" --verify-tct`
(`VERIFIED True`) and `tests/test_state_migration.py`.

### 17.3 The infinite-dimensional half of the VOA bridge

`VOA.lean` had proved what the finite Griess layer carries and, in
`borcherds_commutator_fails`, exactly where it stops. `Heisenberg.lean` builds
the half past it: the Fock space of one free boson over the exact rationals,
`V = MvPolynomial ℕ ℚ`, with creation, annihilation and mode operators, and
proves

* `mode_commutator` — `⁅aₘ, aₙ⁆ = m δ_{m+n,0} · id`, for all integers at once;
* `mode_truncated` — every state is annihilated by all sufficiently high
  modes, so the field is a genuine formal Laurent series;
* `borcherds_commutator` — the same bracket in Borcherds' own form, its tail
  vanishing by `alpha_mode_eq_zero_of_two_le`;
* `no_finite_dimensional_model` — the obstruction, in general: in
  characteristic zero no pair of endomorphisms of a nonzero
  finite-dimensional space satisfies `⁅A, B⁆ = c · id` with `c ≠ 0`, because
  the trace of a commutator is `0`; hence `fock_infinite_dimensional`, and
  `griess_layer_discards_nonzero_modes` names the discarded modes that do the
  damage.

That is the precise sense in which the finite layer cannot be the whole story:
stated and proved rather than asserted. The file is `sorry`-free and depends
only on the standard axioms.

*What recomputes it:* `lake build`.

### 17.4 What it left open

Nothing new. The remaining open items are the ones §3.2 and §3.3 of
[`STATUS.md`](STATUS.md) name: the `O(1)` LLVQ table, the Niemeier deep-hole
census, the two lexicon quantities the physics register does not hold and the
comparative query (both closed since, in Phase 18), open vocabulary as a stated
commitment, and the two ongoing residues (`related_to`, sparse chemistry).

---

## Phase 18 — the two items Phase 16 left open, and a factor basis measured
## instead of asserted

**Status: closed.**

Phase 16 closed with two open items — three lexicon adjectives naming
quantities the physics register did not hold, and no comparative query. Both
are closed here, and closing the first one exposed a third thing worth doing.

### 18.1 The register grown, and the replacement's cost kept measurable

`data_objects/comparison_classes.py` gained **volume**, **illuminance** and
**luminous intensity**: 33 classes over 8 quantities → **45 over 11**, 8 scales
carrying 47 degree words → **11 carrying 64**, and the lexicon overlap 9 words
→ **12**. All **12** of the lexicon's adjectives are now measurable, `large`,
`small` and `dark` among them, and the audit runs over **56 uses** instead of
45: the static reading resolves 12 of them, the widened reading all 56, gaining
**108 pairs** with **0** refinement violations.

That growth removed the shipped data's own refutation of the *replacement*
reading — keep the measurement, drop the concept — which used to fail on
exactly the three unmeasurable words. Rather than let the argument lapse into
an assertion, `replacement_witness()` re-runs the audit over the 56 uses plus
**one unmeasured use of each of the 12 words**, which is the case that arises
the moment a word's quantity is not in a register. Over those **68 uses** the
widening gains **164 pairs** with **0** violations and the replacement gains
the same 164 while **violating refinement on 66**. The general statement is a
theorem, not a measurement: `GLM.Info.measureReading_not_refines_staticLayer`.

### 18.2 The factor basis, swept rather than asserted

`measure_view.FACTOR_BASIS` carried a comment claiming that widening it
converts nothing and only adds ambiguity. `basis_sweep()` tests that claim by
offering **every** quantity the physics register holds as a candidate: of
**713**, **571** change nothing, **125** would make some attribution ambiguous
and are refused, and **17** strictly convert more. Those 17 occupy only **four
dimensions** — the ohm, its reciprocal the siemens, the joule per kelvin and
the radian per metre — and the first two decide the same triple, so the data
decides **three** factors. The basis is 13 → **16** (`resistance`, `entropy`,
`angular_wavenumber`), kept in a separate tuple so the sweep can put it back
and measure the growth rather than assert it, and the comment now states what
was measured. `related_to` conversion moves 15 → **27** of 66 (6
`same_dimension_as`, 21 `differs_by`), residue 51 → **39**, of which exactly
one is declined for having no single basis factor and the rest for an endpoint
that reaches no dimension at all. A dimension is what decides a triple; the
*name* is a choice, and the sweep reports the whole class of names beside each
so the choice stays visible.

### 18.3 The comparative (`hotter than`, `as hot as`)

A comparative is a relation between two **uses**, not between two words, which
is why the static reading cannot answer one and why Phase 16 left it out. It is
now a query kind of its own, `comparative`, recognised structurally in
`runtime/parser.py` — `is <word> in <class> hotter than <word> in <class>`, and
the equative `as <word> as` — with the direction read off the degree word's
position relative to the midpoint of its scale, and a word *at* the midpoint
refused rather than guessed at.

**Measured** by `comparative_audit()`: of the 56 uses, **228 pairs** are
comparable; within one class the word order decides **24 of 24**, and across
classes it gets **151 of 204** backwards — so the comparison class is what
decides the majority of comparable pairs. `is cold in stellar_surface hotter
than hot in tea` is **yes**, `8000 K` against `363 K`, with the two words in the
opposite order on the scale.

`RequestProject/GLM/Comparative.lean` proves the part that is not a
measurement: `hotterThan_trichotomy` (a strict order, trichotomous where
defined), `hotterThan_iff_position_lt` (within one class the word order decides
it exactly), `comparative_not_determined_by_word_order` (across classes it does
not), `comparative_not_static` (no widening-free reading can answer it),
`hotterThan_congr` (the widened view can), and
`not_comparable_left_of_unmeasured` with `hotTea_not_comparable_fastWalking`
(the two refusals are forced by the registers).

*What recomputes it:*
`PYTHONPATH=. python3 GLM.py -q "report measure" --verify-tct`,
`PYTHONPATH=. python3 GLM.py -q "is cold in stellar_surface hotter than hot in tea" -c 1`,
`tests/test_comparison_classes.py`, `tests/test_measure_words.py`,
`tests/test_comparative.py`, `python3 -m glm_universal.evaluation`, and
`lake build`.

### 18.4 What it leaves open

The measurable vocabulary is still a register: a thirteenth adjective naming a
twelfth quantity would be unmeasurable again, which is the case
`replacement_witness()` keeps measured. The comparative relates two uses of
degree words the register holds and nothing wider. Otherwise the open list is
unchanged — §3.2 and §3.3 of [`STATUS.md`](STATUS.md).

---

## Phase 19 — the residue finished as a vocabulary decision

**Status: closed.**

The first of the two items [`STATUS.md`](STATUS.md) §3.4 named. The write-up is
[`studies/DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md).

### 19.1 The search, exhausted before any word was decided

The residue was already split — 27 of the 66 `related_to` triples convert from
the physics register alone (6 `same_dimension_as`, 21 `differs_by`), and each
of the 39 that remain reports why. **38 of those 39 declined for the same
reason**: an endpoint reaches no dimension the register holds. Before deciding
any word by hand, `basis_sweep()` establishes that the automatic half is
finished: every one of the **713** quantities the register holds and the factor
basis did not is offered in turn, **571** change nothing, **125** would make an
attribution ambiguous and are refused, and the **17** that strictly convert
more occupy only **four dimensions**, two of which decide the same triple — so
the data decides three factors, and the basis stands at 16. What is left is a
vocabulary question, and the lexicon's own part of speech says so: of the 38,
**11 are verbs, 21 nouns and 6 absent from the lexicon**.

### 19.2 The register of decisions, and what the decisions changed

`data_objects/denotation.py` decides the residue's **36** undimensioned
endpoints one name at a time, each with its written justification, under six
verdicts: **1 `quantity`, 3 `ambiguous`, 4 `polymorphic`, 9 `carrier`, 11
`process`, 8 `abstraction`**. Only `quantity` makes a name dimensional, and it
supplies no coordinate — *gravity* is the register's own `gravitational_field`
under an ordinary-language spelling, exactly as an alias is, and
`denotation_audit()` refuses an entry that names a quantity the register does
not hold, shadows one that it does, or carries no justification (`sound:
True`).

`reasoning/denotation_view.py` is the second pass, and measures what the
decisions change:

| outcome | triples |
|---|---|
| converted to a dimensional relation | **0** |
| repaired to `names_process_of` | 6 |
| declined, now by what the endpoint *is* | 33 |

Zero conversions is the result rather than a disappointment: deciding what a
word denotes is not a way of manufacturing relations, and *gravity*'s own
triple still declines — now for the other reason, no single basis factor
between a gravitational field and a mass. Coverage is exact in both directions
(36 needed, 36 decided, **0 undecided, 0 idle**), and what is earned is
`closure`: **39 of 39 accounted for, 0 triples waiting on a lookup**. A
`carrier` beside a dimensioned endpoint is deliberately *not* repaired the way
a `process` is — a magnet bears a flux density and a photon does not bear an
illuminance — because a rule that is right half the time is a guess.

The conversions carry: of the **22** analogies the 27 repaired triples license,
**12** are answered and 10 refused, where the unrepaired control answers **1**.

`RequestProject/GLM/Denotation.lean` states the part that is not a measurement,
with no `sorry`: `reach_invents_nothing` (a decision cannot extend the
register), `secondPass_eq_firstPass_of_decided` (a decision never revises a
measurement), `secondPass_eq_firstPass_of_no_quantity_verdict` (the measured
`converted = 0`), `undecided_is_decided` (the closure claim) and
`repaired_not_converted` (the three outcomes partition the residue), with the
*gravity*, *motion* and *move* cases instantiated at the end.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report denotations"
-c 1` (aliases: `report denotation`, `report residue`, `report related_to`,
`report vocabulary`), `tests/test_denotation.py`, and `lake build`.

### 19.3 What it leaves open

The verdicts are judgements, and a lexicon that grows a new vague triple grows
a new one to make; the audit checks their form, never their content. The
second item §3.4 named — the recipe made into an object — is Phase 20 below.

---

## Phase 20 — the recipe made into an object

**Status: closed.**

The second of the two items [`STATUS.md`](STATUS.md) §3.4 named. The write-up
is [`studies/RECIPE_STUDY.md`](studies/RECIPE_STUDY.md).

Every capability in this plan was built by hand from one recipe: a **register**
of carriers whose coordinates derive from something already held; a **reading**
— a layer — over them; an **audit** of what the reading gains and whether it
gives anything up; a **query kind** that answers where the registers decide and
refuses where they do not; and a **machine-checked statement** of the part that
is not a measurement. Comparison classes (Phase 16), harmonics (Phase 13),
prices (Phase 17) and the comparative (Phase 18) are all that recipe, and each
application paid for its own carrier method, codec, audit, report subject and
parsing rule.

This phase makes the recipe's *input* an object, and is therefore
**subtractive**: what it produces is one declarative description of a domain
and a single generic path from such a description to everything the recipe used
to build by hand.

### 20.1 The description, and what it is written in

`recipe/spec.py` holds a `DomainSpec`: what the domain's objects hold, one
derivation rule per coordinate, which coordinates recover the object, the named
selections that make up the layer chain, and what must be refused. A
coordinate is either a **derivation** — one of **25 shared primitives**, which
compose, so `log_bucket(quotient("high", "low"), base=10)` is an ordinary
coordinate — or a **judgement** the domain has to state for itself, marked as
one so that it can be counted rather than hidden. Every value is an `int` or a
`Fraction`; no float is constructed anywhere on the path.

`recipe/descriptions.py` writes down three domains built by hand in earlier
rounds and nothing else — no carrier, no codec, no audit:

| domain | objects | coordinates | derivations | judgements | readings |
|---|---|---|---|---|---|
| comparison | 45 | 24 | 24 | 0 | `bracket` (2) → `measured` (9) → `full` (24) |
| harmonics | 28 | 24 | 18 | **6** | `ratio` (2) → `arithmetic` (14) → `full` (24) |
| economics | 21 | 24 | 24 | 0 | `price` (2) → `magnitude` (7) → `full` (24) |

**72 coordinates, 66 derivations, 6 judgements** — and the six are exactly the
musical conventions: Euler's gradus weighting a prime by `p − 1`, twelve-tone
equal temperament as the tuning a step is measured against, the error against
it, the harmonic and subharmonic readings of a power of two, and what counts as
a comma. That is the shape this plan predicted: what does not generalise is the
judgements, and a description makes them countable instead of invisible. Of
the 25 primitives, 23 are used — `held` by every domain, 7 by two or more, 16
by one, and `collection_size` and `minimum` by none, reported as unused rather
than deleted.

### 20.2 The one path, and the audit it runs

`recipe/build.py` knows nothing about any domain. From a description it
produces the carrier encoding (24 coordinates, each derived), the read-back,
the readings as layers in the sense of `Layers.lean`, the widening audit and
the query surface with its refusal boundary.

| domain | chain | classes | pairs gained | read-back | named refusals refused |
|---|---|---|---|---|---|
| comparison | refinement chain | 42 → 43 → 45 | 1, then 2 | 45 / 45 | 3 / 3 |
| harmonics | refinement chain | 28 → 28 → 28 | 0, then 0 | 28 / 28 | 3 / 3 |
| economics | refinement chain | 21 → 21 → 21 | 0, then 0 | 21 / 21 | 3 / 3 |

The comparison chain is the one that does work — the bracket alone conflates
`room_volume` with `household_lamp`, and two further pairs, `ship` against
`ocean_depth` among them, are split only by the full reading. The other two
gain nothing because their narrowest reading already separates every object,
which the audit *reports* rather than assumes.

### 20.3 The measured result — three domains regenerated

`build.regeneration` deletes each domain and rebuilds it from its description,
comparing the carriers against the shipped ones coordinate by coordinate, the
objects rebuilt through the read-back against the register's own, and the
figures the reasoning modules measure with the regenerated register installed
in the shipped one's place:

| | carriers identical | objects agree | figures unchanged |
|---|---|---|---|
| comparison | 45 / 45 | yes | 4 (+1 exhaustive) |
| harmonics | 28 / 28 | yes | 3 (+1 exhaustive) |
| economics | 21 / 21 | yes | 2 |
| **total** | **94 / 94** | **yes** | **9, and 11 with the exhaustive two** |

Verdict: `regenerated`, 3 of 3 domains, which is the test this phase set — not
that the path works on something new, but that domains built by hand can be
deleted and come back with their measured figures unchanged.

### 20.4 The query surface, and the part that is not a measurement

`derive <coordinate> of <object>` is the twenty-first query kind and is
answered off whichever description derives the coordinate, so a fourth
description costs no new parsing rule: `derive span_ratio of tea` is `373/293`
by the shared `quotient` primitive, `derive numerator of perfect_fifth` reaches
a second domain, `derive euler_gradus of perfect_fifth` is `4` and is reported
as a **judgement**, and `derive cents of perfect_fifth` is refused — a cent is
a logarithm, so no description derives it.

`RequestProject/GLM/Recipe.lean` states the path itself, with no `sorry`:
`readingOn_mono` (widening gives nothing up) with `readingOn_append_least` (it
adds nothing beyond keeping both), `boundary_readingOn_nonempty_iff` (what a
widening gains is exactly the pairs it splits), `lossless_full_of_keys` and
`rebuild_encode` (keys give a lossless carrier with an exact inverse),
`answer_eq_none_iff` (the refusal boundary, decidable and read off the
description) and `encode_congr` / `indist_congr` / `answer_congr` —
regeneration stated formally: two descriptions agreeing on the coordinates
agree on the carriers, on the reading and on every answer. `ratioSpec`
instantiates all of it on an interval as an exact ratio, where the Tenney
height alone is shown *not* to be a reading of the domain and `cents` is
refused.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report recipe" -c 1`
(aliases: `report recipes`, `report descriptions`), the four `derive` cases of
the CLI evaluation, `tests/test_recipe.py`, and `lake build`.

### 20.5 What it leaves open

Three domains are described, not eight: physics, chemistry, molecules,
mathematics and the lexicon are still hand-written, and nothing measured here
says they can be described. The judgements are counted, not removed — and
should not be. A description is trusted about its own facts, since `facts()`
reads the shipped register, so what is re-derivable is the coordinates rather
than the data. The limit this phase named for itself — the surface language
still being a hand-written phrase — is what Phase 21 below closed.

---

## Phase 21 — the surface language driven off the descriptions

**Status: closed.**

The remaining item of [`STATUS.md`](STATUS.md) §3.4, and the limit Phase 20 ran
into head-on. The write-up is
[`studies/LANGUAGE_STUDY.md`](studies/LANGUAGE_STUDY.md).

Phase 20 made the *domain* declarative: a description yields the carriers, the
readings, the audit, the query surface and the refusal boundary with no code of
its own. What it did not make declarative is the **way a question is asked**.
`derive <coordinate> of <object>` is generic in the coordinate and in the
object, but it was still one hand-written phrase in `runtime/parser.py`, and so
are `measure`, `comparative`, `meaning` and every `report <subject>` alias. A
new domain therefore arrived with its carriers, its readings and its refusals,
and then waited for a branch of the parser before anyone could ask it anything.

This phase writes the question down. Its input is a **question description**
beside the domain description; its output is one generic matcher from such a
description to a query kind and its options. Like Phase 20 it is
**subtractive** in intent and comparative in method: the shapes restate surface
the parser already accepts, and the measurement is whether the two agree.

### 21.1 The description, and what a shape is made of

`language/question.py` holds a `QuestionSpec`: the `kind` a match produces, a
`gloss`, a `shape` and the named `refusals`. A shape is an **opening**, then
named **slots** separated by literal **phrasings**, with an optional tail.

A `Phrasing` is a set of surface forms that count as the same thing here, held
longest-first so `derivation of` cannot be shadowed by `derive`, and it cannot
be constructed without a `why` — the sentence that justifies treating those
forms as one set. A `Slot` is a named hole with a role (`coordinate`, `object`,
`domain`, `subject`, `class`, `task`), a flag for whether it may be left out and
a flag for whether leading articles are kept; slots are named after the option
keys the runtime already uses, so a match becomes a query's options by a
dictionary comprehension rather than by a per-kind rule. That is what makes the
matcher generic rather than a switch with three arms.

A shape must **open with a phrasing**, at the head of the string, never on a
keyword found somewhere in the middle: `__post_init__` refuses a shape that does
not, one with a duplicate slot name, and one with no slot at all.

### 21.2 The three descriptions, and why not the other seventeen

`language/descriptions.py` holds them and nothing else — no matching, no kind
special-cased:

| kind | slots | openings | separators | judgements | boundaries |
|---|---|---|---|---|---|
| `derive` | coordinate, object, domain? | 5 | 3, then 1 | 3 | 3 |
| `measure` | subject, class? | 5 | 5 | 2 | 1 |
| `task` | task | 4 | — | 1 | 1 |

**6 slots, 44 surface forms, 6 judgements, 5 named boundaries, 14 openings.**
Each opening is exactly the set of forms `runtime/parser.VERBS` maps to that
kind and each separator exactly the set that branch of `parse_query` splits on,
so the descriptions restate the shipped surface rather than extending it —
which is what makes §21.3 a comparison rather than a demonstration.

Three of the runtime's twenty answerable kinds are *an opening then slots
separated by literal words*. The rest are not, and are left hand-written rather
than forced: `analogy` is an infix operator, `verify` a top-level `=`,
`comparative` a suffix whose two sides must each resolve to a measured use,
`compare` a keyword splitting the original string rather than a remainder, and
`describe` a bare concept name resolved in the register index. A description
language able to express those would be a parser generator; this one describes
one shape, and saying so makes **3 of 20** a measurement of that shape's reach
rather than an apology.

What does **not** generalise is counted, as in Phase 20: the six judgements are
the decisions about English — that the five `derive` openings are one opening,
that `of`, `for` and `on` all attach a coordinate to its object, that the domain
tail admits `in` and nothing else, that the five `measure` openings are one, the
five ways of naming what a measure word is read against, and `puzzle` counting
as `task`.

### 21.3 The measured result — agreement, and the false-positive half

`build.corpus()` generates a question for every opening crossed with every
separator over the coordinates, objects, measure words and tasks the registers
actually hold, and `build.agreement()` puts each to *both* parsers. Agreement
means the same kind **and** the same options.

| what is compared | result |
|---|---|
| generated questions, described matcher against `parse_query` | **692 / 692 agreed** |
| by kind | derive 360, measure 320, task 12 |
| declined by the matcher where the parser answered | **0** |
| answered with a different kind or different options | **0** |
| verdict | `exact` |

A matcher that answered everything would agree on that corpus and be useless,
so the other half is measured too. `build.other_kind_questions()` takes the
question string of every evaluation case whose kind is not described — 114 of
them across the seventeen undescribed kinds — and puts each to the matcher:

| what is measured | result |
|---|---|
| questions of undescribed kinds put to the matcher | 114 |
| matched anyway | **0 false positives** |

Every named boundary is given a witness, so a limit is reachable rather than
claimed (`derive`: `no_separator`, `empty_coordinate`, `empty_object`;
`measure`: `empty_subject`; `task`: `empty_task` — **5 of 5** reached, none
undescribed and none unreachable), and writing is checked to be inverse to
matching: `build.round_trip()` writes every question of the corpus back from
the slots it filled and re-matches it, **692 / 692 returning the same filling**.
The three shapes are a set rather than a priority list because
`build.openings_disjoint()` finds **0 clashes among the 14 openings**.

One caveat is stated rather than buried: the matcher requires its opening at the
**head** of the question, where the shipped parser will find a verb anywhere in
the token stream. That is a difference in surface reach, not in reading, and it
is the thing Phase 22 has to settle first.

### 21.4 The part that is not a measurement

`RequestProject/GLM/Question.lean` models the shape at the level of tokens —
`Phrasing`, `Slot`, `Piece`, `Spec` and `matchPieces`, the same five rules the
Python matcher runs — and proves what the audits above can only sample:
`matchPieces_rendered` (the round trip, for all questions rather than 692 of
them), `matchPieces_required_nonempty` (no silent empty slot, so a refusal is
the only way an unnamed thing leaves the matcher), `matchPieces_adjacent_holes`,
`matchPieces_no_separator` (the `no_separator` boundary as a theorem),
`matchPieces_lit_none` and `matchPieces_not_both` with
`Phrasing.not_both_matchAt` — disjoint openings decide the shape, which is what
makes the descriptions a set. `deriveShape` instantiates all of it on the
shipped `derive` description and four theorems are settled by `decide`. The
file carries no `sorry` and no non-standard axiom.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report language" -c 1`
(aliases: `report question shape`, `report surface language`), the
`report-language` case of the CLI evaluation, `tests/test_language.py`, and
`lake build`.

### 21.5 What it leaves open

Three kinds are described, not twenty, and nothing measured here says the other
seventeen can be described by *this* shape — for four of them the way they are
actually recognised shows they cannot. The shipped parser is still the one that
runs: the descriptions are measured *against* `parse_query`, not in place of it.
The judgements are counted, not removed. The opening must lead. And a
description is trusted about its own vocabulary, since the openings come from
`VERBS` and the separators from the branch they restate — so what is shown
describable is the *shape*, not the word list. The first two of those are
Phase 22, closed below.

---

## Phase 22 — the branches deleted, and a second shape family

**Status: closed.**

The two items of [`STATUS.md`](STATUS.md) §3.4 as it stood after Phase 21, both
settled.

### 22.1 The leading remainder, described rather than allowed

Phase 21 could not delete the branches because of one measured difference: the
described matcher wanted its opening at the **head** of the question, and the
shipped parser found its verb anywhere in the token stream, so
`please measure hot in tea` was answered there and declined here.

Phase 21 named the two honest ways out — describe the leading remainder, or
narrow the surface and record the narrowing. This phase does **both**, because
they turn out to be the same act done carefully. A `Preamble` is an ordered
list of word families that may be skipped before the opening, each a `Phrasing`
carrying its own justification:

```
(i would like to know | i want to know | can you | could you |
 would you | kindly | please)*      ← repeatable: the parser stripped these in a loop
(tell me about | what is | address | explain | profile)?
                                    ← once: the parser stripped one opener
```

`repeatable` reproduces the shipped behaviour exactly — a loop for the fillers,
one strip for the opener — and the *order* is part of the description, so
`what is please derive …` stops at `please` and is refused.

Letting the opening float free instead would have accepted anything before it,
and the hand-written parser demonstrably mis-read such questions.
`build.narrowing()` measures the trade with five stray openings the preamble
does not admit (`the tea`, `give me`, `run`, `in tea`, `what is please`)
written in front of a question of each shape:

| what is measured | result |
|---|---|
| stray openings × shapes | **15 witnesses** |
| declined by the descriptions, at `unrecognised_opening` | **15 / 15** |
| answered by the branches | **15 / 15** |
| …with the stray words coming back *inside an option* | **15 / 15** |

So the narrowing gives up exactly the questions the branch got wrong. The two
preamble pieces are two more judgements on every shape that uses them, which
takes the reported figure from **6 to 12**.

### 22.2 The branches, deleted

The three `if kind == "derive" / "measure" / "task"` blocks are gone from
`runtime/parser.py`, replaced by

```python
if kind in DESCRIBED_KINDS:
    return _described_query(kind, remainder, question)
```

`_described_query` matches the remainder against the shape, turns the filling
into the query's options, maps a boundary the description marks `raises` to a
`QueryError` and any other boundary to empty slots, and answers
`kind="unknown"` where the opening is not recognised. No per-kind code remains
in that path.

That creates a measurement problem, and it is solved rather than ignored: the
descriptions can no longer be measured against the parser, because for these
kinds the parser *is* the descriptions. The deleted code is kept verbatim in
`language/legacy.py` — imported by the measurement and by nothing in the
runtime — and the corpus is widened with fourteen admitted decorations so the
preamble is exercised too:

| what is compared | result |
|---|---|
| generated questions, descriptions against the **deleted branches** | **846 / 846 agreed** |
| by kind | derive 416, measure 362, task 68 |
| declined, or answered with a different kind or different options | **0, 0** |
| questions written back and re-matched | **846 / 846 return the same filling** |
| evaluation questions of the kinds the slot shapes do not cover | **114 put, 0 matched** |

The subtractive test Phase 22 set itself is met: the end-to-end evaluation
returns **130 / 130** with the same 16 expected boundary refusals and no gap.

### 22.3 Is a second shape worth having?

Phase 21's other item was deliberately falsifiable: *if two shapes cover seven
kinds, the description language is worth extending; if a second shape covers
one kind, it is a parser generator being written one kind at a time.*

The second shape covers **three** — `verify`, `analogy` and the relational half
of `compare`. `language/infix.py` describes an operator that cuts a *string*,
which is a genuinely second primitive rather than the first one rearranged: a
slot shape walks tokens, and an infix operand is a notation (`sqrt(2)`,
`mass * acceleration`), which is not a run of words.

| kind | shape | operands | judgements |
|---|---|---|---|
| `verify` | `(does it hold that \| is it true that \| audit \| check \| verify)? <lhs> = <rhs>` | lhs, rhs | 3 |
| `analogy` | `<a> : <b> :: <c> : <d>?` | a, b, c, d | 3 |
| `compare` | `(are \| do \| does \| is)? <left> (…seven relations…) <right>` | left, right | 3 |

Three things a slot shape cannot say are said here: an operator alternative may
carry a **meaning** (`bigger than` and `smaller than` are the same shape asking
opposite questions); an **inner** operator cuts each side again, which holds
the analogy's four terms in one description; and an operand may be **described
but not carried**, the analogy's fourth term being the hole the answer fills.

| what is compared | result |
|---|---|
| generated infix questions, descriptions against the shipped parser | **174 / 174 agreed** |
| by kind | verify 38, analogy 17, compare 119 |
| declined, or answered with different operands | **0, 0** |
| evaluation questions the infix shapes must not cut | **110 put, 0 matched** |

Two shapes cover six kinds, so the description language was worth extending.

### 22.4 The part that is not a measurement

`RequestProject/GLM/Question.lean` gains the preamble: `runPre_of_skipped`
(where the preamble consumes exactly the leading remainder, the shape sees the
bare question and answers it unchanged — skipping is a described act, not a
second parser), `runPre_refuses_undescribed` (where it consumes nothing the
opening must stand at the head, which is §22.1's fifteen witnesses as a
theorem), `skipPiece_once` and `skipPiece_twice` (a piece consumes exactly the
forms written, once or in a loop), and `skipMany_of_le` (the bound that keeps
the repeatable skip structural decides nothing: past the last match, more of it
changes nothing). Five further theorems settle the shipped preamble on the
shipped `derive` shape by `decide`. The file still carries no `sorry` and no
non-standard axiom.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report language"
--verify-tct`, the `report-language` case of the CLI evaluation,
`tests/test_language.py` (90 tests), and `lake build`.

### 22.5 What it leaves open

Six kinds are described and only three are *read* by the runtime. The infix
family is measured but not wired in, and the reason is named rather than
implied: four parts of the six described kinds still need a piece of
description language that does not exist — a **modifier** (`verify`'s semantics
qualifier), a **list** (`compare a and b`), described **trailing options**
(`analogy`'s subspace and limit), and a **nested** shape (`comparative`, an
operator between two measured uses). Those four are Phase 23.

---

## Phase 23 — the four undescribed parts, and the four branches they were blocking

**Status: closed.**

[`STATUS.md`](STATUS.md) §3.4 as it stood after Phase 22, written here as work
and now settled. The study is [`studies/LANGUAGE_STUDY.md`](studies/LANGUAGE_STUDY.md) §13.

Phase 22 left the infix family agreeing with a parser it had not replaced, and
named the reason as a list rather than a feeling: four parts of the six
described kinds needed a piece of description language that did not exist.
All four are now described, and the branches they were the obstacle to are
gone from `runtime/parser.py` and frozen beside the first three in
`language/legacy.py`.

| part | what it needed | branch deleted |
|---|---|---|
| `verify`: the semantics qualifier (`check tensor force = …`) | a **modifier** — a word that directs how the operands are read without naming one | the equation branch |
| `analogy`: the subspace and limit options | **trailing options** — a value written after the operands that narrows the answer | the analogy operator |
| `compare`: the list form (`compare a and b`) | a **list** — a hole whose filling is a sequence | both comparison branches |
| `comparative`: an operator between two *measured uses* | a **nested** shape — an operand that is itself a shape | the comparative |

### 23.1 The three that are not slots

A **list** is a hole that holds more than one value, and which words separate
the items is a decision about English exactly as a shape's separators are. A
`ListSlot` therefore carries its separator phrasing, a second **rank** tried
only when the first leaves too few items — `a or b and c` is two items, not
three, because `and` is cut first — the names its items fill, the minimum that
makes the question well formed, and the one admitted mark. It also keeps the
case of its items, because both sides go to the exact-real grammar unresolved
and `Pb` is an element where `pb` is nothing. That turned `compare` into a
**fourth slot shape**, which is the result this part was not expected to give:
the keyword form needed no new shape family at all.

A **modifier** is the third thing a shape can hold, being neither operand nor
operator. `check tensor force = mass * acceleration` asks the same question of
the same equation under a stricter reading, and the word has to come *out* of
the operands or the equation being audited would carry it. Where it may be
written and where it may be *removed* are two different questions: it is read
off the whole question wherever it stands, and removed only at the head and in
the trailing frame (`… under tensor semantics`). A `tensor` in the middle of
an equation stays exactly where it is.

A **trailing option** is a value written after the operands — the analogy's
subspace and its limit — read by the description rather than by the parser's
own option scanners.

### 23.2 The nested shape, and the price of reuse

`is cold in stellar_surface hotter than hot in tea` is infix, but its operands
are not text: each side has to be a *measured use*, which is the `measure`
shape itself. The nested description therefore holds an operator and **the
shape its sides nest**, tightened — the opening dropped, the class made
required, both slots narrowed to a single name. The last of those is what
keeps an exact-real comparison out of the shape, and it is a consequence rather
than a special case: `is sqrt(2) greater than 7/5` forms the operator and is
still refused, because `sqrt(2)` names no class.

The operator is **formed** rather than listed: any `-er than` word, or any word
inside `as … as`. Which degree words mean anything is the register's decision,
and enumerating them in the shape would put that decision in two places.

Reuse has a measured price, and it is the finding of the phase. A side of a
comparative is the measure shape, and the measure shape admits **five**
separators; the branch this replaces spelled its sides out with a regular
expression of its own, which listed four of them and not `relative to`. So
**148** corpus questions written with `relative to` on a side are read here and
were unknown to the branch. That is declared as a **widening** rather than
counted as agreement, and every widened question is accounted for by it with
**0 left over**. A side spelled out a second time is a side that drifts from
the shape it copies, and the two-word separator being the one that drifted is
the tell.

### 23.3 Measured the same way

| what is compared | result |
|---|---|
| slot corpus, descriptions against the frozen branches | **947 / 947 agreed**, 0 declined, 0 disagreed |
| by kind | derive 416, measure 362, compare 101, task 68 |
| infix corpus | **201 / 201 agreed**, 0 disagreed |
| nested corpus | **480 / 628 agreed**, **148 widened** (0 unexplained), 0 disagreed |
| round trips, slot shapes | **947 checked, 0 broken** |
| questions of undescribed kinds put to the shapes | 110, 110 and 123 put; **0 matched** |
| narrowing witnesses | **20 declined here, 20 misread by the branches** |
| boundary witnesses | 6 slot, 11 infix, 2 nested — every named boundary reached |
| judgements about English | **15** across 4 slot shapes, **13** across 3 infix, **4** across 1 nested |
| coverage | **7 of 20** answerable kinds, across **3** shape families, **all seven read off by the runtime** |
| verdict | `described` |

The subtractive test is met: the end-to-end evaluation returns **130 / 130**
with the same 16 expected boundary refusals and no gap, with `derive`,
`measure`, `task`, `compare`, `verify`, `analogy` and `comparative` all
answered off their descriptions and no branch left for any of them.

### 23.4 The part that is not a measurement

`RequestProject/GLM/QuestionNested.lean` carries the theorems: `ListCut.cut_two`
(the round trip for a list, with `sepAt_shorter` as the termination argument and
`cut_ne_nil`/`cut_append` as the two facts it rests on),
`ModifierFrame.strip_head`, `strip_frame` and `strip_middle` (the modifier is
removed exactly twice, and a word written inside an operand is returned
unchanged — the difference between a directive and a deletion),
`NestedSpec.run_rendered` (the round trip for a nested shape) and
`NestedSpec.run_no_operator` / `run_side_refused` (the two refusals, the second
being the boundary where the operator is formed and the question still
declined). `compareCut`, `tensorModifier` and `comparativeShape` instantiate
all of it on the shipped surfaces, decided by computation. The file carries no
`sorry` and no non-standard axiom.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report language"
--verify-tct`, the `report-language` case of the CLI evaluation,
`tests/test_language.py` (122 tests), and `lake build`.

### 23.5 What it leaves open

`build.UNDESCRIBED_PARTS` no longer lists a missing piece of description
language. What it lists now are **3 limits**, which is a different kind of
entry: thirteen kinds have no description at all; the described kinds fold the
case of their operands except where a description says otherwise; and a verb
*inside* an operand is not removed, because a described opening is read at the
head and a described closing at the tail and nowhere else.

Two of the thirteen are worth naming as *kinds a shape should not be bent to
fit*: `describe` is a bare concept name resolving in the register index, and
`report` is a subject table. A count of 20 with two descriptions bent to fit
would be a worse result than a count of 7 with the reason written down.

One smaller thing is left honest rather than fixed: a shape's judgement count
is the phrasings held in the shape plus the preamble's two, so the two
separator ranks a list slot carries are counted with the slot and not in the
15. Both `why`s are written and checked; only the arithmetic does not reach
them.

---

## Phase 24 — the quantiser's search, replaced by a lookup

**Status: closed.**

The first of the four candidates the described-surface rounds left standing,
and the oldest item on the supplied brief: *the `O(1)` LLVQ lookup table*. The
study is [`studies/LLVQ_TABLE_STUDY.md`](studies/LLVQ_TABLE_STUDY.md).

### 24.1 What was wrong with the old answer

The Leech quantiser is the hot path of every address, and it was a scan: for
each of the two congruence classes of Λ, form the cost of all 4,096 Golay
codewords and keep the cheapest — 8,192 codeword costs and 98,304 additions per
call, a constant of the code rather than of the input.

Two earlier rounds had reached the same wall from other sides.
`reasoning/fwht_decode.py` showed that the 4,096 coset costs are one
Walsh–Hadamard transform and measured that this is *not* a speed-up for this
code, because `n = 2k` makes the transform cost exactly what the direct
summation costs. Its constant-time tier, `certified_lookup`, is a genuine
`O(1)` route but a conditional one, and on the reliability profiles the Leech
step actually produces it fires on **0 of 200** sampled vectors. A tier that
never fires on the real input is not the table.

### 24.2 The table

Under the MOG alignment the package already carries, a 24-bit word is a 4 × 6
grid, and each column has three readings: its GF(4) label, its parity and its
top bit. Three facts, each checked over all **4,096** codewords with 0
failures: the six column labels form a **hexacode word**; the six column
parities are all equal to one bit `p`; the top row's parity is that same `p`.
The count is what turns three necessary conditions into a characterisation —
64 hexacode words × 2 parities = **128 classes** of **32** codewords, and
128 × 32 = 4,096 with nothing left over. Inside a column `(label, parity, top
bit)` determines the 4-bit pattern uniquely, so the lookup table is 16 entries,
and a class is six of them plus one parity constraint on the top bits. That is
the "first few binary digits" the brief asked for, made precise.

### 24.3 What is proved rather than measured

`RequestProject/GLM/LLVQTable.lean`, `sorry`-free and on the standard axioms:

| theorem | what it says |
|---|---|
| `cost_eq` | a choice costs the greedy choice plus the gaps of exactly the columns where the two differ |
| `isLeast_cost_of_parity_eq` | greedy parity right: the class minimum is `∑ lo`, attained by the greedy choice |
| `isLeast_cost_of_parity_ne` | greedy parity wrong: the class minimum is `∑ lo + gap i₀` at a least-gap column |
| `card_parity_class` | the choices of `n` top bits with a fixed parity number `2^(n−1)` — 32 at `n = 6` |
| `isLeast_of_bounded_search` | branch and bound is exact, which is why an unopened class holds nothing better |

Both minimum statements are `IsLeast`, so each carries the attainment and the
bound at once.

### 24.4 The subtractive test, and the claim narrowed

`reasoning/lean_address.py::quantise` decodes through the table now; the scan
is **not** deleted — it stays in `analogy.py` as the thing to agree with, which
is what makes the agreement a comparison rather than a tautology.

| figure | value |
|---|---|
| declarations decoded both ways | **1,270** |
| addresses unchanged | **1,270** — 0 changed |
| vectors compared point for point (sweep, register carriers, boundaries) | **107**, 0 mismatches |
| codeword costs per call, table route (40 deterministic vectors) | `484/5` = **96.8** against the scan's 8,192 |
| classes opened per call | `121/40` ≈ **3.03** of 256; worst call 448 words, 14 classes |

The agreement test earned its keep: the first version of the table route
disagreed with the scan on exactly one vector, the physics carrier
`bekenstein_hawking_entropy`, where two Leech points sit at the same squared
distance and the tie is broken by the `±4` repair — the scan picks by
`(penalty, coordinate index)` and the column-wise version was picking by
penalty alone. Both answers are nearest points; only one is the answer the
address book already contains.

What is **not** claimed is `O(1)`. The table work is fixed and the expansion is
data-dependent with a worst case of the whole code, so the module, the report
and the study all say the same thing: **constant-bounded, not constant**, with
the measured figure quoted and the worst case named. Quoting `O(1)` without the
measurement is what directive D6 exists to prevent.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report llvq"
--verify-tct`, `tests/test_llvq_table.py`, `corpus_report()` and
`search_cost_report(samples=40)` in `reasoning/llvq_table.py`, and `lake build
RequestProject.GLM.LLVQTable`.

---

## Phase 25 — the archive, read to the end

**Status: closed.**

The supplied archive `source_material/GLM-main.zip` had never been read all the
way down. Phases 1–24 took what the running system needed from it; this phase
went through the parts the brief named — `glm_machine`, the two `light/`
calibration rounds, `leech_lattice`, the two `data_object/` encoding attempts,
`FirstPrinciples`, `mog_cube_1`, `Projection`, `GMHGL`, the earlier `glm_lean`
iterations and `arc_agi_15` — and asked one question of each: **is there a
claim here that can be stated as a theorem and checked?**

### 25.1 What came back

**25 files of Lean, 7,170 lines, 848 declarations**, all building against the
pinned Mathlib with no `sorry` and all mirrored in `overlay/glm_lean/`. The
per-file account is
[`studies/RETRIEVED_LEAN_STUDY.md`](studies/RETRIEVED_LEAN_STUDY.md) §2; the
groups are the MOG cube (`Cube/`, five files: the surface identification, the
hexacode tiling, the stabiliser test, the price list and the three-cube
proposal), the lattice shortcut (`Shortcut/`, eight files: the Golay code, its
weight enumerator, a complete decoder, the Gray layer, the Leech step, the
corrected pipeline and two audits of the published directory), the three
generations of the paper's formal companion (`Foundations.lean`, `Gen2.lean`,
`Gen3.lean`), the electromagnetic calibration (`Calibration.lean`,
`AlignmentPoints.lean`), the first-principles sub-study (`FitCapacity.lean`,
`Packing.lean`, `Triad.lean`), the projection sub-study (`SeedLayers.lean`),
the graded cost model (`StepCost.lean`), spatial arithmetic
(`SpatialArithmetic.lean`) and the ARC-era reasoning loop
(`ReasoningLoop.lean`).

### 25.2 Nine of the twenty-five are negative results

That is the part of the retrieval that could not have been had by leaving the
material in the archive, because a refuted claim in a script is
indistinguishable from an unexamined one. The calibration chain returns the `c`
it was given; `3, 6, 9` is produced by any three-element set; what a binary
substrate forces is 23 and not 24; the three-cube rules give a `[24,12,4]`
code that no relabelling repairs; the published directory's "even
quantisation" is true by construction; the substrate's `snap_to_codeword` is
not a decoder; consecutive integers are never a "geodesic jump"; the electron
mass point's error is 0.0090–0.0093 % and not the quoted 0.007 %; and
`FitCapacity.lean` is the instrument that says how much a numerical agreement
could have been worth in the first place.

### 25.3 What it moved, and what it did not

The end-to-end evaluation returns the same **131 / 131** with the same 16
boundary refusals, and the benchmarks and probes are unmoved: the retrieval is
additive to what is *proved*, not to what is answered. The Lean corpus went
from 1,270 declarations across 48 files to **2,118 across 73**, so
`studies/LEAN_ADDRESS_STUDY.md` was re-measured against the code rather than
patched — and the separation signal rose, to 13.2 times chance on the file test
(from 12.3) and 15.0 on the citation test (from 9.6), on a corpus two thirds
larger.

*What recomputes it:* `lake build`, the sorry scan, the two-copy diff,
`tests/test_retrieved_lean.py` (which re-derives every line count and
declaration count the study states, and fails if a cited theorem is renamed),
`PYTHONPATH=. python3 -m glm_universal.tools lean-address` and
`PYTHONPATH=. python3 GLM.py -q "report lean" --verify-tct`.

---

## Phase 26 — the dropped work, restored, and the archive's second reading
## closed

**Status: closed.**

The tree handed over at the end of Phase 25 was missing part of what that phase
had produced: Lean files, their test files and several study documents had not
survived the handover. `dropped.zip` at the repository root is what came back,
and nothing in it was taken on trust — every Lean file was rebuilt against the
pinned Mathlib, every figure its tests pin was recomputed from the substrate,
and the two copies of the Lean tree were diffed.

### 26.1 Where the development stands

**95 files of Lean, 27,548 lines, 2,764 parsed declarations**, no `sorry`, both
copies byte-identical — against 73 files and 2,118 declarations at the close of
Phase 25. The suite was **72 files of tests** at the close of this phase; for
the project as it is now see [`overlay/FIGURES.md`](overlay/FIGURES.md).

### 26.2 The archive's second reading

Eight further results, written up in
[`studies/SOURCE_SALVAGE_SECOND_PASS.md`](studies/SOURCE_SALVAGE_SECOND_PASS.md):
the cube surface as the MOG grid, the read quantum as an operator, the Gray
jump norm, the ARC grid metrics as interval bounds (`GridTension.lean`), the
conditional lobe, the mode algebra, the free cube symmetries
(`Cube/Stabiliser.lean`) and the parity count that caps them at 24
(`Golay/CubeMirror.lean` — the one Lean file of this phase written new rather
than restored). The two questions the first reading left open are answered
**no** in
[`studies/ARCHIVE_DEEP_DIVE_STUDY.md`](studies/ARCHIVE_DEEP_DIVE_STUDY.md): the
archive's 44 balanced octads barely exceed what a null census of all 735,471
eight-subsets predicts, and are not even invariant under relabelling; and its
relaxation reaches the code but not the nearest codeword, so it is not a
decoder. [`studies/SOURCE_SALVAGE_AUDIT.md`](studies/SOURCE_SALVAGE_AUDIT.md)
is the first reading's own write-up, restored in the same way.

### 26.3 The stability measurement, which closes one Phase 27 candidate

`reasoning/stability.py` against `RequestProject/GLM/Stability.lean`: the two
certificates checked in exact rational arithmetic with no square root, the
sharp radius as the least distance to a bisector, and past it a perturbation
*built* rather than asserted. The addresses at radius zero are exactly the
nearest-point ties, and what breaking them by index costs is
[`studies/TIE_BREAK_STUDY.md`](studies/TIE_BREAK_STUDY.md).

### 26.4 The rules made checkable

`reasoning/exactness.py` and `tests/test_exactness.py` turn D7 and D9 into a
machine-checked inventory: every site in the package where a float could be
constructed, every cryptographic digest, and every XOR use is declared, and the
suite fails both when an undeclared site appears and when a declared one stops
existing. `tests/test_number_theory_evidence.py` does the same for
[`studies/GLM_Complete_Number_Theory_Evidence.md`](studies/GLM_Complete_Number_Theory_Evidence.md),
re-running the generators the paper names and comparing its tables and its
worked transcript cell by cell.

### 26.5 What moved in the runtime

`report searchloop` is the **49th report subject** and the evaluation's
**132nd** case; the end-to-end set was **132 / 132** with the same 16 boundary
refusals. The reasoning package went from 49 modules to **57**. The address
book was regenerated over the larger corpus and
[`studies/LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md) re-measured
rather than patched: **2,764 / 2,764 read back exactly, 0 coordinate errors**,
2,426 distinct addresses, nearest-by-address sharing a file **560 / 2,764**
against 37 for the digest control and 23 for the seeded reshuffle, with chance
at `8878/636411`. Phase 27 re-measured all of it again over the larger corpus.

---

## Phase 27 — the address book made to do work, and the first loop

**Status: closed.**

Two faculties the substrate had never been asked for, each measured against
controls and each answered in a way that constrains the claim rather than
flattering it.

### 27.1 Retrieval, against six controls

`reasoning/retrieval.py` turns the address book into an index and measures it
over **202** stride-selected queries of the **2,826**-declaration corpus, with
chance computed in closed form. A hit is a *relative* — same file, or joined by
a citation — and neither relation appears in any feature map, so "the
neighbours are relatives" is a prediction that can fail.

* The address is a real index: hit@5 **51.5 %** against **6.9 %** chance
  (**7.4×**), beating the digest (3.5 %), the seeded reshuffle (6.9 %), the
  random ranking (5.9 %) and name-substring search (34.2 %).
* And it is beaten decisively by plain text: Jaccard overlap of identifier
  tokens reaches **85.6 %** at **57.7 %** precision@5, against the address's
  15.5 %.
* The lattice is not what carries the signal: the same features with **no
  quantisation at all** score **51.0 %**, and a lexical address built from
  identifiers reaches **64.9 %** — better than the structural address, still
  twenty one points behind the text control. The limit is the projection to 24
  capped integers, not the choice of what to put in them.
* An address shortlist does not make the text search cheaper for free: 800
  candidates (28.3 % of the corpus) give 85.1 %, and 1.8 % of the corpus gives
  69.8 %.

### 27.2 What the geometry does earn: an exact guarantee

`RequestProject/GLM/Retrieval.lean` proves the completeness bound behind the
shortlist, and `filterRadius_eq_nil_certifies_absence` is why an empty
shortlist is a *proof* of absence. Measured: **144,075** pairs, **0**
violations; at feature radius 2 the guaranteed-complete shortlist is **70.9**
declarations — **2.5 %** of the corpus — containing all **16.8** feature-close
declarations on average.

### 27.3 The loop: propose, check, refuse

`reasoning/controller.py` builds a physical quantity out of the ten EXT10
generators one factor at a time — twenty moves, a stated tie-break order, the
state compared to the target exactly. Every plan any scorer returned was
re-verified end to end by `verifier.verify_expression_pair` through the digit
stack: **100 %**, under every scorer, by an instrument that did not build it.

Two refusals, and only one is a budget. `Controller.unreachable_of_invariant`
refuses **127 of the register's 726** quantities *with a proof* — an invariant
no move can change — with no node expanded; and `Controller.beam_can_miss` is a
kernel-decided witness that a width-one loop steered by an inexact heuristic
can miss a plan that exists, which is why a failed search is a refusal and
never an answer. `Controller.exists_descent` is the complement: steered by the
exact distance the loop never backtracks.

### 27.4 Can the substrate steer? Yes, and no better than the features

On the 24 reachable tasks the Leech-address scorer solves **18**, against **8**
for no guidance and **12** for a scorer that knows nothing about the target —
so the geometry does real work here, which is more than it managed in the
retrieval experiment. The same distance measured **without** the lattice solves
**17**, one behind and with a better minimality record; and decoded at the
register's own resolution (scale 1 rather than 9) the address scorer falls to
exactly the no-guidance **8**, proposal for proposal, which is what the
read-back bound of `Address.lean` predicts. Scoring by address costs about
twenty milliseconds a state against microseconds for counting exponents.

### 27.5 What moved in the runtime

`report retrieval` and `report controller` are the **50th** and **51st** report
subjects and the evaluation's 133rd and 134th cases; the end-to-end set is
**134 / 134** with the same 16 boundary refusals. Two Lean files
(`Retrieval.lean`, `Controller.lean`) and two test files
(`test_retrieval.py`, `test_controller.py`) came with them.

*What recomputes it:* `lake build`, the sorry scan, the two-copy diff,
`tests/test_retrieval.py`, `tests/test_controller.py`, and
`PYTHONPATH=. python3 GLM.py -q "report retrieval" --verify-tct` and
`"report controller" --verify-tct`, whose third column re-derives every figure
in a fresh interpreter. Write-ups:
[`studies/ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md) and
[`studies/CONTROLLER_STUDY.md`](studies/CONTROLLER_STUDY.md).

---

## Phase 28 — the two candidates that are left

**Status: proposed. This is where the next round starts.**

It is §3.4 of [`STATUS.md`](STATUS.md), which points back here. Phases 20–23
turned a domain, then a question, then the parts of a question into
descriptions, and the language layer has reached the point its own measurement
says it should stop at: the thirteen remaining kinds are not shapes, and
forcing them would make the coverage figure meaningless. So the next round is
**not** a fourth shape family; it is not the LLVQ table (Phase 24), the archive
retrieval (Phase 25) or the address layer made to work (Phase 27), all closed
above. Two candidates stand, in the order they are worth attempting:

1. **The Niemeier deep holes, found rather than tabulated.** The last purely
   geometric item on the list, and the brief's third experiment: whether the
   deep holes of a Niemeier lattice can be *classified from the distribution of
   trajectories* that reach them instead of read out of a table.
   `Golay/Census.lean` is the census for one lattice and
   `reasoning/deep_holes.py` walks to a hole; the classification is what is
   missing. The falsifiable form: if the distribution recovers the known census
   for one lattice it is a method, and if it recovers it for only that one it
   is a coincidence.
2. **`heat : temperature :: force : ?`** — the relation an analogy asserts,
   read off the registers rather than off the coordinates. The analogy shape is
   described now, so what is missing is the *semantic* half, and it is testable
   against the evaluation cases that already exist.
3. **A stability measurement under declared exact perturbation — closed by
   Phase 26.** Every figure in the project is exact by directive D7, and the
   question that had never been asked was how far an address moves when its
   input is perturbed by a declared exact amount. `reasoning/stability.py` and
   `Stability.lean` answer it, and the nearest-point ties they expose are
   [`studies/TIE_BREAK_STUDY.md`](studies/TIE_BREAK_STUDY.md).

Whichever is taken, the discipline is that of Phases 20–24: the thing must be
*described* or *measured* rather than asserted, what does not generalise must
be counted rather than hidden, the old path must be frozen so the new one has
something to agree with, and the end-to-end evaluation must return the same
answers and the same refusals.

---

<!-- figures:history -->

*The closed phases that used to follow live in
[`MASTER_PLAN_ARCHIVE.md`](MASTER_PLAN_ARCHIVE.md), unchanged.  The counts in
them were true when each phase was closed and are deliberately left alone; for
the project as it is now, see [`overlay/FIGURES.md`](overlay/FIGURES.md), which
is regenerated from the code.*
