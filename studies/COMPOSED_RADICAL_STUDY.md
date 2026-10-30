# Roots with no expression in radicals, through a composition

## Tier 0 — the coarse read

**Question.** Phase 114's certificates need a primitive Galois group, so `solve symbolically` says nothing about `x^10 - x^2 - 1`, whose group is not solvable but has blocks. Can the layer find such a polynomial's decomposition `g(h(x))` exactly, certify the outer polynomial instead, and still never certify a polynomial whose group is solvable?

**Verdict.** Yes, whenever the outer polynomial has degree five or more and one of the earlier certificates reaches it. A root `x` in radicals would make `h(x)`, a root of `g`, one too, and that step is proved in Lean, together with a fully proved instance, `x^10 - 4x^2 + 2`. All eight marks were met: the statement reaches the five declared compositions, including Phase 114's silent `x^10 - x^2 - 1`, and all 120 random irreducible compositions of the reach battery; it is given to none of 201 polynomials with solvable groups; and every one of 180 built compositions is decomposed exactly. Dedekind's theorem is still used, not proved, wherever the outer certificate reads Frobenius elements.

**Deciding figure.** 8 of 8 marks met; 5 of 5 compositions certified; 6 of 6 solvable controls silent; 2 of 2 letter questions with the declared reason; 0 of 201 solvable polynomials certified; 120 of 120 random irreducible compositions certified; 180 of 180 decompositions exact; 3 theorems, 0 `sorry`; Phase 114 still 10 of 10 and Phase 112 still 7 of 7.

**Recomputed by.** `glm_universal.runtime.composed_radical_report.composed_radical_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`PRIMITIVE_RADICAL_STUDY.md`](PRIMITIVE_RADICAL_STUDY.md) §4 left, first
among its limits, the imprimitive groups that are not solvable. The declared
case was `x^10 - x^2 - 1`: its roots come in pairs `{r, -r}`, an element that
fixes one root fixes its pair, so no element of cycle type `(9, 1)` exists and
Phase 114's test is silent, as its mark P3 required. That study named the next
step: such a polynomial is a composition `g(h(x))`, here `g = y^5 - y - 1`
and `h = x^2`, so find the decomposition and certify `g`. The line was carried
in `STATUS.md` §2.2 as "Radicals, the rest".

**Order of work, stated plainly.** The Lean file was written first. The cases
and marks (`glm_universal/evaluation/composed_radical_cases.py`) were then
written and committed **before the decomposition was written or tried**; the
commit that holds them precedes the commit that holds the code. The
irreducibility of each declared polynomial was checked beforehand with the
existing factoring, which this round does not change. The declared values are
otherwise classical: `y^5 - y - 1`, `y^5 - 4y + 2` and `y^6 - y - 1` have the
full symmetric group (Phases 112 to 114 certify them); `y^5 - 5y + 12`
(dihedral of order 10), `y^5 + 15y + 12` (the Frobenius group of order 20),
the real quintic of the eleventh roots of unity (cyclic) and the pure powers
`y^5 - c` have solvable groups; and a composition of polynomials with
solvable groups has a solvable group, since it lies in a wreath product of
the two.

## 1. What was added

**The decomposition** (`reasoning/symbolic_factor.py`, new functions
`compose`, `decompose`, `decompositions`). For a polynomial `f` of degree
`n` and each proper divisor `s` of `n`, `decompose(f, s)` looks for `f =
g(h(x))` with `h` monic of degree `s` and `h(0) = 0`; over the rationals that
`h` is unique when it exists. `h^r` (`r = n / s`) must agree with `f / lc(f)`
in its top `s` coefficients, and that fixes the coefficients of `h` one at a
time from the top, each by one division by `r`. `g` is then the `h`-adic
expansion of `f`: divide by `h` repeatedly, and every remainder must be a
constant, or there is no decomposition with that inner degree. Exact
arithmetic throughout, and the answer is recomposed and compared with `f`
before it is returned, so a decomposition returned is a decomposition.

**The certificate** (`radical_free_composed`). For an irreducible `f` of
composite degree at least 10, every decomposition with an outer polynomial of
degree at least 5 is tried, the inner degree smallest first. `g` is
irreducible because `f` is (a factorisation `g = g_1 g_2` would give `f =
g_1(h) g_2(h)`), and it is certified by Phase 112's complex-conjugation test
or by the Frobenius certificates of Phases 113 and 114 — and, recursively, by
a further composition. The statement nests the outer polynomial's reason:

> no root of it is expressible in radicals: it is g(h(x)) with g(y) = y^5 -
> y - 1 and h(x) = x^2, and no root of g is expressible in radicals
> (irreducible over the rationals, of prime degree 5; modulo 2 it factors
> into irreducible factors of degrees 2, 3, …); a root x in radicals would
> make h(x), a root of g, one too
> (GLM.ComposedRadicals.no_radical_root_of_comp)

**Where it is wired.** `radical_free_galois` tries it after Phase 114's
certificate in composite degree, so the branch layer of `symbolic_nonlinear`,
its letter search and the `modes.higher` route (through
`certify_numeric_any`) all carry it with no change of their own; where an
earlier certificate applies, its wording is unchanged. Report
`runtime/composed_radical_report.py`, CLI `tools composed-radical`, tests
`tests/test_composed_radical.py` (16).

## 2. The marks

| mark | declared | result |
|---|---|---|
| C1 | every declared composition with a non-solvable outer polynomial is answered and carries the composition statement | met: 5 of 5 |
| C2 | no solvable control carries any radical-free statement | met: 6 of 6 |
| C3 | `x^10 + a*x^2 = b` refused `NONLINEAR` with the composition reason; `x^10 + a*x^5 = b` with no radical-free reason | met: 2 of 2 |
| C4 | the soundness battery (solvable quintics composed with random inner polynomials, and Phase 114's own battery): no certificate | met: 0 of 201 certified |
| C5 | the reach battery, random irreducible compositions with outer degree 5, 6 or 7 and inner degree 2 or 3: at least 95 % certified | met: 120 of 120 (24 of each shape) |
| C6 | every built composition is decomposed at its inner degree, and the decomposition recomposes exactly | met: 180 of 180 |
| C7 | the Lean file holds every named theorem and no `sorry` | met |
| C8 | Phase 114's report still meets 10 of 10 (its P3 narrowed) and Phase 112's 7 of 7 | met |

The five compositions of C1 are `x^10 - x^2 - 1`, `x^10 - 4x^2 + 2` (the Lean
instance), `x^15 - x^3 - 1`, `x^12 - x^2 - 1` (outer `y^6 - y - 1`, certified
by Phase 114) and `(x^2 + x)^5 - (x^2 + x) - 1` expanded, an inner
polynomial that is not a power. The solvable controls of C2 are Phase 114's
three compositions with a cubic or a quartic, `x^10 - 5x^2 + 12` (outer
dihedral; refused for having no real root, as before), `x^10 - 2`, and `(x^2
+ x)^5 - 2` expanded.

**Why C2 and C4 are a real test.** The conclusion is a theorem, so a
certificate on a solvable polynomial would be a bug — a wrong decomposition
or a wrong outer certificate — and C6 checks the decomposition alone. The
compositions of C4 have outer polynomials of degree 5 with solvable groups,
the case in which the decomposition succeeds and the outer certificate must
refuse.

**What the marks say, in one paragraph.** Yes, whenever the outer polynomial has degree five or more and one of the earlier certificates reaches it. A root `x` in radicals would make `h(x)`, a root of `g`, one too, and that step is proved in Lean, together with a fully proved instance, `x^10 - 4x^2 + 2`. All eight marks were met: the statement reaches the five declared compositions, including Phase 114's silent `x^10 - x^2 - 1`, and all 120 random irreducible compositions of the reach battery; it is given to none of 201 polynomials with solvable groups; and every one of 180 built compositions is decomposed exactly. Dedekind's theorem is still used, not proved, wherever the outer certificate reads Frobenius elements.

**Phase 114's mark P3, narrowed.** P3 declared `x^10 - x^2 - 1` silent
because Phase 114's test needs a primitive group. This round's certificate
now answers it, as it should, so `runtime/primitive_radical_report.py` reads
P3 by Phase 114's own citation
(`GLM.PrimitiveRadicals.no_radical_root_of_primitive_pattern`) instead of by
any radical-free statement, the same narrowing Phase 114 gave Phase 113's F3.
The report still meets 10 of 10, and the unit test of the limit now checks
both halves: Phase 114's certificate silent, the composition certificate
present.

## 3. What is proved

`RequestProject/GLM/ComposedRadicals.lean`, no `sorry`, only the standard
axioms (`propext`, `Classical.choice`, `Quot.sound`, checked with
`#print axioms`):

