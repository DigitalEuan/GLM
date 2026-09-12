# The deep-hole ladder — escalating the reading until the law descends

## Tier 0 — the coarse read

**Question.** The deep-hole round stopped because its statistic could not tell
the same hole from itself under a changed ensemble. Is that a property of the
hole, or of the layer it was read at — and does escalating the reading, in the
declared ladder below, cross the boundary?

**Verdict.** It was the layer. Escalating the reading takes the sanity count
from **3 of 10** at the first round's cell to **10 of 10** — the gate — at the
joint reading with 1920 starts, where the full query set comes out **40 of
44** against 12 for the vertex-count baseline. The passing cell is the
extension rung of §14, decided after the twelve pre-registered cells were
measured, and is reported as an extension throughout; the best pre-registered
cell is 9 of 10.

**Deciding figure.** The number of the ten reference holes that keep their own
label under a bare seed change: 3 of 10 at `(L₁, 240)`, 9 of 10 at
`(L₄, 960)`, 10 of 10 at `(L₄, 1920)`.

**Recomputed by.** `glm_universal.reasoning.deep_hole_escalation.deep_hole_escalation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the module that takes the measurement
exists — §§1–11 are as they were committed, and §12 is whatever came out.

It is the second round on one question, and it exists because the first round
[`DEEP_HOLE_STUDY.md`](DEEP_HOLE_STUDY.md) stopped at its own sanity check: the
arrival-share profile `S₁` of a hole, measured over a declared 240-start
ensemble, moved further when the ensemble seed changed than the profiles of
*different* hole types are apart. Three of ten holes kept their label. The
pre-registered decision tree stopped the round there, and the bit score was
reported and disqualified.

That was recorded as a failure of the method. This round asks whether it is
instead a **boundary of the layer the method read at** — the distinction
[`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md) exists to make, and
the one the retrieved framework in `RequestProject/GLM/Layers.lean` and
`RequestProject/GLM/Cumulative.lean` makes formal:

* a law descends to a layer exactly when the layer's indistinguishability is a
  **congruence** for it (`GLM.Info.Layer.descends_iff_congruent`);
* a layer whose capacity is smaller than the carrier space **must** conflate
  two carriers (`GLM.Info.Layer.exists_indist_of_capacity_lt`);
* a **cumulative** layer — one that carries the layer below it alongside its
  own reading — refines both of its parts (`GLM.Info.Layer.cumulative_refines_left`).

The law this round wants to descend is *"the hole's type is invariant under a
change of the declared ensemble"*. In the first round it did not descend to the
`S₁` layer. Two things were done to `S₁` that a cumulative reading would not
do, and they are the two candidate causes:

1. **The narrow view.** §2 of the first round says an emission further away
   than the minimum seen is a *stray*, and is "counted separately, reported,
   and **excluded from the profile**". The strays are the reading of the layer
   below — the coarse shape of the Voronoi cell around the centre — and they
   were discarded to make the profile commensurable. This is exactly the defect
   the information-loss audit found in the integer layer, which threw the
   substrate parity bits away and broke the cumulative guarantee.
2. **The capacity.** `N = 240` starts over 25 to 48 vertices is a fixed, small
   budget. The measured minimum separation between reference profiles was
   `2/39 ≈ 0.0513` and the measured seed shift exceeded it. A statistic whose
   resolution is coarser than the separation it must detect cannot detect it,
   however the classifier is written.

So this round escalates on both axes at once, in a ladder fixed here, and
reports the cell where the law first descends — or, if no cell reaches the
gate, reports the boundary and refuses the extrapolation. **Either outcome is
a result.** The first is a faculty; the second is a measured statement of how
much capacity the question needs and that this ladder does not have it.

---

## 1. What is used rather than re-derived

* The **frozen path** to a hole and its certification —
  `reasoning.deep_holes` — unchanged, and the same 14 centres the first round
  reached, in the same order, from the same declared walk seeds.
* The **reference table** rule of the first round: the first centre certified
  of a type is that type's reference centre.
* The exact **nearest-Leech-point decoder**
  `fwht_decode.nearest_lattice_point_fwht`, unchanged.
