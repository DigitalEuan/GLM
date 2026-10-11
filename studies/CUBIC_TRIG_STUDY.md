# A cubic in letters with three real roots

## Tier 0 — the coarse read

**Question.** The cubic radical study left a cubic in letters with three real roots refused (`NONLINEAR`, "no real radical form"), and that refusal blocked the normal modes of three-degree-of-freedom systems. Can the branch layer answer it exactly, list every real root, and do so without moving any earlier answer?

**Verdict.** A cubic whose depressed form has `P^3/Q^2` a number is answered as a ratio of the letters times a bracketed algebraic number, and any other cubic whose discriminant is plainly negative is answered by the trigonometric form, three roots in decreasing order. The identical triple pendulum and three masses on four springs now have their three squared frequencies. A Phase 104 reading that printed Cardano's root under a condition no value of the letters satisfies is now answered by the trigonometric form. All 9 marks were met; with the switch off the layer is Phase 104's exactly, and no other reading moved.

**Deciding figure.** 9 of 9 marks met; 4 of 4 homogeneous and 3 of 3 Viète cubics with exactly the declared branches; 7 of 7 scripts verified and 7 of 7 mutants rejected; both three-degree-of-freedom systems with 3 of 3 squared frequencies; batteries 30 of 30 and 30 of 30; 303 texts read with the switch off and on, 0 moved.

