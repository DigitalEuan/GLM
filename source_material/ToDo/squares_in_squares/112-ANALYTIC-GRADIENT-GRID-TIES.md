# 112 — The analytic gradient, the time cap, and the gate that still says no

**Run 156.** The brief named three bottlenecks from run 155 §5 — finite-difference gradients, restarts
with no internal clock, and seeds that do not know where a `k^2 - r` row lives — and asked for them to
be fixed and the calibration gate to pass in under a minute, so that fifteen grid ties could finally be
searched. All three fixes are in, measured, and committed. The gate is now fast (59.1 s) and its first
check passes (the gradient is exact to `2.46e-9`). **The three packing cases still fail, so the gate
still refuses the `n > 100` run**, and no row was searched or promoted.

    calibration gate (analytic gradient, then cold-start packings)
      0. analytic gradient vs finite differences: max |error| = 2.46e-09 over 135 coordinates  PASS
      n= 5  L <= 2.71  grid side 3  found L = 2.710000  max overlap +1.450e-01  restarts 1  (8.2s)  FAIL
      n=10  L <= 3.72  grid side 4  found L = 3.720000  max overlap +9.333e-02  restarts 1  (12.3s)  FAIL
      n=39  L <= 6.85  grid side 7  found L = 6.850000  max overlap +3.626e-02  restarts 3  (38.5s)  FAIL
    calibration gate: 59.1s
    CALIBRATION FAILED

The important sentence in that block is the first one: **the arithmetic problem is solved.** What is
left is a search problem, and the section 4 records the evidence that says so. Nothing was promoted;
`submission.csv` and root `WHITEBOARD.md` are untouched; the score is still **22.217428576** (554
beats, 446 grid ties).

## 1. The analytic gradient

`energy_grad(u, n, L)` returns the smooth energy **and** `dE/d(x, y, θ)` for all `3n` coordinates in one
vectorised numpy pass. The energy is four compositions and each is differentiated in closed form:

| layer | form | derivative |
|---|---|---|
| axis penetration | `a_k = need_k − |proj_k|`, four per pair | `da_k/dx_I = sgn·q_k`, `da_k/dx_J = −sgn·q_k` |
| smooth minimum | `smin = m − τ log Σ exp((m−a_k)/τ)` | `∂smin/∂a_k = w_k`, the softmax of `−a/τ` |
| softplus | `pen = ½(smin + √(smin²+ξ²))` | `∂pen/∂smin = ½(1 + smin/√(smin²+ξ²))` |
| walls | `κ·(excess)²` with `excess = f(h(θ), x, L)` | `∂/∂x` by the active indicator, `∂/∂θ` through `dh/dθ` |

Angles enter twice — through the axis direction (`dq/dθ`) and through the *other* square's projected
half-extent — and both terms are carried explicitly; the position derivative had to be signed against
`dx = x[I] − x[J]` (the convention `pair_pens` uses), which is exactly the kind of error a finite
difference check catches in one line and a search would hide for a week.

**Verification** (inside `--selftest`, control 0): central differences at `h = 1e-6` over all 135
coordinates at `n = 5` and `n = 40` agree with the analytic gradient to **`2.46e-9`**, comfortably
inside the brief's `1e-7`. The check is now part of the gate, not a script someone might forget.

**Measured speedup** (`n = 118`, the real target size):

| quantity | measured |
|---|---|
| one energy evaluation | 5.28 ms |
| one energy **+ gradient** evaluation | 6.54 ms (1.24× the value alone) |
| 60 L-BFGS-B iterations at `n = 39`, finite differences | 3.12 s |
| 60 L-BFGS-B iterations at `n = 39`, analytic (`jac=True`) | **0.04 s** — **86.1×** |
| energy-equivalent passes per gradient | 59× fewer (`3n+1 = 118` finite differences vs 1 analytic) |
| what fits in 12 s at `n = 118` | **~1,835** gradient passes, against **~6** numerically |

That is the brief's "50–100×" met at 86× on the same iteration budget, and the last row is the one that
matters: a restart now does thousands of multi-body steps where run 155 did six.

## 2. The hard wall-clock cap