* The **census** as ground truth, from `reasoning.niemeier`, as an input.
* The four **controls** of the first round, unchanged in definition.

Nothing about the geometry is re-derived. What changes is the *reading*.

---

## 2. The ensemble, and why it is nested

The ensemble is the first round's, with one change fixed here: the starts are
**nested prefixes**. The declared sweep `fwht_decode._Sweep(s)` at a seed emits
starts in a fixed order, so the first 240 starts of a 960-start ensemble *are*
the 240-start ensemble. Escalating `N` therefore adds information and never
replaces it, which is what makes the ensemble axis of the ladder cumulative in
the same sense as the layer axis, and it means one 960-start run per
`(centre, seed)` supplies every cell.

**Start.** As in the first round: coordinate `Fraction(sweep.below(2001) - 1000, 4000)`,
start 0 the zero accumulator.
**Step.** One tick of the delta–sigma loop; the emitted point is the exact
nearest Leech point to `a + c`.
**Stop.** After exactly one tick, so every start contributes one emission.
**Record.** The emitted point *and* its exact raw squared distance to `c`. This
round keeps every emission, and no emission is excluded from any layer above
`L₁`.

**The ladder of sizes.** `N ∈ {240, 480, 960}`, in that order. 240 is the first
round's ensemble and is on the ladder so that the first round is reproduced as
its bottom rung rather than quoted.

**The exactness caution, restated.** The set of start offsets is `2001²⁴`
points and is not enumerable, so the ensemble is a *declared finite
deterministic sweep*, not a sample. There is no randomness and no float. A
different seed is a different declared ensemble, and the whole question of this
round is whether the reading survives changing it.

---

## 3. The ladder of layers

Four readings, each a map from the emission record to a profile, each with an
exact metric. `L₀` is not on the ladder: it is the cheap baseline, kept as a
control.

* **`L₀` — the vertex count.** One integer. The control that mattered in the
  first round.
* **`L₁` — arrival shares.** The first round's primary statistic `S₁`
  unchanged: the shares `a(v)/A` over non-stray arrivals, sorted descending,
  zero-padded to 48, compared by L1 on `ℚ⁴⁸`.
* **`L₂` — arrival shares, widened by the strays.** The pair
  `(shares, stray spectrum)` where the stray spectrum is the shares — over
  **all `N` emissions**, so that the stray fraction is retained rather than
  normalised away — of the emissions grouped by their distinct raw squared
  distances above the minimum, sorted descending and padded to 48. The distance
  is the **sum** of the two L1 distances. This is the cumulative repair of the
  narrow view: `d_{L₂} ≥ d_{L₁}` by construction, so `L₂` refines `L₁`.
* **`L₃` — the exact rational distance measure.** The measure `μ` on `ℚ` that
  puts mass `1/N` at the exact raw squared distance of each emission from the
  centre. The distance between two of these is the exact **1-Wasserstein**
  distance on the line, `∫|F_μ − F_ν|`, computed as a finite sum of
  `Fraction`s over the union of the two supports. This is the rational-layer
  reading: it uses the exact distance *values*, which the share layers see only
  as an ordering, and it is the reading least disturbed by which particular
  vertex a start happened to land on.
* **`L₄` — the joint reading.** `d_{L₄} = d_{L₂} + d_{L₃}`. Cumulative over
  both, and the top of this ladder.

`4 layers × 3 sizes = 12 cells`. The order of escalation is **layer first, then
size**: `(L₁,240)`, `(L₁,480)`, `(L₁,960)`, `(L₂,240)`, … , `(L₄,960)`, and
"the cheapest cell that passes" means the earliest in that order. Escalating
the reading is preferred to escalating the budget because it is what the
information-loss framework says the defect was; the budget axis is there to
show whether capacity alone would have done it.

---

## 4. The primary statistic, and the gate

**Primary — the sanity count `Q₀(cell)`.** For each of the `K` reference holes,
take its profile at the reference seed `20260825` as the reference `f_T`, take
the profile of the **same centre** under the sanity seed `20260826`, and ask
whether `f_T` is the strictly nearest reference to it under the cell's metric.
`Q₀` is the number of holes for which it is, out of `K`.

