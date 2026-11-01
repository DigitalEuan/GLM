# The machine sorts — order folds, ranks, top rows and hole bounds computed in GLM-BAT

## Tier 0 — the coarse read

**Question.** Can GLM-BAT compute, from its own reads, the folds of the stepwise planner's answered chains that Phase 153 left carried — the order folds (median, quartiles, the `k`-th largest), ranks, top rows, folds over the present rows and bounds with holes — so that no fold is carried, with nothing moved?

**Verdict.** Yes. Every fold the stepwise planner answers is now computed by GLM-BAT from its own reads — an order statistic as the reading whose window holds the position, checked by counting for a witness the program offers but the machine does not trust — and the carried steps fall from 92 to 44 with nothing moved.

**Deciding figure.** 8 of 9 marks, 1 of 1 amended (M4′); folds carried 48 → 0 and carried steps 92 → 44; 174 of 174 chains admitted and read back; hole lies 22 of 24 stopped at the first measurement, 24 of 24 after the fix; 702 of 702 recorded texts unchanged.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026. Reconstructed 31 October 2026 from the round records; the original was lost in the October 2026 reorganisation.* The original was written and measured in the Phase 160 session; its pre-registration (§§0–6) was committed before the stored measurement, and one amendment (M4′, §3.1) was declared after the first measurement and before the second.

> **How this reconstruction was made.** Every statement below comes from a
> surviving record: the Phase 160 record of [`MASTER_PLAN.md`](../MASTER_PLAN.md),
> the "machine sorts" row of [`SYSTEM.md`](../SYSTEM.md), §20.34 and the study
> table of [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), To-Do item 2 of
> [`STATUS.md`](../STATUS.md), the row of `tests/README.md` for
> `test_fold_machine.py`, the handler `_fold_machine` of `tools.py` (which
> prints one line per mark and so gives each mark's subject) and the Phase 163
> record (for §7.5). The exact wording and threshold of each mark were not
> recorded anywhere that survived, so §5 gives each mark's subject and §7.1 its
> recorded outcome; nothing here is a new measurement, and no figure appears
> that the records do not give.

## 0. What this document is

A study for Phase 160, taken from the owner's plan of 19 October 2026
(`source_material/GLM_19OCT26_1.md`, Part II.2, *close the remaining
carried-value gaps*), which took over To-Do item 2 (*the machine's reading,
the rest*) as Phase 153 left it.

Phase 153 ([`CARRIED_READ_STUDY.md`](CARRIED_READ_STUDY.md)) gave the batch
machine its own copy of the registers, so a value the stepwise planner looked
up became an entry the machine finds. But 48 fold steps stayed carried —
written into the GLM-BAT program as the planner's value — because GLM-BAT has
no arrays and no numeric sort, and an order statistic had no reading in it.
This round closes them by **counting**.

## 1. What was built

* **`RequestProject/GLM/FoldMachine.lean`** (no `sorry`, standard axioms, as
  recorded): the window characterises the `k`-th smallest (`kth_lt_iff`,
  `kth_eq_iff`, `kth_window`, `window_unique`) — a reading is at position `q`
  of the sorted column exactly when at most `q` readings lie below it and more
  than `q` lie at or below it; the stable position of the top rows is a
  permutation that keeps order and breaks ties by register order
  (`stablePos_lt`, `stablePos_strict`, `stablePos_tie`, `stablePos_injective`);
  `FIND "@k="` fails exactly when the register holds no entry at `k`
  (`hole_needle_iff`, `absent_iff`). `HoleBounds.lean`'s four definitions were
  exposed to importing modules (statements unchanged).
* **`glm_universal/reasoning/fold_machine.py`** (the switch `ON`): order
  folds, ranks, top rows, bounds, folds over the present rows, holes read as
  absences; impossible shapes stop the machine; hooked into
  `planner_ladder.chain_program` in its reading mode.
* **The witness.** Counting every reading's window costs `n²` comparisons —
  43,346 lines for one question over all the elements — so the program offers
  a witness for each position and the machine checks the witness's window, `n`
  comparisons a position. A wrong witness stops the run and cannot move the
  value (`window_unique`).
* **A rank** is one more than the readings above; **the bounds** on a fold
  with holes follow `GLM.HoleBounds` ([`HOLE_FOLDS_STUDY.md`](HOLE_FOLDS_STUDY.md));
  **every declared hole** is read as an absence.
* **The budget.** `batch_machine.run_pipeline` takes a stage budget, and
  `planner_ladder.check_chain` passes its own (`BUDGET`, 200,000): the gated
  pipeline had run under the machine's default of 10,000 while the run it
  gates used 200,000 — a tenth of the budget.
* **The measurement.** `glm_universal/reasoning/fold_machine_study.py`,
  `tools fold-machine [--write] [--baseline]`; the measurements in
  `reasoning/_data/fold_machine_study.json` (the first kept as
  `fold_machine_study_first.json`), the frozen path's baseline in
  `reasoning/_data/fold_machine_baseline.json`.

## 2. The control

A **synthetic control** of 3,000 columns, ties and holes common, drawn by a
declared linear congruential generator: the machine must admit every answer
the planner gives, refuse a lie at every answered column, and leave every
column the planner refuses unwritten. The first attempt drew the columns with
`random`, which turned the blueprint audit's claim 1 (no randomness in the core
sub-packages) to refuted and moved the `report-blueprint` answer; the study
module was changed to the declared generator before the measurement of record.

