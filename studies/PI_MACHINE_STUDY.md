# The machine sums π — Machin's formula and the arctangent series, proved in Lean and run in GLM-BAT

## Tier 0 — the coarse read

**Question.** Can the batch machine GLM-BAT compute its own enclosure of π from integers, by rules proved in Lean, as it already does for `e`, rather than read π as a declared constant?

**Verdict.** Yes. Machin's formula, the error bound of the series for `arctan` and the machine's Horner loop in two integers are proved in Lean, and the four integers the machine leaves are proved to enclose π for every number of terms. The summed enclosure is about 10⁻⁵⁷ wide (the declared constant was 10⁻²⁰), certifies 53 terms of π's continued fraction (the constant certified 19), and every one-step π chain the constant admitted is admitted with the same value.

**Deciding figure.** 6 of 6 marks; `piEnds_enclose`, 0 `sorry`, standard axioms only; 335 machine steps; 53 certified terms against 19; 80 of 80 one-step π chains admitted (47 before, 0 lost); the 237-for-239 control is caught by Mathlib's decimals.

**Recomputed by.** `glm_universal.reasoning.pi_machine_study.pi_machine_marks`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 19 October 2026 (pre-registered 19 October 2026; measured 19 October 2026, in the same session: the marks of §5 were written before the measurement of §7, but not committed separately).*

## 0. What this document is

A study for Phase 166. It takes a line of To-Do item 2 (*the machine's
reading, the rest*), left by
[`TOOL_MACHINE_STUDY.md`](TOOL_MACHINE_STUDY.md) §7.4 and repeated by
[`LEECH_KISSING_STUDY.md`](LEECH_KISSING_STUDY.md) §7.3:

* *`π`'s enclosure is a declared constant (Mathlib's proved bounds), where a
  series the machine sums would make it computed like `e`.*

It also takes the smaller line of the same item: GLM-BAT's REM line for the
Leech kissing number now cites `GLM.LeechKissing.leech_kissing_number` and
`minimal_iff` rather than `minimal_shape`.

## 1. What this round builds

**The Lean file** (`overlay/glm_lean/RequestProject/GLM/PiMachine.lean`, 0
`sorry`, axioms `propext`, `Classical.choice`, `Quot.sound`).

* `machin` — `π = 16 arctan (1/5) − 4 arctan (1/239)`, from Mathlib's
  doubling and addition formulas for `arctan` and `arctan 1 = π/4`.
* `arctan_series_bound` — for `0 ≤ x < 1`, the first `n` terms of
  `∑ (−1)^i x^(2i+1)/(2i+1)` are within `x^(2n+1)/(2n+1)` of `arctan x`
  (Mathlib's power series for `arctan` and its alternating-series error
  bound).
* `atStep`, `atH`, `atH_div`, `atH_arctan_sum` — the machine's loop:
  Horner's rule from the last term back to the first, in two integers,
  `P ← m² Q − (2k+1) P`, `Q ← (2k+1) m² Q`, from `(0, 1)`. After `n` steps
  `P / (m Q)` is exactly the `n`-term partial sum for `arctan (1/m)`.
* `pi_series_bound` — Machin's combination of the two loops is within
  `16 (1/5)^(2a+1)/(2a+1) + 4 (1/239)^(2b+1)/(2b+1)` of `π`.
* `piEnds`, `piEnds_enclose` — the four integers the machine forms, and the
  theorem that `π` lies between the two fractions, with positive
  denominators, for every `a` and `b`.

**The machine** (`overlay/glm_universal/reasoning/tool_machine.py`).
`pi_lines` writes the two loops and the combination as GLM-BAT lines; with the
switch `PI_SUMMED` on (the default) they replace the declared constant
wherever a step needs π. `PI_TERMS = (40, 12)`. `pi_ends` is the Python mirror
of `piEnds`. The switch off restores Phase 163's constant.

**The marks** (`overlay/glm_universal/reasoning/pi_machine_study.py`,
`python3 -m glm_universal.tools pi-machine`), recomputed live in about three
seconds; no stored measurement.

## 2. The control

Machin's formula with `239` replaced by `237`, summed by the same loop and
widened by the same bound, must give an interval disjoint from Mathlib's
twenty-digit decimals of π. Two proved enclosures of one number must
intersect; a wrong formula's interval must not, so the constant Phase 163
used stays in the study as the check on the formula.

## 3. What is not claimed

The number of terms (40 and 12) is chosen, not derived: a round pair whose
enclosure certifies all 40 terms the tool answers (`(30, 9)`, the first pair
tried, certifies 37); no search for the smallest such pair was made. The machine's lines are checked against the Lean
definition by running them and comparing integers (M1), and the Python mirror
against Lean's own evaluation at one small point; the GLM-BAT interpreter
itself is not proved in Lean. The other reals stay carried.

