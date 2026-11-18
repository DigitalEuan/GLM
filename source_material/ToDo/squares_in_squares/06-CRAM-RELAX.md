# 06 — The CRAM translation: energy, thresholds, focused and layered relaxation

**Run 39, 2026-11-17.** Source: B. Hoover, H. Blayney, J. C. R. Whittington,
*Classical Energies Learn to Reason 1,000× Faster than Looped Models*,
arXiv:2611.17309v1 (12 Nov 2026).

**What this document is.** Four mechanisms from that paper, translated into
this project's domain and measured one at a time. The paper's claim is that
descent on an explicit energy — not a loop unrolled by backpropagation —
solves constraint puzzles faster, more stably, and with a stopping rule that
never fires on a wrong answer. The four ideas tested here were: a learned
pairwise coupling used to score candidate seeds (A), a stopping threshold
calibrated on the solved examples (B), relaxation that moves only the most
strained bodies (C), and a two-layer settle in which a coarse field settles
before the fine one (D).

**The score did not move.** No campaign here produced a packing below the
delivered table: 0 of 24 push runs, and the delivered submission is
untouched. What was produced is a measurement of which of the four ideas
transfers to continuous packing and which does not.

---

## 1. What translates, and what the domain refuses

CRAM's energy is a mean-field free energy over a **belief array** `p` of
shape `M × C` (M answer cells, C candidate values per cell), with learnable
pair costs `K_ij` between cells and a bias `B_i` per cell, descended one
cell at a time by Eq. (3):

```
v_i <- (1 - eta) v_i - eta ( sum_j W_ij p_j + B_i ),   p_i = softmax(beta v_i)
```

A packing has no `M × C` array. Its state is `n` continuous `(x, y, theta)`
triples and its constraints are metric (pairwise interior-disjointness plus a
bounding box), so:

| CRAM object | packing counterpart used here |
| --- | --- |
| cell belief `p_i` over `C` values | one body, continuous pose (no candidate set) |
| pair cost `K_ij` | cost of a **relation** (relative-angle bin × contact-distance bin), §3 |
| free energy `E(p)` | the W36/W37 hinge energy, §2 |
| one-cell Gibbs step | one-body Metropolis move (§5) |
| PL training without unrolling | histogram fit of the relation table; PL *evaluated* as a scoring rule |
| threshold `tau` from training solutions | max energy over the 1000 delivered packings, §4 |
| focused Gibbs on strained cells | moves restricted to the top-`k` strained bodies, §5 |
| latent `z` layer (Maze-Hard) | coarse phase: positions move, angles frozen, §5 |

The important structural difference, and the reason idea B comes out as it
does: CRAM's cells can be *wrong but low-energy* — that is why a calibrated
threshold is worth having and why "never stops on a wrong board" is a
non-trivial claim (their Table 4). The packing energy cannot be wrong at low
energy: it is a sum of squares of non-negative hinge terms, so `E = 0` **is**
feasibility.

---

## 2. The instrument

`scripts/cram_relax.py`. Energy, per body `i` and container side `L`:

```
E(state, L) = sum_{i<j} max(0, pen_ij)^2  +  max(0, w - L)^2 + max(0, h - L)^2
```

`pen_ij` is the SAT pair penetration of `packlib` (min over the four
edge-normal axes of `ext_i + ext_j - |d.axis|`); `w, h` are the bounding-box
extents, so the walls are free to translate — a packing's container *is* its
bounding box, which is why `packlib` reports `L = max(w, h)` rather than
checking containment.

Two checks of the instrument against the project's authority:

* the pair penetration matrix agrees with `packlib.verify`'s `worst_pen` to
  machine precision, and the incremental one-body form used inside the
  sampler agrees with the matrix form exactly (0 mismatched rows at
  `n = 5, 20, 60, 110`);
* the sampler's own objective equals `E(state, L)` to 1e-16, so the descent
  and the reported energy are the same function.

Every candidate is gated by `packlib.finalize` + `packlib.verify`; no number
below is a claim from float arithmetic, and the report carries the gate's
own `L` beside the instrument's.

The sampler reuses this project's annealing schedule (`sa_push.anneal`):
Metropolis with a geometric temperature and an improving-only tail, moves
drawn for one body at a time, half of them directed (separate the chosen
body from its worst partner by `pen`) and half isotropic. Deterministic:
`seed = 7919*n + 104729*(attempt+1) + n`, `RandomState`, no wall clock. The
variants differ **only** in which bodies are eligible for a move (C, D) or
in the seed they are given (A) — never in the move grammar or the budget.

Reproduce:

```bash
python3 scripts/cram_relax.py --census --negative --matrix --write   # ~3 min
python3 scripts/cram_relax.py --push --write                         # ~1 min
python3 scripts/cram_relax.py --pl --write                           # ~30 s
# one JSON ledger: workspace/push/cram_relax.json
```

