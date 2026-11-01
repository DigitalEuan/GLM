# The machine works the tools out — convergents, nearest fractions, gate moves and the Leech kissing number computed in GLM-BAT

## Tier 0 — the coarse read

**Question.** Can GLM-BAT compute the 44 steps of the stepwise planner's answered chains that Phase 160 left carried — tool answers (convergents, continued-fraction terms, nearest fractions, gate moves), a conversion, axiom steps, and `choose` and `first` steps — from definitions and checked witnesses rather than repeating the planner's values, and count the Leech kissing number from the Golay code's generator?

**Verdict.** Yes. The batch machine no longer repeats any step of an answered chain: it computes each one from definitions, checks every witness it is offered, and counts the Leech kissing number from the Golay code's generator.

**Deciding figure.** 8 of 9 marks and L1, 1 of 1 amended (F1′); carried steps 44 → 0; 174 of 174 chains admitted and read back; held-out control 2,785 of 2,785 admitted, 215 tool refusals unwritten; the Leech kissing number 196,560 counted from the generator rows (759 octads); F1 699 of 702 at the first measurement, 702 of 702 asked off and on in the same run.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026. Reconstructed 31 October 2026 from the round records; the original was lost in the October 2026 reorganisation.* The original was written on 19 October 2026 (the date of the Phase 163 record); its pre-registration (§§0–6) was written before the measurement, and one amendment (F1′, §3.1) was declared after the first measurement and before the second.

