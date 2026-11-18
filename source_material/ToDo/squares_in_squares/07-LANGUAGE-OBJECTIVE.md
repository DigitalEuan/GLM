# 07 — The language as an objective, and the stir as a collective move

**Run 40, 2026-11-17.** Follows `06-CRAM-RELAX.md` (run 39, the CRAM
translation). Instrument `scripts/cram_language.py`; ledger
`workspace/push/cram_language.json`.

**What this run asked.** Run 39's reading was that the packing energy is a
*gate, not a landscape*: `E = 0` **is** feasibility, so every feasible packing
is a global minimum and `E` cannot prefer the deeper arrangement. What
separates a grid from a record is which *relations* it uses, and that quantity
is graded (idea A: AUC 1.000 / 0.794; Spearman 0.37–0.74). Two consequences
were proposed and are tested here:

* **PL-1** descend the learned relation cost instead of the hinge —
  `F = E + lam * cbar`, with `cbar` the mean learned cost of the near pairs
  (the instrument idea A was measured with). Two schedules: `graded` applies
  `lam` throughout, `tail` only after 85% of the moves (feasibility first).
* **PL-2** the *stir*: a collective move — a body plus its 4 nearest
  neighbours translated rigidly (rotation about the patch centroid with
  p = 0.3). The move a focused Gibbs step cannot make, and the move run 39's
  n = 240 negative named.

**The score did not move and no packing was found.** 0 of every arm's runs
reached `E <= 1e-6`; the delivered table and `submission.csv` are untouched.
What changed is that the reason is now measured rather than argued.

---

## 1. The instrument check, before any result was trusted

Failure 14 of this project's own ledger: *a heuristic is only trustworthy
after it recovers a known answer.* `--check` runs the new loop at `lam = 0`
and compares against run 39's stored `full` column.

| cell | run 39 stored (median `E`) | this loop at `lam = 0` | match |
| --- | ---: | ---: | --- |
| n = 20, amp 0.01 | 2.333e-03 | 2.333e-03 | yes |
| n = 110, amp 0.04 | 9.208e-02 | 9.208e-02 | yes |

Both agree to 1e-12 and on the recovered count. So the move grammar, the
temperature schedule, the RNG call order and the acceptance convention are
run 39's, and every `lam > 0` difference below is a difference of **objective
alone**.

Two instrument facts recorded rather than hidden:

1. **The inherited acceptance proxy.** Run 39's loop accepts on
   `0.5 * d_local + d_wall` — half the true pair increment — while its
   *absolute* value is `E`. It is reproduced here because that is what makes
   the control exact. It is also the reason `coordinate_polish` recovers 2–8×
   on an annealer endpoint: the chain was not descending `E`, it was
   descending a proxy whose pair term is damped by half. Every number this
   document reports is `cram_relax.energy` on the returned state, never the
   proxy.
2. **A schedule defect found and fixed.** The first `tail` arm restarted its
   incumbent at the objective switch, which discards the annealer's best and
   reads as a failure of the objective. Fixed to score both candidates on the
   same function; the arm was re-run and the ledger holds only the fixed
   version. (The un-fixed numbers are not quoted anywhere.)

---

## 2. The cost has no derivative — the measurement that decides everything

`--slope`: perturb one body of a delivered record by up to `eps` in each
coordinate, and ask whether the mean relation cost moves.

| n | eps | draws with `d cbar` **exactly** 0 | median \|`d cbar`\| | max |
| ---: | ---: | ---: | ---: | ---: |
| 60 | 1e-3 | 0.000 | 9.54e-02 | — |
| 60 | 1e-2 | 0.017 | 9.54e-02 | — |
| 60 | 1e-1 | 0.017 | 9.54e-02 | — |
| 240 | 1e-3 | 0.100 | 1.93e-02 | — |
| 240 | 1e-2 | 0.167 | 1.78e-02 | — |
| 240 | 1e-1 | 0.033 | 1.79e-02 | — |

The typical jump is **the same at every step size** — it does not shrink as
the displacement shrinks. That is the signature of a step function, not of a
smooth one: the six 15° angle bins and three distance bins of width
`(sqrt2 - 1)/3 = 0.138` make `cbar` piecewise constant, so its "gradient" is a
distribution of jumps of order 1e-2, not a derivative that tends to zero.

The hinge energy beside it is quadratic and smooth: at a polish endpoint
`dE` is order 1e-5 per move. So the two quantities differ by ~3 decades in
their smallest step, and the consequence is measured in §3: **there is no
`lam` at which the language acts as a small perturbation.** Above about
1e-3 it decides every acceptance; below it, nothing happens. The crossover is
narrow and there is no regime in between.

Direct test of the saturation, one chain per value (`tail`, n = 110, amp 0.04):

| lam | 0 | 0.1 | 1.0 | 1e3 | 1e6 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `E` | 8.64e-02 | 8.60e-02 | 8.60e-02 | 8.60e-02 | 8.60e-02 |
| `cbar` | 4.096 | 4.039 | 4.039 | 4.039 | 4.039 |

Identical from 0.1 to 1e6: the term is **lexicographic** once it is felt at
all, not a weight.

---

## 3. PL-1 — the graded objective: negative, and structurally so

Matrix identical to run 39: `n in {20, 60, 110, 240}` × amps
`{0.005, 0.01, 0.04, 0.08}`, target = the record's own `L`, 8,000 moves, two
seeds, medians after the annealer and after `coordinate_polish`.

**`graded` (lam throughout).** `lam > 0` beats `lam = 0` on polished `E` in
6 of 16 cells — and the wins are small while the losses are not:

| cell | lam = 0 | best lam > 0 | ratio | `cbar` 0 → best |
| --- | ---: | ---: | ---: | --- |
| n = 20, amp 0.005 | 6.28e-05 | 7.88e-03 (0.01) | **125× worse** | 3.03 → 3.11 |
| n = 20, amp 0.01 | 1.33e-04 | 8.27e-03 (0.1) | **62× worse** | 3.27 → 2.95 |
| n = 240, amp 0.005 | 8.03e-04 | 2.96e-03 (0.1) | 3.7× worse | 3.95 → 3.78 |
| n = 110, amp 0.08 | 1.48e-01 | 1.40e-01 (0.01) | 5% better | 4.14 → 4.13 |
| n = 20, amp 0.08 | 2.92e-02 | 2.74e-02 (0.01) | 6% better | 3.00 → 2.87 |

