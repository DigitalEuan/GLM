# Geometric ambiguity as computation

*What happens when the six-fold Golay tie is carried instead of broken, and
what happens when the emitted alphabet is widened.*

This study answers the "wobble / wiggle / noise" part of `ToDo_01.txt` — the
four concepts for making the trajectory's geometry the computation itself, and
the *Directive 2* engineering brief on parallel hypotheses and conceptual
superposition. Every number below is recomputed by code in this repository,
and the load-bearing statements are machine-checked in Lean 4 under
`RequestProject/GLM/`.

Two of the brief's proposals came out differently from how they were posed,
and those are the interesting results:

* **XOR bundling of a complete tie is not a way of carrying information — it
  is a constant.** The directive lists `F₂` symmetric difference and exact
  rational addition side by side under `COMPUTING_IN_SUPERPOSITION_METHOD`.
  For a complete six-fold tie the first destroys the read entirely and the
  second preserves it exactly.
* **Widening the emitted alphabet by *scaling* codewords does not widen what
  the carrier can reach.** What widens it is admitting new *supports* — which
  is what the Leech lattice provides, and what scaled codewords do not.

---

## 1. The tie is exactly six, and it is a sextet

The directive fixes `GOLAY_COVERING_RADIUS_TIE_COUNT = 6`. That constant is now
a theorem about the code the substrate actually uses — the systematic
`[24, 12, 8]` extended binary Golay code with the symmetric parity block `B` of
`overlay/glm_universal/substrate/mog.py`, transcribed into
`RequestProject/GLM/Golay/Code.lean` with the same syndrome convention (spot
checks agree with `GOLAY.syndrome_int` word for word).

A word is its support, a `Finset (Fin 24)`; symmetric difference is addition;
the code is the kernel of `syn s = ∑ k ∈ s, col k`. On that base, five finite
computations settle everything specific to this `B`:

| check | statement | size |
|---|---|---|
| 1 | distinct words of weight ≤ 3 have distinct syndromes | 2,325 |
| 2 | every syndrome realised by a tetrad is realised by exactly **six** | 10,626 |
| 3 | no tetrad shares a syndrome with a word of weight ≤ 3 | 10,626 × 2,325 |
| 4 | two distinct tetrads with the same syndrome are **disjoint** | 10,626² |
| 5 | words of weight ≤ 4 realise all 4,096 syndromes | 12,951 |

Everything else is coset algebra on top of them (`Golay/Sextet.lean`):

* `golay_min_weight` / `golay_min_distance_eight` — **minimum distance 8**.
  Checks 1 and 3 alone force it: a nonzero codeword of weight ≤ 6 splits into
  two halves of weight ≤ 3 with equal syndromes, and one of weight 7 splits
  into a `3` and a `4` with equal syndromes. Both are excluded. Weight 8 is
  attained, because two distinct tetrads of one sextet differ by an octad.
* `unique_nearest_of_le_three` — inside the packing radius the nearest codeword
  is unique: there is nothing to carry forward.
* `covering_radius_le_four`, `covering_radius_eq_four` — every word is within
  distance 4 of the code, and a tetrad is at exactly 4.
* **`ties_card_eq_six`** — a word at distance 4 has exactly six nearest
  codewords. The constant, proved.
* **`sextet_partition`** — the six error patterns are pairwise disjoint tetrads
  whose union is all 24 coordinates: the six tetrads of a MOG sextet.
* `ties_pairwise_hdist_eight` — the six candidates are mutually at distance 8,
  the minimum distance: the hypothesis space is as spread out as the code
  allows.

## 2. The two bundling rules are not interchangeable

Write `v` for the received word and `c₁ … c₆` for the six candidates, so
`cᵢ = v ⊕ uᵢ` with `u₁ … u₆` the sextet.

**XOR bundling is a constant.** Six copies of `v` cancel in characteristic two
and the six tetrads partition the coordinates, so

> `c₁ ⊕ ⋯ ⊕ c₆ = 𝟙` — the all-ones word — **for every received word `v`**.

Lean: `bundleF2_eq_one`, with `bundleF2_constant` for the consequence. In the
package: `bundle_f2` returns `0xFFFFFF = 16777215` on every one of the 256
weight-4 words the report checks, so it distinguishes **1** of them.

