# The construction ladder — the full escalation, generated on the fly, walked out from the middle

## Tier 0 — the coarse read

**Question.** Is reading the substrate at one fixed rung of the Golay–Leech construction ladder a partial system — does escalating the reading across every rung, out from the middle, name more carriers than any single rung can?

**Verdict.** It is a partial system, and the note's five rungs were too few: escalating across the eleven-rung ladder names 462 of 568 queries correctly with 0 wrong, against 327 for the five-rung ladder and 283 for the best single rung.
The six rungs that were added are not ad-hoc: Construction `A` over the trivial
code is `2ℤ²⁴` and over the even-weight code is `D₂₄`, so the lattices that
fill the note's long step are Construction rungs too, and the scaling `L ↦ 2L`
generates them. No single rung is best at more than one perturbation, and the
escalation loses nothing to an oracle that is allowed to pick the rung after
the fact: 462 is the oracle's count too. The order of the walk changes the cost
and not the answer — which is a theorem, not a coincidence — and the sweep over
ladder lengths finds where that theorem's hypothesis fails: the ladder stays
safe to thirteen rungs and breaks at fifteen.

**Deciding figure.** 462 of 568 queries answered correctly with 0 wrong, against 327 for the five-rung ladder and 283 for the best single rung.

**Recomputed by.** `glm_universal.reasoning.ladder_escalation.ladder_escalation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

The round's source is
[`source_material/Golay codes and Hadamard matrices.txt`](../source_material/Golay%20codes%20and%20Hadamard%20matrices.txt),
a note about where the Golay codes come from, how Constructions A, B and C
climb from the integer grid to the Leech lattice, and how the shell depths of
each are read off a theta function. Two things were asked of it: **see the
ladder through properly** — check it, correct it, and build the rungs it names
— and then **use it**, as a reading the machine escalates rather than a picture
in a document.

This document is the round's record. §1 is the note, recomputed claim by claim.
§2 is the ladder as it actually is. §3 is the escalation, declared before it was
run. §4 is what it measured. §5 is what is proved in Lean. §6 is what is left,
written so that the next round can pick it up cold.

Everything below is exact: integers and `Fraction`s, no float, no random
source — the perturbation sweep is a function of a carrier's index through a
Golay codeword, not a sample.

## 1. The note, recomputed

`glm_universal.substrate.golay_paley` recomputes every checkable claim the note
makes about the codes, and `glm_universal.substrate.construction_ladder`
recomputes the ones about the lattices and their shells. Nineteen claims: **12
confirmed, 7 corrected, 0 refuted**. The first and most useful is not a
correction at all:

> **The note's 12 × 12 block is this system's own code.** With `G = [I₁₂ | B]`
> it generates exactly the 4,096 masks `substrate.mog.GOLAY_SET` already holds,
> in the same coordinate labelling and with no permutation applied. Everything
> the note says about `B` is therefore a statement about the substrate the GLM
> runs on, not about an isomorphic copy of it.

Confirmed by recomputation: the code is `[24, 12, 8]`, self-dual, with weight
enumerator `1, 759, 2576, 759, 1`; dropping the last column gives the perfect
`[23, 12, 7]` code (`4096 × 2048 = 2²³`); `Q = J − 2B` is a Hadamard matrix of
order 12; the `11 × 11` core carries a symmetric 2-design; the ternary block
generates the self-dual `[12, 6, 6]` code; `Θ_{Zⁿ} = θ₃ⁿ` and
`Θ_{Dₙ} = (θ₃ⁿ + θ₄ⁿ)/2`; the Leech shells are 196,560 then 16,773,120 then
398,034,000, and the shell between the origin and the first is empty.

The seven corrections, each with its recomputation:

| the note says | what is actually the case |
|---|---|
| `H₁₂ = Q − I₁₂` is a skew-Hadamard matrix | `Q − I` has entries in `{−2, −1, 0, 1}`, so it is not a Hadamard matrix at all. `Q` itself already is one: `Q Qᵀ = 12 I`. |
| the `−1` positions of the normalised `11 × 11` submatrix form a `2-(11, 5, 2)` design | those are the `1` entries of `B`: eleven blocks of **six** meeting in **three**, a `2-(11, 6, 3)` design. Its complement is the `2-(11, 5, 2)` biplane the note means. |
| the ternary enumerator ends `+ 24xy¹¹ + y¹²` | the `[12, 6, 6]` code has **no** word of weight 11 and **24** of weight 12: `x¹² + 264x⁶y⁶ + 440x³y⁹ + 24y¹²`. |
| the printed `6 × 5` block generates the perfect `[11, 6, 5]` ternary Golay code | as printed it generates a code of minimum weight **2** — its row 2 is repeated as row 6. Removing the last column of the `6 × 6` block does give `[11, 6, 5]`, and it is perfect. |
| `Θ_{Λ₂₄} = (1/8)(θ₂²⁴ + θ₃²⁴ + θ₄²⁴) − (69/2)Δ` | that expression has constant term `1/4` and is not a theta series. The identity that gives the note's own coefficients is `E₄³ − 720Δ` with `E₄ = (θ₂⁸ + θ₃⁸ + θ₄⁸)/2` and `Δ = (θ₂θ₃θ₄/2)⁸` — which is what `substrate.leech2.theta_series` already computes. |
| the constructions form a ladder, each rung inside the next | they form a **diamond**. See §2. |
| Construction B on `G₂₄` has 1,152 minimal vectors, "the subset the V3 sieve keeps" | two quantities have been run together. Rung B has **98,256** minimal vectors of norm 32, enumerated. 1,152 is what the old zero-storage sieve *keeps* of the Leech lattice's 196,560 — a recall of `8/1365`, measured in [`ZERO_STORAGE_STUDY.md`](ZERO_STORAGE_STUDY.md). |

## 2. The ladder as it actually is

Five rungs, all in the integral (`×√8`) model this package uses throughout, and
all *generated* from their conditions — there is no stored table of any of
them. Each row's minimum norm and kissing number is checked against the rung's
own generated theta series rather than quoted beside it:

| rung | conditions | min. norm | kissing | covolume |
|---|---|---|---|---|
| `Z` | integer coordinates | 1 | 48 | `2⁰` |
| `D` | even coordinate sum | 2 | 1,104 | `2¹` |
| `A` | even coordinates, mod-4 support a Golay codeword | 16 | 48 | `2³⁶` |
| `C` | `B` together with the odd coset — the Leech lattice | 32 | 196,560 | `2³⁶` |
| `B` | `A` with `Σx ≡ 0 (mod 8)` | 32 | 98,256 | `2³⁷` |

The series are generated: `θ₃²⁴` for `Z`, `(θ₃²⁴ + θ₄²⁴)/2` for `D`,
`W(θ₃(q¹⁶), θ₂(q⁴))` for `A` — where the Golay weight enumerator `W` is exactly
where the code enters the geometry — and `E₄³ − 720Δ` for `C`. `B` is the one
rung whose full series is not generated here; its shells up to the minimum are
derived (it is inside `C`, so everything below norm 32 is empty) and the module
says where the claim stops rather than guessing.

**The ladder is a diamond, not a chain.** `B` is inside both `A` and `C`, and
both are inside `D`, which is inside `Z` — but `A` and `C` are *incomparable*,
and each has an explicit witness:

* `4·e₀` is on rung `A` and not on rung `C`: its coordinate sum is 4, and the
  mod-8 glue forbids it;
* the glue vector `(−3, 1²³)` is on rung `C` and not on rung `A`: its
  coordinates are odd, and `A` is an even-coordinate lattice.

`GLM.ConstructionLadder.ladder_not_chain` is that fact as a theorem. It is the
structural reason a reading cannot simply "climb": there are two routes up, and
a reader that takes one has not seen the other. It is also the reason the walk
in §3 starts in the middle.

## 3. The escalation, as declared

**The idea.** A rung is a way of reading a carrier: quantise the 24 exact
coordinates to the nearest point of that rung's lattice, and use the point as
the address. The rungs trade two things against each other and no single rung
wins both — a coarse rung (`B`, `C`) tolerates a perturbed query but conflates
distinct carriers; a fine rung (`D`, `Z`) separates everything and loses the
address as soon as the query moves. A system fixed at one rung is therefore a
*partial* system by construction, which is what the round set out to test.

**The sample.** The first 24 named objects of each of the six registers, in the
register's own order: **142** carriers (the mathematics register holds fewer
than 24). Not chosen, not sampled.

**The queries.** Each carrier is perturbed by a deterministic offset: Golay
codeword `i mod 4096` chooses the coordinates, the position inside the support
chooses the sign. Four settings, chosen against the rungs' packing radii — a
rung of minimum norm `m` returns the right point for any offset of squared
length below `m/4` — so that the sweep crosses every rung's tolerance in turn:
8 coordinates by `1/8`, by `1/4`, by `1/2` and by `3/4`. That is
`142 × 4 = 568` queries.

**The stopping rule.** The only one available to a reader that does not know
the answer: **stop at the first rung whose cell holds exactly one carrier**.
Occupancy is read from an index built once from the clean carriers; nothing
about the query's identity is used. A rung whose cell is empty, or holds more
than one carrier, has named nothing and the walk goes on.

**The orders.** Three, all with the same stopping rule:

* `middle_out` — `A, D, C, Z, B`: start where the system already reads, one
  step finer, one step coarser, then the ends. This is the movement the round
  was asked to try;
* `coarse_to_fine` — `B, C, A, D, Z`: the note's ladder, climbed from the
  bottom;
* `fine_to_coarse` — `Z, D, A, C, B`: the same ladder from the top.

**The controls.** Each rung read alone — five partial systems — and an
**oracle** that is allowed to pick, after the fact, any rung that would have
been right.

**The cost.** Every quantiser counts its own work: coordinate roundings, Golay
codewords evaluated, and `±4` repairs. A rung cannot buy accuracy quietly.

## 4. What it measured — the five-rung ladder

This section is the round that built the note's five rungs, and it is kept as
written: it is the *before* the thickening in §4a is measured against, and the
stored measurement holds both.

Correct / wrong / refused over all 568 queries:

| reading | correct | wrong | refused | work |
|---|---|---|---|---|
| escalation, `middle_out` | **327** | 0 | 241 | 5,867,885 |
| escalation, `coarse_to_fine` | 327 | 0 | 241 | 6,953,146 |
| escalation, `fine_to_coarse` | 327 | 0 | 241 | 4,735,504 |
| rung `C` alone (best single rung) | 205 | 0 | 363 | 4,707,584 |
| rung `A` alone | 196 | 0 | 372 | 2,353,792 |
| rung `Z` alone | 194 | 0 | 374 | 13,632 |
| rung `B` alone | 187 | 0 | 381 | 2,356,027 |
| rung `D` alone | 164 | 0 | 404 | 13,894 |
| oracle over all five rungs | 327 | — | — | — |

Four readings of that table, in the order they matter.

**The full escalation beats every partial system, and by a lot.** It is a
partial system: escalating across the rungs names 327 of 568 queries correctly
with 0 wrong, against 205 for the best single rung — **+122 queries, a 59 %
increase**, with no wrong answer introduced anywhere. A refusal stays a
refusal; nothing that was right becomes wrong.

**No rung is best twice.** The best single rung *changes with the
perturbation*: `Z` at `1/8` (101 correct) and at `1/4` (93), `A` at `1/2` (39)
and at `3/4` (20). Even a system allowed to choose one rung per perturbation
setting — which a real reader cannot, not knowing the noise — reaches only
101 + 93 + 39 + 20 = 253, still well below 327. This is the sharp form of the
round's question: the partiality is not that the wrong rung was chosen, it is
that *a* rung was chosen.

**The stopping rule costs nothing.** The escalation's 327 is exactly the
oracle's 327: on this sample the first rung that names one carrier is never the
wrong one to have stopped at. That is not luck — across all 568 queries no two
rungs ever named *different* carriers (`rungs_disagree = 0`), and under that
condition the answer is independent of the order, which is
`GLM.ConstructionLadder.firstNamed_order_independent`.

**The movement the round proposed is good but not optimal, and the honest
reading says so.** All three orders return the same 327 answers; they differ
only in work. Middle-out costs 5,867,885 against the note's bottom-up ladder at
6,953,146 — **16 % cheaper** — because it starts where most queries resolve
rather than at the most expensive rung. But starting at the cheap end costs
4,735,504, **19 % cheaper than middle-out**, because the fine rungs are
roundings and the coarse rungs are 4,096-codeword decodes. So: *start in the
middle and work out* is the right picture of the geometry and a real
improvement on climbing, and it is not the cheapest schedule. If cost is the
objective, visit the rungs by price; if the point is to begin where the system
already reads and expand its reading outwards, middle-out is that, and it is
never worse in accuracy.

The occupancy table says why the coarse rungs cannot simply be preferred: at
rung `B` the 142 carriers occupy 116 cells, 110 of them singletons and 32
carriers conflated, with 14 in the largest cell; at `D` and `Z` they occupy 129
cells with 125 singletons and 17 carriers conflated. Conflation is the price of
robustness, and it is not recoverable by reading harder at the same rung.

## 4a. The ladder was too short

§6 of the previous round named the next thing to do: *generate the rungs
between the rungs*, because the tolerance gap is widest between `D` (minimum
norm 2) and `A` (16), where the sweep falls from 93 correct to 39. That has now
been done, and it changes the headline.

**The filling rungs are Construction rungs.** The gap was in the *list*, not in
the construction. Construction `A` over the trivial code `{0}` is exactly
`2ℤ²⁴`, and over the even-weight code it is exactly `D₂₄`; and in this
package's `×√8` model rung `A` is itself `2G`, where `G` is the unscaled Golay
lift — the vectors whose even coordinates form a codeword. So the scaling
`L ↦ 2L` generates the missing rungs, and iterating it generates as many more
as are wanted. Six were admitted, and the ladder is now eleven rungs,
coarsest first:

| rung | what it is | min. norm | kissing | covolume |
|---|---|---|---|---|
| `2A` | Construction `A` doubled | 64 | 48 | `2^60` |
| `4D` | `4 D₂₄` | 32 | 1,104 | `2^49` |
| `4Z` | `4 ℤ²⁴` — Construction `A` over the trivial code, twice scaled | 16 | 48 | `2^48` |
| `B` | Construction `B` | 32 | 98,256 | `2^37` |
| `C` | the Leech lattice | 32 | 196,560 | `2^36` |
| `A` | Construction `A` — where the system already reads | 16 | 48 | `2^36` |
| `2D` | `2 D₂₄` | 8 | 1,104 | `2^25` |
| `2Z` | `2 ℤ²⁴` | 4 | 48 | `2^24` |
| `A/2` | `G`, the unscaled Golay lift | 4 | 48 | `2^12` |
| `D` | the checkerboard lattice | 2 | 1,104 | `2^1` |
| `Z` | the integer grid | 1 | 48 | `2^0` |

Two things about that list are worth stating. The widest step between
neighbouring minimum norms falls from **eight** (2 → 16) to **two**. And its
arithmetic middle is still `A`: the eleven-rung ladder is the longest one the
admission rule generates whose middle is the rung the system already reads
from, so "start in the middle and work outwards" still starts where the system
is.

**The measurement, re-taken.** Same 142 carriers, same four perturbations, same
stopping rule — eleven rungs instead of five:

| reading | correct | wrong | refused | work |
|---|---|---|---|---|
| escalation, `coarse_to_fine` | **462** | 0 | 106 | 5,809,935 |
| escalation, `fine_to_coarse` | 462 | 0 | 106 | 5,931,993 |
| escalation, `middle_out` | 462 | 0 | 106 | 7,678,479 |
| the five-rung ladder, all orders (the recorded *before*) | 327 | 0 | 241 | — |
| rung `2A` alone (best single rung) | 283 | 0 | 285 | 2,381,056 |
| rung `4Z` alone | 267 | 0 | 301 | 40,896 |
| rung `4D` alone | 266 | 0 | 302 | 41,142 |
| rung `C` alone | 205 | 0 | 363 | 4,707,584 |
| rung `A` alone | 196 | 0 | 372 | 2,353,792 |
| rung `A/2` alone | 137 | 0 | 431 | 2,381,056 |
| rung `2D` alone | 113 | 0 | 455 | 41,156 |
| rung `2Z` alone | 105 | 0 | 463 | 40,896 |
| oracle over all eleven rungs | 462 | — | — | — |

So: **462 of 568 queries answered correctly with 0 wrong, against 327 for the
five-rung ladder and 283 for the best single rung** — +135 queries on the
recorded before, a **41 % increase**, with refusals cut from 241 to 106 and no
wrong answer anywhere. The escalation still matches the after-the-fact oracle
exactly, and across all 568 queries no two rungs named different carriers
(`rungs_disagree = 0`), which is the hypothesis of
`GLM.ConstructionLadder.firstNamed_order_independent`.

**How long is too long?** The ladder is generated, so the question can be
measured rather than argued. The rungs are admitted nearest-first — by the
distance between a rung's covolume and `A`'s — and the sweep runs the same
experiment at each length:

| rungs | middle | correct | wrong | refused | rungs disagree | order-independent |
|---|---|---|---|---|---|---|
| 5 | `A` | 327 | 0 | 241 | 0 | yes |
| 7 | `A` | 432 | 0 | 136 | 0 | yes |
| 9 | `A` | 439 | 0 | 129 | 0 | yes |
| 11 | `A` | 462 | 0 | 106 | 0 | yes |
| 13 | `C` | 475 | 0 | 93 | 0 | yes |
| 15 | `B` | 476 | **1** | 92 | 1 | **no** |

Thirteen rungs is the longest safe ladder on this sample: it scores higher
still, and every rung agrees with every other. At fifteen the ladder breaks,
and it breaks in exactly the way the theorem predicts it can — a rung coarse
enough to hold two carriers in one cell can also hold exactly one *wrong*
carrier in the cell a perturbed query lands in, so two rungs name different
carriers, the hypothesis of `firstNamed_order_independent` fails, and the
answer becomes order-dependent: one wrong answer appears under
`coarse_to_fine` and none under the other two orders. That is a measured
instance of the theorem's hypothesis failing, and it is why the declared ladder
is eleven rungs and not as many as can be generated.

**One thing the thickening reversed.** On the note's five rungs, starting in
the middle was cheaper than climbing from the bottom (5,867,885 against
6,953,146). On eleven rungs it is the dearest of the three: 7,678,479 against
5,809,935 for `coarse_to_fine`, because the middle rung is now a
4,096-codeword Golay decode surrounded by more decodes, while the coarse end is
reached in fewer visits. The accuracy is identical either way — that is the
theorem — so the order remains a cost decision, and the cheapest one has moved.

## 5. What is proved rather than measured

`RequestProject/GLM/ScaledLadder.lean`, 0 `sorry`, is the thickening:

* `Dbl P` is the lattice `2L` when `P` is `L`, and `Scaled k P` is `2^k L`;
  `dbl_mono` and `scaled_mono` carry one containment across every scale;
* `isA_iff_dbl_isG` — **Construction `A` is itself a doubled lattice**,
  `A = 2G`, which is what makes the filling rungs Construction rungs;
* `isA_dbl_isD` — **Construction `A` sits inside the doubled checkerboard
  lattice.** This is the containment the thickening rests on, and it rests in
  turn on the Golay code being doubly even
  (`GLM.LatticeShortcut.golay_weight_div_four`): halving a vector of `A` leaves
  the `24 − w` coordinates outside the codeword odd, and `w` divisible by four
  keeps that count even, so the coordinate sum stays even;
* `isG_isD`, `dbl_isZ_isG`, `isC_isG` — the rest of the chain, including that
  the Leech lattice is inside `G` because all its coordinates share a parity;
* `scaled_two_isZ_isA` (`4ℤ²⁴ ⊆ A`) and `scaled_two_isD_isB` (`4D₂₄ ⊆ B`) —
  what attaches the coarse scaled rungs to the note's own;
* `gap_chain` — the filled step as one theorem:
  `A ⊆ 2D₂₄ ⊆ 2ℤ²⁴ ⊆ G ⊆ D₂₄ ⊆ ℤ²⁴`, five steps where the note had one.

The Python side does not take those containments on trust either:
`construction_ladder.inclusion_report` *derives* all 50 containments between
the eleven rungs from a handful of relative rules, and
`containment_spot_check` then tries every derived containment on generated
points of the lower rung, so a wrong derivation is caught rather than believed.

`RequestProject/GLM/ConstructionLadder.lean`, 0 `sorry`:

* `isB_isA`, `isB_isC`, `isA_isD`, `isC_isD`, `isD_isZ` — the containments that
  hold, proved from the rung conditions;
* `fourE_isA`, `fourE_not_isC`, `glue_isC`, `glue_not_isA`,
  `ladder_not_chain` — the two witnesses, and the diamond;
* `middleOut_head`, `middleOut_length`, `middleOut_nodup`,
  `middleOut_perm_range` — a walk out from the middle of a ladder of `2k+1`
  rungs visits every rung exactly once: it is a permutation of the ladder, so
  the movement misses nothing;
* `firstNamed_order_independent` — if every rung that names something names the
  same thing, every visiting order returns the same answer. This is the theorem
  that licenses choosing the order for cost; its hypothesis is the
  `rungs_disagree = 0` the measurement reports;
* `visitCount_eq_one_of_head_named`, `visitCount_le_length` — the cost of
  starting in the right place is one rung, and no walk pays for more rungs than
  the ladder has.

## 6. Limits, and what the next round should take

**Limits of what is claimed.** The figures are about this sample (142 carriers
of six registers) and this sweep (four declared perturbations); a different
register or a different noise model would have to be re-measured. Occupancy is
computed against the sample, so a larger register makes conflation worse at the
coarse rungs and would move the numbers — in which direction is an open
question, not an assumption. Rung `B`'s theta series above norm 32 is not
generated. The escalation measured here reads *carriers*; it is not yet wired
into the query loop that answers questions
([`QUERY_ESCALATION_STUDY.md`](QUERY_ESCALATION_STUDY.md)), so no end-to-end
answer changes because of it.

**Named for the next round, in the order they are worth taking.**

1. *Wire the ladder into the query loop.* The loop in
   `runtime/escalation_loop.py` climbs a ladder of **faculties**; this round
   built a ladder of **readings**. They compose: a refusal tagged `absent`
   could be re-read one rung out before the next faculty is tried. The measured
   gain here is about addressing, so the place to look for an end-to-end effect
   is the address-retrieval register
   ([`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md)), where a query
   already arrives as coordinates.
