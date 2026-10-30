# Roots with no expression in radicals, read from one Frobenius element

## Tier 0 — the coarse read

**Question.** Phase 112's radical-free certificate reads the Galois group through complex conjugation, so it needs exactly two non-real roots and is silent on `x^5 - x - 1`, whose group is the full symmetric group. Can the branch layer of `solve symbolically` read the group through one Frobenius element instead, say with a proved reason when no root is expressible in radicals, and never say it of a polynomial whose group is solvable?

**Verdict.** Yes. The layer now factors an irreducible polynomial of prime degree modulo small primes, and when one factorisation has a cycle shape that no affine map `x ↦ ax + b` has, it states that no root is expressible in radicals, citing Galois's theorem on groups of prime degree, proved in Lean. All nine marks were met: the statement now reaches `x^5 - x - 1`, the A5 quintic `x^5 + 20x + 16`, Trinks's septic with group `PSL(2, 7)` and the septic trinomial in letters, it is given to none of 178 polynomials with solvable groups, and it reaches all 200 random irreducible quintics and septics. Dedekind's theorem, which turns the factorisation into a group element, is used but not proved in Lean, and composite degrees are still out of reach.

**Deciding figure.** 9 of 9 marks met; 6 of 6 non-solvable questions certified; 5 of 5 solvable controls and the composite-degree limit silent; 3 of 3 letter refusals with the declared reason; 0 of 178 solvable polynomials certified; 200 of 200 random irreducible quintics and septics certified (50 by conjugation, all 50 also by Frobenius); 2,561 of 2,561 modular readings and 179 of 179 cycle types read right; 9 theorems, 0 `sorry`; Phase 112 still 7 of 7.

