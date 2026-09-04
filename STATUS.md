# Status

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

## How to work in this repository

**Commit and push after each completed step, not once at the end.** A step is
anything that leaves the tree in a working state — one document reconciled,
one test added, one lemma proved. Never leave a session's work sitting
uncommitted: a commit is cheap, and an interrupted session that has been
committing as it goes hands over something that runs. The same rule is at the
head of [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) and is directive D1.

---

*The one document to read first. What is done, what is open, and how to check
any of it without recomputing anything by hand.*

**Starting a new round? Read §3.4, "Named for the next round", before
anything else** — it now names two pieces of work rather than three: the
Niemeier deep holes classified from a trajectory distribution, and the semantic
half of the analogy. The third, a stability measurement under declared exact
perturbation, is closed and is `reasoning/stability.py` against
`RequestProject/GLM/Stability.lean`. This round gave the address book a
functional role and gave the system its first loop: §2, "The address book, made
to do work" and "The loop: propose, check, refuse". The round before it put
back the work that had been dropped from the delivered tree and closed the
archive's second reading with it — §2, "The dropped work, restored, and the
second reading of the archive closed" — and the one before that read the
supplied archive to the end. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phases 21–27
are the items written as work, and Phase 28 is what §3.4 proposes.

Last reconciled against a full re-run on 2026-09-04.

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
| test suite | `python3 -m pytest glm_universal/tests -q` | **3,163 tests across 73 of the 74 test files, 12,838 subtests, outside the document check**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **134 / 134** — 118 answered, 16 refused as expected (all `boundary`, no `gap`), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites, every suite above its baseline |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 errored, 0 surprises |
| Lean development | `lake build` (repository root) | 97 Lean files, 28,209 lines, **0 `sorry`** |
| figures | `python3 -m glm_universal.figures --write` | regenerates `overlay/FIGURES.md`; every documented count |

The test-suite row is the sign-off ledger's own count, recorded by
`python3 -m glm_universal.signoff --release`, which runs each test file in its
own process with the `exhaustive` tests selected. One `pytest` process over the
same tree collects 3,191 — 3,165 passed and 26 skipped — which is the ledger's
3,163 plus the 28 tests of the document check the ledger's total leaves out,
because a round that adds a document or a figure fails that check until the
documents are reconciled. The 26 skipped are the `exhaustive` tests, which
certify rather than sample and are deselected unless `--exhaustive`,
`GLM_EXHAUSTIVE=1` or the release runner selects them, which is why the
ledger's own count is the full 3,163.

The package is `glm_universal` **v1.15.0**: eleven sub-packages, 112 modules,
**8 registers** holding 1,089 carriers (physics 726, chemistry 118, molecules
51, mathematics 22, lexicon 95, spatial 28, harmonics 28, economics 21) beside
a 45-class comparison register, **21 query kinds**
one of which dispatches **51 report subjects**, and 3 tasks.

---

## 2. What is done

Each entry names the thing that recomputes it, so nothing here has to be taken
on trust. `MASTER_PLAN.md` carries the same list phase by phase with more
detail.

**Substrate and algebra.** Complete syndrome decoding with no silent tie-break;
the full Leech lattice in place of Construction A (kissing number 196,560); the
exact 2A Sakuma product in place of the XOR shortcut; the six-facet orthogonal
decomposition with the lattice index that says what a facet reading loses; the
`LEGACY_TO_CORE` frame bridge, verified an isometry.

**Registers.** Eight of them. Physics (726 quantities, EXT10 exponents and
unit strings cross-checked against each other), chemistry (118 elements),
**molecules** (51 species and ions, every coordinate derived from the element
register at load time, bundle and composite collisions tested at 0),
mathematics, lexicon (95 concepts, 380 explicit relation triples), spatial,
**harmonics** (28 musical intervals as exact rational frequency ratios, every
coordinate computed from the pair `(n, d)` rather than stored beside it) and
**economics** (21 quoted prices as exact rationals over seven instruments and
three quarters, every coordinate computed from the price, its magnitude bucket
and its mantissa).

**Reasoning.** 49 modules. Analogy by named relation, dimensional verification,
Buckingham-Pi from an exact rational nullspace, the Walsh–Hadamard transform
decoder, the deep-hole walk, term arithmetic, unit parsing with the steradian
priced rather than silently redefined, and element-coverage widening that
labels every widened cell by provenance.

**Values.** Reals held as processes with no float anywhere; written arithmetic
over them including `exp`, `log`, `sin`, `cos`, `tan` and real powers; decided
inequality and refused equality; the delta–sigma modulator with its proved
`1/N` rate and, in 24 coordinates, the separating functional that proves a
target outside the hull unreachable.

**Meaning.** The grounded graph — 357 meanings, 1,705 notations, 12,859 edges,
every one re-derived on demand. The inherited ARC-era concept graph was
audited and the decision recorded: **demoted to evidence**, and
`tests/test_inherited_graph.py` enforces it by walking the imports of every
module that answers a question.

**Analogy.** The layer that closed the previous round's five wrong answers, and
the three lexicon/benchmark corrections that closed the last three misses.
Write-up: [`ANALOGY_LAYER_STUDY.md`](studies/ANALOGY_LAYER_STUDY.md).

**Measurement.** Three instruments that do not trust each other: probes
(library boundaries), benchmarks (solver functions) and the end-to-end
evaluation (the CLI in a fresh interpreter per question, scored asymmetrically
so a confident wrong answer is worse than a refusal). Write-up:
[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md).

