# The operations ladder — an old-style machine, learnt as a language

## Tier 0 — the coarse read

**Question.** Can the GLM take the owner's DevOps ladder as a new domain — ninety-seven operational terms, each defined as a composition of lower ones — and an old-style batch machine built from its two lowest tiers, and use them to work things out: say a program as sentences and read it back exactly, answer what a program prints, leaves behind or exits with, decide whether it halts or is idempotent with a certificate, and refuse by name where it cannot know, without a wrong answer?

**Verdict.** Yes, within the declared fragment. The 97 terms of the note are the register tier by tier with every composition layered and grounded; all 25 machine runs, all 18 English questions and all 6 English-written programs came out as declared with 0 wrong answers, every refusal by its declared name; all 78 battery lines were said as sentences and read back exactly; and all 41 answered runs and questions carry a column-3 Python script that passes in a fresh interpreter, while all 158 of their mutations fail. Hypothesis H held narrowly (185 of 242 composition edges monotone against 3/4), but the mean Geometric-Cybernetic tier is not monotone in the DevOps tier, so the two ladders agree on most edges and disagree on the coarse order.

**Deciding figure.** 9 of 9 marks; 25 of 25 runs, 18 of 18 questions, 6 of 6 English programs, 78 of 78 lines read back, 41 of 41 scripts verify and 158 of 158 mutations rejected; 14 of 14 cross-overs resolve; H 185/242 against 3/4; post hoc, 299 of 299 decided generated programs agree between the machine and column 3.

