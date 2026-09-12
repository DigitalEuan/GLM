# Status


## Tier 0 — the coarse read

**Question.** Where does the work stand now, what is open, and how is it re-verified?

**Verdict.** This is the current state: what is done, what is open, and how to re-verify it.

**Deciding figure.** Every instrument in the table at the head of the document reports its own result on demand.

**Recomputed by.** `glm_universal.signoff.ledger.suite_totals`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

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
> The full note, with what follows from it in practice, is the Positioning
> section of [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md).

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
anything else** — the one piece of work it used to name, the Niemeier deep
holes classified from a trajectory distribution, is **closed** by this round,
and what §3.4 names now is what that round left behind: a separation criterion
still unmet, thirteen unreached types, a conflation the exact reading cannot
see past, and — the largest of them — escalation made the default step of the
query loop rather than one study's ladder. This round asked whether the deep
holes of the Leech lattice can be named from the *distribution of trajectories*
that reach them, answered no at the layer the question was first asked at and
said so, then asked whether that was the geometry or the layer, and answered
yes one layer up. The round before it
was a reconciliation; the one before that took a pre-registered question about
the fine-structure constant and returned a number under its own gate.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phases 21–32 are the items written as work,
and Phase 33 is what §3.4 proposes.

Last reconciled against a full re-run on 2026-09-10.

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
| test suite | `python3 -m pytest glm_universal/tests -q` | **<!--figure:suite-->3,631 tests across 88 of the 89 test files, 13,777 subtests, outside the document check<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **147 / 147** — 131 answered, 16 refused as expected (all `boundary`, no `gap`), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites, every suite above its baseline |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 errored, 0 surprises |
| Lean development | `lake build` (repository root) | 111 Lean files, 32,565 lines, **0 `sorry`** |
| figures | `python3 -m glm_universal.figures --write` | regenerates `overlay/FIGURES.md`; every documented count |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the archive partition, the coverage claim of `ENTRY.md`, every generated block and every derived cache — **current**, no drift |

The test-suite row is the sign-off ledger's own count, recorded by
`python3 -m glm_universal.signoff --release`, which runs each test file in its
own process with the `exhaustive` tests selected. One `pytest` process over the
same tree, with `GLM_EXHAUSTIVE=1` so that nothing is deselected, collects
**3,659 passed, 0 skipped, 16,337 subtests, zero failures** — which is the
ledger's 3,631 plus the 28 tests of the document check the ledger's total
leaves out, because a round that adds a document or a figure fails that check
until the documents are reconciled. Without that switch the `exhaustive`
tests — which certify rather than sample — are reported as skipped with their
reason rather than dropped silently, which is why the ledger's own count is
taken from a run that selects them.

The package is `glm_universal` **v1.17.0**: eleven sub-packages, 127 modules,
**8 registers** holding 1,089 carriers (physics 726, chemistry 118, molecules
51, mathematics 22, lexicon 95, spatial 28, harmonics 28, economics 21) beside
a 45-class comparison register, **21 query kinds**
one of which dispatches **63 report subjects**, and 3 tasks.

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

**Reasoning.** 65 modules. Analogy by named relation, dimensional verification,
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

**The cross-register analogy, answered from a register rather than invented.**
`heat : temperature :: force : ?` was refused for as long as the analogy layer
has existed, because the lexicon carries `temperature drives heat` and reaches
nothing from `force`. `reasoning/conjugate.py` supplies the missing relation as
a *register* rather than as a special case: **7 energy domains**, each row an
intensive effort, the extensive extent it acts through and the transfer of
energy they make, **21 names** over three relations (`effort_of`, `extent_of`,
`conjugate_of`). Every row is checked against the physics register in exact
integer arithmetic — the effort's EXT10 exponents and the extent's sum to those
of energy, and their decimal scales sum to its scale — which is what pairs
pressure with volume and not with area; no name occupies two columns, so each
relation is a bijection and the answer is *derived* in either direction.
`force` occupies the effort column, so the question is `effort_of` read
backwards and the answer is **`work`**. **11** transport questions were put
through it: **8 answered, 3 refused**, each refusal naming which of the four
stated criteria — `determinate`, `role_typed`, `functional`, `grounded` — it
failed. `RequestProject/GLM/Conjugate.lean` proves the register-level facts
(`rel_functional`, `rel_injective`, `forward_unique`, `reverse_unique`,
`no_answer_of_unplaced`) and the two facts about the shipped table
(`dimensionally_sound`, `roles_unique_table`). `report conjugates`. Write-up:
[`CONJUGATE_STUDY.md`](studies/CONJUGATE_STUDY.md).

**Sparse chemistry, decided rather than left blank.** The element register
holds **1,257 of 1,652** cells and the other 395 were simply absent.
`reasoning/element_completion.py` gives every one of them a disposition
without writing anything back. A rule is admitted only when its leave-one-out
mean absolute error is at most **half** that of predicting the field's own mean
and it is scored on at least **20** elements — the control is the constant
rule, so admission claims that the rule found something, not that it fits
closely. **9 of the 14 fields** take one, chosen by measurement with every
other field tried as a predictor; **185** cells are filled by estimate, taking
the completed view to **1,442 / 1,652**; and the **210** that stay empty are
**100** inputs absent, **97** no admitted rule and **13** not derivable from
this register at all. Read at the measured provenance the completed view *is*
the register, cell for cell — checked here and proved in
`GLM.Completion` (`dispositions_exhaustive`, `dispositions_exclusive`,
`readMeasured_eq_base`, `coverage_monotone`, `admitted_halves_the_baseline`).
`report completion`. Write-up:
[`ELEMENT_COMPLETION_STUDY.md`](studies/ELEMENT_COMPLETION_STUDY.md).

**The vague `related_to` triples, and the rule that decides the next one.** The
problem was never the 66 triples the lexicon holds — two earlier rounds decided
those, the second by hand — but that every new one brought the hand work back.
`reasoning/vagueness.py` makes the discipline a router: four routes tried in
order — the dimensional rules, the energy-conjugate register, the admitted
proposer rules, and only then a person, who is handed the evidence rather than
the failure. **34 of the 66** are decided without a person (**27**
dimensionally, **1** by the conjugate register, **6** by the proposer) and
**32** are referred. A proposer rule is admitted only if it fires on at least
**5** of the 36 hand-decided names and agrees with the hand decision on every
one of them: **1 of 4** passed, and the three refused are kept with the named
disagreement that refused them, because that is a finding rather than a
failure. `GLM.Vagueness` proves the router total and single-valued
(`route_mem`, `route_unique`, the four `route_eq_*_iff`,
`all_declined_of_referred`) and the gate sound (`proposal_correct_of_admitted`,
`not_admitted_of_disagreement`). `report vagueness`. Write-up:
[`VAGUENESS_STUDY.md`](studies/VAGUENESS_STUDY.md).

**Open vocabulary, made a door rather than a commitment.** "The vocabulary is
exactly the registers" stood on the untouched list for several rounds as a
stated commitment with no mechanism behind it. `reasoning/admission.py` states
the mechanism: a name is admissible exactly when some **stated** route gives it
coordinates **computed** from a register the machine already checks, and
**grounded** is the clause that refuses. Three routes admit — a name held by
one of the nine registers, a unit expression dimensioned by the unit register,
an expression over register names evaluated by term arithmetic — and the fourth
refuses. Over **27** probes the door admits **20** (11 held, 5 by unit, 4 by
arithmetic) and refuses **7**, and the refusal is *conditional* and names its
condition: `justice` is refused until a register that measures it exists, never
as a matter of kind, and `km/h` is refused because the SI-coherent unit
register cannot finish reading the symbol `h` — a gap in the register, not in
the door. Nothing is typed in at admission time and nothing is written back:
the held vocabulary of **1,093** names is unchanged by having been widened.
`GLM.Admission` proves totality and determinacy (`route_mem`, `route_unique`,
`admissible_iff`), that a refused name is given no coordinates
(`no_coordinates_of_refused`) and that an admitted one's coordinates come from
a register (`coordinates_grounded`). `report admission`. Write-up:
[`ADMISSION_STUDY.md`](studies/ADMISSION_STUDY.md).

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