**Layers, and the chain made a real refinement.** The audit that
`reasoning/information_loss.py` runs on the *shipped* layer definitions — not
on an idealisation of them — used to report `refinement_chain_intact = False`:
the substrate's 24-bit parity view separates a unit on coordinate 10 from the
vacuum, and an integer layer that reads only the seven SI7 exponents conflates
them. The decision recorded in
[`INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) §3.1 was to
**widen** the integer layer rather than narrow the substrate, so that no
information is lost at any stage: `LAYER_INTEGER` carries the substrate reading
beside the exponents, the Griess view carries the carrier beside the algebra,
and the report now says `refinement_chain_intact = True` on all four
boundaries. The rejected narrow reading is kept beside it as
`LAYER_INTEGER_RAW` and its cost is still measured. The layers as they now are
are formalised in `RequestProject/GLM/LayerChain.lean`, where
`GLM.Info.glmChain_refines_of_le` is the chain property itself and
`GLM.Info.glmSi7Layer_not_refines_glmSubstrateLayer` is the original defect as
a theorem.

**The layer chain audited at register scale.** The chain above was closed on
seven carriers, and each of those seven had been chosen *because* it exhibited
a boundary. `reasoning/escalation.py` re-runs the whole audit on **one carrier
per named object of every register the package ships** — physics 726,
chemistry 118, molecules 51, mathematics 22, harmonics 28, lexicon 95, 1,040 in
all, nothing sampled — by grouping carriers under each layer's own zero-measure
class key, which turns a quadratic scan and a quartic congruence search into
one pass; `key_agreement` then re-derives every verdict from the layers'
`perceive` and `measure` on 918 pairs and finds no disagreement. Resolution
runs 415 → 544 → 757 and then flat, the two lower boundaries gain 5,883 and
5,475 pairs, and there are **zero refinement violations: the chain is intact at
scale as well as on the sample**. The scale-up also found what seven carriers
could not — a **resolution ceiling**: 757 distinct carriers means 283 named
entries share a carrier, in 104 collision classes every one of which lies
inside a single register (the largest is 78 dimensionless physics quantities),
so what is missing there is a coordinate for the name, not a finer layer. The
rejected `LAYER_INTEGER_RAW` reading, which cost one pair on the sample,
conflates 11,176 pairs the substrate separates.
`RequestProject/GLM/Escalation.lean` proves the parts that are not
measurements — `GLM.Info.entryResolution_le_distinct` (the ceiling),
`GLM.Info.entryResolution_mono` (the order of the stack) and
`GLM.Info.substrate_addition_not_congruent` (why addition does not descend
below the rational layer). Written up in
[`studies/ESCALATION_STUDY.md`](studies/ESCALATION_STUDY.md); recomputed by
`report escalation`.

**Measure words as relative measures.** `hot` used to be a concept and
nothing more: the lexicon says `property_of temperature` and which pole of it
the word names, and cannot say *how hot*. It now carries a measurement beside
the concept. `data_objects/comparison_classes.py` holds **45 comparison
classes over 11 quantities** — each an exact bracket in SI base units, with the
unit, the dimension and the EXT10 exponents read out of the physics register
rather than typed again — and **11 measure scales carrying 64 degree words** at
exact positions in `[0, 1]`, checked against the semantic lexicon on the 12
words the two registers share. `reasoning/measure_view.py` reads a word
against a class as an exact rational: *hot* in tea is **363 K** and *hot* for a
stellar surface is **44 000 K**. Measured over the 56 uses the registers admit,
the static reading resolves **12** and the widened one **56**, gaining **108
pairs with zero refinement violations**. The replacement reading that drops the
concept costs nothing on the shipped data only because every adjective now has
a quantity; `replacement_witness()` re-runs the audit over those 56 uses plus
one unmeasured use of each of the 12 words, and over those **68 uses** the
widening gains 164 pairs with 0 violations while the replacement **violates
refinement on 66** — which is why the reading is added rather than substituted,
exactly as `LAYER_INTEGER_RAW` was kept rather than shipped. **27 of the 66
`related_to` triples** convert to a measured relation (6 `same_dimension_as`,
21 `differs_by`) and the other 39 report why they were declined. The query is
`measure hot in tea`, `measure hot`, `measure 300 in tea`, and the comparative
`is cold in stellar_surface hotter than hot in tea` — **yes**, 8000 K against
363 K, with the two words in the opposite order on the scale, which is what 151
of the 204 cross-class pairs do. Both **refuse** where the registers decide
nothing — `measure hot in walking`, `measure expensive in market` — which
`RequestProject/GLM/MeasureView.lean`'s `GLM.Info.boundary_empty_of_unmeasured`
says is forced rather than missing, beside
`GLM.Info.measureLayer_refines_staticLayer` (the widening),
`GLM.Info.measureReading_not_refines_staticLayer` (the rejected replacement)
and `RequestProject/GLM/Comparative.lean`'s `hotterThan_trichotomy`,
`hotterThan_iff_position_lt` and `comparative_not_static`. Written up in
[`studies/RELATIVE_MEASURE_STUDY.md`](studies/RELATIVE_MEASURE_STUDY.md);
recomputed by `report measure`.

**The undimensioned names, decided.** *"`motion` reaches no dimension the
register holds"* reports a lookup, not a fact about the word, and no amount of
searching settles the difference between a name the register spells differently
and a name that denotes no magnitude at all. `basis_sweep()` first establishes
that the automatic half is exhausted — of the **713** quantities the register
holds and the factor basis did not, 571 change nothing, 125 would make an
attribution ambiguous and are refused, and the 17 that strictly convert more
occupy four dimensions, two deciding the same triple, so the data decides three
factors. `data_objects/denotation.py` then decides the rest by hand: **36
entries**, one per undimensioned endpoint of the residue, each with a verdict
and its written justification — 1 `quantity`, 3 `ambiguous`, 4 `polymorphic`, 9
`carrier`, 11 `process`, 8 `abstraction`. Only `quantity` makes a name
dimensional and it supplies **no coordinate**: *gravity* is the register's own
`gravitational_field` under an ordinary-language spelling, exactly as an alias
is. `reasoning/denotation_view.py` measures what the decisions change: **0** of
the 39 residue triples convert — deciding what a word denotes is not a way of
manufacturing relations — 6 are repaired to `names_process_of` (a process
beside the quantity that quantifies it), 33 are declined by a reason that names
what the endpoint *is*, and the register decides exactly the names the residue
asks about (0 undecided, 0 idle). What is earned is `closure`: **39 of 39
accounted for, 0 waiting on an entry**. A `carrier` beside a quantity is
deliberately *not* repaired — a magnet bears a flux density and a photon does
not bear an illuminance, and a rule right half the time is a guess. The
conversions carry: of the **22** analogies the repaired triples license, 12 are
answered where the unrepaired control answers **1**.
`RequestProject/GLM/Denotation.lean` proves the part that is not a measurement
— `reach_invents_nothing`, `secondPass_eq_firstPass_of_decided`,
`secondPass_eq_firstPass_of_no_quantity_verdict`, `undecided_is_decided` and
`repaired_not_converted`. `report denotations`. Write-up:
[`studies/DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md).

**The recipe, made into an object.** Every capability above was built by hand
from one recipe — a register of derived carriers, a reading over them, an audit
of what the reading gains, a query that refuses where the registers do not
decide, and a machine-checked statement of the part that is not a measurement.
`glm_universal/recipe/` makes the recipe's *input* an object: a **domain
description** says what the objects hold, how each coordinate is derived, which
coordinates recover the object, what the readings are and what must be refused,
and `recipe/build.py` turns any such description into the carriers, the layer
chain, the widening audit, the query surface and the refusal boundary while
knowing nothing about any domain. Three registers built by hand in earlier
rounds — comparison classes, harmonics and prices — are described in **72
coordinates**, of which **66 are shared primitives and 6 are judgements**, all
six of them the musical conventions; the comparison and economic registers need
none at all. The test is subtractive and is run rather than asserted: each
domain is deleted and rebuilt from its description alone, and **94 of 94
carriers** come back identical coordinate by coordinate, every object equal and
every measured figure unchanged with the regenerated register in the shipped
one's place. `derive <coordinate> of <object>` answers off whichever
description derives the coordinate — `derive span_ratio of tea` is `373/293` —
and refuses where none does, which `RequestProject/GLM/Recipe.lean` states as a
theorem (`Spec.answer_eq_none_iff`) beside the widening, the read-back and
regeneration itself (`encode_congr`, `indist_congr`, `answer_congr`).
`report recipe`. Write-up:
[`studies/RECIPE_STUDY.md`](studies/RECIPE_STUDY.md).

**The question shape, made into an object.** The recipe above made a *domain*
declarative and then named its own limit: the way a question is **asked** was
still a hand-written phrase in `runtime/parser.py`, so a new domain arrived
with its carriers and waited for someone to write its questions.
`glm_universal/language/` makes the question's *shape* an object, and the
runtime now reads the descriptions instead of the branches.

A **slot description** is an opening, then named slots separated by literal
words, with an optional tail, a described **preamble**, a slot whose filling is
a **list**, and named boundaries it must refuse at; one generic matcher reads
any of them and knows nothing about any kind. Four of the runtime's twenty
answerable query kinds — `derive`, `measure`, `task` and `compare` — are
written that way, in **7 slots and 47 surface forms at 15 judgements**, every
judgement carrying the sentence that justifies treating its phrasings as one
set.

A **second family** cuts a *string* at a described operator, for questions
whose operands are notations rather than runs of words: `verify`, `analogy` and
the relational half of `compare`, in **8 operands and 39 surface forms at 13
judgements**. Two things a shape may hold beside its operands are described
here rather than scanned for — a **modifier**, a word that directs how the
operands are read without naming one of them, removed at the head and in the
trailing frame and nowhere else, and a described **trailing option**.

A **third family nests**: `comparative` is infix too, but each side must be a
*measured use*, which is the measure shape itself, tightened — the opening
dropped, the class required, both slots narrowed to a single name — at **4
judgements**. The operator is open rather than listed: any `-er than` word, or
any word inside `as … as`.

**All seven hand-written branches are deleted.** `parse_query` dispatches every
described kind through its description, and the deleted code is kept frozen in
`language/legacy.py` so that the comparison still has something to measure
against — imported by the measurement and by nothing in the runtime.

The test is a comparison and is run rather than asserted. Over corpora of
**947, 201 and 628 questions generated from the registers**, the descriptions
produce the same kind and the same options as the deleted branches **947, 201
and 480 times with 0 disagreements**; all **111** evaluation questions of the
undescribed kinds are **declined, not misread**; every named boundary has a
witness that reaches it; every question written back from the slots it filled
matches to the same filling; and **20 narrowing witnesses** record what the
branches answered by keeping stray words inside an option. The one place a
description reads *more* than its branch did — **148 comparatives written with
`relative to` on a side**, a separator the measure shape admits and the
branch's hand-copied side pattern never did — is declared as a widening and
accounted for question by question, with **0 left over**.

