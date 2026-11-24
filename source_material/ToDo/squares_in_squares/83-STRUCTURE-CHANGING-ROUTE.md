# 83 — The structure-changing route, tested (run 124, completed in 126)

Doc 82 pointed at the family that changes *which cells sit where*: `resqueeze`'s patch-coordinate relaxation and
the block swap of run 115. This run drives it on the unbeaten rows inside a per-row budget, with controls first.
**Result: dL is zero on 20/20 rows — and after run 126 made the patch solve fast enough for every row to finish
sweeps, the zero is now a geometry result: the squeeze reaches `L0 - 4e-3` on 19/20 rows, and legalising that
pose costs 4.6e-2 to 3.0.** Read-only: no row changed, no score moved.

## 1. Why this family is different, and what was run

The earlier local routes refused a move the moment it overlapped a cell. This one is a **penalty** method, so it
may pass *through* illegal states — which is the only way a different tiling can be reached from a packed grid.
Per row, inside the budget, three attempts:

| attempt | structural move | then |
|---|---|---|
| 0 | none | squeeze (container hinged at `L0 - 4e-3`), project, legalise |
| 1 | one cell teleported into a void (or displaced 0.4 if there is none) | same |
| 2 | a 2x2 block rotated 90° about its centroid | same |

**squeeze** pays for the box and accepts overlap; **project** removes overlap under a weak wall term;
**legalise** then expands the shape by the smallest factor that passes the 40-digit gate. dL is measured only on
a certified legal pose — an illegal result counts as **no gain**, not as a candidate.

Two instrument facts, both established here, govern how the numbers below may be read:

* the 40-digit pair pass is O(n²) — 12 s at n = 655, 85 s at n = 999, measured this run — so the driver takes the
  exact side from `true_geom.side` (O(n), same digits) and spends the pair pass only where it can change a
  verdict. That is why the ladder's expansion rungs, which are *grossly* illegal, are screened out at 1e-6
  penetration and cost nothing (a full 20-row pass over 10,415 patch solves took 359 s of compute);
* a pose whose exact side is already at or above the delivered side cannot be a gain, because expansion is
  monotone in the factor. The driver stops there, which is an exact early exit, not a truncation.

Budget shape (run 126): the per-attempt budget is **split 60/40** between squeeze and projection. Run 125 gave
`relax` the whole budget, and since `relax` keeps sweeping until its deadline the projection was always entered
with zero time left — every row was judged on a pose nobody had tried to legalise. The iteration caps are
explicit (`--iters 10` per squeeze patch visit, `--proj-iters 40` for projection), which is a throughput choice,
not a relaxation of the objective: at fixed wall clock, fewer iterations per visit and more completed sweeps
leave a *lower* residual penalty (doc 85, §5).

## 2. Controls (run before any number was trusted)

| control | injection | outcome |
|---|---|---|
| A recovery | inflate an n=16 pose by 3.75e-3, hinge back at its side | **3.750e-3 recovered (100.0 %)**, legal, 0 violations |
| B structural absorb | displace one cell of n=12 by 0.3 | absorbed and legalised at 4.0030, **0 violations** |
| C solver equivalence | analytic gradient vs scipy finite differences, same patch | **6.6e-6 to 1.25e-5 relative**, same final objective (1e-22) |

**Three mechanical bugs were found by these controls, and they matter beyond this run:**

1. `resqueeze.patches` (and `resqueeze.solve_patch`) penalise only patch-vs-**outside** pairs, so overlaps
   *inside* a patch are invisible — a patch can sit on top of itself and report zero penalty;
2. `resqueeze.patches` uses `while x < hi_x`, so it returns an **empty patch list** for a pose with zero extent
   in a direction and can skip the last row/column; with no patches, nothing is relaxed and the run reports a
   null for a purely mechanical reason;
3. the first version of this driver reported dL from **illegal** poses; legality is now the only currency.

Run 126 added a fourth, in its own acceleration: the first batched gradient agreed with scipy's finite
differences at the start pose to 1e-17 and was 1e7 wrong one step away, because it perturbed the pose captured
when the problem was built instead of the `z` it was handed. A control that only samples the start point cannot
see that; `--check-solver` now samples three generic points (doc 85, §3).