2. *Generate the rungs between the rungs.* **Taken — see §4a, and taken
   further since.** The prediction made here was that a rung of minimum norm 4
   or 8 would pick up part of the drop between `D` and `A`; it did, and by more
   than was guessed: the thickened ladder answers 462 against 327. The round
   after that replaced the *named* index by the **minimum squared norm**, and
   generated a complete power-of-two family over it —
   [`NORM_FAMILY_STUDY.md`](NORM_FAMILY_STUDY.md) for the family and its
   containments, [`OPERATION_ESCALATION_STUDY.md`](OPERATION_ESCALATION_STUDY.md)
   for what escalation over it does to operations that are not retrieval.
   **The eleven-rung result recorded in §4a is superseded as the ladder in
   use**: the norm-indexed family is measured in `NORM_FAMILY_STUDY.md` §4,
   where the full family turns out to answer a query *wrongly* and is repaired
   by retiring rungs before it is adopted. The figures in §4a are still the
   figures for the eleven named rungs, and are re-derived unchanged by the
   current code. What is left of this item is the direction it did *not* go —
   Construction A over a **shortened** code, and the `D₄`/`E₈` layers below
   `D₂₄`, which are rungs the scaling does not generate.
3. *A cost-aware order, with the theorem it needs.* §4 shows the cheapest order
   is by price, not by position. The theorem to want is the one that says the
   price-sorted order minimises expected work given a distribution over
   resolving rungs — which is a statement about the walk, provable in the same
   file as `firstNamed_order_independent`, and would close the gap this round
   leaves open between the movement the geometry suggests and the schedule the
   cost ledger prefers.
4. *The second half of the note.* Everything about the Monster/moonshine ascent
   and the quasicrystal descent — `E₈ → H₄ → 3D → Penrose`, and the
   `196,884 = 1 + 196,883` embedding — is untouched here.
   `reasoning/monster_stack.py` and `reasoning/moonshine.py` already hold part
   of the left-hand ladder; the right-hand one, the `Φ`-slicing descent, has no
   module at all, and the note's arithmetic for it (`Φ − Φ⁻¹ = 1`, the 120 `H₄`
   roots as `24 + 16 + 84`) is checkable in the same way §1 checked the codes.

**How to re-run any of this.**

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools ladder            # the stored measurement
PYTHONPATH=. python3 -m glm_universal.tools ladder --write    # re-take it (about a minute)
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_construction_ladder.py -q
cd .. && lake build RequestProject.GLM.ConstructionLadder RequestProject.GLM.ScaledLadder
```
