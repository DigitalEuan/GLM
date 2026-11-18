# Run 40 (2026-11-17): the language as an objective; the stir as a collective move

**User order.** After run 39's reading of the CRAM paper — one transfer (the
learned relation cost ranks seeds), two refusals (the threshold is degenerate;
focused relaxation loses) — the order was: list the ideas on the whiteboard and
start trying them, in that direction.

**Score: unchanged.** No packing found (`E <= 1e-6` for 0 runs in every arm);
`submission.csv` and the delivered table untouched.

## What was built

`scripts/cram_language.py` — PL-1 (`F = E + lam * cbar`, `graded` and `tail`
schedules) and PL-2 (collective patch move, `k = 4`, rigid, rotation with
p = 0.3), plus `--slope` and a `--check` recovery test. Ledger
`workspace/push/cram_language.json`. Record `07-LANGUAGE-OBJECTIVE.md`.

## The recovery test, before anything else

`lam = 0` reproduces run 39's stored `full` medians exactly — 2.333e-03 at
(n = 20, amp 0.01) and 9.208e-02 at (n = 110, amp 0.04), to 1e-12. So a
`lam > 0` difference is a difference of objective alone.

Two instrument facts recorded rather than hidden: (a) run 39's acceptance
proxy uses half the true pair increment, which is reproduced deliberately for
the control and which is why `coordinate_polish` recovers 2–8× on its
endpoints; (b) the first `tail` arm restarted its incumbent at the objective
switch — discarding the annealer's best and reading as a property of the
objective. Fixed, re-run, and only the fixed version is quoted.

## Measured

* **`--slope`: the learned cost has no derivative.** Perturbing one body by up
  to `eps` gives a median `|d cbar|` of 9.5e-02 at n = 60 and 1.8e-02 at
  n = 240 — **the same at eps = 1e-3 and at eps = 1e-1**. A 0.001 displacement
  is not a small change in the language; the potential is piecewise constant
  with jumps of order 1e-2. Direct test: at n = 110, amp 0.04, `lam` = 0.1,
  1.0, 1e3 and 1e6 give **identical** results — lexicographic from 0.1 onward.
  There is no weight at which the language acts as a gradient beside `E`.
* **PL-1 negative.** `graded`: `lam > 0` wins on polished `E` in 6/16 cells,
  by 5–6%, and loses by 3.7× to **125×** (n = 20, amp 0.005: 6.28e-05 →
  7.88e-03), while `cbar` falls by at most 5% anywhere. `tail`: neutral at
  n = 110/240 (0.97–1.00×), catastrophic at n = 20/60 (13× to 154× worse).
  One real cell: n = 240, amp 0.01 → 3.12e-03 against 4.42e-03 at 3% lower
  `cbar`. Not a mechanism.
* **PL-2: a narrow positive.** At equal *move* budget (4× the displacements,
  so handicapped in its favour) the patch arm beats `full` in 2 of 16 cells —
  n = 110, amp 0.04 (2.40e-02 vs 3.74e-02, 0.64×) and n = 240, amp 0.01
  (1.39e-03 vs 4.42e-03, 0.31×) — is within ±25% in 13, and worse in 1. Both
  wins sit at mid corruption and large `n`, the same corner where run 39's
  idea D won. It is the first proposal-grammar change in this project to beat
  one-body descent anywhere, and it does not beat it generally.

## What the run says to build

The failure is the objective's *class*, not its weight: a step function has no
infinitesimal form to descend. Next is a C¹ potential — kernel density over
the 21,602 contacts, bandwidths at the bin widths — then the seam at the three
top aims, then the patch at matched displacement.

## Limits

Two seeds, medians, no error bars; only >25% differences are called out. No
run reached feasibility, so these are descent rates, not solvers. `cbar` is the
idea-A histogram as fitted (rows n ≤ 120); a smoothed potential is a different
objective and none of these numbers transfer to it. No Lean, no intake, no GLM
claim.

---

# Run 40, second leg (17 November 2026): PL-10 and the matched stir