**Consequence for the ledger:** run 116's "no beat" result came from an instrument carrying bugs 1 and 2. It was
re-run on the corrected driver — doc 84 — and its conclusion stands while its violation counts do not.

## 3. The measurement

20 evenly spaced unbeaten rows, three attempts each, **20 s per attempt**, `--iters 10 --proj-iters 40`. Every
attempt recorded its own sweep counts, so a row can no longer be zero *because* a sweep was cut off:

* **rows with at least one completed sweep: 20/20** (the count per row is in the table; 18/20 also had a
  cut-off sweep, i.e. they were still budget-limited at the margin, but not before finishing one);
* **rows whose squeeze got below the delivered side: 19/20** (all but n = 1, where there is nothing to move);
* **rows with positive dL: 0/20.**

`squeeze` is the exact 40-digit side of the squeezed pose *before* legalisation — the gain the penalty method
actually finds. `pen@proj` is the squared penetration left after the projection stage. `legalised` is the side
at the first rung of the expansion ladder that is legal (the bar is `L0`, so every rung above it is a loss by
construction); `payback` is `legalised - L0`.

| n | k | delivered side L0 | squeeze (illegal) | gain | pen@proj | sweeps | legalised | payback | rung |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1.000000000000 | — | 0 | 0 | 20/0 | 1.000000000000 | 0 | pose at the bar |
| 33 | 6 | 6.000000001666 | 5.995997135737 | +4.00e-3 | 1.1e-4 | 20/0 | 6.046034179657 | +4.60e-2 | f = 0.01 |
| 74 | 9 | 9.000000001778 | 8.996000931473 | +4.00e-3 | 1.9e-4 | 10/0 | 9.076000318564 | +7.60e-2 | f = 0.01 |
| 114 | 11 | 11.000000001818 | 10.996025836354 | +3.97e-3 | 1.6e-4 | 8/1 | 11.096012554793 | +9.60e-2 | f = 0.01 |
| 159 | 13 | 13.000000001846 | 12.996003101615 | +4.00e-3 | 7.8e-4 | 5/0 | 13.116010774310 | +1.16e-1 | f = 0.01 |
| 196 | 14 | 14.000000001858 | 13.996013869846 | +3.99e-3 | 1.1e-3 | 5/0 | 14.126033296834 | +1.26e-1 | f = 0.01 |
| 249 | 16 | 16.000000001875 | 15.996001580413 | +4.00e-3 | 1.6e-3 | 4/1 | 16.146027135822 | +1.46e-1 | f = 0.01 |
| 288 | 17 | 17.000000001882 | 16.996000554042 | +4.00e-3 | 1.6e-3 | 3/1 | 17.155975991526 | +1.56e-1 | f = 0.01 |
| 350 | 19 | 19.000000001894 | 18.995999764040 | +4.00e-3 | 1.4e-3 | 3/1 | 19.176020272760 | +1.76e-1 | f = 0.01 |
| 393 | 20 | 20.000000001900 | 19.995987717033 | +4.01e-3 | 3.0e-3 | 3/1 | 20.185950566853 | +1.86e-1 | f = 0.01 |
| 439 | 21 | 21.000000001904 | 20.995998631056 | +4.00e-3 | 4.2e-3 | 3/0 | 22.995600867300 | +2.00 | f = 0.1 |
| 510 | 23 | 23.000000001914 | 22.996000717254 | +4.00e-3 | 3.8e-3 | 2/1 | 25.195574934647 | +2.20 | f = 0.1 |
| 559 | 24 | 24.000000001916 | 23.995989155739 | +4.01e-3 | 3.6e-3 | 2/1 | 26.295616159178 | +2.30 | f = 0.1 |
| 610 | 25 | 25.000000001920 | 24.996000154057 | +4.00e-3 | 3.2e-3 | 2/1 | 27.395631481343 | +2.40 | f = 0.1 |
| 662 | 26 | 26.000000001924 | 25.995999088960 | +4.00e-3 | 8.0e-3 | 1/2 | 28.495608353651 | +2.50 | f = 0.1 |
| 715 | 27 | 27.000000001926 | 26.995994361973 | +4.01e-3 | 5.0e-3 | 1/2 | 29.595648678398 | +2.60 | f = 0.1 |
| 770 | 28 | 28.000000001928 | 27.996007996660 | +3.99e-3 | 4.5e-3 | 1/2 | 30.695626816088 | +2.70 | f = 0.1 |
| 826 | 29 | 29.000000001932 | 28.996003633822 | +4.00e-3 | 5.5e-3 | 1/2 | 31.795572850350 | +2.80 | f = 0.1 |
| 883 | 30 | 30.000000001934 | 29.996017676155 | +3.98e-3 | 1.3e-2 | 1/2 | 32.895541960076 | +2.90 | f = 0.1 |
| 942 | 31 | 31.000000001936 | 30.996025580266 | +3.97e-3 | 1.6e-2 | 1/2 | 33.995543715581 | +3.00 | f = 0.1 |

