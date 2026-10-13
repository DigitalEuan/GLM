# Passes that print a counter, long output, and the diagnosis of a refusal

## Tier 0 — the coarse read

**Question.** Can GLM-BAT's counter-lasso reading jump a pass that prints a counter, state output past 100,000 lines in a short checkable form, and say *why* when it still cannot decide — with the Non-Random Coherence Index reported as a diagnosis only — without changing any verdict it already gave and without a verdict a long plain run contradicts?

**Verdict.** Yes, within the declared rule, with two marks missed on how the hand-worked expectations were stated. All 10 battery programs came out exactly as declared, 0 wrong: K5 (as P1) halts after 60,002 steps printing 1 to 20000, K4 (as P2) after 1,500,004 steps printing `tick` 500,000 times with a 208-byte claim in run form, and five more loops that print counters are answered exactly; the 8 refused programs of the diagnosis battery were diagnosed exactly as declared, and the closed forms predicted the next 32 visits of all 8 shaped variables. P8's printed text came out in the declared encoder's segments, not the hand-worked ones, and P2's whole script is over the declared 10,000 bytes because the checker alone is 26,819, so marks A3 and A4 are missed. Non-interference on every earlier answer and all 300 generated programs, and the soundness control against plain runs, were met. The NRCI of a straight line through L12's quadratic counter is 0.999993: a soft score would have called it a line.

**Deciding figure.** 7 of 9 marks; 10 of 10 programs as declared; 19 of 20 questions as declared; 8 of 8 diagnoses as declared and 8 of 8 closed forms predictive; 33 of 33 column-3 scripts verify and 167 of 167 mutations rejected; 26 of 26 earlier programs, 35 of 35 earlier questions and 300 of 300 generated programs unchanged; 8 of 8 jumped *halts* equal to a plain run.

**Recomputed by.** `glm_universal.reasoning.affine_output.affine_output_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 132, committed with its Lean file and before
the code of the rule exists. §§0–6 are as they were committed; §7 is what
came out.

It takes three lines of *GLM-BAT, the rest* in [`STATUS.md`](../STATUS.md)
§2.2, left by Phase 131 ([`CONSTANT_BOUND_STUDY.md`](CONSTANT_BOUND_STUDY.md)
§7.4), and answers the owner's question of this round — whether the
Non-Random Coherence Index (NRCI) could be useful where an additional layer of
diagnosis is required:

* **passes that print a counter** (K5) — the line written at step `r` of pass
  `m` is a template whose holes read the counters, so the skipped output is
  `m` blocks in closed form;
* **output past 100,000 lines** (K4) — a run-length statement of the claim,
  so that the column-3 script need not hold every line;
* **a diagnosis of the refusals that remain** — the shape of growth the
  reading does not take (L12, N5, N6: quadratic and geometric), the reason the
  reading took no jump, and the NRCI of a straight line through the last
  values, reported beside the exact test and never used to decide anything.

**Why NRCI is a diagnosis here and not a gate.** The project has already
proved, and recorded, why a coherence score must never admit an answer:
`GLM.SearchLoop.score_gate_unsound` (a score can prefer a candidate the data
has refuted), `GLM.SearchLoop.gate_blind` (no function of the observed
behaviour separates two survivors), and the archive's ledger rule D2 ("the
soft gate, never"). The NRCI definition is the one written down in Phase 29,
`1 − √(Σr²/Σx²)` with `r` the residuals of a model and `x` the values. This
round reports it on the one place a refused run has numbers to fit, and
declares in advance (mark A5) what it will show: a straight line fits a
quadratic counter with NRCI above 0.99, while
`GLM.AffineOutput.quadratic_not_translation` proves the counter is not a
translation. The exact finite-difference test names the shape; the NRCI shows
how far a soft score would have been fooled.

**Why not an item of §2.1.** As in Phases 130 and 131: items 1–4 each change
answers the evaluation pins and need a frozen-path comparison, and item 1's
premise does not hold yet (no query kind reads a carrier by its address).
This round adds faculties the machine lacks and is bound by the same
non-interference marks.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 131's record: K4 and K5
   refused `UNDECIDED_WITHIN_BUDGET`, halting plainly after 1,500,004 and
   60,002 steps; L12, N5 and N6 refused; K8 does not halt within 2,500,000
   plain steps. Nothing else about any program below had been run.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/AffineOutput.lean` was written and built first (§1).
