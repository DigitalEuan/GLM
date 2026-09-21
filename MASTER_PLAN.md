# Master plan: wiring status


## Tier 0 — the coarse read

**Question.** What has each phase of the wiring plan delivered, and what does the next round start from?

**Verdict.** Phase 53 is closed; the candidates in [`STATUS.md`](STATUS.md) §3.4 are where the next round starts.

**Deciding figure.** Every closed phase names what was built, where it lives, and how to see it recompute itself.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

> **Positioning.** Before starting a round, read the Positioning section of
> [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md): what is claimed, what is
> not, and why an absence at one layer is not a refutation. It is stated once,
> there, and every document in this repository is written under it.

This document tracks the plan to fully wire the Geometric Language Machine,
eliminate the architectural simplifications, and implement multi-resolution
addressing. Each item says what was built, where it lives, and how to see it
recompute itself.

Everything below is reachable from the package's public API and from the query
runtime — **<!--figure:query-kinds-->24 query kinds<!--/figure-->**, **65 report subjects** and **8 registers** — is
covered by the test suite (<!--figure:test-files-->101 test files<!--/figure-->),
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
[`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md).

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

**Phase 53 closed the candidate Phase 52 named first, and §3.4 of
[`STATUS.md`](STATUS.md) is where the next round starts** — its first
candidate is now the one boundary both operations share: the scales neither
can bridge, and the declared table of conversions that would let them.
Phase 53 built the extremum over a whole column, which Phase 51 stopped short
of; Phase 52 closed the tail Phase 51 left; and Phase 51 closed the candidate
that had stood first since Phase 46 — the one question the field surface could
not reach. Phase 49 below took
supplied material rather than a candidate from that list, and says so; the
items Phase 38 listed and no round has taken stand below, unchanged too.

**Phase 38 is where those standing items were written down.** Phase 42 before
it took no candidate at all: it made the round loop cheap — the sign-off
ledger selective, the operating manual written, two directives added and the
historical record moved out of the status document — and recorded, under the
first of those directives, that it moved none of the three faculties. Phase 41
before that
took the declared failure Phase 40 left — the program-text operation answering
wrongly rather than refusing — and closed it by requiring a second reading to
agree: one of six declared configurations is adopted, the wrong answers are
gone, and what the guard costs is counted rather than glossed. Phase 40 before that
re-indexed the construction ladder by minimum squared norm, completed the
power-of-two family over it, escalated six operations that are not retrieval
together with the equation check, and measured the blockers against a
pre-registered language probe — returning two negatives and a declared failure,
all three of which are now the first items of §3.4 of
[`STATUS.md`](STATUS.md). Phase 39 before that generated the construction
ladder and walked it out from the middle. Phase 37 took the
question Phase 36 left — is the geometry's carry set a residue or a class? — and
answered it by naming the register first and measuring it second: a query is
*anonymous* when its identifiers are not the corpus's, and in that register the
text search and the identifier address book both fall to the hit rate chance
gives while the structural address holds most of what it had, with the stack's
existing gate handing the register over untuned. Phase 36 before it took the
standing negative result of the retrieval round and pushed it the other way by
making the faculties into a stack: a stated confidence gate, a stated quota,
and the geometry given only the queries the leading text faculty cannot read.
It is ahead of that leader on a tuning stride, on a disjoint held-out stride
and on goal queries, never below it at any window, and it carries **16**
queries against **1** lost where the matched controls carry **4** and **0** —
with `relay_confident` and `relay_carry` proved in Lean and the same relay run
in a register with no text in it. Phase 35 before it took
four of the five things the deep-hole rounds left behind and closed them as
mechanisms: escalation became a step of the ordinary query loop, the four
remaining failures were diagnosed and found to be the same mechanism as the
unmet separation criterion, cumulativity became a shipping condition with a
check, and the standing set of stalled results was ranked before the next
re-reading rather than after it. What stands now is §3.4 of
[`STATUS.md`](STATUS.md). Phase 32 took the four
items the untouched list had been carrying and closed each as a mechanism
rather than a stated limitation; Phase 31 took neither candidate but a
pre-registered question — is the fine-structure constant structurally
distinctive in the space the substrate permits? — and answered it with one
number under a stated null; Phase 28 took a supplied proposal — stop storing
the substrate's tables and generate them — and measured both the saving and
the generators; Phase 27 asked whether the substrate can do work rather than
hold a table.

---

Phases 14–36 are closed as well, and are recorded in the same archive.

| phase | what it closed |
|---|---|
| 14 | the layer chain made a real refinement, and the repository tidied |
| 15 | the layer chain audited at register scale |
| 16 | measure words as relative measures |
| 17 | the last third of the universality claim, the address layer audited, and the infinite-dimensional half of the VOA bridge |
| 18 | the two items Phase 16 left open, and a factor basis measured instead of asserted |
| 19 | the residue finished as a vocabulary decision |
| 20 | the recipe made into an object |
| 21 | the surface language driven off the descriptions |
| 22 | the branches deleted, and a second shape family |
| 23 | the four undescribed parts, and the four branches they were blocking |
| 24 | the quantiser's search, replaced by a lookup |
| 25 | the archive, read to the end |
| 26 | the dropped work, restored, and the archive's second reading closed |
| 27 | the address book made to do work, and the first loop |
| 28 | generated rather than stored, and the generators checked |
| 29 | the last stored table removed, and the cost of generating measured |
| 30 | the corpus itself made data: the tiered read, the entry point and its coverage claim, the addressed documents, and the studies' tables emitted rather than typed |
| 31 | the wobble landscape, pre-registered and measured: one statistic, two nulls, a gate fixed before the measurement, and **B = 1.79 bits** — weak, so the enumeration was not run |
| 32 | the four things the untouched list had been carrying: the cross-register analogy answered from an energy-conjugate register, sparse chemistry decided rather than blank, a standing rule for a vague `related_to` triple, and open vocabulary made a door — with every figure the growth moved re-measured |
| 33 | the Niemeier deep holes classified from trajectories: pre-registered, beating every control at **15 of 44** against 11 for the vertex count — and stopped by its own sanity check, which kept **3 of 10** labels under a bare seed change |
| 34 | the deep-hole ladder: the same question read one layer up, escalated over layer × budget cells until the law descends — **10 of 10** on the sanity check and **40 of 44** on the full query set at the joint reading with 1920 starts, with the separation criterion still unmet and said to be |
| 35 | what the deep-hole rounds left behind, taken as architecture rather than geometry: escalation made a step of the ordinary query loop (**no answer moves**, **no principled refusal converted**, **4 of 18** probes resolved above the first rung), the four remaining failures diagnosed as **rank-2 near misses on a closest pair** belonging to the very type whose spread stalls `ρ`, cumulativity made a shipping condition (**7** edges verified, **2** non-edges witnessed, **0** defects), the reverse-call planner built and **not promoted** behind directive D14, and the standing set of stalled results ranked before the next re-reading (**8** entries, **1** licensed) |
| 36 | the faculties made into a stack, and the standing negative result pushed the other way: a stated confidence gate of **1/10**, a stated quota and interleave, and the geometry given the queries the text layer cannot read — ahead of the text control on the tuning stride (**356 → 362** of 407), on a disjoint held-out stride (**354 → 358** of 406) and on goal queries (**710 → 715** of 813), never below it at any window; the gate fires on **66** of 1,614 queries and the geometry carries **16** against **1** lost, where a digest-and-reshuffle control carries **1** and a name search **none**; `relay_confident` and `relay_carry` in `RequestProject/GLM/Relay.lean` say what is a theorem rather than a hit rate; and the same relay run in a register with no text in it solves **2 of 50** ARC puzzles with a visual look that discards **95.3 %** of proposals |

| 37 | the register the relay's carry set pointed at, found and measured: a query whose identifiers are not the corpus's — a goal from another formalisation, modelled by renaming everything outside a declared vocabulary — where at k = 5 over **813** queries the text search falls **710 → 84** and the identifier address book **388 → 48**, both to the **48** hits chance gives, while the structural address holds **232 → 171** and leads every other faculty by more than a factor of two; a renaming cannot move a count of the syntax (`features_anonymise`), the identifier overlap it leaves is zero (`overlap_anonymise_eq_zero`) and the stack's existing gate therefore hands the register over (`relay_hands_over`, all in `RequestProject/GLM/Anonymous.lean`) — it fires on **538** of 813 where it fires on **24** of the same queries read plainly; and the shipped feature map is audited rather than idealised: it counts type words inside identifiers too, which moves a coordinate on **33** of 813 queries and never a logical, numeric, bracket or length coordinate |

The detail of each — what was built, where it lives and what recomputes it —
is in [`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md), kept as it was
written.  A phase is a record of a round, so it is archived by the same rule
as everything else: only the open phase is state.

---

## Phase 53 — the column, not the pair: one coordinate over every row, folded or refused

**Status: closed this round.** Under directive **D15** it moved **derivation**
and **refusal**, and it did not move addressing: the table and the coordinate
are the names the question already gives. It took candidate 1 of
[`STATUS.md`](STATUS.md) §3.4 — the operation Phase 51 declared itself to stop
short of.

**What was built.** `glm_universal.reasoning.column_extremum` and the
`extremum` query kind — `largest atomic_weight_u in element` — read one
coordinate off **every** row of one declared table through the same field
surface a single row is read through, and return the end of the column: the
value, exactly, the exact gap to the next distinct value, and **every** row
attaining it. The end is read off the word that opens the question, all six of
which are start-only keywords, because *the smallest vector of the Leech
lattice* asks for no column of any table. A coordinate held inside a mapping
field is a column too, which is how the lexicon register's ten semantic
primitives are reachable, and a derived column — `molar_mass_u`, recomputed
from the element register row by row — folds on the same terms as a stored
one.

