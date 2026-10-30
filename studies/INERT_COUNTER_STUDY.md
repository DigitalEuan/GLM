# Inert variables — a non-termination certificate past the control state

## Tier 0 — the coarse read

**Question.** If GLM-BAT forgets the variables no instruction reads except to update a forgotten variable, does a recurrence of what is left certify that a loop with a growing counter never halts, without changing any verdict the machine already gave and without certifying a program that halts?

**Verdict.** Yes, within the declared rule. All 10 battery programs and all 9 questions came out as declared with 0 wrong: the four loops whose counters are inert (M15 among them) are certified never to halt, and the four whose growing variable some line reads are still refused. Every Phase 125 answer stands except M15 and Q6, all 299 generated programs Phase 125 decided keep their verdicts, no certified program halts within 200000 steps, and the program that does halt after 40003 steps is refused. The one generated program Phase 125 left undecided is still undecided: its growing variable is read.

**Deciding figure.** 7 of 7 marks; 10 of 10 programs and 9 of 9 questions as declared; 8 of 8 column-3 scripts verify and 40 of 40 mutations rejected; 299 of 299 decided generated programs unchanged; 0 of 4 certified programs halt within 200000 steps.

**Recomputed by.** `glm_universal.reasoning.inert_counter.inert_counter_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the module that takes the
measurement exists. §§0–6 are as they were committed; §7 is what came out.

It takes the halting part of *GLM-BAT, the rest* in [`STATUS.md`](../STATUS.md)
§2.2, left by Phase 125
([`OPERATIONS_LADDER_STUDY.md`](OPERATIONS_LADDER_STUDY.md) §7.4): a loop whose
counter grows (M15, `SET /A N=0 / :UP / SET /A N=N+1 / GOTO UP`) is refused
`UNDECIDED_WITHIN_BUDGET`, because its control state — everything but the two
output streams — never recurs: the counter is part of it.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 125's record: 25 battery
   runs, 18 questions, 300 generated programs of which 1 was refused as
   undecided. Nothing about the generated undecided program beyond that count
   was looked at.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/InertCounter.lean` was written and built first.
3. **No code of the rule existed and no program below had been run under it
   when this was committed.** Every expected answer in §3 was worked out by
   hand from the semantics of
   [`OPERATIONS_LADDER_STUDY.md`](OPERATIONS_LADDER_STUDY.md) §2.2.

## 1. Why the counter is not part of the argument

The step of M15 reads `N` only to compute the next `N`. Neither the next line,
nor the files, nor the exit code, nor whether there is a next step at all,
depends on its value. Split the state into the **read part** `c` and the
**inert store** `x`; then the step has the shape

  `step (c, x) = (stepC c).map (fun c' => (c', upd c x))`

and `GLM.InertCounter.never_halts_of_inert_repeat` proves that a recurrence of
the read part, `run stepC i c = run stepC j c` with `i < j`, means the machine
never halts, whatever `x` holds. It is the Phase 125 certificate
(`never_halts_of_projected_repeat`) with the projection that forgets the
store (`inert_step_commutes`).

## 2. The rule

**Inert variables.** A set `F` of variable names (never `ERRORLEVEL`) is
*closed* when every program line that mentions a name of `F` — as a whole
word, in any case, anywhere on the line — is a single assignment to a name of
`F` and nothing else:

* `SET V=text` with `V ∈ F`, or
* `SET /A V=expr` with `V ∈ F` and no `/` or `%` in `expr` (so it cannot fail
  and cannot read a variable by expansion),

with no redirection, pipe or chain on the line (no `<`, `>`, `|`, `&`). An
inert assignment may read variables outside `F`; no other line may read a
variable of `F`, and no inert assignment changes the exit code. For a closed
`F` the GLM-BAT step has the shape of §1 with `x` the values of `F`.
`inert_variables(program)` returns the largest closed set: start from every
assigned name and remove names until the set is closed.