The language cost falls in 10 of 16 cells, by at most 0.2 on a 3–4 scale
(≤5%) — a trade of 3 decades of feasibility for a few percent of language.

**`tail` (lexicographic after 85%).** Neutral at large `n`, catastrophic at
small `n`, with `lam = 0.1` and `lam = 1.0` identical in 13 of 16 cells:

| cell | lam = 0 (run 39) | tail, lam = 0.1 | ratio |
| --- | ---: | ---: | ---: |
| n = 20, amp 0.005 | 6.28e-05 | 9.69e-03 | **154× worse** |
| n = 20, amp 0.04 | 3.66e-03 | 4.87e-02 | 13× worse |
| n = 60, amp 0.01 | 5.42e-04 | 1.81e-02 | 33× worse |
| n = 110, amp 0.04 | 3.74e-02 | 3.65e-02 | 0.97× |
| n = 240, amp 0.04 | 4.20e-02 | 4.19e-02 | 1.00× |
| n = 240, amp 0.01 | 4.42e-03 | 3.12e-03 (`lam` 1.0) | 0.71× |

**Verdict PL-1 — does not transfer, and the reason is the objective's class.**
A piecewise-constant potential cannot be descended: its local behaviour is a
jump, so "add it with a small weight" has no small-weight regime. The one
place the tail helps (n = 240, amp 0.01, 29% lower `E` at 3% lower `cbar`) is
real but single-cell and two seeds; it is not a mechanism.

---

## 4. PL-2 — the collective stir: a narrow mid-corruption positive

Patch of `k = 4` bodies moved rigidly, equal move budget (so the arm gets 4×
the body displacements — a handicap in its favour). Compared to run 39's
`full` at `lam = 0`:

| cell | full | patch | ratio |
| --- | ---: | ---: | ---: |
| n = 110, amp 0.04 | 3.74e-02 | **2.40e-02** | **0.64×** |
| n = 240, amp 0.01 | 4.42e-03 | **1.39e-03** | **0.31×** |
| n = 20, amp 0.04 | 3.66e-03 | 4.73e-03 | 1.29× |
| n = 240, amp 0.08 | 2.91e-01 | 3.51e-01 | 1.20× |

2 cells better (>25%), 13 the same (±25%), 1 worse. Every other cell sits
within noise of `full`.

**Verdict PL-2 — first proposal-grammar change in this project to beat
one-body descent anywhere, and it does not beat it generally.** The two wins
are exactly the mid-corruption, large-`n` cells where run 39's idea D also
won — a consistent location, which is worth more than the sizes. It loses at
heavy corruption, where a rigid patch of 4 cannot do the work and its 4×
displacement budget is spent on coordinated motion in the wrong direction.
No patch chain reached a gated `L` and none reached a fixed point.

---

## 5. What is not shown

* **Two seeds, medians, no error bars.** The 5–10% differences above carry no
  significance claim; only the >25% ones are called out, and only the
  n = 240, amp 0.01 patch win is larger than 2×.
* **No run reached feasibility.** 0 recovered at `E <= 1e-6` in every arm, as
  in run 39 — the relaxation never gets near a packing, so these are descent
  rates at equal budget, not solvers.
* **`cbar` is the idea-A table as fitted** (rows `n <= 120`, six angle bins,
  three distance bins, `-log` histogram). A smoothed or refit potential is a
  different objective and none of these numbers transfer to it.
* **The patch arm's budget is not matched.** Equal *moves*, 4× displacements.
  A matched-displacement run is the clean comparison and has not been done.
* No Lean, no intake, no GLM claim. The score is unchanged.

---

## 6. What the run says to build next

1. **A C¹ relation potential (PL-10).** The failure is the objective's class,
   not its weight. Replace the histogram with a kernel density over the
   21,602 contacts — Gaussian in `(d theta, d)` with bandwidths at the bin
   widths — so `-log p` is differentiable, and a descent on it is well posed.
   That is the one change the measurement actually calls for.
2. **The seam at the three top aims.** 356 / 395 / 355, worth 0.0111 / 0.0107 /
   0.0104 each; the measured seam is a thin 16.7-unit² band across 51
   orientations, not a grid hole.
3. **The stir at matched displacement.** `k = 4` at `moves / 4`, to remove the
   4× budget before the mid-corruption win is believed.

---

## 7. PL-10 — the C¹ potential: the first objective-level positive

The step function failed because it has no slope (§2). So the same 21,602
contacts were refitted as a **probability density** on a 360 × 240 grid over
(relative angle, contact distance), smoothed with a Gaussian of one half-bin
bandwidth (σ = 30 bins in angle, 40 in distance), and used as
`U = -log p` with bilinear interpolation. Fit: 0.4 s. The gradient is then
nonzero everywhere, and `lam` has a genuine range.

Polished `E`, ratio to this arm's own `lam = 0` (which reproduces run 39 —
recovery test still exact after the refactor):

| n | amp 0.005 | amp 0.01 | amp 0.04 | amp 0.08 |
| ---: | ---: | ---: | ---: | ---: |
| 20 | 1.03× | 1.01× | **0.18×** (lam 100) | **0.23×** (lam 1000) |
| 60 | 1.00× | 0.92× | **0.50×** (lam 100) | **0.70×** (lam 100) |
| 110 | 1.00× | 1.00× | **0.59×** (lam 1000) | 0.95× |
| 240 | 1.00× | **0.31×** (lam 0.1) | **0.76×** (lam 1000) | 0.97× |

Ten of sixteen cells improve, the best by **5.9×**; and the language cost falls
with the energy in every improving cell, so it is not a trade — unlike §3,
where every gain was bought with feasibility.

**The regime is measured and it is not uniform.** Every gentle-corruption cell
(amp 0.005, 0.01) is *inert* (1.00–1.03×): the delivered records sit at the
density maximum, so `U`'s gradient there is ~0 by construction and `lam` has
nothing to act on. Every mid/heavy cell acts. And the *wrong* `lam` at gentle
corruption is expensive — 8.7× at (n = 20, amp 0.005, lam 10) and 17.8× at
(n = 110, amp 0.005, lam 1). A fixed weight is therefore the wrong object:
`lam` must be scheduled by how far the seed is from the language, which is
what `cbar` itself measures.

**Verdict PL-10 — stands, as a schedule, not as a constant.** The objective's
class was the obstruction, exactly as §2 said; once it is C¹, the language
does work beside the hinge. The condition is that its weight tracks the
corruption.

## 8. PL-2 at matched displacement — the caveat closes

