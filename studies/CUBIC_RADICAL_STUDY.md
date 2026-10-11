# Cubics, nested square roots and the positive-root dual track

## Tier 0 — the coarse read

**Question.** The nonlinear elimination study left three follow-ups: the cubic that most pairs of conics leave, quadratics whose coefficients hold a square root (nested radicals), and Phase 98's positive-root answers such as circle and line. Can the branch layer answer the first two exactly and without a wrong answer, and does keeping both tracks for the third, with the branch set as the default, give a stronger answer without losing the substitution reading?

**Verdict.** Yes on all three: cubics and higher-degree numeric polynomials are answered as exact bracketed algebraic numbers (and Cardano's root in letters when the cubic has one real root), nested square roots are answered as towers, and positive-root readings now give every real solution with the substitution reading kept beside it. Eight of the nine marks were met. The miss is the no-regression mark: one Phase 98 reading gained a stated real condition, with its branches unchanged.

**Deciding figure.** 8 of 9 marks met; 6 of 6 algebraic and 4 of 4 radical systems with exactly the declared branches; 4 of 4 refusals; 16 of 16 scripts verified and 16 of 16 mutants rejected; 6 of 6 dual-track questions; both planted batteries 60 of 60 answered with the planted point and 0 wrong (Phase 103: 19 of 60); 40 of 40 cubics.

**Recomputed by.** `glm_universal.runtime.cubic_radical_report.cubic_radical_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`NONLINEAR_ELIMINATION_STUDY.md`](NONLINEAR_ELIMINATION_STUDY.md) §6 left
three items: the cubic (37 of its 60 planted systems were refused because a
cubic was left), nested radicals (a quadratic whose coefficients hold a
generator was refused, and so was `u^2 + v^2 = a; u*v = b`), and the
positive-root convention (Phase 98 answers *circle and line* with one branch,
and gives `x` in terms of `y`). The owner asked for all three, with a rule for
the third: keep both tracks active, and default to the stronger answer.

The cases and the marks were committed before any code
(`glm_universal/evaluation/cubic_radical_cases.py`).

## 1. What was added

**Exact real algebra** (`glm_universal.reasoning.symbolic_algebraic`, new):
Sturm chains and real-root isolation with rational brackets, factoring over
the rationals up to degree 6 (distinct-degree factoring modulo small primes
to bound the factor degrees, then Kronecker's search), and the sign of a
polynomial in an algebraic number by interval refinement. No float.

**The branch layer, extended** (`glm_universal.reasoning.symbolic_nonlinear`,
with `extended=True` from Phase 104; `extended=False` reproduces Phase 103
exactly):

* **Algebraic numbers.** A numeric polynomial of degree 3 or more that is left
  after rational roots and rational factors are split off is answered root by
  root as `root(f, lo, hi)`: the one root of `f` in the bracket `[lo, hi]`,
  with a decimal beside it. Arithmetic on such a value is exact, modulo `f`;
  an inverse is taken by Euclid's algorithm modulo `f`.
* **Towers.** A quadratic whose coefficients hold a square root now gets its
  own square root on top, so `x^4 - 2*p*x^2 + q = 0` reads
  `x = ±sqrt(p ± sqrt(p^2 - q))`. Denominators are rationalised from the top
  of the tower down. An even quartic whose constant term is a square is
  factored into two quadratics first.
* **Cardano.** A cubic in letters is answered by Cardano's root in Vieta form,
  `t = A - P/(3A)` with `A` the real cube root of `-Q/2 + sqrt(Q^2/4 + P^3/27)`,
  assuming `P ≠ 0`, and with the stated inequality "D > 0 (then it is the only
  real root)". When that inequality fails the cubic has three real roots and
  the printed root is not real; the layer states this rather than hiding it.
* **Real conditions.** A radicand in letters now carries a stated condition
  ("real when 4*c + 1 >= 0"). The sign of a radicand free of letters is
  decided exactly, so a non-real conjugate is dropped instead of printed.
* **A gcd step.** When coefficients hold generators, an equation is first
  reduced by its gcd with the other equations, which removes branches that
  belong to a conjugate.

**The two tracks** (`glm_universal.runtime.symbolic_frames`, `PHASE = 104`):
when the substitution layer answers by a convention — a target given as a
positive root, or a target whose value holds an unknown it does not print —
the branch layer is consulted too. When the branch layer answers, its full
set of branches is the default answer, and the substitution reading is kept
beside it in square brackets, but only if its own column-3 script passes.
When the branch layer refuses, the substitution reading stands, and the
refusal is noted in column 2. A reading without a convention is untouched.

*Circle and line* now reads:

> 2 solutions: (1) `x = r*sqrt(1 + m^2)/(1 + m^2)`, `y = m*r*sqrt(1 + m^2)/(1 + m^2)`;
> (2) `x = -r*sqrt(1 + m^2)/(1 + m^2)`, `y = -m*r*sqrt(1 + m^2)/(1 + m^2)`;
> derived assuming `1 + m^2 != 0`
> [every real solution; by substitution alone (the positive root of y):
> `x = y/m; y = m*r*sqrt(1/(1 + m^2))` (the positive root); derived assuming
> `m != 0`, `1 + m^2 != 0`]

Both points are given, neither unknown is given in terms of the other, and
the condition `m ≠ 0`, which substitution needed only because it divided by
`m`, is gone from the default answer.

## 2. The marks

| mark | declared | result |
|---|---|---|
| K1 | every algebraic system with exactly the declared branches | met: 6 of 6 |
| K2 | every radical system with exactly the declared branches | met: 4 of 4 |
| K3 | every declared refusal by its code | met: 4 of 4 |
| K4 | every answered script verifies; every mutant rejected | met: 16 of 16, 16 of 16 |
| K5 | every dual question: the branch set is the default, the substitution reading is kept, and it is one of the branches | met: 6 of 6 |
| K6 | no regression | **not met**: see §3 |
| K7 | both planted batteries: 0 wrong, planted point in at least 45 of 60 | met: 60 of 60 each, 0 wrong |
| K8 | the cubic battery: three branches when the discriminant is positive, one when negative, every script verified | met: 40 of 40, 12 with three real roots |
| K9 | a Lean file proves what the additions rest on, with no sorry | met |

**8 of 9 marks met.** Yes on all three: cubics and higher-degree numeric polynomials are answered as exact bracketed algebraic numbers (and Cardano's root in letters when the cubic has one real root), nested square roots are answered as towers, and positive-root readings now give every real solution with the substitution reading kept beside it. Eight of the nine marks were met. The miss is the no-regression mark: one Phase 98 reading gained a stated real condition, with its branches unchanged.

The batteries use the same planted conic pairs as Phase 103 (seed 10301)
and a second seed (10401). Phase 103 answered 19 of 60 on the first seed. An
independent numeric count of the real solutions (a Durand–Kerner root finder
on the resultant, in fixed-point rationals since the package holds no float,
then a check of each pair in both equations) agrees with
the branch count on 119 of the 120 battery systems; it could not decide the
other one, and it disagrees on none.

Some answers, as the machine prints them:

* `x^3 - 3*x + 1 = 0` (three real roots, no real radical form):
  `root(t^3 - 3*t + 1, -2, -1)` (about -1.879385), `root(t^3 - 3*t + 1, 0, 1)`
  (about 0.347296), `root(t^3 - 3*t + 1, 1, 2)` (about 1.532089).
* `x^2 + y^2 = 2; y = x^2 - x + 1` (Phase 103 refused it: a cubic was left):
  `(1, 1)` and `x = root(t^3 - t^2 + 3*t + 1, -1, 0)` (about -0.295598) with
  `y = x^2 - x + 1` (about 1.382976).
* `u^2 + v^2 = a; u*v = b` (Phase 103's declared nested-radical refusal):
  four branches `u, v = ±(sqrt(a + 2*b) ± sqrt(a - 2*b))/2`, real when
  `a + 2*b >= 0, a - 2*b >= 0`.
* `x^4 - 2*p*x^2 + q = 0`: `x = ±sqrt(p ± sqrt(p^2 - q))`, real when
  `p^2 - q >= 0` and each outer radicand is non-negative.
* `x^3 + p*x = q`: Cardano's root, derived assuming `p != 0`, real when
  `(1/108)*(4*p^3 + 27*q^2) > 0` (then it is the only real root). The printed
  value is rationalised and long; column 2 gives the readable form
  `t = cbrt(W) - p/(3*cbrt(W))`, `W = q/2 + sqrt((4*p^3 + 27*q^2)/108)`.
* *kinetic energy* `E = (1/2)*m*v^2`: `v = ±sqrt(2*E*m)/m`, real when
  `2*E*m >= 0`, with Phase 98's `v = sqrt(2*E/m)` (the positive root) beside it.

## 3. The miss, as it is

**K6 — one reading moved that the mark said would not.** The mark declared
that, with Phase 104 on, every Phase 98 reading without a positive root or a
hidden unknown is unchanged. Of the 26 Phase 98 questions, 22 are unchanged,
3 moved because of the convention, as intended (kinetic energy, pendulum,
invariant mass), and 1 moved otherwise: *quadratic* `x^2 + x = c`, which
Phase 98 refuses `NONLINEAR` and Phase 103's layer answers, gained the stated
condition "real when 4*c + 1 >= 0". Its two branches are unchanged. The
other parts of the mark hold: with the additions off, Phase 103's declared
systems read 9 of 10 and its refusals 5 of 5, exactly as recorded, and all
10 of Phase 103's declared branch sets are kept with the additions on. The
moved reading is stronger, not wrong, but the mark was declared as "unchanged"
and it is recorded as not met.

## 4. Testing the owner's rule

The owner's rule was to keep both tracks active and to default to the
stronger answer, with testing to decide. What the tests show:

* On all 6 dual questions the substitution answer is one of the branches
  (K5), so the default never contradicts the old reading; it adds the
  branches the convention dropped.
* The branch set is the stronger answer in each case: it is every real
  solution, it gives each unknown in the parameters only, and it drops
  conditions that came only from the order of substitution (`m ≠ 0` in
  circle and line).
* The substitution track is not always kept. It is shown only when its own
  script verifies. In every dual case it does.
* Outside the physics frames (kinetic energy, pendulum, invariant mass),
  no Phase 98 answer changes. Inside them, a physical root (a speed, a
  period) is usually the positive one; the default now gives both signs, and
  the positive-root reading beside it is the physical one. A frame that wants
  only that root can read the bracketed track.

## 5. Post hoc exploration

Not marks: these were tried after the marks were taken
(`cubic_radical_report.exploration`, or `--explore` on the tool).

* **11 harder systems**: all 11 answered, 11 scripts verified, 11 mutants
  rejected. They include a three-unknown symmetric system (6 branches, the
  permutations of 1, 2, 3), `y = x^3 - 2*x; x = y^3 - 2*y` (5 branches), the
  quintic `x^5 - x - 1` (1 branch), `x^6 - 2` (2 branches) and a cubic in a
  letter `x^3 - 3*a*x + 1` (Cardano).
* **100 random pairs of general conics** (seed 777, not planted): 62
  answered, 32 refused `NO_REAL_ROOT`, 6 refused `INCONSISTENT`; 0 script
  failures; the independent numeric count agrees with the branch count (0 for a
  refusal) on 100 of 100.

## 6. What is proved

`RequestProject/GLM/CubicRadicals.lean` builds with no sorry and only the
standard axioms:

* `cardano_root` — with `A ≠ 0`, `A³ = q/2 + s` and `s² = q²/4 + p³/27`,
  `A - p/(3A)` is a root of `x³ + p x = q`.
* `depressed_cubic_unique_real_root` — when `q²/4 + p³/27 > 0`, two real
  roots of `x³ + p x = q` are equal.
* `biquadratic_iff` — `x⁴ + b x² + c = 0` exactly when `x²` is one of
  `(-b ± s)/2`, with `s * s = b² - 4c`.
* `even_quartic_factor` — `x⁴ + b x² + k² = (x² + m x + k)(x² - m x + k)`
  when `m * m = 2k - b`.
* `cubic_irreducible_of_no_rational_root` — a rational polynomial of degree
  one to three with no rational root is irreducible.
* `root_of_sign_change` — a sign change of a real polynomial on `[a, b]`
  holds a root there.

## 7. Defects found on the way

* **A non-real conjugate printed as a solution.** `x^4 - 2*a^2*x^2 - a^4`
  first gave `sqrt(1 - 2^(1/2))` as a branch. Its script verified, because
  the relation holds formally, but the value is not real. The sign of a
  radicand free of letters is now decided exactly, and the branch is dropped.
* **A Phase 98 print that read wrongly.** A power of a radical printed as
  `2^(1/4)^2`, which reads as `2^(1/16)`, and the script of
  `x^2 = 2; y^2 = x` failed. It now prints `(2^(1/4))^2`.

* **A float in the report.** The report's numeric instrument was first
  written in floating point, which the package's exactness inventory (D7)
  refuses outside its two declared sites. It now works in fixed-point
  rationals, and the declared decimals of the cases are strings with the same
  digits; every mark read the same before and after.

## 8. Limits, and what the round leaves

* **Cardano in letters** is used only when the cubic has one real root. With
  three real roots, no real radical form exists; a cubic in letters is then
  answered with the stated condition, not root by root.
* **Degree.** Numeric polynomials are factored up to degree 6; above that, a
  polynomial that is not a pure power (`x^7 = 2` reads `x = 2^(1/7)`) and has
  no rational root is refused `NONLINEAR`.
* **Quintic in letters** (`x^5 + p*x = q`) is refused `NONLINEAR`, as declared.
* **Cardano's printed form** is long because it is rationalised; column 2
  holds the readable form.
* **Round 9 (retrieval)** in `STATUS.md` §3.4 is still next: N5 and I3.

## 9. Re-running it

From `overlay/`:

* `PYTHONPATH=. python3 -m glm_universal.tools cubic-radical` runs the full
  report in about 30 s. Add `--quick` to skip the batteries, `--explore` for
  §5, and `--json` for the rows.
* `PYTHONPATH=. python3 -m unittest glm_universal.tests.test_cubic_radical`
  runs the tests in about 2 s.
* `lake build RequestProject.GLM.CubicRadicals` from the repository root
  builds the Lean file.