**The corpus itself, made data.** The same discipline, applied to the prose.
`glm_universal/corpus/` reads every document once: its sections, its links, its
tier-0 block, whether it is generated, and whether it is archive — membership
of the archive being a rule on the path and never a judgement, which is the
executable form of `GLM.Corpus.card_state_add_card_archive`. `DIGEST.md` and
every in-document `<!-- generated: … -->` block are emitted rather than typed,
and rendering is idempotent. All **788** sections carry a feature vector and a
Leech address, so `--ask "…"` returns a shortlist complete up to a stated
radius and an empty shortlist is the proof of absence
`GLM.Corpus.absent_of_shortlist_empty` states. Reading every current-state
document at tier 0 costs about **3,042** words against roughly **208,000** for
the full current state, and nothing below a tier 0 may contradict it.
`python3 -m glm_universal.corpus --check` reports every drift at once and is
the instrument of directive **D10**. Write-ups:
[`ENTRY.md`](ENTRY.md) and
[`CORPUS_ADDRESS_STUDY.md`](studies/CORPUS_ADDRESS_STUDY.md).

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
over **213** stride-selected queries of the **3,187**-declaration corpus, with
chance computed in closed form rather than simulated. At `k = 5` the structural
address finds a relative for **46.0 %** of queries against **6.1 %** for chance
— **7.6×** — and beats the digest (4.7 %), the seeded reshuffle (5.6 %), the
random ranking (5.6 %) and name-substring search (33.8 %). It is then beaten
decisively by a plain lexical control: Jaccard overlap of identifier tokens
reaches **85.9 %** at **57.7 %** precision against the address's 14.6 %. Two
ablations say where the signal lives: the same feature vectors ranked with **no
lattice at all** score **44.1 %** on the very same queries — four ahead at
`k = 10` and four behind at `k = 5` — and a second address built from identifiers
rather than syntax reaches **65.7 %** — so the geometry transports the features
faithfully and adds nothing to them. What it does earn
is exactness: `RequestProject/GLM/Retrieval.lean` proves a completeness bound
that holds on **162,486** measured pairs with **0** violations, and at feature
radius 2 the guaranteed-complete shortlist is **70.5** declarations — 2.2 % of
the corpus — so an empty shortlist is a *proof* of absence
(`filterRadius_eq_nil_certifies_absence`). `report retrieval`. Every table in
the write-up is a generated block emitted from the measurement cache, so it
reports staleness rather than an out-of-date number when the Lean tree moves.
Write-up: [`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md).

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

**Generated rather than stored, and the generators checked.** The supplied
`glm_zero_storage_substrate_v3.txt` proposes dropping the substrate's tables
and regenerating them. `reasoning/generative.py` measures that proposal instead
of adopting it. The idea itself is right and now has a number: the audited
tables cost **9,449,445 bytes** stored against **24,648 bytes** of generators —
about **383 to one** — with every regenerated object compared against the
stored one before the row is emitted; and of the overlay's own **7,316,334**
bytes on disk, **7,296,569** are already caches with input digests, leaving
**19,765** bytes of primary data. The proposed *generators*, though, mostly
fail their own claims. The zero-storage Leech sieve is **sound** —
`GLM.ZeroStorage.v3Sieve_sound`, proved rather than sampled — and **99.4 %
incomplete**: it keeps **1,152 of the 196,560** minimal vectors, because its
"Construction B" test asks all 24 coordinates to agree mod 4 rather than asking
the disagreeing coordinates to form a codeword, which admits only the empty and
all-ones words. `v3Sieve_iff` states exactly what it does generate
(`IsLeech x ∧ UniformMod4 x`, a genuine sublattice), and `octadVec_not_v3Sieve`
is a kernel-decided witness of a minimal vector it loses. The one-line repair
(`corrected_sieve`) agrees with the package's own membership test on **196,656**
vectors, **96** of them outside Λ. The snap built on the sieve is worse than
incomplete: on general-position probes it returned a non-lattice point **4 of
4** times, always through a fallback its docstring calls trivially correct and
`fallbackVec_not_isLeech` refutes; the exact coset decoder added beside it
(`exact_snap`) is inside Λ on every probe and within the squared covering
radius **16** every time. Of the script's three stated accuracy claims for
generated reals, **0 hold** — ln 2 yields 9 bits where 256 are claimed, γ's
generator is wrong rather than slow, and the Babylonian denominator doubles in
length each step, so the module's default of 64 iterations cannot be run. The
dyadic tower's contract is the one that survives, and is proved:
`dyadic_surrogate_error`, `dyadic_exact_iff_den_pow_two`, and
`dyadic_value_not_strictMono` for the claim that does not. `report generated`
is the **52nd** report subject and the evaluation's **135th case**, run through
the CLI the way a user runs it; the set is **135 / 135** with the same 16
boundary refusals. Write-up:
[`ZERO_STORAGE_STUDY.md`](studies/ZERO_STORAGE_STUDY.md).

**And then rebuilt as a script that runs.** The audit's findings are now a
single standalone file, `studies/scripts/glm_zero_storage_substrate_v4.py` — no imports beyond
the standard library, no dependency on the overlay, `int` and `Fraction`
throughout, no RNG. It keeps the parts that worked and repairs the parts that
did not: the Golay code is generated from the quadratic residues mod 11 (**36
bytes** of generator rows, weight distribution 1 / 759 / 2576 / 759 / 1),
membership is the three repaired congruences, the whole shell of **196,560**
minimal vectors is streamed from the code and every one of them is of norm²
**32** and accepted by the test, the snap is an exact coset decoder that is
inside Λ₂₄ and within the squared covering radius **16** on every probe and
has **no nearer neighbour among the 196,560** minimal vectors, and a real
number is a process with a contract — `x.at(k)` within `2⁻ᵏ`, denominators of
`k + O(1)` bits — which π, e, √2, φ, ln 2 and γ all meet at `k = 8, 32, 96`.
The "Niemeier portal" is replaced by the object it was reaching for: the
**sextet**, verified on all **10,626** tetrads (six-part partitions, every
pairwise union an octad, **1,771** distinct sextets), with the old detector's
label shown to be constant. The storage audit reproduces **9,449,445 →
24,648 bytes**, about **383 : 1**, each row emitted only after the regenerated
object was compared with the stored one. `python3
studies/scripts/glm_zero_storage_substrate_v4.py --test` runs the lot in about five seconds and
exits 0. On the Lean side, `GLM.ZeroStorage.refinedSieve_iff_isLeech` proves
that the script's deterministic membership test — parity read off coordinate 0,
no search, no table — decides exactly `Λ₂₄`. The v3 draft is kept for the
record at `source_material/glm_zero_storage_substrate_v3.txt`.

**And then the last table removed, and the cost of generating measured.**
`studies/scripts/glm_zero_storage_substrate_v5.py` closes the one corner of the claim v4 left
open and prices what it does. Membership no longer consults the 4096-word set:
the Golay code is self-dual, so the same **12 generator rows** are a
parity-check matrix and a word is a codeword exactly when its **12 parity
checks** vanish — **36 bytes**, twelve word operations, and the 12-bit
**syndrome** for free when it is not. `GLM.ZeroStorageV5.syndromeZero_iff_isGolay`
proves the equivalence and `syndromeSieve_iff_isLeech` carries it to the whole
membership test; before the lookup was removed the two routes were compared on
the **196,560**-vector shell (**0 disagreements**), on 1,536 deliberate
non-codewords, on the entire **16,777,216**-word space (4096 accepted, and the
same set again by exact null-space elimination), and on the Lean development's
own, differently-generated rows. Every answer now carries an exact integer
**cost ledger** — 13 primitives counted, never wall-clock, reproducible byte
for byte — so the storage audit is bytes stored against bytes of generator
**plus the tax to recover one item**: one membership decision is 12 parity
checks, one codeword about one XOR, one nearest-point decode about **50,705**
primitives against **217,272** for the unpruned search (the coset search is now
pruned by a running bound, storing nothing, and returns the same point at the
same distance on every probe). **NRCI** is given one definition —
`1 − √(Σr²/Σx²)`, reported as an exact dyadic enclosure of width `2⁻ᵏ` and as
an exact rational squared form — and measured on three named streams, with the
proved `1/N` bound printed beside the Δ-Σ figure and checked at **every** `n`.
The register now retargets **continuously**: `ds_track_bound` and
`ds_track_moving_target` prove that keeping the accumulator preserves
`|average − mean target| < 1/N` for a moving target and costs exactly the mean
deviation against a fixed one, where the v4 zeroing register held one tick of
evidence on the same trajectory. Second- and third-order noise shaping is
implemented and **measured, not assumed**: through a triangular read-out window
the *guaranteed* bound falls from `1.9 × 10⁻³` (order 1) to `1.3 × 10⁻⁵`
(order 2) at N = 1024, while order 3 at these coefficients is unstable
(`max|e|` reaching **1.4 × 10⁷**) and no decay is claimed for it. The coset
decoder's exactness argument is now formal end to end: the cheapest single ±4
repair *is* the minimum inside a coset (`coset_cost_ge`,
`coset_repair_attained`), that minimum is the coset's nearest point to a
rational target (`coset_min_cost`, `coset_min_attained`), and the 8,192 cosets
exhaust `Λ₂₄` (`leech_in_coset`, `lattice_dist_ge`) — so the search returns the
nearest lattice point rather than the best of what it looked at.
`python3 studies/scripts/glm_zero_storage_substrate_v5.py --test`
runs the whole self-verification in about six seconds and exits 0. Write-up:
[`ZERO_STORAGE_V5_STUDY.md`](studies/ZERO_STORAGE_V5_STUDY.md).

**The dropped work, restored, and the second reading of the archive closed.**
The tree handed over at the end of the retrieval round was missing part of what
that round had produced: Lean files, their test files and several study
documents had not survived the handover, and a recovery bundle is what came
back (the bundle itself has since been removed, every file it held having been
checked against the tree; [`ENTRY.md`](ENTRY.md) records that check).
Everything in it has been put back and re-verified rather than taken on trust —
the Lean sources build against the pinned Mathlib with no `sorry`, and every figure their tests pin was recomputed from the
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
the 3,187-declaration corpus: **3,187 / 3,187 declarations read back
exactly, 0 coordinate errors**, 2,823 distinct addresses, and nearest-by-address
shares a file **624 / 3,187** against 33 for the digest control and 30 for the
seeded reshuffle, with chance at ≈ **1.18 %**. Three citations in the
combiner study pointed at a namespace the theorems do not live in and were
corrected to `GLM.Golay24`.

**The Lean development.** 111 files, no `sorry`. Layer theory and the four
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
the 3187 declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly 3187/3187 with 0 coordinate errors;
2823 distinct addresses, and the quantiser adds no conflation of its own;
nearest-by-address shares a file 624 times against 33 for a SHA-256 control and
30 for a seeded reshuffle, with chance at ≈ 1.18 %. `report lean`.
Write-up: [`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md).

