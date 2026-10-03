# What a round costs: the rebuild chain, measured and cut

## Tier 0 — the coarse read

**Question.** Everything this repository claims is recomputed from the tree. What does one iteration of that cost, and how much of the cost is work that did not need doing?

**Verdict.** Most of the cost was work repeated on things that had not moved, and a cache keyed on what it is derived from does not repeat it.

**Deciding figure.** Rebuilding both address books from nothing decodes <!--figure:rebuild-decodes-from-nothing-->11,463<!--/figure--> vectors and against the stored books decodes <!--figure:rebuild-decodes-now-->0<!--/figure-->; the planner's report is taken once per change instead of <!--figure:planner-reports-per-check-->5<!--/figure--> times per check.

**Recomputed by.** `glm_universal.corpus.cost.cost_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

Code: [`glm_universal/corpus/cost.py`](../overlay/glm_universal/corpus/cost.py),
[`glm_universal/reasoning/lean_address.py`](../overlay/glm_universal/reasoning/lean_address.py),
[`glm_universal/corpus/address.py`](../overlay/glm_universal/corpus/address.py),
[`glm_universal/derived.py`](../overlay/glm_universal/derived.py),
[`glm_universal/signoff/rules.py`](../overlay/glm_universal/signoff/rules.py),
[`glm_universal/signoff/ledger.py`](../overlay/glm_universal/signoff/ledger.py).
Tests: [`glm_universal/tests/test_corpus.py`](../overlay/glm_universal/tests/test_corpus.py),
[`glm_universal/tests/test_lean_address.py`](../overlay/glm_universal/tests/test_lean_address.py),
[`glm_universal/tests/test_derived.py`](../overlay/glm_universal/tests/test_derived.py),
[`glm_universal/tests/test_sandbox_planner.py`](../overlay/glm_universal/tests/test_sandbox_planner.py).
Run: `cd overlay && PYTHONPATH=. python3 -m glm_universal.corpus --refresh`.

---

## 1. The chain, and where the time went

Adding one Lean file used to set off this sequence:

```
a .lean file changes
  → the Lean tree digest changes
    → the declaration address book is stale       (one decode per declaration)
      → the measurement cache is stale            (quadratic in the declarations)
        → three studies print staleness notices instead of tables
          → figures quoted by hand in eight documents move
            → the suite counts move, and they are quoted too