Same patch move, `moves / 4` = 2,000 (so total body displacements match the
one-body arms):

| cell | full | patch, 8,000 | patch, 2,000 (matched) | ratio to full |
| --- | ---: | ---: | ---: | ---: |
| n = 110, amp 0.04 | 3.74e-02 | 2.40e-02 | 2.38e-02 | **0.64×** |
| n = 240, amp 0.01 | 4.42e-03 | 1.39e-03 | 1.39e-03 | **0.31×** |
| n = 20, amp 0.08 | 2.92e-02 | 2.52e-02 | 2.23e-02 | 0.76× |
| n = 110, amp 0.08 | 1.48e-01 | 1.83e-01 | 1.74e-01 | 1.18× |
| n = 240, amp 0.08 | 2.91e-01 | 3.51e-01 | 3.55e-01 | 1.22× |

**The mid-corruption wins survive at a quarter of the budget** — n = 240,
amp 0.01 returns 1.385e-03 at both budgets, i.e. it had converged. So the
§4 wins were not bought with the 4× displacement. The heavy-corruption losses
are real and unchanged (1.18×, 1.22×).

**Verdict PL-2 — a measured narrow positive at matched budget**, in the
mid-corruption large-`n` corner, and a measured loss at heavy corruption.

## 9. What this does not show: the contact word is never recovered

Three cells re-run with the record in hand — the record's own contact set
(pairs with `|pen| <= 1e-6`) compared to the result's:

| cell, arm | `E` polished | contacts (record) | Jaccard with record | mean nearest-body distance | bbox vs target `L` |
| --- | ---: | ---: | ---: | ---: | --- |
| n = 20, amp 0.04, lam 0 | 3.89e-03 | 0 (55) | 0.000 | 0.0200 | 5.0484 / 5.0000 |
| n = 20, amp 0.04, lam 100 | **6.55e-04** | 1 (55) | 0.018 | 0.0199 | **5.0081** / 5.0000 |
| n = 240, amp 0.01, lam 0 | 3.66e-03 | 32 (669) | 0.048 | 0.0079 | 16.0021 / 15.9697 |
| n = 240, amp 0.01, lam 0.1 | **1.23e-03** | 36 (669) | 0.054 | **0.0032** | **15.9829** / 15.9697 |
| n = 110, amp 0.04, lam 0 | 3.49e-02 | 13 (285) | 0.042 | 0.0296 | 11.1281 / 10.9968 |
| n = 110, amp 0.04, lam 1000 | **1.73e-02** | 6 (285) | 0.021 | **0.0163** | 11.0615 / 10.9968 |

Two things follow, and the second is the important one.

1. **The win is real and it is metric.** The bounding box moves toward the
target `L` in every arm (n = 20: 5.048 → 5.008 against 5.000), and at
large `n` the bodies end up **1.8× and 2.5× closer to the record's own
positions**. So the language term does recover geometry, not just tidiness.
2. **The contact word is never recovered.** The Jaccard overlap with the
record's contact set is 0.018–0.054 in every run — six contacts out of 285,
36 out of 669. No chain in run 39 or run 40 has ever reproduced a record's
contact graph, at any energy. The relation language is a *shape prior* that
pulls toward contact geometry; it is not a decoder of the record.

That is the strongest statement this leg produces, and it is consistent with
the 0-of-96 and 0-of-224 feasibility counts: the target `L` is reachable only
by an arrangement the descent never visits, not by polishing the neighbourhood
of one it does.

---

## 10. PL-11 — the weight as a rule, and what best-of-seven was worth

**The objection, stated first.** §7's table picks the best of seven λ per cell
and then reports the ratios. That is selection on the test set: any estimator
with seven chances per cell looks good. The number in §7 is therefore an
*upper bound produced by cheating*, and this section replaces it.

### The rule

```
lam(seed) = (excess / e0)^2 ,   excess = cbar_smooth(seed) - cbar_smooth(record)
```

One parameter, `e0`. The square is the shape a density maximum gives — near
the maximum the potential rises quadratically with the departure, so a force
that tracks the departure grows quadratically in the excess — and the input is
computed from the seed and the record alone, never from an outcome.

**`e0` is fitted on cells disjoint from the test cells**: `n in {30, 80, 150,
300}` × amps `{0.02, 0.06}`, λ grid `{0.1, 1, 10, 100, 1000}`, and the
predicted λ read off that measured grid by log-log interpolation. Fit:
**e0 = 0.3162**, mean |log ratio| 0.075 on the eight training cells (691 s).

Training cells, ratio of polished `E` to λ = 0:

| n | amp 0.02 (excess ≈ 0.045–0.067) | amp 0.06 (excess ≈ 0.26–0.35) |
| ---: | --- | --- |
| 30 | 0.61 / 0.61 / 0.79 / 0.67 / **0.54** | 0.80 / 0.86 / 0.35 / **0.32** / 0.38 |
| 80 | 0.96 / 0.91 / 0.92 / 0.78 / **0.60** | 0.91 / 0.88 / 0.71 / **0.50** / 0.51 |
| 150 | 0.72 / 0.81 / 0.40 / 0.33 / **0.23** | 1.01 / 0.96 / 0.96 / **0.84** / 0.84 |
| 300 | 1.10 / 0.97 / 0.96 / 0.68 / **0.59** | 1.03 / 1.02 / 1.02 / **0.97** / 0.98 |

(columns are λ = 0.1, 1, 10, 100, 1000; **bold** = best.)

### The honest number

One λ per cell, no choice, all 16 cells:

| | geometric mean ratio | median | cells ≥5% better | cells ≥5% worse | best | worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| best-of-seven (§7, **biased**) | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| fitted rule (honest) | **0.898** | 0.977 | **5** | **1** | **0.417** | 1.055 |

The selection was worth **0.75× of the honest figure**: §7 read as a 33%
reduction in polished `E`, the unbiased value is **10%**. Per cell the rule
gives 1.03, 0.95, 0.81, **0.42**, 1.00, 1.00, 0.96, 0.96, 1.00, 1.00, 1.00,
0.91, 1.00, **0.67**, 0.93, 1.05 — so the effect is real, concentrated in the
heaviest cells (n = 20, amp 0.08 → 0.42×; n = 240, amp 0.01 → 0.67×), and
absent in the gentle ones, as §7 predicted.

### Why the rule undershoots, and the next fit