**Recomputed by.** `glm_universal.runtime.frobenius_radical_report.frobenius_radical_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`QUINTIC_RADICAL_STUDY.md`](QUINTIC_RADICAL_STUDY.md) §4 left the
radical-free certificate sufficient and not necessary: `x^5 - x - 1` has no
root in radicals, but it has one real root, so the certificate (two non-real
roots, hence a transposition from complex conjugation) does not apply and the
layer said nothing. It named "Galois group computation by Frobenius cycle
types" as the next step, and the septic trinomial in letters `x^7 + a*x = b`
as a family the letter search could never reach. `STATUS.md` §2.2 carried both
as "Radicals, the rest". Phase 113 takes them.

**Order of work, stated plainly.** The work went in two steps. The first was
Jordan's theorem: a transposition or a 3-cycle in the group (Lean §1–§2 of
the file). With it, Trinks's septic was declared out of reach, because its
group `PSL(2, 7)` holds neither. Writing that limit down showed that Galois's
theorem on groups of prime degree would reach it. That theorem was then
proved (Lean §3), and the layer was moved onto it. The cases and marks
(`glm_universal/evaluation/frobenius_radical_cases.py`) were rewritten for
the second step: Trinks's septic moved from the declared limit to the
certified cases, and a sextic became the declared limit. Throughout, the code
was tried on a handful of the cases before the marks were written, and the
full report was run after. What keeps the marks from being readings of the
layer is where the declared values come from: which cases have a solvable
group and which do not is classical, not read off the layer, and the
soundness battery is solvable by construction.

## 1. What was added

**The test** (`glm_universal.reasoning.symbolic_factor`, new functions
`frobenius_degrees`, `non_affine_power`, `frobenius_pattern`,
`radical_free_frobenius`, `certify_numeric_any`). For an irreducible
polynomial `f` over the rationals of prime degree `n`, primes `q` below 1000
are tried in increasing order. A prime is skipped when it divides the leading
coefficient or `f` is not squarefree modulo `q`, that is, when `q` divides the
discriminant. Otherwise the distinct-degree factorisation modulo `q` gives the
degrees of the irreducible factors, the fixed points counted as 1. The test
fires when that list is *not* of an affine shape. The affine shapes are the
identity, one cycle through every root, and one fixed root with every other
cycle of one length; these are the shapes of the maps `x ↦ ax + b` modulo `n`.
Then:

1. by Dedekind's theorem the Galois group holds an element whose cycle type
   on the roots is that list of degrees (the Frobenius element at `q`);
2. a power of that element moves some roots and fixes at least two: the
   element itself when it fixes two roots, otherwise its `k`-th power, where
   `k` is a cycle length that some other cycle length does not divide;
3. the Galois group of an irreducible polynomial is transitive on its roots,
   and in a solvable transitive group of prime degree only the identity fixes
   two points (Galois);
4. so the group is not solvable, and no root of `f` is solvable by radicals.

Steps 2 to 4 are proved in Lean (§3). Step 1 is not.

**Why the test is complete in the limit.** The other half of Galois's theorem
says a transitive group of prime degree is solvable exactly when it lies in
the affine group. A non-solvable group therefore holds an element of
non-affine shape. By Chebotarev's density theorem, every conjugacy class of
the group occurs as a Frobenius element at a positive proportion of primes.
So for every irreducible polynomial of prime degree with no root in radicals,
some prime makes the test fire. Neither of these two facts is proved here,
and below the prime bound the test can still be silent.

**In the layer** (`glm_universal.reasoning.symbolic_nonlinear`). For an
irreducible factor with real roots, the conjugation certificate is tried
first, as before. When it does not apply, the Frobenius test is tried. When
the test fires, column 2 carries for each root: *"no root of it is
expressible in radicals: irreducible over the rationals, of prime degree 5;
modulo 2 it factors into irreducible factors of degrees 2, 3, so by
Dedekind's theorem its Galois group holds an element of that cycle type; its
square moves some roots and fixes 2 of them, and in a solvable group of prime
degree only the identity fixes two roots, so the group is not solvable
(GLM.FrobeniusRadicals.no_radical_root_of_frobenius_shape; Dedekind's theorem
is not checked in Lean)"*.

**In the letter search.** When no specialised point passes the conjugation
certificate, the same points are tried again with the Frobenius test, at most
100 points and primes below 100 at each. The first point that qualifies is
named in the refusal, whose code stays `NONLINEAR`. `x^7 + a*x = b` is now
refused with *"no formula in radicals of a, b exists: at a = 1, b = 1 the
equation is x^7 + x - 1 = 0, and no root of it is expressible in radicals …
modulo 13 it factors into irreducible factors of degrees 2, 5 …"*. The
quintic in letters keeps Phase 112's wording, because the conjugation pass
runs first.

## 2. The marks

| mark | declared | result |
|---|---|---|
| F1 | every case with a non-solvable group carries the Frobenius statement | met: 6 of 6 (`x^5 - x - 1`, `x^5 - x + 1`, `x^5 + 20x + 16` with group A5, `x^7 - 3x + 1`, `x^11 - x - 1`, and Trinks's `x^7 - 7x + 3` with group `PSL(2, 7)`) |
| F2 | no solvable control carries any radical-free statement | met: 5 of 5 |
| F3 | the declared limit, the sextic `x^6 - x - 1`, carries none: the test applies only to prime degree | met: 1 of 1 |
| F4 | the letter cases, all refused `NONLINEAR`: the septic trinomial with the Frobenius reason, the quintic in letters with Phase 112's, De Moivre's quintic with none | met: 3 of 3 |
| F5 | the soundness battery, solvable by construction: no certificate | met: 0 of 178 certified |
| F6 | the reach battery: at least 95 % certified, and every polynomial the conjugation certificate certifies is certified by Frobenius too | met: 200 of 200; 50 by conjugation, all 50 also by Frobenius |
| F7 | the modular reading: the distinct-degree reading equals the complete modular factorisation, and on every cycle type of degree 5, 7, 11 and 13 the shape test fires exactly off the affine shapes, with a power fixing at least two points and moving one | met: 2,561 of 2,561 (polynomial, prime) pairs; 179 of 179 cycle types |
| F8 | the Lean file holds every named theorem and no `sorry` | met |
| F9 | Phase 112's report still meets 7 of 7 | met |

The solvable controls of F2 are `x^5 - 5x + 12` (dihedral), `x^5 + 15x + 12`
(the Frobenius group of order 20), the quintic with roots `2 cos(2πk/11)`
(cyclic, five real roots), and `x^5 - 2` and `x^7 - 2`, which the layer
answers by radicals anyway. The soundness battery of F5 is De Moivre's quintic
`x^5 - 5a x^3 + 5a^2 x - b` at every integer point with `a` between -4 and 4
and `b` between -8 and 8 (zero excluded), and the pure powers `x^5 - c` and
`x^7 - c` for `c` from 2 to 30, counting only the irreducible ones.

**Why F2 and F5 are a real test.** The conclusion is a theorem, so a
certificate on a solvable polynomial would be a bug in the code, not a
borderline case: either the modular reading was wrong, or the shape test let
through an affine shape. F7 checks both readings separately, and F5 checks
them together on polynomials built to have solvable groups.

**What the marks say, in one paragraph.** Yes. The layer now factors an irreducible polynomial of prime degree modulo small primes, and when one factorisation has a cycle shape that no affine map `x ↦ ax + b` has, it states that no root is expressible in radicals, citing Galois's theorem on groups of prime degree, proved in Lean. All nine marks were met: the statement now reaches `x^5 - x - 1`, the A5 quintic `x^5 + 20x + 16`, Trinks's septic with group `PSL(2, 7)` and the septic trinomial in letters, it is given to none of 178 polynomials with solvable groups, and it reaches all 200 random irreducible quintics and septics. Dedekind's theorem, which turns the factorisation into a group element, is used but not proved in Lean, and composite degrees are still out of reach.

**Phase 112's marks, narrowed.** The new certificate reaches two of Phase
112's R3 controls (`x^5 - x - 1`, `x^7 - 3x + 1`) and its R4 case that had to
carry no reason (`x^7 + a*x = b`). Those marks were about the conjugation
certificate, so `runtime/quintic_radical_report.py` now reads that
certificate by its own words: *"with exactly two non-real roots"* for R2 and
R3, and its Lean citation `quintic_in_letters_no_radical_formula` for R4. The
readings are otherwise unchanged, and the report still meets 7 of 7.

## 3. What is proved

`RequestProject/GLM/FrobeniusRadicals.lean`, namespace
`GLM.FrobeniusRadicals`, no `sorry`, standard axioms only.

§1, group theory:

* `exists_pow_cycleType_singleton`: a permutation with exactly one cycle of
  prime length `ℓ`, whose other cycle lengths are all prime to `ℓ`, has a
  power that is a single `ℓ`-cycle;
* `not_solvable_of_alternating_le`: a permutation group on at least five
  letters containing the alternating group is not solvable. The proof embeds
  five letters and writes a 3-cycle as the conjugate of a commutator by even
  permutations, so the 3-cycle lies in every term of the derived series.

§2, Jordan's theorem for a Galois group (the first step of the round):

* `card_complex_roots`: an irreducible polynomial over `ℚ` has as many complex
  roots as its degree;
* `not_solvable_of_swap_or_three_cycle`,
  `no_radical_root_of_swap_or_three_cycle`, `no_radical_root_of_cycle_pattern`:
  a transposition or a 3-cycle in the Galois group of an irreducible
  polynomial over `ℚ` of prime degree at least 5 rules out roots in radicals.
  They rest on Mathlib's Jordan theorems
  (`subgroup_eq_top_of_isPreprimitive_of_isSwap_mem`,
  `alternatingGroup_le_of_isPreprimitive_of_isThreeCycle_mem`) and on the
  transitivity of the Galois action (`galAction_isPretransitive`).

§3, Galois's theorem and the certificate the layer cites:

* `eq_one_of_two_fixed_of_solvable`: in a solvable transitive permutation
  group of prime degree, an element fixing two distinct points is the
  identity. The last nontrivial term of the derived series is an abelian
  normal subgroup. Its orbits are blocks, and the group is primitive because
  its degree is prime, so the subgroup is transitive. Being abelian, it then
  acts freely, so it has prime order and any of its non-identity elements
  generates it. An element fixing two points commutes with the subgroup
  element that carries one of those points to the other, hence with the whole
  subgroup, hence it fixes every point;
* `NotAffineShape`, the shapes the layer accepts, and `exists_pow_two_fixed`:
  a permutation of that shape has a power that is not the identity and fixes
  two points;
* `no_radical_root_of_frobenius_shape`, **the certificate**: if the Galois
  group of an irreducible polynomial over `ℚ` of prime degree holds an
  element of non-affine shape, no root is solvable by radicals.

**What the proof does not cover.** Dedekind's theorem, that the factor
degrees modulo an unramified prime are the cycle type of a Frobenius element,
is not proved in this project; Mathlib at this version does not state it in
this form. The factorisation modulo `q` and the irreducibility are decided by
the Python side and not checked in Lean. The theorem certifies the inference
from "the group holds an element of this cycle type" to "no root is solvable
by radicals". The converse half of Galois's theorem and Chebotarev's theorem,
which make the test complete in the limit, are not proved either. Nothing in
the layer depends on them: they only explain why silence is expected to be
rare.

## 4. Limits, and what the round leaves

* **Composite degree.** The test applies only to prime degree, where
  transitivity gives primitivity. A sextic or an octic with no root in
  radicals is still silent; the declared case is `x^6 - x - 1`. For composite
  degree the layer would need a test for primitivity, or a resolvent.
  *Taken by Phase 114* for groups holding an `(n - 1, 1)` element and a
  transposition or 3-cycle power, which reaches `x^6 - x - 1`
  ([`PRIMITIVE_RADICAL_STUDY.md`](PRIMITIVE_RADICAL_STUDY.md)); mark F3 now
  reads this study's own citation (`no_radical_root_of_frobenius_shape`).
* **No positive statement.** When the test is silent, nothing is said. It
  never claims a root *is* expressible in radicals: a Frobenius search cannot
  prove a group solvable. The resolvent sextic would decide solvability of a
  quintic exactly.
* **The prime bound.** Primes below 1000, and below 100 in the letter search.
  A non-solvable group whose non-affine classes are rare could need a larger
  prime. None did on the reach battery: every polynomial was certified.
* **Dedekind in Lean.** Proving Dedekind's theorem would close the gap
  between the factorisation and the group element.
* **The modes path.** Phase 109's `modes.higher` route names the roots of a
  characteristic polynomial of degree 5 or more through its coefficients and
  carries neither certificate. Its roots are all real, so only the Frobenius
  certificate could apply there. *Taken by Phase 114*: the route now carries
  the composite-degree certificate, and the chain pendulums of five and six
  links carry the reason.

## 5. Re-running it

From ``:

* `PYTHONPATH=. python3 -m glm_universal.tools frobenius-radical` runs every
  mark in about 20 s. `--quick` skips the batteries and the Phase 112
  regression, and `--json` gives the rows.
* `PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_frobenius_radical.py`
  runs the tests in about 10 s.
* `lake build RequestProject.GLM.FrobeniusRadicals` from the repository root
  builds the Lean file.
