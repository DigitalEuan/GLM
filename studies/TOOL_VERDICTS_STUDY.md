# Tool verdicts — a tool's yes/no answer in the planner, and the nearest fraction without a bound

## Tier 0 — the coarse read

**Question.** Can the stepwise planner use a tool's yes/no answer — as the answer, as the test of a conditional, and as the stopping test of a search — with every step re-checked in a fresh interpreter; can it read Phase 137's two unread phrasings by a general rule, measured on a fresh held-out set; and can the nearest-fraction tool drop its 20,000 bound by proving the classical closest-fraction theorem in Lean?

**Verdict.** Yes on all three. A tool's verdict is now a planner step; *if A, B, otherwise C* builds only the branch its test selects; *the first convergent of X whose denominator is above N* is unrolled into steps with no iteration cap, admitted because a measure proved in Lean ends it. The classical closest-fraction theorem is proved, and the tool now checks a Farey certificate for every bound instead of an exhaustive search up to 20,000. All 6 marks were met. On the fresh rewordings 12 of 16 were read and all 12 were right; 4 were not read and are left unread.

**Deciding figure.** 6 of 6 marks; 14 of 14 held-out verdict questions as expected (12 answered, 2 refused as expected); 12 of 12 chains verified in a fresh interpreter, 53 of 53 mutants caught; 12 of 16 fresh rewordings read, 12 right, 0 wrong, and Phase 137's 2 misses now right; 0 of 404 declared texts read and 0 of 30 stepwise cases moved; 100 of 100 grid cases agree with the exhaustive search and 25 of 25 bounds up to 10^60 certified.