`e0 = 0.316` puts λ at **0.001–4.3** across the test range, while the measured
optima there were **100–1000** for excess ≥ 0.10 — a two-decade undershoot. The
cause is visible in the training table: those plateaus are *flat* (λ = 10 …
1000 all land inside 1.05× of the best), and a mean-log-ratio fit goes to the
middle of a flat region rather than to the intersection that generalises.

So the shape may be right and the *criterion* wrong. The declared next fit
(PL-13): same disjoint grid, same form, but **minimise the maximum |log ratio|
over the training cells** instead of the mean — a min-max fit seeks the
intersection of the plateaus rather than their centre — then re-test the same
16 cells, once, with no further change.

### PL-12's first run: aiming below the record is still null

The rule applied at a squeezed target `L0 (1 - d)`, `d in {0.01, 0.02}`, amp
0.02, four `n`:

| n | λ chosen | d = 0.01 | d = 0.02 | gated `L` | below record |
| ---: | ---: | ---: | ---: | --- | --- |
| 20 | 0.040 | 1.08× | 1.05× | none | no |
| 60 | 0.033 | 1.00× | 0.98× | none | no |
| 110 | 0.013 | 0.96× | 1.00× | none | no |
| 240 | 0.008 | 0.87× | 0.96× | none | no |

**0 of 8 cells produced a gated `L` at all**, so the question "is there a
packing below the record" is not merely unanswered, it was never reached —
the same wall as run 39's 0-of-24. And the test is weak by construction: the
fitted rule puts λ at 0.008–0.04 here, i.e. the language term is effectively
off, so these eight runs are close to a λ = 0 control. **The push question
stays open until PL-13 produces a rule whose λ is actually engaged at
`excess ≈ 0.03`.**

---

## 11. PL-13 — the min-max refit, and the reason it fails

### Two things were wrong with §10's fit, and only one was the criterion

**First, the mean-|log ratio| criterion is degenerate.** At λ → 0 every cell's
ratio → 1.0, so |log ratio| → 0 and the criterion is minimised by *switching
the term off*. Measured on the stored grid: mean |log ratio| is **0.282** at
the fitted `e0` and **0.072** at `e0 = 10` — the objective falls as λ falls,
which is why §10's fit chose the top of its own range (0.3162 = 10^-0.5, the
boundary). The 0.898 honest number therefore came from a rule fitted to do
nothing.

**Second, the fits sit at boundaries in both directions.** Refitting the same
stored grid by **min-max regret** (regret = the log distance from each cell's
own best λ, so "do nothing" is not free) put `e0` at the *other* boundary,
10^-4, giving λ = 10^4 on all eight cells — an extrapolation past the largest
measured λ. So the grid was measured upward (`λ = 10^4, 10^5`) and the refit
repeated. It stayed at 10^4, correctly:

| n | amp 0.02: ratios at λ = 0.1 … 10^5 | amp 0.06: ratios at λ = 0.1 … 10^5 |
| ---: | --- | --- |
| 30 | 0.61 / 0.61 / 0.79 / 0.67 / 0.54 / **0.49** / **0.40** | 0.80 / 0.86 / 0.35 / 0.32 / 0.38 / **0.30** / **0.28** |
| 80 | 0.96 / 0.91 / 0.92 / 0.78 / **0.60** / 0.64 / 0.65 | 0.91 / 0.88 / 0.71 / **0.50** / 0.51 / 0.54 / 0.53 |
| 150 | 0.72 / 0.81 / 0.40 / 0.33 / **0.23** / 0.23 / **0.21** | 1.01 / 0.96 / 0.96 / 0.84 / 0.84 / **0.82** / 0.85 |
| 300 | 1.10 / 0.97 / 0.96 / 0.68 / 0.59 / **0.57** / **0.55** | 1.03 / 1.02 / 1.02 / **0.97** / 0.98 / 0.98 / 1.00 |

Minimum of 0.87–0.97 reached at λ ≥ 10^4 on most cells, so min-max regret
legitimately chooses the largest λ available: `e0 = 1e-4`, **max regret 0.087**,
λ = 10^4 on all eight. The rule is **saturated**: it is no longer a rule in the
excess at all, it is "the language decides everything".

### The honest re-test, with the term fully engaged

| | geo mean ratio | median | ≥5% better | ≥5% worse | best | worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| best-of-seven (§7, biased) | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| mean-\|log\| rule (§10) | 0.898 | 0.977 | 5 | 1 | 0.417 | 1.055 |
| **min-max rule, λ = 10^4** | **1.143** | 0.981 | 8 | 7 | 0.255 | **10.60** |

Split by corruption, the reason is plain:

| amp | ratios (n = 20, 60, 110, 240) | geo mean |
| ---: | --- | ---: |
| 0.005 | 4.09 / 1.35 / 10.60 / 2.80 | **3.57× worse** |
| 0.01 | 1.69 / 1.07 / 5.22 / 0.49 | 1.47× worse |
| 0.04 | **0.25 / 0.47 / 0.63 / 0.74** | **0.49×** |
| 0.08 | **0.27 / 0.75 / 0.94 / 1.03** | **0.67×** |

A maximally engaged language term is the best objective this project has for
mid and heavy corruption — 2.0× and 1.5× lower polished `E` at equal budget
— and it **wrecks gentle corruption**, up to 10.6×. Net effect: 14% worse.

**Why the fit could not see that: the training grid had no gentle cell.**
It was built at amps 0.02 and 0.06, i.e. excess 0.045–0.35. The test set
contains excess 0.003–0.024, and nothing in the fit was paying for that
regime, so min-max bought mid/heavy gains with gentle losses at zero fitted
cost. **The failure is the grid's coverage, not the criterion.**

### And the push? Still null, now with the term actually engaged

λ = 10^4 at every cell (`excess ≈ 0.03`), squeezed targets:

| n | d = 0.01 | d = 0.02 | gated `L` | below record |
| ---: | ---: | ---: | --- | --- |
| 20 | 1.08× | 1.12× | none | no |
| 60 | 0.82× | 0.89× | none | no |
| 110 | 1.34× | 1.22× | none | no |
| 240 | 0.76× | 0.93× | none | no |

**0 of 8 produced a gated `L`; 0 of 8 went below the record.** The earlier
run's null was weak — the term was off — so this is the answer the question
needed: with the language fully driving the descent, at a 1% squeeze the
sampler still never returns a pairwise-clear state. The wall is mechanical,
not a matter of how the objective is weighted.

### The owner's suggestion: train on known optimal packings up to 10,000

Two local facts, both measured (`proven_census`, ledger):

