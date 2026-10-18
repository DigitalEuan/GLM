# The operations ladder in the stepwise planner — the chain as a GLM-BAT program

## Tier 0 — the coarse read

**Question.** Can every chain the stepwise planner answers be said as a GLM-BAT program and run by the batch machine, with drift and rollback as planner checks that gate the answer, without moving any answer the planner or the evaluation gives?

**Verdict.** Yes. All 174 chains the stepwise planner answers among its 283 recorded texts are said as GLM-BAT, read back to the identical lines, run by the batch machine to a halt, leave no drift and are promoted by the gated pipeline, so the gate refused nothing the planner answered. A lie in the last computed step is found at that step in 87 of 87 chains, and the pipeline does not promote and leaves no file. The machine checks what it computes, not what it carries: of the 2,494 steps, 180 are computed and 2,314 carried as data, and a lie in a carried step is caught only downstream, in 87 of 168 cases. No mark was missed.

**Deciding figure.** 7 of 7 measured marks and L1; 174/174 chains said, run, drift-free and promoted (15,092 lines, 15,457 machine steps); lies in a computed step 87/87 found, none promoted; 348/348 column-3 mutants rejected; 283/283 recorded texts and 212/212 evaluation statuses unchanged.

**Recomputed by.** `glm_universal.reasoning.planner_ladder_study.planner_ladder_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 151, item 1 of [`STATUS.md`](../STATUS.md)
§2.1 (*the operations ladder in the planner and the session*, left by Phase
125, [`OPERATIONS_LADDER_STUDY.md`](OPERATIONS_LADDER_STUDY.md) §7.4). §§0–6
were committed with the Lean file and the answering-path code, before the
stored measurement and the frozen-path comparison were taken; §7 is what came
out.

**What the item asked.** The DevOps ladder and its batch machine GLM-BAT were
reached only through `tool ladder` and `tool machine`. The item asks for the
planner's plans, or the session's default domains, to be given the ladder's
vocabulary: a plan step as a GLM-BAT line, drift and rollback as planner
checks. This round takes the **stepwise planner** (`runtime/stepwise.py`),
whose answers are chains of steps.

* **A plan step as GLM-BAT lines** (`reasoning/planner_ladder.py`). Every step
  of an answered chain is said as GLM-BAT. `SET /A` is integer arithmetic, so
  a rational value is a numerator and a nonzero denominator
  (`GLM.PlannerLadder.Rep`). A step the machine can compute (the four
  operations, powers, means and sums, unit conversions, a formula-wheel axiom,
  a comparison, a branch or search result) is **computed** from the machine's
  own earlier values and reduced by Euclid's algorithm, written as a GLM-BAT
  subroutine with a loop. A step whose value comes from outside the machine (a
  register value, a given, a verdict the machine does not decide) is
  **carried** as data. Each step writes `s<k>.txt`.
* **Drift as a planner check.** The desired state is the planner's claim, one
  file per step; the actual state is what the machine leaves.
* **Rollback as a planner check.** A gated program checks each computed step
  by cross-multiplication and exits 1 at the first mismatch; it is the first
  stage of a pipeline whose second stage promotes the last file, with
  rollback on.
* **The gate.** An answered chain is kept only when the machine's run halts,
  leaves no drift and the pipeline promotes; otherwise it is refused as
  `MACHINE_DRIFT` (`stepwise._ladder_gate`, in `answer` and the follow-ups).
  The program is added to the steps and the payload, never to the answer
  text. `GLM.py` prints the program's lines and verifies its scripts.

**What was known before this was written.** The chains were run while the
code was built: 174 of the 283 recorded single-turn texts are answered chains;
all were said, read back, halted, had no drift and promoted. The first lie
test changed the last numeric step of a chain whatever its kind, and so often
hit a **carried** step, which the machine takes as data: it found 85 of 127
lies. A lie in a carried step is outside `drift_eq_lies`'s hypotheses, so P4
was restated to change the last **computed** step (87 chains have one), and
the carried-step lie is kept as a post-hoc reading. Both baselines — the 283
texts (`reasoning/_data/planner_ladder_baseline.json`) and the whole
evaluation (`reasoning/_data/ties_ladder_baseline.json`, shared with Phase
150) — were taken before any answering-path file was edited. **Neither the
stored measurement nor the frozen-path comparison had been run when this was
committed.**

## 1. What is proved before any code

`RequestProject/GLM/PlannerLadder.lean` (namespace `GLM.PlannerLadder`); no
`sorry`, standard axioms only.

* `Rep`, `rep_int`, `rep_add`, `rep_sub`, `rep_mul`, `rep_div` — the
  integer-pair representation of a rational, closed under the four operations
  as the program computes them.
* `rep_check_iff` — the gated program's cross-multiplication test holds
  exactly when the represented value is the claimed one.
* `machine_eq_honest` — if the computed steps are causal and every carried
  step carries the honest value, the machine's values are the honest values.
* `drift_eq_lies` — under the same conditions, a step drifts exactly when its
  claimed value is not the honest one; `no_drift_iff` — no drift exactly when
  the chain is honest.
* `writeAll_append`, `rollback_journal` — restoring the journal after a run
  of writes gives back the files as they were, however far the run got.
* `promoted_iff_no_drift` — the pipeline promotes exactly when no step drifts.

## 2. The rule

As §0.

## 3. The questions

The 283 single-turn texts of the stepwise planner's corpora (rounds one to
five, the tool values and the tool verdicts), recorded before the round; the
chains are the texts the planner answers.

## 4. The marks, declared before the measurement

| mark | claim |
|---|---|
| **L1** | `PlannerLadder.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **P1** | every chain is said as a GLM-BAT program, the program said as English reads back to the identical lines, and the machine's run halts with exit code 0 |
| **P2** | no chain drifts |
| **P3** | every chain's gated pipeline promotes |
| **P4** | every chain with a computed step, its last computed step raised by one: the drift is exactly that step, and the pipeline does not promote and leaves no file |
| **P5** | both column-3 scripts of every chain verify; the run claim with its last file altered, and the pipeline claim with its promotion flipped, are rejected |
| **F1** | every recorded text asked again through the router: the same status and the same answer text |
| **F2** | the evaluation's frozen path (`ties_ladder_frozen`, shared with Phase 150): every case present with the same status, every moved text with a declared cause |

