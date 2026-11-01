# The intake items absorbed where they measurably help — what the hypothesis engine, the formula wheels and the next-term reading add to the GLM on ARC, on Rule 30 and on reasoning across domains

## Tier 0 — the coarse read

**Question.** Do the three intake items that were ready for absorption — the Rule 30 study's hypothesis engine (`Rule30_GLM_Study`), the cent compiler's formula wheels (`cent_compiler_v12`) and the wheels bundle's sequence wheel (`glm_wheels_bundle`) — measurably help the GLM on the stored ARC tasks, on Rule 30, and on general reasoning across domains, with nothing answered wrong, when the same questions are put to the GLM with and without them?

**Verdict.** Yes, with two pre-registered marks not met. With the three items wired in, the GLM answers 9 of the 50 stored ARC tasks where it answered 2, answers Rule 30 claims, conjectures about every n, formula-law questions and next-term questions that it refused before, and across thirty questions in five domains answers 23 right where it answered 4, with 0 wrong; but the ARC tasks are a development set, not a held-out one, the answering path reads only 16 of the 39 Rule 30 sentences right (the bar was 20), and one of the 13 negative controls of the next-term battery is answered where it should be refused. The items' Lean was checked standalone; the owner's build has still to confirm it.

**Deciding figure.** 12 of 14 marks (R2, S2 missed). ARC: 9 of 50 tasks right, 0 wrong (2 before); across domains 23 right, 0 wrong of 30 (4 before); Rule 30 on the answering path 16 right, 0 wrong of 39 (0 before); formula laws 63 of 64 licensed, 0 of 51 not-a-laws; next terms 27 right, 0 wrong of 45 (5 before), 12 of 13 controls refused.