## 4. Faculties

**Derivation.** π, the last real constant the machine read as a declared
value, is now derived by the machine from integers by proved rules.

## 5. The marks

| mark | what is met |
|---|---|
| **L1** | `PiMachine.lean` states `machin`, `arctan_series_bound`, `atH_div`, `atH_arctan_sum`, `pi_series_bound`, `piEnds_enclose` with no `sorry`, and builds |
| **M1** | GLM-BAT run on `pi_lines` halts with exit 0 and leaves exactly `piEnds 40 12`; the Python mirror's `piEnds 3 1` equals Lean's `#eval` |
| **M2** | the summed enclosure lies strictly inside Mathlib's decimals and is narrower than 10⁻⁵⁶ |
| **M3** | it certifies at least the declared constant's terms, at least the tool's 40, and every term equals the tool's |
| **C1** | the 237-for-239 interval is disjoint from Mathlib's decimals |
| **K1** | the 80 one-step π chains (convergents 1–30, the term at every index below 40, the nearest fraction under 10¹ … 10¹⁰), run with the switch off and on: none admitted off is lost on, and none is written where the tool refuses; every chain the tool answers is admitted on |

A further gate, outside the marks: the end-to-end evaluation returns the same
answers and refusals (223 of 223).

## 6. How it is measured

`lake build RequestProject.GLM.PiMachine` from the repository root;
`PYTHONPATH=. python3 -m glm_universal.tools pi-machine` from `overlay/`;
`tests/test_pi_machine.py`.

## 7. What came out

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | 6 of 6 theorems, 0 `sorry`; `lake build RequestProject.GLM.PiMachine` passes; `piEnds_enclose` uses `propext`, `Classical.choice`, `Quot.sound` | yes |
| **M1** | halted, exit 0, 335 steps, 35 lines; ends equal; `piEnds 3 1` = (70364361601808/22397679609375, 23455225520344/7465893203125) both sides | yes |
| **M2** | width 9.563 × 10⁻⁵⁸ against 1.000 × 10⁻²⁰; nested | yes |
| **M3** | 53 terms certified against 19; the tool's 40 agree | yes |
| **C1** | disjoint, with a gap of 1.412 × 10⁻⁴ | yes |
| **K1** | 80 questions, all answered by the tool; admitted 47 off, 80 on; lost 0; gained 33 (convergents 20–30, terms 20–40, the nearest fraction under 10¹⁰); written where the tool refuses 0; at most 1,571 machine steps | yes |

The gate: 223 of 223 evaluation cases, no answer or refusal from answering
code moved. As in Phase 165, the two pins that measure the Lean corpus moved
with the new Lean file once the corpus was refreshed, and were re-pinned with
their claims unchanged: `report relay` 687 → 689 of 811 to 671 → 675 of 812
(still ahead on every set, carrying 9, losing 0), `report anonymous` text
687 → 63 of 811 to 671 → 60 of 812, structure 166 → 167 to 170 → 171; the
query-escalation measurement, which reads the evaluation file, was re-taken.
The full
`lake build` passes (240 files under `GLM/`, 0 `sorry`).

The tool-machine study's stored measurement, whose digest covers
`tool_machine.py`, was re-taken (`tools tool-machine --write`) with the same
marks met and missed as before. Its held-out control is unchanged (2,785 of
2,785 admitted, every lie refused); its paired frozen path (off and on in the
same run) keeps 703 of 703 texts the same; the largest machine-step count is now a π
question, *the first convergent of pi whose denominator is above 1000*, at
3,046 steps (it was an `e` question at 2,402).

### 7.2 What this answers

The machine sums π itself, and from its own enclosure certifies 53 terms of
π's continued fraction. The 33 gained chains were refused before because
the declared constant's enclosure was too wide to certify their terms, not
because they were wrong: with the summed enclosure the machine reaches every
term the tool gives. The first measurement used `(30, 9)` terms, which
certified 37 and left three term questions refused (honest stops, exit 2);
the declaration was raised to `(40, 12)` before the marks were taken as
final, and §3 says so. One defect was found and fixed on the way: the
first version of the marks module printed the widths through Python floats,
which made the blueprint report count one more module in the core
constructing floats and turn one of its confirmed claims to refuted (26 → 25
confirmed). The widths are now written by integer arithmetic, the report is
back to 26 of 39, and the stored measurements were re-taken after the fix.

### 7.3 What is left

* Reals other than π, `e` and `√m` stay carried.
* The generating-function procedure for the Leech shells `t ≥ 3` is still
  argued, not proved.
* The census behind a kissing-number question (about 164,000 machine steps)
  could be cached by digest.
