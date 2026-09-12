# What a round costs: the rebuild chain, measured and cut

## Tier 0 — the coarse read

**Question.** Everything this repository claims is recomputed from the tree. What does one iteration of that cost, and how much of the cost is work that did not need doing?

**Verdict.** Most of the cost was work repeated on things that had not moved, and a cache keyed on what it is derived from does not repeat it.

**Deciding figure.** Rebuilding both address books from nothing decodes <!--figure:rebuild-decodes-from-nothing-->7,726<!--/figure--> vectors and against the stored books decodes <!--figure:rebuild-decodes-now-->0<!--/figure-->; the planner's report is taken once per change instead of <!--figure:planner-reports-per-check-->5<!--/figure--> times per check.

**Recomputed by.** `glm_universal.corpus.cost.cost_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

Code: [`glm_universal/corpus/cost.py`](../overlay/glm_universal/corpus/cost.py),
[`glm_universal/reasoning/lean_address.py`](../overlay/glm_universal/reasoning/lean_address.py),
[`glm_universal/corpus/address.py`](../overlay/glm_universal/corpus/address.py),
[`glm_universal/derived.py`](../overlay/glm_universal/derived.py),
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
| Lean declarations | 3,187 | 6,010 | 0 | 6,374 |
| corpus sections | 871 | 1,716 | 0 | 1,742 |

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
| evaluation cases per report | 147 |
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
the suite is <!--figure:test-files-->89 test files<!--/figure--> today
```

The markers are HTML comments, so a reader sees only the number. `--refresh`
rewrites the body, `--check` fails when it has drifted, and a marker naming a
figure nothing emits is a reported defect rather than a silent no-op.

<!-- generated: cost-figures -->
19 figures are registered and 25 markers carry them, across 8 documents.  A marker whose text is not what its figure now says is what `--refresh` rewrites and what `--check` fails on.

The registry: `corpus-archive-documents`, `corpus-documents`, `corpus-sections`, `corpus-state-documents`, `evaluation-case-count`, `evaluation-cases`, `lean-declaration-files`, `lean-declarations`, `lean-file-count`, `lean-files`, `planner-reports-per-check`, `query-kinds`, `rebuild-decodes-from-nothing`, `rebuild-decodes-now`, `registers`, `report-subjects`, `suite`, `test-file-count`, `test-files`.
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

## 6. What this does not establish

It does not make anything faster that was not repetition. The measurement cache
is still quadratic in the declarations and still costs about four minutes when
the Lean tree moves; the full test suite is still an hour of work, parallel
across cores rather than shortened. Nothing here changes a claim the system
makes — every number is still recomputed from the tree, and every cache is
still refused when its input has moved. What changed is how often the same
answer is computed twice.

<!-- generated: cost-tier -->
**Rebuilding both address books from nothing decodes 7,726 vectors; rebuilding them against the stored books decodes 0.**  The planner's report, one pass over 147 evaluation cases, is quoted by 5 generated blocks and is now taken 0 times per check instead of 5.  25 figures inside sentences, across 8 documents, are emitted rather than typed.
<!-- end generated -->
