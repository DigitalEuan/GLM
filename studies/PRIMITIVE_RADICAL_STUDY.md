# Roots with no expression in radicals in composite degree, and on the modes route

## Tier 0 — the coarse read

**Question.** Phase 113's Frobenius certificate needs prime degree, so `solve symbolically` says nothing about `x^6 - x - 1`, and the `modes.higher` route names the roots of a characteristic polynomial of degree five or more with no statement about radicals at all. Can the layer read two Frobenius elements in composite degree, carry the certificate to the modes route, and still never certify a polynomial whose group is solvable?

**Verdict.** Yes, for groups that hold the two elements the test looks for. An element of cycle type `(n - 1, 1)` makes the Galois group primitive, and an element with a power that is a transposition or a 3-cycle then puts the alternating group inside it (Jordan's theorem); both steps are proved in Lean. All ten marks were met: the statement reaches `x^n - x - 1` for n = 6, 8, 9, 10 and 12, the sextic trinomial in letters, and the chain pendulums of five and six links, it is given to none of 141 polynomials with solvable groups, and it reaches all 200 random irreducible polynomials of degree 6, 8, 9 and 10. It stays silent on an imprimitive group that is not solvable, as declared, and Dedekind's theorem is still used, not proved.

**Deciding figure.** 10 of 10 marks met; 5 of 5 non-solvable questions certified; 7 of 7 solvable controls and the imprimitive limit silent; 2 of 2 letter questions with the declared reason; 0 of 141 solvable polynomials certified; 200 of 200 random irreducible polynomials of composite degree certified; 182 of 182 cycle types read right; 3 theorems, 0 `sorry`; 3 of 3 chain pendulums carry the reason; Phase 113 still 9 of 9.

**Recomputed by.** `glm_universal.runtime.primitive_radical_report.primitive_radical_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`FROBENIUS_RADICAL_STUDY.md`](FROBENIUS_RADICAL_STUDY.md) §4 left two
limits that this round takes, both carried in `STATUS.md` §2.2 as "Radicals,
the rest":

* **Composite degree.** Phase 113's test rests on Galois's theorem for groups
  of prime degree, where a transitive group is automatically primitive. A
  transitive group of composite degree can be imprimitive, and an imprimitive
  group can be solvable while holding a transposition (the wreath products),
  so the prime-degree test cannot simply be run on a sextic. The declared case
  was `x^6 - x - 1`.
* **The modes path.** Phase 109's `modes.higher` route says, for five or more
  degrees of freedom, that "a polynomial of degree n has no general solution
  in radicals (Abel-Ruffini)". That is true of the general polynomial and says
  nothing about the one in front of it.

**Order of work, stated plainly.** The Lean file was written first. The cases
and marks (`glm_universal/evaluation/primitive_radical_cases.py`) were then
written and committed **before the code was tried on any of them**; the
commit that holds them precedes the commit that holds the code. The declared
values are classical mathematics: `x^n - x - 1` has the full symmetric group
for every `n` (Osada); pure powers, cyclotomic polynomials and compositions
`g(x^k)` with `g` of degree at most 4 have solvable groups; `x^10 - x^2 - 1 =
g(x^2)` with `g = y^5 - y - 1` has a group mapping onto `S5`, so not
solvable, but with the blocks `{r, -r}`; and the identical chain pendulum of
`n` links has the characteristic polynomial `n! L_n(x)` in `x = l w^2 / g`,
`L_n` the Laguerre polynomial, whose group is the full symmetric group
(Schur). The one change to the cases after that commit was before any run:
the unequal five-link chain was added to P9, and the chain frame was taught
to read "sextuple", which it did not.

## 1. What was added

**The test** (`glm_universal.reasoning.symbolic_factor`, new functions
`jordan_power`, `is_long_cycle`, `primitive_pattern`,
`radical_free_primitive`, `radical_free_galois`; `certify_numeric_any` now
covers composite degree). For an irreducible polynomial `f` over the
rationals of composite degree `n ≥ 6`, primes `q` below 1000 are tried in
increasing order, skipping those that divide the discriminant or the leading
coefficient, exactly as in Phase 113. The test looks for two primes:

1. one at which the factor degrees are `1, n - 1`: by Dedekind's theorem the
   Galois group holds an element fixing one root and cycling the others;
2. one at which the degrees have exactly one 2 and every other degree odd, or
   exactly one 3 and every other degree prime to 3: a power of that
   Frobenius element (the least common multiple of the other degrees) is a
   transposition or a 3-cycle.

Then the group is transitive (irreducibility), primitive (by the first
element: a block through the fixed root is carried to itself by every power
of the long cycle, and those powers reach every other root), and a primitive
group holding a transposition or a 3-cycle contains the alternating group
(Jordan), which is not solvable for `n ≥ 5`. In prime degree the layer keeps
Phase 113's one-element test, so its wording is unchanged there.

**In the layer** (`glm_universal.reasoning.symbolic_nonlinear`). An
irreducible factor with real roots tries the conjugation certificate, then
the Frobenius test for its degree (`radical_free_galois`). `x^6 - x - 1 = 0`
now carries, beside each real root: *"no root of it is expressible in
radicals: irreducible over the rationals, of degree 6; modulo 5 it factors
into irreducible factors of degrees 1, 5 and modulo 17 into degrees 1, 2, 3,
so by Dedekind's theorem its Galois group holds an element fixing one root
and cycling the other 5, which makes the group primitive, and an element
whose cube is a transposition; a primitive group holding a transposition
contains the alternating group, which is not solvable
(GLM.PrimitiveRadicals.no_radical_root_of_primitive_pattern; Dedekind's
theorem is not checked in Lean)"*.

**In the letter search.** The search for a point where an equation in
letters has no root in radicals no longer requires prime degree; its
Frobenius pass uses the test for the degree. `x^6 + a*x = b` is refused
`NONLINEAR` with *"no formula in radicals of a, b exists: at a = 1, b = 1 the
equation is x^6 + x - 1 = 0, and no root of it is expressible in radicals …"*.

**On the modes route** (`glm_universal.reasoning.derivation`,
`symbolic_nonlinear.modes_radical_reason`, and the text in
`runtime/derivation_frames.modes_higher_text`). When the route `named` is
taken, the characteristic polynomial's letters (masses, lengths, `g`) are
specialised to positive points — all 1 first, then one letter at a time
raised to 2 and to 3 — and the first point where the polynomial keeps its
degree, is irreducible and passes any of the three certificates is stated as
the reason no formula in radicals of the letters gives these roots. The
identical six-link chain now reads *"… no formula in radicals of g, l gives
these roots: at g = 1, l = 1 the equation is w2^6 - 36*w2^5 + 450*w2^4 -
2400*w2^3 + 5400*w2^2 - 4320*w2 + 720 = 0, and no root of it is expressible in
radicals …, so no radical expression defined at that point gives a root
there"*. The chain frame reads six links ("sextuple", "six", "6-link") as
well as two to five.

## 2. The marks

| mark | declared | result |
|---|---|---|
| P1 | every `x^n - x - 1` below carries the primitive statement | met: 5 of 5 (n = 6, 8, 9, 10, 12) |
| P2 | no solvable control of composite degree carries any radical-free statement | met: 7 of 7 |
| P3 | the declared limit `x^10 - x^2 - 1` (not solvable, imprimitive) is answered and carries none | met: 1 of 1 |
| P4 | `x^6 + a*x = b` refused `NONLINEAR` with the primitive reason; `x^6 + a*x^2 = b` with no radical-free reason | met: 2 of 2 |
| P5 | the soundness battery, solvable by construction: no certificate | met: 0 of 141 certified |
| P6 | the reach battery, random irreducible monic polynomials of degree 6, 8, 9, 10: at least 95 % certified | met: 200 of 200 (50 of each degree) |
| P7 | on every cycle type of degree 6, 8, 9, 10 and 12, the Jordan test fires exactly on its declared types and names a power that is a single 2- or 3-cycle, counted from the cycle type; the long-cycle test fires exactly on `(n - 1, 1)` | met: 182 of 182 |
| P8 | the Lean file holds every named theorem and no `sorry` | met |
| P9 | the identical chains of five and six links and the unequal chain of five carry a radical-free reason on their modes | met: 3 of 3 |
| P10 | Phase 113's report still meets 9 of 9 | met |

The solvable controls of P2 are `x^6 - 2`, `x^8 - 2`, the cyclotomic
polynomials of 7 and 9, and the compositions `x^6 - x^2 - 1`, `x^8 - x^2 - 1`
and `x^9 - x^3 - 1`. The two cyclotomic ones are refused `NO_REAL_ROOT`, as
before this round; the mark asks only that no radical-free statement appear.
The soundness battery of P5 is the pure powers `x^n - c` for `n` in 6, 8, 9,
10, 12 and `c` from 2 to 12, the cyclotomic polynomials of 7, 9, 11, 13, 15,
16, 20, 21, 24, 28 and 36, and 100 compositions `g(x^k)` with `g` a monic
cubic or quartic drawn by the package's generator, counting only the
irreducible ones: 141.

**Why P2, P3 and P5 are a real test.** As in Phase 113, the conclusion is a
theorem, so a certificate on a solvable polynomial would be a bug — a wrong
modular reading or a wrong shape test — and P7 checks the shape tests alone.
P3 is the other side: the test must also *not* fire on a group that is not
solvable but is imprimitive, because there it has no theorem behind it. An
element fixing one root of `x^10 - x^2 - 1` fixes its block `{r, -r}`, so no
element of type `(9, 1)` exists, and the layer is silent.

**What the marks say, in one paragraph.** Yes, for groups that hold the two elements the test looks for. An element of cycle type `(n - 1, 1)` makes the Galois group primitive, and an element with a power that is a transposition or a 3-cycle then puts the alternating group inside it (Jordan's theorem); both steps are proved in Lean. All ten marks were met: the statement reaches `x^n - x - 1` for n = 6, 8, 9, 10 and 12, the sextic trinomial in letters, and the chain pendulums of five and six links, it is given to none of 141 polynomials with solvable groups, and it reaches all 200 random irreducible polynomials of degree 6, 8, 9 and 10. It stays silent on an imprimitive group that is not solvable, as declared, and Dedekind's theorem is still used, not proved.

**Phase 113's mark F3, narrowed.** F3 declared the sextic `x^6 - x - 1`
silent because Phase 113's test applies only to prime degree. This round's
test now certifies it, as it should, so `runtime/frobenius_radical_report.py`
reads F3 by Phase 113's own citation
(`GLM.FrobeniusRadicals.no_radical_root_of_frobenius_shape`) instead of by
any radical-free statement. The report still meets 9 of 9.

## 3. What is proved

`RequestProject/GLM/PrimitiveRadicals.lean`, no `sorry`, only the standard
axioms (`propext`, `Classical.choice`, `Quot.sound`, checked with
`#print axioms`):

* `isPreprimitive_of_isCycle_fixing_one` — a transitive permutation group
  holding a single cycle that moves every point but one is primitive;
* `not_solvable_of_long_cycle_of_swap_or_three_cycle` — the Galois group of
  an irreducible polynomial over `ℚ` of degree at least 5 holding such a
  cycle and a transposition or a 3-cycle is not solvable (Jordan's theorem
  from Mathlib, `subgroup_eq_top_of_isPreprimitive_of_isSwap_mem` and
  `alternatingGroup_le_of_isPreprimitive_of_isThreeCycle_mem`);
* `no_radical_root_of_primitive_pattern` — **the certificate the layer
  cites**, with the two elements given by their cycle types, reusing Phase
  113's `exists_pow_cycleType_singleton` for the power.

What is not proved: Dedekind's theorem (the factor degrees modulo `q` are
the cycle type of an element of the group), and the factorisations
themselves, which the Python side decides.

