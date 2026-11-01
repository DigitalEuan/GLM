# The aggregation bench — fifteen mixing methods, one pre-registered bar

## Tier 0 — the coarse read

**Question.** Attention is one way for an architecture to mix a register. Fifteen mixing methods — the two the substrate ships, nine from the literature, four devised from the attention study's own measurements — run on the same registers under the same instruments: which of them is *best*, by a bar written down before the first measurement?

**Verdict.** The incumbent wins: the shipped hard selector `nearest_weights` meets every line of the pre-registered bar, and no newcomer exceeds it — the eligible set is five fully exact distance-family methods (the selector, Shepard IDW, Borda, and the two originals: the neighborhood mean and the exact bridge), all tying the selector's 26 of 35 analogy items, while the entire inner-product family — raw and Cauchy–Schwarz attention, linear attention, the polynomial family, top-k sparse, and the Padé softmax — is captured by giant decoys on 8 of 8 planted queries and answers 0 of 35 analogy items, so the module stays in the sandbox: a measured comparison, not yet a faculty.

**Deciding figure.** 26 of 35 analogy items for the control and every eligible method, 8 of 8 planted queries captured by the giant decoys for every inner-product method, 2 weight bits for the winner against 99,718 for the softest method, and an effective support of 1 that no exponential dial reaches within the declared depth budget while the exact dials walk it in integer steps.

