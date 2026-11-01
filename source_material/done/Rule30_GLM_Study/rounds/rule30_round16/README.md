# Round 16: the period-2 rung, weight growth closed, the triangle question, and GLM operators

**Where the prize stands.** All three Rule 30 problems are still open. This round works on the
next steps recorded in Rounds 14–15, on the feedback suggestions, and on your question about the
triangle.

The Lean work is in five new files, all imported by the package root
`RequestProject/GLM/Rule30.lean`:

| File | What it proves |
|---|---|
| `WeightGrowth.lean` | for every `n ≥ 3` the top-degree part of `a(n)` is **one** monomial; weight `2n − 2`, `+2` per step |
| `RunBoundSearch.lean` | a verified pruned search; **exact period-2 run bounds for every left-white row and every `d ≤ 16`** |
| `ConeGeometry.lean` | the seed's triangle; the chiral influence triangle; slices of the 2D lattice cone |
| `LatticeConeFraction.lean` | a lattice light cone fills exactly `1/(2k)` of all directions of `k`-dimensional space-time |
| `WobbleNormalized.lean` | the exact reason to normalise wobble readings as `z = D(N)/√N` |

They are described in rows C170–C184 of `claims.csv` and in the "Round 16" section of the package
README. Everything builds with no `sorry` and no added axioms.

Labels: `FORMAL` = Lean proof; `CERT` = Lean-checked finite computation; `EMP` = computed outside
Lean, not a theorem; `OPEN` = not settled.

---

## 1. The period-2 rung of Problem 1

Round 14 named "the centre column does not eventually alternate" as the first unproved link. By
the stack lift (Round 13) it is enough to show that for every distance `d`, a column at distance
`d` from the black edge of a left-white row can be 2-periodic only for a bounded time `B(d)`.

**New method (`FORMAL`).** In a left-white row, the cells `(t, ℓ + m − t)` form the `m`-th
diagonal parallel to the left edge. Rule 30 reads diagonal `m` from diagonals `m − 1`, `m − 2`
and itself (`evolve_diag_succ`), and diagonal `m` starts with the single cell `x(ℓ + m)`. The
column at distance `d` meets diagonal `d + t` at time `t`. So the row can be chosen cell by cell,
and a branch can be dropped as soon as the column stops being 2-periodic. `searchDead_sound`
proves this pruned search correct for **every** left-white row. It replaces Round 13's
`2^(d+L+1)` enumeration.

**Result (`CERT`).** `runBound_two_upTo_sixteen` and `runBound_two_witness` give the exact bounds,
each attained by an explicit row:

| d | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B(d) | 1 | 7 | 6 | 5 | 5 | 8 | 9 | 9 | 16 | 15 | 14 | 13 | 14 | 16 | 19 | 21 | 25 |

**Further out (`EMP`, `r16_period_runs.c`, same search in C):** `B(17..26) = 24, 23, 35, 34, 33,
32, 31, 31, 30, 34`.

**Two observations (`EMP`).**
- *Barrier diagonals.* `d + B(d)` takes only a few values: `8` (d = 1–3), `24` (d = 8–11), `41`
  (d = 16–18), `54` (d = 19–23), `55` (d = 24–25), `60` (d = 26). Within a block every longest run ends on the
  same left diagonal. A proof could try to explain why these diagonals cannot be crossed.
- *Linear growth.* All values satisfy `B(d) ≤ 2d + 7`. This is stated as the open target
  `PeriodTwoLinearBound`. `leftWhiteAperiodic_two_of_linearBound` proves that it would settle
  the period-2 rung for every left-white row, including the seed.

As before (`no_finite_certificate_problem1`), no finite table can settle the infinite statement.
These certificates cover the first 17 rows of the seed's stack.

## 2. Feedback item: "prove the right-cone weight growth lemma"

Part of this premise is out of date. The degree formula `deg a(n) = 2n − 1` and the presence of
`M_n = x_{2−n} ⋯ x_n` were proved for all `n` in Round 8 (`TopMonomial.lean`). The step still
missing was uniqueness: that `M_n` is the *only* top-degree monomial. It had been checked only for
`3 ≤ n ≤ 6`. It is now proved for every `n ≥ 3` (`topMonomial_unique`, `FORMAL`):