**Recomputed by.** `glm_universal.evaluation.tool_verdicts_cases.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

The study of Phase 138. It takes the three next steps that `STATUS.md` §2.2
listed after Phase 137 (*the connected machine, the rest*):

1. let the planner use a tool's yes/no answers, not just its numbers;
2. recognise the two unread phrasings (*the second partial quotient of pi*,
   *the convergent number 4 of pi*), after a fresh held-out set;
3. prove the classical closest-fraction theorem in Lean, so that the
   20,000 bound on the nearest-fraction check can go.

The owner's standing preference, restated for this round: avoid limits where
they can be avoided, because in a deterministic system a cap decides answers
for reasons that have nothing to do with the question.

**Order of work, stated plainly.** The Lean theorem came first
(`RequestProject/GLM/NearestFraction.lean`), then the Farey certificate in the
tool. Then both held-out sets (§3) were written and committed on their own,
before any reader of this phase existed, and run once as a baseline. Then the
verdict reader, the conditional, the search and the widened value patterns
were written, and the sets were run again. The value patterns were widened
only by the rule the two Phase 137 misses call for (§1.4); the four fresh
rewordings that are still unread were **not** fitted afterwards.

## 1. What was built

### 1.1 Verdicts (`runtime/tool_values.py`)

`read_verdict(phrase)` reads a yes/no question one tool decides and returns
the tool text, a **test** and the claim in declarative form. The tests are
total over the tool's answer:

| test | meaning | example |
|---|---|---|
| `flag reachable` | the gate tool's boolean figure | *is 0xff reachable from 0x0 (by gate moves)*, *can 0x7 reach 0x3* |
| `flag-not reachable` | its negation | *is 0x3 unreachable from 0x7* |
| `flag reached` | the wiring census's boolean figure | *is the module affine_output reached by a query* |
| `equals <selector> N` | a tool value compared with a stated number | *is 355/113 the closest fraction to pi with denominator at most 1000*, *is 7 the second term of the continued fraction of pi*, *is the third term of the continued fraction of e equal to 2* |

A gate target the tool proves unreachable is a **`False` verdict carrying the
tool's proved reason** (`GLM.SubstrateCognition.gates_fix_of_control_clear`
and its neighbours), not a refusal. A tool that gives no such figure — a
malformed word, an unknown module — gives no verdict, and the step is refused
rather than read as `False`.

### 1.2 The steps (`runtime/stepwise.py`, `reasoning/stepwise_script.py`)

* **A verdict** is a `planned` step whose value is `True` or `False`; its
  column-3 record is `["verdict", tool text, test…]`, and the script re-runs
  the tool and applies the test with its own reading.
* **A conditional**, *if A, B, otherwise C*, is a new `choose` step. A is read
  as any verdict the planner already produces (a tool verdict, *is … prime*,
  *is … odd*, a comparison); a declarative condition (*113 is prime*) is asked
  as the question (*is 113 prime*). **Only the branch the test selects is
  built**: the other may name a value no tool gives (the moves to an
  unreachable word) and is never asked. The step gate and the script both
  check that the branch matches the test.
* **A search**, *the first convergent of X whose denominator is above N*, is
  unrolled: for k = 1, 2, … the denominator of convergent k (a tool value) and
  a `compare` step against N, until the test first holds; then the convergent,
  and a new `first` step that checks every earlier test failed and the last
  held. The loop is GLM-style in that every round is an ordinary checked
  step; there is **no iteration cap**. It is admitted because it has a proved
  measure (§2.3); if the expansion ends first (a fraction written as an
  expression), the tool's refusal is the answer's refusal.

### 1.3 The Farey certificate (`reasoning/rational_approx.py`, `runtime/toolbox.py`)

`best_approximation` still picks the two classical candidates (the last
convergent within N and the semiconvergent below the next) and tells them
apart by the midpoint rule. Every answer now carries a **Farey certificate**,
checked at run time for every N: the two candidates are Farey neighbours
(`b c − a d = ±1`), their denominators add up past N, and the value lies in
the closed interval between them. Those three facts are exactly the
hypotheses of `GLM.NearestFraction.farey_certificate`, so the certificate
alone proves the answer; that the candidates always pass is the classical
theorem (§2.2). The certificate is checked instead of the exhaustive search,
which is left only as the measurement's independent cross-check.

Removed: `EXHAUSTIVE_CAP = 20000` (the exhaustive check is no longer on the
answering path; `exhaustive_nearest` remains as the measurement's independent
cross-check, with no bound of its own), `MAX_DENOMINATOR = 10^12`, and an
undeclared cap of 400 certified terms in `best_approximation`. What remains is
the precision ceiling `MAX_BITS = 2^-4096`, which is not a limit on N but on
how finely an exact real is read; a value that ceiling cannot place is
refused with that reason.

### 1.4 The widened value patterns

Phase 137's two misses call for two general rules, and only those were added:

* **"partial quotient" names a continued-fraction term by itself**, so the
  expansion need not be named (`cf-quotient`, `cf-quotient-number`,
  `cf-quotient-fold`); and a term may be *in the expansion of* X as well as
  *in the continued fraction of* X;
* **a convergent may be numbered** (`convergent number 4 of pi`,
  `convergent 4 of pi`; `convergent-number`).

## 2. What is proved (`RequestProject/GLM/NearestFraction.lean`)

Builds with no `sorry`; the main theorems use only the standard axioms
(`propext`, `Classical.choice`, `Quot.sound`).

### 2.1 The certificate

* `farey_denominator` — a fraction strictly between Farey neighbours `a/b`,
  `c/d` has denominator at least `b + d`.
* `endpoint_nearest` — a point outside an interval is no nearer an inner point
  than the nearer endpoint.
* `farey_certificate` — so if x lies between Farey neighbours whose
  denominators add up past N, the nearer of the two is at least as near x as
  every fraction with denominator at most N.

### 2.2 The classical theorem

* `complete_quotient` — x = (p t + p′)/(q t + q′), with t the complete
  quotient after the first k terms, while the expansion goes on.
* `conv_denominators` — 1 ≤ q and 0 ≤ q′ ≤ q.
* `between_candidates` — x lies between the convergent and the
  semiconvergent of index j whenever j ≤ t.
* `nearest_fraction_candidates` — **the closest-fraction theorem**: with
  q_k ≤ N < q_(k+1) and j = ⌊(N − q_(k−1)) / q_k⌋, both candidates have
  denominator between 1 and N, and every fraction r/s with 1 ≤ s ≤ N is at
  least as far from x as the nearer of them. Its one hypothesis beyond the
  bounds is that the expansion has not ended by term k (an exact fraction
  takes the tool's separate exact path).

### 2.3 The search's measure

* `conv_denominators_fib` — convergent denominators grow at least like the
  Fibonacci numbers: q_n ≥ F(n + 1).
* `search_terminates` — once more than N terms follow the first, the
  denominator is above N. In practice the search ends in about log_φ N rounds
  (5 rounds for pi and N = 1000).

## 3. The held-out sets (`evaluation/tool_verdicts_cases.py`)

Both were written and committed before any reader of this phase existed.

### 3.1 Fresh rewordings (`REWORDINGS_TWO`, 16)

Expected values were computed independently of the GLM — a 200-digit
computation of pi (Machin), e (series) and the square roots (integer square
root), their continued fractions and convergents, and an exhaustive
nearest-fraction search — except the three lattice and moonshine values,
which were read off the GLM's own canonical phrasing (§6).

### 3.2 Verdict questions (`VERDICTS_HELD_OUT`, 14)

Four bare verdicts, two equality verdicts, three conditionals, three searches
and two questions that must be refused (a search on an expansion that ends; a
conditional whose taken branch names a value no tool gives).

## 4. The marks

| mark | what is measured | met when |
|---|---|---|
| T1 | the Lean file | every listed theorem present, no `sorry` |
| T2 | the verdict set through the router | 14 of 14 as expected |
| T3 | column 3 on every answered verdict chain, and its mutations | every chain verifies, every mutant is caught |
| T4 | the fresh rewordings | none wrong, and Phase 137's two misses now right |
| T5 | non-interference | no declared text reads as a verdict; no stepwise case moves with the verdicts switched off |
| T6 | the Farey certificate | agrees with the exhaustive search on Phase 137's 100-case grid; certified on 25 bounds from 20,001 to 10^60 |

T4's threshold was set after the baseline run of §5.1 and before the readers
were written; the other marks were set before any measurement.

## 5. The measurement

`python3 -m glm_universal.tools tool-verdicts`:

```
T1 Lean           RequestProject/GLM/NearestFraction.lean: missing [], sorry False
T2 verdicts       14 of 14 held-out questions as expected
T3 column 3       12 of 12 chains verified; 53 of 53 mutants caught
T4 rewordings     12 of 16 right, 12 read, 0 wrong; Phase 137 misses now right 2 of 2
T5 interference   0 of 404 declared texts read; 0 of 30 stepwise cases moved
T6 certificate    100 of 100 grid cases agree with the exhaustive search; 25 of 25 bounds up to 10^60 certified
marks met         6 of 6
```

### 5.1 Baseline and after

| set | before this round | after |
|---|---|---|
| fresh rewordings (16) | 6 right, 10 unread | 12 right, 4 unread, 0 wrong |
| verdict questions (14) | 2 as expected (the two refusals) | 14 as expected |

The four rewordings still unread: *the fraction closest to e with denominator
at most 50* (the noun after the adjective), *the kissing number of the
24-dimensional leech lattice*, *the number of norm 6 vectors in the leech
lattice* and *the minimum number of gate moves to go from 0x7 to 0x3*.
Reading them now would be fitting to the held-out set, so they wait for the
next fresh set.

### 5.2 Unchanged

The full evaluation passes 188 of 188 after re-pinning the two report cases
whose counts move with every new Lean file (`report-relay`,
`report-anonymous`: the goal-query set grew from 856 to 860; the claims are
unchanged). The Phase 137 measurement (`tools tool-values`) still meets 8 of
8; its held-out mark now reads 12 of 12, because Phase 137's two misses are
read. The Phase 136 measurement (`tools connected-two`) still meets 8 of 8.

### 5.3 What it answers

```
the first convergent of pi whose denominator is above 1000      -> 103993/33102
  (13 steps: five denominators 1, 7, 106, 113, 33102, each tested > 1000;
   the fifth test holds; convergent 5; the first step checks the run)