Coverage is therefore **7 of 20 answerable kinds across 3 families, every one
of them read off its description by the runtime**, with **3 limits written
down** rather than left implicit — the first being the thirteen kinds that
still have a branch apiece and are not shapes of any family.

The slot openings are pairwise non-prefix, so the shapes are a set rather
than a priority list, which `RequestProject/GLM/Question.lean` states as
`matchPieces_not_both`, beside the round trip (`matchPieces_rendered`), the
guarantee that no required slot comes back empty
(`matchPieces_required_nonempty`) and the preamble pair — skipping a described
leading remainder leaves the match unchanged (`runPre_of_skipped`) while an
undescribed one is still refused (`runPre_refuses_undescribed`).
`RequestProject/GLM/QuestionNested.lean` carries the three new parts: the list
cut (`ListCut.cut_sep`, `ListCut.cut_two`, `ListCut.cut_ne_nil`), the modifier
frame removed at the head and the tail and *not* in the middle
(`ModifierFrame.strip_head`, `ModifierFrame.strip_frame`,
`ModifierFrame.strip_middle`) and the nested shape with its round trip and its
two refusals (`NestedSpec.run_rendered`, `NestedSpec.run_no_operator`,
`NestedSpec.run_side_refused`).
`report language`. Write-up:
[`studies/LANGUAGE_STUDY.md`](studies/LANGUAGE_STUDY.md).

**The quantiser's search, replaced by a lookup.** The Leech quantiser is the
hot path of every address and it was a scan: 4,096 Golay codeword costs per
congruence class, 8,192 per call. `reasoning/llvq_table.py` reads the code off
the MOG instead — a codeword is a word whose six GF(4) column labels form a
hexacode word, whose six column parities agree and whose top row carries that
same parity, all three checked over all **4,096** codewords, and 64 hexacode
words × 2 parities = **128 classes of 32** with nothing left over, so the three
conditions characterise the code rather than merely holding on it. Inside a
column `(label, parity, top bit)` fixes the pattern, which is the whole table:
**16 entries**. A class minimum is then a six-term min-sum under one parity
constraint, and the decoder opens a class only while its minimum does not
exceed the best total so far.

That is proved rather than asserted, in `RequestProject/GLM/LLVQTable.lean`:
`isLeast_cost_of_parity_eq` and `isLeast_cost_of_parity_ne` are the class
minimum in both parities, `card_parity_class` is why a class holds 32 words,
and `isLeast_of_bounded_search` is why the bounded search may stop. Measured
over 40 deterministic vectors the table route forms **484/5 = 96.8** codeword
costs per call against the scan's 8,192 (84.6× fewer words, 71.3× fewer
additions), opening 121/40 ≈ 3.03 of 256 classes, with a worst call of 448
words. The claim is **constant-bounded, not constant**, and the worst case —
the whole code — is named rather than hidden.

The subtractive test is the corpus: `lean_address.quantise` now decodes through
the table, the scan stays in `analogy.py` as the thing to agree with, and all
**2,118** declarations of the Lean development decode to the same address,
**0 changed**, beside a point-for-point agreement over the deterministic sweep,
the register carriers and the boundary vectors — **107 vectors, 0
mismatches**. `report llvq`. Write-up:
[`studies/LLVQ_TABLE_STUDY.md`](studies/LLVQ_TABLE_STUDY.md).

**Documentation binding.** `figures.py` recomputes every documented count and
`tests/test_figures.py` makes a stale figure a test failure.

**The archive, read to the end.** The supplied archive had never been read all
the way down, and this round went through the parts the brief named and asked
of each script one question: is there a claim here that can be stated as a
theorem and checked? **25 files of Lean, 7,170 lines, 848 declarations** came back
— the MOG cube, the lattice shortcut, the three generations of the paper's
formal companion, the electromagnetic calibration, the first-principles and
projection sub-studies, the graded cost model, spatial arithmetic and the
ARC-era reasoning loop. **Nine of the twenty-five are negative results**: the
calibration chain returns the `c` it was given, `3, 6, 9` is produced by any
three-element set, what a binary substrate forces is 23 rather than 24, the
three-cube rules give a `[24,12,4]` code no relabelling repairs, the published
directory's "even quantisation" is true by construction, the substrate's
`snap_to_codeword` is not a decoder, consecutive integers are never a "geodesic
jump", and the electron-mass alignment point is off by 0.0090–0.0093 % rather
than the quoted 0.007 % — with `FitCapacity.lean` the instrument that prices
such agreements at all. Nothing the system *answers* moved. Write-up:
[`RETRIEVED_LEAN_STUDY.md`](studies/RETRIEVED_LEAN_STUDY.md).