**Recomputed by.** `glm_universal.reasoning.operations.operations_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the modules that take the
measurement exist. §§0–6 are as they were committed; §7 is what came out.

The owner asked for many more domains and wheels, and in particular for
"older-style computer operations" the GLM could use to *consider* or *work
things out* — "like a sandbox, but more in the way we have the GLM learn the
information as a language so it can reason with it" — starting from the
supplied research note
[`source_material/devops_ladder/DevOps-Ladder.txt`](../source_material/devops_ladder/DevOps-Ladder.txt),
"but do what works properly for the GLM". This round is not on the To-Do list
of [`STATUS.md`](../STATUS.md) §2.1; it is taken at the owner's direction, and
the record says so.

**Order of work, stated plainly.**

1. *What existed before this was written.* The supplied note, read in full.
   The engineering surface's formula wheels (`engineering/wheels.py`), the
   Python dialect and its reverse grammar (`reasoning/python_speech.py`,
   `reasoning/reverse_tct*.py`), the toolbox (`runtime/toolbox.py`) and the
   register base class (`data_objects/base.py`) were read to decide where the
   new domain sits. No module of this round existed.
2. *Committed with this document:* the ladder register itself — the 97 terms,
   the declared composition of each, the declared projection onto the
   Geometric–Cybernetic ladder and the declared cross-overs — as data in
   `glm_universal/reasoning/ops_ladder.py`, with no code that
   measures it; and `RequestProject/GLM/OperationsLadder.lean`, written and
   built first.
3. **No script of the battery below had been run, and no relation, projection
   census or carrier had been computed, when this was committed.** Every
   expected answer in §3 was worked out by hand from the semantics in §2.

## 1. What the note proposes, and what is taken from it

The note proposes three things. Each is taken, and each is turned into
something the GLM can check rather than assert.

* **A ladder as a dictionary, bottom-up and compositional.** Ten tiers, from
  the machine substrate (process, stream, exit code, …) to culture (flow,
  blamelessness, …), "each tier rests on the one below it", "higher tiers
  compose lower ones". Here every one of the 97 terms gets a **declared
  composition** — the terms it is built from — and the register enforces the
  note's rule as a refinement check (D12): a term is built only from terms of
  a strictly lower tier, or from a term listed *earlier* in its own tier. That
  rank strictly decreases along every composition, so the composition graph
  has no cycle (`GLM.OperationsLadder.layered_wf`), every term **grounds** in
  a finite set of the ten tier-0 primitives, and the relation between any two
  terms — the note's own test question, *"what is the geometric relation
  between a pipe and a feedback loop?"* — is **computed** from the two
  closures (what one is built from, what they share, the least terms built
  from both), never stored.
* **Tier 0–1 as registers that connect reasoning to execution.** "Environment
  variables, exit codes, pipes and redirection form the natural registers."
  Here the two lowest tiers become an actual machine — **GLM-BAT**, a small
  DOS-batch-style language with environment variables, exit codes
  (`ERRORLEVEL`), files and directories, standard output and error,
  redirection, pipes, conditionals, loops, labels, jumps and subroutines —
  executed exactly and deterministically. It is the place the GLM *works a
  program out*: it runs it, and every run is a trace.
* **Learnt as a language.** Every GLM-BAT instruction has one English
  sentence, generated from the parsed instruction, and the sentence reads back
  to exactly that instruction. A program can be written in either form, and a
  question about a program is asked in English. That is the reverse-grammar
  discipline of the Python dialect (`studies/REVERSE_TCT_STUDY.md`) applied to
  a second machine.
* **The Geometric–Cybernetic ladder** the note recommends as the primary
  wheel, with DevOps "as a secondary application register projected onto it".
  The projection is declared term by term (each DevOps term to one GC term),
  and the note's implicit claim — that the projection respects the layering —
  is **tested** as hypothesis H below rather than assumed.

What is *not* taken: the note's claims of novelty (not a measurement), and its
suggestion that the ladder become "the internal medium of thought" of the
whole GLM. The register is a domain beside the others; whether it should feed
the planner is left as a To-Do line.

## 2. The objects

### 2.1 The register

The 97 terms of the note's ten tiers, in the note's order, each with a short
identifier, its display name as the note writes it, its tier, and its declared
composition (data in `reasoning/ops_ladder.py`). Two derived sets:

* the **closure** `C(t)`: `t` and everything it is built from, transitively;
* the **ground** `G(t) = C(t) ∩ tier 0`.

The **relation** between `a` and `b` is read in this order: `a` is a part of
`b` (`a ∈ C(b)`, with one shortest composition chain as the witness), or the
converse; otherwise the **shared parts** (the maximal elements of
`C(a) ∩ C(b)` under composition) and the **least common composers** (the terms
`t` with `a, b ∈ C(t)` of least tier, then least index). The ground overlap
`|G(a) ∩ G(b)| / |G(a) ∪ G(b)|` is an exact fraction.

**The carrier.** Each term is a 24-vector (exact integers): coordinates 0–9
count the distinct composition paths from the term down to each tier-0
primitive; 10 is the tier; 11–20 count the closure's terms in each tier; 21
is the index within the tier; 22 the size of the declared composition; 23 the
depth (longest chain to tier 0). Decoding reads (tier, index) and recomputes
the other 22 coordinates, so a carrier that does not match its own term fails
the semantic round trip; the substrate round trip is the base class's.

### 2.2 GLM-BAT, the machine

A program is a list of lines. The **state** is (program counter, environment,
files, directories, call stack, exit code) plus the two output streams. One
**step** executes one line. The fragment:

| form | meaning |
|---|---|
| `REM text` | nothing |
| `:LABEL` | nothing when reached by falling through; `GOTO LABEL` and `CALL :LABEL` continue at the line *after* it |
| `ECHO text` | write `text`, after expansion, to standard output |
| `SET NAME=text` | bind `NAME` to `text` after expansion |
| `SET /A NAME=expr` | integer arithmetic over `+ - * / %` and parentheses, names read as integers, `/` truncating toward zero as `cmd` does; division by zero writes `Divide by zero error.` to standard error, sets the exit code to 1 and leaves `NAME` unchanged |
| `IF [NOT] ERRORLEVEL n cmd` | true when the exit code is at least `n` (the DOS rule) |
| `IF [NOT] "a"=="b" cmd` | string equality after expansion |
| `IF [NOT] a OP b cmd` | `OP` one of `EQU NEQ LSS LEQ GTR GEQ`, compared as integers when both sides are integers, else as strings |
| `IF [NOT] EXIST path cmd`, `IF [NOT] DEFINED NAME cmd` | a file or directory exists; a name is bound |
| `GOTO LABEL`, `GOTO :EOF` | jump; `:EOF` returns from a subroutine or ends the program |
| `CALL :LABEL` | push the return line and jump |
| `EXIT /B n` | return from a subroutine with exit code `n`, or end the program with it |
| `EXIT n` | end the whole program with exit code `n` |
| `FOR %%V IN (a b c) DO cmd` | run `cmd` once per item with `%%V` replaced; a `GOTO` in `cmd` leaves the loop; the whole loop is one step |
| `TYPE path`, `DEL path`, `COPY a b`, `MKDIR path` | the file commands; a missing file or directory writes the `cmd` message to standard error and sets the exit code to 1, success sets it to 0 |
| `SORT`, `FIND "s"`, `FIND /C "s"` | filters on their input: sorted lines; the lines containing `s` (exit code 0 if any, else 1); their count |
| `c > f`, `c >> f`, `c < f`, `c1 \| c2` | redirection and pipes; text before a redirection loses its trailing spaces (a declared departure from `cmd`, which keeps them) |
| `c1 && c2`, `c1 \|\| c2` | `c2` runs when `c1` succeeded, or failed; grouped left to right |

`ECHO`, `SET`, `IF`, `GOTO`, `REM` and labels leave the exit code alone;
`%ERRORLEVEL%` expands to the exit code unless the program bound the name.
A program ends when the counter passes the last line; its exit code is then
the current exit code. A path `d/f` needs the directory `d`.

**Halting, certified.** A run that ends is its own certificate (its trace).
For a run that does not end, the machine records the **control state** before
each step — the state *without* the two output streams, which no instruction
reads back (output that is meant to be read is redirected into a file, and
files are in the control state). If two control states are equal, `s_i = s_j`
with `i < j`, the run never ends: the step function on control states is
deterministic and commutes with forgetting the streams
(`GLM.OperationsLadder.never_halts_of_projected_repeat`). The certificate is
the least such `j` with its `i`. A run that reaches the budget (10,000 steps)
with no repeat is **refused** (`UNDECIDED_WITHIN_BUDGET`): it may halt later,
or never.

**Refusals, by name.** `UNKNOWN_COMMAND` (a command outside the fragment —
the machine never guesses one), `UNDEFINED_VARIABLE` (an answer that depends
on expanding a name nobody bound; `IF DEFINED` is not such a read), `SYNTAX`
(a line the reader does not parse), `UNDECIDED_WITHIN_BUDGET`, and for a
question, `UNREAD_QUESTION`.

**Idempotence**, the note's tier-2 term made operational: a program is
*idempotent in state from* given files when running it twice leaves the same
files and directories as running it once. A difference in exit code or output
between the two runs is reported beside the verdict, never folded into it.

**Unreachable lines** are read statically from the control-flow graph in which
every conditional may go either way; a line no path reaches is unreachable.
This over-approximates reachability, so "unreachable" is sound and "reachable"
is not a claim.

**Drift and reconciliation.** Given desired files and actual files, the drift
is the set of desired files whose actual content differs or is missing; files
the desired set does not name are unmanaged, never drift. The reconciling
program writes each drifted file; running it removes the drift and is
idempotent (`reconcile_no_drift`, `reconcile_idempotent`).

**A pipeline** is a list of stages, each a program, run on one shared set of
files; it stops at the first stage whose exit code is not 0, and the artifact
is promoted exactly when every stage passed (`promoted_iff_all_pass`). With
rollback on, a failed pipeline restores the files it started from.

### 2.3 The three columns

Every answer is given in three columns, as the other surfaces give theirs:
column 1 the English sentences, column 2 the GLM-BAT program and the trace,
column 3 a **generated Python script** that re-derives the answer by a second,
separately written execution path (a transpilation of the program into
straight Python over a dictionary of files) and asserts it, run under
`python3 -I`. A non-halting verdict's script re-runs to step `j` and asserts
`s_i = s_j`.

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| **O1** | `RequestProject/GLM/OperationsLadder.lean` builds with no `sorry` and only the standard axioms, and proves `never_halts_of_repeat`, `never_halts_of_projected_repeat`, `andThen_assoc`, `orElse_assoc`, `reconcile_idempotent`, `reconcile_no_drift`, `reconcile_eq_self_iff`, `rollback_restores`, `layered_wf`, `promoted_iff_all_pass`, `find_find` and `sort_sort`. |
| **O2** | **The register is the note.** The 97 terms, read from the supplied file, are the register's terms tier by tier and in order; every declared composition is layered (strictly lower tier, or earlier in the same tier); every term grounds in tier 0; every tier-0 primitive is used by some term above tier 0. |
| **O3** | **The carrier.** All 97 carriers pass both round trips, and the 97 carriers are pairwise distinct. |
| **O4** | **The machine battery** (§3.1): every one of the 25 declared runs gives the declared output, files, exit code and halting verdict, or the declared refusal; **0 wrong**. |
| **O5** | **The language.** Every line of every battery program is said as one sentence and read back to the identical instruction; each of the 6 English-written programs (§3.2) reads to the declared GLM-BAT program, and runs as declared. |
| **O6** | **The questions** (§3.3): each of the 18 declared English questions is answered as declared or refused with the declared name; **0 wrong**. |
| **O7** | **Certificates.** Every answered battery run and question has a column-3 script that passes under `python3 -I`, and every one of its mutations — the claimed output, exit code, value or file altered, or a cycle's `j` moved by one — fails. |
| **O8** | **The ladder's reasoning** (§3.4): the declared relations and the cross-overs are as declared; every declared cross-over resolves to a module attribute or Lean declaration that exists. |
| **O9** | **Non-interference.** The router's reads census over the contract, engineering, cognition and Python sets is unchanged (no declared question is read by the new tools), and the 179 evaluation cases are unchanged. |

**Hypothesis H, declared with a number.** The note recommends the DevOps
ladder be "projected onto" the Geometric–Cybernetic ladder. If that projection
respects the layering, then along a composition edge `a ⊃ b` the GC tier of
`proj(a)` is at least that of `proj(b)`. **Prediction:** at least 3/4 of the
composition edges are monotone under the declared projection. H is a
measurement, not a mark; a miss is recorded as a miss and is evidence that the
two ladders order things differently.

### 3.1 The machine battery (O4)

Expected answers worked by hand. "out" is standard output, line by line;
"err" standard error; "exit" the exit code; files are given as their lines.

| run | program (lines separated by `/`) | inputs | expected |
|---|---|---|---|
| M1 | `ECHO hello` | — | out `hello`; exit 0; halts in 1 step |
| M2 | `SET NAME=world / ECHO hello %NAME%` | — | out `hello world` |
| M3 | `SET /A X=6*7 / ECHO %X%` | — | out `42`; `X` = 42 |
| M4 | `SET /A N=0 / :TOP / SET /A N=N+1 / IF %N% LSS 5 GOTO TOP / ECHO %N%` | — | out `5`; `N` = 5; halts in 13 steps |
| M5 | `TYPE data.txt / IF ERRORLEVEL 1 GOTO FAIL / ECHO found / EXIT /B 0 / :FAIL / ECHO not found / EXIT /B 2` | no files | out `not found`; err `The system cannot find the file specified.`; exit 2 |
| M6 | the program of M5 | `data.txt` = `alpha` | out `alpha`, `found`; exit 0 |
| M7 | `ECHO pear> fruit.txt / ECHO apple>> fruit.txt / ECHO fig>> fruit.txt / TYPE fruit.txt \| SORT` | — | out `apple`, `fig`, `pear`; `fruit.txt` = `pear`, `apple`, `fig` |
| M8 | `ECHO alpha> a.txt / ECHO beta>> a.txt / TYPE a.txt \| FIND "be" && ECHO yes \|\| ECHO no / TYPE a.txt \| FIND "ga" && ECHO yes \|\| ECHO no` | — | out `beta`, `yes`, `no`; exit 1 |
| M9 | `FOR %%I IN (red green blue) DO ECHO colour %%I` | — | out `colour red`, `colour green`, `colour blue` |
| M10 | `SET /A T=0 / FOR %%I IN (3 4 5) DO SET /A T=T+%%I / ECHO %T%` | — | out `12` |
| M11 | `SET /A X=5 / CALL :DOUBLE / CALL :DOUBLE / ECHO %X% / EXIT /B 0 / :DOUBLE / SET /A X=X*2 / EXIT /B 0` | — | out `20`; exit 0 |
| M12 | `CALL :CHECK / ECHO %ERRORLEVEL% / EXIT /B 0 / :CHECK / EXIT /B 3` | — | out `3`; exit 0 |
| M13 | `:LOOP / SET X=1 / GOTO LOOP` | — | never halts; certificate `(i, j) = (2, 4)` |
| M14 | `:LOOP / ECHO tick / GOTO LOOP` | — | never halts; certificate `(1, 3)` |
| M15 | `SET /A N=0 / :UP / SET /A N=N+1 / GOTO UP` | — | refused `UNDECIDED_WITHIN_BUDGET` |
| M16 | `SET /A Z=0 / SET /A Y=10/Z / ECHO done` | — | out `done`; err `Divide by zero error.`; exit 1 |
| M17 | `ECHO %USERNAME%` | — | refused `UNDEFINED_VARIABLE` |
| M18 | `ECHO %USERNAME%` | `USERNAME` = `ada` | out `ada` |
| M19 | `FORMAT C:` | — | refused `UNKNOWN_COMMAND` |
| M20 | `IF NOT EXIST out MKDIR out / ECHO ready> out/flag.txt` | — | out none; directory `out`; `out/flag.txt` = `ready`; idempotent in state: yes |
| M21 | `ECHO run>> log.txt` | — | idempotent in state: no (`log.txt` has one line after one run, two after two) |
| M22 | `MKDIR out` | — | idempotent in state: yes; the second run exits 1 with err `A subdirectory or file out already exists.` |
| M23 | `GOTO END / ECHO never / :END / ECHO done` | — | out `done`; line 2 unreachable |
| M24 | drift: desired `config.txt` = `mode=prod`; actual `config.txt` = `mode=dev`, `extra.txt` = `x` | — | drift `config.txt` only; the reconciling program is `ECHO mode=prod> config.txt`; after it no drift, and it is idempotent in state |
| M25 | pipeline: build `ECHO built> artifact.bin`; test `TYPE artifact.bin \| FIND "built"`; deploy `COPY artifact.bin prod.bin` — and the same with test `FIND "broken"`, rollback on | — | first: all three pass, promoted, `prod.bin` = `built`; second: stops at `test`, not promoted, files restored to none |

The control states of M13 are `s0` (line 1, nothing bound), `s1` (line 2),
`s2` (line 3, `X` bound), `s3` (line 2, `X` bound), `s4` (line 3, `X` bound)
`= s2`; of M14 `s1 = s3` (line 2, nothing bound), the growing output being
outside the control state. M4's 13 steps: one `SET`, the label falling
through, five `SET`/`IF` pairs, the `ECHO`.

### 3.2 Programs written in English (O5)

| | sentences | declared GLM-BAT | declared run |
|---|---|---|---|
| E1 | `compute N as 0. label TOP. add 1 to N. if %N% is less than 3, go to TOP. print "%N%".` | `SET /A N=0 / :TOP / SET /A N=N+1 / IF %N% LSS 3 GOTO TOP / ECHO %N%` | out `3` |
| E2 | `show file data.txt. if the exit code is at least 1, stop with code 2. print "ok".` | `TYPE data.txt / IF ERRORLEVEL 1 EXIT 2 / ECHO ok` | no files: exit 2 |
| E3 | `for each I in a, b, c: print "item %%I".` | `FOR %%I IN (a b c) DO ECHO item %%I` | out `item a`, `item b`, `item c` |
| E4 | `print "x", writing to file f.txt. show file f.txt, then count lines containing "x".` | `ECHO x> f.txt / TYPE f.txt \| FIND /C "x"` | out `1` |
| E5 | `make directory out, and if that succeeds, print "made".` | `MKDIR out && ECHO made` | out `made` |
| E6 | `set GREETING to "hi". print "%GREETING% there".` | `SET GREETING=hi / ECHO %GREETING% there` | out `hi there` |

### 3.3 The questions (O6)

| | program | question | declared answer |
|---|---|---|---|
| Q1 | M7 | *what does it print?* | `apple`, `fig`, `pear` |
| Q2 | M4 | *what is N at the end?* | `5` |
| Q3 | M8 | *what is the exit code?* | `1` |
| Q4 | M13 | *does it halt?* | no, never: the control state of step 2 recurs at step 4 |
| Q5 | M4 | *does it halt?* | yes, after 13 steps |
| Q6 | M15 | *does it halt?* | refused `UNDECIDED_WITHIN_BUDGET` |
| Q7 | M20 | *is it idempotent?* | yes |
| Q8 | M21 | *is it idempotent?* | no, `log.txt` differs |
| Q9 | M23 | *which lines are unreachable?* | line 2 |
| Q10 | M7 | *which files does it write?* | `fruit.txt` |
| Q11 | M7 | *what is in file fruit.txt?* | `pear`, `apple`, `fig` |
| Q12 | M5 | *what does it say?* | the seven sentences of M5, the first `show file data.txt.` |
| Q13 | M8 | *what does it use?* | the ladder terms `command`, `pipe`, `redirection`, `exit/errorlevel handling`, `stream`, `file`, `exit code` among them |
| Q14 | M17 | *what does it print?* | refused `UNDEFINED_VARIABLE` |
| Q15 | M19 | *what does it print?* | refused `UNKNOWN_COMMAND` |
| Q16 | M4 | *how many steps?* | `13` |
| Q17 | M11 | *what is X at the end?* | `20` |
| Q18 | M1 | *what is the colour of it?* | refused `UNREAD_QUESTION` |

### 3.4 The ladder's reasoning (O8)

Worked by hand from the declared compositions:

* **R1** `pipe` and `feedback loop` (the note's own question): `pipe` is a part
  of `feedback loop`, by the chain `feedback loop ⊃ pipeline ⊃ pipe`.
* **R2** `rollback` and `idempotence`: neither is part of the other; they share
  `state`; the ground overlap is computed, not declared.
* **R3** `process` is a part of every term above tier 0 except those whose
  ground omits it; the census of which terms do not ground in `process` is
  computed, not declared.
* **R4** the projections of `rollback`, `idempotence`, `drift`, `feedback
  loop` and `pipe` are `inverse`, `fixed point`, `error`, `feedback` and
  `composition`.
* **R5** the declared cross-overs — each a term of this ladder and an object
  the GLM already holds — are listed in `reasoning/ops_ladder.py` and each
  must resolve.

## 4. Controls

* **The two execution paths.** Column 3 is a transpilation into Python run in a
  fresh interpreter, written separately from the machine; agreement between
  them is the control on the machine, and the mutations are the control on
  the scripts.
* **The note itself** is the control on the register (O2): the terms are read
  from the supplied file, not from the module.
* **The router's census** is the control on non-interference (O9).
* **The multiplicity count.** Phase 124 stood at 60 statistics; this round
  adds hypothesis H, so **61**. No bit score is computed.

## 5. What this round does not do

* It adds no register to the session's default domains, so the concept index
  and every answer the evaluation pins are untouched; the operations domain is
  reached through its own tools.
* It does not claim GLM-BAT is `cmd.exe`. It is a declared fragment with
  declared departures (trailing spaces, exit codes of `SET /A`, `FOR` as one
  step).
* It does not decide halting. It certifies the two cases it can (a trace, a
  repeated control state) and refuses the rest.
* It does not make the ladder the planner's vocabulary.

## 6. Files

* `RequestProject/GLM/OperationsLadder.lean` — O1.
* `glm_universal/reasoning/ops_ladder.py` — the register (data
  committed with this document), the relation reader, the carrier and codec.
* `glm_universal/reasoning/batch_machine.py` — GLM-BAT: reader,
  machine, certificates, idempotence, drift, pipelines, unreachable lines.
* `glm_universal/reasoning/batch_speech.py` — the sentences, the
  reader of sentences, the questions, and the column-3 transpiler.
* `glm_universal/reasoning/operations.py` — the battery and the
  report; `python3 -m glm_universal.tools operations`.
* Tools `tool ladder …` and `tool machine …` on the connected path.
* Tests: `test_operations.py`.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`python3 -m glm_universal.tools ops-ladder --agreement` takes the whole
measurement in about thirty seconds. **One departure from §6:** the command
§6 names, `tools operations`, already existed (it is an earlier subcommand),
so the battery is reached as `tools ops-ladder [--fast] [--agreement]
[--json]`; nothing else about it changed.

### 7.1 The verdict

Yes, within the declared fragment. The 97 terms of the note are the register tier by tier with every composition layered and grounded; all 25 machine runs, all 18 English questions and all 6 English-written programs came out as declared with 0 wrong answers, every refusal by its declared name; all 78 battery lines were said as sentences and read back exactly; and all 41 answered runs and questions carry a column-3 Python script that passes in a fresh interpreter, while all 158 of their mutations fail. Hypothesis H held narrowly (185 of 242 composition edges monotone against 3/4), but the mean Geometric-Cybernetic tier is not monotone in the DevOps tier, so the two ladders agree on most edges and disagree on the coarse order.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| O1 | the Lean file | **met**: `RequestProject/GLM/OperationsLadder.lean` builds with no `sorry` and proves the twelve declared theorems, with `run_add`, `run_map` and `lex_rank_wf` beside them; `#print axioms` shows at most `propext`, `Classical.choice`, `Quot.sound` (`layered_wf` and `lex_rank_wf` use none) |
| O2 | the register is the note | **met**: 97 terms read from the supplied file, the same tier by tier and in order; 0 layering violations, 0 ungrounded terms, 0 idle primitives |
| O3 | the carrier | **met**: 97 of 97 round trips, 97 distinct carriers (the terms' ground sets take only 43 distinct values, so the carrier is not the ground set) |
| O4 | the machine battery | **met**: 25 of 25 as declared, 0 wrong; M15, M17 and M19 refused by their declared names |
| O5 | the language | **met**: 78 of 78 battery lines said and read back to the identical instruction; 6 of 6 English programs read to the declared GLM-BAT and ran as declared |
| O6 | the questions | **met**: 18 of 18 as declared, 0 wrong; Q6, Q14, Q15 and Q18 refused by their declared names |
| O7 | certificates | **met**: 41 of 41 column-3 scripts pass under `python3 -I`; 158 of 158 mutations fail |
| O8 | the ladder's reasoning | **met**: R1, R2, R4 and R5 as declared; 14 of 14 cross-overs resolve |
| O9 | non-interference | **met**: the toolbox reads none of the router's declared question sets (contract, engineering, cognition, Python), and all 179 evaluation cases pass with 0 confidently wrong. Two of them, `report relay` and `report anonymous`, were re-pinned: their retrieval figures count goal queries sampled from the Lean development, and `OperationsLadder.lean` took that set from 818 to 822 queries (the relay now carries 10 queries and loses 0, where it carried 8; its gate fires on 54 of 1644); their claims are unchanged and no answer moved through routing, as earlier Lean files have needed |

### 7.3 What was seen

* **The machine reasons by running and by certificate.** Asked *does it
  halt?* of M4 it answers "yes, it halts after 13 steps with exit code 0"; of
  M13, "no, it never halts: the control state before step 2 recurs before step
  4" — the repeated control state that `never_halts_of_projected_repeat`
  proves sufficient; of M15, whose counter grows without repeating a control
  state, it refuses `UNDECIDED_WITHIN_BUDGET`. The halting question is never
  decided beyond these two certificates.
* **The language is the program.** A program may be written in English
  sentences (`compute N as 0. label TOP. add 1 to N. …`); the reader turns
  them into GLM-BAT and the sayer turns GLM-BAT back into the same sentences,
  so the GLM holds the operation as something it can say, read and answer
  questions about, not as an opaque call.
* **The second interpreter.** Column 3 is a transpilation of the program into
  a standalone Python script that recomputes the claimed answer and asserts
  it. Agreement of the two interpreters is the control on the machine; the
  mutations (claim altered, cycle index moved by one) are the control on the
  scripts.
* **R2 and R3, computed.** `rollback` and `idempotence` share 5 of the 7
  primitives in the union of their grounds, both being built from `script`
  and `state`, and no term of the note is built from both. Seven terms above
  tier 0 do not ground in `process`: `variable`, `assignment`, `conditional`,
  `exit/errorlevel handling`, `config file`, `log` and `event` — the note's
  declarative and record-keeping terms.
* **Hypothesis H.** 185 of 242 edges are monotone (76.4 %, threshold 75 %):
  held, by four edges. The 57 inverted edges start in tiers 1 to 9; among them the
  note's orchestration terms project below their parts (`pipeline ⊃ workflow`,
  `rollback ⊃ state`, `telemetry ⊃ log`). The mean projected tier by DevOps
  tier is 11/5, 24/13, 23/9, 22/9, 37/8, 3, 17/5, 4, 44/9, 50/9 — rising
  overall, falling at three steps. The note's suggestion that the DevOps
  ladder "projects onto" the Geometric–Cybernetic one is right edge by edge
  and wrong as a tier-to-tier map.
