# Counter lassos — halting and non-termination past the budget

## Tier 0 — the coarse read

**Question.** If GLM-BAT reads a loop whose state repeats except for integer counters that come back translated by a fixed step, can it say *halts* (with the exact step count, outputs and exit code) or *never halts* for loops its budget cannot run out, without changing any verdict it already gave and without a verdict a long plain run contradicts?

**Verdict.** Yes, within the declared rule. All 12 battery programs and all 17 questions came out as declared with 0 wrong: six loops of 40,003 to 2,000,003 steps are answered *halts* with their exact step count, outputs, values and exit code, two loops are certified never to halt — N2, whose counter only the output reads, and one whose odd counter never reaches the zero it is compared with — and the four controls are refused. Every Phase 125 and 126 answer stands except N2 and N3, all 299 generated programs the earlier readings decided keep their verdicts, and the one they left undecided (206) is now certified never to halt. Every *halts* agrees with a plain run of up to 2,500,000 steps and no *never* halts within 200,000; the three refused controls do halt.

**Deciding figure.** 7 of 7 marks; 12 of 12 programs and 17 of 17 questions as declared; 20 of 20 column-3 scripts verify and 112 of 112 mutations rejected; 299 of 299 decided generated programs unchanged and 1 newly decided; 6 of 6 jumped *halts* equal to a plain run, 0 of 3 *never* halting in 200,000 steps.

**Recomputed by.** `glm_universal.reasoning.counter_lasso.counter_lasso_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 130, committed with its Lean file and before
the code of the rule exists. §§0–6 are as they were committed; §7 is what
came out.

It takes the halting part of *GLM-BAT, the rest* in [`STATUS.md`](../STATUS.md)
§2.2, left by Phases 125 and 126
([`INERT_COUNTER_STUDY.md`](INERT_COUNTER_STUDY.md) §7.4): a loop that halts
after more steps than the budget (N3, 40,003 steps against a budget of 10,000)
is refused `UNDECIDED_WITHIN_BUDGET`, and so is a loop whose growing counter
only the output reads (N2), although it never halts.

**Why not an item of §2.1.** Item 1 (the placement guard in the answering
path) was read first. No module the query path loads imports the ladder the
guard protects: `ladder_escalation`, `cell_guard` and `placement_guard` are
reached only from `tools.py` and from other measurement modules, so there is
no answering path to put the guard into until a query kind reads a carrier
by its address. That correction is recorded here and in `STATUS.md`; the
round takes a line that adds a faculty the machine does not have — deciding
a run it cannot finish.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 126's record: N2, N3, N5
   and N6 refused, N3 halting after 40,003 steps under a budget of 200,000,
   and generated program 206 refused. Nothing else about any program below
   had been run.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/CounterLasso.lean` was written and built first (§1).
3. **No code of the rule existed and no program below had been run under it
   when this was committed.** Every expected answer in §3 was worked out by
   hand from the semantics of
   [`OPERATIONS_LADDER_STUDY.md`](OPERATIONS_LADDER_STUDY.md) §2.2.

## 1. What is proved before any code

`RequestProject/GLM/CounterLasso.lean`, no `sorry`, standard axioms only, on
top of `RequestProject/GLM/OperationsLadder.lean`. The state is split into a
part `C` and integer counters `ι → ℤ`; `shift v` adds `v` to the counters.

* `lasso_iterate` — if every step of one pass `path 0 → … → path p` commutes
  with translating the counters by `m • d` for every `m < K`, and the pass
  ends at its start translated by `d`, then from the start translated by
  `m • d` the pass ends at the start translated by `(m + 1) • d`.
* `lasso_accelerate` — so `K` passes take `K * p` steps and end at the start
  translated by `K • d`: the jump.
* `never_halts_of_lasso` — a pass that repeats from every translate means the
  machine never halts (a plain recurrence is the case `d = 0`).
* `halts_of_jump` — run `i` steps to the pass, jump `K` passes, run `n` more
  steps to a state with no successor: the machine halts, after exactly
  `i + K * p + n` steps.
* `indep_equivariant`, `add_equivariant`, `test_equivariant` — the three
  kinds of line the rule admits on a pass, and why each commutes with a
  translation: a line that reads and writes no counter always does; an update
  `x_i := x_i + k` always does; a test does exactly while its outcome is
  unchanged.
