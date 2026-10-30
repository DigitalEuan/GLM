# Round 13: the stack lift, the propose-and-check loop, the vocabulary audit, and the chemistry lab

**Where the prize stands.** All three Rule 30 problems are still open. This round answers your four
questions. Each answer comes with Lean theorems (package `RequestProject/GLM/Rule30`, files
`LeftWhiteLift.lean`, `LeftWhiteCompactness.lean`, `RunBoundData.lean`, `ChemistryLab.lean`; rows
C136–C148 of `claims.csv`; the "Round 13" section of the package README) and with scripts in this
folder. Labels:

* `FORMAL`: a Lean proof for all parameters;
* `CERT`: a finite computation checked in Lean;
* `EMP`: an exact computation outside Lean;
* `OPEN`: not settled.

## 1. What the earlier rounds suggested, and what this round took from them

| Earlier round | Suggestion | Used here |
|---|---|---|
| 7 | the period-1 case of Problem 1 was proved for **every** row that is white left of a black cell, not only the seed | the **stack lift** (§4): lift Problem 1 the same way |
| 10 | the GLM induces the wheel from rows `0..4` (`rows_identify_thirty`) | the propose-and-check loop (§4), run on rows and on the column |
| 12 | the strobe lens: Problem 1 ⇔ "for every stride some phase keeps changing" | the ladder of periods `p = 1, 2, 3, …`; period 1 proved, period 2 is the next rung |
| 12 | "a refusal that names the missing statement is the most useful output" | the **vocabulary audit** (§2) |
| 12 | the formula/theorem wheel: derivable = in the span; not derivable = a vanishing functional | the **chemistry lab** (§3): a vanishing functional is a conservation law |

## 2. What does the GLM need to answer one of the three questions?

Run `python3 r13_glm_vocabulary.py` (output: `r13_glm_vocabulary_output.txt`). This extends the Round 12
theorem wheel with this round's statements (34 statements, 16 spokes). It prints the five-stage
discussion and a **vocabulary audit** for each question.

**The vocabulary is not what is missing.** The GLM can state each question completely: `P1`, `P2`
and `P3` are declared statements, and each one is a Lean definition (`Problem1`, `Problem2`,
`Problem3`). It can also state every reformulation and every sufficient hypothesis found so far.

**What it cannot do is answer.** To answer, it needs a chain of *proved* spokes from proved facts to
the target. No such chain exists, because nobody has the missing theorem. The audit says what the
missing piece is, and what kind of object it is:

| Question | Missing piece (any one would do) | Kind of object |
|---|---|---|
| P1 (periodicity) | `SeedAPBalanced`, `SeedFSTypical`, `NoResonance`, or **`LeftWhiteAperiodicAll`** (new) | the new one is an infinite family over periods `p`; `p = 1` is proved, so it needs a *uniform argument* (an induction or an invariant), not more data |
| P2 (frequency 1/2) | `SeedAPBalanced`, `SeedFSTypical`, `SqrtWobble` | each is one theorem about the seed; counting arguments of small range cannot supply it (§3) |
| P3 (cost) | nothing on the wheel is sufficient | a lower-bound technique for one explicit sequence on Turing machines; no known method proves such a bound for a sequence like this |

**Your "provisions" question.** If "provisions" means *supplying the GLM with more vocabulary*, it
helps the GLM **ask** better, narrower questions. This round's provision is the stack lift. It gives
the GLM a precise next question for P1, **"is `LeftWhiteAperiodic 2` true?"**, with certified
evidence. But a provision cannot **answer** a question: words are statements, and an answer needs a
proof. The wheel chains declared spokes; it never creates one. One more word it lacks is a
"for every p" step. The wheel can hold a family as a single statement, but proving a family needs
an induction, and an induction is a new theorem.

## 3. Chemical wheels: can treating the puzzle as a chemistry lab help?

The analogy is exact in one place. In the GLM's formula wheels (`DomainWheels.lean`), a relation is
**derivable** when its exponent vector lies in the span of the axioms. It is **not derivable** when
some linear functional vanishes on every axiom but not on the relation (`oscillatorWitness`). In
chemistry, balancing a reaction is the same linear algebra. The vanishing functional is a
**conservation law**: a count, like atoms or charge, that every reaction preserves.

So the lab question is: **is anything conserved by Rule 30?** (`ChemistryLab.lean`)

| Chemistry question | Rule 30 answer | Evidence |
|---|---|---|
| balanced reaction table? | yes: 4 of 8 neighbourhoods give black, so a fair-coin row gives fair-coin cells | FORMAL `reaction_table_balanced` |
| reversible? | no: all-black and all-white both react to all-white | FORMAL `step_not_injective` |
| equilibrium mixture? | the fair-coin mixture is invariant | FORMAL `Invariance.lean` (Round 4) |
| trivially conserved quantities? | coboundaries `g(tail w) − g(init w)` have total 0 on every finite row | FORMAL `coboundary_total_zero` |
| **non-trivial conservation law?** | **none of range ≤ 6 in the seed run** | CERT `seed_run_no_conservation_law` (rows `0..T_r`, `T_r = 1, 2, 4, 11, 26, 32`); EMP `r13_conservation.py` |

