# 111 — The calibrated relaxation solver, and the gate that stopped it

**Run 155.** The brief was a repair job with a tripwire in it. Run 154 shipped a two-stage solver
whose Stage 1 was a single-square random walk, and whose negative on twenty rows was therefore
worth nothing: a search that cannot pack five squares into a 2.71 box cannot tell you anything
about 118 of them. So this run had three parts — put a **calibration gate** in front of the
solver, replace both stages' engineering, and only then spend budget on `n = 101..1000`.

The third part did not happen, because the second part did its job:

    n = 5    L <= 2.71   PASS   max overlap -1.367e-4   (1 restart,  51 s)
    n = 10   L <= 3.72   PASS   max overlap +4.441e-16   (1 restart,  97 s)
    n = 39   L <= 6.85   FAIL   max overlap +3.301e-2    (1 restart, 526 s)

The gate says the solver can find genuine tilted packings that beat the integer grid at five and
ten squares, and cannot at thirty-nine. Under the brief's own rule — *do not proceed to `n > 100`
until the solver passes this calibration gate* — the run stops here. **No target row was run, no
candidate was produced, nothing was promoted**, `submission.csv` and root `WHITEBOARD.md` are
untouched, and the score is still **22.217428576** (554 beats, 446 grid ties).

A gate that cannot fail is decoration. This one failed, and the rest of this document is what it
bought.

## 1. The gate itself

`proposal_anneal.py --selftest` now runs the three cases above before anything else. Each case is
**cold**: the seeds are a random fill, a jittered square lattice and a strip stack — no known
packing, no coordinates from the table, and no case may be handed its answer. The pass rule is the
brief's: a pose at side `L <= threshold` whose maximum pairwise overlap is `< 1e-6`. Each threshold
is strictly below the plain integer grid's side (`ceil(sqrt n)` = 3, 4, 7), so a pass is a packing
that *beats the grid*, exactly the capability the target rows need.

| n | side target | grid side | best overlap found | restarts | wall time | verdict |
|---:|---:|---:|---:|---:|---:|:--|
| 5 | ≤ 2.71 | 3 | −1.367e-4 | 1 | 51 s | **PASS** |
| 10 | ≤ 3.72 | 4 | +4.441e-16 | 1 | 97 s | **PASS** |
| 39 | ≤ 6.85 | 7 | +3.301e-2 | 1 | 526 s | **FAIL** |

Two of those numbers deserve a note rather than a celebration. `n = 10` passed at `+4.4e-16` —
an overlap of four parts in `10^16`, which is inside the brief's `1e-6` line by ten orders but is
not, strictly, a legal pose for the exact gate; it is a numerically feasible configuration, and
the exact stage would have to snap and repair it like any other. `n = 39` failed with one restart
in 526 s: the budget is checked *between* restarts, and a single `solve` at 39 squares takes longer
than the whole case budget, so the case got one attempt and not the three or four the loop was
supposed to give it. That is a defect in the gate's accounting, and it is recorded as one — but it
does not change the verdict, because the thing that made `n = 39` slow is the thing that would
make `n = 118` hopeless: see §5.

## 2. Stage 1: what replaced the random walk

The old `solve` was a per-square Metropolis walk with a schedule tuned by hand. The new one has
three parts, and the calibration is what forced each of them:

**A smooth multi-body energy.** For every pair, the four SAT axes give four penetrations
`need_k − |proj_k|`; the pair's penetration is the **minimum** over those four (a pair is separated
if *some* axis separates), smoothed with a log-sum-exp at temperature `tau = 1e-3`, then passed
through a softplus at `xi = 1e-4` so that an overlap costs its square and a gap costs nothing.
Walls are penalised the same way. Everything is vectorised over the `n(n−1)/2` pairs, so one
energy evaluation at `n = 118` is a handful of numpy calls on a 6,903-wide array.

**Joint L-BFGS-B relaxation.** All `3n` coordinates — two positions and one angle per square —
move together, with a numeric gradient (the vectorised energy is what makes that affordable).
This is the difference between "every square reacts to its neighbours" and "one square jitters and
hopes".