* `linear_neg_stable`, `linear_nonneg_stable`, `linear_zero_unique` — a
  comparison `e₀ + b·m ⋈ 0` has the same outcome at every `m` between two
  where it agrees (for `< 0` and `≥ 0`, and so for every order comparison of
  integers), and `= 0` holds at one `m` at most when `b ≠ 0`. This is why the
  first pass at which a comparison changes can be computed exactly from
  `e₀` and `b`.

The comparison that changes first is a linear ranking function: it counts
the passes left. The theorems do not say the Python's reading of a line is
right; that is what the column-3 script checks with its own reading (§2).

## 2. The rule

**Counters.** A name `V` (never `ERRORLEVEL`) is a *counter* of a program if
some line is a lone `SET /A V=V+k` or `SET /A V=V-k`, `k` a decimal literal,
with no redirection, pipe or chain.

**The masked state.** The control state of Phase 125 (everything but the two
output streams), with the value of every counter that holds a canonical
integer (`str(int(v)) == v`) replaced by a tag.

**A pass.** The first recurrence of the masked state, at steps `i < j` (least
`j`). It is *admissible* when every line executed at a step `t` with
`i ≤ t < j` is one of:

* a label or a remark;
* a lone `SET /A V=V+k` or `SET /A V=V-k` with `V` a counter;
* `IF [NOT] a OP b body` with `OP` one of `EQU NEQ LSS LEQ GTR GEQ`, each of
  `a`, `b` either `%V%` for a counter `V` or a decimal integer literal, and a
  `body` that mentions no counter and holds no `FOR`;
* a line that mentions no counter (as a whole word, in any case) and holds
  no `FOR`;
* for a **never** verdict only: an `ECHO` with no redirection, pipe or chain
  (its text may mention counters: it writes only the output stream, which is
  not in the control state).

`d` is the counters' values at `j` minus their values at `i`. For each `IF`
of the pass, at step `t`, `e₀ = a_t − b_t` and `b = d_a − d_b` (a literal has
`d = 0`); its outcome at pass `m` is that of `e₀ + b·m OP 0`. The **first
change** `m*` is the least `m ≥ 1` at which some `IF` of the pass has an
outcome other than at `m = 0` — computed exactly, or none.

* **No change** (`m*` none): the run **never halts** — `never_halts_of_lasso`.
* **A change at `m*`**, and the pass writes no line to either output stream:
  the run **jumps**: the state at step `i` with every counter advanced by
  `m* · d_V`, counted as step `i + m* · (j − i)`
  (`lasso_accelerate`); then the run goes on, and may jump again. A run that
  ends after jumps **halts**, with exact step count, outputs, files and exit
  code (`halts_of_jump`).
* An inadmissible pass, or a pass with a change that writes output: no
  certificate from that pass; the run goes on, and at most the budget of
  concrete steps (10,000) is taken, with at most 100 jumps.

**When it is used.** Only when the Phase 125 run and the Phase 126 inert
re-reading are both undecided. Every verdict either already gives is kept
exactly.

**What the GLM says.** *Does it halt?* — "yes, it halts after 40003 steps
with exit code 0 (the pass from step 2 to step 4 adds 1 to N, and was jumped
19999 times, until IF %N% LSS 20000 changed)", or "no, it never halts: the
pass from step 2 to step 5 adds 1 to N, and no comparison on it ever changes".
Questions about the end of a halting run (*what does it print*, *the value of
N*, *the exit code*, *how many steps*) are answered from the jumped run.
Column 3 has two new claim kinds, `run_jump` and `never_lasso`; their script
re-derives the counters, the masked recurrences, admissibility, `d`, every
first change and every jump with its own reading of the lines, and asserts
that its jumps and its end are the claim's.

## 3. The marks, declared before the code

The battery (lines separated by ` / `; steps count from 0, as in Phase 125;
"jump `(i, j, m)`" is a pass from step `i` to step `j` jumped `m` times):