**The address book, made to do work: retrieval measured against its controls.**
The address book was a table; nothing in the system used it to answer anything.
`reasoning/retrieval.py` makes it an index and measures it against six controls
over **202** stride-selected queries of the **2,826**-declaration corpus, with
chance computed in closed form rather than simulated. At `k = 5` the structural
address finds a relative for **51.5 %** of queries against **6.9 %** for chance
— **7.4×** — and beats the digest (3.5 %), the seeded reshuffle (6.9 %), the
random ranking (5.9 %) and name-substring search (34.2 %). It is then beaten
decisively by a plain lexical control: Jaccard overlap of identifier tokens
reaches **85.6 %** at **57.7 %** precision against the address's 15.5 %. Two
ablations say where the signal lives: the same feature vectors ranked with **no
lattice at all** score **51.0 %**, within half a point, and a second address
built from identifiers rather than syntax reaches **64.9 %** — so the geometry
transports the features faithfully and adds nothing to them. What it does earn
is exactness: `RequestProject/GLM/Retrieval.lean` proves a completeness bound
that holds on **144,075** measured pairs with **0** violations, and at feature
radius 2 the guaranteed-complete shortlist is **70.9** declarations — 2.5 % of
the corpus — so an empty shortlist is a *proof* of absence
(`filterRadius_eq_nil_certifies_absence`). `report retrieval`. Write-up:
[`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md).

**The loop: propose, check, refuse — and whether the substrate can steer it.**
Everything else in the system answers in one shot. `reasoning/controller.py` is
a loop that decomposes, tries, checks and either revises or gives up, built on
the one register where every step is exact: build a physical quantity out of
the ten EXT10 generators one factor at a time, twenty moves per step, the state
checked against the target exactly. Every plan any scorer returned was
re-verified end to end by `verifier.verify_expression_pair` through the digit
stack — **100 %**, under every scorer, by an instrument that did not build it.
It refuses in two ways and only one is a budget: **127 of the register's 726**
quantities are refused *with a proof* — an invariant no move can change,
`Controller.unreachable_of_invariant` — with no node expanded, and a beam that
runs out of depth is refused rather than dressed up as an answer
(`Controller.beam_can_miss` is a decided witness that a width-one loop can miss
a plan that exists). On the 24 reachable tasks the Leech-address scorer solves
**18** against **8** for no guidance and **12** for a scorer blind to the
target — the substrate can steer — but the same distance measured **without**
the lattice solves **17**, one behind and with a better minimality record, and
at the register's own resolution (scale 1 instead of 9) the address scorer
falls to exactly the no-guidance **8**, which is what the read-back bound of
`Address.lean` predicts. `report controller`. Write-up:
[`CONTROLLER_STUDY.md`](studies/CONTROLLER_STUDY.md).

**The dropped work, restored, and the second reading of the archive closed.**
The tree handed over at the end of the retrieval round was missing part of what
that round had produced: Lean files, their test files and several study
documents had not survived the handover, and `dropped.zip` at the repository
root is what came back. Everything in it has been put back and re-verified
rather than taken on trust — the Lean sources build against the pinned Mathlib
with no `sorry`, and every figure their tests pin was recomputed from the
substrate. With them the development stood at **95 files, 27,548 source lines,
2,764 parsed declarations**, against 73 files and 2,118 declarations at the close of
the retrieval round. Three of the study documents could not be restored and
were written from the code instead —
[`SOURCE_SALVAGE_AUDIT.md`](studies/SOURCE_SALVAGE_AUDIT.md),
[`SOURCE_SALVAGE_SECOND_PASS.md`](studies/SOURCE_SALVAGE_SECOND_PASS.md) and
[`ARCHIVE_DEEP_DIVE_STUDY.md`](studies/ARCHIVE_DEEP_DIVE_STUDY.md) — and one
Lean file is new rather than restored: `Golay/CubeMirror.lean`, the parity
count that caps the free symmetries of the cube surface at 24. The archive's
search loop is now the **49th report subject** (`report searchloop`) and the
evaluation's **132nd case**; the end-to-end set was **132 / 132** with the same
16 boundary refusals. The reasoning package went from 49 modules to **57**.

**The exactness inventory, machine-checked.** `reasoning/exactness.py` parses
every module of the package and reports three inventories — where a float
could be constructed, where a cryptographic digest is taken, and (through
`combiner.xor_inventory`) where XOR is used. `tests/test_exactness.py` turns
them into a rule that bites in both directions: the suite fails when the tree
acquires a site nobody declared, and equally when a declared site stops
existing, because a stale inventory misleads as much as an incomplete one. The
scanner itself is tested rather than trusted, and the timing layers are held to
integer nanoseconds with exact formatting (D7, D9).

**The number-theory evidence paper, audited against the code.**
[`GLM_Complete_Number_Theory_Evidence.md`](studies/GLM_Complete_Number_Theory_Evidence.md)
quotes three exact tables, a worked example that walks one number down every
layer, an index of the Lean theorems behind each section, and a count of the
Lean development. `tests/test_number_theory_evidence.py` re-runs the generator
the paper names and compares the tables cell by cell, re-runs
`examples/number_pipeline.py` and compares the transcript line for line,
requires every theorem of Appendix A to exist in the file the appendix puts it
in, requires the quoted Lean file count to be the tree's, and checks the
paper's own no-float claim against the D7 scan. If the code moves, the paper
fails the suite rather than ageing quietly.

**The address book, regenerated over the larger corpus.** The Lean corpus grew
by a third with the restoration, so `studies/LEAN_ADDRESS_STUDY.md` was
re-measured rather than patched, and it has been re-measured again since over
the 2,826-declaration corpus: **2,826 / 2,826 declarations read back
exactly, 0 coordinate errors**, 2,486 distinct addresses, and nearest-by-address
shares a file **578 / 2,826** against 35 for the digest control and 37 for the
seeded reshuffle, with chance at ≈ **1.36 %**. Three citations in the
combiner study pointed at a namespace the theorems do not live in and were
corrected to `GLM.Golay24`.

**The Lean development.** 97 files, no `sorry`. Layer theory and the four
concrete boundaries; the Golay code, its sextet geometry, its coset census and
its dynamics; Cesàro convergence of the perturbation chain's time averages with
the explicit rate `|cesaro μ N f − 1/4096| ≤ 24/N`; the meaning carrier; the
value-layer error budgets; and the state–field map `Y(u, z)` at the Griess
layer of the 2A algebra, with the exact obstruction that shows the finite layer
is not a vertex algebra.  Five of the files carry the two claim ledgers'
subjects: `Mantissa.lean` (a float's orbit under the doubling map always
collapses, the exact orbit of `1/p` never does), `Reversible.lean` (the Gray
step, the cycle counts that refute "exactly half" at every finite width, the
gates, the kink invariant), `Cascade.lean` (a signal-driven modulator, the
closed orbit of a periodic input, and the MASH 1-1 cascade's `O(1/M²)`
triangular-window law against a single loop's `O(1/M)`), `Sturmian.lean` (the
modulator's stream *is* the mechanical word of its target, so entropy, run
lengths and transition rate are closed forms rather than measurements) and
`Feedback.lean` (a vector loop whose error returns through a rational matrix:
the `1/(2N)` law at the identity, the dead zone when the feedback contracts,
and exact equivariance under any permutation the matrix respects).

**The unification blueprint, tested rather than read.**
`reasoning/blueprint.py` turns `glm_unification_blueprint.md` into a live claim
ledger — each testable sentence recomputed against the package and given one of
four verdicts — and the three subjects it needed to reach a verdict on are
built beside it: `reasoning/engine.py` (Part III's carrier engine assembled
from parts the package already had), `reasoning/mantissa.py` (an exact binary64
model in which no float is ever constructed) and `reasoning/reversible.py`
(Part V: the Gray-code read channel, the Toffoli and Fredkin gates, the kink
invariant). `report blueprint`, `report engine`, `report mantissa`,
`report reversible`.

**Noise as a computation.** `reasoning/noise_lab.py` and `report noise`: the
delta-sigma loop stops being a way to *hold* a value and becomes the
computation — a two-tone input tracked inside the `1/N` law, orbits that close
exactly when a period sums to a whole number, cascaded loops whose error is a
second difference, an exact Walsh spectrum of an interacting pair, and a
subtractive-dither sweep that trades the idle tone down for a stated bias.
Everything is exact `Fraction`; nothing is random — and the vector case is
there too: error feedback through a rational matrix, tracking every coordinate
to `1/(2N)`, dying outright when the feedback contracts, and permuting exactly
with any symmetry the matrix keeps. Write-up:
[`NOISE_EXPERIMENT_STUDY.md`](studies/NOISE_EXPERIMENT_STUDY.md).

**The external study catalogue, tested rather than read.** The same treatment
for the second supplied document: `reasoning/catalog.py` recomputes every
testable sentence of `glm_study_findings_catalog.md` against the package —
**58 claims: 33 confirmed, 14 refuted, 7 not reproduced, 4 not implemented** —
with the two instruments it needed built beside it. `reasoning/wobble.py`
(`report signature`) runs the spectral-signature experiment and prints the law
beside every measured column, which is how the headline finding is stated:
those columns are closed forms of the target, proved in `Sturmian.lean`, so
running the loop tests nothing. `reasoning/drift.py` (`report drift`) runs the
prime-iteration stress test in exact arithmetic, in an exact binary64 model and
in binary64 truncated to a fixed number of displayed digits, with no float
constructed anywhere. Write-up:
[`GLM_STUDY_CATALOG_AUDIT.md`](studies/GLM_STUDY_CATALOG_AUDIT.md).

**The two companion preprints, tested rather than read.** The catalogue
above summarises two longer studies, and a summary loses the definitions. The
preprints state them, so `reasoning/companion.py` is a finer ledger over the
same material — **49 claims: 26 confirmed, 17 refuted, 5 not reproduced, 1 not
implemented** (`report companion`) — with the instrument it needs built beside
it. `reasoning/containers.py` (`report containers`) profiles eight constants
through three containers: the exact generator, with the steps to 10, 30 and 50
bits decided by integer comparison against a 200-bit reference; the
delta-sigma stream, with the closed form beside every measured column; and the
24-dimensional projection tested against the convex hull of the Leech minimal
vectors, where **both** verdicts are certificates over all 196,560 vectors
rather than a sample — a sample can establish *inside* and can never establish
*outside*, which is what makes the study's own census unsupported by its
method. Seven of the eight rows are settled, the eighth is left
`undetermined`, and the census reduces to two exact thresholds on the scalar:
inside at or below `0.5297`, outside above `0.8011`. Write-up:
[`GLM_COMPANION_STUDIES_AUDIT.md`](studies/GLM_COMPANION_STUDIES_AUDIT.md).

**A harmonic register, and the musical third of a claim.** The catalogue's
universality sentence — chemical equilibria, musical harmony and market price
discovery all said to be Leech proximity — was carried as `not implemented`
because there was nothing musical to run it against.
`data_objects/harmonics.py` supplies 28 intervals as exact rational frequency
ratios and `reasoning/harmony.py` (`report harmony`) tests the sentence instead
of repeating it: equal temperament's miss is the exact rational `(n/d)^12 / 2^k`
(`531441/524288` at the fifth, `1` at the unison and the octave and nowhere
else), no stack of fifths is a stack of octaves to `n = 200` — and by
`RequestProject/GLM/Harmony.lean` none ever is, for any equal division of the
octave — and Tenney height and Euler's gradus agree at an exact tau of
`313/378`. **The verdict is `not reproduced`**: decoded through their prime
exponents the 28 intervals do separate, at scale 8, and distance from the
unison orders them at tau `53/63` — but the same distance taken *before* the
decoder runs scores `53/63` too and the decoder reorders no pair, so what is
measured is the prime-exponent vector rather than the geometry of the lattice.
Section 6.2 of the catalogue ledger is therefore carried as two claims, each
reading its verdict off its own study at call time — the musical one off this
one, the economic one off the register below.
Write-up: [`HARMONY_STUDY.md`](studies/HARMONY_STUDY.md).

**An economic register, and the last third of that claim.** The economic half
of §6.2 was carried as `not implemented` for exactly as long as there was no
register of prices to run it against. `data_objects/economics_register.py`
supplies 21 quoted prices as exact rationals — seven instruments over three
consecutive quarters, every price a fraction of integers and never a float —
and `reasoning/economics.py` (`report economics`) measures the sentence. The
magnitude each price is read through is an exact bucket decided by integer
comparison rather than by a logarithm, specified and proved well defined,
unique, monotone and scale-shifting in
`RequestProject/GLM/LogBucket.lean`. **The verdict is `not reproduced`**, and
it is the control that decides it: decoded through buckets, mantissas and
EXT10 exponents the lattice separates all 21 records at scale 1024 and every
record's nearest neighbour is another quarter of the same instrument (21 of 21
against a chance rate of `1/10`) — but the same distances taken *before* the
decoder runs score 21 of 21 too, so what is measured is the price vector
rather than the geometry of the lattice. The agreement with the musical third,
reached by the same instrument in an unrelated domain, is itself the finding.
Write-up: [`ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md).