1. **There are no packings above n = 1000 in this tree.** The delivered table
is rows 1..1000; a training grid "up to 10,000" would need 9,000 rows of
optimal packings that do not exist here.
2. **The solved examples we do have are the vacuum.** The 156 proven-optimal
rows (`root_audit38.json` → `proven_floors`, n ∈ [1, 961], 193,742 contacts)
sit **99.99%** in the two lattice relation cells — against 96.07% for all rows
n ≤ 120. Training the relation language on them fits the two cells it already
knows and learns nothing about seams.

And a structural point, which is the real answer: **at an un-corrupted optimal
packing the excess is 0 by definition, so the rule's own form assigns λ = 0.**
A training grid of optimal packings therefore measures the term at the one
place where it is provably inert. What the idea needs is optimal packings used
as *seeds* under corruption that spans the deployment range — which is a
better grid than §10's (solved examples rather than arbitrary rows) and is
logged as PL-14.

---

## 12. PL-14 — the proven grid, the lifted clamp, and the first rule that beats control

**The protocol, once.** Rebuild the training grid from the **proven-optimal
rows** (`proven_floors`) across an amp ladder that reaches into the gentle
regime; lift the 1e4 clamp so the min-max fit is not boundary-constrained;
then fit once, freeze, and test the 16 cells and the below-record targets
once.

### The grid

| | |
| --- | --- |
| rows | **n = 13, 32, 45, 60, 76, 96, 120, 143** — all proven optimal |
| amps | **0.002, 0.005, 0.01, 0.02, 0.06** (excess 0.003 … 0.30) |
| λ | 0, 1, 10, 100, 1e3, 1e4, 1e6, 1e8 |
| seeds | 1 (the test keeps 2) |
| clamp | 1e12 in the rule and the fit; e0 candidates 1e-9 … 1e2 |
| cost | 320 chains + refit + 16 + 8 ≈ 22 min |

Measuring to λ = 1e8 is what makes the fit trustworthy: §11's λ = 1e4 was the
clamp, not an optimum, so the only way to distinguish "the fit wants the
maximum" from "the fit wants the ceiling" is to measure above the ceiling.

### The fit is interior, and it tracks the measured ladder

**e0 = 0.008577**, max regret **0.554**, mean regret **0.106**.

| amp | measured excess | λ chosen | the cells' own optima |
| ---: | ---: | --- | --- |
| 0.002 | 0.0028–0.0055 | **0.10 – 0.30** | λ = 1 inert, λ ≥ 100 costs 2–12× |
| 0.005 | 0.0081–0.013 | **0.89 – 2.17** | λ = 1–10 ≈ 1.0× |
| 0.01 | 0.020–0.028 | **5.4 – 10.7** | mixed, 0.43–10.8× |
| 0.02 | 0.045–0.055 | **41 – 62** | 0.37–0.95× |
| 0.06 | 0.30–0.35 | **1189 – 1935** | 0.37× widely |

Two parameters reproduce the ladder across four decades. The residual max
regret (3.5×) is the honest cost of the form: inside one amp the optimum still
varies with n, and no law in excess alone can follow both. But it is no longer
a boundary fit, and λ = 0.1 … 1935 is a *schedule*, not a clamp.

### The test, once

| | geo mean | median | ≥5% better | ≥5% worse | best | worst |
|---|---:|---:|---:|---:|---:|---:|
| best-of-seven (§7, biased) | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| mean-\|log\| rule (§10) | 0.898 | 0.977 | 5 | 1 | 0.417 | 1.055 |
| min-max, clamped (§11) | 1.143 | 0.981 | 8 | 7 | 0.255 | 10.60 |
| **proven grid, interior (here)** | **0.975** | 0.954 | 8 | 2 | 0.246 | 9.06 |

| amp | §11 clamped | **§12 interior** |
| ---: | ---: | ---: |
| 0.005 | 3.575× worse | **1.016× (neutral)** |
| 0.01 | 1.469× worse | 2.677× worse |
| 0.04 | 0.488× | **0.507×** |
| 0.08 | 0.667× | **0.656×** |

**This is the first rule in the project that beats switching the term off
(geo 0.975) while genuinely engaging it**, and the heavy-corruption gains
(0.51×, 0.66×) survive the honest fit intact. Covering the gentle regime cost
nothing at the heavy end; it only priced out the 3.58× gentle wreckage. Both
of those statements are measurements, not arguments: the same 16 cells, the
same budget, two seeds, one frozen rule.

### What it did not fix — the amp-0.01 band is bimodal

| n | λ | control E | rule E | ratio |
| ---: | ---: | ---: | ---: | ---: |
| 20 | 8.03 | 1.330e-04 | 8.288e-04 | **6.23×** |
| 60 | 6.28 | 5.423e-04 | 5.009e-04 | 0.92× |
| 110 | 2.06 | 7.094e-04 | 6.428e-03 | **9.06×** |
| 240 | 1.94 | 4.417e-03 | 4.348e-03 | 0.98× |

The two surviving failures sit in one amp, on **sub-milli absolute energies**
(the control at n=20 is at 1.3e-4 — already near feasible; 8.3e-4 is a
different basin, not a worse packing). The training cells at amp 0.01 all
measured 0.89–1.31× at λ = 10, so the grid did not predict it either. Same λ,
per-n outcomes flipping between 0.9× and 9×: **bimodality, not a mis-weighted
term** — PL-15.

### The push, for the third time

λ = 11–55 at excess ≈ 0.03, fully engaged, no clamp:

| n | d = 1% | d = 2% | gated `L` | below record |
| ---: | ---: | ---: | --- | --- |
| 20 | 0.906× | 0.974× | none | no |
| 60 | 1.034× | 1.023× | none | no |
| 110 | 1.419× | 1.202× | none | no |
| 240 | 1.007× | 1.067× | none | no |

**0 of 8 gated, 0 of 8 below the record** — with the rule off (§10), saturated
(§11), and interior (§12). Three weightings, one wall. The wall is mechanical.

### The training-set question, settled by measurement

§11 closed on the observation that optimal packings are the vacuum and that at
excess = 0 the rule gives λ = 0. PL-16 (`08-BEYOND-1000.md`) then built the
easy rows above 1000 exactly: **4,794 rows over 4,794 distinct n** (n ∈ [1020,
9900]), 53.27% of the 9,000-row window, 340 provably optimal, all gated. Every
one of them is a **lattice** row. So widening the window with the easy rows
widens the vacuum — it gives a far larger sample of the vacuum phase and the
exact depth ladder above 1000, and it does **not** give a seam vocabulary,
because the easy rows have no seams. Both the reading and its limit are now
measured rather than assumed.