3. **No code of the rule or of the diagnosis existed and no new program below
   had been run when this was committed.** Every expected answer in §3 was
   worked out by hand from the semantics of
   [`OPERATIONS_LADDER_STUDY.md`](OPERATIONS_LADDER_STUDY.md) §2.2 and the
   rules of [`COUNTER_LASSO_STUDY.md`](COUNTER_LASSO_STUDY.md) §2 and
   [`CONSTANT_BOUND_STUDY.md`](CONSTANT_BOUND_STUDY.md) §2, with Phase 131's
   lesson applied: the masked state is compared before every step, so a pass
   starts at the first step whose masked state recurs.

## 1. What is proved before any code

`RequestProject/GLM/AffineOutput.lean`, no `sorry`, standard axioms only, on
top of `RequestProject/GLM/ConstantBound.lean`.

* `wrun_pass_shifted` — with no hypothesis on what a step writes, a pass from
  the start translated by `m • d` ends at the start translated by
  `(m + 1) • d`, having written the first pass's lines as read from the
  translated states.
* `passOutput`, `lasso_output_affine` — `K` passes write pass `m`'s block, as
  read from the translate `m • d`, for `m = 0, …, K − 1`;
  `halts_of_jump_affine` — with a run in and out, the machine halts after
  exactly `i + K * p + n` steps having written `w₀`, the `K` blocks and `w₁`.