**Rational bundling is faithful.** At any coordinate exactly one of the six
error tetrads is present, so five candidates agree with `v` there and one
disagrees:

> `bundleᵢ = (1 + 4·vᵢ)/6 ∈ {1/6, 5/6}`, and `vᵢ = (6·bundleᵢ − 1)/4`.

Lean: `bundleQ_eq`, `bundleQ_recover`, `bundleQ_injective`. In the package:
`bundle_rational` and `recover_from_bundle`, which recovers the received word
on every word checked and distinguishes all 256.

**What this means for the directive.** "VSA bundling (rational vector addition
and `F₂` symmetric difference)" should be read as *rational addition*. `F₂`
bundling is safe only on a *partial* list — the moment the list is complete it
is the all-ones word and the read is gone. This is not a numerical accident of
the code; it follows from the sextet partition, which is why it is stated as a
theorem rather than measured.

## 3. Collapse is a measurement, not a coin flip

`collapse(superposition, context)` filters the hypothesis space by a downstream
predicate — a dimensional check, a stoichiometric balance, a lexicon
constraint — and reports one of three outcomes:

* `collapsed` — exactly one candidate survives; the context did the work no
  tie-break rule could do honestly;
* `superposed` — several survive; the machine stays uncommitted;
* `refuted` — none survive; **that is information**, not a failure: the context
  and the read are incompatible.

No tie is ever broken by enumeration order, which was the defect the complete
decoder was written to retire.

## 4. The wiggle really does compute

Concept 3 asked whether a carrier's long-term trajectory distribution can do
geometric work that a static algorithm would otherwise do by search. In the one
place where the geometry is fully pinned down, it can:

> A carrier that visits the six candidates in a cycle reads back, at every
> completed cycle, **exactly** the rational bundle — and that reading
> determines the received word uniquely.

Lean: `sextet_cycle_avgVec`, `sextet_cycle_determines` (`Wobble.lean`);
package: `sextet_cycle_reading`. Set against the alternative:

> a single chosen codeword is the nearest codeword of **10,626** different
> words at the covering radius (`single_candidate_card`).

So snapping discards a factor of 10,626; wiggling discards nothing. The motion
is the record.

## 5. How often the tie happens: the coset census

Sections 1–4 describe the *shape* of the ambiguity. This one counts it, and
the count is the reason the ambiguity matters. Every 24-bit word lies in one
of the 4,096 cosets of the code, and a coset's weight is the distance from any
of its words to the nearest codeword (`cosetWt_eq_dist`). The census is exact
(`Golay/Census.lean`, `coset_census`; package:
`superposition.coset_weight_distribution`):

| distance to the code | 0 | 1 | 2 | 3 | 4 | total |
|---|---|---|---|---|---|---|
| cosets | 1 | 24 | 276 | 2,024 | **1,771** | 4,096 |

The first four columns are `C(24, w)` — below the packing radius a word *is*
its own error pattern — and the last is `C(24, 4) / 6 = 10626 / 6`, the tetrads
counted six to a sextet. So (`unique_vs_ambiguous`)

> **2,325** of the 4,096 cosets are read uniquely and **1,771** are six-fold
> ties: `1771/4096 ≈ 43%` of all inputs.

and the mean distance to the code is exactly

> `13732 / 4096 = 3433 / 1024 ≈ 3.352`   (`mean_coset_weight`).

Say plainly what that number means. The packing radius of the code is 3 and
its covering radius is 4; `3 < 3433/1024 < 4` (`mean_coset_weight_gt_three`,
`mean_coset_weight_lt_four`). **The average word already sits past the radius
inside which the reading is unique.** Ambiguity is not a corner case for this
code that a decoder meets occasionally at the extremes — it is the typical
case, and a machine that always reports a single nearest codeword is
suppressing a live alternative on nearly half of everything it reads. That is
the quantitative reason `superpose` and `collapse` exist at all.

The package recomputes every figure above rather than quoting it:
`coset_census_report()` builds the distribution from the decoder's own coset
table, forms the mean in exact `Fraction` arithmetic, and checks both against
the Lean values (`census_agrees_with_lean`, `mean_agrees_with_lean`, both
`True`). It is the fourth block of `report superposition`.