* **Cross-overs.** The 14 declared cross-overs each name an object the GLM
  already held: `drift` is `reasoning/drift.py`'s exact-against-rounded drift;
  `idempotence` its fixed point; `rollback` the reversible gate's backward
  round; `feedback loop` the delta-sigma modulator; `retry` and `SLO` the
  probe budget of Phase 124 (`miss_bound`, `budget_serves_every_type`);
  `pipeline` the connected router (`route_cons_none`); `quality gate` the
  sign-off ledger; `version` the file digest and the Golay decoder;
  `on-call` the escalation ladder; `dashboard` the generated figures;
  `health check` the capability probes; `platform` the toolbox itself.

**Post hoc, not a mark.** A seeded generator (seed 20261010) wrote 300
programs from the fragment; the machine decided 299 of them (296 halted,
3 certified never to halt, 1 refused as undecided), and column 3 agreed on all
299; all 4607 of their lines were said and read back exactly. The generator
was written after the marks were taken.

### 7.4 What is left

* **The ladder in the planner and the session.** The operations domain is
  reached through `tool ladder` and `tool machine` only (§5). Giving the
  planner or the session's default domains the ladder's vocabulary changes
  answers the evaluation pins, so it is a round of its own under a
  frozen-path comparison.
* **More of the fragment.** Stream merging (`2>&1`), `SORT` options and case,
  `SETLOCAL`/`ENDLOCAL`, delayed expansion and `FOR /F` are outside GLM-BAT
  and are refused as `SYNTAX` or `UNKNOWN_COMMAND`.
* **Halting beyond the control state.** A loop whose counter grows (M15) is
  refused; a ranking-function certificate (`layered_wf`, `lex_rank_wf` are
  the Lean side of one) would let the machine say *halts* without running to
  the end. *Taken in part by Phase 126*
  ([`INERT_COUNTER_STUDY.md`](INERT_COUNTER_STUDY.md)): a counter no line
  reads except to update it is now forgotten, and M15 and Q6 are certified
  never to halt (`(2, 4)` with `N` forgotten). Re-read with that rule, this
  study's battery gives 43 of 43 column-3 scripts and 168 of 168 mutations
  rejected (the two new claims and their ten mutations), every other answer
  as recorded above. The ranking-function certificate is still open.
* **The statistics count** is now 61 (§4); no bit score was computed.
