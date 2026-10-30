# Constant bounds and repeated output — two more counter lassos

## Tier 0 — the coarse read

**Question.** Can GLM-BAT's counter-lasso reading also jump a pass that writes the same lines on every pass, and a pass whose counter is compared with a variable that is not a counter, so that the two halting controls Phase 130 refused (L10, L11) are answered exactly, without changing any verdict it already gave and without a verdict a long plain run contradicts?

**Verdict.** Yes, within the declared rule, with one mark missed on how the hand-worked battery named its jumps. All 10 battery programs came out with the declared verdict, step count, outputs, standard error and exit code, and 0 wrong: L10 (as K1) halts after 60,002 steps printing `tick` 20,000 times, L11 (as K2) after 40,003, and four more loops of 90,002 to 150,004 steps are answered exactly, one constant-bound loop is certified never to halt, and three controls are refused. For K6 and K10 the declared jump named a pass one line before the masked state's first recurrence, so 8 of 10 are exactly as declared and mark B2 is missed. The 15 questions, the certificates, non-interference on every earlier answer and all 300 generated programs, and the soundness control against plain runs were all met.

**Deciding figure.** 6 of 7 marks; 10 of 10 programs with the declared verdict and end, 8 of 10 with the declared jumps; 15 of 15 questions as declared; 18 of 18 column-3 scripts verify and 112 of 112 mutations rejected; 300 of 300 generated programs unchanged; 6 of 6 jumped *halts* equal to a plain run, 0 of 2 *never* halting in 200,000 steps.

**Recomputed by.** `glm_universal.reasoning.constant_bound.constant_bound_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 131, committed with its Lean file and before
the code of the rule exists. §§0–6 are as they were committed; §7 is what
came out.

It takes two lines of *GLM-BAT, the rest* in [`STATUS.md`](../STATUS.md) §2.2,
left by Phase 130 ([`COUNTER_LASSO_STUDY.md`](COUNTER_LASSO_STUDY.md) §7.4):

* **passes that write output** (L10) — a jump must state the output it
  skipped; the output of a pass whose written lines name no counter is the
  same block on every pass;
* **comparisons with a variable that is not a counter** (L11) — a variable
  read from the rest of the state is the same at the same step of every pass,
  and can be read as a literal.

Both controls halt (L10 after 60,002 steps, L11 after 40,003; Phase 130 §7.2,
C6), so each refusal was a cost of the rule, not a protection.

**Why not an item of §2.1.** Items 1–4 of §2.1 each change answers the
evaluation pins and need a frozen-path comparison of the answering path;
item 1's premise was found not to hold in Phase 130 (no query kind reads a
carrier by its address yet). This round, like Phase 130, adds a faculty the
machine lacks and is bound by the same non-interference marks.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 130's record: L10 and L11
   refused `UNDECIDED_WITHIN_BUDGET`, halting plainly after 60,002 and 40,003
   steps. Nothing else about any program below had been run.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/ConstantBound.lean` was written and built first (§1).
3. **No code of the rule existed and no program below had been run under it
   when this was committed.** Every expected answer in §3 was worked out by
   hand from the semantics of
   [`OPERATIONS_LADDER_STUDY.md`](OPERATIONS_LADDER_STUDY.md) §2.2 and the
   rule of [`COUNTER_LASSO_STUDY.md`](COUNTER_LASSO_STUDY.md) §2.

## 1. What is proved before any code

`RequestProject/GLM/ConstantBound.lean`, no `sorry`, standard axioms only, on
top of `RequestProject/GLM/CounterLasso.lean` (the split of the state into a
part `C` and counters `ι → ℤ`, and `shift`).

* `wrun` — `run` with the lines each step writes collected (`emit s` for the
  step from `s`); `wrun_fst` — forgetting the lines gives the plain run;
  `wrun_add` — two runs in a row write the first's lines, then the second's.
* `wrun_pass` — a pass from the start translated by `m • d`, each step of
  which commutes with that translation and writes lines that do not read the
  counters, ends at the start translated by `(m + 1) • d` having written
  exactly the first pass's `block`.
* `lasso_output` — so `K` passes write that block `K` times over, in `K * p`
  steps.