| program | lines | expected |
|---|---|---|
| L1 | `SET /A N=0 / :UP / SET /A N=N+1 / IF %N% LSS 20000 GOTO UP / ECHO done` (N3) | halts after 40003 steps, out `done`, exit 0, `N` = 20000; jump `(2, 4, 19999)` |
| L2 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / GOTO UP` (N2) | never; pass `(2, 5)`, `d`: N +1 |
| L3 | `SET /A N=1000000 / :LOOP / SET /A N=N-1 / IF %N% GTR 0 GOTO LOOP / ECHO %N%` | halts after 2000003 steps, out `0`, exit 0; jump `(2, 4, 999999)` |
| L4 | `SET /A I=0 / SET /A J=1000000 / :L / SET /A I=I+3 / SET /A J=J+1 / IF %I% LSS %J% GOTO L / ECHO %I% %J%` | halts after 1500004 steps, out `1500000 1500000`, exit 0; jump `(3, 6, 499999)` |
| L5 | `SET /A N=0 / :TOP / CALL :INC / IF %N% LSS 50000 GOTO TOP / ECHO %N% / EXIT /B 0 / :INC / SET /A N=N+1 / GOTO :EOF` | halts after 200004 steps, out `50000`, exit 0; jump `(2, 6, 49999)` |
| L6 | `SET /A N=-7 / :UP / SET /A N=N+2 / IF %N% NEQ 0 GOTO UP / ECHO never` | never; pass `(2, 4)`, `d`: N +2 (an odd counter is never 0) |
| L7 | `SET /A N=-200000 / :UP / SET /A N=N+2 / IF %N% NEQ 0 GOTO UP / ECHO reached` | halts after 200003 steps, out `reached`, exit 0; jump `(2, 4, 99999)` |
| L8 | `SET /A N=0 / :UP / SET /A N=N+1 / IF %N% EQU 30000 EXIT 7 / GOTO UP` | halts after 90001 steps, exit 7, out nothing; jump `(2, 5, 29999)` |
| L9 | `SET /A N=0 / :UP / SET /A N=N+1 / SET /A N=N*1 / IF %N% LSS 20000 GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (`SET /A N=N*1` is not admissible) |
| L10 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO tick / IF %N% LSS 20000 GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (a pass with a change writes output) |
| L11 | `SET /A N=0 / SET L=20000 / :UP / SET /A N=N+1 / IF %N% LSS %L% GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (`%L%` is neither a counter nor a literal) |
| L12 | `SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / IF %B% GTR -1 GOTO UP` (N6) | refused `UNDECIDED_WITHIN_BUDGET` (`B` is not a counter; it grows, so the masked state never recurs) |

| mark | statement |
|---|---|
| **C1** | `RequestProject/GLM/CounterLasso.lean` builds with no `sorry` and only the standard axioms, with the theorems of §1. |
| **C2** | **The battery.** L1–L12 as declared, 0 wrong. |
| **C3** | **The questions.** *Does it halt?* of L1–L12 as declared (yes with the step count and exit code; no; or the refusal); *how many steps?* of L3 is 2000003; *what does it print?* of L4 is `1500000 1500000`; *what is the exit code?* of L8 is 7; *what is the value of N?* of L1 is 20000; *what does it print?* of L2 refuses `NEVER_HALTS`. |
| **C4** | **Certificates.** Every `run_jump` and `never_lasso` claim of C2 and C3 has a column-3 script that passes under `python3 -I`, and every mutation fails: for `run_jump`, the step count moved by one, the first jump's `m` moved by one either way, its `j` moved by one, the jumps dropped, and the first output line altered (or a line added); for `never_lasso`, the pass's `j` moved by one either way, `d` altered, and the verdict claimed for a pass with one counter's `d` set to 0. |
| **C5** | **Non-interference on the machine.** The Phase 125 battery (25 runs), its 18 questions and its 6 English programs, the Phase 126 battery (10 programs) and its 9 questions give their recorded answers, except N2 and N3, which move from `UNDECIDED_WITHIN_BUDGET` to L2's and L1's answers; and every one of the 300 generated programs that Phase 125 or 126 decided keeps its verdict and certificate. |
| **C6** | **Soundness control.** Every program the rule says halts (battery or generated) halts when run plainly, without the rule, under a budget of 2,500,000 steps, with the same step count, outputs, files and exit code; no program the rule says never halts halts within 200,000 plain steps; and L9, L10, L11, which are refused, are reported with their plain outcome under the long budget. |
| **C7** | **Non-interference on the system.** All 179 evaluation cases pass with 0 confidently wrong. Re-pins are allowed only for the retrieval figures that count goal queries sampled from the Lean development (`report relay`, `report anonymous`), which a new Lean file moves, as earlier Lean files have. |

**Not predicted:** whether generated program 206 (refused by Phase 126) is
decided by the rule. Its loop calls a subroutine that bumps `N` and reads it
with `SET /A M=N%3` on an unreachable line; the masked recurrence does not
look at unreachable lines, so it may be certified never to halt. It is
reported either way; C5 and C6 bind it.

## 4. Controls

* **L9, L10, L11** are the controls on admissibility and on the output rule:
  each is a loop that does halt, refused because one line falls outside the
  rule; C6 reports their plain outcomes, so a refusal is visibly a refusal and
  not a wrong *never*.
* **L12** is the control on the counters: a variable that grows by another
  counter is not a translation, and the masked state must not recur.
* **L6 against L7** is the control on equality: the same loop shape, with a
  start from which the counter misses zero and one from which it hits it.
* **C6** is the control that does not trust the theorems or the reading: every
  *halts* is re-run in full, every *never* is run a further 200,000 steps.
* **The multiplicity count.** Phase 126 stood at 63 statistics; this round
  adds the battery and the generated-program re-reading, so **65**. No bit
  score is computed.

## 5. What this round does not do

* No ranking function other than one comparison against a translated counter:
  a counter compared with a variable that is not a counter (L11), a counter
  updated by another counter (L12) or by multiplication, and nested loops whose
  inner pass changes on every outer pass, are refused or run out.
* No jump over a pass that writes output (L10): its output would have to be
  stated, line by line, without being produced.
* No change to the fragment, the English reader or the sayer, the planner, or
  any router path.

## 6. Files

* `RequestProject/GLM/CounterLasso.lean` — C1.
* `glm_universal/reasoning/batch_machine.py` — `counters`, the masked
  state, and the jumped run (`accelerated_run`), used by `run_program` after
  the Phase 125 and 126 readings.
* `glm_universal/reasoning/batch_speech.py` — the answers and the
  `run_jump` and `never_lasso` column-3 claims, their checker and their
  mutations.
* `glm_universal/reasoning/counter_lasso.py` — the battery and the
  marks; `python3 -m glm_universal.tools counter-lasso`.
* Tests: `test_counter_lasso.py`; `test_inert_counter.py` and
  `test_operations.py` re-pinned for N2 and N3 if they pin them.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`PYTHONPATH=. python3 -m glm_universal.tools counter-lasso` takes every mark
except C1 and C7 in about forty seconds; `tests/test_counter_lasso.py` (10
tests) pins them.

### 7.1 The verdict

Yes, within the declared rule. All 12 battery programs and all 17 questions came out as declared with 0 wrong: six loops of 40,003 to 2,000,003 steps are answered *halts* with their exact step count, outputs, values and exit code, two loops are certified never to halt — N2, whose counter only the output reads, and one whose odd counter never reaches the zero it is compared with — and the four controls are refused. Every Phase 125 and 126 answer stands except N2 and N3, all 299 generated programs the earlier readings decided keep their verdicts, and the one they left undecided (206) is now certified never to halt. Every *halts* agrees with a plain run of up to 2,500,000 steps and no *never* halts within 200,000; the three refused controls do halt.

### 7.2 The marks

| mark | what | result |
|---|---|---|
| C1 | the Lean file | **met**: `RequestProject/GLM/CounterLasso.lean` builds with no `sorry`; `#print axioms` gives `propext`, `Classical.choice`, `Quot.sound` for `never_halts_of_lasso` and `halts_of_jump`, `propext` and `Quot.sound` for `lasso_iterate`, and none for `test_equivariant` |
| C2 | the battery | **met**: 12 of 12 as declared, 0 wrong — L1 halts after 40003 steps (jump `(2, 4, 19999)`), L3 after 2000003 (`(2, 4, 999999)`), L4 after 1500004 (`(3, 6, 499999)`), L5 after 200004 (`(2, 6, 49999)`), L7 after 200003 (`(2, 4, 99999)`), L8 after 90001 with exit 7 (`(2, 5, 29999)`); L2 never, pass `(2, 5)` adding 1 to N; L6 never, pass `(2, 4)` adding 2 to N; L9–L12 undecided |
| C3 | the questions | **met**: 17 of 17 as declared |
| C4 | certificates | **met**: 20 of 20 `run_jump` and `never_lasso` scripts pass under `python3 -I`; 112 of 112 mutations fail |
| C5 | non-interference on the machine | **met**: Phase 125's 25 runs, 18 questions and 6 English programs as declared; Phase 126's 8 programs and 7 questions other than N2 and N3 unchanged (status, certificate, forgotten names, steps, outputs and answer text); 299 of 299 decided generated programs unchanged; generated program 206, undecided before, newly certified never to halt, 0 still undecided |
| C6 | soundness control | **met**: all 6 jumped *halts* (L1, L3, L4, L5, L7, L8) equal a plain run without any certificate in steps, outputs, error lines, files, variables and exit code; none of the 3 *never* (L2, L6, generated 206) halts within 200000 plain steps; the refused controls halt plainly — L9 after 60002 steps, L10 after 60002, L11 after 40003 |
| C7 | non-interference on the system | **met**: 179 of 179 evaluation cases, 0 confidently wrong, after the two declared re-pins (§7.5) |