### Reproduction

```bash
python3 scripts/cram_language.py --fit-proven --rule-proven --push-proven --write   # ~22 min
python3 scripts/beyond1000.py --census --gate --write                               # ~40 s
```

---

## 13. PL-17 — all 156 proved rows, and the rule that carries

§12 trained on **8** proved rows. That was a sample, not the set. This section
rebuilds the identical grid — same amp ladder, same λ ladder, same lifted
clamp, same min-max criterion, one seed — on **all 156 rows in
`proven_floors`**, and changes nothing else.

### Cost, stated plainly

Measured cost is ≈ 0.077 · n^0.77 s per chain, so the full grid is 156 rows ×
5 amps × 8 λ = **780 cells, 10.6 h serial**, and **27.5 min on 8 workers**
(the run that completed). Two cloud-runner restarts killed earlier attempts at
430 and 686 cells; the grid is now **checkpointed per cell**
(`workspace/push/train_proven_all.jsonl`, 780 lines) and the wrapper
`scripts/_run_proven_all.sh` resumes from it, so the third attempt lost
nothing. The checkpoint is a reusable artifact, not just scaffolding.

### The fit

| grid | e0 | max regret | mean regret | λ at amp 0.06 |
| --- | ---: | ---: | ---: | ---: |
| 8 rows (§12) | 0.008577 | 0.554 | 0.106 | 1189–1935 |
| **156 rows (here)** | **0.036869** | **1.463** | **0.0882** | **≈ 77** |

λ from the full-set rule, by amp (median over 156 rows):

| amp | excess median | λ median | λ range over rows |
| ---: | ---: | ---: | --- |
| 0.002 | +0.0035 | **0.009** | 0 – 0.03 |
| 0.005 | +0.0096 | **0.068** | 0 – 0.23 |
| 0.01 | +0.0223 | **0.367** | 0 – 1.22 |
| 0.02 | +0.0574 | **2.42** | 0 – 7.68 |
| 0.06 | +0.3238 | **77.1** | 0 – 230 |

**The mechanism is not n.** The cells' own optimum λ is flat across n bands
(amp 0.06: **1000 / 1000 / 1000** for n < 100 / 100–399 / 400–961; amp 0.02,
where the curve is flat at large λ, is noisy but equally flat). So the full
set is not gentler because big packings want a gentler term. It is gentler
because the 156 rows are **heterogeneous** — some penalise any λ strongly — and
min-max therefore stops trying to sit on anyone's optimum and buys uniformity
instead. That is visible in the regret split: **max regret got worse (0.554 →
1.463) while mean regret got better (0.106 → 0.088)**. The fit is explicitly
no longer a point estimate of any cell's best; it is a compromise.

### The compromise is what travels

| rule | grid | geo mean | median | ≥5% better | ≥5% worse | best | worst |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| best-of-seven (§7, biased) | 300/150/80/30 | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| mean-\|log\| (§10) | same | 0.898 | 0.977 | 5 | 1 | 0.417 | 1.055 |
| min-max, clamped (§11) | same | 1.143 | 0.981 | 8 | 7 | 0.255 | 10.60 |
| min-max, 8 proved rows (§12) | proved × 8 | 0.975 | 0.954 | 8 | 2 | 0.246 | 9.06 |
| **min-max, all 156 proved rows** | **proved × 156** | **0.782** | 0.946 | **8** | **0** | 0.32 | **1.028** |

| amp | §12 (8 rows) | **§13 (156 rows)** |
| ---: | ---: | ---: |
| 0.005 | 1.016× | **1.011×** |
| 0.01 | 2.677× worse | **0.885×** |
| 0.04 | 0.507× | 0.592× |
| 0.08 | 0.656× | 0.705× |

**This is the project's first rule with no bad cells at all**: 22% lower
polished energy at equal budget, 8 of 16 cells ≥5% better, and the worst cell
is **1.028×** — inside the noise floor. The single 3.58× gentle failure in
§11, and the two 6–9× failures in §12, are both gone. It gives up a little at
heavy corruption to buy that (0.507 → 0.592, 0.656 → 0.705), and it remains
within 16% of the *biased* best-of-seven oracle (0.674) while needing no
per-cell choice.

**The lesson is the owner's, not the criterion's:** the eight rows were all
near-square (n = k²−1 and neighbours) and therefore maximally lattice-heavy;
the full set contains the individual proofs and the whole area-constrained tail,
and only that second population says how much heterogeneity the weight has to
survive.

### The push, fourth weighting

8 cells, d = 1%/2%, λ = 0.6–3.0 (engaged, gentle): **0 of 8 gated, 0 of 8
below the record** (geo 1.049, best 0.929). Four weightings now — off (§10),
saturated (§11), interior-8 (§12), interior-156 (§13) — and one answer.

### PL-15, settled: the damage was λ, the wobble is bistability

Six seeds per cell at amp 0.01, both arms from the same perturbed state:

| n | λ | geo over 6 seeds | first 2 seeds | spread | per-seed ratios |
| ---: | ---: | ---: | ---: | ---: | --- |
| 20 | 0.509 | 1.020 | 1.016 | 1.66× | 0.79 1.31 1.00 1.09 1.00 1.00 |
| 60 | 0.294 | 0.980 | 0.936 | 1.15× | 1.00 0.88 1.01 1.00 1.00 1.00 |
| 110 | 0.115 | 1.018 | 1.006 | 1.25× | 1.01 1.00 1.02 0.93 1.16 1.00 |
| 240 | 0.104 | **0.551** | 0.316 | **4.01×** | 0.30 0.34 1.00 1.00 0.26 1.06 |

Two separate answers, and both matter:

1. **The 6.23× and 9.06× failures were λ, not the band.** They occurred at
   λ = 2–8, which is what the *eight-row* fit assigned at amp 0.01. The full-set
   λ there is 0.1–0.5 and the same cells come back at **1.02× and 1.02×** over
   six seeds. The §12 damage was an artifact of an under-covered fit, exactly as
   its author suspected.
2. **The residual wobble is bistability, not Gaussian variance.** At n = 240,
   four seeds are inert (1.00, 1.00, 1.06) and two engage (0.30, 0.34) — modes
   separated by ~3.4×, not a spread around a mean. Two seeds said 0.316; six
   seeds say 0.551. A single chain cannot report the value of λ here.