**Order.** Push on as logical — i.e. the two items the first leg named.

**Score unchanged; no packing found (0 runs at E ≤ 1e-6).**

`cram_language.py` gained `--smooth` (PL-10) and `--patch-matched` (PL-2's
caveat). Same ledger; record `07-LANGUAGE-OBJECTIVE.md` §7–§9. The `lam = 0`
recovery test still reproduces run 39 exactly after the refactor.

## PL-10 — the C¹ potential: the first objective-level positive

Kernel density over the same 21,602 contacts, 360 × 240 grid, Gaussian σ = half
a bin (30 angle bins, 40 distance bins), `U = −log p`, bilinear. Fit 0.4 s.
Polished `E`, best λ per cell, ratio to the arm's own λ = 0:

| n | 0.005 | 0.01 | 0.04 | 0.08 |
|---|---:|---:|---:|---:|
| 20 | 1.03× | 1.01× | **0.18×** | **0.23×** |
| 60 | 1.00× | 0.92× | **0.50×** | **0.70×** |
| 110 | 1.00× | 1.00× | **0.59×** | 0.95× |
| 240 | 1.00× | **0.31×** | **0.76×** | 0.97× |

10 of 16 improve, best 5.9×, and the language cost *falls* with the energy in
every improving cell — the opposite of the step-function arm, where every gain
cost feasibility. The regime is measured: gentle corruption is inert (the
records sit at the density maximum, so U's gradient is ~0 there by
construction) and a wrong λ at gentle corruption costs 8.7×–17.8×. Hence the
weight has to be scheduled by corruption — logged as PL-11.

## PL-2 at matched displacement — caveat closed

The patch wins survive at `moves/4`: n = 110, amp 0.04 → 2.38e-02 against
3.74e-02 full (**0.64×**); n = 240, amp 0.01 → 1.39e-03 against 4.42e-03
(**0.31×**), identical at both budgets. Heavy corruption still loses (1.18×,
1.22×).

## The ceiling is visible

Record contact set vs the result's, three cells: **Jaccard 0.018–0.054** at
every energy (6 of 285 contacts; 36 of 669). Positions do approach the record
at large n (1.8× and 2.5× closer) and the bbox moves toward the target `L`
(n = 20: 5.048 → 5.008 against 5.000), so the language is a shape prior, not a
decoder of the record. No chain in run 39 or 40 has ever reproduced a record's
contact word. Logged as PL-12: the open question is whether the target L
should be the record at all, rather than something below it.

---

# Run 40, third leg (17 November 2026): the rule, and the honest number

**Order.** Best-of-seven λ per cell is selection bias — replace it with a rule
derived from the seed's own `cbar`, re-run the 16 cells for an honest number,
then aim that rule below the record.

`lam(seed) = (excess / e0)^2` with `excess = cbar_smooth(seed) −
cbar_smooth(record)`. One parameter, and `e0` is fitted on a grid **disjoint**
from the test cells (n = 30/80/150/300 × amps 0.02/0.06, λ grid 0.1…1000,
predicted λ read off the measured grid by log-log interpolation).
**e0 = 0.3162**, training mean |log ratio| 0.075 (691 s).

## The honest number

| | geo mean ratio | median | ≥5% better | ≥5% worse | best | worst |
|---|---:|---:|---:|---:|---:|---:|
| best-of-seven (§7, biased) | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| fitted rule (honest) | **0.898** | 0.977 | **5** | **1** | **0.417** | 1.055 |

The selection was worth **0.75× of the honest figure** — §7's 33% reduction is
**10%** in fact. Per cell: 1.03, 0.95, 0.81, 0.42, 1.00, 1.00, 0.96, 0.96,
1.00, 1.00, 1.00, 0.91, 1.00, 0.67, 0.93, 1.05. The effect is real and it is
concentrated at the heaviest corruptions (n = 20 amp 0.08 → 0.42×; n = 240
amp 0.01 → 0.67×), absent in the gentle ones.