- no top-degree monomial contains `x_{−n}` (cone separation);
- **new:** none contains `x_{1−n}`. The derivative in that variable is a sum of cells of earlier
  rows, each of degree at most `2n − 3` (`anfCoeff_second_left_small`);
- that leaves exactly the `2n − 1` positions of `M_n`.

So the top-degree part of `a(n)(c)` is exactly `x_{c+2−n} ⋯ x_{c+n}`, with weight `2n − 2` growing
by exactly `+2` per step (`topDegree_weight_growth`). Layer 4 is closed.

**Correction to the feedback.** This does **not** unlock Problems 1 or 3. The degree and weight
are properties of the `n`-step map over all starting rows. The all-white row has the same map and
a periodic centre column (error E2, `map_properties_cannot_decide_periodicity`, since Round 3).

## 3. Feedback item: the early-time transient in the first 2^17 steps

`r16_transient.py` (`EMP`) counts Round 14's near-constant 24-bit windows in three ways. It uses
2000 fair-coin sequences per segment as the reference.

| statistic, first 2^17 steps | Rule 30 | fair-coin mean (sd) | z |
|---|---|---|---|
| W: qualifying windows (Round 14's count) | 125 | 35.8 (13.8) | +6.5 |
| C: clusters (separate events) | 27 | 13.8 (4.2) | +3.1 |
| M: longest cluster | 17 | 7.9 (3.4) | +2.7 |

**Reading.**
- *Mostly an overlap effect.* One long almost-white stretch, for example 40 cells with 6 black at
  `t = 100013`, produces many overlapping windows. Counting separate events reduces the excess from
  `z = 6.5` to `z = 3.1`.
- *Not significant after correction.* Among the 32 segments the largest independent-event excess
  is this one, and another segment (21) reaches `z = 2.7`. Allowing for the 32 segments looked at,
  and for a statistic chosen after seeing the data, a value like this is not significant (roughly
  5–6%).
- *The longest cluster is not special.* Segments 3 and 18 have equally long or longer clusters.

**Conclusion:** the data show no relaxation of the seed into a different regime. The "transient"
is mostly a counting artefact plus a mild fluctuation. In any case an initial transient cannot
bear on Problems 1–3, which concern the infinite tail.

## 4. Your question: the triangle, its angle, circle or cone in a sphere?

**Short answer.** For Rule 30 the triangle *is* the whole light cone. It is not a slice of
anything, because Rule 30 has one space dimension and its space-time is two-dimensional. Lattice
rules never give a round circle or a round cone: their cones are pyramids, and the angle you see
depends on how you slice and scale them. Each statement below is proved.

**(a) Rule 30's dependency triangle (`seed_pattern_triangle`).** From one black cell the pattern
fills exactly `|i| ≤ t`, and both corners are always black. With square cells the apex angle is
`90°` (`face_slice_angle`).
- Counted over the full circle of directions around the apex, the future triangle takes `90°`,
  the past (dependency) triangle `90°`, and the remaining `180°` is "space-like".
- So the empty space around the downward triangle is `270°` of `360°`, or `90°` of the `180°`
  below the seed.

**(b) Rule 30's influence triangle is lopsided.** This is where the "arrow" lives.
- If you flip one cell, the change always reaches `(n, j + n)` on every row: the right side is a
  rigid `45°` ray (`influence_right_ray`).
- The left side is not fixed. It can run at full speed (white background,
  `influence_left_ray_fast`) or not move at all (behind a wall, `influence_left_ray_stalls`).
- On random rows its average speed is `0.243` (`EMP`, `r16_damage_cone.c`, 100 trials to
  `t = 8192`). That is about `13.7°` from the time axis, so the typical influence triangle has an
  apex of about `58.7°` and leans right.
- This asymmetry gives a direction. Information spreads rigidly to the right, while columns are
  *read* (determined) from the right towards the left (`columns_determine_left`). That fits your
  idea of the wobble as a read position or perspective: the triangle's tilt tells the observer
  which way it is looking.

**(c) Higher dimensions: a cone inside a sphere, but a square one.**
- A 2D rule with the usual 3×3 neighbourhood has the space-time light cone
  `max(|x|, |y|) ≤ t`: a square pyramid (`mooreCone`).
- Its vertical slices are triangles whose apex angle depends on the direction `θ` of the slice
  (`moore_slice_mem`, `moore_slice_factor_bounds`). It is `90°` for a slice parallel to a face and
  `2·arctan √2 ≈ 109.47°` for a diagonal slice, where `cos = −1/3`, the tetrahedral angle
  (`diagonal_slice_angle`).
- So when Rule 30 is viewed as a slice of a 2D rule, its triangle is one particular slice of a
  pyramid.

**(d) How much of the sphere does a lattice cone fill? (`lightCone_ball_fraction`).** In
`k`-dimensional space-time the light cone of a radius-one rule fills exactly `1/(2k)` of all
directions:
- `1/4` for Rule 30 (`k = 2`, the `90°` above);
- `1/6` for a 2D rule (`k = 3`, solid angle `2π/3`): the cone is one of the six pyramids that cut a
  cube from its centre.

The proof is general (`axisCone_fraction`). The `2k` cones around the coordinate axes are images
of one another under coordinate swaps and sign changes, they cover everything, and they overlap
only on a null set.

## 5. GLM platform items

**Normalisation operator (`WobbleNormalized.lean`, `FORMAL`, plus
`glm_glm_universal/reasoning/wobble_normalize.py`).**
- Over all `2^N` words of length `N`, the raw carrier satisfies `Σ D² = N·2^N`
  (`sum_wordWobble_sq`), so its typical size grows like `√N` and raw readings at different `N` are
  not comparable.
- The normalised carrier `z = D/√N` has mean square exactly `1` for every `N`
  (`mean_sq_zScore`).
- At most a fraction `1/λ²` of words have `|z| ≥ λ` (`card_large_zScore_le`).
- The Python operator is exact: it carries `z² = D²/N` as a fraction. Example: `D(10⁶) = 1536`
  gives `z = 1.536`, and `D(10⁷) = 4440` gives `z = 1.404`. The raw value grew, but the normalised
  reading fell.

**Structured reading for `discuss`
(`glm_glm_universal/reasoning/theorem_wheel_round16.py`).** This replaces
first-keyword routing. A question is read into slots: property (periodicity, frequency, wobble,
cost, degree, geometry), claim form (bound, limit, equivalence, existence), object and rung.
- *Routing rules.* A bound or limit on the wobble or frequency goes to Problem 2. "Period of
  time" and "over time" are treated as context. Cost words count only with a computing verb.
  Questions about the n-step map carry the E2 warning. Cone questions go to the geometry results.
- *Ambiguity.* When two targets score close, the router asks instead of guessing.
- *Wheel additions.* The Round 16 statements, spokes, evidence and axiom footprints are added
  (`extend()`).
- *Tests.* `test_round16.py` has 8 routing cases. The old router misroutes 2 (the wobble question
  that says "period of time" goes to P1, and the ambiguous "is the frequency periodic?" is silently
  sent to P1) and refuses 2 (the `D(N)/√N` bound question and the light-cone angle question). The
  new reading gets all 8 right.

## What the GLM should say

* "Period 2: the exact run bounds are certified for `d ≤ 16` and grow roughly linearly. A uniform
  bound such as `2d + 7` would settle the rung; it is open."
* "The top-degree part of `a(n)` is one monomial of weight `2n − 2`. This is a fact about the map,
  not about the seed."
* "Rule 30's triangle is its whole light cone, `90°`. The influence triangle leans right: a rigid
  `45°` right side and a variable left side, `≈ 13.7°` on typical rows. Lattice cones are
  pyramids that fill exactly `1/(2k)` of all directions, never round cones."
* "Compare wobble readings as `z = D/√N`, never raw."

## Files

| File | Purpose |
|---|---|
| `r16_period_runs.c`, `r16_period2_runs_output.txt` | exact longest 2-periodic runs by the diagonal search (`./r16_period_runs 2 26 150`); also prints witness rows |
| `r16_transient.py`, `r16_transient_output.txt` | the 2^17 transient: windows vs clusters vs longest cluster, 32 segments, fair-coin reference (needs the centre column from `../rule30_round15/r15_columns.c`) |
| `r16_damage_cone.c`, `r16_damage_cone_output.txt` | the influence triangle on random rows |
| `glm_glm_universal/reasoning/wobble_normalize.py` | normalisation operator |
| `glm_glm_universal/reasoning/theorem_wheel_round16.py` | structured reading, Round 16 wheel additions |
| `test_round16.py`, `test_round16_output.txt` | tests for both |