**Inflation, then basin-hopping.** `shrink_path` starts at `1.30 × L`, relaxes, shrinks by 1% and
repeats — the Lubachevsky–Stillinger compression, with the pose kept feasible as the box closes.
That alone gets close on easy cases and jams on hard ones, so `basin` then perturbs one square
(position and angle) and re-relaxes, keeping the best pose: the global escape from the jammed local
minima that pure gradient descent cannot leave.

**The quench** is now simultaneous, which is the brief's other demand: every violating pair
accumulates a displacement for *both* its squares before anything moves, then the pose is clamped
into the box. Run 154's sequential sweep pushed one pair's overlap into its neighbour and made 18
of 20 rows worse; the Jacobi version cannot do that, because the whole residual field moves at
once.

Two bugs the calibration caught, both of which would have poisoned the target run silently:

1. **The SAT measure was inverted twice.** The first draft took the *maximum* over the four axes
   (a pair "overlaps" if any axis says so — the opposite of SAT), and a `penetration = need − proj`
   convention then had a second sign error in the violation list. The symptom was a solver that
   reported `1.0` of overlap for a known-good five-square lattice, and a clamped grid "penetrating"
   by a whole unit. Without the gate this would have looked like "the solver is weak on hard rows";
   with it, a five-square packing at 2.71 either happens or it does not.
2. **The shrink schedule was far too coarse** (six stages). The pose jammed at the first stage and
   every subsequent relaxation fought a box it could not hold. A 1% step with a short relax keeps
   the pose on the feasible manifold.

## 3. Stage 2: high-precision spinors and simultaneous repair

**Continued fractions at `q <= 100000`.** Run 154 snapped `t = sin/(1+cos)` with
`limit_denominator(32)`, which quantises the angle to about `1e-3` rad — `1.5e-2` of positional slop
at `k = 15`, larger than the overlaps being chased. `cf_convergents` now walks the continued
fraction of the exact decimal `t` and returns the last convergent inside `q <= 1e5`: the 3-4-5
angle comes back as `t = 1/2` *exactly*, and the 45-degree angle as `q = 80782` with
`|t − p/q| = 5.42e-11`, i.e. under `3e-9` of positional slop at `k = 15` — two orders below the
project's `1e-8` noise floor.

**Simultaneous damped-residual relaxation, in `Fraction`.** `relax_simultaneous` accumulates every
violating pair's displacement into a per-square accumulator, applies the whole field damped at
`1/2`, clamps the pose into `[0, L]^2`, and repeats. It is exact — every number is a `Fraction` —
so the residual it reports is a fact about the pose, not a tolerance. Damped Jacobi converges
geometrically, which means it approaches contact but never lands on it; the last step is an
**exact closure** that separates the worst remaining pair by `pen + 1e-18` split between both
squares. `1e-18` is ten orders under the project's noise floor and 22 orders under the `1e-8`
margin rule, and it turns "asymptotically short of legal" into "legal with strict clearance".

Eight controls now stand behind Stage 2 (24 decision functions, 0 naming float):

| control | what it proves |
|---:|---|
| 1 | the spinor: `t = 1/2 → (3/5, 4/5)`, `t = 1 → (0, 1)`, exactly on the circle |
| 2 | the CSV angle `0.927295218001612` snaps back to `t = 1/2` — the 3-4-5 word from a decimal |
| 3 | a rational 3x3 grid gates (L = 3, 20 contacts) and its certificate passes C1/C2 |
| 4 | simultaneous relaxation: a 0.1-overlap chain reaches residual exactly 0 and the gate passes |
| 5 | an overlapping pose is refused by the gate before the margin is consulted |
| 6 | a legal pose that only ties the delivered side fails C2 |
| 8 | continued fractions at `q <= 1e5`: exact words recovered, 45° good to 5.4e-11 rad |
| 7 | bytecode audit: 24 decision functions, 0 naming float |

## 4. The clamped-grid floor

The brief asked for the trivial baseline to be logged for every target row, so that no solver
result can be reported without something to beat. `snap_certify.py --baseline` builds the `k x k`
lattice, clamps it into `L = k − 1e-4` and measures its penetration *exactly* (Fractions, the same
`pair_axes` the gate uses):