**Recomputed by.** `glm_universal.runtime.cubic_trig_report.cubic_trig_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`CUBIC_RADICAL_STUDY.md`](CUBIC_RADICAL_STUDY.md) §8 named as its first
limit a cubic in letters with three real roots: no real radical form exists
(the *casus irreducibilis*), so Phase 104 refused it, and `STATUS.md` §3.4
recorded that the refusal also blocked the normal modes of
three-degree-of-freedom systems: Phase 106 found the triple pendulum's
characteristic cubic refused this way. The owner asked for another item
from `STATUS.md` while the previous round closed; this one was taken.

The cases and the marks were written before any code
(`glm_universal/evaluation/cubic_trig_cases.py`). Two edits were made to
that file before its scorer was written, and none after: the triple
pendulum case was given the outside-style text the chain-pendulum frame
reads, and the Viète battery's description was made precise (`B` an
integer times a monomial, so that minus the discriminant is plainly a sum
of even powers).

## 1. What was added

**The branch layer** (`glm_universal.reasoning.symbolic_nonlinear`, switch
`TRIG`; off, the layer is Phase 104's exactly). Where Cardano's step finds
that the square root of the discriminant `D = Q^2/4 + P^3/27` of the
depressed cubic `t^3 + P t + Q` is not real, or that `-D` is plainly
nonnegative (a sum of even powers with positive coefficients), it now
answers by one of two routes:

* **Homogeneous.** When `P^3/Q^2` is a number, `t = s τ` with `s` a ratio
  of the letters (`Q/P` with its leading coefficient divided out), and `τ`
  is a root of a cubic with rational coefficients. Each root is found by the
  numeric route Phase 104 built (rational roots, a quadratic factor, or a
  bracketed `root(f, lo, hi)`), and when the shift is a number times `s`,
  the undepressed cubic is used, so the answer reads `u = s*root(f, lo, hi)`.
  `x^3 - 3*a^2*x + a^3 = 0` reads `x = a*root(t^3 - 3*t + 1, -2, -1)` and
  the two other brackets.
* **Viète.** Otherwise the three roots are
  `t_k = 2*sqrt(-P/3)*cos(acos(K)/3 - 2*pi*k/3)`, `K = (3Q/(2P))*sqrt(-3/P)`,
  `k = 0, 1, 2` in decreasing order. Each is carried as a generator `y = M t_k`
  (`M` the least common multiple of the denominators of `P` and `Q`) whose
  relation is the cubic itself, so arithmetic on it is exact modulo the cubic.
  The answer states `4*P^3 + 27*Q^2 < 0` and prints the trigonometric form.
  The generator's name is that form, so the answer reads, for example,
  `x = 2*sqrt(1 + a^2)*cos(acos(-a*sqrt(1 + a^2)/(1 + a^2))/3 - 2*pi/3)`.

Two supporting changes: an inverse modulo a generator's relation now takes
the relation's lower powers of the generator into account (for every earlier
generator the relation holds none, and the inverse is unchanged), and the
column-3 script of a branch with a Viète root also checks, by Sturm's
theorem, that the cubic has three real roots at every sample point where its
discriminant is positive.

**The motion check** (`runtime/derivation_scripts.motion_script`). A squared
frequency that holds an algebraic number `root(f, lo, hi)` is handed to the
script under an alias, with `f` and the bracket. The script checks by Sturm's
theorem that the bracket holds one root of `f`, then computes
`det(K - w^2 M)` exactly in `Q[t]/f`. A frequency that holds a Viète root is
not listed: the modes are stated through the characteristic equation, as
before.

**The instrument** (`runtime/cubic_trig_report`, `tools cubic-trig`). It
evaluates a branch in fixed point. A Viète root is evaluated as the `k`-th
largest real root of its cubic at the point. The declared value
`shift + 2 r c_k` is computed separately: `c_k` is the root of
`4c^3 - 3c = K` found by bisection on `[1/2, 1]`, `[-1/2, 1/2]` and
`[-1, -1/2]`, the intervals the Lean ordering theorem puts the three
cosines in.

## 2. The marks

| mark | declared | result |
|---|---|---|
| T1 | every homogeneous case with exactly the declared branches | **met**: 4 of 4 (three each) |
| T2 | every Viète case with exactly the three declared branches, the condition and the form stated | **met**: 3 of 3 |
| T3 | every answered reading's script verifies; the doubled mutant is rejected | **met**: 7 of 7 and 7 of 7 |
| T4 | identical triple pendulum and three masses on four springs: the declared squared frequencies; scripts verify, mutants rejected | **met**: 3 of 3 each; both verify, both mutants rejected |
| T5 | no regression: the declared unchanged readings, the Phase 104 marks K1–K5 and K8, every Phase 106 motion case | **met**: 0 of 5 moved; K1–K5 and K8 all met; 0 of 8 motion cases moved |
| T6 | Viète battery: three branches, scripts verify, three distinct roots at a point | **met**: 30 of 30 (seed 10801) |
| T7 | homogeneous battery: three branches, scripts verify, matched to the roots | **met**: 30 of 30 (seed 10802) |
| T8 | the Lean file, no sorry | **met** |
| T9 | outside texts: only the declared ones move; evaluation cases unchanged | **met**: 303 texts, 0 moved |

The identical triple pendulum's squared frequencies are `g*λ/l` with `λ` the
three roots of `λ^3 - 9λ^2 + 18λ - 6`, about 0.415775, 2.294280 and
6.289945. The three masses on four springs give `(2 - sqrt(2))*k/m`, `2*k/m`
and `(2 + sqrt(2))*k/m`.

**T5 and T9 compare against the switch off.** The comparison is reading by
reading, each pass in a fresh interpreter, because some frames carry state
from one reading to the next. The first attempt read both passes in one
interpreter, and two rate-grid questions of Set B then differed only because
the observation stream had grown; reading each pass from nothing removed
the difference. That was a fault in the comparison, not a moved answer. The
declared outside text the round expected to move (a triple pendulum) is not
in the outside set, so nothing moved there. The triple pendulum is read from
the test text the chain-pendulum frame already answered (T4).

## 3. The vacuous answer it replaces

Phase 104 answered `x^3 - 3*(a^2 + 1)*x + 2*a*(a^2 + 1) = 0` with Cardano's
root under "real when -(1 + a^4 + 2*a^2) > 0 (then it is the only real
root)": a condition no value of `a` satisfies, with the square root of a
negative radicand printed in the answer. The discriminant was negative for
every `a`, but `_square_part` did not see `(1 + a^2)^2` in the expanded
form, so the square root was formed rather than refused. With the
plainly-negative test this cubic now reads three trigonometric roots.

## 4. Lean

`RequestProject/GLM/CubicTrig.lean`, no sorry, standard axioms only:

* `vieta_root` — with `p < 0` and `cos φ = (3q/(2p)) √(-3/p)`, every
  `2√(-p/3) cos(φ/3 - 2πk/3)` is a root of `t³ + p t + q`;
* `vieta_arg_le_one`, `vieta_arg_lt_one` — `|K| ≤ 1` when
  `4p³ + 27q² ≤ 0` (strict when strict), so `φ = arccos K` exists;
* `vieta_cos_strictly_ordered` — for `0 < φ < π` the three cosines strictly
  decrease in `k`;
* `cubic_three_roots_complete` — three distinct roots of a depressed cubic
  are all its roots;
* `vieta_roots_iff` — assembled: when `p < 0` and `4p³ + 27q² < 0` the real
  roots are exactly the three trigonometric values, strictly decreasing;
* `scaled_root`, `scaled_root_iff` — the homogeneous route loses no root and
  adds none.

## 5. Limits, and what the round leaves

* **Sign of the discriminant not decided.** When the squarefree part of `D`
  holds letters and is not plainly negative (`x^3 + p*x = q`, or a triple
  pendulum with unequal masses and lengths), the answer is still Cardano's
  root under "D > 0", as in Phase 104. The three-root regime `D < 0` is not
  given beside it. That would be a split by cases, and it would change Phase
  104's declared answers. The triple pendulum with unequal masses and
  lengths is not answered by this round: its reading did not finish within
  15 minutes when tried after the marks were scored, and its modes are
  always real and distinct, so Cardano's condition would never hold for it.
* **Plainly negative is a syntactic test.** A negative discriminant that is
  not written as a sum of even powers with positive coefficients, and has no
  square factor `_square_part` finds, is not recognised.
* **Viète roots in the motion check.** A frequency that holds a Viète root is
  not listed (the modes are stated), because the motion script carries
  algebraic numbers and one square root, not trigonometric roots.
* The cubic radical study's other §8 items stay open: numeric degree above 6,
  the quintic in letters, and Cardano's long printed form.

**Addendum (sharpening pass after Phase 108).** Three of these limits are
now taken, recorded in [`MASTER_PLAN.md`](../MASTER_PLAN.md) under
"Sharpening pass after Phase 108": a cubic in letters whose discriminant
sign is not decided is answered by cases (Cardano's root when
`4p^3 + 27q^2 > 0`, Viète's three roots when `< 0`), chosen through
`reasoning/routes.py` rather than a switch; the unequal triple pendulum is
answered in about two seconds by a stepwise route (`M` positive definite by
Sylvester's criterion, so the modes are real; the cubic's coefficients,
`P`, `Q`, `K` and the three Viète `w^2` printed in order); and the motion
script checks that cubic against its own `det(K - w^2 M)` and counts its
three roots by Sturm. This round's marks are read with the case split
disabled, so they remain statements about this round. Still open: a
negative discriminant found by factorisation rather than syntax, and
stepwise modes for four or more degrees of freedom.

**Addendum (Phase 109).** Both are now taken, recorded in
[`MASTER_PLAN.md`](../MASTER_PLAN.md) under "Phase 109". The discriminant's
sign is decided, when the surface test fails, from its square-free
factorisation (`reasoning/sign_factor.py`, Yun's algorithm): a signed
constant, odd-power factors each plainly signed, even-power factors squares
(`SignFactor.lean`). It is still a plain-sign test, now on each factor
rather than on the expanded form, so a factor of no plain sign leaves the
case split standing. The modes of four or more degrees of freedom with a
positive-definite `M` take the decision point `modes.higher`: Ferrari's
resolvent for a quartic (the resolvent cubic by Viète, the four roots as
half-sums of square roots, `QuarticResolvent.lean`) and named roots, with
their sum and product, for degree five or more. `report routes` lists every
decision point and runs one reference problem per route. This round's marks
are read with the factor decider off (`cubic.letters:factor`), so they
remain statements about this round. `tests/test_route_choices.py`.

## 6. Re-running it

From `overlay/`:

* `PYTHONPATH=. python3 -m glm_universal.tools cubic-trig` runs every mark in
  about two minutes; `--quick` skips the batteries, the Phase 104 re-read and
  the outside texts; `--json` gives the rows.
* `PYTHONPATH=. python3 -m unittest glm_universal.tests.test_cubic_trig` runs
  the tests in a few seconds.
* `lake build RequestProject.GLM.CubicTrig` from the repository root builds
  the Lean file.