## 6. Does it *settle* there? The dynamical half, answered

The census is a statement about a distribution. The self-organised-criticality
reading of it is a statement about a *process*: that a carrier which is
repeatedly perturbed — and corrected — drifts to the critical boundary and
stays there. The two are not the same claim, and the second one is false in
both of its strong readings. `Golay/Dynamics.lean` makes the process explicit
and settles it; `superposition.coset_chain_report()` recomputes the whole thing
in exact integer/rational arithmetic, with no sampling and no float.

The process. A one-bit perturbation of coordinate `k` adds the parity-check
column `col k` to the carrier's syndrome, so "flip a uniformly chosen
coordinate" is the random walk on the 4,096 cosets generated by the 24
columns, and `step` pushes a law forward.

**The stationary law is the census.** The uniform law is stationary
(`step_unif`), and it is the *only* stationary law (`stationary_unique`: a
maximiser's neighbours are maximisers, and the columns generate every
syndrome). Under it the expected distance to the code is exactly `3433/1024`
(`expect_unif_cosetWt`) and the carrier is at distance 3 or 4 with probability
`3795/4096 ≈ 92.6%` (`prob_unif_critical_band`). So the *averaged* form of the
criticality claim is true, and it is precisely the census.

**But the chain has no limiting law.** Every parity-check column has odd
parity (`par_col`), so the walk alternates between the two 2,048-element
parity classes: after `n` ticks the law is supported on one class and vanishes
on the other, and is therefore never uniform, from any starting point
(`iterate_dirac_ne_unif`). The package sees exactly this: from a point mass
the supports run `24, 277, 2048, 2048, …` and the parity class alternates
`1, 0, 1, 0, …`. "Converges to the critical distribution" is false as stated.

**And it does not concentrate.** Even under the stationary law the carrier is
at distance `≤ 2` with probability `301/4096 > 0`
(`prob_unif_subcritical_pos`). The weight fluctuates for ever; it does not
lock on to a critical value. What settles is the *time average*: after twelve
exact ticks the two-step average distance is `76017479/22674816`, within
`5819/181398528 ≈ 3.2 × 10⁻⁵` of `3433/1024`.

**With correction, criticality disappears altogether.** A one-bit error on a
codeword is corrected back to *that* codeword and to nothing else
(`perturb_correct_returns`, using `unique_nearest_of_le_three`), so a carrier
that is corrected after every perturbation sits on the code for ever at
distance 0 — the opposite of drifting to the boundary. The report checks this
on every coordinate of a sample of codewords: distance before correction is
always 1, after correction always 0.

**The time averages do converge, and the proof is now machine-checked.** The
positive limiting statement in its correct Cesàro form — that
`(1/N) ∑_{n<N} step^n μ` converges to the uniform law — was recorded as open at
the end of `Golay/Dynamics.lean` in the previous round, with the exact
obstruction written down: a Lean proof needs a quantitative mixing argument,
and Mathlib supplies none for a finite kernel of this shape. `Golay/Cesaro.lean`
supplies one, by exact Fourier analysis over `ℚ` on the syndrome group
`(ZMod 2)¹²`, and gets an explicit rate rather than a bare limit:

> `cesaro_converges` — for every probability law `μ`, every syndrome `f` and
> every `N ≥ 1`, `|cesaro μ N f − 1/4096| ≤ 24 / N`.

The chain is a convolution on `Syn = (ZMod 2)¹²`, so the group's characters
diagonalise it, and over `ZMod 2` those characters take the values `±1` and
therefore live in `ℚ` — the whole proof is exact rational arithmetic, with no
limit of real numbers taken anywhere. The eigenvalue at a syndrome `s` is
`lam s = (1/24) ∑_k χ_s(col k)`, and four facts about it finish the argument:
`lam 0 = 1`, which is why the limit is `1/4096` and not `0`; `lam s ≤ 11/12`
for `s ≠ 0`, because some column must fail to be orthogonal to `s` and one
`−1` among twenty-four terms is enough, so the spectral gap is at least
`1/12`; `|lam s| ≤ 1`, attained as `−1` at the all-ones syndrome, which *is*
the periodicity and is why the average and not the iterate converges; and
hence `|∑_{n<N} lam sⁿ| ≤ 2/(1/12) = 24`, which is the 24 in the headline
bound. Reading the same statement as an ordinary limit is `cesaro_tendsto`.