### What this means for the method (the ⅀Δ reading)

Five measurements in a row have each landed on a **boundary** and each time the
answer lived just outside the window we had drawn: the 1e4 clamp (§11), the
degenerate criterion (§11), the grid's missing gentle regime (§12), the eight-row
sample (§13), and now a bistable cell whose two-seed estimate was wrong by 1.8×.
That is not a series of mistakes so much as a limit cycle around the truth: the
estimate overshoots, we widen the window, it overshoots the other way, and the
envelope converges even though no individual sample sits on the target.

Three consequences, applied in this section rather than asserted:

* **Report the distribution, not the median.** The probe reports six seeds and
the spread; §12's 9.06× is now understood as a λ artifact and n=240's 0.551 as
a mode-mixture. Any single number here should be read with its spread.
* **Treat saturation as a wrong window, not a result.** Both times a fit pinned
to a bound (λ = 1e4, then e0 at the edge), the correct response was to measure
further out. Both times the interior answer was different.
* **Do not expect a static optimum, and do not mistake a compromise for a
failure.** The rule that generalises best (0.782) is the one with the *worse*
max regret (1.463): it deliberately sits between cells rather than on any of
them. The wall in the push is likewise not a tuning problem — four weightings
agree — and the existing `delta_sigma_push.py` already contains the right
instrument for it: a contact-order classifier that separates a **RIGID_WALL**
jam (ρ > 0.5, abandon the target / change motif) from a **liquid** jam (ρ ≤
0.5, retry with rotation-rich moves). That classifier has never been run
(`finds_DS.json` does not exist). It is the correct next experiment for PL-12,
because it asks the question λ cannot answer.

### Reproduction

```bash
bash scripts/_run_proven_all.sh          # 780 cells, checkpointed, ~28 min on 8 cores
python3 scripts/cram_language.py --rule-proven-all --push-proven-all --probe-amp01 --write
```

---

## 14. PL-18 — the jam classified, and the wall is *not* mechanical

**§11–§13 called this wall mechanical** ("the wall is not a weighting choice").
That was an inference from the fact that four weightings all gave 0/8. It is
now tested directly, and it is wrong: the jam is **liquid in 12 of 16 states**.

Method: the push table stores energies, not states, so
`cram_language.py --dump-jam-states` re-runs the identical eight cells
(same perturb, same seeds, same budget, same λ from the full-set rule) and
writes the final states. `delta_sigma_push.py --from-states` then applies that
script's own classifier — the lag-1 autocorrelation ρ of the contact bit-stream
over squares sorted by x — with the script's own threshold (ρ > 0.5 →
RIGID_WALL, else ONE_PARAM_JAM).

| n | d | seed | ρ | contacts | verdict |
| ---: | ---: | ---: | ---: | ---: | --- |
| 20 | 1% | 0 | nan (0.95 frac) | 19/20 | RIGID_WALL *(degenerate)* |
| 20 | 1% | 1 | −0.056 | 19/20 | ONE_PARAM_JAM |
| 20 | 2% | 0 | nan (0.95 frac) | 19/20 | RIGID_WALL *(degenerate)* |
| 20 | 2% | 1 | −0.056 | 19/20 | ONE_PARAM_JAM |
| 60 | 1% | 0 | **+1.000** | **60/60** | **RIGID_WALL** |
| 60 | 1% | 1 | +0.482 | 58/60 | ONE_PARAM_JAM |
| 60 | 2% | 0 | **+1.000** | **60/60** | **RIGID_WALL** |
| 60 | 2% | 1 | +0.482 | 58/60 | ONE_PARAM_JAM |
| 110 | 1% | 0 | +0.090 | 98/110 | ONE_PARAM_JAM |
| 110 | 1% | 1 | +0.315 | 107/110 | ONE_PARAM_JAM |
| 110 | 2% | 0 | +0.190 | 105/110 | ONE_PARAM_JAM |
| 110 | 2% | 1 | +0.315 | 107/110 | ONE_PARAM_JAM |
| 240 | 1% | 0 | −0.039 | 231/240 | ONE_PARAM_JAM |
| 240 | 1% | 1 | −0.026 | 234/240 | ONE_PARAM_JAM |
| 240 | 2% | 0 | +0.145 | 234/240 | ONE_PARAM_JAM |
| 240 | 2% | 1 | −0.019 | 235/240 | ONE_PARAM_JAM |

**4/16 rigid, 12/16 liquid, 2 degenerate.**

What it means:

* **Every state at n ≥ 110 is liquid.** At the two larger cells, which are the
  ones that matter for the target, the wall is a **one-parameter family jam**:
  the contact network is 89–98% saturated but not crystalline, so the missing
  freedom is *rotational*, not a missing motif. The classifier's own
  prescription for that case is to retry with rotation-rich moves
  (`rotate_frac = 0.5`). That is a concrete, ready experiment — PL-19.
* **The rigid cases are the small, fully saturated ones.** n = 60 at seed 0 has
  all **60 of 60** squares in contact with ρ = 1.000: a crystalline wall, where
  the script's advice (change the motif, abandon the target) is appropriate. n
  = 20 is below the classifier's resolution: 19 of 20 squares touching makes one
  lag slice constant, so ρ is undefined rather than informative.
* **The verdict flips with the seed at fixed n and depth** (n = 60: 60/60 at
  seed 0, 58/60 at seed 1). That is §13's bistability a second time, now
  visible in contact *order* rather than in energy: the same cell, the same
  objective, two phases.

### A silent wrong answer, found and fixed in the classifier

The first run reported `rho=nan → ONE_PARAM_JAM`. That was a genuine defect of
this instrument, not of the states: with 19 of 20 squares touching, one of the
two lag slices has zero variance, `np.corrcoef` returns nan, and the old code's
`if rho > 0.5` fell through to the liquid branch **without comment** — a
silent classification of an undefined quantity. `classify` now falls back to
the **contact fraction** (≥ 0.9 = crystalline) when ρ is undefined, keeps ρ as
nan so the caller can label it, and reports `degenerate: true` in the ledger.
Exactly the failure mode the audit below was added to prevent, one level down.

### What the wider perspective now looks like

Three independent measurements have converged on the same picture, and it is
not the one §11 drew:

1. The **objective** side is well understood now: a rule fitted on all 156
   solved rows gives 22% lower polished energy with no bad cells (§13).
2. The **contact word** is still not recovered (Jaccard 0.018–0.054, PL-12),
   which says the term is a prior, not a decoder.
