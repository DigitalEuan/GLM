# Nonlinear elimination: systems in letters that substitution cannot isolate

## Tier 0 — the coarse read

**Question.** Phase 98's solver refuses `NONLINEAR` every system in which an unknown appears in a product or in two powers, even when the system has a closed answer. Can a second layer answer those systems exactly, giving every real solution as a branch, without answering anything wrongly and without moving an earlier answer?

**Verdict.** Yes, for systems that reduce to linear and quadratic steps: the new layer answers 9 of the 10 declared systems with exactly the declared branches, refuses all 5 declared refusals by name, and moves no earlier answer. Four of the seven marks were met. The planted battery found a defect that lost solutions, which was repaired before the marks were taken; it then gave 0 wrong answers but answered only 19 of 60 systems, because most random pairs of conics leave a cubic.

**Deciding figure.** 4 of 7 marks met; 9 of 10 declared systems with exactly the declared branches; 5 of 5 refusals; 10 of 10 scripts verified and 10 of 10 mutants rejected; 24 of 26 Phase 98 questions unchanged, the other 2 being its two `NONLINEAR` refusals; planted battery 19 of 60 answered, 0 wrong.

**Recomputed by.** `glm_universal.runtime.nonlinear_report.nonlinear_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`SYMBOLIC_PARAMETERS_STUDY.md`](SYMBOLIC_PARAMETERS_STUDY.md) §6 names the
first limit of Phase 98's operation: "a system where an unknown appears in a
product or in two powers is refused `NONLINEAR`, even when it has a closed
solution. Gröbner bases or resultants would be the next step." The owner's
standing request for this push is to broaden the GLM's reasoning, so this
round took that item ahead of round 9's retrieval candidates (N5 and I3),
which stay next in [`STATUS.md`](../STATUS.md) §3.4.

The cases and the marks were committed before any code
(`glm_universal/evaluation/nonlinear_cases.py`).

## 1. The layer

**Where it sits.** `glm_universal.reasoning.symbolic_nonlinear` runs only
when Phase 98's `solve_system` refuses `NONLINEAR`. Any other answer or
refusal of the operation is untouched, and
`read_system(text, nonlinear=False)` is the operation exactly as Phase 98
shipped it.

**Its objects.** These are the same exact polynomials and rational functions
over `Fraction` as Phase 98, plus **generators**. A generator is a named
square root `sqrt(R)` of a polynomial in the parameters (or a radical of a
constant), with the single relation `sqrt(R)^2 = R`. Every value is kept with
a denominator free of generators: a denominator `d0 + d1·sqrt(R)` is
multiplied through by its conjugate. No float is used.

**Its steps,** taken one at a time in this order:

1. **Isolate** an unknown that appears in the first power with a coefficient
   free of unknowns. The coefficient may hold a generator.
2. **Solve** an equation left in one unknown. Its content is stripped (and
   recorded as a nonzero condition), the root `0` is split off, the
   squarefree part is taken, and rational roots are split off when the
   coefficients are numbers. What is left must be linear or quadratic:
   * a quadratic whose discriminant is a perfect square (found by an exact
     polynomial square root) gives two rational **branches**;
   * otherwise it gives one branch through a new generator, with the square
     factors pulled out of the radicand (`sqrt(v^2 - 2*g*h)`, not
     `sqrt(4*v^2 - 8*g*h)`);
   * a negative constant discriminant has no real root, and that factor is
     dropped;
   * anything of higher degree is refused `NONLINEAR`, and so is a quadratic
     whose coefficients already hold a generator (a nested radical).
3. **Split** on a coefficient `A` that holds other unknowns. Either `A ≠ 0`
   and the unknown is isolated, or `A = 0` and the rest of the equation
   vanishes too. Both cases are followed.
4. **Eliminate** an unknown between two equations by their **resultant**
   (Sylvester's determinant, computed by fraction-free elimination), keeping
   one of the two equations.

**The check.** Every surviving branch is substituted into **every original
equation**, its generators are reduced, and the result must vanish
identically. A branch that fails is dropped and the drop is reported; a
resultant's extraneous pairs end here. The conjugate of a verified branch
(every generator's sign flipped) is printed as a further branch. Refusals
are named: `NONLINEAR`, `NO_REAL_ROOT`, `UNDERDETERMINED`, `INCONSISTENT`,
`OVERDETERMINED`. A branch that leaves an unknown free is a family of
solutions, so the whole system is refused rather than answered in part.

**The reading.** It prints *k solutions: (1) … ; (2) …*, with the derivation
of each branch and the discards. Its column-3 script is Phase 98's
stand-alone check, one per branch, run together: every law as written must
hold at six rational points, with every generator carried formally and
reduced by its own relation, and every printed answer must equal its value.
The mutated reading doubles the first target of every branch, and its script
must fail.

## 2. The marks

| mark | declared | result |
|---|---|---|
| E1 | every declared system answered with exactly the declared branches | **not met**: 9 of 10 |
| E2 | every declared refusal by its code | met: 5 of 5 |
| E3 | every answered script verifies; every mutant rejected | met: 10 of 10, 10 of 10 |
| E4 | no Phase 98 reading moves except its two `NONLINEAR` refusals; Phase 98's refusal mark holds with the layer off | met: 24 of 26 unchanged, 2 now read, 0 otherwise; 8 of 8 |
| E5 | planted battery: 0 wrong, planted point found in at least 45 of 60 | **not met**: 0 wrong, 19 of 60 |
| E6 | with the layer off, every declared system is refused `NONLINEAR` | **not met**: 9 of 10 |
| E7 | a Lean file proves what the layer rests on, with no sorry | met |

**4 of 7 marks met.** So the answer to the question is yes for systems that reduce to linear and quadratic steps: four of the seven marks were met, and the three misses are a declaration error and a battery floor set too high (§3).

The answered systems, as the machine prints them:

* *quadratic* `x^2 + x = c`: `x = (1/2)*(sqrt(4*c + 1) - 1)` or
  `x = -(1/2)*(sqrt(4*c + 1) + 1)`.
* *product of unknowns* `x*y = 1; x + y = 3`: `(3 ± √5)/2` paired with
  `(3 ∓ √5)/2`.
* *sum and product* `x*y = p; x + y = s`: `x = (s ± sqrt(s^2 - 4*p))/2`, with
  `y` the other sign.
* *elastic collision* (momentum and kinetic energy):
  `v1 = u, v2 = 0` or `v1 = u*(m1 - m2)/(m1 + m2), v2 = 2*m1*u/(m1 + m2)`,
  derived assuming `m1 ≠ 0`, `m2 ≠ 0` and `m1 + m2 ≠ 0`.
* *projectile time* `h = v*t - g*t^2/2`: `t = (v ± sqrt(v^2 - 2*g*h))/g`.
* *rectangle* `l*w = A; 2*l + 2*w = P`: `(P ± sqrt(P^2 - 16*A))/4`.
* *hyperbola and circle* `x^2 + y^2 = 5; x*y = 2`: four integer pairs, from a
  split on `y ≠ 0` and a quartic split over the rationals.
* *parabola and circle* `x^2 + y^2 = 2; y = x^2`: `(±1, 1)`. The factor
  `x^2 + 2` has no real root, and its drop is printed.
* *two conics* `x^2 + y^2 = 13; x^2 - x*y + y^2 = 7`: no unknown can be
  isolated, so `y` is eliminated by the resultant. The back-substitution
  offers eight pairs; four fail the check (for example `(2, -3)`), and the
  four true pairs are printed.

## 3. The misses, as they are

**E1 and E6 — one declaration error.** I declared *circle and line*
(`x^2 + y^2 = r^2; y = m*x`) as a system Phase 98 refuses. It does not.
Phase 98's substitution isolates `x = y/m` and `y^2`, and answers by its own
convention with the positive root only:
`x = y/m; y = m*r*sqrt(1/(1 + m^2))`. Because the new layer runs only on a
`NONLINEAR` refusal, it never sees this system, so the reading has one
branch where two were declared. Read directly, the new layer gives both
declared branches, `x = ±r*sqrt(1 + m^2)/(1 + m^2)`, and a test holds that.
This is post hoc, not a mark. Routing a positive-root reading that drops a
branch through the new layer would change a Phase 98 answer, so it is left
for the owner (§6).

**E5 — the cubic.** Two random conics through a rational point meet in up to
four points. The resultant is then a quartic with one known rational root,
and what is left is a cubic, which usually has no rational root. Of the 60
planted systems, 37 were refused because a cubic was left and 4 because of a
nested radical; the other 19 were answered. Every answered system was
verified by its script and contains its planted point, so there are 0 wrong.
The declared floor of 45 assumed more systems would split than do. A cubic's
real roots need cube roots of complex numbers in general (the *casus
irreducibilis*), which the exact layer does not hold.

**The defect the battery found.** As first written, step 3 isolated through a
coefficient holding unknowns and only recorded it as nonzero. Two planted
systems lost their planted point that way: in one, the equation factors as
`(x - 1)(3x + 5 + 3y)`, and isolating `y` through `3x - 3` discards
`x = 1`. Both answers were verified by their scripts, so they were not
wrong in what they said, but they were incomplete. The layer printed fewer
solutions than the system has. The step now **splits** (`A ≠ 0` or
`A = 0`), the two systems have their planted point, and a test holds the
case. The defect was repaired before the marks above were taken. Before it, the battery
gave 17 of 19 answered systems with their planted point, and 2 wrong.

**A Phase 98 crash found on the way.** With the layer on, *no real root*
(`x^2 + 1 = 0`) first crashed the reading. Phase 98's substitution answers
`x^2 = -1`; the printer was handed `sqrt(-1)`, and the script generator
raised an exception instead of refusing. The operation now refuses an even
root of a negative constant `NO_REAL_ROOT`, with the layer on or off. No
Phase 98 declared case reached that path.

## 4. What is proved

`RequestProject/GLM/NonlinearElimination.lean` builds with no sorry and only
the standard axioms:

* `quadratic_branches` — over a field with `2 ≠ 0`, with `a ≠ 0` and
  `s * s = b² - 4ac`, the roots of `a x² + b x + c` are exactly
  `(-b ± s)/2a`. The layer neither loses nor adds a root of a quadratic.
* `conj`, `conj_root`, `conj_conj`, `conjugate_branch` — in
  `R[X]/(X² - D)` the map `√D ↦ -√D` is an involutive algebra map, and it
  carries a solution of any polynomial system over `R` to a solution. This is
  why a conjugate branch may be printed without being derived again.
* `resultant_eq_zero_of_common_root` — after any ring map `φ` (specialising
  the remaining letters), a common root of `f` (of positive degree) and `g`
  makes `φ (Res f g)` vanish. Elimination by resultant keeps every solution;
  only extraneous ones are added, and the check removes them.
* `elastic_collision_iff` and `sum_product_iff` — two declared systems
  solved completely: each has exactly the branches the layer prints.

## 5. What did not change

The substitution layer, its readings and its refusals are unchanged except
for its two `NONLINEAR` refusals and the crash in §3. With the layer off,
Phase 98's refusal mark holds 8 of 8. Phase 98's report and its random
linear battery read the operation with the layer off, so their figures are
the record they were. No retrieval figure, Lean-corpus figure or default
ranking moves.

## 6. Limits, and what the round leaves

* **The cubic.** Most pairs of general conics leave one (§3). Cardano's
  formula with complex cube roots, or an exact real-root isolation printed as
  a bracketed algebraic number, would be the next step.
* **Nested radicals.** A quadratic whose coefficients hold a generator is
  refused. So is a biquadratic in letters such as `u^2 + v^2 = a; u*v = b`.
* **The positive-root convention.** Phase 98 answers *circle and line* with
  one branch. Whether such readings should go through the branch layer is a
  decision for the owner, because it changes earlier answers.
* **Real-root conditions.** A radicand in letters is printed as it is.
  Whether it is non-negative is a condition on the parameters, and the layer
  does not state it.
* **Round 9 (retrieval)** in `STATUS.md` §3.4 is still next: N5 and I3.

## 7. Re-running it

From ``:

* `PYTHONPATH=. python3 -m glm_universal.tools nonlinear` runs the full
  report in about 4 s. Add `--quick` to skip the planted battery, and
  `--json` for the rows.
* `PYTHONPATH=. python3 -m unittest glm_universal.tests.test_nonlinear`
  runs the tests in about 1 s.
* `lake build RequestProject.GLM.NonlinearElimination` from the repository
  root builds the Lean file.