---

## 3. Idea A — the learned relation cost, and what it is worth

**Fit.** One cost per relation cell: relative angle `(theta_j - theta_i) mod
pi/2` in six 15-degree bins, contact distance in `[1, sqrt 2]` in three
equal bins. Costs `w = -log((count + 0.5)/(N + 4.5))`, i.e. the maximum-
entropy pairwise potential at the delivered solutions — CRAM's `K_ij` family
restricted to a saturating feature, fitted **at the solutions, with no
trajectory unrolled**. 21,602 contacts over rows `n <= 120`; `w` ranges
0.6307 … 10.6741.

Contacts by relation cell (angle bin rows: `[0,15) … [75,90)` degrees mod 90;
distance bins `[1.000,1.138)`, `[1.138,1.276)`, `[1.276,1.414]`):

| | d1 | d2 | d3 |
| --- | ---: | ---: | ---: |
| 0–15° | **11,501** | 87 | **9,252** |
| 15–30° | 2 | 75 | 18 |
| 30–45° | 0 | 265 | 38 |
| 45–60° | 0 | 182 | 25 |
| 60–75° | 2 | 41 | 17 |
| 75–90° | 80 | 14 | 3 |

The table reads the task the way the paper's learned weights read Sudoku's
rows: contacts are **square-on at unit distance** or **diagonal at sqrt 2**,
plus the dilute mid-distance classes; a contact at 30–45° relative tilt and
unit distance is never observed (0 of 21,602), and the last bin is the
90-degree relabelling of the first. This is the same statement
`symmetry_audit.py` and `sat_review.py` make about the frontier from the
other direction.

**Does it score seeds?** Two controls, 55 rows (`6 <= n <= 60`), mean cost
per near pair (lower = more record-like):

| | median cost |
| --- | ---: |
| delivered records | **0.6307** |
| angle-destroyed (angles redrawn in `[0, 90°)`) | 7.4147 |
| position-destroyed (centres redrawn in the box) | 1.6458 |

AUC (probability a record scores lower than a control): **1.000** against
the angle control, **0.794** against the position control. So the relation
table is a perfect detector of "these are record angles" and a good, not
perfect, detector of record geometry.

**Does the score predict what relaxation reaches?** For 16 corrupted records
per `n`, scored by the CRAM pseudolikelihood (six local candidate poses per
body, `log softmax` of the true pose) and then relaxed with the same budget:

| n | Spearman (score vs final E) | median final E, best-scored quarter | worst-scored quarter |
| ---: | ---: | ---: | ---: |
| 40 | 0.368 | 0.0722 | 0.5361 |
| 70 | 0.744 | 0.1263 | 2.9468 |
| 110 | 0.562 | 0.1836 | 2.9076 |

**Verdict A — stands, as a ranking rule.** The learned relation cost carries
real information about which seed will relax better (rho 0.37–0.74; the
best-scored quarter lands 4–23× lower in energy than the worst-scored). It
does **not** put a seed below the record and it does not substitute for the
descent: it ranks seeds, and the ranking is strongest where the corruption
is geometric rather than angular. Concretely, the usable form is the one the
brief proposed — score candidate motif seeds first, then commit the
relaxation budget to the best-scored ones.

---

## 4. Idea B — the calibrated threshold, and why it is degenerate here

`tau` is taken exactly as CRAM takes it: the highest energy over the solved
examples, plus tolerance.

| measurement | result |
| --- | --- |
| delivered packings with `E <= 1e-12` at their own `L` | **1000 / 1000** |
| `tau` (max energy over the 1000) | **0.0** |
| corrupted boards (`n = 3..40`, 8 per row) accepted at `tau` | **0 / 304** |
| lowest energy seen on a corrupted board | 7.16e-3 |

So the stopping test is **sound**: four orders of magnitude separate the
worst corrupted board from the accepted set, and it never stops on an
infeasible board. But it is also **binary**: `E = 0` is exactly feasibility,
so the calibrated threshold is the same object as `packlib.verify`, and it
can carry no distance information. The paper's use of `tau` to grade
difficulty and to trip escalation has no counterpart here:

| squeeze of the delivered `L` | rows at or below `tau` (of 400, `n <= 400`) | median `E` |
| --- | ---: | ---: |
| 0.1% | 0 | 4.33e-4 |
| 0.25% | 0 | 2.70e-3 |
| 0.5% | 0 | 1.08e-2 |
| 1% | 0 | 4.33e-2 |

Every row leaves the accepted set at the first squeeze and then only gets
worse. A layer-escalation rule of the form "if `E > tau_L` after a fixed
number of steps, escalate" would therefore fire on every puzzle at every
depth — it grades nothing.