* `halts_of_jump_output` — run `i` steps writing `w₀`, jump `K` passes, run
  `n` steps writing `w₁` to a state with no successor: the machine halts after
  exactly `i + K * p + n` steps, having written `w₀`, the block `K` times, and
  `w₁`.
* `shift_fst` — a translation never moves the part `C`.
* `testStepC`, `testC_equivariant` — a test reading the counters *and* the
  part `C` commutes with a translation exactly while its outcome is unchanged.
* `const_bound_linear`, `const_bound_linear'` — at pass `m`, a counter `a`
  against a bound `L` read from `C` differs by `(x_a − L) + d_a·m` (or
  `(L − x_a) − d_a·m`): Phase 130's linear form with the bound folded into
  `e₀`, so `first_change` applies unchanged.

The theorems do not say the Python's reading of a line is right; the column-3
script checks that with its own reading (§2).

## 2. The rule

Everything of [`COUNTER_LASSO_STUDY.md`](COUNTER_LASSO_STUDY.md) §2 stands;
two clauses are added, and the reading with them is called the *extended*
reading (Phase 130's is kept, as `extended=False`, so that its record can be
re-measured).

**Constant operands.** In a test `IF [NOT] a OP b body` on a pass, an operand
may also be `%L%` where `L` is not a live counter, is not `ERRORLEVEL`, and is
bound at that step to a canonical integer (`str(int(v)) == v`). It is read as
the literal of that value (slope 0). The test must still mention a live
counter, its body must mention none, and `a`, `b` must be counters, literals
or such constants.

**Passes that write.** A pass with a first change `m* ≥ 2` that writes lines
to either output stream is jumped when no line executed on the pass is of
the `echo` kind (an `ECHO` that names a live counter) — so every line written
on it comes from a line naming no live counter, or from a test body naming
none — and when the output after the jump would hold at most
**100,000 lines** (standard output and standard error together). The jump
appends the pass's standard-output block and its standard-error block, each
`m* − 1` times (`lasso_output`). Otherwise the pass is gone on from, as
before.

**When it is used.** As in Phase 130: only when the Phase 125 run and the
Phase 126 inert re-reading are both undecided.

**What the GLM says.** *Does it halt?* as in Phase 130, with ", writing *k*
lines each time" after "was taken *m* times in one jump" when the pass
writes. *What does it print?* of a run with a jump over a writing pass
states runs of equal consecutive lines as `"tick" (50000 times)`; every other
answer text is as before. The `run_jump` and `never_lasso` claims keep their
shape; the column-3 checker gains both clauses with its own reading, and its
script is handed to the interpreter on standard input (a claim holding tens
of thousands of output lines is past the length of one command-line
argument).

## 3. The marks, declared before the code

The battery (lines separated by ` / `; steps count from 0; "jump `(i, j, m)`"
as in Phase 130):

| program | lines | expected |
|---|---|---|
| K1 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO tick / IF %N% LSS 20000 GOTO UP` (L10) | halts after 60002 steps, out `tick` × 20000, exit 0, `N` = 20000; jump `(2, 5, 19999)` |
| K2 | `SET /A N=0 / SET L=20000 / :UP / SET /A N=N+1 / IF %N% LSS %L% GOTO UP` (L11) | halts after 40003 steps, out nothing, exit 0, `N` = 20000; jump `(3, 5, 19999)` |
| K3 | `SET /A N=0 / SET LIM=50000 / :UP / ECHO tick / SET /A N=N+1 / IF %N% LSS %LIM% GOTO UP / ECHO %N%` | halts after 150004 steps, out `tick` × 50000 then `50000`, exit 0; jump `(3, 6, 49999)` |
| K4 | K3 with `LIM=500000` | refused `UNDECIDED_WITHIN_BUDGET` (the output would pass 100,000 lines) |
| K5 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / IF %N% LSS 20000 GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (the pass writes a counter) |
| K6 | `SET /A N=0 / SET L=7 / :UP / SET L=30000 / SET /A N=N+1 / IF %N% LSS %L% GOTO UP / ECHO %N%` | halts after 90004 steps, out `30000`, exit 0, `N` = 30000; jump `(6, 9, 29998)` (the bound is set on the pass; the first pass is not a recurrence) |
| K7 | `SET /A N=0 / SET L=-5 / :UP / SET /A N=N+1 / IF %N% GTR %L% GOTO UP / ECHO unreachable` | never; pass `(3, 5)`, `d`: N +1 |
| K8 | `SET /A N=0 / SET L=abc / :UP / SET /A N=N+1 / IF %N% LSS %L% GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (`abc` is not an integer; the comparison is of text) |
| K9 | `SET /A N=40000 / SET L=0 / :DOWN / ECHO %L% / SET /A N=N-1 / IF %L% LSS %N% GOTO DOWN / ECHO lift-off` | halts after 120004 steps, out `0` × 40000 then `lift-off`, exit 0; jump `(3, 6, 39999)` |
| K10 | `SET /A N=0 / :UP / SET /A N=N+1 / TYPE missing.txt / IF %N% LSS 30000 GOTO UP` | halts after 90002 steps, out nothing, standard error `The system cannot find the file specified.` × 30000, exit 1; jump `(5, 8, 29998)` (the first pass starts with exit code 0, every later one with 1) |

