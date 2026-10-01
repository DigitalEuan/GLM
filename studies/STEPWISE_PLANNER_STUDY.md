# The stepwise planner: the typed planner as the executive of a chain of steps

## Tier 0 — the coarse read

**Question.** Can the typed planner, which answers one question with one plan, be made the executive of a *chain* of steps — composing its own answers, finding the steps a question does not ask for, and carrying the three columns step by step — without answering anything wrongly?

**Verdict.** Yes: the typed planner is now the executive of a chain of steps, each step asked of the planner or computed exactly and checked in all three columns, and on the declared corpus it answered every compound, goal and narrative question as declared with 0 wrong answers, refusing by name wherever readings or derivations disagree.

**Deciding figure.** 57 of 57 declared questions and 4 of 4 follow-ups as declared, 0 wrong, where the planner alone answers 0 of the 30 compound questions; 43 of 43 chain scripts verified (149 of 149 steps aligned) and 172 of 172 declared mutations rejected; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.stepwise.stepwise_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The typed planner (Phase 58, [`SEMANTIC_PLAN_STUDY.md`](SEMANTIC_PLAN_STUDY.md))
reads a question into typed plans, runs every plan, and answers only when
every licensed plan agrees. Since Phase 63 it is the default path and since
Phase 66 it is the last surface of the one question path (`GLM.py --ask`,
[`CONNECTED_MACHINE_STUDY.md`](CONNECTED_MACHINE_STUDY.md)). Its limit is the
unit it works in: **one question, one plan, one step**. Asked *what is the
atomic number of iron?* it answers 26; asked *is the atomic number of iron
prime?* it refuses, although it holds 26 and it decides primality. The same
holds for a sum of two register values, a ratio, a gcd of two looked-up
numbers, and for every engineering question whose givens are not one axiom
away from the target: *given voltage = 12 and resistance = 4, what is the
power?* is refused because the current has to be found first and nobody asked
for it.

The owner's request for this round: make the planner the central, shared
dispatch and reasoning engine, keep the all-plan agreement veto and the
conservative fallback, carry Three Column Thinking **step by step** as well as
for the whole answer, and when a step cannot be taken, **look for a step that
works elsewhere, insert it, and work forwards and backwards** until the
narrative is whole.

## 1. The objects

Exact throughout: `int` and `Fraction`, no float (D7); no digest decides a
meaning (D3).

* **A step** is one operation with named inputs, which are earlier steps, and
  one value. It carries its own three columns: a sentence of a declared,
  readable template (column 1), an exact equation `sₖ = …` (column 2), and a
  check that the script (column 3) runs on that step alone: the sentence is
  read back and must give the equation, and the equation is recomputed with
  the script's own arithmetic. A step whose value is a register entry names
  the table, row and field, and the script re-reads the register.
* **A chain** is a list of steps whose inputs point only backwards. Its answer
  is its last step. The chain's script checks every step, then the links,
  then the answer sentence, and prints `VERIFIED True` only if all hold.
* **Composition.** A compound question is split at its operator words
  (*plus*, *minus*, *times*, *divided by*), function forms (*the gcd of A and
  B*, *the square of A*, *the ratio of A to B*, *the sum of the Xs of A and
  B*), predicates (*is A prime*, *is A larger than B*, *which is larger, A or
  B*) and `then` (with *it* the previous step). Every bracketing is a
  **reading**; every part that is not a number is asked of the planner, one
  question at a time, through `ask_planned` — the planner is the executive of
  each step. A reading is licensed when every step of it is; the answer is
  given only when every licensed reading agrees (the planner's own rule,
  lifted to readings), else `AMBIGUOUS` with the readings named.
* **Goal questions and stitching.** `given A = x and B = y, what is T` is read
  over the axioms of the ten formula wheels, each name split per wheel except
  across a declared junction (the union rule of Phase 66). A reading binds
  each given and the target to one copy. A **derivation** is a tree of axiom
  steps from the givens to the target; an axiom is solved only for a variable
  that occurs to the power ±1, and only through non-zero values. The search
  runs backwards from the target through every axiom that contains it and
  forwards from the givens; every derivation (up to a declared budget) is
  computed. The answer is given only when the givens are consistent — no
  given is re-derived from the others with another value — and every
  derivation in every licensed reading agrees. The presented narrative is the
  smallest derivation; its steps that are neither given nor asked are marked
  **stitched**.