**The wobble landscape, pre-registered and measured.** The question was
whether the fine-structure constant's arithmetic signature is *distinctive*
within the space the substrate permits, and the discipline was to write the
statistic, the nulls, the gate and the decision tree down and commit them
before the measuring module existed. The statistic is the stage-0 long-gap
frequency of the Sturmian word the delta–sigma loop emits, `S(x) =
frac(1/frac(x))`, taken from the closed-form three-distance spectrum rather
than from a simulation and checked against a 20,000-bit run (144 gaps, lengths
{137, 138}, 5 long predicted and 5 observed). **The verdict is B = 1.79 bits**
against the magnitude-matched stride null — all 1,066 exact rationals `j/10⁷`
in `(1/138, 1/136)`, of which **77** deviate at least as much as alpha, a tail
of `77/1066`, 3.79 bits raw and 1.79 after correcting for the 4 statistics
tried. The gate fixed in advance was `B < 1` not evidence, `1 ≤ B < 3` weak,
`B ≥ 3` continue, so **the landscape enumeration was not run**. It is not a
derivation of alpha and not a claim that the substrate selects it. Two older
readings were corrected on the way: the "wobble entropy 0.062" is exactly
`H2(alpha)`, a function of the magnitude alone, and the continued fraction of
`1/alpha` computed from CODATA 2022 is `[137, 27, 1, 3, 1, 1, 18, 1, 8, 1]`,
not the `[137; 28, 1, 1, 2, …]` that was quoted — 137 is `a₀` and nothing more.
The Golay reading was corrected too: `4096 × 2325 = 9,523,200` of `2²⁴` words
lie within distance 3 of a codeword, so `d_min ≤ 3` is the **majority case** at
`2325/4096`, and alpha's `d_min = 0` at depths 24, 48 and 72 is worth **0.00
bits** against the magnitude-matched null, every one of whose 1,066 members
reproduces it. `reasoning/wobble_landscape.py` computes all of it in exact
integers and `Fraction`s with no float anywhere, behind a digest-guarded
measurement cache; `RequestProject/GLM/WobbleLandscape.lean` proves the parts
that are theorems rather than measurements — the two-length gap bound
(`gap_mem_pair`, `gap_image_card_le_two`), the sphere-count identity behind the
Golay null on the substrate's own code (`golay_code_ball_count`,
`golay_ball_majority`) and the monotonicity of the bit score in the tail
probability (`bitScore_antitone`, `corrected_antitone`). `report landscape`,
`python3 -m glm_universal.tools landscape`. Write-up:
[`WOBBLE_LANDSCAPE_STUDY.md`](studies/WOBBLE_LANDSCAPE_STUDY.md).

**Geometry classified from trajectories, and the layer that was doing the
hiding.** Two rounds on one question, both pre-registered before the measuring
code existed. The first asks whether the *distribution of trajectories* that
arrive at a deep hole of the Leech lattice can name the hole's Coxeter–Dynkin
type: a declared 240-start ensemble, the arrival shares as the statistic, a
nearest-reference rule with a stated refusal, and four controls of which the
plain vertex count — `24 + k` vertices for `k` components — is the competitor
that matters. It names **15 of 44** queries against **11** for the vertex
count, **12** for the uniform-profile ablation, **4** for the digest control
and **3** for the reshuffle, so it beats every control — and the round stops
anyway, because the pre-registered sanity query fails: change only the ensemble
seed and just **3 of 10** holes keep their label
(`reasoning/deep_hole_classifier.py`, `DeepHoleClassifier.lean`,
[`DEEP_HOLE_STUDY.md`](studies/DEEP_HOLE_STUDY.md), `report hole classifier`).