| mark | statement |
|---|---|
| **B1** | `RequestProject/GLM/ConstantBound.lean` builds with no `sorry` and only the standard axioms, with the theorems of §1. |
| **B2** | **The battery.** K1–K10 as declared, 0 wrong (status, step count, outputs, standard error where declared, exit code, values, jumps; certificate and `d` for K7). |
| **B3** | **The questions.** *Does it halt?* of K1–K10 as declared (yes with the step count and exit code; no; or the refusal); *what does it print?* of K3 has the value `tick` × 50000 then `50000`, and its text holds `"tick" (50000 times)`; *how many steps?* of K9 is 120004; *what is the exit code?* of K10 is 1; *what is the value of N?* of K6 is `30000`; *what does it print?* of K7 refuses `NEVER_HALTS` — 15 questions. |
| **B4** | **Certificates.** Every `run_jump` and `never_lasso` claim of B2 and B3 has a column-3 script that passes under `python3 -I`, and every mutation fails: Phase 130's mutations, and for a claim whose output holds a repeated line, that output with one copy of the line removed. |
| **B5** | **Non-interference on the machine.** The Phase 125 battery (25 runs), its 18 questions and its 6 English programs; the Phase 126 battery and questions other than N2 and N3; and the Phase 130 battery and questions other than L10 and L11, read with the extended reading, give the answers Phase 130's reading gives (status, certificate, `d`, steps, outputs, exit code, jumps; answer text, refusal and claim); L10 and L11 move to K1's and K2's answers. Every one of the 300 generated programs keeps its verdict, step count, outputs, standard error, exit code and files. |
| **B6** | **Soundness control.** Every program the extended reading says halts (battery or generated) halts when run plainly under 2,500,000 steps with the same step count, outputs, standard error, files, variables and exit code; no program it says never halts halts within 200,000 plain steps; and K4, K5 and K8, which are refused, are reported with their plain outcome under the long budget — K4 halts after 1500004 steps, K5 after 60002, and K8 does not halt within 2,500,000. |
| **B7** | **Non-interference on the system.** All 179 evaluation cases pass with 0 confidently wrong. Re-pins are allowed only for the retrieval figures that count goal queries sampled from the Lean development (`report relay`, `report anonymous`), which a new Lean file moves. |

**Not predicted:** whether any of the 300 generated programs takes a jump the
Phase 130 reading did not (a jump over a writing pass that Phase 130 ran out
concretely); B5 binds their answers either way, and the count is reported.

## 4. Controls

* **K4** is the control on the output bound: the same loop as K3, refused
  only because its output would pass 100,000 lines; B6 reports that it halts.
* **K5** is the control on the output rule: a pass whose written line names
  the counter writes a different line on every pass and must not be jumped.
* **K8** is the control on constants: a variable that holds text makes the
  comparison one of text, which the linear form does not describe.
* **K6** is the control that a constant is read at the step, not at the start
  of the run: the bound changes on the first pass, so the first recurrence is
  the second pass.
