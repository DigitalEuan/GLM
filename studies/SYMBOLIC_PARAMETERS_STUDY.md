# Symbolic parameters: answers that are formulas in letters

## Tier 0 — the coarse read

**Question.** Question Set B left 13 outside questions whose answer is a closed formula in letters (class S) and one transcendental equation (class T). Can the machine answer them with a verified reading, by writing the governing laws as equations in letters and eliminating the unknowns exactly, without answering anything wrongly and without moving an earlier answer?

**Verdict.** Yes: the machine now solves systems of equations in letters exactly, refuses by name the systems it cannot solve, and answers all 13 class-S questions and the class-T question with gate-verified readings and 0 wrong. All eight declared marks were met, one of them only after a control was repaired. A post-hoc battery then found a printer fault that the marks had missed, and a speed limit at four unknowns; both were repaired.

**Deciding figure.** 8 of 8 marks met; 13 of 13 class-S questions answered and verified, 0 wrong; 13 of 13 variants; 18 of 18 declared systems; 8 of 8 refusals; 44 of 44 mutants rejected (43 of 44 as first measured); 27 of 27 framed outside answers and 14 of 14 Set B verdicts unchanged; 87 of 87 answered random systems verified after the printer repair (53 of 87 before).

**Recomputed by.** `glm_universal.runtime.symbolic_report.symbolic_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`QUESTION_SET_B_STUDY.md`](QUESTION_SET_B_STUDY.md) §8 lists the boundaries
of the outside question set as the next tracks. The first is **S, symbolic
parameters (13)**: every one of those questions is a closed formula in
letters, such as `a = (2/3) g sin θ` or `M = m₀ √(2(1 + γ))`. The exact layer
computed only with numbers. Item 5 adds **T (1)**, a crossover frequency that
solves `0.5ω + arctan ω = π`.

[`STATUS.md`](../STATUS.md) §3.4 put round 9 (retrieval) next. The owner asked
for more reasoning ability, so this phase took tracks S and T instead.
Retrieval is unchanged and is still the next round.

## 1. The objects

**Rational functions in letters** (`glm_universal.reasoning.symbolic`). A
`Poly` is a dictionary from monomials to exact `Fraction` coefficients. An
`RF` is a quotient of two polynomials kept in lowest terms by a multivariate
gcd. Square roots and other radicals of known quantities are named atoms. So
are `sin`, `cos`, `tan`, `exp` and `ln` of an expression, with
`sin² + cos² = 1` as a declared relation. `pi` is always a constant. No float
is used at any point.

**The operation** `solve symbolically for T[, ..] [in terms of P..]: EQ; EQ;
..` (`glm_universal.runtime.symbolic_frames`). Unknowns are eliminated by
declared substitution. Each step isolates one unknown that appears in exactly
one power with a coefficient free of other unknowns, and records that
coefficient as a nonzero condition. A target known only through its square is
returned as the positive root. Every answer is printed as the formula, the
conditions it was derived under, and the substitution steps. The refusals are
named: `UNDERDETERMINED`, `INCONSISTENT`, `OVERDETERMINED`, `NONLINEAR`,
`NOT_IN_SYSTEM` and `UNREADABLE`.

**The column-3 check.** The script transliterates the system and the claimed
answer into Python over `Fraction`. It evaluates them at six deterministic
rational points that avoid the conditions, and asserts that every law holds
there. Points are not a proof. `poly_eq_of_agree` (§5) is the reason they
count as evidence, and the Lean file proves the identities the outside frames
rest on.

**The outside frames** (`glm_universal.runtime.symbolic_outside`). There are
14 frames: 13 for class S and `crossover_frequency` for class T. Each reads
its givens from the question text, sets up the laws in letters, solves them
with the operation, and prints the formula.

## 2. Declarations — written before any code of the round

`glm_universal.evaluation.symbolic_cases` was committed first, before any
code:

* 15 `SYSTEMS` and 3 `SYSTEMS_SQUARED`, each answer derived by hand;
* 8 `REFUSALS`, each with its code;
* the 13 `OUTSIDE_S` fragments and `OUTSIDE_T = {35}`;
* 13 `VARIANTS`, each a re-worded question with one given changed;
* the marks.

One fragment was edited before that commit: the CFSE variant fragment became
"octahedral: CFSE = 0".

| Mark | Declared |
|---|---|
| S1 | at least 10 of the 13 class-S outside questions answered through the router with a gate-verified reading containing the declared fragment; 0 answered without it (0 confidently wrong) |
| S2 | every declared variant answered with its own fragment, gate verified (the answer moves with the given) |
| S3 | every system of SYSTEMS answered, each target equal to the declared expression as a rational-function identity; every system of SYSTEMS_SQUARED answered with the declared square |
| S4 | every system of REFUSALS refused with the declared code |
| S5 | every answered reading's column-3 script verifies, and rejects the same script with the answer altered (S1, S2, S3) |
| S6 | no regression: the 27 framed outside answers and the 14 Set B verdicts of Phase 89 unchanged; no earlier declared question is read by the new operation |
| S7 | the class-T question (index 35) answered with the root bracketed to 1/10000 by exact bounds, gate verified |
| S8 | a Lean file proves the identities the frames rest on, with no sorry |

## 3. What was built

* `glm_universal/reasoning/symbolic.py` contains:
  * the polynomial and rational-function algebra, with the gcd and radicals;
  * the parser and the printer;
  * `solve_system`, `diff` and `entails`;
  * the column-3 script writer.
* `glm_universal/runtime/symbolic_frames.py` holds the operation. It is
  routed in `question_frames.frame_of` before the typed frame.
* `glm_universal/runtime/symbolic_outside.py` holds the 14 outside frames and
  their mutants.
* `glm_universal/runtime/symbolic_report.py` holds marks S1–S8 and the
  post-hoc `random_battery`.
* `python3 -m glm_universal.tools symbolic [--json] [--quick] [--no-scripts]
  [--battery]` runs the report.
* `glm_lean/RequestProject/GLM/SymbolicParameters.lean` holds the proofs.
* `glm_universal/tests/test_symbolic.py` holds the tests.

## 4. Results

| Mark | Measured | Met |
|---|---|---|
| S1 | 13 of 13 answered and verified, 0 wrong | yes |
| S2 | 13 of 13 | yes |
| S3 | 18 of 18 | yes |
| S4 | 8 of 8 | yes |
| S5 | 43 of 44 as first measured; 44 of 44 after the control was repaired | not met as declared, met after repair |
| S6 | framed outside 27 of 27, Set B 14 of 14, the new frames read 0 of 494 earlier texts | yes |
| S7 | ω_co in [3.6731, 3.6732], amplitude ratio 0.2626, gain margin 3.8067 | yes |
| S8 | the file exists, every named theorem is present, no sorry | yes |

**S5, honestly.** At the first run one mutant was not rejected: the
crystal-field variant. Its answer is `CFSE = 0`, and the mutant multiplied the
claimed value by 2, and twice zero is zero. The control did not alter
anything, which is a fault in the control, not in the reading. The CFSE
mutation was made additive (`+ Δ/5`), and the measurement then gave 44 of 44.
The mark is recorded as not met as declared and met after repair.

**Outside classes.** After this phase the outside set reads F27, S13, T1,
D3, E32, M18 and P18. `run_outside` still groups the S questions under their
boundary class rather than under F. The figure above counts them by the new
frames.

### 4.1 The post-hoc battery (evidence, not a mark)

`random_battery` generates 90 linear systems in 2–4 unknowns with a fixed
integer generator. Their coefficients are small integers times letters. A
system counts as singular when its coefficient determinant vanishes at three
rational points.

* **First run: it did not finish.** It hung for more than 20 minutes.
  Elimination by substitution built rational functions whose multivariate
  gcds blew up in the pseudo-remainder sequence. A 3×3 system took seconds
  and a 4×4 system more than five minutes. Three repairs, all sound:
  * a trivial-gcd certificate. If, for every variable, specialising the
    others at a point where neither leading coefficient vanishes leaves
    coprime univariate polynomials, the gcd is constant. This brought the
    3×3 case down to about 0.1 s;
  * dividing each substituted equation exactly by the earlier pivots, which
    are already declared nonzero (the Bareiss step);
  * for square linear systems of four or more unknowns, Cramer's rule with
    fraction-free Bareiss determinants. A zero determinant falls back to
    substitution, which then refuses by name. `cramer_solves` proves this
    path loses and invents no solution. The 4×4 case went from more than
    five minutes to about 0.02 s.

  The declared readings were unchanged by all three: the output of every
  declared system and refusal is byte-identical before and after.
* **Second run: 53 of 87 answered systems verified.** The 34 failures were
  real wrong answers. Example: `x2 = (2*r^2 - q)/(2*r^2 - p)` where the right
  answer is `(2r² − q)/(2(r² − p))`. The computed function was right; the
  **printer** was wrong. When the denominator had a numeric factor and was a
  sum, the factor was written without brackets around the sum. None of the
  declared cases had that shape, so no mark could see it. The gate did see
  it: the printed answer is what the script checks.
* **After the printer repair:** 90 systems, 87 nonsingular, 87 answered,
  87 verified, 0 singular answered, 0 nonsingular refused. The three
  refusals were one `NOT_IN_SYSTEM` (an unknown with an all-zero column) and
  two `OVERDETERMINED`. The whole battery takes about 6 s. A test now checks
  that the printed formula reads back to itself over 60 generated rational
  functions.

**Summary of §4.** Yes: the machine now solves systems of equations in letters exactly, refuses by name the systems it cannot solve, and answers all 13 class-S questions and the class-T question with gate-verified readings and 0 wrong. All eight declared marks were met, one of them only after a control was repaired. A post-hoc battery then found a printer fault that the marks had missed, and a speed limit at four unknowns; both were repaired.

## 5. What is proved rather than measured

`SymbolicParameters.lean` builds with no sorry. Its theorems use only the
standard axioms (`propext`, `Classical.choice`, `Quot.sound`):

* `rolling_acceleration` and `rolling_friction_ratio`: `a = g sin θ / (1 + k)`
  and `μ = (k/(1 + k)) tan θ` for every moment-of-inertia factor `k`.
* `invariant_mass_sq` (`M² = m₀²(1 + k² + 2kγ)`) and
  `invariant_mass_sq_identical` (`M² = 2m₀²(1 + γ)`).
* `disturbance_transfer`: `Y = Gd Gp D / (1 + Gc Gv Gp Gm)`.
* `interface_tangent_ratio`: `tan θ₁ / tan θ₂ = ε₁ / ε₂`.
* `ar1_autocorrelation`: `Σ aⁿ aⁿ⁺ᵐ = aᵐ / (1 − a²)` for `|a| < 1`, as a
  `HasSum`.
* `poly_eq_of_agree`: two polynomials of degree below `d` that agree at `d`
  points are equal. This is why the point check is evidence at all.
* `cramer_solves`, added after the battery: with `det A ≠ 0`, `A x = b` holds
  exactly for `x = cramer A b / det A`.

## 6. Limits, and what the round leaves

* **Linear in the unknowns, or isolable in one power.** A system where an
  unknown appears in a product or in two powers is refused `NONLINEAR`, even
  when it has a closed solution. Gröbner bases or resultants would be the
  next step.
* **Size.** Substitution handles up to three unknowns comfortably, and
  Cramer handles square linear systems of four or more. A large non-square
  or nonlinear system can still be slow, because the gcd is a primitive
  pseudo-remainder sequence. No time limit is enforced inside the operation.
* **The other tracks of Question Set B §8 are untouched.** These are P
  (derivations, 18), M (meta, 18) and E (explanations, 32). Item 6 also
  remains: the planner's denotation frame should refuse a text that is a
  question rather than a term.
* **Round 9 (retrieval)** in `STATUS.md` §3.4 is still next.

## 7. Re-running it

From `overlay/`:

* `PYTHONPATH=. python3 -m glm_universal.tools symbolic` runs the full
  report in about 80 s. Add `--quick` to skip S6, `--battery` for §4.1, and
  `--json` for the rows.
* `PYTHONPATH=. python3 -m unittest glm_universal.tests.test_symbolic` runs
  the tests in about 1 s.
* `lake build RequestProject.GLM.SymbolicParameters` from the repository root
  builds the Lean file.