**The two refusals it exists for.** A column with a hole in it is refused and
the missing rows are named: 23 of the element register's 118 rows record
`electronegativity_pauling` as missing, and the largest of the 95 present
values is the largest of the rows that happen to be filled in rather than of
the column. A column gathered from more than one scale is refused too — with
no table named, `line` is the Lean address book's and the package's own source
walk's, and the largest of those numbers jointly is a fact about neither. Both
are proved rather than asserted:
`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a
column whose extremum moves when its one hole is filled, and
`extremum_not_invariant_under_one_row_rescaling` a one-row rescaling that moves
the winner, where `extremum_scale_invariant` shows that rescaling the shared
scale moves the value by the factor and the winners not at all. Two further
reasons restate boundaries the field surface already had — a column of labels,
and a coordinate no row of the table holds.

**What was measured.** <!--figure:extremum-declared-count-->8<!--/figure-->
columns were declared before they were run — four to fold and one for each way
the operation may refuse — and all
<!--figure:extremum-as-declared-->8<!--/figure--> came out as declared:
<!--figure:extremum-answered-->4<!--/figure--> folded,
<!--figure:extremum-refused-->4<!--/figure--> refused, under all
<!--figure:extremum-reasons-->4<!--/figure--> named reasons.
<!--figure:extremum-ties-->1<!--/figure--> of the four answers is a tie —
fourteen rows at the concrete end of `abstract_concrete` — and it is reported
as a tie rather than resolved.

**Where it lives.** `reasoning/column_extremum.py`; the `extremum` kind in
`runtime/parser.py`, its solver in `runtime/session.py`, its column-3 template
in `runtime/tct_engine.py` and its one-rung ladder in
`runtime/escalation_loop.py`; `tools extremum`; eight evaluation cases (four
answers and four `boundary` refusals);
`glm_universal/tests/test_column_extremum.py`;
`RequestProject/GLM/ColumnExtremum.lean` (eleven theorems, no `sorry`); and
[`studies/COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md).

**What it moved elsewhere.** A new query kind is a change to three
measurements the tree takes of itself, and each was re-taken rather than
loosened: the sandbox planner's fallback reading is now taken over **14**
refusals rather than 10 — it refuses all fourteen, so its utility gate still
fails and it is still not promoted; the iteration-cost ledger's blast radius
moved with the new test file and the new Lean file (101 units, 123 Lean files,
89 units an edit to any Lean file used to make stale, worst single file 84);
and the end-to-end set grew to **172** cases with 8 of them the extremum kind's
own.

**The release, earned rather than reported.** `signoff --verify-release`
signs **101 of 101 test files and 7 of 7 instruments** with the exhaustive
cases on, `corpus --check --all` is current, the end-to-end evaluation is
**172 / 172** — 146 answered and 26 refused as expected, every one
`boundary` — and `lake build` is clean over the 122 Lean files with no
`sorry`. The order that earned it is the one the working note records:
documents first, then refresh, then release, and the suite sentence a second
release behind the run that measured it.

**What it does not claim.** A fold over addressed readings is the whole of the
derivation — 118 exact comparisons and a set of maximisers — and nothing here
parses English: *which element is the most electronegative?* is still
hand-translated, and on that column the honest answer is the refusal. A column
is one table, no conversion between scales is held, and the fold is a maximum:
a rank, a median or a top-*k* would each need their own statement of what a
hole does to them.

---

## Phase 52 — the tail of a round, closed: eight counts re-taken and the release earned

**Status: closed.** It is **maintenance**, and says so in those
words: under directive **D15** it moved none of derivation, addressing or
refusal. What it did was finish Phase 51 — which stopped with its counts
re-taken in the working note but not written into the documents, and with no
release run — and then ask the release question over the whole tree.

**What the tree looked like on pick-up.** `corpus --check` failed on four
generated artefacts and on the working note's own tier-0 block, and the counts
the tree quotes about itself had drifted in eight places, four of them
measurements rather than tallies. Every one was re-taken and written down
rather than relaxed:

* **3,422 declarations** in the formal development, not 3,400 — read back
  3,422 / 3,422 with 0 coordinate errors, 3,038 distinct addresses, and
  nearest-by-address sharing a file 686 / 34 / 22 against a closed-form chance
  of ≈ 1.07 %.
* **The relay gate reading moved up.** The strict gain now holds across the
  whole declared band, 1/20 through 1/4, where it used to stop at 1/5 and draw
  level at the top gate; the relay carries 19 and loses 0, against 1 for the
  digest-and-reshuffle control and 2 for the name search. The study's prose,
  its tier-0 figure and the three other documents that quote it now say what
  the instrument reports, and `test_stack.py` asserts the new reading on both
  halves rather than the old one.
* **The planner is now consulted on 10 refusals, not 4**, because the field
  surface and the ordering kind each added three; all ten stop, and the two it
  marks ill formed are the two it marked when four reached it.
* **The end-to-end set is 164 cases with 22 expected refusals**, all
  `boundary`: the capability assessment's per-kind table, its refusal table and
  the status document's sentence were all written for 149 and 16.
* **121 Lean files**, **1,143 carriers** (the lexicon having grown 95 → 149),
  **145 modules** with the reasoning sub-package at 86, and the suite at
  **3,990 tests across 99 of the 100 test files, 15,431 subtests**.

**One test was brittle rather than wrong, and was fixed at the root.**
`test_signoff.py::TestTheRecordedTotals` gave its synthetic document check a
two-digit sentinel and asserted that the sentinel never reaches the totals.
The suite passed 99 counted test files this round, so the sentinel *was* a
legitimate total and the unit failed. It now uses a value no total can take.

**The release, earned rather than reported.** `--verify-release` signs **100
of 100 test files and 7 of 7 instruments** with the exhaustive cases on,
`corpus --check --all` is current, the evaluation is 164 / 164 and `lake build`
is clean with no `sorry`. The order that got there is the one the working note
records and this round re-learned twice: documents first, then refresh, then
release — a document edited after a release makes the units that read it stale
again.

---

## Phase 51 — the comparison a surface could not make: two readings, ordered or refused

**Status: closed.** Under directive **D15** it moved **derivation**
and **refusal**, and it did not move addressing: both readings are found by
the names the question already gives. It took candidate 1 of
[`STATUS.md`](STATUS.md) §3.4 — the question the field surface of Phase 46
declared unreachable before that surface was built.

**What was built.** `glm_universal.reasoning.coordinate_order` and the
`ordering` query kind — `order abstract_concrete of energy and water` — read
one coordinate off *two* rows through the field surface and order them exactly
in rationals. Each side is a **reading**: a value together with the scale it
was read on, written `table:field`. A coordinate held inside a mapping field,
which is how the lexicon register keeps its ten semantic primitives, is read
as a coordinate of that field and the scale records the containing field, so
`carrier:lexicon:primitives.abstract_concrete` cannot be confused with a field
of that name. The verdict names a **pole** only where the register declares
one, and says that the declaration is the register's rather than the
operation's.

**The refusal is the result, not the cost.** Three named reasons —
`unreadable` (the row does not carry the coordinate; the surface's own refusal
restated), `not-ordered` (a label rather than a quantity) and
`different-scale`. The last is what the operation exists for: `line` is held
by both the Lean address book and the package's own source walk, and two
readings on different scales have no common order.
`GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive
rescaling that flips the comparison of two raw numbers, while
`order_scale_invariant` shows that no rescaling of a *shared* scale can.

**What was measured.** Seven comparisons were declared before they were run —
the probe question, three more answerable ones over three different tables,
and the three refusals — and all
<!--figure:ordering-as-declared-->7<!--/figure--> came out as declared:
<!--figure:ordering-answered-->4<!--/figure--> answered,
<!--figure:ordering-refused-->3<!--/figure--> refused. Scored through the same
oracle, on the frozen table with one row replaced, the probe goes
<!--figure:ordering-parsed-before-->15<!--/figure--> →
<!--figure:ordering-parsed-after-->16<!--/figure--> parsed and the last of the
<!--figure:ordering-held-->10<!--/figure--> held-and-unreachable questions is
closed. The replaced row is scored at `pole_row` — the row the answer puts at
the named end — so it can only be matched by an answer that picks a row, and
the no-smuggling rule is re-checked over the whole table.

**Where it lives.** `reasoning/coordinate_order.py`; the `ordering` kind in
`runtime/parser.py`, its solver in `runtime/session.py` and its column-3
template in `runtime/tct_engine.py`; `tools ordering`; seven evaluation cases
(four answers and three `boundary` refusals);
`glm_universal/tests/test_coordinate_order.py`;
`RequestProject/GLM/CoordinateOrder.lean` (twelve theorems, no `sorry`); and
[`studies/ORDERING_STUDY.md`](studies/ORDERING_STUDY.md).

**What moved with the corpus, and was re-taken rather than loosened.** One
new Lean file grows the corpus the two cross-vocabulary measurements read, so
both were re-measured: the relay now runs over 1,712 queries with the gate
firing on 58 of them and the stack ahead of the text control 371 → 377 of 428
on the tuning stride, 368 → 373 of 428 held out and 739 → 747 of 856 on bare
goals, carrying 19 and losing 0; the anonymous register reads 856 queries, the
text search falling 739 → 83 and the identifier address book 426 → 56, both to
the 47 hits chance gives, while the structural address holds 232 → 161. Their
two evaluation phrases were updated to what the instruments now report.

**What it does not claim.** One exact subtraction over two addressed readings
is the whole of the derivation, the coordinate's meaning is the register's
declaration, and nothing here parses English — the question is still
hand-translated into the system's own grammar. The operation composes exactly
two readings; the extremum over a whole column is a different shape, and it
is what Phase 53 above built.

---

## Phase 50 — the release Phase 49 never ran, and the five measurements it hid

**Status: closed this round.** It is **maintenance**, and says so in those
words: under directive **D15** it moved none of derivation, addressing or
refusal. What it did was ask the release question that Phase 49 left unasked,
and repair everything that question turned up — five of them measurements that
had moved and one a discipline the new code had quietly broken.

**What the tree looked like on pick-up.** `corpus --check` reported `DIGEST.md`,
the document address book and the generated blocks of
`studies/CORPUS_ADDRESS_STUDY.md` stale; the whiteboard named one step
remaining, the release. Running it failed six units, none of them noise:

* **The core float ban was broken, and the audit had no way to say so.**
  `reasoning/now_float_control.py` is the second declared float site, added by
  Phase 49 and warranted under **D11** — but it sits inside `reasoning`, which
  is one of the six sub-packages the UBP claim is made for, and
  `reasoning/blueprint.py` knew nothing about declared sites. Rather than
  loosen the check, the audit now *reads* the declared list off the D11
  inventory in `reasoning/exactness.py` (`blueprint.declared_float_sites`), so
  a float inside the core is excused only where its warrant is published. The
  raw per-package tally still counts every float the scan finds; the new
  `declared_`/`undeclared_` columns are what the claim is decided on, and the
  reading names the site rather than hiding it. Four tests in
  `test_blueprint.py` pin that split.
* **The reasoning kernel's import audit had not been told about `time`.** The
  now-receipt audit carries one timing, in integer nanoseconds
  (`time.monotonic_ns`, which is not a float clock). The allow-list in
  `test_reasoning.py` now carries it with the same one-use warrant the other
  four entries carry.
* **The relay's gate reading had moved, and in its favour.** At a gate of
  `1/4` the relay used to fall one query behind the text control; over the
  grown corpus it now draws level (`363/425` against `363/425`), so
  `gain_never_below_across_the_gate` is **true** where it was false, while the
  strict gain still runs out after `1/5`. Re-measured, not re-tuned.
* **The anonymous register had moved with the Lean corpus**, from 846 queries
  to 850: the text search falls `734 -> 72 of 850` and the identifier address
  book `422 -> 47 of 850`, both to the 48 hits chance gives, while the
  structural address holds `225 -> 154 of 850`. The two evaluation phrases
  were re-measured, as was the relay's (`363 -> 365 of 425`, the gate on
  `52 of 1700`, carrying 12 and losing 1).
* **Two counts of the tree had drifted**: the number-theory evidence paper
  quoted 119 Lean files where the tree holds 120, and the query-escalation
  measurement cache was stale against the edited evaluation set and was
  re-taken.

**What the release now says.** `signoff --verify-release` reports **99 of 99
test files and 7 of 7 instruments** signed with the exhaustive cases on; the
suite is **<!--figure:suite-->4,038 tests across 100 of the 101 test files, 15,644 subtests, outside the document check<!--/figure-->**,
one process with `GLM_EXHAUSTIVE=1` collecting 3,979; the end-to-end
evaluation is **157 / 157** with 19 expected refusals; `corpus --check` is
current; and `lake build` is clean over 120 Lean files with no `sorry`.

**What it leaves.** The candidates in [`STATUS.md`](STATUS.md) §3.4 are
untouched by it, which is what a maintenance round should leave behind.

---

## Phase 49 — history recorded in the now: the supplied claim, decided

**Status: closed this round.** Under directive **D15** it moved **refusal**,
on a declared task set, and it did not move derivation or addressing: the
project's evaluation set is unchanged, and the round says so rather than
counting the shipped path it made cheap as progress.

**What it took.** Four supplied studies and a script —
`source_material/HISTORY_RECORDED_NOW_STUDY.md` and its v2, v3 and v4 sequels,
and `source_material/history_recorded_now.py`, which imports this package and
runs here unmodified. Their central claim is that the state of an
exact-rational process is the exact integral of everything that led to it, so
the state is the receipt of its own history. This was not a candidate from
§3.4 of [`STATUS.md`](STATUS.md); it was taken because the material is a
program against this substrate, and so its claims are decidable here.

**What it settled.** Nine claims, each with the function that settles it, in
[`studies/NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md) §8.

