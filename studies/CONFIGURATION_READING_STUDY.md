# The configuration reading — the 28-vertex pair of lattice item 6

## Tier 0 — the coarse read

**Question.** Does a reading of the vertex *configuration* the ensemble reached — which vertices are joined in the hole's affine diagram, weighted by share — separate `E_6^4` from `D_6^4`, and every other pair of reference holes, with `ρ = 2W/B < 1`?

**Verdict.** Yes. The configuration reading separates every pair of reference holes: at 30720 starts the ratio is 0.1261, the per-hole criterion certifies all 10 holes, E_6^4 and D_6^4 included, and the criterion holds with the gate passed at every size from 1920 on. The pair that sorting could not tell apart sits 0.5768 apart, near the uniform-limit 4/7 the Lean file proves; the closest pair is E_8^3/D_8^3 at 0.4351, near its proved limit 4/9. Lattice item 6 is closed for the reference holes.

**Deciding figure.** 6 of 6 marks met (K1–K6); `ρ = 0.1261` at `(L5, 30720)`; per-hole certificate 10 of 10; control 20 of 20 diagrams; bound 80 of 80; 12 theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.reasoning.configuration_reading.configuration_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the module that takes the
measurement and before the Lean file exist. §§0–6 are as they were
committed; §7 is what came out.

[`SHARE_SEPARATION_STUDY.md`](SHARE_SEPARATION_STUDY.md) §7 left lattice item
6 narrowed to one pair: up to 30720 starts no share-carrying rung reaches
`ρ < 1`, and the per-hole criterion certifies every reference hole but
`E_6^4` and `D_6^4`. Both have 28 vertices, and once every vertex's share is
near `1/28` a *sorted* list of shares has nothing left to tell them apart.
§7.8 named the repair: a reading that keeps what sorting throws away — how the
reached vertices sit relative to one another.

**Order of work, stated plainly.** Phase 121's tables were read before this
was written, and so was the classical fact the reading rests on (the vertices
of a deep hole of type `X` form the affine Dynkin diagram of `X`, two vertices
joined by one edge when their squared distance is `3/2` of twice the
covering-radius norm, by two when it is twice it, and orthogonal otherwise).
The reading's value *in the limit of uniform shares* was worked out by hand
from that fact (§3) before any line of code. **No configuration reading of
any stored ensemble had been computed when this was committed.**

## 1. What is used rather than re-derived

* The ten reference holes, their labels, centres and declared vertex sets,
  and the two seeds: `deep_hole_escalation.reference_entries`, unchanged.
* The ensembles: `share_ensemble`'s stored sufficient statistics (every
  emitted point with its exact squared distance and count, at the eight sizes
  240 … 30720), unchanged and not re-taken. The configuration reading is a
  function of that multiset, so no decode is run.
* The cell's statistics (`Q₀`, `W`, `B`, `ρ`, the per-hole ratio) exactly as
  `share_separation.cell` computes them; only the profile and its metric are
  new.

## 2. The reading

For an emission record, let `V` be the **arrival vertices** — the emitted
points at the minimum squared distance `r²` seen — with their arrival shares
`s_v` (exactly the vertices and shares the `L₁` profile sorts). Join two
arrival vertices `u, v` with **multiplicity** `m(u, v)`:

* `m = 1` when `|u − v|² = 3r²` (inner product `−r²/2` about the centre),
* `m = 2` when `|u − v|² = 4r²` (inner product `−r²`),
* `m = 0` otherwise.

This is computed from the emitted points alone, in exact integers; the centre
is not needed. Each arrival vertex gets the **key**

> `κ(v) = (number of arrival vertices in v's connected component, Σ_u m(u, v))`

— the size of its component of the diagram and its degree counted with
multiplicity. The **configuration profile** is the pushforward of the shares
along `κ`: the map `key ↦ Σ_{κ(v) = key} s_v`. Two profiles are compared in
L1 over the union of their keys. Call this rung **`L₅`, the configuration
reading**. It is a function of the record, it does not depend on how the
vertices are listed, and its metric is a pushforward L1, so it obeys the
triangle inequality `GLM.DeepHoleLadder.Reading` asks of a rung.

