# Quadratic lassos: jumping a pass whose step grows

## Tier 0 — the coarse read

**Question.** Can GLM-BAT's counter-lasso reading decide loops whose variables grow quadratically — an accumulator that adds a counter on every pass — by jumping to the exact first pass at which a comparison changes, or by certifying that none ever does, without changing any verdict it already gave and without a verdict a long plain run contradicts?

**Verdict.** Yes, within the declared rule: all 12 battery programs came out exactly as declared, the loops whose step grows now halt with their exact step counts and outputs or are certified never to halt, and every answer the machine gave before is unchanged; one mark is missed on its declaration, because the question list it counted held 21 questions, not 20.

**Deciding figure.** 7 of 8 marks; 12 of 12 programs as declared; 21 of 21 questions as declared; 18 of 18 column-3 scripts verify and 105 of 105 mutations rejected; 47 of 47 earlier programs, 58 of 58 earlier questions and 300 of 300 generated programs unchanged; 7 of 7 jumped *halts* equal to a plain run and 3 of 3 *never* unrefuted; 90,882 of 90,882 first changes equal to brute force.

**Recomputed by.** `glm_universal.reasoning.quadratic_lasso.quadratic_lasso_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 142, committed with its Lean file and before
the code of the rule exists. §§0–6 are as they were committed; §7 is what
came out.

It takes the first line of *GLM-BAT, the rest* in [`STATUS.md`](../STATUS.md)
§2.2, left by Phase 132
([`AFFINE_OUTPUT_STUDY.md`](AFFINE_OUTPUT_STUDY.md) §7.5): *jumps over
quadratic and geometric growth — a jump over a pass whose counter grows
quadratically needs the first change of a quadratic comparison, which is the
next step.* Phase 132 taught the machine to *say* that L12's `B` grows
quadratically; this round teaches it to *reason through* such a loop: to
compute, in closed form, the pass at which the loop's test first changes and
jump there, or to prove that it never changes. It is the loop-reasoning
faculty the owner asked for in the original brief, one shape further.

**Why not an item of §2.1.** As in Phases 130–132: items 1–4 each change
answers the evaluation pins and need a frozen-path comparison; this round adds
a faculty the machine lacks and is bound by the same non-interference marks.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 132's record: L12 (= N6)
   refused `UNDECIDED_WITHIN_BUDGET`, diagnosed as `B grows quadratically
   (second difference 1)`; N5 refused (geometric). Nothing about any new
   program below had been run.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/QuadraticLasso.lean` was written and built first (§1).
3. **No code of the rule existed and no new program below had been run when
   this was committed.** Every expected answer in §3 was worked out by hand
   from the semantics of
   [`OPERATIONS_LADDER_STUDY.md`](OPERATIONS_LADDER_STUDY.md) §2.2, the rules
   of [`COUNTER_LASSO_STUDY.md`](COUNTER_LASSO_STUDY.md) §2,
   [`CONSTANT_BOUND_STUDY.md`](CONSTANT_BOUND_STUDY.md) §2 and
   [`AFFINE_OUTPUT_STUDY.md`](AFFINE_OUTPUT_STUDY.md) §2, and the clauses of
   §2 below.

*One correction made while writing §2, before any code:* the first draft
read an accumulator at a point inside pass `t` as its value at that point of
the first pass plus `t·β + C(t, 2)·γ`, with `β` what the first pass adds. That
is right only at the start of the pass. At a later point the window from pass
`s` to pass `s + 1` already holds the accumulator lines of pass `s + 1` that
come before the point, so the linear coefficient there is `β + g_r`, with
`g_r` the part of `γ` contributed by the accumulator lines before the point.
This is the `W m r = drift m + m • g_r` of `quadratic_iterate`; the hand
computations of §3 use the corrected form.

## 1. What is proved before any code

`RequestProject/GLM/QuadraticLasso.lean`, no `sorry`, standard axioms only, on
top of `RequestProject/GLM/CounterLasso.lean`.

* `drift`, `drift_zero`, `drift_succ` — the displacement after `m` passes is
  `m • d + C(m, 2) • g`, and pass `m` moves the state by `d + m • g`.
* `seq_accelerate`, `halts_of_seq_jump`, `never_halts_of_seq_lasso` — Phase
  130's jump and its two certificates hold for passes that move the state by
  any sequence of displacements starting at `0`.
