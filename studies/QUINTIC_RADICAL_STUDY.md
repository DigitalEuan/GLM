# Past degree six, and roots with no expression in radicals

## Tier 0 — the coarse read

**Question.** The cubic radical study's §8 left two limits on the branch layer of `solve symbolically`: a numeric polynomial above degree 6 was refused because its factors were not decided, and the quintic in letters `x^5 + p*x = q` was refused with no reason beyond its degree. Can the layer factor past degree 6 without a wrong answer, and can it say, with a proved reason, when a root has no expression in radicals at all?

**Verdict.** Yes to both. Numeric polynomials up to degree 24 are now factored by Zassenhaus's algorithm, and their real roots are answered exactly. Any irreducible factor of prime degree at least 5 with exactly two non-real roots is now marked as having no root in radicals, by a theorem proved in Lean. The quintic in letters is still refused, but the refusal now names a rational point where no root is expressible in radicals, so no formula in radicals of the letters can exist. All seven marks were met. Two limits are counted: the certificate is sufficient but not necessary, and the letter search finds nothing for a family that never has two non-real roots.

**Deciding figure.** 7 of 7 marks met; 6 of 6 high-degree questions with the declared real roots; 5 of 5 certificate questions and 5 of 5 controls; 4 of 4 letter refusals with the declared reason; planted battery 40 of 40 answered, 0 wrong; Zassenhaus = Kronecker on 200 of 200; 7 theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.runtime.quintic_radical_report.quintic_radical_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`CUBIC_RADICAL_STUDY.md`](CUBIC_RADICAL_STUDY.md) §8 names what Phase 104
left: numeric polynomials are factored up to degree 6 and refused above
(`x^7 - 3*x + 1 = 0` read *"factors over the rationals were not decided"*),
and the quintic in letters is refused `NONLINEAR`, as declared. `STATUS.md`
§2.1 item 4 carried both as one To-Do line. Phase 112 takes it.

**Order of work, stated plainly.** The code was written and tried on a
handful of questions before the cases and marks
(`glm_universal/evaluation/quintic_radical_cases.py`) were written down, so
the marks were declared knowing the layer answered those questions. What
keeps the marks from being readings of the layer is where their declared
values come from: the real-root count of each high-degree case follows from
its planted factors; which questions carry the certificate follows from the
theorem; and the planted battery's expected counts come from a Sturm chain on
the product, never from the layer's factoring.

## 1. What was added

**Zassenhaus's algorithm** (`glm_universal.reasoning.symbolic_factor`, new).
Kronecker's search, which Phase 104 used, grows with the product of the
divisor counts of `k + 1` values, which is why it stopped at degree 6. The
new module does what has no such growth:

1. choose a prime `p` that keeps the polynomial squarefree and does not divide
   its leading coefficient, taking the one with the fewest factors among the
   first five that qualify;
2. factor completely modulo `p`: distinct-degree factorisation, then Cantor and
   Zassenhaus's equal-degree splitting. The splitting draws its trial
   polynomials from the package's deterministic generator, never from
   `random`, so the answer is the same every run;
3. lift the factorisation to `p^k` with Hensel's lemma, taking `p^k` past twice
   the Mignotte bound on the coefficients of any factor;
4. recombine: try every subset of the lifted factors, smallest first, times the
   leading coefficient and reduced to the symmetric range, by exact division
   over the integers.

Every factor returned has been checked by exact division. The last factor is
irreducible, because no subset of its modular factors divides it. So the
module can fail to decide, but it cannot return a wrong factorisation. Two
caps hold it: degree 24 and 16 modular factors. Past either cap it returns
nothing, and the layer refuses as before.

`symbolic_algebraic.factor_rational` keeps Phase 104's path unchanged up to
degree 6. Past degree 6, or when Kronecker's budget runs out, it calls the new
module.

**The radical-free certificate**
(`symbolic_factor.radical_free`, `symbolic_factor.certify_numeric`). An
irreducible polynomial over the rationals of prime degree `n ≥ 5` with exactly
`n - 2` distinct real roots has the full symmetric group as its Galois group,
which is not solvable, so none of its roots is expressible in radicals. Every
hypothesis is decided exactly by the layer: irreducibility by its factoring,
the degree, and the real roots by a Sturm chain. When an irreducible factor of
an answered question qualifies, column 2 says so for each of its roots and
names the Lean declaration. For example, `x^5 - 4*x + 2 = 0` is answered with
three isolated real roots, each carrying *"no root of it is expressible in
radicals: irreducible over the rationals, of prime degree 5, with exactly two
non-real roots, so its Galois group is the full symmetric group on 5 roots,
which is not solvable"*.

**The quintic in letters, with its reason**
(`symbolic_nonlinear._no_radical_formula`). When a polynomial in letters of
prime degree at least 5 is refused, the layer specialises the letters to small
integers. It tries points smallest first, in a fixed order, up to 400 points,
and looks for one where the polynomial keeps its degree and passes the
certificate. If it finds one, the refusal says so. The refusal code is still
`NONLINEAR`, so every pinned refusal keeps its code. For example:

> x is a root of a polynomial of degree 5 with no rational root:
> x^5 + p*x - q = 0; no formula in radicals of p, q exists: at p = -3, q = 1
> the equation is x^5 - 3*x - 1 = 0, and no root of it is expressible in
> radicals …, so no radical expression defined at that point gives a root
> there

The reason is sound because any expression in radicals of `p` and `q` that is
defined at that rational point evaluates there to a number solvable by
radicals.

## 2. The marks