The second round asks whether that was the geometry or the **layer it was read
at**, which is the question
[`INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) exists to
make answerable, and escalates the reading along a ladder: the same shares,
those shares **widened by the strays the first round discarded**, the exact
rational measure of emission distances compared by an exact 1-Wasserstein
integral, and the two joined — each at 240, 480, 960 and 1920 nested starts, so
one ensemble per centre and seed supplies every cell. The sanity count climbs
`3 → 5 → 8` on budget alone and `3 → 4 → 6` on width alone, reaches **9 of 10**
at the best pre-registered cell and **10 of 10** — the gate — at the joint
reading with 1920 starts, where the full query set comes out **40 of 44**
against **12** for the vertex count, **7** for the digest control and **0** for
the reshuffle, with the mean rank of a query's own reference **1.09**. The
passing cell is an extension rung decided after the twelve declared cells were
measured; it is labelled as one in every table and counted in the multiplicity
correction, which is why `m = 20`. Two things are recorded against it: the
rational reading alone *conflates* `A_1^24` with `A_2^12` — both emit no stray,
so their whole distance measure is one atom — which is a capacity boundary
visible as a pair of names rather than as a bound; and the separation criterion
`ρ = 2W/B < 1` still fails everywhere (best `2.59`), so the classifier now
names holes and still cannot certify an absence — faithfulness needs
`r ≥ 0.0659` where separation allows `r < 0.0179`
(`reasoning/deep_hole_escalation.py`, `DeepHoleEscalation.lean`,
[`DEEP_HOLE_ESCALATION_STUDY.md`](studies/DEEP_HOLE_ESCALATION_STUDY.md),
`report hole ladder`).

**Cumulativity as a shipping condition.** The information-loss round found a
real design flaw by asking whether a layer refines the one below it, and
reported it rather than patching it. That question is now a rule every layer
family has to satisfy before it ships, and an instrument that checks it:
**3** declared families, **2** of them shipped, **7** declared refinement edges
verified on their probe sets and **2** declared non-edges witnessed, with **0**
defects in a shipped family. The rejected integer reading is kept in the
registry precisely so the check has a defect to catch. The rule also keeps the
two failure modes apart: a conflation is *not* a defect but the rung's
resolution — **32** conflated pairs are reported beside the edges as
resolutions — and `RequestProject/GLM/CumulativityRule.lean` is why. Reading a
layer's view again cannot repair a conflation (`factored_conflates`,
`factor_refined_by`); reading the carrier again can, and only if the second
reading sees the pair (`join_separates`, `join_needs_a_second_reading`); and a
chain checked pairwise refines across any gap (`refines_of_le`), which a
cumulative construction satisfies by construction
(`refinementChain_cumulativeTower`). `reasoning/cumulativity.py`,
`report cumulativity`, `python3 -m glm_universal.tools cumulativity`.
Write-up: [`CUMULATIVITY_STUDY.md`](studies/CUMULATIVITY_STUDY.md).

**The four failures the escalated deep-hole reading leaves, diagnosed.** The
escalated reading names 40 of 44 and certifies nothing, and the round asks one
question about the four it misses: which of four mechanisms, declared before
the measuring code existed, accounts for them — and is it the same mechanism
that keeps the separation ratio `ρ = 2W/B` above 1? It is. All **4** failures
are **rank-2 near misses** on a closest reference pair, which
`GLM.DeepHoleFailure.failure_pair_close` says they had to be, and the type
whose within-type spread stalls the ratio — `D_6^4` at `W = 0.0659` against a
closest separation `B = 0.0358`, so `ρ = 2.5943` — is the type the failures
belong to. So the two open questions are one mechanism, not two. The global
negative stands: over **55** declared deletions the ratio gets no lower than
**1.4784** and reaches the criterion nowhere. Read type by type it is not all
negative — `per_type_correct` certifies a type's own answers wherever that
type's own criterion holds, and **3 of 10** types satisfy it — and
`per_type_absent` states the absence the rounds have been short of, under a
faithfulness hypothesis the data does not currently support. `resolves_of_subset`
and `separation_mono` are why the deletion sweep is reported as a floor rather
than as a way of earning the certificate. `reasoning/deep_hole_failures.py`,
`RequestProject/GLM/DeepHoleFailure.lean`, `report hole failures`. Write-up:
[`DEEP_HOLE_FAILURE_STUDY.md`](studies/DEEP_HOLE_FAILURE_STUDY.md).

**Escalation, as a step of the ordinary query loop.** The deep-hole rounds were
the only place in the repository where a refusal was answered by raising the
resolution of the reading instead of stopping. It is now a step of the query
loop: a ladder of three rungs with declared integer costs (`L1` the register
reading at 1, `L2` the semantics reading at 2, `L3` the neighbourhood reading
at 4), declared per query kind rather than one tower for everything, with the
classification of a refusal happening *before* the climb. Both gates are
measured over the whole evaluation set rather than argued: **no answer moves**,
**none becomes more expensive**, and **no principled refusal is converted** —
of the declared refusals, the ones classified as an absence are the only ones
the loop may escalate, the rest are returned at the layer they were classified
at by declared markers. And it buys something: of **18** declared probes, **4**
resolve *above* the first rung (`nearest to k_B`, `describe energie`,
`describe oxigen`, `nearest to velocty`) at costs of 3, 5, 5 and 5 against 1
for a direct answer, and **2** refusals come back as certified absences within
a radius of 2 edits. `RequestProject/GLM/EscalationLoop.lean` proves the loop
rather than exercising it: a principled refusal is preserved whatever the rungs
above would have said (`climb_principled`), an answer at a rung is a statement
about the rungs below it (`climb_answers_least`), a refusal from a fully
climbed ladder is a statement about every rung (`climbFrom_refused_all`), a
direct answer costs exactly the first rung (`climb_direct_cost`), and a climb
costs at least the first rung and never more than the whole ladder
(`climbFrom_cost_ge`, `climb_total`) — which is also the termination statement.
`reasoning/query_escalation.py`, `runtime/escalation_loop.py`,
`report query escalation`. Write-up:
[`QUERY_ESCALATION_STUDY.md`](studies/QUERY_ESCALATION_STUDY.md).

**The reverse-call planner, kept in the sandbox.** An older proposal in the
source material inverts the runtime's order: instead of deciding a query's
*kind* and dispatching one solver, parse the string into a problem and let a
planner select every tool whose declared precondition the problem satisfies.
It is built, measured against two declared gates, and **not promoted** — which
is the result. The safety gate holds: the planner answers **10 of 15** declared
tasks, **all 10** independently checked by a second tool, **5** of them
questions the plain runtime refuses, and no principled refusal ever reaches it.
The utility gate does not: of the evaluation refusals it is offered it
correctly refuses every one, so under the declared fallback rule it would add
nothing to the shipped system today. Directive **D14** is what keeps it
honest — `glm_universal/sandbox/` is imported by nothing the system computes
with, which is checked with `ast` over the sources, the three
documentation-layer exceptions being lazy imports inside the code that reports
on it; its pipeline
row declares that wiring is *forbidden* rather than missing, so it can be
complete without being reachable. Write-up:
[`REVERSE_CALL_PLANNER_STUDY.md`](studies/REVERSE_CALL_PLANNER_STUDY.md).

**The review sweep — which stalled results are worth re-reading, decided
first.** Directive **D13** lets a stalled result be re-read at a finer layer
and then constrains the practice: rank candidates by whether there is an
identifiable *discarded quantity* at the coarse reading, not by how
disappointing the original result was. Nothing implemented that clause, so the
whole standing set is now ranked by it, **before** the next re-reading rather
than after it: **8** stalled results, **1** licensed for a re-reading
(`retrieval-hit-at-5`), **2** already recovered that way (`deep-hole-per-type`,
`rational-conflation`), **1** that no reading settles and that needs a theorem
(`faithfulness-radius`), and **4** that discarded nothing — for which
escalation is not licensed and each entry names what is needed instead. **0**
entry defects: every entry's document exists, and every claimed discarded
quantity has somewhere it is reported. `reasoning/review_sweep.py`,
`report review sweep`, `python3 -m glm_universal.tools review`. Write-up:
[`REVIEW_SWEEP_STUDY.md`](studies/REVIEW_SWEEP_STUDY.md).

**Generate, don't store — with a proof attached.** The supplied PCGS scripts
propose a stronger contract than procedural generation: a compact description
answers with a value, *evidence that the value is right*, and *an exact cost*.
Neither script runs here — both import a package from an absolute path outside
the repository — so the mathematics in them was rewritten against this
project's own substrate as `reasoning/pcgs.py`, and each of the six systems now
states the kind of evidence it has. **Three are proved**: the cost algebra is a
commutative monoid with additive totals and the information axis is the tight
description bound (`GLM.PCGS.Cost.plus_comm`, `algebraicTotal_plus`,
`bitsFor_le_iff`); a Reed-Muller `RM(1,m)` codeword with nonzero linear part hits
exactly half its evaluation points, by a coordinate-flip involution, so the
minimum distance `2^(m-1)` is read off the generator and never off a codeword
table (`rmWeight_of_ne_zero`, `rm_min_distance`); and a reversible step erases
nothing while a rational lower bound for `ln 2` keeps the Landauer figure a
lower bound (`bitsErased_reversible`, `landauerEnergy_le_of_le_log_two`).
**One is a checked transcription**: `ntt_intt` proves the transform pair
generated from `(p, g)` inverts, and the radix-2 algorithm that actually runs is
checked against that definition on every input rather than claimed to be it.
**Two are tested and labelled as tested** — a stencil operator and a transducer.
Caching is priced rather than deprecated: `breakevenQueries_spec` proves
`ceil(store / (generate - lookup))` is exactly the threshold, which puts the
4,096-word Golay table at **8,937** membership queries. Three claims of the
source scripts do not survive checking — "self-dual iff `m` is odd" (only
`m = 3`), an efficiency of zero returned where the ratio is undefined, and a
float fallback in the information bound above 65,536 symbols — and one is
improved: `ln2Fast_le_log_two` proves *every* partial sum of `sum 1/(k 2^k)` is
below `ln 2`, at 64 terms to better than `10^-21`, where the script's
alternating sum at a hundred terms is still wrong in the third decimal place.
`tests/test_pcgs.py` (45 tests, 1,048 subtests). Write-up:
[`PCGS_STUDY.md`](studies/PCGS_STUDY.md).

**What a round costs, measured and cut.** Everything this repository claims is
recomputed from the tree, and most of that recomputation was being repeated on
parts that had not moved: each cache was keyed on a digest of its *whole*
input, so a change to one file threw away all of the derived work.
`glm_universal/corpus/cost.py` states the chain's cost in exact counts rather
than timings, and three links of it were cut. **The address books are
incremental.** An address is a function of the feature vector and of nothing
else — `GLM.Address.address_congr` — so a vector decoded before may be reused,
and a file that has not moved costs nothing: rebuilding both books from nothing
decodes <!--figure:rebuild-decodes-from-nothing-->7,726<!--/figure--> vectors
and rebuilding them against the stored books decodes
<!--figure:rebuild-decodes-now-->0<!--/figure-->. A book refuses to seed from
one written at a different schema, scale or cap, it reports how many entries
were seeded, reused and freshly decoded, and the reuse is audited rather than
assumed — each rebuild re-decodes a sample of what it reused and reports any
that moved. **The planner's report is taken once.** Five generated blocks quote
the reverse-call planner's report, and the document check used to re-take it
for each of them, <!--figure:planner-reports-per-check-->5<!--/figure--> passes
over the evaluation set for a check that changes nothing; it is now stored
beside the digest of the import closure of `glm_universal.sandbox.planner`,
which `glm_universal.signoff.ledger.code_store` computes, and taken 0 times per
check. The promotion checklist's *deterministic* line still re-derives from the
uncached function, so it cannot compare a stored answer with itself, and
`tests/test_sandbox_planner.py` reads the source to require that.
**Numbers inside sentences are emitted rather than typed.** The generated-block
mechanism now works at the size of a phrase — a pair of HTML comments naming a
figure, so a reader sees only the number — and the markers are placed across
the documents that quote a count the code can produce; how many there are, and
what the registry holds, is itself a generated block of the study. A marker
naming a figure nothing emits is a reported defect, and a passage marked as the
record of a past round is left exactly as it was written, because a record that
updates itself is not a record. **One command does the chain in the one
order that converges**: `python3 -m glm_universal.corpus --refresh` rebuilds the
Lean address book, the document address book, the measurement cache, then the
generated documents, blocks and figures, repeating until it settles and
finishing with a fixed-point check; measuring before the book is rebuilt is
refused outright by `measurements.StaleAddressBook` rather than producing the
previous tree's figures under the current tree's digest. **The Lean tree's
second copy is generated** on the same terms as `DIGEST.md`:
`python3 -m glm_universal.tools lean-mirror` reports whether
`overlay/glm_lean/RequestProject/GLM` agrees with the compiled copy and
`--write` makes it agree, so the two are no longer kept in step by hand.
Write-up: [`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md).

**The standing rules, as instruments.**
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) states fourteen rules and
names the instrument for each. `reasoning/directives.py` parses that file and
gives each instrument a live verdict (`report directives`) — **14 of 14** with
every named instrument present; `reasoning/pipeline.py`
reads the stage each piece of work has reached off the tree rather than from
prose — **30 of 30 rows** through all six stages (`report pipeline`), one of
which is the sandbox row that declares wiring forbidden rather than missing;
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