## 5. What would count against

P2 or P3 failing on an honest chain would mean the program does not compute
what the planner claims (or the machine is wrong). P4 failing would mean the
gate cannot see a lie it is proved to see. F1 failing would mean the gate
refused an answer the planner gave.

## 6. What is not claimed

A lie in a **carried** step is data to the machine: the machine cannot find it
at its step, and only finds it downstream when a computed step reads it. The
session's default domains are not given the ladder vocabulary in this round.

## 7. What came out

`python3 -m glm_universal.tools planner-ladder` (stored in
`reasoning/_data/planner_ladder_study.json`, digest-guarded); F2 reads the
shared frozen path, `python3 -m glm_universal.tools ties-ladder-frozen`.

In short: every answered chain is a GLM-BAT program the machine runs and
agrees with, so the gate refused nothing the planner answered; a lie in a
computed step is always caught; a lie in a carried step is caught only when
a computed step reads it. No mark was missed.

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | `PlannerLadder.lean` builds with the full `lake build` (8,251 jobs), no `sorry` | yes |
| **P1** | 174 of 174 chains said as GLM-BAT and read back to the identical lines; 174 of 174 runs halted with exit code 0 (15,092 lines, 15,457 machine steps) | yes |
| **P2** | 174 of 174 chains without drift (180 computed and 2,314 carried steps) | yes |
| **P3** | 174 of 174 gated pipelines promote | yes |
| **P4** | the 87 chains with a computed step, its last computed step raised by one: 87 of 87 drift exactly at that step; 87 of 87 pipelines do not promote and leave no file | yes |
| **P5** | 174 of 174 run scripts and 174 of 174 pipeline scripts verify in column 3; 348 of 348 mutants (the last file altered, the promotion flipped) rejected | yes |
| **F1** | 283 of 283 recorded texts asked again: the same status and the same answer text | yes |
| **F2** | the shared frozen path: 212 of 212 evaluation cases present with the same status, 0 undeclared moved texts (none of them moved by this round) | yes |

*Re-taken at Phase 154* (the `corpus` query kind): 7 of 7 marks again. F1
now reads 283 of 283 with the same status and 272 of 283 with the same text;
each of the 11 moved texts is exactly the old refusal with `'corpus'` added to
its list of query kinds, the one move declared at that re-take, and F1 was
amended then from *the same text* to *the same text or that declared move*.

### 7.2 The post-hoc reading: a lie in a carried step

Kept as declared in §0, with no mark. In 168 chains the last carried step
(a register value, a given or a verdict) was changed instead. The machine
takes a carried value as data, so it found none of them at the step itself;
87 were caught downstream, where a computed step read the changed value and
its result no longer matched the planner's claim, and 81 were not seen at
all, because nothing the machine computes reads that step.

### 7.3 What this answers

The ladder's vocabulary is now part of the stepwise planner's answer: each
answered chain carries its program, its run, its drift (none) and its
promotion, and `GLM.py` prints the program and verifies its scripts. Because
an honest chain never drifts (`no_drift_iff`) and the pipeline promotes
exactly when there is no drift (`promoted_iff_no_drift`), the gate can only
refuse a chain whose computed arithmetic disagrees with the machine, and over
the recorded corpora there is none. What the machine adds is a second,
independent computation of the planner's arithmetic, with a rollback that
leaves nothing behind when it disagrees (`rollback_journal`).

### 7.4 What is left

* Most of a chain is carried, not computed (2,314 of 2,494 steps): the
  machine re-does the arithmetic but trusts the register values and givens.
  A check of a carried step would need the machine to read the register
  itself.
* The session's default domains are not given the ladder vocabulary; only
  the stepwise planner is.
* The typed planner and the plan search (`planner`, `tool machine`) are not
  gated by the machine.
