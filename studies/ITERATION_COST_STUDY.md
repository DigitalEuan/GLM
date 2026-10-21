# What a round costs: the rebuild chain, measured and cut

## Tier 0 — the coarse read

**Question.** Everything this repository claims is recomputed from the tree. What does one iteration of that cost, and how much of the cost is work that did not need doing?

**Verdict.** Most of the cost was work repeated on things that had not moved, and a cache keyed on what it is derived from does not repeat it.

**Deciding figure.** Rebuilding both address books from nothing decodes <!--figure:rebuild-decodes-from-nothing-->15,340<!--/figure--> vectors and against the stored books decodes <!--figure:rebuild-decodes-now-->0<!--/figure-->; the planner's report is taken once per change instead of <!--figure:planner-reports-per-check-->5<!--/figure--> times per check.

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
| Lean declarations | 5,893 | 10,958 | 0 | 11,786 |
| corpus sections | 2,243 | 4,382 | 0 | 4,486 |

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
| evaluation cases per report | 223 |
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
the suite is <!--figure:test-files-->226 test files<!--/figure--> today
```

The markers are HTML comments, so a reader sees only the number. `--refresh`
rewrites the body, `--check` fails when it has drifted, and a marker naming a
figure nothing emits is a reported defect rather than a silent no-op.

<!-- generated: cost-figures -->
164 figures are registered and 593 markers carry them, across 32 documents.  A marker whose text is not what its figure now says is what `--refresh` rewrites and what `--check` fails on.

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
| test units in the suite | 186 |
| Lean files | 210 |
| units an edit to *any* Lean file used to make stale | 172 |
| units one Lean file makes stale now, median | 82 |
| units the worst single Lean file makes stale | 156 |
| units that read the tree with a glob, so are stale whenever it moves | 82 |

The Lean row counts distinct file names the ledger tracks, so it is the
development's 185 files under `RequestProject/GLM/`, the reference tool and
the build's `Main.lean`. Phases 89 and 90 added three Lean files (`QuestionSetB.lean`,
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
once more. Phase 99 added one Lean file (`CelsiusRegister.lean`) and one
unit, `test_celsius_register.py`, which reaches the router and cites its Lean
file, so every row moved by one again. Phase 100 added one Lean file
(`CorpusResample.lean`) and one unit, `test_corpus_resample.py`, which reads
the Lean corpus and cites its Lean file, so every row moved by one once more.
Phase 101 added one Lean file (`CitationScope.lean`), the elaborator's
reference tool (`glm_lean/tools/CitationReference.lean`, which the ledger
also tracks) and two units, `test_citation_scope.py` and
`test_proof_dependency.py`; Phase 102 added one Lean file (`DocumentTree.lean`)
and one unit, `test_document_tree.py`, which cites its Lean file. Together they
moved the file count by three and every other row by three. Phase 105 added one
Lean file (`AstIndex.lean`) and one unit, `test_ast_index.py`, which cites its
Lean file, so every row moved by one. Phase 106 added one Lean file
(`Derivations.lean`) and one unit, `test_derivation.py`, which reaches the
router and cites its Lean file, so every row moved by one again. Phase 107
added one Lean file (`DerivationsTwo.lean`) and one unit,
`test_derivation_two.py`, which reaches the router and cites its Lean file,
and every row moved by one once more. Phase 108 added one Lean file
(`CubicTrig.lean`) and one unit, `test_cubic_trig.py`, which reaches the
router and cites its Lean file, and every row moved by one again. The
sharpening pass after Phase 108 added no Lean file and one unit,
`test_sharpening.py`, which reaches the router (and through it the Lean
files its frames cite), so every row but the file count moved by one.
Phases 109 and 110 together added three Lean files (`QuarticResolvent.lean`,
`SignFactor.lean`, `StrayBlind.lean`) and two units, `test_route_choices.py`,
which reaches the router, and `test_stray_blind.py`, which reads its own Lean
file. The unit count and the any-Lean-file row moved by two, and the median,
the worst single file and the glob row by one each. Phase 113 added one Lean
file (`FrobeniusRadicals.lean`) and one unit, `test_frobenius_radical.py`,
which reaches the router and cites its Lean file, so every row moved by one.
Phases 114 and 115 added one Lean file each (`PrimitiveRadicals.lean`,
`ComposedRadicals.lean`) and one unit each, `test_primitive_radical.py` and
`test_composed_radical.py`, which reach the router and cite their Lean files,
so every row moved by two — and the median passed half of the any-Lean-file
row for the first time (§5k). Phase 116 added one Lean file
(`PrimitiveDegree.lean`) and one unit, `test_primitive_degree.py`, which
cites its Lean file but was written to stay below the frames (it checks the
wiring at the branch layer instead), so it does not reach the router: the
unit count, the file count and the any-Lean-file row moved by one, and the
median, the worst single file and the glob row did not move. Phase 117 added one Lean
file (`MetaAnswers.lean`) and one unit, `test_meta_questions.py`, which also
stays below the frames (it reads the evidence layer, `reasoning/meta_evidence.py`),
so the same three rows moved by one and the other three did not; the median
now stands at exactly half the any-Lean-file row, so the recorded excess is
not used. The cost Phase 117 did add is elsewhere: the router now holds the
six studies its meta frames quote, so editing one of them makes about 48
units stale where it used to make two or three
([`META_QUESTIONS_STUDY.md`](META_QUESTIONS_STUDY.md) §6). Phase 118 added
one Lean file (`NonShannon.lean`, which imports `DerivationsTwo.lean`) and
one unit, `test_derivation_three.py`, which stays below the frames too (it
reads the reasoning layer and `runtime/derivation_three_marks.py`): the unit
count, the file count, the any-Lean-file row and the worst single file moved
by one, and the median and the glob row did not. Phase 119 added two Lean
files (`CopyLemma.lean` and `RobinBoth.lean`) and one unit,
`test_derivation_four.py`, which is held below the router in what it asks but
imports `runtime/derivation_four_frames.py`, and through it takes the whole
development: the file count moved by two and every other row by one.
Phase 120 added one Lean file (`ExplanationAnchors.lean`) and one unit,
`test_explanations.py`, which stays below the frames (it reads
`reasoning/explanation_anchors.py` and the nuclide register): the unit count,
the file count and the any-Lean-file row moved by one, and the median, the
worst single file and the glob row did not.
Phase 121 added one Lean file (`ShareSeparation.lean`) and one unit,
`test_share_separation.py`, which reads its own Lean file and the stored
ensembles and does not reach the router: the unit count, the file count and
the any-Lean-file row moved by one, and the median, the worst single file and
the glob row did not.
Phase 122 added one Lean file (`ConfigurationReading.lean`) and one unit,
`test_configuration_reading.py`, which reads its own Lean file and the same
stored ensembles and does not reach the router: again the unit count, the
file count and the any-Lean-file row moved by one, and the other three did
not.
Phase 123 added one Lean file (`LatticeCompletion.lean`) and four units
(`test_hole_census.py`, `test_configuration_classifier.py`,
`test_empty_rungs.py`, `test_frozen_path.py`): the unit count and the
any-Lean-file row moved by four, the file count by one and the worst single
file by three (147); the median and the glob row did not.
Phase 124 added one Lean file (`ProbeBudget.lean`) and one unit,
`test_probe_budget.py`, which reads its own Lean file and the stored
readings and does not reach the router: the unit count, the file count and
the any-Lean-file row moved by one, and the other three did not.
Phase 125 added one Lean file (`OperationsLadder.lean`) and one unit,
`test_operations.py`, which reaches the toolbox and through it the router
and cites its Lean file, so every row moved by one.
Phase 126 added one Lean file (`InertCounter.lean`) and one unit,
`test_inert_counter.py`, which reaches the operations module and through it
the router and cites its Lean file, so every row moved by one.
Phase 127 added one Lean file (`HexRung.lean`) and one unit,
`test_norm256_hex.py`, which reads the Lean corpus and cites its Lean file,
so the suite, file and any-Lean-file rows moved by one.
Phases 128 and 129 added two Lean files (`CellGuard.lean`,
`PlacementGuard.lean`) and two units, `test_cell_guard.py` and
`test_placement_guard.py`, each of which reads its own Lean file and the
stored measurement: the unit count, the file count and the any-Lean-file
row moved by two, and the other three did not.
Phase 130 added one Lean file (`CounterLasso.lean`) and one unit,
`test_counter_lasso.py`, which reaches the operations module and through it
the router and cites its Lean file, so every row moved by one.
Phase 131 added one Lean file (`ConstantBound.lean`) and one unit,
`test_constant_bound.py`, which reaches the operations module through
`counter_lasso.py` and cites its Lean file, so again every row moved by one.
Phase 132 added one Lean file (`AffineOutput.lean`) and one unit,
`test_affine_output.py`, which reaches the operations module and cites its
Lean file, so every row moved by one once more.
Phase 133 added one Lean file (`DesignedSubstrate.lean`) and one unit,
`test_designed_substrate.py`, which reaches the carried fork and cites its
Lean file but does not read the tree with a glob, so the unit count, the
file count, the any-Lean-file row and the worst single file moved by one,
and the median and the glob row did not.
Phase 134 added one Lean file (`ProtectedTag.lean`) and one unit,
`test_carrier_read.py`, which reaches the carrier read and cites its Lean
file without a glob, so the same four rows moved by one and the median and
the glob row did not.
Phase 135 added one Lean file (`ShortestTag.lean`) and one unit,
`test_shortest_tag.py`, and Phase 136 one Lean file (`CertifiedStreams.lean`)
and one unit, `test_connected_two.py`, which reaches the router and the
toolbox's wiring census; together the unit count, the file count, the
any-Lean-file row and the worst single file moved by two, and the median and
the glob row by one (re-measured at Phase 136; Phase 135 left the table
unmoved).
Phase 68 added one unit (`test_reverse_tct_two.py`) that reaches
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
   (`tools lean-mirror`, and its module `mirror.py` under `signoff`) and the `lean-copies-identical`
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

## 5h. The close that had to be run three times

Through Phase 108 a round's close typically took two or three passes of
`signoff --close`, each re-running units that had just passed. Three
couplings did it, and each is cut in Phase 109:

* **The session notes in 51 closures.** `ARISTOTLE_SUMMARY.md` is rewritten
  between sessions and was named by documents that 51 units read, so each
  new session began with 51 stale units. It is now excluded from every unit
  closure except the document checks (`rules.SESSION_NOTES`).
* **The totals a close records, read by the units it signs.** A unit that
  reads rendered regions was signed against documents that quote the suite
  totals, and recording those totals made it stale. Its digest is now taken
  over the *rendered* text with the run-measured regions emptied
  (`rules.rendered_text`, the `rendered` digest mode); `test_corpus`,
  `test_figures` and the `figures` instrument, which exist to check those
  figures, keep the `raw` digest.
* **The document checks in the same pass as what they check.** They ran
  beside the units whose totals they compare, failed until a refresh, and
  the refresh needed every counted unit to have passed. `--close` now runs
  the counted units first, defers the document checks if one fails, runs
  `corpus --refresh` itself when they are owed, and runs them last. A stale
  measurement cache -- the case that made `test_query_escalation` fail
  inside a close after `evaluation/cases.py` changed -- is re-taken in a
  stage 0 before anything runs.

The ledger schema moved to 5 for the new digest modes, so the Phase 109 close
re-ran everything once; from then on a close is one pass unless a counted
unit genuinely fails.

## 5i. The two edits every round makes, and the round that was never closed

Phase 111 measured what a close pays for the two documents *every* round
edits — the status document and the plan — and what the next session pays
before it has done anything. Both were larger than they needed to be, and
for two reasons the earlier cuts had missed:

* **The ledger's own rules read as a docstring reader.** A closure keeps the
  documents its docstrings mention only when some module of it *reads*
  docstrings. The test was a substring search for `__doc__` and
  `get_docstring`, and `signoff/rules.py` spells both in its own prose and in
  the test itself. Nearly every derivation imports it through `code_store`,
  so every docstring mention of `STATUS.md` or `MASTER_PLAN.md` counted. The
  test now reads the syntax tree and asks whether the name is *used*
  (`rules._uses_docstrings`). Measured with `signoff --impact` before and
  after, on the same tree:

  | edit | units before | units after |
  |---|---|---|
  | `STATUS.md`, by name | 57 (5,604 s serial) | 5 (1,667 s) |
  | `MASTER_PLAN.md`, by name | 63 (5,627 s) | 16 (2,147 s) |
  | `PROJECT_DIRECTIVES.md` | 63 | 63 — named in code by `reasoning/directives.py`, a real read |
  | a usual round: both, plus the document address book they move | 64 | 62 |

  The last row is the one a close pays, and it barely moved. **The floor is
  the document address book**: any document edit makes the refresh rewrite
  `corpus/_data/document_addresses.json` (its stored corpus digest changes
  even when no address does), and 54 units hold that file, because the
  toolbox reaches `reasoning/native_parity.py`, `reasoning/native_words.py`
  and `corpus/address.py`, all of which name it. Measured: a one-line edit to
  `WHITEBOARD.md` after a finished close cost 1,636 s of `signoff --close` on
  8 jobs. Removing a single path does not help — 53 of the 54 still reach
  the book with `native_words` taken out — so the cut is either a digest that
  reads the addresses rather than the file's bytes, or a toolbox whose reach
  into the document corpus is declared rather than imported. It is left as a
  To-Do line, measured.

* **The session note was still in the corpus.** Phase 109 took
  `ARISTOTLE_SUMMARY.md` out of the counted closures but left it in the
  corpus and in the closure of the two document checks. It is rewritten after
  the session that closed a round has ended, so the next session found the
  address book, `DIGEST.md`, `test_corpus` and `test_figures` stale before it
  had changed anything: the pick-up `corpus --check` failed and took two
  minutes instead of three seconds, and `signoff --verify` reported 156 of 158.
  It is now outside the corpus walk (`inventory.SESSION_NOTES`) and in no
  closure at all.

* **What reads the whole corpus now depends on the whole corpus.** Cutting
  the false docstring reader exposed what it had been hiding: the two
  document checks and the documents gate read every document by walking the
  corpus, but their closures held only the documents some module *named* —
  most of them while every docstring counted, 72 and 62 of 147 for
  `test_corpus` and `test_figures` and 22 for the gate once it did not. A
  document nothing names could then move without re-running the check whose
  subject it is. They now hold every written document
  (`rules.written_documents`, the set the corpus walk reads), 147 of 147.
  It costs nothing in practice: every round edits a document those checks
  already held, so they re-run at every close anyway.

The third cut is in the documents rather than the code: the counts that
broke earlier closes when quoted by hand — report subjects, registers, Lean
files, query kinds, CLI cases, and the Lean declaration count — are inline
figures in every state document that quotes them, so `corpus --refresh`
keeps them and no close has to find them. The resulting close, step by step
with its cost, is [`ITERATE.md`](../ITERATE.md) §4.

## 5j. The address book's reach, cut where it was imported

Phase 114 took the To-Do line §5i left: the 54 units (56 by the time the
round started) that held `corpus/_data/document_addresses.json`. The line
named two ways out — digest the addresses rather than the file's bytes, or
cut the toolbox's reach. The first would not have helped: every document edit
moves the lexical vectors of the sections it touched, so the addresses move
with the bytes. The second was measured unit by unit, by walking each
unit's imports breadth-first to the first module that names the book, and it
was almost all one path:

| first module reached | units | what the caller actually needed |
|---|---|---|
| `native_parity` through `runtime/toolbox.py` | 40 | the ledger and the read-back check, which read no document |
| `native_words` through `reasoning/retrieval.py` | 5 | the Lean-corpus word ranking, which reads no document (one of the five, the corpus resample study, also reaches the book directly) |
| `native_parity` through `ast_index.py` → `corpus_resample.py` | 1 first, and nearly all of the toolbox 40 once that path was cut (through the question frames) | the exact sign test, a five-line function |
| `tools.py`, `corpus/render.py`, the corpus itself, the document studies | 10 | the book itself, or the instruments that measure it |

None of the first three reads the book; each imported a module that also
holds a document measurement. So the cut is three moves, each re-exported
unchanged from where it was:

* `reasoning/golay_words.py` — the Golay words of tokens, the rankings and
  the Lean-corpus ranking out of `native_words.py`; the toolbox's
  `native words` tool and the retrieval layer's word schemes import it;
* `reasoning/native_ledger.py` — the ledger, the read-back check and the
  toolbox view out of `native_parity.py`; the toolbox's `native parity` tool
  imports it;
* `reasoning/sign_test.py` — the exact two-sided sign test out of
  `corpus_resample.py`; the AST index imports it.

The measurement caches that read the moved code name the new modules in
their sources, so a change to them still re-takes the cache.

Measured with `signoff --impact` on the same tree, before and after:

| edit | units before | units after |
|---|---|---|
| `corpus/_data/document_addresses.json` (what every document edit rewrites) | 56 (4,855 s serial) | 11 (1,576 s serial) |

The eleven that remain are the two document checks, the two native studies,
the corpus resample and document-tree studies, the sandbox planner (which
reaches the renderer), `test_exactness` (which scans every module), and the
three units that import `tools.py` — the instrument CLI, which imports every
study lazily and so reaches the book honestly. `test_signoff` pins the cut:
the planner's, the frames' and the retrieval units' closures must not hold
the book, and the native-words and corpus units' must.

## 5k. The half-line the router's reach crossed

`tests/test_corpus.py` holds the property §5a's table is evidence for: one
Lean file makes stale at most half the units that name any Lean file. Every
unit that reaches the router takes the whole development, because the router
reaches `reasoning/lean_address.py`, and `lean_address.py` walks the tree with
a `*.lean` glob to build the address book (it also serves the stored book,
which is data). So each new frame test moves the median and the any-Lean-file
row by one together, and the half-line by a half; the margin has been
shrinking by a half per frame round. At Phase 115 it ran out: the median is
75 and half of 148 is 74.

What would cut it is the same move §5j made for the document address book:
split the tree walker out of `lean_address.py`, so that the modules on the
answering path, which read only the stored book, stop naming the glob, and
only the units that build the book or digest the tree keep the whole
development. `reasoning/citation_reference.py` names `.lean` only as the
suffix of a temporary file it writes, which the rule reads as a walk; it
imports `lean_address.py` as well, so fixing that alone moves nothing. The
split touches a module most of the suite reaches, so it is a round of its
own, and it is a To-Do line in [`STATUS.md`](../STATUS.md) §2.2. Until then
the test records the excess (`RECORDED_MEDIAN_EXCESS = 1`) rather than
hiding it, and a larger one fails.

Phase 116 met that line from the other side. Its first test file read the
declared questions through the frames, as the radical rounds before it had,
and the median went to 76 against half of 149, an excess of two, which the
test rejected. The router's dependency on the tree is not an
over-approximation that a split would remove: `toolbox._declaration` and
`proof_dependency` call `lean_address.feature_table()` and
`declaration_names()`, which parse the development when asked. So the round
kept its unit below the frames instead — the pure objects the marks read
moved to `reasoning/primitive_degree_groups.py`, and the layer's wiring is
checked at `symbolic_nonlinear.solve_nonlinear`, which the frame calls — and
the end-to-end reading stays with the instrument (`tools primitive-degree`).
The excess is back to one. Serving the router's two Lean lookups from the
stored book is still the cut that would retire the line.

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
**Rebuilding both address books from nothing decodes 15,340 vectors; rebuilding them against the stored books decodes 0.**  The planner's report, one pass over 223 evaluation cases, is quoted by 5 generated blocks and is now taken 0 times per check instead of 5.  593 figures inside sentences, across 32 documents, are emitted rather than typed.
<!-- end generated -->