**Closed this round.** *The cost of keeping the claims current, measured and
cut.* Nothing the system answers moved: this round was about the machinery that
re-derives the answers, which had grown expensive enough to shape how a round
was worked. Six pieces of work, all recorded in §2 above, and the defect that
running their tests exposed:

* **the planner report is cached.** The sandbox planner's report was recomputed
  once for each of the five generated blocks that quote it, on every
  documentation check — five passes over the evaluation set, about a quarter of
  an hour. It is taken once and stored beside the digest of the code it is
  derived from; the corpus check now takes **28 seconds** on this tree. The
  determinism line of the promotion checklist was rewired to bypass the cache,
  so it still re-derives rather than comparing a stored answer with itself;
* **both address books are incremental.** An unchanged entry is reused from the
  previous book instead of the tree being re-decoded, a book written at a
  different schema, scale or cap is refused as a seed, and every rebuild
  reports what it seeded, reused and decoded afresh. Rebuilding the declaration
  book went from about sixty-five seconds to under a second, and the result is
  byte-identical to a full decode — which the exhaustive run of
  `tests/test_lean_address.py` checks by decoding every address from nothing;
* **one ordered rebuild command.** `--refresh` does the whole chain in the only
  order that converges and finishes with a fixed-point check, and the
  measurement writer now refuses a stale address book outright, so the ordering
  trap that cost a full cycle two rounds ago cannot recur silently;
* **inline generated figures.** A number inside a sentence is emitted rather
  than typed, from a registry of the figures a marker may name, with the
  history and current regions stated once so that a passage recording what a
  past round measured is never rewritten. Running it corrected real drift
  rather than confirming the prose:
  the stale test-file count in five places, and two different stale
  evaluation-case counts;
