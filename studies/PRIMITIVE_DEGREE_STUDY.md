# Roots with no expression in radicals, from one Frobenius element, in a degree that is not a prime power

## Tier 0 — the coarse read

**Question.** Phase 114's composite-degree certificate needs a second Frobenius element, one with a power that is a transposition or a 3-cycle, so `solve symbolically` says nothing about a sextic whose Galois group is `PGL(2, 5)` or `PSL(2, 5)` acting on six points, though neither group is solvable. Can the layer drop the second element where the degree allows it, and still never certify a polynomial whose group is solvable?

**Verdict.** Yes, in every degree that is not a prime power. A solvable primitive permutation group has prime-power degree (Galois), so in degree 6, 10, 12, 14, 15 and so on, one element of cycle type `(n - 1, 1)`, which already makes the group primitive, rules solvability out; both steps are proved in Lean. All eight marks were met: the statement reaches the three declared sextics, built as Cayley resolvents of quintics with groups `S5` and `A5`, and all 60 resolvents of the reach battery, none of which Phase 114's certificate reaches; it is given to none of 201 polynomials with solvable groups, and it stays out of prime-power degree. Dedekind's theorem is still used, not proved.

**Deciding figure.** 8 of 8 marks met; 3 of 3 declared sextics certified; 6 of 6 solvable controls silent; `PGL(2, 5)` and `PSL(2, 5)` built, each holding a `(5, 1)` element and no Jordan element; 0 of 201 solvable polynomials certified; 60 of 60 Cayley sextics certified, 0 by Phase 114; 512 of 512 prime-power readings right and 0 of 100 prime-power-degree polynomials touched; 6 theorems, 0 `sorry`; Phase 115 still 8 of 8.

