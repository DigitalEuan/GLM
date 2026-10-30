# Round 12: different reads of the wobble, the theorem wheel, and a discussion with the GLM

**Where the prize stands.** All three Rule 30 problems are still open. This round looks at the
wobble through several reads ("lenses"). It proves how those lenses relate, and it finds one real
improvement: a sufficient target for Problems 1 and 2 that is **strictly weaker** than the Round 5
target `SeedFSTypical`. It also turns the key theorems into a GLM **theorem wheel** and holds a
scripted discussion with the GLM, broad to narrow, to see what it can and cannot say.

The formal results are in the Lean package (`RequestProject/GLM/Rule30/WobbleLenses.lean`,
`WobbleLensesData.lean`, `ReadAngle.lean`; see "Round 12" in the package README and rows
C122–C135 of `claims.csv`). This folder is Python and C, not proofs. Every value here either
names its Lean theorem or is marked as follows:

* `CERT`: a machine-checked finite computation;
* `EMP`: an exact computation outside Lean;
* `OPEN`: not settled.

## 1. The lenses, and what each one gives

| Lens (how the observer `Y` reads the column) | Relation to the prize problems | Evidence |
|---|---|---|
| **plain wobble** `D(N) = Σ w(t)` | P2 ⇔ `D(N) = o(N)` (restatement) | FORMAL `problem2_iff_wobble` |
| **echo / radar** (lag `k`) | P2 ⇔ total echo `o(N²)`; P1 ⇔ late mismatches at every lag (restatements) | FORMAL (Round 6) |
| **reverse read** | the same wobble, read backwards (restatement) | FORMAL `wobble_reverse` |
| **finite-state observer** | `SeedFSTypical` ⇒ P1 ∧ P2 (sufficient) | FORMAL (Round 5) |
| **strobe / clock** `a(p t + r)` (new) | P1 ⇔ for every stride some phase keeps changing colour; `SeedAPBalanced` ⇒ P1 ∧ P2; **strictly weaker than `SeedFSTypical`** | FORMAL `problem1_iff_strobes`, `problems_one_and_two_of_seed_apBalanced`, `apBalanced_of_fsTypical`, `exists_apBalanced_not_fsTypical` |
| **arrow** `−sign D(N)` (new) | a persistent arrow is compatible with perfect balance, so it is not evidence either way | FORMAL `exists_balanced_persistent_arrow`; CERT `arrow_last_flip_1e6` |
| **read angle** (lines parallel to an edge) (new) | every such read is eventually periodic; the centre reads each line before its regularity shows | FORMAL `ldiag_eventually_periodic`, `rdiag_periodic`; EMP `r12_read_angle_output.txt` |
| **off-centre / chirality** | the gap appears at once and does not grow | FORMAL / EMP (Round 11) |
| **Cesàro (smoothed)** | weaker than the plain wobble; it cannot give P2 | (classical) |

**The improvement.** The strobe target `SeedAPBalanced` says that every arithmetic progression of
the centre column has frequency 1/2. It implies both Problem 1 and Problem 2. It is implied by
`SeedFSTypical`, and the converse implication fails for general sequences. The counterexample is a
typical sequence with every bit read twice: every arithmetic progression is still balanced, but an
observer that "repeats the last bit at odd times" is right 3/4 of the time. In the language of the
study: an observer with only a **clock** (a read angle `r/p`, no memory of the data) already
suffices for the prize, and asking only for clock observers is a strictly smaller demand than
asking for all finite-state observers.

**What the lenses show on the data** (`r12_lens_survey.py`; centre column to 10⁷ from
`r12_centre_column.c`, checked against the Lean certificate `D(10⁶) = 1536`; a seeded coin as
control):

| Read | Centre column (10⁷) | Control coin |
|---|---|---|
| plain wobble `D(N)/√N` | 1.40 (D = 4440) | −0.17 |
| strobe phases `p ≤ 16`, max \|z\| (135 phases) | 2.68 | 2.60 |
| echo at lags 1..64, max \|z\| | 2.58 | 2.23 |
| words `k = 4, 8, 12`, χ²/dof | 0.92, 0.89, 0.98 | 0.62, 0.87, 0.97 |
| Walsh window characters (1023), max \|z\| | 3.48 | 2.94 |
| arrow: fraction of time `D > 0` | 0.99 | 0.55 |