* **K10** is the control on standard error and the exit code inside a pass.
* **B6** is the control that does not trust the theorems or the reading.
* **The multiplicity count.** Phase 130 stood at 65 statistics; this round
  adds the battery, so **66**. No bit score is computed.

## 5. What this round does not do

* No jump over a pass whose written lines name a counter (K5): its output is
  an arithmetic progression of texts, which would need a closed form.
* No output past 100,000 lines from a jump (K4); a run-length statement of
  the claim itself is left.
* No constant read through `ERRORLEVEL`, and no comparison of text.
* No growth that is not a translation (L12, N5, N6), and nothing else of
  Phase 130 §7.4.
* No change to the fragment, the English reader or the sayer outside the two
  answer texts of §2, the planner, or any router path.

## 6. Files

* `RequestProject/GLM/ConstantBound.lean` — B1.
* `glm_universal/reasoning/batch_machine.py` — the two clauses in
  `jumped_run`, behind `extended` (default on), threaded through
  `run_program`.
* `glm_universal/reasoning/batch_speech.py` — the checker's two
  clauses, the answer texts, the mutation, the script on standard input, and
  `extended` threaded through `answer`.
* `glm_universal/reasoning/constant_bound.py` — the battery and the
  marks; `python3 -m glm_universal.tools constant-bound`.
* `glm_universal/reasoning/counter_lasso.py` — Phase 130's
  measurement, read with `extended=False` so that it keeps measuring the rule
  it declared.
* Tests: `test_constant_bound.py`.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`PYTHONPATH=. python3 -m glm_universal.tools constant-bound` takes every mark
except B1 and B7 in about a minute; `tests/test_constant_bound.py` (12 tests)
pins them as measured.

### 7.1 The verdict

Yes, within the declared rule, with one mark missed on how the hand-worked battery named its jumps. All 10 battery programs came out with the declared verdict, step count, outputs, standard error and exit code, and 0 wrong: L10 (as K1) halts after 60,002 steps printing `tick` 20,000 times, L11 (as K2) after 40,003, and four more loops of 90,002 to 150,004 steps are answered exactly, one constant-bound loop is certified never to halt, and three controls are refused. For K6 and K10 the declared jump named a pass one line before the masked state's first recurrence, so 8 of 10 are exactly as declared and mark B2 is missed. The 15 questions, the certificates, non-interference on every earlier answer and all 300 generated programs, and the soundness control against plain runs were all met.

### 7.2 The marks

| mark | what | result |
|---|---|---|
| B1 | the Lean file | **met**: `RequestProject/GLM/ConstantBound.lean` builds with no `sorry`; `#print axioms` gives `propext`, `Classical.choice`, `Quot.sound` for `lasso_output` and `halts_of_jump_output`, `propext` and `Quot.sound` for `const_bound_linear`, `propext` for `wrun_fst`, and none for `testC_equivariant` |
| B2 | the battery | **missed**: 10 of 10 with the declared status, step count, outputs, standard error, exit code and values (K1 60002, K2 40003, K3 150004, K6 90004, K9 120004, K10 90002 with exit 1; K7 never, pass `(3, 5)` adding 1 to N; K4, K5, K8 undecided), but 8 of 10 with the declared jumps: K6 jumps `(4, 7, 29999)`, not `(6, 9, 29998)`, and K10 jumps `(4, 7, 29999)`, not `(5, 8, 29998)` (§7.3) |
| B3 | the questions | **met**: 15 of 15 as declared |
| B4 | certificates | **met**: 18 of 18 `run_jump` and `never_lasso` scripts pass under `python3 -I`; 112 of 112 mutations fail |
| B5 | non-interference on the machine | **met**: Phase 125's 25 runs, 18 questions and 6 English programs as declared; the 18 programs and 22 questions of the Phase 126 and 130 batteries other than N2, N3, L10 and L11 give exactly the answers of Phase 130's reading; L10 and L11 give K1's and K2's runs; 300 of 300 generated programs unchanged in verdict, steps, outputs, standard error, exit code and files, and none takes a new jump |
| B6 | soundness control | **met**: all 6 jumped *halts* (K1, K2, K3, K6, K9, K10) equal a plain run in steps, outputs, standard error, files, variables and exit code; neither *never* (K7, generated 206) halts within 200,000 plain steps; the refused controls, plainly: K4 halts after 1500004 steps, K5 after 60002, K8 does not halt within 2,500,000 |
| B7 | non-interference on the system | **met**: 179 of 179 evaluation cases, 0 confidently wrong, after the two declared re-pins (§7.5) |