* **the chain itself is a study and a module** — what a one-file change
  actually invalidates, in exact counts rather than timings:
  [`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) and
  `glm_universal/corpus/cost.py`, linked from `ENTRY.md`;
* **the mirrored Lean tree is generated** rather than hand-synced:
  `python3 -m glm_universal.tools lean-mirror` reports that the two copies agree
  or `--write` makes them agree, and the `lean-copies-identical` instrument
  still checks the invariant independently.

Two defects were exposed by running the new tests, and both are fixed at their
root rather than waived. The cache factory that keys a derivation on a module's
code closure had been put in `derived.py`, which pulled the documentation prose
into the dependency closure of units that read none of it; it now lives beside
the ledger that owns that notion of a closure, as
`glm_universal.signoff.ledger.code_store`. And the isolation check of
directive **D14** reported `corpus/cost.py` as a violation: it reports how
often the planner's report is taken, so it imports the sandbox — lazily, inside
the function that reports on it, which is exactly the exception D14 declares,
but it had not been added to the declared list. It is declared now, so the
exceptions are the three modules of the documentation layer rather than two.

Everything was then re-earned on the final tree. A release run with the
exhaustive cases on passes **all 89 test files** and **all 7 instruments**, and
the complete-run sentence the documents quote is re-measured at
**<!--figure:suite-->3,631 tests across 88 of the 89 test files, 13,777 subtests, outside the document check<!--/figure-->**;
one `pytest` process over the same tree with `GLM_EXHAUSTIVE=1` reports
**3,659 passed, 0 skipped, 16,337 subtests, zero failures**. Nothing the system
answers moved: `lake build` completes over
**<!--figure:lean-files-->111 Lean files<!--/figure-->** with **0 `sorry`** in
both copies, the end-to-end evaluation is **147 / 147**, the benchmarks
**2,389 / 2,390**, and the probes 33 with 20 holding.

**Closed the round just before.** *Five pieces of work finished, and the four
defects finishing them exposed.* The round added the cumulativity rule, the deep-hole
failure study, the escalation loop, the sandbox planner and the review-sweep
register — three Lean files, five modules, five studies, five test files and
five pipeline rows, all recorded in §2 above. Closing it out turned up four
things that were wrong rather than merely undocumented, and each is fixed at
its root rather than waived:

* the four new report subjects had **no evaluation case**, so the rule that
  every subject is exercised end to end was failing; four cases are added and
  the set is now **147** questions;
* the isolation check for the sandbox compared `ast` nodes across two separate
  parses of the same file, so *no* import could ever be recognised as lazy and
  the declared documentation-layer exceptions were reported as violations; the
  check now decides laziness inside the parse the import was found in;
* the pipeline's two stage tests did not know about the `wire_expected=False`
  flag the sandbox row needs, and read "complete but unwired by design" as a
  contradiction; they now require such a row to name no subject and no
  column-3 template, which is the stronger statement;
* the escalation study's classification table asserted that every declared
  refusal of the evaluation set is refused by the runtime, and two of them are
  refusals *in prose* — answered, with the refusal as the content. The tests
  now say so, which is what the study's own "14 of 16 classified
  non-escalatable" already counted.

The review-sweep register's own use of `importlib` was likewise declared in the
purity audit's list of permitted standard-library roots rather than hidden
behind a dynamic call.

*Finishing that round* — the figure sweep, the generated artefacts and the
complete run — turned up three more of the same kind, all fixed here rather
than recorded as known:

* the evaluation's own `report query escalation` case still demanded the
  phrase *143 evaluation cases* of an answer the runtime now gives as **147**,
  so growing the set had quietly broken the case that reads it; the case, the
  two tests that pin the same figure and the study's tier-0 line now all say
  147, and the end-to-end evaluation is **147 / 147** again;
* `runtime/escalation_loop.py` cited two Lean theorems that do not exist —
  `first_resolving_terminates` and `cost_monotone`, names from the design
  sketch rather than from the file. The audit that requires every `GLM.…` name
  quoted in the package to resolve caught both; they are now
  `climb_total`, `climbFrom_cost_ge` and `climb_direct_cost`, which are the
  statements actually proved, and the study's Lean section names them too;
* the hand-written passages of the two address studies, the capability
  assessment's per-kind table and its report-subject and analogy lines had
  drifted from the re-taken measurements; all are brought to the corpus as it
  now stands — **3,135** declarations across **110** files, **65** report
  cases, `analogy` at **11 / 11** — and the worked examples of the address
  study were re-run rather than re-picked: this round nothing moved at all,
  neither an address nor a neighbourhood.

<!-- figures:history -->

**Closed the round before.** *The measurements the deep-hole rounds moved, re-taken,
and the caches they left stale.* No new claim: a reconciliation, run rather
than reported. Phases 33 and 34 added two Lean files, two modules, two studies,
two test files and an evaluation case, and four things had drifted behind them.
The **lexical address book** was stale against the tree digest, so
`retrieval.py` was answering from a book that did not describe the corpus — it
is recomputed and `fresh`. The **measurement cache** the two address studies
are emitted from was stale, so every generated table in
[`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md) and
[`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md) was printing
its staleness notice instead of a figure; re-measured, both studies report
again, and the hand-written passages around the tables — in those studies, in
this document, in `CAPABILITY_ASSESSMENT.md`, in the number-theory paper and in
the package READMEs — were brought to the new measurements rather than patched.
The address book is **3,100 / 3,100** read back with **0** coordinate errors,
2,736 distinct addresses, nearest-by-address sharing a file **609 / 3,100**
against **36** for the digest control and **18** for the reshuffle at a chance
rate of ≈ **1.21 %**; retrieval is **207** queries at hit@5 **39.1 %** against
**6.3 %** chance (**6.2×**), with the text control ahead at **85.0 %**, the
no-lattice ablation at **40.6 %**, the lexical address at **66.7 %**, and the
completeness bound holding on **154,950** pairs with **0** violations for a
certified shortlist of **58.9** declarations. The **worked examples** of both
studies were re-run rather than re-picked: no address moved, and three of the
four spoken-back declarations gained a nearer neighbour from the new files.
The **suite totals** still described an 81-file suite, so six documents quoted
a sentence no run had produced; a release run with the exhaustive cases on
re-earned it — every test file and all **7** instruments passing — and it now
reads **3,436 tests across 82 of the 83 test files, 12,836 subtests, outside the document check**.
Nothing the system answers moved: `lake build` completes with **0 `sorry`** over
**107** Lean files in both copies, the end-to-end evaluation is **143 / 143**
with the same 16 boundary refusals, the benchmarks **2,389 / 2,390**, the probes
33 with 20 holding, and one `pytest` process over the whole suite with the
exhaustive cases on reports **3,464 passed, 0 skipped, 15,424 subtests, zero
failures**. `python3 -m glm_universal.corpus --check` reports `current` and
`figures --check` matches a fresh computation.

**Closed the round before that.** *The Niemeier deep holes, classified from trajectories,
and the layer that was hiding them* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phases
**33** and **34**). The last purely geometric item on the list is closed in
both directions: a pre-registered round that **fails its own sanity check and
says so**, and a second pre-registered round that finds the failure was the
reading rather than the geometry and takes the sanity count from **3 of 10** to
**10 of 10**, with the full query set at **40 of 44** against 12 for the
vertex-count baseline. Both are written up in §2 above with the numbers that
decide them, and both are in the shape D5 requires — a module, a report
subject, an evaluation case, a test file, a study whose every table is
generated, and a Lean file in both copies. The Lean halves are
`GLM.DeepHole` — invariance of the statistic under the relabelling the walk is
allowed, totality with a refusal that is a value, and certified absence under a
separation hypothesis — and `GLM.DeepHoleLadder` — the separation criterion
proved *sufficient* (`nearest_correct`), a witness that widening a reading can
**break** that criterion even though it refines the reading
(`cumulative_can_break_criterion`), and a ladder that returns the least
resolving rung or a refusal about every rung (`firstResolving_least`,
`firstResolving_eq_none_iff`).

The round also took the standing rules a step further:
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) now states the claim as one
about the substrate **and** the machinery used to read it, and adds **D11** —
a forbidden operation never cancels an experiment; the site is declared, the
cost is carried, and the round runs. The deep-hole rounds are the first use of
it: the digest control that D3 requires is a declared SHA-256 site, and the
experiment needs it precisely because a digest carries no meaning.

**What was deliberately not done.** The hole set was not enlarged: the same 14
centres and 10 of the 23 Niemeier types, with the **13** unreached types
reported as unreached and nothing claimed about them. No secondary statistic
was promoted after the numbers were seen; no pairwise vertex distance, diagram
shape or component-size vector was read at any rung, because those are the
label source; nothing was extrapolated past the top rung, so `N = 3840` is not
guessed at; and the certified-absence theorem was left un-instantiated rather
than run at a radius the data does not support.

**Closed the round before those.** *The four things the untouched list had been carrying,
and the figures the growth moved* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase
32). Four items that had each stood as a stated limitation rather than a
mechanism were closed in the shape directive **D5** requires — a report
subject, a test file, a study and a Lean file each. The **cross-register
analogy** is answered from an energy-conjugate register of **7** dimensionally
checked rows, so `heat : temperature :: force : work` is derived rather than
chosen and **11** transport questions come out 8 answered and 3 refused, each
refusal naming its criterion. **Sparse chemistry** is decided rather than
blank: coverage **1,257 → 1,442 of 1,652** by rules admitted only for halving
the field's own mean out of sample, with the **210** remaining cells carrying
one of three stated reasons. The **vague `related_to` triples** get a standing
rule instead of another hand pass — four routes in order, **34 of 66** decided
without a person, and **1 of 4** proposer rules admitted. **Open vocabulary**
becomes a door: three routes admit and one refuses, **20 of 27** probes
admitted, and the refusal is conditional and names its condition. Each is
written up in §2 above, with `Conjugate.lean`, `Completion.lean`,
`Vagueness.lean` and `Admission.lean` beside them.

The round then re-earned the figures that growth had moved, by re-measuring
rather than patching; the figures here are what *that* round measured, and the
current ones are §1 above: the development was **110 Lean files**, **31,483** lines,
**3,100** parsed declarations, no `sorry`, and the suite is **88 test files**.
The address book and the retrieval study were re-taken against the new tree
digest — read back **3,100 / 3,100** with **0** coordinate errors, 2,736
distinct addresses, nearest-by-address sharing a file **609 / 3,100** against
37 for the digest control and 26 for the seeded reshuffle, and retrieval over
**207** queries at hit@5 **39.1 %** against **6.3 %** chance with the text
control still ahead at **85.0 %** — and the hand-written passages of this
document and of the overlay's README, which still quoted the smaller corpus,
were brought to those measurements. `overlay/FIGURES.md` was regenerated and
`python3 -m glm_universal.corpus --check` reports `current`.

A full release run — every test file in its own process with the exhaustive
cases on, and every instrument — re-earned the suite sentence: **3,379 tests
across 80 of the 88 test files, 12,792 subtests, outside the document check**,
with all **88 test files** and all **7** instruments passing. Nothing the
system answers moved: the end-to-end evaluation is **143 / 143** over its
**143 CLI cases** with the same 16 boundary refusals, the benchmarks
**2,389 / 2,390** with every suite above its baseline, the probes 33 with 20
holding and 13 breaking, and `lake build` completes over the Lean development
with no `sorry` in either copy of the tree. One `pytest` process over the whole
suite with the exhaustive cases on closes the round: **3,407 passed, 0 skipped,
15,378 subtests, zero failures**.

**What was deliberately not done.** No estimate was written back into the
element register: the completed view is a *reading*, and at the measured
provenance it is the register cell for cell. The **32** referred `related_to`
triples were not decided by hand to make the figure look better — the point of
the router is that the next one costs no hand work, not that the residue is
empty — and the three refused proposer rules were kept with their
disagreements rather than tuned until they passed. Nothing was written into the
held vocabulary by admission, so the **1,093** names are the same names after
the door exists as before it. And that round did not take the other candidate
of §3.4: the Niemeier deep holes stood untouched, and alone as the next round's
work — which is the round closed above.

**Closed two rounds before.** *The caches a previous round left stale, re-taken, and
the suite re-counted.* No new claim: a reconciliation, run rather than reported.
Three things had drifted when Phase 31 added a study, a module and a test file.
The corpus address book, `DIGEST.md` and the generated blocks of
[`CORPUS_ADDRESS_STUDY.md`](studies/CORPUS_ADDRESS_STUDY.md) were stale against
the documents that round wrote — re-taken, the corpus is **708** addressable
sections over 64 documents, read back **708 / 708** with **0** coordinate errors
of 16,992, and `python3 -m glm_universal.corpus --check` reports `current`. The
sign-off ledger's suite totals still described a 76-file suite, so five
documents quoted a sentence no run had produced; a full release run re-measured
them, with every test file and all **7** instruments passing — the sentence the
documents carry is re-earned by each release run, and as of the round above it
reads **3,436 tests across 82 of the 83 test files, 12,836 subtests, outside the document check**
— and `overlay/FIGURES.md`, which had also frozen the package version at
1.15.0 against the code's 1.16.0, was regenerated from the code. The two
hand-typed corpus figures in this document were re-derived with them (688
sections → **708**; the tier-0 read **2,548** words against roughly
**194,000**). `lake build` completes over the Lean development — **101 Lean
files**, no `sorry`, both copies identical — and no answer the system gives
moved: the end-to-end evaluation is the same **143 CLI cases** with the same
refusals.

**Closed earlier still.** *The wobble landscape, pre-registered and measured*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 31). A study written and committed
before its own measuring code existed, so the statistic could not be chosen
after seeing the data. The verdict is one number with its null named:
**B = 1.79 bits** against the magnitude-matched stride null of the 1,066 exact
rationals `j/10⁷` in `(1/138, 1/136)` — tail `77/1066`, 3.79 bits raw, 1.79
after correcting for the 4 statistics tried — which the pre-registered gate
calls **weak**, so the landscape enumeration was **not** run. Under the
secondary `k`-sweep null the same statistic scores −1.57 bits, and the
disagreement is a fact about the measure a `k`-sweep puts on `k`. Nothing here
derives alpha or says the substrate selects it. Two figures the older material
quotes were re-examined and corrected: the wobble entropy 0.062 is exactly
`H2(alpha)` and carries only the magnitude, and `d_min ≤ 3` for a 24-bit word
is the majority case at `2325/4096`, worth 0.00 bits against a
magnitude-matched null. `reasoning/wobble_landscape.py`,
`RequestProject/GLM/WobbleLandscape.lean` (sorry-free),
`tests/test_wobble_landscape.py`, `report landscape`. See §2, "The wobble
landscape, pre-registered and measured", and
[`WOBBLE_LANDSCAPE_STUDY.md`](studies/WOBBLE_LANDSCAPE_STUDY.md).

**Closed three rounds before.** *The corpus itself made data*
([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 30). The prose of the project is now
held the way the substrate holds data. `glm_universal/corpus/` classifies every
document by rule — archive membership is decided by the path, never by
judgement — emits `DIGEST.md` and every in-document generated block, addresses
all **788** sections of the corpus on the same lattice the Lean declarations
use, keeps the two studies' expensive measurements beside the digest of the
Lean sources they were taken from, and fails when any of that drifts. Every
current-state document opens with a tier-0 block, so a coarse read of the whole
project costs about **3,042** words against roughly **208,000** for the full
current state, and [`ENTRY.md`](ENTRY.md) states a reading order whose coverage
claim is tested rather than asserted. `RequestProject/GLM/Corpus.lean` is the
part of it that is a theorem — the soundness of the tiered read, the archive
partition, the freshness rule and certified absence — and **D10, *a document is
data***, is the standing rule it leaves behind, with
`python3 -m glm_universal.corpus --check` as its instrument. The tables of
[`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md) and
[`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md) are emitted
from that cache rather than typed, which is what caught the drift that round
reconciled: the development is **110 Lean files, 31,483 lines, 3,100
declarations**, and the suite **88 test files**.

**Closed four rounds before.** *The last stored table removed, and the cost of
generating measured* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 29).
`studies/scripts/glm_zero_storage_substrate_v5.py` replaces the 4096-word Golay lookup by the
**12-bit syndrome** — 12 parity checks against **36 bytes** of generator rows,
with the syndrome itself returned instead of a bare `False` — after checking
the two routes against each other on the **196,560**-vector shell, on the whole
**2²⁴**-word space and on both generators, with **0 disagreements**;
`GLM.ZeroStorageV5.syndromeZero_iff_isGolay` and `syndromeSieve_iff_isLeech`
prove the equivalence. Every answer carries an exact integer **cost ledger**,
so the audit is now stored bytes against generator bytes **plus the tax**;
**NRCI** has one written-down definition and is reported on three named
streams beside the bound that is proved for one of them; the register
retargets **continuously**, with `ds_track_bound` and `ds_track_moving_target`
the restated bounds; higher-order noise shaping is measured rather than
assumed, including the instability at order 3; and the coset decoder is proved
**optimal**, not just checked — the repair step inside a coset
(`coset_cost_ge`, `coset_repair_attained`), the coset minimum for a rational
target (`coset_min_cost`, `coset_min_attained`) and the exhaustion of `Λ₂₄` by
the 8,192 cosets (`leech_in_coset`, `lattice_dist_ge`), so what the decoder
minimises is the distance to the nearest lattice point.
`RequestProject/GLM/ZeroStorageV5.lean` is sorry-free. See §2, "And then the
last table removed, and the cost of generating measured", and
[`ZERO_STORAGE_V5_STUDY.md`](studies/ZERO_STORAGE_V5_STUDY.md).

**Closed five rounds before.** *Generated rather than stored, and the generators
checked* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 28). A supplied script asks
the substrate to stop storing its tables and regenerate them. The perspective
holds and now has a number — **9,449,445 bytes** of audited tables against
**24,648 bytes** of generators, about **383 to one**, every regenerated object
compared with the stored one before the row is emitted, and **99.7 %** of the
overlay's own bytes on disk already caches with input digests. The proposed
generators mostly do not hold: the zero-storage Leech sieve is sound
(`v3Sieve_sound`) and **99.4 % incomplete** (**1,152 of 196,560** minimal
vectors), with `v3Sieve_iff` saying exactly what it generates and
`octadVec_not_v3Sieve` a decided witness of what it loses; the snap built on it
returned a non-lattice point on **4 of 4** general-position probes through a
fallback `fallbackVec_not_isLeech` refutes; and **0 of 3** stated accuracy
claims for the generated constants hold. The repair to the sieve is one line
and agrees with the package's membership test on **196,656** vectors; the exact
coset decoder added beside the snap is inside Λ and within squared covering
radius **16** on every probe. `RequestProject/GLM/ZeroStorage.lean` (sorry-free)
and `tests/test_generative.py` (16 cases) came with it; `report generated` is
the **52nd** report subject and the evaluation's **135th case**, and the
pipeline is **22 of 22** rows through all six stages. See §2, "Generated rather than stored, and the generators checked",
and [`ZERO_STORAGE_STUDY.md`](studies/ZERO_STORAGE_STUDY.md).

**Closed six rounds before.** *The address book made to do work, and the first
loop* ([`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 27). Two questions the brief asks and
the project had never put to itself: can the substrate **retrieve**, and can it
**steer a loop**? Both are now measured against controls rather than asserted,
and both answers are mixed in a way worth having. Retrieval: the address is a
real index — 39.1 % hit@5 against 6.3 % chance — beaten decisively by a plain
text control at 85.0 %, and matched query for query by the same features
with no lattice at all; what the lattice earns is a *proved* completeness
bound, 154,950 pairs with 0 violations, under which an empty shortlist is a
proof of absence. The loop: propose–check–refuse over the EXT10 generators,
every returned plan re-verified end to end by an instrument that did not build
it, 127 of 726 quantities refused with a proof and no node expanded, and the
address scorer solving 18 of 24 against 8 unguided — one *ahead* of nothing and
one *behind* the same distance without the lattice. Two Lean files
(`Retrieval.lean`, `Controller.lean`) and two test files came with them; the
development is **110 Lean files**, 31,483 lines, 3,100 parsed declarations, no
`sorry`; `report retrieval` and `report controller` are the **50th** and
**51st** report subjects and the evaluation's 133rd and 134th cases, so the
end-to-end set is **134 / 134** with the same 16 boundary refusals. See §2,
"The address book, made to do work" and "The loop: propose, check, refuse",
[`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md) and
[`CONTROLLER_STUDY.md`](studies/CONTROLLER_STUDY.md).

**And the round before that.** *The dropped work, restored, and the second reading of
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

**And before that.** *The archive, read to the end*
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

<!-- figures:current -->

### 3.1 The evaluation finds no gap

The end-to-end set is **147 of 147** and every one of its sixteen refusals is a
`boundary` — a theorem or a stated commitment — rather than a `gap`. The last
gap, `coherence-unregistered-molecule`, is closed: see the fall-through
recorded in §2 above. What remains open is listed in §3.2 and §3.3, and none
of it is a question the evaluation set asks.

### 3.2 Named as untouched

The list is kept in `archive/MASTER_PLAN_ARCHIVE.md` §7.9; this is the same list.

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
* **`heat : temperature :: force : ?` — closed.** It used to be refused with a
  stated reason: an analogy whose operands are spread across registers is *not*
  in general refused — `hot : temperature :: fast : velocity` is answered — so
  what stopped this one was the relation, the lexicon carrying `temperature
  drives heat` and reaching nothing from `force` in either direction. The
  relation is now supplied as a register rather than as a special case: seven
  energy-conjugate rows checked against the physics register, so `force`
  reaches `work`, and the four criteria a transportable relation must meet are
  stated so a refusal names the one it failed. See §2, "The cross-register
  analogy", and [`CONJUGATE_STUDY.md`](studies/CONJUGATE_STUDY.md).
* **The `O(1)` LLVQ table — closed, with the claim narrowed.** The table is
  built and is on the quantiser's hot path; what the measurement supports is
  *constant-bounded*, not constant, and the report and the study say so. See
  §2, "The quantiser's search, replaced by a lookup".
* **The Niemeier deep-hole census — closed, and the claim measured in both
  directions.** The trajectory distribution *does* classify: at the escalated
  reading it names **40 of 44** queries and keeps **10 of 10** labels under a
  change of ensemble seed, where the first, unescalated reading kept 3 of 10
  and said so. What is not closed is the certification — the separation
  criterion `ρ = 2W/B < 1` is unmet at every rung — and the census itself is
  still one lattice's worth: **10** of the 23 root systems are reached, and the
  other 13 are reported as unreached. See §2, "Geometry classified from
  trajectories, and the layer that was doing the hiding", with
  [`DEEP_HOLE_STUDY.md`](studies/DEEP_HOLE_STUDY.md) and
  [`DEEP_HOLE_ESCALATION_STUDY.md`](studies/DEEP_HOLE_ESCALATION_STUDY.md).
* **Open vocabulary — closed as a mechanism, and the commitment kept.** The
  vocabulary is still exactly the registers and there is still no coordinate
  for *justice*, but the other half of the question — how a name gets *in* — is
  now a stated door: a name is admissible exactly when some stated route gives
  it coordinates computed from a register the machine already checks. Three
  routes admit and one refuses, and the refusal is conditional and names its
  condition, so *justice* is refused until a register that measures it exists
  rather than as a matter of kind. See §2, "Open vocabulary, made a door", and
  [`ADMISSION_STUDY.md`](studies/ADMISSION_STUDY.md).
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
  triple. That no longer means hand work by default — a new triple is put to
  four routes in order and only the last asks a person, with 34 of the 66
  decided without one and the other 32 referred with their evidence. See §2,
  "The undimensioned names, decided" and "The vague `related_to` triples", with
  [`studies/DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md) and
  [`studies/VAGUENESS_STUDY.md`](studies/VAGUENESS_STUDY.md).