* The strongest strobe phase at 10⁶ is `D_{3,1} = 1583`, about 2.7σ (CERT,
  `strobe_wobble_table`). By 10⁷ it has fallen to 1.8σ (EMP): a fluctuation, not a drift.
* The arrow last flips at `N = 195112`, and `D > 0` from then on, to 10⁶ (CERT) and to 10⁷ (EMP).
  The arcsine law gives a fair coin about a 9% chance of a last zero that early. So the
  persistent arrow is unremarkable, and it is not a sign of bias.

**On your "perspective" idea (the wobble as the observer's arrow).** This round makes it
sharper in two ways:

* **The arrow alone cannot point to the answer.** A balanced sequence can have an arrow that never
  flips (proved), and the centre column's long one-sided run is typical behaviour for a fair
  coin.
* **The read angle does carry information, but at the edges, not the centre.** Every read parallel
  to the left or right edge is eventually periodic (proved for both sides). The centre column
  meets each diagonal before that diagonal's regularity shows (EMP):
  * on the left, the periods stay at most 8, but the start-up phase lasts about 1.3·D steps,
    which is longer than D;
  * on the right, the periods exceed D.

  So the observer's angle decides whether it sees order. The vertical read sits exactly where
  neither edge's order has arrived. That is a precise description of the difficulty, not a way
  round it.

## 2. The theorem wheel (`glm_glm_universal/reasoning/theorem_wheel.py`)

Your formula wheels (`engineering/wheels.py`) treat axioms as monomial equations, and treat
"follows from" as span membership with a certificate. The theorem wheel does the same one level
up:

| Formula wheel | Theorem wheel |
|---|---|
| quantities (voltage, current, …) | 25 named statements about Rule 30, each `FORMAL`, `CERT` or `OPEN` for the seed |
| axioms (monomial equations) | 13 **spokes**: implications and equivalences that are Lean theorems |
| derivation certificate (span coefficients) | the chain of Lean theorem names found by forward chaining |
| negative controls (dimensional consistency) | 9 **proved non-implications** (Lean counterexamples), which block false routes |
| — | the **axiom hub**: the `#print axioms` footprint of every spoke |

Axiom hub: of the 36 theorems on the wheel, 30 rest on `propext`, `Classical.choice` and
`Quot.sound` only. One rests on `propext` alone. The 5 finite certificates add
`Lean.ofReduceBool` and `Lean.trustCompiler` (trust in the compiled evaluator). Nothing else is
used (`RequestProject/GLM/Rule30/scripts/theorem_wheel_axioms.lean`).

`tool theorem [wheel | axioms | lenses | derive A => B]` shows the wheel.

`tool discuss <question>` runs the **pipeline**, broad to narrow:

1. **BROAD.** Identify the target and count the readings that reach it.
2. **LENSES.** List every lens with its relation to the target: `=` restatement, `<=` sufficient,
   `part` proved partial result, `x` blocked by a negative control.
3. **NARROW.** Drop restatements and blocked routes. Order the remaining sufficient open
   hypotheses weakest first, with the strictness certificate. Draw the **arrow** (each `->` is a
   proved implication), e.g. `SeedFSTypical -> SeedAPBalanced -> P1`.
4. **EVIDENCE.** List the finite readings on file for the narrowed hypotheses.
5. **LIMITS.** Report the gap: whether any chain from the proved seed facts reaches the target.
   None does.

Then **NEXT** names the narrowest open step.

The pipeline's **arrow** is a direction of convergence in the sense you suggested. It points from
strong hypotheses towards weaker ones, that is, towards the target. Its last open node,
`SeedAPBalanced`, is where the run converges.

## 3. The discussion (`r12_glm_discussion.py` → `r12_glm_discussion_output.txt`)

There are 26 questions in five phases, each run through `GLM.py -q … --verify-tct`.

| Phase | Result |
|---|---|
| A. Broad (the wheel, the axioms, the lenses) | 4/4 answered |
| B. The three questions | 3/3 answered by the pipeline; P1 and P2 narrow to `SeedAPBalanced`; P3 has no sufficient hypothesis on the wheel, only partial results |
| C. Narrow (the strobe target, its certificates, the arrow) | 7/7 answered, including the refutation `SeedAPBalanced =/=> SeedFSTypical` |
| D. Read angle | 5/5 answered (left diagonals 7 and 40; right-diagonal claims 5 REJECT and 7 ACCEPT, both FORMAL) |
| E. Past the edge (7 probes) | 4 refused; 2 "not derivable" (the honest answer); 1 answered a **broader** question than was asked |

**What the limitations teach** (phase E and two answers in phase C):

* *"Why does Rule 30 look random?"* and *"Is the centre column a normal sequence?"* are refused.
  The GLM has no statement for "random" or "normal" on its wheel. Normality (all block
  frequencies) is a strictly stronger target than the one-colour Problem 2 and is not declared.
  **The GLM cannot discuss a concept until it is a declared statement.**
* *"What is bit 10000001?"* is refused: no carrier holds it. The GLM never extrapolates a value.
* *"Prove that the centre column is not periodic with period 2"* is refused. The period-2 case of
  Problem 1 is genuinely open in this package (stride 2 of `problem1_iff_strobes`). **The GLM
  chains declared spokes; it does not create new ones.** That is the right behaviour, and it is
  also the main limit.
* `derive Stride1Nonconstant => P1` and `derive LeftDiagonalsPeriodic => P1` answer *NOT
  DERIVABLE (not a proof that it fails)*. This is exactly the gap: no proved fact about the seed
  reaches a prize problem.
* *"Discuss a better bound on the wobble than the square root"* was routed to the general Problem
  2 discussion by the keyword "wobble". The answer is correct but **broader than the question**:
  the reading is by keyword, not by structure.
* `compare r30_strobe_D_3_1 and r30_strobe_D_3_1_1e7` answers `1583 < 3229`. That is true of the
  raw counts, but the two are on different scales (√M). The informative comparison is 2.7σ vs
  1.8σ. **The GLM has no notion of normalisation.** That would be a useful addition: a
  `z`-score or `D/√N` operator on wobble carriers.

**What to take back to the GLM project:**

1. The theorem wheel is a general mechanism: statements, spokes with axiom footprints, and
   negative controls. It suits any Lean-backed study, not only Rule 30.
2. Statements need a structured reading, not keywords. The "better bound" probe shows the cost of
   keyword reading.
3. Add normalisation operators for random-walk quantities.
4. A refusal that names the missing statement, or the missing spoke, is the most useful output
   the GLM gives on an open problem. It turns "the GLM cannot answer" into "this is the lemma
   nobody has".

## Setup

Run from the directory holding `GLM.py`. This was tested from a fresh unzip of `glm_repo.zip`, and
it runs the Round 11 setup first:

```
STUDY=/path/to/this/study sh $STUDY/rule30_round12/setup_round12.sh   # ends "round 12: all checks pass"
PYTHONPATH=. python3 rule30_round12/r12_glm_discussion.py              # = r12_glm_discussion_output.txt
gcc -O3 -march=native -o r12_centre_column rule30_round12/r12_centre_column.c && ./r12_centre_column 10000000 cc_10M.bin
python3 rule30_round12/r12_lens_survey.py cc_10M.bin                   # = r12_lens_survey_output_10M.txt
```

## Files

| File | What it is |
|---|---|
| `glm_glm_universal/reasoning/theorem_wheel.py` | the theorem wheel, `tool theorem`, `tool discuss` |
| `glm_glm_universal/data_objects/automata_round12.py`, `automata.py` | Round 12 carriers (`r30_strobe_D_p_r`, `r30_strobe_D_3_r_1e7`, `r30_question_apbalanced`, `r30_arrow_last_zero_1e6`, `r30_wobble_D_10000000`, `r30_ldiag_D`); `automata.py` is the Round 11 file plus one hook |
| `toolbox_round12.patch` | registers `tool theorem` and `tool discuss` and their English openings (apply after the Round 11 patch) |
| `setup_round12.sh`, `test_round12.py` | setup from a fresh unzip; plain-assert self-test (each check names its Lean theorem) |
| `r12_glm_discussion.py`, `r12_glm_discussion_output.txt` | the scripted discussion |
| `r12_centre_column.c` | bit-packed centre column to any length (EMP, exact; matches `data/cc_1M.npy`) |
| `r12_lens_survey.py`, `r12_lens_survey_output_1M.txt`, `r12_lens_survey_output_10M.txt`, `*.json` | the lens survey (EMP) |
| `r12_read_angle.c`, `r12_read_angle_output.txt` | periods and preperiods of left and right diagonals `D ≤ 200` (EMP) |