### 7.3 What was seen

* **The answer says why, and how far it jumped.** Asked *does it halt?* of N3
  the GLM now answers "yes, it halts after 40003 steps with exit code 0 (the
  pass from step 2 to step 4 adds 1 to N, and was taken 19999 times in one
  jump, until IF %N% LSS 20000 GOTO UP changed)". The same reading answers
  *how many steps?*, *what does it print?*, *what is the value of N?* and
  *what is the exit code?* from the jumped run, through `tool machine` as
  well as the module.
* **The second interpreter re-derives the jumps, not only the end.** A
  `run_jump` script asserts that its own jumps are the claimed ones, so a
  claim with the jumps dropped fails although a plain run would reach the same
  end (L1 halts after 40003 steps either way); the mutations of the first
  jump's count and length fail on the same assertion.
* **Equality is where the first change is subtle.** L6 and L7 have the same
  shape: from −7 an odd counter stepping by 2 never equals 0, and the rule
  certifies *never*; from −200000 it equals 0 after 99999 passes, and the rule
  jumps exactly there. `first_change` agrees with a brute-force read on a grid
  of 1,650 comparisons (the test).
* **The three refused controls all halt.** L9 (a pass with `SET /A N=N*1`),
  L10 (a pass that prints) and L11 (a counter compared with a variable) are
  refused as declared, and each halts when run plainly — the cost of the rule's
  conservatism, counted rather than hidden.
