# 85 — Patch-solve throughput: 374–410 ms → 2 ms, and what it found (run 126)

Doc 83 left one named next step: the structure-changing relaxation could not finish a sweep inside the attempt
budget, so its zeros were a throughput result rather than a geometry result. This run removes that limit and
re-runs the same 20-row table (doc 83, §3 is now the completed-sweep version). **The patch solve is 57–67×
cheaper and a full sweep now costs 1.0 s at n = 439 and 3.2 s at n = 942 instead of 72.6 s and 163.3 s.** With
that, the table becomes informative — and it says the route has no tail.

## 1. Where the 400 ms went

`probe126_profile.py` attributes one patch-solve to named stages on the real poses:

| stage | n = 33 | n = 439 | n = 942 |
|---|---|---|---|
| `patches()` (per sweep) | 0.3 ms | 2.2 ms | 3.3 ms |
| near-cell set (per patch) | 3.0 ms | 3.2 ms | 5.5 ms |
| `total_pen` (per sweep) | 0.3 ms | 2.7 ms | 11.6 ms |
| **`solve_patch_w`** | **264 ms** | **145 ms** | **153 ms** |
| patches per sweep | 13 | 194 | 426 |

The cost is entirely inside the L-BFGS-B call, and it is *not* the geometry: a median patch is 9 cells, i.e. 27
variables, and scipy's default 2-point finite differences spend **3c + 1 = 28 objective calls per gradient**.
One objective call in the old code copied three n-element arrays and ran `pen_vec` over ~150 pairs: **43 µs**.
At 120 iterations that is 28 × 120 × 43 µs ≈ 145 ms — the measured number. The n = 33 case is worse for the same
reason: all 33 cells fall in one patch, so it is 99 variables and 100 calls per iteration.

## 2. First acceleration: compact the pose, batch the gradient

Two changes, neither of which touches the function being minimised:

* **Compaction.** The objective is evaluated on the patch plus its neighbour set only
  (`near_cells`, now vectorised from a per-cell python loop into one mask). An objective call is then a copy of
  ~22 cells instead of ~1000.
* **One stacked gradient.** The 3c forward differences that scipy computes one at a time are stacked into a
  single `(3c, m)` batch and evaluated in one `pen_vec` call, with the same step (`sqrt(machine eps) * max(1,|z|)`).

That took a gradient from 6–13 ms to 2.2 ms and a converged-pose patch solve from 128 ms to ~2 ms.

### The bug this produced, and the control that caught it

The first batched gradient agreed with scipy's finite differences at the start pose to **1.7e-17** and was
**2.7e7 wrong one step away**. Cause: it perturbed the pose captured when the problem was built, while the base
value it subtracted was `obj(z)` — consistent at `z0` only. The fix is one line (unpack `z`, perturb that), but
the lesson is the project rule this file now enforces: `--check-solver` samples **three generic perturbed
points**, not the start pose, because a control that only looks where the solver starts cannot see a bug that
vanishes there. (The start pose itself is explicitly *not* asserted for gradient equality: the delivered pose's
objective is 1.5e-17, so a finite difference of it is roundoff noise and cannot referee anything.)

## 3. Analytic gradient

The remaining 2.2 ms was 4 trig evaluations per pair on a `(3c, 153)` batch. The penalty is

    p = clip(eps - best, 0),   best = max over the 4 edge normals q of  |d·q| - hA(q) - hB(q)

so where the maximum is attained by axis q, `d(p²)/dv = -2 p · d(best)/dv` with `d(best)/dv` the derivative of
that axis's separation alone. The parts that are easy to get wrong, and are handled explicitly:

* the **axis rotates with its owner** — for a cell-A axis `dq/dθ_A` is A's other unit vector, so `|d·q|`
  contributes a shape derivative, not only a translation one;
* `hA` and `hB` are exactly 1/2 on their owner's own axes and carry
  `d/dθ = (sign(u)·v - sign(v)·u)/2` on the *other* cell's axes;
* the container's `hx(θ) = (|cos θ| + |sin θ|)/2` has a **cusp at θ = 0**; `np.sign(0) = 0` silently reports no
  torque there, so the right-hand slope is taken. This was found by the same control (a wrong sign on the
  `lo - x + hx` term, and the cusp), again off the start pose.

**Verification (`structure.py --check-solver`):**