* **The identity holds.** The accumulator after `n` ticks is exactly
  `Int.fract (∑ input)` and the emitted count exactly `⌊∑ input⌋`
  (`GLM.NowReceipt.acc_eq_fract`, `count_eq_floor`), and two runs leave the
  same accumulator exactly when their integrals agree modulo one
  (`acc_eq_iff_fract_eq`). The receipt is one rational.
* **The reading of it does not.** With the control the supplied studies omit —
  predict the count with the state *withheld* — all 20 of their demonstration
  runs are recovered without it. Enumerated exhaustively, **4,096** histories
  leave **4** distinct receipts, the largest class holding 1,024;
  `receipt_collision` is the two-tick witness.
* **The capacity extrapolation is refuted.** The reachable receipts on a `1/q`
  grid number `q` however long the run (`acc_mem_grid`,
  `receipt_pigeonhole`), so v3's "about `10²⁰` ticks of history in a
  24-rational carrier" measures the target's precision, not a capacity. The
  "irrational target" of those runs is `math.sqrt(2)/2` — a float, hence a
  dyadic of denominator `2⁵³`, which is why their bit column drifts *down*.
* **The comparative claim is unsupported.** The float loop and the exact loop
  were run side by side, under the package's second declared float site
  (`reasoning/now_float_control.py`, D9 and D11): no divergence in a bit over
  100,000 ticks, and none at two million with the exhaustive switch on. What
  exactness buys is the bound, not this horizon.
* **The seven dimensions are three.** On carrier pairs built to share a
  coordinate, the entropy reading agrees on all of them and the tax and the
  composition do not: the coordinate, the entropy, the scale and the tax are
  readings of the composition, leaving three free readings and two labels.
* **The arrow of time says nothing yet.** The cumulative tax is monotone
  because a running total of non-negative terms is (`cumulative_mono`), and
  v4's differential tax is flat for a decaying carrier — which v4 reports
  itself, and which is reproduced here.

**What the system gained.** Two things, kept apart. *Refusal*: nine declared
history questions, of which the supplied recipe answers all nine and is
therefore wrong on four; the module answers five and refuses four, each
refusal carrying the colliding pair. *Maintenance*: the count and bit closed
forms (`const_count_eq_floor`, `const_bit_eq_floor_diff`) now serve
`exact_real.delta_sigma_average` and `delta_sigma_bits`, so the shipped `real`
query kind reads its 512-tick average off the target instead of running the
loop — identical output, and the wobble landscape cache re-taken after the
change differs only in the digest of the code it was taken from.

**Where it lives.** `RequestProject/GLM/NowReceipt.lean` (nine theorems, no
`sorry`), `overlay/glm_universal/reasoning/now_receipt.py`,
`overlay/glm_universal/reasoning/now_float_control.py`,
`overlay/glm_universal/tests/test_now_receipt.py`,
[`studies/NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md).

**What it deliberately left.** The v4 query-loop reading ("6 of 6 resolved")
has no control and is not rebuilt here; the v4 higher-lattice escalation is an
argument about a code's minimum distance rather than a computation on the
carrier, and is left to the tree's own deep-hole ladder. Both are named in §9
of the study.

---

## Phase 48 — the handover closed, and the query that had grown too slow to pass

**Status: closed this round.** Like Phase 47 it is **maintenance**, and says
so in those words: under directive **D15** it moved none of derivation,
addressing or refusal. It closed the handover Phase 47 left open and fixed the
one thing that closing it exposed.

**What it picked up.** The tree did not open clean. `corpus --check` named
`DIGEST.md`, the document address book and generated blocks in three studies —
`CORPUS_ADDRESS_STUDY.md`, `ITERATION_COST_STUDY.md`, `ZERO_STORAGE_STUDY.md` —
as stale, and `signoff --verify` held only **21 of 98** test files and 6 of 7
instruments. The cause was the order of the previous round's last two steps:
its prose went into those studies *after* its release, so the generated layer
was never re-rendered and 77 units were stale for documents. Refreshing and
re-running is all that was needed, and it is the reason `ITERATE.md` §4 puts
documents before the refresh and the refresh before the release.

**What that release then exposed.** All 98 test files passed and the
evaluation did not: `report lean` **timed out at the harness's 300-second
ceiling**, one case short at 156 / 157. The query was not wrong, it was slow —
about **203 seconds**, and growing with the corpus, because the separation
study behind it ran two loops over the pairs of 3,383 declarations: 69 seconds
on the all-pairs means and 133 on the nearest-neighbour search, for each of the
three schemes. A ceiling that a measurement is drifting through is not a
ceiling to raise, so the arithmetic was fixed instead.

* **The all-pairs means are a closed form.** For any finite point set,
  `sum_{i<j} |x_i - x_j|^2 = n * sum_i |x_i|^2 - |sum_i x_i|^2` — Lagrange's
  identity, integer throughout. Same-file totals are that identity applied file
  by file and the cross-file total is the difference, so the third table of
  §7 costs one pass over the declarations instead of one over their 5,720,653
  pairs.
* **The nearest-neighbour search is pruned, exactly.** Which declaration is
  nearest has no closed form, so two lower bounds do the work: the addresses
  are held in order of their most spread-out coordinate, and a scan outward
  stops in a direction once the gap in that coordinate alone exceeds the best
  distance found; and the next three most spread-out coordinates bound the full
  distance from below before it is computed. A lower bound can only discard a
  candidate the full distance would have discarded, so the minimum and every
  tie are what brute force reports. Declarations sharing an address are each
  other's nearest neighbours at distance zero, so the search runs over the
  3,002 distinct addresses.

| | before | after |
|---|---|---|
| `report lean`, end to end | 203 s | **77 s** |
| the separation study alone | 201 s | **76 s** |
| nearest shares a file, `feature` / control / shuffle | 672 / 33 / 35 | 672 / 33 / 35 |
| nearest is cited either way | 120 / 6 / 3 | 120 / 6 / 3 |

Every published figure is unchanged, which is what an identity and an exact
bound buy over a tolerance. Six cases in `tests/test_lean_address.py` pin it
against the definition rather than against the previous output:
`nearest_points` against `nearest_points_exhaustive` on corpus addresses under
all three schemes, on a constructed tie, and on repeated points, and the
identity against the pairwise loop.

**Verified here, on the final tree.** A release with the exhaustive cases on
signs **98 of 98 test files and 7 of 7 instruments**, and `--verify-release`
confirms it. The suite sentence moved with the six new cases and is
re-measured at **3,924 tests across 97 of the 98 test files, 15,326
subtests**; one `pytest` process with nothing deselected collects **3,952** —
that total plus the 28 tests of the document check. The evaluation is back at
**157 / 157**, `corpus --check` is **current**, `lake build` is clean with no
`sorry`, and both Lean copies are identical.

**Where it is.** `overlay/glm_universal/reasoning/lean_address.py`
(`_group_squared_distance_sum`, `nearest_points`,
`nearest_points_exhaustive`), the new cases in
`overlay/glm_universal/tests/test_lean_address.py`, and §7 of
[`studies/LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md).

---

## Phase 47 — the round loop, measured again: the selectivity a feature undid, and the check that need not be asked

**Status: closed this round.** It is a **maintenance** round and the record
says so in those words: under directive **D15** it moved none of derivation,
addressing or refusal. What it moved is the cost of a round, which the
previous round had left half-measured when it ran out of time, and it repaired
the tree that round handed over.

**What it found.** The sign-off ledger had stopped being selective, and
nothing had noticed because the thing that undid it was a feature, not a bug.
Phase 46's field surface holds the Lean address book as one of its tables, and
that table loaded its rows by calling `lean_address.declarations()`, which
walks the development and parses every file. The surface is reached from the
session, and the session is imported by nearly every test — so the whole
development re-entered nearly every closure. Measured by
`corpus.cost.lean_blast_radius`, a median Lean edit made **79** of 98 units
stale where §5a of
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) had
measured 26 — which is to say that after one edit to one proof, a round paid
for most of a release. That is the answer to *what was taking so long*.

It was caught because the previous rounds had written the cost property down
as a test rather than as a paragraph: `test_signoff.py` asks that a unit
naming one Lean file carries that file and not the rest, and `test_corpus.py`
asks that the table in §5a is what the code computes. Both were failing in
the handed-over tree.

