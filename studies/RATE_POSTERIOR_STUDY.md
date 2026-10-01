# The rate from the machine's own readings — a posterior over declared rates, and the soft channel

## Tier 0 — the coarse read

**Question.** Can the decoder and the second reading estimate the bit-flip rate from the reads themselves, instead of having the caller declare it, and what does a confidence marginalized over that estimate promise?

**Verdict.** The machine can estimate it from the reads, with a measured price: the posterior over the declared grid is exact, the soft floor keeps its promise averaged over the prior in every cell, and the edge refusal catches part of the danger above the grid. At a fixed true rate the promise is not guaranteed: it broke in 2 cells on the grid (1/10, floor 9999/10000), so the declared expectation failed, and in 35 cells at 1/5, above the hunted grid.

**Deciding figure.** 7 of 7 marks met; the promise kept under the prior in 35 of 35 cells; 525 fixed-rate cells classified, 37 broken — 35 at 1/5 and 2 on the grid; 10 of 10 runtime programs as computed.

**Recomputed by.** `glm_universal.reasoning.rate_posterior_marks.rate_posterior_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate P of [`STATUS.md`](../STATUS.md) §3.4, item **P5** (candidate J's
soft-channel item), named by
[`CONFIDENCE_FLOOR_STUDY.md`](CONFIDENCE_FLOOR_STUDY.md) §3: *the rate is
still declared by the caller; the underdeclared result says the price of a
wrong declaration.* Phase 80 measured that price: a floor chosen at a declared
rate breaks its promise in 30 of 210 cells when the true rate is twice the
declared one. The owner's route for this round: the marginal likelihood of a
read at rate `p` with the truth summed out is already built — for the decoder
it is the coset mass the census computes — so a posterior over a declared grid
of rates, and a confidence marginalized over it, are rational evaluations of
tables the machine already holds. The second reading's pair likelihood is the
sum of [`AGREE_CHANNEL_STUDY.md`](AGREE_CHANNEL_STUDY.md) (Phase 81), so the
two items share their machinery.

The owner's decision points 3 and 4 are answered here by declaration; each
choice is one the measurements below can overturn next round.

## 1. Declarations — written before the module that measures them

**The model.** One unknown rate `p`, the same for every read of a call: every
bit of every read flips independently at `p`, and each read (or each pair of
reads of one carrier) has its own truth drawn uniformly from the 4096
codewords. A call that mixes rates violates this; it is the declared
assumption every answer quotes.

**The grid and the prior.** `G = 1/1000, 1/100, 1/50, 1/20, 1/10, 1/5` —
Phase 80's five rates and a guard point at 1/5 above them — with the uniform
prior over `G`. A second prior is declared for sensitivity only: weights
proportional to the rate (the cautious prior, which leans towards the
overdeclared side that Phase 80 proved safe).

**The likelihood.** For one read `y`, `P(y | p) = (1/4096) Σ_c p^d(y,c)
q^(24−d(y,c))` — the coset mass of `y` over 4096, which depends on `y` only
through its coset weight. For two reads of one carrier, `P(y1, y2 | p) =
(1/4096) Σ_c p^D(c) q^(48−D(c))` with `D(c) = d(y1, c) + d(y2, c)`. Reads of
different carriers multiply.

**The posterior and the answer.** `P(p | reads) ∝ prior(p) · Π P(obs | p)`,
exact over `G`, the subject's own read included (it is evidence about the
rate too). The **soft reading** answers the value the reading would answer
(the complete decoder's, or `agree`'s) with its **marginal confidence**
`Σ_p P(p | reads) · conf_p`, where `conf_p` is Phase 77's confidence at `p`.
The soft floor applies a declared floor to the marginal confidence (the
theorem-clean design of the owner's point 4, chosen over the argmax-rate
floor).

**The refusals.** `RATE_GRID_EXCEEDED` when the posterior's most probable
rate is the guard point 1/5: the reads say the rate may lie above every rate
the floor was hunted at, and underdeclaring is the dangerous direction. The
reading's own refusals (`TIE`, `AMBIGUOUS`, `UNCORRECTABLE`) and `BELOW_FLOOR`
as before. No low-edge refusal: a posterior leaning to 1/1000 overstates a
lower true rate, which Phase 80 proved safe.

**The corpus.** Per call: the subject's read (or pair) plus any further reads
the call passes, declared to be of the same channel. A session-history corpus
is not built this round; its price is what J4 measures.

**J1 — the likelihood is right.** (i) At every rate of `G`, the five coset
classes' probabilities `N_d W_d(p)` (`N = 1, 24, 276, 2024, 1771`) sum to one
exactly. (ii) On a declared stride of reads, the per-read likelihood from the
coset class equals the brute-force `(1/4096) Σ_c` sum, 0 disagreements. (iii)
On a stride of pairs, the pair likelihood by the Phase 81 histogram equals the
brute-force sum.

**J2 — the promise under the prior.** For calls of `n = 1, 2, 5, 10, 20`
single reads (the subject and `n − 1` corpus reads) and every floor of Phase 80's `T`, the soft floor's `P(wrong | answered)`
averaged over the declared prior (rate drawn from the prior, then the reads)
is at most `1 − t`, exactly. The Lean theorem of J9 says it must.

**J3 — the fixed-rate table (Phase 80's F4, successor).** At every true rate
in `G` minus the guard, at the midpoints between consecutive rates, and at
half and twice each rate, for each `n` and each floor: the soft floor's
residual and retention, whether the promise holds at that fixed rate, by how
much it breaks where it does, and the probability of `RATE_GRID_EXCEEDED`.
The mark is that every cell is computed exactly and classified. Declared
expectation, not a mark: at every true rate in the grid the promise holds for
`n ≥ 5`.

**J4 — the price of softness.** Per `n`, the soft floor's retention and
residual against the oracle floor (the confidence at the true rate), at every
grid rate. Reported, not marked.

**J5 — identifiability.** Per grid rate, the smallest `n ≤ 20` at which the
posterior's most probable rate is the true one with probability at least
9/10, or *beyond 20*. Reported, not marked.

**J6 — the naive estimator underestimates.** At every rate of `G`, the mean
distance from a read to its nearest codeword — its coset weight,
`E[d(y, C)]` — is below `24p`, the mean number of flipped bits, computed
exactly; and the Lean theorem of J9. This is why the estimator uses the exact likelihood rather than the
residual weight.

**J7 — refusals are evidence.** The probability of a coset-weight-4 read
(`TIE`) rises across `G`, so one refused read moves the posterior mean rate
up, and a pair that `agree` refuses as `UNCORRECTABLE` does too: both checked
exactly at the uniform prior.

**J8 — the runtime, computed not reasoned.** Three dialect builtins:
`decode_soft(subject, *corpus)` → `(value, marginal confidence)`,
`decode_soft_floor(floor, subject, *corpus)` (refusing `BELOW_FLOOR`) and
`agree_soft(r1, r2, *corpus)` → `(value, marginal confidence)`; each answer's
script recomputes the posterior and the marginal confidence by brute-force
sums over every codeword in a fresh interpreter. A declared set of programs,
each outcome computed by the estimator before the runtime is run: all as
computed, 0 wrong. The existing builtins answer exactly as before.

**J9 — Lean** (`RequestProject/GLM/RatePosterior.lean`).
`soft_floor_error_le`: if every answered observation's marginal confidence is
at least `t`, the answered mass is wrong with mass at most `(1 − t)` times the
answered mass, under the joint measure of rate, truth and reads.
`rate_posterior_prod`: updating the posterior one read at a time gives the
batch posterior. `naive_rate_underestimates`: a statistic pointwise at most
another, strictly below it on a set of positive mass, has strictly smaller
mean. `read_marginal_eq_coset_mass`: summing a function of `y + c` over the
code is summing it over the coset of `y`. No `sorry`; the standard axioms
only.

## 2. Results

Recomputed by `rate_posterior_report` (about 35 seconds, `Fraction`
throughout, no sampling: the posterior depends on a call only through the
count vector of its reads' coset weights, whose distribution is multinomial
with exact cells); `tests/test_rate_posterior.py` keeps the figures below.

### 2.1 J1 — the likelihood is right: met

The five coset classes sum to one exactly at every rate of `G`; on a stride of
11 reads and pairs the likelihood from the coset class (and from the Phase 81
histogram for pairs) equals the brute-force sum over every codeword, 0
disagreements.

### 2.2 J2 — the promise under the prior: met

35 of 35 cells (`n = 1, 2, 5, 10, 20` × seven floors) keep `P(wrong |
answered) ≤ 1 − t` averaged over the uniform prior; 0 broken. For example at
`n = 1` the residual is 0.008385 at floor 9/10 and 2.064e-05 at 999/1000; at
`n = 20` it is 5.564e-05 at 999/1000 and 1.681e-06 at 9999/10000. This is what
the Lean theorem `soft_floor_error_le` says must happen; the mark is the
computed check that the runtime design meets its hypothesis.

### 2.3 J3 — the fixed-rate table: met; the declared expectation: not met

525 cells (15 true rates — the five grid rates, their midpoints, half and
twice each — × five `n` × seven floors), every one computed and classified.
37 break the promise:

* **35 at true rate 1/5**, twice the highest hunted rate — every floor, every
  `n`. The edge refusal `RATE_GRID_EXCEEDED` fires on 0.4697 of calls at
  `n = 1`, 0.443 at `n = 2`, 0.5394 at `n = 5`, 0.5825 at `n = 10` and 0.6114
  at `n = 20`: it catches roughly half of the danger, not all of it. The worst
  cell is `n = 2`, floor 9999/10000: residual 0.0208 against 1e-4.
* **2 on the grid**, at true rate 1/10 and floor 9999/10000: residual 1.459e-4
  at `n = 2` and 1.418e-4 at `n = 5`, against the promised 1e-4, with retention
  0.07923 and 0.08289.

So the declared expectation — *at every true rate in the grid the promise
holds for `n ≥ 5`* — **failed** (at 1/10, `n = 5`). Midpoints and half-rates
never break. The soft promise is a promise on the prior average, as the
theorem says; at a fixed rate it is measured, and it can miss by a factor of
about 1.5 at the strictest floor and the highest grid rate.

### 2.4 J4 — the price of softness (reported)

Soft floor against the oracle floor (the confidence at the true rate):

| true rate | floor | n = 1 | n = 2 | n = 5 | n = 10 | n = 20 | oracle |
|---|---|---|---|---|---|---|---|
| 1/20 | 99/100 retention | 0.6811 | 0.739 | 0.888 | 0.9032 | 0.9089 | 0.9112 |
| 1/20 | 999/1000 retention | 0.301 | 0.5522 | 0.731 | 0.7939 | 0.879 | 0.9112 |
| 1/10 | 999/1000 retention | 0.1015 | 0.1807 | 0.2203 | 0.2989 | 0.3571 | 0.3722 |

The soft floor is more conservative than the oracle at small `n` (it keeps
less, at a smaller residual) and approaches the oracle as `n` grows. Per call,
with only the subject's read, the price is heavy; a corpus of 10–20 reads of
the same channel recovers most of it.

### 2.5 J5 — identifiability (reported)

Smallest `n ≤ 20` with P(most probable rate = true rate) ≥ 9/10: 1 at 1/1000,
15 at 1/20, 13 at 1/10, and beyond 20 at 1/100 and 1/50 (neighbouring grid
rates are hard to tell apart from few reads).

### 2.6 J6 — the naive estimator underestimates: met

Mean coset weight against `24p`: 0.4798 against 0.48 at 1/50, 1.188 against
1.2 at 1/20, 2.207 against 2.4 at 1/10, 3.192 against 4.8 at 1/5 — below at
every rate of `G`, exactly.

### 2.7 J7 — refusals are evidence: met

The `TIE` mass rises across `G` (1.042e-08 at 1/1000 to 0.381 at 1/5). Under
the uniform prior (mean 0.0635), one `TIE` read moves the posterior mean to
0.1664; a pair that `agree` refuses `UNCORRECTABLE` moves it to 0.1929; a clean
pair moves it down to 0.009609.

### 2.8 J8 — the runtime, computed not reasoned: met

10 of 10 `decode_soft` / `decode_soft_floor` / `agree_soft` programs returned
the outcome the estimator computed before they ran — answers,
`BELOW_FLOOR`, `TIE` and `RATE_GRID_EXCEEDED` (a lone weight-3 read already
leans to 1/5); 0 wrong; every answer's script prints `VERIFIED True`. The
existing builtins answer as before.

### 2.9 J9 — Lean: met

`RequestProject/GLM/RatePosterior.lean` proves `soft_floor_error_le`,
`rate_posterior_prod`, `naive_rate_underestimates` and
`read_marginal_eq_coset_mass`; no `sorry`, axioms `propext`,
`Classical.choice` and `Quot.sound` only.

## 3. What this round moved, and what it leaves

**Moved.** The machine can answer without a declared rate: `decode_soft`,
`decode_soft_floor` and `agree_soft` estimate it from the reads, answer with a
marginal confidence whose floor keeps its promise on the prior average, and
refuse `RATE_GRID_EXCEEDED` when the reads lean above every hunted rate.

**Leaves.** The fixed-rate promise is not guaranteed: 2 cells at 1/10 and all
of 1/5 break it; a finer grid, a higher guard point or a session corpus
(larger `n`) are the candidate repairs, each measurable with this engine. The
plain `resolve` and `agree` keep their contract (the owner's aside): they do
not print a session-marginal confidence.

## 4. The repairs, measured (Phase 86)

§3 left the fixed-rate breaks with three candidate repairs — a finer grid, a
higher guard point, a larger corpus — each "measurable with this engine". Phase
86 measured them, as the short first step of the round. The repairs were
declared in code before the table was read
(`rate_posterior_marks.REPAIRS`), with one rule added beside them: the
standard device for a guarantee at every fixed value of a parameter rather
than on the prior average, which is to answer with the confidence at the
**upper end of a credible set** of rates (the largest grid rate carrying
posterior mass at least 1/100). Because confidence falls as the rate rises
(`posterior_antitone_rate`, Phase 80), this is never above the confidence at
any rate inside the set. The larger corpus is already J3's `n = 20` column.

Recomputed by `python3 -m glm_universal.tools rate-posterior --repairs`
(about two minutes, exact): the same 525 cells as J3 for each repair.

| repair | grid (hunted, guard) | rule | broken | on the grid | at 1/5 | retention at 1/20, 999/1000, n = 20 |
|---|---|---|---|---|---|---|
| R0 as shipped | Phase 82's five, 1/5 | marginal | 37 | 2 | 35 | 0.8790 |
| R1 finer grid | + the four midpoints, 1/5 | marginal | 37 | 2 | 35 | 0.8172 |
| R2 guard raised | + 1/5 hunted, 3/10 | marginal | 35 | 2 | 33 | 0.8790 |
| R3 finer and raised | + midpoints, 3/20 and 1/5, 3/10 | marginal | 37 | 3 | 34 | 0.8172 |
| R4 upper credible | Phase 82's five, 1/5 | upper | 32 | **0** | 32 | 0.8561 |
| R5 upper and raised | + 1/5 hunted, 3/10 | upper | 26 | **0** | 26 | 0.8561 |

**What it says.**

* **A finer grid and a higher guard point do not repair the breaks.** Neither
  touches the two on-grid cells at 1/10 (R3 adds a third), and the breaks at
  1/5 barely move.
* **The upper-credible rule removes every on-grid break** (R4, R5: 0 of the
  175 on-grid cells), at a small retention cost (0.8790 → 0.8561 at 1/20,
  0.3571 → 0.3555 at 1/10). This is the one repair that works, and it is the
  standard one.
* **Nothing repairs 1/5, and the reason is a theorem, not a tuning.** At a
  fixed true rate the reads are independent, so the corpus says nothing about
  whether the subject is right once its coset class is known. The residual of
  *any* rule that decides from (corpus, subject class) is therefore the
  answered-mass average of `1 − conf_r(d)` over the answered classes
  (`fixed_rate_identity`, checked exactly on every broken cell of every
  repair). At 1/5 every class a rule answers under these floors has
  `conf_{1/5}(d) < t`, so any rule that answers at all breaks the promise
  there. A rule can only keep the promise at 1/5 by never answering those
  classes, which is the oracle's refusal. The distinction is the standard one
  between a Bayesian guarantee (on the prior average, which J2 keeps) and a
  frequentist guarantee (at every fixed parameter, which needs a confidence
  set that contains the true rate).
* `RequestProject/GLM/RateRepair.lean` proves the three facts the argument
  uses: `fixed_rate_wrong_eq` (the wrong mass is the class-by-class sum once
  the corpus is summed out), `fixed_rate_keep` and `fixed_rate_break`. No
  `sorry`; the standard axioms only.

**Not shipped.** The runtime's `decode_soft_floor` keeps Phase 82's marginal
rule, because changing what a floored answer means is a change of contract.
The measurement above is what that decision would rest on: R4 is the rule to
adopt if the owner wants the on-grid promise at every fixed rate as well as on
average. `tests/test_rate_posterior.py::TestTheRepairs` pins the table's
deciding cells.