**The hexcolour address layer, audited.** A hexcolour is the six-hex-digit
rendering of a 24-bit carrier, one digit per four coordinates — an address in
the sense of directive D3 and nothing more. `report state migration` now
measures whether the layer does its job on the shipped data rather than merely
carrying it: 4,680 concepts carry an address, all 4,680 distinct, 0 fail to
read back to their own mask, 0 disagree with the mask stored beside them, 0
fail to commute with the legacy-to-core relabelling, and the 15 legacy
per-task addresses the supplied ARC pipeline left behind are all Golay
codewords and all round-trip. The gap the audit found was that nothing ever
looked anything *up* by an address, which is weaker than the word claims; the
concept store now has lookup by address and every one of the 4,680 concepts is
tested to round-trip through it.
Write-up: [`HEXCOLOUR_STUDY.md`](studies/HEXCOLOUR_STUDY.md).

**Every solver that takes a carrier accepts a formula.** An operand no
register enumerates is handed to the molecule formula parser before the query
is refused, so `coherence PbCl2`, `spatial PbCl2`, `angle PbCl2 water` and
`cluster PbCl2, water, ammonia` are answered from a carrier whose every
coordinate is derived from the element register. Nothing is guessed: an
unparseable formula still refuses. This closed the evaluation set's last `gap`
case.

**Above 24 dimensions.** `substrate/lattice32.py` builds the 32-dimensional
Barnes–Wall lattice by Construction D over `RM(1,5) ⊂ RM(3,5)`, whose payoff is
an address with **three usable resolutions** where a Leech address has one;
`substrate/lattice48.py` builds a 48-dimensional extremal lattice from a
self-dual ternary code and a neighbour step, at a centre density of exactly
`(3/2)^24` — about 16,834 times the Leech lattice's — and at the cost of the
whole binary picture. `reasoning/shell_sigma.py` runs the delta–sigma loop with
its alphabet widened to a Leech shell, so the alphabet no longer covers its own
hull: a target inside is tracked to the `B/N` law, a target outside is
certified unreachable by a separating functional, and the Gibbs-style rule is
reached deterministically by greedy error feedback. `report lattices`,
`report shells`. Write-up:
[`HIGHER_LATTICE_STUDY.md`](studies/HIGHER_LATTICE_STUDY.md).

**The Lean development, addressed.** `reasoning/lean_address.py` gives each of
the 2826 declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly 2826/2826 with 0 coordinate errors;
2486 distinct addresses, and the quantiser adds no conflation of its own;
nearest-by-address shares a file 578 times against 35 for a SHA-256 control and
37 for a seeded reshuffle, with chance at ≈ 1.36 %. `report lean`.
Write-up: [`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md).

**The standing rules, as instruments.**
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) states nine rules and names
the instrument for each. `reasoning/directives.py` parses that file and gives
each instrument a live verdict (`report directives`); `reasoning/pipeline.py`
reads the stage each piece of work has reached off the tree rather than from
prose — **21 of 21 rows** through all six stages (`report pipeline`);
`glm_universal/signoff/` computes a module's dependency closure with `ast` and
plans a run against recorded digests — the closure carries the documents and
Lean sources a module *names* as well as the modules it imports, and the seven
non-pytest instruments (`lake build`, the sorry scan, the two-copy diff, the
probes, the benchmarks, the evaluation and the figures check) are units of the
same ledger, so nothing that has not changed is run twice (§4.1); and
`glm_universal/integrity.py` holds
every SHA-256 use one module above the six core sub-packages, which the purity
audit enforces. `glm_universal/tools.py` is their command line, kept out of the
core for the same reason.

---

## 3. What is open

This is the whole list. Nothing else in the repository is claimed as pending.

**Closed this round.** *The address book made to do work, and the first loop*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 27). Two questions the brief asks and
the project had never put to itself: can the substrate **retrieve**, and can it
**steer a loop**? Both are now measured against controls rather than asserted,
and both answers are mixed in a way worth having. Retrieval: the address is a
real index — 51.5 % hit@5 against 6.9 % chance — beaten decisively by a plain
text control at 85.6 %, and matched to within half a point by the same features
with no lattice at all; what the lattice earns is a *proved* completeness
bound, 144,075 pairs with 0 violations, under which an empty shortlist is a
proof of absence. The loop: propose–check–refuse over the EXT10 generators,
every returned plan re-verified end to end by an instrument that did not build
it, 127 of 726 quantities refused with a proof and no node expanded, and the
address scorer solving 18 of 24 against 8 unguided — one *ahead* of nothing and
one *behind* the same distance without the lattice. Two Lean files
(`Retrieval.lean`, `Controller.lean`) and two test files came with them; the
development is **97 Lean files**, 28,209 lines, 2,826 parsed declarations, no
`sorry`; `report retrieval` and `report controller` are the **50th** and
**51st** report subjects and the evaluation's 133rd and 134th cases, so the
end-to-end set is **134 / 134** with the same 16 boundary refusals. See §2,
"The address book, made to do work" and "The loop: propose, check, refuse",
[`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md) and
[`CONTROLLER_STUDY.md`](studies/CONTROLLER_STUDY.md).

**Closed the round before.** *The dropped work, restored, and the second reading of
the archive closed* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 26). The tree handed over at the end of the retrieval round had
lost part of what that round produced. Everything `dropped.zip` holds — Lean
files, their test files and several study documents — is back and re-verified
from the substrate rather than trusted, three study documents that could not be
restored were written from the code
([`SOURCE_SALVAGE_AUDIT.md`](studies/SOURCE_SALVAGE_AUDIT.md),
[`SOURCE_SALVAGE_SECOND_PASS.md`](studies/SOURCE_SALVAGE_SECOND_PASS.md),
[`ARCHIVE_DEEP_DIVE_STUDY.md`](studies/ARCHIVE_DEEP_DIVE_STUDY.md)), and
`Golay/CubeMirror.lean` was written new. The development stood at **95 files,
27,548 source lines, 2,764 parsed declarations**, building with no `sorry` and identical in
both copies; the suite was **72 files of tests**; the archive's search loop is the
**49th report subject** and the **132nd** evaluation case, and the end-to-end
set was **132 / 132**. The exactness clean-up is finished and enforced by a
machine-checked inventory, the number-theory evidence paper is audited by a
test that re-runs its generators, and the address book was regenerated and
re-measured over the larger corpus. See §2, "The dropped work, restored, and
the second reading of the archive closed", and the three entries below it.