3. The **jam** is liquid, not rigid — so the 0/8 is a search-freedom problem,
   and the specific missing freedom is rotation. The wall is not a theorem
   about what packings exist; it is a statement about what this move grammar
   can reach.

And the census above 1000 closes the loop: the easy rows up there are
crystalline by construction (§16/`08-BEYOND-1000.md`), while the hard half —
n = k² + j with j > k — is exactly where a liquid, rotation-starved jam would
live. The classifier built for one campaign turns out to be the right
instrument for labelling both regimes, and it labels states in O(n²) with no
tolerance and no float gate — which is why it can be pointed at the >1000 rows
without a packlib feasibility pass.

## 15. Flag surface audit

`--dither` parsed, appeared in the dispatch guard, and had **no body**: it ran
nothing and said nothing. The superseded 8-row training path had the same
shape of risk (it worked, but PL-17 replaced it and its grid constant was still
live). Removed in this pass:

* `--dither` (never implemented) and its guard entry;
* `--fit-proven`, `--rule-proven`, `--push-proven`, the serial `train_grid`
  they used, and the `PROVEN_TRAIN_ROWS` constant (§12's 8-row path is
  superseded by the 156-row grid in §13; its measured results stay in the
  record above, only the code path is gone).

Added, so the class of failure cannot recur silently:

* **`audit_flags`** — every action flag is mapped to the ledger section it
  must produce, and a flag that leaves `res` untouched makes `main` exit **2**
  with the flag named. Verified: a stub namespace with only `check` set and an
  empty `res` returns `['--check']`.
* **`--dump-jam-states`** — the reproducible bridge from the push table to the
  classifier; states are now a first-class artifact
  (`workspace/push/jam_states.json`), not something recomputed by hand.

Also fixed while wiring it: `sa_push.py` and `delta_sigma_push.py` hardcoded
`/home/z/my-project` at import time, so the classifier could not be imported
off the owner's machine. Both now resolve relative to the scripts directory
when that root is absent.

---

## 16. PL-19 — rotation-rich moves, and the jam does not break

**The hypothesis, from §14.** 12 of 16 jam states are `ONE_PARAM_JAM` with an
89–98% saturated contact network and no crystalline order, and the classifier's
own prescription for that case is `rotate_frac = 0.5`. The annealer already
rotated — at 3% probability and, in the polish phase, at **±0.0015 rad**, i.e.
the angles were effectively frozen exactly where the jam forms. So the test
was to give it real angular freedom.

**The change.** `relax_graded` gained `rotate_frac` and `rot_amp`; the defaults
(0.3, `None`) reproduce the old code **bit for bit**, verified by §12's
recovery test still matching (2.333e-03, 9.208e-02) and by the rule arm below
reproducing the stored push exactly. The treatment runs at `rotate_frac = 0.5`,
`rot_amp = 0.05` — 1.7× the rotation rate and **33× the angular step**.

**Four arms, so the cause is attributable rather than merely absent:**

| arm | λ | grammar |
| --- | --- | --- |
| ctl | 0 | default |
| rule | full-set rule | default |
| rot_only | 0 | rotation-rich |
| rot_rule | full-set rule | rotation-rich |

| n | d | λ | rule | rot_only | rot_rule |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 1% | 2.97 | 1.040× | 1.163× | **2.472×** |
| 20 | 2% | 2.97 | 1.024× | 0.994× | 1.359× |
| 60 | 1% | 2.41 | 1.030× | 1.000× | 1.000× |
| 60 | 2% | 2.41 | 1.005× | 1.000× | 1.000× |
| 110 | 1% | 0.99 | 1.344× | 0.951× | **2.776×** |
| 110 | 2% | 0.99 | 1.072× | 0.986× | 1.755× |
| 240 | 1% | 0.61 | 0.929× | 1.071× | 1.123× |
| 240 | 2% | 0.61 | 0.991× | 0.942× | 1.120× |

| | geo mean vs ctl | median | best | worst | gated cells |
| --- | ---: | ---: | ---: | ---: | ---: |
| rule | 1.049 | 1.027 | 0.929 | 1.344 | **0/8** |
| rot_only | 1.011 | 0.997 | 0.942 | 1.163 | **0/8** |
| **rot_rule** | **1.459** | 1.241 | 1.000 | 2.776 | **0/8** |

**The jam does not break. Not one arm gated a single cell, and the treatment is
46% *worse* than the control in energy.** Rotation alone is neutral (1.011) —
so the angular freedom is not the binding constraint either way.

### And rotation makes the states *more* crystalline

Classifying the `rot_rule` states with the same instrument:

| | before (PL-18) | after rotation |
| --- | ---: | ---: |
| RIGID_WALL | 4/16 | **7/16** |
| ONE_PARAM_JAM | 12/16 | 9/16 |
| all squares in contact | 2/16 | **7/16** |

At n = 20 **all 20 of 20** squares are in contact at both seeds and both
depths (ρ = 1.000); at n = 60, three of four states are 60/60. Rotation is
being spent closing the last contacts, not opening space. That is the opposite
of breaking a jam, and it is a coherent physical reading: at d = 1–2% the
container is over-full for this grammar, so extra angular freedom converts
slack into contacts.

### What this settles, and what it refutes

* **The classifier's prescription does not transfer.** "Liquid → retry
  rotation-rich" is a heuristic from the shrink-loop campaign on *other*
  targets. Tested on these targets it is refuted: 0/8 gated, and a 46% energy
  penalty. `ONE_PARAM_JAM` should be read as "not crystalline", not as
  "rotation-limited".
* **The wall has now survived five distinct attempts**: four weightings
  (§10–§13), and now angular freedom (§16). It is not a weighting artefact and
  it is not an angular artefact.
* **What remains is reach, not freedom of this kind.** Either the budget is too
  small to find a state that exists, or no state exists at that `L` for this
  square set. Those are different claims and §16 does not distinguish them —
  which is exactly what PL-20 should do, and it is cheap: bisect `d` between 0
  and 1% to find the smallest depth the push ever gates, and run the existing
  **collective** patch move (`relax_patch`, run-40 §8) at the same targets. A
  collective move is a different freedom from single-body rotation: it can
  rearrange a neighbourhood at once, which is what a liquid jam would need.

### Reproduction

```bash
python3 scripts/cram_language.py --push-rotation --write        # 154 s
then classify the written states:
python3 scripts/delta_sigma_push.py --from-states workspace/push/jam_states_rot.json
```