**Verdict B — does not transfer.** The threshold is sound but degenerate:
in a domain whose energy is a feasibility hinge, `tau = 0` *is* the answer
test, so the calibrated-threshold and escalation parts of the paper have no
work to do. What does transfer from idea B is the paper's *second* stopping
rule — **"no single-cell change lowers the energy"** — which is meaningful
here and is implemented as `coordinate_polish` (§5); it is the only stop
criterion that carries information in this domain, and (see §6) it never
fired inside our budgets.

---

## 5. Ideas C and D — focused and two-layer relaxation

Matrix: rows `n in {20, 60, 110, 240}`, seeds corrupted at four amplitudes
(angle sd in radians; position shift a quarter of that, scaled by the
container); target `L` = the delivered side, where a feasible answer
provably exists (the record itself); 8,000 moves, two seeds, identical for
every variant. `E` is the median over the two chains, **after the annealer /
after the single-body polish**. `rec` counts runs reaching `E <= 1e-6`; it is
0 in every cell for every variant.

| n | amp | full | focused | two-layer |
| ---: | ---: | --- | --- | --- |
| 20 | 0.005 | 6.62e-4 / 6.28e-5 | 6.21e-4 / 6.65e-5 | 6.31e-4 / 6.44e-5 |
| 20 | 0.01 | 2.33e-3 / 1.33e-4 | **1.77e-3** / 1.56e-4 | 2.59e-3 / 1.37e-4 |
| 20 | 0.04 | 2.63e-2 / 3.66e-3 | 2.09e-2 / 5.56e-3 | **1.99e-2** / 7.41e-3 |
| 20 | 0.08 | 7.91e-2 / **2.92e-2** | **7.17e-2** / **2.12e-2** | 7.48e-2 / 2.52e-2 |
| 60 | 0.005 | 2.09e-3 / 3.21e-4 | 2.08e-3 / 3.40e-4 | 2.06e-3 / 3.21e-4 |
| 60 | 0.01 | 8.20e-3 / 5.42e-4 | **7.50e-3** / 6.10e-4 | 8.09e-3 / 5.50e-4 |
| 60 | 0.04 | **9.00e-2** / 2.26e-2 | 1.05e-1 / **1.69e-2** | 9.46e-2 / 2.44e-2 |
| 60 | 0.08 | **2.46e-1** / 1.26e-1 | 3.82e-1 / **1.19e-1** | 2.61e-1 / 1.28e-1 |
| 110 | 0.005 | 2.91e-3 / **3.11e-4** | **2.84e-3** / 3.76e-4 | 2.91e-3 / **3.11e-4** |
| 110 | 0.01 | 1.15e-2 / **7.09e-4** | **1.06e-2** / 7.23e-4 | 1.15e-2 / **7.09e-4** |
| 110 | 0.04 | 9.21e-2 / 3.74e-2 | 1.53e-1 / **2.39e-2** | **7.99e-2** / 3.30e-2 |
| 110 | 0.08 | 3.24e-1 / 1.48e-1 | 5.52e-1 / 1.62e-1 | **3.17e-1** / **1.41e-1** |
| 240 | 0.005 | 5.73e-3 / **8.03e-4** | 5.73e-3 / **8.00e-4** | **4.99e-3** / 1.47e-3 |
| 240 | 0.01 | 1.84e-2 / 4.42e-3 | 2.28e-2 / **1.41e-3** | **1.17e-2** / 3.16e-3 |
| 240 | 0.04 | 1.96e-1 / 4.20e-2 | 3.03e-1 / 4.72e-2 | **1.89e-1** / **4.02e-2** |
| 240 | 0.08 | 8.43e-1 / **2.91e-1** | 1.17e0 / 3.48e-1 | **8.21e-1** / 2.94e-1 |