> **How this reconstruction was made.** From the Phase 163 record of
> [`MASTER_PLAN.md`](../MASTER_PLAN.md), the "machine works the tools out" row
> of [`SYSTEM.md`](../SYSTEM.md), §20.37 of
> [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), To-Do item 2 of
> [`STATUS.md`](../STATUS.md), the row of `tests/README.md` for
> `test_tool_machine.py`, the handler `_tool_machine` of `tools.py` (one line
> per mark, which gives each mark's subject), the docstring of
> `reasoning/tool_machine.py`, the line of §7.4 that
> [`PI_MACHINE_STUDY.md`](PI_MACHINE_STUDY.md) quotes, and the stored
> measurement `reasoning/_data/tool_machine_study.json` (§7.5). The marks'
> exact wording and thresholds were not recorded anywhere that survived; §5
> gives their subjects. No figure appears that those records do not give.

## 0. What this document is

A study for Phase 163, taken from the owner's plan of 19 October 2026
(`source_material/GLM_19OCT26_1.md`, Part II.2, the rest; `STATUS.md` §2.1
item 2), with the owner's note for this iteration: the GLM is to reason, not
repeat — no look-up dictionary — using the MOG, Golay and Leech structure where
it works.

After Phase 160 ([`FOLD_MACHINE_STUDY.md`](FOLD_MACHINE_STUDY.md)), 44 steps of
the stepwise planner's answered chains were still carried — written into the
GLM-BAT program as the planner's value, so the machine repeated them: tool
answers (convergents, continued-fraction terms, nearest fractions, gate
moves; [`TOOL_VALUES_STUDY.md`](TOOL_VALUES_STUDY.md),
[`TOOL_VERDICTS_STUDY.md`](TOOL_VERDICTS_STUDY.md)), a conversion, axiom steps
whose inputs it did not hold as numbers, and `choose` and `first` steps whose
inputs are verdicts.

## 1. What was built

* **`RequestProject/GLM/ToolMachine.lean`** (no `sorry`; standard axioms):
  Euclid's algorithm on the two ends of an enclosure emits only terms of every
  number between them (`lockstep_certified`, `euclidTerms_eq`); the convergent
  recurrence (`convRun_eq`); enclosures of `π` (Mathlib's twenty-digit bounds,
  `pi_enclosure`), `e` (the series loop and its error bound, `eT_div`,
  `e_enclosure`) and `√m` (a checked integer root, `sqrt_enclosure`); the
  Farey certificate of a nearest fraction (`between_of_ends`, `side_of_ends`,
  `nearest_of_nearer`); Toffoli and Fredkin by arithmetic on bits and a sound
  breadth-first search (`gateArith_spec`, `machineDist_sound`).
* **`RequestProject/GLM/LeechMachine.lean`** (no `sorry`; finite checks by
  `native_decide`): the Gray-code walk over the 4,096 Golay messages, one
  generator row a step (`gray_step`, `gray_nodup`), counts 759 octads and
  4,096 codewords (`machine_octads`, `machine_codewords`), and
  `128·octads + 4·276 + 24·codewords = 196,560`
  (`leech_kissing_from_census`).
* **`glm_universal/reasoning/tool_machine.py`** (switch `ON`): the GLM-BAT
  subroutines for each, hooked into `planner_ladder.chain_program`. A real is
  held as an enclosure of two fractions, and Euclid's algorithm runs on both
  ends at once: a term is written only while the two quotients agree, and then
  it is a term of every number between them. A nearest fraction with a bounded
  denominator comes with a Farey certificate the machine checks itself, a gate
  count with a breadth-first search over bit masks. The Golay census
  subroutine is written from `substrate.mog.GolayCode.B`, the code's
  generator, never from its census. An axiom's `^` is read as the power it
  means.
* **The measurement.** `glm_universal/reasoning/tool_machine_study.py`;
  `tools tool-machine [--write] [--baseline] [--json]`; stored in
  `reasoning/_data/tool_machine_study.json` (the first measurement kept as
  `tool_machine_study_first.json`).

## 2. The control

A **held-out control** of 3,000 tool questions outside the evaluation: every
answer the tool gives must be admitted by the machine, a lie at each must be
refused, and every question the tool refuses must stay unwritten.

## 3. What is not claimed

Reals other than `π`, `e` and `√m`, and tools other than the five computed,
stay carried; `π` is a declared enclosure (Mathlib's proved bounds), not a
series the machine sums; of the Leech shells only the minimal one is counted,
and the shapes rule that turns the census into 196,560 is declared, not
derived (Phase 164, [`LEECH_SHELLS_STUDY.md`](LEECH_SHELLS_STUDY.md), proved
it). The witness for `√m` is offered, then checked by squaring.

### 3.1 The amendment (F1′)

Declared after the first measurement and before the second. **F1 was missed**
at the first measurement: 699 of 702 recorded texts kept their text, because
the three corpus cases had moved with the documents committed between the
baseline and the measurement — not with the machine. **F1′** asks the frozen
path's question with the switch off and on **in the same run**, so that the
documents cannot move between the two readings.

## 4. Faculties

*Derivation:* every step of an answered chain is now derived by the machine.
*Refusal:* a step whose certificate fails stops the machine. No answer moved
(F1′).

## 5. The marks

Subjects as the round's instrument prints them (`tools.py`, `_tool_machine`);
the exact thresholds were not recorded.

| mark | what it measures |
|---|---|
| **L1** | `ToolMachine.lean` and `LeechMachine.lean` state their theorems with no `sorry` |
| **T1** | carried steps with the switch off and on, and the steps newly computed, by category |
| **T2** | chains admitted by the machine, and read back |
| **T3** | a lie at each newly computed step found at its own step |
| **T4** | a moved square-root witness stops the run |
| **T5** | column 3 (the scripts) and their mutants rejected |
| **K1** | the held-out control: admitted, lies refused, tool refusals left unwritten |
| **G1** | the Leech kissing number from the Golay census: texts admitted, lies found, the shells it does not count kept carried, machine steps |
| **P1** | the largest program and the most machine steps |
| **F1** | the frozen path: every recorded text with the same status and the same text |

## 6. How it is measured

`python3 -m glm_universal.tools tool-machine` reads the stored measurement;
`--write` re-takes it, `--baseline` re-takes the frozen path's baseline with
the switch off. Tests: `tests/test_tool_machine.py` (7), run by hand: 7 of 7
passed (pytest was not installed).

## 7. What came out

### 7.1 The marks

| mark | recorded result | outcome |
|---|---|---|
| **L1** | both files built with no `sorry` | met |
| **T1** | carried steps 44 → 0: convergents 21, continued-fraction and nearest-fraction verdicts 2 + 2, gate verdicts 4, gate moves 1, axiom 7, `choose` 3, `first` 3, conversion 1 | met |
| **T2** | 174 of 174 chains admitted and read back | met |
| **T3** | 20 of 20 lies found at their step | met |
| **T4** | a moved square-root witness stopped 2 of 2 runs | met |
| **T5** | column 3 20 of 20, mutants 40 of 40 | met |
| **K1** | 3,000 tool questions: 2,785 answered by the tool, 2,785 of 2,785 admitted, 2,785 lies refused, 215 tool refusals unwritten | met |
| **G1** | 4 of 4 texts admitted, lies found, about 164,000 machine steps; the norm-6 shell kept carried | met |
| **P1** | largest program 1,783 lines | met |
| **F1** | 699 of 702 at the first measurement (the three corpus cases moved with the documents) | missed |
| **F1′** | asked off and on in the same run, 702 of 702 | met |

**8 of 9 marks and L1, 1 of 1 amended.**

### 7.2 What this answers

Yes. The batch machine no longer repeats any step of an answered chain: it computes each one from definitions, checks every witness it is offered, and counts the Leech kissing number from the Golay code's generator. Given only the code's twelve generator rows, the machine walks its 4,096 codewords one row-flip at a time, counts 759 octads, and forms `128·759 + 4·276 + 24·4096 = 196,560`.

The first attempt read an axiom's `^` as Python's exclusive-or with the wrong
precedence; the machine's own drift check refused four chains, and the reading
was corrected before the measurement.

**What it invalidated.** The new files made nine stored measurements stale
(`runtime/toolbox.py`, `planner_ladder.py` and the new Lean files are in their
digests); all were re-taken: `carried-read` (12 of 12), `fold-machine` (its
study measures with the tool machine off; F1 then 693 of 702 against the Phase
160 baseline, recorded in [`FOLD_MACHINE_STUDY.md`](FOLD_MACHINE_STUDY.md)
§7.5), `planner-ladder` (7 of 7, after `ties-ladder-frozen`, 7 of 7),
`address-read`, `answering-question` (8 of 10, as before), `budget-reading`
(8 of 8), `nearest-address` (7 of 7) and the Lean citation reference. The
evaluation's pinned Lean counts (`report-relay`, `report-anonymous`) did not
move. The test-file sign-off was still owed (pytest not installable).

### 7.3 How it was used next

Phase 164 ([`LEECH_SHELLS_STUDY.md`](LEECH_SHELLS_STUDY.md)) derived the shapes
rule this round declared and counted every shell; Phase 166
([`PI_MACHINE_STUDY.md`](PI_MACHINE_STUDY.md)) took the first line of §7.4.

### 7.4 What is left

* *`π`'s enclosure is a declared constant (Mathlib's proved bounds), where a
  series the machine sums would make it computed like `e`* (the line Phase 166
  quotes and took).
* The Leech shells beyond the minimal one (GLM-BAT counts only the minimal
  shell).
* The census cached by digest: a kissing-number question costs about 164,000
  machine steps.
* The typed planner's plans said as GLM-BAT (ordering and extremum, linear,
  Bezout, factorise, substrate facts).