* **Sparse chemistry — every empty cell now decided, and the sparsity itself
  still ongoing.** 1,257 of 1,652 element cells are measured. The completion
  module raises the *completed view* to 1,442 by rules admitted only for
  halving the field's own mean out of sample, and gives each of the remaining
  210 one of three stated reasons — 100 inputs absent, 97 no admitted rule, 13
  not derivable from this register. Nothing is written back into the register,
  deliberately, so that an estimate is never mistaken for a measurement. What
  stays ongoing is the data: a measurement the register does not hold can only
  be supplied, not derived. See §2, "Sparse chemistry, decided rather than left
  blank", and
  [`ELEMENT_COMPLETION_STUDY.md`](studies/ELEMENT_COMPLETION_STUDY.md).

### 3.4 Named for the next round

This section is the one to read first on the next development push. It is
written up as the proposed next phase in
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 36, which points back here.

**The round just closed retired the largest candidate on this list and one
other.** *Escalation as the default step of the query loop* is built, measured
and wired — see §2, "Escalation, as a step of the ordinary query loop" — so it
is no longer a candidate; and the four failures the deep-hole ladder leaves are
no longer an open diagnosis but a located mechanism (§2, "The four failures the
escalated deep-hole reading leaves, diagnosed"). The round also added two
things this list did not ask for and that constrain what follows: cumulativity
is now a shipping condition every layer family is checked against, and the
stalled results below are ranked by the review-sweep register before any of
them is re-read. One candidate is *sharper* rather than closed — the separation
criterion, item 1a below, now has its obstruction named — and one is new: the
reverse-call planner's utility gate, which is false today and is what keeps the
planner in the sandbox.

The round before that added no candidate and retired none: it re-took the
measurements the two rounds before it had moved, and is recorded in the closed
list above. Those two rounds took the **last** candidate
that used to stand here — the Niemeier deep holes, classified from trajectories
rather than read out of a table — and closed it in two pre-registered halves,
Phases 33 and 34, both recorded in §2 and in the closed list above. The first half returned an honest
negative: the method beat every control, including the vertex-count competitor,
and still stopped, because a bare change of ensemble seed kept only **3 of 10**
labels. The second half asked whether that was the geometry or the *layer it
was read at*, escalated the reading along a declared ladder of layer × budget
cells, and reached **10 of 10** with **40 of 44** on the full query set. The
round before those closed the semantic half of the analogy with the
energy-conjugate register, together with the three items §3.2 and §3.3 had been
carrying; before that came the reconciliation recorded further up §3; before
that the wobble landscape, run as a pre-registered study and returned under its
own gate (§2, and Phase 31); before that the corpus made data — the tiered
read, the entry point, the addressed documents and the studies' tables emitted
rather than typed (Phase 30); and before that the generate-versus-store
question, finished by removing the last stored table and putting an exact cost
on generating (Phase 29). A third item came out
of it — **the coset decoder's global optimality** — and was closed in the same
round: `coset_cost_ge` and `coset_repair_attained` prove the repair step is
the minimum inside a coset, `coset_min_cost` and `coset_min_attained` carry
that to a rational target as the coset minimum, and `leech_in_coset` with
`lattice_dist_ge` prove the 8,192 cosets exhaust `Λ₂₄`, so the winner over
them is the nearest lattice point. What is still checked rather than proved is
the transcription: that the script computes the quantities those theorems are
about.
The prerequisite check for offering any of this upstream was done rather than
assumed and is §10 of
[`studies/ZERO_STORAGE_V5_STUDY.md`](studies/ZERO_STORAGE_V5_STUDY.md): the
pinned Mathlib has the ambient lattice and quadratic-form theory but no Golay
code, no Leech lattice and no linear-code layer, so the missing piece is the
theory beneath the sieve, not the sieve.

The item that used to stand here — the `O(1)` LLVQ table — is closed and is §2,
"The quantiser's search, replaced by a lookup"; so is the round that followed
it, the archive read to the end, which is §2, "The archive, read to the end"
and which added a third of the Lean development without changing an answer.
The second and third of the items named below are closed too: the analogy by
the energy-conjugate register, and the stability measurement by
`reasoning/stability.py` against `RequestProject/GLM/Stability.lean`, with the
nearest-point ties it exposes measured in
[`TIE_BREAK_STUDY.md`](studies/TIE_BREAK_STUDY.md). The language layer has
reached the point its own measurement says it should stop at: the thirteen
remaining query kinds are not shapes of any family, and forcing them would make
the coverage figure meaningless. So the next round is **not** a fourth shape
family. The three candidates below are what the deep-hole rounds left standing;
the two items after them are recorded as closed, with what closed them.

**1. The Niemeier deep holes — closed, and what it left behind.** Closed by
Phases 33 and 34; see §2, "Geometry classified from trajectories, and the layer
that was doing the hiding", with
[`DEEP_HOLE_STUDY.md`](studies/DEEP_HOLE_STUDY.md) and
[`DEEP_HOLE_ESCALATION_STUDY.md`](studies/DEEP_HOLE_ESCALATION_STUDY.md).
Three things it left behind are the candidates for the next round, in the order
they are worth taking.

*1a. The separation criterion, still unmet.* `nearest_correct` in
`DeepHoleLadder.lean` says a reading names holes correctly whenever
`ρ = 2W/B < 1`, where `W` is the largest within-hole spread and `B` the
smallest between-hole gap. Measured, `ρ` falls from `3.90` to **`2.59`** across
the ladder and never crosses `1`, so the classifier that in fact names 40 of 44
still cannot certify a single **absence**: faithfulness would need a radius
`r ≥ 0.0659` where separation permits only `r < 0.0179`. That gap is the sharp
open question, and it is a question about the *reading*, not about the census —
either a rung is found where `ρ < 1`, or a bound is proved saying no reading of
this family can reach it. Either answer closes it.

*1b. The thirteen unreached types.* The ensemble reaches **10** of the 23
Niemeier root systems from the 14 declared centres; the other **13** are
reported as unreached and nothing is claimed about them. Reaching them means
new centres, and new centres mean a new pre-registration, because the centre
set is part of what the first study fixed.

*1c. The rational reading's own boundary, as a pair of names.* Read alone, the
exact distance measure **conflates** `A_1^24` with `A_2^12`: neither emits a
stray, so the whole measure is one atom. That is a capacity boundary of the
kind [`INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) is about,
but it is currently recorded as an observation rather than as a theorem. The
theorem to want is the one that says *which* pairs any stray-blind reading must
conflate.

*1d. The faithfulness radius, as a theorem rather than a measurement.*
`GLM.DeepHoleFailure.per_type_absent` is the certificate the deep-hole rounds
have been short of — a carrier further than `w` from a type's reference is not
of that type, given that the type is faithful at radius `w`. The hypothesis is
empirical and is currently unmet on this data (`r ≥ 0.0659` needed against
`r < 0.0179` permitted), so the theorem is instantiated nowhere. Either an
ensemble is found whose within-type spread meets the bound, or the
incompatibility is proved rather than observed. The review-sweep register
classes this one as *needs-a-theorem*, which is exactly why it is not a
candidate for an escalated re-reading.

**A candidate that came out of the round just closed: the planner's utility
gate.** The reverse-call planner (§2, "The reverse-call planner, kept in the
sandbox") satisfies every safety line the promotion checklist states and fails
the one that decides it: on the project's own evaluation set it gains nothing,
because the refusals it is offered are refusals it agrees with. The question
that would close it is not about the planner but about the **tool registry** —
whether a tool exists that a problem-driven front end could reach and the
kind-driven dispatcher cannot. Until one does, directive **D14** keeps the
planner where it is, imported by nothing the system computes with.

**Escalation as the default step — closed.** This was the largest item on the
list and is now §2, "Escalation, as a step of the ordinary query loop":
`runtime/escalation_loop.py` climbs a three-rung ladder declared per query
kind, `reasoning/query_escalation.py` measures both gates over the whole
evaluation set, and `RequestProject/GLM/EscalationLoop.lean` proves what the
loop guarantees rather than exercising it. What it deliberately does *not* do
is escalate a principled refusal: a refusal classified non-escalatable is
returned at the layer it was classified at, which is `climb_principled`.

**2. `heat : temperature :: force : ?` — closed.** The relation an analogy
asserts, read off the registers rather than off the coordinates. The shape was
described already, so what was missing was the *semantic* half: the lexicon
carries `temperature drives heat`, and from `force` in either direction it
reached nothing, which is why the question was refused with a stated reason
rather than answered wrongly. It is closed the way the item asked for — by
supplying the relation and saying what makes a relation admissible, not by
widening the dispatch: an energy-conjugate register of seven rows, each checked
against the physics register in exact integer arithmetic, with `determinate`,
`role_typed`, `functional` and `grounded` the four criteria a refusal names.
`force` reaches `work`. See §2, "The cross-register analogy", and
[`CONJUGATE_STUDY.md`](studies/CONJUGATE_STUDY.md).

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

The seven instruments in the ledger beside the
<!--figure:test-files-->89 test files<!--/figure--> are `lean-build`,
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
lake build                                                   # 111 Lean files, no sorry
rg -n 'sorry|admit' RequestProject/GLM                       # expect nothing
diff -r RequestProject/GLM overlay/glm_lean/RequestProject/GLM   # the two copies agree

cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q        # the whole suite
PYTHONPATH=. python3 -m glm_universal.capabilities           # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks             # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8    # 147 CLI cases
PYTHONPATH=. python3 -m glm_universal.figures --check        # FIGURES.md is current
PYTHONPATH=. python3 -m glm_universal.figures --write        # regenerate FIGURES.md
PYTHONPATH=. python3 -m glm_universal.corpus --refresh       # every derived document
PYTHONPATH=. python3 -m glm_universal.corpus --check         # exit 1 on any drift
```

`--refresh` is the one to reach for after a change: it rebuilds the Lean
address book, the document address book, the measurement cache and then the
generated documents, blocks and inline figures, in that order — the only order
in which one pass converges — and ends with a fixed-point check. The
`diff -r` above is an invariant rather than a chore, because the mirror is
generated:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools lean-mirror          # do the copies agree?
PYTHONPATH=. python3 -m glm_universal.tools lean-mirror --write  # make them agree
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