## 4. Limits, and what the round leaves

* **Imprimitive groups.** A group that is not solvable but has blocks holds
  no `(n - 1, 1)` element, so the test is silent: the declared case is
  `x^10 - x^2 - 1`. Such a polynomial is a composition `g(h(x))`, and the
  next step would be to find the decomposition and certify `g` — taken by
  Phase 115 ([`COMPOSED_RADICAL_STUDY.md`](COMPOSED_RADICAL_STUDY.md)), whose
  certificate now answers `x^10 - x^2 - 1`; mark P3 reads this round's own
  citation since then.
* **Primitive groups without a transposition or a 3-cycle.** `PGL(2, 5)`
  acting on six points is `S5`, not solvable, and holds no element with a
  power that is a transposition or a 3-cycle; a sextic with that group stays
  silent. A primitive-group classification by degree, or a Galois resolvent,
  would reach it.
  Taken by Phase 116 in every degree that is not a prime power
  ([`PRIMITIVE_DEGREE_STUDY.md`](PRIMITIVE_DEGREE_STUDY.md)): a solvable
  primitive group has prime-power degree, so there the `(n - 1, 1)` element
  alone suffices, and the `PGL(2, 5)` sextics are now certified.
* **No positive statement**, as before: the test never says a root *is*
  expressible in radicals.
* **Dedekind in Lean**, as before.
* **The modes search** tries `1 + 2L` positive points for `L` letters; a
  characteristic polynomial that is reducible at all of them gets no reason.
  None of the three chains needed more than the first point.

## 5. Re-running it

From `overlay/`:

* `PYTHONPATH=. python3 -m glm_universal.tools primitive-radical` runs every
  mark in about 40 s. `--quick` skips the batteries and the Phase 113
  regression, and `--json` gives the rows.
* `PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_primitive_radical.py`
  runs the tests in about 30 s.
* `lake build RequestProject.GLM.PrimitiveRadicals` from the repository root
  builds the Lean file.