**Why it should see the pair.** In the affine diagram `Ẽ_6` (7 nodes) three
nodes have degree 1, three degree 2 and one degree 3; in `D̃_6` (7 nodes) four
have degree 1, one degree 2 and two degree 3. With uniform shares the two
profiles are `(7,1) ↦ 3/7, (7,2) ↦ 3/7, (7,3) ↦ 1/7` and `(7,1) ↦ 4/7,
(7,2) ↦ 1/7, (7,3) ↦ 2/7`, at L1 distance **4/7**. A sorted share list sees
the same pair at distance `0` in that limit.

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| K1 | The Lean file builds with no `sorry` and only the standard axioms, and proves (a) the pushforward of two share vectors along any key map is non-expansive in L1, so the configuration reading's seed shift is at most the vertex-matched shift; (b) the uniform-limit profiles of `Ẽ_6` and `D̃_6`, from their adjacency, and their L1 distance `4/7`; (c) a separation floor: two configuration profiles are at least `4/7 − δ_E − δ_D` apart when their vertex-level departures from uniform are `δ_E`, `δ_D`. |
| K2 | **Control: the diagram is read correctly.** At 30720 starts, for all ten holes and both seeds, the arrival vertices are exactly the declared vertex set, and the components of the multiplicity graph are the affine diagrams of the label (component sizes and degree sequences equal to those of the declared root system). |
| K3 | **The bound holds where it is measured.** At every hole and all eight sizes, the configuration seed shift is at most the vertex-matched share shift (an instance of K1(a), exact arithmetic). |
| K4 | **The primary question.** `ρ < 1` at `(L₅, 30720)`. |
| K5 | **The pair is certified.** At `(L₅, 30720)` the per-hole criterion certifies all ten holes, `E_6^4` and `D_6^4` included. |
| K6 | **Stability.** At `L₅`, `Q₀ = 10` and `ρ < 1` at every size from 1920 to 30720. |

**What each outcome means.** K4 met closes lattice item 6 with the criterion's
guarantee (`nearest_correct`): the nearest-reference reading of `L₅` is then
certified for every query within `W` of its reference. K5 met without K4 still
closes the 28-vertex pair. K4 missed is a measured boundary, reported with the
smallest `ρ` reached.

**The prediction, stated as a number before it is taken.** In the uniform
limit the closest pair of references under `L₅` is `E_8^3`/`D_8^3`, at
`4/9 ≈ 0.444` (their 9-node diagrams have degree counts `3, 5, 1` and
`4, 3, 2`); `E_6^4`/`D_6^4` is at `4/7`, and every other pair differs in its
component sizes and is at least `17/13` apart. The seed shift is at most the
vertex-matched shift, which Phase 121 measured at 30720 starts as at most
about `0.09`; the pushforward should shrink it further. Predicted: `B` about
`0.44` and `ρ` between `0.1` and `0.5` at 30720 starts. At 240 starts some
vertices may be unreached, which changes the degrees of their neighbours; no
prediction is made below 1920.

## 4. Controls

* **K2** is the control on the reading: if the graph does not recover the
  declared diagrams at the top size, the reading is reporting something other
  than the configuration, and K4–K6 are not read.
* **The vertex-matched shift** is reported beside the configuration shift at
  every cell, as in Phase 121.
* **The multiplicity count.** Phase 121 stood at 36 statistics; the eight
  `L₅` cells make it **44**. No bit score is computed.

## 5. What this round does not do

* It does not re-take or extend the ensembles, change the holes, the seeds or
  the gate.
* It does not change the ladder's four readings, and it does not wire `L₅`
  into the deep-hole classifier's answering path; that is a follow-up if K4
  is met.
* It does not decide whether the *sorted* readings' separation tends to zero
  for equal-count pairs (the other half of the To-Do line); it replaces the
  statistic instead.
* It says nothing about lattice items 3 and 7.

## 6. Files

* `RequestProject/GLM/ConfigurationReading.lean` — K1.
* `overlay/glm_universal/reasoning/configuration_reading.py` — the reading,
  the cells, the control and the report, from the stored ensembles.
* `python3 -m glm_universal.tools configuration-reading` — the report.
* `overlay/glm_universal/tests/test_configuration_reading.py`.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