**And the round before that.** *The archive, read to the end*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 25) — the item that stood beside the
three §3.4 hands over. The parts of `source_material/GLM-main.zip` the brief
named were gone through script by script and asked one question: is there a
claim here that can be stated as a theorem and checked? **25 files of Lean,
7,170 lines, 848 declarations** came back, building against the pinned Mathlib
with no `sorry` and mirrored in `overlay/glm_lean/` — the MOG cube, the lattice
shortcut, the three generations of the paper's formal companion, the
electromagnetic calibration, the first-principles sub-study, the projection
sub-study, the graded cost model, spatial arithmetic and the ARC-era reasoning
loop. **Nine of the twenty-five are negative results**, which is the part of
the retrieval that could not have been had by leaving the material in the
archive. Nothing the system answers moved — the end-to-end evaluation is the
same **131 / 131** with the same 16 boundary refusals — but the Lean corpus
grew by two thirds, to **2,118 declarations across 73 files**, so
`studies/LEAN_ADDRESS_STUDY.md` was re-measured rather than patched and the
separation signal rose, to 13.2 times chance on the file test and 15.0 on the
citation test. See §2, "The archive, read to the end", and
[`studies/RETRIEVED_LEAN_STUDY.md`](studies/RETRIEVED_LEAN_STUDY.md).

**And before that.** *The `O(1)` LLVQ lookup table*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 24) — the first of the four
candidates the described-surface rounds left standing, and the oldest item on
the original to-do list. The Leech quantiser's 8,192-codeword scan is replaced
by the MOG's own structure — a 16-entry column table, 64 hexacode words, 128
classes of 32 — with the class minimum and the bounded search proved in
`RequestProject/GLM/LLVQTable.lean`, the scan frozen in `analogy.py` as the
thing to agree with, and the subtractive test run over the address book:
**2,118 declarations decoded both ways, 0 addresses changed**, and 107 vectors
agreeing point for point with 0 mismatches. What is *not* claimed is `O(1)`:
the figure is measured (96.8 codeword costs per call against 8,192) and the
worst case — the whole code — is named. `report llvq`; the end-to-end
evaluation gains a case for it and is **131 / 131** with the same 16 boundary
refusals. See §2, "The quantiser's search, replaced by a lookup", and
[`studies/LLVQ_TABLE_STUDY.md`](studies/LLVQ_TABLE_STUDY.md).

**And earlier still.** *The four undescribed parts, and the four branches
they were blocking* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 23) — the whole of
what the round before handed over. A **list** (a hole whose filling is a
sequence, cut at described separators held in two ranks), a **modifier** (a
word that directs how the operands are read without naming one, removed at the
head and in the trailing frame and *nowhere else*), described **trailing
options**, and a **nested** shape (an operator whose sides are themselves a
shape, tightened) are all now description language. With them, the last four
hand-written branches — the equation, the analogy operator, both comparison
forms and the comparative — are **gone** from `runtime/parser.py` and frozen
beside the first three in `language/legacy.py`.

`compare` turned out to need no new shape family at all: given a list slot it
is a fourth **slot** shape. So the picture is now 4 slot shapes, 3 infix
shapes and 1 nested shape — **7 of 20 answerable query kinds described, across
3 families, every one of them read off its description by the runtime**, with
947/947, 201/201 and 480/628 agreement against the frozen branches, 20
narrowing witnesses, 0 false positives, and the one place a description reads
more than its branch did — 148 comparatives written with `relative to` on a
side, which the branch's hand-copied side pattern had never admitted —
declared as a widening and accounted for with 0 left over. The end-to-end
evaluation is unchanged at **130 / 130** with the same 16 boundary refusals.
See §2, "The question shape, made into an object", and
[`studies/LANGUAGE_STUDY.md`](studies/LANGUAGE_STUDY.md) §13.

**And before that.** *The branches deleted, and a second shape family*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 22). The `derive`, `measure` and
`task` branches were replaced by their descriptions, which a described
**preamble** — the courtesies and interrogatives that may stand before an
opening — is what made possible; and a second shape family, an operator that
cuts a string, was measured over three more kinds.

**And before that.** *The surface language driven off descriptions*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 21). A question's **shape** became an
object: an opening, named slots separated by literal words, an optional tail
and named boundaries, read by one generic matcher that knows nothing about any
kind, measured against the parser it restated.

**And before that.** *The recipe made into an object*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 20). A domain is now **described**
rather than coded, and one generic path turns a description into the carriers,
the readings, the widening audit, the query surface and the refusal boundary.
The test was subtractive and it passed: comparison classes, harmonics and
prices were deleted and regenerated from their descriptions alone, 94 of 94
carriers identical and every measured figure unchanged, with the six judgements
the harmonic domain needs counted rather than hidden. See §2, "The recipe, made
into an object", and [`studies/RECIPE_STUDY.md`](studies/RECIPE_STUDY.md).

**And before that.** *The `related_to` residue, finished as a
vocabulary decision* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 19). The 38
triples that were declining because an endpoint reached no dimension are
decided one name at a time in a register of 36 verdicts, the second pass
measures what the decisions change (0 conversions, 6 process repairs, 33
decided declines), and `closure()` reports 39 of 39 accounted for with none
waiting on a lookup. See §2, "The undimensioned names, decided", and
[`studies/DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md).

**And before that again.** *Steps 2–5 of
[`studies/RELATIVE_MEASURE_PROPOSAL.md`](studies/RELATIVE_MEASURE_PROPOSAL.md)*,
which were the whole of what the previous round left open (step 1, the
escalation audit, closed the round before). All four are done: 27 of the 66
`related_to` triples are converted to a measured relation and the other 39
carry the reason they were declined; the comparison-class register holds 45
classes over 11 quantities and 11 scales carrying 64 degree words; the measure
view is added as a **widening**, taking the reading of a use from 12 of 56 to
56 of 56 and giving nothing up, with `RequestProject/GLM/MeasureView.lean`
proving it on `Cumulative.lean`; and the `measure` query answers *how hot* with
an exact magnitude and **refuses** where the registers hold no quantity, with
all four refusals exercised in the test suite and in the end-to-end evaluation.
The two items that closure itself left open are closed too: the register grew
by *volume*, *illuminance* and *luminous intensity*, so all 12 lexicon
adjectives are measurable, and the **comparative** is a query kind of its own,
with `RequestProject/GLM/Comparative.lean` behind it. See §2, "Measure words as
relative measures",
[`studies/RELATIVE_MEASURE_STUDY.md`](studies/RELATIVE_MEASURE_STUDY.md) and
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 18.

**What is now open** is §3.2 and §3.3 below. Of §3.2, "Words as projections"
is now closed for all twelve lexicon adjectives and for the comparative, and
open only as *data*: a thirteenth adjective naming a quantity the register does
not hold would be unmeasurable again, which is the case `replacement_witness()`
keeps measured rather than assumed away. The resolution ceiling found the round
before points the same way: the 283 entries no layer can separate need a
coordinate for the name.

### 3.1 The evaluation finds no gap

The end-to-end set is **134 of 134** and every one of its sixteen refusals is a
`boundary` — a theorem or a stated commitment — rather than a `gap`. The last
gap, `coherence-unregistered-molecule`, is closed: see the fall-through
recorded in §2 above. What remains open is listed in §3.2 and §3.3, and none
of it is a question the evaluation set asks.

### 3.2 Named as untouched

The list is kept in `MASTER_PLAN_ARCHIVE.md` §7.9; this is the same list.

* **The infinite-dimensional half of the VOA bridge — closed.** `VOA.lean`
  builds the state–field map `Y(u, z) = Σ uₙ z⁻ⁿ⁻¹` at the Griess layer of the
  3-dimensional `2A` algebra and proves what that layer carries — truncation,
  skew-symmetry, an invariant form that invariance itself forces,
  self-adjoint modes, nondegeneracy, and the vacuum `(4/5)(e₀+e₁+e₂)` — and
  why that is as far as a finite model reaches: `borcherds_commutator_fails`
  shows the commutator formula at `m = n = 1` fails on the axis triple, so the
  modes the truncation discards are load-bearing. `Heisenberg.lean` now builds
  the other half: the Fock space of one free boson over the exact rationals
  with its creation, annihilation and mode operators, the Heisenberg relation
  `⁅aₘ, aₙ⁆ = m δ_{m+n,0} · id` for all integers at once, state truncation,
  Borcherds' commutator formula on that space, and — the point of the exercise
  — `no_finite_dimensional_model`, a trace obstruction showing that *no*
  nonzero finite-dimensional rational vector space admits the relation at all.
  That is the precise sense in which the finite Griess layer cannot be the
  whole story, proved rather than asserted.
* **`heat : temperature :: force : ?`** is refused with a stated reason rather
  than answered wrongly. An analogy whose operands are spread across registers
  is *not* in general refused — `hot : temperature :: fast : velocity` is
  answered — so what stops this one is the relation: the lexicon carries
  `temperature drives heat`, and looked up from `force` in either direction it
  reaches nothing. Closing it means supplying the relation, not widening the
  dispatch.
* **The `O(1)` LLVQ table — closed, with the claim narrowed.** The table is
  built and is on the quantiser's hot path; what the measurement supports is
  *constant-bounded*, not constant, and the report and the study say so. See
  §2, "The quantiser's search, replaced by a lookup".
* **The Niemeier deep-hole census** — the generalisation of `Golay/Census.lean`
  over the 23 Niemeier lattices, and with it the claim that a *trajectory
  distribution* classifies them.
* **Open vocabulary.** The vocabulary is exactly the registers; there is no
  coordinate for *justice*, and the semantics layer refuses rather than
  inventing one. This is a commitment, not an oversight.
* **Words as projections — closed for all twelve lexicon adjectives.** `hot`
  is still a concept, and now carries a measurement beside it: read against a
  comparison class it is an exact magnitude (363 K for tea, 44 000 K for a
  stellar surface). The reading is a *widening*, so the concept is unchanged by
  it, and the comparative — `is cold in stellar_surface hotter than hot in
  tea` — is a query kind of its own. What remains open is the data, and only
  in the same sense as any register: a thirteenth adjective naming a quantity
  the register does not hold would be unmeasurable again, which is what
  `replacement_witness()` keeps measured. See
  [`studies/RELATIVE_MEASURE_STUDY.md`](studies/RELATIVE_MEASURE_STUDY.md).
* **No geometric item is left on this list.** Three that were on it are
  closed: sigma–delta on the Leech shells with the Gibbs-style rule
  (`reasoning/shell_sigma.py`, `RequestProject/GLM/ShellSigma.lean`,
  `report shells`), the 32- and 48-dimensional lattices
  (`substrate/lattice32.py`, `substrate/lattice48.py`,
  `reasoning/higher_lattices.py`, `RequestProject/GLM/HigherLattices.lean`,
  `report lattices`) — see `HIGHER_LATTICE_STUDY.md` — and the harmonic
  register (`data_objects/harmonics.py`, `reasoning/harmony.py`,
  `RequestProject/GLM/Harmony.lean`, `report harmony`), see
  `HARMONY_STUDY.md`.
* **An economic register — closed.** The one third of the catalogue's
  universality claim that used to be untestable here is now measured:
  21 quoted prices as exact rationals, an exact magnitude bucket proved well
  defined in `LogBucket.lean`, and the verdict `not reproduced` because the
  undecoded control does exactly as well as the lattice. See §2 above and
  [`ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md); the catalogue ledger's
  §6.2 now reads both halves off their studies rather than carrying either as
  `not implemented`.