### 7.5 State of the files at this reconstruction (31 October 2026)

`reasoning/tool_machine.py` is in the tree. `reasoning/tool_machine_study.py`
was reconstructed on 31 October 2026, in the same repository check; its
figures are the reconstruction's, so the tier-0 block above names no
recomputing function. `tests/test_tool_machine.py` was also rebuilt on
31 October 2026, from its row in `tests/README.md` and this document; its
docstring says so, and what it passes is the reconstruction's, not this
round's. `ToolMachine.lean` and `LeechMachine.lean` are not in the tree (both
Lean files are recorded missing in
[`_lean_files_needed.md`](_lean_files_needed.md), and the test that reads
them skips while they are). A stored measurement
`reasoning/_data/tool_machine_study.json` was in the tree before the
reconstruction: it records the same outcome as §7.1 (8 of 9, F1 missed, F1′
met, 1 of 1 amended) and the same chain figures, with 163,831 machine steps
for G1; its frozen path compares 702 texts (702 same status, 692 same text)
and its paired comparison 703 texts (703 of 703), where the round's record
gives 702, so it is not the round's own file; which later round wrote it is
not recorded. On 31 October 2026 it was replaced by the reconstruction's
re-take (`tools tool-machine --write`), so that the stored measurement is
current against the code: 8 of 9 again (T1–T5, K1, G1, P1 met; F1 not met),
with F1′ *not measured* rather than met, because the frozen path's baseline
was lost with the module; the file it replaced is in the repository's
history, and its figures are the ones quoted above.

## In one paragraph

Phase 160 left 44 steps of the stepwise planner's answered chains carried.
Phase 163 has the machine work each one out: a real is held as an enclosure
of two fractions (`e` summed with a proved error bound, `√m` from a checked
integer root, `π` from Mathlib's bounds) and Euclid's algorithm runs on both
ends at once (`lockstep_certified`); a nearest fraction comes with a Farey
certificate, a gate count with a breadth-first search. Carried steps fall 44 →
0, every lie is found at its step, a moved witness only stops the run, and the
held-out control agrees with the tool on all 2,785 it answers and stays silent
on the 215 it refuses. The Leech kissing number is counted from the Golay
code's generator rows (`leech_kissing_from_census`). F1 was missed because the
documents moved between baseline and measurement; asked off and on in the same
run, no answer moved (F1′). 8 of 9 marks and L1, 1 of 1 amended.
