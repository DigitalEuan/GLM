# The loop through the planner: derivations as program values, questions about programs, and one surface's answer choosing the next step

## Tier 0 — the coarse read

**Question.** Can a program in the GLM's Python dialect hold what the planner and the reverse surface derive — and so let one surface's answer choose the next question put to another — and can the planner hand a question about a Python expression to the evaluator, without answering anything wrongly?

**Verdict.** Yes: the dialect now calls the stepwise planner and the reverse surface as values (`derive`, `ask`, `solve`), a declared frame hands a question about a Python expression to the evaluator, and every answered program's column-3 script re-runs each sub-answer's own script before it binds the value, with every declared case as declared and 0 wrong.

**Deciding figure.** 44 of 44 declared cases as declared (12 derive, 8 ask, 6 solve, 8 loop, 10 frame), 0 wrong; through the router the machine answers 29 of the 29 answer cases and answered 0 of them before the round; the dialect alone answers 0 of the 34 bridge cases; 22 of 22 bridge programs' scripts verified, re-running 47 sub-answer scripts, with all 66 mutations rejected; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.planner_loop_report.planner_loop_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 2 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md): the
loop through the planner, which is three items of [`STATUS.md`](../STATUS.md)
§3.4 that were one piece of work under three letters —

* **K4** ([`CONNECTED_MACHINE_STUDY.md`](CONNECTED_MACHINE_STUDY.md) §6):
  *a builtin `derive(target, y, z)` would make a derivation a value a program
  can use*;
* **I2** ([`PYTHON_SPEECH_STUDY.md`](PYTHON_SPEECH_STUDY.md) §7): *a question
  such as "what does `sum(range(3, 100, 7))` return?" could route through a
  typed frame to `speak`*;
* **O3 = M3** ([`REVERSE_TCT_STUDY.md`](REVERSE_TCT_STUDY.md) §12,
  [`STEPWISE_PLANNER_STUDY.md`](STEPWISE_PLANNER_STUDY.md) §6): *the planner's
  answer chooses the next reverse operation*.

K4 makes a derivation a value a program can hold; I2 makes a program's
expression a question the planner can hold. They are the two directions of
one bridge between the dialect and the rest of the machine, and O3 is the loop
that runs across it. Before this round the machine had every piece — the
stepwise planner derives across wheels, the reverse surface solves linear
statements with certificates, the dialect has `if`, `while`, `for` and
functions — but no surface could use another's answer: each question was
answered alone, and a question whose second step depended on the first
answer's *value* (not just its text) had no reader at all.

## 1. The objects

* **Three dialect builtins that call the rest of the machine**
  ([`reasoning/python_speech.py`](../overlay/glm_universal/reasoning/python_speech.py),
  `b_derive`, `b_ask`, `b_solve`):
  * `derive(target, (name, value), ...)` — the stepwise planner's goal mode,
    *given name = value, …, what is the target*. A value is an `int`, a
    `Fraction` or a `unit(value, name)`; the answer is a `Fraction`.
  * `ask(question)` — one stepwise-planner question in English: a register
    lookup, a composition, a comparative. A number comes back a `Fraction`,
    *prime* / *not prime* a `bool`, a named row a `str`. A single register
    lookup (*the density of gold*), which the stepwise planner leaves to the
    typed planner when it is asked alone, is read here as a one-step chain
    (`stepwise.compose(..., single=True)`), so its record carries a re-checked
    lookup step.
  * `solve(var, equation, (name, value), ...)` — the reverse surface's
    `solve for var: equation`, with the named program values written into the
    equation as exact literals. The equation is written in Python with `==`;
    a unique linear solution `var = v` is the `Fraction` `v`.

  Each refusal of the surface asked is the program's refusal by name —
  `DERIVE_REFUSED`, `ASK_REFUSED`, `SOLVE_REFUSED`, with the surface's own
  refusal (`NO_DERIVATION`, `VALUE_MISSING`, `NONLINEAR`, …) in the reason.
  Without the runtime's bridge — the dialect as the reasoning layer runs it —
  each refuses `BRIDGE_UNAVAILABLE`.