**What was built.** The same split as Phase 44's rule-and-record, one level
down: reading the development and answering from what was read are two jobs.
`reasoning/lean_address.py` builds the book — walks the tree, parses it,
decodes the addresses, writes it. The new `reasoning/lean_book.py` answers
from the book: one generated file, no source of the development named or
reachable. The book's schema is 2, carrying the namespace and the head of
each statement so the surface answers exactly what it answered before, field
for field. Whether the book still describes the development is a question
that needs the tree, and it stays with `cache_state()` and `corpus --check`.

| | with the surface reading the tree | reading the book |
|---|---|---|
| units one Lean file makes stale, median | 79 | **27** |
| units that take the whole development | 79 | **27** |
| units an edit to *any* Lean file makes stale | 85 | 85 |

Beside it, the **documents gate** stopped answering a question it had already
answered. `corpus --check` renders 97 generated blocks and 201 inline figures;
on picking a round up it was doing that over a tree in which nothing had
moved. `glm_universal/corpus/gate.py` stores the verdict beside a digest of
everything the check can read — the documents, the rendering code, the frozen
data it reads and the Lean sources the blocks quote, taken as the ledger's own
closure of the corpus command — and a check whose inputs have not moved since
it last **passed** reports that instead: about **3 s** against **50 s**. Only
a pass is recorded, so a failure is never skipped, and `--check --all` ignores
the record outright.

**What the round also had to repair.** The tree it picked up had not closed:
four documents carried stale generated blocks, the document address book was
stale with them, and the ledger recorded six test files and the evaluation
instrument as failing. Three of those were the selectivity regression above.
The rest were measurements that had moved and had not been re-taken: the
planner's fallback is consulted on **7** refusals rather than 4, because the
field surface added three of its own — all seven stop, the two the planner
marks are the same two, and the utility gate still fails, so the finding is
unchanged over a larger set; the relay and the anonymous register moved with
the corpus (`362 -> 365 of 423`, the gate on `64 of 1692`, `722 -> 73 of 846`
and `236 -> 161 of 846`), and their evaluation phrases were re-measured; and
the query-escalation measurement cache was re-taken. 296 compiled `.pyc`
files were dropped from the index behind the ignore rule an earlier round had
recorded but never written.

**Verified here, on the final tree.** A release with the exhaustive cases on,
resumed once after the totals moved, signs **98 of 98 test files and 7 of 7
instruments**, and `--verify-release` confirms it. The suite sentence is
re-measured at **3,918 tests across 97 of the 98 test files, 15,324
subtests**, and one `pytest` process over the same tree with nothing
deselected collects **3,946** — that total plus the 28 tests of the document
check it leaves out. The end-to-end evaluation is **157 / 157** (138 answered,
19 refused as expected, 0 confidently wrong, 0 errored), the benchmarks
**2,389 / 2,390**, the probes 33 with 20 holding, `lake build` clean with no
`sorry`, both Lean copies identical, and `corpus --check` **current** with the
document checks holding and every inline figure fresh.

**Where it is.** `overlay/glm_universal/reasoning/lean_book.py`,
`reasoning/lean_address.py` (schema 2), `runtime/fields.py`,
`overlay/glm_universal/corpus/gate.py`, `corpus/__main__.py` (`--check --all`),
the new cases in `tests/test_signoff.py`, `tests/test_corpus.py` and
`tests/test_field_surface.py`, §5e and §5f of
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md), and
[`WHITEBOARD.md`](WHITEBOARD.md) — new this round: the round in progress
written down as it happens, so a session that stops mid-round hands over what
it finished, what it had running, and the command that resumes each thing
left. It is read first (`ENTRY.md` 0a, `ITERATE.md` §0) and folded into this
record when the round closes.

---

## Phase 46 — the field surface: the cheap instrument, bought and priced

**Status: closed (the round before Phase 47).** It took candidate 1 of §3.4 of
[`STATUS.md`](STATUS.md), which is what Phase 45 left, and it is the second
consecutive round to take the sharpest candidate rather than maintenance.
Under directive **D15** it moved **none** of derivation, addressing or
refusal in any sense worth claiming: what it built is `table`, the weakest of
the three faculties, and the record says so in those words. What it bought is
coverage, and what it produced beside the coverage is a measurement of
whether the price the previous round quoted was right.

**What Phase 45 left open.** Its record says the round closed; the tree it
handed over had not. The new test file took the suite to 97 and the documents
still said 96, the suite sentence was four files out of date, `test_figures`
and the figures instrument were failing on it, and the ledger held signatures
for 5 of 97 test files with `test_corpus.py` and the evaluation instrument
recorded as failed. Both of those pass when run, so the failure was the
interrupted round rather than the tree; the counts were re-measured and the
release re-run here rather than re-recorded.

**What was built.** `glm_universal/runtime/fields.py` — a surface of
**13** declared tables holding **8,380** rows and **50,364** addressable
`(row, field)` pairs: the element and molecule source rows (which hold far
more than the 24 coordinates a carrier keeps), one table per register's
carrier attributes, the Lean address book as a table of declarations, the
package's own top-level definitions read by the AST walk it already ships,
and a **declared** registry of zero-argument functions whose returned mapping
is addressable by key. Reached by a new query kind with two shapes:
`field atomic_weight_u of carbon` for the value and `fields of <row>` for the
names a row answers to. The keyword is **start-only** — a new parser notion,
because `field` is also an ordinary noun of the physics register, so
`electric field strength` must not become a field query.

**What it refuses.** An unknown row, refused with the nearest row names; an
unknown field of a known row, refused with the fields that row does answer
to; and a field the register records as *missing* for that row, refused as
missing rather than answered with a blank. All three are evaluation cases and
all three are classified `boundary`. A value the register declares derived
rather than stored — `molar_mass_u` — is answered with the rule that
recomputed it, because a surface that let a derived value pass as a held one
would be claiming more than it does.

**What it was worth, against the price quoted for it.** The previous round's
translation table is **frozen and not edited**; a second table is declared
beside it and both are scored by the same locus and no-smuggling rules. One
shortfall was declared *before* the run: *is energy more abstract than water?*
compares one coordinate across two rows and a field query returns one field of
one row, so the prediction under test was nine rather than ten.

| reading | figure |
|---|---|
| held and unreachable, as the oracle found them | 10 of 20 |
| declared reachable by a field surface, before the run | 9 |
| answered by the field surface, measured | 9 |
| the probe's split, before → after | 6/10/4 → 15/1/4 |

The one that remains is the one that was declared, and it is now candidate 1
of §3.4: a comparison across two rows is composition, blocker 3, not
coverage.