* `accStep`, `acc_shift` — `SET /A B=B+A` (sign `σ`) from a state displaced by
  `v` gives its result displaced by `v` and by `σ·v_A` more in `B`'s place.
* `quadratic_iterate`, `quadratic_accelerate`, `halts_of_quadratic_jump`,
  `never_halts_of_quadratic_lasso` — a pass whose step `r` carries the
  displacement `W m r` from `drift m` to `drift m + m • g` is repeated `K`
  times in one jump, to the start displaced by `drift K`; if it can be
  repeated for every `m`, the machine never halts.
* `quad`, `quad_diff`, `quad_closed_form` — a comparison read along the passes
  is `e₀ + b·m + c·C(m, 2)`, with linear first differences `b + c·m`.
* `monotone_on_of_diff_nonneg`, `antitone_on_of_diff_nonpos`, `sign_mono`,
  `sign_change_persists`, `sign_change_persists_anti`, `cmp_of_sign` — on a
  stretch where the differences keep one sign the comparison is monotone, its
  sign once changed from the stretch's first sign never comes back, and each
  of the six comparisons sees only that sign.
* `quad_eventually_pos`, `quad_eventually_neg` — with `c ≠ 0` the comparison
  leaves every bound.

The theorems do not say the Python's reading of a line is right; the column-3
script checks that with its own reading and its own way of finding the first
change (§2.4).

## 2. The rule

Everything of [`AFFINE_OUTPUT_STUDY.md`](AFFINE_OUTPUT_STUDY.md) §2 stands;
the reading with the clauses below is called the *quadratic* reading. Phase
132's is kept, as `quadratic=False`, so that its record can be re-measured;
the quadratic reading needs `affine`.

### 2.1 Accumulators

An *accumulator line* is a lone `SET /A V=V+W` or `SET /A V=V-W` (also with
`%W%`), `W` a name other than `V`, neither `ERRORLEVEL`. A name `V` is an
*accumulator* of the program when it has an accumulator line whose `W` is a
counter of the program (Phase 130: a name with a literal update) and is not
itself the target of any accumulator line. The *pure counters* are the
counters that are not accumulators. Under the quadratic reading the masked
names are the pure counters and the accumulators. A program with no
accumulator line is read exactly as Phase 132 reads it.

### 2.2 A pass