| mark | declared | result |
|---|---|---|
| R1 | every high-degree question answered with the declared real roots, its script verified, every `root(f, lo, hi)` sound (`f` divides the question's polynomial exactly and changes sign on the bracket) | met: 6 of 6 (degrees 7, 8, 8, 10, 12, 9) |
| R2 | every certificate question carries the radical-free statement | met: 5 of 5 |
| R3 | no control carries it | met: 5 of 5 |
| R4 | every letter question refused `NONLINEAR`, with the reason exactly where declared | met: 4 of 4 |
| R5 | planted battery of degrees 7 to 16: 0 wrong, at least 90 % answered | met: 40 of 40 answered, 0 wrong |
| R6 | Zassenhaus's factors equal Kronecker's on degree 4 to 6 | met: 200 of 200 (127 of them reducible) |
| R7 | the Lean file holds every named theorem and no `sorry` | met |

The controls of R3 are `x^5 - x - 1` (Galois group `S5`, but one real root),
`x^5 - 5*x + 12` (solvable, one real root), `x^7 - 3*x + 1` (three real roots
of seven), a cubic and a sextic. The letter cases of R4 that must carry no
reason are De Moivre's quintic `x^5 - 5*a*x^3 + 5*a^2*x = b` and the septic
trinomial `x^7 + a*x = b`. De Moivre's quintic is solvable in radicals for
every value of its letters, so if the certificate ever fired on it, that
would be a bug. It does not.

**What the marks say, in one paragraph.** Yes to both. Numeric polynomials up to degree 24 are now factored by Zassenhaus's algorithm, and their real roots are answered exactly. Any irreducible factor of prime degree at least 5 with exactly two non-real roots is now marked as having no root in radicals, by a theorem proved in Lean. The quintic in letters is still refused, but the refusal now names a rational point where no root is expressible in radicals, so no formula in radicals of the letters can exist. All seven marks were met. Two limits are counted: the certificate is sufficient but not necessary, and the letter search finds nothing for a family that never has two non-real roots.

**Regression.** Phase 104's own report (`tools cubic-radical`) reads exactly
as before: 8 of its 9 marks, with K6 the same documented miss. The quintic in
letters keeps its declared code `NONLINEAR` in both the Phase 104 and the
Phase 108 cases.

## 3. What is proved

`RequestProject/GLM/QuinticRadicals.lean`, namespace `GLM.QuinticRadicals`, no
`sorry`, standard axioms only:

* `no_radical_root_of_prime_degree` — the certificate: an irreducible `p` over
  `ℚ` of prime degree at least 5 with exactly two non-real roots has no root
  solvable by radicals;
* `card_complex_roots_of_irreducible` — such a polynomial has as many complex
  roots as its degree;
* `irreducible_trinomial`, `gal_trinomial`, `trinomial_family_no_radical_root`
  — the family `x^5 - a x + b` with `b < a` and an Eisenstein prime;
* `trinomial_no_radical_root` — no complex root of `x^5 - 4x + 2` is solvable
  by radicals;
* `quintic_in_letters_no_radical_formula` — there are rational `p`, `q` and a
  complex `x` with `x^5 + p x = q` that is not solvable by radicals over `ℚ`.

The construction for the trinomial family follows the Abel–Ruffini example in
Mathlib's `Archive` (Thomas Browning). The Archive is not part of the
importable library, so the construction is restated in the project. The
certificate theorem itself is new to this project and rests on Mathlib's
`galActionHom_bijective_of_prime_degree`, `solvableByRad.isSolvable'` and
`Equiv.Perm.not_solvable`.

**What the proof does not cover.** The Python side decides the hypotheses:
irreducibility (exact division and exhaustive recombination), the degree, and
the real-root count (Sturm). None of these decisions is checked in Lean. The
theorem certifies the inference from those hypotheses to the conclusion, not
the computation of them.

## 4. Limits, and what the round leaves

* **Sufficient, not necessary.** `x^5 - x - 1` has no root in radicals, but it
  has one real root, so the certificate does not apply and the layer says
  nothing. A general solvability test, such as the resolvent sextic for
  quintics or Galois group computation by Frobenius cycle types, would be the
  next step.
* **The letter search** finds nothing for a family that never has exactly two
  non-real roots at small points. `x^7 + a*x = b` has at most three real roots,
  so it never qualifies. In that case the refusal keeps its old wording.
* **Caps.** Degree 24 and 16 modular factors. Swinnerton-Dyer polynomials,
  which split into many factors modulo every prime, would reach the second
  cap. Lattice reduction (van Hoeij) is the known way past it.
* **The modes path.** Phase 109's `modes.higher` route names the roots of a
  characteristic polynomial of degree 5 or more through its coefficients, and
  does not yet carry the certificate.

**Taken by Phase 113.** The first two limits are taken by
[`FROBENIUS_RADICAL_STUDY.md`](FROBENIUS_RADICAL_STUDY.md): a Frobenius
certificate (Galois's theorem on groups of prime degree) now reaches
`x^5 - x - 1` and the septic trinomial in letters. Because it reaches two of
the R3 controls and the R4 septic case, the report now reads this round's
certificate by its own words (*"with exactly two non-real roots"*, and the
citation `quintic_in_letters_no_radical_formula`); it still meets 7 of 7.

## 5. Re-running it

From ``:

* `PYTHONPATH=. python3 -m glm_universal.tools quintic-radical` runs every mark
  in about 15 s. `--quick` skips the batteries and `--json` gives the rows.
* `PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_quintic_radical.py`
  runs the tests in about 10 s.
* `lake build RequestProject.GLM.QuinticRadicals` from the repository root
  builds the Lean file.