This is the statistic the first round failed at 3 of 10, and it is the one the
gate is on, because it is the weakest thing that has to be true: a reading that
cannot recognise a hole as itself cannot name a hole at all.

**The gate, fixed here: `Q₀ = K`.** Every reference hole keeps its own label
under a bare seed change. Nothing less passes — 9 of 10 is a fail, and is
reported as 9 of 10.

**The ratio, reported at every cell.** With
`W = max_T d(f_T, S(c_T, sanity seed))` the worst within-hole seed shift and
`B = min_{T≠U} d(f_T, f_U)` the reference separation, the cell's ratio is

```
ρ = 2W / B
```

`ρ < 1` is the classical separation condition, and it is *sufficient* for
`Q₀ = K` and for correct nearest-reference classification of anything within
`W` of a reference — that implication is the Lean half (§9), not an assumption.
`ρ` is scale-free, so it is comparable across layers whose metrics are not.
The first round's cell `(L₁, 240)` has a `ρ` and it will appear as the bottom
rung.

**Secondaries, named now so that they cannot be promoted later.**

* `S_a` — the same count over **all four transforms** of the first round
  (seed, translation, negation, permutation), not only the seed.
* `S_b` — the faithfulness radius, `max` over queries of the distance to the
  query's own reference, against the certified radius `r* = B/2`; the pair the
  first round found incompatible.
* `S_c` — the accuracy of the full 44-query set at the passing cell.
* `S_d` — the mean rank of a query's own reference.

None of these is the gate.

---

## 5. The multiplicity correction

`m = 16`: the 4 statistics the first round tried, plus the 12 cells of this
ladder. *(§14 adds an extension rung of 4 further cells after the fact, and
raises `m` to 20 accordingly — the correction counts every cell that was
looked at, whenever it was decided on.)* The correction is `log₂(m)` bits
subtracted from every bit score this round reports, whatever the outcome, and it is applied even to the bottom rung
that reproduces the first round.

```
B_bits = log2(1 / p_tail) − log2(16)
```

with `p_tail` the exact rational tail of the uniform labeller, as in the first
round, and `log2` an exact rational bracket. The gate on the bit score, where a
bit score is reported at all, stays the first round's **3 bits**.

---

## 6. The controls

Unchanged from the first round in definition, run at whichever cell the
decision tree lands on, on the same 44-query set:

* **N1 — the digest control (D3).** Profiles replaced by a digest of the hole's
  *name*. Must score at chance. *This control uses SHA-256, which is a declared
  site under D9 and the clearest case of D11: the experiment needs an operation
  that carries no meaning precisely because it must carry none.*
* **N2 — the seeded reshuffle** of the statistic-to-label pairing.
* **N3 — the plain vertex count**, `L₀`: the competitor that matters.
* **N4 — the uniform-profile ablation** on the same support size, which is N3
  expressed inside the method's own metric.

Chance is `1/K` per query, and the tail is an exact rational binomial sum.

---

## 7. The decision tree, fixed before the measurement

| outcome | reading | what happens next |
|---|---|---|
| some cell has `Q₀ = K` | the law descends at that cell: the boundary was the layer, not the hole | take the **cheapest** such cell in the §3 order; run the full query set and all four controls there; report `S_a`–`S_d`; claim the faculty only if it also beats N3 and clears 3 bits |
| no cell has `Q₀ = K`, but `Q₀` rises strictly along the ladder | the ladder is climbing towards the boundary and this budget does not reach it | report the boundary, the best cell, and the extrapolation **refused**: no claim about a cell that was not run |
| no cell has `Q₀ = K` and `Q₀` does not rise | the escalation thesis is refuted for this question: widening and enlarging the reading do not help, so the obstruction is not resolution | say so in tier 0, and record it as a negative result against the framework's own prediction |
| the bottom rung `(L₁, 240)` does not reproduce the first round's 3 of 10 | the two rounds disagree about the same measurement | stop and reconcile; nothing else is read until they agree |

The last row is the reproduction check, and it is a stopping rule like the
others.

---

## 8. What this round has to produce, in the shape D5 requires

* a reasoning module, `glm_universal/reasoning/deep_hole_escalation.py`, with a
  `deep_hole_escalation_report` function;