**Verdict C — not demonstrated; measured mixed, and the large-`n` cells
argue against it.** Focused relaxation is the best variant at `n = 20` and
at the gentlest corruptions, and it is clearly *worse* once the arrangement
is larger and more damaged (`n = 240`, amp 0.08: 1.17 vs 0.84 full, 39%
higher energy; `n = 110`, amp 0.08: 0.55 vs 0.32). The per-body budget makes
that verdict stronger, not weaker: with a fixed total move budget, focusing
on `n/6` bodies gives each *selected* body six times the moves of the full
schedule, and it still loses. The reason is domain-specific and worth
recording: CRAM's focused Gibbs can freeze a cell because a Sudoku cell
carries its own constraint set; a body in a jammed packing does not — the
interior is part of the load path, and freezing it removes exactly the
coordinated motion the rearrangement needs. What survives is the weaker
version: focus is a sensible *tie-break* under a tight budget at small `n`,
and the single-body polish (`coordinate_polish`, idea B's second rule)
recovers most of focus's deficit later — `n = 110`, amp 0.04: focused
1.53e-1 → 2.39e-2 after polish, better than full's 3.74e-2. So focus
conserves basin, not progress.

**Verdict D — a weak, inconsistent positive.** The coarse-then-fine schedule
is never much worse and is sometimes clearly better (`n = 240`, amp 0.01:
1.17e-2 vs 1.84e-2 after the anneal, 3.16e-3 vs 4.42e-3 after polish;
`n = 110`, amp 0.04: 7.99e-2 vs 9.21e-2 and 3.30e-2 vs 3.74e-2). It is
worse in `n = 240` at the two extremes (amp 0.005, 0.08). Its natural
reading: settling *where* bodies sit at fixed angles before letting the tilts
move is a real coarse-to-fine advantage when the corruption is mid-scale, and
it buys nothing when the seed is already almost right or is far away. It does
not reach a fixed point or a feasible packing in any cell.

**The push table (the score question).** Eight cells (`n in {20,60,110,240}`
× depth 1% and 2%), seeded from the record at amp 0.02, one seed per cell,
8,000 moves: **0 of 24 runs produced a gated packing below the record**
(`best_gated_L` is `null` in every cell — the sampler never even returned a
pairwise-clear state at the squeezed side). Median polished `E` at depth 1%:
`n = 20` 4.08e-3 / 3.97e-3 / 5.22e-3, `n = 60` 1.75e-2 for all three,
`n = 110` 3.67e-2 / 3.53e-2 / 3.47e-2, `n = 240` 9.93e-2 / 7.31e-2 / 9.25e-2
(full / focused / two-layer). The stall law holds: `E` at a 1% squeeze is
10–100× the scale at which the descend ever closed anything, and no variant
closes it.

---

## 6. What is *not* shown, and the limits of these numbers

* **No run reached feasibility.** 0 of 96 matrix runs reached `E <= 1e-6`
  after the polish, and **0 of 96 reached a single-body fixed point** within
  four polish sweeps ("no single-cell change lowers the energy" never
  returned true). So C and D are compared as *descent rates at equal budget*,
  not as solvers. Any claim that focused or layered relaxation would or would
  not find packings is unsupported by this run.
* **Budget, not convergence.** 8,000 moves at `n = 240` is 33 moves per body;
  the paper's chains run to a fixed point. A larger budget could change the
  C/D ranking, although it would not change the `n = 240` per-body budget
  argument in §5.
* **Two seeds per cell.** Enough for the ordering reported, not enough for
  error bars; no significance is claimed for differences below ~20%.
* **The instrument is a measurement.** Energies are float; every feasibility
  claim is `packlib`'s. The relation table is fitted by histogram, not by
  gradient descent on the PL objective — the PL objective is *evaluated* as
  the scoring rule, not trained on.
* **No Lean, no absorption.** Nothing here is offered as a verified result
  or as a cent primitive. If an idea from this run is to enter the GLM, it
  goes through the intake (study → test → Lean → measured), and the Lean
  build is the owner's to run.
* `pressure_field.py`'s finite-difference `gradient` is a *directional*
  derivative (all coordinates perturbed at once), not a per-body gradient;
  the first attempt at this instrument used it and stalled. Recorded in the
  script's history, not as a claim against that engine.

---

## 7. What is worth carrying forward

1. **The relation cost table (A) as a seed scorer.** 21,602 contacts, 18
   cells, AUC 1.000 / 0.794 against the two controls, Spearman 0.37–0.74
   with where relaxation lands. It costs 28 s to fit and it is the cheapest
   ranking instrument this project now has. The natural next use is the one
   P2 closed for want of a good prior: score motif candidates before
   committing a relaxation budget, instead of sweeping every cell.
2. **The second stopping rule (B), as a fixed-point certificate.** "No
   single-body change lowers `E`" is the only stopping rule with information
   in this domain, and the polish pass that implements it recovers 2–8× on
   the annealer's endpoint. It is a *local* certificate and must be labelled
   as one — a fixed point of one-body moves is not a certificate of
   optimality, and in this run it never even fired.
3. **The `n = 240` negative for C.** "Freeze the quiescent interior" is not
   portable to a jammed continuous packing; the interior is load-bearing.
   That is a measured difference between CRAM's domain and this one, and it
   is the most useful thing this run learned about the paper.
4. **The threshold degeneracy (B) as a statement about the energies.** The
   paper's guarantees come from an energy whose low levels include wrong
   answers. This project's energy has no wrong low levels, which makes its
   stopping test free and its calibration worthless. That is a clean
   characterisation of what the two systems share and where they part.
