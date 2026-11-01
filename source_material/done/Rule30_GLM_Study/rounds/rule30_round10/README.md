# Round 10: the GLM works through Rule 30 step by step

The formal results of this round are in the Lean package, in
`RequestProject/GLM/Rule30/WheelInduction.lean` and `RequestProject/GLM/Rule30/Observer.lean`
(see "Round 10" in the package README). This folder holds the GLM side. Nothing in it is a proof:
each value it reports either names the Lean theorem it comes from or is marked `EMP` (an exact
computation, not a theorem).

## 0. Is the GLM "fully online"?

The parts of the GLM that are in `glm_repo.zip` are online: the session, its registers, the reports
and the new automata carriers. The connected command line, `tool induce` and `tool arc` are not,
because the archive lacks 22 modules they import. `GLM_AVAILABILITY.md` lists every missing module
and what it blocks, and `find_missing_modules.py` re-checks a checkout. The new wheel-induction
family was therefore run here directly. `toolbox_wheel_induction.patch` puts it behind `tool induce`
in your full tree. It was tested against `toolbox.py` with a placeholder for the missing
`colour_induction` (test only, not shipped).

## 1. Setup (after the Round 9 setup, from the directory holding `GLM.py`)

```
cp -r rule30_round10/glm_glm_universal/.  glm_universal/
PYTHONPATH=. python3 rule30_round10/test_round10.py          # "round 10: all checks pass"
PYTHONPATH=. python3 rule30_round9/test_automata.py          # still passes
PYTHONPATH=. python3 rule30_round10/glm_round10_probe.py     # = glm_round10_probe_output.txt
# in your full checkout, to route `tool induce` to the wheel family when no kit family fits:
patch -p1 < rule30_round10/toolbox_wheel_induction.patch
```

| File | Goes to | What it is |
|---|---|---|
| `glm_glm_universal/data_objects/automata.py` | `glm_universal/data_objects/` | the Round 9 register plus the Round 10 carriers (below) |
| `glm_glm_universal/runtime/wheel_report.py` | `glm_universal/runtime/` | `describe` for the new carriers; four new `report` subjects |
| `glm_glm_universal/reasoning/wheel_induction.py` | `glm_universal/reasoning/` | the radius-1 wheel family: fit, survivors, answer or refuse |
| `toolbox_wheel_induction.patch` | `glm_universal/runtime/toolbox.py` | `tool induce` falls back to the wheel family when no kit family fits |
| `test_round10.py` | | plain-assert self-test; each check names the Lean theorem it mirrors |
| `glm_round10_probe.py`, `glm_round10_probe_output.txt` | | 22 session queries, 4 induction tasks, the observer readings |
| `GLM_AVAILABILITY.md`, `find_missing_modules.py` | | what the archive lacks |

`session.py` and `parser.py` are unchanged from Round 9. The new report subjects reach
`wheel_report` through the Round 9 routing.

## 2. Rule 30, step by step, in the GLM's own language

**Step 1: the run.** Ask `report wheel steps` or `describe r30_step_t` for `t < 64`. Each step shows:
* the row on its light cone;
* the centre neighbourhood `(L,C,R)`;
* the rule evaluated over GF(2), `L + C + R + C·R`;
* the new accumulator `D(t+1)` and the arrow `−sign D`.

The step law is `ecaEvolve_succ` in Lean; the values are exact computations (`EMP`). Example
(`describe r30_step_5`): row 5 is `11011110111`, the centre neighbourhood is `(1,1,1)`, and
`a(6) = 1+1+1+1 = 0 (mod 2)`, `D(6) = 4`, arrow `−1`. Over the first 1000 steps all eight
neighbourhoods occur above the centre cell; `report wheel steps` gives the counts (an exact
count, not a theorem).

**Step 2: which wheel made this?** This is the ARC-style reading: `report wheel induction`,
`describe r30_induction_rows_T`. The GLM's existing induction families (permutations, XOR masks,
shifts, compositions) find nothing: `unsolved`, 0 of 76 hypotheses fit. The new wheel family
gives:

| Demonstrations | Surviving wheels | Unseen | Next row |
|---|---|---|---|
| rows 0..1 | 16 | 011, 101, 110, 111 | refused |
| rows 0..2 | 2: {30, 62} | 101 | **answered** (row 3 does not use 101) |
| rows 0..3 | 2: {30, 62} | 101 | **refused** (row 3 contains 101) |
| rows 0..4 | 1: {30} | none | answered |

Lean results behind the table:
* `rows_identify_thirty`: rows 0..4 determine 30 among all 256;
* `rows_three_do_not_identify`, `row_four_not_determined`: wheel 62 shares rows 0..3;
* `next_row_determined_iff`: the refusals are exact. Every fitting wheel agrees on the next row
  iff the query row uses only neighbourhoods already shown.

The engine checks both refusal criteria against each other on every call.

**Step 3: what one column can tell** (`report wheel observer`, `describe r30_observer_column_c`,
`m3` for −3).

| Observer at column | −5 | −4 | −3 | −2 | −1 | **0** | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| values needed | 10 | 10 | 8 | 12 | 11 | **7, and only gets {30, 86}** | 8 | 8 | 12 | 11 | 13 |

* Centre (Lean `centre_column_class`): the centre column is produced by exactly wheels 30 and 86,
  so the centre observer can never tell left from right.
* Off-centre (Lean `column_one_identifies`, `offCentre_column_identifies`): every column with
  `1 ≤ |c| ≤ 5` determines wheel 30.
* The exact least numbers for `|c| ≥ 2` are `EMP`.

**Step 4: the frame and the arrow** (`report wheel perspective`, `describe r30_arrow_mirror`,
`describe r30_arrow_colour`). This is your Wobble-as-perspective idea, made exact:

| Change of frame | Effect on the arrow `−sign D(N)` | Lean |
|---|---|---|
| mirror (`c ↦ −c`; wheel 30 ↦ 86) | unchanged, for every `N` | `observerArrow_mirror`, `observerArrow_eightySix` |
| colour swap (wheel 30 ↦ 135, complemented impulse) | reversed, for every `N` | `observerArrow_complement`, `observerArrow_oneThirtyFive` |
| time reversal (read the first `N` values backwards) | accumulator after `k` steps is `D(N) − D(N−k)` | `wobble_reverse` (Round 2) |

So the arrow does carry a perspective, but only the **colour frame** (which colour the observer
`Y` calls black). It carries no left/right information. The left/right frame is invisible from
the centre column altogether. It becomes readable one cell off-centre within 8 steps. In GLM
terms, the `Y` that knows "which way it is looking" must sit off the centre line.

**Step 5: the questions.** `describe r30_question_aperiodicity` and the other two still answer
`OPEN`. `real value r30_question_balance` refuses and gives the exact statement. Steps 1–4 are
about the rule and the frame, not the limit. Because 30 and 86 have the same centre column, a
proof of P1 or P2 can only use what the two mirror images share.

## 3. On Qwen's reading of the Round 9 output

Most of it is accurate. The `[carrier]`, `[evidence]`, `[recomputation]`, `[arrow]` and
`[boundary]` steps do what it says, and the E2 and E6 guardrails are deliberate. Three corrections:

* The symmetries were not "automatically discovered" by the GLM. They are proved in Lean
  (`ElementaryCA.lean`: `ecaEvolve_mirror`, `ecaEvolve_complement`, `card_equivalence_classes = 88`)
  and written into the register.
* `SeedFSTypical` is a **sufficient** bridge (`SeedFSTypical ⇒ P1 ∧ P2`), not "the only missing
  bridge". It is itself open in both directions, and a proof of P1 or P2 need not go through it.
* Problem 2 is balance (frequency 1/2, equivalently `D(N)/N → 0`), not full normality.