* **Narratives.** `given …, find A, then B` asks for steps in an order. A step
  that cannot be taken in one axiom step from what is known is **deferred**;
  later steps are tried; after every step taken the deferred ones are retried;
  when nothing moves, the first deferred step is **stitched** from the
  derivation search. The narrative records the order asked and the order
  taken.
* **Follow-ups.** A turn that starts with `then` extends the last chain of
  the conversation with *it* bound to its answer; `why?` replays that chain.
  The chain is kept under the SHA-256 of the whole conversation so far and
  compared verbatim before it is reused (D4, and the plan store's rule).

## 2. Declarations — written before any stepwise code

The corpus is
[`evaluation/stepwise_cases.py`](../overlay/glm_universal/evaluation/stepwise_cases.py),
committed with this section and before the module: 30 composition questions
(22 to be answered, 2 declared `AMBIGUOUS`, 6 refused by name), 21 goal
questions, 6 narratives and 4 two-turn conversations. Every expected answer
was worked by hand.

| mark | claim | measured by |
|---|---|---|
| **S1** | every composition case gets its declared verdict: the declared value, `AMBIGUOUS`, or the declared refusal name; 0 wrong answers. Control: the bare planner answers at most 2 of the 30 | `composition` |
| **S2** | every goal case gets its declared verdict, and every answered one stitches exactly the declared quantities; 0 wrong | `goals` |
| **S3** | the veto matters: a *first derivation found* control (no agreement, no consistency check) answers at least 3 of the goal cases the stepwise planner refuses, and a *naive union* control (every shared name one variable) answers the declared ambiguous case | `controls` |
| **S4** | every narrative gets its declared verdict, values, order taken and stitched quantities | `narratives` |
| **S5** | every answered chain's column-3 script prints `VERIFIED True` in a fresh `python3 -I`, with one `ALIGNED` line per step; four mutations of every chain — a consistent lie in one step's value, column 1 alone altered, two dependent steps swapped, the final sentence altered — are all rejected | `scripts` |
| **S6** | non-interference: on the router's declared sets (the 177 contract cases, the engineering, cognition and Python sets) the stepwise layer changes no answered verdict and turns no declared refusal into an answer | `interference` |
| **S7** | every follow-up conversation gets its declared verdict on the second turn, and the chain is reused only under the exact key | `follow_ups` |
| **S8** | `RequestProject/GLM/StepwisePlanner.lean` builds with no `sorry` and standard axioms, and proves: a derivation evaluates to the value of every model of its axioms and givens; so two derivations that disagree, or a given re-derived otherwise, leave no model; every bracketing of an associative operation agrees, and subtraction's do not; the fallback never changes an answer the planner gave; solving an axiom for a variable of power one is exact | Lean |

The measurement is `glm_universal.runtime.stepwise.stepwise_report`.

**One amendment, before any measurement.** While writing the module a named
refusal was added that no declared case exercises: `PRECISION_OVERLAP`, for a
comparison step between two looked-up values whose stated precisions overlap.
It is the ordering frame's own rule (round two of
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](SUBSTRATE_NATIVE_COGNITION_STUDY.md)),
kept so that a chain never orders what the planner would refuse to order. A
fifth mutation kind, `read-lie` (a lie in the first looked-up, planned or given
value), was added beside the four declared ones and is reported separately.

## 3. What was built