`Cap(seconds)` is a callable handed to **both** optimisers — L-BFGS-B's `callback=` and
basinhopping's `callback=` — and it raises `StopRun` from inside the iteration loop when the clock
passes. `relax` keeps the last accepted iterate, `basin` keeps the last perturbed state, and both return
a pose rather than an exception. The cap is a property of the *restart*, so nothing downstream can
inherit a 500-second stall.

Evidence that it fires and is tight: the gate's three cases now take **8.2 s, 12.3 s and 38.5 s** with
caps of 8, 12 and 15 seconds per restart, and every `solve` reports `cap_hit: True` at exactly its cap.
Run 155's `n = 39` case spent **526 s in one restart** and never got a second attempt; the same case
now gets three attempts inside 38.5 s.

## 3. Seeds that know where the row lives

`seed_defect` removes the missing `m^2 − n` cells from the **boundary and corners** (corners first),
which is where a `k^2 − r` row's deficit actually is, and `seed_corner` builds a `floor(√n) × floor(√n)`
lattice block plus the leftover cells tilted into the margin — the block-plus-`r` structure the target
rows have. Both join `strip`, `lattice` and `random`; all five are random in angle and jitter, so they
are hypotheses about where the packing lives, not copies of a known pose.

## 4. Why the gate still fails, and why that is now a useful statement

Run 155 failed at `n = 39` only. Run 156 fails at `n = 5` as well, with a *faster and better-armed*
solver — and that is not a regression, it is the arithmetic being taken out of the way so the real
obstacle becomes visible. Twelve configurations were measured, all with thousands of basin-hopping steps
in seconds:

| n | seeds tried | perturbation (pos, ang) | best overlap |
|---:|---|---|---:|
| 5 | defect, corner | (0.06, 0.30), (0.35, 1.2), (0.8, 1.6) | 8.2e-2 |
| 10 | defect, corner | (0.06, 0.30), (0.5, 1.4) | 9.7e-2 |
| 39 | defect, corner, strip, random | (0.06, 0.30) | 2.7e-2 |

Every one of them jams in the same kind of place: a lattice block plus one or more squares that cannot
get *between* the block's cells. The `n = 5` optimum at `2 + 1/√2` needs its fifth square to sit in a
pocket between the block's corners — a **topological** rearrangement, reached by moving a square through
a gap that is closed at the current pose. A perturbation-plus-relaxation move cannot do that: it
perturbs one square, the square is pushed back out by the same contacts, and the Metropolis test rejects
the move. More steps and a better gradient do not change that; they just explore the same basin faster.

That is why the honest next step is a **move set**, not a faster idealisation of the same move set:

- a **teleport-into-hole** move (run 127's `legal_slide` family already measures void seats exactly);
- a **block swap** that exchanges a lattice cell with a tilted cell in the margin;
- or a **constructive enumeration** of the block-plus-`r` topology, which is a finite combinatorial
  object (where the `r` tilted cells sit relative to the block's corners), gated at the end by Stage 2.

Until one of those lands inside `proposal_anneal.py`, the gate refuses the target run — correctly.

## 5. The floor any result must beat

Carried over from run 155 and still the right frame: `snap_certify.py --baseline` measures the trivially
clamped `k × k` grid at `L = k − 1e-4` exactly in `Q`, and it penetrates **1.000e-4 on all twenty target
rows** (11–26 violating pairs each). The pass line is `1e-5`, so the trivial baseline is *ten times worse
than passing*, and a solver result above `1e-4` is worse than doing nothing. Run 154's best pose
(`1.49e-2`) was 149× worse than the baseline; run 156's best at `n = 39` (`2.7e-2` at side 6.85) is in
the same regime. The gate exists so that number is never mistaken for progress.

**Kept green.** `snap_certify --selftest` 8/8 (24 decision functions, 0 float offenders);
`exact_words` 8/8; `scale_motifs` 15/15; `sqscore` **22.217428576**, 554 beats, 446 grid ties;
`record_guard` clean; `glm_wheels --audit` 0 offenders with `snap_certify` in the audited list.
`proposal_anneal` remains the declared float stage; its shaping helpers are audited in `--selftest` for
information, and the analytic gradient is the only new decision-bearing arithmetic in it, checked
against finite differences at `2.46e-9`. `n <= 100` was not touched and no candidate reached C1.