* `no_radical_root_of_comp` — **the certificate the layer cites**: if no
  complex root of `g` is solvable by radicals over `ℚ`, no complex root of
  `g.comp h` is, for every `h : ℚ[X]`. The numbers solvable by radicals form
  a field over `ℚ` (Mathlib's `solvableByRad`), so `h(x)` lies in it with
  `x`;
* `no_radical_root_of_comp_X_pow` — the same for `g(x^k)`;
* `decic_no_radical_root` — no complex root of `x^10 - 4x^2 + 2` is solvable
  by radicals, from Phase 112's `x^5 - 4x + 2`
  (`GLM.QuinticRadicals.trinomial_no_radical_root`). This instance has no
  unproved step: neither Dedekind's theorem nor a Python decision.

What is not proved: the decomposition, which the Python side finds and
checks exactly; and, where the outer certificate reads Frobenius elements,
Dedekind's theorem, as in Phases 113 and 114.

## 4. Limits, and what the round leaves

* **Outer polynomials of degree below 5.** The certificate needs the outer
  polynomial to carry the non-solvability. When `g` has degree at most 4 and
  the obstruction sits in the inner polynomial (a candidate is `(x^5 - x -
  1)^2 - 2`, not examined this round), the layer is silent; reaching it
  would need the Galois group of `h(x) - y` over the field of a root `y` of
  `g`.
* **Imprimitive groups that are not compositions.** A polynomial can have an
  imprimitive group without being a composition over `ℚ` (the blocks are
  then defined over a larger field); the layer stays silent on those.
* **Primitive groups without a transposition or a 3-cycle**, **no positive
  statement**, and **Dedekind in Lean**, as Phase 114 left them.

## 5. Re-running it

From ``:

* `PYTHONPATH=. python3 -m glm_universal.tools composed-radical` runs every
  mark in about two minutes, most of it Phase 114's and Phase 112's reports
  for C8. `--quick` skips the batteries and the regressions, and `--json`
  gives the rows.
* `PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_composed_radical.py`
  runs the tests.
* `lake build RequestProject.GLM.ComposedRadicals` from the repository root
  builds the Lean file.
