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
the next round", before anything else.**

**The round just closed (Phase 63) moved the target**: under directive
**D15** it moved **derivation** and **address**, and sharpened **refusal**. It
was round two of
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md):
three near misses of the first round were looked at again and refined into
planner frames — interval consistency, rational recognition with a uniqueness
certificate, and dimensional derivation — which answer 26 of 33 declared
questions and refuse the other 7 as declared, with 0 wrong where the grammar
answers none. The typed planner is now the default path of `GLM.py`
(`--grammar` asks the grammar alone); the 177 contract cases give the same
outcomes either way. A language model as parser (G1) is declined for good.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 63 is the record.

**An earlier round (Phase 60) was a documentation round** taken at the
owner's request: it moved none of **derivation**, **address** or **refusal**
(D15). [`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md) now covers
the system as a whole (the machine, addressing, measured capability, negative
results, method, and a ledger of the supplied material taken and left), and
[`GLM_Complete_Number_Theory_Evidence.md`](studies/GLM_Complete_Number_Theory_Evidence.md)
gained §15–§21. It also resynced the overlay Lean mirror, which Phase 59 had
left one file short. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 60 is the
record.

**The round before it (Phase 59) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, with five **address**
answers and no **table**. It took the supplied formula-wheel session record
(`source_material/formula_wheel/`) rather than a candidate of §3.4, because
the request was to have the GLM reason in electrical and mechanical terms and
the record's own first priority is to run its studies against the GLM's
substrate. `glm_universal.engineering` reads formula wheels as rational spans
with certificates, the Smith chart over Gaussian rationals, the force-voltage
and force-current analogies as maps on laws, and the delta-sigma loop by
theorem, and `engineering/speak.py` lets the machine be asked in words
(`GLM.py --eng`, `GeometricSession.ask_engineering`). On 63 questions
committed before any of that code, both existing paths refused all 53
answerable ones; through the surface it answers **53** correctly and refuses
**10** correctly with **0** wrong, and it reads none of the 374 questions the
machine already answers. The register agrees with the corrected formula study
on all 41 cases at SI7 and at EXT10, the force-voltage analogy preserves 9 of
9 laws each way, and `RequestProject/GLM/EngineeringWheels.lean` proves the
licensing rules (span membership, translation, the Smith disc, the periods of
the bitstream). [`studies/ENGINEERING_LANGUAGE_STUDY.md`](studies/ENGINEERING_LANGUAGE_STUDY.md)
is the study and [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 59 the record.

**The round before that (Phase 58) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, and most of what it gained
is **table** — coverage of operations the machine already had. It took the
supplied roadmap (`source_material/GLM_IMPROVEMENT_ROADMAP.md`) rather than a
candidate of §3.4, because the measurement the roadmap quotes still held: the
frozen language probe, asked through `GeometricSession.ask`, scored two
correct of twenty although the answers to most of it were held behind the
formal grammar. `glm_universal.runtime.semantic_plan` reads a question into
typed plans over the operations the session already has — each slot grounded
against what the registers hold, each plan run, and an answer given only when
every licensed plan agrees — and adds two things that compute rather than
route: exact integer arithmetic and conversion between units whose relation
is a definition. Through it the frozen probe scores
**<!--figure:plans-probe-correct-->19<!--/figure-->** correct and
**<!--figure:plans-probe-wrong-->0<!--/figure-->** wrong, passing the mark
declared before the probe was first run; on the
**<!--figure:plans-held-total-->110<!--/figure-->** held-out questions
committed before the planner existed it answers
**<!--figure:plans-held-correct-->86<!--/figure-->** correctly and refuses
**<!--figure:plans-held-correct-refusal-->22<!--/figure-->** correctly with
**<!--figure:plans-held-wrong-->1<!--/figure-->** wrong — a register holding
iron's atomic weight to four figures where the world uses five, recorded as a
data-truth finding rather than edited away. Two readings that disagree are
refused, not chosen between: *does energy have the same dimensions as
torque?* is yes in the SI projection and no in the extended vector, and the
answer names both. It is opt-in (`GLM.py --plan`,
`GeometricSession.ask_planned`), so the 177-case contract set is untouched.
`RequestProject/GLM/SemanticPlan.lean` proves the licensing rule order-free,
sound and conservative over the grammar, and refutes the first-licensed rule.
[`studies/SEMANTIC_PLAN_STUDY.md`](studies/SEMANTIC_PLAN_STUDY.md) is the study
and [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 58 the record.

The round before these (Phase 55) **moved the
target**: under directive **D15** it moved **refusal**, and widened
**derivation** to a fold over rows of two tables at once. It took candidate 1
of §3.4 — the scales neither operation could bridge — and wrote them down.
`glm_universal.reasoning.scale_conversion` declares nine scales over four
quantities (mass in `u`, molar energy in `kJ·mol⁻¹`, temperature in `K`,
length in `pm`), each row an exact positive-affine map into its quantity's
canonical unit with the source its numbers came from, so that a conversion is
a fact someone wrote down rather than a guess from a name. Seven of twelve
questions declared before the run are answered and five refused, every one of
the twelve as declared; the ordering and extremum operations come out on their
own declared sets exactly as they did — 7 of 7 and 8 of 8 — and `largest mass`
now gathers the element rows and the molecule rows into one unit and folds
them. What the table does not reach it still refuses: it relates 6 of the
7,750 pairs of the 125 numeric scales the field surface holds, and every other
pair is `different-scale` with the table's own reason.
`RequestProject/GLM/ScaleConversion.lean` is the proved half —
`cmpQ_apply` and `order_conversion_invariant` that a positive conversion
leaves the verdict alone, `orderWith_conservative` that the wider operation
never changes an answer the bare one gave, `orderWith_eq_none_iff` that its
silence is still exactly stated, `the_table_carries_the_claim` that the
declaration and not the code is what licenses a bridge, and
`negative_factor_flips_the_verdict` and `raw_gather_names_the_wrong_row` for
the two things it must not do.
[`studies/SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md) is
the study and [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 55 the record.

The round before it **moved the target** too: under directive **D15** it moved
**addressing** and **refusal**. It
did not take a candidate from §3.4; it took the material supplied with it —
`source_material/conversation_experiment/`, eight scripts and a research
document on a conversational GLM, every one of which runs unmodified against
the package — tested its claims, and built the one thing in it this system
could not do at all: a **turn that refers back to an earlier turn**. *describe
it*, *and the smallest?* and *and oxygen?* are now bound to what the
conversation has already said, by the only test that makes the reference a
reading of the registers rather than a guess about word order — a candidate is
**licensed** when the query it produces actually solves. Eight of fifteen
declared follow-ups are bound and seven refused, every one of the fifteen as
declared, where the same fifteen texts asked of a session with no memory are
answered **none** of the time; and the rule a reader would assume — bind to
the most recent mention — differs on three of the ten pronoun follow-ups,
losing one answer the registers hold and giving two confident answers to
questions that have no single answer.
`GLM.Conversation.most_recent_mention_is_not_the_antecedent` is that control
refuted as a theorem rather than as a measurement. Two claims of the supplied
material did **not** survive being re-run, and are recorded as refuted: the
higher-order analogy whose second constraint has no exact solution and
contributes nothing, and the periodic-table reading that is a renaming of two
carrier coordinates.
[`studies/CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md) is the study,
`RequestProject/GLM/Conversation.lean` the proved half, and
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 54 the record.

The round before that **moved the target** too: under directive **D15** it
moved **derivation** and **refusal**. It
took candidate 1 of §3.4 — the column rather than the pair — and built the
operation that closes it: `extremum`, one coordinate read off *every* row of
one declared table and folded to its end, or refused. Four of eight declared
columns are folded and four refused, every one of the eight as declared before
the run, and the two refusals it was built for are the result rather than the
cost: a column with a hole in it has no extremum, because
`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a
column whose extremum over the rows that are filled in is a different value at
a different row, and a column gathered from two scales is not one column,
because `extremum_not_invariant_under_one_row_rescaling` exhibits a one-row
rescaling that moves the winner where `extremum_scale_invariant` shows that
rescaling the shared scale cannot. Where the end is a tie every row attaining
it is named — fourteen of them, on the lexicon register's `abstract_concrete`.
What it does **not** move is addressing: the table and the coordinate are the
names the question already gives.
[`studies/COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md) is the
study, `RequestProject/GLM/ColumnExtremum.lean` the proved half, and
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 53 the record.

The round before that was **maintenance**, and said so: under directive **D15**
it moved none of derivation, addressing or refusal. It finished the round
before it — which
had stopped with its counts re-taken in the working note but not written into
the documents, and with no release run — by re-taking eight counts the tree
quotes about itself, four of them measurements rather than tallies: the formal
development at 3,422 declarations, the relay's strict gain now holding across
the whole declared gate band with 19 queries carried and none lost, the
planner consulted on ten refusals rather than four, and the end-to-end set at
164 cases with 22 expected refusals. One unit was brittle rather than wrong —
it asserted that a two-digit sentinel never reaches the recorded totals, and
the suite reached 99 counted test files — and was fixed at the root. The
release then earned: **every test file of that suite and all 7 instruments**
signed with the exhaustive cases on. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 52 is the record.

The round before that **moved the target** too: under directive **D15** it
moved **derivation** and **refusal**. It took candidate 1 of §3.4 as it then
stood — the comparison a field surface
could not make — and built the operation that closes it: `ordering`, one
coordinate read off two rows and ordered exactly in rationals, or refused.
Four of seven declared comparisons are answered and three refused, every one
of the seven as declared before the run, and the refusals are the result
rather than the cost — two readings are comparable only on one scale, and
`GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive
rescaling that flips the comparison of the bare numbers where
`order_scale_invariant` shows that no rescaling of a shared scale can. It
closes the last of the probe's ten held-and-unreachable questions: *is energy
more abstract than water?* is answered *energy*, by an exact `3/4`, on the
lexicon register's own scale and its own declared poles. What it does **not**
move is addressing, and the derivation it moves is one exact subtraction over
two addressed readings, which is the honest size of it.
[`studies/ORDERING_STUDY.md`](studies/ORDERING_STUDY.md) is the study,
`RequestProject/GLM/CoordinateOrder.lean` the twelve theorems, and
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 51 the record.

The round before it was **maintenance**, and said so: under directive **D15**
it moved none of derivation, addressing or refusal. It asked the release
question the round before it had left unasked, and repaired the six units that
failed it — the UBP source audit, which had no way to say that a float inside
the core was a *declared* site and now reads the declared list off the D11
inventory rather than loosening the check; the reasoning kernel's import
audit, told about the one integer-nanosecond timing; two counts of the tree
that had drifted; and two measurements that had moved with the corpus and were
re-taken. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 50 is the record.

The round before *that* took the four supplied *History Recorded in the Now*
studies seriously enough to decide them. Under directive **D15** it moved
**refusal**, on a declared task set: the supplied recipe answers all nine
history questions and is wrong on the four whose answer the receipt does not
determine, and the module answers five and refuses four, each refusal carrying
the pair of histories that share the receipt.
[`studies/NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md) is the study and
`RequestProject/GLM/NowReceipt.lean` the nine theorems; Phases 21–51 of
[`MASTER_PLAN.md`](MASTER_PLAN.md) are the rest of the record.

Last reconciled against a full re-run on 2026-09-21.

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
| test suite | `python3 -m pytest glm_universal/tests -q` | **<!--figure:suite-->4,267 tests across 108 of the 109 test files, 16,276 subtests, outside the document check<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **<!--figure:evaluation-case-count-->177<!--/figure--> / <!--figure:evaluation-case-count-->177<!--/figure-->** — 149 answered, 28 refused as expected (all `boundary`, no `gap`), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites, every suite above its baseline |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 errored, 0 surprises |
| Lean development | `lake build` (repository root) | <!--figure:lean-files-->133 Lean files<!--/figure-->, **0 `sorry`** |
| figures | `python3 -m glm_universal.figures --write` | regenerates `overlay/FIGURES.md`; every documented count |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the archive partition, the coverage claim of `ENTRY.md`, every generated block and every derived cache — **current**, no drift |
| construction ladder | `python3 -m glm_universal.tools ladder` | **462 / 568** queries named correctly with **0** wrong on the eleven-rung ladder, against **327** for the note's five rungs and **283** for the best single rung |
| norm-family ladder | `python3 -m glm_universal.tools normladder` | the repaired **<!--figure:normesc-rungs-->10<!--/figure-->**-rung norm ladder names **<!--figure:normesc-correct-->467<!--/figure-->** of **<!--figure:normesc-queries-->568<!--/figure-->** correctly with **<!--figure:normesc-wrong-->0<!--/figure-->** wrong; the full **<!--figure:normesc-family-rungs-->12<!--/figure-->**-rung family it repairs answers **<!--figure:normesc-family-wrong-->1<!--/figure-->** wrongly and is **not safe** |
| escalated operations | `python3 -m glm_universal.tools operations` | **<!--figure:opesc-count-->7<!--/figure-->** operations other than retrieval measured against substrate-removed controls; every one gains, and **one of them — program text — answers <!--figure:opesc-program-wrong-->13<!--/figure--> queries wrongly and is reported unsafe** |
| second reading | `python3 -m glm_universal.tools second-reading` | **<!--figure:secondread-adopted-->1<!--/figure-->** of **<!--figure:secondread-configurations-->6<!--/figure-->** declared guard configurations is adopted — `<!--figure:secondread-shipped-->strict+margin<!--/figure-->` takes the program-text operation to **<!--figure:secondread-program-correct-->366<!--/figure-->** correct and **<!--figure:secondread-program-wrong-->0<!--/figure-->** wrong, giving up **<!--figure:secondread-given-up-->150<!--/figure-->** answers where matched refusal removes **<!--figure:secondread-matched-removes-->2<!--/figure-->** of the thirteen |
| field surface | `python3 -m glm_universal.tools fieldsurface` | the surface answers **<!--figure:fieldsurface-moved-->9<!--/figure-->** of the **<!--figure:fieldsurface-held-->10<!--/figure-->** questions the oracle found held and unreachable — exactly the **<!--figure:fieldsurface-predicted-->9<!--/figure-->** declared reachable before the run — taking the probe from **<!--figure:fieldsurface-parsed-before-->6<!--/figure-->** parsed to **<!--figure:fieldsurface-parsed-after-->15<!--/figure-->**; it is `table`, not reasoning |
| ordering operation | `python3 -m glm_universal.tools ordering` | the operation answers **<!--figure:ordering-answered-->4<!--/figure-->** of the **<!--figure:ordering-declared-count-->7<!--/figure-->** comparisons declared before the run and refuses **<!--figure:ordering-refused-->3<!--/figure-->** under **<!--figure:ordering-reasons-->3<!--/figure-->** named reasons — **<!--figure:ordering-as-declared-->7<!--/figure-->** of **<!--figure:ordering-declared-count-->7<!--/figure-->** as declared — and closes the last held-and-unreachable probe question, taking it to **<!--figure:ordering-parsed-after-->16<!--/figure-->** parsed |
| typed planner | `python3 -m glm_universal.tools plans` | the frozen probe through the planner scores **<!--figure:plans-probe-correct-->19<!--/figure-->** correct, **<!--figure:plans-probe-wrong-->0<!--/figure-->** wrong, **<!--figure:plans-probe-refused-->1<!--/figure-->** refused; **<!--figure:plans-held-correct-->86<!--/figure-->** correct and **<!--figure:plans-held-correct-refusal-->22<!--/figure-->** correct refusals of **<!--figure:plans-held-total-->110<!--/figure-->** held-out questions with **<!--figure:plans-held-wrong-->1<!--/figure-->** wrong; the hostile stress set **<!--figure:plans-stress-wrong-->0<!--/figure-->** wrong |
| extremum operation | `python3 -m glm_universal.tools extremum` | the operation folds **<!--figure:extremum-answered-->4<!--/figure-->** of the **<!--figure:extremum-declared-count-->8<!--/figure-->** columns declared before the run and refuses **<!--figure:extremum-refused-->4<!--/figure-->** under all **<!--figure:extremum-reasons-->4<!--/figure-->** of its named reasons — **<!--figure:extremum-as-declared-->8<!--/figure-->** of **<!--figure:extremum-declared-count-->8<!--/figure-->** as declared — and reports **<!--figure:extremum-ties-->1<!--/figure-->** tie as a tie rather than resolving it |
| scale conversions | `python3 -m glm_universal.tools scales` | the declared table of **<!--figure:scales-rows-->9<!--/figure-->** scales over **<!--figure:scales-quantities-->4<!--/figure-->** quantities answers **<!--figure:scales-answered-->7<!--/figure-->** of the **<!--figure:scales-declared-->12<!--/figure-->** questions declared before the run and refuses **<!--figure:scales-refused-->5<!--/figure-->** — **<!--figure:scales-as-declared-->12<!--/figure-->** of **<!--figure:scales-declared-->12<!--/figure-->** as declared — and relates **<!--figure:scales-bridged-->6<!--/figure-->** of the **<!--figure:scales-pairs-->7,750<!--/figure-->** pairs of the **<!--figure:scales-numeric-->125<!--/figure-->** numeric scales, leaving every other pair refused |
| conversation layer | `python3 -m glm_universal.tools conversation` | the layer binds **<!--figure:conversation-answered-->8<!--/figure-->** of the **<!--figure:conversation-declared-count-->15<!--/figure-->** follow-ups declared before the run and refuses **<!--figure:conversation-refused-->7<!--/figure-->** under all **<!--figure:conversation-reasons-->3<!--/figure-->** of its named reasons — **<!--figure:conversation-as-declared-->15<!--/figure-->** of **<!--figure:conversation-declared-count-->15<!--/figure-->** as declared — against **<!--figure:conversation-alone-->0<!--/figure-->** answered by a session with no memory, and the recency control differs on **<!--figure:conversation-control-wrong-->3<!--/figure-->** of **<!--figure:conversation-control-rows-->10<!--/figure-->** |
| role--filler binding | `python3 -m glm_universal.tools binding` | a typed relation written as one 24-bit word gives the filler's reading back with no side condition; naming the filler recovers **<!--figure:binding-recovered-->6<!--/figure-->** of the **<!--figure:binding-declared-count-->12<!--/figure-->** bindings declared before the run and refuses **<!--figure:binding-refused-->6<!--/figure-->** — **<!--figure:binding-as-declared-->12<!--/figure-->** of **<!--figure:binding-declared-count-->12<!--/figure-->** as declared — because only **<!--figure:binding-nameable-->424<!--/figure-->** of the **<!--figure:binding-carriers-->1,143<!--/figure-->** carriers read uniquely, the worst fibre holding **<!--figure:binding-largest-fibre-->136<!--/figure-->** |
| plan store | `python3 -m glm_universal.runtime.plan_store` | a resolved follow-up kept against a digest of the whole conversation replays **<!--figure:planstore-replayed-->15<!--/figure-->** of **<!--figure:planstore-declared-count-->15<!--/figure-->** unchanged, refusals included (**<!--figure:planstore-refusals-replayed-->7<!--/figure-->** of **<!--figure:planstore-refusals-->7<!--/figure-->**), taking the licensing trials from **<!--figure:planstore-trials-first-->27<!--/figure-->** to **<!--figure:planstore-trials-replayed-->0<!--/figure-->**; keyed by the follow-up text alone it answers **<!--figure:planstore-coarse-wrong-->8<!--/figure-->** of the fifteen with another conversation's antecedent |
| engineering surface | `python3 -m glm_universal.tools engineering` | on **63** engineering questions committed before the code: **53** correct, **10** correct refusals, **0** wrong (both existing paths: 0 correct, 53 refused); formula wheels **41 / 41** at SI7 and EXT10; Smith chart **16 / 16**; force-voltage analogy **9 / 9** laws each way; delta-sigma **6 / 6** |
| blockers probe | `python3 -m glm_universal.tools blockers` | the pre-registered language probe scores **<!--figure:probe-correct-->2<!--/figure-->** correct, **<!--figure:probe-wrong-->1<!--/figure-->** wrong, **<!--figure:probe-refused-->17<!--/figure-->** refused of **<!--figure:probe-questions-->20<!--/figure-->** — **below the declared pass mark of <!--figure:probe-pass-mark-->10<!--/figure-->**, a declared failure |

The test-suite row is the sign-off ledger's own count, recorded by
`python3 -m glm_universal.signoff --release`, which runs each test file in its
own process with the `exhaustive` tests selected. One `pytest` process over the
same tree, with `GLM_EXHAUSTIVE=1` so that nothing is deselected, collects
**4,018 tests** — which is the ledger's 3,990 plus the 28 tests of the document
check the ledger's total leaves out, because a round that adds a document or a
figure fails that check until the documents are reconciled. Without that switch the `exhaustive`
tests — which certify rather than sample — are reported as skipped with their
reason rather than dropped silently, which is why the ledger's own count is
taken from a run that selects them.

The package is `glm_universal` **v1.23.0**: eleven sub-packages, 150 modules,
**8 registers** holding 1,143 carriers (physics 726, chemistry 118, molecules
51, mathematics 22, lexicon 149, spatial 28, harmonics 28, economics 21) beside
a 45-class comparison register, **<!--figure:query-kinds-->24 query kinds<!--/figure-->**
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

**A conversation, and what a reference costs.** `runtime/conversation.py` puts
an episodic register of turns in front of the session, so that a turn may
refer back to an earlier one. Three declared shapes are follow-ups and nothing
else is — a pronoun (*describe it*), an end-flip (*and the smallest?*) and a
subject substitution (*and oxygen?*) — and a candidate antecedent is
**licensed** exactly when the query it produces solves, so the reference is
decided by what the registers hold. Recency decides between turns, licensing
within one, and where the deciding side offers two licensed candidates the
layer refuses rather than choosing: the fourteen rows tied at the top of the
lexicon's `abstract_concrete` column give *describe it* fourteen equally good
referents. It binds **<!--figure:conversation-answered-->8<!--/figure-->** of
**<!--figure:conversation-declared-count-->15<!--/figure-->** declared
follow-ups and refuses **<!--figure:conversation-refused-->7<!--/figure-->**,
all **<!--figure:conversation-as-declared-->15<!--/figure-->** as declared,
where a session with no memory answers
**<!--figure:conversation-alone-->0<!--/figure-->**. No answer is new: every
rewritten query is answered by the solver that would have answered it written
out in full. Proved in `RequestProject/GLM/Conversation.lean`. Write-up:
[`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md).

**A relation written as one word, and a resolved follow-up kept.**
`reasoning/role_binding.py` writes a typed relation *R(A, B)* into a single
24-bit word by exclusive-or over parity readings, the role carried by a
permutation of the coordinates rather than by a carrier. Unbinding returns the
filler's reading with **no side condition** — proved in
`RequestProject/GLM/RoleBinding.lean` — and turning that reading into a *name*
is worth exactly what the registers are worth:
**<!--figure:binding-nameable-->424<!--/figure-->** of the
**<!--figure:binding-carriers-->1,143<!--/figure-->** carriers read uniquely
and the other **<!--figure:binding-ambiguous-->719<!--/figure-->** force a
refusal, the largest fibre holding
**<!--figure:binding-largest-fibre-->136<!--/figure-->** physics carriers at
all-zero parity. The product binding the same material offers beside it is
**refuted**: one zero coordinate makes two fillers bind alike, and
**<!--figure:binding-product-zero-->1,133<!--/figure-->** of the carriers read
zero somewhere. Beside it, `runtime/plan_store.py` keeps a resolved follow-up
— refusals exactly as bindings — under a digest of the whole conversation it
was resolved in, and `Conversation` takes one as an optional `store=`: all
**<!--figure:planstore-replayed-->15<!--/figure-->** declared follow-ups replay
unchanged and the licensing trials fall from
**<!--figure:planstore-trials-first-->27<!--/figure-->** to
**<!--figure:planstore-trials-replayed-->0<!--/figure-->**. Proved in
`RequestProject/GLM/PlanStore.lean`. Write-up:
[`SUPPLIED_PORTS_STUDY.md`](studies/SUPPLIED_PORTS_STUDY.md).

**Frames that derive, with a certificate.** The typed planner, the default
reading of every command-line question since Phase 63, carries frames whose
answers no register holds, each checked by `reasoning/certificates.py`:
Bézout, linear Diophantine equations and bounded factorisation (Phase 62);
consistency of a register value with a quoted value or the declared standard,
read at the precision each is held to, with an ordering between overlapping
readings refused; the simplest fraction a decimal pins down, answered only
when every rival's denominator is at least twice the answer's; and dimensional
equations solved exactly, with a certificate for unique, impossible and
undetermined. `python3 -m glm_universal.tools cognition` runs every experiment
of the study; the certificates are proved in
`RequestProject/GLM/CognitionRoundTwo.lean`. Write-up:
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md).

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
the 3766 declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly 3766/3766 with 0 coordinate errors;
3217 distinct addresses, and the quantiser adds no conflation of its own;
nearest-by-address shares a file 722 times against 32 for a SHA-256 control and
32 for a seeded reshuffle, with chance at ≈ 1.00 %. `report lean`.
Write-up: [`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md).

**The register where the address is the only reader.** In the anonymous
register a query's identifiers are not the corpus's, by theorem
(`GLM.Anonymous.overlap_anonymise_eq_zero`): over 883 queries the text search
falls 767 → 85 and the identifier address book 413 → 46 against 49 by chance,
where the structural address holds 258 → 182. Write-up:
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
<!--figure:fieldsurface-rows-->9,248<!--/figure--> rows and
<!--figure:fieldsurface-pairs-->55,173<!--/figure--> addressable `(row,
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

**The ordering operation, and the refusal it is built around.**
`reasoning/coordinate_order.py` reads one coordinate off *two* rows through
the field surface and orders them exactly in rationals — `order
abstract_concrete of energy and water`, the `ordering` query kind. Each side
is a *reading*: a value together with the scale it was read on, `table:field`,
and a coordinate held inside a mapping field — which is how the lexicon
register keeps its ten semantic primitives — is read as a coordinate of that
field. It refuses in <!--figure:ordering-reasons-->3<!--/figure--> named ways:
a coordinate the row does not hold, a reading that is a label rather than a
quantity, and two readings on different scales. The last is the point of it,
and it is proved rather than asserted:
`GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive
rescaling that flips the comparison of two raw numbers, while
`order_scale_invariant` shows that no rescaling of a shared scale can.
Measured on <!--figure:ordering-declared-count-->7<!--/figure--> comparisons
declared before the run it answers <!--figure:ordering-answered-->4<!--/figure-->
and refuses <!--figure:ordering-refused-->3<!--/figure-->, every one as
declared, and it closes the one probe question the field surface named as
unreachable — all <!--figure:ordering-held-->10<!--/figure-->
held-and-unreachable questions are now parsed. `tools ordering`. Write-up:
[`ORDERING_STUDY.md`](studies/ORDERING_STUDY.md).

**The column, not the pair.** The `extremum` query kind reads one coordinate
off **every** row of one declared table and returns the end of it, or refuses.
The end is read off the word that opens the question — `largest`, `highest`,
`maximum` against `smallest`, `lowest`, `minimum` — and every row attaining it
is named rather than one of them picked: fourteen of the lexicon register's
rows sit at the concrete end of `abstract_concrete`, and choosing between them
would be a choice the register does not make. It refuses in
<!--figure:extremum-reasons-->4<!--/figure--> named ways, two of them boundaries
the system had no way to state before. A column with a hole in it has no
extremum — 23 of the element register's 118 rows record
`electronegativity_pauling` as missing, and
`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a
column where the extremum over the rows that are filled in is a different value
at a different row, so an answer over the present rows is wrong rather than
partial. A column gathered from two scales is not one column, which is the
ordering operation's `different-scale` one level up, and
`extremum_not_invariant_under_one_row_rescaling` is why. Measured on
<!--figure:extremum-declared-count-->8<!--/figure--> columns declared before the
run it folds <!--figure:extremum-answered-->4<!--/figure--> and refuses
<!--figure:extremum-refused-->4<!--/figure-->, every one as declared.
`tools extremum`. Write-up:
[`COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md).

**The scales, written down.** `reasoning/scale_conversion.py` holds the
declared table the two operations above did not have: one row per scale,
naming the quantity it measures, the canonical unit of that quantity and the
exact positive-affine map into it, together with the source the numbers came
from. <!--figure:scales-rows-->9<!--/figure--> rows over
<!--figure:scales-quantities-->4<!--/figure--> quantities — mass in `u`, molar
energy in `kJ·mol⁻¹`, temperature in `K`, length in `pm`. The ordering
operation consults it when the two readings are on different scales and the
extremum operation when a column is gathered by quantity rather than by table,
so `largest mass` now folds the element rows and the molecule rows together;
neither gains an answer anywhere the table is silent, and
`GLM.ScaleConversion.orderWith_conservative` is that stated rather than
hoped. That a conversion may be composed into a comparison at all is
`cmpQ_apply` and `order_conversion_invariant`; that the declaration and not
the code is what licenses a bridge is `the_table_carries_the_claim`; the two
things it must not do are `negative_factor_flips_the_verdict` and
`raw_gather_names_the_wrong_row`. Measured on
<!--figure:scales-declared-->12<!--/figure--> questions declared before the run
it answers <!--figure:scales-answered-->7<!--/figure--> and refuses
<!--figure:scales-refused-->5<!--/figure-->, every one as declared, and across
the whole field surface it relates
<!--figure:scales-bridged-->6<!--/figure--> of
<!--figure:scales-pairs-->7,750<!--/figure--> pairs of
<!--figure:scales-numeric-->125<!--/figure--> numeric scales — the rest stay
refused, which is what *declared* costs. `tools scales`. Write-up:
[`SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md).

**Typed question plans.** `runtime/semantic_plan.py` is the bridge from an
English question to the operations the session already has:
**<!--figure:plans-frames-->18<!--/figure-->** frames, each of which reads one
shape of question into a plan whose slots are grounded against the field
surface and the row's own fields, run, and accepted only when every licensed
plan agrees; with none licensed the answer is the grammar's own. Two frames
compute — exact integer arithmetic, and conversion over a declared table of
**<!--figure:plans-units-->17<!--/figure-->** units whose factors are
definitions. Reached with `GLM.py --plan` or
`GeometricSession.ask_planned`; measured by `tools plans` on the frozen probe
and four sets in `evaluation/heldout.py`, three of them committed before the
planner existed. Proved in `RequestProject/GLM/SemanticPlan.lean`. Write-up:
[`SEMANTIC_PLAN_STUDY.md`](studies/SEMANTIC_PLAN_STUDY.md).

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

The end-to-end set is **177 of 177** and every one of its twenty-eight refusals is a
`boundary` — a theorem or a stated commitment — rather than a `gap`. What
remains open is listed below, and none of it is a question the evaluation set
asks.

### 3.2 Named as untouched — all closed, and what each closure left

Every item that used to stand on this list is closed; each is recorded in
[`MASTER_PLAN.md`](MASTER_PLAN.md) with the study that closed it. What the
closures left behind is §3.4.

* **The infinite-dimensional half of the VOA bridge.** `VOA.lean` builds the
  state–field map at the Griess layer (the partial 2A axial algebra on axes) and shows where a finite model stops
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
[`MASTER_PLAN.md`](MASTER_PLAN.md) names Phase 63 as where the next round
starts and points back here. The candidates are ordered: the first is the one that bears
most directly on the standing target.

**H. Substrate-native cognition, round three — named by Phase 63.** In the
order of the study's §8: demote (or narrow) the two chemistry completion rules
that fail nested holdouts, `covalent_radius_pm` and `electron_affinity_eV`;
semantic judgements as annotated provenance (E4); frames generated from a
declaration rather than written by hand (E6); deeper PCGS proofs (E7); a second
independent reading for the deep-hole fork (X1); and concept 6, which waits on
a trilinear object in the runtime.
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md) §8.

**E. Derivation across a declared union of wheels — named by Phase 59.** The
engineering surface derives inside one wheel at a time, as the formula study's
protocol does, and so refuses *derive power from pressure and volume flow
rate*; across the union of the ten wheels that formula (hydraulic power)
follows from W5 and W6. A second mode that names the union it used in the
answer, measured on a set written for it, would say what composition gains
and what it gets wrong. [`ENGINEERING_LANGUAGE_STUDY.md`](studies/ENGINEERING_LANGUAGE_STUDY.md) §3.

**F. Typed physical operators — named by Phase 59.** Monomial wheels cannot
separate real, reactive and apparent power (W2-03), nor dot from cross
product. Complex power with conjugation, over the Gaussian rationals the
Smith chart already uses, is the smallest step. The record's Priority 5.

**G. The archive Lean left behind — named by Phase 60, narrowed by Phase 61.**
Phase 61 rebuilt the small files the supplied-material ledger named —
`GolayMOG.lean`, `Distinction.lean`, `Seeds.lean`, `Fibre.lean`,
`Cheapest.lean` and `Independence.lean` — as `RequestProject/GLM/GolayMOG.lean`,
`Distinction.lean` and `SeedRoles.lean`, proving the irrationality of `e` that
they had assumed. What remains (Appendix C.3 of
[`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md)) is the language half of
`mog_cube_1`, about thirty files, and the unported part of `ObserverY.lean`; no
code path reads either yet. The vision experiments script
(`glm_vision_experiments_v14.py`) is the same kind of candidate on the Python
side.

**A. The planner as the default path — done in Phase 63.** The planner now
reads first, and `--grammar` opts out. What follows is the note as it was
written: the typed planner was opt-in because the command line renders every answer as a three-column
trace and a computed plan (an exact sum, a conversion, a primality witness)
has no trace kind yet. Asked in-process, the 177 contract cases differ in two
answers through the planner and both still pass; what remains is a trace for
the planner's own computations, then the switch, then the contract set run
through it. [`SEMANTIC_PLAN_STUDY.md`](studies/SEMANTIC_PLAN_STUDY.md) §8.

**B. A held-out set nobody on the project wrote — named this round.** The
held-out sets were committed before the planner and share its author; an
independently written set of questions, with labels from outside the
registers, is the test that would separate reach from anticipation. The
scoring rule and the harness exist (`evaluation/heldout.py`,
`reasoning/typed_plans.py`); only the questions are missing.

**C. The register against the world — partly done in Phase 63.** A question
can now ask whether a register value is consistent with the declared standard
table, at the precision each is held to; the full discrepancy report over
every row is still open. The planner's one
wrong answer is the element register holding iron's atomic weight as `55.84`
where the IUPAC value is `55.845`. The roadmap's external-truth layer — a
discrepancy report of register values against cited standard values, never
overwriting the register — would find every such row rather than the one a
question happened to reach.

**D. Discourse state, typed.** The conversation layer binds three surface
shapes of follow-up; the planner's typed slots are the state a fourth shape
needs (*the one before that*, *both of them*), and a set-valued referent is
what candidate 0 below asks for.

**0. The second turn, carried further — named the round before last.** The conversation
layer binds three declared shapes of follow-up and refuses everything else,
and the two things it most obviously cannot do are each a round: a **fourth
shape** that is not a surface pattern at all — *the one before that*, *both of
them*, *why?* — and a **tie carried forward rather than refused**, so that
*describe it* after a fourteen-row tie asks its question of all fourteen and
reports a column rather than a refusal. The second is the more interesting:
it turns the layer's sharpest refusal into the extremum operation's kind of
answer, and it needs a statement of what *the answer for several rows at once*
is before it needs any code.
[`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md) §8, whose §9 now
records the outcome of every piece of the supplied material: four were taken
in Phase 56 — two shipped, one measured into the sandbox and one refuted — and
the rest stand with what they would have to measure to earn a round.

**1. The two halves of the conversion table that are not yet earned — named
last round.** The declared table relates nine scales over four quantities, and two
of its commitments are written but untested. The affine shape admits an
**offset** and no declared row uses one, so the half of
`GLM.ScaleConversion.cmpQ_apply` that the offset exercises is proved and not
shipped: a register holding a temperature in degrees Celsius, or any scale
that does not start at its quantity's zero, is what would settle it. And the
table declares a **unit** rather than a measurand, so it cannot say that an
atomic radius and a covalent radius are two different measurements that happen
to share picometres. A second declaration — measurands, and which pairs of
them are comparable — is the harder and more interesting of the two, because
it is the first thing in this system that would have to be argued for rather
than looked up.
[`SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md) §9.

**2. What a fold other than a maximum does with a hole.** The extremum
operation refuses a column with a missing reading, and proves why. A rank, a
median or a top-*k* over the same column each need their own statement of what
a hole does to them — a median over the present rows is not the median, but it
is wrong in a different way and by a different amount — and none of the three
is built. The narrower question beside it is the answerable one the refusal
declines: *of the rows that are filled in, which is the largest?* is a
different question, and it would have to be asked as one, with the missing
rows named in the answer rather than in the refusal.
[`COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md) §7.

**3. The eight reasoning modules nothing runs — the other half of the wiring
audit.** The wiring
audit recorded in [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 56 reads the import
graph of the package from every entry point it actually runs from, and finds **8** of the
**89** `reasoning/` modules outside the closure: `deep_dive`, `llvq`,
`moonshine`, `pcgs`, `salvage`, `salvage_second`, `stability` and `tie_break`.
Every one of them has a test file and a study, so each is a result that was
reached, checked and written up — and then left where nothing on the machine's
own path can call it. Two of them (`llvq`, `salvage`) are named only inside a
generated recompute script, which is real but runs only when a reader
recomputes a receipt; three more (`deep_dive`, `pcgs`, `salvage_second`) are
catalogued as file paths in `reasoning/combiner.py`'s source table without
ever being imported. The round this becomes is not a port: it is one decision
per module, *reachable or retired*, taken with its study open, and the honest
outcome for some of them is the archive. Re-read it with
`python3 studies/scripts/wiring_audit.py`.

*Closed this round (Phase 57):* candidate 4 of the list as it stood, *the
measurements no reader sees*. All **20** registered figure keys that no
document quoted are now quoted — none was retired, because each was a number
its document was already saying by hand or should have been saying — and the
converse of **D6** is a checked rule rather than a habit:
`tests/test_figures.py::TestEveryRegisteredFigureIsQuoted` fails when a
registered key is read by no document, and when a document quotes a key the
registry does not hold. Closing it exposed a defect worth the round on its
own: `corpus-documents` counted **98** documents where the corpus study's own
inventory counted **95**, because the key counted the three documents the
machine *generates*, which are outputs of the corpus rather than parts of it;
the three document-count keys are now taken over the written corpus, the set
the digest guards. It also turned up a plain D6 breach — the
operation-escalation study was typing its deciding figure by hand. The audit
now reads **135 registered, 135 quoted, 0 never quoted**
(`python3 studies/scripts/wiring_audit.py`).
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 57.

*Closed in Phase 56:* not a candidate from this list but the four
rows of [`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md) §9 — the
supplied conversational material Phase 54 read, ran and left unported. The
**role–filler binding** and the **procedural-plan store** ship:
`reasoning/role_binding.py` writes a typed relation between two named carriers
as one 24-bit word whose inverse is itself, and `runtime/plan_store.py` keeps
a resolved follow-up — refusals exactly as answers — under a digest of the
whole conversation it was resolved in, wired into `runtime/conversation.py` as
an optional `store=`. `RequestProject/GLM/RoleBinding.lean` and
`RequestProject/GLM/PlanStore.lean` prove what is a theorem rather than a rate:
unbinding inverts binding for every role and pair, recovery by name is sound
and refuses exactly when the reading is not unique, replay agrees with running
and preserves a refusal, and the exact key separates two conversations that
share a follow-up where the coarse one does not. The **four-register memory
split** and the **Lean-source generator** were measured and declined: both sit
in `glm_universal/sandbox/` with a computed checklist that says `ready is
False`. Under directive **D15** it moved **addressing** and **refusal**.
[`SUPPLIED_PORTS_STUDY.md`](studies/SUPPLIED_PORTS_STUDY.md). It also carried
the wiring audit that became candidate 3 above and the round Phase 57 then
took, and it closed on two
defects of its own that the suite found: the plan store's digest went round
`hashlib` instead of `glm_universal.integrity`, which breaks **D3**, and the
binding was an unclassified exclusive-or site in `reasoning/combiner.py`'s
table. Both are fixed, and the sandbox now reads its own occupancy rather than
asserting it (`glm_universal.sandbox.occupancy_report`).

*Closed in Phase 55:* candidate 1 of the list as it then stood — the scales
neither operation could bridge. `glm_universal.reasoning.scale_conversion`
declares nine scales over four quantities, each row an exact positive-affine
map into the quantity's canonical unit with the source its numbers came from,
and `RequestProject/GLM/ScaleConversion.lean` proves that a positive
conversion composed into the comparison leaves the verdict alone, that the
wider operation never changes an answer the bare one gave, that its silence is
still exactly stated, and that the declaration itself carries the claim. On a
declared set of twelve questions it answers seven and refuses five, all twelve
as declared, and it leaves the two operations underneath it unchanged on their
own declared sets. Under directive **D15** it moved **refusal** — three of the
five refusals are comparisons the table was given the chance to license and
did not — and widened **derivation** to a fold over rows of two tables at
once. [`SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md).

*Closed in Phase 54:* not a candidate from this list but the
material supplied with the round — `source_material/conversation_experiment/`,
tested rather than believed. All eight of its scripts run unmodified against
the package; two of its headline claims are refuted (the higher-order analogy
whose second constraint has no exact solution, and the periodic-table reading
that renames two carrier coordinates); and the one thing in it the system
could not do is built, measured, proved and released: a turn that refers back
to an earlier turn, bound by licensing, `8` of `15` declared follow-ups bound
and `7` refused against `0` for a session with no memory. Under directive
**D15** it moved **addressing** and **refusal**.
[`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md).

*Closed in Phase 53:* candidate 1 of the round before it — the column
rather than the pair. The `extremum` query kind and
`reasoning/column_extremum.py` read one coordinate off every row of one
declared table and fold it exactly, naming every row that attains the end, or
refuse under one of four named reasons, and
`RequestProject/GLM/ColumnExtremum.lean` proves that the silence is exactly
the second scale, the hole and the empty column, that the value returned is
one of the column's own with nothing past it, that the rows named are exactly
the rows attaining it, and that both refusals are results rather than
fussiness. Under directive **D15** it moved **derivation** — a fold over
addressed readings, which no register holds — and **refusal**, on a declared
task set of eight columns, all eight as declared.
[`COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md).

*Closed in Phase 51:* candidate 1 of the last round — the comparison
the field surface could not make. The `ordering` query kind and
`reasoning/coordinate_order.py` read one coordinate off two rows and order it
exactly, or refuse under one of three named reasons, and
`RequestProject/GLM/CoordinateOrder.lean` proves that the silence is exactly
the missing reading and the mismatched scale, that the answer is the order of
the two values, and that *same scale* is the right side condition because a
rescaling of one reading alone flips the comparison. Under directive **D15**
it moved **derivation** — of the weakest interesting kind, one exact
subtraction over two addressed readings — and **refusal**, on a declared task
set of seven comparisons, all seven as declared. All
<!--figure:ordering-held-->10<!--/figure--> of the probe's held-and-unreachable
questions are now parsed. [`ORDERING_STUDY.md`](studies/ORDERING_STUDY.md).

*Closed in Phase 50 (maintenance):* the release Phase 49 had not run,
and the six units that failed it — the UBP source audit taught to read the
declared float sites off the D11 inventory, the reasoning kernel's import
audit, the Lean file count, the query-escalation cache, and the relay and
anonymous measurements re-taken over the grown corpus. It moved none of
derivation, addressing or refusal, and leaves the candidates above unchanged.

*Closed in Phase 49:* the supplied *History Recorded in the Now*
material, decided rather than illustrated — nine claims settled, three of them
refuted, the refusal faculty moved on a declared task set, and the shipped
modulator's loop replaced by the closed form it was always computing.
[`NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md). It leaves two things
named there and not taken: the v4 query-loop reading, which has no control, and
the v4 higher-lattice escalation, which was argued rather than run.

*Closed in Phase 48 (maintenance):* the handover the round before it
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

**3. The empty rungs of the power-of-two family.** The family is complete as a
family and deliberately incomplete as a *ladder*: norms 2 and 256 are empty in
the ladder actually used, because the rungs that would fill them conflate. What
would close it is a rung at those norms that does not — Construction `A` over a
shortened code, or the `D₄`/`E₈` layers, which the scaling does not generate.
[`NORM_FAMILY_STUDY.md`](studies/NORM_FAMILY_STUDY.md).

**4. A register that arrives anonymous on its own.** Renaming is a faithful
model of a cross-vocabulary goal and it is still a model. The measurement to
want is the same table over goals from a second Lean development, or from a
generator, scored against the same controls — a register nobody constructed.

**5. The leak in the feature map.** The shipped map counts the type vocabulary
wherever it occurs, including inside an identifier, so 39 of 883 queries lose a
coordinate when their names go: a name creeping into a reading that is supposed
to be structural. Either the map is narrowed to count type words only where
they are types, or the leak is priced.

**6. The separation criterion, still unmet.** `nearest_correct` in
`DeepHoleLadder.lean` says a reading names holes correctly whenever
`ρ = 2W/B < 1`. Measured, `ρ` falls from `3.90` to **`2.59`** across the ladder
and never crosses `1`, so a classifier that names 40 of 44 still cannot certify
a single *absence*: faithfulness needs `r ≥ 0.0659` where separation permits
`r < 0.0179`. Either a rung is found where `ρ < 1`, or a bound is proved saying
no reading of this family reaches it. Its companion is
`GLM.DeepHoleFailure.per_type_absent`, the certificate whose hypothesis is
currently unmet, so the theorem is instantiated nowhere.

**7. The thirteen unreached Niemeier types.** The ensemble reaches **10** of
the 23 root systems from the 14 declared centres; the other **13** are reported
as unreached and nothing is claimed about them. Reaching them means new
centres, and new centres mean a new pre-registration.

**8. What the adopted guard costs, and why the metric reading is safe.** The
guard refuses 137 queries it used to answer correctly. The room is in the
*reading* rather than in the contract — the weaker guard is measured and never
reaches safety — and the metric reading answers nothing wrongly on any of the
six operations while losing to the primary on four, which is a decomposition
worth understanding. A margin other than twice the nearest distance is the
obvious sweep. [`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md) §9.

**9. The planner's utility gate.** The reverse-call planner satisfies every
safety line of its promotion checklist and fails the one that decides it: on
this project's own evaluation set it gains nothing, because the refusals it is
offered are refusals it agrees with. The question that would close it is about
the **tool registry** — whether a tool exists that a problem-driven front end
could reach and the kind-driven dispatcher cannot. Until one does, directive
**D14** keeps the planner in the sandbox, imported by nothing the system
computes with.

**10. A conflation the rational reading must make.** Read alone, the exact
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
eight registers are described, and seven of the twenty-three answerable query
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
<!--figure:test-files-->109 test files<!--/figure--> are `lean-build`,
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
lake build                                                   # 133 Lean files, no sorry
rg -n 'sorry|admit' RequestProject/GLM                       # expect nothing
diff -r RequestProject/GLM overlay/glm_lean/RequestProject/GLM   # the two copies agree

cd overlay
PYTHONPATH=. GLM_EXHAUSTIVE=1 python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 -m glm_universal.capabilities           # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks             # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8    # 177 CLI cases
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