Nothing in the negative results of §6 changes: the iterates themselves still
have no limit, which is precisely why the time-averaged statement is the right
one. The measured two-step averages above are now a check on a theorem rather
than evidence for a conjecture.

## 7. The hull: scale changes nothing, support changes everything

Concept 1 proposed widening the emitted alphabet — "Leech lattice points or
scaled codewords" — to broaden the convex hull the carrier can wiggle through.
`Reachable.lean` already showed the hull is the whole story: a single linear
functional certifies a target as unreachable. `HullExpansion.lean` adds the
converse and then tests the proposal.

**The converse** (`cycle_avgVec_eq`): any finite cycle of emitted states is read
back *exactly* as the mean of the cycle. With `avgVec_mem_hull` and
`not_tendsto_avg_of_separating` this pins the reachable set as precisely the
convex hull of the alphabet — no more and no less.

**Scaling fails.** Take the target `½·e₀`: half a unit on coordinate 0, nothing
elsewhere. The functional

> `f(x) = 7·x₀ − ∑_{j≠0} xⱼ`

is `≤ 0` on every codeword — if `0 ∉ c` it is `−|c| ≤ 0`, and if `0 ∈ c` it is
`8 − |c| ≤ 0` because the minimum weight is 8 — hence `≤ 0` on every
non-negative multiple `λ·c`, while `f(½·e₀) = 7/2 > 0`. So no carrier emitting
scaled codewords ever reads that target (`concTarget_not_mem_hull_scaled`,
`concTarget_unreachable_scaled`). The obstruction is not size but **support**: a
codeword through coordinate 0 drags at least seven other coordinates with it,
and scaling cannot separate them. The package checks the functional against all
4,096 codewords in exact arithmetic; the maximum is exactly 0.

**New supports work.** The minimal Leech vectors of shape `(±4², 0²²)` — in the
`×√8` integer model the substrate uses — have support 2, a support no nonzero
codeword has. Admitting `4e₀ + 4e₁` and `4e₀ − 4e₁` puts the same target inside
reach, and the witness is explicit: a 16-tick cycle, one tick on each Leech
point and fourteen at the origin, whose reading is exactly `½·e₀`
(`concTarget_reached_by_leech`, `alphabet_expansion_strictly_helps`).

The engineering conclusion is sharper than the proposal: **widen the set of
supports the quantiser may emit, not the scale.**

## 8. What this does not settle

Stated plainly, because the brief asks for four things and this study now
settles three of them and takes the fourth as far as a finite model goes:

* **The VOA state-field map `Y(u,z)` (concept 4) is built at the Griess layer,
  and no further.** `VOA.lean` constructs the map on the 3-dimensional `2A`
  subalgebra — `mode u 1 v = u ⋆ v`, truncated, skew-symmetric, with an
  invariant form that invariance itself forces, self-adjoint modes, a
  nondegenerate pairing and the vacuum `(4/5)(e₀ + e₁ + e₂)`. It then proves
  the obstruction rather than asserting it: Borcherds' commutator formula at
  `m = n = 1` would require `u ⋆ (v ⋆ w) − v ⋆ (u ⋆ w) = (u ⋆ v) ⋆ w`, and on
  the axis triple the two sides are `(−3/32) e₀ + (3/32) e₁` and
  `(−3/32) e₂` (`borcherds_commutator_fails`). The modes the truncation
  discards are load-bearing, so the infinite-dimensional half of the bridge is
  necessary — and it is not built.