* [`runtime/stepwise.py`](../overlay/glm_universal/runtime/stepwise.py) — the
  stepwise planner: the composition grammar (operator words, function forms,
  predicates, verb forms over *it*, `then`), the leaf asker (every part is one
  question to `semantic_plan.plan_question`, cached per question; a register
  value is re-read from the field surface so it is exact), the agreement rule
  over readings, the goal and narrative modes over the split union of the
  wheels (the `Deriver`, which enumerates every acyclic derivation tree of a
  target, solving an axiom only for a variable of power ±1 and only through
  non-zero values), the consistency veto, the deferral-and-stitch agenda, the
  follow-up conversation keyed by SHA-256, the `Solution` the router returns,
  and `stepwise_report`.
* [`reasoning/stepwise_script.py`](../overlay/glm_universal/reasoning/stepwise_script.py)
  — the step, the chain, the declared templates of column 1 and column 2 and
  their readers, the in-process step gate, the chain's column-3 script (its own
  readers, its own arithmetic, the register re-read, the question re-parsed
  for givens, the wheel's own axiom re-parsed and substituted), and the
  mutations.
* **Wiring.** The router's planner surface hands a text to the stepwise
  planner only when the planner and the grammar behind it refused
  (`router._stepwise`); `GLM.py --ask` prints the chain with both columns per
  step, and `--verify-tct` runs the script and prints one `ALIGNED` line per
  step. `GLM.py --steps TEXT` asks the stepwise planner directly, and
  successive `--steps` are one conversation, so `then …` and `why?` follow on.
  `tools stepwise` takes the measurement.
* [`RequestProject/GLM/StepwisePlanner.lean`](../overlay/glm_lean/RequestProject/GLM/StepwisePlanner.lean)
  — §5.
* `tests/test_stepwise.py` — the marks, a three-chain sample of S5 by default
  and the full script census as an exhaustive case.

## 4. Results

Measured by `tools stepwise` at the close of the round.