**Why it undershoots:** `e0 = 0.316` gives λ = 0.001–4.3 on the test range
while the measured optima were 100–1000 for excess ≥ 0.10 — two decades low.
The training plateaus are flat (λ = 10…1000 all inside 1.05×), and a
mean-log-ratio fit lands in their middle. Declared next fit (PL-13): same form,
same disjoint grid, **minimise the maximum |log ratio|** over the training
cells, then re-test the 16 once.

## Aiming below the record — null, and weak

At `L0(1 − d)`, d = 1%/2%, amp 0.02, four n: **0 of 8 cells produced a gated
`L` at all**, the same wall as run 39's 0-of-24. The rule sets λ = 0.008–0.04
there, so the language term is effectively off and these runs are close to a
λ = 0 control. The push question is not answered; it waits on PL-13.

Ledger sections after this leg: `rule_fit`, `rule`, `push_rule` beside the
earlier arms. `lam = 0` recovery test still exact.

---

# Run 40, fourth leg (17 November 2026): the min-max refit

**Order.** Refit λ by min-max on the same disjoint grid, re-test the 16 cells
and the below-record targets once with the frozen rule, and answer whether the
push is still null when the language term is actually engaged. Proposed: train
on all known optimal packings up to n = 10,000.

## Two defects in §10's fit

1. **The criterion was degenerate.** Mean |log ratio| is minimised by λ → 0,
   since every ratio → 1.0. Measured on the stored grid: 0.282 at the fitted
   e0 against 0.072 at e0 = 10. §10's 0.898 came from a rule fitted to do
   nothing.
2. **Both fits sat at boundaries.** Min-max regret chose e0 at the opposite
   edge (1e-4 → λ = 1e4), extrapolating past the largest measured λ, so the
   training grid was measured at λ = 1e4 and 1e5 as well and the refit
   repeated. It stayed at 1e4 — correctly, the training minima are at
   λ ≥ 1e4 on most cells.

Frozen rule: `e0 = 1e-4`, **λ = 10⁴ on all eight training cells** (max regret
0.087). The rule has saturated: it is no longer a rule in the excess.

## The honest re-test, term fully engaged

| | geo mean | median | ≥5% better | ≥5% worse | best | worst |
|---|---:|---:|---:|---:|---:|---:|
| best-of-seven (§7, biased) | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| mean-\|log\| rule (§10) | 0.898 | 0.977 | 5 | 1 | 0.417 | 1.055 |
| **min-max rule, λ = 10⁴** | **1.143** | 0.981 | 8 | 7 | 0.255 | **10.60** |

By corruption: amp 0.005 **3.57× worse**, 0.01 1.47× worse, **0.04 0.49×**,
**0.08 0.67×**. A fully engaged language term is the best objective this
project has at mid/heavy corruption (2.0× and 1.5×) and it destroys gentle
seeds. Net 14% worse.

**Cause: the training grid (amps 0.02/0.06 → excess 0.045–0.35) contains no
gentle cell**, so min-max bought mid/heavy gains at zero fitted cost. The
criterion was not the defect; the coverage was. Logged as PL-14.

## The push, with the term actually engaged

λ = 10⁴ at every cell (excess ≈ 0.03), d = 1%/2%, four n: **0 of 8 produced a
gated `L` and 0 of 8 went below the record** (ratios 1.08/1.12, 0.82/0.89,
1.34/1.22, 0.76/0.93). The §10 null was weak because the term was off; this
one is not. The wall is mechanical.

## The 10,000 idea, measured

`proven_census`: the table stops at n = 1000, so packings to 10,000 do not
exist in this tree. The 156 proven-optimal rows (n ∈ [1, 961], 193,742
contacts) sit **99.99%** in the two lattice relation cells, against 96.07% for
all rows n ≤ 120 — they are the vacuum. And at an un-corrupted optimal packing
the excess is 0, so the rule's own form gives λ = 0: such a grid measures the
term where it is provably inert. Solved examples are the right *seeds*, not
the right *coverage* — PL-14.