**Recomputed by.** `glm_universal.sandbox.aggregation_bench.bench_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Code:** [`../glm_universal/sandbox/aggregation_bench.py`](../glm_universal/sandbox/aggregation_bench.py)
(the sandbox occupant; nothing the system computes with imports it)
**Run:** `PYTHONPATH=. python3 -c "from glm_universal.runtime.session import GeometricSession; from glm_universal.sandbox import aggregation_bench as b; b.bench_report(GeometricSession())"`

The incumbent wins: the shipped hard selector `nearest_weights` meets every line of the pre-registered bar, and no newcomer exceeds it — the eligible set is five fully exact distance-family methods (the selector, Shepard IDW, Borda, and the two originals: the neighborhood mean and the exact bridge), all tying the selector's 26 of 35 analogy items, while the entire inner-product family — raw and Cauchy–Schwarz attention, linear attention, the polynomial family, top-k sparse, and the Padé softmax — is captured by giant decoys on 8 of 8 planted queries and answers 0 of 35 analogy items, so the module stays in the sandbox: a measured comparison, not yet a faculty.

---

## 1. What this study is

The attention simulator study measured that soft attention runs on this
substrate exactly, needs a declared exponential depth, sits at one point of
a dial whose two ends — the coordinatewise *bundle* and the hard *nearest* —
are faculties the substrate already ships, and is norm-dominated on the live
registers.  Attention is therefore one point in a space of aggregation
methods.  This study is that space, measured: a bench of **fifteen** mixing
methods, each returning exact weights over a register given a query, run
against the same six instruments under a definition of "best" that was
written down before any measurement was taken.

The questions were fixed before the measurements below were taken:

1. **Validity.** Does every method return a distribution (weights
   non-negative, summing to 1, over exactly the offered rows), and are the
   family endpoints exactly the two shipped ends?
2. **Ground truth.** On the shipped analogy benchmarks — chemistry, lexicon
   and physics, 35 items whose answers are external to this package — does
   the method's retrieval match or beat the shipped selector's, in the
   argmax read-out (selection semantics) and the mixture read-out (decode
   the attended mixture by the shipped nearest)?
3. **Norm domination.** On a planted register with orthogonal semantic
   directions at radii 1 to 512 and four giant decoys at radius a million —
   does the method's selection track meaning or mass?
4. **Depth.** For every method with a transcendental: the measured exponent
   range on a live register, the computed Taylor depth at the declared
   target, and a refusal when the declared budget cannot represent the
   range.  For the Padé class: the computed validity bound and the
   disagreement against a fourfold-depth reference.
5. **The dial.** Every knob swept, with the effective support
   (`1 / sum w^2` — exactly 1 at the hard end, exactly `n` at the bundle)
   as the dial coordinate.
6. **Cost.** Exactness priced in integer growth (the largest
   numerator-plus-denominator size among the weights) and in harness wall
   time.

Declared unreachable before the run: a *fully exact* softmax (class E1
carries the exponential at a computed depth by the alternating-series
remainder bound; class E2 replaces it with an exact rational function whose
validity range is itself computed), and a Lean specification (no Lean
toolchain in the measuring environment; the obligation is recorded in the
promotion checklist, not discharged).

## 2. The pile

| # | method | family | exactness | provenance |
|---|---|---|---|---|
| 1 | `bundle` | distance | E0 | shipped: the coordinatewise mean (the t=0 end) |
| 2 | `nearest_weights` | distance | E0 | shipped: the hard selector (the t=∞ end) |
| 3 | `attention_raw` | inner-product | E1 | the paper's `sigma(X A X^T) X V`, raw scores |
| 4 | `attention_cs` | inner-product | E1 | the attention study's Cauchy–Schwarz fix, two-sided |
| 5 | `linear_attention` | inner-product | E0 | linear attention (Katharopoulos et al.): scores as weights |
| 6 | `power_attention` | inner-product | E0 | polynomial-kernel softmax `u^p` |
| 7 | `rbf` | distance | E1 | Gaussian kernel on distance, `sigma^2 = mean d^2` |
| 8 | `idw` | distance | E0 | Shepard inverse-distance-squared weighting |
| 9 | `sparse_topk` | inner-product | E1 | top-k sparse attention |
| 10 | `rank_borda` | rank | E0 | Borda weights by distance rank |
| 11 | `pade_softmax` | inner-product | E2 | `[m/m]` Padé of `e^x`, an exact rational function |
| 12 | `neighbor_mean` | distance | E0 | **original**: hard attention to a soft neighborhood |
| 13 | `exact_bridge` | distance | E0 | **original**: the literal dial `(1-lam) bundle + lam nearest` |
| 14 | `range_softmax` | distance | E1 | **original**: softmax with the exponent range normalised to exactly `t` |
| 15 | `cosine_softmax` | cosine | E1 | **original**: softmax over the shipped `signed_cosine_squared` |

The four originals are devised from the attention study's own measured
results: the neighborhood mean from the finding that the distance term
decides semantics and the two shipped ends are the limits of every dial;
the exact bridge from the finding that the temperature dial is *doing*
bundle-to-nearest interpolation; the range-normalised softmax from the
flagship negative result — *depth below the range inverts the softmax* —
making the range a design parameter caps the computed depth by
construction; and the cosine softmax from the finding that the shipped
cosine-squared is a semantically valid selector on the meaning registers.

Exactness classes: **E0** fully exact over the rationals; **E1** the
exponential carried at a declared Taylor depth computed from the measured
range; **E2** the exponential replaced by its `[m/m]` Padé approximant —
exact arithmetic, approximate function, validity range computed exactly and
enforced as a refusal.

## 3. Instrument I — validity and the dial identities

All fifteen methods return valid distributions on the six-row probe
register (weights non-negative, summing to 1, over exactly the offered
rows; `attention_raw` probed at temperature 1/1000 because its default
temperature exceeds the declared depth budget on that register — a
feasibility fact, recorded by the depth audit).  The pre-registered family
endpoints all hold exactly:

| identity | holds |
|---|---|
| `power_attention(p=0)` = `bundle` | yes |
| `neighbor_mean(k=1)` = `nearest_weights` | yes |
| `neighbor_mean(k=n)` = `bundle` | yes |
| `exact_bridge(lam=0)` = `bundle` | yes |
| `exact_bridge(lam=1)` = `nearest_weights` | yes |
| bundle's effective support = `n` | yes |
| nearest's effective support = 1 | yes |

## 4. Instrument II — the analogy ground truth

The construction is exactly the shipped solver's: `D* = C + (B - A)` over
full carriers, projected onto the session's default subspace for the
domain, with `A`, `B`, `C` excluded from the pool.  The only thing that
varies between methods is the retrieval scoring that turns `D*` into an
answer — the step the shipped session performs with `metric.nearest`.
Ground truth is external (the periodic table, ordinary English, SI
dimensional analysis).  Of 35 items, the shipped selector answers **26**
(chemistry 9/12, lexicon 5/10, physics 12/13).

| method | class | argmax | mixture | refusals |
|---|---|---|---|---|
| `bundle` | E0 | — (no selection) | 1/35 | 0 |
| `nearest_weights` | E0 shipped | **26/35** | **26/35** | 0 |
| `attention_raw` | E1 | 0/35 | 0/35 | 12 |
| `attention_cs` | E1 | 0/35 | 1/35 | 0 |
| `linear_attention` | E0 | 0/35 | 1/35 | 0 |
| `power_attention` | E0 | 0/35 | 1/35 | 0 |
| `rbf` | E1 | 26/35 | 0/35 | 0 |
| `idw` | E0 | 26/35 | 22/35 | 0 |
| `sparse_topk` | E1 | 0/35 | 0/35 | 0 |
| `rank_borda` | E0 | 26/35 | 0/35 | 0 |
| `pade_softmax` | E2 | 0/35 | 1/35 | 0 |
| `neighbor_mean` | E0 | **26/35** | 15/35 | 0 |
| `exact_bridge` | E0 | **26/35** | 6/35 | 0 |
| `range_softmax` | E1 | 26/35 | 1/35 | 0 |
| `cosine_softmax` | E1 | 13/22 | 0/35 | 13 |

Three findings, none of them subtle.  First, **the family law**: every
distance-space method ties the shipped selector at 26/35, and every
inner-product method answers 0/35 — the attention study's row-level
finding (inner-product argmax agreed with the shipped nearest on 1 of 12
rows) reproduces as a family-level law on 35 external-ground-truth items.
Second, **the mixture read-out destroys soft selection**: methods whose
argmax is perfect (rbf, rank_borda, range_softmax at 26/35) decode their
attended mixtures to 0/35 or 1/35 — a soft mixture lands between rows and
decodes to the wrong one; only the hard selector keeps 26/35 and only
idw (whose weights are nearly one-hot on this register) holds 22/35.
Third, **refusals are answers**: the cosine softmax refuses 13 physics
items whose analogy targets project to the zero vector — the shipped
`signed_cosine_squared` declines to take the angle of a vector with no
direction, and the bench records the refusal rather than inventing an
angle.

## 5. Instrument III — the norm-domination probe

The planted register: eight pairwise-orthogonal semantic directions
(three coordinates each) at radii 1, 8, 64, 512, plus four giant decoys
at radius a million whose support touches every direction — related to
everything, belonging to nothing.  Each query is a mid-radius point of
one direction with a one-percent leak into the next; the truth for query
`i` is the rows of direction `i`.

| method family | top-1 semantic | top-1 giant capture | mixture semantic |
|---|---|---|---|
| inner-product (all six) | **0/8** | **8/8** | 1/8 – 3/8 |
| every other method | **8/8** | 0/8 | 1/8 – 8/8 |

The attention study's norm-domination result, planted and reproduced as
a family law: every inner-product method — including linear attention
with no exponential at all, and the Padé class with its exact arithmetic
— puts all its mass on the giant decoys, while every method that scores
in distance or cosine space recovers the semantic direction on all eight
queries.  The exponential is not the problem; the inner product is.

## 6. Instrument IV — the depth audit and the inversion control

Measured on the live lexicon register (149 rows), at the declared target
1e-30 and depth budget 512:

| method | exponent range | computed depth | feasible |
|---|---|---|---|
| `attention_raw` | 1.22e5 | — | **no: refuses** |
| `attention_cs` | 0.0177 | 12 | yes |
| `rbf` | 3.25 | 42 | yes |
| `sparse_topk` | 0.00117 | 8 | yes |
| `pade_softmax` | 0.0177 | 12 (validity bound 4.64) | yes |
| `range_softmax` | exactly 1 | 28 | yes |
| `cosine_softmax` | 0.14 | 17 | yes |

Raw attention cannot answer on the live register at any temperature its
budget can buy — the attention study's finding, now measured as a
refusal.  The two-sided Cauchy–Schwarz scale brings the range to 0.0177
(a depth of 12 — the fix costs almost nothing *numerically*, which is
exactly why its 0/35 and 8/8-giant results are about the score, not the
depth).  The range-normalised softmax's range is exactly 1 *by
construction*, so its depth is a function of `t` alone and can never
surprise.  The Padé class carries its validity bound as the computed
smallest root of its numerator (4.644 for `[3/3]`, the true Padé pole)
and disagrees with a fourfold-depth Taylor reference by 3.19e-20.

The closing control reproduces the attention study's flagship negative
result at fixed depths below the range: raw attention at rational
temperature 1/1000 on a four-row register block — top-1 correct on
**0 of 4** rows for every fixed depth from 4 to 12, 1 of 4 at 16–24,
2 of 4 at 28–32, 3 of 4 at 48, 4 of 4 only from depth 64.  The
staircase is the reason the computed-depth discipline exists.

Bring-up found and fixed two defects in the Padé machinery before any
number above was recorded: the Horner iteration ran in the wrong
direction over the ascending coefficients (evaluating the *reversed*
polynomial `x^m P(1/x)`, which makes the whole E2 class answer at `1/x`
with a sign flip for odd `m`), and the Cauchy root bound divided by the
constant instead of the leading coefficient (bracketing only `|zeta| <=
2`, so the "computed root" was the bound itself).  After the fixes the
approximant matches `e^x` to 9e-13 at x = -0.1 and the bench numbers
were regenerated from scratch.

## 7. Instrument V — the dial

Effective support (`1 / sum w^2`) on the live lexicon register (n = 149),
every knob swept:

| dial | the sweep | the finding |
|---|---|---|
| `attention_cs` (t) | 149 flat through t=16, 137 at 64, 64.7 at 256 | **never near 1 within budget** |
| `range_softmax` (t) | 149 → 141 → 98 → 45 → 18, refuses at t ≥ 256 | same ceiling, by design visible |
| `cosine_softmax` (t) | 149 flat to t=1, 148 at 4, 134 at 16, 31 at 64, **1.16 at 256** | the only exponential dial that nears the hard end |
| `attention_raw` (t) | 149 at 1e-6, 1.17 at 1/1000, refuses t ≥ 1/256 | usable window is microscopic, and at 1/1000 it is hard selection of the *wrong* (norm-maximal) row |
| `power_attention` (p) | 149 flat to p=8, 148 at 16, 146 at 32, 137 at 64 | exact, but the integer knob barely moves it |
| `idw` (alpha) | **1 at every alpha** | inverse-distance is already hard on this register |
| `sparse_topk` (k), `neighbor_mean` (k) | 1, 2, 4, 8, 16, 32, 64 (…128) | the integer staircase, exact |
| `exact_bridge` (lam) | 149, 45, 14.5, 3.92, 1.77, 1.3, 1 | the whole dial in one rational parameter |

The structural result: **the exponential dials cannot reach the hard end**
within the declared depth budget — sharpening attention means growing the
exponent range, and the range is what the budget refuses — while the exact
dials (`k`, `lam`) traverse the full range from 1 to n in integer or
rational steps, at 4 and 15 weight bits respectively.  The dial the
substrate can actually walk is the exact one.

## 8. Instrument VI — cost in the substrate's own currency

Weight bits (largest numerator-plus-denominator size among nonzero
weights, live lexicon register) and harness wall time:

| method | bits | wall |
|---|---|---|
| `nearest_weights` | **2** | 0.02 s |
| `idw` | 2 | 0.02 s |
| `neighbor_mean` | 4 | 0.02 s |
| `bundle` | 9 | < 0.01 s |
| `exact_bridge` | 15 | 0.02 s |
| `rank_borda` | 22 | 0.02 s |
| `linear_attention` | 63 | 0.01 s |
| `power_attention` | 119 | 0.01 s |
| `sparse_topk` | 478 | 0.01 s |
| `attention_cs` | 731 | 0.03 s |
| `range_softmax` | 1,809 | 0.06 s |
| `rbf` | 3,218 | 0.09 s |
| `pade_softmax` | 23,389 | 0.03 s |
| `cosine_softmax` | **99,718** | 0.11 s |
| `attention_raw` | — (refused at default t) | 2.6 s at t=1/1000 |

The winner costs **2 weight bits**; the softest method costs 99,718 —
five orders of magnitude, the price of exactness inside the transcendental
classes, measured in the substrate's own integer growth rather than
seconds.  Wall time is nearly free for everything (the register is 149
rows); the one slow method is raw attention at its fallback temperature,
paying depth ~450 to represent a range its own discipline says it should
have refused.

## 9. The pre-registered verdict

`BEST_BAR` was written down before the first measurement ran.  A method
is *substrate-best* iff it (1) returns a valid distribution, (2) is fully
exact over the rationals (E0), (3) matches or beats the shipped selector's
analogy total in the argmax read-out, (4) recovers the planted semantic
direction on at least 7 of 8 norm-domination queries, and (5) costs at
most a hundred times the bundle's weight bits.  Among methods that meet
the bar, the incumbent wins exact ties; a newcomer must strictly exceed
it.

Five methods are eligible — `nearest_weights`, `idw`, `rank_borda`,
`neighbor_mean`, `exact_bridge` — every one of them fully exact, every
one in distance space, all tying 26/35.  **The winner is
`nearest_weights`, the incumbent.**  No newcomer exceeded it: the soft
methods that tie it on selection (rbf, range_softmax) fail the exactness
line and cost 3,218 and 1,809 bits against its 2; the exact soft methods
that tie it (the neighborhood mean, the bridge) are dials *around* the
selector rather than replacements for it.

The second prize, reported beside the winner because the interesting
question for a substrate that already ships the hard end is what to adopt
*beside* it: **the best soft method is `neighbor_mean`** — the original
E0 neighborhood mean at k=4, effective support exactly 4, 4 weight bits,
26/35 on selection.  It is the shipped selector with the exact dial the
exponential family cannot provide; the near-miss table shows what each
excluded method fails on.

## 10. What promotion would take

The checklist is computed, and 8 of its 11 lines pass: all fifteen
methods return valid distributions; the family endpoints are exactly the
shipped ends; a method meets the pre-registered bar; the bar is met by a
fully exact method; the winner matches the shipped selector and survives
the norm-domination probe; every feasible transcendental carries a
computed depth; the Padé validity bound is computed and enforced (measured:
the method answers below it and refuses beyond it).  The three failing
lines are the absent things, and they are the same three the attention
simulator fails: **a wired query kind, a compiled Lean specification, and
corpus registration of this study.**  Until they exist the module stays
in the sandbox, and deleting it cannot change a single answer the system
gives — verified: no shipped module imports it, and no module that
computes an answer imports it.

## 11. How to recompute

```
cd <repo root>
PYTHONPATH=. python3 -c "
from glm_universal.runtime.session import GeometricSession
from glm_universal.sandbox import aggregation_bench as b
import json
print(json.dumps(b.bench_report(GeometricSession()), default=str))"
PYTHONPATH=. python3 -c "
from glm_universal.sandbox import aggregation_bench as b
import json
print(json.dumps(b.promotion_checklist(), default=str, indent=2))"
```

The experiment harness that produced the figures and the archived
numbers ships beside this study (`aggregation_experiments.py`, stages
exp0–exp6 plus charts, checkpointed and resumable); the findings archive
is `findings/results.json` with the five figures.  Every number in this
document is regenerated from nothing by those two commands.
