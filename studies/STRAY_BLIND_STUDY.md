# Which pairs a stray-blind reading must conflate — lattice item 10

## Tier 0 — the coarse read

**Question.** The deep-hole ladder measured that the exact rational distance measure (`L₃`) cannot tell `A_1^24` from `A_2^12`, and `STATUS.md` §3.4 item 10 recorded that as an observation. Which pairs must a reading of distances alone conflate, as a theorem, and does the measured ladder agree with it?

**Verdict.** A reading of distances alone conflates two equal-size records exactly when their stray spectra agree, whatever the hole types: the arrivals all sit at the one covering radius and contribute only their count. A reading blind to the strays as well conflates every deep hole. This is proved in Lean with no `sorry`. On the ladder's own ensembles, the predicted pairs equal the measured pairs at all four sizes: the one pair `A_1^24`/`A_2^12`, the only two stray-free holes. A conflated pair of references also makes the separation criterion fail at every spread, so the `L₃` rung cannot reach `ρ < 1` at any measured size. That is the theorem's bearing on lattice item 6.

**Deciding figure.** 4 of 4 marks met; predicted = measured at 4 of 4 ensemble sizes; 10 of 10 holes at one covering radius (raw squared distance 16); 7 theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.reasoning.stray_blind.stray_blind_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`DEEP_HOLE_ESCALATION_STUDY.md`](DEEP_HOLE_ESCALATION_STUDY.md) found that
under `L₃`, the reference profiles of `A_1^24` and `A_2^12` are identical.
Neither hole emitted a stray over the declared ensemble, so each measure is a
single atom at the covering radius and the rung's separation is exactly `0`.
`STATUS.md` §3.4 named this as lattice item 10: "the theorem to want says
*which* pairs any stray-blind reading must conflate". The roadmap
([`ROADMAP_STUDY.md`](ROADMAP_STUDY.md)) lists items 6 and 10 as theorems to
attempt in Lean, beside round 8. Phase 110 takes item 10, and records what the
result means for item 6.

**Order of work, stated plainly.** The prediction below was first compared
with the ensembles by an exploratory script, before the module and its tests
were written. The marks were therefore declared knowing that the prediction
held on the measured ladder. What the round adds is the **proof**, which does
not depend on the measurement, and a **standing instrument** that re-checks
the prediction whenever its sources move.

## 1. The theorem

`RequestProject/GLM/StrayBlind.lean`, namespace `GLM.StrayBlind`.

An emission record is a list of `(point, squared distance)` pairs, which is
what `deep_hole_escalation.emissions` keeps. A record is read **at a hole of
squared covering radius `r2`** when no emission is nearer than `r2`. That is
what a deep hole is: every emission is a lattice point, and the hole's
vertices are the lattice points at exactly the covering radius. An emission
at `r2` is an *arrival*; any other emission is a *stray*.

| theorem | statement |
|---|---|
| `minimum_eq_radius` | once one start arrives, the minimum distance seen is `r2`, so the measurement's split at the minimum is the split at `r2` |
| `distances_decomp` | the distance multiset is `A` copies of `r2` plus the stray spectrum |
| `distances_eq_iff` | **item 10:** two records of equal size have equal distance profiles exactly when their stray spectra are equal |
| `strayFree_conflate` | any two stray-free records of equal size are conflated |
| `arrivalMeasure_const` | the normalised measure of arrival distances is the point mass at `r2` for every record with an arrival: a reading blind to both the vertex and the strays conflates every pair |
| `distanceReading_indist` | the same for any ladder rung (`GLM.DeepHoleLadder.Reading`) whose distance depends only on the two distance profiles |
| `not_resolves_of_indist` | **bearing on item 6:** a conflated pair of references with different labels makes `Resolves` fail at every `w ≥ 0` |

The arrivals contribute only their count, so a reading of distances alone
cannot tell two holes apart unless their strays differ; §2 shows the measured
pairs agree with this at every size. The answer to "which pairs" is
therefore: **exactly the pairs with equal
stray spectra, at equal ensemble size**. Type plays no part. Every deep hole
of the Leech lattice is at the same covering radius, so the arrivals carry
nothing that tells types apart. Only the strays, the coarse shape of the
Voronoi cell around the centre, can separate two holes under such a reading.
The first deep-hole round excluded the strays from its profile. The theorem
says what that exclusion costs a distance-only reading: everything.

## 2. The marks, and what was measured

`glm_universal.reasoning.stray_blind` reads the same ten reference holes and
the same reference-seed ensembles as the ladder, at every size of
`STARTS_LADDER` (240, 480, 960 and the 1920 extension rung). Everything is
exact. The census is stored beside the digest of its sources
(`python3 -m glm_universal.tools stray-blind --write`, about a quarter of an
hour of exact decoding).

| mark | statement | result |
|---|---|---|
| S1 | the Lean file builds with no `sorry` and the standard axioms only | met |
| S2 | every reference hole reaches the same minimum distance at every size (the theorem's hypothesis) | met: 10 of 10 at 16, at 4 of 4 sizes |
| S3 | the predicted pairs (equal stray spectra) equal the measured pairs (`L₃` distance exactly `0`) at every size | met: 4 of 4 |
| S4 | the measured pair is the one the ladder reported, and the `L₃` ratio is undefined wherever it persists | met: `A_1^24`/`A_2^12` at every size; both are the only stray-free holes; `ρ` undefined at 4 of 4 |

Across the four sizes of the ladder's own ensembles, the arrivals of every
hole sit at the one covering radius. The equal-size pairs that the theorem
proved must be conflated are exactly the measured ones, and the stray-free
pair is the only such pair at every size as well.

`tests/test_stray_blind.py` pins the pure readings on hand-built records
(equal strays at different vertices are conflated, different strays are
separated, stray-free records are all conflated) and the stored census.

## 3. What it means for lattice item 6

Item 6 asks for one of two things: a rung where `ρ < 1`, or a bound proving
that no reading of this family reaches it. The theorem settles the question
for the `L₃` rung. For as long as two references share a stray spectrum,
`not_resolves_of_indist` rules out `ρ < 1` for that rung, whatever the spread.
The census shows that this holds at every measured size.

It does **not** settle the question for the cumulative rungs `L₂` and `L₄`.
Their share part sees which vertex a start reached, so they separate
`A_1^24` from `A_2^12`: at the passing cell, `ρ = 2.59`.
`cumulative_can_break_criterion` already shows that widening can move `ρ`
either way, so no monotone argument closes item 6 for the whole family.
Item 6 therefore stays open, narrowed to the share-carrying rungs.

## 4. What is left

* **Item 6 for `L₂`/`L₄`.** Find a bound on the share part's seed shift, or a
  rung where it falls below the separation.
  *Taken by Phase 121* ([`SHARE_SEPARATION_STUDY.md`](SHARE_SEPARATION_STUDY.md)):
  the bound is proved (sorting is non-expansive in L1), no share-carrying cell
  reaches `ρ < 1` up to 30720 starts, and the per-hole criterion leaves only
  the 28-vertex pair `E_6^4`/`D_6^4`. *That pair taken by Phase 122*
  ([`CONFIGURATION_READING_STUDY.md`](CONFIGURATION_READING_STUDY.md)): the
  configuration reading `L₅` reaches `ρ = 0.1261` at 30720 starts and
  certifies all ten holes.
* **Stray spectra at larger `N`.** The theorem predicts that `L₃` separates
  `A_1^24` from `A_2^12` once either hole emits a stray. Whether some
  ensemble size makes one of them do so has not been measured.
* Items 3 and 7 remain as they were. Both need new pre-registrations.