**Distribution: dL min 0, median 0, max 0; rows reaching the 4e-3 target: 0/20; rows legal and improving: 0.**

### What the table says

* **The squeeze is not the obstacle.** On every row with something to move, the penalty method reaches
  `L0 - 4e-3` — exactly the hinge target — in 1 to 20 completed sweeps. That is the same magnitude as the
  smallest gain the score needs (3.99e-3 to 9.84e-3 per row, doc 72).
* **Legality is.** The residual penetration after projection grows with n (1.1e-4 at n = 33 to 1.6e-2 at
  n = 942, i.e. a fixed ~3e-6 per cell) and the expansion ladder then needs `f = 1 %` up to n = 393 and
  `f = 10 %` from n = 439 up. Payback is 4.6e-2 at n = 33 and 3.0 at n = 942 — **10× to 750× the gain it was
  trying to bank.**
* Removing the overlap is a *rearrangement at the same density*, and the patch relaxation does not find one:
  removing 1e-2 of mutual penetration without shrinking the box is exactly the hard part of the problem, and it
  is not made easier by more sweeps at the same box. Every extra sweep moves the pose along the same illegal
  manifold instead of off it.

## 4. Verdict

**No positive dL on 20/20 rows, on rows where sweeps completed. The route has no tail.**

* The earlier doubt — "the zeros are a throughput result, not a refusal" — is now resolved in the other
  direction: with 1–20 completed sweeps per row, the squeeze is found every time and legalisation still gives
  back 10×–750× more than it gains. **Run 124's conclusion is reinstated on the evidence it lacked**, with the
  mechanism named: the projection cannot pay for the compression, and more sweeps make its residual smaller
  only slowly (`~3e-6` per cell per sweep-limited visit, never the 1e-3 the ladder needs).
* The improvement needed is structural, not budgetary: a move that changes the tiling *while staying legal* —
  a slide or a swap of a whole row through the free space — rather than a penalty walk that compresses first and
  asks for forgiveness later.
* What survives as a usable tool: the 40-digit gate, the O(n) exact side, the monotone early exits, and now a
  patch solve fast enough to run full sweeps (doc 85). Those are the parts a combinatorial tiling search would
  need.

## 5. Checks

| check | result |
|---|---|
| `structure.py --control` | A: 100.0 % recovery of 3.75e-3, legal; B: displaced cell absorbed, legal |
| `structure.py --check-solver` | gradient 6.6e-6–1.25e-5 vs scipy FD at 3 generic points; same objective; 57–67× faster |
| `structure.py --rows 20 --seconds 20` | 20/20 rows with ≥1 completed sweep; 19/20 squeezes below L0; 0 positive dL |
| patch solve cost | 410/374/383 ms → 2.1–2.4 ms per patch at a relaxed pose; ~21 ms at a stressed pose (iters 10) |
| sweep cost | 5.3 s / 72.6 s / 163.3 s → 0.4 s / 1.0 s / 3.2 s per sweep at n = 33 / 439 / 942 |
| `perturb.py --selftest`, `anchor_chain --selftest` | green |
| `sqscore`, `record_guard`, `void_insert --selftest`, `true_geom --selftest` | green |
| `glm_wheels --audit` | **657 functions, 0 offenders** |
| `submission.csv`, `WHITEBOARD.md` | untouched |