## 3. What is not claimed

The 44 steps still carried after this round (tool answers, axiom inputs,
verdict inputs) are not computed here; set membership is still the planner's;
the typed planner's ordering and extremum plans are not said as GLM-BAT
(§7.4). The witness is offered by the program, not found by the machine: what
is claimed is that the machine never writes a value its own counting does not
confirm.

### 3.1 The amendment (M4′)

Declared after the first measurement and before the second. At the first
measurement a declared hole that pushed a position past the readings left the
fold impossible, and the machine, unable to compute it, carried the claim:
hole lies 22 of 24 were stopped and **M4 was missed**. The fix: impossible
shapes stop the machine. **M4′** asks the same of the amended machine; it is
the measurement of record for the hole lies.

## 4. Faculties

*Refuse* gained a check: a fold whose readings, positions or holes disagree
with the machine's counting is withheld. No answer the evaluation pins moved.

## 5. The marks

The subjects below are those the round's instrument prints (`tools.py`,
`_fold_machine`); the exact thresholds were not recorded.

| mark | what it measures |
|---|---|
| **L1** | `FoldMachine.lean` builds with no `sorry` |
| **M1** | folds carried with the switch off and on, carried steps, and the folds newly computed |
| **M2** | chains admitted by the machine, and read back |
| **M3** | a lie at each fold found at its own step |
| **M4** | a lie at a declared hole stopped |
| **M5** | the witness rotated: runs stopped, runs on a reading of the same value, wrong values written |
| **M6** | column 3 (the scripts) and their mutants rejected |
| **K1** | the synthetic control: admitted, lies refused, planner refusals left unwritten |
| **P1** | the largest program and its machine steps |
| **F1** | the frozen path: every recorded text with the same status and the same text |

## 6. How it is measured

`python3 -m glm_universal.tools fold-machine` reads the stored measurement and
prints one line per mark; `--write` re-takes it, `--baseline` re-takes the
frozen path's baseline with the switch off. Tests: `tests/test_fold_machine.py`
(10), run by hand: 10 of 10 passed (pytest was not installed).

## 7. What came out

### 7.1 The marks

| mark | recorded result | outcome |
|---|---|---|
| **L1** | the file built with no `sorry`, standard axioms | met |
| **M1** | 48 folds carried with the switch off, 0 with it on; carried steps 92 → 44 | met |
| **M2** | 174 of 174 chains admitted and read back | met |
| **M3** | fold lies 48 of 48 found at their step | met |
| **M4** | hole lies 22 of 24 stopped at the first measurement | missed |
| **M5** | the witness rotated in 32 chains: 29 stopped, 3 the same value, 0 wrong | met |
| **M6** | column 3 48 of 48, mutants 96 of 96 | met |
| **K1** | 3,000 columns: 2,188 of 2,188 admitted, 2,168 of 2,168 lies refused, 812 of 812 planner refusals left unwritten | met |
| **P1** | the largest program 1,783 lines (the all-pairs version of the round made 43,346) | met |
| **F1** | 702 of 702 recorded texts unchanged; the evaluation 222 of 222 | met |
| **M4′** | hole lies 24 of 24 stopped after the fix | met |

