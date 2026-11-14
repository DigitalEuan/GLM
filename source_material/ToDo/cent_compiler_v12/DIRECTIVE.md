# DIRECTIVE — cent transfer compiler

**Status:** active. Adopted 2026-11-12; reviewed 2026-11-12.
**Authority:** this file owns the objective, binding rules, work order and
scoreboard. Nothing else may declare "what comes next."
**Execution state:** [`WORKFLOW.md`](WORKFLOW.md).
**Live gate count:** the statistics row in [`README.md`](README.md); this file
does not freeze a number that changes with every test.

**ID convention:** D1–D7 are directive work-order items. Older external-evidence
identifiers from the ledgers are written `EXT-D5` and `EXT-D10x` so they are not
confused with this work order.

---

## 1. Objective

> Build a machine that **originates** cross-domain analogies, states exactly
> what survives the move, and proves a computational target is better for
> having used one. Physical realization is a downstream backend.

Three verbs, in order: **originate → bound → benefit**. The compiler itself is
the first-class computational target: a transfer that cannot be measured on the
compiler is not yet a result.

The directive is satisfied only when a generated analogy is bounded by a
declared mapping, executed on a named target, and judged by evidence that could
have failed. A plausible card, a green check count or a target that reproduces
its own declaration is not enough.

---

## 2. Current state

D1–D7 are complete and gated. The transfer layer now has:

- provenance-labelled retrieval over every mechanism card, with a permanent
  constant-score sabotage test;
- executable `check`/`apply` mapping operators and generated Δ cards;
- source routes and independent `glm-reference` adapters for `exp`, `log`,
  `mult`, `div`, `reciprocal` and three-level `sign`;
- two adopted compiler self-transfers with independent-oracle certificates and
  exercised rollbacks;
- witness-backed Tier-D negatives and derived test obligations;
- a bounded, dated retrodictive holdout with an explicit negative control;
- a declared-operation trial wheel: ten operation contracts, all ten
  testable, with `sign` covered by the threshold comparator;
- a knowledge atlas for addressed documentation parts and stitches.

There is **no open D-item**. The remaining gaps in
[`docs/CURRENT_SCOPE.md`](docs/CURRENT_SCOPE.md) are evidence gaps, not
authorized work. A new item enters this directive only when it is written as a
D8 with its own gate and kill criterion and the owner accepts the trade.

---

## 3. Why this directive exists

At adoption on 2026-11-12, five defects made the old capability claims
unfalsifiable:

1. **Retrieval was a whitelist.** `supported_operations` filtered candidates
   before scoring, so the label was also the filter.
2. **Evaluation was sabotage-invariant.** Replacing the score with a constant
   produced the same headline numbers.
3. **Negative controls defended the whitelist.** Two controls called real
   `exp`/`log` transfers false because the card declared only `sqrt`.
4. **Mapping operators were prose.** There was no executable `check`/`apply`,
   so Τ had never transformed anything.
5. **The gate punished origination.** A newly discovered correct transfer was
   counted as a false positive unless the corpus was edited in lockstep.

D1 repaired the evaluation, D2 made Τ executable, D3 recovered the suppressed
operations, D4 made the compiler a target, D5 generated witness-backed
negatives, and D6 measured a bounded retrodictive holdout. The historical
detail and the pre-fix numbers are in
[`docs/TRANSFER_COMPILER_OBJECTIVE.md`](docs/TRANSFER_COMPILER_OBJECTIVE.md) §7
and the completion records in [`WORKFLOW.md`](WORKFLOW.md). The current tests
that hold the repairs in place are:

```bash
python3 tests/test_evaluation_sabotage.py
python3 tests/test_ablation.py
python3 tests/test_log_domain.py
python3 tests/test_self_target.py
python3 tests/test_refutation.py
python3 tests/test_holdout.py
```

---

## 4. Binding rules

These override any conflicting guardrail elsewhere in the repository.

**R1 — Invent hypotheses; never invent evidence.**
Generation is required to invent: every analogy is a hypothesis until tested.
Hypotheses carry evidence level `speculative` and are never counted as
capability. Evidence, parameters, measurements and provenance remain forbidden
to invent. **Be liberal in what you propose; be conservative in what you
certify.** A precision filter must never be applied at the recall stage.