* a report subject wired into the query runtime and into the evaluation set;
* a test file, `tests/test_deep_hole_escalation.py`, including a test that
  fails if the bottom rung stops reproducing the first round, and a test that
  fails if any control ever rises to the method's rate;
* this document, with every table a generated block emitted from a measurement
  cache guarded by a digest of its sources (D4/D6);
* a Lean file, `RequestProject/GLM/DeepHoleEscalation.lean`, in both copies;
* exactness throughout (D7), with the one non-enumerable part — the start
  offsets — declared in §2 and the one digest site declared in §6.

---

## 9. The Lean half: what is proved rather than measured

The theorems are about the **ladder and its criterion**, not about the Leech
lattice, and they are what makes the measurement above a test of something
rather than a report of numbers.

1. **The separation criterion is sufficient.** If every carrier of class `T`
   lies within `w` of `T`'s reference, and distinct references are more than
   `2w` apart, then the nearest reference to a carrier is its own class's, and
   it is the unique nearest. This is the triangle inequality, and it is why
   `ρ < 1` is the right thing to measure: `separated_nearest_correct`.
2. **The criterion is a congruence statement.** Under the same hypothesis, the
   classification is constant on the indistinguishability of the reading —
   the label descends to the layer, in the exact sense of
   `GLM.Info.Layer.descends_iff_congruent`.
3. **Refinement is not improvement.** A cumulative reading refines its parts —
   it separates at least as much — and this does **not** imply its ratio `ρ` is
   smaller, because widening moves the within-class spread as well as the
   separation. Stated and witnessed by an explicit pair, so that the round
   cannot claim that escalation must work: `refines_not_monotone_ratio`.
   The measurement, not the theory, is what decides whether a wider reading
   helps.
4. **The ladder is total, minimal and refuses.** `firstResolving` returns the
   least index whose criterion holds and `none` when none does; the returned
   index resolves; no earlier one does; and `none` is equivalent to the
   universally quantified failure — so a refusal at the top of the ladder is a
   statement about every rung, which is the difference between "unreasonable"
   and "not yet resolved".

---

## 10. What the GLM gains — three claims, to be argued or refuted by the numbers

1. **Escalation as an inference step, not a repair.** If a cell passes, the
   machine has an instance where a query that *refused* at one resolution is
   *answered* at a higher one by a stated rule, with the rung recorded. That is
   the difference between a lookup and a reading that knows its own resolution.
2. **A measured price for the narrow view.** `L₂` differs from `L₁` only by the
   information the first round threw away. The gap between their `Q₀` counts at
   the same `N` is the cost of that discard, in the units of the question.
3. **A boundary with a number on it.** If nothing passes, the round still
   returns `ρ` at twelve cells, which says how far from the criterion the
   reading is and on which axis it moves — capacity or width. A refusal with a
   distance attached is worth more than a refusal.

---

## 11. Exactness, and how to re-take every number