**Recomputed by.** `glm_universal.runtime.primitive_degree_report.primitive_degree_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`PRIMITIVE_RADICAL_STUDY.md`](PRIMITIVE_RADICAL_STUDY.md) §4 left, second
among its limits, the primitive groups that hold no element with a power that
is a transposition or a 3-cycle: `PGL(2, 5)` acting on the six points of the
projective line over `F_5` is isomorphic to `S5`, so not solvable, and a
sextic with that group stayed silent. The line was carried in `STATUS.md`
§2.2 as part of *Radicals, the rest*, and
[`COMPOSED_RADICAL_STUDY.md`](COMPOSED_RADICAL_STUDY.md) §4 left it as it was.

The fact that removes the second element is classical. If a solvable group
acts primitively on `n ≥ 2` points, take the last nontrivial term of its
derived series: it is a nontrivial normal abelian subgroup. Its Sylow
`p`-subgroup, for a prime `p` dividing its order, is characteristic in it, so
normal in the whole group, and a nontrivial normal subgroup of a primitive
group is transitive, so `n` divides a power of `p`. In a degree that is not a
prime power that is impossible, so primitivity alone rules solvability out,
and Phase 114 already proves primitivity from one element of cycle type
`(n - 1, 1)`.

**Order of work, stated plainly.** The Lean file was written and built first.
The cases and marks (`glm_universal/evaluation/primitive_degree_cases.py`)
were then written and committed **before the certificate was written or
tried**; the commit that holds them precedes the commit that holds the code.
Before the cases were written, the declared sextics were checked to be
irreducible with the existing factoring, which this round does not change,
and their real roots were counted outside the package (`mpmath`), because a
sextic with no real root is refused before any certificate is tried.

**Where the declared sextics come from.** For a quintic `x^5 + a x + b`
with roots `x_1 … x_5`, let `θ` be the square of the sum of `x_i x_j` over
the edges of a pentagon on the roots minus the same sum over its pentagram.
There are six such values, permuted by the Galois group as `S5` permutes the
six pentagons, which is the action of `PGL(2, 5)` on six points. Their monic
polynomial, Cayley's sextic resolvent in this normalisation, is

    θ^6 - 40a θ^5 + 880a^2 θ^4 - 8960a^3 θ^3 + 44800a^4 θ^2
        - (108544a^5 + 3200000b^4) θ + 102400a^6.

It was read off numerical roots to 80 digits at four points and checked at
five more; every coefficient is fixed by weight (`θ` and `a` weigh 4, `b`
weighs 5), so the four points determine it. When the quintic's group is not
solvable the sextic is irreducible with group `PGL(2, 5)` (from `S5`) or
`PSL(2, 5)` (from `A5`); when it is solvable, inside the Frobenius group of
order 20, which fixes one pentagon, the sextic has a rational root. The three
declared sextics are those of `x^5 - x - 1` and `x^5 + 2x - 1` (group `S5`)
and `x^5 + 20x + 16` (group `A5`), rescaled `θ = s u` to small coefficients.

## 1. What was added

**The test** (`glm_universal.reasoning.symbolic_factor`, new functions
`is_prime_power`, `long_cycle_prime`, `radical_free_degree`). For an
irreducible polynomial over the rationals of a degree `n ≥ 6` that is not a
prime power, primes below 1000 are tried in increasing order, skipping those
that divide the discriminant or the leading coefficient, exactly as in Phases
113 and 114, until one gives factor degrees `1, n - 1`. Then the group is
transitive (irreducibility), primitive (Phase 114's argument from that
element), and so not solvable (Galois).

**In the layer.** `radical_free_galois` keeps its order: Phase 113's test in
prime degree; in composite degree Phase 114's two-element test first, so its
wording is unchanged wherever it applies; then this round's test; then Phase
115's composition certificate. The first declared sextic now carries, beside
each real root: *"no root of it is expressible in radicals: irreducible over
the rationals, of degree 6, which is not a prime power; modulo 3 it factors
into irreducible factors of degrees 1, 5, so by Dedekind's theorem its Galois
group holds an element fixing one root and cycling the other 5, which makes
the group primitive; a solvable primitive group has prime-power degree
(Galois), so the group is not solvable
(GLM.PrimitiveDegree.no_radical_root_of_long_cycle_of_not_isPrimePow;
Dedekind's theorem is not checked in Lean)"*. The letter search, the modes
route and the composition certificate's outer reason all call
`radical_free_galois`, so they inherit the test without further change.

**The instrument.** `tools primitive-degree` runs the marks
(`runtime/primitive_degree_report.py`), reading every declared question
through the frames the CLI uses. The exact objects the marks read — the two
projective groups as permutations, the Cayley sextics, the reach battery —
are in `reasoning/primitive_degree_groups.py`, so that the unit tests
(`tests/test_primitive_degree.py`, 16) can check them, and the wiring at the
branch layer, without reaching the router, which would take the whole Lean
development into their closure
([`ITERATION_COST_STUDY.md`](ITERATION_COST_STUDY.md) §5k).

## 2. The marks

| mark | declared | result |
|---|---|---|
| D1 | every declared sextic is answered and carries the new statement | met: 3 of 3 |
| D2 | no solvable control carries any radical-free statement | met: 6 of 6 |
| D3 | `PGL(2, 5)` and `PSL(2, 5)`, built as permutations of the projective line over `F_5`: orders 120 and 60, transitive, a `(5, 1)` element, no element Phase 114's Jordan reading accepts; Phase 114 silent on the declared sextics | met: both groups as declared; silent on 3 of 3 |
| D4 | the soundness batteries of Phases 114 and 115, every group solvable: no certificate | met: 0 of 201 certified |
| D5 | the reach battery, Cayley sextics of random trinomial quintics, both irreducible: at least 95 % certified by the new statement, none by Phase 114's | met: 60 of 60, 0 by Phase 114 |
| D6 | the prime-power test agrees with trial division on 1 to 512, and the new test is silent on every polynomial of degree 8 or 9 in Phase 114's reach battery | met: 512 of 512; 0 of 100 |
| D7 | the Lean file holds every named theorem and no `sorry` | met |
| D8 | Phase 115's report still meets 8 of 8 | met |

The solvable controls of D2 are `x^6 - 2`, `x^6 - 3`, the cyclotomic
polynomials of 7 and 9 (both refused `NO_REAL_ROOT`, as before; the mark asks
only that no statement appear), the composition `x^6 - x^2 - 1`, and the
Cayley sextic of the Frobenius quintic `x^5 + 15x + 12`, which has the
rational root 180.

**Why D3, D4 and D6 are a real test.** The conclusion is a theorem, so a
certificate on a solvable polynomial would be a bug — a wrong modular reading
or a wrong degree gate. D4 is the direct check. D6 is the gate: in degree 8
the affine group `AGL(1, 8)` and in degree 9 `AGL(2, 3)` are solvable,
primitive, and hold `(n - 1, 1)` elements, so a test that fired there would
be unsound; it does not fire on any of the 100 degree-8 and degree-9
polynomials, though every one of them has such an element (Phase 114
certifies them by its two-element test). D3 checks the claim that motivated
the round: neither group holds an element Phase 114's reading accepts, so
nothing short of this round's argument reaches them.

**What the marks say, in one paragraph.** Yes, in every degree that is not a prime power. A solvable primitive permutation group has prime-power degree (Galois), so in degree 6, 10, 12, 14, 15 and so on, one element of cycle type `(n - 1, 1)`, which already makes the group primitive, rules solvability out; both steps are proved in Lean. All eight marks were met: the statement reaches the three declared sextics, built as Cayley resolvents of quintics with groups `S5` and `A5`, and all 60 resolvents of the reach battery, none of which Phase 114's certificate reaches; it is given to none of 201 polynomials with solvable groups, and it stays out of prime-power degree. Dedekind's theorem is still used, not proved.

## 3. What is proved

`RequestProject/GLM/PrimitiveDegree.lean`, no `sorry`, only the standard
axioms (`propext`, `Classical.choice`, `Quot.sound`, checked with
`#print axioms`):