**R2 — Μ, Τ and ∆ are different objects and must be stored separately.**
- **Μ** — substrate-independent principle. Target count: ~5, not 8.
- **Τ** — executable mapping operator with a checkable precondition.
- **∆** — domain interpretation, **generated** as `closure(Μ × Τ)`.

`kcl-conservation`, `fluid-continuity` and `opamp-summing` have identical
structural signatures. They are one Μ in three ∆. `supported_operations` is a
derived validation property, never an authored retrieval gate.

**R3 — No declaration may be both the filter and the label.**
For every headline metric, the candidate set must be produced by a process that
does not read the ground truth. Replace the component the metric claims to
measure with a random or constant function; if the metric does not degrade, the
metric is void. This test is mandatory and permanent.

**R4 — Every transfer states a benefit or explicitly claims none.**
"The transfer computes the right answer" is not a benefit. Each certificate
carries either a measured utility delta against a named non-analogical baseline,
or `utility: none-claimed`. No transfer is reported as useful without the
former.

**R5 — Analogy-derived code never sits on the certificate path.**
Any adopted transfer is paired with an independent oracle; certificates are
issued by the oracle only. Adoption is flagged, reversible and recorded. One
bad analogy must not be able to corrupt the evidence layer.

---

## 5. Work order

D1–D7 are complete. The table is the contract, not a progress narrative;
completion records are in [`WORKFLOW.md`](WORKFLOW.md).

| Item | Status | Gate result |
|---|---|---|
| **D1 — falsifiable evaluation** | Complete | Constant scoring degrades recall; sabotage suite permanent |
| **D2 — split Μ/∆; executable Τ** | Complete | Generated cards rebuilt; four certificates byte-identical |
| **D3 — recover five operations** | Complete | `exp`, `log`, `mult`, `div`, `reciprocal` pass fixed vectors inside `1/10000` |
| **D4 — compiler as target** | Complete | Two adopted self-transfers; `32/152` → `152/152`; `4/12` → `12/12`; rollback exercised |
| **D5 — refutation** | Complete | 8 generated negatives exceed 6 hand-declared; 10 derived obligations |
| **D6 — retrodictive holdout** | Complete, bounded | 5/5 rank-one positives; one declared false positive; one excluded; strict negative control refuses |
| **D7 — recover sign** | Complete | Threshold comparator ranks first; exact reference adapter passes negative, zero and positive vectors; wheel 10/10 |

**Adding work.** A new item must be written here as **D8**, with a concrete
question, a falsifiable gate, a kill criterion and the evidence it would
retire. Do not add a card, route or document merely to fill a row. Do not start
D8 because it is interesting; start it because it closes a named gap in
`CURRENT_SCOPE.md`.

**Closing work.** Every item closes with the gate command and exit status, the
before/after measurement including regressions, which kill criterion fired (if
any), and what remains blocked. A check count alone is not a close.

---

## 6. Scoreboard

The six numbers below are the capability signal. The canonical test gate is a
hygiene metric, not progress on these six.

| # | Metric | Now | Target |
|---|---|---:|---|
| 1 | **Origination rate** — transfers whose Μ–∆ pairing was not hand-authored | 1/9 (D4 self-transfer; D7 is hand-authored and does not improve this metric) | ≥3 |
| 2 | **Sabotage sensitivity** — each headline metric degrades when the component it claims to measure is randomized | 4/4 retrieval-side (D1) | all |
| 3 | **Ablation recall** — deleted cards regenerated and re-certified | 3/3 generated Δ cards; 4/4 KCL certificates identical | ≥2 |
| 4 | **Generated negatives** — with witness proofs | 8 (against 6 hand-declared) | > hand-declared |
| 5 | **Utility deltas measured** — adopted transfers with a baseline comparison | 2 adopted | ≥1 |
| 6 | **Human declarations per transfer** — authoring cost trend | 1 card + 1 adapter + 1 vector set | falling |

Report **identity-based** transfers (`exp(½ log x) = √x`: trivial mathematics,
substantive physics) separately from **structure-based** transfers
(Bresenham ↔ delta-sigma: substantive mathematics). Eight transfers is not
eight analogies.

**D6 is reported separately:** 5/5 rank-one retrodictive recall, one declared
false-positive candidate, one excluded candidate and a strict negative control
that reports `no_licensed_source` and one coverage miss. It is not added to the
production `1/8` origination count; the corpus is small and hand-declared.

---

## 7. Stop doing