### 7.3 What was seen

* **The miss is in the hand computation, not in the rule.** K6 sets its
  bound on the pass (`SET L=30000` after the label) and K10 changes the exit
  code on the pass (`TYPE missing.txt`). Working them by hand, the declared
  jump looked for the first recurrence at the line after the label, where the
  first pass differs from the second (in `L`, in the exit code), and so put
  the jumped pass one pass later. The masked state is compared before *every*
  step, and it first recurs one line further on — after `SET L=30000` in K6,
  after `TYPE missing.txt` in K10 — where the first pass already agrees with
  the second. Both runs jump one pass earlier, 29,999 times instead of
  29,998, and end exactly where declared: the same step counts, outputs,
  standard error and exit codes, all equal to a plain run (B6). The battery
  mark binds the jumps, so it is recorded as missed; the controls the two
  programs were written for (a bound read at its step, the exit code inside a
  pass) behaved as intended.
* **The skipped output is stated exactly.** K1's answer to *does it halt?*
  reads "yes, it halts after 60002 steps with exit code 0 (the pass from step
  2 to step 5 adds 1 to N, and was taken 19999 times in one jump, writing 1
  line each time, until IF %N% LSS 20000 GOTO UP changed)", and its claim holds
  all 20,000 `tick` lines, which the second interpreter re-derives by its own
  jump. K3's *what does it print?* reads `it prints "tick" (50000 times),
  "50000"`. Standard error is repeated the same way (K10, 30,000 lines).
* **A constant on either side.** K9 compares the constant on the left
  (`IF %L% LSS %N%`) against a falling counter and prints the constant on
  every pass; both clauses are used at once.
* **The column-3 script went to standard input.** A claim holding 50,001
  output lines is about 400 kB, past the 128 kB the kernel allows one
  command-line argument; `run_script` now hands every script to
  `python3 -I -` on standard input, which changes no script and no verdict.
* **What the refusals cost.** K4 (output past the bound) and K5 (a pass that
  prints its counter) halt plainly; K8 (a comparison of text) does not halt.

### 7.4 What is left

* **Passes that print a counter** (K5): the output is an arithmetic
  progression of texts, which a jump would have to state in closed form.
* **Output past 100,000 lines** from a jump (K4): a run-length statement of
  the claim, so that the script need not hold every line.
* **Constants read through `ERRORLEVEL`**, and comparisons of text.
* **Growth that is not a translation** (L12, N5, N6), nested loops whose inner
  pass changes on every outer pass, and the rest of GLM-BAT (stream merging,
  `SORT` options, `FOR /F`, `SETLOCAL`, delayed expansion), as Phase 130 left
  them.
* **The statistics count** is now 66 (§4); no bit score was computed.

### 7.5 Non-interference on the system

The full evaluation, run after `corpus --refresh` with `ConstantBound.lean` in
the corpus, passed 177 of 179 cases with 0 errors before any re-pin; the two
that moved are the two B7 names, `report relay` and `report anonymous`, and
both moved only because the goal-query set sampled from the Lean development
grew from 835 to 837 queries. Re-pinned (comments in `evaluation/cases.py`):
the relay reads 720 -> 723 of 837 (ahead) on bare goal queries, the gate
fires on 40 of 1674 and the stack carries 10 queries it misses while losing
0; the anonymous register reads text 720 -> 51 of 837 and structure
174 -> 173 of 837. Both claims are unchanged — the relay is still ahead on
every set and loses nothing, and the text search still falls to chance while
the structural address holds. No other answer moved, none of the batch
machine's included. Re-pinning the case file stales the stored
query-escalation measurement, which hashes the cases; it was re-taken
(`tools queryesc --write`) and the close re-checks all 179.