* **The bridge** ([`runtime/planner_bridge.py`](../overlay/glm_universal/runtime/planner_bridge.py)):
  the runtime object handed to `speak`. Each call returns the value and the
  surface's own checked record: the stepwise chain (its data and its column-3
  script) or the reverse certificate (its read-back and its column-3 script).
  The reasoning layer still starts no process and calls no planner; the
  bridge lives in the runtime, beside the router that already calls both.
* **Column 3 across surfaces** (`python_speech._SCRIPT_BRIDGE`). A bridge
  program's script, for each call, checks three things before it binds the
  value into the plain-Python prelude's table: the record's data is the data
  its script runs on; the record's own script prints `VERIFIED True` in a
  fresh `python3 -I`; and the value is bound to the record — the chain's last
  step for a chain (and the chain answers the question the program built),
  and for a solve the certificate's `var = v`, plus an independent check
  written into the script itself: `v` satisfies the equation as Python
  evaluates it over `Fraction`, and the equation is affine in `var` with
  non-zero slope, so `v` is its only root. Then the whole program is re-run
  under CPython against the table. A call whose answer is not in the table is
  refused in the script exactly as the dialect refuses it.
* **The frames of I2** (`planner_bridge.frame_of`): *what does `E` return*,
  *what is the value of `E`*, *what is `E`*, *evaluate `E`* and *is `E`
  true*, where `E`, the text between backticks, must itself be read by the
  dialect. The router's python surface reads a framed question and hands `E`
  to the evaluator (with the bridge, so `E` may call `derive`); *is `E` true*
  needs a `bool` and is refused `NOT_A_TRUTH_VALUE` otherwise.
* **The loop (O3 = M3)** is the program's own control flow. A branch on a
  derived value chooses which reverse question is asked; a `while` asks the
  planner again until its answer crosses a bound; a solved value feeds a
  derivation; a register value feeds a wheel. No new grammar was written for
  it: the dialect already had the control flow, and what it lacked was a way
  to hold the other surfaces' answers.

## 2. Declarations — written before any code of the round

The corpus is [`evaluation/planner_loop_cases.py`](../overlay/glm_universal/evaluation/planner_loop_cases.py),
committed before any code of the round with its marks: 12 derive, 8 ask, 6
solve, 8 loop and 10 frame cases, every expected value worked by hand in exact
fractions from the wheels' axioms, the element register's own values and
ordinary algebra, and 5 English paraphrases of the loop programs for the
reading of §5.

| mark | what it requires |
|---|---|
| W1 | every derive case as declared, 0 wrong |
| W2 | every ask and solve case as declared, 0 wrong |
| W3 | every loop case as declared, 0 wrong; the bridge-off control (the dialect alone) answers none of the bridge cases and refuses each by name |
| W4 | every frame case as declared; on the earlier declared question sets the frames change the surface of no question |
| W5 | every answered bridge program's column-3 script verifies in a fresh interpreter, re-running every sub-answer's own script, and every mutation (`bridge-lie`, `chain-lie`, `answer`) is rejected |
| W6 | through the router the machine answers every answer case of the corpus; before the round it answered none of the bridge cases |
| W7 | nothing earlier moves: the dialect's declared value and refusal cases, its differential battery (0 wrong) and the stepwise planner's declared chains as they were |
| W8 | the facts the round rests on proved in Lean, without `sorry` |

The three mutations: `bridge-lie` alters the value a call returned and
nothing else; `chain-lie` alters a sub-answer's record and the value
consistently, re-rendering the sub-answer's script from the lied record; and
`answer` alters the program's final claim.

## 3. What was built

* In [`reasoning/python_speech.py`](../overlay/glm_universal/reasoning/python_speech.py):
  the builtins `derive`, `ask`, `solve`; an `Evaluator` that takes a bridge,
  asks each distinct question once per run, and records a `bridge` step per
  call; `speak(source, bridge=...)`; the payload's `bridge` records; and the
  column-3 block that re-runs the records' scripts and binds their values.
