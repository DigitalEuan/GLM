# Status


## Tier 0 — the coarse read

**Question.** Where does the work stand now, what is open, and how is it re-verified?

**Verdict.** This is the current state: what is done, what is open, and how to re-verify it.

**Deciding figure.** Every instrument in the table at the head of the document reports its own result on demand.

**Recomputed by.** `glm_universal.signoff.ledger.suite_totals`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

> **Positioning.** Before starting a round, read the Positioning section of
> [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md): what is claimed, what is
> not, and why an absence at one layer is not a refutation. It is stated once,
> there, and every document in this repository is written under it.

## How to work in this repository

**Commit and push after each completed step, not once at the end.** A step is
anything that leaves the tree in a working state — one document reconciled,
one test added, one lemma proved. Never leave a session's work sitting
uncommitted: a commit is cheap, and an interrupted session that has been
committing as it goes hands over something that runs. The same rule is at the
head of [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) and is directive D1.

---

*The current state: what is done now, what is open, and how to check any of it
without recomputing anything by hand. The record of earlier rounds is in
[`MASTER_PLAN.md`](MASTER_PLAN.md); how to run a round is
[`ITERATE.md`](ITERATE.md).*

**Starting a new round? Read [`ITERATE.md`](ITERATE.md), then §3.4, "Named for
the next round", before anything else.** The round just closed is
**maintenance**, and says so: under directive **D15** it moved none of
derivation, addressing or refusal. It picked the tree up unclosed — four
generated artefacts stale and only 21 of 98 test units still signed, because
the round before it had written its prose after its release — refreshed the
generated layer and re-ran what that made stale. The release that followed
passed every test file and failed on the evaluation, for a reason worth
having: `report lean` had grown to about 203 seconds and crossed the harness's
300-second ceiling. It was fixed by arithmetic rather than by a longer
ceiling. The separation study behind that query ran two loops over the pairs
of 3,383 declarations; the all-pairs means are now a closed form — Lagrange's
identity, exact and integer — and the nearest-neighbour search is pruned by
two exact lower bounds over the 3,002 distinct addresses. The query answers in
**77 seconds** and every published figure is identical, which is checked by
new cases that compare both routines with brute force rather than with their
previous output. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phases 21–48 are the
record; Phase 48 is this round, and §7 of
[`studies/LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md) is the
measurement.

Last reconciled against a full re-run on 2026-09-19.

Every count below is produced by `overlay/glm_universal/figures.py` and written
to [`overlay/FIGURES.md`](overlay/FIGURES.md);
`overlay/glm_universal/tests/test_figures.py` fails if this document and the
code disagree. If a number here looks wrong, regenerate rather than edit:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.figures --write
```

---

## 1. Where the work stands, in one table

| instrument | command | result |
|---|---|---|
| test suite | `python3 -m pytest glm_universal/tests -q` | **<!--figure:suite-->3,924 tests across 97 of the 98 test files, 15,326 subtests, outside the document check<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **<!--figure:evaluation-case-count-->157<!--/figure--> / <!--figure:evaluation-case-count-->157<!--/figure-->** — 138 answered, 19 refused as expected (all `boundary`, no `gap`), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites, every suite above its baseline |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 errored, 0 surprises |
| Lean development | `lake build` (repository root) | <!--figure:lean-files-->119 Lean files<!--/figure-->, **0 `sorry`** |
| figures | `python3 -m glm_universal.figures --write` | regenerates `overlay/FIGURES.md`; every documented count |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the archive partition, the coverage claim of `ENTRY.md`, every generated block and every derived cache — **current**, no drift |
| construction ladder | `python3 -m glm_universal.tools ladder` | **462 / 568** queries named correctly with **0** wrong on the eleven-rung ladder, against **327** for the note's five rungs and **283** for the best single rung |
| norm-family ladder | `python3 -m glm_universal.tools normladder` | the repaired **<!--figure:normesc-rungs-->10<!--/figure-->**-rung norm ladder names **<!--figure:normesc-correct-->467<!--/figure-->** of **<!--figure:normesc-queries-->568<!--/figure-->** correctly with **<!--figure:normesc-wrong-->0<!--/figure-->** wrong; the full **<!--figure:normesc-family-rungs-->12<!--/figure-->**-rung family it repairs answers **<!--figure:normesc-family-wrong-->1<!--/figure-->** wrongly and is **not safe** |
| escalated operations | `python3 -m glm_universal.tools operations` | **<!--figure:opesc-count-->7<!--/figure-->** operations other than retrieval measured against substrate-removed controls; every one gains, and **one of them — program text — answers <!--figure:opesc-program-wrong-->13<!--/figure--> queries wrongly and is reported unsafe** |
| second reading | `python3 -m glm_universal.tools second-reading` | **<!--figure:secondread-adopted-->1<!--/figure-->** of **<!--figure:secondread-configurations-->6<!--/figure-->** declared guard configurations is adopted — `<!--figure:secondread-shipped-->strict+margin<!--/figure-->` takes the program-text operation to **<!--figure:secondread-program-correct-->366<!--/figure-->** correct and **<!--figure:secondread-program-wrong-->0<!--/figure-->** wrong, giving up **<!--figure:secondread-given-up-->150<!--/figure-->** answers where matched refusal removes **<!--figure:secondread-matched-removes-->2<!--/figure-->** of the thirteen |
| field surface | `python3 -m glm_universal.tools fieldsurface` | the surface answers **<!--figure:fieldsurface-moved-->9<!--/figure-->** of the **<!--figure:fieldsurface-held-->10<!--/figure-->** questions the oracle found held and unreachable — exactly the **<!--figure:fieldsurface-predicted-->9<!--/figure-->** declared reachable before the run — taking the probe from **<!--figure:fieldsurface-parsed-before-->6<!--/figure-->** parsed to **<!--figure:fieldsurface-parsed-after-->15<!--/figure-->**; it is `table`, not reasoning |
| blockers probe | `python3 -m glm_universal.tools blockers` | the pre-registered language probe scores **<!--figure:probe-correct-->2<!--/figure-->** correct, **<!--figure:probe-wrong-->1<!--/figure-->** wrong, **<!--figure:probe-refused-->17<!--/figure-->** refused of **<!--figure:probe-questions-->20<!--/figure-->** — **below the declared pass mark of <!--figure:probe-pass-mark-->10<!--/figure-->**, a declared failure |

The test-suite row is the sign-off ledger's own count, recorded by
`python3 -m glm_universal.signoff --release`, which runs each test file in its
own process with the `exhaustive` tests selected. One `pytest` process over the
same tree, with `GLM_EXHAUSTIVE=1` so that nothing is deselected, collects
**3,952 tests** — which is the ledger's 3,924 plus the 28 tests of the document
check the ledger's total leaves out, because a round that adds a document or a
figure fails that check until the documents are reconciled. Without that switch the `exhaustive`
tests — which certify rather than sample — are reported as skipped with their
reason rather than dropped silently, which is why the ledger's own count is
taken from a run that selects them.

The package is `glm_universal` **v1.18.0**: eleven sub-packages, 137 modules,
**8 registers** holding 1,089 carriers (physics 726, chemistry 118, molecules
51, mathematics 22, lexicon 95, spatial 28, harmonics 28, economics 21) beside
a 45-class comparison register, **<!--figure:query-kinds-->22 query kinds<!--/figure-->**
one of which dispatches **65 report subjects**, and 3 tasks.

---
## 2. What the system is now

This section is the **standing description**: what the machine is made of
today, with the thing that recomputes each part named beside it. It is
deliberately short. What each round *did* — the argument, the controls and the
negative results — is the record, and the record is in
[`MASTER_PLAN.md`](MASTER_PLAN.md) under *The delivered record*, phase by
phase, with the study for each finding in `studies/`.

**Substrate and algebra.** Complete syndrome decoding with no silent tie-break;
the full Leech lattice in place of Construction A (kissing number 196,560); the
exact 2A Sakuma product in place of the XOR shortcut; the six-facet orthogonal
decomposition with the lattice index that says what a facet reading loses; the
`LEGACY_TO_CORE` frame bridge, verified an isometry. The quantiser decodes
through the LLVQ class table rather than by scanning the code, on integers
scaled by a common denominator, which is exact and is what makes a whole-corpus
measurement affordable. Write-up:
[`LLVQ_TABLE_STUDY.md`](studies/LLVQ_TABLE_STUDY.md).

**The ladders it reads at.** The construction ladder — `Z²⁴`, `D₂₄`,
Construction `A`, `B` and `C`, all generated from their conditions, and the
scalings that fill the gap between them — is eleven rungs, and an escalated
reading over it names **462** of 568 declared queries correctly with **0**
wrong against **283** for the best single rung. Indexed instead by minimum
squared norm it becomes a family of
**<!--figure:normfamily-rung-count-->25<!--/figure-->** rungs over
**<!--figure:normfamily-norms-->12<!--/figure-->** norms with no power of two
missing; the full family is **not safe** — it answers
**<!--figure:normesc-family-wrong-->1<!--/figure-->** query wrongly — and the
repaired **<!--figure:normesc-rungs-->10<!--/figure-->**-rung ladder names
**<!--figure:normesc-correct-->467<!--/figure-->** of
**<!--figure:normesc-queries-->568<!--/figure-->** with
**<!--figure:normesc-wrong-->0<!--/figure-->** wrong. The containments are
proved in `RequestProject/GLM/NormFamily.lean`. Write-ups:
[`CONSTRUCTION_LADDER_STUDY.md`](studies/CONSTRUCTION_LADDER_STUDY.md),
[`NORM_FAMILY_STUDY.md`](studies/NORM_FAMILY_STUDY.md).

**Escalation, and the second reading that makes one operation safe.**
**<!--figure:opesc-count-->7<!--/figure-->** operations other than retrieval
are measured under the same discipline against substrate-removed controls;
every one gains, and one of them — program text — used to answer
**<!--figure:opesc-program-wrong-->13<!--/figure-->** queries wrongly. A second
reading at another layer removes all thirteen:
`<!--figure:secondread-shipped-->strict+margin<!--/figure-->`, the
**<!--figure:secondread-adopted-->1<!--/figure-->** of
**<!--figure:secondread-configurations-->6<!--/figure-->** declared
configurations that meets all four pre-registered marks, answers
**<!--figure:secondread-program-correct-->366<!--/figure-->** correctly and
**<!--figure:secondread-program-wrong-->0<!--/figure-->** wrongly, giving up
**<!--figure:secondread-given-up-->150<!--/figure-->** answers where matched
refusal removes only **<!--figure:secondread-matched-removes-->2<!--/figure-->**
of the thirteen. What the guards promise rather than score is proved in
`RequestProject/GLM/SecondReading.lean`. Write-ups:
[`OPERATION_ESCALATION_STUDY.md`](studies/OPERATION_ESCALATION_STUDY.md),
[`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md).

**What blocks fuller reasoning, measured rather than asserted.** The
pre-registered language probe — **<!--figure:probe-questions-->20<!--/figure-->**
questions, pass mark **<!--figure:probe-pass-mark-->10<!--/figure-->** — scores
**<!--figure:probe-correct-->2<!--/figure-->** correct,
**<!--figure:probe-wrong-->1<!--/figure-->** wrong,
**<!--figure:probe-refused-->17<!--/figure-->** refused: a declared failure,
kept as one. Widening the lexicon to
**<!--figure:probe-lexicon-held-->57<!--/figure-->** of the probe's
**<!--figure:probe-lexicon-words-->69<!--/figure-->** content words moved the
score by nothing, so the binding blocker is the absence of a parser from open
language to a query kind, and only
**<!--figure:probe-derived-->2<!--/figure-->** measured results are derivation
rather than lookup or addressing. Write-up:
[`BLOCKERS_STUDY.md`](studies/BLOCKERS_STUDY.md).

**Registers.** Eight of them. Physics (726 quantities, EXT10 exponents and
unit strings cross-checked against each other), chemistry (118 elements),
molecules (51 species and ions, every coordinate derived from the element
register at load time), mathematics, lexicon (95 concepts, 380 explicit
relation triples), spatial, harmonics (28 musical intervals as exact rational
frequency ratios) and economics (21 quoted prices as exact rationals), beside
a 45-class comparison register.

**Reasoning.** 80 modules. Analogy by named relation, dimensional
verification, Buckingham-Pi from an exact rational nullspace, the
Walsh–Hadamard transform decoder, the deep-hole walk, term arithmetic, unit
parsing with the steradian priced rather than silently redefined, and
element-coverage widening that labels every widened cell by provenance.

**Values.** Reals held as processes with no float anywhere; written arithmetic
over them including `exp`, `log`, `sin`, `cos`, `tan` and real powers; decided
inequality and refused equality; the delta–sigma modulator with its proved
`1/N` rate and, in 24 coordinates, the separating functional that proves a
target outside the hull unreachable.

**Meaning.** The grounded graph — 357 meanings, 1,705 notations, 12,859 edges,
every one re-derived on demand. The inherited ARC-era concept graph was
audited and demoted to evidence, and `tests/test_inherited_graph.py` enforces
that by walking the imports of every module that answers a question.

**Measurement.** Three instruments that do not trust each other: probes
(library boundaries), benchmarks (solver functions) and the end-to-end
evaluation (the CLI in a fresh interpreter per question, scored asymmetrically
so a confident wrong answer is worse than a refusal). Write-up:
[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md).

**The Lean development, addressed.** `reasoning/lean_address.py` gives each of
the 3383 declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly 3383/3383 with 0 coordinate errors;
2982 distinct addresses, and the quantiser adds no conflation of its own;
nearest-by-address shares a file 669 times against 33 for a SHA-256 control and
27 for a seeded reshuffle, with chance at ≈ 1.10 %. `report lean`.
Write-up: [`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md).

**The register where the address is the only reader.** In the anonymous
register a query's identifiers are not the corpus's, by theorem
(`GLM.Anonymous.overlap_anonymise_eq_zero`): over 842 queries the text search
falls 718 → 73 and the identifier address book 414 → 44 against 48 by chance,
where the structural address holds 238 → 168. Write-up:
[`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md).

**The standing rules, as instruments.**
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) states <!--figure:directives-->16 standing rules<!--/figure--> and
names the instrument for each. `reasoning/directives.py` parses that file and
gives each instrument a live verdict (`report directives`) — **16 of 16** with
every named instrument present; `reasoning/pipeline.py` reads the stage each
piece of work has reached off the tree rather than from prose — **30 of 30
rows** through all six stages (`report pipeline`); `glm_universal/signoff/`
computes a module's dependency closure with `ast` and plans a run against
recorded digests, so nothing unchanged is checked twice (§4.1); and
`glm_universal/integrity.py` holds every SHA-256 use one module above the six
core sub-packages, which the purity audit enforces. `glm_universal/tools.py`
is their command line, kept out of the core for the same reason.

**What a refusal is evidence of.** `reasoning/probe_oracle.py` translates each
of the twenty pre-registered probe questions into the query grammar by hand
and classifies it: `parsed` when a query already answers it at a declared
field, `surface` when a register row or a shipped function holds the answer
and no query kind returns it, `absent` when nothing holds it. The split is
<!--figure:oracle-parsed-->6<!--/figure--> /
<!--figure:oracle-surface-->10<!--/figure--> /
<!--figure:oracle-absent-->4<!--/figure--> of
<!--figure:oracle-questions-->20<!--/figure-->. It keeps no measurement cache
— a live session answers twenty queries in seconds — and
`GLM.ProbeOracle.counts_partition` is why the three counts read the same
twenty questions rather than three samples. `tools oracle`. Write-up:
[`PROBE_ORACLE_STUDY.md`](studies/PROBE_ORACLE_STUDY.md).

**The field surface, and what it was worth.** `runtime/fields.py` answers one
named field of one named row — `field atomic_weight_u of carbon` — over
<!--figure:fieldsurface-tables-->13<!--/figure--> declared tables holding
<!--figure:fieldsurface-rows-->8,408<!--/figure--> rows and
<!--figure:fieldsurface-pairs-->50,516<!--/figure--> addressable `(row,
field)` pairs: the element and molecule source rows, one table per register's
carrier attributes, the Lean address book, the package's own top-level
definitions, and a registry of declared zero-argument functions whose returned
mapping is addressable by key. Its second shape, `fields of <row>`, names the
fields a row answers to. It refuses at three boundaries — an unknown row, an
unknown field of a known row, and a field the register records as missing —
and it says of itself, in every answer, that it is `table`: it derives
nothing. Measured against the oracle's prediction it answers
<!--figure:fieldsurface-moved-->9<!--/figure--> of the
<!--figure:fieldsurface-held-->10<!--/figure--> held-and-unreachable
questions, which is exactly the <!--figure:fieldsurface-predicted-->9<!--/figure-->
declared reachable before the run, taking the probe from
<!--figure:fieldsurface-parsed-before-->6<!--/figure--> parsed to
<!--figure:fieldsurface-parsed-after-->15<!--/figure-->; the tenth is a
comparison across two rows and needs an operation rather than a surface.
`GLM.FieldSurface` proves the boundary is the tables' rather than a search's.
`tools fieldsurface`. Write-up:
[`FIELD_SURFACE_STUDY.md`](studies/FIELD_SURFACE_STUDY.md).

**The round loop itself, measured and cut.** A named `.lean` file resolves to
itself rather than to the whole development, so a median Lean file makes **26**
units stale rather than 84 of 97, and a unit's closure is **116** files rather
than 332. On top of that, a documents check no longer recomputes a stale
derived artefact: it names the artefact and the refresh that rebuilds it, so
`corpus --check` is a matter of seconds whatever else has moved, and the
minutes are paid once by `corpus --refresh`. Write-up:
[`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5a and §5b.

---

## 3. What is open

This is the whole list. Nothing else in the repository is claimed as pending.

### 3.1 The evaluation finds no gap

The end-to-end set is **149 of 149** and every one of its sixteen refusals is a
`boundary` — a theorem or a stated commitment — rather than a `gap`. What
remains open is listed below, and none of it is a question the evaluation set
asks.

### 3.2 Named as untouched — all closed, and what each closure left

Every item that used to stand on this list is closed; each is recorded in
[`MASTER_PLAN.md`](MASTER_PLAN.md) with the study that closed it. What the
closures left behind is §3.4.

* **The infinite-dimensional half of the VOA bridge.** `VOA.lean` builds the
  state–field map at the Griess layer and shows where a finite model stops
  (`borcherds_commutator_fails`); `Heisenberg.lean` builds the Fock space of
  one free boson and proves `no_finite_dimensional_model`.
* **`heat : temperature :: force : ?`** — closed by the energy-conjugate
  register, with the four criteria a transportable relation must meet
  ([`CONJUGATE_STUDY.md`](studies/CONJUGATE_STUDY.md)).
* **The `O(1)` LLVQ table** — built and on the hot path, with the claim
  narrowed to *constant-bounded* and measured rather than asserted.
* **The Niemeier deep-hole census** — the trajectory distribution classifies
  (**40 of 44** at the escalated reading, **10 of 10** labels kept under a
  change of seed); what it does not do is certify, which is §3.4 item 1a
  ([`DEEP_HOLE_STUDY.md`](studies/DEEP_HOLE_STUDY.md),
  [`DEEP_HOLE_ESCALATION_STUDY.md`](studies/DEEP_HOLE_ESCALATION_STUDY.md)).
* **Open vocabulary** — closed as a mechanism: a name is admissible exactly
  when a stated route gives it coordinates computed from a register the machine
  already checks, and *justice* is refused by a condition it names rather than
  by kind ([`ADMISSION_STUDY.md`](studies/ADMISSION_STUDY.md)).
* **Words as projections** — closed for all twelve lexicon adjectives and for
  the comparative; what is open is data, which
  `replacement_witness()` keeps measured
  ([`RELATIVE_MEASURE_STUDY.md`](studies/RELATIVE_MEASURE_STUDY.md)).
* **The geometric items** — sigma–delta on the Leech shells, the 32- and
  48-dimensional lattices, the harmonic register and the economic register are
  all built, the last two with the honest verdict `not reproduced` against
  their controls ([`HIGHER_LATTICE_STUDY.md`](studies/HIGHER_LATTICE_STUDY.md),
  [`HARMONY_STUDY.md`](studies/HARMONY_STUDY.md),
  [`ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md)).

### 3.3 Ongoing rather than finishable

* **`related_to` as a residue.** 66 of the lexicon's 380 triples record that a
  link exists without saying which; all 66 are now *decided* rather than
  declined, 34 without a person, and `closure()` reports **0 triples waiting on
  a lookup**. What stays ongoing is that the lexicon can always grow another
  vague triple ([`DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md),
  [`VAGUENESS_STUDY.md`](studies/VAGUENESS_STUDY.md)).
* **Sparse chemistry.** 1,257 of 1,652 element cells are measured; the
  completed view reaches 1,442 by rules admitted only for halving the field's
  own out-of-sample mean, and each of the remaining 210 carries one of three
  stated reasons. Nothing is written back into the register, deliberately. What
  stays ongoing is the data
  ([`ELEMENT_COMPLETION_STUDY.md`](studies/ELEMENT_COMPLETION_STUDY.md)).

### 3.4 Named for the next round

**Read this section first on the next development push.** The head of
[`MASTER_PLAN.md`](MASTER_PLAN.md) names Phase 49 as where the next round
starts and points back here. The candidates are ordered: the first is the one that bears
most directly on the standing target.

**1. The comparison the field surface could not make — the one question it
left, and the sharpest candidate.** *Is energy more abstract than water?* is
still `surface`: both coordinates are in the lexicon register and no operation
reads two of them and orders them. It was declared unreachable by a field
surface *before* that surface was built, and it is unreachable for a reason
worth taking seriously — it is composition, blocker 3, not coverage. What
would close it is an operation over two readings of the same coordinate, with
the refusal it must make when the two rows carry the coordinate on different
scales. Unlike a field surface this is not `table`, so it is the candidate
that bears on the standing target.
[`FIELD_SURFACE_STUDY.md`](studies/FIELD_SURFACE_STUDY.md) §6.

*Closed this round (Phase 48, maintenance):* the handover the round before it
left open — the generated layer refreshed and every unit re-signed — and the
cost of `report lean`, which had grown through the evaluation's 300-second
ceiling. It is now 77 seconds, by an exact identity and an exact pruning
bound, with every figure of
[`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md) §7 unchanged. Neither
is a claim about reasoning, and the candidates above are unchanged by it.

*Closed in Phase 47 (maintenance):* the round loop itself. The
ledger's Lean selectivity, undone by the field surface reading the development
on the runtime's import path, is restored and pinned by tests — a median Lean
edit costs **27** of 98 units rather than 79 — and a passing documents check
is no longer re-derived over a tree in which nothing has moved. Neither is a
claim about reasoning; both are recorded as what they are, in §5e and §5f of
[`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md). The candidates
above are unchanged by it.

*Closed in Phase 46:* the field surface itself — candidate 1 of the round
before it. It answers <!--figure:fieldsurface-moved-->9<!--/figure--> of the
<!--figure:fieldsurface-held-->10<!--/figure--> questions the translation
experiment found held and unreachable, exactly the number declared reachable
before the run, and it is reported as coverage rather than reasoning:
[`FIELD_SURFACE_STUDY.md`](studies/FIELD_SURFACE_STUDY.md), with the
description in §2 and the proved boundary in `GLM.FieldSurface`.

**2. The empty rungs of the power-of-two family.** The family is complete as a
family and deliberately incomplete as a *ladder*: norms 2 and 256 are empty in
the ladder actually used, because the rungs that would fill them conflate. What
would close it is a rung at those norms that does not — Construction `A` over a
shortened code, or the `D₄`/`E₈` layers, which the scaling does not generate.
[`NORM_FAMILY_STUDY.md`](studies/NORM_FAMILY_STUDY.md).

**3. A register that arrives anonymous on its own.** Renaming is a faithful
model of a cross-vocabulary goal and it is still a model. The measurement to
want is the same table over goals from a second Lean development, or from a
generator, scored against the same controls — a register nobody constructed.

**4. The leak in the feature map.** The shipped map counts the type vocabulary
wherever it occurs, including inside an identifier, so 30 of 826 queries lose a
coordinate when their names go: a name creeping into a reading that is supposed
to be structural. Either the map is narrowed to count type words only where
they are types, or the leak is priced.

**5. The separation criterion, still unmet.** `nearest_correct` in
`DeepHoleLadder.lean` says a reading names holes correctly whenever
`ρ = 2W/B < 1`. Measured, `ρ` falls from `3.90` to **`2.59`** across the ladder
and never crosses `1`, so a classifier that names 40 of 44 still cannot certify
a single *absence*: faithfulness needs `r ≥ 0.0659` where separation permits
`r < 0.0179`. Either a rung is found where `ρ < 1`, or a bound is proved saying
no reading of this family reaches it. Its companion is
`GLM.DeepHoleFailure.per_type_absent`, the certificate whose hypothesis is
currently unmet, so the theorem is instantiated nowhere.

**6. The thirteen unreached Niemeier types.** The ensemble reaches **10** of
the 23 root systems from the 14 declared centres; the other **13** are reported
as unreached and nothing is claimed about them. Reaching them means new
centres, and new centres mean a new pre-registration.

**7. What the adopted guard costs, and why the metric reading is safe.** The
guard refuses 137 queries it used to answer correctly. The room is in the
*reading* rather than in the contract — the weaker guard is measured and never
reaches safety — and the metric reading answers nothing wrongly on any of the
six operations while losing to the primary on four, which is a decomposition
worth understanding. A margin other than twice the nearest distance is the
obvious sweep. [`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md) §9.

**8. The planner's utility gate.** The reverse-call planner satisfies every
safety line of its promotion checklist and fails the one that decides it: on
this project's own evaluation set it gains nothing, because the refusals it is
offered are refusals it agrees with. The question that would close it is about
the **tool registry** — whether a tool exists that a problem-driven front end
could reach and the kind-driven dispatcher cannot. Until one does, directive
**D14** keeps the planner in the sandbox, imported by nothing the system
computes with.

**9. A conflation the rational reading must make.** Read alone, the exact
distance measure conflates `A_1^24` with `A_2^12`. That is a capacity boundary
of the kind [`INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) is
about, and it is recorded as an observation rather than as a theorem. The
theorem to want says *which* pairs any stray-blind reading must conflate.

**The discipline any of them is taken under**, unchanged: the thing must be
described or measured rather than asserted, what does not generalise must be
counted rather than hidden, the path it replaces must be frozen so the new one
has something to agree with, and the end-to-end evaluation must return the same
answers and the same refusals. What should **not** generalise is the
judgements — which brackets count as ordinary cases, which factor basis may
explain a dimensional difference, which pole a word names, which phrasings are
the same question — and a `Phrasing` cannot be constructed without the sentence
that justifies it. Coverage stays two figures rather than one: three of the
eight registers are described, and seven of the twenty-one answerable query
kinds are.

---

## 4. Re-verifying the whole thing

**The operating manual is [`ITERATE.md`](ITERATE.md)**, which states the three
gates — the document check after prose, the changed-unit run after code or
Lean, the release once at the close of a round — and which to run when. This
section is the detail behind them.

### 4.1 The short way — run only what has changed

**Start here.** Everything is signed off in `overlay/.glm_signoff.json`: each
test file and each instrument carries the SHA-256 of everything its last
passing result depended on — the file itself, every module it imports
transitively, the frozen data those modules read, the documents and Lean
sources they name, the harness and the interpreter. If that digest holds,
re-running proves nothing; if a byte in the closure differs, the unit is run
again. Nothing is skipped silently.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check            # documents, ~30 s
PYTHONPATH=. python3 -m glm_universal.signoff --verify          # what still holds
PYTHONPATH=. python3 -m glm_universal.signoff --plan            # what would run
PYTHONPATH=. python3 -m glm_universal.signoff --why             # and why each unit would
PYTHONPATH=. python3 -m glm_universal.signoff --impact ../DIGEST.md  # what an edit would cost
PYTHONPATH=. python3 -m glm_universal.signoff --run-everything --jobs 8
PYTHONPATH=. python3 -m glm_universal.signoff --release --jobs 8   # closing a round
PYTHONPATH=. python3 -m glm_universal.signoff --release --resume --jobs 8  # after one was interrupted
```

A release writes each signature as it is earned rather than at the end, so an
interrupted one is resumed rather than restarted: `--release --resume` runs
only the units the release question still calls stale, and
`--verify-release` — which re-checks every signature and reports anything
signed without the exhaustive cases as `partial` — is still what decides the
round.

`--why` splits a unit's closure into five disjoint groups — scaffolding, data,
documents, Lean, code — and names the ones that moved, so a long plan says
which entries are a prose edit and which are not. `--impact PATH` asks the
same relation in the other direction and *before* the edit: 93 of the 96 units
reach `PROJECT_DIRECTIVES.md` (about 66 minutes), 6 reach
`signoff/ledger.py`, 1 reaches `signoff/__main__.py`.

The seven instruments in the ledger beside the
<!--figure:test-files-->98 test files<!--/figure--> are `lean-build`,
`lean-sorry-free`, `lean-copies-identical`, `capabilities`, `benchmarks`,
`evaluation` and `figures`. Editing a document makes exactly the units that
read that document stale — `test_figures.py` yes, `test_substrate.py` no — so
writing up a finding costs one short re-run rather than a quarter of an hour.
A median Lean edit makes **27** units stale and a unit's closure is **129**
files. [`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md)
§5a is the measurement; `glm_universal.corpus.cost.lean_blast_radius`
recomputes it; directive **D16** is the rule.

That selectivity is a property of the tree and not of the rule alone, and a
feature undid it once: the field surface loaded its Lean rows by parsing the
development, on the runtime's own import path, so the whole development
re-entered nearly every closure and a median Lean edit made **79** of 98 units
stale. The rows come from the stored address book now — `lean_address.py`
builds the book, `lean_book.py` answers from it and reads no source — and the
property is pinned by a test rather than by a paragraph
(`test_signoff.py`, `test_corpus.py`). §5e of the same study is the
measurement.

**The documents gate skips a question whose inputs have not moved.** The
verdict of a passing `corpus --check` is stored beside a digest of everything
that check can read — the documents, the rendering code, the data it reads and
the Lean sources its blocks quote. A check over an unchanged tree answers from
that record in about three seconds instead of re-rendering 97 blocks and 201
figures; only a pass is recorded, so a failure is never skipped, and
`--check --all` ignores the record. §5f of the same study.

The same rule now applies to the ledger's own sources. `signoff/rules.py` is
the **rule** — what a closure is, what a digest covers, how a unit is run —
and is in every closure, so editing it costs the whole suite. `signoff/ledger.py`
is the **record** and costs 6 units; `signoff/checks.py` costs 2 and
`signoff/__main__.py` costs 1. §5c of the same study is the measurement.

**A stale derived artefact is reported, never paid for inside a check.** The
expensive derivations — the planner's fallback reading over the evaluation set,
the type-2 class table, the economic lattice points — are kept beside the
digest of the code they came from. `corpus --check` runs with recomputation
forbidden, so a stale one is named together with the command that rebuilds it
rather than silently costing a quarter of an hour; `corpus --refresh` is where
that cost is paid, once.

### 4.2 The long way — run everything from scratch

In order, from the repository root; the last step is the one that catches a
document drifting from the code.

```bash
lake build                                                   # 119 Lean files, no sorry
rg -n 'sorry|admit' RequestProject/GLM                       # expect nothing
diff -r RequestProject/GLM overlay/glm_lean/RequestProject/GLM   # the two copies agree

cd overlay
PYTHONPATH=. GLM_EXHAUSTIVE=1 python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 -m glm_universal.capabilities           # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks             # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8    # 157 CLI cases
PYTHONPATH=. python3 -m glm_universal.figures --write        # regenerate FIGURES.md
PYTHONPATH=. python3 -m glm_universal.corpus --refresh       # every derived artefact
PYTHONPATH=. python3 -m glm_universal.corpus --check          # exit 1 on any drift
PYTHONPATH=. python3 -m glm_universal.tools lean-mirror --write  # the Lean mirror
```

Spot checks that exercise the runtime the way a user does — each returns
`VERIFIED True`, because the Three Column Thinking template regenerates the
answer's figures in a fresh interpreter and compares them with what was
printed:

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report analogies"  --verify-tct
PYTHONPATH=. python3 GLM.py -q "report chemistry coverage" --verify-tct
PYTHONPATH=. python3 GLM.py -q "report lean"       --verify-tct
PYTHONPATH=. python3 GLM.py -q "report escalation" --verify-tct
PYTHONPATH=. python3 -m glm_universal.tools pipeline      # the wiring stages
PYTHONPATH=. python3 -m glm_universal.tools directives    # the standing rules
PYTHONPATH=. python3 -m glm_universal.tools signoff       # the ledger summary
```

---

## 5. The document map

There is no hand-kept index any more, because a hand-kept index is a stored
table and this project's rule is that a table may be kept only beside the
digest of what it came from.

* [`ENTRY.md`](ENTRY.md) states the reading order and the coverage claim:
  these documents describe the system as it is, everything else is a record of
  a round.  The claim is tested — `glm_universal.corpus.checks` fails if a
  current-state document is unreachable from it or an archived one is missing
  from its list.
* [`DIGEST.md`](DIGEST.md) is that list at tier 0, one row per document —
  question, verdict, deciding figure, and the function that recomputes it.  It
  is **generated** from the documents' own tier-0 blocks by
  `python3 -m glm_universal.corpus --write`, so it cannot drift from them.