* `render`, `render_hole`, `render_append`, `render_const` — a line written
  from a template fills each hole naming counter `i` with `fmt (x_i + m·d_i)`:
  an arithmetic progression in every hole, and the same line on every pass
  when the template has no hole (Phase 131's repeated block).
* `templated_block` — so the block of pass `m` is the first pass's templates
  rendered at the counters translated by `m • d`.
* `diff`, `const_diff_closed_form`, `const_second_diff_closed_form`,
  `const_ratio_closed_form` — constant first differences give `x₀ + t·Δ`,
  constant second differences give `2x_t = 2x₀ + 2tΔ₀ + c·t(t−1)`, a constant
  ratio gives `x₀·rᵗ`; `quadratic_not_translation` — a non-zero constant
  second difference is never a translation.

The theorems do not say the Python's reading of a line is right; the column-3
script checks that with its own reading (§2).

## 2. The rule

Everything of [`CONSTANT_BOUND_STUDY.md`](CONSTANT_BOUND_STUDY.md) §2 stands;
the reading with the clauses below is called the *affine* reading (Phase
131's is kept, as `affine=False`, so that its record can be re-measured; the
affine reading needs `extended`).

**Passes that print a counter.** A line of the `echo` kind on a pass (an
`ECHO` with no redirection, pipe or chain that names a live counter) no longer
stops a jump. Before the step, its text is read as a *template*: each `%V%`
with `V` a counter is a hole, every other `%X%` is replaced by its value at
that step (or `ERRORLEVEL`'s), and everything else is literal. If a hole
names a counter that is not live, the pass is not jumped. The jump appends,
for each skipped pass `t = 1, …, m* − 1`, the first pass's lines in order,
each `echo` line rendered with every hole `V` filled by `str(v_V + t·d_V)`,
where `v_V` is `V`'s value at that step of the first pass, and every other
step's lines as written (`templated_block`, `lasso_output_affine`).

**The output bound.** Under the affine reading a jump over a writing pass is
taken while the output after it holds at most **1,000,000 lines** (standard
output and standard error together; Phase 131's bound was 100,000).

**Claims in run form.** When a claim's standard output and standard error
together hold more than 100,000 lines, the claim states them as `out_runs`
and `err_runs` instead of `out` and `err`: a list of segments
`[block, count, steps]`. A segment is decoded as `count` copies of `block`
(a list of lines), where in copy `t` the `j`-th integer written in the block
(the `j`-th match of `-?\d+`) is advanced by `t · steps[j]`. The encoder is
greedy: at each position it takes the block length `q ∈ 1..16` and the
largest `count ≥ 2` whose decoding reproduces the lines exactly, covering the
most lines (ties to the smaller `q`), or else one line with `count` 1. Every
claim of 100,000 lines or fewer keeps `out` and `err` as before.

**What the GLM says.** *Does it halt?* as in Phase 131, with "(naming N)"
after "writing *k* lines each time" when the pass writes a counter. *What does
it print?* of a run with a jump over a pass that writes a counter, or with
more than 100,000 lines of output, states the output in segments: a repeated
line as `"tick" (500000 times)` (Phase 131's form), a progression of single
lines as `"1" … "20000" (20000 lines; the number steps by 1)` (or `the
numbers step by 1, 3` when a line holds several integers), and a progression
of blocks as `["tick", "N=1"] … ["tick", "N=30000"] (30000 times; the number
steps by 1)`. Every other answer text is as before.

**The diagnosis of a refusal.** A new question, *why is it undecided?* (also
*why can it not decide?*), refused `NOT_UNDECIDED` for a run that is decided.
For an undecided run:

* *the loop head* — run plainly for the budget (10,000 steps); the head is the
  line executed most often (ties to the earliest line), with its number of
  visits;
* *the shapes* — over the last 32 visits, each variable whose value is not
  the same at all of them: `translation Δ` (first differences constant),
  `quadratic c` (second differences constant, `c ≠ 0`), `geometric r` (an
  integer `r` with `x_{t+1} = r·x_t`, values non-zero), `irregular` (integers,
  none of these), or `text` (not all canonical integers); and each file whose
  contents are not the same at all of them;
* *the block* — why the counter-lasso reading took no jump: it found no
  recurring masked state; or a recurring pass on which a line cannot sit
  (named); or a jumpable pass whose output would pass the bound; or it reached
  its jump limit;
* *the NRCI* — for every `quadratic`, `geometric` or `irregular` variable,
  the NRCI `1 − √(Σr²/Σx²)` of the least-squares straight line through its
  last 32 values (exact rationals, printed to four places), stated as "a
  diagnosis, not a certificate". It decides nothing: no verdict, refusal or
  jump reads it.

The answer is
`undecided: at line H (visited n times in 10000 steps), <shapes>; the
counter-lasso reading <block> (<NRCI sentences>)`, with each shape phrased
`V moves by a fixed step (+1 per visit)`, `V grows quadratically (second
difference 1)`, `V grows geometrically (ratio 2)`, `V changes irregularly`,
`V changes as text`, `file F changes`. Its claim, kind `growth`, holds the
head line, the visits, the shapes and the changing files, which the column-3
checker re-derives with its own plain run; the block and the NRCI are not in
the claim.

**When it is used.** As in Phase 130: the jump reading only when the Phase
125 run and the Phase 126 inert re-reading are both undecided; the diagnosis
only when asked.

## 3. The marks, declared before the code

The battery (lines separated by ` / `; steps count from 0; "jump `(i, j, m)`"
as in Phase 130):

| program | lines | expected |
|---|---|---|
| P1 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / IF %N% LSS 20000 GOTO UP` (K5) | halts after 60002 steps, out `1`, `2`, …, `20000`, exit 0, `N` = 20000; jump `(2, 5, 19999)` |
| P2 | `SET /A N=0 / SET LIM=500000 / :UP / ECHO tick / SET /A N=N+1 / IF %N% LSS %LIM% GOTO UP / ECHO %N%` (K4) | halts after 1500004 steps, out `tick` × 500000 then `500000`, exit 0; jump `(3, 6, 499999)`; its claim states `out_runs` |
| P3 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO tick / ECHO N=%N% / IF %N% LSS 30000 GOTO UP` | halts after 120002 steps, out `tick`, `N=1`, …, `tick`, `N=30000` (60000 lines), exit 0; jump `(2, 6, 29999)` |
| P4 | `SET /A N=10 / :DOWN / ECHO %N% / SET /A N=N-1 / IF %N% GEQ -20000 GOTO DOWN` | halts after 60035 steps, out `10`, `9`, …, `-20000` (20011 lines), exit 0, `N` = -20001; jump `(2, 5, 20010)` |
| P5 | `SET /A I=0 / SET /A J=100 / :L / SET /A I=I+1 / SET /A J=J+3 / ECHO %I%:%J% / IF %I% LSS 10000 GOTO L` | halts after 40003 steps, out `1:103`, `2:106`, …, `10000:30100`, exit 0; jump `(3, 7, 9999)` |
| P6 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / IF %N% LSS 1200000 GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (the output would pass 1,000,000 lines) |
| P7 | `SET P=item / SET /A N=0 / :UP / SET /A N=N+1 / ECHO %P% %N% / IF %N% LSS 25000 GOTO UP` | halts after 75003 steps, out `item 1`, …, `item 25000`, exit 0; jump `(3, 6, 24999)` |
| P8 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N%%N% / IF %N% LSS 5000 GOTO UP` | halts after 15002 steps, out `11`, `22`, …, `50005000` (each `N` written twice), exit 0; jump `(2, 5, 4999)` |
| P9 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% / TYPE missing.txt / IF %N% LSS 15000 GOTO UP` | halts after 60002 steps, out `1`, …, `15000`, standard error `The system cannot find the file specified.` × 15000, exit 1; jump `(5, 9, 14999)` |
| P10 | `SET /A N=0 / :UP / SET /A N=N+1 / ECHO %N% > last.txt / IF %N% LSS 20000 GOTO UP` | refused `UNDECIDED_WITHIN_BUDGET` (the file changes on every pass, so no masked state recurs) |

The diagnosis battery (L12 of Phase 130, N5 of Phase 126 and K8 of Phase 131
as they were declared; P6 and P10 above; three new programs):

| program | lines | expected diagnosis |
|---|---|---|
| L12 | `SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / IF %B% GTR -1 GOTO UP` | head line 4, 3333 visits; `A` translation +1, `B` quadratic 1; no recurring masked state; the straight line through `B` has NRCI above 0.99 |
| N5 | `SET /A N=1 / :UP / SET /A N=N*2 / SET /A Q=10/N / GOTO UP` | head line 3, 3333 visits; `N` geometric 2 (`Q` is the same at every visit and is not listed); no recurring masked state |
| K8 | `SET /A N=0 / SET L=abc / :UP / SET /A N=N+1 / IF %N% LSS %L% GOTO UP` | head line 4, 4999 visits; `N` translation +1; a recurring pass on which line 5 cannot sit |
| P6 | above | head line 3, 3333 visits; `N` translation +1; the output would pass 1,000,000 lines |
| P10 | above | head line 3, 3333 visits; `N` translation +1; file `last.txt` changes; no recurring masked state |
| G1 | `SET /A A=0 / SET /A B=1 / :UP / SET /A C=A+B / SET /A A=B / SET /A B=C / IF %B% GTR -1 GOTO UP` | head line 4, 2500 visits; `A`, `B`, `C` irregular; no recurring masked state |
| G2 | `SET /A N=1 / :UP / SET /A N=N*3 / IF %N% GTR 0 GOTO UP` | head line 3, 4999 visits; `N` geometric 3; no recurring masked state |
| G3 | `SET /A N=0 / SET S=x / :UP / SET /A N=N+1 / SET S=%S%x / IF %N% GTR 0 GOTO UP` | head line 4, 3333 visits; `N` translation +1, `S` text; no recurring masked state |

| mark | statement |
|---|---|
| **A1** | `RequestProject/GLM/AffineOutput.lean` builds with no `sorry` and only the standard axioms, with the theorems of §1. |
| **A2** | **The battery.** P1–P10 as declared, 0 wrong (status, step count, outputs, standard error where declared, exit code, values, jumps). |
| **A3** | **The questions.** *Does it halt?* of P1–P10 as declared; *what does it print?* of P1 has the value `1` … `20000` and its text holds `"1" … "20000" (20000 lines; the number steps by 1)`, of P2 holds `"tick" (500000 times), "500000"`, of P8 holds `"11" … "99" (9 lines; the number steps by 11), "1010" … "9999" (90 lines; the number steps by 101), "100100" … "999999" (900 lines; the number steps by 1001), "10001000" … "50005000" (4001 lines; the number steps by 10001)`; *what is the value of N?* of P4 is `-20001`; *how many steps?* of P5 is 40003; *what is the exit code?* of P9 is 1; *why is it undecided?* of L12 holds `B grows quadratically (second difference 1)`, of P6 holds `would pass 1000000 lines`, of G1 holds `C changes irregularly`, and of P1 is refused `NOT_UNDECIDED` — 20 questions. |
| **A4** | **Certificates.** Every `run_jump`, `never_lasso` and `growth` claim of A2, A3 and A5 has a column-3 script that passes under `python3 -I`, and every mutation fails (Phase 131's mutations; for a claim in run form, a segment count lowered by one and a step raised by one; for a `growth` claim, the head moved by one line and a shape's parameter raised by one). P2's script is under 10,000 bytes. |
| **A5** | **The diagnosis.** The eight programs of the diagnosis battery as declared (head line, visits, shapes, changing files, block), 0 wrong; the NRCI of the straight line through L12's `B` is above 0.99. |
| **A6** | **The closed forms predict.** For every `translation`, `quadratic` and `geometric` variable of A5, the closed form read from the window (`const_diff_closed_form`, `const_second_diff_closed_form`, `const_ratio_closed_form`) gives that variable's value at each of the next 32 visits of a longer plain run. |
| **A7** | **Non-interference on the machine.** The Phase 125 battery (25 runs), its 18 questions and its 6 English programs; the Phase 126, 130 and 131 batteries and questions other than N2, N3, L10, L11, K4 and K5, read with the affine reading, give the answers Phase 131's reading gives (status, certificate, `d`, steps, outputs, exit code, jumps; answer text, refusal and claim); K4 and K5 move to P2's and P1's runs. Every one of the 300 generated programs keeps its verdict, step count, outputs, standard error, exit code and files. |
| **A8** | **Soundness control.** Every program the affine reading says halts (battery or generated) halts when run plainly under 2,500,000 steps with the same step count, outputs, standard error, files, variables and exit code; the refused controls, plainly: P6 halts after 3600002 steps (under 4,000,000), and P10 after 60002 steps with `last.txt` holding `20000`. |
| **A9** | **Non-interference on the system.** All 179 evaluation cases pass with 0 confidently wrong. Re-pins are allowed only for the retrieval figures that count goal queries sampled from the Lean development (`report relay`, `report anonymous`), which a new Lean file moves. |

**Not predicted:** the NRCI of any variable other than L12's `B`; how many of
the 300 generated programs are undecided, and their diagnoses (A4 binds every
`growth` claim made of them either way, and the count is reported); whether
any generated program takes a jump the Phase 131 reading did not (A7 binds
their answers either way).

## 4. Controls

* **P6** is the control on the new output bound, and **P10** on output that
  goes to a file: a pass whose written counter changes a file changes the
  masked state, so it must not be read as a lasso.
* **P8** is the control that the template is read from the line and not
  guessed from the output: `%N%%N%` writes `1010` after `99`, which no single
  arithmetic progression of the output describes; the run is exact and the
  answer text needs four segments.
* **P9** is the control on standard error and the exit code inside a pass
  that writes a counter.
* **L12, N5, G1, G2** are the controls on the diagnosis: four growths that are
  not translations, and **G3** a growth of text.
* **K8, P6, P10** are the controls that a translation the reading *could*
  jump is diagnosed by the reason it did not.
* **A6** is the control that the shapes are not overfitted to the window, and
  **A8** the control that does not trust the theorems or the reading.
* **The multiplicity count.** Phase 131 stood at 66 statistics; this round
  adds the battery and the diagnosis battery, so **68**. No bit score is
  computed. The NRCI figures are reported, not tested.

## 5. What this round does not do

* No jump over a growth that is not a translation: the diagnosis names
  quadratic and geometric growth and proves their closed forms, but no
  verdict reads them yet.
* No `ECHO` with redirection or inside a chain or a test body on a jumped
  pass; no constant read through `ERRORLEVEL`, and no comparison of text.
* No output past 1,000,000 lines from a jump.
* The NRCI is never a gate: no verdict, refusal, jump or claim reads it.
* No change to the fragment, the English reader or the sayer outside the
  answer texts of §2, the planner, or any router path.

## 6. Files

* `RequestProject/GLM/AffineOutput.lean` — A1.
* `overlay/glm_universal/reasoning/batch_machine.py` — the templates, the
  affine clause and the bound in `jumped_run`, behind `affine` (default on),
  threaded through `run_program`; the reason a run took no jump; and
  `growth_diagnosis`.
* `overlay/glm_universal/reasoning/batch_speech.py` — the checker's affine
  clause, run-form claims and the `growth` claim, the answer texts, the
  mutations, the new question, and `affine` threaded through `answer`.
* `overlay/glm_universal/reasoning/affine_output.py` — the batteries and the
  marks; `python3 -m glm_universal.tools affine-output`.
* `overlay/glm_universal/reasoning/constant_bound.py` — Phase 131's
  measurement, read with `affine=False` so that it keeps measuring the rule it
  declared.
* Tests: `test_affine_output.py`.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`PYTHONPATH=. python3 -m glm_universal.tools affine-output` takes every mark
except A1 and A9 in about three minutes; `tests/test_affine_output.py` (13
tests) pins them as measured.

### 7.1 The verdict

Yes, within the declared rule, with two marks missed on how the hand-worked expectations were stated. All 10 battery programs came out exactly as declared, 0 wrong: K5 (as P1) halts after 60,002 steps printing 1 to 20000, K4 (as P2) after 1,500,004 steps printing `tick` 500,000 times with a 208-byte claim in run form, and five more loops that print counters are answered exactly; the 8 refused programs of the diagnosis battery were diagnosed exactly as declared, and the closed forms predicted the next 32 visits of all 8 shaped variables. P8's printed text came out in the declared encoder's segments, not the hand-worked ones, and P2's whole script is over the declared 10,000 bytes because the checker alone is 26,819, so marks A3 and A4 are missed. Non-interference on every earlier answer and all 300 generated programs, and the soundness control against plain runs, were met. The NRCI of a straight line through L12's quadratic counter is 0.999993: a soft score would have called it a line.

### 7.2 The marks

| mark | what | result |
|---|---|---|
| A1 | the Lean file | **met**: `RequestProject/GLM/AffineOutput.lean` builds with no `sorry`; `#print axioms` gives `propext`, `Classical.choice`, `Quot.sound` for `lasso_output_affine`, `halts_of_jump_affine`, `const_second_diff_closed_form` and `quadratic_not_translation`, `propext` and `Quot.sound` for `templated_block`, and `propext` for `render_const` and `const_ratio_closed_form` |
| A2 | the battery | **met**: 10 of 10 exactly as declared — P1 60002, P2 1500004, P3 120002, P4 60035 (`N` = -20001), P5 40003, P7 75003, P8 15002, P9 60002 with exit 1 and 15,000 lines of standard error, each with the declared jump; P6 and P10 undecided |
| A3 | the questions | **missed**: 19 of 20 as declared; *what does it print?* of P8 has the right value but not the declared text (§7.3) |
| A4 | certificates | **missed** on one clause: 33 of 33 `run_jump` and `growth` scripts pass under `python3 -I` and 167 of 167 mutations fail, but P2's script is 27,251 bytes, not under 10,000: its claim is 208 bytes and the checker it carries is 26,819 (§7.3) |
| A5 | the diagnosis | **met**: 8 of 8 as declared (head line, visits, shapes, changing files, block); the NRCI of the straight line through L12's `B` is 0.999993 |
| A6 | the closed forms predict | **met**: all 8 `translation`, `quadratic` and `geometric` variables of A5 are predicted exactly at each of the next 32 visits |
| A7 | non-interference on the machine | **met**: Phase 125's 25 runs, 18 questions and 6 English programs as declared; the 26 programs and 35 questions of the Phase 126, 130 and 131 batteries other than N2, N3, L10, L11, K4 and K5 give exactly the answers of Phase 131's reading; K4 and K5 give P2's and P1's runs; 300 of 300 generated programs unchanged, none takes a new jump |
| A8 | soundness control | **met**: all 8 jumped *halts* (P1–P5, P7–P9) equal a plain run in steps, outputs, standard error, files, variables and exit code; plainly, P6 halts after 3600002 steps and P10 after 60002 with `last.txt` holding `20000` |
| A9 | non-interference on the system | **met**: 177 of 179 cases before any re-pin, 0 errors; the two that moved are `report relay` and `report anonymous`, re-pinned because the goal-query set grew from 837 to 840; after the re-pin all 179 pass with 0 confidently wrong (§7.3) |

### 7.3 What was seen

* **The P8 miss is in the hand computation of the encoder, not in the
  rule.** The declared encoder takes, at each position, the block length that
  covers the most lines. Working P8 by hand I compared only block lengths
  whose blocks stay inside one run of equal digit counts, and so expected
  `"11" … "99"` (9 lines) first. Two blocks of 16 lines (`11` to `3232`)
  also form a valid progression — every one of the 16 numbers advances by a
  fixed step from the first block to the second — and cover 32 lines, so the
  encoder takes them; the rest of the text then follows (`"3333" … "9999"`
  (67 lines; the number steps by 101), then the 900- and 4001-line segments
  as declared). The value, the claim and the run are exact; the text is a
  faithful but unhelpful statement of the first 32 lines. A rule that asks
  for at least three copies of a block would give the declared text; it is
  left as a To-Do line rather than changed after the measurement.
* **The P2 size clause was stated against the wrong quantity.** The point of
  the run form is that the claim need not hold every line, and it does not:
  P2's claim is 208 bytes, where its 500,001 lines as a list would be about
  four megabytes. But every column-3 script carries the second interpreter,
  which is 26,819 bytes by itself, so no script of this surface could have
  been under 10,000 bytes. The mark is recorded as missed.
* **A mutation of the first measurement was vacuous.** The first full run
  reported 167 of 170 mutations rejected: for P2's claim (three times, from
  the battery and two questions) the "step raised by one" mutation chose the
  single-line segment `"500000"`, whose step is never applied. The mutation
  now chooses a segment with at least two copies; the 167 that remain are all
  rejected. No claim or verdict changed.
* **The two re-pins.** The full evaluation, run after `corpus --refresh`
  with `AffineOutput.lean` in the corpus, passed 177 of 179 cases with 0
  errors before any re-pin; the two that moved are the two named by A9, and
  both moved only because the goal-query set sampled from the Lean
  development grew from 837 to 840 queries. Re-pinned (comments in
  `evaluation/cases.py`): the relay reads 699 -> 701 of 840 (ahead) on bare
  goal queries, the gate fires on 44 of 1680 and the stack carries 8 queries
  it misses while losing 0; the anonymous register reads text 699 -> 53 of
  840 and structure 153 -> 150 of 840. The text baseline fell from 720 to
  699 with three more queries, so the new sample is harder for every faculty;
  both claims are unchanged — the relay is still ahead on every set and loses
  nothing, and the text search still falls to chance while the structural
  address holds. Re-pinning stales the stored query-escalation measurement,
  which was re-taken (`tools queryesc --write`); the close re-checks all 179.
* **The first NRCI was a float, and the frozen path caught it.** The first
  implementation took the NRCI as `1.0 - float(ratio) ** 0.5`, a float
  constructed inside `reasoning/`, one of the six sub-packages the Universal
  Binary Principle is claimed for. Nothing in this study's marks looks for
  that; the frozen-path re-check (the lattice-completion study's B5) did, because
  `report blueprint` read the source discipline as broken and moved one
  claim from confirmed to refuted (an undeclared text change). The NRCI is
  now held in millionths from an integer square root of its exact rational
  squared form (`batch_machine.line_nrci`, printed by `nrci_decimal`); every
  figure is unchanged (L12's `B` 0.999993), the blueprint reads the core
  clean again, and the frozen path holds with no undeclared change.
* **One measurement that reads the Lean corpus moved.** With
  `AffineOutput.lean` the corpus holds 5,035 declarations, and the stack
  relay's gate sweep (`test_stack.py`) moved back to where Phase 59 left it:
  the gain is strict on four gates, to 1/5, and one query behind the text
  control at 1/4 (350 against 351 of 420 tuning queries). The relay is
  still ahead of the text control on every set and loses nothing at the
  declared gate of 1/10. Recorded as measured in `test_stack.py` and
  [`STACK_RELAY_STUDY.md`](STACK_RELAY_STUDY.md), not as a loss of this
  round's code: no Python of the retrieval path changed.
* **What the diagnosis says.** L12: `A moves by a fixed step (+1 per visit);
  B grows quadratically (second difference 1)`; N5 and G2: geometric with
  ratios 2 and 3; G1 (Fibonacci): all three variables irregular; G3: `S
  changes as text`; K8: a recurring pass on which line 5 (the comparison with
  the text `abc`) cannot sit; P6: a jumpable pass whose output would pass
  1,000,000 lines; P10: no recurring state, with `file last.txt changes`.
  None of the 300 generated programs is undecided, so the diagnosis had
  nothing to read there.

### 7.4 The NRCI as a diagnosis

The owner asked whether the Non-Random Coherence Index could serve where an
additional layer of diagnosis is required. Measured here, with the Phase 29
definition `1 − √(Σr²/Σx²)` of a least-squares straight line through the last
32 values of each variable the exact test does not call a translation:

| program | variable | exact shape | NRCI of a straight line |
|---|---|---|---|
| L12 | `B` | quadratic, second difference 1 | 0.999993 |
| G1 | `A`, `B`, `C` | irregular (Fibonacci) | 0.246089 each |
| N5 | `N` | geometric, ratio 2 | 0.178394 |
| G2 | `N` | geometric, ratio 3 | 0.121055 |

What it shows, in the terms the project already uses:

* **As a gate it would be wrong exactly where it matters.** The one
  quadratic counter, which `quadratic_not_translation` proves is not a
  translation, scores 0.999993 — above any threshold a coherence band would
  set. A rule "treat a variable as a counter when a line fits it with NRCI
  above 0.99" would have read `B` as a fixed-step counter, which it is not
  (its step grows by one on every visit), and any jump taken on that reading
  would have been unsound. This is
  `GLM.SearchLoop.score_gate_unsound` and the archive's rule D2 measured on a
  new surface.
* **As a description it is informative.** It separates near-linear growth
  (L12) from growth a line cannot follow (geometric, Fibonacci), and the
  three Fibonacci variables, which are shifts of one sequence, score the same.
  It is reported next to the exact shape, labelled "a diagnosis, not a
  certificate", and nothing reads it: not the verdict, the refusal, the jump,
  or the column-3 claim.
* **The exact layer is what earns the answer.** The finite-difference shapes
  are exact, re-derived by the second interpreter in every `growth` claim, and
  predictive (A6); the NRCI adds a graded figure on top of them and is useful
  in that place only.

### 7.5 What is left

* **Jumps over quadratic and geometric growth.** The diagnosis names them and
  `const_second_diff_closed_form` and `const_ratio_closed_form` give the
  closed forms, but no verdict reads them yet: a jump over a pass whose
  counter grows quadratically needs the first change of a quadratic
  comparison, which is the next step.
* **The encoder's choice of block** (P8): at least three copies of a block,
  or the shortest block among those covering the most lines over a longer
  horizon, would state P8 as declared.
* **Output past 1,000,000 lines**, `ECHO` with redirection or inside a chain
  or test body on a pass, constants read through `ERRORLEVEL`, comparisons of
  text, and the rest of GLM-BAT, as Phase 131 left them.
* **The statistics count** is now 68 (§4); no bit score was computed.