### 3.3 Ongoing rather than finishable

* **`related_to` as a residue — closed, and the closure is a decision rather
  than a conversion.** 66 of the lexicon's 380 triples are `related_to`, which
  records that a link exists without saying which. 27 convert from the physics
  register alone (6 `same_dimension_as`, 21 `differs_by`); the other 39 are now
  each *decided* rather than merely declined, and `closure()` reports 39 of 39
  accounted for with **0 triples waiting on a lookup**. What remains genuinely
  ongoing is the smaller thing: the lexicon can always grow another vague
  triple, and each new undimensioned endpoint has to be decided by hand in the
  same way. See §2, "The undimensioned names, decided", and
  [`studies/DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md).
* **Sparse chemistry.** 1,257 of 1,652 element cells are filled. The coverage
  module measures the sparsity and widens it by derivation, one linear fit and
  cross-checking, and writes nothing back into the register — deliberately, so
  that an estimate is never mistaken for a measurement.

### 3.4 Named for the next round

This section is the one to read first on the next development push. It is
written up as the proposed next phase in
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 28, which points back here.

The round just closed took neither of the two candidates below: it took the
question underneath them both — whether the substrate can do work rather than
hold a table — and answered it twice, once for retrieval and once for steering
a loop (§2, and Phase 27). Both candidates therefore still stand, in the order
they are worth attempting, and the retrieval result sharpens the first one:
what the geometry demonstrably earns is an *exact* guarantee, so a deep-hole
classification is worth attempting in the same form — a statement that can be
proved complete — rather than as a ranking.

The item that used to stand here — the `O(1)` LLVQ table — is closed and is §2,
"The quantiser's search, replaced by a lookup"; so is the round that followed
it, the archive read to the end, which is §2, "The archive, read to the end"
and which added a third of the Lean development without changing an answer.
The third of the items named below is closed too: the stability measurement is
`reasoning/stability.py` against `RequestProject/GLM/Stability.lean`, with the
nearest-point ties it exposes measured in
[`TIE_BREAK_STUDY.md`](studies/TIE_BREAK_STUDY.md). The language layer has
reached the point its own measurement says it should stop at: the thirteen
remaining query kinds are not shapes of any family, and forcing them would make
the coverage figure meaningless. So the next round is **not** a fourth shape
family. Two candidates stand, in the order they are worth attempting.

**1. The Niemeier deep holes, found rather than tabulated.** This is the last
purely geometric item on the list, and the one the supplied brief asks for in
its third experiment: whether the deep holes of a Niemeier lattice can be
*classified from the distribution of trajectories* that reach them instead of
read out of a table. `Golay/Census.lean` is the census for one lattice and
`reasoning/deep_holes.py` walks to a hole; what is missing is the
classification. The falsifiable form is the one to hold it to: if the
distribution recovers the known census for one lattice it is a method, and if
it recovers it for only that one it is a coincidence — and either result is
worth writing down.

**2. `heat : temperature :: force : ?`** — the relation an analogy asserts,
read off the registers rather than off the coordinates. The analogy shape is
described now, so what is missing is the *semantic* half: the lexicon carries
`temperature drives heat`, and from `force` in either direction it reaches
nothing, which is why the question is refused with a stated reason rather than
answered wrongly. Closing it means supplying the relation and saying what makes
a relation admissible — not widening the dispatch. It is testable against the
evaluation cases that already exist.

**3. A stability measurement under declared exact perturbation — closed.** Every figure
in the project is exact by directive D7, and the question that has never been
asked is how far an address moves when its input is perturbed by a *declared
exact* amount. The LLVQ table makes this cheap for the first time — the corpus
now decodes in one pass rather than 8,192 codeword costs per call — so the
measurement is a sweep over the address book with the perturbation stated as a
rational, not a floating-point experiment. That is what `reasoning/stability.py`
now does: the two certificates of `Stability.lean` transcribed and checked in
exact rational arithmetic with no square root anywhere, the sharp radius
computed as the least distance to a bisector, and past it a perturbation
*built* rather than asserted — one strictly inside the radius that leaves the
address alone, one just outside it that does not, both decoded by the
quantiser. The addresses whose radius is zero are exactly the nearest-point
ties, and what breaking those by index costs is
[`TIE_BREAK_STUDY.md`](studies/TIE_BREAK_STUDY.md).

Whichever is taken, the discipline is the one Phases 20–24 were held to: the
thing must be *described* or *measured* rather than asserted, what does not
generalise must be counted rather than hidden, the path it replaces must be
frozen so the new one has something to agree with, and the end-to-end
evaluation must return the same answers and the same refusals.

What should **not** generalise is the judgements: which brackets count as
ordinary cases, which factor basis may explain a dimensional difference, which
pole a word names, and which phrasings count as the same question. That is
enforced rather than intended — a `Phrasing` cannot be constructed without the
sentence that justifies it — and the count of those sentences is a reported
figure, now **15**, **13** and **4** across the three shape families. A
universal method should make such rules cheap to state and impossible to state
twice, not eliminate them.

The other limit to name explicitly is **coverage**, and it is still two figures
rather than one: three of the eight registers are described, and seven of the
twenty answerable query kinds are, every one of those read off by the runtime.
Nothing measured so far says physics, chemistry, molecules, mathematics or the
lexicon can be described, and a description that had to be bent to fit one of
them would be worth knowing about.

---

## 4. Re-verifying the whole thing

### 4.1 The short way — run only what has changed

**Start here.** Everything below is signed off in
`overlay/.glm_signoff.json`: each test file and each instrument carries the
SHA-256 of everything its last passing result depended on — the file itself,
every package module it imports transitively, the frozen data those modules
read, the documents and Lean sources they name, the test scaffolding and the
interpreter version. If that digest still holds, the result still holds and
re-running it proves nothing. If a single byte anywhere in the closure differs,
the unit is stale and is run again. Nothing is ever skipped silently: `--plan`
says what will be skipped and why, and `--verify` re-checks every signature
without running anything.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.signoff --verify         # what still holds
PYTHONPATH=. python3 -m glm_universal.signoff --plan           # what would run
PYTHONPATH=. python3 -m glm_universal.signoff --run-everything # run just that
PYTHONPATH=. python3 -m glm_universal.tools    signoff         # the summary
```

The seven instruments in the ledger beside the 74 test files are `lean-build`,
`lean-sorry-free`, `lean-copies-identical`, `capabilities`, `benchmarks`,
`evaluation` and `figures`, so the list below is what `--run-everything` runs
when *nothing* is signed off. Editing a document makes exactly the units that
read that document stale — `test_figures.py` yes, `test_substrate.py` no — so
writing up a finding costs one short re-run rather than a quarter of an hour.

### 4.2 The long way — run everything from scratch

What a release check does, and what `--run-all` / `--run-checks-all` do
without consulting the ledger at all. In order, from the repository root; the
last step is the one that catches a document drifting from the code.

```bash
lake build                                                   # 97 Lean files, no sorry
rg -n 'sorry|admit' RequestProject/GLM                       # expect nothing
diff -r RequestProject/GLM overlay/glm_lean/RequestProject/GLM   # the two copies agree

cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q        # the whole suite
PYTHONPATH=. python3 -m glm_universal.capabilities           # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks             # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8    # 134 CLI cases
PYTHONPATH=. python3 -m glm_universal.figures --check        # FIGURES.md is current
PYTHONPATH=. python3 -m glm_universal.figures --write        # regenerate FIGURES.md
```

Spot checks that exercise the runtime the way a user does:

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report analogies"        --verify-tct
PYTHONPATH=. python3 GLM.py -q "report molecules"        --verify-tct
PYTHONPATH=. python3 GLM.py -q "report chemistry coverage" --verify-tct
PYTHONPATH=. python3 GLM.py -q "report semantics"        --verify-tct
PYTHONPATH=. python3 GLM.py -q "report noise"            --verify-tct
PYTHONPATH=. python3 GLM.py -q "report signature"        --verify-tct
PYTHONPATH=. python3 GLM.py -q "report drift"            --verify-tct
PYTHONPATH=. python3 GLM.py -q "report catalog"          --verify-tct
PYTHONPATH=. python3 GLM.py -q "report containers"       --verify-tct
PYTHONPATH=. python3 GLM.py -q "report companion"        --verify-tct
PYTHONPATH=. python3 GLM.py -q "report lattices"         --verify-tct
PYTHONPATH=. python3 GLM.py -q "report shells"           --verify-tct
PYTHONPATH=. python3 GLM.py -q "report llvq"             --verify-tct
PYTHONPATH=. python3 GLM.py -q "report lean"             --verify-tct
PYTHONPATH=. python3 GLM.py -q "report escalation"       --verify-tct
```

The study instruments have their own command line, one module above the core:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools pipeline      # 21 of 21 rows
PYTHONPATH=. python3 -m glm_universal.tools directives    # 8 rules, 0 defects
PYTHONPATH=. python3 -m glm_universal.tools lean-address  # the address book
```

Each returns `VERIFIED True`: the Three Column Thinking template regenerates
the answer's figures in a fresh interpreter and compares them with what was
printed.

---

## 5. The document map

| document | what it is for |
|---|---|
| `README.md` | the repository's front door |
| `STATUS.md` | this file — the current state and the to-do list |
| `MASTER_PLAN.md` | the wiring status, phase by phase, with what recomputes each item |
| `CAPABILITY_ASSESSMENT.md` | what the machine can do, measured rather than described |
| `DOCUMENTS.md` | the index — one line per document, wherever it now lives |
| `studies/ANALOGY_LAYER_STUDY.md` | analogy by named relation |
| `studies/GLM_UNIFICATION_BLUEPRINT_AUDIT.md` | `source_material/glm_unification_blueprint.md` read as a live claim ledger |
| `studies/GLM_STUDY_CATALOG_AUDIT.md` | `source_material/glm_study_findings_catalog.md` recomputed, claim by claim, and given verdicts |
| `studies/GLM_COMPANION_STUDIES_AUDIT.md` | the two companion preprints recomputed against the definitions they state, claim by claim — the finer ledger the catalogue's summary could not support |
| `studies/RELATIVE_MEASURE_PROPOSAL.md` | a proposal, not a result: measure words as relative measures, what is already here and what is missing |
| `studies/RELATIVE_MEASURE_STUDY.md` | the result of steps 2–5 of that proposal: the comparison-class register, the widening measured, and the query that refuses at its boundary |
| `studies/NOISE_EXPERIMENT_STUDY.md` | noise used as the computation: cascaded loops, closed orbits, interacting tones, dither and error feedback through a matrix, all exact |
| `studies/GEOMETRIC_AMBIGUITY_STUDY.md` | the six-fold Golay tie, bundling, collapse, and the chain's dynamics |
| `studies/INFINITE_VALUES_STUDY.md` | reals as processes, and where the value layer stops |
| `studies/INFORMATION_LOSS_STUDY.md` | what a layer boundary costs, made precise enough to prove |
| `studies/ESCALATION_STUDY.md` | the same audit run on every register carrier rather than seven: the chain at scale, and the resolution ceiling it exposes |
| `studies/HIGHER_LATTICE_STUDY.md` | the two rungs above the Leech lattice, and delta–sigma against a shell |
| `studies/LEAN_ADDRESS_STUDY.md` | a deterministic Leech address for every Lean declaration, scored against two null models |
| `studies/ADDRESS_RETRIEVAL_STUDY.md` | the address book made to do work: retrieval measured against six controls, beaten by plain text, and the proved completeness bound it does earn |
| `studies/CONTROLLER_STUDY.md` | the propose–check–refuse loop: every plan re-verified independently, refusals that carry a proof, and what the substrate is worth as a heuristic |
| `studies/HARMONY_STUDY.md` | the harmonic register, and the musical third of the catalogue's universality claim measured against a control it does not beat |
| `studies/ECONOMICS_STUDY.md` | the economic register, and the last third of the same claim — an exact magnitude without a logarithm, and a control the lattice does not beat |
| `studies/HEXCOLOUR_STUDY.md` | the hexcolour address layer audited on the shipped data: distinctness, read-back, agreement with the stored masks, and lookup by address |
| `studies/DENOTATION_STUDY.md` | what the undimensioned names denote: the factor basis swept, the denotation register, and the `related_to` residue finished as a vocabulary decision rather than a failed lookup |
| `studies/RECIPE_STUDY.md` | the recipe made into an object: a domain description, the one generic path from it, and three registers deleted and regenerated from their descriptions with every measured figure unchanged |
| `studies/LANGUAGE_STUDY.md` | the question shape made an object: a question description, the one generic matcher from it, and three query kinds matched by shape in agreement with the hand-written parser over a generated corpus |
| `PROJECT_DIRECTIVES.md` | the standing rules, and the instrument that enforces each |
| `overlay/FIGURES.md` | **generated** — every documented count, recomputed |
| `overlay/README.md` | the package repository's own top-level README, with the archival change log |
| `overlay/glm_lean/RequestProject/GLM/README.md` | the Lean development file by file, and what each one is the specification of |
| `source_material/` — `DYNAMIC_CARRIER_STUDY.md`, `cardinal_geometry_synthesis.md`, `glm_unification_blueprint.md`, `glm_study_findings_catalog.md`, `GLM_Generators_Containers (2).pdf`, `GLM_Iteration_Study (1).pdf`, `geometric_substrate_study.py`, `ToDo_01.txt` | the supplied source material the studies above test |