**8 of 9 marks, 1 of 1 amended.** The count is of the nine measured marks;
L1 is reported beside them. (Phase 161 found that the deciding figures count
their marks in more than one way — the Lean mark with the measured marks,
beside them, or not at all; see [`STUDY_LEDGER_STUDY.md`](STUDY_LEDGER_STUDY.md) §7.4.)

### 7.2 What this answers

Yes. Every fold the stepwise planner answers is now computed by GLM-BAT from its own reads — an order statistic as the reading whose window holds the position, checked by counting for a witness the program offers but the machine does not trust — and the carried steps fall from 92 to 44 with nothing moved.

**What it invalidated.** The stored measurements that digest
`planner_ladder.py` or `batch_machine.py` were re-taken with every mark as
before: `carried-read` (now measured with the fold switch off, since it
measures Phase 153's reads; 12 of 12), `ties-ladder-frozen`, then
`planner-ladder` (7 of 7; [`PLANNER_LADDER_STUDY.md`](PLANNER_LADDER_STUDY.md)).
The test-file sign-off was still owed (pytest not installable).

### 7.3 What the round found on the way

The gated pipeline had been running under a tenth of the budget of the run it
gates (§1, *the budget*), and drawing the control with `random` had silently
refuted a claim of the blueprint audit (§2). Both were fixed in the round.

### 7.4 What is left

* The 44 carried steps (tool answers, axiom inputs, verdict inputs) — taken by
  Phase 163 ([`TOOL_MACHINE_STUDY.md`](TOOL_MACHINE_STUDY.md)), which brought
  them to 0.
* Set membership as a register file (`@<set>.<row>=member;`), so the machine
  can read which rows belong to a declared set.
* Exact question reads (a question read is membership, not position).
* One junction table.
* The typed planner's ordering and extremum plans by the same counting.

### 7.5 Later re-takes

Phase 163 re-took this measurement with the tool machine off (its study
measures with that switch off): F1 then read 693 of 702 against the Phase 160
baseline, nine evaluation texts having moved by later rounds. Nothing in this
round's machine moved them.

### 7.6 State of the files at this reconstruction (31 October 2026)

`reasoning/fold_machine.py` and `reasoning/fold_machine_study.py` were
themselves reconstructed on 31 October 2026, in the same repository check;
their docstrings say so, and the study module says that its marks' thresholds
are its own, declared before its measurement, because the original thresholds
were not recorded. A figure it measures is therefore the reconstruction's, not
this round's, and is not quoted here; that is why the tier-0 block above names
no recomputing function. `tests/test_fold_machine.py` was also rebuilt on
31 October 2026, from its row in `tests/README.md` and this document; its
docstring says so, and what it passes is the reconstruction's, not this
round's. The round's stored measurements and `FoldMachine.lean` are not in
the tree (the Lean file is recorded missing in
[`_lean_files_needed.md`](_lean_files_needed.md), and the test that reads it
skips while it is); `HoleBounds.lean` is present.

## In one paragraph

Phase 153 left 48 folds of the stepwise planner's chains carried because
GLM-BAT has no arrays and no sort. Phase 160 has the machine compute each one
by counting: a reading is at position `q` exactly when at most `q` readings
lie below it and more than `q` at or below it (`kth_eq_iff`), the program
offers a witness and the machine checks its window, top rows are checked by
stable position, ranks counted, bounds follow `GLM.HoleBounds`, and holes are
read as absences (`absent_iff`). All 48 folds are computed, carried steps fall
from 92 to 44, a lie at each fold is found at its step, the synthetic control
agrees on all 2,188 columns the planner answers and leaves the 812 it refuses
unwritten, and 702 of 702 recorded texts are unchanged. One mark (M4) was
missed at the first measurement and met as amended (M4′). 8 of 9 marks, 1 of 1
amended.