* `exists_normal_comm_ne_bot` — a nontrivial solvable group has a nontrivial
  normal abelian subgroup;
* `exists_normal_pGroup_ne_bot` — a nontrivial finite solvable group has a
  nontrivial normal `p`-subgroup;
* `card_dvd_of_normal_ne_bot` — in a primitive permutation group the order of
  a nontrivial normal subgroup is a multiple of the degree (Mathlib's
  `IsPreprimitive.isQuasiPreprimitive` gives transitivity);
* `isPrimePow_card_of_isPreprimitive_of_isSolvable` — **Galois's theorem**,
  the half needed: a solvable primitive permutation group on at least two
  points has prime-power degree;
* `not_solvable_of_long_cycle_of_not_isPrimePow` — the Galois group of an
  irreducible polynomial over `ℚ` of a degree that is not a prime power,
  holding an element of cycle type `(n - 1, 1)`, is not solvable;
* `no_radical_root_of_long_cycle_of_not_isPrimePow` — **the certificate the
  layer cites**.

What is not proved: Dedekind's theorem (the factor degrees modulo `q` are the
cycle type of an element of the group), the factorisations, which the Python
side decides, and the Cayley resolvent formula, which only builds test cases
and is not used by the layer.

## 4. Limits, and what the round leaves

* **Prime-power degree.** In degree 8, 9, 16, 25 and so on, a primitive group
  can be solvable, so this test rightly stays out; Phase 114's two-element
  test is all there is, and a primitive non-solvable group of prime-power
  degree without a Jordan element (for example `PSL(2, 7)` on eight points)
  stays silent.
* **Primitive groups with no `(n - 1, 1)` element.** `S5` acting on the ten
  pairs of five points is primitive and not solvable, but none of its
  elements fixes exactly one pair while cycling the other nine, so a decic
  with that group stays silent. Primitivity read some other way (from two
  elements whose supports overlap, or a resolvent) would reach it.
* **Outer polynomials of degree below 5**, **imprimitive groups that are not
  compositions**, **no positive statement** and **Dedekind in Lean**, as
  Phases 114 and 115 left them.

## 5. Re-running it

From `overlay/`:

* `PYTHONPATH=. python3 -m glm_universal.tools primitive-degree` runs every
  mark in about four minutes, most of it Phase 115's report for D8, which
  re-reads Phases 114 and 112. `--quick` skips the batteries and the
  regression (D4–D6, D8), and `--json` gives the rows.
* `PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_primitive_degree.py`
  runs the tests in a few seconds.
* `lake build RequestProject.GLM.PrimitiveDegree` from the repository root
  builds the Lean file.