**What this means for the puzzle.** In a lab, conservation laws fix yields: the ratio of products
follows from balancing. Problem 2 asks for a yield, black : white → 1 : 1 in the centre column. The
theorem shows that no conservation law of range ≤ 6 exists that could fix it. So the stoichiometric
route is **blocked** at those ranges. That is a negative result, but a precise one. The analogy
still works as a vocabulary:

* equilibrium = the invariant fair-coin measure (proved for almost every row, Round 4);
* yield = the frequency (Problem 2);
* irreversibility = no inverse rule.

The seed is a single molecule rather than a well-mixed sample. Whether that one experiment reaches
equilibrium yield is exactly the open question.

## 4. Look at the rows, see why row 4 exists, propose it, check it, repeat

Run `python3 r13_propose_check.py` (output: `r13_propose_check_output.txt`).

**Part A: rows.** This is the loop as you describe it.

| rows seen | wheels that fit | proposals for the next row | check |
|---|---|---|---|
| 0 | 256 | 8 | — |
| 0..1 | 32 | 9 | — |
| 0..2 | 2 | 1 | row 3 confirmed |
| 0..3 | 2 (30 and 62) | 2 | **row 4 separates them: 30 is confirmed, 62 refuted** |
| 0..4 | 1 (30) | 1 | every later row is confirmed |

*Why row 4:* the neighbourhood `101` first appears in row 3. So rows 1–3 were produced without
ever using it, and wheels 30 and 62 differ only on `101` (FORMAL
`thirty_sixtyTwo_differ_only_at_101`, `rows_three_do_not_identify`, `rows_identify_thirty`). After
row 4 the loop runs through the whole stack. Every row is then *derived* rather than observed
(`next_row_determined_iff`), but the loop never learns anything new. **The questions are not about
rows; they are about the centre column in the limit.**

**Part B: the column.** The same loop on the question itself: propose "the centre column has period
`p` from time `N`", look for the refuting observation, and repeat.

* `problem1_iff_every_proposal_refuted` (FORMAL): Problem 1 says every proposal is eventually
  refuted.
* For `p = 1` the loop has a **proved horizon**: the proposal is refuted by time `4N + 6`
  (`refutation_horizon_one`).
* EMP: every proposal with `p ≤ 8` and `N ≤ 1500` is refuted within 11 steps.

**Part C: lifting the loop to the whole stack.** This is the new mathematics. Every row of the stack
is white left of a black cell (a *left-white* row), and the rule maps left-white rows to left-white
rows (`isLeftWhite_evolve`). So "propose and check at row `N`" is the same task at every row. Lift
the question accordingly:

* **`LeftWhiteAperiodic p`**: no column of *any* left-white row is eventually `p`-periodic.
  * `p = 1` is proved (`leftWhiteAperiodic_one`).
  * If it holds for every `p` (or only for the factorials), then **Problem 1 follows**
    (`problem1_of_leftWhiteAperiodic`, `problem1_of_leftWhiteAperiodic_factorial`).
* It holds for `p` **exactly when** the loop has a horizon for period `p`: a run bound `B_p(d)`
  (`leftWhiteAperiodic_iff_runBound`, by compactness). With a run bound, the proposal `(p, N)` is
  refuted by time `N + B_p(N) + 1` (`refutation_horizon_of_runBound`).
* **CERT, over every left-white row:**
  * the longest 2-periodic run at distance `d = 0..7` from the edge is exactly
    `1, 7, 6, 5, 5, 8, 9, 9`, and each value is attained (`runBound_two_upTo_seven`,
    `runBound_two_sharp`);
  * exact bounds for periods 3–6 at `d ≤ 4` (`runBound_small_periods`).
* **EMP:** exact runs for `p ≤ 6`, `d ≤ 7`; a period-2 search that dies within 38 steps for every
  `d ≤ 24` (`r13_periodic_runs.c`).

So the "repeat until discovery leads through the stack" loop is guaranteed to finish for period 1,
and the data say it finishes quickly for periods 2–6. Proving that it always finishes for period 2,
uniformly in `d`, would settle the period-2 case of Problem 1. That is the narrowest open rung.

**Caution.** The lifted statement is stronger than Problem 1, because it covers every left-white
row. If it failed for some `p`, Problem 1 could still be true. Its advantage is that it is closed
under the rule. A proof can therefore use induction along the stack, which a statement about the
single seed row cannot.

## Files

| File | What it is |
|---|---|
| `r13_glm_vocabulary.py`, `r13_glm_vocabulary_output.txt` | the extended theorem wheel's discussion and the vocabulary audit for P1, P2, P3 |
| `glm_glm_universal/reasoning/theorem_wheel_round13.py` | Round 13 statements, spokes and evidence for the theorem wheel; `vocabulary_audit` (needs the Round 12 `theorem_wheel.py`) |
| `r13_propose_check.py`, `r13_propose_check_output.txt` | the propose-and-check loop: rows, column, lifted loop |
| `r13_periodic_runs.c`, `r13_periodic_runs_output.txt` | exact longest periodic runs over all left-white rows; the period-2 search (`gcc -O2 -o r13_periodic_runs r13_periodic_runs.c`) |
| `r13_conservation.py`, `r13_conservation_output.txt` | conservation-law search in the seed run (mirrors the Lean certificate) |

All scripts run from this folder with Python 3 (standard library only) and a C compiler.
`r13_glm_vocabulary.py` expects `../rule30_round12/` next to this folder, or the Round 12 overlay
installed in the GLM repository.