The reading was applied to the stored ensembles of Phase 121, unchanged
(`python3 -m glm_universal.tools configuration-reading`, about three minutes,
almost all of it the ladder's own `reference_entries`).

### 7.1 The verdict

Yes. The configuration reading separates every pair of reference holes: at
30720 starts the ratio is 0.1261, the per-hole criterion certifies all 10
holes, E_6^4 and D_6^4 included, and the criterion holds with the gate passed
at every size from 1920 on. The pair that sorting could not tell apart sits
0.5768 apart, near the uniform-limit 4/7 the Lean file proves; the closest
pair is E_8^3/D_8^3 at 0.4351, near its proved limit 4/9. Lattice item 6 is
closed for the reference holes.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| K1 | the Lean file, no `sorry`, standard axioms | **met**: `RequestProject/GLM/ConfigurationReading.lean`, 12 theorems (`push_shift_le`, `config_shift_le_matched`, `e6_d6_uniform_distance`, `e8_d8_uniform_distance`, `separation_floor`, `e6_d6_separation_floor`, `e6_d6_separated`, the two degree counts, `diagrams_are_trees` and two lemmas on `l1`); `#print axioms` shows `propext`, `Classical.choice`, `Quot.sound` only |
| K2 | the declared diagrams read back at 30720 starts | **met**: 20 of 20 (hole, seed) pairs — every arrival set is the declared vertex set and its multiplicity graph has the label's component sizes and degree sequence |
| K3 | configuration shift ≤ vertex-matched shift | **met**: 80 of 80 instances (10 holes × 8 sizes) |
| K4 | `ρ < 1` at `(L₅, 30720)` | **met**: `ρ = 0.1261` (`W = 0.0274`, `B = 0.4351`) |
| K5 | the per-hole criterion certifies all ten at 30720 | **met**: 10 of 10; `E_6^4` and `D_6^4` have per-hole ratios 0.0294 and 0.0293 |
| K6 | `Q₀ = 10` and `ρ < 1` at every size from 1920 | **met**: `ρ` = 0.3048, 0.2550, 0.1720, 0.1115, 0.1261 at 1920 … 30720 |

### 7.3 The cells

| starts | `Q₀` | `W` | `B` | `ρ` | per-hole certified | `E_6^4`/`D_6^4` distance |
|---|---|---|---|---|---|---|
| 240 | 10 / 10 | 0.1488 | 0.3831 | 0.7767 | 10 / 10 | 0.5314 |
| 480 | 10 / 10 | 0.1509 | 0.2891 | 1.0437 | 9 / 10 | 0.4856 |
| 960 | 10 / 10 | 0.1187 | 0.3025 | 0.7844 | 10 / 10 | 0.5297 |
| 1920 | 10 / 10 | 0.0578 | 0.3793 | 0.3048 | 10 / 10 | 0.5505 |
| 3840 | 10 / 10 | 0.0526 | 0.4124 | 0.2550 | 10 / 10 | 0.5798 |
| 7680 | 10 / 10 | 0.0348 | 0.4043 | 0.1720 | 10 / 10 | 0.5892 |
| 15360 | 10 / 10 | 0.0238 | 0.4267 | 0.1115 | 10 / 10 | 0.5753 |
| 30720 | 10 / 10 | 0.0274 | 0.4351 | 0.1261 | 10 / 10 | 0.5768 |

The closest pair of references is `E_8^3`/`D_8^3` at every size, as predicted.
The one cell above the criterion is at 480 starts, below the range K6 covers
and the prediction declined to speak for. The spread rose once, from 15360 to
30720 (0.0238 to 0.0274, the `D_16 E_8` hole), so as in Phase 121 the spread
is not monotone in the ensemble size; the ratio stays at a fifth of the
criterion's bound.

### 7.4 Why it works where sorting did not

A sorted share list reads, in the limit, only the vertex count. The
configuration key reads which vertex sits where in the affine diagram, and the
uniform-limit profiles of two holes differ unless their diagrams have the same
component sizes and degree sequences — which no two of the ten reference
holes share. So `B` no longer falls with `W`: it climbs towards its limit
(0.3793 at 1920, 0.4351 at 30720 against `4/9 ≈ 0.4444`) while `W` falls.
`e6_d6_separation_floor` makes the 28-vertex pair's half of this a theorem:
the two profiles are at least `4/7 − δ_E − δ_D` apart, so they stay
separated for every ensemble whose shares are, between the two holes, within
`4/7` of uniform in L1. The prediction (`B` about 0.44, `ρ` between 0.1 and
0.5 at 30720) was met.

### 7.5 What the bound says here

The configuration shift is at most the vertex-matched shift at every instance.
Over the 80 instances the ratio of the two runs from 0 (`A_1^24`, `A_2^12`,
`A_12^2`, where every vertex has the same key, so the profile is a single
point mass) to 0.66 (the largest, at `(E_8^3, 3840)`); at 30720 starts the
configuration shift is at most 0.0274 against matched shifts of 0.03 to 0.05. Holes whose
vertices all share one key are read with zero spread by construction: for
them the reading is the diagram alone.

### 7.6 What is left

* **Wiring `L₅` into the answering path.** The deep-hole classifier still
  names a hole with the ladder's readings; `L₅` is a study instrument. With
  K4 met it is the candidate for the classifier's reading, under a new
  frozen-path comparison.
* **The thirteen unreached Niemeier types** (lattice item 7). Post hoc and
  never a mark: the uniform limit of `L₅` is computable for all 23 types from
  the label alone (`expected_keys`), and `niemeier_uniform_floor` finds all
  253 pairs apart, the closest three being `E_8^3`/`D_8^3` (4/9),
  `D_24`/`A_24` (12/25) and `E_6^4`/`D_6^4` (4/7). So once item 7 supplies
  centres for the other thirteen, `L₅` has a positive floor to read them
  with; whether the ensembles reach their limits fast enough is that round's
  measurement.
* **The multiplicity count** is now 44 statistics; no bit score is computed.
