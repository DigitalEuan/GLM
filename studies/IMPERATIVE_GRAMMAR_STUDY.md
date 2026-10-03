# The imperative grammar: sentences for assignment, loops, branches, functions and `match`

## Tier 0 — the coarse read

**Question.** Can the reverse grammar speak and read back programs with state — assignment, simultaneous assignment, `for` and `while` loops, branches, conditional expressions, functions with recursion and `match` — so that the Phase 64 programs with state have sentences, with their values checked by a fresh interpreter?

**Verdict.** Yes, for the declared fragment: programs with state are said and read back, their values equal CPython's, and a fresh interpreter replays every trace; one refusal of an earlier round is made more specific, so the no-regression mark is not met as declared.

**Deciding figure.** 7 of 7 Phase 64 programs with state said (0 before); 13 of 13 sentences as declared; 21 of 21 further programs equal CPython; 41 of 41 scripts verified and 41 mutants rejected; battery 1412 of 1412 programs read back, 1412 distinct sentences; 8 of 9 marks met (I7 not met).

**Recomputed by.** `glm_universal.runtime.imperative_report.imperative_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 7 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md) and
[`STATUS.md`](../STATUS.md) §3.4: *the third sort — I1 with M's strings,
tuples and ranges; then M's imperative grammar.* Phase 94 took the first half
([`THIRD_SORT_STUDY.md`](THIRD_SORT_STUDY.md)). This round takes the second.

[`REVERSE_TCT_STUDY.md`](REVERSE_TCT_STUDY.md) §8 counted the Phase 64 value
programs the reverse grammar could not speak and named 7 as *programs with
state (loops, functions, `match`, a conditional expression)*; its §9 named the
fix: *a sentence per assignment and loop (a small imperative grammar with the
same count-first discipline) would bring them in.* After Phase 94, 57 of the
83 Phase 64 value programs are said; of the 26 refused, those 7 are refused
because *a program is assignments to names, then a result*, or because the
conditional expression is not a construct of any earlier sort.

## 1. The grammar

Every construct is spelled head first with a fixed number of parts, and every
sequence of steps, parameters, arguments, names, cases or patterns states its
count before its items — the discipline that made the mask literals of
Phase 68 and the sequence literals of Phase 94 uniquely readable. Terms and
conditions are the earlier sorts' (numbers, masks, strings, tuples, ranges and
their statements), with two new terms.

| dialect | sentence |
|---|---|
| a program `S₁ … Sₖ` then the result `T` | `the program of` K `steps:` S₁`;` …`;` Sₖ`. the result is` T`.` (`step` when K is one) |
| a block of steps (a loop's, a branch's, a function's) | `do` K `steps:` S₁`;` …`;` Sₖ, or `do nothing` for no steps |
| `x = T`, `x += T` (as `x = x + T`) | `set` x `to` T |
| `a, b = T, U` (simultaneous) | `set together` K `names` a`,` b `to` T`,` U (K ≥ 2) |
| `for x in T:` | `for each` x `in` T`,` B |
| `while C:` | `while` C`,` B |
| `if C: … else: …` (`elif` as an `if` in the `else`) | `if` C`,` B `otherwise` B′ — the `otherwise` always spelled, `do nothing` when absent |
| `return T` | `return` T |
| `def f(p, q):` | `define` f `of` K `parameters` p`,` q `as` B (`of no parameters` when K is zero) |
| `match T:` with K cases | `match` T `against` K `cases:` A₁`;` …`;` Aₖ |
| a case `case P:` or `case P if C:` | `in case` P`,` B, or `in case` P `provided` C`,` B |
| patterns: a literal, `_`, a name, `P | Q`, `(P, Q)` | `the literal` L, `anything`, `the name` x, `one of` K `patterns` P`,` Q (K ≥ 2), `the sequence of` K `patterns` P`,` Q |
| `f(a, b)` | `the call of` f `on` K `arguments` a`,` b (`argument` when K is one, `on no arguments` when zero) |
| `A if C else B` | `the choice of` A `when` C`, else` B |
| a bare condition `while b:` | b `is nonzero` (a number only) |

**Names.** A variable, a parameter or a function is spelled by its name. A
name that is also a word of the grammar (`total` names the total of a
sequence) is spelled `the variable` x, and only such a name: the reader
refuses `the variable` x for any other x, so every program has one sentence.

**Sorts are decided before the program runs.** `+` and `*` are the sum and
the product of numbers, or the concatenation and repetition of sequences.
The translator decides which by a flow-insensitive pass over the program: a
name takes a sort when every assignment to it has that sort. Where an operand's
sort is not decided (a parameter, an entry of a tuple), the numeric head is
written, and a sequence reaching it at run time is refused `SORT_MISMATCH`.
A sentence never says *the sum* of two strings and means their concatenation.

**Semantics.** CPython's, for the fragment: simultaneous assignment evaluates
every right-hand side before binding any name; a loop variable keeps its last
value; a name assigned anywhere in a function is local to the whole function,
and reading it before its assignment is refused `UNBOUND`, as CPython raises
`UnboundLocalError`; a function reads the program's names at call time;
`match` tries its cases in order, a sequence pattern matches a tuple or a range
(never a string) of its length, and a guard is read after the pattern binds.

**Limits, as refusals.** Every step and every loop round counts; a program
that runs more than 100,000 steps is refused `STEP_LIMIT`, and a call nested
more than 200 deep `DEPTH_LIMIT`. A limit can only withhold an answer: an
answer given under the limits is the answer under any larger limits (proved
for the fuel semantics, §5, and measured, I9).

**Column 1 beyond the program.** After the program sentence, column 1 traces
the first 24 assignments the program makes outside any function call, each
as the statement *x equals V*, then the final value of every name of the
program, then *T equals V* for the result. The column-3 script replays the
program with an interpreter of its own and checks every one of them.

**Where it is asked.** `say:` asks the Phase 67–69 grammar first and the
third sort second; only when both refuse (`NOT_IN_FRAGMENT` or `UNREADABLE`)
is the text read with the imperative grammar. So no earlier answer can change.

**Refusals added:** `STEP_LIMIT`, `DEPTH_LIMIT`, `NO_RESULT` (a call whose
function returns nothing — CPython's `None`, which no term names), `UNBOUND`
(a name read before any assignment), `ARITY` (a call with the wrong number of
arguments). `break`, `continue`, method calls, nested functions, `global`,
star and mapping patterns, and a `return` outside a function stay
`NOT_IN_FRAGMENT`.

## 2. Declarations — written before any code of the round

The declared cases are
`overlay/glm_universal/evaluation/imperative_cases.py`, committed with this
section and before any code of the round. Every expected sentence in
`SAY_CASES` was worked by hand from §1. CPython with the dialect's prelude is
the reference for every value. The answers of the whole surface to the 83
Phase 64 value programs and 26 refusal programs, as they stood before the
round, are frozen in
`overlay/glm_universal/reasoning/_data/imperative_baseline.json`.

* **I1 — sentences.** Every `SAY_CASES` program is said word for word, and
  its value equals CPython's. **0 wrong.**
* **I2 — the Phase 64 programs with state.** All 7 of `PHASE64_STATE` are
  said, the sentence reads back to the structure read off the source, and the
  value equals CPython's.
* **I3 — further programs.** Every `PROGRAM_CASES` program is said, reads
  back, and its value equals CPython's. **0 wrong.**
* **I4 — refusals.** Every `SAY_REFUSALS` program is refused with its
  declared name; every `READ_REFUSALS` sentence `UNREADABLE`.
* **I5 — read back, and the battery.** Every sentence of I1–I3 reads back to
  its structure and is regenerated from it. Over the battery — every program
  the battery generator builds from the declared statement shapes — every
  program's sentence reads back to the program, and no two distinct programs
  share a sentence.
* **I6 — column 3.** Every answer of I1–I3 gets a generated script that
  re-reads every column-1 sentence, replays the program with its own
  interpreter, checks the trace, the final values and the result, and prints
  `VERIFIED True` in a fresh `python3 -I`; a copy with the claimed value
  mutated is rejected. 100 %.
* **I7 — no regression.** Every Phase 64 answer in the frozen baseline is
  unchanged except the 7 of I2, which move from `NOT_IN_FRAGMENT` to said;
  every earlier declared `say:` case and refusal (Phases 67, 68 and 94) gives
  its declared answer.
* **I8 — before.** The same declared material asked of the code as it stood
  at the declarations' commit is recorded (it is the frozen baseline's
  `before` table).
* **I9 — the limits withhold, never change.** Every answer of I1–I3 is
  unchanged with both limits multiplied by 10, and `r-step-limit` and
  `r-depth` are still refused.
* **L — Lean.** Count-first trees — any grammar whose every construct is a
  head with a counted list of parts — are uniquely readable; the fuel
  semantics of a while language is monotone in its fuel (so a limit only
  withholds); the Euclid loop of `while-gcd` computes the gcd; the
  accumulation of `loop-acc` telescopes to `n / (n + 1)`; the recursion of
  `def-fact` computes the factorial.

A mark that is not met is recorded as not met; nothing here is re-declared
after the measurement.

## 3. What was built

* [`reasoning/reverse_tct_imp.py`](../overlay/glm_universal/reasoning/reverse_tct_imp.py)
  — the imperative grammar: the realiser of §1 (each earlier term spelled
  through the earlier realisers, with its children realised here so that a
  nested call, choice or grammar-word name is spelled the imperative way), a
  reader that extends the third sort's reader with the new heads and refuses
  every non-canonical spelling, the translation from CPython's AST with the
  flow-insensitive sort pass, an interpreter with counted steps and bounded
  depth (CPython's scoping, simultaneous assignment and `match`), `say`
  with the trace, the final values and the result in column 1, its own
  column-3 script (an interpreter of its own over the third sort's own script
  evaluator, lifted out of that script) and its mutation, and the battery.
* [`reasoning/reverse_tct.py`](../overlay/glm_universal/reasoning/reverse_tct.py)
  — `say` asks the imperative grammar only after the third sort cannot read
  the text; [`reasoning/reverse_tct_script.py`](../overlay/glm_universal/reasoning/reverse_tct_script.py)
  dispatches a certificate of kind `say-imp` to its script.
* [`runtime/imperative_report.py`](../overlay/glm_universal/runtime/imperative_report.py)
  and `tools imperative` — the marks, and the post-hoc differential battery.
* `RequestProject/GLM/ImperativeGrammar.lean` — §5.

## 4. Results

*Recomputed by `glm_universal.runtime.imperative_report.imperative_report`
(`python3 -m glm_universal.tools imperative`).*

| mark | result | met |
|---|---|---|
| I1 sentences | 13 of 13 said word for word, values equal CPython, 0 wrong | yes |
| I2 the Phase 64 programs with state | 7 of 7 said, read back, equal CPython (`loop-acc`, `while-gcd`, `def-fact`, `def-harmonic`, `if-else`, `match-literal`, `match-guard`) | yes |
| I3 further programs | 21 of 21 said, read back, equal CPython, 0 wrong | yes |
| I4 refusals | 14 of 14 by name; 7 of 7 sentences `UNREADABLE` | yes |
| I5 read back | 41 of 41; battery 1412 of 1412 programs read back, 1412 distinct sentences | yes |
| I6 column 3 | 41 of 41 scripts `VERIFIED True`, 41 of 41 mutants rejected | yes |
| I7 no regression | 0 of 109 frozen Phase 64 answers moved but the 7 declared; 69 earlier declared `say:` cases, 1 moved (`68-refusal:unpack-self`) | **no** |
| I8 before | 0 of 55 declared programs said before the round (all `NOT_IN_FRAGMENT`) | recorded |
| I9 the limits | 0 of 41 answers changed with both limits ×10; 2 of 2 limit refusals still refused | yes |

**Why I7 is not met.** Phase 68 declared `a, b = b, 1` then `a` as a
refusal, `NOT_IN_FRAGMENT`, because a simultaneous assignment that reads its
own targets has no reading as a sequence of `let`s. The imperative grammar
reads simultaneous assignment as CPython does, runs the program and refuses
it `UNBOUND` — `b` is read before any assignment, which is CPython's
`NameError`. The refusal stands; its name is more specific. §1's claim that
*no earlier answer can change* holds for answers: an earlier refusal of
`NOT_IN_FRAGMENT` or `UNREADABLE` can become an answer or a more specific
refusal, and this is the one declared case where that happened without being
declared. The move is kept, and the mark is recorded as not met.

**What went wrong on the way, recorded.** The first measurement of I7 found
two more moves in the frozen Phase 64 refusals, both defects of the first
code, both fixed before the figures above: `float-in-loop` (`s += k / 2`)
was *answered* `3/2` where CPython gives the float `1.5` — a wrong answer in
type — because true division was read as the exact quotient; true division
and a negative literal power are now refused at translation (`Fraction(a, b)`
is the exact quotient), so the earlier refusal stands. `set-iteration` (a
loop over a `frozenset`) moved from `ORDER_UNDEFINED` to `SORT_MISMATCH`; a
loop over a mask is now refused `ORDER_UNDEFINED`, decided before the program
runs where the sort is known.

**Post hoc: a differential battery.** Written after the first measurement,
so reported beside the marks and not as one: 600 deterministic small
programs over two numbers and a string (assignments, `for` and `while`
loops, branches and conditional expressions, nested two deep). 450 are
answered by the imperative grammar and every one equals CPython; 115 are
straight-line programs the earlier grammars answer; 35 are refused. 0 wrong.
(A first version drew its programs with Python's `random` library, which the
UBP source audit forbids in the core; with an integer-only generator in its
place, the new battery found a program whose repeated squaring outgrew the
realiser and crashed `say:`. Values are now bounded: a numerator or
denominator past 4096 bits, or a string past 4096 characters, is the named
refusal `SIZE_LIMIT`. The marks I1–I9 were re-measured after the repair and
are unchanged.)

**What a sentence looks like.** `while-gcd` is said *the program of two
steps: set together two names a, b to one thousand seventy-one, four hundred
sixty-two; while b is nonzero, do one step: set together two names a, b to b,
the remainder of a and b. the result is a.*, and column 1 continues with the
trace *a equals one thousand seventy-one*, *b equals four hundred
sixty-two*, …, *b equals zero*, and the result *a equals twenty-one*.
`loop-acc`'s trace reads *the variable total equals the fraction one over
two*, *… two over three*, … *ten over eleven* — the telescoping that §5
proves, visible step by step.

**In short.** Yes, for the declared fragment: programs with state are said
and read back, their values equal CPython's, and a fresh interpreter replays
every trace; one refusal of an earlier round is made more specific, so the
no-regression mark is not met as declared.

**Which faculty moved.** Speech and verification of programs with state:
7 Phase 64 programs and 34 further declared programs that no sort could say
are now said, read back and replayed by a script a fresh interpreter checks,
with every assignment of the first 24 traced; and refusal grew five names
(`STEP_LIMIT`, `DEPTH_LIMIT`, `NO_RESULT`, `UNBOUND`, `ARITY`) where CPython
would loop, overflow its stack, return `None` or raise.

## 5. What is proved rather than measured

`RequestProject/GLM/ImperativeGrammar.lean` builds with the standard axioms
only and no `sorry` (L):

* **Count-first trees are uniquely readable.** `CTree` is a tree whose every
  node is a head with a list of parts — the shape of every construct of §1.
  For any spelling of heads and of counts with a left inverse on its own
  prefix (the third sort's `PrefixCode`), `decT_encT`: with fuel at least the
  tree's depth, the spelling *head, count, parts* followed by anything reads
  back to the tree and leaves the rest; `encT_injective`: no two trees share
  a spelling. `iterDec_encList` and `depth_lt_of_mem` are the steps.
* **A limit only withholds.** `exec` is the fuel semantics of a while
  language with the statement shapes of §1; `exec_mono`: an answer under a
  limit is the answer under every larger limit; `exec_agree`: two limits
  never give different answers — the proved counterpart of mark I9.
* **Three Phase 64 programs.** `euclidLoop_gcd`: `while b: a, b = b, a % b`
  returns `gcd a b` once its fuel exceeds `b` (`euclidLoop_1071_462`: 21);
  `sum_telescope`: `∑_{k=1}^{n} 1/(k(k+1)) = n/(n+1)` (`loop_acc_value`:
  10/11); `factFuel_eq`: the recursion of `def-fact` returns `n!` once its
  fuel exceeds `n`.

## 6. Limits, and what the round leaves

* **The trace is the first 24 assignments outside any call.** A function's
  inner assignments are replayed by the script but not traced in column 1.
* **Truth is read of numbers only.** `while b:` reads *b is nonzero*; the
  truth of a string, a tuple or a range is refused `SORT_MISMATCH`, as is
  `not` of a bare term. Booleans are still not terms.
* **Undecided sorts are refused at run time.** `+` and `*` on a parameter are
  the numeric heads; a sequence reaching them is refused, not guessed.
* **Outside the fragment:** `break`, `continue`, `pass`, method calls,
  nested functions, closures, `global`, star and mapping patterns, an `as`
  pattern, a capture inside an or-pattern, true division and negative powers
  of a possibly integer base.
* **The relay.** The planner loop of Phase 88 hands Python programs to the
  planner; handing a program with state to it as a *sentence* — so that the
  planner's answer chooses the next step of a loop — is the next piece of
  the reverse track, together with the third sort's §6.

## 7. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools imperative            # I1-I9
PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_imperative_grammar.py
python3 GLM.py -q $'say: a, b = 1071, 462\nwhile b:\n    a, b = b, a % b\na'
cd .. && lake build RequestProject.GLM.ImperativeGrammar           # L
```