if 0xff is reachable from 0x0, the number of gate moves from 0x0 to 0xff, otherwise -1
                                                                 -> -1
  (the otherwise branch; the moves are never asked)
is 22/7 the best rational approximation of pi with denominator at most 100 -> False
tool best approximation pi denominator 100000000000000000000
  -> 265099323460521503743/84383735478118508040, Farey certificate
     (b c - a d = 1, denominators add up to 167925002368810502873)
```

## 6. Asking the GLM for help

At the owner's suggestion the GLM itself was asked questions during the
round, without a formal experiment. What it gave:

* **Its own map.** `tools` lists every surface and tool with its Lean file and
  study. Reading it showed which tools already return a yes/no figure (`gates`:
  `reachable`; `wiring`: `reached`), and that settled the verdict tests of
  §1.1. It also showed that the `best approximation` line still advertised the
  old check (*checked against every denominator where that is cheap*); that
  line is now corrected.
* **Answers for the answer sheet.** The canonical phrasings
  *the dimension of v2 of the moonshine module*, *the number of vectors of
  norm 6 in the leech lattice* and *the kissing number of the leech lattice*
  gave 196884, 16773120 and 196560, each with its tool and selector named;
  those three values went onto the fresh rewording sheet.
* **Its refusals as a gap list.** *is 0xff reachable from 0x0 by gate moves*,
  *is the fourth convergent of pi equal to …* and *the second partial quotient
  of pi* were refused with named reasons before the round; each refusal became
  a requirement.

It could not help with the Lean proof or the design of the step forms; those
were done by hand.

## 7. What this round does not do

* Verdicts are read from two tools with a boolean figure (`gates`, `wiring`)
  and from any tool value by equality. The ladder's relations and a law's fate
  in the law register are not yet verdicts.
* The search reads one shape (the first convergent past a denominator bound).
  A search whose measure is not proved — *the first term of the continued
  fraction of X above 100* — is not admitted, because nothing guarantees it
  ends; admitting it would need either a proof or a cap, and this round adds
  no caps.
* Conditionals do not nest a second *if* inside a branch, and *then* inside a
  conditional is read as a step separator.
* The primality step still has a ceiling of 10^12 (`runtime/stepwise.py`); it
  was not in this round's scope.

## 8. Files

* `overlay/glm_lean/RequestProject/GLM/NearestFraction.lean` — §2.
* `overlay/glm_universal/reasoning/rational_approx.py` — the certificate; the
  caps removed.
* `overlay/glm_universal/runtime/toolbox.py` — the tool's answer and its line.
* `overlay/glm_universal/runtime/tool_values.py` — verdicts; widened patterns.
* `overlay/glm_universal/runtime/stepwise.py` — the verdict, `choose` and
  search readings and steps.
* `overlay/glm_universal/reasoning/stepwise_script.py` — the `choose` and
  `first` step forms, readers, recomputation, and the column-3 script.
* `overlay/glm_universal/evaluation/tool_verdicts_cases.py` — the held-out
  sets and the marks; `tools tool-verdicts`.
* `overlay/glm_universal/tests/test_tool_verdicts.py` — 19 tests.

### 8.1 What this round leaves

* The four unread fresh rewordings (§5.1), for the next fresh held-out set.
* Verdicts from the ladder and the law register; a search over terms, once a
  measure for it is proved.
* The release sign-off, still owed since Phase 134: pytest could not be
  installed here.