* In [`reasoning/python_substrate.py`](../overlay/glm_universal/reasoning/python_substrate.py):
  the four refusal names, and the prelude's `derive`, `ask` and `solve`, which
  build each question exactly as the evaluator does and read the checked
  table — so column 3 also checks that the two sides build the same question.
* [`runtime/planner_bridge.py`](../overlay/glm_universal/runtime/planner_bridge.py):
  the bridge, the frames, `speak_text` (the one place the router and the
  command line read a program or a frame) and the declared mutations.
* In `runtime/router.py`: the python surface reads a framed question and
  hands the dialect the bridge (switches `BRIDGE`, `FRAMES` for the
  controls); in `runtime/stepwise.py`: `compose(..., single=True)`, used only
  by `ask`; in `GLM.py`: `--ask` and `--python` print a bridge program's
  steps and a frame's refusal.
* The measurement [`runtime/planner_loop_report.py`](../overlay/glm_universal/runtime/planner_loop_report.py),
  the command `tools planner-loop`, `tests/test_planner_loop.py` (16 tests),
  and [`RequestProject/GLM/PlannerLoop.lean`](../overlay/glm_lean/RequestProject/GLM/PlannerLoop.lean).

## 4. Results

Recomputed by `PYTHONPATH=. python3 -m glm_universal.tools planner-loop`.
Yes on every mark: all eight are met on the first reading. In total 44 of 44
declared cases are as declared (12 derive, 8 ask, 6 solve, 8 loop, 10
frame), 0 wrong, and all 66 declared mutations (22 of each kind) are
rejected.

| mark | result |
|---|---|
| W1 | met: 12 of 12 derive cases as declared, 0 wrong (7 answered, 5 refused by name) |
| W2 | met: 8 of 8 ask cases and 6 of 6 solve cases as declared, 0 wrong |
| W3 | met: 8 of 8 loop cases as declared, 0 wrong; the dialect alone answers 0 of the 34 bridge cases and refuses all 34 by name (31 `BRIDGE_UNAVAILABLE`; the other 3 are refused before any call — a float literal, and two calls of the wrong shape) |
| W4 | met: 10 of 10 frame cases as declared; 0 of 530 questions of the earlier declared sets change surface |
| W5 | met: 22 of 22 bridge programs' scripts verified, re-running 47 sub-answer scripts; 22 of 22 `bridge-lie`, 22 of 22 `chain-lie` and 22 of 22 `answer` mutations rejected |
| W6 | met: through the router the machine answers 29 of the 29 answer cases; before the round it answered 0 of them (0 of the 34 bridge cases) |
| W7 | met: 83 of 83 declared dialect values and 26 of 26 refusals unchanged, 0 wrong over the 7,128-pair differential battery, and the stepwise planner's earlier rounds held |
| W8 | met: `RequestProject/GLM/PlannerLoop.lean`, no `sorry`, standard axioms only |