Integers and `Fraction` throughout: offsets, distances, shares, Wasserstein
integrals, radii, ratios and tails. `log2` is an exact rational bracket. The
only declared non-exact operation is the digest of N1 (§6). The only
non-enumerable step is the start offsets (§2).

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools escalation --write
PYTHONPATH=. python3 GLM.py -q "report hole ladder" -c 1
PYTHONPATH=. python3 -m glm_universal.corpus --write
```

---

## 12. The measurement

*Written by the measurement, not by hand: every table below is a generated
block emitted from a cache guarded by a digest of the modules that produced
it, so when a source moves the block says so and the corpus check fails.*

<!-- generated: deepholeesc-verdict -->
**The verdict is `the law descends`.**  The ladder is 4 readings at 4 ensemble sizes, 16 cells in all, and the gate is that every one of the 10 reference holes recognises itself when only the ensemble seed changes.

The bottom rung is the first round's cell — the arrival shares at 240 starts — and it returns 3 of 10, against the 3 the first round reported.  The best cell of the whole ladder is `joint` at 1920 starts, which returns 10 of 10 with a ratio of `rho = 2.5943`; the criterion needs `rho < 1`.

The gate is reached at L4 - the joint reading, L2 and L3 together with 1920 starts, which is the cheapest cell in the declared order that reaches it -- and it is a cell of the extension rung, decided after the twelve pre-registered cells were measured, so it is reported as an extension and not as the pre-registered result.
<!-- end generated -->

### 12.1 The ladder, cell by cell

<!-- generated: deepholeesc-ladder -->
| reading | starts | rung | holes recognising themselves | worst seed shift `W` | separation `B` | `rho = 2W/B` | criterion |
|---|---|---|---|---|---|---|---|
| L1 - arrival shares (the first round's statistic) | 240 | declared | 3 / 10 | 0.1000 | 0.0513 | 3.9000 | fails |
| L1 - arrival shares (the first round's statistic) | 480 | declared | 5 / 10 | 0.0694 | 0.0245 | 5.6595 | fails |
| L1 - arrival shares (the first round's statistic) | 960 | declared | 8 / 10 | 0.0467 | 0.0259 | 3.6044 | fails |
| L1 - arrival shares (the first round's statistic) | 1920 | extension | 8 / 10 | 0.0387 | 0.0281 | 2.7512 | fails |
| L2 - arrival shares widened by the stray spectrum | 240 | declared | 4 / 10 | 0.1370 | 0.0709 | 3.8646 | fails |
| L2 - arrival shares widened by the stray spectrum | 480 | declared | 8 / 10 | 0.0944 | 0.0266 | 7.0963 | fails |
| L2 - arrival shares widened by the stray spectrum | 960 | declared | 9 / 10 | 0.0653 | 0.0374 | 3.4968 | fails |
| L2 - arrival shares widened by the stray spectrum | 1920 | extension | 9 / 10 | 0.0424 | 0.0297 | 2.8520 | fails |
| L3 - the exact rational measure of emission distances | 240 | declared | 5 / 10 | 0.0381 | 0.0000 | n/a | fails |
| L3 - the exact rational measure of emission distances | 480 | declared | 6 / 10 | 0.0225 | 0.0000 | n/a | fails |
| L3 - the exact rational measure of emission distances | 960 | declared | 7 / 10 | 0.0157 | 0.0000 | n/a | fails |
| L3 - the exact rational measure of emission distances | 1920 | extension | 8 / 10 | 0.0125 | 0.0000 | n/a | fails |
| L4 - the joint reading, L2 and L3 together | 240 | declared | 6 / 10 | 0.1637 | 0.0873 | 3.7480 | fails |
| L4 - the joint reading, L2 and L3 together | 480 | declared | 9 / 10 | 0.1077 | 0.0338 | 6.3693 | fails |
| L4 - the joint reading, L2 and L3 together | 960 | declared | 9 / 10 | 0.0776 | 0.0481 | 3.2282 | fails |
| L4 - the joint reading, L2 and L3 together | 1920 | extension | 10 / 10 | 0.0465 | 0.0358 | 2.5943 | fails |

The criterion `rho < 1` is *sufficient* for the gate — that is `GLM.DeepHoleLadder.nearest_correct`, proved rather than assumed — so a cell can reach the gate without the criterion holding, but not the other way round.  The best cell is `joint` at 1920 starts.  A rung marked *extension* was added after the twelve pre-registered cells had been measured and the count was seen to be climbing; it is counted in the multiplicity correction and is never read as a pre-registered result.
<!-- end generated -->

### 12.2 The reproduction check

<!-- generated: deepholeesc-reproduction -->
The ladder's bottom rung is the first round's cell exactly — the arrival shares at 240 starts, the same holes, the same reference and sanity seeds — so it must return the first round's number before anything above it is read.  It returns **3 of 10** against the **3** the first round reported: reproduces = `True`.

The two rounds therefore agree, and the rest of the ladder is read.
<!-- end generated -->

### 12.3 The decision, and the cell it lands on

<!-- generated: deepholeesc-decision -->
| item | value |
|---|---|
| the gate | all 10 reference holes recognise themselves |
| cells that reach it | 1 of 16 (0 of the 12 pre-registered) |
| the bottom rung | 3 of 10, `rho = 3.9000` |
| the best cell | `joint` at 1920 starts, 10 of 10, `rho = 2.5943` |
| the sanity count rises along the ladder | `True` |
| the full query set was run | `True` |
| the best pre-registered cell | `joint` at 960 starts, 9 of 10 |
| verdict | `the law descends` |

The gate is reached at L4 - the joint reading, L2 and L3 together with 1920 starts, which is the cheapest cell in the declared order that reaches it -- and it is a cell of the extension rung, decided after the twelve pre-registered cells were measured, so it is reported as an extension and not as the pre-registered result.
<!-- end generated -->

### 12.4 The controls at that cell

<!-- generated: deepholeesc-controls -->
| classifier | correct | queries | accuracy | bits, corrected for the cells tried |
|---|---|---|---|---|
| the escalated reading | 40 | 44 | 90.9 % | 112.10 |
| digest control (D3) | 7 | 44 | 15.9 % | -1.54 |
| seeded reshuffle of the pairing | 0 | 44 | 0.0 % | -4.32 |
| the plain vertex count | 12 | 44 | 27.3 % | 5.67 |
| uniform-profile ablation | 12 | 44 | 27.3 % | 5.67 |

Chance is `1/10` per query, and the bit column is corrected for the 20 cells and statistics this question has been asked with, across both rounds.  Beats the vertex-count baseline: `True`; beats every control: `True`.
<!-- end generated -->

### 12.5 The secondaries

<!-- generated: deepholeesc-secondaries -->
| secondary | reading |
|---|---|
| `S_b` — faithfulness against the certified radius | faithfulness `0.0659`, `r* = 0.0179`, compatible `False` |
| `S_c` — accuracy over the full query set | 40 of 44 |
| `S_d` — the mean rank of a query's own reference | 1.0909 |
| what each reading is worth, at its own best cell | shares 8 of 10, widened by the strays 9, the rational measure 8, the joint reading 10 |
| the cost of the round | 38400 exact decoder calls over 20 ensembles, one per centre and seed at the top rung and sliced for the rungs below |
<!-- end generated -->

### 12.6 What the round establishes

Five things, and the last two are the ones that decide what may be claimed.

**The law descends, and the rung it descends at is named.** The gate — every
reference hole recognising itself under a bare change of ensemble seed — is
reached at the joint reading with 1920 starts: 10 of 10, where the first
round's cell gives 3. Over the full query set at that cell the reading names
**40 of 44** correctly against **12** for the vertex-count baseline, **12** for
the uniform-profile ablation, **7** for the digest control and **0** for the
seeded reshuffle, so it beats every control including the competitor the first
round fixed in advance. The mean rank of a query's own reference is **1.09**.
The cell that does it is the extension rung of §14, decided after the declared
twelve were measured; the best pre-registered cell is 9 of 10, and the two are
kept apart in every table.

**The obstruction was the reading, not the geometry.** The first round
concluded that "240 starts over 25 to 48 vertices does not resolve the arrival
distribution finely enough". That is now measured rather than supposed: with
the same holes, the same seeds and the same walk, the sanity count goes
`3 → 5 → 8 → 8` as the budget alone rises, and `3 → 4 → 6` as the reading
alone widens at fixed budget. Both axes move it, and only both together reach
the gate — the shares alone stall at 8 of 10 even at 1920 starts, so capacity
without width does not finish the job. Nothing about the hole changed; only
what was read of it.

**The discarded strays were worth something, and the amount is now a number.**
`L₂` differs from `L₁` by exactly the information the first round excluded from
the profile. At 240 starts it is worth one hole, at 480 three, at 960 one, at
1920 one — and the joint reading, which adds the exact rational measure on top,
is worth three at 240, four at 480 and two at 1920, where it is the difference
between missing the gate and reaching it. That is the price of the narrow view,
in the units of the question, and it is the second time this repository has
paid it: the information-loss audit found the same defect in the integer layer,
where the substrate parity bits had been thrown away to make the arithmetic
easier.

**A rung can conflate two carriers outright, and one does.** Under `L₃` the
reference profiles of `A_1^24` and `A_2^12` are *identical*: both holes emit no
stray at all over the declared ensemble, so their entire distance measure is a
single atom at the covering radius and the rung cannot tell them apart. The
separation of that rung is therefore exactly `0`, its ratio is undefined, and
the table says `n/a` rather than dividing. This is `exists_indist_of_capacity_lt`
in the concrete: a reading whose view is coarser than the carrier space must
conflate, and here it is visible as a pair of names rather than as a bound.
It is also why `L₃` alone is not the answer and `L₄` — which carries `L₂`
alongside it — is the better rung.

**The criterion is sufficient and emphatically not necessary.** `ρ` never falls
below 1 at any cell; the best is `2.59`. Yet all ten holes recognise themselves
at that cell and 40 of 44 queries are named correctly. The two facts are
consistent because `ρ < 1` is a *worst-case* condition — one hole's seed shift against the closest pair of
references in the whole table — and
`GLM.DeepHoleLadder.nearest_correct` proves only the implication, never the
converse. The honest reading is that the ladder is much closer to naming holes
than the ratio suggests, and much further from *certifying* that it does. A
detector whose negative answers are proofs still needs `ρ < 1`, and that is
still a long way off.

**A faculty, and not yet a certificate.** At the passing cell faithfulness needs
`r ≥ 0.0659` while separation allows only `r < 0.0179`, so the two are still
incompatible and `GLM.DeepHole.absent_certifies` still cannot be instantiated:
the classifier now names holes reliably and still cannot *prove* that a hole is
absent. That is the same distinction the first round drew, moved one step: what
failed there was the naming, what remains open here is only the certificate.

**What is deliberately not concluded.** No claim is made about `N = 3840` or
above, about the thirteen unreached Niemeier types, or about a cell that was not
run. The passing cell is an extension rung and is labelled as one wherever it is
reported, the multiplicity correction counts all sixteen cells, and the bit
score at the passing cell is reported with that correction applied rather than
quoted raw.

---

## 13. What this study does not do

* It does **not** enlarge the hole set. The same 14 centres and the same 10
  types as the first round; the 13 unreached Niemeier types stay unreached and
  nothing is claimed about them.
* It does **not** promote a secondary to primary after seeing the numbers.
  `Q₀` is the gate and it is fixed in §4.
* It does **not** use a pairwise vertex distance, a diagram shape or a
  component-size vector at any rung. Those are the label source, and reading
  them would be reporting the answer key as a method.
* It does **not** extrapolate past the top rung. If `N = 960` and `L₄` do not
  pass, the study says what `ρ` was and refuses to say what `N = 24000` would
  do. §14 runs *one* further rung rather than extrapolating, and marks it as
  decided after the trend was seen.

---

## 14. The extension rung — declared after the trend, before the run

§§1–11 were committed before any measuring code existed and §12 reports what
those twelve cells said. This section is different in kind and says so.

**What was decided after seeing the numbers.** The twelve declared cells took
the sanity count from 3 of 10 to 9 of 10 and stopped one hole short of the
gate, with the count still rising on both axes. One further **size** rung was
therefore added — `N = 1920`, at all four readings, four more cells — and this
paragraph was written and committed before it was run.

**What is unchanged.** The holes, the seeds, the readings, the primary
statistic and the gate. The extension is a rung of the same ladder and not a
new statistic; nothing is promoted, nothing is re-defined, and §12 keeps the
numbers the twelve declared cells produced.

**What changes.** Three things, all in the direction of costing the extension
rather than crediting it:

1. `m` rises from 16 to **20**, so any bit score this round reports is
   corrected for the extension whatever the extension says.
2. Every table marks each cell **declared** or **extension**, and the decision
   block reports the best *pre-registered* cell alongside the best cell
   overall. A gate reached only at an extension rung is reported as an
   extension result, in those words.
3. The stopping rule of §7 is unchanged and still applies: the full query set
   and its controls run only at a cell that reaches the gate.

**Why run it at all.** Because the repository exists to develop the GLM, and a
round that has located a boundary to within one doubling of the budget is one
run away from saying which side of it the question falls on. Refusing to take
that run would leave the more useful of the two possible findings — that the
law does descend, at a stated cost — unmeasured. The cost of taking it is that
the result is post-hoc, and the price of that is paid in the correction above
and in the labelling.