A line may sit on a pass as before, and also as `acc`: an accumulator line
whose target is a live accumulator and whose `W` is a live pure counter. Any
other line naming an accumulator, other than a literal update of it, a
comparison or an `ECHO` without redirection, cannot (in particular an
accumulator line into a name that is itself fed by an accumulator: cubic
growth is refused, §5). For each live name `n`, `β_n` is what the first pass
adds; `γ_n` is the sum, over the `acc` lines of the pass into `n`, of `σ·β_W`;
and at step `r` of the pass `g_r(n)` is the same sum over the `acc` lines
before step `r`. At step `r` of pass `t` the value of `n` is its value at step
`r` of the first pass plus `t·(β_n + g_r(n)) + C(t, 2)·γ_n`
(`quadratic_iterate`'s `W`). Pure counters have `γ = 0`, so this is Phase
130's translation for them.

### 2.3 The first change

A comparison at step `r` reads `e(t) = e₀ + b·t + c·C(t, 2)`, with `e₀` its
difference on the first pass and `b`, `c` the differences of the operands'
coefficients. With `c = 0` the first change is Phase 130's `first_change`.
With `c ≠ 0`, let `T` be the first `t ≥ 0` at which `b + c·t` has the sign of
`c` (or is 0); `e` is monotone on `[0, T]` and on `[T, ∞)`
(`monotone_on_of_diff_nonneg`, `antitone_on_of_diff_nonpos`). On each stretch
the machine finds, by bisection, the first `t` whose sign differs from the
sign at the stretch's start (`sign_change_persists`), and asks whether the
comparison's outcome there differs from its outcome at `t = 0`
(`cmp_of_sign`); if not, it goes on from that point, at most twice per
stretch. On the unbounded stretch, when the sign at its start is already the
extreme one in the direction of monotonicity, nothing changes again; otherwise
an upper end is found by doubling (`quad_eventually_pos`,
`quad_eventually_neg`). The jump takes the least first change over the tests of
the pass; none at all is a `never` verdict, with the pass's `d` and `g` in
the certificate.

### 2.4 Column 3

The second interpreter reads accumulators with its own regular expressions
and finds the first change by another route: the real roots of
`c·t² + (2b − c)·t + 2e₀`, bracketed with an integer square root, and every
integer within three of each, together with `t = 1` — a change between
`t − 1` and `t` needs a sign change and so a real root in `[t − 1, t]`. A
`never_lasso` claim states `g` beside `d` when it is not zero.

## 3. The battery, declared before the code

Each line is one step; a label is a step when it is run through, not when it
is jumped to (§2.2 of the operations-ladder study). `(i, j, m)` is the pass
from step `i` to step `j`, taken `m` times in one jump.

| id | program (lines separated by ` / `) | declared |
|---|---|---|
| Q1 | `SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / IF %B% GTR -1 GOTO UP` (L12, N6) | never: pass `(3, 6)`, `d = {A: 1, B: 1}`, `g = {B: 1}` |
| Q2 | `SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / IF %B% LSS 50000000 GOTO UP / ECHO %A% %B%` | halts after 30004 steps, exit 0, prints `10000 50005000`, jump `(3, 6, 9999)` |
| Q3 | `SET /A N=0 / SET /A S=100000000 / :DOWN / SET /A N=N+2 / SET /A S=S-N / IF %S% GTR 0 GOTO DOWN / ECHO %N% %S%` | halts after 30004 steps, prints `20000 -10000`, jump `(3, 6, 9999)` |
| Q4 | `SET /A K=0 / SET /A T=0 / :UP / SET /A K=K+1 / SET /A T=T+K / ECHO %T% / IF %K% LSS 5000 GOTO UP` | halts after 20003 steps, prints the triangular numbers `1` … `12502500` (5000 lines), `T` = 12502500, jump `(3, 7, 4999)` |
| Q5 | `SET /A I=0 / SET /A J=0 / SET /A S=0 / :L / SET /A I=I+1 / SET /A J=J+4000 / SET /A S=S+I / IF %S% LSS %J% GOTO L / ECHO %I% %S% %J%` | halts after 32001 steps, prints `7999 31996000 31996000`, jump `(4, 8, 7998)` |
| Q6 | `SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B-A / IF %B% LSS 1 GOTO UP` | never: pass `(3, 6)`, `d = {A: 1, B: -1}`, `g = {B: -1}` |
| Q7 | `SET /A V=-3000 / SET /A P=0 / :UP / SET /A V=V+1 / SET /A P=P+V / IF %P% NEQ 0 GOTO UP / ECHO %V% %P%` | halts after 18001 steps, prints `2999 0`, jump `(3, 6, 5998)` (`P` falls, turns at pass 2999, and is 0 again only at pass 5998) |
| Q8 | N5 of Phase 126 (`N=N*2`) | refused `UNDECIDED_WITHIN_BUDGET` (geometric; not an accumulator) |
| Q9 | `SET /A A=0 / SET /A B=0 / SET /A C=0 / :UP / SET /A A=A+1 / SET /A B=B+A / SET /A C=C+B / IF %C% LSS 100000000000 GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (`C` is fed by an accumulator: cubic) |
| Q10 | `SET /A N=0 / SET /A S=0 / :UP / SET /A N=N+1 / ECHO %S% / SET /A S=S+N / IF %N% LSS 4000 GOTO UP` | halts after 16003 steps, prints `0`, `1`, `3`, … `7998000` (4000 lines, `S` read before the line that adds to it), `S` = 8002000, jump `(3, 7, 3999)` |
| Q11 | `SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / IF %B% EQU 50 GOTO END / GOTO UP / :END / ECHO found` | never: pass `(3, 7)`, `d = {A: 1, B: 1}`, `g = {B: 1}` (`B` passes from 45 to 55 and is never 50: its sign changes, the outcome does not) |
| Q12 | as Q11 with `50005000` for `50` | halts after 40003 steps, prints `found`, jump `(3, 7, 9999)` |

The twenty questions: *does it halt?* of Q1–Q12 (yes with the steps and exit
code 0, no, or the refusal); *what does it print?* of Q2 (`10000 50005000`),
Q7 (`2999 0`) and Q12 (`found`); *what is the value of S?* of Q3 (`-10000`)
and of Q10 (`8002000`); *what is the value of T?* of Q4 (`12502500`); *how
many steps?* of Q5 (32001); *why is it undecided?* of Q1 (refused
`NOT_UNDECIDED`) and of Q9 (answered, with the reading's reason *found no
recurring state with the counters masked*).

## 4. The marks

| mark | what | met when |
|---|---|---|
| Q1 | the Lean file | `QuadraticLasso.lean` builds with no `sorry` and standard axioms only |
| Q2 | the battery | 12 of 12 as declared, 0 wrong |
| Q3 | the questions | 20 of 20 as declared |
| Q4 | the certificates | every `run_jump` and `never_lasso` claim of Q2 and Q3 verifies in its column-3 script, and every mutation of it is rejected |
| Q5 | non-interference | every program and question of the Phase 125, 126, 130, 131 and 132 batteries keeps the answer the Phase 132 reading gives, L12 and N6 apart (they hold an accumulator line, and move to Q1's verdict); all 300 generated programs keep their answers |
| Q6 | soundness | every jumped *halts* of the battery equals a plain run under `counter_lasso.LONG_BUDGET` (steps, output, exit code, variables); every new *never* is not contradicted by a plain run of that budget |
| Q7 | the first change, exhaustively | for every `e₀ ∈ [−40, 40]`, `b ∈ [−8, 8]`, `c ∈ [−5, 5]` and each of the six comparisons, the machine's first change equals a brute-force scan to `t = 400` (and none means no change up to 400), and the column-3 route agrees with both |
| Q8 | the evaluation | the end-to-end evaluation passes as before |

**Controls.** Q8 and Q9 are the refusals the rule must keep (geometric and
cubic growth). Q11 is the trap a sign-only reading falls into. `quadratic=False`
re-measures Phase 132's record.

## 5. What this round does not do

Geometric growth (`N=N*2`), cubic and higher growth (an accumulator fed by an
accumulator), accumulators fed by a non-counter variable or by an expression,
and products of counters stay refused. No change is made to the planner or the
other query kinds; the answers reach users through the GLM-BAT questions only.

## 6. Files

* `overlay/glm_lean/RequestProject/GLM/QuadraticLasso.lean` — §1.
* `overlay/glm_universal/reasoning/batch_machine.py` — `quadratic=True` in
  `jumped_run` and `run_program`; `accumulators`, `first_change_quadratic`.
* `overlay/glm_universal/reasoning/batch_speech.py` — the second interpreter's
  accumulators and first change; `g` in the `never_lasso` claim; the answer's
  wording; `answer(..., quadratic=False)`.
* `overlay/glm_universal/reasoning/quadratic_lasso.py` and
  `tools quadratic-lasso [--json]` — the battery and the marks.
* `overlay/glm_universal/tests/test_quadratic_lasso.py`.

## 7. The measurement

`python3 -m glm_universal.tools quadratic-lasso` (about two and a half
minutes; the soundness control runs ten plain runs of up to 2,500,000 steps).

### 7.1 The verdict

Yes, within the declared rule: all 12 battery programs came out exactly as declared, the loops whose step grows now halt with their exact step counts and outputs or are certified never to halt, and every answer the machine gave before is unchanged; one mark is missed on its declaration, because the question list it counted held 21 questions, not 20.

### 7.2 The marks

| mark | outcome |
|---|---|
| Q1 | **met**: `QuadraticLasso.lean` builds with no `sorry`; `#print axioms` gives `propext`, `Classical.choice`, `Quot.sound` for every theorem |
| Q2 | **met**: 12 of 12 as declared, 0 wrong — Q2 and Q3 halt after 30004 steps (jump `(3, 6, 9999)`), Q4 after 20003 printing 5000 triangular numbers (`(3, 7, 4999)`), Q5 after 32001 (`(4, 8, 7998)`), Q7 after 18001 (`(3, 6, 5998)`), Q10 after 16003 (`(3, 7, 3999)`), Q12 after 40003 (`(3, 7, 9999)`); Q1, Q6 and Q11 never, with the declared `d` and `g`; Q8 and Q9 refused |
| Q3 | **missed on its declaration**: every one of the 21 questions §3 lists came out as declared, but the mark was declared as *20 of 20* — §3 miscounted its own list (12 + 3 + 2 + 1 + 1 + 2 = 21). Recorded as missed, not restated |
| Q4 | **met**: 18 of 18 claims (7 `run_jump` and 3 `never_lasso` from the battery, 8 from the questions) verify in their column-3 scripts; 105 of 105 mutations rejected, including the two new mutations of `g` on each `never_lasso` claim |
| Q5 | **met**: the Phase 125 battery, questions and English programs as declared; 47 of 47 programs (the Phase 126, 130, 131 and 132 batteries and the Phase 132 diagnosis battery) and 58 of 58 questions give the same answer with and without the quadratic reading, L12 and N6 apart; 300 of 300 generated programs unchanged; L12 is now *never* |
| Q6 | **met**: 7 of 7 jumped *halts* equal a plain run of 2,500,000 steps in steps, output, exit code and variables; Q1, Q6 and Q11 do not halt in a plain run of that budget |
| Q7 | **met**: 90,882 cases (`e₀ ∈ [−40, 40]`, `b ∈ [−8, 8]`, `c ∈ [−5, 5]`, six comparisons); the machine's first change equals the brute-force scan in every case, and so does the column-3 route, taken from the checker's own source |
| Q8 | **met** (§7.4): 186 of 188 in the full run, the two misses retrieval figures that count Lean goal queries, re-pinned with their claims unchanged and passing on their own |

### 7.3 What was seen

* **The correction of §0 mattered.** Q2's test sits after the line that adds
  to `B`, so its linear coefficient is `β + g_r = 2`, not `β = 1`; with the
  first draft's coefficient the first change of Q2's test works out (by hand)
  at pass 10000 instead of 9999, one pass too late. Q4 and Q10 put an `ECHO` of the accumulator after and before its line
  respectively, and both print exactly the hand-worked sequences.
* **Q11 is the trap a sign-only reading falls into.** `B` passes from 45 to
  55: the sign of `B − 50` changes at pass 9, the outcome of `EQU` does not.
  The bisection finds the sign change, compares the outcome, and goes on; the
  unbounded stretch then starts at the extreme sign, so the verdict is
  *never*. Q12, the same loop with `50005000`, halts on the exact pass.
* **Q7 is the two-stretch case.** `P` falls until pass 2999 and rises after;
  `P ≠ 0` holds on the falling stretch, and the first change is found on the
  rising one at pass 5998.
* **Controls held.** Geometric growth (Q8) and cubic growth (Q9: `C` is fed
  by the accumulator `B`) stay refused; Q9's diagnosis still names `B`
  quadratic and `C` irregular, and the reading's reason is that no state
  recurs with the counters masked (`C` is not masked).
* **Phase 132's measurement is kept by reading it with `quadratic=False`**:
  its diagnosis battery holds L12 as a refusal, which the quadratic reading
  now decides.

### 7.4 The evaluation (mark Q8)

**Met.** The full evaluation (`python3 -m glm_universal.evaluation --jobs 8`,
188 cases) gave 186 of 188 after the corpus refresh: the two failures were
`report-relay` and `report-anonymous`, whose pinned figures count the Lean goal
queries, which `QuadraticLasso.lean` grows from 809 to 813 (relay: the
held-out goal queries 661 -> 664 of 813, ahead, the gate firing on 46 of 1626,
carrying 12 and losing 0; anonymous: text 661 -> 45 and structure 161 -> 157 of
813). Their claims are unchanged, as every earlier Lean file's re-pin recorded;
both were re-pinned and pass when run on their own (the full run was not
repeated after the re-pin). No GLM-BAT case moved.

### 7.5 What is left

* **Geometric growth** (`N=N*2`, N5, G2): the closed form `x₀·rᵗ` is proved
  (`const_ratio_closed_form`); a jump needs the first change of an
  exponential comparison, the next step of this line.
* **Cubic and higher growth** (an accumulator fed by an accumulator, Q9): the
  drift becomes `Σ C(m, k)·g_k`, and the first change a polynomial of degree
  three; `quadratic_iterate` generalises, the bisection needs one more
  stretch per degree.
* **Accumulators fed by a constant variable or an expression**, and products
  of counters, stay refused.
* **The rest of GLM-BAT** as Phase 132 left it: output past 1,000,000 lines,
  `ECHO` with redirection on a pass, constants read through `ERRORLEVEL`,
  comparisons of text.