* **Generated program 206** — refused by Phase 126 because its counter is read
  by `SET /A M=N%3` on a line no control path reaches — is certified never to
  halt: the pass from step 3 to step 7 (`CALL :SUB`, `SET /A N=N+1`,
  `EXIT /B 0`, `GOTO L2`) adds 1 to N and holds no comparison. The masked
  recurrence reads only the lines a run executes, which is the reachability
  Phase 126's closure lacked.

### 7.4 What is left

* **Passes that write output** (L10): a jump must then state the output it
  skipped, line by line; the output of a pass with no counter in it is the
  same block repeated, so a run-length statement of the output would do.
* **Comparisons with a variable that is not a counter** (L11): a variable no
  line of the pass mentions is constant along the passes and could be read as
  a literal.
* **Growth that is not a translation** (L12, N5, N6): a variable that grows by
  a counter grows quadratically, one that doubles grows geometrically; the
  jump would need a closed form for each.
* **Nested loops** whose inner pass changes on every outer pass are run out
  pass by pass, one jump per inner loop, up to 100 jumps and the budget.
* **The rest of GLM-BAT** (Phase 125's list): stream merging, `SORT` options,
  `FOR /F`, `SETLOCAL`, delayed expansion.
* **The statistics count** is now 65 (§4); no bit score was computed.

### 7.5 Non-interference on the system

The full evaluation, run after `corpus --refresh` with `CounterLasso.lean` in
the corpus, passed 177 of 179 cases with 0 errors before any re-pin; the two
that moved are the two C7 names, `report relay` and `report anonymous`, and
both moved only because the goal-query set sampled from the Lean development
grew from 823 to 835 queries. Re-pinned (comments in
`evaluation/cases.py`): the relay reads 686 -> 691 of 835 (ahead) on bare goal
queries, the gate fires on 56 of 1670 and the stack carries 14 queries it
misses while losing 0; the anonymous register reads text 686 -> 53 of 835 and
structure 165 -> 163 of 835. Both claims are unchanged — the relay is still
ahead on every set and loses nothing, and the text search still falls to
chance while the structural address holds. No other answer moved. Re-pinning
the case file stales the stored query-escalation measurement, which hashes
the cases; it was re-taken (`tools queryesc --write`) and the close re-checks
all 179.