**Recomputed by.** `glm_universal.reasoning.intake_capability_study.intake_capability_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 1 November 2026 (Phase 186, directive D22). The marks of §3 were written on 1 November 2026 after the tools of §1 were built and spot-checked on some of these questions, and before the study module's first run; §5 is what came out, and §5.1 records the three corrections made after the first run (none changed a mark).*

**Faculty (D15).** Derive: the GLM now answers Rule 30 claims, conjectures about every `n`, formula-law questions and next-term questions with the reason for each answer (a ring of the engine's wheel, a counterexample, an explicit rational combination of a wheel's axioms, the one stored sequence that runs past the terms), and refuses where those reasons do not exist.

## 0. What this document is

The owner asked on 1 November 2026 for the intake studies set up ready for
absorption to be taken into the GLM *if they have a function that measurably
assists the GLM's abilities*, with a look at whether they help with ARC-AGI,
with Rule 30 puzzles and with general reasoning across domains, and for the
full Lean build if it could be done here.

It could not: the round's machine has neither the project's Lean toolchain
nor network access, so `scripts/rebuild_lean.sh` cannot be run. The owner
was asked what to do and answered: *"Absorb the ones that measurably help
now, based on your measurements and standalone Lean check; record that my own
rebuild_lean.sh run still has to confirm them."* This study is the
measurement that decision rests on, and §6 is the standalone Lean check.

Three items in `source_material/ToDo/` were ready (Lean written, tested,
with a function the GLM did not have):

* **`Rule30_GLM_Study`** — the Rule 30 study's hypothesis engine
  (`glm_engine/hypothesis_engine.py`, version 18): a wheel of three rings
  (*knows*, *thinks true*, *doesn't know*) that escalates a claim through
  scales of exact checks and consults a ledger of Lean results, with three
  domains (Rule 30, a general domain of classic traps, and ARC).
* **`cent_compiler_v12`** — fifteen sound formula wheels (W16–W25, W28, W29,
  W32–W34), installed provisionally on 31 October 2026
  ([`CENT_WHEELS_STUDY.md`](CENT_WHEELS_STUDY.md)), whose derivability answers
  were not reachable from the GLM's answering path.
* **`glm_wheels_bundle`** — the sequence wheel (installed provisionally on
  31 October 2026), which identified a sequence but did not continue one.

## 1. What was built (Phase 186)

* **`reasoning/hypothesis_engine.py`** — the engine, ported into the package:
  exact throughout, with a work-bounded evaluator (`safe_predicate`,
  `WorkBound`) in place of the original's unbounded `eval`, so a claim can no
  longer run away; its XOR sites registered with the combiner.
* **`reasoning/hypothesis_tools.py`** — what the GLM asks of it:
  `rule30_text` (the centre column, a claim, the battery), `conjecture_text`
  (a claim about every `n`, escalated scale by scale within a work budget,
  stopping where the budget runs out and saying so), `arc_plan` (the engine's
  plan search on one ARC test input) and `arc_combined_text`.
* **`tool rule30`**, **`tool conjecture`**, **`tool derive`** in
  `runtime/toolbox.py`, each with English routes (*"in rule 30, ..."*, *"is
  n^2 + n + 41 prime for every n"*, *"is force = mass * acceleration a law"*);
  **`tool arc`** now asks the plan search on the test inputs the colour solver
  refuses, and keeps every answer the colour solver gives.
* **`wheels/derive_query.py`** — `derive_text`: a law question asked of each
  of the thirty formula wheels on its own (the fifteen registry wheels and the
  fifteen cent wheels), answered *derivable* with the explicit rational
  combination, or *not derivable*.
* **The `next` reading of the `sequence` kind** (`wheels/sequence_query.py`)
  — *"what comes next in 1, 1, 2, 5, 14, 42"*: answered only when the one
  stored sequence whose terms start with the claim runs past it, and refused
  at a junction (two stored sequences that agree on the claim and part after
  it, under either indexing convention); its battery is
  `wheels/next_term_battery.py` (45 questions and 13 negative controls,
  fixed before the reading was written).
* **`reasoning/intake_capability_study.py`** and `tools intake-capability`
  — this study.
* **Standalone Lean** in `src/lean/RequestProject/GLM/IntakeChecks/` (§6).
* **The intake ledger**: `absorb-ahead` (absorb an item, or its staged and
  provisional parts, ahead of the build record, by the owner's decision, on
  its measurements and a standalone Lean check) and `confirm-build` (the
  owner's build record confirms it).

## 2. The switch: the GLM without Phase 186

*Without Phase 186* is the same code with three things taken out
(`without_phase186` in `reasoning/intake_capability_study.py`): the tools
`rule30`, `conjecture` and `derive` and their English routes; the hypothesis
engine behind `tool arc` (so `tool arc` is the colour solver alone, the GLM
before this round); and the `next` reading of the `sequence` kind. Everything
else — the router, the other tools, the wheels themselves — is identical, so
a difference is the difference the three items make.

## 3. The marks

Written before the study module's first run; they are not changed below.

| mark | the bar |
|---|---|
| **A1** | ARC with the plan search: 0 wrong test grids on the fifty tasks |
| **A2** | ARC with the plan search: at least 7 tasks right (the colour solver alone: 2; the development figure of the plan search, 9, was known) |
| **A3** | ARC: the plan search changes no answer the colour solver gives, and `tool arc` reports for every task the status computed here |
| **R1** | the Rule 30 battery of 39 claims: with the ledger 39 right, 0 wrong, 0 overclaimed; without the ledger 0 wrong and 0 overclaimed (it abstains instead) |
| **R2** | Rule 30 on the answering path, the 39 sentences worded *"in rule 30, ..."*: without Phase 186 none answered; with it 0 wrong and at least 20 answered right |
| **R3** | the centre column: `tool rule30 centre 1000` equals a plain simulation written in the study, and its first 64 cells the list of `RuleThirtyBits.lean` |
| **G1** | the engine's general domain: with the ledger 10 right and 0 wrong; without it 0 wrong and 0 overclaimed |
| **G2** | twelve conjectures about every `n`: 0 wrong; every false one refuted with a counterexample that is one; no surviving one called proved |
| **D1** | `tool derive` on the 115 questions of [`CENT_WHEELS_STUDY.md`](CENT_WHEELS_STUDY.md) §4: at least 56 of the 64 laws licensed and 0 of the 51 not-a-laws, the fifteen registry wheels alone licensing at most 4 laws |
| **S1** | next terms: 0 wrong on the 45 positives, and more right than without the `next` reading |
| **S2** | next terms: every one of the 13 negative controls refused |
| **X1** | thirty questions across five domains: 0 wrong with Phase 186 |
| **X2** | across domains: at least 15 more right with Phase 186 than without |
| **L1** | the four standalone Lean files: present, every theorem the study names stated, no `sorry`, each imported by `AxiomAuditAll.lean` |

**Grading.** A test grid is *right* when it equals the stored output, which
no solver sees. A Rule 30 or general claim is *right* when the verdict
(true / false / not settled) matches its truth — *not settled* is right for
an open claim, and an abstention, not a wrong answer, for a settled one; a
claim called true or false while open is *overclaimed*. A false conjecture is
right only when it is refuted with a counterexample the study's own plain
predicate confirms. A next-term answer is right when it states the expected
term; a negative control is right when refused. An answering-path question is
*refused* when the GLM does not answer it.

**The thirty questions across domains** (`CROSS_DOMAIN`): six each in Rule 30
(the centre column twice, three settled claims, one open claim), number
theory (six conjectures, four false), physics (six law questions, two not
laws), sequences (four to continue, two to refuse), and ARC (the first six
stored tasks in name order — chosen by that rule, not by outcome). The
expected outcomes are computed in the study: the centre column by a plain
simulation, the next terms by closed forms, the truths by theorem or least
counterexample.

## 4. The development-set caveat

*The fifty stored ARC tasks (`arc_agi_17`) are a development set, not a
held-out one.* The engine's plan search was written by the intake item's
author against these same tasks, so the ARC figures say what the GLM now
answers on them, not how it would do on unseen tasks. The engine's own
synthetic ARC families (seed 18; 50 puzzles) are reported beside them for
information only: 4 right with the base provisions, 46 with the provisions
the engine asks for, against 15 and 12 for random provision sets of the same
size.

## 5. The measurement (1 November 2026)

`PYTHONPATH=src python3 -m glm_universal.tools intake-capability --write`
(about a minute and a half; stored in
`reasoning/_data/intake_capability_study.json`).

| mark | result | figure |
|---|---|---|
| **A1** | met | 0 wrong of 53 test grids |
| **A2** | met | 9 of 50 tasks right: 1e0a9b12, 45737921, 484b58aa, 662c240a, 7953d61e, ae58858e, b91ae062, bc4146bd, d631b094 (the colour solver alone: 2, 1e0a9b12 and ae58858e — the two the vision stack solves) |
| **A3** | met | the colour solver's 2 answers unchanged; `tool arc` agrees with the study on all 50 tasks |
| **R1** | met | with the ledger 39 right, 0 wrong, 0 overclaimed; without it 24 right, 0 wrong, 15 abstained |
| **R2** | missed | without Phase 186 0 of 39 answered; with it 16 right, 0 wrong, 23 refused (bar: at least 20 right) |
| **R3** | met | 481 black cells in the first 1000; equal to the plain simulation, and the first 64 to the list of `RuleThirtyBits.lean` |
| **G1** | met | with the ledger 10 right, 0 wrong; without it 6 right, 0 wrong, 4 abstained |
| **G2** | met | 12 of 12 right: the 7 false ones refuted at their least counterexample (n = 40, 41, 4, 3, 5, 25, 15), the 5 true ones left *thinks true*, none called proved |
| **D1** | met | 63 of 64 laws and 0 of 51 not-a-laws licensed; the fifteen registry wheels alone: 1 law |
| **S1** | met | 27 right, 0 wrong, 18 refused of 45; without the `next` reading 5 right |
| **S2** | missed | 12 of 13 controls refused; C08 (*1, 2, 4, 8, 16*) is answered 32 |
| **X1** | met | 0 wrong of 30 |
| **X2** | met | 23 right with Phase 186, 4 without: 19 more |
| **L1** | met | 4 of 4 files present, 18 of 18 named theorems stated, no `sorry`, each imported by `AxiomAuditAll.lean` |

**12 of 14 marks met; R2 and S2 missed.**

Across the five domains (right without → right with; 0 wrong in every cell):
Rule 30 1 → 6, number theory 0 → 6, physics 0 → 6, sequences 2 → 4, ARC 1 → 1.
The one Rule 30 question right without Phase 186 is the open claim, which is
right when refused; the two sequence questions right without it are the two
to refuse. The plan search's ARC gains are not among the first six tasks, so
the ARC row does not move there.

**R2 missed.** The Rule 30 recognisers of the engine read 17 of the 39
battery sentences (the rest are checked inside the engine's battery, where R1
counts them, but are not read from a question). `tool rule30 claim` is right
on all 17; the answering path answers 16 of them right — the seventeenth
(*the least periods of the left diagonals are unbounded*) is in the ring
*doesn't know*, and the answering path keeps a tool's reply only when the
tool answers, so it is refused, which is not wrong. The bar of 20 was above
what the recognisers can read; it was set without counting them, and it is
left as set.

**S2 missed.** Moser's circle regions (1, 2, 4, 8, 16, 31) are not on the
sequence wheel, so the junction rule sees no junction after *1, 2, 4, 8, 16*
and the powers of 2 continue it with 32. That is a genuine limit of a
junction rule — it sees only the sequences the wheel holds — and it is
recorded in `wheels/next_term_battery.py` and in the answer's own provisional
note.

The verdict, in full: Yes, with two pre-registered marks not met. With the three items wired in, the GLM answers 9 of the 50 stored ARC tasks where it answered 2, answers Rule 30 claims, conjectures about every n, formula-law questions and next-term questions that it refused before, and across thirty questions in five domains answers 23 right where it answered 4, with 0 wrong; but the ARC tasks are a development set, not a held-out one, the answering path reads only 16 of the 39 Rule 30 sentences right (the bar was 20), and one of the 13 negative controls of the next-term battery is answered where it should be refused. The items' Lean was checked standalone; the owner's build has still to confirm it.

### 5.1 After the first run

No mark was changed. Three things were corrected after the first run. The
study's reading of a verdict expected the claim in single quotes, so two Rule
30 sentences containing an apostrophe (quoted in double quotes in the reply)
were read as giving no verdict; corrected, the answering-path count of R2 went
from 14 right to 16 right, and R2 stays missed. The Lean mark, written `L` at
first, was renamed L1 so that the study ledger reads it as a mark; its test
is unchanged. Third, the engine drew its synthetic ARC families and its
random-provision control from Python's `random` module, which the
blueprint's Universal Binary Principle bans from the six core sub-packages:
the evaluation's frozen-path re-take found `report blueprint` moved from 26
to 25 confirmed claims. The engine now draws from an exact integer generator
of its own (`ExactDraw`), and the blueprint is back at 26. The synthetic grids
are therefore drawn differently, and the information-only synthetic figures
of §4 moved (from 6 and 47 right to 4 and 46; the controls from 12 and 14 to
15 and 12); the stored ARC tasks, the Rule 30 battery and every mark read the
same figures as before.

### 5.2 The absorption decision

The owner's words of 1 November 2026 were the rule: *absorb the ones that
measurably help now*. Two of the three items had already been measured and
accepted against criteria of their own studies, and were installed
provisionally only because the owner's build had not run:
`cent_compiler_v12` on [`CENT_WHEELS_STUDY.md`](CENT_WHEELS_STUDY.md) §8 and
`glm_wheels_bundle` on [`INTEGER_WHEEL_STUDY.md`](INTEGER_WHEEL_STUDY.md) §7.
This study adds what their wheels now do on the answering path — D1 for the
cent wheels behind `tool derive`, S1 and S2 for the sequence wheel's `next`
reading — and their acceptances stand as recorded. The hypothesis engine of
`Rule30_GLM_Study` had no measurement on GLM questions; its acceptance rests
on this study, against this criterion, which makes the owner's words concrete
and was written after the measurement of §5 (the reader should weigh that):

**Absorption criterion.** The hypothesis engine of `Rule30_GLM_Study` is absorbed when, wired in, the GLM answers right questions it refused without it on the stored ARC tasks, on Rule 30 or on conjectures about every n, with 0 wrong answers there (A1, R1, G1, G2), and its standalone Lean check holds (L1).

**Result for the hypothesis engine.** With the hypothesis engine the GLM answers 9 of the 50 stored ARC tasks right (2 without it), 16 of the 39 Rule 30 sentences right on the answering path (0 without it) and 12 of 12 conjectures right, with 0 wrong; the Rule 30 battery is 39 right with the ledger and the general domain 10 right.

The marks that carry the help are A1, A2, A3, R1, R3, G1, G2, X1 and L1, all
met; R2 measures how much of the Rule 30 battery the answering path reads, and
its miss is a shortfall of coverage, not a wrong answer. S2 concerns the
sequence wheel's `next` reading, not the engine.

## 6. Lean: the standalone check

The round's machine cannot run the project's Lean build, so the finite
claims the absorbed functions rest on were written as four standalone files
in `src/lean/RequestProject/GLM/IntakeChecks/` and checked on their own
(with Lean 4.34 and Mathlib, outside the project's build; the axioms used are
only the standard three):

* `IntakeChecks/RuleThirtyBits.lean` — Rule 30's local rule is Wolfram's
  table, the engine's bit-level step is that rule, and the first 64 centre
  cells are the list R3 reads (35 of them black).
* `IntakeChecks/SporadicOrderCheck.lean` — the 26 sporadic group orders the
  wheels bundle's Monster Wheel answers from, each equal to its prime
  factorisation, and distinct (so an order names at most one group).
* `IntakeChecks/NextTerm.lean` — the next-term rule: an answer is the next term
  of every stored sequence that begins with the claim, and of at least one;
  two stored sequences that begin with the claim and part after it force a
  refusal; the Catalan and Fibonacci terms of the wheel against Mathlib's own
  definitions.
* `IntakeChecks/Derivability.lean` — derivability as membership of the
  rational span of a wheel's axioms: an explicit rational combination proves
  it, a separating linear functional refutes it, with one instance of each.

Each is imported by `AxiomAuditAll.lean`. **The owner's
`scripts/rebuild_lean.sh` has still to confirm them** inside the project's
build (Lean v4.28). Until it does, the intake ledger records each item as
*absorbed ahead of the build*, with `confirm-build` as its next step, and the
register of provisional families (`wheels/_data/provisional.json`) lists it,
so every answer resting on an absorbed module or wheel ends with the
register's note saying so.

## 7. What follows

* The owner runs `scripts/rebuild_lean.sh`; when its build record verifies the
  `IntakeChecks` files, `python3 -m glm_universal.intake confirm-build <id>`
  for `Rule30_GLM_Study`, `cent_compiler_v12` and `glm_wheels_bundle`.
* R2: more of the battery's sentences read by the recognisers (the right
  diagonals, the eventually-white diagonals below a bound, the centre column
  not eventually constant) — a new measurement, with a new mark.
* S2: a junction rule cannot see a sequence the wheel does not hold; more
  sequences on the wheel narrow the gap, never close it.
* ARC: a held-out set of tasks the plan search was not written against, before
  any claim about ARC beyond these fifty.

Tests: `tests/test_intake_capability_study.py`,
`tests/test_hypothesis_engine.py`, `tests/test_hypothesis_tools.py`,
`tests/test_derive_query.py`, `tests/test_sequence_next.py`.