Every mutation was caught at the check written for it: each `bridge-lie` at
the binding check (the value is not the record's), each `chain-lie` at the
re-run of the sub-answer's own script (the lied step does not recompute), and
each `answer` at the final re-run of the program.

Three programs worth reading in full.

*`l02`* — the least whole resistance at which the current at 12 volts falls
below one ampere:

```python
r = 1
while derive("current", ("voltage", 12), ("resistance", r)) >= 1:
    r = r + 1
r
```

answers `13`. The planner is asked thirteen distinct goal questions, each
answered by a three-step chain over wheel W1; the program's column 3 re-runs
all thirteen chain scripts before re-running the loop. The router, asked the
same question in English, refuses it (§5).

*`l01`* — a derived value chooses the reverse question:

```python
p = derive("power", ("voltage", 12), ("resistance", 4))
if p > 30:
    t = solve("t", "p * t == 7200", ("p", p))
else:
    t = solve("t", "p * t == 3600", ("p", p))
t
```

answers `Fraction(200, 1)`: the planner's 36 takes the first branch, and the
reverse surface solves `36 * t == 7200` with a certificate whose column-3
script, and the program's own substitution check, both re-run.

*`l08`* — a register value feeds a wheel through the program:
`m = ask("the melting point of iron")` is a one-step lookup chain whose
script re-reads the register; `derive("energy", ("temperature", unit(m,
"kelvin")), ("entropy", 2))` is `3622`.

## 5. Item 9, re-read: the utility gate

The roadmap asked that the loop be re-read against item 9 of
[`STATUS.md`](../STATUS.md) §3.4 — *whether a tool exists that a
problem-driven front end could reach and the kind-driven dispatcher cannot*
([`REVERSE_CALL_PLANNER_STUDY.md`](REVERSE_CALL_PLANNER_STUDY.md)). Asked
directly, the router answers **0 of the 5** English paraphrases of the loop
programs (`l01`, `l02`, `l03`, `l07`, `l08`): each needs one surface's answer
to choose the next step, and the kind-driven dispatcher sends a question to
one surface. The same five questions, written as programs, are answered and
re-checked. So there is now a reach of the kind item 9 asked about: a program
is a problem-driven front end over the declared surfaces, and it reaches
answers the dispatcher does not.

What this does **not** change: the supplied reverse-call planner of that
study is still not promoted. Its gate was measured on the evaluation set's
refusals, and those are refusals it agrees with; nothing here re-runs that
measurement. The finding is narrower and is recorded as a reading, not a
mark: the loop is the first tool reachable by composition that no single
surface reaches.

## 6. What this round moved

**Derive** — answers no surface gives alone: a quantity searched for by a
loop over derivations, a reverse solve whose equation holds a derived value,
a derivation fed by a solved value or a register value, each with every
sub-answer re-checked by its own script. **Refuse** — a surface's refusal
reaches the program by name, and no answer is given that rests on a refused
call (`run_eq_none_of_refused`); a frame whose expression is not a truth value
is refused rather than read as one. **Address** — a question about a Python
expression in English now reaches the evaluator.

## 7. The Lean file

[`RequestProject/GLM/PlannerLoop.lean`](../overlay/glm_lean/RequestProject/GLM/PlannerLoop.lean)
models a program as a tree that returns a value or calls an oracle at a key
and continues with the answer, and proves, with the standard axioms only:

* `run_eq_of_agree` — a table that agrees with the oracle at every key the
  run asks gives the same verdict, which is why column 3's table of checked
  answers is enough; `run_restrict` — the oracle restricted to the asked keys;
* `isSome_of_run_eq_some` — an answered run had an answer at every key it
  asked; `run_eq_none_of_refused` — a refusal at any asked key is the run's
  refusal;
* `affine_slope_ne_zero`, `affine_root_unique`, `affine_second_difference` —
  the binding check of a solved value;
* `least_resistance_thirteen` — the declared loop `l02`.

## 8. What this leaves

* **The relay's side of O3.** `relay:` still hands only the planner's
  approximation and recognition questions; letting it read the integer
  certificate kinds (a bound's witness, an `INDEPENDENT` verdict's two
  integer points) and hand an `INDEPENDENT` witness to the question layer as a
  follow-up — [`REVERSE_TCT_STUDY.md`](REVERSE_TCT_STUDY.md) §12's last
  item — is unchanged, now as a smaller piece beside a working loop.
* **More of the machine as values.** The engineering surface's other frames
  (the Smith chart, the analogies), the reverse surface's `bounds of` (an
  interval, which needs the third sort of track 5) and `entails` (a verdict
  with a witness) are not yet builtins.
* **Follow-ups across the bridge.** A program's answer is not yet bound as a
  conversational *it* (candidate K3, track 4 of the roadmap).
* **A held-out set** (candidate B = O1): every program here was written by the
  project, as every corpus before it.