| quantity | result |
|---|---|
| gradient vs scipy 2-point FD, 3 generic points | **6.6e-6, 8.7e-6, 1.25e-5** relative (the residual is the FD truncation itself) |
| final objective, analytic vs scipy-FD solve, same patch | **identical to 1e-22** (dpose ~2e-14) |
| per patch solve, same patch | **2.0–2.3 ms vs 118–133 ms → 57–67×** |
| gradient cost | 0.27 ms, against 0.19 ms for a single objective call |
| `--control` after the change | A: **100.0 %** recovery of 3.75e-3; B: displaced cell absorbed at 4.0030 |

The search remains float (like `resqueeze`/`relax_angles`); nothing about the verdict moved. Legality and every
side are still decided by `true_geom` at 40 digits, and `glm_wheels --audit` still reports 657 functions with 0
offenders.

## 4. Sweeps now fit

| n | patches / sweep | per patch (relaxed pose) | one sweep, run 125 | one sweep, run 126 |
|---|---|---|---|---|
| 33 | 13 | 2.0 ms | 5.3 s | **0.4 s** |
| 439 | 194 | 2.4 ms | 72.6 s | **1.0 s** |
| 942 | 426 | 2.1 ms | 163.3 s | **3.2 s** |

A *stressed* pose (an actual squeeze, where the solver does not stop at iteration 0) costs more: **21 ms per
patch at `--iters 10`**, so a full sweep is ~9 s at n = 942. That is why the re-run uses a 20 s attempt budget:
it buys 1–2 completed sweeps on every tested row, which is exactly what run 125 could not buy at 3 s.

## 5. Two more findings from the same measurements

**(a) Fewer iterations per visit beats more iterations, at a fixed wall clock.** n = 662, 25 s cap, hinge at
`L0 - 4e-3`, `wall_w = 1e5`:

| `--iters` | completed sweeps | residual penalty |
|---|---|---|
| 20 | **2** | **6.60e-3** |
| 40 | 1 | 1.01e-2 |
| 120 | 1 | 1.12e-2 |

and at n = 942 (25 s cap): `--iters 10` → 2 sweeps, 6.56e-3; `--iters 20` → 1 sweep, 9.29e-3. A sweep is a
*defined* unit (visit every patch once); how hard each visit pushes is a budget choice, and at fixed time the
shallower-and-wider allocation leaves a lower penalty. The objective, the pair list and `eps` are unchanged, so
this is throughput allocation, not a weakened test — and the controls are green at the same settings.

**(b) The run-125 attempt spent its whole budget before legalising.** `relax` sweeps until its deadline, and the
driver handed it the entire per-attempt budget, so the projection stage was always entered with zero time left
and every row was judged on a pose nobody had tried to legalise. The budget is now split **60/40**
(`--split`), with `--proj-iters` capping the projection's own visits. This is a driver bug, not a geometry
result, and it is part of why run 125's zeros were uninformative.

## 6. What this does and does not buy

* It buys the measurement: the 20-row table in doc 83 now has a completed sweep on every row, 19/20 squeezes
  reach `L0 - 4e-3`, and legalisation still costs 4.6e-2 to 3.0. **The route's null is now a geometry result.**
* It does not buy a gain: no row reaches +4e-3, and none is legal, so nothing was delivered and `submission.csv`
  and the root `WHITEBOARD.md` are untouched.
* It does not touch the verifier: same `true_geom` gate, same exact side, same audit result.
* What is left to try, named: a move that changes the tiling *while staying legal* — a slide of a row through
  free space, or a swap of two blocks into each other's void — instead of a penalty walk that compresses first
  and asks for forgiveness later. The instrumentation for that (fast full sweeps, exact side, 40-digit gate) is
  now in place.

## 7. Checks

| check | result |
|---|---|
| `structure.py --check-solver` | gradient 6.6e-6–1.25e-5 vs scipy FD at 3 generic points; same objective; 57–67× faster |
| `structure.py --control` | A: 100.0 % recovery of 3.75e-3, legal; B: 0.3 displacement absorbed, legal |
| `structure.py --rows 20 --seconds 20 --iters 10 --proj-iters 40` | 20/20 rows ≥ 1 completed sweep; 0 positive dL; 10,415 patch solves in 359 s |
| `py_compile` on structure, resqueeze, and both probes | OK |
| `sqscore` | 22.218056945, 553 beats, 447 grid rows |
| `record_guard` | OK, no stale total presented as current |
| `glm_wheels --audit` | **657 functions, 0 offenders** |
| `submission.csv`, `WHITEBOARD.md` | untouched |