**What is proved rather than measured.** `RequestProject/GLM/FieldSurface.lean`
states the surface as a list of tables of rows of named fields and proves
`lookup_eq_none_iff` (the answerable pairs are exactly the declared ones, so a
refusal is a fact about the tables and not a failed search — the field
surface's counterpart of `GLM.Recipe.Spec.answer_eq_none_iff`), `lookup_sound`
(an answer is some table's own value; nothing is invented),
`lookup_isSome_iff_mem_names` (the listing shape and the lookup shape agree)
and `lookup_cons_of_some` with `lookup_append_of_isSome` (priority is
monotone, so extending the surface cannot change an existing answer).

**Where it is.** `overlay/glm_universal/runtime/fields.py`, the `field` branch
of `runtime/parser.py` with its `START_ONLY` set, `_solve_field` in
`runtime/session.py`, the `field` script template in `runtime/tct_engine.py`,
`glm_universal/reasoning/field_surface.py` (the measurement),
`glm_universal/tests/test_field_surface.py` (35 cases), eight new evaluation
cases, three generated blocks and eleven inline figures in
`glm_universal/corpus/render.py`, `tools fieldsurface`,
[`studies/FIELD_SURFACE_STUDY.md`](studies/FIELD_SURFACE_STUDY.md) and
`RequestProject/GLM/FieldSurface.lean`. Like the oracle it keeps **no
measurement cache**: both translation tables are asked of a live session in
seconds.

---

## Phase 45 — what a refusal is evidence of: blocker 1's own experiment, run

**Status: closed (the round before Phase 46).** It took candidate 1 of §3.4 of
[`STATUS.md`](STATUS.md) — the sharpest one, and the first candidate a round
has taken since Phase 41. Under directive **D15** it moved **none** of
derivation, addressing or refusal: what it produced is a measurement that
prices two instruments and recommends neither by itself, and the record says
so in those words.

**What Phase 44 left open.** Its record says the round closed on a complete
release run with the compiled files untracked. Neither was true of the tree it
handed over: 291 `.pyc` files were still in the index, `.gitignore` carried no
rule for them, the planner's derived reading and the query-escalation
measurement were both stale — so `corpus --check` refused to run and the
escalation study rendered two "measurement stale" placeholders instead of its
tables — and the sign-off ledger held signatures for 5 of 96 test files, with
the figures instrument and `test_figures.py` failing on a suite sentence four
test files out of date. All of it is fixed rather than re-recorded: the caches
were re-taken in the order that converges, the suite sentence re-measured, the
compiled files removed from the index behind an ignore rule, and this round
closed on a release run that was taken rather than intended.

**The experiment.** `BLOCKERS_STUDY.md` §1 declares the smallest experiment
that would price blocker 1 — *hand-write the query each of the twenty probe
questions should become, and measure how many the existing solvers then
answer* — and it had stood undone through four rounds. It is run in
`glm_universal/reasoning/probe_oracle.py`: twenty declared translations, no
new code, no solver touched.

Each question ends in one of three classes, computed from two facts rather
than judged: **`parsed`** (a query in the existing grammar answers it, with
the declared fragment in the declared field), **`surface`** (no query answers
it and a shipped register row, function or source holds the answer) and
**`absent`** (nothing holds it, and the refusal is right).

| reading | figure |
|---|---|
| answered as asked, in English | 2 of 20 |
| answered by a hand-written query | 6 of 20 |
| held by a register or a shipped function, reachable by no query | 10 of 20 |
| held nowhere, where refusing is correct | 4 of 20 |

So the seventeen refusals of the language probe were reading as one failure
and are three. **The parser is worth 4 questions**; a *field surface* — one
query kind returning a named field of a named register row — is worth **10**,
and is by far the cheaper instrument. That recommendation is about coverage
and not about reasoning, and the study says so: a field surface is `table`,
the weakest of the three faculties, and the questions that would need
derivation are among the four absent ones.

**Two rules that make the measurement worth more than the probe's own.** The
**locus**: for every translation the field that must carry the fragment is
declared beside the query, so `approximate 12/18 to 4 places` cannot score
`6` against `0.6667` — the probe's rule would have accepted it. The
**no-smuggling rule**: a translation may not contain the fragment it is scored
on unless the question already contains it, so `relate velocity position` is
not a translation of *what is velocity the derivative of?*. Both are enforced
by tests rather than by intention.

**What is proved rather than measured.** `RequestProject/GLM/ProbeOracle.lean`
carries the classification and what the study's arithmetic depends on:
`classify_exhaustive` and `classify_exclusive` (every question gets one class
and no question gets two), `counts_partition` (the three counts sum to the
sample, so the headline reads the same twenty questions three ways),
`not_parsed_of_not_answered` and `witness_irrelevant_when_answered` (a witness
can only ever move a question into `surface`, so the experiment cannot flatter
the grammar).

**Where it is.** `overlay/glm_universal/reasoning/probe_oracle.py`,
`glm_universal/tests/test_probe_oracle.py` (18 cases),
`glm_universal/corpus/render.py` (two generated blocks and six inline
figures), `glm_universal/tools.py` (`tools oracle`),
[`studies/PROBE_ORACLE_STUDY.md`](studies/PROBE_ORACLE_STUDY.md),
`RequestProject/GLM/ProbeOracle.lean`. The experiment keeps **no measurement
cache**: it asks a live session twenty times in a few seconds, so the
documents quote what the solvers do now and the documents gate pays nothing to
keep them honest.

---

## Phase 44 — the rule split from the record, and the gate made legible

**Status: closed this round.** Like Phases 42 and 43 it took no candidate from
§3.4 of [`STATUS.md`](STATUS.md) and moved none of derivation, addressing or
refusal (directive **D15**): it is maintenance of the loop the rounds run in,
and it finished what Phase 43 had left open.

**What Phase 43 left open.** Its release run never completed, so the tree was
handed over with the suite totals measured over 92 test files when there were
96, two document checks failing on their own figures, and 73 units carrying no
signature. The `.pyc` files it recorded as untracked were still tracked — 289
of them — and `.gitignore` had no rule that would have kept them out. Both are
now true rather than recorded as true: `__pycache__/`, `*.pyc` and `*.pyo` are
ignored, the files are out of the index, and the round closed on a complete
release run rather than on an intention to take one.

**The rule and the record.** Every unit's closure has to contain the files
that define what a dependency *is* — if the rule changes, no old signature is
trustworthy — and the whole of `signoff/ledger.py` was one of them. That file
held two unlike things: the rule (what a closure is, what a digest covers, how
a unit is run) and the record (the plan, the stored signatures, the parallel
runner, the suite totals, the reporting). Only the first can change what a
test observes; the second is what a round actually edits. The rule is now
`signoff/rules.py` and is scaffolding; the record stays in `signoff/ledger.py`
and is in no closure but those of the six units that import it, and re-exports
the rule's names so nothing that called `ledger.unit_closure` had to change.

| an edit to | units it makes stale | their last recorded time |
|---|---|---|
| `signoff/rules.py` (the rule) | 96 of 96 | 3,970 s |
| `signoff/ledger.py` (the record) | 6 of 96 | 797 s |
| `signoff/checks.py` (the instrument table) | 2 of 96 | 375 s |
| `signoff/__main__.py` (the command line) | 1 of 96 | 54 s |

**Two questions the gate could not answer, and now does.** A digest says that
something moved and nothing else. `signoff --why` splits a closure into five
disjoint groups whose union is exactly the closure — scaffolding, data,
documents, Lean, code — records a digest per group beside the signature (five
hex strings, deciding nothing) and names the groups that moved, so
`changed: documents` is read as a prose edit and `changed: code` is not.
`signoff --impact PATH` inverts the closure relation and prices an edit
*before* it is made: 93 of 96 units reach `PROJECT_DIRECTIVES.md`, which is
the measured form of the standing advice to batch directive edits into one
pass. Both are tested in `tests/test_signoff.py` — the groups partition the
closure, each group holds only its own kind of file, the reason is honest
about a signature that predates it, and the inversion agrees with the plan.

**The caches nothing was watching.** Ten study modules keep a measurement
cache keyed on the digest of their sources, and nothing enumerated them: a
stale one was found by whatever happened to read it, which this round was the
end-to-end evaluation twenty minutes into a release run.
`glm_universal.corpus.caches` is the census — a module is in it when its
source defines both `module_digest` and `current`, and the command that
re-takes it is read out of `tools.py` rather than listed — and
`corpus --check` runs it and names each stale cache with its command, without
ever paying for one. §5d of the cost study is the measurement.

**A count that two documents disagreed about.** `ENTRY.md` said "the sixteen
rules" and `ITERATE.md` said "the fourteen rules"; both were hand-written and
one was wrong. The count is now a generated figure (`directives`, over
`glm_universal.reasoning.directives.directives_report`) with a sentence
pattern, so any document stating a number of standing rules is checked against
the document that states them — directive **D6** applied to the rules
themselves.

**Where it is.** `overlay/glm_universal/signoff/rules.py` (the rule),
`signoff/ledger.py` (`stale_groups`, `reason`, `impact`),
`signoff/__main__.py` (`--why`, `--impact`),
`glm_universal/figures.py` and `corpus/render.py` (the directive figure),
`glm_universal/corpus/caches.py` (the cache census, wired into
`corpus/__main__.py`),
`glm_universal/tests/test_signoff.py` and `tests/test_corpus.py` (fourteen new
cases),
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5c (the
measurement).

---

## Phase 43 — the gates made fast, and the status document cut back to the present tense

**Status: closed.** It took no candidate from §3.4 of
[`STATUS.md`](STATUS.md), and says so: under directive **D15** it moved none of
derivation, addressing or refusal. Like Phase 42 it was maintenance — of the
loop the rounds run in — and it finished three things Phase 42 had left
unfinished.

**The documents gate never pays for a derivation again.** Five generated blocks
quote the sandbox planner's report, and that report is kept beside the digest
of the code it was derived from. When the code moves, the digest moves, and
`corpus --check` was *recomputing* the report inside the check: a documents
check that should cost half a minute cost a quarter of an hour, and it was
doing so on the tree as delivered. `glm_universal.derived` now has a
`no_recompute` guard and a registry of stores; `corpus --check` runs inside the
guard, so a stale derivation is **named**, together with the command that
rebuilds it, rather than silently paid for. Measured on this tree:
**26 seconds** against **more than twenty minutes**. The cost is paid once, by
`corpus --refresh`, which is where it belongs.

**The quantiser decodes on scaled integers.** `reasoning/llvq_table.py` did
every cost comparison in `Fraction`. Multiplying through by the square of a
common denominator of the target's coordinates turns each cost into an `int`
and changes no comparison and no tie, so the decoded point is the point the
rational route returns — which is checked rather than asserted: the scaled
rounding and the scaled column costs are put beside the rational ones in
`tests/test_llvq_table.py`, and the whole agreement sweep against
`analogy.nearest_lattice_point` still finds no mismatch. Measured on 200
targets after warm-up: **1.15 ms** a call against **10.55 ms**, about nine
times faster, on the hot path of every address the system takes.

**The planner's fallback reading runs on every core.** It asks the live runtime
each of the 149 declared evaluation cases, which is the expensive half of the
report and, at **955 s**, most of a refresh. The cases are independent, so
`fallback_row` now takes a case by index and `fallback_rows` maps it over a
process pool — every core by default, one when `GLM_PLANNER_JOBS=1`, the rows
in declared order either way, and the two readings required to agree row for
row by a test.

**The compiled files are untracked, for real this time.** Phase 42 recorded
that 382 `.pyc` files were being tracked as source and are "ignored now". They
were still in the index: 289 of them. They are removed from it, and
`__pycache__/` and `*.pyc` are in `.gitignore`.

**The status document, cut back to the present tense.** [`STATUS.md`](STATUS.md)
had grown back to 959 lines, most of it the round-by-round narrative that Phase
42 had moved here once already — "the round before that…", each retelling a
phase this document already records. It is **487** lines now: the instrument
table, the standing description of what the system is made of, the open list
with the candidates ordered sharpest first, and how to re-verify. Nothing was
lost: every narrative paragraph removed restates a phase recorded in *The
delivered record* below.

**The rest of the tidy-up.** The positioning note is stated once, in
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md), and the paraphrase of it that
had survived in the number-theory paper now points there;
`glm_vision_experiments_v14.py` is filed under `source_material/`; the
directives document keeps the rules and the round protocol, with the long-form
rationale of each rule moved to
[`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md);
and [`overlay/README.md`](overlay/README.md) is brought up to date with all of
it.

---

## Phase 42 — the round loop made cheap, and the record split from the state

**Status: closed this round.** It took no candidate from §3.4 of
[`STATUS.md`](STATUS.md), and says so: under directive **D15**, which this
round added, it moved none of derivation, addressing or refusal. It was
maintenance — of the machinery that was costing every round its last hour.

**The sign-off ledger made selective.** The ledger computes, for each test
unit, a digest of everything its result depended on, so that nothing unchanged
is run twice. One line stopped it working: a module whose string constants
named **any** `.lean` file pulled the **whole** development into its closure,
and since the constants that fire are mostly prose — a docstring in
`reasoning/wobble.py` mentions `Sturmian.lean`, and most of the package
reaches `wobble.py` — one Lean edit made **83 of 96** units stale. A named
file is now resolved to itself in both copies; a `*.lean` glob, which is what
a module that *walks* the tree writes, still takes everything; and a token
written as a path resolves as a path rather than by base name, which matters
for the fifteen `README.md`. Measured by
`glm_universal.corpus.cost.lean_blast_radius`: a median Lean file makes **25**
units stale, the worst **79**, and a typical unit's closure is **116** files
rather than 332. Both halves are tested, and the safe half — an unresolvable
name still takes the whole development — is tested too.
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5a.

**An operating manual.** [`ITERATE.md`](ITERATE.md): the four reads that
orient a session, the three gates — documents, changed units, release — and
which to run when, the edits that invalidate widely and how to pay for them
once, where each kind of finding is written down, the standing target, and a
table of what to run when a check fails. [`ENTRY.md`](ENTRY.md) names it
first.

**Two directives, sixteen in all.** **D15** requires a round to name which of
derivation, addressing and refusal it moved, or to say it moved none. **D16**
requires the cheapest gate that could fail, and treats a closure that is too
coarse as a defect rather than a cost. `report directives` reports **16 of
16** with every named instrument present.

**The record split from the state.** [`STATUS.md`](STATUS.md) had reached
2,579 lines, most of it the stack of past rounds. The history moved here,
under *The delivered record*, inside a `figures:history` region so its figures
are frozen rather than rewritten; the status document keeps the current state
and the round just closed.

**Drift found by running it rather than reporting it.** The relay's gate band
had moved with the corpus and the test still asserted the older reading: it is
strict on the four thresholds **1/20** through **1/5** and at **1/4** sits one
query *below* the text control. The blockers tier-0 verdict named a result its
body never stated. The number-theory paper quoted 116 Lean files against 117.
And 382 compiled `.pyc` files were tracked as source; they are ignored now.

---

## Phase 41 — a second reading before answering

**Status: closed the round before.** It took the first of the three candidates Phase
40 left — *the program-text operation answers wrongly rather than refusing* —
and took it in the form §3.4 of [`STATUS.md`](STATUS.md) stated: require
agreement with a second reading before answering, and measure what that costs
in refusals. It took none of Phase 38's items, which stand below exactly as
they were.

What it did, in order.

**The study was pre-registered and committed before the code that measures
it.** [`studies/SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md)
declares two second readings, two guard strengths, two controls and four pass
marks, and says what was known beforehand: the *shape* of each reading was
scouted so that neither was degenerate, and nothing about any guard's score
was. All six declared configurations are reported, passing or failing.

**Two second readings, both at a different layer from the ladder's
quantisation.** `code` binarises a carrier against the exact per-coordinate
lower median and decodes the 24-bit word by complete Golay syndrome decoding,
refusing when the decoding is ambiguous — the substrate read one layer down,
at the `[24, 12, 8]` code. `margin` takes the exact `ℓ¹` distance to every
carrier and answers only when every carrier within twice the nearest distance
carries one label — no quantisation and no code.

**Two guards, and the answer the round came for.** `strict` answers only when
both readings answer and agree; `veto` answers unless the second reading
contradicts. Of the six configurations exactly **one** is adopted:
`strict+margin` takes the program-text operation from **503 correct, 13 wrong**
to **366 correct, 0 wrong**, damages no other operation by as much as a
quarter, and gives up **150** answers to remove all thirteen wrong ones where
refusing 150 answers chosen by a digest removes **2**. Every `veto`
configuration fails the safety mark — a veto only fires when the second reading
answers *and* disagrees, and there it is usually refusing — and the two
configurations built on the code layer are safe and useless, answering 21 and
19 of 576 and taking two other operations to zero.

**What is proved rather than measured.**
`RequestProject/GLM/SecondReading.lean`, 0 `sorry`: `strictGuard_eq_some` and
`vetoGuard_eq_some` characterise both guards; `strictGuard_sound` and
`vetoGuard_sound` say a guard invents nothing; `strictGuard_wrong_imp` and
`strict_blocks_unless_second_repeats` say a wrong answer now needs both
readings to agree on it; `strictGuard_safe_of_sound` and
`vetoGuard_safe_of_sound` turn that round, with the extra hypothesis the weaker
contract costs; and `strict_correctCount_le`, `veto_correctCount_le`,
`strict_wrongCount_le`, `veto_wrongCount_le` and `strict_correctCount_le_veto`
carry both directions to counts, so that guarding provably moves both columns
of the score sheet downwards and safety has to be paid for.

Write-up, with what it leaves for the next round:
[`studies/SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md).

---

## Phase 40 — the norm family, the operations that are not retrieval, and the blockers

**Status: closed (the round before Phase 41).** It took item 2 of Phase 39's write-up —
*generate the rungs between the rungs* — and pushed it past the point where a
handful of named constructions can carry it, then applied the same discipline
to operations the ladder had never touched. It took none of Phase 38's items,
which stand below exactly as they were.

What it did, in order.

**The prior measurements re-derived rather than trusted.** The eleven-rung
result, the length sweep and the point at which the reading first goes wrong
were all recomputed before anything was built on them, and all three came back
identical to the recorded values: **462** correct, **0** wrong, 106 refused;
the sweep 327 / 432 / 439 / 462 / 475 / 476; safe to thirteen rungs and first
broken at fifteen.

**The ladder re-indexed by minimum squared norm, and the family completed.**
`substrate/norm_family.py` generates
**<!--figure:normfamily-rung-count-->25<!--/figure-->** rungs over
**<!--figure:normfamily-norms-->12<!--/figure-->** minimum squared norms — every
power of two from 1 upward, with no gap. The gap is the point: doubling a
lattice multiplies squared norms by **four**, so the scalings alone reach only
every other power of two, and the Z/D/A-type rungs have to be interleaved with
them to fill the rest. Every rung's membership test, theta series, covolume,
kissing number and place in the containment order is generated from its key
rather than stored, and containment is checked across the whole family on
generated points of the lower rung.

**The containments proved.** `RequestProject/GLM/NormFamily.lean`, 0 `sorry`:
`scaled_normSq` and `scaled_min_norm` — scaling a lattice by `k` multiplies
every squared norm, and therefore the minimum, by `k²`; the three step
containments `dbl_isD_isG`, `dbl_isA_isB` and `dbl_isC_isA`; and
`norm_family_chain` with `family_tower`, which chain them into the tower the
family's order needs.

**The escalation re-taken, and the family found unsafe.** Same query set, same
controls. The full **<!--figure:normesc-family-rungs-->12<!--/figure-->**-rung
norm ladder names **<!--figure:normesc-family-correct-->470<!--/figure-->**
correctly and answers **<!--figure:normesc-family-wrong-->1<!--/figure-->**
*wrongly* — a loss of the one property that matters, reported as a failure.
Two declared retirement clauses and a bounded repair retire the offending rung
and a rung that buys only duplication, and the repaired
**<!--figure:normesc-rungs-->10<!--/figure-->**-rung ladder names
**<!--figure:normesc-correct-->467<!--/figure-->** of
**<!--figure:normesc-queries-->568<!--/figure-->** with
**<!--figure:normesc-wrong-->0<!--/figure-->** wrong, matching the oracle with
no rung disagreeing. The length sweep puts the break at
**<!--figure:normesc-first-broken-->9<!--/figure-->** rungs and safety through
**<!--figure:normesc-longest-safe-->8<!--/figure-->**. Order-independence holds
everywhere in the family, so the new breaking point is safety rather than
order-dependence — a different failure from the one the named ladder had.

**Escalation applied to operations that are not retrieval.**
`reasoning/operation_escalation.py` measures
**<!--figure:opesc-count-->7<!--/figure-->** of them — the register, dimension,
chemistry, physics, harmony and program-text classifications and the equation
check — each with a stated refusal contract and each against a control with the
substrate removed and against a label prior. Every one gains; the program-text
operation is **unsafe**, answering
**<!--figure:opesc-program-wrong-->13<!--/figure-->** of
**<!--figure:opesc-program-queries-->576<!--/figure-->** wrongly.

**The blockers, with a pre-registered probe.** `reasoning/blockers.py` declares
**<!--figure:probe-questions-->20<!--/figure-->** questions, their scoring and
a pass mark of **<!--figure:probe-pass-mark-->10<!--/figure-->** correct before
running them. The probe scores **<!--figure:probe-correct-->2<!--/figure-->**
correct, **<!--figure:probe-wrong-->1<!--/figure-->** wrong,
**<!--figure:probe-refused-->17<!--/figure-->** refused — **a failure against
its own declared mark**. Each blocker carries the measurement that demonstrates
it and the smallest experiment that would remove it, and the faculty ledger
separates table lookup from lookup with geometric addressing from derivation
the system performs itself, with only
**<!--figure:probe-derived-->2<!--/figure-->** results in the last column.

Write-ups: [`studies/NORM_FAMILY_STUDY.md`](studies/NORM_FAMILY_STUDY.md),
[`studies/OPERATION_ESCALATION_STUDY.md`](studies/OPERATION_ESCALATION_STUDY.md),
[`studies/BLOCKERS_STUDY.md`](studies/BLOCKERS_STUDY.md).

---

## Phase 39 — the construction ladder, generated and walked out from the middle

**Status: closed (the round before Phase 40).** It took none of Phase 38's
items, which stand
below exactly as they were: the round came from a new piece of supplied
material, `source_material/Golay codes and Hadamard matrices.txt`, and the
question it asks — *is a system that reads the substrate at one fixed rung a
partial system?* — is not on that list.

What it did, in order.

**The note, recomputed rather than believed.** Nineteen checkable claims:
**12 confirmed, 7 corrected, 0 refuted**, each with the function that
recomputed it (`substrate/golay_paley.py`,
`substrate/construction_ladder.py`). The most useful is not a correction: the
note's 12 × 12 Paley block generates **exactly** the 4,096 codewords this
system already runs on, in the same coordinate labelling, so everything the
note says about it is a statement about this substrate. The corrections are
listed in the study; the sharpest are that `Q − I` is not a Hadamard matrix
(`Q` is), that the ternary enumerator has **24** words of weight 12 and none of
weight 11, that the printed `6 × 5` ternary block has a repeated row and
generates a minimum weight of **2** rather than the perfect `[11, 6, 5]` code,
and that the quoted Leech theta identity is not a theta series at all — the one
that gives its own coefficients is `E₄³ − 720Δ`.

**The two missing rungs, built.** `Z²⁴` and `D₂₄` sat below the Construction
A/B/C ladder this package already had, and were never written down. All five
rungs are now generated from their conditions, with each one's minimum norm and
kissing number **checked against its own generated theta series** rather than
quoted: `Z` (1, 48), `D` (2, 1,104), `A` (16, 48), `C` (32, 196,560), `B`
(32, 98,256).

**The ladder is a diamond.** `A` and `C` are incomparable — `4·e₀` is in `A`
and not in `C`, `(−3, 1²³)` is in `C` and not in `A` — so there are two routes
up and a reading that climbs one has not seen the other
(`GLM.ConstructionLadder.ladder_not_chain`). That is the structural reason the
escalation starts in the middle.

**The escalation, measured against every partial system.** 142 carriers, four
declared perturbations, 568 queries, one stopping rule available to a reader
that does not know the answer. On the note's five rungs the escalated reading
names **327** correctly with **0** wrong against **205** for the best single
rung, and the oracle over those five rungs reaches 327 too, so the stopping
rule loses nothing.

**The ladder was too short, and the rungs that fill it are generated.**
Construction `A` over the trivial code is `2ℤ²⁴` and over the even-weight code
is `D₂₄`, and in this package's scaling `A` is itself `2G` with `G` the
unscaled Golay lift — so `L ↦ 2L` generates the rungs the note's list was
missing. The ladder is now **eleven** rungs
(`2A, 4D, 4Z, B, C, A, 2D, 2Z, A/2, D, Z`), the widest step between
neighbouring minimum norms falls from eight to two, and its arithmetic middle
is still `A`. Re-measured over the same sweep: **462** correct, **0** wrong,
106 refused — against 327 before and **283** for the best single rung, with the
oracle again matching at 462 and no two rungs ever naming different carriers.
The sweep over ladder lengths (5, 7, 9, 11, 13, 15) records 327, 432, 439, 462,
475 and then the break: at fifteen rungs two rungs disagree, one wrong answer
appears under one order and not the others, and the hypothesis of
`firstNamed_order_independent` fails — a measured boundary rather than an
assumed one. Thickening also moved the cheapest order: middle-out was cheapest
of the three on five rungs and is now the dearest (**7,678,479** against
**5,809,935** for coarse-to-fine), which the order-independence theorem makes a
cost decision and not an accuracy one.

**What is proved rather than measured.**
`RequestProject/GLM/ConstructionLadder.lean`, 0 `sorry`: the containments; the
diamond; that a walk out from the middle of a ladder of `2k+1` rungs is a
permutation of it (`middleOut_perm_range`), so the movement misses nothing;
that the answer does not depend on the order when the naming rungs agree
(`firstNamed_order_independent`), which is what licenses choosing an order for
cost; and the cost of starting in the right place
(`visitCount_eq_one_of_head_named`).
`RequestProject/GLM/ScaledLadder.lean`, 0 `sorry`, adds the thickening:
`isA_iff_dbl_isG` (`A = 2G`), `isA_dbl_isD` (**Construction `A` sits inside the
doubled checkerboard lattice**, which is the Golay code's doubly-even weight),
`isG_isD`, `dbl_isZ_isG`, `isC_isG`, `scaled_two_isZ_isA`,
`scaled_two_isD_isB`, and `gap_chain` — the filled step as one theorem,
`A ⊆ 2D₂₄ ⊆ 2ℤ²⁴ ⊆ G ⊆ D₂₄ ⊆ ℤ²⁴`.

Write-up, with what the next round should take:
[`studies/CONSTRUCTION_LADDER_STUDY.md`](studies/CONSTRUCTION_LADDER_STUDY.md).

---

## Phase 38 — what Phase 37 left behind

**Status: proposed. This is where the next round starts.**

It is §3.4 of [`STATUS.md`](STATUS.md), which points back here. Phase 36 took
the standing negative result of the retrieval round — retrieval by lattice
address beats chance and loses to plain text overlap — and answered it as an
architecture question rather than a geometry one: the faculties were made into
a stack, and the geometry was given only the queries the leading faculty cannot
read. Phase 37 then asked whether what the stack carries is a residue or a
class, and closed that question with the anonymous register. Both are closed.
Seven candidates stand — the four the deep-hole rounds left, the one the stack
round added, the two the anonymous round added in place of the one it closed,
and the one Phase 41 added when it closed the program-text failure:

1. **The separation criterion, still unmet globally.** `nearest_correct` says a
   reading names holes correctly whenever `ρ = 2W/B < 1`. Phase 35 located the
   obstruction exactly — the stalling spread is `D_6^4`'s, and the four
   remaining failures belong to that same type — and showed that deleting
   references cannot earn the criterion (`resolves_of_subset`,
   `separation_mono`), so a deletion sweep is a floor and not a route. What is
   left is the honest pair of alternatives: find a reading whose `ρ < 1` over
   the whole ten-type set, or prove a bound saying no reading of this family
   reaches it. `per_type_correct` already certifies 3 of the 10 types, which is
   the shape a partial answer would take.
2. **The faithfulness radius.** `per_type_absent` states the absence the
   deep-hole rounds have been short of, and needs `∀ y of the type,
   dist y p ≤ w`. The measured radius and the certified radius are currently
   incompatible on this data (`r ≥ 0.0659` against `r < 0.0179`), so the
   theorem is instantiated nowhere. Either an ensemble is found whose within-
   type spread meets the bound, or the incompatibility is proved rather than
   observed.
3. **The thirteen unreached types.** Unchanged: the ensemble reaches 10 of the
   23 Niemeier root systems from the 14 declared centres, and reaching the rest
   means new centres and therefore a new pre-registration.
4. **A register that arrives anonymous on its own.** Phase 37 closed the
   question this item used to ask — the carry set is a class, not a residue —
   by renaming every identifier outside a declared vocabulary and measuring
   retrieval over the result. Renaming is a faithful model of a
   cross-vocabulary goal, and it is still a model. The measurement to want is
   the same table over goals that arrive anonymous without being made so:
   statements from a second Lean development, or from a generator, scored
   against the same controls. The gate is also still a stated constant: the
   sweep shows the gain strict on four consecutive thresholds, 1/20 through
   1/5, and level with the control at 1/4, which is robustness over a band
   rather than calibration at a point.
4a. **The leak the audit found in the feature map.** The shipped structural map
   counts the type vocabulary wherever those words occur, including inside an
   identifier, so a renaming moves a coordinate on 30 of 826 queries. The
   reading that is supposed to be name-blind is therefore not quite name-blind,
   and the extent of it is measured rather than assumed. Either the map is
   narrowed to count a type word only where it is a type, or the leak is
   priced — and either way it is a measurement with its own control, not a
   patch.
5. **What the second-reading guard costs, and why the metric reading is
   safe.** Added by Phase 41. The adopted guard refuses 137 queries the
   program-text operation used to answer correctly, and the room to get them
   back is in the *reading* rather than the contract, because the weaker
   contract is already measured and never reaches safety. Beside it stands an
   unexplained fact: the metric reading answers nothing wrongly on any of the
   six operations while losing to the primary on four, so a safe weak reading
   sits next to a strong unsafe one. What the margin is doing on exactly the
   queries the ladder gets wrong, and whether a margin other than twice the
   nearest distance trades the two off better, is the measurement to want.
6. **The planner's utility gate.** The reverse-call planner satisfies every
   safety line and fails the one that matters: it adds nothing to the shipped
   system, because the refusals it is offered are refusals it agrees with. The
   question that would close it is whether a *tool* exists that the planner
   could reach and the dispatcher cannot — which is a question about the tool
   registry, not about the planner — and until one does, D14 keeps it where it
   is.

Whichever is taken, the discipline is that of Phases 20–24 and 31–35: the thing
must be *described* or *measured* rather than asserted, the study must be
committed before the code that measures it, what does not generalise must be
counted rather than hidden, the old path must be frozen so the new one has
something to agree with, and the end-to-end evaluation must return the same
answers and the same refusals.

---

<!-- figures:history -->

*The closed phases that used to follow live in
[`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md), unchanged.  The counts in
them were true when each phase was closed and are deliberately left alone; for
the project as it is now, see [`overlay/FIGURES.md`](overlay/FIGURES.md), which
is regenerated from the code.*

---

## The delivered record — what each round built

*The historical record, moved here from `STATUS.md` so that the status
document stays short enough to read at the start of every round. `STATUS.md`
now carries the current state and the round just closed; everything older is
here. Nothing was dropped in the move. The figures below are the ones each
round measured, and the whole section is marked as a record, so they are not
rewritten when the system moves on — a section reference inside it ("§2",
"§3.4") is to the status document as it stood when the entry was written.*

<!-- figures:history -->

### What earlier rounds delivered

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

**The faculties made into a stack: the geometry given the queries the text
layer cannot read.** The result above was measured with each faculty answering
alone. `reasoning/stack.py` asks what the machine does when they answer
together: each faculty reports how much evidence it has for *this* query, and
below a stated gate of **1/10** the leading lexical search is judged to have
abstained, so the two geometric address books answer in its place by a stated
quota and interleave. At `k = 5` the stack is ahead of the text control on the
tuning stride (**358 → 360** of 413), on a disjoint held-out stride (**352 →
359** of 413) and on bare goal queries (**710 → 713** of 826), and it is never
below it at any window of the ladder. The gate fires on **62** of 1,652
queries; the geometry carries **13** queries the text control misses against
**1** lost, where the same relay to the digest addresses and a seeded
permutation carries **2** and a relay to the name search carries **none**. The
gain is strict on four consecutive thresholds, **1/20 through 1/5**, and level
with the control at **1/4**, never below it across that band. What is a theorem
rather than a hit rate is in `RequestProject/GLM/Relay.lean`:
`relay_confident` — above the gate the relay *is* the leader's ranking, so the
stack cannot cost anything where the leader is strong — and `relay_carry`,
which says whatever a faculty holds inside its quota survives into the
answer's window, so a faculty that has the answer cannot be drowned out by the
ones that do not. `vision_stack.py` runs the identical relay in a register
with no text in it — 50 ARC training puzzles under `overlay/arc_agi_17` — where
an eight-dimension visual look removes **95.3 %** of 1,089 proposals before the
expensive check sees them and the relay solves a puzzle its leading faculty
does not. `report relay`. Write-up:
[`STACK_RELAY_STUDY.md`](studies/STACK_RELAY_STUDY.md).

**The register where the address is the only reader.** The relay above wins on
a residue: 13 queries in 1,652, mostly constants and calibration lemmas.
`reasoning/anonymous.py` asks whether a register exists in which the structural
address is not a second opinion but the *only* faculty that can read the query,
and finds one. A query is **anonymous** when its identifiers are not the
corpus's — a goal from a second formalisation, a generated goal with no names
yet, an autoformalised statement in its source's vocabulary — and the
reproducible form of it is renaming every identifier outside a declared
vocabulary of 39 words to a positional placeholder, with the placeholders
checked fresh against the corpus rather than assumed. Over the same **826**
queries at `k = 5` the text search falls **710 → 67** and the identifier
address book **395 → 44** — both to within a hair of the **48** hits
chance gives — while the
structural address holds **236 → 164** and leads every other faculty in the
register by more than a factor of two. The identifier address book is the
control that matters: it is geometric too, so what survives is the *structural*
reading rather than geometry in general. `RequestProject/GLM/Anonymous.lean`
says why: `features_anonymise` — any reading that is a function of the kept
skeleton is unchanged by a renaming; `overlap_anonymise_eq_zero` — a fresh
renaming leaves the text faculty's overlap at zero, so it has no evidence by
construction; `relay_hands_over` — with confidence zero the relay of
`Relay.lean` *is* the interleave, so the stack's existing gate reads the
register with the geometry without being re-tuned, and it does: it fires on
**551** of the 826 against **31** of the same queries read plainly, and lifts
the leader **67 → 111**. Checked against the shipped feature map rather than
the idealisation, **796** of 826 queries keep every syntax coordinate and the
**30** that do not move only the six that count type words — an audit finding
of the round, since the shipped map counts those words inside identifiers too.
`report anonymous`. Write-up:
[`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md).

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

**And the ledger read from both ends.** §8 of that study is the note the
saving needs: generating rather than storing buys a smaller data footprint and
no index to consult, and what pays for it is work at each use — so a fair
comparison charges the table for more than its bytes. The bill it lists is the
table's: the bytes in the tree and in every clone, release and backup; the
loading and indexing before the first answer; the digest a derived table has
to be kept beside and the check, every round, that it still holds; the rebuild
when its inputs move; the reader code the generator would not have needed; and
the risk of believing a stale table. Both sides are already measured in
integers here — the storage side in §1 of the same study, the keeping side in
[`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) — and the rule
that follows is stated plainly: cache a derived object when the generator's
cost per use, times the uses between two invalidations, exceeds the cost of
holding the table *and* keeping it honest, and generate otherwise. The Golay
code is the first case and the Lean address book the second, which is why one
is regenerated from twelve rows and the other is stored beside its digest.

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
decodes 8,157 vectors
and rebuilding them against the stored books decodes
5. A book refuses to seed from
one written at a different schema, scale or cap, it reports how many entries
were seeded, reused and freshly decoded, and the reuse is audited rather than
assumed — each rebuild re-decodes a sample of what it reused and reports any
that moved. **The planner's report is taken once.** Five generated blocks quote
the reverse-call planner's report, and the document check used to re-take it
for each of them, 5 passes
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


### The round-by-round ledger

**Closed this round.** *The storage ledger read from both ends, and the round
before it reconciled.* No new mechanism was added: the work was the note the
generate-rather-than-store idea needed, and the verification chain the previous
round left part-run.

* **the two-sided ledger,** in
  [`ZERO_STORAGE_STUDY.md`](studies/ZERO_STORAGE_STUDY.md) §8, cross-referenced
  from [`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §6 and
  summarised in §2 above. Generating instead of storing buys a smaller data
  footprint and no index to consult, and the price is work at each use — so
  the comparison has to charge the table for more than its bytes: the copies in
  every clone, release and backup; the loading and indexing; the digest a
  derived table is kept beside and the round-by-round check that it holds; the
  rebuild when its inputs move; the reader code the generator does not need;
  and the risk of believing a stale table. Both sides of that ledger were
  already measured in integers here, and the rule that follows is now written
  down rather than assumed;
* **the repository's own storage split is emitted, not typed.** Four inline
  figures — `repo-stored-bytes`, `repo-cache-bytes`, `repo-primary-bytes`,
  `repo-cache-share` — put the overlay's on-disk bytes and the share of them
  that is cache into the sentence that quotes them, which is what caught the
  figure that paragraph had been carrying since the tree was smaller;
* **the anonymous register's deciding figure now says what the study measures.**
  The document check was failing on exactly two tier-0 rules for it — the
  verdict grounded in the body, and every number of the deciding figure written
  somewhere below it — because the headline still quoted a superseded
  measurement. It quotes **710 → 84**, **388 → 48** and **232 → 171** now, the
  same numbers the generated tables carry, and the body states them in prose;
* **four documents brought to the current run.** The plan's phase-37 row
  (**813** queries, not 807), the repository readme's gate count (**538**), the
  invariance figures (**780** of 813 keep every syntax coordinate, **33** move
  a type-word coordinate) in the status document and the study, and the header
  prose of `RequestProject/GLM/Anonymous.lean` itself. The declaration count
  four documents quote moved **3187 → 3249** and the Lean file count in the
  Lean readme and the number-theory evidence paper **112 → 113**;
* **the chain re-run in order,** as §4.2 states it: the Lean mirror
  regenerated, `lake build` clean over
  **117 Lean files** with **0 `sorry`**,
  the escalation measurement cache re-taken after the last file was touched,
  the corpus refreshed until `--refresh` reports **current** with the document
  checks holding, and the figures regenerated;
* **and the release earned on the quiescent tree.** All **92 test files** and
  all **7 instruments** pass with the exhaustive cases on; the suite sentence is
  re-measured at
  **3,742 tests across 91 of the 92 test files, 14,081 subtests, outside the document check**
  and one `pytest` process over the same tree reports **3,770 passed, 0
  skipped, 16,649 subtests, zero failures**; the end-to-end evaluation is
  **149 / 149** (133 answered, 16 refused as expected, all `boundary`, no
  `gap`, 0 confidently wrong, 0 errored), the benchmarks **2,389 / 2,390** with
  every suite above its baseline, and the probes **33 — 20 hold, 13 break, 0
  errored**.

**Closed the round before.** *The register where the geometric address is the only
reader.* The round before this one made the faculties into a stack and found
the geometry carrying a **residue** — 16 queries in 1,626, mostly constants and
calibration lemmas — and named the right question as the next candidate: is
there a register in which a geometric address is *structurally* the only
faculty that can read the query, making the carry set a class? There is, and it
is written up in
[`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md):

* **the register, declared before it was measured.** A query is *anonymous*
  when its identifiers are not the corpus's — a goal from a second
  formalisation, a generated goal with no names yet, an autoformalised
  statement in its source's vocabulary. The reproducible form of it is
  renaming: every identifier outside a declared vocabulary of 39 words (Lean's
  own syntax, and the type names the feature map already counts) is replaced by
  a positional placeholder, and the placeholders are *checked* fresh against
  the corpus rather than assumed (`glm_universal.reasoning.anonymous`);
* **what it does to each faculty.** Over the same 813 queries at `k = 5`, the
  text search falls **710 → 84** and the identifier address book **388 → 48** —
  both to the **48** hits chance gives — while the structural address holds
  **232 → 171** and leads every other faculty in the register by more than a
  factor of two. The identifier address book is the control that matters: it is
  geometric too, and it collapses, so what survives is the *structural*
  reading, not geometry in general;
* **why, as a theorem and as an audit.** `RequestProject/GLM/Anonymous.lean`
  (113th Lean file): `features_anonymise` — any reading that is a function of
  the kept skeleton is unchanged by a renaming; `overlap_anonymise_eq_zero` —
  a fresh renaming leaves the text faculty's exact overlap at zero, so it has
  no evidence by construction; and `relay_hands_over` — with confidence zero
  the relay of `Relay.lean` is the interleave. Measured against the *shipped*
  feature map rather than the idealisation, 780 of 813 queries keep every
  syntax coordinate, and the 33 that do not move only the six coordinates that
  count type words, because the shipped map counts those words inside
  identifiers too. That leak is an audit finding of this round, reported rather
  than repaired;
* **and the stack notices on its own.** The gate is the relay study's 1/10,
  not re-tuned and not told about the register: it fires on **538** of the 813
  anonymous queries against **24** of the same queries read plainly, and the
  relay lifts the text leader **84 → 128**. `report anonymous`, with its
  column-3 script, a 27-test file and a pipeline row;
* **what it does not settle,** stated in the study and repeated here: this is
  not a reversal of the standing negative result — where names are informative
  the text search is still the better faculty by a wide margin — the absolute
  rate in the register is modest (about one query in five against one in
  seventeen by chance), and the register is *constructed* by renaming rather
  than observed in the wild.

**Closed the round before.** *The faculties made into a stack: the geometry given the
queries the text layer cannot read.* The standing negative result of
[`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md) — retrieval
by lattice address beats chance and loses to a plain lexical overlap — was
measured with each faculty answering *alone*. This round asked what the machine
does when they answer together, and the answer is in
[`STACK_RELAY_STUDY.md`](studies/STACK_RELAY_STUDY.md):

* **the relay, and the confidence that fires it.** A faculty reports how much
  evidence it has for *this* query; below a stated gate of 1/10 the leading
  lexical search is judged to have abstained and the two geometric address
  books answer in its place, by a stated quota and interleave
  (`glm_universal.reasoning.stack`). At `k = 5` the stack is ahead of the text
  control on the tuning stride (356 → 362 of 407), on a disjoint held-out
  stride (354 → 358 of 406) and on bare goal queries (710 → 715 of 813), and it
  is never below it at any window of the ladder;
* **and the gain is the substrate's.** The gate fires on 48 of 1,626 queries,
  the geometry carries **16** queries the text control misses against **1**
  lost, and the same relay to the digest addresses and a seeded permutation
  carries **1** while a relay to the name search carries **none**. Every
  threshold from 1/20 to 1/4 improves on the control, so the gate is a stated
  mechanism rather than a fitted constant;
* **what is a theorem rather than a hit rate.** `RequestProject/GLM/Relay.lean`
  (112th Lean file): `relay_confident` — above the gate the relay *is* the
  leader's ranking, so the stack cannot cost anything where the leader is
  strong; `mem_relay` and `interleave_nodup` — nothing invented, nothing
  offered twice; and `relay_carry`, the carry theorem — whatever a faculty
  holds inside its quota is inside the answer's window of the summed quotas, so
  a faculty that has the answer cannot be drowned out by the ones that do not;
* **the same stack in a register with no text in it.** `vision_stack.py` runs
  the identical relay over the 50 ARC training puzzles kept under
  `overlay/arc_agi_17/data/training`, with a generator, an eight-dimension
  visual filter and a cross-domain word check: the cheap look removes **95.3 %**
  of the 1,089 proposals before the expensive verification gate sees them, two
  different faculties supply the rule that verifies, and the relay solves a
  puzzle its leading faculty does not — 2 of 50, which is the honest headline
  for these generators;
* **a defect fixed at the root.** `--refresh` rebuilt the declaration address
  book and the document address book and *not* the lexical address book, which
  is keyed to the same digest and read by the same measurements; a Lean file
  added this round left it stale. It is now the second step of the ordered
  chain and the chain's docstring says so.

**Closed two rounds before.** *The cost of keeping the claims current, measured and
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
exhaustive cases on passes **all 92 test files** and **all 7 instruments**, and
the complete-run sentence the documents quote is re-measured at
**3,742 tests across 91 of the 92 test files, 14,081 subtests, outside the document check**;
one `pytest` process over the same tree with `GLM_EXHAUSTIVE=1` reports
**3,770 passed, 0 skipped, 16,649 subtests, zero failures**. Nothing the system
answers moved: `lake build` completes over
**117 Lean files** with **0 `sorry`** in
both copies, the end-to-end evaluation passes every case in the set (**147** of
them at that round, **149** now), the benchmarks **2,389 / 2,390**, and the
probes 33 with 20 holding.

**Closed two rounds before this one.** *Five pieces of work finished, and the four
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