```

Every link is sensible on its own. What made it expensive is that the work was
**repeated** on parts that had not moved: each cache was keyed on a digest of
its **whole** input — the entire Lean tree, the entire
corpus — so a change of about one and a half per cent of the corpus threw away
one hundred per cent of the derived work.

Three things were measured before anything was changed, and they are the three
this round addressed.

* **The address books.** Rebuilding the declaration book decoded once per
  declaration: sixty-five seconds for a tree in which, typically, one file had
  moved.
* **The document check.** `--check` renders every generated block. Five of
  them quote the reverse-call planner's report, and the report was re-taken for
  each one: five passes over the evaluation set, about fifteen minutes in all,
  for a check that changes nothing.
* **The prose.** Numbers inside sentences were reconciled by hand every round.
  That sweep is where a stale number survives: this round began with the suite
  described as *88 test files* in five documents, the evaluation set as
  *134 cases* in one and *141* in another, against 89 and 147.

## 2. What an address book is keyed on now

An address is a function of the feature vector and of nothing else — that is
`GLM.Address.address_congr`, the theorem that says equal features force equal
addresses. So an answer may be reused exactly when the vector has been decoded
before: in this rebuild, or in the stored book of the last one. A file that has
not changed contributes the vectors it contributed before, and they cost
nothing.

<!-- generated: cost-addresses -->
| book | units | decodes from nothing | decodes now | reused |
|---|---|---|---|---|
| Lean declarations | 4,539 | 8,593 | 0 | 9,078 |
| corpus sections | 1,460 | 2,870 | 0 | 2,920 |

Reuse is checked, not assumed: each rebuild re-decodes a sample of the answers it reused and reports any that moved (4 sampled in the declaration book, 4 in the document book, none moved).
<!-- end generated -->

The reuse is not asserted. `glm_universal.reasoning.lean_address.Decoder`
counts what it reused and what it decoded, and its `audit` re-decodes a sample
of the reused answers from scratch and reports any that moved; the rebuild
prints that count. `tests/test_lean_address.py` checks the cheap direction on
every run — the rebuilt book is the stored book, and nothing was decoded — and
the exhaustive run checks the expensive one, decoding every address from
nothing and requiring the two books to be equal byte for byte.

## 3. The report five blocks shared

<!-- generated: cost-planner -->
| reading | value |
|---|---|
| blocks quoting the report | 5 |
| evaluation cases per report | 177 |
| reports taken per check, before | 5 |
| reports taken per check, now | 0 |
| stored report | fresh |

The store is keyed on the import closure of `glm_universal.sandbox.planner` -- the code the report is derived from, and not the documents that quote it -- so a documentation round does not re-take it and a change to the planner does.
<!-- end generated -->

Two layers, both of them the pattern the package already used for data. Within
one process the report is memoised, so five blocks cost one report. Across
processes it is stored beside the digest of the code it is derived from, which
`glm_universal.signoff.ledger.code_store` computes as the import closure of
`glm_universal.sandbox.planner` — the modules it can reach and the frozen
tables they read, with the documents left out, because the report reads no
document.

One line of the promotion checklist needed care. The checklist's *deterministic*
line is measured by planning the declared tasks twice and comparing; a memo
compared with itself would make that line true by construction. The repeat is
therefore taken from `task_rows.__wrapped__`, the uncached derivation, and
`tests/test_sandbox_planner.py` reads the source to require it.

## 4. A figure inside a sentence

A generated block hands a whole section to the code that measures it. That
works for tables and not for a sentence, and the sentences were where the drift
lived. The block mechanism is now available at the size of a phrase:

```markdown
the suite is <!--figure:test-files-->143 test files<!--/figure--> today
```

The markers are HTML comments, so a reader sees only the number. `--refresh`
rewrites the body, `--check` fails when it has drifted, and a marker naming a
figure nothing emits is a reported defect rather than a silent no-op.

<!-- generated: cost-figures -->
164 figures are registered and 569 markers carry them, across 30 documents.  A marker whose text is not what its figure now says is what `--refresh` rewrites and what `--check` fails on.

The registry: `binding-ambiguous`, `binding-as-declared`, `binding-carriers`, `binding-control-wrong`, `binding-declared-count`, `binding-largest-fibre`, `binding-nameable`, `binding-product-recoverable`, `binding-product-zero`, `binding-readings`, `binding-reasons`, `binding-recovered`, `binding-refused`, `binding-roles`, `conversation-alone`, `conversation-answered`, `conversation-as-declared`, `conversation-control-rows`, `conversation-control-wrong`, `conversation-declared-count`, `conversation-reasons`, `conversation-refused`, `corpus-archive-documents`, `corpus-documents`, `corpus-sections`, `corpus-state-documents`, `directive-count`, `directives`, `evaluation-case-count`, `evaluation-cases`, `extremum-answered`, `extremum-as-declared`, `extremum-declared-count`, `extremum-reasons`, `extremum-reasons-declared`, `extremum-refused`, `extremum-ties`, `fieldsurface-fields`, `fieldsurface-held`, `fieldsurface-moved`, `fieldsurface-pairs`, `fieldsurface-parsed-after`, `fieldsurface-parsed-before`, `fieldsurface-predicted`, `fieldsurface-rows`, `fieldsurface-surface-after`, `fieldsurface-surface-before`, `fieldsurface-tables`, `lean-declaration-files`, `lean-declarations`, `lean-file-count`, `lean-files`, `normesc-correct`, `normesc-family-correct`, `normesc-family-rungs`, `normesc-family-wrong`, `normesc-first-broken`, `normesc-longest-safe`, `normesc-named-correct`, `normesc-named-rungs`, `normesc-queries`, `normesc-refused`, `normesc-rungs`, `normesc-wrong`, `normfamily-norms`, `normfamily-rung-count`, `opesc-count`, `opesc-program-correct`, `opesc-program-queries`, `opesc-program-wrong`, `oracle-absent`, `oracle-english`, `oracle-parsed`, `oracle-parser-worth`, `oracle-questions`, `oracle-surface`, `ordering-answered`, `ordering-as-declared`, `ordering-declared-count`, `ordering-held`, `ordering-parsed-after`, `ordering-parsed-before`, `ordering-reasons`, `ordering-refused`, `ordering-surface-after`, `ordering-surface-before`, `ordering-surface-parsed`, `planner-reports-per-check`, `plans-ambiguous`, `plans-bare-probe-correct`, `plans-bare-probe-refused`, `plans-bare-probe-wrong`, `plans-frames`, `plans-gained`, `plans-gains-address`, `plans-gains-derive`, `plans-gains-table`, `plans-held-bare-correct`, `plans-held-bare-correct-refusal`, `plans-held-bare-wrong`, `plans-held-correct`, `plans-held-correct-refusal`, `plans-held-total`, `plans-held-wrong`, `plans-probe-correct`, `plans-probe-refused`, `plans-probe-wrong`, `plans-questions`, `plans-stress-bare-correct`, `plans-stress-bare-wrong`, `plans-stress-correct`, `plans-stress-correct-refusal`, `plans-stress-first-correct`, `plans-stress-first-refused`, `plans-stress-refused`, `plans-stress-wrong`, `plans-units`, `planstore-coarse-wrong`, `planstore-declared-count`, `planstore-refusals`, `planstore-refusals-replayed`, `planstore-replayed`, `planstore-trials-first`, `planstore-trials-replayed`, `planstore-worst-case`, `probe-correct`, `probe-derived`, `probe-lexicon-held`, `probe-lexicon-words`, `probe-pass-mark`, `probe-questions`, `probe-refused`, `probe-wrong`, `query-kinds`, `reasoning-modules`, `rebuild-decodes-from-nothing`, `rebuild-decodes-now`, `registers`, `repo-cache-bytes`, `repo-cache-share`, `repo-primary-bytes`, `repo-stored-bytes`, `report-subjects`, `scales-answered`, `scales-as-declared`, `scales-bridged`, `scales-declared`, `scales-numeric`, `scales-pairs`, `scales-quantities`, `scales-refused`, `scales-rows`, `scales-still-refused`, `secondread-adopted`, `secondread-configurations`, `secondread-given-up`, `secondread-matched-removes`, `secondread-program-correct`, `secondread-program-refused`, `secondread-program-wrong`, `secondread-shipped`, `suite`, `test-file-count`, `test-files`.
<!-- end generated -->

Two rules keep it honest. A figure must be **cheap** — a check renders every
one of them — and **live**, computed from the tree as it stands rather than
read out of a cache that could be stale; anything failing either test belongs
in a block, where staleness can be reported in the body. And a passage marked
`<!-- figures:history -->` is a record of a past round: the refresh leaves its
figures exactly as they were written, and a live marker found inside one is
reported as a defect, because a record that updates itself is not a record.

## 5. One command, in the one order that converges

The measurement cache is computed *from* the stored address book but stamped
with the digest of the tree as it stands. Re-measuring before rebuilding the
book therefore produced figures for the previous tree wearing the current
tree's digest — fresh-looking and wrong. It happened once, and cost a full
cycle.

`python3 -m glm_universal.corpus --refresh` now does the whole chain in
dependency order: the Lean address book, the document address book, the
measurements, then the generated documents, blocks and figures, and finally a
second pass that checks the result is a fixed point. Doing it by hand in the
wrong order is refused: `write_measurements` raises
`glm_universal.corpus.measurements.StaleAddressBook` rather than measuring a
book that no longer describes the tree.

## 5a. The line that stopped the ledger being selective

The sign-off ledger is only worth having if a change makes a *few* units
stale. It was not selective, and the reason was one rule: a module whose
string constants named **any** `.lean` file pulled the **whole** Lean
development into its closure. That is the safe direction, and it was written
as such — but the constants it fires on are mostly prose. A docstring in
`reasoning/wobble.py` mentions `Sturmian.lean`; `wobble.py` is reachable from
most of the package; so every unit that reached it depended on all 118 Lean
files, and one Lean edit made almost the whole suite stale.

A named file is now resolved to itself, in both copies, and only a `*.lean`
glob — what a module that *walks* the tree writes — or a name the development
does not hold still takes everything. Both halves are tested
(`tests/test_signoff.py`), and the second half is what keeps the change safe:
nothing that reads the tree loses its dependency on the tree.

A token written as a path is resolved the same way. `"studies/RECIPE_STUDY.md"`
names one file; resolving it by base name pulled in every file of that name,
which for the fifteen `README.md` in the tree meant that editing any one of
them made every unit that named a readme stale.

Measured over the suite, by `glm_universal.corpus.cost.lean_blast_radius`:

| | |
|---|---|
| test units in the suite | 143 |
| Lean files | 169 |
| units an edit to *any* Lean file used to make stale | 129 |
| units one Lean file makes stale now, median | 57 |
| units the worst single Lean file makes stale | 124 |
| units that read the tree with a glob, so are stale whenever it moves | 57 |

The Lean row counts distinct file names the ledger tracks, so it is the
development's 168 files under `RequestProject/GLM/` plus the build's
`Main.lean`. Phases 89 and 90 added three Lean files (`QuestionSetB.lean`,
`QuestionSetBAnswers.lean`, `TypedOperators.lean`). Phase 90 also added one
unit, `test_typed_operators.py`, which reaches the router and cites its Lean
file, so every row but the file count moved by one. Phase 91 added one Lean
file (`DeclaredFrames.lean`) and one unit, `test_stepwise_five.py`, which
reaches the router and cites its Lean file, so every row moved by one. Phase
92 added one Lean file (`DiscourseState.lean`) and one unit,
`test_discourse_state.py`, which reaches the router and cites its Lean file,
so every row moved by one again. Phase 93 added one Lean file
(`RegisterWorld.lean`) and one unit, `test_register_world.py`, which reaches
the router and cites its Lean file, so every row moved by one once more. Phase
94 added one Lean file (`ThirdSort.lean`) and one unit, `test_third_sort.py`,
which reaches the router and cites its Lean file, so every row moved by one
again. Phase 95 added one Lean file (`ImperativeGrammar.lean`) and one unit,
`test_imperative_grammar.py`, which reaches the router and cites its Lean
file, so every row moved by one once more. Phase 96 added one Lean file
(`SecondView.lean`) and one unit, `test_second_view.py`, which reaches the
router and cites its Lean file, so every row moved by one again. Phase 97
added one Lean file (`OnDemandView.lean`) and one unit, `test_unpacking.py`,
which reaches the router and cites its Lean file, so every row moved by one
once more. Phase 68 added one unit (`test_reverse_tct_two.py`) that reaches
the router, and so the development through it, which is why the floor moved
from 34 to 35 with the other rows; Phase 69 added another
(`test_reverse_tct_int.py`), and the floor moved from 35 to 36; Phase 70
added `test_native_parity.py`, which reads the Lean corpus, and the floor
moved from 36 to 37; Phase 71 added `test_native_words.py`, which reads it
too, and the floor moved from 37 to 38; Phase 72 added `test_stepwise.py`,
which reaches the router and cites its Lean file, and the floor moved from 38
to 39; Phase 73 added `test_stepwise_two.py`, which does the same for
`StepwiseFrames.lean`, and the floor moved from 39 to 40; Phase 74 added
`test_law_register.py`, which cites `LawRegister.lean` and reads the
development, and the floor moved from 40 to 41.

Phases 75 and 76 added `test_law_absorption.py` and `test_held_precision.py`
without moving the floor, but they reintroduced the leak the next paragraph
describes: the substrate frame put `law_absorption.py` on the planner's import
path, it imports `law_register.py`, which imports `deep_dive.py`, which imports
`salvage.py` — and three provenance labels in `salvage.py` named archive Lean
files the development does not hold, which the closure resolves to the whole
development. Every unit that builds a session carried all of it (the median
Lean edit went to 103 units). The labels now name the archive folder and the
file in words, and the median is back to 42. Phase 77 added
`test_decoder_confidence.py`, which reaches the router through the Python
dialect as `test_python_speech.py` does, and the floor moved from 41 to 42
and the median from 42 to 43 with it.
Phase 78's closure rules (§5g) — docstrings no longer dependencies, Lean
names that do not exist ignored rather than widened to the whole development —
moved the floor from 42 to 38, the median from 43 to 39, and the units that
name any Lean file from 111 to 109.
Phase 79 added `test_integer_decision.py`, which reaches the router and
cites `IntegerDecision.lean`, and the floor moved from 38 to 39, the median
from 39 to 40, and the units that name any Lean file from 109 to 110.
Phase 80 added `test_confidence_floor.py`, which reaches the router through
the Python dialect and cites `ConfidenceFloor.lean`, and the floor moved from
39 to 40, the median from 40 to 41, and the units that name any Lean file from
110 to 111.
Phases 81–83 added `test_agree_channel.py`, `test_rate_posterior.py` and
`test_law_triage.py`; the first two reach the router through the Python
dialect and cite `Agree.lean` and `RatePosterior.lean`, and the floor moved
from 40 to 42, the median from 41 to 42, the worst single file from 106 to
109, and the units that name any Lean file from 111 to 114.
Phase 84 added `test_stepwise_three.py`, which reaches the router and cites
`StepwiseWiden.lean`, and the floor moved from 42 to 43, the median from 42
to 43, the worst single file from 109 to 110, and the units that name any
Lean file from 114 to 115.
Phase 85 added `test_stepwise_four.py`, which reaches the router and cites
`HoleBounds.lean`, and the floor moved from 43 to 44, the median from 43
to 44, the worst single file from 110 to 111, and the units that name any
Lean file from 115 to 116.
Phase 86 added `test_measurands.py`, which reaches the router and cites
`MeasurandKinds.lean` (and added `RateRepair.lean`, cited by
`test_rate_posterior.py`), and the floor moved from 44 to 45, the median from
44 to 45, the worst single file from 111 to 112, and the units that name any
Lean file from 116 to 117.
Phase 87 added `test_measurand_register.py`, which reaches the router and
cites `MeasurandRegister.lean`, and the floor moved from 45 to 46, the median
from 45 to 46, the worst single file from 112 to 113, and the units that name
any Lean file from 117 to 118.
Phase 88 added `test_planner_loop.py`, which reaches the router through the
Python dialect and cites `PlannerLoop.lean`, and the floor moved from 46 to
47, the median from 46 to 47, the worst single file from 113 to 114, and the
units that name any Lean file from 118 to 119.
Phase 89 added `test_question_frames.py`, which reaches the router and cites
`QuestionSetB.lean`, and `test_contract_matrix.py`, and the floor moved from
47 to 49, the median from 47 to 49, the worst single file from 114 to 116, and
the units that name any Lean file from 119 to 121.

The floor of 35 is not a defect: those units name a `*.lean` glob because they
read the development, and a reading of the development is stale when the
development moves. The change is that the other 67 units now depend on the
files they name rather than on all of them. Naming one Lean file used to mean
carrying all of them.

**The floor has to be defended, not won once.** It was lost between §5e and
the round that measured it again: the probe oracle reads one declaration's
file name, it read it off the development rather than off the book, and every
unit that reaches the probe — which is most of them, through the field surface
— carried the whole tree again, taking the median from its floor back to **81**. The
repair is the same one §5e describes, applied to the second reader, and the
leak is easy to reintroduce for a reason worth stating: the closure is
computed from *string constants*, so a docstring that writes the glob, or even
the bare extension, is a dependency on the whole development exactly as an
`rglob` call is. A sentence explaining the rule broke the rule while it was
being written.

## 5b. The check that was paying for a derivation

The cache of §3 fixed the *repetition* — five blocks quoting one report, one
pass instead of five — and left the harder half in place: when the report's
cache is **stale**, something has to rebuild it, and what was rebuilding it was
the documents check. On the tree as it stood at the start of this round the
planner's cache was stale by one edit to a docstring, and
`corpus --check` took **more than twenty minutes** before printing anything.
That is the worst possible place to put the cost: the check is the thing a
session runs to find out whether it has broken something, so it is run often
and it is run first.

The rule now is that **a reader may report a stale derivation and may not pay
for one**. `glm_universal.derived.no_recompute` is a context manager inside
which `DerivedStore.cached` raises `StaleDerivation` instead of computing, and
`corpus --check` runs its whole pass inside it; the message names the artefact
and the command that rebuilds it. Measured on this tree:

| | before | after |
|---|---|---|
| `corpus --check`, planner cache fresh | ~25 s | ~25 s |
| `corpus --check`, planner cache stale | > 20 min | **26 s**, with the reason named |
| `corpus --refresh`, planner cache stale | ~16 min | ~6 min |

Two things made the refresh itself cheaper, and both are exact rather than
approximate:

* **The quantiser decodes on scaled integers.** Every cost the LLVQ decoder
  compares was a `Fraction`. Multiplying through by the square of a common
  denominator of the target makes each one an `int`, which changes no
  comparison and no tie, so the decoded point is the point the rational route
  returns — checked against `analogy.nearest_lattice_point` over the whole
  agreement sweep, and helper by helper in `tests/test_llvq_table.py`. On 200
  targets after warm-up: **1.15 ms** a call against **10.55 ms**.
* **The planner's reading runs on every core.** It asks the live runtime each
  declared evaluation case — 149 of them when this was timed, 164 now;
  serially that is **955 s**, and the
  cases are independent. `fallback_row` takes a case by index and
  `fallback_rows` maps it across a process pool: **362 s** at eight workers.
  The speed-up is 2.6× rather than 8× because the load is uneven — the longest
  single case is **201 s** and the total serial work is **1,168 s**, so no
  arrangement of eight workers finishes sooner than the longest case. That is
  the floor, and it is named here rather than smoothed over: cutting it means
  making `report-lean`, `report-anonymous`, `report-measure`, `report-relay`
  and `report-denotations` cheaper, not adding workers.

## 5c. The rule, the record, and the two questions a session asks

§5a made a *Lean* edit selective. The same defect survived one level up, in
the ledger's own sources. Every unit's closure contains the files that define
what a dependency is — it has to, because if the rule changes no old signature
is trustworthy — and the whole of `signoff/ledger.py` was one of them. But
that file held two different things: the **rule** (what a closure is, what a
digest covers, how a unit is run) and the **record** (the plan, the stored
signatures, the parallel runner, the suite totals, the reporting). Only the
first can change what a test observes. The second is what a round actually
edits — and editing it re-ran all 96 units.

The rule is now `signoff/rules.py` and is in every closure; the record stays in
`signoff/ledger.py` and is in no closure but those of the units that import
it. Measured with `signoff --impact`:

| an edit to | units it makes stale | their last recorded time |
|---|---|---|
| `signoff/rules.py` (the rule) | 96 of 96 | 3,970 s |
| `signoff/ledger.py` (the record) | 6 of 96 | 797 s |
| `signoff/checks.py` (the instrument table) | 2 of 96 | 375 s |
| `signoff/__main__.py` (the command line) | 1 of 96 | 54 s |

The six are the units that import the ledger to test it. The direction of
safety is unchanged: anything that can alter what a test observes is still in
every closure, and `tests/test_signoff.py` now asserts both halves — `rules.py`
is scaffolding, `ledger.py` is not, and a unit that imports the ledger still
carries it.

Two questions a session asks were unanswerable and are now instruments:

* **Why is this unit stale?** A closure splits into five disjoint groups —
  scaffolding, data, documents, Lean, code — whose union is exactly the
  closure. A digest per group is recorded beside the signature (five hex
  strings; they decide nothing), and `signoff --why` reports the groups that
  moved. `changed: documents` is a prose edit that will pass; `changed: code`
  may not.
* **What would this edit cost?** `signoff --impact PATH` inverts the closure
  relation and names the units an edit to that file *would* make stale,
  together with what they last took — before the edit, rather than after.
  `--impact ../PROJECT_DIRECTIVES.md` answers 93 of 96 units and 3,966 s,
  which is the measured form of the standing advice to batch directive edits
  into one pass.

## 5d. The caches nothing was watching

Ten study modules keep a measurement cache: figures that cost minutes to take,
stored beside the digest of the sources they came from, with a `current()`
that returns `None` when the digest has moved. The discipline is right — a
stale measurement refuses rather than answers — but nothing *enumerated* them,
so a stale cache was found by whatever happened to read it. In this round that
was the end-to-end evaluation, twenty minutes into a release run, reporting a
report subject that had gone quiet.

`glm_universal.corpus.caches` is the census, and both halves of it are
computed rather than listed: a module is in it when its source defines both
`module_digest` and `current`, and the command that re-takes it is read out of
`tools.py` by resolving the aliases its handlers use and finding the
sub-command whose handler calls `write_measurements()`. `corpus --check` runs
the census — a read and a digest per cache, a fraction of a second — and names
each stale one together with the exact command, in the same half-minute it
already cost. It never re-takes one: that is minutes of work and belongs to
the session, not to a check (D16).

| | |
|---|---|
| measurement caches in the package | 10 |
| found by shape rather than by a list | 10 |
| whose re-taking command is read out of `tools.py` | 10 |
| stale when the census was first run | 1 (`query_escalation`) |
| where that staleness used to surface | a failing evaluation, ~20 min into a release |

## 5e. The selectivity that a new feature quietly undid

§5a is a property of the *tree*, not of the rule alone: it holds only while
nothing on the runtime's import path reads the whole development. A later
round wired a **field surface** into the session, and one of its tables — the
Lean address table — loaded its rows by calling
`reasoning.lean_address.declarations()`, which walks the development and
parses every file. The session is imported by nearly every test, so the
whole development re-entered nearly every closure and the ledger stopped being
selective. Nothing failed visibly; what happened is that a round that touched
one Lean file paid for most of a release.

The ledger caught it, because §5a had been written down as a test rather than
as a paragraph: `tests/test_signoff.py` asks that a unit naming one Lean file
carries that file and not the rest, and `tests/test_corpus.py` asks that the
numbers in the table above are the numbers the code computes. Both failed.
That is the argument for pinning a cost property the same way a claim is
pinned: an efficiency gain that nothing checks is an efficiency gain with a
half-life.

The fix is a boundary rather than a workaround, and it is the same split as
§5c. Reading the development and answering from what was read are two jobs:

* `reasoning/lean_address.py` **builds** the address book — it walks the tree,
  parses it, decodes the addresses, and writes the book. It belongs to the
  refresh chain.
* `reasoning/lean_book.py` **answers** from the book. It opens one generated
  file, names no source of the development and imports nothing that does.

The field surface now takes its Lean rows from the book, so the runtime does
not read the development at all; the book carries the namespace and the head
of each statement (schema 2) so the surface answers exactly what it answered
before, field for field. Whether the book still *describes* the development
is a separate question that needs the tree, and it stays where it was — with
`lean_address.cache_state()` and `corpus --check`, which report a stale book
and name the command that rebuilds it.

Measured on the same instrument as §5a, before and after:

| | with the surface reading the tree | reading the book |
|---|---|---|
| units one Lean file makes stale, median | 79 | **27** |
| units that take the whole development | 79 | **27** |
| units the worst single Lean file makes stale | 82 | 81 |
| units an edit to *any* Lean file makes stale | 85 | 85 |

The last two rows are the honest part of the table: this changes *nothing*
about units that genuinely read the development, and nothing about the
over-approximation by which a unit that names a Lean file in its prose depends
on it. What it changes is the common case, which is the case a round pays for.

## 5f. The check that does not have to be asked

The documents gate renders all 97 generated blocks and all 201 inline figures
across the corpus and compares each with what is written. That is the right
thing to do after an edit. It is *also* what it did on picking a round up,
when nothing at all had moved since the last round closed — and the answer a
check gives about a tree that has not changed is the answer it gave last time.

So the verdict is now stored beside a digest of everything the check can read:
the documents, the code that renders them, the frozen data that code reads and
the Lean sources the blocks quote — computed as the sign-off ledger's own
closure of the corpus command, so nothing the check reads is outside it. If
the digest matches and the stored verdict was a **pass**, the check says so and
stops.

| | blocks rendered | figures rendered | about |
|---|---|---|---|
| after an edit, or with `--check --all` | 97 | 201 | 50 s |
| nothing in the closure has moved | 0 | 0 | 3 s |

Three things keep it from being a way to miss a defect. Only a pass is ever
recorded, so a session that has just been told what is stale runs the whole
gate again and sees the same failure. The digest is over the closure rather
than over a list, so a file that moves without mattering costs one full check
while a file that matters cannot move unnoticed — the same direction of safety
as §5a. And `--check --all` refuses the record outright, which is what the
release does: the record is an optimisation, and nothing depends on it being
there.

The measurement is `glm_universal.corpus.gate`, and
`tests/test_corpus.py::TestTheDocumentsGateRecord` pins what the digest covers,
that a failure is never skippable, and that a record written under another rule
is ignored rather than trusted.

## 5g. The round that invalidated itself

**The problem, as the owner put it.** Every round had to re-check most of the
repository, rounds ran out of time before the close, and during a close some
numbers moved again, so the close had to be repeated. Measured on the tree at
the start of Phase 78, with the ledger's own closure rule:

* the tree held **two copies of the Lean development** (`RequestProject/GLM/`
  at the repository root and `overlay/glm_lean/RequestProject/GLM/`), both
  hashed into every closure that named a Lean file, kept in step by a
  generator and checked by a seventh instrument;
* a unit's closure averaged **284 files**;
* every `_data/` directory beside a module was hashed whole, so re-taking
  **one** measurement cache made **117 of 123** units stale (about 82 CPU
  minutes), because `reasoning/_data/` holds eighteen files and nearly every
  unit reaches some reasoning module;
* a document named anywhere in a module's string constants was a dependency,
  docstrings included, so `PROJECT_DIRECTIVES.md` was in **120** closures;
* a document was hashed whole, so `corpus --refresh` rewriting a figure inside
  a sentence made every unit that named that document stale, although nothing
  a person wrote had moved;
* the native-parity and native-words caches were keyed on the repository's own
  documents and Lean tree. Writing the round up moved that corpus, so the
  caches went stale; re-taking them could move a tie; the study reporting the
  tie then had to change, which moved the corpus again. That is the circular
  close.

**What changed.** Six edits, all computed rather than listed:

1. **One Lean copy.** `lakefile.toml` builds `overlay/glm_lean` in place
   (`srcDir`); the repository-root copy, the mirror generator
   (`tools lean-mirror`, `signoff/mirror.py`) and the `lean-copies-identical`
   instrument are gone. `lake build` compiles the files the package reads.
2. **Data by name** (`signoff/rules.py`, `_data_files_for`). A data file is in
   a closure when a module of that closure names it, or names a file pattern
   with its suffix (`*.json`). Re-taking one cache now stales the units that
   read it: **22** for `native_parity.json`, **23** for `typed_plans.json`.
3. **Docstrings are prose** (`_string_constants(docstrings=False)`). A
   document or Lean file mentioned only in a docstring is not a dependency,
   unless the closure holds a module that reads docstrings (`__doc__`,
   `get_docstring`). One descriptive `note=` string in
   `evaluation/cases.py` that named the directives file was reworded.
   `PROJECT_DIRECTIVES.md` is now in **32** closures (was 120),
   `MASTER_PLAN.md` in 30 (was 38), `STATUS.md` in 24 (was 39), and a
   commonly cited Lean file such as `Sturmian.lean` in 47 (was 103).
4. **Generated regions are masked** (`document_digest`). A unit is signed
   against a document's written part: inline figure values and generated
   block bodies are emptied, markers kept. The **19** units whose closure
   holds the renderer, the document checks or the figure registry are still
   signed against raw bytes, since those regions are what they check; the
   other **104** are not re-run by a refresh that only moved numbers.
5. **Self-measurements are dated, not gated** (`native_parity`,
   `native_words`). Their `module_digest` covers the measuring code only; the
   corpus they were taken over is stored as `corpus_digest`, and a moved
   corpus is a `note:` in `corpus --check`, never a failure. They are re-taken
   when their code moves or when a round decides to, at its start.
6. **Derivations do not key on the harness** (`code_store`). A derived store
   such as the planner's reading of the evaluation set no longer includes
   the test scaffolding and the sign-off rule in its key, so an edit to the
   rule stops costing a re-derivation.

And one change of procedure: a round closes with **`signoff --close`** — the
release question (every unit and instrument signed with the exhaustive cases
on), paid incrementally, then `--verify-release`. A from-scratch `--release`
ignores the ledger and re-runs about 97 CPU minutes of tests plus the
instruments; it is now reserved for a change to the rule itself. The ledger's
plan also got cheaper to compute: tokens, module paths and repository paths
are memoised per process, which roughly halved `signoff --plan` on this
machine.

**Measured after the change**, same tree, same 123 units: the mean closure is
**183 files**, against 284 before: removing the second Lean copy accounts for
284 → 213 and the new closure rules for 213 → 183.
What one rule change costs is unchanged by design: this round bumped the
ledger schema, so this round's close re-ran everything once.

**What it does not fix.** The package's import graph is still dense: about
ninety units reach the same core of roughly a hundred modules, so a code edit
in that core still re-runs most of the suite, and `lean_addresses.json`, which
the runtime's field surface reads, is in **99** closures — a new Lean file,
once the refresh rebuilds the book, still re-runs those units. Cutting that
is a refactor of the package (lazy imports on the hub modules and a
declaration book the session loads on demand), and is named for a later
round rather than claimed here.

## 6. What this does not establish

It does not make anything faster that was not repetition. The measurement cache
is still quadratic in the declarations and still costs about four minutes when
the Lean tree moves; the full test suite is still an hour of work, parallel
across cores rather than shortened. Nothing here changes a claim the system
makes — every number is still recomputed from the tree, and every cache is
still refused when its input has moved. What changed is how often the same
answer is computed twice.

It is also only one side of a ledger. What is priced here is the cost of
*keeping* a derived table — the rebuild, the digest, the check — which is
exactly what a comparison between generating an object and looking it up has
to charge the lookup with, and usually does not.
[`ZERO_STORAGE_STUDY.md`](ZERO_STORAGE_STUDY.md) §8 puts the two sides
together: the data footprint saved by generating, against the work per use
that pays for it, with the storage, loading, digesting and rebuilding of the
table counted on the table's side rather than assumed away.

<!-- generated: cost-tier -->
**Rebuilding both address books from nothing decodes 11,463 vectors; rebuilding them against the stored books decodes 0.**  The planner's report, one pass over 177 evaluation cases, is quoted by 5 generated blocks and is now taken 0 times per check instead of 5.  569 figures inside sentences, across 30 documents, are emitted rather than typed.
<!-- end generated -->