| mark | result | figure |
|---|---|---|
| **S1** | met | 30 of 30 composition cases as declared: 22 answered with the declared value, 2 refused `AMBIGUOUS` with both readings named, 6 refused by the declared name; 0 wrong. The bare planner answers 0 of the 30 |
| **S2** | met | 21 of 21 goal cases as declared, every answered one stitching exactly the declared quantities; 0 wrong |
| **S3** | met | the first-derivation control answers all 3 goal cases the veto refuses by inconsistency or ambiguity (24, 3 and 2, each wrong or arbitrary); the naive union answers the ambiguous one (2, the capacitor's energy, where the kinetic energy is 9) |
| **S4** | met | 6 of 6 narratives: values, order taken and stitched quantities as declared |
| **S5** | met | 43 of 43 answered chains verified in a fresh `python3 -I`, 149 of 149 steps `ALIGNED`; value lie 43 of 43, column 1 alone 43 of 43, reordering 43 of 43, answer 43 of 43 rejected (and `read-lie` 43 of 43) |
| **S6** | met | 11 of the 273 declared questions of the contract, engineering and cognition sets are read by the stepwise layer at all; every one of the 11 is answered by the planner first, so none reaches it, and none would be turned from a refusal into an answer |
| **S7** | met | 4 of 4 follow-ups as declared; a conversation with a different history does not reuse the chain |
| **S8** | met | §5 |

**In all.** 57 of the 57 declared questions (30 composition, 21 goal, 6
narrative) and 4 of 4 follow-ups were answered or refused as declared, with 0
wrong answers; of the declared mutations of S5's four counted kinds, 172 of
172 were rejected (43 of each). So the answer to the question is yes, on this
corpus: the planner composes its own answers and finds unasked steps, refusing
by name wherever readings or derivations disagree.

**What the veto buys, case by case.** `given voltage = 12, current = 2 and
resistance = 4, what is the power` is refused `INCONSISTENT_GIVENS` because the
wheel re-derives the voltage as 8; the first derivation found answers 24.
`given voltage = 12, resistance = 4 and power = 20, what is the current` is
refused because the power re-derives as 36; the first derivation found
answers 3, which the power contradicts. `given mass = 2, velocity = 3,
capacitance = 1 and voltage = 2, what is the energy` is refused `AMBIGUOUS`:
the kinetic energy is 9 and the capacitor's is 2, and nothing in the question
says which is meant; the naive union answers 2.

**What composition buys.** The same planner that answers *what is the atomic
number of iron?* now answers *is the atomic number of iron prime?* (26 = 2 ×
13, so not), *what is the lcm of the atomic numbers of carbon and oxygen?*
(24), *what is the ratio of the atomic number of iron to the atomic number of
carbon?* (13/3), and chains such as *what is the atomic number of copper, then
multiply it by 3, then is it prime?* (87 = 3 × 29) — with 53 planner questions
asked across the 30 cases, each once. *2 times the atomic number of carbon
plus the atomic number of oxygen* is refused because its two readings give 28
and 20; *the atomic number of carbon plus that of oxygen plus that of iron* is
answered (40) because both of its readings give 40.

**Faculty (D15).** Derive: every answered chain computes a value no register
holds, from register values and axioms, with the steps shown and re-checked.
Refuse: the veto refuses the three goal cases the first-found control answers,
and the two composition cases whose readings disagree.

### 4.1 Beyond the declaration — not counted

Nineteen further questions, written after the module worked and so **not** a
held-out test, were run once to find the edges (`GLM.py --ask`). Fifteen were
answered and each was checked by hand: 0 wrong. The four left are refused or
unread: *how many more protons does iron have than carbon* and *is the atomic
number of gold odd* (no frame for *how many more*, or for parity), *the
average of …* (no averaging form), and givens written with units (*voltage =
12 volts*), which the goal reader does not accept, rather than guess a unit.

## 5. Lean

`RequestProject/GLM/StepwisePlanner.lean` builds with no `sorry` and the
standard axioms only.

* `eval_eq_model` — an admissible derivation evaluates to the model's value of
  what it derives, in every model of the rules and the givens;
  `derivations_agree` — so two derivations of one quantity agree whenever a
  model exists; `disagreement_refutes_model` and
  `rederived_given_refutes_model` — so disagreement, or a given re-derived
  otherwise, leaves no model: the refusals `DERIVATIONS_DISAGREE` and
  `INCONSISTENT_GIVENS` withhold nothing that was true.
* `solve_power_one`, `solve_power_neg_one` — solving an axiom for a variable
  of power ±1 through non-zero values is exact.
* `bracketing_sum`, `bracketing_prod`, `sum_bracketings_agree`,
  `prod_bracketings_agree` — every bracketing of a sum or a product agrees;
  `sub_bracketings_disagree` (case `c20`, 44 against 56) and
  `times_plus_readings_disagree` (case `c11`, 20 against 28) — the refused
  cases.
* `agreed_perm`, `agreed_eq_some_iff` — the agreement over readings is
  order-free and is a value every licensed reading gives.
* `checked_iff_recomputed` — a chain passes every local step check exactly
  when its values are the values recomputed from scratch.
* `fallback_conservative`, `fallback_sound` — the router's fallback never
  changes an answer the planner gave.

The file is written in Lean's module system (`module`, `public`); the
declaration parsers of `reasoning/lean_address.py` and `reasoning/retrieval.py`
now accept the `public` modifier.

## 6. What this leaves

* **A held-out set nobody on the project wrote** (candidate B of `STATUS.md`
  §3.4) matters more here than anywhere: the corpus and the module share an
  author, and every mark was met on the first reading. §4.1 is the honest
  size of the reach beyond it.
* **Frames the leaves lack**: *how many more*, parity, averages, and givens
  with units (read through the planner's unit table, converting to SI before
  the wheels). *Taken by Phase 73*
  ([`STEPWISE_TWO_STUDY.md`](STEPWISE_TWO_STUDY.md)).
* **The reverse relay into the chain**: let `relay:` hand a column-2 value to
  the stepwise planner as a composition, so the planner's multi-step answer
  chooses the next reverse operation (candidate M's last item).
* **Stitching across the register and the wheels together**: a given read
  from the register (*the density of gold*) feeding a wheel derivation. *Taken by
  Phase 73* ([`STEPWISE_TWO_STUDY.md`](STEPWISE_TWO_STUDY.md)).