**When it is used.** Only when the Phase 125 run is undecided: the program is
run again with the variables of `F` left out of the control state, and the
first recurrence of that state (least `j`) within the budget is the
certificate `(i, j)` with the forgotten names. A program the Phase 125 run
decides keeps its verdict and certificate exactly, even if it has inert
variables (M13's `X` is inert; its certificate stays `(2, 4)`).

**What the GLM says.** *Does it halt?* — "no, it never halts: with N
forgotten (no instruction reads it except to update a forgotten variable),
the control state before step 2 recurs before step 4". Column 3 is a new claim
kind, `never_inert`, whose script re-checks the closure of the claimed `F`
with its own reading of the lines and re-runs the forgetful recurrence.

## 3. The marks, declared before the code

The battery (lines separated by ` / `; certificates `(i, j)` count steps from
0, as in Phase 125):

| program | lines | expected |
|---|---|---|
| N1 | `SET /A N=0 / :UP / SET /A N=N+1 / GOTO UP` (M15) | never; `F = {N}`; `(2, 4)` |
| N2 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (`N` is read by `ECHO`; the rule is conservative) |
| N3 | `SET /A N=0 / :UP / SET /A N=N+1 / IF %N% LSS 20000 GOTO UP / ECHO done` | refused `UNDECIDED_WITHIN_BUDGET`; it halts, after 40003 steps, under a budget of 200000 |
| N4 | `SET /A N=0 / SET /A M=0 / :UP / SET /A N=N+1 / SET /A M=M+N / GOTO UP` | never; `F = {M, N}`; `(3, 6)` |
| N5 | `SET /A N=1 / :UP / SET /A N=N*2 / SET /A Q=10/N / GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (`Q`'s update divides; `N` is read by it) |
| N6 | `SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / IF %B% GTR -1 GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (`B` is read by `IF`, so `A`, read by `B`'s update, is not inert either) |
| N7 | `SET /A K=0 / :TOP / CALL :BUMP / GOTO TOP / :BUMP / SET /A K=K+1 / GOTO :EOF` | never; `F = {K}`; `(2, 6)` |
| N8 | `SET S=x / :UP / SET S=%S%x / GOTO UP` | never; `F = {S}`; `(2, 4)` |
| N9 | `SET /A N=0 / :UP / SET /A N=N+1 / IF %N% LSS 5 GOTO UP / ECHO %N%` | halts after 13 steps, out `5`, exit 0 (decided by the Phase 125 run) |
| N10 | `:LOOP / SET X=1 / GOTO LOOP` (M13) | never by the Phase 125 certificate `(2, 4)`, with nothing forgotten |

| mark | statement |
|---|---|
| **I1** | `RequestProject/GLM/InertCounter.lean` builds with no `sorry` and only the standard axioms, and proves `inert_step_commutes`, `inert_run_fst` and `never_halts_of_inert_repeat`. |
| **I2** | **The battery.** N1–N10 as declared, 0 wrong. |
| **I3** | **The question.** *Does it halt?* of N1, N4, N7 and N8 answers *no* with the declared forgotten names and certificate; of N2, N3, N5 and N6 it refuses `UNDECIDED_WITHIN_BUDGET`; *what does it print?* of N1 refuses `NEVER_HALTS`. |
| **I4** | **Certificates.** Every `never_inert` claim of I2 and I3 has a column-3 script that passes under `python3 -I`, and every mutation fails: the certificate's `j` moved by one either way, the forgotten set emptied, its first name dropped, and a name added that a non-assignment line reads (or, where there is none, `ERRORLEVEL`). |
| **I5** | **Non-interference on the machine.** The Phase 125 battery (25 runs), its 18 questions and its 6 English programs give their Phase 125 answers, except M15 and Q6, which move from `UNDECIDED_WITHIN_BUDGET` to N1's answer; and every one of the 300 generated programs that Phase 125 decided keeps its verdict and certificate. |
| **I6** | **Soundness control.** No program the rule certifies — battery or generated — halts when run without the rule under a budget of 200000 steps; N3 halts under that budget and is refused by the rule. |
| **I7** | **Non-interference on the system.** All 179 evaluation cases pass with 0 confidently wrong. Re-pins are allowed only for the retrieval figures that count goal queries sampled from the Lean development (`report relay`, `report anonymous`), which a new Lean file moves, as earlier Lean files have. |

**Not predicted:** whether the one generated program Phase 125 left undecided
is certified by the rule. It is reported either way; I5 and I6 bind it.

## 4. Controls

* **N9 and N10** are the controls on the order of use: a program the Phase 125
  run decides is not re-read.
* **N2, N3, N5, N6** are the controls on the closure: each has a variable that
  grows and that the rule must not forget.
* **I6** is the control on soundness that does not trust the closure
  argument: it runs the certified programs a further 190000 steps.
* **The multiplicity count.** Phase 125 stood at 61 statistics; this round
  adds the battery and the generated-program re-reading, so **63**. No bit
  score is computed.

## 5. What this round does not do

* No ranking-function certificate: a loop that halts after more steps than
  the budget (N3) is still refused, not proved to halt.
* No forgetting of a variable that only output reads (N2) — sound, since the
  output streams are already forgotten, but not declared here.
* No change to the fragment, the English reader or the sayer, the planner,
  or any router path.

## 6. Files

* `RequestProject/GLM/InertCounter.lean` — I1.
* `glm_universal/reasoning/batch_machine.py` — `inert_variables`, and
  the forgetful re-run in `run_program`.
* `glm_universal/reasoning/batch_speech.py` — the answer and the
  `never_inert` column-3 claim, its checker and its mutations.
* `glm_universal/reasoning/inert_counter.py` — the battery and the
  marks; `python3 -m glm_universal.tools inert-counter`.
* Tests: `test_inert_counter.py`; `test_operations.py` re-pinned for M15/Q6.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`PYTHONPATH=. python3 -m glm_universal.tools inert-counter` takes every mark
except I1 and I7 in about thirty seconds; `tests/test_inert_counter.py` (11
tests) pins them.

### 7.1 The verdict

Yes, within the declared rule. All 10 battery programs and all 9 questions came out as declared with 0 wrong: the four loops whose counters are inert (M15 among them) are certified never to halt, and the four whose growing variable some line reads are still refused. Every Phase 125 answer stands except M15 and Q6, all 299 generated programs Phase 125 decided keep their verdicts, no certified program halts within 200000 steps, and the program that does halt after 40003 steps is refused. The one generated program Phase 125 left undecided is still undecided: its growing variable is read.

### 7.2 The marks

| mark | what | result |
|---|---|---|
| I1 | the Lean file | **met**: `RequestProject/GLM/InertCounter.lean` builds with no `sorry`; `#print axioms` gives `propext`, `Classical.choice`, `Quot.sound` for `never_halts_of_inert_repeat` and `propext` alone for `inert_run_fst` |
| I2 | the battery | **met**: 10 of 10 as declared, 0 wrong — N1 `(2, 4)` with `N`, N4 `(3, 6)` with `M, N`, N7 `(2, 6)` with `K`, N8 `(2, 4)` with `S`; N2, N3, N5, N6 undecided; N9 halts after 13 steps with out `5`; N10 keeps `(2, 4)` with nothing forgotten |
| I3 | the questions | **met**: 9 of 9 as declared |
| I4 | certificates | **met**: 8 of 8 `never_inert` scripts pass under `python3 -I`; 40 of 40 mutations fail |
| I5 | non-interference on the machine | **met**: 25 of 25 runs, 18 of 18 questions, 6 of 6 English programs as declared, M15 and Q6 moved to N1's answer; 299 of 299 decided generated programs unchanged (status, certificate, steps, outputs, exit code, files), 0 newly certified, 1 still undecided |
| I6 | soundness control | **met**: 0 of the 4 certified programs halt within 200000 steps without the rule; N3 halts after 40003 steps and is refused |
| I7 | non-interference on the system | **met**: all 179 evaluation cases pass with 0 confidently wrong. Before the re-pin, exactly the two declared retrieval cases moved: `InertCounter.lean` took the goal-query set from 822 to 823 queries; `report relay` now reads 710 → 712 of 823 (ahead), carrying 7 queries and losing 0, its gate firing on 44 of 1646; `report anonymous` reads text 710 → 52 and structure 163 → 161 of 823. Their claims are unchanged |

### 7.3 What was seen

* **The answer says why.** Asked *does it halt?* of M15 the GLM now answers
  "no, it never halts: with N forgotten (no instruction reads it except to
  update a forgotten variable), the control state before step 2 recurs before
  step 4", and column 3 re-checks both halves on its own: the closure of `{N}`
  from the program text, and the recurrence of the forgetful state.
* **The mutations bind both halves.** Emptying the forgotten set, or dropping
  its first name, leaves a growing variable in the state and the recurrence
  fails; adding a name that a line reads (or `ERRORLEVEL`) fails the closure.
* **The rule is conservative, and says so by refusing.** N2 never halts (its
  counter reaches only the output stream, which is already forgotten) and is
  refused; N5 and N6 never halt and are refused because a growing variable
  reaches a line that is not an inert assignment. N3, which halts, is refused
  on the same grounds — the soundness control is that a refusal, not a
  certificate.
* **The generated program Phase 125 left undecided** (index 206 of 300) is
  refused still. Its counter `N`, bumped by a subroutine the loop `:L2 /
  CALL :SUB / GOTO L2` calls forever, is read by `SET /A M=N%3` — an update
  whose `%` the rule does not admit — so `N` is not inert. That line is in
  fact unreachable (it follows the unconditional `GOTO L2`), so the program
  never halts; the closure reads every line, reachable or not.

### 7.4 What is left

* **Halting past the budget.** A ranking-function certificate (`layered_wf`,
  `lex_rank_wf` are the Lean side) would let the machine say *halts* for N3
  without running it out.
* **Output-only variables.** Forgetting a variable that only `ECHO` reads
  without redirection (N2) is sound — the output streams are not in the
  control state — but needs the closure to distinguish an output line from a
  read; not declared here.
* **Reachability in the closure.** Reading only the lines a control path
  reaches (the machine already computes them, `unreachable_lines`) would
  certify generated program 206; not declared here.
* **The statistics count** is now 63 (§4); no bit score was computed.