* **Self-organised criticality (concept 2) is now answered, and the answer is
  mostly negative** — see sections 5 and 6. The static half is the census:
  the mean distance to the code is `3433/1024`, past the packing radius, so
  ambiguity is the typical case. The dynamical half fails in both strong
  readings: the perturbation chain has no limiting law (it is periodic), its
  stationary law does not concentrate at the critical weight, and under
  correction the carrier returns to the code rather than drifting to the
  boundary. What survives is the time-averaged statement, and that is no
  longer a gap: `Golay/Cesaro.lean` proves Cesàro convergence with the rate
  `24/N` (see §6). What remains unproved is the original claim that *tuning a
  noise floor to that boundary makes the visit frequencies compute
  multi-variable probabilities*; what is proved is the special case where the
  six are visited equally often, and there the distribution is a faithful
  encoding of the input rather than a probability estimate.
* **Niemeier classification by trajectory distribution (concept 3)** is
  partly addressed and not settled. `reasoning/voronoi_walk.py` and
  `reasoning/deep_holes.py` now reach a deep hole by *walking* to it and
  climbing to the covering radius, so the Niemeier type is derived rather than
  looked up among 196,560 facets, and `report deep holes` recomputes it. The
  full census over the 23 Niemeier lattices is still outstanding, and so is
  the claim that a *trajectory distribution* classifies them: the result in
  this study is about the Golay sextet.

Several items this section previously listed as outstanding have since been
built, and are named here so the list is not read as current: the FWHT wiring
(`reasoning/fwht_decode.py`, `report transform decoder`), arithmetic inside a
description (`reasoning/term_arithmetic.py`), the molecules domain
(`data_objects/molecules.py`, 51 species, `report molecules`), the sparse
chemistry attributes (`reasoning/element_coverage.py`, `report chemistry
coverage`) and the unit strings including the priced steradian
(`reasoning/units.py`, `report units`). Multi-domain analogy is now *refused
with a stated reason* rather than answered wrongly, which is progress but not
an answer — see [`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md). The `O(1)`
LLVQ table remains unbuilt. The current list of what is untouched is kept in
one place, `MASTER_PLAN_ARCHIVE.md` §7.9, and mirrored in `STATUS.md`.

## 9. Re-running it

```bash
# the machine-checked development (no sorry)
lake build

# the package study, recomputed
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_superposition.py -q
PYTHONPATH=. python3 GLM.py -q "report superposition" -c 1
PYTHONPATH=. python3 GLM.py -q "report superposition" --verify-tct
```

The last command regenerates the whole study in a fresh interpreter from the
column-3 script and checks it key by key against what the session reported.

## 10. Where the statements live

| claim | Lean | package |
|---|---|---|
| six equidistant codewords | `Golay/Sextet.lean` `ties_card_eq_six` | `superpose`, `sextet_partition_report` |
| the six are a sextet partition | `sextet_partition` | `sextet_partition_report` |
| minimum distance 8, radii 3 and 4 | `golay_min_distance_eight`, `covering_radius_eq_four` | `golay_decode.coset_census` |
| XOR bundling is constant | `Superposition.lean` `bundleF2_eq_one` | `bundle_f2`, `bundling_report` |
| rational bundling is faithful | `bundleQ_eq`, `bundleQ_injective` | `bundle_rational`, `recover_from_bundle` |
| one candidate is 10,626-fold ambiguous | `single_candidate_card` | `bundling_report` |
| a cycle reads back the bundle | `Wobble.lean` `sextet_cycle_avgVec` | `sextet_cycle_reading` |
| a cycle is read back exactly | `HullExpansion.lean` `cycle_avgVec_eq` | — |
| scaling does not broaden the hull | `concTarget_unreachable_scaled` | `alphabet_expansion_report` |
| new supports do | `concTarget_reached_by_leech` | `alphabet_expansion_report` |
| the coset census | `Golay/Census.lean` `coset_census`, `unique_vs_ambiguous` | `coset_weight_distribution`, `coset_census_report` |
| mean distance `3433/1024`, past the packing radius | `mean_coset_weight`, `mean_coset_weight_gt_three` | `mean_coset_weight` |
| the uniform law is the unique stationary law | `Golay/Dynamics.lean` `step_unif`, `stationary_unique` | `coset_chain_report` |
| the chain has no limiting law (period 2) | `par_col`, `iterate_dirac_ne_unif` | `coset_chain_report` |
| it does not concentrate at the critical weight | `prob_unif_subcritical_pos` | `coset_chain_report` |
| correction returns the carrier to the code | `perturb_correct_returns` | `coset_chain_report` |