- **Stop adding mechanism cards to fill rows.** A card you can regenerate is
  worth more than a card you can list.
- **Stop treating refusal as a terminal state.** Every refusal names its
  unblock and its owner. T1/T3 are queues, not filing cabinets.
- **Stop reconciling status by hand.** `DIRECTIVE.md` owns priority;
  `README.md` owns the live gate count; `WORKFLOW.md` owns execution state;
  `CURRENT_SCOPE.md` owns the gap ledger. Link, do not restate.
- **Stop counting checks as progress.** The gate is hygiene. The scoreboard is
  the capability record.
- **Stop quoting 10/10 recall.** It is a historical artifact of the old
  evaluation, not a capability result.
- **Stop adding a document for a status that already has an owner.** Use
  `cent knowledge find` and `cent knowledge stitch`.

---

## 8. Document authority

| File | Owns | Must not contain |
|---|---|---|
| `DIRECTIVE.md` | objective, binding rules, work order, scoreboard | evidence detail, phase history |
| `README.md` | install/quick start, current gate count, public command surface | priority, phase history |
| `WORKFLOW.md` | execution state, task board, completion records | priority beyond the directive, new work |
| `docs/CURRENT_SCOPE.md` | capability boundary, gap ledger | priority, "next" |
| `PHYSICAL_COMPILER_ROADMAP.md` | completed workstream history, blocked-item register | priority, "next", an active roadmap |
| `docs/TRANSFER_COMPILER_OBJECTIVE.md` | schemas, contracts, phase history | current status |
| `docs/KNOWLEDGE_ATLAS.md` | part addresses, duplicate detection, stitching rules | project status |
| `applications/README.md` | shared legacy show-work parts | current transfer status |

One owner per question. Any claim appearing in two files with different values
is a gate failure. Addressed document parts make the owning section findable;
they do not create a second authority.

---

## 9. Owner decisions

The 2026-11-12 owner direction was **test and follow the best application based
on results**. It resolved the three adoption questions:

1. **GLM status:** audit-only, narrow external probe; `cent-self` is the primary
   computational target. Promote GLM only if a measured utility delta beats its
   named baseline and the independent oracle confirms it.
2. **D3 scope:** in scope and completed. Results, not card count, decided which
   operations survived the declared tolerance.
3. **D1 regression:** accepted. The old 10/10 headline is withdrawn; the worse
   honest baseline is published.

No owner decision is currently open. A new decision belongs in this section
with its date and its effect on the work order.

---

## 10. Working contract

**Gate.** Run the full gate before claiming a change is finished:

```bash
python3 tests/run_all.py
```

Use the focused suite for the area being changed; the full gate is the final
check. Do not weaken an assertion or change a declared expectation to make a
suite pass.

**Environment.** The package uses only the Python standard library except
`numpy`, which is required by the legacy delta-sigma simulator and its tests.
Install the declared dependency with:

```bash
python3 -m pip install -r requirements.txt
```

**Documentation.** Read [`docs/README.md`](docs/README.md) and
[`docs/KNOWLEDGE_ATLAS.md`](docs/KNOWLEDGE_ATLAS.md). A new claim goes in the
owning document; cross-cutting reading is a stitch. A live gate count belongs
in `README.md`, never in a copied status line.

**Evidence.** A `target-simulated` certificate is not a measured device. A
proposal is not a fabricated device. A text match is not a graph proof. A
declared bridge is not an axiom proof. Preserve those distinctions in output,
tests and prose.

---

## Appendix — supporting files

- [`review/refuter_demo.py`](review/refuter_demo.py) — runnable Tier-D
  refutation demonstration used as the D5 working specification.
- [`examples/transfer/README.md`](examples/transfer/README.md) — current
  proposal bundles and evaluation payload.
- [`examples/holdout/README.md`](examples/holdout/README.md) — D6 frozen
  retrodictive corpus and stated limitations.
- [`examples/refutation/negatives.json`](examples/refutation/negatives.json) —
  portable D5 witness ledger.
- [`examples/self/utility.json`](examples/self/utility.json) — portable D4
  self-transfer ledger.

The historical `review/TOP_LEVEL_REVIEW.md`, `review/retrieval_probe.py` and
`repo/cent_compiler/` snapshot named by the adoption draft were not retained.
The tests above are the current regression surface; no task depends on the
missing snapshot.