| n | k | tier | clamped-grid penetration | violations |
|---:|---:|:--:|---:|---:|
| 117 | 11 | A | 1.000e-4 | 17 |
| 140 | 12 | A | 1.000e-4 | 19 |
| 118 | 11 | A | 1.000e-4 | 18 |
| 165 | 13 | A | 1.000e-4 | 21 |
| 141 | 12 | A | 1.000e-4 | 20 |
| 192 | 14 | A | 1.000e-4 | 23 |
| 221 | 15 | A | 1.000e-4 | 25 |
| 166 | 13 | A | 1.000e-4 | 22 |
| 193 | 14 | A | 1.000e-4 | 24 |
| 222 | 15 | A | 1.000e-4 | 26 |
| 111 | 11 | B | 1.000e-4 | 11 |
| 133 | 12 | B | 1.000e-4 | 12 |
| 112 | 11 | B | 1.000e-4 | 12 |
| 157 | 13 | B | 1.000e-4 | 13 |
| 134 | 12 | B | 1.000e-4 | 13 |
| 113 | 11 | B | 1.000e-4 | 13 |
| 158 | 13 | B | 1.000e-4 | 14 |
| 135 | 12 | B | 1.000e-4 | 14 |
| 184 | 14 | B | 1.000e-4 | 15 |
| 159 | 13 | B | 1.000e-4 | 15 |

The number is exactly the shrink (`1e-4`), because the only cells that move are the ones on the far
wall, and each lands `1e-4` inside its neighbour. Two consequences are worth stating plainly:

- The pass line is `1e-5`, so the **trivial baseline is already ten times worse than passing**.
  Any solver result above `1e-4` is worse than "do nothing", and run 154's best pose
  (`1.49e-2` at n = 112) was **149× worse than the clamped grid**. The gate and the baseline
  together make that impossible to miss next time.
- A row only becomes interesting when a pose beats `1e-4` *by an order of magnitude*, and the
  only way to do that is to rearrange the lattice rather than compress it — which is exactly the
  capability the calibration gate is testing for.

## 5. Why `n = 39` failed, and what it costs

The failure is not mysterious: at 39 squares the pose has to hold a density the grid cannot
(39 cells in `6.85^2`), so the whole arrangement has to be found, not polished. The measured costs
are the honest part:

- one `solve` at `n = 39` takes **~8 minutes** (a 1% shrink path plus 160 basin-hopping steps, each
  an L-BFGS run over 117 coordinates with a numeric gradient);
- at `n = 118` the same code has **354 coordinates and 6,903 pairs** — 19× the pair count and 3× the
  coordinates — so a single restart would be hours, and a search that needs dozens of restarts is
  out of reach;
- and the gate's budget is checked between restarts, so a slow case gets one attempt. That is a
  gate bug, but fixing it would only have bought `n = 39` two more 8-minute attempts.

So the honest reading is not "the solver almost passed". It is: **the method is calibrated where it
is cheap and unaffordable where it matters**, and the brief's gate caught that before another
twenty rows were spent. The next step is a cheaper inner loop, not a longer run:

1. **Analytic gradients.** The energy is a composition of softmax, softplus and absolute values; its
   gradient w.r.t. `(x, y, θ)` is a page of algebra and would replace `3n` finite-difference
   evaluations with one pass — 100× at `n = 118`, which is the difference between hours and minutes.
2. **Bounded restarts.** A per-solve step cap (not just a per-case budget) so the gate tests
   capability rather than one lucky slow run.
3. **Structured seeds at density.** Random and jittered-lattice seeds are hopeless at 83% density;
   the seeds that work in this literature are *defect lattices* (a lattice with a known number of
   cells removed, then healed), which the strip seed only approximates.

Until (1) lands, the two-stage solver stays where it is: calibrated at five and ten squares, and
refused at thirty-nine.

**Kept green.** `snap_certify --selftest` 8/8 (24 decision functions, 0 float offenders);
`exact_words` 8/8; `scale_motifs` 15/15; `sqscore` **22.217428576**, 554 beats, 446 grid ties;
`record_guard` clean; `glm_wheels --audit` **708 functions, 0 offenders** with `snap_certify` in the audited list.
`proposal_anneal` remains the declared float stage and is excluded from that audit by design; its
own shaping helpers are audited inside `--selftest` for information only. `n <= 100` was not
touched, and no candidate reached C1.
